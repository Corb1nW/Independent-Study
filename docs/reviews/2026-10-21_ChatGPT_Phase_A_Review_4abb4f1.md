# ChatGPT Phase A review — D-051 P4

**Date:** 2026-10-21  
**Reviewer:** ChatGPT (GPT-6)  
**Reviewed SHA:** `4abb4f1995956d926959ac5ef0f0f68656619ee6`  
**Base SHA:** `d04fb78e86f851db26738bbc94a068201eb41b02`  
**Conclusion:** **AMEND** (static review only; executable tests not independently reproduced)

## Scope, method and environment

Read the exact historical Phase A commit and files through the connected GitHub API, not through `main`. Inspected `src/quantitative.py`, `src/datum_model.py`, `src/integrity.py`, `src/ontology.py`, `tests/test_phase_a.py`, ontology snippets, `PROJECT_STATE.md`, commit metadata and import PR #1. The later merge and `pytest.ini` are excluded from the implementation under review.

The local sandbox's `git ls-remote https://github.com/Corb1nW/Independent-Study.git HEAD` failed with `Could not resolve host: github.com`. No exact-SHA working checkout was obtainable in the sandbox. Thus `pip install -r requirements.txt`, `python -m pytest -q`, `python -m src.integrity`, and `python tools/review_cycle1_probes.py` **were not executed by ChatGPT**. Claude's 65 tests passing and the integrity/probe results remain **reported, not reproduced**. The primary anatomical sources were not independently verified during this review.

## Findings

### A1 — MEDIUM — Cross-dataset source registry leakage

`QuantitativeSchema.load_dataset()` mutates a shared `self.known_sources` set with every dataset's sources; `_evidence_errors()` checks citations against that accumulated set. A citation in dataset B to a source declared only in dataset A may pass or fail depending on which dataset loaded first. Fix by using an explicit project-wide catalog or verifying each dataset's sources in its own context. Add two-dataset negative tests (both load orders). **Statically inferred; not reproduced.**

### A2 — MEDIUM — Incomplete reference coverage

`src/integrity.py` checks selected ontology, dataset alias, model and target references, but not `quality.value_comparisons[].related_observation`, `quality.conflicts_with[]`, or derivation input references. In `src/quantitative.py`, `coordinate_context.frame_id` and `.coordinate_id` are checked against ontology entities, but `.convention_source_id` is not checked against source IDs. The public claim that **all** cross-file references resolve is too broad. Enumerate the supported references, implement focused checks with negative tests, and document deferred classes. **Statically inferred; not reproduced.**

### A3 — MEDIUM — Simulation readiness overclaim

`validation_report()` returns `ready_for_simulation = YES` for any populated datum with no validation errors. It does not check model-specific geometry, force-to-torque assumptions, parameter completeness, or dynamics. Rename the result to something like `datum_input_valid` or clearly limit its meaning to candidate input eligibility. Full simulation readiness should be evaluated in later model-specific checks. **Statically inferred; not reproduced.**

### A4 — LOW — Source registry membership is not scientific evidence validation

The evidence layer confirms that source IDs exist and supported-claim strings are present; it cannot prove that Ward 2009 or a clinical anatomy reference supports the claim. Preserve this as an explicit Phase A boundary. **Statically inferred.**

### A5 — LOW — Keep execution provenance exact

The current `PROJECT_STATE.md` correctly marks author-run checks as not independently reproduced. The historical `PROJECT_STATE.md` at the reviewed SHA predates Phase A. Do not silently include `pytest.ini` from the later import merge when claiming to test Phase A at `4abb4f1`; if test discovery needs `python -m pytest -q tests`, record that deviation. **Verified from source metadata.**

## Positive findings

- Pydantic strict models and forbidden extra fields significantly improve structural validation.
- Conditional treatment of unpopulated data avoids inappropriate requirements for intentionally absent values.
- Pint units, conversion traces, property aliases, and explicit default precedence address important baseline failure modes.
- Side-specific coordinate records and tests support laterality without falsely interpreting shared baseline values as side-specific measurements.
- Separate immutable Phase A and import commits preserve a meaningful review boundary.

## Verification table

| Test or capability | Status |
|---|---|
| Retrieve exact commit and file tree through GitHub | **PASS** |
| Read files at arbitrary SHA | **PASS** |
| Local checkout of the exact SHA | **NOT AVAILABLE** (network/DNS) |
| Install `requirements.txt` | **NOT RUN** |
| `python -m pytest -q` | **NOT RUN** |
| `python -m src.integrity` | **NOT RUN** |
| `python tools/review_cycle1_probes.py` | **NOT RUN** |
| Ward 2009/anatomical claims independently checked | **NOT DONE** |

## Outstanding issues and decision

**AMEND, not reject.** A1 and A2 are the most important corrections before claiming comprehensive integrity. A3 and A4 need clear scope language. Request targeted negative tests and a clean pinned-SHA CI run. A passing author-run suite or a successful GitHub PR does not constitute independent execution by ChatGPT. This review is a source-level review; it does not approve Phase A software verification or biomedical validity.
