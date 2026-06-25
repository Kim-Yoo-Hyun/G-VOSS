# Open3DSG Raw Provenance Review

Status: `open3dsg_raw_provenance_review_ready`
Mode: `h001_covered_recovery_sensitivity`
Created at: `2026-06-06T11:59:10+00:00`

## Claim Boundary

This is an appendix/sensitivity branch for the historical 127-scan H001 covered scope. It is not the paper-facing full-validation main route.

## H001 Covered-Recovery Sensitivity

- preprocess coverage: `388/388`
- feature coverage: `388/388`
- canonical raw rows: `19224`
- clean-return retry2 raw rows: `19224`
- clean-return retry2 process exit: `137`
- canonical vs clean-return retry2 equivalence: `row_equivalent`
- downstream table status: `open3dsg_h001_covered_recovery_sensitivity_ready`

## Metric Snapshot

| condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| semantic_only | 0.3972 | 0.4990 | 0.1331 | 0.1199 |
| probabilistic_recalibrated | 0.3870 | 0.5607 | 0.0594 | 0.0811 |
| rule_verified_point_subtype | 0.4177 | 0.5265 | 0.0000 | 0.0000 |
| family_conditional_risk | 0.4558 | 0.6012 | 0.0254 | 0.0323 |

## Decision

Use R2 as appendix robustness evidence: the old 377/388 historical scope caveat does not drive the Open3DSG trend. Do not use it to replace the current full-validation 548/548 recovery main route.
