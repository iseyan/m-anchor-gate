"""Read-only receipt checks. Does not execute the submitted code or schema checker."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import sqlite3
import zipfile

RUN = 'environment-check-20260930T143626Z-f7a97493'
BINDING = 'stage3/execution-bindings/stage3-preparation-001-binding-001/'
KIT = 'local-tools/stage3-environment-check-v0.1/'
CONTEXT = 'stage3/execution-contexts/stage3-preparation-001-context-001/'
BASIS = '2153827e8dc9baec6ab6a64d4742e89d680ccddc'
FORM = 'stage3/run-forms/stage3-preparation-001/official-run-form.json'


def pairs(values):
    result = {}
    for key, value in values:
        if key in result:
            raise ValueError('duplicate_JSON_key:' + key)
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=pairs)


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else encode(value)).hexdigest()


def win(path):
    return str(PureWindowsPath(path)).casefold()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    if args.output.exists():
        parser.error('output exists; use a new record path')
    raw_zip = args.archive.read_bytes()
    assertions = []
    def check(name, passed):
        assertions.append({'name': name, 'matches': bool(passed)})
        if not passed:
            raise AssertionError(name)
    def local(path):
        return decode((root / path).read_bytes())
    with zipfile.ZipFile(args.archive) as archive:
        names = archive.namelist()
        check('archive_unique_confined_file_names', len(names) == len(set(names)) and all(
            not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts
            and n.startswith(RUN + '/') and not n.endswith('/') for n in names))
        check('archive_CRC', archive.testzip() is None)
        files = {name[len(RUN) + 1:]: archive.read(name) for name in names}
    def record(name):
        return decode(files[name])
    manifest = {}
    for line in files['SHA256SUMS.txt'].decode('utf-8').splitlines():
        expected, name = line.split('  ', 1)
        check('unique_manifest_entry:' + name, name not in manifest)
        manifest[name] = expected
    check('manifest_complete_except_itself', set(manifest) == set(files) - {'SHA256SUMS.txt'})
    payload_hashes = {name: sha(raw) for name, raw in files.items()}
    check('all_manifest_payload_hashes_match', all(payload_hashes[name] == digest for name, digest in manifest.items()))

    start = record('run-start.json')
    result = record('run-result.json')
    environment = record('environment.json')
    report = record('binding-check/report.json')
    writer = record('binding-check/writer/writer-record.json')
    plan = local(KIT + 'environment-check-plan.json')
    targets = local(KIT + 'target-manifest.json')['files']
    helpers = local(KIT + 'tool-manifest.json')['files']
    runtime = local(BINDING + 'runtime-manifest.json')
    form = local(FORM)
    context = local(CONTEXT + 'execution-context.plan.json')
    ref003 = local('stage3/schema-gates/schema-gate-003/verification.json')
    check('record_identity_and_fixed_basis', start['run_id'] == result['run_id'] == RUN
          and start['context_id'] == context['context_id'] and start['basis_commit'] == plan['basis_commit'])
    for field, path in [('plan_sha256', KIT + 'environment-check-plan.json'),
                        ('tool_manifest_sha256', KIT + 'tool-manifest.json'),
                        ('target_manifest_sha256', KIT + 'target-manifest.json'),
                        ('conditions_sha256', FORM),
                        ('runtime_manifest_sha256', BINDING + 'runtime-manifest.json')]:
        check('start_link:' + field, start[field] == sha((root / path).read_bytes()))
    for label, rows in [('tool', helpers), ('target', targets)]:
        expected = {row['path']: row['sha256'] for row in rows}
        for phase in ['before', 'after']:
            observed = record(label + '-hashes.' + phase + '.json')
            check(label + '_' + phase + '_hashes', len(observed) == len(expected) and all(
                row['path'] in expected and row['expected_sha256'] == row['observed_sha256'] == expected[row['path']]
                and row['matches'] is True for row in observed) and len({row['path'] for row in observed}) == len(expected))
        base = root / KIT if label == 'tool' else root
        check(label + '_matches_repository_bytes', all(sha((base / path).read_bytes()) == value for path, value in expected.items()))
    check('runtime_manifest_snapshot', files['binding-check/source-snapshot/runtime-manifest.json'] == (root / BINDING / 'runtime-manifest.json').read_bytes())
    expected_snapshots = {row['path']: row['sha256'] for row in runtime['files'] if row['path'] != 'requirements.txt'}
    observed_snapshots = {key.replace('\\', '/'): value for key, value in report['source_sha256'].items()}
    check('all_22_runtime_source_snapshots', observed_snapshots == expected_snapshots and all(
        sha(files['binding-check/source-snapshot/' + name]) == digest for name, digest in expected_snapshots.items()))
    check('checker_and_writer_hash_links', result['checker_report_sha256'] == payload_hashes['binding-check/report.json']
          and report['writer_record_sha256'] == payload_hashes['binding-check/writer/writer-record.json']
          and report['runtime_manifest_sha256'] == start['runtime_manifest_sha256'])

    probe = record('validator-probe.process.json')
    checker = record('binding-check.process.json')
    probe_command = record('validator-probe.command.json')
    checker_command = record('binding-check.command.json')
    check('probe_and_checker_exit_zero', all(p['exit_code'] == 0 and p['timed_out'] is False for p in [probe, checker]))
    check('probe_stdout_is_environment_receipt', record('validator-probe.stdout.txt') == environment)
    check('specified_validator_observed', environment['validator_ready'] is True and environment['validator_version'] == '4.26.0'
          and environment['validator_class'] == 'jsonschema.validators.Draft202012Validator'
          and environment['schema_checks_performed'] is False)
    check('same_recorded_003_interpreter_and_prefix', win(start['requested_python']) == win(environment['python_executable']) == win(ref003['execution']['python_executable'])
          and win(environment['python_prefix']) == win(ref003['execution']['python_prefix'])
          and environment['python_version'] == ref003['execution']['python_version'])
    check('same_interpreter_used_by_probe_and_checker', all(win(p['command'][0]) == win(environment['python_executable']) for p in [probe_command, checker_command]))
    check('default_exact_mode_and_output_path', '--structural-only' not in checker_command['command']
          and checker_command['command'][-2] == '--output'
          and win(checker_command['command'][-1]) == win(str(PureWindowsPath(start['result_path']) / 'binding-check'))
          and report['mode'] == 'exact_jsonschema' and report['validation'] == 'jsonschema_4.26.0_Draft202012Validator')
    check('output_outside_kit_and_source', not PureWindowsPath(start['result_path']).is_relative_to(PureWindowsPath(start['kit_path']))
          and not PureWindowsPath(start['result_path']).is_relative_to(PureWindowsPath(start['repo_path'])))
    old_names = [x['name'] for x in local(BINDING + 'checks/local-check-005.report.json')['checks']
                 if x['name'] != 'structural_checker_cannot_accept_live_origin']
    check('68_named_exact_mode_checks_passed', len(old_names) == plan['expected_exact_mode_check_count'] == 68
          and [x['name'] for x in report['checks']] == old_names
          and all(x['passed'] is True for x in report['checks'])
          and result['passed_checks'] == result['check_count'] == report['passed_checks'] == 68)
    check('success_receipts_agree', result['status'] == 'passed_offline_environment_check'
          and report['status'] == 'passed_offline_checks'
          and result['external_schema_conformance_verified'] is report['external_schema_conformance_verified'] is True
          and record('binding-check.stdout.txt')['status'] == report['status'])
    check('chronology', start['started_at_utc'] <= probe['started_at_utc'] <= probe['ended_at_utc']
          <= checker['started_at_utc'] <= report['started_at'] <= writer['ended_at']
          <= report['writer_exit_observed_at'] <= report['ended_at'] <= checker['ended_at_utc'] <= result['ended_at_utc'])

    # Read submitted SQLite bytes in memory, without running their Python sources.
    stores = {}
    audit_checks = []
    for path in sorted(name for name in files if name.endswith('.sqlite')):
        conn = sqlite3.connect(':memory:')
        conn.deserialize(files[path])
        metadata = {key: decode(value) for key, value in conn.execute('SELECT key,value FROM metadata')}
        rows = [{'seq': row[0], 'case_id': row[1], 'kind': row[2], 'record_id': row[3], 'value': decode(row[4])}
                for row in conn.execute('SELECT seq,case_id,kind,record_id,payload FROM records ORDER BY seq')]
        conn.close()
        latest = {}
        for row in rows:
            latest[row['kind']] = row['value']
        check('SQLite_case_and_mode:' + path, all(row['case_id'] == metadata['case_id'] for row in rows)
              and metadata['validation_mode'] == report['validation'])
        audits = [row['value'] for row in rows if row['kind'] == 'audit']
        for audit in audits:
            before, after = audit['state_before'], audit['state_after']
            valid = (audit['state_hash_before'] == sha(before) and audit['state_hash_after'] == sha(after))
            if audit['status'] == 'rejected':
                valid = valid and before == after
            else:
                valid = valid and after['version'] == before['version'] + 1
                if not metadata['comparison']:
                    applied = audit['applied_evidence']
                    supported = {'h_B'} if applied else {'h_A', 'h_B'}
                    valid = valid and set(applied) <= set(latest['authority']['admitted_valid_ids'])
                    valid = valid and (set(before['K']) & supported) <= set(after['K']) <= set(before['K'])
            audit_checks.append(valid)
        stores[path] = {'metadata': metadata, 'latest': latest, 'rows': rows,
                        'counts': {kind: sum(row['kind'] == kind for row in rows) for kind in ['state', 'action']}}
    check('all_stored_audit_hashes_versions_and_checked_preservation', all(audit_checks))

    restarts = []
    readers = []
    for row in writer['restart_paths']:
        trial = row['trial_id']
        read = record('binding-check/' + trial + '.reader.stdout')
        readers.append(read)
        trace = read['trace']
        request = base64.b64decode(read['api_request_base64'], validate=True)
        body = decode(request)
        payload = decode(body['input'])
        receipt = read['offline_output']['binding']
        path = PureWindowsPath(row['store']).relative_to(PureWindowsPath(start['result_path'])).as_posix()
        saved = stores[path]
        view = read['view']
        check(trial + '_saved_state_action_summary_match_read', not saved['metadata']['comparison']
              and view['state'] == saved['latest']['state'] and view['action'] == saved['latest']['action']
              and view['summary'] == saved['latest']['summary'])
        check(trial + '_hash_and_version_linkage', sha(view['state']) == view['state_sha256'] == trace['state_sha256_read']
              and sha(view['action']) == trace['action_sha256_read'] == view['state']['action_sha256']
              and trace['state_version_read'] == view['state']['version']
              and trace['action_id_read'] == view['action']['action_id']
              and sha(view) == trace['read_input_sha256'])
        check(trial + '_read_to_exact_unsent_request', payload['read_only_view'] == view
              and sha(request) == trace['api_input_sha256'] == receipt['api_input_sha256']
              and request == files['binding-check/writer/journal/calls/' + trial + '/request.json']
              and set(payload) == {'task', 'output_schema', 'read_only_view'}
              and trace['expected_values_included'] is False and trace['previous_conversation_inherited'] is False)
        check(trial + '_restart_process_and_timing', trace['host_pid'] == receipt['dispatch_pid']
              and trace['host_pid'] not in [writer['writer_pid'], report['pid']]
              and report['writer_exit_observed_at'] < trace['read_at'] < report['ended_at'])
        check(trial + '_offline_origin_and_no_read_write', read['http_dispatched'] is False and read['model_api_calls'] == 0
              and read['store_unchanged'] is True and receipt['origin'] == 'offline_transport_fixture'
              and trace['api_request_id'] is None and trace['summary_used_to_reconstruct_K'] is False)
        candidate_set = view['state']['K']
        expected = {'schema_version': 'stage3-decision/v0.1', 'case_id': row['case_id'],
                    'state_version_read': view['state']['version'], 'state_sha256_read': view['state_sha256'],
                    'selected_action': view['action']['selected_action'], 'retained_candidates': candidate_set,
                    'cause_status': 'candidate_exhaustion' if not candidate_set else 'single_candidate_under_interpretation' if len(candidate_set) == 1 else 'unresolved'}
        observed = decode(base64.b64decode(read['offline_output']['raw_base64'], validate=True))
        check(trial + '_decision_matches_saved_read', observed == expected == read['offline_assessment']['observed']
              and read['offline_assessment']['matches'] is True)
        restarts.append({'trial_id': trial, 'reader_pid': trace['host_pid'], 'case_id': row['case_id'],
                         'state_version': view['state']['version'], 'K': candidate_set,
                         'action_id': view['action']['action_id'], 'selected_action': view['action']['selected_action'],
                         'cause_status': observed['cause_status'], 'state_sha256': view['state_sha256'],
                         'request_sha256': sha(request), 'http_dispatched': False})
    check('four_distinct_readers', len({row['reader_pid'] for row in restarts}) == 4
          and report['restart_reader_pids'] == [row['reader_pid'] for row in restarts])
    check('summary_control_preserves_state_action_and_decision', readers[0]['view']['state'] == readers[3]['view']['state']
          and readers[0]['view']['action'] == readers[3]['view']['action']
          and readers[0]['view']['summary'] != readers[3]['view']['summary']
          and readers[0]['offline_assessment']['observed'] == readers[3]['offline_assessment']['observed'])
    check('K_and_action_controls_are_distinct', restarts[0]['K'] == ['h_A', 'h_B'] and restarts[1]['K'] == ['h_B']
          and restarts[0]['selected_action'] == 'a_B' and restarts[2]['selected_action'] == 'a_A'
          and restarts[2]['K'] == restarts[0]['K'] and restarts[2]['cause_status'] == 'unresolved')

    proposal_results = writer['proposal_records']
    transitions = []
    for n, proposal in enumerate(proposal_results, start=1):
        trial = 'P00' + str(n)
        audits = proposal['audits']
        check(trial + '_matched_raw_proposals', len(audits) == 2
              and audits[0]['raw_response_base64'] == audits[1]['raw_response_base64']
              and all(sha(base64.b64decode(a['raw_response_base64'], validate=True)) == a['raw_response_sha256'] for a in audits)
              and all(a['origin'] == 'offline_transport_fixture' for a in audits))
        for comparator, audit in zip(['checked', 'unchecked'], audits):
            db = stores['binding-check/writer/' + comparator + '/r' + str(n) + '.sqlite']
            check(trial + '_' + comparator + '_audit_and_state_saved', any(r['kind'] == 'audit' and r['value'] == audit for r in db['rows'])
                  and db['latest']['state'] == audit['state_after'])
        transitions.append({'trial_id': trial, 'checked_status': audits[0]['status'], 'unchecked_status': audits[1]['status'],
                            'checked_K': audits[0]['state_after']['K'], 'unchecked_K': audits[1]['state_after']['K'],
                            'preservation_legal': proposal['score']['preservation_legal'],
                            'task_met': proposal['score']['task_met'], 'valid_partial_incorporation': proposal['score']['valid_partial_incorporation']})
    check('R1_only_matched_commit_difference', [t['trial_id'] for t in transitions if t['checked_status'] != t['unchecked_status']] == ['P001'])
    check('R1_preserved_R2_full_update_R3_partial_separate', transitions[0]['checked_K'] == ['h_A', 'h_B']
          and transitions[1]['checked_K'] == ['h_B'] and transitions[1]['task_met'] is True
          and transitions[2]['preservation_legal'] is True and transitions[2]['valid_partial_incorporation'] is True
          and transitions[2]['task_met'] is False)
    check('four_R4_categories_retained_and_rejected', [r['fixture_id'] for r in writer['r4_replays']] == ['F001', 'F002', 'F003', 'F004']
          and all(a['status'] == 'rejected' and a['state_before'] == a['state_after'] for r in writer['r4_replays'] for a in r['audits'])
          and writer['r4_before'] == writer['r4_after'])
    for i, comparator in enumerate(['checked', 'unchecked']):
        stored = stores['binding-check/writer/' + comparator + '/r4.sqlite']
        signature = writer['r4_after'][i]
        check('R4_' + comparator + '_counts_match_SQLite', stored['counts'] == signature['counts']
              and stored['latest']['state'] == signature['state'] and sha(signature['state']) == signature['sha256'])
    negative = record('binding-check/negative-audits.json')
    check('nine_negative_proposals_retained', len(negative) == 9 and all(a['status'] == 'rejected' and a['state_before'] == a['state_after'] for a in negative))

    call_rows = []
    for trial in ['P001', 'P002', 'P003', 'A001', 'A002', 'A003', 'A004']:
        base = 'binding-check/writer/journal/calls/' + trial + '/'
        req = record(base + 'request-record.json')
        call = record(base + 'result.json')
        check(trial + '_journal_raw_request_and_response_hashes', sha(files[base + 'request.json']) == req['request_sha256'] == call['api_input_sha256']
              and sha(files[base + 'request-record.json']) == call['request_record_sha256']
              and sha(files[base + 'response.raw']) == call['raw_response_sha256'])
        check(trial + '_mock_transport_only', call['transport_mode'] == req['transport_mode'] == 'offline_fixture'
              and call['model_api_calls'] == 0 and call['offline_fixture_calls'] == 1
              and req['bound_record'] is None and req['read_trace']['api_request_id'] is None)
        call_rows.append({'trial_id': trial, 'fixture_response_id': call['api_request_id'],
                          'request_sha256': call['api_input_sha256'], 'response_sha256': call['raw_response_sha256']})
    check('missing_usage_preserves_stop_and_reservation', 'binding-check/timeout/STOP.json' in files
          and 'binding-check/timeout/budget/P001.reserve.json' in files
          and 'binding-check/timeout/budget/P001.settled.json' not in files)
    check('four_auxiliary_output_failures_preserved', all('binding-check/' + k + '/calls/P001/response.raw' in files
          for k in ['refusal', 'incomplete', 'malformed_envelope', 'model_mismatch']))
    check('live_preflight_blocked_before_reservation', 'binding-check/live-blocked/calls/P001/preflight-blocked.json' in files
          and not any(n.startswith('binding-check/live-blocked/budget/') for n in files))
    check('zero_calls_and_stage_boundaries', result['model_api_calls'] == result['token_count_api_calls'] == report['http_requests'] == report['model_api_calls'] == 0
          and result['official_run_state_store_writes'] == report['official_state_store_writes'] == 0
          and all(result[k] is False for k in ['execution_ready', 'live_run_started', 'preparation_evaluation_complete', 'stage3_complete', 'stage4_started', 'schema_gate_003_rerun']))

    verification = {
        'record_type': 'received_offline_environment_check_verification',
        'reviewed_at_utc': datetime.now(timezone.utc).isoformat(), 'basis_commit': BASIS,
        'run_id': RUN, 'status': 'received_records_consistent_offline_check_passed',
        'origin': 'User-executed Windows run; receiver checked submitted bytes, source links, JSON records and SQLite snapshots. The receiver did not rerun the Windows checker or jsonschema.',
        'original_zip': {'file': args.archive.name, 'sha256': sha(raw_zip), 'bytes': len(raw_zip)},
        'payload_file_count': len(files), 'manifest_entry_count': len(manifest),
        'payload_sha256': payload_hashes,
        'checks': assertions,
        'fixed_references': {path: sha((root / path).read_bytes()) for path in [FORM, BINDING + 'binding.json', BINDING + 'runtime-manifest.json', CONTEXT + 'execution-context.plan.json', KIT + 'environment-check-plan.json', KIT + 'tool-manifest.json', KIT + 'target-manifest.json']},
        'matched_tool_files': len(helpers), 'matched_target_files': len(targets),
        'source_snapshot_files_matched': len(expected_snapshots),
        'environment': environment,
        'execution': {'started_at_utc': start['started_at_utc'], 'ended_at_utc': result['ended_at_utc'],
                      'launcher_pid': start['launcher_pid'], 'checker_launch_pid': checker['pid'],
                      'checker_self_reported_pid': report['pid'], 'writer_pid': report['writer_pid'],
                      'reader_pids': report['restart_reader_pids'], 'checker_exit_code': checker['exit_code'],
                      'probe_exit_code': probe['exit_code'], 'writer_exit_observed_at': report['writer_exit_observed_at'],
                      'same_recorded_003_interpreter_and_prefix': True,
                      'python_override_supplied_note': 'The CMD wrapper passes --python explicitly even for its default path; the true flag does not by itself indicate an operator-selected different environment.',
                      'pid_note': 'The Popen PID and checker self-reported PID are distinct fields and are retained as recorded. Their equality is not assumed; this receipt does not independently reconstruct the OS process tree.'},
        'new_code_check': {'mode': 'exact_jsonschema', 'passed_checks': 68,
                           'names': [r['name'] for r in report['checks']],
                           'validator': 'jsonschema==4.26.0 / Draft202012Validator',
                           'schema_names': sorted(form['schemas']['files']),
                           'four_check_schema_calls_basis': 'Frozen Contracts source checks all four schemas before exact-mode runtime validation; the received exact-mode run completed successfully. Not independently rerun by receiver.',
                           'external_conformance_scope': 'The pinned new implementation and its offline inputs/proposals/states/decisions exercised in this run only; not future live data.'},
        'restart_reads': restarts, 'matched_proposal_transitions': transitions,
        'retained_main_fixture_calls': call_rows,
        'main_fixture_dispatches': report['main_fixture_dispatches'],
        'auxiliary_error_fixture_dispatches': report['auxiliary_error_fixture_dispatches'],
        'fixture_usage_note': 'usage, estimated_charge_usd, HTTP 200 and offline-* IDs belong to simulated responses. They are not observed API usage, billed spend, real API IDs or a verified token upper bound.',
        'model_api_calls': 0, 'token_count_api_calls': 0, 'spend_incurred_usd': '0.00',
        'official_run_state_store_writes': 0, 'temporary_fixture_store_writes': True,
        'github_actions_used': False, 'execution_ready': False, 'live_run_started': False,
        'preparation_evaluation_complete': False, 'stage3_complete': False, 'stage4_started': False,
        'schema_gate_003_rerun': False, 'new_code_exact_validator_check_passed_as_received_record': True,
        'token_bound_status': 'unresolved_for_frozen_call_plan', 'account_access_status': 'not_verified',
        'remaining': ['Supported full-request bound of at most 8192 tokens, with exact per-request linkage and unchanged or separately revised call accounting.',
                      'A separate live-start record binding the confirmed environment, current costs, absolute output root and per-request bound evidence.'],
        'limitations': ['Receipt and consistency verification, not an independent Windows reproduction.',
                       'Hashes identify bytes; they do not authenticate an execution or prove privileged-write resistance.',
                       'No model understanding, prompt-injection resistance, live API linkage, adoption or Stage 3 completion claim.'],
        'previous_records': 'Keep all prior records unchanged, including failed local-check-001, failed authoring probe, 001–003, conditions, binding, context plan, distribution ZIP, Bundle and materials.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(verification, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'status': verification['status'], 'manifest_entries': len(manifest),
                      'recorded_exact_mode_checks': 68, 'output': str(args.output), 'execution_ready': False}))


if __name__ == '__main__':
    main()
