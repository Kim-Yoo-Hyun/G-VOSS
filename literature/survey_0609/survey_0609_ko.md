# Survey 0609 한국어: 3D Scene Graph의 Semantic-Geometry Consistency Representation

- 확인 날짜: 2026-06-09 KST
- 작업 범위: 기존 H001 본류를 수정하지 않는 H001 인접 새 branch 조사
- 작업 루트: `literature/survey_0609/`
- 영문 원본: `survey_0609.md`
- 100편 논문 목록: `meta/selected_papers.md`
- PDF/cache manifest: `meta/download_manifest.json`
- Code inventory: `meta/code_inventory.md`

## 0. 검색 및 다운로드 기록

사실:

- 사용자가 요청한 "Google Scholar 관련 연구 100개" 조사는 primary-source 기반 수집으로 대체했다. Google Scholar는 공식 public API가 없고, 자동 scraping은 CAPTCHA 또는 rate limit에 걸릴 가능성이 높기 때문이다.
- Semantic Scholar Graph API는 이번 실행에서 HTTP `429 Too Many Requests`를 반환했다. 이는 보통 인증 없는 요청, shared IP 사용량, 짧은 시간 내 반복 요청 등으로 생기는 API quota/rate-limit 문제다. 논문 접근 권한이나 PDF 저작권 문제가 아니다.
- 대체로 사용한 primary source는 기존 `literature/` seed paper, arXiv API, OpenAlex API, CVF Open Access, PMLR, RSS proceedings, NeurIPS page, official project page, official GitHub repository다.
- 선정 논문: 100편.
- 로컬 PDF: 100/100 다운로드 완료. 위치는 `papers/`.
- 공식 code URL 확인: 20개.
- GitHub repository clone: 19/20개. 위치는 `repos/`.
- code 접근 실패: `SMKA`는 논문/CVF metadata에 `https://github.com/HHrEtvP/SMKA`가 적혀 있으나 GitHub 접근이 실패했다. 기존 local metadata에도 접근 불가로 기록되어 있었다.

연도별 분포:

| Year | Count |
| --- | ---: |
| 2026 | 24 |
| 2025 | 35 |
| 2024 | 20 |
| 2023 | 13 |
| 2022 | 3 |
| 2021 | 2 |
| 2020 | 2 |
| 2019 | 1 |

역할별 분포:

| Role | Count |
| --- | ---: |
| Core 3DSG / representation | 30 |
| Open-vocabulary 3DSG / grounding | 25 |
| LLM/VLM 3D reasoning | 15 |
| Semantic-geometry consistency / representation | 11 |
| Robotics / embodied graph | 11 |
| Functional / affordance graph | 3 |
| Edge-specific 3DSG representation | 2 |
| 3DGS / neural scene graph | 2 |
| Spatial-knowledge 3DSG | 1 |

Claim boundary:

- 이 문서는 100편 전체에 대한 full paper-card intake가 아니라 screened survey다.
- 기존에 이미 읽은 논문의 상세 정리는 기존 `literature/<paper-folder>/`에 유지한다.
- 새로 수집한 논문은 현재 아이디어와의 관계, 즉 "semantic relation score가 높을 때 그 relation이 3D geometry상 실제로 성립하는가"를 중심으로 screening했다.

## 1. 작업 연구 질문

사용자 아이디어:

> 3D Scene Graph에서 semantic과 geometry를 둘 다 활용해, representation 관점에서 semantic 정보와 geometry 간의 일관성을 연구한다. 즉, semantic score는 높은데 geometry상 성립하는가를 검증한다.

정제된 질문:

> 3DSG relation edge가 semantic plausibility와 geometric validity를 분리되고 calibration 가능한 quantity로 표현할 수 있는가? 그렇게 해서 semantic상 그럴듯하지만 물리적으로 일관되지 않은 relation을 detect, re-rank, abstain, repair할 수 있는가?

현재 H001과의 관계:

- 기존 H001: 기존 relation-source output에 대해 calibrated geometry-consistency evaluation/re-ranking을 수행한다.
- 새 branch: relation-edge representation 자체에 semantic confidence, geometry evidence, uncertainty, provenance를 명시적으로 넣고, 이것을 학습/평가 가능한 구조로 만든다.

추론:

- 현재 H001의 평가/재랭킹 layer와 매우 가깝지만, 논문 질문의 중심이 "평가 도구"에서 "relation representation"으로 이동한다.

## 2. 논문 간 관계 지도

### 2.1 Foundation: semantic plus 3D structure로서의 3DSG

주요 논문:

- `3D Scene Graph: A Structure for Unified Semantics, 3D Space, and Camera` (ICCV 2019)
- `Learning 3D Semantic Scene Graphs from 3D Indoor Reconstructions` (CVPR 2020)
- `SceneGraphFusion` (arXiv 2021)
- `Hydra` (RSS 2022)

사실:

- 이 논문들은 3DSG를 object, place, room, camera, relation을 연결하는 structured graph로 정의한다.
- geometry는 이미 3DSG representation의 일부다.

추론:

- 따라서 novelty는 "semantic과 geometry를 결합했다"가 될 수 없다.
- 진짜 gap은 relation-edge accountability다. 즉, edge가 semantic plausibility와 geometric validity를 구분할 만큼 충분한 evidence를 저장하는가가 핵심이다.

### 2.2 Edge modeling과 closed-set relation prediction

주요 논문:

- `SGGpoint` (CVPR 2021)
- `SMKA` (CVPR 2023)
- `VL-SAT` (CVPR 2023 Highlight)
- `SGFormer` (arXiv 2023)
- `Lang3DSG` (arXiv 2023)
- `3D-VLAP` (arXiv / TMM 2024)

사실:

- `SGGpoint`는 EdgeGCN 계열 reasoning으로 relation edge를 first-class learned object로 다룬다.
- `SMKA`는 support hierarchy, spatial knowledge, symbolic knowledge를 point-cloud relation prediction에 넣는다.
- `VL-SAT`는 visual-linguistic semantic supervision을 이용해 long-tail/ambiguous relation prediction을 개선한다.

추론:

- "edge-aware" 또는 "semantic plus geometry feature"는 이미 선행 연구가 강하다.
- 방어 가능한 branch는 learned edge representation이 predicate recall만 높이는지, 아니면 physical consistency에 calibration되어 있는지를 물어야 한다.

### 2.3 Open-vocabulary 3DSG와 queryable graph system

주요 논문:

- `Open3DSG` (CVPR 2024)
- `CCL-3DSGG` (CVPR 2024)
- `ConceptGraphs` (ICRA 2024)
- `OVSG` (CoRL 2023)
- `HOV-SG` (RSS 2024)
- `OpenGraph` (RA-L 2024)
- `Open-Vocabulary Octree-Graph` (ICCV 2025)
- `ZING-3D` (arXiv 2025)
- `VIZOR` (WACV 2026)

사실:

- 최근 system들은 CLIP/VLM/LLM feature를 사용해 queryable object, open-set relation, downstream task grounding을 다룬다.
- 일부 graph representation은 distance, vector, hierarchy, coarse spatial relation 같은 geometry-like edge attribute를 저장한다.

추론:

- Open-vocabulary relation prediction은 semantic-confidence 문제를 더 크게 만든다. language prior상 그럴듯한 relation phrase가 실제 scan geometry에서는 틀릴 수 있기 때문이다.
- 이는 또 다른 open-vocabulary generator보다 semantic/geometry decoupling representation을 지지한다.

### 2.4 Semantic-geometry consistency와 직접 novelty threat

주요 논문:

- `RelWitness` (arXiv 2026)
- `FirePlace` (CVPR 2025)
- `RieMind` (arXiv 2026)
- `3D-VCD` (CVPR 2026 accepted / arXiv)
- `SG-PGM` (arXiv 2024)
- `GREAT` (CVPR 2025)
- `ToLL` (arXiv 2026)
- `Statistical Confidence Rescoring for Robust 3D Scene Graph Generation from Multi-View Images` (arXiv 2025)

사실:

- `RelWitness`는 가장 가까운 novelty threat다. open-vocabulary 3DSG에서 visual-geometric relation witness와 calibrated witness quality를 명시적으로 제안한다.
- `FirePlace`와 `RieMind`는 LLM semantic/common-sense reasoning이 explicit 3D geometric refinement 또는 tool로 개선될 수 있음을 보인다.
- `3D-VCD`는 scene-graph perturbation / contrastive decoding을 통해 hallucination mitigation을 다룬다.
- `SG-PGM`과 `GREAT`는 downstream alignment와 affordance grounding에서 semantic-geometric fusion을 사용한다.

추론:

- 새 branch는 geometry verification, witness, semantic-geometric fusion, calibration을 처음 썼다고 주장하면 안 된다.
- 더 강한 claim은 여러 relation source에서 semantic confidence와 geometry validity를 representation level에서 분리하고, explicit controls로 그 mismatch를 평가한다는 것이다.

### 2.5 LLM/VLM graph reasoning과 downstream task

주요 논문:

- `SayPlan` (CoRL 2023 Oral)
- `SG-Nav` (NeurIPS 2024)
- `3DGraphLLM` (ICCV 2025)
- `3D-Mem` (CVPR 2025)
- `3D-GRAND` (CVPR 2025)
- `SCOUT/SymSearch` (arXiv 2026)
- `SceneGraphGrounder` (arXiv 2026)
- `View-on-Graph` (AAAI 2026)
- `GraphEQA`, `GraphPad`, `EmbodiedRAG`

사실:

- 3DSG는 LLM/VLM planning, navigation, visual grounding, QA, embodied reasoning의 interface로 점점 더 많이 쓰이고 있다.
- 이런 system들은 task success, grounding accuracy, hallucination을 평가하지만, relation-level semantic error와 geometry violation을 항상 분리하지는 않는다.

추론:

- downstream 사용성은 relation consistency가 왜 중요한지 설명하는 motivation이다.
- 하지만 relation-level representation이 먼저 검증되기 전에는 downstream task를 main branch로 삼지 않는 편이 안전하다.

### 2.6 Functional, affordance, articulation, dynamic graph

주요 논문:

- `OpenFunGraph` (CVPR 2025 Highlight)
- `FunGraph` (arXiv 2025)
- `FunFact` (arXiv 2026)
- `ArtiSG` (arXiv 2025)
- `Pandora` (arXiv 2026)
- `DovSG` (T-RO/arXiv 2024)
- `FROSS` (ICCV 2025)
- `LOST-3DSG`, `DGSG-Mind`, `OGScene3D`

사실:

- Functional/articulated relation은 단순 spatial predicate를 넘어선다.
- Dynamic/online system은 graph update와 temporal consistency를 요구한다.

추론:

- 이 축들은 좋은 future extension이지만, 첫 representation branch로는 범위가 너무 넓다.
- H001 continuity를 유지하려면 먼저 geometry-checkable relation family에서 시작하고, functional/attachment/articulation은 이후 확장으로 두는 것이 안전하다.

## 3. Code 조사 요약

전체 static inventory는 `meta/code_inventory.md`에 있다.

| Code group | Repositories | 이 branch에 유용한 점 | 한계 |
| --- | --- | --- | --- |
| Closed-set 3DSG edge models | `SGGpoint`, `VL-SAT` | Edge feature extraction, relation score, 3DSSG-compatible baseline | 대부분 label prediction 중심이고 explicit validity channel이 없다 |
| Open-vocabulary relation sources | `Open3DSG`, `OpenFunGraph`, `FROSS` | Open-set relation proposal과 source adapter | relation confidence가 geometry-calibrated라고 보장되지 않는다 |
| Queryable/open-vocab maps | `ConceptGraphs`, `OVSG`, `HOV-SG`, `OpenGraph`, `Octree-Graph` | Node/edge graph construction, object retrieval, distance/vector field | 주로 map/downstream system 중심이고 relation-level consistency benchmark가 아니다 |
| Upstream open-vocab perception | `OpenScene`, `OpenMask3D`, `LangSplat` | Object feature, mask, language field | node/object level 중심이라 edge validity에는 부족하다 |
| Robotics graph infrastructure | `Hydra`, `DovSG`, `SG-Nav`, `3D-Mem` | Hierarchy, online graph update, downstream task motivation | simulator/planning complexity가 커진다 |
| Graph-to-LLM interfaces | `3DGraphLLM`, `Beyond Bare Queries` | Graph serialization/embedding, relation use in language task | semantic-score/geometric-validity decoupling을 직접 해결하지 않는다 |

구현 추론:

- H001-compatible branch에서 가장 재사용성이 높은 코드는 여전히 `VL-SAT`와 `Open3DSG` relation source, 그리고 기존 H001 geometry join artifact다.
- `Octree-Graph`, `OVSG`, `HOV-SG`, `OpenGraph`는 hierarchy, distance, vector, queryable graph structure를 보여주는 representation reference다.
- `RelWitness`는 방법론적으로 매우 가깝지만 이번 run에서는 official code를 찾지 못했다. 실행 baseline이 아니라 required related-work boundary로 다루는 것이 맞다.

## 4. 이 아이디어에 대한 문헌상의 함의

사실:

- 3DSG는 이미 semantic과 spatial structure를 함께 인코딩한다.
- Open-vocabulary 및 VLM 기반 3DSG는 이제 흔한 흐름이 되었다.
- 최근 논문들은 geometry, witness, distance, task-grounding evidence를 점점 더 명시적으로 노출한다.
- 현재 H001에는 이미 Docker-generated `VL-SAT`/`Open3DSG` source output, geometry join, violation metric, controls, bootstrap evidence가 있다.

Paper claim 함의:

- 약한 claim: "We combine semantic and geometry in 3DSG."
- 더 강한 claim: "Relation semantic confidence와 geometric validity는 서로 다른 변수이며, 그 mismatch를 정량화하고, 그 mismatch를 관찰/활용할 수 있는 relation-edge representation을 학습/평가한다."

Reviewer-defense 함의:

- high semantic score지만 invalid geometry인 사례를 보여야 한다.
- geometry-only 또는 hard-rule filtering만으로 충분하지 않음을 보여야 한다.
- recall/coverage cost와 denominator caveat를 반드시 보고해야 한다.
- wrong-pair/shuffled-geometry와 family-specific control을 포함해야 한다.
- source-agnostic claim을 하려면 최소 두 relation source를 비교해야 한다.

## 5. 적용 가능한 방법 제안 7개

### Method 1. Dual-Channel Relation Edge Representation

핵심 아이디어:

- 모든 candidate edge를 다음처럼 표현한다.
  `edge = (subject, object, predicate_text, semantic_score, geometry_evidence, p_geom_valid, uncertainty, provenance)`
- `semantic_score`와 `p_geom_valid`를 하나의 confidence로 합치지 않고 분리해 유지한다.

H001 통합:

- 현재 H001의 `VL-SAT`와 `Open3DSG` row에 바로 적용 가능하다.
- 기존 geometry join은 distance, vertical order, contact/support evidence, overlap, relation family, verifier decision을 제공할 수 있다.

평가:

- `Recall@K`, `Violation@K`, `p_geom_valid`의 `ECE/Brier`, high-semantic invalid rate, abstention coverage.

Novelty risk:

- `Octree-Graph`, `Open3DSG`, `RelWitness`, `SGGpoint`를 반드시 cite해야 한다.
- novelty는 edge tuple 자체가 아니라 semantic-validity separation과 calibrated evaluation에 있다.

판정:

- 가장 좋은 첫 branch다. 구현 위험이 낮고 현재 H001과 가장 잘 맞는다.

### Method 2. Semantic-Geometry Consistency Embedding

핵심 아이디어:

- valid `(predicate, subject geometry, object geometry, pair geometry)` tuple은 가깝게, counterfactual invalid tuple은 멀게 배치하는 embedding을 학습한다.
- positive GT relation과 wrong-pair, swapped-subject/object, shuffled-geometry, predicate-family counterfactual 같은 generated negative를 사용한다.

H001 통합:

- 현재 H001 exact-label GT positive와 GT-derived negative를 사용한다.
- 먼저 `support_contact`, `proximity`, `relative_vertical`로 시작한다. `attachment_deferred`는 별도 사용자 확인 뒤에만 추가한다.

평가:

- valid vs invalid AUROC/AUPRC.
- semantic candidate 중 valid edge retrieval.
- wrong-pair control robustness.
- `VL-SAT`에서 `Open3DSG`로 calibration transfer.

Novelty risk:

- contrastive / visual-linguistic pretraining 계열과 유사할 수 있다.
- 차별점은 object/node semantic이 아니라 relation-level semantic-geometry consistency에 집중하는 것이다.

판정:

- 작은 모델을 학습할 시간이 있다면 가장 강한 representation-method 후보.

### Method 3. Score Decomposition: Semantic Prior Plus Geometry Residual

핵심 아이디어:

- relation confidence를 다음처럼 분해한다.
  `logit(edge_valid) = f_sem(predicate, labels, source_score) + f_geom(3D evidence) + f_interaction(predicate, geometry)`
- 논문의 핵심 분석은 `f_sem`은 높지만 `f_geom`이 contradict하는 경우다.

H001 통합:

- 현재 semantic-only score를 `f_sem` input으로 사용한다.
- 기존 verifier/calibrator feature를 `f_geom`으로 사용한다.
- train/train-dev에서만 train/calibrate하고 validation metric만 보고한다.

평가:

- semantic-only vs geometry-only vs decomposed model.
- family별 calibration curve.
- high-semantic/low-geometry quadrant analysis.

Novelty risk:

- decomposition을 분석하지 않으면 단순 calibrated reranker처럼 보일 수 있다.

판정:

- 현재 H001 re-ranking에서 가장 위험이 낮은 upgrade.

### Method 4. Graph-Level Consistency Energy

핵심 아이디어:

- edge를 독립적으로 scoring하는 대신 graph-level consistency를 본다.
- 예: conflicting support direction, impossible vertical cycle, incompatible contact/proximity state, 동일 object pair의 duplicate contradictory predicate를 penalty로 둔다.

H001 통합:

- reliable edge-level score가 필요하므로 Method 1 또는 Method 3 이후에 시작한다.
- H001 prediction row를 candidate로 두고, subgraph별 small graph energy 또는 factor graph를 최적화한다.

평가:

- Edge-level `Violation@K`.
- Graph-level contradiction count.
- Recall loss.
- Qualitative failure taxonomy.

Novelty risk:

- factor-graph reasoning, Hydra-style spatial structure, `FunFact`와 관련된다.
- full robot planning이 아니라 relation consistency로 scope를 유지해야 한다.

판정:

- 좋은 second-stage method다. 첫 branch로는 너무 넓다.

### Method 5. Counterfactual Consistency Benchmark

핵심 아이디어:

- semantic plausibility와 geometry를 의도적으로 분리하는 benchmark protocol을 만든다.
- 예: wrong pair, shuffled geometry, swapped subject/object, perturbed object height, removed contact, relation-family label flip.

H001 통합:

- 현재 H001 control에도 wrong-pair/shuffled-style 아이디어가 이미 있다.
- 이를 representation benchmark로 formalize한다.
- 같은 `VL-SAT`와 `Open3DSG` source output을 사용한다.

평가:

- Counterfactual sensitivity.
- Geometry corruption에서 false-valid rate.
- Geometry-breaking perturbation에 대한 semantic-score invariance.

Novelty risk:

- benchmark-only contribution은 method evidence 또는 매우 강한 diagnostic result가 필요하다.

판정:

- evaluation component로는 필수지만, 단독 main method로는 부족하다.

### Method 6. Evidence-Retrieval Relation Verifier

핵심 아이디어:

- semantic relation proposal마다 geometry evidence와 필요 시 visual witness view를 retrieve하고, 그 evidence가 relation을 support하는지 scoring한다.
- relation edge는 scalar score만 저장하지 않고 evidence provenance를 저장한다.

H001 통합:

- 기존 H001 geometry evidence를 첫 evidence source로 사용할 수 있다.
- Qwen-VL 또는 image crop은 후속 third-source extension으로 가능하지만, Docker inference/validation이 끝나기 전에는 main evidence로 두지 않는다.

평가:

- Evidence availability.
- Evidence sufficiency.
- Invalid high-semantic relation demotion.
- Human-auditable examples.

Novelty risk:

- `RelWitness`와 매우 가깝다.
- 이 branch는 first witness evidence가 아니라 arbitrary relation-source reliability, denominator transparency, existing-source re-ranking을 강조해야 한다.

판정:

- 가치 있지만 Related Work positioning을 매우 조심한 뒤 진행해야 한다.

### Method 7. Uncertainty-Gated Graph Interface For LLM/Robot Tasks

핵심 아이디어:

- semantic channel과 geometry channel이 동의하는 relation edge만 LLM/planner에 노출한다.
- 불일치하면 abstain, ask for more evidence, uncertain 표시를 한다.

H001 통합:

- Method 1의 edge representation을 input으로 사용한다.
- full navigation이 아니라 graph QA/grounding/target-selection 같은 offline task부터 평가한다.

평가:

- Invalid answer rate.
- Hallucinated relation use.
- Abstention rate.
- Task accuracy.
- Relation-violation breakdown.

Novelty risk:

- `SayPlan`, `SG-Nav`, `3DGraphLLM`, `RieMind`, `3D-VCD`, `3D-Mem`과 겹친다.
- downstream validation으로 두고 main contribution으로 키우지 않는 것이 안전하다.

판정:

- relation representation 검증 이후의 좋은 future extension.

## 6. 추천 branch 계획

추천 main direction:

> Semantic-Geometry Consistency Edge Representation for 3D Scene Graphs.

최소 1차 prototype:

1. 기존 H001 `VL-SAT`와 `Open3DSG` relation-source output을 사용한다.
2. Method 1의 dual-channel edge schema를 정의한다.
3. Method 3의 score decomposition을 첫 trainable/calibrated model로 추가한다.
4. Method 5의 control을 benchmark protocol로 사용한다.
5. Edge-level metric과 quadrant analysis를 함께 보고한다.
   - high semantic / high geometry
   - high semantic / low geometry
   - low semantic / high geometry
   - low semantic / low geometry

처음부터 하지 말아야 할 것:

- 새로운 open-vocabulary 3DSG generator 만들기.
- full robot navigation/planning.
- functional 또는 articulated relation을 main scope로 삼기.
- Qwen-VL을 full Docker validation 전에 main evidence로 쓰기.

성공 시 가능한 paper claim:

> Open-vocabulary 3DSG의 relation confidence는 하나의 quantity가 아니다. Semantic plausibility와 geometric validity는 불일치할 수 있다. Dual-channel calibrated relation-edge representation은 이 불일치를 드러내고, source-transfer와 counterfactual geometry control에서 reliability를 개선한다.

## 7. Orthogonal Persona Review

### Persona A: 3DSSG / Computer Vision Method Reviewer

Review stance:

- 이 reviewer는 `SGGpoint`, `VL-SAT`, `Open3DSG`, `CCL-3DSGG`, `FROSS`, `VIZOR`, 특히 `RelWitness` 대비 novelty를 본다.

Assessment:

- 통합 가능성: 가능.
- 핵심 우려: representation question이 중심이 아니면 "또 다른 geometry verifier"로 보일 수 있다.
- 필요한 evidence:
  - `VL-SAT`만이 아니라 두 relation source.
  - Counterfactual geometry controls.
  - Per-family analysis.
  - Recall/violation tradeoff.
  - `RelWitness`와의 차이: first witness evidence가 아니라 existing-source reliability와 semantic/geometry score separation.

판정:

- calibrated relation-edge representation과 reliability diagnosis로 framing하면 가능한 branch다.
- "3DSG에 geometry를 추가했다"로 framing하면 약하다.

### Persona B: ML Representation / Calibration Reviewer

Review stance:

- 이 reviewer는 semantic channel과 geometry channel이 통계적으로 의미 있고 calibration되어 있으며 validation에 tuning되지 않았는지를 본다.

Assessment:

- 통합 가능성: 가능. H001에는 이미 GT positive, GT-derived negative, source score, geometry feature, bootstrap machinery가 있다.
- 핵심 우려: hand-designed feature와 threshold가 post hoc처럼 보일 수 있다.
- 필요한 evidence:
  - Train/train-dev-only fitting.
  - Calibration curve, Brier/NLL/ECE, AUROC/AUPRC.
  - Wrong-pair와 shuffled-geometry control.
  - Source-transfer test: 하나의 source 또는 train-dev에서 fit하고 `VL-SAT`와 `Open3DSG` 모두에서 평가.
  - Ablation: semantic-only, geometry-only, dual-channel, interaction/decomposition.

판정:

- 통합 경로가 강하다.
- Method 2 또는 Method 3가 rule-based verifier 이상의 branch로 만들어줄 수 있다.

### Persona C: Robotics / Embodied AI Reviewer

Review stance:

- 이 reviewer는 reliable relation edge가 benchmark table뿐 아니라 downstream task에 의미가 있는지를 본다.

Assessment:

- 통합 가능성: 가능하지만 downstream은 secondary여야 한다.
- 핵심 우려: branch가 navigation/search/planning으로 바로 가면 simulator/perception complexity가 thesis를 압도한다.
- 필요한 evidence:
  - Offline relation reliability를 main claim으로 유지.
  - Relation metric이 안정된 뒤에만 작은 downstream sanity check 추가.
  - Robot은 high-semantic but geometry-invalid edge에 따라 행동하면 안 되므로 abstention/uncertainty behavior 보고.
  - ObjectNav나 full manipulation보다 graph QA/grounding/target-selection부터 시작.

판정:

- 장기 가치는 좋지만 첫 paper는 robotics system paper가 되면 안 된다.

## 8. 최종 feasibility 판단

사실:

- 현재 literature에는 open-vocabulary 및 LLM/VLM 3D graph system이 매우 많다.
- 직접 선행 연구는 이미 edge modeling, spatial knowledge, visual-linguistic training, open-vocabulary graph generation, geometry witness, functional relation, LLM geometry tool을 다룬다.
- 현재 H001 artifact는 드문 장점을 갖고 있다: 두 relation source, geometry join, violation metric, calibration artifact, controls, denominator-transparent report가 이미 있다.

추론:

- 이 아이디어는 representation/calibration 문제로 다룰 때 viable하다.
- Semantic confidence는 geometric validity와 같지 않다는 점을 중심으로 세워야 한다.
- 가장 방어 가능한 새 branch는 새 3DSG generator가 아니라, semantic-geometry disagreement를 expose, calibrate, evaluate하는 relation-edge representation이다.
- 가장 강한 초기 조합은 Method 1 + Method 3 + Method 5다:
  dual-channel representation, score decomposition, counterfactual consistency benchmark.

이 branch를 promote할 경우 추천 next file:

- `hypothesis/CAND-001/H001_geometry-grounded-verification/semantic_geometry_representation_0609.md`

아직 main H001 paper claim으로 promote하지 말 것:

- 이 문서는 branch exploration이다.
- Claim expansion은 명시적인 사용자 결정과 Docker-reproducible evidence가 생긴 뒤에 해야 한다.

