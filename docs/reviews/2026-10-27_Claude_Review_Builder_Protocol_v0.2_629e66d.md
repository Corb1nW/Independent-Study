# Claude Review of ChatGPT's Builder Protocol v0.2 Candidate

**Reviewer:** Claude. **Author of the reviewed text:** ChatGPT (owner records: Q-entries proposed in the integration record, items P-1 and P-2).
**Reviewed SHA:** `629e66d6e42340ea0ed46879b994f114a774ea93` (ChatGPT's files committed verbatim by Claude; SHA-256 of each file in that commit's message, matching the candidate zip)
**Base SHA:** `6c8b6ef96b2a8f41667fb7e80ae002d068b0fbfb` (`main`, merge of PR #14)
**Scope:** `docs/protocols/CORE.md`, `BUILDER.md`, `checklists/handoff_contract.md`, `checklists/verification.md`, `checklists/edge_cases.md`, checked against accepted decisions D-041 to D-053 in `docs/DECISIONS.md` (revision 10) at the base SHA, and against the agreed F1 to F13 and R1 to R7 dispositions.
**Independence:** Claude committed ChatGPT's text unchanged, which does not make Claude its author (see G5). Claude authored F1 to F13 and R1 to R7, the requirements this text implements; proposing a requirement does not disqualify a reviewer. **Disclosure:** some passages adopt Claude's own proposed wording with only minor rewording, so for those passages this review is **not independent**: CORE "Light path" (from R1's proposed text), CORE "Provenance, authorship, independence" (R4), BUILDER §3 last sentence and edge_cases 3 (R3), edge_cases 2 (R2). Under `REVIEWER.md` §6, ChatGPT's review of the integrated protocol should cover them. All other passages are ChatGPT's own wording and were reviewed independently.
**Method:** non-executable review (D-045). Each rule was compared line by line with the decision text it cites or restates. Supporting execution: at the base SHA, `python -m pytest -q` gave 104 passed, `python -m src.integrity` PASSED, and `python tools/review_cycle1_probes.py` gave 9/9 REJECTED (Python 3.13.18, pydantic 2.13.5, pint 0.26.2, PyYAML 6.0.3, pytest 9.1.1). This only shows that the protocol files sit on a healthy base. It says nothing about the protocol itself.

**Verdict: AMEND (minor).** The text implements F1 to F13 and R1 to R7 faithfully. I found no rule that contradicts an accepted decision. G1 to G10 below are omissions, wording that is narrower or wider than the decision it cites, and two gaps exposed by this integration itself (G3 and G6). Claude's proposed fixes are in later commits on this branch. They are separate from ChatGPT's text so that ChatGPT can review them independently.

Severity: **High** = could produce a wrong record or an unauthorized change. **Medium** = inconsistency or gap likely to cause friction or rework. **Low** = clarity or packaging.

---

## Findings

### G1 (Medium). The status vocabulary says "exactly" but omits values the log defines

**Text (CORE, Records and statuses):** "Use D-043's three separate status fields exactly", followed by four decision values, three implementation values and four verification values.
**Log (§3 Status values, base SHA):** decision status also allows `Superseded by D-xxx` and `Accepted (baseline)`. Implementation and verification statuses both allow `Not applicable`, which D-051, D-053 and D-039 to D-041 use. The log also qualifies values in practice: `Accepted (Q18)`, `Independently checked (software)`.
**Problem:** "exactly" plus an incomplete list would make valid existing entries look non-conforming. It also restates the source it should cite (F10).
**Fix:** cite §3 as the authoritative list, and allow a qualifier only in parentheses (approval ID, scope such as "software"), never as a new value.

### G2 (Medium). D-047 requires delegated choices to be recorded; the Builder text does not say so

**D-047:** the building model may decide the listed items without separate approval, "recording each choice and its basis in the commit message or `PROJECT_STATE.md`". D-050 is the worked example.
**Text:** BUILDER §2 and §3 cover reserved changes, but nowhere requires delegated choices to be recorded. A reviewer then cannot check that a choice stayed inside the delegation.
**Also:** CORE says the D-047 categories are "reserved where specified". D-047 reserves them always ("remains a proposal for Corbin"). "where specified" reads as a weakening.
**Fix:** add the recording duty to BUILDER §3 and the handoff contract. In CORE, replace "are reserved where specified" with "are reserved for the owner".

### G3 (Medium). The snapshot-mismatch rule is too literal and too broad

**Text (BUILDER §1; edge_cases 1):** "If `PROJECT_STATE.md` names a different snapshot than `main`, stop and report the conflict."
**Observed at the base SHA:** `PROJECT_STATE.md` defines its snapshot as "the commit that last changed this file", so it never literally names a different snapshot. What actually happens is that its content goes stale. At `6c8b6ef` it still says the Phase B build is "awaiting Claude's independent review and Corbin's merge", but PRs #13 and #14 were merged at 18:17 on 2026-10-27. Open PR #15 (Claude, other session) corrects it.
**Problem:** read literally, the rule never fires. Read broadly, it would have stopped this protocol task over a stale Phase B entry that does not affect the task.
**Fix:** "If `PROJECT_STATE.md` is inconsistent with `main` (stale phase, task, roles or snapshot), record both in the handoff. Stop only if the inconsistency affects this task's scope, inputs or role assignment. Do not correct it unless that is part of the assigned task."

### G4 (Medium). Verdict words ACCEPT and REJECT collide with owner decision statuses

**Text (handoff_contract):** "Requested action: ACCEPT / AMEND / REJECT at exact SHA".
**Log:** `Accepted` and `Rejected` are decision statuses that only Corbin can confer (Rule 7, D-047). Reviews in the repository have used **AGREE / AMEND / DISAGREE**: Claude's D-053 and Phase B reviews, ChatGPT's D-052 re-review, and the `PROJECT_STATE.md` next-task text ("Respond AGREE/AMEND/DISAGREE").
**Problem:** "the reviewer ACCEPTED it" invites exactly the confusion F3 removed, where agreement gets read as acceptance. The design-review exchange (including Corbin's request for this review) used ACCEPT/AMEND/REJECT, so this is a vocabulary choice the owner should confirm.
**Fix (proposed; owner question Q-A in the integration record):** reviewer verdicts are AGREE / AMEND / DISAGREE; the words Accept and Reject are reserved for owner decisions.

### G5 (Medium). Independence does not cover one model committing another model's text

**Text (CORE, Provenance):** independence holds only if "the checking model authored none of the commits, data values, or text being checked".
**Problem:** in this PR, Claude committed ChatGPT's files (commit `629e66d`) and then reviewed them. "authored none of the commits" could be read as disqualifying Claude, even though the text is ChatGPT's. Conversely, a model could pass off edited text as a "transcription". The same happens whenever one model lacks push access and another commits for it (a D-051 item 12 fallback).
**Fix:** "Committing another model's text unchanged is transcription, not authorship, if the commit names the text's author and records evidence that the content is unchanged (for example SHA-256 of each source file). Any change during transcription, including formatting, makes the committer an author of that change, and it must be in a separate commit."

### G6 (Low). Parallel PRs that edit the shared records

**Observed:** open PR #15 edits `docs/DECISIONS.md` (revision 11, adding Q19 and A-5) and `PROJECT_STATE.md`. Under F7 as written, the next free approval ID on the base is Q19, which PR #15 already uses. F7 and BUILDER §5 cover only `D-xxx` IDs. Two concurrent edits to `PROJECT_STATE.md` also conflict on merge.
**Fix:** extend the ID rule to approval (`Q-n`), action (`A-n`) and correction (`C-n`) IDs, and check open PRs as well as `main`. While another open PR edits `DECISIONS.md` or `PROJECT_STATE.md`, put proposed record changes in the PR and apply them after that PR merges. This PR does so (integration record, "Proposed records").

### G7 (Low). A decision entry for every protocol change is heavier than needed

**Text (CORE, Role permissions):** "All protocol amendments take the full review path and a decision entry". This came from my R7.3.
**Concession:** a new `D-xxx` for every protocol wording fix is disproportionate and fills the index. D-044's mechanism fits better: a dated, labeled amendment appended to the adoption decision.
**Fix:** "Protocol changes take the full review path and owner approval at a pinned SHA, and are recorded as amendments to the protocol's adoption decision. A change that alters a governing rule substantially may instead get its own decision."

### G8 (Low). Entry points are not stated precisely

**Text:** BUILDER says "Read `CORE.md` first" with no location. CORE has no read order for checklists. There is no ChatGPT entry text (F12) and no index.
**Problem:** if `BUILDER.md` is loaded as a standalone skill (for example a claude.ai skill), the relative name does not resolve.
**Fix:** use repository paths (`docs/protocols/CORE.md`), always read at the current `main` or the named candidate SHA. Add `docs/protocols/README.md` with the read order and the platform entry texts, clearly marked as not installed until adoption.

### G9 (Low). D-051's "when unsure, use the standard path" is missing from the light path

**D-051 item 3:** "When unsure which path applies, use the standard path." CORE provides escalation by a doubting reviewer or owner, but not this default for the builder.
**Fix:** add the sentence to CORE's light-path paragraph.

### G10 (Low). No rule for who records owner approvals in the log

**Problem:** §2 of the log names Claude as "maintainer of this log", but both models have edited it (revisions 8 and 9 were ChatGPT's). Recording approvals and status updates (records PRs: #4, #6, #8, #12, #15) is neither a build nor a review, so the protocol does not say who does it, which path it takes, or who checks it.
**Fix (proposed):** "Any model may prepare a records update (approval quotes, status fields and index rows per D-044) on a `records/<model>-<topic>` branch. It takes the standard path, except that the owner's merge is sufficient confirmation of his own quoted words. The other model checks the rest of the records change at its next review."

---

## Confirmed as consistent (no change)

- D-047 scope list and "when unsure, proposal" (CORE, except G2's wording); approval limited to what it names and its SHA (D-051 item 8, D-053's representation-only approval).
- Verbatim approval capture with offset timestamps (D-042, F2, R7.4); append-only reasoning and labeled corrections (D-044).
- Independence per authored diff, same-model sessions, unknown authorship, reviewer commits (R4); review candidate definition (R7.6); PR as the authoritative handoff (D-051 item 4, F6).
- Light path boundary and exclusions (R1; D-051 item 3), apart from G9.
- Moving `main`, blockers, unanswered escalations as a BLOCKED draft PR, tool capability proofs (R2, R3, F8, R7.5; D-051 items 7 and 12).
- Verification layers kept separate; tests never establish scientific validity (D-051 item 10, D-045).
- Verification checklist items match the Phase B lessons: committed-input checks, Git-normalized hashing on Windows, raw-byte hashes kept for resolution-to-execution (D-053 B2; Phase B build reviews; carried note N4).

## Requested actions

1. **ChatGPT:** independently review Claude's amendment commits for G1 to G10 and respond AGREE / AMEND / DISAGREE per finding.
2. **Corbin:** answer Q-A (verdict vocabulary, G4) and Q-B (G10 records rule) in the integration record.
