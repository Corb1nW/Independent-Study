# Stage D2 build: post-merge review and execution check

Reviewed by (model): ChatGPT\
Built by (model): Claude\
Review date: 2026-11-10\
Reviewed SHA (full): `b9e96edb4a2e4a56e35679c8982152d5bc182315`\
Build PR: [#34](https://github.com/Corb1nW/Independent-Study/pull/34)\
Build base SHA: `02ca1f877dc0b69866109cc875e779d88d85eb11`\
Official result-generation SHA: `7ac0f2d2d83752d43f85a4221923f43f54e26b61`\
Merged main / review-record base SHA: `3821bd0c111a0b8abf4b90da638e0aac1246bd8b`\
Record branch: `reviews/chatgpt-d2-build-b9e96ed`

**Verdict: AMEND — two Medium configuration-validation defects.** The committed default results and OpenSim reference reproduce. The amendments below make the runner reject settings it would otherwise misinterpret or describe falsely; the reproduced default numbers remain supported.

**Status: REVIEWED, NOT APPROVED.** This is Corbin's requested post-merge review. A merge does not supply an independent check or remove the need to address a finding. No approval or reversal of an owner decision is inferred here.

## Scope, authority and independence

Corbin asked me to review the accidentally merged D2 build and run the tests/results myself. I read the Reviewer instructions, accepted D-059 with Amendments 1–3, the builder's handoff, applicable process decisions, and all substantive changed code/schema/data-generation/ontology sections. The build diff contains 21 files, five commits. Main at the recorded SHA differs from the build head only in records and prior review files; executable code, tests, configuration, data and result artifacts are the same. PR #34 first landed on the scope branch; PR #35 subsequently carried the build to main. Review and execution are pinned to the build head above.

This is independent execution of Claude-authored D2 work. My earlier method recommendations, hand fixtures, comparison code and probes are self-authored/self-checked; I do not claim independent verification of my own work. Inherited ChatGPT-authored Phase B regressions are also self-checks. Tests establish software behavior, not anatomical, physiological or clinical validity.

The review preserves the accepted static-optimization method, muscle set and declared simplifications. It checks their implementation rather than reopening the scope proposal or authenticating unseen Q58/Q59 chat quotations. The current source/clinical limitations continue to apply.

## Executed results

Environment: CPython 3.12.14, Linux x86_64/glibc 2.41; NumPy 2.3.5, SciPy 1.17.0, quadprog 0.1.14, Clarabel 0.11.1, OpenSim 4.6, pydantic 2.13.4/core 2.46.4, PyYAML 6.0.3, pytest 9.2.0, SymPy 1.14.0, Pint 0.26.2. Dependencies were installed into a separate review virtual environment. Git configuration was isolated with `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_NOSYSTEM=1`.

A hash-checked shallow/sparse checkout had exact HEAD `b9e96edb4a2e4a56e35679c8982152d5bc182315`, tree `0c61f945bf5482474070cd497e8d919a8fb42381`, and clean working status before and after. The unrelated binary phase-overview PDF remains excluded; no full binary-repository verification is claimed.

| Executed command/check | Result |
|---|---|
| `python -m pytest -q` | **213 passed**, exit 0, 56.08 s; one installed anyio/pytest deprecation warning |
| `python -m src.integrity` | **PASSED**, exit 0 |
| `python tools/review_cycle1_probes.py` | **9/9 REJECTED**, exit 0 |
| `python -m tools.build_segment_datasets --check` | All three generated datasets current, exit 0 |
| `python -m tools.make_d2_oracle --output <fresh-reference>` | Exit 0; 322 geometry states, 192 force states, plus 31 unmodified-model states |
| `python -m tools.run_phase_d2 --commit-sha b9e96edb4a2e4a56e35679c8982152d5bc182315 --d1-manifest results/phase_d/2026-11-04_d1_squat_runs_dd89fff.json --output <fresh-run>` | Exit 0; all verification passed; statuses below |
| `python -m tools.sensitivity_d2 --commit-sha b9e96edb4a2e4a56e35679c8982152d5bc182315 --output <fresh-sensitivity> --markdown <fresh-table>` | Exit 0; all recorded sensitivity solvers converged |
| `python -m tools.build_d2_page --manifest <manifest> --output <fresh-page>` | Exit 0, run for both the original and reproduced manifest |
| Reviewer-owned recursive comparator and OpenSim/configuration probes | Executed successfully; evidence below |
| Generated page JavaScript: `node --check` | Passed; actual browser rendering was blocked by environment permissions |

OpenSim warned that optional VTP visualization geometry files were missing. The numerical oracle completed; no mesh-dependent calculation was claimed.

### Own comparison against committed artifacts

The comparator walks every scalar leaf, checks keys and lengths, and reports numeric and nonnumeric changes separately. It does not import a builder comparator or discard numerical discrepancies.

| Artifact | Scalars / numeric values compared | Differences |
|---|---:|---|
| Fresh oracle vs `tests/data/d2_oracle_reference.json` | 44,597 / **44,034** | **Zero numeric differences**. Only Python, NumPy and platform metadata changed. Model, transformation-tool and matched-copy hashes agree. |
| Fresh D2 run vs `2026-11-10_d2_muscle_runs_7ac0f2d.json` | 155,605 / **153,757** | **Zero numeric differences**. Only top-level `commit_sha` changed from `7ac0f2d…` to `b9e96ed…`. |
| Fresh sensitivity vs `2026-11-10_d2_sensitivity_7ac0f2d.json` | 331 / **206** | Top-level commit plus three small changes in exponent-3 largest activation change; exact values below. |
| Viewer from original manifest | Byte comparison | **Byte-identical** to the committed viewer |
| Viewer from reproduced manifest | Byte comparison | Identical after one full commit-SHA replacement |
| Sensitivity Markdown | Byte comparison | Identical after the short commit-SHA replacement |

The sensitivity activation-change differences are:

| Body | Committed | Reproduced | Absolute difference |
|---|---:|---:|---:|
| Female | 0.20976174827413274 | 0.20976174827413502 | 2.2759572e-15 |
| Male | 0.2188262112390088 | 0.21882619281151905 | **1.8427490e-8** |
| Gait2392 | 0.21637049781894896 | 0.21637049781894613 | 2.8310687e-15 |

These differences do not change the reported conclusions. All 24 baseline and all 24 sensitivity input records were separately rehashed with raw SHA-256 and Git-filtered blob IDs.

| Default body | Largest stage-1 reserve | Muscle status | Other checks |
|---|---:|---|---|
| Female | 0 N·m | Feasible | D1 consistency, mechanics and optimizer passed; contact feasible; force domain in range |
| Male | 5.814680 N·m at 1.52 s | Flagged | Same verification results |
| Gait2392 | 6.361827 N·m at 1.52 s | Flagged | Same verification results |

The flagged profiles are declared model results, not test failures or evidence of human incapacity.

### Separate check of the knee explanation

I independently constructed the D1-matched XML from the retained source and joint datum; its SHA-256 is `de489305a77c0661239d7edafabdd06bf9574147d6da23deee59b8345a740531`, exactly the oracle's matched-copy hash.

Using OpenSim directly for tendon forces and moment arms, and separately written HiGHS interior-point LP calls, I checked all **301 Gait2392 sample states**. The largest difference from the stored reserve series was **3.8398841e-7 N·m**, consistent with using the manifest's six-decimal torque demands. The independently computed peak was 6.36182726043603 N·m.

Restoring **only the knee translation splines**, while retaining the z-axis ankle, locked subtalar/MTP, same muscles/force law and D1 torque demand, gave **t* = 0 at all 301 states**. This supports the stated knee-geometry explanation without also changing the ankle axis. It remains a counterfactual muscle-geometry comparison: moving-knee inverse dynamics and a physiologically validated squat were not computed.

## D2-B01 — Medium, must fix: configuration units are accepted but ignored

**Location:** [`tools/run_phase_d2.py:58`](https://github.com/Corb1nW/Independent-Study/blob/b9e96edb4a2e4a56e35679c8982152d5bc182315/tools/run_phase_d2.py#L58), especially :63–75; reserve classification :172–173 and reported allowance :198.

**Evidence:** in an isolated copy, I changed only the allowance's unit from `N*m` to `mN*m`, retaining numeric value 1 (and used the declaration probes in D2-B02 below). `load_config` accepted it. All **35 D2 tests passed**, and the full runner exited 0 with `verified_git_head_and_inputs` and optimizer verification passed. Its configuration says **1 mN·m**, but the summary says **1 N·m** and classification uses 1 rather than 0.001 N·m.

At male samples 138, 166 and 167, and Gait2392 samples 137, 138 and 167, the reserve lies between 0.001 and 1 N·m: the run incorrectly treats those samples as within the declared allowance. A separate load-only probe also accepted `1000 mN*m` as numeric 1000 N·m.

**Problem:** `unit` is a required field but its content is never checked or converted. The same weakness applies to the other numerical parameters. The runner can silently misinterpret a quantity and write contradictory units and feasibility information.

**Exact fix accepted:** require these canonical units before extracting bare numbers, rejecting unsupported units with `ValueError`:

| Parameter | Required unit |
|---|---|
| `epsilon_reserve` | `N*m` |
| `solver_band_delta` | `N*m` |
| `kkt_tolerance` | `1` |
| `second_solver_t_star_tolerance` | `N*m` |
| `second_solver_activation_tolerance` | `1` |
| `d1_consistency_N_m` | `N*m` |
| `passive_strain_sensitivity` | `1` |

Canonical-unit rejection suffices; adding unit conversion is not requested. Add rejection coverage for compatible noncanonical units and dimensionally wrong units, and retain the current valid-config execution. This is a configuration guard, not a change to the accepted reserve method or allowance.

## D2-B02 — Medium, must fix: unsupported force-law declarations become false manifest claims

**Location:** [`tools/run_phase_d2.py:76`](https://github.com/Corb1nW/Independent-Study/blob/b9e96edb4a2e4a56e35679c8982152d5bc182315/tools/run_phase_d2.py#L76), :249–264; [`src/muscles_d2.py:58`](https://github.com/Corb1nW/Independent-Study/blob/b9e96edb4a2e4a56e35679c8982152d5bc182315/src/muscles_d2.py#L58) and :377–381.

**Evidence:** `load_config` separately accepts `active_force_width_scale: 2.0` and `passive_fiber_force: included`. The isolated full-run probe used both declarations. All 35 D2 tests passed, the runner exited 0 and claimed verification passed, and the manifest retained both declarations. Every body's numerical series was **exactly identical** to the original width-1, passive-off baseline. The calculations use the fixed active curve and never add passive force in this runner.

**Problem:** only damping and tendon declarations are guarded. Other physical declarations are copied into the manifest without controlling or being checked against the implemented model. A run can therefore describe a force law it did not compute. This is a false provenance/model claim, not a request for an additional force-law option.

**Exact fix accepted:** treat the baseline physical settings as fixed declarations and reject unsupported or missing values before a run: active-force width scale 1, passive force ignored, activation dynamics ignored, rigid tendon, damping 0. The existing descriptive prose fields can remain prose; validate the physical option fields against the actual implementation. Add negative tests for the demonstrated passive and width changes. Implementing alternative baseline physics is not requested.

The executed full-run mutation was local-only commit `6000e425f666e3b1b82e5f017fa4aacda5520e28`, with parent equal to the reviewed head. Only `config/phase_d2_muscles.yaml` changed. No mutated commit or result was pushed. An initial `1000 mN*m` probe tripped the test that hardcodes numeric allowance 1 (34 passed, one expected default-value assertion failed); the subsequent unit-only change with numeric value 1 bypassed that assertion and produced the successful but inconsistent run described above. These mutation results are separate from the unmodified build's 213 passing tests.

## Earlier findings and nonblocking follow-through

| Earlier item | Build assessment |
|---|---|
| D2-R01 | L∞ stage 1 and strictly convex stage 2 implemented; signed reserve and independent solver checks pass. Closed method issue remains closed. |
| D2-R02 | Fiber velocity, normalization, constant thickness, one cos projection, domains and explicit force defaults implemented; full force/intermediate oracle comparison reproduced. |
| D2-R03 | Geometry, assembled-force, derivative/virtual-work and optimizer verification implemented substantially as specified; coverage refinements below are nonblocking. |
| D2-R04 | Branch policy and inclusive range implemented; no path-length differentiation across switches; all eight path jumps reported. |
| L01, L02 | Simplifications remain explicit; D1 inertial demand retained. |
| D2-A2-N01 | **Addressed:** t*, signed stage-2 reserves and delta are stored separately and explained in the manifest. |

**D2-BN01 / Low / boundary coverage (nonblocking).** `tools/make_d2_oracle.py:106–144` records geometry on both sides of six distinct switch edges (eight conditional points), but does not record exact-edge states or the promised left/right tendon-force values there. `tests/test_phase_d2.py:261–264` returns without exercising the lower normalized-length bound because that particular pennation fixture cannot reach it. Carry exact-edge/force transition samples and a reachable low-length fixture into a follow-up test refinement. The current branch rules and lower guard are present, the fresh oracle/default results pass, and no numerical defect is asserted from this coverage note. It does not block the verdict independently of B01/B02.

The new anatomy entities distinguish anatomical capabilities from model actuators, including the disclosed gastrocnemius moment-arm reversal. Schema 0.7.0 and ontology 0.2.0 changes preserve the prior hip module's standalone loading. Dataset regeneration/traceability and source-registration checks pass.

## Sources, limitations and handoff

**Sources checked:** unchanged retained Gait2392 XML and De Groote header; registered OpenSim source at `01683ac33568a3cb5eef2e445c7815f8220e8905`, including `SimmSpline.cpp`; OpenSim 4.6 execution; new source registry uses and new ontology evidence links. The relevant indexed excerpts of the same StatPearls chapters support the gross-anatomy additions: [Gastrocnemius](https://www.ncbi.nlm.nih.gov/books/NBK532946/), [Leg Anterior Compartment](https://www.ncbi.nlm.nih.gov/books/NBK539725/), [Thigh Muscles](https://www.ncbi.nlm.nih.gov/books/NBK482445/). Direct StatPearls pages were paywalled/inaccessible here and direct NCBI pages returned interstitials, so this is an indexed-excerpt check, not a claimed full-page reading. These are alternate URLs for already registered chapters, not three new sources; the builder can add the accessible mirror URLs/authors to their existing rows.

**Read/reasoned only:** accepted scope and records; source support/ontology interpretation; model simplifications and method semantics. **Not independently rerun:** the builder's exact eight-fault mutation script (not committed), Windows behavior and browser layout. Chromium launch failed with `socket() failed: Operation not permitted`; no screenshot or successful browser render is claimed. Generated HTML byte comparison and JS syntax did pass. No physiological or clinical validation is claimed.

**Out of scope:** new knee dynamics, changes to the muscle set, fresh source-model calibration, broader anatomy expansion, and owner-approval quotation authentication. They are not requested fixes in this review.

**Handoff:** Claude makes a follow-up fix PR for **D2-B01 and D2-B02** with configuration rejection tests, reruns the required regressions and shows that the valid default run remains unchanged. ChatGPT re-reviews that exact fix SHA; Corbin decides and merges. The nonblocking boundary note may accompany that work or a later test refinement.

**Must fix to close this post-merge build review: D2-B01 and D2-B02. Verdict: AMEND. Status: REVIEWED, NOT APPROVED.**

Supporting evidence (one authoritative verdict remains in this file):

- [Execution evidence and comparisons](evidence/d2_b9e96ed/execution_evidence.json): exact commands, environments, results, differences, hashes and mutation summaries.
- [Executed comparator source](evidence/d2_b9e96ed/compare_outputs.py).
- [Executed additional probe source](evidence/d2_b9e96ed/reviewer_probes.py).

The preserved scripts use the execution layout `<review-dir>/repo` for the pinned checkout and `<review-dir>/out` for regenerated outputs. Copy them into `<review-dir>` to rerun. The probe writes temporary matched model files; the mutation setup and its exact changed values/SHAs are recorded in the evidence JSON. These are review evidence, not new product implementation or claims of independently verified reviewer code.
