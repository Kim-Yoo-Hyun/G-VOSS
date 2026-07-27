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
- 검토 범위: 기존 이슈, section별 역할과 문체, section 간 정합성,
  Introduction claim--evidence 연결, main--supplement 정합성, Figure/Table,
  수치와 notation, Author Kit, BibTeX, 제출 artifact, citation 원문 검증
- F-01--F-05 source 수정, citation 정리, clean build, canonical 교체,
  release 재생성과 extracted-source 검증까지 current source 기준으로 완료했다.
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

F-01--F-05의 직전 pass와 citation source 정리는 완료됐다. Current main과
supplement에서 사용하는 43개 citation key는 모두 bibliography에 존재한다.
VIZOR는 `Madhavaram_2026_WACV`, Ovadia는 `Ovadia2019CanYT`로 통일했고,
TAD는 실제 참고한 arXiv v1 URL을 명시했다. Heo는 Google Scholar와 author
repository BibTeX를 기준으로 2026을 유지한다는 저자 결정을 반영했다.
RelWitness는 Related Work에서 proposal 범위로만 기술한다.
Scientific residual risk는 independent validity label 부재와 single-target
범위다. 이는 숨겨진 transcript 오류가 아니라 현재 claim boundary다.

## 2. 통합 이슈 판정

이 절은 기존 이슈 재검토, I-015--I-021 엄격 재판정, Author Kit, BibTeX를
하나로 통합한다. 완료된 항목은 핵심 결론만 남긴다.

### 2.1 최종 source와 artifact 이슈

| 이슈 | 상태 | 최종 결론 |
|---|---|---|
| F-01 Supplement optimizer | `[x]` | Linear는 800-step full-batch gradient descent, MLP는 120-step full-batch Adam으로 active code/protocol과 일치시켰고 obsolete L-BFGS/500-epoch 문장을 삭제함 |
| F-02 score-mapping notation | `[x]` | mapping을 \(g_\gamma,g_\tau\)로 바꾸어 estimator \(q\)와 predicate semantics \(T_i\)의 collision을 제거함 |
| F-03 Supplement Table 호출 | `[x]` | 기존 여섯 Table을 포함해 모든 main/supplement Figure와 Table이 본문에서 최소 한 번 참조됨 |
| F-04 Open3DSG BibTeX title | `[x]` | `queryable objects and open-set relationships`로 수정했고 BibTeX warning 0개를 확인함 |
| F-05 canonical/release synchronization | `[x]` | Current citation source로 main 9쪽, supplement 10쪽, checklist 2쪽을 clean rebuild하고 canonical PDFs와 release bundle을 동기화함 |

Current release:

`release/relcompat3d_aaai27_openreview_20260728_022521/`

| 파일 | 쪽수/내용 | SHA-256 |
|---|---:|---|
| `main.pdf` | 9 pages | `ddaa71272112dfd231745bf8125b9daf22c7a4c65e245583e4f0630b53919d70` |
| `technical_supplement.pdf` | 10 pages | `8c718bb50eea9d8665f0e198661e1fc41213e4323ee3205b7272c9524bf2b5a5` |
| `reproducibility_checklist.pdf` | 2 pages | `d929e8b5dc38e32bc1e92c498ae7d41a7699d37f4aaf80027152117e8f6bb270` |
| `code_and_data_supplement.zip` | 221 archive entries | `a8044cba4fbe7a74a1b897a68050873f753ff65455068cadb04c74403a4da2a6` |

Outer `UPLOAD_MANIFEST.sha256`, ZIP integrity, extracted
`MANIFEST.sha256`, Python compilation, JSON parsing, Docker Compose validation,
US-Letter/PDF 1.5, embedded fonts, anonymity, filename allowlist, 그리고 ZIP
내부 source의 9/10/2-page rebuild가 모두 통과했다.

#### F-06. Generative-AI role disclosure `[저자 확인]`

AAAI-27 call은 generative AI 사용을 허용하지만 저자가 내용에 책임을 지며, AAAI
publication policy는 연구 개발에서 AI system이 맡은 역할의 적절한 기록을 요구한다.
이 프로젝트에서는 AI-assisted writing, review, code organization이 광범위했으므로
`해당 없음`으로 처리하기 어렵다.

권장 처리:

- 제출 시스템에 전용 disclosure field가 있으면 그곳에 사실대로 기록한다.
- 전용 field가 없거나 manuscript statement가 요구되면 anonymity를 깨지 않는 짧은
  role statement를 사용한다.
- 정확한 위치가 불명확하면 AAAI workflow chair의 공식 안내를 확인한다.

이 항목은 기술 내용 수정이 아니라 저자와 venue policy의 최종 확인 사항이다.

#### F-07. Derived-row 재배포 권한 `[저자 확인]`

One-command regeneration은 완료됐지만 derived row bundle은 3RScan/3DSSG
source-derived annotation을 포함할 수 있다. 명시적 재배포 허용을 확인하지 못했다.

권장 처리:

- 허용이 확인되면 bundle과 checksum을 code/data ZIP에 포함한다.
- 허용되지 않으면 licensed inputs에서 bundle을 만드는 deterministic exporter,
  schema, expected manifest만 공개한다.
- 허용 여부가 불명확한 상태에서 row bundle 자체를 배포하지 않는다.

#### F-08. First-page vertical overfull `[보류]`

Current log에는 다음 warning 하나가 남는다.

> Overfull \vbox (36.77646pt too high) has occurred while \output is active

Page 1을 시각적으로 확인한 결과 text, Figure 1, caption은 paper boundary 안에 있고
잘림은 보이지 않는다. 사용자는 Figure 1의 첫 페이지 배치를 유지하기로 결정했다.
따라서 table/figure font, line width, caption을 축소하지 않는다.

최종 처리:

- PDF 업로드 전 Acrobat/브라우저에서 page 1의 실제 clipping과 margin만 다시 본다.
- visible overflow가 없으면 known layout warning으로 유지할 수 있다.
- warning 자체를 반드시 제거하려면 Figure 1의 크기가 아니라 첫 페이지 prose의
  vertical space 또는 float spacing을 Author Kit 허용 범위에서 소폭 조정해야 한다.

### 2.2 기존 I-001--I-021 재판정

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
| I-021 | `[x]` | training-positive construction과 evaluation ground-truth use의 split boundary가 명확함 |

### 2.3 Author Kit와 BibTeX 완료 항목

| 항목 | 상태 | 최종 결론 |
|---|---|---|
| Technical-content page limit | `[x]` | main은 9 pages이며 technical content와 모든 main Figure/Table은 pages 1--7에 있음 |
| References | `[x]` | references는 page 7에서 시작하고 pages 8--9에는 references만 존재함 |
| US Letter / PDF version | `[x]` | current outputs는 US Letter, PDF 1.5 |
| Fonts | `[x]` | Type 3와 CID/Identity fonts가 없고 outlined-v15 Figure inclusion warning도 없음 |
| Figure crop | `[x]` | external outlined figures를 사용하며 `trim`/`clip` 문제 없음 |
| Caption manual bold | `[x]` | Main captions는 수동 bold title을 쓰지 않음. Supplement의 일부 bold 명사구는 금지 사항이 아니며 형식상 유지 가능 |
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

## 3. 전체 문체와 source 체크리스트

| 기준 | 상태 | 판단 |
|---|---|---|
| 용어 통일 | `[x]` | Main과 supplement의 core terms 및 score-mapping notation이 일치함 |
| Easy to read | `[x]` | 문제, estimator, transformation, ranking, evaluation 순서가 명확함 |
| Straightforward | `[x]` | 각 section이 고유 역할을 가지며 main story가 우회하지 않음 |
| 독자 친절성 | `[x]` | \(T,G,Z\), relation family, metrics, Source가 최초 사용 근처에서 설명됨 |
| Good English | `[x]` | 치명적인 문법 오류나 부자연스러운 collocation이 없음 |
| 같은 의미의 용어 혼용 | `[x]` | `source relation score`, `ordered pair`, `family-aware re-ranking`, `verifier-derived Violation`이 일관됨 |
| `A's B` 자제 | `[x]` | active prose에 해당 소유격 패턴이 없음 |
| em dash 남용 | `[x]` | prose에 em dash가 없음 |
| semicolon 남용 | `[x]` | prose에는 없고 feature-vector 수식 구분에만 사용함 |
| 긴 문장 | `[x]` | 즉시 분할해야 할 정도로 서로 다른 논거가 한 문장에 몰리지 않음 |
| Figure/Table 본문 참조 | `[x]` | 모든 main/supplement Figure와 Table이 본문에서 최소 한 번 참조됨 |
| Figure/Table caption | `[x]` | Main captions는 목적, metric, 비교 대상, 방향을 필요한 수준으로 설명함 |
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
  ground-truth relations를 명시한다.
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
- `[x]` **Overclaiming 방지:** `one shared 3DSSG validation target`, `point
  estimates`, `lower or tied`, `preserving or improving`이 evidence의 hedging과
  일치한다.
- `[x]` **중복 관리:** Contribution bullets를 그대로 반복하지 않고 problem
  resolution 중심으로 끝난다.

### Supplement

- `[x]` **구조와 main 정합성:** Notation/preprocessing, construction boundary,
  formal properties, optimization, diagnostics, robustness, audit, controls,
  intervals, transfer, qualitative cases 순서가 main의 story를 확장한다.
- `[x]` **용어와 notation:** Active optimizer 설명과
  \(g_\gamma,g_\tau\) score-mapping notation이 main 및 frozen protocol과
  일치한다.
- `[x]` **Figure/Table 호출:** 모든 supplement Figure와 Table이 본문에서 최소
  한 번 참조된다.
- `[x]` **정보량과 우선순위:** 10쪽과 16 tables는 main claim 방어와 재현성에
  필요한 compact evidence다. Full per-condition rows는 machine-readable
  artifact로 분리했다.
- `[x]` **Main self-containment:** Supplement-only evidence는 sensitivity,
  diagnostic, oracle, provenance이며 core method와 main claim은 supplement
  없이 이해 가능하다.

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
| Main--supplement 수치 | `[x]` | M-1--M-3, audit, intervals, controls가 일치함 |
| Main--supplement scope | `[x]` | Main은 core claim, supplement는 sensitivities와 reproducibility를 담당함 |

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
| Table 3 | Yes | \(K\), agreement label, \(\Delta V\), M/D, units를 설명 | audit prose와 일치 | `[x]` |

Figure 1이 page 1에 있는 것은 문제가 아니다. Qualitative motivation/failure case를
teaser로 두고 Results에서 다시 참조하는 구성은 자연스럽다. Figure 2 caption의
quotation은 relation label을 충분히 구분하며 `\texttt`로 바꿀 필요가 없다.

### 7.2 Supplement

- Figure 1개는 본문에서 호출되고 caption이 subject/object encoding과 outcome을
  설명한다.
- Table captions는 dataset/metric/condition을 대체로 설명한다.
- 모든 Figure와 Table이 본문에서 최소 한 번 호출된다.
- Full tables의 숫자는 main의 compact rows 및 machine-readable outputs와 일치한다.

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

### Major 1. Evaluator와 training construction의 construct dependence `[범위 한계]`

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

남은 rebuttal boundary:

- `independent physical validity`를 주장하지 않고 `verifier-derived reliability on
  a shared target`으로 답한다.
- 더 강한 claim을 하려면 training construction을 보지 않은 별도 annotator protocol,
  independent labels, richer contact/pose evidence가 필요하다.

### Major 2. Single-target external validity와 downstream significance `[범위 한계]`

Risk:

- 세 predictor 비교가 하나의 3DSSG target에 집중된다.
- ReplicaSSG/FROSS는 supplement stress test이며 support/contact ontology를
  포함하지 않는다.
- 실제 downstream task 개선은 보고하지 않는다.

현재 대응:

- Abstract, Discussion, Conclusion을 shared-target claim으로 제한한다.
- Fixed predictor reliability layer로 contribution을 정의한다.
- Supplement에서 transfer와 candidate coverage를 공개한다.

Rebuttal:

- 이 논문의 evidence axis는 dataset 수가 아니라 동일 target에서 predictor가 바뀌어도
  나타나는 score--geometry mismatch라고 설명한다.
- Dataset-level generalization과 embodied downstream utility는 주장하지 않는다.

### Major 3. Novelty가 calibration/post-processing의 결합으로 보일 위험 `[부분 대응]`

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

Rebuttal:

- 단일 component의 우월성이 아니라 세 design constraint가 failure cause에 각각
  대응한다는 구조를 강조한다.
- Pairwise loss를 전체 성능의 유일한 원인으로 주장하지 않는다.

### Major 4. Product score의 scale sensitivity `[대응 완료, scoped]`

현재 대응:

- Fixed monotonic grid에서 Linear 75/75, MLP 74/75 conditions가 Source-relative
  joint direction을 유지한다.
- Percentile stress의 작은 Recall losses와 score-scale invariance가 아님을
  supplement에 공개한다.
- Main은 `Source-relative conclusion remains unchanged ... all but one
  comparison`으로 정확히 요약한다.

남은 원칙: `scale invariant`를 주장하지 않는다.

### Major 5. Family-aware rule의 필요성 `[대응 완료, claim 정정]`

현재 대응:

- Joint P/V matched control은 estimator와 \(K\)에 따라 결과가 달라진다.
- 따라서 family-aware route를 aggregate-optimal이라고 주장하지 않는다.
- Main과 supplement 모두 composition-preserving constraint로 해석한다.

### Major 6. Closest simple baseline 부족 `[대응 완료]`

현재 대응:

- Training-positive robust-density baseline을 동일 candidate pool과 route에서
  평가한다.
- Main은 \(K=50\)에서 두 variants가 세 predictor 모두에서 higher Recall/lower
  Violation임을 한 문장으로 보고한다.
- Hard-tail/Hard-drop은 verifier label을 ranking input으로 쓰는 non-deployable
  diagnostics로 분리한다.

### Major 7. Artifact reproducibility `[조건부 완료]`

현재 대응:

- Derived rows로 Table 1--3과 Figure 3 data를 한 command에서 재생성한다.
- 291 canonical cells를 tolerance \(10^{-12}\)에서 maximum error 0으로 검증한다.
- Docker exporter, reproducer, schema, compact outputs, manifests가 있다.

남은 조건:

- F-07의 derived-row 재배포 권한을 저자가 확인해야 한다.
- Current ZIP은 licensed row bundle을 제외한 deterministic exporter, schema,
  compact outputs, expected manifest를 포함하며 release 검증을 통과했다.

### Minor risk

| 항목 | 상태 | 판단 |
|---|---|---|
| Primary verifier transparency | `[x]` | metric, status, construction overlap, feature removals을 supplement에 공개함 |
| Uncertain denominator | `[x]` | Main에서 uncertain이 denominator에 들어감을 정의하고 alternative policies를 supplement에 둠 |
| Training stochasticity | `[x]` | five-seed Linear/MLP 결과와 한 작은 exception을 supplement에 공개함 |
| Qualitative selection | `[x]` | Main text가 vertical demotion, proximity demotion, proximity promotion을 다루고 supplement에 three-family panel이 있음. Systematic blinded audit은 더 강한 claim을 위한 선택적 확장이지 현재 이슈가 아님 |
| Open3DSG coverage | `[x]` | 533/548 public coverage와 recovery sensitivity를 supplement에 공개함 |
| Fixed-candidate ceiling | `[x]` | Method scope와 candidate-pool oracle이 generation error를 분리함 |

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
| P1-1 row reproduction | 291 cells exact regeneration | 없음 | schema와 validation | `[x, F-07 조건]` |
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
| Reproducibility checklist | `[x]` | 2-page separate PDF |
| Supplement optional/self-contained main | `[x]` | core claims는 main에서 이해 가능 |
| Author list finality | `[저자 확인]` | submission system에서 지금 확정 |
| Multiple submissions | `[x]` | 저자 확인 결과 해당 없음 |
| Ethics violation | `[x]` | 저자 확인 결과 해당 없음 |
| Generative AI policy | `[저자 확인]` | F-06 처리 |
| Derived data license | `[저자 확인]` | F-07 처리 |
| Final file synchronization | `[x]` | Current source, canonical PDFs, release PDFs, ZIP source와 manifests를 동기화하고 extracted-source rebuild까지 검증함 |
| Last-hour upload risk | `[저자 확인]` | 최종 files를 deadline 직전이 아닌 시점에 업로드 |

## 12. 제출 전 남은 저자 작업

Citation source, clean build, canonical PDFs, release ZIP, outer/inner
manifests, extracted-source rebuild 검증은 완료됐다. 남은 작업은 저자 소유의
정책 및 submission-system 확인이다.

1. F-06 AI-system role disclosure 위치 확정
2. F-07 derived-row redistribution 권한 확정
3. submission-system author list 확인
4. main, supplement, checklist, code/data ZIP을 각각 올바른 upload slot에 배치

## 13. 예상 reviewer 판정

### 예상 Rating: Weak Reject, borderline Weak Accept

강점:

1. Failure mode와 claim boundary가 명확하다.
2. 세 fixed predictor에서 같은 target/protocol로 비교한다.
3. Main controls와 supplement sensitivities가 reviewer의 단순-baseline,
   score-scale, routing, component 질문에 직접 답한다.
4. Point/mesh audit와 dependency disclosure가 verifier dependence를 숨기지 않는다.
5. Reproduction artifact가 매우 강하다.

Reject 쪽으로 남는 이유:

1. 핵심 validity evidence가 independently annotated physical ground truth는 아니다.
2. Main empirical claim은 하나의 3DSSG target에 집중된다.
3. 일부 reviewer는 method를 careful post-processing으로 보고 novelty/significance를
   낮게 평가할 수 있다.
4. Closed-set predictors의 절대 변화는 Open3DSG보다 작다.

Weak Accept로 이동시키는 가장 중요한 방어:

- Claim을 넓히지 않는다.
- Same-pair score-excluded compatibility와 valid transformations가 왜 failure
  mechanism에 필요한지 명확히 유지한다.
- Main M-1--M-3과 Table 2/3을 rebuttal의 첫 evidence로 사용한다.
- Independent ground truth가 아니라는 한계를 선제적으로 인정하되, feature removal,
  alternative measurements, uncertainty policies가 같은 방향을 보인다는
  triangulation을 강조한다.
- F-01--F-05는 닫혔다. F-06 AI disclosure와 F-07 redistribution boundary만
  저자가 venue policy와 license에 맞게 확정한다.

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

| Key | 공식 title, author order, venue/year | 현재 claim support와 판정 |
|---|---|---|
| `cormack2009reciprocal` | *Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods*. Gordon V. Cormack, Charles L. A. Clarke, Stefan Büttcher. ACM SIGIR 2009. [DOI](https://doi.org/10.1145/1571941.1572114) | RRF가 rankings를 결합한다는 Baseline 설명을 직접 지원함 `[x]` |
| `armeni20193d` | *3D Scene Graph: A Structure for Unified Semantics, 3D Space, and Camera*. Iro Armeni, Zhi-Yang He, JunYoung Gwak, Amir R. Zamir, Martin Fischer, Jitendra Malik, Silvio Savarese. ICCV 2019. [CVF](https://openaccess.thecvf.com/content_ICCV_2019/html/Armeni_3D_Scene_Graph_A_Structure_for_Unified_Semantics_3D_Space_ICCV_2019_paper.html) | 3D scene graph의 structured representation 정의를 직접 지원 `[x]` |
| `chen2024clip` | *CLIP-Driven Open-Vocabulary 3D Scene Graph Generation via Cross-Modality Contrastive Learning*. Lianggangxu Chen, Xuejiao Wang, Jiale Lu, Shaohui Lin, Changbo Wang, Gaoqi He. CVPR 2024. [CVF](https://openaccess.thecvf.com/content/CVPR2024/html/Chen_CLIP-Driven_Open-Vocabulary_3D_Scene_Graph_Generation_via_Cross-Modality_Contrastive_Learning_CVPR_2024_paper.html) | Multimodal/open-vocabulary relation generation을 지원 `[x]` |
| `chen2026beyond` | *Beyond Isolated Objects: Relationship-aware Open Vocabulary Scene Understanding via 3D Scene Graph Analysis*. Xianhao Chen, Jiarui Hu, Yuanbo Yang, Xiyu Zhang, Tengyue Wang, Hujun Bao, Guofeng Zhang, Zhaopeng Cui. arXiv 2026. [arXiv](https://arxiv.org/abs/2607.05348) | RelGraphOV의 relation-aware graph construction과 geometric pruning 설명을 직접 지원 `[x]` |
| `fei2026open` | *Open-World 3D Scene Graph Generation for Retrieval-Augmented Reasoning*. Yu Fei, Quan Deng, Shengeng Tang, Li Yuehua, Lechao Cheng. AAAI 2026. [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/37391) | Retrieval, grounding, reasoning, planning downstream claim을 지원함. Current author parsing은 OJS citation export와 일치 `[x]` |
| `feng20233d` | *3D Spatial Multimodal Knowledge Accumulation for Scene Graph Prediction in Point Cloud*. Mingtao Feng, Haoran Hou, Liang Zhang, Zijie Wu, Yulan Guo, Ajmal Mian. CVPR 2023. [CVF](https://openaccess.thecvf.com/content/CVPR2023/html/Feng_3D_Spatial_Multimodal_Knowledge_Accumulation_for_Scene_Graph_Prediction_in_CVPR_2023_paper.html) | Spatial knowledge와 multimodal cues claim을 직접 지원 `[x]` |
| `Feng_2026_CVPR` | *GEODE: Geometry-Guided Discrete Diffusion for Open-Vocabulary 3D Scene Graph Generation*. Changqun Feng, Wangxiandi Yin, Xin Hu, Lei Zhao, Dongyang Zhang, Tao He. CVPR 2026 Findings. [CVF](https://openaccess.thecvf.com/content/CVPR2026F/html/Feng_GEODE_Geometry-Guided_Discrete_Diffusion_for_Open-Vocabulary_3D_Scene_Graph_Generation_CVPRF_2026_paper.html) | Geometry와 predicate를 joint denoising한다는 claim을 지원. Current source와 bibliography key 및 metadata가 일치 `[x]` |
| `gu2024conceptgraphs` | *ConceptGraphs: Open-Vocabulary 3D Scene Graphs for Perception and Planning*. Qiao Gu, Alihusein Kuwajerwala, Sacha Morin, Krishna Murthy Jatavallabhula, Bipasha Sen, Aditya Agarwal, Corban Rivera, William Paul, Kirsty Ellis, Rama Chellappa, Chuang Gan, Celso Miguel de Melo, Joshua B. Tenenbaum, Antonio Torralba, Florian Shkurti, Liam Paull. ICRA 2024. [Project](https://concept-graphs.github.io/) | Querying/planning claim을 직접 지원함. Current abbreviated BibTeX는 official project export와 동일 `[x]` |
| `guo2017calibration` | *On Calibration of Modern Neural Networks*. Chuan Guo, Geoff Pleiss, Yu Sun, Kilian Q. Weinberger. ICML 2017, PMLR 70. [PMLR](https://proceedings.mlr.press/v70/guo17a.html) | Miscalibration과 temperature scaling claim을 직접 지원 `[x]` |
| `heo2026object` | *Object-Centric Representation Learning for Enhanced 3D Semantic Scene Graph Prediction*. KunHo Heo, GiHyun Kim, SuYeon Kim, MyeongAh Cho. NeurIPS volume 38, selected year 2026. [Author repository](https://github.com/VisualScienceLab-KHU/OCRL-3DSSG-Codes) | Object-centric feature claim을 지원함. Google Scholar와 author repository BibTeX에 따라 2026을 유지하기로 저자가 확정 `[x]` |
| `hou2025fross` | *FROSS: Faster-than-Real-Time Online 3D Semantic Scene Graph Generation from RGB-D Images*. Hao-Yu Hou, Chun-Yi Lee, Motoharu Sonogashira, Yasutomo Kawanishi. ICCV 2025. [CVF](https://openaccess.thecvf.com/content/ICCV2025/papers/Hou_FROSS_Faster-Than-Real-Time_Online_3D_Semantic_Scene_Graph_Generation_from_RGB-D_ICCV_2025_paper.pdf) | Online generation claim을 직접 지원 `[x]` |
| `huang2025fireplace` | *FirePlace: Geometric Refinements of LLM Common Sense Reasoning for 3D Object Placement*. Ian Huang, Yanan Bao, Karen Truong, Howard Zhou, Cordelia Schmid, Leonidas Guibas, Alireza Fathi. CVPR 2025. [CVF](https://openaccess.thecvf.com/content/CVPR2025/html/Huang_FirePlace_Geometric_Refinements_of_LLM_Common_Sense_Reasoning_for_3D_CVPR_2025_paper.html) | Adjacent geometry-aware object placement work라는 current wording을 직접 지원 `[x]` |
| `hughes2022hydra` | *Hydra: A Real-time Spatial Perception System for 3D Scene Graph Construction and Optimization*. Nathan Hughes, Yun Chang, Luca Carlone. RSS 2022. [RSS](https://www.roboticsproceedings.org/rss18/p050.pdf) | Online persistent graph construction을 직접 지원함. Current arXiv entry도 실제 version을 정확히 식별 `[x]` |
| `koch2024open3dsg` | *Open3DSG: Open-Vocabulary 3D Scene Graphs from Point Clouds with Queryable Objects and Open-Set Relationships*. Sebastian Koch, Narunas Vaskevicius, Mirco Colosi, Pedro Hermosilla, Timo Ropinski. CVPR 2024. [CVF](https://openaccess.thecvf.com/content/CVPR2024/html/Koch_Open3DSG_Open-Vocabulary_3D_Scene_Graphs_from_Point_Clouds_with_Queryable_CVPR_2024_paper.html) | Open-vocabulary source와 Figure 1 source attribution을 직접 지원 `[x]` |
| `koch2024sgrec3d` | *SGRec3D: Self-Supervised 3D Scene Graph Learning via Object-Level Scene Reconstruction*. Sebastian Koch, Pedro Hermosilla, Narunas Vaskevicius, Mirco Colosi, Timo Ropinski. WACV 2024. [CVF](https://openaccess.thecvf.com/content/WACV2024/html/Koch_SGRec3D_Self-Supervised_3D_Scene_Graph_Learning_via_Object-Level_Scene_Reconstruction_WACV_2024_paper.html) | Self-supervised pretraining claim을 직접 지원 `[x]` |
| `lakshminarayanan2017simple` | *Simple and Scalable Predictive Uncertainty Estimation Using Deep Ensembles*. Balaji Lakshminarayanan, Alexander Pritzel, Charles Blundell. NeurIPS 2017. [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2017/hash/9ef2ed4b7fd2c810847ffa5fa85bce38-Abstract.html) | Deep ensembles uncertainty claim을 직접 지원함 `[x]` |
| `liu2026view` | *View-on-Graph: Zero-Shot 3D Visual Grounding via Vision-Language Reasoning on Scene Graphs*. Yuanyuan Liu, Haiyang Mei, Dongyang Zhan, Jiayue Zhao, Dongsheng Zhou, Bo Dong, Xin Yang. AAAI 2026. [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/37677) | Scene-graph-based visual grounding claim을 직접 지원 `[x]` |
| `ma2026edge` | *Edge-Centric Relational Reasoning for 3D Scene Graph Prediction*. Yanni Ma, Hao Liu, Yulan Guo, Theo Gevers, Martin R. Oswald. AAAI 2026. [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/37728) | Edge-centric representations/reasoning claim을 직접 지원 `[x]` |
| `Madhavaram_2026_WACV` | *VIZOR: Viewpoint-Invariant Zero-Shot Scene Graph Generation for 3D Scene Reasoning*. Vivek Madhavaram, Vartika Sengar, Arkadipta De, Charu Sharma. WACV 2026. [CVF](https://openaccess.thecvf.com/content/WACV2026/html/Madhavaram_VIZOR_Viewpoint-Invariant_Zero-Shot_Scene_Graph_Generation_for_3D_Scene_Reasoning_WACV_2026_paper.html) | Downstream object grounding과 viewpoint-aware reasoning claim을 지원하며 current source와 bibliography key가 일치 `[x]` |
| `maggio2024clio` | *Clio: Real-Time Task-Driven Open-Set 3D Scene Graphs*. Dominic Maggio, Yun Chang, Nathan Hughes, Matthew Trang, Dan Griffith, Carlyn Dougherty, Eric Cristofalo, Lukas Schmid, Luca Carlone. IEEE RA-L 2024. [arXiv](https://arxiv.org/abs/2404.13696) | Task-driven querying/interaction과 online graph construction을 지원 `[x]` |
| `nag2025conformal` | *Conformal Prediction and MLLM Aided Uncertainty Quantification in Scene Graph Generation*. Sayak Nag, Udita Ghosh, Calvin-Khang Ta, Sarosij Bose, Jiachen Li, Amit K. Roy-Chowdhury. CVPR 2025. [CVF](https://openaccess.thecvf.com/content/CVPR2025/html/Nag_Conformal_Prediction_and_MLLM_aided_Uncertainty_Quantification_in_Scene_Graph_CVPR_2025_paper.html) | Conformal prediction-set claim을 직접 지원 `[x]` |
| `neau2026visual` | *Visual Commonsense Driven Knowledge Refinements for Scene Graph Generation*. Maëlic Neau, Salim Baloch, Jakob Suchan, Zoe Falomir, Mehul Bhatt. arXiv 2026. [arXiv](https://arxiv.org/abs/2606.06369) | 2D fixed-prediction declarative refinement라는 current comparison을 직접 지원 `[x]` |
| `nguyen2026relwitness` | *RelWitness: Open-Vocabulary 3D Scene Graph Generation with Visual-Geometric Relation Witnesses*. Minh Anh Nguyen, Quang Huy Tran, Bao Ngoc Le, Tuan Kiet Pham, Sui Yang Guang. arXiv 2026. [arXiv](https://arxiv.org/abs/2605.20823) | Method proposal 범위만 기술하도록 current prose가 `proposes`를 사용함 `[x]` |
| `Ovadia2019CanYT` | *Can You Trust Your Model's Uncertainty? Evaluating Predictive Uncertainty Under Dataset Shift*. Yaniv Ovadia, Emily Fertig, Jie Jessie Ren, Zachary Nado, D. Sculley, Sebastian Nowozin, Joshua V. Dillon, Balaji Lakshminarayanan, Jasper Snoek. NeurIPS 2019. [Semantic Scholar](https://www.semanticscholar.org/paper/Can-You-Trust-Your-Model's-Uncertainty-Evaluating-Ovadia-Fertig/1eb7f46b1a0a7df823194d86543e5554aa21021a) | Distribution-shift uncertainty evaluation claim을 직접 지원하며 current source와 selected Semantic Scholar BibTeX key가 일치 `[x]` |
| `Peng_2023_CVPR` | *OpenScene: 3D Scene Understanding With Open Vocabularies*. Songyou Peng, Kyle Genova, Chiyu “Max” Jiang, Andrea Tagliasacchi, Marc Pollefeys, Thomas Funkhouser. CVPR 2023. [CVF](https://openaccess.thecvf.com/content/CVPR2023/html/Peng_OpenScene_3D_Scene_Understanding_With_Open_Vocabularies_CVPR_2023_paper.html) | Queryable point/region feature claim을 직접 지원함. Current key와 full author list가 official CVF BibTeX와 일치 `[x]` |
| `sarkar2023sgaligner` | *SGAligner: 3D Scene Alignment with Scene Graphs*. Sayan Deb Sarkar, Ondrej Miksik, Marc Pollefeys, Daniel Barath, Iro Armeni. ICCV 2023. [CVF](https://openaccess.thecvf.com/content/ICCV2023/html/Sarkar_SGAligner_3D_Scene_Alignment_with_Scene_Graphs_ICCV_2023_paper.html) | Scene graph alignment과 downstream registration claim을 직접 지원 `[x]` |
| `saxena2025zing` | *ZING-3D: Zero-Shot Incremental 3D Scene Graphs via Vision-Language Models*. Pranav Saxena, Jimmy Chiun. arXiv 2025. [arXiv](https://arxiv.org/abs/2510.21069) | Incremental, geometrically grounded, embodied-use framing을 지원 `[x]` |
| `shao2025great` | *GREAT: Geometry-Intention Collaborative Inference for Open-Vocabulary 3D Object Affordance Grounding*. Yawen Shao, Wei Zhai, Yuhang Yang, Hongchen Luo, Yang Cao, Zheng-Jun Zha. CVPR 2025. [CVF](https://openaccess.thecvf.com/content/CVPR2025/html/Shao_GREAT_Geometry-Intention_Collaborative_Inference_for_Open-Vocabulary_3D_Object_Affordance_Grounding_CVPR_2025_paper.html) | Adjacent geometry-aware affordance grounding work라는 current wording을 직접 지원 `[x]` |
| `sun2026not` | *Not All Relations Rotate Alike: Transformation-Aware Decoupling for Viewpoint-Robust 3D Scene Graph Generation*. Jingjun Sun, Chaowei Wang, Zhirui Liu, Jiaxu Tian, Ming Yang, Yaoxing Wang, Shan Gao. arXiv 2026 v1. [arXiv v1](https://arxiv.org/abs/2606.27412v1) | TAD와 viewpoint-robustness description을 정확히 지원하며 BibTeX가 v1 URL을 명시함 `[x]` |
| `takmaz2023openmask3d` | *OpenMask3D: Open-Vocabulary 3D Instance Segmentation*. Ayça Takmaz, Elisabetta Fedele, Robert W. Sumner, Marc Pollefeys, Federico Tombari, Francis Engelmann. NeurIPS 2023. [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2023/hash/d77b5482e38339a8068791d939126be2-Abstract-Conference.html) | Queryable instance features claim을 직접 지원함. Current arXiv entry도 동일 paper를 정확히 식별 `[x]` |
| `wald2019rio` | *RIO: 3D Object Instance Re-Localization in Changing Indoor Environments*. Johanna Wald, Armen Avetisyan, Nassir Navab, Federico Tombari, Matthias Nießner. ICCV 2019. [CVF](https://openaccess.thecvf.com/content_ICCV_2019/html/Wald_RIO_3D_Object_Instance_Re-Localization_in_Changing_Indoor_Environments_ICCV_2019_paper.html) | Repeated indoor reconstruction and 3RScan claim을 직접 지원 `[x]` |
| `wald2020learning` | *Learning 3D Semantic Scene Graphs From 3D Indoor Reconstructions*. Johanna Wald, Helisa Dhamo, Nassir Navab, Federico Tombari. CVPR 2020. [CVF](https://openaccess.thecvf.com/content_CVPR_2020/html/Wald_Learning_3D_Semantic_Scene_Graphs_From_3D_Indoor_Reconstructions_CVPR_2020_paper.html) | 3DSSG annotations, benchmark, shared target claim을 직접 지원 `[x]` |
| `wang2023vl` | *VL-SAT: Visual-Linguistic Semantics Assisted Training for 3D Semantic Scene Graph Prediction in Point Cloud*. Ziqin Wang, Bowen Cheng, Lichen Zhao, Dong Xu, Yang Tang, Lu Sheng. CVPR 2023. [CVF](https://openaccess.thecvf.com/content/CVPR2023/html/Wang_VL-SAT_Visual-Linguistic_Semantics_Assisted_Training_for_3D_Semantic_Scene_Graph_CVPR_2023_paper.html) | VL-SAT source와 visual-linguistic cue claim을 직접 지원 `[x]` |
| `wang2025open` | *Open-Vocabulary Octree-Graph for 3D Scene Understanding*. Zhigang Wang, Yifei Su, Chenhui Li, Dong Wang, Yan Huang, Xuelong Li, Bin Zhao. ICCV 2025. [CVF](https://openaccess.thecvf.com/content/ICCV2025/html/Wang_Open-Vocabulary_Octree-Graph_for_3D_Scene_Understanding_ICCV_2025_paper.html) | Open-vocabulary graph representation, spatial relation, downstream retrieval/planning claim을 지원 `[x]` |
| `werby2024hierarchical` | *Hierarchical Open-Vocabulary 3D Scene Graphs for Language-Grounded Robot Navigation*. Abdelrhman Werby, Chenguang Huang, Martin Büchner, Abhinav Valada, Wolfram Burgard. RSS 2024. [RSS](https://www.roboticsproceedings.org/rss20/p077.pdf) | Language-grounded navigation claim을 직접 지원함. Current workshop entry도 실제 version을 정확히 식별 `[x]` |
| `wu2021scenegraphfusion` | *SceneGraphFusion: Incremental 3D Scene Graph Prediction From RGB-D Sequences*. Shun-Cheng Wu, Johanna Wald, Keisuke Tateno, Nassir Navab, Federico Tombari. CVPR 2021. [CVF](https://openaccess.thecvf.com/content/CVPR2021/html/Wu_SceneGraphFusion_Incremental_3D_Scene_Graph_Prediction_From_RGB-D_Sequences_CVPR_2021_paper.html) | Incremental system과 SGFN source attribution을 직접 지원 `[x]` |
| `xie2024sg` | *SG-PGM: Partial Graph Matching Network with Semantic Geometric Fusion for 3D Scene Graph Alignment and Its Downstream Tasks*. Yaxu Xie, Alain Pagani, Didier Stricker. CVPR 2024. [CVF](https://openaccess.thecvf.com/content/CVPR2024/papers/Xie_SG-PGM_Partial_Graph_Matching_Network_with_Semantic_Geometric_Fusion_for_CVPR_2024_paper.pdf) | Semantic-geometric alignment과 downstream geometric tasks claim을 직접 지원 `[x]` |
| `yang2021probabilistic` | *Probabilistic Modeling of Semantic Ambiguity for Scene Graph Generation*. Gengcong Yang, Jingyi Zhang, Yong Zhang, Baoyuan Wu, Yujiu Yang. CVPR 2021. [CVF](https://openaccess.thecvf.com/content/CVPR2021/html/Yang_Probabilistic_Modeling_of_Semantic_Ambiguity_for_Scene_Graph_Generation_CVPR_2021_paper.html) | Semantic ambiguity와 probabilistic modeling claim을 직접 지원 `[x]` |
| `yang2026puf` | *PUF: Plug-and-Play Uncertainty-Aware Fusion for Online 3D Scene Graph Generation*. Yi Yang, Myrna Castillo, Bodo Rosenhahn, Michael Ying Yang. arXiv 2026, accepted ECCV 2026. [arXiv](https://arxiv.org/abs/2607.07170) | Association and incremental fusion uncertainty claim을 직접 지원 `[x]` |
| `yeo2025statistical` | *Statistical Confidence Rescoring for Robust 3D Scene Graph Generation from Multi-View Images*. Qi Xun Yeo, Yanyan Li, Gim Hee Lee. ICCV 2025. [CVF](https://openaccess.thecvf.com/content/ICCV2025/html/Yeo_Statistical_Confidence_Rescoring_for_Robust_3D_Scene_Graph_Generation_from_ICCV_2025_paper.html) | Masks, neighboring relations, statistical priors rescoring claim을 직접 지원 `[x]` |
| `zhang2021exploiting` | *Exploiting Edge-Oriented Reasoning for 3D Point-Based Scene Graph Analysis*. Chaoyi Zhang, Jianhui Yu, Yang Song, Weidong Cai. CVPR 2021. [CVF](https://openaccess.thecvf.com/content/CVPR2021/html/Zhang_Exploiting_Edge-Oriented_Reasoning_for_3D_Point-Based_Scene_Graph_Analysis_CVPR_2021_paper.html) | Edge reasoning과 point-cloud relation prediction claim을 직접 지원 `[x]` |
| `zhang2025open` | *Open-Vocabulary Functional 3D Scene Graphs for Real-World Indoor Spaces*. Chenyangguang Zhang, Alexandros Delitzas, Fangjinhua Wang, Ruida Zhang, Xiangyang Ji, Marc Pollefeys, Francis Engelmann. CVPR 2025. [CVF](https://openaccess.thecvf.com/content/CVPR2025/html/Zhang_Open-Vocabulary_Functional_3D_Scene_Graphs_for_Real-World_Indoor_Spaces_CVPR_2025_paper.html) | Functional relations and downstream reasoning/manipulation claim을 직접 지원 `[x]` |
| `zhu2024calibration` | *Calibration for Long-Tailed Scene Graph Generation*. Xuhan Zhu, Yifei Xing, Ruiping Wang, Yaowei Wang, Xiangyuan Lan. ACM MM 2024. [OpenReview](https://openreview.net/forum?id=jGNDRM2vul) | Long-tailed SGG calibration claim을 직접 지원함 `[x]` |

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
| Known layout warning | `[보류]` | Main의 first-page vertical overfull 36.77646 pt만 저자 결정에 따라 유지함 |
| Canonical synchronization | `[x]` | Working PDFs와 canonical PDFs 및 release PDFs의 byte hash가 일치함 |
| Release integrity | `[x]` | ZIP 221 entries, outer/inner SHA-256, ZIP integrity, JSON parsing, Python compilation, Compose parsing이 통과함 |
| Extracted-source rebuild | `[x]` | ZIP에서 재빌드한 9/10/2-page PDFs가 release PDFs와 text 및 page geometry에서 일치함 |
