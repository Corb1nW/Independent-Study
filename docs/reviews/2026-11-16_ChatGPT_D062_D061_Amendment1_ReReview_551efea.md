# D-062 scope review and D-061 Amendment 1 re-review

- **Date:** 2026-11-16
- **Reviewed by (model):** ChatGPT
- **Built by (model):** Claude
- **Proposal:** [PR #43](https://github.com/Corb1nW/Independent-Study/pull/43)
- **Reviewed SHA:** `551efea2279dd2fe89610e50752de41acf173d1b`
- **Base SHA:** `c29572becc1e495b78a7efe643a516b63f9c3ba4`
- **Earlier reviewed SHA:** `57bfeaa7ac1beebceeff2b572aa3e2d5cd29c1e8`, [PR #46](https://github.com/Corb1nW/Independent-Study/pull/46)
- **Verdict:** **AMEND** on the D-062 scope. Corbin makes the decision.
- **Status:** REVIEWED, NOT APPROVED

## Scope and independence

I checked D-061 Amendment 1, the new Stage D4 scope in D-062, the source and handoff changes, and the delta from the earlier review. Relative to current main, the four changed files are documentation. The additional demo files since the earlier SHA match main. The quoted Q66 and Q67 direction in the decision log matches the PR handoff, with tentative agreement followed by D4-only scope. The underlying Claude transcript was outside this check. I verified the A-18 merge SHAs and times for PRs #44 and #45.

I authored the earlier review, including its center-of-rotation counterexample. The amended D4 checks and the independent probes of their behavior below were reviewed against Claude's proposal and existing model inputs. This review reads the proposal and probes its acceptance conditions using the existing models and data.

## Earlier findings

| Finding | Disposition | Evidence |
|---|---|---|
| D061-B01 | Resolved in principle | C1 derives crossings from path topology. C2 computes leverage independently and permits negligible leverage. A5 includes the center-of-rotation case and a crossing deletion. D4 includes both same-side knee relationships for the four bilateral muscle pairs and preserves standalone hip loading. The D-062 findings below concern how the new checks would run. [D-062 items 5–7, A4–A5](https://github.com/Corb1nW/Independent-Study/blob/551efea2279dd2fe89610e50752de41acf173d1b/docs/DECISIONS.md#L2306-L2361) |
| D061-B02 | Main changes resolved. One deferred wording issue | D6 separates article and dataset terms, conditions public vendoring, and ties validation claims to preregistered results. Joint moments are compared with published inverse-dynamics estimates. The Wang source row says terms pending. The D6 outlook risk row still says the alternative needs permission. Use “verify terms for both candidates” there when maintaining the outlook. This does not block D4. [D6](https://github.com/Corb1nW/Independent-Study/blob/551efea2279dd2fe89610e50752de41acf173d1b/docs/plans/2026-11-11_squat_proof_of_concept_plan.md#L91-L114) · [Risk row](https://github.com/Corb1nW/Independent-Study/blob/551efea2279dd2fe89610e50752de41acf173d1b/docs/plans/2026-11-11_squat_proof_of_concept_plan.md#L204-L211) · [Sources](https://github.com/Corb1nW/Independent-Study/blob/551efea2279dd2fe89610e50752de41acf173d1b/sources/SOURCES.md#L44-L47) |
| D061-B03 | Resolved | Amendment 1 withdraws P4's tiers and keeps the D-047/D-051 documentation boundary and execution checks for changed behavior. [D-061 Amendment 1](https://github.com/Corb1nW/Independent-Study/blob/551efea2279dd2fe89610e50752de41acf173d1b/docs/DECISIONS.md#L2229-L2249) |

## Blocking findings in D-062

### D062-B01 · High · Scientific verification · C3 versus A1–A4

C3 compares the sign of a material moment arm to the anatomical capability. The current gastrocnemius entry declares knee flexion. I ran the accepted fixed and moving knee paths at all 301 poses for each body. In the fixed variant, `lat_gas_r` has an extension moment arm of at least 1 mm in magnitude at 49 poses for every body. I independently queried OpenSim 4.6 on the matched Gait2392 models. At pose 150 it gives **−3.085149 mm with the fixed knee** and **+10.385203 mm with the moving knee** in the project's flexion-positive convention. The moving variant passes the proposed sign test on all three bodies. The fixed variant cannot both reproduce the accepted geometry and pass the stated C3 sign rule. [D-062 C3 and A1–A4](https://github.com/Corb1nW/Independent-Study/blob/551efea2279dd2fe89610e50752de41acf173d1b/docs/DECISIONS.md#L2317-L2356) · [Gastrocnemius entry](https://github.com/Corb1nW/Independent-Study/blob/551efea2279dd2fe89610e50752de41acf173d1b/ontology/lower_limb_sagittal.yaml#L498-L525)

**Fix.** Apply the anatomy sign criterion to the moving-knee baseline and its growth variant. For the fixed-knee regression, verify the moment arms against the accepted fixed-knee reference, retain the other consistency checks, and record the reference-confirmed lateral gastrocnemius sign difference as a fixed-knee deviation. Keep the anatomical capability and historical geometry as recorded. Apply magnitude thresholds to `abs(moment_arm)` so both signs enter the checks.

### D062-B02 · High · Scientific verification · A4 bilateral detection

The four bilateral pairs all have the same omission. In the pinned ontology I swapped the sides on `CROSSES` and `ACTS_ON` and compared the sets. All four pairs passed mirror equality before repair. C1, with the hip endpoint resolved, flags exactly the four missing right knee crossings among the 14 modeled actuators. An equality-only mirror test cannot flag the corresponding left gaps as A4 promises. [D-062 item 5 and A4](https://github.com/Corb1nW/Independent-Study/blob/551efea2279dd2fe89610e50752de41acf173d1b/docs/DECISIONS.md#L2306-L2309) · [A4](https://github.com/Corb1nW/Independent-Study/blob/551efea2279dd2fe89610e50752de41acf173d1b/docs/DECISIONS.md#L2356-L2361) · [Merged demo follow-up](https://github.com/Corb1nW/Independent-Study/pull/45)

**Fix.** For these four supported pairs, derive the expected right knee edge from the modeled path and use the evidenced `ACTS_ON` action. Require their side-swapped expectations on the left. A4 must check required edges on each side so it fails when both sides omit an edge. Keep the pairwise mirror check for asymmetric changes.

### D062-B03 · Medium · Assembly · Item 1 hip endpoint

The stated `CONNECTS` → `REPRESENTED_BY` traversal cannot resolve one right hip endpoint. The joint connects `LB:BONE:HIP_BONE_R` to `LB:BONE:FEMUR_R`. The femur has a direct segment mapping. The hip bone has none. The unique `HAS_PART`–`REPRESENTED_BY` route goes through the bony pelvis to `LB:SEG:PELVIS`. The stated traversal alone leaves the hip out of the assembled tree. [D-062 item 1](https://github.com/Corb1nW/Independent-Study/blob/551efea2279dd2fe89610e50752de41acf173d1b/docs/DECISIONS.md#L2281-L2290) · [Bony pelvis and right hip bone](https://github.com/Corb1nW/Independent-Study/blob/551efea2279dd2fe89610e50752de41acf173d1b/ontology/hip.yaml#L97-L128) · [Hip joint](https://github.com/Corb1nW/Independent-Study/blob/551efea2279dd2fe89610e50752de41acf173d1b/ontology/hip.yaml#L686-L694)

**Fix.** Include a data-driven endpoint resolution rule in D-062. Resolve a direct representation where present, otherwise use a unique containing skeletal complex with a representation, or declare the endpoint mapping explicitly in the model data. Then apply the specified low-back merge into the HAT. Require each retained joint to resolve to two distinct segments and reject unresolved or ambiguous endpoints.

## Execution and sources

Linux x86-64, Python 3.12.14, pytest 9.2.0, NumPy 2.3.5, SciPy 1.17.0, OpenSim 4.6. I verified the detached Git commit and tree `e5d7e4f2e1b1536cd89291819c0239accf89e417`. The sparse checkout omitted the unrelated phase-overview PDF. The worktree was clean before and after.

| Check | Result |
|---|---|
| `python -m pytest -q` | 285 passed in 66.02 s, one AnyIO deprecation warning |
| `python -m src.integrity` | Passed |
| `python tools/review_cycle1_probes.py` | 9/9 invalid probes rejected |
| `python -m tools.build_segment_datasets --check` | Passed |
| Reviewer checks on ontology and both knee variants | Reproduced the four right-side topology gaps with the missing endpoint mapped in memory, verified symmetric omissions, and measured the sign differences above |
| Vendored Gait2392 and OpenSim 4.6 growth pre-check | Both new actuators switch on `hip_flexion_r` in the squat. Their conditional points are active at 172 poses and inactive at 129, with switches between samples 85/86 and 214/215 using zero-based indices. Both give positive hip moment arms and no D2 fiber-domain flags in the unscaled matched OpenSim motion. |

For the topology probe I read the two ontology modules, mapped the recorded actuator path-point frames to their segments, and compared the union of joint paths with `CROSSES`. For the sign probe I used the 301 committed pose states and the six existing body/knee combinations. For the OpenSim check I used the repository's matched XML preparation and `computeMomentArm`, with the project's coordinate signs. OpenSim reported missing visualization meshes. These runs checked numerical geometry only. Sources were the pinned ontology, generated datasets, committed pose reference, and vendored Gait2392 model. The two outlook source entries requested in the earlier review are present and marked as cited by Claude. This review adds no external source.

The new assembler and its official D4 and growth runs are still proposed. I did not rerun the official D1–D3 simulations or open the D6 data archives for this documentation amendment. The tests cover the pinned existing code.

Resolve D062-B01 through D062-B03 before deciding D-062. The scoped D4 build and data-only growth experiment fit Q67. Decisions beyond D4 are deferred.

**Status: REVIEWED, NOT APPROVED.**
