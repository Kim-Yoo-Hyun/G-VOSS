# Open3DSG Docker Env Check

Date: `2026-05-07`

Status: `ready`

Command:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm env_check'
```

Result:

- Docker image: `h001-open3dsg-repro:cu128`
- CUDA container version: `12.8.1`
- `torch.cuda.is_available()`: `True`
- CUDA device count: `1`
- torch version: `2.8.0+cu128`
- CUDA device: `NVIDIA GeForce RTX 5090`
- required CUDA arch: `sm_120`

Dependency fixes applied:

- replaced Anaconda `Miniconda3-latest` with conda-forge `Miniforge3`;
- upgraded the reproduction image to CUDA 12.8 / PyTorch 2.8.0 cu128 because the earlier cu118 image could not execute kernels for RTX 5090 `sm_120`;
- installed all pip packages through `conda run -n open3dsg python -m pip`;
- pinned `transformers==4.46.3` with `sentencepiece` so current HF InstructBLIP tokenizer artifacts load;
- set `MPLCONFIGDIR=/tmp/matplotlib` for non-root container runs.

Remaining warnings:

- `lightning_fabric` emits a `pkg_resources` deprecation warning;
- TensorFlow reports CPU feature and missing TensorRT warnings.

These warnings did not block import or CUDA visibility.
