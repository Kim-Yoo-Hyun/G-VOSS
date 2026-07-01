# GeoCalib Reference Expansion Survey

Date: 2026-06-25 KST

Purpose: expand the GeoCalib/H001 paper reference set without broadening the
claim beyond calibrated relation reliability. The survey prioritizes papers
that help defend the current claim, contribution, method wording, and Related
Work structure.

## Current Gap

The manuscript already cited the main H001 sources and several recent
open-vocabulary 3D Scene Graph papers, but the reference set was thin in four
places:

1. Foundational and online 3D Scene Graph construction.
2. Recent closed-set 3DSSG relation-prediction methods after VL-SAT.
3. Open-vocabulary graph systems used for planning, navigation, or LLM
   reasoning.
4. General calibration / selective-risk literature supporting the
   `calibrated reliability` terminology.

## Surveyed Literature and Paper Role

| Role | Papers | Paper-facing use |
| --- | --- | --- |
| Foundational 3DSG | Armeni et al. ICCV 2019; SceneGraphFusion CVPR 2021; Hydra RSS 2022 | Shows 3DSG is a stable 3D-grounded representation and has online/incremental construction lineage. |
| Direct relation predictors | SGGpoint, SMKA, VL-SAT, SGRec3D, OCRL-3DSSG NeurIPS 2025, LEO AAAI 2026 | Competing relation-prediction family; GeoCalib is not another generator but a post-source reliability layer. |
| Open-vocabulary 3D perception | OpenScene CVPR 2023; OpenMask3D NeurIPS 2023 | Upstream open-vocabulary object/region features motivate open-vocabulary 3DSG, but do not solve relation-edge reliability. |
| Open-vocabulary graph systems | ConceptGraphs ICRA 2024; HOV-SG RSS 2024; Clio RA-L 2024; Open3DSG; CCL-3DSGG; FROSS; OpenFunGraph; Octree-Graph | Supports the claim that graph edges are now language-facing and downstream-facing, so plausible text relations need physical grounding. |
| LLM / embodied reasoning boundary | 3DGraphLLM ICCV 2025; 3D-VCD CVPR 2026; ZING-3D; VIZOR; Open-World 3DSG-RAG | Motivation and boundary only. These should not make GeoCalib sound like a full LLM, RAG, navigation, or hallucination-mitigation paper. |
| Geometry / witness / rescoring threat | RelWitness 2026; Statistical Confidence Rescoring ICCV 2025; FirePlace CVPR 2025; GREAT CVPR 2025; SG-PGM CVPR 2024 | Directly sharpens novelty wording: GeoCalib is not first geometry, calibration, witness, or rescoring method; its contribution is the identity-preserving, source-output reliability contract with Violation@K and controls. |
| Calibration and risk | Guo et al. ICML 2017; Geifman and El-Yaniv NeurIPS 2017 | Supports calibrated confidence and risk/coverage terminology. |

## Promotion Decision

Promote into the AAAI Related Work:

- `armeni20193dscenegraph`
- `wu2021scenegraphfusion`
- `hughes2022hydra`
- `peng2023openscene`
- `takmaz2023openmask3d`
- `gu2024conceptgraphs`
- `werby2024hovsg`
- `maggio2024clio`
- `yeo2025scrssg`
- `zemskova2025graphllm`
- `heo2025ocrl3dssg`
- `ma2026leo`
- `ogunleye2026vcd`
- `guo2017calibration`
- `geifman2017selective`

Keep but frame carefully:

- `nguyen2026relwitness` remains the nearest novelty-threat citation.
- `saxena2025zing3d`, `madhavaram2026vizor`, and
  `yu2025openworld3dsg` remain trend/boundary citations, not baselines.

Do not add for now:

- Broad 2D SGG prior/bias papers such as Neural Motifs and TDE. They can support
  a semantic-prior story, but they risk pulling the paper away from the 3D
  relation-reliability contribution.
- Additional open-vocabulary segmentation papers beyond OpenScene/OpenMask3D
  unless the manuscript discusses node proposal quality in detail.

## Claim and Contribution Impact

The expanded references strengthen three paper claims:

1. 3D Scene Graphs are reused as compact spatial-symbolic interfaces for
   robotics, planning, navigation, and LLM reasoning; therefore relation
   reliability is not cosmetic.
2. Existing 3DSSG predictors and open-vocabulary graph systems already use
   semantic and geometric information, so GeoCalib should not claim novelty as
   simply "adding geometry."
3. Calibration and risk/coverage framing are established ML ideas; GeoCalib's
   contribution is instantiating them for geometry-checkable relation rows with
   identity-preserving evidence joins and recall/violation reporting.

## Primary Sources Checked

- Armeni et al., ICCV 2019: https://openaccess.thecvf.com/content_ICCV_2019/papers/Armeni_3D_Scene_Graph_A_Structure_for_Unified_Semantics_3D_Space_ICCV_2019_paper.pdf
- SceneGraphFusion, CVPR 2021: https://openaccess.thecvf.com/content/CVPR2021/papers/Wu_SceneGraphFusion_Incremental_3D_Scene_Graph_Prediction_From_RGB-D_Sequences_CVPR_2021_paper.pdf
- Hydra, RSS 2022: https://arxiv.org/abs/2201.13360
- OpenScene, CVPR 2023: https://openaccess.thecvf.com/content/CVPR2023/html/Peng_OpenScene_3D_Scene_Understanding_With_Open_Vocabularies_CVPR_2023_paper.html
- OpenMask3D, NeurIPS 2023: https://research.google/pubs/openmask3d-open-world-3d-instance-segmentation/
- ConceptGraphs, ICRA 2024: https://concept-graphs.github.io/
- HOV-SG, RSS 2024: https://arxiv.org/abs/2403.17846
- Clio, RA-L 2024: https://github.com/MIT-SPARK/Clio
- Statistical Confidence Rescoring, ICCV 2025: https://openaccess.thecvf.com/content/ICCV2025/html/Yeo_Statistical_Confidence_Rescoring_for_Robust_3D_Scene_Graph_Generation_from_ICCV_2025_paper.html
- OCRL-3DSSG, NeurIPS 2025: https://openreview.net/forum?id=LjmXrUsSrg
- LEO, AAAI 2026: https://ojs.aaai.org/index.php/AAAI/article/view/37728
- 3DGraphLLM, ICCV 2025: https://openaccess.thecvf.com/content/ICCV2025/html/Zemskova_3DGraphLLM_Combining_Semantic_Graphs_and_Large_Language_Models_for_3D_ICCV_2025_paper.html
- 3D-VCD, CVPR 2026: https://openaccess.thecvf.com/content/CVPR2026/html/Ogunleye_3D-VCD_Hallucination_Mitigation_in_3D-LLM_Embodied_Agents_through_Visual_Contrastive_CVPR_2026_paper.html
- Calibration, ICML 2017: https://proceedings.mlr.press/v70/guo17a/guo17a.pdf
- Selective Classification, NeurIPS 2017: https://proceedings.neurips.cc/paper_files/paper/7073-selective-classification-for-deep-neural-networks.pdf
