"""D-053 Phase B software checks: not clinical/biomechanical validation."""
from copy import deepcopy
from hashlib import sha256
from math import isclose, pi, sqrt
import shutil
import subprocess
import pytest
import yaml
from src.hip_phase_b import (ROOT, resolve_inputs, simulate, load_config,
                             load_scenario, run_manifest, serialize_manifest,
                             first_boundary, verify_git_inputs)
from src.quantitative import QuantitativeSchema

CONFIG=ROOT/"config/phase_b_hip.yaml"
BASE=ROOT/"config/phase_b_scenario_baseline.yaml"
CHANGE=ROOT/"config/phase_b_scenario_perturbed.yaml"
DATA=ROOT/"ontology/quantitative_data/gluteus_maximus.yaml"

def inputs(scenario=BASE):
    return resolve_inputs(CONFIG, scenario)

def test_force_sign_and_ontology_source():
    x=inputs(); out=simulate(x)
    assert x["baseline_fmax_N"] == 1852.6
    assert x["right_fmax_N"] == x["left_fmax_N"] == 1852.6
    assert isclose(out["gluteus_torque_N_m"], -0.04*0.02*1852.6)
    assert out["gluteus_torque_N_m"] < 0
    assert out["outcome"] == "domain_exit" and out["which_limit"] == "lower"
    assert out["q_rad"] == pytest.approx(-pi/6)

def test_zero_activation():
    x=inputs(); x["params"]["activation"]=0
    out=simulate(x)
    assert out["gluteus_torque_N_m"] == 0
    assert out["outcome"] == "completed" and out["q_rad"] == 0

def test_overlay_force_and_canonical_source_integrity():
    before=sha256(DATA.read_bytes()).hexdigest()
    baseline, changed=inputs(), inputs(CHANGE)
    assert changed["right_fmax_N"] == pytest.approx(1.2*baseline["right_fmax_N"])
    assert changed["left_fmax_N"] == baseline["left_fmax_N"]
    assert simulate(changed)["gluteus_torque_N_m"] == pytest.approx(
        1.2*simulate(baseline)["gluteus_torque_N_m"])
    assert simulate(changed)["time_s"] < simulate(baseline)["time_s"]
    assert simulate(changed)["time_s"]/simulate(baseline)["time_s"] == pytest.approx(1/sqrt(1.2), abs=1e-12)
    assert sha256(DATA.read_bytes()).hexdigest() == before

def test_step_size_and_analytic_boundary_time():
    x=inputs()
    a=simulate(x, step_override_s=0.1)
    b=simulate(x, step_override_s=0.003)
    expected=sqrt((2*pi/6)/abs(a["angular_acceleration_rad_s2"]))
    assert a["time_s"] == pytest.approx(expected, abs=1e-11)
    assert b["time_s"] == pytest.approx(a["time_s"], abs=1e-11)

def test_upper_boundary():
    x=inputs()
    x["params"]["activation"]=0
    x["params"]["external_torque_N_m"]=3.0
    out=simulate(x, step_override_s=0.06)
    assert out["outcome"] == "domain_exit"
    assert out["which_limit"] == "upper"
    assert out["q_rad"] == pytest.approx(pi/3)
    assert out["qdot_rad_per_s"] > 0

@pytest.mark.parametrize("bound,v,a,expected",[
    ("lower",-0.5,0,True),("lower",0,-0.2,True),("lower",0,0.2,False),
    ("upper",0.5,0,True),("upper",0,0.2,True),("upper",0,-0.2,False)])
def test_n2_boundary_start(bound,v,a,expected):
    q=-pi/6 if bound=="lower" else pi/3
    hit=first_boundary(q,v,a,0.01,-pi/6,pi/3,1e-10)
    assert (hit is not None and hit[0]==0) == expected

def test_n2_simulate_at_boundary():
    x=inputs()
    x["params"]["initial_q_rad"]=-pi/6
    x["params"]["initial_qdot_rad_s"]=0
    outward=simulate(x)
    assert outward["outcome"]=="domain_exit" and outward["time_s"]==0
    x["params"]["activation"]=0
    x["params"]["external_torque_N_m"]=2
    inward=simulate(x)
    assert inward["time_s"] > 0

def test_n3_invalid_overlay_rejected(tmp_path):
    schema=QuantitativeSchema(ROOT/"ontology/quantitative_schema.yaml")
    dataset=schema.load_dataset(DATA)
    orig=yaml.safe_load(CHANGE.read_text())
    invalid=[
        ("target_entity_id","LB:MUS:GLUTEUS_MAXIMUS_L"),
        ("target_entity_id","LB:MUS:NOT_REAL"),
        ("base_observation_id","LB-QD:NOT_REAL"),
        ("scenario_multiplier",0),
        ("scenario_multiplier",-1),
        ("scenario_multiplier",float("inf")),
        ("scenario_multiplier","1.2"),
        ("kind","literature_evidence")]
    for key,value in invalid:
        sample=deepcopy(orig); sample[key]=value
        path=tmp_path/"bad.yaml"
        path.write_text(yaml.safe_dump(sample))
        with pytest.raises(ValueError):
            load_scenario(path,schema,dataset)

def test_n3_missing_reason_rejected(tmp_path):
    schema=QuantitativeSchema(ROOT/"ontology/quantitative_schema.yaml")
    dataset=schema.load_dataset(DATA)
    sample=yaml.safe_load(BASE.read_text()); del sample["reason"]
    path=tmp_path/"missing.yaml";path.write_text(yaml.safe_dump(sample))
    with pytest.raises(ValueError):
        load_scenario(path,schema,dataset)

def test_config_rejects_bad_metadata_and_values(tmp_path):
    sample=yaml.safe_load(CONFIG.read_text())
    for name,field,value in [
        ("initial_q_rad","value",2),
        ("moment_arm_m","value",-0.1),
        ("activation","value",1.1),
        ("step_s","unit","cm")]:
        case=deepcopy(sample); case["parameters"][name][field]=value
        path=tmp_path/"config.yaml";path.write_text(yaml.safe_dump(case))
        with pytest.raises(ValueError):
            load_config(path)

def test_manifest_pins_provenance_and_assumptions():
    x=inputs(CHANGE)
    # CI checks out a synthetic PR merge commit; use the actual checked-out SHA.
    import subprocess
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True)
    sha = commit.stdout.strip() if commit.returncode == 0 else "a"*40
    manifest=run_manifest(x,simulate(x),sha)
    assert manifest["source"]["observation_id"]=="LB-QD:GMAX:FMAX:ARNOLD2010"
    assert manifest["source"]["dataset_sha256"]==sha256(DATA.read_bytes()).hexdigest()
    assert manifest["scenario_sha256"]==sha256(CHANGE.read_bytes()).hexdigest()
    assert manifest["configuration"]["parameters"]["moment_arm_m"]["kind"]=="demonstration_assumption"
    assert "7.8%" in manifest["pennation_disclosure"]["conditional_overstatement"]
    assert manifest["omitted_physics"]["status"] == "deliberate_demonstration_simplifications"
    assert "gravity" in manifest["omitted_physics"]
    assert serialize_manifest(manifest).startswith("{")
    with pytest.raises(ValueError):
        run_manifest(x,simulate(x),"not-a-full-sha")


def test_c2_resolver_rejects_corrupt_source_evidence(tmp_path):
    """Mutation guard: replacing schema.validate_datum with no-op must break this test."""
    project = tmp_path / "project"
    ontology = project / "ontology"
    (ontology / "quantitative_data").mkdir(parents=True)
    for path in (ROOT / "ontology" / "hip.yaml", ROOT / "ontology" / "quantitative_schema.yaml"):
        shutil.copy2(path, ontology / path.name)
    dataset = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    # Preserve the correct scalar, unit and model ID, but remove its evidence claims:
    # only the structural/semantic/evidence validator should reject this.
    record = dataset["observations"]["LB-QD:GMAX:FMAX:ARNOLD2010"]
    record["provenance"]["source_claims"] = []
    path = ontology / "quantitative_data" / "gluteus_maximus.yaml"
    path.write_text(yaml.safe_dump(dataset), encoding="utf-8")
    with pytest.raises(ValueError, match="source datum fails validation"):
        resolve_inputs(CONFIG, BASE, root=project)


def _git_fixture(tmp_path):
    """Tiny isolated checkout, never changes the real project working tree."""
    root = tmp_path / "checkout"
    root.mkdir()
    target = root / "config.yaml"
    target.write_text("moment_arm_m: 0.04\n", encoding="utf-8")
    commands = [
        ["git", "init", "-q"],
        ["git", "config", "user.name", "Fixture"],
        ["git", "config", "user.email", "fixture@example.invalid"],
        ["git", "add", "config.yaml"],
        ["git", "commit", "-qm", "initial model input"]
    ]
    for command in commands:
        subprocess.run(command, cwd=root, capture_output=True, check=True)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                         capture_output=True, check=True, text=True).stdout.strip()
    return root, target, sha


def test_c1_git_input_provenance_clean_and_dirty(tmp_path):
    root, target, sha = _git_fixture(tmp_path)
    assert verify_git_inputs(root, {"config": target}, sha) == "verified_git_head_and_inputs"
    target.write_text("moment_arm_m: 0.08\n", encoding="utf-8")
    with pytest.raises(ValueError, match="differs from HEAD"):
        verify_git_inputs(root, {"config": target}, sha)


def test_c1_git_input_provenance_external_and_untracked(tmp_path):
    root, target, sha = _git_fixture(tmp_path)
    outside = tmp_path / "external.yaml"
    outside.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError, match="outside repository"):
        verify_git_inputs(root, {"config": outside}, sha)
    untracked = root / "untracked.yaml"
    untracked.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError, match="tracked input"):
        verify_git_inputs(root, {"config": untracked}, sha)


def test_c1_git_input_provenance_post_resolution_change(tmp_path):
    root, target, sha = _git_fixture(tmp_path)
    with pytest.raises(ValueError, match="changed since input resolution"):
        verify_git_inputs(root, {"config": target}, sha,
                          expected_hashes={"config": "0" * 64})


def test_c1_manifest_rejects_external_config_in_real_checkout(tmp_path):
    x = inputs()
    external = tmp_path / "config.yaml"
    external.write_bytes(CONFIG.read_bytes())
    x["input_paths"]["config"] = str(external)
    sha_process = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True)
    sha = sha_process.stdout.strip() if sha_process.returncode == 0 else "a" * 40
    if sha_process.returncode == 0:
        with pytest.raises(ValueError, match="outside repository"):
            run_manifest(x, simulate(x), sha)
    else:
        # ZIP fallback must never claim verification for an arbitrary input.
        manifest = run_manifest(x, simulate(x), sha)
        assert manifest["commit_provenance_status"].startswith("caller_supplied_sha_unverified")
