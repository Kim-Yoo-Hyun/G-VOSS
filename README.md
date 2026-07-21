# RelCompat3D Research Repository

This repository contains the H001/RelCompat3D research workspace for reliable 3D Scene Graph relations. The active paper is titled `Beyond Semantic Confidence: Relation-Consistent Geometric Re-ranking for 3D Scene Graphs`. RelCompat3D reports family-specific Linear heads and a compact shared MLP as two compatibility capacities whose inputs exclude predictor identity and the source relation score, enforces known relation transformations by score averaging, and measures Recall--Violation trade-offs under family-aware re-ranking. The paper-facing scope is `support_contact`, `proximity`, and `relative_vertical`, evaluated across VL-SAT, Open3DSG, and SGFN on one shared 3DSSG target. H001 remains an internal experiment identifier.

## Core Question

3D Scene Graph relation predictors can assign high semantic confidence to relations that are physically inconsistent with the subject-object geometry. This project asks whether relation confidence agrees with relation-level geometry, and whether a scoped compatibility layer can reduce top-K violations without hiding recall trade-offs.

## Current H001 State

- Claim: relation reliability based on separate predicate, geometry, and
  source-score factors, evaluated
  across three predictors on a shared 3DSSG target; no dataset-level,
  family-uniform, SOTA, or best-fusion claim.
- Main evidence: VL-SAT, Open3DSG, and SGFN evaluations over 548 contexts and
  3,972 in-scope exact-label relations.
- Novelty mechanism: linked-counterfactual margin fitting plus exact
  transformation averaging yields source-score-excluded compatibility;
  family-aware re-ranking uses it within proximity/vertical relations while
  preserving support/contact ordering.
- Active framework: the strict train-only `no_family_indicator_v1` refit uses
  `T_i=p_i`; the family label selects the head and procedure but is not a
  constant feature. Its three heads store 66 parameters, 43 of which are used
  by the primary proximity/vertical path. A shared 69-parameter MLP using the
  same targets, objective, transformations, product utility, and ranking rule
  is the second proposed capacity.
- Transfer boundary: an application without target-specific refitting is
  complete on ReplicaSSG/FROSS. The family-aware product improves both metrics at
  K=10 and K=50, while heavily quantized source scores make it nearly inert at
  K=100. The target informed prior diagnostics, candidate recall is capped at
  44.19%, and support/contact is unmapped; this is a transfer stress test rather
  than dataset-level generalization evidence.
- Canonical PDFs: `paper/aaai/main_aaai27.pdf`,
  `supplement_aaai27.pdf`, and `reproducibility_checklist_aaai27.pdf`.
- Current verified upload bundle:
  `release/h001_aaai27_openreview_20260720_084307/`; it selects the teaser
  manuscript and includes matched ablations, compact active-method
  external-transfer evidence, and independently rebuildable anonymous source.
- Cleanup state: Replica/FROSS raw archives, runtime, weights, source clones,
  and shards are absent; compact development rows and summaries are retained.

## Canonical H001 Paths

- Focused Docker entry point: `configs/h001/compose.structured.yaml`
- Active method pointer: `experiments/H001_geom_reliability/active_method.json`
- Frozen method/model: `experiments/H001_geom_reliability/no_family_indicator_v1/fit/`
- Primary family-aware evaluation: `experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/routed_comparators/`
- Synchronized all-family comparisons: `experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/structured_main/`
- Matched-procedure strong comparators: `experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/routed_comparators/`
- RelCompat3D-MLP model/evaluation: `experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/nonlinear/`
- Matched MLP controls and surface audit: `experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/{mlp_ablation,mlp_surface_audit}/`
- Open3DSG coverage sensitivity: `experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/open3dsg_route/`
- ReplicaSSG active-method transfer stress test: `experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/external_transfer/`
- Paper-facing family-aware K=50/100 ablations: `experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/routed_ablation/`
- All-K scan-cluster intervals: `experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/scan_cluster/`
- CPU re-ranking benchmark: `experiments/H001_geom_reliability/no_family_indicator_v1/evaluation/runtime/`
- Compact result summary: `results/h001_geom_reliability/report.md`
- Paper figures: `paper/generated/figures/`
- Active AAAI source and canonical PDFs: `paper/aaai/`
- Current verified upload bundle:
  `release/h001_aaai27_openreview_20260720_084307/`.
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
  -f configs/h001/compose.structured.yaml run --rm support_contact_routing
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm support_routing_scan_cluster
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm routed_public_ablation_evaluation
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm routed_comparator_evaluation
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm supervision_matched_nonlinear
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm open3dsg_official_route_sensitivity
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm external_dataset_transfer
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

Use the verified 2026-07-17 field bundle listed above for upload; older bundles
are historical snapshots.

## Artifact Policy

Git should contain source code, configs, runbooks, compact reports, metric summaries, figure specs, and paper source. Large datasets, checkpoints, model caches, feature caches, raw dumps, and row-level JSONL outputs are not Git artifacts; keep them in `local_dataset/`, `release/`, or an external artifact bundle and verify them with counts/checksums before cleanup.

Before rerunning, uploading, transferring, or deleting H001 artifacts, read `docs/reproducibility.md`.

## Navigation

- `summary.md`: current research story, evidence, claim boundary, and paper direction.
- `TODO.md`: current task board.
- `docs/index.md`: documentation index and file ownership pointers.
- `docs/reproducibility.md`: recovery, artifact bundle, dataset/checkpoint, and cleanup runbook.
- `results/h001_geom_reliability/report.md`: compact H001 result summary.
