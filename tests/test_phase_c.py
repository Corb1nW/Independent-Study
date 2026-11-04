"""Phase C (D-055): shared run manifest (C1), velocity normalization (C3),
traceability gate (C4) and the growth test (C5)."""
from copy import deepcopy
from hashlib import sha256
import shutil
import subprocess

import pytest
import yaml

from src import run_manifest as rm
from src.hip_phase_b import ROOT, resolve_inputs, simulate, run_manifest
from src.input_gate import SCOPE_LIMIT, check_input, require_traceable, traceability_report
from src.integrity import check_project
from src.quantitative import QuantitativeSchema

SCHEMA_PATH = ROOT / "ontology" / "quantitative_schema.yaml"
DATA = ROOT / "ontology" / "quantitative_data" / "gluteus_maximus.yaml"
CONFIG = ROOT / "config" / "phase_b_hip.yaml"
BASELINE = ROOT / "config" / "phase_b_scenario_baseline.yaml"
PERTURBED = ROOT / "config" / "phase_b_scenario_perturbed.yaml"
FMAX = "LB-QD:GMAX:FMAX:ARNOLD2010"
VELOCITY = "LB-QD:GMAX:MAX_CONTRACTION_VELOCITY"
FIBER_LENGTH = "LB-QD:GMAX:OPTIMAL_FIBER_LENGTH:WARD2009"


@pytest.fixture(scope="module")
def schema():
    return QuantitativeSchema(SCHEMA_PATH)


@pytest.fixture()
def dataset(schema):
    return schema.load_dataset(DATA)


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                          text=True).stdout.strip()


def _repo(tmp_path, content=b"moment_arm_m: 0.04\n"):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Test")
    (root / ".gitattributes").write_text("*.yaml text\n", encoding="utf-8")
    target = root / "config.yaml"
    target.write_bytes(content)
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "fixture")
    return root, target, _git(root, "rev-parse", "HEAD")


# ----------------------------------------------------------------- C1 manifest
def test_c1_records_git_blob_id_of_head(tmp_path):
    root, target, sha = _repo(tmp_path)
    status, records = rm.verify_inputs(root, {"config": target}, sha)
    assert status == rm.VERIFIED
    assert records["config"]["path"] == "config.yaml"
    assert records["config"]["git_blob_id"] == _git(root, "rev-parse", "HEAD:config.yaml")
    assert records["config"]["sha256"] == sha256(target.read_bytes()).hexdigest()


def test_c1_blob_id_is_platform_independent_raw_hash_is_not(tmp_path):
    """N4: a CRLF (Windows-style) checkout of the same commit keeps the blob ID."""
    root, target, sha = _repo(tmp_path)
    _, lf = rm.verify_inputs(root, {"config": target}, sha)
    _git(root, "config", "core.autocrlf", "true")
    target.write_bytes(b"moment_arm_m: 0.04\r\n")
    status, crlf = rm.verify_inputs(root, {"config": target}, sha)
    assert status == rm.VERIFIED
    assert crlf["config"]["git_blob_id"] == lf["config"]["git_blob_id"]
    assert crlf["config"]["sha256"] != lf["config"]["sha256"]


def test_c1_dirty_input_still_rejected(tmp_path):
    root, target, sha = _repo(tmp_path)
    target.write_bytes(b"moment_arm_m: 0.08\n")
    with pytest.raises(ValueError, match="differs from HEAD"):
        rm.verify_inputs(root, {"config": target}, sha)


def test_c1_archive_has_no_blob_ids_and_still_pins_raw_bytes(tmp_path):
    root = tmp_path / "archive"
    root.mkdir()
    target = root / "config.yaml"
    target.write_bytes(b"x: 1\n")
    status, records = rm.verify_inputs(root, {"config": target}, "a" * 40)
    assert status == rm.UNVERIFIED_ARCHIVE
    assert records["config"]["git_blob_id"] is None
    with pytest.raises(ValueError, match="changed since input resolution"):
        rm.verify_inputs(root, {"config": target}, "a" * 40,
                         expected_hashes={"config": "0" * 64})


def test_c1_header_states_validity_and_never_review_state(tmp_path):
    root, target, sha = _repo(tmp_path)
    header = rm.manifest_header(root, {"config": target}, sha)
    assert "status" not in header
    assert header["validity"]["physiological_validity"] == "not established"
    assert header["validity"]["clinical_validity"] == "not established"
    assert "not asserted" in header["validity"]["review_state"]
    assert header["verified_input_files"] == ["config"]
    for bad in ("not-a-sha", "A" * 40, "a" * 39, None):
        with pytest.raises(ValueError, match="40-character"):
            rm.manifest_header(root, {"config": target}, bad)


def test_c1_phase_b_manifest_uses_shared_header():
    sha_process = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True)
    sha = sha_process.stdout.strip() if sha_process.returncode == 0 else "a" * 40
    x = resolve_inputs(CONFIG, BASELINE)
    manifest = run_manifest(x, simulate(x), sha)
    assert "status" not in manifest
    assert "UNREVIEWED" not in rm.serialize_manifest(manifest)
    assert manifest["validity"] == rm.VALIDITY
    assert {"run_manifest", "input_gate", "hip_model", "dataset"} <= set(manifest["inputs"])
    assert manifest["input_traceability"]["passed"] is True
    if manifest["commit_provenance_status"] == rm.VERIFIED:
        for record in manifest["inputs"].values():
            assert len(record["git_blob_id"]) == 40


# ------------------------------------------------- C3 velocity normalization
def _populated_velocity(dataset, normalization="default"):
    d = deepcopy(dataset["observations"][VELOCITY])
    d.update(status="populated", value=10.0)
    d["applicability"]["level"] = "generic_model"
    d["derivation"]["assumptions"] = ["test value"]
    if normalization == "default":
        d["normalization"] = {"length_property": "optimal_fiber_length",
                              "reference_observation": FIBER_LENGTH,
                              "basis": "test"}
    elif normalization is not None:
        d["normalization"] = normalization
    return d


def test_c3_schema_declares_normalizing_length(schema):
    definition = schema.property_definition("maximum_contraction_velocity")
    assert definition["normalization_required"]["length_property"] == "optimal_fiber_length"


def test_c3_valid_normalization_accepted(schema, dataset):
    assert schema.validate_datum(_populated_velocity(dataset), dataset) == []


def test_c3_unpopulated_velocity_needs_no_normalization(schema, dataset):
    assert schema.validate_datum(dataset["observations"][VELOCITY], dataset) == []


@pytest.mark.parametrize("normalization,message", [
    (None, "must declare normalization"),
    ({"length_property": "muscle_length", "reference_observation": FIBER_LENGTH},
     "length_property must be optimal_fiber_length"),
    ({"length_property": "optimal_fiber_length"}, "must name normalization.reference_observation"),
    ({"length_property": "optimal_fiber_length", "reference_observation": "LB-QD:NOPE"},
     "does not exist in the dataset"),
    ({"length_property": "optimal_fiber_length",
      "reference_observation": "LB-QD:GMAX:MUSCLE_LENGTH:WARD2009"}, "not optimal_fiber_length"),
])
def test_c3_bad_normalization_rejected(schema, dataset, normalization, message):
    errors = schema.validate_datum(_populated_velocity(dataset, normalization), dataset)
    assert any(message in e for e in errors), errors


def test_c3_normalization_only_where_defined(schema, dataset):
    d = deepcopy(dataset["observations"][FMAX])
    d["normalization"] = {"length_property": "optimal_fiber_length"}
    assert any("normalization is not defined" in e for e in schema.validate_datum(d, dataset))


def test_c3_unknown_normalization_field_rejected(schema, dataset):
    d = _populated_velocity(dataset)
    d["normalization"]["guess"] = 1
    assert any("structure: normalization.guess" in e for e in schema.validate_datum(d, dataset))


# --------------------------------------------------------- C4 traceability gate
def test_c4_phase_b_input_passes(schema, dataset):
    report = traceability_report(schema, dataset, [FMAX])
    assert report["passed"] is True
    assert report["inputs"][0]["resolved_id"] == FMAX
    assert report["scope_limit"] == SCOPE_LIMIT
    assert "Does not establish that the source supports the value" in SCOPE_LIMIT


def _failures(schema, dataset, oid=FMAX):
    return " | ".join(check_input(schema, dataset, oid)["failures"])


def test_c4_a_unknown_and_ambiguous_ids(schema, dataset):
    assert "(a)" in _failures(schema, dataset, "LB-QD:GMAX:NOPE")
    assert "alias for 2 observations" in _failures(schema, dataset, "LB-QD:GMAX:MOMENT_ARM")


def test_c4_a_invalid_datum(schema, dataset):
    dataset["observations"][FMAX]["value"] = -1.0
    assert "(a) datum fails validation" in _failures(schema, dataset)


def test_c4_b_unresolved_value(schema, dataset):
    assert "(b) no usable value" in _failures(schema, dataset, VELOCITY)


def test_c4_c_unregistered_source_and_empty_supports(schema, dataset):
    claim = dataset["observations"][FMAX]["provenance"]["source_claims"][0]
    claim["source_id"] = "SRC:NOT_REGISTERED"
    assert "(c)" in _failures(schema, dataset)
    claim["source_id"] = "SRC:ARNOLD_2010"
    claim["supports"] = []
    assert "(c)" in _failures(schema, dataset)


def test_c4_d_value_not_tied_to_claim(schema, dataset):
    obs = dataset["observations"][FMAX]
    obs["provenance"]["source_claims"][0]["value_directly_reported"] = False
    obs["provenance"]["transformation_history"][-1]["output_value"] = 1000.0
    assert "(d)" in _failures(schema, dataset)
    obs["provenance"]["transformation_history"][-1]["output_value"] = obs["value"]
    assert "(d)" not in _failures(schema, dataset)  # traced through the history instead
    obs["provenance"]["transformation_history"][-1]["output_unit"] = "kN"
    assert "(d)" in _failures(schema, dataset)


def test_c4_e_applicability(schema, dataset):
    obs = dataset["observations"][FMAX]
    obs["applicability"]["model_id"] = None
    assert "(e) model_derived datum without applicability.model_id" in _failures(schema, dataset)
    obs["applicability"]["level"] = None
    assert "(e) applicability.level not declared" in _failures(schema, dataset)


def test_c4_require_traceable_raises_with_every_failure(schema, dataset):
    with pytest.raises(ValueError, match="input traceability gate failed") as exc:
        require_traceable(schema, dataset, [FMAX, VELOCITY, "LB-QD:GMAX:NOPE"])
    assert VELOCITY in str(exc.value) and "LB-QD:GMAX:NOPE" in str(exc.value)
    with pytest.raises(ValueError):
        require_traceable(schema, dataset, [])


# ------------------------------------------------------------- C5 growth test
# Updated in Stage D1 (D-058): the knee now exists in ontology/lower_limb_sagittal.yaml, so
# growth is tested the way the project now grows, by adding a further module file.
STUB_ENTITIES = {
    "LB:BONE:PATELLA_R": {"name": "Right Patella (growth-test stub)", "class": "Bone", "side": "right"},
    "LB:JOINT:PATELLOFEMORAL_R": {"name": "Right Patellofemoral Joint (growth-test stub)",
                                  "class": "SynovialPlaneJoint", "side": "right",
                                  "relationships": {"CONNECTS": ["LB:BONE:FEMUR_R", "LB:BONE:PATELLA_R"]}},
}
STUB = "growth_stub.yaml"


def _grow(tmp_path, entities=None):
    """Copy the data the project reads into a temporary root and add a stub module file.

    The stub is a fixture for testing growth, not anatomy entered into the project:
    names are marked as stubs, no evidence is attached and nothing is written back.
    """
    root = tmp_path / "grown"
    for folder in ("ontology", "config"):
        shutil.copytree(ROOT / folder, root / folder)
    original = deepcopy(QuantitativeSchema(ROOT / "ontology" / "quantitative_schema.yaml").ontology.entities)
    stub = {"ontology_module": {"extends": "LB-AO", "module": "growth_stub"},
            "class_hierarchy": {"SynovialPlaneJoint": "SynovialJoint"},
            "entities": deepcopy(entities or STUB_ENTITIES)}
    assert not set(stub["entities"]) & set(original)
    (root / "ontology" / STUB).write_text(yaml.safe_dump(stub, sort_keys=False), encoding="utf-8")
    schema_path = root / "ontology" / "quantitative_schema.yaml"
    schema_data = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    schema_data["ontology"] = list(schema_data["ontology"]) + [STUB]
    schema_path.write_text(yaml.safe_dump(schema_data, sort_keys=False), encoding="utf-8")
    # A cross-file reference from the original module to the new one.
    hip = root / "ontology" / "hip.yaml"
    onto = yaml.safe_load(hip.read_text(encoding="utf-8"))
    rf = onto["entities"]["LB:MUS:RECTUS_FEMORIS_R"]["relationships"]
    rf["CROSSES"] = rf["CROSSES"] + ["LB:JOINT:PATELLOFEMORAL_R"]
    hip.write_text(yaml.safe_dump(onto, sort_keys=False), encoding="utf-8")
    return root, original


def test_c5_growth_keeps_ids_evidence_and_validation(tmp_path, schema):
    root, original = _grow(tmp_path)
    assert check_project(root) == []
    grown = QuantitativeSchema(root / "ontology" / "quantitative_schema.yaml")
    for eid, entity in original.items():  # every existing ID survives
        assert eid in grown.ontology.entities
        if eid != "LB:MUS:RECTUS_FEMORIS_R":
            assert grown.ontology.get(eid) == entity
    crossing = [e for e, _ in grown.ontology.muscles_crossing("LB:JOINT:PATELLOFEMORAL_R")]
    assert crossing == ["LB:MUS:RECTUS_FEMORIS_R"]
    # Joint properties reach the new joint through the class hierarchy (D-031).
    assert grown.property_applies_to_entity("range_of_motion", "LB:JOINT:PATELLOFEMORAL_R")
    # Existing observations, aliases and the evidence gate are unchanged.
    old = schema.load_dataset(DATA)
    new = grown.load_dataset(root / "ontology" / "quantitative_data" / "gluteus_maximus.yaml")
    assert new == old
    for alias in old["observation_aliases"]:
        assert grown.resolve_observation_ids(new, alias) == schema.resolve_observation_ids(old, alias)
    assert traceability_report(grown, new, [FMAX])["passed"]


def test_c5_growth_leaves_phase_b_results_unchanged(tmp_path):
    root, _ = _grow(tmp_path)
    for scenario in (BASELINE, PERTURBED):
        before = resolve_inputs(CONFIG, scenario)
        after = resolve_inputs(root / "config" / CONFIG.name, root / "config" / scenario.name,
                               root=root)
        assert after["right_fmax_N"] == before["right_fmax_N"]
        assert simulate(after) == simulate(before)


def test_c5_growth_test_would_catch_a_broken_reference(tmp_path):
    """Negative control: a stub that references a missing entity must fail loading."""
    broken = deepcopy(STUB_ENTITIES)
    broken["LB:JOINT:PATELLOFEMORAL_R"]["relationships"]["CONNECTS"].append("LB:BONE:NOT_THERE_R")
    with pytest.raises(ValueError, match="references missing LB:BONE:NOT_THERE_R"):
        _grow(tmp_path, broken)
        check_project(tmp_path / "grown")


# ------------------------------------------------------------- C6 result plot
OFFICIAL = ROOT / "results" / "phase_b" / "2026-10-27_phase_b_runs_6c8b6ef.json"


def test_c6_plot_from_manifest_carries_validity_and_provenance():
    import json
    from tools.plot_phase_b import render, trajectory
    runs = json.loads(OFFICIAL.read_text(encoding="utf-8"))
    svg = render(runs, OFFICIAL.name)
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    assert runs[0]["commit_sha"][:12] in svg and OFFICIAL.name in svg
    assert "NOT CLINICALLY/PHYSIOLOGICALLY VALIDATED" in svg  # pre-Phase C manifest wording
    assert "0.841" in svg and "0.767" in svg and "73 ms sooner" in svg
    for run in runs:  # each curve ends exactly on the recorded exit state
        points, params = trajectory(run)
        assert points[0] == (0.0, 0.0)
        assert abs(points[-1][1] - run["simulation"]["q_rad"] * 180 / 3.141592653589793) < 1e-9


def test_c6_plot_uses_new_validity_fields_and_rejects_bad_input():
    import json
    from tools.plot_phase_b import render
    runs = json.loads(OFFICIAL.read_text(encoding="utf-8"))
    for run in runs:
        del run["status"]
        run["validity"] = dict(rm.VALIDITY)
    assert "Physiological validity: not established" in render(runs, "x.json")
    with pytest.raises(ValueError, match="no runs"):
        render([], "x.json")
    runs[1]["commit_sha"] = "b" * 40
    with pytest.raises(ValueError, match="different commits"):
        render(runs, "x.json")
