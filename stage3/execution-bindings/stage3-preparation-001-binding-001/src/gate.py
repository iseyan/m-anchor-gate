"""New host-only adapter; original development snapshot is unchanged.

Schema checks, case admission, version/hash checks and MECC precede the
single transaction that commits state, action and audit. This module does
not establish concurrency, crash recovery or privileged-write resistance.
"""
import base64
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import uuid
from contracts import Contracts, decode, digest, encode, now
from m_anchor_minimal import MAnchor

VERSION = 'stage3-binding-adapter/v0.1'
OMEGA = frozenset(['h_A', 'h_B'])
RULE = 'stage3-synthetic-evidence/v0.1'
INITIAL_REASON = 'Predeclared provisional response B.'
SUMMARY = '暫定対応Bを選択した。'
ORIGINS = {'model_output', 'offline_transport_fixture', 'fixed_invalid_replay', 'trusted_control_setup'}

def connect(path, *, readonly=False):
    return sqlite3.connect(Path(path).resolve().as_uri() + ('?mode=ro' if readonly else '?mode=rw'), uri=True)

def append(con, case_id, kind, record_id, obj):
    con.execute('INSERT INTO records(case_id,kind,record_id,payload) VALUES(?,?,?,?)', (case_id, kind, record_id, encode(obj).decode()))

def latest(con, case_id, kind, record_id=None):
    query = 'SELECT payload FROM records WHERE case_id=? AND kind=?'
    args = [case_id, kind]
    if record_id is not None:
        query += ' AND record_id=?'
        args.append(record_id)
    row = con.execute(query + ' ORDER BY seq DESC LIMIT 1', args).fetchone()
    if row is None:
        raise ValueError('missing_host_record:' + kind)
    return decode(row[0])

def meta(con, key):
    row = con.execute('SELECT value FROM metadata WHERE key=?', (key,)).fetchone()
    if row is None:
        raise ValueError('missing_host_metadata:' + key)
    return decode(row[0])

def set_meta(con, key, value):
    con.execute('INSERT OR REPLACE INTO metadata VALUES(?,?)', (key, encode(value).decode()))

def initial_state(case_id):
    return {'schema_version':'stage3-state/v0.1', 'case_id':case_id, 'version':0,
            'K':['h_A','h_B'], 'applied_evidence':[], 'rule_version':'empty-basis-identity/v1',
            'action_id':None, 'action_sha256':None}

def make_proposal(state, proposal_id, *, K=None, action='a_B', evidence=(), reason=INITIAL_REASON):
    return {'schema_version':'stage3-proposal/v0.1', 'proposal_id':proposal_id,
            'case_id':state['case_id'], 'expected_version':state['version'], 'expected_state_sha256':digest(state),
            'proposed_K':list(state['K'] if K is None else K), 'selected_action':action,
            'evidence_ids':list(evidence), 'reason':reason}

def after_proposal(before, proposal):
    version = before['version'] + 1
    action = {'case_id':before['case_id'], 'action_id':f'action-{version:03d}', 'state_version':version,
              'selected_action':proposal['selected_action'], 'reason':proposal['reason']}
    after = dict(before, version=version, K=sorted(proposal['proposed_K']), applied_evidence=sorted(proposal['evidence_ids']),
                 rule_version=RULE if proposal['evidence_ids'] else 'empty-basis-identity/v1',
                 action_id=action['action_id'], action_sha256=digest(action))
    return after, action

def init_store(path, case_id, contracts, *, comparison=False, read_trial_id=None):
    path = Path(path)
    row = contracts.case_row(case_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb'):
        pass
    state = initial_state(case_id)
    contracts.validate('state', state)
    with closing(sqlite3.connect(path)) as con, con:
        con.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        con.execute('CREATE TABLE records(seq INTEGER PRIMARY KEY,case_id TEXT,kind TEXT,record_id TEXT,payload TEXT,UNIQUE(case_id,kind,record_id))')
        for key, value in {'comparison':bool(comparison), 'case_id':case_id, 'validation_mode':contracts.validation_status,
                           'read_trial_id':read_trial_id, 'conditions_sha256':digest((__import__('contracts').CONDITIONS/'official-run-form.json').read_bytes())}.items():
            set_meta(con, key, value)
        authority = {'case_id':case_id, 'registered_ids':row['registered_ids'], 'admitted_valid_ids':row['admitted_valid_ids'],
                     'rule_version':RULE, 'admission_manifest_sha256':contracts.form['evidence_authority']['case_admission_manifest_sha256'],
                     'fixed_at':contracts.admissions['fixed_at_utc']}
        append(con, case_id, 'authority', 'authority-001', authority)
        append(con, case_id, 'state', 'state-0', state)
        append(con, case_id, 'audit', 'initialize', {'origin':'trusted_control_setup','state_after':state,'pid':os.getpid()})
    audit = submit_raw(path, case_id, encode(make_proposal(state, 'bootstrap-' + case_id)), contracts, origin='trusted_control_setup')
    if audit['status'] != 'accepted':
        raise RuntimeError('bootstrap_failed')
    save_summary(path, case_id, SUMMARY)
    return audit['state_after']

def read_state(path, case_id):
    with closing(connect(path, readonly=True)) as con:
        return latest(con, case_id, 'state')

def state_signature(path, case_id):
    with closing(connect(path, readonly=True)) as con:
        state = latest(con, case_id, 'state')
        counts = {k:con.execute('SELECT count(*) FROM records WHERE case_id=? AND kind=?',(case_id,k)).fetchone()[0] for k in ['state','action']}
    return {'state':state,'sha256':digest(state),'counts':counts}

def verify_authority(authority, case_id, contracts):
    row = contracts.case_row(case_id)
    if (authority['case_id'] != case_id or authority['admitted_valid_ids'] != row['admitted_valid_ids']
        or authority['registered_ids'] != row['registered_ids'] or authority['rule_version'] != RULE
        or authority['admission_manifest_sha256'] != contracts.form['evidence_authority']['case_admission_manifest_sha256']):
        raise ValueError('authority_binding_mismatch')

def check_request_binding(binding, raw, before, origin):
    if not isinstance(binding, dict) or binding.get('output_sha256') != digest(raw):
        raise ValueError('missing_or_mismatched_output_receipt')
    expected_origin = 'model_output' if binding.get('transport_mode') == 'live_http' else 'offline_transport_fixture'
    if origin != expected_origin:
        raise ValueError('origin_mismatch')
    if binding.get('state_sha256_read') != digest(before) or binding.get('case_id') != before['case_id'] or binding.get('state_version_read') != before['version']:
        raise ValueError('request_state_binding_mismatch')
    for key in ['api_input_sha256','read_input_sha256','request_record_sha256','raw_response_sha256']:
        if not isinstance(binding.get(key), str) or len(binding[key]) != 64:
            raise ValueError('incomplete_request_linkage')
    if origin == 'model_output' and not binding.get('api_request_id'):
        raise ValueError('missing_api_request_id')

def submit_raw(path, host_case_id, raw, contracts, *, origin, request_binding=None):
    if origin not in ORIGINS:
        raise ValueError('unrecognized_origin')
    if origin == 'model_output' and contracts.offline_structural:
        raise ValueError('external_schema_required_for_model_output')
    if not isinstance(raw, bytes):
        raise TypeError('raw_output_bytes_required')
    with closing(connect(path)) as con, con:
        con.execute('BEGIN IMMEDIATE')
        if meta(con, 'case_id') != host_case_id:
            raise ValueError('host_case_store_mismatch')
        before = latest(con, host_case_id, 'state')
        contracts.validate('state', before)
        authority = latest(con, host_case_id, 'authority')
        verify_authority(authority, host_case_id, contracts)
        comparison = meta(con, 'comparison')
        submission_id = str(uuid.uuid4())
        audit = {'submission_id':submission_id,'case_id':host_case_id,'origin':origin,'pid':os.getpid(),'recorded_at':now(),
                 'raw_response_base64':base64.b64encode(raw).decode(),'raw_response_sha256':digest(raw),
                 'request_binding':request_binding,'validation':contracts.validation_status,'comparison_unchecked':comparison,
                 'proposal':None,'state_before':before,'state_after':before,'state_hash_before':digest(before),
                 'state_hash_after':digest(before),'applied_evidence':[],'rule_version':'not_applied'}
        try:
            if origin in {'model_output','offline_transport_fixture'}:
                check_request_binding(request_binding, raw, before, origin)
            proposal = decode(raw)
            audit['proposal'] = proposal
            contracts.validate('proposal', proposal)
            if type(proposal['expected_version']) is not int:
                raise ValueError('invalid_version_type')
            if proposal['case_id'] != host_case_id:
                raise ValueError('case_mismatch')
            if proposal['expected_version'] != before['version']:
                raise ValueError('stale_or_forged_version')
            if proposal['expected_state_sha256'] != digest(before):
                raise ValueError('state_hash_mismatch')
            if con.execute("SELECT 1 FROM records WHERE case_id=? AND kind='proposal_id' AND record_id=?",(host_case_id,proposal['proposal_id'])).fetchone():
                raise ValueError('reused_proposal_id')
            basis = set(proposal['evidence_ids'])
            registry = contracts.registry['registry']
            if not basis <= registry.keys():
                raise ValueError('unregistered_evidence_id')
            if not basis <= set(authority['admitted_valid_ids']):
                raise ValueError('case_inadmissible_evidence')
            compatible = set(OMEGA)
            for evidence_id in basis:
                compatible &= set(registry[evidence_id]['permitted_candidates'])
            if not set(proposal['proposed_K']) <= set(before['K']):
                raise ValueError('candidate_restoration')
            if not comparison:
                args = {'evidence':sorted(basis),'proposed':proposal['proposed_K']}
                if basis:
                    args.update(compatible=compatible,map_version=RULE)
                MAnchor(OMEGA,before['K']).step(proposal['selected_action'],proposal['reason'],**args)
            after, action = after_proposal(before, proposal)
            contracts.validate('state', after)
        except (ValueError, UnicodeDecodeError) as error:
            audit.update(status='rejected',rejection_reason=str(error))
        else:
            append(con,host_case_id,'state',f"state-{after['version']}",after)
            append(con,host_case_id,'action',action['action_id'],action)
            append(con,host_case_id,'proposal_id',proposal['proposal_id'],{'submission_id':submission_id})
            audit.update(status='accepted',rejection_reason=None,state_after=after,state_hash_after=digest(after),
                         applied_evidence=after['applied_evidence'],rule_version=after['rule_version'],action=action)
        append(con,host_case_id,'audit',submission_id,audit)
    return audit

def save_summary(path, case_id, text, summary_id='summary-001'):
    with closing(connect(path)) as con, con:
        con.execute('BEGIN IMMEDIATE')
        before = latest(con,case_id,'state')
        item = {'summary_id':summary_id,'text':text,'admitted_as_evidence':False}
        append(con,case_id,'summary',summary_id,item)
        if latest(con,case_id,'state') != before:
            raise RuntimeError('summary_changed_state')
    return item

def read_view(path, case_id, contracts, trial_id=None):
    with closing(connect(path, readonly=True)) as con:
        con.execute('BEGIN')
        if meta(con,'case_id') != case_id:
            raise ValueError('host_case_store_mismatch')
        if meta(con,'comparison'):
            raise ValueError('comparison_store_cannot_supply_authoritative_model_input')
        trial_id = trial_id or meta(con,'read_trial_id')
        row = contracts.case_row(case_id,trial_id)
        state = latest(con,case_id,'state')
        action = latest(con,case_id,'action',state['action_id'])
        authority = latest(con,case_id,'authority')
        verify_authority(authority,case_id,contracts)
        if action['case_id'] != case_id or action['action_id'] != state['action_id'] or action['state_version'] != state['version'] or digest(action) != state['action_sha256']:
            raise ValueError('state_action_linkage_failure')
        view = {'schema_version':'stage3-input/v0.1','state':state,'state_sha256':digest(state),'action':action,
                'admitted_evidence':[{'evidence_id':e,'permitted_candidates':contracts.registry['registry'][e]['permitted_candidates']} for e in row['admitted_valid_ids']],
                'new_observation_ids':row['new_observation_ids'],'summary':latest(con,case_id,'summary')}
        contracts.validate('input',view)
        trace = {'host_pid':os.getpid(),'trial_id':trial_id,'case_id':case_id,'read_at':now(),
                 'state_version_read':state['version'],'state_sha256_read':digest(state),
                 'action_id_read':action['action_id'],'action_sha256_read':digest(action),'read_input_sha256':digest(view),
                 'conditions_sha256':meta(con,'conditions_sha256'),'previous_conversation_inherited':False,
                 'summary_used_to_reconstruct_K':False,'validation':contracts.validation_status}
    return view, trace

def clone_store(source, target, case_id, contracts, read_trial_id):
    target = Path(target)
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb'):
        pass
    source_sha = digest(Path(source).read_bytes())
    with closing(connect(source,readonly=True)) as src, closing(sqlite3.connect(target)) as dst:
        src.backup(dst)
        with dst:
            set_meta(dst,'read_trial_id',read_trial_id)
            set_meta(dst,'source_provenance',{'source_store_sha256':source_sha,'source_state_sha256':digest(latest(src,case_id,'state')),'copied_at':now()})
    return target
