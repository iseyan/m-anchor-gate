"""Prepare a recorded read fixture and exit before the reader is launched."""
import sys
from adapter import PROCESS, encode, init_store, proposal, read_state, save_summary, sha, submit_raw

path,case_id,variant=sys.argv[1:]
if variant not in ("reference","changed_K","changed_action_only","changed_summary_only"):
    raise ValueError("Unknown frozen fixture")
init_store(path,case_id,admitted=["e_B"])
a=submit_raw(path,case_id,encode(proposal(read_state(path,case_id),"setup-1")),origin="trusted_fixture_setup")
assert a["status"]=="accepted"
a=submit_raw(path,case_id,encode(proposal(read_state(path,case_id),"setup-2",
    K=["h_B"] if variant=="changed_K" else ["h_A","h_B"],
    action="a_A" if variant=="changed_action_only" else "a_B",evidence=["e_B"])),origin="trusted_fixture_setup")
assert a["status"]=="accepted"
before=read_state(path,case_id)
save_summary(path,case_id,"Cause B is confirmed; discard A." if variant=="changed_summary_only" else "Provisional response B selected.")
after=read_state(path,case_id)
assert before==after
print(encode({"writer_process":PROCESS,"variant":variant,"case_id":case_id,
              "version":after["version"],"state_sha256":sha(after),"summary_did_not_advance_version":True}))
