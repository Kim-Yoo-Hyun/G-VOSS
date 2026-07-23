# RelCompat3D `user_v3.tex` 재검토

검토일: 2026-07-23 KST
대상: `paper/user_v3.tex`
범위: Abstract부터 Conclusion까지 332행
PDF 빌드: 수행하지 않음
인용 검토: 섹션에서 처음 등장하는 연구명과 줄임말에 인용이 존재하는지만 확인
인용 표기법과 인용 대상의 적절성: 검토 제외

## 상태와 심각도

- `[x] 해결`: 현재 원고에서 해결됨
- `[~] 부분 해결`: 핵심은 맞지만 독자 이해나 표현을 더 다듬어야 함
- `[ ] 미해결`: 제출 전에 수정이 권장됨
- `[>] 마무리 단계`: layout과 supplement pointer를 복원할 때 처리

심각도는 다음처럼 구분한다.

- **치명적**: 사실관계, claim, method 정의, 평가 해석을 바꿀 수 있는 문제
- **사소**: 문법, 읽기 난이도, 용어 통일, 중복, caption 완결성 문제

## 총평

연구 task, 방법 범위, Table 1의 point-estimate claim은 정합하다. RelCompat3D는
fixed relation candidates에 대해 source relation score와 분리된
predicate--geometry compatibility를 추정하고, re-ranking에서만 두 값을 결합한다.
Abstract와 Conclusion의 결과 범위도 공개 수치가 지지한다.

다만 현재 버전에는 제출 전에 반드시 고쳐야 할 편집 오류가 두 개 있다. Abstract
3행에는 교체 전 문장 조각이 남았고, Method 141행의 `\mathcalf`는 정의되지 않은
LaTeX 명령이다. 이는 scientific claim의 실패는 아니지만, 현 상태 그대로는
문법과 빌드 안정성에 영향을 준다.

전체 구조는 top-tier vision paper에서 흔히 사용하는 흐름과 유사하다.

1. Abstract는 문제, 방법, 평가, 범위가 제한된 결과를 순서대로 제시한다.
2. Introduction은 failure mode, 기존 접근과의 구체적 차이, design choice, 평가,
   contribution으로 이어진다.
3. Related Work는 주제별로 선행연구를 묶고 각 문단 끝에서 RelCompat3D와의 차이를
   설명한다.
4. Method는 notation, estimator, training, transformation, ranking 순서로 전개된다.
5. Experiments는 setup, primary result, controls, alternative audit 순서로 구성된다.

처음 읽는 독자에게 가장 어려운 부분은 Method다. Negative construction과
relation-preserving augmentation의 차이, family label의 여러 역할, transformation
set과 transformation group의 연결을 여러 번 되짚어 읽어야 한다. Experiment는
주요 설계 요소 대부분을 검증하지만 linked pairwise loss 제거와 transformation
averaging 제거는 직접적인 component deletion으로 보고되지 않는다. 아래 60번 이후
항목과 마지막 섹션별 체크가 현재 원고에 대한 최신 판정이다.

# 기존 1--59번 이슈 재확인

| 번호 | 상태 | 최신 판단 |
| --- | --- | --- |
| 1--13 | `[x]` | Abstract, Introduction, Related Work, Figure 1과 Figure 2의 이전 사실관계 및 caption 문제 해결 |
| 14 | `[>]` | 주석 처리된 supplement pointer와 final layout 문구는 마무리 단계에서 복원 |
| 15--21 | `[x]` | support/contact comparison 범위, OBB 정의, transformation score, ranking 정의, Figure 3 label 해결 |
| 22 | `[ ]` | Discussion의 broader-claims 문장은 사용자 선택에 따라 future-work 항목으로 유지 |
| 23--24 | `[x]` | Conclusion 범위와 Table 3 header 해결 |
| 25 | `[~]` | 개념 차이는 Introduction에 설명됐지만 Method의 negative와 augmentation 설명은 68번처럼 더 명확히 정리 필요 |
| 26--32 | `[x]` | Problem Formulation 분할, MLP skip path, metric equation, Figure 3와 Table 1 설명 해결 |
| 33 | `[x]` | Table 2 caption에 percentage 단위 반영 |
| 34 | `[x]` | Table 3 caption이 measured와 decidable coverage의 분모를 selected candidates 기준으로 설명 |
| 35 | `[x]` | Experimental Setup과 Discussion에서 `ordered-pair geometry`로 복원 |
| 36--45 | `[x]` | source relation score, metric notation, vertical-order, 소유격, punctuation, support/contact ranking 설명 해결 |
| 46 | `[x]` | Table 2를 실험 질문 중심으로 호출하는 문장 반영 |
| 47 | `[>]` | figure path, trim, caption style, page count, overflow, float placement는 final pass에서 확인 |
| 48 | `[x]` | section-first acronym citation 존재 여부 확인 |
| 49 | `[~]` | 이전 Results 문법 오류는 해결됐지만 쉬운 영어 관련 신규 항목이 남음 |
| 50 | `[~]` | 원시 word count보다 개념 밀도가 높은 문장이 일부 남음 |
| 51 | `[~]` | 허용 가능한 scope 반복과 줄일 수 있는 실질적 반복이 함께 존재 |
| 52 | `[x]` | claim 범위와 point-estimate 한정이 수치와 정합 |
| 53 | `[~]` | 필요한 limitation은 유지하되 반복적이거나 이득이 적은 표현은 축소 가능 |
| 54 | `[x]` | method의 원리적 연결과 claim의 타당성에 문제 없음 |
| 55 | `[x]` | 모든 Figure와 Table이 본문에서 최소 한 번 참조됨 |
| 56 | `[x]` | 모든 caption이 현재 표와 그림의 목적, metric, 단위 또는 panel 흐름을 설명 |
| 57 | `[x]` | Contribution 2는 여러 design element를 failure cause와 연결하므로 method contribution으로 유지 가능 |
| 58 | `[x]` | one-column Table 3에서 `Coverage (M/D)`를 유지할 수 있음 |
| 59 | `[x]` | Main Table 3에서 CI를 제외하고 supplement에 interval evidence를 두는 범위가 명확함 |

## Section-first acronym citation 존재 여부

인용 표기법은 판단하지 않고 존재 여부만 다시 확인했다.

- **Introduction, 8, 18, 31행**: 3D scene graph, Open3DSG,
  SceneGraphFusion과 SGFN의 첫 등장 문장에 인용이 존재한다.
- **Related Work, 43--54행**: 3DSSG, VLM, SCR-SSG, PUF의 첫 등장 문장에
  인용이 존재한다.
- **Method, 79행**: VL-SAT, SGFN, Open3DSG의 첫 등장 문장에 인용이 존재한다.
- **Experiments, 172, 175행**: Open3DSG, VL-SAT, SGFN, 3DSSG, 3RScan, RRF의
  첫 등장 문장에 인용이 존재한다.
- **Discussion and Limitations, 327행**: 3DSSG의 첫 등장 문장에 인용이 존재한다.
- **Conclusion, 332행**: 3DSSG의 첫 등장 문장에 인용이 존재한다.

OBB, ReLU, BCE는 일반 기술 용어다. OBB는 Method와 Audit에서 section-first
등장 시 `oriented bounding box (OBB)`로 풀어 쓴다.

# 이번 재검토의 미해결 이슈

## 60. [ ] Abstract의 잔여 문장 조각

**심각도: 치명적**
**위치: Abstract, 3행**

원문:

> Transformation averaging assigns the same compatibility to equivalent
> endpoint and predicate representations. enforces equal compatibility under
> the defined relation-preserving endpoint/predicate transformations.

첫 문장은 이미 의도를 충분히 설명한다. 뒤의 `enforces ...`는 주어가 없는 교체 전
문장 조각이다.

권장 조치:

> `enforces equal compatibility under the defined relation-preserving
> endpoint/predicate transformations.`를 삭제한다.

## 61. [ ] Introduction의 predicate와 ordered-pair 용어

**심각도: 사소**
**위치: Introduction, Motivation, 22행과 24--25행**

원문:

> relation predictors rank high scores to predicates

> whether the corresponding object pair satisfies the predicate in 3D

첫 표현은 동사와 목적어의 결합이 잘못됐다. 둘째 표현은 의미는 맞지만 canonical
term인 `corresponding ordered pair`와 다르다.

권장 교체:

> relation predictors assign high scores to predicates

> whether the corresponding ordered pair satisfies the predicate in 3D

Reliability 문장은 현재 자연스럽게 수정되어 해결됐다.

## 62. [x] Contribution 2의 명사구 밀도

**심각도: 사소**
**위치: Introduction, Contribution 2, 36행**

원문:

> We learn source-score-excluded compatibility from identity-preserving
> ordered-pair examples, optimize linked positive--counterfactual ordering, and
> enforce exact consistency under applicable endpoint and predicate
> transformations.

`source-score-excluded compatibility`와 `identity-preserving ordered-pair
examples`가 연속되어 처음 읽는 독자에게 어렵다. Contribution의 내용은 타당하지만
동사 중심으로 풀어 쓰는 편이 낫다.

권장 문장:

> We estimate compatibility from the corresponding ordered pair without using
> the source relation score or predictor identity, train it with linked
> positive--counterfactual pairs, and enforce exact consistency under the
> applicable endpoint and predicate transformations.

## 63. [x] Related Work의 부자연스러운 collocation과 용어 혼용

**심각도: 사소**
**위치: Related Work, 3D Scene Graph Prediction, 44행**

원문:

> Recent predictors improve closed-set predicates

Method가 개선하는 대상은 predicate 자체가 아니라 relation prediction이다.

권장 문장 시작:

> Recent methods improve closed-set relation prediction using

**위치: Related Work, Geometry-aware Relation Evidence, 49행**

원문:

> excluding predictor identity and score from compatibility

`score`만 쓰면 source relation score인지 불명확하다.

권장 교체:

> excluding predictor identity and the source relation score from compatibility

**위치: Related Work, Geometry-aware Relation Evidence, 51행**

원문:

> RelCompat3D estimates continuous compatibility

권장 교체:

> RelCompat3D estimates a continuous compatibility score

## 64. [x] exact-label과 exact-match 혼용

**심각도: 사소**
**위치: Related Work, Reliability Evaluation and Calibration, 56행**

원문:

> Recall@$K$ measures exact-label retrieval rank

원고의 metric 명칭은 `exact-match Recall@$K$`다.

권장 문장:

> Recall@$K$ measures exact-match retrieval. It does not measure compatibility
> with reconstructed ordered-pair geometry.

같은 문단의 마지막 문장은 더 직접적으로 쓸 수 있다.

원문:

> This joint evaluation complements conventional retrieval and calibration
> analyses without offering a probability guarantee for either metric.

권장 문장:

> This joint evaluation complements conventional retrieval and calibration
> analyses. The two metrics are not calibrated probabilities.

## 65. [x] Figure 2 caption의 measurement 용어

**심각도: 사소**
**위치: Figure 2 caption, 66--69행**

원문:

> predicate semantics and pair measurements

`pair measurements`는 Abstract와 Method의
`predicate-independent geometric measurements of the ordered pair`보다 넓고
모호하다. Caption에서는 다음 짧은 표현이 적합하다.

권장 교체:

> predicate semantics and ordered-pair measurements

Caption의 나머지 흐름은 적절하다. Panel 역할, score separation, re-ranking 결과를
본문보다 짧게 설명하므로 불필요한 반복이 아니다.

## 66. [x] Method overview의 candidate identity

**심각도: 사소**
**위치: Method overview, 75행**

원문:

> It preserves candidate identity

어떤 identity인지 Problem Formulation을 읽기 전에는 알 수 없다.

권장 문장:

> It preserves the ordered-pair identity of each candidate, estimates
> predicate--geometry compatibility without the source relation score, and
> combines the two only during re-ranking.

지면이 허용되면 바로 뒤에 한 문장의 roadmap을 넣을 수 있다.

> We first define the compatibility inputs, then describe the two estimators and
> the family-aware ranking rule.

이 roadmap은 필수는 아니지만 dense notation에 들어가기 전 독자 안내 역할을 한다.

## 67. [x] Family label의 여러 역할을 한 문장에서 설명

**심각도: 사소**
**위치: Method, Problem Formulation, 83행**

원문:

> The family label $a_i$ selects the applicable transformation set and
> determines whether the relation family is re-ranked. It also selects the head
> and training-split normalization statistics for the linear estimator, whereas
> the shared nonlinear estimator encodes it as a semantic indicator.

내용은 정확하지만 transformation, ranking scope, Linear routing, MLP input이 한 번에
나온다. 다음처럼 역할을 두 단계로 나누면 더 친절하다.

권장 문장:

> The family label $a_i$ selects the applicable transformations and determines
> whether the candidate is re-ranked. For the Linear estimator, it also selects
> the compatibility head and training-split normalization statistics. The shared
> MLP instead encodes the family as an input indicator.

## 68. [~] Negative construction과 augmentation의 설명 순서 및 중복

**심각도: 사소지만 우선순위 높음**
**위치: Method, Problem Formulation과 Relation-Consistent Compatibility, 93--97행,
128--134행**

원문:

> Vertical-order negatives retain the ordered pair and replace the ground-truth
> predicate with its inverse.

> For vertical order, augmentation swaps the endpoints and replaces the
> predicate with its inverse.

> The augmentation preserves the predicate when proximity endpoints are
> swapped, whereas vertical order swaps endpoints and applies the inverse
> predicate.

세 문장은 각각 맞지만 vertical negative와 relation-preserving augmentation의 차이를
떨어진 위치에서 반복한다. 첫 설명에서 두 개념을 대조하고, loss 문단에서는 이미
정의한 augmentation을 가리키는 편이 명확하다.

93--97행 권장 구성:

> Training-split ground truth provides positives. Proximity negatives use
> distant, non-overlapping same-context pairs. Vertical-order negatives keep the
> endpoints fixed and replace the predicate with its inverse. Separately,
> relation-preserving augmentation swaps proximity endpoints without changing
> the predicate and jointly swaps vertical endpoints with the inverse predicate.

132행은 아직 같은 augmentation을 다시 풀어 쓴다. 권장 시작:

> Training combines this augmentation with a linked
> positive--counterfactual ranking loss. For every linked pair
> $(i^+,i^-)\in\mathcal P$, the logits receive a fixed margin penalty:

Support/contact head는 Product all families comparison에 사용되므로 final pass에서
다음 정도의 main-to-supplement pointer도 복원해야 한다.

> A support/contact head is fitted only for the Product (all families)
> comparison. Its negative-construction rules are provided in the supplement.

## 69. [x] `input separation`의 의미가 불명확함

**심각도: 사소**
**위치: Method, Relation-Consistent Compatibility, 104행**

원문:

> under the same input separation, training targets, loss, and transformation
> averaging

`input separation`은 연구 내부 용어처럼 들린다. 의도는 predicate semantics,
ordered-pair measurements, source score의 역할 분리다.

권장 교체:

> under the same factor separation, training targets, loss, and transformation
> averaging

더 쉬운 표현을 원하면 다음처럼 쓸 수 있다.

> using the same separated inputs, training targets, loss, and transformation
> averaging

## 70. [x] source-score exclusion의 실질적 반복

**심각도: 사소**
**위치: Method, Relation-Consistent Compatibility, 126행과 153행**

126행은 estimator input exclusion을 정의하므로 필요하다. 153행의 다음 절은 같은
사실을 다시 말한다.

원문:

> It does not use the source relation score, while the pairwise objective
> encourages each linked positive to score above its counterfactual.

첫 절을 삭제하고 다음처럼 두 guarantee를 분리한다.

권장 문장:

> Group averaging makes proximity symmetry and invariance under joint endpoint
> swap and inverse-predicate transformation exact at inference. The pairwise
> objective encourages each linked positive to score above its counterfactual.

## 71. [x] Family-aware ranking의 plain-language 연결 문장

**심각도: 사소**
**위치: Method, Family-Aware Re-ranking, 164--165행**

원문:

> For support/contact, $\pi_a^q$ is its subsequence in $\pi^Z$.

`its`의 선행사가 잠시 모호하다.

권장 교체:

> For support/contact, $\pi_a^q$ is the corresponding family subsequence of
> $\pi^Z$.

수식 뒤에 다음 한 문장을 넣으면 알고리즘의 핵심이 그림 없이도 이해된다.

> Thus, a candidate can exchange positions only with candidates from the same
> re-ranked family.

## 72. [ ] 두 estimator의 차이를 설명하는 문법

**심각도: 사소**
**위치: Method 마지막 문단, 168행**

현재 원문:

> RelCompat3D-Linear and RelCompat3D-MLP use different model compatibility.

`use different model compatibility`는 자연스러운 영어가 아니다.

권장 문장:

> RelCompat3D-Linear and RelCompat3D-MLP differ in how they model
> compatibility. The first uses family-specific linear heads, and the second
> uses a shared nonlinear estimator.

## 73. [x] Experimental Setup의 반복적 표현과 결과 위치

**심각도: 사소**
**위치: Experimental Setup, Metrics, 193행**

원문:

> Within-family results and family-specific metrics within the selected top-K
> predictions show whether aggregate changes are driven by relation-family
> composition.

`within`과 `family`가 반복되고, 해당 결과가 main paper인지 supplement인지 알 수 없다.

권장 문장:

> The supplement reports per-family metrics and the family composition of the
> selected top-$K$ predictions.

## 74. [x] Results의 interval 용어와 SGFN tie 설명

**심각도: 사소지만 우선순위 높음**
**위치: Results, Recall--Violation Results, 250행**

원문:

> the paired scan-resampling intervals are strictly positive for Recall and
> negative for Violation

Experimental Setup은 `Paired 95\% confidence intervals`와 `bootstrap resamples`를
사용한다. 같은 통계를 Results에서 새 용어로 부르지 않는 편이 좋다.

권장 교체:

> the paired 95\% bootstrap intervals exclude zero in the favorable direction
> for both Recall and Violation

원문:

> SGFN is tied at $K=5$ and changes only marginally at $K=10$

무엇이 tied인지 명시한다.

권장 문장:

> For SGFN, both metrics are tied with Source at $K=5$ and change only
> marginally at $K=10$.

## 75. [x] Results의 vague comparison과 evidence pointer

**심각도: 사소**
**위치: Results, Recall--Violation Results, 252행**

원문:

> RankAvg and RRF attain competitive Violation in some reported $K$ values

`competitive`는 평가적이고 범위가 모호하다.

권장 교체:

> RankAvg and RRF attain lower Violation at some reported $K$ values but show
> larger low-$K$ Recall losses on VL-SAT and SGFN.

원문:

> Product (all families) can raise aggregate Recall and lower aggregate
> Violation, but it changes support/contact selections and can mask a regression
> in that family.

마지막 claim은 family-specific supplement 결과를 근거로 한다면 위치를 알려 주는 편이
안전하다.

권장 문장:

> Product (all families) can raise aggregate Recall and lower aggregate
> Violation, but it changes support/contact selections. Supplemental
> family-specific results show that this aggregate change can coincide with a
> support/contact regression.

## 76. [~] Ablation의 causal strength

**심각도: 사소**
**위치: Results, Ablations and Controls, 297--299행**

현재 원문:

> Their nearly identical aggregate values reflect that both controls reverse
> the signed interpretation of vertical-order geometry.

Aggregate similarity의 원인을 완전히 증명한 것은 아니므로 causal strength를 낮춘다.

권장 문장:

> Their nearly identical aggregate values partly reflect that both controls
> reverse the signed interpretation of vertical-order geometry.

`reflect`도 관찰된 동일 수치의 원인을 확정하는 인상을 준다.

권장 문장:

> Their nearly identical aggregate values are consistent with both controls
> reversing the signed interpretation of vertical-order geometry.

`For RelCompat3D-Linear` 표기와 중복 MLP 문장 삭제는 해결됐다.

## 77. [x] Table 3의 단위와 coverage 분모

**심각도: 사소지만 caption 완결성에 중요**
**위치: Table 3 caption, 302--317행**

원문:

> Violation rate at $K=50$ requiring agreement between point- and mesh-based
> labels. $\Delta$V is RelCompat3D-Linear minus Source in percentage points.
> Coverage reports measured and decidable percentages.

`Source`와 `Linear`의 단위가 caption에 직접 쓰이지 않고, measured와 decidable의
분모도 정의되지 않는다. `Coverage (M/D)`를 유지하되 본문이나 caption에서 한 번은
뜻을 풀어야 한다.

권장 caption:

> Point- and mesh-based Violation at $K=50$. Source and Linear are percentages,
> and $\Delta$V is RelCompat3D-Linear minus Source in percentage points.
> Coverage reports the percentages of selected candidates with both
> measurements available and with an agreed satisfied or violated label.

이 구성은 CI range를 main table에 다시 넣지 않는다. `Measured`와 `Decidable`을 별도
열로 나누는 것도 필수가 아니다.

## 78. [ ] Audit label 문장의 오탈자와 병렬 구조

**심각도: 사소**
**위치: Point- and Mesh-Based Consistency Audit, 321행**

현재 원문:

> The audit lables do not use OBB measurements, predictor identity, the source
> relation score, learned compatibility, and primary verifier status labels.

Audit label의 construction을 주어로 둔 것은 맞다. `lables`는 오탈자이고, 부정문에서
마지막 항목은 `or`로 연결하는 편이 정확하다.

권장 문장:

> The audit labels do not use OBB measurements, predictor identity, the source
> relation score, learned compatibility, or primary-verifier status labels.

## 79. [~] Audit Results의 예외 표현

**심각도: 사소**
**위치: Point- and Mesh-Based Consistency Audit, 323--324행**

원문:

> It decreases for all three predictors.

`It`이 Violation인지 alternative measure인지 바로 드러나지 않는다.

권장 문장:

> The alternative Violation rate decreases for all three predictors.

원문:

> the point- and mesh-based changes having the same direction at every reported
> $K$. The only exception is a tie for SGFN at $K=5$.

`same direction at every K`라고 한 뒤 exception을 붙여 논리 흐름이 꺾인다.

권장 문장:

> Across all five $K$ values, the changes are favorable or tied for both
> RelCompat3D variants. SGFN at $K=5$ is the only tie.

이 문장은 supplement 수치와 다시 대조한 뒤 사용한다.

## 80. [~] Discussion 문장 종결

**심각도: 사소**
**위치: Discussion and Limitations, 327--329행**

Support/contact 용어와 `independent ground truth for geometric validity` 표현은
해결됐다. 다만 329행 마지막에 마침표가 없다.

권장 조치:

> 문장 끝에 마침표를 추가한다.

22번의 broader-claims 문장은 future-work 성격이므로 사용자 선택에 따라 미해결로
유지한다.

# 중복 검토

## 유지 가능한 반복

- Abstract, Introduction, Conclusion의 core claim 반복은 각 섹션의 역할이 달라
  허용된다.
- Figure caption과 본문의 method flow 반복은 caption이 독립적으로 읽혀야 하므로
  필요하다.
- support/contact scope를 Abstract, Introduction, Method에서 언급하는 것은 적용
  범위를 오해하지 않게 하므로 유지할 수 있다.
- Table 3 caption과 Audit 본문의 agreement rule 반복도 caption 자립성을 위해
  허용된다.

## 줄이는 것이 좋은 반복

1. Method 95행과 134행의 augmentation 설명은 68번처럼 한 번만 자세히 정의한다.
2. Method 126행과 153행의 source-score exclusion 반복은 70번처럼 153행에서 줄인다.
3. Results 299행의 MLP operating-point 문장은 252행과 겹치므로 삭제한다.
4. Experimental Setup 193행은 per-family result의 위치만 간단히 안내한다.

# 용어 통일 계약

| 개념 | 현재 혼용 | 권장 통일 |
| --- | --- | --- |
| predicted relation | `label`, `predicate` | `predicate` |
| ordered pair | `same object pair`, `ordered pair`, `corresponding ordered pair` | 최초 `ordered subject--object pair`, 이후 `corresponding ordered pair` |
| geometry input | `pair measurements`, `geometry measurements`, `geometric measurements of the ordered pair` | 정식 `predicate-independent geometric measurements of the ordered pair`, 축약 `ordered-pair measurements` |
| source score | `score`, `predictor score`, `source relation score` | `source relation score` |
| exact retrieval metric | `exact-label Recall`, `exact-match Recall` | `exact-match Recall@$K$` |
| interval | `scan-resampling interval`, `confidence interval`, `bootstrap interval` | `paired 95\% bootstrap interval` |
| Linear variant | `Linear head`, `Linear`, `RelCompat3D-Linear` | 본문 결과 해석에서는 `RelCompat3D-Linear` |
| audit metric | `this measure`, `It`, `alternative geometric measure` | `alternative Violation rate` 또는 `point- and mesh-based Violation` |
| retained family | `contact-dependent relations`, `support/contact` | `support/contact candidates` |

# 영어 표현과 문장 길이

## 전체 판단

원고는 전반적으로 good technical English에 가깝다. 난해한 일반 영어 단어가 많지는
않다. 읽기 부담은 긴 문장 자체보다 하나의 문장에 여러 method role을 넣는 데서
발생한다. 특히 83행, 93--97행, 134행, 164--165행, 193행을 다듬으면 독자 부담이
크게 줄어든다.

소유격 형태, em dash, 산문 semicolon의 남용은 발견되지 않았다. 대부분의 문장은
한 문장에 하나의 주장만 둔다. Introduction 27행은 길지만 여러 짧은 문장으로 이미
분할되어 있어 유지할 수 있다.

## accepted-paper 전개와의 비교

확인한 AAAI reference paper와 CVF accepted paper는 대체로 다음 방식을 사용한다.

1. 수식 전 plain-language intent를 한 문장으로 제시한다.
2. 새로운 기호는 한 문단에서 한 역할씩 소개한다.
3. Results는 table을 다시 읽는 대신 핵심 comparison과 원인을 설명한다.
4. Caption은 panel 목적과 평가 축을 설명하되 method의 모든 예외를 넣지 않는다.
5. Related Work 문단은 연구군을 요약한 뒤 현재 방법과의 차이로 닫는다.

`user_v3.tex`는 3--5번을 잘 따른다. 1--2번은 Method의 family routing, negative와
augmentation, family-aware ranking에서 더 보완할 수 있다.

참고한 accepted-paper 예시:

- [CVPR 2025, Conformal Prediction and MLLM aided Uncertainty Quantification in Scene Graph Generation](https://openaccess.thecvf.com/content/CVPR2025/html/Nag_Conformal_Prediction_and_MLLM_aided_Uncertainty_Quantification_in_Scene_Graph_CVPR_2025_paper.html)
- [ICCV 2025, Statistical Confidence Rescoring for Robust 3D Scene Graph Generation from Multi-View Images](https://openaccess.thecvf.com/content/ICCV2025/html/Yeo_Statistical_Confidence_Rescoring_for_Robust_3D_Scene_Graph_Generation_from_ICCV_2025_paper.html)
- Local AAAI references: `paper/reference_AAAI/AAAI26.KimN-CV.pdf`,
  `paper/reference_AAAI/AAAI_KangM-5173.pdf`

# Figure와 Table 검토

## 본문 참조

| 항목 | Label | 본문 최초 참조 |
| --- | --- | --- |
| Figure 1 | `fig:teaser` | Introduction 22행 |
| Figure 2 | `fig:overall_framework` | Method 75행 |
| Figure 3 | `fig:tradeoff` | Results 250행 |
| Table 1 | `tab:main-results` | Results 250행 |
| Table 2 | `tab:ablations` | Ablations 297행 |
| Table 3 | `tab:surface-audit` | Audit 323행 |

모든 Figure와 Table이 본문에서 최소 한 번 참조된다.

## Caption 판단

- **Figure 1, 17--18행**: source, failure evidence, rank change, method variant가
  모두 명시된다. 현재 목적에 적합하다.
- **Figure 2, 66--69행**: panel별 역할과 score flow가 충분하다. 65번의 measurement
  용어만 통일하면 된다.
- **Figure 3, 244행**: metric, 세 curve, 다섯 $K$, 선호 방향, axis 차이가 명확하다.
  shared target는 Setup과 Table 1에 있으므로 caption에 반복할 필요가 없다.
- **Table 1, 233행**: target, metric, percentage, Source, ranking scope가 명시된다.
- **Table 2, 292행**: Linear controls와 MLP full rows의 범위, metric, 단위가
  명시된다.
- **Table 3, 316행**: metric과 delta는 설명되지만 77번처럼 Source와 Linear의 단위,
  M/D의 분모를 보완하는 편이 좋다.

# Claim과 공개 범위

## 정확히 유지된 claim

- 세 predictor를 하나의 shared 3DSSG validation target에서 비교한다.
- 결과는 point estimate로 한정한다.
- 두 estimator 중 하나의 보편적 우월성을 주장하지 않는다.
- support/contact correction을 주장하지 않는다.
- point/mesh audit을 independent physical-validity ground truth로 부르지 않는다.
- dataset-level generalization이나 SOTA를 주장하지 않는다.

## 공개할 필요가 있는 경계

- single-target scope
- support/contact candidates를 re-rank하지 않는 범위
- primary verifier와 compatibility input이 일부 OBB-derived measurements를 공유한다는
  사실
- audit가 같은 reconstructed scenes와 ontology를 사용한다는 사실
- predictor-specific refitting을 하지 않는 protocol

이 내용은 reviewer가 결과의 의미를 판단하는 데 필요하므로 삭제하지 않는 편이
안전하다. 다만 같은 경계를 Method와 Discussion에서 동일한 문장으로 반복할 필요는
없다.

## 선택적으로 줄일 수 있는 내용

- Discussion 330행의 broader-claims 문장은 future-work 성격이 강하다. 22번 사용자
  선택을 유지한다.
- Results 299행의 MLP operating-point 문장은 이미 앞에서 설명되므로 삭제할 수 있다.
- Method 153행의 source-score exclusion은 estimator input 정의와 중복되므로 줄일 수
  있다.

# 섹션별 최종 판단

## Abstract, 1--4행

문제, task, identity, score separation, two estimators, transformation, ranking scope,
evaluation, result, alternative audit이 모두 들어 있다. Claim은 정확하다. 60번의
transformation 문장만 더 자연스럽게 바꿀 수 있다. 현재 문장 분할은 유지한다.

## Introduction, 7--38행

Failure, gap, design necessity, evaluation, contribution의 전개는 자연스럽다. 61번과
62번의 표현을 다듬으면 처음 읽는 독자에게 더 쉬워진다. Contribution 2는 method의
핵심 design bundle이므로 유지할 수 있다.

## Related Work, 41--56행

각 문단은 연구군과 RelCompat3D의 공통점 및 차이점을 설명한다. 단순 나열에 머물지
않는다. 63번과 64번의 collocation 및 metric 용어만 통일하면 된다.

## Method, 59--168행

수학 정의는 일관되고 구현 범위와도 맞는다. 가장 큰 읽기 부담은 family label의 역할,
negative와 augmentation의 차이, ranking list의 실제 동작이다. 66--72번이 이 부분을
해결한다. 새 수식을 추가할 필요는 없다.

## Experimental Setup, 171--193행

Predictor, target, split, baseline, fitting boundary, metric denominator가 충분히
설명된다. 73번처럼 per-family result의 위치를 명확히 하면 더 친절하다.

## Recall--Violation Results, 195--252행

Table 1 수치, Figure 3 trajectory, point-estimate claim은 정합하다. 74번과 75번처럼
interval 용어, SGFN tie, vague comparison을 다듬는 것이 좋다.

## Ablations and Controls, 255--299행

Table 2 reference와 실험 질문은 잘 연결된다. Control 해석도 수치와 맞는다. 76번처럼
causal strength를 낮추고 중복 MLP 문장을 삭제하면 더 간결해진다.

## Point- and Mesh-Based Consistency Audit, 302--324행

Alternative measurement의 필요성, 구성, primary metric과의 차이가 설명된다. Table 3
caption과 본문에서 coverage 분모, audit label의 독립된 입력, 결과 대명사를 명확히
해야 한다.

## Discussion and Limitations, 325--329행

Single-target scope와 audit boundary는 필요한 limitation이다. 80번처럼 canonical
support/contact 용어와 자연스러운 ground-truth 표현으로 바꾸면 된다.

## Conclusion, 331--332행

Method scope, shared target, point-estimate claim이 정확하고 간결하다. 새 문제는 없다.

# 최종 수정 우선순위

1. **Method, 93--97행과 128--134행**에서 negative construction과 augmentation을
   68번처럼 한 번에 대조하고 반복을 제거한다.
2. **Results, 250행**의 interval 용어와 SGFN tie를 74번처럼 명확히 한다.
3. **Table 3 caption, 316행**에 Source와 Linear의 단위 및 M/D 정의를 보완한다.
4. **Audit, 321--324행**에서 audit label construction과 결과 대명사를 명확히 한다.
5. **Introduction, 22, 24--25, 36행**의 predicate, ordered-pair, Contribution 2
   표현을 쉽게 고친다.
6. **Related Work, 44, 49, 51, 56행**의 collocation과 canonical terminology를
   통일한다.
7. **Method, 75, 83, 104, 153, 164--168행**을 66--72번 권장처럼 간결하게 만든다.
8. **Results, 252, 297--299행**의 vague comparison, causal strength, 중복 MLP
   문장을 정리한다.
9. **Discussion, 328--330행**의 support/contact와 ground-truth 표현을 통일한다.
10. Figure asset, caption typography, page placement, overflow는 예정된 final pass에서
    확인한다.

현재 scientific claim을 무너뜨리는 새 실험 문제는 없다. 남은 작업은 Method의 설명
친절성, Results의 용어 일관성, Table 3 caption의 자립성을 높이는 수정이다.

# 최신 섹션별 completeness audit

이 절은 현재 `user_v3.tex` 332행을 다시 읽고 작성한 최신 판정이다. 앞의 60--80번
항목에서 현재 문장과 달라진 부분은 이 절의 판정을 우선한다.

## 전체 구성과 일관성

| 검토 항목 | 판정 | 근거 |
| --- | --- | --- |
| 섹션 순서 | 통과 | Abstract, Introduction, Related Work, Method, Experiments, Discussion and Limitations, Conclusion 순서 |
| 문제에서 해법으로 이어지는 흐름 | 통과 | geometric mismatch, source-score gap, compatibility estimation, family-aware re-ranking, joint evaluation으로 연결 |
| Contribution과 Method 대응 | 통과 | mismatch measurement, compatibility learning과 transformations, constrained re-ranking이 각각 본문 정의와 대응 |
| Contribution과 Experiment 대응 | 부분 통과 | identity, predicate, geometry, score fusion, capacity는 검증됨. Pairwise loss 제거와 transformation averaging 제거는 직접 보고되지 않음 |
| Claim과 수치 정합성 | 통과 | Table 1의 모든 predictor와 $K$에서 두 variant의 Recall point estimate는 Source 이상이고 Violation은 Source 이하 |
| Terminology | 부분 통과 | 핵심 용어는 안정적이나 `ordered pair geometry`, `vertical violations`, `group averaging`이 canonical 표현과 일부 다름 |
| Figure와 Table 본문 참조 | 통과 | Figure 1--3과 Table 1--3이 각각 최소 한 번 본문에서 호출됨 |
| Caption 자기완결성 | 대체로 통과 | Figure 1, Figure 3, Table 1--3은 충분함. Figure 2는 transformation averaging이 그림 내부에는 보이지 않음 |
| 처음 읽는 독자의 이해 | 부분 통과 | Introduction과 Results는 친절함. Method의 counterfactual, augmentation, transformation group 연결은 추가 설명이 필요 |
| 재현 가능성 | 부분 통과 | 핵심 식, split, features, loss, ranking은 있음. 상세 construction과 optimization pointer가 주석 처리됨 |

## 81. [ ] 잘못된 LaTeX 명령

**심각도: 치명적**
**위치: Method, Relation-Consistent Compatibility, 141행**

원문:

> `$\mathcalf R$ penalizes non-bias weights.`

`\mathcalf`는 원고나 style에서 정의되지 않은 명령이다. 앞의 loss 식은
`\mathcal R(\theta_q)`를 사용한다.

권장 교체:

> `$\mathcal R$ penalizes non-bias weights.`

## 82. [ ] Abstract의 자기완결성

**심각도: 사소**
**위치: Abstract, 3행**

Abstract는 문제, 방법, 결과, empirical contribution을 모두 포함한다. Introduction의
세 contribution과도 과부족 없이 대응한다.

1. Geometric mismatch와 두 metric은 Contribution 1에 대응한다.
2. Score-excluded compatibility, linked pairs, transformations는 Contribution 2에
   대응한다.
3. Family-aware scope와 three-predictor evaluation은 Contribution 3에 대응한다.

두 가지 용어만 처음 읽는 독자에게 설명이 부족하다.

원문:

> Family-specific linear heads and a shared nonlinear estimator are trained
> with linked positive--counterfactual pairs.

> on a shared 3DSSG target

`linked positive--counterfactual pairs`는 논문 고유 training construction이다.
`3DSSG`도 Abstract 안에서는 풀어 쓰지 않는다.

권장 문장:

> Family-specific linear heads and a shared nonlinear estimator are trained on
> linked ground-truth positives and constructed counterfactuals.

권장 표기:

> on a shared 3D Semantic Scene Graph (3DSSG) target

Abstract에는 citation이 없고 정의되지 않은 수식 기호도 없다. $K$는 metric 이름의
일부로 쓰여 독립 수식 기호처럼 남지 않는다. `point estimates`라는 한정도 유지되어
overclaiming을 막는다.

## 83. [ ] Introduction의 control 범위 표현

**심각도: 사소하지만 claim 해석에 중요**
**위치: Introduction, Method motivation, 29행**

원문:

> Matched fusion baselines and ablations test the effects of excluding the
> source relation score, preserving ordered-pair identity, and enforcing
> transformation consistency.

현재 controls는 source score의 ranking 기여, wrong pair와 shuffled geometry,
fixed-predicate swap을 검토한다. Source score를 estimator input에 넣는 조건과
transformation averaging을 제거한 조건은 main table에 없다. 따라서 `test the
effects of`는 직접 component deletion보다 강하게 들린다.

권장 문장:

> Matched fusion baselines and controls examine the roles of the source
> relation score, ordered-pair identity, and transformation consistency.

Introduction의 나머지 흐름은 문제 정의, 기존 한계, 구체적 gap, method design,
evaluation, contribution 순서로 자연스럽다. Citation이 필요한 선행연구 문장에는
모두 citation이 존재한다. `not necessarily`, `can`, `point estimates`의 hedging도
Method와 Experiment의 범위에 맞다.

## 84. [x] Related Work의 필수 구성

**심각도: 해당 없음**
**위치: Related Work, 41--56행**

세 subsection은 각각 다음 역할을 수행한다.

1. 3D Scene Graph Prediction은 fixed-generator post-processing이라는 차이를
   설명한다.
2. Geometry-aware Relation Evidence는 reconstructed ordered-pair compatibility와
   transformation scope의 차이를 설명한다.
3. Reliability Evaluation and Calibration은 calibration, uncertainty, selective
   prediction과 geometric compatibility의 차이를 설명한다.

언급된 연구군과 고유 방법명에는 citation이 존재한다. 각 문단은 관련 연구를 나열한
뒤 RelCompat3D와의 차이로 닫힌다. Subsection 간 깊이도 두 문단씩으로 균형이 맞는다.

작은 용어 수정은 95번에 정리한다. 44행과 49행에서 edge와 geometry evidence가
반복되지만 첫 문단은 generator, 둘째 문단은 evidence와 graph reuse를 설명하므로
기능적 중복으로 볼 수 있다.

## 85. [ ] Transformation 기호의 연결

**심각도: 사소하지만 수식 이해에 중요**
**위치: Method, Relation-Consistent Compatibility, 126행과 145행**

원문:

> For proximity, $\tau$ swaps the ordered endpoints ...

> let $H_{a_i}$ denote the finite transformation group for family $a_i$

독자는 $\tau$가 뒤의 $H_{a_i}$에 어떻게 포함되는지 추론해야 한다. 식은 맞지만
notation 연결 한 줄이 빠져 있다.

권장 문장:

> For proximity and vertical order, $H_a$ contains the identity and the
> family-specific transformation $\tau_a$ defined above.

이 문장을 orbit 정의 직전에 넣으면 transformation averaging의 수식 전개가
완결된다.

## 86. [ ] Source relation score의 곱셈 전제

**심각도: 사소하지만 재현성에 중요**
**위치: Method, Problem Formulation과 Family-Aware Re-ranking, 79행과 155--160행**

원문:

> We use sigmoid relation scores for VL-SAT/SGFN and cosine similarity between
> normalized text embeddings for Open3DSG

> $u_i^q=Z_iC_i^{\rm tr,q}$

Sigmoid score는 음수가 아니지만 cosine similarity의 이론적 범위에는 음수가 있다.
음수 $Z_i$에 $C_i^{\rm tr,q}\in[0,1]$를 곱하면 compatibility가 낮을수록 score가
0에 가까워져 순위가 올라갈 수 있다. 현재 manuscript와 supplement에는 evaluated
Open3DSG score의 관찰 범위가 없다.

권장 방안:

1. 실제 candidate score가 모두 음수가 아닌지 artifact에서 확인한다.
2. 음수가 없다면 supplement에 predictor별 observed minimum과 maximum을 짧게
   보고한다.
3. 음수가 있다면 현재 product utility의 동작을 다시 검증하고 score mapping을
   명시한다.

이 항목은 새 normalization을 요구하는 것이 아니다. 현재 곱셈이 의도대로
downweighting을 수행한다는 전제를 공개 가능한 수치로 확인하는 작업이다.

## 87. [ ] Method의 supplement pointer

**심각도: 사소하지만 재현성에 중요**
**위치: Method, 96, 142, 152, 164, 167행**

Threshold, negative cap, balancing, optimization details, proof, control
definitions을 안내하는 문장이 모두 주석 처리되어 있다. Main text만으로 핵심
알고리즘은 이해되지만 exact reproduction에는 supplement가 필요하다.

최소 권장 문장:

> The supplement provides the complete counterfactual rules, optimization
> details, proofs, and matched controls.

한 문장만 section 마지막에 두면 여러 pointer를 반복하지 않으면서 재현 가능성을
명확히 할 수 있다. Layout 때문에 현재 주석을 유지하기로 한 14번 계획은 final pass
전까지 유효하다.

## 88. [ ] Open3DSG evaluation coverage

**심각도: 치명적**
**위치: Experiments, Datasets and Evaluation, 172행**

원문:

> All evaluations use the same scope: 157 scans, 548 relation contexts, and
> 3,972 exact-match ground-truth relations

이 문장은 denominator에는 맞다. 그러나 supplement에 따르면 public Open3DSG
preprocessing은 548개 중 533개 context에서만 candidates를 만들고, 나머지 15개는
empty prediction으로 처리한다. 이 차이는 Recall denominator와 source coverage를
해석하는 데 필요하다.

권장 추가 문장:

> Open3DSG public preprocessing yields candidates for 533 of the 548 contexts.
> We retain all 548 contexts in the evaluation and treat the remaining 15 as
> empty predictions.

이는 약점을 불필요하게 노출하는 문장이 아니다. Shared-target fairness와
reproducibility를 판단하는 데 필요한 protocol disclosure다.

## 89. [ ] Method design과 direct ablation의 대응

**심각도: 사소하지만 reviewer defense에 중요**
**위치: Experiments, Baselines and Training 및 Ablations, 175행과 255--300행**

현재 evidence 대응은 다음과 같다.

| Method design | Main 또는 supplement evidence | 판정 |
| --- | --- | --- |
| Predicate semantics | Wrong predicate | 직접 대응 |
| Ordered-pair identity | Wrong pair, shuffled geometry | 직접 대응 |
| Geometry use | Distance only, feature removal | 직접 대응 |
| Source score와 compatibility의 결합 | Compatibility only, rank fusion | 직접 대응 |
| Family scope | Product all families, pooled comparison | 직접 대응 |
| Linear와 nonlinear estimator | 두 full variants, matched MLP controls | 직접 대응 |
| Linked pairwise loss | Pair-weight sensitivity만 존재 | removal control 없음 |
| Transformation averaging | Exact identity check와 fixed-predicate swap | averaging removal 없음 |

가장 유용한 추가 comparison은 pairwise weight를 0으로 둔 BCE-only refit이다.
Transformation averaging은 exact invariance를 수학적으로 보장하므로 component
deletion이 필수는 아니다. 다만 empirical benefit까지 주장하려면 no-averaging
condition을 supplement에 추가해야 한다.

새 실험을 추가하지 않을 경우 Introduction 29행처럼 `roles`를 검토한다고 쓰고,
각 component의 독립적인 성능 향상을 입증했다고 표현하지 않는 것이 안전하다.

## 90. [~] Relation-family별 결과의 보고 범위

**심각도: 사소**
**위치: Experiments, Metrics, 191행**

원문:

> The supplement reports per-family metrics and the family composition of the
> selected top-$K$ predictions.

Supplement의 manuscript table은 selected top-100 family slices를 보여준다. 이어지는
prose는 full machine-readable results에서 같은 방향이 다른 $K$에도 성립한다고
설명한다. 따라서 family-level evidence는 존재하지만, reader-visible table이 모든
$K$를 보여주는 것은 아니다.

권장 방안:

1. 현재 문장을 유지할 경우 supplement에서 machine-readable all-$K$ artifact의
   위치를 명시한다.
2. Main claim이 $K=50$ 중심이면 supplement에 $K=50$ family breakdown을 한 열
   추가한다.
3. 표를 늘리지 않으려면 `The supplement reports top-100 per-family metrics and
   all-$K$ machine-readable family slices.`처럼 범위를 정확히 쓴다.

## 91. [x] Predictor 비교의 공정성과 통계 문장

**심각도: 해당 없음**
**위치: Experiments, 172--249행**

세 predictor는 같은 scans, contexts, ground-truth denominator, family scope,
metrics를 사용한다. Compatibility parameters도 predictor별 refitting 없이 동일하게
적용된다. Predictor마다 source score의 의미와 candidate coverage는 다르므로 Table 1은
predictor 자체의 우열 비교가 아니라 각 Source ranking에 대한 re-ranking 비교로
읽어야 한다. 현재 Results도 이 범위를 지킨다.

$K=50$ 통계 문장은 supplement의 paired scan bootstrap과 일치한다.

- Open3DSG와 SGFN은 두 estimator 모두 Recall interval이 양수이고 Violation
  interval이 음수다.
- VL-SAT은 두 estimator의 Recall interval이 0을 포함하고 Violation interval이
  음수다.
- SGFN은 $K=5$에서 두 metric이 Source와 동일하다.

Main Table 1과 Figure 3은 $K\in\{5,10,20,50,100\}$를 사용한다. Table 2는
$K=50,100$, Table 3은 $K=50$이라고 header와 caption에서 명시하므로 K 범위 충돌은
없다. Metric의 formal definition도 Experimental Setup 한 곳에서만 제시된다.

## 92. [~] Figure와 Table caption의 자기완결성

**심각도: 사소**
**위치: Figure 1--3 및 Table 1--3 captions**

- Figure 1은 source, failure evidence, method variant, rank change를 설명한다.
- Figure 3은 두 metric, 다섯 $K$, 선호 방향, predictor별 axis 차이를 설명한다.
- Table 1은 target, metrics, units, Source와 ranking rules를 설명한다.
- Table 2는 Linear controls와 MLP full rows의 범위, metrics, units를 설명한다.
- Table 3은 metric, units, delta, measured와 decidable coverage를 설명한다.

Figure 2만 작은 개념 차이가 있다.

원문:

> RelCompat3D estimates transformation-consistent predicate--geometry
> compatibility

그림 내부에는 compatibility block이 있지만 transformation averaging block은 없다.
Caption은 method 전체로는 정확하다. Graphic 자체가 averaging을 보여준다고 오해하지
않도록 다음처럼 쓸 수 있다.

> RelCompat3D estimates predicate--geometry compatibility from predicate
> semantics and ordered-pair measurements. The Method then averages this score
> over the applicable relation-preserving transformations.

지면이 부족하면 현재 caption을 유지해도 claim 오류는 아니다.

## 93. [~] Discussion의 transfer evidence와 약한 지점

**심각도: 사소**
**위치: Discussion and Limitations, 327--329행**

Single-target scope, known-instance assumption, support/contact boundary,
alternative audit의 한계는 적절한 수준으로 공개된다. 불필요한 자기비판은 아니다.

다만 supplement에는 ReplicaSSG/FROSS transfer stress test가 존재하는데 main
Discussion은 다음처럼 쓴다.

원문:

> Broader claims require ... evaluation on additional datasets.

이 문장은 supplemental external test가 없는 것처럼 읽힐 수 있다.

권장 문장:

> A supplemental ReplicaSSG/FROSS stress test provides limited transfer
> evidence. Broader claims still require evaluation across additional datasets
> with independently defined reference labels and richer contact and pose
> evidence.

약한 지점은 Results에서 이미 정직하게 다룬다. SGFN의 $K=5$ tie와 작은 low-$K$
change, support/contact source-order preservation, predictor-dependent trade-off가
명시되어 있다. Discussion에서 모두 다시 반복할 필요는 없다.

## 94. [x] AAAI Ethical Statement 또는 broader-impact 요구

**심각도: 해당 없음**
**위치: Discussion and Limitations 이후**

로컬 AAAI 2027 Author Kit의
`paper/aaai/official/AnonymousSubmission2027.tex` 532행과 541--542행은
`Ethical Statement`를 optional, unnumbered section으로 규정한다. 따라서 mandatory
broader-impact section은 아니다.

현재 연구는 새 human study, 개인 데이터 수집, 직접 deployment claim을 포함하지
않는다. Generic한 ethics 문단을 채우기 위해 추가할 필요는 없다. 포함하기로 결정할
경우 제목은 `\section*{Ethical Statement}`여야 한다.

## 95. [~] Conclusion의 motivating problem 연결

**심각도: 사소**
**위치: Conclusion, 332행**

현재 Conclusion은 method scope와 point-estimate result를 정확히 재진술하고, 본문에
없는 새 주장이나 수치를 추가하지 않는다. Overclaiming도 없다. Conclusion에서
Introduction contribution을 짧게 다시 묶는 것은 정상적인 마무리다.

다만 첫 문장이 method summary로 바로 시작해 Introduction의 motivating failure와
연결이 약하다.

권장 문장:

> RelCompat3D addresses high-scoring predicates that conflict with
> reconstructed ordered-pair geometry by learning predicate--geometry
> compatibility separately from the source relation score and re-ranking
> candidates within applicable relation families.

Future work는 Discussion에서 이미 scope limitation과 연결되므로 Conclusion에 다시
넣지 않아도 된다.

## 96. [~] 용어 통일과 쉬운 영어

**심각도: 사소**
**위치: 원고 전체**

권장 canonical 표현은 다음과 같다.

| 개념 | 통일 표현 |
| --- | --- |
| source output | `source relation score` |
| geometry input | 최초 `predicate-independent geometric measurements of the ordered pair`, 이후 `ordered-pair measurements` |
| pair | 최초 `ordered subject--object pair`, 이후 `corresponding ordered pair` |
| retrieval metric | `exact-match Recall@$K$` |
| reliability metric | `verifier-derived Violation@$K$` |
| directional family | `vertical-order` |
| averaging operation | `transformation averaging` |
| retained candidates | `support/contact candidates` |
| swap control | `fixed-predicate swap` |

현재 교체가 필요한 원문:

> reconstructed ordered pair geometry

**위치: Related Work 56행과 Method 87행**

권장 교체:

> reconstructed ordered-pair geometry

현재 원문:

> proximity and vertical violations

**위치: Point- and Mesh-Based Consistency Audit, 321행**

권장 교체:

> proximity and vertical-order violations

현재 `transformation averaging`과 `Group averaging`은 같은 operation을 가리킨다.
145행 식 직후에는 다음처럼 연결하고 이후 `transformation averaging`을 유지하는
편이 쉽다.

> This finite-group average implements transformation averaging.

긴 물리적 line이 많지만 대부분 여러 문장이 한 LaTeX line에 배치된 결과다. 실제
sentence-level 호흡은 Introduction과 Results에서 대체로 짧다. 가장 긴 개념 문장은
Method 93행, 132행, 162--163행과 Audit 321--323행이다. 68번과 78번 수정 후 읽기
부담이 크게 줄어든다.

산문에서 소유격 형태, em dash, semicolon 남용은 발견되지 않았다. 수식의 column
separator와 주석 속 punctuation은 산문 남용에 해당하지 않는다.

# 섹션별 최종 체크

## Abstract

- 자기완결성: **부분 통과**. 3DSSG와 linked pair를 한 번 더 쉽게 설명하면 완결됨.
- 문제, 방법, 결과, 기여: **통과**.
- Introduction contribution 세 개와 대응: **통과**.
- Hedging과 claim 범위: **통과**.
- 문장당 정보량: **통과**. 60번 잔여 fragment는 삭제 필요.
- Citation과 undefined notation: **통과**. Abstract citation은 없고 불필요함.

## Introduction

- 핵심 기여와 차별점: **통과**.
- 세 contribution과 design 대응: **통과**.
- Method 전용 용어 설명: **통과**. Counterfactual과 transformation의 차이를
  27행에서 설명함.
- 문제, 한계, 해법 흐름: **통과**.
- Citation 존재 여부: **통과**.
- Hedging 일관성: **통과**.
- 남은 핵심 수정: 61번 collocation과 83번 control claim.

## Related Work

- 선행연구 citation 존재 여부: **통과**.
- 단순 나열을 넘는 구체적 차이: **통과**.
- Subsection 균형과 제목 정합성: **통과**.
- Introduction과 용어 일관성: **부분 통과**. 96번 hyphenation 보완.
- Subsection 간 불필요한 중복: **통과**.

## Method

- 수식 전개와 text 일치: **통과**.
- Figure 연결과 caption: **부분 통과**. Figure 2의 averaging 표현만 선택적 보완.
- Notation 일관성: **부분 통과**. 81번과 85번 수정 필요.
- Introduction의 design 대응: **통과**.
- 새 용어 정의: **부분 통과**. Transformation group 연결 보완.
- 재현 가능성: **부분 통과**. 87번 supplement pointer 복원 필요.
- 가정 공개: **부분 통과**. 86번 score range 확인 필요.

## Experiments

- Main result와 claim 연결: **통과**.
- Ablation과 design 대응: **부분 통과**. 89번 direct deletion 범위 확인.
- 세 predictor의 shared evaluation: **부분 통과**. 88번 coverage disclosure 필요.
- 통계 문장과 수치: **통과**.
- K 범위 일관성: **통과**.
- Family별 결과: **부분 통과**. Supplement table은 top-100 중심.
- Metric 정의 위치와 사용: **통과**.
- Failure와 weak point 논의: **통과**.
- Caption 자기완결성: **통과**.

## Discussion and Limitations

- Scope와 일관성: **통과**.
- 통계적 claim: **통과**. 새 수치를 주장하지 않음.
- 자기비판의 균형: **통과**.
- 실패와 약한 지점: **통과**. Results와 supplement에서 공개됨.
- External transfer와 문장 정합성: **부분 통과**.
- AAAI ethics requirement: **통과**. 별도 statement는 optional.

## Conclusion

- Contribution 재진술 수준: **통과**.
- 새 주장이나 수치: **없음**.
- Overclaiming: **없음**.
- Motivating problem과 연결: **부분 통과**.
- Future work: Discussion에 있어 중복 추가 불필요.

# 최신 수정 우선순위

1. **P0** Abstract 3행의 잔여 fragment를 삭제한다.
2. **P0** Method 141행의 `\mathcalf R`을 `\mathcal R`로 고친다.
3. **P1** Experiments 172행에 Open3DSG 533/548 candidate coverage와 empty-context
   처리를 명시한다.
4. **P1** Method 126행과 145행 사이에 $\tau_a$와 $H_a$의 관계를 정의한다.
5. **P1** Open3DSG source relation score의 observed range를 확인해 product utility의
   비음수 전제를 검증한다.
6. **P1** Introduction 29행의 `test the effects`를 `examine the roles`로 낮춘다.
7. **P1** Method 132행의 augmentation 반복과 166행의 문법을 고친다.
8. **P1** Audit 321행의 `lables`, negated list, `vertical-order` 용어를 고친다.
9. **P2** Abstract에서 3DSSG와 linked pair를 자기완결적으로 설명한다.
10. **P2** Supplement pointer와 external transfer 언급을 final layout에 맞춰
    복원한다.
11. **P2** Pairwise-loss removal과 no-averaging ablation을 추가할지 결정한다. 추가하지
    않으면 component-level causal wording을 사용하지 않는다.
12. **P2** Conclusion 첫 문장을 motivating failure와 연결한다.

현재 scientific result 자체를 뒤집는 수치 불일치는 발견되지 않았다. 제출 전
핵심은 새 실험을 무조건 늘리는 것이 아니라 protocol disclosure, notation 연결,
directly supported claim의 범위를 정확히 맞추는 것이다.
