# H001 Docker Entry Point

Last updated: 2026-07-22 KST.

compose.structured.yaml is the only public experiment compose file. It exposes
the active no_family_indicator_v1 fitting and evaluation services and mounts
the repository at /workspace.

## Validate

~~~bash
docker compose -f configs/h001/compose.structured.yaml config --quiet
~~~

## Main Route

~~~bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm no_family_indicator_fit

env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm no_family_indicator_freeze_initial

scripts/run_no_family_indicator_v1.sh downstream
~~~

## Included Services

- no_family_indicator_fit
- no_family_indicator_freeze_initial
- no_family_indicator_structured_main
- no_family_indicator_support_routing
- no_family_indicator_open3dsg_route
- no_family_indicator_nonlinear
- no_family_indicator_freeze_downstream
- no_family_indicator_routed_comparators
- no_family_indicator_routed_ablation
- relcompat3d_mlp_ablation
- no_family_indicator_scan_cluster
- no_family_indicator_structured_scan_cluster
- no_family_indicator_surface_audit
- relcompat3d_mlp_surface_audit
- no_family_indicator_held_out_primitive
- no_family_indicator_counterfactual_sensitivity
- no_family_indicator_candidate_build
- no_family_indicator_candidate_figures
- no_family_indicator_runtime
- no_family_indicator_external_transfer

The corresponding protocols and compact outputs live under
experiments/H001_geom_reliability/no_family_indicator_v1/.

## Data Boundary

The repository contains compact outputs, not the row-level source inputs.
Fitting and numerical regeneration require the external artifacts listed in
docs/reproducibility.md. A GitHub-only checkout can validate code, configs,
locks, JSON, and the stored summaries but cannot reproduce source inference or
point/mesh measurements without those external inputs.

The manuscript image is independently defined by paper/aaai/Dockerfile.tex.
