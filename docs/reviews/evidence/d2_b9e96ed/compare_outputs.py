"""Reviewer-owned full recursive comparison; no project comparator imports."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).parent
REPO, OUT = ROOT/'repo', ROOT/'out'


def compare(old, new):
    counts = defaultdict(int)
    numeric = defaultdict(lambda: {'count': 0, 'max_abs': 0., 'example': None})
    other = []
    def walk(a, b, path='$'):
        if isinstance(a, dict) and isinstance(b, dict):
            if a.keys() != b.keys():
                other.append({'path': path, 'old_keys': sorted(a), 'new_keys': sorted(b)})
            for k in sorted(a.keys() & b.keys()):
                walk(a[k], b[k], path+'.'+k)
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                other.append({'path': path, 'old_length': len(a), 'new_length': len(b)})
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, path+f'[{i}]')
        else:
            counts['scalar_leaves'] += 1
            if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
                counts['numeric_leaves'] += 1
                if a != b:
                    counts['numeric_differences'] += 1
                    key = re.sub(r'\[\d+\]', '[]', path)
                    row = numeric[key]
                    row['count'] += 1
                    delta = abs(a-b)
                    if delta > row['max_abs']:
                        row.update(max_abs=delta, example={'path': path, 'old': a, 'new': b})
            elif type(a) is not type(b) or a != b:
                other.append({'path': path, 'old': a, 'new': b})
    walk(old, new)
    return {'counts': dict(counts), 'numeric_differences_by_field': dict(numeric), 'other_differences': other}


report = {}
pairs = {
    'oracle': (REPO/'tests/data/d2_oracle_reference.json', OUT/'oracle_fresh.json'),
    'run': (REPO/'results/phase_d/2026-11-10_d2_muscle_runs_7ac0f2d.json', OUT/'d2_run_b9e96ed.json'),
    'sensitivity': (REPO/'results/phase_d/2026-11-10_d2_sensitivity_7ac0f2d.json', OUT/'sensitivity_b9e96ed.json'),
}
for label, (old, new) in pairs.items():
    if not new.exists():
        continue
    report[label] = compare(json.loads(old.read_text()), json.loads(new.read_text()))
    report[label]['sha256'] = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in [('old', old), ('new', new)]}

# Check input records using our own raw-byte hash and Git-filtered object lookup.
for label in ('run', 'sensitivity'):
    p = pairs[label][1]
    if not p.exists():
        continue
    manifest = json.loads(p.read_text())
    records = []
    for name, v in manifest['inputs'].items():
        actual = hashlib.sha256((REPO/v['path']).read_bytes()).hexdigest()
        git_blob = subprocess.check_output(['git', 'hash-object', '--', v['path']], cwd=REPO, text=True).strip()
        assert actual == v['sha256'], name
        assert git_blob == v['git_blob_id'], name
        records.append(name)
    report[label]['input_records_rehashed'] = records
    assert manifest['commit_sha'] == 'b9e96edb4a2e4a56e35679c8982152d5bc182315'

page = OUT/'viewer_committed_input.html'
if page.exists():
    original = REPO/'results/phase_d/2026-11-10_d2_muscle_viewer_7ac0f2d.html'
    report['page_byte_identical_from_committed_manifest'] = original.read_bytes() == page.read_bytes()

(OUT/'comparisons.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
for key, r in report.items():
    if isinstance(r, dict):
        print(key, json.dumps(r.get('counts')), 'other:', json.dumps(r.get('other_differences')))
        print('numeric difference fields', json.dumps(r.get('numeric_differences_by_field')))
    else:
        print(key, r)
