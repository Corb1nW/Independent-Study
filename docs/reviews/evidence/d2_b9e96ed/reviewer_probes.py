"""Additional post-merge D2 review probes, authored by ChatGPT."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import xml.etree.ElementTree as ET

import numpy as np
import opensim as osim
from scipy.optimize import linprog
import yaml

ROOT = Path(__file__).parent
REPO, OUT = ROOT/'repo', ROOT/'out'
sys.path.insert(0, str(REPO))
from tools import run_phase_d2 as runner

record = json.loads((OUT/'d2_run_b9e96ed.json').read_text())
reference = json.loads((OUT/'oracle_fresh.json').read_text())
source = REPO/'sources/vendor/opensim-models/gait2392_millard2012muscle.osim'
data = yaml.safe_load((REPO/'ontology/quantitative_data/segments_gait2392.yaml').read_text())['observations']
knee = data['LB-QD:G2392:JOINT:KNEE_R']['value']
names = reference['actuators']
report = {}

# Write a matched copy independently from the source file and stated D1 rules.
def model_bytes(moving_knee=False):
    xml = ET.parse(source).getroot()
    joints = {j.get('name'): j for j in xml.iter('CustomJoint')}
    if not moving_knee:
        axes = {a.get('name'): a for a in joints['knee_r'].iter('TransformAxis')}
        for axis, value in zip(('translation1', 'translation2'), knee[:2]):
            obj = axes[axis]
            for child in list(obj):
                if child.tag not in ('coordinates', 'axis'):
                    obj.remove(child)
            obj.find('coordinates').text = ''
            ET.SubElement(ET.SubElement(obj, 'Constant'), 'value').text = repr(float(value))
    for a in joints['ankle_r'].iter('TransformAxis'):
        if a.get('name') == 'rotation1': a.find('axis').text = '0 0 1'
        if a.get('name') == 'rotation3': a.find('axis').text = '1 0 0'
    for c in xml.iter('Coordinate'):
        if c.get('name') in ('subtalar_angle_r', 'mtp_angle_r'):
            c.find('locked').text = 'true'
            c.find('default_value').text = '0'
    return ET.tostring(xml, encoding='utf-8', xml_declaration=True)

matched_hash = hashlib.sha256(model_bytes()).hexdigest()
assert matched_hash == reference['provenance']['matched_model_sha256']
report['independent_matched_copy_sha256'] = matched_hash

cfg = yaml.safe_load((REPO/'config/phase_d1_squat.yaml').read_text())['parameters']
time = np.linspace(0., cfg['period']['value'], cfg['samples']['value'])
freq = 2*np.pi/cfg['period']['value']
start, depth = (np.array(cfg[k]['value']) for k in ('start_angles', 'depth_angles'))
amp = (depth-start)[:, None]/2
q = start[:, None] + amp*(1-np.cos(freq*time))
qd = amp*freq*np.sin(freq*time)
gait = next(r for r in record['runs'] if r['body'] == 'gait2392')
tau = np.array([gait['series']['tau_per_leg_N_m'][j] for j in ('ankle','knee','hip')])
reported = np.array(gait['series']['t_star_N_m'])

def solve_t(C, target):
    m, n = C.shape
    A = np.vstack((np.c_[-C,-np.ones(m)], np.c_[C,-np.ones(m)]))
    lp = linprog(np.r_[np.zeros(n),1.], A_ub=A, b_ub=np.r_[-target,target],
                 bounds=[(0.,1.)]*n+[(0.,None)], method='highs-ipm')
    assert lp.success
    return float(lp.fun)

def capacity_sweep(path):
    m = osim.Model(str(path))
    osim.DeGrooteFregly2016Muscle.replaceMuscles(m)
    muscles = [osim.DeGrooteFregly2016Muscle.safeDownCast(m.getMuscles().get(n)) for n in names]
    for mu in muscles:
        mu.set_ignore_tendon_compliance(True)
        # Activations are prescribed states, with no time integration.
        mu.set_ignore_activation_dynamics(False)
        mu.set_ignore_passive_fiber_force(True)
        mu.set_fiber_damping(0.)
        mu.set_active_force_width_scale(1.)
        mu.set_passive_fiber_strain_at_one_norm_force(.6)
        mu.set_tendon_strain_at_one_norm_force(.049)
    state = m.initSystem()
    coords = [m.getCoordinateSet().get(n) for n in ('ankle_angle_r','knee_angle_r','hip_flexion_r')]
    sign = np.array([1.,-1.,1.])
    values = []
    for i in range(len(time)):
        for j, c in enumerate(coords):
            c.setValue(state,float(sign[j]*q[j,i]),False)
            c.setSpeedValue(state,float(sign[j]*qd[j,i]))
        m.assemble(state)
        for mu in muscles: mu.setActivation(state,1.)
        m.realizeDynamics(state)
        C = np.zeros((3,len(muscles)))
        for j, mu in enumerate(muscles):
            assert .2 <= mu.getNormalizedFiberLength(state) <= 1.8
            assert -1. <= mu.getNormalizedFiberVelocity(state) <= 1.
            C[:,j] = mu.getTendonForce(state)*sign*np.array([mu.computeMomentArm(state,c) for c in coords])
        values.append(solve_t(C,tau[:,i]))
    return np.array(values)

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    fixed = tmp/'fixed.osim'; fixed.write_bytes(model_bytes())
    moving = tmp/'moving_knee_only.osim'; moving.write_bytes(model_bytes(True))
    fixed_t = capacity_sweep(fixed)
    moving_t = capacity_sweep(moving)
    error = float(np.max(np.abs(fixed_t-reported)))
    assert error < 1e-6, error   # official manifest rounds D1 torque to 6 decimals
    report['direct_opensim_capacity'] = {
        'samples': len(time), 'fixed_knee_max_t_star_N_m': float(fixed_t.max()),
        'max_abs_difference_from_manifest_t_star_N_m': error,
        'moving_knee_only_max_t_star_N_m': float(moving_t.max()),
        'moving_knee_only_flagged_samples': int(np.sum(moving_t>1.)),
        'held_fixed': 'D1 torque demand, z-axis ankle, locked subtalar/MTP, force law and muscle set',
        'limit': 'Counterfactual muscle-geometry check, not moving-knee inverse dynamics.'}

    base = yaml.safe_load(runner.CONFIG.read_text())
    cases = {}
    for label in ('wrong_reserve_unit', 'unsupported_force_width', 'unsupported_passive_baseline'):
        bad = copy.deepcopy(base)
        if label == 'wrong_reserve_unit':
            bad['parameters']['epsilon_reserve'].update(value=1000., unit='mN*m')
        if label == 'unsupported_force_width':
            bad['baseline_force_law']['active_force_width_scale'] = 2.
        if label == 'unsupported_passive_baseline':
            bad['baseline_force_law']['passive_fiber_force'] = 'included'
        p = tmp/(label+'.yaml'); p.write_text(yaml.safe_dump(bad))
        try:
            parsed, params = runner.load_config(p)
            cases[label] = {'accepted': True, 'parsed_baseline': parsed['baseline_force_law'],
                'interpreted_reserve_allowance_N_m': params['epsilon_reserve'],
                'gait2392_classified_feasible_with_current_t_star': float(fixed_t.max()) <= params['epsilon_reserve']}
        except ValueError as exc:
            cases[label] = {'accepted': False, 'reason': str(exc)}
    report['configuration_adversarial'] = cases

(OUT/'reviewer_probes.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
print(json.dumps(report, indent=2, sort_keys=True))
