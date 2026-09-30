# Stage 2: Fixed scenario for Demonstration 1

Unresolved causes A/B, response B, summary, restart, and use of retained distinctions

Scenario specification v0.1  |  2026-09-29 (JST)  |  iseyan

The governing document is Guarantee scope and success criteria v0.1. This sheet fixes the inputs, sequence, and records for its primary scenario (criterion 3). Criteria 1 (preserve), 2 (reject and log), and 4 (evidence control) remain in force. This is a pre-implementation specification, not a run report.

**Fixed decision wording: unchanged from criterion 3**

> a_B was selected; causes A/B remain unresolved.

## Fixed primary scenario

| Step | Fixed specification |
| --- | --- |
| 1  Initial state | Case ID: demo1-main. State version 0; K = {h_A, h_B}; no applied evidence. h_A and h_B denote fictional fault causes A/B. Add no evidence during this primary scenario. |
| 2  Response B; save | Use binary output B (response a_B) as the fixed input: a provisional choice required by the submission procedure. Check the candidate update; save K = {h_A, h_B}, the empty evidence basis, and the audit record. Associate state version 1 with response record action-001. |
| 3  Summary | Fix the summary to “Provisional response B was selected.” Store it as a summary of the selected response; do not admit it as evidence. Authoritative K and state version 1 remain unchanged. |
| 4  Stop; restart | After saving, terminate the first process normally. Give a separate process only the case ID and store location. It reads the saved summary, authoritative state version 1, and response record action-001. Do not carry over the earlier process memory. |
| 5  Decide; record | Derive the fixed decision above from K and the response record actually read. Trace which process read which version, candidates, and response, and how it used that distinction in its decision. |

A state version identifies a checked save. Step 2 advances 0 to 1 even though K is unchanged; storing the summary or reading state does not advance it.

## Values to link in the resumption record (expected, not observed)

| Item | Expected value / recording rule |
| --- | --- |
| Read source | case_id = demo1-main / state_version_read = 1 |
| Read contents | K_read = {h_A, h_B} / evidence_basis = [] |
| Response record | action_record_id = action-001 / selected_action = a_B |
| Decision linkage | Link the decision above to state version 1 and the response record used. Record the actual writer and resumed-process identifiers at execution time. |

## Applying the acceptance criterion

Criterion 3 is met when the trace shows that the resumed process read both candidates in version 1 and the response record, then used them to decide without reconstructing K from the summary. A surviving file or matching sentence alone does not pass. The evaluator checks the expected values; they are not inputs to the resumed process.

This fixes the primary scenario only. The guarantee, exclusions, and remaining acceptance criteria are inherited from the governing specification. Implementation and execution will be recorded separately.

Basis: Guarantee scope and success criteria v0.1 (2026-09-29), criterion 3, “Use after restart.”

[M-Anchor_Demo1_Scope_and_Success_Criteria_v0.1.en.md](M-Anchor_Demo1_Scope_and_Success_Criteria_v0.1.en.md)

SHA-256 of governing English MD: `b98463b08e10fc729e2d1b9bdeb42960826200b301836c0e56944185b7d31320`
