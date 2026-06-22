# H001_v2 Dataset And Artifact Contract

Last updated: 2026-06-22 KST

## Boundary

H001_v2 is allowed to read existing H001 artifacts, but it must write new
outputs under a separate H001_v2 root. It must not overwrite H001_v1 metrics,
tables, paper source, or release bundles.

## Read-Only Inputs

Allowed input categories:

- H001 prediction JSONL.
- H001 ground-truth JSONL.
- H001 geometry verification JSONL.
- H001 `p_geom_valid` calibration outputs.
- H001 train/train-dev calibration rows.
- H001 source metrics only for baseline comparison after the H001_v2 protocol is frozen.

Disallowed input usage:

- selecting `alpha`, `delta`, `tau_grid`, or `tau*` from full-validation source
  metrics.
- choosing a source-specific threshold after seeing VL-SAT/Open3DSG results.
- modifying existing H001 metric JSON files.
- modifying H001 paper tables or manuscript text from this branch.

## Calibration Split

Primary calibration provenance source:

```text
archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/train_dev_calib/
```

Primary threshold-selection source:

```text
archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_smoke/scores.jsonl
```

using only:

```text
role == "dev"
```

The source inventory and schema probe record the exact files, row counts, and
available fields. They must record:

- calibration row path.
- scan split files.
- positive/counterfactual label provenance.
- available geometry features.
- available `p_geom_valid` field.
- status/violation label source.

`train_dev_calib/table.jsonl` must not be used alone for threshold selection,
because it has `label.geom_valid` but not deployable `p_geom_valid` or source
semantic ranking fields.

## Source Evaluation Inputs

Candidate source evaluation roots:

```text
experiments/H001_geom_reliability/sources/vlsat/full_validation/
experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/
```

These are read-only inputs. H001_v2 output must be written elsewhere.

## Output Root

Proposed output root:

```text
hypothesis/CAND-001/H001_v2_risk_controlled_reranking/artifacts/
```

Do not use `results/h001_geom_reliability/` until the user explicitly promotes
H001_v2 from hypothesis to paper-facing experiment.

## Required H001_v2 Outputs

Before any source metric claim:

```text
05_source_inventory.md
06_schema_probe.md
artifacts/calibration_threshold_selection/manifest.json
artifacts/calibration_threshold_selection/selection_curve.jsonl
artifacts/calibration_threshold_selection/thresholds.json
artifacts/calibration_threshold_selection/report.md
```

After source evaluation is explicitly approved:

```text
artifacts/source_eval/<source_id>/metrics.json
artifacts/source_eval/<source_id>/report.md
artifacts/source_eval/<source_id>/selected_predictions.jsonl
```

## Minimum Source Inventory Fields

```text
source_id
split_role
predictions_jsonl
ground_truth_jsonl
verification_jsonl
metrics_json
allowed_read_purpose
must_not_modify
row_count_predictions
row_count_ground_truth
row_count_verification
in_scope_family_count
required_fields_present
hidden_or_forbidden_fields
```

## Implementation Gate

Implementation can start only after:

- this contract is accepted as the owning H001_v2 artifact boundary.
- source inventory is written.
- the calibration threshold rule is implemented as a no-source-eval dry run.
- validation checks confirm that the output root does not overlap H001_v1
  paper-facing result paths.
