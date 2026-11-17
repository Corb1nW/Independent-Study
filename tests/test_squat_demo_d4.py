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
    try:
        return demo.load_official()
    except SystemExit as exc:   # a working copy changed and a shallow checkout lacks the archive commit
        pytest.skip(f"official manifests need Git history: {exc}")


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


# ---------------------------------------------------------------- ChatGPT's D4-DEMO-01 to 03

def test_card_parameters_are_the_selected_body_and_set(manifests, data):
    """D4-DEMO-01: fibre and slack lengths scale with each body; the card reads them from the shown run."""
    assembled, growth, _ = manifests
    for key, m in (("d4", assembled), ("growth", growth)):
        for run in m["runs"]:
            if run["variant"] != "moving_knee":
                continue
            shown = data["sets"][key][run["body"]]["params"]
            assert set(shown) == {a["name"] for a in run["actuators"]}
            for a in run["actuators"]:
                assert shown[a["name"]] == {"fmax": a["max_isometric_force_N"],
                                            "lopt_mm": round(a["optimal_fiber_length_m"] * 1000, 1),
                                            "lts_mm": round(a["tendon_slack_length_m"] * 1000, 1),
                                            "penn_deg": round(float(__import__("numpy").degrees(a["pennation_at_optimal_rad"])), 1)}
    g = data["sets"]["d4"]["gait2392"]["params"]["bifemlh_r"]
    f = data["sets"]["d4"]["female"]["params"]["bifemlh_r"]
    assert (g["lopt_mm"], g["lts_mm"]) == (109.0, 326.0) and (f["lopt_mm"], f["lts_mm"]) == (105.1, 314.2)
    assert all("lopt_mm" not in m for m in data["muscles"].values())   # no body-independent copy left
    assert "r.params[selected]" in demo.TEMPLATE


def _altered_copy(tmp_path):
    """The official assembled manifest at its default path under a scratch root, with the female mass changed and
    every metadata field, including the execution SHA and provenance label, left as it was (ChatGPT's probe)."""
    m = json.loads(demo.official_text("assembled"))
    run = next(r for r in m["runs"] if r["body"] == "female")
    run["body_mass_kg"] += 1.0
    path = tmp_path / demo.ASSEMBLED
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(m), encoding="utf-8")
    return path, m


def test_an_edited_manifest_at_the_default_path_cannot_reach_the_page(tmp_path, manifests):
    """D4-DEMO-02: the edited working copy is ignored in favour of the archived file; the page keeps the official
    values under the official label."""
    path, altered = _altered_copy(tmp_path)
    try:
        text = demo.official_text("assembled", root=tmp_path)
    except SystemExit as exc:
        pytest.skip(f"archive commit needs Git history: {exc}")
    official = json.loads(text)
    assert official == manifests[0] and official["commit_sha"] == altered["commit_sha"]
    female = lambda m: next(r for r in m["runs"] if r["body"] == "female")["body_mass_kg"]  # noqa: E731
    assert female(official) != female(altered)


def test_an_edited_manifest_given_explicitly_is_marked_custom(tmp_path, manifests):
    """D4-DEMO-02: the same file passed on the command line is not official, and the page says so instead of
    carrying the official provenance."""
    path, altered = _altered_copy(tmp_path)
    assert not demo.is_official(path, "assembled")
    assert demo.is_official(ROOT / demo.ASSEMBLED, "assembled") or pytest.skip("working copy differs from the archive")
    data = page_data(demo.render(altered, manifests[1], manifests[2], (path, demo.GROWTH, demo.D3), official=False))
    assert data["official"] is False
    assert page_data(PAGE.read_text(encoding="utf-8"))["official"] is True
    assert 'id="custom" hidden' in demo.TEMPLATE and "if (!DATA.official)" in demo.TEMPLATE


def test_a_wrong_archive_record_stops_the_build(tmp_path, monkeypatch):
    path, commit, _ = demo.OFFICIAL["assembled"]
    monkeypatch.setitem(demo.OFFICIAL, "assembled", (path, commit, "0" * 64))
    with pytest.raises(SystemExit):
        demo.official_text("assembled", root=tmp_path)


def test_solver_checks_show_their_configured_units_and_tolerances(data):
    """D4-DEMO-03: KKT is dimensionless with tolerance 1e-8; the second solvers agree within their tolerances."""
    import yaml
    d2 = yaml.safe_load((ROOT / "config" / "phase_d2_muscles.yaml").read_text(encoding="utf-8"))["parameters"]
    tol = data["checks"]["solver_tolerances"]
    for k in ("kkt_tolerance", "second_solver_t_star_tolerance", "second_solver_activation_tolerance"):
        assert tol[k] == {"value": d2[k]["value"], "unit": d2[k]["unit"]}
    assert tol["kkt_tolerance"]["unit"] == "1"
    opt = data["checks"]["optimizer"]
    assert opt["largest_kkt_residual"] <= tol["kkt_tolerance"]["value"]
    assert opt["second_solver_activation_difference"] <= tol["second_solver_activation_tolerance"]["value"]
    assert opt["second_solver_t_star_difference_N_m"] <= tol["second_solver_t_star_tolerance"]["value"]


def test_a5_text_describes_probes_and_the_positive_control():
    t = demo.TEMPLATE
    assert "Six failure probes" in t and "positive control" in t
    assert "Each test changes one thing with all path data fixed" not in t
