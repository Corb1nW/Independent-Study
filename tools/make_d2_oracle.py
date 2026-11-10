"""OpenSim oracle for Stage D2 (D-059 item 8 with Amendments 1 and 2).

    python -m tools.make_d2_oracle --output tests/data/d2_oracle_reference.json
    python -m tools.make_d2_oracle --matched-copy-only out.osim   # no OpenSim needed

Writes a reference file of values computed by OpenSim (pip package `opensim` 4.6) on a
D1-MATCHED copy of the vendored Gait2392 model. The copy is produced from the
unmodified file by `matched_model_xml`, which makes exactly these changes:

  1. knee_r translation1/translation2: SimmSpline -> Constant at the D1 knee centre
     (dataset observation LB-QD:G2392:JOINT:KNEE_R), freezing the knee translation;
  2. ankle_r rotation1 axis -> (0, 0, 1) and rotation3 axis -> (1, 0, 0), so the ankle
     rotates about z as in D1 (rotation2 and rotation3 are constant 0 in the file);
  3. subtalar_angle_r and mtp_angle_r locked at 0.

After loading, every Millard muscle is converted with
DeGrooteFregly2016Muscle.replaceMuscles, and the properties that conversion copies
from the Millard muscles are RESET (Amendment 1): rigid tendon, passive fiber force
ignored (baseline) or not (passive case), fiber damping 0, active-force width scale 1,
passive strain 0.6, tendon strain 0.049.

Ordinary tests read the reference file; they never import OpenSim. The values come from
OpenSim, never from src/muscles_d2.py.
"""
import argparse
import hashlib
import json
import math
import platform
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
OSIM = ROOT / "sources" / "vendor" / "opensim-models" / "gait2392_millard2012muscle.osim"
KNEE_DATUM = ROOT / "ontology" / "quantitative_data" / "segments_gait2392.yaml"
CONFIG = ROOT / "config" / "phase_d1_squat.yaml"
ACTUATORS = ["glut_max1_r", "glut_max2_r", "glut_max3_r", "bifemlh_r", "semimem_r", "semiten_r", "vas_med_r",
             "vas_int_r", "vas_lat_r", "rect_fem_r", "med_gas_r", "lat_gas_r", "soleus_r", "tib_ant_r"]
COORDS = {"ankle": "ankle_angle_r", "knee": "knee_angle_r", "hip": "hip_flexion_r"}
# OpenSim coordinate = sign x D1 coordinate (knee: Gait2392 flexion is negative).
SIGN = {"ankle": 1.0, "knee": -1.0, "hip": 1.0}
OVERRIDES = {"ignore_tendon_compliance": True, "ignore_activation_dynamics": False, "fiber_damping": 0.0,
             "active_force_width_scale": 1.0, "passive_fiber_strain_at_one_norm_force": 0.6,
             "tendon_strain_at_one_norm_force": 0.049}
ACTIVITY_TOL = 1e-5
SWITCH_OFFSET = 1e-4      # rad beyond the widened edge, so both conventions agree
ACTIVATIONS = (0.0, 0.37, 1.0)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def knee_centre():
    d = yaml.safe_load(KNEE_DATUM.read_text(encoding="utf-8"))
    return d["observations"]["LB-QD:G2392:JOINT:KNEE_R"]["value"]


def matched_model_xml():
    """Bytes of the D1-matched model, from the unmodified vendored file (no OpenSim needed)."""
    tree = ET.parse(OSIM)
    root = tree.getroot()
    joints = {j.get("name"): j for j in root.iter("CustomJoint")}
    knee = joints["knee_r"]
    kc = knee_centre()
    for axis_name, value in (("translation1", kc[0]), ("translation2", kc[1])):
        ta = [t for t in knee.iter("TransformAxis") if t.get("name") == axis_name][0]
        func = list(ta)
        for child in func:
            if child.tag not in ("coordinates", "axis"):
                ta.remove(child)
                const = ET.SubElement(ta, "Constant")
                ET.SubElement(const, "value").text = repr(float(value))
        ta.find("coordinates").text = ""
    ankle = joints["ankle_r"]
    for ta in ankle.iter("TransformAxis"):
        if ta.get("name") == "rotation1":
            ta.find("axis").text = "0 0 1"
        if ta.get("name") == "rotation3":
            ta.find("axis").text = "1 0 0"
    for c in root.iter("Coordinate"):
        if c.get("name") in ("subtalar_angle_r", "mtp_angle_r"):
            locked = c.find("locked")
            if locked is None:
                locked = ET.SubElement(c, "locked")
            locked.text = "true"
            c.find("default_value").text = "0"
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def d1_poses():
    """D1 sample states of the configuration's motion: q, qdot (3 x n) in D1 coordinates."""
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))["parameters"]
    start = np.array(cfg["start_angles"]["value"]); depth = np.array(cfg["depth_angles"]["value"])
    period, n = cfg["period"]["value"], int(cfg["samples"]["value"])
    t = np.linspace(0.0, period, n)
    w = 2 * math.pi / period
    amp = (depth - start)[:, None] / 2
    return start[:, None] + amp * (1 - np.cos(w * t)), amp * w * np.sin(w * t), depth


def geometry_states(tree_root):
    """Poses for the geometry check: D1 samples, spline knots and both sides of each conditional switch."""
    q, _, depth = d1_poses()
    states = [{"kind": "d1_sample", "index": i, "q": q[:, i].tolist()} for i in range(q.shape[1])]
    ratio = depth / depth[1]                       # ankle and hip follow the knee in D1's motion
    muscles = {m.get("name"): m for m in tree_root.iter("Millard2012EquilibriumMuscle")}
    knots, edges = set(), set()
    for name in ACTUATORS:
        for p in muscles[name].find(".//PathPointSet/objects"):
            if p.tag == "MovingPathPoint":
                for ax in "xyz":
                    s = p.find(f"{ax}_location")[0]
                    if s.tag == "SimmSpline":
                        knots.update(float(v) for v in s.findtext("x").split())
            if p.tag == "ConditionalPathPoint":
                lo, hi = map(float, p.findtext("range").split())
                edges.update((lo - ACTIVITY_TOL, hi + ACTIVITY_TOL))
    for k in sorted(knots):
        qk = -k
        if 0.0 <= qk <= depth[1]:
            states.append({"kind": "spline_knot", "knee_angle_gait2392": k, "q": (ratio * qk).tolist()})
    for e in sorted(edges):
        qk = -e
        if 0.0 < qk < depth[1]:
            for side, off in (("flexion_side", SWITCH_OFFSET), ("extension_side", -SWITCH_OFFSET)):
                states.append({"kind": "switch_side", "edge_knee_angle_gait2392": e, "side": side,
                               "q": (ratio * (qk + off)).tolist()})
    return states


def force_states():
    """States for the assembled force law: poses across the motion with shortening and lengthening speeds."""
    q, qd, depth = d1_poses()
    out = []
    for i in (0, 40, 75, 110, 150, 190, 225, 260):
        for scale in (1.0, -1.0, 3.0, -3.0):
            out.append({"q": q[:, i].tolist(), "qdot": (scale * qd[:, i] if i not in (0, 150) else
                                                      scale * np.array([0.2, 0.5, 0.37])).tolist()})
    return out


def _model(xml_path, passive):
    import opensim as osim
    m = osim.Model(str(xml_path))
    osim.DeGrooteFregly2016Muscle.replaceMuscles(m)
    for name in ACTUATORS:
        mu = osim.DeGrooteFregly2016Muscle.safeDownCast(m.getMuscles().get(name))
        mu.set_ignore_tendon_compliance(OVERRIDES["ignore_tendon_compliance"])
        mu.set_ignore_activation_dynamics(OVERRIDES["ignore_activation_dynamics"])
        mu.set_ignore_passive_fiber_force(not passive)
        mu.set_fiber_damping(OVERRIDES["fiber_damping"])
        mu.set_active_force_width_scale(OVERRIDES["active_force_width_scale"])
        mu.set_passive_fiber_strain_at_one_norm_force(OVERRIDES["passive_fiber_strain_at_one_norm_force"])
        mu.set_tendon_strain_at_one_norm_force(OVERRIDES["tendon_strain_at_one_norm_force"])
    s = m.initSystem()
    return m, s


def _set(m, s, q, qd=(0.0, 0.0, 0.0)):
    cs = m.getCoordinateSet()
    for j, (key, name) in enumerate(COORDS.items()):
        cs.get(name).setValue(s, SIGN[key] * q[j], False)
        cs.get(name).setSpeedValue(s, SIGN[key] * qd[j])
    m.assemble(s)


def run_oracle(matched_path):
    import opensim as osim
    m, s = _model(matched_path, passive=False)
    cs = m.getCoordinateSet()
    root = ET.parse(matched_path).getroot()
    geometry = []
    for st in geometry_states(root):
        _set(m, s, st["q"])
        m.realizePosition(s)
        row = dict(st)
        row["length_m"], row["moment_arm_m"] = {}, {}
        for name in ACTUATORS:
            mu = m.getMuscles().get(name)
            row["length_m"][name] = mu.getLength(s)
            # OpenSim moment arm r = -dL/d(OpenSim coordinate); in D1 coordinates R = sign x r.
            row["moment_arm_m"][name] = [SIGN[k] * mu.computeMomentArm(s, cs.get(c)) for k, c in COORDS.items()]
        geometry.append(row)
    forces = []
    for passive in (False, True):
        mp, sp = _model(matched_path, passive=passive)
        for st in force_states():
            for a in ACTIVATIONS:
                _set(mp, sp, st["q"], st["qdot"])
                for name in ACTUATORS:
                    osim.DeGrooteFregly2016Muscle.safeDownCast(mp.getMuscles().get(name)).setActivation(sp, a)
                mp.realizeDynamics(sp)
                vals = {}
                for name in ACTUATORS:
                    mu = osim.DeGrooteFregly2016Muscle.safeDownCast(mp.getMuscles().get(name))
                    vals[name] = {"length_m": mu.getLength(sp), "lengthening_speed_m_s": mu.getLengtheningSpeed(sp),
                                  "fiber_length_m": mu.getFiberLength(sp), "pennation_rad": mu.getPennationAngle(sp),
                                  "fiber_velocity_m_s": mu.getFiberVelocity(sp),
                                  "normalized_fiber_velocity": mu.getNormalizedFiberVelocity(sp),
                                  "tendon_force_N": mu.getTendonForce(sp),
                                  "passive_fiber_force_N": mu.getPassiveFiberForce(sp)}
                forces.append({"passive": passive, "q": st["q"], "qdot": st["qdot"], "activation": a, "values": vals})
    return geometry, forces


def run_unmodified():
    """Lengths and moment arms on the UNMODIFIED Gait2392 file at every 10th D1 sample (D-059 item 8f)."""
    m, s = _model(OSIM, passive=False)
    cs = m.getCoordinateSet()
    q, _, _ = d1_poses()
    rows = []
    for i in range(0, q.shape[1], 10):
        _set(m, s, q[:, i])
        m.realizePosition(s)
        rows.append({"index": i, "q": q[:, i].tolist(),
                     "length_m": {n: m.getMuscles().get(n).getLength(s) for n in ACTUATORS},
                     "moment_arm_m": {n: [SIGN[k] * m.getMuscles().get(n).computeMomentArm(s, cs.get(c))
                                          for k, c in COORDS.items()] for n in ACTUATORS}})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--output")
    ap.add_argument("--matched-copy-only")
    args = ap.parse_args()
    xml = matched_model_xml()
    if args.matched_copy_only:
        Path(args.matched_copy_only).write_bytes(xml)
        print("wrote", args.matched_copy_only, sha256(xml))
        return
    import tempfile
    import opensim as osim
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "gait2392_d1_matched.osim"
        path.write_bytes(xml)
        geometry, forces = run_oracle(path)
    unmodified = run_unmodified()
    ref = {
        "description": ("OpenSim oracle values for Stage D2 (D-059 item 8): computed by OpenSim on the D1-matched copy "
                        "of the vendored Gait2392 model. Not produced by src/muscles_d2.py."),
        "provenance": {
            "opensim_version": osim.__version__, "python": sys.version.split()[0], "platform": platform.platform(),
            "numpy": np.__version__,
            "source_model": str(OSIM.relative_to(ROOT)), "source_model_sha256": sha256(OSIM.read_bytes()),
            "matched_model_sha256": sha256(xml), "tool": "tools/make_d2_oracle.py",
            "tool_sha256": sha256(Path(__file__).read_bytes()),
            "matched_model_changes": ["knee_r translation1/2 -> Constant at LB-QD:G2392:JOINT:KNEE_R",
                                      "ankle_r rotation1 axis -> 0 0 1; rotation3 axis -> 1 0 0",
                                      "subtalar_angle_r and mtp_angle_r locked at 0"],
            "muscle_conversion": "DeGrooteFregly2016Muscle.replaceMuscles, then overrides reset",
            "overrides": OVERRIDES, "passive_cases": "ignore_passive_fiber_force true (baseline) and false",
            "coordinate_map": {k: f"{COORDS[k]} = {SIGN[k]:+.0f} x D1 q_{k}" for k in COORDS},
            "moment_arm_sign": "stored in D1 coordinates: R = -dL/dq_D1",
            "units": "m, rad, m/s, N; activation dimensionless",
            "conditional_activity_tolerance_rad": ACTIVITY_TOL, "switch_offset_rad": SWITCH_OFFSET,
            "unmodified_geometry": ("the vendored model as published (knee translation splines, oblique ankle axis, "
                                    "free subtalar and MTP at 0), every 10th D1 sample, for D-059 item 8f")},
        "actuators": ACTUATORS,
        "geometry": geometry,
        "forces": forces,
        "unmodified_geometry": unmodified,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ref, separators=(",", ":")) + "\n", encoding="utf-8")
    print("wrote", out, f"({len(geometry)} geometry states, {len(forces)} force states)")


if __name__ == "__main__":
    main()
