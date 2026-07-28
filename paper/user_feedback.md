# RelCompat3D 최종 제출본 통합 재검토

- 검토일: 2026-07-28 KST
- 검토 대상:
  - `paper/aaai/sec/0_abstract.tex`
  - `paper/aaai/sec/1_introduction.tex`
  - `paper/aaai/sec/2_related_work.tex`
  - `paper/aaai/sec/3_method.tex`
  - `paper/aaai/sec/4_experiments.tex`
  - `paper/aaai/sec/5_discussion_limitations.tex`
  - `paper/aaai/sec/6_conclusion.tex`
  - `paper/aaai/sec/supplement.tex`
  - `paper/aaai/reproducibility_checklist.tex`
- 검토 범위: 기존 이슈, section별 역할과 문체, section 간 정합성,
  Introduction claim--evidence 연결, main--supplement 정합성, Figure/Table,
  수치와 notation, Author Kit, BibTeX, 제출 artifact, citation 원문 검증
- F-01--F-10, I-021--I-022, citation 정리와 최종 artifact 동기화는 완료됐다.
  공식 제출 경로는 `paper/aaai/main.tex`이다. 최신 source에서 canonical PDFs와
  release를 다시 생성했고 clean-build 및 manifest 검증을 통과했다.
- 2026-07-28 citation audit에서는 current main의 43개 고유 citation key를 공식
  proceedings, publisher, arXiv 원문과 대조했다. Google Scholar는 안정적인
  공식 BibTeX API가 없고 사용자가 제공한 `scholar.googleusercontent.com`
  URL도 세션 서명 때문에 외부 세션에서 HTTP 403을 반환했다. 사용자가 확인한
  Scholar BibTeX 내용은 반영하되, 충돌할 때는 versioned arXiv와 공식
  proceedings/publisher metadata를 판정 기준으로 사용했다.

상태 표시는 다음과 같다.

- `[x]`: 해결 완료 또는 현재 표현으로 충분
- `[~]`: claim을 훼손하지 않지만 제출 전 수정 권장
- `[ ]`: 제출 전에 수정해야 함
- `[선택]`: 규정 위반이나 factual error는 아니며 품질 향상을 위한 선택 사항
- `[보류]`: 사용자가 현 상태를 유지하기로 결정한 layout 항목
- `[저자 확인]`: 정책, 라이선스, 또는 저자 행위에 관한 확인 필요
- `[범위 한계]`: 오류는 아니지만 reviewer risk로 남는 연구 범위

## 1. 최종 판단

현재 main paper의 problem--method--experiment story와 핵심 수치는 정합하다.
세 contribution은 Method의 설계와 Experiment의 evidence에 대응하며, main의
M-1--M-3 문장도 supplement의 고정 protocol 결과와 일치한다. Main은 broad SOTA,
dataset-level generalization, independent physical validity를 주장하지 않는다.
Figure 2 반영본은 실제 outlined asset, caption, Method/Results 참조,
clean-build 번호가 모두 정상이다. Asset은 predicate semantics와 ordered-pair
measurements만 compatibility estimator에 입력되고 source relation score는
within-family score에서 합쳐지는 흐름을 보여준다. Caption과 Results의
Open3DSG proximity 사례도 \(4.33\,\mathrm{m}\), rank \(19\rightarrow178\),
RelCompat3D-Linear로 일치한다.

Citation source 정리는 완료됐다. Current main과 supplement에서 사용하는 43개
citation key는 모두 bibliography에 존재한다.
VIZOR는 `Madhavaram_2026_WACV`, Ovadia는 `Ovadia2019CanYT`로 통일했고,
TAD는 실제 참고한 arXiv v1 URL을 명시했다. Heo는 Google Scholar와 author
repository BibTeX를 기준으로 2026을 유지한다는 저자 결정을 반영했다.
RelWitness는 Related Work에서 proposal 범위로만 기술한다.
Scientific residual risk는 independent validity label 부재와 single-target
범위다. 이는 숨겨진 transcript 오류가 아니라 현재 claim boundary다.

현재 source에서 남은 과학적 내용 수정은 없다. Section~16의 L-01, L-03--L-09
교정도 반영됐다. L-02는 rank를 바깥으로 이동시킨다는 의미를 살리기 위해
`moves it to 425`를 유지한다. 제출 전에는 F-06의 generative-AI role
documentation과 submission-system author metadata 확인만 남는다. F-07은 source terms가
파생 row 재배포를 명시적으로 허용하지 않는다는 보수적 해석에 따라 stable source
identifiers와 source-derived row bundles를 release에서 제외해 닫았다.

## 2. 통합 이슈 판정

이 절은 기존 이슈 재검토, I-015--I-022 엄격 재판정, Author Kit, BibTeX를
하나로 통합한다. 완료된 항목은 핵심 결론만 남긴다.

### 2.1 최종 source와 artifact 이슈

| 이슈 | 상태 | 최종 결론 |
|---|---|---|
| F-01 Supplement optimizer | `[x]` | Linear는 800-step full-batch gradient descent, MLP는 120-step full-batch Adam으로 active code/protocol과 일치시켰고 obsolete L-BFGS/500-epoch 문장을 삭제함 |
| F-02 score-mapping notation | `[x]` | mapping을 \(g_\gamma,g_\tau\)로 바꾸어 estimator \(q\)와 predicate semantics \(T_i\)의 collision을 제거함 |
| F-03 Supplement Table 호출 | `[x]` | 기존 여섯 Table을 포함해 모든 main/supplement Figure와 Table이 본문에서 최소 한 번 참조됨 |
| F-04 Open3DSG BibTeX title | `[x]` | `queryable objects and open-set relationships`로 수정했고 BibTeX warning 0개를 확인함 |
| F-05 canonical/release synchronization | `[x]` | 최종 교정을 포함한 main, supplement, checklist를 clean build하고 canonical PDFs와 `20260728_214915` release를 재생성함. Outer/inner manifests, ZIP integrity, extracted-source rebuild와 PDF text equivalence가 모두 통과함 |
| F-09 caption typography | `[x]` | Main과 supplement의 manual-bold caption을 모두 제거했고 Author Kit의 roman caption typography를 사용함 |
| F-10 supplement table font | `[x]` | Paired-interval cell의 `\scriptsize`를 제거해 surrounding `\small` 9-point table text로 통일했고 10-page build를 유지함 |

Current source clean test build:

| 산출물 | 쪽수 | clean-build 판정 |
|---|---:|---|
| Main | 9 | Figure 1--3과 Table 1--3은 pages 1--7, pages 8--9는 references only |
| Supplement | 10 | Undefined reference와 overfull warning 없음 |
| Reproducibility checklist | 2 | 정상 빌드 |

세 output은 US Letter와 PDF 1.5이며 Type 3, CID/Identity, unembedded font가
없다. Undefined citation/reference, `.blg` warning, graphics inclusion warning,
overfull box도 0이다.

#### F-06. Generative-AI role disclosure `[저자 확인]`

AAAI-27 [Main Technical Track Call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/)
은 generative AI 사용을 허용하지만 저자가 내용에 책임을 진다고 명시한다. 더
구체적으로 [AAAI Publication Policies](https://aaai.org/aaai-publications/aaai-publication-policies-guidelines/)
는 AAAI-affiliated publication 개발에 사용된 AI system의 역할을 manuscript에
properly documented 해야 한다고 명시한다.
이 프로젝트에서는 AI-assisted writing, review, code organization이 광범위했으므로
`해당 없음`으로 처리하기 어렵다.

권장 처리:

- 제출 시스템의 field만으로 충분하다고 가정하지 않는다. Publication policy의
  문면은 manuscript documentation을 요구한다.
- 실제 사용 범위를 저자가 확인한 뒤 anonymity를 깨지 않는 짧은 statement를
  manuscript에 넣는다. 권장 초안은
  `Generative AI tools assisted with language editing, code organization,
  and internal review. The authors verified the manuscript, citations,
  implementation, and reported results and remain responsible for all content.`
- 역할 범위나 위치가 불명확하면 AAAI workflow chair에게 확인한다.

이 항목은 기술 내용 수정이 아니라 저자와 venue policy의 최종 확인 사항이다.

#### F-07. Derived-row 재배포 권한 `[x, 보수적 처리]`

3RScan [project page](https://waldjohannau.github.io/RIO/)와 현재 access form의
terms는 research use와 access sharing conditions를 제시하지만 source-derived
row나 stable scan/object identifier의 재배포를 명시적으로 허용하지 않는다.
따라서 “raw scans만 제외하고 stable IDs가 있는 derived rows는 배포한다”는 방식은
관행상 볼 수 있어도 가장 보수적인 선택은 아니다.

Current release는 licensed scans, meshes, RGB-D data, third-party checkpoints,
stable source identifiers, source-derived row bundles를 제외한다. 대신 code,
schema, aggregate outputs, expected manifests, licensed inputs에서 실행하는
deterministic exporters를 제공한다. Release builder에는 stable UUID가 남으면
실패하는 gate도 추가했다.

#### F-08. First-page vertical overfull `[x]`

사용자가 조정한 float 위치를 반영한 `main.tex` clean build에서 first-page
vertical overfull이 사라졌다. Figure 1은 page 1에 남아 있고 margin, caption,
figure/table font를 줄이지 않았다. Final main log의 overfull box는 0이다.

### 2.2 기존 I-001--I-022 재판정

| 이슈 | 상태 | 최종 결론 |
|---|---|---|
| I-001--I-003 | `[x/제외]` | 기존 문법·metric 이슈는 해결됐고, 사용자가 제외한 추가 limitation 제안은 다시 열지 않음 |
| I-004 | `[x]` | normalized height를 \(\Delta z_i^{\rm norm}\)으로 통일함 |
| I-005 | `[x]` | Violation 해석을 Table 2 수치에 맞게 낮춰 씀 |
| I-006 | `[x]` | MLP는 Method에서 `multilayer perceptron (MLP)`으로 처음 풀어 씀 |
| I-007--I-008 | `[x]` | subsection 명칭과 모호한 pointer를 구체화함 |
| I-009--I-010 | `[x]` | obsolete comment version을 제거하고 demotion/promotion 사례를 main/supplement에 연결함 |
| I-011 | `[x]` | Table 3 caption이 \(K\), label rule, \(\Delta V\), M/D와 단위를 설명함 |
| I-012 | `[x]` | support/contact의 identity transformation과 all-family comparison 범위를 명시함 |
| I-013 / I-015 | `[x]` | evaluated source score가 nonnegative이며 predictor별 range와 sign 해석을 supplement에 보고함 |
| I-014 | `[x]` | pairwise-loss와 transformation-averaging removal을 두 estimator에 대해 보고함 |
| I-016 | `[x]` | point/mesh agreement, uncertainty, measured/decidable coverage가 결정됨 |
| I-017 | `[x]` | ordered-pair identity, measurements, alternative audit terminology가 일치함 |
| I-018 | `[x]` | Related Work가 Recall@\(K\)를 exact-match retrieval at a rank cutoff로 설명함 |
| I-019 | `[x]` | Main interval claim과 supplement의 paired interval이 일치함 |
| I-020 | `[x]` | relation phrase의 quotation/`\texttt` 선택은 현재 plain quotation으로 충분함 |
| I-021 | `[x]` | `Evaluation-split ground-truth relations`로 범위를 한정해 Method의 training positives와 충돌하지 않음 |
| I-022 | `[x]` | 66,454 rows를 constructed training+internal-development 합계로 명시하고 뒤의 60,208 fitting rows와 구분함 |

### 2.3 Author Kit, BibTeX, artifact 항목

| 항목 | 상태 | 최종 결론 |
|---|---|---|
| Technical-content page limit | `[x]` | main은 9 pages이며 technical content와 모든 main Figure/Table은 pages 1--7에 있음 |
| References | `[x]` | references는 page 7에서 시작하고 pages 8--9에는 references만 존재함 |
| US Letter / PDF version | `[x]` | current outputs는 US Letter, PDF 1.5 |
| Fonts | `[x]` | Type 3와 CID/Identity fonts가 없고 outlined-v15 Figure inclusion warning도 없음 |
| Figure crop | `[x]` | external outlined figures를 사용하며 `trim`/`clip` 문제 없음 |
| Caption manual bold | `[x]` | Main과 supplement caption의 수동 `\textbf`를 모두 제거함 |
| Table text size | `[x]` | Supplement paired-interval cells가 surrounding `\small` 9-point text를 상속함 |
| Table 2 horizontal overflow | `[x]` | 이전 4.4306 pt warning이 current log에서 사라짐 |
| Undefined citation/reference | `[x]` | 43개 current citation key의 정적 대조와 clean build에서 undefined citation/reference 0을 확인함 |
| BibTeX volume/number warning | `[x]` | `fei2026open`, `liu2026view`, `ma2026edge`를 `@inproceedings`와 volume-only로 정리함 |
| BibTeX warning count | `[x]` | Current source의 clean main build에서 `.blg` warning 0을 확인함 |
| Anonymous main/supplement | `[x]` | author, affiliation, email, acknowledgment, author-owned URL이 없음 |
| Own-material web link ban | `[x]` | main과 supplement에 저자 소유 자료 링크가 없음 |
| Reproducibility checklist | `[x]` | 별도 2-page PDF가 생성됨 |
| Reference title casing | `[선택]` | AAAI 제출 규정 위반은 아님. 다만 `.bbl`에서 method name과 acronym이 변형되지 않도록 `{3D}`, `{OpenScene}`, `{VL-SAT}` 등을 brace로 보존하면 reference 품질이 좋아짐 |
| Forbidden layout/package manipulation | `[x]` | margin 변경, geometry package, font 축소용 비표준 명령이 없음 |
| Ethics violation statement | `[x]` | 저자 확인 결과 해당 없음 |
| Simultaneous submission | `[x]` | 저자 확인 결과 해당 없음 |
| Self-citation anonymity | `[x]` | 저자 확인 결과 해당 없음 |
| Submission count/reviewer pool | `[x]` | 저자 확인 결과 위반 없음 |
| First-page overfull | `[x]` | Current `main.tex` clean log에서 overfull box 0을 확인함 |
| Canonical/release synchronization | `[x]` | Current 9/10/2-page canonical PDFs와 `20260728_214915` release가 최종 source와 동기화됨 |

## 3. 전체 문체와 source 체크리스트

| 기준 | 상태 | 판단 |
|---|---|---|
| 용어 통일 | `[x]` | Main과 supplement의 core terms 및 score-mapping notation이 일치함 |
| Easy to read | `[x]` | 문제, estimator, transformation, ranking, evaluation 순서가 명확함 |
| Straightforward | `[x]` | 각 section이 고유 역할을 가지며 main story가 우회하지 않음 |
| 독자 친절성 | `[x]` | \(T,G,Z\), relation family, metrics, Source가 최초 사용 근처에서 설명됨 |
| Good English | `[x]` | L-01, L-03--L-09의 collocation, parallel structure, terminology, source-spacing 교정을 반영함. L-02는 저자 의도에 따라 유지했고 L-10은 의미 오류가 없는 선택적 표현 개선으로만 남김 |
| 같은 의미의 용어 혼용 | `[x]` | `source relation score`, `ordered pair`, `family-aware re-ranking`, `verifier-derived Violation`이 일관됨 |
| `A's B` 자제 | `[x]` | active prose에 해당 소유격 패턴이 없음 |
| em dash 남용 | `[x]` | prose에 em dash가 없음 |
| semicolon 남용 | `[x]` | prose에는 없고 feature-vector 수식 구분에만 사용함 |
| 긴 문장 | `[x]` | 즉시 분할해야 할 정도로 서로 다른 논거가 한 문장에 몰리지 않음 |
| Figure/Table 본문 참조 | `[x]` | 모든 main/supplement Figure와 Table이 본문에서 최소 한 번 참조됨 |
| Figure/Table caption | `[x]` | 모든 caption이 자기완결적이며 수동 bold 없이 Author Kit typography를 따름 |
| section별 첫 약어 citation | `[x]` | Introduction, Method, Experiments에서 predictor 이름과 citation을 one-to-one으로 연결함 |
| 수식의 일반화 | `[x]` | loss hyperparameter를 변수로 쓰고 실제 값을 prose/supplement에 둠 |
| hyperparameter 근거 | `[x]` | active optimizer와 step/lr 설명이 code, protocol, supplement에서 일치하고 sensitivity를 보고함 |
| equation/notation 순서 | `[x]` | Main과 supplement의 \(T,G,Z,q,C,u,g_\gamma,g_\tau\)가 충돌 없이 정의됨 |
| Contribution bullet 간결성 | `[x]` | 세 항목 모두 한 문장이고 task, estimator, ranking으로 분리됨 |
| Intro/Related Work 중복 | `[x]` | Intro는 design necessity, Related Work는 literature contrast를 담당함 |
| Intro/Related Work 분량 | `[x]` | 현재 압축 수준은 Method와 Experiment 공간을 침해하지 않음 |
| 주석 처리된 obsolete text | `[x]` | PDF에 영향을 주는 obsolete 대안 문단은 없음. Experiments의 한 줄 comment는 무해한 source cleanup 대상 |

## 4. Section별 검토

### Abstract

- `[x]` **고유 용어의 최소 설명과 자기 완결성:** RelCompat3D를 fixed relation
  prediction을 위한 re-ranking framework로 정의한다.
- `[x]` **문제--방법--결과--기여:** High-score mismatch, compatibility
  estimation, family-aware re-ranking, three-predictor result, alternative
  audit가 모두 포함된다.
- `[x]` **Introduction contribution과 대응:** Introduction의 세 contribution과
  과부족 없이 대응한다.
- `[x]` **Hedging과 claim boundary:** `reported predictor--K settings`,
  `point estimates`, `verifier-derived`가 claim을 정확히 제한한다.
- `[x]` **문장당 정보량:** Result sentence는 두 metric의 joint claim 하나를
  전달하며 추가 분할이 필수적이지 않다.
- `[x]` **Citation과 기호:** Citation과 정의되지 않은 기호가 없다.
- `[x]` **Experiment 수치와 일치:** All-\(K\) non-decrease/non-increase
  point-estimate claim이 Table 1과 일치한다.

### Introduction

- `[x]` **현재 claim을 명시적으로 제안하는 문장:** Source score가 same-pair
  compatibility를 직접 추정하지 않는다는 한계와 `We propose RelCompat3D`
  문단이 task, inputs, score exclusion, estimators, training,
  transformations를 명시한다.
- `[x]` **선행연구 citation 존재:** 언급된 연구군과 predictor에 citation이 있다.
- `[x]` **Contribution 세 개와 Method 대응:** Contribution 1은 Problem
  Formulation과 Metrics, Contribution 2는 Compatibility Estimation,
  Contribution 3은 Family-Aware Re-Ranking과 cross-predictor evaluation에
  대응한다. Literal subsection 이름보다 기능적 1:1 대응이 명확하다.
- `[x]` **Method 전용 용어 정의:** \(T,G,Z\), counterfactual과 transformation의
  차이, re-ranking scope가 Method 전에 필요한 수준으로 설명된다.
- `[x]` **논리 흐름:** Downstream need, observed failure, score limitation,
  compatibility design, ranking, evaluation, contributions 순서가 자연스럽다.
- `[x]` **Experiment 수치와 일치:** 모든 다섯 \(K\)에서 두 variants의 Recall
  point estimate는 Source보다 낮지 않고 Violation은 높지 않다. SGFN \(K=5\)
  tie도 현재 표현에 포함된다.
- `[x]` **Hedging 일관성:** `point estimates`, shared target, alternative audit
  표현이 Results와 Discussion의 범위와 맞는다.
- `[x]` **Figure 1 역할:** Motivation을 보여주는 qualitative failure case로
  적합하며 Results에서 다시 호출된다.

### Related Work

- `[x]` **Subsection 구성과 제목 정합성:** 3D Scene Graph Prediction,
  Geometry-aware Relation Evidence, Reliability Evaluation and Calibration의
  세 축이 내용과 일치한다.
- `[x]` **선행연구 citation 정확성:** 43개 current key가 bibliography와
  일치한다. OpenScene, GEODE, VIZOR, Ovadia key를 선택한 entries와 통일했고,
  RelWitness는 proposal 범위로 낮췄으며 TAD는 실제 참고한 v1 URL을 명시했다.
  Heo 2026은 저자가 확인한 Scholar와 author repository metadata를 따르는
  저자 결정이다.
- `[x]` **Citation 중복과 mapping:** SGAligner/SG-PGM의 반복 설명은
  삭제됐다. Method와 Experiments에서도 source와 citation mapping을 문장별로
  분리했고 citation 앞 spacing을 정리했다.
- `[x]` **공통점과 차이점:** 각 연구군 뒤에서 fixed-generator
  post-processing, source-score exclusion, transformation consistency라는
  RelCompat3D의 차이를 구체화한다.
- `[x]` **Introduction과 중복 관리:** 같은 핵심 용어를 사용하되 motivation
  문단을 그대로 반복하지 않는다.
- `[x]` **Calibration 경계:** Recall@\(K\)와 Violation@\(K\)가 calibrated
  probability를 제공하지 않는다고 명시한다.
- `[x]` **Figure 2 연결:** Caption은 input separation, score combination,
  re-ranking 결과를 자기완결적으로 설명하고 Method 본문이 세부 절차를 잇는다.
- `[x]` **Figure 2 source 복구:** `fig:overall_framework` block과
  `Figure2_outlined_v15.pdf` 경로가 복구됐다. Clean build에서 Figure 2로
  배치되고 Method와 Results의 두 참조가 모두 해결된다.

### Method

- `[x]` **Notation과 정의 순서:** Candidate identity, \(T,G,Z,a\),
  evaluated/ranked family를 순서대로 정의하고 재정의하지 않는다.
- `[x]` **Introduction 설계 선택과 대응:** Linear/MLP estimators, linked
  counterfactuals, transformation averaging, family-aware scoring이 예고한
  설계와 대응한다.
- `[x]` **수식과 prose의 일치:** Source score는 compatibility estimator에
  들어가지 않고 within-family score에서만 결합된다.
- `[x]` **Support/contact 범위:** Identity transformation과 source-order
  preservation이 명확하다.
- `[x]` **가정과 scope:** Known instances, reconstructed pair geometry,
  applicable relation transformations를 명시한다.
- `[x]` **재현 가능성:** Active optimizer, step 수, learning rate, seed와
  sensitivity가 supplement 및 frozen protocol과 일치한다.
- `[x]` **Figure caption 연결:** Figure 2의 flow와 Problem Formulation,
  Compatibility Estimation, Family-Aware Re-Ranking이 같은 순서를 따른다.
- `[x]` **비필수 source cleanup:** `3_method.tex`의 prose와
  `\subsubsection{Linear Estimator.}`가 같은 physical line에 있으나 PDF와
  scientific content에는 영향이 없다.

### Experiments

- `[x]` **Dataset과 evaluation scope:** 157 scans, 548 contexts, 3,972 exact
  ground-truth relations가 명확하다. `Evaluation-split ground-truth
  relations`로 범위를 한정해 Method의 training positives와 문면상 충돌하지
  않는다. 첫 문장도 `on the 3DSSG validation split of 3RScan`으로 교정되어
  157-scan evaluation scope와 자연스럽게 연결된다.
- `[x]` **공정한 비교:** 세 predictor는 같은 target, candidate scope, metrics,
  \(K\), bootstrap protocol에서 평가된다.
- `[x]` **Metric 정의와 사용:** Recall과 Violation은 한 곳에서 정의되고 이후
  일관되게 쓰인다.
- `[x]` **\(K\) 범위 일관성:** \(K\in\{5,10,20,50,100\}\)이 Table 1,
  Figure 3, main prose, supplement에서 일치한다.
- `[x]` **Table 1 비교 범위:** Bold는 family sequence와 support/contact order를
  보존하는 comparable rows 안에서만 metric별 best를 표시한다. Product는 scope
  comparison으로 제외된다.
- `[x]` **Ablation과 설계 대응:** Table 2는 predicate, pair identity, geometry,
  source score의 역할을 검증하며 matched MLP controls는 supplement에 있다.
- `[x]` **Main sensitivity 문장:** M-1, M-2, M-3은 supplement의 frozen score
  mapping, robust-density, routing-control 결과와 일치한다.
- `[x]` **통계적 주장:** \(K=50\) paired interval 문장과 point-estimate
  all-\(K\) 문장을 구분하며 실제 표와 일치한다.
- `[x]` **Alternative audit 경계:** Point/mesh audit는 alternative
  measurement이지 independent ground truth가 아니라고 명시한다.
- `[x]` **Qualitative coverage:** Main text가 vertical demotion, proximity
  demotion, proximity promotion을 포함한다. Figure 1과 Figure 2의 이미 검증된
  사례를 재사용하므로 선택적 사례를 새로 추가하지 않는다.

### Discussion and Limitations

- `[x]` **Scope 한계 일관성:** Single target, known instances,
  support/contact scope가 Method와 일치한다.
- `[x]` **통계적 주장:** Dataset-level generalization과 independent physical
  validity를 주장하지 않는다.
- `[x]` **자기비판의 균형:** 필요한 claim boundary만 남기고 과도한 약점 나열을
  피한다.
- `[x]` **실패와 약한 지점:** Point/mesh audit가 same scenes와 ontology를
  사용한다는 한계와 additional-dataset 필요성을 정직하게 설명한다.
- `[x]` **Ethics/Broader impact:** 별도 broader-impact paragraph가 필요한
  위험한 application claim은 없고 ethics violation도 저자 확인 결과 해당 없다.

### Conclusion

- `[x]` **Introduction과 연결:** Motivating problem으로 돌아가 method와 scoped
  result를 한 문장씩 요약한다.
- `[x]` **새 주장 여부:** Method와 Experiment에 없던 수치, claim, future work를
  추가하지 않는다.
- `[x]` **Overclaiming 방지:** `the shared 3DSSG validation scenes`, `point
  estimates`, `lower or tied`, `preserving or improving`이 evidence의 hedging과
  일치한다.
- `[x]` **중복 관리:** Contribution bullets를 그대로 반복하지 않고 problem
  resolution 중심으로 끝난다.

### Supplement

- `[x]` **구조와 main 정합성:** Notation/preprocessing, construction boundary,
  formal properties, optimization, diagnostics, robustness, audit, controls,
  intervals, transfer, qualitative cases 순서가 main의 story를 확장한다.
  28,977/37,477은 training+internal-development 합계로 명시되어 뒤의 60,208
  fitting rows와 구분된다.
- `[x]` **용어와 notation:** Active optimizer 설명과
  \(g_\gamma,g_\tau\) score-mapping notation이 main 및 frozen protocol과
  일치한다.
- `[x]` **Figure/Table 호출:** 모든 supplement Figure와 Table이 본문에서 최소
  한 번 참조된다.
- `[x]` **Author Kit typography:** 네 caption의 manual bold와 paired-interval
  cell의 7-point `\scriptsize`를 제거했다. Caption은 roman이고 해당 table은
  surrounding `\small` 9-point text를 사용한다.
- `[x]` **정보량과 우선순위:** 10쪽과 17 tables는 main claim 방어와 재현성에
  필요한 compact evidence다. Full per-condition rows는 machine-readable
  artifact로 분리했다.
- `[x]` **Main self-containment:** Supplement-only evidence는 sensitivity,
  diagnostic, oracle, provenance이며 core method와 main claim은 supplement
  없이 이해 가능하다.
- `[x]` **최종 영어 교정:** Negative-cap 문장의 병렬 구조,
  row-regeneration error 문구, relation-family terminology와 selected-subsequence
  표현을 교정했다. Uncertainty denominator의 대체 문장은 의미 오류가 없는
  선택적 개선이므로 현재 표현을 유지해도 된다.

### Reproducibility Checklist

- `[x]` **Official template 보존:** 질문, Instructions, response options를
  수정하지 않고 author response만 채웠다.
- `[x]` **Main과 supplement 근거:** Dataset access, Docker preprocessing,
  metric definitions, fixed seeds, final hyperparameters, bootstrap intervals,
  infrastructure 답변이 manuscript와 code/data package 범위에 맞는다.
- `[x]` **`partial` 응답의 정직성:** Controlled dataset access, excluded
  third-party assets, release-license 경계 때문에 code와 dataset 공개 문항을
  과장해 `yes`로 쓰지 않았다.
- `[x]` **Theoretical section 처리:** Parent answer가 `no`이고 하위 문항 앞에
  `If yes`가 있으므로 하위 response를 비워 둔 현재 형식이 적절하다.
- `[x]` **Build:** Standalone checklist는 2-page US Letter, PDF 1.5로
  빌드되며 warning, overfull box, font 문제가 없다.

## 5. Section 간 정합성 체크리스트

| 항목 | 상태 | 판정 |
|---|---|---|
| 용어 통일 | `[x]` | Main과 supplement의 core terms 및 score-mapping notation이 일치함 |
| Citation 존재와 정확성 | `[x]` | Current main의 43개 key가 모두 bibliography에 존재하고 CIT-01--CIT-08의 wording, version, mapping 판정이 source에 반영됨 |
| Notation | `[x]` | \(T,G,Z,q,C,u,g_\gamma,g_\tau\)가 재정의 없이 일관됨 |
| Claim/evidence mapping | `[x]` | 세 contribution이 Method와 Experiment evidence에 대응함 |
| 요약 수치 | `[x]` | Abstract, Intro, Results, Conclusion의 all-\(K\) claim이 Table 1과 일치함 |
| Statistical claim | `[x]` | point estimate와 interval claim을 구분함 |
| Hedging tone | `[x]` | `verifier-derived`, `shared target`, `point estimate`, `stress test`가 일관됨 |
| 용어 최초 정의 | `[x]` | \(T,G,Z\), MLP, OBB, metrics가 사용 전에 정의됨 |
| Main self-containment | `[x]` | 핵심 method, main metrics, comparison, controls, limitations이 main에 있음 |
| Main--supplement pointer | `[x]` | optimization, matched MLP controls, component removal, audit, intervals가 연결됨 |
| Main--supplement 수치 | `[x]` | M-1--M-3, audit, intervals, controls가 일치하고 constructed training+internal-development 합계와 fitting rows도 구분됨 |
| Main--supplement scope | `[x]` | Main은 core claim, supplement는 sensitivities와 reproducibility를 담당함 |
| Split boundary | `[x]` | Method의 training-split positives와 Experiments의 `Evaluation-split ground-truth relations`가 명확히 구분됨 |
| Figure numbering and references | `[x]` | Figure 2 복구 후 Figure 1--3 번호, labels, Method/Results references가 clean build에서 모두 해결됨 |
| Checklist--manuscript 정합성 | `[x]` | Dataset access, Docker code, seed, hyperparameter, metric, bootstrap, hardware 답변이 main/supplement와 일치하며 공개 범위가 제한된 문항은 `partial`로 유지됨 |

## 6. Introduction claim과 evidence 연결

| Introduction claim/contribution | Method 대응 | Main evidence | Supplement evidence | 상태 |
|---|---|---|---|---|
| Source score와 ordered-pair compatibility의 mismatch | \(T,G,Z\) 분리, score-excluded \(C\) | Figure 1, Table 1, Figure 3 | score ranges, simple baseline, feature removal | `[x]` |
| Ordered-pair identity가 필요함 | pair identity key와 geometry join | Table 2 wrong pair/shuffled geometry | Linear/MLP matched controls | `[x]` |
| Applicable transformations의 consistency | transformation orbit와 averaging | Table 2 wrong predicate/fixed swap, supplement pointer | exact diagnostics와 no-averaging control | `[x]` |
| Source score와 compatibility가 상호 보완적임 | \(u=ZC^{\rm tr}\) | compatibility-only, distance-only, RankAvg/RRF | robust-density와 mapping sensitivity | `[x]` |
| Family-aware re-ranking | family sequence와 support/contact subsequence 보존 | Product scope comparison, M-3 prose | Joint P/V matched routing control | `[x]` |
| Verifier dependence를 제한해서 해석함 | verifier input exclusion boundary | Table 3, Discussion | dependency matrix, feature removal, uncertainty variants | `[x]` |
| Fixed-candidate method임 | generator를 교체하지 않는 formulation | three frozen predictors | candidate-pool oracle | `[x]` |

세 contribution과 설계/evidence의 대응:

1. Mismatch 정의와 joint metric은 Figure 1, Table 1, Figure 3, Table 3으로 검증된다.
2. Score-excluded compatibility와 transformations는 Table 2와 matched removal로
   검증된다.
3. Family-aware re-ranking은 Method의 preservation rule과 routing controls로
   검증된다.

## 7. Figure와 Table 점검

### 7.1 Main

| 항목 | 본문 참조 | Caption 자기완결성 | 수치/표현 | 판정 |
|---|---:|---|---|---|
| Figure 1 | Yes | Source, contradiction, before/after rank, top-50을 설명 | 6 \(\rightarrow\) 425 일치 | `[x]` |
| Figure 2 | Yes | pair geometry, score exclusion, within-family combination, result를 설명 | 19 \(\rightarrow\) 178은 Linear 결과와 일치 | `[x]` |
| Figure 3 | Yes | metrics, \(K\), methods, preferred direction, axis 차이를 설명 | Table 1 전 수치와 일치 | `[x]` |
| Table 1 | Yes | dataset, metrics, Source, bold scope, Product scope를 설명 | 모든 \(K\)와 prose claim 일치 | `[x]` |
| Table 2 | Yes | controls, estimator scope, metrics, units, ranking procedure를 설명 | Results 해석과 일치 | `[x]` |
| Table 3 | Yes | \(K\), agreement label, \(\Delta V\), M/D, units를 설명 | 수치와 prose가 일치하고 manual-bold caption도 제거됨 | `[x]` |

Figure 1이 page 1에 있는 것은 문제가 아니다. Qualitative motivation/failure case를
teaser로 두고 Results에서 다시 참조하는 구성은 자연스럽다. Figure 2는 복구된
source에서 page 4의 Figure 2로 정상 배치되며 caption과 본문 참조도 일치한다.
Figure 2 caption의 quotation은 relation label을 충분히 구분하며 `\texttt`로 바꿀
필요가 없다.

### 7.2 Supplement

- Figure 1개는 본문에서 호출되고 caption이 subject/object encoding과 outcome을
  설명한다.
- Table captions는 dataset/metric/condition을 대체로 설명한다.
- 모든 Figure와 Table이 본문에서 최소 한 번 호출된다.
- Full tables의 숫자는 main의 compact rows 및 machine-readable outputs와 일치한다.
- Table 8, 11, 13, 14 caption은 roman caption으로 통일됐고 paired-interval
  table도 9-point `\small` text를 사용한다.

## 8. Main--Supplement 반영 상태

### 8.1 Main에 남긴 evidence

- M-1: five pre-specified monotonic score transformations의 scoped robustness
- M-2: \(K=50\) robust-density comparator
- M-3: matched routing control의 mixed result와 composition-preserving 해석
- Core Table 1--3, Figure 1--3
- Point/mesh alternative measurement와 independent-ground-truth caveat

### 8.2 Supplement-only 결정

다음 항목은 저자와 에이전트 모두 supplement-only가 적절하다고 판단했다.

- M-4: component removal과 linked-pair diagnostics
- M-5: five-seed training robustness
- M-6: point/mesh full-\(K\), uncertainty-policy, feature-removal package
- M-7: full score-mapping and percentile stress rows
- M-8: full routing and family-composition rows
- M-9: candidate-pool oracle and row-level reproduction

이들은 main claim을 보강하지만 main table/plot의 핵심 비교를 바꾸지 않는다.
Main에 모두 넣으면 7-page story가 sensitivity study 중심으로 흐려진다.

### 8.3 Main에 없는 것이 정당한 항목

- Full per-\(K\) confidence intervals
- Hard-tail/Hard-drop direct-verifier diagnostics
- Open3DSG coverage recovery
- ReplicaSSG/FROSS transfer stress
- Feature-removal variants와 alternative uncertainty denominators
- Oracle Recall과 row-level artifact schema

Main은 해당 항목 없이도 core method와 scoped evidence를 이해할 수 있다.

## 9. Reviewer 관점의 잔여 risk와 대응

AAAI-27은 Phase 1에서 reject된 paper에 author response를 제공하지 않는다.
따라서 아래 rebuttal 계획은 Phase 2에 진입했을 때의 대응이며, main의 core
evidence 누락을 나중에 보충하는 수단으로 간주하지 않는다. 현재 24시간 안에
무리한 새 experiment를 추가하기보다 scoped claim과 이미 완료된 evidence를
정확히 연결하는 것을 우선한다.

### Major 1. Evaluator와 training construction의 construct dependence `[범위 한계 / 처리 방향]`

원문:

> The compatibility estimators and primary verifier share some oriented bounding
> box (OBB)-derived measurements.

Risk:

- Counterfactual construction과 primary verifier가 OBB primitive와 일부 threshold를
  공유한다.
- Point/mesh audit도 같은 reconstructed scenes와 ontology를 사용하므로 independent
  physical-validity ground truth가 아니다.

현재 대응:

- Evaluation rows, source scores, verifier labels는 training construction에서 제외한다.
- Exact/related feature removal, uncertainty variants, point/mesh audit,
  dependency matrix를 보고한다.
- Discussion에서 independent ground truth가 아니라고 명시한다.

Main 제출 전 24시간:

- 새 human label을 급하게 추가하지 않는다. Annotation protocol 없이 저자가
  method output을 본 뒤 만든 label은 independent evidence로 방어하기 어렵고,
  post-hoc confirmation bias 우려를 추가한다.
- Main의 claim을 `verifier-derived Violation`과 `alternative geometric
  measurements`로 유지한다. Point/mesh audit을 physical ground truth로
  부르지 않는다.
- Training construction, primary verifier, point/mesh audit이 공유하거나
  제외하는 정보를 supplement dependency matrix에 그대로 유지한다.

Rebuttal 기간:

- Reviewer가 이 construct validity를 직접 문제 삼으면 현재 dependency matrix,
  feature removal, uncertainty sensitivity, point/mesh agreement 결과를 먼저
  연결해 답한다.
- 추가 human audit이 필요하면 frozen random sample과 사전 정의한 annotation
  rubric을 사용한다. Annotator에게 predictor, Source/Linear/MLP, rank,
  compatibility, verifier label을 숨기고 raw reconstructed points/meshes만
  제시한다. Candidate order도 무작위화한다.
- 가능하면 저자 외 annotator를 포함하고 두 명 이상의 독립 label,
  inter-annotator agreement, disagreement adjudication을 보고한다. 저자 한 명만
  label하면 `author-annotated blind audit`으로 명명하고 independent ground truth로
  부르지 않는다.
- Rebuttal에서 처음 만든 소규모 audit은 보조 분석으로만 사용한다. Core validity
  claim을 사후 실험 하나에 의존시키지 않는다.

현재 수준으로 유지할 boundary:

- `independent physical validity`를 주장하지 않고 `verifier-derived reliability on
  a shared target`으로 답한다.
- Reconstructed point cloud나 mesh를 사람이 보고 만든 label은 independent human
  reference label이 될 수 있지만 실제 scene의 physical ground truth는 아니다.
  Physical-validity claim에는 별도 reference annotation과 richer contact/pose
  evidence가 필요하다.

### Major 2. Single-target external validity와 downstream significance `[범위 한계 / 처리 방향]`

Risk:

- 세 predictor 비교가 하나의 3DSSG target에 집중된다.
- ReplicaSSG/FROSS는 supplement stress test이며 support/contact ontology를
  포함하지 않는다.
- 실제 downstream task 개선은 보고하지 않는다.

현재 대응:

- Abstract, Discussion, Conclusion을 shared-target claim으로 제한한다.
- Fixed predictor reliability layer로 contribution을 정의한다.
- Supplement에서 transfer와 candidate coverage를 공개한다.

Main 제출 전 24시간:

- 새 dataset이나 downstream task를 급하게 추가하지 않는다. 현재 main의 split,
  scenes, point-estimate wording과 Discussion의 dataset-level generalization
  boundary를 유지한다.
- Abstract, Introduction, Results, Conclusion에서 `across three predictors on
  the shared 3DSSG validation scenes`보다 넓은 일반화 표현이 없는지만 최종 확인한다.
- ReplicaSSG/FROSS와 candidate-pool oracle은 supplement evidence로 유지하고 main
  headline claim으로 승격하지 않는다.

Rebuttal 기간:

- 이 논문의 evidence axis는 dataset 수가 아니라 동일 target에서 predictor가 바뀌어도
  나타나는 score--geometry mismatch라고 설명한다.
- Same target은 annotation, candidate scope, verifier와 \(K\)를 고정해 predictor
  차이를 비교하는 controlled design이라는 점을 명확히 한다.
- Reviewer가 transfer를 묻는 경우 supplement의 ReplicaSSG/FROSS stress test와
  ontology/geometry shift에 따른 non-uniform behavior를 함께 제시한다.

현재 수준으로 유지할 boundary:

- Dataset-level generalization과 embodied downstream utility는 주장하지 않는다.
- Single-target limitation은 제거할 수 있는 writing issue가 아니라 현재 evidence
  범위다. Additional datasets와 downstream tasks는 future extension으로 유지한다.

### Major 3. Novelty가 calibration/post-processing의 결합으로 보일 위험 `[부분 대응 / 처리 방향]`

Risk:

- Reviewer가 method를 geometry features와 product re-ranking의 incremental
  combination으로 볼 수 있다.
- Pairwise loss 제거의 aggregate 변화가 작다.

현재 대응:

- Novelty를 새 fusion formula가 아니라 source-score-excluded same-pair
  compatibility, relation-preserving transformations, family-composition
  constraint의 결합으로 정의한다.
- Matched RankAvg/RRF, robust-density, component removal, routing control을
  보고한다.

Main 제출 전 24시간:

- `[x]` 새 실험보다 Introduction의 failure cause와 design necessity를 한 문장으로
  선명하게 만드는 것을 우선했다. Line 18에 다음 문장이 반영됐다.

  > Geometry may inform a predictor without making its source relation score an
  > explicit estimate of whether the same ordered pair satisfies the predicate
  > in 3D.

- Contribution과 Method 이름은 `source-score-excluded same-pair compatibility`,
  `relation-preserving transformations`, `family-aware re-ranking`에 계속
  대응시킨다.
- Product formula 자체, geometry feature 사용, pairwise loss 단독을 novelty로
  제시하지 않는다.

Rebuttal 기간:

- 단일 component의 우월성이 아니라 세 design constraint가 failure cause에 각각
  대응한다는 구조를 강조한다.
- Wrong-predicate/wrong-pair/shuffled-geometry controls는 same-pair compatibility,
  transformation removal은 equivalent representation consistency, matched
  routing control은 family-composition constraint에 대응한다고 표 형태로
  연결할 수 있다.
- Robust-density, RankAvg/RRF, score-mapping sensitivity를 이용해 단순
  post-processing 또는 score-scale artifact만으로 설명되지 않는다고 답한다.

현재 수준으로 유지할 boundary:

- Pairwise loss를 전체 성능의 유일한 원인으로 주장하지 않는다.
- RelCompat3D를 universal calibration, new relation generator, aggregate-optimal
  fusion rule로 확장해 주장하지 않는다.
- Novelty는 각 component의 개별 최초성보다 failure-specific constraints를 갖춘
  fixed-prediction reliability framework에 둔다.

### Major 4. Product score의 scale sensitivity `[대응 완료, scoped]`

현재 대응:

- Fixed monotonic grid에서 Linear 75/75, MLP 74/75 conditions가 Source-relative
  joint direction을 유지한다.
- Percentile stress의 작은 Recall losses와 score-scale invariance가 아님을
  supplement에 공개한다.
- Main은 `Source-relative conclusion remains unchanged ... all but one
  comparison`으로 정확히 요약한다.

남은 원칙: `scale invariant`를 주장하지 않는다.

### Major 5. Family-aware rule의 필요성과 aggregate optimum 부재 `[대응 완료, residual reviewer risk]`

현재 대응:

- Joint P/V matched control은 estimator와 \(K\)에 따라 결과가 달라진다.
- 따라서 family-aware route를 aggregate-optimal이라고 주장하지 않는다.
- Main과 supplement 모두 composition-preserving constraint로 해석한다.
- Table~1의 Product (all families)가 일부 predictor와 \(K\)에서 더 높은 aggregate
  Recall 또는 더 낮은 Violation을 보인다는 사실도 숨기지 않는다.

남은 reviewer risk:

- Aggregate metric만 중시하는 reviewer는 source family composition을 보존해야 하는
  이유보다 Product의 더 좋은 일부 수치에 주목할 수 있다.
- 현재 방어는 family-aware rule이 최고 성능을 위한 heuristic이 아니라
  cross-family competition과 support/contact 변경을 막는 scope constraint라는
  점이다. 이 선택은 명확하지만 모든 reviewer가 그 실용적 가치를 높게 평가하지는
  않을 수 있다.

### Major 6. Closest simple baseline 부족 `[대응 완료]`

현재 대응:

- Training-positive robust-density baseline을 동일 candidate pool과 route에서
  평가한다.
- Main은 \(K=50\)에서 두 variants가 세 predictor 모두에서 higher Recall/lower
  Violation임을 한 문장으로 보고한다.
- Hard-tail/Hard-drop은 verifier label을 ranking input으로 쓰는 non-deployable
  diagnostics로 분리한다.

### Major 7. Artifact reproducibility와 licensed-input 접근성 `[부분 대응, 보수적 배포]`

현재 대응:

- Derived rows로 Table 1--3과 Figure 3 data를 한 command에서 재생성한다.
- 291 canonical cells를 tolerance \(10^{-12}\)에서 maximum error 0으로 검증한다.
- Docker exporter, reproducer, schema, compact outputs, manifests가 있다.

Current ZIP은 licensed row bundle과 stable source identifiers를 제외하고
deterministic exporter, schema, compact outputs, expected manifest를 포함한다.
이 보수적 boundary에서 release 검증은 통과했다.

남은 reviewer risk:

- Reviewer는 current ZIP만으로 raw predictions, geometry joins, Table 1--3을
  end-to-end 재생성할 수 없다. Full regeneration에는 3RScan/3DSSG access,
  source-predictor outputs 또는 checkpoints, 그리고 excluded derived rows가
  필요하다.
- 따라서 artifact는 implementation과 compact-result verification에는 강하지만,
  외부 licensed inputs 없이 즉시 실행되는 self-contained reproduction은 아니다.
- 제출 시에는 checklist의 `partial` boundary와 README를 그대로 유지한다. Source
  terms가 명시적으로 허용하지 않는 row나 stable identifier를 reproducibility
  점수를 높이기 위해 재배포하지 않는다.

### Major 8. Restricted relation-family scope와 non-standard benchmark interpretation `[범위 한계 / 추가 risk]`

원문:

> Candidates outside these families are excluded from the reported Recall and
> Violation evaluation.

> Support/contact is evaluated but kept in source order.

Risk:

- Reported evaluation은 support/contact, proximity, vertical-order로 제한되고,
  RelCompat3D가 실제로 순서를 바꾸는 family는 proximity와 vertical-order뿐이다.
- 따라서 Table~1의 Recall@$K$는 full-ontology 3DSSG relation prediction 성능이나
  기존 논문의 표준 Recall과 직접 비교하는 수치가 아니다.
- Fixed-candidate re-ranking은 candidate pool에 없는 exact relation을 생성할 수
  없다. Supplement oracle에서도 Open3DSG exact-label candidate coverage는
  79.68\%로, generation ceiling이 명확하다.
- Reviewer는 실제 개선 범위를 두 relation families의 post-hoc correction으로
  좁게 평가할 수 있다.

현재 대응:

- Method와 Experiments에서 evaluation family와 re-ranking family를 분리해
  정의한다.
- Introduction, Discussion, Conclusion은 fixed predictions와 shared validation
  scenes로 claim을 제한한다.
- Table~1은 paper 내부의 Source-relative comparison으로만 사용하며 SOTA나 기존
  full benchmark와의 우월성을 주장하지 않는다.
- Supplement는 per-family metrics, family composition, Product scope comparison,
  candidate-pool coverage와 oracle Recall을 제공한다.

Rebuttal 방향:

- 이 논문의 질문은 relation generator의 전체 accuracy가 아니라, fixed candidate의
  source score가 same-pair geometric compatibility를 반영하는지라고 명확히 한다.
- 동일 candidate pool, family scope, verifier와 \(K\)를 고정한 Source-relative
  comparison이 이 질문에 맞는 controlled evaluation임을 설명한다.
- 동시에 absent candidates와 support/contact correction은 해결하지 않는다는
  boundary를 유지한다. Full-ontology 또는 graph-generation improvement로 claim을
  확장하지 않는다.

### Minor risk

| 항목 | 상태 | 판단 |
|---|---|---|
| Primary verifier transparency | `[x]` | metric, status, construction overlap, feature removals을 supplement에 공개함 |
| Uncertain denominator | `[x]` | Main에서 uncertain이 denominator에 들어감을 정의하고 alternative policies를 supplement에 둠 |
| Training stochasticity | `[x]` | five-seed Linear/MLP 결과와 한 작은 exception을 supplement에 공개함 |
| Qualitative selection | `[x]` | Main text가 vertical demotion, proximity demotion, proximity promotion을 다루고 supplement에 three-family panel이 있음. Systematic blinded audit은 더 강한 claim을 위한 선택적 확장이지 현재 이슈가 아님 |
| Open3DSG coverage | `[x]` | 533/548 public coverage와 recovery sensitivity를 supplement에 공개함 |
| Fixed-candidate ceiling | `[x]` | Method scope와 candidate-pool oracle이 generation error를 분리함 |
| Predictor-dependent effect size | `[범위 한계]` | Open3DSG 변화는 크지만 VL-SAT와 SGFN의 Recall 변화는 작다. Main이 이를 숨기지 않고 `predictor-dependent behavior`로 framing하므로 오류는 아니지만 significance 평가에는 불리할 수 있음 |
| Phase-1 evidence visibility | `[잔여 presentation risk]` | Robust-density, routing, component, seed, oracle의 full tables는 supplement에 있다. Main에는 M-1--M-3 요약이 있지만 Phase-1 reviewer가 supplement를 적게 읽으면 novelty defense가 Table~1과 Table~2 중심으로 보일 수 있음 |
| Multiple-\(K\) interpretation | `[x, scoped]` | 모든 \(K\)에 대한 문장은 point-estimate 방향만 주장한다. 통계적 검정이나 family-uniform significance로 확대하지 않으므로 multiplicity overclaim은 없음 |

## 10. P0/P1 evidence 상태

완료 protocol의 긴 path와 hash는 experiment README와 manifest가 소유한다. 여기서는
paper-facing 결론만 유지한다.

| 분석 | 핵심 결과 | Main | Supplement | 상태 |
|---|---|---|---|---|
| P0-1 score mappings | Smooth mappings에서 Linear 75/75, MLP 74/75 joint direction 유지 | M-1 | full mapping/percentile/rank stability | `[x]` |
| P0-2 robust-density | \(K=50\)에서 두 variants가 세 predictors의 baseline을 Pareto-dominate | M-2 | all-\(K\), direct-verifier diagnostics | `[x]` |
| P0-3 routing | Joint P/V 결과가 estimator와 \(K\)에 따라 달라짐 | M-3 | all-\(K\), composition changes | `[x]` |
| P0-4 construct dependence | OBB overlap을 공개하고 alternative evidence와 uncertainty policies로 경계 확인 | Table 3/Discussion | dependency package | `[x]` |
| Component diagnostics | Pairwise/no-averaging와 transformation error 보고 | pointer | Linear/MLP full diagnostics | `[x]` |
| Seed robustness | 다섯 fixed seed에서 방향 안정성 점검 | 없음 | mean/std와 exception | `[x]` |
| P1-1 row reproduction | 291 cells exact regeneration | 없음 | schema와 validation | `[x, conservative release]` |
| P1-2 candidate oracle | fixed candidate ceiling과 attainable gap 정량화 | 없음 | three oracle bounds | `[x]` |

## 11. AAAI-27 제출 체크리스트

Official references:

- [Main Technical Track Call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/)
- [Submission Instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/)
- [Supplementary Material](https://aaai.org/conference/aaai/aaai-27/supplementary-material/)
- [AAAI Publication Policies](https://aaai.org/aaai-publications/aaai-publication-policies-guidelines/)

| 항목 | 상태 | 최종 조치 |
|---|---|---|
| 7 technical pages / 9 total | `[x]` | current source PDF 기준 충족 |
| References only after page 7 | `[x]` | pages 8--9는 references only |
| Anonymous main/supplement | `[x]` | 저자 식별 정보 없음 |
| No author-owned web links | `[x]` | 해당 링크 없음 |
| Fonts/letter/PDF | `[x]` | current build 통과 |
| Caption typography | `[x]` | Main과 supplement caption에서 manual bold가 없음 |
| Table minimum font | `[x]` | Supplement interval table이 `\small` 9-point text를 사용함 |
| Overfull boxes | `[x]` | Main, supplement, checklist final logs에서 overfull box 0 |
| Reproducibility checklist | `[x]` | 2-page separate PDF |
| Supplement optional/self-contained main | `[x]` | core claims는 main에서 이해 가능 |
| Author list finality | `[저자 확인]` | submission system에서 지금 확정 |
| Multiple submissions | `[x]` | 저자 확인 결과 해당 없음 |
| Ethics violation | `[x]` | 저자 확인 결과 해당 없음 |
| Generative AI policy | `[저자 확인]` | F-06 처리 |
| Derived data license | `[x, 보수적 처리]` | Stable IDs와 source-derived row bundles를 ZIP에서 제외함 |
| Final file synchronization | `[x]` | 최종 source에서 canonical PDFs, release ZIP, outer/inner manifests를 재생성했고 extracted-source 9/10/2-page rebuild와 PDF text equivalence를 확인함 |
| Last-hour upload risk | `[저자 확인]` | 최종 files를 deadline 직전이 아닌 시점에 업로드 |

## 12. 제출 전 남은 저자 작업

Scientific content, citation, layout, final copy-edit, canonical PDFs, and
release validation are complete. 남은 제출 작업은 저자 소유의 다음 두 가지다.

1. F-06의 실제 generative-AI 역할을 확인하고 AAAI policy에 맞게 manuscript에
   문서화한다.
2. Submission-system author list, order, profiles, conflicts, topics, TL;DR,
   upload slot을 확인한 뒤 deadline 이전에 업로드한다. OpenReview가 표시하는
   page count와 rendered PDF도 마지막으로 확인한다.

## 13. 예상 reviewer 판정

### 예상 Rating: Weak Reject (borderline Weak Accept)

강점:

1. Failure mode와 claim boundary가 명확하다.
2. 세 fixed predictor에서 같은 target/protocol로 비교한다.
3. Main controls와 supplement sensitivities가 reviewer의 단순-baseline,
   score-scale, routing, component 질문에 직접 답한다.
4. Point/mesh audit와 dependency disclosure가 verifier dependence를 숨기지 않는다.
5. Docker source, compact artifacts, manifests와 extracted-source rebuild까지
   제공해 구현 및 결과 추적 가능성이 높다.

Weak Reject를 중심값으로 두는 이유:

1. 핵심 validity evidence가 independently annotated physical ground truth는
   아니며, counterfactual construction과 primary verifier가 일부 geometric
   primitives를 공유한다.
2. Main empirical claim은 하나의 3DSSG validation split과 제한된 relation-family
   scope에 집중된다. 실제 re-ranking은 proximity와 vertical-order에만 적용된다.
3. Fixed-candidate post-hoc method이므로 absent relations, object-instance errors,
   support/contact correction과 downstream task utility를 해결하지 않는다.
4. 일부 reviewer는 source-score exclusion, transformations, family constraint의
   결합을 principled framework보다 careful geometry-based post-processing으로
   평가할 수 있다.
5. 효과 크기는 predictor-dependent하다. Open3DSG에서는 크지만 VL-SAT와 SGFN의
   Recall 변화는 작다.
6. Release는 강한 compact verification을 제공하지만 licensed inputs 없이 raw
   end-to-end result regeneration이 가능한 self-contained artifact는 아니다.

Weak Accept로 이동시키는 가장 중요한 방어:

- Claim을 full 3DSSG 성능이나 physical validity로 넓히지 않는다.
- Same-pair source-score-excluded compatibility, relation-preserving
  transformations, composition-preserving re-ranking이 각각 어떤 failure를
  막는지 1:1로 설명한다.
- Main의 Table~1--3과 M-1--M-3을 먼저 제시하고, supplement의 robust-density,
  component, routing, seed, uncertainty, oracle evidence를 reviewer 질문에
  맞춰 연결한다.
- Independent ground truth가 아니라는 한계를 인정하면서도 feature removal,
  alternative point/mesh measurements, uncertainty policies가 같은 방향을
  보인다는 triangulation을 강조한다.
- Restricted-family Recall은 standard full-ontology benchmark가 아니라 동일
  candidate scope 안의 Source-relative reliability comparison임을 명확히 한다.
- Scientific P0/P1 evidence, I-021/I-022, F-05, F-07--F-10은 닫혔다.
  제출 전 필수 잔여 항목은 F-06 generative-AI role documentation과
  submission-system metadata 확인이다.

최종 판단:

- Soundness와 experimental rigor는 Weak Accept 수준에 가깝다.
- Novelty, significance, external validity는 reviewer 성향에 따라 Weak Reject로
  기울 수 있다.
- 따라서 현재 가장 현실적인 중심 평가는 `Weak Reject`이며, reviewer가 scoped
  reliability task의 중요성과 supplement evidence를 충분히 인정하면
  `Weak Accept`로 이동할 수 있는 borderline paper다.

## 14. Citation 원문 검증

### 14.1 검증 범위와 판정 기준

- Current main의 43개 고유 citation key를 모두 검사했다. Paper가 실제로
  존재하는지, title, author order, venue/year, 그리고 인접 claim을 지원하는지를
  분리해 판정했다.
- 제목, 저자명과 순서, venue, 연도는 공식 proceedings, publisher page, 또는
  versioned arXiv record를 기준으로 판정했다.
- 주장 적합성은 abstract와 필요한 경우 원문 본문에서 해당 citation이 실제로
  앞 문장의 주장을 뒷받침하는지 확인했다.
- 사용자가 제공한 Google Scholar BibTeX URL은 세션에 결합된 서명 URL이라
  외부 세션에서 직접 재다운로드할 수 없었다. 사용자가 확인한 export 값은
  대조 자료로 사용했다. Scholar와 official venue가 충돌하면 CVF, NeurIPS,
  PMLR, AAAI OJS, ACM DOI, RSS proceedings, versioned arXiv를 우선한다.

핵심 결론:

- Fabricated paper는 확인되지 않았다.
- Current source의 43개 citation key는 모두 bibliography에 존재한다.
- Heo는 Google Scholar와 author repository BibTeX를 기준으로
  `heo2026object`, `year={2026}`을 유지한다는 저자 결정을 따른다.
- `fei2026open`의 current `Yuehua, Li`는 AAAI OJS의 `Yuehua, L.` citation
  parsing 및 사용자가 확인한 Scholar export와 일치한다. 이전의
  `Li, Yuehua` 강제 수정 권장은 철회한다.
- TAD metadata는 arXiv v1에 정확히 존재한다. Latest v2는 OAR로 바뀌었지만,
  main 문장이 TAD를 설명하므로 v1을 인용하는 현재 선택은 유효하다.

### 14.2 Citation 이슈 최종 판정

Current main과 supplement가 사용하는 43개 citation key는 모두
`paper/references.bib`에 존재한다. CIT-01--CIT-08은 다음과 같이 정리됐다.

| 이슈 | 상태 | 최종 판정과 반영 |
|---|---|---|
| CIT-01 RelWitness claim | `[x]` | Related Work는 완료된 empirical result를 주장하지 않고 `proposes visual--geometric relation witnesses`로 proposal 범위만 기술함 |
| CIT-02 TAD/OAR version | `[x]` | 실제 참고한 TAD v1의 title과 seven-author entry를 유지하고 `https://arxiv.org/abs/2606.27412v1`을 BibTeX URL로 고정함 |
| CIT-03 Heo year | `[x]` 저자 결정 | Google Scholar와 author repository BibTeX를 기준으로 `heo2026object`, `year={2026}`을 유지하기로 저자가 확정함 |
| CIT-04 `fei2026open` author | `[x]` | Current `Yuehua, Li`가 AAAI OJS citation export 및 저자가 확인한 Scholar export와 일치함 |
| CIT-05 venue와 entry | `[x]` | GEODE는 `Feng_2026_CVPR`, VIZOR는 `Madhavaram_2026_WACV`로 source와 bibliography를 통일함. OpenMask3D, Hydra, HOV-SG, PUF의 선택된 version도 실제 자료를 식별함 |
| CIT-06 title capitalization | `[x]` | AAAI 규정 위반이 아님. 고유 method name과 acronym의 brace 보존은 선택적 reference-quality 정리로만 유지함 |
| CIT-07 OpenScene key | `[x]` | Official CVF BibTeX의 `Peng_2023_CVPR` key와 full author list를 사용함. Citation key 형식은 AAAI 규정 위반이 아님 |
| CIT-08 mapping과 중복 | `[x]` | Predictor별 citation mapping, RankAvg/RRF 분리, citation spacing, alignment 설명 중복이 모두 정리됨 |

`geifman2017selective`는 current main, supplement, bibliography에서 삭제됐다.
NeurIPS entry type, optional DOI, PMLR extra fields처럼 reference를 정확히
식별하는 데 지장이 없는 선택적 정리는 별도 이슈로 세지 않는다.

### 14.3 43개 citation key별 원문 대조

상태에서 `[x]`는 현재 claim과 핵심 metadata가 맞음을 뜻한다. `[~]`는 claim은
맞지만 wording 또는 author completeness의 보완을 권장함을 뜻한다. `[ ]`는
제출 전 수정이 필요한 key/metadata 오류다.

| 판정 | Key | 공식 title, author order, venue/year | 현재 claim support |
|---|---|---|---|
| `[x]` | `cormack2009reciprocal` | *Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods*. Gordon V. Cormack, Charles L. A. Clarke, Stefan Büttcher. ACM SIGIR 2009. [DOI](https://doi.org/10.1145/1571941.1572114) | RRF가 rankings를 결합한다는 Baseline 설명을 직접 지원함 |
| `[x]` | `armeni20193d` | *3D Scene Graph: A Structure for Unified Semantics, 3D Space, and Camera*. Iro Armeni, Zhi-Yang He, JunYoung Gwak, Amir R. Zamir, Martin Fischer, Jitendra Malik, Silvio Savarese. ICCV 2019. [CVF](https://openaccess.thecvf.com/content_ICCV_2019/html/Armeni_3D_Scene_Graph_A_Structure_for_Unified_Semantics_3D_Space_ICCV_2019_paper.html) | 3D scene graph의 structured representation 정의를 직접 지원 |
| `[x]` | `chen2024clip` | *CLIP-Driven Open-Vocabulary 3D Scene Graph Generation via Cross-Modality Contrastive Learning*. Lianggangxu Chen, Xuejiao Wang, Jiale Lu, Shaohui Lin, Changbo Wang, Gaoqi He. CVPR 2024. [CVF](https://openaccess.thecvf.com/content/CVPR2024/html/Chen_CLIP-Driven_Open-Vocabulary_3D_Scene_Graph_Generation_via_Cross-Modality_Contrastive_Learning_CVPR_2024_paper.html) | Multimodal/open-vocabulary relation generation을 지원 |
| `[x]` | `chen2026beyond` | *Beyond Isolated Objects: Relationship-aware Open Vocabulary Scene Understanding via 3D Scene Graph Analysis*. Xianhao Chen, Jiarui Hu, Yuanbo Yang, Xiyu Zhang, Tengyue Wang, Hujun Bao, Guofeng Zhang, Zhaopeng Cui. arXiv 2026. [arXiv](https://arxiv.org/abs/2607.05348) | RelGraphOV의 relation-aware graph construction과 geometric pruning 설명을 직접 지원 |
| `[x]` | `fei2026open` | *Open-World 3D Scene Graph Generation for Retrieval-Augmented Reasoning*. Yu Fei, Quan Deng, Shengeng Tang, Li Yuehua, Lechao Cheng. AAAI 2026. [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/37391) | Retrieval, grounding, reasoning, planning downstream claim을 지원함. Current author parsing은 OJS citation export와 일치 |
| `[x]` | `feng20233d` | *3D Spatial Multimodal Knowledge Accumulation for Scene Graph Prediction in Point Cloud*. Mingtao Feng, Haoran Hou, Liang Zhang, Zijie Wu, Yulan Guo, Ajmal Mian. CVPR 2023. [CVF](https://openaccess.thecvf.com/content/CVPR2023/html/Feng_3D_Spatial_Multimodal_Knowledge_Accumulation_for_Scene_Graph_Prediction_in_CVPR_2023_paper.html) | Spatial knowledge와 multimodal cues claim을 직접 지원 |
| `[x]` | `Feng_2026_CVPR` | *GEODE: Geometry-Guided Discrete Diffusion for Open-Vocabulary 3D Scene Graph Generation*. Changqun Feng, Wangxiandi Yin, Xin Hu, Lei Zhao, Dongyang Zhang, Tao He. CVPR 2026 Findings. [CVF](https://openaccess.thecvf.com/content/CVPR2026F/html/Feng_GEODE_Geometry-Guided_Discrete_Diffusion_for_Open-Vocabulary_3D_Scene_Graph_Generation_CVPRF_2026_paper.html) | Geometry와 predicate를 joint denoising한다는 claim을 지원. Current source와 bibliography key 및 metadata가 일치 |
| `[x]` | `gu2024conceptgraphs` | *ConceptGraphs: Open-Vocabulary 3D Scene Graphs for Perception and Planning*. Qiao Gu, Alihusein Kuwajerwala, Sacha Morin, Krishna Murthy Jatavallabhula, Bipasha Sen, Aditya Agarwal, Corban Rivera, William Paul, Kirsty Ellis, Rama Chellappa, Chuang Gan, Celso Miguel de Melo, Joshua B. Tenenbaum, Antonio Torralba, Florian Shkurti, Liam Paull. ICRA 2024. [Project](https://concept-graphs.github.io/) | Querying/planning claim을 직접 지원함. Current abbreviated BibTeX는 official project export와 동일 |
| `[x]` | `guo2017calibration` | *On Calibration of Modern Neural Networks*. Chuan Guo, Geoff Pleiss, Yu Sun, Kilian Q. Weinberger. ICML 2017, PMLR 70. [PMLR](https://proceedings.mlr.press/v70/guo17a.html) | Miscalibration과 temperature scaling claim을 직접 지원 |
| `[x]` | `heo2026object` | *Object-Centric Representation Learning for Enhanced 3D Semantic Scene Graph Prediction*. KunHo Heo, GiHyun Kim, SuYeon Kim, MyeongAh Cho. NeurIPS volume 38, selected year 2026. [Author repository](https://github.com/VisualScienceLab-KHU/OCRL-3DSSG-Codes) | Object-centric feature claim을 지원함. Google Scholar와 author repository BibTeX에 따라 2026을 유지하기로 저자가 확정 |
| `[x]` | `hou2025fross` | *FROSS: Faster-than-Real-Time Online 3D Semantic Scene Graph Generation from RGB-D Images*. Hao-Yu Hou, Chun-Yi Lee, Motoharu Sonogashira, Yasutomo Kawanishi. ICCV 2025. [CVF](https://openaccess.thecvf.com/content/ICCV2025/papers/Hou_FROSS_Faster-Than-Real-Time_Online_3D_Semantic_Scene_Graph_Generation_from_RGB-D_ICCV_2025_paper.pdf) | Online generation claim을 직접 지원 |
| `[x]` | `huang2025fireplace` | *FirePlace: Geometric Refinements of LLM Common Sense Reasoning for 3D Object Placement*. Ian Huang, Yanan Bao, Karen Truong, Howard Zhou, Cordelia Schmid, Leonidas Guibas, Alireza Fathi. CVPR 2025. [CVF](https://openaccess.thecvf.com/content/CVPR2025/html/Huang_FirePlace_Geometric_Refinements_of_LLM_Common_Sense_Reasoning_for_3D_CVPR_2025_paper.html) | Adjacent geometry-aware object placement work라는 current wording을 직접 지원 |
| `[x]` | `hughes2022hydra` | *Hydra: A Real-time Spatial Perception System for 3D Scene Graph Construction and Optimization*. Nathan Hughes, Yun Chang, Luca Carlone. RSS 2022. [RSS](https://www.roboticsproceedings.org/rss18/p050.pdf) | Online persistent graph construction을 직접 지원함. Current arXiv entry도 실제 version을 정확히 식별 |
| `[x]` | `koch2024open3dsg` | *Open3DSG: Open-Vocabulary 3D Scene Graphs from Point Clouds with Queryable Objects and Open-Set Relationships*. Sebastian Koch, Narunas Vaskevicius, Mirco Colosi, Pedro Hermosilla, Timo Ropinski. CVPR 2024. [CVF](https://openaccess.thecvf.com/content/CVPR2024/html/Koch_Open3DSG_Open-Vocabulary_3D_Scene_Graphs_from_Point_Clouds_with_Queryable_CVPR_2024_paper.html) | Open-vocabulary source와 Figure 1 source attribution을 직접 지원 |
| `[x]` | `koch2024sgrec3d` | *SGRec3D: Self-Supervised 3D Scene Graph Learning via Object-Level Scene Reconstruction*. Sebastian Koch, Pedro Hermosilla, Narunas Vaskevicius, Mirco Colosi, Timo Ropinski. WACV 2024. [CVF](https://openaccess.thecvf.com/content/WACV2024/html/Koch_SGRec3D_Self-Supervised_3D_Scene_Graph_Learning_via_Object-Level_Scene_Reconstruction_WACV_2024_paper.html) | Self-supervised pretraining claim을 직접 지원 |
| `[x]` | `lakshminarayanan2017simple` | *Simple and Scalable Predictive Uncertainty Estimation Using Deep Ensembles*. Balaji Lakshminarayanan, Alexander Pritzel, Charles Blundell. NeurIPS 2017. [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2017/hash/9ef2ed4b7fd2c810847ffa5fa85bce38-Abstract.html) | Deep ensembles uncertainty claim을 직접 지원함 |
| `[x]` | `liu2026view` | *View-on-Graph: Zero-Shot 3D Visual Grounding via Vision-Language Reasoning on Scene Graphs*. Yuanyuan Liu, Haiyang Mei, Dongyang Zhan, Jiayue Zhao, Dongsheng Zhou, Bo Dong, Xin Yang. AAAI 2026. [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/37677) | Scene-graph-based visual grounding claim을 직접 지원 |
| `[x]` | `ma2026edge` | *Edge-Centric Relational Reasoning for 3D Scene Graph Prediction*. Yanni Ma, Hao Liu, Yulan Guo, Theo Gevers, Martin R. Oswald. AAAI 2026. [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/37728) | Edge-centric representations/reasoning claim을 직접 지원 |
| `[x]` | `Madhavaram_2026_WACV` | *VIZOR: Viewpoint-Invariant Zero-Shot Scene Graph Generation for 3D Scene Reasoning*. Vivek Madhavaram, Vartika Sengar, Arkadipta De, Charu Sharma. WACV 2026. [CVF](https://openaccess.thecvf.com/content/WACV2026/html/Madhavaram_VIZOR_Viewpoint-Invariant_Zero-Shot_Scene_Graph_Generation_for_3D_Scene_Reasoning_WACV_2026_paper.html) | Downstream object grounding과 viewpoint-aware reasoning claim을 지원하며 current source와 bibliography key가 일치 |
| `[x]` | `maggio2024clio` | *Clio: Real-Time Task-Driven Open-Set 3D Scene Graphs*. Dominic Maggio, Yun Chang, Nathan Hughes, Matthew Trang, Dan Griffith, Carlyn Dougherty, Eric Cristofalo, Lukas Schmid, Luca Carlone. IEEE RA-L 2024. [arXiv](https://arxiv.org/abs/2404.13696) | Task-driven querying/interaction과 online graph construction을 지원 |
| `[x]` | `nag2025conformal` | *Conformal Prediction and MLLM Aided Uncertainty Quantification in Scene Graph Generation*. Sayak Nag, Udita Ghosh, Calvin-Khang Ta, Sarosij Bose, Jiachen Li, Amit K. Roy-Chowdhury. CVPR 2025. [CVF](https://openaccess.thecvf.com/content/CVPR2025/html/Nag_Conformal_Prediction_and_MLLM_aided_Uncertainty_Quantification_in_Scene_Graph_CVPR_2025_paper.html) | Conformal prediction-set claim을 직접 지원 |
| `[x]` | `neau2026visual` | *Visual Commonsense Driven Knowledge Refinements for Scene Graph Generation*. Maëlic Neau, Salim Baloch, Jakob Suchan, Zoe Falomir, Mehul Bhatt. arXiv 2026. [arXiv](https://arxiv.org/abs/2606.06369) | 2D fixed-prediction declarative refinement라는 current comparison을 직접 지원 |
| `[x]` | `nguyen2026relwitness` | *RelWitness: Open-Vocabulary 3D Scene Graph Generation with Visual-Geometric Relation Witnesses*. Minh Anh Nguyen, Quang Huy Tran, Bao Ngoc Le, Tuan Kiet Pham, Sui Yang Guang. arXiv 2026. [arXiv](https://arxiv.org/abs/2605.20823) | Method proposal 범위만 기술하도록 current prose가 `proposes`를 사용함 |
| `[x]` | `Ovadia2019CanYT` | *Can You Trust Your Model's Uncertainty? Evaluating Predictive Uncertainty Under Dataset Shift*. Yaniv Ovadia, Emily Fertig, Jie Jessie Ren, Zachary Nado, D. Sculley, Sebastian Nowozin, Joshua V. Dillon, Balaji Lakshminarayanan, Jasper Snoek. NeurIPS 2019. [Semantic Scholar](https://www.semanticscholar.org/paper/Can-You-Trust-Your-Model's-Uncertainty-Evaluating-Ovadia-Fertig/1eb7f46b1a0a7df823194d86543e5554aa21021a) | Distribution-shift uncertainty evaluation claim을 직접 지원하며 current source와 selected Semantic Scholar BibTeX key가 일치 |
| `[x]` | `Peng_2023_CVPR` | *OpenScene: 3D Scene Understanding With Open Vocabularies*. Songyou Peng, Kyle Genova, Chiyu “Max” Jiang, Andrea Tagliasacchi, Marc Pollefeys, Thomas Funkhouser. CVPR 2023. [CVF](https://openaccess.thecvf.com/content/CVPR2023/html/Peng_OpenScene_3D_Scene_Understanding_With_Open_Vocabularies_CVPR_2023_paper.html) | Queryable point/region feature claim을 직접 지원함. Current key와 full author list가 official CVF BibTeX와 일치 |
| `[x]` | `sarkar2023sgaligner` | *SGAligner: 3D Scene Alignment with Scene Graphs*. Sayan Deb Sarkar, Ondrej Miksik, Marc Pollefeys, Daniel Barath, Iro Armeni. ICCV 2023. [CVF](https://openaccess.thecvf.com/content/ICCV2023/html/Sarkar_SGAligner_3D_Scene_Alignment_with_Scene_Graphs_ICCV_2023_paper.html) | Scene graph alignment과 downstream registration claim을 직접 지원 |
| `[x]` | `saxena2025zing` | *ZING-3D: Zero-Shot Incremental 3D Scene Graphs via Vision-Language Models*. Pranav Saxena, Jimmy Chiun. arXiv 2025. [arXiv](https://arxiv.org/abs/2510.21069) | Incremental, geometrically grounded, embodied-use framing을 지원 |
| `[x]` | `shao2025great` | *GREAT: Geometry-Intention Collaborative Inference for Open-Vocabulary 3D Object Affordance Grounding*. Yawen Shao, Wei Zhai, Yuhang Yang, Hongchen Luo, Yang Cao, Zheng-Jun Zha. CVPR 2025. [CVF](https://openaccess.thecvf.com/content/CVPR2025/html/Shao_GREAT_Geometry-Intention_Collaborative_Inference_for_Open-Vocabulary_3D_Object_Affordance_Grounding_CVPR_2025_paper.html) | Adjacent geometry-aware affordance grounding work라는 current wording을 직접 지원 |
| `[x]` | `sun2026not` | *Not All Relations Rotate Alike: Transformation-Aware Decoupling for Viewpoint-Robust 3D Scene Graph Generation*. Jingjun Sun, Chaowei Wang, Zhirui Liu, Jiaxu Tian, Ming Yang, Yaoxing Wang, Shan Gao. arXiv 2026 v1. [arXiv v1](https://arxiv.org/abs/2606.27412v1) | TAD와 viewpoint-robustness description을 정확히 지원하며 BibTeX가 v1 URL을 명시함 |
| `[x]` | `takmaz2023openmask3d` | *OpenMask3D: Open-Vocabulary 3D Instance Segmentation*. Ayça Takmaz, Elisabetta Fedele, Robert W. Sumner, Marc Pollefeys, Federico Tombari, Francis Engelmann. NeurIPS 2023. [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2023/hash/d77b5482e38339a8068791d939126be2-Abstract-Conference.html) | Queryable instance features claim을 직접 지원함. Current arXiv entry도 동일 paper를 정확히 식별 |
| `[x]` | `wald2019rio` | *RIO: 3D Object Instance Re-Localization in Changing Indoor Environments*. Johanna Wald, Armen Avetisyan, Nassir Navab, Federico Tombari, Matthias Nießner. ICCV 2019. [CVF](https://openaccess.thecvf.com/content_ICCV_2019/html/Wald_RIO_3D_Object_Instance_Re-Localization_in_Changing_Indoor_Environments_ICCV_2019_paper.html) | Repeated indoor reconstruction and 3RScan claim을 직접 지원 |
| `[x]` | `wald2020learning` | *Learning 3D Semantic Scene Graphs From 3D Indoor Reconstructions*. Johanna Wald, Helisa Dhamo, Nassir Navab, Federico Tombari. CVPR 2020. [CVF](https://openaccess.thecvf.com/content_CVPR_2020/html/Wald_Learning_3D_Semantic_Scene_Graphs_From_3D_Indoor_Reconstructions_CVPR_2020_paper.html) | 3DSSG annotations, benchmark, shared target claim을 직접 지원 |
| `[x]` | `wang2023vl` | *VL-SAT: Visual-Linguistic Semantics Assisted Training for 3D Semantic Scene Graph Prediction in Point Cloud*. Ziqin Wang, Bowen Cheng, Lichen Zhao, Dong Xu, Yang Tang, Lu Sheng. CVPR 2023. [CVF](https://openaccess.thecvf.com/content/CVPR2023/html/Wang_VL-SAT_Visual-Linguistic_Semantics_Assisted_Training_for_3D_Semantic_Scene_Graph_CVPR_2023_paper.html) | VL-SAT source와 visual-linguistic cue claim을 직접 지원 |
| `[x]` | `wang2025open` | *Open-Vocabulary Octree-Graph for 3D Scene Understanding*. Zhigang Wang, Yifei Su, Chenhui Li, Dong Wang, Yan Huang, Xuelong Li, Bin Zhao. ICCV 2025. [CVF](https://openaccess.thecvf.com/content/ICCV2025/html/Wang_Open-Vocabulary_Octree-Graph_for_3D_Scene_Understanding_ICCV_2025_paper.html) | Open-vocabulary graph representation, spatial relation, downstream retrieval/planning claim을 지원 |
| `[x]` | `werby2024hierarchical` | *Hierarchical Open-Vocabulary 3D Scene Graphs for Language-Grounded Robot Navigation*. Abdelrhman Werby, Chenguang Huang, Martin Büchner, Abhinav Valada, Wolfram Burgard. RSS 2024. [RSS](https://www.roboticsproceedings.org/rss20/p077.pdf) | Language-grounded navigation claim을 직접 지원함. Current workshop entry도 실제 version을 정확히 식별 |
| `[x]` | `wu2021scenegraphfusion` | *SceneGraphFusion: Incremental 3D Scene Graph Prediction From RGB-D Sequences*. Shun-Cheng Wu, Johanna Wald, Keisuke Tateno, Nassir Navab, Federico Tombari. CVPR 2021. [CVF](https://openaccess.thecvf.com/content/CVPR2021/html/Wu_SceneGraphFusion_Incremental_3D_Scene_Graph_Prediction_From_RGB-D_Sequences_CVPR_2021_paper.html) | Incremental system과 SGFN source attribution을 직접 지원 |
| `[x]` | `xie2024sg` | *SG-PGM: Partial Graph Matching Network with Semantic Geometric Fusion for 3D Scene Graph Alignment and Its Downstream Tasks*. Yaxu Xie, Alain Pagani, Didier Stricker. CVPR 2024. [CVF](https://openaccess.thecvf.com/content/CVPR2024/papers/Xie_SG-PGM_Partial_Graph_Matching_Network_with_Semantic_Geometric_Fusion_for_CVPR_2024_paper.pdf) | Semantic-geometric alignment과 downstream geometric tasks claim을 직접 지원 |
| `[x]` | `yang2021probabilistic` | *Probabilistic Modeling of Semantic Ambiguity for Scene Graph Generation*. Gengcong Yang, Jingyi Zhang, Yong Zhang, Baoyuan Wu, Yujiu Yang. CVPR 2021. [CVF](https://openaccess.thecvf.com/content/CVPR2021/html/Yang_Probabilistic_Modeling_of_Semantic_Ambiguity_for_Scene_Graph_Generation_CVPR_2021_paper.html) | Semantic ambiguity와 probabilistic modeling claim을 직접 지원 |
| `[x]` | `yang2026puf` | *PUF: Plug-and-Play Uncertainty-Aware Fusion for Online 3D Scene Graph Generation*. Yi Yang, Myrna Castillo, Bodo Rosenhahn, Michael Ying Yang. arXiv 2026, accepted ECCV 2026. [arXiv](https://arxiv.org/abs/2607.07170) | Association and incremental fusion uncertainty claim을 직접 지원 |
| `[x]` | `yeo2025statistical` | *Statistical Confidence Rescoring for Robust 3D Scene Graph Generation from Multi-View Images*. Qi Xun Yeo, Yanyan Li, Gim Hee Lee. ICCV 2025. [CVF](https://openaccess.thecvf.com/content/ICCV2025/html/Yeo_Statistical_Confidence_Rescoring_for_Robust_3D_Scene_Graph_Generation_from_ICCV_2025_paper.html) | Masks, neighboring relations, statistical priors rescoring claim을 직접 지원 |
| `[x]` | `zhang2021exploiting` | *Exploiting Edge-Oriented Reasoning for 3D Point-Based Scene Graph Analysis*. Chaoyi Zhang, Jianhui Yu, Yang Song, Weidong Cai. CVPR 2021. [CVF](https://openaccess.thecvf.com/content/CVPR2021/html/Zhang_Exploiting_Edge-Oriented_Reasoning_for_3D_Point-Based_Scene_Graph_Analysis_CVPR_2021_paper.html) | Edge reasoning과 point-cloud relation prediction claim을 직접 지원 |
| `[x]` | `zhang2025open` | *Open-Vocabulary Functional 3D Scene Graphs for Real-World Indoor Spaces*. Chenyangguang Zhang, Alexandros Delitzas, Fangjinhua Wang, Ruida Zhang, Xiangyang Ji, Marc Pollefeys, Francis Engelmann. CVPR 2025. [CVF](https://openaccess.thecvf.com/content/CVPR2025/html/Zhang_Open-Vocabulary_Functional_3D_Scene_Graphs_for_Real-World_Indoor_Spaces_CVPR_2025_paper.html) | Functional relations and downstream reasoning/manipulation claim을 직접 지원 |
| `[x]` | `zhu2024calibration` | *Calibration for Long-Tailed Scene Graph Generation*. Xuhan Zhu, Yifei Xing, Ruiping Wang, Yaowei Wang, Xiangyuan Lan. ACM MM 2024. [OpenReview](https://openreview.net/forum?id=jGNDRM2vul) | Long-tailed SGG calibration claim을 직접 지원함 |

### 14.4 여러 논문 동시 인용의 분리 권장 위치

모든 multi-citation을 기계적으로 분리할 필요는 없다. 여러 논문이 정확히 같은
일반 주장 하나를 공동으로 뒷받침하면 group citation이 자연스럽다. 반대로 한 문장에
서로 다른 task, method property, venue status가 나열되면 citation을 해당 명사구
직후로 옮기는 편이 명확하다.

이 기준은 current source에 반영됐다. Method line 7은 세 predictor와 score
type의 citation을 one-to-one으로 연결한다. Experiments line 9는 RankAvg와
RRF 정의를 분리한다. Related Work line 14는 citation spacing을 정리했다.
Introduction의 downstream-use group, Related Work의 category-level group
citations, Reliability subsection의 task별 citations은 같은 일반 주장을
공동으로 뒷받침하므로 추가 분리가 필요하지 않다.

### 14.5 Citation 반영 후 검증 결과

| 검증 | 상태 | 결과 |
|---|---|---|
| Clean build | `[x]` | Main, supplement, checklist가 각각 9, 10, 2 pages로 빌드됨 |
| BibTeX와 reference | `[x]` | Main `.blg` warning 0, undefined citation/reference 0 |
| Page boundary | `[x]` | Main Figure 1--3과 Table 1--3은 pages 1--7에 있고 pages 8--9는 references only |
| PDF 형식과 fonts | `[x]` | 세 PDF 모두 US Letter, PDF 1.5이며 Type 3, CID/Identity, unembedded font가 없음 |
| Known layout warning | `[x]` | Main, supplement, checklist의 final log에 overfull box가 없음 |
| Caption/table typography | `[x]` | Manual-bold captions와 7-point supplement table text를 제거함 |
| Canonical synchronization | `[x]` | 최종 source와 9/10/2-page canonical PDFs 및 `20260728_214915` release의 hashes가 일치함 |
| Release integrity | `[x]` | Outer manifest 6 files와 ZIP 내부 manifest 211 entries가 통과했고 ZIP 212 files의 압축 무결성을 확인함 |
| Extracted-source rebuild | `[x]` | 최신 ZIP source에서 main, supplement, checklist를 9/10/2 pages로 재빌드했고 release PDFs와 추출 text가 일치함 |

최종 upload candidate는
`release/relcompat3d_aaai27_openreview_20260728_214915/`이다. SHA-256은
main `f0a3c6ab9810e58eb7e1cab6f61989eac6f4fcedca7b00ae68e2a6e001cc8cdf`,
supplement `2785ba776d587fb9d38fba2cc652dfe6a99359470a2824c436229da5c687d760`,
checklist `f712082e0709572f82be637bd962bf438580d3145ce60d7c7650bb38a5611939`,
code/data ZIP
`cf678a127381d6bc686f82dfa7ed1d58bcd99819e8b35c04eddf914ec39e91ff`다.

## 15. F31--F34 최종 읽기 점검

검토 기준은 current `main.tex`와 최신 9-page clean test PDF다. Caption은 그림이나
표가 무엇을 보여주는지 설명해야 하고, 본문은 그 결과의 의미와 claim 연결을
담아야 한다. 이 구분을 기준으로 각 항목을 직접 읽고 PDF 배치까지 확인했다.

### 15.1 F31. Figure와 Table caption의 자기완결성

| 대상 | 판정 | 점검 결과 |
|---|---|---|
| Figure 1 | `[x]` | Open3DSG의 source relation, point-cloud evidence, Source와 RelCompat3D-Linear의 rank, top-50 membership 변화를 모두 설명한다. Orange와 blue는 object name에 직접 대응하므로 별도 color legend가 필요하지 않다. |
| Figure 2 | `[x]` | (a)와 (b)의 역할, ordered-pair distance, compatibility inputs, source-score exclusion, within-family scoring, rank 변화를 설명한다. \(T\), \(G\), \(Z\)는 그림 내부에서 각각 predicate semantics, pair measurements, predictor score로 풀어 쓰여 있다. |
| Figure 3 | `[x]` | Shared 3DSSG validation scenes, metric, \(K\), 세 ranking, 선호 방향, increasing-\(K\) 순서, 서로 다른 axis range를 설명한다. Legend가 color와 marker를 정의한다. |
| Table 1 | `[x]` | Dataset, Recall과 Violation, 단위, Source baseline, bold 범위, Product의 다른 scope를 모두 설명한다. Row와 column만으로도 predictor, ranking rule, \(K\)를 식별할 수 있다. |
| Table 2 | `[x]` | Shared 3DSSG validation scenes, Linear controls, MLP reference rows, R/V 방향, 단위, matched candidate/routing 조건이 모두 설명된다. Header가 `R@50`, `V@50` 약어를 사용하므로 caption에서 R과 V를 다시 정의하는 것은 불필요한 반복이 아니라 standalone table을 위한 local definition이다. Metric formula까지 반복할 필요는 없다. |
| Table 3 | `[x]` | Shared 3DSSG validation scenes, \(K=50\), point/mesh agreement와 uncertainty rule, Source/Linear, \(\Delta V\), measured/decidable coverage를 직접 설명한다. 각 열의 의미와 단위가 caption만으로 복원된다. |

Main의 여섯 caption은 모두 자기완결적이다. Caption은 표시 대상과 표기법을
설명하고, 결과의 해석은 본문에 남겨 역할도 적절히 분리된다.

### 15.2 F32. 본문 대응, 해석, 참조와 PDF 배치

모든 main Figure와 Table은 본문에서 명시적으로 참조된다. 첫 참조와 실제
배치의 거리는 다음과 같다.

| 대상 | 본문 최초 참조 | PDF 배치 | 판정 |
|---|---:|---:|---|
| Figure 1 | page 1 | page 1 | `[x]` |
| Figure 2 | page 3 | page 4 | `[x]` |
| Table 1 | page 5 | page 6 | `[x]` |
| Figure 3 | page 5 | page 6 | `[x]` |
| Table 2 | page 6 | page 7 | `[x]` |
| Table 3 | page 7 | page 7 | `[x]` |

한 페이지를 넘는 간격이 없고, technical content의 읽기 흐름 안에서 모두
가까이 배치되어 있다.

- `[x]` **Table 1과 Figure 3:** Caption은 표시 대상과 읽는 방법을 설명한다.
  Results는 all-\(K\) 방향, bootstrap interval, SGFN tie, Open3DSG 변화,
  method 간 trade-off를 해석하므로 caption을 반복하지 않는다.
- `[x]` **Table 2:** Caption은 control 구성과 표기법을 설명한다. 본문은
  wrong-pair, shuffled geometry, wrong predicate, distance-only,
  compatibility-only가 어떤 설계 주장을 검증하는지 연결한다.
- `[x]` **Table 3:** Caption은 audit label과 열을 설명한다. 본문은 OBB overlap을
  피한 이유, alternative measurement의 범위, all-\(K\) supplement 결과와
  Recall 불변성을 해석한다.
- `[x]` **Figures 1과 2의 qualitative paragraph:** 본문은 두 caption의 rank와
  distance를 반복하지 않고, vertical-order와 proximity에서 일관되지 않은
  candidate를 demote한다는 해석과 supplement promotion 사례의 역할을 연결한다.

### 15.3 F33. 처음부터 끝까지의 유기적 연결

- `[x]` **Abstract:** semantically plausible but geometrically inconsistent
  relation이라는 문제에서 시작해 source-score-excluded compatibility,
  family-aware re-ranking, Recall/Violation 결과, alternative audit로 끝난다.
- `[x]` **Introduction:** downstream need, observed failure, existing geometry
  use, source-score separation, estimator와 transformation, routing,
  evaluation, contributions 순서가 자연스럽다.
- `[x]` **Related Work:** relation generation, geometry-aware evidence,
  reliability/calibration의 세 축에서 fixed-candidate post-hoc compatibility와의
  차이를 설명한다.
- `[x]` **Method:** ordered-pair identity와 \(T,G,Z\)를 정의한 뒤 estimator,
  training, transformation averaging, family-aware re-ranking 순서로
  Introduction의 설계 선택을 구현한다.
- `[x]` **Experiments:** shared evaluation scope와 metric을 먼저 고정하고,
  main trade-off, score/routing sensitivity, qualitative cases, structural
  controls, alternative audit 순서로 각 claim을 검증한다.
- `[x]` **Discussion과 Conclusion:** single-split scope와 independent-ground-truth
  한계를 유지하면서 motivating problem과 scoped result로 돌아온다. 앞선
  claim을 뒤집거나 새로운 결과를 추가하지 않는다.
- `[x]` **표현과 문장 패턴의 반복:** Main에서 `We propose`, `We evaluate`,
  `The supplement reports` 같은 기능적 표현은 필요한 위치에만 나타난다.
  Related Work의 비교 문장도 subsection별 연구군을 정리하는 역할이 달라
  과도한 template 반복으로 읽히지 않는다. Supplement의 `Table ... reports`와
  `At \(K\)` 패턴은 많은 추가 결과를 안내하는 데 필요한 수준이다.
- `[x]` **문장 길이와 리듬:** Abstract와 Introduction은 짧은 claim 문장과
  중간 길이의 설명 문장을 섞고, Method는 정의와 수식 사이에 짧은 해설을 둔다.
  Results도 수치 문장 뒤에 해석 문장을 배치한다. 한 길이의 문장만 이어지는
  단조로운 구간이나 여러 독립 논거가 한 문장에 몰린 구간은 없다.

전체 manuscript는 하나의 흐름으로 읽히며 섹션 사이의 claim, terminology,
hedging에 충돌이 없다.

### 15.4 F34. 기억에 남을 핵심 포인트

현재 manuscript의 핵심 메시지는 다음 한 문장으로 정리된다.

> A source relation score is not an explicit estimate of same-pair
> predicate--geometry compatibility.

`Geometry may inform a predictor without making its source relation score ...`
문장이 Introduction에 반영됐다. 이 메시지는 score-excluded compatibility,
same-pair controls, family-aware re-ranking, Recall--Violation evaluation,
Conclusion까지 동일하게 이어진다. F34는 `[x]`로 완료다.

## 16. 최종 언어 교정

Main, supplement, reproducibility checklist를 source와 clean-build PDF에서 다시
읽었다. Ordinary-English spelling, adjacent duplicate words, subject--verb
agreement, article omission, comma splice, 접속사 오용을 점검했다.

### 16.1 전체 판정

- `[x]` **오타와 중복 단어:** 기술명, dataset명, 수식 기호를 제외한 명백한
  spelling error와 adjacent duplicate word가 없다.
- `[x]` **관사와 수 일치:** Claim의 의미를 바꾸는 관사 누락이나
  subject--verb agreement 오류가 없다.
- `[x]` **Comma splice와 문장 연결:** 독립절을 comma만으로 연결한 문장이 없고,
  `while`, `whereas`, `because`, `so`의 논리 관계도 적절하다.
- `[x]` **문장 리듬:** Main은 짧은 claim과 중간 길이 설명을 섞는다.
  Supplement는 결과 안내 문장이 반복되지만 table-heavy 문서에서 필요한
  수준이며 읽기 흐름을 방해하지 않는다.
- `[x]` **Reproducibility checklist:** 질문 문구와 Instructions는 official
  template이므로 수정하지 않는다. 저자가 입력한 `yes`, `partial`, `no`, `NA`
  답은 current main, supplement, conservative code/data release 범위와
  일치한다. Theoretical Contributions의 parent가 `no`이므로 `If yes` 아래
  문항을 비워 둔 현재 형식도 template 구조에 맞다.

### 16.2 제출 전 권장 교정

아래 항목은 claim이나 수치를 바꾸지 않는 final copy-edit다. 요청된 교정은
반영했으며 L-02는 저자 의도에 따라 현재 표현을 유지한다.

| 이슈 | 위치와 원문 | 권장 문장 | 판정 |
|---|---|---|---|
| L-01 | Experiments, Datasets and Evaluation: `We evaluate all three on the 3DSSG/3RScan scene` | `We evaluate all three on the 3DSSG validation split of 3RScan` | `[x]` 반영 완료 |
| L-02 | Figure 1 caption: `ranks ... at 6`와 `moves it to 425` | `ranks ... at rank 6`와 `moves it to rank 425` | `[x, 저자 결정]` 바깥 순위로 이동시킨다는 동작을 강조하기 위해 현재 `moves it to 425`를 유지 |
| L-03 | Method, Problem Formulation: `Without predictor-specific normalization or refitting, candidates are ranked separately for each predictor` | `We rank candidates separately for each predictor without predictor-specific normalization or refitting` | `[x]` 반영 완료 |
| L-04 | Results: `lower verifier-derived  Violation` | 두 공백을 하나로 정리 | `[x]` 반영 완료 |
| L-05 | Supplement, Open3DSG: `An eligible-context sensitivity analysis contains 3,899 relations.` | `An eligible-context sensitivity analysis uses 3,899 relations.` | `[x]` 반영 완료 |
| L-06 | Supplement, Target Construction: `At most two negatives are generated per positive, 200 per context--family, and three times the number of positives per family.` | `We cap negatives at two per positive, 200 per context--family, and three times the number of positives per family.` | `[x]` 반영 완료 |
| L-07 | Supplement, Row-Level Regeneration Check: `with zero maximum absolute error at tolerance \(10^{-12}\)` | `The completed run checks 291 cells. The maximum absolute error is zero under the \(10^{-12}\) tolerance.` | `[x]` 반영 완료 |
| L-08 | Supplement, Qualitative Pair Analysis: `The proximity and vertical examples` | `The proximity and vertical-order examples` | `[x]` 반영 완료 |
| L-09 | Supplement, Family Composition: `preserves both its selection and the source family sequence` | `preserves its selected subsequence and the source family-label sequence` | `[x]` 반영 완료 |
| L-10 | Supplement, Verifier-Uncertainty Sensitivity: `includes uncertain candidates in its denominator but does not label them satisfied` | `includes uncertain candidates in its denominator without counting them as violations` | `[선택]` 현재 문장도 status와 numerator 처리를 오해시키지 않으므로 이번 요청 범위에서는 유지 |

이 열 문장 외에는 제출 직전 문체를 다시 흔들 필요가 없다. 특히 Abstract,
Introduction contribution bullets, main result claim, Discussion, Conclusion은
현재 wording을 유지하는 편이 안전하다.
