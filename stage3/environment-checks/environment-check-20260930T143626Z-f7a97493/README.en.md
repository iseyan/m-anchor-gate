# New-code local environment check — received-record verification

Run: `environment-check-20260930T143626Z-f7a97493`. The user executed the frozen check on Windows. The received records, source snapshots and saved states support successful completion of all 68 exact-validator checks. **This local check passed; overall preparation remains incomplete and `execution_ready=false`.**

Execution was recorded on 30 September 2026, 14:36:26–14:36:33 UTC (23:36:26–23:36:33 JST). The receiver did not rerun the Windows checker or jsonschema. This is receipt and consistency verification, not independent reproduction.

| Item | Verified position |
| --- | --- |
| Python | 3.13.5; executable path, venv prefix and version match the recorded 003 environment |
| Validator | `jsonschema==4.26.0`, `Draft202012Validator` |
| Mode | `exact_jsonschema`; no structural fallback |
| Outcome | All 68 named checks passed; probe and checker exit codes were 0 |
| Archive | 156 files; all 155 payload checksum entries match, excluding the checksum manifest itself |
| Frozen targets | Before/after records for 44 target files and 7 helper files match published bytes |
| Source snapshots | 22 code/template/fixture/test files and the runtime manifest match the fixed binding |
| Calls | 0 model API calls, 0 count API calls; 7 main and 5 auxiliary error fixture dispatches |
| Storage | New output outside the kit; temporary fixture SQLite writes, 0 official-run store writes |

The import probe's `schema_checks_performed=false` describes only that probe. The subsequent default checker uses the frozen `Contracts`, which calls `check_schema` for four schemas before runtime validation. Its received successful record supports this path. This does not certify future live inputs or outputs.

The earlier 69-check structural route contains one additional structural-only branch. The present 68 checks are the complete unchanged exact-validator route. They are not a rerun of the 82 development instances in 003 and do not change earlier missing-validator failures into passes.

Writer PID 32956 ended before the recorded reader accesses. The receipt check linked SQLite state/action/summary records to reader views, exact unsent request bytes and mock decisions.

| Trial | Reader PID | Saved version | K | Action | Mock cause status |
| --- | ---: | ---: | --- | --- | --- |
| A001 reference | 11056 | 1 | h_A, h_B | a_B | unresolved |
| A002 changed candidates | 32408 | 2 | h_B | a_B | single candidate under synthetic interpretation |
| A003 changed action | 18756 | 2 | h_A, h_B | a_A | unresolved |
| A004 changed summary | 25216 | 1 | h_A, h_B | a_B | unresolved |

A004 changes only the summary; saved state, action and decision match A001. A003 advances the version through a checked action save. Preserved request bytes conform to the fixed assembly without inherited conversation or evaluator answers. They were not sent to an API, so this is not live API linkage verification.

Among identical-proposal replays P001–P003, only P001 differs in commit outcome: unsupported removal is rejected by the checked store and accepted by the comparator. P002 permits full incorporation of admitted evidence. P003 remains preservation-legal while failing the full-incorporation task. The difference concerns the gate, not model improvement.

All four R4 fixed invalid categories are rejected in both stores without changing the state/version/hash or state/action counts. Nine additional invalid proposals and timeout/refusal/incomplete/malformed-envelope/model-mismatch fixtures are retained. The live entry is blocked before budget reservation.

The `offline-*` IDs, HTTP 200, usage and charge estimates in these artifacts are simulated response fields. They establish neither real API responses or charges nor an input-token bound. Account access remains unverified.

The frozen condition and implementation binding are inherited. This receipt satisfies the remaining task of checking the new code with the specified validator in an observed environment and retaining a separate result. The supported full-request bound of 8,192 tokens is still unresolved. Count requests cannot be added by silently redefining the frozen call total. Resolve the method and exact-request linkage, then bind runtime, current costs and the absolute output root in a separate live-start record.

Do not amend the condition form, binding-001, context-001, 001–003, distribution kit, Bundle, materials or closed reports. This record does not fully freeze the official form, start live execution, complete Stage 3 or enter Stage 4. Review remains advisory, without new approval authority or acceptance criteria.

The original archive is retained under `received/`; `verification.json` records the receipt checks. Archive SHA-256: `8c3f2dd55446d9a52bc5d5fe1df8e31d93f72e8ab4335058389ec7ca91ceb6b4`. Hashes identify bytes and support consistency checks.

`verify_received.py` uses only the standard library and does not execute submitted code. Its first draft stopped because it treated an initialization audit as a normal transition audit. That draft and its failure note remain under `receiver-notes/receipt-check-001.*`; the verifier was corrected to distinguish the two record shapes. This was a receiver-side verifier correction, not a failure of the user's run or replacement of inputs or expected results.
