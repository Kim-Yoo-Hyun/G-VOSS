# VL-SAT Layout Check

Generated: 2026-05-02T16:52:48+00:00

## Verdict

- status: `blocked`
- default VL-SAT ready: `false`
- H001 one-scan geometry ready scans: `1`

## Counts

- subset all entries: `1335`
- subset all unique scans: `1335`
- train entries: `3852`
- train unique scans: `1178`
- validation entries: `548`
- validation unique scans: `157`
- train/validation overlap: `0`
- local 3RScan scan dirs: `1`

## Blockers

- missing VL-SAT config relation label file: local_dataset/3DSSG_subset/relations.txt
- missing train_scans.txt required by VL-SAT dataset loader
- missing validation_scans.txt required by VL-SAT dataset loader
- aligned PLY missing for at least one local scan
- multi_view features missing for at least one local scan while VL-SAT default uses 2D features

## Warnings

- local 3RScan root uses local_dataset/3RScan/scans/<scan_id>, not direct 3RScan/<scan_id>
- no downloaded local scan payload currently belongs to official validation split
- only one local 3RScan scan payload is available; multi-scan evaluation remains blocked

## Missing Generated Annotation Files

- `local_dataset/3DSSG_subset/relations.txt`: missing
- `local_dataset/3DSSG_subset/train_scans.txt`: missing
- `local_dataset/3DSSG_subset/validation_scans.txt`: missing

## Local Scan Coverage

- `f62fd5fd-9a3f-2f44-883a-1e5cf819608e`: h001_ready=`true`, aligned_ply=`false`, multi_view=`false`

## Next

1. Generate or stage `relations.txt`, `train_scans.txt`, and `validation_scans.txt` outside source dataset mutation.
2. Decide faithful aligned+`multi_view` route vs 3D-only plumbing route.
3. Download selected H001-Mini scan payloads before prediction-level evaluation.
