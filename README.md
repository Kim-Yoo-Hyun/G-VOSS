# RelCompat3D

This repository contains the anonymous submission source, compact experiment
evidence, and Docker entry points for RelCompat3D. The selected submission title
is “RelCompat3D: Predicate–Geometry Compatibility for Re-ranking 3D Scene Graph
Relations.” The consolidated TeX source still carries the preceding working
title and must be synchronized during the pending layout pass.

RelCompat3D estimates predicate–geometry compatibility without using predictor
identity or the source relation score. It combines compatibility with the fixed
source score only during family-aware re-ranking. The paper evaluates
RelCompat3D-Linear and RelCompat3D-MLP on VL-SAT, Open3DSG, and SGFN over one
shared 3DSSG validation target.

## Submission Snapshot

Last updated: 2026-07-22 KST.

The public tree is intentionally limited to:

- paper/: manuscript, supplement, checklist, bibliography, and figure sources;
- src/relcompat3d/: the verified code-and-data supplement allowlist plus the
  point/mesh audit entry point and one transitive calibration dependency needed
  by active Compose services;
- configs/relcompat3d/: the focused Docker image and active compose services;
- scripts/: the active no-family-indicator execution wrapper;
- experiments/RelCompat3D_geom_reliability/: frozen protocols, model locks, and compact
  paper/supplement evidence;
- results/relcompat3d_geom_reliability/: the compact result index and claim summary;
- docs/: workflow rules and the current reproducibility runbook.

Historical experiments, H002 development, literature PDFs and notes, superseded
source adapters, optional runtime configs, caches, and old result mirrors are
not part of the public submission tree. Their local preservation boundary is
documented by archive/README.md.

## Claim Boundary

The reported evidence supports re-ranking fixed relation predictions for
support/contact, proximity, and vertical-order evaluation on a shared 3DSSG
target. RelCompat3D re-ranks proximity and vertical-order candidates and keeps
support/contact candidates in source order.

The repository does not claim:

- broad 3D scene graph SOTA;
- dataset-level generalization;
- predictor-score calibration;
- family-uniform improvement;
- independent physical-validity ground truth;
- solved support/contact compatibility.

See results/relcompat3d_geom_reliability/report.md for the compact result summary and
paper/risk.md for manuscript-facing risks.

## Canonical Paths

| Role | Path |
| --- | --- |
| Selected manuscript | paper/aaai/main_teaser_aaai27.pdf |
| Manuscript source | paper/aaai/main_teaser.tex |
| Supplement source | paper/aaai/supplement.tex |
| Active method lock | experiments/RelCompat3D_geom_reliability/active_method.json |
| Active experiment | experiments/RelCompat3D_geom_reliability/no_family_indicator_v1/ |
| Compact result index | results/relcompat3d_geom_reliability/manifest.json |
| Compact result report | results/relcompat3d_geom_reliability/report.md |
| Docker compose | configs/relcompat3d/compose.structured.yaml |
| Main wrapper | scripts/run_no_family_indicator_v1.sh |
| Recovery runbook | docs/reproducibility.md |

## Quick Validation

Run from the repository root:

~~~bash
docker compose -f configs/relcompat3d/compose.structured.yaml config --quiet
python -m compileall -q src/relcompat3d
jq empty experiments/RelCompat3D_geom_reliability/active_method.json
jq empty results/relcompat3d_geom_reliability/manifest.json
~~~

The active compact outputs can be inspected without the raw datasets. Rerunning
fits, source evaluation, or point/mesh audits requires the external rows and
datasets listed in docs/reproducibility.md.

## Docker Execution

Build or run the active route through Docker:

~~~bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml build no_family_indicator_fit

env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm no_family_indicator_fit

scripts/run_no_family_indicator_v1.sh downstream
~~~

The complete active command map is in
experiments/RelCompat3D_geom_reliability/commands.md.

## Paper Build

~~~bash
docker build -f paper/aaai/Dockerfile.tex \
  -t relcompat3d-aaai27-tex:20260712 paper/aaai

docker run --rm -v "$PWD/paper:/work" -w /work/aaai \
  relcompat3d-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main_teaser.tex
~~~

The current source builds to nine US-Letter pages. Technical content ends and
the references begin on page 7; the references continue on pages 8--9. The
prior horizontal overflow is resolved. One 36.77646 pt first-page vertical
overfull remains before final upload.

## Artifact Policy

Git carries code, Docker configuration, paper source, compact manifests, and
summaries. Raw predictions, verifier rows, datasets, checkpoints, feature
caches, point clouds, meshes, logs, release bundles, and local archives remain
ignored. Restoring or deleting those materials must follow
docs/reproducibility.md.

The latest synchronized candidate bundle is staged locally at
release/relcompat3d_aaai27_openreview_20260726_214500/. It is a verification
candidate, not an upload-ready replacement for the final layout-fixed release.
