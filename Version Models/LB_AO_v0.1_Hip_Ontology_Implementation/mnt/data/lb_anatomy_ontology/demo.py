from src.ontology import AnatomyOntology

onto = AnatomyOntology('ontology/hip.yaml')

print('Right hip:', onto.get('LB:JOINT:HIP_R')['anatomical_properties'])
print('\nStructures crossing the right hip:')
for eid, entity in onto.crossing('LB:JOINT:HIP_R'):
    print(f'  {eid}: {entity["name"]}')

print('\nWhat does the bony pelvis map to computationally?')
for eid in onto.related('LB:BONE:PELVIS', 'REPRESENTED_BY'):
    print(f'  {eid}: {onto.get(eid)["name"]}')
