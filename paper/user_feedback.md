# RelCompat3D 제출용 통합 검토

- 최종 갱신: 2026-07-31 KST
- Main source: `paper/aaai/main.tex`
- Main sections: `paper/aaai/sec/0_abstract.tex`--`6_conclusion.tex`
- Technical Supplement: `paper/aaai/supplement.tex`,
  `paper/aaai/sec/supplement.tex`
- Reproducibility checklist:
  `paper/aaai/reproducibility_checklist_main.tex`,
  `paper/aaai/reproducibility_checklist.tex`
- 현재 편집 경계: **Main paper는 제출 완료 상태로 동결한다.**
  이 문서는 Section별 판정, rebuttal 근거, Technical Supplement 개선 사항을
  관리한다.

상태 표시는 다음과 같다.

- `[x]`: 해결 완료 또는 현재 표현으로 충분
- `[~]`: 오류는 아니지만 제출 전 개선 권장
- `[ ]`: Technical Supplement 제출 전 해결 권장
- `[선택]`: claim을 바꾸지 않는 선택적 보강
- `[저자 확인]`: 정책, 라이선스, 저자 행위에 관한 확인 필요
- `[범위 한계]`: writing으로 제거할 수 없는 현재 evidence 범위

## 1. 최종 판단과 핵심 상태

Main의 problem--method--experiment story와 핵심 수치는 정합하다. 논문은
source relation score가 same-pair predicate--geometry compatibility의 명시적
추정값이 아닐 수 있다는 failure를 제기하고, source-score-excluded
compatibility, relation-preserving transformation averaging, family-aware
re-ranking으로 답한다. 세 contribution은 Method와 Experiment evidence에
대응한다.

Main은 broad SOTA, full-ontology 3DSSG improvement, dataset-level
generalization, independent ground truth for geometric validity를 주장하지
않는다. 남는 scientific risk는 evaluator와 training construction의 construct
dependence, single-target 범위, post-hoc re-ranking으로 보일 novelty risk다.
이 세 항목의 rebuttal boundary와 evidence는 Section 3에서 관리한다.

현재 Technical Supplement는 9-page US-Letter PDF이며 A--C sections,
16 tables, Figure S1을 포함한다. Table S2/S3 배치, checkpoint provenance,
implementation diagnostic의 정보량과 table heading을 정리했다. Figure S1은
검증된 `desk close by chair` promotion을 proximity case로 사용한다.
Section 6이 supplement 관련 authoritative review다.

## 2. Section별 검토

### Abstract

- `[x]` **고유 용어의 최소 설명과 자기 완결성:** RelCompat3D를 fixed relation
  prediction을 위한 post-hoc re-ranking framework로 정의한다.
- `[x]` **문제--방법--결과--기여:** High-score mismatch, compatibility
  estimation, family-aware re-ranking, three-predictor result, alternative
  audit가 모두 포함된다.
- `[x]` **Introduction contribution과 대응:** Introduction의 세 contribution과
  과부족 없이 대응한다.
- `[x]` **Hedging과 claim boundary:** `reported predictor--K settings`,
  `point estimates`, `verifier-derived`가 적절하다. Point/mesh audit도
  alternative Violation 변화의 방향만 뒷받침한다고 제한한다.
- `[x]` **문장당 정보량:** Result sentence는 두 metric의 joint claim 하나를
  전달하며 추가 분할이 필수적이지 않다.
- `[x]` **Citation과 기호:** Citation과 정의되지 않은 기호가 없다.
- `[x]` **Experiment 수치와 일치:** All-\(K\) non-decrease/non-increase
  point-estimate claim이 Table 1과 일치한다.
- `[x]` **최종 영어:** 관사, number agreement, collocation이 자연스럽고
  `predictor-agnostic reliability signal`의 범위도 Discussion과 일치한다.

### Introduction

- `[x]` **현재 claim을 명시적으로 제안하는 문장:** Source score가 same-pair
  compatibility를 직접 추정하지 않는다는 한계와 `We propose RelCompat3D`
  문단이 task, inputs, score exclusion, estimators, training,
  transformations를 명시한다.
- `[x]` **선행연구 citation 존재:** 언급된 연구군과 predictor에 citation이 있다.
- `[x]` **Contribution 세 개와 Method 대응:** Contribution 1은 Problem
  Formulation과 Metrics, Contribution 2는 Compatibility Estimation,
  Contribution 3은 Family-Aware Re-Ranking과 cross-predictor evaluation에
  대응한다.
- `[x]` **Method 전용 용어 정의:** \(T,G,Z\), counterfactual과 transformation의
  차이, re-ranking scope가 Method 전에 필요한 수준으로 설명된다.
- `[x]` **논리 흐름:** Downstream need, score-type motivation, general score
  limitation, method, evaluation, contributions 순서가 적절하다.
- `[x]` **Experiment 수치와 일치:** All-\(K\) claim은 Table 1과 일치하며
  Source-relative point estimates로 한정한다.
- `[x]` **Hedging 일관성:** Shared validation scenes, verifier-derived
  Violation, alternative audit 표현이 Results와 Discussion의 범위와 맞는다.
- `[x]` **Figure 1 역할:** Motivation을 보여주는 qualitative failure case로
  적합하며 Results에서 다시 호출된다.
- `[x]` **Predictor-dependent motivation:** Text-embedding similarity와
  ordered-pair geometric support를 구분하고, compatibility의 역할이 predictor
  score type에 따라 달라질 수 있음을 Table 2 해석과 연결한다.
- `[x]` **Good English와 용어:** `task-specific`, `relation-preserving`,
  `source relation score`, `ordered-pair geometry`가 일관된다.

### Related Work

- `[x]` **Subsection 구성과 제목 정합성:** 3D Scene Graph Prediction,
  Geometry-aware Relation Evidence, Reliability Evaluation and Calibration의
  세 축이 내용과 일치한다.
- `[x]` **선행연구 citation 정확성:** Current main의 43개 citation key는
  bibliography에 존재하며 공식 proceedings, publisher, versioned arXiv
  metadata와 대조했다. Heo 2026은 저자가 확인한 Scholar와 author repository
  metadata를 따르는 저자 결정이다.
- `[x]` **공통점과 차이점:** Fixed-generator post-processing,
  source-score exclusion, transformation consistency를 prior relation
  generation과 구체적으로 구분한다.
- `[x]` **Introduction과 중복 관리:** Introduction은 failure와 design necessity,
  Related Work는 prior-method 대비를 담당한다.
- `[x]` **Calibration 경계:** Recall@\(K\)와 Violation@\(K\)가 calibrated
  probability를 제공하지 않는다고 명시한다.
- `[x]` **Figure 2 연결:** Caption은 input separation, score combination,
  re-ranking 결과를 설명하고 Method 본문이 세부 절차를 잇는다.
- `[x]` **Good English:** 다중 연구를 가리키는 plural subject, citation
  mapping, ordered-pair geometry 표현이 자연스럽다.

### Method

- `[x]` **Notation과 정의 순서:** Candidate identity,
  \(T,G,Z,a,q,C,H,\mathcal O,u\), evaluated/re-ranked family 순서가 적절하다.
  Support/contact transformation set은 불필요한 단발성 identity 기호 없이
  문장으로 정의한다.
- `[x]` **Introduction 설계 선택과 대응:** Linear/MLP estimators, linked
  counterfactuals, transformation averaging, family-aware scoring이 예고한
  설계와 대응한다.
- `[x]` **수식과 prose의 일치:** Source score는 compatibility estimator에
  들어가지 않고 within-family score에서만 결합된다.
- `[x]` **Support/contact 범위:** Identity transformation과 source-order
  preservation이 명확하다.
- `[x]` **가정과 scope:** Known instances, reconstructed pair geometry,
  applicable relation transformations를 명시한다.
- `[x]` **재현 가능성:** Optimizer, step 수, learning rate, seed와 loss
  hyperparameter가 supplement 및 frozen protocol과 일치한다.
- `[x]` **Figure caption 연결:** Figure 2의 flow와 Problem Formulation,
  Compatibility Estimation, Family-Aware Re-Ranking이 같은 순서를 따른다.
- `[x]` **Source readability:** Heading, MLP 설명, proximity-negative 문장,
  compatibility-head antecedent, support/contact identity 정의가 자연스럽다.

### Experiments

- `[x]` **Dataset과 evaluation scope:** 157 scans, 548 contexts, 3,972 exact
  ground-truth relations가 명확하다. Training positives와 evaluation-split
  ground truth를 구분한다.
- `[x]` **공정한 비교:** 세 predictor는 같은 split, candidate scope, metrics,
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
- `[x]` **Main sensitivity 문장:** Score mapping, robust-density, routing
  control의 compact statements는 supplement의 frozen results와 일치한다.
- `[x]` **통계적 주장:** \(K=50\) paired interval 문장과 point-estimate
  all-\(K\) 문장을 구분한다.
- `[x]` **Alternative audit 경계:** Point/mesh audit는 alternative
  measurement이지 independent ground truth가 아니다.
- `[x]` **Qualitative coverage:** Main text가 vertical demotion, proximity
  demotion, proximity promotion을 다룬다.
- `[x]` **Section structure:** Main trade-off, sensitivity, qualitative cases,
  ablations, alternative audit가 중복 없이 한 번씩 제시된다.
- `[x]` **Ablation interpretation:** Compatibility-only, wrong predicate,
  wrong pair, shuffled geometry, fixed-predicate swap, distance-only의
  predictor-dependent 의미를 각각 설명한다.

### Discussion and Limitations

- `[x]` **Scope 한계 일관성:** Single split, known instances,
  support/contact scope가 Method와 일치한다.
- `[x]` **통계적 주장:** Dataset-level generalization과 independent physical
  validity를 주장하지 않는다.
- `[x]` **자기비판의 균형:** Predictor-score interpretation과 claim boundary를
  두 paragraph로 나누어 과도한 약점 나열을 피한다.
- `[x]` **실패와 약한 지점:** Point/mesh audit가 same scenes와 ontology를
  사용한다는 한계와 additional-dataset 필요성을 설명한다.
- `[x]` **Broader implication:** Predictor-agnostic construction과
  predictor-dependent effect를 구분하며, corresponding pair geometry가 있는
  grounded relation ranking으로의 확장 가능성을 제시한다.
- `[x]` **Good English:** Collocation, spelling, number agreement가 적절하다.

### Conclusion

- `[x]` **Introduction과 연결:** Source-score exclusion, predictor-dependent
  control result, predictor-agnostic signal을 같은 핵심 메시지로 마무리한다.
- `[x]` **새 주장 여부:** Method와 Experiment에 없던 수치나 claim을 추가하지
  않는다.
- `[x]` **Overclaiming 방지:** `shared 3DSSG validation scenes`, `point
  estimates`, Source-relative wording이 evidence의 범위와 일치한다.
- `[x]` **중복 관리:** Contribution bullets를 그대로 복사하지 않고 final
  synthesis를 제공한다.
- `[x]` **최종 영어:** 오타, 관사, subject--verb agreement 문제가 없다.

### Supplement

- `[x]` **통합 판정:** Method details와 main-supporting evidence가 충분하다.
  Table S2/S3 배치, checkpoint provenance, diagnostic 정보량과 table heading을
  정리했다. Figure S1은 새 evidence를 만들지 않고 검증된 proximity case를
  `Proximity demotion`으로 명확히 표시한다.

### Reproducibility Checklist

- `[x]` **Official template 보존:** 질문, Instructions, response options를
  수정하지 않고 author response만 채웠다.
- `[x]` **Main과 supplement 근거:** Dataset access, preprocessing,
  metric definitions, fixed seeds, final hyperparameters, bootstrap intervals,
  infrastructure 답변이 manuscript 범위와 맞는다.
- `[x]` **Code appendix 응답:** Review 단계에 Code and Data Supplement를
  제출하지 않으므로 preprocessing code와 full code appendix는 `no`다.
  Post-acceptance code release 계획은 별도 문항에 사실대로 답한다.
- `[x]` **Theoretical section 처리:** Parent answer가 `no`이고 하위 문항이
  `If yes` 조건부이므로 하위 response를 비워 둔 현재 형식이 적절하다.
- `[x]` **Build:** Standalone checklist는 2-page US Letter, PDF 1.5이며
  warning, overfull box, font 문제가 없다.

## 3. Reviewer 관점의 잔여 risk와 rebuttal

AAAI-27 Phase 1 reject에는 author response가 없다. 아래 rebuttal은 Phase 2에
진입했을 때의 대응이다. Core evidence를 rebuttal에서 새로 만드는 계획으로
해석하면 안 된다.

### Major 1. Evaluator와 training construction의 construct dependence

**Risk.**

- Counterfactual construction과 primary verifier가 일부 OBB measurements와
  family thresholds를 공유한다.
- Point/mesh audit도 같은 reconstructed scenes와 ontology를 사용하므로
  independent physical-validity ground truth가 아니다.

**현재 evidence.**

- Evaluation candidate rows, source relation scores, predictor identity,
  primary verifier labels는 compatibility fitting에 사용하지 않는다.
- Exact-scalar, related-measurement, alternative-evidence removals,
  uncertainty variants, point/mesh audit, information-use matrix를 보고한다.
- Discussion에서 audit를 independent ground truth라고 부르지 않는다.

**Rebuttal 방향.**

- 먼저 information-use matrix와 feature-removal 결과를 연결해 evaluator label
  leakage와 shared geometric construct를 구분한다.
- 추가 human audit가 요구되면 frozen random sample과 사전 정의된 rubric을
  사용한다. Annotator에게 predictor, method, rank, compatibility, verifier
  status를 숨기고 candidate 순서를 무작위화한다.
- 가능하면 두 명 이상의 독립 annotator와 blinded adjudication을 사용한다.
  저자 한 명만 label하면 `author-annotated blind audit`로 명명하고 independent
  physical ground truth라고 부르지 않는다.

**범위 한계 / 유지할 claim.**

- Claim은 `verifier-derived reliability on shared validation scenes`다.
- Reconstructed geometry를 사람이 판독한 label도 human reference label일 수는
  있지만 실제 scene의 independent physical ground truth와 같지 않다.

### Major 2. Single-target external validity와 downstream significance

**Risk.**

- 세 predictor 비교가 하나의 3DSSG validation split에 집중된다.
- 실제 downstream task 개선은 보고하지 않는다.

**현재 evidence.**

- Abstract, Discussion, Conclusion을 shared-target claim으로 제한한다.
- 동일 target에서 split, contexts, family scope, metrics, \(K\), verifier를
  고정해 predictor score type의 차이를 비교한다.

**Rebuttal 방향.**

- Evidence axis가 dataset 수가 아니라 동일 target에서 predictor가 바뀔 때의
  score--geometry mismatch임을 설명한다.
- Same-target design은 annotation과 evaluation scope를 고정한 controlled
  comparison이다.
- 추가 target 결과가 사용 가능하더라도 ontology와 geometry shift의 차이를
  숨기지 않고 stress evidence로만 제시한다.

**범위 한계 / 유지할 claim.**

- Dataset-level generalization과 embodied downstream utility를 주장하지 않는다.
- Additional datasets와 downstream tasks는 future extension이다.

### Major 3. Novelty가 calibration 또는 generic post-processing으로 보일 위험

**Risk.**

- Reviewer가 method를 geometry features와 product re-ranking의 incremental
  combination으로 볼 수 있다.
- Pairwise-loss removal의 aggregate 변화가 작다.

**현재 evidence.**

- Novelty를 product formula가 아니라 source-score-excluded same-pair
  compatibility, relation-preserving transformations, family-composition
  constraint의 결합으로 정의한다.
- Wrong-predicate, wrong-pair, shuffled-geometry, no-averaging, matched routing,
  robust-density, RankAvg/RRF controls를 제공한다.
- Introduction이 semantic score와 ordered-pair geometric support의 차이를
  failure cause로 설명한다.

**Rebuttal 방향.**

- 세 design constraint가 failure cause에 각각 대응함을 표로 연결한다.
- Pair/geometry controls는 same-pair identity, transformation diagnostics는
  equivalent representation consistency, routing control은 non-interference와
  family composition에 대응한다고 설명한다.
- Robust-density와 matched fusion results로 generic distance rule이나 단순
  score replacement만으로 결과를 설명할 수 없음을 보인다.

**범위 한계 / 유지할 claim.**

- Pairwise loss를 전체 성능의 유일한 원인으로 주장하지 않는다.
- RelCompat3D를 universal calibration, new relation generator,
  aggregate-optimal fusion rule로 주장하지 않는다.

### Major 4. Product score의 scale sensitivity

**현재 대응.**

- Fixed smooth mappings에서 Linear 75/75, MLP 74/75 settings가 Source-relative
  joint direction을 유지한다.
- Percentile mapping의 작은 Recall losses를 공개한다.
- RankAvg/RRF를 같은 family-aware route에서 비교한다.

**Rebuttal 방향과 boundary.**

- Tested mappings에서 conclusion이 안정적이라고 답한다.
- `score-scale invariant` 또는 calibrated-product superiority를 주장하지 않는다.

### Major 5. Family-aware rule의 필요성과 aggregate optimum 부재

**Risk.**

- Joint P/V 또는 Product가 일부 aggregate cells에서 더 좋아 보일 수 있다.

**현재 evidence.**

- Joint P/V control은 estimator와 \(K\)에 따라 결과가 달라진다.
- Family-aware rule은 source family sequence와 support/contact subsequence를
  정확히 보존한다.
- Product는 support/contact selection을 바꾸므로 동일-scope comparator가
  아니다.

**Rebuttal 방향.**

- Family-aware re-ranking을 aggregate-optimal rule이 아니라 cross-family
  competition과 unsupported support/contact intervention을 막는
  composition-preserving constraint로 설명한다.
- Product를 숨기지 않되 comparable-method best에서 제외하는 이유를
  non-interference scope로 답한다.

**범위 한계.**

- Support/contact compatibility improvement를 주장하지 않는다.
- Family-aware route가 모든 estimator와 \(K\)에서 최적이라고 주장하지 않는다.

### Major 6. Closest simple baseline 부족

**현재 대응.**

- Training-positive robust-density baseline을 동일 candidate pool, product
  score, transformation averaging, family-aware route에서 평가한다.
- \(K=50\)에서 두 RelCompat3D estimators가 세 predictors 모두에서 higher
  Recall과 lower Violation을 보인다.
- Hard-tail/Hard-drop은 evaluation verifier labels를 ranking input으로 쓰므로
  non-deployable diagnostics로 분리한다.

**Rebuttal 방향.**

- Robust-density가 가장 가까운 non-learned deployable baseline임을 정의한다.
- Direct-verifier diagnostics는 upper diagnostic이지 method comparator가
  아니라고 구분한다.

### Major 7. Artifact reproducibility와 licensed-input 접근성

**현재 evidence.**

- Derived rows로 Tables 1--3과 Figure 3 data를 한 command에서 재생성한다.
- 291 canonical cells를 tolerance \(10^{-12}\)에서 maximum error 0으로
  검증했다.
- Docker exporter, reproducer, schema, compact outputs, manifests가 내부에 있다.

**Review-stage boundary.**

- Technical Supplement만 제출하며 Code and Data Supplement는 제출하지 않는다.
- Licensed scans, meshes, RGB-D data, third-party checkpoints, stable source
  identifiers, source-derived row bundle을 재배포하지 않는다.
- Post-acceptance release는 upstream terms를 확인한 code와 aggregate artifact로
  제한한다.

**Rebuttal risk.**

- Reviewer는 review artifact만으로 raw predictions와 geometry join을
  end-to-end 재생성할 수 없다.
- Checklist에는 code appendix 부재를 `no`로 답한다. Technical Supplement는
  protocol과 internal regeneration check를 설명하지만 executable artifact라고
  표현하지 않는다.

### Major 8. Restricted relation-family scope와 benchmark interpretation

**Risk.**

- Reported evaluation은 support/contact, proximity, vertical-order로 제한된다.
  실제 re-ranking은 proximity와 vertical order에만 적용된다.
- Table 1 Recall은 full-ontology standard 3DSSG Recall과 denominator,
  candidate competition, predicate coverage가 다르다.
- Fixed-candidate re-ranking은 candidate pool에 없는 relation을 생성할 수 없다.

**현재 evidence.**

- Method와 Experiments에서 evaluation families와 re-ranking families를
  분리한다.
- Source와 모든 conditions는 같은 restricted candidate pool과 denominator를
  사용하므로 within-paper Source-relative comparison은 공정하다.
- Main은 SOTA나 full-ontology improvement를 주장하지 않는다.

**Rebuttal 방향.**

- Research question이 full graph generation accuracy가 아니라 fixed candidate
  score의 same-pair compatibility인지 설명한다.
- 동일 pool, scope, verifier, \(K\)를 고정한 comparison이 이 질문에 맞는
  controlled evaluation임을 강조한다.

**범위 한계.**

- Absent candidates, support/contact correction, full-ontology generation은
  해결하지 않는다.

### Minor risks

| 항목 | 현재 상태와 대응 |
|---|---|
| Primary verifier transparency | Metric, status, shared measurements, feature removals을 supplement에 공개 |
| Uncertain denominator | Main definition과 alternative uncertainty policies가 있음 |
| Training stochasticity | Five-seed results와 작은 exception을 supplement에 보고 |
| Qualitative selection | Main은 demotion과 promotion을 포함함. Supplement Figure S1의 중복 개선은 Section 6.6에서 별도 판단 |
| Open3DSG coverage | Missing-context와 recovery sensitivity를 supplement에서 설명 |
| Fixed-candidate ceiling | Method scope로 명시. Oracle은 review PDF에서 제외해도 core claim은 유지 |
| Predictor-dependent effect | Introduction, Table 2 interpretation, Discussion, Conclusion에서 숨기지 않음 |
| Multiple-\(K\) interpretation | All-\(K\) statement는 point-estimate direction으로만 제한 |

## 4. P0/P1 evidence 상태

상세 protocol path와 hash는 experiment README와 manifest가 소유한다. 여기서는
paper-facing conclusion만 유지한다.

| 분석 | 핵심 결과 | Main | Technical Supplement | 상태 |
|---|---|---|---|---|
| P0-1 score mappings | Smooth mappings에서 Linear 75/75, MLP 74/75 joint direction 유지 | Compact statement | Mapping/percentile sensitivity | `[x]` |
| P0-2 robust density | \(K=50\)에서 두 estimators가 세 predictors의 baseline보다 higher Recall/lower Violation | Compact statement | All-\(K\) table | `[x]` |
| P0-3 routing | Joint P/V 결과가 estimator와 \(K\)에 따라 달라짐 | Compact interpretation | All-\(K\), composition change | `[x]` |
| P0-4 construct dependence | Shared OBB construct를 공개하고 alternative evidence와 uncertainty policies로 경계 확인 | Table 3/Discussion | Dependency matrix와 removals | `[x]` |
| Component diagnostics | Pairwise/no-averaging와 transformation error 보고 | Pointer | Linear/MLP diagnostics | `[x]` |
| Seed robustness | 다섯 fixed seeds에서 방향 안정성 점검 | 없음 | Secondary diagnostic | `[x]` |
| P1-1 row regeneration | 291 cells exact regeneration | 없음 | Internal check | `[x, post-acceptance release]` |
| P1-2 candidate oracle | Fixed-candidate ceiling 정량화 | 없음 | Review PDF에서 제외 | `[x, 내부 보존]` |

## 5. Main 제출과 source의 핵심 확인

이 절은 이전 Author Kit, citation, language, Figure/Table, build history에서
현재 제출 판단에 필요한 결론만 남긴다.

### 5.1 Main manuscript

- `[x]` Technical content는 page 7 안에 끝나며 references는 이후 pages다.
- `[x]` US Letter, PDF 1.5, embedded fonts, no Type 3/CID/Identity font를
  확인했다.
- `[x]` Undefined citation/reference, BibTeX warning, overfull box,
  graphics-inclusion warning은 current clean build에서 0이었다.
- `[x]` Figure 1--3과 Table 1--3은 모두 본문에서 참조되고 caption과 수치가
  일치한다.
- `[x]` Caption은 roman typography를 사용하고 table text는 9-point minimum을
  지킨다.
- `[x]` Main과 supplement에 author, affiliation, acknowledgment,
  author-owned web link가 없다.
- `[x]` Ethics violation, simultaneous submission, self-citation anonymity,
  submission-count issue는 저자 확인 결과 해당 없다.
- `[저자 확인]` Generative-AI role documentation은 실제 사용 범위와 AAAI
  publication policy에 맞춰 저자가 최종 확인한다.

### 5.2 Citation

- `[x]` Current main의 43개 citation key는 모두 bibliography에 존재한다.
- `[x]` Official proceedings/publisher metadata와 versioned arXiv를 우선
  판정 기준으로 사용했다.
- `[x]` VIZOR는 `Madhavaram_2026_WACV`, Ovadia는
  `Ovadia2019CanYT`, TAD는 참고한 arXiv v1, Heo는 2026 entry로 통일했다.
- `[x]` RelWitness는 proposal 범위로만 기술한다.
- `[x]` Undefined citation과 `.blg` warning은 0이었다.

### 5.3 용어와 문체

- `[x]` `source relation score`, `predicate--geometry compatibility`,
  `ordered-pair measurements`, `family-aware re-ranking`,
  `verifier-derived Violation`, `shared 3DSSG validation scenes`가 일관된다.
- `[x]` 의도하지 않은 paragraph duplication, 45단어 이상의 run-on,
  comma splice, em-dash와 semicolon 남용, 불필요한 possessive form은 없다.
- `[x]` Abstract--Conclusion은 같은 motivating failure, method scope,
  Source-relative evidence, limitation으로 연결된다.

### 5.4 예상 reviewer 판정

현재 예상은 **Weak Reject와 Weak Accept의 경계**다. Clarity, controls,
predictor-dependent interpretation, scoped claim은 강점이다. 반면 independent
validity label 부재, single-target 범위, post-hoc framework로 보일 novelty risk는
writing만으로 제거할 수 없다. Phase 2에 진입하면 Section 3의 rebuttal evidence를
claim별로 직접 연결하는 것이 중요하다.

## 6. Technical Supplement 1차 개선 검토

확인일은 2026-07-30 KST다. Main은 수정하지 않으며, 이 절은
`paper/aaai/sec/supplement.tex`과 Technical Supplement PDF에만 적용한다.

### 6.1 공식 규정과 accepted-paper 관행

공식 자료:

- [AAAI-27 Supplementary Material](https://aaai.org/conference/aaai/aaai-27/supplementary-material/)
- [AAAI-27 Main Technical Track Call](https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/)

AAAI-27은 Supplementary Document를 proofs, derivations, experimental
details, dataset descriptions, extended results를 위한 optional supporting
PDF로 정의한다. Main은 self-contained해야 하며 reviewer는 supplement를 읽을
의무가 없다. Anonymous repository를 포함한 author-owned web pointer도 금지된다.
따라서 supplement의 목표는 가능한 모든 내부 분석을 싣는 것이 아니라 main
claim을 검증하고 재구현하는 데 직접 필요한 정보를 읽기 쉬운 순서로 제공하는
것이다.

Accepted-paper 사례:

- [ECCV 2024 3D-HetSGP supplement](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/03785-supp.pdf)는
  implementation details, fair comparison, additional results, ablation,
  qualitative results 순으로 구성한다. VL-SAT와 SGFN은 open-source code로
  학습했다고 설명하며 opaque한 로컬 checkpoint filename을 요구하지 않는다.
- [CVPR 2024 Discriminative Sample-Guided supplement](https://openaccess.thecvf.com/content/CVPR2024/supplemental/Perera_Discriminative_Sample-Guided_and_CVPR_2024_supplemental.pdf)는
  공개된 pretrained weights를 사용했다는 provenance를 설명한다.
- [CVPR 2024 Face2Diffusion supplement](https://openaccess.thecvf.com/content/CVPR2024/supplemental/Shiohara_Face2Diffusion_for_Fast_CVPR_2024_supplemental.pdf)는
  released checkpoint를 그대로 쓴 경우와 official training code로 다시
  학습한 경우를 구분한다.
- [CVPR 2024 MeaCap supplement](https://openaccess.thecvf.com/content/CVPR2024/supplemental/Zeng_MeaCap_Memory-Augmented_Zero-shot_CVPR_2024_supplemental.pdf)는
  peak memory를 보고하지만 computational-cost comparison이 명시적 실험
  항목일 때 사용한다.
- [NeurIPS 2022 supplement example](https://proceedings.neurips.cc/paper_files/paper/2022/file/1165af8b913fb836c6280b42d6e0084f-Supplemental-Conference.pdf)는
  optimizer, learning rate, training iterations, hardware와 runtime을
  implementation section에 모아 보고한다.

공통 원칙은 다음과 같다.

1. Publicly released artifact를 사용하면 release provenance와 stable model
   name을 쓴다.
2. Official code로 직접 학습하면 official implementation/configuration,
   split과 checkpoint-selection rule을 쓴다.
3. `epoch=...-step=...ckpt` 같은 opaque한 로컬 filename은 public artifact를
   식별하지 못하면 PDF에서 생략할 수 있다.
4. Runtime 또는 memory가 central claim이 아니면 environment를 재현에 필요한
   수준으로만 보고한다.

### 6.2 Table S2와 S3 배치

#### S-01. Counterfactual table의 two-column 전환 `[x]`

**판단.** 건의사항은 합당하며 우선순위가 높다. Current page 1의 Table S2는
one-column 3열 표다. `Relation to verifier` 열이 단어 단위로 끊기고 세 family
rule을 읽으려면 줄을 여러 번 왕복해야 한다. 내용은 soundness와 construct
dependence에 중요하므로 삭제하거나 더 작은 font로 줄이는 것보다 two-column
배치가 낫다.

**권장안.**

- Table S2를 `table*`로 바꾸어 page 2 top에 배치한다.
- Columns은 `Family`, `Construction rule`, `Relation to verifier`를 유지한다.
- `\small`을 유지하고 width 확보를 위해 font를 줄이지 않는다.
- 첫 페이지 prose에는 `Table~\ref{tab:counterfactual-rules}` pointer만 남긴다.
- Table S2 뒤에 `\FloatBarrier`를 두거나 S3 placement를 제어해 PDF reading
  order에서 S3가 S2보다 먼저 보이지 않게 한다.
- 강제 `\newpage`는 page flow가 안정되지 않을 때만 사용한다.

**반영 결과.** Table S2를 `table*`로 바꾸어 PDF page 2 상단에 배치했다.
`\small`을 유지했으며 세 열의 설명이 단어 단위로 과도하게 끊기지 않는다.
강제 page break나 `\FloatBarrier` 없이도 Table S3보다 먼저 보이고 page 1의
본문 흐름을 해치지 않는다.

#### S-02. Information-use table의 one-column 전환 `[x]`

**판단.** Table S3는 7행의 Yes/No matrix라 one-column으로 바꾸기 적합하다.
현재 `table*`가 page 3 상단의 폭을 과도하게 사용한다.

**권장 heading.**

| 현재 | 권장 |
|---|---|
| `Information` | `Information` |
| `Training construction` | `Train` |
| `Primary verifier` | `Verifier` |
| `Point/mesh audit` | `Audit` |

Caption에서 `Train`, `Verifier`, `Audit`의 범위를 풀어 쓴다. Row labels도
`Evaluation candidates`, `Source score`, `Verifier labels`,
`OBB measurements`, `Point/mesh measurements`, `Evaluation scene identities`,
`Relation ontology`로 줄일 수 있다.

**반영 결과.** Table S3를 one-column 표로 전환하고 heading과 row label을
위와 같이 줄였다. Caption이 `Train`, `Verifier`, `Audit`의 범위를 정의하며,
Table S2 아래 page 2에서 읽기 쉬운 폭으로 배치된다.

### 6.3 Open3DSG와 SGFN checkpoint 표현

#### S-03. Open3DSG provenance `[x]`

현재 문장:

> Open3DSG uses the official non-averaged BLIP checkpoint
> `epoch=13-step=13104.ckpt`, selected using training and development losses.

**판단.** 저자가 official code/configuration으로 학습한 checkpoint라면
`official checkpoint`라고 부르면 안 된다. Exact local filename도 reviewer에게
stable provenance를 주지 않는다. 다만 학습·선택 protocol을 숨기면 안 된다.

**권장 문장.**

> We train Open3DSG using the official implementation and non-averaged BLIP
> configuration, and select the checkpoint using training and development
> losses only.

평가 labels로 checkpoint를 선택하지 않았다는 사실이 핵심이다. Exact filename,
run ID, hash는 internal manifest와 post-acceptance artifact에 유지한다. 실제
weight 공개는 upstream code/model/data terms를 확인한 뒤 결정하며, Technical
Supplement에서 공개를 약속할 필요는 없다.

**반영 결과.** Opaque local checkpoint filename과 `official checkpoint`
표현을 삭제했다. Official implementation과 non-averaged BLIP configuration으로
학습하고 training/development loss만으로 checkpoint를 선택했다는 protocol은
유지했다.

#### S-04. SGFN provenance `[x]`

현재 `SGFN_full_l160`이 공개 release의 stable identifier라면 유지해도 된다.
그렇지 않고 local filename이라면 다음처럼 configuration 중심으로 줄이는 편이
낫다.

> We evaluate the released SGFN checkpoint with its 160-object and
> 26-relation configuration on the same validation scenes and denominator.

Open3DSG와 SGFN을 같은 문장으로 처리하면 안 된다. 전자는 직접 학습한 model,
후자는 released checkpoint이므로 provenance가 다르다.

**반영 결과.** Local identifier 대신 released SGFN checkpoint와
160-object/26-relation configuration을 명시했다. Open3DSG의 직접 학습
provenance와 분리되어 있다.

### 6.4 Implementation and development diagnostics

#### S-05. Environment 정보량 축소 `[x]`

**판단.** Peak RSS 보고 자체가 top-tier 관행에 어긋나는 것은 아니다. 다만
accepted papers에서 peak memory는 memory efficiency나 deployment cost가
claim일 때 주로 보고된다. RelCompat3D의 core claim은 reliability이고
366.5 MiB는 baseline comparison이나 memory claim과 연결되지 않는다. 현재
paragraph는 over-showing에 가깝다.

**유지.**

- Pinned Docker environment
- Python과 핵심 numerical library version
- Re-ranking이 CPU-only라는 사실
- Runtime을 유지한다면 CPU model과 timing scope
- Source-predictor inference가 timing에서 제외된다는 boundary

**삭제 또는 내부 기록으로 이동.**

- Linux kernel version
- Pillow version
- Peak process memory 366.5 MiB

Runtime도 lightweight deployment claim을 하지 않을 경우 삭제 가능하다. 다만
1.81--2.45 s가 method의 practical overhead를 간단히 보여주므로 peak memory보다
유지 가치가 높다.

**반영 결과.** Linux kernel, Pillow와 peak memory를 삭제했다. Pinned Docker,
Python 3.11.9, NumPy 1.26.4, CPU execution, CPU model, timing scope와
source-predictor inference 제외 경계만 유지했다.

#### S-06. Development diagnostic 축소 `[x]`

**판단.** AUROC/Brier는 main claim에 직접 쓰이지 않는다. 특히 main이
compatibility를 posterior probability로 해석하지 않는다고 밝히므로 Brier를
강조하면 calibration claim으로 오독될 수 있다.

**유지.**

- Applicable transformation identities의 numerical check
- Linked positive--counterfactual ordering check
- Validation results가 fixed evaluation protocol에서 나온다는 boundary

**삭제 또는 Section D로 이동.**

- Aggregate AUROC/Brier pair
- `optimization validity`처럼 넓은 해석

권장 compact prose:

> All RelCompat3D jobs use a pinned Docker image with Python 3.11.9 and
> NumPy 1.26.4. Re-ranking runs on CPU. Five runs take 1.81--2.45 seconds per
> predictor on an Intel Core Ultra 7 265KF, excluding source-predictor
> inference. Development checks verify the applicable transformation identities
> to numerical precision and a 99.23\% linked-pair ordering rate for the MLP.

**반영 결과.** Environment/development subsection에는 transformation identity,
MLP linked-pair ordering과 fixed evaluation protocol만 남겼다. Development-only
AUROC/Brier 수치도 삭제했으며, re-ranking 결과를 직접 보여주는 component와
feature-removal evidence는 유지했다.

#### S-08. Primary verifier specification `[x]`

**판단.** Main은 Violation의 denominator와 uncertainty 처리를 정의하지만,
Technical Supplement에는 frozen primary verifier의 family별 전체 status
boundary가 없었다. Code and Data Supplement를 제출하지 않는 현재 review
설정에서는 compact specification을 두는 것이 reproducibility와 metric
transparency에 도움이 된다.

**반영 결과.** `Reproducibility and Experimental Setup`에 Table S5와
support/contact score definition을 추가했다. Proximity와 vertical order의
OBB measurements, support/contact의 instance-point subtype score,
`satisfied / uncertain / violated` threshold, missing-evidence 처리와
out-of-scope exclusion을 명시했다. Table S2는 training counterfactual
construction, Table S5는 evaluation status rule이라는 차이도 분명히 했다.
Compatibility estimator나 training target으로 오해하지 않도록 caption과 prose에
claim boundary를 유지했다.

### 6.5 전체 Table terminology와 width

Accepted papers에 특정 column vocabulary를 강제하는 규정은 없다. `Method`,
`Model`, `Predictor`, `Condition`, `Setting`, `Feature`, `Definition`,
`Metric`, `Recall`, `Runtime`, `Memory`는 일반적이다. 중요한 기준은 main
terminology와 일치하고 caption만으로 의미를 복원할 수 있는지다.

#### 현재 그대로 사용해도 되는 headings

- `Symbol`, `Meaning`
- `Family`, `Feature`, `Definition`
- `Predictor`, `Estimator`, `Condition`
- `Ranking rule`, `Re-ranking`
- `Selected`, `Share`, \(\Delta R\), \(\Delta V\)
- \(K\), R@\(K\), V@\(K\)

#### 수정 권장 headings

| Table | 현재 | 권장 | 이유 |
|---|---|---|---|
| S3 | `Training construction / Primary verifier / Point/mesh audit` | `Train / Verifier / Audit` | One-column 전환 |
| S7 | `Min Jaccard / Min. exact-context rate` | `Min. top-\(K\) overlap / Min. exact agreement` | Jaccard score와 exact set agreement를 caption에서 직접 정의 |
| S8 | 긴 removal condition | `No verifier scalar / No related measurements / Alternative evidence` | One-column 줄바꿈 축소 |
| S10 | `Both` | `Pass` | 두 방향 조건을 함께 만족하는 count임을 caption에서 정의 |
| S16 | `Dec. cov.` | 유지 | Caption에서 decidable coverage를 정의함 |

#### One-column layout 원칙

- Definition table에서 설명이 여러 줄이 되는 것은 자연스럽다. 모든 row를
  억지로 한 줄로 만들기 위해 font를 줄이면 안 된다.
- Result table의 method/condition label은 가능하면 한 줄로 둔다.
- Table S8의 긴 labels는 `No verifier scalar`, `No related measurements`,
  `Alternative evidence`로 줄이고 caption에서 정의하면 one-column을 유지할 수
  있다. 그래도 wrap되면 `table*` 전환이 낫다.
- Table S15처럼 수치 열이 많은 one-column table은 abbreviation을 caption에서
  정확히 정의하고 실제 PDF에서 9-point readability와 column collision을
  확인한다.
- Table S1처럼 `Symbol--Meaning` 구조에서 Meaning이 여러 줄인 것은 문제가
  아니다. 이 표의 목적이 정의이기 때문이다.

### 6.6 Figure S1의 main-case 중복

#### S-07. Proximity panel 중복 처리 `[x]`

**판단.** Panel (a)의 `heater / close by / trash can`은 main Figure 2와 같은
case라 additional qualitative evidence로서의 가치가 낮다. 규정 위반이나
factual error는 아니지만 supplement가 main을 확장한다는 목적에는 다른 case가
더 낫다.

**가장 권장하는 대체 case.**

- `desk close by chair`, Source rank 81 \(\rightarrow\) Linear rank 30
- Exact-label, verifier-satisfied promotion
- Main의 two demotions와 반대 방향의 top-50 membership change를 보여주므로
  선택 편향에 대한 방어 효과가 크다.

현재 supplement prose에는 이 case의 rank와 XY distance가 있지만, frozen
figure-ready pair geometry record는 현재 active tree에서 확인되지 않았다.
따라서 숫자만으로 panel을 임의 생성하면 안 된다. Canonical candidate row,
exact candidate identity, source/method ranks, verifier status를 다시 고정하고
licensed geometry에서 projection을 생성해야 한다.

현재 archive에서 바로 사용 가능한 active qualitative records는 다음 세 개뿐이다.

1. Heater--trash-can proximity demotion
2. Floor--curtain vertical demotion
3. Door--floor support/contact preservation

H002 또는 superseded historical cases는 현재 RelCompat3D evidence로 사용하지
않는다.

**시간 내 새 panel을 검증하지 못할 경우.**

- Current panel을 유지해도 submission blocker는 아니다.
- `(a) Proximity correction`을 `(a) Proximity demotion`으로 바꾸면 outcome이
  더 정확하다.
- Figure의 목적을 새 사례 제시가 아니라 main proximity case의
  pair--evidence--outcome decomposition으로 명시한다.

**반영 결과.** 검증되지 않은 promotion geometry를 새로 만들지 않았다. Existing
verified panel을 유지하고 `(a) Proximity correction`을
`(a) Proximity demotion`으로 바꿨다. Figure S1은 main case를 반복해 성능
evidence를 늘리는 그림이 아니라, measured evidence와 rank outcome을 한 패널에서
분해해 보여주는 보충 설명으로 사용한다.

### 6.7 정보 밀도와 권장 최종 구조

Current A--C order를 유지한다.

#### A. Supplementary Method Details

1. Notation
2. Counterfactual construction
3. Separation of training and evaluation information
4. Estimator and feature specification
5. Formal properties

#### B. Reproducibility and Experimental Setup

1. Split, predictors, evaluation scope
2. Concise preprocessing and checkpoint provenance
3. Compact implementation environment

#### C. Additional Results Supporting Main Claims

1. Component and feature removals
2. Alternative-geometry audit
3. Qualitative pair analysis
4. Score, baseline, routing sensitivities
5. Paired intervals, family composition, uncertainty sensitivity
6. Seed and construction robustness

Reviewer가 읽을 우선순위가 분명하도록 C의 각 subsection은 setup 1--2문장,
핵심 pattern 1개, claim boundary 1문장만 남긴다. Table의 모든 cell을 prose로
반복하지 않는다. Full grids, hashes, artifact inventories는 internal
post-acceptance material이 소유한다.

### 6.8 1차 개선 우선순위

| 우선순위 | 작업 | 이유 |
|---:|---|---|
| 완료 | Table S2를 page 2의 `table*`로 이동하고 S3를 one-column으로 전환 | PDF 배치와 readability 확인 |
| 완료 | Open3DSG를 official implementation/configuration으로 학습한 model로 쓰고 opaque filename 삭제 | Provenance 정확성 확보 |
| 완료 | Peak RSS, kernel, Pillow, development-only AUROC/Brier를 삭제 | 정보 밀도와 claim alignment 개선 |
| 완료 | S6/S8/S9/S15 headings와 one-column labels 정리 | Table terminology 통일 |
| 완료 | Figure S1의 verified panel을 유지하고 `Proximity demotion`으로 명명 | 검증되지 않은 새 evidence 생성 방지 |

### 6.9 최종 체크리스트

#### 구조와 구성

| 항목 | 상태 | 판정 |
|---|---|---|
| Main 참조 순서 | `[x]` | A Method, B setup, C main-supporting results와 secondary checks 순서 |
| Numbering | `[x]` | TOC override 없이 A/A.1와 S-table/S-figure numbering 사용 |
| Table S2/S3 실제 배치 | `[x]` | S2는 page 2 상단의 two-column, S3는 같은 page의 one-column 표로 확인 |
| Main--supplement cross-reference | `[x]` | Main pointers의 evidence가 supplement에 존재 |
| AAAI 규정 | `[x]` | Anonymous Technical Supplement, author-owned web pointer 없음 |

#### 재현성

| 항목 | 상태 | 판정 |
|---|---|---|
| Architecture와 optimization | `[x]` | Linear/MLP architecture, parameter 수, optimizer, steps, LR, loss가 있음 |
| Feature specification | `[x]` | 17 measurements와 missing-value rule이 있음 |
| Split와 preprocessing | `[x]` | 1,061/117/157 scans, 548 contexts, 3,972 GT와 source preprocessing이 있음 |
| Checkpoint provenance | `[x]` | Open3DSG 직접 학습 protocol과 released SGFN configuration을 구분 |
| Environment | `[x]` | Pinned Docker, Python, NumPy와 source-predictor execution boundary만 유지 |
| Primary verifier | `[x]` | Family별 measurement, status threshold, missing-evidence 처리와 training-construction 분리를 Table S5에 명시 |
| Statistical procedure | `[x]` | 1,000 paired scan-level bootstrap이 명시됨 |
| Code/data boundary | `[x]` | Review에는 Technical Supplement만 제출하고 licensed assets는 재배포하지 않음 |

#### 정확성과 가독성

| 항목 | 상태 | 판정 |
|---|---|---|
| Main claim과 수치 | `[x]` | Main compact statements, controls, audit와 일치 |
| Ablation definitions | `[x]` | Changed component와 fixed protocol을 구분 |
| Table terminology | `[x]` | `Min. top-\(K\) overlap`, `Min. exact agreement`, `Pass`, `Ranking rule`로 국소 교정 |
| One-column readability | `[x]` | S2/S3 폭을 교환했고 최신 PDF에서 collision과 overfull이 없음 |
| Figure S1 역할 | `[x]` | Verified `desk close by chair` promotion과 vertical demotion, support/contact preservation을 함께 제시 |
| Supplement standalone readability | `[x]` | Notation, method, split, metrics와 experiment scope를 복원 가능 |

### 6.10 1차 판정

초기 다섯 건의사항과 primary-verifier specification을 모두 반영했다. Table S2/S3의 폭 교환과 checkpoint provenance
교정이 가장 큰 가독성·정확성 개선이었다. Environment와 development diagnostics는
core claim에 필요한 범위로 줄였고 table terminology를 국소 교정했다. Figure S1은
검증된 record만 사용한다는 원칙을 우선해 proximity promotion case를
반영했다. 최신 supplement는 9-page US Letter이며
overfull box, undefined reference와 undefined citation이 없다.

### 6.11 2차 가독성 개선 반영

Accepted supplement의 equation/table 관행과 current PDF를 대조한 뒤 다음을
반영했다.

1. Table S7의 두 set diagnostic을 `Min. top-\(K\) overlap`과
   `Min. exact agreement`로 명명했다. Caption은 top-\(K\) overlap을 Jaccard
   score로 정의하고, exact agreement를 두 selected set이 완전히 같은
   context의 비율로 정의한다.
2. Table S8의 condition을 `Full`, `No verifier scalar`,
   `No related measurements`, `Alternative evidence`로 줄였다. 제거되는
   measurement의 범위는 caption에 유지했다.
3. Table S14는 각 bracket을 paired 95\% `bootstrap confidence interval`로
   명시했다. 비대칭 interval이므로 lower/upper bracket 표기를 유지했다.
4. Table S7 아래에서 `.9635`와 `.6975`를 반복하던 문장을 삭제했다.
   Transformation averaging이 exact consistency를 만든다는 해석과 aggregate
   effect boundary만 남겼다.
5. 다른 result table 주변 prose도 점검했다. Score-mapping paragraph에서는
   Table S10의 pass count와 worst change를 그대로 반복하지 않고 exception의
   위치와 해석만 남겼다. Routing paragraph에서는 Table S13에서 계산되는
   Recall 차이를 삭제하고 방향과 composition mechanism만 유지했다.
   Uncertainty paragraph에서는 Table S16의 predictor별 delta를 삭제하고
   interval 방향과 all-\(K\) conclusion만 유지했다. Table에 없는
   linked-pair diagnostic, rank-stability, coverage, qualitative geometry와
   selected-family count는 재현성과 mechanism 설명에 필요하므로 유지했다.
6. Primary-verifier score와 stress-test grid의 수치는 frozen evaluation
   protocol을 정확히 정의하므로 유지했다. General method objective는 main과
   동일하게 symbolic form과 별도 implementation values를 사용한다.
7. Docker clean build 결과는 9-page US-Letter PDF다. Undefined
   reference/citation, overfull box, inclusion warning은 없으며 모든 font가
   embedded되어 있다. Canonical Technical Supplement의 SHA-256은
   `2f7ca7f7c7cadd2dff763b23c76a2d1d20a26033706ff990aacd1908cba121c5`다.

### 6.12 Supplement transcript 통일 및 가독성 `[x]`

`paper/aaai/sec/supplement.tex` 전체를 두 차례 검토하고 권장 사항을 모두
반영했다. 해결된 세부 권장문장은 삭제하고 최종 판정만 유지한다.

- `[x]` **Claim boundary:** 독립적인 물리적 정답을 암시하던 표현을
  `ground truth for geometric validity`와 `evidence of geometric validity`로
  제한해 main의 claim 범위와 맞췄다.
- `[x]` **Main 용어 통일:** `ordered pair`, `measurements`,
  `relation-preserving augmentation`, `signed-height interactions`,
  `Point- and Mesh-Based Consistency Audit`, `robust-density baseline`,
  `matched MLP controls`, `Product (all families)`를 main과 동일하게
  사용한다.
- `[x]` **직접적이고 쉬운 영어:** 추상적인 진단 표현과 인위적인 문구를
  condition, metric, protocol을 직접 설명하는 문장으로 교체했다. 불필요한
  `cap`, `blanket`, `comprise`, `nonconstant`, `eligible`,
  `subtype`, `pseudonymized`, `membership`, `non-tied`,
  `corrupted`, `permits`, `bijection`, `singleton` 표현도
  쉬운 문장으로 정리했다.
- `[x]` **수학적 정확성:** finite transformation group, orbit,
  re-indexing proof, prefix utility, sigmoid, logit, softplus,
  interquartile range, Kendall correlation, top-\(K\) set overlap, bootstrap,
  monotonic mapping, percentile mapping 등 정의나 검증에 필요한 용어는
  유지했다.
- `[x]` **Protocol 정확성:** Table S15는 point estimate만 보고하도록
  설명을 바로잡았고, 사용하지 않은 context-level bootstrap 표현을 삭제했다.
  Counterfactual construction과 verifier 규칙은 threshold와 uncertain 처리를
  직접 설명한다.
- `[x]` **정보 밀도:** 표와 중복되는 수치 재진술, 비핵심 runtime 범위,
  내부 artifact 용어를 제거했다. Score range와 verifier threshold처럼
  재현성과 scoring-rule 해석에 필요한 수치는 유지했다.
- `[x]` **표 강조 규칙:** 직접 비교 가능한 predictor와 matched condition
  안에서 metric별 최선 값을 bold 처리하고 동률도 모두 표시했다. Recall,
  Violation, coverage, uncertainty와 change metric의 방향은 caption 또는
  Section C의 공통 규칙으로 명시했다. Relation family나 성격이 다른
  diagnostic을 억지로 비교하지 않았다.
- `[x]` **추가 문체 정리:** `Pair--evidence--outcome analysis`,
  `routing-constraint controls`, `no-pairwise refits`처럼 인위적이거나
  내부적인 표현을 각각 `Qualitative ordered-pair examples`, `matched routing
  controls`, `models trained without the pairwise loss`로 바꿨다.
  `relation-family label` 표현도 main과 통일했다.
- `[x]` **내부 기록 제거:** Exact seed IDs, timed-run 범위와 CPU 모델,
  development-only diagnostic 수치, derived-row regeneration 기록, 표 없이
  남아 있던 pooled/recovery 수치를 Technical Supplement에서 삭제했다.
- `[x]` **Build 검증:** Technical Supplement는 9-page US-Letter PDF이며
  undefined citation/reference, overfull box, graphics inclusion warning이 없다.
  Canonical SHA-256은
  `2f7ca7f7c7cadd2dff763b23c76a2d1d20a26033706ff990aacd1908cba121c5`이다.
- `[x]` **수정 범위:** Main source와 main PDF는 변경하지 않았다.

### 6.13 최종 권장 사항 1--5 반영 `[x]`

1. `[x]` **Table 순서와 배치:** 최신 PDF의 column-wise reading order에서
   Table S1--S16이 번호 순서대로 나타난다. Page 6에는 Table S9,
   Figure S1, Table S10이 배치되고, page 7에는 Tables S11--S13만 배치된다.
   Point/mesh audit, qualitative analysis, score-mapping protocol을 page 5로
   앞당겨 강제 page break 앞의 큰 공백을 제거했다. Table S14도 page 8로
   당겨져 paragraph 간격이 자연스러워졌고, 나머지 결과는 page 9에서 이어진다.
2. `[x]` **Main 용어 정합성:** `source relation score`,
   `point- and mesh-based audit`, `counterfactual construction`, `validation
   scenes`로 통일했다.
3. `[x]` **Robustness protocol:** 다섯 pre-specified seeds와 negatives per
   positive, pairwise weight, proximity-negative threshold, vertical absolute
   margin의 여덟 one-factor conditions를 명시했다. 내부 seed ID는 삭제했다.
4. `[x]` **Metric 단위:** Recall, Violation, coverage는 percentage로,
   Source 대비 변화는 percentage points로 명시했다. Compatibility와 set
   agreement diagnostic은 단위 없는 score로 유지했다.
5. `[x]` **마지막 페이지:** 별도 Section D를 제거하고 secondary robustness와
   scope checks를 Section C의 마지막 paragraph로 병합했다. AAAI가
   `balance` package를 금지하므로 허용된 two-column flow를 유지했다.

## 7. 장문과 비일반 용어 최종 점검

### 7.1 전체 판정

- `[x]` **치명적인 장문 없음:** Main의 일반 prose는 대부분 30단어 미만이다.
  32--37단어 문장은 주로 notation이나 metric을 정의하며, 수식과 바로 연결되어
  있어 길이만으로 문제가 되지 않는다.
- `[~]` **Main의 선택적 개선:** Method의 notation 문장 두 개는 정확하지만 한
  문장에 기호 정의와 역할 설명이 함께 들어간다. Main은 제출 후 동결되었으므로
  현재 PDF를 다시 열 정도의 오류는 아니다.
- `[x]` **Supplement의 경미한 개선:** robustness setting, routing count,
  robust-density comparison, uncertainty caption을 짧은 문장으로 나눴다.
  수치와 claim boundary는 유지했다.
- `[x]` **Table S14 정렬:** `R@50`과 `V@50` 열을 오른쪽 정렬에서 중앙 정렬로
  바꿨다. Header, point estimate, confidence interval이 각 metric 열의 중앙을
  공유한다.
- `[x]` **숫자 정보의 필요성:** verifier threshold, 학습 hyperparameter,
  source-score range, split size, bootstrap 횟수와 routing selected count는
  evaluation 재현 또는 claim 해석에 직접 필요하다. 내부 날짜, seed ID,
  runtime log와 중복 table 수치는 남아 있지 않다.

### 7.2 Main의 긴 문장

#### L-M1. Method / Problem Formulation, line 8 `[선택]`

원문:

> We distinguish the ordered-pair identity
> \(k^{\rm pair}_i=(\mathrm{scan}_i,\mathrm{context}_i,s_i,o_i)\) from the exact
> relation-candidate identity
> \(k^{\rm rel}_i=(\mathrm{scan}_i,\mathrm{context}_i,s_i,p_i,o_i)\) used for
> evaluation.

판정: 약 37단어이며 두 identity와 evaluation 역할을 한 번에 정의한다. 수학적으로
정확하지만 처음 읽는 독자는 두 tuple의 차이를 다시 확인할 수 있다.

권장안:

> The ordered-pair identity is
> \(k^{\rm pair}_i=(\mathrm{scan}_i,\mathrm{context}_i,s_i,o_i)\). The exact
> relation-candidate identity used for evaluation is
> \(k^{\rm rel}_i=(\mathrm{scan}_i,\mathrm{context}_i,s_i,p_i,o_i)\).

#### L-M2. Method / Linear Estimator, line 77 `[선택]`

원문:

> The family label \(a_i\) selects the linear head and training-split
> normalization statistics but is not included as a constant input:
> \(f_{\rm lin}(T_i,a_i,G_i)=w_{a_i}^\top\Phi_{\rm lin}(T_i,G_i)\).

판정: 약 37단어이며 selection 역할과 input exclusion, 수식을 한 문장에 넣는다.
의미는 명확하므로 필수 수정은 아니다.

권장안:

> The family label \(a_i\) selects the linear head and training-split
> normalization statistics. It is not included as a constant input, so
> \(f_{\rm lin}(T_i,a_i,G_i)=w_{a_i}^\top\Phi_{\rm lin}(T_i,G_i)\).

#### 유지해도 되는 긴 문장 `[x]`

- Method line 6의 candidate-field 정의는 하나의 tuple을 순서대로 설명하므로
  현재 구성이 더 간결하다.
- Experiments line 24의 \(D_K,N_s,N_u,N_v\) 정의는 바로 뒤의 Violation 수식과
  연결되므로 분할 이득이 작다.
- Results line 34의 33단어 문장은 Table 1과 Figure 3의 핵심 결론을 한 번에
  요약한다. 절 구조가 단순하고 claim boundary도 정확하다.
- Abstract의 가장 긴 문장들은 약 29단어이며 문제, inference, 결과를 각각 한
  문장씩 담당한다. 현재 호흡을 유지해도 된다.

### 7.3 Supplement의 긴 문장

#### L-S1. Additional Robustness Checks, line 704 `[x]`

원문:

> We also vary one setting at a time relative to the reported configuration:
> negatives per positive in \(\{1,4\}\) instead of 2, pairwise weight in
> \(\{0.125,0.5\}\) instead of 0.25, proximity-negative threshold in
> \(\{2.0,3.0\}\) instead of 2.5, and vertical absolute margin in
> \(\{0.20,0.30\}\,\mathrm m\) instead of \(0.25\,\mathrm m\).

판정: 네 parameter와 각 기준값을 한 문장에 넣어 현재 supplement에서 가장
호흡이 긴 일반 prose다. 수치는 필요하지만 문장 구조는 나눌 수 있다.

권장안:

> We vary four settings one at a time. For negatives per positive and the
> pairwise weight, we test \(\{1,4\}\) and \(\{0.125,0.5\}\), compared with
> 2 and 0.25. For the proximity-negative threshold and vertical absolute
> margin, we test \(\{2.0,3.0\}\) and
> \(\{0.20,0.30\}\,\mathrm m\), compared with 2.5 and
> \(0.25\,\mathrm m\).

반영 완료. 네 setting을 세 문장으로 나눠 기준값과 비교값을 구분했다.

#### L-S2. Routing Controls, line 596 `[x]`

원문:

> At Open3DSG \(K=50\), the MLP control changes the selected
> proximity/vertical-order counts from 6,295/6,508 to 3,423/9,380 while
> leaving all 13,833 support/contact selections unchanged.

권장안:

> At Open3DSG \(K=50\), the MLP control changes the selected
> proximity/vertical-order counts from 6,295/6,508 to 3,423/9,380. All 13,833
> support/contact selections remain unchanged.

반영 완료. 선택 수 변화와 support/contact 보존을 별도 문장으로 분리했다.

#### L-S3. Robust-Density Baseline, line 575 `[x]`

원문:

> The baseline improves both metrics over a learned estimator only for MLP on
> Open3DSG at \(K=5\); the other comparisons favor a learned estimator on both
> metrics or show a trade-off.

권장안:

> The baseline improves both metrics over a learned estimator only for MLP on
> Open3DSG at \(K=5\). The remaining comparisons favor a learned estimator on
> both metrics or show a trade-off.

반영 완료. 유일한 예외와 나머지 비교를 별도 문장으로 분리했다.

#### L-S4. Table S16 Caption, line 694 `[x]`

원문:

> \(V_{\rm all}\) is the reported Violation, \(V_{\rm dec}\) is decidable-only
> Violation, \(U\) is the uncertain fraction, and \(V_{u\to v}\) counts
> uncertain candidates as violations.

권장안:

> \(V_{\rm all}\) is the reported Violation, and \(V_{\rm dec}\) is
> decidable-only Violation. \(U\) is the uncertain fraction.
> \(V_{u\to v}\) counts uncertain candidates as violations.

반영 완료. 네 metric 정의를 세 문장으로 나눴다.

### 7.4 비일반적이거나 내부적으로 보일 수 있는 표현

| 위치 | 현재 표현 | 판정 | 권장 표현 또는 처리 |
|---|---|---|---|
| Main Results line 40 | `Source-relative conclusion` | 의미는 알 수 있지만 일반적인 collocation은 아님 | `The comparison with Source remains unchanged ...` |
| Main Results line 40 | `composition-preserving constraint`, `aggregate-optimal rule` | claim은 정확하지만 두 compound가 연속되어 인위적으로 보일 수 있음 | `We therefore treat family-aware re-ranking as preserving relation-family composition rather than maximizing aggregate performance.` |
| Main Discussion line 3 | `grounded relation ranking` | 별도 task로 정의되지 않아 다소 추상적임 | `ranking relations linked to scene geometry` |
| Supplement Formal Properties line 165 | `Prefix utility optimality` | 내부 theorem 이름처럼 들림 | `[x]` `Optimality for each prefix`로 수정 |
| Supplement Architecture line 147 | `full-batch gradient-descent steps` | `gradient descent`는 보통 하이픈 없이 씀 | `[x]` `full-batch gradient descent steps`로 수정 |
| Supplement routing table/prose | `Joint P/V` | 표 너비에는 적합하지만 첫 독자에게 즉시 명확하지 않을 수 있음 | `[x]` 첫 prose 언급에서 `joint proximity/vertical control (Joint P/V)`로 정의하고 표에서는 유지 |

### 7.5 유지해야 하는 전문 용어 `[x]`

다음 표현은 일반 독자에게 전문적으로 보일 수 있지만 방법이나 평가를 정확히
정의하므로 쉬운 일반어로 바꾸지 않는다.

- `predicate--geometry compatibility`, `ordered-pair identity`,
  `family-aware re-ranking`, `verifier-derived Violation`은 논문의 핵심 용어다.
- `counterfactual`, `transformation averaging`, `transformation group`,
  `transformation orbit`, `sigmoid`, `softplus`, `ReLU`는 Method에서 정의된다.
- `bootstrap confidence interval`, `interquartile range`, `Kendall rank
  correlation`, `Jaccard score`, `percentile mapping`은 표준 통계 또는 ranking
  용어이며 Supplement에서 역할을 설명한다.
- `decidable-only Violation`과 `uncertain-as-violation`은 일반 benchmark
  명칭은 아니지만 정의가 바로 제공되므로 현재 표현이 가장 직접적이다.
- `robust-density baseline`은 새 comparator의 이름이지만, 계산 방식이 첫
  문장에서 정의되어 있어 내부 코드명으로 보이지 않는다.

### 7.6 우선순위

1. `[x]` L-S1--L-S4, `full-batch gradient descent`, formal-property 제목,
   Joint P/V 최초 정의를 모두 반영했다.
2. `[x]` Table S14의 두 metric 열을 중앙 정렬하고 최종 PDF에서 header와 값의
   정렬을 확인했다.
3. Main 관련 표현은 이미 제출된 source를 다시 열 정도의 오류가 아니다.
   향후 camera-ready에서만 반영하면 충분하다.
