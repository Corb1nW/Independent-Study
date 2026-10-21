# LB-AO Project State

**Updated:** 2026-10-21
**Updated by:** Claude
**Repository:** `https://github.com/Corb1nW/Independent-Study` (canonical, public; D-051 and its Amendment 1)
**Authoritative snapshot:** branch `main` on the remote, the commit that last changed this file (`git log -1 -- PROJECT_STATE.md`). Phase A implementation: `4abb4f1`. Baseline of the original work: `d04fb78`. LB-AO history imported into this repository at `2814236` (PR #1).
**Component versions:** ontology `hip.yaml` 0.3.0 · schema LB-QPS 0.4.0 · dataset `gluteus_maximus.yaml` 0.3.0 · `DECISIONS.md` revision 6
**Current phase:** **Phase A under review** (D-049 accepted: Amendments 2 and 3). ChatGPT's re-review of `29e256e` (`docs/reviews/2026-10-21_ChatGPT_ReReview_D052_29e256e.md` (PR #5)): AGREE with the D-052 fixes on source review; AMEND D-049 (pennation domain needs Corbin's ruling) and these records. ChatGPT's attempt to run the checks was blocked (no `pint` and no network in its sandbox); a retry with offline wheels is pending. Phase B not started.

## Implemented work

**Phase A review response (D-052; merged at `29e256e`, PR #3)**
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
| Check out an arbitrary SHA | Yes | No: native `git clone`/checkout blocked (sandbox cannot resolve github.com) |
| Extract an uploaded archive | Yes | Yes |
| Install requirements and run the checks | Yes | **Not verified; blocked.** No network to the package index, and `pint` is not preinstalled (2026-10-21). Retry pending with offline wheels supplied by Corbin |
| Push a branch / commit files | Yes | Yes: `phase-a/chatgpt-review-4abb4f1` (`b10e301`), `phase-a/chatgpt-rereview-d052-29e256e` (`e7ad2c2`); confirmed by Corbin (Q11) |
| Open or comment on a PR | Yes | Yes: PRs #2 and #5, created by ChatGPT (Q11); GitHub attributes them to Corbin's account, so reviews name their author in the text |
| Push tags | No (refused at the connection) | Not reported |

**Fallback for ChatGPT's execution:** Corbin downloads `https://github.com/Corb1nW/Independent-Study/archive/<SHA>.zip` and uploads it; ChatGPT runs the checks on that file snapshot and states the SHA (item 12). Because ChatGPT's sandbox cannot install packages, Corbin also uploads `pint_offline_wheels.zip`: unmodified PyPI wheels of pint 0.26.2 and its four pure-Python dependencies, with SHA256 sums that Claude matched against PyPI's published hashes. ChatGPT installs them with `pip install --no-index --find-links`. Claude tested this exact setup offline with ChatGPT's reported versions (pydantic 2.13.5, pytest 9.0.2, PyYAML 6.0.3) on a git archive of `29e256e`: 80 passed, integrity PASSED, 9 probes REJECTED. That was Claude's run, not ChatGPT's. `tools/mutation_check_phase_a.py` needs git history and cannot run on an archive.

**Owner-only merging (P2):** ruleset “main” is active: pull request required, merge commits only, deletion and force-push blocked. **Residual risk:** Claude and ChatGPT both act through Corbin's GitHub account, so “only Corbin merges” is partly procedural, and GitHub's authorship labels do not identify the model (D-051 Amendment 3).

**Review records:** ChatGPT's Phase A review via PR #2 (`79eb168`); its re-review in `docs/reviews/2026-10-21_ChatGPT_ReReview_D052_29e256e.md` (PR #5), open.

**Pass criteria (P7):**

| Criterion | Status |
|---|---|
| Remote holds the intended history and commits | Met (`d04fb78`, `4abb4f1` are ancestors of `main`; tags dropped, Amendment 2) |
| Both models read the same SHA, or a documented fallback was used | Met for reading (`4abb4f1`) |
| Review pinned to a commit with honest test-execution status | Met, twice: `4abb4f1` (nothing executed) and `29e256e` (execution attempted, blocked, reported as such) |
| Builder responded through new commits | Met (PR #3; this records PR) |
| Corbin approved a specific SHA and merged it | Met: PR #3 head `603f1e2` merged as `29e256e` (A-3). Merged before the re-review, so D-052 stays Proposed |
| `PROJECT_STATE.md` and `DECISIONS.md` consistent after the merge | Pending: `main` at `29e256e` is stale (ChatGPT's re-review, MEDIUM finding). Met once this records PR merges, subject to ChatGPT's check |
| *Not a pilot criterion, but open:* independent execution of the checks by ChatGPT | Blocked; retry with offline wheels pending |

## Accepted but unimplemented

- **D-036** minimal hip-only model; **D-037** force-to-torque representation recorded before running (Phase B)
- **D-039 / D-040** remaining phases B–F, including the Phase B boundary (D-039 Amendment 1)

## Open proposals and disagreements

- **D-051** shared repository: pilot in progress; decided after the pilot.
- **D-052** Phase A review response: merged; ChatGPT AGREEs on source review; awaiting Corbin's acceptance and ChatGPT's independent run of the checks.
- **D-049 physical bounds:** pennation bound `[0, π/2)` **accepted by Corbin (Q13, Option A)** as the operational domain of Hill-type models with a cos(pennation) projection, not an anatomical limit; label stored in the schema; revisit with D-037 in Phase B. The 13 positivity bounds **approved by Corbin (Q14)**, labelled definitional. D-049 is Accepted.
- **D-050** caveat (ChatGPT): before any contraction velocity is populated or used dynamically, the datum must state which fiber length normalizes `optimal_fiber_lengths/s` (the schema definition already requires the convention to be declared). Open item for Phase B/C.
- **Q8 and Q9 interpretations (`DECISIONS.md` §4):** Corbin may correct either.
- **Deferred by Corbin until their phase (Q8):** D-028, D-029, D-030, D-032, D-033, D-038.
- **No open disagreements between models.**

## Next task

**Owners:** Corbin and ChatGPT, in parallel.
**Tasks:**
1. **Corbin:** ~~rule on the D-049 pennation bound~~ done (Q13); ~~merge PRs #4 and #5~~ done (A-4). ~~Approve the D-049 positivity bounds~~ done (Q14).
2. **ChatGPT:** with the commit archive of `29e256e` and `pint_offline_wheels.zip`, install pint offline and run `python -m pytest -q`, `python -m src.integrity`, `python tools/review_cycle1_probes.py`. Report the results as an addendum to the re-review on a new branch and PR (one record per review; D-051 item 6). Also check this records PR.
3. **Then:** with execution reproduced and the records consistent, the pilot's P7 criteria are met and Corbin decides on D-051. D-052 and D-049 are accepted or amended by Corbin. Then Phase B (hip-only model), starting with the D-037 force-to-torque choice.

**Required inputs:** this repository; `docs/DECISIONS.md` D-049 to D-052; {RR}.

## Handoff protocol (D-048, as amended by D-051)

1. Start from a pushed commit and state its full SHA.
2. Read this file and the `DECISIONS.md` entries named in the next task.
3. Return: changes as commits on a branch; validation evidence (commands, environment, results); proposals as `Proposed` entries for `DECISIONS.md`; unresolved questions. Reviews are one file in `docs/reviews/`, pinned to a SHA.
4. Update this file at the end of every build or review.
