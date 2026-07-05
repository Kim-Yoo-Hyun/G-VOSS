# H002 Report 0702: Official Metric Result Review and Paper-Level Experiment Gate

## 1. 현재 위치

H002는 현재 `Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations`
방향으로 진행 중이다. 핵심은 relation source score를 그대로 신뢰하지 않고,
relation reliability를 구성하는 요소를 다음처럼 분리하는 것이다.

```text
T_e = semantic content
Z_e = source confidence
G_e = predicate-independent geometry evidence
C_e = compatibility(T_e, G_e)
Q_e = evidence quality / observability
p_obs = P(evidence is sufficient to decide)
p_rel = P(relation is reliable | evidence is observable)
```

이번 단계에서는 `p_rel` 또는 `p_obs`까지 가지 않고, 먼저 `C_e =
compatibility(T_e, G_e)`가 official validation candidate pool에서도 의미 있는지를 검증했다.

## 2. 방금 진행한 내용

직전 단계에서 frozen protocol을 따르는 Docker official metric runner를 실행했다.

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-official-metric-runner
```

생성 위치:

```text
experiments/H002_compatibility_routing/official_evaluation/latest/
artifacts/compatibility_dataset_v3_official_metric_runner_after_protocol_freeze/
```

검증된 조건:

- official validation rows는 eval-only로 사용했다.
- official test는 사용하지 않았다.
- trainable view는 internal train split에서 fit했다.
- main `C_e`에는 `T_e`와 `G_e`만 사용했다.
- `Z_e`, `Q_e`, H001 `p_geom_valid`, hidden construction fields는 main `C_e`에서 제외했다.
- validation errors는 `0`이다.

## 2.1 Validation Result와 Test Result 분리

H002의 현재 결과는 **official validation result**다. **official test result는 아직 없다.**
이 둘은 반드시 분리해서 기록해야 한다.

| 구분 | 현재 상태 | 용도 | Paper claim에서의 표현 |
| --- | --- | --- | --- |
| internal train | `4868` rows | trainable view fitting | 학습/fit에 사용 |
| internal dev | `1044` rows | protocol/debug sanity | official result 아님 |
| official validation | `23062` rows | eval-only metric | validation evidence |
| official test | 사용하지 않음 | 최종 blind evaluation 후보 | 현재 claim 금지 |

따라서 현재 보고 가능한 것은 다음이다.

```text
official_validation_metric_produced = true
official_validation_eval_only = true
official_test_usage = false
paper_metric_promoted = false
```

해석:

- validation result는 paper-level experiment gate를 판단하기 위한 evidence로 사용할 수 있다.
- 하지만 validation 결과를 official test 결과처럼 쓰면 안 된다.
- test result를 만들려면 현재처럼 claim boundary, schema, control, promotion gate를 먼저
  고정한 뒤 별도 test protocol을 열어야 한다.
- 지금 단계에서는 test set을 보지 않았으므로, reviewer-facing 표현도
  "validation evaluation" 또는 "official validation split"으로 제한해야 한다.

## 3. Official Validation Metric 결과

Primary metric은 frozen protocol에서 정한 `macro_family_AUROC`다.
Overall AUROC는 `relative_horizontal` row 수가 전체를 지배할 수 있으므로 secondary로만 본다.

Official validation row 구성은 다음과 같다.

| Family | Negative | Positive | Total |
| --- | ---: | ---: | ---: |
| `relative_horizontal` | 13290 | 5474 | 18764 |
| `relative_vertical` | 390 | 390 | 780 |
| `size_relative` | 170 | 170 | 340 |
| `support_contact` | 1589 | 1589 | 3178 |
| **Total** | **15439** | **7623** | **23062** |

| View | Macro-family AUROC | Weighted-family AUROC | Overall AUROC |
| --- | ---: | ---: | ---: |
| `M1_T_semantic_only` | 0.417633 | 0.455374 | 0.404333 |
| `M2_G_geometry_only` | 0.500000 | 0.500000 | 0.528329 |
| `M3_T_plus_G_concat` | 0.416923 | 0.454625 | 0.406137 |
| `M4_TxG_compatibility` | 0.835547 | 0.720781 | 0.724835 |

Family-level M4:

| Family | Rows | M4 AUROC | Balanced accuracy | 판단 |
| --- | ---: | ---: | ---: | --- |
| `relative_vertical` | 780 | 0.991321 | 0.957692 | main evidence 후보 |
| `size_relative` | 340 | 0.999585 | 0.988235 | main evidence 후보 |
| `relative_horizontal` | 18764 | 0.719568 | 0.701522 | caveat付き 후보 |
| `support_contact` | 3178 | 0.631712 | 0.566394 | diagnostic/challenging |

## 4. Control 결과

Macro-family 기준 control 결과는 다음과 같다.

| Comparison | Delta AUROC | 해석 |
| --- | ---: | --- |
| `M4_vs_M1` | 0.417913 | semantic-only보다 강함 |
| `M4_vs_M2` | 0.335547 | geometry-only보다 강함 |
| `M4_vs_M3` | 0.418624 | 단순 concat보다 강함 |
| `M4_vs_wrong_T_within_route` | 0.671120 | predicate가 틀리면 크게 무너짐 |
| `M4_vs_wrong_T_across_route` | 0.270464 | route 밖 wrong predicate에서도 저하 |
| `M4_vs_shuffled_G_global` | 0.341733 | geometry를 섞으면 저하 |
| `M4_vs_shuffled_G_within_family` | 0.318753 | family 내부 geometry shuffle도 저하 |
| `M4_vs_subject_object_swap` | 0.717045 | directed pair control 저하 |
| `M4_vs_sign_flip` | 0.717045 | signed geometry control 저하 |
| `M4_vs_horizontal_frame_swap` | 0.038149 | macro 기준 margin 약함 |

중요한 해석:

- `M4_TxG_compatibility`가 semantic-only, geometry-only, 단순 concat을 모두 이긴다.
- wrong-`T`와 shuffled-`G` control이 무너진다.
- 이는 모델이 단순히 predicate/class prior나 geometry alone만 보는 것이 아니라,
  `T_e`와 `G_e`의 matching을 보고 있다는 근거다.
- 다만 `horizontal_frame_swap`은 macro delta가 약하다. 이는 non-horizontal family에는
  frame-swap이 사실상 적용되지 않기 때문이므로, `relative_horizontal`은 family-specific
  frame-control caveat와 함께 다뤄야 한다.

## 5. Paper-Level Experiment Gate에서 확인한 내용

이번 gate의 목적은 “지금 결과를 paper-level experiment로 실행해도 되는 상태였는가?”와
“실행된 결과를 paper-facing evidence로 올릴 수 있는가?”를 분리해 판단하는 것이다.

| Gate | 결과 | 판단 |
| --- | --- | --- |
| Docker 재현 가능성 | pass | `h002-official-metric-runner`가 exit 0으로 실행됨 |
| Official validation policy | pass | validation은 eval-only, official test 미사용 |
| Feature boundary | pass | main `C_e`는 `T_e + G_e`만 사용 |
| Hidden/source leakage | pass | `Z_e`, `Q_e`, H001 `p_geom_valid`, hidden fields 제외 |
| Primary metric | pass | M4 macro-family AUROC가 모든 baseline보다 높음 |
| Counterfactual controls | pass | wrong-`T`, shuffled-`G`, swap, sign flip에서 성능 저하 |
| Family-wise reporting | pass | family별 metric이 분리되어 있음 |
| `relative_horizontal` | caveat | frame-control wording 필요 |
| `support_contact` | caveat | solved claim 금지, diagnostic only |
| Paper promotion | conditional pass | claim-boundary lock 이후 승격 여부 결정 |

결론:

```text
paper_level_experiment_execution_gate = passed_with_caveats
paper_result_promotion = not_yet
next_action = claim_boundary_lock
```

즉, paper-level experiment를 실행해도 되는 상태였고 실제로 실행도 완료했다.
하지만 결과를 최종 paper table로 올리려면 claim boundary를 먼저 잠가야 한다.

## 6. Family별 Claim Boundary

현재 결과 기준으로 가장 안전한 family별 위치는 다음이다.

| Family | Claim boundary |
| --- | --- |
| `relative_vertical` | main evidence 가능. Axis-order relation에서 predicate-conditioned geometry compatibility가 강하게 작동한다. |
| `size_relative` | main evidence 가능. Size-comparison relation에서 `T_e x G_e` compatibility가 명확하다. |
| `relative_horizontal` | supporting/main 후보 가능. 단, frame-control caveat를 명시해야 한다. |
| `support_contact` | diagnostic/challenging only. Contact/pose evidence가 아직 부족하며 solved claim 금지. |

## 7. 아직 막아야 하는 Claim

아래 claim은 현재 결과만으로는 쓰면 안 된다.

- 모든 3DSSG relation type에서 일반화된다.
- `support_contact`가 해결됐다.
- `relative_horizontal`이 frame-invariant하게 완전히 해결됐다.
- `p_rel` / `p_obs` reliability까지 검증됐다.
- VL-SAT/Open3DSG source reranking의 recall/violation tradeoff까지 개선했다.
- official test 결과다.

## 8. 다음 단계

다음 TODO는 다음이다.

```text
compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review
```

여기서 해야 할 일:

- paper-facing main table에 어떤 family를 넣을지 확정한다.
- `relative_vertical`, `size_relative`를 main evidence로 둘지 확정한다.
- `relative_horizontal`을 main/supporting 중 어디에 둘지 frame-control caveat와 함께 결정한다.
- `support_contact`를 diagnostic/failure taxonomy로 고정한다.
- paper wording에서 금지 claim과 허용 claim을 분리한다.
- paper-level result promotion 여부를 결정한다.

## 9. Claim Boundary Lock 결과

위 다음 단계는 실행 완료됐다.

```text
artifact_root = artifacts/compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review/
status = h002_compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review_locked
selected_path = official_claim_boundary_locked_select_paper_table_skeleton
validation_errors = 0
next_todo = compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock
```

Lock된 table role은 다음과 같다.

| Family | Paper role | 해석 |
| --- | --- | --- |
| `relative_vertical` | primary mechanism row | signed vertical-order compatibility의 main evidence |
| `size_relative` | primary mechanism row | signed size-comparison compatibility의 main evidence |
| `relative_horizontal` | caveated frame-aware row | frame-aware evidence는 가능하지만 frame-invariant claim 금지 |
| `support_contact` | diagnostic/failure-taxonomy row | challenging route로만 사용, solved claim 금지 |

결론적으로 bounded paper-table draft는 가능해졌다. 하지만 final paper result promotion은
아직 아니다. 다음 단계에서는 위 boundary를 지키는 paper table skeleton을 만들고,
primary row, caveated row, diagnostic row가 같은 표에서 어떻게 보이는지 검토해야 한다.

## 10. Paper Table Skeleton 결과

위 table skeleton 생성 단계도 실행 완료됐다.

```text
artifact_root = artifacts/compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock/
status = h002_compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock_ready
selected_path = paper_table_skeleton_ready_select_table_review
validation_errors = 0
next_todo = compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock
```

Skeleton의 핵심 표 구조는 다음과 같다.

| Block | Scope | Method | AUROC | AUPRC | Balanced Acc. |
| --- | --- | --- | ---: | ---: | ---: |
| primary mechanism macro | `relative_vertical + size_relative` | `T_e only` | 0.500000 | 0.499505 | 0.500000 |
| primary mechanism macro | `relative_vertical + size_relative` | `G_e only` | 0.500000 | 0.507762 | 0.500000 |
| primary mechanism macro | `relative_vertical + size_relative` | `T_e + G_e concat` | 0.498994 | 0.527248 | 0.509615 |
| primary mechanism macro | `relative_vertical + size_relative` | `C_e compatibility` | 0.995453 | 0.995505 | 0.972964 |
| caveated row | `relative_horizontal` | `C_e compatibility` | 0.719568 | 0.444788 | 0.701522 |
| diagnostic row | `support_contact` | `C_e compatibility` | 0.631712 | 0.643417 | 0.566394 |

해석:

- main paper mechanism evidence는 `relative_vertical + size_relative`로 제한한다.
- `relative_horizontal`은 frame-aware evidence로만 둔다.
- `support_contact`는 diagnostic/failure-taxonomy row로 둔다.
- official test, source reranking, calibrated `p_rel`/`p_obs`, all-relation 3DSSG
  improvement claim은 여전히 금지한다.

다음 단계는 이 skeleton 자체를 review하는 것이다. 즉, 이 표 구조가 paper claim으로
충분히 강한지, 아니면 hypothesis/report artifact로 남겨야 하는지 판단해야 한다.

## 11. Paper Table Skeleton Review 및 원리성 판단

위 review 단계도 실행 완료됐다.

```text
artifact_root = artifacts/compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock/
status = h002_compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock_reviewed
selected_path = table_review_keep_as_bounded_mechanism_evidence_select_gap_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_principled_design_gap_plan_after_table_review
```

원리성 판단:

- 현재 H002 구조는 원리적으로 자연스럽다.
- Relation reliability를 source confidence 하나로 보지 않고 `T_e`, `Z_e`, `G_e`,
  `C_e`, `Q_e`로 분리하는 것은 현재 문제에서 필요한 분해다.
- `T_e`와 `Z_e`를 분리하는 것은 source score shortcut을 막기 위해 필요하다.
- predicate-independent `G_e`는 semantic과 geometry가 실제로 맞는지 검증하기 위한
  전제다.
- `C_e = compatibility(T_e, G_e)`는 relation reliability를 설명하는 핵심 mechanism으로
  유지하는 것이 맞다.
- `Q_e`, `p_obs`, `p_rel`도 원리적으로 맞지만, 현재 official table에서는 아직 검증하지
  않았으므로 결과 claim으로 쓰면 안 된다.

Paper claim 판단:

- 현재 primary table signal은 강하다. `relative_vertical + size_relative`에서
  `C_e compatibility` AUROC는 `0.995453`이고, baseline은 약 `0.50`이다.
- 하지만 primary relation이 signed comparison route에 치우쳐 있어, reviewer가
  “직접 geometry sign rule을 맞춘 것 아닌가?”라고 볼 수 있다.
- 따라서 이 table은 bounded mechanism evidence로 유지하고, standalone final paper
  result로 승격하지 않는다.
- 다음 단계에서는 harder compatibility route 또는 source-deployable evidence 중 어떤
  gap을 먼저 줄일지 결정해야 한다.

## 12. Principled Design Gap Plan 결과

위 gap plan 단계도 실행 완료됐다.

```text
artifact_root = artifacts/compatibility_dataset_v3_principled_design_gap_plan_after_table_review/
status = h002_compatibility_dataset_v3_principled_design_gap_plan_after_table_review_ready
selected_path = select_harder_support_contact_route_protocol_before_source_deployable_promotion
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan
```

결론:

- H002의 factorization은 유지한다.
- 현재 table은 bounded mechanism evidence로만 사용한다.
- final paper result promotion은 아직 하지 않는다.
- 다음 gap은 `harder_support_contact_route`로 선택한다.
- source-deployable reranking은 중요하지만, hard-route `C_e`가 안정화된 뒤 진행한다.
- `p_obs`/`p_rel` branch는 독립 observability label이 안정화될 때까지 미룬다.

다음 protocol에서 고정해야 할 내용:

| 항목 | 결정 |
| --- | --- |
| main relation | `standing on`, `lying on` |
| diagnostic relation | `supported by` |
| `T_e` | predicate semantic content only |
| `G_e` | predicate-independent pose/contact/overlap/gap/point/mesh evidence |
| `Z_e` | main `C_e` input에서 제외 |
| `Q_e` | main `C_e` input에서 제외, p_obs 안정화 전까지 diagnostic |
| controls | semantic-only, geometry-only, concat, wrong-`T`, shuffled-`G`, subject/object swap, class-pair shortcut audit |
| blocked claims | solved support/contact, calibrated `p_rel`/`p_obs`, source reranking, official test, all-relation generalization |

이 선택의 이유는 현재 H002가 막힌 지점이 방법론 자체가 아니라 evidence difficulty이기
때문이다. `support_contact`는 signed comparison보다 어렵고, pose/contact evidence가
필요하므로 현재 top-tier novelty threat를 줄이는 다음 경로로 가장 적절하다.

## 13. Support/Contact Hard Route Protocol 및 Source Inventory 결과

Gap plan 이후 support/contact hard route protocol을 고정하고, 이어서 source inventory를
완료했다.

Protocol artifact:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan/
status = h002_compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol
```

Source inventory artifact:

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol/
status = h002_compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol_ready
selected_path = support_contact_harder_route_source_inventory_ready_select_materialization_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_harder_route_materialization_plan_after_source_inventory
```

고정된 hard-route 범위:

| 항목 | 결정 |
| --- | --- |
| main predicates | `standing on`, `lying on` |
| diagnostic predicate | `supported by` |
| main input | `T_e + G_e` |
| excluded from main `C_e` | `Z_e`, `Q_e`, hidden fields, H001 `p_geom_valid`, rule labels |
| official test | 사용하지 않음 |
| paper promotion | 아직 하지 않음 |

Source inventory 결과:

| Source | Rows | Main Rows | Scans | 상태 |
| --- | ---: | ---: | ---: | --- |
| official validation current materialization | 3178 | 3178 | 156 | OBB proxy `G_e`만 materialized |
| official validation source assets | 3178 | 3178 | 156 | semseg/PLY/mesh/segment/normal asset available |
| train point/multiview inventory | 800 | 640 | 357 | feature template reference |
| train point/multiview materialization | 800 | 640 | 357 | point/pose/contact numeric feature available |

해석:

- official validation에서 support/contact hard route를 더 진행할 재료는 충분하다.
- 다만 현재 official `G_e`는 아직 OBB proxy 중심이므로, paper-level hard-route metric을
  바로 주장하면 안 된다.
- 다음 단계는 vertical gap, XY support overlap, bottom proximity를 유지하면서
  support surface normal, subject pose/principal axis, contact patch, local point density,
  mesh gap/intersection 또는 missing-mask를 추가하는 materialization plan이다.
- `predicate_x_class_pair` majority accuracy가 `0.993707`로 높기 때문에, `support_contact`
  solved claim은 여전히 금지한다.
- 이 단계는 validation/test result가 아니라 source readiness gate다.

## 14. Support/Contact Hard Route Materialization Plan 결과

Source inventory 이후 materialization plan 단계도 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_harder_route_materialization_plan_after_source_inventory/
status = h002_support_contact_harder_route_materialization_plan_after_source_inventory_ready
selected_path = support_contact_harder_route_materialization_plan_ready_select_docker_materializer_implementation
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_harder_route_docker_materialization_after_plan
```

고정된 materialization scope:

| 항목 | 값 |
| --- | ---: |
| official validation support/contact rows | 3178 |
| same-pair predicate-flip groups | 1589 |
| paired groups passing integrity check | 1589 |
| mixed `predicate x class-pair` cells | 8 |
| mixed `predicate x class-pair` balanced rows | 40 |

이번 plan에서 중요한 결정은 primary view를 `model_safe_main_no_class`로 둔 것이다.

```text
allowed = T_e.predicate_text + T_e.route_family + G_e_hard_route_numeric
blocked = Z_e, Q_e, class labels, ids, GT/source/construction fields, H001 p_geom_valid
```

이유는 단순하다. 현재 support/contact에서 `predicate x class-pair` shortcut이 강하므로,
class label을 first main view에 넣으면 method가 predicate-geometry compatibility를
학습했는지 class prior를 복사했는지 분리하기 어렵다. 따라서 class semantics는 ablation
view로만 둔다.

다음 Docker materializer가 만들어야 할 것은 다음이다.

- `candidate_rows.jsonl`
- `model_safe_main_no_class.jsonl`
- `model_safe_main_with_class_ablation.jsonl`
- `model_safe_geometry_only.jsonl`
- `model_safe_qe_diagnostic.jsonl`
- `hidden_manifest.jsonl`
- `group_manifest.jsonl`
- `feature_availability.csv`
- `schema_precheck.json`
- `validation_errors.jsonl`

다음 단계는 Docker materializer 구현이다. 이 단계에서도 metric은 실행하지 않는다.
Metric은 materialization schema audit, shortcut audit, control readiness를 통과한 뒤에만
진행한다.

## 15. Support/Contact Hard Route Docker Materialization 결과

Docker 기반 materializer 구현과 실행을 완료했다.

```text
runtime_output = experiments/H002_compatibility_routing/support_contact_harder_materialization/latest/
artifact_root = artifacts/compatibility_dataset_v3_support_contact_harder_route_docker_materialization_after_plan/
status = h002_support_contact_harder_route_docker_materialization_after_plan_ready
selected_path = support_contact_harder_route_materialized_select_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_harder_route_schema_shortcut_audit_after_docker_materialization
```

실행 command:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-support-contact-hard-materialize
```

Runtime output:

| Output | Rows |
| --- | ---: |
| `candidate_rows.jsonl` | 3178 |
| `model_safe_main_no_class.jsonl` | 3178 |
| `model_safe_main_with_class_ablation.jsonl` | 3178 |
| `model_safe_geometry_only.jsonl` | 3178 |
| `model_safe_qe_diagnostic.jsonl` | 3178 |
| `hidden_manifest.jsonl` | 3178 |
| `group_manifest.jsonl` | 1589 |
| `validation_errors.jsonl` | 0 |

생성된 richer `G_e`는 `43`개 feature를 포함한다. 기존 OBB proxy보다 확장된 부분은
다음이다.

- subject/object pose와 flatness
- dominant normal upness
- support surface normal upness
- surface/normal alignment
- local contact point count와 density
- contact patch proxy

이 단계의 해석:

- support/contact hard route를 위한 더 강한 materialized evidence는 준비됐다.
- 하지만 이 단계는 metric이 아니다.
- official test는 사용하지 않았다.
- `support_contact` solved claim은 아직 금지다.
- 다음 단계는 schema leakage, shortcut risk, wrong-`T`, shuffled-`G`,
  within-class-pair shuffled-`G` control readiness를 보는 audit이다.

## 16. Support/Contact Hard Route Schema/Shortcut Audit 결과

Richer support/contact materialization 이후 Docker schema/shortcut audit를 실행했다.

```text
runtime_audit_root = experiments/H002_compatibility_routing/support_contact_harder_schema_audit/latest/
artifact_root = artifacts/compatibility_dataset_v3_support_contact_harder_route_schema_shortcut_audit_after_docker_materialization/
status = h002_support_contact_harder_route_schema_shortcut_audit_after_docker_materialization_ready_with_warnings
selected_path = support_contact_harder_route_schema_ready_select_metric_protocol_freeze
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit
```

실행 command:

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-support-contact-hard-schema-audit
```

Audit 결과:

| 항목 | 값 |
| --- | ---: |
| rows | 3178 |
| groups | 1589 |
| richer `G_e` features | 43 |
| labels | 1589 / 1589 |
| `standing on` / `lying on` | 1589 / 1589 |
| validation errors | 0 |
| blocked field hits | 0 |
| control readiness | 7 / 7 |

Shortcut 결과:

| Probe | Majority Acc. | Risk |
| --- | ---: | --- |
| predicate-only | 0.853996 | medium |
| class-pair only | 0.500000 | low |
| predicate x class-pair | 0.993707 | high |

이 결과는 paper-level experiment 실행 전 gate 관점에서 다음을 의미한다.

- schema separation은 통과했다.
- primary `C_e` view에는 `T_e + G_e`만 남아 있다.
- `Z_e`, `Q_e`, class labels, source score/rank, H001 `p_geom_valid`, hidden provenance는 primary view에서 제외됐다.
- wrong-`T`, shuffled-`G`, within-class-pair shuffled-`G` control은 생성 가능하다.
- 하지만 `predicate x class-pair` shortcut이 높으므로 support/contact를 solved family로 주장할 수 없다.

따라서 다음 단계는 metric 실행이 아니라 metric protocol freeze다. Protocol에는
semantic-only, geometry-only, concat, interaction, class-ablation, predicate-only,
`predicate x class-pair`, wrong-`T`, global shuffled-`G`, within-class-pair shuffled-`G`
비교군을 고정해야 한다. 이 protocol을 고정한 뒤에만 support/contact hard-route metric을
실행할 수 있다.

## 17. Support/Contact Hard Route Metric Protocol Freeze

Schema/shortcut audit 이후 metric protocol을 고정했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit/
status = h002_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit_ready
selected_path = support_contact_hard_metric_protocol_frozen_select_train_eval_alignment
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze
```

고정한 metric contract:

| 항목 | 값 |
| --- | --- |
| Target | `C_e` |
| Route | `support_contact` |
| Predicates | `standing on`, `lying on` |
| Primary metric | `support_contact_AUROC` |
| Primary model | `M4_TxG_compatibility` |
| Main baselines | `M1_predicate_only`, `M2_geometry_only`, `M3_T_plus_G_concat` |
| Diagnostics | class-ablation, `Q_e`, `predicate x class-pair` |

이 protocol에서 중요한 결정은 official validation을 계속 eval-only로 둔 것이다. 현재
official validation hard-route materialization은 `3178` rows와 `43` canonical `G_e`
features를 갖는다. 반면 train reference는 `640` main rows가 있지만 feature schema가
prefixed `63` features로 다르다.

따라서 paper-level experiment gate 관점에서 바로 metric runner로 가면 안 된다. Official
validation에서 학습하거나 threshold를 고르면 leakage가 된다. 다음 gate는 train-side
point/OBB/contact feature를 official 43-feature canonical schema로 맞출 수 있는지 확인하는
train/eval feature alignment audit다.

현재까지 support/contact hard route의 상태는 다음과 같다.

- materialization 가능: yes
- schema separation: pass
- shortcut warning: remains high
- metric protocol: frozen
- metric runner: not yet
- paper result: not promoted
- `support_contact solved`: blocked

## 18. Support/Contact Hard Route Train/Eval Alignment 결과

Metric protocol freeze 이후 train-side feature를 official validation의 43-feature canonical
`G_e` schema에 맞추는 alignment를 완료했다.

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze/
status = h002_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze_ready
selected_path = support_contact_train_eval_aligned_select_metric_runner_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_harder_route_metric_runner_after_train_eval_alignment
```

결과:

| 항목 | 값 |
| --- | ---: |
| official canonical features | 43 |
| mapped train features | 43 |
| direct/direct-transform mappings | 31 |
| derived/proxy mappings | 12 |
| aligned rows | 640 |
| internal train rows | 531 |
| internal dev rows | 109 |
| official validation scan overlap | 0 |
| official validation endpoint overlap | 0 |
| validation errors | 0 |

Split balance:

| Split | Rows | Label 0 | Label 1 | `standing on` | `lying on` |
| --- | ---: | ---: | ---: | ---: | ---: |
| `internal_train` | 531 | 270 | 261 | 263 | 268 |
| `internal_dev` | 109 | 50 | 59 | 57 | 52 |

이제 support/contact hard-route metric runner로 넘어갈 수 있다. 다만 `31/43` feature는
direct 또는 direct-transform이지만, `12/43` feature는 derived/proxy mapping이다.
따라서 다음 runner 결과를 해석할 때 “raw extractor가 완전히 동일하다”가 아니라
“runner용 canonical feature schema가 맞춰졌다”고 표현해야 한다.

현재 gate 결론:

- metric runner 준비: yes
- official validation leakage: no
- official test usage: no
- paper result promotion: no
- `support_contact solved` claim: still blocked

## 19. Support/Contact Hard Route Metric Runner 결과

Train/eval alignment 이후 support/contact hard-route Docker metric runner를 실행했다.

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-support-contact-hard-metric-runner
```

생성 위치:

```text
experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/
artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_runner_after_train_eval_alignment/
```

검증된 조건:

- aligned train/dev rows: `640`
- internal train/dev split: `531` / `109`
- official validation rows: `3178`, eval-only
- official test usage: `false`
- main `C_e`: `T_e + G_e`
- `Z_e`, `Q_e`, H001 `p_geom_valid`, class labels: primary `C_e`에서 제외
- runtime validation errors: `0`

결과:

| View | Internal dev AUROC | Official validation AUROC | 해석 |
| --- | ---: | ---: | --- |
| `M1_predicate_only` | 0.460339 | 0.146004 | predicate-only는 부족 |
| `M2_geometry_only` | 0.532712 | 0.500000 | official에서는 tie/neutral |
| `M3_T_plus_G_concat` | 0.518644 | 0.454660 | simple concat도 충분하지 않음 |
| `M4_TxG_compatibility` | 0.721356 | 0.077539 | internal dev signal은 있지만 official transfer 실패 |
| `C1_wrong_T_same_route` | - | 0.922461 | wrong predicate가 오히려 강함 |

중요한 점은 runner 자체가 실패한 것이 아니라, metric expectation이 실패했다는 것이다.
Internal dev에서는 `M4`가 baseline보다 강하지만, official validation에서는 `M4`가 random보다
낮고 wrong-`T`가 높다. 이는 support/contact hard-route를 paper-facing 성공 evidence로
승격할 수 없다는 명확한 신호다.

Feature drift audit도 같은 방향을 가리킨다.

| Feature | Train mean | Official mean | Official outside train range |
| --- | ---: | ---: | ---: |
| `support_contact_likelihood_proxy` | 0.027720 | 0.761419 | 0.694147 |
| `xy_overlap_min_ratio` | 0.100429 | 0.983581 | 0.950913 |
| `surface_gap_subject_bottom_to_object_top` | -0.261022 | -0.296430 | 0.069226 |

따라서 다음 result review는 “모델을 더 세게 돌리는 단계”가 아니라 원인을 분리하는 단계다.

검토해야 할 원인:

- train-side label target과 official GT predicate-flip target의 의미 불일치
- train-aligned `G_e`와 official canonical `G_e`의 feature distribution shift
- `standing on`/`lying on` predicate sign convention mismatch
- current `G_e`가 support/contact official validation으로 transfer되지 않는 문제

현재 gate 결론:

- metric runner completed: yes
- paper metric promoted: no
- support/contact solved claim: blocked
- source-deployable reranking: deferred
- `p_obs/p_rel`: deferred
- next: `compatibility_dataset_v3_support_contact_harder_route_metric_result_review_after_runner`

## 20. Support/Contact Hard Route Result Review

목적:

Internal dev에서는 `support_contact` hard route의 `M4_TxG_compatibility`가 약한 signal을
보였지만, official validation에서는 expectation이 무너졌다. 이 단계에서는 해당 실패가
H002 방향 전체의 실패인지, 아니면 support/contact route의 target/feature contract 문제인지
분리해서 검토했다.

결과:

Official validation에서 `M4`는 AUROC `0.077539`이고, wrong-`T` control은 AUROC
`0.922461`이다. Paired group 기준으로도 `M4` accuracy는 `0.182505`, wrong-`T` accuracy는
`0.817495`다. 즉 현재 support/contact hard route는 correct predicate보다 wrong predicate가
더 잘 맞는 inversion failure다.

Feature distribution도 크게 다르다. `support_contact_likelihood_proxy`는 official row의
`0.694147`이 train range 밖에 있고, `xy_overlap_min_ratio`는 `0.950913`이 train range 밖에
있다. 따라서 현재 실패는 단순히 모델이 약한 것이 아니라 train-side target/feature regime과
official validation GT-counterfactual regime이 맞지 않는 문제로 보는 것이 맞다.

결론은 다음과 같다.

- H002 방향 전체가 잘못된 것은 아니다.
- `support_contact` hard route는 현재 형태로 paper success claim에 넣으면 안 된다.
- score를 post-hoc flip해서 성공처럼 쓰면 안 된다.
- `support_contact`는 diagnostic/failure taxonomy로 고정한다.
- 다시 시도하려면 target/feature contract를 새로 설계해야 한다.

다음 step은 `compatibility_dataset_v3_support_contact_harder_route_path_decision_after_result_review`다.

## 21. Support/Contact Hard Route Path Decision

목적:

`support_contact` hard route result review 이후, 이 route를 계속 수리할지 아니면
diagnostic/failure taxonomy로 고정하고 H002의 paper-facing scope를 clean `C_e` route 중심으로
제한할지 결정했다.

결과:

선택한 경로는 `freeze_support_contact_harder_route_as_diagnostic_scope_h002_to_clean_routes`다.
Validation error는 `0`이다.

핵심 근거는 다음과 같다.

| Metric | Value |
| --- | ---: |
| official validation `M4_TxG_compatibility` AUROC | 0.077539 |
| official validation wrong-`T` AUROC | 0.922461 |
| paired `M4` accuracy | 0.182505 |
| paired wrong-`T` accuracy | 0.817495 |

따라서 현재 support/contact hard route는 성공 결과가 아니라 correct predicate보다 wrong predicate가
강한 inversion failure다. 이 결과를 post-hoc flip하거나 success claim으로 승격하지 않는다.

최종 처리:

- `relative_vertical`, `size_relative`는 main clean `C_e` evidence로 유지한다.
- `relative_horizontal`은 frame-aware evidence로 유지하되 frame-invariant spatial reasoning으로 과장하지 않는다.
- `support_contact`는 diagnostic/failure taxonomy로 freeze한다.
- source reranking, official test, calibrated `p_obs/p_rel`은 final H002 scope/method freeze 이후로 미룬다.

다음 step은 `compatibility_dataset_v3_final_h002_scope_lock_after_support_contact_freeze`다.

## 22. Final H002 Scope Lock

목적:

`support_contact` hard route를 diagnostic/failure taxonomy로 freeze한 뒤, H002의
paper-facing scope와 metric 역할을 최종 고정했다. 이 단계는 새 성능을 만드는 단계가 아니라,
현재까지의 official validation result와 path decision을 바탕으로 어떤 claim을 남기고 어떤
claim을 막을지 정리하는 gate다.

결과:

```text
status = h002_compatibility_dataset_v3_final_h002_scope_lock_after_support_contact_freeze_ready
selected_path = final_scope_locked_clean_Ce_routes_support_contact_diagnostic
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_protocol_plan_after_final_scope_lock
```

최종 route scope는 다음과 같다.

| Route family | Relation types | Final role |
| --- | --- | --- |
| `relative_vertical` | `higher than`, `lower than` | primary clean `C_e` mechanism |
| `size_relative` | `bigger than`, `smaller than` | primary clean `C_e` mechanism |
| `relative_horizontal` | `left`, `right`, `front`, `behind` | caveated frame-aware `C_e` mechanism |
| `proximity` | `close by` | geometry-only route control |
| `support_contact` | `standing on`, `lying on`, `supported by` | diagnostic failure taxonomy |
| `attachment_observability` | `attached to`, `hanging on`, `connected to` | future observability route |
| `containment_occlusion_identity_structural` | `inside`, `cover`, `leaning against`, `same as`, `same symmetry as`, `part of`, `belonging to` 등 | future route taxonomy |

Metric role도 같이 lock했다.

| Metric | 현재 역할 |
| --- | --- |
| family-wise AUROC / macro-family AUROC | current primary |
| wrong-`T`, shuffled-`G`, endpoint-swap, sign-flip controls | current primary |
| balanced accuracy / AUPRC | current secondary |
| `Recall@K` | downstream future |
| `Violation@K` | downstream future, not primary `C_e` metric |
| risk-coverage / abstain quality | future `p_obs` branch |

따라서 `Violation@K`는 버린 것이 아니다. 다만 현재 H002의 핵심은 `C_e =
compatibility(T_e, G_e)`가 relation-family별로 의미 있는 mechanism인지 검증하는 것이므로,
`Violation@K`는 현재 main metric이 아니다. `Violation@K`는 다음 source reranking protocol을
열고 top-K graph selection을 평가할 때 downstream metric으로 다시 사용한다.

허용되는 claim:

- H002는 `T_e`, `Z_e`, `G_e`, `C_e`, `Q_e`를 분리하는 factorized evidence contract다.
- `relative_vertical`, `size_relative`는 clean `C_e` mechanism evidence다.
- `relative_horizontal`은 frame-aware compatibility evidence로만 보고한다.
- relation family마다 필요한 evidence route가 다르다는 relation-aware routing claim은 유지한다.

차단되는 claim:

- `support_contact` solved claim
- all-relation generalization
- source reranking result claim
- `Violation@K`를 현재 `C_e` mechanism의 primary metric으로 쓰는 claim
- calibrated `p_obs` / `p_rel` reliability claim
- official test result claim

다음 step은 `compatibility_dataset_v3_source_reranking_protocol_plan_after_final_scope_lock`다.

## 23. Source Reranking Protocol Plan

목적:

Final H002 scope lock 이후 `Recall@K`와 `Violation@K`를 downstream source-reranking metric으로
다시 열기 위한 protocol을 고정했다. 이 단계에서는 source reranking metric을 실행하지 않았다.
공식 test도 사용하지 않았고, paper metric도 promote하지 않았다.

결과:

```text
status = h002_compatibility_dataset_v3_source_reranking_protocol_plan_after_final_scope_lock_ready
selected_path = source_reranking_protocol_ready_select_source_inventory
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_source_inventory_after_protocol_plan
```

핵심 결정은 다음과 같다.

- Source candidates는 official validation으로 제한한다.
- 사용할 source bridge는 `vlsat_full_validation`과 `open3dsg_recovery_relaxed_views_min2`다.
- `C_e = compatibility(T_e, G_e)` 내부에는 `Z_e`를 넣지 않는다.
- Source score는 reranking stage에서만 `C_e`와 결합한다.
- Primary bridge score 후보는 `normalized_source_score * normalized_C_e_score`다.
- `Recall@K`와 `Violation@K`는 K = `{5,10,20,50,100}`에서 downstream metric으로 평가한다.
- `support_contact`는 diagnostic only이며 success aggregation에서 제외한다.

Route별 현재 source-reranking 역할:

| Route family | Role | Inclusion |
| --- | --- | --- |
| `relative_vertical` | primary bridge candidate | include |
| `size_relative` | primary bridge candidate with feature caveat | include after H002 `G_e` materialization check |
| `relative_horizontal` | caveated frame-aware bridge | separate/caveated table |
| `proximity` | geometry-only control | optional if source candidates exist |
| `support_contact` | diagnostic only | exclude from success metric |

Score contract:

| Score | Role | Formula |
| --- | --- | --- |
| `S0_source_score` | baseline | source score or ranking score |
| `S1_Ce_only` | diagnostic | `C_e(T_e, G_e)` |
| `S2_source_x_Ce` | primary bridge candidate | normalized source score * normalized `C_e` score |
| `S3_source_plus_lambda_Ce` | ablation/future | `log(source_score) + lambda * normalized C_e` |
| `C1_shuffled_Ce` | control | source score with shuffled `C_e` or `G_e` |
| `C2_wrong_predicate_Ce` | control | source score with wrong-`T` `C_e` |

다음 단계는 metric run이 아니라 source-reranking-specific inventory다. 여기서 source prediction
join key, H002 `G_e` materialization 가능성, `C_e` score 계산 가능성, `Recall@K` /
`Violation@K` 계산 가능성을 family/source별로 다시 점검해야 한다.

## 24. Source Reranking Source Inventory

목적:

Source reranking protocol 이후 VL-SAT/Open3DSG source candidates가 실제 reranking
experiment에 필요한 조건을 갖췄는지 점검했다. 이 단계에서도 metric은 실행하지 않았다.

결과:

```text
status = h002_compatibility_dataset_v3_source_reranking_source_inventory_after_protocol_plan_ready
selected_path = source_inventory_ready_select_source_candidate_materialization_protocol
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_materialization_protocol_after_source_inventory
```

Source-level inventory:

| Source | In-scope rows | Join key | Source score/rank |
| --- | ---: | --- | --- |
| `vlsat_full_validation` | 441696 | available | available |
| `open3dsg_recovery_relaxed_views_min2` | 321192 | available | available |

Metric readiness:

| Metric / score | Status | 이유 |
| --- | --- | --- |
| `Recall@K` with `S0_source_score` | computable | source ranking score와 official validation GT match가 있음 |
| `Violation@K` with H001 geometry | partially computable | `relative_vertical`, `proximity`, diagnostic `support_contact`는 checkable; `size_relative`, `relative_horizontal`은 H001 geometry verification 없음 |
| `Recall@K` with `S2_source_x_Ce` | blocked | source-wide `C_e` score가 없음 |
| `Violation@K` with `S2_source_x_Ce` | blocked | source-wide `C_e`와 family별 violation label/materialization이 필요 |

핵심 blocker는 source-wide `C_e` materialization이다. 현재 H002 `C_e` score는 official
GT/counterfactual materialization row에 대해서만 존재한다. Source prediction universe 전체에
대해 직접 join되는 비율은 낮다.

| Source | Family | H2 `C_e` direct join rate |
| --- | --- | ---: |
| `vlsat_full_validation` | `relative_vertical` | 0.010596 |
| `vlsat_full_validation` | `size_relative` | 0.004619 |
| `vlsat_full_validation` | `relative_horizontal` | 0.106173 |
| `open3dsg_recovery_relaxed_views_min2` | `relative_vertical` | 0.008369 |
| `open3dsg_recovery_relaxed_views_min2` | `size_relative` | 0.003661 |
| `open3dsg_recovery_relaxed_views_min2` | `relative_horizontal` | 0.109916 |

따라서 지금 바로 source reranking metric을 실행하면 안 된다. `S0_source_score` baseline만
계산하는 것은 가능하지만, H002의 핵심 bridge인 `S2_source_x_Ce`와 비교할 수 없어 H002
claim에는 충분하지 않다.

다음 단계는 source-wide `C_e` materialization protocol이다. Source prediction universe keyed by
`scan_id / subject_id / object_id / predicate`에 대해 model-safe `T_e`/`G_e` blocks를 만들고,
hidden GT/violation labels는 metric computation에만 사용하도록 분리해야 한다.

## 25. Source Reranking Materialization Protocol

목적:

Source reranking source inventory 이후, full source prediction universe에 대해 `S2_source_x_Ce`를
계산하려면 source-wide `C_e` materialization이 필요하다는 점을 확인했다. 이 단계는 metric을
실행하는 것이 아니라, Docker materializer가 만들어야 할 model-safe view와 hidden metric
manifest의 schema를 고정하는 gate다.

결과:

```text
status = h002_compatibility_dataset_v3_source_reranking_materialization_protocol_after_source_inventory_ready
selected_path = source_reranking_materialization_protocol_ready_select_docker_implementation
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_docker_materialization_after_protocol
```

고정된 runtime target:

```text
runtime_output_dir = experiments/H002_compatibility_routing/source_reranking_materialization/latest
total_source_family_rows_to_materialize = 762888
primary_success_family_rows = 254296
```

필수 output:

| Output | 역할 |
| --- | --- |
| `source_candidates.jsonl` | full source prediction universe |
| `model_safe_ce_view.jsonl` | `C_e` scoring input; `T_e + G_e` only |
| `model_safe_geometry_only_view.jsonl` | `G_e` diagnostic/control view |
| `source_rank_view.jsonl` | `Z_e` source score/rank for reranking only |
| `hidden_metric_manifest.jsonl` | GT match and violation labels for metrics only |
| `row_manifest.json` | counts, provenance, policy flags |
| `validation_errors.jsonl` | runtime validation errors |

핵심 boundary:

- `C_e = compatibility(T_e, G_e)`에는 `Z_e`를 넣지 않는다.
- `source_rank_view`의 source score/rank는 reranking stage에서만 사용한다.
- GT match, violation status, H001 `p_geom_valid`는 hidden metric/control 영역에 둔다.
- 이 단계에서는 `Recall@K`, `Violation@K`, source reranking metric을 실행하지 않았다.
- Official test는 사용하지 않았고, paper metric promotion도 없다.

다음 step은 Docker materializer 구현/실행이다. 그 결과가 schema/leakage gate를 통과해야
source reranking metric freeze로 넘어갈 수 있다.

## 26. Source Reranking Docker Materialization

목적:

Source-wide materialization protocol에 따라 `VL-SAT`와 `Open3DSG` official validation source
prediction universe 전체를 H002 source-reranking용 view로 실제 생성했다. 이 단계는
`S2_source_x_Ce` 계산을 위한 입력 준비 단계이며, metric 실행 단계가 아니다.

결과:

```text
runtime_root = experiments/H002_compatibility_routing/source_reranking_materialization/latest/
status = h002_source_reranking_docker_materialization_after_protocol_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_materialization_schema_audit_after_docker_materialization
```

생성된 runtime output:

| Output | Rows | 역할 |
| --- | ---: | --- |
| `source_candidates.jsonl` | 762888 | source prediction identity rows |
| `model_safe_ce_view.jsonl` | 762888 | `C_e` input; `T_e + G_e` only |
| `model_safe_geometry_only_view.jsonl` | 762888 | `G_e` diagnostic/control input |
| `source_rank_view.jsonl` | 762888 | `Z_e` source score/rank, reranking only |
| `hidden_metric_manifest.jsonl` | 762888 | GT match and violation labels, metric only |
| `validation_errors.jsonl` | 0 | runtime errors |

Family/source counts:

| Group | Rows |
| --- | ---: |
| `relative_vertical` | 127148 |
| `size_relative` | 127148 |
| `relative_horizontal` | 254296 |
| `proximity` | 63574 |
| `support_contact` | 190722 |
| `vlsat_full_validation` | 441696 |
| `open3dsg_recovery_relaxed_views_min2` | 321192 |

검증 결과:

- `model_safe_ce_view`는 `T_e`와 `G_e` feature block만 가진다.
- `source_rank_view`는 `Z_e`를 별도 보관하며 `C_e` scoring input이 아니다.
- `hidden_metric_manifest`는 metric-only label/violation 정보를 보관한다.
- candidate-id alignment across model-safe, geometry-only, rank, and hidden views passed.
- source reranking metric, `Recall@K`, `Violation@K`는 실행하지 않았다.
- official test는 사용하지 않았다.

다음 단계는 source-reranking materialization schema audit이다. 이 audit에서 blocked field deep scan,
score/hidden separation, family-balanced success aggregation, and control generation readiness를
확인해야 metric protocol freeze로 넘어갈 수 있다.

## 27. Source Reranking Materialization Schema Audit

목적:

Source-wide Docker materialization 이후, metric protocol freeze로 넘어가기 전에
`model_safe_ce_view`, `source_rank_view`, `hidden_metric_manifest`가 제대로 분리됐는지
검증했다. 이 단계는 source reranking metric 실행이 아니라 schema/leakage/control-readiness
audit이다.

결과:

```text
runtime_root = experiments/H002_compatibility_routing/source_reranking_schema_audit/latest/
status = h002_source_reranking_materialization_schema_audit_after_docker_materialization_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_metric_protocol_freeze_after_schema_audit
```

Schema separation:

| Check | Result |
| --- | --- |
| candidate-id alignment | pass |
| `C_e` feature blocks are `T_e + G_e` only | pass |
| blocked `C_e` feature hits | 0 |
| `source_rank_view` owns `Z_e` | pass |
| `hidden_metric_manifest` is metric-only | pass |
| geometry-only view is `G_e` only | pass |

Success aggregation:

| Family | Rows | Role |
| --- | ---: | --- |
| `relative_vertical` | 127148 | primary success |
| `size_relative` | 127148 | primary success |
| `relative_horizontal` | 254296 | caveated separate table |
| `proximity` | 63574 | geometry-only control |
| `support_contact` | 190722 | diagnostic excluded |

Control readiness:

- `relative_vertical`, `size_relative`: wrong-`T` and shuffled-`G` controls ready.
- `relative_horizontal`: controls ready, but caveated separate-table route.
- `proximity`: wrong-`T` not applicable because it is a single-predicate geometry-only control.
- `support_contact`: controls ready but success aggregation excluded.

Metric boundary:

- `Recall@K` and `Violation@K` were not computed.
- Source reranking metric was not run.
- Official test was not used.
- Next stage is metric protocol freeze, not metric execution.

## 28. Source Reranking Metric Protocol Freeze

목적:

Source reranking schema audit이 통과된 뒤, `Recall@K`와 `Violation@K`를 실제로
계산하기 전에 score definition, family aggregation, normalization, and controls를
고정했다. 이 단계는 source reranking metric 실행이 아니라 metric runner를 실행해도 되는지
확인하는 protocol freeze다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_source_reranking_metric_protocol_freeze_after_schema_audit/
status = h002_source_reranking_metric_protocol_freeze_after_schema_audit_ready
selected_path = source_reranking_metric_protocol_frozen_select_metric_runner
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_metric_runner_after_protocol_freeze
```

Frozen score contract:

| Score | Role | 사용 방식 |
| --- | --- | --- |
| `S0_source_score` | source baseline | source score/rank only |
| `S1_Ce_only` | diagnostic | `C_e_score(T_e, G_e)` only |
| `S2_source_x_Ce` | primary bridge | normalized source score와 normalized `C_e` 결합 |
| `S3_log_source_plus_Ce` | fixed ablation | lambda fixed to `1.0`, tuning 금지 |
| `C1_source_x_shuffled_Ce` | negative control | shuffled `C_e` 결합 |
| `C2_source_x_wrong_T_Ce` | negative control | wrong-`T` `C_e` 결합 |

Metric contract:

| 항목 | 결정 |
| --- | --- |
| Metrics | `Recall@K`, `Violation@K`, `Selected@K` |
| K grid | `{5, 10, 20, 50, 100}` |
| Ranking scope | `source_id + subgraph_id + route_family` |
| Primary families | `relative_vertical`, `size_relative` |
| Caveated family | `relative_horizontal` |
| Control family | `proximity` |
| Diagnostic excluded family | `support_contact` |

Boundary:

- Metric runner는 아직 실행하지 않았다.
- Official test는 사용하지 않았다.
- `C_e = compatibility(T_e, G_e)` 내부에는 `Z_e`를 넣지 않는다.
- Source score/rank는 `S2` reranking stage에서만 결합한다.
- Validation metric을 본 뒤 lambda를 조정하지 않는다.
- `p_obs` / `p_rel` claim은 아직 열지 않는다.

다음 step은 Docker source reranking metric runner를 구현/실행해서 frozen protocol에 따라
`S0`, `S1`, `S2`, controls의 `Recall@K`와 `Violation@K`를 family-wise로 계산하는 것이다.

## 29. Source Reranking Metric Runner

목적:

Frozen source-reranking protocol을 실제 Docker runner로 실행했다. 이 단계는
`C_e = compatibility(T_e, G_e)` scorer를 internal train에서만 fit한 뒤, source-wide official
validation 후보에 적용하고, `S2_source_x_Ce`가 source baseline `S0_source_score` 대비
top-K recall/violation tradeoff를 개선하는지 확인하는 validation-level metric이다.

결과:

```text
runtime_root = experiments/H002_compatibility_routing/source_reranking_evaluation/latest/
artifact_root = artifacts/compatibility_dataset_v3_source_reranking_metric_runner_after_protocol_freeze/
status = h002_source_reranking_metric_runner_after_protocol_freeze_ready
selected_path = source_reranking_metric_runner_ready_select_result_review
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_metric_result_review_after_runner
```

Runner boundary:

| 항목 | 값 |
| --- | --- |
| source rows scored | `762888` |
| `C_e` train rows | `4868` internal train rows |
| official validation use | eval-only |
| official test usage | false |
| `C_e` input | `T_e + G_e` only |
| `Z_e` usage | reranking stage only |
| post-hoc lambda tuning | false |
| support/contact | diagnostic/excluded |

Primary weighted result:

| K | `S2` Recall@K | `S0` Recall@K | Delta | `S2` Violation@K | `S0` Violation@K | Delta |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 0.352608 | 0.344671 | +0.007937 | 0.054491 | 0.295181 | -0.240690 |
| 10 | 0.513605 | 0.471655 | +0.041950 | 0.072342 | 0.302201 | -0.229859 |
| 20 | 0.724490 | 0.642857 | +0.081633 | 0.100487 | 0.343578 | -0.243091 |
| 50 | 0.952381 | 0.849206 | +0.103175 | 0.165998 | 0.425197 | -0.259199 |
| 100 | 1.000000 | 0.995465 | +0.004535 | 0.341919 | 0.484792 | -0.142873 |

Control 결과:

- `S2_source_x_Ce`는 모든 K에서 `S0_source_score` 대비 Recall@K를 유지 또는 개선했다.
- `S2_source_x_Ce`는 모든 K에서 `S0_source_score` 대비 Violation@K를 낮췄다.
- shuffled-`C_e`와 wrong-`T` control은 primary Recall@K에서 `S2`보다 낮았다.
- wrong-`T` control은 Violation@K가 크게 높아졌다.

해석:

이 결과는 `C_e`를 source score와 결합하는 downstream reranking 방향이 단순 source score보다
더 좋은 recall/violation tradeoff를 만들 수 있다는 validation evidence다. 특히 `C_e`만
사용하는 `S1`은 low-K recall이 낮으므로, H002의 source-deployable score는 `C_e` 단독이
아니라 `Z_e`와 `C_e`를 분리한 뒤 reranking에서 결합하는 구조가 맞다는 해석을 지지한다.

Boundary:

- Final paper result promotion은 아직 아니다.
- Official test result가 아니다.
- `p_obs` / `p_rel` 검증이 아니다.
- `support_contact` success claim은 여전히 금지다.
- 다음 단계는 result review로, source별/family별 비대칭과 control 결과를 paper-facing
  claim으로 올릴 수 있는지 판단해야 한다.

## 30. Source Reranking Metric Result Review

목적:

Source-reranking metric runner 결과를 paper-facing claim으로 승격해도 되는지 review했다.
검토 기준은 frozen protocol의 다음 항목이었다.

- `S2_source_x_Ce` vs `S0_source_score` recall/violation tradeoff
- shuffled-`C_e` and wrong-`T` controls
- source별/family별/K별 비대칭
- `C_e` 단독 score의 한계
- official validation/test boundary
- claim promotion 가능 범위

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_source_reranking_metric_result_review_after_runner/
status = h002_source_reranking_metric_result_review_after_runner_ready
selected_path = source_reranking_validation_evidence_ready_select_claim_boundary_lock
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_claim_boundary_lock_after_result_review
```

Review decision:

| 항목 | 판단 |
| --- | --- |
| source-reranking validation evidence | positive |
| paper promotion | not yet |
| official test usage | false |
| claim-boundary lock | required next |
| reviewed source-family-K cells | 20 |
| negative Recall@K cells | 3 |
| Violation@K non-improvement cells | 0 |

Allowed claim candidate:

```text
On official validation source candidates, combining source confidence with
predicate-geometry compatibility improves the primary recall-violation tradeoff
over source-only ranking for the clean comparison families.
```

Blocked claims:

- `S2` improves every source/family/K cell.
- `C_e` alone is a deployable source-ranking score.
- This is an official test result.
- This is final paper promotion.
- `support_contact` is solved.
- `p_obs` / `p_rel` posterior is validated.

구체적 caveat:

20개 source-family-K cell 중 3개에서 Recall@K가 소폭 낮아졌다.

| Source | Family | K | Delta Recall@K | Delta Violation@K |
| --- | --- | ---: | ---: | ---: |
| `open3dsg_recovery_relaxed_views_min2` | `size_relative` | 5 | -0.010204 | -0.265888 |
| `vlsat_full_validation` | `relative_vertical` | 5 | -0.017949 | -0.047810 |
| `vlsat_full_validation` | `size_relative` | 50 | -0.011765 | -0.216954 |

해석:

- Weighted primary result는 강하게 positive다.
- 모든 reviewed cell에서 Violation@K는 개선됐다.
- 일부 source/family/K에서는 recall이 소폭 낮아지므로, "uniform improvement" claim은
  금지해야 한다.
- `S1_Ce_only`는 low-K recall이 낮으므로, H002의 deployable source score는 `C_e` 단독이
  아니라 `Z_e`와 `C_e`를 분리한 뒤 reranking에서 결합하는 `S2`로 해석해야 한다.

다음 단계:

`compatibility_dataset_v3_source_reranking_claim_boundary_lock_after_result_review`에서
위 allowed/blocked wording을 고정하고, source-reranking result를 paper table 후보로 둘지
appendix/validation evidence로 둘지 결정한다.

## 31. Source Reranking Claim Boundary Lock

목적:

Source-reranking metric result review 이후 paper-facing claim boundary를 고정했다.
이 단계는 source-reranking metric을 다시 계산하는 단계가 아니라, 이미 생성된 official
validation source-candidate 결과를 어떤 논문 evidence로 사용할 수 있는지 잠그는 gate다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_source_reranking_claim_boundary_lock_after_result_review/
status = h002_source_reranking_claim_boundary_lock_after_result_review_locked
selected_path = source_reranking_claim_boundary_locked_select_validation_table_skeleton
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_validation_table_skeleton_after_claim_boundary_lock
```

Locked role:

| 항목 | 결정 |
| --- | --- |
| result type | validation-level source-reranking deployability evidence |
| table role | secondary validation table candidate or appendix table |
| main text usage | allowed only with validation-only qualifier |
| final paper/test table | not allowed yet |
| primary score | `S2_source_x_Ce` |
| baseline | `S0_source_score` |
| primary families | `relative_vertical`, `size_relative` |

Allowed wording:

```text
On official validation source candidates, combining source confidence with
predicate-geometry compatibility improves the primary recall-violation tradeoff
over source-only ranking for clean comparison families.
```

Required caveats:

- Official validation only이며 official test는 사용하지 않았다.
- Clean comparison families인 `relative_vertical`, `size_relative`에 한정한다.
- 20개 source-family-K cell 중 3개에서 Recall@K가 소폭 낮아졌으므로 uniform improvement
  claim은 금지한다.
- 모든 reviewed cell에서 Violation@K는 개선됐다.
- `C_e` alone은 low-K source ranking용 deployable score가 아니다.
- `support_contact`, `p_obs`, `p_rel`은 이 결과로 검증되지 않았다.

Blocked wording:

- official test or final paper result.
- every source/family/K cell improves.
- `C_e` alone is a deployable source-ranking score.
- `support_contact` is solved.
- `p_obs` / `p_rel` posterior is validated.
- SOTA or full 3DSSG improvement.
- post-hoc tuned reranking.

해석:

이번 결과는 H002의 factor separation이 source-reranking 단계에서도 의미가 있음을 보이는
validation evidence다. 다만 source-level deployability를 보여주는 보조 evidence로 보는 것이
맞고, H002의 main mechanism evidence인 `C_e = compatibility(T_e, G_e)` official validation
table을 대체하지 않는다. 다음 단계에서는 이 boundary를 지키는 validation table skeleton을
작성해야 한다.

## 32. Source Reranking Validation Table Skeleton

목적:

Source-reranking claim boundary lock 이후, 그 boundary를 지키는 validation table skeleton을
작성했다. 이 단계는 새 metric을 계산한 것이 아니라, 이미 frozen protocol로 계산한
`S2_source_x_Ce` source-reranking 결과를 논문/appendix 표로 보여줄 때 필요한 row 구조,
control row, caveat row를 고정한 것이다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_source_reranking_validation_table_skeleton_after_claim_boundary_lock/
status = h002_source_reranking_validation_table_skeleton_after_claim_boundary_lock_ready
selected_path = source_reranking_validation_table_skeleton_ready_select_table_review
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_validation_table_review_after_skeleton
```

생성된 표 skeleton:

| 파일 | 역할 |
| --- | --- |
| `primary_tradeoff_table.csv` | `S2_source_x_Ce` vs `S0_source_score` primary weighted Recall@K / Violation@K |
| `control_table.csv` | `C_e` only, shuffled-`C_e`, wrong-`T` control |
| `source_family_caveat_table.csv` | 반드시 보고해야 하는 3개 Recall@K regression cell |
| `source_family_full_table.csv` | 20개 source-family-K cell 전체 |
| `table_position_lock.csv` | main text / appendix / blocked position decision |

Primary tradeoff skeleton:

| K | S2 Recall@K | S0 Recall@K | Delta Recall@K | S2 Violation@K | S0 Violation@K | Delta Violation@K |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 0.352608 | 0.344671 | +0.007937 | 0.054491 | 0.295181 | -0.240690 |
| 10 | 0.513605 | 0.471655 | +0.041950 | 0.072342 | 0.302201 | -0.229859 |
| 20 | 0.724490 | 0.642857 | +0.081633 | 0.100487 | 0.343578 | -0.243091 |
| 50 | 0.952381 | 0.849206 | +0.103175 | 0.165998 | 0.425197 | -0.259199 |
| 100 | 1.000000 | 0.995465 | +0.004535 | 0.341919 | 0.484792 | -0.142873 |

Required caveat rows:

| Source | Family | K | Delta Recall@K | Delta Violation@K |
| --- | --- | ---: | ---: | ---: |
| `open3dsg_recovery_relaxed_views_min2` | `size_relative` | 5 | -0.010204 | -0.265888 |
| `vlsat_full_validation` | `relative_vertical` | 5 | -0.017949 | -0.047810 |
| `vlsat_full_validation` | `size_relative` | 50 | -0.011765 | -0.216954 |

해석:

- `S2_source_x_Ce`는 primary weighted 기준에서 모든 K의 Recall@K를 유지/개선하고
  Violation@K를 낮춘다.
- 그러나 20개 source-family-K cell 중 3개에서 Recall@K가 소폭 낮아졌으므로 uniform
  improvement claim은 금지한다.
- `C_e` only는 low-K deployable ranking score가 아니라, 왜 `Z_e`와 `C_e`를 분리한 뒤
  reranking stage에서 결합해야 하는지 보여주는 negative ablation으로 둔다.
- 이 표는 H002 main mechanism table을 대체하지 않고, source-level deployability를 보조하는
  validation table 후보 또는 appendix table 후보다.

## 33. Source Reranking Validation Table Review

목적:

Validation table skeleton을 paper benchmark table로 사용할 수 있는지 review했다. 사용자 결정에
따라 최종 benchmark table은 validation이 아니라 test set으로 만들기로 하고, 현재 validation
table은 appendix 또는 secondary validation analysis로 낮췄다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_source_reranking_validation_table_review_after_skeleton/
status = h002_source_reranking_validation_table_review_after_skeleton_ready
selected_path = downgrade_validation_table_select_test_benchmark_preflight
validation_errors = 0
next_todo = compatibility_dataset_v3_test_benchmark_preflight_after_validation_downgrade
```

Locked decision:

| 항목 | 결정 |
| --- | --- |
| validation table position | appendix or secondary analysis only |
| main benchmark table | test set required |
| validation table as benchmark | blocked |
| official test ready now | false |
| final paper result promotion | not yet |

Local test probe:

- canonical `local_dataset/3DSSG_subset/relationships_test.json`은 존재하지 않는다.
- Open3DSG staged runtime 아래 `relationships_test.json` 후보는 존재하지만, non-empty 후보들은
  canonical validation scans와 전부 overlap한다.
- 따라서 현재 관찰된 staged `relationships_test.json`은 provenance와 split-disjointness 확인
  전에는 independent test benchmark로 사용할 수 없다.

Experiment 전에 추가 검증해야 할 gate:

1. `test_label_provenance`: 독립 official test label 또는 official evaluation server 확인.
2. `split_disjointness`: train/validation/test scan, object-pair, candidate-id overlap audit.
3. `source_prediction_availability`: VL-SAT/Open3DSG test source prediction availability 확인.
4. `frozen_Ce_model_and_features`: `C_e` model, feature schema, family scope, score IDs, K grid freeze.
5. `normalization_freeze`: source score / `C_e` normalization을 test label이나 post-hoc test statistic으로 조정하지 않도록 고정.
6. `test_materialization_schema_audit`: model-safe/source-rank/hidden metric views 분리와 blocked-field audit.
7. `metric_and_claim_freeze`: Recall@K, Violation@K, controls, family aggregation, CI, wording freeze.
8. `single_final_test_run_policy`: test 실행 후 method/threshold/lambda/feature/family/wording 변경 금지.

해석:

현재 validation table은 H002 방향이 source-reranking에서도 가능성이 있다는 보조 evidence로는
쓸 수 있다. 하지만 benchmark table은 아니다. Test benchmark를 만들려면 먼저 test label
provenance와 split independence를 확인하고, 이후 protocol freeze와 Docker materialization /
schema audit / metric freeze를 거친 뒤 single final test run으로 진행해야 한다.

## 34. Test Benchmark Preflight

목적:

Validation table을 appendix/secondary analysis로 낮춘 뒤, H002 main benchmark table을 test set으로
만들 수 있는지 preflight했다. 이 단계는 test metric을 실행하는 단계가 아니라, 독립 test label,
split disjointness, test source prediction, frozen protocol 준비 여부를 판정하는 hypothesis gate다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_test_benchmark_preflight_after_validation_downgrade/
status = h002_test_benchmark_preflight_after_validation_downgrade_ready_blocked
selected_path = test_benchmark_blocked_select_independent_test_provenance_or_eval_server
validation_errors = 0
next_todo = compatibility_dataset_v3_test_benchmark_source_resolution_after_preflight
```

Decision:

| 항목 | 판단 |
| --- | --- |
| test benchmark ready | false |
| experiments test run allowed | false |
| validation table position | appendix or secondary analysis only |
| canonical test file | missing |
| non-empty staged test candidates | 2 |
| validation-alias candidates | 2 |
| official-test source rows | 0 |
| official-validation source rows | 762888 |

Test label provenance:

- canonical `local_dataset/3DSSG_subset/relationships_test.json`은 존재하지 않는다.
- staged `relationships_test.json` 후보 중 non-empty 후보는 canonical validation scans와 overlap한다.
- 따라서 현재 staged test file을 독립 test benchmark로 사용하면 validation alias risk가 있다.

Source prediction availability:

- 현재 source-reranking materialization은 `official_validation` split만 가진다.
- `vlsat_full_validation`과 `open3dsg_recovery_relaxed_views_min2` source rows는 모두 validation rows다.
- `official_test` source rows는 `0`이다.

Gate status:

| Gate | Status | Reason |
| --- | --- | --- |
| `test_label_provenance` | fail | canonical test missing; staged non-empty test candidates overlap validation scans |
| `split_disjointness` | fail | validation-alias candidates observed |
| `test_source_prediction_availability` | fail | official-test source rows are 0 |
| `frozen_Ce_model_and_features` | partial | validation model/schema exists, but no test-specific frozen artifact contract |
| `normalization_freeze` | partial | validation normalization exists, but test policy must be frozen |
| `test_materialization_schema_audit` | pending_blocked | no official-test materialization exists |
| `metric_and_claim_freeze` | partial | validation wording exists, but test benchmark wording/CI policy not frozen |
| `single_final_test_run_policy` | pending | must be documented before any test run |

해석:

현재 H002는 test benchmark experiment를 열면 안 된다. test set을 benchmark table로 사용하려면
먼저 독립 test source를 확보해야 한다. 다음 단계는 metric runner가 아니라
`test_benchmark_source_resolution`이다. 여기서 official evaluation server, 독립 test label,
또는 validation-only appendix 유지 중 하나를 선택해야 한다.

## 35. Test Benchmark Source Resolution

목적:

Test benchmark preflight가 blocked였기 때문에, official evaluation server나 독립
3DSSG relation-test label/source prediction route가 실제로 확인되는지 검토했다.
사용자 판단처럼 공식 evaluation server를 먼저 찾는 순서가 맞지만, scan-level test
split과 relation-label benchmark availability를 분리해서 보았다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_test_benchmark_source_resolution_after_preflight/
status = h002_test_benchmark_source_resolution_after_preflight_ready_blocked
selected_path = official_eval_server_not_confirmed_keep_validation_appendix_request_external_provenance
validation_errors = 0
next_todo = compatibility_dataset_v3_test_benchmark_external_provenance_request_after_source_resolution
```

Decision:

| 항목 | 판단 |
| --- | --- |
| accepted official evaluation server | not confirmed |
| independent relation test label | not confirmed |
| 3RScan scan-level test split | exists |
| scan-level split sufficient for H002 | false |
| local staged test candidates usable | false |
| relation-test source predictions | unavailable |
| experiments test run allowed | false |
| validation table position | appendix / secondary analysis only |

근거:

- 3RScan official repository는 train/validation/test split link를 제공한다. 그러나 이는
  scan-level split이다.
- 3DSSG official project page와 official GitHub pages repo를 확인한 범위에서는 accepted
  public relation evaluation server가 확인되지 않았다.
- Open3DSG official README는 3DSSG가 training/validation용 GT scene graph를 제공한다고
  설명한다.
- Local Open3DSG code의 `test_scans_3rscan` option은 존재하지만, help text가 3RScan
  test scans are not labeled in 3DSSG라고 되어 있어 H002 relation-GT benchmark로 바로
  사용할 수 없다.
- Local H002 preflight는 canonical `relationships_test.json` missing, validation-alias
  staged candidates `2`, official-test source rows `0`을 확인했다.

해석:

H002의 benchmark table은 지금 실행하면 안 된다. “3RScan test split이 있다”는 사실은
맞지만, H002가 필요한 것은 relation-label GT와 exact test source predictions다. 현재
이 둘이 확인되지 않았으므로 source-reranking 결과는 validation-level appendix/secondary
evidence로 유지한다.

다음 단계:

- official evaluation server route 또는 independent `relationships_test.json` provenance를
  요청/확인한다.
- split-disjointness proof와 exact test split에 대한 VL-SAT/Open3DSG source prediction
  availability가 확인되기 전까지 test metric runner를 실행하지 않는다.

## 36. External Provenance Request

목적:

Source-resolution gate에서 accepted official evaluation server와 independent relation-test
label provenance가 확인되지 않았기 때문에, 3DSSG/3RScan relation test benchmark 가능성을
공식적으로 확인하기 위한 request packet을 만들었다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_test_benchmark_external_provenance_request_after_source_resolution/
status = h002_test_benchmark_external_provenance_request_after_source_resolution_ready
selected_path = external_request_packet_ready_keep_test_benchmark_blocked
validation_errors = 0
next_todo = compatibility_dataset_v3_test_benchmark_external_response_ingestion_after_request
```

Generated files:

| File | 내용 |
| --- | --- |
| `request_packet.md` | maintainer/contact request draft |
| `request_questions.csv` | 공식 답변이 필요한 질문과 unblocking target |
| `source_evidence.csv` | 3RScan/3DSSG/Open3DSG/VL-SAT 근거 |
| `readiness_matrix.csv` | checkpoint/source prediction과 relation-GT readiness 분리 |
| `next_contract.json` | 응답 수집 후 다음 gate |

핵심 판단:

- VL-SAT checkpoint route는 존재한다.
- Open3DSG test execution route도 존재한다.
- 하지만 checkpoint는 prediction을 만들 수 있을 뿐, relation label GT를 만들지 못한다.
- Prediction-only 3RScan test export는 `Recall@K` benchmark가 아니다.
- H002 test benchmark를 열려면 official hidden evaluator 또는 independent
  `relationships_test.json` provenance가 필요하다.

따라서:

- test benchmark metric runner는 여전히 실행 금지다.
- validation source-reranking table은 appendix/secondary analysis로 유지한다.
- 외부 응답 또는 공식 문서 증빙이 들어오면 `external_response_ingestion`에서 positive /
  negative / validation-standard answer로 분기한다.

## 37. External Response Ingestion

목적:

External provenance request 이후 실제 official response, official documentation, 또는
relation-test provenance artifact가 들어왔는지 확인했다. 응답이 없으면 test benchmark를
열지 않고, validation-only paper positioning을 고정하는 단계로 넘어가야 한다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_test_benchmark_external_response_ingestion_after_request/
status = h002_test_benchmark_external_response_ingestion_after_request_ready_blocked_no_external_response
selected_path = no_external_response_keep_test_benchmark_blocked_select_validation_position_lock
validation_errors = 0
external_response_found = false
candidate_response_files = 0
next_todo = compatibility_dataset_v3_validation_only_position_lock_after_no_external_response
```

Generated files:

| File | 내용 |
| --- | --- |
| `response_inventory.csv` | response inbox 존재 여부와 candidate response file inventory |
| `ingestion_decision_matrix.csv` | official server / test GT / validation-standard 확인 상태 |
| `blocked_claims.csv` | 아직 막혀 있는 benchmark claim 목록 |
| `response_requirements.csv` | positive external provenance로 인정할 조건 |
| `next_contract.json` | 다음 validation-only position lock contract |

핵심 판단:

- Official evaluation server: not confirmed.
- Independent relation-test label: not confirmed.
- Official validation-as-standard protocol: not confirmed.
- Checkpoint reproduction is not sufficient for test `Recall@K`.
- Prediction-only 3RScan test export is not sufficient for benchmark reporting.
- Test benchmark execution remains blocked.
- Validation source-reranking table remains appendix/secondary analysis only.

해석:

이 단계는 “응답이 없어서 실패”가 아니라, benchmark provenance가 아직 없다는 사실을
paper-level gate로 고정한 것이다. 따라서 현재 H002는 official test result를 만들지 않고,
validation 결과의 paper position과 wording을 보수적으로 잠그는 다음 단계로 진행한다.

## 38. Validation-Only Position Lock

목적:

External response가 없기 때문에 현재 H002 source-reranking 결과를 official test benchmark로
승격하지 않고, official 3DSSG validation split 기반 custom evaluation으로 위치를 잠갔다.
동시에 allowed claim, blocked claim, Open3DSG vocabulary boundary, reopen condition을
고정했다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_validation_only_position_lock_after_no_external_response/
status = h002_validation_only_position_lock_after_no_external_response_ready
selected_path = validation_only_appendix_secondary_lock_keep_test_benchmark_blocked
validation_errors = 0
paper_position = appendix_or_secondary_analysis
official_test_benchmark = false
next_todo = compatibility_dataset_v3_h002_post_validation_position_path_decision
```

Generated files:

| File | 내용 |
| --- | --- |
| `paper_position_lock.csv` | validation-only paper position |
| `allowed_claims.csv` | 허용 가능한 validation-level claim |
| `blocked_claims.csv` | 금지할 official-test / SOTA / open-set claim |
| `reopen_conditions.csv` | test path를 다시 여는 조건 |
| `source_vocab_boundary.csv` | VL-SAT / Open3DSG source와 evaluation-GT boundary |
| `metric_position.csv` | `Recall@K`, `Violation@K`, `C_e` metric의 논문 내 역할 |
| `wording_guidance.md` | allowed / blocked wording guidance |

현재 허용되는 주장:

- H002 reranking을 VL-SAT / Open3DSG validation predictions에 적용했다.
- Official 3DSSG validation split의 GT relation 기준으로 custom protocol의
  `Recall@K`, `Violation@K` 변화를 보고한다.
- Open3DSG는 open-vocabulary relation source로 쓰되, 정량 평가는 closed-vocabulary
  3DSSG label mapping 기준이다.

막힌 주장:

- official 3DSSG test result.
- SOTA / leaderboard claim.
- unconstrained open-set relation-GT evaluation.
- validation table as final benchmark table.
- prediction-only 3RScan test scan export를 `Recall@K` benchmark로 쓰는 주장.

해석:

현재 H002 결과는 무효가 아니다. 다만 paper main benchmark가 아니라 validation-level
secondary evidence다. Test result를 주장하려면 official `relationships_test.json`,
hidden evaluation server, validation-as-standard official statement, 또는 별도
human-audited benchmark protocol 중 하나가 필요하다.

## 39. Post-Validation Position Path Decision

목적:

사용자 판단을 반영해 H002의 main claim을 official 3DSSG validation split에서 진행하는
방향으로 재정의했다. 이유는 VL-SAT와 Open3DSG 비교가 같은 validation GT 기준에서
가능하고, 기존 공개 relation evaluation 흐름도 validation split을 중심으로 구성되어 있기
때문이다. 따라서 이전 appendix/secondary-only position은 superseded된다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_h002_post_validation_position_path_decision/
status = h002_post_validation_position_path_decision_ready
selected_path = promote_official_validation_as_main_comparative_claim_keep_test_blocked
validation_errors = 0
main_claim_split = official_3DSSG_validation_split
main_table_allowed = true_validation_benchmark
official_test_benchmark = false
next_todo = compatibility_dataset_v3_main_validation_claim_table_lock_after_path_decision
```

Updated paper position:

- H002 main empirical claim은 official 3DSSG validation split에서 진행한다.
- Main table은 validation benchmark table로 둘 수 있다.
- VL-SAT와 Open3DSG validation predictions를 같은 GT 기준으로 비교한다.
- `Recall@K`는 closed-label 3DSSG validation recall이다.
- `Violation@K`는 H002 custom geometry-consistency / reliability metric이다.
- Open3DSG는 open-vocabulary source지만, 정량 평가는 closed-vocabulary 3DSSG mapping
  기준이다.

계속 막힌 주장:

- official 3DSSG test result.
- leaderboard/SOTA claim.
- unconstrained open-set relation-GT evaluation.
- prediction-only 3RScan test scan export as `Recall@K`.

다음 단계:

`main_validation_claim_table_lock`에서 table caption, baseline comparison wording,
Open3DSG source/evaluation caveat, negative source-family-K cells, family caveats를 고정한다.

## 40. Main Validation Claim Table Lock

목적:

Post-validation path decision 이후 H002 main validation benchmark table의 caption, baseline
wording, blocked wording, required caveat, H003 embedding extension position을 고정했다.
이 단계는 새 metric run이 아니라 paper wording/claim boundary lock이다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_main_validation_claim_table_lock_after_path_decision/
status = h002_main_validation_claim_table_lock_after_path_decision_ready
selected_path = main_validation_table_claim_locked_keep_official_test_blocked
validation_errors = 0
main_table = official_3DSSG_validation_split
official_test_benchmark = false
next_todo = compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock
```

Locked caption 핵심:

```text
Main validation benchmark on the official 3DSSG validation split. We compare
source-score ranking with H002 compatibility-aware reranking on VL-SAT and
Open3DSG validation predictions. Open3DSG is used as an open-vocabulary source,
while quantitative Recall@K is computed after mapping to closed-vocabulary 3DSSG
labels. Violation@K is our geometry-consistency metric.
```

Locked claim boundary:

- H002는 factorized reliability/reranking layer다.
- `C_e`는 `T_e + G_e`로 계산하고 `Z_e` source score는 final reranking에서만 결합한다.
- Main table은 official 3DSSG validation split 기준이다.
- Official 3DSSG test result, leaderboard/SOTA, unconstrained open-set GT evaluation은 막는다.
- H003 embedding은 H002 `C_e`의 representation-learning extension이며, 현재 main claim이
  아니라 future/optional extension이다.

다음 단계:

`main_validation_table_materialization`에서 caption-ready compact table rows와 caveat rows를
생성한다.

## 41. Main Validation Table Materialization

목적:

H002 main validation benchmark claim lock 이후, 이미 생성된 validation source-reranking
metric을 paper에 넣을 수 있는 compact table 형태로 정리했다. 이 단계는 새 metric 실행,
threshold tuning, official test 사용이 아니다.

결과:

```text
artifact_root = artifacts/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock/
status = h002_main_validation_table_materialization_after_claim_lock_ready
selected_path = main_validation_table_materialized_select_review
validation_errors = 0
main_table_rows = 5
source_family_caveat_rows = 3
control_rows = 15
next_todo = compatibility_dataset_v3_main_validation_table_review_after_materialization
```

Materialized files:

- `main_validation_table.csv`: K `{5,10,20,50,100}`에서 `S0_source_score`와 `S2_source_x_Ce` 비교.
- `main_validation_table.md`: caption-ready table.
- `source_family_caveats.csv`: 3개 Recall@K regression caveat.
- `control_table_compact.csv`: `C_e only`, shuffled-`C_e`, wrong-`T` control.
- `blocked_wording_checklist.csv`: official test, SOTA, open-set GT, uniform improvement, H003 main claim 차단.

현재 해석:

- Main validation benchmark material은 준비됐다.
- Official test benchmark result는 여전히 아니다.
- Open3DSG는 open-vocabulary source지만, 정량 평가는 closed-vocabulary 3DSSG mapping 기준이다.
- `Violation@K`는 H002 custom geometry-consistency metric으로 설명해야 한다.

## 42. Paper-Facing Folder Cleanup

목적:

H002 root, `tools/`, `artifacts/`가 hypothesis-stage exploration 파일로 과도하게 커져
현재 paper claim과 핵심 코드 경로를 파악하기 어려웠다. 따라서 paper claim에 직접 필요한
파일만 active H002 폴더에 남기고, 과거 target mining, smoke, diagnostic, path-search stage는
archive로 이동했다.

결과:

```text
archive_root = archive/hypothesis_records/hypothesis/H002_factorized-relation-confidence_cleanup_20260703/
root_stage_files = 236 -> 7
tools_py = 501 -> 26
artifact_dirs = 238 -> 28
pre_cleanup_readme = archive/.../root_files/README_before_cleanup.md
```

Active core:

- `README.md`: 현재 상태와 paper-facing file map.
- `paper_claim_core.md`: score 정의, runtime code, output artifact map.
- `summary_branch_v2.md`: full research-history synthesis.
- `artifacts/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock/`: main validation table.
- `tools/`: current paper-claim chain validators only.
- `experiments/H002_compatibility_routing/scripts/`: 실제 materialization, score extraction, geometry-only view, evaluation runtime code.
