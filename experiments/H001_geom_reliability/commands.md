# H001 Commands

Last updated: 2026-07-11

Run from the repository root.

This file records the current GeoCalib/H001 command surface. Older historical
run logs remain in source subfolders and `logs/`; they should not be used as
the current paper-facing route unless explicitly referenced below.

## Current Paper-Facing Route

- VL-SAT source root: `experiments/H001_geom_reliability/sources/vlsat/full_validation/`
- Open3DSG source root: `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/`
- Compact results: `results/h001_geom_reliability/`
- Main score alias: `family_conditional_risk`
- Legacy raw metric key that may still appear in JSON: `control_family_specific_p_geom_valid`
- Pooled ablation: `probabilistic_recalibrated`
- Main K grid: `{5,10,20,50,100}`

## Compose Sanity

```bash
docker compose -f configs/h001/compose.yaml config --quiet
docker compose -f configs/open3dsg/compose.open3dsg.yaml config --quiet
docker compose -f configs/qwen_vl/compose.qwen.yaml config --quiet
```

## Generate Compact Tables And Report

```bash
docker compose -f configs/h001/compose.yaml run --rm table_builder
```

If the current shell has not picked up docker group membership:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm table_builder'
```

Expected compact outputs:

- `results/h001_geom_reliability/report.md`
- `results/h001_geom_reliability/manifest.lock.json`
- `results/h001_geom_reliability/tables/`
- `results/h001_geom_reliability/figures/figure_specs.md`

## Bootstrap Confidence Intervals

Current compact bootstrap mirror:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm bootstrap_ci'
```

Expected outputs:

- `results/h001_geom_reliability/bootstrap_ci/manifest.json`
- `results/h001_geom_reliability/bootstrap_ci/summary.json`
- `results/h001_geom_reliability/bootstrap_ci/summary.md`

The paper-facing compact bootstrap mirror should report
`family_conditional_risk` as the main GeoCalib score and keep pooled
`probabilistic_recalibrated` as an ablation/baseline.

## Independent Physical-Validity And Reviewer-Extension Gates

Freeze or reproducibly regenerate the blinded audit queue and raw 3D evidence:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm physical_validity_audit_freeze
```

After both independent annotator sheets and required adjudication are complete,
run the pre-frozen human Violation@K and semantic-calibration evaluator:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm physical_validity_audit_evaluate
```

Generate family-wise paired CIs and the fixed rank-average/RRF fusion baselines:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm reviewer_extension_metrics
```

Freeze/check post-hoc provenance and the prospective confirmatory contract:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm confirmatory_protocol_freeze
```

Freeze and verify the H001 factor-isolation protocol before any factor metric:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm factor_isolation_protocol_freeze
```

Frozen outputs are under
`factor_isolation_protocol/frozen_v1/`: `feature_ledger.json`,
`conditions.json`, `controls.json`, `evaluation.json`,
`equivalence_audit.json`, and `manifest.json`. Fit the pre-registered models,
then run the fresh official source in the exact order recorded in
`docs/reproducibility.md`; the final metric commands are:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm 3dssg_confirmatory_metrics
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm 3dssg_confirmatory_audit
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm factor_isolation_metrics_3dssg
```

Do not delete and rerun the target freeze after seeing metrics. Existing output
guards intentionally require a fresh output root for scientific reruns.

## Strict Train-only Reestablishment

The authoritative execution order is fixed. Existing nonempty frozen outputs
must not be overwritten after seeing metrics:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm train_only_reestablishment_freeze
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm train_only_calibration_export
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm train_only_calibrator_fit
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm train_only_internal_dev_stage
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm train_only_internal_dev_preprocess
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm train_only_internal_dev_preprocess_finalize
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm train_only_execution_freeze
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm train_only_internal_dev_inference
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm train_only_internal_dev_adapter
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm train_only_internal_dev_geometry
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm train_only_internal_dev_evaluation
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm train_only_final_lock
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm train_only_final_validation_evaluation
```

Primary compact artifacts:

- `train_only_reestablishment_v1/split_firewall.json`
- `train_only_reestablishment_v1/provenance_audit.json`
- `train_only_reestablishment_v1/calibration/fitted/manifest.json`
- `train_only_reestablishment_v1/execution_contract.json`
- `train_only_reestablishment_v1/internal_dev/evaluation/summary.json`
- `train_only_reestablishment_v1/final_lock.json`
- `train_only_reestablishment_v1/final_validation/evaluation/summary.json`

The first inference attempt on 2026-07-11 stopped before any prediction because
the generalized wrapper expected the legacy preprocess status. The wrapper-only
`--preprocess-status internal_dev_preprocess_ready` correction was applied
before source output existed; model, score, evaluator, K, denominator, and
controls were unchanged.

Regenerate the leakage-safe Codex proxy draft and local user-review UI:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm physical_validity_codex_proxy
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm physical_validity_codex_rereview_v2
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm physical_validity_codex_compare
```

The draft is not human evidence. Review `physical_validity_audit/codex_proxy_v1/review.html`
or fill `user_review.csv`.

SGFN pre-inference split erratum and checkpoint audit:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_confirmatory_target_amend
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_checkpoint_audit
```

The checkpoint audit intentionally exits `2` for the downloaded
`SGFN_full_l20.zip`: its `[20,256]` object head and `[8,256]` relation head do
not match the locked full_l160 contract. The user subsequently authorized v3
before correct-checkpoint download. The frozen v3 execution order is:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_confirmatory_target_v3_freeze
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_checkpoint_audit_v3
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_runtime_stage
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_preprocess
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_preprocess_finalize
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_inference_smoke
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_inference
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_adapter_export
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_geometry_join
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_confirmatory_metrics
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_confirmatory_audit
```

Primary outputs:

- `physical_validity_audit/frozen_v1/`: 488-row blinded audit protocol, two
  separately shuffled annotator sheets, private probability-sampling sidecar,
  and adjudication sheet.
- `physical_validity_audit/evaluation_v1/`: label-ready human V@K and semantic
  calibration evaluation; it remains `awaiting_independent_human_labels` while
  either first-pass sheet is incomplete.
- `reviewer_extension_metrics/frozen_v1/`: family-wise/global-slice metrics,
  paired 95% CIs, and fixed strong fusion baselines.
- `confirmatory_evaluation/frozen_v1/`: main-score chronology, retrospective vs
  confirmatory classification, and no-change protocol.
- `factor_isolation_protocol/frozen_v1/`: frozen feature/condition/control/
  evaluation contracts and bit-exact existing-score equivalence audit; no new
  factor metric result.
- `confirmatory_evaluation/sgfn_target_v2/`: pre-inference split identity
  erratum plus blocked checkpoint audit; no prediction or metric output.
- `confirmatory_evaluation/sgfn_target_v3/`: user-authorized correct-checkpoint
  erratum and passing full_l160 checkpoint audit.
- `physical_validity_audit/codex_rereview_v2/` and
  `codex_review_comparison/`: second same-agent blinded pass, comparison, and
  all-disagreement visual follow-up; not human agreement evidence.

## Low-K Metric Sweeps

VL-SAT full validation:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm --entrypoint python table_builder \
  /workspace/src/geocalib/evaluate_predictions.py \
  --predictions-jsonl /workspace/experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/predictions.jsonl \
  --ground-truth-jsonl /workspace/experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl \
  --verification-jsonl /workspace/experiments/H001_geom_reliability/sources/vlsat/full_validation/geometry/verification.jsonl \
  --output-dir /workspace/experiments/H001_geom_reliability/sources/vlsat/full_validation/metrics_k_sweep \
  --source-id vlsat_closed_set_full_validation \
  --ks 5 10 20 50 100
```

Open3DSG selected recovery branch:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm --entrypoint python table_builder \
  /workspace/src/geocalib/evaluate_predictions.py \
  --predictions-jsonl /workspace/experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/adapter/predictions.jsonl \
  --ground-truth-jsonl /workspace/experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl \
  --verification-jsonl /workspace/experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/geometry/verification.jsonl \
  --output-dir /workspace/experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics_k_sweep \
  --source-id open3dsg_ov_full_validation_recovery_relaxed_views_min2 \
  --ks 5 10 20 50 100
```

K=50/100 in `metrics_k_sweep/metrics.json` must match each source's locked
`metrics/metrics.json` point estimates.

## Full-Validation Source Regeneration

Use these only when intentionally regenerating row-level artifacts. They are
not needed for ordinary paper/table checks if the verified external artifact
bundle is present.

VL-SAT downstream after raw dump:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm vlsat_full_validation_adapter_export
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm vlsat_full_validation_geometry_join
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm vlsat_full_validation_metric_eval
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm vlsat_full_validation_gt_verifier_eval
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm bootstrap_ci_full_validation_vlsat
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm vlsat_failure_generator_full_validation
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm vlsat_failure_case_sampler_full_validation
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm vlsat_failure_case_inspection_full_validation
```

Open3DSG selected recovery downstream artifacts already exist under
`sources/open3dsg/full_validation/recovery_relaxed_views_min2/`. If
regenerating the branch, preserve the recovery-policy caveat:
`OPEN3DSG_MIN_VISIBLE_OBJECTS=2` plus relaxed two-scan view generation.

## Artifact Bundle Verification

```bash
bash results/h001_geom_reliability/full_validation_transition/artifact_bundle/verify_upload_bundle.sh
```

Latest verified logs:

- checksums: `logs/h001_fullval_upload_checksums_family_main_20260625_085344.log`, exit 0.
- verification: `logs/h001_fullval_upload_verify_family_main_20260625_085354.log`, exit 0.

## Paper Build

```bash
docker build -f paper/aaai/Dockerfile.tex -t h001-aaai-tex:20260526 paper/aaai
docker run --rm -v "$PWD/paper:/work" -w /work/aaai h001-aaai-tex:20260526 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Latest verified paper build:

- `logs/h001_aaai_pdf_build_family_main_20260625_084157.log`, exit 0.
- `paper/aaai/main.pdf`: 10 total pages; technical content pages 1-7; references pages 8-9; checklist page 10.

## Do Not Promote By Default

These are not current main-claim evidence unless explicitly promoted:

- historical 127-scan route;
- Open3DSG non-avg historical branch;
- Qwen-VL extension;
- `relative_horizontal`;
- `relative_lateral`;
- `attachment_deferred`;
- H001_v2 fixed-threshold or lambda-soft diagnostic runs.
