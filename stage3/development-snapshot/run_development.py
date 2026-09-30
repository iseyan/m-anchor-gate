"""Recorded fixed-input development checks; not a Stage 3 evaluation run."""
import argparse
import base64
from contextlib import closing
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

import adapter as a

ROOT=Path(__file__).resolve().parent
def filehash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
def counts(path,case_id):
    with closing(a.connect(path)) as con:
        return dict(con.execute("SELECT kind,count(*) FROM records WHERE case_id=? GROUP BY kind",(case_id,)))
def diff(left,right,prefix=""):
    if isinstance(left,dict) and isinstance(right,dict):
        result=[]
        for key in sorted(set(left)|set(right)):
            if key not in left or key not in right: result.append(prefix+"/"+key)
            else: result.extend(diff(left[key],right[key],prefix+"/"+key))
        return result
    return [] if left==right else [prefix]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    out=args.output.resolve()
    if out.exists(): raise FileExistsError("Previous run directory must be retained; use a new directory")
    out.mkdir(parents=True)
    trials=json.loads((ROOT/"fixtures/development-trials.json").read_text())
    expected=json.loads((ROOT/"evaluator/development-expected.json").read_text())
    plan=json.loads((ROOT/"fixtures/development-plan.json").read_text())
    source_files=[p for p in ROOT.rglob("*") if p.is_file() and not any(x in p.parts for x in ("results","__pycache__")) and p.suffix in (".py",".json",".txt",".md")]
    freeze={"plan":plan,"frozen_before_execution_at":a.now(),"source_sha256":{str(p.relative_to(ROOT)):filehash(p) for p in sorted(source_files)},
            "model_api_calls":0,"is_stage3_evaluation":False,"external_schema_entry_condition_met":False,
            "environment":{"python":sys.version,"platform":platform.platform(),"adapter":a.VERSION}}
    dump(out/"pre-execution.json",freeze)
    records=[]
    instances=[]
    reads=[]
    reason_fragments={"D02":"Unsupported removal", "D03":"unregistered_evidence_id",
      "D04":"unregistered_evidence_id","D05":"unregistered_evidence_id","D06":"case_inadmissible_evidence",
      "D07":"case_mismatch","D08":"stale_or_forged_version","D09":"state_hash_mismatch",
      "D10":"proposal_field_mismatch","D11":"Expecting value","D14":"candidate_restoration"}
    result={"run_id":plan["id"],"scope":"fixed_input_development_checks_only",
            "stage3_model_evaluation":"not_started","external_schema_gate":"not_met",
            "model_api_calls":0,"transition_trial_results":[],"read_process_results":[],
            "schema_conformance":"not_claimed","stop_on_unexpected_result":True}
    try:
        for t in trials:
            tid=t["id"]
            case_id="dev-"+tid
            paths={mode:out/(tid+"-"+mode+".sqlite3") for mode in ("checked","comparison")}
            for mode,path in paths.items():
                a.init_store(path,case_id,t.get("admitted",[]),t.get("new_observations",[]),comparison=mode=="comparison")
                setup=a.submit_raw(path,case_id,a.encode(a.proposal(a.read_state(path,case_id),"setup-1")),origin="trusted_fixture_setup")
                assert setup["status"]=="accepted"
                if "initial_K" in t:
                    setup=a.submit_raw(path,case_id,a.encode(a.proposal(a.read_state(path,case_id),"setup-2",K=t["initial_K"],evidence=["e_B"])),origin="trusted_fixture_setup")
                    assert setup["status"]=="accepted"
                before=a.read_state(path,case_id)
                a.save_summary(path,case_id,"Provisional response B selected.")
                assert before==a.read_state(path,case_id)
            before=a.read_state(paths["checked"],case_id)
            assert before==a.read_state(paths["comparison"],case_id)
            prop=a.proposal(before,tid,K=t.get("K"),evidence=t.get("evidence",[]))
            prop.update(t.get("override",{}))
            raw=t.get("raw",a.encode(prop))
            raw_file=out/(tid+".raw.txt")
            raw_file.write_text(raw)
            if "raw" not in t:
                instances.append({"id":tid+"-proposal","schema":"proposal.schema.json","instance":prop,"expected_valid":expected[tid]["proposal_schema_valid"]})
            pair={"id":tid,"name":t["name"],"raw_file":raw_file.name,"raw_sha256":filehash(raw_file),"outcomes":{}}
            for mode,path in paths.items():
                c0=counts(path,case_id)
                audit=a.submit_raw(path,case_id,raw)
                c1=counts(path,case_id)
                records.append(audit)
                with (out/"transition-audit.jsonl").open("a") as log: log.write(a.encode(audit)+"\n")
                assert base64.b64decode(audit["raw_response_base64"])==raw.encode()
                assert audit["raw_response_sha256"]==pair["raw_sha256"]
                assert audit["status"]==expected[tid][mode+"_status"], (tid,mode,"unexpected_status")
                assert audit["state_after"]["K"]==expected[tid][mode+"_K"], (tid,mode,"unexpected_K")
                delta=1 if audit["status"]=="accepted" else 0
                assert audit["state_after"]["version"]==before["version"]+delta
                assert c1["state"]==c0["state"]+delta and c1["action"]==c0["action"]+delta
                assert c1["audit"]==c0["audit"]+1
                if not delta:
                    assert audit["state_after"]==before
                    assert audit["state_hash_after"]==audit["state_hash_before"]
                    assert reason_fragments[tid] in audit["rejection_reason"]
                else:
                    with closing(a.connect(path)) as con:
                        action=a.latest(con,case_id,"action",audit["state_after"]["action_id"])
                        assert action["state_version"]==audit["state_after"]["version"]
                        assert a.sha(action)==audit["state_after"]["action_sha256"]
                for which in ("before","after"):
                    instances.append({"id":tid+"-"+mode+"-state-"+which,"schema":"state.schema.json","instance":audit["state_"+which],"expected_valid":True})
                pair["outcomes"][mode]={"status":audit["status"],"version":audit["state_after"]["version"],
                                        "K":audit["state_after"]["K"],"rejection_reason":audit["rejection_reason"]}
            pair["passed_development_expectation"]=True
            result["transition_trial_results"].append(pair)
            dump(out/"result.json",result)
        variants=("reference","changed_K","changed_action_only","changed_summary_only")
        for variant in variants:
            path=out/("read-"+variant+".sqlite3")
            case_id="dev-read"
            writer=subprocess.run([sys.executable,str(ROOT/"reader_fixture_writer.py"),str(path),case_id,variant],capture_output=True,text=True)
            (out/(variant+"-writer.stdout")).write_text(writer.stdout)
            (out/(variant+"-writer.stderr")).write_text(writer.stderr)
            assert writer.returncode==0,(variant,"writer_failed")
            writer_record=json.loads(writer.stdout)
            # subprocess.run has waited for this writer to exit before launch.
            reader=subprocess.run([sys.executable,str(ROOT/"adapter.py"),"resume",str(path),case_id],capture_output=True,text=True)
            (out/(variant+"-reader.stdout")).write_text(reader.stdout)
            (out/(variant+"-reader.stderr")).write_text(reader.stderr)
            assert reader.returncode==0,(variant,"reader_failed")
            read=json.loads(reader.stdout)
            assert writer_record["writer_process"]["pid"]!=read["trace"]["reader_process"]["pid"]
            assert writer_record["state_sha256"]==read["trace"]["state_sha256_read"]
            assert a.sha(read["input"])==read["trace"]["input_sha256"]
            assert a.read_state(path,case_id)["version"]==2
            expected_K=["h_B"] if variant=="changed_K" else ["h_A","h_B"]
            expected_action="a_A" if variant=="changed_action_only" else "a_B"
            assert read["decision"]["retained_candidates"]==expected_K
            assert read["decision"]["selected_action"]==expected_action
            assert read["decision"]["cause_status"]==("single_candidate_under_interpretation" if variant=="changed_K" else "unresolved")
            reads.append(read)
            for kind in ("input","decision"):
                instances.append({"id":variant+"-"+kind,"schema":kind+".schema.json","instance":read[kind],"expected_valid":True})
            result["read_process_results"].append({"variant":variant,"writer":writer_record,
                "writer_exited_before_reader_launch":True,"writer_exit_code":writer.returncode,
                "reader_exit_code":reader.returncode,"read_trace":read["trace"],"decision":read["decision"],
                "actual_input_difference_paths":diff(reads[0]["input"],read["input"]),
                "passed_deterministic_development_expectation":True,"model_observation":False})
            dump(out/"result.json",result)
        assert reads[0]["input"]["state"]==reads[3]["input"]["state"]
        assert reads[0]["decision"]==reads[3]["decision"]
        result.update(status="passed_development_checks",transition_trials_passed=len(trials),
                      store_submissions=len(records),fresh_reader_processes_passed=len(reads),
                      unsupported_removal_comparison_differences=["D02"],
                      live_model_performance_inference=False,stage3_preparation_complete=False,
                      next_gate="External JSON Schema validation and a frozen live-model run form remain required.")
        rc=0
    except Exception as error:
        result.update(status="failed_development_check",failure_type=type(error).__name__,failure=str(error),
                      failure_preserved=True,progression_stopped=True)
        rc=1
    dump(out/"schema-instances.json",instances)
    dump(out/"result.json",result)
    print(json.dumps({"status":result["status"],"output":str(out),"transition_trials_recorded":len(result["transition_trial_results"]),"read_processes_recorded":len(result["read_process_results"]),"model_api_calls":0}))
    return rc

if __name__=="__main__": sys.exit(main())
