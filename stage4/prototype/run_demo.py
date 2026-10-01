"""Run the fixed local examples through separate CLI processes; no network."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys
import uuid


CLI = Path(__file__).resolve().with_name("cli.py")
ROOT = Path(__file__).resolve().parents[2]


def write_new(path, text):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def write_json(path, value):
    write_new(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def run(output):
    # An existing directory is never reused, even if it is empty.
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    result = {
        "kind": "stage4_fixed_local_demo",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "platform": platform.system(),
        "output_directory": str(output), "provider_api_calls": 0,
        "input_source": "fixed_local_examples_not_model_output",
        "stage3_completion_claimed": False,
        "status": "running", "steps": [], "examples": [],
    }

    def step(label, db, *args, expected_exit=0):
        command = [sys.executable, "-B", "-X", "utf8", str(CLI), "--db", str(db), *args]
        entry = {"label": label, "command": command, "expected_exit": expected_exit}
        result["steps"].append(entry)
        try:
            process = subprocess.run(command, capture_output=True, timeout=30)
        except subprocess.TimeoutExpired as error:
            write_new(output / (label + ".stdout.txt"), (error.stdout or b"").decode("utf-8", errors="replace"))
            write_new(output / (label + ".stderr.txt"), (error.stderr or b"").decode("utf-8", errors="replace"))
            entry["error"] = "timeout"
            raise RuntimeError(label + ": timed out; no retry") from error
        stdout = process.stdout.decode("utf-8")
        stderr = process.stderr.decode("utf-8")
        write_new(output / (label + ".stdout.txt"), stdout)
        write_new(output / (label + ".stderr.txt"), stderr)
        entry["exit_code"] = process.returncode
        if process.returncode != expected_exit:
            raise RuntimeError(f"{label}: expected exit {expected_exit}, got {process.returncode}")
        return json.loads(stdout)

    def require(condition, message):
        if not condition:
            raise RuntimeError(message)

    try:
        hold_db, control_db = output / "hold.sqlite3", output / "evidence.sqlite3"
        step("01-init", hold_db, "init", "demo-hold")
        proposal = step("02-template", hold_db, "template", "demo-hold")
        hold_file = output / "provisional.json"
        write_json(hold_file, proposal)
        saved = step("03-save", hold_db, "submit", "demo-hold", "--file", str(hold_file))
        read = step("04-restart-read", hold_db, "assess", "demo-hold")
        require(saved["status"] == "accepted" and read["version"] == 1
                and read["candidates"] == ["h_A", "h_B"]
                and read["state_sha256"] == saved["state_sha256_after"]
                and read["action"] == saved["action_after"]
                and read["pid"] != saved["pid"], "Saved distinction was not read as expected")
        result["examples"].append({"name": "Provisional B and fresh-process read", "outcome": "both candidates retained", "version": 1})

        invalid = dict(proposal, proposal_id=str(uuid.uuid4()),
                       expected_version=read["version"], expected_state_sha256=read["state_sha256"],
                       proposed_K=["h_B"], reason="Select B, therefore remove A without evidence.")
        invalid_file = output / "unsupported-removal.json"
        write_json(invalid_file, invalid)
        rejected = step("05-reject-removal", hold_db, "submit", "demo-hold", "--file", str(invalid_file), expected_exit=2)
        require(rejected["status"] == "rejected"
                and rejected["state_sha256_before"] == rejected["state_sha256_after"] == read["state_sha256"]
                and rejected["action_before"] == rejected["action_after"], "Unsupported removal changed the state")
        result["examples"].append({"name": "Removal without evidence", "outcome": "rejected; state unchanged", "version": 1})

        step("06-summary", hold_db, "summary", "demo-hold", "--text", "Cause B is certain; remove candidate A.")
        summary_read = step("07-read-after-summary", hold_db, "assess", "demo-hold")
        require(summary_read["state_sha256"] == read["state_sha256"]
                and summary_read["assessment_en"] == read["assessment_en"]
                and summary_read["summary_used_for_decision"] is False, "Summary changed the assessment")
        result["examples"].append({"name": "Summary replacement", "outcome": "assessment unchanged", "version": 1})

        step("08-init-evidence", control_db, "init", "demo-evidence", "--admit", "e_B")
        control = step("09-template-evidence", control_db, "template", "demo-evidence")
        control.update(proposed_K=["h_B"], evidence_ids=["e_B"], reason="Apply the host-admitted synthetic evidence.")
        control_file = output / "admitted-evidence.json"
        write_json(control_file, control)
        accepted = step("10-save-evidence", control_db, "submit", "demo-evidence", "--file", str(control_file))
        control_read = step("11-read-evidence", control_db, "assess", "demo-evidence")
        require(accepted["status"] == "accepted" and control_read["candidates"] == ["h_B"]
                and control_read["version"] == 1
                and control_read["state_sha256"] == accepted["state_sha256_after"], "Admitted evidence was not applied")
        result["examples"].append({"name": "Host-admitted synthetic evidence", "outcome": "only h_B retained", "version": 1})
        result["status"] = "completed"
    except Exception as error:
        result.update(status="failed", error=str(error))
    result["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    write_json(output / "demo-result.json", result)
    lines = ["Stage 4 local demo / 工程4 ローカル実演", "Status / 状態: " + result["status"], ""]
    lines.extend(item["name"] + ": " + item["outcome"] for item in result["examples"])
    if "error" in result:
        lines.extend(["", "Error / エラー: " + result["error"]])
    lines.extend(["", "Fixed local inputs; no model or counting API calls.",
                  "固定入力の実演。モデル・計数APIの呼出しなし。",
                  "This does not complete Stage 3 or establish product readiness.",
                  "Stage 3完了や製品提供可能という判定ではない。"])
    write_new(output / "summary.txt", "\n".join(lines) + "\n")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="A new output directory; never reused")
    args = parser.parse_args(argv)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = args.output or ROOT / "run-output" / ("stage4-demo-" + stamp + "-" + uuid.uuid4().hex[:8])
    try:
        result = run(destination)
    except (OSError, ValueError) as error:
        print("Demo could not start or save its result: " + str(error), file=sys.stderr)
        return 1
    print("Local demo: " + result["status"])
    for item in result["examples"]:
        print("  " + item["name"] + ": " + item["outcome"])
    print("Open: " + str(Path(result["output_directory"]) / "summary.txt"))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
