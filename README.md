# GeoCalib Research Repository

This repository contains the H001/GeoCalib research workspace for reliable 3D Scene Graph relations. GeoCalib evaluates whether semantic relation predictions are geometrically consistent in 3D, then reports recall and violation tradeoffs under calibrated geometry-aware scoring and re-ranking. The current paper-facing scope is `support_contact`, `proximity`, and `relative_vertical`, with VL-SAT as the controlled reproduced anchor and Open3DSG as the main open-vocabulary relation-source case study. H001 remains an internal experiment identifier.

## Core Question

3D Scene Graph relation predictors can assign high semantic confidence to relations that are physically inconsistent with the subject-object geometry. This project asks whether relation confidence is calibrated to relation-level physical consistency, and whether a scoped geometry-consistency layer can reduce top-K violations without hiding recall tradeoffs.

## Repository Structure

- `src/`: core GeoCalib Python code for staging, geometry evidence, adapters, metrics, bootstrap CI, and table generation.
- `scripts/`: shell wrappers for long-running reproducible jobs.
- `configs/`: Dockerfiles and compose files.
- `experiments/`: source-specific experiment records, ablations, analysis outputs, and row-level runtime result locations.
- `results/`: lightweight paper-facing summaries, compact tables, reports, figure specs, and locked manifests.
- `docs/`: workflow rules, dashboard, and reproducibility runbook.
- `literature/`: literature notes and paper cards. Existing internal layout is preserved.
- `paper/`: manuscript source, figures, appendix/risk planning, and venue files.
- `archive/`: preserved hypothesis records, old code/output, superseded venue files, optional expansion tracks, caches, and files preserved instead of deleted.
- `local_dataset/`, `release/`, `logs/`: ignored local data, external bundle staging, and runtime logs.

## Execution

Run paper-facing experiments through Docker from the repository root:

```bash
cd /home/yoohyun/research
docker compose -f configs/h001/compose.yaml run --rm table_builder
docker compose -f configs/h001/compose.yaml run --rm bootstrap_ci
```

Main configuration entry points:

- `configs/h001/compose.yaml`: GeoCalib table, metric, bootstrap, source-adapter, and analysis services.
- `configs/h001/Dockerfile`: lightweight GeoCalib Python image.
- `configs/open3dsg/compose.open3dsg.yaml`: Open3DSG reproduction/runtime services.
- `configs/qwen_vl/compose.qwen.yaml`: Qwen-VL extension runtime services.

Useful source-level checks:

```bash
docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm env_check
docker compose -f configs/qwen_vl/compose.qwen.yaml run --rm qwen_vl_cache_verify
```

Build the current AAAI paper source with:

```bash
docker build -f paper/aaai/Dockerfile.tex -t h001-aaai-tex:20260526 paper/aaai
docker run --rm -v "$PWD/paper:/work" -w /work/aaai h001-aaai-tex:20260526 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

## Artifact Policy

Git should contain source code, configs, runbooks, compact reports, metric summaries, figure specs, and paper source. Large datasets, checkpoints, model caches, feature caches, raw dumps, and row-level JSONL outputs are not Git artifacts; keep them in `local_dataset/`, `release/`, or an external artifact bundle and verify them with counts/checksums before cleanup.

Before rerunning, uploading, transferring, or deleting H001 artifacts, read `docs/reproducibility.md`.

## Navigation

- `summary.md`: current research story, evidence, claim boundary, and paper direction.
- `TODO.md`: current task board.
- `docs/index.md`: dashboard and file ownership pointers.
- `docs/reproducibility.md`: recovery, artifact bundle, dataset/checkpoint, and cleanup runbook.
- `results/h001_geom_reliability/report.md`: compact H001 result summary.
