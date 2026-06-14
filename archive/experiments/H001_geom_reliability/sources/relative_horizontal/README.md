# Relative Horizontal Expansion Track

Last updated: 2026-06-06 KST

Status: `appendix_limitation_frozen_no_metric_execution`

This folder tracks the optional `relative_horizontal` expansion path for H001.
It is not part of the current paper claim yet. The locked main claim remains
scoped to `support_contact`, `proximity`, and `relative_vertical` until this
track reaches the same evidence standard.

Update: `left/right` has been split into a narrower `relative_lateral`
candidate family under `../relative_lateral/`. `front/behind` remains deferred
as `relative_depth_deferred` because the full `relative_horizontal` audit is not
strong enough for promotion.

Consolidated relation expansion status is tracked in
`../relation_expansion_status.md`.

## Motivation

The current H001 denominator has 2,545 in-scope GT rows:

- `support_contact`: 1,199
- `proximity`: 1,128
- `relative_vertical`: 218

The largest excluded geometry-adjacent family is `relative_horizontal`:

- `relative_horizontal`: 3,570 GT rows
- labels: `left`, `right`, `front`, `behind`

If validated, the geometry-checkable denominator would expand from 2,545 to
6,115 GT rows, about 81% of the 7,505 held-out GT rows.

## Claim Boundary

Allowed now:

- Use `relative_horizontal` as a separate validation track to test whether the
  calibrated geometry-consistency framework can expand to another spatial
  family.
- Report its current status as planned or appendix/future-work evidence.

Blocked now:

- Do not add `relative_horizontal` to Table 3, the abstract, or the main claim.
- Do not describe H001 as covering all spatial relations.
- Do not call the result broader until Docker metrics, controls, calibration,
  bootstrap CI, and failure/audit evidence are complete.

## Core Risk

`left/right/front/behind` relations may depend on a coordinate-frame convention:
scan/world axes, room axes, object-centric axes, annotator viewpoint, or camera
viewpoint. A wrong frame can make a verifier look wrong even if the reliability
framework is sound.

Therefore the first gate is not metric execution. It is coordinate-frame and
label-semantics validation.

## Promotion Gates

G0. Coordinate-frame and label-semantics audit

- Determine whether `left/right/front/behind` labels are stable under a known
  frame.
- Test scan/world axis, camera/viewpoint, and axis-flip hypotheses.
- Record ambiguous cases explicitly.

G1. Denominator and coverage audit

- Count GT rows, prediction rows, excluded rows, and covered rows.
- Preserve exact predicate-label recall; family grouping must not relax
  `left/right/front/behind` labels.

G2. Geometry status policy

- Define `satisfied`, `violated`, and `uncertain` rules.
- Add a wrong-frame or axis-flip control as a required control, not an optional
  extra.

G3. Calibration and counterfactuals

- Build train-dev calibration positives and counterfactual negatives without
  using held-out prediction failures.
- Freeze thresholds and calibrator files before held-out metrics.

G4. GT verifier evaluation and visual sanity check

- Run GT-positive/counterfactual verifier evaluation.
- Add a targeted visual sanity check for horizontal labels.

G5. Source-result metrics

- Run VL-SAT and Open3DSG metrics with `relative_horizontal` included.
- Report `R@K` and `Violation@K` together.

G6. Nontriviality controls

- Include geometry-only, shuffled-geometry, wrong-pair geometry, and
  wrong-frame/axis-flip geometry controls.
- Include distance-only only if it is a meaningful horizontal baseline.

G7. Bootstrap CI and failure analysis

- Run subgraph bootstrap CI at the same level as the current paper claim.
- Generate row-level failure analysis and qualitative cases.

## Pass / Fail Rule

Pass:

- The expanded family reaches the current H001 evidence standard and improves
  recall/violation tradeoff under a transparent coordinate-frame policy.

Partial:

- Metrics are promising but coordinate-frame ambiguity or visual audit remains
  unresolved. Keep as appendix evidence.

Fail:

- Frame semantics are too ambiguous or controls show a coordinate artifact.
  Keep the current paper claim unchanged and report the result as a limitation
  or future-work boundary.

## Immediate Next Step

The no-training, no-inference scope audit is complete under `scope_audit/`.
It records:

- GT denominator for `relative_horizontal`;
- label counts for `left`, `right`, `front`, and `behind`;
- available object-pair geometry fields;
- candidate coordinate-frame hypotheses;
- required controls and blockers before metric execution.

Scope audit result:

- status: `relative_horizontal_scope_audit_ready_no_metric_execution`
- current H001 denominator: 2,545 GT rows
- `relative_horizontal` denominator: 3,570 GT rows
- expanded candidate denominator: 6,115 / 7,505 GT rows, share 0.8148
- GT labels: `left` 1,132, `right` 1,132, `front` 653, `behind` 653
- source rows: VL-SAT 103,664, Open3DSG 76,400
- current verification status: unsupported for both sources
- coordinate-frame protocol: `coordinate_frame_protocol.md`
- coordinate audit: `coordinate_audit/`
- bucket inspection: `bucket_inspection/`

Coordinate audit result:

- status: `relative_horizontal_coordinate_audit_blocked_no_metric_execution`
- rows audited: 3,570 GT rows across 125 scans
- frames evaluated: 16 scan/world XY and room-PCA variants
- selected candidate frame: `scan_left_neg_x_front_neg_y`
- macro strict purity: 0.7725, below the predeclared 0.80 gate
- strict eligible share: 0.6403
- per-label strict purity: `left` 0.8005, `right` 0.8005, `front` 0.7445, `behind` 0.7445
- directed inverse-pair consistency: 3,570 / 3,570 = 1.0
- wrong-frame gap to the next best candidate: 0.1231

Interpretation:

- The family is not random noise: inverse consistency is perfect and the best
  scan-frame candidate is clearly better than wrong-frame controls.
- It is still not strong enough for main-claim promotion because the
  predeclared macro and front/behind purity gates fail narrowly.
- The current paper claim must stay scoped to `support_contact`, `proximity`,
  and `relative_vertical`.
- For reviewer defense, report the raw diagnostic evidence first: selected
  frame, per-label purity, inverse consistency, wrong-frame gap, and ambiguity
  buckets. The threshold is only a conservative non-promotion rule, not an
  official benchmark threshold and not the source of the scientific claim.

Bucket inspection result:

- status: `relative_horizontal_bucket_inspection_ready_no_metric_execution`
- output files: `bucket_inspection/{manifest.json,summary.json,examples.jsonl,report.md}`
- selected frame: `scan_left_neg_x_front_neg_y`
- inverse consistency: 1.0
- wrong-frame gap: 0.1231
- `front`/`behind` strict match:contradiction: 2.9143
- `front`/`behind` strict purity: 0.7445
- `front`/`behind` sign-only purity: 0.7491
- `left`/`right` strict purity: 0.8005
- `front`/`behind` ambiguity flags: `axis_margin_ambiguous` 230,
  `conflicting_axis_dominates` 430, `strong_projected_overlap` 44
- recommendation: `do_not_promote_relative_horizontal_to_main_claim`

Interpretation:

- The threshold-free evidence is meaningful enough to keep this as a disciplined
  appendix/limitation track: the selected frame is not arbitrary, inverse
  consistency is strong, and wrong-frame controls are worse.
- It is not strong enough to justify expanded-family paper metrics. The
  `front`/`behind` bucket still contains too many ambiguous or contradictory
  cases to define a reliable geometry-status policy without another targeted
  check.

Current AAAI-path decision:

- Stop here and use the result only as appendix/limitation or future-work
  evidence. This protects the main paper from a weak broader-coverage claim.
- Do not run full `relative_horizontal` VL-SAT/Open3DSG source metrics for the
  current AAAI path.
- The narrower `relative_lateral` policy-freeze artifact may proceed only as a
  separate expansion track. That follow-up train/dev gate and dev diagnosis are
  now complete, and the current decision is also to stop `relative_lateral` as
  appendix/future-work boundary evidence.
- If the paper strategy later pivots to broader spatial-family coverage, the
  next required step is a targeted `front`/`behind` visual/frame-metadata check,
  followed by verifier policy, calibration, source metrics, controls, bootstrap
  CI, and failure/audit evidence at the current H001 standard.
