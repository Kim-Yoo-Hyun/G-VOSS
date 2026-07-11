# H002 Runtime Scripts

## Core Compatibility

- `preflight.py`: mount/protocol/H001 read-only checks
- `materialize_routes.py`: route input materialization
- `audit_materialization_schema.py`: leakage and schema audit
- `make_grouped_split.py`: grouped train/dev split
- `run_grouped_eval.py`: semantic, geometry, concat, compatibility and controls
- `run_official_metric.py`: shared feature/model helpers used by reranking

## Source Reranking

- `materialize_source_reranking_candidates.py`
- `audit_source_reranking_materialization_schema.py`
- `run_source_reranking_metric.py`
- `bootstrap_source_reranking_ci.py`
- `run_source_reranking_sensitivity.py`

## Route Analysis

- `audit_relative_horizontal_frame_route.py`
- `run_relative_horizontal_route_scorer.py`
- `run_relative_horizontal_split_route_scorer.py`

## Paper Assets

- `refresh_main_validation_table_after_lateral_lock.py`
- `build_qualitative_evidence_package.py`
- `build_paper_assets.py`

Historical hypothesis wrappers and scripts for learned G_e, p_obs/p_rel,
support/contact repair loops, and transition scaffolds were removed because they
do not implement the current paper claim.
