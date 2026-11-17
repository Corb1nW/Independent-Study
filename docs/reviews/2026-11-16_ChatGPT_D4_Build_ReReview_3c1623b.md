# Stage D4 build re-review

- **Date:** 2026-11-16
- **Reviewed by (model):** ChatGPT
- **Built by (model):** Claude
- **Build PR:** [#47](https://github.com/Corb1nW/Independent-Study/pull/47)
- **Reviewed SHA:** `3c1623b41ac775af795828acba6b3f4e4caf166e`
- **Base SHA:** `ee2b3df3df4f2eab8a3962d5d5fe51c075a8d257`
- **Previous reviewed SHA:** `d1ef9f2e032def97870258dc255628f73a0440fa`
- **Amended execution SHA:** `2f5c8a8a8187f68b6e4373c400623b1e61e8cb6e`
- **Original execution SHA:** `31a9d3fabf3c8b4777e09c7a5af51c8fb98df996`
- **Fix SHA:** `a5abd25cb3ffbf43ec15ed2a7b83f73c510a3bbd`
- **Verdict:** **AMEND**.
- **Status:** REVIEWED, NOT APPROVED

## Scope and independence

Reviewed the six-commit delta against D-062 Amendments 3–4 and the Q71–Q72 direction. The implementation and test files at the reviewed head match the amended execution commit. The later commits archive runs and update the records. The verifier commit `d0fc0087461152495e3e5d4c4093a63a09f4b78e` has the same workflow, scripts and published result files as the reviewed head. Claude wrote the fixes, tests and workflow. ChatGPT initiated both second attempts and inspected their job logs and artifact records. The reviewer probes below use the committed result data and the implementation. [Amendment 4](https://github.com/Corb1nW/Independent-Study/blob/3c1623b41ac775af795828acba6b3f4e4caf166e/docs/DECISIONS.md#L2613-L2648) · [Builder response](https://github.com/Corb1nW/Independent-Study/pull/47#issuecomment-6932406176)

## Reviewer-triggered execution

| Target | Python suite | OpenSim reference regeneration | D4 manifests and job evidence |
|---|---:|---|---|
| `31a9d3f` | 393 passed (119.10 s) | All three matched | Both matched with zero differing paths. [Attempt 2 job 133699479674](https://github.com/Corb1nW/Independent-Study/actions/runs/43977930176/job/133699479674), artifact `14283049460`. |
| `2f5c8a8` | 408 passed (124.55 s) | All three matched | Both matched with zero differing paths. [Attempt 2 job 133699455270](https://github.com/Corb1nW/Independent-Study/actions/runs/43977928194/job/133699455270), artifact `14281714852`. |

Both jobs checked out the requested full SHA and reported a clean worktree. Ubuntu 24.04 x86-64 ran Python 3.13.18, OpenSim 4.6, NumPy 2.5.3 and SciPy 1.18.1. The job ran `python -m pytest -q`, `python -m src.integrity`, `python tools/review_cycle1_probes.py`, and `python -m tools.build_segment_datasets --check`. Integrity and the dataset check passed, and all nine invalid-input probes were rejected in both jobs.

The jobs ran `tools.oracle_coverage` and regenerated all three references with `tools.make_d2_oracle`. They detected zero differences in 70,092, 75,811 and 90,275 numeric values respectively. They ran `tools.run_phase_d4` with each target SHA and the assembled and iliopsoas configurations. All four executions returned 0. The two jobs used the pinned verifier commit as the manifest comparison ref. Both new artifact uploads succeeded.

I separately compared the committed original and amended run records. All 319,620 stored series numbers across the two configurations, the per-run checks and statuses, and H1 agree. Every recorded input blob ID matches its file at the amended execution SHA.

## Disposition of the four findings

| Finding | Disposition | Evidence |
|---|---|---|
| D4-B01 · A2 coverage | **Partly resolved** | All six body and knee cases now report the complete expected field names and zero excess. The D1, D2 and D3 counts are respectively 6/3, 12/7 and 15/7 series/statuses. Missing, extra, changed and nonfinite cases have tests. The production timestamp and nested-series gaps below still allow a false pass. [A2 implementation](https://github.com/Corb1nW/Independent-Study/blob/3c1623b41ac775af795828acba6b3f4e4caf166e/tools/run_phase_d4.py#L281-L397) · [Tests](https://github.com/Corb1nW/Independent-Study/blob/3c1623b41ac775af795828acba6b3f4e4caf166e/tests/test_phase_d4.py#L759-L851) |
| D4-B02 · C1 per actuator | **Resolved** | C1 compares each actuator before making the per-muscle summary. The mutation test removes one gastrocnemius crossing and verifies that the affected actuator is named. The reproduced manifests report 14 and 16 matching actuators. [C1](https://github.com/Corb1nW/Independent-Study/blob/3c1623b41ac775af795828acba6b3f4e4caf166e/src/consistency.py#L116-L135) · [Mutation test](https://github.com/Corb1nW/Independent-Study/blob/3c1623b41ac775af795828acba6b3f4e4caf166e/tests/test_phase_d4.py#L971-L984) |
| D4-B03 · C4 structural basis | **Resolved** | The gate traces each of 13 represented structural entities and fails for an empty basis. The tests remove the evidence basis for a coordinate and for a joint. Both reproduced manifests report 13 traced entries. [C4](https://github.com/Corb1nW/Independent-Study/blob/3c1623b41ac775af795828acba6b3f4e4caf166e/src/consistency.py#L244-L325) · [Tests](https://github.com/Corb1nW/Independent-Study/blob/3c1623b41ac775af795828acba6b3f4e4caf166e/tests/test_phase_d4.py#L995-L1030) |
| D4-B04 · A9 active inputs | **Resolved** | Both reproduced inventories record 17 project modules, including the D1 loader and datum validator. The 35 baseline and 32 growth records all match the Git tree. An unverified late load is refused, and the test exercises a dirty D1 loader. [Inventory](https://github.com/Corb1nW/Independent-Study/blob/3c1623b41ac775af795828acba6b3f4e4caf166e/tools/run_phase_d4.py#L50-L86) · [Late-load guard](https://github.com/Corb1nW/Independent-Study/blob/3c1623b41ac775af795828acba6b3f4e4caf166e/tools/run_phase_d4.py#L485-L487) · [Tests](https://github.com/Corb1nW/Independent-Study/blob/3c1623b41ac775af795828acba6b3f4e4caf166e/tests/test_phase_d4.py#L1033-L1059) |

## Remaining blockers

### D4-B01 · High · A2 can still pass a changed time or series structure

`run_case` takes the reported time from `res["t"]` and puts it in both the published series and the regression input. `build_manifest` then replaces the regression input with a separate `np.linspace` timeline. The new timestamp test calls `run_case` and `regression` directly, so it does not exercise the overwrite on the build path. I replayed the production data flow on the committed Gait2392 moving-knee case. Shifting the emitted time of sample 7 from 0.070000 s to 0.070001 s still produces a compared value of 0.070000 s after the overwrite. The emitted timestamp differs and the A2 check still agrees. [Produced series and raw time](https://github.com/Corb1nW/Independent-Study/blob/3c1623b41ac775af795828acba6b3f4e4caf166e/tools/run_phase_d4.py#L202-L224) · [Overwrite](https://github.com/Corb1nW/Independent-Study/blob/3c1623b41ac775af795828acba6b3f4e4caf166e/tools/run_phase_d4.py#L448-L453) · [Test path](https://github.com/Corb1nW/Independent-Study/blob/3c1623b41ac775af795828acba6b3f4e4caf166e/tests/test_phase_d4.py#L759-L775)

`stored_precision_difference` flattens both sides before comparing length and values. I combined the first two frames of the committed D3 Gait2392 `muscle_path_xy_m` series into one. The resulting series has 300 frames instead of 301 and its 26,438 flattened numeric values are exactly equal. The current comparator accepts that change. The repo data and reviewer JavaScript replays show the two paths. The hosted suite exercised the committed Python tests. [Comparison helper](https://github.com/Corb1nW/Independent-Study/blob/3c1623b41ac775af795828acba6b3f4e4caf166e/tools/run_phase_d4.py#L119-L150)

**Required fix.** Preserve `run_case`'s actual time in `build_manifest` and test an altered emitted timestamp through that production path. Check the nested sequence shape before leaf-wise precision comparison, including each frame and actuator in the ragged muscle paths. Add a regression case for merging two frames with the same flattened leaf sequence.

### D4-B05 · Medium · The manual verifier can reinterpret or skip the requested comparison ref

The new manual input `compare_ref` is written as an output and expanded directly inside the later `run` script. For that route the user-supplied text can become shell code instead of a literal ref. Also, an unresolved explicit comparison ref makes `git ls-tree` fail and the script suppresses the error, marks comparison skipped and can return success. The two reviewer-triggered runs used the push route with the fixed verifier SHA and performed both comparisons. [Workflow input and output](https://github.com/Corb1nW/Independent-Study/blob/3c1623b41ac775af795828acba6b3f4e4caf166e/.github/workflows/d4-verify.yml#L34-L44) · [Shell interpolation](https://github.com/Corb1nW/Independent-Study/blob/3c1623b41ac775af795828acba6b3f4e4caf166e/.github/workflows/d4-verify.yml#L77-L78) · [Comparison handling](https://github.com/Corb1nW/Independent-Study/blob/3c1623b41ac775af795828acba6b3f4e4caf166e/ci/d4-verify/verify.sh#L63-L75) · [GitHub secure use guidance](https://docs.github.com/en/actions/reference/security/secure-use#use-an-intermediate-environment-variable)

**Required fix.** Pass the compare value as a quoted environment variable or argument and resolve it to a commit before comparison. Reject an invalid explicit ref, and fail when an explicit request cannot find an expected manifest. A documented run on an unarchived commit can report that comparison was unavailable. Exercise the manual route with a valid comparison commit and an unresolved requested ref.

**Required before agreeing to the build.** Close the two remaining A2 bypasses and correct the verifier's manual comparison handling. The reruns independently reproduce the current software results under the stated model assumptions.

**Status: REVIEWED, NOT APPROVED.**
