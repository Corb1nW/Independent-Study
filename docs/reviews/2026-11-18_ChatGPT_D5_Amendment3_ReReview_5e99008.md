# Stage D5 build re-review of D-063 Amendment 3

- **Reviewed by (model)** ChatGPT
- **Built by (model)** Claude
- **Date** 2026-11-18
- **Reviewed SHA** `5e99008fc490d3f330ee1d1d0d5cfcc79084f0c3`
- **PR base SHA** `c5d082c05e66db0ab21925fbbb795f2e006f6703`
- **Previous reviewed SHA** `629c6b454c126bf5008e301d50afed1f0f8a2678`
- **PR** [#55](https://github.com/Corb1nW/Independent-Study/pull/55)
- **Scope** D-063 Amendments 1–3, specifically the F4 correction, H4 reporting, the generated page and D5-B01 regression coverage.
- **Independence** Claude adopted wording I supplied in the original review. The wording is self-checked. I separately executed the checks on Claude's builder, regression test and generated output.

## Findings

**D5-B01 (High) — resolved.** F4 in `docs/DECISIONS.md`, `tools/build_squat_demo_d5.py` and the generated page agrees with archived H4. The three vasti still reach full activation near the bottom. The maximum fixed-knee reserve drops from 5.815 to 3.372 N·m for the male body and from 6.362 to 3.700 N·m for Gait2392. A residual shortfall persists. The wording limits the TFL knee-extension claim to this model and leaves the total reserve reduction unattributed to any single muscle. The prior review's 1.52 s breakdown is explicitly attributed to the reviewer in Amendment 3.

The full amendment diff touches five files. The two versions of the demo have identical text outside the embedded JSON and identical JSON after removing the F4 entry from both versions. The run manifests, report, schema, source data and ontology files have identical Git content. The correction is within the accepted scope.

## Execution

Python 3.12.14, pytest 9.2.0, NumPy 2.5.5, SciPy 1.18.1, Clarabel 0.11.1 and quadprog 0.1.14.

- `python -m pytest -q -rs` reported 506 passed and 1 explained D4 fixture skip in 261.16 s. The archived D4 ontology path is covered by the rebuild test. Pytest emitted one deprecation warning from the environment's AnyIO plugin.
- `python -m src.integrity` passed. `python tools/review_cycle1_probes.py` rejected all nine invalid inputs. `python -m tools.build_segment_datasets --check` passed.
- `python -m tools.build_squat_demo_d5` regenerated the committed HTML byte for byte.
- `python -m tools.report_phase_d5` with the archived D4 growth and D5 manifests regenerated the committed report byte for byte, including the H4 values above.
- The new F4 test passed at this SHA and failed as expected with only that test transplanted onto `629c6b4`. The failure was the missing D4 reserve value 5.815.
- Parsed the fixed- and moving-knee OpenSim reference JSON. Across all 301 official squat poses in each variant, the TFL knee moment arm is negative in the flexion-positive convention. The ranges are −12.980 to −6.954 mm for the fixed knee and −13.972 to −1.886 mm for the moving knee.
- `git diff --check 629c6b4 HEAD` passed.

## Evidence and limits

Read the accepted D-063 decision and amendments, prior review in [PR #56](https://github.com/Corb1nW/Independent-Study/pull/56), D5 report and OpenSim fixtures. The sourced knee-flexion capability remains tied to the existing `SRC:STATPEARLS_TFL` record. This review adds no external sources. I used the committed fixtures and manifests for the targeted checks above. Fresh official dynamics runs and OpenSim fixture regeneration were performed in the prior review and were outside this wording correction.

N1 and N2 remain nonblocking. N2, the hip dataset version-label proposal, remains Corbin's decision. No new findings.

**Verdict AGREE.** No changes required before Corbin decides. **Status REVIEWED, NOT APPROVED.**
