# Open3DSG Eval Preflight

Created at: `2026-05-07T15:34:46.142511+00:00`
Status: `blocked`

## Gates

- checkpoint: `False`
- runtime: `True`
- scope: `True`
- imports: `True`

## Checkpoint

- path: `None`
- exists: `False`
- bytes: `0`

## Scope

- selected scans: `127`
- contexts: `388`

## Raw Dump Contract

- status: `contract_ready_raw_dump_missing`
- raw dump JSONL: `experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl`
- schema version: `h001_open3dsg_raw_dump_v1`

## Imports

- torch: `ok` `2.8.0+cu128`
- pytorch_lightning: `ok` `2.1.1`
- tensorflow: `ok` `2.12.0`
- open3d: `ok` `0.19.0`
- transformers: `ok` `4.46.3`
- clip: `ok` `None`
- open_clip: `ok` `3.3.0`
- CUDA available: `True`
- CUDA device count: `1`
- torch: `2.8.0+cu128`

## Blockers

- `missing_checkpoint_env:OPEN3DSG_CHECKPOINT`
