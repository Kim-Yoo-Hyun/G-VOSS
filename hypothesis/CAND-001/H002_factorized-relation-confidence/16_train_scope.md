# H002 Train Scope

Last updated: 2026-06-12

## Purpose

H002 hypothesis-stage diagnostics must be performed on train-set artifacts.
Validation or held-out artifacts should be reserved for final confirmation after
the hypothesis, metric contract, baseline contract, and audit taxonomy are fixed.

This document corrects the current H002 evidence boundary.

## Correction

The following H002 documents were built from H001 `full_validation` artifacts:

- `14_lh_diagnostic.md`
- `15_lh_audit.md`

They are now treated as held-out workflow diagnostics only.

Allowed use:

- check that the RGA-HL/RGA-LH projection code works.
- check that visual/contact-sheet audit packaging is feasible.
- identify likely field/schema requirements for a train-set rerun.

Blocked use:

- hypothesis selection.
- threshold choice.
- model-design decision.
- baseline comparison.
- paper claim.
- deciding whether H002 should continue or stop.

## Available Train-Side Artifacts

### Geometry Calibration

Ready train/dev calibration artifacts exist:

```text
hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/train_dev_calib/table.jsonl
hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/train_dev_calib/negatives.jsonl
hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/train_dev_calib/manifest.json
hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/train_dev_payload/manifest.json
```

Current counts:

| Artifact | Rows |
| --- | ---: |
| `train_dev_calib/table.jsonl` | 5,809 |
| `train_dev_calib/negatives.jsonl` | 3,244 |

These artifacts can support geometry calibration and counterfactual geometry
checks, but they do not provide source semantic ranks for RGA-HL/RGA-LH.

Important manifest boundary:

```text
Semantic scores remain null until the prediction adapter exists.
```

### VL-SAT

Ready H001 experiment artifacts currently found for VL-SAT are under:

```text
experiments/H001_geom_reliability/sources/vlsat/full_validation/
```

No ready train-set `predictions.jsonl + verification.jsonl + ground_truth.jsonl`
bundle was found under `experiments/H001_geom_reliability/sources/vlsat/`.

Older H001 hypothesis artifacts exist under:

```text
hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/evaluation/vlsat_closed_set/hardened/
hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/evaluation/vlsat_closed_set/hardened_geometry/
```

But their manifests mark them as held-out/smoke validation data, not calibration
train data. They must not be used for H002 hypothesis selection.

### Open3DSG

Train-side preprocessing and views exist:

| Artifact | Status |
| --- | --- |
| `experiments/H001_geom_reliability/sources/open3dsg/train_views/manifest.json` | `views_ready` |
| `experiments/H001_geom_reliability/sources/open3dsg/train_preprocess/manifest.json` | `preprocess_partial_ready` |

Key counts:

| Item | Count |
| --- | ---: |
| train ready scans with views | 1,178 |
| train preprocess total subgraphs | 3,852 |
| train preprocess ready subgraphs | 3,744 |
| train preprocess missing subgraphs | 108 |

No ready train-set Open3DSG adapter prediction file or geometry verification file
was found.

## Required Train Bundle

H002 train diagnostics require the following source bundle:

```text
train_predictions.jsonl
train_ground_truth.jsonl
train_geometry/verification.jsonl
train_failure_rows/rows.jsonl or equivalent match-status join
train_manifest.json
```

Minimum required fields:

- `prediction_id`
- `scan_id`
- `subgraph_id`
- `subject_id`
- `object_id`
- `predicate_label`
- `predicate_family`
- semantic score or rank
- `verification_status`
- `p_geom_valid`
- match status against train GT

Without semantic rank, H002 cannot compute `RGA-HL` or `RGA-LH`.

## Updated Evidence Policy

H002 evidence order:

1. Train-set diagnostic:
   - define RGA buckets.
   - inspect train RGA-HL/RGA-LH distributions.
   - select audit taxonomy.
   - design factorized posterior and baseline contract.
2. Train/dev internal check:
   - fit/calibrate only on train or train-dev as appropriate.
   - run ablations and threshold sensitivity.
3. Validation confirmation:
   - use H001 `full_validation` only after the train-stage choices are frozen.

The existing `14_lh_diagnostic.md` and `15_lh_audit.md` can be reused as a
template for the validation confirmation stage, not as current hypothesis
evidence.

## Baseline Boundary

`p_geom_valid` remains the geometry-only calibrated validity proxy.

Core scoring conditions stay:

1. `semantic-only`
2. `geometry-only` = `p_geom_valid`
3. `semantic + geometry`
4. `factorized reliability posterior`

But all design choices for these conditions must be fixed using train-set or
train-dev evidence before any validation-set confirmation.

## Current Decision

Current H002 status:

```text
train_scope_required_before_manual_lh_review
```

Do not proceed to `16_lh_manual_review.md` on the current validation-derived LH
queue.

## Next TODO

Next document:

```text
17_train_rga_seed.md
```

Required next work:

- Choose the first train-set source route.
- Prefer the route with the smallest missing execution gap.
- Build or locate train-set predictions, GT, geometry verification, and match
  rows.
- Re-run `RGA-HL/RGA-LH` diagnostics on train artifacts only.
- Only after train RGA diagnostics are ready, create train-side visual/audit
  queues.
