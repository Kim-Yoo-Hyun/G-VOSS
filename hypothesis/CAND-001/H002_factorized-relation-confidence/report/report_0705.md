# H002 Report 0705: Principle and Framework Scope Review

## 목적

이번 단계는 H002의 다음 TODO인 normalization / no-route geometry sensitivity를
진행한 뒤, 사용자가 강조한 기준을 중심으로 다시 점검한 것이다.

점검 기준:

```text
방법/method가 우리가 설정한 문제를 원리적으로 자명하고 자연스럽게 해결하는 방향인가?
relation-aware evidence routing framework를 실제로 구축했는가?
general reliable 3D relation framework라고 부를 수 있는가?
```

## 결론

```text
method_principle = natural_and_principled_for_scoped_problem
relation_aware_evidence_routing_framework = constructed_as_framework_and_partially_validated
general_reliable_3d_relation_framework = not_yet_validated
```

즉, 현재 H002는 우리가 설정한 문제에는 원리적으로 잘 맞는다. 하지만 아직
`general reliable 3D relation framework`가 완성됐다고 말할 수는 없다.

가장 안전한 paper claim은 다음이다.

```text
H002는 source confidence와 predicate-geometry compatibility를 분리하고,
이를 다시 결합해 geometry-checkable comparison relation에서 validation-level
source reranking을 개선한다.
```

## 왜 원리적으로 자연스러운가

우리가 정의한 문제는 다음이었다.

```text
source relation score는 semantic plausibility, geometry compatibility,
source confidence가 섞인 single confidence다.
따라서 이 score를 그대로 relation reliability로 보면 안 된다.
```

H002의 대응은 다음이다.

```text
T_e = relation/predicate semantic content
G_e = geometry evidence
Z_e = source confidence
C_e = compatibility(T_e, G_e)
S2 = Z_e * C_e
```

이 구조는 문제 원인과 직접 맞는다.

- `C_e` 안에는 `Z_e`를 넣지 않는다.
- source confidence를 복사하지 않고, predicate와 geometry의 compatibility를 먼저 계산한다.
- 이후 source score는 완전히 버리지 않고, 최종 reranking에서만 결합한다.
- 이 방식은 `C_e only`처럼 recall을 크게 잃는 문제도 피한다.

따라서 현재 H002 method는 억지로 끼워맞춘 방식이 아니라, 문제 정의에서 자연스럽게 나온 방식이다.

## Sensitivity 결과

Runtime:

```text
experiments/H002_compatibility_routing/source_reranking_sensitivity/latest/
```

Primary comparison route, K=10/20/50:

| Score | K | Recall@K | Violation@K |
| --- | ---: | ---: | ---: |
| `S0_source_score_minmax` | 10 | 0.471655 | 0.302201 |
| `S0_source_score_minmax` | 20 | 0.642857 | 0.343578 |
| `S0_source_score_minmax` | 50 | 0.849206 | 0.425197 |
| `S2_minmax_source_x_Ce` | 10 | 0.513605 | 0.072342 |
| `S2_minmax_source_x_Ce` | 20 | 0.724490 | 0.100487 |
| `S2_minmax_source_x_Ce` | 50 | 0.952381 | 0.165998 |
| `S2_raw_source_x_Ce` | 10 | 0.498866 | 0.071246 |
| `S2_raw_source_x_Ce` | 20 | 0.698413 | 0.097640 |
| `S2_raw_source_x_Ce` | 50 | 0.942177 | 0.159383 |
| `S2_rankpct_source_x_Ce` | 10 | 0.386621 | 0.025758 |
| `S2_rankpct_source_x_Ce` | 20 | 0.640590 | 0.073311 |
| `S2_rankpct_source_x_Ce` | 50 | 0.928571 | 0.240886 |
| `A1_minmax_route_G_only` | 10 | 0.476190 | 0.281193 |
| `A1_minmax_route_G_only` | 20 | 0.646259 | 0.327534 |
| `A1_minmax_route_G_only` | 50 | 0.834467 | 0.427885 |
| `A1_minmax_no_route_G_only` | 10 | 0.476190 | 0.281193 |
| `A1_minmax_no_route_G_only` | 20 | 0.646259 | 0.327511 |
| `A1_minmax_no_route_G_only` | 50 | 0.834467 | 0.427885 |
| `A2_minmax_TG_concat` | 10 | 0.482993 | 0.299050 |
| `A2_minmax_TG_concat` | 20 | 0.629252 | 0.330770 |
| `A2_minmax_TG_concat` | 50 | 0.825397 | 0.412118 |

해석:

- `S2_minmax_source_x_Ce`는 `S0`, `A1`, `A2`보다 강하다.
- `A1_minmax_no_route_G_only`도 `S2`보다 약하므로, S2 gain이 route-family one-hot이 들어간 G-only baseline 때문이라고 보기 어렵다.
- `S2_raw_source_x_Ce`도 S0보다 Recall@K와 Violation@K 방향을 유지한다.
- `S2_rankpct_source_x_Ce`는 violation을 강하게 낮추지만 K=10 recall이 떨어진다.

따라서 결론은:

```text
S2 효과는 단순 G-only나 route-family one-hot 때문에 생긴 것이 아니다.
다만 normalization에는 민감도가 있으므로 normalization-invariant claim은 금지한다.
```

## Relation-Aware Evidence Routing Framework 점검

현재 구축된 것:

| Component | 상태 | 해석 |
| --- | --- | --- |
| route map | constructed | comparison, geometry-only, frame-aware, support/contact, observability-heavy, semantic/structural route 정의됨 |
| comparison route | validated main | `relative_vertical`, `size_relative`에서 main quantitative success |
| geometry-only route | diagnostic/control | `close by`와 G-only controls로 route diversity를 보여줌 |
| support/contact route | failure taxonomy | hard-route로 실패 원인과 richer evidence 필요성을 보여줌 |
| p_obs/p_rel | framework component only | selective stress-test는 통과했지만 calibrated solved claim은 blocked |

즉 relation-aware evidence routing framework는 “구축”은 됐다.
다만 “완성된 general framework”로 검증된 것은 아니다.

정확한 표현:

```text
H002 builds a relation-aware evidence routing framework and validates its
comparison-route reranking mechanism.
```

금지 표현:

```text
H002 solves general reliable 3D relation reasoning across all relation families.
```

## General Reliable 3D Relation Framework 여부

현재는 아직 아니다.

이유:

- main quantitative success가 comparison route에 집중되어 있다.
- support/contact는 solved가 아니라 failure taxonomy다.
- attachment / containment / cover / semantic-structural route는 아직 main quantitative evidence가 없다.
- p_obs/p_rel은 framework에는 포함되지만 calibrated reliability solved claim은 blocked다.

따라서 paper에서는 다음처럼 써야 한다.

```text
Toward a relation-aware reliable 3D relation framework
```

또는

```text
a route-aware reliability/reranking framework candidate
```

## Paper Claim Boundary Lock 반영

Sensitivity review 이후 paper claim은 다음처럼 고정한다.

```text
locked_claim = validation_level_comparison_route_source_reranking
comparison_route_main_claim_allowed = true
relation_aware_framework_partially_validated = true
general_reliable_framework_completed_result = false
pobs_prel_solved_claim_allowed = false
normalization_invariant_claim_allowed = false
```

따라서 현재 paper의 중심 문장은 다음이다.

```text
Factor-isolated predicate-geometry compatibility improves validation-level
source reranking for geometry-checkable comparison relations.
```

이 경계는 “최종 목표를 포기한다”는 뜻이 아니다. 현재 evidence로 바로 주장할 수
있는 범위를 고정한 것이다.

## Hypothesis / Experiment / Paper 단계 구분

이번 claim-boundary lock은 엄밀히 말하면 hypothesis 자체라기보다
paper/experiment 전환 경계에 있는 작업이다.

앞으로의 역할 분리는 다음처럼 둔다.

| Stage | 역할 | H002에서 해야 할 일 |
| --- | --- | --- |
| hypothesis | 문제 정의, method necessity, claim 가능성 판단 | 왜 `T_e/G_e/Z_e/C_e/Q_e` 분리가 필요한지, 어떤 route가 가능한지 정리 |
| experiment | Docker 기반 metric, ablation, calibration, route 검증 | support/contact, p_obs/p_rel, normalization robustness 검증 |
| paper | 통과한 evidence를 claim/table/figure/prose로 고정 | scoped claim 문장화, caption, limitation, reviewer defense |

따라서 앞으로 `paper claim boundary`, `table caption`, `draft insertion`은
paper workspace에서 진행하는 것이 맞다. 반대로 `support/contact solved`,
`calibrated p_obs/p_rel solved`, `normalization-invariant improvement`는
experiment 단계에서 추가 검증해야 한다.

## 더 가야 하는 방향

사용자 판단처럼 아래 세 방향은 최종적으로 더 가는 것이 맞다.

1. `support/contact solved`
   - 현재는 failure taxonomy다.
   - general reliable 3D relation framework claim으로 가려면 richer `G_e`가
     필요하다.
   - 필요한 evidence: contact patch, support surface, pose/orientation,
     point/mesh evidence, multi-view confirmation, class-pair controlled split.

2. `calibrated p_obs/p_rel solved`
   - 현재는 framework component와 stress-test evidence다.
   - solved claim을 하려면 real observability labels가 필요하다.
   - 필요한 metric: ECE, Brier, NLL, reliability diagram, AURC,
     coverage-risk curve, missing-evidence controls.

3. `normalization-invariant improvement`
   - 현재는 minmax main + raw-product sensitivity까지만 가능하다.
   - rank-percentile에서 low-K recall이 떨어졌기 때문에 invariant claim은
     아직 불가능하다.
   - 가려면 train/dev-frozen normalization, raw log-utility, source-family
     calibration, lambda freeze를 비교해야 한다.

즉 현재 scoped paper claim은 안전한 중간 claim이고, top-tier 수준의 더 강한
framework claim을 원하면 위 세 가지는 experiment 단계에서 더 진행해야 한다.

## Experiment-Stage General Framework Gap Synthesis

요청한 다섯 단계는 paper 문장 정리가 아니라 experiment-stage에서 진행했다.

Runtime artifact:

```text
experiments/H002_compatibility_routing/general_framework_gap/latest/
```

생성 파일:

```text
summary.json
general_framework_gap_targets.csv
support_contact_gate.csv
pobs_prel_gate.csv
normalization_gate.csv
route_source_wide_summary.csv
route_source_wide_deltas.csv
validation_errors.jsonl
```

Docker service:

```text
h002-general-framework-gap
```

결과:

```text
status = h002_general_framework_gap_experiment_synthesis_ready
validation_errors = 0
general_framework_claim = blocked_continue_experiment_stage
support_contact_solved = false
calibrated_pobs_prel_solved = false
normalization_invariant_improvement = false
route_aware_source_wide_generalization = false
```

### 1. General-Framework Gap Plan

현재 general reliable 3D relation framework로 승격하려면 네 축이 모두 필요하다.

| Axis | 현재 판정 | 이유 |
| --- | --- | --- |
| support/contact solved | blocked | broad support/contact는 near-threshold지만 hard official route가 실패 |
| calibrated p_obs/p_rel solved | blocked | p_rel calibration ECE 실패, real negative/ambiguous observability label 부족 |
| normalization-invariant improvement | blocked | raw product는 통과하지만 rank-percentile low-K recall이 실패 |
| route-aware source-wide generalization | blocked | supported route가 부족하고 observability-heavy route가 없음 |

따라서 현재 paper-level claim은 여전히 comparison-route source reranking까지만
직접 주장하는 것이 맞다.

### 2. Support/Contact Hard Route 강화 결과

현재 사용 가능한 support/contact 결과:

| Scope | AUROC | Balanced Acc. | 판정 |
| --- | ---: | ---: | --- |
| broad official support/contact M4 | 0.631712 | 0.566394 | near but not solved |
| hard-route official validation M4 | 0.077539 | 0.180931 | failed generalization |
| hard-route internal dev M4 | 0.721356 | 0.658983 | internal signal only |

해석:

- 내부 dev에서는 signal이 있지만 official validation으로 일반화되지 않는다.
- `support/contact solved` claim은 불가능하다.
- 다음 실험은 richer `G_e`와 relabel/decomposition protocol이 필요하다.

필요한 다음 root:

```text
experiments/H002_compatibility_routing/support_contact_generalization_repair/
```

필요한 evidence:

- contact patch
- support surface
- pose/orientation
- point/mesh evidence
- multi-view confirmation
- `standing on`, `lying on`, `supported by` 분리 또는 relabel/abstain

### 3. p_obs / p_rel 재검증 결과

현재 calibration-upgrade 결과:

| Metric | Value | Gate | Passed |
| --- | ---: | --- | --- |
| p_rel calibrated AUROC | 0.723800 | >= 0.70 | true |
| p_rel calibrated ECE@10 | 0.223458 | <= 0.10 | false |
| decision macro-F1 | 0.778072 | >= 0.70 | true |
| asset negative/ambiguous observability | false | true 필요 | false |
| attachment/containment rows present | false | true 필요 | false |

해석:

- discrimination은 살아 있다.
- calibration은 아직 부족하다.
- real `observable / unobservable / ambiguous` label이 충분하지 않다.
- attachment/containment route가 빠져 있어 `p_obs`를 general framework claim으로
  올릴 수 없다.

필요한 다음 root:

```text
experiments/H002_compatibility_routing/pobs_prel_observability_repair/
```

### 4. Normalization Robustness 결과

| Variant | Passed | 해석 |
| --- | --- | --- |
| raw `source_score * C_e` | true | minmax가 아니어도 방향은 유지 |
| rank-percentile `source_score * C_e` | false | low-K recall 손실 |
| no-route G-only sensitivity | true | S2 gain은 route one-hot G-only 때문이 아님 |

해석:

- robustness는 일부 확인됐다.
- 하지만 normalization-invariant improvement는 아직 주장할 수 없다.
- 특히 rank-percentile에서 K=10 recall이 떨어지는 점이 남아 있다.

필요한 다음 root:

```text
experiments/H002_compatibility_routing/normalization_robustness/
```

다음에 필요한 비교:

- train/dev-frozen minmax
- raw log-utility score
- source-family calibration
- lambda freeze
- rank-percentile repair 또는 low-K recall tradeoff 분석

### 5. Route-Aware Source-Wide Evaluation 결과

Route-wise source-wide 결과:

| Route | Cells | Pass cells | 판정 |
| --- | ---: | ---: | --- |
| proximity | 4 | 4 | supported |
| relative_vertical | 4 | 4 | supported |
| size_relative | 4 | 3 | mixed_or_blocked |
| support_contact | 4 | 2 | mixed_or_blocked |
| relative_horizontal | 4 | 0 | mixed_or_blocked |

해석:

- source-wide route evidence는 `proximity`, `relative_vertical`에서 안정적이다.
- `size_relative`는 거의 통과하지만 일부 cell이 남는다.
- `support_contact`는 source에 따라 mixed이고 solved route가 아니다.
- `relative_horizontal`은 violation tradeoff가 나빠져 현재 general route evidence가
  아니다.
- observability-heavy route가 아직 없다.

따라서 최소 route coverage 기준을 만족하지 못한다.

필요한 다음 root:

```text
experiments/H002_compatibility_routing/route_wide_generalization/
```

### Experiment-Stage 최종 판정

다섯 단계 결과를 종합하면:

```text
general reliable 3D relation framework claim = blocked
current paper-level claim = comparison-route source reranking 유지
next experiment = support_contact_generalization_repair
```

즉 현재 방향은 잘못된 것이 아니라, 아직 general framework claim으로 올리기에는
필요한 route evidence가 부족하다.

다음 실험 순서:

1. `support_contact_generalization_repair`
2. `pobs_prel_observability_repair`
3. `normalization_robustness_train_dev_frozen`
4. `route_wide_generalization_after_repairs`

## 최종 판단

현재 H002 방향은 원리적으로 맞다.

하지만 claim boundary는 다음처럼 고정해야 한다.

Allowed:

```text
comparison route에서 factor-isolated C_e가 source reranking을 개선한다.
```

Allowed:

```text
relation-aware evidence routing framework를 설계하고,
일부 route에 대해 검증했으며,
hard route에서는 왜 추가 evidence가 필요한지 보였다.
```

Blocked:

```text
general reliable 3D relation framework를 완성했다.
```

Next TODO:

```text
support_contact_generalization_repair
```

## Support/Contact Generalization Repair

이번 단계는 support/contact를 바로 solved route로 승격하는 실험이 아니라,
현재 hard route 실패 원인을 정리하고 다음 materialization을 고정하는
experiment-stage repair synthesis다.

Runtime artifact:

```text
experiments/H002_compatibility_routing/support_contact_generalization_repair/latest/
```

생성 파일:

```text
summary.json
feature_gap.csv
predicate_error_summary.csv
class_pair_error_summary.csv
failure_taxonomy.csv
repair_protocol.csv
gate_plan.csv
validation_errors.jsonl
```

Docker service:

```text
h002-support-contact-generalization-repair
```

결과:

```text
status = h002_support_contact_generalization_repair_ready
validation_errors = 0
candidate_rows = 3178
feature_count = 43
fully_available_feature_count = 43
hard_internal_dev_M4_AUROC = 0.721356
hard_official_M4_AUROC = 0.077539
hard_official_M4_balanced_accuracy = 0.180931
broad_official_support_contact_M4_AUROC = 0.631712
support_contact_solved = false
selected_path = pose_aware_relabel_abstain_repair_before_more_model_capacity
```

### 핵심 해석

현재 support/contact 실패는 단순히 geometry feature가 없어서 생긴 문제가 아니다.
현재 hard-route materialization에서는 `43/43`개의 `G_e` feature가 모든
`3178`개 row에서 사용 가능하다. 그런데 official hard-route에서
`T_e x G_e` compatibility가 AUROC `0.077539`로 뒤집힌다.

high-confidence failure는 다음처럼 정리된다.

| Predicate | Failure rows | Error pattern | Repair implication |
| --- | ---: | --- | --- |
| lying on | 40 | false positive | lying pose evidence 필요 |
| standing on | 40 | false negative | upright support pose evidence 필요 |

class-pair 기준으로는 `sofa->floor`, `couch->floor`, `kitchen cabinet->floor`,
`table->floor`, `shelf->floor`에 failure가 집중된다. 이는 object class prior와
floor-support semantics가 실제 pose state와 강하게 얽혀 있음을 의미한다.

### Repair Decision

다음 방향으로 고정한다.

| Step | Scope | Action |
| --- | --- | --- |
| R1 | standing on | upright-support subtype target 정의 |
| R2 | lying on | horizontal-support subtype target 정의 |
| R3 | supported by | superordinate support decomposition / relabel / abstain route로 이동 |
| R4 | Q_e | pose observability를 C_e와 분리 |
| R5 | controls | wrong-T, shuffled-G, within-class-pair shuffled-G, subject/object swap control 재구성 |

따라서 다음 TODO는:

```text
support_contact_generalization_repair_materialization
```

이 단계에서는 `standing on`과 `lying on`을 pose-aware subtype으로 다시
materialize하고, ambiguous support/contact는 binary accept/reject가 아니라
relabel 또는 abstain으로 분리해야 한다. `Q_e`는 pose/mesh/multiview 관측
가능성 label에는 사용하되, `C_e = compatibility(T_e, G_e)` main input에는 넣지
않는다.

## Support/Contact Repair Materialization

위 repair decision에 따라 `standing on` / `lying on`을 바로 다시 metric으로
돌리지 않고, 먼저 mixed class-pair 기준의 repaired target surface를 materialize했다.

Runtime artifact:

```text
experiments/H002_compatibility_routing/support_contact_repair_materialization/latest/
```

생성 파일:

```text
row_manifest.json
schema_precheck.json
validation_errors.jsonl
gate_failures.jsonl
model_safe_binary_no_class.jsonl
model_safe_binary_with_class_semantic.jsonl
model_safe_binary_geometry_only.jsonl
model_safe_selective_no_class.jsonl
hidden_manifest.jsonl
group_manifest.jsonl
class_pair_quota.csv
pose_proxy_diagnostics.csv
```

Docker service:

```text
h002-support-contact-repair-materialize
```

결과:

```text
status = h002_support_contact_generalization_repair_materialization_ready
validation_errors = 0
gate_failures = 1
hard_input_rows = 3178
hard_input_groups = 1589
mixed_class_pairs = 4
main_binary_groups = 20
model_safe_binary_no_class = 40
model_safe_binary_with_class_semantic = 40
model_safe_binary_geometry_only = 40
model_safe_selective_no_class = 3178
single_subtype_groups = 1536
mixed_overflow_groups = 33
metric_rerun_ready = false
```

### Materialization Logic

기존 hard route는 class-pair shortcut이 너무 강했다. 따라서 이번 materialization은
같은 class-pair 내부에서 `standing on` positive와 `lying on` positive가 모두
존재하는 경우만 main binary target으로 남겼다. 나머지는 binary target으로 억지로
사용하지 않고 abstain/diagnostic으로 분리했다.

남은 mixed class-pair는 다음 네 개뿐이다.

| Class pair | standing positive groups | lying positive groups | selected binary rows |
| --- | ---: | ---: | ---: |
| box->floor | 23 | 5 | 20 |
| item->floor | 4 | 2 | 8 |
| object->floor | 12 | 2 | 8 |
| shoes->floor | 4 | 1 | 4 |

따라서 main binary rows는 `40`개뿐이다. label은 `20/20`으로 균형이고,
predicate도 `standing on 20`, `lying on 20`으로 균형이지만, row 수와 class-pair
수가 너무 작다.

### Gate Decision

이번 materialization은 schema 관점에서는 정상이다.

```text
blocked_field_hits = 0
validation_errors = 0
```

하지만 metric rerun gate는 통과하지 못했다.

```text
required_binary_rows = 200
required_mixed_class_pairs = 10
actual_binary_rows = 40
actual_mixed_class_pairs = 4
```

따라서 다음 단계는 metric runner가 아니라 capacity decision이다.

```text
next_todo = support_contact_generalization_repair_capacity_decision
```

해석:

- support/contact에서 `standing on` / `lying on`을 제대로 검증하려면 단순히 모든
  GT pair를 쓰면 안 된다.
- 대부분의 class-pair는 한 predicate만 positive라서 class-pair만으로도 label이
  결정된다.
- shortcut을 막고 나면 남는 main binary target이 너무 작다.
- 따라서 support/contact를 solved route로 밀려면 추가 mining, visual/mesh audit,
  또는 `supported by` relabel/abstain decomposition이 필요하다.
- 현재 상태에서는 support/contact를 metric rerun하거나 main solved claim으로
  올리면 안 된다.

## Support/Contact Capacity Decision

repair materialization 이후 support/contact를 계속 metric route로 밀지, 아니면
diagnostic/failure taxonomy로 고정할지 결정했다.

Runtime artifact:

```text
experiments/H002_compatibility_routing/support_contact_capacity_decision/latest/
```

생성 파일:

```text
summary.json
capacity_options.csv
decision_matrix.csv
paper_boundary.csv
reopen_conditions.csv
class_pair_capacity.csv
validation_errors.jsonl
```

Docker service:

```text
h002-support-contact-capacity-decision
```

결과:

```text
status = h002_support_contact_generalization_repair_capacity_decision_ready
validation_errors = 0
binary_rows = 40
mixed_class_pairs = 4
selective_rows = 3178
abstain_rows = 3138
selected_path = freeze_support_contact_as_diagnostic_failure_taxonomy_no_metric_rerun
support_contact_metric_rerun_allowed = false
support_contact_solved_claim_allowed = false
next_todo = pobs_prel_observability_repair
```

### Decision

선택지는 네 가지였다.

| Option | 판단 | 이유 |
| --- | --- | --- |
| strict mixed class-pair 40 rows로 metric 실행 | reject | underpowered metric / unstable CI |
| single-subtype class-pair까지 풀어서 사용 | reject for main metric | class-pair shortcut이 다시 들어옴 |
| 추가 visual/mesh audit으로 support/contact 계속 확장 | defer | 가능하지만 새로운 independent label 구축이 필요 |
| support/contact를 diagnostic으로 고정하고 observability repair로 이동 | select | 현재 가장 원리적으로 안전 |

따라서 support/contact는 현재 H002 paper path에서 solved route가 아니다.
대신 다음 메시지로 사용한다.

```text
support/contact is a challenging diagnostic route showing that some relation
families require observability-aware abstain or relabel handling.
```

blocked wording:

```text
support/contact is solved.
support/contact metric rerun is paper evidence.
the route-aware framework is validated for all physical relations.
```

### Reopen Conditions

support/contact를 다시 solved route 후보로 열려면 아래 조건이 필요하다.

| Condition | Requirement | Current |
| --- | --- | --- |
| independent pose audit capacity | >= 200 binary rows and >= 10 mixed class-pairs | 40 rows / 4 class-pairs |
| observability labels | observable / unobservable / ambiguous label 필요 | 없음 |
| supported_by decomposition | subtype mapping + relabel/abstain target 필요 | 현재 없음 |
| shortcut control | predicate/class-pair/source/rank shortcut이 target을 못 풀어야 함 | 현재 single-subtype class-pair가 지배 |

결론적으로 support/contact는 실패가 아니라 route-aware framework의 경계 조건을
보여주는 diagnostic evidence로 남긴다. 다음 experiment-stage TODO는:

```text
pobs_prel_observability_repair
```

## p_obs / p_rel Observability Repair

support/contact capacity decision 이후, `p_obs/p_rel`을 main claim으로 올리기
위해 필요한 observability target을 점검했다. 이 단계에서는 metric을 다시 돌리지
않고, real visual/mesh observability label을 만들기 위한 schema와 audit queue를
고정했다.

Runtime artifact:

```text
experiments/H002_compatibility_routing/pobs_prel_observability_repair/latest/
```

생성 파일:

```text
summary.json
observability_gap.csv
label_schema.csv
observability_label_queue.jsonl
queue_summary.csv
gate_plan.csv
next_steps.csv
validation_errors.jsonl
```

Docker service:

```text
h002-pobs-prel-observability-repair
```

결과:

```text
status = h002_pobs_prel_observability_repair_ready
validation_errors = 0
asset_observability_label_counts = observable:23062
has_real_negative_or_ambiguous_observability_labels = false
p_rel_calibrated_ECE_10 = 0.223458
observability_label_queue_rows = 265
pobs_prel_metric_rerun_allowed = false
pobs_prel_calibrated_solved_claim_allowed = false
next_todo = pobs_prel_observability_label_fill
```

### 핵심 판단

현재 `p_obs`의 높은 성능은 실제 negative/ambiguous observability label을 푼 것이
아니다. 기존 asset audit label은 모두 `observable`이고, `no_view`,
`low_visibility`, `missing_mesh`, `shuffled_view`, `wrong_pair_evidence`는
synthetic missing-evidence control이다.

따라서 다음 주장은 아직 막혀 있다.

```text
calibrated p_obs/p_rel is solved.
```

이 주장을 열려면 real visual/mesh audit에서 다음 label이 필요하다.

| Label | p_obs target | p_rel target allowed | 의미 |
| --- | ---: | --- | --- |
| observable_clear | 1 | true | relation accept/reject를 판단할 evidence가 충분함 |
| unobservable_missing_evidence | 0 | false | 필요한 evidence가 없음, 가려짐, 깨짐 |
| ambiguous_evidence | 0 | false | evidence는 있으나 subtype/accept-reject 판단이 애매함 |
| unsupported_route | - | false | 현재 route materialization 자체가 부족함 |

### Audit Queue

생성한 audit queue는 `265` rows다.

| Queue kind | Rows | 역할 |
| --- | ---: | --- |
| support_contact_single_subtype_abstain | 120 | support/contact ambiguity 후보 |
| support_contact_mixed_overflow_abstain | 60 | mixed class-pair overflow ambiguity 후보 |
| support_contact_binary_control | 40 | observable/relation control 후보 |
| route_observable_control | 45 | non-support observable control 후보 |

이 queue의 `codex_seed_hint_not_gt`는 정답이 아니다. visual/mesh evidence를 보고
`observable_clear`, `unobservable_missing_evidence`, `ambiguous_evidence` 중 하나로
채워야 한다.

### Gate Decision

현재 gate는 다음과 같다.

| Gate | Current | Decision |
| --- | --- | --- |
| real observability label classes | `observable:23062` only | blocked |
| audit queue | 265 rows | label collection ready |
| support/contact ambiguous candidates | available | audit source ready |
| attachment/containment route rows | 0 / 0 | broad observability claim blocked |
| calibrated p_obs/p_rel claim | not met | blocked |

따라서 다음 experiment-stage TODO는:

```text
pobs_prel_observability_label_fill
```

label fill과 ingestion이 끝나기 전에는 `p_obs/p_rel` metric rerun을 하지 않는다.

## p_obs / p_rel Observability Label Fill, Ingestion, Schema Audit

`pobs_prel_observability_repair` 이후 생성된 `265`개 audit queue를 Codex가 먼저
채우고, 이를 ingestion/schema audit까지 진행했다. 이 단계의 목적은 바로 metric을
다시 돌리는 것이 아니라, `Q_e` observability label이 model-safe feature와 hidden
label로 분리될 수 있는지 확인하는 것이다.

Runtime artifacts:

```text
experiments/H002_compatibility_routing/pobs_prel_observability_labels/latest/
experiments/H002_compatibility_routing/pobs_prel_observability_ingestion/latest/
experiments/H002_compatibility_routing/pobs_prel_observability_schema_audit/latest/
```

Docker services:

```text
h002-pobs-prel-observability-label-fill
h002-pobs-prel-observability-ingest
h002-pobs-prel-observability-schema-audit
```

결과:

```text
label_fill_status = h002_pobs_prel_observability_label_fill_ready
ingestion_status = h002_pobs_prel_observability_label_ingestion_ready
schema_audit_status = h002_pobs_prel_observability_schema_audit_ready
validation_errors = 0 / 0 / 0
rows = 265
observable_clear = 135
ambiguous_evidence = 126
unobservable_missing_evidence = 4
accept = 66
reject = 69
abstain = 130
blocked_field_hits = 0
human_confirmed = false
metric_rerun_allowed_now = false
next_todo = pobs_prel_observability_metric_gate_decision
```

### 해석

이번 단계에서 해결된 것은 다음이다.

| 항목 | 결과 |
| --- | --- |
| audit queue fill | `265/265` 완료 |
| label 다양성 | `observable_clear`, `ambiguous_evidence`, `unobservable_missing_evidence` 확보 |
| Q_e / hidden label 분리 | 통과 |
| model-safe blocked field | `0` hits |
| row alignment | Q_e view, p_rel view, hidden label 모두 `265` rows |

하지만 이 label은 사람이 직접 확인한 GT가 아니다. provenance는
`codex_filled_not_human_confirmed`이며, `human_confirmed=false`로 명시했다. 따라서
이번 결과는 p_obs/p_rel metric rerun을 위한 schema 준비 단계로는 충분하지만,
`calibrated p_obs/p_rel is solved` 같은 paper claim을 바로 여는 근거는 아니다.

### 다음 판단

다음 TODO는 `pobs_prel_observability_metric_gate_decision`이다. 여기서 결정해야 할
것은 다음이다.

```text
Can Codex-filled observability labels be used for a diagnostic p_obs/p_rel
metric rerun, or should the rerun remain blocked until user-reviewed /
human-confirmed labels are available?
```

보수적 기준에서는 metric rerun을 하더라도 `diagnostic-only`로 제한하는 것이 맞다.
paper-level calibrated p_obs/p_rel claim은 user-reviewed 또는 human-confirmed
observability labels가 확보되기 전까지 계속 막아둔다.

## p_obs / p_rel User-Confirmed Observability Metric Rerun

사용자가 Codex-filled observability label을 확인 완료했다고 판단했으므로, metric
gate를 열고 diagnostic rerun을 수행했다. 단, raw label file의 provenance는 여전히
Codex fill에서 시작되었기 때문에, 이 결과는 paper-level independent GT benchmark가
아니라 `user-confirmed diagnostic subset`으로 해석한다.

Runtime artifacts:

```text
experiments/H002_compatibility_routing/pobs_prel_observability_metric_gate/latest/
experiments/H002_compatibility_routing/pobs_prel_observability_metric/latest/
```

Docker services:

```text
h002-pobs-prel-observability-metric-gate
h002-pobs-prel-observability-metric-runner
```

Metric protocol:

```text
train = existing internal_train p_obs/p_rel materialization
eval = user-confirmed 265-row observability subset
pobs_train = 24340
pobs_eval = 265
prel_train = 4868
prel_eval = 135
official_test_used = false
```

결과:

| Metric | Value | 판단 |
| --- | ---: | --- |
| p_obs AUROC | 0.500000 | fail |
| p_obs ECE@10 | 0.446174 | fail |
| p_rel AUROC | 0.774704 | pass signal |
| p_rel ECE@10 | 0.083819 | usable diagnostic |
| decision accuracy | 0.335849 | fail |
| decision macro-F1 | 0.331637 | fail |
| validation errors | 0 | pass |

Queue별 결과:

| Queue | Rows | Median p_obs | Predicted abstain rate | 해석 |
| --- | ---: | ---: | ---: | --- |
| route_observable_control | 45 | 0.955608 | 0.000 | observable control은 결정함 |
| support_contact_binary_control | 40 | 0.955608 | 0.000 | observable binary도 결정함 |
| support_contact_mixed_overflow_abstain | 60 | 0.955608 | 0.000 | 일부 abstain label을 놓침 |
| support_contact_single_subtype_abstain | 120 | 0.955608 | 0.000 | 전부 abstain해야 하지만 전부 결정함 |

Observability label별 결과:

| Label | Rows | Median p_obs | Predicted abstain rate |
| --- | ---: | ---: | ---: |
| observable_clear | 135 | 0.955608 | 0.000 |
| ambiguous_evidence | 126 | 0.955608 | 0.000 |
| unobservable_missing_evidence | 4 | 0.955608 | 0.000 |

### Interpretation

이 rerun의 결론은 명확하다.

`p_rel`은 observable subset에서 어느 정도 relation reliability 신호를 갖는다.
반면 `p_obs`는 현재 `Q_e` feature로 ambiguous/missing-evidence row를 전혀 구분하지
못한다. 즉, p_obs 실패는 label ingestion 문제가 아니라 `Q_e` feature/schema
부족 문제다.

따라서 현재 claim boundary는 다음과 같다.

```text
p_rel diagnostic signal exists on user-confirmed observable rows.
p_obs / abstention is not solved.
calibrated p_obs/p_rel solved claim remains blocked.
```

### Next

다음 TODO는:

```text
pobs_prel_observability_metric_result_review
```

리뷰에서 결정할 것은 두 가지다.

1. p_obs/p_rel을 현재 H002 paper에서 framework component로만 둘지
2. p_obs를 살리기 위해 `Q_e`를 어떻게 repair할지

현재 결과만 보면 가장 필요한 repair는 `Q_e`에 실제 observability/ambiguity evidence를
넣는 것이다. 예를 들어 visual/mesh coverage, subtype ambiguity, support-contact
pose conflict, missing contact-surface evidence, view quality를 명시적 feature로
추가해야 한다.

## p_obs / p_rel Observability Metric Result Review

위 diagnostic rerun을 별도 review artifact로 고정했다.

Runtime artifact:

```text
experiments/H002_compatibility_routing/pobs_prel_observability_metric_review/latest/
```

Docker service:

```text
h002-pobs-prel-observability-metric-review
```

결과:

```text
status = h002_pobs_prel_observability_metric_result_review_ready
validation_errors = 0
p_obs_status = failed_observability_gate
p_rel_status = diagnostic_signal_present
selective_decision_status = failed_due_to_no_abstain_behavior
pobs_prel_framework_component_allowed = true
pobs_prel_solved_claim_allowed = false
paper_promotion_pass = false
next_todo = pobs_prel_qe_repair_plan
```

### 핵심 원인

리뷰 결과, 실패 원인은 metric runner나 label ingestion이 아니라 `Q_e` feature/label
mismatch다.

| Observability label | Rows | Q_e sufficient rows | Alignment |
| --- | ---: | ---: | --- |
| observable_clear | 135 | 135 | aligned/partial |
| ambiguous_evidence | 126 | 126 | mismatch |
| unobservable_missing_evidence | 4 | 4 | mismatch |

즉 hidden label은 `ambiguous_evidence` 또는 `unobservable_missing_evidence`로
바뀌었지만, model-safe `Q_e`는 여전히 모든 row를 `sufficient`로 보고 있다. 그래서
학습된 `p_obs`는 모든 row에 높은 score를 주고 abstain을 만들지 못한다.

### Claim Boundary

현재 허용 가능한 주장은 다음이다.

```text
p_rel has diagnostic reliability signal on user-confirmed observable rows.
```

막힌 주장은 다음이다.

```text
p_obs / abstention is solved.
calibrated p_obs/p_rel is a paper-level quantitative result.
```

### Q_e Repair Plan

다음 단계는 p_obs/p_rel 전체 metric rerun이 아니라 `Q_e` repair plan이다.

| Priority | Repair | 이유 |
| ---: | --- | --- |
| 1 | audit-aligned Q_e state로 교체 | 현재 Q_e가 ambiguous/missing row도 sufficient로 표시함 |
| 2 | visual/mesh coverage feature 추가 | view count, crop quality, mesh/contact-surface availability, occlusion이 필요함 |
| 3 | support/contact pose ambiguity feature 추가 | abstain row 대부분이 missing이 아니라 standing/lying subtype ambiguity임 |
| 4 | balanced observability train row 구성 | train은 synthetic missing control 중심이고 eval은 user-confirmed ambiguity label임 |
| 5 | p_obs-only repair rerun 먼저 수행 | p_rel은 신호가 있으므로 p_obs bottleneck을 먼저 분리해야 함 |

따라서 다음 H002 TODO는:

```text
pobs_prel_qe_repair_plan
```

## p_obs / p_rel Q_e Repair Plan

`pobs_prel_observability_metric_result_review` 이후, Q_e repair plan을 Docker
artifact로 고정했다.

Runtime artifact:

```text
experiments/H002_compatibility_routing/pobs_prel_qe_repair_plan/latest/
```

Docker service:

```text
h002-pobs-prel-qe-repair-plan
```

결과:

```text
status = h002_pobs_prel_qe_repair_plan_ready
validation_errors = 0
failure_cause = qe_feature_label_mismatch
ambiguous_rows_marked_sufficient = 126
missing_rows_marked_sufficient = 4
pobs_prel_solved_claim_allowed = false
next_todo = pobs_prel_qe_repair_materialization
```

### Repaired Q_e v2 Schema

| Block | 목적 | 예시 feature |
| --- | --- | --- |
| `Q_e_asset_availability` | missing evidence와 usable evidence 구분 | mesh, point pair crop, contact surface proxy, OBB availability |
| `Q_e_visual_coverage` | view/crop quality 기반 observability 판단 | co-visible view count, crop quality, visibility ratio, occlusion proxy |
| `Q_e_geometry_quality` | geometry가 route 판단에 충분한지 측정 | geometry feature coverage, surface patch, local point density, normal availability |
| `Q_e_ambiguity` | geometry는 있지만 판단이 애매한 경우 표현 | support subtype count, standing/lying pose conflict, class-pair subtype entropy |
| `Q_e_state_v2` | 기존 sufficient-only state 대체 | sufficient / limited / ambiguous / missing |

### Materialization Contract

다음 단계에서 만들어야 하는 산출물은 다음이다.

| Artifact | 역할 |
| --- | --- |
| `model_safe_qe_v2_train.jsonl` | internal train p_obs-only 학습 view |
| `model_safe_qe_v2_eval.jsonl` | 265-row user-confirmed observability subset 평가 view |
| `hidden_observability_v2_labels.jsonl` | hidden label, model-safe view에서 제외 |
| `qe_v2_schema_audit/latest/` | leakage / schema / feature-label alignment audit |

중요한 제한은 다음이다.

```text
Q_e v2는 observability_label, decision_label, rel_label, source score/rank,
p_geom_valid, codex seed hint, hidden queue kind를 직접 input으로 쓰면 안 된다.
```

### Pass / Fail Gates

| Gate | Threshold |
| --- | --- |
| schema separation | validation_errors=0 and blocked_field_hits=0 |
| Q_e label alignment | ambiguous/missing rows are not all q_e_sufficient_v2=1 |
| p_obs signal | p_obs AUROC >= 0.70 on user-confirmed subset |
| abstain behavior | ambiguous/missing abstain recall >= 0.70 and observable abstain false-positive <= 0.30 |
| calibration sanity | p_obs ECE@10 <= 0.20 diagnostic, <= 0.10 paper promotion |

### Decision

이 계획은 p_obs 실패를 posterior 결합 방식 문제가 아니라 representation 문제로
고정한다. 따라서 다음 단계는 full p_obs/p_rel metric rerun이 아니라 repaired `Q_e`
view materialization이다.

다음 H002 TODO:

```text
pobs_prel_qe_repair_materialization
```

## p_obs / p_rel Q_e Repair Materialization

`pobs_prel_qe_repair_plan` 이후 repaired `Q_e v2` view를 Docker artifact로
materialize했다.

Runtime artifact:

```text
experiments/H002_compatibility_routing/pobs_prel_qe_repair_materialization/latest/
```

Docker service:

```text
h002-pobs-prel-qe-repair-materialize
```

결과:

```text
status = h002_pobs_prel_qe_repair_materialization_ready
validation_errors = 0
blocked_field_hits = 0
train_qe_v2_rows = 14604
eval_qe_v2_rows = 265
next_todo = pobs_prel_qe_repair_schema_audit
```

### Materialized Views

| Artifact | Rows | 역할 |
| --- | ---: | --- |
| `model_safe_qe_v2_train.jsonl` | 14,604 | p_obs-only train view |
| `model_safe_prel_v2_train.jsonl` | 14,604 | later selective rerun용 train view |
| `model_safe_qe_v2_eval.jsonl` | 265 | diagnostic eval view |
| `model_safe_prel_v2_eval.jsonl` | 265 | later selective rerun용 eval view |
| `hidden_observability_v2_labels.jsonl` | 14,869 | train/eval hidden labels |

Train label balance:

| Label | Rows |
| --- | ---: |
| `observable_clear` | 4,868 |
| `ambiguous_evidence` | 4,868 |
| `unobservable_missing_evidence` | 4,868 |

Eval label alignment:

| Eval label | Rows | Q_e v2 state |
| --- | ---: | --- |
| `observable_clear` | 135 | `sufficient` |
| `ambiguous_evidence` | 126 | `ambiguous` |
| `unobservable_missing_evidence` | 4 | `missing` |

### 해석

이 단계는 이전 `p_obs_AUROC=0.5` 실패의 직접 원인이었던
`ambiguous/missing row도 모두 sufficient로 들어가는 문제`를 artifact 수준에서
수정했다. 즉, 이제 model-safe `Q_e v2`는 hidden observability label과 분리되어
있고, 평가 subset에서 ambiguous/missing row가 더 이상 sufficient state로 들어가지
않는다.

단, 이 materialization은 아직 paper-level calibrated p_obs/p_rel solved evidence가
아니다. Eval `Q_e v2`는 independent visual/mesh annotation이 아니라 audit-proxy
diagnostic에 기반한다. 따라서 허용되는 다음 단계는 full selective-decision rerun이
아니라 schema audit과 p_obs-only diagnostic smoke이다.

다음 H002 TODO:

```text
pobs_prel_qe_repair_schema_audit
```

## p_obs / p_rel Q_e Repair Schema Audit

`pobs_prel_qe_repair_materialization` 이후 repaired `Q_e v2` view의
model-safe / hidden separation을 Docker audit으로 검증했다.

Runtime artifact:

```text
experiments/H002_compatibility_routing/pobs_prel_qe_repair_schema_audit/latest/
```

Docker service:

```text
h002-pobs-prel-qe-repair-schema-audit
```

결과:

```text
status = h002_pobs_prel_qe_repair_schema_audit_ready
validation_errors = 0
blocked_field_hits = 0
schema_separation = true
row_alignment = true
qe_required_blocks = true
train_label_balance = true
eval_ambiguous_missing_not_sufficient = true
pobs_only_diagnostic_metric_allowed = true
full_selective_decision_rerun_allowed = false
paper_level_pobs_prel_solved_claim_allowed = false
next_todo = pobs_prel_qe_repair_pobs_only_metric
```

### Audit Checks

| Check | Result |
| --- | --- |
| model-safe blocked field hits | `0` |
| train Q_e / p_rel / hidden row alignment | `14,604 / 14,604 / 14,604`, pass |
| eval Q_e / p_rel / hidden row alignment | `265 / 265 / 265`, pass |
| Q_e-only view block constraint | pass |
| p_rel view required blocks | `T_e`, `G_e`, `Q_e`, `Z_e`, pass |
| required Q_e v2 blocks | pass |
| train label balance | `4,868` each, pass |
| eval ambiguous/missing not sufficient | pass |

Q_e v2 feature-label alignment:

| Split | Label | Rows | Q_e v2 state |
| --- | --- | ---: | --- |
| train | `observable_clear` | 4,868 | sufficient |
| train | `ambiguous_evidence` | 4,868 | limited 2,425 / ambiguous 2,443 |
| train | `unobservable_missing_evidence` | 4,868 | missing |
| eval | `observable_clear` | 135 | sufficient |
| eval | `ambiguous_evidence` | 126 | ambiguous |
| eval | `unobservable_missing_evidence` | 4 | missing |

### 해석

이 audit은 이전 `p_obs` 실패 원인이었던 Q_e state mismatch가 materialized
artifact에서는 해결되었음을 확인한다. 특히 eval subset에서 ambiguous/missing row가
더 이상 `sufficient` state로 들어가지 않는다.

하지만 이 단계는 아직 metric 성능 검증이 아니다. 따라서 허용되는 다음 단계는
`p_obs-only` diagnostic smoke test이고, full selective-decision rerun 및
paper-level calibrated p_obs/p_rel solved claim은 계속 막아둔다.

다음 H002 TODO:

```text
pobs_prel_qe_repair_pobs_only_metric
```

## p_obs / p_rel Q_e Repair p_obs-Only Metric

`pobs_prel_qe_repair_schema_audit` 이후, repaired `Q_e v2`만 사용해
`p_obs`가 observable row와 ambiguous/missing-evidence row를 구분하는지
diagnostic smoke test를 실행했다. 이 단계에서는 `p_rel`, accept/reject head,
source score, predicate/geometry compatibility는 사용하지 않았다.

Runtime artifact:

```text
experiments/H002_compatibility_routing/pobs_prel_qe_repair_pobs_only_metric/latest/
```

Docker service:

```text
h002-pobs-prel-qe-repair-pobs-only-metric
```

결과:

```text
status = h002_pobs_prel_qe_repair_pobs_only_metric_ready
validation_errors = 0
train_rows = 14604
eval_rows = 265
p_obs_AUROC = 1.000000
p_obs_ECE_10 = 0.049266
p_obs_Brier = 0.004222
p_obs_NLL = 0.051518
abstain_precision = 1.000000
abstain_recall = 1.000000
observable_false_abstain_rate = 0.000000
false_observable_rate = 0.000000
diagnostic_pass = true
next_todo = pobs_prel_qe_repair_pobs_metric_review
```

### Baseline Comparison

| Score | AUROC | ECE@10 | Abstain Recall | 해석 |
| --- | ---: | ---: | ---: | --- |
| `p_obs_learned(Q_e v2)` | 1.000000 | 0.049266 | 1.000000 | repaired Q_e가 observable/abstain을 완전히 분리 |
| direct `Q_e state_code` | 1.000000 | 0.166415 | 1.000000 | state 자체도 diagnostic signal을 가짐 |
| legacy all-sufficient | 0.500000 | 0.490566 | 0.000000 | 이전 실패 구조 |

Observability label별 learned p_obs:

| Label | Rows | Mean p_obs | Pred abstain rate |
| --- | ---: | ---: | ---: |
| `observable_clear` | 135 | 0.991225 | 0.000000 |
| `ambiguous_evidence` | 126 | 0.093758 | 1.000000 |
| `unobservable_missing_evidence` | 4 | 0.014320 | 1.000000 |

Risk-coverage 관점에서는 상위 50% coverage까지 unobservable risk가 `0`이고, 이후
ambiguous/missing row가 포함되면서 risk가 증가한다.

### 해석

이 결과는 이전 `p_obs_AUROC=0.5` 실패가 posterior 결합 문제가 아니라 `Q_e`
representation 문제였다는 해석을 지지한다. Repaired `Q_e v2`를 쓰면 p_obs-only
smoke test는 통과한다.

다만 이 결과는 paper-level calibrated p_obs/p_rel solved evidence가 아니다. Eval
`Q_e v2`는 independent visual/mesh annotation이 아니라 audit-proxy diagnostic에
기반하고, direct `Q_e state_code`도 같은 수준의 분리력을 보인다. 따라서 다음
단계에서는 이 성능이 진짜 observability reasoning인지, proxy shortcut인지 리뷰해야
한다.

다음 H002 TODO:

```text
pobs_prel_qe_repair_pobs_metric_review
```

## p_obs / p_rel Q_e Repair p_obs Metric Review

`pobs_prel_qe_repair_pobs_only_metric` 이후, repaired `Q_e v2`의 p_obs-only
통과가 실제 paper claim으로 승격 가능한지 review했다.

Runtime artifact:

```text
experiments/H002_compatibility_routing/pobs_prel_qe_repair_pobs_metric_review/latest/
```

Docker service:

```text
h002-pobs-prel-qe-repair-pobs-metric-review
```

결과:

```text
status = h002_pobs_prel_qe_repair_pobs_metric_review_ready
validation_errors = 0
p_obs_AUROC = 1.000000
p_obs_ECE_10 = 0.049266
abstain_recall = 1.000000
direct_Qe_state_AUROC = 1.000000
proxy_shortcut_risk = high
pobs_required_for_core_claim = false
pobs_main_claim_allowed = false
pobs_optional_framework_component = true
full_selective_decision_rerun_now = false
selected_path = demote_pobs_to_optional_diagnostic_keep_core_claim_on_Ce_source_reranking
next_todo = h002_core_claim_without_pobs_boundary_update
```

### 판단

`p_obs`는 현재 H002 core claim에 필수적이지 않다.

H002의 핵심 문제는 기존 relation source score가 semantic plausibility,
geometry compatibility, source confidence가 섞인 single score라는 점이다. 이
문제에 직접 대응하는 구성은 다음이다.

```text
T_e = predicate / relation-family semantic content
G_e = geometry evidence
Z_e = source score / rank
C_e = compatibility(T_e, G_e)
S2(e) = normalized_source_score(Z_e) * C_e
```

반면 `p_obs`는 “현재 evidence로 판단 가능한가?”라는 selective decision 문제다.
이건 attachment, containment, occlusion-heavy, missing-evidence relation으로
claim을 넓힐 때 필요하지만, 현재 가장 강한 validation-level claim인 comparison
route source reranking에는 필수 구성요소가 아니다.

### 왜 main claim에서 내리는가

- direct `Q_e state_code`도 AUROC `1.000000`이므로 learned p_obs가 독립적인
  observability reasoning을 배웠다고 보기 어렵다.
- eval `Q_e v2`는 independent visual/mesh annotation이 아니라 audit-proxy
  diagnostic material이다.
- `unobservable_missing_evidence` row가 `4`개뿐이므로 missing-evidence
  generalization을 주장할 수 없다.
- 이번 run은 p_obs-only smoke test이고, full p_obs/p_rel selective-decision
  rerun이 아니다.

따라서 `p_obs`는 optional diagnostic/future component로 유지하고, 현재 H002의
main claim은 `C_e` compatibility source reranking에 집중하는 것이 원리적으로 더
자연스럽다.

다음 H002 TODO:

```text
h002_core_claim_without_pobs_boundary_update
```
