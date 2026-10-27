---
name: independent-study-builder
description: Use when assigned the Builder role on the Independent Study / LB-AO project, before modifying any file.
---

# Builder Skill — v0.2 candidate

**Status:** proposed; **author:** ChatGPT, amendments marked [G2], [G3], [G6], [G8] by Claude; **independent reviewer:** Claude for ChatGPT's text, ChatGPT for Claude's amendments. Read `docs/protocols/CORE.md` first, at the current `main` or the named candidate SHA [G8], and follow accepted repository decisions over this draft. Follow the full path unless the narrowly defined light path in `CORE.md` applies.

## 1. Establish authoritative state
Confirm repo, access mode, `main` full SHA, base/working branches, `git status`, assigned roles, approved scope and acceptance criteria. Read `PROJECT_STATE.md`, `DECISIONS.md`, relevant source records, specifications, tests and unresolved reviews. If `PROJECT_STATE.md` is inconsistent with `main` (stale phase, task, roles or snapshot), record both in the handoff; stop only if the inconsistency affects this task's scope, inputs or role assignment, and do not correct it unless that is part of the assigned task [G3]. Never silently choose between them. Demonstrate tool capabilities before relying on tests, push, PRs or comments; disclose unavailable capabilities.

## 2. Plan and seek required decisions
Map each requirement to planned changes, tests, scientific evidence and limitations. Record assumptions, units, sign/coordinate conventions, valid ranges, provenance, source-versus-derived-versus-demo values, symmetry, and muscle/compartment scope when relevant. Assess compatibility and interface effects. Obtain owner authorization for D-047-reserved changes; a blocker does not widen delegation. Capture mid-session owner decisions verbatim with timestamp, offset and question answered as proposed approval records.

## 3. Implement within approved scope
Use a task branch consistent with repository convention; keep changes focused and preserve compatibility unless authorized otherwise. Add meaningful positive, negative, boundary and regression tests. Preserve baseline sourced data; apply scenario changes through overlays rather than editing shared parameters. Record effective inputs, source references, units, environment, and exact code snapshot in relevant run manifests. Detect dirty, untracked or external inputs when committed-input integrity is required. If an out-of-scope defect appears, fix only if already delegated or covered by accepted scope; otherwise propose and await owner direction. Record each choice made under D-047's delegation, with its basis, in the commit message or the handoff, so the reviewer can check it stayed inside the delegation (D-047; example D-050) [G2].

## 4. Verify and report evidence
Report separately (a) repository/input integrity, (b) software checks and (c) scientific support/validation limits. Run applicable checks, normally `python -m pytest -q`, `python -m src.integrity`, and relevant probes. Record exact commands, environment, dependencies, outcomes, warnings and omissions. Do not reuse another model's reported results as if reproduced. Apply conditional checks in `checklists/verification.md`. Builder verification status is `Reported by author`, never `Independently checked`.

## 5. Commit and hand off
Record full starting and final SHAs, status and changed files. Put `Authored by (model): ChatGPT` or `Claude` in commit body and PR description. Push/open PR only after capability and success are confirmed. Fill `checklists/handoff_contract.md` in the PR description; update `PROJECT_STATE.md` to point to it and name the next action, unless another open PR is editing it (then follow `CORE.md`, Records updates). Recheck all proposed record IDs (`D`, `Q`, `A`, `C`) against `main` and open PRs before merge, and renumber collisions before merge [G6]. Request independent review of the exact final SHA. Do not self-approve or merge without owner authority.

## Review cycle and exit
Evaluate findings on evidence, document agreements/disagreements, fix accepted issues, and submit a **new** pinned SHA for re-review. If blocked by unanswered authorization, stop at the decision boundary; when permitted and possible, push a **draft PR marked BLOCKED** with the open question first and the completed work clearly scoped. If remote operations are unavailable, provide a precise fallback and do not claim they succeeded. A complete Builder handoff means **ready for review, not approved or scientifically validated**.
