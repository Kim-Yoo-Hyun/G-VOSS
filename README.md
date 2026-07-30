# RelCompat3D

This repository contains the anonymous submission source, compact experiment
evidence, and Docker entry points for RelCompat3D. The selected submission title
is “RelCompat3D: Re-Ranking 3D Scene Graph Relations with Geometric Evidence.”

RelCompat3D estimates predicate–geometry compatibility without using predictor
identity or the source relation score. It combines compatibility with the fixed
source score only during family-aware re-ranking. The paper evaluates
RelCompat3D-Linear and RelCompat3D-MLP on VL-SAT, Open3DSG, and SGFN over
shared 3DSSG validation scenes.

## Submission Snapshot

Last updated: 2026-07-30 KST.

The public tree is intentionally limited to:

- paper/: manuscript, supplement, checklist, bibliography, and figure sources;
- src/relcompat3d/: the verified code-and-data supplement allowlist plus the
  point/mesh audit entry point and one transitive calibration dependency needed
  by active Compose services;
- configs/relcompat3d/: the focused Docker image and active compose services;
- scripts/: the active no-family-indicator execution wrapper;
- experiments/RelCompat3D_geom_reliability/: frozen protocols, model hashes, and
  compact paper/supplement evidence; fitted parameter payloads are restored
  from the private recovery bundle;
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

See results/relcompat3d_geom_reliability/report.md for the compact result
summary and paper/review.md for the integrated reviewer-risk assessment.

## Canonical Paths

| Role | Path |
| --- | --- |
| Selected manuscript | paper/aaai/main_aaai27.pdf |
| Manuscript source | paper/aaai/main.tex |
| Supplement source | paper/aaai/supplement.tex |
| Active method lock | experiments/RelCompat3D_geom_reliability/active_method.json |
| Active experiment | experiments/RelCompat3D_geom_reliability/no_family_indicator_v1/ |
| Post-hoc score robustness | experiments/RelCompat3D_geom_reliability/score_robustness_v1/ |
| Routing constraint controls | experiments/RelCompat3D_geom_reliability/routing_controls_v1/ |
| Construct-dependence package | experiments/RelCompat3D_geom_reliability/construct_dependence_v1/ |
| Compact result index | results/relcompat3d_geom_reliability/manifest.json |
| Compact result report | results/relcompat3d_geom_reliability/report.md |
| Docker compose | configs/relcompat3d/compose.structured.yaml |
| Main wrapper | scripts/run_no_family_indicator_v1.sh |
| Recovery runbook | docs/reproducibility.md |

## Fresh-Server Setup

Clone the public release branch and validate the Docker configuration:

~~~bash
git clone --branch release https://github.com/Kim-Yoo-Hyun/3DSG.git RelCompat3D
cd RelCompat3D
docker compose -f configs/relcompat3d/compose.structured.yaml config --quiet
~~~

### Official Data and Source Environments

Use the original distributions and follow their terms and setup instructions:

- [3RScan toolkit](https://github.com/WaldJohannaU/3RScan) and
  [3RScan project/access page](https://waldjohannau.github.io/RIO/)
- [3DSSG dataset and documentation](https://3dssg.github.io/)
- [VL-SAT official implementation](https://github.com/wz7in/CVPR2023-VLSAT)
- [SGFN/3DSSG official implementation](https://github.com/ShunChengWu/3DSSG)
- [Open3DSG official implementation](https://github.com/boschresearch/Open3DSG)

This repository does not redistribute 3RScan/3DSSG data, dataset-derived
training rows, pseudonymized evaluation rows, or third-party checkpoints.

### Public Model Links

- [RelCompat3D fitted models](https://drive.google.com/file/d/1DaZoibKFyPS681e728Tzs613qscMgv4u/view?usp=drive_link)
- [Selected Open3DSG checkpoint](https://drive.google.com/file/d/1PJNduscoRAB6cQcggBOo-ErzkiBs_QDG/view?usp=drive_link)

VL-SAT and SGFN checkpoints are provided through their official repositories
above. The expected Open3DSG checkpoint path is:

~~~text
local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/
363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/
epoch=13-step=13104.ckpt
~~~

Paper-level numerical regeneration requires authorized users to construct the
derived rows with `relcompat3d_export_rows`. The resulting files belong at:

~~~text
experiments/RelCompat3D_geom_reliability/
row_reproduction_v1/artifacts/derived_rows/
~~~

Build the pinned environment and regenerate Tables 1--3 and Figure 3:

~~~bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml \
  build relcompat3d_reproduce_rows

env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml \
  run --rm relcompat3d_reproduce_rows
~~~

The regenerated CSV, LaTeX, SVG, PNG, PDF, and numerical validation files are
written to:

~~~text
experiments/RelCompat3D_geom_reliability/row_reproduction_v1/regenerated/
~~~

Figure 3 is regenerated by the command above. The reconstructed Figure 2 XY
panel can be regenerated with the same Docker image:

~~~bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml \
  run --rm --entrypoint python relcompat3d_reproduce_rows \
  /workspace/paper/generated/generate_figure2_xy.py
~~~

Its SVG, PDF, outlined-PDF, and PNG outputs are written under
`paper/generated/`.

The expected validation covers 291 canonical cells with tolerance
\(10^{-12}\). This paper-level route does not require source-predictor
inference after the derived rows have been created. Full fitting and
evaluation require the licensed inputs listed in `docs/reproducibility.md`.

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
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
~~~

The current source builds to nine US-Letter pages. Technical content ends on
page 7, and the references occupy pages 8--9. The
prior horizontal overflow and first-page vertical overfull are resolved.

## Artifact Policy

Git carries code, Docker configuration, paper source, compact manifests, and
summaries. Raw predictions, verifier rows, datasets, checkpoints, feature
caches, point clouds, meshes, logs, release bundles, and local archives remain
ignored. Restoring or deleting those materials must follow
docs/reproducibility.md.

The latest synchronized post-acceptance candidate bundle is staged locally at
`release/relcompat3d_aaai27_openreview_20260729_223000/`. Its main,
supplement, checklist, code/data ZIP, and manifests have passed the release
verification described in `docs/reproducibility.md`. The review submission
does not upload this Code and Data Supplement or a Media Supplement.
