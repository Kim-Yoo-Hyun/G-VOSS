# Open3DSG Train Preprocess Filter

Created at: `2026-05-07T23:53:28.778553+00:00`
Status: `filter_applied`
Applied: `True`

## Counts

- original train subgraphs: `3852`
- kept train subgraphs: `3744`
- removed train subgraphs: `108`
- original train scans: `1178`
- kept train scans: `1158`
- removed-only scans: `20`
- original relation annotations: `81190`
- kept relation annotations: `79704`
- removed relation annotations: `1486`

## Recoverability Check

- full preprocess missing rows: `108`
- `too few visible objects` log count: `108`
- retry manifest: `experiments/H001_geom_reliability/sources/open3dsg/train_preprocess_retry/manifest.json`
- retry missing rows: `6`
- decision: `not_recoverable_by_simple_retry_filter_missing_subgraphs`

## Runtime Files

- filtered relationships: `experiments/H001_geom_reliability/sources/open3dsg/train_preprocess_filter/relationships_train.filtered.json`
- filtered train scans: `experiments/H001_geom_reliability/sources/open3dsg/train_preprocess_filter/train_scans.filtered.txt`
- missing rows: `experiments/H001_geom_reliability/sources/open3dsg/train_preprocess_filter/missing.jsonl`
- removed rows: `experiments/H001_geom_reliability/sources/open3dsg/train_preprocess_filter/removed.jsonl`

## Applied Runtime Mutation

- runtime relationships_train.json: `local_dataset/Open3DSG_staged/training_repro/data/3RScan/3DSSG_subset/relationships_train.json`
- runtime train_scans.txt: `local_dataset/Open3DSG_staged/training_repro/data/3RScan/3DSSG_subset/train_scans.txt`
- backup relationships: `local_dataset/Open3DSG_staged/training_repro/data/3RScan/3DSSG_subset/relationships_train.unfiltered.json`
- backup train scans: `local_dataset/Open3DSG_staged/training_repro/data/3RScan/3DSSG_subset/train_scans.unfiltered.txt`

## Claim Limit

Open3DSG training will use an explicit preprocessed-ready train split. Report train coverage as 3744/3852 subgraphs and do not claim full official-train preprocessing.
