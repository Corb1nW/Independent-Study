# LB-AO v0.1 - Pelvis & Hip Complex

Machine-readable reference ontology for the Musculoskeletal Digital Twin project.

## Design rule
Anatomical truth is stored separately from biomechanical/computational assumptions.

## Run
```bash
pip install -r requirements.txt
python demo.py
```

## Initial queries
- `get(entity_id)` - retrieve one entity.
- `find(entity_class=..., side=...)` - filter entities.
- `related(entity_id, predicate)` - outgoing relationships.
- `incoming(target_id, predicate)` - reverse relationships.
- `crossing(joint_id)` - structures explicitly recorded as crossing a joint.

## Expansion
The same ID and schema conventions should be reused for the knee, ankle, foot, and additional muscles/landmarks. Numerical biomechanical parameters should include provenance rather than being treated as universal anatomical facts.
