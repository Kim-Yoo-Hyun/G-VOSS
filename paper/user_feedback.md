# RelCompat3D Active-Section 통합 재검토

- 검토일: 2026-07-27 KST
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
- Main teaser source는 Docker에서 다시 빌드했다. 최신 disposable
  `main_teaser.pdf`는 9-page US Letter이며 undefined reference/citation은 없다.
  Technical artifacts는 pages 1--7, references는 pages 8--9에 있다.
  Canonical `main_teaser_aaai27.pdf`는 덮어쓰지 않았다. Supplement는 용어 동기화
  와 direct component/five-seed diagnostics 반영 후 Docker build를 통과했다.
  Canonical supplement는 18-page US Letter이며 unresolved reference와
  LaTeX/overfull warning이 없다.

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
| I-006 | `[x]` | MLP 첫 정의는 Introduction의 `shared nonlinear estimator`와 Method line 41의 `multilayer perceptron (MLP)`으로 정리됨 |
| I-007 | `[x]` | Method subsection 명칭은 `Compatibility Estimation`으로 수정됨 |
| I-008 | `[x]` | `corresponding results`는 `these additional metrics`로 구체화됨 |
| I-009 | `[x]` | Introduction과 Related Work에 중복돼 있던 이전 원고 주석 및 qualitative paragraph의 obsolete 주석 버전이 삭제됨 |
| I-010 | `[x]` | Main Results에 demotion과 promotion을 함께 설명하고 supplement에는 promotion 근거를 prose로 기록함 |
| I-011 | `[x]` | Table 3 caption이 \(K\), agreement rule, \(\Delta V\), M/D의 명칭과 단위를 설명함. `\textbf` 형식은 이번 내용 검토에서 제외 |
| I-012 | `[x]` | support/contact에 \(H_a=\{e\}\)를 정의하고 all-family comparison의 역할을 명시함 |
| I-013 | `[x]` | 세 predictor의 evaluated score가 모두 non-negative이며 정확한 범위와 product sign 해석이 supplement에 존재함. 현재 scoped claim에는 main 반복이 필수적이지 않음 |
| I-014 | `[x]` | Linear/MLP의 matched component removal, linked-pair margin 분포, transformation error 분포, transformed-view top-\(K\) consistency가 supplement에 있고 main pointer도 유지됨 |

## I-015--I-021 엄격 재판정

이번 재판정에서는 다음 세 조건 중 하나를 만족할 때만 미해결 이슈로 남겼다.

1. 현재 문장이 사실 또는 수치와 다르다.
2. Main claim과 실제 method 또는 evidence가 어긋난다.
3. 재현이나 핵심 표의 해석을 막는 정보가 main과 supplement 모두에 없다.

| 항목 | 재판정 | 근거 |
|---|---|---|
| I-015 | `[x]` | 평가된 re-ranking candidate의 score가 모두 non-negative라는 사실, predictor별 minimum과 maximum, sign-change 해석이 supplement의 `Observed ranges of source relation scores`에 명시돼 있다. Main claim은 이 세 evaluated predictor로 한정되므로 main에 같은 문장을 반복하는 것은 선택 사항이다. |
| I-016 | `[x]` | Table 3 caption이 agreement가 있을 때 label을 부여한다고 설명하고 M/D를 measured/decidable coverage로 푼다. Supplement는 disagreement를 uncertain으로 처리하고 denominator에 포함하는 규칙과 coverage 값을 명시한다. Main table의 비교 방향을 이해하는 데 필요한 정보는 이미 충분하다. |
| I-017 | `[x]` | `pair measurements`는 ordered-pair identity에 묶여 있고 Introduction은 `using alternative geometric measurements`로 문법과 audit 표현을 통일했다. `exact consistency`도 applicable transformations로 범위가 제한돼 수식의 exact invariance와 맞는다. |
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
| Figure 1 | Introduction과 Results | failure, measured evidence, Source와 Linear rank change를 설명 | Author Kit-3 |
| Figure 2 | Method | compatibility input, score 결합 시점, within-family outcome을 설명 | 없음 |
| Figure 3 | Results | metrics, five \(K\), three ranking rules, preferred direction, axis 차이를 설명 | 없음 |
| Table 1 | Results | target, metrics, Source, methods, family scope를 설명 | 없음 |
| Table 2 | Ablations | Linear controls, MLP full row, metrics, \(K\), shared route를 설명 | horizontal overfull 해결 |
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

### Author Kit-1. External crop과 `trim`/`clip` `[x]`

Active source는 `paper/reference_AAAI/figure/`의
`Figure1_outlined_v15.pdf`, `Figure2_outlined_v15.pdf`,
`Figure3_outlined_v15.pdf`를
직접 사용한다.
세 `\includegraphics`에는 `width`만 있고 `trim`, `clip`, `viewport`는 없다.
각 PDF의 MediaBox와 CropBox가 일치하고, rendered content는 각 edge에서 약
2--3 pt 이내에 시작한다. 따라서 Author Kit이 금지하는 LaTeX-side crop 문제는
해결됐다.

각 outlined asset의 `pdffonts` 결과는 빈 목록이며, rebuilt
`main_teaser.pdf` 전체에서도 CID, Identity-H, Type 3 font가 검출되지 않았다.
따라서 figure font 문제는 해결됐다.

세 v15 asset과 rebuilt manuscript는 모두 PDF 1.5다. Forced Docker rebuild의
log에는 `inclusion: found PDF version`, `PDF inclusion`, 또는 그 밖의 graphics
inclusion warning이 없다. 이전 PDF 1.7 asset에서 발생하던 inclusion warning도
해결됐다.

### Author Kit-2. Caption manual bold `[x]`

Official Author Kit은 Figure와 Table caption을 10-point roman으로 두고 bold 또는
italic caption으로 만들지 말라고 명시한다. 현재 main section의 Figure 1--3과
Table 1--3 caption에는 manual `\textbf` 또는 `\bf`가 없다. Table cell에서 best
score와 proposed method를 표시하는 bold는 caption formatting과 별개다. 따라서
caption manual-bold 이슈는 해결됐다.

### Author Kit-3. First-page vertical overfull `[보류]`

- `user_v6.tex`의 float 선언 순서와 Figure 3의 `[!t]` 배치를 복원한 fresh Docker
  build는 9 pages다. Table 1과 Figure 3은 page 6, Table 2와 Table 3은 page 7에
  있다. Technical content가 page 7에서 끝난 뒤 references가 같은 페이지에서
  시작하고 pages 8--9로 이어진다.
- 따라서 Figure/Table 내부 글자 크기, line width, caption을 줄이지 않는다.
- Table 2의 기존 horizontal overfull은 해소됐다.
- 남은 page-layout 문제는 첫 페이지의
  `Overfull \vbox (36.77646pt too high)`다.
- Figure 1을 축소하거나 caption을 한 줄로 줄여도 같은 수치가 발생하고 Figure 1을
  제거하면 사라진다. 일반적인 figure-height 문제가 아니라 첫 페이지 one-column
  float와 anonymous copyright output routine의 상호작용으로 판단한다.
- Style/layout 우회 명령, negative spacing, caption 축소는 사용하지 않는다.

다음 단계는 pristine official `aaai2027.sty`로 minimal example을 재현한 뒤 동일하면
AAAI publication support에 문의하는 것이다. 첫 페이지 Figure 1을 유지하는 조건
아래에서는 warning을 숨기거나 무시하지 않는다.

### Author Kit-4. AI-system role disclosure `[ ]`

AAAI publication policy는 publication 개발에 사용한 AI system의 역할을 manuscript에
기록하도록 한다. 현재 active main section에는 해당 문장이 없다. 실제 사용 범위를
반영한 짧은 disclosure를 Conclusion 뒤, References 앞에 둘 필요가 있다.

실제 사용 범위를 authors가 최종 확인한 뒤 다음처럼 두 문장으로 기록할 수 있다.

> Generative AI tools were used to assist with language editing, code
> development, and document-format checks. The authors verified all generated text, code,
> citations, and reported results and take full responsibility for the
> submission.

### Author Kit-5. Main과 supplement title casing `[x]`

Main과 supplement 제목을 모두 `Re-Ranking`으로 통일했다. Paper-facing planning
documents와 Method subsection의 `Family-Aware Re-Ranking`에도 같은 title casing을
반영했다. Supplement smoke build는 11-page US Letter PDF를 생성했으며 undefined
reference, undefined citation, overfull warning은 없었다.

### Author Kit-6. Reproducibility checklist의 theoretical contribution `[x]`

Current checklist는 theoretical contribution에 `no`라고 답하고 하위 이론 문항을
`NA`로 처리한다. Main paper가 transformation consistency와 family-sequence
preservation을 standard method guarantee로 사용하고 별도 theorem novelty를
주장하지 않는 framing과 일치한다.

### Author Kit-7. Active TeX 정적 규정 검사 `[x]`

`main_teaser.tex`가 불러오는 `main.tex`, `preamble.tex`, 그리고
`sec/0_abstract.tex`--`sec/6_conclusion.tex`만 대상으로 다시 검사했다.

- 문서는 `letterpaper`, `aaai2027`의 `submission` mode, anonymous author
  information을 사용한다.
- Author Kit의 금지 package, font package, page-layout command, negative
  spacing, `trim`, `clip`, `viewport`, `resizebox`, 수동 caption font 변경은 없다.
- 표의 세 `\setlength{\tabcolsep}{...}`는 Author Kit가 명시적으로 허용한
  `\tabcolsep` 예외다. 표는 `\small`인 9-point 하한을 지키며 전체 표를
  강제 축소하지 않는다.
- Figure와 Table caption은 모두 artifact 아래에 있고 manual `\textbf` 또는
  `\bf`가 없다.
- Forced rebuild는 9-page US Letter PDF 1.5를 생성한다. Technical content와
  모든 main Figure/Table은 pages 1--7에 있고 references만 pages 8--9에 있다.
- Undefined citation/reference, BibTeX warning, graphics inclusion warning,
  horizontal overfull은 없다. Final PDF의 모든 문서 font는 embedded/subset
  Type 1이며 CID, Identity-H, Type 3 font는 없다.

이 정적 검사와 별개로 남은 제출 이슈는 Author Kit-3의 first-page vertical
overfull과 Author Kit-4의 AI-system role disclosure다. Log의 underfull box는
margin 침범을 뜻하지 않으며 현재 제출 위반으로 판정하지 않는다.

## AAAI-27 deadline-mail 제출 체크리스트

2026-07-26 KST에 전달된 deadline reminder를
[Main Technical Track Call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/),
[Submission Instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/),
[Supplementary Material Guidelines](https://aaai.org/conference/aaai/aaai-27/supplementary-material/),
그리고
[AAAI Publication Policies](https://aaai.org/aaai-publications/aaai-publication-policies-guidelines/)
와 대조했다.

상태 표기에서 `[x]`는 local artifact로 확인 완료, `[~]`는 일부 완료 또는 final
bundle 재생성 필요, `[ ]`는 제출 전 조치 필요, `[사용자 확인]`은 repository만으로
판정할 수 없는 항목을 뜻한다.

| Mail/Call 항목 | 상태 | 현재 판정과 제출 전 조치 |
|---|---|---|
| Full-paper deadline | `[x]` | 2026-07-28 23:59 UTC-12다. KST로는 2026-07-29 20:59이며 연장은 없다. |
| Supplement/code deadline | `[x]` | 2026-07-31 23:59 UTC-12다. KST로는 2026-08-01 20:59이다. Main deadline 이후에는 supplement와 code만 갱신할 수 있다. |
| Main page limit | `[~]` | Current build는 9-page US Letter이며 technical content는 pages 1--7, pages 8--9는 references only다. Page allocation은 통과하지만 Author Kit-3의 first-page overfull을 해결해야 최종 통과다. |
| Anonymous main PDF | `[x]` | `Anonymous Submission`, 빈 affiliations, acknowledgements 없음, 저자·기관·이메일·로컬 경로가 PDF text/metadata에서 검출되지 않았다. |
| Anonymous technical supplement | `[x]` | Current source를 `/tmp`에서 fresh build한 11-page supplement는 anonymous이며 저자·기관·acknowledgements·자체 웹 링크가 검출되지 않았다. Supplement에는 별도 page limit이 명시되지 않는다. |
| Anonymous reproducibility checklist | `[x]` | Current checklist는 2-page standalone PDF로 완성되어 있고 placeholder answer가 남아 있지 않다. 저자 식별 정보도 없다. OpenReview의 지정 field에 main과 별도로 업로드해야 한다. |
| Self-citation anonymity | `[사용자 확인]` | Active prose에는 `our previous work`, `we previously` 같은 자기 식별 표현이 없다. 다만 실제 author list를 알 수 없으므로 bibliography의 저자 논문이 포함돼 있다면 모두 제3자 문체로 서술됐는지 최종 author-side 대조가 필요하다. |
| 저자 소유 웹 자료 링크 금지 | `[x]` | Main, fresh supplement, checklist PDF에는 URL annotation이 없고 source에도 project page, anonymous GitHub, Hugging Face repository 링크가 없다. 기존 공개 dataset/library를 bibliographic citation으로 인용하는 것은 허용된다. |
| Code/Data Supplement 직접 업로드 | `[x]` | `release/relcompat3d_aaai27_openreview_20260726_214500/code_and_data_supplement.zip`을 current main/supplement에 맞춰 재생성했다. ZIP은 약 3.0 MB이며 184개 manifest-verified payload를 포함한다. Current `src/relcompat3d`, Docker/Compose, frozen protocols와 model locks, compact CSV/JSON evidence, exact paper/supplement source, v15 outlined figures만 allowlist로 담았다. `old.tex`, `user_v*`, historical release, Git metadata, logs, raw rows, dataset, checkpoint는 제외했다. |
| README anonymity | `[x]` | 새 ZIP의 anonymous README는 archive map, reproduction boundary, external-input requirement만 설명한다. 저자·기관·이메일·자체 웹 링크·host absolute path·historical release path는 검출되지 않았다. Frozen `held_out_primitive.json`에는 비식별 실행 provenance인 `first_run_log` 문자열 하나가 남지만 log 파일이나 저자 정보는 포함되지 않는다. |
| Main의 self-contained evidence | `[x]` | Main에 task, method, primary metrics, all-\(K\) result, ablations, alternative geometry audit가 있다. Supplement가 없어도 central claim을 평가할 수 있으며 supplement는 세부 규칙과 확장 결과를 보강한다. |
| Reproducibility materials at submission | `[x]` | Main, 11-page technical supplement, 2-page checklist, code/data ZIP을 동일 source 시점에서 재생성했다. ZIP 해시, JSON 83개, Python compilation, Docker Compose, active method/model hashes, extracted-source main/supplement/checklist rebuild를 모두 검증했다. |
| Generative-AI use policy | `[ ]` | AAAI는 AI system 사용 역할을 manuscript에 기록하도록 한다. 현재 disclosure가 없으므로 Author Kit-4의 실제 사용 범위에 맞는 문장을 7 content pages 안에 추가해야 한다. AI system은 author 또는 citable source로 두지 않으며 모든 내용은 저자가 검증하고 책임져야 한다. |
| Ethics violations policy | `[사용자 확인]` | 별도 Ethics 섹션이 모든 paper에 의무라는 지침은 확인되지 않았다. 다만 plagiarism/self-plagiarism, fabricated content/reference, prompt injection, reciprocal-review coordination, duplicate/near-duplicate submission이 없음을 authors가 확인해야 한다. 이 연구 범위에는 human-subject 또는 sensitive-personal-data 실험이 보이지 않아 별도 ethics-study statement를 추가할 근거는 현재 없다. |
| Simultaneous/overlapping submission | `[사용자 확인]` | Full-paper deadline 시점에 같은 또는 substantially similar work가 다른 archival venue의 review/accepted/published 상태이면 안 된다. 다른 review에서 철회했다면 AAAI 제출 전에 철회가 완료돼야 한다. Overlapping-author AAAI submissions도 독립 기여인지 확인해야 한다. |
| OpenReview author list/order | `[사용자 확인]` | 모든 author의 profile, 순서, institutional email, conflict, reviewer eligibility를 full-paper deadline 전에 확정한다. 제출 후 author 추가·변경을 전제로 하면 안 된다. |
| Submission count/reviewer pool | `[사용자 확인]` | Author별 Main Technical Track 제출 수가 10편 이하인지, qualified author가 reviewer pool 의무를 충족하는지 확인한다. |
| Live title/abstract/TL;DR consistency | `[사용자 확인]` | 새 `submission_metadata.md`의 title과 abstract는 current source에서 동기화했고 TL;DR도 current one-sentence version으로 갱신했다. OpenReview live form이 이 세 항목과 일치하는지, abstract-submission 버전 대비 허용 범위인지 authors가 최종 확인해야 한다. |
| Final upload timing and receipt | `[사용자 확인]` | 마지막 한 시간 제출을 피하고, 업로드 뒤 paper ID에서 PDF를 다시 열어 모든 페이지를 확인한다. 필요하면 OpenReview의 Email 기능으로 receipt를 보낸다. |

### Deadline-mail 검사에서 확인된 artifact 상태

- Current synchronized candidate:
  `release/relcompat3d_aaai27_openreview_20260726_214500/`.
- `main.pdf`는 9-page US Letter PDF 1.5, `technical_supplement.pdf`는
  11 pages, `reproducibility_checklist.pdf`는 2 pages다.
- 세 PDF는 anonymous이고 URL annotation이 없으며, embedded/subset Type 1
  document font만 사용한다. Included v15 figure PDFs에는 font object가 없다.
- Outer manifest 6개와 ZIP internal manifest 184개를 검증했다. ZIP에서 extracted
  source를 Docker로 다시 빌드했을 때 page count와 extracted text가 release PDF와
  일치했다.
- Main의 유일한 overfull은 Author Kit-3의 first-page vertical overfull이다.

### Build-1. BibTeX metadata warning `[x]`

사용자의 판단에 동의한다. AAAI OJS의 공식 metadata가 journal-style인 것은
사실이지만, 제출 manuscript의 bibliography 형식은 AAAI Author Kit과
`aaai2027.bst`의 proceedings convention을 우선하는 편이 안전하다.

따라서 `fei2026open`, `liu2026view`, `ma2026edge`는 `@inproceedings`로 유지하고
`booktitle`, `volume`, `pages`, `year`를 사용하며 `number`는 제외한다. 이는
Author Kit의 “Proceedings paper published by a society, press or publisher”
예시와 bibliography 전체의 형식을 일치시킨다.

현재 `paper/references.bib`가 이미 이 형식이며, fresh main build의 `.blg`에는
세 entry에 대한 `volume`/`number` warning이나 다른 BibTeX warning이 없다.

## 제출 전 우선순위

### P0: transcript correctness

현재 확인된 blocking transcript correctness 이슈는 없다.

### P1: reviewer readability

현재 확인된 필수 reviewer-readability 수정은 없다.

### P2: final submission format

1. Pristine Author Kit과 minimal example로 first-page vertical overfull을 재현하고
   필요하면 AAAI publication support에 문의한다.
2. AI-system role disclosure를 실제 사용 범위에 맞게 추가한다.
3. OpenReview의 author list/order, live title, abstract, TL;DR, conflict와 reviewer
   profile을 deadline 전에 확정한다.
4. 다른 archival venue의 simultaneous/overlapping submission이 없음을 authors가
   확인한다.
5. 최종 rebuild에서 US Letter, 7 technical pages, references-only 이후 페이지,
   no overfull, no undefined references/citations를 확인한 뒤 canonical PDF를
   갱신한다.

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

## TL;DR
RelCompat3D re-ranks fixed 3D scene graph predictions using predicate–geometry compatibility, yielding non-decreasing Recall and non-increasing verifier-derived Violation point estimates across three predictors.

## AAAI 2027 adversarial reviewer review

이 절은 기존 proofreading checklist와 다른 목적을 가진다. 저자를 방어하지 않고,
AAAI reviewer가 reject 근거로 사용할 수 있는 scientific weakness를 최대한 강하게
해석한다. 기존 형식 검토의 “blocking transcript correctness 이슈 없음”은 수식이나
서술의 명백한 오류가 없다는 뜻이며, 아래 novelty, significance, construct validity
평가를 대체하지 않는다.

Release 정리 상태는 다음과 같다. 이전 `release/` 항목은 모두 삭제했고
`release/relcompat3d_aaai27_openreview_20260726_214500/`만 남겼다.

### 기준별 체크리스트

표기에서 `[x]`는 충족, `[~]`는 부분 충족, `[ ]`는 reject 위험이 남음을 뜻한다.

#### Soundness

- `[x]` Candidate identity, ranking utility, metric은 수식으로 정의된다.
- `[x]` Evaluation rows와 verifier-status labels를 training에 사용하지 않는다고
  명시한다.
- `[~]` Point/mesh audit, feature-removal analysis, uncertainty-policy checks,
  dependency matrix로 construct dependence를 명시하고 완화한다.
- `[ ]` 핵심 Violation metric에 독립적인 human 또는 physical-validity ground
  truth가 없다.
- `[ ]` Training counterfactual과 primary verifier가 OBB measurements와 일부
  threshold를 공유한다.
- `[~]` \(u=ZC^{tr}\)는 score-scale invariant하지 않지만, canonical pool의
  고정-grid sensitivity에서 다섯 smooth non-identity mapping 중 Linear 75/75,
  MLP 74/75 predictor--\(K\) 조건이 Source 대비 유리한 point-estimate 방향을
  유지한다. Percentile condition의 작은 Recall 손실은 명시적으로 남긴다.
- `[~]` 모든 \(K\)에 대한 주장은 point estimate로 제한되지만 통계적 지지는
  predictor와 \(K\)에 따라 다르다.
- `[~]` Matched component diagnostics가 aggregate effect와 direct mechanism을
  분리한다. Pairwise term은 small, estimator-dependent regularizer이고,
  transformation averaging은 두 estimator에서 transformed compatibility와
  top-\(K\) membership을 정확히 같게 만든다. 따라서 aggregate-gain 원인으로
  과장하지 않는 bounded claim이 필요하다.

#### Significance

- `[x]` High-scoring relation이 reconstructed geometry와 충돌할 수 있다는 문제는
  실제 downstream risk와 연결된다.
- `[~]` Open3DSG에서는 큰 변화가 관찰된다.
- `[ ]` VL-SAT과 SGFN의 Recall 개선은 매우 작거나 일부 \(K\)에서 정확히 0이다.
- `[ ]` Downstream task에서 개선된 graph가 실제 reasoning 또는 navigation 성능을
  높이는지 검증하지 않는다.
- `[ ]` Support/contact, reference-frame relations, missing candidate generation을
  해결하지 못한다.
- `[ ]` 세 predictor가 모두 하나의 3DSSG target에서 평가되어 문제의 일반성이
  충분히 입증되지 않는다.

#### Novelty

- `[x]` Source-score-excluded compatibility와 ordered-pair identity를 하나의
  post-hoc framework로 정리한 framing은 명확하다.
- `[~]` Transformation consistency와 family-sequence preservation은 구조적으로
  잘 정의된다.
- `[ ]` 핵심 구성은 handcrafted geometry classifier, group averaging, score
  multiplication, constrained sorting의 조합으로 보일 수 있다.
- `[ ]` Group averaging 자체는 표준적인 invariance construction이다.
- `[x]` Canonical candidate pool에서 verifier-based Hard-tail/Hard-drop과
  training-positive Positive-density를 직접 비교한다. 전자는 non-deployable
  diagnostics로, 후자는 closest non-learned continuous baseline으로 분리한다.
- `[~]` Component diagnostics는 transformation averaging의 exact guarantee를
  직접 지지하지만 pairwise term의 효과는 작고 MLP margin에서는 mixed다.
  Pairwise loss를 독립적인 performance contribution으로 내세우지 않는 현재
  해석을 유지해야 한다.

#### Clarity

- `[x]` 전체 문제에서 방법과 실험으로 이어지는 흐름은 파악할 수 있다.
- `[x]` Linear와 MLP의 차이와 re-ranking scope는 비교적 명확하다.
- `[~]` Metric formula는 정의되지만 verifier가 satisfied, uncertain, violated를
  판정하는 핵심 규칙은 main paper에 없다.
- `[~]` Family-aware ranking의 동작은 설명된다. Canonical matched control도
  완료됐지만, 그 결과는 우월성보다 family composition 보존이라는 목적을
  지지하므로 main에 이 해석을 한 문장으로 반영해야 한다.
- `[~]` Supplement에 predictor별 candidate row 수, fixed-pool exact-label
  coverage, 548-context evaluation universe, Open3DSG의 15개 empty context가
  함께 제시된다. Main 첫 독자에게는 candidate-pool 구조가 여전히 짧게만
  설명되므로, 추가 문장은 page budget에 따라 선택한다.
- `[ ]` Open3DSG의 15개 empty context와 score-range 특성이 main paper에서 보이지
  않는다.

#### Experimental rigor

- `[x]` Training, development, evaluation split이 분리된다.
- `[x]` Scan-level paired bootstrap과 여러 \(K\)를 보고한다.
- `[x]` Wrong-pair, wrong-predicate, shuffled-geometry controls를 포함한다.
- `[~]` MLP matched controls는 supplement에만 존재한다.
- `[x]` Hard-tail과 Hard-drop의 모든 \(K\) Recall, primary/decidable Violation,
  uncertainty, coverage, selected count가 canonical pool에서 재계산됐다.
- `[x]` Frozen monotonic mappings와 training-positive robust-density baseline이
  동일 candidate pool, family route, bootstrap resamples에서 직접 평가됐다.
- `[x]` Support/contact positions와 IDs를 고정한 채 proximity와 vertical-order
  queue만 합치는 matched routing ablation을 canonical pool에서 완료했다.
- `[~]` 다섯 predeclared fit을 완료했다. Linear는 정확히 반복되며, MLP는 15개
  predictor--\(K\) cells 중 14개에서 모든 seed가 Source 대비 두 방향을
  유지한다. VL-SAT \(K=50\) 한 seed는 Violation을 낮추면서 exact-label relation
  한 건을 잃으므로 seed-uniform Pareto claim은 할 수 없다.
- `[ ]` 많은 predictor--\(K\) 비교에 대한 multiplicity 처리가 없다.
- `[ ]` Qualitative evidence가 같은 context에서 선택된 소수 사례에 머문다.

#### Reproducibility

- `[x]` Source code, Docker configuration, model locks, protocol, compact
  results가 제공된다.
- `[x]` Main과 supplement에 대부분의 hyperparameter와 training construction이
  기록된다.
- `[~]` Public datasets와 source checkpoints를 사용하므로 일부 외부 의존성은
  불가피하다.
- `[~]` Licensed inputs에서 pseudonymized row bundle을 만드는 Docker exporter와
  그 bundle만으로 Tables 1--3 및 Figure 3 data를 재생성하는 one-command
  reproducer가 완료됐다. 291 canonical cells의 maximum absolute error는 0이다.
  다만 derived rows의 public ZIP 포함은 3RScan/3DSSG redistribution terms 확인
  전까지 보류하므로, 현재 공개 패키지는 compact outputs와 deterministic
  exporter를 제공하는 상태다.
- `[ ]` 원 source inference에서 compact result까지의 완전한 end-to-end
  reproduction은 현재 package만으로 불가능하다.

#### Limitations

- `[x]` Single target, known instances, support/contact 제외, independent validity
  label 부재를 인정한다.
- `[~]` Score mapping 결과는 bounded robustness를 지지하지만 percentile
  mapping에서 작은 Recall 손실이 남는다. 원고에 반영할 때 invariance 대신
  tested-mapping sensitivity로 한정해야 한다.
- `[ ]` Reconstruction noise, OBB error, partial observation의 영향을 충분히
  논의하지 않는다.
- `[~]` Supplement의 candidate-pool oracle이 missing-candidate ceiling을
  정량화한다. Method 첫 문장은 fixed-prediction re-ranking 범위를 밝히지만,
  `missing candidates cannot be recovered`라는 직접 문장을 main에 넣는지는
  저자 편집 선택으로 남아 있다.
- `[ ]` Source family sequence preservation 때문에 family-level source error를
  수정할 수 없다.
- `[ ]` Object class를 배제해 scale- or affordance-dependent relation을 처리하기
  어려운 점이 논의되지 않는다.

### Summary

본 논문은 fixed 3D scene graph predictions에서 source relation score와
ordered-pair predicate--geometry compatibility를 분리하고, learned compatibility를
source score와 결합해 proximity와 vertical-order candidates를 relation family
내부에서 재정렬하는 RelCompat3D를 제안한다. Linear와 compact MLP estimator,
counterfactual training, transformation averaging, family-sequence-preserving
re-ranking을 사용하며, 3DSSG의 동일 validation target에서 Open3DSG, VL-SAT,
SGFN을 평가한다. Exact-match Recall과 author-defined verifier-derived Violation을
함께 보고하고, point/mesh audit와 여러 controls로 geometric signal의 역할을
분석한다.

### Strengths

1. 문제 설정이 구체적이다. Relation label plausibility와 same-pair geometric
   compatibility의 차이를 명확히 구분한다.
2. 평가 identity를 엄밀하게 관리한다. Ordered-pair identity와 exact relation
   identity를 분리하고 family mapping이 label matching에 사용되지 않는다고
   명시한다.
3. 결과 보고가 비교적 정직하다. Linear와 MLP를 단일 winner로 만들지 않고 서로
   다른 Recall--Violation operating point로 설명한다.
4. Controls와 supplement가 풍부하다. Wrong-pair, wrong-predicate,
   feature-removal, uncertainty sensitivity, point/mesh audit를 포함한다.
5. 방법이 가볍고 source predictor를 재학습하지 않아 적용 비용이 낮다.

### Weaknesses

#### Major 1. 핵심 평가가 training construction과 충분히 독립적이지 않다

> “The compatibility estimators and primary verifier share some oriented
> bounding box (OBB)-derived measurements.”

> “Thresholds are fixed from training-split positive relations.”

논문의 핵심 개선은 대부분 verifier-derived Violation 감소로 측정된다. 그러나
training counterfactual과 primary verifier는 OBB distance, signed height, overlap,
일부 threshold를 공유한다. 따라서 학습된 estimator가 독립적인 geometric validity를
발견했다기보다 evaluation rule과 상관된 proxy를 학습했을 가능성을 배제할 수 없다.

Point/mesh audit은 좋은 보완이지만 동일한 reconstructed scenes, ontology,
training-positive-derived thresholds를 사용한다. 저자도 다음과 같이 독립적 ground
truth가 아니라고 인정한다.

> “Because the point- and mesh-based audit uses the same reconstructed scenes
> and ontology, it is an alternative geometric measurement rather than
> independent ground truth for geometric validity.”

이 한계는 현재 논문의 가장 강한 Open3DSG 결과까지 metric alignment의 산물일 수
있다는 의심을 남긴다.

**2026-07-27 대응 결과.** 이 우려를 숨기지 않고 검증 범위를 한 package로
고정했다. `construct_dependence_v1`은 training construction, primary verifier,
point/mesh audit이 evaluation rows, source scores, verifier labels, OBB
measurements, point/mesh measurements, scene identities, ontology를 각각
사용하는지 dependency matrix로 기록한다. Linear와 MLP의 point/mesh audit은
각각 15 cells 중 14 cells에서 Violation이 감소하고 한 cell에서 tie며 증가
cell은 없다. Primary, decidable-only, uncertain-as-violated 정의에서도 두
estimator를 합친 30 predictor--\(K\) cells가 모두 Source 대비 non-increasing이다.
Feature-removal, counterfactual-sensitivity, component-removal artifact도 같은
manifest에서 hash 검증된다. 따라서 label leakage와 단일 OBB scalar 의존 우려는
상당히 완화되지만, 이 package가 independent physical-validity ground truth를
제공하지는 않는다. Main의 scoped wording은 유지하고 dependency matrix와 전체
결과는 supplement에 둔다.

#### Major 2. Product utility가 source-score scale에 본질적으로 민감하다

> “We use sigmoid relation scores for VL-SAT/SGFN and cosine similarity between
> normalized text embeddings for Open3DSG, without predictor-specific
> normalization or refitting.”

> \(u_i^q=Z_iC_i^{\rm tr,q}\)

Source ranking은 monotonic transformation에 불변이지만 \(Z_iC_i^{tr}\)는 그렇지
않다. 동일 predictor score에 temperature scaling, power transform, affine mapping을
적용하면 source ranking은 같아도 RelCompat3D ranking은 달라질 수 있다.

특히 supplement의 observed range는 Open3DSG가 \([0.6394,0.9281]\)처럼 압축되어
있고 VL-SAT과 SGFN은 거의 0까지 내려간다. 따라서 Open3DSG에서 compatibility가
상대적으로 강하게 작용하는 현상이 method superiority가 아니라 score dynamic range
차이에서 발생했을 수 있다. 가장 큰 개선이 Open3DSG에 집중된다는 결과와 직접
연결되는 위험이다.

**2026-07-27 대응 결과.** 이 우려는
`experiments/RelCompat3D_geom_reliability/score_robustness_v1/`의 frozen
Docker sensitivity로 직접 평가했다. 다섯 smooth non-identity mapping에서
Linear는 75/75, MLP는 74/75 predictor--\(K\) 조건에서 Source 대비 Recall이
낮지 않고 Violation이 높지 않은 방향을 유지했다. MLP의 한 예외는 VL-SAT
\(K=50\), power 4에서 Recall \(-0.025\) percentage points이며 paired interval은
zero를 포함하고 Violation은 감소한다. Context-and-family percentile condition은
Linear 2/15, MLP 4/15 조건에서 최대 0.227 points의 Recall 손실을 보였고
Violation은 모든 조건에서 감소하거나 같았다. 따라서 missing experiment는
해결됐지만 결과는 score-scale invariance가 아니라 fixed-grid bounded robustness로
해석해야 한다.

#### Major 3. 핵심으로 소개한 component가 실제 결과를 설명하지 못한다 `[대응 완료, claim 제한]`

Introduction의 두 번째 contribution은 다음과 같다.

> “We estimate predicate--geometry compatibility without the source relation
> score and enforce exact consistency under applicable endpoint and predicate
> transformations.”

그러나 supplement의 direct removal 결과는 다음과 같다.

> “Removing the linked pairwise term changes the reported point estimates only
> marginally.”

> “Removing transformation averaging also has a small aggregate effect.”

Linked pairwise loss와 transformation averaging은 main Recall--Violation gain의
원인이 아니다. Transformation averaging은 representation invariance를 정확히
보장하지만 aggregate performance에서는 거의 영향을 주지 않는다. Pairwise loss
역시 사실상 regularizer다.

리뷰어는 가장 단순한 BCE-trained geometry classifier와 product re-ranking만으로
결과가 대부분 재현된다고 해석할 수 있다. 그러면 논문의 method novelty가 크게
축소된다.

**2026-07-27 대응 결과.** 이 우려를 aggregate ablation만으로 방어하지 않고 각
component가 직접 겨냥하는 diagnostic으로 분리해 평가했다.
`component_diagnostics_v1`은 Linear와 MLP 각각에 대해 Full, no-pairwise,
no-averaging을 같은 rows, features, optimizer, source scores, family route에서
비교한다.

- 3,516 held-out linked pairs에서 pairwise term은 positive-win rate를 Linear
  0.085, MLP 0.057 percentage points 높인다. Linear에서는 mean margin이
  13.6145에서 14.1413으로 늘고 softplus margin loss가 .03607에서 .03534로
  낮아진다.
- MLP는 positive-win rate와 lower-tail margin은 좋아지지만 mean/median margin과
  softplus loss는 좋아지지 않는다. 따라서 pairwise term은 제한적이고
  estimator-dependent한 training regularizer로 해석한다.
- Transformation averaging을 적용하면 두 estimator와 no-pairwise refit 모두
  transformed compatibility error가 mean/P95/max에서 0이고 transformed-view
  top-\(K\) membership이 정확히 같다.
- Averaging을 제거하면 minimum top-\(K\) Jaccard/exact-context rate가 Linear
  .9635/.8266, MLP .6975/.4617로 낮아진다. No-averaging compatibility error의
  worst source-specific proximity mean/P95/max는 Linear
  .0150/.0817/.4532, MLP .1684/.5805/.9370이다.

따라서 이 실험은 pairwise loss가 main aggregate gain의 원인이라는 주장을
지지하지 않는다. 반면 transformation averaging이 수행하는 exact consistency
역할은 직접 검증한다. Main contribution은 source-score-excluded compatibility와
family-aware combination에 두고, pairwise term은 training regularizer,
averaging은 inference-time guarantee로 한정하는 것이 정확하다.

#### Major 4. Family-aware ranking의 필요성을 입증하는 matched ablation이 부족하다

> “It preserves the sequence of relation-family labels in the source ranking
> and the source order of support/contact candidates.”

> “Product (all families) can raise aggregate Recall and lower aggregate
> Violation, but it changes support/contact selections.”

Source family sequence를 보존하는 것은 설계 선택이지 자명한 requirement가 아니다.
Source가 family composition 자체를 잘못 예측한 경우 RelCompat3D는 그 오류를
수정하지 못한다.

Product (all families)는 여러 setting에서 더 높은 Recall이나 낮은 Violation을
보인다. Table 1은 Product를 scope comparison으로 분리하고 best-score bold
대상에서 제외한다. 합리적 설명은 있지만 reviewer에게는 더 강한 방법을 비교
대상에서 사실상 배제한 것으로 보일 수 있다.

필요한 비교는 다음과 같다.

- proximity/vertical만 re-rank하되 global family sequence는 보존하지 않는 variant
- support/contact head 없이 global re-ranking하는 variant
- hard filter와 soft compatibility의 Recall--Violation trade-off
- source family sequence preservation이 실제 support/contact regression을 막는다는
  수치

현재는 constrained ranking이 필요한 이유보다 안전한 claim scope를 만들기 위한
장치처럼 보일 위험이 있다.

**2026-07-27 대응 결과.** `routing_controls_v1`에서 current `family_slots`와
`pv_global`을 동일 candidates, compatibility, product utility, support/contact
positions와 IDs 아래 직접 비교했다. `pv_global`은 proximity와 vertical-order만
하나의 queue로 합친다. 결과는 estimator와 \(K\)에 따라 mixed다. Open3DSG
Linear에서는 Recall이 모든 \(K\)에서 \(+0.58\)에서 \(+4.46\) points 높아지지만,
MLP에서는 \(K=50,100\) Recall이 각각 \(2.92,3.80\) points 낮아진다. Open3DSG
MLP \(K=50\)의 감소는 support/contact 변화가 아니라 proximity selected count가
6,295에서 3,423으로 줄고 vertical-order count가 6,508에서 9,380으로 늘어난
family-composition shift와 대응한다. Identity route, family-sequence 보존,
support/contact position과 ID 보존 검증은 모두 통과했다. 이 결과는 current
route의 aggregate optimality를 지지하지 않는다. 대신 family slots가 cross-family
replacement를 막는 composition-preserving operating point라는 정확한 역할을
보인다. Main에는 이 bounded interpretation을 한 문장으로 남기고, 전체 route,
family slice, membership, paired interval 표는 supplement에 둔다.

#### Major 5. 외적 타당성과 실질적 효과가 제한적이다

> “All three predictors are evaluated on the same 3DSSG target.”

> “Open3DSG shows the largest gains across the reported \(K\) values.”

세 predictor 평가는 세 독립 benchmark가 아니다. 모두 같은 3DSSG/3RScan geometry와
ontology를 사용한다. VL-SAT과 SGFN에서는 Recall 개선이 매우 작고, SGFN은 낮은
\(K\)에서 완전히 동일하다. 강한 결과는 사실상 Open3DSG 한 source에 집중된다.

Supplement의 ReplicaSSG/FROSS stress test는 긍정적이지만 ground-truth relation이
172개로 작고 \(K\)에 따라 통계적 지지가 달라 main generalization evidence로
충분하지 않다.

개선된 graph가 navigation, question answering, alignment 같은 downstream task에
실제 이득을 제공하는지도 보여주지 않는다. 문제의 중요성은 설득되지만 해결의
practical impact는 입증되지 않는다.

#### Major 6. Closest baseline 구성이 충분하지 않다

> “Matched rank-average fusion (RankAvg) and reciprocal rank fusion (RRF)
> combine predictor and linear-compatibility ranks.”

현재 baseline은 Source, RankAvg, RRF, Product 중심이다. 그러나 central question은
learned compatibility가 필요한가이므로 다음 비교가 더 직접적이다.

- verifier threshold 기반 hard filtering
- rule confidence를 연속값으로 사용한 soft re-ranking
- score-only calibrated re-ranker
- training-split distance/height likelihood baseline
- isotonic 또는 temperature-calibrated product
- geometry nearest-neighbor 또는 nonparametric compatibility
- closest constraint-refinement method의 적용 가능한 variant

Supplement가 hard-rule baseline의 uncertainty를 언급하지만 정확한
Recall--Violation trade-off를 main comparison으로 제공하지 않는다. 이 때문에
learned model의 필요성이 충분히 입증되지 않는다.

**2026-07-27 대응 결과.** Canonical candidate pool에서 Hard-tail, Hard-drop,
그리고 training-positive Positive-density를 동일한 \(K\), family route, source
scores, verifier, bootstrap resamples로 재평가했다. Positive-density는
evaluation-verifier label이나 counterfactual negative를 사용하지 않는 closest
non-learned continuous baseline이다. \(K=50\)에서 Linear와 MLP 모두 세 predictor
전부에서 Positive-density를 Pareto-dominate한다. 전체 15 predictor--\(K\)
조건에서 Linear는 12개를 dominate하고 3개가 trade-off이며, MLP는 12개를
dominate하고 2개가 trade-off, Open3DSG \(K=5\) 한 조건에서만 dominated된다.
Hard-tail과 Hard-drop은 evaluation-verifier labels를 직접 읽으므로
non-deployable diagnostics다. Hard-drop의 zero primary Violation은 construction의
결과이며 일부 \(K\)에서 selected count가 부족하다. 따라서 closest baseline
누락은 해결됐지만 verifier-based route를 learned method보다 우수한 deployable
baseline으로 해석해서는 안 된다.

#### Major 7. 제공 artifact만으로 핵심 수치를 재생성할 수 없다
`[기술 대응 완료, derived-row 공개 조건 확인 필요]`

> “The released artifacts provide these additional metrics for all five
> \(K\) values.”

현재 ZIP은 code, protocols, locks, compact summaries를 제공하지만 row-level
predictions, joined geometry, verifier inputs가 없다. Reviewer는 JSON summary를
검증할 수는 있어도 Table 1--3을 처음부터 재계산할 수 없다.

원 source repository와 datasets가 필요하다는 것은 이해할 수 있으나, 최소한
anonymized candidate-level evaluation rows나 deterministic regeneration inputs가
있어야 reported metrics의 실질적 reproducibility가 높아진다.

**2026-07-27 대응 결과.** Hash-locked licensed inputs에서 601,140 candidate
rows와 3,972 ground-truth rows를 deterministic하게 내보내는 Docker exporter를
추가했다. Derived bundle은 keyed HMAC으로 scan, context, instance identity를
pseudonymize하고 original identifiers, object categories, raw geometry를
제외한다. 별도 Docker reproducer는 이 bundle만 읽어 Tables 1--3, Figure 3 data,
verification rendering, canonical comparison을 생성한다. Main tables의 291개
cells가 tolerance \(10^{-12}\)에서 maximum absolute error 0으로 일치했다.
Candidate row counts, GT denominator, input and bundle hashes, Table 3 status
accounting도 모두 validation을 통과했다.

남은 것은 과학적 구현이 아니라 배포 권한 확인이다. 3RScan/3DSSG terms에서
source-derived annotation row의 재배포 허용 문구를 확인하지 못했으므로 61 MiB
bundle은 public ZIP에 넣지 않는다. Anonymous artifact에는 exporter, reproducer,
schema, compact regenerated outputs, hashes를 포함하고, 저자가 data owner 또는
terms를 확인한 경우에만 bundle을 추가한다. 허용되지 않으면 licensed external
inputs에서 동일 manifest를 만드는 deterministic export command를 공식
재현 경로로 유지한다.

#### Minor 1. Main paper에서 verifier가 지나치게 불투명하다

> “the rule-based geometry verifier returns satisfied, uncertain, or violated”

Main에는 각 family에서 무엇이 satisfied 또는 violated인지, uncertain이 어떤
경우인지 설명이 없다. 논문의 핵심 \(V@K\)를 이해하려면 supplement를 읽어야 한다.

#### Minor 2. Primary Violation denominator가 직관적이지 않다

> “Thus uncertain candidates enter the denominator but not the numerator.”

Uncertain candidate가 많아지면 Violation이 인위적으로 낮아질 수 있다. Supplement의
decidable-only와 uncertain-as-violation sensitivity가 방향성을 지지하지만 primary
metric 선택의 근거가 main에서 부족하다.

#### Minor 3. 학습 stochasticity가 평가되지 않는다 `[대응 완료, 한 예외 공개]`

> “RelCompat3D-MLP uses one shared multilayer perceptron (MLP) with a single
> two-unit ReLU hidden layer.”

Bootstrap은 evaluation scan uncertainty만 반영한다. MLP fitting seed,
initialization, negative sampling에 따른 variance가 보고되지 않는다.

**2026-07-27 대응 결과.** 사전 고정한 seed
\(\{20260714,\ldots,20260718\}\)로 두 estimator를 다시 fit했다. Training rows와
linked-pair identities는 모든 실행에서 고정했다. Active MLP seed 20260714는
분석 전에 고정돼 있었고 결과를 보고 재선택하지 않았다.

- Linear는 zero initialization과 full-batch optimization을 사용해 다섯 실행의
  model hash와 모든 metric이 정확히 같다.
- MLP는 seed별 model hash가 다르지만 평균 표준편차는 작다. 다만 VL-SAT
  \(K=50\), seed 20260718에서 Recall이 Source 92.724\%에서 92.699\%로 exact-label
  relation 한 건 감소하고 Violation은 2.675\%에서 1.821\%로 낮아진다.
- 나머지 14개 MLP predictor--\(K\) cells에서는 다섯 seed 모두 Source 대비
  Recall non-decrease와 Violation non-increase를 함께 유지한다.

따라서 fitting variation은 평가됐지만, 모든 seed에서 Pareto improvement가
보장된다는 주장은 할 수 없다. Scan-resampling interval과 training-seed
variation은 서로 다른 uncertainty로 분리해 supplement에 보고한다.

#### Minor 4. Qualitative evidence가 선택적으로 보인다

> “Together, these cases illustrate two types of top-50 membership change”

Demotion과 promotion이 같은 context에서 선택된 두 사례뿐이다. Random 또는
stratified qualitative sample, failure case count, error taxonomy가 없어서
cherry-picking 가능성이 남는다.

#### Minor 5. Open3DSG evaluation coverage가 main에서 보이지 않는다

Main은 548 contexts라고 하지만 supplement에 따르면 public preprocessing은
533/548 contexts에서만 candidates를 생성한다. Conservative denominator를 사용한
것은 적절하지만 main에서 한 문장으로 알려주는 편이 공정하다.

#### Minor 6. Fixed-candidate scope가 놓치는 오류 유형이 충분히 강조되지 않는다

> “RelCompat3D re-ranks fixed relation predictions rather than replacing a 3D
> scene graph generator.”

후보에 없는 exact relation은 복구할 수 없고 잘못된 object instance나 missing
object도 수정할 수 없다. 이는 단순 구현 한계가 아니라 re-ranking framework의
구조적 recall ceiling이다.

### Questions for authors

1. Blind human annotation이나 독립적인 physical-validity label에서 compatibility
   ranking과 Violation 감소를 검증했는가?
2. `[답변됨]` Source score에 temperature, power, percentile mapping을 적용한
   결과는 P0-1에 기록했다. Smooth grid는 거의 완전히 안정적이고 percentile에서
   최대 0.227-point Recall sensitivity가 남는다.
3. `[답변됨]` Pairwise term은 small, estimator-dependent training regularizer로
   한정한다. Transformation averaging은 aggregate gain의 원인이 아니라
   transformed compatibility와 top-\(K\) membership을 정확히 같게 만드는
   inference-time guarantee다.
4. `[답변됨]` Support/contact를 고정한 `pv_global` 비교는 estimator와 \(K\)에
   따라 mixed다. Family slots는 aggregate-optimal route가 아니라
   family-composition을 보존하는 constraint로 해석한다.
5. Product (all families)가 더 높은 aggregate Recall을 얻는 setting에서
   support/contact에 실제로 어떤 regression이 발생하는가?
6. `[답변됨]` Hard-tail과 Hard-drop의 Recall, primary/decidable Violation,
   uncertainty, coverage, selected count를 모든 \(K\)에서 재계산했다. 이들은
   evaluation labels를 읽는 diagnostics로 분리한다.
7. `[부분 답변]` Open3DSG의 큰 변화는 여러 smooth score mapping에서 유지되어
   identity scale 하나에만 의존하지 않는다. Predictor별 효과 차이의 원인을
   source quality나 candidate diversity까지 인과적으로 분해한 것은 아니다.
8. `[답변됨]` 다섯 predeclared fit에서 Linear는 정확히 반복된다. MLP는
   14/15 predictor--\(K\) cells에서 모든 seed가 Source 대비 두 방향을 유지하며,
   VL-SAT \(K=50\) 한 seed는 Violation을 낮추면서 exact-label relation 한 건을
   잃는다.
9. 3DSSG 외 target에서 더 큰 evaluation을 제공할 수 있는가? 현재 ReplicaSSG
   172-relation stress test를 어느 정도 일반화 근거로 해석해야 하는가?
10. `[기술 답변됨, 배포 권한 확인 필요]` Pseudonymized rows만으로 Tables 1--3과
    Figure 3 data를 maximum error 0으로 재생성한다. Public ZIP 포함은
    3RScan/3DSSG derived-row redistribution terms 확인 뒤 결정하며, 불허 시
    licensed inputs에서 동일 bundle을 만드는 Docker exporter를 제공한다.

### 예상 Rating

**Weak Reject**

이유는 구현 오류나 명백한 잘못된 수식 때문이 아니다. P0-1은 product conclusion이
fixed smooth mapping 하나에만 의존한다는 우려를 크게 낮췄고, P0-2는 closest
continuous baseline 누락을 해결했다. P0-3은 family slots의 역할을 matched
comparison으로 한정했고, P0-4는 construct-dependence evidence를 한 package로
검증했다. 후속 component diagnostics는 transformation averaging의 exact mechanism을
검증하고 pairwise term의 제한적 역할을 분리했으며, five-seed 분석은 fitting
variation을 정량화했다. P1 row reproduction은 canonical tables와 figure data를
exactly 재생성하고 candidate oracle은 fixed-pool ceiling을 정량화했다. 그러나
AAAI accept 기준에서는 다음 위험이 남는다.

- Core metric과 training construction의 construct dependence
- Pairwise regularizer의 제한적인 method necessity와 framework novelty ceiling
- 한 shared target과 제한된 downstream evidence에 따른 significance 불확실성
- Fixed-candidate oracle가 Open3DSG pool coverage 79.68%와 active-route
  headroom을 정량화했지만, candidate generation 자체를 개선하지 않는 scope

P0-1--P0-4는 처음 지적한 대안 설명을 상당 부분 차단해 Weak Accept 경계에는
가까워졌다. 다만 independent validity와 component-level methodological necessity는
여전히 논쟁적이고, 큰 효과가 하나의 shared target의 Open3DSG에 집중된다. 따라서
현재 보수적 예상은 여전히 **Weak Reject**이며, 이는 새 실험 누락보다 novelty와
construct-validity 해석에 좌우되는 판정이다.

### 이슈별 대응 계획

아래 대응은 단순한 rebuttal 문구가 아니라, 각 우려를 실제로 닫기 위한 실행
기준이다. 우선순위는 다음과 같다.

- **P0**: 제출 판단과 rating을 바꿀 가능성이 큰 핵심 validity 이슈
- **P1**: accept 가능성을 높이지만 claim을 좁혀서도 방어 가능한 이슈
- **P2**: 명료성, 보고 완결성, reproducibility를 보강하는 이슈

각 실험은 기존 frozen train/development/evaluation split, candidate pool, metric
definition, bootstrap unit을 유지해야 한다. 새로운 결과를 official evaluation에서
확인한 뒤 method나 hyperparameter를 다시 선택하면 protocol leakage가 되므로,
선택이 필요한 값은 training 또는 development split에서 먼저 고정하고 그 기록과
hash를 남긴다.

#### Major 1. Verifier construct dependence `[P0]`

**리뷰어 우려.** Training counterfactual construction과 primary Violation verifier가
일부 OBB-derived measurement와 threshold logic을 공유하므로, 낮아진 Violation이
독립적인 physical validity 향상보다 evaluation rule에 대한 alignment일 수 있다.

**현재 사용할 수 있는 근거.**

- Evaluation rows, source scores, verifier-status labels는 training example 생성에
  사용하지 않았다.
- Proximity negative construction과 primary verifier는 동일한 evaluation row를
  공유하지 않으며 일부 threshold도 동일하지 않다.
- Exact verifier scalar removal 이후에도 주요 방향이 유지된다.
- Point- and mesh-based audit은 OBB input과 primary verifier label을 읽지 않는다.
- Decidable-only와 uncertain-as-violation 정의에서도 변화 방향을 확인할 수 있다.

이 근거는 **label leakage가 없고 결과가 한 scalar에만 의존하지 않는다**는 점은
방어하지만, 독립적인 geometric-validity ground truth를 제공하지는 않는다.

**최소 제출 대응.**

1. Main Method의 training construction 설명에서 `evaluation rows and verifier-status
   labels are not used`를 유지한다.
2. Main Results에서는 Violation을 항상 `verifier-derived Violation`으로 부르고
   physical validity 또는 ground-truth validity로 확대하지 않는다.
3. Point/mesh audit은 `independent validation`이 아니라 `alternative geometric
   measurement`로 기술한다.
4. Supplement에 다음 dependency matrix를 한 표로 정리한다.

   | Component | Training target | Primary verifier | Point/mesh audit |
   |---|---|---|---|
   | Evaluation rows | No | Yes | Yes |
   | OBB measurements | Some | Yes | No |
   | Primary status labels | No | Output | No |
   | Reconstructed scene/ontology | Yes | Yes | Yes |

5. Exact-scalar removal, all-related-feature removal, decidable-only,
   uncertain-as-violation 결과를 같은 subsection에서 연결해 reviewer가 근거를
   흩어 읽지 않도록 한다.

**강한 추가 대응.** Evaluation sample을 source rank와 method output을 숨긴 상태로
독립 annotator가 판정하는 blind audit을 추가한다.

- Sampling: predictor와 relation family별 stratified random sample을 사전에
  고정한다. Source-only, retained, demoted, promoted candidates를 포함한다.
- Evidence: RGB/point/mesh view만 제공하고 source score, verifier label,
  RelCompat3D rank는 숨긴다.
- Label: `satisfied / violated / insufficient evidence`와 confidence를 기록한다.
- Report: inter-annotator agreement, decidable coverage, Source와 두 RelCompat3D
  variant의 violation rate, paired confidence interval을 함께 보고한다.
- Leakage control: annotator guide와 sample manifest를 evaluation 전에 freeze하고
  hash를 남긴다.

**이슈 종료 기준.**

- 최소 기준: OBB scalar를 제거한 결과와 point/mesh audit에서 세 predictor의 변화
  방향이 유지되고, uncertainty 정의를 바꿔도 결론이 뒤집히지 않는다.
- 강한 기준: blind audit에서 적어도 primary claim 대상의 pooled 또는 predictor별
  violation 감소가 같은 방향이며 confidence interval까지 보고된다.
- 위 기준을 충족하지 못하면 claim은 `the ranking better matches the specified
  verifier`로 좁혀야 하며 geometric reliability 향상이라는 표현은 제거한다.

**원고 반영 위치.**

- Main Method, training construction 문단: leakage boundary 한 문장
- Main Experiments, Metrics: `verifier-derived`라는 metric status
- Main Results, Point/mesh audit: alternative measurement와 결과 방향
- Discussion: 독립 ground truth가 아니라는 범위 한 문장
- Supplement: dependency matrix, feature-removal, uncertainty sensitivity, blind
  audit protocol과 전체 결과

**피해야 할 대응.** 같은 scene과 ontology를 사용한 point/mesh audit을
`independent physical validation`이라고 부르거나, threshold가 일부 다르다는 사실만
근거로 circularity가 완전히 해소되었다고 주장하지 않는다.

#### Major 2. Source-score scale sensitivity `[P0]`

**리뷰어 우려.** Source ranking은 monotonic score transformation에 불변이지만
\(u=ZC^{\rm tr}\)는 불변이 아니다. Open3DSG의 compressed cosine-score range 때문에
compatibility가 상대적으로 강하게 작동해 큰 개선이 발생했을 가능성이 있다.

**현재 상태: 실험 해결, 원고 반영 선택 대기.** 아래 protocol은
`score_robustness_v1`에서 Docker로 완료됐다. 다섯 smooth non-identity mapping은
Linear 75/75, MLP 74/75 conditions에서 favorable point-estimate direction을
유지한다. Percentile stress에서는 최대 0.227-point Recall sensitivity가 남고
Violation은 증가하지 않는다. 상세 수치, artifact, 원고 삽입 위치는 아래
`P0-1. Source-score monotonic sensitivity`에 정리했다.

**실행된 분석 protocol.**

1. Candidate pool과 source ordering은 고정한다.
2. Predictor별로 아래 monotonic mapping을 적용한다.

   - Identity: \(q(Z)=Z\)
   - Temperature-logit mapping: sigmoid score에 대해
     \(q_T(Z)=\sigma(\operatorname{logit}(Z)/T)\)
   - Power mapping: \(q_\gamma(Z)=Z^\gamma\)
   - Empirical percentile mapping: training 또는 development candidate score의
     empirical CDF

3. \(T\)와 \(\gamma\)는 broad fixed grid를 사전에 선언한다. Evaluation 결과로
   가장 좋은 값을 선택하지 않는다.
4. 각 mapping에 대해 세 predictor와 모든 \(K\)에서 Recall, primary Violation,
   top-\(K\) Jaccard overlap, Kendall rank correlation을 보고한다.
5. Source ranking이 mapping 전후 정확히 동일한지 assertion으로 확인한다.
6. Linear와 MLP를 모두 평가하되, 표가 커지면 worst-case 변화와 전체 curve를
   supplement에 둔다.

**필수 comparator.** Percentile 또는 rank-based scale-invariant fusion을 포함한다.
이는 현재 RankAvg/RRF와 연결되지만, compatibility rank와 source rank를 같은
family-aware route에 넣은 matched condition임을 명확히 해야 한다.

**이슈 종료 기준.**

- 핵심 결론이 mapping별로 안정적이라는 기준을 사전에 정의한다. 권장 기준은 모든
  predictor에서 적어도 한 proposed variant가 Source 대비 Recall을 낮추지 않고
  Violation을 높이지 않는 방향을 유지하며, Open3DSG의 큰 개선이 특정 한 mapping에만
  존재하지 않는 것이다.
- Top-\(K\) membership이 크게 바뀌더라도 Recall--Violation 결론이 유지되면 method
  conclusion은 방어 가능하지만, product ranking 자체가 scale-invariant하다고
  주장하면 안 된다.
- 결론이 mapping에 따라 뒤집히면 product를 default fusion으로 정당화할 수 없다.
  이 경우 development-frozen percentile mapping 또는 rank utility를 active method로
  바꾸고 전체 표, CI, figure, audit를 재생성해야 한다.

**원고 반영 위치.**

- Main Method, source-score 정의 직후: score type과 predictor 내부에서만 ranking함을
  유지하되 scale invariance는 주장하지 않는다.
- Main Experiments, Baselines/Controls: `monotonic score-mapping sensitivity` 한
  문장과 supplement pointer
- Main Discussion: 결과가 raw source-score scale에 의존하는 범위를 한 문장으로
  제한
- Supplement: observed score range, mapping formulas, frozen grids, 전체
  Recall--Violation와 rank-stability 결과

**권장 rebuttal 문장 구조.** “The source order is unchanged by every tested
monotonic mapping. We therefore isolate only the scale dependence of the product
utility and report the resulting Recall--Violation and top-\(K\) stability, with
all mapping parameters fixed before evaluation.”

**피해야 할 대응.** 모든 score가 non-negative라는 사실은 product의 부호 문제만
해결한다. 이것을 scale robustness의 증거로 사용하지 않는다. RankAvg/RRF가 존재한다는
사실만으로 product sensitivity가 검증되었다고 쓰지 않는다.

#### Major 3. Pairwise loss와 transformation averaging의 작은 aggregate effect `[P1 완료, bounded]`

**리뷰어 우려.** 두 요소를 제거해도 aggregate Recall--Violation이 거의 유지되므로,
Introduction에서 이들을 성능 향상의 핵심 원인처럼 제시하면 method necessity가
약해진다.

**역할을 분리한 claim.**

- Linked pairwise loss: positive와 constructed counterfactual 사이의 ordering을
  직접 학습하도록 하는 training regularizer
- Transformation averaging: equivalent endpoint/predicate representation에 정확히
  같은 compatibility를 주는 inference-time guarantee
- Main empirical gain: predicate/pair geometry로 학습한 compatibility와 source
  score의 family-aware combination

**필수 보고.**

1. Full, no-pairwise-loss, no-transformation-averaging을 동일 seed와 split에서
   비교한다.
2. Main metrics뿐 아니라 component가 직접 겨냥한 진단값을 보고한다.

   - Pairwise: held-out linked-pair ordering accuracy, mean positive-negative
     logit margin, BCE 또는 ranking loss
   - Averaging: transformed-pair compatibility absolute difference의 mean, 95th
     percentile, maximum, transformation 후 top-\(K\) membership consistency

3. 기존 no-averaging maximum discrepancy인 proximity 0.4532와 vertical 0.0192를
   전체 분포와 함께 제시한다. Maximum만 단독으로 사용하면 outlier 공격을 받을 수
   있다.
4. Linear와 MLP에서 각각 보고한다. 한 estimator에서만 효과가 있다면 그 범위를
   명시한다.

**이슈 종료 기준.**

- Pairwise removal이 main metric에는 작더라도 held-out counterfactual ordering을
  일관되게 개선하면 regularizer로 유지할 수 있다.
- Transformation averaging이 numerical tolerance 안에서 transformed
  compatibility 차이를 0으로 만들고 transformed input의 selected ranking을
  동일하게 유지하면 exact-consistency mechanism으로 정당화된다.
- Pairwise diagnostic도 개선하지 않으면 해당 loss를 contribution에서 내리고
  implementation detail 또는 supplement로 이동한다.

**원고 반영 위치.**

- Abstract: component 이름을 모두 나열할 필요는 없으며 relation-preserving
  consistency를 한 구절로만 유지
- Introduction contribution 2: performance gain이 아니라 exact consistency
  enforcement로 표현
- Method: loss와 averaging의 서로 다른 목적을 각 정의 직후 명시
- Main Ablations: `direct component removals are in the supplement` pointer
- Supplement: direct diagnostic과 aggregate metrics의 matched table

**피해야 할 대응.** Aggregate metric effect가 작다는 사실을 숨기거나
transformation averaging이 Recall 향상의 주원인이라고 쓰지 않는다. 반대로 exact
guarantee가 aggregate 평균에 작게 나타났다는 이유만으로 method에서 제거할 필요도
없다.

**완료 protocol과 검증.**

- Frozen protocol:
  `experiments/RelCompat3D_geom_reliability/component_diagnostics_v1/protocol.json`
- Docker evaluator:
  `src/relcompat3d/evaluate_components.py`
- Compact results:
  `experiments/RelCompat3D_geom_reliability/component_diagnostics_v1/evaluation/`
- Manifest SHA-256:
  `107c83993359b0681d77cc4c808696bb23e97c8f9c708a6feec140815bfaa917`
- Active MLP reproduction의 maximum parameter error는
  \(6.9\times10^{-15}\)이고 main reference metric을 정확히 재현한다.
- 1,061/117/157 split, 60,208 training rows, 6,246 development rows,
  3,972 evaluation GT denominator, family sequence와 support/contact
  subsequence가 모두 validation을 통과했다.

**직접 진단 결과.**

| Estimator | Condition | Positive win | Mean margin | P05 | Median | P95 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Linear | Full | .9926 | 14.1413 | 4.1397 | 13.3462 | 27.8989 |
| Linear | No pairwise | .9918 | 13.6145 | 4.0170 | 12.7360 | 26.9527 |
| MLP | Full | .9932 | 12.1491 | 3.9317 | 11.6214 | 21.8631 |
| MLP | No pairwise | .9926 | 12.6489 | 3.7400 | 12.0326 | 22.5406 |

- Pairwise term은 positive-win rate를 두 estimator에서 소폭 높인다.
- Linear는 mean/median/lower-tail margin과 softplus margin loss가 모두
  개선된다.
- MLP는 win rate와 P05는 개선되지만 mean/median margin과 softplus loss는
  개선되지 않는다. 이를 universal component benefit으로 해석하지 않는다.

Transformation averaging의 결과는 더 명확하다.

| Estimator | No-averaging family | Error mean | P95 | Max | Min top-\(K\) Jaccard | Min exact-context |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Linear | Proximity | .0150 | .0817 | .4532 | .9635 | .8266 |
| Linear | Vertical | .0014 | .0080 | .0192 | .9635 | .8266 |
| MLP | Proximity | .1684 | .5805 | .9370 | .6975 | .4617 |
| MLP | Vertical | .0402 | .2896 | .9157 | .6975 | .4617 |

Full과 no-pairwise condition은 averaging을 유지하므로 두 estimator 모두
error mean/P95/max가 0이고 transformed-view top-\(K\) membership이 정확히
같다. 따라서 averaging은 aggregate metric improvement가 아니라 claimed exact
consistency mechanism으로 정당화된다.

**Supplement 반영.**

- `[x]` `tab:component-removals`에 두 estimator의 Full, no-pairwise,
  no-averaging \(K=50,100\) 결과를 넣었다.
- `[x]` `tab:pairwise-diagnostics`에 3,516 held-out pairs의 win rate와
  margin distribution을 넣었다.
- `[x]` `tab:transformation-diagnostics`에 error mean/P95/max와 transformed-view
  membership consistency를 넣었다.
- `[x]` Pairwise term을 dominant performance source가 아닌
  estimator-dependent regularizer로 해석한다.

**Main 반영 판단.**

- 현재 main에는 direct component removals가 supplement에 있다는 pointer가 있어
  추가 문장은 필수가 아니다.
- 향후 한 문장을 넣는다면 `Ablations and Controls` 마지막 문장 다음에 다음
  bounded wording을 사용한다.

  > Direct diagnostics show that the pairwise term has a small,
  > estimator-dependent effect, whereas transformation averaging makes
  > compatibility and selected membership identical under the applicable
  > transformed representations.

- 사용자가 main 반영을 보류했으므로 현재 main source에는 넣지 않았다.

#### Major 4. Family-aware ranking의 필요성 `[P0]`

**리뷰어 우려.** Source family sequence 보존은 안전한 scope restriction일 수는
있지만 최적이거나 필요한 설계라는 실험 근거가 부족하다. Product (all families)가
여러 aggregate cell에서 더 좋아 보여 proposed route가 임의적으로 보일 수 있다.

**필수 matched variants.**

모든 variant는 같은 candidates, compatibility estimator, score fusion, tie-breaking,
evaluation split을 사용하고 ranking constraint만 바꾼다.

1. `Family-sequence preserved` — 현재 RelCompat3D
2. `Global P/V` — proximity와 vertical candidates를 합쳐 global re-ranking하되
   support/contact 후보는 source 위치 또는 source subsequence로 고정
3. `Family counts unfrozen` — support/contact 내부 순서는 유지하지만 top-\(K\)의
   family composition은 바뀔 수 있게 함
4. `All families` — support/contact compatibility까지 적용
5. 가능하면 `No compatibility, same constraint` — constraint 자체가 결과를
   바꾸는지 확인하는 identity control

**필수 metric breakdown.**

- Aggregate Recall와 Violation
- Family-specific Recall와 Violation
- Top-\(K\) family counts와 Source 대비 변화
- Support/contact exact-match gain/loss와 violation change
- 각 variant가 source top-\(K\)에서 제거하고 추가한 candidate 수

**이슈 종료 기준.**

- 현재 route가 support/contact family-specific 결과를 정확히 보존하면서
  proximity/vertical 결과를 개선한다는 것은 construction으로 보장된다.
- 추가로, unconstrained variants가 aggregate metric을 개선하더라도
  support/contact regression 또는 family-composition confounding을 만든다는 수치를
  보여야 `controlled reliability layer`라는 설계 필요성이 설득된다.
- Unconstrained route가 모든 family에서 동등하거나 더 좋다면 current constraint를
  methodological necessity로 주장하지 않는다. 이 경우 safety-preserving operating
  point로 재정의하고 Product를 별도 stronger-coverage variant로 정직하게 제시한다.

**원고 반영 위치.**

- Method: family sequence preservation이 optimization superiority가 아니라
  unaffected-family preservation constraint임을 명시
- Table 1 caption/body: Product가 다른 scope임을 설명하되 best comparison에서
  임의로 배제했다는 인상을 피하도록 family-specific result pointer 제공
- Ablations: ranking-constraint-only matched comparison 한 문장
- Supplement: 전체 variants와 family-specific breakdown

**권장 본문 문장.** “The constraint is intended to isolate changes to the two
re-ranked families rather than to optimize aggregate performance by changing
family composition. The supplement compares matched unconstrained variants and
reports the resulting family-specific changes.”

**피해야 할 대응.** Product가 scope가 다르다는 말만 반복하거나, aggregate score가
더 높다는 이유만으로 support/contact regression을 수치 없이 추정하지 않는다.

#### Major 5. 외적 타당성과 실질적 효과 `[P1]`

**리뷰어 우려.** 세 predictor가 모두 하나의 3DSSG/3RScan target에 평가되어
cross-predictor evidence가 dataset generalization을 뜻하지 않는다. 큰 효과가
Open3DSG에 집중되고 downstream benefit도 확인되지 않았다.

**claim을 먼저 고정한다.**

- 허용: `three predictors on a shared 3DSSG target`,
  `cross-predictor reliability evidence`
- 금지: `generalizes across datasets`, `broad 3D scene graph improvement`,
  `predictor-agnostic`, `SOTA`
- ReplicaSSG/FROSS: `small transfer stress test`, dataset-level generalization
  증거가 아님

**추가 evidence의 우선순위.**

1. **가장 현실적인 보강:** 기존 ReplicaSSG/FROSS 172 relations에서 predictor,
   relation family, \(K\), geometry availability별 결과와 exact denominator를
   완전 공개한다.
2. **더 강한 보강:** 두 번째 target에서 candidate-generation부터 geometry join,
   exact-label mapping, verifier coverage, CI까지 동일 protocol로 평가한다.
3. **가장 강한 보강:** downstream query 또는 reasoning task에서 source와
   RelCompat3D graph를 입력으로 사용해 geometry-contradictory answer 또는 planning
   error가 감소하는지 비교한다.

**Open3DSG 집중 효과 분석.**

- Source의 family별 candidate count와 Violation
- score dynamic range
- compatibility와 source score의 within-family rank correlation
- 바뀐 top-\(K\) candidate 수
- exact-match로 새로 들어오고 나간 candidate 수

이를 VL-SAT/SGFN과 같은 표로 비교해 큰 효과가 source quality, candidate diversity,
score compression 중 무엇과 연관되는지 설명한다. 인과로 단정하지 않고 descriptive
analysis로 보고한다.

**이슈 종료 기준.**

- Main claim을 shared-target cross-predictor evidence로 정확히 제한하면 최소 방어는
  가능하다.
- Dataset-general claim을 하려면 독립 target에서 동일 방향의 결과와 충분한 coverage가
  필요하다.
- Practical-impact claim을 하려면 downstream metric이 필요하다. 없으면
  Introduction의 downstream use는 motivation으로만 두고 결과 claim으로 연결하지
  않는다.

**원고 반영 위치.**

- Abstract/Introduction/Conclusion: `shared target`을 유지
- Results: Open3DSG가 가장 큰 변화인 이유를 descriptive evidence 범위에서 설명
- Discussion: shared target과 fixed-candidate scope
- Supplement: ReplicaSSG/FROSS의 전체 denominator, coverage, family breakdown

**피해야 할 대응.** 세 predictor를 세 dataset처럼 표현하거나 작은 ReplicaSSG
stress test를 broad generalization evidence로 승격하지 않는다.

#### Major 6. Closest baseline gap `[P0]`

**리뷰어 우려.** RankAvg와 RRF는 fusion baseline이지만 learned compatibility가
simple geometry rule보다 필요한지를 직접 검증하지 않는다.

**현재 상태: 실험 해결, 원고 반영 선택 대기.** 아래 두 baseline class는
canonical candidate pool에서 Docker로 완료됐다. \(K=50\)에서 두 learned
variants 모두 세 predictor의 Positive-density를 Pareto-dominate한다.
Hard-tail/Hard-drop은 verifier labels를 읽는 non-deployable diagnostics다.
상세 수치, artifact, 원고 삽입 위치는 아래 `P0-2. Closest simple baselines`에
정리했다.

**실행된 baseline 두 개.**

1. **Hard verifier filter**
   - Violated candidate는 제거하거나 family tail로 이동한다.
   - Satisfied와 uncertain의 order는 source order로 유지한다.
   - Recall, primary Violation, decidable-only Violation, uncertainty,
     effective list length를 모든 \(K\)에서 보고한다.
   - Candidate 부족 시 top-\(K\)를 어떻게 채우는지 사전에 정의한다.

2. **Continuous geometry-rule re-ranking**
   - Training-positive distributions에서 distance/height/overlap의 continuous
     compatibility를 구성한다.
   - Rule parameter와 threshold는 training split에서만 고정한다.
   - 현재와 동일한 \(Z\times C\)와 family-aware ranking을 적용한다.
   - Learned head와의 유일한 차이가 compatibility estimator가 되도록 한다.

**가능하면 추가할 baseline.**

- Training-positive likelihood 또는 kernel-density compatibility
- k-nearest-neighbor geometry compatibility
- Score-only calibration control. Calibration은 source order를 보존하므로 단독
  Recall 변화가 없어야 하며, product에 들어갔을 때만 scale effect를 검증한다.

**공정성 조건.**

- 같은 candidate pool, same family scope, same source scores, same top-\(K\),
  same verifier, same bootstrap resamples
- Rule baseline도 evaluation verifier status label을 직접 score로 쓰는 경우와
  training-derived measurement만 쓰는 경우를 분리
- Main verifier 자체를 scoring baseline으로 사용하면 circular upper-bound 성격을
  명시

**이슈 종료 기준.**

- Learned variants가 hard filter보다 Recall을 더 잘 보존하면서 낮은 Violation을
  달성해야 soft learned re-ranking의 장점이 성립한다.
- Learned variants가 continuous rule baseline보다 여러 predictor에서 더 나은
  Recall--Violation operating point를 보여야 feature interaction과
  counterfactual learning의 필요성이 설득된다.
- Simple baseline과 동률이면 novelty claim을 `learned estimator superiority`가
  아니라 identity-preserving, transformation-consistent constrained framework로
  좁힌다.

**원고 반영 위치.**

- Experiments, Baselines: 각 baseline의 information access와 ranking scope
- Main table 또는 compact \(K=50\) comparison: 적어도 Source, hard filter,
  continuous rule, Linear, MLP
- Supplement: 모든 \(K\), uncertainty, coverage, family-specific results

**피해야 할 대응.** Evaluation verifier의 binary status를 직접 사용한 hard filter만
놓고 learned model이 Recall을 덜 잃는다고 결론내리거나, RankAvg/RRF를
geometry-rule baseline의 대체물로 취급하지 않는다.

#### Major 7. Artifact-level reproducibility
`[기술 대응 완료, public row bundle은 terms 확인 대기]`

**리뷰어 우려.** Compact JSON summaries는 결과를 보존하지만 Table 1--3과 Figure 3를
row level에서 재계산할 수 없어서 result verification이 제한된다.

**완료된 대응.** Pseudonymized derived-row exporter와 one-command Docker
reproducer를 구현했다. Tables 1--3, Figure 3 data, verification rendering을
재생성하며 291 canonical cells가 tolerance \(10^{-12}\)에서 maximum absolute
error 0으로 일치한다. Original IDs와 raw geometry는 제외되고 input, bundle,
output hashes가 manifest에 고정된다. 아래 공개 schema, privacy, one-command
verification 요구는 모두 충족한다. 다만 derived-row redistribution permission은
명시적으로 확인되지 않아 public ZIP 포함만 보류한다. 허용되지 않는 경우의 종료
조건인 deterministic licensed-input export command와 expected manifest는 이미
제공한다.

**권장 공개 schema.**

- 익명화된 `scan_id`, `context_id`, `subject_id`, `object_id`
- predicate, relation family
- predictor ID, source score, source rank
- Linear/MLP compatibility와 transformed compatibility
- 각 ranking rule의 rank 또는 deterministic regeneration에 필요한 utility
- exact-match flag
- primary verifier status와 point/mesh status
- 필요한 geometry features. Dataset license가 좌표 공개를 제한하면 raw point/mesh
  대신 derived scalar와 regeneration pointer를 제공
- split, protocol version, model hash, score hash

**필수 privacy/anonymity 검사.**

- Local absolute path, username, hostname, Git remote, author name 제거
- README에 author-owned URL을 넣지 않음
- Dataset 원본 payload와 license-restricted mesh/scan을 ZIP에 복제하지 않음
- Stable IDs는 원 ID를 복원할 수 없는 salted hash 또는 dataset policy가 허용하는
  public ID를 사용

**one-command verification 목표.**

1. Schema와 manifest 검증
2. Candidate identity uniqueness와 row counts 검증
3. Table 1, Table 2, Table 3 재생성
4. Figure 3 재생성
5. Canonical outputs와 numeric tolerance 비교

Command는 Docker 안에서 실행되고 dependency/version, random seed, expected output
hash를 기록해야 한다.

**이슈 종료 기준.**

- Clean extraction 후 dataset inference 없이 공개 row artifact에서 모든 main
  numeric table과 trade-off figure가 재생성된다.
- 생성 결과가 canonical JSON/PDF source values와 exact 또는 사전 정의된 floating
  tolerance 안에서 일치한다.
- Row-level 공개가 license 때문에 불가능하면, 최소한 deterministic download/join
  command와 expected intermediate manifest를 제공하고 제한 이유를 명시한다.

**원고/패키지 반영 위치.**

- Reproducibility checklist: 공개 범위와 license 제한
- Supplement, reproducibility section: command, schema, manifest
- Code/Data ZIP README: 단일 entrypoint와 expected outputs
- Release manifest: file counts와 checksums

**피해야 할 대응.** Summary JSON의 존재를 full reproducibility라고 표현하거나,
실행에 필요한 ignored local artifact를 문서화하지 않은 채 source code만 공개한다.

#### Minor 1. Verifier 설명 부족 `[P2]`

**대응.** Main Metrics subsection에 family별 판정 원리를 한 문장씩 추가한다.

- Proximity: pair separation과 overlap evidence
- Vertical order: signed relative height
- Support/contact: gap, overlap, point-level contact evidence
- Uncertain: required measurement가 없거나 conflicting evidence인 경우

Threshold 수치와 예외 규칙은 supplement 표로 보낸다. Main에는 verifier가
compatibility model과 동일한 estimator가 아니라 fixed evaluation procedure라는 점을
명시한다.

**종료 기준.** 처음 읽는 reviewer가 supplement 없이도 satisfied, violated,
uncertain의 의미와 세 family의 evidence type을 설명할 수 있어야 한다.

#### Minor 2. Violation denominator와 uncertainty `[P2]`

**대응.**

1. Main에서 uncertain을 denominator에 포함하는 이유를 `lack of evidence is not
   counted as a contradiction`으로 한 문장 설명한다.
2. Coverage, uncertainty rate, decidable-only Violation,
   uncertain-as-violation을 supplement에 같은 \(K\) grid로 보고한다.
3. Method가 uncertain candidate를 늘려 primary Violation을 낮춘 것이 아닌지
   Source 대비 \(\Delta N_s,\Delta N_u,\Delta N_v\) 또는 rate 변화로 확인한다.

**종료 기준.** Primary conclusion이 decidable-only와
uncertain-as-violation에서도 방향상 유지되고, uncertainty 증가만으로 설명되지
않아야 한다. 유지되지 않으면 primary metric 결과를 단독 reliability claim으로
사용하지 않는다.

#### Minor 3. Training stochasticity `[P2 완료, bounded]`

**대응.**

- Linear와 MLP를 최소 5개의 사전 고정 seed로 train split에서 다시 fit한다.
- Negative construction이 stochastic이면 sample seed도 model seed와 분리해
  기록한다.
- 각 predictor와 \(K\)에서 mean, standard deviation, min/max를 보고한다.
- Evaluation scan bootstrap과 training-seed variance를 섞지 않고 별도로 보고한다.
- Active model은 seed를 보고 고르지 말고 predeclared seed 또는 development criterion
  으로 고정한다.

**종료 기준.** Seed variation이 Source 대비 reported gain의 방향을 뒤집지 않아야
한다. 뒤집히면 single-seed point estimate claim을 낮추고 ensemble 또는 deterministic
fit을 고려한다.

**완료 protocol과 검증.**

- Frozen protocol:
  `experiments/RelCompat3D_geom_reliability/seed_robustness_v1/protocol.json`
- Docker evaluator:
  `src/relcompat3d/evaluate_seeds.py`
- Predeclared seeds:
  `20260714`, `20260715`, `20260716`, `20260717`, `20260718`
- Compact results:
  `experiments/RelCompat3D_geom_reliability/seed_robustness_v1/evaluation/`
- Manifest SHA-256:
  `2bcc816f3307ab22fe93002d2db0db930b7a0088aacda54315b5aba1c78d09fe`
- Active Linear/MLP parameter reproduction과 main reference point estimates가
  모두 validation을 통과했다.
- Active MLP seed 20260714는 분석 전에 고정됐고 결과를 보고 재선택하지 않았다.

**결과.**

- Linear는 deterministic zero initialization과 full-batch fitting을 사용해 다섯
  실행의 model hash와 모든 metrics가 정확히 같다.
- MLP는 15 predictor--\(K\) cells 중 14개에서 다섯 seed 모두 Source 대비
  Recall non-decrease와 Violation non-increase를 유지한다.
- 유일한 예외는 VL-SAT \(K=50\), seed 20260718이다. Recall은 92.724\%에서
  92.699\%로 exact-label relation 한 건 감소하고 Violation은 2.675\%에서
  1.821\%로 감소한다.
- 따라서 MLP initialization에 catastrophic dependence가 있다고 보기는 어렵지만,
  seed-uniform Pareto improvement는 성립하지 않는다.

**Supplement 반영.**

- `[x]` `tab:seed-robustness`에 predictor별 모든 \(K\)의 Recall/Violation
  mean과 population SD를 보고한다.
- `[x]` Scan bootstrap과 training-seed variation을 별도 uncertainty로 설명한다.
- `[x]` One-relation exception과 active seed non-selection을 명시한다.

**Main 반영 판단.**

- Main claim은 active frozen fit의 point estimate와 scan-resampling interval로
  이미 한정돼 있으므로 seed 표를 main에 추가할 필요는 없다.
- 향후 reviewer response나 main prose에 한 문장을 넣는다면 Experimental Setup의
  split 문장 다음에 다음처럼 쓸 수 있다.

  > Five predeclared fits reproduce the Linear result exactly and show small
  > MLP variation; one VL-SAT \(K=50\) seed trades one exact-label relation for
  > lower Violation, as detailed in the supplement.

- 사용자가 main 반영을 보류했으므로 현재 main source에는 넣지 않았다.

#### Minor 4. Qualitative cherry-picking `[P2]`

**대응.**

1. Qualitative taxonomy를 사전에 정의한다: correct demotion, correct promotion,
   harmful demotion, harmful promotion, unchanged contradiction, uncertain.
2. Predictor와 family별로 random 또는 stratified sample을 뽑고 sampling seed와
   inclusion rule을 기록한다.
3. 각 category의 count와 representative examples를 supplement에 보고한다.
4. Main Figure 1은 illustrative example로만 부르고 representative 또는 typical이라고
   주장하지 않는다.
5. Promotion 사례에는 exact-label GT와 verifier-satisfied 조건을 명시한다.

**종료 기준.** 선택된 Figure 1 외에도 random/stratified sample에서 beneficial
membership change가 관찰되고 harmful cases와 uncertain cases도 함께 공개되어야
한다.

#### Minor 5. Open3DSG context coverage `[P2]`

**대응.** Experimental Setup의 Open3DSG 소개 직후 다음 정보를 한 문장으로 둔다.

- Public preprocessing이 548개 중 533개 context에 candidates를 생성함
- 나머지 15개는 empty candidate list로 평가함
- Recall denominator와 shared target scope에서는 제외하지 않음

Supplement에는 predictor별 non-empty contexts, candidate rows, ground-truth
denominator, coverage를 표로 둔다.

**종료 기준.** Main의 `548 contexts`가 candidate coverage 100%로 오해되지 않고,
empty context 처리 방식이 metric 재현에 충분히 명시되어야 한다.

#### Minor 6. Fixed-candidate recall ceiling
`[실험·supplement 대응 완료, main 직접 문장은 저자 선택]`

**대응.** Method 첫 문단 또는 Discussion에 다음 구조의 한 문장을 둔다.

> RelCompat3D can change only the order of supplied candidates. It cannot
> recover a missing predicate candidate, correct object instances, or create
> missing objects.

Predictor별 candidate-pool coverage와 active-route, family-slot,
unconstrained oracle Recall@\(K\)를 Docker로 계산하고 supplement에 보고했다.
Pool coverage는 VL-SAT 99.72%, Open3DSG 79.68%, SGFN 99.72%다.
\(K=50\) active-route oracle Recall은 각각 96.73%, 63.72%, 86.05%로,
observed method와 oracle 사이의 ranking headroom 및 Open3DSG의
missing-candidate ceiling을 분리한다.

**종료 기준 판정.** Generator replacement가 아니라 post-source re-ranking이라는
범위는 Abstract, Introduction, Method에서 일관되고 missing-candidate recovery
주장은 없다. Oracle evidence는 supplement에 반영됐다. Main에서 한계를 더 직접
표현하려면 Discussion의 첫 문단에서
`RelCompat3D can reorder only supplied candidates and cannot recover missing
relations or object instances.`를 `RelCompat3D assumes known object instances`
문장 바로 앞에 추가한다. 이 문장은 정확하지만 main page pressure가 있으면
Method 첫 문장의 existing scope와 supplement oracle로도 bounded claim은 유지된다.

### P0-1--P0-4와 후속 Major/Minor 진단의 대응 현황

다음 판정은 active main source와 supplement, 그리고
`active_method.json`이 가리키는 canonical evaluation을 기준으로 한다. 과거 또는
development-stage artifact에 수치가 있더라도 active candidate pool과 ranking
route를 재현하지 않으면 현재 paper의 근거로 보지 않는다.

| 항목 | Main paper | Supplement | Existing artifact | 현재 판정 |
|---|---|---|---|---|
| P0-1 score mapping | Score type과 raw product를 정의하고 RankAvg/RRF를 비교함. 새 결과 문장은 아직 넣지 않음 | Frozen smooth/percentile mappings, all-\(K\) favorable counts, worst changes, rank stability를 `tab:score-mapping-sensitivity`에 반영함 | Canonical pool의 seven-mapping Linear/MLP sensitivity와 rank stability가 Docker에서 완료됨 | **Supplement 반영 완료. Main 한 문장은 저자 후속 선택으로 유지** |
| P0-2 simple baselines | Source, rank fusion, distance-only, compatibility-only가 있음. 새 결과 문장은 아직 넣지 않음 | Positive-density all-\(K\) 비교와 label-consuming Hard-tail/Hard-drop diagnostics를 각각 `tab:simple-baseline`, `tab:direct-verifier-diagnostics`에 반영함 | Canonical pool의 Hard-tail, Hard-drop, Positive-density와 paired intervals가 Docker에서 완료됨 | **Supplement 반영 완료. Main 한 문장은 저자 후속 선택으로 유지** |
| P0-3 ranking constraint | Family-slot preservation과 Product (all families)를 설명함. 새 해석 문장은 아직 넣지 않음 | Matched family-slots/P/V-global all-\(K\) 비교와 broader route relaxations를 `tab:routing-constraint`, `tab:routing-relaxations`에 반영함 | Canonical pool에서 Linear/MLP matched routing controls와 paired intervals가 Docker에서 완료됨 | **Supplement 반영 완료. Main 한 문장은 저자 후속 선택으로 유지** |
| P0-4 construct dependence | Leakage boundary, point/mesh audit, limitation을 이미 명시함 | Dependency matrix, component/feature removal, all-\(K\) point/mesh 방향, uncertainty-policy 결과를 하나의 evidence chain으로 연결함 | Dependency matrix와 compact evidence package가 hash-verified Docker artifact로 완료됨 | **Supplement 반영 완료. Main 추가 불필요** |
| Major 3 component diagnostics | Main은 direct removal의 supplement pointer를 유지함. 새 결과 문장은 아직 넣지 않음 | Linear/MLP aggregate removals, linked-pair margins, transformation errors, transformed-view membership을 `tab:component-removals`--`tab:transformation-diagnostics`에 반영함 | Canonical pool의 matched component diagnostics가 Docker에서 완료됨 | **Supplement 반영 완료. Pairwise claim은 bounded. Main 한 문장은 저자 후속 선택** |
| Minor 3 training seeds | Active frozen fit과 scan-level intervals를 보고함. Seed 결과 문장은 아직 넣지 않음 | 다섯 fit의 all-\(K\) mean/SD와 one-relation exception을 `tab:seed-robustness`에 반영함 | Predeclared five-seed Linear/MLP refit이 Docker에서 완료됨 | **Supplement 반영 완료. Seed-uniform Pareto claim은 제외. Main 추가는 선택 사항** |
| P1-1 row-level reproduction | Main 수치와 caption은 변경하지 않음 | Pseudonymized schema, one-command regeneration, 291-cell exact check를 `Row-Level Regeneration Check`에 반영함 | 601,140 candidates로 Tables 1--3과 Figure 3 data를 maximum error 0으로 재생성함 | **기술·supplement 대응 완료. Derived bundle의 public ZIP 포함은 data terms 확인 후 결정** |
| P1-2 candidate-pool oracle | Fixed-prediction re-ranking 범위는 Method 첫 문장에 있음. 직접적인 ceiling 문장은 아직 넣지 않음 | Pool coverage와 active-route/family-slot/unconstrained all-\(K\) oracle을 `tab:candidate-oracle`에 반영함 | Canonical pool의 exact-label oracle가 Docker에서 완료됨 | **Supplement 반영 완료. Main limitation 한 문장은 저자 후속 선택** |

#### P0-1. Source-score monotonic sensitivity

**완료 protocol과 검증.**

- Frozen protocol:
  `experiments/RelCompat3D_geom_reliability/score_robustness_v1/protocol.json`
- Docker evaluator:
  `src/relcompat3d/evaluate_score_robustness.py`
- Compact results:
  `experiments/RelCompat3D_geom_reliability/score_robustness_v1/evaluation/`
- Canonical gate는 Source, Linear, MLP의 90 Recall/Violation cells를
  absolute error 0으로 재현한다.
- Tier-B input hashes, 548-context universe, 3,972 GT denominator, candidate
  identity uniqueness, source score bounds, family sequence, support/contact
  order가 모두 validation을 통과한다.
- Identity, power \(\gamma\in\{0.5,2,4\}\), logit temperature
  \(T\in\{0.5,2\}\), context-and-family percentile을 Linear와 MLP 모두에
  적용한다. Grid에서 새 method를 고르지 않는다.
- Logit temperature는 monotonic scale stress일 뿐이며 Open3DSG cosine score를
  calibrated probability로 해석하지 않는다.

**결과.**

- 다섯 smooth non-identity mapping에서 Linear는 75/75 conditions가 Source 대비
  Recall non-decrease와 Violation non-increase를 동시에 유지한다.
- MLP는 74/75다. 유일한 예외는 VL-SAT \(K=50\), power 4에서 Recall
  \(-0.025\) percentage points이고 paired interval은
  \([-0.084,0.000]\) points이며 Violation은 0.383 points 감소한다.
- Context-and-family percentile은 scale-independent한 stress condition이지만
  small Recall loss를 만든다. Linear는 SGFN \(K=10,20\)의 2/15 conditions에서
  각각 \(-0.227,-0.151\) points, MLP는 4/15 conditions에서 최대
  \(-0.201\) points다. 모든 percentile condition에서 Violation은 증가하지 않는다.
- 따라서 product는 score-scale invariant하지 않다. Fixed smooth grid에서
  conclusion이 매우 안정적이고 percentile stress에서 작은 Recall sensitivity가
  남는다는 bounded interpretation이 정확하다.

**Main 반영 위치와 권장 문장.**

- `paper/aaai/sec/4_experiments.tex`의 `Baselines and Training`에서
  `We apply the principal controls to both proposed estimators.` 다음에 넣는다.

  > We also test pre-specified monotonic transformations of each source score
  > without selecting a replacement mapping from evaluation results.

- 같은 파일의 Results comparator 문단, 즉 Product 문장 다음에 넣는다.

  > Across five smooth non-identity score mappings, the favorable
  > Recall--Violation direction is retained in all 75 Linear and 74 of 75 MLP
  > predictor--\(K\) settings, while a percentile stress test produces Recall
  > losses of at most 0.23 percentage points without increasing Violation.

**편집 결정.**

- P0-1과 P0-2 결과는 main에 위 문장과 아래 P0-2 문장, 총 두 문장으로
  요약하는 구성이 가장 좋다.
- P0-1의 mapping별 Recall, Violation, paired interval, rank stability는 전부
  supplement에 둔다. Table~1에 mapping row를 추가하면 main comparison의 중심이
  score-transform stress test로 흐려지고 page pressure만 커진다.
- Main과 supplement 어디에서도 `scale-invariant`를 사용하지 않는다.

**Supplement 반영 위치.**

- `[x]` `Supplementary Experiments > Results > Estimator, Fusion, and Routing
  Sensitivities`에 mapping formulas, frozen grid, all-\(K\) summary,
  percentile exceptions, rank-stability lower bounds를 반영했다.
- `[x]` `tab:score-mapping-sensitivity`는 paper-facing compact summary를
  제공하고, full rows는 canonical `score_mapping.csv`와
  `rank_stability.csv`에 유지한다.

#### P0-2. Closest simple baselines

**완료 protocol과 comparator.**

- P0-1과 같은 frozen protocol, canonical candidate pool, family route, source
  scores, \(K\), verifier, bootstrap resamples를 사용한다.
- `Positive-density`는 evaluation verifier status와 counterfactual negatives를
  쓰지 않는다. Training-positive predicate medians와 IQRs로 diagonal robust
  density를 만들고 transformation averaging, \(Z\times C\), active family slots를
  적용한다.
- `Hard-tail`은 re-ranked family 안에서 non-violated rows를 violated rows보다
  먼저 두되 source order와 family slots를 유지한다.
- `Hard-drop`은 primary-verifier violated rows를 제거하고 remaining source order와
  effective selected count를 보고한다.
- Hard-tail과 Hard-drop은 evaluation-verifier outputs를 ranking input으로
  사용하므로 non-deployable direct-verifier diagnostics다.

**결과.**

- \(K=50\)에서 Linear와 MLP 모두 VL-SAT, Open3DSG, SGFN의 Positive-density를
  Recall과 Violation에서 동시에 Pareto-dominate한다.
- 전체 15 predictor--\(K\) conditions에서 Linear는 Positive-density를 12회
  dominate하고 세 조건은 trade-off이며 dominated condition은 없다.
- MLP는 12회 dominate, 두 조건 trade-off, Open3DSG \(K=5\)에서 한 번
  dominated된다.
- \(K=50\)의 Source / Positive-density / Linear / MLP Recall--Violation
  percentages는 VL-SAT에서 92.72/2.68, 91.77/2.68, 92.77/1.97,
  92.72/1.89이고 Open3DSG에서 40.43/13.87, 43.76/5.09, 44.18/3.42,
  46.70/4.13이며 SGFN에서 74.02/3.85, 73.87/4.01, 74.50/2.63,
  74.57/2.58이다.
- Hard-tail은 learned variants보다 Violation이 낮은 경우가 있지만 Recall과
  trade-off한다. 이것은 verifier label을 직접 읽는 upper diagnostic의 expected
  behavior다.
- Hard-drop은 primary Violation 0을 construction으로 보장하고 VL-SAT/SGFN
  \(K=100\), Open3DSG \(K=50,100\)에서 \(K\)보다 적은 rows를 선택한다. 같은-scope
  method ranking으로 사용하지 않는다.

**Main 반영 위치와 권장 문장.**

- `paper/aaai/sec/4_experiments.tex`의 `Baselines and Training`에서 P0-1 pointer
  다음에 넣는다.

  > A non-learned robust-density baseline uses only training-positive geometry,
  > while verifier-label Hard-tail and Hard-drop routes are treated as
  > non-deployable diagnostics.

- Results comparator 문단의 P0-1 result 다음에 넣는다.

  > At \(K=50\), both learned variants Pareto-dominate the training-positive
  > density baseline for all three predictors, while direct-verifier routes are
  > reported only as label-consuming diagnostics.

- Table~1에 세 row를 추가하지 않는다. Positive-density의 \(K=50\) compact table은
  supplement에 두고 main에서는 한 문장으로 참조하는 편이 page budget과 comparator
  scope 모두에 맞다.

**편집 결정.**

- P0-2는 위 한 문장만 main에 두고 Source, Positive-density, Linear, MLP의
  \(K=50\) compact table과 all-\(K\) 결과를 supplement로 보낸다.
- Hard-tail과 Hard-drop은 deployable baseline과 같은 block에서 성능 순위를
  매기지 않는다. Evaluation label access와 effective selected count를 함께
  표시한 별도 diagnostic block으로 둔다.
- 따라서 P0-1과 P0-2를 합쳐 main result 추가량은 정확히 두 문장이다.

**Supplement 반영 위치.**

- `[x]` `Estimator, Fusion, and Routing Sensitivities`에
  `Closest simple baseline`과 `Direct-verifier diagnostics`를 분리했다.
- `[x]` `tab:simple-baseline`은 Source, Positive-density, Linear, MLP의
  all-\(K\) comparable results를 보고한다.
- `[x]` `tab:direct-verifier-diagnostics`는 Hard-tail/Hard-drop의 verifier-label
  access, uncertainty, effective selected count를 별도 보고한다.
- Full paired rows는 canonical `simple_baselines.csv`에 유지한다.

#### P0-3. Family-aware constraint-only ablation

**Main에 이미 있는 내용.**

- `paper/aaai/sec/3_method.tex:86--87`은 source family-slot sequence와
  support/contact subsequence 보존을 정의한다.
- Table~1의 Product (all families)는 모든 family를 re-rank하는 scope comparison을
  제공한다.
- `paper/aaai/sec/4_experiments.tex:119`은 Product가 support/contact selection을
  바꾼다고 명시한다.

**기존 supplement와 artifact에 있던 내용.**

- `paper/aaai/sec/supplement.tex:98--116`은 preservation과 prefix utility를
  증명한다.
- `paper/aaai/sec/supplement.tex:931--967`은 active route에서 support/contact
  \(\Delta R=\Delta V=0\)임을 보고한다.
- `evaluation/support_routing/metrics.csv`에는 `structured_product`,
  `support_passthrough_product`, `family_slot_rerank`가 모두 존재한다.

기존 `support_routing` artifact는 active candidate pool과 점수가 일치하지 않아
matched control로 승격하지 않았다. 대신 다음 canonical control을 새로 완료했다.

**완료 protocol과 검증.**

- Frozen protocol:
  `experiments/RelCompat3D_geom_reliability/routing_controls_v1/protocol.json`
- Docker evaluator:
  `src/relcompat3d/evaluate_routing_constraints.py`
- Compact results:
  `experiments/RelCompat3D_geom_reliability/routing_controls_v1/evaluation/`
- Protocol SHA-256:
  `43c366cc616bddd1bd8907ab2af268086a6f7c41657c4916c47f737c31ef5c1c`
- Manifest SHA-256:
  `f3e3e5dbda813d60a2a47307a876ab2bd1bfdf693085d0e7689bfe64c43a7bca`
- Source, Linear, MLP canonical point estimates를 absolute error 0으로
  재현했다. Identity route도 source ranking을 완전히 재현했다.
- `family_slots`는 source family sequence와 support/contact IDs를 보존했다.
  Direct matched control인 `pv_global`도 support/contact positions와 IDs를
  정확히 보존했다.
- 모든 결과는 157 scans, 548 contexts, \(K\in\{5,10,20,50,100\}\)에서
  동일한 1,000회 paired scan resampling으로 평가했다.

**완료 condition.**

- `family_slots`: active route다.
- `pv_global`: 같은 candidates, compatibility, product utility를 사용한다.
  Support/contact positions와 identity는 고정하고 proximity와 vertical-order만
  하나의 queue로 합친 direct matched control이다.
- `support_order_only`: support/contact의 relative source order만 유지하고
  global competition을 허용한다.
- `all_families`: support/contact에도 compatibility를 적용하는 scope comparison이다.
- `identity_family_slots`: routing implementation이 Source를 재현하는 sanity
  control이다.

**결과.**

- `pv_global`은 Linear에서 Open3DSG의 Recall을 \(K=5,10,20,50,100\)에서
  각각 \(+4.26,+4.46,+1.71,+0.58,+0.98\) percentage points 바꿨다.
  모든 paired Recall interval은 0보다 높다. \(K=50,100\)에서는 Violation도
  각각 0.03, 0.16 points 낮다.
- 같은 control은 MLP에서 Open3DSG \(K=5,10\) Recall을
  \(+3.78,+3.07\) points 높이지만 \(K=50,100\)에서는
  \(-2.92,-3.80\) points 낮춘다. 두 감소의 paired intervals는 0보다 낮다.
- VL-SAT 변화는 작다. SGFN에서는 \(K=50,100\) MLP Recall이
  \(+0.68,+0.25\) points이고 \(K=100\) Violation은 0.14 points 낮다.
- 이 결과는 한 route가 모든 estimator와 \(K\)에서 우월하다는 결론을 지지하지
  않는다. Family slots는 aggregate-optimal route가 아니라 cross-family
  competition과 family-composition 변화를 막는 conservative constraint로
  해석해야 한다.
- 특히 Open3DSG MLP \(K=50\)에서 `pv_global`은 proximity selected count를
  6,295에서 3,423으로 줄이고 vertical-order count를 6,508에서 9,380으로
  늘린다. Support/contact 13,833 rows는 그대로다. Aggregate Recall 감소는
  family composition shift와 직접 연결된다.

**편집 결정과 Main 권장 문장.**

- P0-3은 method-design claim을 직접 검증하므로 main에 한 문장은 남기는 편이
  accept 관점에서 유리하다. Full route별 aggregate, family slice, membership,
  paired interval 표는 supplement로 보낸다.
- Main Results의 Product (all families) 설명 다음에 넣는다.

  > Matched routing controls preserve support/contact exactly but produce
  > estimator- and \(K\)-dependent changes when proximity and vertical-order
  > candidates share a queue, so we treat family slots as a
  > composition-preserving constraint rather than an aggregate-optimal route.

- `[x]` Direct matched `family_slots`/`pv_global` all-\(K\) 수치는
  `tab:routing-constraint`에 반영했다.
- `[x]` `support_order_only`와 `all_families`는 추가 constraint까지 완화하는
  scope comparisons로 분리해 `tab:routing-relaxations`에 반영했다.
- Main Table~1에는 route rows를 추가하지 않는다.

#### P0-4. Construct-dependence package

**Main에 이미 있는 내용.**

- `paper/aaai/sec/3_method.tex:21`은 evaluation rows, source scores,
  verifier-status labels가 training construction에 들어가지 않는다고 명시한다.
- `paper/aaai/sec/4_experiments.tex:148`은 feature-removal와 direct component
  removal을 supplement로 연결한다.
- `paper/aaai/sec/4_experiments.tex:150--156`과 Table~3은 OBB-free point/mesh
  audit을 보고한다.
- `paper/aaai/sec/5_discussion_limitations.tex:5`는 point/mesh audit이 independent
  ground truth가 아니라고 명시한다.

**Supplement에 반영된 내용.**

- Counterfactual rule과 verifier의 shared primitive 및 threshold를 family별로
  공개한다.
- `tab:construct-dependence`가 training construction, primary verifier,
  point/mesh audit의 information access를 직접 비교한다.
- Exact-scalar, related-measurement, alternative-evidence feature removal과
  pairwise-loss/transformation-averaging removals를 보고한다.
- Point/mesh section은 Linear와 MLP의 모든 \(K\), paired interval, coverage,
  14/15 decrease와 한 tie를 보고한다.
- Verifier-uncertainty section은 두 estimator의 primary, decidable-only,
  uncertain-as-violation 결과가 30 predictor--\(K\) settings에서 모두
  non-increasing임을 기록한다.

**현재 판정.**

- 현재 claim을 `verifier-derived reliability on a shared target`으로 유지하는
  경우, construct dependence는 숨겨져 있지 않고 주요 sensitivity도 이미 있다.
- 따라서 P0-4는 새로운 model experiment보다 existing evidence를 한 곳에서
  연결하는 편집이 먼저다.
- Independent physical-validity claim을 하려면 blind human audit 또는 외부
  reference label이 여전히 필요하다. 현재 paper는 그 claim을 하지 않으므로 blind
  audit은 accept를 위한 강한 보강이지만 현재 scoped claim의 필수 누락으로 단정하지
  않는다.

**완료 package와 검증.**

- Frozen protocol:
  `experiments/RelCompat3D_geom_reliability/construct_dependence_v1/protocol.json`
- Docker builder:
  `src/relcompat3d/build_construct_package.py`
- Compact results:
  `experiments/RelCompat3D_geom_reliability/construct_dependence_v1/evaluation/`
- Protocol SHA-256:
  `17425b002c3d26d413d04fec65c25a04a7e341ded5331fc9459fcc0521d29103`
- Manifest SHA-256:
  `caf38e8ab74e0ae76c1f23ffaa6e53c10de4b4fbcf7db6bc6f15dc6da600d426`
- 모든 input hash와 여섯 existing evidence manifest가 검증을 통과했다.
- Exact-scalar, primitive-family, alternative-evidence feature-removal
  conditions가 모두 존재한다.
- Point/mesh agreement는 Linear와 MLP 모두 15 cells 중 14 cells에서
  Violation이 감소하고 SGFN \(K=5\) 한 cell에서 tie다. 증가 cell은 없다.
- Primary, decidable-only, uncertain-as-violated Violation은 두 estimator를
  합친 30 predictor--\(K\) cells 모두에서 Source 대비 non-increasing이다.

Dependency matrix는 다음 범위를 명시한다.

| Information | Training construction | Primary verifier | Point/mesh audit |
|---|---:|---:|---:|
| Evaluation candidate rows | No | Yes | Yes |
| Source relation score | No | No | No |
| Primary verifier status labels | No | Output | No |
| OBB-derived measurements | Some | Yes | No |
| Point/mesh measurements | No | No | Yes |
| Evaluation scene identities | No | Yes | Yes |
| Relation ontology | Yes | Yes | Yes |

**편집 결정.**

- P0-4의 새 결과는 전부 supplement에 둔다. Main은 이미 Table~3,
  feature-removal pointer, Discussion boundary를 가지고 있어 같은 caveat와
  count를 추가하면 중복이 커진다.
- Supplement의 counterfactual-construction table 직후 dependency matrix를
  배치하고, matrix 아래에서 feature-removal, uncertainty-policy, point/mesh,
  component-removal subsection을 한 번씩 연결한다.
- Main에는 새 문장을 추가하지 않는다. 현재 Table~3과 Discussion의
  `not independent reference` boundary를 유지하면 충분하다.
- Blind human audit은 independent physical-validity claim을 추가할 때 필요한
  별도 확장이다. 현재 verifier-derived scoped claim의 unresolved requirement로
  남기지 않는다.

#### P1-1. Row-level one-command paper reproduction

**완료 protocol과 구현.**

- Frozen protocol:
  `experiments/RelCompat3D_geom_reliability/row_reproduction_v1/protocol.json`
- Protocol SHA-256:
  `4e8fc15b9453645a6eb90b8ccb7b8d3d28e89d7003f8b1feabe610de465fbe06`
- Docker exporter:
  `src/relcompat3d/build_reproduction_rows.py`
- Docker reproducer:
  `src/relcompat3d/reproduce_from_rows.py`
- Compact results:
  `experiments/RelCompat3D_geom_reliability/row_reproduction_v1/evaluation/`
- Completed evaluation manifest SHA-256:
  `21ead0d178af66109c2f90707b0560f4e4f1d6f4308486b08955eb6b687f7104`

Exporter는 세 canonical candidate pools와 GT를 읽어 다음 derived rows를 만든다.

- Candidate rows: VL-SAT 220,848, Open3DSG 159,444, SGFN 220,848,
  총 601,140
- Ground-truth rows: 3,972
- Candidate fields: pseudonymized identity, predictor, predicate/family,
  source score, Linear/MLP compatibility, source/method/control ranks,
  exact-match flag, primary verifier status, point/mesh agreement status
- 제외 fields: original scan/context/instance IDs, object categories, OBB and
  surface measurements, point clouds, meshes, RGB-D data
- Pseudonymization: local secret을 사용한 HMAC-SHA256의 24-hex prefix이며 key는
  artifact에서 제외한다.

**One-command 결과와 검증.**

`relcompat3d_reproduce_rows` Docker service는 derived rows만 읽어 다음을 생성한다.

1. Table 1 전체 six ranking rules
2. Table 2의 Linear controls와 MLP operating points
3. Table 3의 point/mesh agreement Violation 및 measured/decidable coverage
4. Figure 3 data와 independent verification SVG/PNG/PDF
5. Canonical-cell comparison CSV와 hash manifest

Canonical reference 291 cells의 maximum absolute error는 0이고 required tolerance는
\(10^{-12}\)다. Candidate row counts, 3,972 GT denominator, Table 1 selected
count bounds, Table 3 status accounting, row-bundle hashes, canonical reference
hashes가 모두 validation을 통과했다. Verification Figure 3는 numeric
reproduction용 rendering이며 outlined submission asset을 대체하지 않는다.

**배포 권한 경계와 사용자 조치.**

- Derived bundle은 gzip 기준 약 61 MiB다.
- Official 3DSSG access가 3RScan terms 동의를 요구한다는 사실은 확인했지만,
  source-derived annotation rows의 재배포를 명시적으로 허용하는 조항은
  확인하지 못했다.
- 따라서 current release ZIP에는 bundle을 넣지 않고 exporter, schema, compact
  regenerated outputs, expected manifests만 포함한다.
- 제출 전 저자가 3RScan/3DSSG terms 또는 data owner에게 derived-row redistribution
  허용 여부를 확인해야 한다. 허용되면 bundle과 manifest를 ZIP에 추가하고,
  허용되지 않으면 licensed inputs에서 동일 bundle을 만드는 deterministic export
  command를 공식 경로로 유지한다.

**Main 및 supplement 편집 결정.**

- Main paper에는 새 result sentence를 넣지 않는다. 이 분석은 method claim이 아니라
  artifact reproducibility를 방어한다.
- Reproducibility checklist와 anonymous README에는 `licensed external inputs`,
  one-command outputs, 291-cell tolerance check, redistribution condition을
  사실대로 기록한다.
- `[x]` Supplement의 `Supplementary Experiments > Experimental Setup >
  Row-Level Regeneration Check`에 schema boundary, regenerated artifacts,
  291-cell exact check, license-dependent redistribution을 반영했다.

#### P1-2. Candidate-pool oracle Recall

**완료 protocol과 구현.**

- Frozen protocol:
  `experiments/RelCompat3D_geom_reliability/candidate_oracle_v1/protocol.json`
- Protocol SHA-256:
  `3591a5b2265310cfb426e31af24f4ee957c9172625d5e49ab15e219dc8415c86`
- Docker evaluator:
  `src/relcompat3d/evaluate_candidate_oracle.py`
- Compact results:
  `experiments/RelCompat3D_geom_reliability/candidate_oracle_v1/evaluation/`
- Completed manifest SHA-256:
  `a7aee28622c84a21aa61c92a6e288f08b58a3e33d69b42118c296cfa2d20a563`

Oracle는 active method를 선택하거나 변경하지 않는 post-hoc diagnostic이다.
세 upper bound의 정의는 다음과 같다.

- `Active-route oracle`: source top-\(K\) family counts와 selected
  support/contact subsequence를 고정하고 proximity와 vertical-order slots만
  exact-match candidates로 최적화한다.
- `Family-slot oracle`: source top-\(K\) family counts만 보존하고 각 family
  내부를 최적화한다.
- `Unconstrained oracle`: context별 fixed candidate pool에서 family constraints
  없이 최대 \(K\) exact-match candidates를 선택한다.

**결과.**

- Exact-label candidate-pool coverage는 VL-SAT 99.72%, Open3DSG 79.68%,
  SGFN 99.72%다.
- \(K=50\) Source / best active variant / Active-route oracle /
  Family-slot oracle / Unconstrained oracle Recall percentages:
  - VL-SAT: 92.72 / 92.77 / 96.73 / 99.52 / 99.72
  - Open3DSG: 40.43 / 46.70 / 63.72 / 73.46 / 79.68
  - SGFN: 74.02 / 74.57 / 86.05 / 88.07 / 99.72
- \(K=100\) Active-route oracle는 VL-SAT 98.79%, Open3DSG 71.88%,
  SGFN 98.49%다.
- Open3DSG는 fixed pool 자체가 전체 GT의 20.32%를 포함하지 않아
  re-ranking으로 복구할 수 없는 candidate-generation ceiling이 크다.
- 세 predictor 모두 active-route oracle와 observed method 사이에 headroom이
  남아 있으므로 현재 결과가 candidate-pool ceiling에 도달했다고 주장하지 않는다.

**검증.**

Row-bundle hashes, candidate identity uniqueness, 3,972 denominator,
finite values, \(K\)에 따른 oracle monotonicity가 모두 통과했다. 모든 cell에서
observed Linear/MLP Recall은 active-route oracle 이하이고,
active-route \(\leq\) family-slot \(\leq\) unconstrained ordering도 유지된다.

**Main 및 supplement 편집 결정.**

- `[x]` Supplement의 `Candidate-Pool Oracle Recall` subsection과
  `tab:candidate-oracle`에 세 predictor와 다섯 \(K\) 전체를 반영했다.
- Main Table~1이나 Figure~3에는 oracle curve를 추가하지 않는다. Oracle은
  attainable comparator가 아니며 main trade-off plot에 넣으면 method result로
  오해될 수 있다.
- Main에 한 문장을 넣는다면 Discussion 첫 문단에서
  `RelCompat3D assumes known object instances` 바로 앞에 다음 bounded sentence를
  둔다.

  > RelCompat3D can reorder only supplied candidates and cannot recover
  > missing relations or object instances; candidate-pool upper bounds are
  > reported in the supplement.

- 이 main 문장은 reviewer가 fixed-candidate ceiling을 핵심 한계로 볼 때
  유용하지만, 현재 Method 첫 문장의 `re-ranks fixed relation predictions rather
  than replacing a generator`와 supplement oracle로 scope가 이미 분명하므로
  page pressure가 크면 저자 후속 선택으로 남긴다.

### P0 prerequisite 결과

P0-1과 P0-2에 필요한 VL-SAT, Open3DSG, SGFN verifier rows, shared GT,
training export, official context annotation을 ignored local archive에서
중복 복사 없이 참조했다. Protocol은 모든 input hash를 실행 전에 고정한다.
최종 manifest는 다음을 모두 통과한다.

1. 모든 Tier-B file hashes가 frozen values와 일치한다.
2. Candidate prediction IDs는 source별로 unique하다.
3. Evaluation universe는 548 contexts와 3,972 GT relations다.
4. Canonical Source, Linear, MLP의 90 metric cells가 absolute error 0으로
   재현된다.
5. 새 결과는 `score_robustness_v1/evaluation/`에 저장되어
   `no_family_indicator_v1`과 `active_method.json`을 변경하지 않는다.
6. Docker command, inputs, outputs, validations, warnings, claim boundary가
   manifest에 기록된다.

다른 컴퓨터에서 full rerun하려면 `docs/reproducibility.md`의 hash-locked Tier-B
rows를 복원해야 한다. Compact CSV, JSON, manifest 검증에는 raw rows가 필요하지
않다.

### 수정된 실행 우선순위와 의사결정 순서

1. `[x]` **Tier B hash와 canonical rerun gate**
2. `[x]` **P0-1 score mapping sensitivity**
3. `[x]` **P0-2 closest simple baselines**
4. `[x]` **P0-3 routing constraint controls**
5. `[x]` **P0-4 construct-dependence package**
6. `[x]` P0-1--P0-4의 full paper-facing evidence를 supplement에 반영했다.
   Percentile sensitivity, verifier-label access, mixed routing result,
   construct-dependence boundary를 숨기지 않았다.
7. `[저자 후속 선택]` Main에는 P0-1과 P0-2 결과를 각 한 문장으로 요약할지
   결정한다. 반영한다면 위에 기록한 정확한 위치와 bounded wording을 사용한다.
8. `[저자 후속 선택]` P0-3의 mixed result를 한 문장으로 추가한다면 current
   route를 aggregate-optimal로 쓰지 않고 composition-preserving constraint로
   한정한다. Official evaluation에서 route를 재선택하지 않는다.
9. `[x]` P0-4는 supplement dependency matrix와 existing evidence chain으로
   통합했다. Main의 existing audit와 limitation은 반복하지 않는다.
10. `[x]` Major 3 component diagnostics와 Minor 3 five-seed robustness를
    frozen Docker protocol로 완료하고 supplement에 반영했다.
11. `[x]` P1-1 row-level one-command reproduction을 완료했다. Tables 1--3과
    Figure 3 data의 291 canonical cells가 maximum absolute error 0으로
    재생성된다. Derived bundle의 public ZIP 포함만 data terms 확인을 기다린다.
12. `[x]` P1-2 candidate-pool oracle를 완료하고 all-\(K\) pool coverage,
    active-route, family-slot, unconstrained upper bounds를 supplement에 반영했다.
13. `[x]` P1 분석을 포함한 supplement를 재빌드해 unresolved reference와
    LaTeX overfull warning이 없음을 확인했다. Canonical
    `supplement_aaai27.pdf`는 19 US-Letter pages이며 SHA-256은
    `505361303b01c46a3cba01f7ae9e7e7c708a39ac1fa8d5e7e1ea6698b095ff5f`다.
14. `[다음: 저자 선택]` P0-1/P0-2의 두 결과 문장과 P0-3의 한 bounded
    interpretation 문장을 main에 넣을지 결정한다. P0-4는 main에 반복하지 않는다.
    Major 3, Minor 3, P1-2의 optional one-sentence pointers도 같은 시점에
    판단한다.
15. `[사용자 확인]` 3RScan/3DSSG terms 또는 data owner를 통해 pseudonymized
    derived-row bundle의 public redistribution 가능 여부를 확인한다.
16. `[후속]` Main 반영 여부와 row-bundle 배포 여부가 결정되면 release bundle과
    one-command
    regeneration manifest를 최종 갱신한다.

### Rebuttal 작성 원칙

- 각 답변은 `Concern → controlled comparison → numeric result → bounded
  interpretation → manuscript change` 순서로 쓴다.
- 기존 표의 수치를 반복하는 대신 reviewer가 제기한 alternative explanation을
  직접 차단하는 새 비교를 제시한다.
- 수행하지 않은 실험을 계획처럼 쓰지 않는다. Rebuttal 시점에 완료된 결과만
  과거형으로 기술한다.
- 실패하거나 mixed result가 나오면 숨기지 않고 claim을 좁힌다. 특히 dataset
  generalization, independent validity, scale invariance, component-level gain은
  근거 없이 사용하지 않는다.
- “scope가 다르다”, “supplement에 있다”, “future work다”만으로 Major concern을
  닫지 않는다.
