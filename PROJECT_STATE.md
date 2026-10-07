# LB-AO Project State

**Updated:** 2026-10-07
**Updated by:** Claude
**Authoritative snapshot:** branch `main`, the commit that last changed this file (`git log -1 -- PROJECT_STATE.md`). Phase A implementation: `4abb4f1`. Baseline of the original work: `d04fb78`.
**Component versions:** ontology `hip.yaml` 0.3.0 · schema LB-QPS 0.4.0 · dataset `gluteus_maximus.yaml` 0.3.0 · `DECISIONS.md` revision 3
**Current phase:** **Phase A (Integrity) built; awaiting ChatGPT's review.** Phase B not started.

## Implemented work

**Phase A (`4abb4f1`; D-024, D-025, D-026, D-027, D-031, D-034, D-035; choices in D-050)**
- **Layered validator:** structural (`src/datum_model.py`, Pydantic) → semantic (vocabularies, property definitions, units via pint, physical bounds, ontology references) → evidence (sources, assumptions, derivations, applicability), in `src/quantitative.py`.
- **Cross-file integrity check:** `src/integrity.py`, run with `python -m src.integrity`.
- **Data fixes D1–D9** (D9 found during Phase A: a truncated YAML note). Details are in the D-024 Amendment 1.
- **Hip joint** now receives joint kinematic and kinetic properties through `class_hierarchy` (D-031).
- **Adductor magnus dual innervation** added after verification against StatPearls (D-034).
- **Ward 2009 fiber-length normalization** verified against the primary source and recorded (D-019).
- **One defaults function** with explicit-field precedence (D6).
- **47 new tests** in `tests/test_phase_a.py`; 2 baseline tests adapted (listed in D-050).

**Earlier:** baseline `d04fb78`; review documents in `docs/reviews/`; probe script `tools/review_cycle1_probes.py`; `docs/DECISIONS.md` (D-001 to D-050).

## Validation

Environment: Python 3.13.16, PyYAML 6.0.3, pytest 9.1.1, pydantic 2.13.5, pint 0.26.1 (minimums in `requirements.txt`).

| Check | Snapshot | Run by | Command | Result |
|---|---|---|---|---|
| Test suite | `d04fb78` | Claude | `python -m pytest -q` | 18 passed |
| Test suite | `4abb4f1` | Claude | `python -m pytest -q` | 65 passed |
| Mutation check: new tests vs. old validator | `4abb4f1` with the baseline `validate_datum` swapped in | Claude | `python tools/mutation_check_phase_a.py` | 30 of 47 Phase A tests fail (the other 17 test data and structure, not the validator) |
| Integrity check | `d04fb78` data, Phase A checker | Claude | `python -m src.integrity` | FAILED, 48 problems: 44 deprecated `pennation_angle` names (D2), 2 unresolved coordinates (D1), Fmax without `model_id` (D6), MUSCLE_FORCE junk key (D9) |
| Integrity check | `4abb4f1` | Claude | `python -m src.integrity` | PASSED |
| Review Cycle 1 probes | `d04fb78` | Claude | `python tools/review_cycle1_probes.py` | All 9 validator probes ACCEPTED; D1, D2, D3, D5 findings present |
| Review Cycle 1 probes | `4abb4f1` | Claude | `python tools/review_cycle1_probes.py` | All 9 validator probes **REJECTED**; no D1, D2 or D5 findings; D3 list down from 11 to 10 classes (hip joint fixed; the rest is Phase C per D-031) |

**Reported, not independently reproduced:** all Phase A results above (ChatGPT review pending).

## Accepted but unimplemented

- **D-036** minimal hip-only model; **D-037** force-to-torque representation recorded before running (Phase B)
- **D-039 / D-040** remaining phases B–F, including the Phase B boundary (D-039 Amendment 1)

## Open proposals and disagreements

- **D-049 physical bounds:** implemented to close probe 3. The bound values await review, especially pennation < π/2.
- **Q8 interpretation (`DECISIONS.md` §4):** Claude read Corbin's approval as covering D-026, D-027, D-031, D-034, D-035, plus the build/review roles. Corbin may correct it.
- **Deferred by Corbin until their phase (Q8):** D-028, D-029, D-030, D-032, D-033, D-038.
- **No open disagreements between models.**

## Next task

**Owner:** ChatGPT (reviewer). Roles per Q8.
**Task:** Review Phase A against its exit criterion (D-024, D-025):
1. Check out `4abb4f1` or later and confirm the snapshot.
2. Install the requirements.
3. Run `python -m pytest -q`, `python -m src.integrity` and `python tools/review_cycle1_probes.py`; compare with the table above.
4. Review the validator rules, data changes and D-050 choices; check D-049.
5. Return findings as Agree / Amend / Disagree with evidence. Reproduced results are reported as *independently checked*.

**Completion criterion:** every Phase A result is either reproduced by ChatGPT or disputed with evidence, and any findings are filed as `Proposed` entries for `DECISIONS.md`.
**Then:** Phase B (hip-only model), starting with the D-037 force-to-torque choice for Corbin's approval.
**Required inputs:** this repository (`lbao_repo.zip` with git history); `docs/DECISIONS.md` D-019, D-024 to D-027, D-031, D-034, D-035, D-049, D-050.

## Handoff protocol (D-048)

1. Start from the snapshot above and confirm it matches.
2. Read this file and the `DECISIONS.md` entries named in the next task.
3. Return: changes (as commits), validation evidence (commands and results), proposals (as new `Proposed` entries for `DECISIONS.md`), and unresolved questions.
4. Update this file at the end of every build or review.
