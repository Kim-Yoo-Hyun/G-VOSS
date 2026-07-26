# RelCompat3D Result Index

This directory is a lightweight index for the current RelCompat3D manuscript. The
canonical numerical artifacts are under
`experiments/RelCompat3D_geom_reliability/no_family_indicator_v1/evaluation/`; they
are not duplicated here.
The post-hoc P0 score-mapping and simple-baseline artifacts are under the
sibling `score_robustness_v1/evaluation/` directory and do not change the
active method.
The P0 routing controls and construct-dependence package are under
`routing_controls_v1/evaluation/` and `construct_dependence_v1/evaluation/`.
They are post-hoc claim audits and do not change the active method.
Matched component diagnostics and the predeclared five-seed fitting analysis
are under `component_diagnostics_v1/evaluation/` and
`seed_robustness_v1/evaluation/`. They retain the active method and report
bounded mechanism and fitting-variation evidence.
The row-level paper check and fixed-candidate Recall upper bounds are under
`row_reproduction_v1/evaluation/` and `candidate_oracle_v1/evaluation/`.
The former regenerates Tables 1--3 and Figure 3 data; the latter separates
candidate-pool coverage, routing constraints, and remaining ranking headroom.

- `manifest.json` maps each paper or supplement evidence class to its
  canonical compact artifact.
- `report.md` summarizes the active result and its claim boundary.

Historical pre-promotion tables and interval summaries are preserved only in
the ignored local snapshot
`archive/local/pre_submission_20260722/previous_archive/results/`
under the historical RelCompat3D compact-result subtree.
