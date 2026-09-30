# Schema gate 003: local execution record

**Outcome: the four existing acceptance criteria were satisfied for the four fixed schemas and 82 listed fixtures.**

Run ID: `schema-gate-003-20260930T104603Z-36d5c5c4`  
Execution: 2026-09-30 10:46:03–10:46:04 UTC (19:46:03–19:46:04 JST)  
Japanese companion: [report.ja.md](report.ja.md)

This report reviews records of validation executed by the user on Windows. The reviewer compared the uploaded original records with the fixed targets and did not rerun the Windows validation.

## 1. The four acceptance criteria

| Existing criterion | Evidence in the received records |
| --- | --- |
| Specified `jsonschema==4.26.0` / `Draft202012Validator` | Version, class and Draft 2020-12 match |
| Successful `check_schema` for all four schemas | All four succeeded |
| All 82 classifications match saved expectations | 82 matches; zero mismatches |
| Validation command exits with code 0 | PID 3332, exit 0, no timeout |

The launcher also exited with code 0. The validator report and stdout parse to the same JSON object. Empty stderr is not the basis for the pass decision. These four criteria are unchanged from those fixed following 002.

## 2. Validator and targets

The environment is Windows 11, Python 3.13.5 and `jsonschema==4.26.0`. The imported class is `jsonschema.validators.Draft202012Validator`, using Draft 2020-12. No `format` keywords are used; identifier constraints use patterns.

The targets are the following six files under `stage3/development-snapshot/`: four schemas, the unchanged validator script and the file containing 82 fixtures. Execution used byte-identical copies under the preparation kit's `targets/` directory. Reported hashes before and after execution match the fixed repository files.

| Relative path | SHA-256 |
| --- | --- |
| `schemas/decision.schema.json` | `6ed201e6d3e6b731ae861f3ba041415b2f1085f7e6308b71eff4a5303f9fb81d` |
| `schemas/input.schema.json` | `a301da3af83adefd8932a4786045351ebf8e3a03a5d1273d3c8a792546afb5d1` |
| `schemas/proposal.schema.json` | `e1f4e6ed2143e6691963af81426c8497c492ab6e7b9578bb7d9d37daaf227176` |
| `schemas/state.schema.json` | `5da9fc4feb447f6e724c52f2e72e161c4a567671385a6b9845a334615be0a934` |
| `validate_schemas.py` | `d13701ac713323c58b7d809a273f2e2df48f54b24efc24c7460d1b52e2115230` |
| `results/dev-001/schema-instances.json` | `146461c25fedd2f2d584c430c6f9e8a83b074f45d4ab31c949755d6c1d8f5f06` |

The inventory comprises 60 states, 14 parsed proposals, four inputs and four decisions. There were 81 valid instances and one expected invalid instance, `D10-proposal`. The result is **82 matching classifications**, not 82 valid instances.

D11's malformed raw JSON is excluded from the saved denominator of 14 parsed proposals and was not retested as raw JSON in this gate. Its four before/after states are included among the 82 fixtures. Neither targets nor expected classifications were changed to fit results. The distinction between preservation legality and an unmet full-incorporation task in D15 was not reassessed by schema validation.

## 3. Link from preparation to execution

Preparation ID: `local-preparation-20260930T102507Z-5db00b37`. The preparation result included in the ZIP is byte-identical to the result previously received.

- Preparation-result SHA-256: `f04a9b7a2a4660cde8d3b18ab3f967f827750957b4fd26c98c983e54cb0c6422`
- Executed launcher SHA-256: `a070097fa20eb9c9bd2cb0089ae357786a4502d435c587e589df06f5d36797bf`
- Corresponding published source commit: `3df3b4310094c47f1553fdc997cf0b1e816a57e2`

The preparation result's `installed_environment.executable`, the validation record's `python_executable` and the first argument of the actual validation command identify the same Python executable. The venv prefix and Python version also match. The unchanged `validate_schemas.py` was invoked with `-I -B -X utf8`, `--instances` and `--report`; the exact command and PID are retained in the original records.

The pre-execution `run-start.json` retains false started/pass flags; the completed `run-result.json` records true started/pass flags. The start record was not rewritten to match the outcome.

The output directory is `schema-gate-003-results/schema-gate-003-20260930T104603Z-36d5c5c4` on the desktop, outside the extracted preparation kit and under a separate ID. Model calls: zero. State-store writes: zero. GitHub Actions: not used.

## 4. Preserved original records

The [received ZIP](received/schema-gate-003-20260930T104603Z-36d5c5c4.zip) is 9,366 bytes with SHA-256 `04481b4f2c3d52aafbe880882f55836a09d24d57666514eb875ba05b4732f30a`. Its ten files are preserved byte-for-byte under [run/schema-gate-003-20260930T104603Z-36d5c5c4/](run/schema-gate-003-20260930T104603Z-36d5c5c4/). All nine files listed by the manifest, excluding the manifest itself, match their declared SHA-256 values. [verification.json](verification.json) records the receipt checks.

Hashes identify the container and bytes and support consistency checks between records. They do not independently establish execution or reproducibility.

## 5. Scope and remaining work

This closes the schema gate for the fixed schemas and 82 listed development fixtures. It does not complete preparation evaluation as a whole, live model integration evaluation or real-workflow comparison. Schema conformance does not substitute for case-specific evidence admissibility, version/hash correspondence, candidate preservation or checked commit paths. No claim is made about prompt-injection resistance or model improvement.

The official run form remains unfrozen, `execution_ready=false`, Stage 3 is incomplete and Stage 4 has not started. The next work is a separate official run form fixing the still-unselected model identifier/settings, trial count, spending limit and case-admitted evidence before model execution.

No changes are made to 001, 002, existing closures, the Actions preparation record, distributed preparation ZIP, Bundle, frozen materials ZIP or closed development report. Success in 003 does not rewrite earlier failed attempts as passes.
