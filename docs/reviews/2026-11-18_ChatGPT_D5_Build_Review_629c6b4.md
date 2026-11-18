# Stage D5 build review

- **Reviewed by (model):** ChatGPT
- **Built by (model):** Claude
- **Reviewed SHA (full):** `629c6b454c126bf5008e301d50afed1f0f8a2678`
- **Base SHA (full):** `c5d082c05e66db0ab21925fbbb795f2e006f6703`
- **Official execution SHA (full):** `4c0e320df79c1208602bd409285781ca95c456b5`
- **PR:** [#55](https://github.com/Corb1nW/Independent-Study/pull/55)
- **Scope:** D-063 with Amendment 1, its implementation and Amendment 2 build record; A1–A8, H2–H4, the D5 demo, and Claude's F1/A5/gemelli questions. Blocking findings only.
- **Independence:** Claude wrote the implementation. The scope remedies originated in my earlier recommendations; reassessing that design is self-checked. I independently executed Claude's implementation and wrote my own comparisons and probes; my comparison code is reviewer-authored evidence, not independently verified software.
- **Verdict:** **AMEND**
- **Must fix before Corbin decides:** **D5-B01**, the false F4 interpretation in the record and demo.
- **Status:** **REVIEWED, NOT APPROVED**

The computations reproduce, including the hypotheses. The one blocking correction concerns the explanation presented with those results.

## D5-B01 (High) — Correct the knee-extension and shortfall explanation

**Locations:** [D-063 Amendment 2, F4](https://github.com/Corb1nW/Independent-Study/blob/629c6b454c126bf5008e301d50afed1f0f8a2678/docs/DECISIONS.md#L2906); [demo builder's F4](https://github.com/Corb1nW/Independent-Study/blob/629c6b454c126bf5008e301d50afed1f0f8a2678/tools/build_squat_demo_d5.py#L141); the same generated finding in `SQUAT_DEMO_D5.html`'s DATA.

The record says Gait2392 adds no knee extensor and therefore the fixed-knee shortfall is not relieved. The demo says D5 cannot relieve the vasti for that reason. These statements conflict with the model's newly added TFL path, the already recorded F2 deviation, and the independently reproduced H4 result.

At 1.52 s in the male fixed-knee case, my separate reconstruction of the recruitment problem gives:

| Quantity | D4 growth, 16 actuators | D5, 43 actuators |
| --- | ---: | ---: |
| Required knee moment, N·m | -87.311339 | -87.311339 |
| Minimum largest reserve t*, N·m | 5.814680 | 3.371648 |
| Rectus-femoris knee moment, N·m | -13.299542 | -15.178471 |
| TFL knee moment, N·m | No actuator | -0.187238 |

Negative knee moment is extension in this coordinate convention. The new TFL actuator has a -0.006732790 m knee moment arm at this pose. It supplies knee extension in the model even though its sourced anatomical capability is knee flexion, the discrepancy already disclosed as F2. The three vasti remain fully active at this pose, but their saturation does not establish that the shortfall was unchanged or cannot be relieved. Recruitment also reallocates existing muscles. I do not attribute the whole reserve reduction to TFL.

**Exact fix I would agree to:** replace F4 in the decision record and demo builder with, for example:

> The three vasti still reach full activation near the bottom. D5 reduces the fixed-knee maximum reserve from 5.815 to 3.372 N·m for the male body and from 6.362 to 3.700 N·m for Gait2392, without eliminating the shortfall. The newly added TFL path supplies knee-extension moment in this model, despite its sourced knee-flexion action (F2).

Regenerate `SQUAT_DEMO_D5.html`. Remove the unsupported “no knee extensor” causal explanation. The saved run data and report already contain the correct numbers; this finding requires a correction to their interpretation.

## Execution performed

Clean detached checkouts were used for the reviewed head and official execution commit. Environment: Linux x86_64; Python **3.13.5**, OpenSim **4.6**, NumPy **2.5.3**, SciPy **1.18.1**, Clarabel **0.11.1**, quadprog **0.1.14**, pydantic **2.13.5**, PyYAML **6.0.3**, pytest **9.1.1**. A test-only Git configuration supplied an identity for tests creating commits.

At the reviewed head:

| Check | Result |
| --- | --- |
| `python -m pytest -q` | **505 passed, 1 skipped**, 223.89 s |
| `python -m src.integrity` | **PASSED** |
| `python tools/review_cycle1_probes.py` | **9/9 invalid probes rejected**, exit 0 |
| `python -m tools.build_segment_datasets --check` | Exit **0**, current |
| D5 fixed/moving `tools.oracle_coverage` | **COVERAGE OK** for each 43-actuator reference |
| D5 results report regenerated | **Byte identical** |
| D5 demo regenerated | **Byte identical** |
| `git diff --check` against the base | Exit **0** |

The skip is the existing D4 working-ontology fixture at `tests/test_squat_demo_d4.py:101`: the ontology has changed since that archived run, so its archived-blob route is covered by the rebuild test. I reran that file with `-rs`: 18 passed and the same explained skip. It is not a skipped D5 result or page test.

I ran `tools.run_phase_d4` with `config/phase_d5.yaml` at both the reviewed head and `4c0e320df79c1208602bd409285781ca95c456b5`. At the execution commit I also ran `config/phase_d4_assembled.yaml` and `config/phase_d4_iliopsoas.yaml`. **All four runs exited 0 with verification passed and verified provenance.**

### My comparisons

I wrote a recursive JSON comparison that checks key sets, list lengths, leaf types, strings, booleans, numbers and paired NaNs. It does not import the project's comparator or suppress residual differences. I separately compared run series, statuses, reserve summaries and torque shares, and recomputed H2–H4 from the rerun's values.

- **Official D5 replay:** the regenerated manifest is **byte identical** to the committed `2026-11-17_d5_runs_4c0e320.json`: **0 differences**, including 443,675 numeric leaves.
- **D5 at PR head:** only the top-level execution commit SHA differs; every other field is equal.
- **D4 compatibility:** both regenerated manifests retain **exactly equal series, statuses, reserve summaries, regression/oracle results and H1**. The two series comparisons cover 147,942 and 171,678 floating-point values. Each complete manifest has 61 changed paths: provenance/input inventory, the documented C3/C5 changes and six second-solver activation-difference diagnostics. The older C5 modelled-joint unactuated list grows 17 → 28 in assembled D4 and 15 → 26 in the growth run.
- **OpenSim regeneration:** I regenerated all five committed references with OpenSim 4.6. The following numeric leaves are **exactly equal**; each file differs only in `provenance.python` and `provenance.platform`:

| Reference | Specification / knee | Equal numeric leaves |
| --- | --- | ---: |
| D5 fixed | squat_d5 / fixed | 232,726 |
| D5 moving | squat_d5 / moving | 238,445 |
| D2 | squat_d2 / fixed | 70,098 |
| D3 | squat_d2 / moving | 75,817 |
| D4 growth | squat_d4_iliopsoas / moving | 90,281 |

The runtime differences are the author's Python 3.13.18 versus 3.13.5 and the host platform string. Structure, numeric values and all other metadata match.

### Hypotheses, independently recalculated

| Hypothesis | Result |
| --- | --- |
| H2 | Supported: moving-knee maximum t* is **0.0** for all three bodies |
| H3, male | Middle/lower gluteus-maximus peaks **1.0/1.0 → 0.556306/0.557922** |
| H3, Gait2392 | Peaks **1.0/1.0 → 0.568296/0.569947** |
| H4, male | Fixed-knee maximum t* **5.814680 → 3.371648 N·m** |
| H4, Gait2392 | **6.361827 → 3.700210 N·m** |

H3 and H4 are supported; H4 remains nonzero, as the report says.

## Answers to Claude's review questions

**F1 — Row scaling is acceptable.** Each strictly positive row scale divides C, tau and its reserve band together. It preserves that inequality's feasible set and leaves the objective unchanged. The zero-row fallback uses 1.0. The primary quadprog recruitment is unchanged; tolerances and the final agreement gate remain in place.

I reproduced the male fixed-knee sample 120 using the pre-D5 `stage2_second` function extracted from the base commit and the amended function on the same problem. The former returns `AlmostSolved` and differs from the primary activation vector by **0.001286714554**; the amended function returns `Solved` and differs by **1.5564e-12**. Primary KKT residuals are at most **7.11e-15**, and the independently evaluated scaled-row slack identity differs by at most **3.34e-17**. This is a sound numerical cross-check correction.

**A5 — The numerical compatibility requirement is met.** I agree that the shared ontology's expanded C5 inventory is an expected consequence of D5. It should remain explicitly distinguished from an identical whole manifest. The build record already discloses the 15 → 26 change. The extra inventory entries and new policy fields do not change D4's physical results. This is my recommendation on the stated reading of A5; Corbin decides the build.

**Gemelli and direction exceptions — Acceptable within the agreed scope.** The Delp table lists a single gemelli entry and does not establish its precise anatomical decomposition. The two-gemellus mapping is expressly labelled an interpretation, as D-063 permits; the source numerical actuator is retained. All 20 deviation declarations are bounded by actuator, coordinate, variant and motion, with their basis retained.

On D5's actual 43-actuator specification, my own mutations confirm that reversing biceps femoris long head's knee capability fails with the matched OpenSim references on **both knees**. Removing the TFL declaration fails; changing the confirming reference's TFL sign also fails. The unmodified case passes. The suite additionally covers stale declarations, lumped evidence/crossing failures and nested inheritance.

## Earlier scope findings and data boundaries

- **D5-R01:** Resolved in the implementation, with the bounded-rule probes above.
- **D5-R02:** Resolved: the oracle uses the shared recursive resolver, tools read the module list, and C5 places all 102 muscle entities into represented or unactuated groups. The actual data commits `1510872` and `aaf1cf7` change no `src/` or `tools/` files, satisfying A2.

## Sources, nonblocking notes and limits

Checked the source registry and new evidence records, the accessible StatPearls foot and gluteus-medius chapters, the PubMed TFL excerpt, the Delp parameter table, and indexed compartment-chapter material. The TFL excerpt supports its sourced knee-flexion action; it does not justify rewriting that capability to match the model. All of these sources are already registered; this review introduces no new source requiring registration.

The full hip, thigh and anterior-compartment chapter text was not independently available in this session; those complete readings remain author-reported. Source spot checks and executable consistency checks do not establish anatomical or physiological validity.

**Nonblocking N1 — Conservative anatomical omissions.** The long toe extensors' ankle-only ontology records explicitly omit toe crossings because the selected chapter does not name the joints, while the foot chapter describes distal phalangeal attachments. The intrinsic-foot records also use conservative action/crossing subsets, and the chapter contains the already reported count ambiguity. Preserve those limits for the later foot/out-of-plane model work; an omitted relationship must not become an assertion that the muscle does not act across that joint. No extra D5 numerical fixture or foot simulation is required for this review.

**Nonblocking N2 — Version label.** The proposed `hip.yaml` label update is reasonable housekeeping. If it changes an input, any resulting official rerun must retain traceable provenance. It is not the blocking finding here.

**Read or reasoned only:** source interpretation, exact row-scaling equivalence, anatomical and planar-model limitations, owner-record consistency with the handoff.

**Not run:** hosted Actions and interactive browser rendering. Local execution reproduced the results directly; the demo's deterministic generation and embedded-data checks passed. Claude's browser screenshots/rendering observations remain author-reported.

**Next:** Claude corrects D5-B01 and regenerates the page; ChatGPT re-reviews that pinned revision; Corbin decides and merges. **REVIEWED, NOT APPROVED.**
