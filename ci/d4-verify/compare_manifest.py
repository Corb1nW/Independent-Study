"""Compare a regenerated D4 run manifest with the committed official one (D4 verification job).

    python compare_manifest.py COMMITTED.json REGENERATED.json REPORT.json

Structure and types are compared exactly first: a key present in only one file, a list of another length, or two
leaves of different JSON types (an integer and a float, a number and a boolean, a string or null, a list or object in
place of a number) is always a failure, wherever it occurs. Integers, strings and booleans must be equal. Two NaNs
compare equal; a NaN against any other number is a failure. Only a changed pair of finite floats is then classified:

- residual-level: solver and check residuals, whose size depends on the machine (paths matching RESIDUALS); reported,
  never failing. Their pass/fail verdicts are compared exactly, because statuses and check verdicts are strings or
  booleans.
- rounding-level: two finite floats that differ by at most TOLERANCE * max(1, |a|, |b|). Unrounded diagnostics (for
  example the extreme moment arms in C3 and C5) can differ in their last few binary digits on another processor,
  because OpenBLAS picks its kernel by processor type. Reproduced in Claude's session with OPENBLAS_CORETYPE=Haswell
  at 31a9d3f: 9 such values, 1 to 8 units in the last place (at most 8.7e-19 m), the same 43 differing paths as
  ChatGPT's hosted rerun on another runner type; with Sandybridge, at most 1.9e-17 (relative). Reported, not failing.
- other: everything else, including every structural or type difference above and any change between finite floats
  larger than the tolerance. Fails.

Why 1e-12: every stored series value is rounded, so a real change to one is at least one unit of its last decimal.
In the official D4 manifests the smallest such change, measured by the rule above, is 3.33e-10 (one unit of the
final time 3.000000000 s, stored to 9 decimals; ChatGPT's D4-V01 review), about 333 times the tolerance; the largest
rounding-level difference seen is 1.9e-17, more than 50,000 times below it. Exit 1 if any "other" difference exists.
"""
import json
import math
import sys

RESIDUALS = ("/checks/residuals/", "/verification/", "largest_", "_difference", "excess_over_half_unit")
TOLERANCE = 1e-12


def _finite_float(x):
    return type(x) is float and math.isfinite(x)


def within_rounding(a, b):
    """True when a and b are finite floats that differ by at most TOLERANCE * max(1, |a|, |b|)."""
    if not (_finite_float(a) and _finite_float(b)):
        return False
    return abs(a - b) <= TOLERANCE * max(1.0, abs(a), abs(b))


def _kind(x):
    return "null" if x is None else type(x).__name__


def walk(a, b, path, out):
    """Append (path, text, pair) for every difference. pair is (a, b) only for two finite floats that differ;
    every other difference (structure, type, integer, string, boolean, NaN) has pair None and always fails."""
    if type(a) is not type(b):
        out.append((path, f"type {_kind(a)} vs {_kind(b)}: {a!r} vs {b!r}", None))
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append((f"{path}/{k}", "present in only one file", None))
            else:
                walk(a[k], b[k], f"{path}/{k}", out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append((path, f"length {len(a)} vs {len(b)}", None))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, f"{path}[{i}]", out)
    elif isinstance(a, float):
        if math.isnan(a) and math.isnan(b):
            return
        if a != b:
            pair = (a, b) if math.isfinite(a) and math.isfinite(b) else None
            out.append((path, f"{a!r} vs {b!r}", pair))
    elif a != b:
        out.append((path, f"{a!r} vs {b!r}", None))


def classify(diffs):
    """Only changed pairs of finite floats may be residual- or rounding-level; everything else is "other"."""
    residual, rounding, other = [], [], []
    for path, text, pair in diffs:
        if pair is None:
            other.append(f"{path}: {text}")
        elif any(r in path for r in RESIDUALS):
            residual.append(f"{path}: {text}")
        elif within_rounding(*pair):
            rounding.append((f"{path}: {text}", abs(pair[0] - pair[1]) / max(1.0, abs(pair[0]), abs(pair[1]))))
        else:
            other.append(f"{path}: {text}")
    return residual, rounding, other


def main(committed, regenerated, report):
    a, b = (json.load(open(p, encoding="utf-8")) for p in (committed, regenerated))
    diffs = []
    walk(a, b, "", diffs)
    residual, rounding, other = classify(diffs)
    result = {"committed": committed, "regenerated": regenerated, "difference_count": len(diffs),
              "tolerance": {"rule": "|a - b| <= tolerance * max(1, |a|, |b|)", "value": TOLERANCE},
              "residual_level_differences": residual[:500],
              "rounding_level_differences": [d for d, _ in rounding][:500],
              "largest_rounding_level_relative_difference": max((r for _, r in rounding), default=0.0),
              "other_differences": other[:500],
              "status_equal": a.get("status") == b.get("status"),
              "passed": not other}
    json.dump(result, open(report, "w", encoding="utf-8"), indent=2)
    print(f"{committed}: {len(diffs)} differing paths ({len(residual)} residual-level, {len(rounding)} rounding-level "
          f"<= {TOLERANCE:g} relative, largest {result['largest_rounding_level_relative_difference']:.3g}; "
          f"{len(other)} other); status {'equal' if result['status_equal'] else 'DIFFERENT'}")
    return 0 if not other else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
