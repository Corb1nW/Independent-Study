# D-062 Amendment 1 re-review

- **Date:** 2026-11-16
- **Reviewed by (model):** ChatGPT
- **Built by (model):** Claude
- **Proposal:** [PR #43](https://github.com/Corb1nW/Independent-Study/pull/43)
- **Reviewed SHA:** `3dcbb72a4f90c0e5b1d670c1046486940cf00f3b`
- **Base SHA:** `c29572becc1e495b78a7efe643a516b63f9c3ba4`
- **Previous reviewed SHA:** `551efea2279dd2fe89610e50752de41acf173d1b`
- **Verdict:** **AGREE** on the D-062 scope with Amendment 1. Corbin decides.
- **Status:** REVIEWED, NOT APPROVED

## Scope and independence

This review covers the one-commit delta since `551efea`. It changes `PROJECT_STATE.md`, `docs/DECISIONS.md` and the D-061 plan. I checked the amended D4 acceptance criteria and the deferred dataset wording. Q68 and Q69 agree between the handoff and the decision log. I authored the previous findings and suggested fixes. The assessment below checks Claude's amended decision text and uses reviewer probes of the existing repository data.

## Findings from the previous review

| Finding | Disposition | Evidence |
|---|---|---|
| D062-B01 · Fixed-knee direction | Resolved | C2 and C3 use moment-arm magnitude for thresholds. The anatomical direction criterion applies to the moving-knee baseline and growth variant. The fixed-knee regression checks disagreements against the OpenSim reference by direction and pose. C5 records them and A5 requires the direction check to fail if the corresponding reference disagreement is removed. [Amendment](https://github.com/Corb1nW/Independent-Study/blob/3dcbb72a4f90c0e5b1d670c1046486940cf00f3b/docs/DECISIONS.md#L2411-L2430) |
| D062-B02 · Bilateral required edges | Resolved | The check derives right-side crossings from modeled paths and requires the corresponding left-side edges. It also requires the capability-supported `ACTS_ON` edges. The revised A4 and A5 cover the symmetric omission and distinguish it from a unilateral deletion. [Amendment](https://github.com/Corb1nW/Independent-Study/blob/3dcbb72a4f90c0e5b1d670c1046486940cf00f3b/docs/DECISIONS.md#L2432-L2450) |
| D062-B03 · Hip assembly endpoint | Resolved | A direct segment, its explicit representation, or a unique represented containing skeletal complex resolves each endpoint. Missing and ambiguous mappings stop assembly. The declared merges cover subtalar, low back and the endpoint-free lumped MTP. [Amendment](https://github.com/Corb1nW/Independent-Study/blob/3dcbb72a4f90c0e5b1d670c1046486940cf00f3b/docs/DECISIONS.md#L2452-L2472) |
| D061-B02 · Deferred dataset wording | Resolved | The risk row calls for verifying both datasets' terms during D6 scope. [Plan](https://github.com/Corb1nW/Independent-Study/blob/3dcbb72a4f90c0e5b1d670c1046486940cf00f3b/docs/plans/2026-11-11_squat_proof_of_concept_plan.md#L204-L210) |

## Verification

- **Knee reference data.** I read the pinned D2 and D3 OpenSim geometry references and checked every actuator's directions at all 301 prescribed poses with the ontology capabilities. Under the documented stature scaling, all three bodies have 49 fixed-knee lateral gastrocnemius disagreements with magnitude at least 1 mm, at poses 126–174. Pose 150 is −3.085149 mm fixed and +10.385203 mm moving for Gait2392. No moving-knee baseline reference disagrees at the 1 mm threshold. At the 1e-9 m numerical-zero threshold, C5 also covers 12 smaller lateral disagreements and 29 medial disagreements. The amended deviation rule covers both. [Fixed reference](https://github.com/Corb1nW/Independent-Study/blob/3dcbb72a4f90c0e5b1d670c1046486940cf00f3b/tests/data/d2_oracle_reference.json) · [Moving reference](https://github.com/Corb1nW/Independent-Study/blob/3dcbb72a4f90c0e5b1d670c1046486940cf00f3b/tests/data/d3_oracle_reference.json)
- **Ontology probes.** From the pinned segment graph, 14 actuator paths, and 11 muscles' capabilities, my probe identifies the four known right-side crossings and 16 missing `CROSSES`/`ACTS_ON` edges across eight entities. The pairwise mirror comparison passes on the current data. The in-memory repair satisfies the required edges. Deleting the left edge fails both checks. Deleting both sides fails the required-edge check and passes the mirror check. [Hip ontology](https://github.com/Corb1nW/Independent-Study/blob/3dcbb72a4f90c0e5b1d670c1046486940cf00f3b/ontology/hip.yaml) · [Lower-limb ontology](https://github.com/Corb1nW/Independent-Study/blob/3dcbb72a4f90c0e5b1d670c1046486940cf00f3b/ontology/lower_limb_sagittal.yaml) · [Path data](https://github.com/Corb1nW/Independent-Study/blob/3dcbb72a4f90c0e5b1d670c1046486940cf00f3b/ontology/quantitative_data/muscles_gait2392.yaml)
- **Endpoint probes.** The amended rule resolves both hips to pelvis and thigh, each distal retained joint to its adjacent segments, the subtalar joint to the foot at both ends, and low back to pelvis and torso. In-memory removal of the bony pelvis mapping or addition of a second candidate rejects the hip endpoint. The lumped MTP has no stated endpoints, as recorded.

The probes ran as reviewer JavaScript against the pinned GitHub blobs. Claude reports 285 passing tests, integrity passed, 9/9 invalid probes rejected and a passing dataset check. I could read and test the committed reference data in this session. Fresh Python and OpenSim runs required the unavailable executor. The D4 assembler, growth variant and regression suite are future build work. This re-review introduces no new source.

**No blocking findings.** The amended D-062 scope is ready for Corbin's decision.

**Status: REVIEWED, NOT APPROVED.**
