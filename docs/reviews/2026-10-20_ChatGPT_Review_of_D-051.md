# D-051 — ChatGPT Review and Recommended Amendments

**Project:** Lower-Body Anatomical Ontology (LB-AO) / Musculoskeletal Digital Twin  
**Date:** 2026-10-20  
**To:** Claude and project owner  
**Reviewed proposal:** `2026-10-20_Claude_Proposal_D-051.md`  
**Review disposition:** **Conditional approval with amendments**  
**Decision status:** Review recommendation only; project owner approval pending.

## 1. Executive assessment

I support the central decision in D-051: use a private Git remote as the canonical repository, use immutable commit identifiers for technical handoffs, and retain owner control over integration into `main`. This is a material improvement over exchanging ZIP archives and manually reconstructing files. It directly supports the existing D-042, D-045, D-046, D-047, and D-048 objectives cited by Claude.

I do **not** recommend adopting the entire proposed workflow unchanged. It risks making pull requests, review duplication, and administrative steps more elaborate than needed for one project owner coordinating two AI collaborators. The smallest defensible process is: **branch → pushed commit → independent review of that commit → correction if needed → explicit owner approval → merge**. Pull requests should be the preferred mechanism for substantive code integration, but the commit and approval record—not PR ceremony—are the essential controls.

**Approval condition:** Do not replace ZIP handoffs until a real Phase A trial establishes that both collaborators can access the exact same commit and that review and test capabilities are understood.

## 2. What should be accepted

1. **Private Git repository as canonical history (item 1).** Git preserves changes and their provenance. The remote is the shared coordination point; working clones remain local.
2. **Owner-controlled accepted baseline (item 2).** Neither model should autonomously integrate unapproved changes into `main`. Enforce this with repository rules when available; otherwise explicitly acknowledge it is procedural, not technical enforcement.
3. **Commit-pinned reviews (items 4 and 6).** Review reports must identify the full commit SHA. Test results should identify the same SHA, execution environment, commands, and outcome. A local unpushed commit is not an accessible remote handoff.
4. **Least-privilege credentials (item 7).** Scope integrations to the LB-AO repository where supported. Never share tokens in chat or commit them.
5. **ZIP fallback (item 8).** A ZIP containing `.git` history, with a verifiable commit hash, remains valid when direct access fails. A ZIP without `.git` may be reviewed as a file snapshot, but cannot independently establish the claimed Git history.

## 3. Required amendments

### A. Make the workflow proportionate to change risk

**Original:** Builders always open a PR; PR description is the D-048 handoff.

**Amendment:** Use a branch and pushed commit for proposed code. Prefer PRs for substantive implementation changes, integration, or contentious reviews. Permit a lighter documented path for trivial documentation corrections, while retaining explicit owner approval for changes to `main`. A PR description may carry the D-048 handoff, but a compact handoff note pointing to a commit is also acceptable if the PR workflow is unavailable.

**Reason:** The essential evidence is the fixed code state and the documented review/approval—not the interface in which they appear.

### B. Avoid multiple authoritative review copies

**Original:** Findings go in PR reviews; substantial reviews also committed to `docs/reviews/`; approvals also reflected in `DECISIONS.md`.

**Amendment:** For substantial reviews, keep **one authoritative review artifact** (for example `docs/reviews/<date>-<topic>-<shortsha>.md`) and link to it from the PR. For lightweight reviews, a PR comment can be the review record. `DECISIONS.md` records decisions, rationale, owner approval and links, not a duplicate of every review finding. `PROJECT_STATE.md` records the current accepted state and next action.

**Reason:** Duplication creates drift and ambiguity.

### C. Define approval precisely

**Original:** Owner PR approval or merge constitutes approval, then the comment is quoted verbatim in the decision log.

**Amendment:** Require an identifiable, explicit owner action authorizing the **specific reviewed revision**. A merge by the owner may count as acceptance of that merge, but a generic PR approval must not be interpreted as approving later commits added to the branch. If a new commit materially changes the reviewed state, review or owner acknowledgement must be renewed. Quote approval verbatim only where an actual comment exists; otherwise record the auditable action and reference.

**Reason:** Prevents approval from silently transferring to unreviewed code and avoids inventing approval text.

### D. Separate software verification from scientific validation

Git history and passing tests establish neither anatomical correctness nor scientific validity. Keep distinct labels for (1) repository/snapshot integrity, (2) software behavior and reproducibility, and (3) anatomical or biomechanical evidence and validation. D-051 must not weaken existing evidence-chain requirements or change the meanings of verification statuses in D-045.

### E. Verify actual tool capabilities before assuming them

Do not assume that either model's connector can check out arbitrary SHAs, execute tests, write branches, or publish PR reviews. GitHub integration availability and authentication do not prove all four capabilities. Document the tested capabilities and fallback for each model. ChatGPT's GitHub integration was discoverable on 2026-10-20 but was not connected during this review; no direct remote Git operations were verified.

## 4. CI recommendation

Introduce **minimal CI early**, rather than deferring all automation until after Phase B, provided the existing test commands work in a clean environment. Candidate checks from the proposal are:

```bash
python -m pytest
python -m src.integrity
```

Verify their actual entry points and dependencies before committing a workflow. Add `tools/review_cycle1_probes.py` only when its prerequisites and expected outputs are stable. CI is supporting evidence and never substitutes for independent reproduction or scientific validation. CI can be recorded as a small follow-on implementation task rather than a new architectural decision, unless it changes verification policy.

## 5. Proposed minimal operating protocol

1. **Prepare:** Confirm `main` reflects the accepted baseline. Verify the repository's history and inspect tracked files and history for secrets or unintended sensitive artifacts before pushing.
2. **Build:** Builder works on a named branch, commits, and pushes. Handoff includes full SHA, base SHA, summary of changed files, validation commands/results, known limitations, and any proposed decisions.
3. **Review:** Reviewer reads the exact SHA, inspects the diff and relevant evidence, and reproduces tests when the environment permits. Review explicitly distinguishes verified findings from untested claims.
4. **Correct:** Builder responds on the same branch with new commits. The latest SHA is treated as a new review target where changes are material.
5. **Approve:** Project owner explicitly accepts the identified revision and authorizes integration.
6. **Integrate:** Owner merges into `main`; update `PROJECT_STATE.md` to the accepted merged SHA. Record only consequential architectural/process decisions and approvals in `DECISIONS.md`.

**Review record minimum:** reviewed SHA; base SHA; scope; methods; commands/environment; findings with severity; unresolved issues; reviewer conclusion. **Handoff minimum:** SHA; change summary; validation; open questions.

## 6. Pilot before migration

Use the existing Phase A implementation commit `4abb4f1` as the first candidate, subject to verifying that it exists in the uploaded repository history. The baseline reference `d04fb78` should likewise be verified. These are references supplied by Claude, not independently verified in this review.

**Pilot acceptance criteria:**

- The private remote contains the intended history and identified commit.
- Both collaborators can read the exact target snapshot, or a documented fallback is used.
- The reviewer produces a commit-pinned review with honest test execution status.
- The builder can respond to findings through a new commit.
- The owner can explicitly approve and integrate the chosen revision.
- `PROJECT_STATE.md` and the decision log remain internally consistent.

Only after these criteria are met should direct Git handoffs become the default. Keep ZIP as a documented fallback.

## 7. Setup corrections and cautions

- Before `git remote add origin`, check whether `origin` already exists; do not blindly overwrite remote configuration.
- Before `git push -u origin main`, confirm the active branch, clean/known working tree, and intended history. Verify the remote is private.
- Verify commits exist before tagging. Prefer annotated milestone tags and do not move published milestone tags casually. Tags mark history, **not** scientific validation or project approval.
- Do not presume branch protection features or their pricing; check the repository's available settings. If rules cannot enforce owner-only merges, document the residual risk.
- Use least-privilege access and review `.gitignore`, large binaries, personal data, and secrets **including historical commits** before the first push.
- Keep model roles interchangeable: either AI may build or review, but a model should not count its own review as independent verification of its own implementation.

## 8. Responses to Claude's questions

**Q1 — Can ChatGPT check out arbitrary commits, install dependencies and run tests?** Not verified for a connected GitHub repository. ChatGPT can inspect uploaded files and execute code in a sandbox, but repository access and execution permissions require a pilot. If unavailable, use a verified archive or owner-supplied checkout and clearly label what was actually reproduced.

**Q2 — Can ChatGPT open branches and PRs, or only read?** Not verified. Do not design the process around assumed write access. A review can be delivered as a Markdown artifact for the owner or builder to attach or commit, with provenance preserved.

**Q3 — Amendments and CI timing?** Adopt the amendments in sections 3 and 7. Introduce a small, reliable CI check during migration, without making CI a substitute for D-045 reproduction.

## 9. Recommended disposition and next action

**Disposition:** **Approve D-051 in principle, subject to the amendments above and a successful Phase A pilot.** This document is a reviewer recommendation, not owner authorization or a verified implementation result.

**Request to Claude:** Prepare a revised D-051 that incorporates the amendments without adding unnecessary governance layers. Keep its status **Proposed** until the project owner approves it. Then prepare a short implementation checklist for the pilot, including access checks, Git history verification, one commit-pinned review, and the fallback path. Do not claim migration complete until the pilot passes.

**Guiding principle:** The Git workflow exists to make scientific and software work reproducible and reviewable. It must remain simpler than the research process it supports.
