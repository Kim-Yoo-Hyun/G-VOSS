# Attachment Deferred G5d Full-Source Metrics

Status: `attachment_deferred_g5d_full_source_metrics_ready`
Created at: `2026-06-28T08:47:49+00:00`

## Claim Boundary

`attachment_deferred` remains outside the current AAAI main claim unless
explicitly promoted after reviewing this artifact. This G5d run provides
source metrics and controls, not a paper-claim update by itself.

## Counts

- scored rows: `190722`
- validation errors: `0`
- shards complete: `99` / `99`

## Source Metrics

### open3dsg_ov

- covered denominator: `968` / `1205`
- missing exact-label GT rows: `237`

| condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 | U@100 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `semantic_only` | 0.1395 | 0.2149 | 0.2965 | 0.4917 | 0.7738 | 0.2675 | 0.3174 | 0.3493 | 0.3343 | 0.3163 | 0.4720 |
| `probabilistic_recalibrated` | 0.2211 | 0.3027 | 0.3812 | 0.4659 | 0.6529 | 0.0219 | 0.0373 | 0.0635 | 0.1434 | 0.2538 | 0.4594 |
| `rule_verified_attachment_policy` | 0.1415 | 0.2304 | 0.3326 | 0.5795 | 0.9008 | 0.0015 | 0.0024 | 0.0080 | 0.0306 | 0.0907 | 0.6463 |
| `control_p_geom_valid_only` | 0.1674 | 0.2479 | 0.3326 | 0.4659 | 0.6498 | 0.0109 | 0.0225 | 0.0528 | 0.1433 | 0.2542 | 0.4590 |
| `control_distance_only` | 0.0217 | 0.1364 | 0.3110 | 0.7438 | 0.9380 | 0.0055 | 0.0334 | 0.0650 | 0.1134 | 0.2201 | 0.4721 |
| `control_shuffled_geometry` | 0.0682 | 0.1126 | 0.1890 | 0.4008 | 0.6715 | 0.3186 | 0.3271 | 0.3211 | 0.3214 | 0.3239 | 0.4820 |
| `control_wrong_pair_geometry` | 0.0826 | 0.1209 | 0.2231 | 0.4959 | 0.7810 | 0.3234 | 0.3397 | 0.3312 | 0.3154 | 0.3191 | 0.4604 |

### vlsat_closed_set

- covered denominator: `1205` / `1205`
- missing exact-label GT rows: `0`

| condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 | U@100 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `semantic_only` | 0.7983 | 0.9336 | 0.9809 | 0.9959 | 1.0000 | 0.1288 | 0.1265 | 0.1349 | 0.1626 | 0.2176 | 0.6132 |
| `probabilistic_recalibrated` | 0.5710 | 0.8050 | 0.9369 | 0.9884 | 0.9992 | 0.0467 | 0.0604 | 0.0846 | 0.1455 | 0.2262 | 0.5668 |
| `rule_verified_attachment_policy` | 0.7295 | 0.8498 | 0.8905 | 0.8996 | 0.9112 | 0.0000 | 0.0000 | 0.0000 | 0.0048 | 0.0207 | 0.7646 |
| `control_p_geom_valid_only` | 0.1693 | 0.2481 | 0.3485 | 0.4639 | 0.5527 | 0.0040 | 0.0128 | 0.0304 | 0.1055 | 0.2254 | 0.4640 |
| `control_distance_only` | 0.0149 | 0.0929 | 0.2349 | 0.6498 | 0.9079 | 0.0026 | 0.0226 | 0.0496 | 0.0759 | 0.1756 | 0.4819 |
| `control_shuffled_geometry` | 0.5859 | 0.7610 | 0.8647 | 0.9344 | 0.9751 | 0.1365 | 0.1372 | 0.1462 | 0.1789 | 0.2434 | 0.5887 |
| `control_wrong_pair_geometry` | 0.7021 | 0.8598 | 0.9369 | 0.9826 | 0.9967 | 0.1347 | 0.1345 | 0.1464 | 0.1876 | 0.2418 | 0.5765 |

## Warnings

- `connected_to_dev_absent_use_pooled_or_train_only_caveat`
