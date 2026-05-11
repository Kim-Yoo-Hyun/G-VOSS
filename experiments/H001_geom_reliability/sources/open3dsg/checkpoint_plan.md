# Open3DSG Checkpoint Reproduction Plan

Generated: 2026-05-07T15:35:45.373151+00:00

## Decision

Generate the Open3DSG checkpoint ourselves through Dockerized reproduction, then run raw dump, JSONL export, geometry join, and H001 metrics.

## Claim Boundary

- Allowed now: VL-SAT-centered geometry reliability result only
- Blocked until metric: cross-predictor reliability-layer claim
- Upgrade condition: Open3DSG checkpoint, identity-preserving raw dump, prediction JSONL, geometry join, and metric table exist

## Split Policy

| Split | Source | Scans | Subgraphs | Relations |
| --- | --- | ---: | ---: | ---: |
| train | `local_dataset/3DSSG_subset/relationships_train.json` | 1178 | 3852 | 81190 |
| H001 eval | `H001 hardened validation/test subset` | 127 | 388 | 7505 |

Leakage guard: Do not train on H001 hardened validation/test scans used for second-source evaluation.

## Current Readiness

- H001 eval staged root: `staged_metadata_root_ready_mesh_texture_ready_external_artifacts_missing`
- H001 eval views: `views_ready`
- H001 eval preprocess: `preprocess_partial_ready` (377/388)
- Model artifacts: `model_artifacts_partial_ready`
- Training repro: `training_repro_staged_root_ready_for_view_preprocess`
- Blockers: missing_model:open3dsg_checkpoint, empty_staged_train_split, missing_full_train_preprocessed:0/3852, missing_full_train_views:0/1178, missing_full_train_scan_dirs:33/1178, missing_training_python_modules:open3d,pytorch_lightning,tensorflow,transformers, compute_below_official_example_gpus:1/4
- Training repro blockers: none
- Docker GPU smoke: target: NVIDIA GeForce RTX 5090 requires CUDA 12.8-compatible PyTorch wheels; the previous cu118 image reached Open3DSG execution but failed on sm_120.

## Docker Pins

- Base image: `nvidia/cuda:12.8.1-cudnn-devel-ubuntu22.04`
- Python: `3.9 via Miniforge`
- Torch: `torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 with CUDA 12.8 wheels`
- PyG wheels: `torch-scatter/sparse/cluster/spline-conv from https://data.pyg.org/whl/torch-2.8.0+cu128.html`
- Dockerfile: `experiments/H001_geom_reliability/sources/open3dsg/Dockerfile.repro`
- Compose file: `experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml`

## Execution Sequence

1. Build h001-open3dsg-repro:cu128 image.
2. Run env_check and cache_preflight; require imports, CUDA, writable cache dirs, local model files, and disk budget.
3. Create local_dataset/Open3DSG_staged/training_repro from official 3DSSG_subset train split and full 3RScan payloads.
4. Generate train views and preprocessed pickles for 1178 train scans / 3852 train subgraphs.
5. Optionally dump OpenSeg+BLIP features to a mounted cache; budget about 300GB per README.
6. Run 1-epoch pilot with single GPU, batch_size=1, accumulate_grad_batches=4, mixed precision.
7. Run full training only if the pilot creates a checkpoint and train/eval row counts match the plan.
8. Run eval_preflight, then H001 eval raw dump with GT objects on hardened validation/test subset.
9. Export Open3DSG prediction JSONL, run geometry join, and build cross-source Table 6.

## Failure Budget

| Item | Budget |
| --- | --- |
| environment build attempts | 2 |
| train data staging attempts | 2 |
| preprocess attempts | 2 |
| pilot train attempts | 2 |
| full train attempts | 1 |
| minimum free disk before feature dump | 450 GB |
| minimum train scan coverage | 1178/1178 |
| minimum train preprocess coverage | 3852/3852 |

Fallback: If Dockerized Open3DSG reproduction exceeds budget, keep VL-SAT-only reliability-layer claim and report second-source blocker.
