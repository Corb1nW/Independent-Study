# Review of the Phase B build (PR #13)

**Reviewer:** Claude (Phase B reviewer, Q17)
**Date:** 2026-10-21
**Reviewed SHA:** `bf92dfd44d79de2681aab1318ee31ad171f12690` (PR #13 head, branch `phase-b/chatgpt-hip-model`)
**Base SHA:** `cfba5957370d7a676673080039c5d21d179c1ff4`
**Author of the work reviewed:** ChatGPT (Phase B builder)
**Implements:** D-053 as accepted at `ab082f5` (Q18), with re-review notes N2 and N3
**Disposition:** **AMEND.** The model, resolver, event handling and scenario overlay are correct, and the numbers match closed-form mechanics exactly. Two medium findings should be fixed before merge: the run manifest can certify a commit while using uncommitted inputs (C1), and no test fails if source validation is removed from the resolver (C2). Four low findings follow.

## Scope and methods

- Read every changed file: `src/hip_phase_b.py`, `config/phase_b_hip.yaml`, both scenario files, `tests/test_phase_b.py`, `tools/run_phase_b.py`, `PHASE_B_README.md`, and the `PROJECT_STATE.md` diff.
- **Executed** in a git checkout of `bf92dfd` (Python 3.13.16, pytest 9.1.1, pydantic 2.14.1, pint 0.26.2, PyYAML 6.0.3):

| Command | Result |
|---|---|
| `python -m pytest -q` | **98 passed** (82 existing + 16 new) |
| `python -m src.integrity` | PASSED |
| `python tools/review_cycle1_probes.py` | 9/9 REJECTED (CI doesn't run this; now reproduced at the exact head) |
| `python -m tools.run_phase_b --commit-sha bf92dfd… --output <tmp>` | ran; both scenarios `domain_exit` at the lower limit; provenance `verified_git_head` |

  CI on the PR also passed (98 tests, integrity check). My run is independent of both CI and ChatGPT's local archive run.
- **Mutation checks** (one change at a time, then restored): see C2.
- **Adversarial check** of manifest provenance with an uncommitted config edit: see C1.
- The output below is from an unmerged branch and is **not a project result**. Results count only after Corbin merges and the runner is executed at the merged commit (D-040 Amendment 1).

## The numbers check out exactly

With `r0 = 0.04 m`, `a = 0.02`, `I = 1 kg·m²`, `Fmax = 1852.6 N`, starting at rest at `q = 0`, the torque is constant, so the motion has a closed form: `τ = −r0·a·F`, `q̈ = τ/I`, time to reach `−π/6` is `t = √(2·(π/6)/|q̈|)`, and exit speed is `√(2·(π/6)·|q̈|)`.

| Scenario | Right Fmax (N) | Torque (N·m) | Exit time, model (s) | Closed form (s) | Exit speed (rad/s) |
|---|---|---|---|---|---|
| baseline (×1.0) | 1852.6 | −1.48208 | 0.840578902667 | 0.840578902667 | −1.24581 (closed form −1.24581) |
| perturbed (×1.2) | 2223.12 | −1.778496 | 0.767340043923 | — | −1.36471 |

The output change is **explainable**: exit time scales as `1/√F`, so a 20% force increase should shorten it by a factor of `1/√1.2 = 0.912871`. The model gives 0.912871 (agreement within 1e-15). This is the D-036 / D-040 exit criterion working as intended: a YAML-level input change produces a predicted, interpretable output change. The integrator is exact for constant acceleration, so step-size insensitivity holds by construction, and the tests confirm it against the closed form.

## What is right

- **Resolver:** `effective_baseline(dataset, RIGHT)` then `validate_datum(datum, dataset)` (D-052), plus checks on property, role, form, unit and `model_id`. The left-side value is reported but unchanged.
- **D-053 law and signs:** `τ = −r0·a·F_right` gives negative (extension) torque under flexion-positive `q`. The ontology IDs `LB:DOF:HIP_FLEX_EXT_R` and `LB:FRAME:PELVIS` are bound and resolved, and the domain is pinned to exactly `[−π/6, π/3]`.
- **B1 events:** analytic first-crossing per step, with no clamping, no hidden torque and no out-of-domain state returned. Initial states outside the domain are rejected, and an "undetected domain exit" raises.
- **N2:** a boundary start uses velocity, or acceleration when the velocity is zero. Tested both ways at both limits.
- **N3 / B2:** the overlay loader requires exact fields, the label `demonstration_scenario_not_evidence`, the right-side target, an existing base observation, and a positive finite multiplier (booleans and strings rejected). The canonical dataset hash is tested as unchanged.
- **Config:** every number has a unit, the kind `demonstration_assumption` and a rationale. `r0` and `I` are stated as round, non-anatomical values, as D-053 allowed.
- **Honesty of the handoff:** the PR distinguishes ChatGPT's archive run from the exact-head CI run, says probes weren't run at the head, and labels outputs as unreviewed. The first CI failure was diagnosed correctly: the test was wrong, not the code.

## Findings

### C1 — MEDIUM: the manifest says `verified_git_head` even when inputs differ from that commit
`run_manifest` checks only that the supplied SHA equals `git rev-parse HEAD`. I changed `moment_arm_m` to 0.08 in the working tree without committing. The manifest still reported `commit_provenance_status: verified_git_head`, with `r0 = 0.08`. The config hash is recorded, so a careful reader could detect the mismatch, but the status field asserts something false. `tools/run_phase_b.py` also accepts `--config` / `--baseline` / `--perturbed` paths outside the repository with the same status. Recording exactly which numbers ran at which commit is the purpose of Phase B (D-036, D-040 Amendment 1).
**Requested:** check for uncommitted changes (e.g. `git status --porcelain`) to the model, config, scenario and dataset files, and check that every input path lies inside the checkout. If either fails, either refuse to run or set a distinct status such as `head_matches_but_inputs_modified` / `inputs_outside_repository`. Add a test for each.

### C2 — MEDIUM: removing source validation from the resolver breaks no test
Mutation results against `tests/test_phase_b.py`:

| Mutation | Tests failing |
|---|---|
| torque sign flipped | 3 |
| event detection disabled | 6 |
| scenario multiplier ignored | 1 |
| N2 rule removed | 3 |
| **`validate_datum(…)` replaced by “no errors”** | **0** |
| right-side check in the overlay loader removed | 0 (redundant: the target is also pinned to one ID) |

The validated resolver is the bridge from evidence to dynamics, and nothing tests that it rejects a bad source record.
**Requested:** a test that builds a temporary project root (as `test_integrity_check_catches_dangling_observation_reference` does) with a corrupted Fmax record, for example a wrong unit or a removed source claim, and asserts that `resolve_inputs(…, root=tmp)` raises. The side-check redundancy needs no change.

### C3 — LOW: make the perturbation test check the explanation, not just the direction
`test_overlay_force_and_canonical_source_integrity` asserts only that the perturbed exit time is shorter.
**Requested:** assert `t_perturbed / t_baseline == 1/√1.2` (closed form above). That turns “output changed” into “output changed by exactly the predicted amount”.

### C4 — LOW: declare tuned values and omitted physics in the config and manifest, not only the README
- `activation = 0.02` has the rationale “Constant illustrative muscle activation”. Its effect is to make the exit time about 0.84 s. If it was chosen for that reason, the rationale should say so: a value chosen to make the output observable is honest only if labelled that way.
- Gravity, passive joint structures and the knee are omitted. The README says so, but the config and manifest do not; `external_torque_N_m = 0` reads “No external torque in baseline”. Since the manifest is meant to stand alone, add a `limitations` / `omitted_physics` block (gravity omitted, pelvis fixed and orientation undefined, no passive torque, no activation or tendon dynamics) to both.

### C5 — LOW: record the B2 implementation choice
D-053 Amendment 1 (B2) describes building a *temporary copied YAML dataset*. The build reads the canonical dataset read-only and applies the multiplier in memory, never writing any file, and the hash test confirms that. This is simpler and equivalent in substance, but the decision text and the code now differ. Note it in `PHASE_B_README.md` or the PR record so a later reader doesn't think a step was skipped.

### C6 — LOW: records housekeeping
- `PROJECT_STATE.md` lists `DECISIONS.md` as revision 6; it is revision 10 on `main`. **This staleness is mine**: my PRs #8 and #12 didn't update that line. Fix it whenever this file is next edited.
- Several commits repeat the same message (separate per-file uploads through the connector). That is harmless and needs no change, though a single commit per logical change would make the history easier to read.

## Conclusion

**AMEND.** After C1 and C2 are fixed (C3–C6 are recommended), I expect to AGREE. The mechanics are correct and verified against closed form, and the perturbation is explainable to 15 digits. Then Corbin merges, and the runner is executed at the merged commit to produce the official Phase B baseline and perturbation record.
