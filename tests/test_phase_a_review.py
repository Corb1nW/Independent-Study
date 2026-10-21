"""Negative tests for ChatGPT's Phase A review findings A1-A3 (review of 4abb4f1, 2026-10-21).

Each test failed (the bad record was accepted) at 4abb4f1; see
docs/reviews/2026-10-21_Claude_Response_to_Phase_A_Review.md.
"""
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from src.integrity import check_project
from src.quantitative import QuantitativeSchema

ROOT = Path(__file__).parents[1]
SCHEMA = ROOT / "ontology" / "quantitative_schema.yaml"
GMAX = ROOT / "ontology" / "quantitative_data" / "gluteus_maximus.yaml"
MASS = "LB-QD:GMAX:MASS:WARD2009"
FMAX = "LB-QD:GMAX:FMAX:ARNOLD2010"

q = QuantitativeSchema(SCHEMA)
data = q.load_dataset(GMAX)
OBS = data["observations"]


def errors_contain(d, fragment, dataset=data):
    errs = q.validate_datum(d, dataset)
    assert any(fragment in e for e in errs), f"expected '{fragment}' in {errs}"


# ---------------------------------------------------------------- A1 source registry scope
@pytest.fixture
def two_datasets(tmp_path):
    """Dataset A defines SRC:ONLY_IN_A; dataset B has no sources but cites it."""
    a = {"sources": {"SRC:ONLY_IN_A": {"title": "defined only in dataset A"}}, "observations": {}}
    obs = deepcopy(OBS[MASS])  # defaults already resolved, so B needs no `common` block
    obs["provenance"]["source_claims"] = [{"source_id": "SRC:ONLY_IN_A", "supports": ["mass"]}]
    b = {"observations": {MASS: obs}}
    (tmp_path / "a.yaml").write_text(yaml.safe_dump(a), encoding="utf-8")
    (tmp_path / "b.yaml").write_text(yaml.safe_dump(b), encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("order", [("a", "b"), ("b", "a")])
def test_dataset_cannot_cite_another_datasets_source(two_datasets, order):
    schema = QuantitativeSchema(SCHEMA)
    loaded = {name: schema.load_dataset(two_datasets / f"{name}.yaml") for name in order}
    errs = schema.validate_datum(loaded["b"]["observations"][MASS], loaded["b"])
    assert any("unknown source SRC:ONLY_IN_A" in e for e in errs), errs


def test_loading_a_dataset_does_not_change_the_global_registry(two_datasets):
    schema = QuantitativeSchema(SCHEMA)
    before = set(schema.known_sources)
    schema.load_dataset(two_datasets / "a.yaml")
    assert schema.known_sources == before


def test_dataset_may_cite_its_own_sources():
    assert q.validate_datum(OBS[MASS], data) == []


def test_without_dataset_only_ontology_sources_are_known():
    errors_contain(OBS[MASS], "unknown source SRC:WARD_2009", dataset=None)


# ---------------------------------------------------------------- A2 reference fields
def test_dangling_related_observation_rejected():
    d = deepcopy(OBS[FMAX])
    d["quality"]["value_comparisons"][0]["related_observation"] = "LB-QD:DOES_NOT_EXIST"
    errors_contain(d, "related_observation LB-QD:DOES_NOT_EXIST does not exist")


def test_related_observation_alias_accepted():
    alias = next(iter(data.get("observation_aliases") or {}))
    d = deepcopy(OBS[FMAX])
    d["quality"]["value_comparisons"][0]["related_observation"] = alias
    assert q.validate_datum(d, data) == []


def test_dangling_conflicts_with_rejected():
    d = deepcopy(OBS[MASS])
    d["quality"]["conflicts_with"] = ["LB-QD:DOES_NOT_EXIST"]
    errors_contain(d, "conflicts_with LB-QD:DOES_NOT_EXIST does not exist")


def test_unknown_convention_source_rejected():
    d = deepcopy(OBS[MASS])
    d["coordinate_context"]["convention_source_id"] = "SRC:DOES_NOT_EXIST"
    errors_contain(d, "convention_source_id cites unknown source SRC:DOES_NOT_EXIST")


def test_known_convention_source_accepted():
    d = deepcopy(OBS[MASS])
    d["coordinate_context"]["convention_source_id"] = "SRC:ISB_WU_2002"
    assert q.validate_datum(d, data) == []


def test_unknown_derivation_input_source_rejected():
    d = deepcopy(OBS[FMAX])
    d["derivation"]["inputs"][0]["source_id"] = "SRC:DOES_NOT_EXIST"
    errors_contain(d, "cites unknown source SRC:DOES_NOT_EXIST")


def test_free_text_derivation_inputs_are_not_references():
    d = deepcopy(OBS[MASS])
    d["derivation"]["inputs"] = ["a free-text description, not an ID"]
    assert q.validate_datum(d, data) == []


def test_integrity_check_catches_dangling_observation_reference(tmp_path):
    """The project-wide check validates each observation against its own dataset."""
    for sub in ("ontology", "ontology/quantitative_data"):
        (tmp_path / sub).mkdir(parents=True, exist_ok=True)
    for name in ("hip.yaml", "quantitative_schema.yaml"):
        (tmp_path / "ontology" / name).write_text((ROOT / "ontology" / name).read_text(encoding="utf-8"),
                                                 encoding="utf-8")
    raw = yaml.safe_load(GMAX.read_text(encoding="utf-8"))
    quality = deepcopy(OBS[MASS]["quality"])  # MASS takes quality from the dataset's `common` block
    quality["conflicts_with"] = ["LB-QD:DOES_NOT_EXIST"]
    raw["observations"][MASS]["quality"] = quality
    (tmp_path / "ontology" / "quantitative_data" / "gluteus_maximus.yaml").write_text(
        yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
    problems = check_project(tmp_path)
    assert any("conflicts_with LB-QD:DOES_NOT_EXIST" in p for p in problems), problems
    assert check_project(ROOT) == []


# ---------------------------------------------------------------- A3 readiness wording
def test_report_does_not_claim_simulation_readiness():
    report = q.validation_report(OBS[MASS], data)
    assert "ready_for_simulation" not in report
    assert report["admissible_as_simulation_input"].startswith("YES")
    assert "not model readiness" in report["admissible_as_simulation_input"]


def test_invalid_datum_is_not_admissible():
    d = deepcopy(OBS[MASS])
    d["unit"] = None
    assert q.validation_report(d, data)["admissible_as_simulation_input"] == "NO"
