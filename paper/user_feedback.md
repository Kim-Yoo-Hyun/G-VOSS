# RelCompat3D 사용자 원고 검토

> Reviewer-style transcript review · 2026-07-21 · PDF로 빌드하지 않은 검토 문서

# 검토 범위와 총평

검토 대상은 `paper/user.tex`에 조립한 사용자의 Abstract부터
Conclusion까지의 원고, Figure 1--3, Table 1--3이다. 실제 제출 원고인
`paper/aaai/` 아래 파일은 변경하지 않았다. PDF도 빌드하지 않았다.

현재 원고의 중심 논리는 대체로 정합하다.

1. 고득점 relation score가 같은 ordered pair의 predicate--geometry
    compatibility를 직접 나타내지는 않는다는 failure를 정의한다.
2. predictor score를 compatibility input에서 분리하고, pair identity와
    relation-preserving transformation을 보존하는 compatibility estimator를
    학습한다.
3. proximity와 vertical-order만 family 내부에서 다시 정렬하고,
    support/contact는 source order로 유지한다.
4. exact-match Recall과 verifier-derived Violation을 함께 보고하고,
    point/mesh audit와 controls로 construct dependence를 점검한다.

따라서 task, method, main evidence의 큰 방향은 서로 맞는다. 다만 제출 전에 반드시
고쳐야 할 문제가 있다. 가장 큰 문제는 (i) Abstract의 사실관계 오류, (ii) SGFN
$K=5$ tie를 ``lower'' 또는 ``decreases''로 쓴 결과 과장, (iii) Figure caption과
실제 Figure의 불일치, (iv) Table 3 coverage의 모호성, (v) AAAI caption/figure
형식 위반이다. 독자가 이해하기 어려운 부분은 주로 Method의 첫 문단, counterfactual
설명, MLP 설명, family-aware re-ranking 절차, 그리고 Point/mesh audit에 집중되어
있다.

## 심각도 기준

- **[치명적]** 사실관계, claim, method scope, metric 해석, 또는 AAAI 형식 준수에
    직접 영향을 주어 제출 전 수정이 필요한 항목이다.
- **[사소]** 핵심 결론을 바꾸지는 않지만 문법, collocation, 가독성, 용어
    통일성을 떨어뜨리는 항목이다.

# 최우선 수정 목록

| 심각도 | 위치 | 문제와 조치  |
| --- | --- | --- |
| **[치명적]** | Abstract | ``preserves ordered-pair measurements and the relation score''는 실제 factor separation을 잘못 설명한다. ordered-pair *identity*를 보존하고, $T/G$로 compatibility를 추정하며, $Z$는 re-ranking에서만 결합한다고 고쳐야 한다.  |
| **[치명적]** | Introduction/Conclusion | ``improve'' 및 ``lower ... at every $K$''는 SGFN $K=5$ tie와 모순된다. ``improve or tie'', 또는 ``no worse point estimates''로 고쳐야 한다.  |
| **[치명적]** | Results | ``SGFN is tied at $K=$''는 미완성 표기이며 $K=5$로 고쳐야 한다. 같은 문장의 ``Violation ... decreases for every predictor''도 ``decreases or ties''가 정확하다.  |
| **[치명적]** | Figure 1 | 실제 그림은 strict elevation projection이 아니라 reconstructed point-cloud view이며, 6에서 425로의 이동은 Linear variant 결과다. caption과 그림 내부의 ``Relcompat3D'' 표기를 수정해야 한다.  |
| **[치명적]** | Figure 2 | 그림 내부에는 transformation averaging이 나타나지 않는데 caption은 transformation-consistent compatibility를 말한다. 최소한 caption에서 averaging과 Linear rank example을 명시하고, primary re-ranking scope도 한 문장으로 한정해야 한다.  |
| **[치명적]** | Experiments | support/contact까지 포함한 scope를 ``can be re-ranked''로 설명한다. 실제로는 ``can be assessed''이며, re-ranking은 proximity/vertical-order에 한정된다.  |
| **[치명적]** | Table 3 | ``Ours''와 ``Cov.''가 모호하다. Ours를 Linear로 바꾸고, coverage가 Linear의 measured/decidable coverage임을 명시해야 한다. Table 1의 Violation과 직접 비교할 수 없는 별도 construct라는 문장도 caption에 필요하다.  |
| **[치명적]** | AAAI format | Figure/Table caption의 bold lead-in, Figure 3의 `trim`/`clip`, 그리고 현재 root Figure PDF의 Identity-H fonts는 AAAI-27 규정과 충돌한다.  |
| **[치명적]** | Contribution 2 | transformation averaging 자체는 표준적인 group averaging 성질이다. 독립 novelty처럼 쓰지 말고 source-score exclusion, identity-preserving linked counterfactual supervision, exact transformation consistency의 결합으로 claim해야 한다.  |

# 받은 피드백에 대한 판단

## 처음 읽는 독자에게 불친절한 부분

이 피드백은 맞다. 특히 다음 다섯 부분에서 독자가 정의를 뒤늦게 조합해야 한다.

1. Introduction에서 ``linked positive--counterfactual pairs''가 처음
    나오지만, counterfactual이 wrong pair인지 inverse predicate인지 설명되지 않는다.
    
2. Problem Formulation의 첫 문단은 $r_i$, 두 identity tuple, $T_i$, $a_i$,
    $G_i$, score type을 한 번에 정의한다. 세 문단으로 분리하는 편이 낫다.

3. ``family-aware re-ranking''이 왜 family label sequence를 보존하는지
    formal list 정의 전에는 직관적으로 설명되지 않는다. 작은 toy sequence 또는
    한 문장짜리 procedural description이 필요하다.

4. ``predicate-linear skip connection''과 ``two-hidden-unit ReLU''는
    architecture에 익숙하지 않은 독자에게 역할이 보이지 않는다. predicate indicator가
    output으로 직접 가는 linear path라는 설명을 붙여야 한다.

5. Point/mesh audit에서 ``robust vertex distances''와 ``area-weighted
    triangle samples''가 왜 OBB와 다른 construct인지 한 문장으로 풀어야 한다.

원고를 장황하게 만들 필요는 없다. 각 지점에 한 문장씩만 보충하면 충분하다. 예를
들어 counterfactual은 다음처럼 처음 정의할 수 있다.

> Linked counterfactuals pair each training positive with a deliberately
> incompatible predicate or ordered pair constructed from the same training
> context.

family-aware re-ranking은 다음 한 문장으로 먼저 풀 수 있다.

> At each source position, the method selects the next candidate from the same
> relation family, but proximity and vertical-order candidates are reordered by
> the combined score.

## 먼저 공개하지 않아도 되는 약점

``약점을 숨긴다''와 ``main text에서 불필요한 future-work 목록을 줄인다''는 구분해야
한다. 다음 세 boundary는 결과 해석에 직접 영향을 주므로 숨기면 안 된다.

- 세 predictor가 하나의 3DSSG/3RScan validation target에서 평가된다는 점.
- primary Violation이 verifier-derived이며 point/mesh audit도 독립적인
    physical-validity ground truth가 아니라는 점.
- support/contact는 평가하지만 primary method가 re-rank하지 않는다는 점.

반면 다음 내용은 main text에서 줄이거나 supplement로 옮겨도 된다.

- ReplicaSSG/FROSS의 negative transfer를 구체적으로 먼저 말하는 문장. Main
    Discussion에는 single-target scope만 남기고 stress-test 결과는 supplement에서
    설명할 수 있다.
- ``Broader claims require ...''로 시작하는 reference labels/contact/pose/
    datasets의 긴 future-work 목록. 현재 audit이 independent ground truth가 아니라는
    한 문장만 남기면 충분하다.
- Metrics 문단의 pessimistic Violation, uncertainty rate, 두 종류 coverage
    수식 전체. Primary denominator는 본문에 유지하고 나머지는 supplement pointer로
    압축할 수 있다.
- Support/contact counterfactual 생성 세부 규칙. Primary variants가 이
    family를 re-rank하지 않으므로, all-family comparison에만 쓰인다는 설명 없이
    main Method에 두면 혼란스럽다.
- Re-ranking의 summed-utility maximization과 exchange-proof 설명. 보존
    property만 본문에 두고 formal claim은 supplement로 보낼 수 있다.

## Table 3에서 CI와 coverage를 뺄 것인가

**판단: 95% CI는 유지하는 것이 좋고, coverage도 원칙적으로 필요하다.**

95% CI는 임의의 ``range''가 아니라 paired change의 sampling uncertainty를 보여준다.
NeurIPS 2024의 *Verifiably Robust Conformal Prediction*은 main table에서
coverage와 95% confidence interval을 함께 보고한다. CVPR 계열 논문도 metric
mean과 95% CI lower/upper를 table에 두는 사례가 있다. 따라서 top-tier 관행을
이유로 CI를 제거할 근거는 없다.

- NeurIPS example:
    <https://proceedings.neurips.cc/paper_files/paper/2024/file/0814a342597d65e0832fc7ec9b42c317-Paper-Conference.pdf>
- CVPR example:
    <https://openaccess.thecvf.com/content/CVPR2026F/supplemental/Li_Counterfactual_Segmentation_Reasoning_CVPRF_2026_supplemental.pdf>

coverage는 이 논문에서 더 직접적인 역할이 있다. Point/mesh disagreement가 uncertain이
되고, uncertain은 Violation numerator에는 들어가지 않기 때문에, Violation 감소가
decidable coverage 감소로 생긴 것이 아닌지 확인해야 한다. Selective-prediction
연구가 risk와 coverage를 함께 보고하는 이유와 같다.

- NeurIPS selective-prediction example:
    <https://proceedings.neurips.cc/paper_files/paper/2023/file/a8526465a91166fbb90aaa8452b21eda-Paper-Conference.pdf>

다만 현재 표의 coverage는 불친절하다. `surface_audit/summary.json`을
확인하면 95.5/71.0, 98.2/83.7, 95.8/79.9는 Linear ranking의 measured/decidable
coverage다. Source coverage와의 차이는 measured coverage에서 0.5 percentage
point 이내, decidable coverage에서 1.3 points 이내다. 이를 caption 또는 본문에서
명시하면 coverage-collapse 공격을 더 직접적으로 막을 수 있다.

권장 header는 다음과 같다.

```text
Predictor & Source V & Linear V & Delta V [95% CI] & Linear Cov. (M/D)
```

지면 때문에 반드시 한 열을 줄여야 한다면, CI보다 coverage를 supplement로 옮기되
본문에 Source/Linear coverage가 크게 변하지 않았다는 수치를 한 문장으로 남기는 것이
낫다. 아무 설명 없이 coverage만 삭제하는 것은 권하지 않는다.

## Figure caption의 `\texttt`

`\texttt` 자체가 학술 caption에서 금지된 명령은 아니다.
공식 ACL style example도 Figure caption 안에서 package 이름
`mwe`를 monospace로 표시한다.

- Official ACL template:
    <https://github.com/acl-org/acl-style-files/blob/master/acl_latex.tex>

하지만 그 용도는 code, filename, command, literal token과 같이 monospace가 의미를
가질 때다. `heater close by trash can`은 code가 아니라 자연어 relation
triplet이므로 현재 caption에서는 이질적이다. 더구나 AAAI-27 Author Kit은 figure
caption을 10-point roman으로 두라고 명시한다
(`paper/aaai/official/AnonymousSubmission2027.tex:581`). 따라서 이
caption에서는 다음 중 하나를 권장한다.

```text
Open3DSG ranks ``heater close by trash can'' at 19, ...
```

또는 predicate만 italicize한다.

```text
Open3DSG ranks the relation heater -- close by -- trash can at 19, ...
```

## Contribution 2 재판단

현재 Contribution 2는 그대로 두면 독립 contribution으로 약하게 읽힐 수 있다.

```text
We learn predicate--geometry compatibility from the corresponding ordered
subject--object pair without using the predictor score, and enforce invariance
under applicable relation-preserving endpoint and predicate transformations.
```

문제는 transformation averaging의 invariance 자체가 표준적인 group averaging
성질이라는 점이다. ``averaging을 사용했다''만으로는 novelty가 아니다. 그러나
다음 세 요소를 failure cause에서 유도된 하나의 method design으로 묶으면 contribution
수준이 된다.

1. source relation score와 predictor identity를 compatibility input에서
    배제한다.
2. candidate의 ordered-pair identity를 보존한 linked positive--counterfactual
    supervision을 사용한다.
3. proximity/vertical-order의 의미 보존 변환에 대해 exact consistency를
    inference에서 보장한다.

권장 Contribution 2는 다음과 같다.

> We introduce source-score-excluded compatibility learning for fixed relation
> candidates, using linked positive--counterfactual supervision and
> relation-preserving transformation averaging to assign the same compatibility
> to equivalent endpoint/predicate representations.

이 표현은 transformation averaging만을 새롭다고 주장하지 않으면서도 factor
separation과 training supervision을 하나의 재현 가능한 method contribution으로
만든다. Contribution 3은 family composition과 unsupported family를 보존하는 constrained
re-ranking으로 별도 유지할 수 있다.

# 섹션별 상세 검토

## Title

### **[사소]** ``Semantic Confidence''의 정밀도.

원문:
```text
Beyond Semantic Confidence: Relation-Consistent Geometric Re-ranking for
3D Scene Graphs
```

제목의 후반부는 method 및 scope와 잘 맞는다. 다만 $Z$는 calibrated confidence가
아니라 sigmoid relation score 또는 cosine similarity이므로 ``Semantic Confidence''는
조금 넓다. 현재 제목은 rhetorical framing으로 유지 가능하지만, 최대한 엄밀하게 하려면
``Beyond Relation Scores''가 대안이다. 제목 변경은 필수는 아니다.

## Abstract

### **[치명적]** 보존 대상과 factor separation의 사실관계 오류.

원문:
```text
RelCompat3D, a re-ranking framework that preserves ordered-pair measurements
and the relation score produced by the predictor.
```

Method가 보존하는 핵심은 ordered-pair identity다. Measurements와 score를 하나로
``preserves''한다고 쓰면 둘을 model input으로 함께 유지하는 것처럼 읽힌다. 실제로
compatibility는 $T,G$로 계산하고 $Z$는 마지막 ranking에서만 결합한다.

수정 제안:
> RelCompat3D preserves ordered-pair identity and estimates compatibility from
> predicate semantics and predicate-independent ordered-pair measurements without
> using predictor identity or score.

### **[사소]** evaluation target 표현.

원문:
```text
on a shared 3DSSG
```

3DSSG가 dataset, ontology, validation target 중 무엇인지 불명확하다.

수정 제안:
> on one shared 3DSSG validation target

### **[사소]** predictor--$K$ values collocation.

원문:
```text
Across all reported predictor--K values
```

predictor는 value가 아니므로 ``settings''가 자연스럽다.

수정 제안:
> Across all reported predictor--$K$ settings

### **[사소]** alternative measure의 수 불일치.

원문:
```text
under an alternative geometric measure
```

point와 mesh 두 representation을 결합한 audit이므로 ``using alternative geometric
measurements''가 더 정확하다.

## Introduction

### **[치명적]** 빈 citation과 caption 형식.

원문:
```text
Open3DSG (source)~\cite{} predicts ...
```

빈 citation은 제거하거나 실제 Open3DSG key를 넣어야 한다. 또한 모든 figure/table
caption의 bold lead-in은 AAAI-27의 10-point roman caption 규정과 맞지 않는다.
\texttt{\ textbf\{RelCompat3D.\}}를 삭제한다.

### **[치명적]** Figure 1의 view와 estimator가 부정확하다.

원문:
```text
although the elevation view places the desk below the ceiling.
...
RelCompat3D demotes the inconsistent relation to rank 425
```

현재 Figure 1은 axis-aligned elevation plot이 아니라 reconstructed point-cloud view다.
또한 rank 425는 RelCompat3D-Linear 결과다.

수정 제안:
> Open3DSG ranks ``desk higher than ceiling'' at 6, although the reconstructed
> point-cloud view places the desk below the ceiling. RelCompat3D-Linear demotes
> the same candidate to rank 425, outside the top 50.

### **[치명적]** ``plausible'' motivation과 teaser example의 불일치.

원문:
```text
relation predictors rank plausible labels ... Figure 1 shows this failure.
```

``desk higher than ceiling''은 category level에서도 자연스럽게 plausible한 relation은
아니다. Figure 1은 high-scoring geometric contradiction을 잘 보여주지만 category-level
plausibility를 직접 보여주지는 않는다. 첫 문장을 ``high-scoring labels''로 바꾸면
teaser와 claim이 정렬된다. Category-plausible failure는 Figure 2의 heater--trash-can
case로 설명할 수 있다.

### **[사소]** 핵심 method paragraph의 정보 밀도.

원문:
```text
Both estimators are trained with linked positive--counterfactual pairs ...
We then average compatibility over known relation-preserving transformations ...
```

처음 읽는 독자는 counterfactual과 transformation이 각각 negative construction과
equivalence augmentation이라는 점을 구분하기 어렵다. 두 문장 사이에 다음 문장을
넣는 것이 좋다.

> Counterfactuals create incompatible training pairs, whereas the transformations
> encode alternative representations of the same relation semantics.

### **[치명적]** all-$K$ result 문장의 overclaim.

원문:
```text
Across all reported K values, both variants improve the Recall--Violation
point-estimate trade-off over the source ranking
```

SGFN $K=5$는 두 metric 모두 Source와 tie다. ``improve''를 strict improvement로
읽을 수 있으므로 다음이 정확하다.

> Across all reported $K$ values, both variants yield no worse Recall--Violation
> point estimates than the source rankings, with the largest changes on Open3DSG.

### **[사소]** Contribution 1의 ``joint''가 combined metric처럼 읽힘.

원문:
```text
joint Recall@K--Violation@K reporting
```

두 metric을 하나로 합친 objective가 아니므로 ``reporting Recall@$K$ and
Violation@$K$ together'' 또는 ``paired reporting''가 더 직접적이다.

### **[치명적]** Contribution 2 scope.

원문:
```text
enforce invariance under applicable relation-preserving endpoint and predicate
transformations
```

``applicable''만으로는 support/contact까지 변환하는 것으로 읽힐 수 있다.
``the defined proximity and vertical-order transformations''로 범위를 명시한다.
Contribution-level 판단은 앞 절의 composite formulation을 따른다.

## Related Work

### **[사소]** typo와 잘못된 collocation.

원문:
```text
absentation decisions
```

``abstention decisions''가 맞다. 더 자연스럽게는 ``selective abstention''이다.

### **[사소]** Recall@$K$ 정의가 부정확함.

원문:
```text
Recall@K measures retrieval rank rather than compatibility ...
```

Recall@$K$는 rank 자체가 아니라 cutoff에서의 exact-label retrieval을 측정한다.

수정 제안:
> Recall@$K$ measures exact-label retrieval at a ranking cutoff rather than
> compatibility with reconstructed ordered-pair geometry.

### **[사소]** 2D prior-work 문장.

원문:
```text
For fixed 2D scene graph generation predictions, Neau et al. ...
```

수식어 연결이 어색하다.

수정 제안:
> For fixed predictions from 2D scene graph generators, Neau et al. ...

### 잘 된 점.

각 prose paragraph는 related methods와 RelCompat3D의 공통점 또는 차이로 끝난다.
3D generation, geometry-aware evidence, transformation methods, calibration/uncertainty와의
novelty boundary도 분리되어 있다. Related Work의 구조는 유지하는 것이 좋다.

## Method

### **[사소]** Problem Formulation 첫 문단이 지나치게 조밀함.

원문은 $r_i$, score contracts, context, 두 identity, $T_i$, $a_i$, $G_i$를 한
문단에서 정의한다. 다음 세 단위로 나누는 것이 좋다.

1. candidate tuple, native source score, context;
2. ordered-pair identity와 exact relation identity;
3. $T_i$, $a_i$, $G_i$의 역할.

### **[사소]** family label 설명의 문법과 의미.

원문:
```text
The family label a_i always selects the transformation set and re-ranking
relation families.
```

하나의 $a_i$가 ``relation families''를 선택한다는 표현은 어색하다.

수정 제안:
> The family label $a_i$ selects the applicable transformation set and determines
> whether the candidate's family is re-ranked.

### **[치명적]** support/contact training head의 목적이 빠짐.

원문:
```text
Support/contact negatives replace one endpoint under separation margins.
```

primary variants는 support/contact를 re-rank하지 않는데 이 family의 negative
construction이 갑자기 등장한다. 이 detail을 supplement로 옮기거나, all-family
comparison의 linear head에만 쓰인다고 명시해야 한다.

### **[치명적]** exact construction rule pointer가 없음.

원문:
```text
Evaluation rows, predictor scores, and verifier-status labels are not used to
construct training examples.
```

boundary는 좋지만 threshold, cap, balancing이 어디에 있는지 rendered text에서 알 수
없다. 다음 한 문장을 유지해야 한다.

> The supplement specifies the family-specific thresholds, negative cap, and
> balancing rules.

이는 불필요한 약점 공개가 아니라 재현성 pointer다.

### **[사소]** nonlinear architecture 설명의 난이도.

원문:
```text
one shared two-hidden-unit ReLU network
...
With a predicate-linear skip connection
```

``two-hidden-unit''는 hidden layer가 두 개인지 unit이 두 개인지 잠깐 모호하다.

수정 제안:
> one shared single-hidden-layer ReLU network with two hidden units

그리고 skip connection은 ``a direct linear path from predicate indicators to
the output logit''로 한 번 풀어 쓴다.

### **[사소]** outputs collocation.

원문:
```text
Transformation averaging therefore outputs ...
```

수학적 relation에는 ``yields'' 또는 ``guarantees''가 자연스럽다.

### **[치명적]** loss가 실제 ordering을 보장하는 것처럼 씀.

원문:
```text
the pairwise objective still orders each linked positive above its
counterfactual
```

loss는 ordering을 장려하지만 모든 sample에 대해 보장하지 않는다.

수정 제안:
> the pairwise objective encourages each linked positive to score above its
> counterfactual

### **[치명적]** log-score 설명의 전제가 불명확함.

원문:
```text
For positive factors ... log u_i = log Z_i + log C_i ...
```

Open3DSG의 native score는 cosine similarity이므로 score positivity가 일반 정의에서
자동으로 보장되지 않는다. 이 identity는 method에 필요하지 않으므로 삭제하는 것이
가장 안전하다. 유지하려면 $Z_i>0$ 및 $C_i^{\rm tr,q}>0$ 조건과 실제 observed score
contract를 명시해야 한다.

### **[사소]** optimization property가 main flow를 방해함.

원문:
```text
maximizes their sum of ranking scores subject to the preserved family counts
and support/contact subsequence
```

construction property는 맞을 수 있지만 핵심 이해에는 필요하지 않다. 본문은 family
sequence와 support/contact subsequence 보존만 설명하고 exchange proof와 utility
maximization은 supplement로 옮기는 것이 읽기 쉽다.

### **[사소]** source score 명칭 통일.

원고는 ``predictor score'', ``source score'', ``source relation score'', ``relation
score produced by the predictor''를 혼용한다. $Z$의 통일 표현은 ``source relation
score''가 가장 정확하다. probability 또는 calibrated confidence로 부르지 않는다.

## Experimental Setup

### **[치명적]** evaluation scope와 re-ranking scope의 혼동.

원문:
```text
restricted to relations whose consistency can be re-ranked from reconstructed
ordered-pair geometry
```

support/contact는 평가 scope에는 있지만 re-ranking scope에는 없다.

수정 제안:
> restricted to relation families whose consistency can be assessed from
> reconstructed ordered-pair geometry

### **[사소]** family 이름 통일.

원문:
```text
relative vertical families
```

Method와 맞춰 ``vertical-order family''로 통일한다.

### **[사소]** pooled model의 위치가 불명확함.

원문:
```text
a pooled linear model tests whether family-specific fitting is necessary
```

Table 1에는 pooled model이 없다. ``reported in the supplement''를 바로 붙여야 독자가
누락된 baseline으로 오해하지 않는다.

### **[사소]** Metrics 문단의 과밀함.

Primary Recall/Violation 수식과 uncertain denominator는 본문에 필요하다. 반면
uncertainty rate, decidable-only violation, status coverage, decidable coverage,
pessimistic variant를 한 문장에 모두 나열하면 main setup이 audit checklist처럼 읽힌다.

수정 제안:
> The supplement reports uncertainty, coverage, decidable-only Violation, and a
> pessimistic variant that counts uncertain candidates as violations.

### bootstrap 표현에 대한 판단.

원문:
```text
Paired 95% confidence intervals use 1,000 bootstrap resamples of the 157 scans,
keeping all contexts from each scan together ...
```

이 문장은 필요하고 자연스럽다. ``bootstrap''은 top-tier empirical papers에서 흔히
쓰는 표준 통계 용어다. 같은 scan의 context가 독립 sample이 아니므로 scan-level
resampling을 밝히는 것이 오히려 rigor를 높인다. ``cluster bootstrap''이라는 말을
반드시 쓸 필요는 없고, 현재처럼 procedural definition을 쓰면 충분하다.

## Results

### **[치명적]** tie를 decrease로 서술함.

원문:
```text
the Violation point estimate decreases for every predictor. SGFN is tied at
K= and changes only marginally at K=10
```

SGFN $K=5$는 Source, Linear, MLP가 Recall 31.17, Violation 2.37로 모두 tie다.

수정 제안:
> Across $K\in\{5,10,20,50,100\}$, neither variant has a lower Recall point
> estimate or a higher Violation point estimate than Source. SGFN is tied at
> $K=5$ and changes only marginally at $K=10$.

### **[사소]** ``reported ranges'' collocation.

원문:
```text
the largest gains across the reported ranges
```

``reported $K$ values''가 정확하다.

### **[사소]** ``better''의 정의.

원문:
```text
yields a better K=50 point estimate Recall-Violation trade-off
```

두 metric이 모두 weakly 개선된다는 뜻을 바로 밝히면 좋다.

수정 제안:
> at $K=50$, each variant has a Recall point estimate no lower and a Violation
> point estimate lower than Source for all three predictors

### 잘 된 점.

Linear와 MLP 중 하나를 universal winner로 만들지 않고 Open3DSG의 Recall--Violation
operating-point 차이를 설명한 점은 엄밀하다. RankAvg/RRF의 low-$K$ Recall loss와
all-family product의 support/contact selection change도 comparator 역할과 맞게
해석했다.

## Discussion and Limitations

### **[사소]** main text에서 줄일 수 있는 stress-test 문장.

원문:
```text
The supplementary ReplicaSSG evaluation using FROSS predictions shows that
performance changes under ontology and geometry shifts.
```

정직하지만 main claim을 방어하는 데 필수는 아니다. single-target scope를 바로
말한 뒤 이 문장은 supplement에 두는 편이 submission narrative에는 더 유리하다.
삭제하더라도 cross-dataset generalization을 주장해서는 안 된다.

### **[치명적]** 반드시 남겨야 하는 construct boundary.

원문:
```text
The point- and mesh-based audit still uses the same reconstructed instance
geometry and relation ontology, so it does not provide an independent reference
for geometric validity.
```

이 문장은 핵심 construct validity boundary이므로 유지해야 한다. 숨기면 reviewer가
audit을 independent ground truth로 오해하거나 circularity를 지적했을 때 더 큰 문제가
된다. 다만 다음 future-work 문장은 줄일 수 있다.

```text
Broader claims require independently defined reference labels, richer contact
and pose evidence, and evaluation on additional datasets.
```

권장 압축:
> Because the point- and mesh-based audit uses the same reconstructed scenes and
> ontology, it is an alternative geometric measurement rather than independent
> validity ground truth.

### **[사소]** outside-scope 목록 압축.

support/contact는 main boundary이므로 유지한다. Reference-frame relations와 complete
graph generation은 한 문장으로 줄일 수 있다.

> RelCompat3D assumes known instances and reconstructed ordered-pair geometry; it
> does not generate complete graphs or correct contact-dependent relations.

## Conclusion

### **[치명적]** strict lower claim이 Table 1과 모순됨.

원문:
```text
both variants yield lower verifier-derived Violation point estimates while
preserving or improving Recall point estimates at every reported K
```

SGFN $K=5$는 Violation도 tie다.

수정 제안:
> Across three predictors on one shared 3DSSG validation target, both variants
> yield lower or tied verifier-derived Violation point estimates while preserving
> or improving Recall point estimates at every reported $K$.

# Figure 검토

## Figure 1: failure case

### 내용 적합성.

Figure 1은 failure case의 목적을 대체로 잘 수행한다. 같은 candidate가 Source rank
6에서 Linear rank 425로 이동하고, desk가 ceiling 아래에 있는 reconstructed point-cloud
evidence가 함께 보인다. 따라서 ``high source score does not ensure same-pair geometric
compatibility''라는 task motivation은 전달된다.

다만 다음 수정이 필요하다.

- 그림 내부 ``Relcompat3D''를 ``RelCompat3D-Linear''로 수정한다.
- caption의 ``elevation view''를 ``reconstructed point-cloud view''로
    수정한다.
- rank change가 Linear 결과임을 caption에 명시한다.
- 이 사례는 category-plausible error라기보다 obvious vertical contradiction이다.
    Introduction의 ``plausible'' failure와 동일 사례라고 단정하지 않는다.

## Figure 2: method overview

현재 Figure 2가 보여주는 핵심 흐름은 맞다.

1. predicate semantics와 pair measurements만 compatibility block으로 들어간다.
2. source relation score는 compatibility를 우회한다.
3. 두 signal은 within-family score에서 결합된다.
4. family-aware re-ranking 후 rank가 19에서 178로 이동한다.

따라서 Linear/MLP architecture, BCE, margin loss를 그림 안에 추가할 필요는 없다.
그림을 과밀하게 만들지 않으려는 판단은 타당하다. 그러나 다음 두 정보는 caption에
필요하다.

- compatibility는 relation-preserving transformations에 대해 averaging된
    score라는 점;
- illustrated 19--178 rank change는 RelCompat3D-Linear 결과라는 점.

가능하면 그림 내부 ``T/G Compatibility''는 ``Predicate--geometry compatibility''로
바꾼다. Slash 표기는 $T$와 $G$의 단순 ratio처럼 보일 수 있다. Primary scope를 그림에
더 넣기 어렵다면 caption 끝에 다음 한 문장을 추가한다.

> The method re-ranks proximity and vertical-order candidates; support/contact
> candidates retain source order. The illustrated 19-to-178 change is produced by
> RelCompat3D-Linear.

## Figure 3: quantitative trajectory

Figure 3의 plot type은 적합하다. Table 1이 exact values를, Figure 3이 right/down
movement와 $K$에 따른 trajectory를 담당하므로 bar chart보다 현재 line trajectory가
더 많은 정보를 보존한다. 세 predictor의 scale이 달라 axis range가 다른 점도 caption에
명시되어 있다.

수정할 부분은 다음과 같다.

- legend의 ``Ours (Linear)/(MLP)''를 가능하면 Table과 같은
    ``RelCompat3D-Linear/MLP''로 통일한다.
- ``same budget order''를 ``same increasing-$K$ order''로 바꾼다.
- 현재 45 coordinates는 active
    `evaluation/routed_comparators/metrics.csv`의 수치와 일치한다.

## Figure source의 AAAI 형식 문제

**[치명적]** `paper/user.tex`이 직접 참조하는
`paper/Figure1.pdf`, `Figure2.pdf`, `Figure3.pdf`를
`pdffonts`로 확인하면 모두 CID TrueType/Identity-H font를 포함한다. AAAI-27
Author Kit은 CID/Identity-H를 제거하거나 outline으로 변환하도록 요구한다
(`AnonymousSubmission2027.tex:232`). 또한 Figure 3 inclusion은 다음을
사용한다.

```text
trim={0bp 43bp 0bp 45bp}, clip
```

Author Kit은 LaTeX의 trim/clip에 의존한 crop을 금지하고 figure file 자체를 외부에서
crop하라고 명시한다
(`AnonymousSubmission2027.tex:575--579`). 따라서 최종 제출에서는
outlined-font PDF를 만들고 crop을 asset에 적용한 뒤 단순
`\includegraphics[width=...]`로 삽입해야 한다.

# Table 및 수치 검토

## Table 1

### 수치.

Table 1의 Source, Linear, MLP, RankAvg, RRF values는 active routed-comparator
artifact와 일치한다. Abstract의 ``no lower Recall/no higher Violation point
estimates''도 모든 30 proposed-variant predictor--$K$ pair에 대해 point-estimate
수준에서 맞다. 단, tie를 strict decrease로 바꾸면 안 된다.

### **[사소]** caption 문법.

원문:
```text
Source denoted each predictor's original ranking.
```

``Source denotes''가 맞다. ``All entries are percentages''도 넣어야 한다. Caption의
bold lead-in은 제거한다.

권장 caption:
> Shared 3DSSG validation results. Exact-match Recall (R, higher is better) and
> verifier-derived Violation (V, lower is better) are percentages. Source denotes
> each predictor's original ranking. Both RelCompat3D variants, RankAvg, and RRF
> use the same family-aware ranking procedure; Product (all families) applies
> compatibility to every evaluated family.

## Table 2: Ablations

### 수치.

제시한 Linear control 값과 full MLP rows는 locked K=50/100 artifacts와 정합하다.
각 predictor block의 row count도 8로 맞다.

### **[치명적]** caption의 scope가 완전히 명시되지 않음.

원문:
```text
For compactness, control rows are shown for RelCompat3D-Linear.
```

표 안의 MLP row가 full method인지 MLP control인지 caption만으로는 모호하다. 또한
모든 값이 percentage라는 설명이 빠졌다.

권장 caption:
> Ablations and counterfactual controls at $K\in\{50,100\}$. Control rows use
> RelCompat3D-Linear; the RelCompat3D-MLP rows report the full nonlinear variant
> for comparison, with matched MLP controls in the supplement. All entries are
> percentages; R is Recall (higher is better) and V is verifier-derived Violation
> (lower is better). Every condition uses the same candidates and family-aware
> ranking procedure as Table 1.

## Table 3: Point/mesh audit

### 수치.

Source, Linear, paired change, and Linear measured/decidable coverage는 frozen
surface-audit artifact와 일치한다. Change는 percentage-point 차이다.

### **[치명적]** ``Ours''와 coverage provenance.

원문:
```text
Predictor & Source & Ours & Change (95% CI) & Cov.
...
Ours denotes RelCompat3D-Linear; ... Cov. is measured/decidable coverage.
```

두 proposed variant가 있으므로 ``Ours''는 모호하다. ``Linear''로 바꾼다. Coverage가
Source인지 Linear인지도 header에서 드러나지 않는다. ``Linear Cov. (M/D)''로
바꾸고 caption에서 M/D를 푼다.

### **[치명적]** primary metric과 다른 construct라는 설명 누락.

현재 body에는 설명이 있지만 caption만 읽으면 Table 1 Violation을 다른 방법으로
재측정한 것으로 오해할 수 있다. ``These values are not directly comparable to the
primary Violation in Table 1''를 caption에 넣는다.

권장 compact caption:
> Point-/mesh-based Violation at $K=50$ (%, lower is better). Satisfied or
> violated status requires agreement between the two measurements; disagreement
> is uncertain. $\Delta V$ is Linear minus Source in percentage points with a
> paired 95% interval from scan-level resampling; M/D is Linear
> measured/decidable coverage. These values are not directly comparable to the
> primary Violation in Table 1.

이 caption이 너무 길면 agreement rule을 바로 앞 본문에 두되, alternative metric과
coverage provenance는 caption에 남긴다.

# 표현 통일 계약

다음 표현으로 통일하는 것이 좋다.

| 개념 | 통일 표현  |
| --- | --- |
| generic field | 3D scene graph (고유명/제목이 아니면 lowercase)  |
| $Z$ | source relation score  |
| $G$ | predicate-independent ordered-pair measurements  |
| $C$ | predicate--geometry compatibility  |
| pair | 첫 등장 ordered subject--object pair, 이후 ordered pair  |
| vertical family | vertical-order relations/candidates  |
| metric | exact-match Recall@$K$; verifier-derived Violation@$K$  |
| ranking | family-aware re-ranking  |
| support/contact | candidates retain source order  |
| audit | point- and mesh-based consistency audit / alternative geometric measure  |

다음 혼용은 정리한다.

- predictor score / source score / source relation score
- predicate-geometry / predicate--geometry
- vertical / relative vertical / vertical order
- ordered pair geometry / ordered-pair geometry
- Recall@K / Recall@$K$

# 권장 수정 순서

1. Abstract의 factor-separation 문장, Results의 SGFN tie, Conclusion의 strict
    lower claim을 먼저 수정한다.
2. Figure 1/2 caption을 실제 view와 Linear rank change에 맞추고 caption의
    bold/monospace를 제거한다.
3. Method의 support/contact negative 목적, counterfactual rule pointer,
    pairwise-loss 보장 표현, log-score 문장을 정리한다.
4. Experiments의 assessed/re-ranked scope를 분리하고 Table 2/3 caption을
    self-contained하게 만든다.
5. Discussion은 single-target와 non-independent-audit boundary만 남기고
    FROSS 상세 및 future-work 목록을 supplement로 축소한다.
6. 최종 Figure PDF의 Identity-H fonts와 Figure 3 trim/clip을 제거한다.

# 최종 판단

현재 원고는 ``geometry를 추가했다''는 단순 claim보다 강한 구조를 갖는다. Failure의
원인을 source relation score와 same-pair compatibility의 차이로 정의하고, 그 원인에
맞춰 score-excluded compatibility, identity preservation, transformation consistency,
family-constrained re-ranking을 설계했기 때문이다. Wrong-pair/shuffled-geometry,
wrong-predicate/swap, distance-only, compatibility-only controls도 이 논리를 검증한다.

그러나 Contribution 2를 transformation averaging 자체로 내세우면 novelty ceiling이
낮아진다. 반드시 source-score exclusion과 linked counterfactual supervision을 포함한
composite design으로 써야 한다. 또한 verifier-derived result를 strict physical-validity
claim으로 넓히지 않고, point/mesh audit을 alternative construct check로 한정해야 한다.
이 두 조건과 위의 사실/형식 오류를 수정하면, transcript는 reviewer가 task, method,
evidence, boundary를 일관되게 요약할 수 있는 수준에 도달한다.

# 추가 문체 감사: possessive, 용어, 문장부호, 문장 길이

이 절은 `paper/user.tex`만을 다시 검사한 결과이다. LaTeX 수식 안의 구분자와
일반 산문을 구분했고, 단순 문자열 탐지 뒤 각 용례를 문맥에서 확인했다.

## 요약

- 영어 possessive 형태인 `A's B`는 3건뿐이며 남발되지 않았다. 세 표현 모두
  문법적으로 허용되지만, formal prose와 용어 통일을 위해 `the B of A` 또는
  전치사구로 바꾸는 편이 더 명확하다.
- Unicode em dash (`—`)와 LaTeX em dash (`---`)는 모두 0건이다. 따라서 em dash
  남발 문제는 없다. 원고의 `--`는 em dash가 아니라 LaTeX en dash이다.
- semicolon은 총 14건이다. 이 중 3건은 feature vector의 수학적 구분자이고,
  11건은 산문이다. 전체 분량 대비 남발은 아니지만 Metrics, Results, Table 3
  caption, audit 문단에 몰려 있어 일부는 마침표로 나누는 것이 좋다.
- 가장 중요한 문체 문제는 긴 문장이다. 특히 세 가지 이상의 주장이나 조건을 한
  문장에 넣은 Introduction, Related Work, Method, Results 문장은 분리해야 한다.
  실무 기준으로 35단어를 넘는 문장은 우선 분리하고, 28--35단어 문장은 절이 세 개
  이상이거나 목록을 포함할 때 분리하는 것을 권장한다. 이는 venue 규정이 아니라
  reviewer 가독성을 위한 기준이다.

## `A's B` 형태

### **[사소]** possessive는 적지만 모두 더 명시적으로 바꿀 수 있음.

`user.tex`에서 확인된 possessive는 다음 세 곳이다.

| 위치 | 원문 | 권장 표현 |
| --- | --- | --- |
| line 50 | `each candidate's ordered subject--object identity` | `the ordered-pair identity of each candidate` |
| line 167 | `that family's candidates` | `the candidates in family $a$` |
| line 209 | `each predictor's original ranking` | `the original ranking of each predictor` |

영어 논문에서 무생물 possessive를 쓰는 것 자체는 오류가 아니다. 따라서 이를
기계적으로 전부 금지할 필요는 없다. 다만 위 세 용례는 각각 이미 정의된 technical
object를 가리키므로 전치사구가 더 정확하다. 특히 line 209는 possessive와 별개로
`Source denoted`를 `Source denotes`로 고쳐야 한다.

## 용어 및 표기 통일

### **[사소]** 같은 개념의 dash와 철자 표기가 섞여 있음.

핵심 용어가 다음 세 형태로 혼용된다.

```text
predicate–geometry compatibility   % Unicode en dash, line 32
predicate--geometry compatibility  % LaTeX en dash, 다수
predicate-geometry compatibility   % single hyphen, lines 76 and 90
```

LaTeX 원고에서는 `predicate--geometry compatibility`로 통일하는 것이 가장
안전하다. 같은 이유로 line 137의 `linked positive-counterfactual`은
`linked positive--counterfactual`, line 235의 `Recall-Violation trade-off`는
`Recall--Violation trade-off`로 고친다. Abstract의 Unicode
`predictor–$K$`도 `predictor--$K$`로 바꾸면 source-level 표기가 일관된다.

### **[치명적]** metric 명칭이 같은 construct에 여러 표현을 사용함.

현재 `exact-match Recall`, `exact-label Recall`, `Recall with exact predicate
matching`이 같은 metric을 가리킨다. 또한 `rule-based Violation`과
`verifier-derived Violation`이 섞여 있다. 독자가 서로 다른 metric으로 오해하지
않도록 다음 계약이 좋다.

- 첫 정의와 주요 claim: `exact-match Recall@$K$`와
  `verifier-derived Violation@$K$`
- 이후 문맥상 분명할 때: `Recall@$K$`와 `Violation@$K$`
- 수식 내부: 현재처럼 `\mathrm{Recall@K}`와 `\mathrm{Violation@K}` 유지
- Table header: `R@50`, `V@50`처럼 caption에서 정의된 약어 유지 가능

따라서 line 78의 `exact-label Recall@K with rule-based Violation@K`는
`exact-match Recall@$K$ with verifier-derived Violation@$K$`로 통일한다.

### **[사소]** relation-family 명칭이 혼용됨.

`vertical relations`, `vertical order`, `vertical-order`, `relative vertical
families`가 같은 family를 가리킨다. 산문에서는 `vertical-order relations`,
`vertical-order candidates`, `vertical-order family`로 통일한다. 수학적 집합
이름 `\mathrm{vertical\ order}`는 그대로 두어도 된다. 이에 따라 line 52의
`proximity and vertical relations`와 line 216의 `relative vertical families`를
각각 `proximity and vertical-order relations`, `proximity and vertical-order
families`로 고친다.

### **[사소]** $Z$의 이름을 하나로 고정할 필요가 있음.

동일한 $Z$를 `predictor score`, `source score`, `source relation score`로
부른다. 첫 정의에서 `$Z_i$ is the source relation score produced by the
predictor`라고 쓴 뒤, 산문에서는 `source relation score`로 통일하는 것이 가장
정확하다. `source ranking`은 score가 아니라 순서를 뜻하므로 별도 용어로 유지한다.
Figure 내부 label을 `Predictor Score ($Z$)`로 남겨야 한다면 caption에서 한 번
`the source relation score $Z$`와 연결하면 충분하다.

### **[사소]** ordered-pair 표현의 명사형과 수식형을 구분해야 함.

첫 등장에서는 `ordered subject--object pair`, 이후 명사형은 `ordered pair`, 다른
명사를 수식할 때는 `ordered-pair identity`, `ordered-pair geometry`,
`ordered-pair measurements`가 자연스럽다. Figure 1 caption의 `ordered object
pair`는 방향성을 흐리므로 `ordered subject--object pair`로 바꾼다. `ordered pair
geometry`도 attributive form인 `ordered-pair geometry`로 통일한다.

### **[사소]** estimator, head, variant의 층위를 유지해야 함.

두 제안 방법은 `RelCompat3D-Linear`와 `RelCompat3D-MLP` variants이고, 일반 명칭은
`compatibility estimators`이다. `linear head`는 Linear estimator 내부의
family-specific module을 가리킬 때만 사용한다. 이 구분을 유지하면 `Linear head`,
`Linear estimator`, `Linear variant`가 서로 다른 방법처럼 읽히지 않는다.

## Em dash와 semicolon

### Em dash: 문제 없음.

원고에는 Unicode em dash `—`도, LaTeX em dash `---`도 없다. 확인된 26개의
double hyphen `--`는 `subject--object`, `predicate--geometry`,
`positive--counterfactual`, `Recall--Violation` 같은 relational compound를
표기하는 LaTeX en dash이다. 이를 em dash 남발로 집계하면 안 된다. 다만 Unicode
en dash와 LaTeX `--`를 섞지 말고 후자로 통일해야 한다.

### **[사소]** 산문 semicolon은 수 자체보다 배치가 조밀함.

수식 line 114의 semicolon 3개는 feature-vector 요소를 구분하므로 유지한다. 산문의
11개는 전체적으로 과도하지 않지만, 아래처럼 독립 문장을 연결한 곳은 마침표가 더
읽기 쉽다.

- line 220:
  `Normalization, imputation, and model parameters use only 1,061 training
  scans. Model design and the applicable relation families were selected on the
  117-scan development split.`
- line 223:
  `Both sets use exact relation identity $(s_i,p_i,o_i)$ within $c$. Family
  mapping is used only for re-ranking and never for label matching.`
- line 231:
  secondary metric 목록 뒤 문장을 끝내고, `A pessimistic variant counts
  uncertain candidates as violations.`를 별도 문장으로 둔다.
- line 237:
  Linear/MLP 수치 비교 뒤 문장을 끝내고, `The two variants are nearly tied on
  VL-SAT and SGFN.`을 분리한다.
- line 297:
  `Both are proposed compatibility estimators. The corresponding MLP controls
  are reported in the supplement.`
- lines 315--316:
  Table 3 caption의 `Ours denotes ...; Change is ...; Cov. is ...`를 세 문장으로
  나눈다. 가능하면 모호한 `Ours`와 `Cov.` 자체도 앞 절의 권장안대로 header에서
  명시한다.
- lines 324--325:
  agreement rule과 supplement 결과를 각각 짧은 독립 문장으로 쓴다.

Figure 3 caption line 250의 semicolon은 문법적으로 허용되지만,
`Numbers label ... . All curves follow the same increasing-$K$ order.`가 더 빠르게
읽힌다.

## 긴 문장 점검

### **[사소 · 높은 수정 우선순위]** 세 개의 design rationale가 한 문장에 몰림.

line 50 원문:

> Excluding $Z$ prevents direct copying of the predictor score, preserving
> ordered-pair identity prevents geometry from another object pair from being
> substituted for the candidate evidence, and transformation averaging assigns
> equal compatibility to equivalent endpoint/predicate representations.

36단어이고 세 독립 주장으로 구성되어 있다. 다음처럼 분리하는 것이 가장 명확하다.

> Excluding $Z$ prevents direct copying of the source relation score.
> Preserving ordered-pair identity prevents geometry from another pair from
> replacing the candidate evidence. Transformation averaging assigns equal
> compatibility to equivalent endpoint/predicate representations.

### **[사소 · 높은 수정 우선순위]** Related Work의 비교와 차이를 한 문장에 결합함.

line 73 원문:

> These methods and RelCompat3D all use structured relation evidence, but
> RelCompat3D estimates continuous compatibility from the reconstructed ordered
> subject--object pair and enforces applicable endpoint/predicate transformations
> before joint Recall@K--Violation@K evaluation.

다음처럼 commonality와 difference를 분리한다.

> These methods and RelCompat3D all use structured relation evidence.
> RelCompat3D instead estimates continuous compatibility for a fixed candidate
> from its reconstructed ordered pair. It then enforces the applicable
> endpoint/predicate transformations before evaluation.

### **[사소 · 높은 수정 우선순위]** candidate tuple 정의가 한 호흡에 너무 많은
기호를 설명함.

lines 93--94의 `where $s_i$ and $o_i$ ...` 문장은 30단어를 넘고, 이어지는 한
문단에서 score type, context, 두 identity, $T_i$, $a_i$, $G_i$까지 모두 정의한다.
다음처럼 세 단위로 나눈다.

> Here, $s_i$ and $o_i$ are the ordered subject and object instance identifiers,
> and $p_i$ is the predicate. The family label $a_i$ selects the family-specific
> procedure. The source relation score is denoted by $Z_i$.

이후 `score contract`, `candidate identity`, `compatibility inputs`를 각각 별도
문단으로 두면 그림 없이 읽어도 정의 순서가 보인다.

### **[사소 · 높은 수정 우선순위]** support/contact scope와 이유가 한 문장에
겹침.

line 98 원문:

> Support/contact is evaluated but kept in source order because this family
> requires richer local contact and pose evidence, and no single endpoint
> transformation preserves the semantics for every predicate in the family.

권장:

> Support/contact candidates are evaluated but remain in source order. Their
> assessment requires richer local contact and pose evidence, and no single
> endpoint transformation preserves every predicate in this family.

### **[사소 · 높은 수정 우선순위]** re-ranking의 선택 성질과 최적화 성질이 한
문장에 있음.

line 167 원문:

> For each prefix, the rule also selects the highest-scoring candidates within
> each re-ranked family and maximizes their sum of ranking scores subject to the
> preserved family counts and support/contact subsequence.

권장:

> For each prefix, the rule selects the highest-utility candidates within each
> re-ranked family. Subject to the preserved family counts and support/contact
> subsequence, this selection maximizes the sum of within-family ranking scores.

### **[사소 · 높은 수정 우선순위]** Results의 관찰과 해석을 나누어야 함.

line 235 원문:

> Open3DSG exposes the mismatch most strongly: Source baseline ranks
> geometrically inconsistent relation candidates near the top, whereas both
> RelCompat3D variants raise Recall and lower Violation without applying a hard
> filter.

권장:

> Open3DSG exposes the mismatch most strongly. Its Source baseline ranks many
> geometrically inconsistent candidates near the top. Both RelCompat3D variants
> raise Recall and lower Violation without applying a hard filter.

line 237의 Linear/MLP 수치 비교도 semicolon에서 문장을 끝내야 한다. 두 variant의
trade-off 설명은 다음 문장으로 분리한다. 이 수정은 수치 관찰과 해석의 경계를
분명하게 만든다.

## 길지만 유지 가능한 문장

다음 문장은 26--29단어 수준이지만 논리 구조가 하나이므로 반드시 나눌 필요는 없다.

- line 48의 source relation score와 same-pair predicate satisfaction의 차이
- line 231의 paired scan-resampling 절차
- line 331의 point/mesh audit independence 한계
- line 334의 Conclusion 요약

단, line 334는 길이와 별개로 SGFN $K=5$ tie 때문에 `lower`를 `lower or tied`로
고쳐야 한다. 이 claim 오류는 앞의 Conclusion 검토 절에서 이미 지적했다.

## 이 문체 감사의 수정 우선순위

1. line 50, lines 93--94, line 167, lines 235--237의 긴 문장을 먼저 나눈다.
2. metric 명칭과 `$Z$` 명칭을 통일한다.
3. Unicode/single-hyphen 표기를 LaTeX en dash 형태로 통일한다.
4. Table 1/3 caption과 Metrics/Audit 문단의 semicolon을 마침표로 바꾼다.
5. 세 possessive는 마지막 language pass에서 전치사구로 정리한다.
