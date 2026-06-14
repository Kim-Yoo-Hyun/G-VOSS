#!/usr/bin/env python3
"""Create the Dockerized Open3DSG checkpoint reproduction plan."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paths import H001_HYPOTHESIS_REL


HYPOTHESIS_ROOT = H001_HYPOTHESIS_REL
OPEN3DSG_ARTIFACT_ROOT = HYPOTHESIS_ROOT / "artifacts/evaluation/open3dsg_ov"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def path_exists(repo_root: Path, rel: str) -> bool:
    return (repo_root / rel).exists()


def build_plan(repo_root: Path) -> dict[str, Any]:
    artifacts = {
        "training_route": load_json(repo_root / OPEN3DSG_ARTIFACT_ROOT / "training_route/manifest.json"),
        "model_artifacts": load_json(repo_root / OPEN3DSG_ARTIFACT_ROOT / "model_artifacts/manifest.json"),
        "staged_root": load_json(repo_root / OPEN3DSG_ARTIFACT_ROOT / "staged_root/manifest.json"),
        "views": load_json(repo_root / OPEN3DSG_ARTIFACT_ROOT / "views/manifest.json"),
        "preprocess": load_json(repo_root / OPEN3DSG_ARTIFACT_ROOT / "preprocess/manifest.json"),
        "adapter": load_json(repo_root / OPEN3DSG_ARTIFACT_ROOT / "adapter/manifest.json"),
    }

    train = artifacts["training_route"]
    model = artifacts["model_artifacts"]
    staged = artifacts["staged_root"]
    views = artifacts["views"]
    preprocess = artifacts["preprocess"]
    training_repro_path = repo_root / "experiments/H001_geom_reliability/sources/open3dsg/training_repro/manifest.json"
    training_repro = load_json(training_repro_path) if training_repro_path.exists() else None

    plan = {
        "schema_version": "h001_open3dsg_checkpoint_reproduction_plan_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "plan_ready_training_not_started",
        "decision": "Generate the Open3DSG checkpoint ourselves through Dockerized reproduction, then run raw dump, JSONL export, geometry join, and H001 metrics.",
        "claim_boundary": {
            "allowed_now": "VL-SAT-centered geometry reliability result only",
            "blocked_until_metric": "cross-predictor reliability-layer claim",
            "upgrade_condition": "Open3DSG checkpoint, identity-preserving raw dump, prediction JSONL, geometry join, and metric table exist",
        },
        "source": {
            "repo_snapshot": "local_dataset/Open3DSG_staged/h001_runtime/source/open3dsg_source",
            "run_script": "open3dsg/scripts/run.py",
            "config_strategy": "use env-driven config.py already staged in source snapshot",
            "source_exists": path_exists(repo_root, "local_dataset/Open3DSG_staged/h001_runtime/source/open3dsg_source/open3dsg/scripts/run.py"),
        },
        "split_policy": {
            "train_source": train["official_3dssg_train"]["path"],
            "train_unique_scans": train["official_3dssg_train"]["unique_scans"],
            "train_subgraphs": train["official_3dssg_train"]["subgraphs"],
            "train_relations": train["official_3dssg_train"]["relations"],
            "eval_source": "H001 hardened validation/test subset",
            "eval_unique_scans": staged["validation_unique_scans"],
            "eval_subgraphs": staged["validation_subgraphs"],
            "eval_relations": staged["validation_relations"],
            "leakage_guard": "Do not train on H001 hardened validation/test scans used for second-source evaluation.",
            "current_staged_train_status": {
                "unique_scans": train["staged_train"]["unique_scans"],
                "subgraphs": train["staged_train"]["subgraphs"],
                "relations": train["staged_train"]["relations"],
                "reason": "current H001 staged root was inference-only; a separate training_repro root is required",
            },
            "training_repro_status": None
            if training_repro is None
            else {
                "status": training_repro["status"],
                "official_train": training_repro["official_train"],
                "train_dev_without_h001": training_repro["train_dev_without_h001"],
                "train_scan_dirs_ready": training_repro["train_payload"]["existing_scan_dirs"],
                "train_scan_dirs_expected": training_repro["train_payload"]["expected_scans"],
                "h001_overlap_train": len(training_repro["leakage"]["train_h001_overlap"]),
                "h001_overlap_train_dev": len(training_repro["leakage"]["train_dev_h001_overlap"]),
            },
        },
        "current_readiness": {
            "h001_eval_staged_root": staged["status"],
            "h001_eval_scan_symlinks": staged["selected_scan_count"],
            "h001_eval_views": views["status"],
            "h001_eval_preprocess": preprocess["status"],
            "h001_eval_preprocessed_ready": preprocess["summary"]["ready_subgraph_count"],
            "h001_eval_preprocessed_expected": preprocess["summary"]["processed_subgraph_count"],
            "model_artifacts": model["status"],
            "model_blockers": model["blockers"],
            "training_route_previous_status": train["status"],
            "previous_blockers": train["blockers"],
            "training_repro_status": None if training_repro is None else training_repro["status"],
            "training_repro_blockers": [] if training_repro is None else training_repro["blockers"],
            "docker_gpu_smoke": "target: NVIDIA GeForce RTX 5090 requires CUDA 12.8-compatible PyTorch wheels; the previous cu118 image reached Open3DSG execution but failed on sm_120.",
        },
        "docker": {
            "base_image": "nvidia/cuda:12.8.1-cudnn-devel-ubuntu22.04",
            "python": "3.9 via Miniforge",
            "torch": "torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 with CUDA 12.8 wheels",
            "pyg_wheels": "torch-scatter/sparse/cluster/spline-conv from https://data.pyg.org/whl/torch-2.8.0+cu128.html",
            "core_pins": {
                "numpy": "1.23.3",
                "pytorch-lightning": "2.1.1",
                "tensorflow": "2.12.0",
                "torch-geometric": "2.5.0",
                "transformers": "4.46.3",
                "sentencepiece": "latest",
            },
            "compose_file": "configs/open3dsg/compose.open3dsg.yaml",
            "dockerfile": "configs/open3dsg/Dockerfile.repro",
            "image": "h001-open3dsg-repro:cu128",
        },
        "mounts": {
            "repo": "/workspace",
            "training_repro_root": "/workspace/local_dataset/Open3DSG_staged/training_repro",
            "h001_eval_root": "/workspace/local_dataset/Open3DSG_staged/h001_runtime",
            "raw_3rscan": "/workspace/local_dataset/3RScan",
            "official_3dssg_subset": "/workspace/local_dataset/3DSSG_subset",
            "hf_cache": "/workspace/local_dataset/model_cache/huggingface",
            "torch_cache": "/workspace/local_dataset/model_cache/torch",
            "home_cache": "/workspace/local_dataset/model_cache/home",
            "xdg_cache": "/workspace/local_dataset/model_cache/xdg",
            "open3dsg_cache": "/workspace/local_dataset/Open3DSG_staged/cache",
        },
        "commands": {
            "stage_train_root": "docker compose -f configs/h001/compose.yaml run --rm open3dsg_train_root",
            "env_check": "docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm env_check",
            "cache_preflight": "docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm cache_preflight",
            "train_views_audit": "docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_views_audit",
            "train_views_smoke": "docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_views_smoke",
            "train_views_full": "docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_views_full",
            "train_preprocess_smoke": "docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_preprocess_smoke",
            "train_preprocess_full": "docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_preprocess_full",
            "dump_features": "docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm dump_features_3rscan",
            "pilot_train": "docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_pilot",
            "full_train": "docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_full",
            "eval_preflight": "docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm eval_preflight",
            "eval_after_checkpoint": "docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects",
        },
        "execution_sequence": [
            "Build h001-open3dsg-repro:cu128 image.",
            "Run env_check and cache_preflight; require imports, CUDA, writable cache dirs, local model files, and disk budget.",
            "Create local_dataset/Open3DSG_staged/training_repro from official 3DSSG_subset train split and full 3RScan payloads.",
            "Generate train views and preprocessed pickles for 1178 train scans / 3852 train subgraphs.",
            "Optionally dump OpenSeg+BLIP features to a mounted cache; budget about 300GB per README.",
            "Run 1-epoch pilot with single GPU, batch_size=1, accumulate_grad_batches=4, mixed precision.",
            "Run full training only if the pilot creates a checkpoint and train/eval row counts match the plan.",
            "Run eval_preflight, then H001 eval raw dump with GT objects on hardened validation/test subset.",
            "Export Open3DSG prediction JSONL, run geometry join, and build cross-source Table 6.",
        ],
        "failure_budget": {
            "environment_build_attempts": 2,
            "train_data_staging_attempts": 2,
            "preprocess_attempts": 2,
            "pilot_train_attempts": 2,
            "full_train_attempts": 1,
            "minimum_free_disk_gb_before_feature_dump": 450,
            "minimum_train_scan_coverage": "1178/1178",
            "minimum_train_preprocess_coverage": "3852/3852",
            "pilot_success_criterion": "at least one Lightning checkpoint and no held-out-scope mutation",
            "fallback": "If Dockerized Open3DSG reproduction exceeds budget, keep VL-SAT-only reliability-layer claim and report second-source blocker.",
        },
        "next_outputs_required": [
            "Docker env-check log",
            "training_repro staged-root manifest",
            "full train payload/view/preprocess manifests",
            "pilot checkpoint path",
            "full checkpoint path or explicit failed-budget report",
            "Open3DSG raw dump",
            "open3dsg_ov prediction JSONL",
            "Open3DSG geometry join",
            "Open3DSG metric table",
        ],
    }
    return plan


def render_plan_md(plan: dict[str, Any]) -> str:
    return f"""# Open3DSG Checkpoint Reproduction Plan

Generated: {plan['created_at_utc']}

## Decision

{plan['decision']}

## Claim Boundary

- Allowed now: {plan['claim_boundary']['allowed_now']}
- Blocked until metric: {plan['claim_boundary']['blocked_until_metric']}
- Upgrade condition: {plan['claim_boundary']['upgrade_condition']}

## Split Policy

| Split | Source | Scans | Subgraphs | Relations |
| --- | --- | ---: | ---: | ---: |
| train | `{plan['split_policy']['train_source']}` | {plan['split_policy']['train_unique_scans']} | {plan['split_policy']['train_subgraphs']} | {plan['split_policy']['train_relations']} |
| H001 eval | `{plan['split_policy']['eval_source']}` | {plan['split_policy']['eval_unique_scans']} | {plan['split_policy']['eval_subgraphs']} | {plan['split_policy']['eval_relations']} |

Leakage guard: {plan['split_policy']['leakage_guard']}

## Current Readiness

- H001 eval staged root: `{plan['current_readiness']['h001_eval_staged_root']}`
- H001 eval views: `{plan['current_readiness']['h001_eval_views']}`
- H001 eval preprocess: `{plan['current_readiness']['h001_eval_preprocess']}` ({plan['current_readiness']['h001_eval_preprocessed_ready']}/{plan['current_readiness']['h001_eval_preprocessed_expected']})
- Model artifacts: `{plan['current_readiness']['model_artifacts']}`
- Training repro: `{plan['current_readiness']['training_repro_status']}`
- Blockers: {', '.join(plan['current_readiness']['model_blockers'] + plan['current_readiness']['previous_blockers'])}
- Training repro blockers: {', '.join(plan['current_readiness']['training_repro_blockers']) if plan['current_readiness']['training_repro_blockers'] else 'none'}
- Docker GPU smoke: {plan['current_readiness']['docker_gpu_smoke']}

## Docker Pins

- Base image: `{plan['docker']['base_image']}`
- Python: `{plan['docker']['python']}`
- Torch: `{plan['docker']['torch']}`
- PyG wheels: `{plan['docker']['pyg_wheels']}`
- Dockerfile: `{plan['docker']['dockerfile']}`
- Compose file: `{plan['docker']['compose_file']}`

## Execution Sequence

""" + "\n".join(f"{idx}. {step}" for idx, step in enumerate(plan["execution_sequence"], 1)) + f"""

## Failure Budget

| Item | Budget |
| --- | --- |
| environment build attempts | {plan['failure_budget']['environment_build_attempts']} |
| train data staging attempts | {plan['failure_budget']['train_data_staging_attempts']} |
| preprocess attempts | {plan['failure_budget']['preprocess_attempts']} |
| pilot train attempts | {plan['failure_budget']['pilot_train_attempts']} |
| full train attempts | {plan['failure_budget']['full_train_attempts']} |
| minimum free disk before feature dump | {plan['failure_budget']['minimum_free_disk_gb_before_feature_dump']} GB |
| minimum train scan coverage | {plan['failure_budget']['minimum_train_scan_coverage']} |
| minimum train preprocess coverage | {plan['failure_budget']['minimum_train_preprocess_coverage']} |

Fallback: {plan['failure_budget']['fallback']}
"""


def repro_dockerfile() -> str:
    return """FROM nvidia/cuda:12.8.1-cudnn-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV CONDA_DIR=/opt/conda
ENV PATH=/opt/conda/envs/open3dsg/bin:/opt/conda/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV MPLCONFIGDIR=/tmp/matplotlib

RUN apt-get update && apt-get install -y --no-install-recommends \\
    bash ca-certificates curl git build-essential libgl1 libglib2.0-0 libxrender1 libxext6 \\
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -o /tmp/miniforge.sh \\
    && bash /tmp/miniforge.sh -b -p /opt/conda \\
    && rm /tmp/miniforge.sh \\
    && conda config --set channel_priority strict \\
    && conda create -y -n open3dsg python=3.9 pip \\
    && conda clean -afy

SHELL ["/bin/bash", "-lc"]

RUN conda run -n open3dsg python -m pip install --no-cache-dir \\
    torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 \\
    --index-url https://download.pytorch.org/whl/cu128

RUN conda run -n open3dsg python -m pip install --no-cache-dir \\
    torch-cluster==1.6.3 torch-scatter==2.1.2 torch-sparse==0.6.18 torch-spline-conv==1.2.2 \\
    -f https://data.pyg.org/whl/torch-2.8.0+cu128.html

RUN conda run -n open3dsg python -m pip install --no-cache-dir \\
    easydict ftfy mlflow numpy==1.23.3 open3d opencv-python open_clip_torch graphviz plyfile \\
    pytorch-lightning==2.1.1 scipy tensorflow==2.12.0 torch-geometric==2.5.0 tqdm \\
    transformers==4.46.3 sentencepiece trimesh \\
    git+https://github.com/katsura-jp/pytorch-cosine-annealing-with-warmup.git \\
    git+https://github.com/openai/CLIP.git

WORKDIR /workspace

CMD ["python", "-c", "import torch, pytorch_lightning, tensorflow, open3d, transformers; print('open3dsg docker env ready', torch.__version__)"]
"""


def compose_yaml() -> str:
    return """services:
  open3dsg_base: &open3dsg_base
    build:
      context: ../../../..
      dockerfile: configs/open3dsg/Dockerfile.repro
    image: h001-open3dsg-repro:cu128
    working_dir: /workspace
    user: "${UID:-1000}:${GID:-1000}"
    environment:
      OPEN3DSG_HOME: /workspace
      OPEN3DSG_BASE: /workspace/local_dataset/Open3DSG_staged/training_repro
      OPEN3DSG_DATA: /workspace/local_dataset/Open3DSG_staged/training_repro/data
      OPEN3DSG_DATA_OUT: /workspace/local_dataset/Open3DSG_staged/training_repro/output
      HF_HOME: /workspace/local_dataset/model_cache/huggingface
      TORCH_HOME: /workspace/local_dataset/model_cache/torch
      TRANSFORMERS_CACHE: /workspace/local_dataset/model_cache/huggingface
      HOME: /workspace/local_dataset/model_cache/home
      XDG_CACHE_HOME: /workspace/local_dataset/model_cache/xdg
    volumes:
      - ../../../..:/workspace
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  env_check:
    <<: *open3dsg_base
    command: >
      bash -lc "python -c 'import torch, pytorch_lightning, tensorflow, open3d, transformers;
      print(torch.cuda.is_available(), torch.cuda.device_count(), torch.__version__)'"

  cache_preflight:
    <<: *open3dsg_base
    command: >
      bash -lc "python /workspace/src/geocalib/open3dsg_cache_preflight.py
      --repo-root /workspace --ensure-dirs --check-imports --min-free-gb 300"

  train_views_audit:
    <<: *open3dsg_base
    command: >
      bash -lc "python /workspace/src/geocalib/patch_open3dsg_source.py --repo-root /workspace --source-root /workspace/local_dataset/Open3DSG_staged/training_repro/source/open3dsg_source &&
      python /workspace/src/geocalib/run_open3dsg_train_views.py --audit-only --workers 1"

  train_views_smoke:
    <<: *open3dsg_base
    command: >
      bash -lc "python /workspace/src/geocalib/patch_open3dsg_source.py --repo-root /workspace --source-root /workspace/local_dataset/Open3DSG_staged/training_repro/source/open3dsg_source &&
      python /workspace/src/geocalib/run_open3dsg_train_views.py --limit ${OPEN3DSG_TRAIN_STAGE_LIMIT:-1} --workers 1"

  train_views_full:
    <<: *open3dsg_base
    command: >
      bash -lc "python /workspace/src/geocalib/patch_open3dsg_source.py --repo-root /workspace --source-root /workspace/local_dataset/Open3DSG_staged/training_repro/source/open3dsg_source &&
      python /workspace/src/geocalib/run_open3dsg_train_views.py --workers ${OPEN3DSG_TRAIN_STAGE_WORKERS:-4}"

  train_preprocess_audit:
    <<: *open3dsg_base
    command: >
      bash -lc "python /workspace/src/geocalib/patch_open3dsg_source.py --repo-root /workspace --source-root /workspace/local_dataset/Open3DSG_staged/training_repro/source/open3dsg_source &&
      python /workspace/src/geocalib/run_open3dsg_train_preprocess.py --audit-only --workers 1"

  train_preprocess_smoke:
    <<: *open3dsg_base
    command: >
      bash -lc "python /workspace/src/geocalib/patch_open3dsg_source.py --repo-root /workspace --source-root /workspace/local_dataset/Open3DSG_staged/training_repro/source/open3dsg_source &&
      SCAN_ID=$$(python -c 'import json; print(json.load(open(\\"/workspace/local_dataset/Open3DSG_staged/training_repro/data/3RScan/3DSSG_subset/relationships_train.json\\"))[\\"scans\\"][0][\\"scan\\"])') &&
      python /workspace/src/geocalib/run_open3dsg_train_views.py --scan-id "$$SCAN_ID" --workers 1 &&
      python /workspace/src/geocalib/run_open3dsg_train_preprocess.py --scan-id "$$SCAN_ID" --workers 1 --deep-inspect"

  train_preprocess_full:
    <<: *open3dsg_base
    command: >
      bash -lc "python /workspace/src/geocalib/patch_open3dsg_source.py --repo-root /workspace --source-root /workspace/local_dataset/Open3DSG_staged/training_repro/source/open3dsg_source &&
      python /workspace/src/geocalib/run_open3dsg_train_preprocess.py --workers ${OPEN3DSG_TRAIN_STAGE_WORKERS:-4}"

  dump_features_3rscan:
    <<: *open3dsg_base
    working_dir: /workspace/local_dataset/Open3DSG_staged/training_repro/source/open3dsg_source
    command: >
      bash -lc "python /workspace/src/geocalib/open3dsg_training_preflight.py --repo-root /workspace --mode dump_features --ensure-dirs --check-imports &&
      python /workspace/src/geocalib/patch_open3dsg_source.py --repo-root /workspace --source-root /workspace/local_dataset/Open3DSG_staged/training_repro/source/open3dsg_source &&
      pip install -e . &&
      python open3dsg/scripts/run.py --dump_features --dataset 3rscan --scales 3 --top_k_frames 5 --clip_model OpenSeg --blip"

  train_pilot:
    <<: *open3dsg_base
    working_dir: /workspace/local_dataset/Open3DSG_staged/training_repro/source/open3dsg_source
    command: >
      bash -lc "python /workspace/src/geocalib/open3dsg_training_preflight.py --repo-root /workspace --mode train_pilot --ensure-dirs --check-imports &&
      python /workspace/src/geocalib/patch_open3dsg_source.py --repo-root /workspace --source-root /workspace/local_dataset/Open3DSG_staged/training_repro/source/open3dsg_source &&
      pip install -e . &&
      python open3dsg/scripts/run.py --epochs 1 --batch_size 1 --gpus 1 --workers 4 --use_rgb
      --dataset 3rscan --clip_model OpenSeg --blip --mixed_precision --accumulate_grad_batches 4
      --load_features /workspace/local_dataset/Open3DSG_staged/training_repro/output/features
      --run_name h001_open3dsg_pilot"

  train_full:
    <<: *open3dsg_base
    working_dir: /workspace/local_dataset/Open3DSG_staged/training_repro/source/open3dsg_source
    command: >
      bash -lc "python /workspace/src/geocalib/open3dsg_training_preflight.py --repo-root /workspace --mode train_full --ensure-dirs --check-imports &&
      python /workspace/src/geocalib/patch_open3dsg_source.py --repo-root /workspace --source-root /workspace/local_dataset/Open3DSG_staged/training_repro/source/open3dsg_source &&
      pip install -e . &&
      python open3dsg/scripts/run.py --epochs 100 --batch_size 1 --gpus 1 --workers 4 --use_rgb
      --dataset 3rscan --clip_model OpenSeg --blip --mixed_precision --accumulate_grad_batches 4
      --load_features /workspace/local_dataset/Open3DSG_staged/training_repro/output/features
      --run_name h001_open3dsg_full"

  eval_preflight:
    <<: *open3dsg_base
    working_dir: /workspace/local_dataset/Open3DSG_staged/h001_runtime/source/open3dsg_source
    environment:
      OPEN3DSG_HOME: /workspace
      OPEN3DSG_BASE: /workspace/local_dataset/Open3DSG_staged/h001_runtime
      OPEN3DSG_DATA: /workspace/local_dataset/Open3DSG_staged/h001_runtime/data
      OPEN3DSG_DATA_OUT: /workspace/local_dataset/Open3DSG_staged/h001_runtime/output
      HF_HOME: /workspace/local_dataset/model_cache/huggingface
      TORCH_HOME: /workspace/local_dataset/model_cache/torch
      TRANSFORMERS_CACHE: /workspace/local_dataset/model_cache/huggingface
      HOME: /workspace/local_dataset/model_cache/home
      XDG_CACHE_HOME: /workspace/local_dataset/model_cache/xdg
      OPEN3DSG_CHECKPOINT: ${OPEN3DSG_CHECKPOINT:-}
    command: >
      bash -lc "python /workspace/src/geocalib/open3dsg_eval_preflight.py
      --repo-root /workspace --ensure-dirs --check-imports"

  eval_h001_gt_objects:
    <<: *open3dsg_base
    working_dir: /workspace/local_dataset/Open3DSG_staged/h001_runtime/source/open3dsg_source
    environment:
      OPEN3DSG_HOME: /workspace
      OPEN3DSG_BASE: /workspace/local_dataset/Open3DSG_staged/h001_runtime
      OPEN3DSG_DATA: /workspace/local_dataset/Open3DSG_staged/h001_runtime/data
      OPEN3DSG_DATA_OUT: /workspace/local_dataset/Open3DSG_staged/h001_runtime/output
      HF_HOME: /workspace/local_dataset/model_cache/huggingface
      TORCH_HOME: /workspace/local_dataset/model_cache/torch
      TRANSFORMERS_CACHE: /workspace/local_dataset/model_cache/huggingface
      HOME: /workspace/local_dataset/model_cache/home
      XDG_CACHE_HOME: /workspace/local_dataset/model_cache/xdg
      OPEN3DSG_CHECKPOINT: ${OPEN3DSG_CHECKPOINT:-}
    command: >
      bash -lc "python /workspace/src/geocalib/open3dsg_eval_preflight.py
      --repo-root /workspace --ensure-dirs --check-imports &&
      python /workspace/src/geocalib/patch_open3dsg_source.py --repo-root /workspace --source-root /workspace/local_dataset/Open3DSG_staged/h001_runtime/source/open3dsg_source &&
      pip install -e . &&
      python open3dsg/scripts/run.py --test --dataset 3rscan --checkpoint \"$${OPEN3DSG_CHECKPOINT}\"
      --n_beams 5 --weight_2d 0.5 --clip_model OpenSeg --node_model ViT-L/14@336px --blip --gt_objects"
"""


def commands_md() -> str:
    return """# Open3DSG Docker Reproduction Commands

Run from the repository root.

Build the reproduction image:

```bash
sg docker -c 'docker compose -f configs/open3dsg/compose.open3dsg.yaml build'
```

Environment import/GPU check:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm env_check'
```

Model/cache preflight:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm cache_preflight'
```

Do not run `dump_features_3rscan`, `train_pilot`, or `train_full` until `local_dataset/Open3DSG_staged/training_repro/` has full official train payload, train views, and train preprocessed pickles.
The compose commands enforce this with `open3dsg_training_preflight.py`.

Stage `training_repro` metadata and scan symlinks from the top-level H001 compose file:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_train_root'
```

Train view/preprocess staging:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_views_audit'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_views_smoke'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_preprocess_smoke'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_views_full'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_preprocess_full'
```

Pilot command after full train staging:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_pilot'
```

Full training command after pilot checkpoint:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_full'
```

H001 eval command after checkpoint:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/<checkpoint>.ckpt docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm eval_preflight'
```

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/<checkpoint>.ckpt docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects'
```

`eval_h001_gt_objects` is protected by `open3dsg_eval_preflight.py` and stops before Open3DSG execution if checkpoint/runtime/scope/import gates fail.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out", default="experiments/H001_geom_reliability/sources/open3dsg")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_root = Path(args.out)
    if not out_root.is_absolute():
        out_root = repo_root / out_root
    out_root.mkdir(parents=True, exist_ok=True)

    plan = build_plan(repo_root)
    write_json(out_root / "checkpoint_plan.json", plan)
    write_text(out_root / "checkpoint_plan.md", render_plan_md(plan))
    write_text(out_root / "Dockerfile.repro", repro_dockerfile())
    write_text(out_root / "compose.open3dsg.yaml", compose_yaml())
    write_text(out_root / "commands.open3dsg.md", commands_md())

    status_path = out_root / "status.json"
    status = load_json(status_path) if status_path.exists() else {}
    status.update({
        "schema_version": "h001_open3dsg_source_status_v4",
        "checkpoint_plan_status": "checkpoint_reproduction_plan_ready_training_not_started",
        "plan": "checkpoint_plan.json",
        "dockerfile": "Dockerfile.repro",
        "compose": "compose.open3dsg.yaml",
        "commands": "commands.open3dsg.md",
    })
    status["status"] = "training_repro_payload_ready_train_stage_smoke_passed"
    status["next_gate"] = "full train view/preprocess coverage for local_dataset/Open3DSG_staged/training_repro/"
    write_json(out_root / "status.json", status)
    print(json.dumps({"status": status["checkpoint_plan_status"], "out": str(out_root)}, sort_keys=True))


if __name__ == "__main__":
    main()
