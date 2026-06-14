# H002 Train RGA Seed

Last updated: 2026-06-12

## Purpose

`16_train_scope.md`에서 H002 hypothesis-stage diagnostics must use train-set
artifacts라는 기준을 고정했다. 이번 문서는 첫 train-set RGA diagnostic route를
선택한다.

## Current Constraint

현재 H002의 `14_lh_diagnostic.md`와 `15_lh_audit.md`는 H001 `full_validation`
artifacts에서 생성되었다. 따라서 hypothesis evidence가 아니라 workflow feasibility
evidence다.

Train-set RGA를 위해서는 semantic rank와 geometry verification이 같은 prediction
row에 있어야 한다.

Required bundle:

```text
train_predictions.jsonl
train_ground_truth.jsonl
train_geometry/verification.jsonl
train_failure_rows/rows.jsonl or equivalent match-status join
train_manifest.json
```

## Candidate Routes

### Route A: Train/Dev Geometry Calibration Table

Available:

```text
hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/train_dev_calib/table.jsonl
hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/train_dev_calib/negatives.jsonl
```

Pros:

- already train/dev scoped.
- geometry-positive and counterfactual-negative rows exist.
- useful for `p_geom_valid` calibration and geometry-only baseline.

Blocker:

- semantic scores/ranks are null.
- cannot compute `RGA-HL` or `RGA-LH`.

Verdict:

```text
not sufficient as the first RGA seed
```

Use later for geometry calibration/baseline, not for semantic-geometric
mismatch diagnostics.

### Route B: VL-SAT Train Source

Available:

```text
experiments/H001_geom_reliability/sources/vlsat/full_validation/
```

No ready train-set `predictions.jsonl + verification.jsonl + ground_truth.jsonl`
bundle was found under:

```text
experiments/H001_geom_reliability/sources/vlsat/
```

Verdict:

```text
defer until a train runtime/export path is identified
```

VL-SAT remains attractive because H001 already uses it as a strong closed-set
source, but the immediate execution gap is larger than Open3DSG train source.

### Route C: Open3DSG Train Source

Available train-side artifacts:

| Artifact | Status |
| --- | --- |
| `experiments/H001_geom_reliability/sources/open3dsg/train_views/manifest.json` | `views_ready` |
| `experiments/H001_geom_reliability/sources/open3dsg/train_preprocess/manifest.json` | `preprocess_partial_ready` |
| selected trained checkpoint | available from H001 Open3DSG training route |

Known counts:

| Item | Count |
| --- | ---: |
| train ready scans with views | 1,178 |
| train preprocess ready subgraphs | 3,744 |
| train preprocess missing subgraphs | 108 |

Missing for H002:

- train raw dump.
- train adapter `predictions.jsonl`.
- train geometry verification join.
- train match-status/failure rows.

Verdict:

```text
selected first route
```

Reason:

- it already has train split preprocessing/views and a selected checkpoint route.
- missing pieces are downstream source-export/join artifacts, not training data
  discovery.
- the route can start with a bounded train pilot instead of full 3,744 subgraphs.

## Selected Seed Scope

Selected first seed:

```text
Open3DSG train pilot RGA seed
```

Scope:

- train split only.
- bounded pilot subset before full train source export.
- no validation artifact in source selection, threshold selection, or manual audit.

Minimum pilot target:

```text
>= 100 train subgraphs if runtime is cheap enough
otherwise >= 32 train subgraphs as a smoke seed
```

Selection rule:

- use train preprocessed subgraphs only.
- preserve source identity fields.
- include all H001-supported relation families:
  - `proximity`
  - `relative_vertical`
  - `support_contact`
- retain unsupported rows for coverage accounting, but do not use them in
  geometry-checkable denominators.

## Expected Outputs

New H002 artifacts should be written under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/
```

Required outputs:

```text
source_manifest.json
train_predictions.jsonl
train_ground_truth.jsonl
train_geometry/verification.jsonl
train_rga_summary.json
train_lh_queue.jsonl
train_hl_queue.jsonl
report.md
```

If source generation must reuse Docker/H001 source scripts, the generated raw
source artifacts may live under `experiments/H001_geom_reliability/`, but H002
must record read-only provenance and must not overwrite existing H001 validation
artifacts.

## Baseline Implication

`p_geom_valid` remains geometry-only.

The train seed should only report diagnostic summaries first. Do not fit or
compare the full factorized posterior until the train source bundle exists.

Baseline contract order:

1. confirm train semantic-only rank field.
2. confirm train `p_geom_valid` coverage.
3. compute train `semantic + geometry` simple fusion.
4. only then define factorized reliability posterior inputs.

## Next TODO

Next document:

```text
18_train_source_contract.md
```

Required next work:

- Define exact train source contract for the Open3DSG train pilot.
- Identify or write the minimal command sequence to produce train raw dump,
  adapter predictions, geometry verification, and match-status rows.
- Freeze pilot subset selection before running source export.
- Record expected runtime, output paths, and verification commands.
