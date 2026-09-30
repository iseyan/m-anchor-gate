"""Separate external JSON Schema gate; fail closed if validator is unavailable."""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--instances", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    a=p.parse_args()
    if a.report.exists():
        raise FileExistsError("Choose a new validation report; keep earlier failures")
    report={"checked_at":datetime.now(timezone.utc).isoformat(),"validator":"jsonschema.Draft202012Validator",
            "requested_package_version":"4.26.0","dialect":"2020-12","format_policy":"No format keywords; IDs use patterns.",
            "schemas":[],"instances":[],"stage3_complete":False}
    try:
        from jsonschema import Draft202012Validator
        report["installed_version"]=importlib.metadata.version("jsonschema")
        if report["installed_version"] != "4.26.0":
            raise RuntimeError("Validator version differs from the recorded plan")
        validators={}
        for f in sorted((ROOT/"schemas").glob("*.json")):
            schema=json.loads(f.read_text())
            Draft202012Validator.check_schema(schema)
            validators[f.name]=Draft202012Validator(schema)
            report["schemas"].append({"file":f.name,"valid":True})
        for row in json.loads(a.instances.read_text()):
            valid=validators[row["schema"]].is_valid(row["instance"])
            report["instances"].append({"id":row["id"],"valid":valid,"expected_valid":row["expected_valid"]})
            if valid!=row["expected_valid"]:
                raise ValueError("Schema-instance result differs from preregistered expectation: "+row["id"])
        report["status"]="passed_for_listed_development_instances"
        report["scope"]="Listed schemas and fixture instances only; future model outputs need runtime validation."
        rc=0
    except Exception as error:
        report.update(status="blocked_or_failed",error_type=type(error).__name__,error=str(error))
        rc=2
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(report,ensure_ascii=False))
    return rc

if __name__=="__main__":
    sys.exit(main())
