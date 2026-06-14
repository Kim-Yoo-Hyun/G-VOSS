# Attachment Deferred Source Scoring Preflight

Status: `attachment_deferred_source_scoring_preflight_ready_no_metrics`
Created at: `2026-05-28T06:57:59+00:00`

## Claim Boundary

This is a bounded source evidence extraction and p_geom scoring preflight.
It does not compute source metrics, controls, bootstrap CI, or update the
current AAAI main claim.

## Counts

- selected source rows: `120`
- evidence rows: `120`
- scored rows: `120`
- validation errors: `0`

## Source Counts

- `open3dsg_ov`: 60
- `vlsat_closed_set`: 60

## Selection

- max rows per source/label: `20`
- VL-SAT attachment rows seen: `77748`
- VL-SAT selected unique scans: `20`
- Open3DSG attachment rows seen: `57300`
- Open3DSG selected unique scans: `20`

## Score Distribution

- mean p_geom_valid: `0.36097181955688334`
- median p_geom_valid: `0.057955692988128193`
- min/max p_geom_valid: `7.146309812314544e-05` / `0.9998720121538349`

## Warnings

- none

## Next Gate

`G5c_attachment_full_source_scoring_or_metric_protocol_freeze`
