# Re-review of D-053 (PR #9) after Amendment 1

**Reviewer:** Claude (Phase B reviewer, Q17)
**Date:** 2026-10-21
**Reviewed SHA:** `ab082f5d3bcc27e5388bda5c6e5bf473513aed31` (PR #9 head)
**Previous review:** `docs/reviews/2026-10-21_Claude_Review_D-053_70f518f.md`, at `70f518f` (AMEND, minor)
**Author of the work reviewed:** ChatGPT (Phase B builder)
**Disposition:** **AGREE. I recommend Corbin approve D-053 at `ab082f5`.** All five findings are resolved. Three non-blocking notes are for the build PR.

## Scope and methods

- Read `git diff 70f518f ab082f5` (`docs/DECISIONS.md` only: D-053 Amendment 1, header, revision 9) and ChatGPT's response comment on PR #9.
- **Executed** at `ab082f5` (Python 3.13.16, pytest 9.1.1, pydantic 2.14.1, pint 0.26.2, PyYAML 6.0.3): `python -m pytest -q` → 82 passed; `python -m src.integrity` → PASSED; `python tools/review_cycle1_probes.py` → 9/9 REJECTED. `git diff --name-only 42ca56a ab082f5` → only `docs/DECISIONS.md`; one `### D-053` entry. GitHub reports PR #9 mergeable (clean), and `git merge-tree` against current `main` shows no conflict.
- Mechanics are assessed by derivation; no primary sources were read.

## Findings

| # | Request | Amendment 1 | Status |
|---|---|---|---|
| B1 | Define behaviour at the domain boundary | Closed interval; invalid initial states rejected; terminate at the first crossing with event localization; `domain_exit` outcome recording time, state, limit, method and tolerance; no clamping, hidden torque, reflection or continuation; both limits and step sizes tested | **Resolved.** Clearer than I asked for, including the `completed` outcome and the note that trial steps outside the domain are never accepted as output |
| B2 | The perturbation must not edit the shared `Fmax` record | Canonical file immutable; temporary copy plus a labelled right-side scenario overlay that *points to* the Arnold datum; baseline resolved and validated first (`effective_baseline`, `validate_datum(…, dataset)`), multiplier applied in memory to the right side only; tests for an unchanged file hash, an unchanged left side, the right-side proportion, and invalid input; manifest records the overlay and hashes | **Resolved.** The overlay keeps scenario inputs separate from evidence, as D-015 requires |
| B3 | Bind `q` to ontology IDs | `LB:DOF:HIP_FLEX_EXT_R` relative to `LB:FRAME:PELVIS`, both must resolve, flexion-positive per `SRC:ISB_WU_2002`; neutral pose declared in configuration | **Resolved** |
| B4 | Record the size of omitting `cos α` | ≈7.8%, conditional on `Fmax` being a fiber force, explicitly illustrative; disclosed in run reports | **Resolved.** The caveat wording is better than mine |
| B5 | Housekeeping | Header scope updated; D-037 status to be updated only after acceptance, without backdating | **Resolved** |

## Non-blocking notes for the build PR

- **N1 (wording).** Amendment 1's opening says its clarifications apply “without changing the **approved** status”. D-053 is not approved yet; this presumably means “the Proposed status”. It can be fixed when acceptance is recorded.
- **N2 (boundary edge case).** “Directed outward” at a boundary start should be defined in the build. I suggest: by the sign of `qdot`; when `qdot = 0`, by the sign of the net angular acceleration at `t = 0`. This avoids an ambiguous zero-velocity start, which is likely if the first run starts at rest at a limit.
- **N3 (overlay format).** The scenario overlay is a new, Phase B–only input format. The build PR should include its loader and validation (target entity exists and is right-sided, base observation exists in the dataset, multiplier positive and finite) together with the tests Amendment 1 lists, so the format isn't used before it is checked.

## Conclusion

**AGREE.** D-053 at `ab082f5` meets D-037 Amendment 1: the representation and its rationale are recorded; force and moment arm have compatible definitions (whole-muscle lumped force, constant signed arm, length relation consistent under `r = −dL_MT/dq`); torque direction is testable; and the assumptions are traceable in the planned run record. Next, Corbin explicitly approves this SHA. The `r0` value, inertia, activation, initial state and integrator settings come in the separate build PR, which I will review before anything runs.
