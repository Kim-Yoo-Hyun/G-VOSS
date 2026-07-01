# H002 Proximity Close-By Candidate Materialization

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_proximity_close_by_candidate_materialization/
status = h002_compatibility_dataset_v3_proximity_close_by_candidate_materialization_ready_for_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit
```

## Decision

`close by` materialization은 성공했다. 계획했던 `1284`개 train-only row를 모두
materialize했고, quota/cap/schema precheck가 통과했다. 이 단계는 row construction이며,
learned smoke나 paper evidence가 아니다.

## Materialized Rows

```text
total_rows = 1284
primary_binary_rows = 800
  accept = 400
  reject = 400
abstain_qe_rows = 240
raw_distance_diagnostic_rows = 240
gt_geometry_conflict_audit_rows = 4
```

## Outputs

```text
model_safe_view.jsonl
hidden_manifest.jsonl
row_index.csv
quota_audit.csv
cap_audit.csv
schema_precheck.csv
report.md
summary.json
validation_errors.jsonl
```

## Quota Audit

All planned quotas passed.

```text
primary_binary accept = 400 / 400
primary_binary reject = 400 / 400
abstain near_nonexact_satisfied = 120 / 120
abstain ambiguous_distance = 80 / 80
abstain geometry_uncertain = 40 / 40
raw_distance_diagnostic accept = 120 / 120
raw_distance_diagnostic reject = 120 / 120
gt_geometry_conflict_audit = 4 / 4
total = 1284 / 1284
```

## Cap Audit

All caps passed.

```text
scan_id max = 15 / limit 18
directed_pair_id max = 1 / limit 2
primary_subject_object_class_pair max = 6 / limit 48
primary_class_pair_rank max = 2 / limit 24
raw_distance_bin max = 50 / limit 80
```

## Schema Precheck

`model_safe_view.jsonl` feature blocks do not contain:

```text
label_match_status
geometry_status
candidate_bucket
distance_bucket
scan_id
directed_pair_id
row_key
prediction_id
p_geom_valid
p_geom_invalid
```

These fields are stored only in `hidden_manifest.jsonl` for audit and controls.

## Boundary

```text
split = train_only_candidate_materialization
validation_usage = false
test_usage = false
h001_artifacts_modified = false
fills_labels = false
runs_learned_smoke = false
trains_new_model = false
paper_evidence_allowed = false
```

## Next

```text
compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit
```
