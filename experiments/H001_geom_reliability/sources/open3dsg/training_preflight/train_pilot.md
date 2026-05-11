# Open3DSG Training Preflight

Created at: `2026-05-07T15:34:13.135574+00:00`
Mode: `train_pilot`
Status: `blocked`

## Gates

- payload: `True`
- runtime stage: `False`
- paths: `False`
- imports: `True`

## Payload

- train scan dirs: `1178/1178`
- train raw files min: `1178/1178`
- train mesh/texture min: `1178/1178`
- train sequence min: `1178/1178`

## Runtime Stage

- train views: `2/1178`
- train preprocessed: `7/3852`

## Source

- Open3DSG run script: `/workspace/local_dataset/Open3DSG_staged/training_repro/source/open3dsg_source/open3dsg/scripts/run.py`

## Imports

- CUDA available: `True`
- CUDA device count: `1`
- torch CUDA build: `2.8.0+cu128`
- CUDA device: `NVIDIA GeForce RTX 5090`
- required CUDA arch: `sm_120`
- torch supported arch list: `sm_70, sm_75, sm_80, sm_86, sm_90, sm_100, sm_120`
- torch: `ok` `2.8.0+cu128`
- pytorch_lightning: `ok` `2.1.1`
- tensorflow: `ok` `2.12.0`
- open3d: `ok` `0.19.0`
- transformers: `ok` `4.46.3`

## Blockers

- `train_views:2/1178`
- `train_preprocessed:7/3852`
- `missing_feature_outputs:/workspace/local_dataset/Open3DSG_staged/training_repro/output/features`
