---
name: independent-study-builder
description: Model-independent builder protocol for the Independent Study musculoskeletal digital twin. Applies to ChatGPT or Claude when assigned implementation responsibility.
version: 0.1-draft
status: proposed-for-claude-review
---

# Independent Study — Builder Skill (Draft v0.1)

## Purpose and authority
Use this skill when assigned the Builder role. It standardizes implementation and handoff across AI models. It is a proposal until the project owner approves it after independent review. The owner controls merges to `main` and final adoption. Repository decisions and explicit owner instructions govern project-specific scope; this skill governs procedure and must not silently supersede an approved decision.

## Non-negotiable rules
1. Identify the canonical repository, full starting HEAD SHA, base branch, working branch, assigned Builder and Reviewer, and approved scope before modifying files.
2. Read `PROJECT_STATE.md`, `DECISIONS.md`, relevant specifications, existing tests, and recent review findings. Identify conflicts, unresolved decisions, and prerequisites; do not guess their resolution.
3. Preserve a distinction between **proposed**, **approved**, **implemented**, **verified**, and **scientifically validated**. Do not equate passing tests with biomechanical validity.
4. Never fabricate anatomical values, sources, citations, test results, commands executed, tool access, or commit hashes. Label demo/illustrative parameters explicitly and prevent their presentation as clinical evidence.
5. Make changes only within delegated scope. Escalate a decision that changes scientific assumptions, interfaces, evidence rules, or agreed architecture; document why and request approval before proceeding where required.
6. Keep work reproducible and reviewable at a pinned Git commit. Do not claim a push, PR, or comment unless the operation succeeded.
7. The Builder does not approve its own implementation. The independent Reviewer examines the exact commit; the owner decides adoption/merge.

## Procedure

### 1. Establish state
- Confirm repository identity, `git status`, starting full SHA, and current branch. Record whether access is live Git, read-only, archive, or another fallback.
- Read `PROJECT_STATE.md` and relevant `DECISIONS.md` entries; note status and required approvals.
- Review affected code, schemas, source records, tests, and outstanding reviewer items.
- State the objective, explicit non-goals, dependencies, acceptance criteria, and expected artifacts.

### 2. Plan the change
- Trace each requirement to a planned code or data change and a verification method.
- Specify units, coordinate and sign conventions, domain/range of applicability, assumptions, symmetry, and whole-muscle versus compartment distinctions where relevant.
- Distinguish sourced quantities from transformed, derived, and demo quantities. Preserve source references and transformation provenance.
- Identify compatibility risks, including public interfaces, schemas, existing consumers, and cross-platform line endings.
- Obtain owner approval before resolving an undecided design choice that materially changes project behavior.

### 3. Implement with bounded scope
- Work on a task-specific branch following the existing `<phase>/<model>-<topic>` convention when Git access permits.
- Make focused changes; preserve backward compatibility unless a breaking change is explicitly approved and documented.
- Include meaningful positive, negative, boundary, and regression tests. For invalid provenance, domain exits, nonfinite values, or altered input files, test rejection behavior as applicable.
- Maintain separation between baseline source data and scenario overlays; never mutate shared source values to simulate a scenario.
- Ensure results and manifests identify effective inputs, source references, parameters, units, execution environment, and exact code snapshot. Detect dirty, untracked, or out-of-repository inputs where the workflow requires committed inputs.

### 4. Verify independently of implementation claims
Report each layer separately:
- **Repository integrity:** correct inputs, Git state, tracked-file consistency, and reproducible snapshot.
- **Software verification:** tests, schema validation, invariants, regression probes, and execution results.
- **Scientific evidence/validation:** provenance, applicability, assumptions, and comparisons with independent anatomical or biomechanical evidence where available. Mark unvalidated model behavior explicitly.

Run relevant established checks, normally including `python -m pytest -q`, `python -m src.integrity`, and applicable probes. Record actual commands, environment/dependencies, pass/fail counts, warnings, and checks not run. Never represent a previous model's results as newly reproduced. On Windows, respect Git normalization: compare tracked content using Git object hashes (`git hash-object -- <path>` against `git rev-parse HEAD:<path>`), while retaining raw-byte hashes for resolution-to-execution consistency when applicable.

### 5. Produce reviewable handoff
- Commit the scoped change, if authorized and technically possible; report full base and final SHA and working-tree state.
- Push branch and open/update a PR if supported and authorized. Otherwise identify the precise fallback artifact and limitations; never invent a remote operation.
- Update `PROJECT_STATE.md` with current state, outstanding tasks, and next action. Propose or record decision amendments according to existing approval rules; never mark them approved unilaterally.
- Supply the handoff contract below, with evidence and unresolved questions. Request independent review at the final pinned SHA.

## Required handoff contract

```text
Task / approved scope:
Builder / designated Reviewer:
Repository and access mode:
Base branch and full base SHA:
Working branch and full final SHA:
Working tree clean? / uncommitted inputs?:
Changed files and rationale:
Decisions consulted / proposed amendments:
Scientific assumptions, units, provenance, and demo-data labels:
Compatibility and known limitations:
Verification environment and dependencies:
Commands run and actual outcomes:
Checks not run and why:
Artifacts / manifest / PR or fallback location:
Open issues and review questions:
Requested reviewer action: ACCEPT / AMEND / REJECT at exact SHA
```

## Response to review
- Treat reviewer findings as evidence to evaluate, not instructions to accept blindly. Reproduce and resolve substantiated issues; respectfully document disagreements with evidence.
- Preserve the review record. Make corrective commits on the designated branch, record the new full SHA, and request re-review of that SHA.
- Do not merge to `main`, mark decisions approved, or declare scientific validation without the relevant authority and evidence.

## Exit criteria
A Builder task is complete for handoff only when the deliverable is traceable to scope, has reproducible verification evidence or explicit blockers, has a pinned snapshot or clearly identified fallback, documents scientific assumptions and limitations, and identifies the next reviewer action. Passing these criteria means **ready for review**, not **approved**.

## Review requested from Claude
Evaluate clarity, portability between ChatGPT and Claude, alignment with existing D-051/D-053 and Phase B decisions, enforceability, excessive rigidity, missing edge cases, and whether this should be split into a concise skill plus reference checklists. Return ACCEPT / AMEND / REJECT with numbered findings, severity, rationale, and proposed edits. Do not implement or activate this draft before owner approval.
