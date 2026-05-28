# Attachment Deferred G3 Calibration / Counterfactual Route

Status: `attachment_deferred_calibration_counterfactual_plan_ready_no_fit_no_metrics`
Created at: `2026-05-28T05:14:05+00:00`

## Claim Boundary

This is a G3 route-freeze artifact. It prepares train-dev positive seeds,
counterfactual-negative seeds, policy-smoke routing, GT verifier-evaluation
inputs, and threshold-freeze protocol before any source metrics. It does not
apply the verifier policy, fit calibration, score VL-SAT/Open3DSG predictions,
or compute paper metrics.

## Positive Seeds

- rows: `315`
- by role: `{'dev': 72, 'train': 243}`
- by label: `{'attached to': 269, 'connected to': 6, 'hanging on': 40}`
- by role/label: `{'dev:attached to': 57, 'dev:hanging on': 15, 'train:attached to': 212, 'train:connected to': 6, 'train:hanging on': 25}`

## Counterfactual Seeds

- rows: `446`
- by role: `{'dev': 105, 'train': 341}`
- by label: `{'attached to': 354, 'connected to': 12, 'hanging on': 80}`
- by strategy: `{'far_object_pair': 274, 'floor_support_replacement_for_hanging': 40, 'gravity_inconsistent_hanging': 40, 'wrong_pair_attachment': 6, 'wrong_surface_replacement': 86}`

Counterfactual seeds require geometry-margin validation before becoming
calibration negatives. They are not absent-edge negatives.

## Warnings

- `dev_split_has_no_connected_to_positive_seed_use_pooled_or_augmented_dev_before_family_specific_connected_claim`
- `skipped_negative_generation:{'duplicate_negative_id': 2, 'no_negative_candidate:train:attached to': 1}`

## Next Gate

`G4_attachment_gt_verifier_evaluation_and_policy_smoke`
