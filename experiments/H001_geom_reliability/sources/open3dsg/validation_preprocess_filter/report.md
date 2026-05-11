# Open3DSG Validation Preprocess Filter

Created at: `2026-05-08T01:31:33.897512+00:00`
Status: `filter_applied`
Applied: `True`

## Counts

- original validation subgraphs: `160`
- kept validation subgraphs: `156`
- removed validation subgraphs: `4`
- original validation scans: `30`
- kept validation scans: `30`
- removed-only scans: `0`
- original relation annotations: `3749`
- kept relation annotations: `3696`
- removed relation annotations: `53`

## Recoverability Check

- full preprocess missing rows: `4`
- `too few visible objects` log count: `None`
- retry manifest: `experiments/H001_geom_reliability/sources/open3dsg/validation_preprocess_retry/manifest.json`
- retry missing rows: `4`
- decision: `not_recoverable_by_simple_retry_filter_missing_subgraphs`

## Runtime Files

- filtered relationships: `experiments/H001_geom_reliability/sources/open3dsg/validation_preprocess_filter/relationships_validation.filtered.json`
- filtered scan list: `experiments/H001_geom_reliability/sources/open3dsg/validation_preprocess_filter/validation_scans.filtered.txt`
- missing rows: `experiments/H001_geom_reliability/sources/open3dsg/validation_preprocess_filter/missing.jsonl`
- removed rows: `experiments/H001_geom_reliability/sources/open3dsg/validation_preprocess_filter/removed.jsonl`

## Applied Runtime Mutation

- runtime relationships file: `local_dataset/Open3DSG_staged/training_repro/data/3RScan/3DSSG_subset/relationships_validation.json`
- runtime scans file: `local_dataset/Open3DSG_staged/training_repro/data/3RScan/3DSSG_subset/validation_scans.txt`
- backup relationships: `local_dataset/Open3DSG_staged/training_repro/data/3RScan/3DSSG_subset/relationships_validation.unfiltered.json`
- backup scans: `local_dataset/Open3DSG_staged/training_repro/data/3RScan/3DSSG_subset/validation_scans.unfiltered.txt`

## Claim Limit

Open3DSG training will use an explicit preprocessed-ready validation split. Report validation coverage as 156/160 subgraphs and do not claim full validation preprocessing.
