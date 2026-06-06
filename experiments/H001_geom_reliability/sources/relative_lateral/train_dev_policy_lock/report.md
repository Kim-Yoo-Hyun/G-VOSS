# Relative Lateral Train/Dev Policy Lock

Status: `relative_lateral_train_dev_policy_lock_ready_with_caveats_no_source_metrics`
Created at: `2026-06-06T07:57:19.999372+00:00`

## Claim Boundary

This artifact locks relative-lateral policy/calibration provenance on
train/dev GT annotations only. It does not use source prediction rows,
does not compute VL-SAT/Open3DSG metrics, and does not change the paper
claim.

## Policy Evaluation

| Split | Row type | Rows | Status counts | Strict purity | Lenient rate |
|---|---|---:|---|---:|---:|
| train | gt_positive | 1538 | `{"satisfied": 886, "uncertain": 524, "violated": 128}` | 0.8738 | 0.9168 |
| train | label_flip_counterfactual | 1538 | `{"satisfied": 128, "uncertain": 524, "violated": 886}` | 0.8738 | 0.9168 |
| dev | gt_positive | 378 | `{"satisfied": 166, "uncertain": 140, "violated": 72}` | 0.6975 | 0.8095 |
| dev | label_flip_counterfactual | 378 | `{"satisfied": 72, "uncertain": 140, "violated": 166}` | 0.6975 | 0.8095 |

## Calibration

| Split | Rows | Brier | NLL | ECE-10 | AUROC |
|---|---:|---:|---:|---:|---:|
| train | 3076 | 0.1295 | 0.4252 | 0.0678 | 0.8913 |
| dev | 756 | 0.2164 | 0.6784 | 0.1687 | 0.7401 |

## Gate

- passed: `false`
- blocker: `dev_positive_strict_purity_ge_0_80`
- blocker: `dev_counterfactual_strict_negative_purity_ge_0_80`

## Next

The dev strict policy gate did not pass. Do not run paper-facing
VL-SAT/Open3DSG lateral source metrics from this artifact yet unless
the result is explicitly kept as caveated appendix evidence.
The next technical step is to diagnose dev strict contradictions and
uncertain rows without changing the validation policy.
