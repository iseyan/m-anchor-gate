# Stage 4: Draft productization plan

v0.1 (review revision) | 2026-09-30 JST | Draft plan / entry form not frozen

## 1. Position

This plan corresponds to Stage 4, consideration of productization, in the research roadmap dated 2026-09-29. It covers a common API, connectors, version management, audit and maintenance procedures, and identification of the intended use and paying user. It connects Stage 3 evaluation results to a product scope and terms of provision that can be maintained.

The public status is "Draft plan / entry form not frozen." This document describes the roadmap's Stage 4 in advance; it does not substitute for Stage 3 preparation or partner-workflow evaluation. Stage 4 entry conditions remain unconfirmed, and implementation and execution have not started.

The reviewed English development report v0.1 is closed as a final document. Demonstration 1, the Stage 3 specification and original records, including schema-gate-001, remain references. This draft is not integrated into the mainline, Gradio or the Bundle.

## 2. Records received from the preceding stage

The table describes the documents referenced for this draft. These references do not include records supporting a decision that Stage 3 as a whole is complete. Stage 4 entry conditions also remain unconfirmed. Results from other experiments or demos are not automatically treated as Stage 3 completion records; any new evidence is assessed in a separate entry record.

| Reference record | Treatment in this plan |
| --- | --- |
| Stage 3 specification v0.1.1 | Governs the distinction between preparation evaluation and partner-workflow evaluation; its text is unchanged |
| Development report v0.1 | Final record of fixed-input development checks; not a live-model evaluation or completion of Stage 3 |
| Partially prepared run form v0.1 | At the time of reference, execution_ready=false; official settings are not frozen and external schema validation is incomplete |
| Full Stage 3 completion record | Not included in this draft's references; comparison with the existing method in an actual selected workflow is to be assessed in a separate entry record |

Under the existing specification, full Stage 3 completion is assessed from records of improvement or no difference, false rejection of valid updates, latency, integration effort and remaining bypass paths in the selected workflow. Passing preparation evaluation or closing a report review does not substitute for those records. Unfavorable results are retained and used in the productization decision.

## 3. Inherited preservation contract

The model returns structured proposals; an external checking and persistence path controls authoritative state updates. Candidate sets, selected responses, admitted evidence and summaries remain distinct. Neither response selection nor a summary becomes independent evidence authorizing candidate removal.

Connectors check the case, referenced version, state hash, case-specific evidence admission and fixed interpretation rules. Validated updates, actions and audits are committed together. Rejection, summary handling and reads alone do not advance the state version. Processing after restart must leave a trace of reading authoritative state and using its distinctions in the next decision.

Partial evidence incorporation that satisfies preservation is assessed separately from a task requirement for full incorporation. An empty candidate set is not ordinary unresolved status. Changes to the candidate universe, evidence withdrawal and candidate restoration require specification outside ordinary candidate updates.

An API does not extend the guarantee to the truth of real-world evidence, internal model understanding, authority management in general, prompt-injection resistance or prevention of real-world accidents. Any scope extension requires separately specified conditions and evaluation in another version.

## 4. Candidate deliverables after entry confirmation

These are candidate deliverables to be created and assessed in Stage 4 after entry conditions are confirmed. They do not describe implemented features or an established guarantee scope. Concrete API names, formats and product form will be determined from Stage 3 results and the selected workflow.

| Deliverable | Content to specify or implement | Supporting records |
| --- | --- | --- |
| Use scope and terms of provision | Workflow, user, paying party, inputs and outputs, persisted information, guarantees and exclusions | Stage 3 workflow comparison and scope and terms confirmed by the intended user |
| Common API contract | State reads, proposal submission, outcome and audit access; separation of model proposals from host-managed versions and evidence admissibility | Input/output definitions, schema-validation records and mapping to the selected implementation version |
| Connectors | Connect the selected model and workflow system to validated persistence and authoritative reads after restart | Linkage among actual inputs, raw responses, state reads and commits; inventory of controlled write paths |
| Version and migration procedures | Map API, schema, connector, evidence-admission and interpretation-rule versions to stored-state versions | Compatibility decisions, reasons and impact of changes, required migrations and verification records |
| Audit procedures | Trace accepted and rejected proposals, communication failures and retries; inspect before/after states and applied evidence | Audit fields, access methods, retention and access scope |
| Maintenance procedures | Define stopping on violations, failure retention, repair, revalidation and operational handover | Links between failed and repaired versions, checks required by the change, responsible roles and contact routes |

Model replaceability does not establish portability to another workflow without adaptation. Identify the common and workflow-specific parts, and do not add untested integrations merely to present a broader supported scope.

## 5. Work sequence

The immediate work is to prepare the new external schema-gate record and the official Stage 3 run form in separate files. If corresponding records already exist, confirm their references and versions. Map these records, live-model integration and restart-use records, and comparison in the selected workflow into a separate Stage 4 entry record.

Because entry confirmation remains unfinished, this draft designates no version for progression into product implementation. An unresolved failure covered by a Stage 3 stop condition prevents progression of that version into product implementation. This inherits existing conditions; it does not add a new model test.

After entry conditions are confirmed, identify a candidate workflow and use scope, then define the common API contract and connector scope. Develop the version, audit and maintenance procedures for that implementation. Reuse existing checks and limit additional verification to changed integration or migration behavior and the requirements of the adopting environment. If concurrency or crash recovery is required, evaluate it separately when introduced.

Price, product form, willingness to pay and maintenance arrangements remain undecided. Technical feasibility does not establish demand or willingness to pay. Preparing this plan does not establish that partner discussions, spending, publication or service provision have occurred.

## 6. Completion decision

The roadmap's completion condition is an identified paying user and use scope whose guarantees can be maintained over time. The decision record identifies the target, supporting evidence, provision scope, responsible roles and unresolved issues.

Proceeding with productization, continuing consideration within a narrower scope, and declining to proceed are all retained outcomes. Closing consideration does not by itself establish readiness to provide a product. A decision to proceed must identify its supporting basis for the version and guarantee scope to be offered.

## 7. Present outputs and subsequent records

The present outputs are the Japanese and English draft plans and stage4-productization-entry-form.v0.1.json. The entry form remains unfilled and unfrozen, with execution_ready=false. It assesses entry into Stage 4 and does not replace the official Stage 3 run form. The existence of a plan or closure of its document review does not satisfy entry conditions.

Keep subsequent records in separate files, rather than appending them to this draft or the closed English development report. Do not rewrite schema-gate-001 as a pass. When a Stage 4 entry decision is made, create a separate finalized entry record linked to the supporting records.

References: research-roadmap-2026-09-29.ja.pdf (stage table and completion conditions); stage3-integration-evaluation-v0.1.1.ja.md; development-report.v0.1.en.md (after shortening Status and remaining work); stage3-prepared-run-form.v0.1.json. Referenced on 2026-09-30 JST.
