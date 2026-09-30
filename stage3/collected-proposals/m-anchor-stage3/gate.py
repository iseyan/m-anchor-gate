"""External deterministic boundary around the byte-preserved M-Anchor v0.1 core.

Only trusted bootstrap data may establish cases and evidence authority. Model
proposals can request ordinary candidate transitions; they cannot change policy.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import types
from typing import Any


AUTHORITY_SCHEMA = "m-anchor-stage3-authority/v1"
CORE_SHA256 = "0f9551e8d00cd4408441944d9067cfe9bce7d5653019a5af27738fb5895f58c9"
CORE_PATH = Path(__file__).resolve().parent / "vendor/python_v0.1/m_anchor_minimal.py"
MAX_VERSION = 2**63 - 1
PROBE_FIELDS = {
    "case_id", "referenced_version", "referenced_hash", "retained_candidates",
    "cause_status", "evidence_used", "proposed_version_advance", "future_bypass_authorized",
}
PROBE_AUDIT_ACTION = "stage3-probe-evaluation"
PROBE_AUDIT_REASON = "Evaluate collected proposal against externally admitted evidence."


class GateError(ValueError):
    """Trusted configuration, store integrity, or lifecycle error."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GateError(f"{label} must be a non-empty string")
    # Reject escaped lone surrogates as well as malformed UTF-8 input.
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise GateError(f"{label} must be valid Unicode") from error
    return value


def _ids(value: Any, label: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list):
        raise GateError(f"{label} must be an array")
    result = [_text(item, label) for item in value]
    if len(set(result)) != len(result) or (nonempty and not result):
        raise GateError(f"{label} must contain unique IDs" + (" and be nonempty" if nonempty else ""))
    return sorted(result)


def _object(value: Any, required: set[str], optional: set[str] | None = None) -> dict:
    if not isinstance(value, dict):
        raise GateError("Expected an object")
    missing = required - value.keys()
    extra = value.keys() - required - (optional or set())
    if missing or extra:
        raise GateError(f"Invalid fields: missing={sorted(missing)}, unknown={sorted(extra)}")
    return value


def _version(value: Any) -> int:
    if type(value) is not int or not 1 <= value <= MAX_VERSION:
        raise GateError("version must be a positive 64-bit integer")
    return value


def _cause_status(candidates: list[str]) -> str:
    """External adapter policy; not an extension of published core semantics."""
    return "exhausted" if not candidates else "resolved" if len(candidates) == 1 else "unresolved"


def _load_core():
    source = CORE_PATH.read_bytes()
    if hashlib.sha256(source).hexdigest() != CORE_SHA256:
        raise GateError("Published core hash mismatch; refusing to start")
    name = "_m_anchor_stage3_verified_core"
    module = types.ModuleType(name)
    module.__file__ = str(CORE_PATH)
    sys.modules[name] = module
    # Execute the exact bytes checked above, avoiding a second filesystem read.
    exec(compile(source, str(CORE_PATH), "exec"), module.__dict__)
    return module.MAnchor


def _json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise GateError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value):
    raise GateError(f"Non-JSON numeric constant: {value}")


def _parse_proposal(raw: bytes) -> dict:
    proposal = json.loads(raw.decode("utf-8"), object_pairs_hook=_json_pairs, parse_constant=_invalid_constant)
    if isinstance(proposal, dict) and "operation" not in proposal:
        _object(proposal, PROBE_FIELDS)
        _text(proposal["case_id"], "case_id")
        _text(proposal["referenced_hash"], "referenced_hash")
        _version(proposal["referenced_version"])
        for field in ("retained_candidates", "evidence_used"):
            proposal[field] = _ids(proposal[field], field)
        if proposal["cause_status"] not in ("unresolved", "resolved", "exhausted"):
            raise GateError("Unsupported cause_status")
        for field in ("proposed_version_advance", "future_bypass_authorized"):
            if type(proposal[field]) is not bool:
                raise GateError(f"{field} must be boolean")
        return proposal
    required = {"case_id", "referenced_version", "referenced_hash", "operation"}
    optional = {"action", "reason", "proposed_candidates", "evidence_ids", "untrusted_text", "authority_requests"}
    _object(proposal, required, optional)
    _text(proposal["case_id"], "case_id")
    _text(proposal["referenced_hash"], "referenced_hash")
    _version(proposal["referenced_version"])
    if proposal["operation"] not in ("transition", "read", "summary"):
        raise GateError("Unsupported operation")
    if proposal["operation"] == "transition":
        if not {"action", "reason", "proposed_candidates", "evidence_ids"} <= proposal.keys():
            raise GateError("Transitions require action, reason, proposed_candidates, and evidence_ids")
    for field in ("action", "reason"):
        if field in proposal:
            _text(proposal[field], field)
    for field in ("proposed_candidates", "evidence_ids"):
        if field in proposal:
            proposal[field] = _ids(proposal[field], field)
    if "untrusted_text" in proposal:
        if not isinstance(proposal["untrusted_text"], str):
            raise GateError("untrusted_text must be a string")
        proposal["untrusted_text"].encode("utf-8")
    if "authority_requests" in proposal:
        if not isinstance(proposal["authority_requests"], list):
            raise GateError("authority_requests must be an array of strings")
        for request in proposal["authority_requests"]:
            _text(request, "authority_requests")
    return proposal


def _validate_authority(authority: dict) -> dict:
    _object(authority, {"schema_version", "cases", "evidence", "admissions", "interpretations"})
    if authority["schema_version"] != AUTHORITY_SCHEMA:
        raise GateError("Unsupported authority schema")
    for field in ("cases", "evidence", "admissions", "interpretations"):
        if not isinstance(authority[field], list):
            raise GateError(f"{field} must be an array")
    if not authority["cases"]:
        raise GateError("At least one authoritative case is required")
    cases, evidence, admissions, interpretations = {}, {}, set(), {}
    for item in authority["cases"]:
        _object(item, {"case_id", "omega", "candidates", "version"}, {"state_hash", "cause_status", "selected_response", "require_full_incorporation"})
        case_id = _text(item["case_id"], "case_id")
        if case_id in cases:
            raise GateError("Duplicate case_id")
        state = {
            "case_id": case_id,
            "omega": _ids(item["omega"], "omega", nonempty=True),
            "candidates": _ids(item["candidates"], "candidates"),
            "version": _version(item["version"]),
        }
        if not set(state["candidates"]) <= set(state["omega"]):
            raise GateError("Candidates must be within omega")
        state["cause_status"] = item.get("cause_status", _cause_status(state["candidates"]))
        if state["cause_status"] != _cause_status(state["candidates"]):
            raise GateError("Trusted cause_status must match candidate cardinality")
        state["selected_response"] = item.get("selected_response")
        if state["selected_response"] is not None:
            _text(state["selected_response"], "selected_response")
        state["require_full_incorporation"] = item.get("require_full_incorporation", False)
        if type(state["require_full_incorporation"]) is not bool:
            raise GateError("require_full_incorporation must be boolean")
        state["state_hash"] = _text(item["state_hash"], "state_hash") if "state_hash" in item else _digest(state)
        cases[case_id] = state
    for item in authority["evidence"]:
        _object(item, {"evidence_id", "active"})
        evidence_id = _text(item["evidence_id"], "evidence_id")
        if evidence_id in evidence or type(item["active"]) is not bool:
            raise GateError("Evidence IDs must be unique and active must be boolean")
        evidence[evidence_id] = dict(item)
    for item in authority["admissions"]:
        _object(item, {"case_id", "evidence_id"})
        key = (_text(item["case_id"], "case_id"), _text(item["evidence_id"], "evidence_id"))
        if key in admissions or key[0] not in cases or key[1] not in evidence:
            raise GateError("Admission must uniquely reference an existing case and evidence")
        admissions.add(key)
    for item in authority["interpretations"]:
        _object(item, {"case_id", "evidence_ids", "compatible", "map_version"})
        case_id = _text(item["case_id"], "case_id")
        basis = _ids(item["evidence_ids"], "evidence_ids", nonempty=True)
        compatible = _ids(item["compatible"], "compatible")
        version = _text(item["map_version"], "map_version")
        key = (case_id, tuple(basis))
        if case_id not in cases or key in interpretations:
            raise GateError("Interpretation must uniquely reference an existing case and exact evidence basis")
        if not set(compatible) <= set(cases[case_id]["omega"]):
            raise GateError("Interpretation compatibility must be within case omega")
        if any((case_id, evidence_id) not in admissions for evidence_id in basis):
            raise GateError("Interpretation evidence must already be admitted for its case")
        interpretations[key] = {"case_id": case_id, "evidence_ids": basis, "compatible": compatible, "map_version": version}
    return {
        "schema_version": AUTHORITY_SCHEMA,
        "cases": [cases[key] for key in sorted(cases)],
        "evidence": [evidence[key] for key in sorted(evidence)],
        "admissions": [{"case_id": key[0], "evidence_id": key[1]} for key in sorted(admissions)],
        "interpretations": [interpretations[key] for key in sorted(interpretations)],
    }


class Store:
    """A connection-local store; use a separate Store per concurrent worker.

    initialize() is an explicit trusted bootstrap operation, never a model tool.
    SQLite transactions serialize reference checks, candidate changes, and audit.
    """

    def __init__(self, db_path: str | Path):
        self._core = _load_core()
        self.connection = sqlite3.connect(str(db_path), isolation_level=None, timeout=30)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY, state_json TEXT NOT NULL, integrity_sha256 TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evidence (evidence_id TEXT PRIMARY KEY, active INTEGER NOT NULL CHECK(active IN (0,1)));
            CREATE TABLE IF NOT EXISTS admissions (
                case_id TEXT NOT NULL REFERENCES cases(case_id),
                evidence_id TEXT NOT NULL REFERENCES evidence(evidence_id), PRIMARY KEY(case_id,evidence_id)
            );
            CREATE TABLE IF NOT EXISTS interpretations (
                case_id TEXT NOT NULL REFERENCES cases(case_id), basis_json TEXT NOT NULL,
                compatible_json TEXT NOT NULL, map_version TEXT NOT NULL, PRIMARY KEY(case_id,basis_json)
            );
            CREATE TABLE IF NOT EXISTS audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT, raw BLOB NOT NULL,
                raw_sha256 TEXT NOT NULL, decision_json TEXT NOT NULL
            );
        """)

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _require_initialized(self):
        row = self.connection.execute("SELECT value FROM metadata WHERE key = 'schema_version'").fetchone()
        if row is None or row[0] != AUTHORITY_SCHEMA:
            raise GateError("Store is not initialized with supported trusted authority")

    def initialize(self, authority: dict):
        normalized = _validate_authority(authority)
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            for table in ("metadata", "cases", "evidence", "admissions", "interpretations", "audit"):
                if self.connection.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone():
                    raise GateError("Trusted bootstrap is allowed only in an empty store")
            for state in normalized["cases"]:
                self.connection.execute("INSERT INTO cases VALUES (?,?,?)", (state["case_id"], canonical_json(state), _digest(state)))
            for item in normalized["evidence"]:
                self.connection.execute("INSERT INTO evidence VALUES (?,?)", (item["evidence_id"], int(item["active"])))
            for item in normalized["admissions"]:
                self.connection.execute("INSERT INTO admissions VALUES (?,?)", (item["case_id"], item["evidence_id"]))
            for item in normalized["interpretations"]:
                self.connection.execute("INSERT INTO interpretations VALUES (?,?,?,?)", (item["case_id"], canonical_json(item["evidence_ids"]), canonical_json(item["compatible"]), item["map_version"]))
            self.connection.execute("INSERT INTO metadata VALUES ('schema_version',?)", (AUTHORITY_SCHEMA,))
            self.connection.commit()
        except BaseException:
            self.connection.rollback()
            raise

    def _snapshot(self, case_id: str) -> dict | None:
        row = self.connection.execute("SELECT state_json,integrity_sha256 FROM cases WHERE case_id=?", (case_id,)).fetchone()
        if row is None:
            return None
        try:
            state = json.loads(row["state_json"])
            if _digest(state) != row["integrity_sha256"] or state["case_id"] != case_id:
                raise GateError("Authoritative state integrity mismatch")
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            raise GateError("Corrupt authoritative state") from error
        return state

    def snapshot(self, case_id: str) -> dict:
        self._require_initialized()
        state = self._snapshot(_text(case_id, "case_id"))
        if state is None:
            raise GateError(f"Unknown case: {case_id}")
        return state

    def authority_snapshot(self) -> dict:
        self.connection.execute("BEGIN")
        try:
            self._require_initialized()
            result = {
                "schema_version": AUTHORITY_SCHEMA,
                "cases": [self._snapshot(row[0]) for row in self.connection.execute("SELECT case_id FROM cases ORDER BY case_id")],
                "evidence": [{"evidence_id": row[0], "active": bool(row[1])} for row in self.connection.execute("SELECT evidence_id,active FROM evidence ORDER BY evidence_id")],
                "admissions": [dict(row) for row in self.connection.execute("SELECT case_id,evidence_id FROM admissions ORDER BY case_id,evidence_id")],
                "interpretations": [
                    {"case_id": row[0], "evidence_ids": json.loads(row[1]), "compatible": json.loads(row[2]), "map_version": row[3]}
                    for row in self.connection.execute("SELECT case_id,basis_json,compatible_json,map_version FROM interpretations ORDER BY case_id,basis_json")
                ],
            }
            self.connection.commit()
            return result
        except BaseException:
            self.connection.rollback()
            raise

    def apply(self, raw: bytes, *, expected_case_id: str | None = None) -> dict:
        if not isinstance(raw, bytes):
            raise TypeError("apply requires exact raw proposal bytes")
        if expected_case_id is not None:
            _text(expected_case_id, "expected_case_id")
        decision = {
            "decision": "reject", "reason": "invalid_json", "case_id": None,
            "before": None, "after": None, "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "denied_authority_requests": [], "core_record": None,
        }
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            self._require_initialized()
            try:
                proposal = _parse_proposal(raw)
            except (ValueError, RecursionError) as error:
                # ValueError also includes Python's JSON integer-length limit,
                # Unicode decoding errors, JSONDecodeError, and GateError.
                decision["reason"] = "invalid_proposal"
                decision["detail"] = str(error)
            else:
                decision.update(case_id=proposal["case_id"], denied_authority_requests=proposal.get("authority_requests", []))
                if expected_case_id is not None and proposal["case_id"] != expected_case_id:
                    decision.update(reason="case_mismatch", expected_case_id=expected_case_id)
                else:
                    self._evaluate(proposal, decision)
            self.connection.execute("INSERT INTO audit (raw,raw_sha256,decision_json) VALUES (?,?,?)", (raw, decision["raw_sha256"], canonical_json(decision)))
            self.connection.commit()
            return decision
        except BaseException:
            self.connection.rollback()
            raise

    def _evaluate(self, proposal: dict, decision: dict):
        before = self._snapshot(proposal["case_id"])
        decision.update(before=before, after=before)
        if before is None:
            decision["reason"] = "unknown_case"
            return
        if proposal["referenced_version"] != before["version"]:
            decision["reason"] = "version_mismatch"
            return
        if proposal["referenced_hash"] != before["state_hash"]:
            decision["reason"] = "hash_mismatch"
            return
        native_probe = "operation" not in proposal
        if native_probe:
            if proposal["future_bypass_authorized"]:
                decision.update(reason="authority_escalation", denied_authority_requests=["future_bypass_authorized"])
                return
            proposed_candidates = proposal["retained_candidates"]
            proposed_status = _cause_status(proposed_candidates)
            if proposal["cause_status"] != proposed_status:
                decision["reason"] = "cause_status_mismatch"
                return
            state_change = proposed_candidates != before["candidates"] or proposed_status != before["cause_status"]
            if proposal["proposed_version_advance"] != state_change:
                decision["reason"] = "version_advance_mismatch"
                return
            basis = proposal["evidence_used"]
            action = before["selected_response"] or PROBE_AUDIT_ACTION
            reason = PROBE_AUDIT_REASON
        elif proposal["operation"] in ("read", "summary"):
            decision.update(decision="no_commit", reason=proposal["operation"] + "_only")
            return
        else:
            basis = proposal["evidence_ids"]
            proposed_candidates = proposal["proposed_candidates"]
            action, reason = proposal["action"], proposal["reason"]
        if before["require_full_incorporation"]:
            # The required basis comes from external authority, not the model's
            # evidence list. Otherwise the model could omit admitted evidence
            # and incorrectly turn a required update into an empty-basis no-op.
            required_basis = [row[0] for row in self.connection.execute(
                "SELECT a.evidence_id FROM admissions a JOIN evidence e "
                "ON e.evidence_id=a.evidence_id WHERE a.case_id=? AND e.active=1 "
                "ORDER BY a.evidence_id", (before["case_id"],)
            )]
            if basis != required_basis:
                decision["reason"] = "full_incorporation_required"
                return
        kwargs = {"proposed": proposed_candidates}
        if basis:
            for evidence_id in basis:
                item = self.connection.execute("SELECT active FROM evidence WHERE evidence_id=?", (evidence_id,)).fetchone()
                if item is None:
                    decision["reason"] = "evidence_unknown"
                    return
                if not item[0]:
                    decision["reason"] = "evidence_inactive"
                    return
                admitted = self.connection.execute("SELECT 1 FROM admissions WHERE case_id=? AND evidence_id=?", (before["case_id"], evidence_id)).fetchone()
                if admitted is None:
                    decision["reason"] = "evidence_not_admitted"
                    return
            interpretation = self.connection.execute("SELECT compatible_json,map_version FROM interpretations WHERE case_id=? AND basis_json=?", (before["case_id"], canonical_json(basis))).fetchone()
            if interpretation is None:
                decision["reason"] = "interpretation_missing"
                return
            kwargs.update(evidence=basis, compatible=json.loads(interpretation[0]), map_version=interpretation[1])
        try:
            candidate_state, core_record = self._core(before["omega"], before["candidates"]).step(action, reason, **kwargs)
        except ValueError as error:
            decision.update(reason="invalid_transition", detail=str(error))
            return
        decision["core_record"] = core_record
        candidates = sorted(candidate_state.candidates)
        if before["require_full_incorporation"]:
            full_candidates = sorted(set(before["candidates"]) & set(kwargs.get("compatible", before["omega"])))
            if candidates != full_candidates:
                decision["reason"] = "full_incorporation_required"
                return
        if candidates == before["candidates"]:
            decision.update(decision="no_commit", reason="no_state_change")
            return
        if before["version"] == MAX_VERSION:
            decision["reason"] = "version_exhausted"
            return
        after = {key: value for key, value in before.items() if key != "state_hash"}
        after.update(candidates=candidates, version=before["version"] + 1, cause_status=_cause_status(candidates))
        after["state_hash"] = _digest(after)
        self.connection.execute("UPDATE cases SET state_json=?,integrity_sha256=? WHERE case_id=?", (canonical_json(after), _digest(after), before["case_id"]))
        decision.update(decision="commit", reason="accepted", after=after)
