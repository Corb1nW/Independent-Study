"""D-053: right sagittal hip, demonstration-only data-to-dynamics path.

Constant signed moment arm, fixed activation, constant angular acceleration.
No anatomical/clinical validity is claimed.
"""
import hashlib
import json
import math
import subprocess
from pathlib import Path

import yaml
from .quantitative import QuantitativeSchema

ROOT = Path(__file__).resolve().parents[1]
TARGET = "LB:MUS:GLUTEUS_MAXIMUS_R"
BASE_ID = "LB-QD:GMAX:FMAX:ARNOLD2010"
COORD = "LB:DOF:HIP_FLEX_EXT_R"
FRAME = "LB:FRAME:PELVIS"
UNITS = {
    "moment_arm_m": "m", "thigh_inertia_kg_m2": "kg*m^2",
    "activation": "1", "external_torque_N_m": "N*m",
    "initial_q_rad": "rad", "initial_qdot_rad_s": "rad/s",
    "q_min_rad": "rad", "q_max_rad": "rad",
    "step_s": "s", "duration_s": "s", "event_tolerance_s": "s",
}


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finite(value, field):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{field}: expected finite numerical value")
    return float(value)


def load_config(path):
    config = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    required = {"model_id", "coordinate_id", "frame_id", "neutral_pose",
                "force_observation_id", "target_entity_id", "parameters"}
    if not isinstance(config, dict) or set(config) != required:
        raise ValueError("incorrect configuration fields")
    if (config["coordinate_id"], config["frame_id"], config["target_entity_id"],
        config["force_observation_id"]) != (COORD, FRAME, TARGET, BASE_ID):
        raise ValueError("wrong ontology reference or force observation")
    if not all(isinstance(config[k], str) and config[k].strip()
               for k in ("model_id", "neutral_pose")):
        raise ValueError("neutral pose and model ID required")
    entries = config["parameters"]
    if not isinstance(entries, dict) or set(entries) != set(UNITS):
        raise ValueError("missing or unexpected numerical parameter")
    values = {}
    for name, unit in UNITS.items():
        item = entries[name]
        if not isinstance(item, dict) or set(item) != {"value", "unit", "kind", "rationale"}:
            raise ValueError(f"{name}: incomplete parameter provenance")
        if (item["unit"] != unit or item["kind"] != "demonstration_assumption"
            or not isinstance(item["rationale"], str) or not item["rationale"].strip()):
            raise ValueError(f"{name}: unit or provenance invalid")
        values[name] = finite(item["value"], name)
    for name in ("moment_arm_m", "thigh_inertia_kg_m2", "step_s",
                 "duration_s", "event_tolerance_s"):
        if values[name] <= 0:
            raise ValueError(f"{name} must be positive")
    if not 0 <= values["activation"] <= 1:
        raise ValueError("activation out of bounds")
    if (not math.isclose(values["q_min_rad"], -math.pi/6, abs_tol=1e-12)
        or not math.isclose(values["q_max_rad"], math.pi/3, abs_tol=1e-12)):
        raise ValueError("D-053 demonstration domain altered")
    if not values["q_min_rad"] <= values["initial_q_rad"] <= values["q_max_rad"]:
        raise ValueError("initial angle outside domain")
    if values["event_tolerance_s"] >= values["step_s"]:
        raise ValueError("event tolerance must be below time step")
    return config, values


def load_scenario(path, schema, dataset):
    scenario = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    expected = {"scenario_id", "kind", "target_entity_id", "base_observation_id",
                "parameter", "scenario_multiplier", "reason"}
    if not isinstance(scenario, dict) or set(scenario) != expected:
        raise ValueError("missing or unexpected scenario field")
    if not all(isinstance(scenario[k], str) and scenario[k].strip()
               for k in ("scenario_id", "reason")):
        raise ValueError("scenario ID and reason required")
    if (scenario["kind"] != "demonstration_scenario_not_evidence"
        or scenario["parameter"] != "maximum_isometric_force"):
        raise ValueError("scenario must be labelled as a force demonstration, not evidence")
    target = scenario["target_entity_id"]
    if (target != TARGET or target not in schema.ontology.entities
        or schema.ontology.get(target).get("side") != "right"):
        raise ValueError("target must be an existing right-side gluteus maximus")
    if (scenario["base_observation_id"] != BASE_ID
        or BASE_ID not in dataset["observations"]):
        raise ValueError("scenario must cite the existing source observation")
    multiplier = finite(scenario["scenario_multiplier"], "scenario_multiplier")
    if multiplier <= 0:
        raise ValueError("multiplier must be strictly positive")
    return scenario, multiplier


def resolve_inputs(config_path, scenario_path, root=ROOT):
    root = Path(root)
    config, p = load_config(config_path)
    schema = QuantitativeSchema(root/"ontology"/"quantitative_schema.yaml")
    for entity in (TARGET, COORD, FRAME):
        if entity not in schema.ontology.entities:
            raise ValueError(f"unresolved ontology reference {entity}")
    path = root/"ontology"/"quantitative_data"/"gluteus_maximus.yaml"
    dataset = schema.load_dataset(path)
    baseline = schema.effective_baseline(dataset, TARGET)
    if BASE_ID not in baseline:
        raise ValueError("populated whole-muscle force unavailable")
    datum = baseline[BASE_ID]
    errors = schema.validate_datum(datum, dataset)
    if errors:
        raise ValueError("source datum fails validation: " + "; ".join(errors))
    if (datum["property_id"] != "maximum_isometric_force"
        or datum["property_role"] != "parameter"
        or datum["value_form"] != "scalar"
        or datum["unit"] != "N"
        or datum["applicability"].get("model_id") != "ARNOLD_2010_LOWER_LIMB"):
        raise ValueError("incorrect source force scope, unit or definition")
    base_value = finite(datum["value"], "Fmax")
    if base_value <= 0:
        raise ValueError("Fmax must be positive")
    scenario, factor = load_scenario(scenario_path, schema, dataset)
    right_force = base_value*factor
    if not math.isfinite(right_force) or right_force <= 0:
        raise ValueError("nonfinite effective force")
    left = schema.effective_baseline(dataset, "LB:MUS:GLUTEUS_MAXIMUS_L")[BASE_ID]["value"]
    return {
        "config": config, "params": p, "scenario": scenario, "observation": datum,
        "baseline_fmax_N": base_value, "right_fmax_N": right_force,
        "left_fmax_N": left, "source_dataset_hash": file_hash(path),
        "config_hash": file_hash(config_path), "scenario_hash": file_hash(scenario_path),
    }


def first_boundary(q, v, acc, dt, lo, hi, tolerance):
    """First outward boundary crossing of the constant-acceleration trajectory."""
    hits = []
    for bound, which in ((lo, "lower"), (hi, "upper")):
        if abs(q-bound) <= 1e-12:
            outward = (v < -1e-12 if which == "lower" else v > 1e-12)
            if abs(v) <= 1e-12:  # N2: zero-speed boundary uses net acceleration
                outward = (acc < 0 if which == "lower" else acc > 0)
            if outward:
                hits.append((0.0, bound, which))
        if abs(acc) < 1e-15:
            roots = [(bound-q)/v] if abs(v) > 1e-15 else []
        else:
            discriminant = v*v - 2*acc*(q-bound)
            roots = [] if discriminant < 0 else [
                (-v-math.sqrt(discriminant))/acc, (-v+math.sqrt(discriminant))/acc]
        for t in roots:
            if 1e-12 < t <= dt+tolerance:
                velocity = v+acc*t
                if velocity < -1e-12 if which == "lower" else velocity > 1e-12:
                    hits.append((min(t, dt), bound, which))
    return min(hits, key=lambda x:x[0]) if hits else None


def simulate(inputs, *, step_override_s=None):
    p = inputs["params"]
    dt = p["step_s"] if step_override_s is None else finite(step_override_s, "step")
    if dt <= p["event_tolerance_s"]:
        raise ValueError("step must exceed tolerance")
    torque = -p["moment_arm_m"]*p["activation"]*inputs["right_fmax_N"]
    net_torque = torque+p["external_torque_N_m"]
    acc = net_torque/p["thigh_inertia_kg_m2"]
    q, v, t = p["initial_q_rad"], p["initial_qdot_rad_s"], 0.0
    lower, upper = p["q_min_rad"], p["q_max_rad"]
    steps = 0
    while t < p["duration_s"]-1e-14:
        h = min(dt, p["duration_s"]-t)
        hit = first_boundary(q, v, acc, h, lower, upper, p["event_tolerance_s"])
        if hit is not None:
            delta, boundary, which = hit
            result = ("domain_exit", t+delta, boundary, v+acc*delta, which)
            break
        q_new = q+v*h+acc*h*h/2
        if q_new < lower-1e-12 or q_new > upper+1e-12:
            raise RuntimeError("undetected domain exit")
        v += acc*h
        q = q_new
        t += h
        steps += 1
    else:
        result = ("completed", t, q, v, None)
    status, time_s, angle, velocity, limit = result
    return {
        "outcome": status, "time_s": time_s, "q_rad": angle,
        "qdot_rad_per_s": velocity, "which_limit": limit,
        "last_valid_state": {"time_s": t, "q_rad": q, "qdot_rad_per_s": v},
        "event_method": "analytic_quadratic_step_root",
        "event_tolerance_s": p["event_tolerance_s"],
        "gluteus_torque_N_m": torque, "net_torque_N_m": net_torque,
        "angular_acceleration_rad_s2": acc, "steps_before_exit": steps,
    }


def run_manifest(inputs, result, commit_sha):
    if not isinstance(commit_sha, str) or len(commit_sha) != 40 or any(
            ch not in "0123456789abcdef" for ch in commit_sha):
        raise ValueError("exact 40-character commit SHA required")
    try:
        actual = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        status = "caller_supplied_sha_unverified_archive_or_no_git"
    else:
        if actual != commit_sha:
            raise ValueError("supplied SHA differs from Git checkout HEAD")
        status = "verified_git_head"
    obs = inputs["observation"]
    return {
        "status": "UNREVIEWED DEMONSTRATION — NOT CLINICALLY/PHYSIOLOGICALLY VALIDATED",
        "commit_sha": commit_sha, "commit_provenance_status": status,
        "decision": "D-053", "model_id": inputs["config"]["model_id"],
        "coordinate_id": COORD, "frame_id": FRAME,
        "neutral_pose": inputs["config"]["neutral_pose"],
        "equations": {
            "force": "F_MT = activation * effective_right_Fmax",
            "muscle_torque": "tau_GMAX = -r0 * F_MT",
            "dynamics": "I * qdd = tau_GMAX + external_torque",
            "sign": "q positive flexion; gluteus extension torque negative",
            "length_if_used": "L_MT = L_ref + r0*q; r=-dL_MT/dq"},
        "configuration": inputs["config"],
        "configuration_sha256": inputs["config_hash"],
        "scenario": inputs["scenario"], "scenario_sha256": inputs["scenario_hash"],
        "source": {
            "observation_id": BASE_ID, "value_N": inputs["baseline_fmax_N"],
            "unit": obs["unit"], "datum_kind": obs["datum_kind"],
            "source_claims": obs["provenance"]["source_claims"],
            "transformation_history": obs["provenance"].get("transformation_history"),
            "source_value_location": obs["provenance"].get("source_value_location"),
            "applicability": obs["applicability"], "target": obs["target"],
            "dataset_sha256": inputs["source_dataset_hash"]},
        "effective_values": {
            "baseline_Fmax_N": inputs["baseline_fmax_N"],
            "right_Fmax_N": inputs["right_fmax_N"],
            "left_baseline_Fmax_N": inputs["left_fmax_N"],
            "scenario_multiplier": inputs["scenario"]["scenario_multiplier"]},
        "pennation_disclosure": {
            "rule": "No additional cos(pennation) projection",
            "illustrative_ward_mean_deg": 21.9,
            "conditional_overstatement": "about 7.8% if Fmax denotes fiber force; NOT a verified Arnold correction",
            "status": "pennation not consumed in dynamics"},
        "simulation": result,
    }


def serialize_manifest(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+"\n"
