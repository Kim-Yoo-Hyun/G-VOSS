# Attachment Deferred Calibration Fit

Status: `attachment_deferred_calibration_fit_ready_no_source_metrics`
Created at: `2026-05-28T06:26:40+00:00`
Model id: `h001-attachment-deferred-p-geom-valid-strict-v1`

## Claim Boundary

This fits a pooled attachment-deferred calibration model from the G4c
strict-only filter. It does not score source predictions, compute source
metrics, run controls/bootstrap, or change the current AAAI main claim.

## Counts

- train rows: `242`
- dev rows: `83`
- train positives/negatives: `94` / `148`
- dev positives/negatives: `27` / `56`

## Dev Metrics

- Brier: `0.0010268071750410028`
- NLL: `0.0077383149722480785`
- ECE: `0.007145890189565561`
- AUROC(valid): `1.0`
- AUPRC(valid): `1.0`

## Baselines

- constant_train_prior dev Brier/NLL/ECE: `0.22346554443990024` / `0.6393853592641501` / `0.06312854724683903`
- label_train_prior dev Brier/NLL/ECE: `0.21944941347761043` / `0.6304310291216844` / `0.032521262301397846`

## Train Metrics

- train Brier/NLL/ECE: `9.70302517963579e-05` / `0.0024022348732642335` / `0.002349785618746308`

## Warnings

- `connected_to_dev_absent_use_pooled_or_train_only_caveat`
- `strict_subset_nearly_separable_not_source_metric_evidence`

## Next Gate

Use this fitted model to score attachment-deferred VL-SAT/Open3DSG source
rows only after source evidence extraction is available. Then run source
metrics and controls. Main AAAI claim promotion still requires explicit
final user confirmation.
