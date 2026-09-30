"""Create fixed development inputs and schemas before freezing/running them."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
def write(path, value):
    (ROOT / path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

text = {"type": "string", "minLength": 1, "pattern": "\\S"}
hash_id = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
version = {"type": "integer", "minimum": 0}
K = {"type": "array", "items": {"enum": ["h_A", "h_B"]}, "uniqueItems": True, "maxItems": 2}
ids = {"type": "array", "items": text, "uniqueItems": True}
def obj(props):
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}
state = obj({"schema_version": {"const": "stage3-state/v0.1"}, "case_id": text,
             "version": version, "K": K, "applied_evidence": ids, "rule_version": text,
             "action_id": {"anyOf": [text, {"type": "null"}]},
             "action_sha256": {"anyOf": [hash_id, {"type": "null"}]}})
action = obj({"case_id": text, "action_id": text, "state_version": version,
              "selected_action": {"enum": ["a_A", "a_B"]}, "reason": text})
proposal = obj({"schema_version": {"const": "stage3-proposal/v0.1"}, "proposal_id": text,
                "case_id": text, "expected_version": version, "expected_state_sha256": hash_id,
                "proposed_K": K, "selected_action": {"enum": ["a_A", "a_B"]}, "evidence_ids": ids, "reason": text})
decision = obj({"schema_version": {"const": "stage3-decision/v0.1"}, "case_id": text,
                "state_version_read": version, "state_sha256_read": hash_id,
                "selected_action": {"enum": ["a_A", "a_B"]}, "retained_candidates": K,
                "cause_status": {"enum": ["unresolved", "single_candidate_under_interpretation", "candidate_exhaustion"]}})
input_schema = obj({"schema_version": {"const": "stage3-input/v0.1"}, "state": state,
                    "state_sha256": hash_id, "action": action,
                    "admitted_evidence": {"type": "array", "items": obj({"evidence_id": text, "permitted_candidates": K}), "uniqueItems": True},
                    "new_observation_ids": ids,
                    "summary": obj({"summary_id": text, "text": {"type": "string"}, "admitted_as_evidence": {"const": False}})})
for name, s in {"input": input_schema, "state": state, "proposal": proposal, "decision": decision}.items():
    s = {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "Stage 3 development " + name, **s}
    write("schemas/" + name + ".schema.json", s)

trials = [
 {"id":"D01","name":"preserve_without_evidence","K":["h_A","h_B"]},
 {"id":"D02","name":"unsupported_removal","K":["h_B"]},
 {"id":"D03","name":"unknown_evidence","evidence":["e_unknown"],"K":["h_B"]},
 {"id":"D04","name":"action_as_evidence","evidence":["action-001"],"K":["h_B"]},
 {"id":"D05","name":"summary_as_evidence","evidence":["summary-001"],"K":["h_B"]},
 {"id":"D06","name":"registered_case_inadmissible","evidence":["e_B"],"K":["h_B"]},
 {"id":"D07","name":"wrong_case","override":{"case_id":"other-case"}},
 {"id":"D08","name":"forged_version","override":{"expected_version":7}},
 {"id":"D09","name":"forged_hash","override":{"expected_state_sha256":"0"*64}},
 {"id":"D10","name":"extra_authoritative_metadata","override":{"version":7,"state_sha256":"H7"}},
 {"id":"D11","name":"malformed_json","raw":"{\"case_id\":"},
 {"id":"D12","name":"valid_full_incorporation","admitted":["e_B"],"new_observations":["e_B"],"evidence":["e_B"],"K":["h_B"]},
 {"id":"D13","name":"reuse_existing_evidence","admitted":["e_B"],"new_observations":[],"evidence":["e_B"],"K":["h_B"]},
 {"id":"D14","name":"candidate_restoration","admitted":["e_B"],"initial_K":["h_B"],"evidence":["e_B"],"K":["h_A","h_B"]},
 {"id":"D15","name":"valid_partial_incorporation","admitted":["e_B"],"evidence":["e_B"],"K":["h_A","h_B"]}
]
write("fixtures/development-trials.json", trials)
expected = {}
accepted = {"D01", "D12", "D13", "D15"}
for t in trials:
    tid=t["id"]
    before=t.get("initial_K",["h_A","h_B"])
    expected[tid] = {"checked_status": "accepted" if tid in accepted else "rejected",
                     "comparison_status": "accepted" if tid in accepted or tid=="D02" else "rejected",
                     "checked_K": t.get("K",before) if tid in accepted else before,
                     "comparison_K": t.get("K",before) if tid in accepted or tid=="D02" else before,
                     "proposal_schema_valid": tid not in {"D10","D11"}}
write("evaluator/development-expected.json", expected)
write("fixtures/evidence-authority.json", {"version":"stage3-synthetic-evidence/v0.1",
      "authority":"host_fixed_development_fixture", "registry":{"e_B":{"permitted_candidates":["h_B"]}},
      "case_admission_rule":"Use only each predeclared trial's admitted list; registered alone is insufficient.",
      "claims_real_causation":False})
write("fixtures/development-plan.json", {"id":"stage3-adapter-development-20260929-v0.1",
      "scope":"fixed_input_development_checks_only", "stage3_evaluation_run":False,
      "model_api_calls":0, "model_identifier":None, "spending":0,
      "transition_trials":len(trials), "stores_per_trial":2, "read_processes":4,
      "retry_count":0, "expected_values_location":"evaluator/development-expected.json",
      "entry_condition_external_schema":"not_met; checked separately, not simulated",
      "comparison_only_difference":"unsupported_candidate_removal_check",
      "stop_on_unexpected_result":True, "overwriting_previous_runs":False})
print("Wrote four unvalidated schemas and 15 fixed development trial templates.")
