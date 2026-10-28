"""Traceability gate for observations a model consumes (D-055 item C4).

Applies D-039's condition (claim-specific provenance for every consumed input)
as far as software can. For each consumed observation it checks:

  (a) the ID resolves in the dataset, directly or through a documented alias to
      exactly one current observation, and the datum passes ``validate_datum``
      with its dataset;
  (b) it has a usable value: status ``populated`` and a non-null value;
  (c) at least one source claim whose ``source_id`` is in the source registry
      and whose ``supports`` list is non-empty;
  (d) the stored value is tied to a claim: some claim has
      ``value_directly_reported: true``, or the last step of
      ``transformation_history`` outputs the stored value and unit;
  (e) applicability is declared (``applicability.level``), including
      ``applicability.model_id`` for ``model_derived`` data.

SCOPE LIMIT: passing establishes traceability to a declared source claim. It
does not establish that the source actually supports the value: ``supports``
labels are free text with no machine link to the value. Whether a source
supports a value is a human source check (as in D-019 and D-055 C2), recorded
on the datum.
"""
from math import isclose

SCOPE_LIMIT = ("Traceability to a declared source claim only. Does not establish that the "
               "source supports the value; 'supports' labels are free text. Source support "
               "is a human source check recorded on the datum (D-055 C4).")


def _same_value(a, b):
    """Scalars, or vectors of equal length (D-058), equal within floating-point rounding."""
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b) and a:
        return all(_same_value(x, y) for x, y in zip(a, b))
    return False


def check_input(schema, dataset, observation_id):
    """Return ``{"observation_id", "resolved_id", "passed", "failures"}`` for one input."""
    result = {"observation_id": observation_id, "resolved_id": None,
              "passed": False, "failures": []}
    fail = result["failures"].append
    # (a) resolution and validation
    try:
        ids = schema.resolve_observation_ids(dataset, observation_id)
    except KeyError:
        fail(f"(a) {observation_id} does not resolve in the dataset")
        return result
    if len(ids) != 1:
        fail(f"(a) {observation_id} is an alias for {len(ids)} observations {ids}; "
             "name one current observation ID")
        return result
    oid = ids[0]
    result["resolved_id"] = oid
    datum = dataset["observations"][oid]
    errors = schema.validate_datum(datum, dataset)
    if errors:
        fail("(a) datum fails validation: " + "; ".join(errors))
    # (b) usable value
    if datum.get("status") != "populated" or datum.get("value") is None:
        fail(f"(b) no usable value (status {datum.get('status')}, value {datum.get('value')})")
    # (c) a resolvable, non-empty source claim
    registry = schema.source_registry(dataset)
    provenance = datum.get("provenance") or {}
    claims = [c for c in provenance.get("source_claims") or []
              if c.get("source_id") in registry and c.get("supports")]
    if not claims:
        fail("(c) no source claim with a registered source_id and a non-empty supports list")
    # (d) the stored value is tied to a claim
    direct = any(c.get("value_directly_reported") is True for c in claims)
    history = provenance.get("transformation_history") or []
    traced = False
    if history:
        last = history[-1]
        value = datum.get("value")
        out = last.get("output_value")
        traced = _same_value(out, value) and last.get("output_unit") == datum.get("unit")
    if claims and not (direct or traced):
        fail("(d) value not tied to a claim: no claim has value_directly_reported: true and "
             "the last transformation_history step does not output the stored value and unit")
    # (e) applicability
    applicability = datum.get("applicability") or {}
    if not applicability.get("level"):
        fail("(e) applicability.level not declared")
    if datum.get("datum_kind") == "model_derived" and not applicability.get("model_id"):
        fail("(e) model_derived datum without applicability.model_id")
    result["passed"] = not result["failures"]
    return result


def traceability_report(schema, dataset, observation_ids):
    """Check every consumed observation. ``passed`` is True only if all inputs pass."""
    results = [check_input(schema, dataset, oid) for oid in observation_ids]
    return {"passed": bool(results) and all(r["passed"] for r in results),
            "inputs": results, "scope_limit": SCOPE_LIMIT, "decision": "D-055 C4"}


def require_traceable(schema, dataset, observation_ids):
    """Raise ``ValueError`` naming every failure unless all inputs pass; return the report."""
    report = traceability_report(schema, dataset, observation_ids)
    if not report["passed"]:
        lines = [f"{r['observation_id']}: {f}" for r in report["inputs"] for f in r["failures"]]
        raise ValueError("input traceability gate failed: " + " | ".join(lines or ["no inputs"]))
    return report
