# H001 Low-K Sweep Protocol

Status: `frozen_before_low_k_metric_execution`

Last updated: `2026-06-13 KST`

## Role

This artifact freezes a low-K top-rank reliability diagnostic for the existing
H001 full-validation sources. It does not replace the current main
R@50/R@100 and Violation@50/Violation@100 protocol unless the result is
reviewed and explicitly promoted later.

## Fixed K Grid

- Paper-metric candidate grid: `K = {5, 10, 20, 50, 100}`.
- `K=1` is excluded from paper-metric consideration because it is too noisy and
  too sensitive to scan/source-specific ranking artifacts. It may only be used
  as a sanity check if needed.
- `K=50` and `K=100` must exactly match the locked full-validation metric
  outputs before any low-K interpretation is accepted.

## Inputs

- VL-SAT full-validation source:
  `experiments/H001_geom_reliability/sources/vlsat/full_validation/`
- Open3DSG full-validation recovery source:
  `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/`

The sweep reuses existing Docker-generated row-level artifacts:

- `adapter/predictions.jsonl`
- `adapter/ground_truth.jsonl` for VL-SAT full-validation GT
- `geometry/verification.jsonl`
- locked `metrics/metrics.json` for K=50/100 consistency checks

## Outputs

Low-K outputs must be written to separate diagnostic roots and must not
overwrite the locked main outputs:

- `metrics_k_sweep/`
- `bootstrap_ci_k_sweep/`
- `experiments/H001_geom_reliability/k_sweep/`

## Promotion Gate

Low-K results may be considered for main-result reflection only if:

- K=10 and K=20 show consistent Violation@K reduction on both VL-SAT and
  Open3DSG recovery.
- Recall does not collapse; operationally, delta R@K versus semantic-only must
  be no worse than -5 percentage points on both sources for the candidate
  condition.
- Open3DSG recovery bootstrap CI supports the direction of the effect.
- VL-SAT is interpreted with ceiling effects in mind: recall deltas may be
  small, but violation trends must remain consistent.
- A K=5-only improvement is treated as insufficient for main-result promotion.

## Claim Boundary

This diagnostic evaluates whether calibrated geometry-consistency re-ranking
changes the top-ranked relation region more clearly than the current standard
K=50/100 table. It is not a new semantic source, a new relation family, or a
new broad open-vocabulary 3DSSG improvement claim.
