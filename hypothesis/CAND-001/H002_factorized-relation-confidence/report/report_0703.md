# H002 Report 0703: Score Extraction and Main Validation Table Review

## 1. 목적

이 문서는 현재 H002에서 score를 어떻게 만들고, 어떤 파일에서 어떤 정보를
읽어 비교하는지 정리한다. 또한 `main_validation_table` materialization 이후
paper draft에 넣기 전에 필요한 review gate 결과를 기록한다.

현재 H002의 paper-facing claim은 다음으로 제한한다.

```text
official 3DSSG validation split에서
VL-SAT / Open3DSG validation predictions를 대상으로
source score baseline S0와 compatibility-aware reranking S2를 비교한다.
```

공식 test, leaderboard, SOTA, unconstrained open-set GT claim은 현재 금지한다.

## 2. H002 Score 구조

H002는 relation source가 준 score를 곧바로 relation reliability로 보지 않는다.
대신 edge 정보를 다음처럼 분리한다.

```text
T_e = predicate / relation-family semantic content
G_e = predicate-independent geometry evidence
Z_e = source confidence, score, rank
C_e = compatibility(T_e, G_e)
S2(e) = normalized_source_score(Z_e) * normalized_C_e(e)
```

중요한 원칙:

- `C_e`를 만들 때는 `T_e + G_e`만 사용한다.
- `Z_e`는 `C_e` 내부에 넣지 않는다.
- `Z_e`는 최종 reranking score `S2_source_x_Ce`를 만들 때만 결합한다.
- GT match, violation label, H001 `p_geom_valid`, hidden construction field는
  model input에 들어가지 않는다.

## 3. 데이터와 파일 흐름

### 3.1 Source-wide row materialization

실행 코드:

```text
experiments/H002_compatibility_routing/scripts/materialize_source_reranking_candidates.py
```

출력 위치:

```text
experiments/H002_compatibility_routing/source_reranking_materialization/latest/
```

핵심 파일:

| File | 역할 |
| --- | --- |
| `model_safe_ce_view.jsonl` | `C_e` 학습/추론용 `T_e + G_e` view |
| `model_safe_geometry_only_view.jsonl` | geometry-only diagnostic view |
| `source_rank_view.jsonl` | `Z_e` source score/rank view |
| `hidden_metric_manifest.jsonl` | GT match / violation metric-only view |

`model_safe_ce_view.jsonl`와 `source_rank_view.jsonl`를 분리하는 이유는
compatibility score가 source score shortcut을 복사하지 못하게 하기 위해서다.

### 3.2 Schema audit

실행 코드:

```text
experiments/H002_compatibility_routing/scripts/audit_source_reranking_materialization_schema.py
```

출력 위치:

```text
experiments/H002_compatibility_routing/source_reranking_schema_audit/latest/
```

검사 내용:

- `model_safe_ce_view`에 `Z_e`, GT, violation, H001 `p_geom_valid`가 없는지 확인한다.
- `source_rank_view`가 source score/rank만 담당하는지 확인한다.
- `hidden_metric_manifest`가 metric-only로 분리되어 있는지 확인한다.
- primary success aggregation이 `relative_vertical + size_relative`로 고정됐는지 확인한다.

### 3.3 Score runner

실행 코드:

```text
experiments/H002_compatibility_routing/scripts/run_source_reranking_metric.py
```

출력 위치:

```text
experiments/H002_compatibility_routing/source_reranking_evaluation/latest/
```

핵심 파일:

| File | 역할 |
| --- | --- |
| `score_manifest.json` | score 정의, normalization, row count, score bounds |
| `score_condition_metrics.csv` | aggregate metric by score condition |
| `source_family_metrics.csv` | source/family/K별 metric |
| `control_metrics.csv` | S2와 S0/S1/control 비교 |
| `selected_predictions.jsonl` | score별 top-K selected prediction rows |

`C_e` scorer는 internal train split에서 fit하고, official validation source rows는
eval-only로 사용한다.

## 4. 비교하는 Score ID

`run_source_reranking_metric.py`가 비교하는 score는 다음이다.

| Score ID | 의미 | Paper에서의 위치 |
| --- | --- | --- |
| `S0_source_score` | 기존 relation source score baseline | main baseline |
| `S1_Ce_only` | source score 없이 `C_e`만 사용 | diagnostic ablation |
| `S2_source_x_Ce` | normalized source score와 `C_e` 곱 | H002 main score |
| `S3_log_source_plus_Ce` | log-source + log-`C_e` diagnostic | formula-equivalent diagnostic |
| `C1_source_x_shuffled_Ce` | shuffled geometry/compatibility control | supporting control |
| `C2_source_x_wrong_T_Ce` | wrong predicate semantic control | supporting control |

최종 paper-facing 비교는 주로 다음이다.

```text
S0_source_score vs S2_source_x_Ce
```

즉, 기존 source ranking을 그대로 쓰는 경우와, H002 compatibility score를
곱해 reranking하는 경우를 같은 candidate pool에서 비교한다.

## 5. Geometry-only는 무엇인가

H002에서 geometry-only는 두 층위가 있다.

첫째, route/family mechanism evaluation의 geometry-only model이다.

```text
experiments/H002_compatibility_routing/scripts/run_official_metric.py
M2_G_geometry_only
```

이것은 `G_e`만으로 label을 맞출 수 있는지 보는 baseline이다. `T_e x G_e`
compatibility가 단순 geometry rule보다 나은지 확인하는 데 쓴다.

둘째, source-reranking materialization의 geometry-only diagnostic view다.

```text
source_reranking_materialization/latest/model_safe_geometry_only_view.jsonl
```

이 view는 schema separation과 diagnostic 분석용이다. 현재 main source-reranking
table의 deployable score는 geometry-only가 아니라 `S2_source_x_Ce`다.

따라서 paper에서 geometry-only를 말할 때는 어느 층위인지 분리해야 한다.

## 6. Metric 계산 방식

같은 source candidate pool을 score별로 정렬하고 K = `{5, 10, 20, 50, 100}`에서
top-K를 선택한다.

```text
Recall@K = selected GT-matching relation / total GT relation
Violation@K = geometry-violating selected relation / violation-checkable selected relation
```

현재 main validation table은 primary success families만 aggregate한다.

```text
primary_success_families = relative_vertical + size_relative
```

`support_contact`는 diagnostic/failure taxonomy로 유지하고, primary success
aggregation에는 넣지 않는다.

## 7. Main Validation Table Review 결과

Review artifact:

```text
artifacts/compatibility_dataset_v3_main_validation_table_review_after_materialization/
```

결과:

```text
status = h002_main_validation_table_review_after_materialization_ready
validation_errors = 0
selected_path = main_validation_table_reviewed_select_paper_insertion_plan
next_todo = compatibility_dataset_v3_paper_draft_insertion_plan_after_main_validation_table_review
```

Main validation table은 다음 패턴을 보인다.

| K | Delta Recall@K | Delta Violation@K |
| ---: | ---: | ---: |
| 5 | +0.007937 | -0.240690 |
| 10 | +0.041950 | -0.229859 |
| 20 | +0.081633 | -0.243091 |
| 50 | +0.103175 | -0.259199 |
| 100 | +0.004535 | -0.142873 |

해석:

- primary success families에서는 모든 K에서 Recall@K가 증가하고 Violation@K가 감소한다.
- 이 결과는 `S2_source_x_Ce`가 source score baseline보다 좋은 validation-level
  recall/violation tradeoff를 만든다는 근거다.
- 하지만 source/family/K 세부 셀 3개에서 작은 Recall@K regression이 있으므로
  uniform improvement claim은 금지한다.

필수 caveat:

| source_id | route_family | K | Delta Recall@K |
| --- | --- | ---: | ---: |
| `open3dsg_recovery_relaxed_views_min2` | `size_relative` | 5 | -0.010204 |
| `vlsat_full_validation` | `relative_vertical` | 5 | -0.017949 |
| `vlsat_full_validation` | `size_relative` | 50 | -0.011765 |

## 8. Control 해석

Control rows는 H002 주장을 보조하지만, 표현을 조심해야 한다.

- `C_e only`는 매우 낮은 violation을 만들 수 있지만 low-K recall이 낮다.
  따라서 deployable score가 아니라 diagnostic ablation이다.
- `source x shuffled C_e`와 `source x wrong-T C_e`는 `S2`보다 violation-risk ranking이
  나빠진다.
- 다만 paper에서는 "모든 control이 recall에서 collapse한다"라고 쓰면 안 된다.
  더 정확한 표현은 "wrong-T / shuffled-C_e controls worsen compatibility-specific
  violation-risk ranking"이다.

## 9. 현재 결론

현재 H002 main validation table은 paper draft에 넣을 후보로 사용할 수 있다.
단, 다음 boundary를 지켜야 한다.

- official 3DSSG validation split 결과로만 표현한다.
- official test, SOTA, leaderboard wording은 금지한다.
- Open3DSG는 open-vocabulary source지만 정량 Recall@K는 closed 3DSSG mapping 기준이라고 쓴다.
- 3개 Recall@K regression caveat를 숨기지 않는다.
- `C_e only`를 main method처럼 쓰지 않는다.
- `p_obs/p_rel`은 H002 main framework의 selective decision layer로 포함할 수
  있지만, 별도 정량 result claim은 추가 protocol이 필요하다.
- H003 embedding은 H002의 CI, qualitative example, failure taxonomy 정리 이후
  future/optional extension으로 둔다.

paper draft insertion plan은 생성됐다. 다음 H002 TODO는 이 H002 결과를 독립
paper claim으로 가져갈지, H001/H002 manuscript의 method/result section에
통합할지 결정하는 단계다.

## 10. H002 Paper Claim 가능성에 대한 판단

내 판단은 다음이다.

```text
H002는 paper claim 가능성이 있다.
다만 broad 3D Scene Graph SOTA claim이 아니라,
relation reliability layer / compatibility-aware reranking claim으로 제한해야 한다.
```

가능한 claim:

- source confidence는 relation reliability와 같지 않다.
- relation semantic content `T_e`, predicate-independent geometry evidence `G_e`,
  source confidence `Z_e`를 분리하면, source score가 놓치는
  predicate-geometry compatibility signal을 만들 수 있다.
- `C_e = compatibility(T_e, G_e)`를 source score와 결합하면 official 3DSSG
  validation split에서 Recall@K를 유지 또는 개선하면서 Violation@K를 크게 낮출 수 있다.
- H002의 final decision layer는 `p_obs`와 `p_rel`로 분리할 수 있다. 즉,
  evidence가 충분한지 먼저 판단하고, 판단 가능한 edge에 대해서만 relation
  reliability를 결정한다.
- 이 효과는 `relative_vertical`과 `size_relative`처럼 clean signed-comparison
  family에서 가장 강하다.

아직 불가능한 claim:

- 모든 3DSSG relation family를 해결했다.
- `support_contact`까지 안정적으로 해결했다.
- official test benchmark 또는 leaderboard 성능을 개선했다.
- Open3DSG의 unconstrained open-vocabulary GT evaluation을 했다.
- `p_obs/p_rel`의 selective decision 성능까지 정량적으로 검증 완료했다.
- H003 embedding까지 paper main method로 검증했다.

따라서 H002의 가장 안전한 paper framing은 다음이다.

```text
Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations:
a source-agnostic reliability/reranking layer that separates semantic content,
geometry evidence, source confidence, and observability-aware reliability decisions.
```

Top-tier claim으로 만들려면 novelty를 "geometry를 추가했다"가 아니라 다음처럼
써야 한다.

```text
기존 relation source score는 semantic plausibility와 physical/geometric
compatibility가 섞인 single confidence이므로, relation reliability를 직접
나타내지 않는다. H002는 이 score를 그대로 믿지 않고, T_e, G_e, Z_e를 분리한 뒤
T_e x G_e compatibility를 학습하고 source ranking에 risk-aware하게 결합한다.
그 다음 evidence가 부족한 edge는 `p_obs`로 abstain하고, observable edge는
`p_rel`로 accept/reject한다.
```

## 11. 지금까지의 핵심 수치 결과

### 11.1 Official validation mechanism metric

위치:

```text
experiments/H002_compatibility_routing/official_evaluation/latest/
```

Official 3DSSG validation row 구성:

| Route family | Negative | Positive | Total |
| --- | ---: | ---: | ---: |
| `relative_horizontal` | 13290 | 5474 | 18764 |
| `relative_vertical` | 390 | 390 | 780 |
| `size_relative` | 170 | 170 | 340 |
| `support_contact` | 1589 | 1589 | 3178 |
| Total | 15439 | 7623 | 23062 |

Main model comparison:

| View | Overall AUROC | Macro-family AUROC | Weighted-family AUROC | 해석 |
| --- | ---: | ---: | ---: | --- |
| `M1_T_semantic_only` | 0.404333 | 0.417633 | 0.455374 | semantic content만으로는 부족 |
| `M2_G_geometry_only` | 0.528329 | 0.500000 | 0.500000 | geometry만으로는 universal reliability가 아님 |
| `M3_T_plus_G_concat` | 0.406137 | 0.416923 | 0.454625 | 단순 concat은 실패 |
| `M4_TxG_compatibility` | 0.724835 | 0.835547 | 0.720781 | compatibility interaction이 가장 강함 |

해석:

- `T_e`만 쓰거나 `G_e`만 쓰는 방식으로는 relation reliability를 설명하기 어렵다.
- 단순히 `T_e`와 `G_e`를 붙이는 concat도 충분하지 않다.
- `T_e x G_e` compatibility가 macro-family AUROC `0.835547`로 가장 강하다.
- 따라서 H002의 핵심 주장인 "semantic content와 geometry evidence를 분리한 뒤
  compatibility로 결합해야 한다"는 official validation mechanism metric에서는
  지지된다.

### 11.2 Family별 mechanism 결과

| Route family | Rows | M4 AUROC | Balanced Acc. | 현재 해석 |
| --- | ---: | ---: | ---: | --- |
| `relative_vertical` | 780 | 0.991321 | 0.957692 | strong main evidence |
| `size_relative` | 340 | 0.999585 | 0.988235 | strong main evidence |
| `relative_horizontal` | 18764 | 0.719568 | 0.701522 | usable, frame/reference caveat 필요 |
| `support_contact` | 3178 | 0.631712 | 0.566394 | diagnostic/challenging only |

해석:

- `relative_vertical`, `size_relative`는 H002의 clean compatibility mechanism을
  매우 강하게 보여준다.
- `relative_horizontal`은 데이터 수가 크고 성능도 유의미하지만, reference frame
  정의와 horizontal frame control caveat를 함께 써야 한다.
- `support_contact`는 성능이 약하고 contact/pose evidence가 부족하므로 solved
  claim으로 쓰면 안 된다.

### 11.3 Counterfactual control 결과

Official validation aggregate에서 `M4_TxG_compatibility`는 여러 control보다 강하다.

| Control | Macro-family AUROC | 해석 |
| --- | ---: | --- |
| `C1_wrong_T_within_route` | 0.164427 | predicate semantic을 틀리면 크게 무너짐 |
| `C2_wrong_T_across_route` | 0.565083 | route 밖 wrong predicate도 약화 |
| `C3_shuffled_G_global` | 0.493814 | geometry alignment를 깨면 near chance |
| `C4_shuffled_G_within_family` | 0.516794 | family 내부 geometry shuffle도 약화 |
| `C5_subject_object_swap` | 0.118501 | subject/object 방향성이 중요 |
| `C6_sign_flip` | 0.118501 | signed comparison 방향성이 중요 |
| `C7_horizontal_frame_swap` | 0.797398 | horizontal에서는 frame-specific caveat 필요 |

해석:

- wrong-`T`, shuffled-`G`, swap, sign-flip에서 성능이 무너지는 것은
  `C_e`가 단순 shortcut이 아니라 predicate와 geometry의 alignment를 쓰고 있음을
  지지한다.
- `C7_horizontal_frame_swap`은 완전히 무너지지 않으므로 horizontal family는
  main claim에 넣더라도 "reference-frame-sensitive route"로 제한해야 한다.

### 11.4 Source reranking validation result

위치:

```text
experiments/H002_compatibility_routing/source_reranking_evaluation/latest/
```

Source-wide candidate materialization:

| 항목 | 수량 |
| --- | ---: |
| total source rows scored | 762888 |
| VL-SAT validation rows | 441696 |
| Open3DSG validation rows | 321192 |
| primary success-family rows | 254296 |
| `C_e` train split rows | 4868 |
| validation/schema errors | 0 |

Primary success-family weighted result:

| Score | K | Recall@K | Violation@K |
| --- | ---: | ---: | ---: |
| `S0_source_score` | 5 | 0.344671 | 0.295181 |
| `S2_source_x_Ce` | 5 | 0.352608 | 0.054491 |
| `S0_source_score` | 10 | 0.471655 | 0.302201 |
| `S2_source_x_Ce` | 10 | 0.513605 | 0.072342 |
| `S0_source_score` | 20 | 0.642857 | 0.343578 |
| `S2_source_x_Ce` | 20 | 0.724490 | 0.100487 |
| `S0_source_score` | 50 | 0.849206 | 0.425197 |
| `S2_source_x_Ce` | 50 | 0.952381 | 0.165998 |
| `S0_source_score` | 100 | 0.995465 | 0.484792 |
| `S2_source_x_Ce` | 100 | 1.000000 | 0.341919 |

Delta summary:

| K | Delta Recall@K | Delta Violation@K |
| ---: | ---: | ---: |
| 5 | +0.007937 | -0.240690 |
| 10 | +0.041950 | -0.229859 |
| 20 | +0.081633 | -0.243091 |
| 50 | +0.103175 | -0.259199 |
| 100 | +0.004535 | -0.142873 |

해석:

- `S2_source_x_Ce`는 `S0_source_score` 대비 모든 K에서 Recall@K를 높이고
  Violation@K를 낮춘다.
- 특히 K=20, 50에서 recall gain과 violation reduction이 함께 크다.
- 이는 H002가 단순히 violation만 낮추고 recall을 희생하는 filter가 아니라,
  source ranking을 더 reliability-aware하게 재정렬할 수 있음을 보여준다.

### 11.5 C_e-only와 control reranking

`S1_Ce_only`:

| K | Recall@K | Violation@K |
| ---: | ---: | ---: |
| 5 | 0.018141 | 0.000821 |
| 10 | 0.063492 | 0.005069 |
| 20 | 0.213152 | 0.015195 |
| 50 | 0.748299 | 0.082185 |
| 100 | 1.000000 | 0.340590 |

해석:

- `C_e`만 쓰면 violation은 매우 낮지만 low-K recall이 크게 무너진다.
- 따라서 H002의 최종 score는 `C_e only`가 아니라 `Z_e`와 `C_e`를 결합한
  `S2_source_x_Ce`가 맞다.
- 이 결과는 source confidence `Z_e`를 버리면 안 되고, reliability layer로
  보정해야 한다는 주장을 강화한다.

Negative controls:

| Score | K=20 Recall@K | K=20 Violation@K | 해석 |
| --- | ---: | ---: | --- |
| `S2_source_x_Ce` | 0.724490 | 0.100487 | main score |
| `C1_source_x_shuffled_Ce` | 0.634921 | 0.378879 | geometry alignment가 깨지면 violation 증가 |
| `C2_source_x_wrong_T_Ce` | 0.521542 | 0.685297 | predicate semantic이 틀리면 violation 크게 증가 |

이 control은 H002 score가 단순히 source score에 다른 scalar를 곱한 것이 아니라,
predicate-geometry compatibility alignment에 의존한다는 근거다.

### 11.6 Support/contact hard route 결과

위치:

```text
experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/
```

핵심 수치:

| Setting | Metric | Value |
| --- | --- | ---: |
| internal dev | `M4_TxG_compatibility` AUROC | 0.721356 |
| official validation | `M4_TxG_compatibility` AUROC | 0.077539 |
| official validation | wrong-`T` AUROC | 0.922461 |
| paired groups | `M4` accuracy | 0.182505 |
| paired groups | wrong-`T` accuracy | 0.817495 |

해석:

- support/contact는 internal dev에서는 약한 signal이 있었지만 official validation으로
  transfer되지 않았다.
- wrong-`T`가 오히려 더 높다는 것은 현재 hard-route target 또는 feature가
  correct predicate-geometry compatibility를 안정적으로 잡지 못한다는 뜻이다.
- 따라서 `standing on`, `lying on`, `supported by` 계열은 현재 paper success
  table에 넣으면 안 된다.
- 이 결과는 실패가 아니라, H002가 relation family별 evidence route를 구분해야
  한다는 failure taxonomy 근거로 쓰는 것이 맞다.

### 11.7 p_obs / p_rel을 main claim에 넣기 위한 추가 검증

`p_obs`와 `p_rel`은 H002의 main framework에 포함하는 것이 맞다. 다만 현재
수치 결과가 강하게 지지하는 부분은 `C_e`와 `S2_source_x_Ce` reranking이다.
따라서 paper 구조는 다음처럼 잡는 것이 안전하다.

```text
Stage 1: C_e = compatibility(T_e, G_e)
Stage 2: S2 = source_score(Z_e) * C_e
Stage 3: p_obs / p_rel selective decision
```

Decision rule:

```text
p_obs low -> abstain
p_obs high + p_rel high -> accept
p_obs high + p_rel low -> reject
```

여기서 `p_obs`와 `p_rel`을 main paper claim으로 올리려면 다음 검증이 추가로
필요하다.

| 항목 | 필요한 이유 |
| --- | --- |
| `Q_e` schema freeze | observability / evidence quality가 `G_e`와 섞이지 않도록 분리 |
| observable / unobservable label | `p_obs`가 relation truth가 아니라 판단 가능성을 배우는지 확인 |
| accept / reject / abstain target | `p_rel`과 abstain decision을 동시에 평가 |
| selective prediction metric | coverage-risk curve, AURC, abstain precision/recall 필요 |
| calibration metric | ECE, Brier, reliability diagram 등으로 confidence quality 확인 |
| missing-evidence controls | no-view, low-visibility, missing-mesh, shuffled-view control 필요 |
| failure taxonomy 연결 | support/contact, containment, attachment 같은 hard route에서 abstain이 타당한지 확인 |

즉 `p_obs/p_rel`은 H002 main method에 포함하되, 이 시점의 정량 성능 claim은
`C_e` reranking 중심이었다. 이후 materialization/evaluation을 실행해 selective
stress-test는 통과했지만, calibrated paper-result claim은 아직 보류한다.

Protocol artifact:

```text
artifacts/compatibility_dataset_v3_pobs_prel_main_claim_protocol_after_report_0703/
status = h002_pobs_prel_main_claim_protocol_after_report_0703_ready
selected_path = include_pobs_prel_as_main_framework_claim_not_yet_quantitative_result
next_todo = compatibility_dataset_v3_pobs_prel_materialization_plan_after_protocol
```

이 artifact는 `Q_e` schema, observable/unobservable label, accept/reject/abstain
target, selective prediction metric, calibration metric, missing-evidence control,
failure-route mapping을 고정한다. 따라서 `p_obs/p_rel`의 method/protocol 정의는
완료됐다.

### 11.8 p_obs / p_rel materialization and selective metric result

Runtime output:

```text
experiments/H002_compatibility_routing/pobs_prel_materialization/latest/
experiments/H002_compatibility_routing/pobs_prel_schema_audit/latest/
experiments/H002_compatibility_routing/pobs_prel_evaluation/latest/
```

Result review artifact:

```text
artifacts/compatibility_dataset_v3_pobs_prel_result_review_after_metric_runner/
status = h002_pobs_prel_result_review_after_metric_runner_ready
selective_metric_pass = true
paper_promotion_pass = false
validation_errors = 0
```

Materialization:

| 항목 | 수량 |
| --- | ---: |
| input observed rows | 30014 |
| output rows per view | 150070 |
| synthetic unobservable controls | 120056 |
| official validation eval rows | 115310 |
| hidden abstain labels | 120056 |
| hidden accept labels | 11099 |
| hidden reject labels | 18915 |

Schema audit:

| Check | Result |
| --- | ---: |
| blocked field hits | 0 |
| validation errors | 0 |
| `Q_e` view rows | 150070 |
| `p_rel` view rows | 150070 |
| hidden label rows | 150070 |

Selective metric:

| Metric | Value | Gate |
| --- | ---: | --- |
| `p_obs` AUROC | 1.000000 | pass |
| `p_obs` ECE@10 | 0.043647 | pass |
| `p_rel` AUROC | 0.724615 | pass |
| `p_rel` ECE@10 | 0.171030 | paper-promotion warning |
| accept/reject/abstain macro-F1 | 0.778449 | pass |
| decision accuracy | 0.936476 | pass |
| missing-control abstain rate | 1.000000 | pass |
| AURC | 0.163562 | diagnostic |

해석:

- `p_obs`는 synthetic missing-evidence controls를 안정적으로 abstain으로 보낸다.
- `p_rel`은 observable original rows에서 최소 AUROC gate를 넘는다.
- accept/reject/abstain selective decision도 macro-F1 기준을 넘는다.
- 하지만 `p_rel` ECE가 0.171로 calibration warning threshold 0.15를 넘고,
  unobservable label이 independent human label이 아니라 synthetic missing-evidence
  control이므로, paper-ready calibrated result claim은 아직 보류한다.

따라서 현재 위치는 다음이다.

```text
p_obs/p_rel selective stress-test passed.
Calibrated paper-result promotion is not yet passed.
```

### 11.9 CI / qualitative / failure wording result

Artifact:

```text
artifacts/compatibility_dataset_v3_ci_qualitative_failure_wording_after_pobs_prel_review/
status = h002_ci_qualitative_failure_wording_after_pobs_prel_review_ready
selected_path = keep_pobs_prel_as_framework_component_ci_qualitative_wording_ready
paper_promotion_pass = false
validation_errors = 0
```

Bootstrap CI:

| Metric | Point | 95% CI |
| --- | ---: | --- |
| `p_obs` AUROC | 1.000000 | [1.000000, 1.000000] |
| `p_rel` AUROC | 0.724615 | [0.715937, 0.730900] |
| decision macro-F1 | 0.778449 | [0.773312, 0.782656] |
| missing-control abstain rate | 1.000000 | [1.000000, 1.000000] |

Qualitative examples:

```text
qualitative_examples = 40
example_types = correct_accept, correct_reject, correct_abstain,
                false_accept, false_reject
```

Allowed paper wording:

- selective-decision stress test passes.
- `p_obs/p_rel` can remain as an H002 framework component.
- the current evidence is validation-level and uses synthetic missing-evidence
  controls.
- calibration remains imperfect.

Blocked paper wording:

- official-test p_obs/p_rel result.
- independent human observability labels.
- calibrated p_obs/p_rel reliability solved.
- support/contact, attachment, containment solved by this stress test.

### 11.10 H002 paper outline / integration decision

Artifact:

```text
artifacts/compatibility_dataset_v3_h002_paper_outline_or_integration_decision_after_insertion_plan/
status = h002_paper_outline_or_integration_decision_after_insertion_plan_ready
selected_path = open_h002_standalone_outline_candidate_no_h001_edit_no_new_paper_root
validation_errors = 0
next_todo = compatibility_dataset_v3_h002_standalone_outline_gap_review_after_decision
```

Decision:

- H002는 독립 paper-outline candidate로 유지한다.
- 지금 H001/GeoCalib manuscript에 통합하지 않는다.
- 새 top-level paper folder도 아직 만들지 않는다.
- H002 outline gap review를 먼저 진행한 뒤, 실제 paper workspace 승격 여부를
  결정한다.

이 판단의 이유는 H002가 H001과 같은 문제 계열에 있으나 method shape이 다르기
때문이다. H001은 calibrated geometry-consistency reranking이고, H002는
`T_e/G_e/Z_e/Q_e`, `C_e`, `p_obs/p_rel`을 포함한 factorized compatibility
reliability framework다. 지금 섞으면 H001의 claim이 흐려지고 H002의 아직 남은
validation-only, support/contact failure, p_obs/p_rel calibration caveat까지 H001이
떠안게 된다.

### 11.11 H002 standalone outline gap review

Artifact:

```text
artifacts/compatibility_dataset_v3_h002_standalone_outline_gap_review_after_decision/
status = h002_standalone_outline_gap_review_after_decision_ready
selected_path = keep_outline_candidate_do_not_promote_paper_workspace_yet_resolve_gap_pack
validation_errors = 0
next_todo = compatibility_dataset_v3_h002_gap_resolution_plan_after_outline_review
```

결론:

- H002는 standalone outline candidate로 유지한다.
- 새 paper workspace로 바로 승격하지 않는다.
- H001 manuscript도 수정하지 않는다.

Blocking gates:

| Gate | 판단 |
| --- | --- |
| `G1_claim_thesis` | design-necessity narrative 부족 |
| `G2_table_plan` | main/appendix table placement 미고정 |
| `G3_figure_plan` | figure spec 미작성 |
| `G4_related_work` | related-work matrix와 novelty-threat map 미작성 |
| `G5_ablation_contract` | final ablation/control contract 미고정 |
| `G8_failure_taxonomy` | support/contact qualitative taxonomy 부족 |
| `G9_workspace_promotion` | 새 paper root 생성 금지 |

Ready gates:

| Gate | 판단 |
| --- | --- |
| `G6_calibration_boundary` | `p_obs/p_rel`은 stress-test only로 경계가 명확함 |
| `G7_benchmark_boundary` | validation-only, no-SOTA, no-official-test wording이 잠겨 있음 |

## 12. 종합 해석

지금까지의 실험은 H002의 핵심 claim 중 일부를 꽤 강하게 지지한다.

지지되는 내용:

- source confidence 하나로 relation reliability를 설명하기 어렵다.
- `T_e`와 `G_e`를 분리한 뒤 `C_e = compatibility(T_e, G_e)`를 만들면
  semantic-only, geometry-only, 단순 concat보다 강한 signal이 나온다.
- `C_e`를 source score와 결합한 `S2`는 validation source reranking에서
  Recall@K를 유지/개선하면서 Violation@K를 크게 낮춘다.
- wrong-`T`, shuffled-`G`, swap, sign-flip controls는 H002가 실제
  predicate-geometry alignment를 보고 있음을 보조한다.
- `p_obs/p_rel`을 main framework의 selective decision layer로 포함하는 것은
  원리적으로 자연스럽고, selective stress-test metric은 통과했다.

아직 약한 내용:

- `support_contact`처럼 contact/pose/mesh/visual evidence가 필요한 relation은
  현재 feature로 해결되지 않았다.
- `relative_vertical`, `size_relative`의 강한 결과가 signed scalar comparison에
  몰려 있으므로, reviewer가 "sign rule reranking 아닌가?"라고 물을 수 있다.
- official test result가 없고, 현재는 official validation split 기반 result다.
- `p_obs/p_rel`은 selective stress-test는 통과했지만, calibrated paper-result
  claim에는 CI, qualitative case, failure wording, proxy-label boundary가 남아 있다.
- confidence interval, bootstrap, source별/family별 failure case figure는 아직
  paper-ready 형태로 충분히 정리되지 않았다.

따라서 H002의 현재 claim 가능성은 다음처럼 판단한다.

| Claim level | 가능 여부 | 판단 |
| --- | --- | --- |
| Hypothesis validation | 가능 | 충분히 지지됨 |
| Validation-level paper result | 가능 | boundary를 지키면 가능 |
| `p_obs/p_rel` main framework claim | 가능 | selective decision layer로 포함 가능 |
| `p_obs/p_rel` quantitative result claim | 조건부 | selective metric은 통과, calibration/proxy-label boundary 남음 |
| Broad all-relation 3DSSG reliability | 불가 | support/contact와 semantic/structural route 미해결 |
| Official test/SOTA benchmark | 불가 | official test GT/eval server 미확보 |
| AAAI-level standalone paper | 조건부 가능 | claim을 좁히고 failure taxonomy/CI/ablation을 보강해야 함 |

## 13. 다음 단계

현재 바로 해야 할 일은 새 relation family를 계속 추가하는 것이 아니라,
H002 standalone outline candidate의 gap-resolution plan을 만드는 것이다.

추천 next step:

1. main method를 `C_e reranking + p_obs/p_rel selective decision`의 two-stage
   reliability framework로 정의한다.
2. `p_obs/p_rel` selective result는 framework component로 유지하되,
   calibrated quantitative result claim은 보류한다.
3. main result table은 `S0_source_score` vs `S2_source_x_Ce` validation
   reranking table로 둔다.
4. mechanism table은 `M1/M2/M3/M4`와 controls를 family-wise로 둔다.
5. `support_contact`는 success row가 아니라 challenging failure taxonomy와
   `p_obs` 필요성을 보여주는 case로 둔다.
6. CI/qualitative/failure wording artifact를 paper planning에서 참조한다.
7. gap-resolution plan을 만들어 claim thesis, table placement, figure plan,
   related work, ablation contract, failure taxonomy를 어떤 순서로 닫을지 고정한다.
8. H003 embedding은 H002 paper outline/integration decision 이후 optional
   extension으로 시도한다.

현재 상태에서 H002를 억지로 넓히는 것보다, "어디까지는 강하고 어디부터는
아직 안 된다"를 명확히 쓰는 편이 reviewer defense에 더 좋다.

## 14. Gap Resolution Pack, 2026-07-03

요청된 paper-claim gap 6개를 하나의 pack으로 정리했다.

Artifact:

```text
artifacts/compatibility_dataset_v3_h002_gap_resolution_pack_after_outline_review/
```

결과:

```text
status = h002_gap_resolution_pack_after_outline_review_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_h002_paper_workspace_promotion_decision_after_gap_resolution_pack
```

생성된 핵심 파일:

| File | 내용 |
| --- | --- |
| `claim_thesis.md` | source confidence와 fixed fusion이 왜 부족하고, 왜 `T_e/G_e/Z_e/Q_e`, `C_e`, `p_obs/p_rel` 분리가 필요한지 정리 |
| `main_result_ci_table.csv` | `S0`, `S2`의 Recall@K / Violation@K bootstrap CI |
| `main_result_delta_ci_table.csv` | `Delta(S2-S0)`의 Recall@K / Violation@K bootstrap CI |
| `table_ablation_contract.csv` | main/appendix table 배치와 ablation/control contract |
| `figure_specs.md` | framework, leakage boundary, recall-violation tradeoff, support/contact failure figure spec |
| `related_work_novelty_map.csv` | primary-source 기반 related-work / novelty-threat map |
| `support_contact_failure_taxonomy.csv` | support/contact를 success가 아니라 failure taxonomy로 쓰기 위한 정리 |

Main result CI는 Docker runtime에서 생성했다.

Runtime output:

```text
experiments/H002_compatibility_routing/source_reranking_ci/latest/
```

검증 결과:

```text
n_bootstrap = 1000
bootstrap_unit = source_id/subgraph_id/route_family
unit_count = 2192
point_metric_mismatch_count = 0
validation_errors = 0
```

핵심 CI 해석:

| K | Metric | Delta(S2-S0) | 95% CI | 해석 |
| ---: | --- | ---: | --- | --- |
| 5 | Recall@K | +0.007937 | [-0.006049, 0.022589] | recall delta는 0과 분리되지 않음 |
| 5 | Violation@K | -0.240690 | [-0.254359, -0.227705] | violation 감소는 지지됨 |
| 10 | Recall@K | +0.041950 | [0.023208, 0.062085] | recall 개선 지지됨 |
| 10 | Violation@K | -0.229859 | [-0.239725, -0.220192] | violation 감소 지지됨 |
| 20 | Recall@K | +0.081633 | [0.048096, 0.118007] | recall 개선 지지됨 |
| 20 | Violation@K | -0.243091 | [-0.251882, -0.235094] | violation 감소 지지됨 |
| 50 | Recall@K | +0.103175 | [0.068924, 0.140698] | recall 개선 지지됨 |
| 50 | Violation@K | -0.259199 | [-0.266175, -0.252394] | violation 감소 지지됨 |
| 100 | Recall@K | +0.004535 | [0.000000, 0.011393] | 보수적으로 neutral로 표현 |
| 100 | Violation@K | -0.142873 | [-0.146752, -0.139429] | violation 감소 지지됨 |

Support/contact는 최신 hard-route 결과상 success claim으로 쓰면 안 된다.
`M4_TxG_compatibility` AUROC가 `0.077539`이고 wrong-T control이 `0.922461`로
뒤집혀 있어, 현재 target/evidence 방향이 의도한 compatibility와 정렬되지 않았다.
따라서 support/contact는 “해결된 relation family”가 아니라 contact/pose/mesh/
observability evidence가 부족한 failure taxonomy로 사용한다.

현재 6개 gap은 resolved로 기록했지만, 새 H002 paper workspace 생성은 여전히
사용자 명시 승인 전까지 blocked 상태다.

## 15. p_obs / p_rel Calibration Upgrade, 2026-07-04

`calibrated p_obs/p_rel reliability is solved` claim을 올릴 수 있는지 확인하기
위해 추가 실험 6개를 진행했다.

Runtime output:

```text
experiments/H002_compatibility_routing/pobs_prel_calibration_upgrade/latest/
```

Review artifact:

```text
artifacts/compatibility_dataset_v3_pobs_prel_calibration_upgrade_result_review_after_runner/
```

실행 결과:

```text
status = h002_pobs_prel_calibration_upgrade_ready
review_status = h002_pobs_prel_calibration_upgrade_result_review_after_runner_ready
validation_errors = 0
calibrated_quantitative_claim_pass = false
pobs_prel_framework_component_allowed = true
```

6개 항목별 결과:

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| `Q_e / observability label` | asset audit rows `23062`, label `observable=23062` | 실제 3RScan scan/multiview/mesh 파일을 확인했지만 official observed rows가 전부 observable이라 real negative/ambiguous observability label이 생기지 않음 |
| calibration split | `internal_dev`에서 calibrator 선택 | official validation을 보고 calibrator를 조정하지 않았음 |
| calibration metric | `p_rel` raw ECE `0.171030`, calibrated ECE `0.223458` | internal-dev isotonic calibration이 official validation에서 오히려 악화됨 |
| selective metric | calibrated decision macro-F1 `0.778072`, AURC `0.147590` | selective stress-test로는 여전히 사용 가능 |
| missing evidence controls | no-view / low-visibility / missing-mesh / shuffled-view / wrong-pair abstain rate `1.0` | missing-evidence control은 통과 |
| failure-route 연결 | support_contact `3178` rows, attachment_like/containment `0` rows | support/contact는 연결됐지만 attachment/containment는 현 runtime에 없어 empirical claim 불가 |

핵심 수치:

| Metric | Value |
| --- | ---: |
| `p_obs_calibrated_ECE_10` | `0.000001` |
| `p_rel_raw_ECE_10` | `0.171030` |
| `p_rel_calibrated_ECE_10` | `0.223458` |
| `p_rel_calibrated_AUROC` | `0.723800` |
| `decision_macro_F1_calibrated` | `0.778072` |
| `p_rel_calibrated_AUROC_95CI` | `[0.717310, 0.730271]` |
| `p_rel_calibrated_ECE_95CI` | `[0.217850, 0.229772]` |

판단:

- `p_obs/p_rel`은 H002 method의 selective-decision component로 유지한다.
- 하지만 `calibrated p_obs/p_rel reliability is solved`는 현재 blocked다.
- 이유는 `p_rel` calibration이 통과하지 못했고, 실제 asset-audit observability
  label이 negative/ambiguous case를 제공하지 못했으며, attachment/containment
  route가 current runtime에 존재하지 않기 때문이다.

따라서 paper에서는 다음 wording이 안전하다.

```text
We include p_obs/p_rel as a selective-decision layer and validate it through
missing-evidence stress tests. However, calibrated selective reliability remains
an open requirement because real negative observability labels and additional
observability-heavy routes are not yet available.
```
