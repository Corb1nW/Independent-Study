# LB-AO Project State

**Updated:** 2026-11-10
**Updated by:** Claude (D2 post-merge review fixes, D-059 Amendment 4)
**Repository:** `https://github.com/Corb1nW/Independent-Study` (canonical, public; D-051 and its Amendment 1)
**Authoritative snapshot:** branch `main` on the remote, the commit that last changed this file (`git log -1 -- PROJECT_STATE.md`). Phase A implementation: `4abb4f1`. Baseline of the original work: `d04fb78`. LB-AO history imported into this repository at `2814236` (PR #1).
**Component versions:** ontology `hip.yaml` 0.3.0 + `lower_limb_sagittal.yaml` 0.2.0 · schema LB-QPS 0.7.0 · datasets `gluteus_maximus.yaml` 0.3.1, `segments_gait2392.yaml` 0.1.0, `segments_de_leva_1996.yaml` 0.1.0, `muscles_gait2392.yaml` 0.1.0 · `DECISIONS.md` revision 22
**Current phase:** **Phase D: Stage D1 accepted; Stage D2 scope D-059 Accepted at `7358c2d` (Q58) after ChatGPT's AGREE (PR #33); Stage D2 implemented and merged by Corbin (A-13; official run at `7ac0f2d`); ChatGPT's post-merge review (PR #36) reproduced the results exactly and asked for two configuration guards, fixed in D-059 Amendment 4 (re-review pending).** Female body: muscles suffice. Male and Gait2392: flagged near the bottom (largest reserve 5.8 and 6.4 N·m), a result traced to D1's fixed-centre knee (with Gait2392's moving-knee geometry the muscles suffice); accepted as the reading of the result (Q59, P1 option (a)).** D-056 is Accepted (Q53). D-059 specifies:
- instantaneous optimization on D1's official torques, with 14 Gait2392 actuators per leg (main squat muscles plus tibialis anterior; Q54, Q57) and a reserve check (Q57), made exact by a two-stage rule (Amendment 2: smallest largest per-joint reserve first, then minimum effort);
- the De Groote force law with rigid tendons and no passive force in the baseline;
- OpenSim 4.6 as an independent verification oracle;
- muscles drawn on the page, coloured by effort (Q55).

Awaiting ChatGPT's review and Corbin's decision; Claude builds after acceptance (Q38 interpretation). Stage D1 remains as accepted at `3b86cc4` (official run `dd89fff`).

## Implemented work

**Phase D, Stage D2 (D-059 with Amendments 1–3; merged A-13; P1 (a) and P2 accepted, Q59):** `src/muscles_d2.py` (Gait2392 path geometry on D1's chain with OpenSim's SimmSpline and conditional-point rule; De Groote rigid-tendon force law, constants read from the vendored header, domain policy; two-stage recruitment: HiGHS LP, quadprog QP, second solvers HiGHS interior point and Clarabel; limiting-joint diagnostic), `ontology/quantitative_data/muscles_gait2392.yaml` (generated), `lower_limb_sagittal.yaml` 0.2.0 (knee and ankle muscles, nerves, 14 model actuators), schema LB-QPS 0.7.0, `config/phase_d2_muscles.yaml`, `tools/make_d2_oracle.py` and `tests/data/d2_oracle_reference.json` (OpenSim 4.6), `tools/run_phase_d2.py`, `tools/sensitivity_d2.py`, `tools/build_d2_page.py`, `tests/test_phase_d2.py` (35 tests). Results in `results/phase_d/2026-11-10_d2_*_7ac0f2d.*`.

**Phase D, Stage D1 (D-058; accepted at `3b86cc4`, Q51; merged `3b6f6e6`, A-12; proposals (a)–(f) accepted, Q50):** `src/squat_d1.py` (Newton–Euler inverse dynamics; independent symbolic Lagrange formulation; static, energy, Newton, one-step forward and closed-form checks; contact feasibility), `config/phase_d1_squat.yaml` (all values labeled), two generated segment datasets from kept source copies, a second ontology module and multi-file loading, `tools/run_phase_d1.py` (manifest), `tools/build_squat_page.py` (animated page), `tests/test_phase_d1.py` (33 tests at the build; 36 test functions at `3b86cc4`). Results in `results/phase_d/`; the official run, sensitivity analysis and page are at `dd89fff`.

**Phase C (D-055 Amendment 1; accepted at `506ece5`, Q36; merged `fe705de`, A-8):** shared run manifest with git blob IDs and a fixed validity block (`src/run_manifest.py`); Arnold `Fmax` source check recorded on the datum and proposed as D-056; contraction-velocity normalization required by the schema (LB-QPS 0.5.0); traceability gate for model inputs (`src/input_gate.py`), enforced in the Phase B resolver; growth test with a knee stub; result plot (`tools/plot_phase_b.py`). Tests in `tests/test_phase_c.py`. **Source list (D-057, Accepted Q37):** `sources/SOURCES.md` lists every unique source; rule in `sources/README.md`; enforced for registered IDs and notes links by `tests/test_sources.py`.

**Role skills (D-054, Accepted Q32; merged as `9cc3963`, A-6):** one-page Builder and Reviewer skills in `docs/skills/`, meant to be installed in both models by Corbin (Claude's installed copies checked against the repository; ChatGPT's not observable). The longer protocol candidate they replaced is archived, not in force, in `docs/archive/protocol-v0.2-candidate/` (closed PR #16).

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
| Test suite, integrity, probes | `fa2e8fb` (Phase C build) | Claude | `python -m pytest -q`; `python -m src.integrity`; `python tools/review_cycle1_probes.py` (Python 3.13.18, pydantic 2.13.5, pint 0.26.2, PyYAML 6.0.3, pytest 9.1.1) | **133 passed** (29 new in `tests/test_phase_c.py`); integrity PASSED; 9/9 REJECTED |
| Mutation check, Phase C rules | `fa2e8fb` in a temporary worktree | Claude | normalization rule disabled; C4 check (d) disabled | 6 of 9 C3 tests fail; 1 of 8 C4 tests fails (the (d) test); the remaining tests cover other rules |
| Phase B run reproduced through the shared manifest (D-055 C1) | `fa2e8fb` | Claude | `python -m tools.run_phase_b --commit-sha fa2e8fbfb0300e49a8e97e7ba272b9b820dfefe9 --output results/phase_b/2026-10-27_phase_b_runs_fa2e8fb.json` | Provenance `verified_git_head_and_inputs` (12 files, each with a git blob ID); traceability gate passed; `simulation` and `effective_values` **identical** to the official run at `6c8b6ef` (exits 0.840578902667 s and 0.767340043923 s). A builder's reproduction, not a new official run |
| Figure (D-055 C6) | manifest at `fa2e8fb` | Claude | `python -m tools.plot_phase_b --manifest results/phase_b/2026-10-27_phase_b_runs_fa2e8fb.json --output results/phase_b/2026-10-27_phase_b_hip_angle_fa2e8fb.svg` | Rendered and inspected; carries the manifest's validity statement and commit |
| Test suite, integrity, probes | `38d5bdf` (Stage D1 build) | Claude | `python -m pytest -q`; `python -m src.integrity`; `python tools/review_cycle1_probes.py` (Python 3.13.18, numpy 2.5.3, sympy 1.14.0, pydantic 2.13.5, pint 0.26.2, PyYAML 6.0.3, pytest 9.1.1) | **169 passed** (33 new in `tests/test_phase_d1.py`); integrity PASSED; 9/9 REJECTED |
| Stage D1 run (D-058) | `38d5bdf` | Claude | `python -m tools.run_phase_d1 --commit-sha 38d5bdf98b1ef73162c96344b3a5fa32fc7e621a --output results/phase_d/2026-10-28_d1_squat_runs_38d5bdf.json` | Provenance `verified_git_head_and_inputs` (17 files). Female, male and Gait2392: every mechanics check passed (residuals about 1e-13 against tolerances of 1e-8 or tighter; one-step forward error falls 32-fold per halving); contact feasible throughout (centre of pressure −2.3 to 4.2 cm from the ankle within the heel–ball support; grip needed about 0.02). Peak knee torque per leg about −74 (female), −87 (male), −91 N·m (Gait2392). Idealized mechanics verified; not validated against measured squats |
| Phase B reproduced after the D1 changes | `38d5bdf` | Claude | `python -m tools.run_phase_b --commit-sha 38d5bdf…` | `simulation` and `effective_values` identical to the official run at `6c8b6ef`; provenance verified (now also lists `lower_limb_sagittal.yaml`) |
| Squat viewer page (D-058 item 11) | manifest at `38d5bdf` | Claude | `python -m tools.build_squat_page --manifest results/phase_d/2026-10-28_d1_squat_runs_38d5bdf.json --output results/phase_d/2026-10-28_d1_squat_viewer_38d5bdf.html` | Rendered at desktop (light) and phone (dark) widths and inspected; no horizontal scroll; no script errors |
| After ChatGPT's review (D-058 Amendment 3) | `9988620` | Claude | pytest; integrity; probes; `python -m tools.build_segment_datasets --check`; `python -m tools.run_phase_d1 --commit-sha 9988620c3351608ab78dd951d5378e2b261e0da9 --output results/phase_d/2026-10-28_d1_squat_runs_9988620.json`; `python -m tools.sensitivity_d1 --output results/phase_d/2026-10-28_d1_sensitivity_9988620.json`; page builder; Phase B runner | **175 passed** (39 in D1); integrity PASSED; 9/9 REJECTED; datasets current. D1 run: exit 0; mechanics PASSED, contact FEASIBLE, sources provisional for all three bodies; short-horizon forward error 5e-11 rad at 1 ms. Sensitivity table in `results/phase_d/2026-10-28_d1_sensitivity_9988620.md`. Phase B output identical. Page rendered, no script errors |
| Re-review follow-up (D1-R07, D1-R08) | `0146e42` | Claude | `python -m pytest -q`; `python -m src.integrity`; `python tools/review_cycle1_probes.py`; `python -m tools.build_segment_datasets --check`; `python -m tools.run_phase_d1 --commit-sha 0146e425769e0c0d5d9782ef2e3a0cfcf11e7e5a …`; `python -m tools.run_phase_b --commit-sha 0146e42… …`; `python -m tools.sensitivity_d1 --commit-sha 0146e42… --output results/phase_d/2026-10-28_d1_sensitivity_0146e42.json --markdown …md` | **178 passed**; integrity PASSED; 9/9 REJECTED; datasets current. D1 runner exit 0, series and statuses identical to the `9988620` run. Phase B runner identical to the official run. Sensitivity output provenance `verified_git_head_and_inputs` (18 files); knee-centre case now +7.7% (female), +7.8% (male), +8.9% (Gait2392) knee peak, margin 12–13 mm, feasible |
| Stage D1 source-level reviews | `0aa4651`, `9988620`, `3b86cc4` | **ChatGPT (reviewer, independent of the builder)** | reading files at each SHA (GitHub connector) | AMEND → AMEND → **AGREE**. Records: PRs #24 and #26 |
| Verification package (builder's check) | `3b86cc4` | Claude | the commands in the package's instructions, offline, from the zip: Python 3.13.18 with pydantic 2.13.5, pytest 9.0.2 and PyYAML 6.0.3 preinstalled, the rest from the packaged wheels | 178 passed with a clean git config (this host's commit-signing setting otherwise fails 8 git-fixture tests; an environment issue, now covered in the instructions); integrity PASSED; 9/9 REJECTED; datasets current; outputs equal to the committed results apart from the expected metadata. Packaging check only, not independent |
| **Stage D1 independent execution** | `3b86cc4` (git bundle; HEAD and a blob ID checked against GitHub) | **ChatGPT (independent of the builder)** | pytest; integrity; probes; dataset check; D1, Phase B and sensitivity runners; its own comparison program (CPython 3.12.14, NumPy 2.3.5, pydantic 2.14.1, pytest 9.2.0, PyYAML 6.0.3, SymPy 1.14.0, Pint 0.26.2) | **AGREE.** 178 passed, integrity PASSED, 9/9 REJECTED, datasets current; D1 manifest: 20,570 values compared, 0 numeric differences (3 metadata differences: commit and model-file hash); sensitivity differs only in commit; Phase B `simulation` and `effective_values` exact. Record: PR #27 |
| **Official Stage D1 run** | `dd89fff` (`main` after A-12; Stage D1 code identical to `3b86cc4`) | Claude | `python -m pytest -q` (clean git config); `python -m src.integrity`; `python tools/review_cycle1_probes.py`; `python -m tools.build_segment_datasets --check`; `python -m tools.run_phase_d1 --commit-sha dd89fff908eb9f5002c2f62d36bccf5bc6694330 --output results/phase_d/2026-11-04_d1_squat_runs_dd89fff.json`; `python -m tools.sensitivity_d1 --commit-sha dd89fff… --output results/phase_d/2026-11-04_d1_sensitivity_dd89fff.json --markdown …md`; `python -m tools.build_squat_page --manifest results/phase_d/2026-11-04_d1_squat_runs_dd89fff.json --output results/phase_d/2026-11-04_d1_squat_viewer_dd89fff.html`; Phase B runner (Python 3.13.18, numpy 2.5.4, sympy 1.14.0, pint 0.26.2, pydantic 2.13.5, PyYAML 6.0.3, pytest 9.0.2) | 178 passed; integrity PASSED; 9/9 REJECTED; datasets current. D1: exit 0; all three bodies mechanics PASSED, contact FEASIBLE, sources provisional; provenance `verified_git_head_and_inputs` (17 files); equal to the `9988620` run apart from `commit_sha` and the model file's hash. Sensitivity: provenance verified (18 files); equal to `0146e42` apart from `commit_sha`. Page equal to the `9988620` page once commit and date are normalized. Phase B output identical to the official run |
| Test suite, integrity, probes, datasets | `7ac0f2d` (Stage D2 build) | Claude | `python -m pytest -q` (clean git config); `python -m src.integrity`; `python tools/review_cycle1_probes.py`; `python -m tools.build_segment_datasets --check` (Python 3.13.18, numpy 2.5.3, scipy 1.18.1, quadprog 0.1.14, clarabel 0.11.1, sympy 1.14.0, pydantic 2.13.5, pint 0.26.2, PyYAML 6.0.3, pytest 9.1.1) | **213 passed** (35 in `tests/test_phase_d2.py`); integrity PASSED; 9/9 REJECTED; datasets current |
| D2 oracle reference | `tools/make_d2_oracle.py` at the build | Claude | `python -m tools.make_d2_oracle --output tests/data/d2_oracle_reference.json` (opensim 4.6 from PyPI) | 322 geometry states, 192 force states, 31 unmodified-model states. Implementation vs OpenSim: lengths and moment arms within 4e-16 m, intermediates within 2e-15, tendon force within 1.6e-11 N |
| Mutation check, D2 tests | build | Claude | 8 deliberate faults in `src/muscles_d2.py` | each fault fails 1–7 tests |
| **Stage D2 run (D-059)** | `7ac0f2d` | Claude | `python -m tools.run_phase_d2 --commit-sha 7ac0f2d2d83752d43f85a4221923f43f54e26b61 --d1-manifest results/phase_d/2026-11-04_d1_squat_runs_dd89fff.json --output results/phase_d/2026-11-10_d2_muscle_runs_7ac0f2d.json`; `python -m tools.sensitivity_d2 …`; `python -m tools.build_d2_page …` | Exit 0; provenance `verified_git_head_and_inputs` (24 files). All bodies: D1 consistency PASSED (difference 0), optimizer PASSED (KKT ≤ 1.1e-11; second solvers within 5.6e-7), force-law domain IN_DOMAIN. Muscle feasibility: female FEASIBLE; male and Gait2392 FLAGGED 1.39–1.66 s (t* 5.815 and 6.362 N·m). Sensitivity: unmodified Gait2392 geometry gives t* = 0. Page rendered at desktop (light) and phone (dark) widths; no horizontal scroll; no script errors |
| **Stage D2 independent execution** | `b9e96ed` | **ChatGPT (independent of the builder)** | pytest; integrity; probes; dataset check; OpenSim oracle; D2 runner; sensitivity; page builder; its own comparator (CPython 3.12.14, NumPy 2.3.5, SciPy 1.17.0, quadprog 0.1.14, Clarabel 0.11.1, OpenSim 4.6) | **AMEND** (D2-B01, D2-B02). 213 passed; integrity PASSED; 9/9 REJECTED; oracle 44,034 values and default run 153,757 values identical to the committed files; sensitivity within 1.8e-8; page byte-identical. Knee explanation confirmed with OpenSim (knee translations restored: t* = 0 at all 301 states). Record: PR #36 |

**Independently reproduced** (ChatGPT, `docs/reviews/2026-10-21_ChatGPT_D052_Execution_Addendum_29e256e.md` (PR #7)): the test suite, integrity check and probes at `29e256e`, which contains the Phase A code and the D-052 fixes. This upgrades those results from author-reported. **Still author-reported:** the mutation check (30 of 47 Phase A tests fail against the old validator), the 11/4 comparison of the new tests against `4abb4f1`, and all results at other snapshots. Independent execution checks software behavior only, never anatomical or biomechanical validity (D-051 item 10). CI is a third-party run and counts as supporting evidence only. PR #6 adds two label tests (82 total at its head), not covered by ChatGPT's run.

**Independently reproduced, Stage D1** (ChatGPT, `docs/reviews/2026-11-04_ChatGPT_D1_Execution_Addendum_3b86cc4.md` (PR #27)): the test suite, integrity check, probes, dataset check and the D1, Phase B and sensitivity runners at `3b86cc4`, with exact output equality against the committed results. ChatGPT limits its independence claim to the Claude-authored D1 behaviour; the Phase B regression is its own code, so a self-check.

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

- **D-039 / D-040** remaining phases: Stage D2, E and F (implemented so far: D-036 and D-037/D-053 in Phase B, D-055 in Phase C, D-058 Stage D1)
- **D-056** fiber-force reading of maximum isometric force: Accepted (Q53); first used by Stage D2's force law (D-059, if accepted)

## Open proposals and disagreements

- **D-049 physical bounds:** pennation bound `[0, π/2)` **accepted by Corbin (Q13, Option A)** as the operational domain of Hill-type models with a cos(pennation) projection, not an anatomical limit; label stored in the schema; revisit with D-037 in Phase B. The 13 positivity bounds **approved by Corbin (Q14)**, labelled definitional. D-049 is Accepted.
- **D-050** caveat (ChatGPT): before any contraction velocity is populated or used dynamically, the datum must state which fiber length normalizes `optimal_fiber_lengths/s` (the schema definition already requires the convention to be declared). Open item for Phase C or whenever contraction velocity is first used (not used in Phase B).
- **Q8 interpretation (`DECISIONS.md` §4):** Corbin may correct it. (Q9 was confirmed by Q12 and superseded by the D-051 acceptance, Q15.)
- **Deferred by Corbin until their phase (Q8):** D-028, D-029, D-030, D-032, D-033, D-038.
- **D-054 role skills:** Accepted with both new rules (Q32). ChatGPT has not yet reviewed Claude's Reviewer skill.
- **D-055 slim Phase C:** Accepted (Q32); implemented and accepted at `506ece5` (Q36).
- **D-056 meaning of Arnold `Fmax`:** **Accepted (Q53)**: whole-muscle maximum fiber force, projected once by cos(pennation); labeled an interpretation. Quotes checked against the PDF by Claude; ChatGPT could not open the source.
- **D-057 source list:** Accepted (Q37); in both role skills (A-9), reinstalled in both models (Q38, reported by Corbin).
- **Q29 conflict:** resolved by Q31 (wait for review).
- **Q28 interpretation (`DECISIONS.md` §4):** reviewer for Phase C read as ChatGPT; Corbin may correct it.
- **D-058 Phase D:** Accepted at `787e5a6` (Q40). Amendment 2 (Q41–Q44): Gait2392 geometry, de Leva fractions via the BMC open data, three bodies. Open concerns 6–9: de Leva values not checked against the paper; Gait2392 stature (1.8 m documented, about 1.66 m measured by a forum user); radius-of-gyration column is an interpretation; de Leva bodies borrow Gait2392's HAT shape and foot. Six proposals in the build Accepted (Q50); Stage D1 build Accepted at `3b86cc4` (Q51), merged (A-12). Amendment 3 (Q45–Q47): HAT shape from Gait2392 approved; de Leva values provisional; whole-motion forward check replaced. Sensitivity: Gait2392 stature 1.66 m instead of 1.8 m raises knee torque about 9%; knee-centre location 8–9%; HAT position changes hip torque by about 4–5 N·m.
- **Q40 interpretation:** read as acceptance of D-058; Corbin may correct it.
- **Q38 interpretation:** Phase D reviewer read as ChatGPT; Corbin may correct it.
- **Q50 principle on simplifications:** recorded as Corbin's stated principle; he chose to record the quote only (Q52), so there is no new rule or file.
- **D-059 Stage D2 scope:** Proposed. Builder's pre-check: thin knee-extensor margin at the bottom (about 7% for the Gait2392 body); rigid-tendon passive soleus artifact at 40° dorsiflexion, so the baseline excludes passive force. ChatGPT's review at `a3efd33` (PR #31): AMEND, D2-R01 to D2-R03 (reserve semantics, force-law and domain contract including fiber damping inherited as 0.1 through `replaceMuscles`, verification of the assembled force and the eight path switches inside D1's knee range). All accepted after Claude checked them; addressed in D-059 Amendment 1. The reserve rule is Corbin's choice. ChatGPT's re-review at `936c12c` (PR #32): AMEND; D2-R02, D2-R03, L01, L02 resolved; D2-R01 in part (a sum-of-squares stage 1 does not certify a per-joint allowance) and new D2-R04 (path length jumps at conditional via points; confirmed in OpenSim 4.6, up to 0.35 mm for medial gastrocnemius). Addressed in Amendment 2.
- **Q38 interpretation for Stage D2:** Claude builds, ChatGPT reviews; Corbin may correct it.
- **No open disagreements between models.**

## Next task

**Owner:** Corbin (merge ChatGPT's review PR #36); ChatGPT (re-review the configuration-guard fix PR); Corbin (merge; next stage).
1. **ChatGPT re-reviews the D2 fixes** (D-059 Amendment 4) at the head of their PR: D2-B01 and D2-B02, and the D2-BN01 coverage.
2. **Corbin merges** PR #36 and the fix PR.
3. **Corbin decides the next stage.** Builder's recommendation: a moving knee for D1 and D2 (P1 option (b)), before muscle results are cited; then Phase E (conditions).

**Required inputs:** this repository; `docs/DECISIONS.md` D-008, D-022, D-050, D-055, D-056, D-058, D-059; the official D1 run in `results/phase_d/` (`dd89fff`); `sources/vendor/`; `sources/SOURCES.md`.

## Handoff protocol (D-048, as amended by D-051)

1. Start from a pushed commit and state its full SHA.
2. Read this file and the `DECISIONS.md` entries named in the next task.
3. Return: changes as commits on a branch; validation evidence (commands, environment, results); proposals as `Proposed` entries for `DECISIONS.md`; unresolved questions. Reviews are one file in `docs/reviews/`, pinned to a SHA.
4. Update this file at the end of every build or review.

## Review handoff — D-059 Amendment 2 (2026-11-10; superseded: D-059 Accepted, Q58, and Stage D2 merged, A-13)

**Reviewed by (model): ChatGPT.** PR #30 at `7358c2dbb6af373b477d7c71a14a520a853f36c5` (base `2f7cf983cb1660ae3f0fb8d08fbe51b69ceabe7e`); comparison from `936c12c9fe72a128c629a62f6cd67fd367fded7b`. **AGREE**, scoped to the amended L∞ reserve rule (D2-R01) and path-switch transition policy (D2-R04); both resolved at proposal level. Earlier resolved items remain closed. No blocking findings.

Authoritative review: [`2026-11-10_ChatGPT_D2_Amendment2_ReReview_7358c2d.md`](docs/reviews/2026-11-10_ChatGPT_D2_Amendment2_ReReview_7358c2d.md). Tests: 178 passed; integrity PASSED; probes 9/9 REJECTED; generated datasets current. Review-only mathematical/geometry probes passed; OpenSim not run and D2 not yet built. Nonblocking N01 carries numerical-band reporting into the build review.

**Next:** Corbin decides D-059 at the reviewed SHA; if approved, Claude builds Stage D2 and ChatGPT reviews the build. No approval or merge is inferred. This handoff supplements the main-branch snapshot above; PR #30 contains the pending proposal and its fuller state update. **Status: REVIEWED, NOT APPROVED.**
