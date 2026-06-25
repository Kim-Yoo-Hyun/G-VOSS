# H001 Commands

Last updated: 2026-06-25

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
