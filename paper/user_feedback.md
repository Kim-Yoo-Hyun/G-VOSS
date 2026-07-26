# RelCompat3D Active-Section 통합 재검토

- 검토일: 2026-07-26 KST
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
  후 Docker smoke build를 통과한 상태다.

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
- `[~]` Point/mesh audit와 feature-removal analysis로 circularity를 완화한다.
- `[ ]` 핵심 Violation metric에 독립적인 human 또는 physical-validity ground
  truth가 없다.
- `[ ]` Training counterfactual과 primary verifier가 OBB measurements와 일부
  threshold를 공유한다.
- `[ ]` \(u=ZC^{tr}\)가 source-score scale과 monotonic reparameterization에
  민감하다.
- `[~]` 모든 \(K\)에 대한 주장은 point estimate로 제한되지만 통계적 지지는
  predictor와 \(K\)에 따라 다르다.
- `[ ]` Linked pairwise loss와 transformation averaging이 실제 aggregate gain에
  거의 기여하지 않는다.

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
- `[ ]` Closest post-hoc alternatives와 직접적인 실험 비교가 부족하다.
- `[ ]` Component removal 결과가 pairwise loss와 transformation averaging의
  실질적 필요성을 약화한다.

#### Clarity

- `[x]` 전체 문제에서 방법과 실험으로 이어지는 흐름은 파악할 수 있다.
- `[x]` Linear와 MLP의 차이와 re-ranking scope는 비교적 명확하다.
- `[~]` Metric formula는 정의되지만 verifier가 satisfied, uncertain, violated를
  판정하는 핵심 규칙은 main paper에 없다.
- `[~]` Family-aware ranking의 동작은 설명되지만 source family sequence를 반드시
  보존해야 하는 이유는 충분히 설득되지 않는다.
- `[ ]` 세 predictor의 candidate pool과 context가 실제로 어떻게 대응되는지 처음
  읽는 reviewer에게 불명확하다.
- `[ ]` Open3DSG의 15개 empty context와 score-range 특성이 main paper에서 보이지
  않는다.

#### Experimental rigor

- `[x]` Training, development, evaluation split이 분리된다.
- `[x]` Scan-level paired bootstrap과 여러 \(K\)를 보고한다.
- `[x]` Wrong-pair, wrong-predicate, shuffled-geometry controls를 포함한다.
- `[~]` MLP matched controls는 supplement에만 존재한다.
- `[ ]` Hard-rule filtering의 완전한 Recall--Violation trade-off가 없다.
- `[ ]` Score calibration, monotonic rescaling, simple threshold rescoring 같은
  직접 baseline이 없다.
- `[ ]` Family-aware constraint 제거만을 분리한 matched ablation이 없다.
- `[ ]` Model-training seed variation이나 repeated fitting variance가 없다.
- `[ ]` 많은 predictor--\(K\) 비교에 대한 multiplicity 처리가 없다.
- `[ ]` Qualitative evidence가 같은 context에서 선택된 소수 사례에 머문다.

#### Reproducibility

- `[x]` Source code, Docker configuration, model locks, protocol, compact
  results가 제공된다.
- `[x]` Main과 supplement에 대부분의 hyperparameter와 training construction이
  기록된다.
- `[~]` Public datasets와 source checkpoints를 사용하므로 일부 외부 의존성은
  불가피하다.
- `[ ]` Row-level candidate, geometry, verifier input이 release ZIP에서 빠져 있어
  reported tables를 artifact만으로 재생성할 수 없다.
- `[ ]` 원 source inference에서 compact result까지의 완전한 end-to-end
  reproduction은 현재 package만으로 불가능하다.

#### Limitations

- `[x]` Single target, known instances, support/contact 제외, independent validity
  label 부재를 인정한다.
- `[ ]` Source-score scale sensitivity를 limitation으로 명시하지 않는다.
- `[ ]` Reconstruction noise, OBB error, partial observation의 영향을 충분히
  논의하지 않는다.
- `[ ]` Fixed candidate re-ranking이 missing relation을 복구할 수 없다는 한계가
  명시적이지 않다.
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

#### Major 3. 핵심으로 소개한 component가 실제 결과를 설명하지 못한다

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

#### Major 7. 제공 artifact만으로 핵심 수치를 재생성할 수 없다

> “The released artifacts provide these additional metrics for all five
> \(K\) values.”

현재 ZIP은 code, protocols, locks, compact summaries를 제공하지만 row-level
predictions, joined geometry, verifier inputs가 없다. Reviewer는 JSON summary를
검증할 수는 있어도 Table 1--3을 처음부터 재계산할 수 없다.

원 source repository와 datasets가 필요하다는 것은 이해할 수 있으나, 최소한
anonymized candidate-level evaluation rows나 deterministic regeneration inputs가
있어야 reported metrics의 실질적 reproducibility가 높아진다.

#### Minor 1. Main paper에서 verifier가 지나치게 불투명하다

> “the rule-based geometry verifier returns satisfied, uncertain, or violated”

Main에는 각 family에서 무엇이 satisfied 또는 violated인지, uncertain이 어떤
경우인지 설명이 없다. 논문의 핵심 \(V@K\)를 이해하려면 supplement를 읽어야 한다.

#### Minor 2. Primary Violation denominator가 직관적이지 않다

> “Thus uncertain candidates enter the denominator but not the numerator.”

Uncertain candidate가 많아지면 Violation이 인위적으로 낮아질 수 있다. Supplement의
decidable-only와 uncertain-as-violation sensitivity가 방향성을 지지하지만 primary
metric 선택의 근거가 main에서 부족하다.

#### Minor 3. 학습 stochasticity가 평가되지 않는다

> “RelCompat3D-MLP uses one shared multilayer perceptron (MLP) with a single
> two-unit ReLU hidden layer.”

Bootstrap은 evaluation scan uncertainty만 반영한다. MLP fitting seed,
initialization, negative sampling에 따른 variance가 보고되지 않는다.

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
2. Source score에 temperature, power, percentile 같은 monotonic mapping을
   적용했을 때 \(ZC^{tr}\) 결과가 얼마나 변하는가?
3. Linked pairwise loss와 transformation averaging을 제거해도 main metrics가 거의
   동일한데 왜 이를 main methodological contribution으로 봐야 하는가?
4. Source family sequence를 보존하지 않는 proximity/vertical-only global
   re-ranking과 비교하면 어떻게 되는가?
5. Product (all families)가 더 높은 aggregate Recall을 얻는 setting에서
   support/contact에 실제로 어떤 regression이 발생하는가?
6. Hard-rule baseline의 Recall, decidable Violation, uncertainty를 RelCompat3D와
   같은 표에서 비교할 수 있는가?
7. VL-SAT과 SGFN의 변화가 작은 이유는 무엇이며 Open3DSG의 큰 변화가 compressed
   cosine-score range 때문이 아님을 어떻게 보이는가?
8. 같은 model fitting을 여러 seed로 반복했을 때 Linear와 MLP 결과의 변동은 어느
   정도인가?
9. 3DSSG 외 target에서 더 큰 evaluation을 제공할 수 있는가? 현재 ReplicaSSG
   172-relation stress test를 어느 정도 일반화 근거로 해석해야 하는가?
10. Anonymous candidate-level rows를 supplementary ZIP에 포함해 Table 1--3을
    source inference 없이 재생성할 수 있는가?

### 예상 Rating

**Weak Reject**

이유는 구현 오류나 명백한 잘못된 수식 때문이 아니다. 문제 설정은 흥미롭고 실험도
성실하지만 AAAI accept 기준에서 다음 네 가지가 동시에 남는다.

- Core metric과 training construction의 construct dependence
- Product utility의 score-scale sensitivity
- Main component removal이 보여주는 제한적인 method necessity
- 한 shared target과 불충분한 direct baseline에 따른 novelty와 significance
  불확실성

독립적인 validity evidence와 score-scale robustness가 추가되고 family-aware
constraint 및 learned compatibility의 필요성을 더 직접적으로 입증하면 Weak
Accept까지 올라갈 수 있다. 현재 상태에서는 “잘 구성된 scoped
diagnostic/rescoring study이지만 top-tier methodological contribution으로는
incremental하다”는 판정이 가장 가능성이 높다.

### Major weakness별 rebuttal 방향

#### 1. Verifier construct dependence

현재 가진 근거를 정확히 묶어야 한다.

- Evaluation rows와 verifier-status labels는 training에 사용하지 않았다.
- Proximity negative threshold와 violation threshold가 완전히 동일하지 않다.
- Exact verifier scalar 제거 후에도 Open3DSG 효과가 유지된다.
- Point/mesh audit은 OBB와 primary labels를 사용하지 않는다.
- Uncertain-as-violation과 decidable-only metric에서도 방향이 유지된다.

다만 “independent validation”이라고 주장하면 안 된다. 가장 강한 대응은 blind
human audit 또는 externally defined relation-validity labels를 추가하는 것이다.

#### 2. Source-score scale sensitivity

가장 필요한 추가 실험은 monotonic mapping sensitivity다.

- \(Z\), sigmoid-temperature \(Z_T\), percentile rank, power transform을 비교한다.
- Mapping parameter는 train/dev에서만 고정한다.
- 각 predictor별 Recall--Violation curve와 ordering stability를 보고한다.
- 가능하면 score-scale-invariant rank utility를 proposed alternative로 제공한다.

현재 RankAvg와 RRF 결과만으로는 product-scale fragility를 방어하기 어렵다.

#### 3. Pairwise loss와 transformation averaging의 작은 metric effect

두 구성요소의 역할을 분리해야 한다.

- Pairwise loss는 core gain이 아니라 training regularizer라고 명시한다.
- Transformation averaging은 aggregate gain이 아니라 exact representation
  consistency guarantee라고 명시한다.
- No-averaging에서 proximity compatibility discrepancy가 최대 0.4532라는 기존
  결과를 전면에 제시한다.
- Endpoint representation을 바꿨을 때 rank와 output이 안정적인지 추가 보고한다.

즉 “성능을 올리는 component”가 아니라 “동일 relation representation에 동일
output을 보장하는 component”로 방어해야 한다.

#### 4. Family-aware ranking necessity

다음 matched variants가 필요하다.

- No-family-sequence preservation
- Proximity/vertical global re-ranking
- Support/contact frozen but family counts unfrozen
- All-family product의 family-specific Recall과 Violation

특히 Product (all families)가 바꾼 support/contact selection 중 정확히 어떤
regression이 있었는지 숫자로 제시해야 한다. “Scope가 다르다”만으로는 부족하다.

#### 5. Limited generalization and practical impact

Supplement의 ReplicaSSG/FROSS 결과를 더 명확히 연결하되 과장하지 않아야 한다.
가능한 추가 근거는 다음과 같다.

- Second target 규모 확대
- Relation-family별 transfer 결과
- Reconstruction quality 또는 geometry shift별 breakdown
- Downstream query 또는 reasoning task에서 corrupted relation 감소 효과

새 실험이 어렵다면 claim을 “shared-target cross-predictor reliability”로 더 좁히고
general framework 표현을 줄이는 편이 안전하다.

#### 6. Baseline gap

최소한 다음 둘은 추가하는 것이 좋다.

- Verifier hard filter의 Recall--Violation--uncertainty trade-off
- Training-derived continuous geometry-rule score와 \(Z\)의 simple product

이 둘보다 learned compatibility가 우수해야 counterfactual learning과 feature
interaction의 필요성이 설득된다.

#### 7. Reproducibility

Code/Data ZIP에 anonymized evaluation rows를 추가하는 것이 가장 직접적이다.

- Candidate identity
- Predicate/family
- Source score
- Geometry features
- Exact-match flag
- Verifier status
- Split/context identifiers의 익명화된 stable ID

이 데이터와 하나의 command로 Table 1--3 및 Figure 3가 재생성되도록 만들면
reviewer의 재현성 우려를 크게 줄일 수 있다.
