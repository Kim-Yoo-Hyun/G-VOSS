# CAND-001: Geometry-Grounded Open-Vocabulary Relation Graph

Last updated: 2026-04-28

## Research Question

Open-vocabulary 3D relation prediction에서 LLM/VLM이 제안한 semantic relation을 3D geometry evidence로 검증/보정하면 relation hallucination을 줄이고 rare/open-set predicate 성능을 유지할 수 있는가?

## Top-Tier Evidence Scan

Date checked: 2026-04-28

Scope: AI/ML/Computer Vision/Robotics top-tier venue 중심으로 확인했다. 우선순위는 CVPR, ICCV, NeurIPS, RSS, ICRA, CoRL 논문/공식 프로젝트 페이지/공식 코드다.

### Evidence Corpus for CAND-001

| Role | Paper | Venue | Evidence for CAND-001 |
| --- | --- | --- | --- |
| Benchmark anchor | [3DSSG](https://3dssg.github.io/) | CVPR 2020 | 3D scene graph를 object-node / relation-edge로 예측하고 3DSSG/3RScan benchmark를 제공한다. |
| Edge modeling anchor | [SGGpoint](https://sggpoint.github.io/) | CVPR 2021 | EdgeGCN과 multi-dimensional edge feature를 사용해 relation edge 자체를 explicit modeling한다. |
| Semantic+geometry training anchor | [VL-SAT](https://cvpr.thecvf.com/virtual/2023/poster/22846) | CVPR 2023 Highlight | visual-language semantics, 3D geometry, long-tail relation을 함께 다룬다. |
| Spatial knowledge anchor | [3D Spatial Multimodal Knowledge Accumulation](https://openaccess.thecvf.com/content/CVPR2023/html/Feng_3D_Spatial_Multimodal_Knowledge_Accumulation_for_Scene_Graph_Prediction_in_CVPR_2023_paper.html) | CVPR 2023 | symbolic/text knowledge와 3D spatial hierarchy를 3DSSG relationship prediction에 결합한다. |
| Open-vocabulary relation anchor | [Open3DSG](https://openaccess.thecvf.com/content/CVPR2024/papers/Koch_Open3DSG_Open-Vocabulary_3D_Scene_Graphs_from_Point_Clouds_with_Queryable_CVPR_2024_paper.pdf) | CVPR 2024 | open-vocabulary object와 open-set relationship을 3D scene graph로 예측한다. |
| Open-vocabulary relation baseline | [CCL-3DSGG](https://openaccess.thecvf.com/content/CVPR2024/html/Chen_CLIP-Driven_Open-Vocabulary_3D_Scene_Graph_Generation_via_Cross-Modality_Contrastive_Learning_CVPR_2024_paper.html) | CVPR 2024 | CLIP 기반 cross-modality contrastive learning으로 novel object/predicate 3DSGG를 평가한다. |
| Robotics graph anchor | [OVSG](https://ovsg-l.github.io/) | CoRL 2023 | free-form query를 3D scene graph matching으로 ground한다. |
| Robotics graph anchor | [ConceptGraphs](https://concept-graphs.github.io/) | ICRA 2024 | 2D foundation model output을 3D graph로 fuse하고 LLM/VLM으로 relation edge를 생성한다. |
| Hierarchical open-vocab graph | [HOV-SG](https://hovsg.github.io/) | RSS 2024 | floor-room-object hierarchy와 open-vocabulary features를 결합해 language-grounded navigation에 쓴다. |
| Functional relation anchor | [Open-Vocabulary Functional 3D Scene Graphs](https://openaccess.thecvf.com/content/CVPR2025/html/Zhang_Open-Vocabulary_Functional_3D_Scene_Graphs_for_Real-World_Indoor_Spaces_CVPR_2025_paper.html) | CVPR 2025 | 기존 spatial relation 중심 3DSG의 한계를 지적하고 functional relation과 interactive element를 open-vocabulary 3DSG로 확장한다. |
| Geometry-aware reasoning anchor | [FirePlace](https://openaccess.thecvf.com/content/CVPR2025/html/Huang_FirePlace_Geometric_Refinements_of_LLM_Common_Sense_Reasoning_for_3D_CVPR_2025_paper.html) | CVPR 2025 | LLM commonsense를 3D geometric constraint로 refine하는 직접 근거다. |
| Spatial relation limitation anchor | [3D-Mem](https://openaccess.thecvf.com/content/CVPR2025/html/Yang_3D-Mem_3D_Scene_Memory_for_Embodied_Exploration_and_Reasoning_CVPR_2025_paper.html) | CVPR 2025 | object-centric 3D scene graph의 restrictive textual relationship이 nuanced spatial understanding에 약하다는 문제를 제기한다. |
| Hallucination evaluation anchor | [3D-GRAND](https://openaccess.thecvf.com/content/CVPR2025/html/Yang_3D-GRAND_A_Million-Scale_Dataset_for_3D-LLMs_with_Better_Grounding_and_CVPR_2025_paper.html) | CVPR 2025 | 3D-LLM에서 dense grounding과 hallucination benchmark의 필요성을 보여준다. |
| Graph-to-LLM anchor | [3DGraphLLM](https://openaccess.thecvf.com/content/ICCV2025/html/Zemskova_3DGraphLLM_Combining_Semantic_Graphs_and_Large_Language_Models_for_3D_ICCV_2025_paper.html) | ICCV 2025 | 3D semantic graph를 LLM 입력 표현으로 써서 3D vision-language task를 수행한다. |
| Structured open-vocab spatial graph | [Open-Vocabulary Octree-Graph](https://openaccess.thecvf.com/content/ICCV2025/html/Wang_Open-Vocabulary_Octree-Graph_for_3D_Scene_Understanding_ICCV_2025_paper.html) | ICCV 2025 | adaptive-octree node와 spatial-relation edge로 open-vocabulary 3D representation을 만든다. |

### What This Changes

- Fact: CAND-001은 top-tier 문헌 기준으로 "존재하지 않는 문제를 새로 만드는" 방향이 아니다. 이미 open-vocabulary 3DSG, robotics scene graph, LLM/VLM grounding이 빠르게 붙고 있다.
- Fact: 직접적인 경쟁축은 `Open3DSG`, `CCL-3DSGG`, `ConceptGraphs`, `OVSG`, `Open-Vocabulary Functional 3D Scene Graphs`, `Octree-Graph`다.
- Inference: CAND-001의 차별점은 open-vocabulary 3DSG 자체가 아니라, relation edge에 semantic predicate와 explicit geometry evidence를 함께 저장하고 그 consistency를 평가하는 것이다.
- Inference: 3D-Mem과 Open-Vocabulary Functional 3D Scene Graphs는 중요한 warning이다. 단순한 textual relation label이나 spatial relation label만 추가하면 "nuanced spatial/functional reasoning" 문제를 충분히 해결하지 못한다.
- User judgment needed: CAND-001을 석사 주제로 가져가려면 `functional relation`까지 포함할지, 아니면 `support/proximity/relative-position/containment` 같은 geometry-checkable predicate에 먼저 제한할지 결정해야 한다.

### After VL-SAT / SGGpoint Intake

- Date checked: 2026-04-28
- Fact: `SGGpoint` explicitly models relation edges through EdgeGCN and multi-dimensional edge features, improving object, predicate, and triplet metrics on 3DSSG-O27R16.
- Fact: `VL-SAT` uses 2D visual semantics and CLIP-aligned language semantics during training to improve 3DSSG relation prediction, especially tail predicates and unseen triplets.
- Inference: Together, these papers define the strongest closed-set baseline family for CAND-001: `SGGpoint` covers edge-oriented geometry/structure reasoning, while `VL-SAT` covers semantic assistance for long-tail relations.
- Inference: CAND-001 should not claim novelty from "using edge features" or "using visual-language semantics" alone. The novel claim must be explicit edge-level geometry evidence, provenance, and consistency verification.
- Candidate baseline role: `SGGpoint` as closed-set edge-reasoning baseline; `VL-SAT` as semantic-assisted closed-set baseline; `Open3DSG` / `CCL-3DSGG` as open-vocabulary baselines.

### After SMKA Intake

- Date checked: 2026-04-28
- Fact: `SMKA` uses 3DSSG, 160 object categories, and 27 relationship classes to evaluate PredCls, SGCls, and SGDet with R@K/mR@K.
- Fact: It constructs a ConceptNet-derived hierarchical symbolic knowledge graph, adds support hierarchy tokens/edges, builds a hierarchical visual graph, and accumulates visual/textual 3D spatial multimodal knowledge for relation prediction.
- Fact: It outperforms SGPN, EdgeGCN/SGGpoint, and KISG on reported PredCls and SGCls metrics, and improves head/body/tail relation R@50.
- Inference: SMKA is the clearest closed-set evidence that spatial hierarchy plus symbolic/text knowledge improves 3D relation prediction.
- Inference: CAND-001 cannot claim novelty from "adding spatial knowledge" alone. The stronger gap is that SMKA uses support hierarchy as latent regularization, while CAND-001 can expose edge-level geometry evidence and evaluate violation/consistency.
- Candidate baseline role: `SMKA` as spatial-knowledge closed-set baseline; compare against or cite it when motivating explicit support/contact/proximity evidence.

### After OpenFunGraph Intake

- Date checked: 2026-04-28
- Fact: `OpenFunGraph` introduces functional 3D scene graphs with object nodes, interactive element nodes, and functional relationship edges.
- Fact: It explicitly criticizes existing 3DSG methods for focusing on object nodes and spatial relationships, and compares against adapted `Open3DSG` and `ConceptGraphs` baselines.
- Fact: Functional relationships include local relations such as `handle opens door` and remote relations such as `switch controls light`.
- Inference: CAND-001 should not expand into full functional relation discovery at the beginning. That would require interactive element detection, LLM/VLM common-sense reasoning, and possibly interaction evidence.
- Inference: The safer thesis cut remains geometry-grounded verification of spatial/support/containment/proximity relation edges. Functional relationships can be a later extension, especially local functional relations where geometry evidence is meaningful.
- Candidate evaluation idea: Borrow OpenFunGraph's decomposition into node association, edge prediction, and overall triplet recall, then add geometry-consistency and violation metrics.

### After Open-Vocabulary Octree-Graph Intake

- Date checked: 2026-04-28
- Fact: `Open-Vocabulary Octree-Graph` represents each object as an adaptive-octree node and stores spatial-relation edge attributes such as semantic relation, distance, and 3D vector.
- Fact: It evaluates semantic segmentation, instance segmentation, Sr3D object retrieval, HM3DSem path planning, storage, and occupancy efficiency, but does not report 3DSSG-style predicate/triplet recall.
- Inference: This paper is a strong representation reference for CAND-001, especially for compact occupancy and explicit geometric edge attributes.
- Inference: It should not be treated as the first direct baseline for CAND-001 unless the thesis shifts toward object retrieval, path planning, or scene-map representation.
- Candidate schema update: CAND-001 can borrow `distance`, `3D vector`, `occupancy query`, and `world-coordinate relation` as geometry evidence fields, while still evaluating relation-edge correctness and geometry violation separately.
- Candidate boundary: Do not turn CAND-001 into a full Octree-Graph-style map/planning system before the relation verifier is specified.

## CAND-001 Synthesis Pass

Date synthesized: 2026-04-28

### Synthesis Verdict

CAND-001 is ready to move from literature intake to problem formulation. The accumulated evidence is sufficient to define a narrow thesis problem, but not yet sufficient to begin experiments without dataset/code access checks.

Recommended formulation:

> Geometry-grounded verification and representation of open-vocabulary 3D scene graph relations.

Practical thesis statement:

> Given object instances and candidate semantic relations in a 3D indoor scene, construct relation edges that store both semantic predicate information and explicit geometry evidence, then verify/refine those relations using geometry-consistency checks.

This should not be framed as:

- another open-vocabulary 3D scene graph predictor;
- a generic semantic + geometry fusion model;
- a robotics map or planning system;
- full functional 3DSG discovery.

### Evidence Compression

| Evidence axis | Main papers | What is already solved | Remaining gap for CAND-001 |
| --- | --- | --- | --- |
| Benchmark / problem setting | 3DSSG, SGRec3D | 3DSSG/3RScan gives object-node and relation-edge benchmark with R@K/mR@K style comparability. | Closed-set labels do not evaluate whether predicted relations are geometrically valid. |
| Edge-centered modeling | SGGpoint | EdgeGCN and multi-dimensional edge features make relation edges first-class model components. | Edge features are latent; output edge does not expose inspectable geometry evidence or violation status. |
| Spatial / symbolic knowledge | SMKA | Support hierarchy, ConceptNet-derived symbolic knowledge, visual context, and graph reasoning improve 3DSSG relation prediction. | Spatial knowledge is used as latent regularization; it is not an explicit verifier attached to each relation edge. |
| Visual-language semantics | VL-SAT | 2D visual semantics and CLIP-aligned language features improve long-tail and unseen relation triplets. | Semantic assistance does not guarantee geometry consistency of relation edges. |
| Open-vocabulary 3DSG | Open3DSG, CCL-3DSGG | Open-vocabulary or zero-shot object/predicate settings are active and have baselines. | Open-vocabulary relation prediction is still mostly evaluated as label recall, not as grounded relation validity. |
| Geometry-aware LLM/VLM reasoning | FirePlace | 3D geometric constraints can refine LLM common-sense reasoning. | It is not a general 3DSG relation-edge representation or 3DSSG benchmark method. |
| Functional / structured open-vocab graphs | OpenFunGraph, Octree-Graph | Functional relation graphs and compact spatial graph representations are already active directions. | CAND-001 must stay focused on edge-level verification, not broaden into functional relation discovery or map/planning systems. |

### Core Gap

Existing work can predict 3D scene graph relations, improve them with edge features, inject spatial/symbolic knowledge, or use VLM/LLM semantics. What remains under-specified is an edge representation and evaluation protocol where each semantic relation is paired with explicit, inspectable 3D geometric evidence.

The gap is not:

- "3D scene graph uses geometry";
- "open-vocabulary 3D scene graph";
- "spatial knowledge helps relation prediction";
- "LLM/VLM can reason over 3D graphs".

The gap is:

> Relation edges do not usually expose why they are geometrically valid, which geometric constraint they satisfy or violate, and how much the semantic relation should be trusted given observed 3D evidence.

### Proposed Edge Schema V1

```text
edge(i, j):
  nodes:
    subject_id
    object_id
    subject_label_or_text
    object_label_or_text

  semantic_relation:
    predicate_label_or_text
    predicate_family
    semantic_confidence
    proposal_source
    vocabulary_status

  geometry_evidence:
    center_delta_xyz
    distance_3d
    distance_xy
    vertical_order
    bbox_iou_3d
    bbox_containment_ratio
    projected_overlap_xy
    contact_or_near_contact_score
    support_surface_score
    relative_orientation
    same_room_or_region
    same_support_context
    occupancy_free_space_between

  verification:
    expected_geometry_constraints
    satisfied_constraints
    violated_constraints
    geometry_score
    calibrated_edge_confidence
    uncertainty

  provenance:
    geometry_source
    semantic_source
    instance_source
    scan_id
    timestamp_or_view_ids
```

Field notes:

- `predicate_family` should group predicates into geometry-checkable families, not only dataset labels.
- `proposal_source` can be `ground_truth_label`, `closed_set_model`, `open_vocab_model`, `LLM`, or `VLM`.
- `vocabulary_status` can be `seen`, `zero_shot`, `open_text`, or `mapped_to_closed_set`.
- `expected_geometry_constraints` should be generated from predicate family, e.g. support predicates require vertical ordering and near-contact.
- `calibrated_edge_confidence` should combine semantic confidence and geometry score, but both raw components must remain visible.

### Predicate Subset V1

Start with geometry-checkable predicates where a verifier can be implemented without solving full common-sense reasoning.

| Predicate family | Example predicates | Geometry evidence | Priority | Reason |
| --- | --- | --- | --- | --- |
| Support / contact | `standing on`, `lying on`, `supported by`, `on` | vertical order, surface proximity, contact/near-contact, projected overlap, support surface score | P0 | Central to 3DSSG and SMKA; strong geometry signal. |
| Proximity | `near`, `next to`, `close to` | 3D distance, XY distance, normalized distance by object size, same room/region | P0 | Common in 3DSSG; useful for retrieval; easier to verify. |
| Relative position | `left`, `right`, `in front of`, `behind`, `above`, `below` | world/camera coordinate frame, center delta, heading-aware relation, vertical order | P0 | Important but coordinate-frame sensitive; needs explicit frame definition. |
| Containment / enclosure | `inside`, `surrounding`, `contained in` | bbox containment, point containment, occupancy overlap, enclosure geometry | P1 | Valuable but harder with partial scans and open objects. |
| Attachment-like local relation | `attached to`, `mounted on`, `hanging on` | contact, normal/orientation, surface proximity, height prior | P1 | Geometry-checkable in some cases, but labels may be sparse/noisy. |
| Comparative geometry | `bigger than`, `smaller than`, `higher than` | bbox size, volume, height, centroid | P2 | Easy to compute but less aligned with semantic hallucination problem. |
| Functional relation | `opens`, `controls`, `used for` | part geometry, affordance cues, interaction evidence | Out of first scope | OpenFunGraph shows this is a separate active problem. |
| Pure semantic/common-sense relation | `same as`, `belonging to`, `made of` | weak or indirect geometry | Out of first scope | Not enough direct geometry evidence for first verifier. |

Recommended first subset:

- support/contact;
- proximity;
- relative position;
- limited containment if labels and geometry are reliable.

Do not start with full 3DSSG predicate space. The first experiment should report both full benchmark compatibility and a geometry-checkable subset result.

### Baseline Table

| Baseline type | Candidate papers / systems | Role in CAND-001 | Reproduction priority |
| --- | --- | --- | --- |
| Dataset / metric anchor | 3DSSG / 3RScan | Defines object-node / relation-edge setup and closed-set relation labels. | P0 |
| Closed-set 3DSG baseline | SGPN, SGFN, SGRec3D | Standard comparison family if code/results are available. | P1 |
| Edge reasoning baseline | SGGpoint | Shows strong precedent for edge-oriented modeling. | P0 paper-level; P1 reproduction |
| Spatial knowledge baseline | SMKA | Strongest warning that spatial hierarchy + symbolic knowledge is already done. | P0 paper-level; P1 reproduction if code becomes available |
| Semantic-assisted baseline | VL-SAT | Shows VLM/CLIP semantics improve long-tail/unseen triplets. | P0 paper-level; P1 reproduction |
| Open-vocabulary 3DSG baseline | Open3DSG, CCL-3DSGG | Main comparison for open-vocabulary object/predicate setting. | P0 paper-level; P1 reproduction |
| Geometry constraint reference | FirePlace | Supports using 3D constraints to correct LLM/VLM common-sense errors. | Reference only |
| Functional boundary | OpenFunGraph | Shows functional 3DSG is active and should not be absorbed into first prototype. | Boundary/reference |
| Representation boundary | Octree-Graph | Provides compact geometry evidence inspiration: distance, vector, occupancy. | Boundary/reference |
| Robotics motivation | OVSG, ConceptGraphs, HOV-SG | Motivates graph query/planning, but broadens scope. | Later |

### Minimal Evaluation Plan

Primary evaluation should be offline and relation-edge centered.

1. Use 3DSSG / 3RScan with ground-truth instances or reliable instance masks.
2. Generate candidate semantic relations from one of:
   - ground-truth labels for upper-bound verifier analysis;
   - closed-set baseline predictions;
   - Open3DSG / CCL-3DSGG-style open-vocabulary predictions;
   - controlled LLM/VLM relation proposals after baseline feasibility is known.
3. Compute geometry evidence for each candidate edge.
4. Verify or re-score each relation using predicate-family constraints.
5. Report standard relation metrics and geometry metrics together.

Primary metrics:

| Metric | Purpose |
| --- | --- |
| Predicate R@K / mR@K | Maintain comparability with 3DSSG baselines. |
| Triplet R@K / mR@K | Check whether verified edges still preserve scene graph prediction quality. |
| Geometry consistency score | Measure whether accepted relation edges satisfy predicate-family constraints. |
| Violation rate | Measure how often predicted semantic relations contradict 3D evidence. |
| Consistency-filtered recall | Measure recall after removing geometry-invalid predictions. |
| Tail / zero-shot predicate score | Ensure geometry verification does not only improve head classes. |
| Relation-guided retrieval success | Optional downstream metric after edge verification works. |

Important evaluation principle:

> A method that increases recall but also increases geometry violations is not clearly better for CAND-001. A method that keeps recall similar but reduces violations can be a valid contribution if the evaluation makes that tradeoff explicit.

### Minimum Viable Prototype

The first prototype should be deliberately narrow.

1. Dataset: 3DSSG / 3RScan.
2. Input: ground-truth object instances and candidate relation labels.
3. Predicate subset: support/contact, proximity, relative position.
4. Geometry features:
   - object centers and bounding boxes;
   - 3D/XY distance;
   - vertical ordering;
   - projected overlap;
   - bbox containment;
   - near-contact threshold;
   - same room/region if available.
5. Verifier:
   - rule-based geometry verifier first;
   - learned calibrator second, only if rule baseline is meaningful.
6. Output:
   - original semantic relation;
   - geometry evidence;
   - satisfied/violated constraints;
   - calibrated confidence.
7. Metrics:
   - predicate/triplet recall;
   - violation rate;
   - consistency-filtered recall.

This prototype is enough to test whether CAND-001 has signal before reproducing broader open-vocabulary systems.

### Remaining Gap After Synthesis

Research gap:

- Need a relation-edge representation that keeps semantic relation, geometry evidence, confidence, and violation status together.
- Need evaluation that treats geometry consistency as a first-class outcome, not a qualitative comment.
- Need a controlled predicate subset where geometric validity can be measured defensibly.

Engineering gap:

- Need dataset access check for 3RScan / 3DSSG.
- Need preprocessing decision: ground-truth instances first, then predicted instances.
- Need baseline reproduction decision: whether to reproduce SGGpoint/VL-SAT/Open3DSG/CCL-3DSGG or use reported results plus a verifier on available predictions.
- Need code availability recheck for SMKA because the listed repository was inaccessible on 2026-04-28.

Scope gap:

- Do not include full functional relations until spatial/support verifier works.
- Do not include robotics navigation until relation-edge evaluation is stable.
- Do not require online RGB-D scene graph generation in the first thesis experiment.

### Go / No-Go Criteria

Go if:

- 3DSSG / 3RScan access is available;
- support/proximity/relative-position predicates can be mapped to reliable geometry constraints;
- a simple verifier reduces violation rate without destroying predicate/triplet recall;
- at least one closed-set or open-vocabulary baseline prediction source can be obtained.

No-go or pivot if:

- relation labels are too noisy to define geometry validity;
- 3RScan/3DSSG access blocks progress for too long;
- geometry evidence only reproduces trivial distance thresholds without meaningful relation improvement;
- open-vocabulary baselines cannot be run or approximated.

Pivot options:

- Narrow to closed-set `geometry-consistency evaluation for 3DSSG relations`.
- Shift to `relation-guided retrieval with evidence-bearing edges`.
- Shift to robotics motivation only after OVSG/ConceptGraphs/HOV-SG intake and dataset feasibility checks.

## Baseline Code Feasibility Check

Date checked: 2026-04-28

Scope restriction:

- 3DSSG / 3RScan acquisition route is known by the user and official access/layout documents were checked.
- Actual dataset download, unpacking, and local file validation were not performed in this pass.
- No `docs/hypothesis.md` or hypothesis workflow was created.
- This pass checked public code availability, repository shape, environment burden, dataset access path, expected layout, and likely baseline role.

### Summary Verdict

The most practical near-term path is not to reproduce all baselines. Start with an offline verifier using 3DSSG-style ground-truth or baseline relation outputs when data access is allowed, then decide whether a full baseline reproduction is necessary.

Reproduction priority:

1. `VL-SAT`: best practical closed-set codebase candidate.
2. `Open3DSG`: important open-vocabulary proposal model, but heavy and archived; use after first verifier works.
3. `SGGpoint`: strong conceptual baseline, but standalone official repo is too partial for first reproduction.
4. `CCL-3DSGG`: paper-level baseline only unless code is found.

### Repository Feasibility Table

| Target | Official code status | Checked evidence | Feasibility for CAND-001 | Decision |
| --- | --- | --- | --- | --- |
| SGGpoint | Public official repo: `chaoyivision/SGGpoint` | Repo contains `EdgeGCN.py`, `SubNetworks.py`, preprocessing scripts, and dataset preprocessing guidance. It does not look like a complete one-command train/eval reproduction package. | Medium-low for direct reproduction; high as conceptual edge-modeling baseline. | Use as paper-level baseline first. Prefer VL-SAT repo if SGGpoint-style code is needed, because VL-SAT includes an SGGpoint model folder. |
| VL-SAT | Public official repo: `wz7in/CVPR2023-VLSAT` | README provides dependencies, default config, train/eval commands, 3DSSG/3RScan preparation, multi-view generation, CLIP adapter, and checkpoint link. | Medium. Old CUDA/PyTorch/PyG stack and data preparation are non-trivial, but this is the most complete closed-set candidate. | First reproduction candidate after data access is allowed. |
| Open3DSG | Public official repo: `boschresearch/Open3DSG`; archived on 2026-02-19 | README provides setup, preprocessing, training, testing, ScanNet/3RScan/3DSSG requirements, OpenSeg/BLIP2/PointNet weights, and optional 300GB-per-dataset feature dumping. | Medium-low for first reproduction. It is the right open-vocabulary baseline, but setup is heavy and repo is read-only. | Use as open-vocabulary proposal reference first; reproduce only after the verifier prototype works. |
| CCL-3DSGG | No official code found in this pass | CVF page provides paper/PDF only. GitHub repository searches for title and `CCL-3DSGG` did not find a matching official repo. | Low. Cannot plan reproduction without code or author release. | Keep as paper-level open-vocabulary/zero-shot baseline. Recheck later. |

### Practical Implications

For CAND-001, the first experimental target should not depend on running Open3DSG or CCL-3DSGG end-to-end. A safer sequence is:

1. Use ground-truth relation labels or saved baseline predictions as semantic proposals.
2. Implement geometry evidence extraction and verification.
3. Measure violation rate and consistency-filtered recall on a geometry-checkable predicate subset.
4. Only then integrate a full learned baseline such as VL-SAT or Open3DSG.

### Environment / Engineering Risks

- `VL-SAT` depends on Python 3.8, PyTorch 1.12.1 + CUDA 11.3, PyTorch Geometric packages, OpenAI CLIP, Open3D, and 3DSSG/3RScan preprocessing.
- `Open3DSG` depends on Python 3.9, PyTorch 2.0.1 + CUDA 11.8, OpenSeg, BLIP2 positional embedding, PointNet/PointNet2 weights, ScanNet, 3RScan, 3DSSG, and possibly hundreds of GB of precomputed 2D features.
- `SGGpoint` official repo is useful for EdgeGCN/preprocessing references but appears incomplete for direct reproducibility.
- `CCL-3DSGG` currently has no public official code path.

### Updated Baseline Strategy

| Stage | Baseline source | Why |
| --- | --- | --- |
| Stage 0: verifier sanity check | Ground-truth relations or hand-exported predictions | Tests whether geometry evidence has signal without baseline engineering overhead. |
| Stage 1: closed-set learned baseline | VL-SAT, with SGGpoint as conceptual/ablation reference | Most complete accessible code path among closed-set semantic/edge baselines. |
| Stage 2: open-vocabulary proposal baseline | Open3DSG | Strong fit for semantic relation proposal, but heavy setup. |
| Stage 3: paper-only comparison | CCL-3DSGG, SMKA, OpenFunGraph, Octree-Graph | Important for positioning but not first reproduction target. |

### Next Feasibility Step

When dataset access is allowed, check in this order:

1. Whether 3DSSG/3RScan can be downloaded and organized into the VL-SAT expected layout.
2. Whether a small subset can run through VL-SAT eval mode.
3. Whether predicted relation outputs can be exported in a format usable by the CAND-001 verifier.
4. Whether Open3DSG can be run only for inference or proposal generation without full retraining.

## Dataset Access and Layout Feasibility

Date checked: 2026-04-28

Status:

- User confirms the 3DSSG / 3RScan acquisition route is known.
- Official documentation was checked for expected files and baseline-specific layout.
- Local download and checksum/file-presence validation are pending.

### Official Dataset Route

3RScan:

- Official source: `WaldJohannaU/3RScan`.
- Access requires agreeing to the 3RScan Terms of Use and obtaining the official download script.
- The 3RScan folder is organized by scan id.
- Files relevant to CAND-001 and baselines include:
  - `labels.instances.annotated.v2.ply`;
  - `semseg.v2.json`;
  - `mesh.refined.v2.obj`;
  - `sequence.zip` if RGB-D frames, poses, and intrinsics are needed;
  - `3RScan.json` metadata and train/val/test split files.

3DSSG:

- Official source: `3DSSG/3DSSG.github.io`.
- `3DSSG.zip` contains the full graph annotation files:
  - `objects.json`;
  - `relationships.json`;
  - `classes.txt`;
  - `relationships.txt`;
  - attributes / affordance metadata.
- `3DSSG_subset.zip` contains the common train/validation subset used by many baselines:
  - `relationships.json`;
  - `relationships_train.json`;
  - `relationships_validation.json`;
  - `classes.txt`;
  - `relationships.txt`.

### Baseline-Specific Layout Expectations

VL-SAT expects:

```text
data/
  3DSSG_subset/
    relations.txt
    classes.txt
    relationships.json
    relationships_train.json
    relationships_validation.json
    train_scans.txt
    validation_scans.txt
  3RScan/
    <scan_id>/
      multi_view/
      labels.instances.align.annotated.v2.ply
      labels.instances.annotated.v2.ply
      semseg.v2.json
      ...
```

VL-SAT notes:

- It follows the 3DSSG preparation route.
- It needs multi-view 2D images generated from point clouds.
- It uses `pointcloud2image.py`.
- It may need `labels.instances.align.annotated.v2.ply`, generated through the data processing scripts.

Open3DSG expects:

```text
<data_root>/
  3RScan/
    <scan_id>/
      3DSSG_subset files as subdirectory or colocated annotation files
      image sequences unpacked where needed
  ScanNet/
    scannet_2d/
    scannet_3d/
  checkpoints/
    OpenSeg checkpoint
    BLIP2 positional embedding
    PointNet / PointNet2 weights
```

Open3DSG notes:

- It uses both 3RScan/3DSSG and ScanNet in its full pipeline.
- It can require 2D-3D feature preprocessing.
- The README warns that optional 2D feature dumping can require about 300GB per dataset.

SGGpoint expects:

- Either the authors' preprocessed `3DSSG-O27R16` dataset or self-derived preprocessing from raw 3RScan + 3DSSG.
- The official repo provides preprocessing references, but direct train/eval reproduction still looks less complete than VL-SAT.

CCL-3DSGG:

- Dataset requirements are paper-level only in this pass because no official code was found.
- Keep as a paper-level baseline until code or prediction outputs are available.

### Local Validation Checklist

When data is actually placed in the workspace or external data path, validate the following before hypothesis workflow starts:

```text
3RScan root exists
3DSSG_subset exists
relationships_train.json exists
relationships_validation.json exists
classes.txt exists
relationships.txt exists
at least one scan_id folder exists
labels.instances.annotated.v2.ply exists for a sample scan
semseg.v2.json exists for a sample scan
labels.instances.align.annotated.v2.ply exists or generation script is available
train/validation split files are present or reproducible
```

Local workspace check on 2026-04-28:

- No `3RScan` or `3DSSG_subset` directory was found under `/home/yoohyun/research`.
- No `3RScan` or `3DSSG_subset` directory was found under `/home/yoohyun` within `maxdepth 4`.
- Therefore, dataset acquisition route is known, but local dataset validation is still pending.

### Updated Feasibility Verdict

Dataset access is no longer the conceptual blocker because the acquisition route is known. The remaining practical blocker is local validation and baseline-specific preprocessing.

Recommended next order before `docs/hypothesis.md`:

1. Confirm local dataset root path.
2. Validate the file checklist above on 1-2 scan ids.
3. Choose first executable path:
   - `VL-SAT eval` if preprocessed data and checkpoint are ready;
   - CAND-001 verifier on ground-truth `3DSSG_subset` relations if baseline eval is not ready.
4. Then design `docs/hypothesis.md` around the feasible first experiment.

## Closed-set 3DSG Problem Setting

기본 problem setting은 3D indoor scene의 object instance를 node로, object-object relation을 edge로 두고, point cloud / RGB-D / instance mask에서 object label과 predicate label을 예측하는 것이다.

- Canonical dataset: 3DSSG built on 3RScan.
- Original 3DSSG paper reports 1482 scans from 478 changing indoor environments, 48k object nodes, 544k edges, 534 object classes, 40 object relationships, and 93 attributes.
- Later benchmark settings often use reduced label spaces, e.g. 160 object classes and 27 relationship categories in SGRec3D/Open3DSG discussions, or 26 predicate classes in CCL-3DSGG.
- Typical evaluation: object R@K, predicate R@K, relationship triplet R@K, and mR@K for class imbalance.
- Common baselines: 3DSSG, SGGPoint, SGFN, SGRec3D, VL-SAT.
- Known issue: closed-set labels make evaluation clean, but they restrict rare/open-set semantic relations and do not directly measure geometric consistency.

### 3DSSG Relation Taxonomy

3DSSG relations are useful for CAND-001 because they are not purely linguistic labels.

- Spatial / proximity: e.g. `next to`, `in front of`.
- Support: support candidates are derived from nearby instances and then semantically verified, e.g. standing/lying support relations.
- Comparative: derived from attributes, e.g. bigger than, darker than, same shape as.

This taxonomy suggests a staged verifier: start with support/proximity predicates, then handle comparative and affordance-like predicates later.

### Why Closed-set Still Matters

CAND-001 should not skip closed-set 3DSG. A practical thesis can first evaluate on 3DSSG because it gives baseline comparability, then add open-vocabulary or geometry-consistency checks on top. The closed-set benchmark is the anchor; the contribution is the semantic+geometric edge evidence beyond the label.

## Feasibility Notes for CAND-001

### Candidate Verdict

`CAND-001: Geometry-Grounded Open-Vocabulary Relation Graph` is feasible as a thesis direction if the scope is kept to edge-level relation verification/refinement, not full scene reconstruction, robot deployment, or general 3D-LLM reasoning.

### Minimum Viable Thesis Shape

1. Use an existing 3DSG pipeline or ground-truth instance masks.
2. Produce semantic relation proposals from an open-vocabulary source such as Open3DSG or a controlled VLM/LLM prompt.
3. Compute explicit geometry evidence for each candidate edge.
4. Refine/filter relations using geometry evidence.
5. Evaluate relation accuracy and geometry consistency.

### Candidate Edge Schema

This initial schema is superseded by `Proposed Edge Schema V1` in the synthesis pass above, but remains as a compact summary.

```text
edge(i, j):
  semantic_relation:
    label_or_text
    confidence
    source
  geometry_evidence:
    relative_position
    distance
    bbox_overlap_or_containment
    vertical_support
    contact_or_near_contact
    orientation_or_normal_alignment
    room_or_topological_context
  consistency:
    geometry_score
    violated_constraints
    uncertainty
```

### Datasets

| Dataset | Use | Risk |
| --- | --- | --- |
| 3DSSG / 3RScan | Main benchmark and primary first prototype | Access friction; labels are closed-set; relation set may not cover all open-vocab relations |
| ScanNet | Open3DSG distillation / extra 3D data | Does not provide native 3DSG relation labels |
| ReplicaSSG | Secondary online/Replica-based relation benchmark from FROSS | Newer dataset; relation quality depends on 2D SG; Gaussian geometry may be too coarse for fine support/contact |
| SceneFun3D / FunGraph3D | Optional functional relation benchmark if CAND-001 expands beyond spatial predicates | Scope can become manipulation/affordance-heavy rather than core 3DSG relation verification; best used only after spatial verifier works |
| Synthetic or manually filtered subset | Geometry violation evaluation for support/contact/containment | Risk of being seen as too narrow unless tied to real 3DSG data |

### Metrics

| Metric | Purpose |
| --- | --- |
| Object R@K / Predicate R@K / Triplet R@K | Compatibility with 3DSSG baselines |
| mR@K | Head/body/tail class balance |
| Zero-shot predicate recall | Open-vocabulary relation value |
| Geometry consistency score | Whether predicted relation is supported by 3D evidence |
| Violation rate | Fraction of semantic relations contradicted by geometry |
| Relation-guided retrieval/query success | Downstream usefulness of semantic+geometry graph |
| Grounding / hallucination score | Whether language-derived relation edges are grounded in observed 3D evidence |

### Baselines

- Closed-set: 3DSSG, SGFN, SGRec3D, VL-SAT.
- Edge reasoning / spatial knowledge: SGGpoint, 3D Spatial Multimodal Knowledge Accumulation.
- Open-vocabulary 3DSG: Open3DSG, CCL-3DSGG, ConceptGraphs, OVSG.
- Functional / structured open-vocabulary graph: Open-Vocabulary Functional 3D Scene Graphs, Open-Vocabulary Octree-Graph.
- Geometry/tool reference: FirePlace constraint functions, SGRec3D reconstruction verification.
- LLM/grounding reference: 3D-Mem, 3D-GRAND, 3DGraphLLM.
- Online reference if needed: FROSS, Incremental 3D Semantic Scene Graph Prediction.

### Recommended Scope After Top-Tier Scan

1. Primary dataset: 3DSSG / 3RScan.
2. Primary predicate subset: geometry-checkable support, proximity, relative position, containment/attachment-like relations.
3. Primary baselines: SGGpoint/VL-SAT/SGRec3D for closed-set and edge/semantic-geometric learning, Open3DSG and CCL-3DSGG for open-vocabulary relation prediction.
4. Primary contribution: add explicit geometry evidence and consistency checking to relation edges.
5. Secondary benchmark: FROSS / ReplicaSSG only after the offline verifier is stable.
6. Do not make ConceptGraphs/HOV-SG the first reproduction target; use them as robotics/downstream motivation unless the thesis shifts to planning/navigation.
7. Do not include full OpenFunGraph-style functional relation discovery in the first prototype; only consider local functional relations as an optional extension.

### Updated Verdict After Top-Tier Evidence Scan

CAND-001 is defensible, but the thesis must be formulated narrowly because top-tier work already covers open-vocabulary 3DSG, robotics 3D scene graphs, and graph-to-LLM reasoning. The strongest formulation is:

> Geometry-grounded verification and representation of open-vocabulary 3D scene graph relations.

The key novelty should be an edge-level representation and evaluation protocol, not merely another open-vocabulary relation classifier or another LLM-on-3DSG pipeline.

### Main Risk

The contribution can become too broad if it tries to solve open-vocabulary SGG, geometry reconstruction, LLM reasoning, and downstream robotics at once. The safer thesis cut is:

> Given object instances and candidate semantic relations, learn or compute geometry-grounded edge evidence that improves relation reliability.

### Next Research Decision

The P0 intake priority decision and CAND-001 synthesis pass are complete.

Recommended next intake order:

1. `VL-SAT`: completed as `literature/2023_cvpr_vl-sat/`.
2. `SGGpoint`: completed as `literature/2021_cvpr_sggpoint/`.
3. `Open-Vocabulary Functional 3D Scene Graphs`: completed as `literature/2025_cvpr_openfungraph/`.
4. `Open-Vocabulary Octree-Graph`: completed as `literature/2025_iccv_octree-graph/`.
5. `3D Spatial Multimodal Knowledge Accumulation`: completed as `literature/2023_cvpr_smka/`.
6. `OVSG`: robotics grounding motivation.
7. `ConceptGraphs`: robotics/planning motivation and broad open-vocabulary graph baseline.

The next concrete research-harness task should be either:

- keep literature-only scope and perform `OVSG` intake for robotics grounding motivation; or
- if CAND-001 is selected as the primary direction, create the next workflow document for hypothesis/problem formulation and start dataset/code feasibility checks.
