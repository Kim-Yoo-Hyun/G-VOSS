# H002 Proximity Close-By Candidate Materialization Plan

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan/
status = h002_compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan_ready
selected_path = materialize_close_by_controlled_candidates_with_distance_controls
validation_errors = 0
warnings = 2
next_todo = compatibility_dataset_v3_proximity_close_by_candidate_materialization
```

## Decision

`close by` candidate materialization으로 진행한다. 이 단계는 아직 row를 실제로 뽑지 않았고,
materialization contract만 고정했다. Learned smoke, label fill, model training, paper evidence는
아직 아니다.

## Planned Rows

```text
planned_total_rows = 1284
primary_binary_rows = 800
  accept_anchor = 400
  reject_far_geometry = 400
abstain_qe_rows = 240
  near_nonexact_satisfied = 120
  ambiguous_distance = 80
  geometry_uncertain = 40
raw_distance_diagnostic_rows = 240
  accept = 120
  reject = 120
gt_geometry_conflict_audit_rows = 4
```

Primary binary는 `C_e`와 `p_rel`의 accept/reject target이다. Abstain rows는 `Q_e`와
`p_obs`를 위한 보류/관측성 target이다. Raw-distance diagnostic subset은 `close by`가 단순
거리 threshold 문제로 붕괴하는지 확인하기 위한 별도 subset이다.

## Quota Policy

```text
accept_anchor =
  exact_match
  and geometry_status == satisfied
  and normalized_distance_xy <= 0.8

reject_far_geometry =
  label_match_status != exact_match
  and geometry_status == unsatisfied
  and normalized_distance_xy >= 2.5

abstain_qe =
  non-exact near row
  or ambiguous normalized distance
  or geometry_status == uncertain
```

`reject_far_geometry`는 `no_gt_for_pair`로 정의하지 않는다. Reject 근거는 far geometry와
unsatisfied geometry다. 단, 실제 reject 후보 중 `no_gt_for_pair`가 많기 때문에 이 정보는 hidden
control로만 보관하고 model input에는 넣지 않는다.

## Required Caps

```text
max_rows_per_scan = 18
max_rows_per_class_pair = 48
max_rows_per_class_pair_rank = 24
max_rows_per_directed_pair = 2
max_rows_per_raw_distance_bin = 80
```

이 cap은 scan memorization, class-pair shortcut, endpoint duplication, raw-distance bin
concentration을 막기 위한 것이다.

## Required Model Views And Controls

필수 view:

```text
T_only
Z_only
G_only
distance_only
p_geom_valid_rule
T_plus_G_compatibility
T_plus_G_plus_Q
Z_plus_C_plus_Q_later
```

필수 control:

```text
class_pair_only
source_only_Z
distance_only
p_geom_valid_rule
raw_distance_diagnostic_subset
shuffled_geometry
wrong_pair_geometry
```

`normalized_distance_diagnostic_subset`은 현재 불가능하다. Source inventory에서
normalized-distance bin accept/reject balanced capacity가 `0`이기 때문이다.

## Warnings

```text
normalized_distance_matched_capacity_zero
reject_pool_contains_no_gt_rows
```

해석:

- `close by`는 normalized distance로 target이 쉽게 나뉠 수 있다.
- 따라서 `distance_only`와 `p_geom_valid_rule` baseline 없이 H002 claim으로 올리면 안 된다.
- Reject 후보는 geometry-defined지만, 많은 row가 `no_gt_for_pair` 상태이므로 no-GT 정보를 hidden
  control로 분리해야 한다.

## Boundary

```text
split = train_only_materialization_plan
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
quota_table.csv
sampling_caps.csv
model_view_contract.csv
control_plan.csv
blocked_fields.csv
row_schema_contract.json
materialization_gates.csv
warnings.jsonl
route_decision.csv
report.md
validation_errors.jsonl
```

## Next

```text
compatibility_dataset_v3_proximity_close_by_candidate_materialization
```

다음 단계에서 실제 candidate rows를 materialize한다. 이후 반드시 schema/shortcut audit을 거친
뒤에만 learned smoke로 넘어갈 수 있다.
