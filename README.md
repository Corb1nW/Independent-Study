# LB-AO v0.5 — Gluteus Maximus Reference Muscle

This release turns gluteus maximus into the reference template for future LB-AO muscle modules.

## Core rules implemented

1. **Evidence chain is claim-specific.** A citation supports named claims, not an entire entity.
2. **Property roles are explicit.** Quantities are classified as `parameter`, `function_of_state`, or `state_output`.
3. **Bilateral symmetry is a model assumption.** One generic baseline initializes left and right, but both targets remain independently overridable for future personalization.
4. **Measured/literature architecture stays distinct from model-derived values.** Maximum isometric force preserves its PCSA × specific-tension derivation.
5. **No fake completeness.** Tendon slack length, contraction velocity, and activation constants remain unresolved until a specific model/evidence choice supports them.
6. **State-dependent quantities are not constants.** Moment arm and musculotendon length are represented as functions of configuration; muscle force is a dynamic output.

## Evidence-backed baseline content

Ward et al. (2009) supplies cohort-level gluteus maximus architecture (mass, muscle length, fiber length, pennation and PCSA). Arnold et al. (2010) supplies the Hill-type model translation and maximum-isometric-force derivation. Model-specific quantities remain tied to their computational representation.

## Install

```powershell
py -m pip install -r requirements.txt
```

## Run the audit-style demo

```powershell
py demo_gluteus_maximus.py
```

The demo labels each quantity by role, evidence kind, status, source support, derivation, assumptions and validation outcome so the output can be understood without reading the YAML first.

The earlier schema demo remains available:

```powershell
py demo_quantitative.py
```

## Tests

```powershell
py -m pytest -q
```

## Important modeling boundary

The current shared left/right values are a **generic baseline initialization policy**, not an assertion of biological symmetry. Future subject-specific or side-specific observations can override either target without altering the original cohort evidence record.
