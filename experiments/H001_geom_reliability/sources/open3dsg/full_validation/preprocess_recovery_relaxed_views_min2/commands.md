# Open3DSG Full-Validation Missing-15 Recovery Commands

Date: 2026-06-05 KST

This branch is isolated at the artifact/output level. It does not overwrite the
canonical `sources/open3dsg/full_validation/` metric bundle. The Open3DSG
runtime still uses its fixed preprocessed root, so the recovered preprocessed
pickles must remain in the staged runtime until the recovery raw dump finishes.

## Diagnosis

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml \
  run --rm open3dsg_base bash -lc '
python /workspace/experiments/H001_geom_reliability/scripts/diagnose_open3dsg_missing15.py \
  --repo-root /workspace \
  --output-dir /workspace/experiments/H001_geom_reliability/sources/open3dsg/full_validation/preprocess_missing15_diagnosis \
  --write
'
```

## Recovery Policy

- `OPEN3DSG_MIN_VISIBLE_OBJECTS=2` for the 15 missing contexts.
- Relaxed view-generation thresholds only for the two scans that still had one
  visible annotation object after the min-visible relaxation.
- Recovery results must stay under a separate branch root until feature audit,
  raw dump, adapter, geometry join, metrics, bootstrap CI, failure rows, and
  table/caveat regeneration all pass.

## Feature Dump

Feature run directory:

```text
local_dataset/Open3DSG_staged/h001_full_validation_runtime/output/features/clip_features_h001_full_validation_recovery_relaxed_views_min2
```

Running tmux job:

```text
h001_open3dsg_fullval_recovery_features
```

Log:

```text
logs/h001_open3dsg_fullval_recovery_features_20260605_015956.log
```

Completion check:

```bash
test -f logs/h001_open3dsg_fullval_recovery_features_20260605_015956.exit && \
  cat logs/h001_open3dsg_fullval_recovery_features_20260605_015956.exit

find local_dataset/Open3DSG_staged/h001_full_validation_runtime/output/features/clip_features_h001_full_validation_recovery_relaxed_views_min2 \
  -type f -name '*.pt' | wc -l
```

Expected final count: `1644` `.pt` files for `548` complete feature ids.

## Next Gate

After the feature dump exits cleanly, run feature audit into:

```text
experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/features/
```

If that audit reports `548/548`, run the recovery raw dump and all downstream
artifacts under:

```text
experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/
```
