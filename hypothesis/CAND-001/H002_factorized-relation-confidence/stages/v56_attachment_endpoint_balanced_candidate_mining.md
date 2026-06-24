# V56 Attachment Endpoint-Balanced Candidate Mining

## Purpose

v55 capacity scan에서 통과한 exact endpoint-pair mixed contrast route를 실제 train-only
candidate sheet와 hidden manifest로 materialize한다.

이 단계는 candidate mining이며 label fill, source inventory, posterior smoke가 아니다.

Input:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan/
```

Output:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_candidate_mining/
```

Script:

```text
tools/reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_candidate_mining.py
```

## Result

```text
status = h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_candidate_mining_ready_for_source_inventory
next_todo = reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_source_inventory
validation_errors = 0
posterior_smoke_allowed = false
visible_leakage_hits = 0
```

Candidate counts:

```text
selected_rows = 320
primary_binary_candidate_rows = 256
connected_diagnostic_rows = 64
attached_to_rows = 128
hanging_on_rows = 128
connected_to_rows = 64
unique_scans = 247
unique_subgraphs = 294
unique_visible_endpoint_pairs = 104
```

Hidden proxy balance:

```text
attached to positive/negative proxy = 64/64
hanging on positive/negative proxy = 64/64
connected to near/far diagnostic = 32/32
```

Selection route:

```text
E1_exact_visible_endpoint_pair = 256
E4_global_hard_negative_or_diagnostic_fallback = 64
```

`E4` rows are the `connected to` diagnostic rows. The primary binary rows remain exact endpoint-pair
mixed contrast.

## Boundary

- Train-only H002 hypothesis artifact.
- No validation/test rows were used.
- No labels were filled.
- No posterior was trained or evaluated.
- Hidden proxy role, typed witness cell, rank band, scan/subgraph ids, selection route, and geometry
  construction fields are hidden manifest fields only.
- Reviewer-visible sheet has no detected leakage hits.
- Multi-view/mesh assets must be inventoried before label fill.
- H001 and paper artifacts were not modified.

## Next

```text
reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_source_inventory
```
