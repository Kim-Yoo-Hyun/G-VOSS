# Open3DSG Training Preflight

Created at: `2026-05-15T08:27:49.569857+00:00`
Mode: `train_full`
Status: `ready`

## Gates

- payload: `True`
- runtime stage: `True`
- paths: `True`
- imports: `True`
- gpu memory: `True`

## Payload

- train scan dirs: `1178/1178`
- train raw files min: `1178/1178`
- train mesh/texture min: `1178/1178`
- train sequence min: `1178/1178`
- validation scan dirs: `30/30`
- validation raw files min: `30/30`
- validation mesh/texture min: `30/30`
- validation sequence min: `30/30`

## Runtime Stage

- train views: `1158/1158`
- train preprocessed: `3744/3744`
- validation views: `30/30`
- validation preprocessed: `156/156`

## Source

- Open3DSG run script: `/workspace/local_dataset/Open3DSG_staged/training_repro/source/open3dsg_source/open3dsg/scripts/run.py`

## Imports

- CUDA available: `True`
- CUDA device count: `1`
- torch CUDA build: `2.8.0+cu128`
- CUDA device: `NVIDIA GeForce RTX 5090`
- required CUDA arch: `sm_120`
- torch supported arch list: `sm_70, sm_75, sm_80, sm_86, sm_90, sm_100, sm_120`
- GPU free memory: `19868` MB
- GPU total memory: `32100` MB
- GPU free-memory threshold: `18000` MB
- torch: `ok` `2.8.0+cu128`
- pytorch_lightning: `ok` `2.1.1`
- tensorflow: `ok` `2.12.0`
- open3d: `ok` `0.19.0`
- transformers: `ok` `4.46.3`
