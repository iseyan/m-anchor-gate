"""Demo 1 v0.1: a single-writer fixture, not a security boundary.

The unchanged Python v0.1 guard checks K. This module owns the fixed evidence
interpretation and transactional persistence. No model, network, or real action.
"""

import hashlib
import json
import os
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType

from m_anchor_minimal import MAnchor

VERSION = "demo1/v0.1"
OMEGA = frozenset({"h_A", "h_B"})
REGISTRY_VERSION = "demo1-registry/v0.1"
REGISTRY = MappingProxyType({"e_B": frozenset({"h_B"})})
RULE_VERSION = "demo1-evidence-map/v0.1"


def now():
    return datetime.now(timezone.utc).isoformat()


PROCESS = {"pid": os.getpid(), "instance_id": str(uuid.uuid4()), "started_at_utc": now()}


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(dumps(value).encode("utf-8")).hexdigest()


def connect(path, create=False):
    path = Path(path).resolve()
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path.as_uri() + ("?mode=rwc" if create else "?mode=rw"), uri=True)
    if create:
        con.execute("""CREATE TABLE IF NOT EXISTS records (
            seq INTEGER PRIMARY KEY, case_id TEXT NOT NULL, kind TEXT NOT NULL,
            record_id TEXT NOT NULL, version INTEGER NOT NULL, payload TEXT NOT NULL,
            UNIQUE(case_id, kind, record_id))""")
        con.commit()
    return con


def put(con, case_id, kind, record_id, version, payload):
    con.execute("INSERT INTO records(case_id,kind,record_id,version,payload) VALUES(?,?,?,?,?)",
                (case_id, kind, record_id, version, dumps(payload)))


def get(con, case_id, kind, record_id=None):
    query = "SELECT payload FROM records WHERE case_id=? AND kind=?"
    args = [case_id, kind]
    if record_id is not None:
        query += " AND record_id=?"
        args.append(record_id)
    row = con.execute(query + " ORDER BY version DESC, seq DESC LIMIT 1", args).fetchone()
    if row is None:
        raise ValueError(f"Missing authoritative record: {case_id}/{kind}/{record_id}")
    return json.loads(row[0])


def initialize(path, case_id):
    initial = MAnchor(OMEGA)
    audit_id = str(uuid.uuid4())
    state = {
        "schema_version": "demo1-state/v0.1", "case_id": case_id, "state_version": 0,
        "K": sorted(initial.candidates), "omega": sorted(OMEGA), "evidence_basis": [],
        "registry_version": REGISTRY_VERSION, "rule_version": "empty-basis-identity/v1",
        "action_record_id": None, "transition_audit_id": audit_id,
        "writer_process": PROCESS, "saved_at_utc": now(),
    }
    with closing(connect(path, create=True)) as con, con:
        con.execute("BEGIN IMMEDIATE")
        put(con, case_id, "state", "state-0", 0, state)
        put(con, case_id, "audit", audit_id, 0,
            {"audit_id": audit_id, "kind": "initialize", "state_after": state, "process": PROCESS})
    return state


def interpret(evidence_ids):
    if not isinstance(evidence_ids, list) or any(not isinstance(x, str) for x in evidence_ids):
        raise ValueError("evidence_ids must be a list of registered IDs")
    if len(set(evidence_ids)) != len(evidence_ids):
        raise ValueError("Duplicate evidence ID")
    unknown = sorted(set(evidence_ids) - REGISTRY.keys())
    if unknown:
        raise ValueError(f"Unregistered evidence ID: {unknown}")
    allowed = OMEGA
    for evidence_id in evidence_ids:
        allowed = allowed & REGISTRY[evidence_id]
    return allowed


def checked_save(path, case_id, proposal):
    """The only ordinary state-update entry point; log rejected proposals too."""
    with closing(connect(path)) as con, con:
        con.execute("BEGIN IMMEDIATE")
        before = get(con, case_id, "state")
        audit_id = str(uuid.uuid4())
        audit = {
            "audit_id": audit_id, "kind": "transition", "process": PROCESS,
            "recorded_at_utc": now(), "proposal": proposal,
            "evidence_ids": proposal.get("evidence_ids", []),
            "registry_version": REGISTRY_VERSION, "rule_version": "not-applied",
            "state_before": before, "state_after": before,
        }
        try:
            fields = {"action_record_id", "selected_action", "reason", "evidence_ids", "proposed_K"}
            if set(proposal) != fields:
                raise ValueError("Proposal fields must be fixed; caller-supplied interpretations are forbidden")
            if proposal["selected_action"] not in ("a_A", "a_B"):
                raise ValueError("Unknown response ID")
            if not isinstance(proposal["action_record_id"], str) or not proposal["action_record_id"].strip():
                raise ValueError("Missing action record ID")
            basis = proposal["evidence_ids"]
            compatible = interpret(basis)
            audit["rule_version"] = RULE_VERSION if basis else "empty-basis-identity/v1"
            audit["compatible"] = sorted(compatible)
            kwargs = {"evidence": basis, "proposed": proposal["proposed_K"]}
            if basis:
                kwargs.update(compatible=compatible, map_version=RULE_VERSION)
            after_guard, kernel_record = MAnchor(OMEGA, before["K"]).step(
                proposal["selected_action"], proposal["reason"], **kwargs)
        except ValueError as error:
            audit.update(status="rejected", rejection_reason=str(error))
        else:
            version = before["state_version"] + 1
            after = dict(before, state_version=version, K=sorted(after_guard.candidates),
                         evidence_basis=sorted(basis), rule_version=audit["rule_version"],
                         action_record_id=proposal["action_record_id"], transition_audit_id=audit_id,
                         writer_process=PROCESS, saved_at_utc=now())
            action = {
                "case_id": case_id, "action_record_id": proposal["action_record_id"],
                "state_version": version, "selected_action": proposal["selected_action"],
                "binary_output": proposal["selected_action"].removeprefix("a_"),
                "reason": proposal["reason"], "candidates_at_selection": before["K"],
                "writer_process": PROCESS, "transition_audit_id": audit_id,
            }
            put(con, case_id, "state", f"state-{version}", version, after)
            put(con, case_id, "action", proposal["action_record_id"], version, action)
            audit.update(status="accepted", state_after=after, kernel_record=kernel_record)
        put(con, case_id, "audit", audit_id, audit["state_after"]["state_version"], audit)
    return audit


def save_summary(path, case_id, text_ja, text_en):
    with closing(connect(path)) as con, con:
        con.execute("BEGIN IMMEDIATE")
        state = get(con, case_id, "state")
        summary = {"summary_id": "summary-001", "case_id": case_id,
                   "state_version_at_save": state["state_version"],
                   "text_ja": text_ja, "text_en": text_en, "admitted_as_evidence": False,
                   "writer_process": PROCESS, "saved_at_utc": now()}
        put(con, case_id, "summary", "summary-001", state["state_version"], summary)
    return summary


def derive(K, selected_action):
    """Deterministic rule application. No case ID, summary, or expected verdict."""
    candidates = frozenset(K)
    if not candidates <= OMEGA or selected_action not in ("a_A", "a_B"):
        raise ValueError("Unknown candidate or action")
    if candidates == OMEGA:
        return "unresolved", f"{selected_action}は選択済み／原因A・Bは未決", \
            f"{selected_action} was selected; causes A/B remain unresolved."
    if len(candidates) == 1:
        label = next(iter(candidates)).removeprefix("h_")
        return "single_candidate_under_interpretation", f"この証拠解釈では{label}のみ保持", \
            f"only {label} is retained under this evidence interpretation"
    return "candidate_exhaustion", "候補枯渇", "candidate exhaustion"


def resume(path, case_id):
    """Read authoritative records, apply the rule, and record their exact linkage."""
    with closing(connect(path)) as con, con:
        con.execute("BEGIN IMMEDIATE")
        state = get(con, case_id, "state")
        action = get(con, case_id, "action", state["action_record_id"])
        summary = get(con, case_id, "summary")
        if state["action_record_id"] is None or action["state_version"] != state["state_version"]:
            raise ValueError("State and response record are not linked")
        status, text_ja, text_en = derive(state["K"], action["selected_action"])
        record = {
            "schema_version": "demo1-decision/v0.1", "decision_id": str(uuid.uuid4()),
            "case_id": case_id, "reader_process": PROCESS, "read_at_utc": now(),
            "state_version_read": state["state_version"], "K_read": state["K"],
            "evidence_basis": state["evidence_basis"], "rule_version": state["rule_version"],
            "state_sha256": digest(state), "state_writer_process": state["writer_process"],
            "transition_audit_id": state["transition_audit_id"],
            "action_record_id": action["action_record_id"], "selected_action": action["selected_action"],
            "action_sha256": digest(action), "summary_read": summary,
            "decision_rule": "candidate-cardinality-and-action/v0.1",
            "decision_inputs": {"K": state["K"], "selected_action": action["selected_action"]},
            "summary_used_for_decision": False,
            "status": status, "decision_ja": text_ja, "decision_en": text_en,
        }
        put(con, case_id, "decision", record["decision_id"], state["state_version"], record)
    return record
