# RelCompat3D Docker Entry Point

Last updated: 2026-07-29 KST.

compose.structured.yaml is the only public experiment compose file. It exposes
the active no_family_indicator_v1 fitting and evaluation services and mounts
the repository at /workspace.

## Validate

~~~bash
docker compose -f configs/relcompat3d/compose.structured.yaml config --quiet
~~~

## Main Route

~~~bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm no_family_indicator_fit

env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm no_family_indicator_freeze_initial

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
- relcompat3d_component_removals
- relcompat3d_score_robustness
- relcompat3d_routing_constraints
- relcompat3d_construct_dependence
- relcompat3d_component_diagnostics
- relcompat3d_seed_robustness
- relcompat3d_export_rows
- relcompat3d_reproduce_rows
- relcompat3d_candidate_oracle
- no_family_indicator_runtime
- no_family_indicator_external_transfer

The active method protocols and compact outputs live under
`experiments/RelCompat3D_geom_reliability/no_family_indicator_v1/`. The
post-hoc score-robustness, routing-control, construct-dependence,
component-diagnostic, and seed-robustness protocols and outputs live under
sibling versioned directories and do not alter the active method.

The row export separates gated preprocessing from public-style metric
regeneration. `relcompat3d_export_rows` removes original identifiers and raw
geometry. `relcompat3d_reproduce_rows` regenerates Tables 1--3, Figure 3, and
canonical tolerance checks from the derived bundle. The bundle remains ignored
until its redistribution status is confirmed. `relcompat3d_candidate_oracle`
uses the same rows to quantify fixed-candidate Recall ceilings.

## Data Boundary

The repository contains compact outputs, not the row-level source inputs.
Fitting and numerical regeneration require the external artifacts listed in
docs/reproducibility.md. A GitHub-only checkout can validate code, configs,
locks, JSON, and the stored summaries but cannot reproduce source inference or
point/mesh measurements without those external inputs.

The manuscript image is independently defined by paper/aaai/Dockerfile.tex.
