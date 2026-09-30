"""Fixed-fixture adapter development build; not a completed Stage 3 run.

Only the host calls this module. It contains no model client or real actions.
Strict local shape checks are not a substitute for the separate external
JSON Schema entry gate. Concurrency, crash recovery and privileged writes
remain outside this development check.
"""
import argparse
import base64
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid

from m_anchor_minimal import MAnchor

VERSION = "stage3-adapter-development/v0.1"
OMEGA = frozenset(("h_A", "h_B"))
RULE = "stage3-synthetic-evidence/v0.1"
REGISTRY = {"e_B": frozenset(("h_B",))}
PROCESS = {"pid": os.getpid(), "instance_id": str(uuid.uuid4())}
PROPOSAL_FIELDS = {"schema_version", "proposal_id", "case_id", "expected_version",
                   "expected_state_sha256", "proposed_K", "selected_action", "evidence_ids", "reason"}

def now():
    return datetime.now(timezone.utc).isoformat()

def encode(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def sha(obj):
    return hashlib.sha256(encode(obj).encode()).hexdigest()

def connect(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=rw", uri=True)

def append(con, case_id, kind, record_id, payload):
    con.execute("INSERT INTO records(case_id,kind,record_id,payload) VALUES(?,?,?,?)",
                (case_id, kind, record_id, encode(payload)))

def latest(con, case_id, kind, record_id=None):
    sql = "SELECT payload FROM records WHERE case_id=? AND kind=?"
    args = [case_id, kind]
    if record_id is not None:
        sql += " AND record_id=?"
        args.append(record_id)
    row = con.execute(sql + " ORDER BY seq DESC LIMIT 1", args).fetchone()
    if row is None:
        raise ValueError("Missing host-owned record")
    return json.loads(row[0])

def init_store(path, case_id, admitted=(), new_observations=(), comparison=False):
    """Trusted fixture setup. No model-controlled configuration or admission."""
    path = Path(path)
    if path.exists():
        raise FileExistsError("Never overwrite a previous development run")
    if not set(admitted) <= REGISTRY.keys() or not set(new_observations) <= set(admitted):
        raise ValueError("Invalid fixture admission")
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as con, con:
        con.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        con.execute("CREATE TABLE records(seq INTEGER PRIMARY KEY,case_id TEXT,kind TEXT,record_id TEXT,payload TEXT,UNIQUE(case_id,kind,record_id))")
        con.execute("INSERT INTO metadata VALUES('comparison',?)", (encode(bool(comparison)),))
        authority = {"case_id": case_id, "registered_ids": sorted(REGISTRY),
                     "admitted_valid_ids": sorted(admitted), "new_observation_ids": sorted(new_observations),
                     "authority": "host_fixed_development_fixture", "rule_version": RULE,
                     "fixed_at": now()}
        append(con, case_id, "authority", "authority-001", authority)
        state = {"schema_version": "stage3-state/v0.1", "case_id": case_id,
                 "version": 0, "K": sorted(OMEGA), "applied_evidence": [],
                 "rule_version": "empty-basis-identity/v1", "action_id": None, "action_sha256": None}
        append(con, case_id, "state", "state-0", state)
        append(con, case_id, "audit", "initialize", {"origin": "trusted_fixture_setup", "state_after": state, "process": PROCESS})
    return state

def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result

def _constant(value):
    raise ValueError("non_json_number")

def _shape(p):
    """Local structural checks only; external schema conformance is separate."""
    if not isinstance(p, dict) or set(p) != PROPOSAL_FIELDS:
        raise ValueError("proposal_field_mismatch")
    if p["schema_version"] != "stage3-proposal/v0.1":
        raise ValueError("proposal_schema_version")
    for key in ("proposal_id", "case_id", "reason"):
        if not isinstance(p[key], str) or not p[key].strip():
            raise ValueError("invalid_text_field:" + key)
    if type(p["expected_version"]) is not int or p["expected_version"] < 0:
        raise ValueError("invalid_version_type")
    h = p["expected_state_sha256"]
    if not isinstance(h, str) or len(h) != 64 or any(c not in "0123456789abcdef" for c in h):
        raise ValueError("invalid_hash_shape")
    if p["selected_action"] not in ("a_A", "a_B"):
        raise ValueError("unknown_action")
    for key in ("proposed_K", "evidence_ids"):
        v = p[key]
        if not isinstance(v, list) or any(not isinstance(s, str) or not s.strip() for s in v):
            raise ValueError("invalid_id_array:" + key)
        if len(v) != len(set(v)):
            raise ValueError("duplicate_id:" + key)
    if not set(p["proposed_K"]) <= OMEGA:
        raise ValueError("unknown_candidate")

def read_state(path, case_id):
    with closing(connect(path)) as con:
        return latest(con, case_id, "state")

def proposal(state, proposal_id, K=None, action="a_B", evidence=()):
    """Host fixture helper, not a model or evaluator prompt."""
    return {"schema_version": "stage3-proposal/v0.1", "proposal_id": proposal_id,
            "case_id": state["case_id"], "expected_version": state["version"],
            "expected_state_sha256": sha(state), "proposed_K": list(state["K"] if K is None else K),
            "selected_action": action, "evidence_ids": list(evidence), "reason": "Fixed development fixture."}

def submit_raw(path, host_case_id, raw, origin="fixed_development_fixture"):
    """One checked transaction for state, action and audit; rejected raw is kept.

    The unchecked comparison variant differs only in unsupported-removal
    checking; format, admission, case/version/hash and restoration checks stay.
    No public live-model entry point is implemented in this build.
    """
    if origin not in ("fixed_development_fixture", "trusted_fixture_setup"):
        raise ValueError("Live model execution requires the unfulfilled Stage 3 entry gate")
    raw = raw.encode() if isinstance(raw, str) else raw
    start = time.monotonic()
    with closing(connect(path)) as con, con:
        con.execute("BEGIN IMMEDIATE")
        before = latest(con, host_case_id, "state")
        authority = latest(con, host_case_id, "authority")
        comparison = json.loads(con.execute("SELECT value FROM metadata WHERE key='comparison'").fetchone()[0])
        submission_id = str(uuid.uuid4())
        audit = {"submission_id": submission_id, "case_id": host_case_id, "origin": origin,
                 "raw_response_base64": base64.b64encode(raw).decode(),
                 "raw_response_sha256": hashlib.sha256(raw).hexdigest(), "proposal": None,
                 "process": PROCESS, "recorded_at": now(), "comparison_unchecked": comparison,
                 "external_schema_validation": "not_performed", "state_before": before,
                 "state_after": before, "state_hash_before": sha(before), "state_hash_after": sha(before),
                 "applied_evidence": [], "rule_version": "not_applied"}
        try:
            p = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
            audit["proposal"] = p
            _shape(p)
            if p["case_id"] != host_case_id:
                raise ValueError("case_mismatch")
            if p["expected_version"] != before["version"]:
                raise ValueError("stale_or_forged_version")
            if p["expected_state_sha256"] != sha(before):
                raise ValueError("state_hash_mismatch")
            used = con.execute("SELECT 1 FROM records WHERE case_id=? AND kind='proposal_id' AND record_id=?",
                               (host_case_id, p["proposal_id"])).fetchone()
            if used:
                raise ValueError("reused_proposal_id")
            basis = set(p["evidence_ids"])
            if not basis <= REGISTRY.keys():
                raise ValueError("unregistered_evidence_id")
            if not basis <= set(authority["admitted_valid_ids"]):
                raise ValueError("case_inadmissible_evidence")
            compatible = OMEGA
            for evidence_id in basis:
                compatible &= REGISTRY[evidence_id]
            proposed = set(p["proposed_K"])
            if not proposed <= set(before["K"]):
                raise ValueError("candidate_restoration")
            if not comparison:
                kwargs = {"evidence": sorted(basis), "proposed": p["proposed_K"]}
                if basis:
                    kwargs.update(compatible=compatible, map_version=RULE)
                MAnchor(OMEGA, before["K"]).step(p["selected_action"], p["reason"], **kwargs)
        except (ValueError, UnicodeDecodeError) as error:
            audit.update(status="rejected", rejection_reason=str(error))
        else:
            version = before["version"] + 1
            action = {"case_id": host_case_id, "action_id": f"action-{version:03d}",
                      "state_version": version, "selected_action": p["selected_action"], "reason": p["reason"]}
            after = dict(before, version=version, K=sorted(proposed), applied_evidence=sorted(basis),
                         rule_version=RULE if basis else "empty-basis-identity/v1",
                         action_id=action["action_id"], action_sha256=sha(action))
            append(con, host_case_id, "state", f"state-{version}", after)
            append(con, host_case_id, "action", action["action_id"], action)
            append(con, host_case_id, "proposal_id", p["proposal_id"], {"submission_id": submission_id})
            audit.update(status="accepted", rejection_reason=None, state_after=after, state_hash_after=sha(after),
                         applied_evidence=sorted(basis), rule_version=after["rule_version"], action=action)
        audit["adapter_store_seconds"] = time.monotonic() - start
        append(con, host_case_id, "audit", submission_id, audit)
    return audit

def save_summary(path, case_id, text, summary_id="summary-001"):
    with closing(connect(path)) as con, con:
        con.execute("BEGIN IMMEDIATE")
        state = latest(con, case_id, "state")
        record = {"summary_id": summary_id, "text": text, "admitted_as_evidence": False}
        append(con, case_id, "summary", summary_id, record)
        assert state == latest(con, case_id, "state")
    return record

def resume(path, case_id):
    """New host process exports exact inputs and uses a deterministic reader.

    This is not a model response, API-input trace or Stage 3 R5 model result.
    """
    with closing(connect(path)) as con, con:
        con.execute("BEGIN IMMEDIATE")
        state = latest(con, case_id, "state")
        action = latest(con, case_id, "action", state["action_id"])
        authority = latest(con, case_id, "authority")
        summary = latest(con, case_id, "summary")
        if action["state_version"] != state["version"] or sha(action) != state["action_sha256"]:
            raise ValueError("Host state/action linkage failure")
        view = {"schema_version": "stage3-input/v0.1", "state": state, "state_sha256": sha(state),
                "action": action, "admitted_evidence": [
                    {"evidence_id": e, "permitted_candidates": sorted(REGISTRY[e])}
                    for e in authority["admitted_valid_ids"]],
                "new_observation_ids": authority["new_observation_ids"], "summary": summary}
        status = "unresolved" if len(state["K"]) > 1 else "single_candidate_under_interpretation" if state["K"] else "candidate_exhaustion"
        decision = {"schema_version": "stage3-decision/v0.1", "case_id": case_id,
                    "state_version_read": state["version"], "state_sha256_read": sha(state),
                    "selected_action": action["selected_action"], "retained_candidates": state["K"], "cause_status": status}
        trace = {"case_id": case_id, "reader_process": PROCESS, "state_version_read": state["version"],
                 "state_sha256_read": sha(state), "action_id_read": action["action_id"],
                 "action_sha256_read": sha(action), "input_sha256": sha(view), "read_at": now(),
                 "decision_source": "deterministic_development_reader", "api_request_id": None,
                 "previous_conversation_inherited": False, "summary_used_to_reconstruct_K": False}
        result = {"input": view, "decision": decision, "trace": trace}
        append(con, case_id, "read", str(uuid.uuid4()), result)
        assert state == latest(con, case_id, "state")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["resume"])
    parser.add_argument("store")
    parser.add_argument("case_id")
    args = parser.parse_args()
    print(encode(resume(args.store, args.case_id)))
