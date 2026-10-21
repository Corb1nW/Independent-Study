# LB-AO Project State

**Updated:** 2026-10-21
**Updated by:** Claude
**Repository:** `https://github.com/Corb1nW/Independent-Study` (canonical, public; D-051 and its Amendment 1)
**Authoritative snapshot:** branch `main` on the remote, the commit that last changed this file (`git log -1 -- PROJECT_STATE.md`). Phase A implementation: `4abb4f1`. Baseline of the original work: `d04fb78`. LB-AO history imported into this repository at `2814236` (PR #1).
**Component versions:** ontology `hip.yaml` 0.3.0 · schema LB-QPS 0.4.0 · dataset `gluteus_maximus.yaml` 0.3.0 · `DECISIONS.md` revision 6
**Current phase:** **Phase B (hip-only model) starting.** Builder: **ChatGPT**; reviewer: **Claude** (Q17). Phase A complete and reviewed: ChatGPT agreed with D-052 and independently reproduced the software checks at `29e256e`; Corbin accepted D-049, D-051 and D-052.

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
| Source-level re-review | `29e256e` | ChatGPT | reading files at the SHA and the archive | AGREE with D-052; AMEND D-049 and records (since resolved). Record: PR #5 |
| Test suite | `29e256e` archive | **ChatGPT (independent)** | `python -m pytest -q` | **80 passed** (Python 3.13.5, pytest 9.0.2, pydantic 2.13.5, PyYAML 6.0.3, pint 0.26.2 from offline wheels) |
| Integrity check | `29e256e` archive | **ChatGPT (independent)** | `python -m src.integrity` | **PASSED** |
| Review Cycle 1 probes | `29e256e` archive | **ChatGPT (independent)** | `python tools/review_cycle1_probes.py` | **9/9 REJECTED**; the 10-class D3 list is the documented Phase C deferral |
| Archive provenance | `29e256e` archive | ChatGPT | `git hash-object` on 3 files vs GitHub blob SHAs at `29e256e` | 3/3 match (partial corroboration, not full archive verification) |
| Mutation check; new tests vs `4abb4f1` | — | ChatGPT | — | **Not run**: needs git history, absent from the archive |

**Independently reproduced** (ChatGPT, `docs/reviews/2026-10-21_ChatGPT_D052_Execution_Addendum_29e256e.md` (PR #7)): the test suite, integrity check and probes at `29e256e`, which contains the Phase A code and the D-052 fixes. This upgrades those results from author-reported. **Still author-reported:** the mutation check (30 of 47 Phase A tests fail against the old validator), the 11/4 comparison of the new tests against `4abb4f1`, and all results at other snapshots. Independent execution checks software behavior only, never anatomical or biomechanical validity (D-051 item 10). CI is a third-party run and counts as supporting evidence only. PR #6 adds two label tests (82 total at its head), not covered by ChatGPT's run.

## D-051 pilot

**Capabilities (P3)**, as tested 2026-10-20/21:

| Capability | Claude | ChatGPT |
|---|---|---|
| Read files at a given SHA | Yes | Yes (GitHub connector) |
| Check out an arbitrary SHA | Yes | No: native `git clone`/checkout blocked (sandbox cannot resolve github.com) |
| Extract an uploaded archive | Yes | Yes |
| Install requirements and run the checks | Yes | **Yes, with offline wheels** supplied by Corbin (no network to the package index; `pint` not preinstalled). Verified 2026-10-21 (PR #7). The first attempt without wheels was blocked |
| Run git-history tools (mutation check) | Yes | No: archives lack `.git`. A zip including `.git` would allow it |
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
| `PROJECT_STATE.md` and `DECISIONS.md` consistent after the merge | Met by PR #4, which ChatGPT checked and agreed with (PR #7). Its LOW follow-up (execution status superseded) is addressed here (PR #6) |
| *Not a pilot criterion:* independent execution of the checks by ChatGPT | Done via the D-051 item 12 fallback (archive plus offline wheels) |

**Pilot result:** all P7 criteria met. **D-051 accepted by Corbin (Q15).** Git handoffs are now the default; a commit archive (plus offline wheels for ChatGPT) is the fallback.

## Accepted but unimplemented

- **D-036** minimal hip-only model; **D-037** force-to-torque representation recorded before running (Phase B)
- **D-039 / D-040** remaining phases B–F, including the Phase B boundary (D-039 Amendment 1)

## Open proposals and disagreements

- **D-049 physical bounds:** pennation bound `[0, π/2)` **accepted by Corbin (Q13, Option A)** as the operational domain of Hill-type models with a cos(pennation) projection, not an anatomical limit; label stored in the schema; revisit with D-037 in Phase B. The 13 positivity bounds **approved by Corbin (Q14)**, labelled definitional. D-049 is Accepted.
- **D-050** caveat (ChatGPT): before any contraction velocity is populated or used dynamically, the datum must state which fiber length normalizes `optimal_fiber_lengths/s` (the schema definition already requires the convention to be declared). Open item for Phase B/C.
- **Q8 interpretation (`DECISIONS.md` §4):** Corbin may correct it. (Q9 was confirmed by Q12 and superseded by the D-051 acceptance, Q15.)
- **Deferred by Corbin until their phase (Q8):** D-028, D-029, D-030, D-032, D-033, D-038.
- **No open disagreements between models.**

## Next task

**Owner:** ChatGPT (builder). Reviewer: Claude. Approver: Corbin (Q17).
**Task: Phase B, hip-only model** (D-036; effective Phase B row in D-040 Amendment 1; boundary in D-039 Amendment 1).

1. **First, D-037 (force-to-torque representation), before any simulation runs.** Propose a constant moment arm or a sourced r(q) curve as a `Proposed` entry in `DECISIONS.md`. Declare the coordinate and torque sign convention, valid angle range, units, applicability, and whether force is whole-muscle or one compartment. Keep it as a model assumption, separate from anatomical observations. Revisit the pennation bound at the same time (D-049 Amendment 2). Open a small PR; Claude reviews; Corbin approves before step 2.
2. **Build:** pelvis plus thigh, sagittal hip. Resolve gluteus maximus parameters from the YAML through the validator (passing each dataset, D-052). Use an equation of motion and integrator, a perturbation test (a YAML change produces an explainable output change), basic numerical checks, and a lightweight run manifest recording every number used, with its source, units and the commit SHA.
3. **Inputs not yet in the data** (segment inertia, geometry, initial conditions) need provenance (D-036). Anatomical values go in the data with source claims. Demonstration assumptions go in the model configuration, labelled as assumptions. If contraction velocity is used, declare its normalization first (D-050 caveat).

**Exit criterion (D-040 Amendment 1):** input-resolution record, declared dynamics assumptions, baseline and perturbation results, basic numerical checks, exact commit. Physiological or clinical validity is not implied.
**Working rules (D-051):** branches `phase-b/chatgpt-<topic>`; PR descriptions carry the handoff minimum (item 4); state what was executed; new dependencies go in `requirements.txt` and must run in CI. Claude reviews each PR at its head SHA and reruns the checks.
**Required inputs:** this repository; `docs/DECISIONS.md` D-014, D-015, D-021, D-036, D-037, D-039, D-040, D-049, D-050, D-052; `ontology/quantitative_data/gluteus_maximus.yaml`.

## Handoff protocol (D-048, as amended by D-051)

1. Start from a pushed commit and state its full SHA.
2. Read this file and the `DECISIONS.md` entries named in the next task.
3. Return: changes as commits on a branch; validation evidence (commands, environment, results); proposals as `Proposed` entries for `DECISIONS.md`; unresolved questions. Reviews are one file in `docs/reviews/`, pinned to a SHA.
4. Update this file at the end of every build or review.
