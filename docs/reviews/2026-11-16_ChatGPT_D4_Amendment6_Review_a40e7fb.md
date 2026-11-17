# Stage D4 Amendment 6 review

- **Reviewed by (model):** ChatGPT
- **Built by (model):** Claude
- **Reviewed SHA (full):** `a40e7fbcc6e96a2ed7259f6912031e1b0e514727`
- **Base SHA (full):** `c744788d87f61d453743d5097288ec3101b3c697`
- **PR:** [#49](https://github.com/Corb1nW/Independent-Study/pull/49)
- **Scope:** D-062 Amendment 6 and its verifier acceptance criteria under D-045, plus the Q74 and A-20 records.
- **Independence:** I reviewed and ran Claude's comparator and model. I wrote the local comparison probes and the scratch comparison rule described below.
- **Verdict:** AMEND
- **Must fix before Corbin decides:** D4-V01.
- **Status:** REVIEWED, NOT APPROVED

## D4-V01 (High) — The comparator accepts malformed fields and fractional sample indices

`classify()` exempts any path matching `RESIDUALS` before it checks what actually changed. In the official assembled `af21e78` manifest, `/runs[0]/verification/largest_kkt_residual` is a finite float. Removing it or replacing it with `false`, `NaN`, a string or a list each returned exit 0 and reported the difference as residual-level. The same path condition can swallow missing keys and shape changes.

`within_rounding()` also treats integers and floats as interchangeable inputs to the tolerance. On the same real manifest, changing the female fixed-knee C3 `extreme_sample` from `150` to `150.0000000000375` returned exit 0 and reported rounding-level. That field identifies a discrete sample. A one-unit change to the rounded timestamp returned exit 1, and an adjacent floating-point C3 moment arm returned exit 0 as intended. [Comparator](https://github.com/Corb1nW/Independent-Study/blob/a40e7fbcc6e96a2ed7259f6912031e1b0e514727/ci/d4-verify/compare_manifest.py#L27-L71) · [Existing tests](https://github.com/Corb1nW/Independent-Study/blob/a40e7fbcc6e96a2ed7259f6912031e1b0e514727/tests/test_d4_verify_tools.py#L61-L93)

**Required fix.** Compare keys, lengths and leaf types exactly. Apply the residual exemption and the rounding tolerance only to changed pairs of finite floats. Keep integers exact and keep the stated equality rule for two NaNs. Add CLI or `main()` regression cases on an official manifest for a missing residual, a residual replaced by a boolean or NaN, and a fractional sample index.

I exercised this rule in a scratch copy of Claude's comparator. It accepted all four real Haswell manifests and rejected all the malformed variants above. The same scratch copy accepted the finite residual and adjacent-float controls.

**Margin wording.** Using the series' actual decimal precisions, the smallest normalized one-unit step across the four official manifests is about `3.33e-10` at the final timestamp (`3.0` → `3.000000001` s), about 333 times the proposed tolerance. The comparator rejects it. Update the stated minimum in the comparator documentation, the test label and D-062 Amendment 6. [Series precision](https://github.com/Corb1nW/Independent-Study/blob/a40e7fbcc6e96a2ed7259f6912031e1b0e514727/tools/run_phase_d4.py#L225-L237)

## Independent execution

I ran `ci/d4-verify/verify.sh` locally at `a40e7fbcc6e96a2ed7259f6912031e1b0e514727` with the locked packages on Linux x86-64 (Python 3.13.5, OpenSim 4.6, NumPy 2.5.3 and SciPy 1.18.1). **422 tests passed.** Integrity, all nine invalid-input probes, the dataset check, and all three oracle coverage checks passed. The three regenerated OpenSim references matched exactly and both D4 runners exited 0. I independently compared their manifests to the committed `af21e78` files. Only `commit_sha` differed, as expected for the reviewed checkout.

I ran both D4 configurations locally with `OPENBLAS_CORETYPE=Haswell` in detached worktrees at `31a9d3fabf3c8b4777e09c7a5af51c8fb98df996` and `af21e7881825f426f82f3591623a49d5ef8f9734`. NumPy and SciPy both reported Haswell. For each checkout, I ran the two `python -m tools.run_phase_d4 --config config/phase_d4_<kind>.yaml --commit-sha <sha> --output <path>` commands and compared the regenerated files to the committed archives with the base and PR comparators.

| Execution | Configuration | Differing paths | Residual | Rounding | Other with PR comparator |
|---|---|---:|---:|---:|---:|
| `31a9d3f` | Assembled | 43 | 34 | 9 | 0 |
| `31a9d3f` | Iliopsoas | 48 | 39 | 9 | 0 |
| `af21e78` | Assembled | 43 | 34 | 9 | 0 |
| `af21e78` | Iliopsoas | 48 | 39 | 9 | 0 |

The old comparator exited 1 on all four, with nine differences outside the residual group each time. The PR comparator exited 0 on all four. All 319,620 stored series numbers per execution, statuses, per-run check verdicts and H1 matched their archives. The largest rounding difference was `8.67e-19 m`. At `31a9d3f` all 43 assembled paths matched the earlier failed hosted report, and the same nine C3/C5 paths appeared in the iliopsoas run. [Earlier hosted baseline](https://github.com/Corb1nW/Independent-Study/actions/runs/43987261019/job/133725256696)

I triggered attempt 2 of the hosted Haswell run at `31a9d3fabf3c8b4777e09c7a5af51c8fb98df996`. The job used verifier `d5eec5794d53972219d8766f6c5fc79afd81f0ab`, which differs from the reviewed head only in the records. On AMD EPYC and Python 3.13.18, 393 tests passed, all three OpenSim references were identical, and the 43 assembled and 49 iliopsoas differences were all residual- or rounding-level with zero other differences. I also checked the logs for the author-triggered Haswell run at `af21e78`, which reports 43 and 48 differences and zero other. The Sandybridge and default hosted runs in the handoff are author-run evidence. [Reviewer-triggered baseline](https://github.com/Corb1nW/Independent-Study/actions/runs/43995780385/job/133762784436) · [Author-triggered amended execution](https://github.com/Corb1nW/Independent-Study/actions/runs/43995783150/job/133747385692)

## Records

Q74 has the same wording in the PR handoff and the decision log. The verbatim quote is attributed to Claude's session. GitHub independently confirms that `Corb1nW` merged PR #47 into `b74d88852da6c66b25b1c3fd697db79c856f8f9c` at 20:12:01 ET and PR #48 into `c744788d87f61d453743d5097288ec3101b3c697` at 20:12:14 ET on November 16, matching A-20. [Q74 and A-20](https://github.com/Corb1nW/Independent-Study/blob/a40e7fbcc6e96a2ed7259f6912031e1b0e514727/docs/DECISIONS.md#L188-L189) · [Build PR #47](https://github.com/Corb1nW/Independent-Study/pull/47) · [Build review PR #48](https://github.com/Corb1nW/Independent-Study/pull/48)

The recommendation applies to the Amendment 6 verifier in PR #49. The Stage D4 build decision is recorded separately in Q74.
