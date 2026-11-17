"""Tests of the Stage D4 demonstration page (tools/build_squat_demo_d4.py) and the per-stage demo names.

The page is presentation only. These tests check that it rebuilds byte for byte from pinned inputs, that the numbers
it shows are the official D4 manifests' numbers, that the figure and the muscles come from the same model, and that
its pinned-input reader refuses a file that no longer matches the run's record.
"""
import copy
import json
from pathlib import Path

import pytest

from tools import build_squat_demo_d4 as demo

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "SQUAT_DEMO_D4.html"


@pytest.fixture(scope="module")
def manifests():
    return demo.load(demo.ASSEMBLED), demo.load(demo.GROWTH), demo.load(demo.D3)


@pytest.fixture(scope="module")
def data(manifests):
    try:
        return demo.build_data(*manifests)
    except SystemExit as exc:   # a shallow checkout after the ontology has changed has no pinned blobs
        if "is not available" in str(exc):
            pytest.skip(f"pinned inputs need Git history: {exc}")
        raise


def page_data(html):
    start = html.index("const DATA = ") + len("const DATA = ")
    return json.loads(html[start:html.index(";\nconst JOINTS")].replace("<\\/", "</"))


def test_committed_page_rebuilds_byte_for_byte(manifests, data):
    assert demo.render(*manifests) == PAGE.read_text(encoding="utf-8")


def test_page_embeds_exactly_the_built_data(data):
    assert page_data(PAGE.read_text(encoding="utf-8")) == json.loads(json.dumps(data))


def test_numbers_are_the_manifests(manifests, data):
    assembled, growth, _ = manifests
    assert data["growth"]["hypothesis"] == growth["hypotheses"][0]
    assert data["status"] == assembled["status"]
    assert data["regression"]["largest_excess"] == max(v["largest_excess"] for v in assembled["regression"].values())
    assert [s[2] for s in data["consistency"]["summary"]] == [
        assembled["consistency"][k]["passed"]
        for k in ("C1_crossings", "C2_leverage", "C3_actions", "C4_evidence", "required_edges", "mirror")]
    assert data["oracle"] == assembled["oracle_references"]
    for run in assembled["runs"]:
        for k, v in run["checks"]["residuals"].items():
            assert data["checks"]["mechanics"][k]["worst"] >= abs(v)


def test_both_muscle_sets_and_all_bodies_are_shown(manifests, data):
    assembled, growth, _ = manifests
    for key, m in (("d4", assembled), ("growth", growth)):
        moving = [r for r in m["runs"] if r["variant"] == "moving_knee"]
        assert set(data["sets"][key]) == {r["body"] for r in moving}
        for r in moving:
            shown = data["sets"][key][r["body"]]
            assert set(shown["act"]) == set(r["series"]["activation"])
            assert len(shown["paths"]) == len(r["series"]["t_s"])
    assert set(data["sets"]["growth"]["female"]["act"]) - set(data["sets"]["d4"]["female"]["act"]) == {"iliacus_r", "psoas_r"}


def test_figure_points_are_the_d3_points_that_a2_regressed(manifests, data):
    _, _, d3 = manifests
    for r in d3["runs"]:
        pts = data["sets"]["d4"][r["body"]]["pts"]
        assert pts == demo.r({k: r["series"]["d1_points_m"][k] for k in pts}, 4)


def test_a_different_muscle_drawing_is_refused(manifests):
    assembled, growth, d3 = copy.deepcopy(manifests)
    run = next(r for r in assembled["runs"] if r["variant"] == "moving_knee")
    run["series"]["muscle_path_xy_m"][10][0][0][0] += 0.001
    with pytest.raises(SystemExit, match="differs from D3"):
        demo.build_data(assembled, growth, d3)


def test_pinned_reader_refuses_a_record_that_matches_neither_file_nor_blob(manifests):
    record = dict(manifests[0]["inputs"]["ontology_hip"], sha256="0" * 64)
    with pytest.raises(SystemExit):
        demo.pinned_text(record)


def test_pinned_reader_reads_the_working_file_when_unchanged(manifests):
    record = manifests[0]["inputs"]["ontology_hip"]
    path = ROOT / record["path"]
    if __import__("hashlib").sha256(path.read_bytes()).hexdigest() != record["sha256"]:
        pytest.skip("ontology changed since the run; the blob path is covered by the rebuild test")
    assert demo.pinned_text(record) == path.read_text(encoding="utf-8")


def test_cited_review_records_exist():
    for p in demo.REVIEWS.values():
        assert (ROOT / p).is_file(), p


def test_a_missing_review_record_stops_the_build(manifests, monkeypatch):
    monkeypatch.setitem(demo.REVIEWS, "missing", "docs/reviews/does_not_exist.md")
    with pytest.raises(SystemExit, match="cited review record missing"):
        demo.build_data(*manifests)


def test_demo_pages_are_named_by_stage():
    assert (ROOT / "SQUAT_DEMO_D3.html").is_file() and PAGE.is_file()
    assert not (ROOT / "SQUAT_DEMO.html").exists()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "SQUAT_DEMO_D4.html" in readme and "SQUAT_DEMO_D3.html" in readme and "SQUAT_DEMO.html" not in readme


def test_pinned_reader_falls_back_to_the_recorded_blob(manifests):
    record = manifests[0]["inputs"]["ontology_lower_limb_sagittal"]
    moved = dict(record, path="does/not/exist.yaml")    # as if the working file had changed or gone
    try:
        text = demo.pinned_text(moved)
    except SystemExit as exc:
        if "is not available" in str(exc):
            pytest.skip(f"blob needs Git history: {exc}")
        raise
    assert __import__("hashlib").sha256(text.encode("utf-8")).hexdigest() == record["sha256"]
