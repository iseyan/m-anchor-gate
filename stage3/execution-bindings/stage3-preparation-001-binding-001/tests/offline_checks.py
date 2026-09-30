"""New local checks only. Never executes schema-gate-003 or any model API.

Default requires exact jsonschema. --structural-only is explicitly narrower,
cannot enable live dispatch, and reports external schema checks unperformed.
Every invocation requires a new output directory and retains failures.
"""
import argparse
import base64
from contextlib import closing
from decimal import Decimal
import importlib.metadata
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from contracts import BINDING, Contracts, decode, digest, encode, now
from gate import init_store, make_proposal, read_state, read_view, state_signature, submit_raw
from request_builder import build_request
from evaluator import score_decision, score_transition, compare_decisions, expected_decision
from api_client import Journal, OfflineTransport, LiveHTTPTransport, OneShotClient, Reply, DispatchBlocked

def block_network(event,args):
    if event in {'socket.connect','socket.getaddrinfo'}:
        raise RuntimeError('offline_check_network_disabled')

def main():
    sys.addaudithook(block_network)
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--structural-only',action='store_true')
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    report={'record_type':'pre_execution_binding_offline_checks','started_at':now(),'pid':os.getpid(),
            'python':sys.version,'platform':platform.platform(),'mode':'offline_structural' if a.structural_only else 'exact_jsonschema',
            'model_api_calls':0,'http_requests':0,'network_policy':'socket.connect and socket.getaddrinfo blocked by Python audit hook',
            'schema_gate_003_rerun':False,'execution_ready':False,'checks':[]}
    for folder in ['src','tests','prompts','fixtures']:
        shutil.copytree(BINDING/folder,out/'source-snapshot'/folder)
    shutil.copy2(BINDING/'runtime-manifest.json',out/'source-snapshot/runtime-manifest.json')
    report['runtime_manifest_sha256']=digest((BINDING/'runtime-manifest.json').read_bytes())
    report['source_sha256']={str(p.relative_to(BINDING)):digest(p.read_bytes()) for folder in ['src','tests','prompts','fixtures'] for p in (BINDING/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    def check(name,condition):
        report['checks'].append({'name':name,'passed':bool(condition)})
        if not condition: raise AssertionError(name)
    try:
        contracts=Contracts(offline_structural=a.structural_only)
        report['validation']=contracts.validation_status
        command=[sys.executable,'-B',str(BINDING/'tests/writer_fixture.py'),str(out/'writer')]
        if a.structural_only: command.append('--structural-only')
        run=subprocess.run(command,capture_output=True,timeout=45)
        (out/'writer.stdout').write_bytes(run.stdout);(out/'writer.stderr').write_bytes(run.stderr)
        check('writer_exit_zero_before_readers',run.returncode==0)
        writer=decode((out/'writer/writer-record.json').read_bytes())
        report['writer_record_sha256']=digest((out/'writer/writer-record.json').read_bytes())
        report['writer_pid']=writer['writer_pid'];report['writer_exit_observed_at']=now()
        r1,r2,r3=writer['proposal_records']
        check('R1_unsupported_removal_only_checked_store_rejects',[x['status'] for x in r1['audits']]==['rejected','accepted'])
        check('R1_checked_preserves_K_version_and_hash',r1['audits'][0]['state_before']==r1['audits'][0]['state_after'])
        check('R2_valid_full_update_accepted_in_both_stores',all(x['status']=='accepted' and x['state_after']['K']==['h_B'] for x in r2['audits']))
        check('R3_old_evidence_without_new_observation_accepted',all(x['status']=='accepted' for x in r3['audits']))
        check('D15_legality_and_task_failure_separated',r3['score']['preservation_legal'] and r3['score']['valid_partial_incorporation'] and not r3['score']['task_met'])
        check('three_model_shaped_fixtures_not_real_model_outputs',all(x['call']['model_api_calls']==0 and x['fixture_dispatches']==1 for x in writer['proposal_records']))
        check('paired_stores_receive_identical_raw_outputs',all(len({a['raw_response_sha256'] for a in r['audits']})==1 for r in writer['proposal_records']))
        for trial in ['P001','P002','P003']:
            planned=decode((BINDING/f'fixtures/initial-input-{trial}.json').read_bytes())
            request=decode((out/f'writer/journal/calls/{trial}/request.json').read_bytes())
            check(trial+'_planned_initial_input_equals_actual_read',decode(request['input'])['read_only_view']==planned)
        check('R4_four_categories_rejected_in_both_stores',len(writer['r4_replays'])==4 and all(x['status']=='rejected' for r in writer['r4_replays'] for x in r['audits']))
        check('R4_no_state_action_count_version_or_hash_change',writer['r4_before']==writer['r4_after'])
        try: read_view(out/'writer/unchecked/r1.sqlite','stage3-preparation-001-r1',contracts,'P001');blocked=False
        except ValueError: blocked=True
        check('unchecked_store_cannot_be_authoritative_input',blocked)
        reads=[];scores=[]
        for row in writer['restart_paths']:
            process=subprocess.run([sys.executable,'-B',str(BINDING/'src/reader.py'),row['store'],row['case_id']],capture_output=True,timeout=30)
            (out/(row['trial_id']+'.reader.stdout')).write_bytes(process.stdout)
            (out/(row['trial_id']+'.reader.stderr')).write_bytes(process.stderr)
            check(row['trial_id']+'_reader_exit_zero',process.returncode==0)
            read=decode(process.stdout);reads.append(read)
            check(row['trial_id']+'_different_pid',read['trace']['host_pid']!=writer['writer_pid'] and read['trace']['host_pid']!=os.getpid())
            body=base64.b64decode(read['api_request_base64'])
            receipt=read['offline_output']['binding']
            check(row['trial_id']+'_exact_read_to_request_bytes',digest(body)==read['trace']['api_input_sha256']==receipt['api_input_sha256'])
            check(row['trial_id']+'_same_reader_and_fixture_dispatch_process',receipt['dispatch_pid']==read['trace']['host_pid'])
            payload=decode(decode(body)['input'])
            check(row['trial_id']+'_view_is_actual_read',payload['read_only_view']==read['view'])
            check(row['trial_id']+'_evaluator_answer_not_in_input',set(payload)=={'task','output_schema','read_only_view'} and 'evaluator' not in decode(body)['instructions'])
            score=score_decision(read['view'],base64.b64decode(read['offline_output']['raw_base64']),contracts);scores.append(score)
            check(row['trial_id']+'_fixture_decision_matches_authoritative_read',score['matches'])
        check('four_distinct_reader_processes',len({x['trace']['host_pid'] for x in reads})==4)
        pairs=[compare_decisions(scores[0],scores[i],kind) for i,kind in [(1,'changed_K'),(2,'response_only'),(3,'summary_only')]]
        check('three_restart_fixture_contrasts',all(x['passed'] for x in pairs))
        check('summary_only_preserves_state_version_action',reads[0]['view']['state']==reads[3]['view']['state'] and reads[0]['view']['action']==reads[3]['view']['action'] and reads[0]['view']['summary']!=reads[3]['view']['summary'])
        check('R5_old_evidence_not_new_observation',reads[1]['view']['new_observation_ids']==[] and reads[1]['view']['admitted_evidence'][0]['evidence_id']=='e_B')
        report['restart_comparisons']=pairs
        report['restart_reader_pids']=[x['trace']['host_pid'] for x in reads]
        # Independent malformed/forged proposal checks, not additional API trials.
        case='stage3-preparation-001-r1';store=out/'negative.sqlite'
        state=init_store(store,case,contracts)
        base=make_proposal(state,'negative-base')
        variants=[('wrong_case',encode(dict(base,case_id='wrong-case'))),
                  ('wrong_version',encode(dict(base,expected_version=999))),
                  ('wrong_hash',encode(dict(base,expected_state_sha256='0'*64))),
                  ('unadmitted_e_B',encode(dict(base,evidence_ids=['e_B'],proposed_K=['h_B']))),
                  ('malformed_JSON',b'{broken'),('duplicate_JSON_key',b'{"case_id":"a","case_id":"b"}'),
                  ('extra_field',encode(dict(base,future_bypass=True))),
                  ('wrong_version_type',encode(dict(base,expected_version=True))),
                  ('duplicate_candidate',encode(dict(base,proposed_K=['h_A','h_A']))) ]
        negative=[]
        for label,raw in variants:
            before=state_signature(store,case)
            audit=submit_raw(store,case,raw,contracts,origin='fixed_invalid_replay')
            check(label+'_rejected_without_state_action_change',audit['status']=='rejected' and state_signature(store,case)==before)
            negative.append(audit)
        (out/'negative-audits.json').write_bytes(encode(negative)+b'\n')
        # Exact input bytes must be retained; forged linkage does not commit.
        view,trace=read_view(store,case,contracts,'P001');body,trace=build_request(view,trace,contracts)
        altered=dict(trace,api_input_sha256='0'*64)
        transport=OfflineTransport(error=TimeoutError())
        client=OneShotClient(contracts,Journal(out/'tampered-request'),transport)
        try: client.call(body,altered);blocked=False
        except ValueError: blocked=True
        check('changed_request_blocked_before_dispatch',blocked and transport.calls==0)
        # Transport failure: one attempt, preserve reservation, no second attempt.
        fail_transport=OfflineTransport(error=TimeoutError())
        fail_journal=Journal(out/'timeout')
        failure,_=OneShotClient(contracts,fail_journal,fail_transport).call(body,trace)
        check('timeout_retained_no_retry',failure['status']=='transport_failure' and fail_transport.calls==1 and fail_journal.stopped())
        check('unknown_usage_reservation_not_released',(fail_journal.root/'budget/P001.reserve.json').exists() and not (fail_journal.root/'budget/P001.settled.json').exists())
        # Refusal, incomplete generation, malformed envelope and model mismatch.
        from writer_fixture import response
        sample=response('{}',contracts.form)
        examples=[]
        refusal=decode(encode(sample));refusal['output'][0]['content']=[{'type':'refusal','refusal':'Offline refusal fixture.'}]
        examples.append(('refusal',encode(refusal)))
        incomplete=decode(encode(sample));incomplete['status']='incomplete';examples.append(('incomplete',encode(incomplete)))
        examples.append(('malformed_envelope',b'not JSON'))
        mismatch=decode(encode(sample));mismatch['model']='unexpected-model';examples.append(('model_mismatch',encode(mismatch)))
        for label,raw in examples:
            tr=OfflineTransport(Reply(200,'offline-error',raw));j=Journal(out/label)
            record,result=OneShotClient(contracts,j,tr).call(body,trace)
            check(label+'_retained_no_usable_output',result is None and tr.calls==1 and (j.root/'calls/P001/response.raw').read_bytes()==raw)
        live=LiveHTTPTransport(None)
        try: OneShotClient(contracts,Journal(out/'live-blocked'),live).call(body,trace);blocked=False
        except DispatchBlocked: blocked=True
        check('live_http_unready_blocked_before_reservation',blocked and not (out/'live-blocked/budget').exists())
        if contracts.offline_structural:
            before=state_signature(store,case)
            try: submit_raw(store,case,encode(base),contracts,origin='model_output');blocked=False
            except ValueError: blocked=True
            check('structural_checker_cannot_accept_live_origin',blocked and before==state_signature(store,case))
        # The old-evidence control can perform a full update, not just a legal partial one.
        old_case='stage3-preparation-001-r3';old_store=out/'old-evidence-full.sqlite'
        old_state=init_store(old_store,old_case,contracts)
        old_view,_=read_view(old_store,old_case,contracts,'P003')
        old_proposal=make_proposal(old_state,'old-evidence-full',K=['h_B'],evidence=['e_B'])
        old_audit=submit_raw(old_store,old_case,encode(old_proposal),contracts,origin='trusted_control_setup')
        check('old_evidence_full_update_without_new_observation',old_view['new_observation_ids']==[] and old_audit['status']=='accepted' and old_audit['state_after']['K']==['h_B'])
        # Check exhaustion distinction on a synthetic evaluator-only view.
        empty=decode(encode(view));empty['state']['K']=[];empty['state_sha256']=digest(empty['state'])
        check('empty_K_is_exhaustion',expected_decision(empty)['cause_status']=='candidate_exhaustion')
        (out/'restart-scores.json').write_bytes(encode(scores)+b'\n')
        reserves=list((out/'writer/journal/budget').glob('*.reserve.json'))
        check('seven_main_fixture_dispatches_zero_model_calls',len(reserves)==7 and all(decode(x.read_bytes())['transport_mode']=='offline_fixture' for x in reserves))
        try: Journal(out/'writer/journal').reserve('A005',contracts.form,'offline_fixture');blocked=False
        except DispatchBlocked: blocked=True
        check('eighth_dispatch_not_permitted',blocked and len(list((out/'writer/journal/budget').glob('*.reserve.json')))==7)
        # Budget accounting is tested separately using a declared simulated prior charge.
        budget=Journal(out/'budget-cap');budget.reserve('P001',contracts.form,'offline_fixture')
        budget.write('budget/P001.settled.json',{'charge_usd':'0.99','simulated_charge':True})
        try: budget.reserve('P002',contracts.form,'offline_fixture');blocked=False
        except DispatchBlocked: blocked=True
        check('budget_cap_blocks_before_next_reservation',blocked and not (budget.root/'budget/P002.reserve.json').exists())
        report.update(status='passed_offline_checks',main_fixture_dispatches=7,external_schema_conformance_verified=not a.structural_only,
                      auxiliary_error_fixture_dispatches=5,live_api_linkage_verified=False,preparation_evaluation_complete=False,stage3_complete=False,
                      official_state_store_writes=0,temporary_fixture_store_writes=True,spend_incurred_usd='0.00')
        rc=0
    except Exception as error:
        report.update(status='blocked_or_failed',error_type=type(error).__name__,error=str(error))
        (out/'failure-traceback.txt').write_text(traceback.format_exc(),encoding='utf-8')
        rc=2
    report['ended_at']=now();report['passed_checks']=sum(x['passed'] for x in report['checks'])
    (out/'report.json').write_bytes(encode(report)+b'\n')
    print(encode({'status':report['status'],'checks':report['passed_checks'],'report':str(out/'report.json'),'model_api_calls':0}).decode())
    return rc

if __name__=='__main__':
    sys.exit(main())
