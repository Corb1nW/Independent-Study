# Stage D2 scope re-review — PR #30 at 936c12c

Reviewed by (model): ChatGPT\
Built by (model): Claude\
Reviewed SHA (full): `936c12c9fe72a128c629a62f6cd67fd367fded7b`\
PR base SHA: `2f7cf983cb1660ae3f0fb8d08fbe51b69ceabe7e`\
Previous reviewed SHA: `a3efd33329cae0c92f7266d726ba64ef05992782`\
PR: [#30](https://github.com/Corb1nW/Independent-Study/pull/30), `phase-d/claude-d2-scope`\
Previous review: [PR #31](https://github.com/Corb1nW/Independent-Study/pull/31), record commit `ffbe58b99b528ca1e5f7b3b909c85923b798f655`\
Review date: 2026-11-10\
Record branch: `reviews/chatgpt-d2-rereview-936c12c` (from the PR base/main SHA above)

**Verdict: AMEND.** The response resolves the force-law/default contract and expands the verification plan as requested. The reserve-first hierarchy is valid and fixes the original soft-cost counterexample. Two focused amendments remain: qualify the reserve certificate's norm relative to its per-joint allowance, and replace the unsupported claim of continuous conditional muscle-path lengths with an explicit transition policy. The method and 14-actuator scope can be retained.

**Status: REVIEWED, NOT APPROVED**

## Scope, authority and independence

Corbin requested a re-review of Claude's response in the ongoing Independent Study Reviewer role. I reread the supplied Reviewer instructions, the full PR response and the entire `a3efd33..936c12c` diff: one commit, three changed record files (`PROJECT_STATE.md`, `docs/DECISIONS.md`, `sources/SOURCES.md`). No implementation, tests, configuration, model data, source header or role skill changed.

I applied the accepted review/verification/decision rules and read D-059 with its full Amendment 1, its acceptance criteria, and the current source registry. D-059 remains Proposed; no D2 implementation or new owner approval is inferred.

Claude wrote the response. The original review suggestions and copied hand-fixture values are my own earlier work, so checking their incorporation is partly self-check. Inherited ChatGPT code in the existing regression suite is also self-checked. I independently inspected the response and its new source citation; my mathematical/point-distance probes and this review are self-authored/self-checked. The probes are not an OpenSim execution, a D2 implementation or scientific validation.

## Disposition of the earlier findings

| Earlier item | Disposition at this SHA | Evidence |
|---|---|---|
| D2-R01, reserve semantics | **Partly resolved** | Amendment 1 items 1/3 use a valid reserve-first hierarchy, signed absolute reserves, separate 1 N·m demonstration allowance and 1e-6 N·m numerical tolerance. The old 14-actuator case now has reserve zero. The remaining per-joint-margin certificate issue is detailed below. |
| D2-R02, complete force-law/domain/default contract | **Resolved at proposal level** | :1728–1735 state positive-projection geometry, fiber velocity/sign/normalization, domain checks, nonfinite failure, flagged exclusion, explicit damping 0 and inherited-value resets, and controlled passive/compliant comparisons. |
| D2-R03, assembled force and boundary verification | **Resolved as requested at proposal level** | :1739–1749 add complete force/intermediates, activation/velocity cases, KKT/bounds for both stages, independent solver, source-derived switch coverage and oracle provenance. The newly asserted path continuity introduces D2-R04 below. |
| L01, simplifications/exclusion rationale | **Resolved** | :1751–1756 add zero damping, domain exclusion, ideal-constraint/reaction limitations and shared generic strengths; the short-head exclusion is properly qualified. |
| L02, instantaneous versus quasi-static wording | **Resolved** | :1721 explicitly retains D1's inertial demand while solving recruitment independently at each instant. |
| Source registration requested by the first review | **Resolved** | `sources/SOURCES.md` now lists *Working with Static Optimization* as Read and expands the pinned source-code uses, distinguishing files read by ChatGPT from those read by Claude. |

These are assessments of the proposed build contract. No D2 solver or force-law implementation exists to execute yet.

## D2-R01 — Medium, still open in part: the reserve certificate needs a norm-consistent interpretation

**Location:** `docs/DECISIONS.md:1722–1726`, especially the claim that a flagged result certifies a shortfall by the 1 N·m margin; :1758, alternative (h).

The following parts of the response are correct:

- With a fixed linear torque map and bounded activations, the achievable torque set is compact and convex. The minimum-`sum(r_j^2)` reserve vector is unique.
- That vector is zero exactly when the demand can be met with muscles alone, subject to the stated domain policy and numerical tolerance.
- Holding the vector fixed and minimizing `sum(a_i^2)` gives a unique second-stage activation vector.
- Giving reserves priority removes the earlier effort-versus-assistance trade-off. The original 14-actuator counterexample is resolved.

However, **minimizing the sum of squared reserves does not minimize the largest absolute joint reserve**. Applying a maximum-component allowance afterward gives a defined policy screen, but a flag is not proof that every activation choice violates that per-joint allowance.

**Executed exact-arithmetic counterexample** (a mathematical fixture, not a Gait2392 result):

```text
One activation: 0 <= a <= 1
Muscle torque vector C*a, with C = (4, -1) N·m
Demand tau = (2.95, 0.45) N·m
Reserve r = tau - C*a
Per-joint demonstration allowance = 1 N·m
```

| Choice | Activation | Reserves (N·m) | Maximum absolute reserve |
|---|---:|---|---:|
| Unique minimum squared-reserve solution | 227/340 = 0.667647058824 | (19/68, 19/17) = (0.279411764706, 1.117647058824) | 1.117647058824 — flagged |
| A bounded activation meeting both allowances | 0.5 | (0.95, 0.95) | 0.95 — within allowance |

The first point satisfies the exact interior stationarity condition `C dot r = 0` and has smaller squared-reserve objective (1.327205882353 versus 1.805). Thus this is not a solver failure or an activation-cost trade-off. The flagged minimum-L2 result can coexist with a solution that needs less than 1 N·m at every joint.

A nonzero minimum-L2 residual certifies **failure of exact matching**, and its L2 norm is the minimum Euclidean torque error. Those are valid claims. The componentwise 1 N·m gate does not additionally certify that no activation vector meets that componentwise allowance. A passing gate supplies a witness; a flag can be conservative.

**Proposed fix:** keep the two-stage minimum-L2 rule if that is the intended policy, but explicitly describe the flag as the maximum component of the minimum-L2 residual and restrict the margin certificate to its Euclidean norm. Remove the implication that it is a necessary-and-sufficient per-joint-allowance test.

If Corbin instead wants the 1 N·m-per-joint decision to be an actual bounded-deficit feasibility certificate, use a matching feasibility/max-absolute-deficit calculation. Stage 1's optimum scalar under an L-infinity objective is unique even if its activation/reserve vector is not; minimizing squared activation over the first-stage optimal set can provide the final unique solution. Nonuniqueness of the first-stage vector alone is not a reason the two-stage pipeline cannot be used.

Add the two-joint fixture above to the proposed checks, and label the selected norm/policy in the manifest. No change back to soft reserves is requested.

**Clarification of my earlier guidance:** my option to prioritize reserves was valid and Claude followed it. My earlier wording did not fully distinguish the norm used for that priority from the norm used for an allowance certificate. This re-review makes that distinction explicit; it does not withdraw the reserve-first recommendation.

## D2-R04 — Medium, new: conditional activation does not guarantee continuous path length

**Location:** `docs/DECISIONS.md:1737` (“`L(q)` is continuous but its derivative may jump”), related checks :1740–1741 and the simplifications list.

Claude's source check of the activity convention is correct. At [opensim-core `01683ac`, `ConditionalPathPoint.cpp:160–168`](https://github.com/opensim-org/opensim-core/blob/01683ac33568a3cb5eef2e445c7815f8220e8905/OpenSim/Simulation/Model/ConditionalPathPoint.cpp#L160), a point is active over its range expanded by 1e-5 on each side. That is a boolean inclusion rule, not a continuity construction.

Inserting a via point preserves the sum-of-segment-distances length only when that point lies exactly on the line segment between its active neighbours. The source rule alone does not ensure this, especially after imposing D1's simplified joints.

**Executed point-distance check:** I read the retained Gait2392 points and joint-position dataset, and used the proposed D1 frame definitions without any OpenSim or project kinematics import. For the Gait2392 body at the gastrocnemius switch:

- effective D1 knee angle is **0.785408 rad** (the source's −0.785398 lower range, including the 1e-5 band);
- D1 ankle angle is **0.3141632 rad**, from its common profile and 40/100 depth-angle ratio;
- P1 and conditional P2 are both in the **femur** frame; P3 is in the **calcaneus** frame;
- knee position is frozen at its D1 zero-angle value, ankle rotates about z, and subtalar is locked.

The two limiting active-point configurations at this same pose give:

| Actuator | Length with via point (m) | Length without via point (m) | Difference (mm) |
|---|---:|---:|---:|
| `med_gas_r` | 0.449212741222 | 0.448858871908 | 0.353869314 |
| `lat_gas_r` | 0.445430559146 | 0.445399514320 | 0.031044826 |

Evaluating on both sides with angular offsets 1e-6, 1e-8 and 1e-10 rad converges to these **nonzero** jumps. For `med_gas_r`, the last left-minus-right result is 0.000353869313123645 m. I also recomputed the distances in the fixed-foot world frame using D1's segment-origin/absolute-angle equations; both coordinate-frame calculations agree within 1e-14 m.

This is a direct geometric calculation on the **proposed D1-matched frames**, not an observed OpenSim run or a completed D2 result. It is enough to contradict the universal continuity assertion; the build's independent OpenSim fixture should confirm and quantify the behavior.

**Problem:** a path-length jump is different from a continuous path with a derivative kink. At the jump, a finite ordinary `dL/dt` is not defined. Reporting a finite branch velocity or a virtual-work identity away from the switch does not establish a globally differentiable, continuous muscle path.

**Proposed fix:** remove the unconditional continuity claim. Extend the proposed oracle check to measure left/right **length as well as moment-arm/force values at the effective expanded-range boundaries**, and declare the observed jumps as a model simplification. State the velocity/force reporting policy at those transitions and the scope of one-sided derivative/power tests; do not assert an ordinary derivative at a discontinuity. If smoothing is introduced, name and record it as an additional model assumption instead of silently changing the source path.

This can be resolved by an honest boundary/applicability policy and reported jump sizes; adding muscles, compliant-tendon trajectories or forward control is not required.

## What now works in the response

The complete baseline law, positive lengthening convention and normalized fiber velocity are coherent. Zero damping and conversion resets prevent the inherited Millard damping from silently changing the baseline. The separate `force_law_domain` flag makes domain exclusions visible; feasibility statements must refer to the retained in-domain actuator set, as the amendment describes.

In the passive-on case, the force law is **affine** in activation with a known passive offset. Moving that offset to the right-hand side keeps the stated convex optimization structure; this is consistent with the method despite the phrase “no longer linear.” The bottom-pose compliant comparison now holds activation and path length fixed and reports equilibrium/domain diagnostics.

The assembled-force oracle, source-derived path switches, property overrides, units/hashes and explicit failure statuses are a substantial improvement and remain appropriately scoped. Ordinary tests can consume committed reference data; a future independent OpenSim rerun is still needed to verify the build.

The vendored header is unchanged, with SHA-256 `c430bfc2a69996e6eb5700ea6bd7bc80fcd5ea9bfc6b234e23f05dc7bd8ff3e6`. The original curve landmarks and hand force fixtures reproduced again. No curve-constant correction is requested.

## Ran, with environment and results

At exact HEAD `936c12c9fe72a128c629a62f6cd67fd367fded7b`, with clean tracked/index state before and after:

| Command | Exit | Observed result |
|---|---:|---|
| `python -m pytest -q` | 0 | 178 passed, 1 third-party pytest deprecation warning (34.04 s) |
| `python -m src.integrity` | 0 | PASSED |
| `python tools/review_cycle1_probes.py` | 0 | 9/9 negative probes REJECTED |
| `python -m tools.build_segment_datasets --check` | 0 | current (exit 0, no stdout) |
| `python .../original_review_probes.py` | 0 | Previous header/force/velocity fixtures and source switch inventory reproduced. |
| `python .../rereview_probes.py` | 0 | Exact reserve-metric counterexample; old toy resolved by the hierarchy; direct conditional-path length/jump and frame-invariance checks. |

Environment: CPython **3.12.14**, Linux x86_64/glibc **2.41**, NumPy **2.3.5**, pydantic **2.13.4** / core **2.46.4**, pytest **9.2.0**, PyYAML **6.0.3**, SymPy **1.14.0**, Pint **0.26.2**. These versions were observed afresh, not copied from the prior review. `GIT_CONFIG_GLOBAL=/dev/null` and `GIT_CONFIG_NOSYSTEM=1` were set. The pytest warning was an installed anyio plugin's deprecated pytest alias; no project check failed.

I reconstructed the new commit/tree from hash-checked GitHub connector objects on the existing shallow/sparse checkout. Review tree: `b0e403f1d32b546b42905ab41dfdbcb6c830dc07`. The only omitted working-tree file is the unrelated phase-overview PDF, whose binary blob remains unavailable through the connector; checkout emitted the already documented warning for that skipped file. Every source/model/test file used here is present. No full-repository fsck or PDF-content check is claimed.

The regression suite verifies current software, not an unbuilt D2 model. The new small probes are mathematical/source checks and not physiological validation.

## Sources, records and limits

Sources actually checked in this re-review: the exact response/diff and current accepted decision rules; the retained Gait2392 XML, D1 joint-position dataset, D1 motion configuration and frame equations; the unchanged curve header; and the pinned upstream `ConditionalPathPoint.cpp`. All are already represented in `sources/SOURCES.md` or are project records/derived artifacts. No new research-source entry is required by this re-review.

The addition of *Working with Static Optimization* and expanded source-file uses are correct. Attribution now clearly distinguishes what Claude read from what ChatGPT read.

Q53–Q57 and D-056's acceptance record were not changed by this response. The earlier limitation about unavailable original owner messages is neither silently upgraded nor rechecked here. Claude's preliminary 93% capacity and 27 N·m soleus numbers remain author-reported estimates.

**Read or reasoned only:** the two-stage convexity/uniqueness argument, interpretation of the residual norm, proposed domain/exclusion/status policy, oracle sufficiency as an implementation plan and the future compliant comparison. Only the listed source/math probes and current-project commands were executed.

**Not run, and why:** no D2 implementation exists; OpenSim 4.6, the new oracle, recruitment runs, compliant sensitivity and new visualization were not executed. No new primary-paper/PDF, Windows or clinical validation was performed.

**Earlier findings:** D2-R01 partly resolved; D2-R02/R03 resolved at proposal level; L01/L02 resolved; source-registration request resolved. D2-R04 is a new finding against a claim added in the response, not a claim that Claude ignored the earlier geometry request.

**Out-of-scope observations:** none requiring a wider D2 scope. The proposal remains a demonstration under stated assumptions; owner acceptance and merging remain Corbin's decisions.

**Verdict: AMEND** (recommendation; Corbin decides).\
**Must fix before Corbin decides:** D2-R01's norm/certificate qualification and D2-R04's path-continuity/transition policy.\
**Status: REVIEWED, NOT APPROVED**

## Appendix: executed re-review probe

This is my self-authored probe. It uses standard-library exact arithmetic and source point distances, with PyYAML only to read the committed configuration/dataset. It imports no project kinematics, optimization implementation or OpenSim. Adapt `ROOT` to rerun elsewhere.

```python
"""Re-review counterexamples only; no D2 implementation or OpenSim imports."""
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import yaml

ROOT=Path(__file__).parent
REPO=ROOT/'repo'
OUT=ROOT/'out'

# Exact one-actuator, two-joint example distinguishing the L2 projection
# from a componentwise reserve allowance. All torques are N.m.
C=(F(4),F(-1)); demand=(F(59,20),F(9,20))
a_l2=sum(c*t for c,t in zip(C,demand))/sum(c*c for c in C)
r_l2=tuple(t-c*a_l2 for c,t in zip(C,demand))
a_box=F(1,2)
r_box=tuple(t-c*a_box for c,t in zip(C,demand))
assert 0<a_l2<1 and sum(c*r for c,r in zip(C,r_l2))==0
assert max(map(abs,r_l2))>1 and max(map(abs,r_box))<1
report={'reserve_metrics':{
 'C_N_m_per_unit_activation':list(map(float,C)), 'demand_N_m':list(map(float,demand)),
 'activation_L2':float(a_l2), 'reserve_L2_N_m':list(map(float,r_l2)),
 'max_abs_reserve_L2_N_m':float(max(map(abs,r_l2))),
 'squared_L2_reserve':float(sum(r*r for r in r_l2)),
 'feasible_activation_within_allowance':float(a_box),
 'feasible_reserve_within_allowance_N_m':list(map(float,r_box)),
 'squared_reserve_at_feasible_point':float(sum(r*r for r in r_box)),
 'allowance_N_m':1.0}}

# Recheck the old exact-feasibility counterexample under the amended rule.
n=14; k=F(1,10); tau=F(7,5)
assert n*k==tau
report['old_toy_under_hierarchy']={'activation_each':1.,'reserve_N_m':0.}

# Point-distance check on D1's explicitly stated sagittal body frames.
# D1 fixes the knee at its q=0 translation and the foot frame at zero.
# In the tibia frame, a femur point is Rz(q_knee)*(p-knee_translation).
# A calcaneus point is ankle_translation + Rz(q_ankle)*(subtalar+p).
source=REPO/'sources/vendor/opensim-models/gait2392_millard2012muscle.osim'
xml=ET.parse(source).getroot()
observations=yaml.safe_load((REPO/'ontology/quantitative_data/segments_gait2392.yaml').read_text())['observations']
config=yaml.safe_load((REPO/'config/phase_d1_squat.yaml').read_text())
assert config['parameters']['start_angles']['value']==[0.,0.,0.]
depth=config['parameters']['depth_angles']['value']
ankle_knee_ratio=depth[0]/depth[1]
def joint(name): return tuple(map(float,observations['LB-QD:G2392:JOINT:'+name]['value']))
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def rotate(a,p):
    c,s=math.cos(a),math.sin(a)
    return (c*p[0]-s*p[1],s*p[0]+c*p[1],p[2])
def point_in_tibia(point,qk):
    p=tuple(map(float,point.findtext('location').split()))
    frame=point.findtext('socket_parent_frame')
    if frame=='/bodyset/femur_r': return rotate(qk,sub(p,joint('KNEE_R')))
    if frame=='/bodyset/tibia_r': return p
    if frame=='/bodyset/calcn_r': return add(joint('ANKLE_R'),rotate(ankle_knee_ratio*qk,add(joint('SUBTALAR_R'),p)))
    raise ValueError(frame)

cases=[]
for name in ('med_gas_r','lat_gas_r'):
    muscle=next(x for x in xml.findall('.//Millard2012EquilibriumMuscle') if x.get('name')==name)
    p1,p2,p3=list(muscle.find('.//PathPointSet/objects'))
    assert p2.tag=='ConditionalPathPoint'
    assert p2.findtext('socket_coordinate')=='/jointset/knee_r/knee_angle_r'
    lo,hi=map(float,p2.findtext('range').split())
    q_boundary=-lo+1e-5
    points=[point_in_tibia(p,q_boundary) for p in (p1,p2,p3)]
    included=math.dist(points[0],points[1])+math.dist(points[1],points[2])
    excluded=math.dist(points[0],points[2])
    assert included-excluded>1e-6
    # Cross-check distances in the fixed-foot world frame using D1's
    # independently written segment-origin/absolute-angle construction.
    qa=ankle_knee_ratio*q_boundary
    knee_world=rotate(-qa,tuple(-v for v in joint('ANKLE_R')))
    hip_world=add(knee_world,rotate(-qa+q_boundary,tuple(-v for v in joint('KNEE_R'))))
    def world_point(point):
        local=tuple(map(float,point.findtext('location').split()))
        frame=point.findtext('socket_parent_frame')
        if frame=='/bodyset/femur_r': return add(hip_world,rotate(-qa+q_boundary,local))
        if frame=='/bodyset/calcn_r': return add(joint('SUBTALAR_R'),local)
        raise ValueError(frame)
    u,v,w=map(world_point,(p1,p2,p3))
    world_jump=math.dist(u,v)+math.dist(v,w)-math.dist(u,w)
    assert abs(world_jump-(included-excluded))<1e-14
    def length(q):
        u,v,w=[point_in_tibia(p,q) for p in (p1,p2,p3)]
        return math.dist(u,v)+math.dist(v,w) if lo-1e-5<=-q<=hi+1e-5 else math.dist(u,w)
    checks=[{'delta_rad':h,'left_minus_right_m':length(q_boundary-h)-length(q_boundary+h)} for h in (1e-6,1e-8,1e-10)]
    assert abs(checks[-1]['left_minus_right_m']-(included-excluded))<1e-9
    cases.append({'actuator':name,'point_frames':[p.findtext('socket_parent_frame') for p in (p1,p2,p3)],
      'knee_switch_rad':q_boundary,'ankle_at_switch_rad':ankle_knee_ratio*q_boundary,
      'tibia_frame_points_m':points,'length_included_m':included,'length_excluded_m':excluded,
      'length_jump_m':included-excluded,'limit_checks':checks})
report['conditional_path_length']=cases
report['geometry_method']='Direct Euclidean point distances on the proposed D1-matched frames; not an OpenSim run.'
report['source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
header=REPO/'sources/vendor/opensim-core/DeGrooteFregly2016Muscle.h'
report['header_sha256']=hashlib.sha256(header.read_bytes()).hexdigest()
assert report['header_sha256']=='c430bfc2a69996e6eb5700ea6bd7bc80fcd5ea9bfc6b234e23f05dc7bd8ff3e6'
(OUT/'rereview_probes.json').write_text(json.dumps(report,indent=2,sort_keys=True))
print(json.dumps(report,indent=2,sort_keys=True))
```
