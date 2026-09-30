"""Fixed proposal replay. These inputs are not passed to the resumed process."""

import argparse
import json
from demo1 import PROCESS, checked_save, initialize, save_summary


def write_case(store, case_id, scenario):
    initialize(store, case_id)
    proposal = {"action_record_id": "action-001", "selected_action": "a_B",
                "reason": "Provisional choice required by the submission procedure",
                "evidence_ids": ["e_B"] if scenario == "control" else [],
                "proposed_K": ["h_B"] if scenario == "control" else ["h_A", "h_B"]}
    accepted = checked_save(store, case_id, proposal)
    if accepted["status"] != "accepted":
        raise RuntimeError(accepted["rejection_reason"])
    save_summary(store, case_id, "暫定対応Bを選択した。", "Provisional response B was selected.")
    if scenario == "rejections":
        for evidence in ([], ["unregistered-evidence"], ["action-001"], ["summary-001"]):
            attempt = dict(proposal, proposed_K=["h_B"], evidence_ids=evidence)
            audit = checked_save(store, case_id, attempt)
            if audit["status"] != "rejected":
                raise RuntimeError("An invalid update was accepted")
    return {"case_id": case_id, "writer_process": PROCESS, "completed": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--scenario", required=True, choices=["main", "control", "rejections"])
    args = parser.parse_args()
    print(json.dumps(write_case(args.store, args.case_id, args.scenario), ensure_ascii=True))
