# Independent Study — Shared Protocol Core (v0.2 candidate)

**Status:** proposed, not adopted. **Author:** ChatGPT. **Reviewer:** Claude. **Authority:** project owner and accepted repository decisions. This file must be reconciled against `docs/DECISIONS.md` at a recorded full `main` SHA before adoption. If it conflicts with an accepted decision, follow that decision and report the conflict as a proposed protocol amendment.

## Applicability and authority
Read this core before any Builder or Reviewer work, then read the assigned role file. Confirm assignment from an owner record, not session habit. The owner retains final decision and merge authority. D-047 governs delegation: scope, scientific content (anatomy, sources, parameter values, modeling assumptions), architecture, identifiers in use, and accepted requirements are reserved where specified. When unsure, submit a proposal rather than silently deciding. An approval covers only what it names and the pinned snapshot it names (D-051).

## Records and statuses
Use D-043's three separate status fields exactly:
- Decision: `Proposed`, `Accepted`, `Rejected`, `Superseded`.
- Implementation: `Not started`, `In progress`, `Implemented`.
- Verification: `Not checked`, `Reported by author`, `Independently checked`, `Failed`.

Software verification never implies scientific validation. Do not invent facts, anatomical values, citations, commands, test outcomes, access, or Git SHAs. Clearly label demonstration parameters and prevent them being mistaken for clinical evidence.

If the owner decides or approves something in a session, preserve the statement **verbatim** with the question answered and timestamp in `America/New_York` including offset (example: `2026-10-27 18:34 -04:00`) as a proposed §4 approval-record entry. Do not paraphrase the quote. When ambiguous, state an interpretation and request clarification. Follow existing decision-log correction and append-only rules (D-042/D-044).

## Provenance, authorship, independence
Name the authoring model in each commit message body, PR description, and review record; GitHub account attribution alone is insufficient. A review is independent for a given change only when the checking model authored none of the commits, data values, or text being checked. Merely proposing a requirement does not disqualify a reviewer. A new session of the same model is **not** independent. Unknown authorship cannot be counted as independently checked until resolved. A reviewer normally does not modify the reviewed branch; owner-requested reviewer commits must be checked by the other model. For mixed authorship, record which commits and changes each model independently checked, and disclose any self-authored portion. Never label self-checks independent.

## Review candidate and authoritative handoff
A **review candidate** is an exact full commit SHA submitted with its handoff contract. The PR description is the authoritative handoff copy. `PROJECT_STATE.md` points to the PR and next task instead of duplicating the handoff. If a PR is unavailable, name the authoritative fallback artifact and its exact location. A new SHA is a new candidate; owner acceptance must name the final SHA. Reviewer findings and outcomes remain in the review record.

## Light path
A change qualifies only if limited to documentation formatting or wording within D-047's delegation and the Builder declares in the PR: **“No change to scientific meaning, normative requirements, interfaces, identifiers or acceptance criteria.”** Never use the light path for bodies of `DECISIONS.md` entries (use labeled corrections under D-044), protocol files or checklists, schemas, or data files. If owner or reviewer doubts the declaration, escalate to full path without needing justification. Light path: branch, commit, short scope/SHA/files handoff, owner merge; omit full planning and scientific verification. The owner retains merge authority.

## Role permissions and changes to protocol
Builder changes are bounded by D-047 and approved scope. Reviewer may author review records and update `PROJECT_STATE.md` where D-048 permits, without separate approval; other edits are proposals unless explicitly authorized. All protocol amendments take the full review path and a decision entry; no role may activate or modify governing rules unilaterally. Review and adoption must reference a verified full repository SHA.
