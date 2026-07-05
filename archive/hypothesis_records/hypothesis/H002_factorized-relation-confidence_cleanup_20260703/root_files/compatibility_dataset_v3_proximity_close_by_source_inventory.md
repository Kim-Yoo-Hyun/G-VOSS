# H002 Proximity Close-By Source Inventory

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_source_inventory/
status = h002_compatibility_dataset_v3_proximity_close_by_source_inventory_ready_for_candidate_materialization_plan
selected_path = select_close_by_candidate_materialization_plan_with_far_geometry_negatives_and_controls
validation_errors = 0
next_todo = compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan
```

## Decision

`close by`는 candidate materialization plan으로 넘어갈 수 있다. 단, 이것은 아직
learned smoke나 paper evidence가 아니라 train-only source inventory 결과다.

핵심은 negative를 `no_gt_for_pair`로 정의하지 않았다는 점이다. Reject 후보는 다음 조건으로
정의했다.

```text
reject_far_geometry =
  label_match_status != exact_match
  and geometry_status == unsatisfied
  and normalized_distance_xy >= 2.5
```

즉 missing GT가 아니라 far geometry가 reject 후보의 근거다.

## Bucket Policy

```text
near = normalized_distance_xy <= 0.8
far = normalized_distance_xy >= 2.5
ambiguous = otherwise
```

이 기준은 이전 target plan의 full-train quantile에서 나온 것이다. `exact_match` close-by의
`normalized_distance_xy` 90% 지점이 약 `0.78`이고, `uncertain` row의 10% 지점이 약 `2.56`이라
`0.8 / 2.5`를 inventory threshold로 사용했다.

## Candidate Counts

```text
close_by_rows = 185346
accept_anchor = 8682
reject_far_geometry = 6688
abstain_or_audit = 169972
gt_geometry_conflict = 4
```

세부 분포:

```text
distance_bucket_counts = near 113280 / ambiguous 58046 / far 14020
label_status_counts = no_gt_for_pair 142571 / pair_has_other_predicate 33247 / exact_match 9528
geometry_status_counts = satisfied 171326 / uncertain 7328 / unsatisfied 6692
reject_label_status_counts = no_gt_for_pair 6138 / pair_has_other_predicate 550
```

`accept_anchor`는 `exact_match + satisfied + near`로 잡았다. `reject_far_geometry`는
`non-exact + unsatisfied + far`다. `abstain_or_audit`는 uncertain, ambiguous, 또는 non-exact
near row를 포함한다.

## Control Capacity

```text
class_pair mixed groups = 529
class_pair balanced rows = 3684
class_pair_rank mixed groups = 550
class_pair_rank balanced rows = 3280
raw_distance_bin mixed groups = 6
raw_distance_bin balanced rows = 804
norm_distance_bin mixed groups = 0
norm_distance_bin balanced rows = 0
scan mixed groups = 520
scan balanced rows = 7656
```

해석:

- class-pair와 class-pair+rank control은 충분하다.
- raw-distance matched control은 가능하지만 수량이 작으므로 diagnostic subset으로 둔다.
- normalized-distance matched control은 0이다. 현재 target 자체가 normalized distance로
  near/far를 나누기 때문에 당연한 결과다.
- 따라서 `close by`에서 `distance_only` baseline은 필수다. H002가 주장할 수 있는 것은
  “distance threshold 하나로 충분하다”가 아니라, distance baseline과 비교하면서 scale, overlap,
  semantic content, evidence quality를 구조적으로 분리한다는 점이다.

## Feature Availability

Current match rows에서 다음 `G_e` 후보는 전 row에서 사용 가능하다.

```text
distance_3d
distance_xy
normalized_distance_3d
normalized_distance_xy
projected_iou_xy
projected_subject_overlap_ratio
projected_object_overlap_ratio
center_delta_z
normalized_center_delta_z
subject/object top and bottom z
```

`p_geom_valid`도 전 row에 있지만 baseline-only다. `C_e`의 main input/target으로 직접 사용하지
않는다.

현재 없는 축:

```text
subject_object_full_xyz_extent
multi_view_visibility
```

따라서 full 3D extent나 multi-view visibility를 쓰려면 별도 source adapter가 필요하다. 이번
close-by path에서는 현재 match row의 metric geometry와 projected overlap을 먼저 사용한다.

## Gate Result

모든 inventory gate를 통과했다.

```text
accept_anchor_count = 8682 / required 160
reject_far_geometry_count = 6688 / required 160
abstain_or_audit_count = 169972 / required 80
class_pair_balanced_capacity = 3684 / required 400
class_pair_rank_balanced_capacity = 3280 / required 400
raw_distance_balanced_capacity = 804 / required 200
```

## Boundary

```text
split = train_only_source_inventory
validation_usage = false
test_usage = false
h001_artifacts_modified = false
materializes_rows = false
fills_labels = false
runs_learned_smoke = false
trains_new_model = false
paper_evidence_allowed = false
```

## Artifacts

```text
summary.json
candidate_policy.csv
target_bucket_counts.csv
feature_availability.csv
control_group_summary.csv
class_pair_mixed_capacity.csv
class_pair_rank_mixed_capacity.csv
raw_distance_mixed_capacity.csv
raw_distance_rank_mixed_capacity.csv
raw_distance_class_pair_mixed_capacity.csv
norm_distance_mixed_capacity.csv
scan_mixed_capacity.csv
candidate_examples.json
gate_results.csv
route_decision.csv
report.md
validation_errors.jsonl
```

## Next

```text
compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan
```

다음 materialization plan에서는 scan/class-pair concentration cap, class-pair+rank control,
raw-distance diagnostic subset, distance-only baseline, shuffled/wrong-pair geometry control을
반드시 포함한다. Support/contact 개별 predicate probe는 close-by candidate path 결정 이후
진행한다.
