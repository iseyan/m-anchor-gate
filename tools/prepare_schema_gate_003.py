"""Check installation for a future schema-gate-003; do not validate schemas."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "stage3/schema-gates/schema-gate-003-preparation/preparation-plan.v0.1.json"
REQUIREMENTS = PLAN.parent / "requirements.txt"


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def run_command(label, command, output, records, timeout=240):
    started = now()
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        timed_out = True
    (output / (label + ".stdout.txt")).write_bytes(stdout)
    (output / (label + ".stderr.txt")).write_bytes(stderr)
    record = {"step": label, "command": command, "started_at_utc": started,
              "ended_at_utc": now(), "pid": process.pid, "process_exit_code": process.returncode,
              "timed_out": timed_out, "exit_code": 124 if timed_out else process.returncode,
              "stdout": label + ".stdout.txt", "stderr": label + ".stderr.txt"}
    records.append(record)
    if record["exit_code"]:
        raise RuntimeError(label + " failed with exit code " + str(record["exit_code"]))
    return stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError("Write preparation output outside the checked-out repository.")
    output.mkdir(parents=True, exist_ok=False)
    plan = json.loads(PLAN.read_bytes())
    commands = []
    files_before = {}
    report = {
        "record_type": "schema_gate_003_environment_preparation",
        "started_at_utc": now(), "status": "preparing", "model_api_calls": 0,
        "state_store_writes": 0, "schema_gate_003_started": False,
        "schemas_checked": 0, "instances_checked": 0,
        "schema_validation_performed": False, "check_schema_called": False,
        "official_run_form_frozen": False, "execution_ready": False,
        "stage3_complete": False, "stage4_started": False,
        "required_validator": plan["required_validator"],
        "plan_sha256": digest(PLAN), "requirements_sha256": digest(REQUIREMENTS),
        "script_sha256": digest(Path(__file__)), "source_basis_commit": plan["source_basis_commit"],
        "host_python": sys.version, "platform": platform.platform(),
        "github": {key: os.environ.get(key) for key in [
            "GITHUB_ACTIONS", "GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_RUN_ID",
            "GITHUB_RUN_ATTEMPT", "GITHUB_WORKFLOW", "GITHUB_JOB", "RUNNER_OS", "RUNNER_ARCH"]},
        "runner_image": {key: os.environ.get(key) for key in ["ImageOS", "ImageVersion"]},
        "environment_persistence": "The hosted runner is ephemeral; verify installation again in the future validation job.",
    }
    write_json(output / "preparation-start.json", report)
    exit_code = 2
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        report["checked_out_commit"] = head
        if os.environ.get("GITHUB_SHA") and head != os.environ["GITHUB_SHA"]:
            raise ValueError("Checked-out commit differs from the triggering commit.")
        for item in plan["source_files"]:
            path = ROOT / item["path"]
            actual = digest(path)
            files_before[item["path"]] = actual
            if actual != item["sha256"]:
                raise ValueError("Source hash mismatch: " + item["path"])
        rows = json.loads((ROOT / plan["instances"]["path"]).read_bytes())
        report["target_inventory"] = {
            "schemas": len(plan["schemas"]), "instances": len(rows),
            "expected_valid": sum(row["expected_valid"] is True for row in rows),
            "expected_invalid": sum(row["expected_valid"] is False for row in rows),
            "note": "Inventory only; no instance was schema-validated.",
        }
        if (len(rows), report["target_inventory"]["expected_valid"],
                report["target_inventory"]["expected_invalid"]) != (82, 81, 1):
            raise ValueError("Saved fixture inventory differs from the fixed plan.")
        environment = output.parent / (output.name + "-venv")
        if environment.exists():
            raise FileExistsError("Use a new environment directory for each attempt.")
        run_command("01-create-venv", [sys.executable, "-m", "venv", str(environment)], output, commands)
        executable = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run_command("02-install", [str(executable), "-m", "pip", "install", "--no-input",
                    "--disable-pip-version-check", "--index-url", "https://pypi.org/simple",
                    "--only-binary=:all:", "--report", str(output / "pip-install-report.json"),
                    "-r", str(REQUIREMENTS)], output, commands)
        probe = """import importlib.metadata as m, json, sys
from jsonschema import Draft202012Validator
version = m.version('jsonschema')
if version != '4.26.0':
    raise RuntimeError('Unexpected jsonschema version: ' + version)
names = ['jsonschema', 'referencing', 'jsonschema-specifications', 'attrs', 'rpds-py']
print(json.dumps({'validator_version': version,
    'validator_class': Draft202012Validator.__module__ + '.' + Draft202012Validator.__name__,
    'python_version': sys.version, 'executable': sys.executable,
    'prefix': sys.prefix, 'base_prefix': sys.base_prefix,
    'packages': {name: m.version(name) for name in names},
    'validation_performed': False}))
"""
        raw = run_command("03-import-and-version", [str(executable), "-I", "-c", probe], output, commands)
        report["installed_environment"] = json.loads(raw)
        freeze = run_command("04-freeze", [str(executable), "-m", "pip", "freeze", "--all"], output, commands)
        (output / "requirements-observed.txt").write_bytes(freeze)
        report["status"] = "installation_and_import_confirmed"
        report["preparation_check_passed"] = True
        exit_code = 0
    except Exception as error:
        report.update(status="preparation_blocked_or_failed", preparation_check_passed=False,
                      error_type=type(error).__name__, error=str(error))
    finally:
        changed = [path for path, before in files_before.items()
                   if not (ROOT / path).is_file() or digest(ROOT / path) != before]
        report["source_integrity"] = {"files_checked": len(files_before), "changed_or_missing": changed,
                                       "sha256_before": files_before}
        if changed:
            report.update(status="preparation_blocked_or_failed", preparation_check_passed=False,
                          integrity_error="A fixed source file changed during preparation.")
            exit_code = 2
        report.update(ended_at_utc=now(), exit_code=exit_code, commands=commands)
        write_json(output / "preparation-result.json", report)
        sums = [digest(path) + "  " + path.name for path in sorted(output.iterdir()) if path.is_file()]
        (output / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "exit_code": exit_code,
                          "schema_gate_003_started": False, "output": str(output)}))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
