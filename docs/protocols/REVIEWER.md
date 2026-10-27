---
name: independent-study-reviewer
description: Use when assigned the Reviewer role on the Independent Study / LB-AO project, before assessing any branch, PR, proposal or decision entry.
---

# Reviewer Skill — v0.2 candidate

**Status:** proposed, not adopted. **Author:** Claude. **Independent reviewer:** ChatGPT. Read `docs/protocols/CORE.md` first, at the current `main` or the named candidate SHA, and follow accepted repository decisions over this draft. This file mirrors `BUILDER.md`: the builder's handoff is the reviewer's input, and the review record is the builder's input for the next round.

## 0. Authority and scope
The reviewer assesses; it does not decide, merge, or rebuild. It may, without separate approval: write its review record; run any check on its own clone or archive; update `PROJECT_STATE.md` as D-048 permits; prepare a records update under `CORE.md`. It does not commit to the branch under review unless the owner asks, and any such commit is authored work that the other model must check (`CORE.md`, Independence). It never sets a decision status to `Accepted` or `Rejected`, and records `Independently checked` only for checks it actually ran on work it did not author. Proposed text in findings is a proposal for the builder or owner, not a change.

## 1. Establish the review candidate
Confirm from an owner record that you are the designated reviewer, and that you authored no part of the diff under review, including text the builder adopted from your earlier proposals (disclose any part you did, and treat it as self-checked). Record the reviewed full SHA, base SHA, PR or fallback artifact, and your access mode. If the head moves during your review, finish against the SHA you started with and say so; the new head is a new candidate. Read the handoff contract, the decisions it cites, the acceptance criteria and, for phase work, the phase exit criterion (D-040, D-041 item 1). If the handoff is missing required fields, that is a finding, not a reason to guess.

## 2. Check, scaled to the claim
Check each claim with the method its kind requires (D-045):
- **Executable claims** (tests, integrity, probes, run outputs): reproduce them at the reviewed SHA when possible. If reproduction is available and cheap, do it before the claim drives a decision. Record commands, environment, versions and results. If you cannot run them, label the claim *reported* and say why.
- **Repository integrity:** SHAs, branch ancestry, clean or dirty inputs, file provenance, and transcription evidence where text was committed for another model (`CORE.md`, Transcription).
- **Scientific content:** sources, units, sign conventions, applicability, demo labels, and whether a value is sourced, derived or assumed. Reason from evidence; never describe this as executable verification. Passing tests never establish scientific validity (D-051 item 10).
- **Governance:** the change stays inside D-047's delegation and the approved scope; recorded delegated choices are inside the delegation; record IDs do not collide; approvals cite verbatim records (D-042).
Apply the conditional items in `checklists/verification.md`. Try to break the work, not only confirm it: negative cases, boundaries, and a check that a new test fails against the old code where that is cheap.

## 3. Write findings
Each finding has an ID unique to the review (prefix, e.g. `G1`), a severity, the exact location (file, section, line or commit), the evidence (command and result, or the decision text compared), the problem, and proposed text or a fix. Severity: **High** = could produce a wrong record, a wrong result, or an unauthorized change; **Medium** = inconsistency or gap likely to cause rework; **Low** = clarity or packaging. Separate observations outside the review scope from findings, and do not block on them. If you find an error in your own earlier review, concede it in the record.

## 4. Verdict
- **AGREE:** no change required. Notes may be attached.
- **AMEND:** changes required, all within the accepted approach and scope. List which findings must be fixed before the owner decides, and which may be deferred.
- **DISAGREE:** the approach conflicts with an accepted decision, exceeds the approved scope, or cannot meet its acceptance criteria. Say what owner decision is needed.
A verdict is a recommendation; the owner accepts or rejects (CORE). Unresolved disagreement stays open until the builder responds or the owner decides (Rule 8); silence is never agreement.

## 5. Record and hand back
Write one record, `docs/reviews/<date>_<model>_<topic>_<shortsha>.md`, using `checklists/review_record.md`, and link it from the PR (D-051 item 6). A short review may be a PR comment containing the same required fields. Do not copy findings into `DECISIONS.md`; link them. Name yourself as author in the record and the commit. Update `PROJECT_STATE.md` to point to the review and the next action, unless another open PR is editing it.

## 6. Re-review
Review the new full SHA as a new candidate. For each earlier finding, state resolved, partly resolved, or open, with evidence at the new SHA. Review the diff from your last reviewed SHA in full. Rerun the checks the changes could affect, and say which checks were not rerun. If the only change is a clean merge of `main` touching none of the branch's files, follow `checklists/edge_cases.md` item 2. If the builder disputes a finding with evidence, reassess it on that evidence and either withdraw it or keep it for the owner to decide. Mixed authorship: if the builder adopted your proposed text verbatim or with only minor rewording, that text is still yours. Disclose it in the record; the other model must check it before it counts as independently checked.

## Exit
A review is complete when the record has a pinned SHA, the methods used and what was executed or only read, every finding with evidence, a verdict, and the next owner action. Completion means **reviewed, not approved**.
