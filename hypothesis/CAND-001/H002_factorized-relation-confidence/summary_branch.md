# H002 Factorized Relation Confidence

- 작성일: 2026-06-11 KST
- 위치: `hypothesis/CAND-001/H002_factorized-relation-confidence/`
- 상태: branch-level 초기 hypothesis 정리
- 보존 원칙: 기존 `H001_geometry-grounded-verification/` 및 기존 H001 실험/논문 산출물은 수정하지 않는다.
- 근거 문서: `literature/survey_0609/survey_0609_ko.md`, `literature/survey_0609/meta/selected_papers.md`, 기존 H001 artifact/report.
- 2026-06-11 방향 결정: H002는 `Relation-Geometric Agreement Benchmark`로 문제를 정의하고, `Semantic-Geometric Factor Graph Rescoring`으로 푸는 방향을 우선 검증한다.

## Research Direction

새 방향은 3D Scene Graph relation edge의 confidence를 하나의 점수로 보지 않고, `semantic plausibility`와 `geometric validity`를 분리된 변수로 표현하는 연구다. H002의 현재 우선순위는 문제를 새 metric/benchmark인 `RGA(Relation-Geometric Agreement)`로 명확히 정의하고, 그 다음 `Semantic-Geometric Factor Graph Rescoring`으로 edge validity posterior를 재계산하는 것이다.

핵심 방향:

> Factorized relation confidence representation for 3D Scene Graphs: semantic score가 높은 relation이 실제 3D geometry에서 성립하는지 `RGA`로 분리 측정하고, semantic prior와 geometric residual을 factor graph로 결합해 edge validity posterior를 재계산한다.

H001과의 차이:

- H001은 기존 relation predictor output을 geometry consistency로 평가하고 re-ranking하는 reliability layer다.
- H002는 relation confidence 자체가 왜 단일 score여야 하는지 문제 삼고, relation edge representation을 `semantic channel`과 `geometry channel`로 factorize한다.
- 따라서 H002는 H001의 후처리/평가 관점보다 한 단계 원리적인 representation 관점의 연구다.

권장 paper framing:

> Existing 3DSSG relation predictors conflate semantic plausibility and geometric validity into a single relation confidence. H002 factorizes relation confidence into semantic and geometry channels, then evaluates and reduces their disagreement through score decomposition and counterfactual geometry controls.

현재 더 구체적인 framing:

> Existing 3DSSG metrics reward relation-label correctness without separately measuring whether the predicted relation is geometrically satisfiable in the observed 3D scene. H002 introduces `Relation-Geometric Agreement (RGA)` to expose this semantic-geometric mismatch, and uses semantic-geometric factor graph rescoring to estimate edge validity posterior from semantic prior, node confidence, and metric constraint residuals.

## Research Background

사실:

- 3D Scene Graph는 원래 object, relation, spatial structure를 함께 표현하려는 graph representation이다.
- `3DSSG`, `SGGpoint`, `SMKA`, `VL-SAT`는 point cloud 기반 relation prediction, edge reasoning, spatial knowledge, visual-linguistic semantic supervision을 다룬다.
- `Open3DSG`, `CCL-3DSGG`, `ConceptGraphs`, `HOV-SG`, `Open-Vocabulary Octree-Graph`, `FROSS`, `ZING-3D`, `VIZOR`는 open-vocabulary / queryable / online / VLM-based 3D graph 흐름을 확장한다.
- `RelWitness`, `FirePlace`, `RieMind`, `3D-VCD`, `SG-PGM`, `GREAT`는 relation witness, geometry refinement, hallucination mitigation, semantic-geometric fusion을 이미 선행 연구로 만든다.
- 기존 H001은 `VL-SAT`와 Open3DSG 두 relation source에 대해 geometry join, `p_geom_valid`, `Violation@K`, controls, bootstrap, failure rows, qualitative inspection을 이미 확보했다.

추론:

- "semantic과 geometry를 결합한다"는 연구 방향은 이미 너무 넓고 novelty가 약하다.
- 더 강한 질문은 "semantic score와 geometry validity가 왜 하나의 confidence로 합쳐져야 하는가?"이다.
- H002는 3DSG relation edge를 `semantic_score`, `geometry_evidence`, `p_geom_valid`, `uncertainty`, `provenance`를 가진 factorized representation으로 정의함으로써 H001의 문제를 더 근본적으로 다룬다.

## Motivation

기존 3DSSG/open-vocabulary 3DSG relation predictor는 보통 relation 후보에 하나의 score 또는 rank를 부여한다. 이 score는 semantic prior, dataset frequency, visual-language association, point-cloud geometry, object label plausibility가 섞인 값일 수 있다.

문제는 다음과 같다.

- `cup on table`처럼 semantic prior가 강한 relation은 실제 contact/support geometry가 약해도 높은 score를 받을 수 있다.
- `chair near table`처럼 language상 그럴듯한 relation은 실제 3D distance나 object pair identity가 맞지 않아도 후보로 남을 수 있다.
- `picture above sofa`처럼 semantic relation이 plausible해도 vertical order, wall attachment, object support evidence가 불충분할 수 있다.
- LLM/VLM downstream task는 이런 high-semantic but geometry-invalid edge를 신뢰하면 hallucinated answer, invalid target selection, infeasible planning을 만들 수 있다.

H001은 이 문제를 geometry-consistency evaluation/re-ranking으로 완화했다. H002는 더 근본적으로 relation edge가 처음부터 다음 질문에 답해야 한다고 본다.

> 이 relation은 semantic상 그럴듯한가? 그리고 별도로, 이 relation은 현재 3D geometry에서 성립하는가?

## Limitation of Existing Work

### 1. Core 3DSG relation prediction의 한계

`3DSSG`, `SGGpoint`, `SMKA`, `VL-SAT` 계열은 relation prediction 성능을 높이지만, relation confidence를 semantic plausibility와 geometric validity로 명시적으로 분해하지 않는다.

한계:

- edge feature는 존재하지만 validity channel이 분리되어 있지 않다.
- Recall@K/mR@K는 semantic label matching에는 유용하지만 high-semantic/low-geometry failure를 직접 측정하지 않는다.
- spatial knowledge가 들어가도 그 knowledge가 relation-level physical consistency로 calibration되었는지는 별도 문제다.

### 2. Open-vocabulary 3DSG의 한계

`Open3DSG`, `CCL-3DSGG`, `FROSS`, `VIZOR`, `ZING-3D` 등은 open-vocabulary relation generation 또는 queryable graph를 강화한다.

한계:

- language prior가 강해질수록 semantic plausibility와 metric/topological geometry의 불일치가 커질 수 있다.
- relation phrase가 open-vocabulary로 풍부해져도, 해당 phrase가 실제 scan geometry에서 성립하는지는 별도로 검증되어야 한다.
- source confidence가 geometry-calibrated라고 보장되지 않는다.

### 3. Geometry evidence / witness 계열의 한계

`RelWitness`는 visual-geometric relation witness와 calibrated witness quality를 명시적으로 다루므로 직접 novelty threat다.

한계 또는 H002의 차별점:

- H002는 witness generation 자체가 아니라 existing relation-source confidence의 factorization과 source-transfer reliability를 목표로 한다.
- H002는 `semantic_score`와 `p_geom_valid`의 disagreement를 counterfactual geometry benchmark로 측정한다.
- 따라서 "geometry evidence를 쓴다"가 아니라 "semantic confidence와 geometry validity가 분리 가능한 failure signal인지 검증한다"가 핵심이다.

### 4. Downstream LLM/VLM 3D reasoning의 한계

`SayPlan`, `SG-Nav`, `3DGraphLLM`, `3D-Mem`, `RieMind`, `3D-VCD`는 3D graph를 planning, grounding, QA, hallucination mitigation에 사용한다.

한계:

- downstream success/failure가 relation semantic error인지, geometry violation인지, perception failure인지 분리되지 않는 경우가 많다.
- H002는 downstream system을 새로 만드는 대신 relation edge reliability를 먼저 분해해 downstream risk를 설명할 수 있는 기반을 만든다.

## Problem Definition

H002의 문제 정의는 `RGA(Relation-Geometric Agreement)`를 중심으로 둔다.

기존 relation evaluation은 대체로 predicted predicate가 GT label과 맞는지를 본다. 그러나 H002가 다루는 실패는 label correctness와 별개로, predicted relation이 실제 3D scene geometry에서 성립 가능한지다.

H002가 분리해서 보는 두 축:

- `Relation-label correctness`: predicate label 또는 open relation text가 semantic/annotation 기준으로 맞는가?
- `Geometric satisfiability`: 그 relation이 object pair의 3D geometry에서 성립하는가?

`RGA`는 이 둘을 동시에 보되, 하나로 뭉개지 않는다. 예를 들어 `on` label이 semantic상 plausible하더라도 support/contact evidence가 없으면 `label plausible / geometry unsatisfied`로 기록한다.

### Input

한 scene/subgraph에서 object pair `(s, o)`와 predicate candidate `p`가 주어진다.

각 candidate edge는 relation source에서 다음 정보를 받을 수 있다.

- subject/object identity
- object labels
- predicate label or predicate text
- source semantic score 또는 rank
- scan/subgraph id
- optional visual-language feature

3D geometry module은 다음 evidence를 제공할 수 있다.

- distance / normalized distance
- vertical order
- support/contact evidence
- overlap / projection evidence
- object size and bounding box
- relation-family-specific geometry features
- geometry evidence provenance

### Output

H002의 edge representation은 최소 다음 필드를 가져야 한다.

```text
edge = {
  subject_id,
  object_id,
  predicate,
  semantic_score,
  geometry_evidence,
  p_geom_valid,
  semantic_geometry_disagreement,
  uncertainty,
  provenance
}
```

### Core problem

기존 relation source의 단일 confidence가 다음 두 변수를 conflation한다고 본다.

- `S(e)`: relation edge `e`의 semantic plausibility
- `G(e)`: relation edge `e`의 geometric validity

H002의 핵심 문제는 `RGA`로 다음 mismatch를 측정하고 줄이는 것이다.

```text
High S(e), Low G(e)
```

즉 semantic score는 높지만 실제 3D geometry에서 relation이 성립하지 않는 edge를 찾고, 그 원인을 relation representation과 score decomposition으로 설명한다.

초기 `RGA` schema:

```text
RGA(e) = {
  label_match: true/false/unknown,
  geom_satisfied: true/false/uncertain,
  semantic_score: float,
  geom_residual: dict,
  p_geom_valid: float,
  rga_bucket: HH / HL / LH / LL,
  evidence_family: support_contact / proximity / relative_vertical / ...
}
```

여기서 `HL`은 high semantic / low geometry이며 H002의 핵심 failure bucket이다.

### Falsification condition

다음 결과가 나오면 H002의 핵심 가설은 약해진다.

- `semantic_score`와 `p_geom_valid`가 거의 같은 signal이라 분리할 이득이 없다.
- high-semantic/low-geometry quadrant가 드물거나 failure taxonomy상 의미가 없다.
- `RGA`가 기존 `Violation@K`나 H001 table을 이름만 바꾼 수준이라 별도 metric/benchmark 역할을 하지 못한다.
- factor graph rescoring이 H001의 기존 calibrated re-ranking보다 설명력이나 robustness를 추가하지 못한다.
- counterfactual geometry corruption에서 semantic score와 geometry validity가 함께 변해 factorization의 필요성이 약해진다.
- `VL-SAT`와 Open3DSG 사이에 현상이 재현되지 않는다.

## Core Hypothesis

H002:

> 3D Scene Graph relation confidence는 단일 score가 아니라 semantic plausibility와 geometric validity로 factorize되어야 한다. 기존 relation predictor와 기존 relation-label 중심 metric은 두 변수를 conflation하기 때문에 high-semantic but geometry-invalid relation을 숨길 수 있다. `RGA(Relation-Geometric Agreement)`는 이 mismatch를 측정하고, semantic-geometric factor graph rescoring은 semantic prior, node confidence, and metric constraint residual을 결합해 edge validity posterior를 더 신뢰성 있게 추정할 수 있다.

세부 가설:

1. `semantic_score`와 `p_geom_valid`는 서로 다른 failure signal을 가진다.
2. `RGA`의 high-semantic/low-geometry bucket은 `VL-SAT`와 Open3DSG 모두에서 반복적으로 나타난다.
3. semantic-geometric factor graph rescoring은 semantic-only, geometry-only, hard-rule-only, 기존 H001 re-ranking보다 counterfactual robustness와 calibration이 좋다.
4. counterfactual geometry benchmark는 기존 semantic score가 geometry corruption에 취약함을 드러낸다.
5. factorized representation은 recall tradeoff를 숨기지 않고 `Recall@K`, `Violation@K`, calibration, abstention coverage를 함께 보고할 수 있다.

성공 기준:

- 두 relation source에서 high-semantic/low-geometry failure가 확인된다.
- `RGA`가 기존 label recall과 다른 failure bucket을 안정적으로 드러낸다.
- factor graph rescoring이 semantic-only 대비 `Violation@K`와 `RGA-HL rate`를 낮추고 recall loss를 명시적으로 관리한다.
- geometry-only 또는 hard-rule-only보다 calibration/recall tradeoff가 낫다.
- wrong-pair/shuffled-geometry/swapped-pair counterfactual에서 factorized model이 semantic-only보다 false-valid rate를 낮춘다.

## Proposed Framework

H002의 초기 framework는 `RGA(Relation-Geometric Agreement) benchmark`로 문제를 정의한 뒤, `Semantic-Geometric Factor Graph Rescoring`으로 푸는 구조다. 기존 Method 1/3/5 용어로 보면 dual-channel edge representation과 counterfactual consistency는 유지하되, 중심 method는 factor graph posterior rescoring으로 재정렬한다.

### Module 1. Source Adapter

목표:

- `VL-SAT`, Open3DSG, optional Qwen-VL relation output을 공통 edge schema로 변환한다.

초기 범위:

- H001에서 이미 Docker-generated artifact가 있는 `VL-SAT`와 Open3DSG를 우선 사용한다.
- Qwen-VL은 full Docker validation 전까지 main evidence로 쓰지 않는다.

### Module 2. Dual-Channel Edge Representation

목표:

- relation edge에 semantic channel과 geometry channel을 분리 저장한다.

필드:

- `semantic_score`: relation source의 score/rank/logit.
- `geometry_evidence`: family-specific geometry feature.
- `p_geom_valid`: calibrated probability that relation is geometrically valid.
- `semantic_geometry_disagreement`: `semantic_score`와 `p_geom_valid`의 불일치 지표.
- `uncertainty`: abstention 또는 deferred decision을 위한 confidence.
- `provenance`: source, split, scan, object pair, geometry join version.

### Module 3. RGA Benchmark Layer

목표:

- 기존 label recall만으로는 보이지 않는 semantic-geometric mismatch를 `RGA`로 측정한다.

초기 bucket:

- `RGA-HH`: high semantic / geometry satisfied
- `RGA-HL`: high semantic / geometry unsatisfied
- `RGA-LH`: low semantic / geometry satisfied
- `RGA-LL`: low semantic / geometry unsatisfied
- `RGA-HU`: high semantic / geometry uncertain

핵심 metric:

- `RGA-HL@K`: top-K relation 중 high-semantic but geometry-unsatisfied 비율.
- `RGA-valid@K`: top-K relation 중 geometry satisfied 또는 nonviolated 비율.
- `RGA-disagreement`: semantic score와 geometry validity score의 disagreement.
- `RGA-coverage`: RGA 판정이 가능한 candidate/GT denominator 비율.

### Module 4. Semantic-Geometric Factor Graph Rescoring

목표:

- relation confidence를 semantic prior, node confidence, metric residual factor로 분해해 edge validity posterior를 재계산한다.

형식:

```text
P(valid_e | factors)
  proportional to
    phi_sem(predicate, source_score, language_prior)
  * phi_node(subject_class_conf, object_class_conf)
  * phi_geom(metric_residuals, relation_family)
  * phi_consistency(optional graph-level constraints)
```

초기 factor:

- `semantic prior`: source relation score/rank, predicate family, object label compatibility.
- `node confidence`: subject/object class confidence. H001 artifact에서 없으면 초기에는 constant 또는 unavailable로 둔다.
- `metric residual`: distance, vertical order, support/contact, overlap 등 H001 geometry evidence.
- `temporal observation count`: 초기 offline H002에서는 제외하고 future extension으로 둔다.

출력:

- `posterior_edge_valid`
- `posterior_rga_bucket`
- `factor_contribution`
- `abstain_or_promote` decision

비교 조건:

- semantic-only
- geometry-only
- H001 probabilistic re-ranking
- hard-rule verified condition
- semantic-geometric factor graph rescoring

### Module 5. Counterfactual Consistency Benchmark

목표:

- semantic plausibility는 유지하면서 geometry만 깨거나 바꾸는 benchmark를 만든다.

Counterfactual types:

- wrong-pair counterfactual
- shuffled-geometry counterfactual
- swapped subject/object
- relation-family label flip
- distance perturbation
- support/contact removal
- vertical order inversion

측정 질문:

- semantic score가 geometry corruption에 둔감한가?
- decomposed model은 corrupted geometry를 invalid로 낮추는가?
- relation family별로 어떤 counterfactual이 가장 치명적인가?

### Module 6. Quadrant Analysis

각 edge를 다음 네 quadrant로 나눈다.

| Quadrant | 의미 | 해석 |
| --- | --- | --- |
| High semantic / High geometry | semantic과 geometry가 모두 지지 | reliable relation |
| High semantic / Low geometry | semantic은 그럴듯하지만 geometry 위반 | 핵심 failure mode |
| Low semantic / High geometry | geometry는 맞지만 semantic source가 낮게 평가 | missed relation / source bias |
| Low semantic / Low geometry | 둘 다 약함 | reject 또는 low priority |

H002의 핵심 분석은 두 번째 quadrant를 정량화하고 줄이는 것이다.

## Experiment Plan(Metric, Baseline)

### Dataset / Source

초기 검증은 기존 H001 artifact를 재사용한다.

- Dataset: `3DSSG_subset` / `3RScan`
- Relation sources:
  - `VL-SAT`
  - Open3DSG full-validation recovery branch
- Relation families:
  - `support_contact`
  - `proximity`
  - `relative_vertical`
- Optional future family:
  - `attachment_deferred`는 별도 사용자 확인 전에는 main H002 claim에 넣지 않는다.

Paper experiment로 승격할 경우:

- 모든 결과는 Docker command로 재생성 가능해야 한다.
- Host-only 결과는 hypothesis debugging/smoke evidence로만 둔다.

### Baselines

Primary baselines:

1. `semantic_only`
   - relation source score/rank만 사용.
2. `geometry_only`
   - semantic score 없이 geometry evidence만 사용.
3. `H001 probabilistic_recalibrated`
   - 기존 H001 calibrated geometry re-ranking.
4. `rule_verified`
   - hard geometry rule로 invalid edge 제거.
5. `family_specific_p_geom_valid`
   - family-specific geometry validity calibration.
6. `semantic_geometric_factor_graph`
   - H002 proposed condition. Semantic prior, node confidence, and metric residual factor를 결합해 edge validity posterior를 계산한다.

Reference but not executable baseline:

- `RelWitness`
  - direct related-work boundary로 cite한다.
  - official code/reproduced result가 없으면 main executable baseline으로 두지 않는다.

### Metrics

Prediction utility:

- `Recall@K`
- `Recall retention`
- Predicate-family recall
- Exact-label denominator coverage

Geometry reliability:

- `Violation@K`
- `RGA-HL@K`
- `RGA-valid@K`
- `RGA-coverage`
- `RGA-disagreement`
- high-semantic invalid rate
- geometry-valid precision among top-K
- rule-violated but high-score count

Calibration:

- AUROC / AUPRC for valid vs invalid
- Brier score
- NLL
- ECE
- per-family calibration curve

Representation analysis:

- semantic/geometry score correlation
- quadrant distribution
- high-semantic/low-geometry failure taxonomy
- source-transfer stability from `VL-SAT` to Open3DSG
- factor contribution analysis: semantic prior vs metric residual vs node confidence

Counterfactual benchmark:

- false-valid rate under wrong-pair
- false-valid rate under shuffled-geometry
- sensitivity to swapped subject/object
- geometry corruption robustness
- semantic-score invariance under geometry break

Uncertainty / abstention:

- abstention coverage
- invalid-edge reduction at fixed recall
- recall loss at fixed violation budget

### Initial Validation Gates

G0. Artifact audit:

- 기존 H001 full-validation `VL-SAT`와 Open3DSG row-level artifacts가 H002 schema로 변환 가능한지 확인한다.
- scan/subgraph/object-pair identity가 유지되는지 확인한다.

G1. Quadrant diagnostic:

- `semantic_score`와 `p_geom_valid`를 같은 row에서 비교한다.
- high-semantic/low-geometry quadrant의 빈도와 대표 failure cases를 집계한다.

G2. RGA metric freeze:

- `RGA-HL@K`, `RGA-valid@K`, `RGA-coverage`, `RGA-disagreement`의 정의를 고정한다.
- geometry-uncertain edge를 invalid로 볼지, 별도 uncertain bucket으로 볼지 policy를 고정한다.
- 이 단계 이후 validation 결과를 보고 RGA bucket/threshold를 바꾸지 않는다.

G3. Factor graph rescoring smoke:

- train/train-dev 기반으로 단순 semantic-geometric factor graph model을 fit한다.
- validation source result는 고정된 protocol로만 평가한다.

G4. Counterfactual consistency:

- wrong-pair, shuffled-geometry, swapped-pair control을 생성한다.
- semantic-only와 H002 factor graph model의 false-valid rate를 비교한다.

G5. Source-transfer:

- `VL-SAT`와 Open3DSG에서 같은 failure pattern과 metric trend가 나오는지 확인한다.

G6. Claim decision:

- H002가 기존 H001 re-ranking보다 원리적 설명력과 robustness를 추가하면 별도 hypothesis로 승격한다.
- 그렇지 않으면 H002는 H001의 analysis/appendix 아이디어로 유지한다.

### Expected Positive Evidence

H002가 H001보다 원리적으로 강하다고 판단할 수 있는 결과:

- high-semantic/low-geometry quadrant가 두 source 모두에서 안정적으로 나타난다.
- `RGA-HL@K`가 기존 `Violation@K`만으로 설명되지 않는 semantic-geometric mismatch를 드러낸다.
- factor graph model이 semantic-only보다 violation과 `RGA-HL@K`를 줄이고, geometry-only보다 recall을 보존한다.
- counterfactual geometry corruption에서 semantic-only는 false-valid를 유지하지만 H002 factor graph posterior는 invalid로 낮춘다.
- `semantic_score`와 `p_geom_valid`의 disagreement가 qualitative failure taxonomy와 일치한다.
- Source-transfer에서 같은 relation-family failure mechanism이 반복된다.

### Expected Negative Evidence

H002를 별도 branch로 유지할 필요가 약해지는 결과:

- `semantic_score`와 `p_geom_valid`가 거의 같은 ranking을 만든다.
- `RGA`가 기존 `Violation@K` 또는 H001 failure rows의 이름 바꾸기에 그친다.
- counterfactual benchmark에서 factor graph model이 기존 H001보다 나아지지 않는다.
- high-semantic/low-geometry failure가 소수 outlier에 그친다.
- relation-family별 rule이 너무 ad hoc해져 representation contribution보다 verifier engineering처럼 보인다.

## H002 TODO

현재 H002의 TODO는 다음 순서로 진행한다. 모두 기존 H001 파일을 수정하지 않고 H002 folder 내부에서 먼저 문서/스모크 수준으로 검증한다.

### Now

- [ ] `RGA` metric contract 작성: `RGA-HL@K`, `RGA-valid@K`, `RGA-coverage`, `RGA-disagreement`, uncertain bucket policy를 정의한다.
- [ ] H001 full-validation artifacts가 H002 edge schema로 projection 가능한지 inventory를 작성한다. 대상 source는 `VL-SAT`와 Open3DSG recovery branch다.
- [ ] H002 schema 초안을 작성한다: `semantic_score`, `geometry_residual`, `p_geom_valid`, `rga_bucket`, `posterior_edge_valid`, `provenance`.

### Next

- [ ] RGA diagnostic smoke plan 작성: existing H001 rows에서 high-semantic/low-geometry bucket을 산출하는 데 필요한 artifact path, columns, denominator를 정리한다.
- [ ] Factor graph variable/factor spec 작성: `phi_sem`, `phi_node`, `phi_geom`, optional `phi_consistency`의 input/output과 unavailable field policy를 고정한다.
- [ ] Baseline comparison matrix 작성: `semantic_only`, `geometry_only`, `H001 probabilistic_recalibrated`, `rule_verified`, `semantic_geometric_factor_graph`.
- [ ] Counterfactual benchmark spec 작성: wrong-pair, shuffled-geometry, swapped subject/object를 최소 세 control로 고정한다.

### Later

- [ ] Docker experiment로 승격할지 결정한다. 승격 전에는 host-only 결과를 paper metric evidence로 쓰지 않는다.
- [ ] RGA diagnostic 결과가 충분하면 `01_overview.md`, `02_method.md`, `03_data_baseline.md` 같은 H002 canonical file 분리를 검토한다.
- [ ] H002가 H001 대비 추가 설명력을 보이면 AAAI 2027 branch로 유지할지, H001 appendix/analysis로 흡수할지 사용자 판단을 받는다.

## 초기 판단

H002는 H001보다 더 원리적인 문제 설정을 가진다. H001이 relation output의 geometry reliability를 평가/보정한다면, H002는 relation confidence가 semantic plausibility와 geometric validity를 conflation한다는 원인을 직접 다룬다.

하지만 H002는 아직 branch-level hypothesis다. 현재 논문 완성도와 metric evidence는 H001이 훨씬 강하다. 따라서 H002는 H001을 대체하기보다 다음 순서로 검증하는 것이 맞다.

1. H001 artifact를 손상하지 않고 H002 schema로 projection한다.
2. high-semantic/low-geometry quadrant가 실제로 충분한 failure mode인지 본다.
3. score decomposition과 counterfactual benchmark가 기존 H001보다 추가 설명력을 주는지 본다.
4. 추가 설명력이 확인되면 H002를 독립 hypothesis 또는 AAAI 2027 branch로 승격한다.
