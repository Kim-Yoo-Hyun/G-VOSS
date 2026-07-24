# RelCompat3D Python Modules

The filenames use a short `verb_target.py` convention. Docker services call the
training, evaluation, audit, and artifact entry points directly; shared modules
provide features, relation-consistency logic, controls, metrics, and paths. All
modules use file-relative imports and the packages pinned in
`configs/relcompat3d/Dockerfile`.

## Functional Groups

- Training: `build_training_rows.py`, `fit_train_only.py`, `fit_linear.py`,
  `fit_mlp.py`, and `fit_factor_controls.py`.
- Core logic: `compatibility_features.py`, `relation_consistency.py`,
  `control_utils.py`, `evaluate_metrics.py`, and `paths.py`.
- Main evaluation: `evaluate_main.py`, `evaluate_comparators.py`,
  `evaluate_linear_controls.py`, `evaluate_mlp_controls.py`, and
  `evaluate_component_removals.py`.
- Family and uncertainty checks: `evaluate_support_order.py`,
  `evaluate_support_intervals.py`, and `evaluate_scan_intervals.py`.
- Construct checks: `audit_point_mesh.py`, `audit_mlp_point_mesh.py`,
  `evaluate_feature_removal.py`, and `evaluate_counterfactuals.py`.
- Additional evidence: `benchmark_runtime.py`, `evaluate_open3dsg.py`, and
  `evaluate_transfer.py`.
- Paper artifacts: `build_paper_artifacts.py` and `render_paper_figures.py`.

Generated rows, caches, checkpoints, and model payloads do not belong under
`src/`.
