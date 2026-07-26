# RelCompat3D Submission Commands

Last updated: 2026-07-27 KST

Run commands from the repository root. Paper experiments use Docker; the
compact tracked artifacts may be inspected without external data.

## Row-Level Paper Reproduction and Candidate Oracle

Build the pseudonymized, geometry-free row bundle from gated inputs:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_export_rows
```

Regenerate main-paper Tables 1--3, Figure 3 data and rendering, and the
canonical tolerance report from that bundle:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_reproduce_rows
```

Compute candidate-pool coverage and constrained oracle Recall:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_candidate_oracle
```

The row bundle remains excluded from the public ZIP until derived-row
redistribution is confirmed under the dataset terms.

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

## Direct Component Removals

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_component_removals
```

This evaluates RelCompat3D-Linear after removing either the linked pairwise
term or inference-time transformation averaging while retaining the same
candidate set and family-aware route.

## Score Robustness and Closest Simple Baselines

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_score_robustness
```

This post-hoc run checks the active product utility under a frozen set of
monotonic source-score mappings and evaluates Hard-tail, Hard-drop, and a
training-positive robust-density baseline. It reads the hash-locked Tier-B rows
documented by `score_robustness_v1/protocol.json`, reproduces the canonical
identity points before accepting results, and does not select a replacement
method.

## Routing Constraints and Construct Dependence

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_routing_constraints

env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_construct_dependence
```

The first command compares the active family-slot route with matched
constraint relaxations while preserving the frozen candidates and model
scores. The second command hash-verifies the construct-dependence matrix and
the existing feature-removal, uncertainty-policy, component-removal, and
point/mesh evidence.

## Component Diagnostics and Five-Seed Robustness

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_component_diagnostics

env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_seed_robustness
```

The first command compares Full, no-pairwise-loss, and
no-transformation-averaging conditions for both promoted estimators. It
records held-out linked-pair margins, transformation-error distributions,
transformed-view top-\(K\) membership consistency, and aggregate metrics. The
second command reruns the deterministic Linear fit and the MLP under five
predeclared seed identifiers while holding constructed rows fixed. Neither
command changes the active method lock.

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
