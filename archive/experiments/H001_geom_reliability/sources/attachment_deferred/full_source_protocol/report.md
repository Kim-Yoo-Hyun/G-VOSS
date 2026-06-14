# Attachment Deferred Full-Source Protocol

Status: `attachment_deferred_full_source_protocol_frozen_no_metrics`
Created at: `2026-05-28T07:15:17+00:00`

## Claim Boundary

This is a G5c protocol freeze only. It does not run full-source scoring,
R@K, Violation@K, controls, bootstrap CI, source metrics, or main-claim
promotion. The current AAAI claim remains unchanged.

## Denominator Policy

- global attachment exact-label GT denominator: `967`
- primary recall denominator: source-specific covered exact-label GT rows
- exact predicate-label matching: required
- source comparison: requires coverage caveat

## Source Coverage

- `open3dsg_ov`: covered `768`, missing `199`, coverage `0.7942`
- `vlsat_closed_set`: covered `967`, missing `0`, coverage `1.0000`

## Sharding

- shard count: `69`
- expected full-source rows: `135048`
- rows per shard: `2000`

## Required Metric Conditions

- `semantic_only`
- `probabilistic_recalibrated`
- `rule_verified_attachment_policy`
- `control_p_geom_valid_only`
- `control_distance_only`
- `control_shuffled_geometry`
- `control_wrong_pair_geometry`

## Known Caveat

`connected to` has no dev strict rows in G4c. The frozen protocol allows
pooled scoring but forbids a label-specific connected-to calibration claim
unless future train/dev evidence is added before source metrics.

## Next Gate

`G5d_attachment_full_source_scoring_metrics_controls`
