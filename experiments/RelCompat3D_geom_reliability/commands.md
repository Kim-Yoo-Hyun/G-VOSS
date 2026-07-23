# RelCompat3D Submission Commands

Last updated: 2026-07-22 KST

Run commands from the repository root. Paper experiments use Docker; the
compact tracked artifacts may be inspected without external data.

## Validate the Tracked Contract

```bash
docker compose -f configs/relcompat3d/compose.structured.yaml config --quiet
jq '.' experiments/RelCompat3D_geom_reliability/active_method.json
jq '.' experiments/RelCompat3D_geom_reliability/no_family_indicator_v1/fit/final_lock.json
```

## Fit and Evaluate the Active Method

Exact reruns require the official or derived row-level inputs declared by the
protocol files and mounted as described in `docs/reproducibility.md`.

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm no_family_indicator_fit
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm no_family_indicator_freeze_initial
bash scripts/run_no_family_indicator_v1.sh initial
bash scripts/run_no_family_indicator_v1.sh downstream
```

The `initial` phase produces the structured main result, support-routing
comparison, Open3DSG route sensitivity, and nonlinear estimator. The
`downstream` phase produces matched comparators, Linear controls, scan-level
intervals, point/mesh audit, feature-removal analysis, and counterfactual
sensitivity.

## MLP, Runtime, and Transfer Evidence

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm relcompat3d_mlp_ablation
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm relcompat3d_mlp_surface_audit
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm no_family_indicator_runtime
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm no_family_indicator_external_transfer
```

The transfer command reproduces a previously observed ReplicaSSG/FROSS stress
test. It is not an independent cross-dataset confirmation.

## Inspect Paper-Facing Outputs

```bash
jq '.validation' \
  experiments/RelCompat3D_geom_reliability/no_family_indicator_v1/evaluation/routed_comparators/manifest.json
sed -n '1,220p' \
  experiments/RelCompat3D_geom_reliability/no_family_indicator_v1/evaluation/routed_comparators/summary.md
sed -n '1,220p' results/relcompat3d_geom_reliability/report.md
```

## Build the Manuscript and Supplement

```bash
docker build -f paper/aaai/Dockerfile.tex -t relcompat3d-aaai27-tex:20260712 paper/aaai
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD:/workspace" -w /workspace/paper/aaai \
  relcompat3d-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main_teaser.tex
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD:/workspace" -w /workspace/paper/aaai \
  relcompat3d-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error supplement.tex
```

Do not treat ignored local archives, old release bundles, or regenerated
candidate-paper directories as submission artifacts.
