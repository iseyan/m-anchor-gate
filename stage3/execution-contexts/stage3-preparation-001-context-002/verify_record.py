"""Read-only record consistency check; no token counting or live entry point."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path, PureWindowsPath
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def main():
    checks = []

    def check(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})
        if not condition:
            raise ValueError(name)

    def reference(row):
        raw = (ROOT / row['path']).read_bytes()
        check('reference:' + row['path'], digest(raw) == row['sha256']
              and ('bytes' not in row or len(raw) == row['bytes']))

    try:
        ctx = read(HERE / 'execution-context.record.json')
        method = read(HERE / 'token-method.candidate.json')
        review = read(HERE / 'request-linkage-review.json')
        for row in ctx['fixed_references']:
            reference(row)
        reference(ctx['token_method_record'])
        reference(ctx['request_linkage_review'])
        reference(review['source_archive'])
        reference(review['source_receipt'])
        reference(review['method_candidate'])
        refs = {r['path']: r for r in ctx['fixed_references']}
        form_path = method['current_call_accounting']['source']['path']
        form = read(ROOT / form_path)
        check('condition_source_matches', refs[form_path] == method['current_call_accounting']['source'])
        target_path = 'local-tools/stage3-environment-check-v0.1/target-manifest.json'
        targets = read(ROOT / target_path)['files']
        for target in targets:
            reference(target)
        check('target_scope', len(targets) == 44)
        receipt = read(ROOT / review['source_receipt']['path'])
        check('received_environment_linked', ctx['environment']['received'] == receipt['environment'])
        check('received_exact_mode_success', receipt['new_code_exact_validator_check_passed_as_received_record'] is True
              and ctx['environment']['exact_validator_checks_as_received'] == 68)
        check('call_cap_preserved', form['trial_plan']['maximum_total_api_calls'] == 7
              and ctx['call_accounting']['maximum_total_api_calls'] == 7
              and method['current_call_accounting']['remaining_call_capacity_for_counting'] == 0
              and ctx['call_accounting']['token_count_calls_adopted'] == 0)
        candidate = method['accounting_revision_candidate']
        check('candidate_not_adopted', method['adopted'] is False
              and candidate['adopted'] is False and candidate['approved'] is False
              and candidate['generation_attempt_cap'] == 7 and candidate['count_attempt_cap'] == 7
              and candidate['combined_attempt_cap'] == 14
              and candidate['extra_generations'] == 0 and candidate['all_retries'] == 0)
        check('no_live_ready_or_bound_claim', ctx['execution_ready'] is False
              and method['execution_ready'] is False
              and ctx['live_run_started'] is False
              and method['verified_host_bound_records_created'] == 0
              and method['full_request_token_gate_closed'] is False
              and not any(ctx[k] for k in ['preparation_evaluation_complete', 'stage3_complete', 'stage4_started']))
        prices = ctx['pricing']
        rates = prices['rate_basis']
        cost = (Decimal(8192) * Decimal(rates['uncached_input_usd_per_million'])
                + Decimal(2048) * Decimal(rates['output_usd_per_million'])) / Decimal(1000000)
        check('conditional_generation_arithmetic', rates == form['budget']['rate_basis']
              and cost == Decimal(prices['generation_charge_arithmetic_usd_per_call'])
              and cost * 7 == Decimal(prices['generation_charge_arithmetic_usd_for_seven'])
              and prices['run_budget_usd'] == form['budget']['limit'] == '1.00')
        check('count_cost_not_invented', prices['count_endpoint_price_verified'] is False
              and prices['count_cost_is_assumed_zero'] is False
              and candidate['count_request_cost_bound_usd'] is None)
        mapping = method['payload_mapping']
        copied = mapping['copy_unchanged_from_exact_generation_body']
        excluded = mapping['generation_controls_not_in_count_reference']
        expected_order = ['P001', 'P002', 'P003', 'A001', 'A002', 'A003', 'A004']
        check('seven_existing_fixture_requests', [r['trial_id'] for r in review['rows']] == expected_order)
        receipt_hashes = {r['trial_id']: r['request_sha256'] for r in receipt['retained_main_fixture_calls']}
        with zipfile.ZipFile(ROOT / review['source_archive']['path']) as z:
            prefix = 'environment-check-20260930T143626Z-f7a97493/'
            run_start = json.loads(z.read(prefix + 'run-start.json'))
            check('received_source_root', ctx['environment']['source_repo_path_on_windows'] == run_start['repo_path'])
            for row in review['rows']:
                trial = row['trial_id']
                raw = z.read(row['source_member'])
                body = json.loads(raw)
                view = json.loads(body['input'])['read_only_view']
                projected = canonical({key: body[key] for key in copied})
                check('request_linkage:' + trial,
                      set(body) == set(copied) | set(excluded)
                      and not set(mapping['forbidden_in_this_fixed_request']).intersection(body)
                      and body['model'] == form['model']['model_identifier']
                      and all(body[k] == v for k, v in form['model']['settings'].items())
                      and digest(raw) == row['generation_request_sha256'] == receipt_hashes[trial]
                      and len(raw) == row['generation_request_utf8_bytes']
                      and digest(projected) == row['candidate_count_request_sha256']
                      and len(projected) == row['candidate_count_request_utf8_bytes']
                      and digest(body['instructions'].encode('utf-8')) == row['instructions_utf8_sha256']
                      and digest(body['input'].encode('utf-8')) == row['input_string_utf8_sha256']
                      and view['state']['case_id'] == row['case_id']
                      and view['state']['version'] == row['state_version']
                      and view['state_sha256'] == row['state_sha256']
                      and row['input_token_count'] is None and row['input_token_upper_bound'] is None
                      and row['http_dispatched'] is False and row['bound_issued'] is False)
        storage = ctx['storage']
        physical = PureWindowsPath(storage['physical_root_plan'])
        original_map = read(ROOT / 'stage3/execution-contexts/stage3-preparation-001-context-001/storage-map.json')
        originals = original_map['future_live_run']['case_store_paths']
        check('planned_store_mapping', len(storage['case_store_map']) == len(originals)
              and all({k: v for k, v in row.items() if k != 'physical_path_plan'} == original
                      and row['physical_path_plan'] == str(physical.joinpath(*row['logical_path'].split('/')))
                      for row, original in zip(storage['case_store_map'], originals)))
        kit = PureWindowsPath(run_start['kit_path'])
        venv = PureWindowsPath(receipt['environment']['python_prefix'])
        check('path_plan_outside_kit_and_venv', physical.is_absolute()
              and not physical.is_relative_to(kit) and not physical.is_relative_to(venv)
              and storage['physical_run_directory_plan'] == str(physical.joinpath(*storage['logical_run_directory'].rstrip('/').split('/')))
              and storage['physical_root_exists'] is None and storage['writable'] is None
              and storage['run_directory_absent'] is None
              and storage['directory_created_by_this_work'] is False)
        check('zero_experimental_calls', all(d[k] == 0 for d in [ctx, method, review]
              for k in ['generation_api_calls', 'token_count_api_calls'])
              and ctx['official_run_state_store_writes'] == 0 and ctx['github_actions_used'] is False)
        status, error, exit_code = 'record_consistency_passed_token_gate_still_open', None, 0
    except Exception as exc:
        status, error, exit_code = 'record_consistency_failed', f'{type(exc).__name__}: {exc}', 1
    report = {
        'artifact_type': 'local_read_only_document_consistency_check',
        'checked_at_utc': datetime.now(timezone.utc).isoformat(),
        'checker_sha256': digest(Path(__file__).read_bytes()),
        'status': status, 'checks': checks, 'error': error, 'exit_code': exit_code,
        'model_or_count_API_called': False, 'schema_validator_called': False,
        'received_68_checks_rerun': False, 'schema_gate_003_rerun': False,
        'input_token_counts_observed': 0, 'verified_host_bounds_issued': 0,
        'windows_path_or_environment_reobserved': False,
        'experimental_state_stores_written': 0, 'execution_ready': False,
        'scope': 'Byte references, fixture-request projection, conditional arithmetic and planned path consistency only.',
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
