# RelCompat3D `user_v6.tex` 통합 재검토

- 검토일: 2026-07-25
- transcript 대상: `paper/user_v6.tex`
- release 점검 대상: `paper/aaai/main.tex`, `paper/aaai/main_teaser.pdf`, `paper/aaai/main_teaser_aaai27.pdf`, supplement, reproducibility checklist
- 기준 제목: **RelCompat3D: Predicate–Geometry Compatibility for Re-Ranking 3D Scene Graph Relations**
- 범위: 논리, 영어, claim, notation, section 구성, Figure와 Table, 기존 이슈, AAAI-27 submission 규정
- 인용: citation 표기 방식은 판단하지 않았다. 선행연구와 section별 첫 약어에 citation이 존재하는지만 확인했다.
- 이번 검토에서는 PDF를 새로 빌드하지 않았다. 기존 PDF, build log, figure asset을 진단했다.

상태 표시는 다음과 같다.

- `[x]` 해결 완료 또는 규정 충족
- `[~]` 핵심 내용은 맞지만 제출 전 짧은 수정 필요
- `[ ]` 제출 전 수정 필요
- `[차단]` 현재 상태로 제출하면 안 되는 규정 또는 release 문제
- `[제외]` 사용자 판단에 따라 검토 대상에서 제외

## 전체 판단

`user_v6.tex`에는 main claim을 무너뜨리는 과학적 모순이 없다. 문제, 설계 선택, 실험 근거, claim boundary가 다음과 같이 연결된다.

1. Introduction은 source relation score와 reconstructed ordered-pair geometry의 불일치를 제기한다.
2. Method는 ordered-pair identity, source-score-excluded compatibility, transformation averaging, family-aware re-ranking으로 문제에 답한다.
3. Experiments는 Source 비교, matched fusion, ordered-pair controls, transformation controls, point- and mesh-based audit로 설계를 검증한다.
4. Discussion and Limitations는 세 predictor를 하나의 shared target에서 평가한 범위를 dataset-level generalization으로 확대하지 않는다.
5. Conclusion은 본문에 없는 새 주장 없이 reported point estimates를 요약한다.

현재 transcript에서 반드시 고칠 substantive issue는 두 개다.

1. normalized-height notation이 `\rm norm`과 `norm`으로 다르다.
2. Ablations and Controls의 `largest Violation increases` 해석이 모든 predictor와 두 \(K\) 값에서 성립하지 않는다.

그 외 transcript 수정은 약어 정의, subsection 이름, 모호한 지시어, source 정리 수준이다.

현재 release는 아직 submission-ready가 아니다. `user_v6.tex`의 `trim`과 `clip`, bold caption lead-in, fresh teaser PDF의 10-page 결과, page 8의 technical content, 4.4306 pt overfull, 생성형 AI 사용 역할의 미공개가 제출 전 차단 항목이다. 기존 9-page canonical PDF는 이 조건을 충족하던 이전 산출물이지만 `user_v6.tex`과 현재 선택 제목보다 오래된 파일이다.

## 기존 이슈 재확인

중복되는 설명은 현재 V6 이슈와 AAAI 이슈에 한 번만 남겼다.

| 기존 번호 | 상태 | `user_v6.tex` 기준 처리 |
|---|---|---|
| 1--59 | `[x]` | 문법, 용어, metric, caption 내용, family-aware ranking 관련 기존 수정 유지 |
| 14 | `[x]` | Method 끝의 supplement 안내 문장 유지 |
| 60--78 | `[x]` | 기존 수정 유지 |
| 79 | `[x]` | Table 3 헤더가 `$\Delta V$`로 유지 |
| 80--86 | `[x]` | 기존 수정 유지, source-score range는 supplement에 존재 |
| 87 | `[제외]` | 사용자 요청에 따라 제외 |
| 88 | `[x]` | coverage 상세는 supplement에 유지 |
| 89 | `[x]` | pairwise-loss removal과 transformation-averaging removal이 supplement에 존재하고 main pointer도 유지 |
| 90--92 | `[x]` | family evidence, artifact 역할, 본문 참조 유지 |
| 93 | `[제외]` | 추가 limitation 제안에서 제외 |
| 94--105 | `[x]` | contribution 압축, story 연결, notation table, loss 일반화 유지 |

### `user_v5.tex`에서 남았던 이슈

| 이전 이슈 | 상태 | `user_v6.tex` 판단 |
|---|---|---|
| V5-1 normalized-height notation | `[ ]` | V6-1로 유지 |
| V5-2 `same separated inputs` | `[x]` | line 99에서 의미가 분명한 문장으로 수정됨 |
| V5-3 verifier 범위 | `[x]` | line 288에서 `candidates labeled as violated by the geometry verifier`로 수정됨 |
| V5-4 Table 3 caption | `[x]` | agreement rule과 M/D 의미가 caption에 직접 설명됨 |
| V5-5 `source scores` | `[x]` | line 23에서 `source relation scores`로 통일됨 |
| F-1 loss equation 일반화 | `[x]` | symbolic hyperparameter와 실제 설정값이 분리됨 |
| F-2 기호 정의 | `[~]` | `\sigma`와 `\theta_q`는 정의됨. V6-1 표기만 남음 |
| F-3 compact MLP 설정 | `[x]` | two hidden units가 main에 있고 parameter count는 supplement에 있음 |

## 현재 transcript 수정 이슈

### V6-1. normalized-height notation 불일치 `[ ]`

- 심각도: 중간
- Section: Method, Linear Estimator
- 위치: `paper/user_v6.tex:106`, `paper/user_v6.tex:109`

수식:

> `\Delta z_i^{\rm norm}`

정의 문장:

> `\Delta z_i^{norm}`

같은 feature이므로 표기를 일치시켜야 한다.

권장:

```tex
We define $\Delta z_i=z_{s_i}-z_{o_i}$ and
$\Delta z_i^{\rm norm}=2\Delta z_i/(h_{s_i}+h_{o_i})$.
```

### V6-2. ablation의 `largest` 해석이 수치 전체와 일치하지 않음 `[ ]`

- 심각도: 중간
- Section: Experiments, Ablations and Controls
- 위치: `paper/user_v6.tex:311`

원문:

> A wrong predicate and an endpoint swap that keeps the predicate fixed produce the largest Violation increases.

Open3DSG에서는 이 해석이 맞다. 그러나 VL-SAT의 두 \(K\) 값과 SGFN의 \(K=50\)에서는 Distance only의 Violation이 더 높다. 따라서 모든 predictor와 두 \(K\)에 대한 문장으로는 과하다.

권장:

> A wrong predicate and an endpoint swap that keeps the predicate fixed sharply increase Violation. Their nearly identical aggregate values are consistent with both controls reversing the signed interpretation of vertical-order geometry.

이 수정은 control의 의미를 유지하면서 표 수치와 정확히 맞춘다.

### V6-3. MLP 약어가 처음 등장할 때 풀리지 않음 `[~]`

- 심각도: 낮음
- Section: Method, Problem Formulation과 Nonlinear Estimator
- 위치: `paper/user_v6.tex:83`, `paper/user_v6.tex:113`

`MLP`는 line 83에서 처음 등장하지만 transcript 안에서 multilayer perceptron으로 풀리지 않는다. Abstract와 Introduction은 `shared nonlinear estimator`만 사용한다.

line 83에서는 `shared nonlinear estimator`를 유지하고, line 113에서 처음 정의하는 구성이 가장 자연스럽다.

권장:

> RelCompat3D-MLP uses one shared multilayer perceptron (MLP) with a single two-unit ReLU hidden layer.

### V6-4. Method subsection 이름이 정의된 용어와 다름 `[~]`

- 심각도: 낮음
- Section: Method
- 위치: `paper/user_v6.tex:95`

현재 제목:

> Relation-Consistent Compatibility

본문에서 정의하는 용어는 `predicate--geometry compatibility`와 `transformation-consistent compatibility`다. `relation-consistent compatibility`는 이 subsection 제목에서만 사용되어 세 번째 유사 용어가 된다.

권장 제목:

```tex
\subsection{Compatibility Estimation and Transformation Averaging}
```

이 제목은 Linear와 MLP estimator, transformation definition, averaging equation을 모두 직접 설명한다.

### V6-5. `corresponding results`의 지시 대상이 모호함 `[~]`

- 심각도: 낮음
- Section: Experiments, Metrics
- 위치: `paper/user_v6.tex:190`

원문:

> The released artifacts provide the corresponding results for all five \(K\) values.

바로 앞에는 per-family metrics와 family composition이 나오고, 그 앞에는 uncertainty와 coverage가 나온다. `corresponding results`가 어느 결과를 뜻하는지 한 번에 알기 어렵다.

의도가 uncertainty, coverage, decidable-only Violation, family metrics를 묶는 것이라면 다음이 더 명확하다.

> The released artifacts provide these additional metrics for all five \(K\) values.

### V6-6. 최종 source에 obsolete 주석과 inline heading이 남음 `[~]`

- 심각도: 낮음
- Section: Related Work와 Method
- 위치:
  - `paper/user_v6.tex:44--45`
  - `paper/user_v6.tex:99`
  - `paper/user_v6.tex:127--135`

삭제 권장:

1. 압축 전 open-vocabulary 문장 두 줄
2. symbolic loss로 대체된 이전 fixed-number loss equation

line 99의 `\subsubsection{Linear Estimator}`는 앞 문장과 같은 source line에 있다. 별도 줄과 빈 줄로 분리하면 source 구조와 diff 검토가 쉬워진다. 출력 의미는 바뀌지 않는다.

## 기존 86번 source-score range `[x]`

평가에 사용한 proximity와 vertical-order candidates의 source relation score는 모두 음수가 아니다.

| Predictor | 관찰 범위 | Candidates | Negative | Exact zero |
|---|---:|---:|---:|---:|
| VL-SAT | \([5.30\times10^{-22},\,0.9954]\) | 110,424 | 0 | 0 |
| Open3DSG | \([0.6394,\,0.9281]\) | 79,722 | 0 | 0 |
| SGFN | \([4.61\times10^{-20},\,0.5846]\) | 110,424 | 0 | 0 |

Open3DSG의 전체 candidate 범위도 \([0.5772,\,0.9707]\)이며 음수가 없다. 따라서 현재 product utility에서 음수 score가 순서를 뒤집는 문제는 없다.

이 결과는 `paper/aaai/sec/supplement.tex`의 source-score range 표에 존재한다. Main은 predictor별 score 종류와 predictor 사이에서 score를 비교하지 않는다는 점을 이미 설명한다. 페이지가 제한된 main에 범위 수치를 다시 넣을 필요는 없다.

## 기존 89번 direct component removal `[x]`

동일한 frozen rows와 family-aware route에서 다음 실험이 supplement에 존재한다.

- linked pairwise loss 제거
- transformation averaging 제거
- transformation identity check
- matched Linear와 MLP controls

해석도 현재 main claim과 맞는다.

1. Pairwise loss는 training regularizer다. 제거 시 aggregate metric 변화는 작다.
2. Transformation averaging은 aggregate gain의 유일한 원인이 아니다.
3. Transformation averaging 제거 시 exact endpoint and predicate consistency가 깨진다.
4. 따라서 transformation averaging의 핵심 역할은 exact implementation guarantee다.

Main pointer는 `paper/user_v6.tex:314`에 있다.

> The supplement reports feature-removal analyses, direct component removals, transformation checks, and matched controls for both estimators.

Main에 removal 수치를 추가할 필요는 없다.

## AAAI-27 submission 규정 점검

검토 근거:

- [AAAI-27 Main Technical Track Call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/)
- [AAAI-27 Submission Instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/)
- [AAAI-27 Supplementary Material](https://aaai.org/conference/aaai/aaai-27/supplementary-material/)
- [AAAI Publication Policies and Guidelines](https://aaai.org/aaai-publications/aaai-publication-policies-guidelines/)
- local official Author Kit: `paper/aaai/official/AnonymousSubmission2027.tex`

### AAAI-1. `trim`과 `clip` 사용 `[차단]`

- 심각도: 치명적 형식 위반
- 위치:
  - Figure 1: `paper/user_v6.tex:11--15`
  - Figure 2: `paper/user_v6.tex:61--65`
  - Figure 3: `paper/user_v6.tex:236--240`

AAAI-27 Author Kit은 figure를 LaTeX 밖에서 crop하도록 요구하며 `trim`과 `clip` option을 명시적으로 금지한다.

필수 조치:

1. 세 PDF의 media box를 최종 보이는 범위로 외부에서 고정한다.
2. `\includegraphics`에는 `width`와 file path만 남긴다.

권장 형태:

```tex
\includegraphics[width=\columnwidth]{AuthorKit27/Figures/Figure1.pdf}
```

```tex
\includegraphics[width=\textwidth]{AuthorKit27/Figures/Figure2.pdf}
```

```tex
\includegraphics[width=\textwidth]{AuthorKit27/Figures/Figure3.pdf}
```

### AAAI-2. bold caption lead-in `[차단]`

- 심각도: 높은 형식 위반
- 위치:
  - Figure 1: `paper/user_v6.tex:16`
  - Figure 2: `paper/user_v6.tex:66`
  - Table 1: `paper/user_v6.tex:230`
  - Table 2: `paper/user_v6.tex:282`

AAAI-27은 figure와 table caption을 10 pt roman으로 요구하고 caption을 bold 또는 italic으로 만들지 말라고 명시한다.

현재의 `\textbf{RelCompat3D.}`, `\textbf{RelCompat3D overview.}`, `\textbf{Shared 3DSSG validation results.}`, `\textbf{Ablations and counterfactual controls.}`를 일반 roman text로 바꿔야 한다.

Caption 내용은 충분하다. 정보 추가가 아니라 bold command만 제거하면 된다.

### AAAI-3. 현재 fresh teaser build가 페이지 제한을 위반함 `[차단]`

- 심각도: 치명적
- 대상: `paper/aaai/main_teaser.pdf`

AAAI-27 main paper는 최대 9페이지이고 page 8과 page 9는 references만 허용된다.

확인 결과:

- `main_teaser.pdf`는 10페이지다.
- technical Table 2가 page 8에 남아 있다.
- references가 page 10까지 이어진다.
- 따라서 현재 fresh teaser build는 제출할 수 없다.

`main_teaser_aaai27.pdf`는 9페이지이고 page 8과 page 9가 references다. 그러나 생성 시각이 2026-07-21이며 `user_v6.tex`과 현재 선택 제목보다 이전 상태다. 이 파일을 최신 원고의 규정 통과 근거로 사용하면 안 된다.

필수 조치:

1. `user_v6.tex`의 확정 내용을 active `paper/aaai/sec/` source와 동기화한다.
2. 선택 제목을 main, supplement, OpenReview metadata에 동일하게 반영한다.
3. teaser version을 다시 빌드한다.
4. page 1--7에 모든 technical content가 끝나는지 확인한다.
5. page 8--9에 references만 있는지 확인한다.

### AAAI-4. 4.4306 pt overfull이 남음 `[차단]`

- 심각도: 높은 형식 위반
- 근거: `paper/aaai/main.log`
- 위치: active source의 main result table에 대응하는 log lines 199--235

AAAI-27 Author Kit은 margin이나 gutter intrusion을 허용하지 않으며 overfull box를 모두 고치도록 요구한다.

현재 log:

> Overfull \hbox (4.4306pt too wide)

Table 1은 이미 two-column table이므로 다음 순서로 해결하는 것이 안전하다.

1. column heading 또는 `Product (all families)` label을 짧게 한다.
2. decimal precision을 필요한 수준으로 유지한다.
3. `\tabcolsep`를 소폭 줄인다.

`\setlength{\tabcolsep}{...}`는 Author Kit이 명시적으로 허용한 예외다. `\resizebox`, `\scalebox`, 전체 font 축소는 사용하지 않는다.

### AAAI-5. 생성형 AI 사용 역할이 manuscript에 기록되지 않음 `[차단]`

- 심각도: 정책 준수
- 위치: Conclusion 뒤, References 앞의 7-page content 안

AAAI는 manuscript 준비에 생성형 AI 사용을 허용하지만 역할을 manuscript에 기록하도록 요구한다. 현재 main과 supplement에서 해당 disclosure를 찾지 못했다.

익명성을 해치지 않는 최소 문장:

```tex
\paragraph{Use of AI systems.}
AI-assisted tools were used for language editing and manuscript organization.
The authors verified all scientific claims, experiments, figures, and references.
```

실제 사용 범위가 더 넓다면 사실에 맞게 조정해야 한다. AI system을 저자나 citation source로 표기하면 안 된다.

### AAAI-6. title casing과 release 간 제목 불일치 `[~]`

- 심각도: 중간
- 위치:
  - `paper/aaai/main.tex:21`
  - `paper/aaai/supplement.tex:19`
  - OpenReview title field

선택한 제목은 현재 supplement와 가깝지만 active main은 이전 제목을 사용한다. 또한 AAAI Author Kit은 Chicago Title Case를 요구하고 hyphenated term의 양쪽 핵심 단어를 대문자로 쓰도록 안내한다.

최종 권장:

> RelCompat3D: Predicate–Geometry Compatibility for Re-Ranking 3D Scene Graph Relations

본문의 일반 동사나 명사로 쓰는 `re-ranking`은 소문자를 유지해도 된다. 제목에서만 `Re-Ranking`으로 맞춘다.

### AAAI-7. reproducibility checklist의 theoretical contribution 응답 재판단 `[~]`

- 심각도: 중간
- 위치: `paper/aaai/reproducibility_checklist.tex:112--139`

Checklist는 별도 파일로 존재하며 실제 질문에 빈 placeholder는 없다. 이는 규정을 충족한다.

다만 현재 다음 질문에 `yes`로 답한다.

> Does this paper make theoretical contributions?

Paper framing은 group averaging의 standard invariance와 family-sequence preservation을 novelty theorem이 아니라 implementation guarantee로 다룬다. AGENTS.md의 claim boundary도 이를 theoretical novelty로 강조하지 않도록 한다.

별도의 이론 기여를 주장하지 않는다면 답을 `no`로 바꾸는 편이 manuscript framing과 일치한다. 그러면 하위 theorem 관련 응답도 적용 대상이 아니다. 이 변경은 main claim을 약화하지 않고 오히려 과장된 novelty 인상을 줄인다.

Checklist는 main PDF에 붙이지 않고 OpenReview의 지정 field에 별도로 제출해야 한다.

## AAAI-27 규정 충족 항목

| 항목 | 상태 | 확인 결과 |
|---|---|---|
| US Letter | `[x]` | 기존 main PDF가 612 × 792 pt |
| submission style | `[x]` | `\usepackage[submission]{aaai2027}` 사용 |
| 익명화 | `[x]` | active main과 supplement가 Anonymous Submission이며 author identity와 affiliation이 없음 |
| acknowledgments 제거 | `[x]` | review manuscript에서 발견되지 않음 |
| Abstract citation 금지 | `[x]` | Abstract에 citation 없음 |
| Type 1 또는 TrueType font | `[x]` | 기존 canonical PDF는 embedded Type 1 font만 포함하며 Type 3 없음 |
| Figure 해상도 | `[x]` | canonical Figure 3 raster가 약 350 ppi, Figure 1과 Figure 2는 vector 중심 |
| Figure label과 stroke | `[x]` | current generated asset specification은 final placement 기준 9 pt 이상과 0.5 pt 이상을 목표로 생성됨 |
| color-only 구분 회피 | `[x]` | Figure 3은 line style과 marker shape를 함께 사용 |
| Figure와 Table caption 위치 | `[x]` | 모두 artifact 아래에 위치 |
| Table font | `[x]` | `\small`은 9 pt table 허용 범위 |
| `\tabcolsep` 조정 | `[x]` | Author Kit이 허용한 exception |
| Figure와 Table 본문 참조 | `[x]` | Figure 1--3과 Table 1--3 모두 최소 한 번 참조됨 |
| web supplement pointer 금지 | `[x]` | main과 supplement에서 외부 supplement URL을 찾지 못함 |
| supplement 익명화 | `[x]` | author identity와 외부 repository pointer 없음 |
| separate checklist | `[x]` | 별도 checklist PDF와 source 존재 |
| review-stage source 제출 | `[x]` | review 시 main은 PDF만 요구됨. single-source archive는 acceptance 이후 문제 |

Figure label 크기, stroke, contrast는 최종 rebuilt PDF에서도 다시 측정해야 한다. 현재 통과 판단은 기존 canonical PDF와 generated asset을 기준으로 한다.

## F4--F20 처리 여부

| 항목 | 상태 | `user_v6.tex` 기준 판단 |
|---|---|---|
| F4 Figure와 Table 본문 참조 | `[x]` | Figure 1--3과 Table 1--3이 모두 본문에서 호출됨 |
| F5 caption 명확성 | `[~]` | 내용은 자기완결적이다. AAAI-2의 bold formatting만 고쳐야 함 |
| F6 section별 첫 약어의 citation 존재 | `[x]` | Introduction, Related Work, Method, Experiments, Discussion, Conclusion에서 확인됨 |
| F7 영어 소유격 형태 자제 | `[x]` | prose에서 해당 형태를 발견하지 않음 |
| F9 용어 통일 | `[~]` | source relation score, ordered pair, exact-match Recall, verifier-derived Violation은 통일됨. V6-1과 V6-4가 남음 |
| F11 em dash와 prose semicolon 자제 | `[x]` | em dash 없음. semicolon은 feature vector의 수학 구분자에만 사용 |
| F12 긴 문장 | `[x]` | 분할이 반드시 필요한 과도한 prose sentence를 발견하지 않음 |
| F14 수식 숫자 일반화 | `[x]` | loss equation은 symbolic hyperparameter를 사용하고 실제 값은 뒤에서 설정 |
| F15 hyperparameter 근거 | `[x]` | train/development 분리와 supplement sensitivity가 존재 |
| F16 수식과 기호 점검 | `[~]` | equation 전개는 자연스럽다. V6-1 notation만 수정 필요 |
| F17 contribution bullet 간결성 | `[x]` | 세 bullet이 problem, method, evaluation role을 각각 한 문장으로 전달 |
| F18 story 일관성 | `[x]` | failure, pair identity, score separation, transformations, re-ranking, audit가 Method와 Experiments에 연결 |
| F19 Introduction과 Related Work 중복 | `[x]` | gap 설명과 fixed-predictor 대비가 역할별로 분리됨 |
| F20 Introduction과 Related Work 압축 | `[x]` | transcript는 충분히 압축됨. 실제 페이지 제한 문제는 AAAI-3에서 별도 처리 |

## Section별 검토

### Abstract `[x]`

- 문제, 방법, 결과, alternative audit가 모두 포함된다.
- Introduction의 contribution 세 개와 대응한다.
- citation이나 정의되지 않은 수학 기호가 없다.
- `point estimates`와 `reported predictor--K settings`가 statistical scope를 제한한다.
- support/contact boundary는 한 번만 설명되며 과도하지 않다.

### Introduction `[x]`

- 문제 정의, 기존 score의 한계, method design, evaluation, contribution 순서가 자연스럽다.
- counterfactual과 transformation의 역할을 구분해 처음 읽는 독자의 혼동을 줄였다.
- contribution bullet은 간결하다.
- Introduction에서 강조한 claim은 Method와 Experiments에 근거가 있다.

### Related Work `[x]`

- 세 subsection의 제목과 내용이 정합하다.
- 각 연구군 뒤에 RelCompat3D와의 차이가 설명된다.
- 3D scene graph generation, geometry-aware evidence, calibration의 역할이 겹치지 않는다.
- 단순 논문 나열로 끝나는 paragraph가 없다.
- obsolete 주석은 V6-6에 따라 삭제하면 된다.

### Method `[~]`

- ordered-pair identity, score separation, compatibility estimators, transformation averaging, family-aware re-ranking 순서가 논리적이다.
- source relation score \(Z\)는 compatibility estimator에서 제외되고 re-ranking에서만 사용된다.
- Linear와 MLP의 입력 차이가 사실대로 설명된다.
- V6-1 notation, V6-3 acronym, V6-4 subsection title을 수정해야 한다.
- Figure 2 caption은 compatibility 입력과 score 결합 시점을 정확히 설명한다.

### Experiments `[~]`

- 세 predictor는 같은 target, candidate scope, metric에서 비교된다.
- Table 1과 Figure 3은 overall Recall--Violation behavior를 검증한다.
- Table 2는 pair identity, predicate, geometry, source score 역할을 검증한다.
- Table 3은 OBB input과 다른 point- and mesh-based measurements로 방향을 재검토한다.
- 모든 \(K\) 값과 main table 수치는 서로 일치한다.
- V6-2의 `largest` 해석을 수정해야 한다.
- V6-5의 artifact 문장을 명확히 하면 auxiliary results의 위치가 더 친절해진다.

### Discussion and Limitations `[x]`

- cross-predictor evidence와 dataset-level generalization을 구분한다.
- known instances와 support/contact boundary가 현재 method scope와 맞는다.
- point- and mesh-based audit를 independent ground truth로 부르지 않는다.
- 새로운 수치나 근거 없는 failure claim이 없다.
- 별도 Broader Impact 또는 Ethics section이 필수인 human-subject intervention은 발견되지 않았다.

### Conclusion `[x]`

- Introduction의 motivating problem으로 돌아간다.
- Method와 Experiments에 없는 새 claim을 추가하지 않는다.
- `lower or tied`와 `preserving or improving`이 실제 point estimates와 일치한다.
- SOTA, broad generalization, physical ground truth claim이 없다.

## Introduction claim과 evidence 연결

| Introduction의 claim 또는 design | Method 대응 | Experiment 대응 | 판단 |
|---|---|---|---|
| high score와 ordered-pair geometry의 불일치 | compatibility formulation | Figure 1, Table 1, Figure 3 | 충분 |
| source relation score와 compatibility 분리 | \(C_i^q\)에서 \(Z_i\) 제외 | Compatibility only, RankAvg, RRF | 충분 |
| ordered-pair identity 보존 | pair identity와 relation identity 정의 | Wrong pair, Shuffled geometry | 충분 |
| relation-preserving transformations | transformation orbit와 averaging | Fixed-predicate swap, exact checks, direct removal | 충분 |
| family-aware re-ranking | \(u_i^q\)와 family subsequence | Table 1, Product (all families), family metrics | 충분 |
| alternative geometric measurement | point- and mesh-based audit | Table 3와 supplement all-\(K\) audit | 충분 |

Introduction에서 강조하지만 실험 근거가 없는 main claim은 발견되지 않았다. Introduction에서 전혀 예고되지 않은 핵심 experiment도 없다.

## Figure와 Table 점검

| Artifact | 본문 참조 | 내용과 caption 판단 | 형식 판단 |
|---|---|---|---|
| Figure 1 | Introduction line 21 | failure case, source, ordered pair, Linear rank change를 설명 | trim과 clip 제거, bold lead-in 제거 필요 |
| Figure 2 | Method line 75 | pair geometry, compatibility input, source score 결합 시점, Linear outcome을 설명 | trim과 clip 제거, bold lead-in 제거 필요 |
| Figure 3 | Results line 288 | metric 방향, 다섯 \(K\), 세 predictor, axis 차이를 설명 | trim과 clip 제거 필요 |
| Table 1 | Results line 288 | target, metrics, Source, ranking rules를 설명 | bold lead-in 제거, overfull 해결 필요 |
| Table 2 | Ablations line 311 | Linear controls와 MLP full rows의 역할을 설명 | bold lead-in 제거 필요 |
| Table 3 | Audit line 319 | alternative labels, delta, measured and decidable coverage를 설명 | 내용상 충분 |

Figure 3와 Table 2 caption에 shared-target 문장을 반복해서 넣을 필요는 없다. Experimental Setup과 Table 1이 공통 평가 범위를 정의하며 두 artifact는 같은 Results 흐름에서 해석된다.

## 제출 전 우선순위

### P0: submission blocker

1. `user_v6.tex`의 확정 내용을 active AAAI source에 동기화한다.
2. main, supplement, OpenReview의 제목을 `Re-Ranking` 표기까지 동일하게 맞춘다.
3. 생성형 AI 사용 역할을 7-page content 안에 기록한다.
4. Figure 1--3의 crop을 asset에 반영하고 모든 `trim`과 `clip`을 제거한다.
5. Figure 1, Figure 2, Table 1, Table 2 caption의 manual bold를 제거한다.
6. Table 1의 4.4306 pt overfull을 해결한다.
7. teaser PDF를 다시 빌드해 technical content를 page 7 안에 끝낸다.
8. page 8과 page 9에 references만 남는지 확인한다.

### P1: transcript correctness

1. V6-1의 `\Delta z_i^{\rm norm}` 표기를 통일한다.
2. V6-2의 `largest Violation increases`를 수치에 맞게 낮춘다.

### P2: readability와 source hygiene

1. V6-3에서 MLP를 처음 풀어 쓴다.
2. V6-4의 subsection 제목을 정의된 용어에 맞춘다.
3. V6-5의 `corresponding results`를 구체화한다.
4. V6-6의 obsolete comments와 inline heading을 정리한다.
5. Reproducibility checklist의 theoretical contribution 응답을 main framing과 맞춘다.

### 최종 release 검증

1. `pdfinfo`로 9 pages와 US Letter를 확인한다.
2. page 8--9가 references only인지 page별 text extraction으로 확인한다.
3. `pdffonts`로 embedded Type 1 또는 TrueType만 있는지 확인한다.
4. build log에서 overfull, undefined reference, undefined citation이 없는지 확인한다.
5. Figure labels 9 pt 이상, stroke 0.5 pt 이상, raster 300 ppi 이상을 최종 placement 기준으로 확인한다.
6. grayscale과 color-blind 조건에서도 Figure 1--3을 읽을 수 있는지 확인한다.
7. author identity, affiliation, acknowledgments, repository URL이 main과 supplement에 없는지 확인한다.
8. reproducibility checklist를 main과 별도 field에 업로드한다.

AAAI-27 공식 일정은 full paper가 2026-07-28, supplementary material과 code가 2026-07-31 마감이다. 두 마감 모두 Anywhere on Earth 기준이다.
