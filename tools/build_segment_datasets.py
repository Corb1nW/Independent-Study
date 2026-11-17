"""Build the segment-parameter datasets for Stage D1 (D-058 Amendment 2) and the muscle dataset for Stage D2 (D-059).

    python -m tools.build_segment_datasets          # writes all three datasets
    python -m tools.build_segment_datasets --check  # exit 1 if a dataset differs

Inputs are the unmodified source files in ``sources/vendor/`` (see its README):

- the OpenSim Gait2392 model file, for the reference body and for the geometry
  that the de Leva bodies are scaled from;
- the BMC reproduction of de Leva (1996) Table 4, for the female and male
  fractions of body mass and of segment length.

Every stored value is copied from those files, or computed from them with the
step recorded in ``transformation_history``. Nothing is typed in by hand except
the values from documentation pages (body mass and stature), which are quoted
with their location. ``tests/test_phase_d1.py`` regenerates both datasets and
checks that they equal the committed files.
"""
import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.model_spec import default_ontology  # noqa: E402
VENDOR = ROOT / "sources" / "vendor"
OSIM = VENDOR / "opensim-models" / "gait2392_millard2012muscle.osim"
BMC = {"female": VENDOR / "bmc" / "BSPfemale_ZdeLeva.txt", "male": VENDOR / "bmc" / "BSPmale_ZdeLeva.txt"}
OUT = ROOT / "ontology" / "quantitative_data"
RETRIEVED = "2026-10-28"
OSIM_COMMIT = "d9b05d470b1a481c222372c85b75772faf8f7792"
BMC_COMMIT = "4d0c2a2ae8adaea578d499076a0c520b2e47d82c"


def _vec(text):
    return [float(x) for x in text.split()]


def _num(x):
    """Plain float for YAML; integers stay floats so the files are stable."""
    return float(x)


def datum(property_id, definition, value, unit, kind, claims, location, target, applicability,
          value_form="scalar", frame=None, history=None, derivation=None, role="parameter",
          notes=None):
    d = {
        "target": target,
        "property_id": property_id,
        "property_definition": definition,
        "property_role": role,
        "value_form": value_form,
        "value": value,
        "unit": unit,
        "datum_kind": kind,
        "provenance": {"source_claims": claims, "source_value_location": location,
                       "retrieval_date": RETRIEVED, "transformation_history": history or []},
        "applicability": applicability,
        "derivation": derivation or {"inputs": [], "formula": None, "assumptions": []},
        "status": "populated",
    }
    if frame:
        d["coordinate_context"] = {"frame_id": frame, "coordinate_id": None, "convention_source_id": None,
                                   "axis": "x anterior, y superior, z right (Gait2392 body frame)",
                                   "reference_pose": "Gait2392 default pose (all coordinates zero)"}
    if notes:
        d["quality"] = {"validation_status": "reviewed_for_source_traceability", "limitations": [],
                        "conflicts_with": [], "value_comparisons": [], "reviewer_notes": notes}
    return d


# --------------------------------------------------------------------- Gait2392
G_APPLICABILITY = {
    "level": "generic_model",
    "population": ("Unscaled OpenSim Gait2392 model, documented as a subject about 1.8 m tall with a mass of "
                   "75.16 kg. Inertial parameters adapted from Anderson and Pandy (1999), averaged over five "
                   "subjects (age 26 +/- 3 years, height 177 +/- 3 cm, weight 70.1 +/- 7.8 kg); hindfoot and toe "
                   "values from a size-10 shoe. Sex not stated in the model documentation."),
    "model_id": "OPENSIM_GAIT2392",
    "sex": None,
}
BODY_SEG = {"femur_r": ("LB:SEG:THIGH_R", "LB:FRAME:GAIT2392_FEMUR_R"),
            "tibia_r": ("LB:SEG:SHANK_R", "LB:FRAME:GAIT2392_TIBIA_R"),
            "talus_r": ("LB:SEG:FOOT_R", "LB:FRAME:GAIT2392_TALUS_R"),
            "calcn_r": ("LB:SEG:FOOT_R", "LB:FRAME:GAIT2392_CALCN_R"),
            "toes_r": ("LB:SEG:FOOT_R", "LB:FRAME:GAIT2392_TOES_R"),
            "pelvis": ("LB:SEG:PELVIS", "LB:FRAME:GAIT2392_PELVIS"),
            "torso": ("LB:SEG:TORSO", "LB:FRAME:GAIT2392_TORSO")}
# joint -> (parent body frame, ontology joint, frame entity)
JOINTS = {"hip_r": ("LB:JOINT:HIP_R", "LB:FRAME:GAIT2392_PELVIS"),
          "ankle_r": ("LB:JOINT:ANKLE_R", "LB:FRAME:GAIT2392_TIBIA_R"),
          "subtalar_r": ("LB:JOINT:SUBTALAR_R", "LB:FRAME:GAIT2392_TALUS_R"),
          "mtp_r": ("LB:JOINT:MTP_R", "LB:FRAME:GAIT2392_CALCN_R"),
          "back": ("LB:JOINT:LUMBAR_GAIT2392", "LB:FRAME:GAIT2392_PELVIS")}


def _onto():
    """The ontology (the schema's modules, relationship additions applied), read once."""
    global _ONTOLOGY
    if _ONTOLOGY is None:
        _ONTOLOGY = default_ontology()   # the modules the schema names (D-063 Amendment 1)
    return _ONTOLOGY


_ONTOLOGY = None


def _joint_target(entity, jname):
    """Target of a joint-location record; a joint that is itself a model element (class ModelJoint) is also named
    in model_entity_id (LB-QPS 0.9.0). Anatomical joints have no separate model-joint entity."""
    target = {"entity_ids": [entity], "anatomical_scope": f"Gait2392 joint '{jname}'", "laterality": None,
              "computational_representation": f"OpenSim Gait2392 joint '{jname}'"}
    if _onto().get(entity).get("class") == "ModelJoint":
        target["model_entity_id"] = entity
    return target


def _claim(location, supports, notes=None):
    c = {"source_id": "SRC:GAIT2392_OSIM", "supports": supports, "evidence_domain": "computational_model",
         "claim_scope": location, "value_directly_reported": True}
    if notes:
        c["notes"] = notes
    return c


def _interp(xs, ys, x):
    for (x0, y0), (x1, y1) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):
        if x0 <= x <= x1:
            return y0 + (x - x0) * (y1 - y0) / (x1 - x0), (x0, y0, x1, y1)
    raise ValueError("outside spline knots")


def gait2392():
    root = ET.parse(OSIM).getroot()
    bodies = {b.get("name"): b for b in root.iter("Body")}
    obs = {}
    for body, (seg, frame) in BODY_SEG.items():
        b = bodies[body]
        key = body.upper()
        target = {"entity_ids": [seg], "anatomical_scope": f"Gait2392 body '{body}'", "laterality": None,
                  "computational_representation": f"OpenSim Gait2392 body '{body}'",
                  "model_entity_id": _onto().entity_for_model_element("gait2392", body)}
        assert target["model_entity_id"] == frame, body
        loc = f"gait2392_millard2012muscle.osim, BodySet/{body}"
        obs[f"LB-QD:G2392:{key}:MASS"] = datum(
            "mass", f"Mass of Gait2392 body '{body}'.", _num(b.findtext("mass")), "kg", "model_derived",
            [_claim(f"{loc}/mass", [f"{body}_mass"])], f"{loc}/mass", target, G_APPLICABILITY,
            derivation={"inputs": [], "formula": "published model parameter", "assumptions": []})
        obs[f"LB-QD:G2392:{key}:COM"] = datum(
            "center_of_mass_position", f"Centre of mass of '{body}' in its own body frame.",
            [_num(v) for v in _vec(b.findtext("mass_center"))], "m", "model_derived",
            [_claim(f"{loc}/mass_center", [f"{body}_mass_center"])], f"{loc}/mass_center", target,
            G_APPLICABILITY, value_form="vector", frame=frame,
            derivation={"inputs": [], "formula": "published model parameter", "assumptions": []})
        i = _vec(b.findtext("inertia"))  # Ixx Iyy Izz Ixy Ixz Iyz about the centre of mass
        tensor = [[i[0], i[3], i[4]], [i[3], i[1], i[5]], [i[4], i[5], i[2]]]
        obs[f"LB-QD:G2392:{key}:INERTIA"] = datum(
            "inertia_tensor", f"Inertia tensor of '{body}' about its centre of mass, in its body frame.",
            [[_num(v) for v in row] for row in tensor], "kg*m^2", "model_derived",
            [_claim(f"{loc}/inertia", [f"{body}_inertia"],
                    "OpenSim order Ixx Iyy Izz Ixy Ixz Iyz, arranged as a symmetric 3x3 tensor")],
            f"{loc}/inertia", target, G_APPLICABILITY, value_form="tensor", frame=frame,
            derivation={"inputs": [], "formula": "published model parameter", "assumptions": []})
    joints = {j.get("name"): j for j in root.iter("CustomJoint")}
    for jname, (entity, frame) in JOINTS.items():
        j = joints[jname]
        parent = [f for f in j.iter("PhysicalOffsetFrame") if f.get("name") == j.findtext("socket_parent_frame")][0]
        loc = f"gait2392_millard2012muscle.osim, JointSet/{jname}/frames/{parent.get('name')}/translation"
        obs[f"LB-QD:G2392:JOINT:{jname.upper()}"] = datum(
            "joint_center_position", f"Location of Gait2392 joint '{jname}' in the parent body frame.",
            [_num(v) for v in _vec(parent.findtext("translation"))], "m", "model_derived",
            [_claim(loc, [f"{jname}_location_in_parent"])], loc,
            _joint_target(entity, jname),
            G_APPLICABILITY, value_form="vector", frame=frame,
            derivation={"inputs": [], "formula": "published model parameter", "assumptions": []})
    # Knee: Gait2392 moves the tibia along splines of knee angle. D1 fixes the knee centre at the
    # location for knee angle zero, found by linear interpolation between the neighbouring knots.
    knee = joints["knee_r"]
    value, steps = [], []
    for axis_name in ("translation1", "translation2"):
        ta = [t for t in knee.iter("TransformAxis") if t.get("name") == axis_name][0]
        xs, ys = _vec(ta.find(".//SimmSpline/x").text), _vec(ta.find(".//SimmSpline/y").text)
        y0, (a, fa, b, fb) = _interp(xs, ys, 0.0)
        value.append(y0)
        steps.append({"operation": "linear_interpolation", "input_value": None, "input_unit": "m",
                      "output_value": y0, "output_unit": "m",
                      "formula": f"{axis_name}: knots ({a}, {fa}) and ({b}, {fb}) evaluated at knee_angle_r = 0"})
    value.append(0.0)
    steps.append({"operation": "assemble_vector", "input_value": None, "input_unit": "m",
                  "output_value": value, "output_unit": "m",
                  "formula": "[translation1(0), translation2(0), 0]; translation3 is the constant 0"})
    loc = "gait2392_millard2012muscle.osim, JointSet/knee_r/SpatialTransform/translation1 and translation2 (SimmSpline)"
    obs["LB-QD:G2392:JOINT:KNEE_R"] = datum(
        "joint_center_position",
        "Knee centre (tibia origin) in the femur frame at knee angle zero, held fixed in Stage D1.",
        value, "m", "calculated",
        [{"source_id": "SRC:GAIT2392_OSIM", "supports": ["knee_r_translation_spline_knots"],
          "evidence_domain": "computational_model", "claim_scope": loc, "value_directly_reported": False,
          "notes": "The model gives spline knots, not this value; the value is interpolated (see history)."}],
        loc, {"entity_ids": ["LB:JOINT:KNEE_R"], "anatomical_scope": "Gait2392 joint 'knee_r'", "laterality": None,
              "computational_representation": "OpenSim Gait2392 joint 'knee_r' at knee angle 0"},
        G_APPLICABILITY, value_form="vector", frame="LB:FRAME:GAIT2392_FEMUR_R", history=steps,
        derivation={"inputs": [], "formula": "linear interpolation of the knee translation spline knots at 0 rad",
                    "assumptions": ["OpenSim evaluates these splines as smooth curves; linear interpolation between the "
                                    "two knots next to 0 differs from it by well under 1 mm here",
                                    "Stage D1 holds the knee centre fixed at this location for all knee angles"]})
    # Moving knee (D-060): the same splines, kept as functions of the knee angle for Stage D3.
    spl = {}
    for axis_name in ("translation1", "translation2"):
        ta = [t for t in knee.iter("TransformAxis") if t.get("name") == axis_name][0]
        spl[axis_name] = {"kind": "simm_spline", "x": _vec(ta.find(".//SimmSpline/x").text),
                          "y": _vec(ta.find(".//SimmSpline/y").text)}
    d = datum(
        "joint_center_position",
        "Knee centre (tibia origin) in the femur frame as a function of the Gait2392 knee angle (Stage D3).",
        {"kind": "moving_joint_centre",
         "coordinate": "Gait2392 knee_angle_r (rad, flexion negative) = -LB:DOF:KNEE_FLEX_EXT_R",
         "x": spl["translation1"], "y": spl["translation2"], "z": {"kind": "constant", "value": 0.0},
         "evaluation": "OpenSim SimmSpline (opensim-core 01683ac, OpenSim/Common/SimmSpline.cpp)"},
        "m", "model_derived",
        [_claim(loc, ["knee_r_translation_spline_knots"])], loc,
        {"entity_ids": ["LB:JOINT:KNEE_R"], "anatomical_scope": "Gait2392 joint 'knee_r'", "laterality": None,
         "computational_representation": "OpenSim Gait2392 joint 'knee_r', translation coupled to the knee angle"},
        G_APPLICABILITY, value_form="function", frame="LB:FRAME:GAIT2392_FEMUR_R",
        derivation={"inputs": [], "formula": "published model knee translation splines", "assumptions": [
            "A one-coordinate model coupling (Gait2392), not measured knee motion (D-060 simplification 1)"]})
    d["coordinate_context"]["coordinate_id"] = "LB:DOF:KNEE_FLEX_EXT_R"
    obs["LB-QD:G2392:JOINT:KNEE_R_MOVING"] = d
    doc = "OpenSim documentation, 'Gait 2392 and 2354 Models'"
    whole = {"entity_ids": ["LB:BODY:WHOLE"], "anatomical_scope": "whole body", "laterality": None,
             "computational_representation": "unscaled Gait2392 model"}
    for key, prop, val, unit, quote in (
            ("BODY_MASS", "body_mass", 75.16, "kg", "has a mass of 75.16 kg"),
            ("STATURE", "stature", 1.8, "m", "about 1.8 m tall")):
        obs[f"LB-QD:G2392:{key}"] = datum(
            prop, f"Documented {prop.replace('_', ' ')} of the unscaled Gait2392 model.", val, unit, "model_derived",
            [{"source_id": "SRC:OPENSIM_GAIT2392", "supports": [f"gait2392_{prop}"], "evidence_domain": "computational_model",
              "claim_scope": doc, "value_directly_reported": True, "notes": f"Quoted: '{quote}'."}],
            doc, whole, G_APPLICABILITY,
            derivation={"inputs": [], "formula": "documented model value", "assumptions": []},
            notes=("The documentation says 'about 1.8 m'. A user measured the model's default geometry at about "
                   "1.66 m (SimTK forum, unanswered). D-058 Amendment 2 uses 1.8 m and lists this as an open concern.")
            if key == "STATURE" else None)
    return {
        "dataset": {"id": "LB-QD:SEGMENTS:GAIT2392", "version": "0.3.0",
                    "description": ("OpenSim Gait2392 body segment parameters and joint locations (reference body and scaling "
                                    "basis for Stage D1); moving-knee splines for Stage D3 (0.2.0, D-060); "
                                    "model_entity_id on body and model-joint records (0.3.0, D-062 item 4)."),
                    "generated_by": "python -m tools.build_segment_datasets",
                    "decision": "D-058"},
        "sources": {
            "SRC:GAIT2392_OSIM": {
                "title": "OpenSim Gait2392 model file (gait2392_millard2012muscle.osim)",
                "citation": ("opensim-org/opensim-models, Models/Gait2392_Simbody/gait2392_millard2012muscle.osim, "
                             f"commit {OSIM_COMMIT}. Credits: Delp, Loan, Hoy, Zajac, Topp, Rosen, Thelen, Anderson, Seth. CC BY 3.0."),
                "url": "https://github.com/opensim-org/opensim-models/blob/master/Models/Gait2392_Simbody/gait2392_millard2012muscle.osim",
                "local_copy": "sources/vendor/opensim-models/gait2392_millard2012muscle.osim",
                "evidence_domain": "computational_model", "role": "model_parameter_source"}},
        "observations": obs,
    }


# ---------------------------------------------------------------------- de Leva
DL_ROWS = {  # BMC row name -> (segment entities, endpoint description)
    "Head": (["LB:SEG:HEAD"], "VERT-MIDG (vertex to mid-gonion)"),
    "Trunk": (["LB:SEG:TRUNK_DELEVA"], "SUPR-MIDH (suprasternale to mid-hip)"),
    "Upper arm": (["LB:SEG:UPPER_ARM_R", "LB:SEG:UPPER_ARM_L"], "SJC-EJC (shoulder to elbow joint centre)"),
    "Forearm": (["LB:SEG:FOREARM_R", "LB:SEG:FOREARM_L"], "EJC-WJC (elbow to wrist joint centre)"),
    "Hand": (["LB:SEG:HAND_R", "LB:SEG:HAND_L"], "WJC-MET3 (wrist joint centre to third metacarpale)"),
    "Thigh": (["LB:SEG:THIGH_R", "LB:SEG:THIGH_L"], "HJC-KJC (hip to knee joint centre)"),
    "Shank": (["LB:SEG:SHANK_R", "LB:SEG:SHANK_L"], "KJC-AJC (knee to ankle joint centre)"),
    "Foot": (["LB:SEG:FOOT_R", "LB:SEG:FOOT_L"], "HEEL-TTIP (pternion to acropodion)"),
}
LENGTH_FRACTIONS = ("Thigh", "Shank")  # the only rows whose COM and radius fractions D1 consumes
# Reference body sizes, from the caption of de Leva's Table 4 (see notes in the claims).
DL_BODY = {"female": (61.9, 1.735), "male": (73.0, 1.741)}


def read_bmc(path):
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        cells = [c.strip() for c in line.split("\t")]
        if len(cells) == 7:
            rows[cells[0]] = {"endpoints": cells[1], "mass": cells[2], "com": cells[3],
                              "rg_sag": cells[4], "rg_trans": cells[5], "rg_long": cells[6]}
    return rows


def de_leva():
    obs = {}
    for sex, path in BMC.items():
        rows = read_bmc(path)
        S = sex[0].upper()
        appl = {"level": "cohort", "sex": sex,
                "population": ("Young adult sample of Zatsiorsky and Seluyanov, as adjusted by de Leva (1996); "
                               "sample details not transcribed."),
                "model_id": None}
        for name, (entities, endpoints) in DL_ROWS.items():
            row = rows[name]
            key = name.upper().replace(" ", "_")
            target = {"entity_ids": entities, "anatomical_scope": f"de Leva segment '{name}'",
                      "laterality": "shared_bilateral_baseline" if len(entities) == 2 else None,
                      "computational_representation": f"de Leva 1996 Table 4 row '{name}', endpoints {endpoints}"}
            fields = [("mass_fraction", "mass", "Rg")]
            if name in LENGTH_FRACTIONS:
                fields += [("center_of_mass_fraction", "com", None), ("radius_of_gyration_fraction", "rg_trans", None)]
            for prop, col, _ in fields:
                label = {"mass": "Mass", "com": "CM Long", "rg_trans": "Rg Trans"}[col]
                loc = f"{path.name}, row '{name}', column '{label}'"
                claims = [
                    {"source_id": "SRC:DE_LEVA_1996", "supports": [f"{key.lower()}_{prop}_{sex}"],
                     "evidence_domain": "anthropometry", "claim_scope": f"Table 4, {name} ({endpoints}), {sex}",
                     "value_directly_reported": True,
                     "notes": "Read from the reproduction SRC:BMC_DELEVA_DATA; not checked against the paper (D-058 Amendment 2)."},
                    {"source_id": "SRC:BMC_DELEVA_DATA", "supports": [f"{key.lower()}_{prop}_{sex}"],
                     "evidence_domain": "anthropometry", "claim_scope": loc, "value_directly_reported": True}]
                definition = {"mass_fraction": f"de Leva {sex} {name} mass as a fraction of body mass.",
                              "center_of_mass_fraction": f"de Leva {sex} {name} centre of mass from the first endpoint, as a fraction of segment length.",
                              "radius_of_gyration_fraction": f"de Leva {sex} {name} radius of gyration for rotation in the sagittal plane, as a fraction of segment length."}[prop]
                notes = None
                if prop == "radius_of_gyration_fraction":
                    notes = (f"Interpretation (D-058 Amendment 2): de Leva's 'transverse' radius (about the transverse, i.e. "
                             f"mediolateral, axis) is taken as the radius for rotation in the sagittal plane. The 'sagittal' "
                             f"column of the same row is {row['rg_sag']}. The paper's own axis definitions were not checked.")
                obs[f"LB-QD:DELEVA:{S}:{key}:{prop.upper()}"] = datum(
                    prop, definition, float(row[col]), "1", "literature_derived", claims, loc, target, appl,
                    notes=notes)
        mass, stature = DL_BODY[sex]
        whole = {"entity_ids": ["LB:BODY:WHOLE"], "anatomical_scope": "whole body", "laterality": None,
                 "computational_representation": f"de Leva 1996 {sex} reference body"}
        corroboration = ("Also given as the 'standard female' (1735 mm, 61.9 kg) in the SimTK lab handout "
                         "SRC:SIMTK_BSP_LAB, which cites de Leva 1996.") if sex == "female" else (
                         "Single machine reading of the caption; no second reading found (D-058 Amendment 2, open concern).")
        for prop, val, unit in (("body_mass", mass, "kg"), ("stature", stature, "m")):
            claims = [{"source_id": "SRC:DE_LEVA_1996", "supports": [f"{sex}_reference_{prop}"],
                       "evidence_domain": "anthropometry", "claim_scope": "Table 4 caption",
                       "value_directly_reported": True,
                       "notes": "Read through a machine text extraction of a PDF copy of the paper. " + corroboration}]
            if sex == "female":
                claims.append({"source_id": "SRC:SIMTK_BSP_LAB", "supports": [f"{sex}_reference_{prop}"],
                               "evidence_domain": "anthropometry", "claim_scope": "results table, standard female",
                               "value_directly_reported": True})
            obs[f"LB-QD:DELEVA:{S}:{prop.upper()}"] = datum(
                prop, f"Reference {sex} {prop.replace('_', ' ')} for which de Leva's Table 4 is given.", val, unit,
                "literature_derived", claims, "de Leva 1996, Table 4 caption", whole, appl)
    return {
        "dataset": {"id": "LB-QD:SEGMENTS:DE_LEVA_1996", "version": "0.1.0",
                    "description": "de Leva (1996) segment fractions and reference body sizes, female and male (Stage D1).",
                    "generated_by": "python -m tools.build_segment_datasets",
                    "decision": "D-058",
                    "bilateral_policy": {"assumption": "symmetric_baseline",
                                         "rationale": "de Leva gives one value per limb segment; it initializes both sides.",
                                         "anatomical_fact": False,
                                         "shared_baseline_targets": sorted({e for v in DL_ROWS.values() for e in v[0] if e[-2:] in ("_R", "_L")}),
                                         "independent_override_supported": True}},
        "sources": {
            "SRC:DE_LEVA_1996": {
                "title": "Adjustments to Zatsiorsky-Seluyanov's segment inertia parameters",
                "citation": "de Leva P. Journal of Biomechanics. 1996;29(9):1223-1230.",
                "url": "https://ebm.ufabc.edu.br/wp-content/uploads/2013/12/Leva-1996.pdf",
                "evidence_domain": "anthropometry", "role": "primary_anthropometric_source"},
            "SRC:BMC_DELEVA_DATA": {
                "title": "BSPfemale_ZdeLeva.txt and BSPmale_ZdeLeva.txt (reproduction of de Leva 1996 Table 4)",
                "citation": (f"Duarte M. Notes on Scientific Computing for Biomechanics and Motor Control (BMC), BMClab/BMC, "
                             f"data/BSPfemale_ZdeLeva.txt and data/BSPmale_ZdeLeva.txt, commit {BMC_COMMIT}. CC BY 4.0."),
                "url": "https://github.com/BMClab/BMC/tree/master/data",
                "local_copy": "sources/vendor/bmc/",
                "evidence_domain": "anthropometry", "role": "secondary_machine_readable_reproduction"},
            "SRC:SIMTK_BSP_LAB": {
                "title": "4.5 Lab: Human body segments mass properties",
                "citation": "SimTK document, 'Lab 4: Mass distribution of rigid bodies in Simbody' (author not stated).",
                "url": "https://simtk.org/docman/view.php/199/632/handwrittenPartLabHumanBodySegment.pdf",
                "evidence_domain": "anthropometry", "role": "corroborating_secondary_source"}},
        "observations": obs,
    }


# ---------------------------------------------------------------------- muscles (D-059)
# Gait2392 actuator -> (anatomical muscle entity, part of the muscle it represents)
def model_actuators():
    """Actuators named by the ontology's model views and specifications, in order of first appearance (D-062 item 4):
    `represents` of a view (squat_d2) and `actuators` of an executable specification (squat_d4 and its extensions).
    Returns {model element name: actuator entity ID}."""
    onto, out = _onto(), {}
    for spec in onto.data["models"].values():
        for eid in list(spec.get("represents") or []) + list(spec.get("actuators") or []) + list(spec.get("add_actuators") or []):
            if onto.get(eid).get("class") == "ModelActuator":
                model, name = onto.model_element(eid)
                if model == "gait2392":
                    out.setdefault(name, eid)
    return out


def _coordinate_text(osim_coordinate_path):
    """Map an OpenSim coordinate path to (ontology coordinate ID, prose) through the coordinates' model_coordinates."""
    name = osim_coordinate_path.split("/")[-1]
    onto = _onto()
    hits = [(eid, m["sign"]) for eid, e in onto.entities.items() for m in e.get("model_coordinates", [])
            if m["model"] == "gait2392" and m["coordinate"] == name]
    if len(hits) != 1:
        raise ValueError(f"{len(hits)} ontology coordinates map to Gait2392 coordinate {name}")
    dof, sign = hits[0]
    word = onto.get(dof)["positive_motion"].split("_", 1)[1]
    return dof, (f"Gait2392 {name} (rad, {word} {'negative' if sign < 0 else 'positive'}) = "
                 f"{'-' if sign < 0 else ''}{dof}")
FMAX_DOC = ("OpenSim documentation (version 2.4), 'Gait 2392 Max Isometric Muscle Force': Delp's (1990) values, scaled "
            "upward using Anderson and Pandy (1999) and Carhart (2000, reported in Yamaguchi 2001), not by one uniform "
            "factor (D-059 item 4).")
PARAMS = (  # XML element, property, unit, definition text
    ("max_isometric_force", "maximum_isometric_force", "N",
     "Gait2392 maximum isometric force of '{a}', read as maximum fiber force (D-056)."),
    ("optimal_fiber_length", "optimal_fiber_length", "m", "Gait2392 optimal fiber length of '{a}'."),
    ("tendon_slack_length", "tendon_slack_length", "m", "Gait2392 tendon slack length of '{a}'."),
    ("pennation_angle_at_optimal", "pennation_angle_at_optimal", "rad",
     "Gait2392 pennation angle of '{a}' at optimal fiber length."),
    ("max_contraction_velocity", "maximum_contraction_velocity", "optimal_fiber_lengths/s",
     "Gait2392 maximum contraction velocity of '{a}', in its own optimal fiber lengths per second."),
)


def _function(element):
    """A coordinate function from the model file: SimmSpline knots, or a constant."""
    f = element[0]
    if f.tag == "SimmSpline":
        return {"kind": "simm_spline", "x": _vec(f.findtext("x")), "y": _vec(f.findtext("y"))}
    if f.tag == "Constant":
        return {"kind": "constant", "value": float(f.findtext("value"))}
    raise ValueError(f"unsupported path-point function {f.tag}")


def muscles():
    root = ET.parse(OSIM).getroot()
    found = {m.get("name"): m for m in root.iter("Millard2012EquilibriumMuscle")}
    obs = {}
    for name, actuator in model_actuators().items():
        m = found[name]
        key = name.upper()
        a = _onto().get(actuator)
        reps = a["represents"] if isinstance(a["represents"], list) else [a["represents"]]   # lumped (D-063 item 5)
        target = {"entity_ids": list(reps), "anatomical_scope": a["represented_scope"], "laterality": a["side"],
                  "computational_representation": f"OpenSim Gait2392 actuator '{name}' ({actuator})",
                  "model_entity_id": actuator}
        base = f"gait2392_millard2012muscle.osim, ForceSet/{name}"
        for element, prop, unit, text in PARAMS:
            loc = f"{base}/{element}"
            claims = [_claim(loc, [f"{name}_{element}"])]
            if prop == "maximum_isometric_force":
                claims.append({"source_id": "SRC:OPENSIM24_GAIT2392_FMAX", "supports": ["provenance_of_gait2392_forces"],
                               "evidence_domain": "computational_model", "claim_scope": FMAX_DOC,
                               "value_directly_reported": False})
            d = datum(prop, text.format(a=name), float(m.findtext(element)), unit, "model_derived", claims, loc,
                      target, G_APPLICABILITY,
                      derivation={"inputs": [], "formula": "published model parameter", "assumptions": []})
            if prop == "maximum_contraction_velocity":
                d["normalization"] = {"length_property": "optimal_fiber_length",
                                      "reference_observation": f"LB-QD:G2392:MUS:{key}:OPTIMAL_FIBER_LENGTH",
                                      "basis": "OpenSim defines max_contraction_velocity in optimal fiber lengths per second"}
            obs[f"LB-QD:G2392:MUS:{key}:{prop.upper()}"] = d
        points = list(m.find(".//PathPointSet/objects"))
        for k, p in enumerate(points, 1):
            frame_name = p.findtext("socket_parent_frame").split("/")[-1]
            frame_entity = _onto().entity_for_model_element("gait2392", frame_name)
            loc = f"{base}/GeometryPath/PathPointSet/{p.get('name')}"
            ctx_coord = None
            if p.tag == "PathPoint":
                value, form = _vec(p.findtext("location")), "vector"
                text = f"Fixed path point {k} of {len(points)} of '{name}' in the '{frame_name}' frame."
            elif p.tag == "ConditionalPathPoint":
                ctx_coord, coord_text = _coordinate_text(p.findtext("socket_coordinate"))
                coord_name = p.findtext("socket_coordinate").split("/")[-1]
                lo, hi = _vec(p.findtext("range"))
                value = {"kind": "conditional", "location": _vec(p.findtext("location")),
                         "coordinate": coord_text,
                         "active_range": [lo, hi],
                         "activity_rule": f"active when lo - 1e-5 <= {coord_name} <= hi + 1e-5 (OpenSim "
                                          "ConditionalPathPoint::isActive at opensim-core 01683ac)"}
                form = "function"
                text = f"Conditional path point {k} of {len(points)} of '{name}' in the '{frame_name}' frame."
            elif p.tag == "MovingPathPoint":
                coords = {p.findtext(f"socket_{ax}_coordinate") for ax in "xyz"}
                if len(coords) != 1:
                    raise ValueError(f"{name}: a moving point driven by several coordinates is not supported")
                ctx_coord, coord_text = _coordinate_text(coords.pop())
                value = {"kind": "moving",
                         "coordinate": coord_text,
                         **{ax: _function(p.find(f"{ax}_location")) for ax in "xyz"},
                         "evaluation": "OpenSim SimmSpline (opensim-core 01683ac, OpenSim/Common/SimmSpline.cpp)"}
                form = "function"
                text = f"Moving path point {k} of {len(points)} of '{name}' in the '{frame_name}' frame."
            else:
                raise ValueError(p.tag)
            d = datum("attachment_position", text, value, "m", "model_derived", [_claim(loc, [f"{p.get('name')}"])],
                      loc, target, G_APPLICABILITY, value_form=form, frame=frame_entity,
                      derivation={"inputs": [], "formula": "published model path point", "assumptions": []})
            d["coordinate_context"]["coordinate_id"] = ctx_coord
            obs[f"LB-QD:G2392:MUS:{key}:PATH:{k:02d}"] = d
    return {
        "dataset": {"id": "LB-QD:MUSCLES:GAIT2392", "version": "0.4.0",
                    "description": (f"OpenSim Gait2392 parameters and path points of the {len(model_actuators())} "
                                    "actuators named by the ontology's model views and specifications (D-059 item 4; "
                                    "list read from the ontology and model_entity_id added, 0.2.0, D-062 item 4; "
                                    "iliacus and psoas added for the growth test, 0.3.0, D-062 item 8; the 27 further "
                                    "actuators of squat_d5, 0.4.0, D-063 item 3)."),
                    "generated_by": "python -m tools.build_segment_datasets",
                    "decision": "D-059, D-062, D-063"},
        "sources": {
            "SRC:GAIT2392_OSIM": gait2392()["sources"]["SRC:GAIT2392_OSIM"],
            "SRC:OPENSIM24_GAIT2392_FMAX": {
                "title": "Gait 2392 Max Isometric Muscle Force (OpenSim documentation, version 2.4)",
                "citation": "OpenSim Confluence, OpenSim24 space; comment by S. Hamner (2008).",
                "url": "https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim24/pages/54001706/Gait+2392+Max+Isometric+Muscle+Force",
                "evidence_domain": "computational_model", "role": "provenance_documentation"}},
        "observations": obs,
    }


DATASETS = {"segments_gait2392.yaml": gait2392, "segments_de_leva_1996.yaml": de_leva,
            "muscles_gait2392.yaml": muscles}
HEADER = "# GENERATED by `python -m tools.build_segment_datasets` from sources/vendor/. Do not edit by hand.\n"


def render(builder):
    return HEADER + yaml.safe_dump(builder(), sort_keys=False, allow_unicode=True, width=120)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if a committed dataset differs")
    args = parser.parse_args()
    stale = []
    for name, builder in DATASETS.items():
        text, path = render(builder), OUT / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(name)
        else:
            path.write_text(text, encoding="utf-8")
            print("wrote", path.relative_to(ROOT))
    if stale:
        print("out of date:", ", ".join(stale))
        sys.exit(1)


if __name__ == "__main__":
    main()
