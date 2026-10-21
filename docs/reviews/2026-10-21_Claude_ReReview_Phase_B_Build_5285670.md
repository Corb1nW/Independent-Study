# Re-review of the Phase B build (PR #13) after C1–C6

**Reviewer:** Claude (Phase B reviewer, Q17)
**Date:** 2026-10-21
**Reviewed SHA:** `528567001ffa20e08c816885cb4870600c70b2bd` (PR #13 head)
**Previous review:** `docs/reviews/2026-10-21_Claude_Review_Phase_B_Build_bf92dfd.md` (AMEND)
**Author of the work reviewed:** ChatGPT (Phase B builder)
**Disposition:** **AMEND, one small fix.** C1–C6 are all resolved, and verified by execution and by mutation. The new provenance check introduced one portability defect (D1): on a normal Windows checkout, the manifest refuses to run and one test fails. The fix is a few lines. With D1 fixed I will AGREE.

## Scope and methods

- Read `git diff bf92dfd 5285670` (6 commits: `src/hip_phase_b.py`, `config/phase_b_hip.yaml`, `tests/test_phase_b.py`, `PHASE_B_README.md`, `PROJECT_STATE.md`).
- **Executed** in a git checkout of `5285670` (Linux; Python 3.13.16, pytest 9.1.1, pydantic 2.14.1, pint 0.26.2, PyYAML 6.0.3):

| Command | Result |
|---|---|
| `python -m pytest -q` | **103 passed** |
| `python -m src.integrity` | PASSED |
| `python tools/review_cycle1_probes.py` | 9/9 REJECTED |
| `python -m tools.run_phase_b --commit-sha 5285670… --output <tmp>` | `verified_git_head_and_inputs`, 10 files checked; exit times 0.840578902667 s and 0.767340043923 s, ratio 0.912871 = 1/√1.2 (unchanged from `bf92dfd`) |

- Unofficial output from an unmerged branch; not a project result.

## C1–C6

| # | Check performed | Result |
|---|---|---|
| C1 | Repeated my reproduction: uncommitted edit of `moment_arm_m` → `ValueError: config: working file differs from HEAD`. External `--config` → `ValueError: … input path outside repository`. Mutation: disabling the byte comparison breaks 1 test | **Resolved.** The design also covers untracked files, inputs changed after resolution, and the code files themselves (10 files), and it fails closed on git errors. Archives are labelled unverified, never verified |
| C2 | Mutation: replacing `validate_datum` with no-op now breaks **2** tests (was 0) | **Resolved.** The temporary-root test with removed source claims is exactly the right shape |
| C3 | `t_perturbed / t_baseline == 1/√1.2` asserted to 1e-12 | **Resolved** |
| C4 | Activation rationale now says “deliberately tuned to reach the domain boundary within ~0.84 s; not a physiological estimate”. An `omitted_physics` block (gravity, pelvis, passive structures, other joints, muscle dynamics) is required by the loader and copied into every manifest | **Resolved.** The loader *requiring* the block is a good touch |
| C5 | README records the read-only, in-memory overlay as an explicit deviation from Amendment 1's wording | **Resolved** |
| C6 | `PROJECT_STATE.md` now shows `DECISIONS.md` revision 10 | **Resolved** |

## New finding

### D1 — MEDIUM: the provenance check rejects clean Windows checkouts
`verify_git_inputs` compares the working file's raw bytes with the blob from `git show HEAD:<path>`. Git for Windows normally checks text files out with CRLF line endings (`core.autocrlf=true`), while blobs store LF. So on a Windows checkout every input “differs from HEAD”, even though git itself reports the tree clean.

**Reproduced:** a fresh clone of `5285670` with `core.autocrlf=true`, files re-checked out with CRLF. `git status --porcelain` was empty, yet `python -m tools.run_phase_b …` raised `config: working file differs from HEAD`, and `python -m pytest -q` gave **1 failed, 102 passed**. The repository has no `.gitattributes`, and the README's own commands are written for Windows (`py …`), so this would affect Corbin directly.

**Requested fix:** compare the way git does. Use `git hash-object -- <path>`, which applies the same line-ending filters as `git add`, against `git rev-parse HEAD:<path>`. In the same CRLF checkout these were equal, as expected. Keep the separate raw-byte hash check against the hashes captured at resolution time; that one is unaffected. Optionally, also add a `.gitattributes` with `* text=auto` so line-ending handling is explicit for every collaborator. A regression test would be welcome: in the isolated fixture, set `core.autocrlf=true`, rewrite the file with CRLF, and expect verification to pass.

## Conclusion

**AMEND, D1 only.** Everything from the first review is fixed and verified. After the D1 fix I expect to AGREE without further changes, and then Corbin can approve and merge. After the merge, the runner is executed at the merged commit to produce the official Phase B record.
