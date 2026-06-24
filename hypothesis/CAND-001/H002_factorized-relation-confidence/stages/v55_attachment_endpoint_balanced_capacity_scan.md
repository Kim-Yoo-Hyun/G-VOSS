# V55 Attachment Endpoint-Balanced Capacity Scan

## Purpose

v54에서 고정한 v20 endpoint-balanced counterfactual repair contract가 full train
attachment candidate pool에서 실제로 가능한지 검증한다.

이 단계는 capacity scan이며 candidate sheet, label fill, posterior smoke가 아니다.

Input:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan/
  match_rows.jsonl
```

Output:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan/
```

Script:

```text
tools/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan.py
```

## Result

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan_passed_ready_for_candidate_mining
capacity_pass = true
selected_capacity_route = exact_endpoint_pair_mixed_contrast_primary
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_candidate_mining
validation_errors = 0
posterior_smoke_allowed = false
```

## Pool

```text
attachment_rows = 556038
primary_rows = 370692
diagnostic_rows = 185346
raw_feature_join_coverage = 1.0
distinct_visible_endpoint_pairs = 7995
```

Primary proxy capacity:

```text
attached to positive / negative / uncertain = 54034 / 108852 / 22460
hanging on positive / negative / uncertain = 25457 / 148997 / 10892
connected to near / far diagnostic = 105712 / 79634
```

## Contrast Capacity

```text
exact_endpoint_pair_mixed_groups = 4616
exact_endpoint_pair_balanced_pairs = 26054
object_family_mixed_groups = 168
object_family_balanced_pairs = 10029
scan_balanced_mixed_blocks = 2309
scan_balanced_pairs = 60615
```

이 결과는 fallback이 아니라 exact visible endpoint-pair mixed contrast를 primary route로
쓸 수 있음을 의미한다.

## Preview Feasibility

All sample-size options pass.

```text
N=240 selected_rows = 240
N=320 selected_rows = 320
N=400 selected_rows = 400
quota_deficits = {}
```

Default next candidate size remains `320` because it gives:

```text
attached to positive/negative = 64/64
hanging on positive/negative = 64/64
connected to near/far diagnostic = 32/32
unique scans = 247
unique subgraphs = 294
unique visible endpoint pairs = 104
```

## Interpretation

v55 resolves the v54 capacity question positively. The blocker is no longer row capacity or
contrast availability. The next risk is candidate mining quality:

- selected rows must remain hidden-field-safe;
- exact endpoint-pair contrast should remain the primary construction route;
- `connected to` must remain diagnostic-only;
- internal preview fields must not become visible label fields or model inputs;
- posterior smoke remains blocked until label fill, ingestion, and target-independence audit pass.

## Boundary

- Train-only H002 hypothesis artifact.
- No validation/test rows were used.
- No labels were filled.
- No candidate sheet was released.
- No posterior was trained or evaluated.
- Internal preview files contain hidden capacity-audit fields only.
- H001 and paper artifacts were not modified.

## Next

```text
reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_candidate_mining
```
