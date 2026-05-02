# CAND-003: Geometry-Aware Refinement of LLM/VLM Task Reasoning on 3DSG

Last updated: 2026-04-30

Latest check: 2026-04-30, primary sources checked through CVF Open Access, ICCV/CVPR proceedings pages, NeurIPS proceedings, RSS proceedings, PMLR, OpenReview, arXiv, official project pages, and official code/project repositories.

## Research Question

LLM/VLM이 3D Scene Graph 위에서 task reasoning을 수행할 때, 명시적 geometric constraints, scene-graph tools, 또는 violation checker를 넣으면 object placement, navigation/search, spatial QA decision의 오류와 hallucination을 줄일 수 있는가?

## Scope

### In Scope

- 3DSG 또는 object-centric 3D scene representation을 LLM/VLM input, memory, retrieval context, 또는 tool interface로 사용하는 연구.
- Geometry-aware refinement: geometric constraints, path/planning feasibility, object relation checks, 3D scene-graph perturbation, tool-calling 기반 metric reasoning.
- Offline graph query / refinement: static scene graph나 reconstructed scene에서 answer/action candidate를 만들고 geometry로 검증하는 축.
- Evaluation: task success, invalid action/placement rate, grounding/hallucination rate, relation-guided retrieval/search success, reasoning latency.

### Out of First Scope

- Full robot stack 구축, online SLAM, manipulation execution, physics simulation training.
- 3D scene generation 자체.
- Full functional 3DSG discovery. OpenFunGraph 계열은 novelty boundary로 보되, CAND-003의 첫 실험은 geometry-verifiable task reasoning으로 제한한다.

## Survey Verdict

CAND-003은 CAND-001보다 downstream하고 위험도가 높다. 그러나 2023-2026 문헌 흐름은 분명하다. 3DSG는 LLM/VLM task reasoning의 compact context로 이미 쓰이고 있고, 최근에는 단순 graph serialization보다 geometry-grounded tool use, hallucination mitigation, relation-aware object search, hierarchical navigation reasoning으로 이동하고 있다.

권장되는 좁은 formulation:

> Geometry-grounded verification of LLM/VLM task reasoning over 3D scene graphs.

실용적인 thesis cut:

> Given a 3DSG and a language task/query, let an LLM/VLM propose an answer, target object, placement, or next decision, then verify/refine that output using explicit 3D geometry constraints and graph-derived evidence before evaluating task correctness and violation/hallucination rates.

이 방향은 다음과 같이 포지셔닝해야 한다.

- Not another 3D-LLM.
- Not another open-vocabulary 3DSG mapper.
- Not a full robot planner.
- Not full functional relation discovery.
- Yes: a task-level verifier/refiner that exposes where LLM/VLM reasoning violates 3D scene geometry.

## Evidence Corpus for CAND-003

| Role | Paper | Venue / status | Link | Evidence for CAND-003 |
| --- | --- | --- | --- | --- |
| Direct geometry-aware object placement anchor | FirePlace: Geometric Refinements of LLM Common Sense Reasoning for 3D Object Placement | CVPR 2025 | [CVF](https://openaccess.thecvf.com/content/CVPR2025/html/Huang_FirePlace_Geometric_Refinements_of_LLM_Common_Sense_Reasoning_for_3D_CVPR_2025_paper.html) | MLLM common-sense proposal을 low-level 3D geometric constraints로 refine한다. CAND-003의 verifier/refinement design pattern에 가장 직접적이다. |
| Direct 3DSG + geometric tool anchor | RieMind: Geometry-Grounded Spatial Agent for Scene Understanding | arXiv 2026 preprint | [arXiv](https://arxiv.org/abs/2603.15386) | Explicit 3DSG와 structured geometric tools로 LLM spatial reasoning을 수행한다. CAND-003의 "tool-based geometry grounding"과 매우 직접적으로 겹친다. |
| Direct hallucination mitigation anchor | 3D-VCD: Hallucination Mitigation in 3D-LLM Embodied Agents through Visual Contrastive Decoding | CVPR 2026 accepted / arXiv | [arXiv](https://arxiv.org/abs/2604.08645), [project](https://plan-lab.github.io/projects/3d-vcd/) | 3D scene graph에 semantic/geometric perturbation을 주고 contrastive decoding으로 hallucination을 줄인다. CAND-003 novelty boundary이자 evaluation reference다. |
| 3DSG-based LLM planning anchor | SayPlan: Grounding Large Language Models using 3D Scene Graphs for Scalable Robot Task Planning | CoRL 2023 Oral | [project](https://sayplan.github.io/), [OpenReview](https://openreview.net/forum?id=wMpOMO0Ss7a) | Hierarchical 3DSG semantic search와 scene graph simulator feedback으로 infeasible action을 줄이는 iterative replanning을 제안한다. |
| Open-vocabulary entity grounding anchor | Context-Aware Entity Grounding with Open-Vocabulary 3D Scene Graphs | CoRL 2023 | [PMLR](https://proceedings.mlr.press/v229/chang23b.html), [code](https://github.com/changhaonan/OVSG) | Free-form text query를 3DSG context로 ground한다. Task reasoning 전 단계인 target grounding baseline이다. |
| Open-vocabulary planning graph anchor | ConceptGraphs: Open-Vocabulary 3D Scene Graphs for Perception and Planning | ICRA 2024 | [project](https://concept-graphs.github.io/), [arXiv](https://arxiv.org/abs/2309.16650) | 2D foundation model output을 3D graph로 fuse하고 object caption/relation을 LLM planning에 쓴다. Broad system baseline / scope risk다. |
| Hierarchical navigation graph anchor | HOV-SG: Hierarchical Open-Vocabulary 3D Scene Graphs for Language-Grounded Robot Navigation | RSS 2024 | [RSS](https://www.roboticsproceedings.org/rss20/p077.html), [code](https://github.com/hovsg/HOV-SG) | floor-room-object hierarchy와 open-vocabulary features로 long-horizon navigation을 수행한다. |
| Online 3DSG prompting for navigation | SG-Nav: Online 3D Scene Graph Prompting for LLM-based Zero-shot Object Navigation | NeurIPS 2024 | [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2024/hash/098491b37deebbe6c007e69815729e09-Abstract-Conference.html) | Observed scene을 LLM-friendly 3DSG로 표현하고 hierarchical CoT prompt로 goal location을 reasoning한다. MP3D/HM3D/RoboTHOR 평가축을 제공한다. |
| 3D scene memory warning | 3D-Mem: 3D Scene Memory for Embodied Exploration and Reasoning | CVPR 2025 | [CVF](https://openaccess.thecvf.com/content/CVPR2025/html/Yang_3D-Mem_3D_Scene_Memory_for_Embodied_Exploration_and_Reasoning_CVPR_2025_paper.html) | Object-centric 3DSG의 restrictive textual relationship이 nuanced spatial understanding에 약하다고 지적한다. CAND-003은 graph relation을 더 geometry-aware하게 만들어야 한다. |
| 3D graph to LLM representation anchor | 3DGraphLLM: Combining Semantic Graphs and Large Language Models for 3D Scene Understanding | ICCV 2025 | [CVF](https://openaccess.thecvf.com/content/ICCV2025/html/Zemskova_3DGraphLLM_Combining_Semantic_Graphs_and_Large_Language_Models_for_3D_ICCV_2025_paper.html) | Semantic relations in 3DSG를 LLM token embedding으로 넣어 ScanRefer/Multi3DRefer/ScanQA/SQA3D/Scan2Cap를 개선한다. CAND-003은 여기서 geometric verification으로 차별화해야 한다. |
| 3D-LLM interactive planning anchor | Scene-LLM: Extending Language Model for 3D Visual Reasoning | WACV 2025 | [CVF](https://openaccess.thecvf.com/content/WACV2025/html/Fu_Scene-LLM_Extending_Language_Model_for_3D_Visual_Reasoning_WACV_2025_paper.html) | Scene-level + egocentric 3D feature representation으로 captioning, QA, interactive planning을 수행한다. Direct 3DSG는 아니지만 task reasoning benchmark 참고축이다. |
| Situated reasoning benchmark anchor | Multi-modal Situated Reasoning in 3D Scenes | NeurIPS 2024 Datasets and Benchmarks | [NeurIPS](https://nips.cc/virtual/2024/poster/97727) | MSQA와 MSNN을 통해 situated QA와 next-step navigation을 평가한다. 3DSG/VLM 기반 데이터 생성과 multi-modal input ambiguity 문제가 중요하다. |
| 3D-LLM hallucination benchmark anchor | 3D-GRAND: A Million-Scale Dataset for 3D-LLMs with Better Grounding and Less Hallucination | CVPR 2025 | [CVF](https://openaccess.thecvf.com/content/CVPR2025/html/Yang_3D-GRAND_A_Million-Scale_Dataset_for_3D-LLMs_with_Better_Grounding_and_CVPR_2025_paper.html) | 3D-POPE hallucination benchmark와 dense grounding dataset을 제공한다. CAND-003의 hallucination metric reference다. |
| Relation-aware task reasoning anchor | Relationship-Aware Hierarchical 3D Scene Graph for Task Reasoning | ICRA 2026 / arXiv | [project](https://ntnu-arl.github.io/reasoning_graph/), [arXiv](https://arxiv.org/abs/2602.02456) | VLM-derived object relations와 LLM/VLM task reasoning module을 결합해 object search, trash disposal, prepare bedroom 같은 task reasoning을 수행한다. |
| Object search utility anchor | Relational Semantic Reasoning on 3D Scene Graphs for Open World Interactive Object Search | arXiv 2026 preprint | [arXiv](https://arxiv.org/abs/2603.05642) | SCOUT/SymSearch는 3DSG 위 relational semantic reasoning을 object search utility로 distill한다. CAND-003의 search benchmark와 lightweight inference 참고축이다. |
| Retrieval-reasoning boundary | SGR3 Model: Scene Graph Retrieval-Reasoning Model in 3D | arXiv 2026 preprint | [arXiv](https://arxiv.org/abs/2603.04614) | MLLM+RAG로 semantic scene graph generation을 수행한다. Task refinement보다는 graph generation 쪽이라 secondary boundary다. |

## Facts

- 2023년부터 `SayPlan`, `OVSG`, `ConceptGraphs`는 3DSG를 LLM/VLM task planning, free-form query grounding, perception/planning representation으로 사용했다.
- 2024년 `HOV-SG`와 `SG-Nav`는 hierarchy와 online 3DSG prompting을 navigation/search로 연결했다.
- 2025년 `FirePlace`, `3D-Mem`, `3DGraphLLM`, `Scene-LLM`, `3D-GRAND`는 3D reasoning에서 geometry grounding, scene memory, graph-to-LLM representation, hallucination evaluation의 필요성을 강화했다.
- 2026년 preprint / accepted work인 `Relationship-Aware Hierarchical 3D Scene Graph`, `SCOUT`, `RieMind`, `3D-VCD`는 relation-aware task reasoning, structured geometric tools, hallucination mitigation을 더 직접적으로 다룬다.

## Paper Claims

- `SayPlan`: hierarchical 3DSG를 이용하면 LLM planning을 large-scale multi-room/multi-floor 환경으로 확장할 수 있고, simulator feedback 기반 iterative replanning으로 infeasible action을 줄일 수 있다.
- `FirePlace`: MLLM은 semantic common sense에는 강하지만 fine-grained 3D geometry에는 약하므로, geometric constraint construction/solving을 결합해야 object placement quality가 올라간다.
- `3D-Mem`: object-centric 3DSG는 scene memory로 쓰기에는 textual relationship이 제한적이고, nuanced spatial understanding과 active exploration을 충분히 지원하지 못한다.
- `3DGraphLLM`: object coordinate만 쓰는 3D LLM input보다 semantic relationship을 포함한 3DSG representation이 3D vision-language task 성능을 높인다.
- `RieMind`: explicit 3DSG와 structured geometric tools로 perception/reasoning을 분리하면 VLM spatial reasoning을 크게 개선할 수 있다.
- `3D-VCD`: 3D-LLM hallucination은 object presence, spatial layout, geometric grounding에서 발생하므로, distorted 3D scene graph와 contrastive decoding이 inference-time mitigation에 효과적이다.
- `SG-Nav`: online 3DSG prompting, hierarchical CoT reasoning, and re-perception improve zero-shot ObjectNav over LLM navigation baselines on MP3D, HM3D, and RoboTHOR.
- `SCOUT`: LLM relational knowledge를 offline distillation해 3DSG search utility로 쓰면 real-time object search에서 LLM 수준 reasoning을 더 효율적으로 approximating할 수 있다.

## Inferences

- CAND-003의 novelty는 `3DSG + LLM/VLM` 자체가 아니다. 이 조합은 이미 CoRL 2023부터 강하게 존재한다.
- 더 방어 가능한 gap은 task output의 geometry-aware verification/refinement다. 예: answer, target object, route choice, placement candidate가 3D geometry와 graph constraints를 만족하는지 명시적으로 검사한다.
- `RieMind`와 `3D-VCD`가 2026년에 이미 explicit 3DSG + geometric tools / perturbation을 제안했기 때문에, CAND-003은 이들보다 좁고 검증 가능한 task와 metric으로 들어가야 한다.
- CAND-003은 CAND-001 위에 얹을 수 있다. CAND-001이 relation edge evidence/verifier를 만들고, CAND-003이 그 evidence를 LLM/VLM task reasoning의 decision-time verifier로 사용한다.
- 첫 thesis prototype은 online robot execution이 아니라 offline graph query/refinement로 제한해야 한다. 그래야 3-6개월 범위에서 dataset, metric, baseline이 관리 가능하다.

## After P0 Intake: RieMind / 3D-VCD / SayPlan

Date checked: 2026-04-29

Detailed folders:

- `literature/2026_arxiv_riemind/`
- `literature/2026_cvpr_3d-vcd/`
- `literature/2023_corl_sayplan/`

### Facts

- `RieMind` directly implements explicit 3DSG + deterministic geometric tools for static indoor spatial QA, using ground-truth 3DSG annotations as an upper-bound evaluation on VSI-Bench.
- `3D-VCD` directly implements inference-time hallucination mitigation by contrasting original and semantically/geometrically distorted 3D scene graph contexts.
- `SayPlan` directly implements 3DSG-grounded LLM task planning with semantic search, path planning, scene-graph simulator verification, and iterative replanning.

### Paper Claims

- `RieMind`: tool-mediated access to explicit 3D geometry improves metric/static spatial reasoning over base VLMs and fine-tuned spatial QA models.
- `3D-VCD`: scene-graph perturbation and contrastive decoding reduce 3D-LLM over-affirmation and embodied hallucination without retraining.
- `SayPlan`: hierarchical 3DSG search and simulator feedback let LLM planners scale to large multi-room/multi-floor environments and generate more executable plans.

### Inferences

- CAND-003 now has three strong novelty boundaries: `RieMind` covers explicit 3DSG geometric tools, `3D-VCD` covers distorted 3D scene graph contrastive decoding for hallucination mitigation, and `SayPlan` covers scene-graph simulator feedback for LLM task planning.
- The remaining defensible gap is a verifier/evaluation layer that uses relation-level geometry evidence to diagnose and correct task outputs, while reporting exactly which object, relation, or constraint caused the correction.
- CAND-003 should reuse CAND-001's edge evidence if possible. Without relation-level evidence, it risks becoming a weaker version of RieMind or 3D-VCD.

### Recommended Updated First Cut

Start with offline spatial QA / graph query verification, but phrase it as a verifier benchmark rather than a new LLM agent:

> Given a 3DSG-derived answer or target-object decision from an LLM/VLM, can explicit relation-edge geometry evidence identify invalid spatial claims and correct them without rejecting valid answers?

Minimum evaluation should include:

- answer / target correctness;
- geometry violation rate;
- verifier rejection precision;
- valid-answer preservation;
- correction success;
- error type breakdown: nonexistent object, wrong relation, impossible support/contact, wrong relative direction, weak graph evidence.

## After P0 Intake: SG-Nav / SCOUT-SymSearch

Date checked: 2026-04-29

Detailed folders:

- `literature/2024_neurips_sg-nav/`
- `literature/2026_arxiv_scout/`

### Facts

- `SG-Nav` is a NeurIPS 2024 ObjectNav system that builds an online 3D scene graph from observed RGB-D input, summarizes it for LLM prompting, uses hierarchical CoT to infer likely goal locations, and uses re-perception to update incorrect object observations.
- `SG-Nav` evaluates on MP3D, HM3D, and RoboTHOR with SR and SPL, so it is a navigation-side benchmark anchor rather than an offline verifier benchmark.
- `SCOUT` is a 2026 arXiv object-search system that distills LLM relational knowledge into a 3DSG search utility over graph nodes and relations.
- `SCOUT` introduces `SymSearch`, a symbolic interactive object-search benchmark built from InteriorGS scenes, and also evaluates on OmniGibson and real-world Toyota HSR trials.

### Paper Claims

- `SG-Nav`: hierarchical 3DSG prompting plus re-perception improves zero-shot ObjectNav success over frontier, commonsense, and LLM navigation baselines.
- `SCOUT`: offline-distilled relational semantic priors can approximate LLM-level object-search reasoning with much lower online inference latency.

### Inferences

- Search/navigation is now a well-supported CAND-003 branch, but it is also a scope risk. A thesis framed as "3DSG + LLM for navigation/search" would compete with `SayPlan`, `SG-Nav`, `SCOUT`, `HOV-SG`, `OVSG`, and `ConceptGraphs`.
- The defensible first CAND-003 gap remains relation-level geometry verification and error decomposition, not a broad object-navigation or object-search agent.
- `SG-Nav` and `SCOUT` are better downstream motivation for the first prototype unless the user explicitly pivots CAND-003 toward search/navigation benchmarks.

### Recommended Scope Boundary

Keep the first CAND-003 prototype offline:

- verify/refine LLM/VLM answer or target-object decisions using explicit 3DSG geometry evidence;
- report invalid-decision and geometry-violation metrics;
- use search/navigation papers as motivation and later evaluation paths after the verifier is stable.

## After P1 Intake: 3DGraphLLM / 3D-Mem

Date checked: 2026-04-30

Detailed folders:

- `literature/2025_iccv_3dgraphllm/`
- `literature/2025_cvpr_3d-mem/`

### Facts

- `3DGraphLLM` is an ICCV 2025 graph-to-LLM method that maps 3D semantic scene graph node and edge features into an LLM token embedding space.
- `3DGraphLLM` evaluates across ScanRefer, Multi3DRefer, Scan2Cap, ScanQA, and SQA3D, and its official code is public.
- `3D-Mem` is a CVPR 2025 embodied scene-memory method that explicitly argues object-centric 3DSG textual relations are too restrictive for nuanced spatial reasoning.
- `3D-Mem` uses Memory Snapshots and Frontier Snapshots instead of relying only on graph captions, and evaluates on A-EQA, EM-EQA, and GOAT-Bench. Its official code is public.

### Paper Claims

- `3DGraphLLM`: adding semantic relation embeddings from 3DSG improves LLM-based 3D grounding, captioning, and QA over object-only learnable scene representations.
- `3D-Mem`: image-based memory snapshots preserve spatial/contextual cues that object-centric graph captions lose, improving embodied QA and lifelong navigation.

### Inferences

- P1 intake strengthens CAND-003, but only as a narrow verifier/refiner candidate. The broad alternatives are now clearly covered: `3DGraphLLM` covers graph-to-LLM representation, and `3D-Mem` covers embodied scene memory/exploration.
- CAND-003 should not be promoted as "a 3DSG representation for LLMs" or "a better embodied memory." Both directions have strong recent prior art.
- The remaining defensible gap is an explicit 3DSG relation verifier that takes LLM/VLM task outputs and reports whether the referenced objects, relations, and geometric constraints are satisfied.
- `3D-Mem` makes the bar higher: if CAND-003 uses 3DSG, the graph edges must be richer than textual predicates. They need measurable evidence, provenance, and violation status.

### Scope Decision Note for User Judgment

Recommended promotion condition:

> Promote CAND-003 only if it is framed as an offline geometry-verifier/refiner for LLM/VLM task outputs over 3DSG, reusing CAND-001 relation-edge evidence where possible.

Candidate promoted hypothesis:

> For geometry-checkable 3D scene reasoning tasks, adding an explicit 3DSG relation-edge geometry verifier to LLM/VLM outputs will reduce spatial hallucination and invalid object-reference decisions while preserving valid answers.

Minimum first artifact if promoted:

- define a geometry-checkable offline task subset from 3DSSG/3RScan plus ScanRefer/ScanQA/SQA3D-style queries;
- produce unverified LLM/VLM answers or target-object decisions;
- run deterministic checks for object existence, support/contact, containment, proximity, relative direction, and distance constraints;
- report answer/object correctness, geometry violation rate, verifier rejection precision, valid-answer preservation, correction success, and error-type breakdown.

Do not promote if the intended thesis direction is full embodied navigation/search, general 3D-LLM representation learning, or image-based scene memory. Those paths now look too broad for the first CAND-003 cut.

## Novelty Boundary

| Existing direction | Already covered by | Boundary for CAND-003 |
| --- | --- | --- |
| LLM task planning with 3DSG | SayPlan | 단순 graph serialization이나 hierarchical search는 novelty가 약하다. |
| Open-vocabulary 3D graph for planning | ConceptGraphs, OVSG, HOV-SG | mapping/perception/planning system 전체로 가면 범위가 커진다. |
| 3DSG as LLM representation | 3DGraphLLM | semantic relation tokenization 자체보다 geometric verifier가 필요하다. |
| Embodied scene memory for VLM reasoning | 3D-Mem | image-memory/exploration system이 아니라 evidence-bearing 3DSG relation verifier로 좁혀야 한다. |
| Object placement with geometry constraints | FirePlace | placement-only로 가면 3DSG thesis보다 3D scene generation/placement thesis가 된다. |
| 3D-LLM hallucination mitigation | 3D-GRAND, 3D-VCD | hallucination benchmark는 중요하지만 3DSG relation/task verifier로 좁혀야 한다. |
| Explicit 3DSG + geometric tools | RieMind | 매우 가까운 경쟁축이다. CAND-003은 task-specific verifier metric과 relation evidence provenance로 차별화해야 한다. |
| Object search with relational semantics | SCOUT/SymSearch, SG-Nav | search/navigation을 택하면 simulator complexity와 online setting 위험이 커진다. |

## Candidate Task Cuts

### Cut A: Offline Spatial QA / Graph Query Verification

- Input: reconstructed scene or 3DSG, object instances, geometry evidence.
- LLM/VLM output: answer or referenced object(s).
- Verifier: object existence, distance/order/support/containment constraints, relation edge consistency.
- Possible datasets: ScanQA, SQA3D, ScanRefer, Multi3DRefer, MSQA, VSI-Bench static split if access is feasible.
- Metrics: answer accuracy, grounding accuracy, geometry violation rate, hallucination/over-affirmation rate, verifier correction precision.
- Risk: Medium. Dataset alignment and object id mapping are the main issue.

### Cut B: Object Search / Navigation Decision Refinement

- Input: partial 3DSG or explored scene graph.
- LLM/VLM output: next room/frontier/object to inspect.
- Verifier: reachability, room-object priors, object-object co-occurrence, distance/path feasibility.
- Possible datasets: MP3D, HM3D, RoboTHOR, SymSearch, Habitat-compatible scenes.
- Metrics: success rate, SPL, exploration steps, invalid target rate, latency, LLM calls.
- Risk: Medium-High. Simulator setup can dominate the thesis.

### Cut C: Object Placement Constraint Refinement

- Input: 3D scene, object to place, candidate placements.
- LLM/VLM output: placement candidate or ranked placement.
- Verifier: contact, support, no-overhang, collision, visibility, semantic compatibility.
- Possible references: FirePlace; ScanNet/Replica/Objaverse-style assets if accessible.
- Metrics: physical feasibility, semantic alignment, plausibility, visibility, geometry violation rate.
- Risk: Medium-High. It may drift away from 3DSG unless edge evidence is central.

### Recommended First Cut

Start with Cut A.

Reason: Cut A can reuse CAND-001 relation evidence and local 3DSSG/3RScan geometry before building a simulator. The first research question can be:

> Does an explicit geometry-verifier over 3DSG edges reduce LLM/VLM spatial answer hallucination or invalid object-reference decisions on offline 3D scene reasoning tasks?

## Dataset / Benchmark Candidates

| Candidate | Role | Fit | Risk |
| --- | --- | --- | --- |
| 3DSSG / 3RScan | relation-edge evidence and geometry verifier source | High for CAND-001-to-CAND-003 bridge | Needs task/query layer, not enough alone for LLM task reasoning |
| ScanQA / SQA3D | 3D QA evaluation used by 3DGraphLLM | Medium | Need align answers to geometry-checkable constraints |
| ScanRefer / Multi3DRefer | referred object grounding | Medium | Good for object-reference verification, less direct for task reasoning |
| MSQA / MSNN | situated reasoning and next-step navigation benchmark | Medium-High | Need access and alignment with graph/geometry representation |
| 3D-POPE | hallucination evaluation for 3D-LLMs | Medium-High | Direct hallucination metric, but not necessarily 3DSG-native |
| HEAL | embodied hallucination probing | Medium | Useful if available; may require agent/task format |
| VSI-Bench static split | spatial reasoning benchmark used by RieMind | Medium | Very relevant to geometric tools, but may be preprint-driven and benchmark setup needs validation |
| SymSearch | symbolic object search benchmark from SCOUT | Medium | Very relevant for search; preprint status and access need verification |
| MP3D / HM3D / RoboTHOR | navigation/search evaluation | Medium | Simulator setup risk |
| Replica / ReplicaSSG | online 3DSG / relation search secondary | Medium | Better after offline verifier works |

## Candidate Metrics

- Task success: answer accuracy, object grounding accuracy, navigation/search success, placement success.
- Invalid decision/action rate: unreachable target, impossible placement, missing precondition, violated support/contact/containment.
- Geometry violation rate: predicted answer/action references relations that violate measured 3D geometry.
- Hallucination rate: nonexistent object, wrong spatial relation, unsupported affordance/state, over-affirmation.
- Correction utility: fraction of invalid LLM/VLM outputs corrected by verifier without rejecting valid outputs.
- Latency / cost: LLM calls, verifier time, token length, online feasibility.
- Explanation consistency: whether the final answer names the evidence used, without relying on LLM-as-judge as the only metric.

## Feasibility Assessment

### Feasible 3-6 Month Version

Offline graph-query refinement:

1. Use a static 3DSG or object-instance scene representation.
2. Generate or collect spatial/task queries where answers depend on geometry-checkable relations.
3. Ask LLM/VLM for an answer or target object using graph text or graph tools.
4. Run deterministic geometry verifier on the proposed answer/action.
5. Report task accuracy, hallucination/violation rate, correction precision, and latency.

### Risky Version

Full embodied navigation/search or manipulation:

- Requires simulator integration, partial observability, exploration policy, perception errors, task-specific reward, and robot stack assumptions.
- Valuable as later work, but too broad for the first CAND-003 pass.

## Paper Intake Priority for CAND-003

| Priority | Paper | Why |
| --- | --- | --- |
| P0 | RieMind | Closest direct competition: explicit 3DSG + geometric tools for LLM spatial reasoning. |
| P0 | 3D-VCD | Latest direct hallucination mitigation with distorted 3D scene graph and geometric perturbations. |
| P0 | SayPlan | Foundational 3DSG + LLM task planning paper; defines planning/replanning precedent. |
| P0 | SG-Nav | Read; strong navigation benchmark path with online 3DSG prompting. |
| P0 | SCOUT / SymSearch | Read; strong object-search and relational semantic reasoning path; useful for task-level metric design. |
| P1 | 3DGraphLLM | Read; graph-to-LLM representation baseline and dataset list. |
| P1 | 3D-Mem | Read; important critique of object-centric textual 3DSG for embodied reasoning. |
| P1 | MSQA / MSNN | Benchmark source for situated QA and next-step navigation. |
| P1 | 3D-GRAND / 3D-POPE | Hallucination benchmark and grounding dataset source. |
| P1 | ConceptGraphs / OVSG / HOV-SG | Broad open-vocabulary graph systems and robotics motivation; avoid making them first reproduction targets. |

## Contribution Candidate Shape

### Candidate Problem Statement

Existing LLM/VLM task reasoning systems over 3D environments increasingly use 3DSG-like representations, but the model output is often judged by task success or answer correctness without explicitly measuring which geometric constraints were satisfied or violated. This makes it difficult to distinguish semantic reasoning failure, perception failure, graph relation failure, and geometry inconsistency.

### Candidate Hypothesis Draft

For geometry-checkable 3D scene reasoning tasks, adding an explicit 3DSG-based geometry verifier to LLM/VLM task outputs will reduce spatial hallucination and invalid decisions while preserving or improving task accuracy.

### Why This Is 3D Scene Graph Research

The core object is not only an LLM prompt or a robot policy. The core representation is a 3DSG whose relation edges and object nodes expose geometry evidence used to verify task decisions.

### What Failure Would Teach

- If verifier rejection improves consistency but reduces task accuracy, the geometry constraints are too brittle or misaligned with task semantics.
- If LLM/VLM already performs well with graph text alone, the dataset may not require real 3D geometry and may contain language shortcuts.
- If geometry evidence cannot be extracted reliably from available scenes, CAND-003 should wait for CAND-001 verifier robustness.
- If simulator setup dominates progress, return to offline graph query/refinement.
- If CAND-003 becomes a graph-to-LLM representation project, it is too close to 3DGraphLLM.
- If CAND-003 becomes an embodied scene-memory project, it is too close to 3D-Mem.

## User Judgment Needed

- CAND-003을 CAND-001의 downstream extension으로 둘지, 독립 thesis 후보로 키울지 결정해야 한다.
- 첫 pass에서는 Cut A가 가장 안전하다. Cut B나 Cut C를 선택하면 더 흥미롭지만 engineering risk가 커진다.
- `RieMind`와 `3D-VCD`가 최신 direct competition이므로, CAND-003의 차별점은 "explicit geometry evidence + task-level verifier metric + relation provenance"로 매우 좁게 잡아야 한다.
