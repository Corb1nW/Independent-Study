"""Reviewer rerun of the rejected configurations from PR #36."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import yaml

ROOT = Path(__file__).parent
REPO, OUT = ROOT/'repo', ROOT/'out'
sys.path.insert(0, str(REPO))
from tools import run_phase_d2 as runner

base = yaml.safe_load(runner.CONFIG.read_text())
results = {}
for key, val in [('unit_mN_m', 'mN*m'), ('unit_1000_mN_m', 'mN*m'),
                 ('width', 2.), ('passive', 'included'), ('activation', 'first_order'),
                 ('damping_bool', False), ('missing', 'passive_fiber_force'),
                 ('extra', 'unsupported'), ('combined', None)]:
    cfg = copy.deepcopy(base)
    if key.startswith('unit'):
        cfg['parameters']['epsilon_reserve']['unit'] = val
        if key.startswith('unit_1000'):
            cfg['parameters']['epsilon_reserve']['value'] = 1000.
    elif key == 'missing':
        cfg['baseline_force_law'].pop(val)
    elif key == 'extra':
        cfg['baseline_force_law'][val] = 'present'
    elif key == 'combined':
        cfg['parameters']['epsilon_reserve'].update(value=1., unit='mN*m')
        cfg['baseline_force_law'].update(active_force_width_scale=2., passive_fiber_force='included')
    else:
        field = {'width':'active_force_width_scale', 'passive':'passive_fiber_force',
                 'activation':'activation_dynamics', 'damping_bool':'fiber_damping'}[key]
        cfg['baseline_force_law'][field] = val
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)/'bad.yaml'
        path.write_text(yaml.safe_dump(cfg))
        try:
            runner.load_config(path)
        except ValueError as exc:
            results[key] = {'rejected': True, 'reason': str(exc)}
        else:
            raise AssertionError('Bad configuration accepted: '+key)
        if key == 'combined':
            output = Path(tmp)/'must_not_be_written.json'
            args = [sys.executable, '-m', 'tools.run_phase_d2', '--commit-sha',
                    '9ed7b1f1454bb1e3f4d16cd8cb8ec511b76c9926', '--config', str(path),
                    '--d1-manifest', 'results/phase_d/2026-11-04_d1_squat_runs_dd89fff.json',
                    '--output', str(output)]
            env = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_NOSYSTEM='1')
            proc = subprocess.run(args, cwd=REPO, env=env, capture_output=True, text=True)
            assert proc.returncode != 0 and not output.exists()
            assert 'epsilon_reserve: unit must be' in proc.stderr
            results['combined_cli'] = {'exit': proc.returncode, 'manifest_created': output.exists(),
                                       'failure': proc.stderr.splitlines()[-1]}

assert runner.load_config()[1]['epsilon_reserve'] == 1.
(OUT/'guard_probes.json').write_text(json.dumps(results, indent=2)+'\n')
print(json.dumps(results, indent=2))
