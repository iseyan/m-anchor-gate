"""Check the frozen binding offline; never install packages or start a live run."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import subprocess
import sys
import time
import traceback
import uuid
import zipfile

KIT = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def block_network(event, args):
    if event in {'socket.connect', 'socket.getaddrinfo'}:
        raise RuntimeError('environment_check_network_disabled')


def child_env():
    # Pass only OS bootstrap variables; no API credentials or Python overrides.
    allowed = {'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH', 'COMSPEC',
               'PATHEXT', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'HOME',
               'LANG', 'LC_ALL'}
    env = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    env.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1')
    return env


def inspect_files(base, entries):
    rows = []
    for item in entries:
        path = (base / item['path']).resolve()
        if not path.is_relative_to(base):
            raise ValueError('manifest_path_outside_root:' + item['path'])
        observed = sha(path) if path.is_file() else None
        rows.append({'path': item['path'], 'expected_sha256': item['sha256'],
                     'observed_sha256': observed, 'matches': observed == item['sha256']})
    return rows


def process(command, out, label, timeout):
    write_json(out / (label + '.command.json'),
               {'command': command, 'cwd': str(out), 'started_at_utc': now(),
                'timeout_seconds': timeout, 'shell': False,
                'environment_policy': 'OS allowlist; UTF-8; no credential variables'})
    record = {'started_at_utc': now(), 'pid': None, 'exit_code': None, 'timed_out': False}
    begin = time.monotonic()
    with (out / (label + '.stdout.txt')).open('xb') as stdout, (out / (label + '.stderr.txt')).open('xb') as stderr:
        try:
            proc = subprocess.Popen(command, cwd=out, env=child_env(), stdout=stdout, stderr=stderr)
            record['pid'] = proc.pid
            try:
                record['exit_code'] = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                record['timed_out'] = True
                proc.kill()
                record['exit_code'] = proc.wait()
        except OSError as error:
            record.update(launch_error_type=type(error).__name__, launch_error=str(error))
    record.update(ended_at_utc=now(), elapsed_seconds=round(time.monotonic() - begin, 6))
    write_json(out / (label + '.process.json'), record)
    return record


def path_identity(value):
    return str(PureWindowsPath(value)).casefold() if os.name == 'nt' else str(Path(value).resolve())


def finalize_archive(out):
    members = sorted(path for path in out.rglob('*') if path.is_file())
    with (out / 'SHA256SUMS.txt').open('x', encoding='utf-8', newline='\n') as stream:
        for path in members:
            stream.write(sha(path) + '  ' + path.relative_to(out).as_posix() + '\n')
    archive = out.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(out.rglob('*')):
            if path.is_file():
                bundle.write(path, out.name + '/' + path.relative_to(out).as_posix())
    with archive.with_suffix('.zip.sha256').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(sha(archive) + '  ' + archive.name + '\n')
    return archive


def main():
    sys.addaudithook(block_network)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', help='Interpreter to check. Default: the recorded schema-gate-003 venv.')
    parser.add_argument('--repo', type=Path, help='Pinned repository source root, if not using the ZIP.')
    parser.add_argument('--results-root', type=Path)
    parser.add_argument('--run-id', help='New record ID; an existing directory is never reused.')
    args = parser.parse_args()
    plan = read_json(KIT / 'environment-check-plan.json')
    repo = (args.repo or KIT / 'targets/repo').resolve()
    results_root = (args.results_root or KIT.parent / 'stage3-environment-check-results').resolve()
    if results_root.is_relative_to(KIT) or results_root.is_relative_to(repo):
        parser.error('results must be outside the kit and source repository')
    run_id = args.run_id or ('environment-check-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,95}', run_id):
        parser.error('run ID must contain only ASCII letters, digits, hyphens or underscores')
    out = results_root / run_id
    if out.with_suffix('.zip').exists() or out.with_suffix('.zip.sha256').exists():
        parser.error('result archive already exists; choose a new ID')
    try:
        out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error('result directory already exists; choose a new ID')
    requested_python = args.python or plan['preferred_python_executable']
    python = Path(str(PureWindowsPath(requested_python)) if os.name == 'nt' else requested_python)
    if not python.is_absolute():
        python = python.absolute()
    # Do not resolve a venv symlink to its base interpreter.
    write_json(out / 'run-start.json', {
        'record_type': 'offline_environment_check_start', 'run_id': run_id,
        'started_at_utc': now(), 'launcher_pid': os.getpid(),
        'context_id': plan['context_id'], 'basis_commit': plan['basis_commit'],
        'kit_path': str(KIT), 'repo_path': str(repo), 'result_path': str(out),
        'requested_python': str(python), 'python_override_supplied': args.python is not None,
        'plan_sha256': sha(KIT / 'environment-check-plan.json'),
        'tool_manifest_sha256': sha(KIT / 'tool-manifest.json'),
        'target_manifest_sha256': sha(KIT / 'target-manifest.json'),
        'conditions_sha256': plan['conditions_sha256'],
        'runtime_manifest_sha256': plan['runtime_manifest_sha256'],
        'mode': 'exact_jsonschema', 'execution_ready': False,
        'live_run_started': False, 'model_api_calls': 0, 'token_count_api_calls': 0,
        'github_actions_used': False, 'schema_gate_003_rerun': False})
    result = {'record_type': 'offline_environment_check_result', 'run_id': run_id,
              'status': 'blocked_or_failed', 'validator_probe_started': False,
              'frozen_checker_started': False, 'new_code_check_passed': False,
              'passed_checks': None, 'external_schema_conformance_verified': False,
              'model_api_calls': 0, 'token_count_api_calls': 0, 'http_inference_requests': 0,
              'official_run_state_store_writes': 0, 'spend_incurred_usd': '0.00',
              'execution_ready': False, 'live_run_started': False,
              'preparation_evaluation_complete': False, 'stage3_complete': False,
              'stage4_started': False, 'schema_gate_003_rerun': False,
              'scope': 'Pinned binding with offline fixtures; no live inputs or model outputs tested.'}
    tool_entries = target_entries = None
    try:
        tool_entries = read_json(KIT / 'tool-manifest.json')['files']
        before_tools = inspect_files(KIT, tool_entries)
        write_json(out / 'tool-hashes.before.json', before_tools)
        if not before_tools or not all(row['matches'] for row in before_tools):
            raise RuntimeError('tool_hash_mismatch')
        target_entries = read_json(KIT / 'target-manifest.json')['files']
        before_targets = inspect_files(repo, target_entries)
        write_json(out / 'target-hashes.before.json', before_targets)
        if not before_targets or not all(row['matches'] for row in before_targets):
            raise RuntimeError('frozen_target_hash_mismatch')
        if not python.is_file():
            raise RuntimeError('requested_python_executable_not_found')
        result['validator_probe_started'] = True
        probe_process = process([str(python), '-I', '-B', '-X', 'utf8', str(KIT / 'probe_environment.py')], out, 'validator-probe', 60)
        try:
            probe = read_json(out / 'validator-probe.stdout.txt')
        except (ValueError, UnicodeError):
            raise RuntimeError('validator_probe_did_not_return_JSON')
        write_json(out / 'environment.json', probe)
        result['same_executable_path_as_003'] = path_identity(probe['python_executable']) == path_identity(plan['preferred_python_executable'])
        result['same_prefix_path_as_003'] = path_identity(probe['python_prefix']) == path_identity(plan['recorded_003_python_prefix'])
        if (probe_process['exit_code'] != 0 or probe.get('validator_ready') is not True
                or probe.get('validator_version') != '4.26.0'
                or probe.get('validator_class') != 'jsonschema.validators.Draft202012Validator'):
            raise RuntimeError('specified_validator_not_ready; no structural fallback or installation attempted')
        script = repo / plan['checker_path']
        result['frozen_checker_started'] = True
        checker_process = process([str(python), '-B', '-X', 'utf8', str(script), '--output', str(out / 'binding-check')], out, 'binding-check', 420)
        report_path = out / 'binding-check/report.json'
        if not report_path.is_file():
            raise RuntimeError('checker_report_missing')
        report = read_json(report_path)
        checks = report.get('checks', [])
        result.update(checker_report_sha256=sha(report_path), checker_exit_code=checker_process['exit_code'],
                      passed_checks=report.get('passed_checks'), check_count=len(checks))
        checks_pass = (checker_process['exit_code'] == 0 and not checker_process['timed_out']
                      and report.get('status') == 'passed_offline_checks'
                      and report.get('mode') == 'exact_jsonschema'
                      and report.get('validation') == 'jsonschema_4.26.0_Draft202012Validator'
                      and report.get('external_schema_conformance_verified') is True
                      and report.get('runtime_manifest_sha256') == plan['runtime_manifest_sha256']
                      and len(checks) == plan['expected_exact_mode_check_count']
                      and report.get('passed_checks') == len(checks)
                      and all(row.get('passed') is True for row in checks)
                      and report.get('model_api_calls') == 0 and report.get('http_requests') == 0
                      and report.get('official_state_store_writes') == 0
                      and report.get('execution_ready') is False)
        if not checks_pass:
            raise RuntimeError('frozen_checker_did_not_complete_exact_mode_checks')
        result.update(status='passed_offline_environment_check', new_code_check_passed=True,
                      external_schema_conformance_verified=True)
    except Exception as error:
        result.update(error_type=type(error).__name__, error=str(error))
        with (out / 'failure-traceback.txt').open('x', encoding='utf-8') as stream:
            stream.write(traceback.format_exc())
    finally:
        unchanged = tool_entries is not None and target_entries is not None
        for label, base, entries in [('tool', KIT, tool_entries), ('target', repo, target_entries)]:
            if entries is not None:
                try:
                    after = inspect_files(base, entries)
                    write_json(out / (label + '-hashes.after.json'), after)
                    unchanged = unchanged and bool(after) and all(row['matches'] for row in after)
                except Exception as error:
                    unchanged = False
                    result[label + '_after_hash_error'] = str(error)
        result['source_hashes_match_after'] = unchanged
        if not unchanged:
            result.update(status='blocked_or_failed', new_code_check_passed=False,
                          external_schema_conformance_verified=False)
        result['temporary_fixture_store_writes'] = 'see_binding_check_records' if result['frozen_checker_started'] else 'not_started'
        result['ended_at_utc'] = now()
        write_json(out / 'run-result.json', result)
    archive = finalize_archive(out)
    print(json.dumps({'status': result['status'], 'result_zip': str(archive), 'execution_ready': False}, ensure_ascii=False))
    return 0 if result['new_code_check_passed'] else 2


if __name__ == '__main__':
    sys.exit(main())
