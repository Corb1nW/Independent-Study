# LB-AO Project State

**Updated:** 2026-10-07
**Updated by:** Claude
**Authoritative snapshot:** branch `main`, the commit that last changed this file (`git log -1 -- PROJECT_STATE.md`). Baseline of the original work: `d04fb78`.
**Component versions:** ontology `hip.yaml` 0.2.0 · schema LB-QPS 0.3.0 · dataset `gluteus_maximus.yaml` 0.2.0 · README label LB-AO v0.5 · `DECISIONS.md` revision 2
**Current phase:** Governance base complete; **Phase A (Integrity) not started**

## Implemented work

- Original work by ChatGPT (framework, hip ontology, quantitative schema, gluteus maximus dataset, loaders/validator, 18 tests, demos), committed unchanged as baseline `d04fb78` (D-046).
- Review documents in `docs/reviews/`; design documents in `docs/design/`.
- `tools/review_cycle1_probes.py`: reproduces Review Cycle 1 defects D1–D8 and the Appendix A validator probes, plus probe 1b for an incompatible unit (D-046).
- `docs/DECISIONS.md` revision 2: D-001 to D-048, approval record (D-042), three status fields (D-043).
- This file (D-048).

No code or data has been changed from the baseline.

## Validation

| Check | Snapshot | Run by | Command | Result |
|---|---|---|---|---|
| Existing test suite | `d04fb78` | Claude | `python -m pytest -q` | 18 passed |
| Review Cycle 1 probes | `d04fb78` | Claude | `python tools/review_cycle1_probes.py` | All defects reproduce: 2 unresolved coordinate references (D1); 1 parameter-name mismatch (D2); 11 classes with no properties (D3); 2 form mismatches (D5); all 9 validator probes ACCEPTED (D4) |

**Reported, not independently reproduced:** ChatGPT has not yet rerun the probes (open item, D-045).
**Environment:** Python 3 with PyYAML 6.0.3 and pytest (versions per `requirements.txt` minimums).

## Accepted but unimplemented

- **D-024** fix defects D1–D8 · **D-025** negative tests for every validator rule (Phase A)
- **D-036** minimal hip-only model · **D-037** force-to-torque representation recorded before running (Phase B)
- **D-039 / D-040** phase plan, including the Phase B boundary (Amendment 1)

## Open proposals and disagreements

- **Awaiting Corbin's decision:** D-026 to D-035 and D-038. Both models agree on each; Corbin has not approved them individually (D-042). Several are Phase A inputs: D-026 (unit validation), D-031 (class reconciliation), D-034 (anatomy corrections), D-035 (structural validation).
- **No open disagreements between models.**

## Next task

**Owner (proposed, awaiting Corbin):** Claude builds Phase A; ChatGPT reviews against the Phase A exit criterion.
**Prerequisite:** Corbin decides D-026 to D-035 and D-038 (they can be approved as a batch).
**Task:** Phase A (Integrity) per D-024, D-025 and D-039, within the delegated scope of D-047:
1. Fix D1–D8.
2. Add a failing-case test for each validator loophole (including probes 1b and 2 for units).
3. Add the cross-file reference check.
4. Enforce status and enum values; require a rationale for `assumed` data.
5. Use one defaults-merging function.
6. Give the hip joint its kinematic properties.
7. Make anatomy corrections after source verification.
8. Confirm the Ward 2009 fiber-length normalization.

**Completion criterion:** malformed records are rejected with clear messages; legitimate records and conversions pass; all cross-file references resolve; `tools/review_cycle1_probes.py` reports every validator probe as REJECTED except probe 1 (relabeling, see D-026); the existing behavior of the baseline data is preserved.
**Required inputs:** this repository at the snapshot above; Ward et al. 2009 (Table 3); an anatomy reference for D-034 corrections.

## Handoff protocol (D-048)

1. Start from the snapshot above and confirm it matches.
2. Read this file and the `DECISIONS.md` entries named in the next task.
3. Return: changes (as commits), validation evidence (commands and results), proposals (as new `Proposed` entries for `DECISIONS.md`), and unresolved questions.
4. Update this file at the end of every build or review.
