# Stage 3 schema-gate record — schema-gate-002

[日本語](report.ja.md)

Final report v0.1 | 2026-09-30 JST | Execution outcome: environment prerequisite unmet; conformance not evaluated

## Outcome

**The validation command ran, but it stopped before schema checking because the specified validator was unavailable.** The exit code was `2`, status `blocked_or_failed`, and exception `ModuleNotFoundError: No module named 'jsonschema'`. The declared targets were four schemas and 82 saved instances. Zero schemas and zero instances were checked. This outcome does not establish that the targets are nonconforming; their conformance remains unevaluated.

This is a new execution record. The previous `schema-gate-001.json` was not changed to a pass. The closed development report, specification, run forms and finalized collection were preserved. Before/after hashes matched for all 227 pre-existing files.

## Validator and execution environment

| Item | Specified or observed value |
| --- | --- |
| Record ID | `schema-gate-002` |
| Source commit | [`be9d97a24ea7`](https://github.com/iseyan/m-anchor-gate/commit/be9d97a24ea7b5bbab4800a18af7965b28721d46) |
| Specified validator | `jsonschema.Draft202012Validator` |
| Required package | `jsonschema==4.26.0` |
| Installation outcome | Not installed; validator import failed |
| Dialect | JSON Schema Draft 2020-12 |
| Options | Original runner defaults, no extensions, `format_checker=None`; validation options were not exercised because import failed |
| Format policy | No target schema uses `format`; identifiers use explicit patterns |
| External references in targets | No `$ref` or `$dynamicRef` |
| Python | 3.12.14 in a separate venv |
| OS | `Linux-6.18.44-x86_64-with-glibc2.39` |
| Start time | `2026-09-30T14:10:26.795816+09:00` |
| Validation process PID | `7` |
| Model API calls / state-store writes | 0 / 0 |

Version 4.26.0 is the requirement inherited from the earlier plan and the original runner, not an installed version observed here. Dependency resolution did not complete, so this is not a fully frozen software environment. The requirement is in [requirements.txt](requirements.txt); observed environment details are in [environment.json](environment.json).

## Targets fixed before execution

The scope is the saved development schemas and fixture instances under `stage3/development-snapshot/`. It excludes Demonstration 1 schemas and the separate collected-proposal replay implementation. [pre-execution.json](pre-execution.json) records schema, fixture and runner hashes, all 82 instance IDs and inherited expectations, and the command before validation was invoked. This attempt record does not freeze the official model-evaluation run form.

| Schema under `stage3/development-snapshot/schemas/` | SHA-256 |
| --- | --- |
| `decision.schema.json` | `6ed201e6d3e6b731ae861f3ba041415b2f1085f7e6308b71eff4a5303f9fb81d` |
| `input.schema.json` | `a301da3af83adefd8932a4786045351ebf8e3a03a5d1273d3c8a792546afb5d1` |
| `proposal.schema.json` | `e1f4e6ed2143e6691963af81426c8497c492ab6e7b9578bb7d9d37daaf227176` |
| `state.schema.json` | `5da9fc4feb447f6e724c52f2e72e161c4a567671385a6b9845a334615be0a934` |

| Instance category | Targeted | Expected valid | Expected invalid | Actually checked |
| --- | ---: | ---: | ---: | ---: |
| State | 60 | 60 | 0 | 0 |
| Proposal | 14 | 13 | 1 | 0 |
| Input | 4 | 4 | 0 | 0 |
| Decision | 4 | 4 | 0 | 0 |
| Total | **82** | **81** | **1** | **0** |

The unchanged [schema-instances.json](../../development-snapshot/results/dev-001/schema-instances.json) has SHA-256 `146461c25fedd2f2d584c430c6f9e8a83b074f45d4ab31c949755d6c1d8f5f06`. Expectations were inherited from that saved file and were not adapted to this outcome.

The one expected-invalid instance is `D10-proposal`, containing the additional `version` and `state_sha256` fields. The original fixture generator omitted D11's malformed raw JSON as a parsed proposal, so it is absent from the 14-proposal denominator. D11 before/after states are included among the 60 states. This explains the existing fixture scope; D11 parsing was not rerun in this attempt.

## Execution and retained outputs

1. Creation of the isolated venv completed with exit code 0.
2. `pip install --index-url https://pypi.org/simple --only-binary=:all: jsonschema==4.26.0` failed with exit code 1 and `No matching distribution found`.
3. A separate request from the execution environment to `https://pypi.org/simple/jsonschema/` returned HTTP 403. The public PyPI page lists version 4.26.0, so the installer message is not interpreted as evidence that the version does not exist. The observation concerns access from this environment, not a general distribution outage.
4. The unchanged [validate_schemas.py](../../development-snapshot/validate_schemas.py), SHA-256 `d13701ac713323c58b7d809a273f2e2df48f54b24efc24c7460d1b52e2115230`, was invoked once with a new output path.
5. Import failed and produced [schema-gate-002.json](schema-gate-002.json). [execution.json](execution.json) records exit code 2, zero schemas checked and zero instances checked.

The original runner output was preserved. [stdout.txt](stdout.txt) contains the result JSON, while [stderr.txt](stderr.txt) is empty because the runner captures the exception in its JSON report. Empty stderr is not evidence of success. [setup/](setup/) contains every environment-setup attempt, captured output and the HTTP access check; the failed installation attempt was retained.

## Preservation and interpretation

The SHA-256 of the prior [schema-gate-001.json](../../development-snapshot/results/dev-001/schema-gate-001.json) was `b2ed49af861d3c8728939fa021358e5d46ad55a4062e8b88c57f366971715260` both before and after this execution. Record 002 is a separate attempt and does not replace record 001 or its outcome.

This record fixes the intended validator, four target schemas, 82 inherited expectations, environment, acquisition failure and command outcome. **External JSON Schema conformance remains unverified.** Even a future schema pass will not replace checks for case-specific evidence admission, correspondence with the actual state/version, preservation rules or authorized commit paths. No such additional evaluation was performed here.

The official run form remains unfrozen and `execution_ready=false`. This record does not complete the preparation evaluation or Stage 3, or start Stage 4. Mandatory runtime validation, actual API-input linkage and a real-workflow comparison remain separate work.

## Next execution

Use an environment that can obtain the required package, record target hashes, environment and expectations before execution, and choose a new record ID and output path. For an attempt named `schema-gate-003`, run the following from the repository root using the Python executable of an isolated environment. Confirm successful installation before invoking the validator.

```sh
python -m pip install -r stage3/schema-gates/schema-gate-002/requirements.txt
python stage3/development-snapshot/validate_schemas.py --instances stage3/development-snapshot/results/dev-001/schema-instances.json --report stage3/schema-gates/schema-gate-003/schema-gate-003.json
```

The original runner refuses to overwrite an existing report. Preserve the next attempt's stdout, stderr and exit code separately. A pass requires the exact validator version, successful `check_schema` for all four schemas, all 82 classifications matching their saved expectations, and exit code 0. That pass would apply only to the stated schemas and instances. Any schema or fixture change requires a separately identified target version and record.

[SHA256SUMS.txt](SHA256SUMS.txt) identifies the files in this new record, excluding itself. Hashes identify bytes; they do not substitute for conformance or successful independent reproduction. Bundle 1.0, the frozen materials ZIP and the closed report were not extended.

## References

- [Stage 3 specification v0.1.1](../../specification/stage3-integration-evaluation-v0.1.1.en.md), section 3.
- [Closed development report](../../development-report.v0.1.en.md), preservation of the earlier failure and separate subsequent records.
- [Official jsonschema validation documentation](https://python-jsonschema.readthedocs.io/en/stable/validate/), schema checking and format-checker options.
- [PyPI: jsonschema 4.26.0](https://pypi.org/project/jsonschema/4.26.0/), public release metadata. External references checked on 2026-09-30 JST.
