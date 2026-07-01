# H002 R6 Supported-By Decomposition Candidate Materialization Plan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan/
status = h002_compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan_ready
selected_path = plan_320row_supported_by_decomposition_with_240row_min_viable_fallback
validation_errors = 0
next_todo = compatibility_dataset_v3_supported_by_decomposition_candidate_materialization
```

## Plan

R6 `supported by`를 binary compatibility target이 아니라 four-way decomposition
target으로 materialize한다.

Preferred target:

```text
total_rows = 320
per_label = 80
```

Minimum viable fallback:

```text
total_rows = 240
per_label = 60
```

## Labels

| Label | Preferred | Minimum | Source Role |
| --- | ---: | ---: | --- |
| `accept_broad_support` | 80 | 60 | exact supported-by / clear accept |
| `relabel_to_subtype` | 80 | 60 | support exists but `standing on` or `lying on` is more specific |
| `reject_no_support` | 80 | 60 | explicit no-support geometry/visual contradiction |
| `abstain` | 80 | 60 | generic/missing/occluded/ontology-overlap/unclear subtype |

## Source Capacity

```text
supported_by_rows = 50601
supported_by_class_pair_balanced_rows = 164
supported_by_class_pair_rank_balanced_rows = 130
clear_accept_rows = 491
hard_reject_no_support_rows = 12712
overlap_or_abstain_rows = 37398
existing_supported_by_diagnostic_rows = 160
```

## Balancing Gates

- `max_rows_per_scan = 12`
- `max_rows_per_directed_pair = 1`
- `max_rows_per_subject_object_class_pair = 16`
- `min_mixed_class_pair_cells = 12`
- `max_hard_surface_share = 0.55`
- `max_generic_endpoint_abstain_share = 0.50`

## Required Controls

- `class_pair_only`
- `source_score_rank_hidden`
- `generic_endpoint_only`
- `hard_surface_slice`
- `wrong_pair_geometry`
- `shuffled_G_within_class_pair`
- `no_GT_not_negative`
- `subtype_relabel_consistency`

## Boundary

- Train-only planning only.
- No rows materialized in this step.
- No learned smoke/model training.
- No validation/test usage.
- H001 artifacts were not modified.
- No paper-level evidence is claimed.

## Next

```text
compatibility_dataset_v3_supported_by_decomposition_candidate_materialization
```
