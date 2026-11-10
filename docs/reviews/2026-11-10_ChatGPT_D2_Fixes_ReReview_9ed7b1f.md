# Stage D2 configuration fixes — re-review of PR #37

Reviewed by (model): ChatGPT\
Built by (model): Claude\
Date: 2026-11-10\
Reviewed SHA (full): `9ed7b1f1454bb1e3f4d16cd8cb8ec511b76c9926`\
PR: [#37](https://github.com/Corb1nW/Independent-Study/pull/37), `phase-d/claude-d2-config-guards`\
PR base SHA: `3821bd0c111a0b8abf4b90da638e0aac1246bd8b`\
Previously reviewed build SHA: `b9e96edb4a2e4a56e35679c8982152d5bc182315`\
Previous review: [PR #36](https://github.com/Corb1nW/Independent-Study/pull/36)\
Official result-generation SHA: `7ac0f2d2d83752d43f85a4221923f43f54e26b61`\
Review-record branch: `reviews/chatgpt-d2-fixes-9ed7b1f`, from main `ffeebdb30192408b4cb6ad67251b3ed45de9e7b7`

**Verdict: AGREE. No blocking findings. Must fix before Corbin decides: none.**

**Status: REVIEWED, NOT APPROVED.** The proposed fixes resolve D2-B01 and D2-B02; the nonblocking D2-BN01 coverage note is also resolved. Corbin alone approves and merges.

## Scope and independence

Corbin asked whether I agree with Claude's amendments in the continuing Reviewer role. I read the Reviewer instructions, PR #37's handoff, D-059 Amendment 4, the full eight-file fix diff, and the changed configuration/tests/oracle reference. The method, force-law calculations, solvers, anatomy, muscle dataset and sensitivity tool are unchanged. Previously closed proposal issues remain closed.

Claude wrote the implementation. The unit map and baseline restrictions were prescribed by my prior review, so checking those choices is partly self-check. My guard probes and comparator are self-authored/self-checked; execution of Claude's fix is independent of its author. Inherited ChatGPT-authored regressions retain their earlier self-check qualification.

No new modeling choice, source value or owner approval is inferred. Amendment 4 accurately describes the two guards, the added coverage and the earlier reproduction results. The Q60 quotation is consistent between the handoff and decision log; this review does not authenticate the unseen original chat.

## Disposition of earlier findings

| Item | Disposition | Evidence |
|---|---|---|
| **D2-B01 — units** | **Resolved** | `tools/run_phase_d2.py:55–57,80–86`: all seven parameters require their specified canonical unit before numbers are used. Compatible noncanonical and dimensionally wrong units are rejected; no implicit conversion. |
| **D2-B02 — baseline claims** | **Resolved** | `:60–62,87–99`: exact field set and supported physical values/types are required; prose must be nonempty. Unsupported passive force, width, dynamics, damping and tendon settings fail. The valid activation-dynamics declaration is now `ignored`, with its explanation in a comment. |
| **D2-BN01 — boundary coverage** | **Resolved** | `tools/make_d2_oracle.py:133–158,206–222` and added tests: exact inclusive switch edges and left/right/edge tendon-force cases; both velocity directions, three activations, both passive settings. A thin-pennation fixture reaches both sides of the lower normalized-length bound. |

I reran the previous bad-input cases myself: allowance `1 mN*m`, `1000 mN*m`, width 2, passive included, first-order dynamics, boolean damping, missing and extra physical fields, and the combined old mutation. All **nine configurations were rejected with ValueError**. For the combined case the actual CLI exited **1 before writing a manifest**. The default configuration still loads. This closes the previously demonstrated successful-but-inconsistent-run path.

## Ran, environment and results

Exact hash-checked HEAD `9ed7b1f1454bb1e3f4d16cd8cb8ec511b76c9926`, tree `1a6fb94e0ebe2eabae7d16df09b490e5c197d98b`; working status clean before and after. As in the previous execution review, the shallow/sparse checkout excludes only the unrelated binary phase-overview PDF; a complete binary-repository check is not claimed.

Environment: CPython 3.12.14, Linux x86_64/glibc 2.41; NumPy 2.3.5, SciPy 1.17.0, quadprog 0.1.14, Clarabel 0.11.1, OpenSim 4.6, pydantic 2.13.4/core 2.46.4, PyYAML 6.0.3, pytest 9.2.0, Pint 0.26.2, SymPy 1.14.0. Existing review virtual environment; `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_NOSYSTEM=1`.

| Executed check | Result |
|---|---|
| `python -m pytest -q` | **240 passed**, exit 0, 55.54 s; one installed anyio/pytest deprecation warning |
| `python -m src.integrity` | **PASSED**, exit 0 |
| `python tools/review_cycle1_probes.py` | **9/9 REJECTED**, exit 0 |
| `python -m tools.build_segment_datasets --check` | Datasets current, exit 0 |
| `python -m tools.make_d2_oracle --output <fresh-reference>` | Exit 0; **328 geometry / 408 force states**, plus 31 unmodified-model states |
| `python -m tools.run_phase_d2 --commit-sha 9ed7b1f1454bb1e3f4d16cd8cb8ec511b76c9926 --d1-manifest results/phase_d/2026-11-04_d1_squat_runs_dd89fff.json --output <fresh-run>` | Exit 0; verification passed, original body statuses retained |
| Own guard probes and full recursive comparisons | Passed; exact commands/results and executed guard source linked below |

**Fresh oracle vs expanded committed reference:** all **70,098 numeric values** match exactly (71,291 scalar leaves checked). Only Python, NumPy and platform metadata differ. The new reference preserves all previous **322 geometry rows**, **192 force rows** (apart from the new `kind` label), and **31 unmodified geometry rows** exactly. It adds six exact-edge geometry states and 216 switch/edge force states. Geometry now covers 301 D1 samples, nine spline knots, 12 switch sides and six exact edges; force coverage is 192 motion, 144 switch-side and 72 switch-edge rows.

**Default run vs official `7ac0f2d` manifest:** all **153,757 numeric values** match exactly (155,605 scalar leaves checked). Keys and array lengths match. The only eight nonnumeric changes are the commit SHA, the activation-dynamics description, and the SHA-256/Git blob pairs for the changed configuration, runner and reference. All **24 input records** were independently rehashed with raw SHA-256 and Git-filtered blob IDs.

Female remains muscle-feasible; male and Gait2392 remain flagged with peak t* 5.814680 and 6.361827 N·m at 1.52 s. D1 consistency, optimizer and mechanics checks pass; contact is feasible and the force-law domain is in range. These are demonstration-model results, not physiological validation.

## Read only, sources and limits

The source registry adds the three NCBI mirror links to their existing StatPearls rows and explicitly says Claude did not open those mirrors. This is honest attribution with no duplicated source identity or new anatomical claim. No additional external source was needed for this re-review.

Read/reasoned only: guard semantics, source/records consistency and unchanged accepted scope. Sensitivity, page rendering, the knee-only sweep and the earlier builder mutation set were not rerun this round: their implementation/calculation inputs are unchanged apart from the accepted guard and reference-extension changes, and the previous execution review records their evidence. No new Windows, browser-layout, anatomical, physiological or clinical validation is asserted.

New findings: **none**. Out-of-scope observations: **none requiring action**. The official result remains the historical run at `7ac0f2d`; the new run above establishes numerical regression equality without relabeling that older artifact.

**Handoff:** Corbin can approve and merge fix PR #37 at the reviewed SHA and this review record. No further configuration amendment or re-review round is needed on B01/B02/BN01 at this SHA. The next modeling stage remains Corbin's decision.

**Verdict: AGREE. Must fix before Corbin decides: none. Status: REVIEWED, NOT APPROVED.**

Evidence: [execution and comparison record](evidence/d2_fixes_9ed7b1f/execution_evidence.json), [executed guard-probe source](evidence/d2_fixes_9ed7b1f/guard_probes.py). The recursive comparator uses the [previous reviewer-owned implementation](evidence/d2_b9e96ed/compare_outputs.py), with the current output filename and exact-SHA constant substituted. The guard script's execution layout is `<review-dir>/repo` and `<review-dir>/out`; place the script in `<review-dir>` to rerun.
