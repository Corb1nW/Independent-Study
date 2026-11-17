# Stage D4 Amendment 5 re-review

- **Reviewed by (model):** ChatGPT
- **Built by (model):** Claude
- **Reviewed SHA (full):** `0a503d1453a433c7706d5baf5a6d815e85546b30`
- **Base SHA (full):** `ee2b3df3df4f2eab8a3962d5d5fe51c075a8d257`
- **Build PR:** [#47](https://github.com/Corb1nW/Independent-Study/pull/47)
- **Amended execution SHA:** `af21e7881825f426f82f3591623a49d5ef8f9734`
- **Original execution SHA:** `31a9d3fabf3c8b4777e09c7a5af51c8fb98df996`
- **Hosted verifier SHA:** `ba4c9216ff00407fc3c97f4e9ddfe27745ab5a1a`
- **Scope:** Blocking findings D4-B01 (remainder) and D4-B05 under D-062 Amendment 5, Q73. Software verification under D-045 and D-051 item 10.
- **Independence:** Claude authored the implementation and verifier. ChatGPT wrote the previous findings and the independent probes and comparisons in this review.
- **Verdict:** AGREE
- **Must fix before Corbin decides:** None.
- **Status:** REVIEWED, NOT APPROVED

I checked the diff from `3c1623b41ac775af795828acba6b3f4e4caf166e`. The changes between the amended execution commit and the reviewed head consist of records and the archived manifests. The hosted verifier and the reviewed head have identical executable files and inputs. [D-062 Amendment 5](https://github.com/Corb1nW/Independent-Study/blob/0a503d1453a433c7706d5baf5a6d815e85546b30/docs/DECISIONS.md#L2652) · [Claude's response](https://github.com/Corb1nW/Independent-Study/pull/47#issuecomment-6933783529)

## Findings

**D4-B01 resolved.** The build keeps the time from `ma.run` for the published series and for A2. I shifted sample 7 of the actual Gait2392 moving-knee run by 1 µs through `build_manifest`. The published time changed from 0.070000 s to 0.070001 s and A2 flagged `t_s`. I also merged two emitted path frames while preserving the order and values of every actuator path. A2 identified 300 frames where 301 were stored and rejected the shape before comparing values. The mutated case failed, the other five passed, and the manifest exit code was 1. All six unmodified comparisons passed with zero excess. [Runner](https://github.com/Corb1nW/Independent-Study/blob/0a503d1453a433c7706d5baf5a6d815e85546b30/tools/run_phase_d4.py#L464-L521) · [Shape check](https://github.com/Corb1nW/Independent-Study/blob/0a503d1453a433c7706d5baf5a6d815e85546b30/tools/run_phase_d4.py#L125-L155) · [Regression tests](https://github.com/Corb1nW/Independent-Study/blob/0a503d1453a433c7706d5baf5a6d815e85546b30/tests/test_phase_d4.py#L857-L901)

**D4-B05 resolved.** The workflow passes inputs through environment variables and quoted arguments. Its input script validates the syntax, and `verify.sh` resolves the comparison ref to one commit. I independently confirmed that an invalid literal produces no step outputs, and that an unresolved ref and a resolved ref without required manifests stop before running the checks. The required manual rerun compared both manifests successfully. The local run at the reviewed head exercised the optional case and explicitly reported both comparisons as unavailable for that SHA. [Workflow](https://github.com/Corb1nW/Independent-Study/blob/0a503d1453a433c7706d5baf5a6d815e85546b30/.github/workflows/d4-verify.yml#L42-L55) · [Verification script](https://github.com/Corb1nW/Independent-Study/blob/0a503d1453a433c7706d5baf5a6d815e85546b30/ci/d4-verify/verify.sh#L25-L42)

**D4-B02, D4-B03 and D4-B04 remain resolved.** The per-actuator C1 check and the C4 structural evidence checks are intact. I matched the archived input inventories against the amended commit's Git blob IDs and the raw input SHA-256 hashes. All 35 assembled inputs and 32 iliopsoas inputs verified.

## Execution

I ran the verifier in a clean detached checkout at the reviewed SHA, with Python 3.13.5 on Linux x86-64 and the locked packages (OpenSim 4.6, NumPy 2.5.3, SciPy 1.18.1). It exited 0. Pytest passed 411 tests, integrity passed, all 9 invalid inputs were rejected, and the dataset check passed. Three oracle coverage checks passed, and all three regenerated references had zero numeric or provenance differences across 70,092, 75,811, and 90,275 numeric values. Both D4 runners exited 0.

```bash
bash repo/ci/d4-verify/verify.sh repo \
  0a503d1453a433c7706d5baf5a6d815e85546b30 \
  0a503d1453a433c7706d5baf5a6d815e85546b30 out-head optional
```

I triggered these second attempts on GitHub Actions with Python 3.13.18 and the same locked versions of OpenSim, NumPy and SciPy.

| Target | Comparison route | Pytest | Manifest comparison | Job |
|---|---|---:|---|---|
| `af21e78` | Default ref | 411 passed | 0 differing paths in each manifest | [133725251358](https://github.com/Corb1nW/Independent-Study/actions/runs/43987261365/job/133725251358) |
| `af21e78` | Explicit ref, comparison required | 411 passed | 0 differing paths in each manifest | [133725233052](https://github.com/Corb1nW/Independent-Study/actions/runs/43987271547/job/133725233052) |
| `31a9d3f` | Default ref | 393 passed | Exit 1 at manifest comparison, 43 and 49 differing paths | [133725256696](https://github.com/Corb1nW/Independent-Study/actions/runs/43987261019/job/133725256696) |

Integrity, the input probes, the dataset check and the three OpenSim reference comparisons passed in all three jobs. I inspected the author-triggered jobs for rejected syntax, an unresolved ref and the unarchived target. They corroborate the local input and comparison checks. [Rejected syntax](https://github.com/Corb1nW/Independent-Study/actions/runs/43987278315/job/133718576868) · [Unresolved ref](https://github.com/Corb1nW/Independent-Study/actions/runs/43987275190/job/133718567816) · [Unarchived target](https://github.com/Corb1nW/Independent-Study/actions/runs/43987261574/job/133718513634)

## Independent record comparison

- I compared both local manifests from the exact reviewed head against the committed `af21e78` manifests, recursively by field, sequence shape and value. Each differed in exactly one field, `commit_sha`, which correctly identified the checkout used.
- Comparing the original and amended archives directly, all 319,620 stored run-series values, run statuses, checks and H1 agreed. The Amendment 4 and 5 manifests differ at three paths each: `commit_sha`, and the Git blob ID and SHA-256 for `tools/run_phase_d4.py`.
- I opened the archived output from the failed hosted baseline comparison and compared it directly with the committed `31a9d3f` records. The 43 assembled and 49 iliopsoas differences were in unrounded diagnostics. Nine per manifest were C3/C5 extreme moment arms, with a maximum absolute change of `8.67e-19 m`, which the comparison script treats as strict equality fields. The stored series, statuses, check verdicts and H1 agreed. I reran both original D4 commands locally at `31a9d3f`. Both exited 0 and each manifest matched its archive exactly.

Corbin decides on the Stage D4 build.
