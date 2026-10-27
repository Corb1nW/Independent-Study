# Cross-model edge cases — v0.2 candidate

*Author: ChatGPT; items 1 and 7 amended and item 10 added by Claude [G3, G6].*

1. **Snapshot mismatch:** if `PROJECT_STATE.md` is inconsistent with `main`, record both references in the handoff. Stop and ask for reconciliation only if the inconsistency affects the task's scope, inputs or roles [G3].
2. **`main` advances:** inspect changes first. Merge `main` into the branch; do not rebase after reviewer pins a SHA. New SHA = new candidate. For a clean merge with no touched branch files, limited re-review may rerun established checks and confirm only `main` additions; otherwise review merge/conflict resolution fully. Owner approval names final SHA.
3. **Out-of-scope defect:** repair only if delegated or within accepted scope, with evidence; otherwise propose and stop at affected boundary. Being blocked is not authorization.
4. **Unanswered escalation:** stop at decision boundary; where possible push a draft PR marked BLOCKED, with question first and work completed identified. Otherwise report precise fallback.
5. **Unproven tool access:** demonstrate test/PR/push capabilities before claiming them. Record fallback and offline dependency constraints.
6. **Role swap:** use owner assignment record, not conversational habit. Same model in another session is not independent.
7. **Record-ID collision:** for `D`, `Q`, `A` and `C` IDs, allocate the next ID free on `main` and in open PRs, recheck before merge, renumber pre-merge only [G6].
8. **Reviewer writes code:** reviewer-authored commits must be independently checked by the other model; review record maps checks to commits.
9. **Normative document typo:** do not use light path for decision bodies, protocol/checklists, schemas or data; use full path and accepted correction rules.
10. **Parallel records PRs:** if another open PR edits `docs/DECISIONS.md` or `PROJECT_STATE.md`, do not edit them concurrently; put proposed record changes in your PR and apply them after that PR merges [G6].
