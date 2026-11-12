# Squat proof of concept: plan

- **Decision:** D-061. Direction agreed tentatively (Q66). **This round is limited to Stage D4 (Q67)**, which is specified in D-062. Stages D5–D9 below are an **outlook, not decided**; each gets its own scope decision if Corbin goes on.
- **Written by:** Claude (Phase D builder), 2026-11-11, from Corbin's direction Q65; amended the same day (D-061 Amendment 1)
- **Base:** `main` at `cef38be` (Stage D3 merged)
- **Review:** ChatGPT, AMEND at `57bfeaa` (PR #46). D061-B01 is applied in D-062; D061-B02 and B03 are applied below.

## 1. What we are proving

Corbin's direction (Q65, 2026-11-11 12:49):

> “My goal is to have a proof of concept for a much larger and more comphrensive project. A lot of the physical therapy connection and human personalization will come along much further along. Right now I want to prove two things: working with AI to create legit scietific research and that we can use an ontology based view of all the musclskeletal system to build digital twin which will later grow in PT use. For now I want to narrow our focus towards a full example of a motion will recreated from this onotology. I want to stay with this squat and continue to make it as robust of a simulation as we can.”

This plan turns that into two claims, each with evidence we can show.

**Claim A: AI models can produce legitimate scientific research.** "Legitimate" is made concrete as seven properties, each of which the final package must show:
1. every number is sourced, derived from sources, or labelled as an assumption;
2. acceptance and validation criteria are written down **before** the results are seen;
3. the computation is verified by independent methods (two formulations, an external oracle);
4. the model is **evaluated** against measured human data under preregistered criteria, every outcome is reported, and "validated" is claimed only where the criteria are met;
5. the other AI model reproduces the results independently;
6. errors and corrections are on the record, including each model's own;
7. a human expert reads the result.

The project already shows 1, 3, 5 and 6. This plan adds 2, 4 and 7, and makes all seven visible in one report.

**Claim B: an ontology of the musculoskeletal system can build a working digital twin.** Concretely:
1. the squat model is **assembled from the ontology and its datasets** by generic code that names no anatomy;
2. anatomy added to the ontology enters the simulation **as data, with no code change**;
3. the ontology and the model **check each other** (for example, a muscle acts on a joint only if the ontology says it crosses it);
4. the assembled model **performs the squat**: a muscle-driven forward simulation, not only a backwards calculation from a given motion.

**Not in scope now:** clinical conditions (Phase E) and personalization to a patient (Phase F). They stay the larger project's direction. The only fitting to a person here is scaling the model to a measured subject's height and mass (stage D6), as D1 already does for its three bodies.

## 2. Where we start

Stages D1–D3 give a sagittal squat with three joints, three bodies and 14 Gait2392 muscles, using Gait2392's moving knee. Its geometry and forces match OpenSim to machine precision, and the muscles can supply the torques for all three bodies. The gaps, for these two claims:

| Gap | Why it matters | Stage |
|---|---|---|
| The model's **structure** (segments, joints, which muscles) is written in Python; the ontology lists it but nothing reads it | Claim B, items 1–3 | D4 |
| 14 of Gait2392's 43 leg muscles; no hip flexor except rectus femoris (iliopsoas missing); rigid tendons; no passive force | Robustness; the near-standing co-activation found in D3 | D5 |
| The squat motion is **designed**, not measured; nothing is compared with real people | Claim A, item 4 | D6 |
| Inverse only: the motion is given and the muscles are solved for; no activation dynamics, no forward simulation | Claim B, item 4 ("recreated") | D7 |
| Uncertainty only as one-at-a-time sensitivity cases | Robustness | D8 |
| Evidence spread across 60 decisions and 42 PRs | Claim A, presented | D9 |

## 3. Stages

Each stage gets its own scope decision with pre-stated acceptance criteria, as D1–D3 did, and its own build and review. The descriptions below are the plan, not those decisions.

### D4. The model is assembled from the ontology

**Work.**
- **Ontology content.** For the squat, the ontology states everything structural:
  - each model segment and the bones it represents;
  - each joint: its parent and child segment, its coordinates, sign conventions and ranges, and the dataset datum giving its location (including the moving knee's spline function);
  - each actuator: the muscle it represents, the joints that muscle crosses, and the dataset records holding its path and parameters;
  - the foot's contact points, and what the head-arms-trunk segment is made of.

  Numbers stay in the quantitative datasets, as now.
- **Executable model specifications.** The `models:` blocks already in the ontology (`squat_d1`, `squat_d2`: represents, retained and omitted coordinates, assumptions) become the input the assembler reads.
- **Assembler.** A new module reads the ontology and datasets through the existing validator and traceability gate. It builds a generic planar multibody tree by traversal, plus the actuator set, and names no anatomy in code. Generic tree dynamics (recursive Newton–Euler, with Kane's method as the second formulation) replace the squat-specific code. The current D1–D3 modules stay as regression oracles.
- **Two-way checks between anatomy and model** (as amended by ChatGPT's D061-B01; details and thresholds in D-062):
  - (a) The joints each muscle path crosses are derived from its path and the segment tree, and must match the ontology's `CROSSES`.
  - (b) Leverage is computed from geometry, without reading `CROSSES`. Non-negligible leverage needs a crossing. A crossing with negligible leverage (a path through the joint centre) is allowed and recorded.
  - (c) The sign of the leverage agrees with the muscle's stated actions.
  - (d) Every entity the model represents resolves to evidence.
  - (e) A deviation register (represented, simplified, omitted) is generated from the ontology.
- **Repair.** The demo's known gap is fixed: the knee crossings of biceps femoris long head, semimembranosus, semitendinosus and rectus femoris, both sides.

**Acceptance.** Fixed in D-062, before the build: regression to the D1–D3 official runs; the consistency checks, including deliberate-error tests; no anatomy in code; and a growth test adding iliopsoas with no code changes.

**Shows:** Claim B, items 1–3.

### D5. Complete the squat's anatomy (as data, through D4)

**Work.**
- Add Gait2392's remaining right-leg muscles that act at the hip, knee or ankle: 43 leg muscles in all (Gait2392's 46 per side minus its 3 trunk muscles), including iliopsoas. Their out-of-plane actions are declared omitted.
- Reconcile the additions with the muscles `hip.yaml` already describes with evidence.
- Make passive fiber force and tendon compliance (both in the De Groote force law) available, and test them as variations against the rigid-tendon baseline. D2's passive soleus artefact at 40° dorsiflexion is the known risk.
- The low-back joint stays locked (declared).

**Acceptance.**
- The OpenSim oracle and coverage check extended to every added muscle, at D2's tolerances.
- Results compared with the 14-muscle run.
- A **pre-stated hypothesis**: adding iliopsoas removes the near-standing gastrocnemius–tibialis co-activation found in D3. Reported whichever way it comes out.

**Shows:** robustness; Claim B item 2 at scale (about 30 muscles added as data).

### D6. A measured squat, and validation

**Data (preferred candidate).** Scherpereel et al. (2023), *Scientific Data* 10:924. The article is published under CC BY 4.0; the dataset files have their own DOI, and their terms have not yet been checked. The study has:
- squats with a 25 lb weight, from 12 adults;
- motion capture at 200 Hz and force plates at 1000 Hz;
- EMG from 8 muscles per leg;
- OpenSim (gait2354-based) inverse kinematics and joint moments.

D6's scope decision checks the exact squat files and their reuse and redistribution terms (ChatGPT's D061-B02). The files are vendored publicly only if those terms allow it; otherwise a pinned acquisition record lets others obtain the same files. The workspace cannot download them, so Corbin would. The alternative, Wang et al. (2022, Zenodo), has bodyweight squats with EMG. Its terms are pending confirmation: the record page Claude read showed no licence, while OpenAIRE lists CC BY 3.0 NL alongside an unspecified entry (per ChatGPT's review).

**Work.**
- Map the measured motion to the planar model (sagittal angles, with the filter declared).
- Scale the model to each subject's height and mass only.
- Model the 25 lb load as a point mass, with its placement declared.
- Run inverse dynamics and recruitment on the measured motion.

**Validation, pre-registered.** Before any comparison, the D6 decision fixes the metrics and pass thresholds:
- joint moments against the dataset's own inverse dynamics (peak and RMS per joint, normalised by body mass);
- centre of pressure against the force plates;
- EMG on/off timing against predicted activation, for the 6 recorded muscles that are in the 14-muscle set (gluteus maximus, biceps femoris, vastus lateralis, rectus femoris, tibialis anterior, medial gastrocnemius), plus gracilis and gluteus medius once D5 adds them.

The thresholds will be argued from published inter-model differences, not chosen after the fact. D6 completes the preregistered evaluation and reports every outcome, never tuned to fit. The squat is called "validated" only for the measures and conditions that meet the criteria, and the joint-moment comparison is described as a comparison with published inverse-dynamics estimates.

**Shows:** Claim A, items 2 and 4, to the extent the preregistered criteria are met. The squat becomes measured, not designed.

### D7. The model performs the squat (forward simulation)

**Work.**
- First-order activation dynamics, with time constants from a source.
- Forward integration of the muscle-driven model.
- A **tracking controller** in the style of computed muscle control: feedback on joint angles gives target accelerations, and a per-step optimization gives muscle excitations. Gains, stability and delay are analysed: this is where dynamic systems and control theory enter.
- Independent check: the same tracking problem in **OpenSim Moco** (included in OpenSim 4.6; checked in this workspace) on the matched model.
- **Stretch: a predictive squat.** The motion is generated from an objective (effort plus standing start and end, a depth target and foot contact) with no measured motion, then compared with the measured squat.

**Acceptance.** Pre-stated tolerances for:
- tracking error;
- activations against the inverse solution and against Moco;
- energy consistency;
- convergence as the step size is halved.

**Shows:** Claim B item 4: the squat is recreated by the model the ontology built.

### D8. Robustness and uncertainty

**Work.**
- **Numerical robustness:** solver tolerances, step sizes, alternative solvers.
- **Parameter uncertainty:** Monte Carlo over muscle strengths, segment parameters and tendon slack lengths, with explicit sampling assumptions (D-028, which needs Corbin's decision).
- **Global sensitivity analysis:** variance-based, to rank which parameters matter most.
- **Cross-platform reproduction:** Windows, run by Corbin, and Linux, run by both models.

Can run alongside D6 and D7.

**Acceptance.** Uncertainty bands on joint moments, activations and feasibility; a ranked list of the parameters that matter most; identical results across platforms.

**Shows:** robustness, and honest uncertainty.

### D9. The proof-of-concept package

1. **Technical report** in paper form:
   - methods;
   - verification;
   - validation against the pre-registered criteria;
   - uncertainty;
   - limitations, with the ontology-generated deviation register;
   - a methods section on the AI collaboration.

   Every number in it traces to a run manifest.
2. **Audit of the research process**, compiled from `DECISIONS.md` and `docs/reviews/`:
   - review findings by stage and by kind (science, numerics, data, engineering, wording);
   - which findings changed results;
   - corrections each model made to its own claims;
   - independent reproductions.
3. **Demo viewer: ontology → model → simulation.**
   - Click a muscle on the figure to see its ontology entity, evidence and parameters, and where it appears in the results.
   - Switch between the inverse and forward solutions, and between measured and simulated motion.
4. **Human expert review.** Corbin arranges a biomechanics or physical therapy faculty reader. This is the clearest outside check of "legitimate".
5. **Reproduction package:** pinned environment and a one-command rerun.

**Shows:** Claims A and B, in one place.

## 4. Order, and where it can stop

D4 → D5 → D6 → D7 → D9, with D8 running alongside from D6.

Every stage ends with a complete result:
- after **D4**, Claim B's core is shown;
- after **D6**, the preregistered evaluation against measured data is complete, with every outcome reported; validation is claimed only where the criteria are met;
- after **D7**, forward tracking is reported against its own criteria.

If time runs short, the first things to cut are D7's predictive squat and D8's global sensitivity analysis. D9 can be written after any stage.

## 5. How we work (proposed changes)

1. **Pre-registration.** Each stage's scope decision states its acceptance and validation criteria before the results exist. A criterion changed after results are seen is an amendment that says so.
2. **Review tiers: withdrawn (ChatGPT's D061-B03).** The existing boundary stays: the D-047 light path covers documentation wording and formatting only (D-051). Any change to executable behaviour keeps a targeted run of the affected path, plus a regeneration check for generated outputs. A future proposal for a separate path for executable changes would name the D-051 amendment for Corbin's decision.
3. **Builder rotation.** ChatGPT builds one stage and Claude reviews it, so the record shows both models building and both reviewing. Suggested: D8, which needs only packages ChatGPT already has offline.
4. **Findings log.** From now on each review finding is tagged with a kind, for D9's audit.

## 6. Decisions for Corbin

**This round (Q67):** only Stage D4 is up for decision, as **D-062**. P2–P6 below are withdrawn until the outlook beyond D4 is decided.

| # | Decision | Status |
|---|---|---|
| P1 | The plan, and the D-040 amendment (Phases E and F deferred; new Phase D exit criterion) | Direction agreed tentatively (Q66). The D-040 amendment waits for the outlook beyond D4 |
| P2 | Muscle set for D5 | Withdrawn for now |
| P3 | Dataset for D6 | Withdrawn for now; data terms to be checked first (D061-B02) |
| P4 | Review tiers and builder rotation | Tiers withdrawn (D061-B03); rotation withdrawn for now |
| P5 | D-028 sampling assumptions, for D8 | Withdrawn for now |
| P6 | A faculty expert reader for D9 | Withdrawn for now |

**Outlook: Phase D exit criterion (not decided; replacing "mechanics validated before conditions are added"):** a squat measured in people is reproduced by a muscle-driven forward simulation of a model assembled from the ontology. The result carries independent verification, pre-registered validation results, stated uncertainty and an independent reproduction by the other model. It is not validated beyond the measured data used, and only for the measures that meet their preregistered criteria.

## 7. Risks

| Risk | Handling |
|---|---|
| Dataset files are hard to access or in an awkward format | Check the squat files first in D6's scope; the alternative dataset needs permission |
| The measured squat is weighted (25 lb) and recorded with gait2354 | Model the load explicitly; compare joint moments, not model internals |
| Forward simulation with compliant tendons is numerically stiff | Rigid-tendon forward simulation first; Moco as an independent check |
| Validation fails | A legitimate result: reported, explained and kept |
| Scope outgrows the time available | The stopping points in §4 |
| A generic assembler hides squat-specific shortcuts | D4's regression to the D1 and D3 runs to machine precision, and the zero-code growth test |

## 8. Sources

New in this plan (listed in `sources/SOURCES.md`):
- **Scherpereel et al. (2023),** *Scientific Data* 10:924, [doi:10.1038/s41597-023-02840-6](https://doi.org/10.1038/s41597-023-02840-6); data at [doi:10.35090/gatech/70296](https://doi.org/10.35090/gatech/70296). Article page read; data not yet accessed.
- **Wang, Basu, Durandau and Sartori (2022),** Zenodo [doi:10.5281/zenodo.6457662](https://doi.org/10.5281/zenodo.6457662). Record page read, as the alternative; terms pending confirmation.

Cited by ChatGPT's review (D061-B02), not accessed by Claude: the [Georgia Tech EPIC Lab dataset description](https://www.epic.gatech.edu/a-human-lower-limb-biomechanics-and-wearable-sensors-dataset-during-cyclic-and-non-cyclic-activities/) and the [OpenAIRE record for the Wang DOI](https://explore.openaire.eu/search/result?pid=10.5281%2Fzenodo.6457662).

Gait2392, OpenSim 4.6 (including Moco) and De Groote et al. (2016) are already listed.
