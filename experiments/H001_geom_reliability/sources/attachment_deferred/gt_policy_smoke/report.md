# Attachment Deferred G4 GT Policy Smoke

Status: `attachment_deferred_gt_policy_smoke_ready_no_source_metrics`
Created at: `2026-05-28T05:40:50+00:00`

## Claim Boundary

This is a G4 policy-smoke and train-dev GT/counterfactual verifier
evaluation artifact. It does not run source metrics, fit calibration,
score VL-SAT/Open3DSG predictions, or change the current AAAI main
claim.

## G1c Policy Smoke

- rows: `36`
- status counts: `{'satisfied': 15, 'uncertain': 14, 'violated': 7}`

## Train/Dev GT-Counterfactual Evaluation

- rows: `761`
- positives: `315`
- counterfactuals: `446`
- positive nonviolated rate: `0.904762`
- positive strict satisfied rate: `0.384127`
- counterfactual nonsatisfied rate: `0.827354`
- counterfactual strict violated rate: `0.457399`
- calibration-ready counterfactual negatives: `204`
- uncertain rate all: `0.432326`

## Important Interpretation

`positive_nonviolated_rate` and `counterfactual_nonsatisfied_rate` are
conservative policy checks. `uncertain` is counted as nonviolated for
positives and nonsatisfied for counterfactuals, but uncertain rows are
not calibration-ready proof. A fitted `p_geom_valid` calibrator, source
metrics, controls, bootstrap CI, and visual audit remain required before
any main-claim promotion.

## Next Gate

`G4b_attachment_error_visual_sanity_before_calibration`
