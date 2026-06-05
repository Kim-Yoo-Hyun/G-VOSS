# Full Official Validation Scope Contract

Status: `full_official_validation_scope_contract_ready_no_metric_execution`
Created at: `2026-06-03T09:05:41+00:00`

## Boundary

- This is a protocol-freeze artifact, not metric evidence.
- The current 127-scan results remain current evidence until full-validation artifacts are regenerated.
- H001-Mini is hypothesis/feasibility evidence only.
- Final method design, verifier policy, counterfactuals, and `p_geom_valid` calibration are train/train-dev-derived.

## Scope

| Item | Count |
| --- | --- |
| completed hardened scans | 127 |
| completed hardened contexts | 388 |
| completed hardened GT rows | 7505 |
| completed hardened H001-family GT rows | 2545 |
| full validation scans | 157 |
| full validation contexts | 548 |
| full validation GT-positive directed pairs | 7720 |
| full validation candidate directed pairs | 36808 |
| full validation GT rows | 11254 |
| full validation H001-family GT rows | 3972 |
| expected VL-SAT prediction rows | 957008 |

## H001 Family Counts

| Family | GT rows |
| --- | --- |
| support_contact | 1816 |
| proximity | 1766 |
| relative_vertical | 390 |

## All Family Counts

| Family | GT rows |
| --- | --- |
| attachment_deferred | 1205 |
| proximity | 1766 |
| relative_horizontal | 5474 |
| relative_vertical | 390 |
| support_contact | 1816 |
| unsupported_first_pass | 603 |

## Local Readiness

| Item | Ready |
| --- | --- |
| raw 3RScan geometry | 157/157 scans |
| VL-SAT raw geometry | 157/157 scans |
| Open3DSG mesh/texture | 157/157 scans |
| Open3DSG sequence | 157/157 scans |
| existing VL-SAT hardened staged root | 127/157 scans |
| existing Open3DSG h001 runtime views | 127/157 scans |
| existing Open3DSG h001 runtime preprocess | 377/548 contexts |
| existing Open3DSG training_repro views | 30/157 scans |
| existing Open3DSG training_repro preprocess | 155/548 contexts |

## Promotion Gates

- `regenerate_vlsat_full_validation_staging_and_raw_dump_under_full_validation_paths`
- `export_vlsat_full_validation_predictions_and_ground_truth_jsonl`
- `run_geometry_join_with_frozen_train_dev_calibrators`
- `run_vlsat_metrics_controls_gt_eval_bootstrap_ci_and_report`
- `decide_open3dsg_checkpoint_route_after_non_avg_retry_or_explicit_waiver`
- `regenerate_open3dsg_full_validation_payload_views_preprocess_features_raw_dump`
- `run_open3dsg_identity_adapter_geometry_metrics_bootstrap_failure_rows_caveats`
- `update_paper_tables_only_after_all_source_specific_caveats_are_known`

## Warnings

- `scope_contract_only_no_metric_execution`
- `do_not_edit_current_127_scan_tables_by_denominator_substitution`
- `vlsat_full_validation_runtime_docker_service_must_be_added_or_documented_before_paper_metric_promotion`
- `open3dsg_full_validation_coverage_must_be_recomputed_after_preprocess_feature_raw_dump_regeneration`
- `existing_vlsat_hardened_staged_root_only:127/157`
- `existing_open3dsg_h001_runtime_preprocess_only:377/548`
