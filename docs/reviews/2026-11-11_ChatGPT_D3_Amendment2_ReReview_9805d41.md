# Stage D3 Amendment 2 re-review

- **Reviewed by (model):** ChatGPT
- **Built by (model):** Claude
- **Reviewed SHA:** `9805d41099ce0c2a45d1e36b48359a973ccce2d9`
- **Base SHA:** `ad11987d1a458ab4fb65462219c2ac533bc5f0c8`
- **Previous reviewed SHA:** `b06400b4c7bf00a023a570b47fdb95a95c6cb079`
- **Official amended run SHA:** `d3efc563b9abd097f2adf1eddbd579560bbfa48d`
- **PR:** [#41](https://github.com/Corb1nW/Independent-Study/pull/41)
- **Date:** 2026-11-11
- **Verdict:** **AMEND**. The three original findings are resolved. D3-B04 is the remaining blocker.
- **Status:** **REVIEWED, NOT APPROVED**

## Scope and independence

Reviewed the changes since the prior D3 build review under D-060 and the D-059 oracle and simplification checks. The new code and output files address D3-B01 through D3-B03 and D3-N03. The numerical model and vendored sources have the same Git blobs as in the earlier review. Q63 is recorded as direction for the fixes in the Git handoff. The original Claude conversation was unavailable for direct verification of the quote.

Claude authored the fixes and release artifacts. I independently reran and compared those artifacts. I self-checked the review criteria, the comparator and probes I authored, and the earlier ChatGPT work covered by the regression suite.

## Earlier findings

| Finding | Disposition | Evidence |
|---|---|---|
| **D3-B01** | **Resolved** | At 1.50 s all three vasti reach 1 for every body. Female gluteus maximus activations are 0.188682, 0.474273 and 0.477005. Male and Gait2392 reach 1 in the middle and lower compartments and rectus femoris. The co-activation peaks in the stated windows reproduce, including zero at the bottom in D3 and 0.113, 0.130 and 0.136 near standing. The Gait2392 standing moment arms and force contributions support the reported recruitment mechanism. The unmeasured margin claim is withdrawn. |
| **D3-B02** | **Resolved** | I exercised the regenerated viewer JavaScript with a DOM fixture for all three bodies, moving → fixed → moving. All 20 moving and 15 fixed assumption labels and texts matched their respective manifests. Heading, feasibility and commit changed with the mode. The D3 view states that the motion comes from D1 and both torques and muscle paths use the moving knee. |
| **D3-B03** | **Resolved** | I paired 31 identical poses in the regenerated OpenSim models and recomputed all 42 actuator-coordinate maxima. The diagnostic agrees to its reported precision. The maximum is 4.3930 mm at the ankle for tibialis anterior, followed by 0.0188 mm at the knee for lateral gastrocnemius, with zero to reporting precision at the hip. Both models keep the moving knee. |
| **D3-N03** | **Resolved for reference coverage** | Both committed and regenerated references pass on the LF checkout. A test reference with 301 copies of the upright pose and distinct indices now yields a coverage error and fails the kinematics check. D3-B04 concerns rejection of valid files after Git's line-ending conversion. |

## Execution

At the reviewed SHA, I ran `python -m pytest -q` (**284 passed**), `python -m src.integrity` (**passed**), `python tools/review_cycle1_probes.py` (**9/9 rejected**), `python -m tools.build_segment_datasets --check` (**exit 0**) and both `python -m tools.oracle_coverage` commands (**coverage OK**). I regenerated the references using `python -m tools.make_d2_oracle --knee fixed` and `--knee moving` with output paths outside the checkout. All 70,098 fixed and 75,817 moving numeric values matched. Only environment strings differed. Comparing the revised committed fixed reference with its predecessor also confirmed identical data and changes limited to the knee-mode, platform and generator hash fields.

In a detached checkout of the official amended run SHA, I ran the following commands.

```bash
python -m tools.run_phase_d3 \
  --commit-sha d3efc563b9abd097f2adf1eddbd579560bbfa48d \
  --d1-manifest results/phase_d/2026-11-04_d1_squat_runs_dd89fff.json \
  --d2-manifest results/phase_d/2026-11-10_d2_muscle_runs_7ac0f2d.json \
  --output /tmp/d3_amended.json
python -m tools.build_d2_page \
  --manifest results/phase_d/2026-11-10_d2_muscle_runs_7ac0f2d.json \
  --moving-manifest /tmp/d3_amended.json --output /tmp/d3_amended.html
```

The manifest and viewer matched the amended commits byte for byte. My comparator matched all 157,484 manifest numbers, rehashed all 30 input records and confirmed that the complete per-body run objects and aggregate status match the original `525e2c3` run. The amended manifest SHA-256 is `d393797ec76cb89cce78073367c75a5af5bef7a2eebf41787a5a4f6006ddfa42`. All three bodies have zero stage-1 reserve shortfall on the moving knee.

The checkouts had exact HEADs and hash-checked Git trees. Sparse checkout omitted the unrelated phase-overview PDF. The environment was Linux x86-64, CPython 3.12.14, NumPy 2.3.5, SciPy 1.17.0, OpenSim 4.6, quadprog 0.1.14, Clarabel 0.11.1, PyYAML 6.0.3 and pytest 9.2.0. I attempted `python -m tools.check_viewer`. Chromium startup failed with `socket() failed: Operation not permitted`. I verified the switch logic and text with the DOM fixture. Desktop and phone layout remain builder-reported. The CRLF probe used Git on Linux to reproduce the Windows line-ending conversion. The scientific scope is the stated software computation.

## D3-B04 — High — The oracle check rejects a Git-clean CRLF checkout

The new check at `tools/oracle_coverage.py:78` compares the raw worktree bytes of `tools/make_d2_oracle.py` against the generator hash stored in both committed oracle files. The path inherits `* text=auto` from `.gitattributes`, so Git can write CRLF in a Windows checkout with `core.autocrlf=true`.

I enabled `core.autocrlf=true` in an isolated checkout at the reviewed SHA and had Git rewrite the generator with `git checkout-index -f -- tools/make_d2_oracle.py`. Its normalized object ID still matched HEAD (`9381ee5589352f1694bbe8b980acf5e989577bdc`). After refreshing the index with `git add -- tools/make_d2_oracle.py`, both the worktree and index were clean. `git ls-files --eol` reported `i/lf w/crlf`. Both coverage commands exited 1 with only “recorded oracle-tool hash does not match tools/make_d2_oracle.py”. Both committed-reference coverage tests failed. The D3 runner verified its Git inputs and computed the same mechanics, then exited 1 and marked kinematics verification failed for all three bodies.

**Fix I would accept.** Add this path-specific rule after the general text rule in `.gitattributes`.

```gitattributes
tools/make_d2_oracle.py text eol=lf
```

This keeps the raw-byte provenance check and the strict stale-tool rejection. I tested the rule in `.git/info/attributes` in a second isolated checkout with `core.autocrlf=true`. Git wrote LF for the generator, both coverage commands passed, and the full D3 run exited 0 with the same per-body outputs and statuses. On the amended SHA, reproduce those checks with the tracked rule. The existing generator and references already use LF.

## Handoff

D3-B04 is the only required change at the reviewed SHA. The earlier D3 findings are closed. The sources checked are the existing vendored Gait2392 model, both generated OpenSim references and the accepted D1/D2 runs. The follow-up should demonstrate the line-ending fix and return the amended SHA for review. Corbin makes the merge decision.
