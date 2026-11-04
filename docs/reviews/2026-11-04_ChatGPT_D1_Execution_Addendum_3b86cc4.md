# Stage D1 execution addendum — PR #23 at 3b86cc4

Reviewed by (model): ChatGPT\
Built by (model): Claude (Stage D1 and archive packaging); inherited components include earlier ChatGPT work\
Reviewed SHA (full): `3b86cc4683e6ac921e605302be5a863be0cafe9b`\
Base SHA (PR #23): `ce0acce23c9ae94efcd2b877b4fd78fdde303e28`\
PR under check: [#23](https://github.com/Corb1nW/Independent-Study/pull/23) (`phase-d/claude-d1-squat`)\
Execution date: 2026-11-04; principal commands 08:20–08:21 EST (13:20–13:21 UTC)\
Record branch: `reviews/chatgpt-d1-execution-3b86cc4`\
Record branch base: `406a0899555cec7390b393c0a0dfd3b024b90f7f` (`main`; separate from PR #23's branch)

**Verdict: AGREE for the requested execution check.** All required project commands exited 0. All 178 tests passed. Exact recursive comparisons found no numerical differences. The complete list of metadata differences is below. This is a recommendation; Corbin decides.

**Status: REVIEWED, NOT APPROVED**

## Scope and independence

Corbin explicitly assigned the Independent Study Reviewer role and requested an execution check only. I followed the supplied Reviewer instructions, checked that they match the repository's `docs/skills/independent-study-reviewer/SKILL.md` byte for byte, and read the builder's `README_FOR_CHATGPT.md`, PR handoff/comments, D-051 (including its incorporated item 10), and D-058 with Amendments 1–3 and the D1-R07/D1-R08 follow-up.

Scope: package/snapshot integrity; every execution command in the supplied README; D1 mechanics/contact/source statuses and provenance; exact output comparison against the three specified committed result files; Phase B regression; and sensitivity output. This is not a new source review or a new decision about the D1 proposals.

**Independence:** Claude authored the Stage D1 implementation and packaged the inputs. I ran it here and wrote my own comparison program, with no project comparison helpers or project imports. Claude's packaging/check claims were not taken as execution evidence. The broader repository includes earlier ChatGPT-authored code, especially Phase B, and D1 responds to earlier ChatGPT review suggestions. Inherited ChatGPT implementation, copied suggestions/wording, and the Phase B regression are **self-checked**, not independently verified. My comparator and this addendum are also self-authored and self-checked. The independent-execution claim is limited to reproducing Claude-authored D1 behavior and outputs; it is not blanket independence for the entire 178-test suite.

## Snapshot and package integrity

- Input archive: `LB-AO_D1_verification_3b86cc4.zip`; observed SHA-256 `36ba60a04ab7132997b50c5c70526ee8faf06cdcdbf342b58471aa07e8690587`.
- `sha256sum -c SHA256SUMS.txt`: **21/21 OK**, exit 0 (bundle, source ZIP, README, all 18 wheels).
- Bundle SHA-256: `6b596eadf554072ec859dc47762dc8d60a14d39e6a8a00166b81a75178ec2c58`; source ZIP SHA-256: `efa8b56705e32a3a6a64c07aeba67c042ae64b3b288c0a0a58810d34b67a2cfc`.
- `git clone -q LB-AO_3b86cc4.bundle repo` and `git checkout -q 3b86cc4683e6ac921e605302be5a863be0cafe9b`: exit 0.
- `git rev-parse HEAD` before and after all runs: exactly `3b86cc4683e6ac921e605302be5a863be0cafe9b`.
- `git status --porcelain` before and after all runs: empty, exit 0. No source/result file in the checked-out commit was modified.
- Additional `git fsck --full` and `git bundle verify ../LB-AO_3b86cc4.bundle`: exit 0; complete history verified.
- GitHub's PR #23 metadata independently returned the same full head SHA and base SHA. GitHub's blob ID for `src/squat_d1.py`, `98183fcb41f048228bd05544fac7a34a3fdc8827`, exactly matched `git rev-parse HEAD:src/squat_d1.py`.
- Packaged wheel checksums were checked against the supplied checksum manifest. Claude's claim of matching them against PyPI is **reported**, not independently repeated here.

## Ran, with environment and results

Environment: Linux x86_64, glibc 2.39, kernel 6.18.57; CPython 3.12.14 (Clang 22.1.3). A new virtual environment was created with `python -m venv --system-site-packages /workspace/scratch/5513ec304951/verification/d1-env`. It used the runtime's already-installed compatible compiled packages and installed the missing pure-Python dependencies from the supplied wheels.

| Package | Executed version |
|---|---|
| Python | 3.12.14 |
| NumPy | 2.3.5 |
| pydantic | 2.14.1 |
| pydantic_core | 2.50.1 |
| pytest | 9.2.0 |
| PyYAML | 6.0.3 |
| SymPy | 1.14.0 |
| Pint | 0.26.2 |

`pip install --no-index --find-links ../wheels -r requirements.txt` succeeded, exit 0; all six declared requirements were satisfied without a network package install. `python --version` and `pip list` were run and their output captured. Additional installed dependency versions: flexcache 0.3, flexparser 0.4, iniconfig 2.3.1, mpmath 1.3.0, packaging 26.3, platformdirs 4.14.4, pluggy 1.7.0, Pygments 2.21.0.

For every project command, the virtual environment's `bin` was first on PATH, and `GIT_CONFIG_GLOBAL=/dev/null` and `GIT_CONFIG_NOSYSTEM=1` were set. All commands ran in the clean checkout at the reviewed SHA; output was directed outside the checkout.

```text
SHA=3b86cc4683e6ac921e605302be5a863be0cafe9b
OUT=/workspace/scratch/5513ec304951/verification/out
```

| Command | Exit | Observed result |
|---|---:|---|
| `python -m pytest -q` | 0 | 178 passed in 43.71 s. |
| `python -m src.integrity` | 0 | INTEGRITY CHECK PASSED: all checked cross-file references resolve and all observations validate. |
| `python tools/review_cycle1_probes.py` | 0 | 9/9 negative probes REJECTED; no probe was accepted. |
| `python -m tools.build_segment_datasets --check` | 0 | No stdout; exit 0, datasets current. |
| `python -m tools.run_phase_d1 --commit-sha 3b86cc4683e6ac921e605302be5a863be0cafe9b --output $OUT/d1_runs_3b86cc4.json` | 0 | female, male, gait2392: mechanics PASSED; contact FEASIBLE; sources provisional. Verified provenance, 17 inputs. |
| `python -m tools.run_phase_b --commit-sha 3b86cc4683e6ac921e605302be5a863be0cafe9b --output $OUT/phase_b_runs_3b86cc4.json` | 0 | Both manifests produced with verified_git_head_and_inputs (13 inputs each). |
| `python -m tools.sensitivity_d1 --commit-sha 3b86cc4683e6ac921e605302be5a863be0cafe9b --output $OUT/d1_sensitivity_3b86cc4.json --markdown $OUT/d1_sensitivity_3b86cc4.md` | 0 | JSON and Markdown produced; verified_git_head_and_inputs, 18 inputs; all reported cases feasible. |

D1's top-level and all three per-body statuses were exactly `mechanics_verification: passed`, `contact_feasibility: feasible`, `source_validation: provisional`. All eight recorded per-body checks were true. The D1 manifest's provenance was `verified_git_head_and_inputs`; my separate program rehashed all 17 inputs with SHA-256 and checked their Git blob IDs against the reviewed commit. It did the same for all 18 sensitivity inputs.

The reproduced short-horizon errors at 1 ms were 5.342567113357269e-11 rad (female), 6.574630847780611e-11 rad (male), and 6.181651800954858e-11 rad (gait2392), identical to the committed D1 results. Phase B domain-exit times were exactly 0.8405789026673781 s (baseline) and 0.7673400439231044 s (increased_right_force).

## Own-code comparison

I loaded each reference with `git show 3b86cc4683e6ac921e605302be5a863be0cafe9b:<path>`, rather than relying on a movable branch or a working copy of the reference. The standalone comparator below recursively checked types, dictionary key sets, list lengths/order, and scalar values. Numeric agreement here is **exact parsed-value equality**, not tolerance-based agreement. The program contains a diagnostic tolerance calculation for any numeric differences; there were none.

| Generated output | Reference at reviewed SHA |
|---|---|
| `d1_runs_3b86cc4.json` | `results/phase_d/2026-10-28_d1_squat_runs_9988620.json` |
| `d1_sensitivity_3b86cc4.json` | `results/phase_d/2026-10-28_d1_sensitivity_0146e42.json` |
| `phase_b_runs_3b86cc4.json`: both entries' `simulation` and `effective_values` | `results/phase_b/2026-10-27_phase_b_runs_6c8b6ef.json` |

| Compared scope | Scalar leaves | Numeric leaves | All differing leaves | Numeric differences |
|---|---:|---:|---:|---:|
| D1 full manifest | 20,570 | 20,022 | 3 | 0 |
| Sensitivity full JSON | 444 | 280 | 1 | 0 |
| Phase B: both scenario IDs, simulation and effective_values | 38 | 30 | 0 | 0 |

These are **all** differences in the compared scopes; no fields were excluded from the D1 or sensitivity comparisons:

| Output | JSON path | Committed value | Fresh value |
|---|---|---|---|
| D1 | `$.commit_sha` | `9988620c3351608ab78dd951d5378e2b261e0da9` | `3b86cc4683e6ac921e605302be5a863be0cafe9b` |
| D1 | `$.inputs.model.git_blob_id` | `c0ccaf5b678e53a3f0e2c26ab1c6f2e89340d87b` | `98183fcb41f048228bd05544fac7a34a3fdc8827` |
| D1 | `$.inputs.model.sha256` | `fa4d22d16ae2f4f873bb2da09594d8919de33e85764e94b4e4b3a9d962fe2e5a` | `8908f80be259a4afbb5bb4a9c4254bb3e083df9eba803f79e3eafbb054d19de3` |
| Sensitivity | `$.commit_sha` | `0146e425769e0c0d5d9782ef2e3a0cfcf11e7e5a` | `3b86cc4683e6ac921e605302be5a863be0cafe9b` |

Thus the D1 model's changed hash is represented by **both** `inputs.model.git_blob_id` and `inputs.model.sha256`; all other D1 fields, including statuses, inputs and every series/check value, matched exactly. Git history confirms `src/squat_d1.py` changed in `0146e425769e0c0d5d9782ef2e3a0cfcf11e7e5a`; its blob there is the fresh blob shown above. This is consistent with the builder's stated D1-R07 change and unchanged baseline outputs.

Sensitivity JSON matched completely apart from `commit_sha`. I additionally compared `d1_sensitivity_3b86cc4.md` with committed `results/phase_d/2026-10-28_d1_sensitivity_0146e42.md`: exact text equality after replacing only the old full commit SHA with the reviewed SHA.

Phase B's two requested sections matched exactly for each scenario, with scenario identity and count also checked. No claim of full Phase B manifest equality is made; its other metadata was outside that comparison contract.

Observed output fingerprints:

| Output | SHA-256 of fresh file bytes |
|---|---|
| `d1_runs_3b86cc4.json` | `09ba6090d67807b7e744125d8c210cc35863b6f65a9cdc89c6f7868b3941bc34` |
| `d1_sensitivity_3b86cc4.json` | `9c0d44cd7bfc2735cd8d642adcb3a7a0af56e733c331ccf0f395537ebf56560a` |
| `phase_b_runs_3b86cc4.json` | `5ee23bd411e656e47a9b221e61592c76b5924a871960588618145bc158bd9163` |

## Deviations and limits

1. Paths were adapted to the uploaded archive's workspace location. I first inspected and extracted the archive with Python's ZIP reader, then also ran `unzip -q` into a separate scratch directory. The Git bundle, not the source-only ZIP, supplied the execution checkout.
2. Only CPython 3.12 was installed. The supplied NumPy, pydantic_core and PyYAML compiled wheels target CPython 3.13; those wheel binaries were not used. The system-site-packages virtual environment used compatible preinstalled NumPy 2.3.5, pydantic 2.14.1/core 2.50.1 and PyYAML 6.0.3. Missing dependencies came from the supplied pure-Python wheels. This differs from both Claude's author-reported Python 3.13.18 environment and the packaged wheel versions. Every required command still completed, and all compared numerical outputs were exactly equal.
3. Return codes and stdout/stderr were captured directly by a subprocess runner instead of appending `echo "exit $?"`. Git isolation settings were passed through the subprocess environment; `pip list` output was filtered by my runner. No project command was omitted.
4. No Windows run, Python 3.13 rerun, browser/page render, new anatomy/source-paper assessment, new implementation, or new source review was performed; these are outside this execution request. Existing scientific/source limitations are not resolved by passing software checks.

## Findings and disposition

**Findings (ID / severity / location / evidence / problem / fix):** None requiring amendment within this execution scope. The three D1 metadata changes and one sensitivity metadata change are exhaustively listed above; no unanticipated output difference or failed command was found.

**Earlier findings:** This is an execution addendum to the prior source-level review, not a new disposition of D1-R01 through D1-R08. The committed regression suite now has an observed 178/178 pass result at the exact target; independence qualifications are stated above.

**Read or reasoned only:** the role instructions, accepted decisions, builder's handoff/claims, PR metadata, and the explanation for the changed model hash. No scientific source claim was re-reviewed.

**Not run, and why:** no README project command was left unrun. Cross-checking wheel hashes against PyPI and the additional platform/source/page checks above were outside scope.

**Sources checked (and new sources):** supplied checksum manifest, Git objects/history and GitHub commit/blob metadata, and the three specified committed result files. No new anatomical or biomechanical source is cited; no addition to `sources/SOURCES.md` is proposed.

**Out-of-scope observations:** the D1 output still labels sources provisional and says it is not validated against measured squats. Execution verifies software behavior for the stated model, never anatomical, biomechanical or clinical validity (D-051 item 10). This addendum does not approve D1's pending proposals.

**Verdict: AGREE** (execution recommendation; Corbin decides).\
**Must fix before Corbin decides:** none identified by this execution check.\
**Status: REVIEWED, NOT APPROVED**

## Appendix: comparison program actually executed

This is the self-authored standalone comparator that produced the counts and differences above. Its absolute scratch paths identify this run; adapt `ROOT` to reproduce it elsewhere. It uses only the Python standard library and Git.

```python
"""ChatGPT's standalone comparator; no project imports or comparison helpers."""
import collections
import hashlib
import json
import math
from pathlib import Path
import subprocess

ROOT = Path('/workspace/scratch/5513ec304951/verification')
REPO = ROOT / 'LB-AO_D1_verification_3b86cc4/repo'
OUT = ROOT / 'out'
SHA = '3b86cc4683e6ac921e605302be5a863be0cafe9b'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=REPO)

def read_reference(path):
    data = git('show', SHA + ':' + path)
    return json.loads(data), hashlib.sha256(data).hexdigest()

def differences(expected, actual, path='$', counts=None):
    if counts is None:
        counts = collections.Counter()
    if type(expected) is not type(actual):
        yield dict(path=path, kind='type', expected=expected, actual=actual)
    elif isinstance(expected, dict):
        for key in sorted(set(expected) | set(actual)):
            if key not in expected or key not in actual:
                yield dict(path=path + '.' + key, kind='key', expected=expected.get(key), actual=actual.get(key))
            else:
                yield from differences(expected[key], actual[key], path + '.' + key, counts)
    elif isinstance(expected, list):
        if len(expected) != len(actual):
            yield dict(path=path, kind='length', expected=len(expected), actual=len(actual))
        for i, (left, right) in enumerate(zip(expected, actual)):
            yield from differences(left, right, f'{path}[{i}]', counts)
    else:
        counts['leaves_compared'] += 1
        if isinstance(expected, (int, float)) and not isinstance(expected, bool):
            counts['numeric_leaves_compared'] += 1
        if expected != actual:
            row = dict(path=path, kind='scalar', expected=expected, actual=actual)
            if isinstance(expected, (int, float)) and not isinstance(expected, bool):
                row.update(abs_delta=abs(actual - expected),
                           rel_delta=abs(actual - expected) / max(abs(actual), abs(expected)) if actual or expected else 0,
                           close_1e_12=math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12))
            yield row

report = {}
files = [('d1', 'd1_runs_3b86cc4.json', 'results/phase_d/2026-10-28_d1_squat_runs_9988620.json'),
         ('sensitivity', 'd1_sensitivity_3b86cc4.json', 'results/phase_d/2026-10-28_d1_sensitivity_0146e42.json'),
         ('phase_b', 'phase_b_runs_3b86cc4.json', 'results/phase_b/2026-10-27_phase_b_runs_6c8b6ef.json')]
for name, output, reference in files:
    actual_bytes = (OUT / output).read_bytes()
    actual = json.loads(actual_bytes)
    expected, reference_hash = read_reference(reference)
    stats = collections.Counter()
    if name == 'phase_b':
        # Check both scenario identities and both requested sections in every entry.
        assert len(actual) == len(expected) == 2
        expected = [dict(scenario_id=x['scenario']['scenario_id'], simulation=x['simulation'], effective_values=x['effective_values']) for x in expected]
        actual = [dict(scenario_id=x['scenario']['scenario_id'], simulation=x['simulation'], effective_values=x['effective_values']) for x in actual]
    diffs = list(differences(expected, actual, counts=stats))
    numeric = [d for d in diffs if 'abs_delta' in d]
    report[name] = dict(reference=reference, reference_sha256=reference_hash,
                        output=output, output_sha256=hashlib.sha256(actual_bytes).hexdigest(),
                        statistics=dict(stats), differences_count=len(diffs), differences=diffs,
                        numeric_differences_count=len(numeric),
                        non_numeric_differences_count=len(diffs)-len(numeric),
                        numeric_outside_1e_12=sum(not d['close_1e_12'] for d in numeric),
                        max_absolute_difference=max((d['abs_delta'] for d in numeric), default=0),
                        max_relative_difference=max((d['rel_delta'] for d in numeric), default=0))

provenance = {}
for name, output, _ in files[:2]:
    manifest = json.loads((OUT / output).read_bytes())
    assert manifest['commit_sha'] == SHA
    assert manifest['commit_provenance_status'] == 'verified_git_head_and_inputs'
    checked = []
    for label, inp in manifest['inputs'].items():
        path = inp['path']
        raw_sha = hashlib.sha256((REPO / path).read_bytes()).hexdigest()
        blob_sha = git('rev-parse', SHA + ':' + path).decode().strip()
        assert raw_sha == inp['sha256'], (name, label, 'raw sha256')
        assert blob_sha == inp['git_blob_id'], (name, label, 'git blob')
        checked.append(path)
    provenance[name] = dict(commit_sha=SHA, status=manifest['commit_provenance_status'], independently_rehashed_inputs=len(checked))
report['provenance'] = provenance
assert git('rev-parse', 'HEAD').decode().strip() == SHA
assert git('status', '--porcelain') == b''
(OUT / 'comparison_report.json').write_text(json.dumps(report, indent=2, sort_keys=True))
for name, row in report.items():
    if name == 'provenance':
        print(name, json.dumps(row, sort_keys=True))
        continue
    print(name, json.dumps({k: v for k, v in row.items() if k != 'differences'}, sort_keys=True))
    for d in row['differences'][:16]:
        print(' ', json.dumps(d, sort_keys=True))
print('Full comparison saved to comparison_report.json')
```
