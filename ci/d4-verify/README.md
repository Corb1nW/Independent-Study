# Stage D4 verification job

`.github/workflows/d4-verify.yml` runs `verify.sh` against a full commit SHA with the pinned packages in
`requirements.lock` (the environment of the official D4 runs). It was added at Corbin's request so that ChatGPT can
re-run the checks independently (PR #48).

What it does, in order (each step's log is in the artifact under `logs/`):

1. prints the commit under test, the checked-out HEAD, Python, the platform, OpenSim and `pip freeze`; refuses a
   different or unclean checkout;
2. `python -m pytest -q`, `python -m src.integrity`, `python tools/review_cycle1_probes.py`,
   `python -m tools.build_segment_datasets --check`;
3. for each `tests/data/*_oracle_reference.json`: `python -m tools.oracle_coverage`, a fresh OpenSim regeneration
   with `tools/make_d2_oracle.py`, and a value-by-value comparison with the committed file (`compare_reference.py`);
4. both D4 runs (`config/phase_d4_*.yaml`) with `--commit-sha` set to the commit under test;
5. a comparison of each regenerated manifest with the committed official one for that commit (`compare_manifest.py`),
   taken from `compare_ref` (default: the workflow's own commit, which holds the records).

Start a run:

- **Before the workflow is on `main`:** push a branch named `verify/<full SHA>` whose tip contains this workflow
  (for example, at the head of PR #47): `git push origin <workflow commit>:refs/heads/verify/<full SHA>`.
- **After it is on `main`:** Actions → d4-verify → Run workflow → `target_sha`.
- **Repeat a run:** open the run → Re-run all jobs.

The same script runs locally in any Python 3.13 session: install `requirements.lock` with `--no-deps`, check out the
commit, then `bash ci/d4-verify/verify.sh <checkout> <full SHA> <ref holding the manifests> <output dir>`.
