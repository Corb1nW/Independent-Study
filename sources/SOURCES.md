# Source list

Every unique source the project has used. Rules and how to add one: [`README.md`](README.md).
**How complete this is:** built on 2026-10-27 from the data registries, `Research Materials`, the sources cited in PR #19, and a search of `docs/DECISIONS.md`, `docs/reviews/` and `PROJECT_STATE.md` for author–year citations, PMC/NBK/DOI/PMID identifiers and links. Commit messages and PR descriptions were not searched exhaustively. Treat it as a curated inventory; reviewers keep checking new citations by hand (ChatGPT review P19-02).

Status: **Read** = opened and used · **Cited, not accessed** = named because another source relies on it · **Background** = read for context; no claim depends on it.

## Anatomy, biomechanics and modeling (evidence)

| ID | Source | Link | Used for | Status |
|---|---|---|---|---|
| `SRC:ARNOLD_2010` | Arnold EM, Ward SR, Lieber RL, Delp SL (2010). A model of the lower limb for analysis of human movement. *Ann Biomed Eng* 38(2):269–279 | [doi:10.1007/s10439-009-9852-5](https://doi.org/10.1007/s10439-009-9852-5) · [PMC2903973](https://pmc.ncbi.nlm.nih.gov/articles/PMC2903973/) | Hill-type model translation; gluteus maximus maximum isometric force 1852.6 N and model PCSA (D-019, D-020, `gluteus_maximus.yaml`); meaning of that force (D-056) | Read |
| `SRC:ARNOLD_DELP_2011` | Arnold EM, Delp SL (2011). Fibre operating lengths of human lower limb muscles during walking. *Philos Trans R Soc Lond B Biol Sci* 366:1530–1539 | [PMC3130447](https://pmc.ncbi.nlm.nih.gov/articles/PMC3130447/) | Why tendon slack length stays model-specific (D-021, `gluteus_maximus.yaml`) | Read |
| — | de Leva P (1996). Adjustments to Zatsiorsky-Seluyanov's segment inertia parameters. *J Biomech* 29(9):1223–1230 | no stable link recorded (journal DOI not printed in the copy read) | Segment mass, centre of mass, radius of gyration and endpoints for female and male bodies (D-058, planned dataset) | Read (a PDF copy, through machine extraction; Table 4 not yet transcribed, see D-058 open concern 1) |
| — | Delp SL, Loan JP, Hoy MG, Zajac FE, Topp EL, Rosen JM (1990). An interactive graphics-based model of the lower extremity to study orthopaedic surgical procedures. *IEEE Trans Biomed Eng* 37:757–767 (as cited in Arnold 2010, ref. 13) | no link recorded | Arnold 2010 splits gluteus maximus force across compartments using its proportions (D-056) | Cited, not accessed |
| — | Grood ES, Suntay WJ (1983). A joint coordinate system for the clinical description of three-dimensional motions: application to the knee. *J Biomech Eng* (volume and pages not recorded) | [doi:10.1115/1.3138397](https://doi.org/10.1115/1.3138397) | Planned knee flexion convention (D-058 item 6) | Cited, not accessed |
| — | HAS-Motion (Visual3D) wiki. Adjusted Zatsiorsky-Seluyanov's segment inertia parameters | [wiki.has-motion.com](https://wiki.has-motion.com/Adjusted_Zatsiorsky-Seluyanov%27s_segment_inertia_parameters) | Secondary reproduction of de Leva 1996; compared with the paper, some rows differ (D-058 open concern 1). Not used as a source of values | Read |
| `SRC:HIP_CAPSULE_REVIEW` | Jimenez AE, et al. (2020). Hip joint capsular anatomy, mechanics, and surgical management. *JBJS Reviews* | [PMC7406151](https://pmc.ncbi.nlm.nih.gov/articles/PMC7406151/) | Hip capsule anatomy (`hip.yaml`) | Read |
| `SRC:STATPEARLS_ADDUCTOR_MAGNUS` | Jeno SH, Launico MV, Schindler GS. Anatomy, Bony Pelvis and Lower Limb: Thigh Adductor Magnus Muscle. *StatPearls* (updated 2023-10-24) | [NBK534842](https://www.ncbi.nlm.nih.gov/books/NBK534842/) | Adductor magnus dual innervation (D-034, `hip.yaml`) | Read |
| — | OpenStax. *Anatomy and Physiology* (edition not recorded) | no link recorded | Named in the source hierarchy as the gross-anatomy source (D-009); no data in the project cites it yet | Cited, not accessed |
| `SRC:OPENSIM_GAIT2392` | OpenSim documentation. Gait2392 and Gait2354 Models | [OpenSim Confluence](https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim/pages/53086215) | Computational modeling reference, not anatomical ground truth (D-011, `hip.yaml`) | Read |
| — | OpenSim API documentation (version 3.2). `Millard2012EquilibriumMuscle` class reference | [simtk.org](https://simtk.org/api_docs/opensim/api_docs32/classOpenSim_1_1Millard2012EquilibriumMuscle.html) | Maximum isometric force as a fiber property projected by cos(pennation) (D-056) | Read |
| `SRC:STATPEARLS_HIP` | Anatomy, Bony Pelvis and Lower Limb, Hip. *StatPearls* | [NBK526019](https://www.ncbi.nlm.nih.gov/books/NBK526019/) | Hip regional anatomy (D-009, `hip.yaml`) | Read |
| `SRC:WARD_2009` | Ward SR, Eng CM, Smallwood LH, Lieber RL (2009). Are current measurements of lower extremity muscle architecture accurate? *Clin Orthop Relat Res* 467(4):1074–1082 | [doi:10.1007/s11999-008-0594-8](https://doi.org/10.1007/s11999-008-0594-8) · [PMC2650051](https://pmc.ncbi.nlm.nih.gov/articles/PMC2650051/) | Gluteus maximus architecture: mass, lengths, fiber length normalization, pennation, PCSA (D-019, `gluteus_maximus.yaml`) | Read |
| `SRC:ISB_WU_2002` | Wu G, et al. (2002). ISB recommendation on definitions of joint coordinate system, Part I: ankle, hip, and spine. *J Biomech* 35(4):543–548 | [PMID 11934426](https://pubmed.ncbi.nlm.nih.gov/11934426/) | Joint coordinate conventions (D-011, `hip.yaml`); does not cover the knee (D-055 Amendment 1) | Read |
| — | Winter DA. *Biomechanics and Motor Control of Human Movement* (Wiley; edition not recorded) | no link recorded | Considered as an alternative anthropometric source and not chosen (D-058 alternative c) | Cited, not accessed |
| — | Zajac FE (1989). Muscle and tendon: properties, models, scaling, and application to biomechanics and motor control. *Crit Rev Biomed Eng* 17:359–411 (as cited in Arnold 2010, ref. 48) | no link recorded | The Hill-type muscle model Arnold 2010 uses (D-056) | Cited, not accessed |

## Digital twins and related tools (background)

From the course notes (`Research Materials`). No project claim depends on these.

| ID | Source | Link | Used for | Status |
|---|---|---|---|---|
| — | A roadmap for the development of human body digital twins (authors and venue not recorded; PDF kept locally by Corbin) | local file, no public link recorded | Project background | Background |
| — | AnyBody Technology. AnyBody Modeling System | [anybodytech.com](https://www.anybodytech.com/software/anybodymodelingsystem/) | Comparable musculoskeletal modeling software | Background |
| — | Digital twins in healthcare: a comprehensive review and future directions (authors not recorded) | [PMC12671388](https://pmc.ncbi.nlm.nih.gov/articles/PMC12671388/) | Project background | Background |
| — | European Commission. European Virtual Human Twins (VHT) Initiative | [digital-strategy.ec.europa.eu](https://digital-strategy.ec.europa.eu/en/policies/virtual-human-twins) | Project background | Background |
| — | MyoSuite (website, demo and code repository) | [Website](https://sites.google.com/view/myosuite) · [Demo](https://myohub.github.io/myosuite_demo/) · [GitHub](https://github.com/MyoHub/myosuite) | Comparable musculoskeletal simulation framework | Background |
| — | NASA TechPort. Human Digital Twin Platform (HDTP) | [techport.nasa.gov](https://techport.nasa.gov/projects/154412) | Project background | Background |
| — | Article on nature.com, listed in the notes as “Regenerative Article” (title and authors not recorded) | [nature.com/articles/s41536-026-00464-z](https://www.nature.com/articles/s41536-026-00464-z#article-info) | Project background | Background |
| — | Stanford Medicine (2025). The Virtual You: How Medical Digital Twins are Revolutionizing Healthcare | [medicine.stanford.edu](https://medicine.stanford.edu/news/stories/2025/06/medical-digital-twins.html) | Project background | Background |

## Project design documents (internal)

Written for this project by ChatGPT; listed so every document the work rests on is in one place. Copies in `docs/design/` and `References/`.

| ID | Source | Link | Used for | Status |
|---|---|---|---|---|
| — | LB-AO QPS Rationale | [`docs/design/LB_AO_QPS_Rationale.pdf`](../docs/design/LB_AO_QPS_Rationale.pdf) | Quantitative schema design (D-013 to D-022) | Read |
| — | LB-AO Source & Evidence Standard | [`docs/design/LB_AO_Source_and_Evidence_Standard.pdf`](../docs/design/LB_AO_Source_and_Evidence_Standard.pdf) | Source hierarchy and claim classes (D-009, D-010) | Read |
| — | LB-AO v0.1 Pelvis & Hip Complex Ontology | [`docs/design/LB_AO_v0.1_Pelvis_Hip_Complex_Ontology.pdf`](../docs/design/LB_AO_v0.1_Pelvis_Hip_Complex_Ontology.pdf) | Ontology structure (D-004 to D-008) | Read |
| — | Musculoskeletal Digital Twin Ontological Framework | [`docs/design/Musculoskeletal_Digital_Twin_Ontological_Framework.pdf`](../docs/design/Musculoskeletal_Digital_Twin_Ontological_Framework.pdf) | Overall architecture (D-001 to D-003) | Read |
