# Splits

## Role

Stores grouped train/dev/heldout split assignments for the internal H002
candidate pool.

## Latest Outputs

```text
latest/model_safe_split_view.jsonl
latest/split_assignments.jsonl
latest/group_manifest.jsonl
latest/split_manifest.json
latest/leakage_audit.csv
latest/validation_errors.jsonl
```

## Paper Status

Used to fit internal C_e models without scan/group leakage. It is not official
validation/test itself.
