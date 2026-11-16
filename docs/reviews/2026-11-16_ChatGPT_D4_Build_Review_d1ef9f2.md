# Stage D4 build review

- **Date:** 2026-11-16
- **Reviewed by (model):** ChatGPT
- **Built by (model):** Claude
- **Build:** [PR #47](https://github.com/Corb1nW/Independent-Study/pull/47)
- **Reviewed SHA:** `d1ef9f2e032def97870258dc255628f73a0440fa`
- **Base SHA:** `ee2b3df3df4f2eab8a3962d5d5fe51c075a8d257`
- **Official run SHA:** `31a9d3fabf3c8b4777e09c7a5af51c8fb98df996`
- **Verdict:** **AMEND** on the D4 build.
- **Status:** REVIEWED, NOT APPROVED

## Scope and independence

I reviewed the build against D-062 and Amendment 1, accepted in Q70. The current base already contains the two scope PRs. Comparing its files to the reviewed tree isolates the build delta. The Q70 quote in the decision log matches the build handoff. Claude authored the implementation and the runs. I authored the earlier scope reviews and the independent probes of the committed build data described here. [Accepted criteria](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/docs/DECISIONS.md#L2349-L2373) · [Build record](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/docs/DECISIONS.md#L2480-L2578)

## Blocking findings

### D4-B01 · High · A2 regression can pass without comparing required series and statuses

D-062 A2 requires every series and status in the pinned D1–D3 manifests to agree at stored precision. The actual D4 regression report omits `points_m` and `t_s` for D1, and `d1_points_m` and `t_s` for both D2 and D3. These position series contain the hip, knee, centers of mass, and HAT drawing point. It omits `optimizer_verification` for D2 and D3 and other status keys. This follows directly from the allowlist in the configuration. Additionally, the runner skips a configured series when it is absent in a manifest, and the finite-expected/NaN-new path can return zero excess because the NaN comparison is false. For example, changing the stored D3 knee position and its optimizer status leaves all inputs to the configured comparisons identical, so A2 would still report a pass. [A2](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/docs/DECISIONS.md#L2356) · [Configuration](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/config/phase_d4_assembled.yaml#L30-L59) · [Comparison](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/tools/run_phase_d4.py#L231-L270) · [Numeric check](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/tools/run_phase_d4.py#L84-L102) · [Official D4 output](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/results/phase_d/2026-11-16_d4_assembled_runs_31a9d3f.json)

**Fix.** Compare the full required key sets for each pinned manifest, including time, the assembled positions under their legacy labels, and statuses. State any semantic status mappings explicitly. Fail on missing required fields and on a nonfinite replacement for a finite value. Test a changed body-point sample, an omitted field, and a changed status. Regenerate the official results.

### D4-B02 · High · C1 combines actuator crossings before applying a per-actuator rule

C1 in D-062 requires each actuator's derived joint crossings to agree with its represented muscle. The implementation unions all paths for a muscle first. The current paths agree individually. A reviewer probe using the two gastrocnemius actuator paths removed the knee crossing from the medial path's derived set, leaving the lateral path intact. The union still equaled the muscle's two declared joints and passed the implemented C1 predicate. Comparing each path separately caught the omission. [C1 requirement](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/docs/DECISIONS.md#L2321-L2322) · [C1 implementation](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/src/consistency.py#L96-L125)

**Fix.** Compare each actuator's derived crossings with the applicable declared modeled crossings and identify the actuator in a failure. Retain the muscle-level summary for A4. Add a negative test that removes the crossing from one of two actuators representing the same muscle.

### D4-B03 · High · C4 skips entity-level traceability for model structure

C4 requires each represented entity to resolve to evidence. The implementation checks muscles, crossing and action edges, actuators, and consumed observations. It relegates missing segment, joint and coordinate evidence to a list outside the pass condition. The official manifest reports C4 passed while listing 12 such structural entities, including the knee joint and its coordinate. A pooled gate over numeric observations cannot establish an entity-specific chain for how that joint or coordinate is represented. The implementation also has no failing C4 path when the represented hip joint loses its evidence and the numeric inputs stay valid. [C4 requirement](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/docs/DECISIONS.md#L2332) · [C4 implementation](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/src/consistency.py#L234-L262) · [Official D4 output](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/results/phase_d/2026-11-16_d4_assembled_runs_31a9d3f.json)

**Fix.** For each structural element in the assembled specification, record and check an entity-level link to registered evidence or to the sourced records and declared assumptions that justify its representation. A model convention may be explicitly identified as such. An element with no trace should fail C4 and name the entity. Test removal of one represented joint or coordinate's evidence link.

### D4-B04 · High · A9 grants verified provenance with active files outside the Git check

Every listed blob ID matches the tree of the run commit. The input inventory omits `src/squat_d1.py`, even though the D4 runner calls its configuration loader for motion, gravity and contact parameters. It also omits `src/datum_model.py`, which supplies the validator used by the quantitative schema. Git verification loops over the supplied paths and does not check these files. A working-tree edit to the D1 loader can therefore alter resolved parameters without invalidating the manifest's `verified_git_head_and_inputs` status. The growth run has no A2 regression to reveal an altered input numerically. [D-055 C1](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/docs/DECISIONS.md#L1424-L1431) · [Runner input list](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/tools/run_phase_d4.py#L38-L45) · [Loader call](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/tools/run_phase_d4.py#L312-L329) · [Datum validator import](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/src/quantitative.py#L39-L48) · [The Git check](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/src/run_manifest.py#L90-L110)

**Fix.** Put the active project-code dependencies, including the two omitted modules, through the existing HEAD-and-blob verification. Add a test where a dirty D1 loader prevents a verified D4 manifest. Repeat the official runs at the corrected, clean commit.

## Independent checks of committed artifacts

| Check | Result |
|---|---|
| Moving-knee output vs D3 | Identical across 146,136 comparable numeric values in 14 stored series and three bodies. This includes timestamps, torques, contact series, activations, tendon forces, reserves and muscle paths. D4 provides per-case fixed-knee regression summaries. |
| Growth and H1 | The growth commit changes four data, configuration and reference files. The growth reference covers 16 actuators and 331 geometry rows, including hip-switch cases. The saved near-standing co-activation calculation reproduces 0.112699, 0.130222 and 0.135927 for female, male and Gait2392 in D3 and zero at saved precision for all three with iliopsoas. |
| References and observations | The regenerated D2/D3 geometry, force, unmodified-model and applicable kinematics arrays equal their earlier versions. The 121 pre-existing muscle observations and 30 segment observations match after removing the added model-entity link. The growth appends 20 muscle observations. |
| Anatomy and topology | The eight bilateral muscles receive the 16 expected knee links. Path-frame routes for the committed actuators agree individually with their declared modeled crossings. The committed C3 data record the fixed-knee direction deviations. The endpoint rule in the specification resolves hip via the bony pelvis and records the merged MTP exception. |
| Run commit audit | All 29 baseline and 27 growth input blob IDs agree with their paths at the claimed run commit, within the recorded inventories. B04 identifies active code missing from those inventories. |

Sources checked include the existing registered StatPearls thigh and hip entries. The accessible thigh chapter supports the modeled knee actions and the hip chapter supplies the innervation information Claude described. The knee-edge evidence is in the additions. [Thigh muscles](https://www.ncbi.nlm.nih.gov/sites/books/NBK482445/) · [Hip](https://www.ncbi.nlm.nih.gov/sites/books/NBK526019/) · [Knee relationships](https://github.com/Corb1nW/Independent-Study/blob/d1ef9f2e032def97870258dc255628f73a0440fa/ontology/lower_limb_sagittal.yaml#L916-L1002)

I used JavaScript probes over pinned GitHub files and static inspection. The executor was unavailable for a fresh Python test suite, full inverse dynamics, optimizer, or OpenSim execution. Claude reports 393 passing tests, integrity passed, 9/9 probes rejected, datasets current and all three reference coverage checks passing at the run commit. Those execution results remain author-reported. The comparisons above check the saved numerical evidence and the regression, consistency and provenance contracts.

**Required before agreeing to the build.** Resolve D4-B01 through D4-B04 and attach regenerated run records.

**Status: REVIEWED, NOT APPROVED.**
