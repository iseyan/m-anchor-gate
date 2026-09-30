# Local installation preparation v0.1

This package checks installation of `jsonschema==4.26.0` and import/version identity of `Draft202012Validator` on the user's computer, without GitHub Actions. Git, a GitHub account and API keys are not required. Downloading the specified package and its dependencies requires access to PyPI.

Extract the entire ZIP to a writable directory. On Windows with Python 3.13 and the `py` launcher, double-click `run-preparation.cmd`, or run:

```text
py -3.13 prepare_local.py
```

With another installed Python 3.10+ interpreter, use `python prepare_local.py`; on macOS/Linux, use `python3 prepare_local.py`.

The script checks the hashes of the four schemas, existing validator script and saved 82-instance fixture file. It then creates a fresh venv under `environments/`, installs the required distribution, checks import/version identity and records observed dependency versions. Existing Python environments are not modified.

Every attempt writes a new directory under `runs/`. Installation success is recorded as `status="installation_and_import_confirmed"`, `installation_confirmed=true`, `exit_code=0` in `preparation-result.json`. Commands, timestamps, exit codes, stdout and stderr are retained, including on failure. Earlier results are not overwritten. Empty stderr alone is not treated as success.

The local installation route is not yet executed at distribution time. Success previously observed in a different environment is not a result for the user's computer. The package authoring check uses only `--inspect-only`, which does not install anything and records `installation_confirmed=false`.

This is preparation only. The script does not call `check_schema`, classify the 82 instances, call a model API or write to a state store. The saved inventory of 81 expected-valid and one expected-invalid instance is not a validation outcome.

Schema-gate-003 still requires the specified validator, successful `check_schema` for four schemas, all 82 classifications matching saved expectations and validation-command exit 0. Preparation exit 0 does not satisfy that gate. The official run form remains unfrozen, `execution_ready=false`; neither Stage 3 completion nor Stage 4 entry is claimed.

001, 002, existing preparation records, Bundle, the frozen materials ZIP and closed development reports are not included or modified. The packaged target files are byte-identical copies identified in `preparation-plan.json`. `SHA256SUMS.txt` identifies the package contents, not schema conformance.
