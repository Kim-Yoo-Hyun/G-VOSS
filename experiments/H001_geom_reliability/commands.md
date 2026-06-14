# Commands

Last updated: 2026-06-04

Run from the repository root.

## Build

```bash
docker compose -f experiments/H001_geom_reliability/compose.yaml build
```

## Generate Tables And Report

```bash
docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm table_builder
```

If the current shell has not picked up docker group membership, use:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm table_builder'
```

Expected completion line:

```json
{"out": "/workspace/experiments/H001_geom_reliability", "status": "ready"}
```

The table builder also writes `sources/open3dsg/table6_hook.json`; Open3DSG rows in Table 6 are now ready when `sources/open3dsg/metrics/metrics.json` reports status `ready`.

## Bootstrap Confidence Intervals

Compute subgraph-level bootstrap confidence intervals for VL-SAT and Open3DSG
source metrics:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm bootstrap_ci'
```

This creates:

- `bootstrap_ci/manifest.json`
- `bootstrap_ci/summary.json`
- `bootstrap_ci/summary.md`

Expected completion line:

```json
{"out": "experiments/H001_geom_reliability/bootstrap_ci", "sources": ["open3dsg_ov", "vlsat_closed_set"], "status": "ready"}
```

## Open3DSG Non-Avg Downstream Branch

The official non-averaged BLIP checkpoint is evaluated under
`sources/open3dsg/non_avg/` so that avg-BLIP paper-facing artifacts are not
overwritten. Current raw dump run record:

```text
experiments/H001_geom_reliability/sources/open3dsg/non_avg/raw_dump/run_20260604_182423.md
```

Current downstream continuation record:

```text
experiments/H001_geom_reliability/sources/open3dsg/non_avg/downstream_after_raw_20260604_183622.md
```

The continuation runner is:

```bash
experiments/H001_geom_reliability/scripts/run_open3dsg_nonavg_downstream_after_raw.sh
```

After the raw-dump exit file contains `0`, run:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_raw_dump_identity_nonavg
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_adapter_raw_dump_nonavg
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_geometry_join_nonavg
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_metric_eval_nonavg
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm bootstrap_ci_nonavg
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_non_avg_table6_caveats
```

This branch is not paper evidence until all downstream commands pass and the
user explicitly confirms whether non-avg results should replace or supplement
the current avg-BLIP Open3DSG wording.

## Full Official Validation Scope Contract

Freeze the full official `3DSSG_subset` validation scope before any
full-validation metric rerun:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm full_validation_scope_contract'
```

This creates:

- `full_validation_transition/scope_contract/manifest.json`
- `full_validation_transition/scope_contract/scope_contract.json`
- `full_validation_transition/scope_contract/scans.txt`
- `full_validation_transition/scope_contract/contexts.jsonl`
- `full_validation_transition/scope_contract/commands.md`
- `full_validation_transition/scope_contract/report.md`

Current result: status
`full_official_validation_scope_contract_ready_no_metric_execution`; target
scope is official validation 157 scans / 548 contexts / 11,254 GT rows / 3,972
H001-family GT rows. This is a protocol-freeze artifact only. Do not edit the
current 127-scan tables by denominator substitution. Full-validation paper
promotion requires separate VL-SAT and Open3DSG output paths, fresh geometry
join, metrics, controls, bootstrap CI, and caveat wording.

## VL-SAT Full Validation Runtime

Stage the full official validation runtime root:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm --build vlsat_full_validation_stage'
```

Refresh the runtime/job record:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm --build vlsat_full_validation_runtime_record'
```

Run the raw-dump preflight:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm vlsat_full_validation_raw_preflight'
```

Current result: status `vlsat_full_validation_metric_bundle_ready`; 157/157
faithful staged scans, runtime image `h001-open3dsg-repro:cu128`, 16/16
checkpoint files, raw preflight `ready_to_run`, raw dump `raw_dump_ready`,
adapter export `ready`, geometry join `ready`, metrics `ready`, GT verifier
eval `ready`, and VL-SAT-only bootstrap CI `ready`. Artifacts:

- `sources/vlsat/full_validation/stage/stage_manifest.json`
- `sources/vlsat/full_validation/stage/stage_report.md`
- `sources/vlsat/full_validation/runtime_record/manifest.json`
- `sources/vlsat/full_validation/runtime_record/runtime_contract.json`
- `sources/vlsat/full_validation/runtime_record/commands.md`
- `sources/vlsat/full_validation/runtime_record/report.md`
- `sources/vlsat/full_validation/raw_preflight/summary.json`
- `sources/vlsat/full_validation/raw_preflight/report.md`
- `sources/vlsat/full_validation/raw/run_20260604_204428.md`
- `sources/vlsat/full_validation/raw/raw.jsonl`
- `sources/vlsat/full_validation/adapter/predictions.jsonl`
- `sources/vlsat/full_validation/adapter/ground_truth.jsonl`
- `sources/vlsat/full_validation/geometry/verification.jsonl`
- `sources/vlsat/full_validation/metrics/metrics.json`
- `sources/vlsat/full_validation/gt_eval/metrics.json`
- `sources/vlsat/full_validation/bootstrap_ci/summary.md`

Launch template:

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_vlsat_full_validation_raw "\
cd /home/yoohyun/research && \
env UID=\$(id -u) GID=\$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm vlsat_full_validation_raw_dump \
> logs/vlsat_full_validation_raw_${ts}.log 2>&1; \
echo \$? > logs/vlsat_full_validation_raw_${ts}.exit"
```

The raw dump alone is not paper metric evidence. The downstream commands below
now complete the VL-SAT full-validation metric bundle under the same
full-validation scope.

Downstream commands:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm vlsat_full_validation_adapter_export
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm vlsat_full_validation_geometry_join
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm vlsat_full_validation_metric_eval
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm vlsat_full_validation_gt_verifier_eval
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm bootstrap_ci_full_validation_vlsat
```

Latest downstream result: predictions `957,008`, ground-truth rows `11,254`,
H001-family GT rows `3,972`, geometry rows preserved `957,008/957,008`, metric
status `ready`, GT verifier AUROC `0.9772`, bootstrap warnings `0`. This is
valid VL-SAT full-validation metric evidence, but paper-wide full-validation
promotion now depends on explicit user confirmation and table/report
regeneration.

## Open3DSG Full Validation Runtime

The Open3DSG full official validation branch lives under
`sources/open3dsg/full_validation/` and uses the selected official non-avg BLIP
checkpoint. It does not overwrite the existing avg-BLIP or non-avg hardened
branches.

Payload and source-runtime preparation:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_full_validation_payload
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm feature_audit_full_validation
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_full_validation_feature_seed
```

Feature generation, when not seeding from compatible feature caches:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm dump_features_full_validation_nonavg
```

Raw dump should be launched as a background job:

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_open3dsg_full_validation_raw "\
cd /home/yoohyun/research && \
env UID=\$(id -u) GID=\$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm eval_full_validation_gt_objects_nonavg \
> logs/open3dsg_full_validation_raw_${ts}.log 2>&1; \
echo \$? > logs/open3dsg_full_validation_raw_${ts}.exit"
```

After `raw_dump/stream_manifest.json` reports `raw_dump_stream_complete`, run:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_adapter_raw_dump_full_validation
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_raw_dump_identity_full_validation
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_geometry_join_full_validation
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_metric_eval_full_validation
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm bootstrap_ci_full_validation
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_failure_generator_full_validation
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_full_validation_table6_caveats
```

Latest result: status `open3dsg_full_validation_metric_bundle_ready_with_caveats`.
Views are 157/157; preprocess is 533/548 with 15 missing contexts after
recovery; covered-scope features are 533/533; raw stream wrote 26,746 rows and
533 completed batches; adapter has 690,924 prediction rows; geometry preserves
690,924/690,924 rows; metrics, bootstrap CI, failure rows, and table/caveat
regeneration are ready. Key metrics: semantic_only R@50/R@100
`0.4043/0.5111`, V@50/@100 `0.1387/0.1242`; probabilistic_recalibrated
R@50/R@100 `0.3943/0.5685`, V@50/@100 `0.0590/0.0807`;
rule_verified_point_subtype R@50/R@100 `0.4242/0.5320`, V@50/@100 `0.0/0.0`;
family_specific control R@50/R@100 `0.4612/0.5999`, V@50/@100
`0.0265/0.0332`.

Review the unmodified 533/548 branch clean-exit retry/equivalence closeout:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_full_validation_raw_clean_exit_review
```

Current result: `sources/open3dsg/full_validation/raw_clean_exit_review/`
status `open3dsg_raw_provenance_review_ready`; the expected retry artifact is
not present after cleanup, so the unmodified branch keeps its process-level
exit-137 caveat. The selected 548/548 recovery branch is unaffected.

## Low-K Top-Rank Diagnostic

The low-K diagnostic reuses existing full-validation row-level outputs and does
not rerun VL-SAT/Open3DSG inference. It writes separate outputs and does not
overwrite locked `metrics/`.

Protocol:

```text
experiments/H001_geom_reliability/k_sweep/protocol.md
```

Commands:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm vlsat_full_validation_metric_eval_k_sweep
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_metric_eval_full_validation_recovery_k_sweep
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm bootstrap_ci_full_validation_recovery_k_sweep
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm h001_low_k_sweep_report
```

Outputs:

- `sources/vlsat/full_validation/metrics_k_sweep/metrics.json`
- `sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics_k_sweep/metrics.json`
- `sources/open3dsg/full_validation/recovery_relaxed_views_min2/bootstrap_ci_k_sweep/summary.json`
- `k_sweep/summary.md`
- `k_sweep/recall_violation_curve.csv`
- `k_sweep/recall_violation_curve.svg`

Latest result: `k_sweep/summary.md` status `ready`; `K=50/100` point
estimates, denominators, selected counts, and geometry coverage match the
locked `metrics/` outputs; bootstrap point estimates match
`metrics_k_sweep/metrics.json` for all reported K values. The diagnostic
supports considering a main-text top-rank reliability figure/table, especially
for Open3DSG recovery K=10/20, but it does not by itself replace the standard
R@50/R@100 table.

## Relative Horizontal Scope Audit

Run the no-training, no-inference audit for the optional
`relative_horizontal` expansion track:

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm relative_horizontal_scope_audit
```

This creates:

- `sources/relative_horizontal/scope_audit/manifest.json`
- `sources/relative_horizontal/scope_audit/label_counts.json`
- `sources/relative_horizontal/scope_audit/report.md`

Current result: status `relative_horizontal_scope_audit_ready_no_metric_execution`;
expanded candidate denominator 6,115/7,505 if `relative_horizontal` is
validated. This is not metric evidence and does not change the current paper
claim.

## Relative Horizontal Coordinate Audit

Run the GT-only coordinate-frame semantics gate before any verifier or metric
promotion:

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm relative_horizontal_coordinate_audit
```

This creates:

- `sources/relative_horizontal/coordinate_audit/manifest.json`
- `sources/relative_horizontal/coordinate_audit/frame_metrics.json`
- `sources/relative_horizontal/coordinate_audit/records.jsonl`
- `sources/relative_horizontal/coordinate_audit/ambiguity_buckets.json`
- `sources/relative_horizontal/coordinate_audit/report.md`

This is not source-prediction metric evidence. It only tests whether
`left/right/front/behind` labels are stable under a deterministic coordinate
frame and whether wrong-frame controls are clearly worse.

Current result: status
`relative_horizontal_coordinate_audit_blocked_no_metric_execution`; best frame
`scan_left_neg_x_front_neg_y`, macro strict purity 0.7725, strict eligible share
0.6403, left/right purity 0.8005, front/behind purity 0.7445, inverse
consistency 1.0, wrong-frame gap 0.1231. This blocks main-claim promotion.

## Relative Horizontal Bucket Inspection

Inspect threshold-free `front` / `behind` ambiguity and contradiction buckets
from the coordinate audit:

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm relative_horizontal_bucket_inspection
```

This creates:

- `sources/relative_horizontal/bucket_inspection/manifest.json`
- `sources/relative_horizontal/bucket_inspection/summary.json`
- `sources/relative_horizontal/bucket_inspection/examples.jsonl`
- `sources/relative_horizontal/bucket_inspection/report.md`

Use this only as scope-expansion diagnostic evidence. It is not a verifier,
not a source metric, and not a main-claim result.

Current result: status
`relative_horizontal_bucket_inspection_ready_no_metric_execution`;
recommendation `do_not_promote_relative_horizontal_to_main_claim`.
Threshold-free diagnostics: inverse consistency 1.0, wrong-frame gap 0.1231,
front/behind match:contradiction 2.9143, front/behind strict purity 0.7445,
front/behind sign-only purity 0.7491, and ambiguity flags
axis_margin_ambiguous 230 / conflicting_axis_dominates 430 /
strong_projected_overlap 44. Current AAAI-path decision is to freeze this as
appendix/limitation evidence and not run expanded-family metrics.

## Attachment Deferred Scope Audit

Run the no-training, no-inference audit for the preferred future
`attachment_deferred` relation-family upgrade:

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm attachment_deferred_scope_audit
```

This creates:

- `sources/attachment_deferred/scope_audit/manifest.json`
- `sources/attachment_deferred/scope_audit/label_counts.json`
- `sources/attachment_deferred/scope_audit/evidence_schema.json`
- `sources/attachment_deferred/scope_audit/report.md`

Use this only as scope and evidence-schema planning. It is not a verifier,
not a source metric, and not a main-claim result.

Current result: status
`attachment_deferred_scope_schema_ready_no_metric_execution`; current H001 GT
denominator 2,545, attachment GT rows 967, expanded candidate denominator
3,512 / 7,505, VL-SAT candidate rows 77,748, Open3DSG candidate rows 57,300,
and existing verification status `unsupported` for both sources. Next gate is
`G1_attachment_evidence_extractor_design`.

## Attachment Deferred Evidence Extractor Contract

Run the G1 design/contract step for the future attachment evidence extractor:

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm attachment_deferred_extractor_contract
```

This creates:

- `sources/attachment_deferred/evidence_extractor/manifest.json`
- `sources/attachment_deferred/evidence_extractor/extractor_contract.json`
- `sources/attachment_deferred/evidence_extractor/output_schema.json`
- `sources/attachment_deferred/evidence_extractor/field_catalog.json`
- `sources/attachment_deferred/evidence_extractor/subtype_policy.json`
- `sources/attachment_deferred/evidence_extractor/extraction_plan.json`
- `sources/attachment_deferred/evidence_extractor/validation_plan.json`
- `sources/attachment_deferred/evidence_extractor/example_row.json`
- `sources/attachment_deferred/evidence_extractor/commands.md`
- `sources/attachment_deferred/evidence_extractor/report.md`

Use this only as extractor design and output-contract evidence. It is not a
verifier, not a calibration run, not a source metric, and not a main-claim
result.

Current result: status
`attachment_deferred_extractor_contract_ready_no_extraction`; this contract was
used by the completed G1b dry run.

## Attachment Deferred Extractor Dry Run

Run the G1b schema-validated evidence-only dry run:

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm attachment_deferred_extractor_dry_run
```

This creates:

- `sources/attachment_deferred/extractor_dry_run/rows.jsonl`
- `sources/attachment_deferred/extractor_dry_run/manifest.json`
- `sources/attachment_deferred/extractor_dry_run/summary.json`
- `sources/attachment_deferred/extractor_dry_run/validation.json`
- `sources/attachment_deferred/extractor_dry_run/report.md`

Use this only as a small evidence-output dry run. It is not a verifier,
calibration run, source metric, or main-claim result.

Current result: status
`attachment_deferred_extractor_dry_run_ready_no_verifier`; 36 input rows
produced 36 output rows, validation errors 0, source rows 9 each for
`gt_positive`, `counterfactual`, `vlsat_closed_set`, and `open3dsg_ov`, and
labels 12 each for `attached to`, `hanging on`, and `connected to`. Forbidden
verifier/metric fields are absent. All rows are `partial` because the dry run
uses semseg OBB and `dominantNormal` proxies only. Subsequent G1c validation is
now complete.

## Attachment Deferred Point/Surface Validation

Run the G1c segmented-point contact and surface-normal validation:

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm attachment_deferred_point_surface_validation
```

This creates:

- `sources/attachment_deferred/point_surface_validation/rows.jsonl`
- `sources/attachment_deferred/point_surface_validation/diagnostics.jsonl`
- `sources/attachment_deferred/point_surface_validation/manifest.json`
- `sources/attachment_deferred/point_surface_validation/summary.json`
- `sources/attachment_deferred/point_surface_validation/validation.json`
- `sources/attachment_deferred/point_surface_validation/report.md`

Use this only as point/surface estimator validation. It is not a verifier,
calibration run, source metric, or main-claim result.

Current result: status
`attachment_deferred_point_surface_validation_ready_no_verifier`; 36 input rows
produced 36 output rows, validation errors 0, ready rows 36, point available
rows 36, normal available rows 36, and near-contact rows 27 under the 0.05m
diagnostic threshold. Forbidden verifier/metric fields are absent. Next gate is
`G2_attachment_verifier_policy_design`.

## Attachment Deferred Verifier Policy

Run the G2 conservative verifier-policy design step:

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm attachment_deferred_verifier_policy
```

This creates:

- `sources/attachment_deferred/verifier_policy/manifest.json`
- `sources/attachment_deferred/verifier_policy/verifier_policy.json`
- `sources/attachment_deferred/verifier_policy/decision_schema.json`
- `sources/attachment_deferred/verifier_policy/threshold_plan.json`
- `sources/attachment_deferred/verifier_policy/reason_codes.json`
- `sources/attachment_deferred/verifier_policy/calibration_plan.json`
- `sources/attachment_deferred/verifier_policy/commands.md`
- `sources/attachment_deferred/verifier_policy/report.md`

Use this only as a verifier-policy design artifact. It does not apply decisions
to source predictions, fit calibration, compute metrics, or change the main
paper claim.

Current result: status
`attachment_deferred_verifier_policy_ready_no_decisions_no_metrics`; 9 subtype
rules are covered. Conservative defaults are near-contact 0.05m, uncertain
contact band 0.05-0.15m, clear-far distance 0.30m, min near-contact points 3,
and min contact patch score 0.20. No decision rows, calibration, source
scoring, or metrics were emitted. Next gate is
`G3_attachment_calibration_counterfactual_generation` (now completed).

## Attachment Deferred Calibration / Counterfactual Route

Prepare the G3 train-dev positive/counterfactual route before any held-out
source metric execution:

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm attachment_deferred_calibration_counterfactuals
```

This creates:

- `sources/attachment_deferred/calibration_counterfactuals/manifest.json`
- `sources/attachment_deferred/calibration_counterfactuals/positive_seeds.jsonl`
- `sources/attachment_deferred/calibration_counterfactuals/counterfactual_seeds.jsonl`
- `sources/attachment_deferred/calibration_counterfactuals/split_plan.json`
- `sources/attachment_deferred/calibration_counterfactuals/counterfactual_plan.json`
- `sources/attachment_deferred/calibration_counterfactuals/policy_smoke_plan.json`
- `sources/attachment_deferred/calibration_counterfactuals/gt_eval_inputs.json`
- `sources/attachment_deferred/calibration_counterfactuals/threshold_freeze_protocol.json`
- `sources/attachment_deferred/calibration_counterfactuals/commands.md`
- `sources/attachment_deferred/calibration_counterfactuals/report.md`

Current result: status
`attachment_deferred_calibration_counterfactual_plan_ready_no_fit_no_metrics`;
315 train/dev positive seeds and 446 counterfactual negative seeds are ready.
Counterfactual seeds require geometry-margin validation before becoming
calibration negatives. No decision rows, calibration, source scoring, or metrics
were emitted. Subsequent G4 GT policy smoke is now complete.

## Attachment Deferred GT Policy Smoke

Run the G4 policy-smoke and train-dev GT/counterfactual evaluation before any
attachment source metrics:

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm attachment_deferred_gt_policy_smoke
```

This creates:

- `sources/attachment_deferred/gt_policy_smoke/manifest.json`
- `sources/attachment_deferred/gt_policy_smoke/summary.json`
- `sources/attachment_deferred/gt_policy_smoke/validation.json`
- `sources/attachment_deferred/gt_policy_smoke/policy_smoke_decisions.jsonl`
- `sources/attachment_deferred/gt_policy_smoke/gt_evidence_rows.jsonl`
- `sources/attachment_deferred/gt_policy_smoke/gt_evidence_diagnostics.jsonl`
- `sources/attachment_deferred/gt_policy_smoke/gt_policy_decisions.jsonl`
- `sources/attachment_deferred/gt_policy_smoke/gt_eval_rows.jsonl`
- `sources/attachment_deferred/gt_policy_smoke/visual_sanity_plan.json`
- `sources/attachment_deferred/gt_policy_smoke/commands.md`
- `sources/attachment_deferred/gt_policy_smoke/report.md`

Current result: status
`attachment_deferred_gt_policy_smoke_ready_no_source_metrics`; policy-smoke
decision rows 36/36 and train/dev seed decision rows 761/761 pass schema
validation with scan errors 0. Positive nonviolated is 0.9048,
counterfactual nonsatisfied is 0.8274, positive strict satisfied is 0.3841,
counterfactual strict violated is 0.4574, and overall uncertain rate is 0.4323.
This is not fitted calibration, not source metric evidence, and not a main
claim update. The subsequent G4b error/visual sanity planning step is now
complete, the subsequent G4c strict-only calibration-filter freeze is complete,
the subsequent G5a pooled strict calibration fit is complete, and the subsequent
G5b bounded source scoring preflight is complete. The subsequent G5c
full-source scoring/metric protocol freeze is also complete; the current gate is
optional G5d full-source scoring plus source metrics/controls.

## Attachment Deferred Error / Visual Sanity

Run the G4b error taxonomy, calibration-filter, and visual-queue planning step:

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm attachment_deferred_error_visual_sanity
```

This creates:

- `sources/attachment_deferred/error_visual_sanity/manifest.json`
- `sources/attachment_deferred/error_visual_sanity/summary.json`
- `sources/attachment_deferred/error_visual_sanity/review_cases.jsonl`
- `sources/attachment_deferred/error_visual_sanity/visual_queue.jsonl`
- `sources/attachment_deferred/error_visual_sanity/calibration_filter.jsonl`
- `sources/attachment_deferred/error_visual_sanity/guide.md`
- `sources/attachment_deferred/error_visual_sanity/commands.md`
- `sources/attachment_deferred/error_visual_sanity/report.md`

Current result: status
`attachment_deferred_error_visual_sanity_plan_ready_no_source_metrics`; review
cases 436, visual queue rows 50, calibration-filter rows 761. The queue is
label-diverse with `attached to` 38, `connected to` 6, and `hanging on` 6.
Strict calibration candidates are 121 positives and 204 negatives; 77
false-satisfied counterfactuals, 30 false-violated positives, and 329 uncertain
rows require review, exclusion, or soft-label protocol before calibration. This
is not fitted calibration, not source metric evidence, and not a main-claim
update. The subsequent G4c strict-only calibration-filter freeze is now
complete.

## Attachment Deferred Strict Filter Freeze

Run the G4c strict-only calibration-filter freeze:

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm attachment_deferred_strict_filter_freeze
```

This creates:

- `sources/attachment_deferred/strict_filter_freeze/manifest.json`
- `sources/attachment_deferred/strict_filter_freeze/summary.json`
- `sources/attachment_deferred/strict_filter_freeze/freeze_policy.json`
- `sources/attachment_deferred/strict_filter_freeze/strict_calibration_rows.jsonl`
- `sources/attachment_deferred/strict_filter_freeze/excluded_rows.jsonl`
- `sources/attachment_deferred/strict_filter_freeze/commands.md`
- `sources/attachment_deferred/strict_filter_freeze/report.md`

Current result: status
`attachment_deferred_strict_filter_frozen_no_fit_no_source_metrics`; strict
calibration rows 325, strict positives 121, strict negatives 204, and excluded
non-strict rows 436. Strict label counts are `attached to` 200, `hanging on`
113, and `connected to` 12. Split counts are train 242 and dev 83. Warning:
`connected to` has no dev strict rows, so future connected-to family-specific
calibration requires pooled calibration, augmented dev selection, or explicit
limitation. This is not fitted calibration, not source metric evidence, and not
a main-claim update. The subsequent G5a attachment calibration fit and G5b
bounded source scoring preflight are complete; the next gate is full-source
scoring/metric protocol freeze before VL-SAT/Open3DSG source metrics and
controls.

## Attachment Deferred Calibration Fit

Run the G5a pooled strict calibration fit:

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm attachment_deferred_calibration_fit
```

This creates:

- `sources/attachment_deferred/calibration_fit/manifest.json`
- `sources/attachment_deferred/calibration_fit/model.json`
- `sources/attachment_deferred/calibration_fit/metrics.json`
- `sources/attachment_deferred/calibration_fit/scores.jsonl`
- `sources/attachment_deferred/calibration_fit/commands.md`
- `sources/attachment_deferred/calibration_fit/report.md`

Current result: status
`attachment_deferred_calibration_fit_ready_no_source_metrics`; model id
`h001-attachment-deferred-p-geom-valid-strict-v1`; train/dev rows 242/83;
dev positives/negatives 27/56; dev Brier/NLL/ECE 0.0010/0.0077/0.0071; dev
AUROC/AUPRC 1.0/1.0. Warnings:
`connected_to_dev_absent_use_pooled_or_train_only_caveat` and
`strict_subset_nearly_separable_not_source_metric_evidence`. This is a fitted
calibration artifact only; it does not score source predictions, compute source
metrics, run controls/bootstrap, or update the main AAAI claim.

## Attachment Deferred Source Scoring Preflight

Run the G5b bounded source evidence extraction and `p_geom_valid` scoring
preflight:

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm attachment_deferred_source_scoring_preflight
```

This creates:

- `sources/attachment_deferred/source_scoring_preflight/manifest.json`
- `sources/attachment_deferred/source_scoring_preflight/summary.json`
- `sources/attachment_deferred/source_scoring_preflight/source_rows.jsonl`
- `sources/attachment_deferred/source_scoring_preflight/evidence_rows.jsonl`
- `sources/attachment_deferred/source_scoring_preflight/diagnostics.jsonl`
- `sources/attachment_deferred/source_scoring_preflight/scored_rows.jsonl`
- `sources/attachment_deferred/source_scoring_preflight/commands.md`
- `sources/attachment_deferred/source_scoring_preflight/report.md`

Current result: status
`attachment_deferred_source_scoring_preflight_ready_no_metrics`; selected and
scored rows 120; source counts Open3DSG 60 and VL-SAT 60; label counts
`attached to` 40, `connected to` 40, `hanging on` 40; selected unique scans 20
per source; evidence rows ready 120/120; validation errors 0; mean/median
`p_geom_valid` 0.3610/0.0580. This is bounded preflight only. It does not
compute R@K, Violation@K, controls, bootstrap CI, or update the main AAAI claim.

## Attachment Deferred Full-Source Protocol Freeze

Run the G5c protocol freeze before any full-source attachment metric:

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm attachment_deferred_full_source_protocol
```

This creates:

- `sources/attachment_deferred/full_source_protocol/manifest.json`
- `sources/attachment_deferred/full_source_protocol/protocol.json`
- `sources/attachment_deferred/full_source_protocol/denominator_audit.json`
- `sources/attachment_deferred/full_source_protocol/shards.jsonl`
- `sources/attachment_deferred/full_source_protocol/validation.json`
- `sources/attachment_deferred/full_source_protocol/commands.md`
- `sources/attachment_deferred/full_source_protocol/report.md`

Current result: status
`attachment_deferred_full_source_protocol_frozen_no_metrics`; validation errors
0; expected full-source rows 135,048; deterministic shards 69 with 2,000 rows
per shard; global exact-label GT denominator 967; VL-SAT covered denominator
967/967; Open3DSG covered denominator 768/967 with 199 missing exact-label GT
rows. Frozen metric conditions are `semantic_only`,
`probabilistic_recalibrated`, `rule_verified_attachment_policy`,
`control_p_geom_valid_only`, `control_distance_only`,
`control_shuffled_geometry`, and `control_wrong_pair_geometry`. This is still
not full-source scoring, not source metric evidence, and not a main-claim
update.

## Qwen-VL Full-Source Crops

Qwen-VL remains a third semantic source / modern VLM extension. Render and
verify pair crops before any full-source Qwen inference:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) QWEN_VL_FULL_SOURCE_SHARD_ID=qwen_full_source_shard_0000 docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_crop_render'
sg docker -c 'env UID=$(id -u) GID=$(id -g) QWEN_VL_FULL_SOURCE_SHARD_ID=qwen_full_source_shard_0000 docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_crop_preflight'
```

The current shard smoke passed for `qwen_full_source_shard_0000`: 250 input
rows, 84 unique pair crops, 84 verified crops, 0 errors.

Launch the all-scope render as a background job:

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_qwen_vl_full_crop_render "cd /home/yoohyun/research && bash -lc 'sg docker -c '\''env UID=$(id -u) GID=$(id -g) QWEN_VL_FULL_SOURCE_SHARD_ID=all docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_crop_render'\''; rc=\$?; printf \"%s\n\" \"\$rc\" > logs/qwen_vl_full_source_crop_render_all_${ts}.exit; exit \"\$rc\"' > logs/qwen_vl_full_source_crop_render_all_${ts}.log 2>&1"
```

After exit code 0, run all-scope preflight:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) QWEN_VL_FULL_SOURCE_SHARD_ID=all docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_crop_preflight'
```

Freeze the full-source Qwen inference runner and resume policy:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_inference_plan'
```

Dry-run the first shard without model load or inference:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) QWEN_VL_FULL_SOURCE_SHARD_ID=qwen_full_source_shard_0000 docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_full_source_infer_dry_run'
```

Current result: runner plan status `full_source_inference_runner_frozen_no_inference`;
dry-run shard `qwen_full_source_shard_0000` has 250 rows, 84 unique pair crops,
and 0 blockers. Actual inference uses `qwen_vl_full_source_infer_shard` and
must run as a timestamped background job.

Qwen downstream validation and metric generation from a completed runtime root:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_aggregate'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_validate'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_adapter_export'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_geometry_join'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_metric_eval'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_bootstrap_ci'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_failure_schema'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_failure_generator'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_failure_case_sampler'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_failure_case_inspection'
```

## Direct Docker Equivalent

```bash
docker build -f experiments/H001_geom_reliability/Dockerfile -t h001-geom-reliability:latest .
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/workspace" -w /workspace h001-geom-reliability:latest --repo-root /workspace --out /workspace/experiments/H001_geom_reliability
```

## Rule

Only outputs generated by these Docker commands may be promoted to paper experiment results.

## Open3DSG Checkpoint Plan

Generate the Dockerized Open3DSG checkpoint reproduction plan:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_plan'
```

This creates:

- `sources/open3dsg/checkpoint_plan.json`
- `sources/open3dsg/checkpoint_plan.md`
- `sources/open3dsg/Dockerfile.repro`
- `sources/open3dsg/compose.open3dsg.yaml`
- `sources/open3dsg/commands.open3dsg.md`

## Open3DSG Failure Analysis Schema

Freeze the failure-analysis taxonomy before Open3DSG metric/failure inspection:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_failure_schema'
```

This creates:

- `sources/open3dsg/failure_analysis/schema.json`
- `sources/open3dsg/failure_analysis/taxonomy.json`
- `sources/open3dsg/failure_analysis/aggregation_plan.json`
- `sources/open3dsg/failure_analysis/example.jsonl`
- `sources/open3dsg/failure_analysis/manifest.json`
- `sources/open3dsg/failure_analysis/report.md`

Validate the row generator skeleton with synthetic rows only:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_failure_generator_smoke'
```

This creates:

- `sources/open3dsg/failure_analysis_generator_smoke/rows.jsonl`
- `sources/open3dsg/failure_analysis_generator_smoke/summary.json`
- `sources/open3dsg/failure_analysis_generator_smoke/manifest.json`
- `sources/open3dsg/failure_analysis_generator_smoke/report.md`

Generate real failure rows and qualitative case inspection after Open3DSG metrics exist:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_failure_generator_real'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_failure_case_sampler'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_failure_case_inspection'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_paper_caveats'
```

This creates:

- `sources/open3dsg/failure_rows/rows.jsonl`
- `sources/open3dsg/failure_rows/summary.json`
- `sources/open3dsg/failure_cases/queue.jsonl`
- `sources/open3dsg/failure_cases/inspection.json`
- `sources/open3dsg/failure_cases/inspection.md`
- `sources/open3dsg/paper_caveats/manifest.json`
- `sources/open3dsg/paper_caveats/report.md`

## Open3DSG Training Repro Root

Stage the leakage-guarded Open3DSG `training_repro` root metadata and scan symlinks:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_train_root'
```

This creates:

- `sources/open3dsg/training_repro/manifest.json`
- `sources/open3dsg/training_repro/records.jsonl`
- `sources/open3dsg/training_repro/missing_train_scans.txt`
- `sources/open3dsg/training_repro/missing_train_dev_scans.txt`
- `sources/open3dsg/training_repro/report.md`

## Open3DSG Post-Dump Handoff

Freeze the command order and gates for the transition after the official feature dump:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_post_dump_handoff'
```

This creates:

- `sources/open3dsg/post_dump_handoff/manifest.json`
- `sources/open3dsg/post_dump_handoff/commands.md`
- `sources/open3dsg/post_dump_handoff/report.md`

## Open3DSG Checkpoint Selection

Freeze the checkpoint provenance schema and primary-selection policy before checkpoint outputs are inspected:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_checkpoint_selection'
```

This creates:

- `sources/open3dsg/checkpoint_selection/selection_policy.json`
- `sources/open3dsg/checkpoint_selection/record_template.json`
- `sources/open3dsg/checkpoint_selection/manifest.json`
- `sources/open3dsg/checkpoint_selection/commands.md`
- `sources/open3dsg/checkpoint_selection/report.md`

## Open3DSG Caveat-Reduction Plan

Freeze the optional retry order before launching any heavy non-avg BLIP or
`388/388` covered-context job:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_caveat_reduction_plan'
```

This creates:

- `sources/open3dsg/caveat_reduction_plan/manifest.json`
- `sources/open3dsg/caveat_reduction_plan/retry_plan.json`
- `sources/open3dsg/caveat_reduction_plan/commands.md`
- `sources/open3dsg/caveat_reduction_plan/report.md`

## Open3DSG H001 Eval Features

Stage H001 held-out scan symlinks under the `h001_runtime` root:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm h001_eval_payload'
```

Generate H001 held-out eval features under the `h001_runtime` root before raw dump:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_CHECKPOINT=/workspace/<selected-ckpt> docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm dump_features_h001_eval'
```

Resumable shard command for the current H001 eval feature cache. This keeps the full eval denominator for later metric runs, but limits this feature-cache job to missing ids only:

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_open3dsg_dump_features_h001_eval_shard "cd /home/yoohyun/research && bash -lc 'set -o pipefail; env UID=\$(id -u) GID=\$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt OPEN3DSG_FEATURE_SHARD_ONLY_MISSING=1 OPEN3DSG_FEATURE_SHARD_MAX_NEW_IDS=5 OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=1 OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:64 docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm dump_features_h001_eval; rc=\$?; echo \"finished_at=\$(date -Is)\"; echo \"exit_code=\$rc\"; printf \"%s\n\" \"\$rc\" > logs/open3dsg_dump_features_h001_eval_shard_${ts}.exit; exit \$rc' > logs/open3dsg_dump_features_h001_eval_shard_${ts}.log 2>&1"
```

Audit the generated H001 eval feature run:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm feature_audit_h001_eval'
```

This creates or checks:

- `sources/open3dsg/h001_eval_payload/manifest.json`
- `sources/open3dsg/h001_eval_payload/records.jsonl`
- `sources/open3dsg/h001_eval_payload/report.md`
- `local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3/`
- `sources/open3dsg/dump_features_h001_eval/manifest.json`
- `sources/open3dsg/dump_features_h001_eval/report.md`

## Open3DSG Raw-Dump Identity

Freeze the raw-dump identity audit checklist before raw dump conversion:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_raw_dump_identity'
```

This creates:

- `sources/open3dsg/raw_dump_identity/checklist.json`
- `sources/open3dsg/raw_dump_identity/manifest.json`
- `sources/open3dsg/raw_dump_identity/commands.md`
- `sources/open3dsg/raw_dump_identity/report.md`

## Open3DSG Metric Scope

Freeze the predicate-family mapping and filtered-denominator caveat before real metric execution:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_metric_scope'
```

This creates:

- `sources/open3dsg/metric_scope/predicate_mapping.json`
- `sources/open3dsg/metric_scope/denominator_policy.json`
- `sources/open3dsg/metric_scope/manifest.json`
- `sources/open3dsg/metric_scope/commands.md`
- `sources/open3dsg/metric_scope/report.md`

## Open3DSG Metric/Join Contract

Freeze the Open3DSG metric/join runner contract before runtime inputs exist:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_metric_join_contract'
```

This creates blocked-input artifacts until real Open3DSG prediction and geometry JSONL files exist:

- `sources/open3dsg/metric_join_contract/input_contract.json`
- `sources/open3dsg/metric_join_contract/output_contract.json`
- `sources/open3dsg/metric_join_contract/metrics.json`
- `sources/open3dsg/metric_join_contract/manifest.json`
- `sources/open3dsg/metric_join_contract/commands.md`
- `sources/open3dsg/metric_join_contract/report.md`

## 3RScan Payload Batch

Audit the current Open3DSG `training_repro` payload queue:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_payload --repo-root /workspace'
```

Run a small download/extract pilot batch:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_payload --repo-root /workspace --download-missing --extract-sequence --limit 1 --workers 2'
```

This creates:

- `sources/open3dsg/payload/manifest.json`
- `sources/open3dsg/payload/records.jsonl`
- `sources/open3dsg/payload/report.md`

## Qwen-VL Adapter Contract

Generate the modern-VLM semantic-source adapter contract:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_adapter_contract'
```

This creates:

- `sources/qwen_vl/adapter_contract.json`
- `sources/qwen_vl/input_schema.json`
- `sources/qwen_vl/input_schema_example.json`
- `sources/qwen_vl/output_schema.json`
- `sources/qwen_vl/output_jsonl_contract.md`
- `sources/qwen_vl/model_candidates.json`
- `sources/qwen_vl/prediction_schema_example.json`
- `sources/qwen_vl/prompt_templates.md`
- `sources/qwen_vl/commands.qwen_vl.md`
- `sources/qwen_vl/report.md`

Validate the frozen input/output JSONL contract and parser skeleton before any model download or inference:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_contract_validator'
```

This creates:

- `sources/qwen_vl/validation/input_smoke.jsonl`
- `sources/qwen_vl/validation/parsed.jsonl`
- `sources/qwen_vl/validation/parser_contract.json`
- `sources/qwen_vl/validation/manifest.json`
- `sources/qwen_vl/validation/report.md`

Select the non-held-out tiny pilot scope without model download or inference:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_tiny_pilot_scope'
```

Validate the tiny pilot input JSONL and synthetic parser template:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_tiny_pilot_validator'
```

This creates:

- `sources/qwen_vl/tiny_pilot/input.jsonl`
- `sources/qwen_vl/tiny_pilot/selection.jsonl`
- `sources/qwen_vl/tiny_pilot/raw_response_template.jsonl`
- `sources/qwen_vl/tiny_pilot/scans.txt`
- `sources/qwen_vl/tiny_pilot/manifest.json`
- `sources/qwen_vl/tiny_pilot/report.md`
- `sources/qwen_vl/tiny_pilot/validation/manifest.json`
- `sources/qwen_vl/tiny_pilot/validation/report.md`

Plan crop rendering and model runtime lock without downloading a model:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_runtime_plan'
```

This creates:

- `sources/qwen_vl/runtime_plan/crop_plan.jsonl`
- `sources/qwen_vl/runtime_plan/model_recommendation.json`
- `sources/qwen_vl/runtime_plan/commands.md`
- `sources/qwen_vl/runtime_plan/manifest.json`
- `sources/qwen_vl/runtime_plan/report.md`

Render tiny-pilot pair crops without downloading a model or running inference:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_pair_crop_render'
```

This creates small tracked manifests and ignored crop images:

- `sources/qwen_vl/crops/records.jsonl`
- `sources/qwen_vl/crops/manifest.json`
- `sources/qwen_vl/crops/report.md`
- `local_dataset/qwen_vl_crops/tiny_pilot/*/pair_view_000.png`

After rendering, rerun validation and runtime preflight:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_tiny_pilot_validator'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_runtime_plan'
```

## Qwen-VL Runtime Smoke

Build the Qwen-VL runtime image and download the locked primary model in a
background session:

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_qwen_vl_model_download \
  "cd /home/yoohyun/research && bash -lc 'set -o pipefail; sg docker -c '\''env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml build qwen_vl_model_download && env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_model_download && env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_cache_verify'\''; rc=$?; printf \"%s\n\" \"$rc\" > logs/qwen_vl_model_download_${ts}.exit; exit $rc' > logs/qwen_vl_model_download_${ts}.log 2>&1"
```

After the download job completes, verify the cache:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_cache_verify'
```

Run GPU-dependent smoke only after the model cache is complete and the GPU is
not occupied by the Open3DSG feature dump:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_runtime_preflight'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_tiny_inference_smoke'
```

These commands create or update:

- `sources/qwen_vl/model_cache/download_<timestamp>.md`
- `sources/qwen_vl/runtime_smoke/cache/manifest.json`
- `sources/qwen_vl/runtime_smoke/cache/report.md`
- `sources/qwen_vl/runtime_smoke/preflight/manifest.json`
- `sources/qwen_vl/runtime_smoke/preflight/report.md`
- `sources/qwen_vl/runtime_smoke/tiny_inference/raw_response.jsonl` after tiny inference
- `sources/qwen_vl/runtime_smoke/tiny_inference/predictions.jsonl` after tiny inference

Qwen-VL runtime smoke is not paper metric evidence and does not replace the
VL-SAT controlled anchor or Open3DSG reproduction anchor.

## Qwen-VL Full-Source Promotion Plan

Freeze the third-source promotion protocol before any full Qwen paper-metric
run:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_plan'
```

This command creates or updates:

- `sources/qwen_vl/full_source_plan/manifest.json`
- `sources/qwen_vl/full_source_plan/protocol.json`
- `sources/qwen_vl/full_source_plan/commands.md`
- `sources/qwen_vl/full_source_plan/report.md`

The next implementation command is not inference. Add and run a Docker
`qwen_vl_full_source_input` builder first to audit the complete directed-pair /
family input universe, crop coverage, missing-row policy, and shard list.

Current full-source input audit command:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_input'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_contract_validator --repo-root /workspace --contract-dir /workspace/experiments/H001_geom_reliability/sources/qwen_vl --input-jsonl /workspace/experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/input.jsonl --out /workspace/experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/validation'
```

Current result: 77,748 universe query rows, 33,384 inferable input rows, 44,364
missing rows, 134 shards, and 0 input contract errors. Full-source crop
preflight, inference, parser validation, adapter export, geometry join, metrics,
bootstrap, and diagnostic audit are now complete as optional third-source
extension evidence.
