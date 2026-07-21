# RelCompat3D Paper Outline

Last updated: 2026-07-18 KST

이 문서는 현재 AAAI manuscript의 section 구조와 각 section이 담당할 논리만
소유한다. Method의 상세 설명은 `paper/method.md`, experiment contract는
`paper/experiment.md`, figure 제작 명세는 `paper/figures.md`, reviewer risk는
`paper/risk.md`를 따른다. 과거 title 후보, 역사적 수치, 이전 9-section 구조는
이 문서에 보존하지 않는다.

## 1. Paper Identity

- Title: **Beyond Semantic Confidence: Relation-Consistent Geometric Re-ranking
  for 3D Scene Graphs**
- Method: **RelCompat3D**
- Task: compatibility assessment and re-ranking for fixed 3D Scene Graph
  relation predictions.
- Main scope: proximity and relative-vertical re-ranking; support/contact is
  evaluated but its source order is retained.
- Evaluation: VL-SAT, Open3DSG, and the released `SGFN_full_l160` benchmark
  model from the SceneGraphFusion 3DSSG implementation on a shared 3DSSG target.
- Non-claim: a new relation generator, universal fusion rule, all-relation
  physical validity, or cross-dataset generalization.

## 2. Core Paper Logic

본문 전체는 다음 인과 순서를 유지한다.

```text
Observed failure
→ the predictor score does not directly measure predicate–geometry compatibility for the corresponding ordered pair
→ the predictor score and predicate–geometry compatibility must be separated
→ transformation-consistent compatibility is estimated without the predictor score
→ proximity and vertical relations are re-ranked while support/contact stays in source order
→ exact-match Recall and Violation computed by a rule-based geometry verifier are evaluated jointly
→ family and construct limitations are disclosed
```

Scope/limitation을 Introduction과 Results에서 반복하지 않는다. Introduction은
claim boundary를 한 번 정의하고, 상세 limitation은 Section 5에 둔다.

## 3. Contributions

Introduction의 contribution은 세 개만 사용한다.

1. **Failure formulation.** Exact-match Recall만으로 포착되지 않는 predictor score와
   reconstructed ordered-pair consistency의 mismatch를 identity-preserving
   evaluation과 Recall--Violation contract로 정의한다.
2. **Compatibility.** Predictor score를 compatibility 입력에서 분리하고,
   linked positive--counterfactual ordering과 exact proximity/vertical
   transformation averaging을 결합한다.
3. **Constrained re-ranking and evidence.** Source family sequence와
   support/contact subsequence를 보존하는 prefix-utility-optimal rule을 사용하고,
   하나의 fitted compatibility layer를 세 predictor에 적용해 predictor/family별
   성공 조건과 실패 범위를 분석한다. Prefix optimality는 이 제약 아래의 utility
   성질이며 fusion 또는 Recall--Violation의 전역 최적성을 뜻하지 않는다.

세 predictor의 결과와 qualitative example은 contribution을 별도로 늘리지 않고
세 contribution을 검증하는 evidence로 둔다.

## 4. Six-Section Structure

### 1. Introduction

권장 paragraph flow:

1. 3D Scene Graph relation이 spatial reasoning과 embodied decision에 사용되므로
   실제 object pair와 일치해야 한다.
2. 실제 failure: semantic/category plausibility가 높지만 pair distance, contact,
   vertical order와 어긋나는 relation이 상위에 나타난다.
3. 원인: predictor가 geometry를 사용했는지와 별개로, 최종 relation confidence는
   동일 pair가 predicate를 만족하는지 직접 나타내지 않는다.
4. 설계 필요성: predicate semantics, predicate-independent geometric
   measurements of the ordered pair, predictor score를 분리한 뒤 마지막 ranking에서만
   결합해야 한다.
5. RelCompat3D overview와 relation-family scope.
6. 세 contribution과 한 문단의 result summary.

Introduction에 두지 않을 내용:

- counterfactual threshold.
- optimizer, parameter count, split row count.
- Open3DSG coverage 숫자.
- external stress-test 상세.
- human/LLM annotation chronology.

Figure 1은 Introduction 끝 또는 contribution 직전에 배치한다.

### 2. Related Work

세 묶음으로 구성한다.

1. **3D Scene Graph relation prediction**
   - closed-set, open-vocabulary, online relation predictors.
   - 기존 method도 geometry를 사용한다는 점을 인정한다.
2. **Geometry-aware relation evidence and constraints**
   - edge geometry, semantic-geometric fusion, constraint refinement.
   - RelCompat3D의 차이는 fixed candidate의 predicate--geometry compatibility를
     predictor score와 분리해 평가한다는 점이다.
3. **Reliability, calibration, and structured consistency**
   - confidence rescoring, witness/constraint methods, transformation-aware
     representations.
   - generator 내부 representation 개선과 post-prediction reliability layer를
     구분한다.
   - PUF의 online association/evidence fusion과 fixed relation candidate의
     predicate--geometry compatibility assessment를 구분한다.

Related Work는 “기존 연구가 모두 못한다”는 식으로 쓰지 않는다. 가장 가까운
방법과 task contract, supervision, output 차이를 직접 설명한다.

### 3. Method

#### 3.1 Problem Setup

- relation candidate와 context 정의.
- prediction을 geometry·ground truth와 연결할 때 ordered subject--object
  instance identity를 유지한다.
- T: predicate semantics, G: predicate-independent geometric measurements of
  the ordered pair, Z: predictor score. The family label selects the
  family-specific head, training statistics, transformations, and ranking
  scope; it is not a model input.
- compatibility C는 T와 G만 사용하고 Z는 사용하지 않음.
- C는 physical-validity probability가 아니라 constructed target score.
- reported evaluation scope $\mathcal A_{\rm eval}$은 support/contact,
  proximity, vertical order이며, re-ranking scope $\mathcal A_{\rm rank}$은
  proximity와 vertical order로 제한한다.
- counterfactual construction과 primary verifier가 일부 OBB measurement 및
  threshold를 공유한다는 사실을 명시하고 Violation을 verifier-derived로 한정한다.

#### 3.2 Relation-Consistent Compatibility

- family-specific small linear heads.
- T, G, 그리고 vertical predicate-signed height interaction의 분리.
- GT positives와 linked counterfactual negatives.
- BCE, linked positive–counterfactual ordering loss, L2 regularization.
- train-only standardization/imputation.
- proximity: endpoint swap 후 predicate 유지.
- vertical: endpoint swap과 inverse predicate를 함께 적용.
- original/transformed score averaging으로 exact consistency 보장.
- support/contact에는 blanket transform을 적용하지 않음.

#### 3.3 Family-Aware Re-ranking

- $a\in\mathcal A_{\rm rank}$: Z×C로 family 내부 sort.
- support/contact: source ranking의 family subsequence를 그대로 사용.
- source family sequence를 유지하며 family-specific ordered list에서 선택.
- 고정된 prefix family count와 support/contact subsequence 아래에서 각 re-ranked
  family의 utility 합을 최대화함.
- rank-average/RRF는 Method 마지막에 comparison으로 간단히 정의.

Method의 자세한 교육용 설명과 수식은 `paper/method.md`가 소유한다.

### 4. Experiments

#### 4.1 Experimental Setup

- 1,061 train / 117 development / 157 evaluation split.
- 548 contexts, 3,972 exact-match GT.
- VL-SAT, Open3DSG, and the released `SGFN_full_l160` benchmark model.
- K={5,10,20,50,100}.
- Exact-match Recall, Violation computed by a rule-based geometry verifier, uncertainty variants.
- paired 1,000-resample intervals from a cluster bootstrap over scans at every reported K.
- bounded CPU re-ranking cost and parameter count in the supplement.

Table 1을 result interpretation보다 먼저 보이도록 배치한다.

#### 4.2 Recall–Violation Results

- Table 1의 full K grid를 먼저 해석한다.
- prose는 모든 cell을 반복하지 않고 source별 pattern을 설명한다.
- K=50은 intermediate reported budget이며 selected endpoint로 표현하지
  않는다.
- RelCompat3D-Linear/MLP capacity trade-off와 RankAvg, RRF, Product (all
  families)의 차이를 설명한다.

#### 4.3 Surface-Based Geometry Audit

- Main Results: K=50 strict point--mesh consensus surface-based Violation을
  exact numbers로 요약한다. Surface-based Violation은 primary Violation과
  직접 비교하지 않는다.
- Point/mesh measurements exclude OBB inputs and primary verifier labels.
- Full all-K point, mesh, consensus, coverage, intervals, threshold, and
  intervention results remain in the supplement.
- 동일 reconstructed surface와 ontology를 공유하므로 independent physical
  ground truth라고 부르지 않는다.

#### 4.4 Ablations and Controls

- Main Table 2: Linear/MLP wrong predicate/pair, shuffled geometry,
  fixed-predicate endpoint swap, distance-only, compatibility-only at K=50.
- Supplement: complete K=100 matched-control table and control definitions.
- linked positive–counterfactual ordering과 transformation consistency.
- feature-removal analysis와 threshold sensitivity는 supplement pointer로 둔다.
- Figure 2: all-K trajectory.
- Supplement qualitative figure: proximity correction, vertical correction,
  support/contact residual.
- family-wise result에서 support/contact가 unchanged임을 설명한다.

Experiment의 정확한 계산법과 비교 목적은 `paper/experiment.md`가 소유한다.

### 5. Discussion and Limitations

다음 네 가지를 한 번씩만 쓴다.

1. 세 predictor가 shared 3DSSG/3RScan target을 사용한다.
2. Compatibility target과 primary Violation verifier가 일부 OBB geometry
   primitive를 공유한다. Surface audit가 exact-rule overlap을 줄이지만
   independent physical ground truth는 아니다.
3. Support/contact는 source order를 유지하므로 error가 해결되지 않는다.
4. Matched nonlinear/rank fusion과 source-dependent trade-off가 있어 best
   formula를 주장하지 않는다.

External ReplicaSSG/FROSS 결과는 “target-dependent transfer stress test” 한
문장과 supplement pointer로 충분하다. 실패 수치를 main Discussion에서 반복하지
않는다.

### 6. Conclusion

두 문장 이내의 압축 구조를 유지한다. Predictor score를 compatibility
입력에서 제외했다는 점, 한 shared target의 세 predictor에서 K=10--50
Recall과 Violation point estimate가 함께 개선됐다는 점, support/contact order가 변하지 않는다는
점을 넘어서지 않는다.

Conclusion에 새 claim, 새 숫자, 새 baseline을 추가하지 않는다.

## 5. Figure and Table Placement

| item | 위치 | 역할 |
| --- | --- | --- |
| Figure 1 | Introduction 후반 | failure → factor separation → re-ranking |
| Table 1 | p.5 상단, result prose 전 | 모든 K와 main comparisons |
| Figure 2 | p.6 상단 | source별 K trajectory |
| Table 2 | Results 본문 내 one column | K=50 matched Linear/MLP controls |
| Supplement qualitative | supplement | evidence와 rank outcome 연결 |
| Supplement controls | supplement | complete K=100 controls and definitions |

모든 main table/figure가 Conclusion 전에 나타나야 한다. Table 1은 full width,
Table 2는 single column을 유지한다. Complete K=100 controls는 supplement의
full width로 둔다.

## 6. Main Tables

### Table 1

- percentage point scale.
- K=5/10/20/50/100의 Recall과 Violation을 같은 table에서 paired column으로
  보고.
- rows: Source, RelCompat3D-Linear, RelCompat3D-MLP, RankAvg, RRF, Product (all families).
- pooled compatibility와 hard filter는 supplement/diagnostic.

### Table 2

- percentage point scale.
- K=50 Recall/Violation for Full method, Wrong predicate, Wrong pair, Shuffled
  geometry, Fixed-label swap, Distance only, and Compatibility only.
- Linear/MLP head를 모두 표시하고 세 predictor를 같은 표에서 비교한다.

### Supplemental control tables

- percentage point scale.
- complete K=100 results; K=50 is retained in the main paper.
- columns: Linear and MLP for each predictor.
- rows: Full method, Wrong predicate, Wrong pair, Shuffled geometry,
  Fixed-predicate swap, Distance only, Compatibility only.

## 7. Manuscript-Wide Terminology Contract

Introduction, Related Work, Method, Experiments, captions, supplement에 다음
표기를 동일하게 적용한다.

| 개념 | 표준 표현 |
| --- | --- |
| $Z$ | `predictor score` |
| $G$ | `predicate-independent geometric measurements of the ordered pair` |
| $C$ | `predicate--geometry compatibility` |
| $C^{\rm tr}$ | `transformation-consistent compatibility` |
| $u$ | `within-family ranking score` |
| vertical 변환 | `joint endpoint swap and inverse-predicate transformation` |
| ranking | `family-aware re-ranking` |
| pair 최초 정의 | `ordered subject--object pair` |
| pair 후속 지칭 | `corresponding ordered pair` |
| primary metric | `Recall@$K$`, `Violation@$K$` |
| surface audit metric | `surface-based Violation`; primary `Violation@$K$`와 직접 비교하지 않음 |
| 일반 오류 | 문장 안에서 lowercase `violation` |
| evaluation scope | $\mathcal A_{\rm eval}$: support/contact, proximity, vertical order |
| re-ranking scope | $\mathcal A_{\rm rank}$: proximity/vertical; support/contact는 source subsequence 유지 |

다음 표현은 사용하지 않는다.

- `same-pair geometry`, `same-pair compatibility`.
- `vertical inverse relation`, `predicate inversion`.
- $Z$를 뜻하는 `source score` 또는 `source confidence`.
- `actual geometry`, `actual object pair`, `underlying world state`.
- 범위가 불분명한 `geometry-checkable relations`.
- `test this separation`, `consistent behavior`처럼 대상을 명시하지 않는 표현.
- `contemporaneous`, `sharpen this boundary`처럼 연구 chronology나 reviewer
  대응으로 읽히는 표현.
- H001 방법을 가리키는 `algebra-consistent`; prior work의 고유한
  `relation-algebra constraints`는 정확한 인용 문맥에서만 허용한다.

추가 claim 제한:

- `physical-validity probability`.
- `universal/best rescorer`.
- `dataset-level generalization established`.
- `support/contact solved`.
- `official Open3DSG SOTA`.
- 연구 과정이나 구현 관리에만 쓰이는 이름.

본문 수치 원칙:

- Abstract는 exact performance number 없이 결과 방향을 요약한다.
- Results는 대표 comparison과 interval 해석만 쓴다.
- dense grid는 Table 1--2 및 supplement에 둔다.
