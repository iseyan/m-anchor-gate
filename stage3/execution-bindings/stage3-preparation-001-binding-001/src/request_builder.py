"""Build the exact request bytes from a host read; no evaluator imports."""
from contracts import BINDING, decode, digest, encode, verify_runtime_manifest

def build_request(view, trace, contracts):
    if verify_runtime_manifest() != contracts.runtime_manifest_sha256:
        raise ValueError('runtime_manifest_changed')
    contracts.validate('input',view)
    if trace['read_input_sha256'] != digest(view) or trace['state_sha256_read'] != view['state_sha256']:
        raise ValueError('read_view_trace_mismatch')
    tasks = decode((BINDING/'prompts/tasks.json').read_bytes())
    trial_id = trace['trial_id']
    if trial_id not in tasks:
        raise ValueError('unplanned_api_trial')
    task = tasks[trial_id]
    kind = task['output_schema']
    instructions = (BINDING/f'prompts/{kind}.txt').read_text(encoding='utf-8')
    payload = {'task':task['task'],'output_schema':contracts.schemas[kind],'read_only_view':view}
    if kind == 'proposal':
        payload['proposal_id'] = trial_id
    form = contracts.form
    body = {'model':form['model']['model_identifier'],**form['model']['settings'],
            'instructions':instructions,'input':encode(payload).decode('utf-8')}
    raw = encode(body)
    trace = dict(trace,api_input_sha256=digest(raw),model_input_utf8_bytes=len(raw),
                 expected_values_included=False,output_schema=kind,
                 api_request_id=None,request_id_status='not_dispatched')
    return raw, trace
