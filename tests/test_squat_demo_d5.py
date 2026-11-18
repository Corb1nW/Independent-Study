"""Tests of the Stage D5 demonstration page (tools/build_squat_demo_d5.py).

The page is presentation only. These tests check that it rebuilds byte for byte from the archived official files, that
the numbers it shows are those files' numbers, that an edited working copy cannot reach the page, that the figure and
the muscles come from the same model, and that the builder's own consistency checks fail when they should.
"""
import copy
import json
from pathlib import Path

import pytest

from tools import build_squat_demo_d5 as demo

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "SQUAT_DEMO_D5.html"


@pytest.fixture(scope="module")
def official():
    try:
        return demo.load_official()
    except SystemExit as exc:   # a working copy changed and a shallow checkout lacks the archive commit
        pytest.skip(f"official files need Git history: {exc}")


@pytest.fixture(scope="module")
def data(official):
    try:
        return demo.build_data(*official)
    except SystemExit as exc:
        if "is not available" in str(exc):
            pytest.skip(f"pinned inputs need Git history: {exc}")
        raise


def page_data(html):
    start = html.index("const DATA = ") + len("const DATA = ")
    return json.loads(html[start:html.index(";\nconst JOINTS")].replace("<\\/", "</"))


def test_committed_page_is_the_build_output(official):
    assert PAGE.read_text(encoding="utf-8") == demo.render(*official)


def test_page_numbers_are_the_official_files_numbers(data, official):
    d5, report, growth, _ = official
    assert data["run_commits"] == {"d5": d5["commit_sha"], "d4": growth["commit_sha"],
                                   "d3": official[3]["commit_sha"]}
    male5 = next(x for x in d5["runs"] if x["body"] == "male" and x["variant"] == "moving_knee")
    assert data["sets"]["d5"]["male"]["act"]["glut_max2_r"] == [round(v, 3) for v in
                                                               male5["series"]["activation"]["glut_max2_r"]]
    assert data["results"]["hypotheses"] == report["hypotheses"]
    assert len(data["sets"]["d5"]["male"]["act"]) == 43 and len(data["sets"]["d4"]["male"]["act"]) == 16
    assert len(data["consistency"]["deviations"]) == len(d5["consistency"]["C3_actions"]["declared_deviations"])
    assert all(d["confirmed_in"] for d in data["consistency"]["deviations"])


def test_inventory_places_every_muscle_once(data):
    inv = data["consistency"]["inventory"]
    counted = len(data["consistency"]["actuated_muscles"]) + sum(len(v) for v in inv.values())
    assert counted == data["anatomy"]["total_muscles"] == 102


def test_a2_is_computed_from_git_and_passes(data):
    assert set(data["a2"]) == set(demo.A2_COMMITS) and all(not v["code"] for v in data["a2"].values())
    assert next(a for a in data["acceptance"] if a["id"] == "A2")["passed"] is True


def test_edited_working_copy_is_ignored(tmp_path, official):
    """A changed file at the official path never reaches the page: the archived blob is read instead."""
    path, _, digest = demo.OFFICIAL["d5"]
    work = tmp_path / path
    work.parent.mkdir(parents=True)
    m = copy.deepcopy(official[0])
    m["runs"][0]["body_mass_kg"] = 999.0
    work.write_text(json.dumps(m), encoding="utf-8")
    try:
        text = demo.official_text("d5", root=tmp_path)
    except SystemExit as exc:
        pytest.skip(f"archive commit not available: {exc}")
    assert '"body_mass_kg":999.0' not in text.replace(" ", "")
    assert json.loads(text)["runs"][0]["body_mass_kg"] == official[0]["runs"][0]["body_mass_kg"]


def test_report_from_other_manifests_is_refused(official):
    d5, report, growth, d3 = official
    bad = copy.deepcopy(report)
    bad["inputs"]["d5_manifest"]["sha256"] = "0" * 64
    with pytest.raises(SystemExit, match="not computed from the official d5"):
        demo.build_data(d5, bad, growth, d3)


def test_display_groups_must_cover_the_actuators(official, monkeypatch):
    monkeypatch.setattr(demo, "GROUPS", demo.GROUPS[:-1])
    with pytest.raises(SystemExit, match="display groups"):
        demo.build_data(*official)


def test_d4_drawings_must_equal_d5s(official):
    d5, report, growth, d3 = official
    g = copy.deepcopy(growth)
    run = next(x for x in g["runs"] if x["variant"] == "moving_knee" and x["body"] == "female")
    order = [a.split(":")[-1].lower() for a in g["specification"]["actuators"]]
    j = order.index("iliacus_r")
    run["series"]["muscle_path_xy_m"][10][j][0][0] += 1e-9
    with pytest.raises(SystemExit, match="iliacus_r"):
        demo.build_data(d5, report, g, d3)


def test_page_states_review_status_and_names_no_custom_inputs():
    html = PAGE.read_text(encoding="utf-8")
    assert "awaiting ChatGPT's review (PR #55)" in html
    assert "--assembled" not in html and "custom inputs" not in html
    assert page_data(html)["manifests"]["d5"]["sha256"] == demo.OFFICIAL["d5"][2]


def test_f4_states_the_reported_shortfall_reduction(data, official):
    """D5-B01: F4 must agree with H4 and F2, not claim that no knee extensor was added."""
    f4 = next(f for f in data["findings"] if f["id"] == "F4")
    h4 = next(h for h in official[1]["hypotheses"] if h["id"] == "H4")["values_N_m"]
    for body in ("male", "gait2392"):
        for stage in ("d4", "d5"):
            assert f"{h4[body][stage]:.3f}" in f4["text"]
    assert "no knee extensor" not in f4["text"] and "cannot relieve" not in f4["text"]
    assert "TFL" in f4["text"] and "(F2)" in f4["text"]
    html = PAGE.read_text(encoding="utf-8")
    assert "no knee extensor" not in html and "cannot relieve" not in html
