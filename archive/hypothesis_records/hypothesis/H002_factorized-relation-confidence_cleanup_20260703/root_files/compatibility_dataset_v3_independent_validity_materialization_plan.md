# H002 Independent Validity Materialization Plan

## Status

```text
stage = compatibility_dataset_v3_independent_validity_materialization_plan
status = h002_compatibility_dataset_v3_independent_validity_materialization_plan_ready
selected_path = materialize_balanced_gt_anchored_independent_validity_candidates
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_candidate_materialization
```

## Artifact

```text
script = tools/compatibility_dataset_v3_independent_validity_materialization_plan.py
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_materialization_plan/
input_inventory = artifacts/compatibility_dataset_v3_independent_validity_source_inventory/
```

Generated files:

- `summary.json`
- `row_schema_contract.json`
- `matching_policy.json`
- `next_plan_contract.json`
- `quota_table.csv`
- `blocked_field_table.csv`
- `validation_errors.jsonl`
- `report.md`

## Planned Counts

```text
planned_total_rows = 4027
planned_primary_binary_rows = 3200
planned_nonbinary_audit_or_abstain_rows = 827
```

Family totals:

```text
relative_vertical = 2012
support_contact_pose_conditioned = 2015
```

Role totals:

```text
positive = 1600
negative = 1600
abstain_or_audit = 400
abstain = 400
audit_required = 27
```

## Primary Binary Plan

Primary binary rows are balanced by family:

| Family | Positive Pool | Positive Quota | Negative Pool | Negative Quota |
| --- | --- | --- | --- | --- |
| `relative_vertical` | `exact GT + geometry satisfied` | `800` | `GT-pair other-predicate/same-family mismatch + geometry unsatisfied` | `800` |
| `support_contact_pose_conditioned` | `exact GT + geometry satisfied` | `800` | `GT-pair other-predicate/same-family mismatch + geometry unsatisfied` | `800` |

This gives:

```text
primary_binary_rows = 3200
positive = 1600
negative = 1600
```

## Abstain And Audit Plan

No-GT rows are not negatives. They are materialized only as abstain/audit rows:

| Family | Pool | Quota | Role |
| --- | --- | --- | --- |
| `relative_vertical` | `no-GT + geometry satisfied` | `200` | abstain/audit |
| `relative_vertical` | `geometry uncertain` | `200` | abstain |
| `relative_vertical` | `exact GT + geometry unsatisfied` | `12` | audit required |
| `support_contact_pose_conditioned` | `no-GT + geometry satisfied` | `200` | abstain/audit |
| `support_contact_pose_conditioned` | `geometry uncertain` | `200` | abstain |
| `support_contact_pose_conditioned` | `exact GT + geometry unsatisfied` | `15` | audit required |

## Label Policy

```text
C_e_validity:
  positive rows -> 1
  negative rows -> 0
  no-GT / uncertain rows -> abstain
  exact-GT-but-unsatisfied rows -> audit_required

p_rel:
  positive rows -> accept
  negative rows -> reject
  abstain rows -> abstain
  audit rows -> audit_required

p_obs:
  geometry satisfied or unsatisfied rows -> observable
  geometry uncertain rows -> abstain_or_unobservable
```

## Schema Boundary

Model-safe blocks:

- `T_e`
- `Z_e_safe`
- `G_e`
- `Q_e_safe`

Blocked from model input:

- row identity fields;
- scan id and directed pair id;
- raw GT join labels;
- matched GT ids and matched predicates;
- target labels;
- hidden controls;
- provenance fields.

## Hard-Negative Matching Policy

Priority:

1. same predicate family when available;
2. same rank band;
3. same object-class pair if possible;
4. scan and visible-pair caps.

Caps:

```text
max_single_scan_share = 0.08
max_single_visible_pair_share = 0.05
group_by = scan_id + directed_pair_id
```

## Next

The next stage may materialize the rows following this frozen plan:

```text
compatibility_dataset_v3_independent_validity_candidate_materialization
```

Required gates after materialization:

- row-count and quota audit;
- no-GT negative policy audit;
- blocked-field absence audit;
- group integrity audit;
- single-feature shortcut audit;
- schema/shortcut audit before learned smoke.

## Boundary

- Train-only materialization plan.
- No validation/test usage.
- No row materialization in this stage.
- No learned model trained.
- No H001 artifact modification.
- No paper-level evidence promotion.
