"""D-060 proposal probes only: source geometry and translational virtual work."""
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import numpy as np
import opensim as osim
import yaml

ROOT = Path(__file__).parent
REPO, OUT = ROOT/'repo', ROOT/'out'
sys.path.insert(0, str(REPO))
from src.muscles_d2 import SimmSpline

source = REPO/'sources/vendor/opensim-models/gait2392_millard2012muscle.osim'
xml = ET.parse(source).getroot()
joint = next(j for j in xml.iter('CustomJoint') if j.get('name') == 'knee_r')
axes = {a.get('name'): a for a in joint.iter('TransformAxis')}
splines = []
for name in ('translation1', 'translation2'):
    a = axes[name]
    assert a.findtext('coordinates') == 'knee_angle_r'
    f = a.find('SimmSpline')
    x, y = (list(map(float, f.findtext(k).split())) for k in ('x', 'y'))
    splines.append(SimmSpline(x, y))
    assert min(x) <= -math.radians(100) <= 0 <= max(x)

def T(q):
    return np.array([s.value(-q) for s in splines]+[0.])
def dT(q):
    return -np.array([s.derivative(-q) for s in splines]+[0.])

model = osim.Model(str(source))
state = model.initSystem()
knee = model.getCoordinateSet().get('knee_angle_r')
femur, tibia = (model.getBodySet().get(n) for n in ('femur_r','tibia_r'))
rows = []
for deg in (0., 30., 60., 100.):
    q = math.radians(deg)
    knee.setValue(state, -q, False)
    model.assemble(state)
    model.realizePosition(state)
    p = tibia.findStationLocationInAnotherFrame(state, osim.Vec3(0), femur)
    actual = np.array([p.get(i) for i in range(3)])
    expected = T(q)
    error = float(np.max(np.abs(actual-expected)))
    assert error < 1e-12, (deg, actual, expected)
    rows.append({'flexion_deg':deg,'tibia_origin_in_femur_m':actual.tolist(),'max_error_m':error})

observations = yaml.safe_load((REPO/'ontology/quantitative_data/segments_gait2392.yaml').read_text())['observations']
fixed = np.array(observations['LB-QD:G2392:JOINT:KNEE_R']['value'])
zero = T(0.)
bottom = T(math.radians(100.))

# Fixture forces chosen only to check the virtual-work identity, not anatomy.
q, qdot = math.radians(60.), .7
force = np.array([100., -300., 0.])
h = 1e-5
numeric = (T(q+h)-T(q-h))/(2*h)
generalized = float(force@dT(q))
assert abs(generalized-float(force@numeric)) < 1e-7
power = float(force@(dT(q)*qdot))
assert abs(power-generalized*qdot) < 1e-12

report = {
    'opensim_version':osim.__version__,
    'source_joint_axes':{n:axes[n].findtext('axis') for n in ('rotation1','translation1','translation2')},
    'source_geometry':rows,
    'legacy_D1_fixed_knee_m':fixed.tolist(),
    'smooth_T_at_zero_m':zero.tolist(),
    'smooth_zero_minus_legacy_fixed_mm':((zero-fixed)*1000).tolist(),
    'smooth_0_to_100_translation_mm':((bottom-zero)*1000).tolist(),
    'virtual_work_fixture':{'knee_flexion_deg':60.,'force_N':force.tolist(),'qdot_rad_s':qdot,
                            'dT_dq_m_per_rad':dT(q).tolist(),
                            'translation_contribution_N_m':generalized,'translation_power_W':power},
    'limits':'Source geometry and a mathematical fixture only; no D3 inverse dynamics or feasibility pre-check was reproduced.'}
(OUT/'scope_probes.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
