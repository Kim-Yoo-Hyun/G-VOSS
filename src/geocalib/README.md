# RelCompat3D Python Entry Points

These scripts are executed directly by the focused H001 Docker Compose file.
They use file-relative imports and require only the pinned packages in
configs/h001/Dockerfile.

## Functional Groups

- fit_no_family_indicator.py and fit_strict_train_only_calibrators.py:
  train-only Linear fitting and locks;
- run_supervision_matched_nonlinear.py: matched compact MLP estimator;
- run_structured_main_evaluation.py, run_routed_comparator_evaluation.py, and
  run_routed_ablation_evaluation.py: main rankings, baselines, and controls;
- run_support_contact_routing.py and run_support_routing_scan_cluster.py:
  family-sequence and support/contact preservation;
- run_relcompat3d_mlp_ablation.py and
  run_relcompat3d_mlp_surface_audit.py: matched MLP controls and audit;
- run_orthogonal_geometry_audit.py and
  run_held_out_primitive_evaluation.py: point/mesh alternative-construct and
  feature-removal checks;
- run_counterfactual_threshold_sensitivity.py: train-only construction
  sensitivity; `export_calibration.py` supplies its frozen counterfactual row
  construction;
- benchmark_relcompat3d_runtime.py: bounded post-load CPU timing;
- run_external_dataset_transfer.py: ReplicaSSG/FROSS transfer stress test;
- build_no_family_indicator_candidate.py and
  render_no_family_indicator_candidate_figures.py: candidate paper artifacts.

Additional shared scoring and feature logic is contained in the remaining
allowlisted modules. Generated rows, caches, checkpoints, and model payloads do
not belong under src/.
