# LB-AO Project State

**Updated:** 2026-10-21
**Updated by:** Claude
**Repository:** `https://github.com/Corb1nW/Independent-Study` (canonical, public; D-051 and its Amendment 1)
**Authoritative snapshot:** branch `main` on the remote, the commit that last changed this file (`git log -1 -- PROJECT_STATE.md`). Phase A implementation: `4abb4f1`. Baseline of the original work: `d04fb78`. LB-AO history imported into this repository at `2814236` (PR #1).
**Component versions:** ontology `hip.yaml` 0.3.0 · schema LB-QPS 0.4.0 · dataset `gluteus_maximus.yaml` 0.3.0 · `DECISIONS.md` revision 4
**Current phase:** **Phase A under review.** ChatGPT's source-level review returned AMEND; Claude's response (D-052) is on branch `phase-a/claude-review-response`, awaiting ChatGPT's re-review and Corbin's merge. Phase B not started.

## Implemented work

**Phase A review response (D-052; branch `phase-a/claude-review-response`)**
- **A1:** a datum may cite ontology sources plus its own dataset's sources; loading a dataset no longer widens what other datasets may cite. `validate_datum(datum, dataset=None)`.
- **A2:** reference checks added for `related_observation`, `conflicts_with`, `convention_source_id` and structured derivation-input `source_id`; checked and unchecked fields listed in `src/quantitative.py`.
- **A3:** report key `ready_for_simulation` is now `admissible_as_simulation_input` (datum-level only).
- **A4:** documented that the evidence layer checks registry membership, not claim support.
- **15 new tests** in `tests/test_phase_a_review.py`; mutation-check tool repaired.
- **CI:** `.github/workflows/tests.yml` runs pytest and the integrity check on every push and PR (supporting evidence only).

**Phase A (`4abb4f1`; D-024, D-025, D-026, D-027, D-031, D-034, D-035; choices in D-050)**
- **Layered validator:** structural (`src/datum_model.py`, Pydantic) → semantic (vocabularies, property definitions, units via pint, physical bounds, ontology references) → evidence (sources, assumptions, derivations, applicability), in `src/quantitative.py`.
- **Cross-file integrity check:** `src/integrity.py`, run with `python -m src.integrity`.
- **Data fixes D1–D9** (D9 found during Phase A: a truncated YAML note). Details are in the D-024 Amendment 1.
- **Hip joint** now receives joint kinematic and kinetic properties through `class_hierarchy` (D-031).
- **Adductor magnus dual innervation** added after verification against StatPearls (D-034).
- **Ward 2009 fiber-length normalization** verified against the primary source and recorded (D-019).
- **One defaults function** with explicit-field precedence (D6).
- **47 new tests** in `tests/test_phase_a.py`; 2 baseline tests adapted (listed in D-050).

**Repository (D-051 pilot):** LB-AO history merged into `Corb1nW/Independent-Study` without rewriting any commit (`2814236`). `pytest.ini` limits test collection to `tests/`, because `Version Models/` holds the original v0.1–v0.5 uploads with clashing test module names. Course notes, `References/` and `Version Models/` are unchanged. `References/` and `docs/design/` hold byte-identical copies of the four design PDFs.

**Earlier:** baseline `d04fb78`; review documents in `docs/reviews/`; probe script `tools/review_cycle1_probes.py`; `docs/DECISIONS.md` (D-001 to D-052).

## Validation

Environment for Claude's runs: Python 3.13.16, PyYAML 6.0.3, pytest 9.1.1; pydantic 2.13.5 and pint 0.26.1 on 2026-10-07, pydantic 2.14.1 and pint 0.26.2 on 2026-10-20/21 (minimums in `requirements.txt`).

| Check | Snapshot | Run by | Command | Result |
|---|---|---|---|---|
| Test suite | `d04fb78` | Claude | `python -m pytest -q` | 18 passed |
| Test suite | `4abb4f1` | Claude | `python -m pytest -q` | 65 passed |
| Test suite | `cfea57c` (import) | Claude | `python -m pytest -q` | 65 passed |
| Test suite | `976251c` (D-052) | Claude | `python -m pytest -q` | 80 passed |
| New tests vs. `4abb4f1` logic | `976251c` tests, `4abb4f1` validator and checker (signature shimmed) | Claude | `python -m pytest -q tests/test_phase_a_review.py` | 11 failed, 4 passed (the 4 are acceptance cases) |
| Mutation check: Phase A tests vs. old validator | `4abb4f1`; again at `976251c` | Claude | `python tools/mutation_check_phase_a.py` | 30 of 47 fail, both times |
| Integrity check | `d04fb78` data, Phase A checker | Claude | `python -m src.integrity` | FAILED, 48 problems: 44 deprecated `pennation_angle` names (D2), 2 unresolved coordinates (D1), Fmax without `model_id` (D6), MUSCLE_FORCE junk key (D9) |
| Integrity check | `4abb4f1`; `cfea57c`; `976251c` | Claude | `python -m src.integrity` | PASSED |
| Review Cycle 1 probes | `d04fb78` | Claude | `python tools/review_cycle1_probes.py` | All 9 validator probes ACCEPTED; D1, D2, D3, D5 findings present |
| Review Cycle 1 probes | `4abb4f1`; `976251c` | Claude | `python tools/review_cycle1_probes.py` | All 9 validator probes **REJECTED**; no D1, D2 or D5 findings; D3 list down from 11 to 10 classes (hip joint fixed; the rest is Phase C per D-031) |
| CI | `e3c3b4e` | GitHub Actions | `.github/workflows/tests.yml` | success (pytest and integrity steps passed; step status read through the API, logs not readable from Claude's session) |
| Source-level review | `4abb4f1` | ChatGPT | reading files at the SHA | AMEND: findings A1–A5, all agreed (D-052). Record: PR #2 |

**Reported, not independently reproduced:** every executable result above. ChatGPT read the code at `4abb4f1` but could not execute it (its sandbox cannot reach GitHub). CI is a third-party run and counts as supporting evidence only (D-051 item 10).

## D-051 pilot

**Capabilities (P3)**, as tested 2026-10-20/21:

| Capability | Claude | ChatGPT |
|---|---|---|
| Read files at a given SHA | Yes | Yes (GitHub connector) |
| Check out an arbitrary SHA | Yes | No (sandbox cannot resolve github.com) |
| Install requirements and run the checks | Yes | Yes in its sandbox, but only on uploaded files |
| Push a branch | Yes | Yes, apparently: branch `phase-a/chatgpt-review-4abb4f1` (commit `b10e301`) |
| Open or comment on a PR | Yes | Yes, apparently: PR #2. Its wording is ChatGPT's, but GitHub attributes the commit and PR to Corbin's account; Corbin to confirm |
| Push tags | No (refused at the connection) | Not reported |

**Fallback for ChatGPT's execution:** Corbin downloads `https://github.com/Corb1nW/Independent-Study/archive/<SHA>.zip` and uploads it; ChatGPT runs the checks on that file snapshot and states the SHA (item 12).

**Owner-only merging (P2):** ruleset “main” is active: pull request required, merge commits only, deletion and force-push blocked. **Residual risk:** Claude, and apparently ChatGPT, act through Corbin's GitHub account, so “only Corbin merges” is partly procedural, and GitHub's authorship labels do not identify the model (D-051 Amendment 3).

**Review record:** ChatGPT's Phase A review enters the repository through PR #2. Merge PR #2 before PR #3.

**Pass criteria (P7):**

| Criterion | Status |
|---|---|
| Remote holds the intended history and commits | Met (`d04fb78`, `4abb4f1` are ancestors of `main`; tags dropped, Amendment 2) |
| Both models read the same SHA, or a documented fallback was used | Met for reading (`4abb4f1`) |
| Review pinned to a commit with honest test-execution status | Met (ChatGPT's review states nothing was executed) |
| Builder responded through new commits | Met (this branch) |
| Corbin approved a specific SHA and merged it | Pending |
| `PROJECT_STATE.md` and `DECISIONS.md` consistent after the merge | Pending |

## Accepted but unimplemented

- **D-036** minimal hip-only model; **D-037** force-to-torque representation recorded before running (Phase B)
- **D-039 / D-040** remaining phases B–F, including the Phase B boundary (D-039 Amendment 1)

## Open proposals and disagreements

- **D-051** shared repository: pilot in progress; decided after the pilot.
- **D-052** Phase A review response: awaiting ChatGPT's re-review and Corbin's merge.
- **D-049 physical bounds:** implemented to close probe 3. The bound values await review, especially pennation < π/2. Not covered by ChatGPT's 2026-10-21 review.
- **Q8 and Q9 interpretations (`DECISIONS.md` §4):** Corbin may correct either.
- **Deferred by Corbin until their phase (Q8):** D-028, D-029, D-030, D-032, D-033, D-038.
- **No open disagreements between models.**

## Next task

**Owner:** ChatGPT (reviewer), then Corbin.
**Task:**
1. Re-review the head SHA of the PR for `phase-a/claude-review-response`: the D-052 fixes, `tests/test_phase_a_review.py`, and the record changes. Pin the review to that SHA.
2. Reproduce the executable checks if Corbin uploads the commit archive (fallback above): `python -m pytest -q`, `python -m src.integrity`, `python tools/review_cycle1_probes.py`. Report anything not run as not run.
3. Still outstanding from the Phase A task: review D-049 (bounds) and the D-050 choices.
4. Return Agree / Amend / Disagree with evidence, as one file in `docs/reviews/` (D-051 item 6).

**Then:** Corbin approves and merges the reviewed SHA (D-051 item 8), completing the pilot; Corbin decides on D-051. Then Phase B (hip-only model), starting with the D-037 force-to-torque choice.
**Required inputs:** this repository; `docs/DECISIONS.md` D-049 to D-052; `docs/reviews/2026-10-21_Claude_Response_to_Phase_A_Review.md`.

## Handoff protocol (D-048, as amended by D-051)

1. Start from a pushed commit and state its full SHA.
2. Read this file and the `DECISIONS.md` entries named in the next task.
3. Return: changes as commits on a branch; validation evidence (commands, environment, results); proposals as `Proposed` entries for `DECISIONS.md`; unresolved questions. Reviews are one file in `docs/reviews/`, pinned to a SHA.
4. Update this file at the end of every build or review.
