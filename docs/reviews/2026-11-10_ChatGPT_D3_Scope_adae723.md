# Stage D3 scope review — D-060, PR #39

Reviewed by (model): ChatGPT\
Built/proposed by (model): Claude\
Review date: 2026-11-10\
Reviewed SHA (full): `adae7238cfbd5d1c70f3a239378df3e73d6017e1`\
Base SHA / review-record base: `c227793962719a38c95775d946a6e09a5dfd9ef1`\
PR: [#39](https://github.com/Corb1nW/Independent-Study/pull/39), `phase-d/claude-d3-scope`\
Record branch: `reviews/chatgpt-d3-scope-adae723`

**Verdict: AGREE on the scope, with two nonblocking build/records notes. No blocking findings. Must fix before Corbin decides: none.**

**Status: REVIEWED, NOT APPROVED.** D-060 is ready for Corbin's decision. The preliminary D3 dynamics/feasibility figures are author-reported estimates, not results established by this review.

## Scope, authority and independence

Corbin asked me to check Claude's new proposal in the continuing Reviewer role. I read the Reviewer instructions, the handoff, D-060, its cited accepted decisions and the complete diff: one commit changes only `docs/DECISIONS.md` and `PROJECT_STATE.md`. No code, source data, schema or tests changed. D-060 remains Proposed, implementation Not started, verification Not checked.

This is a scope review under Corbin's instruction to reserve AMEND for material errors in the build contract. Routine implementation choices, extra fixtures and wording/estimate refinements remain nonblocking. Earlier D2 findings are closed and were not reopened.

Claude wrote D-060. The earlier knee-only OpenSim sweep referenced in its motivation is my own work, so that part is self-checked, not independently reverified here. The new source-geometry and virtual-work probes are also self-authored/self-checked. I independently inspected Claude's proposal and executed the existing Claude-authored software within the inherited qualifications for ChatGPT-authored regressions.

The A-15/Q61 records are consistent with the reviewed PR history and prior review records. This review does not authenticate an unseen original Claude-session quotation or treat my AGREE as owner approval.

## Assessment of the proposal

**The stage is right-sized and tests the intended explanation.** One prescribed knee coordinate acquires the source model's translations; ankle/foot simplifications, muscle set, force law, recruitment, body properties and prescribed motion remain controlled. Updating both inverse dynamics and muscle geometry corrects the earlier mixed-geometry sensitivity comparison. A broader contact knee or patella model is not required for this question.

**The mechanics plan contains the essential term.** A coupled knee coordinate does translational as well as rotational work. Projecting the joint wrench onto the allowed virtual motion includes `F dot dT/dq_knee`, with `dT/dq_knee = -dT/dtheta` for `theta = -q_knee`; the complete sign follows the chosen side of the joint wrench. D-060 explicitly includes that term in Newton–Euler and uses analytic spline Jacobians for Kane's method. It also fixes inertial properties in body frames, avoiding a pose-dependent change in segment mass distribution.

The plan is implementable: partial velocities/Jacobians give the generalized inertial forces and mass matrix; spline derivatives supply translation velocities and accelerations. Retaining the same coupled kinematics in muscle length derivatives makes generalized muscle torque and generalized mechanical demand compatible. The D-059 force law and reserve rule can be reused.

**Verification is sufficient at proposal level.** The OpenSim copy keeps the source knee while applying the stated D1 ankle/foot changes. Comparing positions in a common foot frame, muscle lengths/moment arms/forces, two dynamics formulations, virtual-work gravity, energy rate, ground-force identity, mass bookkeeping and forward consistency provides checks for real geometry, sign, inertia and force-projection errors. Exact derivative implementations, tolerances beyond the stated inherited contract, solver choices and reference-file layout belong in the build.

**The outcome remains falsifiable.** The exit criterion requires verified computation and reported contact/muscle feasibility; it does not require t* = 0 or a chosen improvement. Comparing torques, centre of pressure, reserves and activations against the unchanged official D1/D2 runs is the right analysis even if a body remains flagged. A single-commit manifest/comparison/page preserves traceability.

**Scope/data/source treatment is appropriate.** Function-form knee data are generated from the retained model; the old fixed observation remains. Proposed schema 0.8.0 is a narrow extension of the existing function representation. The splines are labeled computational model coupling, not measured patient motion. The provenance-origin task and existing de Leva limitations stay explicit.

## Nonblocking notes for the build

### D3-N01 — Low: correct the preliminary translation description

**Location:** `docs/DECISIONS.md:1929` (“about 6 mm anteriorly and 14 mm inferiorly”).

I evaluated the retained knee splines and checked the tibia origin in the femur frame directly with OpenSim 4.6 at 0°, 30°, 60° and 100°. The source SimmSpline values and OpenSim positions agree within **5.3e-18 m** in these checks.

| Knee flexion | Tibia-origin x (m) | Tibia-origin y (m) |
|---:|---:|---:|
| 0° | −0.004499856518 | −0.395820696448 |
| 100° | 0.001790007695 | −0.416941516214 |

The endpoint change is **+6.289864 mm anterior and −21.120820 mm inferior**. Correct the pre-check description to approximately **6.3 mm anterior and 21.1 mm inferior**.

This is nonblocking because item 1 defines the build by the actual retained splines and the OpenSim oracle, not by the preliminary displacement estimate. The scalar-description correction changes no method, source choice or acceptance criterion. It can accompany the build records; no additional scope-review round is requested.

### D3-N02 — Low: distinguish the historical fixed centre from smooth T(0)

**Location:** D-060 items 1/2/6 (`:1936–1945`); existing `tools/build_segment_datasets.py:155–184` and `src/squat_d1.py:141–218`.

D1 deliberately used **linear interpolation** between source knots for its fixed observation. It is not exactly the smooth spline's zero-angle value:

- historical D1 fixed centre: `(-0.004098264724626691, -0.39590120267799883, 0)` m;
- smooth source T(0): `(-0.004499856517536013, -0.39582069644835033, 0)` m;
- difference: **−0.401592 mm horizontally, +0.080506 mm vertically**.

For a frozen-knee regression against historical D1, freeze at the **existing D1 datum**, not silently at the new T(0). The proposal already preserves that datum. A separate T(0)-frozen comparison can isolate the interpolation-offset contribution if useful; it is optional.

D1 stores segment quantities in frames based on their lower joint. In D3, convert the historical thigh COM to a fixed femur frame once before applying a moving joint origin, so item 1's fixed body properties are honored. In particular, do not rebuild de Leva COMs/inertias from a different instantaneous thigh length at each pose. This is build follow-through on the existing rigid-body requirement, not an additional modeling stage or a required proposal amendment.

## Ran, with environment and results

Exact hash-checked HEAD `adae7238cfbd5d1c70f3a239378df3e73d6017e1`, tree `57070663deb5ccd5e484735d4ebe1237f4435349`; working status clean before and after. The same shallow/sparse limitation as earlier reviews excludes the unrelated binary phase-overview PDF; full binary-repository verification is not claimed.

Environment: CPython 3.12.14, Linux x86_64/glibc 2.41; NumPy 2.3.5, SciPy 1.17.0, quadprog 0.1.14, Clarabel 0.11.1, OpenSim 4.6, pydantic 2.13.4/core 2.46.4, pytest 9.2.0, PyYAML 6.0.3, Pint 0.26.2, SymPy 1.14.0. Git configuration isolated with `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_NOSYSTEM=1`.

| Executed check | Result |
|---|---|
| `python -m pytest -q` | **240 passed**, exit 0, 44.86 s; one installed anyio/pytest deprecation warning |
| `python -m src.integrity` | **PASSED**, exit 0 |
| `python tools/review_cycle1_probes.py` | **9/9 REJECTED**, exit 0 |
| `python -m tools.build_segment_datasets --check` | Datasets current, exit 0 |
| Own `scope_probes.py` using OpenSim 4.6 and the retained source | Exit 0; four source-geometry comparisons, source-domain check and translational virtual-work fixture |

The virtual-work fixture uses explicitly artificial force `(100, -300, 0)` N at 60° flexion and qdot = 0.7 rad/s. The spline derivative gives an additional generalized-force contribution **4.804983 N·m**, and power **3.363488 W**, matching finite differentiation/power projection. These are mathematical check values, not measured anatomy or a D3 dynamics run.

**Read/reasoned only:** D-060's two-formulation mechanics/verification plan, source and schema choices, scope and handoff. **Not run:** the uncommitted Kane prototype, its torque/COP/reserve pre-check figures, a D3 implementation, new D3 muscle recruitment, forward runs or page rendering. The existing tests are regression evidence only. In particular, the proposed all-three-body t* = 0 result remains **reported by Claude** and must be established in the build.

**Sources checked:** existing `SRC:GAIT2392_OSIM` source model, source joint transforms/knots and credits, generated knee datum, D1 body construction and the already-reviewed SimmSpline port; OpenSim 4.6 is already registered. No new external research source is cited or needs registration. The origin of the model's coupling remains D-060 open concern 1; checking the source function is not verification of its original experimental basis.

New blocking findings: **none**. Earlier D2 findings: remain closed. Out-of-scope observations: none requiring action. Physiological/clinical validity remains unestablished.

**Handoff:** Corbin decides D-060 at this SHA. If approved, Claude builds Stage D3, carries N01/N02 into the build records/tests, and demonstrates the stated mechanics, oracle and comparison checks. ChatGPT reviews the implementation at a new exact SHA.

**Verdict: AGREE on scope. Must fix before Corbin decides: none. Status: REVIEWED, NOT APPROVED.**

Evidence: [commands and source/math probe results](evidence/d3_scope_adae723/execution_evidence.json), [executed scope-probe source](evidence/d3_scope_adae723/scope_probes.py). The probe uses the execution layout `<review-dir>/repo` and `<review-dir>/out`; place it in `<review-dir>` to rerun.
