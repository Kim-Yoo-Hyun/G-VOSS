# Score Robustness and Simple Baselines

This folder owns the frozen post-hoc experiments requested for reviewer risks
P0-1 and P0-2. It uses the active `no_family_indicator_v1` candidate pool,
model locks, family-slot route, exact-label denominator, five reported values of
K, and scan-cluster bootstrap protocol.

## P0-1: source-score mapping sensitivity

The frozen grid contains Identity, power mappings with gamma 0.5, 2, and 4,
logit-temperature mappings with temperature 0.5 and 2, and a within-context,
within-family percentile mapping. Linear and MLP compatibility are evaluated
under every mapping. No mapping is selected from evaluation results.
The logit-temperature functions are used only as monotonic scale stresses.
They do not treat the Open3DSG cosine score as a calibrated probability.

Outputs record Recall, primary and decidable Violation, uncertainty, coverage,
selected count, paired scan-cluster intervals, top-K Jaccard overlap, and
Kendall rank correlation.

## P0-2: closest simple baselines

- `hard_tail` places verifier-violated candidates after non-violated candidates
  inside each re-ranked family.
- `hard_drop` removes every verifier-violated candidate, retains source order
  among the remaining candidates, and records the selected count.
- `positive_density` is a non-learned continuous baseline fitted from
  training-split positive geometry only. It uses fixed relation-aware features,
  predicate medians and IQRs, transformation averaging, product fusion, and the
  active family-slot route.

The density fit uses 14,618 training-positive rows: 11,340 proximity rows and
1,639 rows for each vertical predicate. No required feature cell is missing.

Hard-tail and Hard-drop read evaluation-verifier labels. They are upper
diagnostics and are not deployable comparators. Positive-density is the closest
training-derived simple comparator.

## Canonical gate

The archived Tier-B inputs are referenced in place to avoid duplicating roughly
10 GB of row data. Every input is hash-locked. The evaluator must reproduce the
active Source, RelCompat3D-Linear, and RelCompat3D-MLP point estimates exactly
before its robustness results are accepted.

## Run record

- Final Docker run: 2026-07-27 KST
- Local ignored log:
  `logs/relcompat3d_score_robustness_20260727_002945.log`
- Exit code: 0
- Evaluation manifest SHA-256:
  `57780a58173759b03f784549c2ea0213c9cfdbd5c633863ff7dbd977f8dd3548`

## Docker command

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_score_robustness
```

Expected outputs are written to `evaluation/`:

- `summary.json` and `summary.md`
- `canonical_validation.csv`
- `score_mapping.csv`
- `simple_baselines.csv`
- `rank_stability.csv`
- `density_stats.json`
- `manifest.json`

## Results

All manifest validations pass. The Docker rerun reproduces the 90 canonical
Source, RelCompat3D-Linear, and RelCompat3D-MLP Recall/Violation cells exactly
with zero numerical error.

### P0-1

Five smooth non-identity mappings are evaluated for each estimator: three
power mappings and two logit-temperature mappings. Across the resulting 75
predictor--K conditions, Linear retains a Recall point estimate no lower than
Source and a Violation point estimate no higher than Source in 75/75
conditions. MLP does so in 74/75 conditions. Its only exception is VL-SAT at
\(K=50\) under power 4, where Recall changes by \(-0.025\) percentage points
and the paired interval includes zero, while Violation decreases.

The context-and-family percentile condition exposes limited scale dependence.
Linear loses 0.227 and 0.151 Recall points on SGFN at \(K=10\) and \(K=20\),
respectively. MLP has four losses no larger than 0.201 points. Violation does
not increase in any tested mapping condition. These findings support
robustness over the fixed smooth grid, not score-scale invariance.
Across the full grid including percentile, the minimum pair-weighted Kendall
correlation with the identity product ranking is 0.810 and the minimum
\(K=50\) micro-Jaccard overlap is 0.815.

### P0-2

At \(K=50\), both learned variants Pareto-dominate the training-positive
Positive-density baseline for all three predictors. Across all 15
predictor--K conditions, Linear dominates Positive-density in 12 and has a
Recall--Violation trade-off in three. MLP dominates it in 12, has a trade-off
in two, and is dominated only for Open3DSG at \(K=5\).

| Predictor | Source R/V | Positive-density R/V | Linear R/V | MLP R/V |
| --- | ---: | ---: | ---: | ---: |
| VL-SAT | 92.72 / 2.68 | 91.77 / 2.68 | 92.77 / 1.97 | 92.72 / 1.89 |
| Open3DSG | 40.43 / 13.87 | 43.76 / 5.09 | 44.18 / 3.42 | 46.70 / 4.13 |
| SGFN | 74.02 / 3.85 | 73.87 / 4.01 | 74.50 / 2.63 | 74.57 / 2.58 |

The table reports percentages at \(K=50\).

Hard-tail and Hard-drop are not fair deployable baselines because they read
the evaluation-verifier output. Hard-tail often reaches a lower Violation
point at the cost of Recall. Hard-drop yields zero primary Violation by
construction and can return fewer than \(K\) candidates. They are retained as
direct-verifier diagnostics, not evidence of learned-estimator superiority.

The canonical compact values and all paired intervals are in
`evaluation/score_mapping.csv` and `evaluation/simple_baselines.csv`.
`evaluation/rank_stability.csv` records Kendall correlation and top-\(K\)
Jaccard overlap. `evaluation/manifest.json` locks the inputs, outputs, Docker
command, validations, and interpretation boundary.

## User action

No intervention is needed to rerun or verify the experiment while the local
archive remains available. The remaining author decision is presentation:
add a short main-paper pointer and place the full mapping and baseline tables
in the supplement, or keep the entire analysis in the supplement. The active
method and Table 1 must not be changed from this post-hoc analysis.
