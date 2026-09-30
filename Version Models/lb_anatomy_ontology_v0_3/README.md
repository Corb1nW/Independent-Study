# LB-AO v0.3 — Pelvis/Hip Ontology + Quantitative Property Schema

This repository extends the v0.2 machine-readable pelvis/hip ontology with the first quantitative-property schema (LB-QPS v0.1).

## Design rule

**Schema first, values second.** The schema defines what can be known quantitatively and what metadata is required to defend a value. It intentionally does **not** populate convenient numerical values.

Every populated quantitative datum is classified as measured, estimated, literature-derived, model-derived, scaled, assumed, or calculated. It also carries provenance, applicability, method, uncertainty, and coordinate/model context where relevant.

## Files

- `ontology/hip.yaml` — v0.2 anatomical/biomechanical hip ontology.
- `ontology/quantitative_schema.yaml` — quantitative-property definitions and validation rules.
- `src/ontology.py` — anatomy ontology query/validation API.
- `src/quantitative.py` — quantitative schema API.
- `demo.py` — anatomical queries.
- `demo_quantitative.py` — quantitative schema demonstration.
- `tests/` — automated validation tests.

## Install

```powershell
py -m pip install -r requirements.txt
```

## Run

```powershell
py demo_quantitative.py
py -m pytest -q
```

## Initial quantitative domains

The schema currently covers segment inertial properties; hip kinematics and kinetics; musculotendon parameters; passive tissue mechanics; and anatomical/model geometry.

## Evidence policy

A citation supports a specific claim, not an entire entity. Populated values require a `source_claim` unless explicitly classified as a model assumption. Derived/scaled values must preserve transformation history. Coordinate-dependent values require a declared frame/coordinate convention. Population values remain population values and are never silently promoted to subject-specific measurements.
