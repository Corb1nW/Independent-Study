# Second re-review of the Phase B build (PR #13): D1

**Reviewer:** Claude (Phase B reviewer, Q17)
**Date:** 2026-10-21
**Reviewed SHA:** `354984c20a09aa406f8b1020675e70318d728f93` (PR #13 head)
**Previous reviews:** at `bf92dfd` (AMEND, C1–C6) and `5285670` (AMEND, D1 only)
**Author of the work reviewed:** ChatGPT (Phase B builder)
**Disposition:** **AGREE. I recommend Corbin approve and merge PR #13 at `354984c`.**

## Scope and methods

- Read `git diff 5285670 354984c`: `verify_git_inputs` now compares `git hash-object` with `git rev-parse HEAD:<path>`; a new root `.gitattributes` (`* text=auto`); a new test, `test_d1_crlf_checkout_is_clean_and_raw_resolution_hash_still_checked`.
- **Executed** (Python 3.13.16, pytest 9.1.1, pydantic 2.14.1, pint 0.26.2, PyYAML 6.0.3):

| Check | Linux checkout (LF) | Windows-style checkout (`core.autocrlf=true`, every file CRLF) |
|---|---|---|
| `git status --porcelain` | clean | clean |
| `python -m pytest -q` | **104 passed** | **104 passed** (was 1 failed at `5285670`) |
| `python -m src.integrity` | PASSED | (run via tests) |
| `python tools/review_cycle1_probes.py` | 9/9 REJECTED | (not rerun) |
| `python -m tools.run_phase_b …` | `verified_git_head_and_inputs`; 0.840578902667 s / 0.767340043923 s; ratio 1/√1.2 | `verified_git_head_and_inputs`; identical times (was refused at `5285670`) |
| Uncommitted edit of `moment_arm_m` | rejected (`differs from HEAD`) | n/a |
| External `--config` | rejected (`outside repository`) | n/a |

- **Mutation:** putting back the old raw-byte comparison makes 2 tests fail, so the new behaviour is pinned by tests.
- **`.gitattributes` side effects:** no blob in the repository at `354984c` contains a carriage return, so `* text=auto` causes no spurious “modified” files. A fresh checkout is clean on both platforms, and binary files (the PDFs) are auto-detected.

## D1

**Resolved.** The comparison now uses git's own content identity, which applies line-ending normalization. The raw SHA-256 check against resolution-time hashes is kept, and the new test confirms it is not normalized away. A genuine value change in a CRLF file is still rejected.

## Non-blocking note for later

- **N4.** The manifest's `configuration_sha256`, `scenario_sha256` and `dataset_sha256` are hashes of the raw working-tree bytes, so they differ between a Windows and a Linux run of the same commit (CRLF vs LF), while the simulation results are identical. That is correct as a record of the exact bytes consumed, but someone comparing manifests across machines could be confused. In Phase C, consider recording git blob IDs alongside them (platform-independent), or note the platform in the manifest. No change is needed now.

## Overall Phase B assessment (all three reviews)

- **D-053 implemented as accepted:** `τ = −r0·a·F_right`, flexion-positive `q` bound to the ontology IDs, the domain `[−π/6, π/3]` with event-terminated exits, and N2 boundary-start logic.
- **Evidence path:** the Arnold `Fmax` is resolved and validated with dataset context; the canonical data are never modified; the right-only perturbation is a labelled overlay.
- **Provenance:** the manifest verifies the commit and every consumed file, refuses dirty or external inputs, and works on Windows and Linux.
- **Mechanics:** outputs match the closed form exactly, and the perturbation is explained to 15 digits (`t ∝ 1/√F`).
- **Honesty:** every number is labelled a demonstration assumption, including the tuned activation. Omitted physics is declared in every manifest, and no physiological or clinical validity is claimed.

This meets the D-040 Amendment 1 exit criterion *as software*: an input-resolution record, declared dynamics assumptions, a baseline and a perturbation, numerical checks, and the exact commit. The official baseline and perturbation record should be produced by running `python -m tools.run_phase_b --commit-sha <merge SHA> --output …` **at the merged commit** and committing that manifest.

**AGREE.**
