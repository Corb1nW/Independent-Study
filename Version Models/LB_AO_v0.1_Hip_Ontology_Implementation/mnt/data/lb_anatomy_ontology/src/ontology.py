from pathlib import Path
import yaml

class AnatomyOntology:
    def __init__(self, path):
        self.path = Path(path)
        with self.path.open('r', encoding='utf-8') as f:
            self.data = yaml.safe_load(f)
        self.entities = self.data['entities']
        self.relationship_types = set(self.data['relationship_types'])
        self.validate()

    def get(self, entity_id):
        return self.entities[entity_id]

    def find(self, *, entity_class=None, side=None):
        out = []
        for eid, e in self.entities.items():
            if entity_class and e.get('class') != entity_class:
                continue
            if side and e.get('side') != side:
                continue
            out.append((eid, e))
        return out

    def related(self, entity_id, predicate):
        return self.get(entity_id).get('relationships', {}).get(predicate, [])

    def incoming(self, target_id, predicate=None):
        hits = []
        for source_id, entity in self.entities.items():
            for pred, targets in entity.get('relationships', {}).items():
                if (predicate is None or pred == predicate) and target_id in targets:
                    hits.append((source_id, pred))
        return hits

    def crossing(self, joint_id):
        return [(eid, self.entities[eid]) for eid, _ in self.incoming(joint_id, 'CROSSES')]

    def validate(self):
        errors = []
        ids = set(self.entities)
        for eid, entity in self.entities.items():
            for pred, targets in entity.get('relationships', {}).items():
                if pred not in self.relationship_types:
                    errors.append(f'{eid}: unknown predicate {pred}')
                if not isinstance(targets, list):
                    errors.append(f'{eid}: {pred} must contain a list')
                    continue
                for target in targets:
                    if target not in ids:
                        errors.append(f'{eid}: {pred} references missing {target}')
        if errors:
            raise ValueError('Ontology validation failed:\n' + '\n'.join(errors))
        return True
