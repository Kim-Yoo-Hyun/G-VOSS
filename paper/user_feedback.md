# RelCompat3D `user_v2.tex` 재검토

검토일: 2026-07-23 KST
대상: `paper/user_v2.tex`
범위: Abstract부터 Conclusion까지 338행
인용 검토: 각 섹션에서 처음 등장하는 연구명과 줄임말에 인용이 존재하는지만 확인
인용 표기법과 문헌의 적절성: 검토 제외
PDF 빌드: 수행하지 않음

## 상태 표기

- `[x] 해결`: 현재 원고에서 해결됨
- `[~] 부분 해결`: 핵심은 반영됐으나 작은 수정이 남음
- `[ ] 미해결`: 제출 전에 수정 필요하거나 사용자 선택이 남음
- `[>] 마무리 단계`: final pass에서 처리하기로 확정

심각도는 다음처럼 구분한다.

- **치명적**: 사실관계, claim, 수학 전제, 표 설명, reference 무결성에 영향을 주는 문제
- **사소**: 문법, 용어, 문장 길이, 중복, caption 완결성 문제

## 총평

`user_v2.tex`는 연구 task, method, experiment, claim boundary가 전반적으로 정합하다.
두 compatibility estimator 모두 fixed candidates를 사용하고, source relation score를
compatibility estimation에서 제외하며, family-aware re-ranking 단계에서만 결합한다.
Table 1의 모든 predictor와 $K$ 설정에서도 두 variant의 point estimate가 Source보다
낮은 Recall 또는 높은 Violation을 보이지 않는다는 원고의 범위가 수치와 맞는다.

과장된 SOTA, dataset-level generalization, 모든 relation family의 개선 주장은 없다.
Transformation averaging도 독립 novelty로 부풀리지 않고 framework의 consistency
mechanism으로 사용한다. 이 부분은 원리적으로 자연스럽다.

현재 제출 전 우선 수정할 항목은 다음과 같다.

1. Introduction 27행의 문법 오류를 고친다.
2. Related Work 51행의 관사를 보완한다.
3. Table 3의 `Change`와 `Coverage` header를 metric 의미가 드러나게 바꾼다.
4. Main Table 3에서 제외한 CI를 Results가 언급할 때 supplement 결과임을 밝힌다.
5. `ordered object pair`, `ordered pair`, `ordered-pair`의 용어 계약을 통일한다.
6. Table 1과 Table 2 caption에 percentage와 shared-target scope를 보완한다.
7. Conclusion에서 섹션 첫 3DSSG 등장에 인용이 존재하도록 한다.

Figure 1, Figure 2, Figure 3, Table 1, Table 2, Table 3은 모두 본문에서 최소 한 번
명시적으로 참조된다. `user_v1.tex`에서 누락됐던 Figure 3 definition도 복원됐다.

# 기존 번호별 수정 TODO 갱신

## P0: 사실관계와 reference 무결성

1. [x] **Abstract, 2--3행**
   Ordered-pair identity와 source-score exclusion이 정확히 표현됐다.

2. [x] **Abstract, 2--3행**
   `predicate--geometry`와 `predictor--$K$ settings` 표기가 통일됐다.

3. [x] **Abstract, 3행**
   `SceneGraphFusion (SGFN)`이 첫 등장에 풀어 쓰였다.

4. [x] **Abstract, 3행**
   모든 공개 predictor와 $K$ 설정에 대한 point-estimate claim은 Table 1과 맞는다.

5. [x] **Introduction, Figure 1 caption, 17--18행**
   Point-cloud evidence와 RelCompat3D-Linear의 rank 6에서 425 변화가 명시됐다.

6. [x] **Introduction, Evaluation paragraph, 31행**
   중복 all-$K$ 문장이 삭제됐고, 한 번의 범위 한정된 결과 문장만 남았다.

7. [x] **Introduction, Contribution 2, 36행**
   Ordered-pair identity, source-score exclusion, linked counterfactual ordering,
   transformation consistency가 하나의 method design으로 묶였다.

8. [x] **Related Work, 44, 46, 49, 51, 54--56행**
   각 subsection은 관련 연구와 RelCompat3D의 공통점과 차이를 설명한다.

9. [ ] **Related Work, Geometry-aware Relation Evidence, 51행, 사소**
   다음 원문에는 관사가 빠졌다.

   > For fixed predictions from 2D scene graph generator, Neau et al. ...

   다음처럼 수정한다.

   > For fixed predictions from a 2D scene graph generator, Neau et al. ...

10. [x] **Related Work, Reliability Evaluation and Calibration, 53--56행**
    Calibration, uncertainty, selective prediction과 compatibility assessment의
    차이가 명확하다.

11. [x] **Figure 2 caption, 66--69행**
    Transformation averaging의 상세 설명은 Method에 두고 caption은 panel의 역할과
    score flow만 설명한다. Rank 19에서 178의 변화가 RelCompat3D-Linear 결과라는
    attribution도 들어갔다.

12. [x] **Figure 2 caption과 Method, 66--69, 85--87, 155--166행**
    Caption에 support/contact boundary를 반복하지 않는다. Scope는 Method에 충분히
    설명돼 있다.

13. [x] **Method와 Experimental Setup, 85--87, 176행**
    Evaluation scope와 re-ranking scope가 분리됐다.

14. [>] **Method, Problem Formulation과 Relation-Consistent Compatibility, 94, 98,
    130--131, 143, 153, 167, 170행**
    Supplement pointer와 주석은 final pass에서 복원하거나 정리한다. 현재는 사용자
    결정에 따라 상태를 유지한다.

15. [x] **Method와 Experimental Setup, 85--87, 179행**
    Support/contact head는 `Product (all families)` comparison에서 사용된다는 점이
    Experimental Setup에 나온다. Method에서 다시 길게 설명할 필요는 없다.

16. [x] **Method, Relation-Consistent Compatibility, 102행**
    OBB-derived model input과 point-level support/contact verifier evidence가 분리됐다.

17. [x] **Method, Relation-Consistent Compatibility, 127--152행**
    Transformation relation은 transformation-averaged score에 대해 정의된다.

18. [x] **Method, Relation-Consistent Compatibility, 133--152행**
    Pairwise objective는 보장이 아니라 linked positive가 더 높은 score를 갖도록
    유도하는 항으로 한정됐다.

19. [x] **Method, Family-Aware Re-ranking, 155--162행**
    양수 source score를 전제하던 log-score 해석이 삭제됐다. Piecewise ranking score만
    남아 모든 predictor score type과 정합하다.

20. [x] **Method, Family-Aware Re-ranking, 165--166행**
    Source position, family list, next unused candidate, support/contact subsequence가
    순서대로 설명된다. 본문에 있던 prefix maximization claim도 제거됐다.

21. [x] **Results, Figure 3, 241, 247--256행**
    `fig:tradeoff` environment와 label이 복원됐고 본문에서 참조된다.

22. [ ] **Discussion and Limitations, 334행, 사용자 선택**
    다음 문장은 optional future-work 항목이다.

    > Broader claims require independently defined reference labels, richer
    > contact and pose evidence, and evaluation on additional datasets.

    유지해도 claim boundary와 자연스럽게 연결되고, 삭제해도 현재 limitation의 사실성이
    훼손되지 않는다. 사용자의 요청에 따라 미해결 상태로 둔다.

23. [x] **Conclusion, 338행**
    `vertical-order candidates`와 shared 3DSSG validation target이 정확히 쓰였다.

24. [~] **Table 3, 304--320행, 사소**
    Main table의 CI는 교수 피드백에 따라 제외됐고 caption에서도 CI 설명이 삭제됐다.
    이 부분은 해결됐다. CI는 임의의 데이터 range가 아니라 반복 표본추출에 따른
    불확실성 구간이다. 다만 표에서는 lower와 upper bound로 보이기 때문에 넓은 의미의
    구간형 범위로 읽힐 수 있다. 현재 결정대로 main table에 복원하지 않는다.

    남은 문제는 header의 자립성이다.

    > Predictor & Source & Ours & Change & Coverage

    `Change`는 이해 가능하지만 어떤 metric의 변화인지 header만으로 알 수 없다.
    `Coverage` 셀은 measured와 decidable의 두 값을 `/`로 묶는데, header에 그 순서가
    나타나지 않는다. 가장 권장하는 header는 다음과 같다.

    > Predictor & Source & Linear & $\Delta$V (pp) & Coverage (M/D)

    공간이 허용되면 `Coverage`를 `Measured`와 `Decidable` 두 열로 나누는 구성이 더
    명확하다. `Ours`보다 `Linear`가 실제 variant를 직접 나타낸다.

## P1: 독자 이해, 재현성, caption 완결성

25. [x] **Introduction과 Method, 27, 93--97행**
    Counterfactual negative와 relation-preserving transformation의 역할이 구분된다.

26. [x] **Method, Problem Formulation, 78--87행**
    Candidate fields, identity, semantics와 family scope가 여러 문단으로 분리됐다.

27. [x] **Method, Nonlinear Estimator, 117--125행**
    Skip connection이 predicate indicator에서 output logit으로 가는 직접 linear path임을
    설명한다.

28. [x] **Method와 Metrics, 89--162, 183--195행**
    Core method equation과 두 metric equation은 각각 별도 정의 역할이 있다. 불필요했던
    log interpretation과 prefix optimization claim은 삭제됐다.

29. [x] **Point- and Mesh-Based Consistency Audit, 322--327행**
    Vertex-based measurement, triangle-sample measurement, agreement rule, primary
    metric과의 차이가 설명된다.

30. [x] **Experimental Setup, Metrics, 183--195행**
    Recall, Violation, uncertain denominator가 main text에 남고 secondary metrics가
    supplement로 이동했다.

31. [x] **Results, Figure 3, 241, 247--256행**
    Figure 3 caption은 Source, Linear, MLP, 다섯 $K$ 값, 선호 방향, predictor별 axis
    range를 설명한다.

32. [~] **Table 1 caption, 235행, 사소**
    Shared 3DSSG target, metric, Source, ranking rule이 정의돼 있다. 수치 단위를 더
    명확히 하려면 다음 문장을 추가한다.

    > All entries are percentages.

33. [~] **Table 2 caption, 295행, 사소**
    Linear control rows와 MLP full variant의 범위는 명확하다. Caption이 독립적으로
    읽히게 하려면 첫 문장에 dataset scope와 단위를 보완한다.

    > Ablations and counterfactual controls on the shared 3DSSG validation target.
    > All entries are percentages.

34. [~] **Table 3 caption과 본문, 318, 325--327행, 사소**
    Metric construction과 Linear variant는 설명된다. Caption에 shared-target scope를
    추가하고, header는 24번 권장처럼 구체화한다. Primary Violation과 직접 비교할 수
    없다는 설명은 본문에 있으므로 caption에서 다시 길게 반복하지 않아도 된다.

35. [ ] **Introduction, Related Work, Method, Results, 22, 24, 27, 29, 46, 51,
    81, 83, 87, 300행, 사소**
    `ordered subject--object pair`, `ordered object pair`, `ordered pair`,
    `ordered-pair`가 혼용된다. 다음 계약으로 통일한다.

    - 처음 정의할 때: `ordered subject--object pair`
    - 이후 명사형: `ordered pair`
    - 복합 수식형: `ordered-pair identity`, `ordered-pair geometry`

    `ordered object pair`는 모두 `ordered pair`로 바꾸는 것이 가장 자연스럽다.

36. [x] **Figure 2 caption과 Method, 68--69, 75행**
    `source relation score`로 통일됐다.

37. [x] **전체 원고**
    산문에서는 `Recall@$K$`, `Violation@$K$`를 쓰고 equation operator는
    `Recall@K`, `Violation@K`를 쓴다. 역할에 따른 차이로 일관적이다.

38. [x] **Method와 Experiments**
    `vertical-order`는 수식형, `vertical order`는 명사형으로 구분된다.

39. [x] **전체 원고**
    영어 소유격 형태는 검출되지 않았다.

40. [x] **전체 원고**
    산문에 em dash와 semicolon이 검출되지 않았다. Equation 구분자와 주석은 산문
    punctuation 검토에서 제외했다.

41. [x] **Method, Linear Estimator, 114행**
    `a constant input`의 중복 공백이 제거됐다.

42. [x] **Method, Problem Formulation, 95행**
    Vertical augmentation이 endpoint를 바꾸고 predicate를 inverse로 교체한다고
    명확히 표현됐다.

43. [ ] **Introduction, Method overview, 27행, 치명적 문법 오류**
    다음 원문은 주어가 중복되어 문법적으로 성립하지 않는다.

    > This preserves ordered-pair identity prevents geometry from another object
    > pair from being substituted for the candidate evidence.

    다음처럼 고친다.

    > Preserving ordered-pair identity ensures that compatibility is computed
    > from the geometry of the corresponding pair.

44. [x] **Related Work, Geometry-aware Relation Evidence, 51행**
    Continuous compatibility와 transformation-aware evaluation의 차이가 두 문장으로
    나뉘었다. 관사 문제는 9번에만 남는다.

45. [x] **Method, Problem Formulation과 Family-Aware Re-ranking, 87, 165--166행**
    Support/contact scope와 ranking procedure가 짧은 문장으로 나뉘었다.

46. [~] **Results, Recall--Violation Results와 Ablations, 241, 245, 300행, 사소**
    Results의 문장 구조는 이전보다 좋아졌다. 다음 두 범위 설명은 caption 또는 Method와
    반복된다.

    > Both proposed variants, RankAvg, and RRF use the same family-aware ranking
    > procedure and therefore preserve the source relation-family sequence.

    > Table~\ref{tab:ablations} shows structural controls for
    > RelCompat3D-Linear and includes the RelCompat3D-MLP operating point at
    > $K=50$ and $K=100$.

    첫 문장은 Table 1 caption이 이미 같은 내용을 설명하므로 삭제할 수 있다. 두 번째
    문장은 Table 2 caption과 겹치므로 다음처럼 결과 해석으로 바로 시작할 수 있다.

    > For RelCompat3D-Linear, wrong-pair and shuffled geometry reduce Recall and
    > increase Violation for every predictor at both reported $K$ values.

47. [>] **Figure와 layout format**
    Figure asset path, `trim`, `clip`, bold caption lead-in, page count, overflow,
    float placement는 아직 해결하지 않은 상태로 유지한다. Final layout pass에서 검증한다.

# 추가 검토 TODO

## 48. [ ] Section-first acronym citation 존재 여부

**심각도: 사소**

- **Introduction, 31행**: SceneGraphFusion benchmark model과 SGFN의 첫 등장 문장에
  인용이 존재한다.
- **Related Work, 44, 46, 54행**: 3DSSG, VLM, SCR-SSG, PUF의 첫 등장 문장에 인용이
  존재한다.
- **Method, 79행**: VL-SAT, SGFN, Open3DSG의 첫 등장 문장에 인용이 존재한다.
- **Experiments, 176, 179행**: Open3DSG, VL-SAT, SGFN, 3DSSG, 3RScan, RRF의 첫
  등장 문장에 인용이 존재한다.
- **Discussion and Limitations, 332행**: 3DSSG의 첫 등장 문장에 인용이 존재한다.
- **Conclusion, 338행**: 3DSSG가 이 섹션에서 처음 등장하지만 인용이 없다.

사용자가 정한 섹션별 first-use 규칙을 적용하려면 Conclusion을 다음처럼 고친다.

> Across three predictors on one shared 3DSSG validation
> target~\cite{wald2020learning}, ...

`OBB`, `ReLU`, `BCE`는 dataset 또는 연구명 줄임말이 아니라 일반 기술 용어다. 별도
인용보다 첫 등장에 full term을 적는 것이 중요하다. Method 102행과 Audit 323행의
`OBB`는 `oriented bounding box (OBB)`로 한 번씩 풀어 쓰는 것을 권장한다.

## 49. [ ] Good English와 독자 친화성

**심각도: 사소, 43번 문법 오류만 높은 우선순위**

### Abstract, 2--3행

다음 두 문장은 지나치게 끊겨 보인다.

> We formulate predicate--geometry compatibility for fixed relation predictions
> and introduce RelCompat3D, a re-ranking framework.
> RelCompat3D preserves ...

다음처럼 한 문장으로 연결해도 길지 않다.

> We formulate predicate--geometry compatibility for fixed relation predictions
> and introduce RelCompat3D, a re-ranking framework that preserves the
> ordered-pair identity of each candidate.

### Introduction, 24행

다음 표현은 의미는 맞지만 collocation이 다소 무겁다.

> This makes the problem a reliability issue, not only a 3DSSG implementation
> detail ...

다음처럼 바꾸면 더 직접적이다.

> The resulting mismatch is a reliability problem rather than only an
> implementation issue in 3D scene graph prediction.

### Method, Relation-Consistent Compatibility, 102행

한 문단에서 geometry features, contact evidence, standardization, two estimators를
연속 설명한다. 다음 위치에서 문단을 나누면 읽기 쉽다.

1. Geometry vector와 point-level evidence를 설명한 뒤 문단을 끝낸다.
2. Standardization과 two estimator setup을 새 문단으로 시작한다.

### Results, Recall--Violation Results, 241행

다음 표현은 `better trade-off`가 무엇을 뜻하는지 독자가 다시 Table 1에서 확인해야 한다.

> yields a better $K=50$ point estimate Recall--Violation trade-off

다음처럼 관찰값을 직접 쓴다.

> At $K=50$, both variants preserve or raise Recall and reduce Violation relative
> to Source for all three predictors.

같은 문단의 다음 표현에는 관사가 필요하다.

> Source baseline ranks geometrically inconsistent relation candidates ...

다음처럼 수정한다.

> The Source baseline ranks geometrically inconsistent relation candidates ...

### Point- and Mesh-Based Consistency Audit, 326--327행

다음 구조는 길고 어색하다.

> with the point- and mesh-based changes having the same direction throughout
> except for SGFN at $K=5$, which is the only tie

다음처럼 두 문장으로 나눈다.

> Both measurements show the same direction of change at every reported $K$.
> The only exception is a tie for SGFN at $K=5$.

## 50. [~] 문장 길이

**심각도: 사소**

원고 전체가 한 문장을 과도하게 길게 이어 쓰는 형태는 아니다. 대부분 15--30 words
범위다. 우선 분할할 문장은 다음 세 곳이다.

1. **Introduction, 27행**: design rationale가 여러 문장으로 나뉘었지만 문법 오류가
   남았다. 43번 문장으로 수정한다.
2. **Method, Relation-Consistent Compatibility, 102행**: feature, evidence,
   standardization, estimator setup을 두 문단으로 나눈다.
3. **Results, Point- and Mesh-Based Consistency Audit, 326--327행**: supplement 범위와
   all-$K$ observation을 두 문장으로 나눈다.

## 51. [~] 중복 표현

**심각도: 사소**

- Support/contact source order는 Abstract, Introduction, Method에 반복되지만 method
  scope의 핵심 경계이므로 유지할 수 있다.
- Figure 2 caption과 Method의 source-score separation 반복은 figure가 독립적으로
  읽히기 위해 필요하다.
- Results 245행의 ranking procedure 설명은 Table 1 caption과 중복되므로 삭제할 수 있다.
- Ablation 300행의 첫 문장은 Table 2 caption과 중복된다. 46번처럼 바로 control 결과로
  시작하면 된다.
- Table 3 caption과 Audit 본문의 agreement rule 반복은 caption 자립성을 위해 허용할
  수 있다.

## 52. [x] Claim의 명확성과 과장 여부

**심각도: 문제 없음**

- Abstract와 Conclusion은 point estimates에 한정한다.
- Shared 3DSSG target에서 세 predictor를 비교했다고 쓰며 dataset-level generalization을
  주장하지 않는다.
- Source보다 낮지 않은 Recall과 높지 않은 Violation이라는 표현은 Table 1의 모든 공개
  predictor와 $K$ 설정에 맞는다.
- Linear와 MLP 중 하나가 보편적으로 우수하다고 쓰지 않는다.
- Point- and mesh-based audit은 independent ground truth가 아니라 alternative geometric
  measurement로 한정한다.
- Product all families의 aggregate 결과를 primary method의 우월성으로 사용하지 않는다.

`better trade-off`만 49번처럼 직접 관찰값으로 바꾸면 claim이 더 명확해진다.

## 53. [~] 공개하지 않아도 되는 내용

**심각도: 사소**

다음 내용은 숨기면 reviewer가 더 크게 문제 삼을 수 있으므로 유지한다.

- Single-target scope
- OBB-derived inputs와 primary verifier의 partial overlap
- Point/mesh audit이 independent ground truth가 아니라는 경계
- Support/contact를 primary method가 re-rank하지 않는 범위
- Predictor-specific refitting과 normalization을 하지 않았다는 protocol

Discussion 332행의 다음 절은 fixed-prediction framing과 겹친다.

> it does not generate complete graphs

공간이 부족하면 삭제할 수 있다. 다음 절은 실제 method scope이므로 유지하되 표현을
정확히 바꾼다.

> it does not re-rank contact-dependent relations

22번 future-work 문장은 선택 사항으로 미해결 상태를 유지한다.

## 54. [x] 원리적 타당성

**심각도: 문제 없음**

- Source-score exclusion은 source score를 compatibility target으로 다시 복제하는 경로를
  막는다.
- Ordered-pair identity는 다른 pair의 geometry가 candidate evidence로 섞이는 것을
  막는다.
- Transformation averaging은 정의된 finite transformation set에서 exact invariance를
  만든다.
- Family-aware re-ranking은 family composition과 support/contact subsequence를 보존하는
  constrained ranking으로 설명된다.
- Linear와 MLP의 서로 다른 operating point는 특정 estimator form 하나에만 효과가
  의존하지 않는다는 framework-level evidence로 사용된다.

억지로 claim에 맞춘 별도 proposition이나 자명한 성질의 과도한 novelty 주장은 없다.

## 55. [x] Figure와 Table 본문 참조

**심각도: 문제 없음**

| 항목 | Label | 본문 최초 참조 |
| --- | --- | --- |
| Figure 1 | `fig:teaser` | Introduction 22행 |
| Figure 2 | `fig:overall_framework` | Method 75행 |
| Figure 3 | `fig:tradeoff` | Results 241행 |
| Table 1 | `tab:main-results` | Results 241행 |
| Table 2 | `tab:ablations` | Ablations 300행 |
| Table 3 | `tab:surface-audit` | Audit 325행 |

모든 Figure와 Table이 본문에서 최소 한 번 호출된다.

## 56. [~] Figure와 Table caption checklist

**심각도: 사소**

### Figure 1, Introduction 10--20행

목적, source predictor, geometric contradiction, rank 변화가 모두 설명된다. Caption만
읽어도 failure case의 역할을 이해할 수 있다.

### Figure 2, 59--71행

Panel (a)는 pair geometry와 source prediction을 설명한다. Panel (b)는 compatibility
estimation, source-score combination, within-family re-ranking의 흐름을 설명한다.
Transformation averaging과 support/contact boundary는 Method에 맡기는 현재 구성이
적절하다.

### Figure 3, 247--256행

Metric, method, $K$ grid, 선호 방향, axis 차이가 설명된다. 실험 setting을 caption만으로
알 수 있게 첫 문장에 다음 구를 추가할 수 있다.

> on the shared 3DSSG validation target

### Table 1, 197--237행

Predictor row, ranking-rule row, $K$ column, R/V metric, Source가 명시된다. `All entries
are percentages.`만 추가하면 충분하다.

### Table 2, 258--297행

Predictor와 condition row, R/V와 $K$ column, Linear control scope, MLP comparison scope가
명시된다. Shared target와 percentage 단위를 첫 문장에 보완한다.

### Table 3, 304--320행

Predictor row와 Source/Linear comparison은 이해할 수 있다. `Change`와 `Coverage`는
24번처럼 metric-specific header로 바꾸는 것이 좋다.

## 57. [x] Contribution 2의 적합성

**심각도: 문제 없음**

Contribution 2는 단순히 compatibility head 하나를 학습했다는 주장이 아니다. 다음
요소를 하나의 design으로 묶는다.

1. Ordered-pair identity 보존
2. Source relation score 제외
3. Linked positive--counterfactual ordering
4. Applicable endpoint/predicate transformation consistency

각 요소는 failure cause와 직접 연결되고 ablation 또는 control로 검증된다. 따라서
method contribution으로 유지할 수 있다. 다만 `exact consistency`는 정의된
transformation에만 해당하므로 현재처럼 `applicable` 범위를 함께 써야 한다.

## 58. [~] `Change`와 `Coverage`의 top-tier 사용 관례

**심각도: 사소**

확인 결과는 다음과 같다.

- `Coverage`와 축약형 `Cov`는 selective prediction과 conformal prediction에서 널리
  쓰이는 metric header다. CVPR 2025의 conformal scene graph 논문은 `Cov`, `CovGap`,
  `AvgSize`를 별도 열로 사용한다.
- CVPR 2024의 continual change captioning 논문도 `Coverage`를 metric header로
  사용한다.
- 상대 변화는 top-tier table에서 괄호 안 improvement, arrow, 또는 $\Delta$로 자주
  표시된다. Bare `Change`도 이해는 되지만 어떤 metric의 변화인지 header만으로
  결정하기 어렵다.

따라서 현재 Table 3에는 `Change`보다 `$\Delta$V (pp)`가 더 정확하다. `Coverage`는
사용해도 되지만 두 종류를 한 cell에 넣으므로 `Coverage (M/D)`로 쓰거나 두 열로
분리한다.

확인한 accepted-paper 예시:

- [CVPR 2025, Conformal Prediction and MLLM aided Uncertainty Quantification in
  Scene Graph Generation](https://openaccess.thecvf.com/content/CVPR2025/papers/Nag_Conformal_Prediction_and_MLLM_aided_Uncertainty_Quantification_in_Scene_Graph_CVPR_2025_paper.pdf)
- [CVPR 2024, The STVchrono Dataset](https://openaccess.thecvf.com/content/CVPR2024/papers/Sun_The_STVchrono_Dataset_Towards_Continuous_Change_Recognition_in_Time_CVPR_2024_paper.pdf)
- [ICCV 2025, Adversarial Robust Memory-Based Continual Learner](https://www.openaccess.thecvf.com/content/ICCV2025/papers/Mi_Adversarial_Robust_Memory-Based_Continual_Learner_ICCV_2025_paper.pdf)

## 59. [~] Main table에서 제외한 CI와 본문 claim

**심각도: 사소**

Table 3에서 CI를 제외한 결정은 유지한다. Supplement에는 Linear와 MLP의 paired
scan-level intervals가 실제로 존재하므로 Audit 326행의 통계적 문장을 삭제할 필요는
없다. 다만 현재 문장은 Table 3이 interval을 보여 주는 것처럼 읽힐 수 있다.

원문:

> It decreases for all three predictors, with paired 95\% intervals below zero.

권장:

> It decreases for all three predictors. The paired intervals reported in the
> supplement are below zero.

이렇게 하면 main table은 point difference만 보여 주고, interval evidence는 supplement가
소유한다는 경계가 명확해진다.

# 섹션별 최종 판단

## Abstract, 1--4행

문제, task, identity, score separation, two estimators, transformation averaging,
re-ranking scope, evaluation, point-estimate result, alternative audit이 모두 들어 있다.
Claim은 정확하다. 2--3행의 짧게 끊긴 두 문장만 49번처럼 연결하면 더 자연스럽다.

## Introduction, 7--38행

Problem, prior gap, design necessity, evaluation, contributions의 흐름은 자연스럽다.
Contribution 2도 method contribution으로 충분하다. 27행의 문법 오류와 ordered-pair
terminology를 우선 고쳐야 한다.

## Related Work, 41--56행

각 subsection은 선행연구의 공통점과 차이를 설명한다. Reliability와 calibration의
task boundary도 정확하다. 51행의 article만 필수 수정이다.

## Method, 73--170행

Candidate identity, source-score separation, Linear와 MLP, counterfactual construction,
transformation averaging, ranking score, family-sequence preservation이 구현과 맞게
정의된다. 핵심 알고리즘은 그림 없이도 재구성할 수 있다. OBB full term, 102행 문단
분리, final supplement pointer만 남는다.

## Experimental Setup, 173--195행

Predictor, shared target, split, baseline, fitting boundary, metric denominator가 충분히
설명된다. Pair bootstrap도 방법과 목적이 명시돼 재현 가능하다. 인용 존재 여부도
사용자 규칙을 만족한다.

## Table 1과 Recall--Violation Results, 197--256행

Table 1 수치, Figure 3 trajectory, point-estimate claim이 정합하다. K=50 interval
interpretation은 supplement 결과와도 맞는다. `better trade-off`를 직접 관찰값으로
바꾸고 Table 1에 percentage 단위를 추가하면 더 명확하다.

## Table 2와 Ablations, 258--302행

Linear controls와 MLP full operating point의 범위가 명확하다. Wrong pair, shuffled
geometry, signed vertical controls, distance-only, compatibility-only 해석은 수치와
맞는다. Caption과 본문 첫 문장의 scope 반복만 줄일 수 있다.

## Table 3과 Point- and Mesh-Based Consistency Audit, 304--327행

Main table에서 CI를 제외한 결정은 적용됐다. Alternative measurement의 구성과 primary
Violation과의 차이도 설명된다. 남은 개선은 `$\Delta$V (pp)`, `Coverage (M/D)` header,
supplement interval attribution, 327행 문장 분리다.

## Discussion and Limitations, 330--334행

Single-target scope와 alternative audit이 independent ground truth가 아니라는 경계는
필요하다. Complete-graph 문구는 fixed-prediction task와 중복되어 삭제할 수 있다.
22번 future-work 문장은 사용자 선택을 위해 미해결로 둔다.

## Conclusion, 337--338행

Method scope, shared target, point-estimate claim이 정확하고 간결하다. 사용자 규칙을
엄격히 적용하면 3DSSG 첫 등장에 인용을 추가한다.

# 최종 수정 우선순위

1. **Introduction, 27행**의 문법 오류를 고친다.
2. **Related Work, 51행**에 article을 추가한다.
3. **Table 3, 310행**을 `$\Delta$V (pp)`와 `Coverage (M/D)`로 바꾼다.
4. **Audit, 326행**에서 interval이 supplement 결과임을 밝힌다.
5. **전체 원고**의 ordered-pair terminology를 통일한다.
6. **Table 1과 Table 2 caption**에 percentage와 shared-target scope를 보완한다.
7. **Results, 241행**의 vague trade-off 표현을 직접 관찰값으로 바꾼다.
8. **Conclusion, 338행**의 3DSSG 첫 등장에 인용을 추가한다.
9. **Discussion, 334행**의 future-work 문장은 사용자 선택 상태로 유지한다.
10. Figure path, caption style, page layout, overflow는 final pass에서 처리한다.

현재 원고에는 scientific claim을 무너뜨리는 새 문제는 없다. 남은 핵심 수정은 문법,
Table 3 header, supplement interval attribution, 용어 통일, caption 자립성이다.
