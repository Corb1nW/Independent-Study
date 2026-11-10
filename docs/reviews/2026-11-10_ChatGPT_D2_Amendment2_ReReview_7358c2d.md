# Stage D2 Amendment 2 re-review — PR #30 at 7358c2d

Reviewed by (model): ChatGPT\
Built by (model): Claude\
Reviewed SHA (full): `7358c2dbb6af373b477d7c71a14a520a853f36c5`\
PR base SHA: `2f7cf983cb1660ae3f0fb8d08fbe51b69ceabe7e`\
Previous reviewed SHA / comparison base: `936c12c9fe72a128c629a62f6cd67fd367fded7b`\
PR: [#30](https://github.com/Corb1nW/Independent-Study/pull/30), `phase-d/claude-d2-scope`\
Previous review: [PR #32](https://github.com/Corb1nW/Independent-Study/pull/32)\
Date: 2026-11-10\
Record branch: `reviews/chatgpt-d2-amendment2-7358c2d`, from the PR base SHA above

**Verdict: AGREE. No blocking findings. Must fix before Corbin decides: none.**

**Status: REVIEWED, NOT APPROVED.** D-059 is ready for Corbin's decision at the reviewed SHA. This recommendation concerns the scope proposal; it does not approve a D2 implementation or start the build.

## Scope and independence

Corbin explicitly assigned the Reviewer role and limited this round to Amendment 2's L∞ reserve rule (D2-R01) and path-switch policy (D2-R04). A blocker must make the build wrong or the proposal untrue; numerical tolerances, wording, additional fixtures and details settled during implementation are nonblocking. I read the complete `936c12c..7358c2d` diff for regressions without reopening resolved items.

The one new commit changes `docs/DECISIONS.md`, `PROJECT_STATE.md`, `sources/SOURCES.md` and adds an OpenSim run log. No executable project code, tests, configuration, anatomical/model data or vendored source header changed. D-059 remains Proposed, implementation Not started and verification Not checked. The affine-force wording correction is consistent with the already resolved force-law contract.

Claude authored the response. The reserve-first/minimax suggestions and earlier geometry counterexample came from my reviews; their adoption and my mathematical probes are **self-checked**, not an independent verification of my own work. I independently inspected Claude's response within that limitation. Existing ChatGPT-authored Phase B code is also self-checked. Tests of Claude-authored behavior are rerun evidence, not biomechanical validation.

## Earlier findings

| Item | Disposition | Evidence at the reviewed SHA |
|---|---|---|
| D2-R01 | **Resolved at proposal level** | `docs/DECISIONS.md:1770–1785`: LP minimizes maximum absolute per-joint reserve; strictly convex stage 2 chooses effort within the optimum band; the feasibility flag uses stage-1 `t*`. |
| D2-R04 | **Resolved at proposal level** | `:1787–1799`, `:1807`: jumps disclosed; inclusive active-point selection; branch velocity; no differences/interpolation across switches or smoothing; left/right length, moment arm and force checks; simplification 15. |
| D2-R02, D2-R03, L01, L02, source registration | **Remain closed at proposal level** | Complete diff contains no regression in those contracts. Amendment 2 preserves the earlier checks and strengthens their transition scope. No new source is introduced. |

## D2-R01: method and certificate

Let `C` be the fixed in-domain torque map at one sample. Stage 1 computes

`t* = min_{0 <= a <= 1} ||tau - C a||_infinity`.

The activation box is compact and the objective is continuous, so an optimum exists. Its scalar value is unique even when several activation patterns attain it. Replacing each absolute-value bound by two linear inequalities gives the stated LP. Consequently, `t* <= 1 N·m` is equivalent to existence of a bounded activation pattern keeping **every** joint's reserve within that allowance. The claim is limited to the specified retained actuators, force law, geometry and sample.

The second-stage feasible set is nonempty and convex; squared activation is strictly convex, so its minimizing activation is unique. Allowing the numerical band `delta` is implementable. Stage-2 reserves need not individually be the smallest possible; Amendment 2 now expressly discloses this.

**Executed check:** the earlier counterexample has `r1 = 2.95 - 4a`, `r2 = 0.45 + a`. For every `a`, `r1 + 4r2 = 4.75`, hence `max(|r1|, |r2|) >= 0.95`. At `a = 0.5`, both reserves are 0.95 N·m: the minimum is exactly **0.95 N·m**, so the new rule correctly passes. My separately written LP calculation agrees. The 14-actuator example gives `t* = 0`; an unavoidable negative reserve of −2 N·m correctly flags. These are mathematical fixtures, not Gait2392 capacity results.

The existing proposal's KKT checks for both stages, bounds and equality checks, and second solver can detect a real optimizer error under the amended method. Solver selection and detailed test tolerances belong in the build.

## D2-R04: transition policy

The proposal now treats source path geometry as piecewise smooth branches separated by disclosed length jumps. It chooses length and moment arms from the inclusive active-point set at each sample and uses that branch's `Ldot = -sum(R_j qdot_j)`. It makes no ordinary derivative claim through a jump. This is a coherent, implementable modeling convention; the physical discontinuity is retained as an explicit simplification.

The amended oracle checks both sides of each widened-range edge, including length, moment arm and tendon force. Derivative and virtual-work checks apply within branches. These checks can catch wrong branch selection, sign/geometry errors and incorrect force evaluation without demanding continuity that the source lacks.

**Executed policy check:** a source-point evaluator on D1's sagittal frames reproduces the gastrocnemius jumps: **0.353869314 mm medial**, **0.031044826 mm lateral** at D1 knee angle 0.785408 rad. Inclusive branch selection is consistent at the edge, and velocities computed from fixed-branch length gradients agree with fixed-branch directional derivatives. This checks the policy's meaning; it is **not an OpenSim run** or the future oracle.

Claude's eight unmodified-model OpenSim jump magnitudes remain **builder-reported**. They need not equal the D1-frame numbers above. The proposal already leaves actual D1-matched-copy values and per-body force effects to the build.

## Nonblocking note for the build

**D2-A2-N01 / Low / numerical reporting** — `docs/DECISIONS.md:1775–1778,1796`.

The written stage-2 band is `t* + delta`, so “without reserves,” “never above t*” and the ideal fixture activations should be read to numerical tolerance. My execution with `delta = 1e-6 N·m` gives `a = 0.49999975`, reserves approximately `(0.950001, 0.94999975)` for the two-joint fixture; the 14-actuator case leaves approximately 1e-6 N·m reserve. This is the stated relaxation, not a failure of the stage-1 certificate.

**Build follow-through:** report `t*`, actual signed stage-2 reserves and numerical tolerance separately; retain the distinction between the 1 N·m demonstration allowance and solver accuracy. Review boundary behavior when code exists. No tolerance change, extra fixture list or proposal amendment is required for this verdict.

## Ran, environment and limits

A hash-checked shallow/sparse Git checkout had exact HEAD `7358c2dbb6af373b477d7c71a14a520a853f36c5` and tree `e4be3254765afe297e5bd8786efa7a11236d5791`; working status was clean before and after. The unrelated binary phase-overview PDF is excluded as in the previous review; this is not a full binary-repository verification.

Environment: CPython 3.12.14, Linux x86_64/glibc 2.41; NumPy 2.3.5, pydantic 2.13.4/core 2.46.4, PyYAML 6.0.3, pytest 9.2.0, Pint 0.26.2, SymPy 1.14.0. Review-only numerical probes used SciPy 1.17.0; this does not select the build's solver. Existing review virtual environment; `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_NOSYSTEM=1`.

| Command | Result |
|---|---|
| `python -m pytest -q` | Exit 0; **178 passed**, one installed anyio/pytest deprecation warning, 35.21 s |
| `python -m src.integrity` | Exit 0; **PASSED** |
| `python tools/review_cycle1_probes.py` | Exit 0; **9/9 REJECTED** |
| `python -m tools.build_segment_datasets --check` | Exit 0; datasets current |
| `.../d1-env/bin/python d2-amendment2-7358c2d/scope_probes.py` from the workspace | Exit 0; reserve and branch-policy checks above; complete executed source below |

**Read or reasoned only:** amended LP/QP existence, uniqueness and certificate; transition/verification contract; full diff, handoff, source registry and applicable accepted process decisions (D-044–D-048, D-051, D-054, D-057).

**Not run, and why:** no D2 code exists; OpenSim is not installed in this environment. No OpenSim oracle, complete muscle build, new physiological validation or Windows execution is claimed. The 178 existing tests are regression evidence, not verification of unbuilt D2.

**Sources checked:** existing registry entries for the Gait2392 source, pinned OpenSim source and OpenSim 4.6; Amendment 2 adds a use to the existing software row. Source-point geometry uses the unchanged vendored model and D1 joint dataset. No new external source is cited or needs registration.

**Out-of-scope observations:** the added `sources/vendor/opensim-models/opensim.log` is an operational log, not changed model data. Its retention is nonblocking. Closed reviews, owner quotes, force-law constants, original scope sizing and D1 close-out were not reopened.

**Handoff:** Corbin decides D-059 at the reviewed SHA. If approved, Claude builds Stage D2 under that scope, carries N01 into numerical reporting and the build review, and executes the already proposed oracle/optimizer checks. No further scope re-review is needed on the issues assessed here.

**Must fix before Corbin decides: none. Verdict: AGREE. Status: REVIEWED, NOT APPROVED.**

<details>
<summary>Executed review probe source (self-authored; not project implementation)</summary>

```python
"""Review probes for D-059 Amendment 2; not the future D2 implementation."""
from fractions import Fraction as F
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
from scipy.optimize import linprog, minimize
import yaml

ROOT = Path(__file__).parent
REPO = ROOT / 'repo'
report = {}


def hierarchy(C, tau):
    C, tau = np.asarray(C, float), np.asarray(tau, float)
    m, n = C.shape
    # Eliminate r = tau - C*a; t bounds both residual signs.
    A = np.vstack((np.column_stack((-C, -np.ones(m))),
                   np.column_stack((C, -np.ones(m)))))
    b = np.r_[-tau, tau]
    lp = linprog(np.r_[np.zeros(n), 1.], A_ub=A, b_ub=b,
                 bounds=[(0., 1.)] * n + [(0., None)], method='highs')
    assert lp.success, lp.message
    t = lp.x[-1]
    delta = 1e-6
    band = t + delta
    qp = minimize(lambda a: a @ a, lp.x[:-1], jac=lambda a: 2*a,
                  bounds=[(0., 1.)] * n,
                  constraints={'type': 'ineq',
                      'fun': lambda a: np.r_[band-tau+C@a, band+tau-C@a],
                      'jac': lambda a: np.vstack((C, -C))},
                  method='SLSQP', options={'ftol': 1e-12, 'maxiter': 200})
    assert qp.success, qp.message
    r = tau - C @ qp.x
    assert np.max(np.abs(r)) <= band + 1e-9
    return {'t_star_N_m': float(t), 'feasible_at_1_N_m': bool(t <= 1.),
            'stage2_activation': qp.x.tolist(), 'stage2_reserve_N_m': r.tolist(),
            'stage2_numerical_band_N_m': float(band)}


# Exact lower bound: r1 + 4*r2 = 19/4, hence 5*max|r| >= 19/4.
# a=1/2 attains r1=r2=19/20, proving the minimax optimum without a solver.
C = (F(4), F(-1))
tau = (F(59, 20), F(9, 20))
a = F(1, 2)
r = tuple(t-c*a for t, c in zip(tau, C))
assert r == (F(19, 20), F(19, 20))
assert tau[0] + 4*tau[1] == 5*F(19, 20)
report['two_joint'] = hierarchy([[4], [-1]], [2.95, .45])
assert abs(report['two_joint']['t_star_N_m'] - .95) < 1e-12
assert report['two_joint']['feasible_at_1_N_m']

report['fourteen_actuator'] = hierarchy([[.1] * 14], [1.4])
assert abs(report['fourteen_actuator']['t_star_N_m']) < 1e-12
assert min(report['fourteen_actuator']['stage2_activation']) > .99999

# No retained actuator torque: the largest signed deficit is unavoidable.
report['signed_shortfall'] = hierarchy([[0], [0]], [-2, .5])
assert report['signed_shortfall']['t_star_N_m'] == 2.
assert not report['signed_shortfall']['feasible_at_1_N_m']

# Reuse source point data, but independently write a branch length evaluator.
# This checks transition semantics on D1's sagittal frames, not OpenSim values.
xml = ET.parse(REPO/'sources/vendor/opensim-models/gait2392_millard2012muscle.osim').getroot()
obs = yaml.safe_load((REPO/'ontology/quantitative_data/segments_gait2392.yaml').read_text())['observations']
def j(name):
    return np.asarray(obs['LB-QD:G2392:JOINT:'+name]['value'], float)
def rot(q):
    return np.array([[math.cos(q), -math.sin(q), 0.],
                     [math.sin(q), math.cos(q), 0.], [0., 0., 1.]])
def point(p, qa, qk):
    x = np.fromstring(p.findtext('location'), sep=' ')
    frame = p.findtext('socket_parent_frame')
    if frame == '/bodyset/femur_r':
        return rot(qk) @ (x-j('KNEE_R'))
    if frame == '/bodyset/calcn_r':
        return j('ANKLE_R') + rot(qa) @ (j('SUBTALAR_R')+x)
    raise ValueError(frame)

paths = []
for name in ('med_gas_r', 'lat_gas_r'):
    muscle = next(m for m in xml.findall('.//Millard2012EquilibriumMuscle') if m.get('name') == name)
    p1, p2, p3 = muscle.find('.//PathPointSet/objects')
    lo, hi = map(float, p2.findtext('range').split())
    edge = -lo + 1e-5
    def active(qk):
        return lo-1e-5 <= -qk <= hi+1e-5
    def length(qa, qk, included):
        u, v, w = (point(p, qa, qk) for p in (p1, p2, p3))
        return np.linalg.norm(u-v)+np.linalg.norm(v-w) if included else np.linalg.norm(u-w)
    assert active(edge) and active(edge-1e-8) and not active(edge+1e-8)
    qa = .4*edge
    jump = length(qa, edge, True)-length(qa, edge, False)
    assert jump > 0.
    velocities = []
    # Differentiate only a fixed point set; no difference crosses a switch.
    for included in (True, False):
        h = 1e-6
        gradient = np.array([(length(qa+h, edge, included)-length(qa-h, edge, included))/(2*h),
                             (length(qa, edge+h, included)-length(qa, edge-h, included))/(2*h)])
        moment_arm = -gradient
        qdot = np.array([.2, .5])
        velocity = -moment_arm @ qdot
        directional = (length(qa+h*qdot[0], edge+h*qdot[1], included)
                      -length(qa-h*qdot[0], edge-h*qdot[1], included))/(2*h)
        assert abs(velocity-directional) < 1e-9
        velocities.append(float(velocity))
    paths.append({'actuator': name, 'switch_D1_knee_rad': edge,
                  'jump_m': float(jump), 'branch_velocities_m_per_s': velocities})
report['transition_semantics'] = paths
report['limitations'] = 'Own math and D1-frame geometry only; no OpenSim run and no D2 build exists.'
(ROOT/'out/scope_probes.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
print(json.dumps(report, indent=2, sort_keys=True))
```

</details>
