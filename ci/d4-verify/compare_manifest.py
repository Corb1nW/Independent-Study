"""Compare a regenerated D4 run manifest with the committed official one (D4 verification job).

    python compare_manifest.py COMMITTED.json REGENERATED.json REPORT.json

Reports every differing path. Exit 1 when a status, the regression or consistency verdicts, or any stored series
differs; residual-level differences in unrounded check values (machine arithmetic) are reported but do not fail.
"""
import json
import sys

RESIDUALS = ("/checks/residuals/", "/verification/", "largest_", "_difference", "excess_over_half_unit")


def walk(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append((f"{path}/{k}", "present in only one file"))
            else:
                walk(a[k], b[k], f"{path}/{k}", out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append((path, f"length {len(a)} vs {len(b)}"))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, f"{path}[{i}]", out)
    elif a != b:
        out.append((path, f"{a!r} vs {b!r}"))


def main(committed, regenerated, report):
    a, b = (json.load(open(p, encoding="utf-8")) for p in (committed, regenerated))
    diffs = []
    walk(a, b, "", diffs)
    residual = [d for d in diffs if any(r in d[0] for r in RESIDUALS)]
    other = [d for d in diffs if d not in residual]
    result = {"committed": committed, "regenerated": regenerated, "difference_count": len(diffs),
              "residual_level_differences": [f"{p}: {v}" for p, v in residual][:500],
              "other_differences": [f"{p}: {v}" for p, v in other][:500],
              "status_equal": a.get("status") == b.get("status"),
              "identical_apart_from_residuals": not other}
    json.dump(result, open(report, "w", encoding="utf-8"), indent=2)
    print(f"{committed}: {len(diffs)} differing paths ({len(residual)} residual-level, {len(other)} other); "
          f"status {'equal' if result['status_equal'] else 'DIFFERENT'}")
    return 0 if not other else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
