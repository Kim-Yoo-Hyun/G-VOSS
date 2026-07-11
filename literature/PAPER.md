# Paper Registry

Last updated: 2026-07-11

이 파일은 3D Scene Graph literature pass에서 추적하는 논문 목록과 reading queue를 관리한다. 논문별 상세 정리는 각 paper folder에 둔다.

## Paper Registry

| Paper | Year / venue | Folder | Status | Why it matters |
| --- | --- | --- | --- | --- |
| [3D Scene Graph: A Structure for Unified Semantics, 3D Space, and Camera](https://openaccess.thecvf.com/content_ICCV_2019/html/Armeni_3D_Scene_Graph_A_Structure_for_Unified_Semantics_3D_Space_ICCV_2019_paper.html) | ICCV 2019 | TBD | Candidate | 3D 공간, 객체/방/카메라/속성 semantics를 통합하는 초기 구조 |
| [Learning 3D Semantic Scene Graphs from 3D Indoor Reconstructions](https://3dssg.github.io/) | CVPR 2020 | `literature/2020_cvpr_3dssg/` | Read | 3DSSG/3RScan 계열의 기본 dataset과 closed-set 3DSG baseline |
| [SceneGraphFusion](https://shunchengwu.github.io/SceneGraphFusion) | CVPR 2021 | TBD | Candidate | RGB-D sequence에서 geometric segmentation과 GNN 예측을 융합해 incremental 3DSG 생성 |
| [Exploiting Edge-Oriented Reasoning for 3D Point-Based Scene Graph Analysis](https://sggpoint.github.io/) | CVPR 2021 | `literature/2021_cvpr_sggpoint/` | Read | EdgeGCN과 multi-dimensional edge feature로 relation edge 자체를 explicit modeling |
| [Hydra](https://arxiv.org/abs/2201.13360) | RSS 2022 | TBD | Candidate | real-time hierarchical 3DSG; ESDF, topology, room/object hierarchy, graph optimization |
| [OpenScene](https://openaccess.thecvf.com/content/CVPR2023/papers/Peng_OpenScene_3D_Scene_Understanding_With_Open_Vocabularies_CVPR_2023_paper.pdf) | CVPR 2023 | TBD | Related | CLIP-aligned dense 3D features; open-vocabulary object/material/affordance query의 upstream 근거 |
| [VL-SAT](https://cvpr.thecvf.com/virtual/2023/poster/22846) | CVPR 2023 Highlight | `literature/2023_cvpr_vl-sat/` | Read | visual-language semantics와 3D geometry를 3DSSG training에 결합; long-tail relation 보강 |
| [SGAligner: 3D Scene Alignment with Scene Graphs](https://openaccess.thecvf.com/content/ICCV2023/papers/Sarkar_SGAligner_3D_Scene_Alignment_with_Scene_Graphs_ICCV_2023_paper.pdf) | ICCV 2023 | TBD | Related / positioning | 3D scene graph를 partial-overlap scene alignment와 registration에 사용하는 downstream 근거; CAND-001의 direct baseline은 아님 |
| [3D Spatial Multimodal Knowledge Accumulation for Scene Graph Prediction in Point Cloud](https://openaccess.thecvf.com/content/CVPR2023/html/Feng_3D_Spatial_Multimodal_Knowledge_Accumulation_for_Scene_Graph_Prediction_in_CVPR_2023_paper.html) | CVPR 2023 | `literature/2023_cvpr_smka/` | Read | 3D spatial hierarchy와 symbolic/text knowledge를 3DSSG relation prediction에 결합; CAND-001의 spatial-knowledge closed-set baseline |
| [Incremental 3D Semantic Scene Graph Prediction From RGB Sequences](https://openaccess.thecvf.com/content/CVPR2023/papers/Wu_Incremental_3D_Semantic_Scene_Graph_Prediction_From_RGB_Sequences_CVPR_2023_paper.pdf) | CVPR 2023 | TBD | Candidate | RGB sequence에서 sparse geometry, geometric feature, edge feature로 online 3D SSG 추정 |
| [OpenMask3D](https://openmask3d.github.io/) | NeurIPS 2023 | TBD | Related | open-vocabulary 3D instance segmentation; CAND-001의 object-node proposal upstream |
| [OVSG](https://proceedings.mlr.press/v229/chang23b.html) | CoRL 2023 | TBD | CAND-003 P1 | free-form text query를 3D scene graph matching으로 ground; context-aware entity grounding |
| [SayPlan](https://proceedings.mlr.press/v229/rana23a.html) | CoRL 2023 Oral | `literature/2023_corl_sayplan/` | Read | LLM task planning을 3DSG로 grounding; graph가 downstream planning에 쓰이는 근거 |
| [ChatGPT outperforms crowd workers for text-annotation tasks](https://doi.org/10.1073/pnas.2305016120) | PNAS 2023 | TBD | H001 LLM-audit evidence | ChatGPT annotation을 trained-human/crowd benchmark에 직접 검증; LLM label 사용의 선례이지만 human benchmark 없는 gold 대체를 정당화하지 않음 |
| [G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment](https://aclanthology.org/2023.emnlp-main.153/) | EMNLP 2023 | TBD | H001 LLM-as-judge evidence | GPT-4 automatic evaluator를 human correlation으로 검증하고 model-generated-text bias를 명시 |
| [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685) | arXiv 2023 | TBD | H001 LLM-as-judge evidence | LLM judge를 human preference와 비교하고 position/verbosity/self-enhancement bias를 분석 |
| [SGRec3D](https://openaccess.thecvf.com/content/WACV2024/html/Koch_SGRec3D_Self-Supervised_3D_Scene_Graph_Learning_via_Object-Level_Scene_Reconstruction_WACV_2024_paper.html) | WACV 2024 | `literature/2024_wacv_sgrec3d/` | Read | graph bottleneck reconstruction으로 3DSG representation pretraining |
| [Open3DSG](https://arxiv.org/abs/2402.12259) | CVPR 2024 | `literature/2024_cvpr_open3dsg/` | Read | open-vocabulary object와 open-set relation을 LLM/VLM feature로 예측 |
| [CCL-3DSGG](https://openaccess.thecvf.com/content/CVPR2024/html/Chen_CLIP-Driven_Open-Vocabulary_3D_Scene_Graph_Generation_via_Cross-Modality_Contrastive_Learning_CVPR_2024_paper.html) | CVPR 2024 | `literature/2024_cvpr_ccl-3dsgg/` | Read | CLIP 기반 cross-modality contrastive learning으로 novel object/predicate 처리 |
| [GPT-4V(ision) is a Human-Aligned Evaluator for Text-to-3D Generation](https://openaccess.thecvf.com/content/CVPR2024/html/Wu_GPT-4Vision_is_a_Human-Aligned_Evaluator_for_Text-to-3D_Generation_CVPR_2024_paper.html) | CVPR 2024 | TBD | Direct H001 multimodal-evaluator precedent | GPT-4V로 3D asset을 평가하지만 human preference study로 alignment를 검증; H001과 가장 가까운 modality precedent |
| [AnnoLLM: Making Large Language Models to Be Better Crowdsourced Annotators](https://aclanthology.org/2024.naacl-industry.15/) | NAACL Industry 2024 | TBD | H001 LLM-annotation evidence | explain-then-annotate LLM pipeline을 crowd label과 비교하고 생성 dataset 품질을 human evaluation으로 검증 |
| [If in a Crowdsourced Data Annotation Pipeline, a GPT-4](https://arxiv.org/abs/2402.16795) | CHI 2024 | TBD | H001 hybrid-annotation evidence | GPT-4, ethical crowd pipeline, hybrid aggregation을 gold accuracy로 비교; LLM+human 조합이 단독보다 강할 수 있음을 보임 |
| [MEGAnno+: A Human-LLM Collaborative Annotation System](https://aclanthology.org/2024.eacl-demo.18/) | EACL Demo 2024 | TBD | H001 annotation-workflow evidence | complex/domain-specific context에서 LLM 오류 가능성을 명시하고 human verification을 포함한 collaborative workflow를 제안 |
| [Large Language Models for Data Annotation and Synthesis: A Survey](https://aclanthology.org/2024.emnlp-main.54/) | EMNLP 2024 | TBD | Surveyed for H001 | LLM annotation generation, assessment, utilization과 limitation taxonomy를 정리 |
| [SG-PGM: Partial Graph Matching Network with Semantic Geometric Fusion for 3D Scene Graph Alignment and Its Downstream Tasks](https://openaccess.thecvf.com/content/CVPR2024/papers/Xie_SG-PGM_Partial_Graph_Matching_Network_with_Semantic_Geometric_Fusion_for_CVPR_2024_paper.pdf) | CVPR 2024 | TBD | Related / positioning | partial graph matching, semantic-geometric fusion, point-matching rescoring; H001의 re-ranking framing과 가깝지만 목표는 scene graph alignment/registration |
| [ConceptGraphs](https://concept-graphs.github.io/) | ICRA 2024 | TBD | CAND-003 P1 | 2D foundation model 출력을 3D graph로 융합하고 LLM/VLM으로 inter-object relation 생성 |
| [HOV-SG](https://www.roboticsproceedings.org/rss20/p077.html) | RSS 2024 | TBD | CAND-003 P1 | dense open-vocabulary maps를 floor-room-object hierarchy와 navigation graph로 압축 |
| [EgoSG](https://openaccess.thecvf.com/content/CVPR2024W/SG2RL/html/Zhang_EgoSG_Learning_3D_Scene_Graphs_from_Egocentric_RGB-D_Sequences_CVPRW_2024_paper.html) | CVPRW 2024 | TBD | Candidate | camera pose/reconstruction 없이 egocentric RGB-D sequence에서 3DSG 추정 |
| [SG-Nav](https://proceedings.neurips.cc/paper_files/paper/2024/hash/098491b37deebbe6c007e69815729e09-Abstract-Conference.html) | NeurIPS 2024 | `literature/2024_neurips_sg-nav/` | Read | online 3D scene graph prompting과 hierarchical CoT로 zero-shot object navigation 수행 |
| [Multi-modal Situated Reasoning in 3D Scenes](https://nips.cc/virtual/2024/poster/97727) | NeurIPS 2024 Datasets and Benchmarks | TBD | CAND-003 P1 | MSQA/MSNN으로 situated 3D QA와 next-step navigation benchmark 제공 |
| [LangSplat](https://openaccess.thecvf.com/content/CVPR2024/papers/Qin_LangSplat_3D_Language_Gaussian_Splatting_CVPR_2024_paper.pdf) | CVPR 2024 Highlight | TBD | Related | 3DGS 기반 language field; relation graph보다는 open-vocabulary 3D query representation의 upstream |
| [Scene-LLM](https://openaccess.thecvf.com/content/WACV2025/html/Fu_Scene-LLM_Extending_Language_Model_for_3D_Visual_Reasoning_WACV_2025_paper.html) | WACV 2025 | TBD | CAND-003 P1 | 3D visual-language model로 scene captioning, QA, interactive planning을 평가 |
| [FirePlace](https://openaccess.thecvf.com/content/CVPR2025/html/Huang_FirePlace_Geometric_Refinements_of_LLM_Common_Sense_Reasoning_for_3D_CVPR_2025_paper.html) | CVPR 2025 | `literature/2025_cvpr_fireplace/` | Read | 3DSG 논문은 아니지만 LLM commonsense와 3D geometric constraint 결합의 직접 근거 |
| [Open-Vocabulary Functional 3D Scene Graphs for Real-World Indoor Spaces](https://openaccess.thecvf.com/content/CVPR2025/html/Zhang_Open-Vocabulary_Functional_3D_Scene_Graphs_for_Real-World_Indoor_Spaces_CVPR_2025_paper.html) | CVPR 2025 Highlight | `literature/2025_cvpr_openfungraph/` | Read | spatial relation을 넘어 functional relation을 open-vocabulary 3DSG로 모델링; Open3DSG/ConceptGraphs baseline 비교 |
| [3D-Mem](https://openaccess.thecvf.com/content/CVPR2025/html/Yang_3D-Mem_3D_Scene_Memory_for_Embodied_Exploration_and_Reasoning_CVPR_2025_paper.html) | CVPR 2025 | `literature/2025_cvpr_3d-mem/` | Read | object-centric 3DSG의 restrictive textual relation 한계를 지적; nuanced spatial understanding 평가 근거 |
| [3D-GRAND](https://openaccess.thecvf.com/content/CVPR2025/html/Yang_3D-GRAND_A_Million-Scale_Dataset_for_3D-LLMs_with_Better_Grounding_and_CVPR_2025_paper.html) | CVPR 2025 | TBD | Related | 3D-LLM hallucination과 dense grounding benchmark 근거; CAND-001 evaluation inspiration |
| [GREAT](https://openaccess.thecvf.com/content/CVPR2025/html/Shao_GREAT_Geometry-Intention_Collaborative_Inference_for_Open-Vocabulary_3D_Object_Affordance_Grounding_CVPR_2025_paper.html) | CVPR 2025 | TBD | Related | open-vocabulary 3D affordance grounding에서 geometry와 intention knowledge 결합 |
| [Universal Scene Graph Generation](https://openaccess.thecvf.com/content/CVPR2025/html/Wu_Universal_Scene_Graph_Generation_CVPR_2025_paper.html) | CVPR 2025 | TBD | Related | image/text/video/3D modality를 통합하는 SG representation 제안 |
| [FROSS](https://openaccess.thecvf.com/content/ICCV2025/html/Hou_FROSS_Faster-Than-Real-Time_Online_3D_Semantic_Scene_Graph_Generation_from_RGB-D_ICCV_2025_paper.html) | ICCV 2025 | `literature/2025_iccv_fross/` | Read | 2D scene graph를 3D로 lift하고 3D Gaussian으로 online/faster-than-real-time 3D SSG 생성; ReplicaSSG 제안 |
| [3DGraphLLM](https://openaccess.thecvf.com/content/ICCV2025/html/Zemskova_3DGraphLLM_Combining_Semantic_Graphs_and_Large_Language_Models_for_3D_ICCV_2025_paper.html) | ICCV 2025 | `literature/2025_iccv_3dgraphllm/` | Read | 3D semantic graph를 LLM 입력 표현으로 사용해 3D vision-language task 수행 |
| [Open-Vocabulary Octree-Graph for 3D Scene Understanding](https://openaccess.thecvf.com/content/ICCV2025/html/Wang_Open-Vocabulary_Octree-Graph_for_3D_Scene_Understanding_ICCV_2025_paper.html) | ICCV 2025 | `literature/2025_iccv_octree-graph/` | Read | adaptive-octree node와 spatial-relation edge로 open-vocabulary 3D representation 구성; CAND-001의 compact geometry evidence 참고축 |
| [ZING-3D: Zero-shot Incremental 3D Scene Graphs via Vision-Language Models](https://arxiv.org/abs/2510.21069) | arXiv 2025 | TBD | Final RW trend citation | zero-shot incremental 3D scene graph generation with VLMs, depth-grounded 2D scene graphs, and edges carrying spatial/semantic relations plus inter-object distances; not a direct H001 baseline |
| [Open-World 3D Scene Graph Generation for Retrieval-Augmented Reasoning](https://arxiv.org/abs/2511.05894) | AAAI 2026 / arXiv 2025 | TBD | Final RW boundary citation | open-world 3DSG plus retrieval-augmented reasoning across 3DSSG/Replica and downstream QA/grounding/retrieval/planning; boundary against broad open-world/RAG claims |
| [Relationship-Aware Hierarchical 3D Scene Graph for Task Reasoning](https://arxiv.org/abs/2602.02456) | ICRA 2026 | TBD | CAND-003 P1 | VLM으로 semantic relation을 추론하고 LLM/VLM task reasoning module을 결합 |
| [View-on-Graph: Zero-Shot 3D Visual Grounding via Vision-Language Reasoning on Scene Graphs](https://ojs.aaai.org/index.php/AAAI/article/view/37677) | AAAI 2026 | TBD | Final RW downstream citation | scene graph externalizes 3D spatial information for zero-shot 3D visual grounding; supports graph-as-reasoning-interface trend rather than direct H001 baseline |
| [VIZOR: Viewpoint-Invariant Zero-Shot Scene Graph Generation for 3D Scene Reasoning](https://openaccess.thecvf.com/content/WACV2026/papers/Madhavaram_VIZOR_Viewpoint-Invariant_Zero-Shot_Scene_Graph_Generation_for_3D_Scene_Reasoning_WACV_2026_paper.pdf) | WACV 2026 | TBD | Final RW boundary citation | training-free viewpoint-invariant zero-shot 3D scene graph generation from meshes; direct boundary for spatial relation coordinate-frame claims |
| [RieMind](https://arxiv.org/abs/2603.15386) | arXiv 2026 | `literature/2026_arxiv_riemind/` | Read | explicit 3DSG와 structured geometric tools로 LLM spatial reasoning을 수행 |
| [SGR3](https://arxiv.org/abs/2603.04614) | arXiv 2026 | TBD | Candidate | MLLM+RAG 기반 semantic 3D scene graph generation; explicit reconstruction을 우회 |
| [SCOUT](https://arxiv.org/abs/2603.05642) | arXiv 2026 | `literature/2026_arxiv_scout/` | Read | 3DSG 위에서 relational semantic reasoning을 object search utility로 distill |
| [ReLaGS](https://arxiv.org/abs/2603.17605) | arXiv 2026 | TBD | Candidate | language-distilled Gaussian scene + 3D semantic scene graph + relational reasoning; venue needs official verification |
| [ToLL](https://arxiv.org/abs/2603.28178) | arXiv 2026 | TBD | Candidate | topological geometry reasoning을 3DSG pretraining proxy로 사용 |
| [3D-VCD](https://arxiv.org/abs/2604.08645) | CVPR 2026 accepted / arXiv | `literature/2026_cvpr_3d-vcd/` | Read | distorted 3D scene graph와 visual contrastive decoding으로 3D-LLM hallucination을 줄임 |
| [RelWitness: Open-Vocabulary 3D Scene Graph Generation with Visual-Geometric Relation Witnesses](https://arxiv.org/abs/2605.20823) | arXiv 2026 | `literature/2026_arxiv_relwitness/` | Full-PDF novelty-threat skim | direct H001 novelty threat: visual-geometric relation witnesses plus calibrated witness quality for open-vocabulary 3DSG under incomplete relation supervision; v2 numerical tables are simulated planning values |

## CAND-001 Evidence View

Date checked: 2026-05-23

| Evidence role | Papers | What they support for CAND-001 |
| --- | --- | --- |
| Direct 3DSG benchmark anchor | 3DSSG, SGGpoint, SMKA, VL-SAT, SGRec3D, Open3DSG, CCL-3DSGG | 3DSSG/3RScan, predicate R@K/mR@K, explicit edge feature modeling, spatial-knowledge relation regularization, long-tail semantic relation prediction, open-vocabulary relation prediction |
| Open-vocabulary 3D graph / robotics anchor | OVSG, ConceptGraphs, HOV-SG, OpenFunGraph, Open-Vocabulary Octree-Graph, ZING-3D, Open-World 3DSG-RAG, VIZOR | 3D graph is useful when open-vocabulary semantics must be compact, queryable, incremental, view-invariant, and usable for planning/navigation/manipulation |
| Geometry-grounding anchor | SGGpoint, SMKA, SGRec3D, FirePlace, GREAT, Octree-Graph, ZING-3D, RelWitness | Geometry/edge attributes, support hierarchy, inter-object distance, and visual-geometric witnesses can constrain semantic relations, affordances, support/contact-like reasoning, and spatial relation usability |
| LLM/VLM grounding and hallucination anchor | Open3DSG, 3D-GRAND, 3DGraphLLM, 3D-Mem, SayPlan | LLM/VLM reasoning over 3D needs structured grounding; hallucination and restrictive textual relations are explicit evaluation concerns |
| Upstream object-node proposal anchor | OpenScene, OpenMask3D, LangSplat | Open-vocabulary object/region features can supply nodes, but relation-edge grounding remains under-specified |
| Downstream alignment / registration motivation | SGAligner, SG-PGM | 3D scene graphs are used as structured inputs for scene alignment, registration, mosaicking, overlap checking, and navigation; this supports why relation reliability matters, but these are not direct relation-prediction baselines for H001 |
| Direct novelty-threat watch | RelWitness | "visual-geometric relation witnesses" and calibrated witness quality are now very recent explicit prior-art-adjacent phrases. H001 must emphasize reproduced calibrated reliability evaluation/re-ranking, source adapters, recall/violation tradeoffs, controls, and Docker metrics rather than claiming novelty from relation witnesses or calibration alone. |

## CAND-001 Alignment/Downstream Positioning Note

Date checked: 2026-05-11

| Paper | Fit to H001 | What it supports | Boundary |
| --- | --- | --- | --- |
| SGAligner | Medium problem fit, high positioning fit | Uses 3D scene graphs for partial-overlap scene alignment and downstream point-cloud registration; good evidence that 3DSG quality matters beyond label recall | It aligns existing scene graphs rather than improving predicate-level relation reliability; do not use as H001 main baseline |
| SG-PGM | Medium-high method fit, high positioning fit | Treats 3D scene graph alignment as partial graph matching and fuses semantic/geometric features; its point-matching rescoring is conceptually close to H001's calibrated re-ranking framing | Its target is graph/node/point matching and registration, not relation-edge calibration; avoid implying H001 must solve downstream alignment unless adding a separate optional experiment |

Inference:

- These papers strengthen the motivation that 3D scene graph edges should be geometrically reliable before they are reused for alignment, registration, navigation, or mapping.
- They should appear in related work under `3D scene graph downstream use / alignment / semantic-geometric fusion`, not under direct 3DSSG relation-prediction baselines.
- If H001 later adds a downstream sanity check, the clean question is whether geometry-consistency-filtered or re-ranked relation edges improve alignment robustness. This should remain optional until Open3DSG second-source relation evidence is complete.

## H001 Final Related Work Promotion Decision

Date checked: 2026-05-23

| Paper | Fit to H001 | What it changes | Required H001 response |
| --- | --- | --- | --- |
| RelWitness | Required direct novelty-threat citation | Makes visual-geometric relation witnesses and calibrated witness quality for open-vocabulary 3DSSG an explicit recent topic; full-PDF skim confirms all numerical tables are simulated planning values | Cite in geometry/reliability Related Work. Do not claim novelty as relation witnesses, geometry verification, or first calibrated witness quality. |
| VIZOR | Required boundary citation | Proposes training-free viewpoint-invariant zero-shot 3D scene graph generation from raw 3D scenes, with object-centric spatial relations and open-vocabulary spatial/proximity edges | Cite in open-vocabulary/spatial-relation boundary. H001 should not claim viewpoint-invariant zero-shot 3DSG generation or relative-horizontal relation resolution. |
| ZING-3D | Keep as final trend citation | Uses VLMs for zero-shot incremental 3DSG with 3D grounding and inter-object distance edges, on Replica/HM3D | Cite once in the open-vocabulary/VLM 3DSG trend paragraph. It supports timeliness and Qwen-VL-source motivation, not H001 metric claims. |
| Open-World 3DSG-RAG | Keep as final broad-boundary citation | Connects open-world 3DSG to retrieval-augmented reasoning across 3DSSG/Replica and downstream QA, grounding, retrieval, and planning | Cite once as a broad open-world/RAG boundary. Do not broaden H001 into RAG/task-reasoning without separate experiments. |
| View-on-Graph | Keep as final downstream citation | Uses scene graphs as an externalized spatial-information interface for zero-shot 3D visual grounding | Cite once as downstream graph-mediated reasoning motivation. It is not a relation-prediction or reliability baseline. |

Inference:

- The reference set was too thin for a top-tier Related Work section if it only cited core 3DSSG and the two reproduced sources.
- The final H001 Related Work should retain all five recent citations but assign them different roles: one direct novelty threat, one spatial-relation boundary, one VLM/incremental trend, one open-world/RAG boundary, and one downstream grounding motivation.
- The strongest pressure is not "H001 is invalid"; it is that the paper must separate itself from relation-witness/generation/downstream systems by leaning on calibrated evaluation, source-agnostic re-ranking, denominator transparency, and controls.

## CAND-003 Evidence View

Date checked: 2026-04-30

| Evidence role | Papers | What they support for CAND-003 |
| --- | --- | --- |
| 3DSG-to-LLM task planning anchor | SayPlan, SG-Nav, Relationship-Aware Hierarchical 3D Scene Graph | 3DSG is already used as LLM/VLM task context for planning, navigation, object search, and feasibility reasoning. |
| Open-vocabulary graph system anchor | OVSG, ConceptGraphs, HOV-SG | Open-vocabulary 3D graphs are useful for free-form query grounding and planning, but broad mapping/planning systems are too large for first CAND-003 reproduction. |
| Geometry-aware refinement anchor | FirePlace, RieMind, 3D-VCD | The strongest CAND-003 gap is explicit geometry-based verification/refinement of LLM/VLM task outputs, not simply giving graph text to an LLM. |
| 3D-LLM representation and memory anchor | 3DGraphLLM, Scene-LLM, 3D-Mem | LLM/VLM 3D reasoning benefits from structured scene representations, but textual/object-centric scene graphs can miss nuanced spatial geometry. |
| Evaluation / hallucination anchor | MSQA/MSNN, 3D-GRAND/3D-POPE, HEAL, SymSearch | Candidate metrics include situated QA accuracy, next-step navigation success, hallucination/over-affirmation, invalid decision rate, and search efficiency. |
| Retrieval-reasoning boundary | SGR3 | Retrieval/RAG can generate semantic 3D scene graphs, but CAND-003 should stay focused on task-output verification unless the direction shifts. |

## CAND-003 Intake Priority Decision

Date decided: 2026-04-29

Goal: CAND-003을 `geometry-aware refinement of LLM/VLM task reasoning on 3DSG`로 조사하되, CAND-001의 relation verifier와 연결 가능한 offline first prototype을 찾는다.

### Selected Order

| Rank | Paper | Decision | Reason |
| --- | --- | --- | --- |
| 1 | RieMind | Intake completed | explicit 3DSG와 structured geometric tools로 LLM spatial reasoning을 수행한다. CAND-003의 가장 가까운 direct competition이다. |
| 2 | 3D-VCD | Intake completed | distorted 3D scene graph와 geometric perturbation으로 3D-LLM hallucination을 줄인다. 최신 hallucination mitigation boundary다. |
| 3 | SayPlan | Intake completed | 3DSG + LLM task planning의 foundational robotics paper다. semantic search와 iterative replanning precedent를 제공한다. |
| 4 | SG-Nav | Intake completed | online 3DSG prompting과 hierarchical CoT를 object navigation benchmark로 연결한다. |
| 5 | SCOUT / SymSearch | Intake completed | relational semantic reasoning을 object search utility로 distill하고 symbolic benchmark를 제안한다. |
| 6 | 3DGraphLLM + 3D-Mem | Intake completed | graph-to-LLM representation과 object-centric textual 3DSG limitation을 정리하는 데 중요하다. |
| 7 | MSQA + 3D-GRAND | Evaluation-support intake | situated reasoning, next-step navigation, 3D hallucination metric을 정리한다. |
| 8 | ConceptGraphs + OVSG + HOV-SG | Broad system references | robotics/open-vocabulary motivation은 강하지만 first reproduction target으로는 범위가 크다. |

### Decision Rationale

- Directness to CAND-003: `RieMind`, `3D-VCD`, `SayPlan`.
- Search/navigation benchmark path: `SG-Nav`, `SCOUT/SymSearch`.
- Evaluation support: `MSQA/MSNN`, `3D-GRAND/3D-POPE`, `HEAL`.
- Scope risk: `ConceptGraphs`, `OVSG`, `HOV-SG` are important but can pull the project into full mapping/planning systems.
- Recommended first cut: offline spatial QA / graph query verification before embodied simulation or robot execution.

## P0 Intake Priority Decision

Date decided: 2026-04-28

Goal: CAND-001을 `geometry-grounded verification and representation of open-vocabulary 3D scene graph relations`로 좁히기 위해, paper folder를 추가로 만들 때의 우선순위를 정한다.

### Selected Order

| Rank | Paper | Decision | Reason |
| --- | --- | --- | --- |
| 1 | VL-SAT | Intake first | 3DSSG/point cloud 기반에서 visual-language semantics와 3D geometry를 함께 training에 넣는다. CAND-001의 "semantic relation + geometry evidence" 문제와 가장 직접적으로 맞닿아 있다. |
| 2 | SGGpoint | Intake second | EdgeGCN과 multi-dimensional edge feature로 relation edge를 명시적으로 모델링한다. CAND-001의 edge schema와 verifier 설계의 closed-set baseline 근거가 된다. |
| 3 | Open-Vocabulary Functional 3D Scene Graphs | Intake third | 기존 spatial 3DSG의 한계를 functional relation으로 확장한다. CAND-001이 functional predicate까지 확장해야 하는지 판단하는 핵심 경쟁축이다. |
| 4 | Open-Vocabulary Octree-Graph | Intake fourth, completed | graph edge가 spatial relation을 담는 open-vocabulary representation이다. 다만 primary contribution은 octree/map representation이라 CAND-001의 first baseline보다는 비교/positioning 근거에 가깝다. |
| 5 | OVSG | Intake after core baselines | free-form language query를 3D scene graph matching으로 ground한다. robotics grounding 근거는 강하지만, CAND-001의 primary evaluation보다는 downstream motivation에 가깝다. |
| 6 | ConceptGraphs | Intake after OVSG | open-vocabulary 3D graph를 LLM planning에 연결한다. relation edge를 LLM/VLM으로 생성한다는 점은 중요하지만, thesis first prototype의 reproduction target으로는 범위가 크다. |

### Decision Rationale

- Directness to CAND-001: `VL-SAT`, `SGGpoint`.
- Novelty boundary / competition: `Open-Vocabulary Functional 3D Scene Graphs`, `Open-Vocabulary Octree-Graph`.
- Robotics/downstream motivation: `OVSG`, `ConceptGraphs`.
- Implementation risk: `ConceptGraphs` and `OVSG` are useful but may pull the thesis toward planning/navigation. Keep them as secondary until the relation-edge verifier is specified.

## Reading Queue

| Priority | Topic or Paper | Why It Matters | Status |
| --- | --- | --- | --- |
| P0 | 3DSSG / 3RScan 계열 | 기본 dataset과 closed-set 3DSG 문제 설정 파악 | Read |
| P0 | Open3DSG + CCL-3DSGG | open-vocabulary relation prediction이 semantic reasoning 쪽 핵심축 | Read |
| P0 | VL-SAT | visual-language semantics와 3D geometry를 3DSSG training에 결합하는 방식 확인 | Read |
| P1 | SGAligner + SG-PGM | 3D scene graph alignment, semantic-geometric fusion, and rescoring as downstream motivation for relation reliability | Surveyed for positioning; not main H001 baseline |
| P0 | SGGpoint | edge-oriented reasoning과 multi-dimensional edge feature 확인 | Read |
| P0 | 3D Spatial Multimodal Knowledge Accumulation | 3D spatial knowledge와 symbolic/text knowledge가 relation prediction에 어떻게 쓰이는지 확인 | Read |
| P0 | SGRec3D + ToLL | geometry/topology-aware representation learning 축 확인 | SGRec3D read; ToLL selected |
| P0 | Open-Vocabulary Functional 3D Scene Graphs | functional relation이 CAND-001 범위에 들어와야 하는지 판단 | Read |
| P0 | Open-Vocabulary Octree-Graph | open-vocabulary graph representation에서 spatial relation edge가 어떻게 정의되는지 확인 | Read |
| P1 | OVSG + ConceptGraphs + HOV-SG | robotics에서 open-vocabulary 3D graph가 query/planning/navigation에 쓰이는 방식 확인 | Secondary motivation after core baselines |
| P0 | FirePlace | LLM semantic commonsense를 3D geometry constraint로 refine하는 참고축 | Read |
| P1 | FROSS + EgoSG | online/reconstruction-light 3DSG 생성 방식 확인 | FROSS read; EgoSG surveyed |
| P1 | 3D-Mem + 3DGraphLLM + 3D-GRAND | LLM/VLM 3D reasoning에서 relation representation, grounding, hallucination 평가 근거 확인 | 3D-Mem and 3DGraphLLM read; 3D-GRAND remains evaluation support |
| P1 | ReLaGS | 3DGS/language feature 기반 semantic-geometric graph 확인 | Surveyed |
| P0 | RieMind + 3D-VCD | CAND-003 direct competition: explicit 3DSG geometric tools and 3D scene-graph perturbation based hallucination mitigation | Read |
| P0 | SayPlan + SG-Nav + SCOUT/SymSearch | CAND-003 planning/search/navigation evidence: 3DSG-based task planning, online graph prompting, relational object search utility | Read |
| P1 | MSQA/MSNN + Scene-LLM | CAND-003 evaluation support: situated QA, next-step navigation, interactive 3D reasoning | Selected for CAND-003 evaluation scan |
| P1 | OVSG + ConceptGraphs + HOV-SG for CAND-003 | Open-vocabulary 3D graph systems as broad downstream motivation and scope boundary | Secondary motivation |
| P2 | OpenScene + OpenMask3D + LangSplat | CAND-001의 node proposal/upstream open-vocabulary 3D features 후보 확인 | Supporting only |
| P0 | RelWitness future-version watch | Direct novelty-threat check for visual-geometric relation witnesses, incomplete relation supervision, calibrated witness quality, and witness-consistent decoding overlap with H001 | Full-PDF novelty-threat skim complete for v2; watch for reproduced results, code, arbitrary-source adapters, `Violation@K`, and wrong-pair/shuffled-geometry controls |
| P1 | ZING-3D + Open-World 3DSG-RAG + View-on-Graph + VIZOR | Recent 2025-2026 expansion of VLM/open-world/zero-shot graph reasoning; needed to keep H001 Related Work current and claim boundary sharp | Final Related Work roles decided; no full paper folders unless a later section needs detailed reproduction or baseline analysis |
