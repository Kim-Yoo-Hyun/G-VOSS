# VL-SAT Source

This source currently provides the controlled-anchor full-validation H001
result. The older 127-scan H001 result is retained as historical/sensitivity
evidence.

The Docker table builder reads locked artifacts from:

```text
archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/evaluation/vlsat_closed_set/
```

Do not retune scan scope, verifier thresholds, or calibration models from this experiment root.

## Full Official Validation Route

Status:

```text
vlsat_full_validation_metric_bundle_ready
vlsat_full_validation_failure_analysis_ready
```

The paper-facing primary route now uses the full official `3DSSG_subset`
validation split. VL-SAT is the controlled-anchor source, while Open3DSG
`recovery_relaxed_views_min2/` is the primary open-vocabulary source.
Scope contract:

```text
results/h001_geom_reliability/full_validation_transition/scope_contract/
```

Target full-validation VL-SAT scope:

- 157 validation scans
- 548 contexts
- 36,808 candidate directed pairs
- 957,008 expected prediction rows under the all-non-`none` predicate export policy
- 11,254 GT rows
- 3,972 H001-family GT rows

Full-validation output root:

```text
experiments/H001_geom_reliability/sources/vlsat/full_validation/
```

Current Docker-ready artifacts:

- source-local README: `full_validation/README.md`
- stage: `full_validation/stage/`
- runtime record: `full_validation/runtime_record/`
- raw preflight: `full_validation/raw_preflight/`
- raw run record: `full_validation/raw/run_20260604_204428.md`
- adapter export: `full_validation/adapter/`
- geometry join: `full_validation/geometry/`
- metric eval: `full_validation/metrics/`
- GT verifier eval: `full_validation/gt_eval/`
- bootstrap CI: `full_validation/bootstrap_ci/`
- failure rows: `full_validation/failure_rows/`
- qualitative failure queue/inspection: `full_validation/failure_cases/`

Current result:

- 157/157 faithful staged scans
- reference-scan identity aligned PLYs use symlinks to avoid duplicate storage
- runtime image: `h001-open3dsg-repro:cu128`
- checkpoint files: 16/16 present with checksums recorded
- raw preflight: `ready_to_run`
- preflight errors: 0
- preflight warnings: 1 expected `src_lib_pointnet_graph` import-shim warning
- raw dump: `raw_dump_ready`, rows `548`, directed pairs `36,808`, errors `0`
- adapter export: `ready`, predictions `957,008`, ground-truth rows `11,254`,
  validation errors `0`
- geometry join: `ready`, rows preserved `957,008/957,008`,
  primary-family rows `220,848`, validation errors `0`
- metrics: `ready`
- GT verifier eval: `ready`, positives/negatives `3,972/3,972`, AUROC `0.9772`
- bootstrap CI: `ready`, 1,000 subgraph resamples, warnings `0`
- failure rows: `failure_analysis_real_ready`, rows `59,841`, validation
  errors `0`, visual-audit queue rows `2,897`
- qualitative failure sample: `failure_case_sample_ready`, 36 selected cases,
  all high-severity and unique
- qualitative failure inspection: `qualitative_case_inspection_ready`, 36
  cases, 28 demoted by geometry-aware reranking, 8 promoted/retained, and 7
  violated rows with `p_geom_valid > 0.9`

Key full-validation metric pattern:

| condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| semantic_only | 0.9272 | 0.9635 | 0.0268 | 0.0476 |
| probabilistic_recalibrated | 0.9305 | 0.9688 | 0.0229 | 0.0404 |
| rule_verified_point_subtype | 0.9257 | 0.9627 | 0.0000 | 0.0000 |
| control_family_specific_p_geom_valid | 0.9288 | 0.9683 | 0.0206 | 0.0333 |

This is now valid VL-SAT full-validation metric and failure-taxonomy evidence
for the current H001 families. Treat `failure_cases/` as deterministic
qualitative reviewer-defense evidence, not as an independent human visual
audit.
