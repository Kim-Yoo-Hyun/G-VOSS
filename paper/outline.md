# RelCompat3D Paper Outline

Last updated: 2026-07-17 KST

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
- Evaluation: VL-SAT, Open3DSG, and SceneGraphFusion on a shared 3DSSG target.
- Non-claim: a new relation generator, universal fusion rule, all-relation
  physical validity, or cross-dataset generalization.

## 2. Core Paper Logic

본문 전체는 다음 인과 순서를 유지한다.

```text
Observed failure
→ the source relation score does not directly measure predicate–geometry compatibility for the corresponding ordered pair
→ the source relation score and predicate–geometry compatibility must be separated
→ transformation-consistent compatibility is estimated without the source relation score
→ proximity and vertical relations are re-ranked while support/contact stays in source order
→ Recall and verifier-derived Violation are evaluated jointly
→ family and construct limitations are disclosed
```

Scope/limitation을 Introduction과 Results에서 반복하지 않는다. Introduction은
claim boundary를 한 번 정의하고, 상세 limitation은 Section 5에 둔다.

## 3. Contributions

Introduction의 contribution은 세 개만 사용한다.

1. **Failure formulation.** Exact-label Recall만으로 포착되지 않는 relation-score와
   reconstructed pair-geometry consistency의 mismatch를 identity-preserving
   evaluation과 Recall--Violation contract로 정의한다.
2. **Compatibility.** Source relation score를 compatibility 입력에서 분리하고,
   linked positive--counterfactual ordering과 exact proximity/vertical
   transformation averaging을 결합한다.
3. **Constrained re-ranking and evidence.** Source family sequence와
   support/contact subsequence를 보존하는 prefix-utility-optimal rule을 사용하고,
   하나의 fitted compatibility layer를 세 predictor에 적용해 predictor/family별
   성공 조건과 실패 범위를 분석한다. Prefix optimality는 이 제약 아래의 utility
   성질이며 fusion 또는 Recall--Violation의 전역 최적성을 뜻하지 않는다.

Cross-predictor 결과와 qualitative example은 contribution을 별도로 늘리지 않고
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
4. 설계 필요성: predicate semantics, predicate-independent pair-geometry
   measurements, source relation score를 분리한 뒤 마지막 ranking에서만
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
     source relation score와 분리해 평가한다는 점이다.
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
- T: predicate semantics, G: predicate-independent pair-geometry measurements,
  Z: source relation score.
- compatibility C는 T와 G만 사용하고 Z는 사용하지 않음.
- C는 physical-validity probability가 아니라 constructed target score.

#### 3.2 Relation-Consistent Compatibility

- family-specific small linear heads.
- T, G, T×G feature separation.
- GT positives와 linked counterfactual negatives.
- BCE, linked-pair ordering loss, L2 regularization.
- train-only standardization/imputation.
- proximity: endpoint swap 후 predicate 유지.
- vertical: endpoint swap과 inverse predicate를 함께 적용.
- original/transformed score averaging으로 exact consistency 보장.
- support/contact에는 blanket transform을 적용하지 않음.

#### 3.3 Family-Aware Re-ranking

- proximity/vertical: Z×C로 family 내부 sort.
- support/contact: source order.
- source family sequence를 유지하며 family-specific ordered list에서 선택.
- 고정된 prefix family count와 support/contact subsequence 아래에서
  proximity/vertical utility 합을 최대화함.
- rank-average/RRF는 Method 마지막에 comparison으로 간단히 정의.

Method의 자세한 교육용 설명과 수식은 `paper/method.md`가 소유한다.

### 4. Experiments

#### 4.1 Experimental Setup

- 1,061 train / 117 development / 157 evaluation split.
- 548 contexts, 3,972 exact-label GT.
- VL-SAT, Open3DSG, SceneGraphFusion.
- K={5,10,20,50,100}.
- Recall, verifier-derived Violation, uncertainty variants.
- paired 1,000-resample scan-cluster intervals at every reported K.
- bounded CPU re-ranking cost and parameter count in the supplement.

Table 1을 result interpretation보다 먼저 보이도록 배치한다.

#### 4.2 Recall–Violation Results

- Table 1의 full K grid를 먼저 해석한다.
- prose는 모든 cell을 반복하지 않고 source별 pattern을 설명한다.
- K=50은 intermediate reported budget이며 selected endpoint로 표현하지
  않는다.
- matched MLP, RankAvg, RRF, Product (all families)의 trade-off를 설명한다.

#### 4.3 Ablations and Controls

- Table 2: wrong predicate/pair, shuffled geometry, label-fixed swap,
  distance-only, compatibility-only.
- linked-pair ordering과 transformation consistency.
- feature-removal analysis와 threshold sensitivity는 supplement pointer로 둔다.

#### 4.4 Qualitative and Family Analysis

- Figure 2: all-K trajectory.
- Figure 3: proximity correction, vertical correction, support/contact residual.
- family-wise result에서 support/contact가 unchanged임을 설명한다.

Experiment의 정확한 계산법과 비교 목적은 `paper/experiment.md`가 소유한다.

### 5. Discussion and Limitations

다음 네 가지를 한 번씩만 쓴다.

1. 세 predictor가 shared 3DSSG/3RScan target을 사용한다.
2. Compatibility target과 Violation verifier가 일부 geometry primitive를
   공유하므로 independent construct validation이 아니다.
3. Support/contact는 source order를 유지하므로 error가 해결되지 않는다.
4. Matched nonlinear/rank fusion과 source-dependent trade-off가 있어 best
   formula를 주장하지 않는다.

External ReplicaSSG/FROSS 결과는 “target-dependent transfer stress test” 한
문장과 supplement pointer로 충분하다. 실패 수치를 main Discussion에서 반복하지
않는다.

### 6. Conclusion

두 문장 구조를 유지한다.

1. Source relation score와 predicate--geometry compatibility를 분리했다.
2. Transformation consistency와 family-aware re-ranking을 통해 세 predictor의 shared
   target에서 Recall--Violation behavior를 개선/분석했다.

Conclusion에 새 claim, 새 숫자, 새 baseline을 추가하지 않는다.

## 5. Figure and Table Placement

| item | 위치 | 역할 |
| --- | --- | --- |
| Figure 1 | Introduction 후반 | failure → factor separation → re-ranking |
| Table 1 | p.5 상단, result prose 전 | 모든 K와 main comparisons |
| Figure 2 | p.6 상단 | source별 K trajectory |
| Table 2 | p.6 Figure 2 아래 | falsification/information controls |
| Figure 3 | p.7 상단 | evidence와 rank outcome 연결 |

모든 main table/figure가 Conclusion 전에 나타나야 한다. Table 1은 full width,
Table 2는 single column을 유지한다.

## 6. Main Tables

### Table 1

- percentage point scale.
- K=5/10/20/50/100의 Recall과 Violation을 같은 table에서 paired column으로
  보고.
- rows: Source, RelCompat3D, Matched MLP, RankAvg, RRF, Product (all families).
- pooled compatibility와 hard filter는 supplement/diagnostic.

### Table 2

- percentage point scale.
- K=50/100.
- rows: RelCompat3D, Wrong predicate, Wrong pair, Shuffled geometry,
  Fixed-label swap, Distance only, Compatibility only.

## 7. Manuscript-Wide Terminology Contract

Introduction, Related Work, Method, Experiments, captions, supplement에 다음
표기를 동일하게 적용한다.

| 개념 | 표준 표현 |
| --- | --- |
| $Z$ | `source relation score` |
| $G$ | `predicate-independent pair-geometry measurements` |
| $C$ | `predicate--geometry compatibility` |
| $C^{\rm tr}$ | `transformation-consistent compatibility` |
| vertical 변환 | `joint endpoint swap and inverse-predicate transformation` |
| ranking | `family-aware re-ranking` |
| pair 최초 정의 | `ordered subject--object pair` |
| pair 후속 지칭 | `corresponding ordered pair` |
| metric | `Recall@$K$`, `Violation@$K$` |
| 일반 오류 | 문장 안에서 lowercase `violation` |
| 적용 범위 | proximity/vertical은 re-rank, support/contact는 source order 유지 |

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
