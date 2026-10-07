from pathlib import Path
from src.ontology import AnatomyOntology
ROOT=Path(__file__).parents[1]
onto=AnatomyOntology(ROOT/"ontology"/"hip.yaml")
def test_valid(): assert onto.validate()
def test_bilateral_hips(): assert onto.get("LB:JOINT:HIP_R")["side"]=="right" and onto.get("LB:JOINT:HIP_L")["side"]=="left"
def test_muscle_inventory(): assert len(onto.muscles_crossing("LB:JOINT:HIP_R")) >= 20
def test_gluteus_maximus_innervation(): assert "LB:NERVE:INFERIOR_GLUTEAL" in onto.innervation("LB:MUS:GLUTEUS_MAXIMUS_R")
def test_three_coordinates(): assert len(onto.related("LB:JOINT:HIP_R","HAS_COORDINATE"))==3
