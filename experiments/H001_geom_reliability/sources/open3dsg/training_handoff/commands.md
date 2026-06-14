# Open3DSG Training Handoff

Created at: `2026-05-07T14:51:21.608275+00:00`
Status: `ready_for_open3dsg_env_check`

## Payload Gate

- passed: `True`
- train scan dirs: `1178/1178`
- train raw files min: `1178/1178`
- train mesh/texture min: `1178/1178`
- train sequence min: `1178/1178`

## Next Commands

- `build_repro_image`: `sg docker -c 'docker compose -f configs/open3dsg/compose.open3dsg.yaml build'`
- `env_check`: `sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm env_check'`
- `cache_preflight`: `sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm cache_preflight'`
- `dump_features_3rscan`: `sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm dump_features_3rscan'`
- `train_pilot`: `sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_pilot'`
- `train_full`: `sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_full'`
- `eval_preflight`: `sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/<checkpoint>.ckpt docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm eval_preflight'`
- `eval_h001_gt_objects`: `sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/<checkpoint>.ckpt docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects'`

## Claim Boundary

This handoff fixes the Docker command order only. It does not train Open3DSG, create a checkpoint, or create second-source metric evidence.
