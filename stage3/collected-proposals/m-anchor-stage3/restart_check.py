"""Verify local store persistence across real CLI process exits, without API calls.

The raw proposals are the same preserved shared-conversation transcriptions used
by replay.py. This verifies the local integration, not the original model runs.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone

from gate import GateError, Store, canonical_json
from replay import MANIFEST, ROOT, checked_file, load_dataset, sha256, write_json


def check_restart(manifest_path: Path, out: Path) -> dict:
    manifest_path = manifest_path.resolve()
    out = out.resolve()
    manifest, manifest_raw, authority, records = load_dataset(manifest_path)
    by_id = {trial["trial_id"]: (trial, raw) for trial, raw in records}
    required = ("PI-05-T1", "PI-05-T2", "PI-09-T1")
    if any(trial_id not in by_id for trial_id in required):
        raise GateError("Restart check requires PI-05-T1, PI-05-T2 and PI-09-T1")
    authority_raw = checked_file(manifest_path.parent, manifest["authority_file"], manifest["authority_sha256"])
    if out.exists():
        raise GateError("Output directory already exists; choose a new path to preserve prior results")
    out.mkdir(parents=True)
    inputs = out / "inputs"
    inputs.mkdir()
    authority_file = inputs / "authority.json"
    authority_file.write_bytes(authority_raw)
    for trial_id in required:
        (inputs / f"{trial_id}.json").write_bytes(by_id[trial_id][1])
    database = out / "persistent.sqlite3"
    trace = {
        "schema_version": "m-anchor-stage3-restart/v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "manifest_sha256": sha256(manifest_raw),
        "authority_sha256": manifest["authority_sha256"],
        "raw_sha256": {trial_id: sha256(by_id[trial_id][1]) for trial_id in required},
        "scope": "Real local CLI process restarts. No model or API calls. This does not authenticate or recreate the original model-session restart.",
        "steps": [],
        "passed": False,
    }

    def run(label: str, *arguments: str) -> dict:
        command = [sys.executable, str(ROOT / "replay.py"), *map(str, arguments)]
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, encoding="utf-8")
        try:
            stdout, stderr = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            trace["steps"].append({"label": label, "argv": command, "launcher_pid": process.pid,
                                   "returncode": process.returncode, "stdout": stdout,
                                   "stderr": stderr, "timeout": True})
            write_json(out / "restart-trace.json", trace)
            raise GateError(f"Restart subprocess timed out: {label}")
        entry = {"label": label, "argv": command, "launcher_pid": process.pid,
                 "returncode": process.returncode, "stdout": stdout, "stderr": stderr}
        trace["steps"].append(entry)
        write_json(out / "restart-trace.json", trace)
        if process.returncode != 0:
            raise GateError(f"Restart subprocess failed: {label}; see restart-trace.json")
        result = json.loads(stdout)
        # Windows virtual-environment executables may launch a child interpreter;
        # keep both observed IDs instead of assuming the wrapper is Python itself.
        runtime_pid = result.get("process_id")
        if type(runtime_pid) is not int or runtime_pid <= 0 or runtime_pid == os.getpid():
            raise GateError(f"Invalid subprocess runtime PID: {label}")
        entry["pid"] = runtime_pid
        entry["result"] = result
        return result

    def authority_snapshot() -> dict:
        # Each read also closes its connection before the next child starts.
        with Store(database) as store:
            return store.authority_snapshot()

    run("initialize", "init", "--authority", authority_file, "--db", database)
    before = authority_snapshot()
    pi05_before = run("PI-05 before rejection", "snapshot", "--db", database, "--case", "PI-05")["state"]
    rejected = run("PI-05-T1 reject", "apply", "--db", database, "--case", "PI-05", "--raw", inputs / "PI-05-T1.json")
    pi05_reloaded = run("PI-05 reload after rejection", "snapshot", "--db", database, "--case", "PI-05")["state"]
    after_reject = authority_snapshot()
    noop = run("PI-05-T2 no-op in new process", "apply", "--db", database, "--case", "PI-05", "--raw", inputs / "PI-05-T2.json")
    pi05_after = run("PI-05 reload after no-op", "snapshot", "--db", database, "--case", "PI-05")["state"]
    after_noop = authority_snapshot()
    pi09_before = run("PI-09 before commit", "snapshot", "--db", database, "--case", "PI-09")["state"]
    accepted = run("PI-09-T1 commit", "apply", "--db", database, "--case", "PI-09", "--raw", inputs / "PI-09-T1.json")
    pi09_after = run("PI-09 reload after commit", "snapshot", "--db", database, "--case", "PI-09")["state"]
    after_commit = authority_snapshot()
    stale = run("PI-09 same old proposal after restart", "apply", "--db", database, "--case", "PI-09", "--raw", inputs / "PI-09-T1.json")
    pi09_final = run("PI-09 reload after stale rejection", "snapshot", "--db", database, "--case", "PI-09")["state"]
    final = authority_snapshot()
    with closing(sqlite3.connect(database)) as connection:
        audit = connection.execute("SELECT raw,raw_sha256 FROM audit ORDER BY id").fetchall()
    expected_raws = [by_id[trial_id][1] for trial_id in (*required, "PI-09-T1")]
    expected_commit_hash = hashlib.sha256(canonical_json({k: v for k, v in pi09_after.items() if k != "state_hash"}).encode()).hexdigest()
    checks = {
        "separate_processes_completed": all(step["returncode"] == 0 and step["result"]["process_id"] == step["pid"] for step in trace["steps"]),
        "summary_rejected": rejected["decision"] == "reject" and rejected["reason"] == "evidence_unknown",
        "rejection_preserves_all_authority": before == after_reject and pi05_before == pi05_reloaded,
        "no_op_after_restart": noop["decision"] == "no_commit" and noop["reason"] == "no_state_change",
        "no_op_preserves_all_authority": before == after_noop and pi05_before == pi05_after,
        "valid_update_committed": accepted["decision"] == "commit" and accepted["reason"] == "accepted",
        "valid_update_persisted": pi09_after == accepted["after"] and pi09_after["candidates"] == ["h_B"] and pi09_after["cause_status"] == "resolved" and pi09_after["version"] == 2 and pi09_after["state_hash"] == expected_commit_hash and pi09_after["state_hash"] != pi09_before["state_hash"],
        "commit_preserves_evidence_authority": all(before[key] == after_commit[key] for key in ("evidence", "admissions", "interpretations", "schema_version")),
        "commit_preserves_other_cases": [state for state in before["cases"] if state["case_id"] != "PI-09"] == [state for state in after_commit["cases"] if state["case_id"] != "PI-09"],
        "stale_proposal_rejected_after_restart": stale["decision"] == "reject" and stale["reason"] == "version_mismatch" and pi09_final == pi09_after and final == after_commit,
        "exact_raw_bytes_audited": len(audit) == len(expected_raws) and all(row[0] == raw and row[1] == sha256(raw) for row, raw in zip(audit, expected_raws)),
        "source_inputs_unchanged": all(checked_file(manifest_path.parent, by_id[trial_id][0]["raw_file"], by_id[trial_id][0]["raw_sha256"]) == by_id[trial_id][1] for trial_id in required),
    }
    trace.update(checks=checks, before=before, after_reject=after_reject, after_noop=after_noop,
                 after_commit=after_commit, final=final, audit_count=len(audit), passed=all(checks.values()))
    write_json(out / "restart-trace.json", trace)
    return trace


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = check_restart(args.manifest, args.out)
        print(json.dumps({"passed": result["passed"], "checks": result["checks"], "processes": len(result["steps"])}))
        return 0 if result["passed"] else 1
    except (GateError, OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        print(f"Restart check error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
