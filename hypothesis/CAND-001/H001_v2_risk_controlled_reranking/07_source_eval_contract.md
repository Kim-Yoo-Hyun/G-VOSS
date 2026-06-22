# H001_v2 Source Evaluation Contract

Last updated: 2026-06-22 KST

This file freezes the first source-evaluation contract for H001_v2. It does
not report source metrics. It defines how the fixed calibration-selected
threshold will be applied to VL-SAT and Open3DSG without changing H001 locked
artifacts.

## Status

- Contract status: `frozen_for_implementation`
- First implementation route: hypothesis runner under `src/geocalib/`
- Docker route: deferred until H001_v2 point metrics are worth promoting
- Source metric execution: allowed only under the H001_v2 artifact root

Rationale:

- A small hypothesis runner is enough to validate the fixed-threshold semantics.
- Docker promotion should happen only if the H001_v2 result becomes a candidate
  paper-facing experiment.
- Existing H001 `metrics/`, `bootstrap_ci/`, source roots, paper tables, and
  result bundles remain read-only.

## Fixed Policy Input

Policy file:

```text
hypothesis/CAND-001/H001_v2_risk_controlled_reranking/artifacts/calibration_threshold_selection/thresholds.json
```

Frozen primary policy:

```text
tau* = 0.20
p_geom_valid_threshold = 0.80
alpha = 0.05
delta = 0.05
```

This threshold was selected on held-out calibration rows only. It must not be
changed after reading VL-SAT or Open3DSG metrics.

## Source Inputs

VL-SAT:

```text
predictions_jsonl = experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/predictions.jsonl
ground_truth_jsonl = experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl
verification_jsonl = experiments/H001_geom_reliability/sources/vlsat/full_validation/geometry/verification.jsonl
```

Open3DSG:

```text
predictions_jsonl = experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/adapter/predictions.jsonl
ground_truth_jsonl = experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl
verification_jsonl = experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/geometry/verification.jsonl
```

Open3DSG uses the same full-validation H001 ground-truth denominator as the
current H001 source metrics.

## Fixed Evaluation Grid

Families:

```text
support_contact
proximity
relative_vertical
```

K values:

```text
K = {5, 10, 20, 50, 100}
```

Primary source conditions:

| Condition | Definition |
| --- | --- |
| `semantic_only` | Original source semantic ranking. |
| `probabilistic_recalibrated` | H001_v1 score, `semantic_score * p_geom_valid`. |
| `rule_verified_point_subtype` | Existing H001 filter-safe point-subtype verifier condition. |
| `h001_v2_risk_controlled_pooled_tau` | Keep only in-scope rows with `calibration.p_geom_valid >= 0.80`, then rank by original semantic score. |

Required optional controls after the primary condition is implemented:

| Condition | Definition |
| --- | --- |
| `control_p_geom_valid_only` | Existing H001 p-geom-only control. |
| `control_shuffled_geometry_tau` | Apply the same `0.80` threshold to deterministic shuffled-family donor p-geom values. |
| `control_wrong_pair_geometry_tau` | Apply the same `0.80` threshold to deterministic wrong-pair donor p-geom values. |

The first point-metric implementation may omit the optional H001_v2 controls,
but the controls are required before any method-promotion claim.

## H001_v2 Selection Semantics

For each prediction row `e`:

```text
in_scope(e) = predicate_family(e) in {support_contact, proximity, relative_vertical}
p(e) = verification[e.prediction_id].calibration.p_geom_valid
eligible(e) = in_scope(e) and p(e) >= 0.80
utility(e) = original semantic ranking score
```

For each subgraph and each K:

```text
TopK_H001_v2(g, K) = first K eligible rows in g sorted by utility(e)
```

Important constraints:

- Do not multiply semantic score by `p_geom_valid` in H001_v2.
- Do not use `verification_status` to decide eligibility.
- Do not use source `Violation@K`, `R@K`, or selected-count results to change
  the threshold.
- If fewer than K rows are eligible in a subgraph, select fewer and report this
  as selected-count reduction.

## Required Metrics

For every source and every condition:

- `R@5`, `R@10`, `R@20`, `R@50`, `R@100`
- `Violation@5`, `Violation@10`, `Violation@20`, `Violation@50`, `Violation@100`
- selected prediction count at each K
- geometry coverage at each K
- in-scope input rows
- eligible rows for H001_v2
- threshold-excluded rows for H001_v2
- missing verification rows
- missing `p_geom_valid` rows

Required deltas:

- H001_v2 minus `semantic_only`: `Delta R@K`, `Delta Violation@K`
- H001_v2 minus `probabilistic_recalibrated`: `Delta R@K`,
  `Delta Violation@K`

Recall and violation deltas must be reported together. A violation reduction
with hidden selected-count or recall collapse is not promotable.

## Output Root

All source-eval outputs must be written under:

```text
hypothesis/CAND-001/H001_v2_risk_controlled_reranking/artifacts/source_eval/
```

Per-source output directories:

```text
artifacts/source_eval/vlsat_full_validation/
artifacts/source_eval/open3dsg_recovery_relaxed_views_min2/
```

Required files:

| File | Role |
| --- | --- |
| `manifest.json` | source id, command, input paths, threshold file, code path, and status |
| `metrics.json` | source metric table and deltas |
| `report.md` | human-readable source-eval summary |
| `selected_predictions.jsonl` | selected H001_v2 rows with selection rank and threshold metadata |
| `selection_summary.json` | selected/excluded/missing counts by source, K, family, and subgraph |
| `commands.md` | exact commands used |

Do not write source-eval outputs under:

- `experiments/H001_geom_reliability/sources/**/metrics/`
- `experiments/H001_geom_reliability/sources/**/bootstrap_ci/`
- `results/h001_geom_reliability/`
- `paper/`

## No-Overwrite Guard

The source-eval runner must fail before writing if `--output-dir` is under any
read-only H001 source root or paper/result root.

The runner must also fail on a non-empty H001_v2 output directory unless an
explicit `--overwrite` flag is provided.

Read-only roots:

```text
experiments/H001_geom_reliability/sources/vlsat/full_validation/
experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/
archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/
results/h001_geom_reliability/
paper/
```

## Proposed Commands

These commands are the implementation target. They should not be run until the
source-eval runner exists.

VL-SAT:

```bash
PYTHONPATH=src/geocalib python src/geocalib/evaluate_h001_v2_source.py \
  --source-id vlsat_full_validation \
  --predictions-jsonl experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/predictions.jsonl \
  --ground-truth-jsonl experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl \
  --verification-jsonl experiments/H001_geom_reliability/sources/vlsat/full_validation/geometry/verification.jsonl \
  --thresholds-json hypothesis/CAND-001/H001_v2_risk_controlled_reranking/artifacts/calibration_threshold_selection/thresholds.json \
  --output-dir hypothesis/CAND-001/H001_v2_risk_controlled_reranking/artifacts/source_eval/vlsat_full_validation \
  --ks 5 10 20 50 100
```

Open3DSG:

```bash
PYTHONPATH=src/geocalib python src/geocalib/evaluate_h001_v2_source.py \
  --source-id open3dsg_recovery_relaxed_views_min2 \
  --predictions-jsonl experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/adapter/predictions.jsonl \
  --ground-truth-jsonl experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl \
  --verification-jsonl experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/geometry/verification.jsonl \
  --thresholds-json hypothesis/CAND-001/H001_v2_risk_controlled_reranking/artifacts/calibration_threshold_selection/thresholds.json \
  --output-dir hypothesis/CAND-001/H001_v2_risk_controlled_reranking/artifacts/source_eval/open3dsg_recovery_relaxed_views_min2 \
  --ks 5 10 20 50 100
```

## Promotion Gate

H001_v2 source metrics are hypothesis evidence until all of the following are
true:

- both source point metrics are generated from the fixed threshold;
- selected-count and coverage loss are reported;
- fixed-threshold bootstrap CI is added without reselecting `tau*`;
- shuffled/wrong-pair threshold controls are run;
- the user explicitly approves promotion to paper-facing H001/GeoCalib tables.
