# Stage D2 scope review — PR #30 at a3efd33

Reviewed by (model): ChatGPT\
Built by (model): Claude\
Reviewed SHA (full): `a3efd33329cae0c92f7266d726ba64ef05992782`\
Base SHA: `2f7cf983cb1660ae3f0fb8d08fbe51b69ceabe7e`\
PR: [#30](https://github.com/Corb1nW/Independent-Study/pull/30), `phase-d/claude-d2-scope`\
Review date: 2026-11-04\
Review branch: `reviews/chatgpt-d2-scope-a3efd33` (from the base/main SHA above)

**Verdict: AMEND.** Static optimization with the selected actuators is an appropriate next step for the prescribed D1 squat. Rigid tendon and no passive fiber force are defensible demonstration-baseline choices. The vendored curve header is correct. Amend the reserve semantics, the complete force-law/domain contract, and verification coverage before deciding the proposal. These are scope/acceptance-contract findings; there is no D2 implementation in this PR.

**Status: REVIEWED, NOT APPROVED**

## Scope and independence

Corbin explicitly assigned the Independent Study Reviewer role. I read the supplied Reviewer skill; the unchanged repository copy is the governing role checklist, subject to accepted decisions. I read the full PR handoff, full four-file diff, D-056 and its acceptance note, Q53–Q57 with their question/context notes, D-059 in full, the related D-058 exit criterion and the source registry.

Changed files are `PROJECT_STATE.md`, `docs/DECISIONS.md`, `sources/SOURCES.md`, and the vendored `DeGrooteFregly2016Muscle.h`. No project implementation, test, schema, ontology, model configuration, requirement or role-skill change was found.

Claude authored this proposal. My earlier suggestions for progressing from D1 to D2, inherited ChatGPT implementation, and the representation of my earlier review findings are self-checks. I inspected Claude's new proposal and vendor copy, read primary sources, and independently exercised the mathematical claims with my own small probes. Those probes and this review are self-authored/self-checked; they are not a D2 implementation, OpenSim execution, or scientific validation.

## Assessment of the requested topics

| Topic | Assessment |
|---|---|
| Right-sized method | Yes. Known motion, lengths and velocities make each baseline muscle force linear in activation; the squared-activation/reserve problem is a small convex quadratic problem. Retain 14 actuators, three bodies, committed OpenSim references and the proposed visual. No forward controller or compliant-tendon trajectory optimization is needed for this stage. |
| Force law and baseline | The fiber-force convention, one pennation projection, constant thickness and velocity normalization are coherent. Rigid tendon/no passive force are useful controlled simplifications, with the planned sensitivities. Complete the defaults, admissible domains and sensitivity comparison conditions (D2-R02). |
| Reserve rule | A finite recruitment penalty does not certify muscle capacity; the magnitude/signed rule also needs to be explicit (D2-R01). |
| Checks 8a–f | A good structure, but separate-curve agreement does not verify the complete force calculation, and generic pose grids do not assure coverage of active path switches (D2-R03). |
| Simplifications list | Substantial and honest, including the important rigid-tendon/passive/strength/compartment omissions. Add the force-law defaults/domain policy and clarify the remaining interpretation limits described below. |
| Curve constants | Vendor bytes match upstream at the stated pin and the stated hash. Landmarks are reproduced. No D2 constants/code exist yet to certify as an implementation. |
| D-056 and Q53–Q57 | Internally consistent and appropriately distinguish an accepted interpretation from a pending D2 proposal. Original new owner messages were unavailable to this reviewer; exact quotation authentication remains reported. |

[De Groote et al. 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC5043004/), equations 4–7 and the accompanying rigid-tendon discussion, support the force/length/pennation structure. The paper distinguishes static recruitment from dynamic activation/contraction modeling. [OpenSim's static-optimization documentation](https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim/pages/53089619/How+Static+Optimization+Works) specifically describes active fiber force projected along an inextensible tendon, excluding the parallel elastic contribution. These support a labeled software baseline, not a claim that passive force or compliance is negligible in human squats. The pre-check's 93% capacity and 27 N·m soleus figures remain builder-reported estimates on the unmodified model; I did not independently reproduce them.

## Required amendments

### D2-R01 — Medium: separate penalized reserve use from capacity, and specify signed magnitudes

**Location:** `docs/DECISIONS.md:1629–1631` (D-059 items 1 and 3), :1651 (8e), :1665 (status), :1680–1681 (exit criterion).

**Evidence:** the proposed objective is `sum(a_i^2) + sum((r_j/r0)^2)`, with `r0=1 N·m`. My executed reserve probe used a one-joint mathematical example with 14 identical actuators, each producing 0.1 N·m at full activation, and demand 1.4 N·m. All activations equal to 1 exactly reproduce the demand with zero reserve. The proposed penalized optimum instead has:

- activation per actuator: **0.12280701754385963**;
- reserve: **1.2280701754385963 N·m**;
- objective: **1.7192982456140347**, versus 14 for the muscle-only solution;
- interior stationarity residual: approximately **−2.78e−17**.

This is the unique optimum of that strictly convex toy problem. It would exceed the proposed reserve threshold even though an exact bounded muscle-only solution exists. This is a counterexample to using penalized reserve magnitude as a certificate of inadequate muscle capacity; it is **not a claim that Gait2392 produces these numbers**.

Also, reserves must be signed to cover both torque directions. Read literally, “at or below 1 N·m” permits a reserve of −10 N·m. The probe confirms that `r <= 1` passes that example while `abs(r) <= 1` does not.

**Problem:** a reserve from a soft recruitment trade-off measures what that objective chose, not necessarily the minimum assistance the muscle set needs. Calling the threshold a muscle-feasibility test can mislabel feasible cases. The dimensional scale `r0` and feasibility allowance happen to have the same numerical value but have different roles.

**Proposed fix:** retain small labeled reserves, but state `max_{t,j}|r_j(t)| <= epsilon_reserve`, with finite checks, signed per-joint outputs, units and numerical tolerance. Define the 1 N·m allowance explicitly as a demonstration tolerance. Then choose one of these contract-consistent options:

1. Certify bounded-muscle feasibility separately (for example, minimize the maximum absolute torque deficit under `0<=a<=1`, or use an equivalent feasibility solve), and distinguish that certificate from reserve use in the recruitment optimum.
2. Give reserve minimization priority over activation minimization, with a precise hierarchy.
3. Keep the soft objective and call its status a **reserve-use flag**, without claiming it proves a muscle-capacity shortfall.

Do not attempt to turn an arbitrarily large finite penalty into an exact certificate. Add both signed-threshold cases and a feasible-but-penalized-reserve toy case to 8d/e.

### D2-R02 — Medium: complete the rigid-tendon force-law and applicability contract

**Location:** `docs/DECISIONS.md:1633–1639` (item 5), :1655–1660 (sensitivity cases), :1667–1677 (simplifications).

**Evidence and problem:** the stated force equation is sensible, but the remaining choices affect whether a muscle can pull and which model the oracle represents.

For constant width `h=l_opt*sin(alpha0)` and `x=L_MT-l_ts`, the intended positive-projection branch gives:

```text
l_M = sqrt(x^2 + h^2)
cos(alpha) = x/l_M
v_M = cos(alpha) * dL_MT/dt
normalized_v_M = v_M/(v_max*l_opt)
F_T = F0*a*f_act(l_M/l_opt)*f_v(normalized_v_M)*cos(alpha)
```

The proposal names normalized fiber velocity but does not explicitly state this kinematic conversion or its sign. Passing musculotendon velocity directly into the force-velocity curve is wrong when pennation is nonzero.

The vendor header, :442–454, specifies normalized velocity domain **[-1,1]** and puts checking it on the caller. My executed evaluation gives `f_v(-2)=-0.22922210162278223`: unrestricted extrapolation can produce negative active force. Nonpositive `x` also leaves the intended positive-cosine pennation branch; zero-length/nonfinite cases need handling. The header's fiber-length bounds are 0.2 and 1.8 (:994–995); a valid-range policy must be declared rather than silently assuming every D1-scaled path is admissible.

The baseline also needs a deliberate zero-damping choice. At the pinned upstream source, `DeGrooteFregly2016Muscle.cpp:77` constructs damping 0, but `replaceMuscles()` at :968–982 copies Millard damping and strain settings. `Millard2012EquilibriumMuscle.cpp:257` defaults damping to **0.1**, and the vendored muscle file does not override it. Thus simply converting this model does not give a zero-damping baseline. Disabling passive elastic force does not disable damping (header :595–604). This matters because D-059's equation omits that term.

**Proposed fix:** amend item 5 to define the fiber velocity conversion/sign, positive-projection branch, applicability domains, and failure/flag behavior for nonfinite, out-of-range or negative-force cases. Adopt or justify the declared fiber-length range and enforce the velocity curve's stated domain; do not silently extrapolate or clamp while still claiming the same model.

Explicitly set and record the oracle/baseline options: tendon compliance ignored, activation dynamics ignored, passive elastic force ignored, **fiber damping zero**, active-force width scale, and the actual curve/strain defaults used. Reset inherited values after any `replaceMuscles()` conversion. Add zero damping to the simplifications list. Record the passive curve/default used for the passive-on case; use the same corrected header formulation consistently.

For the bottom-pose compliance comparison, state what is held fixed (for example the same activation and path length in passive-on rigid and compliant cases), and report equilibrium residual and applicable bounds. A change in recruitment and a change in tendon compliance are different comparisons.

### D2-R03 — Medium: verify the assembled force law and geometry switches, not just the component curves

**Location:** `docs/DECISIONS.md:1646–1654` (8a–f), :1665 (verification status), :1679–1685 (exit criterion).

**Evidence:** 8a/b check geometry and derivatives; 8c checks exported normalized curves; 8d checks the optimizer. Those can all pass while the force coefficient fed to the optimizer has an omitted/double pennation factor or the wrong fiber velocity. The optimizer then accurately solves the wrong model.

My hand-defined probe with `F0=1000 N`, `a=0.5`, `l_M=l_opt=0.1 m` and `alpha0=30 degrees` gives, at zero velocity:

| Assembly | Tendon force |
|---|---:|
| Correct single projection | 433.01270189221935 N |
| Projection omitted | 500 N |
| Projection applied twice | 375 N |

All three can use exactly correct `f_act(1)` and `f_v(0)`. At path velocity 0.05 m/s with `v_max=10`, the correct normalized fiber velocity is **0.04330127018922194**, not 0.05. The corresponding correct/incorrect tendon forces are **475.94546724506705 / 482.00599558627266 N**. These are deliberately chosen algebraic fixtures, not patient or Gait2392 observations.

The chosen paths also have conditional-point boundaries **inside the actual 0–100 degree D1 knee range**:

| Conditional point | Source knee boundary (rad) | D1 knee boundary (degrees) |
|---|---:|---:|
| `semimem_r-P2` | -0.558505 | 31.99998 |
| `semiten_r-P2` | -0.331613 | 19.00003 |
| `vas_med_r-P3` | -1.21004 | 69.33019 |
| `vas_int_r-P3` | -1.42 | 81.36001 |
| `vas_lat_r-P3` | -1.21004 | 69.33019 |
| `rect_fem_r-P2` | -1.45997 | 83.65012 |
| `med_gas_r-P2` | -0.785398 | 44.99999 |
| `lat_gas_r-P2` | -0.785398 | 44.99999 |

Moving points use knee-dependent splines as well. A generic pose grid and a central difference across a point switch do not specify correct boundary behavior.

**Proposed fix:** expand 8c to compare **complete tendon force and its intermediate fiber length, pennation, fiber velocity and normalization** against an equivalently configured OpenSim model at nonzero pennation and shortening/lengthening velocities. Include `a=0`, an interior activation and `a=1`; test linearity in activation for this baseline, single projection, zero baseline passive/damping force, and the passive-on case. Add a simple independently calculated fixture such as the one above.

Expand 8a/b to cover the actual D1 poses plus spline knots and both sides of the listed conditional switches, with explicit active-point conventions, step-size/convergence checks and one-sided comparisons where appropriate. Do not assert a central derivative at a nondifferentiable switch. Test a two-joint path and the knee sign conversion; include a muscle/joint power or virtual-work identity as a useful cross-check.

For 8d, make the acceptance checks include primal torque equality, activation bounds, dual feasibility, stationarity and complementarity, plus independent solver agreement and D2-R01's cases. Distinguish an optimizer failure from a valid reserve-flagged result. State tolerances and units in the eventual test/configuration contract.

The committed oracle fixture should carry the exact OpenSim package/version/platform, source/model/transformation hashes, overrides, units and sampled states. Its outputs must come from OpenSim rather than from the implementation being tested. This fits the planned reference-file tool and does not require OpenSim for ordinary tests.

## Simplifications and nonblocking refinements

**L01 — Low, item 2 and simplifications list:** add the zero-damping/default/domain choices from D2-R02 and explain that force outside the three retained coordinates is absorbed by ideal constraints and is not a new joint-reaction/contact-stress prediction. The female/male cases share generic muscle strengths; they are stature-scaled demonstration profiles, not validated sex-specific strength models.

The omission of biceps femoris short head is a scope choice, not proved harmless by a net knee-extension torque. A knee flexor can still influence recruitment when a two-joint actuator is being recruited for hip flexion. The proposal itself recognizes that biarticular coupling can require antagonists. Keep the 14-muscle-actuator scope, but qualify the exclusion rationale and let the reserve/capacity diagnostics show its limits.

**L02 — Low, item 1:** “static optimization” here means independent recruitment at each instant. D1's inertial torque demand is retained. Prefer that description to “quasi-static” if the latter could suggest skeletal inertia has been discarded.

The ten existing simplifications correctly identify the main new approximations: D1 geometry, instantaneous activation, criterion-driven co-contraction, rigid tendons, no passive baseline, gait-derived paths/strengths, no strength scaling, changed curves, independent actuators and omitted muscles. I do not recommend expanding to full activation dynamics, extra muscles or forward motion prediction to resolve these findings.

## Curve-constant check against the vendor file

Vendor file: `sources/vendor/opensim-core/DeGrooteFregly2016Muscle.h`. Its full bytes match upstream at [opensim-core `01683ac33568a3cb5eef2e445c7815f8220e8905`](https://github.com/opensim-org/opensim-core/blob/01683ac33568a3cb5eef2e445c7815f8220e8905/OpenSim/Actuators/DeGrooteFregly2016Muscle.h):

- SHA-256: `c430bfc2a69996e6eb5700ea6bd7bc80fcd5ea9bfc6b234e23f05dc7bd8ff3e6`.
- Git blob: `e9a9df51778f71422efc6d33bd4aa6ea62efb8a6`.

The full-precision active-force-length constants are:

| Term i | b1i | b2i | b3i | b4i |
|---|---:|---:|---:|---:|
| 1 | 0.8150671134243542 | 1.055033428970575 | 0.162384573599574 | 0.063303448465465 |
| 2 | 0.433004984392647 | 0.71677541339776 | -0.029947116970696 | 0.200356847296188 |
| 3 | 0.1 | 1 | 0.353553390593274 | 0 |

Force-velocity constants: `d1=-0.3211346127989808`, `d2=-8.149`, `d3=-0.374`, `d4=0.8825327733249912`. The equivalent stable expression is `d1*asinh(d2*v+d3)+d4`. The Gaussian denominator is **squared** (header :896–906).

Other sensitivity-related constants are `kPE=4`, `c1=0.2`, `c2=1`, `c3=0.2`; defaults/overrides still need the explicit contract requested above. The corrected passive curve is at header :479–489; it is not simply the unmodified supplement expression.

Executed landmark checks: `f_act(1)=1`, `f_v(-1)=0`, `f_v(0)=0.9999999999999999`, `f_v(1)=1.7943429635553172`. The header documents the modified peak/velocity points, inverse-velocity correction and passive-curve change, so citing **the pinned OpenSim implementation** rather than claiming literal supplement constants is honest. D-059 does not provide a separate transcribed table or implementation yet; my check authenticates the authority/constants and their interpretation, not future code.

## D-056 acceptance and Q53–Q57

The status fields, acceptance note and pending D2 scope are consistent. D-056 remains labeled an **interpretation**, retains its source limitations, projects fiber force once using same-model parameters, and does not change Phase B. I independently read the accessible primary [Arnold et al. 2010 HTML](https://pmc.ncbi.nlm.nih.gov/articles/PMC2903973/) including Model Parameters and Table 1 notes: PCSA is volume divided by optimal fiber length; peak force uses 61 N/cm²; gluteus maximus compartments have separate force/pennation values and the whole-muscle force is distributed by stated proportions. This supports the recorded interpretation. It does not turn the paper into an explicit fiber-versus-tendon quotation. The author's PDF timed out, so I do not claim the previously requested independent PDF cross-check.

Q53 records acceptance of D-056 as that interpretation. Q54's earlier coverage claim is preserved with a correction explaining why Q57 adds tibialis anterior. Q55 maps the requested visual to activation/force plots. Q56 records owner confirmation of Q49–Q52. Q57 supports adding the dorsiflexor and a reserve check; the numerical 1 N·m policy remains a clearly marked builder proposal. Q53–Q57 do **not** imply acceptance of all of D-059, and the PR correctly leaves D-059 Proposed.

Available personal-history search did not retrieve the original Q53–Q57 selections or timestamps. The cited Claude session was inaccessible during the preceding review and remains unavailable here. These new answers, including Q56's owner confirmation, are **reported through Claude's record**, not original messages independently seen by ChatGPT. Q56 can be recorded as owner confirmation reported by Claude; it does not retroactively make my prior review an independent transcript check. No misquotation is alleged, and I have not rewritten the earlier limitation record.

The Q38-for-D2 role reading is explicitly marked an interpretation, with silence distinguished from approval. No hidden role assignment is inferred by this review.

## Ran, with environment and results

Exact HEAD before/after: `a3efd33329cae0c92f7266d726ba64ef05992782`; `git status --porcelain` empty. Execution date/time: 2026-11-04, 09:45–09:46 EST.

Environment: Linux x86_64/glibc 2.39, CPython 3.12.14; NumPy 2.3.5; pydantic 2.14.1/core 2.50.1; pytest 9.2.0; PyYAML 6.0.3; SymPy 1.14.0; Pint 0.26.2. `GIT_CONFIG_GLOBAL=/dev/null` and `GIT_CONFIG_NOSYSTEM=1` were set.

| Command | Exit | Observed result |
|---|---:|---|
| `python -m pytest -q` | 0 | 178 passed in 37.47 s |
| `python -m src.integrity` | 0 | PASSED |
| `python tools/review_cycle1_probes.py` | 0 | 9/9 negative probes REJECTED |
| `python -m tools.build_segment_datasets --check` | 0 | current (exit 0, no stdout) |
| `python /workspace/scratch/5513ec304951/pr30-check/reviewer_probes.py` | 0 | Header hash/landmarks, reserve counterexample, pennation/velocity examples and XML path-boundary inventory reproduced. |

These 178 existing tests protect the current project. They cannot verify a D2 implementation that does not exist.

Checkout method: the hash-checked shallow/sparse snapshot from the preceding review was copied locally, then new text blobs, trees and signed commits were fetched through the GitHub connector and required to reproduce their Git object IDs. Review tree: `81c186be7fd03fdb66b5b3f1c1d9aaae2c79030b`; base tree: `89c14fa67923ace5655cfd0b9385ed5a52c9950e`. Direct Git cloning was unavailable for this partial snapshot. The unrelated binary `References/LB_AO_Project_Phases_Overview.pdf` remains excluded because the connector cannot transfer it. Checkout emitted missing-object warnings for that excluded PDF, with exit 0; every relevant code/test/model/source file is present and hash-checked. I make no full-repository fsck or PDF-content claim.

## Sources checked and registration

Primary sources actually read: De Groote 2016 main text; Arnold 2010 primary HTML; the two OpenSim static-optimization pages below; the vendored Gait2392 XML and curve header; and these pinned upstream source files:

- [DeGrooteFregly2016Muscle.cpp](https://github.com/opensim-org/opensim-core/blob/01683ac33568a3cb5eef2e445c7815f8220e8905/OpenSim/Actuators/DeGrooteFregly2016Muscle.cpp) — defaults, rigid fiber velocity, `replaceMuscles` inheritance.
- [Millard2012EquilibriumMuscle.cpp](https://github.com/opensim-org/opensim-core/blob/01683ac33568a3cb5eef2e445c7815f8220e8905/OpenSim/Actuators/Millard2012EquilibriumMuscle.cpp) — default damping.
- [GeometryPath.cpp](https://github.com/opensim-org/opensim-core/blob/01683ac33568a3cb5eef2e445c7815f8220e8905/OpenSim/Simulation/Model/GeometryPath.cpp) and [MovingPathPoint.cpp](https://github.com/opensim-org/opensim-core/blob/01683ac33568a3cb5eef2e445c7815f8220e8905/OpenSim/Simulation/Model/MovingPathPoint.cpp) — coordinate-dependent point work/derivatives; this supported, rather than contradicted, the planned virtual-work approach.

The registered OpenSim source row already covers the pinned repository and first two implementation files; add the geometry-file uses to it rather than duplicating the source.

**New source cited by this review that the builder should add to `sources/SOURCES.md`:** OpenSim documentation, Jennifer Hicks, **Working with Static Optimization**, updated 2024-03-22, [official page](https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim/pages/53085189/Working+with+Static+Optimization), status **Read**, used for reserve weighting/interpretation and the limitations of instantaneous optimization (D-059 review D2-R01). This is distinct from the already registered **How Static Optimization Works** page. Its reserve-cost discussion supports using a low reserve scale as a practical preference; my mathematical counterexample shows why that preference is not a universal exact capacity certificate.

De Groote/Arnold and the other reused sources are already registered. I did not independently access the De Groote supplement, Delp dissertation, Carhart or Yamaguchi; their cited-not-accessed/reported provenance is preserved. The SimTK 4.5 API page was unavailable; pinned implementation code supplied the technical check instead.

## Disposition

**Findings:** D2-R01, D2-R02, D2-R03, all Medium; amend the proposal before Corbin decides. L01/L02 are nonblocking refinements. Add the new source entry described above in the response.

**Earlier findings:** this is the first review of D-059. Prior Stage D1 code findings are not reopened. Q56's treatment of VL28-01 is discussed above; no prior review or result is rewritten.

**Read or reasoned only:** proposed architecture, full-force equations/derivation, applicability and reserve semantics, optimizer sufficiency for a convex baseline, source interpretation, approval scope and proposed sensitivity controls. The original Q53–Q57 messages and builder's uncommitted OpenSim pre-checks remain reported.

**Not run, and why:** no D2 solver/runner/reference generator exists. OpenSim 4.6 was not installed or executed; a committed oracle is future work. No independent reproduction of the builder's 93%/27 N·m pre-check, compliant-tendon sensitivity, new visual, Windows run or primary-source PDF check. The standalone probes are explicitly not substitutes for these.

**Out-of-scope observations:** no decision on clinical validity or realistic muscle activation is implied. D1's provisional inputs and concerns carry over. This review does not authorize a D2 build or change any accepted decision.

**Verdict: AMEND** (recommendation; Corbin decides).\
**Must fix before Corbin decides:** D2-R01–R03: reserve/capacity semantics and signed threshold; complete force-law/default/domain contract; assembled-force and geometry-boundary verification.\
**Status: REVIEWED, NOT APPROVED**

## Appendix: review-only probe actually executed

This self-authored standard-library program reproduces the source/hash checks and numerical examples. It reads committed inputs but implements no project D2 solver or muscle-path engine. Adapt its root directory if rerunning elsewhere.

```python
"""Review-only algebra/source probes; not a D2 implementation or OpenSim run."""
import hashlib
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).parent
REPO=ROOT/'repo'
header=(REPO/'sources/vendor/opensim-core/DeGrooteFregly2016Muscle.h').read_bytes()
sha=hashlib.sha256(header).hexdigest()
assert sha=='c430bfc2a69996e6eb5700ea6bd7bc80fcd5ea9bfc6b234e23f05dc7bd8ff3e6'
c={k:float(v) for k,v in re.findall(r'constexpr static double\s+(\w+)\s*=\s*([-+\d.eE]+)\s*;',header.decode())}

def fl(length):
    return sum(c[f'b1{i}']*math.exp(-.5*((length-c[f'b2{i}'])/(c[f'b3{i}']+c[f'b4{i}']*length))**2) for i in (1,2,3))

def fv(velocity):
    return c['d1']*math.asinh(c['d2']*velocity+c['d3'])+c['d4']

assert abs(fl(1)-1)<1e-12 and abs(fv(-1))<1e-12 and abs(fv(0)-1)<1e-12
report={'header_sha256':sha,'constants':{k:c[k] for k in [f'b{j}{i}' for i in (1,2,3) for j in (1,2,3,4)]+['d1','d2','d3','d4','kPE','c1','c2','c3']},
 'force_length_values':{str(x):fl(x) for x in (.2,1.,1.3,1.8)},
 'force_velocity_values':{str(x):fv(x) for x in (-2.,-1.,0.,1.,2.)}}

# A soft reserve penalty can flag an exactly muscle-only feasible problem.
n=14; k=.1; tau=1.4; r0=1.
a=k*tau/(r0*r0+n*k*k)
r=tau-n*k*a
stationarity=2*a-2*k*r/(r0*r0)
assert 0<a<1 and abs(stationarity)<1e-12 and abs(n*k-tau)<1e-12 and r>1
report['reserve_toy']={'actuators':n,'torque_per_unit_activation_N_m':k,'demand_N_m':tau,
 'exact_muscle_only_activation':1.,'penalized_activation_each':a,'penalized_reserve_N_m':r,
 'penalized_objective':n*a*a+(r/r0)**2,'muscle_only_objective':float(n),'stationarity_residual':stationarity}
report['signed_reserve_predicate']={'reserve_N_m':-10.,'one_sided_at_or_below_one':-10<=1,'absolute_at_or_below_one':abs(-10)<=1}

# Pennation/velocity coupling not established by normalized curve checks alone.
F0=1000.; activation=.5; lopt=.1; alpha0=math.pi/6; vmax=10.; path_velocity=.05
h=lopt*math.sin(alpha0); x=lopt*math.cos(alpha0)
l=math.hypot(x,h); cosalpha=x/l
fiber_velocity=cosalpha*path_velocity
norm_velocity=fiber_velocity/(vmax*lopt)
eps=1e-7
numeric_velocity=(math.hypot(x+path_velocity*eps,h)-math.hypot(x-path_velocity*eps,h))/(2*eps)
assert abs(numeric_velocity-fiber_velocity)<1e-9
report['pennation_toy']={'cos_alpha':cosalpha,'fiber_velocity_m_s':fiber_velocity,'finite_difference_fiber_velocity_m_s':numeric_velocity,
 'normalized_fiber_velocity':norm_velocity,'wrong_path_velocity_normalization':path_velocity/(vmax*lopt),
 'correct_static_tendon_force_N':F0*activation*fl(1)*cosalpha,
 'missing_projection_static_force_N':F0*activation*fl(1),
 'double_projection_static_force_N':F0*activation*fl(1)*cosalpha**2,
 'correct_moving_tendon_force_N':F0*activation*fl(1)*fv(norm_velocity)*cosalpha,
 'wrong_velocity_tendon_force_N':F0*activation*fl(1)*fv(path_velocity/(vmax*lopt))*cosalpha}

names='glut_max1 glut_max2 glut_max3 bifemlh semimem semiten vas_med vas_int vas_lat rect_fem med_gas lat_gas soleus tib_ant'.split()
xml=ET.parse(REPO/'sources/vendor/opensim-models/gait2392_millard2012muscle.osim').getroot()
muscles={m.attrib['name']:m for m in xml.findall('.//Millard2012EquilibriumMuscle')}
rows=[]
for name in names:
    m=muscles[name+'_r']
    assert float(m.findtext('max_contraction_velocity'))==10
    for p in m.findall('.//ConditionalPathPoint'):
        assert p.findtext('socket_coordinate')=='/jointset/knee_r/knee_angle_r'
        lo,hi=map(float,p.findtext('range').split())
        if max(lo,-math.radians(100))<=min(hi,0):
            for edge in (lo,hi):
                if -math.radians(100)<=edge<=0:
                    rows.append({'point':p.attrib['name'],'source_knee_boundary_rad':edge,'D1_knee_boundary_deg':-math.degrees(edge)})
report['conditional_boundaries_in_D1_motion']=rows
report['all_14_vmax_are_10']=True
(ROOT/'out/reviewer_probes.json').write_text(json.dumps(report,indent=2,sort_keys=True))
print(json.dumps(report,indent=2,sort_keys=True))
```
