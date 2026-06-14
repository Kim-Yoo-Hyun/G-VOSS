# Attachment Deferred G4b Error / Visual Sanity

Status: `attachment_deferred_error_visual_sanity_plan_ready_no_source_metrics`
Created at: `2026-05-28T05:50:42+00:00`

## Claim Boundary

This is an error-review and visual-sanity planning artifact. It does not
fit calibration, score VL-SAT/Open3DSG predictions, compute source
metrics, or change the current AAAI main claim.

## Error Distribution

- false satisfaction counterfactuals: `77`
- false violation positives: `30`
- uncertain positives: `164`
- uncertain counterfactuals: `165`
- strict positive candidates: `121`
- strict negative candidates: `204`

## Visual Queue

- queue rows: `50`
- queue by case type: `{'false_satisfaction_counterfactual': 20, 'false_violation_positive': 15, 'uncertain_counterfactual': 1, 'uncertain_positive': 14}`
- queue by label: `{'attached to': 38, 'connected to': 6, 'hanging on': 6}`

## Calibration Guidance

- exclude false-satisfied counterfactuals from negative calibration unless visual review confirms the seed is valid
- visual-check false-violated positives before relaxing policy thresholds
- keep uncertain rows out of strict calibration tables unless a separate soft-label protocol is defined

## Promotion Decision

`attachment_deferred` remains blocked for source metrics and main-claim
promotion until visual sanity review, calibration filter freeze, source
metrics, controls, bootstrap CI, and audit are complete. Main AAAI claim
promotion still requires explicit final user confirmation.

## Next Gate

`G4c_attachment_visual_review_or_calibration_filter_freeze`
