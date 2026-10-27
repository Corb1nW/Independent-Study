# Claude Review of the Builder Skill Draft v0.1

**Reviewer:** Claude
**Date:** 2026-10-27
**Document reviewed:** `BUILDER_SKILL_DRAFT_v0.1.md` (proposed; author not stated in the file; passed to Claude by Corbin)
**Suggested repository path:** `docs/reviews/2026-10-27_Claude_Review_Builder_Skill_v0.1.md`
**Review type:** Non-executable (D-045). No code or tests are involved. Alignment with D-042 to D-050 was checked against `docs/DECISIONS.md` revision 3. Alignment with D-051, D-052 and D-053 was checked against Claude's records of the 2026-10-20/21 sessions, **not** against the repository at a pinned SHA. Those comparisons are *reported*, and should be rechecked against `main` before the skill is adopted.

**Verdict: AMEND.** The draft is sound in substance. It already encodes the hardest lessons from Phase A and Phase B (no fabricated results, pinned SHAs, dirty-input detection, line-ending normalization, verification ≠ validation). The amendments below fix vocabulary drift from the decision log, two gaps in how the skill connects to D-047 and D-051, missing edge cases that come from the models swapping roles, and a structure that will be hard for either model to follow consistently.

---

## Findings

Severity: **High** = could produce a wrong record or an unauthorized change. **Medium** = inconsistency or gap likely to cause friction or rework. **Low** = clarity or packaging.

### F1 (High). Escalation triggers do not match D-047's delegation list

**Draft:** Rule 5 escalates changes to "scientific assumptions, interfaces, evidence rules, or agreed architecture".
**D-047 (accepted, Q6):** reserves for Corbin anything affecting *scope, scientific content (anatomy, sources, parameter values, modeling assumptions), architecture, identifiers in use, or an accepted requirement*, and says "when unsure, treat it as a proposal".
**Problem:** The draft omits *identifiers in use*, *parameter values* and *sources*, and does not carry the "when unsure" default. Two lists that nearly match will drift. D-053 shows why this matters: approval of the moment-arm *representation* explicitly did not cover its numerical values, which needed a separate reviewed PR.
**Proposed edit (Rule 5):**
> Make changes only within the delegated scope defined by D-047. Anything D-047 reserves for the owner (scope, scientific content including anatomy, sources, parameter values and modeling assumptions, architecture, identifiers in use, or an accepted requirement) is a proposal. When unsure, treat it as a proposal. An approval covers only what it names, at the SHA it names (D-051).

### F2 (High). Owner approvals received in one model's session are invisible to the other

**Problem:** Roles now swap. Corbin's approvals arrive in whichever model's chat he happens to be using, and the other model cannot see that chat. The log handles this with verbatim quotes in §4 (D-042), but the skill never tells a builder what to do when Corbin approves something mid-build.
**Proposed addition (new step under §2 Plan):**
> If the owner approves or decides something during your session, record it verbatim with date, time (America/New_York) and the question it answered, as a proposed §4 Approval record entry. Never paraphrase an approval into the record. If an instruction is ambiguous, state your interpretation and invite correction, as with Q8.

### F3 (Medium). Status vocabulary differs from the decision log

**Draft:** Rule 3 uses *proposed, approved, implemented, verified, scientifically validated*.
**Log (D-043):** three separate fields. Decision: `Proposed · Accepted · Rejected · Superseded`. Implementation: `Not started · In progress · Implemented`. Verification: `Not checked · Reported by author · Independently checked · Failed`.
**Problem:** "Approved" vs "Accepted" and a single "verified" level will produce records that don't match the index. A builder's own test runs are specifically `Reported by author`; only the reviewer can produce `Independently checked`.
**Proposed edit (Rule 3):**
> Use the three status fields and values of D-043 exactly. A builder's own verification is recorded as `Reported by author`. Scientific validation is a separate claim that no status field implies; passing tests never establish it (D-051).

### F4 (Medium). No proportionate path for trivial changes

**Problem:** D-051 (ChatGPT's amendment A, narrowed by Claude) gives wording and formatting fixes a lighter path, bounded by D-047's "formatting and wording of documentation". The draft applies the full procedure to everything, including a typo fix. That is the rigidity ChatGPT's own D-051 review warned against.
**Proposed addition (after Purpose):**
> **Light path.** Changes limited to formatting and wording of documentation (D-047) skip planning and scientific verification: branch, commit, short handoff (scope, SHAs, files), owner merge. Code, data, schemas and the substance of `DECISIONS.md` entries never use the light path.

### F5 (Medium). Author identity is not required in the text

**Problem:** D-051 Amendment 3 records that both models act through Corbin's GitHub account, so GitHub's authorship labels do not identify the model. The handoff contract has "Builder / designated Reviewer", but nothing requires the commit message or PR description to name the authoring model.
**Proposed edit (Rule 6 and handoff contract):** add "Name the authoring model in every commit message body, PR description and review record; GitHub attribution does not identify it." Add a contract line: `Authored by (model):`.

### F6 (Medium). Duplicate handoff locations

**Problem:** D-051 places the handoff in the PR description, and D-051 item 6 (amendment B) requires one authoritative record. The draft asks for the contract, a `PROJECT_STATE.md` update, and decision entries, without saying which is authoritative.
**Proposed edit (§5):**
> The handoff contract goes in the PR description; that is the authoritative copy. `PROJECT_STATE.md` is updated to point to it and to the next task, not to repeat it. If no PR is possible, the contract goes in the fallback artifact named in the contract.

### F7 (Medium). Decision ID collisions between parallel branches

**Problem:** Rule 9 of the log allocates `D-xxx` IDs only in the log. With two models able to build on separate branches, both may claim the same next number.
**Proposed addition (§5):**
> Proposed entries take the next free ID on the base branch at the time of writing, and the builder rechecks it against `main` before requesting merge. If it collides, renumber before merge, never after.

### F8 (Medium). Missing edge cases from role swapping

Each of these has already happened or nearly happened. Proposed one-line rules for the reference checklist (see F11):

1. **Snapshot mismatch at start.** If `PROJECT_STATE.md` names a different snapshot than `main`, stop and report; do not choose one.
2. **`main` moves during a build.** Merge `main` into the working branch; do not rebase once a reviewer has pinned a SHA, because rebasing changes the SHA they reviewed.
3. **Out-of-scope defect found while building** (precedent: D9 in Phase A). If it blocks the scoped work, fix it and record it as an amendment with evidence; otherwise file it as a proposal and leave it.
4. **Escalation unanswered.** Do not proceed past the point that needs the decision. Commit and push what is done as a draft PR labeled as blocked, with the open question first.
5. **Tool capability unproven.** Before relying on push, PR or test execution, demonstrate it (D-051 amendment E). If the sandbox cannot install dependencies, use the offline bundle and say so.
6. **Role assignment.** Confirm who builds and who reviews from an owner record (e.g. the Q-entry that swapped Phase B roles), not from the previous session's habit.

### F9 (Low). Scenario-overlay and Windows hashing rules are project specifics in a general procedure

The overlay rule (§3) and the `git hash-object` comparison (§4) are correct and came from real defects (D-053 N3; the Phase B line-ending bug). But they apply only to some tasks and will be skipped or misapplied when read inline. Move them to the verification checklist (F11), keyed to "when the task touches simulation inputs" and "when execution on Windows is possible".

### F10 (Low). Restated governance will drift from the log

Several rules restate `DECISIONS.md` (D-042 to D-048, D-051). Restated text eventually diverges from its source. Prefer short rules that cite the decision ID, and keep the existing sentence that the skill never overrides an accepted decision. Add: "If this skill and an accepted decision disagree, follow the decision and report the conflict as a proposed amendment to this skill."

### F11 (Low). Recommended structure: shared core, two role files, checklists

The user's goal is consistency as roles swap, so the builder and reviewer skills should share one source for the rules both must follow. Proposed layout in the repository:

```
docs/protocols/
  CORE.md                  rules for every role: authority, D-047 scope, status vocabulary,
                           approvals, author identity, no fabrication, pinned SHAs
  BUILDER.md               ~1 page: when it applies, the 5 steps, exit criteria
  REVIEWER.md              ~1 page, written next, same shape
  checklists/
    handoff_contract.md    the template (filled in the PR description)
    verification.md        repo integrity, software checks, scientific evidence,
                           Windows hashing, overlays, offline bundle
    edge_cases.md          F8 items
```

The role files say "read `CORE.md` first". Putting the files in the repository, versioned under D-051, means both models read the same text at a known SHA, and changes go through review like anything else.

### F12 (Low). Portability of the frontmatter

The `name`/`description` frontmatter is the Claude skill format; ChatGPT ignores it, which is harmless. Two notes: Claude's skill format keeps only `name` and `description`, so `version` and `status` should move into the body; and the `description` decides when Claude loads the skill, so it should name the trigger plainly, e.g. "Use when assigned the Builder role on the Independent Study / LB-AO project, before modifying any file." For ChatGPT, the practical equivalent is a line in its project instructions: "At the start of any Independent Study task, read `docs/protocols/CORE.md` and the file for your assigned role at the current `main`."

### F13 (Low). Adoption record

The draft should be adopted through a decision entry (next free D-number), approved by Corbin at a pinned SHA, like D-051. Remove the "Review requested from Claude" section from the adopted version; it belongs in this review's history, not in the skill.

---

## What should stay as written

- Rule 4 (never fabricate values, sources, results, commands, tool access or hashes) and the demo-data labeling requirement.
- Rule 7 (builder never approves its own work).
- §4's three verification layers, and "never represent a previous model's results as newly reproduced".
- The handoff contract's "Checks not run and why" and the closing line "ready for review, not approved".

## Requested next actions

1. **Draft author:** respond to F1 to F13 as Agree / Amend / Disagree.
2. **Then:** one model produces v0.2 in the F11 layout, with the reviewer skill drafted alongside so `CORE.md` is settled once.
3. **Corbin:** approve the final version at a pinned SHA as a decision entry (F13).
4. **Recheck:** the D-051 and D-053 comparisons above against `main` at that SHA.
