# Qwen-VL H001 Adapter Export Report

Status: `qwen_vl_adapter_export_ready`
Created at: `2026-06-11T18:16:10+00:00`

## Counts

- input_rows: `46506`
- parsed_rows: `46506`
- exported_predictions: `35131`
- exported_in_scope_predictions: `32236`
- ground_truth_rows: `11254`
- target_family_gt_rows: `3972`
- target_family_gt_rows_with_qwen_input_pair_family: `2880`
- exact_label_gt_keys_hit_by_qwen_predictions: `1453`

## Parser Status

- parsed: `46505`
- parsed_with_warning: `1`

## Canonicalization Boundary

The adapter maps Qwen visual-language synonyms into the existing H001 predicate vocabulary only where the current verifier semantics are aligned: `next to`/`near` -> `close by`, `above` -> `higher than`, and `under` -> `lower than`. `far from` and `part of` are exported as unsupported for the current H001 metric scope.

This export is still not paper evidence until geometry join, metric/control evaluation, bootstrap CI, and failure/audit artifacts are generated.
