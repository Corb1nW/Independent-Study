from pathlib import Path
from src.ontology import AnatomyOntology

onto=AnatomyOntology(Path(__file__).parent/"ontology"/"hip.yaml")
print("SUMMARY",onto.summary())
print("\nRIGHT HIP MUSCLES")
for eid,e in onto.muscles_crossing("LB:JOINT:HIP_R"):
    print("-",eid,e["name"])

m="LB:MUS:GLUTEUS_MAXIMUS_R"
print("\nGLUTEUS MAXIMUS")
print("attachments:",onto.attachments(m))
print("innervation:",onto.innervation(m))
print("evidence:",[s["title"] for s in onto.evidence(m)])
