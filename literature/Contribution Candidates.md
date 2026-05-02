# Contribution Candidates

Last updated: 2026-04-30

이 파일은 literature 조사에서 나온 연구 기여 후보를 관리한다. 후보가 충분히 구체화되면 별도 `CAND-<number>.md` 파일로 세부 내용을 분리한다.

## CAND-001: Geometry-Grounded Open-Vocabulary Relation Graph

- Detail file: `literature/CAND-001.md`
- Date: 2026-04-27
- Research question: Open-vocabulary 3D relation prediction에서 LLM/VLM이 제안한 semantic relation을 3D geometry evidence로 검증/보정하면 relation hallucination을 줄이고 rare/open-set predicate 성능을 유지할 수 있는가?
- Existing limitation: Open3DSG/CCL-3DSGG 계열은 open-vocabulary semantics를 강화하지만, LLM/VLM relation이 실제 3D support/contact/containment/relative pose와 얼마나 일관되는지 평가가 약할 수 있다. 반대로 classical 3DSG는 geometry는 쓰지만 closed-set relation에 묶인다.
- Proposed direction: relation proposal은 VLM/LLM 또는 CLIP-aligned feature가 담당하고, geometric verifier가 relative pose, contact/support, containment, distance, topology, occlusion evidence를 edge attribute로 추가한다.
- Why this is 3D Scene Graph research: 핵심 산출물이 object-node와 semantic+geometric relation-edge를 갖는 3DSG representation이다.
- Required data / benchmark: 3DSSG/3RScan, ReplicaSSG, ScanNet/Replica 기반 추가 relation annotations 검토.
- Possible metrics: predicate R@K/mR@K, zero-shot predicate recall, geometry consistency score, violation rate, relation-grounded retrieval success.
- Baselines: SGRec3D, Open3DSG, CCL-3DSGG, FROSS.
- Failure condition: geometry verifier가 단순 spatial predicates만 개선하고 semantic/functional predicates에는 효과가 없으면 contribution 범위가 좁아진다.
- Feasible scope: Medium. 석사 3-6개월 범위에서 "proposal + verifier + evaluation"로 줄이면 가능.
- Updated after B pass: Stronger. Use 3DSSG as primary benchmark, CCL-3DSGG/Open3DSG as open-vocabulary baselines, and FROSS/ReplicaSSG as optional online secondary benchmark.
- Updated after top-tier scan: Stronger but narrower. Top-tier work already covers open-vocabulary 3DSG and graph-to-LLM reasoning, so CAND-001 should focus on geometry-grounded relation-edge verification/evaluation rather than proposing another broad open-vocabulary 3DSG pipeline.
- Updated after SMKA intake: Stronger gap definition. Spatial hierarchy plus symbolic/text knowledge has already been used for 3DSSG relation prediction, so CAND-001 should emphasize explicit edge-level geometry evidence and violation/consistency evaluation rather than generic spatial-knowledge fusion.
- Updated after OpenFunGraph intake: Keep full functional relation discovery out of first scope. Functional 3DSG is now an active top-tier direction; CAND-001 should start with geometry-checkable spatial/support/containment/proximity relations and treat local functional relations as optional extension.
- Updated after Octree-Graph intake: Use compact occupancy, distance, 3D vector, and world-coordinate spatial relation as representation inspiration. Do not make full map/path-planning reproduction the first CAND-001 target.

## CAND-002: Dual-Channel Edge Representation for 3D Scene Reasoning

- Date: 2026-04-27
- Research question: 3DSG edge를 semantic channel과 geometry channel로 분리해 저장하면, language query / object search / relation-guided retrieval에서 단일 predicate label보다 더 안정적인 reasoning이 가능한가?
- Existing limitation: 단일 relation label은 "on", "near", "inside" 같은 predicate의 semantic meaning과 geometric evidence를 섞어버린다.
- Proposed direction: edge schema를 `semantic_relation`, `geometric_relation`, `evidence`, `uncertainty`, `source`로 구조화하고 query-time에 조합한다.
- Required data / benchmark: 3DSSG, ReplicaSSG, SCOUT/SymSearch류 semantic reasoning benchmark 참고.
- Possible metrics: graph query accuracy, relation-guided retrieval, symbolic consistency, task success.
- Feasible scope: Medium-Low risk if benchmark is well defined.

## CAND-003: Geometry-Aware Refinement of LLM/VLM Task Reasoning on 3DSG

- Detail file: `literature/CAND-003.md`
- Date: 2026-04-27
- Research question: LLM/VLM이 3DSG 위에서 task reasoning을 할 때, 명시적 geometric constraints를 넣으면 object placement/navigation/search decision의 오류를 줄일 수 있는가?
- Existing limitation: FirePlace는 object placement에서 이 문제를 잘 보여주지만, 일반적인 3DSG representation/evaluation으로 확장할 여지가 있다.
- Proposed direction: 3DSG를 LLM input으로 줄 때 symbolic relation만 주지 않고, geometry-derived constraints와 violation checker를 함께 제공한다.
- Required data / benchmark: embodied navigation/search 시뮬레이션, Replica/HM3D/ScanNet 계열, SCOUT/SymSearch 참고.
- Possible metrics: task success, invalid action/placement rate, reasoning latency, graph consistency.
- Feasible scope: Medium-High risk. task environment까지 만들면 범위가 커지므로, 먼저 offline graph query/refinement로 축소하는 게 좋다.
- Updated after 2026-04-29 survey: Stronger but high-risk. `SayPlan`, `SG-Nav`, `ConceptGraphs`, `OVSG`, `HOV-SG`, `3DGraphLLM`, `RieMind`, and `3D-VCD` show that `3DSG + LLM/VLM` is already an active direction. CAND-003 should not be framed as "use 3DSG for LLM reasoning"; it should focus on explicit geometry-aware verification/refinement of task outputs.
- Recommended first cut: offline spatial QA / graph query verification. Use 3DSG/object geometry to verify LLM/VLM answers or target-object decisions before attempting full embodied navigation/search or object placement execution.
- Novelty boundary: `RieMind` is the closest explicit 3DSG + geometric tool competitor; `3D-VCD` is the closest 3D hallucination mitigation competitor. A defensible CAND-003 contribution needs task-level verifier metrics, relation evidence provenance, and clear separation between semantic reasoning failure and geometry violation.
- Updated after P0 intake: `RieMind`, `3D-VCD`, and `SayPlan` are now read. The defensible problem is narrower: use relation-level geometry evidence to verify/correct LLM/VLM task outputs and report invalid-decision/error-type metrics, not another 3DSG agent, contrastive decoding method, or robot planner.
- Updated after SG-Nav / SCOUT intake: search/navigation is a strong but broad downstream branch. `SG-Nav` and `SCOUT/SymSearch` support the task-utility motivation, but the first CAND-003 cut should still stay offline unless the candidate explicitly pivots to object search/navigation benchmarks.
- Updated after 3DGraphLLM / 3D-Mem intake: graph-to-LLM representation and embodied scene memory are now strong novelty boundaries. CAND-003 should be promoted only as an offline geometry-verifier/refiner over LLM/VLM task outputs, preferably reusing CAND-001 relation-edge evidence.
