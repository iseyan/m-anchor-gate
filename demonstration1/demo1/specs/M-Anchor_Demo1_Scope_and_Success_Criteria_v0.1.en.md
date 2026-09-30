# Guarantee scope and success criteria

Demonstration 1: preserve candidate distinctions and use them after restart

Working specification v0.1  |  2026-09-29 (JST)  |  iseyan

**Status: acceptance specification, before implementation**

Formal Note v0.4 gives a conditional preservation result; Python v0.1 includes nine unit tests. Persistence, summarization, and use after restart in a separate process remain to be demonstrated. This document reports no demonstration results.

## 1  Scope and implementation assumptions

Fix Ω = {h_A, h_B} and the modeled world; exclude evidence retraction and candidate restoration. Freeze the evidence registry and interpretation rules in advance. Treat proposals as data. Authoritative writes use one checked path, one writer, and one store. Save state and audit records in the same transaction.

## 2  Conditional guarantee

K is the externally retained candidate set; D is the accepted, still-valid evidence applied to this transition; M(D) contains candidates permitted by its interpretation, with M(∅) = Ω. Under the assumptions and enforced checks:

$$
K_t\cap M(D_t)\subseteq K_{t+1}\subseteq K_t,\qquad D_t=\varnothing\implies K_{t+1}=K_t.
$$

Output a_B alone is not evidence for removal. Previously accepted, still-valid evidence may be reapplied with a documented basis, even without a new observation. MECC does not require immediate full incorporation.

## 3  Simulated workflow and acceptance criteria

Select provisional response B while causes A/B remain unresolved. Criterion 3 is the primary outcome; retain checks 1-2 and verify control 4.

**1  Preserve** Starting with K = {h_A, h_B}, emit a_B without evidence. Both candidates remain after summarization. Do not adopt output or summary text directly as independent evidence.

**2  Reject and log** Reject an unsupported update to {h_B} and an unregistered evidence ID; leave K unchanged. Record the proposal, rejection reason, referenced evidence IDs, rule version, and before/after states.

**3  Use after restart** Save output and summary, then terminate the process. A separate process reads authoritative K and concludes: “a_B was selected; causes A/B remain unresolved.” Trace the state version and candidates read, their use in the decision, and its result. Do not reconstruct K from the summary alone.

**4  Evidence control** Apply registered evidence e_B with the fixed rule M({e_B}) = {h_B}. Choose full incorporation and accept K = {h_B}. The same resumption procedure concludes “only B is retained under this evidence interpretation,” distinguishing it from the unresolved case.

A surviving file or generic uncertainty wording alone does not pass. Fixed proposals may be replayed; an LLM API and aggregate UECR/SCR metrics are not required.

## 4  Exclusions and required record

Excluded: model internals; evidence truth or candidate completeness; automatic language interpretation; authorization or real-world actions; concurrency or crash recovery; privileged bypass; general AI safety. An empty set denotes candidate exhaustion.

Deliver the code version/hash, environment, reproduction command, state/proposal/audit/resumption-decision logs, and each verdict. Version the demonstration separately from Bundle 1.0.

Basis: Formal Note v0.4 §§2-4, 6; Python v0.1 Implementation and Verification Report; [Research Roadmap, 2026-09-29 (bd9cf3c)](https://github.com/iseyan/m-anchor-framework/blob/bd9cf3c43bf8c14cd8a7721aa78250327cdd7cf8/plans/research-roadmap-2026-09-29.en.md)
