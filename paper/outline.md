# RelCompat3D Paper Outline

Last updated: 2026-07-22 KST

이 문서는 현재 AAAI manuscript의 section 논리, contribution 배치, main
figure/table 역할만 소유한다. Method의 상세 정의는 `paper/method.md`, 실험
계약은 `paper/experiment.md`, 시각화 명세는 `paper/figures.md`, reviewer
판단과 위험 대응은 각각 `paper/review.md`와 `paper/risk.md`가 소유한다.

## 1. Paper Identity

- Selected title: **RelCompat3D: Predicate–Geometry Compatibility for Re-Ranking
  3D Scene Graph Relations**
- Source status: synchronize the consolidated TeX title during the pending
  layout and release-regeneration pass.
- Method: **RelCompat3D**
- Selected main PDF: `paper/aaai/main_teaser_aaai27.pdf`
- Task: fixed 3D scene graph relation predictions에 대한
  predicate--geometry compatibility assessment와 family-aware re-ranking.
- Main scope: proximity와 vertical-order candidates를 re-rank하고,
  support/contact candidates는 source order로 유지한다.
- Evaluation: VL-SAT, Open3DSG, and the released SceneGraphFusion benchmark
  model (SGFN) on one shared 3DSSG/3RScan target.
- Non-claim: a new relation generator, universal fusion rule, calibrated
  physical-validity probability, all-family correction, or established
  cross-dataset generalization.

선택된 canonical teaser PDF는 9 pages이고 technical content는 page 7에서
끝난다. 병합된 최신 source의 smoke build는 현재 10 pages이며 4.43-pt
overfull row가 남아 있다. 사용자의 결정에 따라 이 layout debt는 다음
release regeneration 단계에서 해결하고, 지금은 scientific transcript와 문서
구조를 변경하지 않는다.

## 2. Core Paper Logic

본문은 다음 인과 관계를 유지한다.

```text
High-scoring relation failure on a reconstructed ordered pair
→ the source relation score is not an explicit estimate of predicate–geometry compatibility
→ predicate semantics and ordered-pair measurements are separated from the source relation score
→ linear and nonlinear compatibility estimators learn from linked counterfactuals
→ transformation averaging enforces the applicable endpoint/predicate consistency
→ compatibility and the source relation score are combined only for within-family ranking
→ exact-match Recall and verifier-derived Violation are evaluated together
→ matched controls and an alternative point- and mesh-based audit delimit the claim
```

Introduction은 이 원인과 설계 필요성을 설명하고, Method는 구현 계약을,
Experiments는 falsifiable evidence를, Discussion은 claim boundary를 각각 한 번만
담당한다.

## 3. Contributions

Introduction의 contribution은 세 개로 유지한다.

1. **Failure and evaluation formulation.** Exact-match Recall만으로 포착되지
   않는 source relation score와 instance-level geometric compatibility의
   mismatch를 ordered-pair identity를 보존한 Recall@$K$--Violation@$K$
   평가로 정의한다.
2. **Factor-separated compatibility estimation.** Source relation score와 predictor identity를
   compatibility input에서 제외하고, linked positive--counterfactual training과
   applicable endpoint/predicate transformation averaging을 결합한다. Linear와
   MLP는 이 framework의 두 estimator이며 transformation averaging 자체만을
   독립 novelty로 주장하지 않는다.
3. **Family-aware re-ranking and evidence.** Source family-label sequence와
   support/contact subsequence를 보존하면서 proximity/vertical-order candidates를
   re-rank하고, 세 predictor·matched controls·alternative geometric audit로
   predictor- and family-dependent behavior를 분석한다.

세 predictor의 수치, qualitative case, point- and mesh-based audit는 위 contribution을
검증하는 evidence이며 별도 contribution으로 늘리지 않는다.

## 4. Manuscript Structure

Source는 Abstract와 여섯 top-level section으로 정리되어 있다.

| order | source | role |
| --- | --- | --- |
| Abstract | `paper/aaai/sec/0_abstract.tex` | problem, method, evaluation, scoped result |
| 1 | `paper/aaai/sec/1_introduction.tex` | failure → cause → design → contributions |
| 2 | `paper/aaai/sec/2_related_work.tex` | closest task and novelty boundaries |
| 3 | `paper/aaai/sec/3_method.tex` | formulation, estimators, transformations, ranking |
| 4 | `paper/aaai/sec/4_experiments.tex` | setup, metrics, results, controls, audit |
| 5 | `paper/aaai/sec/5_discussion_limitations.tex` | claim and evidence limits |
| 6 | `paper/aaai/sec/6_conclusion.tex` | scoped takeaway |

Active supplement는 `paper/aaai/sec/supplement.tex`, submission에서 제외한
relative-size extension은 `paper/aaai/sec/old.tex`가 소유한다.

### Abstract

- 문제: high source relation score와 reconstructed ordered-pair geometry의 mismatch.
- 방법: ordered-pair identity를 유지하고 source relation score 없이
  compatibility를 추정한 뒤 re-ranking에서만 결합.
- mechanism: Linear/MLP estimators, linked counterfactuals, transformation
  averaging, family-aware scope.
- 평가: exact-match Recall@$K$와 verifier-derived Violation@$K$ on three
  predictors and one shared target.
- 결과: 모든 공개 predictor--$K$ setting에서 Source보다 나쁘지 않은 point
  estimate pattern. Statistical superiority나 physical validity로 확대하지 않는다.

### 1. Introduction

권장 paragraph flow:

1. 3D scene graph relation이 downstream spatial reasoning에 사용되므로 해당
   ordered pair를 설명해야 한다.
2. measured geometry와 충돌하는 high-scoring predicate failure를 정의한다.
3. 기존 predictor도 geometry를 쓰지만 final score가 same-pair compatibility를
   직접 나타내지는 않는다는 gap을 설명한다.
4. $T/G/Z$ factor separation과 두 compatibility estimator를 소개한다.
5. compatibility가 re-ranking에서만 $Z$와 결합되고 family sequence와
   support/contact order가 보존됨을 설명한다.
6. predictors, metrics, contributions, result direction을 요약한다.

Counterfactual threshold, optimizer, parameter count, coverage 세부 수치는
Introduction에 두지 않는다.

### 2. Related Work

세 subsection을 유지한다.

1. **3D Scene Graph Prediction:** generator와 post-prediction reliability
   assessment의 차이.
2. **Geometry-Aware Relation Evidence:** geometry/constraint를 사용하는 prior
   work와 fixed-candidate, source-score-excluded compatibility의 차이.
3. **Reliability Evaluation and Calibration:** confidence calibration,
   uncertainty, selective prediction과 predicate--geometry compatibility의 차이.

각 문단은 관련 연구를 나열한 뒤 RelCompat3D와의 공통점과 차이점을 명시한다.
선행연구가 geometry를 사용하지 않는다고 주장하지 않는다.

### 3. Method

#### 3.1 Problem Setup

- candidate tuple, native source relation score, context 정의.
- ordered-pair identity와 exact relation-candidate identity 구분.
- $T$: predicate semantics; $G$: predicate-independent ordered-pair
  measurements; $a$: estimator/transformation/ranking family selector;
  $Z$: source relation score.
- Linear에서 $a$는 head와 training statistics를 선택하지만 constant input으로
  반복되지 않는다. Shared MLP는 family indicator를 입력으로 사용한다.
- evaluation scope는 support/contact, proximity, vertical order이며,
  re-ranking scope는 proximity와 vertical order다.
- compatibility는 constructed-target ranking score이지 physical-validity
  posterior가 아니다.

#### 3.2 Compatibility Estimation

- OBB-derived distance, height, overlap, gap measurements; point contact는
  primary compatibility input이 아니다.
- family-specific Linear heads와 compact shared MLP.
- train-only standardization/imputation.
- positive, negative counterfactual, relation-preserving augmentation을 구분.
- BCE + linked positive--counterfactual softplus ranking term + L2.
- proximity endpoint symmetry와 vertical joint endpoint-swap/inverse-predicate
  consistency를 transformation averaging으로 보장.
- formal proof와 full construction rules는 supplement.

#### 3.3 Family-Aware Re-Ranking

- proximity/vertical-order: $u_i=Z_iC_i^{\rm tr}$.
- support/contact: source-ranking family subsequence를 그대로 사용.
- source position의 family label에 맞는 ordered list에서 다음 candidate를
  선택해 source family sequence를 보존.
- Product score는 posterior나 universal optimum이 아니며 fitted fusion
  parameter를 추가하지 않는 within-family ranking score다.
- RankAvg/RRF/Product (all families)는 같은 candidate universe에서 비교한다.

### 4. Experiments

#### 4.1 Experimental Setup

- 1,061 train / 117 development / 157 evaluation scans.
- 548 contexts and 3,972 exact-match GT relations.
- VL-SAT, Open3DSG, released SGFN model.
- $K\in\{5,10,20,50,100\}$.
- exact-match Recall@$K$ and verifier-derived Violation@$K$.
- uncertain rows는 primary Violation denominator에는 들어가지만 numerator에는
  들어가지 않음.
- paired scan-level bootstrap intervals; secondary uncertainty/coverage results는
  supplement.

#### 4.2 Recall--Violation Results

- Table 1과 Figure 3을 함께 해석한다.
- 모든 15 predictor--$K$ cells에서 두 variants의 point estimates가 Source보다
  나쁘지 않지만, interval claim은 predictor와 $K$별로 제한한다.
- Open3DSG가 가장 큰 change를 보인다.
- Linear와 MLP는 서로 다른 Recall--Violation operating points이며 어느
  estimator도 보편적으로 우월하다고 쓰지 않는다.
- RankAvg/RRF/Product (all families)의 trade-off와 scope 차이를 설명한다.

#### 4.3 Ablations and Controls

- Main Table 2: K=50 matched controls for Linear and MLP.
- wrong predicate, wrong pair, shuffled geometry, fixed-predicate swap,
  distance-only, compatibility-only.
- complete K=100 controls, feature removal, transformation and linked-pair
  checks는 supplement.

#### 4.4 Point- and Mesh-Based Consistency Audit

- Main Table 3은 Linear의 K=50 alternative Violation을 보고한다.
- satisfied/violated label은 point and mesh measurements가 일치할 때만
  부여하고 disagreement는 uncertain으로 둔다.
- primary Violation과 직접 비교하지 않는다.
- MLP와 all-$K$ results, separate point- and mesh-based results, coverage,
  thresholds, interventions는
  supplement.
- independent physical-validity ground truth라고 부르지 않는다.

### 5. Discussion and Limitations

다음 boundary만 한 번씩 설명한다.

1. 세 predictor는 one shared 3DSSG target을 사용한다.
2. Compatibility target과 primary verifier는 일부 OBB-derived measurements를
   공유하며 alternative audit도 same reconstructed geometry/ontology를 사용한다.
3. Support/contact는 평가하지만 re-rank하지 않는다.
4. Formula/head별 trade-off가 존재하므로 universal superiority를 주장하지 않는다.

External ReplicaSSG/FROSS는 supplement stress test로만 다루고 main claim을
cross-dataset generalization으로 넓히지 않는다.

### 6. Conclusion

두 문장 이내로 factor separation, relation-preserving transformation,
shared-target three-predictor point-estimate pattern을 요약한다. 새로운 claim,
baseline, future-work 목록을 추가하지 않는다.

## 5. Selected Main Layout

`main_teaser_aaai27.pdf`의 canonical placement는 다음과 같다.

| item | page | role |
| --- | ---: | --- |
| Abstract / Introduction start | 1 | problem and method motivation |
| Figure 1 | 2 | `desk higher than ceiling`, rank 6 → 425 demotion |
| Figure 2 | 3 | pair geometry → compatibility → within-family score → re-ranking |
| Table 1 | 6 | all-$K$ main comparison |
| Table 2 | 7, left | K=50 matched controls for Linear/MLP |
| Table 3 | 7, right | K=50 point- and mesh-based agreement audit for Linear |
| Figure 3 | 7 | Source/Linear/MLP Recall--Violation trajectories |
| Discussion / Conclusion | 6--7 | scope and takeaway |
| References | 7--9 | references only after technical content |

Figure 1은 outcome/motivation, Figure 2는 mechanism, Figure 3은 aggregate
trajectory를 담당하므로 역할을 합치지 않는다. Three-case qualitative grid와
complete controls는 supplement에 둔다.

## 6. Main Table Contracts

### Table 1

- Rows: Source, RelCompat3D-Linear, RelCompat3D-MLP, RankAvg, RRF, Product
  (all families), grouped by predictor.
- Columns: paired Recall/Violation at K=5/10/20/50/100.
- All values are percentages.
- Product (all families)는 support/contact scope가 다른 comparison임을 caption과
  본문에서 명시한다.

### Table 2

- K=50 matched controls on the shared target.
- Cells report Recall / Violation by predictor, condition, and head.
- Distance-only의 `Both`는 shared control임을 caption에서 정의한다.
- K=100 results는 supplement.

### Table 3

- K=50 alternative Violation from point- and mesh-based agreement.
- `Linear` denotes RelCompat3D-Linear.
- $\Delta V$ is Linear minus Source in percentage points.
- Coverage is measured/decidable coverage.
- Values are not directly comparable to primary Violation in Table 1.

## 7. Terminology and Claim Contract

| concept | canonical expression |
| --- | --- |
| $Z$ | `source relation score` |
| $G$ | `predicate-independent measurements of the ordered pair` |
| $C$ | `predicate--geometry compatibility` |
| $C^{\rm tr}$ | `transformation-consistent compatibility` |
| $u$ | `within-family ranking score` |
| vertical transformation | `joint endpoint swap and inverse-predicate transformation` |
| ranking | `family-aware re-ranking` |
| primary metrics | `exact-match Recall@$K$`, `verifier-derived Violation@$K$` |
| audit | `point- and mesh-based consistency audit` or `alternative geometric measure` |
| support/contact | `candidates retain source order` |

Blocked claims:

- independent or human-validated physical correctness.
- calibrated probability of validity.
- universal/best re-ranking formula.
- support/contact improvement.
- cross-dataset generalization established.
- 3D scene graph generation SOTA.
