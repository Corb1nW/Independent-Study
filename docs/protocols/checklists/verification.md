# Conditional verification checklist — v0.2 candidate

Select applicable checks and report omissions; do not claim universal applicability.

- **Always for substantive changes:** confirm pinned SHA, tracked/dirty state, relevant tests, integrity checks, warnings, and explicit checks not run. Report repository integrity, software verification, and scientific support separately.
- **Scientific/model/data changes:** verify evidence chain, units, transformations, sign conventions, applicability ranges, symmetry assumptions, whole-muscle vs compartment meaning, and labels for demo values. Do not call passing tests scientific validation.
- **Simulation inputs / scenarios:** ensure scenario overlays do not mutate shared baseline/source Fmax or other source quantities; verify effective input provenance and rejected invalid sources; check domain-boundary event behavior and invalid/nonfinite values where relevant.
- **Reproducible committed-input runs:** reject uncommitted, untracked, out-of-repository or modified effective inputs as specified by the run contract; preserve resolution-time raw-byte hashes where applicable.
- **Windows / cross-platform checkouts:** compare `git hash-object -- <path>` against `git rev-parse HEAD:<path>` for Git-normalized tracked content rather than comparing checkout raw bytes with `git show HEAD:path`. Retain separate raw-byte checks for resolution-to-execution consistency. Add CRLF regression coverage when touching this path. Respect repository `.gitattributes`.
- **Environment limits:** record actual dependency versions and whether offline wheels/bundles were used; never infer success from another model's runs.
