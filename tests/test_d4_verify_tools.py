"""Tests of the D4 verification job's manifest comparison (ci/d4-verify/compare_manifest.py; D-062 Amendment 6).

The comparison must tolerate the last-bit differences that another processor's OpenBLAS kernel produces in
unrounded diagnostics (reproduced with OPENBLAS_CORETYPE=Haswell: 1 to 8 units in the last place in the C3/C5
extreme moment arms), and must still fail on the smallest real change to a stored value, a changed status, a
boolean replaced by a number, or a changed structure. Keys, lengths and leaf types are compared exactly everywhere,
including under the residual paths; only changed pairs of finite floats can be residual- or rounding-level, and
integers stay exact (ChatGPT's D4-V01).
"""
import importlib.util
import subprocess
import sys
import json
import math
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "results/phase_d/2026-11-16_d4_assembled_runs_af21e78.json"
_spec = importlib.util.spec_from_file_location("compare_manifest", ROOT / "ci/d4-verify/compare_manifest.py")
cm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cm)


@pytest.fixture(scope="module")
def official():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _compare(tmp_path, a, b):
    pa, pb, pr = tmp_path / "a.json", tmp_path / "b.json", tmp_path / "r.json"
    pa.write_text(json.dumps(a), encoding="utf-8")
    pb.write_text(json.dumps(b), encoding="utf-8")
    code = cm.main(str(pa), str(pb), str(pr))
    return code, json.loads(pr.read_text(encoding="utf-8"))


def _ulps(x, n):
    for _ in range(n):
        x = math.nextafter(x, math.inf)
    return x


def _arm(m):
    """The Gait2392 fixed-knee C3 extreme moment arm, the value that moved by 8 units in the last place."""
    return m["consistency"]["C3_actions"]["direction"]["gait2392 | fixed_knee"]["disagreements_above_numerical_zero"][0]


def test_identical_manifests_pass(tmp_path, official):
    code, r = _compare(tmp_path, official, deepcopy(official))
    assert code == 0 and r["difference_count"] == 0 and r["passed"]


def test_last_bit_differences_in_diagnostics_pass_as_rounding_level(tmp_path, official):
    new = deepcopy(official)
    _arm(new)["extreme_moment_arm_m"] = _ulps(_arm(new)["extreme_moment_arm_m"], 8)
    code, r = _compare(tmp_path, official, new)
    assert code == 0 and r["passed"]
    assert len(r["rounding_level_differences"]) == 1 and not r["other_differences"]
    assert 0 < r["largest_rounding_level_relative_difference"] < 1e-17


@pytest.mark.parametrize("label, change", [
    ("diagnostic moved by 1e-9 m", lambda m: _arm(m).update(extreme_moment_arm_m=_arm(m)["extreme_moment_arm_m"] + 1e-9)),
    ("one unit of the knee angle's last decimal (5.7e-10 relative)",
     lambda m: m["runs"][0]["series"]["q_rad"]["LB:DOF:KNEE_FLEX_EXT_R"].__setitem__(
         150, round(m["runs"][0]["series"]["q_rad"]["LB:DOF:KNEE_FLEX_EXT_R"][150] + 1e-9, 9))),
    ("one unit of the final time's last decimal (the smallest real change, 3.33e-10 relative)",
     lambda m: m["runs"][0]["series"]["t_s"].__setitem__(-1, round(m["runs"][0]["series"]["t_s"][-1] + 1e-9, 9))),
    ("fractional sample index", lambda m: _arm(m).update(extreme_sample=_arm(m)["extreme_sample"] + 3.75e-11)),
    ("integer sample index written as a float", lambda m: _arm(m).update(extreme_sample=float(_arm(m)["extreme_sample"]))),
    ("status", lambda m: m["status"].update(consistency_checks="failed")),
    ("boolean replaced by 1", lambda m: m["consistency"]["C3_actions"].update(passed=1)),
    ("integer sample index", lambda m: _arm(m).update(extreme_sample=_arm(m)["extreme_sample"] + 1)),
    ("list length", lambda m: m["runs"][0]["series"]["t_s"].pop()),
    ("number replaced by NaN", lambda m: _arm(m).update(extreme_moment_arm_m=float("nan"))),
])
def test_real_changes_still_fail(tmp_path, official, label, change):
    new = deepcopy(official)
    change(new)
    code, r = _compare(tmp_path, official, new)
    assert code == 1 and not r["passed"] and r["other_differences"], label


def _residual(m):
    """The assembled female run's largest KKT residual: a finite float under the residual paths."""
    v = m["runs"][0]["verification"]
    assert type(v["largest_kkt_residual"]) is float
    return v


@pytest.mark.parametrize("label, change", [
    ("residual removed", lambda v: v.pop("largest_kkt_residual")),
    ("residual replaced by false", lambda v: v.update(largest_kkt_residual=False)),
    ("residual replaced by NaN", lambda v: v.update(largest_kkt_residual=float("nan"))),
    ("residual replaced by infinity", lambda v: v.update(largest_kkt_residual=float("inf"))),
    ("residual replaced by a string", lambda v: v.update(largest_kkt_residual="1e-12")),
    ("residual replaced by a list", lambda v: v.update(largest_kkt_residual=[v["largest_kkt_residual"]])),
    ("residual replaced by null", lambda v: v.update(largest_kkt_residual=None)),
    ("key added under the residual paths", lambda v: v.update(largest_new_residual=0.0)),
])
def test_malformed_residuals_fail(tmp_path, official, label, change):
    new = deepcopy(official)
    change(_residual(new))
    code, r = _compare(tmp_path, official, new)
    assert code == 1 and not r["passed"] and r["other_differences"], label
    assert not r["residual_level_differences"] and not r["rounding_level_differences"], label


def test_identical_nans_compare_equal(tmp_path, official):
    old, new = deepcopy(official), deepcopy(official)
    _residual(old)["largest_kkt_residual"] = _residual(new)["largest_kkt_residual"] = float("nan")
    code, r = _compare(tmp_path, old, new)
    assert code == 0 and r["difference_count"] == 0


def test_command_line_rejects_fractional_sample_index(tmp_path, official):
    new = deepcopy(official)
    _arm(new)["extreme_sample"] = _arm(new)["extreme_sample"] + 3.75e-11
    pb, pr = tmp_path / "b.json", tmp_path / "r.json"
    pb.write_text(json.dumps(new), encoding="utf-8")
    run = subprocess.run([sys.executable, str(ROOT / "ci/d4-verify/compare_manifest.py"), str(MANIFEST), str(pb), str(pr)],
                         capture_output=True, text=True)
    report = json.loads(pr.read_text(encoding="utf-8"))
    assert run.returncode == 1 and len(report["other_differences"]) == 1
    assert "extreme_sample" in report["other_differences"][0] and "type int vs float" in report["other_differences"][0]


def test_residuals_are_reported_not_failed(tmp_path, official):
    new = deepcopy(official)
    v = new["runs"][0]["verification"]
    key = next(k for k in v if k.startswith("largest_"))
    v[key] = v[key] * 10 + 1e-12
    code, r = _compare(tmp_path, official, new)
    assert code == 0 and r["residual_level_differences"] and not r["other_differences"]


def test_tolerance_rule():
    assert cm.within_rounding(1.0, _ulps(1.0, 100))
    assert cm.within_rounding(0.0, 5e-19)
    assert not cm.within_rounding(1.745329252, 1.745329253)
    assert not cm.within_rounding(True, 1) and not cm.within_rounding("a", "a")
    assert not cm.within_rounding(float("nan"), 0.0)
    assert not cm.within_rounding(150, 150.0000000000375) and not cm.within_rounding(150, 151)
    assert not cm.within_rounding(float("inf"), float("inf"))
