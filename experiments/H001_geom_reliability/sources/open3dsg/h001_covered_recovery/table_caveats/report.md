# Open3DSG H001 Covered-Recovery Sensitivity Report

Status: `open3dsg_h001_covered_recovery_sensitivity_ready`
Created at: `2026-06-05T18:11:32+00:00`

## Scope

- branch role: historical 127-scan H001 covered-scope sensitivity, not the paper-facing full-validation main result
- preprocess coverage: `388/388`
- feature coverage: `388/388`
- raw stream: `388` batches, `19224` rows
- raw process exit: `137`
- adapter rows: `498212`
- geometry rows: `498212`
- bootstrap: `ready`

## Metrics

| condition | R2 R@50 | R2 R@100 | R2 V@50 | R2 V@100 | R2 - avg R@100 | R2 - avg V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| semantic_only | 0.3972 | 0.4990 | 0.1331 | 0.1199 | +0.28 pp | +0.04 pp |
| probabilistic_recalibrated | 0.3870 | 0.5607 | 0.0594 | 0.0811 | +0.28 pp | +0.08 pp |
| rule_verified_point_subtype | 0.4177 | 0.5265 | 0.0000 | 0.0000 | +0.28 pp | +0.00 pp |
| control_family_specific_p_geom_valid | 0.4558 | 0.6012 | 0.0254 | 0.0323 | +0.28 pp | +0.13 pp |

## Interpretation

- R2 removes the historical 377/388 covered-scope missing-context caveat for the 127-scan sensitivity branch.
- R2 changes the old avg-BLIP point estimates only slightly: R@100 rises by about +0.28 percentage points for all main conditions, while Violation@100 rises by about +0.04 to +0.13 percentage points.
- The qualitative paper message does not change: geometry-aware variants still reduce violations strongly, and family-specific calibration still gives the best R@100/violation tradeoff among the listed Open3DSG conditions.
- The wording value is robustness/sensitivity, not main-claim expansion. It can support an appendix sentence that the historical missing 11 contexts did not drive the Open3DSG trend.
- This branch should not replace the current full-validation 548/548 recovery main route.

## Caveats

- R2 is a historical H001 covered-scope sensitivity branch, not the full official validation paper-facing route.
- R2 uses recovery-policy interventions: the Open3DSG visible-object gate was relaxed to min_visible=2 for recovered contexts, and one scan required relaxed view regeneration.
- The latest raw stream artifact is complete, but the Docker process still exited 137 after finalization due to container teardown/OOM; this is a process provenance caveat, not a row-completeness blocker.
- R2 reduces the missing-preprocessed-context caveat only for this historical branch. It does not solve attachment_deferred candidate-pair-universe gaps.
- A raw-dump-only runner is useful only if this R2 branch is promoted as process-clean provenance; it is not required for the current main full-validation claim.
