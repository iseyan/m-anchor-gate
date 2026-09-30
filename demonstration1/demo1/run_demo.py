"""Execute the frozen scenario and its inherited checks; grade outside the reader."""

import argparse
import hashlib
import json
import os
import platform
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(value):
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def launch(script, args):
    # No case data, model history, expected values, or stdin are inherited.
    env = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP")
           if key in os.environ}
    env["PYTHONUTF8"] = "1"
    command = [sys.executable, str(ROOT / script), *args]
    start = time.monotonic_ns()
    result = subprocess.run(command, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                            capture_output=True, text=True, encoding="utf-8", timeout=30)
    stopped = time.monotonic_ns()
    if result.returncode != 0:
        raise RuntimeError(f"{script} failed ({result.returncode}): {result.stderr}")
    payload = json.loads(result.stdout)
    process = payload.get("reader_process", payload.get("writer_process"))
    return payload, {"argv": command, "environment_keys": sorted(env),
                     "stdin": "DEVNULL", "returncode": result.returncode,
                     "started_monotonic_ns": start, "returned_monotonic_ns": stopped,
                     "process": process, "stderr": result.stderr}


def inspect_records(store):
    with sqlite3.connect(store.as_uri() + "?mode=ro", uri=True) as con:
        return [{"seq": seq, "case_id": case, "kind": kind, "record_id": rid,
                 "version": ver, "payload": json.loads(payload)}
                for seq, case, kind, rid, ver, payload in
                con.execute("SELECT seq,case_id,kind,record_id,version,payload FROM records ORDER BY seq")]


def evaluate(records, lifecycle):
    def items(case, kind):
        return [r["payload"] for r in records if r["case_id"] == case and r["kind"] == kind]

    def case_check(case, candidates, evidence, status, decision):
        states, actions, summaries, judgments = [items(case, k) for k in ("state", "action", "summary", "decision")]
        audit = [a for a in items(case, "audit") if a["kind"] == "transition" and a["status"] == "accepted"]
        s, a, summary, j = states[-1], actions[-1], summaries[-1], judgments[-1]
        life = lifecycle[case]
        return {
            "versions_exactly_0_then_1": [x["state_version"] for x in states] == [0, 1],
            "initial_both_without_evidence": states[0]["K"] == ["h_A", "h_B"] and states[0]["evidence_basis"] == [],
            "retained_candidates": s["K"] == candidates,
            "evidence_basis": s["evidence_basis"] == evidence,
            "action_link": s["action_record_id"] == a["action_record_id"] == "action-001" and a["state_version"] == 1,
            "audit_link": len(audit) == 1 and audit[0]["audit_id"] == s["transition_audit_id"] == a["transition_audit_id"],
            "summary_is_not_evidence": summary["admitted_as_evidence"] is False and summary["state_version_at_save"] == 1,
            "summary_fixed": summary["text_ja"] == "暫定対応Bを選択した。",
            "normal_exit_before_restart": life["writer"]["returncode"] == 0 and life["writer"]["returned_monotonic_ns"] < life["reader"]["started_monotonic_ns"],
            "different_process_instances": life["writer"]["process"]["instance_id"] != life["reader"]["process"]["instance_id"],
            "writer_identity": life["writer"]["process"] == s["writer_process"] == j["state_writer_process"],
            "reader_identity": life["reader"]["process"] == j["reader_process"],
            "reader_case_inputs_only": life["reader"]["argv"][2:] == ["--store", life["store"], "--case-id", case],
            "exact_state_and_action_read": j["state_version_read"] == 1 and j["state_sha256"] == digest(s) and j["action_sha256"] == digest(a),
            "read_to_decision_link": j["K_read"] == candidates and j["evidence_basis"] == evidence and j["action_record_id"] == a["action_record_id"] and j["transition_audit_id"] == s["transition_audit_id"],
            "decision_uses_read_values": j["decision_inputs"] == {"K": candidates, "selected_action": a["selected_action"]},
            "summary_excluded_from_rule": j["summary_used_for_decision"] is False and j["summary_read"] == summary,
            "decision_status": j["status"] == status,
            "decision_wording": j["decision_ja"] == decision,
        }

    main = case_check("demo1-main", ["h_A", "h_B"], [], "unresolved", "a_Bは選択済み／原因A・Bは未決")
    control = case_check("demo1-control", ["h_B"], ["e_B"], "single_candidate_under_interpretation", "この証拠解釈ではBのみ保持")
    rejected = [a for a in items("demo1-rejections", "audit") if a.get("status") == "rejected"]
    rejection_checks = {
        "four_rejections_recorded": len(rejected) == 4,
        "expected_bases": [a["evidence_ids"] for a in rejected] == [[], ["unregistered-evidence"], ["action-001"], ["summary-001"]],
        "state_and_version_unchanged": bool(rejected) and all(a["state_before"] == a["state_after"] and a["state_after"]["state_version"] == 1 and a["state_after"]["K"] == ["h_A", "h_B"] for a in rejected),
        "proposal_reason_and_rule_recorded": bool(rejected) and all(a["proposal"]["proposed_K"] == ["h_B"] and a["rejection_reason"] and a["registry_version"] and a["rule_version"] for a in rejected),
        "no_extra_state_saved": [s["state_version"] for s in items("demo1-rejections", "state")] == [0, 1],
    }
    preservation_keys = ["versions_exactly_0_then_1", "initial_both_without_evidence", "retained_candidates", "evidence_basis", "summary_is_not_evidence", "summary_fixed"]
    criteria = {
        "1_preserve": all(main[key] for key in preservation_keys),
        "2_reject_and_log": all(rejection_checks.values()),
        "3_use_after_restart": all(main.values()),
        "4_evidence_control": all(control.values()),
    }
    return {"passed": all(criteria.values()), "criteria": criteria,
            "main_checks": main, "rejection_checks": rejection_checks, "control_checks": control}


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    store = (output / "demo1.sqlite3").resolve()
    lifecycle = {}
    for scenario, case in (("main", "demo1-main"), ("rejections", "demo1-rejections"), ("control", "demo1-control")):
        base = ["--store", str(store), "--case-id", case]
        _, writer = launch("writer.py", [*base, "--scenario", scenario])
        decision, reader = launch("reader.py", base)
        lifecycle[case] = {"store": str(store), "writer": writer, "reader": reader}
        write_json(output / f"{case}.decision.json", decision)
    records = inspect_records(store)
    (output / "records.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    write_json(output / "process-lifecycle.json", lifecycle)
    verdict = evaluate(records, lifecycle)
    write_json(output / "acceptance.json", verdict)
    sources = [*ROOT.glob("*.py"), *ROOT.glob("schemas/*.json"), *ROOT.glob("specs/*.md")]
    manifest = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)}
    write_json(output / "source-hashes.json", manifest)
    write_json(output / "environment.json", {
        "implementation_version": "demo1/v0.1", "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "python_executable": sys.executable, "platform": platform.platform(),
        "sqlite": sqlite3.sqlite_version, "reproduction": "python run_demo.py --output-dir results/new-run",
        "source_manifest_sha256": hashlib.sha256((output / "source-hashes.json").read_bytes()).hexdigest(),
        "network_used_by_demo": False, "model_api_used": False,
    })
    print(json.dumps({"passed": verdict["passed"], "criteria": verdict["criteria"], "output": str(output)}, indent=2))
    return 0 if verdict["passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    sys.exit(run(parser.parse_args().output_dir.resolve()))
