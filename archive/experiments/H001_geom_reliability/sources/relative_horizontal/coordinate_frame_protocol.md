# Relative Horizontal Coordinate-Frame Protocol

Last updated: 2026-05-27 KST

Status: `protocol_frozen_no_metric_execution`

This file defines the next gate after `scope_audit/`. It does not implement a
verifier, does not run metrics, and does not change the current paper claim.

## Starting Point

The Docker scope audit found:

- current H001 denominator: 2,545 GT rows;
- `relative_horizontal` candidate denominator: 3,570 GT rows;
- expanded candidate denominator: 6,115 / 7,505 GT rows;
- labels: `left` 1,132, `right` 1,132, `front` 653, `behind` 653;
- source rows: VL-SAT 103,664 and Open3DSG 76,400;
- current verification status: unsupported for both sources.

The blocker is not row availability. The blocker is coordinate-frame semantics.

## Frame Hypotheses

H0. Scan/world XY frame

- `left/right/front/behind` are defined by signed object-center displacement in
  the reconstructed scan/world XY plane.
- Candidate evidence: `dx = center_x(subject) - center_x(object)`,
  `dy = center_y(subject) - center_y(object)`, normalized by pair scale.

H1. Axis-flipped or axis-swapped scan frame

- The dataset may use the opposite sign or swap horizontal axes.
- This is not a fallback to optimize metrics; it is a required control to test
  whether any apparent result is just a coordinate convention artifact.

H2. Room-layout principal frame

- `front/behind` or `left/right` may align better after estimating a dominant
  room axis from object centers or room geometry.
- This hypothesis is only usable if the frame is computed deterministically
  from the scene before held-out prediction metrics.

H3. Viewpoint or annotator frame

- Labels may be tied to a camera/viewpoint or annotation perspective rather
  than an allocentric scan frame.
- If this is the dominant hypothesis and no stable viewpoint metadata can be
  recovered, `relative_horizontal` should not be promoted.

H4. Object-centric frame

- Labels may depend on subject/object orientation.
- This is risky in 3RScan/3DSSG because reliable object yaw is not guaranteed
  for many indoor object categories. Treat this as a failure/limitation unless
  object orientation evidence is available.

## Required Tests

T1. GT sign-purity audit

- For each hypothesis, compute how often each GT label agrees with the expected
  signed axis relation.
- Report per-label purity for `left`, `right`, `front`, and `behind`.
- Report uncertain rows when axis displacement is below a predeclared margin.

T2. Directed inverse-pair consistency

- For GT rows where both directions are annotated, check:
  `left(s,o)` vs `right(o,s)` and `front(s,o)` vs `behind(o,s)`.
- Low inverse consistency means label semantics may not be a simple geometric
  frame relation.

T3. Wrong-frame / axis-flip control

- Compare the selected frame to swapped-axis and sign-flipped variants.
- A valid frame should outperform wrong-frame controls on GT verifier
  separation and later source-result metrics.

T4. Ambiguity bucket audit

- Rows with small horizontal displacement, strong overlap, or conflicting axes
  must be marked `uncertain`, not forced into satisfied/violated.
- The uncertainty policy must be fixed before held-out source metrics.

T5. Visual sanity check

- Build a balanced small queue across four labels and status buckets.
- Use it only as sanity/failure-mechanism evidence, not as primary metric
  evidence.

## Provisional Promotion Thresholds

These thresholds are predeclared gate criteria, not final metric claims:

- macro GT sign-purity at least 0.80 under one deterministic frame;
- no individual label below 0.75 sign-purity unless routed to `uncertain`;
- inverse-pair consistency at least 0.85 when inverse annotations exist;
- wrong-frame / axis-flip controls must be clearly worse than the selected
  frame;
- visual sanity contradiction rate at most 0.10 on the balanced check;
- exact predicate-label recall must remain exact for `left`, `right`, `front`,
  and `behind`.

If these thresholds are not met, keep `relative_horizontal` out of the main
claim and report it as unresolved coordinate-frame scope.

## Metric Promotion Rule

Only after the coordinate-frame gate passes:

1. Implement a deterministic `relative_horizontal` verifier with
   `satisfied`, `violated`, and `uncertain` status.
2. Build train-dev calibration positives and counterfactual negatives without
   using held-out prediction failures.
3. Run GT verifier evaluation.
4. Run VL-SAT and Open3DSG expanded-family metrics.
5. Run geometry-only, shuffled-geometry, wrong-pair, and wrong-frame controls.
6. Run bootstrap CI and failure analysis.

Until all six steps pass, the current three-family paper claim remains
unchanged.
