"""Package checks in a new scratch directory; no installation or live calls."""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
NAME = 'stage3-environment-check-v0.1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree(path):
    return {p.relative_to(path).as_posix(): digest(p) for p in path.rglob('*') if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.is_relative_to(ROOT):
        parser.error('output must be outside the repository')
    out.mkdir(parents=True, exist_ok=False)
    checks = []
    def check(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})
        if not condition:
            raise AssertionError(name)
    zip_path = ROOT / 'distributions' / (NAME + '.zip')
    with zipfile.ZipFile(zip_path) as archive:
        check('ZIP_CRC_valid', archive.testzip() is None)
        check('ZIP_member_names_confined', all(not p.startswith('/') and '..' not in Path(p).parts for p in archive.namelist()))
        archive.extractall(out / 'extracted')
    kit = out / 'extracted' / NAME
    repo = kit / 'targets/repo'
    baseline = tree(kit)
    target_manifest = json.loads((kit / 'target-manifest.json').read_text())
    tool_manifest = json.loads((kit / 'tool-manifest.json').read_text())
    check('all_44_frozen_targets_match', len(target_manifest['files']) == 44 and all(digest(repo / x['path']) == x['sha256'] for x in target_manifest['files']))
    check('all_helper_hashes_match', all(digest(kit / x['path']) == x['sha256'] for x in tool_manifest['files']))
    expected_names = {x['path'] for x in tool_manifest['files']} | {'tool-manifest.json'} | {'targets/repo/' + x['path'] for x in target_manifest['files']}
    check('ZIP_has_exactly_52_manifested_files', set(baseline) == expected_names and len(baseline) == 52)
    for p in kit.rglob('*.py'):
        ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
    check('all_Python_sources_parse', True)
    cmd = (kit / 'run-environment-check.cmd').read_bytes()
    check('CMD_is_ASCII_CRLF', cmd.isascii() and b'\r\n' in cmd and b'\n' not in cmd.replace(b'\r\n', b''))
    module_spec = importlib.util.spec_from_file_location('kit_runner_check', kit / 'run_environment_check.py')
    module = importlib.util.module_from_spec(module_spec)
    sys.dont_write_bytecode = True
    module_spec.loader.exec_module(module)
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'offline-test-sentinel', 'PYTHONPATH': 'offline-test-sentinel'}):
        env = module.child_env()
        check('child_environment_omits_credentials_and_PYTHONPATH', 'OPENAI_API_KEY' not in env and 'PYTHONPATH' not in env)
        check('child_environment_preserves_UTF8_without_bytecode', all(env.get(k) == v for k, v in {'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8', 'PYTHONDONTWRITEBYTECODE': '1'}.items()))

    def invoke(label, extra):
        command = [sys.executable, '-I', '-B', '-X', 'utf8', str(kit / 'run_environment_check.py'), '--python', sys.executable] + extra
        run = subprocess.run(command, capture_output=True, timeout=60)
        (out / (label + '.stdout.txt')).write_bytes(run.stdout)
        (out / (label + '.stderr.txt')).write_bytes(run.stderr)
        (out / (label + '.process.json')).write_text(json.dumps({'command': command, 'exit_code': run.returncode}, indent=2) + '\n')
        return run

    result_root = out / 'results'
    run = invoke('missing-validator', ['--results-root', str(result_root), '--run-id', 'packaging-validator-probe-001'])
    result_dir = result_root / 'packaging-validator-probe-001'
    result = json.loads((result_dir / 'run-result.json').read_text())
    check('actual_authoring_validator_failure_retained', run.returncode == 2 and result['status'] == 'blocked_or_failed' and result['validator_probe_started'] and not result['frozen_checker_started'])
    check('no_fallback_no_live_run', result['passed_checks'] is None and result['model_api_calls'] == 0 and result['token_count_api_calls'] == 0 and result['execution_ready'] is False)
    with zipfile.ZipFile(result_root / 'packaging-validator-probe-001.zip') as archive:
        check('failed_probe_result_ZIP_valid', archive.testzip() is None)
    existing = tree(result_root)
    rerun = invoke('existing-id', ['--results-root', str(result_root), '--run-id', 'packaging-validator-probe-001'])
    check('existing_run_id_refused_without_modification', rerun.returncode == 2 and tree(result_root) == existing)
    inside = invoke('inside-kit', ['--results-root', str(kit / 'forbidden-results')])
    check('output_inside_kit_refused_before_creation', inside.returncode == 2 and not (kit / 'forbidden-results').exists())
    check('untampered_kit_remains_byte_identical', tree(kit) == baseline)
    tampered = out / 'tampered-repo'
    shutil.copytree(repo, tampered)
    changed = tampered / 'stage3/execution-bindings/stage3-preparation-001-binding-001/prompts/proposal.txt'
    changed.write_bytes(changed.read_bytes() + b'\nPackage test: deliberate change.\n')
    tamper = invoke('changed-target', ['--repo', str(tampered), '--results-root', str(result_root), '--run-id', 'packaging-target-mismatch-001'])
    mismatch = json.loads((result_root / 'packaging-target-mismatch-001/run-result.json').read_text())
    check('changed_target_refused_before_validator_or_checker', tamper.returncode == 2 and mismatch.get('error') == 'frozen_target_hash_mismatch' and not mismatch['validator_probe_started'] and not mismatch['frozen_checker_started'])
    check('all_package_check_records_keep_execution_unready', all(json.loads(p.read_text())['execution_ready'] is False for p in result_root.rglob('run-result.json')))
    report = {'record_type': 'local_package_checks_not_Windows_environment_result',
              'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'python_executable': sys.executable,
              'python_version': sys.version, 'zip_sha256': digest(zip_path),
              'checks': checks, 'passed_checks': sum(x['passed'] for x in checks),
              'status': 'passed_package_checks', 'actual_validator_probe': result,
              'Windows_CMD_executed': False, 'new_code_exact_validator_check_performed': False,
              'model_api_calls': 0, 'token_count_api_calls': 0,
              'official_state_store_writes': 0, 'execution_ready': False,
              'interpretation': 'A retained validator failure is the expected package test outcome, not successful schema validation.'}
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'passed_checks': report['passed_checks'], 'report': str(out / 'report.json')}))


if __name__ == '__main__':
    main()
