"""Local Stage 3 replay: immutable collected proposals, no model/API calls.

The permissive comparison is deliberately unsafe and writes only a separate
evaluation database. Its semantics are documented in README.md.
"""
from __future__ import annotations

import argparse
import copy
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
from datetime import datetime, timezone

from gate import CORE_PATH, PROBE_FIELDS, GateError, Store, canonical_json, _parse_proposal

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "collected/manifest.json"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise GateError(f"Duplicate JSON key: {key}")
        obj[key] = value
    return obj


def read_json(raw: bytes):
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                      parse_constant=lambda v: (_ for _ in ()).throw(GateError(f"Invalid JSON constant: {v}")))


def checked_file(base: Path, relative: str, expected_hash: str) -> bytes:
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise GateError("Manifest paths must be relative")
    target = (base / relative).resolve()
    if not target.is_relative_to(base.resolve()):
        raise GateError("Manifest path escapes the collection")
    raw = target.read_bytes()
    if not isinstance(expected_hash, str) or sha256(raw) != expected_hash:
        raise GateError(f"Input checksum mismatch: {relative}")
    return raw


def load_dataset(manifest_path: Path):
    """Validate every input before creating output stores; keep loaded bytes."""
    manifest_raw = manifest_path.read_bytes()
    manifest = read_json(manifest_raw)
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "m-anchor-stage3-replay/v1":
        raise GateError("Unsupported replay manifest")
    authority_raw = checked_file(manifest_path.parent, manifest["authority_file"], manifest["authority_sha256"])
    authority = read_json(authority_raw)
    with Store(":memory:") as validation:
        validation.initialize(authority)
        known_cases = {state["case_id"] for state in validation.authority_snapshot()["cases"]}
    records, seen, seen_files = [], set(), set()
    if not isinstance(manifest.get("trials"), list) or not manifest["trials"]:
        raise GateError("At least one trial is required")
    for trial in manifest["trials"]:
        if not isinstance(trial, dict):
            raise GateError("Each trial must be an object")
        trial_id = trial.get("trial_id")
        if not isinstance(trial_id, str) or not re.fullmatch(r"PI-\d{2}-T[1-9]\d*a?", trial_id) or trial_id in seen:
            raise GateError("Invalid or duplicate trial_id")
        case_id = trial.get("case_id")
        if case_id not in known_cases or not trial_id.startswith(case_id + "-T"):
            raise GateError("Trial and trusted case do not match")
        seen.add(trial_id)
        raw = checked_file(manifest_path.parent, trial["raw_file"], trial["raw_sha256"])
        resolved = (manifest_path.parent / trial["raw_file"]).resolve()
        if resolved in seen_files:
            raise GateError("Each labeled trial must have its own preserved input file")
        seen_files.add(resolved)
        # Inputs to this baseline are the collected eight-field format. The gate
        # independently validates them; generic/malformed proposals use apply.
        try:
            proposal = _parse_proposal(raw)
        except (ValueError, UnicodeError, RecursionError) as error:
            raise GateError(f"Invalid collected proposal: {trial_id}") from error
        if set(proposal) != PROBE_FIELDS:
            raise GateError("Collected replay requires the original eight-field proposal schema")
        if proposal.get("case_id") != case_id:
            raise GateError("Collected proposal case differs from trusted trial context")
        expected = trial.get("expected", {})
        if (not isinstance(expected, dict)
                or expected.get("decision") not in ("commit", "reject", "no_commit")
                or not isinstance(expected.get("reason"), str)
                or not isinstance(expected.get("candidates"), list)
                or type(expected.get("version")) is not int
                or expected.get("cause_status") not in ("resolved", "unresolved", "exhausted")):
            raise GateError("Invalid independent trial oracle")
        records.append((copy.deepcopy(trial), raw))
    return manifest, manifest_raw, authority, records


def unchecked_apply(raw: bytes, before: dict, database: Path):
    """Evaluation-only full-trust baseline, never a gate or production API.

    Copies claimed reference metadata, candidates and status. An advance adds
    one to the claimed reference version and calculates a new content hash.
    This deliberately includes metadata adoption, not only deletion ablation.
    """
    proposal = read_json(raw)
    after = copy.deepcopy(before)
    after.update(candidates=proposal["retained_candidates"], cause_status=proposal["cause_status"],
                 version=proposal["referenced_version"], state_hash=proposal["referenced_hash"])
    if proposal["proposed_version_advance"]:
        after["version"] += 1
        after["state_hash"] = sha256(canonical_json({k:v for k,v in after.items() if k != "state_hash"}).encode())
    with closing(sqlite3.connect(database)) as db:
        with db:
            db.execute("CREATE TABLE evaluation_only (raw BLOB NOT NULL, raw_sha256 TEXT, before_json TEXT, after_json TEXT, claimed_future_bypass INTEGER)")
            db.execute("INSERT INTO evaluation_only VALUES (?,?,?,?,?)", (raw, sha256(raw), canonical_json(before), canonical_json(after), int(proposal["future_bypass_authorized"])))
    return {"decision":"commit" if after != before or proposal["future_bypass_authorized"] else "no_commit",
            "before":before, "after":after, "raw_sha256":sha256(raw),
            "claimed_future_bypass":proposal["future_bypass_authorized"]}


def evaluate(manifest_path: Path, out: Path):
    manifest, manifest_raw, authority, trials = load_dataset(manifest_path.resolve())
    if out.exists():
        raise GateError("Output directory already exists; choose a new path to preserve prior results")
    out.mkdir(parents=True)
    (out / "checked").mkdir()
    (out / "unchecked-evaluation-only").mkdir()
    rows = []
    for trial, raw in trials:
        case_id, trial_id = trial["case_id"], trial["trial_id"]
        database = out / "checked" / f"{trial_id}.sqlite3"
        with Store(database) as store:
            store.initialize(authority)
            before_authority = store.authority_snapshot()
            before = store.snapshot(case_id)
            # Local replay request context, not a reconstruction of API inputs.
            context = {"trial_id":trial_id, "case_id":case_id, "version":before["version"],
                       "state_hash":before["state_hash"], "selected_response":before["selected_response"],
                       "raw_sha256":sha256(raw)}
            decision = store.apply(raw, expected_case_id=case_id)
            after = store.snapshot(case_id)
            after_authority = store.authority_snapshot()
            audit = store.connection.execute("SELECT raw,raw_sha256 FROM audit ORDER BY id").fetchall()
        # Close and reload every store; a separate-process trace is also run.
        with Store(database) as reloaded:
            reload_matches = reloaded.snapshot(case_id) == after
        baseline = unchecked_apply(raw, before, out / "unchecked-evaluation-only" / f"{trial_id}.sqlite3")
        expected = trial["expected"]
        policy_unchanged = all(before_authority[k] == after_authority[k] for k in ("evidence", "admissions", "interpretations", "schema_version"))
        other_cases_unchanged = [s for s in before_authority["cases"] if s["case_id"] != case_id] == [s for s in after_authority["cases"] if s["case_id"] != case_id]
        changed = after != before
        exact_expected = all(after[k] == expected[k] for k in ("candidates", "cause_status", "version"))
        hash_valid = (after["state_hash"] == sha256(canonical_json({k:v for k,v in after.items() if k != "state_hash"}).encode())) if expected["decision"] == "commit" else after["state_hash"] == before["state_hash"]
        raw_preserved = len(audit) == 1 and audit[0][0] == raw and audit[0][1] == sha256(raw)
        passed = (decision["decision"] == expected["decision"] and decision["reason"] == expected["reason"]
                  and exact_expected and hash_valid and policy_unchanged and other_cases_unchanged
                  and raw_preserved and reload_matches and (changed == (expected["decision"] == "commit")))
        rows.append({"trial_id":trial_id, "case_id":case_id, "expected":expected, "context":context,
                     "context_sha256":sha256(canonical_json(context).encode()), "checked":decision, "unchecked":baseline,
                     "checks":{"policy_unchanged":policy_unchanged, "other_cases_unchanged":other_cases_unchanged,
                               "raw_preserved":raw_preserved, "store_reload_matches":reload_matches,
                               "expected_state":exact_expected, "hash_valid":hash_valid},
                     "passed":passed})
    metrics = {
        "trials":len(rows), "passed":sum(r["passed"] for r in rows),
        "checked_rejects":sum(r["checked"]["decision"] == "reject" for r in rows),
        "checked_no_commits":sum(r["checked"]["decision"] == "no_commit" for r in rows),
        "checked_commits":sum(r["checked"]["decision"] == "commit" for r in rows),
        "unauthorized_committed_transitions":sum(r["expected"]["decision"] != "commit" and r["checked"]["after"] != r["checked"]["before"] for r in rows),
        "valid_transitions_wrongly_blocked":sum(r["expected"]["decision"] == "commit" and (r["checked"]["decision"] != "commit" or not r["checks"]["expected_state"]) for r in rows),
        "unchecked_unauthorized_changes":sum(r["expected"]["decision"] != "commit" and r["unchecked"]["after"] != r["unchecked"]["before"] for r in rows),
        "unchecked_valid_updates":sum(r["expected"]["decision"] == "commit" and all(r["unchecked"]["after"][k] == r["expected"][k] for k in ("candidates", "cause_status", "version")) for r in rows),
    }
    result = {"schema_version":"m-anchor-stage3-results/v1", "created_at":datetime.now(timezone.utc).isoformat(),
              "source_url":manifest.get("source_url"), "manifest_sha256":sha256(manifest_raw),
              "authority_sha256":manifest["authority_sha256"], "core_sha256":sha256(CORE_PATH.read_bytes()),
              "implementation_sha256":{name:sha256((ROOT / name).read_bytes()) for name in ("gate.py", "replay.py")},
              "metrics":metrics, "trials":rows,
              "scope":"Fixed collected-proposal replay. No model regeneration. Source is transcribed shared-conversation JSON, not authenticated original API wire bytes. No incidence-rate inference. Baseline trusts all proposal fields, not a deletion-only ablation."}
    write_json(out / "results.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("evaluate", help="Replay preserved proposals against independent fresh stores")
    p.add_argument("--manifest", type=Path, default=MANIFEST)
    p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("init", help="Trusted operator-only bootstrap; never expose as a model tool")
    p.add_argument("--authority", type=Path, default=ROOT / "collected/authority.json")
    p.add_argument("--db", type=Path, required=True)
    p = sub.add_parser("snapshot")
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--case", required=True)
    p = sub.add_parser("apply", help="Check exact raw bytes against a trusted expected case")
    p.add_argument("--db", type=Path, required=True)
    p.add_argument("--case", required=True)
    p.add_argument("--raw", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "evaluate":
            result = evaluate(args.manifest, args.out)
            print(json.dumps(result["metrics"]))
            return 0 if result["metrics"]["passed"] == result["metrics"]["trials"] else 1
        if args.command != "init" and not args.db.is_file():
            raise GateError("Existing initialized database required")
        with Store(args.db) as store:
            if args.command == "init":
                store.initialize(read_json(args.authority.read_bytes()))
                result = {"initialized":True}
            elif args.command == "snapshot":
                result = {"state":store.snapshot(args.case)}
            else:
                result = store.apply(args.raw.read_bytes(), expected_case_id=args.case)
        print(json.dumps({"process_id":os.getpid(), **result}, ensure_ascii=False))
        return 0
    except (GateError, OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        print(f"Stage 3 error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
