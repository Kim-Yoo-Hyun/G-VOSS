# Open3DSG Cache Preflight

Created at: `2026-05-07T15:29:33.192596+00:00`
Status: `ready_with_cache_warnings`

## Gates

- paths: `True`
- disk: `True`
- imports: `True`
- require model cache: `False`

## Disk

- training_root: `601.186GB free` at `/workspace/local_dataset/Open3DSG_staged/training_repro`
- hf_home: `601.186GB free` at `/workspace/local_dataset/model_cache/huggingface`
- torch_home: `601.186GB free` at `/workspace/local_dataset/model_cache/torch`

## Required Local Model Files

- blip2_positional_embedding: `/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/blip2_positional_embedding.pt` `724580` bytes
- pointnet_checkpoint: `/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/pointnet.pth` `41785402` bytes
- pointnet2_ulip_checkpoint: `/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/pointnet2_ulip.pt` `617835287` bytes
- openseg_saved_model: `/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/openseg/saved_model.pb` `5011391` bytes

## Cache Hints

- `model_cache_missing_or_empty:torch_hub:/workspace/local_dataset/model_cache/torch/hub`

## Imports

- torch: `ok` `2.8.0+cu128`
- transformers: `ok` `4.46.3`
- tensorflow: `ok` `2.12.0`
- clip: `ok` `None`
- open_clip: `ok` `3.3.0`
- CUDA available: `True`
- CUDA device count: `1`
- CUDA device: `NVIDIA GeForce RTX 5090`
- required CUDA arch: `sm_120`
- torch supported arch list: `sm_70, sm_75, sm_80, sm_86, sm_90, sm_100, sm_120`

## Warnings

- `model_cache_missing_or_empty:torch_hub:/workspace/local_dataset/model_cache/torch/hub`
