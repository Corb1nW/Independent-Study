# Squat demo playback re-review

- **Reviewed by (model):** ChatGPT
- **Built by (model):** Claude
- **PR:** [#44](https://github.com/Corb1nW/Independent-Study/pull/44)
- **Reviewed SHA:** `3e6104d824cd3854273933e989a73d85be981162`
- **Base SHA:** `cef38be756c460d19d31ac26502b1bc6c9a71d80`
- **Previous reviewed SHA:** `aee97518193d9ad999533837353e8935573ec4db`
- **Date:** 2026-11-11
- **Verdict:** **AGREE**. DEMO-B01 is resolved. No blocking findings.
- **Status:** **REVIEWED, NOT APPROVED**

## Scope and independence

The fix commit removes the per-callback timestamp reset from `tick` in the template and regenerated HTML. It is the complete delta from the previous review. I proposed the timer change and self-checked that design. I executed Claude's committed version in a separate checkout and compared it with the earlier page using a reviewer-written fixture.

## Checks run

Linux x86-64, Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, pytest 9.2.0 and Node.js 24.22.1. Both Git snapshots were checked by object ID. The reviewed worktree was clean and its sparse checkout excluded the unrelated phase-overview PDF.

The Node fixture ran each page's embedded JavaScript with one second of frame timestamps.

| Callback rate | Previous page | Amended page |
|---|---:|---:|
| 60 Hz | 1.00 s | 1.00 s |
| 120 Hz | 0.00 s | 1.00 s |
| 144 Hz | 0.00 s | 1.00 s |

Three successive 4 ms intervals advanced the amended page from 1.50 s to 1.51 s. The fixture also exercised pause, resume without catch-up, restart from the final frame, the body controls, and the four muscle-card gap callouts. Timing was checked with synthetic frame timestamps in the DOM fixture.

`python -m pytest -q` passed all 285 tests. `python -m src.integrity` passed. `python tools/review_cycle1_probes.py` rejected all nine probes. `python -m tools.build_segment_datasets --check` passed. Rebuilding with `python -m tools.build_squat_demo --output /tmp/SQUAT_DEMO.html` matched the committed HTML byte for byte, SHA-256 `5d561c4799e8ab0723e8280131f8426d8b52a8c3400fc45ad0f3ef88a11db52f`. The display data matched the official D1–D3 manifests at the stated display precision. The prior review records the browser's local-file restriction. No live layout was inspected for this timer-only change.

## Disposition

**DEMO-B01 is resolved.** The demo keeps the four ontology gap callouts. P1 records the missing bilateral `CROSSES` and `ACTS_ON` knee links for the next ontology–model consistency stage, currently proposed as D4 in [PR #43](https://github.com/Corb1nW/Independent-Study/pull/43). The source material checked was the template, generated demo, manifests and existing ontology records. Corbin makes the merge decision.
