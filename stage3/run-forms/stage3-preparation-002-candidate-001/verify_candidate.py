"""Local document checks only. No API client, schema validator or state writer."""
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path, PureWindowsPath
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / 'stage3/run-forms/stage3-preparation-001'
RUN = 'stage3-preparation-002'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def renamed(value):
    if isinstance(value, str):
        return value.replace('stage3-preparation-001', RUN)
    if isinstance(value, list):
        return [renamed(x) for x in value]
    if isinstance(value, dict):
        return {k: renamed(v) for k, v in value.items()}
    return value


def pointer_get(obj, pointer):
    if not pointer:
        return obj
    for token in pointer[1:].split('/'):
        key = token.replace('~1', '/').replace('~0', '~')
        obj = obj[int(key)] if isinstance(obj, list) else obj[key]
    return obj


def leaf_changes(a, b, pointer=''):
    if type(a) is not type(b):
        return {pointer}
    if isinstance(a, dict):
        result = set()
        for key in set(a) | set(b):
            p = pointer + '/' + key.replace('~', '~0').replace('/', '~1')
            result |= {p} if key not in a or key not in b else leaf_changes(a[key], b[key], p)
        return result
    if isinstance(a, list):
        if len(a) != len(b):
            return {pointer}
        return set().union(*(leaf_changes(x, y, pointer + '/' + str(i)) for i, (x, y) in enumerate(zip(a, b))))
    return set() if a == b else {pointer}


def main():
    checks = []
    def check(name, value):
        checks.append({'name': name, 'passed': bool(value)})
        if not value:
            raise ValueError(name)

    try:
        docs = {p.name: read(p) for p in HERE.glob('*.json') if p.name != 'verification.json'}
        form, adm, plan = (docs[k] for k in ['run-form.candidate.json', 'case-admissions.candidate.json', 'trial-plan.candidate.json'])
        price, binding, delta = (docs[k] for k in ['pricing-bound.review.json', 'implementation-binding.plan.json', 'change-register.json'])
        old_form, old_adm, old_plan = (read(OLD / k) for k in ['official-run-form.json', 'case-admissions.json', 'trial-plan.json'])
        refs = set()
        def walk(obj):
            if isinstance(obj, dict):
                if isinstance(obj.get('path'), str) and isinstance(obj.get('sha256'), str):
                    refs.add((obj['path'], obj['sha256']))
                for value in obj.values():
                    walk(value)
            elif isinstance(obj, list):
                for value in obj:
                    walk(value)
        for obj in docs.values():
            walk(obj)
        for path, sha in sorted(refs):
            check('reference:' + path, hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha)
        for stem in ['case_admission', 'condition']:
            section = form['evidence_authority'] if stem == 'case_admission' else form['trial_plan']
            path = section[stem + '_manifest_path']
            check('embedded_manifest:' + stem, hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == section[stem + '_manifest_sha256'])
        check('new_proposed_id', form['run']['run_id'] == adm['run_id'] == plan['run_id'] == binding['proposed_run_id'] == RUN)
        check('unadopted_unfrozen_unexecuted', all(d['adopted'] is False for d in docs.values())
              and form['execution_ready'] is False and price['execution_ready'] is False and binding['execution_ready'] is False
              and form['freeze']['conditions_frozen'] is False and form['freeze']['official_form_fully_frozen'] is False
              and binding['implementation_binding_frozen'] is False
              and form['run']['frozen_at'] is None and form['run']['freeze_manifest_path'] is None
              and adm['fixed_at_utc'] is None and plan['fixed_at_utc'] is None
              and form['evidence_authority']['admission_fixed_at'] is None
              and form['entry_checks']['case_admission_fixed'] is False and form['entry_checks']['requested_parameters_frozen'] is False
              and form['adoption']['decision_record'] is None and plan['run_started'] is False)
        for field in ['scope', 'baseline', 'stop_conditions', 'failure_policy', 'partner_evaluation']:
            check('inherited:' + field, form[field] == old_form[field])
        for field in ['model_identifier', 'settings', 'omitted_settings', 'maximum_input_tokens', 'request_timeout_seconds',
                      'tools_available', 'previous_conversation_inherited', 'model_fallback_allowed', 'output_validation']:
            check('inherited_model:' + field, form['model'][field] == old_form['model'][field])
        check('schema_sources_unchanged', form['schemas']['files'] == old_form['schemas']['files'])
        check('evidence_interpretation_unchanged', adm['interpretation'] == old_adm['interpretation']
              and adm['registry_reference'] == old_adm['registry_reference']
              and adm['rejected_evidence_categories'] == old_adm['rejected_evidence_categories'])
        check('eight_case_rows_renamed_only', len(adm['case_rows']) == 8 and adm['case_rows'] == renamed(old_adm['case_rows']))
        form_rows = [{k: v for k, v in r.items() if k != 'admission_record_ref'} for r in form['evidence_authority']['case_rows']]
        check('admission_rows_agree', form_rows == adm['case_rows'])
        for row in form['evidence_authority']['case_rows']:
            check('admission_link:' + row['condition_id'] + '/' + row['variant'],
                  row['admission_record_ref'] == form['evidence_authority']['case_admission_manifest_path'] + '#' + row['condition_id'] + '/' + row['variant'])
        check('generation_trials_unchanged_except_case_id', plan['calls'] == renamed(old_plan['calls'])
              and plan['generation_order'] == old_plan['generation_order'])
        for field in ['retry_policy', 'proposal_replays', 'R4_fixed_replay_plan', 'R5_restart_plan', 'task_legality_separation']:
            check('inherited_trial_contract:' + field, plan[field] == renamed(old_plan[field]))
        cp = plan['counting_plan']
        check('paired_count_plan', len(cp['calls']) == 7
              and all(c == {'count_attempt_id': 'C-' + g['trial_id'], 'generation_trial_id': g['trial_id'],
                            'case_id': g['case_id'], 'maximum_attempts': 1} for c, g in zip(cp['calls'], plan['calls']))
              and cp['attempt_order_if_reached'] == [x for t in plan['generation_order'] for x in ['C-' + t, t]])
        check('proposed_endpoint_and_aggregate_caps', plan['maximum_generation_calls'] == 7
              and plan['maximum_count_api_calls'] == 7 and plan['maximum_count_attempts_per_trial'] == 1
              and plan['maximum_total_api_calls'] == 14 and form['trial_plan']['maximum_total_api_calls'] == 14
              and form['trial_plan']['maximum_generation_api_calls'] == 7 and form['trial_plan']['maximum_count_api_calls'] == 7
              and form['trial_plan']['allowance_adopted'] is False and old_form['trial_plan']['maximum_total_api_calls'] == 7)
        check('generation_budget_inherited', form['budget']['limit'] == old_form['budget']['limit'] == '1.00'
              and form['budget']['rate_basis'] == old_form['budget']['rate_basis'] == price['generation_rate_basis']
              and form['budget']['reservation_usd_per_call'] == '0.02')
        rate = price['generation_rate_basis']
        charge = (Decimal(8192) * Decimal(rate['uncached_input_usd_per_million']) + Decimal(2048) * Decimal(rate['output_usd_per_million'])) / Decimal(1000000)
        check('conditional_cost_arithmetic', charge == Decimal('0.01536')
              and charge * 7 == Decimal(price['generation_cost_bound_usd_for_seven_conditional'])
              and Decimal('0.02') * 7 == Decimal(price['generation_reservations_usd_for_seven'])
              and Decimal('1.00') - Decimal('0.14') == Decimal(price['symbolic_budget']['remaining_reservation_capacity_usd']))
        check('count_cost_and_total_remain_unknown', all(price[k] is None for k in ['count_endpoint_cost_basis', 'count_endpoint_cost_source', 'count_request_cost_upper_bound_usd', 'count_request_reservation_usd', 'combined_cost_upper_bound_usd'])
              and price['count_free_assumed'] is False and price['unknown_count_price_blocks_first_count'] is True
              and price['combined_cost_upper_bound_established'] is False
              and form['budget']['combined_cost_upper_bound_usd'] is None)
        check('implementation_not_claimed', binding['new_code_created'] is False and binding['new_code_checked'] is False
              and binding['new_runtime_manifest_sha256'] is None and binding['new_input_binding_sha256'] is None
              and binding['new_R4_fixture_manifest_sha256'] is None)
        storage = binding['storage_plan']
        check('new_output_namespace_only_planned', storage['logical_run_directory'] == 'stage3/runs/' + RUN + '/'
              and storage['physical_run_directory'] == str(PureWindowsPath(storage['physical_root']) / 'stage3' / 'runs' / RUN)
              and storage['created'] is False and storage['locally_verified'] is False)
        for pair in delta['pairs']:
            source = read(ROOT / pair['source']['path'])
            candidate = read(ROOT / pair['candidate']['path'])
            rows = pair['differences']
            check('complete_change_register:' + pair['candidate']['path'],
                  {row['pointer'] for row in rows} == leaf_changes(source, candidate)
                  and len(rows) == len({row['pointer'] for row in rows})
                  and all(('before' not in row or pointer_get(source, row['pointer']) == row['before'])
                          and ('after' not in row or pointer_get(candidate, row['pointer']) == row['after']) for row in rows))
        check('no_new_execution', form['creation_record']['model_api_calls'] == 0
              and form['creation_record']['token_count_api_calls'] == 0
              and form['creation_record']['state_store_writes'] == 0
              and form['creation_record']['github_actions_used'] is False
              and price['paid_API_calls'] == price['count_API_calls'] == 0)
        status, error, code = 'candidate_document_consistency_passed', None, 0
    except Exception as exc:
        status, error, code = 'candidate_document_consistency_failed', f'{type(exc).__name__}: {exc}', 1
    report = {
        'artifact_type': 'candidate_document_consistency_check_only',
        'checked_at_utc': datetime.now(timezone.utc).isoformat(),
        'checker_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'status': status, 'checks': checks, 'error': error, 'exit_code': code,
        'adopted': False, 'execution_ready': False, 'token_gate_closed': False,
        'schema_validation_performed': False, 'new_runtime_code_tested': False,
        'old_69_or_68_checks_rerun': False, 'schema_gate_003_rerun': False,
        'generation_API_calls': 0, 'count_API_calls': 0, 'state_store_writes': 0,
        'scope': 'References, complete recorded differences, inherited scientific conditions, proposed endpoint pairing and conditional arithmetic only.',
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == '__main__':
    sys.exit(main())
