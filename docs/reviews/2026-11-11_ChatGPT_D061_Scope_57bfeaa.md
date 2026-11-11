# D-061 squat proof-of-concept scope review

- **Date:** 2026-11-11
- **Reviewed by (model):** ChatGPT
- **Built by (model):** Claude
- **Proposal:** [PR #43](https://github.com/Corb1nW/Independent-Study/pull/43)
- **Reviewed SHA:** `57bfeaa7ac1beebceeff2b572aa3e2d5cd29c1e8`
- **Proposal base SHA:** `cef38be756c460d19d31ac26502b1bc6c9a71d80`
- **Review branch base SHA:** `c29572becc1e495b78a7efe643a516b63f9c3ba4`
- **Verdict:** **AMEND**. Corbin decides on D-061.
- **Status:** REVIEWED, NOT APPROVED

## Scope and independence

The four-file diff proposes a roadmap and records the D3 merge. I checked D-061 and its plan, the handoff and source changes, and the cited decisions D-040, D-047, D-048, D-051 and D-058 through D-060, plus the proposed D-028. Q65 is the direction reported in the handoff. A-17 is consistent with the merge record and the pinned D3 re-review. I authored none of PR #43. The baseline suite includes prior ChatGPT work and the demo finding is cited from my earlier review.

The roadmap fits Q65. D4 should show that the ontology can assemble the accepted squat and that an actuator can be added as data. D5 then tests that at scale. D6 and D7 address measured-data evaluation and muscle-driven forward tracking, respectively. Deferring clinical conditions and patient personalization keeps this proof of concept focused. Each stage retains its own scope decision.

## Execution at the reviewed SHA

Clean detached Linux checkout on x86-64, Python 3.12.14, OpenSim 4.6, NumPy 2.3.5, SciPy 1.17.0 and pytest 9.2.0. The sparse checkout excluded the unrelated project overview PDF. `git rev-parse HEAD` returned the full reviewed SHA before and after execution. The worktree was clean before and after the checks.

| Check | Result |
|---|---|
| `python -m pytest -q` | 285 passed in 70.78 s, one AnyIO pytest deprecation warning |
| `python -m src.integrity` | Passed |
| `python tools/review_cycle1_probes.py` | 9/9 invalid probes rejected |
| `python -m tools.build_segment_datasets --check` | Passed |
| Parse the vendored Gait2392 `ForceSet` XML | 92 muscle elements, 46 right-side elements, 43 after excluding `ercspn_r`, `extobl_r` and `intobl_r`. Iliacus and psoas have separate elements. |
| Import OpenSim 4.6 and inspect available classes | `MocoStudy`, `MocoTrack` and `CMCTool` present |

The PR changes records only. The results above cover the existing code. The D1–D3 official simulations were read through their existing records. Dataset archives, a D4 assembler, D6 validation and a D7 matched Moco solve are outside this execution check.

## Blocking findings

### D061-B01 · High · Scientific verification · D4 check (a)

Joint crossing and nonzero moment arm are different properties. A path between a parent and child segment routed through the revolute joint center crosses that joint and has constant length as the child rotates. The moment arm, the negative derivative of length with respect to angle, is zero. In a reviewer probe I placed anchors at `(-0.21, 0.06)` m on the parent and `(0.22, -0.07)` m in the child frame and routed the path through the origin. Over 121 poses from 0° through 120°, length varied by `5.55e-17` m and the largest centered finite-difference moment arm at `h = 1e-5 rad` was `5.55e-12` m. The proposed iff rejects this valid configuration. [Plan §3 D4](https://github.com/Corb1nW/Independent-Study/blob/57bfeaa7ac1beebceeff2b572aa3e2d5cd29c1e8/docs/plans/2026-11-11_squat_proof_of_concept_plan.md#L64-L72)

**Fix I would accept.** Compare declared in-scope crossings with the joints independently derived from each modeled path and the body tree. Compute leverage about every retained coordinate from geometry independent of the crossing declarations. Require a matching crossing or a documented modeled coupling wherever leverage is non-negligible. Record negligible leverage and omitted actions in the deviation register. Delete a known crossing while keeping the path and other data fixed and require the check to catch it.

Carry the demo's P1 follow-up into D4. Repair both the `CROSSES` and `ACTS_ON` links to each same-side knee for biceps femoris long head, semimembranosus, semitendinosus and rectus femoris. Scope the dependency on the lower-limb module with the repair. Use one of those known crossings for the deletion check. [Merged demo review](https://github.com/Corb1nW/Independent-Study/pull/45)

### D061-B02 · High · Evidence and claims · D6, P3 and the milestones

The Scherpereel article and the authors' lab page support the dataset choice. The study includes 25 lb squats, 12 participants, measured ground reactions and bilateral EMG, with inverse-dynamics moments derived from a gait2354-based model. The article explicitly licenses the article under CC BY 4.0. The repository files have a separate DOI and their terms and trial contents remain unverified. §3 commits to vendoring them. The fallback's assertion that author permission is required is also stronger than the accessible rights record supports. OpenAIRE shows a CC BY 3.0 NL entry alongside an unspecified entry for the Wang DOI. [Plan §3 D6](https://github.com/Corb1nW/Independent-Study/blob/57bfeaa7ac1beebceeff2b572aa3e2d5cd29c1e8/docs/plans/2026-11-11_squat_proof_of_concept_plan.md#L91-L114) · [Article](https://doi.org/10.1038/s41597-023-02840-6) · [Georgia Tech dataset](https://doi.org/10.35090/gatech/70296) · [Wang repository record](https://zenodo.org/records/6457662) · [OpenAIRE metadata](https://explore.openaire.eu/search/result?pid=10.5281%2Fzenodo.6457662)

§4 says the squat is validated after D6. §7 correctly allows the preregistered evaluation to fail. The final research claims need to depend on the outcomes, and the moment comparison should retain its status as a comparison to published inverse-dynamics estimates. [Plan §4](https://github.com/Corb1nW/Independent-Study/blob/57bfeaa7ac1beebceeff2b572aa3e2d5cd29c1e8/docs/plans/2026-11-11_squat_proof_of_concept_plan.md#L171-L180) · [Plan §7](https://github.com/Corb1nW/Independent-Study/blob/57bfeaa7ac1beebceeff2b572aa3e2d5cd29c1e8/docs/plans/2026-11-11_squat_proof_of_concept_plan.md#L206-L215)

**Fix I would accept.** Keep P3 as the preferred candidate. Check the exact squat files and their reuse and redistribution terms in the D6 scope. Identify the paper licence as such and make public vendoring conditional on the dataset terms. A pinned acquisition record can support reproduction when the files are acquired separately. Treat the fallback terms as pending confirmation. State that D6 completes the preregistered evaluation and reports all outcomes. Describe validation only for the measures and conditions that meet the criteria. D7 reports whether forward tracking meets its own criteria. The D6 and D7 decisions still set their metrics and tolerances.

### D061-B03 · Medium · Workflow · §5.2 and P4

The proposed diff-only tier includes executable viewers and tooling. Accepted D-051 incorporates the narrower D-047 documentation formatting and wording light path. D-061 only names D-040 as a decision it amends. This boundary affected the recent demo. At `aee9751`, the page regenerated byte for byte and 285 tests passed, yet an execution fixture showed playback stuck at 0.00 s at 120 and 144 Hz. The amended playback advanced correctly. [Plan §5](https://github.com/Corb1nW/Independent-Study/blob/57bfeaa7ac1beebceeff2b572aa3e2d5cd29c1e8/docs/plans/2026-11-11_squat_proof_of_concept_plan.md#L182-L191) · [D-051](https://github.com/Corb1nW/Independent-Study/blob/57bfeaa7ac1beebceeff2b572aa3e2d5cd29c1e8/docs/DECISIONS.md#L1274-L1289) · [Merged demo review](https://github.com/Corb1nW/Independent-Study/pull/45)

**Fix I would accept.** Keep diff-only review for D-047 documentation wording and formatting. For changed executable behavior, include a targeted run of the affected path and a regeneration check for affected generated outputs. Keep full review for changes affecting the model, data, scientific results or claims. If P4 introduces a separate workflow for executable changes, name the D-051 amendment and have Corbin decide on it explicitly. Builder rotation can be decided independently of the review tiers.

## Source check and disposition

I read the registered Scherpereel paper and Wang record, inspected the vendored Gait2392 model and checked OpenSim's installed classes. Additional sources for the record are the [Georgia Tech EPIC Lab dataset description](https://www.epic.gatech.edu/a-human-lower-limb-biomechanics-and-wearable-sensors-dataset-during-cyclic-and-non-cyclic-activities/) and the [OpenAIRE aggregation of the Wang DOI](https://explore.openaire.eu/search/result?pid=10.5281%2Fzenodo.6457662). Register them if the amended plan relies on them. The aggregate rights metadata is a lead for confirmation with the dataset record.

This is the first D-061 review. Amend the D4 consistency check, D6 evidence conditions and P4 review boundary before adopting the proposal as written. D4 remains the first build after its scope decision. The verified D1–D3 baselines and the merged demo review provide the starting evidence. Corbin decides on the plan and merge.

**Status: REVIEWED, NOT APPROVED.**
