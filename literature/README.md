# Literature Index

Last updated: 2026-05-23

이 폴더는 3D Scene Graph 문헌 조사 결과를 저장한다. workflow와 작성 규칙은 `docs/literature.md`를 따른다.

논문별 폴더에는 가능한 경우 원문 PDF를 `paper.pdf`로 저장한다.

Latest check: 2026-05-23, focused on H001/CAND-001 novelty-threat expansion for relation-level visual-geometric evidence, open-world/open-vocabulary 3DSG, VLM-based zero-shot/incremental graph generation, and graph-mediated 3D grounding. Primary sources checked in this pass include arXiv, AAAI proceedings, and CVF Open Access.

## Files

- `PAPER.md`: paper registry와 reading queue
- `Contribution Candidates.md`: contribution candidate 목록
- `CAND-001.md`: CAND-001 세부 문제 설정과 feasibility
- `CAND-003.md`: CAND-003 세부 문제 설정과 literature survey
- `<paper-folder>/`: 논문별 PDF와 paper card

## Field Map

초기 조사 축:

| Axis | What to Investigate | Evidence Needed |
| --- | --- | --- |
| Closed-set 3D Scene Graph Generation | 고정된 object/predicate label에서의 기본 문제 설정 | 대표 dataset, metric, baseline |
| Open-vocabulary / Open-world 3DSG | 학습하지 않은 object/relation을 다루는 방법 | CLIP/VLM 활용 방식, zero-shot split |
| LLM/VLM + 3D Scene Reasoning | scene graph를 reasoning memory나 structured context로 쓰는 방식 | VQA, captioning, planning task |
| Robotics / Embodied AI | 로봇 map, navigation, manipulation에 쓰이는 구조 | online update, hierarchy, action grounding |
| Dynamic / Online / 4D Scene Graph | 시간이 지나며 변하는 scene graph 처리 | streaming input, object permanence, temporal relation |
| 3D Generation from Scene Graphs | scene graph를 3D scene synthesis control로 쓰는 방향 | controllability, relation fidelity metric |
| 3DGS / NeRF + Semantic Graph | 빠른 3D representation과 semantic graph 결합 | scene representation, query, editing |
| Semantic reasoning + Geometry-aware 3DSG | LLM/VLM/commonsense relation과 metric/topological/support/contact geometry를 함께 표현/검증 | relation grounding, geometry violation metric, semantic query success |
| LLM/VLM Task Reasoning on 3DSG | 3DSG를 LLM/VLM planning, QA, navigation, object search, placement reasoning에 쓰는 흐름 | task success, invalid decision rate, hallucination rate, geometry/tool verification |

## Trend Synthesis

### Trend: Semantic reasoning and geometry-aware modeling are converging, but not yet cleanly unified

- Date checked: 2026-04-27
- Evidence: 3DSSG, SGRec3D, Open3DSG, CCL-3DSGG, HOV-SG, FirePlace, FROSS, ReLaGS, Relationship-Aware H3DSG.
- What is changing: 초기 3DSG는 point cloud/object geometry와 closed-set relation classification에 강했고, 최근 흐름은 CLIP/VLM/LLM을 써서 open-vocabulary object/relation과 task reasoning을 추가하는 방향으로 이동 중이다.
- Why it matters: semantic relation은 LLM/VLM prior만으로는 3D geometry에 hallucination될 수 있고, geometry-only relation prediction은 open-world semantic reasoning이 약하다.
- What remains unsolved: relation edge가 "semantic predicate"와 "geometric evidence"를 함께 갖고, relation이 3D metric/topological constraint에 의해 검증되는 representation/evaluation은 아직 명확한 표준이 약하다.
- Possible thesis angle: geometry-grounded semantic relation graph. VLM/LLM이 relation을 propose하고, 3D geometry module이 support/contact/containment/relative pose/topology evidence로 verify/refine하는 3DSG.

### Trend: Robotics papers need hierarchical spatial structure; VLM papers need geometry grounding

- Date checked: 2026-04-27
- Evidence: Hydra, HOV-SG, Relationship-Aware H3DSG, SCOUT, FirePlace.
- What is changing: robot navigation/search/planning 쪽은 floor-room-object-place 같은 hierarchy와 topology가 중요하고, 최근에는 open-vocabulary feature와 LLM/VLM reasoning이 붙고 있다.
- Why it matters: task reasoning은 "cup on table" 같은 relation뿐 아니라 "reachable", "inside a room", "near a target area", "supported by stable surface" 같은 semantic+geometric predicate가 필요하다.
- What remains unsolved: task-level success와 graph-level semantic/geometric correctness를 동시에 측정하는 benchmark 설계가 약하다.

### Trend: Evaluation is shifting from label recall to grounded usability

- Date checked: 2026-04-27
- Evidence: Open3DSG, SGRec3D, FirePlace, FROSS, HOV-SG, ReLaGS.
- What is changing: Standard R@K/mR@K remains necessary, but newer work increasingly evaluates retrieval, navigation, online speed, placement quality, visibility, plausibility, or task success.
- Why it matters: A semantic+geometry 3DSG should not be judged only by whether it predicts the dataset predicate label. It should also answer whether the edge is geometrically valid and useful for downstream reasoning.
- What remains unsolved: There is no single standard metric for open-vocabulary relation grounding plus geometric consistency.
- Possible thesis angle: introduce a compact edge-level evaluation suite: relation recall, geometry violation rate, and relation-guided query success.

### Trend: Open-vocabulary benchmarks exist, but geometry-grounded open-vocabulary benchmarks are still weak

- Date checked: 2026-04-28
- Evidence: Open3DSG, CCL-3DSGG, 3DSSG, FROSS.
- What is changing: Open3DSG and CCL-3DSGG both provide ways to evaluate open-vocabulary or zero-shot relation prediction on 3DSSG-style labels.
- Why it matters: This gives CAND-001 a baseline path: compare against open-vocabulary relation predictors, then add geometry-grounded verification.
- What remains unsolved: The open-vocabulary scores still mostly reduce generated or prompted relations to fixed benchmark labels. They do not directly answer whether a relation is physically/geometrically valid in 3D.
- Possible thesis angle: evaluate "semantic recall under geometry consistency" rather than only relation recall.

### Trend: LLM/VLM task reasoning over 3DSG is moving from graph serialization to geometry-grounded verification

- Date checked: 2026-04-29
- Evidence: SayPlan, OVSG, ConceptGraphs, HOV-SG, SG-Nav, FirePlace, 3DGraphLLM, 3D-Mem, Relationship-Aware Hierarchical 3D Scene Graph, SCOUT, RieMind, 3D-VCD.
- What is changing: 3DSG is no longer only a scene representation or relation prediction output. It is increasingly used as LLM/VLM task context, scene memory, navigation/search substrate, or tool interface.
- Why it matters: Giving graph text to an LLM is becoming baseline-level. Stronger work now asks whether the model's answer, placement, target object, or next decision is grounded in object presence, spatial layout, and metric geometry.
- What remains unsolved: Many task systems report success rate or answer accuracy, but do not cleanly separate semantic reasoning failure, perception failure, relation error, and geometry violation.
- Possible thesis angle: a task-level verifier over 3DSG relation evidence that reduces invalid/hallucinated LLM/VLM decisions and reports explicit violation metrics.

### Trend: Top-tier work is moving from object-centric open-vocabulary 3D maps to relation-aware graph reasoning

- Date checked: 2026-04-28
- Evidence: VL-SAT, Open3DSG, CCL-3DSGG, OVSG, ConceptGraphs, HOV-SG, Open-Vocabulary Functional 3D Scene Graphs, 3DGraphLLM, Octree-Graph, 3D-Mem.
- What is changing: CV/robotics papers are increasingly using graph representations not only to store objects, but also to support open-vocabulary query, navigation, planning, 3D QA, and functional reasoning.
- Why it matters: This makes CAND-001 timely, but also raises the novelty bar. A thesis cannot simply claim "open-vocabulary 3D scene graph" because that is now an active line with multiple top-tier papers.
- What remains unsolved: Relation edges are still often represented as predicted/captioned text, fixed predicate labels, or coarse spatial edges. Explicit evidence provenance and geometry-consistency evaluation for each semantic relation remains under-standardized.
- Possible thesis angle: edge-level relation verification: relation proposal from semantic models, verification/refinement from 3D geometric evidence, and evaluation by relation recall plus violation/grounding metrics.

### Trend: Visual-geometric relation evidence is becoming explicit prior art

- Date checked: 2026-05-22
- Evidence: RelWitness, Open3DSG, CCL-3DSGG, FROSS, OpenFunGraph, Open-Vocabulary Octree-Graph, ZING-3D, VIZOR.
- What is changing: Recent 3DSSG work increasingly treats relations as open-vocabulary, VLM-mediated, incomplete-supervision, or zero-shot outputs, and several papers now expose geometry-related edge attributes or relation evidence rather than only predicate labels.
- Why it matters: H001 can no longer safely claim novelty as "visual-geometric relation witnesses", "geometry evidence on relation edges", or "verification with geometry" by itself.
- What remains unsolved: A reproduced, source-agnostic reliability evaluation/re-ranking protocol with identity-preserving geometry joins, calibrated `p_geom_valid`, recall/violation operating points, source-transfer evidence, wrong-pair/shuffled-geometry controls, and denominator-transparent caveats is still a defensible narrower contribution. RelWitness has calibrated witness quality, so H001 should not claim calibration novelty by itself.
- Possible thesis angle: position H001 as a calibrated relation reliability layer and evaluation protocol, not as a new open-vocabulary 3DSG generator.
- Confidence: Medium-High. RelWitness is very direct; full-PDF skim confirms the method overlap is real, but v2 numerical tables are simulated planning values rather than reproduced results.

### Trend: Recent open-world/VLM graph systems widen the field but sharpen H001's boundary

- Date checked: 2026-05-22
- Evidence: ZING-3D, Open-World 3D Scene Graph Generation for Retrieval-Augmented Reasoning, View-on-Graph, VIZOR, SGR3, RieMind, 3DGraphLLM, 3D-Mem.
- What is changing: 3D scene graphs are increasingly used as VLM input/output, incremental scene memory, retrieval substrate, or graph-reasoning interface for grounding, QA, planning, and object search.
- Why it matters: These papers make "open-world 3D scene graph for reasoning" too broad as an H001 contribution.
- What remains unsolved: Many systems still need relation-level reliability accounting: which relation edge is geometrically valid, which source produced it, whether re-ranking reduces contradictions, and how much recall is lost.
- Possible thesis angle: keep H001 as a paper about relation-source reliability under geometry-checkable families; treat Qwen-VL and downstream task reasoning as optional extension evidence only after the core claim is stable.
- Confidence: Medium.

### Insight: Recent 2025-2026 papers should enter H001 Related Work with separated roles

- Date: 2026-05-23
- Based on: RelWitness, VIZOR, ZING-3D, Open-World 3DSG-RAG, View-on-Graph.
- Facts: RelWitness directly overlaps relation-level visual-geometric evidence and calibrated witness quality. VIZOR directly targets viewpoint-invariant zero-shot 3D scene graph generation and object-centric spatial relations. ZING-3D targets zero-shot incremental VLM-based 3DSG with depth grounding and distance-bearing edges. Open-World 3DSG-RAG broadens 3DSG to retrieval-augmented reasoning across QA/grounding/retrieval/planning. View-on-Graph uses scene graphs as the interface for zero-shot 3D visual grounding.
- Inference: All five should remain in final H001 Related Work, but not as equivalent baselines. They should be grouped as direct novelty threat, spatial-relation boundary, VLM/incremental trend, open-world/RAG boundary, and downstream grounding motivation.
- Confidence: High.

## Cross-Paper Insights

### Insight: 이 방향은 좋지만, "semantic+geometry를 결합한다"만으로는 novelty가 약하다

- Date: 2026-04-27
- Based on: 3D Scene Graph ICCV 2019, 3DSSG CVPR 2020, SGRec3D WACV 2024, Open3DSG CVPR 2024, FirePlace CVPR 2025.
- Facts: 3DSG 자체가 원래 semantic information과 3D space/geometry를 통합하려는 representation이다. 3DSSG 계열도 object/relation semantics와 point cloud geometry를 함께 사용한다.
- Inference: 따라서 contribution은 "둘을 합친다"가 아니라, "open-vocabulary semantic reasoning을 explicit 3D geometric evidence로 ground/verify/refine한다"로 좁혀야 한다.
- Confidence: High.

### Insight: Edge representation을 두 채널로 나누면 연구 질문이 선명해진다

- Date: 2026-04-27
- Based on: Open3DSG, CCL-3DSGG, FirePlace, ReLaGS, ToLL.
- Inference: node보다 edge가 핵심이다. 각 edge를 `(semantic predicate, geometry evidence, confidence, provenance)`로 표현하면 LLM/VLM hallucination, closed-set relation, geometry shortcut 문제를 동시에 다룰 수 있다.
- Example edge: `cup --on--> table` with semantic confidence, support/contact evidence, vertical relation, distance, overlap/contact ratio, viewpoint provenance.
- Confidence: Medium-High.

### Insight: Evaluation이 contribution의 성패를 좌우한다

- Date: 2026-04-27
- Based on: 3DSSG, ReplicaSSG/FROSS, Open3DSG, SCOUT.
- Inference: 기존 Recall@K/mR@K만으로는 "semantic reasoning과 geometry-aware 정보가 함께 맞는지"를 보기 어렵다. geometry violation rate, relation grounding accuracy, task/query success를 같이 설계해야 연구 기여가 선명해진다.
- Confidence: Medium.

### Insight: CAND-001 should start offline, not online

- Date: 2026-04-28
- Based on: 3DSSG, CCL-3DSGG, FROSS.
- Facts: 3DSSG gives the canonical relation labels and closed-set comparability. CCL-3DSGG gives open-vocabulary/zero-shot baselines. FROSS gives online/ReplicaSSG, but relation quality depends strongly on 2D SG quality and Gaussian geometry is approximate.
- Inference: The first thesis prototype should use 3DSSG/3RScan offline data with ground-truth or reliable instance masks. FROSS/ReplicaSSG should be secondary, after relation verification works offline.
- Confidence: High.

### Insight: Predicate subset selection is necessary

- Date: 2026-04-28
- Based on: 3DSSG relation taxonomy, SGRec3D, FROSS, FirePlace.
- Inference: A geometry verifier should not attempt all predicates immediately. It should start with geometry-checkable predicates: support/contact, containment, proximity, vertical ordering, front/behind/left/right. Functional and affordance predicates should be separate or later-stage.
- Confidence: High.

### Insight: CAND-001 is viable only if it is not framed as another open-vocabulary 3DSG method

- Date: 2026-04-28
- Based on: Open3DSG, CCL-3DSGG, OVSG, ConceptGraphs, HOV-SG, Open-Vocabulary Functional 3D Scene Graphs, Octree-Graph, 3DGraphLLM, 3D-Mem.
- Facts: Top-tier work already covers open-vocabulary 3D scene graph prediction, open-vocabulary graph mapping for robotics, hierarchical 3DSG navigation, functional 3DSG, and graph-to-LLM 3D reasoning.
- Inference: The thesis should be positioned as `geometry-grounded verification and representation of relation edges`, with explicit geometry evidence, provenance, uncertainty, and violation metrics.
- Confidence: High.

### Insight: The next paper intake should prioritize closed-set relation-edge evidence before robotics graph systems

- Date: 2026-04-28
- Based on: VL-SAT, SGGpoint, Open-Vocabulary Functional 3D Scene Graphs, Open-Vocabulary Octree-Graph, OVSG, ConceptGraphs.
- Facts: `VL-SAT` and `SGGpoint` directly operate in 3DSSG-style relation prediction and edge/semantic-geometric modeling. `OVSG` and `ConceptGraphs` are important open-vocabulary robotics graph systems, but they are broader downstream systems.
- Inference: For CAND-001, the next paper folders should be `VL-SAT` then `SGGpoint`, because they help define the relation-edge representation and baseline space before moving to robotics/planning use cases.
- Confidence: High.

### Insight: VL-SAT and SGGpoint define what CAND-001 must go beyond

- Date: 2026-04-28
- Based on: SGGpoint CVPR 2021, VL-SAT CVPR 2023.
- Facts: `SGGpoint` makes relation edges first-class learned representations through EdgeGCN. `VL-SAT` adds visual-language semantics during training and improves long-tail / unseen relation triplets.
- Inference: A CAND-001 thesis cannot claim novelty just by saying "edge-aware" or "semantic + geometry". The gap is that both papers still output closed-set labels and do not attach explicit, inspectable geometry evidence or violation status to relation edges.
- Confidence: High.

### Insight: SMKA closes the "spatial knowledge" loophole for CAND-001

- Date: 2026-04-28
- Based on: 3D Spatial Multimodal Knowledge Accumulation for Scene Graph Prediction in Point Cloud, CVPR 2023.
- Facts: `SMKA` uses support hierarchy, ConceptNet-derived symbolic knowledge, visual context, and graph reasoning to improve 3DSSG relation prediction. It reports better PredCls/SGCls than SGPN, EdgeGCN/SGGpoint, and KISG.
- Inference: CAND-001 should not be framed as "add spatial knowledge to relation prediction"; that has already been done in a strong closed-set baseline. The defensible gap is explicit edge evidence: support/contact/proximity measurements, provenance, uncertainty, and geometry violation evaluation.
- Recommended thesis cut: use SMKA as a spatial-knowledge baseline/reference, then argue for evidence-bearing relation edges rather than latent knowledge regularization.
- Confidence: High.

### Insight: OpenFunGraph makes functional relations a tempting but risky expansion

- Date: 2026-04-28
- Based on: Open-Vocabulary Functional 3D Scene Graphs for Real-World Indoor Spaces, CVPR 2025 Highlight.
- Facts: OpenFunGraph extends 3DSG with interactive element nodes and functional relationship edges, and evaluates against adapted Open3DSG and ConceptGraphs baselines on SceneFun3D/FunGraph3D.
- Inference: Functional 3DSG is a strong novelty boundary for CAND-001. If CAND-001 includes all functional relations, the project becomes part-level detection + affordance/common-sense reasoning + robotics manipulation, which is too broad for the first thesis prototype.
- Recommended thesis cut: keep CAND-001 on geometry-checkable relation verification first. Treat local functional relations as an optional later extension and remote functional relations as out-of-scope unless interaction evidence is available.
- Confidence: High.

### Insight: Octree-Graph is a representation reference, not the first CAND-001 baseline

- Date: 2026-04-28
- Based on: Open-Vocabulary Octree-Graph for 3D Scene Understanding, ICCV 2025.
- Facts: `Octree-Graph` stores each object as an adaptive-octree node and stores edge attributes such as semantic relation, distance, and 3D vector. It evaluates retrieval, path planning, storage, occupancy, semantic segmentation, and instance segmentation, but not 3DSSG-style predicate/triplet recall.
- Inference: This paper supports the idea that CAND-001 edges should expose compact geometric evidence. However, CAND-001 should not become a full open-vocabulary map/path-planning system unless the thesis direction changes.
- Recommended thesis cut: borrow distance/vector/occupancy/world-coordinate grounding as edge evidence fields, while keeping the primary contribution on relation-edge verification and geometry-consistency evaluation.
- Confidence: High.

### Insight: CAND-003 should start as offline verifier/refiner, not a full embodied robot system

- Date: 2026-04-29
- Based on: SayPlan, SG-Nav, SCOUT, RieMind, 3D-VCD, FirePlace, 3DGraphLLM, 3D-Mem.
- Facts: 3DSG has already been used for LLM planning, open-vocabulary query grounding, navigation, object search, graph-to-LLM representation, geometric tool use, and hallucination mitigation.
- Inference: CAND-003 is viable only if it narrows to geometry-aware verification/refinement of task outputs. A full robot planner, open-vocabulary mapper, or 3D-LLM would be too broad and too close to existing systems.
- Recommended thesis cut: offline spatial QA / graph query verification first. Use explicit 3DSG geometry evidence to verify LLM/VLM answers or target-object decisions before attempting navigation/search simulation.
- Confidence: Medium-High.

### Insight: RieMind and 3D-VCD raise the novelty bar for CAND-003

- Date: 2026-04-29
- Based on: RieMind, 3D-VCD, FirePlace.
- Facts: `RieMind` grounds an LLM in explicit 3DSG and structured geometric tools. `3D-VCD` uses distorted 3D scene graphs and semantic/geometric perturbations to reduce 3D-LLM hallucination.
- Inference: CAND-003 cannot claim novelty from explicit geometry tools or scene-graph perturbation alone. The contribution should emphasize task-specific verifier design, relation evidence provenance, and evaluation that distinguishes geometry violation from semantic failure.
- Confidence: Medium-High.

### Insight: SayPlan makes simulator feedback a prior-art baseline for CAND-003 planning

- Date: 2026-04-29
- Based on: SayPlan CoRL 2023 Oral.
- Facts: `SayPlan` uses a hierarchical 3DSG, LLM semantic search, a classical path planner, and scene-graph simulator feedback to produce executable mobile-manipulator task plans in large-scale environments.
- Inference: CAND-003 should not claim novelty from "LLM plan + scene graph feedback" alone. If it stays in the planning/search direction, the contribution must be more specific: relation-level geometry verification, invalid decision taxonomy, or verifier correction metrics.
- Recommended thesis cut: borrow SayPlan's correctness/executability split, but start with offline answer/target validity before building a full robot planning system.
- Confidence: High.

### Insight: SG-Nav and SCOUT make search/navigation strong but risky for CAND-003

- Date: 2026-04-29
- Based on: SG-Nav NeurIPS 2024, SCOUT arXiv 2026, SayPlan CoRL 2023.
- Facts: `SG-Nav` uses online 3DSG prompting, hierarchical CoT, and re-perception for zero-shot ObjectNav on MP3D/HM3D/RoboTHOR. `SCOUT` distills LLM relational knowledge into 3DSG object-search utility and introduces `SymSearch` with OmniGibson and real-world evaluations.
- Inference: Search/navigation is a credible downstream branch, but it would pull CAND-003 into simulator, partial observability, perception, planning, and robot-execution complexity. Unless CAND-003 explicitly pivots to this branch, the first prototype should remain an offline verifier/refiner over LLM/VLM task outputs.
- Recommended thesis cut: use `SG-Nav` and `SCOUT` as motivation and later benchmark references, while keeping the first contribution on relation-level geometry evidence, invalid-decision detection, and error-type decomposition.
- Confidence: High.

### Insight: 3DGraphLLM and 3D-Mem force CAND-003 into the verifier gap

- Date: 2026-04-30
- Based on: 3DGraphLLM ICCV 2025, 3D-Mem CVPR 2025.
- Facts: `3DGraphLLM` already maps 3D semantic scene graph relations into LLM token embeddings and improves ScanRefer/Multi3DRefer/Scan2Cap/ScanQA/SQA3D. `3D-Mem` explicitly argues that object-centric 3DSG textual relations are too restrictive for nuanced embodied spatial reasoning, and uses image-based Memory Snapshots / Frontier Snapshots instead.
- Inference: CAND-003 is viable only if it avoids both broad alternatives: not another graph-to-LLM representation and not another embodied scene-memory system. The defensible space is explicit relation-edge geometry verification of LLM/VLM task outputs.
- Recommended thesis cut: promote CAND-003 only as an offline verifier/refiner that uses CAND-001-style relation evidence to diagnose object-reference, spatial-relation, and geometry-constraint failures.
- Confidence: High.

### Insight: RelWitness is a direct method-wording threat, not yet a reproduced-baseline replacement

- Date: 2026-05-23
- Based on: RelWitness arXiv v2 PDF.
- Facts: RelWitness introduces visual-geometric relation witnesses for open-vocabulary 3DSSG under incomplete relation supervision. It includes a calibrated witness quality `Q`, family-dependent thresholds, a three-stage positive-unlabeled learning schedule, witness-consistent decoding, and an RGB-D missing-relation audit protocol. It also states that numerical results are simulated manuscript-planning values.
- Inference: H001 must cite/track RelWitness as the nearest very recent overlap. The defense is narrower than before: H001's contribution is not relation witnesses or calibration alone, but reproduced calibrated geometry-consistency evaluation/re-ranking over existing relation-source outputs with identity-preserving joins, `Violation@K`, controls, and denominator discipline.
- Confidence: Medium-High.

### Insight: The current H001 reference set needs expansion before serious submission

- Date: 2026-05-22
- Based on: `paper/draft.md` citation-key count and the 2025-2026 registry expansion.
- Facts: The current draft cites the core H001 baselines and several positioning papers, but recent 2025-2026 work now includes additional open-world, zero-shot, graph-reasoning, and visual-geometric relation-evidence papers.
- Inference: For a top-tier target, Related Work should separate four groups: direct 3DSSG relation predictors, open-vocabulary/open-world 3DSG generators, geometry/witness/reliability methods, and graph-mediated downstream reasoning. H001 must explicitly state which group it competes with and which groups are only motivation/boundary.
- Confidence: High.

## Open Questions

1. 3D Scene Graph 연구는 최근 어떤 방향으로 이동하고 있는가?
2. Open-vocabulary, LLM/VLM, robotics, dynamic scene, 3D generation 흐름은 서로 어떻게 연결되는가?
3. 석사 연구로 현실적으로 기여할 수 있는 문제는 무엇인가?
4. 좋은 기여 후보를 검증하려면 어떤 dataset, benchmark, metric이 필요한가?
5. semantic reasoning relation과 geometry-derived relation을 edge에서 어떻게 함께 표현해야 하는가?
6. CAND-003을 CAND-001의 downstream extension으로 둘 것인가, 아니면 독립 thesis 후보로 키울 것인가?
7. LLM/VLM task output의 오류를 semantic hallucination, missing perception, graph relation error, geometry violation으로 어떻게 분해해 측정할 것인가?
8. RelWitness future version에서 reproduced results, code, arbitrary-source adapters, `Violation@K`, or wrong-pair/shuffled-geometry controls가 추가되는지 추적해야 한다.
9. Final Related Work에 들어간 recent boundary papers가 H001을 broad open-world generation/RAG/downstream grounding paper처럼 보이게 만들지 않도록 citation sentence를 계속 통제해야 한다.
