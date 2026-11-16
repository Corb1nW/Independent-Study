"""Compare a regenerated OpenSim oracle reference with the committed one (D4 verification job).

    python compare_reference.py COMMITTED.json REGENERATED.json REPORT.json

Every numeric array (geometry, forces, unmodified geometry, kinematics) and the actuator list must be identical.
Provenance fields that describe the machine (python, platform, numpy) are reported, not compared. Exit 1 on any
other difference.
"""
import json
import sys

MACHINE = {"python", "platform", "numpy"}


def walk(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}/{k}: present in only one file")
            else:
                walk(a[k], b[k], f"{path}/{k}", out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path}: length {len(a)} vs {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, f"{path}[{i}]", out)
    elif a != b:
        out.append(f"{path}: {a!r} vs {b!r}")


def count(x):
    if isinstance(x, dict):
        return sum(count(v) for v in x.values())
    if isinstance(x, list):
        return sum(count(v) for v in x)
    return 1 if isinstance(x, (int, float)) and not isinstance(x, bool) else 0


def main(committed, regenerated, report):
    a, b = (json.load(open(p, encoding="utf-8")) for p in (committed, regenerated))
    diffs = []
    for key in sorted(set(a) | set(b)):
        if key == "provenance":
            continue
        walk(a.get(key), b.get(key), "/" + key, diffs)
    pa, pb = a.get("provenance", {}), b.get("provenance", {})
    prov = [f"/provenance/{k}: {pa.get(k)!r} vs {pb.get(k)!r}" for k in sorted(set(pa) | set(pb))
            if k not in MACHINE and pa.get(k) != pb.get(k)]
    machine = {k: [pa.get(k), pb.get(k)] for k in sorted(MACHINE)}
    result = {"committed": committed, "regenerated": regenerated, "numeric_values": count({k: v for k, v in a.items()
              if k != "provenance"}), "differences": diffs[:200], "difference_count": len(diffs),
              "provenance_differences": prov, "machine": machine, "identical": not diffs and not prov}
    json.dump(result, open(report, "w", encoding="utf-8"), indent=2)
    print(f"{committed}: {result['numeric_values']} numeric values, {len(diffs)} differences, "
          f"{len(prov)} provenance differences -> {'IDENTICAL' if result['identical'] else 'DIFFERENT'}")
    return 0 if result["identical"] else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
