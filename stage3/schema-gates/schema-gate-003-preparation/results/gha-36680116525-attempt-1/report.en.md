# Schema gate 003: installation preparation check

**Installation, import and exact-version verification succeeded. Schema-gate-003 validation has not started.**

On 30 September 2026, a fresh venv on a separate GitHub Actions runner installed `jsonschema==4.26.0`. The probe imported `Draft202012Validator` and verified the distribution version. Exit 0 in this record belongs to the preparation command; it is not a schema-gate pass.

## Execution identity

| Item | Observation |
| --- | --- |
| Run | [36680116525 / attempt 1](https://github.com/iseyan/m-anchor-gate/actions/runs/36680116525) |
| Source commit | `7135d8725dd5b6f12f557284e077cf136e40cfb9` |
| Preparation start/end, UTC | `2026-09-30T06:47:53.313107+00:00` → `2026-09-30T06:47:57.566544+00:00` |
| Separate environment | GitHub-hosted `ubuntu-24.04`, image `20260920.314.1`, fresh venv |
| Python | `3.12.14` |
| Validator | `jsonschema==4.26.0` / `jsonschema.validators.Draft202012Validator` |
| Preparation commands | Venv creation, installation, import/version probe and dependency inventory each exited 0 |
| Retrieved artifact | ID `11081871547`, 13 files |

The workflow, preparation script and [target plan](../../preparation-plan.v0.1.json) were fixed in the source commit before execution. The recorded `GITHUB_SHA` matches the checked-out commit. [github-actions-receipt.json](github-actions-receipt.json) links the API run metadata to the artifact. [preparation-result.json](artifact/preparation-result.json) retains commands, PIDs, timestamps and exit codes.

## Scope checked

The six fixed source files comprise four schemas, the existing validation script and the file containing 82 fixture instances. Their SHA-256 values matched the plan and remained unchanged during preparation. The inventory of 82 instances, with 81 expected valid and one expected invalid, identifies saved targets; it is not a validation result.

No `check_schema`, instance validation or invocation of the existing `validate_schemas.py` occurred. Schemas checked: 0. Instances checked: 0. Model API calls: 0. State-store writes: 0. Success was determined from installation exit status and the probe's output and version, not from empty stderr.

[requirements-observed.txt](artifact/requirements-observed.txt) records the installed dependency versions. These are observations after installation, not a claim that every dependency version was frozen beforehand. [pip-install-report.json](artifact/pip-install-report.json) retains download locations and distribution hashes.

The downloaded ZIP's SHA-256 matched GitHub's artifact digest. All 13 extracted files were retained unchanged; 12 members matched the artifact's `SHA256SUMS.txt`. Hashes identify the retained record and do not establish schema conformance or reproducibility. The ZIP itself was not added to the repository.

## Status and remaining work

This check resolves whether the specified validator can be installed and imported in the separate environment. The hosted runner is ephemeral. A future schema-gate-003 validation job must confirm installation first and then invoke the validator in that same job environment.

The existing four gate criteria remain unchanged:

1. Use `jsonschema==4.26.0` / `Draft202012Validator`.
2. Pass `check_schema` for all four target schemas.
3. Match all 82 saved expected classifications.
4. Exit the validation command with code 0.

This preparation record does not evaluate criteria 2–4. The official run form remains unfrozen and `execution_ready=false`. It does not establish Stage 3 preparation completion, Stage 3 completion or Stage 4 entry.

The preparation source commit preserves all 246 preceding files as the same Git blobs. No changes or additions were made to 001, 002, their closure records, Bundle, the frozen materials ZIP or the closed development report. Schema-gate-003 validation must have a separate ID and output record.
