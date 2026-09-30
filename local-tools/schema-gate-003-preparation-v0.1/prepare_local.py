"""Check validator installation locally; do not run schema-gate-003 validation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import uuid


ROOT = Path(__file__).resolve().parent
PLAN = ROOT / "preparation-plan.json"
REQUIREMENTS = ROOT / "requirements.txt"


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def run_step(label, command, output, records):
    stdout_path = output / (label + ".stdout.txt")
    stderr_path = output / (label + ".stderr.txt")
    record = {"step": label, "command": command, "started_at_utc": now(),
              "stdout": stdout_path.name, "stderr": stderr_path.name,
              "pid": None, "exit_code": None, "timed_out": False}
    records.append(record)
    try:
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            process = subprocess.Popen(command, cwd=ROOT, stdout=stdout, stderr=stderr)
            record["pid"] = process.pid
            try:
                code = process.wait(timeout=300)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                record["timed_out"] = True
                code = 124
            record["process_exit_code"] = process.returncode
            record["exit_code"] = code
    except Exception as error:
        record["launch_error"] = str(error)
        raise
    finally:
        record["ended_at_utc"] = now()
    if record["exit_code"] != 0:
        raise RuntimeError(label + " failed: exit " + str(record["exit_code"]))
    return stdout_path.read_bytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspect-only", action="store_true",
                        help="Check packaged targets only; do not create a venv or install packages.")
    parser.add_argument("--output-root", type=Path, default=ROOT / "runs")
    args = parser.parse_args()
    run_id = "local-preparation-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    output = args.output_root.resolve() / run_id
    output.mkdir(parents=True, exist_ok=False)
    report = {"record_type": "schema_gate_003_local_preparation", "run_id": run_id,
              "started_at_utc": now(), "status": "started", "inspect_only": args.inspect_only,
              "schema_gate_003_started": False, "schema_validation_performed": False,
              "schemas_checked": 0, "instances_checked": 0, "model_api_calls": 0,
              "state_store_writes": 0, "official_run_form_frozen": False,
              "execution_ready": False, "stage3_complete": False, "stage4_started": False,
              "installation_confirmed": False, "host_python": sys.version,
              "host_executable": sys.executable, "platform": platform.platform(),
              "commands": []}
    save_json(output / "preparation-start.json", report)
    before = {}
    exit_code = 2
    try:
        if sys.version_info < (3, 10):
            raise RuntimeError("Use Python 3.10 or newer.")
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        report.update(source_basis_commit=plan["source_basis_commit"],
                      required_validator=plan["required_validator"], plan_sha256=digest(PLAN),
                      script_sha256=digest(Path(__file__)), requirements_sha256=digest(REQUIREMENTS))
        if REQUIREMENTS.read_text(encoding="utf-8").strip() != "jsonschema==4.26.0":
            raise ValueError("Requirements differ from the specified validator version.")
        for entry in plan["source_files"]:
            path = (ROOT / entry["package_path"]).resolve()
            if ROOT not in path.parents:
                raise ValueError("Target path leaves the package directory.")
            actual = digest(path)
            before[entry["package_path"]] = actual
            if actual != entry["sha256"]:
                raise ValueError("Target hash mismatch: " + entry["package_path"])
        rows = json.loads((ROOT / plan["instances"]["package_path"]).read_text(encoding="utf-8"))
        inventory = {"schemas": len(plan["schemas"]), "instances": len(rows),
                     "expected_valid": sum(row["expected_valid"] is True for row in rows),
                     "expected_invalid": sum(row["expected_valid"] is False for row in rows)}
        if inventory != {"schemas": 4, "instances": 82, "expected_valid": 81, "expected_invalid": 1}:
            raise ValueError("Target inventory differs from the saved plan.")
        report["target_inventory_only"] = inventory
        if args.inspect_only:
            report["status"] = "packaged_targets_confirmed_only"
        else:
            environment = ROOT / "environments" / run_id
            if environment.exists():
                raise FileExistsError("Use a new environment for each preparation attempt.")
            print("Creating a fresh local environment...", flush=True)
            run_step("01-create-venv", [sys.executable, "-m", "venv", str(environment)], output, report["commands"])
            executable = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            print("Installing jsonschema==4.26.0 from PyPI...", flush=True)
            run_step("02-install", [str(executable), "-m", "pip", "install", "--no-input",
                     "--disable-pip-version-check", "--index-url", "https://pypi.org/simple",
                     "--only-binary=:all:", "--report", str(output / "pip-install-report.json"),
                     "-r", str(REQUIREMENTS)], output, report["commands"])
            probe = """import importlib.metadata as m, json, sys
from jsonschema import Draft202012Validator
version = m.version('jsonschema')
if version != '4.26.0':
    raise RuntimeError('Unexpected validator version: ' + version)
print(json.dumps({'validator_version': version,
    'validator_class': Draft202012Validator.__module__ + '.' + Draft202012Validator.__name__,
    'python_version': sys.version, 'executable': sys.executable,
    'prefix': sys.prefix, 'base_prefix': sys.base_prefix,
    'schema_validation_performed': False}))
"""
            raw = run_step("03-import-and-version", [str(executable), "-I", "-c", probe], output, report["commands"])
            report["installed_environment"] = json.loads(raw)
            versions = run_step("04-freeze", [str(executable), "-m", "pip", "freeze", "--all"], output, report["commands"])
            (output / "requirements-observed.txt").write_bytes(versions)
            report.update(status="installation_and_import_confirmed", installation_confirmed=True)
        exit_code = 0
    except Exception as error:
        report.update(status="blocked_or_failed", error_type=type(error).__name__, error=str(error))
    finally:
        after = {name: digest(ROOT / name) if (ROOT / name).is_file() else None for name in before}
        changed = [name for name, value in before.items() if after[name] != value]
        report["source_integrity"] = {"sha256_before": before, "sha256_after": after,
                                       "changed_or_missing": changed}
        if changed:
            report.update(status="blocked_or_failed", installation_confirmed=False,
                          integrity_error="A packaged target changed during preparation.")
            exit_code = 2
        report.update(ended_at_utc=now(), exit_code=exit_code)
        save_json(output / "preparation-result.json", report)
        sums = [digest(p) + "  " + p.name for p in sorted(output.iterdir()) if p.is_file()]
        (output / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")
        print("Status: " + report["status"])
        print("Record: " + str(output / "preparation-result.json"))
        print("Schema-gate-003 validation has not been run.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
