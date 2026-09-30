"""Run the unchanged schema validator in the already confirmed Windows venv.

This launcher is linked to local-preparation-20260930T102507Z-5db00b37.
It performs no installation and never writes to the preparation kit.
"""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import zipfile

KIT = Path(r"C:\Users\ise\Desktop\schema-gate-003-local-preparation-v0.1")
PREPARATION_ID = "local-preparation-20260930T102507Z-5db00b37"
PREPARATION_SHA256 = "f04a9b7a2a4660cde8d3b18ab3f967f827750957b4fd26c98c983e54cb0c6422"
PLAN_SHA256 = "dbb6a48620cd9b8d3f6cefb9a961fdef4b4aa6d6f8788e0aec61a7e42df49ef1"
SOURCE_SHA256 = {
    "schemas/decision.schema.json": "6ed201e6d3e6b731ae861f3ba041415b2f1085f7e6308b71eff4a5303f9fb81d",
    "schemas/input.schema.json": "a301da3af83adefd8932a4786045351ebf8e3a03a5d1273d3c8a792546afb5d1",
    "schemas/proposal.schema.json": "e1f4e6ed2143e6691963af81426c8497c492ab6e7b9578bb7d9d37daaf227176",
    "schemas/state.schema.json": "5da9fc4feb447f6e724c52f2e72e161c4a567671385a6b9845a334615be0a934",
    "validate_schemas.py": "d13701ac713323c58b7d809a273f2e2df48f54b24efc24c7460d1b52e2115230",
    "results/dev-001/schema-instances.json": "146461c25fedd2f2d584c430c6f9e8a83b074f45d4ab31c949755d6c1d8f5f06",
}
CRITERIA = [
    "specified jsonschema==4.26.0 / Draft202012Validator",
    "check_schema succeeds for all four target schemas",
    "all 82 classifications match saved expectations",
    "validation command exits with code 0",
]


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main():
    if os.name != "nt":
        print("This launcher is for the recorded Windows environment.")
        return 2
    run_id = "schema-gate-003-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    output = KIT.parent / "schema-gate-003-results" / run_id
    output.mkdir(parents=True, exist_ok=False)
    source = KIT / "targets" / "stage3" / "development-snapshot"
    result_path = KIT / "runs" / PREPARATION_ID / "preparation-result.json"
    report = {
        "record_type": "schema_gate_003_local_validation",
        "run_id": run_id, "started_at_utc": now(), "status": "started",
        "preparation_run_id": PREPARATION_ID,
        "preparation_result_sha256": PREPARATION_SHA256,
        "launcher_sha256": sha256(Path(__file__)),
        "python_executable": sys.executable, "python_version": sys.version,
        "python_prefix": sys.prefix, "python_base_prefix": sys.base_prefix,
        "schema_gate_003_started": False, "schema_gate_passed": False,
        "schema_gate_acceptance_unchanged": CRITERIA,
        "target_sha256_expected": SOURCE_SHA256,
        "schemas_checked": 0, "instances_checked": 0,
        "model_api_calls": 0, "state_store_writes": 0,
        "github_actions_used": False, "official_run_form_frozen": False,
        "execution_ready": False, "stage3_complete": False, "stage4_started": False,
        "scope": "Four fixed schemas and 82 saved development fixtures only.",
    }
    save(output / "run-start.json", report)
    exit_code = 2
    process = None
    try:
        if sha256(result_path) != PREPARATION_SHA256:
            raise ValueError("Preparation result differs from the received record.")
        with (output / "preparation-result.json").open("xb") as handle:
            handle.write(result_path.read_bytes())
        prepared = json.loads(result_path.read_text(encoding="utf-8"))
        if (prepared["run_id"] != PREPARATION_ID
                or prepared["status"] != "installation_and_import_confirmed"
                or prepared["installation_confirmed"] is not True
                or prepared["inspect_only"] is not False
                or prepared["exit_code"] != 0):
            raise ValueError("The linked preparation did not confirm installation.")
        expected_env = prepared["installed_environment"]
        if not Path(sys.executable).samefile(expected_env["executable"]):
            raise ValueError("Use the exact Python executable from the successful preparation.")
        if not Path(sys.prefix).samefile(expected_env["prefix"]) or sys.prefix == sys.base_prefix:
            raise ValueError("The prepared venv is not active.")
        report["same_prepared_venv_confirmed"] = True
        plan_path = KIT / "preparation-plan.json"
        if sha256(plan_path) != PLAN_SHA256:
            raise ValueError("The preparation plan has changed.")
        before = {name: sha256(source / name) for name in SOURCE_SHA256}
        report["target_sha256_before"] = before
        if before != SOURCE_SHA256:
            raise ValueError("A fixed validation target has changed.")
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        if plan["schema_gate_acceptance_unchanged"] != CRITERIA:
            raise ValueError("The recorded four criteria differ.")
        rows = json.loads((source / "results/dev-001/schema-instances.json").read_text(encoding="utf-8"))
        if len(rows) != 82:
            raise ValueError("The saved fixture inventory differs.")
        from jsonschema import Draft202012Validator
        report["installed_validator"] = {
            "distribution": "jsonschema", "version": importlib.metadata.version("jsonschema"),
            "class": Draft202012Validator.__module__ + "." + Draft202012Validator.__name__,
            "dialect": "2020-12",
        }
        if report["installed_validator"]["version"] != "4.26.0":
            raise ValueError("The specified validator version is not installed.")
        validation_report = output / "schema-validation.json"
        command = [sys.executable, "-I", "-B", "-X", "utf8",
                   str(source / "validate_schemas.py"),
                   "--instances", str(source / "results/dev-001/schema-instances.json"),
                   "--report", str(validation_report)]
        invocation = {"command": command, "cwd": str(output),
                      "started_at_utc": now(), "timeout_seconds": 300,
                      "stdout": "validation.stdout.txt", "stderr": "validation.stderr.txt",
                      "pid": None, "exit_code": None, "timed_out": False}
        save(output / "validation-command.json", invocation)
        with (output / "validation.stdout.txt").open("xb") as stdout, (output / "validation.stderr.txt").open("xb") as stderr:
            process = subprocess.Popen(command, cwd=output, stdout=stdout, stderr=stderr)
            invocation["pid"] = process.pid
            report["schema_gate_003_started"] = True
            save(output / "validation-started.json", {"run_id": run_id, "pid": process.pid, "at_utc": now()})
            try:
                invocation["exit_code"] = process.wait(timeout=300)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                invocation.update(timed_out=True, exit_code=124)
            except KeyboardInterrupt:
                process.kill()
                process.wait()
                invocation.update(interrupted=True, exit_code=130)
            finally:
                invocation.update(process_exit_code=process.returncode, ended_at_utc=now())
                save(output / "validation-process-result.json", invocation)
        report["validation_process"] = invocation
        checked = json.loads(validation_report.read_text(encoding="utf-8")) if validation_report.is_file() else {}
        schemas = checked.get("schemas", [])
        instances = checked.get("instances", [])
        expected_names = sorted(Path(name).name for name in SOURCE_SHA256 if name.startswith("schemas/"))
        criteria = {
            "specified_validator": checked.get("installed_version") == "4.26.0"
                and checked.get("validator") == "jsonschema.Draft202012Validator"
                and checked.get("dialect") == "2020-12",
            "four_schemas_check_schema": len(schemas) == 4
                and sorted(item["file"] for item in schemas) == expected_names
                and all(item["valid"] is True for item in schemas),
            "all_82_classifications_match": len(instances) == 82
                and all(item["id"] == row["id"] and item["valid"] is row["expected_valid"]
                        and item["expected_valid"] is row["expected_valid"]
                        for item, row in zip(instances, rows)),
            "validation_exit_zero": invocation["exit_code"] == 0,
        }
        report.update(criteria=criteria, schemas_checked=len(schemas), instances_checked=len(instances))
        if not all(criteria.values()):
            raise ValueError("The four existing schema-gate criteria were not all satisfied; retain the logs.")
        report.update(status="passed_for_listed_development_instances", schema_gate_passed=True)
        exit_code = 0
    except Exception as error:
        report.update(status="blocked_or_failed", schema_gate_passed=False,
                      error_type=type(error).__name__, error=str(error))
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        try:
            after = {name: sha256(source / name) if (source / name).is_file() else None for name in SOURCE_SHA256}
            report["target_sha256_after"] = after
            report["fixed_targets_unchanged"] = after == SOURCE_SHA256
            if after != SOURCE_SHA256:
                report.update(status="blocked_or_failed", schema_gate_passed=False,
                              integrity_error="A fixed target is missing or differs from its recorded hash.")
                exit_code = 2
        except Exception as error:
            report.update(status="blocked_or_failed", schema_gate_passed=False, integrity_error=str(error))
            exit_code = 2
        report.update(ended_at_utc=now(), exit_code=exit_code)
        save(output / "run-result.json", report)
        sums = [sha256(path) + "  " + path.name for path in sorted(output.iterdir()) if path.is_file()]
        with (output / "SHA256SUMS.txt").open("x", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(sums) + "\n")
        archive = output.with_suffix(".zip")
        with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
            for path in sorted(output.iterdir()):
                if path.is_file():
                    bundle.write(path, run_id + "/" + path.name)
        print("Status: " + report["status"])
        print("Validation report: " + str(output / "run-result.json"))
        print("Upload this ZIP: " + str(archive))
        print("Stage 3 is not complete. Stage 4 has not started.")
        try:
            os.startfile(str(output.parent))
        except OSError as error:
            print("Open the output folder manually: " + str(error))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
