# D-063 Stage D5 scope — Amendment 1 re-review

- **Reviewed by (model):** ChatGPT
- **Proposed by (model):** Claude
- **Reviewed SHA (full):** `9a8fc44f4267590a6d83bd5ecb41ec952cda690d`
- **Base SHA (full):** `1076704133c1e0af9fb2bf9623e30e16243285a7`
- **Earlier reviewed SHA (full):** `c3adca05556d9affdaa7e21cec757ce9d04a6e75`
- **Proposal PR:** [#53](https://github.com/Corb1nW/Independent-Study/pull/53)
- **Scope:** Blocking findings only on D-063 Amendment 1: D5-R01, D5-R02, the superseded requirements and the accompanying project-state changes. The full diff since the earlier review changes only `docs/DECISIONS.md` and `PROJECT_STATE.md`.
- **Independence:** Claude authored the amendment. Its remedies adopt my earlier recommendations, so reassessing those remedies is self-checked. I read Claude's actual revision and ran the repository checks myself.
- **Verdict:** **AGREE** on the amended scope.
- **Must fix before Corbin decides:** None.
- **Status:** **REVIEWED, NOT APPROVED**

Both earlier findings are resolved in the proposal. D-063 remains Proposed; Corbin decides whether to proceed with the build.

## Earlier findings

**D5-R01 — Resolved in scope.** [Replacement 1 and amended A3/A6](https://github.com/Corb1nW/Independent-Study/blob/9a8fc44f4267590a6d83bd5ecb41ec952cda690d/docs/DECISIONS.md#L2844) require an explicit actuator, coordinate, variant, path direction and source or model basis. A material disagreement passes only when declared and confirmed at that sample by the raw OpenSim moment arm, computed without consulting the ontology capability. Undeclared, unconfirmed and stale exceptions fail. A6 explicitly requires the biceps-femoris capability-flip probe to fail with the reference supplied on the moving knee and also on the fixed knee. This removes the proposed blanket reliance on a disagreement set derived from the same capabilities being checked.

**D5-R02 — Resolved in scope.** [Replacement 2](https://github.com/Corb1nW/Independent-Study/blob/9a8fc44f4267590a6d83bd5ecb41ec952cda690d/docs/DECISIONS.md#L2849) withdraws the “only code change” claim and puts all generic preparation into step 1. It covers lumped representation, bounded C3, recursive oracle inheritance through the shared resolver, schema-driven ontology module loading, the complete unactuated-muscle inventory and generic torque-share reporting. Steps 3–5 retain A2's prohibition on changes to `src/` or `tools/`. A6 includes the nested-inheritance and anatomy-only MTP probes, together with the earlier lumped-actuator error checks.

Amended A5 preserves the D4 series, statuses, regression results, oracle comparisons and H1, while allowing the specified C3-policy and C5-inventory changes to be recorded explicitly. This is compatible with the newly authorized preparation. The build review must check that evidence.

## Ran, environment and results

Clean detached checkout at the exact reviewed SHA, Linux x86_64, Python **3.13.5**; pytest **9.1.1**, PyYAML **6.0.3**, NumPy **2.5.3**, SciPy **1.18.1**, OpenSim **4.6**. Used the existing locked-package environment and a test-only Git configuration for tests that create commits.

| Command | Result |
| --- | --- |
| `python -m pytest -q` | **454 passed**, 148.18 s |
| `python -m src.integrity` | **PASSED** |
| `python tools/review_cycle1_probes.py` | **9/9 invalid-input probes rejected**, exit 0 |
| `python -m tools.build_segment_datasets --check` | Exit **0**, no stale datasets |
| `git diff --check c3adca05556d9affdaa7e21cec757ce9d04a6e75 HEAD` | Exit **0** |
| HEAD and checkout status before/after execution | Exact reviewed SHA; clean |

These execution results cover the existing software at the proposal SHA. No code, data, ontology or tests changed in Amendment 1.

## Read or reasoned only

Read the full amendment diff, the earlier review, the author's [per-finding response](https://github.com/Corb1nW/Independent-Study/pull/53#issuecomment-6960379279), D-063's original criteria and supersession rules, and the D-062 policy it replaces. The new C3 rule and generic preparation were assessed as specified methods and build obligations.

**Not run, and why:** The new D5 behavior and its A6 probes have no implementation at this SHA. Full official D4 reruns were not repeated for this documentation change; amended A5 requires their comparison during the build.

**Sources checked:** Repository records and the pinned amendment. It adds no external anatomical source or numerical parameter. Q81 is attributed to Claude's session and matches the author's handoff; that session transcript is not independently available here. This round adds no external source citation requiring registration.

## Findings and build follow-through

**New blocking findings:** None.

**Nonblocking note N1:** PR #53's opening description still contains the original SHA and “only code change” summary. Refresh that summary to Amendment 1 when updating the handoff. The pinned amendment and latest per-finding response expressly supersede that text.

**Out-of-scope observations:** No new source review. The anatomical completeness, lumped `gem_r` mapping, source registrations and detailed build checks remain obligations of the build review, as previously recorded. The required A6 failures, A2 commit boundaries and A5 compatibility must be demonstrated by the implementation.

**Next:** Corbin decides the amended D-063 scope. If he proceeds, Claude builds and the implementation receives its own review.
