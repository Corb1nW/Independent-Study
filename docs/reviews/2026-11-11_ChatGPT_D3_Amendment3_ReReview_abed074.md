# Stage D3 Amendment 3 re-review

- **Reviewed by (model):** ChatGPT
- **Built by (model):** Claude
- **PR:** [#41](https://github.com/Corb1nW/Independent-Study/pull/41)
- **Reviewed SHA:** `abed0742c13b5e976a4da76aab58f45a0f379a1e`
- **Base SHA:** `ad11987d1a458ab4fb65462219c2ac533bc5f0c8`
- **Previous reviewed SHA:** `9805d41099ce0c2a45d1e36b48359a973ccce2d9`
- **Fix SHA:** `e6ab89622cad7cd1086edc1390cea2c5e2f51070`
- **Official D3 run SHA:** `d3efc563b9abd097f2adf1eddbd579560bbfa48d`
- **Date:** 2026-11-11
- **Verdict:** **AGREE**. D3-B04 is resolved. No blocking findings.
- **Status:** **REVIEWED, NOT APPROVED**

## Scope and independence

Reviewed the D3-B04 fix in D-060 Amendment 3. The complete delta from `9805d41` is the Git attribute, its regression test, and the decision and project-state records. The tracked rule keeps the oracle generator's bytes in LF form for the raw-hash check. I proposed that rule in the earlier review and self-checked its design. I independently executed Claude's implementation and regression test. Q64 is recorded as direction for the fix. The Claude conversation was unavailable for direct quote verification.

## Execution

I used Git 2.52.0 on Linux x86-64 with CPython 3.12.14, NumPy 2.3.5, SciPy 1.17.0, quadprog 0.1.14, Clarabel 0.11.1, PyYAML 6.0.3 and pytest 9.2.0. For each revision I populated a fresh worktree from the exact Git tree with `core.autocrlf=true` before `git checkout-index -a -f -u`. Git status was clean. The sparse trees excluded the unrelated binary phase-overview PDF.

| Check | Before at `9805d41` | After at `abed074` |
|---|---|---|
| Generator checkout bytes | CRLF, among 184 converted files | LF, with 183 other files converted to CRLF |
| Git identity of the generator | `9381ee5589352f1694bbe8b980acf5e989577bdc` | Same blob ID |
| Fixed and moving oracle coverage | Both exit 1 on the generator hash | Both exit 0 and report coverage OK |

The Git attributes resolve to `text: set` and `eol: lf` for `tools/make_d2_oracle.py`. The file's raw SHA-256 matches `tool_sha256` in both committed references. I removed the rule in a separate fixture while retaining the LF working file. The new guard test failed on the missing attribute, so it catches the regression before a CRLF checkout reproduces it.

At `abed074` in the CRLF-converted worktree I ran:

```bash
python -m pytest -q
python -m src.integrity
python tools/review_cycle1_probes.py
python -m tools.build_segment_datasets --check
python -m tools.oracle_coverage tests/data/d2_oracle_reference.json --knee fixed
python -m tools.oracle_coverage tests/data/d3_oracle_reference.json --knee moving
python -m tools.run_phase_d3 \
  --commit-sha abed0742c13b5e976a4da76aab58f45a0f379a1e \
  --d1-manifest results/phase_d/2026-11-04_d1_squat_runs_dd89fff.json \
  --d2-manifest results/phase_d/2026-11-10_d2_muscle_runs_7ac0f2d.json \
  --output /tmp/d3_b04_crlf.json
```

All **285 tests passed**. Integrity passed, the probes rejected all nine invalid cases, and the dataset check passed. The D3 run exited 0. My comparator verified every result and status against `d3efc56` and rehashed all 30 input records. Each Git blob ID matched. The SHA and the raw hashes of 25 CRLF-converted inputs were the only manifest differences. The worktree was clean afterward.

This is a Linux reproduction of Git's Windows line-ending conversion. Earlier review records cover the OpenSim regeneration and the viewer. The sources for this re-review are the committed attributes, oracle references, runner and official manifest.

## Disposition

**D3-B04 is resolved.** D3-B01 to D3-B03 and D3-N03 were resolved in the previous re-review. The official results and the checks support proceeding to Corbin's merge decision.

One nonblocking wording clarification for the decision record. The generator is the text-converted file whose raw hash is compared with the oracle references. The verifier also hashes the vendored model, which has the `-text` attribute. Run manifests store raw SHA-256 values for provenance and use Git-filtered blob IDs to verify the checkout. See `tools/oracle_coverage.py:74` and `src/run_manifest.py:100`.
