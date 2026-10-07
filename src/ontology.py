from pathlib import Path
import yaml

class AnatomyOntology:
    def __init__(self,path):
        self.path=Path(path)
        self.data=yaml.safe_load(self.path.read_text(encoding="utf-8"))
        self.entities=self.data["entities"]
        self.relationship_types=set(self.data["relationship_types"])
        self.sources=self.data.get("sources",{})
        self.validate()
    def get(self,eid): return self.entities[eid]
    def find(self,*,entity_class=None,side=None,name_contains=None):
        out=[]
        for eid,e in self.entities.items():
            if entity_class and e.get("class")!=entity_class: continue
            if side and e.get("side")!=side: continue
            if name_contains and name_contains.lower() not in e.get("name","").lower(): continue
            out.append((eid,e))
        return out
    def related(self,eid,predicate): return self.get(eid).get("relationships",{}).get(predicate,[])
    def incoming(self,target_id,predicate=None):
        hits=[]
        for source_id,e in self.entities.items():
            for pred,targets in e.get("relationships",{}).items():
                if (predicate is None or pred==predicate) and target_id in targets: hits.append((source_id,pred))
        return hits
    def crossing(self,joint_id,entity_class=None):
        hits=[(eid,self.entities[eid]) for eid,_ in self.incoming(joint_id,"CROSSES")]
        return [x for x in hits if not entity_class or x[1].get("class")==entity_class]
    def muscles_crossing(self,joint_id): return self.crossing(joint_id,"SkeletalMuscle")
    def attachments(self,muscle_id):
        e=self.get(muscle_id); r=e.get("relationships",{})
        return {"origins":r.get("ORIGINATES_FROM",[]),"insertions":r.get("INSERTS_ON",[])}
    def innervation(self,muscle_id): return self.related(muscle_id,"INNERVATED_BY")
    def evidence(self,eid): return [self.sources[s] for s in self.get(eid).get("evidence",[]) if s in self.sources]
    def validate(self):
        errors=[]; ids=set(self.entities); src=set(self.sources)
        for eid,e in self.entities.items():
            if not e.get("name") or not e.get("class"): errors.append(f"{eid}: missing name/class")
            for pred,targets in e.get("relationships",{}).items():
                if pred not in self.relationship_types: errors.append(f"{eid}: unknown predicate {pred}")
                if not isinstance(targets,list): errors.append(f"{eid}: {pred} must contain a list"); continue
                for target in targets:
                    if target not in ids: errors.append(f"{eid}: {pred} references missing {target}")
            for s in e.get("evidence",[]):
                if s not in src: errors.append(f"{eid}: missing evidence source {s}")
        if errors: raise ValueError("Ontology validation failed:\n"+"\n".join(errors))
        return True
    def summary(self):
        classes={}
        for e in self.entities.values(): classes[e["class"]]=classes.get(e["class"],0)+1
        return {"version":self.data["ontology"]["version"],"entities":len(self.entities),"classes":dict(sorted(classes.items()))}
