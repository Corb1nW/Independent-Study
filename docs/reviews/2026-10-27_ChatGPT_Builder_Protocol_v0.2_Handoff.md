# Handoff to Claude — Builder protocol v0.2 candidate

**Author:** ChatGPT. **Recipient:** Claude. **Owner assignment recorded in Claude's 2026-10-27 re-review:** ChatGPT drafts Builder v0.2; Claude reviews. **New owner direction:** Claude will implement the Builder protocol and author the Reviewer role skill; ChatGPT will independently review Claude's Reviewer skill. **Status:** proposal; no adoption claimed.

## Deliverables
Candidate files: `CORE.md`, `BUILDER.md`, `checklists/handoff_contract.md`, `checklists/verification.md`, `checklists/edge_cases.md`. Proposed repository destination: `docs/protocols/`. Claude should independently draft `REVIEWER.md` to complement `CORE.md`, not silently rewrite Builder rules. If integration reveals conflicts, raise them as explicit amendments.

## Required implementation workflow
1. Fetch current `main` and report **actual full SHA**, repository state, access capabilities and relevant decisions D-042 through D-053 (including D-041, D-045, D-047, D-048, D-051 and D-053). The author could not verify these against a pinned repository SHA while preparing this package. Do not present the package as verified against `main`.
2. Create a decision-by-decision and F1–F13/R1–R7 change map tied to that verified SHA; resolve any conflicts in favor of accepted decisions and flag proposed amendments.
3. Add these as proposed versioned files on a branch. Draft full `REVIEWER.md` with explicit reviewer scope, independent checks, finding severity, ACCEPT/AMEND/REJECT, proportionate re-review and mixed authorship handling.
4. Confirm skill loading/entrypoint conventions for each platform without claiming identical native behavior. Include appropriate Claude frontmatter and ChatGPT project-instruction entrypoint text.
5. Record authoring model in commits/PR, checks actually performed, full candidate SHA, and authoritative PR handoff. Request ChatGPT independent review of **Claude-authored Reviewer material and any Claude edits to shared core**; Claude must not independently approve its own additions. ChatGPT-authored Builder text should be independently checked by Claude. Mixed-authorship review records must map reviewer to changed portions.
6. Do not merge, activate, or mark decisions Accepted until owner explicitly approves the final reviewed SHA and the required adoption decision entry is recorded.

## Review reconciliation
- F1–F13 from Claude's first review accepted with the three ChatGPT refinements; R1–R7 accepted in full.
- R1: light path uses declaration plus escalation, with normative file exclusions.
- R2: `main` merge gets impact assessment and proportionate delta review.
- R3: blockers never expand delegated authority.
- R4: independence is per authored diff, including same-model sessions and unknown/mixed authorship.
- R5: Reviewer authority explicitly bounded.
- R6: v0.1 authorship ChatGPT, v0.2 drafter ChatGPT; owner assignment recorded in Claude re-review.
- R7: verified SHA in change map; reviewer role drafted before joint adoption; protocol edits full path; offset timestamps; BLOCKED draft PR; define review candidate.

## Requested response from Claude
Return exact SHA, PR link if created, list of files and changes, decision verification and change map, test/document checks, unresolved questions, and the Reviewer skill draft for ChatGPT's independent review. State clearly that this is a review candidate, not adopted.
