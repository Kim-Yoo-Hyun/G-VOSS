# Attachment Deferred G4c Strict Filter Freeze

Status: `attachment_deferred_strict_filter_frozen_no_fit_no_source_metrics`
Created at: `2026-05-28T06:11:44+00:00`

## Claim Boundary

This artifact freezes a strict-only calibration subset. It does not fit
calibration, score VL-SAT/Open3DSG predictions, compute source metrics,
run controls/bootstrap, or change the current AAAI main claim.

## Frozen Rows

- strict rows: `325`
- strict positives: `121`
- strict negatives: `204`
- excluded rows: `436`
- strict by label: `{'attached to': 200, 'connected to': 12, 'hanging on': 113}`
- strict by split: `{'dev': 83, 'train': 242}`

## Exclusions

- excluded by disposition: `{'exclude_or_review_counterfactual_seed_false_satisfaction': 77, 'review_false_violation_before_any_positive_calibration_use': 30, 'skip_or_review_uncertain_negative': 165, 'soft_positive_or_review_before_calibration': 164}`
- excluded by label: `{'attached to': 423, 'connected to': 6, 'hanging on': 7}`

## Warnings

- `connected to:dev:no_strict_rows`
- `connected_to_dev_absent_use_pooled_or_train_only_caveat`

## Next Gate

Fit attachment train-dev calibration from `strict_calibration_rows.jsonl`,
then run VL-SAT/Open3DSG source metrics and controls. Do not promote
`attachment_deferred` into the main AAAI claim without explicit final
user confirmation.
