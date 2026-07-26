# RelCompat3D Supplement Guide

Last updated: 2026-07-26 KST

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
  preprocessing, runtime을 구체화한다.
- **설계 검증:** component removals, feature removal, matched Linear/MLP
  controls, transformation checks를 보고한다.
- **통계·construct validity:** scan-level intervals, point- and mesh-based audit,
  uncertainty sensitivity를 보고한다.
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

### 3.1 Notation

Main과 supplement에서 사용하는 candidate, compatibility, transformation,
ranking, metric notation을 한 표에 모은다.

- Reviewer 질문: “\(T,G,Z,C^{\rm tr},u\), pair identity와 relation identity가
  정확히 무엇인가?”
- Main support: Method의 수식과 supplement의 분석을 빠르게 연결한다.
- 우선순위: **P1**

### 3.2 Model and Preprocessing Details

Open3DSG checkpoint와 missing-context 처리, released SGFN model, observed source
relation score range, Linear/MLP training details, parameter count, runtime을
보고한다.

- Reviewer 질문: “세 source relation score를 그대로 곱해도 sign reversal이
  생기지 않는가?”
- Reviewer 질문: “어떤 checkpoint와 preprocessing route를 사용했는가?”
- Reviewer 질문: “Compatibility layer의 추가 비용은 어느 정도인가?”
- 우선순위: score range와 source route는 **P0**, training details는 **P1**,
  runtime은 **P2**

### 3.3 Guarantees and Compatibility Analyses

Transformation consistency, family-sequence preservation, prefix utility,
counterfactual construction, direct component removal, factor use,
feature-removal analysis를 다룬다.

- Reviewer 질문: “Transformation averaging이 실제로 무엇을 보장하는가?”
- Reviewer 질문: “Pairwise loss와 averaging이 없어도 같은 결과 아닌가?”
- Reviewer 질문: “Verifier와 같은 scalar를 학습한 결과를 다시 verifier로 평가한
  것은 아닌가?”
- 우선순위: construction과 feature removal은 **P0**, direct removal은 main
  pointer 때문에 **P0**, proofs는 **P1**

### 3.4 Point- and Mesh-Based Consistency Audit

OBB inputs와 primary verifier labels를 사용하지 않는 point- and mesh-based
measurements로 동일 rankings를 다시 평가한다. Point, mesh, agreement-based labels,
coverage, paired intervals, synthetic intervention monotonicity를 보고한다.

- Reviewer 질문: “Primary Violation 감소가 shared OBB rules를 학습한 결과일
  뿐인가?”
- Main support: Abstract, Introduction, Results, Discussion의 alternative audit
  claim을 직접 뒷받침한다.
- 우선순위: **P0**

### 3.5 Qualitative Pair Analysis

Proximity correction, vertical-order correction, support/contact scope
boundary를 ordered-pair projection과 measured evidence로 보여준다. Main Results가
언급하는 `desk close by chair` promotion case도 prose로 기록한다.

- Reviewer 질문: “실제 candidate가 왜 이동했으며, 바꾸지 않는 family는 무엇인가?”
- Main support: aggregate 수치가 어떤 pair-level outcome을 만드는지 보여준다.
- 우선순위: **P1**

### 3.6 Counterfactual-Policy Sensitivity

Proximity threshold, vertical margin, negative cap, pairwise-loss weight를
한 번에 하나씩 바꾸고 train-only refit 결과를 비교한다.

- Reviewer 질문: “한 threshold 또는 negative count에 과도하게 맞춘 결과인가?”
- Main support: reported trend가 작은 construction 변화에 안정적임을 보여준다.
- 우선순위: **P1**

### 3.7 Estimator, Fusion, and Open3DSG Sensitivities

Linear/MLP와 RankAvg/RRF, matched controls, pooled compatibility, Open3DSG
coverage route를 비교한다.

- Reviewer 질문: “결과가 Linear form 하나에만 의존하는가?”
- Reviewer 질문: “Family-specific fitting이 필요한가?”
- Reviewer 질문: “Open3DSG의 15 missing contexts가 결과를 만들었는가?”
- 우선순위: matched controls와 coverage는 **P0**, pooled fitting은 **P1**,
  main Table 1과 중복되는 compact estimator/fusion table은 **P2**

### 3.8 Scan-Level Cluster Bootstrap

157 scans를 cluster 단위로 1,000회 resample한 paired intervals를 Linear와 MLP에
대해 모든 reported \(K\) values에서 제시한다.

- Reviewer 질문: “Point-estimate 변화가 scan variation 아래에서도 유지되는가?”
- Main support: Results의 interval 해석을 직접 검증한다.
- 우선순위: **P0**

### 3.9 External Transfer Stress Test

3DSSG-trained Linear estimator를 ReplicaSSG/FROSS에 unchanged 적용한다. 일부
\(K\)에서는 joint improvement가 나타나지만 \(K=100\)에서는 score quantization과
candidate ceiling 때문에 변화가 거의 없다.

- 장점: single-dataset criticism에 제한적인 추가 evidence를 제공한다.
- 위험: target이 완전히 untouched가 아니고, support/contact mapping이 없으며,
  \(K=100\)에서 saturation이 나타난다.
- Main paper는 dataset-level generalization을 주장하지 않으며 현재 이 결과를 직접
  참조하지 않는다.
- 우선순위: **P2**
- 권장: single-dataset scope를 보완하는 유일한 evidence라는 가치는 있다. 다만
  별도 generalization claim을 추가하지 않고 반드시 `stress test`로만 부른다.
  Page pressure가 크거나 previously observed target에 대한 공격 가능성을 최소화해야
  한다면 P0/P1 evidence를 보존한 뒤 제외를 검토한다.

### 3.10 Family Composition within the Selected Top-100 Predictions

Support/contact, proximity, vertical order의 global top-100 slice 안에서
Linear-minus-Source Recall/Violation 변화를 보고한다.

- Reviewer 질문: “Aggregate improvement가 relation-family composition
  변화로 만들어진 것인가?”
- Main support: support/contact가 정확히 unchanged이고, vertical order가 감소의
  큰 부분을 담당함을 보인다.
- 우선순위: **P0**

### 3.11 Verifier-Uncertainty Sensitivity

Primary \(V_{\rm all}\), decidable-only \(V_{\rm dec}\), uncertainty rate,
uncertain-as-violation \(V_{u\to v}\)를 비교한다.

- Reviewer 질문: “Uncertain candidates를 denominator에 넣어 Violation을
  인위적으로 낮춘 것인가?”
- Main support: denominator convention을 바꿔도 Linear의 Violation 감소 방향이
  유지됨을 보인다.
- 우선순위: **P0**

## 4. 현재 Table 목록과 의미

아래 번호는 현재 LaTeX source 순서에 따른 intended supplementary numbering이다.
Float placement에 따라 PDF의 실제 위치는 달라질 수 있다.

| Table | Label | 무엇을 보여주는가 | Main claim과의 관계 | 우선순위 |
| --- | --- | --- | --- | --- |
| **S1** | `tab:notation` | Candidate, identity, compatibility, transformation, ranking, metric notation의 정의 | Method를 자기완결적으로 읽게 함 | P1 |
| **S2** | `tab:source-score-ranges` | Re-ranked families의 candidate 수와 source relation score minimum/maximum. 모든 score가 non-negative임 | \(u=ZC^{\rm tr}\)에서 sign reversal이 없음을 검증 | **P0** |
| **S3** | `tab:counterfactual-rules` | Family별 negative intervention, acceptance threshold, primary verifier와 공유하는 primitive/threshold | Training target 재현성과 construct-dependence boundary를 동시에 공개 | **P0** |
| **S4** | `tab:runtime` | Linear CPU re-ranking time, contexts, scored candidates | Method overhead가 작음을 보이지만 end-to-end latency는 아님 | P2 |
| **S5** | `tab:family-discrimination` | Family별 train/dev rows, parameter count, linked pairs, AUROC, Brier | Constructed target을 학습할 수 있음을 확인 | P3 |
| **S6** | `tab:component-removals` | Full Linear, no pairwise loss, no transformation averaging의 R/V | Pairwise loss는 regularizer이고 averaging은 aggregate gain보다 exact consistency guarantee를 제공함 | **P0** |
| **S7** | `tab:primitive-holdout` | Exact verifier scalar, related measurement family를 제거하거나 alternative evidence만 사용해 refit | Primary result가 단일 verifier scalar 복사만으로 생기지 않았음을 보임 | **P0** |
| **S8** | `tab:surface-audit-full` | Point, mesh, agreement-based Violation을 Source/Linear/MLP와 모든 \(K\)에서 비교 | Alternative geometric measurements에서도 방향이 유지됨 | **P0** |
| **S9** | `tab:surface-audit-ci` | Linear-minus-Source point/mesh/agreement \(\Delta V\)와 paired 95% intervals | Main Table 3의 Linear audit를 all-\(K\)로 확장 | **P0** |
| **S10** | `tab:surface-audit-ci-mlp` | MLP-minus-Source point/mesh/agreement \(\Delta V\)와 paired 95% intervals | MLP도 alternative audit에서 같은 방향임을 확인 | **P0** |
| **S11** | `tab:counterfactual-sensitivity` | Nine one-factor train-only refits의 linked ordering과 R/V | Threshold, negative cap, pair weight 민감도 방어 | P1 |
| **S12** | `tab:nonlinear-comparison` | Linear, MLP, RankAvg, RRF의 \(K=50,100\) R/V | 두 estimator와 fusion trade-off를 요약하지만 main Table 1과 중복 | P2 |
| **S13** | `tab:ablations-k50` | Linear/MLP full matched structural controls at \(K=50\) | Main Table 2가 생략한 complete MLP controls 제공 | **P0** |
| **S14** | `tab:ablations-k100` | 같은 controls at \(K=100\) | Control direction이 다른 cutoff에서도 유지됨 | **P0** |
| **S15** | `tab:pooled-ablation` | Family-specific product와 pooled all-family product 비교 | Family conditioning과 support/contact scope의 필요성 설명 | P1 |
| **S16** | `tab:open3dsg-routes` | Eligible 533, conservative full-target 548, recovered 548 route의 R/V | Missing contexts와 denominator 선택이 conclusion을 만들지 않았음을 보임 | **P0** |
| **S17** | `tab:scan-cluster` | Linear-minus-Source \(\Delta\)Recall/\(\Delta\)Violation와 scan-level intervals | Main Results의 Linear statistical statement 근거 | **P0** |
| **S18** | `tab:scan-cluster-mlp` | MLP-minus-Source의 같은 intervals | Main Results의 MLP statistical statement 근거 | **P0** |
| **S19** | `tab:replica-transfer` | ReplicaSSG/FROSS에서 all-\(K\) Source/Linear R/V | Single-dataset scope를 일부 보완하지만 saturation과 mapping caveat가 큼 | P2 |
| **S20** | `tab:family-slices` | Top-100 안에서 family별 Linear-minus-Source 변화 | Aggregate gain과 family composition을 분리하고 support/contact preservation 확인 | **P0** |
| **S21** | `tab:uncertainty-sensitivity` | \(V_{\rm all},V_{\rm dec},U,V_{u\to v}\) 비교 | Uncertain denominator에 의한 인위적 improvement 공격 방어 | **P0** |

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
   - S16 Open3DSG coverage sensitivity
   - Linear/MLP optimization details
2. **Matched method evidence**
   - S13--S14 complete Linear/MLP controls
   - S6 direct component removals
   - S7 feature removal
3. **Alternative geometric audit**
   - S8--S10 full point- and mesh-based results and intervals
   - Coverage and synthetic intervention test
4. **Statistical and metric robustness**
   - S17--S18 scan-level intervals
   - S21 uncertainty sensitivity
   - S20 family composition
5. **Qualitative and hyperparameter support**
   - Figure S1 and promotion prose
   - S11 counterfactual-policy sensitivity
   - S15 pooled family comparison
6. **Optional tail**
   - S4 runtime
   - S5 training/development discrimination
   - S12 compact estimator/fusion duplication
   - S19 external transfer stress test

## 7. 반드시 유지할 내용

최종 supplement에서 다음 항목은 삭제하면 main paper의 pointer 또는 claim 근거가
약해진다.

1. **Counterfactual construction and training details**
   - S3와 exact split/optimizer/example-count 설명.
2. **Complete controls for both estimators**
   - S13과 S14.
3. **Direct component removals**
   - S6. Pairwise loss의 효과가 작더라도 main paper가 component removal을
     직접 가리키므로 유지해야 한다.
4. **Feature-removal analysis**
   - S7. Primary verifier와 shared primitives에 대한 핵심 방어다.
5. **Full point- and mesh-based audit**
   - S8--S10, coverage, intervention monotonicity.
6. **Paired scan-level intervals**
   - S17--S18. Main Results의 statistical wording을 뒷받침한다.
7. **Family and uncertainty analyses**
   - S20--S21. Aggregate change와 uncertain-denominator 공격을 방어한다.
8. **Open3DSG denominator/coverage route**
   - S16과 source preprocessing prose.
9. **Observed source relation score ranges**
   - S2. Raw score product의 sign behavior를 결정한다.
10. **Qualitative promotion prose**
    - Main Results가 supplement의 promotion case를 명시적으로 가리킨다.

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

S5의 매우 높은 AUROC는 constructed target을 잘 학습했다는 sanity check다.
Physical validity나 independent evidence가 아니며, reviewer가 circularity로
오해할 수 있다.

- 권장: parameter/row counts는 model details에 유지한다.
- AUROC/Brier table은 페이지 압박이 있으면 prose 한 문장으로 축약한다.
- 유지할 경우 caption의 `not human physical-validity judgments` 경계를 보존한다.

### 8.3 Compact estimator/fusion comparison — P2

S12는 main Table 1의 \(K=50,100\) 일부를 다시 보여준다. Complete controls와
all-\(K\) main table이 이미 있으므로 독립 정보량이 작다.

- 권장: RankAvg/RRF 공식은 유지한다.
- 표는 페이지 압박 시 삭제하거나 main Table 1 pointer로 대체한다.
- Source-specific exact-match MLP upper comparator prose는 main comparison과
  혼동될 수 있으므로 필요한 artifact가 없다면 축약한다.

### 8.4 Runtime — P2

S4는 efficiency 질문에는 유용하지만 end-to-end latency가 아니며 main contribution도
아니다. 페이지 압박이 있으면 parameter count와 ms/context 범위만 prose로 남길 수
있다.

### 8.5 Direct component removals는 낮추지 않음

S6은 pairwise-loss removal과 no-averaging의 aggregate 차이가 작아 보일 수 있다.
그러나 이를 빼는 것은 권장하지 않는다.

- Pairwise term은 dominant performance source가 아니라 training regularizer라고
  정확히 해석한다.
- Transformation averaging의 기여는 aggregate gain보다 exact endpoint/predicate
  consistency guarantee다.
- 이 구분은 오히려 method claim을 원리적으로 더 정확하게 만든다.

## 9. 최종 권장안

현재 11-page supplement를 유지할 수 있다면 P0와 P1은 보존하는 것이 가장 안전하다.
분량을 줄여야 한다면 다음 순서로 축소한다.

1. S5 training/development discrimination을 prose로 축약.
2. S12 estimator/fusion duplicate table 삭제하고 공식과 main pointer만 유지.
3. S4 runtime table을 prose로 축약.
4. S19 External Transfer Stress Test를 유지할지 single-dataset defense와
   previously observed target caveat를 비교해 결정.
5. S15 pooled comparison을 compact prose 또는 artifact pointer로 축약.

P0 evidence를 줄여 supplement 길이를 맞추는 것은 권장하지 않는다. 특히
point- and mesh-based audit, matched MLP controls, scan-level intervals,
feature removal, uncertainty sensitivity는 본문을 보충하고 reviewer의 핵심 공격을
직접 방어하는 자료다.
