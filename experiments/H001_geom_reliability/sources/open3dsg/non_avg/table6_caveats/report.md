# Open3DSG Non-Avg Branch Table 6 And Caveat Report

Status: `open3dsg_non_avg_branch_ready`
Created at: `2026-06-04T11:43:27.450286+00:00`

## Branch Status

- blockers: none

## Table 6 Candidate Rows

| source | metric status | claim use | caveat |
| --- | --- | --- | --- |
| Open3DSG avg-BLIP | ready | current paper-facing Open3DSG result | averaged-BLIP variant; filtered train/dev; covered H001 377/388; exact-label denominator 2545 |
| Open3DSG official non-avg | ready | candidate replacement or robustness branch after full downstream regeneration | official non-avg checkpoint; filtered train/dev and covered-scope caveats still apply |

## Metric Comparison

| condition | avg R@100 | non-avg R@100 | delta R@100 | avg V@100 | non-avg V@100 | delta V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| semantic_only | 0.4963 | 0.5320 | 0.0358 | 0.1195 | 0.1256 | 0.0061 |
| probabilistic_recalibrated | 0.5580 | 0.5639 | 0.0059 | 0.0803 | 0.0782 | -0.0021 |
| rule_verified_point_subtype | 0.5238 | 0.5481 | 0.0244 | 0.0000 | 0.0000 | 0.0000 |
| family_conditional_risk | 0.5984 | 0.6047 | 0.0063 | 0.0311 | 0.0310 | -0.0001 |

## Caveat Wording

- if blocked: Do not update the current paper Table 6 or Open3DSG caveat wording. The active downstream result remains the avg-BLIP Open3DSG branch.
- if ready: Report the official non-avg Open3DSG branch as a separately regenerated downstream result. The averaged-BLIP caveat can be removed only for this branch, while filtered train/dev, covered H001 377/388, exact-label denominator 2545, validation_missing_preprocessed:11, and residual calibration-risk caveats remain visible. Promotion over avg-BLIP requires user confirmation.

## Claim Boundary

This artifact compares Open3DSG downstream branches. It does not promote the non-avg branch to the main paper claim without complete metrics, bootstrap, caveat wording, and user confirmation.
