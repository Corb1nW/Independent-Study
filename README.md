This is an Independant Study between Corbin Wright and Fanchao Meng for the 2026 Fall semester at Misericordia University

The goal is to take my experience with dynamic system and control theory and apply this to my ambition with the field of Physical Therapy. The project is to create a digital twin of the human musculoskeletal system that can allow us to tune different parameters to reflect different conditions you may see in the real world. This tool would have benfits within clinics and students preparing for their time in the field. This project will be just laying the groundwork for a much more in depth product which will be highly customizable and reflects all the major systems that impact movement. 


## Repository layout

- **LB-AO code and records (repository root):** `src/`, `ontology/`, `tests/`, `tools/`, the demo scripts, `docs/DECISIONS.md` (decision log) and `PROJECT_STATE.md` (current state and next task). This is the line of work under review; its history begins at commit `d04fb78`.
- **`Notes`, `Research Materials`, `References/`:** course notes, research links and the design documents.
- **`Version Models/`:** the original v0.1 to v0.5 uploads (September 2026), kept as history. The root code supersedes them.

## LB-AO v0.5 — Gluteus Maximus Reference Muscle

This release turns gluteus maximus into the reference template for future LB-AO muscle modules.

### Core rules implemented

1. **Evidence chain is claim-specific.** A citation supports named claims, not an entire entity.
2. **Property roles are explicit.** Quantities are classified as `parameter`, `function_of_state`, or `state_output`.
3. **Bilateral symmetry is a model assumption.** One generic baseline initializes left and right, but both targets remain independently overridable for future personalization.
4. **Measured/literature architecture stays distinct from model-derived values.** Maximum isometric force preserves its PCSA × specific-tension derivation.
5. **No fake completeness.** Tendon slack length, contraction velocity, and activation constants remain unresolved until a specific model/evidence choice supports them.
6. **State-dependent quantities are not constants.** Moment arm and musculotendon length are represented as functions of configuration; muscle force is a dynamic output.

### Evidence-backed baseline content

Ward et al. (2009) supplies cohort-level gluteus maximus architecture (mass, muscle length, fiber length, pennation and PCSA). Arnold et al. (2010) supplies the Hill-type model translation and maximum-isometric-force derivation. Model-specific quantities remain tied to their computational representation.

### Install

```powershell
py -m pip install -r requirements.txt
```

### Run the audit-style demo

```powershell
py demo_gluteus_maximus.py
```

The demo labels each quantity by role, evidence kind, status, source support, derivation, assumptions and validation outcome so the output can be understood without reading the YAML first.

The earlier schema demo remains available:

```powershell
py demo_quantitative.py
```

### Tests

```powershell
py -m pytest -q
```

### Integrity check (Phase A)

Checks the cross-file references between the ontology, the quantitative schema and the datasets that are listed in the `src/quantitative.py` module docstring (free-text fields are not references and are not checked), and validates every observation against its own dataset. Exit code 1 on failure.

```powershell
py -m src.integrity
```

Validation runs in layers (DECISIONS.md D-035): structural (`src/datum_model.py`, Pydantic), semantic (vocabularies, property definitions, units via pint, physical bounds, ontology references) and evidence (sources, assumptions, derivations, applicability). The evidence layer checks that provenance is complete and every cited source is registered; it does **not** check that a source actually supports the value, which needs a reviewer to read the source. A datum that passes is reported as *admissible as a simulation input*: a datum-level result, not model-level simulation readiness (Phase C). `py tools/review_cycle1_probes.py` reruns the Review Cycle 1 probes.

### Project governance

- `docs/DECISIONS.md`: every decision, its defense, and how disagreements between collaborators were resolved.
- `PROJECT_STATE.md`: what currently exists, what has been verified, and the next task.
- `docs/skills/`: the Builder and Reviewer role skills that both AI models follow, whichever role each holds.

### Important modeling boundary

The current shared left/right values are a **generic baseline initialization policy**, not an assertion of biological symmetry. Future subject-specific or side-specific observations can override either target without altering the original cohort evidence record.
