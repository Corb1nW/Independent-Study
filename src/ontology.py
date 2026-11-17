from pathlib import Path
import yaml

MERGED_BLOCKS=("entities","sources","class_hierarchy","models")
ADDITION_FIELDS={"entity","add","evidence","basis","decision"}
COORDINATE_SIGNS=(1,-1)


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
        if self.data.get("relationship_additions"):
            raise ValueError(f"{self.path.name}: the primary module cannot contain relationship_additions")
        pending=[]
        for extra in paths[1:]:
            module=yaml.safe_load(extra.read_text(encoding="utf-8"))
            header=module.get("ontology_module") or {}
            if header.get("extends")!=self.data["ontology"]["id"]:
                raise ValueError(f"{extra.name}: ontology_module.extends must be {self.data['ontology']['id']}")
            unknown=set(module)-set(MERGED_BLOCKS)-{"ontology_module","relationship_additions"}
            if unknown:
                raise ValueError(f"{extra.name}: unsupported blocks {sorted(unknown)}")
            defined_before=set(self.data["entities"])
            for block in MERGED_BLOCKS:
                for key,value in (module.get(block) or {}).items():
                    if key in self.data[block]:
                        raise ValueError(f"{extra.name}: {block} key {key} is already defined")
                    self.data[block][key]=value
            self.modules.append({"file":extra.name,"module":header.get("module")})
            pending.append((extra.name,header.get("module"),module.get("relationship_additions") or [],defined_before))
        self.entities=self.data["entities"]
        # Relationship additions (D-062 item 5): a later module adds edges to entities defined in an
        # EARLIER module. Additions never remove or replace an edge; each names its evidence.
        self.added_edges=[]
        for file,mod,additions,defined_before in pending:
            self._apply_additions(file,mod,additions,defined_before)
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
    def _apply_additions(self,file,module,additions,defined_before):
        if not isinstance(additions,list): raise ValueError(f"{file}: relationship_additions must be a list")
        for i,item in enumerate(additions):
            where=f"{file}: relationship_additions[{i}]"
            if not isinstance(item,dict) or set(item)-ADDITION_FIELDS or not {"entity","add","evidence"}<=set(item):
                raise ValueError(f"{where}: needs entity, add and evidence (optional: basis, decision)")
            eid=item["entity"]
            if eid not in defined_before:
                raise ValueError(f"{where}: {eid} is not defined in an earlier module")
            evidence=item["evidence"]
            if not isinstance(evidence,list) or not evidence:
                raise ValueError(f"{where}: evidence must be a non-empty list of source IDs")
            for s in evidence:
                if s not in self.data["sources"]: raise ValueError(f"{where}: unknown evidence source {s}")
            if not isinstance(item["add"],dict) or not item["add"]:
                raise ValueError(f"{where}: add must map predicates to target lists")
            rel=self.entities[eid].setdefault("relationships",{})
            for pred,targets in item["add"].items():
                if pred not in self.data["relationship_types"]: raise ValueError(f"{where}: unknown predicate {pred}")
                if not isinstance(targets,list) or not targets: raise ValueError(f"{where}: {pred} needs a list of targets")
                for t in targets:
                    if t not in self.entities: raise ValueError(f"{where}: {pred} target {t} does not exist")
                    if t in rel.get(pred,[]): raise ValueError(f"{where}: {eid} {pred} {t} already exists")
                    rel.setdefault(pred,[]).append(t)
                    self.added_edges.append({"entity":eid,"predicate":pred,"target":t,"module":module,"file":file,
                                             "evidence":list(evidence),"basis":item.get("basis"),"decision":item.get("decision")})
    def edge_origin(self,eid,predicate,target):
        """The module that added an edge through relationship_additions, or None for an edge stated with its entity."""
        for e in self.added_edges:
            if (e["entity"],e["predicate"],e["target"])==(eid,predicate,target): return e["module"]
        return None
    def edge_evidence(self,eid,predicate,target):
        """Evidence for one edge: the addition's own sources for an added edge, otherwise the entity's."""
        for e in self.added_edges:
            if (e["entity"],e["predicate"],e["target"])==(eid,predicate,target): return list(e["evidence"])
        return list(self.get(eid).get("evidence",[]))
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
            errors+=self._coordinate_errors(eid,e)
            me=e.get("model_element")
            if me is not None and (not isinstance(me,dict) or set(me)!={"model","name"} or not all(isinstance(v,str) and v for v in me.values())):
                errors.append(f"{eid}: model_element needs model and name")
        seen={}
        for eid,e in self.entities.items():
            me=e.get("model_element")
            if isinstance(me,dict):
                key=(me.get("model"),me.get("name"))
                if key in seen: errors.append(f"{eid}: model_element {key} is also named by {seen[key]}")
                seen[key]=eid
        for child in self.class_hierarchy:
            try: self.class_ancestors(child)
            except ValueError as exc: errors.append(str(exc))
        if errors: raise ValueError("Ontology validation failed:\n"+"\n".join(errors))
        return True
    def _coordinate_errors(self,eid,e):
        """Machine-readable coordinate conventions (D-062 item 2), checked where present."""
        keys={"positive_motion","negative_motion","model_coordinates"}&set(e)
        if not keys: return []
        errors=[]
        if e.get("class")!="JointCoordinate": return [f"{eid}: {sorted(keys)} apply only to a JointCoordinate"]
        motions=[e.get("positive_motion"),e.get("negative_motion")]
        if not all(isinstance(m,str) and m for m in motions) or motions[0]==motions[1]:
            errors.append(f"{eid}: positive_motion and negative_motion must be two different names")
        mc=e.get("model_coordinates")
        if not isinstance(mc,list) or not mc: errors.append(f"{eid}: model_coordinates must be a non-empty list"); return errors
        for m in mc:
            if not isinstance(m,dict) or set(m)!={"model","coordinate","sign"} or m.get("sign") not in COORDINATE_SIGNS:
                errors.append(f"{eid}: each model coordinate needs model, coordinate and sign (+1 or -1)")
        return errors
    def model_element(self,eid):
        """(model, element name) of a computational entity, e.g. ('gait2392', 'femur_r')."""
        me=self.get(eid).get("model_element")
        if not me: raise KeyError(f"{eid} has no model_element")
        return me["model"],me["name"]
    def entity_for_model_element(self,model,name):
        hits=[eid for eid,e in self.entities.items() if (e.get("model_element") or {})=={"model":model,"name":name}]
        if len(hits)!=1: raise KeyError(f"{len(hits)} entities name {model} element {name!r}")
        return hits[0]
    def coordinate_for_motion(self,motion):
        """[(coordinate ID, +1 or -1)] for the coordinates whose positive or negative motion has this name."""
        out=[]
        for eid,e in self.entities.items():
            if e.get("positive_motion")==motion: out.append((eid,1))
            if e.get("negative_motion")==motion: out.append((eid,-1))
        return out
    def model_coordinate(self,coordinate_id,model):
        """(model coordinate name, sign) of an ontology coordinate in a computational model."""
        hits=[m for m in self.get(coordinate_id).get("model_coordinates",[]) if m["model"]==model]
        if len(hits)!=1: raise KeyError(f"{coordinate_id} has {len(hits)} coordinates in model {model}")
        return hits[0]["coordinate"],hits[0]["sign"]
    def summary(self):
        classes={}
        for e in self.entities.values(): classes[e["class"]]=classes.get(e["class"],0)+1
        return {"version":self.data["ontology"]["version"],"entities":len(self.entities),"classes":dict(sorted(classes.items()))}
