"""Coverage check for the OpenSim oracle reference files (ChatGPT note D3-N03).

    python -m tools.oracle_coverage tests/data/d2_oracle_reference.json --knee fixed
    python -m tools.oracle_coverage tests/data/d3_oracle_reference.json --knee moving

A comparison against a reference only means something if the reference holds the states it is
supposed to hold. This module rebuilds the expected state list from the same functions that
tools/make_d2_oracle.py uses to generate it (no OpenSim needed) and checks that the file matches it
exactly: every geometry, force, unmodified-model and kinematics row, in order, with identical poses
and speeds; the source and matched model hashes; the recorded oracle-tool hash; and finite values
for every actuator and quantity. A stale, truncated, repeated or edited reference fails with a list
of problems. It checks the reference's coverage and provenance, not OpenSim's values.

Kept separate from tools/make_d2_oracle.py so that adding checks here does not change that tool's
hash, which each reference records.
"""
import argparse
import hashlib
import math
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

from tools import make_d2_oracle as oracle

TOOL = Path(oracle.__file__)
KINEMATIC_KEYS = ("knee_m", "hip_m", "pelvis_origin_m", "femur_com_m", "tibia_com_m")
FORCE_KEYS = ("length_m", "lengthening_speed_m_s", "fiber_length_m", "pennation_rad", "fiber_velocity_m_s",
              "normalized_fiber_velocity", "tendon_force_N", "passive_fiber_force_N")


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _finite(values):
    return all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values)


def expected_states(knee_mode):
    """The states tools/make_d2_oracle.py generates for this knee mode, in file order."""
    root = ET.fromstring(oracle.matched_model_xml(knee_mode))
    geometry = oracle.geometry_states(root)
    forces = [{"passive": passive, "kind": st.get("kind", "motion"), "q": st["q"], "qdot": st["qdot"], "activation": a}
              for passive in (False, True) for st in oracle.force_states(root) for a in oracle.ACTIVATIONS]
    q, _, _ = oracle.d1_poses()
    unmodified = [{"index": i, "q": q[:, i].tolist()} for i in range(0, q.shape[1], 10)]
    kinematics = [{"index": i, "q": q[:, i].tolist()} for i in range(q.shape[1])] if knee_mode == "moving" else None
    return {"geometry": geometry, "forces": forces, "unmodified_geometry": unmodified, "kinematics": kinematics}


def _compare_rows(name, rows, expected, keys, problems):
    if not isinstance(rows, list):
        problems.append(f"{name}: missing")
        return
    if len(rows) != len(expected):
        problems.append(f"{name}: {len(rows)} rows, expected {len(expected)}")
    for k, (row, exp) in enumerate(zip(rows, expected)):
        for key in keys:
            if key in exp and row.get(key) != exp[key]:
                problems.append(f"{name}[{k}]: {key} is {row.get(key)!r}, expected {exp[key]!r}")
                break


def check_reference(ref, knee_mode):
    """List of problems (empty when the reference covers exactly the expected states with finite values)."""
    problems = []
    prov = ref.get("provenance", {})
    if prov.get("knee_mode", "fixed") != knee_mode:
        problems.append(f"provenance.knee_mode is {prov.get('knee_mode')!r}, expected {knee_mode!r}")
    if prov.get("source_model_sha256") != _sha(oracle.OSIM.read_bytes()):
        problems.append("source model hash does not match the vendored model file")
    if prov.get("matched_model_sha256") != _sha(oracle.matched_model_xml(knee_mode)):
        problems.append("matched model hash does not match the copy the current tool builds")
    if prov.get("tool_sha256") != _sha(TOOL.read_bytes()):
        problems.append("recorded oracle-tool hash does not match tools/make_d2_oracle.py")
    if ref.get("actuators") != oracle.ACTUATORS:
        problems.append("actuator list differs from the 14 Stage D2 actuators")
    exp = expected_states(knee_mode)
    _compare_rows("geometry", ref.get("geometry"), exp["geometry"],
                  ("kind", "index", "q", "side", "edge_knee_angle_gait2392", "knee_angle_gait2392"), problems)
    _compare_rows("forces", ref.get("forces"), exp["forces"], ("passive", "kind", "q", "qdot", "activation"), problems)
    _compare_rows("unmodified_geometry", ref.get("unmodified_geometry"), exp["unmodified_geometry"],
                  ("index", "q"), problems)
    if exp["kinematics"] is not None:
        _compare_rows("kinematics", ref.get("kinematics"), exp["kinematics"], ("index", "q"), problems)
    elif "kinematics" in ref:
        problems.append("kinematics present in a fixed-knee reference")
    for name in ("geometry", "unmodified_geometry"):
        for k, row in enumerate(ref.get(name) or []):
            for a in oracle.ACTUATORS:
                L, R = row.get("length_m", {}).get(a), row.get("moment_arm_m", {}).get(a)
                if L is None or R is None or len(R) != 3 or not _finite([L, *R]):
                    problems.append(f"{name}[{k}]: missing or non-finite values for {a}")
                    break
    for k, row in enumerate(ref.get("forces") or []):
        vals = row.get("values", {})
        if set(vals) != set(oracle.ACTUATORS) or not all(
                set(FORCE_KEYS) <= set(v) and _finite([v[key] for key in FORCE_KEYS]) for v in vals.values()):
            problems.append(f"forces[{k}]: missing or non-finite force values")
    for k, row in enumerate(ref.get("kinematics") or []):
        if not all(isinstance(row.get(key), list) and len(row[key]) == 3 and _finite(row[key]) for key in KINEMATIC_KEYS):
            problems.append(f"kinematics[{k}]: missing or non-finite positions")
    if exp["kinematics"] is not None and isinstance(ref.get("kinematics"), list):
        positions = np.array([row.get("knee_m", [np.nan] * 3) for row in ref["kinematics"]], float)
        if positions.size and len(np.unique(np.round(positions, 12), axis=0)) < len(positions) // 2:
            problems.append("kinematics: knee positions repeat across most rows (a repeated or stale pose)")
    return problems


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("reference", type=Path)
    p.add_argument("--knee", choices=("fixed", "moving"), required=True)
    args = p.parse_args()
    problems = check_reference(json.loads(args.reference.read_text(encoding="utf-8")), args.knee)
    for line in problems[:50]:
        print(line)
    print(f"{args.reference}: {'COVERAGE OK' if not problems else f'{len(problems)} PROBLEM(S)'}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
