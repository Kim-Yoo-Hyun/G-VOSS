# H002 R7 Attachment Observability Class-Pair Repair Capacity Scan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan/
status = h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan_ready_for_candidate_mining
selected_path = exact_predicate_class_pair_repair_candidate_mining
validation_errors = 0
next_todo = compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining
```

## Result

The scan used full-train Open3DSG-side R7 rows only. It did not materialize
model rows, create packets, fill labels, or run learned smoke.

Exact `predicate_label + subject_label + object_label` capacity:

| Axis | Groups | Mixed Groups | Raw Balanced Rows | Scan-Capped Balanced Rows |
| --- | ---: | ---: | ---: | ---: |
| exact predicate/class-pair | 15,990 | 4,616 | 81,724 | 73,636 |

Per-predicate exact class-pair capacity:

| Predicate | Groups | Mixed Groups | Accept Proxy | Reject Proxy | Uncertain Proxy | Scan-Capped Balanced Rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `attached to` | 7,995 | 3,232 | 54,034 | 108,852 | 22,460 | 50,662 |
| `hanging on` | 7,995 | 1,384 | 25,457 | 148,997 | 10,892 | 22,974 |

Capacity gates:

- balanced primary rows `>= 400`: pass
- positive rows `>= 100`: pass
- exact predicate/class-pair mixed strata `>= 20`: pass
- per-predicate mixed strata `>= 10`: pass for both primary predicates
- per-predicate scan-capped balanced rows `>= 120`: pass for both primary predicates

## Interpretation

The previous 560-row R7 artifact failed because exact predicate/class-pair cells
were not mixed. The full-train scan shows that this is a sampling artifact, not
an inherent lack of material: `attached to` and `hanging on` have many exact
class-pair cells containing both accept-proxy and reject-proxy candidates.

This does not yet prove the H002 observability route. The labels are still
capacity proxies derived from attachment-specific geometry/coverage heuristics.
The next step must mine a controlled candidate set and then run packet/label
ingestion plus schema/shortcut audits before any learned smoke.

## Boundary

- Train-only capacity scan.
- No validation/test use.
- No H001 artifacts modified.
- No candidate rows or model-safe rows materialized.
- No labels filled.
- No packet creation.
- No learned model or posterior smoke.
- `proxy_role`, `geometry_bucket`, `coverage_proxy`, rank, source confidence,
  and GT match status remain hidden construction fields, not model input.

