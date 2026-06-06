# Attachment Deferred G5d Full-Source Metrics

Status: `attachment_deferred_g5d_full_source_metrics_ready`
Created at: `2026-06-06T05:05:38+00:00`

## Claim Boundary

`attachment_deferred` remains outside the current AAAI main claim unless
explicitly promoted after reviewing this artifact. This G5d run provides
source metrics and controls, not a paper-claim update by itself.

## Counts

- scored rows: `135048`
- validation errors: `0`
- shards complete: `69` / `69`

## Source Metrics

### open3dsg_ov

- covered denominator: `768` / `967`
- missing exact-label GT rows: `199`

| condition | R@50 | R@100 | V@50 | V@100 | U@100 |
|---|---:|---:|---:|---:|---:|
| `semantic_only` | 0.7995 | 0.9297 | 0.2792 | 0.3021 | 0.4821 |
| `probabilistic_recalibrated` | 0.4831 | 0.6628 | 0.1409 | 0.2460 | 0.4569 |
| `rule_verified_attachment_policy` | 0.7930 | 0.9245 | 0.0257 | 0.0842 | 0.6483 |
| `control_p_geom_valid_only` | 0.4818 | 0.6602 | 0.1375 | 0.2467 | 0.4562 |
| `control_distance_only` | 0.7578 | 0.9479 | 0.1078 | 0.2085 | 0.4715 |
| `control_shuffled_geometry` | 0.4219 | 0.6901 | 0.3148 | 0.3198 | 0.4795 |
| `control_wrong_pair_geometry` | 0.5208 | 0.7786 | 0.3102 | 0.3141 | 0.4580 |

### vlsat_closed_set

- covered denominator: `967` / `967`
- missing exact-label GT rows: `0`

| condition | R@50 | R@100 | V@50 | V@100 | U@100 |
|---|---:|---:|---:|---:|---:|
| `semantic_only` | 0.9959 | 1.0000 | 0.1594 | 0.2126 | 0.6075 |
| `probabilistic_recalibrated` | 0.9897 | 0.9979 | 0.1419 | 0.2210 | 0.5630 |
| `rule_verified_attachment_policy` | 0.9276 | 0.9380 | 0.0033 | 0.0215 | 0.7530 |
| `control_p_geom_valid_only` | 0.4829 | 0.5688 | 0.1016 | 0.2208 | 0.4565 |
| `control_distance_only` | 0.6649 | 0.9204 | 0.0756 | 0.1653 | 0.4772 |
| `control_shuffled_geometry` | 0.9462 | 0.9814 | 0.1718 | 0.2355 | 0.5846 |
| `control_wrong_pair_geometry` | 0.9814 | 0.9969 | 0.1811 | 0.2349 | 0.5729 |

## Warnings

- `connected_to_dev_absent_use_pooled_or_train_only_caveat`
