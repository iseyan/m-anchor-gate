"""Local, single-case API prototype. No model calls or action execution."""

from __future__ import annotations

import base64
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import sys


API_VERSION = "stage4-local-api/v0.1"
_STORE_KIND = "m-anchor-gate.stage4.local-prototype"
_OMEGA = frozenset({"h_A", "h_B"})
_PROPOSAL_FIELDS = {
    "proposal_id", "case_id", "expected_version", "expected_state_sha256",
    "proposed_K", "selected_action", "evidence_ids", "reason",
}
_CORE_PATH = (Path(__file__).resolve().parents[2]
              / "demonstration1/demo1/m_anchor_minimal.py")
_SPEC = importlib.util.spec_from_file_location("_stage4_demo1_guard", _CORE_PATH)
_CORE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _CORE
_SPEC.loader.exec_module(_CORE)


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _hash(state):
    return hashlib.sha256(_json(state).encode("utf-8")).hexdigest()


def _nonempty(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


def _ids(value, field):
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    for item in value:
        _nonempty(item, field)
    if len(value) != len(set(value)):
        raise ValueError(f"{field} contains duplicate IDs")
    return set(value)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _constant(value):
    raise ValueError(f"Non-JSON constant: {value}")


def _status(candidates):
    if not candidates:
        return "candidate_exhaustion"
    return "single_candidate" if len(candidates) == 1 else "unresolved"


class GateAPI:
    """One SQLite store per case; evidence admission belongs to initialization."""

    def __init__(self, db_path):
        self.db_path = Path(db_path).resolve()
        with self._connection() as connection:
            self._config = self._read_config(connection)
        self.case_id = self._config["case_id"]

    @classmethod
    def initialize(cls, db_path, case_id, admitted_evidence=()):
        """Create a new store exclusively. Existing files are never replaced."""
        _nonempty(case_id, "case_id")
        if isinstance(admitted_evidence, (str, bytes)):
            raise ValueError("admitted_evidence must be a collection of IDs")
        admitted = _ids(list(admitted_evidence), "admitted_evidence")
        if not admitted <= {"e_B"}:
            raise ValueError("Only synthetic registry evidence e_B is available")
        path = Path(db_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(descriptor)
        connection = None
        try:
            connection = sqlite3.connect(str(path))
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("CREATE TABLE metadata (config TEXT NOT NULL)")
            connection.execute("CREATE TABLE state (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
            connection.execute("CREATE TABLE actions (action_id TEXT PRIMARY KEY, proposal_id TEXT UNIQUE NOT NULL, payload TEXT NOT NULL)")
            connection.execute("CREATE TABLE summaries (id INTEGER PRIMARY KEY, text TEXT NOT NULL)")
            connection.execute("CREATE TABLE audit (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
            config = {"kind": _STORE_KIND, "api_version": API_VERSION,
                      "case_id": case_id, "admitted_evidence": sorted(admitted)}
            state = {"case_id": case_id, "version": 0, "K": sorted(_OMEGA),
                     "status": "unresolved", "action_id": None,
                     "applied_evidence": []}
            connection.execute("INSERT INTO metadata VALUES (?)", (_json(config),))
            connection.execute("INSERT INTO state VALUES (1, ?)", (_json(state),))
            connection.commit()
        except Exception:
            if connection is not None:
                connection.close()
                connection = None
            path.unlink()
            raise
        finally:
            if connection is not None:
                connection.close()
        return cls(path)

    @contextmanager
    def _connection(self):
        # mode=rw prevents accidental store creation during a read/open.
        connection = sqlite3.connect(self.db_path.as_uri() + "?mode=rw", uri=True)
        try:
            yield connection
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _read_config(connection):
        try:
            rows = connection.execute("SELECT config FROM metadata").fetchall()
            if len(rows) != 1:
                raise ValueError("Invalid prototype metadata")
            config = json.loads(rows[0][0])
            if (not isinstance(config, dict)
                    or config.get("kind") != _STORE_KIND
                    or config.get("api_version") != API_VERSION):
                raise ValueError("Not a compatible Stage 4 prototype store")
            _nonempty(config["case_id"], "case_id")
            if not _ids(config["admitted_evidence"], "admitted_evidence") <= {"e_B"}:
                raise ValueError("Unknown admitted evidence")
            return config
        except (sqlite3.DatabaseError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("Not a compatible Stage 4 prototype store") from exc

    @contextmanager
    def _transaction(self, case_id, write=False):
        if case_id != self.case_id:
            raise ValueError("Unknown host case_id")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            if self._read_config(connection) != self._config:
                raise ValueError("Prototype store metadata changed")
            yield connection
            connection.commit()

    def _view(self, connection):
        row = connection.execute("SELECT payload FROM state WHERE id=1").fetchone()
        if row is None:
            raise ValueError("Missing authoritative state")
        state = json.loads(row[0])
        if state["case_id"] != self.case_id:
            raise ValueError("Stored case mismatch")
        action = None
        if state["action_id"] is not None:
            row = connection.execute("SELECT payload FROM actions WHERE action_id=?",
                                     (state["action_id"],)).fetchone()
            if row is None:
                raise ValueError("Missing linked action")
            action = json.loads(row[0])
            if (action["action_id"] != state["action_id"]
                    or action["state_version"] != state["version"]):
                raise ValueError("Stored action/version mismatch")
        summary = connection.execute("SELECT text FROM summaries ORDER BY id DESC LIMIT 1").fetchone()
        return {"state": state, "state_sha256": _hash(state), "action": action,
                "admitted_evidence": list(self._config["admitted_evidence"]),
                "summary": summary[0] if summary else None}

    def read(self, case_id):
        with self._transaction(case_id) as connection:
            return self._view(connection)

    @staticmethod
    def _append_audit(connection, record):
        cursor = connection.execute("INSERT INTO audit(payload) VALUES (?)", (_json(record),))
        return {"audit_id": cursor.lastrowid, **record}

    def submit(self, case_id, raw: bytes):
        """Validate raw proposal bytes, then commit state/action/audit together."""
        if not isinstance(raw, bytes):
            raise ValueError("raw must be bytes")
        with self._transaction(case_id, write=True) as connection:
            before = self._view(connection)
            record = {
                "record_type": "proposal", "case_id": case_id,
                "recorded_at": datetime.now(timezone.utc).isoformat(), "pid": os.getpid(),
                "raw_base64": base64.b64encode(raw).decode("ascii"),
                "raw_sha256": hashlib.sha256(raw).hexdigest(), "proposal_id": None,
                "status": "rejected", "rejection_reason": None,
                "state_before": before["state"], "state_after": before["state"],
                "state_sha256_before": before["state_sha256"],
                "state_sha256_after": before["state_sha256"],
                "action_before": before["action"], "action_after": before["action"],
                "applied_evidence": [],
            }
            try:
                proposal = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                                      parse_constant=_constant)
                _json(proposal).encode("utf-8")
                if not isinstance(proposal, dict) or set(proposal) != _PROPOSAL_FIELDS:
                    raise ValueError("Proposal fields do not match the API contract")
                for field in ("proposal_id", "case_id", "expected_state_sha256", "reason"):
                    _nonempty(proposal[field], field)
                record["proposal_id"] = proposal["proposal_id"]
                if proposal["case_id"] != case_id:
                    raise ValueError("Proposal case_id mismatch")
                if type(proposal["expected_version"]) is not int:
                    raise ValueError("expected_version must be an integer")
                if proposal["expected_version"] != before["state"]["version"]:
                    raise ValueError("State version mismatch")
                if proposal["expected_state_sha256"] != before["state_sha256"]:
                    raise ValueError("State hash mismatch")
                proposed = _ids(proposal["proposed_K"], "proposed_K")
                evidence = _ids(proposal["evidence_ids"], "evidence_ids")
                if proposal["selected_action"] not in ("a_A", "a_B"):
                    raise ValueError("Unknown selected_action")
                if not evidence <= {"e_B"}:
                    raise ValueError("Unregistered evidence ID")
                if not evidence <= set(self._config["admitted_evidence"]):
                    raise ValueError("Evidence is not admitted for this case")
                if connection.execute("SELECT 1 FROM actions WHERE proposal_id=?",
                                      (proposal["proposal_id"],)).fetchone():
                    raise ValueError("Accepted proposal_id cannot be reused")
                core = _CORE.MAnchor(_OMEGA, frozenset(before["state"]["K"]))
                after_core, core_record = core.step(
                    proposal["selected_action"], proposal["reason"], evidence=evidence,
                    compatible={"h_B"} if evidence else None,
                    map_version="synthetic-e_B/v1" if evidence else None,
                    proposed=proposed,
                )
                version = before["state"]["version"] + 1
                action_id = f"action-{version:03d}"
                state = {"case_id": case_id, "version": version,
                         "K": sorted(after_core.candidates),
                         "status": _status(after_core.candidates),
                         "action_id": action_id, "applied_evidence": sorted(evidence)}
                action = {"action_id": action_id, "value": proposal["selected_action"],
                          "reason": proposal["reason"], "proposal_id": proposal["proposal_id"],
                          "state_version": version}
            except (ValueError, UnicodeError, RecursionError) as exc:
                record["rejection_reason"] = str(exc)
            else:
                connection.execute("UPDATE state SET payload=? WHERE id=1", (_json(state),))
                connection.execute("INSERT INTO actions VALUES (?, ?, ?)",
                                   (action_id, proposal["proposal_id"], _json(action)))
                record.update(status="accepted", state_after=state,
                              state_sha256_after=_hash(state), action_after=action,
                              applied_evidence=sorted(evidence), core_audit=core_record["audit"])
            return self._append_audit(connection, record)

    def save_summary(self, case_id, text):
        if not isinstance(text, str):
            raise ValueError("summary must be a string")
        # Ensure it can be stored as UTF-8 before entering the transaction.
        text.encode("utf-8")
        with self._transaction(case_id, write=True) as connection:
            view = self._view(connection)
            cursor = connection.execute("INSERT INTO summaries(text) VALUES (?)", (text,))
            return self._append_audit(connection, {
                "record_type": "summary", "case_id": case_id,
                "recorded_at": datetime.now(timezone.utc).isoformat(), "pid": os.getpid(),
                "summary_id": f"summary-{cursor.lastrowid:03d}", "summary": text,
                "state_before": view["state"], "state_after": view["state"],
                "state_sha256_before": view["state_sha256"],
                "state_sha256_after": view["state_sha256"],
            })

    def history(self, case_id):
        with self._transaction(case_id) as connection:
            return [{"audit_id": row[0], **json.loads(row[1])} for row in
                    connection.execute("SELECT id, payload FROM audit ORDER BY id")]

    def assess(self, case_id):
        view = self.read(case_id)
        state, action = view["state"], view["action"]
        selected = action["value"] if action else None
        action_en = f"{selected} selected" if selected else "no action selected"
        action_ja = f"{selected}は選択済み" if selected else "対応は未選択"
        if state["status"] == "unresolved":
            cause_en, cause_ja = "cause A/B unresolved", "原因A・Bは未決"
        elif state["status"] == "candidate_exhaustion":
            cause_en, cause_ja = "candidate exhaustion", "候補は空集合"
        else:
            candidate = state["K"][0]
            cause_en, cause_ja = f"only {candidate} remains", f"候補は{candidate}のみ"
        return {"case_id": case_id, "version": state["version"],
                "state_sha256": view["state_sha256"], "candidates": state["K"],
                "action": action, "status": state["status"], "pid": os.getpid(),
                "assessment_en": f"{action_en}; {cause_en}",
                "assessment_ja": f"{action_ja}／{cause_ja}",
                "summary_used_for_decision": False}
