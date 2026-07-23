# RelCompat3D Experiment Guide

Last updated: 2026-07-21 KST

이 문서는 현재 논문의 experiment가 **무엇을, 어떤 predictor와 dataset에서,
어떤 조건과 metric으로 검증하는지** 설명한다. 실행 명령, Docker image, model hash,
row-level artifact는 `docs/reproducibility.md`와
`experiments/RelCompat3D_geom_reliability/README.md`가 소유한다.

## 1. Evaluation task

RelCompat3D experiment는 새로운 3D scene graph generator의 성능을 측정하지 않는다.
세 relation predictor가 이미 만든 fixed candidates를 입력으로 받아, 같은 candidate
universe 안에서 ranking만 바꾼다.

각 candidate에는 다음 정보가 있다.

\[
r_i=(\mathrm{scan}_i,\mathrm{context}_i,s_i,o_i,p_i,a_i,Z_i).
\]

- \(s_i,o_i\): ordered subject/object instance.
- \(p_i\): predicted predicate.
- \(a_i\): relation family.
- \(Z_i\): predictor가 제공한 native relation-ranking score.
- \(G_i\): 같은 ordered pair에서 계산한 geometric measurements.

실험의 목표는 \(T_i=p_i\)와 \(G_i\)로 학습한 compatibility가 Source ranking의
geometric inconsistency를 낮추면서 exact-label relations를 보존하는지 확인하는
것이다.

## 2. 실험이 답하려는 질문

### Q1. 높은 predictor score에 ordered-pair inconsistency가 남아 있는가?

Source top-\(K\)의 verifier-derived Violation을 측정한다. Predictor가 geometry를
사용했더라도 native score가 같은 ordered pair의 predicate--geometry compatibility를
직접 나타내는 것은 아닌지 확인한다.

### Q2. Compatibility re-ranking이 Violation만 낮추고 Recall을 잃는가?

Source와 RelCompat3D를 동일 candidate, context, \(K\), ground-truth denominator에서
비교한다. Recall과 Violation은 항상 함께 보고한다.

### Q3. 효과가 하나의 linear formula에만 의존하는가?

같은 factor separation, training targets, transformation averaging, product score,
family-aware ranking을 사용하는 RelCompat3D-Linear와 RelCompat3D-MLP를 비교한다.
두 variant의 차이는 compatibility estimator의 parameterization이다.

### Q4. Product fusion이 일반적인 rank fusion보다 적합한가?

동일한 family-aware ranking을 사용하는 RankAvg와 RRF를 비교한다. 어느 하나가 모든
predictor와 \(K\)에서 우월하다고 가정하지 않고, Recall--Violation operating point의
차이를 본다.

### Q5. Predicate, ordered-pair identity, geometry, transformation이 실제로 필요한가?

Wrong predicate, Wrong pair, Shuffled geometry, Fixed-predicate swap,
Distance only, Compatibility only control을 비교한다.

### Q6. Support/contact까지 같은 compatibility로 다시 정렬해야 하는가?

Primary method와 Product (all families)를 비교하고 family-wise metrics를 확인한다.
Primary method는 support/contact candidates를 source order로 유지한다.

### Q7. Primary verifier와 겹치는 OBB measurement가 결과를 만든 것인가?

Feature-removal analyses와 point- and mesh-based audit을 사용한다. Alternative audit은
OBB inputs와 primary verifier labels를 사용하지 않지만, 같은 reconstructed geometry와
ontology를 사용하므로 independent physical-validity ground truth로 해석하지 않는다.

## 3. Data splits and information boundary

| split | scans | 사용 목적 |
| --- | ---: | --- |
| training | 1,061 | target construction, normalization, imputation, model fitting |
| internal development | 117 | model form, transformations, applicable family scope 결정 |
| final evaluation | 157 | main Recall/Violation, paired intervals, audit evaluation |

모든 compatibility training example은 training split에서 만든다. Final evaluation의
rows, predictor scores, verifier-status labels는 training target이나 model fitting에
사용하지 않는다. Final-evaluation ground truth는 Recall을 계산할 때만 사용하며
candidate filtering이나 ranking에는 사용하지 않는다.

Counterfactual construction과 primary verifier는 일부 OBB-derived measurements와
일부 thresholds를 공유한다. 이 partial construct dependence는 숨기지 않고,
point/mesh audit과 feature-removal analyses로 별도 점검한다.

## 4. Main evaluation target

### Shared 3DSSG/3RScan target

| 항목 | 설정 |
| --- | --- |
| final-evaluation scans | 157 |
| relation contexts | 548 |
| exact-match ground-truth denominator | 3,972 |
| reported \(K\) | \(\{5,10,20,50,100\}\) |
| main relation families | support/contact, proximity, vertical order |

각 context는 독립적인 top-\(K\) ranking 단위다. Candidate가 \(K\)개보다 적으면
synthetic candidate를 추가하지 않는다.

Open3DSG는 public predictions를 사용하며, candidate list가 없는 official context도
evaluation target에 남겨 empty selection으로 처리한다. Candidate coverage와
alternative preprocessing sensitivity는 supplement에서 보고한다.

### Relation predictors

| predictor | paper에서의 역할 | native score |
| --- | --- | --- |
| Open3DSG | open-vocabulary relation predictor | normalized text-embedding cosine similarity |
| VL-SAT | closed-set 3D relation predictor | sigmoid relation score |
| SGFN | released `SGFN_full_l160` SceneGraphFusion benchmark model | sigmoid relation score |

Predictor별 score normalization이나 target-specific refitting은 수행하지 않는다.
각 predictor는 독립적으로 ranking되며 서로 다른 predictor의 \(Z_i\)를 직접 비교하지
않는다.

세 predictor가 geometry, ontology, evaluation target을 공유하므로 main experiment는
**shared data에서의 cross-predictor behavior**를 평가한다. Cross-dataset
generalization test가 아니다.

## 5. Evaluation scope and re-ranking scope

보고하는 evaluation family는 다음과 같다.

\[
\mathcal A_{\mathrm{eval}}
=\{\mathrm{support/contact},\mathrm{proximity},\mathrm{vertical\ order}\}.
\]

실제로 compatibility로 순서를 바꾸는 family는 더 좁다.

\[
\mathcal A_{\mathrm{rank}}
=\{\mathrm{proximity},\mathrm{vertical\ order}\}.
\]

- proximity/vertical-order: \(Z_iC_i^{\mathrm{tr},q}\)로 family 내부를 정렬한다.
- support/contact: Source ranking의 family subsequence를 그대로 유지한다.
- source ranking의 relation-family label sequence는 모든 top-\(K\) prefix에서
  유지한다.

따라서 aggregate change가 family composition을 바꾸어 얻어진 것인지와 실제
within-family selection 변화인지 구분할 수 있다.

## 6. Compatibility training setup

RelCompat3D-Linear와 RelCompat3D-MLP는 다음 요소를 공유한다.

- training rows와 constructed positive/counterfactual targets.
- linked positive--counterfactual ordering objective.
- binary cross-entropy와 soft margin-ranking loss.
- transformation-consistent augmentation과 inference-time averaging.
- predictor score, rank, identity, object class를 compatibility input에서 제외.
- proximity/vertical product score와 family-aware ranking procedure.

두 estimator의 차이:

| variant | compatibility estimator |
| --- | --- |
| RelCompat3D-Linear | family-specific linear heads; constant family input 없음 |
| RelCompat3D-MLP | shared width-2 ReLU estimator; family indicator 포함 |

공통 loss 설정:

- pairwise margin: 1.
- pairwise-loss weight: 0.25.
- non-bias \(L_2\) coefficient: \(10^{-4}\).
- normalization과 missing-value imputation: training split statistics만 사용.

Linear와 MLP 모두 Source predictor별 hyperparameter search나 final-evaluation
refitting을 하지 않는다.

## 7. Main comparison conditions

### Table 1 conditions

| ranking rule | 정의 | 확인하는 질문 |
| --- | --- | --- |
| Source | native predictor score \(Z\) 순서 | 원래 ranking의 기준점 |
| RelCompat3D-Linear | Linear compatibility와 \(Z\)의 within-family product | factor-separated linear instantiation |
| RelCompat3D-MLP | MLP compatibility와 \(Z\)의 within-family product | 효과가 linear form에만 의존하는가 |
| RankAvg | source rank와 Linear compatibility rank의 평균 | score scale을 버리는 rank fusion의 trade-off |
| RRF | reciprocal rank fusion | 일반 rank fusion의 trade-off |
| Product (all families) | Linear compatibility를 support/contact까지 적용 | primary family scope가 필요한가 |

RankAvg와 RRF는 Linear compatibility를 사용하고 같은 family-aware ranking을
적용한다. RelCompat3D-MLP는 fusion baseline이 아니라 second proposed compatibility
instantiation이다.

Pooled compatibility, hard filtering, exact-label nonlinear rescorer는 mechanism 또는
upper-comparison analysis로 supplement에 둔다. Main claim은 이 조건들보다 보편적으로
우월하다는 주장이 아니다.

## 8. Ablations and controls

Main ablation table은 RelCompat3D-Linear의 full method와 다음 controls를
\(K\in\{50,100\}\)에서 보고하고, 같은 표에 RelCompat3D-MLP full-method row를 둔다.
MLP에 동일하게 적용한 complete controls는 supplement에서 보고한다.

| condition | 바꾸는 요소 | 검증 질문 |
| --- | --- | --- |
| Wrong predicate | 같은 pair의 geometry에 wrong/inverse predicate 적용 | predicate meaning을 사용하는가 |
| Wrong pair | 다른 ordered pair의 geometry 연결 | candidate identity가 필요한가 |
| Shuffled geometry | candidate 사이에서 geometry를 섞음 | marginal geometry distribution만으로 충분한가 |
| Fixed-predicate swap | endpoints를 바꾸고 predicate는 고정 | endpoint와 inverse predicate를 함께 바꿔야 하는가 |
| Distance only | compatibility를 pair distance 하나로 대체 | method가 단일 distance ordering인가 |
| Compatibility only | \(Z_i\)를 제거 | geometry compatibility가 semantic relevance를 대체하는가 |

Wrong predicate와 Fixed-predicate swap은 다른 개입이지만 vertical candidates에서
signed predicate--geometry interpretation을 모두 뒤집을 수 있다. 비슷한 aggregate
결과를 독립된 두 근거로 과대해석하지 않는다.

## 9. Candidate identity and top-\(K\) selection

- ordered-pair identity:
  \((\mathrm{scan},\mathrm{context},s,o)\).
- exact relation-candidate identity:
  \((\mathrm{scan},\mathrm{context},s,p,o)\).

Recall은 exact relation-candidate identity를 사용한다. Relation family는 re-ranking
scope를 정할 때만 사용하며 label matching에는 사용하지 않는다.

각 context에서:

1. Source는 \(Z_i\)로 candidate를 정렬한다.
2. Source의 family-label sequence를 기록한다.
3. proximity와 vertical lists는 condition-specific score로 다시 정렬한다.
4. support/contact list는 Source subsequence를 그대로 사용한다.
5. 원래 family positions를 각 family list에서 차례로 채운다.
6. 완성된 ranking의 top-\(K\)를 평가한다.

Re-ranked family의 ties는 exact candidate identity로 deterministic하게 해결한다.
Support/contact에는 별도 tie re-ordering을 적용하지 않는다.

## 10. Metrics

### Exact-match Recall@K

Context \(c\)의 selected top-\(K\) candidates를 \(L_K(c)\), exact ground-truth
relations를 \(Y_c\)라 하면

\[
\mathrm{Recall@K}
=\frac{\sum_c |L_K(c)\cap Y_c|}
{\sum_c |Y_c|}.
\]

Subject instance, predicate, object instance가 모두 같아야 numerator에 들어간다.
Main denominator는 모든 predictor와 ranking rule에서 3,972로 고정한다.

### Verifier-derived Violation@K

Selected candidates 중 rule-based geometry verifier가 satisfied, uncertain,
violated 중 하나를 반환한 집합을 \(D_K\)라 하고, counts를 \(N_s,N_u,N_v\)라 하면

\[
\mathrm{Violation@K}
=\frac{N_v}{N_s+N_u+N_v}.
\]

Uncertain rows는 denominator에는 들어가지만 numerator에는 들어가지 않는다.
Violation은 physical-validity ground truth가 아니라 verifier-derived measure다.

### Coverage and uncertainty sensitivity

Supplement는 다음을 함께 보고한다.

\[
\mathrm{UncertaintyRate}=\frac{N_u}{N_s+N_u+N_v},
\]

\[
\mathrm{DecidableViolation}=\frac{N_v}{N_s+N_v},
\qquad
\mathrm{DecidableCoverage}=\frac{N_s+N_v}{N_s+N_u+N_v}.
\]

또한 uncertain을 모두 violation으로 세는 pessimistic variant를 사용한다. 이 분석은
main Violation 감소가 uncertain denominator만으로 만들어졌는지 확인한다.

## 11. Statistical reporting

Main paired intervals는 scan 단위 resampling을 사용한다.

1. 157 scan IDs를 replacement와 함께 1,000번 resample한다.
2. 선택된 scan의 모든 contexts를 함께 가져온다.
3. 모든 ranking rule에 동일한 resample indices를 적용한다.
4. 각 replicate에서 method-minus-Source \(\Delta R\)과 \(\Delta V\)를 계산한다.
5. 2.5/97.5 percentiles를 paired 95% interval로 보고한다.

Point estimate가 더 좋아도 interval이 zero를 포함하면 statistical improvement라고
쓰지 않는다. K=50은 reported curve의 intermediate reference이지 별도로
pre-registered된 endpoint가 아니다.

## 12. Point- and mesh-based consistency audit

Primary compatibility input과 verifier가 일부 OBB-derived measurements를 공유하므로,
proximity와 vertical-order candidates를 reconstructed instance geometry의 두 다른
representation으로 다시 측정한다.

- point-based estimate: robust point-cloud vertex distance와 height.
- mesh-based estimate: area-weighted triangle samples의 distance와 height.
- thresholds와 uncertainty margins: training-split positive relations에서만 고정.
- OBB inputs, predictor identity, \(Z_i\), learned compatibility, primary verifier
  labels는 사용하지 않는다.

Satisfied/violated label은 point와 mesh estimate가 같은 label을 낼 때만 결정하고,
둘이 다르면 uncertain으로 둔다. Main Table 3은 \(K=50\)에서
RelCompat3D-Linear와 Source를 비교하고, paired change와 measured/decidable coverage를
보고한다. MLP와 모든 \(K\)의 point/mesh/agreement 결과는 supplement에 둔다.

이 audit은 ranking을 바꾸지 않으므로 Recall은 Table 1과 같다. Primary Violation과
다른 construct이므로 절대값을 직접 비교하지 않는다.

## 13. Main evidence map

| paper element | 무엇을 검증하는가 |
| --- | --- |
| Table 1 | 세 predictor와 다섯 \(K\)에서 Source, 두 proposed variants, matched fusion, all-family comparison |
| Figure 3 | Table 1의 Source/Linear/MLP Recall--Violation trajectory |
| Main ablation table | Linear controls at \(K=50/100\), MLP full operating point |
| Point/mesh table | alternative geometric measure at \(K=50\) for Linear |
| Supplement | MLP controls, all-\(K\) audits, uncertainty, family analysis, threshold/feature sensitivity |

Figure 1과 Figure 2의 rank changes는 source-backed qualitative examples지만 aggregate
effect의 근거는 Table 1과 Figure 3다.

## 14. External transfer stress test

ReplicaSSG/FROSS result는 target-specific refitting 없이 적용한 supplementary
stress test다. Ontology, geometry, candidate support, score scale 변화에 대한 failure
mechanism을 확인하지만 dataset-level generalization claim의 근거로 사용하지 않는다.

## 15. Claim boundary

이 experiment가 지지하는 표현:

> On one shared 3DSSG validation target, both RelCompat3D variants produce Recall
> point estimates no lower and verifier-derived Violation point estimates no
> higher than Source across the reported predictor--\(K\) settings, with
> predictor- and family-dependent operating points.

피해야 하는 표현:

- 모든 Recall improvement가 statistically significant하다.
- Violation이 independent physical-validity ground truth다.
- RelCompat3D가 support/contact를 해결한다.
- Linear 또는 MLP가 보편적으로 더 우수하다.
- product score가 optimal fusion formula다.
- 세 predictor 결과가 dataset-level generalization을 증명한다.
- Open3DSG 결과가 broad 3D scene graph SOTA를 의미한다.
