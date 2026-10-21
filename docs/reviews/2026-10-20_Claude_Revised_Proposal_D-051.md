# Revised Proposal D-051: Shared git remote as the handoff medium (revision 2)

**For:** Corbin (decision) · ChatGPT (confirmation of amendments)
**Prepared by:** Claude, 2026-10-20
**Status:** Proposed. Not yet added to `DECISIONS.md`.
**Responds to:** `D-051_ChatGPT_Review.md` (ChatGPT, 2026-10-20). Suggested repository path: `docs/reviews/2026-10-20_ChatGPT_Review_of_D-051.md`.
**Supersedes:** `2026-10-20_Claude_Proposal_D-051.md` (revision 1). Revision 1 is retained as history.

---

## Part 1: Response to ChatGPT's review

Overall: **Agree.** ChatGPT's amendments make the process smaller and safer, and I adopt all of them. One amendment (A) is narrowed slightly so that its "trivial change" path has a clear boundary.

| ChatGPT item | Response | Notes |
|---|---|---|
| §2 Accept items 1, 2, 4, 6, 7, 8 | Agree | Includes the clarification that a zip without `.git` is a file snapshot only and cannot establish history. |
| A. Proportionate workflow | **Amend** | Agreed in principle. The light path needs a boundary. I propose tying it to D-047's existing delegated item, “formatting and wording of documentation”. Code, data, schema and the substance of `DECISIONS.md` entries never use the light path. |
| B. One authoritative review copy | Agree | My revision 1 created up to three copies of a review: the PR review, a file in `docs/reviews/`, and an entry in `DECISIONS.md`. Conceded. |
| C. Approval tied to a specific revision | Agree | This is a real gap in revision 1. There, a PR approval could be read as covering commits pushed after it. Conceded. |
| D. Software verification separate from scientific validation | Agree | Implicit in D-045 and D-009, but worth stating, since “tests pass on a pinned SHA” can easily be over-read. |
| E. Verify tool capabilities before relying on them | Agree | Revision 1 posed these as questions; ChatGPT is right that they must be *tested*. My own capabilities are also untested: I can attach a GitHub repo to a session, but I have not yet done so for this project. |
| §4 Minimal CI early | Agree | `pytest` and `src.integrity` first; probes later. Treated as a follow-on task, not a decision. |
| §6 Pilot before migration | Agree | Zip handoff stays the default until the pilot passes. |
| §7 Setup cautions | Agree | Checklist rewritten below: check `origin` first, scan history for secrets, annotate tags, and don't assume plan features. |
| §7 A model's own review is not independent | Agree | Added as an explicit rule (item 5). |

**Reported, not verified:** ChatGPT states its GitHub integration was discoverable but not connected on 2026-10-20. I have not verified that. Commits `d04fb78` and `4abb4f1` are cited from `PROJECT_STATE.md` and are not re-verified in this document; the pilot verifies them (step P0).

---

## Part 2: Revised log entry

### D-051  Shared git remote as the handoff medium
- Decision status:        Proposed (adoption gated on the pilot in Part 3)
- Implementation status:  Not started
- Verification status:    Not applicable (process decision); the pilot result is recorded when run
- Date:                   proposed 2026-10-20
- Proposed by:            Corbin (idea: both models get direct access to project files); refined by Claude; amended by ChatGPT · **Reviewed by:** ChatGPT (conditional approval with amendments)
- Approval basis:         not confirmed
- Evidence:               Claude session transcript, 2026-10-20 13:11 (Corbin's proposal, quoted in revision 1); `docs/reviews/2026-10-20_ChatGPT_Review_of_D-051.md`; this revision
- Implementation ref:     not started
- Amends / supersedes:    amends D-046 and D-048; related to D-042, D-045, D-047
- Phase:                  All
- Open concerns:          tool capabilities untested for both models; branch-rule availability on Corbin's GitHub plan unknown

**Context.** Handoffs currently require downloading a zip, uploading it to the other model, and recreating files from chat output. This is slow and risks transcription errors. Corbin proposed giving both models direct access to the project files.

**Decision.**

*Repository*
1. **Canonical remote.** A private GitHub repository holds the canonical history from `d04fb78` onward. Local folders are working clones.
2. **Owner-controlled `main`.** Only Corbin integrates changes into `main`. Where available, repository rules enforce this. Otherwise the rule is procedural, and that residual risk is recorded in `PROJECT_STATE.md`.

*Changes and handoffs*

3. **Changes are pushed commits on a branch** named `<phase>/<model>-<topic>`.
   - *Standard path:* code, data, schema, and the substance of `DECISIONS.md` entries. The change gets an independent review, preferably in a pull request.
   - *Light path:* documentation wording or formatting within D-047's delegated scope. Owner approval and merge are still required, but no separate review is needed.
   - When unsure which path applies, use the standard path.
4. **Handoff minimum:** full SHA, base SHA, change summary, validation (commands, environment, results), and open questions or proposals. The handoff goes in the PR description, or in a short note pointing to the commit if PRs are unavailable.

*Review*

5. **Reviews are pinned to a full SHA.** Each review records at least: reviewed SHA, base SHA, scope, methods, commands and environment, findings with severity, unresolved issues, and a conclusion. It must separate reproduced results from untested claims (D-045). A model's review of its own implementation is not independent verification.
6. **One authoritative review record.** A substantial review is a single file, `docs/reviews/<date>_<model>_<topic>_<shortsha>.md`, linked from the PR. A lightweight review may be a PR comment. `DECISIONS.md` records decisions, rationale, approvals and links, not copies of review findings.
7. **Corrections are new commits on the same branch.** If a correction materially changes the reviewed state, the new SHA becomes a new review target.

*Approval*

8. **Approval names a specific revision.** Approval is an explicit owner action tied to an identified SHA. A merge by Corbin counts as acceptance of the merged revision. An approval never carries over to commits added afterward; a material change requires renewed review or owner acknowledgement. In `DECISIONS.md` §4, Corbin's comment is quoted verbatim where one exists. Otherwise, the action is recorded with its reference (PR link, merge commit) and no approval text is invented.

*Evidence and access*

9. **Only pushed commits are snapshots.** Uncommitted or unpushed work is never a reviewed state (D-046).
10. **Three kinds of verification are kept distinct:** (a) repository and snapshot integrity, (b) software behavior and reproducibility, and (c) anatomical and biomechanical evidence. Git history and passing tests establish (a) and (b), never (c). D-051 does not change D-045's verification statuses or any evidence rule.
11. **Scoped access.** Integrations are limited to this repository where supported. Tokens are never pasted in chat or committed. History is checked for secrets and unintended files before the first push.
12. **Capabilities are tested and recorded.** For each model, the following are tested and recorded in `PROJECT_STATE.md`: read at a SHA, check out an arbitrary SHA, run tests, push a branch, comment on or open a PR. Where a capability is missing, the fallback is a zip *with* `.git` plus the SHA. A zip without `.git` is reviewed as a file snapshot only, and the handoff says which method was used.

*Adoption*

13. **Adoption is gated on a pilot.** Direct git handoffs become the default only after the pilot in Part 3 passes and Corbin approves. Until then, zip handoffs remain the default.

**Records.** `PROJECT_STATE.md` holds the accepted merged SHA and the next action. `DECISIONS.md` holds consequential decisions and approvals only.

**Defense.** The essential controls are a fixed code state, an independent review of that state, and an explicit owner approval of that state. Everything else is interface. Pinning every artifact to a SHA meets D-046 and D-048 without manual transfer. Tying approval to a revision meets D-042. Keeping a single review record avoids drift. The pilot keeps the project from building its process on untested assumptions about tool access, which applies D-045 to the workflow itself.

**Alternatives.** (a) A shared local folder: no fixed snapshot, and silent overwrites are possible. It is kept as a way of *working*, not as the handoff. (b) A shared cloud folder: same problems as (a), and git history is lost. (c) Status quo zip handoffs: kept as the fallback. (d) Revision 1's always-PR workflow: rejected after ChatGPT's review as heavier than needed.

**Challenges.** ChatGPT recommended amendments A–E, CI timing, a pilot and setup corrections. Claude adopted all of them, narrowing A's light path to D-047's delegated documentation scope. ChatGPT's confirmation of that narrowing is pending.

**Consequences.** The project depends on GitHub and on each model's access. If branch rules are unavailable on Corbin's plan, owner-only merging is procedural. **Follow-on task after the pilot:** a minimal CI workflow running `python -m pytest -q` and `python -m src.integrity` in a clean environment, with the probes added once their output is confirmed stable. CI is supporting evidence, never a substitute for D-045 reproduction or scientific validation. It counts as test tooling under D-047, not a new decision, unless it changes verification policy.

---

## Part 3: Pilot checklist

**Goal:** prove that both models can work from the same pushed commit, and that review, correction, approval and merge work end to end. **Pilot target:** the Phase A commit `4abb4f1`. ChatGPT's Phase A review is already the next task, so the pilot doubles as that review.

### P0. Preflight (Corbin, in the local repository)
```bash
git status                       # working tree clean?
git branch --show-current        # expect: main
git cat-file -t d04fb78          # expect: commit
git cat-file -t 4abb4f1          # expect: commit
git log --oneline | head         # history looks as expected
git remote -v                    # does an 'origin' already exist? If so, stop and check before adding one
```
**Secrets and unintended files.** Search all history, not just current files:
```bash
git log --all --stat | less      # skim for unexpected files (large binaries, personal files)
git grep -I -n -i -E "api[_-]?key|token|secret|password" $(git rev-list --all)
```
Expect no real credentials. Anything found must be removed from history *before* pushing; ask for help with that step rather than improvising. Also confirm `.gitignore` covers caches and virtual environments.

### P1. Create the remote and push
1. Create a **private**, empty repository on GitHub (no README or `.gitignore`).
2. Push the history and add annotated milestone tags:
   ```bash
   git remote add origin https://github.com/<your-username>/lb-ao.git
   git push -u origin main
   git tag -a baseline-received d04fb78 -m "Original work as received (D-046)"
   git tag -a phase-a-built 4abb4f1 -m "Phase A implementation, pre-review"
   git push origin --tags
   ```
   Tags mark history only, not approval or scientific validity. Don't move them later.
3. On GitHub, confirm that the repository is private and that both commits and both tags appear.

### P2. Repository rules
In the repository settings, try to require a pull request for `main`, allow only yourself to merge, and, if offered, dismiss existing approvals when new commits are pushed. Record whether owner-only merging is **enforced** or **procedural**.

### P3. Capability check (each model; record the results)
| Capability | Claude | ChatGPT |
|---|---|---|
| Read files at a given SHA | | |
| Check out an arbitrary SHA | | |
| Install requirements and run `pytest` / `src.integrity` | | |
| Push a branch | | |
| Comment on or open a PR | | |

Claude: connect GitHub in claude.ai, then I attach the repo in a session and test each row. ChatGPT: connect its GitHub integration with access to this repository only, then test each row. Where a capability is missing, write down the fallback (zip with `.git` plus SHA).

### P4. Pilot review
ChatGPT performs the Phase A review in `PROJECT_STATE.md` against `4abb4f1`, read from the remote, or through the recorded fallback if access fails. It produces one review file in the item 5 format, saying exactly what was reproduced.

### P5. Correction round
Claude creates the branch `phase-a/claude-review-response` and commits responses to any findings. The same branch carries the record-keeping:
- the ChatGPT review file;
- both D-051 proposals and ChatGPT's D-051 review in `docs/reviews/`;
- D-051 added to `DECISIONS.md` as `Proposed`;
- the capability table added to `PROJECT_STATE.md`.

If the review raises no findings, this record-keeping commit alone still tests the builder step. No change is invented to exercise it.

### P6. Approval and merge
ChatGPT confirms or disputes the branch head SHA. Corbin explicitly approves that SHA and merges. `PROJECT_STATE.md` is updated to the merged SHA.

### P7. Pass or fail
| Criterion | Met? |
|---|---|
| The remote holds the intended history, commits and tags | |
| Both models read the same SHA, or a documented fallback was used | |
| The review is pinned to a commit with honest test-execution status | |
| The builder responded through new commits | |
| Corbin approved a specific SHA and merged it | |
| `PROJECT_STATE.md` and `DECISIONS.md` are consistent after the merge | |

If every criterion is met, Corbin decides whether to accept D-051. On acceptance, git handoffs become the default, the zip remains the fallback, and the CI task follows. If any criterion fails, the cause is recorded, zip handoffs continue, and D-051 is amended.

---

## Requested decisions

1. **Corbin:** approve running the pilot. D-051 itself stays Proposed until the pilot passes.
2. **ChatGPT:** confirm or dispute the narrowing of amendment A (light path limited to D-047's delegated documentation scope).
