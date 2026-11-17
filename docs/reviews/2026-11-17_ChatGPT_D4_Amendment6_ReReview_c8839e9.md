# Stage D4 Amendment 6 re-review

- **Reviewed by (model):** ChatGPT
- **Built by (model):** Claude
- **Reviewed SHA (full):** `c8839e95f1c97de54e7e55bd0803b79c1df3a6b3`
- **Base SHA (full):** `c744788d87f61d453743d5097288ec3101b3c697`
- **Previous reviewed SHA:** `a40e7fbcc6e96a2ed7259f6912031e1b0e514727`
- **Implementation SHA:** `a2bab546ea422c18a769a4640be7ec76b49d5a61`
- **Build PR:** [#49](https://github.com/Corb1nW/Independent-Study/pull/49)
- **Scope:** D4-V01 and the manifest comparison under D-062 Amendment 6, Q74 and D-045.
- **Independence:** Claude implemented the fix following my D4-V01 recommendation. I ran the regression probes and comparisons myself.
- **Verdict:** AGREE
- **Must fix before Corbin decides:** None.
- **Status:** REVIEWED, NOT APPROVED

The diff from `a40e7fbcc6e96a2ed7259f6912031e1b0e514727` covers the comparator, its tests and the project records. The implementation commit and reviewed head differ only in the decision log revision number cited in `PROJECT_STATE.md`. [Builder handoff](https://github.com/Corb1nW/Independent-Study/pull/49#issuecomment-6955685261) · [D-062 revision](https://github.com/Corb1nW/Independent-Study/blob/c8839e95f1c97de54e7e55bd0803b79c1df3a6b3/docs/DECISIONS.md#L2731-L2735)

## D4-V01 resolved

The comparator checks JSON types, keys and list lengths before comparing values. Only changed pairs of finite floats may use the residual exemption or rounding tolerance. I ran the CLI on copies of the official `af21e78` assembled manifest. It returned exit 1 for a missing or extra residual, a residual replaced with a boolean, NaN, infinity, string, list or null, and a fractional sample index or integer written as a float. It also rejected a changed list length and a change from 3.0 to 3.000000001 s. [Comparator](https://github.com/Corb1nW/Independent-Study/blob/c8839e95f1c97de54e7e55bd0803b79c1df3a6b3/ci/d4-verify/compare_manifest.py#L49-L87)

The CLI returned exit 0 for a one-ULP C3 change, a finite solver residual change, two NaNs and matching positive infinities. Opposite infinities returned exit 1. The revised 24-test file yielded 12 failures when run with the previous comparator and passed with the reviewed comparator. The revised margin in the decision record and test agrees with the final timestamp probe at about 333 times the tolerance.

## Independent execution

I ran `ci/d4-verify/verify.sh` in a clean detached checkout at `c8839e95f1c97de54e7e55bd0803b79c1df3a6b3` using the dependency lock on Linux x86-64 (Python 3.13.5, OpenSim 4.6, NumPy 2.5.3, SciPy 1.18.1). The verifier exited 0. **435 tests passed**, including the 24 comparator tests. Integrity and the dataset check passed, all nine invalid inputs were rejected, and all three oracle coverage checks passed and the regenerated OpenSim references matched exactly. Both D4 runners exited 0. I directly compared their manifests to the official `af21e78` archives. The only difference was the expected checkout SHA.

I applied the reviewed comparator to four outputs from my earlier forced-Haswell runs. All four matched archived statuses, per-run check verdicts, hypotheses and stored series. The comparator reported no differences outside its residual and rounding allowances.

| Execution SHA | Configuration | Residual differences | Rounding differences | Other differences |
|---|---|---:|---:|---:|
| `31a9d3f` | Assembled | 34 | 9 | 0 |
| `31a9d3f` | Iliopsoas | 39 | 9 | 0 |
| `af21e78` | Assembled | 34 | 9 | 0 |
| `af21e78` | Iliopsoas | 39 | 9 | 0 |

I read the three author-triggered hosted logs at verifier `a2bab546ea422c18a769a4640be7ec76b49d5a61`. Both default-kernel runs reported zero differing paths. The forced-Haswell run at `af21e78` passed with 43 assembled and 49 iliopsoas differences, all residual- or rounding-level. [Original default-kernel run](https://github.com/Corb1nW/Independent-Study/actions/runs/44137221750/job/134229936604) · [Amended default-kernel run](https://github.com/Corb1nW/Independent-Study/actions/runs/44137221588/job/134229937761) · [Forced Haswell run](https://github.com/Corb1nW/Independent-Study/actions/runs/44137221272/job/134229944642)

Corbin decides on Amendment 6.
