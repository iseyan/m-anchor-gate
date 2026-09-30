# Stage 3 environment check kit v0.1

This kit checks the frozen binding-001 with the specified validator in a local environment. The Windows check has not been run at distribution. It makes no API calls, installs no packages and uses no GitHub Actions. `execution_ready=false` remains unchanged.

## Use

1. Extract the ZIP completely.
2. Double-click `run-environment-check.cmd`.
3. Return the result ZIP shown by the command, whether the check passes or fails.

The default interpreter is the recorded schema-gate-003 venv, `local-preparation-20260930T102507Z-5db00b37/Scripts/python.exe`. Activation is unnecessary. If its location differs, pass the actual interpreter as the first CMD argument. No interpreter fallback is automatic. A different interpreter is recorded as a different observed environment, not as the original 003 environment.

If Python itself is absent, the CMD launcher stops before creating a check record. Once the Python launcher starts, an unavailable validator produces a new failure record and ZIP. It requires `jsonschema==4.26.0` and `Draft202012Validator`; it does not install dependencies or fall back to structural checks.

Outputs use a new ID beneath the sibling `stage3-environment-check-results` directory. Existing IDs are refused. Results cannot be placed inside the kit or referenced source repository. UTF-8 and disabled bytecode writing are propagated to children. Credentials and Python override environment variables are not forwarded.

## Scope

After the import/version probe, the selected interpreter runs the frozen `tests/offline_checks.py` in its default exact-validator mode. This checks four schemas and the new implementation's offline fixtures. It does not obtain live model outputs. Mock responses retain the `offline_transport_fixture` origin.

The exact-validator path contains 68 checks. The prior 69-check structural path includes one additional conditional check, `structural_checker_cannot_accept_live_origin`. This difference follows the unchanged source. It is not a deleted test or a rerun of the 82 schema-gate-003 instances.

The launcher writes a start record before checking and a separate result at the end. It retains commands, exit codes, raw stdout/stderr, failures, before/after hashes and checker outputs. Empty stderr alone never means success. The wrapper requires matching frozen bytes, the specified validator, successful exact-mode completion and all checks passing. These are criteria for this new offline check, not amendments to the four schema-gate-003 criteria.

Temporary fixture SQLite stores are written under the result directory; official run stores are not used. Python audit hooks block socket connection and name lookup in the intended check processes. They do not establish privileged-bypass resistance or general security.

Passing this check leaves the supported 8,192-input-token bound and the separate live-start record outstanding. It does not complete preparation, Stage 3 or Stage 4. Frozen conditions, binding-001, 001–003, Bundle and collected materials stay unchanged.

From repository source, invoke `run_environment_check.py --repo <repository-root>` using Python with `-I -B -X utf8`; the distribution instead contains `targets/repo`. The target manifest identifies a required subset of frozen files. The tool manifest identifies the new helper files. Hashes identify bytes, not execution or independent reproduction.
