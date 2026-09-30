"""Host composition helpers. No command here launches paid inference."""
from pathlib import Path
import base64
from contextlib import closing
from contracts import BINDING, decode, digest, encode
from gate import connect, meta, read_view, read_state, state_signature, submit_raw, clone_store, make_proposal, save_summary
from request_builder import build_request

def proposal_call(checked, unchecked, case_id, trial_id, contracts, client, *, bound_record=None):
    with closing(connect(unchecked,readonly=True)) as con:
        if not meta(con,'comparison'):
            raise ValueError('comparison_path_not_marked_unchecked')
    view, trace = read_view(checked,case_id,contracts,trial_id)
    other = read_state(unchecked,case_id)
    if other != view['state']:
        raise ValueError('comparison_start_states_differ')
    body, trace = build_request(view,trace,contracts)
    record, result = client.call(body,trace,bound_record=bound_record)
    if result is None:
        return {'call':record,'audits':[]}
    raw, binding = result
    audits = [submit_raw(p,case_id,raw,contracts,origin=binding['origin'],request_binding=binding) for p in [checked,unchecked]]
    client.journal.write(f'calls/{trial_id}/store-comparison.json',{'audits':audits,'same_raw_sha256':digest(raw),
                         'attribution':'integration_mechanism','fixed_replay':False})
    from evaluator import score_transition
    scored = score_transition(audits[0],contracts,full_incorporation=trial_id in ['P002','P003'])
    if audits[0]['status']=='accepted' and (not scored['preservation_legal'] or not scored['evidence_admissible']):
        client.journal.stop('checked_path_invariant_violation',trial_id)
    return {'call':record,'audits':audits,'score':scored}

def decision_call(store,case_id,contracts,client,*,bound_record=None):
    before = state_signature(store,case_id)
    view, trace = read_view(store,case_id,contracts)
    body, trace = build_request(view,trace,contracts)
    record, result = client.call(body,trace,bound_record=bound_record)
    if state_signature(store,case_id) != before:
        client.journal.stop('state_changed_during_read_only_call',trace['trial_id'])
        raise RuntimeError('state_changed_during_read_only_call')
    from evaluator import score_decision
    score = None if result is None else score_decision(view,result[0],contracts)
    client.journal.write(f"calls/{trace['trial_id']}/decision-score.json",{'assessment':score,'store_unchanged':True,
                         'response_receipt':record,'evaluator_only':True})
    return {'view':view,'trace':trace,'api_request_base64':base64.b64encode(body).decode(),
            'call_record':record,'output':None if result is None else {'raw_base64':base64.b64encode(result[0]).decode(),'binding':result[1]},
            'assessment':score,'store_unchanged':True}

def coverage_from_audits(audits,contracts):
    covered = {}
    for audit in audits:
        if audit.get('origin') not in {'model_output','offline_transport_fixture'} or audit.get('status')!='rejected':
            continue
        proposal = audit.get('proposal')
        try:
            contracts.validate('proposal',proposal)
        except ValueError:
            continue
        ids = set(proposal['evidence_ids'])
        reason = audit['rejection_reason']
        categories = []
        if reason == 'unregistered_evidence_id':
            action_id = audit['state_before']['action_id']
            if action_id in ids: categories.append('action_id')
            if 'summary-001' in ids: categories.append('summary_id')
            if ids - set(contracts.registry['registry']) - {action_id,'summary-001'}: categories.append('unregistered_id')
        elif reason == 'case_inadmissible_evidence':
            categories.append('registered_but_not_case_admitted')
        for category in categories:
            covered[category]={'proposal_id':proposal['proposal_id'],'case_id':audit['case_id'],'origin':audit['origin'],
                              'rejection_reason':reason,'raw_sha256':audit['raw_response_sha256']}
    return covered

def fixed_replays(checked,unchecked,case_id,contracts,model_audits=()):
    covered = coverage_from_audits(model_audits,contracts)
    manifest = decode((BINDING/'fixtures/r4-manifest.json').read_bytes())
    rows = []
    for fixture in manifest['proposals']:
        if fixture['category'] in covered:
            rows.append({'fixture_id':fixture['fixture_id'],'status':'not_replayed_attempt_recorded','coverage_record':covered[fixture['category']]})
            continue
        raw = (BINDING/fixture['path']).read_bytes()
        if digest(raw) != fixture['sha256']:
            raise ValueError('fixed_proposal_hash_mismatch')
        rows.append({'fixture_id':fixture['fixture_id'],'origin':'fixed_invalid_replay','audits':[
            submit_raw(p,case_id,raw,contracts,origin='fixed_invalid_replay') for p in [checked,unchecked]]})
    return rows

def restart_controls(reference,output_dir,case_id,contracts):
    output_dir = Path(output_dir)
    action = clone_store(reference,output_dir/'response-only.sqlite',case_id,contracts,'A003')
    summary = clone_store(reference,output_dir/'summary-only.sqlite',case_id,contracts,'A004')
    before = read_state(action,case_id)
    proposed = make_proposal(before,'control-response-A',action='a_A',evidence=before['applied_evidence'],reason='Predeclared response-only control.')
    audit = submit_raw(action,case_id,encode(proposed),contracts,origin='trusted_control_setup')
    if audit['status']!='accepted':
        raise RuntimeError('response_control_setup_rejected')
    save_summary(summary,case_id,contracts.trials['R5_restart_plan']['summary_only_text'],'summary-002')
    return action,summary,audit
