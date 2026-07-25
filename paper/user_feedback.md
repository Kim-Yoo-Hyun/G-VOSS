# RelCompat3D Active-Section 통합 재검토

- 검토일: 2026-07-25 KST
- transcript 대상:
  - `paper/aaai/sec/0_abstract.tex`
  - `paper/aaai/sec/1_introduction.tex`
  - `paper/aaai/sec/2_related_work.tex`
  - `paper/aaai/sec/3_method.tex`
  - `paper/aaai/sec/4_experiments.tex`
  - `paper/aaai/sec/5_discussion_limitations.tex`
  - `paper/aaai/sec/6_conclusion.tex`
- 기준: accept 가능성, reviewer 설득력, 과학적 정합성, 쉬운 영어,
  section 역할, 용어와 notation 일관성
- citation은 표기 방식이나 인용 내용의 적절성을 판단하지 않았다. 선행연구 언급과
  section별 첫 약어에 citation이 존재하는지만 확인했다.
- Main PDF는 다시 빌드하지 않았다. Supplement는 용어 동기화 후 Docker에서
  smoke build를 통과했다.

상태 표시는 다음과 같다.

- `[x]`: 해결 완료 또는 현재 문장으로 충분
- `[~]`: 핵심 내용은 맞지만 제출 전 짧은 수정 권장
- `[ ]`: 제출 전 수정 필요
- `[보류]`: 사용자 결정에 따라 최종 layout 단계로 보류
- `[제외]`: 사용자 요청에 따라 검토 대상에서 제외

## 전체 판단

현재 active transcript에는 main claim을 무너뜨리는 수치 모순이나 논리적 비약이
없다. Reviewer가 논문의 acceptance case를 다음과 같이 요약할 수 있다.

1. Fixed relation predictor의 score는 해당 ordered pair에 대한
   predicate--geometry compatibility를 직접 나타내지 않을 수 있다.
2. RelCompat3D는 candidate identity와 ordered-pair measurements를 유지하면서
   source relation score 없이 compatibility를 추정한다.
3. Applicable transformation consistency를 보장한 뒤, source relation score와
   compatibility를 family 내부에서만 결합한다.
4. 세 predictor와 다섯 \(K\) 값에서 두 estimator 모두 Source보다 나쁘지 않은
   Recall--Violation point estimates를 보인다.
5. Controls와 point- and mesh-based audit가 pair association, score separation, metric
   dependence의 범위를 점검한다.

현재 main claim을 뒤집거나 재현을 막는 transcript 이슈는 없다. I-015--I-021을
사실 오류, claim과 evidence의 불일치, 재현성 장애라는 고정 기준으로 다시 판정한
결과, 일곱 항목은 모두 현재 source, supplement, 또는 주변 문맥에서 해결됐다.
추가로 필수 수정할 transcript 항목은 확인되지 않았다.

## 기존 이슈 재검토

| 이슈 번호 | 현재 상태 | active section 기준 판단 |
|---|---|---|
| I-001 | `[x]` | 기존 1--105번의 문법, metric, family-aware ranking, score range, direct component removal 수정은 유지됨 |
| I-002 | `[제외]` | 기존 87번은 사용자 요청에 따라 제외 유지 |
| I-003 | `[제외]` | 기존 93번의 추가 limitation 제안은 제외 유지 |
| I-004 | `[x]` | normalized-height notation은 `\Delta z_i^{\rm norm}`으로 통일됨 |
| I-005 | `[x]` | `largest Violation increases`를 `increase Violation`으로 낮춰 Table 2 수치와 일치함 |
| I-006 | `[x]` | MLP 첫 정의는 line 11의 `shared nonlinear estimator`와 line 44의 `multilayer perceptron (MLP)`으로 정리됨 |
| I-007 | `[x]` | Method subsection 명칭은 `Compatibility Estimation`으로 수정됨 |
| I-008 | `[x]` | `corresponding results`는 `these additional metrics`로 구체화됨 |
| I-009 | `[x]` | qualitative paragraph의 obsolete 주석 버전이 삭제됨 |
| I-010 | `[x]` | Main Results에 demotion과 promotion을 함께 설명하고 supplement에는 promotion 근거를 prose로 기록함 |
| I-011 | `[x]` | Table 3 caption이 \(K\), agreement rule, \(\Delta V\), M/D의 명칭과 단위를 설명함. `\textbf` 형식은 이번 내용 검토에서 제외 |
| I-012 | `[x]` | support/contact에 \(H_a=\{e\}\)를 정의하고 all-family comparison의 역할을 명시함 |
| I-013 | `[x]` | 세 predictor의 evaluated score가 모두 non-negative이며 정확한 범위와 product sign 해석이 supplement에 존재함. 현재 scoped claim에는 main 반복이 필수적이지 않음 |
| I-014 | `[x]` | pairwise-loss removal과 transformation-averaging removal이 supplement에 있고 main pointer도 유지됨 |

## I-015--I-021 엄격 재판정

이번 재판정에서는 다음 세 조건 중 하나를 만족할 때만 미해결 이슈로 남겼다.

1. 현재 문장이 사실 또는 수치와 다르다.
2. Main claim과 실제 method 또는 evidence가 어긋난다.
3. 재현이나 핵심 표의 해석을 막는 정보가 main과 supplement 모두에 없다.

| 항목 | 재판정 | 근거 |
|---|---|---|
| I-015 | `[x]` | 평가된 re-ranking candidate의 score가 모두 non-negative라는 사실, predictor별 minimum과 maximum, sign-change 해석이 supplement의 `Observed ranges of source relation scores`에 명시돼 있다. Main claim은 이 세 evaluated predictor로 한정되므로 main에 같은 문장을 반복하는 것은 선택 사항이다. |
| I-016 | `[x]` | Table 3 caption이 agreement가 있을 때 label을 부여한다고 설명하고 M/D를 measured/decidable coverage로 푼다. Supplement는 disagreement를 uncertain으로 처리하고 denominator에 포함하는 규칙과 coverage 값을 명시한다. Main table의 비교 방향을 이해하는 데 필요한 정보는 이미 충분하다. |
| I-017 | `[x]` | `pair measurements`는 바로 뒤의 ordered-pair identity에 묶이고, `alternative geometric measure`는 두 representation을 결합한 하나의 audit measure를 가리킨다. Slash 표기와 `and` 표기는 의미 차이를 만들지 않는다. `exact consistency`도 applicable transformations로 범위가 제한돼 수식의 exact invariance와 맞는다. |
| I-018 | `[x]` | Related Work가 Recall@$K$를 `exact-match retrieval at a rank cutoff`으로 설명해 metric의 역할과 일치한다. |
| I-019 | `[x]` | Main prose의 interval claim은 supplement의 paired interval table과 일치하고, 바로 다음 문장에서 supplement가 두 variant와 다섯 \(K\) 값을 보고한다고 연결한다. 별도의 반복 pointer는 필요하지 않다. |
| I-020 | `[x]` | 현재 plain-roman relation phrase도 predicate와 rank를 명확히 전달한다. Quotation mark나 `\texttt`는 선택적 typography이며 과학적 명확성 문제는 아니다. |
| I-021 | `[x]` | 해당 문장은 `Datasets and Evaluation` subsection의 evaluation scope를 설명한다. Method는 별도로 `Training-split ground truth provides positives`와 evaluation rows 미사용을 명시한다. 두 문장을 함께 읽으면 split boundary가 명확하며 모순이 없다. |

### I-018. Recall@$K$ 설명의 정밀성 `[x]`

- 심각도: 사소
- Section: Related Work, Reliability Evaluation and Calibration
- 위치: `paper/aaai/sec/2_related_work.tex:18`

현재 해결 문장:

> Recall@$K$ measures exact-match retrieval at a rank cutoff rather than compatibility
> with reconstructed ordered-pair geometry.

현재 문장은 Recall@$K$가 개별 relation의 rank 자체가 아니라 top-\(K\) cutoff에서의
exact-match retrieval을 측정한다는 점을 정확히 설명한다. 추가 수정은 필요하지 않다.

### 선택적 보강이며 이슈로 세지 않는 항목

- Main Method에 source-score non-negativity pointer를 한 문장 넣는 것
- Main audit prose에 disagreement와 coverage denominator를 다시 정의하는 것
- `Ground-truth relations` 앞에 `Evaluation-split`을 추가하는 것
- Caption의 exact relation phrase에 quotation mark를 쓰는 것

이 네 항목은 넣어도 정확하지만, 현재 source와 supplement만으로도 의미와 protocol이
충분히 결정되므로 제출 전 필수 이슈나 우선순위 항목으로 취급하지 않는다.

## Section별 검토

### 전체 transcript 체크리스트

- `[x]` **용어 통일 여부:** core terms와 서로 다른 범위를 가리키는 audit
  표현이 일관된다. 가까운 표기 차이는 의미 구분을 해치지 않는다.
- `[x]` **Accept에 도움이 되는가:** failure cause, method necessity, controls,
  scoped claim이 직접 연결된다. SOTA나 broad generalization으로 넓히지 않는다.
- `[x]` **Reviewer 설득과 이해:** 전체 story는 충분하다. Score range와 audit의
  상세 operational rule은 supplement에 있고, split boundary는 Method와
  Experimental Setup에서 구분된다.
- `[x]` **Easy to read:** 문단별 역할이 분리되고 과도하게 긴 prose sentence가
  없다. Standard network parameter는 equation만으로도 충분히 이해할 수 있다.
- `[x]` **Straightforward:** problem, estimator, transformation, ranking,
  evaluation 순서가 곧바르다.

### 기존 문체와 source 체크리스트

| 항목 | 상태 | active section 기준 판단 |
|---|---|---|
| 모든 Figure와 Table의 본문 참조 | `[x]` | Figure 1--3과 Table 1--3을 본문에서 각각 한 번 이상 호출함 |
| Figure와 Table caption의 내용 설명 | `[x]` | Figure 1--3과 Table 1--3이 목적, 비교 대상, metric 또는 coverage 표기를 필요한 수준으로 설명함 |
| section별 첫 약어의 citation 존재 | `[x]` | Introduction, Related Work, Method, Experiments의 named predictor와 연구군에 citation이 존재함 |
| `A's B` 형태 | `[x]` | active prose에 해당 소유격 표현이 없음 |
| 용어 통일 | `[x]` | 핵심 용어는 일관되며 가까운 표기 차이는 서로 다른 문맥이나 동일한 의미 범위 안에 있음 |
| em dash | `[x]` | active prose에 em dash가 없음 |
| semicolon 남용 | `[x]` | prose에는 없고 feature-vector 수식의 구분 기호로만 사용함 |
| 긴 문장 | `[x]` | 즉시 분할해야 할 정도로 여러 논거가 뒤섞인 문장은 없음 |
| 수식의 임의 숫자 하드코딩 | `[x]` | loss는 \(m\), \(\lambda_{\rm pair}\), \(\lambda_{\rm reg}\)로 일반화하고 실제 값을 prose에서 명시함 |
| 하이퍼파라미터와 configuration 근거 | `[x]` | main은 공통값과 predictor-specific search 부재를 명시하고 sensitivity와 optimization details를 supplement로 연결함 |
| 수식 번호와 기호 정의 | `[x]` | equation 흐름과 핵심 기호는 일관되며 standard network parameter도 수식에서 역할이 명확함 |
| 간결한 contribution bullets | `[x]` | 세 항목이 각각 한 문장이고 task, estimator, ranking contribution으로 분리됨 |
| Introduction과 Related Work 중복 | `[x]` | Introduction은 motivation과 design necessity, Related Work는 문헌 대비를 담당하여 기능적 중복만 남음 |
| Introduction과 Related Work 분량 | `[x]` | 현재 압축된 문단 구성은 Method와 Experiments의 공간을 과도하게 침해하지 않음 |

### Abstract

- `[x]` **고유 용어의 최소 설명과 자기 완결성:** RelCompat3D를 re-ranking
  framework로 정의하고 ordered-pair identity, compatibility, estimator scope를
  최소한으로 설명한다.
- `[x]` **문제, 방법, 결과, 기여:** high-score mismatch, two estimators와
  re-ranking, three-predictor result, alternative audit가 모두 있다.
- `[x]` **Introduction contribution 세 개와 대응:** mismatch formulation,
  compatibility estimation과 transformations, family-aware re-ranking과
  evaluation이 과부족 없이 대응한다.
- `[x]` **Hedging과 overclaiming:** `reported predictor--K settings`와
  `point estimates`가 statistical scope를 제한한다.
- `[x]` **문장당 정보량:** 두 metric을 함께 설명해야 하는 result sentence를
  제외하면 각 문장이 하나의 역할을 가진다.
- `[x]` **Citation과 기호:** citation이 없고 정의되지 않은 수학 기호도 없다.
- `[x]` **표현 일관성:** `predicate-independent pair measurements`는 앞선
  ordered-pair identity에 결합되어 의미가 명확하고 transformation sentence도
  relation-preserving scope를 직접 한정한다.

### Introduction

- `[x]` **현재 claim을 명시적으로 제안하는 문장:** line 20의
  `We propose RelCompat3D` 문단이 task, inputs, source-score exclusion,
  estimators, training, transformations를 명시한다.
- `[x]` **선행연구 citation 존재:** 언급된 연구군과 predictor에 citation이 있다.
- `[x]` **Contribution 세 개와 Method 대응:** Contribution 1은 Problem
  Formulation과 Metrics, Contribution 2는 Compatibility Estimation,
  Contribution 3은 Family-Aware Re-Ranking과 cross-predictor evaluation에
  대응한다. Literal subsection 이름보다 기능적 1:1 대응이 명확하므로 별도
  재작성은 필요하지 않다.
- `[x]` **Method 전용 용어 정의:** \(T,G,Z\), counterfactual과 transformation의
  차이, re-ranking scope가 Method 전에 필요한 수준으로 설명된다.
- `[x]` **논리 흐름:** downstream need, observed failure, score limitation,
  compatibility design, ranking, evaluation, contributions 순서가 자연스럽다.
- `[x]` **Experiment 수치와 일치:** 모든 다섯 \(K\)에서 두 variants의 Recall
  point estimate는 Source보다 낮지 않고 Violation은 높지 않다. SGFN \(K=5\)
  tie도 `match or improve`, `match or reduce`에 포함된다.
- `[x]` **Hedging 일관성:** `point estimates`, shared target, alternative audit
  표현이 Results와 Discussion의 범위와 맞는다.
- `[x]` **Caption과 용어:** exact relation phrase와 ordered-pair 표현은 현재
  문맥에서 충분히 구분된다.

### Related Work

- `[x]` **모든 선행연구 citation 존재:** named method와 연구군에 citation이 있다.
  사용된 44개 citation key도 bibliography에 존재한다.
- `[x]` **구체적 차별점:** generation 대 fixed-candidate re-ranking,
  generator-internal geometry 대 post-source compatibility,
  calibration 대 predicate--geometry compatibility로 차이를 설명한다.
- `[x]` **분량과 깊이 균형:** 3D prediction, geometry evidence,
  reliability/calibration이 각각 두 문단 수준으로 균형을 이룬다.
- `[x]` **소제목과 내용 정합:** 각 subsection의 문헌군과 마지막 대비 문장이
  제목에 맞는다.
- `[x]` **Introduction과 용어 일관성:** source relation score, ordered pair,
  fixed candidates, exact-match Recall, verifier-derived Violation을 유지한다.
- `[x]` **subsection 간 중복:** fixed generator 대비가 두 번 나오지만 closed-set과
  open-vocabulary 흐름을 각각 닫는 역할이라 과도한 중복이 아니다.
- `[x]` **Metric 설명:** Recall@$K$를 `retrieval at a rank cutoff`으로
  설명해 metric 정의와 일치한다.

### Method

- `[x]` **Notation 일관성과 재정의:** \(T,G,Z,a,q,C,C^{\rm tr},u,\pi\)는
  일관된다. Transformation set은 support/contact까지 닫혔고 source position의
  family \(a_j\)도 해당 문장에서 직접 정의된다.
- `[x]` **Introduction의 설계 선택 대응:** ordered-pair identity와 score
  separation은 Problem Formulation, transformations와 counterfactual learning은
  Compatibility Estimation, constrained routing은 Family-Aware Re-Ranking에
  대응한다.
- `[x]` **새 용어의 최초 정의:** OBB, sigmoid, MLP, loss symbols는 처음 등장할 때
  정의된다. \(W,b,v,b_o,\beta\)는 standard network notation이며 equation에서
  역할이 명확하다.
- `[x]` **재현 가능성:** native score type, feature family, network width,
  loss, margin, weights, split boundary가 main에 있다. Complete construction,
  optimizer, proof는 supplement pointer가 있다.
- `[x]` **가정 선언:** fixed candidates, known geometry, evaluation and
  ranking families, support/contact boundary, no cross-predictor score
  comparison이 명시된다. Evaluated source-score 범위와 non-negative 조건은
  supplement에 수치로 보고된다.
- `[x]` **수식과 텍스트 정합:** support/contact identity transformation,
  compatibility averaging, product score, family-subsequence algorithm은
  prose와 일치한다.

### Experiments

- `[x]` **세 설계 선택에 대응하는 ablation:** source-score role은
  Compatibility only, ordered-pair association은 Wrong pair와 Shuffled
  geometry, transformation role은 Fixed-predicate swap과 supplement의 direct
  removal로 점검한다.
- `[x]` **공정한 비교:** candidate universe, split, targets, objective,
  family-aware ranking은 동일하고 predictor별 refitting을 하지 않는다.
- `[x]` **training/evaluation boundary:** Method는 training-split positives와
  evaluation rows 미사용을 명시하고, Experimental Setup은 evaluation subsection
  안에서 ground truth의 Recall-only 사용을 설명한다.
- `[x]` **통계 주장과 수치:** \(K=50\) interval 문장, all-\(K\) point-estimate
  문장, SGFN tie, Open3DSG largest-change 문장이 table과 scan-bootstrap
  artifact에 일치한다.
- `[x]` **검증 범위 일관성:** \(K\in\{5,10,20,50,100\}\), 세 predictor,
  shared 3DSSG/3RScan target, 세 evaluation family가 일관된다.
- `[x]` **Metric 정의 위치와 사용:** Recall과 Violation은 Metrics에서 한 번
  정의되고 이후 같은 이름과 방향으로 사용된다.
- `[x]` **실패 사례와 약한 지점:** Open3DSG high-Violation case,
  support/contact non-re-ranking, comparator trade-offs, metric overlap이
  숨겨지지 않는다.
- `[x]` **caption 자기 완결성:** Figure 1--3과 Table 1--3은 목적, metric,
  methods, direction 또는 단위를 필요한 수준으로 설명한다. Table 3은 agreement
  rule과 M/D 명칭을 제공하고, 상세 denominator는 supplement에 있다.
  `\textbf` 형식은 이번 내용 검토에서 제외했다.
- `[x]` **모든 Figure와 Table 본문 참조:** Figure 1--3과 Table 1--3이 각각
  최소 한 번 본문에서 호출된다.
- `[x]` **qualitative evidence:** Figure 1의 demotion과 supplement에 기록된
  promotion을 main Results에서 구분해 설명한다. 두 relation family의 직접 교환으로
  표현하지 않는다.
- `[x]` **audit 해석:** main point estimates와 supplement intervals가 정확하며,
  main caption과 supplement를 함께 보면 agreement, uncertainty, coverage
  definition이 모두 결정된다.

### Discussion and Limitations

- `[x]` **scope 일관성:** one shared target, known instances, reconstructed
  ordered-pair geometry, support/contact source order가 Method와 일치한다.
- `[x]` **통계 주장 정확성:** 이 section은 새로운 significance나 수치를
  주장하지 않는다.
- `[x]` **자기비판의 균형:** dataset generalization과 independent ground truth
  한계를 밝히지만 main result 자체를 부정하는 표현은 없다.
- `[x]` **실패 사례의 정직성:** richer contact/pose evidence가 필요한 범위와
  alternative audit의 한계를 명시한다.
- `[x]` **중복 관리:** primary verifier와 OBB overlap은 바로 앞 Results에서
  설명되고, Discussion은 dataset와 ground-truth boundary만 요약한다. 같은 내용을
  반복해서 늘릴 필요가 없다.

### Conclusion

- `[x]` **Introduction contribution과 관계:** compatibility separation,
  applicable-family ranking, three-predictor result를 한 번에 요약하되
  contribution bullet을 그대로 반복하지 않는다.
- `[x]` **새 주장이나 수치:** Method와 Experiments에 없는 내용이 없다.
- `[x]` **Overclaiming:** `lower or tied`, `preserving or improving`,
  `point estimates`, `one shared target`이 기존 hedging과 일치한다.
- `[x]` **motivating problem과 연결:** high-scoring predicate와 reconstructed
  ordered-pair geometry의 conflict로 돌아가 마무리한다.
- `[x]` **Future work:** Conclusion에는 별도 future-work 문장이 없다.
  실제 한계와 다음 단계는 Discussion에서 이미 자연스럽게 제시되므로 추가할
  필요가 없다.

## Introduction claim과 evidence 연결

| Introduction claim 또는 design | Method 대응 | Experiment 대응 | 판단 |
|---|---|---|---|
| high score와 ordered-pair geometry의 mismatch | Problem Formulation과 compatibility definition | Figure 1, Table 1, Figure 3 | `[x]` |
| source relation score와 compatibility 분리 | \(C_i^q\)에서 \(Z_i\) 제외 | Compatibility only, RankAvg, RRF | `[x]` |
| ordered-pair identity 보존 | pair identity와 exact candidate identity | Wrong pair, Shuffled geometry | `[x]` |
| linked counterfactual ordering | linked loss | supplement direct removal과 sensitivity | `[x]` |
| transformation consistency | \(H_a\), orbit, averaging | Fixed-predicate swap, exact checks, direct removal | `[x]` |
| family-aware re-ranking | \(u_i^q\)와 family subsequence | Table 1, Product (all families), family metrics | `[x]` |
| alternative geometric measurements | audit protocol | Table 3와 supplement all-\(K\) audit | `[x]` |

Introduction에서 강조하지만 실험 근거가 없는 central claim은 없다. 반대로 main
experiment 중 Introduction에서 전혀 예고되지 않은 central evidence도 없다.

## Figure와 Table 점검

| Artifact | 본문 참조 | 내용과 caption | 남은 조치 |
|---|---|---|---|
| Figure 1 | Introduction과 Results | failure, measured evidence, Source와 Linear rank change를 설명 | Author Kit-1 |
| Figure 2 | Method | compatibility input, score 결합 시점, within-family outcome을 설명 | 없음 |
| Figure 3 | Results | metrics, five \(K\), three ranking rules, preferred direction, axis 차이를 설명 | Author Kit-1 |
| Table 1 | Results | target, metrics, Source, methods, family scope를 설명 | deferred overfull |
| Table 2 | Ablations | Linear controls, MLP full row, metrics, \(K\), shared route를 설명 | deferred overfull |
| Table 3 | Audit | alternative labels, delta, measured/decidable coverage를 설명 | 없음 |

Figure 3와 Table 2에 shared-target 문장을 다시 넣을 필요는 없다. Experimental
Setup과 Table 1이 공통 평가 범위를 정의하고 두 artifact는 같은 Results 흐름에서
해석된다.

## Author Kit과 release 상태

형식 판단은 local official source
`paper/aaai/official/AnonymousSubmission2027.tex`의 graphics, caption, overflow
지침을 기준으로 했다. AI-system disclosure 판단은
[AAAI Publication Policies and Guidelines](https://aaai.org/aaai-publications/aaai-publication-policies-guidelines/)
를 기준으로 했다.

### Author Kit-1. `trim`과 `clip` `[ ]`

Current active source에서 다음 두 Figure만 해당한다.

- Figure 1: `paper/aaai/sec/1_introduction.tex:6--10`
- Figure 3: `paper/aaai/sec/4_experiments.tex:67--71`

AAAI-27 Author Kit은 crop을 LaTeX 밖에서 수행하고 `trim`과 `clip`을 사용하지
말라고 명시한다. Figure 2에는 해당 option이 없으므로 이전 feedback의 Figure 2
지적은 해결됐다.

### Author Kit-2. Caption manual bold `[제외]`

사용자 요청에 따라 `\textbf` 형식 문제는 이번 section별 내용 검토와 우선순위에서
제외했다. Caption이 전달하는 정보와 본문 연결만 검토했다.

### Author Kit-3. Page와 overflow `[보류]`

- 2026-07-25 19:44 KST의 selected PDF는 9 pages다.
- 해당 PDF에서 technical content는 page 7에 끝나고 pages 8--9는 references다.
- 이후 qualitative paragraph가 source에 추가됐으므로 final rebuild 검증이 필요하다.
- 최신 확인 log에는 first-page vertical overfull \(36.77646\) pt와 Table 2
  horizontal overfull \(4.4306\) pt가 남아 있다.
- 사용자가 현재 layout을 유지하고 마지막 단계에서 처리하기로 했으므로 보류한다.
  최종 submission 전에 margin과 gutter intrusion 여부를 다시 확인해야 한다.

### Author Kit-4. AI-system role disclosure `[ ]`

AAAI publication policy는 publication 개발에 사용한 AI system의 역할을 manuscript에
기록하도록 한다. 현재 active main section에는 해당 문장이 없다. 실제 사용 범위를
반영한 짧은 disclosure를 Conclusion 뒤, References 앞에 둘 필요가 있다.

### Author Kit-5. Main과 supplement title casing `[x]`

Main과 supplement 제목을 모두 `Re-Ranking`으로 통일했다. Paper-facing planning
documents에도 같은 title casing을 반영했다. Supplement smoke build는 11-page
US Letter PDF를 생성했으며 undefined reference, undefined citation, overfull
warning은 없었다.

### Author Kit-6. Reproducibility checklist의 theoretical contribution `[~]`

Checklist는 exact transformation consistency와 family-sequence preservation을
근거로 theoretical contribution에 `yes`라고 답한다. Main paper는 이를 standard
implementation guarantee로 사용하고 theorem novelty로 전면화하지 않는다.
별도 이론 기여를 주장하지 않는 최종 framing이라면 `no`가 더 일관된다.

## 제출 전 우선순위

### P0: transcript correctness

현재 확인된 blocking transcript correctness 이슈는 없다.

### P1: reviewer readability

현재 확인된 필수 reviewer-readability 수정은 없다.

### P2: final submission format

1. Figure 1과 Figure 3의 `trim`과 `clip`을 asset-side crop으로 바꾼다.
2. AI-system role disclosure를 실제 사용 범위에 맞게 추가한다.
3. user decision에 따라 보류한 overflow를 최종 점검한다.
4. 최종 rebuild에서 9 pages, pages 8--9 references only, no undefined
   references/citations를 확인한다.

## 최종 reviewer 관점

현재 transcript의 strongest acceptance argument는 단순한 geometry fusion이 아니다.
Fixed candidate score와 ordered-pair compatibility의 역할을 분리하고, pair identity,
applicable transformation consistency, family scope를 controls로 검증한다는 점이다.
Linear와 MLP가 서로 다른 operating point를 제공하면서도 Source 대비 같은 방향의
point-estimate 변화를 보인다는 점도 framework-level claim을 지지한다.

가장 큰 scientific risk는 single shared target과 constructed verifier dependence다.
현재 manuscript는 이를 dataset-level generalization이나 independent physical
validity로 확대하지 않으므로 claim은 방어 가능하다. I-015--I-021 재판정에서
scientific correctness 또는 reproducibility를 막는 새 이슈는 확인되지 않았다.
