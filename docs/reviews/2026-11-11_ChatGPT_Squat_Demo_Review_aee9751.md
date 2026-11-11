# Squat demo presentation review

- **Reviewed by (model):** ChatGPT
- **Built by (model):** Claude
- **PR:** [#44](https://github.com/Corb1nW/Independent-Study/pull/44)
- **Reviewed SHA:** `aee97518193d9ad999533837353e8935573ec4db`
- **Base SHA:** `cef38be756c460d19d31ac26502b1bc6c9a71d80`
- **Date:** 2026-11-11
- **Verdict:** **AMEND** for playback finding DEMO-B01. P1 is a next-phase follow-up.
- **Status:** **REVIEWED, NOT APPROVED**

## Scope and independence

Reviewed the five-file presentation change against the approved D1–D3 work and the request for an easy-to-open squat demonstration. The page uses the official D1 `dd89fff`, D2 `7ac0f2d`, and D3 `d3efc56` manifests. The displayed motion is prescribed and the simulation computes torques and muscle recruitment along that motion. The public handoff records the request at 13:14 ET. I read the handoff and checked Claude's new demo and generator independently. The underlying model and earlier review records are existing inputs. I wrote the two test fixtures used for this review.

## Checks run

Linux x86-64, Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, pytest 9.2.0, Node.js 24.22.1. Exact Git HEAD and clean status were verified. The sparse checkout excluded the unrelated binary phase-overview PDF.

| Check | Result |
|---|---|
| `python -m pytest -q` | 285 passed |
| `python -m src.integrity` | Passed |
| `python tools/review_cycle1_probes.py` | 9/9 rejected |
| `python -m tools.build_segment_datasets --check` | Passed |
| `python -m tools.build_squat_demo --output /tmp/SQUAT_DEMO.html` | Byte-identical to the committed page, SHA-256 `0215420729a16158e7bf1b9b3fbb524a789ed830cfa11f51bf252253180f9d77` |
| Embedded data compared directly with the official manifests | All 301 samples per body match at the stated display precision, including angles, per-leg torques, muscle paths in actuator order, activations, forces, and fixed/moving reserves. All 20 simplifications and 12 registered source rows are present. |
| JavaScript interaction fixture | Body switch, 1.50 s scrub, reserve readout and all four gap callouts pass. Playback result below. |

I exercised the generated JavaScript with a DOM fixture. The browser rejected the local file URL, so desktop and phone layout observations are builder-reported.

## DEMO-B01 — High — Playback stalls at high refresh rates

In `tools/squat_demo_template.html:478` and the generated page, `tick` assigns `last = ts` before checking whether enough time has elapsed for a 10 ms simulation step. When callbacks arrive less than 10 ms apart, `adv` is zero and the next callback starts measuring from the latest timestamp. That drops the fractional elapsed time on every callback. The play control reports playing while the figure stays at the initial frame.

I ran the actual embedded script and supplied `requestAnimationFrame` timestamps spaced by `1000 / rate` ms for one second.

| Callback rate | Committed playback time | With the proposed fix |
|---|---:|---:|
| 60 Hz | 1.00 s | 1.00 s |
| 120 Hz | 0.00 s | 1.00 s |
| 144 Hz | 0.00 s | 1.00 s |

**Fix I would accept.** Remove the unconditional `last = ts;` immediately after the `dt` calculation. Keep initial timestamp setup, the timestamp update inside `adv > 0`, and the paused reset. This retains substep time until a sample can advance. Regenerate `SQUAT_DEMO.html` from the amended template and verify playback at both 60 Hz and a callback cadence below 10 ms per frame.

## P1 — Ontology follow-up for the next phase

Corbin asked to keep the gap visible in this demo and address it in the next phase. Retain the Limits panel and individual muscle-card notes in PR #44. The two missing relationships are `CROSSES` and `ACTS_ON` to the same-side knee for the **left and right** entries below. Their `mechanical_capabilities` already list the indicated knee action. The right-side moving-knee moment arms come from all 301 matched poses in the committed D3 OpenSim reference.

| Muscle | Existing knee action | Peak absolute knee moment arm |
|---|---|---:|
| Biceps femoris, long head | Flexion | 34.9 mm |
| Semimembranosus | Flexion | 40.5 mm |
| Semitendinosus | Flexion | 48.5 mm |
| Rectus femoris | Extension | 50.4 mm |

The anatomical entries are in `ontology/hip.yaml`. Both knee entities are defined in `ontology/lower_limb_sagittal.yaml`. The demo's paths come from the official Gait2392-based run. The presentation and its numerical results can be reviewed while the anatomical records await repair.

Carry P1 into the next ontology–model consistency stage, currently proposed as **D4** in [PR #43](https://github.com/Corb1nW/Independent-Study/pull/43). Scope the bilateral joint-relationship repair and module dependency together. Hip-only loading is exercised in `tests/test_phase_d1.py` and `tests/test_phase_d2.py`. Include a regression that catches a missing same-side crossing and checks that the affected action relationships resolve. Use the existing anatomical evidence for the relationships and the OpenSim moment arms for the model-side consistency check.

## Handoff

The playback fix is required before the demo decision. P1 is recorded for the next phase. No new source is introduced by this review. Corbin decides whether to merge the amended demo and the next-stage plan.
