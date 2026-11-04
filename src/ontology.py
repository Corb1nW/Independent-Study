from pathlib import Path
import yaml

MERGED_BLOCKS=("entities","sources","class_hierarchy","models")


class AnatomyOntology:
    """The LB-AO ontology, from one file or several module files (D-058 item 7).

    The first file is the primary module: it carries the `ontology` header and the
    controlled relationship vocabulary. Each further module file contributes entities,
    sources, class_hierarchy entries and model views. An ID defined in two files is an
    error, so adding a module can never silently replace an existing entity. References
    are validated across all files together.
    """
    def __init__(self,path):
        paths=[Path(p) for p in path] if isinstance(path,(list,tuple)) else [Path(path)]
        if not paths: raise ValueError("at least one ontology file required")
        self.paths=paths
        self.path=paths[0]
        self.data=yaml.safe_load(self.path.read_text(encoding="utf-8"))
        for block in MERGED_BLOCKS:
            self.data[block]=dict(self.data.get(block) or {})
        self.modules=[{"file":self.path.name,"module":self.data["ontology"].get("module")}]
        for extra in paths[1:]:
            module=yaml.safe_load(extra.read_text(encoding="utf-8"))
            header=module.get("ontology_module") or {}
            if header.get("extends")!=self.data["ontology"]["id"]:
                raise ValueError(f"{extra.name}: ontology_module.extends must be {self.data['ontology']['id']}")
            unknown=set(module)-set(MERGED_BLOCKS)-{"ontology_module"}
            if unknown:
                raise ValueError(f"{extra.name}: unsupported blocks {sorted(unknown)}")
            for block in MERGED_BLOCKS:
                for key,value in (module.get(block) or {}).items():
                    if key in self.data[block]:
                        raise ValueError(f"{extra.name}: {block} key {key} is already defined")
                    self.data[block][key]=value
            self.modules.append({"file":extra.name,"module":header.get("module")})
        self.entities=self.data["entities"]
        self.relationship_types=set(self.data["relationship_types"])
        self.sources=self.data["sources"]
        # IS_A hierarchy between entity classes: {child_class: parent_class} (D-031)
        self.class_hierarchy=self.data["class_hierarchy"]
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
    def class_ancestors(self,entity_class):
        """Return [entity_class, parent, grandparent, ...] following class_hierarchy (D-031)."""
        chain=[entity_class]; seen={entity_class}
        while chain[-1] in self.class_hierarchy:
            parent=self.class_hierarchy[chain[-1]]
            if parent in seen: raise ValueError(f"class_hierarchy cycle at {parent}")
            chain.append(parent); seen.add(parent)
        return chain
    def is_a(self,entity_class,ancestor): return ancestor in self.class_ancestors(entity_class)
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
            ref=e.get("convention_reference")
            if ref and ref not in src: errors.append(f"{eid}: convention_reference {ref} is not a known source")
        for child in self.class_hierarchy:
            try: self.class_ancestors(child)
            except ValueError as exc: errors.append(str(exc))
        if errors: raise ValueError("Ontology validation failed:\n"+"\n".join(errors))
        return True
    def summary(self):
        classes={}
        for e in self.entities.values(): classes[e["class"]]=classes.get(e["class"],0)+1
        return {"version":self.data["ontology"]["version"],"entities":len(self.entities),"classes":dict(sorted(classes.items()))}
