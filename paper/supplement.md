# RelCompat3D Supplement Guide

Last updated: 2026-07-27 KST

이 문서는 현재 AAAI supplement
[`aaai/sec/supplement.tex`](aaai/sec/supplement.tex)의 내용을 reviewer-facing
역할에 따라 정리한다. Experiment artifact의 authoritative owner를 대신하지 않으며,
supplement에 무엇을 유지하고 무엇을 축소할지 판단하는 문서다.

## 1. Supplement의 역할

Main paper가 직접 주장하는 내용은 다음과 같다.

1. RelCompat3D는 source relation score와 predicate--geometry compatibility를
   분리한다.
2. Ordered-pair identity와 applicable endpoint/predicate transformations가
   compatibility estimation에 필요하다.
3. RelCompat3D-Linear와 RelCompat3D-MLP는 세 predictor의 reported \(K\) values에서
   Source보다 낮지 않은 Recall point estimates와 높지 않은 Violation point
   estimates를 보인다.
4. Primary verifier와 compatibility inputs의 일부 OBB-derived measurements가
   겹치지만, point- and mesh-based alternative measurements에서도 변화 방향이
   유지된다.
5. Family-aware re-ranking은 proximity와 vertical-order candidates만 바꾸고
   support/contact candidates는 source order로 유지한다.

Supplement는 위 claim을 다음 네 방향에서 방어한다.

- **재현성:** notation, score range, counterfactual construction, model,
  preprocessing, runtime, row-level paper regeneration을 구체화한다.
- **설계 검증:** component removals, feature removal, matched Linear/MLP
  controls, transformation checks, simple baseline, routing-constraint
  controls를 보고한다.
- **통계·construct validity:** scan-level intervals, point- and mesh-based audit,
  uncertainty sensitivity, source-score mapping sensitivity,
  construct-dependence matrix를 보고한다.
- **scope discipline:** Open3DSG coverage, family composition, qualitative
  boundary, external-transfer 범위를 구분한다.

## 2. 우선순위 기준

| 등급 | 의미 | 유지 원칙 |
| --- | --- | --- |
| **P0 — 반드시 유지** | Main text가 직접 가리키거나 central claim의 타당성을 결정 | 삭제하지 않는다. 분량을 줄이더라도 표 또는 정확한 수치 근거를 유지한다. |
| **P1 — 강한 support** | Reviewer의 핵심 반론을 직접 방어하지만 main claim이 이것 하나에 의존하지는 않음 | 가능한 한 유지한다. P0 뒤에 배치한다. |
| **P2 — 선택적 보강** | 재현성 또는 추가 해석에는 유용하지만 main과 일부 중복 | 페이지 압박이 있으면 prose 축약 또는 artifact pointer로 대체할 수 있다. |
| **P3 — 낮은 우선순위** | Main claim에 필수적이지 않고 새로운 caveat나 공격 지점을 더 많이 만듦 | 제출본에서 제외하거나 마지막에 짧게 두는 것을 우선 검토한다. |

낮은 우선순위는 불리한 결과를 숨긴다는 의미가 아니다. Central design claim의
해석에 직접 필요한 negative result는 유지해야 한다. 반대로 main scope 밖의
exploratory result는 새로운 claim을 만들지 않는다면 굳이 제출본에 포함할 필요가
없다.

## 3. 현재 Section 구성

Supplement는 main paper의 `Method → Experiments` 전개를 그대로 따른다.
추가 결과를 독립적인 top-level section으로 나열하지 않고, 해당 claim을 소유하는
subsection 아래에 둔다.

### 3.1 Supplementary Method Details

#### 3.1.1 Notation

Candidate identity, compatibility, transformation, ranking, metric notation을
한 표에 모은다. 우선순위는 **P1**이다.

#### 3.1.2 Model and Preprocessing Details

Open3DSG/SGFN source route, observed source relation score ranges, missing-context
처리를 기록한다. Score ranges와 source route는 **P0**이다.

#### 3.1.3 Compatibility Estimation and Family-Aware Re-Ranking

Transformation consistency, family-sequence preservation, prefix utility,
counterfactual construction, construct-dependence matrix, estimator inputs와
optimization details를 기록한다. Counterfactual rules와 dependency matrix는
**P0**, proofs와 optimizer details는 **P1**이다.

### 3.2 Supplementary Experiments

#### 3.2.1 Experimental Setup

Runtime, development diagnostics, row-level paper regeneration을 보고한다.
Runtime은 **P2**, exact training counts와 parameterization은 **P1**이다.
291 canonical cells를 검사하는 one-command regeneration은 **P1**이다.

#### 3.2.2 Results

- **Component and Feature-Removal Analyses:** pairwise-loss와 transformation
  averaging removal, held-out linked-pair margin, transformed-view top-\(K\)
  consistency, verifier scalar/primitive removals. **P0**
- **Training-Seed Robustness:** 사전 고정 5회 fit의 predictor별 all-\(K\)
  mean/standard deviation과 Source 방향 점검. **P1**
- **Point- and Mesh-Based Consistency Audit:** OBB-free alternative
  measurements, coverage, paired intervals, mechanism check. **P0**
- **Qualitative Pair Analysis:** proximity/vertical-order demotion과
  support/contact scope boundary. **P1**
- **Counterfactual-Policy Sensitivity:** thresholds, negative cap,
  pairwise-loss weight의 train-only refits. **P1**
- **Estimator, Fusion, and Routing Sensitivities:** source-score mappings,
  Positive-density, direct-verifier diagnostics, Linear/MLP and RankAvg/RRF,
  structural controls, pooled fitting, matched routing controls, Open3DSG
  coverage. Score mapping, simple baseline, structural and routing controls,
  coverage는 **P0**이다.
- **Candidate-Pool Oracle Recall:** fixed-pool exact-label coverage와
  active-route, family-slot, unconstrained upper bounds. Missing-candidate
  ceiling과 remaining ranking headroom을 분리한다. **P1**
- **Paired Scan-Level Intervals:** 157 scans의 1,000 paired resamples. **P0**
- **External Transfer Stress Test:** ReplicaSSG/FROSS의 scoped stress test.
  **P2**
- **Family Composition:** selected top-100의 family-specific changes. **P0**
- **Verifier-Uncertainty Sensitivity:** primary, decidable-only,
  uncertain-as-violation definitions의 방향 비교. **P0**

## 4. 현재 Table 목록과 의미

아래 번호는 현재 LaTeX source 순서 기준이다. 실제 PDF float 위치가 달라도
`label`이 authoritative identifier다.

| Table | Label | 무엇을 보여주는가 | Main claim과의 관계 | 우선순위 |
| --- | --- | --- | --- | --- |
| **S1** | `tab:notation` | Candidate, identity, compatibility, transformation, ranking, metric notation | Method를 자기완결적으로 읽게 함 | P1 |
| **S2** | `tab:source-score-ranges` | Source relation score 범위와 non-negative 여부 | Product sign reversal 가능성을 배제 | **P0** |
| **S3** | `tab:counterfactual-rules` | Family별 counterfactual intervention과 acceptance rule | Training target 재현성과 verifier overlap 공개 | **P0** |
| **S4** | `tab:construct-dependence` | Construction, verifier, point/mesh audit의 information access | Construct-dependence boundary를 명시 | **P0** |
| **S5** | `tab:runtime` | Linear CPU re-ranking cost | 추가 비용 설명. End-to-end latency는 아님 | P2 |
| **S6** | `tab:family-discrimination` | Family별 rows, parameters, AUROC, Brier | Constructed target learnability diagnostic | P3 |
| **S7** | `tab:component-removals` | Linear/MLP Full, no pairwise, no averaging aggregate results | Component의 aggregate 범위를 숨기지 않음 | **P0** |
| **S8** | `tab:pairwise-diagnostics` | Held-out linked-pair win rate와 margin distribution | Pairwise regularizer의 estimator-dependent 직접 효과 | **P0** |
| **S9** | `tab:transformation-diagnostics` | Transformation error mean/P95/max와 top-\(K\) consistency | Averaging의 exact guarantee를 직접 검증 | **P0** |
| **S10** | `tab:seed-robustness` | 5회 fit의 all-\(K\) R/V mean과 SD | MLP initialization 의존성과 Linear repeatability를 분리 | P1 |
| **S11** | `tab:primitive-holdout` | Exact scalar, related primitives, alternative evidence removals | Single-scalar copying 설명을 반박 | **P0** |
| **S12** | `tab:surface-audit-full` | Point, mesh, agreement-based all-\(K\) Violation | Alternative geometric measure의 방향 확인 | **P0** |
| **S13** | `tab:surface-audit-ci` | Linear audit changes와 paired intervals | Main Table 3을 all-\(K\)로 확장 | **P0** |
| **S14** | `tab:surface-audit-ci-mlp` | MLP audit changes와 paired intervals | 두 estimator에서 방향 확인 | **P0** |
| **S15** | `tab:counterfactual-sensitivity` | Train-only counterfactual-policy refits | Threshold와 pair-weight sensitivity 방어 | P1 |
| **S16** | `tab:score-mapping-sensitivity` | Frozen source-score mappings의 favorable counts와 worst changes | Product score의 bounded scale sensitivity 검증 | **P0** |
| **S17** | `tab:simple-baseline` | Source, Positive-density, Linear, MLP all-\(K\) 비교 | Closest simple continuous baseline 방어 | **P0** |
| **S18** | `tab:direct-verifier-diagnostics` | Hard-tail/drop의 R/V, uncertainty, selected count | Label-consuming diagnostic을 baseline과 분리 | **P0** |
| **S19** | `tab:nonlinear-comparison` | Linear, MLP, RankAvg, RRF at \(K=50,100\) | Estimator/fusion trade-off 요약 | P2 |
| **S20** | `tab:ablations-k50` | 두 estimator의 matched controls at \(K=50\) | Main Table 2가 생략한 MLP controls | **P0** |
| **S21** | `tab:ablations-k100` | 같은 controls at \(K=100\) | Control direction의 cutoff robustness | **P0** |
| **S22** | `tab:pooled-ablation` | Family-specific와 pooled all-family product | Family conditioning과 scope 해석 | P1 |
| **S23** | `tab:routing-constraint` | Family slots와 P/V global all-\(K\) 비교 | Family-aware route의 direct matched ablation | **P0** |
| **S24** | `tab:routing-relaxations` | Support-order only와 all-families scope relaxations | Matched route test와 broader scope 분리 | **P0** |
| **S25** | `tab:open3dsg-routes` | Eligible, conservative, recovered Open3DSG routes | Missing contexts sensitivity | **P0** |
| **S26** | `tab:candidate-oracle` | Pool coverage와 three fixed-candidate Recall upper bounds | Missing-candidate ceiling과 ranking headroom 정량화 | P1 |
| **S27** | `tab:scan-cluster` | Linear scan-level paired intervals | Main Linear statistical statement 근거 | **P0** |
| **S28** | `tab:scan-cluster-mlp` | MLP scan-level paired intervals | Main MLP statistical statement 근거 | **P0** |
| **S29** | `tab:replica-transfer` | ReplicaSSG/FROSS stress test | Scoped transfer evidence | P2 |
| **S30** | `tab:family-slices` | Selected top-100 family-specific changes | Aggregate와 family composition 분리 | **P0** |
| **S31** | `tab:uncertainty-sensitivity` | Primary, decidable-only, uncertainty-aware variants | Denominator convention 공격 방어 | **P0** |

## 5. 현재 Figure 목록과 의미

### Supplementary Figure S1 — Pair--Evidence--Outcome Analysis

Asset:
[`aaai/supplement_figures/qualitative_geometry_panels.png`](aaai/supplement_figures/qualitative_geometry_panels.png)

LaTeX label: `fig:supp-qualitative`

| Panel | Relation | Measured evidence | Rank outcome | 전달하는 의미 |
| --- | --- | --- | --- | --- |
| (a) Proximity | `heater close by trash can` | XY center distance 4.33 m | 19 \(\rightarrow\) 178 | Large separation과 맞지 않는 proximity candidate를 demote |
| (b) Vertical order | `floor higher than curtain` | subject--object center \(\Delta z=-1.02\) m | 1 \(\rightarrow\) 430 | Inverted vertical order candidate를 demote |
| (c) Support/contact | `door lying on floor` | vertical bottom--top gap \(-0.06\) m, contact unresolved | 21 \(\rightarrow\) 21 | Evidence가 부족한 support/contact candidate를 수정했다고 주장하지 않고 source order 유지 |

이 Figure의 핵심은 성공 사례를 세 개 나열하는 것이 아니다. 두 geometry-checkable
families에서는 measured evidence와 rank outcome이 연결되고, support/contact에서는
method scope가 명시적으로 멈춘다는 점을 한 그림에서 보여준다.

- Main Figure 1의 vertical demotion과 Figure 2의 proximity demotion을 더 구체적인
  pair evidence로 보완한다.
- Main Results가 언급하는 `desk close by chair` 81 \(\rightarrow\) 30 promotion은
  이 Figure의 panel이 아니라 supplement prose에 기록되어 있다.
- 우선순위: **P1**
- 약점 노출: panel (c)는 unresolved family를 보여주지만 이미 main Method와
  Discussion에서 support/contact source-order scope를 선언했으므로 새로운 약점이
  아니다. 오히려 scope discipline을 시각적으로 확인한다.
- 향후 redraw 시 `Contact residual`보다 `Support/contact scope boundary`가 main
  terminology와 더 정확히 맞는다.

## 6. 권장 유지·배치 순서

Reviewer가 main claim의 근거를 빠르게 찾도록 다음 순서를 권장한다.

1. **Notation and reproducibility**
   - S1 notation
   - Open3DSG/SGFN route
   - S2 score ranges
   - S3 counterfactual construction
   - S4 construct-dependence matrix
   - S25 Open3DSG coverage sensitivity
   - Linear/MLP optimization details
   - Row-level regeneration check
2. **Matched method evidence**
   - S16 score-mapping sensitivity
   - S17 closest simple baseline와 S18 direct-verifier diagnostics
   - S20--S21 complete Linear/MLP controls
   - S23--S24 routing controls
   - S26 candidate-pool oracle
   - S7 direct component removals
   - S11 feature removal
3. **Alternative geometric audit**
   - S12--S14 full point- and mesh-based results and intervals
   - Coverage and synthetic intervention test
4. **Statistical and metric robustness**
   - S27--S28 scan-level intervals
   - S31 uncertainty sensitivity
   - S30 family composition
5. **Qualitative and hyperparameter support**
   - Figure S1 and promotion prose
   - S15 counterfactual-policy sensitivity
   - S22 pooled family comparison
6. **Optional tail**
   - S5 runtime
   - S6 training/development discrimination
   - S19 compact estimator/fusion duplication
   - S29 external transfer stress test

## 7. 반드시 유지할 내용

최종 supplement에서 다음 항목은 삭제하면 main paper의 pointer 또는 claim 근거가
약해진다.

1. **Counterfactual construction and training details**
   - S3--S4와 exact split/optimizer/example-count 설명.
2. **Complete controls for both estimators**
   - S20과 S21.
3. **Direct component removals**
   - S7. Pairwise loss의 효과가 작더라도 main paper가 component removal을
     직접 가리키므로 유지해야 한다.
4. **Feature-removal analysis**
   - S11. Primary verifier와 shared primitives에 대한 핵심 방어다.
5. **Full point- and mesh-based audit**
   - S12--S14, coverage, intervention monotonicity.
6. **Paired scan-level intervals**
   - S27--S28. Main Results의 statistical wording을 뒷받침한다.
7. **Family and uncertainty analyses**
   - S30--S31. Aggregate change와 uncertain-denominator 공격을 방어한다.
8. **Open3DSG denominator/coverage route**
   - S25와 source preprocessing prose.
9. **Observed source relation score ranges**
   - S2. Raw score product의 sign behavior를 결정한다.
10. **Score mapping, simple baseline, and routing controls**
    - S16--S18와 S23--S24. Product scale, closest-simple-baseline,
      family-slot necessity에 대한 P0 방어다.
11. **Qualitative promotion prose**
    - Main Results가 supplement의 promotion case를 명시적으로 가리킨다.
12. **Row-level regeneration check**
    - Tables 1--3와 Figure 3 data의 one-command numeric reproduction을
      검증한다.
13. **Candidate-pool oracle**
    - S26. Fixed-candidate ceiling과 remaining route headroom을 정량화한다.

## 8. 낮은 우선순위 또는 축소 후보

### 8.1 External Transfer Stress Test — P2

Single-dataset scope를 일부 보완하므로 단순한 약점 표는 아니다. 다만 일부
\(K\)에서 favorable transfer를 보이는 동시에 다음 caveat를 추가로 연다.

- target이 완전히 untouched가 아니다.
- exact ontology mapping이 proximity와 vertical-order 일부에 한정된다.
- support/contact가 제외된다.
- \(K=100\)에서 source relation score quantization으로 re-ranking이 거의
  작동하지 않는다.
- candidate support가 Recall ceiling을 만든다.

Main paper가 dataset-level generalization을 주장하거나 이 결과를 가리키지 않으므로
central claim의 필수 evidence는 아니다. 유지하면 `stress test`라는 범위를 고정한다.
제외한다면 single-dataset defense 하나가 줄어드는 trade-off를 감수해야 한다.

### 8.2 Training/development discrimination — P3

S6의 매우 높은 AUROC는 constructed target을 잘 학습했다는 sanity check다.
Physical validity나 independent evidence가 아니며, reviewer가 circularity로
오해할 수 있다.

- 권장: parameter/row counts는 model details에 유지한다.
- AUROC/Brier table은 페이지 압박이 있으면 prose 한 문장으로 축약한다.
- 유지할 경우 caption의 `not human physical-validity judgments` 경계를 보존한다.

### 8.3 Compact estimator/fusion comparison — P2

S16은 main Table 1의 \(K=50,100\) 일부를 다시 보여준다. Complete controls와
all-\(K\) main table이 이미 있으므로 독립 정보량이 작다.

- 권장: RankAvg/RRF 공식은 유지한다.
- 표는 페이지 압박 시 삭제하거나 main Table 1 pointer로 대체한다.
- Source-specific exact-match MLP upper comparator prose는 main comparison과
  혼동될 수 있으므로 필요한 artifact가 없다면 축약한다.

### 8.4 Runtime — P2

S5는 efficiency 질문에는 유용하지만 end-to-end latency가 아니며 main contribution도
아니다. 페이지 압박이 있으면 parameter count와 ms/context 범위만 prose로 남길 수
있다.

### 8.5 Matched component diagnostics는 낮추지 않음

S7--S9는 pairwise-loss removal과 no-averaging의 aggregate 차이가 작다는 사실과
각 component의 직접 diagnostic을 함께 보여준다. 이를 빼는 것은 권장하지 않는다.

- Pairwise term은 dominant performance source가 아니라 training regularizer라고
  정확히 해석한다. Linear direct diagnostic은 개선되지만 MLP margin 결과는
  mixed라는 범위를 유지한다.
- Transformation averaging의 기여는 aggregate gain보다 exact endpoint/predicate
  consistency guarantee이며, no-averaging의 transformed-view membership
  변화가 이를 직접 뒷받침한다.
- 이 구분은 오히려 method claim을 원리적으로 더 정확하게 만든다.

S10의 5-seed 결과는 MLP의 fitting variation을 공개한다. 30 estimator--predictor--
\(K\) cells 중 Linear 15개는 모두 exact repeat이고, MLP는 15개 중 14개에서
모든 seed가 Source 대비 두 방향을 유지한다. VL-SAT \(K=50\) 한 seed는 Recall
한 relation을 잃으면서 Violation을 낮추므로, seed-uniform Pareto claim은 하지
않는다.

## 9. 최종 권장안

현재 19-page supplement를 유지할 수 있다면 P0와 P1은 보존하는 것이 가장 안전하다.
분량을 줄여야 한다면 다음 순서로 축소한다.

1. S6 training/development discrimination을 prose로 축약.
2. S19 estimator/fusion duplicate table 삭제하고 공식과 main pointer만 유지.
3. S5 runtime table을 prose로 축약.
4. S28 External Transfer Stress Test를 유지할지 single-dataset defense와
   previously observed target caveat를 비교해 결정.
5. S22 pooled comparison을 compact prose 또는 artifact pointer로 축약.

P0 evidence를 줄여 supplement 길이를 맞추는 것은 권장하지 않는다. 특히
point- and mesh-based audit, matched MLP controls, scan-level intervals,
feature removal, uncertainty sensitivity는 본문을 보충하고 reviewer의 핵심 공격을
직접 방어하는 자료다.
