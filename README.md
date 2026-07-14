# RelCompat3D Research Repository

This repository contains the H001/RelCompat3D research workspace for reliable 3D Scene Graph relations. The active paper is titled `Beyond Semantic Confidence: Relation-Algebra-Constrained Geometric Compatibility for 3D Scene Graph Relations`. RelCompat3D learns predictor-agnostic predicate--geometry compatibility without source scores, applies relation-algebra projection, and reports recall--violation trade-offs under re-ranking. The paper-facing scope is `support_contact`, `proximity`, and `relative_vertical`, evaluated across VL-SAT, Open3DSG, and SGFN on one shared 3DSSG target. H001 remains an internal experiment identifier.

## Core Question

3D Scene Graph relation predictors can assign high semantic confidence to relations that are physically inconsistent with the subject-object geometry. This project asks whether relation confidence agrees with relation-level geometry, and whether a scoped compatibility layer can reduce top-K violations without hiding recall trade-offs.

## Current H001 State

- Claim: predictor-agnostic, factor-isolated relation reliability on
  geometry-identifiable families under a shared 3DSSG target; no dataset-level,
  family-uniform, SOTA, or best-fusion claim.
- Main evidence: VL-SAT, Open3DSG, and SGFN evaluations over 548 contexts and
  3,972 in-scope exact-label relations.
- Novelty mechanism: a 3DSSG-only structured-development branch finds that
  linked-counterfactual margin fitting plus exact relation-algebra projection
  is the sole candidate passing structural and three-source continuity gates;
  it is now the promoted main compatibility model.
- Transfer boundary: dataset-level generalization is out of scope;
  ReplicaSSG/FROSS is archived development provenance, not submission evidence.
- Canonical PDFs: `paper/aaai/main_aaai27.pdf`,
  `supplement_aaai27.pdf`, and `reproducibility_checklist_aaai27.pdf`.
- Active upload bundle: `release/h001_aaai27_openreview_20260714_170829/`;
  outer/inner checksums, archive integrity, manifest gates, and author-path
  scans pass.
- Cleanup state: Replica/FROSS raw archives, runtime, weights, source clones,
  and shards are absent; compact development rows and summaries are retained.

## Canonical H001 Paths

- Focused Docker entry point: `configs/h001/compose.structured.yaml`
- Frozen method/model: `experiments/H001_geom_reliability/relation_algebra_v1/`
- Promoted synchronized evaluation: `experiments/H001_geom_reliability/structured_main_v1/evaluation/`
- Fixed-model K=50/100 ablations: `experiments/H001_geom_reliability/structured_ablation_v1/evaluation/`
- Compact result summary: `results/h001_geom_reliability/report.md`
- Paper figures: `paper/generated/figures/`
- Active AAAI source and canonical PDFs: `paper/aaai/`
- Verified upload bundle: `release/h001_aaai27_openreview_20260714_170829/`
- Recovery, transfer, and cleanup authority: `docs/reproducibility.md`

The current Docker retention matrix is also owned by
`docs/reproducibility.md`: keep the active structured-evaluation, SGFN
full-reproduction, and AAAI-27 TeX images; the old AAAI-26, non-main proposal,
and de-scoped ReplicaSSG/FROSS images are cleanup candidates.

The dated `summary_0713.md` file is a historical handoff snapshot. Use
`summary.md` and `TODO.md` for the current state.

## Repository Structure

- `src/`: core RelCompat3D Python code for staging, geometry evidence, adapters, metrics, bootstrap CI, and table generation.
- `scripts/`: shell wrappers for long-running reproducible jobs.
- `configs/`: Dockerfiles and compose files.
- `experiments/`: source-specific experiment records, ablations, analysis outputs, and row-level runtime result locations.
- `results/`: lightweight paper-facing summaries, compact tables, reports, figure specs, and locked manifests.
- `docs/`: workflow rulebooks, navigation index, and reproducibility runbook.
- `literature/`: literature notes and paper cards. Existing internal layout is preserved.
- `paper/`: manuscript source, figures, appendix/risk planning, and venue files.
- `archive/`: preserved hypothesis records, old code/output, superseded venue files, optional expansion tracks, caches, and files preserved instead of deleted.
- `local_dataset/`, `release/`, `logs/`: ignored local data, external bundle staging, and runtime logs.

## Execution

Run paper-facing experiments through Docker from the repository root:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm relation_algebra_development
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm structured_main_evaluation
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm scan_cluster_sensitivity
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm structured_ablation_evaluation
```

Main configuration entry points:

- `configs/h001/compose.structured.yaml`: focused strict train-only main-method and synchronized-evaluation services.
- `configs/h001/compose.yaml`: full historical recovery, source-adapter, and optional-analysis service registry.
- `configs/h001/Dockerfile`: lightweight RelCompat3D Python image.
- `configs/open3dsg/compose.open3dsg.yaml`: Open3DSG reproduction/runtime services.
- `configs/qwen_vl/compose.qwen.yaml`: Qwen-VL extension runtime services.

Useful source-level checks:

```bash
docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm env_check
docker compose -f configs/qwen_vl/compose.qwen.yaml run --rm qwen_vl_cache_verify
```

Build the current AAAI paper source with:

```bash
docker build -f paper/aaai/Dockerfile.tex -t h001-aaai27-tex:20260712 paper/aaai
docker run --rm -v "$PWD/paper:/work" -w /work/aaai h001-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The verified AAAI-27 field files are under
`release/h001_aaai27_openreview_20260714_170829/`.

## Artifact Policy

Git should contain source code, configs, runbooks, compact reports, metric summaries, figure specs, and paper source. Large datasets, checkpoints, model caches, feature caches, raw dumps, and row-level JSONL outputs are not Git artifacts; keep them in `local_dataset/`, `release/`, or an external artifact bundle and verify them with counts/checksums before cleanup.

Before rerunning, uploading, transferring, or deleting H001 artifacts, read `docs/reproducibility.md`.

## Navigation

- `summary.md`: current research story, evidence, claim boundary, and paper direction.
- `TODO.md`: current task board.
- `docs/index.md`: documentation index and file ownership pointers.
- `docs/reproducibility.md`: recovery, artifact bundle, dataset/checkpoint, and cleanup runbook.
- `results/h001_geom_reliability/report.md`: compact H001 result summary.
