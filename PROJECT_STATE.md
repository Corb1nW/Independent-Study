# LB-AO Project State

**Updated:** 2026-10-27
**Updated by:** Claude (records cleanup and Phase C scope proposal, Q28)
**Repository:** `https://github.com/Corb1nW/Independent-Study` (canonical, public; D-051 and its Amendment 1)
**Authoritative snapshot:** branch `main` on the remote, the commit that last changed this file (`git log -1 -- PROJECT_STATE.md`). Phase A implementation: `4abb4f1`. Baseline of the original work: `d04fb78`. LB-AO history imported into this repository at `2814236` (PR #1).
**Component versions:** ontology `hip.yaml` 0.3.0 · schema LB-QPS 0.4.0 · dataset `gluteus_maximus.yaml` 0.3.0 · `DECISIONS.md` revision 12
**Current phase:** **Phase B complete.** The hip-only model (D-036, D-053) was built by ChatGPT, reviewed by Claude (AMEND, AMEND, AGREE), accepted by Corbin at `354984c` (Q19) and merged as `29e10d0`. The official run is `results/phase_b/2026-10-27_phase_b_runs_6c8b6ef.json`, made at `6c8b6ef`. **Next: Phase C, slimmed** (D-055, Proposed). Claude builds (Q28); reviewer read as ChatGPT. The build starts once Corbin approves the D-055 scope.

## Implemented work

**Role skills (D-054, Proposed; merged as `9cc3963`, A-6):** one-page Builder and Reviewer skills in `docs/skills/`, meant to be installed in both models by Corbin (Claude's installed copies checked against the repository; ChatGPT's not observable). The longer protocol candidate they replaced is archived, not in force, in `docs/archive/protocol-v0.2-candidate/` (closed PR #16).

**Phase B (D-036, D-053; PR #13 merged `29e10d0`, accepted at `354984c`, Q19):** `src/hip_phase_b.py` resolves the Arnold 2010 whole-muscle `Fmax` through the validated resolver, applies D-053's constant signed moment arm `τ = −r0·a·F` to a one-DOF right hip (`LB:DOF:HIP_FLEX_EXT_R` in `LB:FRAME:PELVIS`), and integrates exactly, with event-terminated exits from `[−π/6, π/3]`. `config/phase_b_hip.yaml` labels every number a demonstration assumption (`r0` = 0.04 m, `I` = 1 kg·m², activation 0.02, tuned for an observable exit time) and declares the omitted physics. The scenario overlays (×1.0, ×1.2 right only) never edit the evidence. `tools/run_phase_b.py` writes a manifest that verifies the commit and all 10 consumed files and refuses dirty or external inputs (Windows and Linux). `tests/test_phase_b.py` holds 22 tests. Official run: `results/phase_b/2026-10-27_phase_b_runs_6c8b6ef.json`.

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
| Phase B reviews | `bf92dfd`, `5285670`, `354984c` | **Claude (reviewer, independent of the builder)** | pytest, integrity, probes and runner at each SHA; mutation and adversarial checks; Windows-style CRLF checkout | AMEND → AMEND (D1) → **AGREE**. At `354984c`: 104 passed (LF and CRLF), integrity PASSED, 9/9 REJECTED |
| **Phase B official run** | `6c8b6ef` (`main`; code identical to `354984c`) | Claude | `python -m tools.run_phase_b --commit-sha 6c8b6ef… --output results/phase_b/2026-10-27_phase_b_runs_6c8b6ef.json` (Python 3.13.16, pydantic 2.14.1, pint 0.26.2, PyYAML 6.0.3) | Provenance `verified_git_head_and_inputs` (10 files). Baseline: `F` = 1852.6 N, `τ` = −1.48208 N·m, domain exit (lower) at **0.840578902667 s**. ×1.2 right: `F` = 2223.12 N, `τ` = −1.778496 N·m, exit at **0.767340043923 s**. Ratio 0.912871 = 1/√1.2 (difference 3e-16); baseline equals the closed form. Left `F` unchanged. Tests at `6c8b6ef`: 104 passed, integrity PASSED, 9/9 REJECTED |

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

- **D-039 / D-040** remaining phases C–F (D-036 and D-037/D-053 are implemented in Phase B)

## Open proposals and disagreements

- **D-049 physical bounds:** pennation bound `[0, π/2)` **accepted by Corbin (Q13, Option A)** as the operational domain of Hill-type models with a cos(pennation) projection, not an anatomical limit; label stored in the schema; revisit with D-037 in Phase B. The 13 positivity bounds **approved by Corbin (Q14)**, labelled definitional. D-049 is Accepted.
- **D-050** caveat (ChatGPT): before any contraction velocity is populated or used dynamically, the datum must state which fiber length normalizes `optimal_fiber_lengths/s` (the schema definition already requires the convention to be declared). Open item for Phase C or whenever contraction velocity is first used (not used in Phase B).
- **Q8 interpretation (`DECISIONS.md` §4):** Corbin may correct it. (Q9 was confirmed by Q12 and superseded by the D-051 acceptance, Q15.)
- **Deferred by Corbin until their phase (Q8):** D-028, D-029, D-030, D-032, D-033, D-038.
- **D-054 role skills:** in use since A-6; Corbin's explicit confirmation requested, including two new rules (model-name line in commits and PRs; review exemption for small wording fixes). ChatGPT has not yet reviewed Claude's Reviewer skill.
- **D-055 slim Phase C:** scope proposed (C1 reusable run manifest with git blob IDs; C2 meaning of Arnold `Fmax`; C3 velocity normalization; C4 input gate; C5 growth test; C6 result plot, included by Corbin, Q29). C4 narrowed to traceability after ChatGPT's review (R18-03). Awaiting ChatGPT's re-review and Corbin's approval.
- **Q29 conflict:** Corbin answered both “Not yet” (D-055) and “Build in parallel”. Claude has asked which applies and has not started the build.
- **Q28 interpretation (`DECISIONS.md` §4):** reviewer for Phase C read as ChatGPT; Corbin may correct it.
- **No open disagreements between models.**

## Next task

**Owner:** Corbin, then Claude (Phase C builder, Q28).
1. **Merge the records PR** for revision 12 (cleanup, D-054, D-055) after ChatGPT's review, or approve D-055 directly so the build can start while ChatGPT reviews.
2. **Approve, amend or reject D-055** (slim Phase C scope; C6 included, Q29), and say whether Claude builds now as a BLOCKED draft or waits.
3. **Claude builds Phase C** on a `phase-c/claude-…` branch: C1–C6, tests, a reproduced Phase B run at the new commit. ChatGPT reviews the pinned head SHA with the Reviewer skill.

**Exit criterion (D-055):** C1–C5 done with tests; growth test passes; Arnold `Fmax` meaning recorded with its source; reviewed and accepted. Then Phase D (planar squat).
**Deferred by D-055 to first use:** D-029, D-030, D-032, D-033, broad anatomy evidence migration, deferred-attachment records, entity-ID aliases. D-028 and D-038 stay in Phase E.
**Required inputs:** this repository; `docs/DECISIONS.md` D-039, D-040, D-049, D-050, D-053, D-055; `results/phase_b/2026-10-27_phase_b_runs_6c8b6ef.json`; the three Phase B build reviews in `docs/reviews/`.

## Handoff protocol (D-048, as amended by D-051)

1. Start from a pushed commit and state its full SHA.
2. Read this file and the `DECISIONS.md` entries named in the next task.
3. Return: changes as commits on a branch; validation evidence (commands, environment, results); proposals as `Proposed` entries for `DECISIONS.md`; unresolved questions. Reviews are one file in `docs/reviews/`, pinned to a SHA.
4. Update this file at the end of every build or review.
