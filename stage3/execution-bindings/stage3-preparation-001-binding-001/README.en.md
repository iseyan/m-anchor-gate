# Stage 3 pre-execution binding v0.1

`stage3-preparation-001-binding-001` / `2026-09-30T13:55:11+00:00`

This new record binds code, inputs, fixed proposals and evaluator to the unchanged conditions version. Review comments remain advisory and add no acceptance or approval authority. Basis commit: `840d6b7be93924f4781f6ac19ca53afbc592507b`. The machine-readable record is [binding.json](binding.json).

**Implementation and input binding is frozen; execution has not started.** `conditions_frozen=true`, `implementation_binding_frozen=true`, `execution_ready=false`. Full official-form freeze, preparation completion and Stage 3 completion are not claimed.

| Target | Bound artifact and scope |
| --- | --- |
| Adapter | Schema, case, version/hash, admission and preservation checks before atomic state/action/audit commit; original development adapter unchanged |
| API entry | One-shot Responses transport; raw requests/responses, usage and failures retained; zero retries or fallback; no live communication test |
| Inputs | Proposal/decision templates, seven tasks and three planned initial views; R5 requests assembled from actual saved state |
| R4 | Four complete invalid proposal byte sequences with hashes, bound to the predeclared version-1 starting state |
| Evaluator | Expected values derived from actual host reads outside model input; preservation legality separated from full-incorporation success |
| Restart | Writer exit precedes fresh reader PIDs; only case ID and store path are handed over; reads link to dispatch-candidate bytes, without a real API request ID |

The minimal candidate guard is copied byte-for-byte. No live model output is relabeled as a development fixture to bypass the old adapter restriction. Offline responses are labeled `offline_transport_fixture`; future live output uses `model_output`. Unchecked comparison stores cannot provide authoritative model input.

The final source passed **69 offline checks**. Seven main-path dispatches and five error-case dispatches are all mocks, with zero model calls. Checks cover unsupported removal, valid evidence updates, old-evidence reuse, R4 rejection in both stores, the D15 distinction, four fresh readers, summary invariance, exact request bytes, error retention, call caps and budget stops. Temporary fixture stores were written; official run stores were neither created nor updated.

| Separate check | Recorded result |
| --- | --- |
| local-check-001 | Missing pinned validator; blocked before checks. Zero checked instances is not a conformance classification |
| local-check-002 | 61 structural/semantic checks on initial code, offline |
| local-check-003 | 68 checks including added budget cases, offline |
| local-check-004 | 69 checks including source/input hash binding, offline |
| local-check-005 | 69 checks on final source, using the shared decision-call composition in the fresh readers, offline |

Reports and raw-record ZIPs remain separate under `checks/`; earlier failures and intermediate results are retained. The explicit structural checker is not a full JSON Schema validator and cannot enable live-origin acceptance or HTTP dispatch.

Both attempts to obtain `jsonschema==4.26.0` failed in this environment. This is an environment observation, not a claim that the published version is nonexistent. Schema gate 003 and its Windows receipt verification remain unchanged. Its four schemas and 82 classification matches do not establish conformance of this new implementation or future live inputs/outputs.

Remaining live-entry work is a new exact-validator check in the intended runtime and a supported input-token counting/bounding method with an exact-request record proving the frozen 8,192-token cap. This binding does not treat a byte count as an established token count. Missing bounds stop dispatch. No additional counting API is called or added to the seven-call plan. Account access remains unverified; this record does not add an account-access proof to acceptance criteria.

A separate execution-context record will bind runtime, current costs and output paths. Actual API receipts and results belong in new records outside this directory. Do not append readiness or completion to the conditions or this binding. Creation used no model calls or paid inference and no GitHub Actions. 001–003, Bundle, the materials ZIP, closed reports and frozen ledger remain unchanged.

`runtime-manifest.json` identifies code, templates and fixed proposals and is checked on load. `FILES.sha256` identifies the files in this new record. Hashes do not prove API execution or independent reproduction.

Implementation sources: [Responses](https://developers.openai.com/api/reference/cli/resources/responses/methods/create), [JSON output](https://developers.openai.com/api/docs/guides/structured-outputs), [token counting](https://developers.openai.com/api/docs/guides/token-counting).
