# H001 Reproducibility Runbook

Last updated: 2026-06-05 KST

This document consolidates dataset, checkpoint, environment, Docker, reproduction,
and evaluation-summary information for `experiments/H001_geom_reliability/`.
Detailed stage logs remain in the experiment subfolders.

## Resume Reading Order

Before any download, deletion, training, feature dump, or metric rerun, recover
the current research state from tracked files first.

Basic harness context:

1. `AGENTS.md`
2. `README.md`
3. `TODO.md`
4. `docs/index.md`
5. `docs/hypothesis.md`
6. `docs/paper.md`
7. `docs/reproducibility.md`
8. `summary.md`

H001 hypothesis and experiment contract:

1. `hypothesis/README.md`
2. `hypothesis/CAND-001/H001_geometry-grounded-verification/01_overview.md`
3. `hypothesis/CAND-001/H001_geometry-grounded-verification/02_method.md`
4. `hypothesis/CAND-001/H001_geometry-grounded-verification/03_data_baseline.md`
5. `hypothesis/CAND-001/H001_geometry-grounded-verification/04_results.md`
6. `hypothesis/CAND-001/H001_geometry-grounded-verification/05_audit.md`
7. `hypothesis/CAND-001/H001_geometry-grounded-verification/06_second_source.md`
8. `hypothesis/CAND-001/H001_geometry-grounded-verification/07_experiment_spec.md`

H001 Docker experiment and result state:

1. `experiments/H001_geom_reliability/README.md`
2. `experiments/H001_geom_reliability/report.md`
3. `experiments/H001_geom_reliability/commands.md`
4. `experiments/H001_geom_reliability/manifest.lock.json`
5. `experiments/H001_geom_reliability/compose.yaml`
6. `experiments/H001_geom_reliability/tables/`
7. `experiments/H001_geom_reliability/figures/figure_specs.md`
8. `experiments/H001_geom_reliability/bootstrap_ci/summary.md`

Open3DSG source-specific state:

1. `experiments/H001_geom_reliability/sources/open3dsg/README.md`
2. `experiments/H001_geom_reliability/sources/open3dsg/commands.open3dsg.md`
3. `experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml`
4. `experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection/report.md`
5. `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/README.md`
6. `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics/metrics.json`
7. `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/bootstrap_ci/summary.md`
8. `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_rows/report.md`
9. `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_cases/inspection.md`
10. `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/table_caveats/report.md`
11. `experiments/H001_geom_reliability/sources/open3dsg/full_validation/raw_clean_exit_review/report.md`
12. `experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/provenance_review/report.md`
13. `experiments/H001_geom_reliability/sources/open3dsg/raw_dump_identity/report.md`

VL-SAT full-validation source state:

1. `experiments/H001_geom_reliability/sources/vlsat/README.md`
2. `experiments/H001_geom_reliability/sources/vlsat/full_validation/README.md`
3. `experiments/H001_geom_reliability/sources/vlsat/full_validation/metrics/metrics.json`
4. `experiments/H001_geom_reliability/sources/vlsat/full_validation/bootstrap_ci/summary.md`
5. `experiments/H001_geom_reliability/sources/vlsat/full_validation/gt_eval/report.md`
6. `experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_rows/report.md`
7. `experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_cases/inspection.md`

Qwen-VL extension/resume state:

1. `experiments/H001_geom_reliability/sources/qwen_vl/README.md`
2. `experiments/H001_geom_reliability/sources/qwen_vl/report.md`
3. `experiments/H001_geom_reliability/sources/qwen_vl/status.json`
4. `experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml`
5. `experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/manifest.json`
6. `experiments/H001_geom_reliability/sources/qwen_vl/full_source_inference_plan/commands.md`
7. `experiments/H001_geom_reliability/sources/qwen_vl/full_source_runtime/manifests/`
8. `logs/qwen_vl_full_source_infer_remaining_20260527_023111.status.tsv`
9. `logs/qwen_vl_full_source_infer_remaining_20260527_023111.exit`

Paper writing state:

1. `paper/README.md`
2. `paper/preview.md`
3. `paper/progress.md`
4. `paper/appendix.md`
5. `paper/outline.md`
6. `paper/draft.md`
7. `paper/risk.md`
8. `paper/figures.md`
9. `paper/aaai/README.md`
10. `paper/aaai/inspection/report.md`

If any listed runtime result file is missing, do not infer that the experiment
was never run. First check the artifact bundle section below and then verify
whether the file is in an external bundle, ignored runtime root, or regenerated
cache. Inspect large logs or JSONL files only through counts, `head`, `tail`,
targeted `rg`, or checksums.

## Current Status

Facts:

- Active experiment root: `experiments/H001_geom_reliability/`.
- Paper-body experiment outputs must be generated through Docker.
- Full-validation `VL-SAT` artifacts, Open3DSG recovery artifacts, source
  metrics, source failure rows, deterministic qualitative failure inspections,
  Table 6, and Docker subgraph bootstrap CI are ready for the selected
  paper-facing H001 route.
- Paper handoff and planning are ready: `paper/README.md`, `paper/preview.md`,
  `paper/progress.md`, `paper/appendix.md`, `paper/outline.md`,
  `paper/draft.md`, `paper/risk.md`, `paper/aaai/`, `paper/iccv/`,
  `paper/figures.md`, and
  `paper/generated/figures/` contain the paper workspace map, current claim
  boundary, appendix/provenance table, paper skeleton, first-pass prose,
  reviewer-risk register, venue-specific LaTeX sources, figure locks, and
  reviewer-defense guardrails.
- Latest paper/reproducibility tasks completed: AAAI reproducibility checklist
  insertion, reviewer-defense main-text passes, Docker subgraph bootstrap CI,
  reproducibility artifact bundle planning, and official AAAI-26 Author Kit
  replacement/verification, plus the appendix/provenance and Open3DSG
  caveat-consistency pass. Docker build verification for `paper/aaai/` is
  complete with `h001-aaai-tex:20260526`; the latest compression
  rebuild log is `logs/h001_aaai_pdf_build_compression_20260606_105126.log`,
  with 9 total pages, technical content on pages 1-7, references on page 8,
  and the AAAI reproducibility checklist on page 9. The manuscript uses
  Open3DSG as the main open-vocabulary relation-source case study and VL-SAT as
  the controlled reproduced anchor.
- Qwen-VL is a third semantic source / modern VLM extension path. The locked
  Qwen3-VL-4B cache, runtime preflight, 3-row tiny inference smoke,
  raw-response validation, full-source promotion protocol, and full-source
  input audit, all-scope crop preflight, full-source inference runner plan, and
  shard 0000 contract validation are ready, but full Qwen inference is not
  paper metric evidence yet. Current Qwen input audit has 33,384 inferable rows
  and 134 shards. The remaining shard loop run id `20260527_023111` stopped at
  shard 0014 because the GPU guard observed utilization 36% against the 35%
  threshold; shards 0000-0013 are complete with 3,500 rows written, and resume
  should start from `qwen_full_source_shard_0014`.
- Runtime pressure is volatile: check `docker ps`, `tmux ls`, `nvidia-smi`, and
  `free -h` before launching heavy Open3DSG or Qwen jobs. The historical
  2026-05-26 Qwen-VL runtime-preflight retry was blocked by GPU guard, but the
  later 2026-05-27 runtime preflight, tiny inference smoke, crop preflight, and
  shard 0000 inference contract validation passed.

## Data Locations

Large runtime data is intentionally under ignored local roots:

| Purpose | Path |
| --- | --- |
| Raw 3RScan payload | `local_dataset/3RScan/scans/` |
| Open3DSG training root | `local_dataset/Open3DSG_staged/training_repro/` |
| Open3DSG H001 eval root | `local_dataset/Open3DSG_staged/h001_runtime/` |
| Open3DSG train/dev features | `local_dataset/Open3DSG_staged/training_repro/output/features/clip_features_h001_official_blip_top5_scales3/` |
| Open3DSG H001 eval features | `local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3/` |
| Open3DSG full-validation recovery features | `local_dataset/Open3DSG_staged/h001_full_validation_runtime/output/features/clip_features_h001_full_validation_recovery_relaxed_views_min2/` |
| Qwen-VL model cache | `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17/` |
| Qwen-VL tiny crops | `local_dataset/qwen_vl_crops/tiny_pilot/` |
| Qwen-VL full-source crops | `local_dataset/qwen_vl_crops/full_source/` |

Tracked experiment artifacts and runbooks live under:

```text
experiments/H001_geom_reliability/
docs/reproducibility.md
paper/README.md
paper/preview.md
paper/progress.md
paper/appendix.md
paper/outline.md
paper/draft.md
paper/risk.md
paper/aaai/
paper/iccv/
paper/figures.md
paper/generated/figures/
```

Hypothesis-stage smoke artifacts may exist under ignored `artifacts/` or
`**/evaluation/` paths. They are not the preferred cross-machine source of
truth; use the tracked reports, manifests, Docker commands, and locked tables
under `experiments/H001_geom_reliability/`.

## GitHub Portability And `.gitignore` Audit

Checked on 2026-05-21 KST with `git check-ignore` and `git ls-files`.

Can be committed to GitHub:

- Root workflow docs: `README.md`, `TODO.md`, `AGENTS.md`, `summary.md`.
- Reproducibility docs: `docs/reproducibility.md`, `docs/index.md`,
  `docs/paper.md`, `docs/hypothesis.md`, `docs/literature.md`.
- Paper planning/source docs: `paper/README.md`, `paper/preview.md`, `paper/progress.md`,
  `paper/appendix.md`, `paper/outline.md`, `paper/draft.md`, `paper/risk.md`, `paper/aaai/`, `paper/iccv/`, `paper/figures.md`, and
  compact figure metadata under `paper/generated/figures/`.
- Docker/reproduction source files:
  `experiments/H001_geom_reliability/Dockerfile`,
  `experiments/H001_geom_reliability/compose.yaml`,
  `experiments/H001_geom_reliability/commands.md`,
  Open3DSG/Qwen Dockerfiles and compose files, and all experiment scripts under
  `experiments/H001_geom_reliability/scripts/`.
- Reproduction summaries and compact results: `manifest*.json`, `report.md`,
  table `.md`/`.json`, bootstrap CI summaries, figure specs, Open3DSG metric
  JSON, paper caveat reports, adapter/geometry/failure summary manifests, and
  Qwen contract/runtime-plan manifests.

Intentionally not committed because of `.gitignore`:

- Large local datasets and caches under `local_dataset/`.
- Downloaded or generated model/checkpoint/feature files such as `*.ckpt`,
  `*.pth`, `*.pt`, `*.npy`, `*.npz`, archives, and scan/mesh binaries.
- Large row-level runtime outputs such as Open3DSG `raw_dump/raw.jsonl`,
  adapter `predictions.jsonl`, geometry `verification.jsonl`, failure
  `rows.jsonl`, and queue/record JSONL files.
- Ignored hypothesis/runtime roots such as `artifacts/`, `**/artifacts/`, and
  `**/evaluation/`.

Implication for another computer:

- The GitHub repo can carry the exact commands, Docker setup, paper/research
  state, compact manifests, and metric summaries.
- Another machine must either rebuild/download the ignored runtime payloads
  using the commands in this file, or receive a separate data bundle containing
  `local_dataset/`, Open3DSG checkpoint/features/raw JSONL, VL-SAT checkpoints,
  and the Qwen-VL model cache.
- Do not rely on GitHub alone to carry the trained Open3DSG checkpoint or large
  raw row outputs; they are intentionally excluded.
- Open3DSG feature `.pt` files are regenerable, but the cost is high. The
  current train/dev feature cache is about 131 GB and the H001 eval feature
  cache is about 13 GB. The previous official TopK5/scales3 train/dev feature
  dump required multiple resumable tmux runs over several days on the local RTX
  5090 setup, while the H001 eval feature cache required a bounded shard loop.
  Prefer transferring these feature directories if fast setup matters; regenerate
  only when storage transfer is impractical or provenance needs to be rebuilt.

## Reproducibility Artifact Bundle Plan

The public GitHub repo should carry source code, paper source, Dockerfiles,
compose files, runbooks, compact manifests, and metric summaries. Large
runtime artifacts should be published separately, for example through Google
Drive, Zenodo, or Hugging Face Dataset, because several files are too large or
license-sensitive for normal GitHub commits.

## Open3DSG Dual-Route Retention Policy

Keep both Open3DSG full-validation routes. They answer different reviewer
questions and neither should be deleted during cleanup.

| Route | Path | Coverage | Role |
| --- | --- | ---: | --- |
| Unmodified source route | `experiments/H001_geom_reliability/sources/open3dsg/full_validation/` | 533/548 loadable contexts | Public-source/as-is evidence. The 15 missing contexts are Open3DSG source-runtime preprocess visibility drops, not missing GT annotations. |
| Recovery route | `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/` | 548/548 contexts | Coverage-completion variant. Must disclose `OPEN3DSG_MIN_VISIBLE_OBJECTS=2` and relaxed two-scan view generation. |

Reporting rule:

- Use the unmodified source route to defend against "you tuned Open3DSG
  preprocessing for your method" objections.
- Use the recovery route to show the conclusion is not an artifact of the 15
  missing contexts.
- If table space permits, report both Open3DSG rows. If only one row is shown in
  the main table, the other route must appear in the caption, appendix, or
  sensitivity discussion.

Provenance review:

- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/raw_clean_exit_review/`
  records the clean-exit retry/equivalence closeout for the unmodified 533/548
  branch. The expected retry artifact is no longer present after cleanup, so the
  branch keeps its process-level exit-137 caveat.
- `experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/provenance_review/`
  records the historical 127-scan R2 `388/388` sensitivity review. The
  clean-return raw files are row/predicate-score equivalent to the canonical R2
  raw dump after excluding run-metadata fields, so R2 is ready as appendix
  sensitivity evidence despite process-level teardown/OOM exit `137`.

Recommended release tiers:

| Tier | Include | Purpose | Current size / count | Release note |
| --- | --- | --- | --- | --- |
| A. GitHub tracked source | `README.md`, `TODO.md`, `docs/`, `paper/aaai/`, `experiments/H001_geom_reliability/{Dockerfile,compose.yaml,commands.md,scripts/,reports,compact manifests}` | Rebuild commands and paper source | small | Commit to GitHub. |
| B. Full-validation paper result bundle | selected official non-avg Open3DSG checkpoint, full-validation VL-SAT row JSONL/metrics/bootstrap/failure artifacts, Open3DSG recovery branch row JSONL/metrics/bootstrap/failure artifacts, table outputs, manifest locks | Reproduce current paper-facing full-validation tables without rerunning multi-day feature/training jobs | row JSONL counts: VL-SAT predictions 957,008, verification 957,008, failure rows 59,841; Open3DSG recovery raw 26,938, predictions 695,916, verification 695,916, failure rows 82,155 | Good candidate for Google Drive or Zenodo. |
| C. Large feature-cache transfer bundle | Open3DSG train/dev features and H001 eval features | Fast full rerun without regenerating features | train/dev 131 GB; eval 13 GB | Optional; high storage cost but saves multi-day regeneration. |
| D. External-only dependencies | raw 3RScan/3DSSG/VL-SAT data, official third-party checkpoints, Qwen-VL HF cache | Dataset/model access under original terms | Qwen cache 8.3 GB; raw datasets much larger | Prefer documented download/rebuild over redistribution. |

Full-validation paper result bundle paths:

```text
local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt
experiments/H001_geom_reliability/full_validation_transition/scope_contract/
experiments/H001_geom_reliability/full_validation_transition/artifact_bundle/
experiments/H001_geom_reliability/manifest.lock.json
experiments/H001_geom_reliability/report.md
experiments/H001_geom_reliability/tables/
experiments/H001_geom_reliability/sources/vlsat/full_validation/raw/raw.jsonl
experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/predictions.jsonl
experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl
experiments/H001_geom_reliability/sources/vlsat/full_validation/geometry/verification.jsonl
experiments/H001_geom_reliability/sources/vlsat/full_validation/metrics/metrics.json
experiments/H001_geom_reliability/sources/vlsat/full_validation/bootstrap_ci/summary.json
experiments/H001_geom_reliability/sources/vlsat/full_validation/gt_eval/metrics.json
experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_rows/rows.jsonl
experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_cases/queue.jsonl
experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_cases/inspection.json
experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/raw_dump/raw.jsonl
experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/adapter/predictions.jsonl
experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/geometry/verification.jsonl
experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics/metrics.json
experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/bootstrap_ci/summary.json
experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_rows/rows.jsonl
experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_cases/queue.jsonl
experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_cases/inspection.json
experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/table_caveats/
experiments/H001_geom_reliability/sources/open3dsg/full_validation/raw_clean_exit_review/
experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection/
```

Checked row counts for the current full-validation row files:

```text
VL-SAT raw/raw.jsonl: 548
VL-SAT adapter/predictions.jsonl: 957,008
VL-SAT adapter/ground_truth.jsonl: 11,254
VL-SAT geometry/verification.jsonl: 957,008
VL-SAT failure_rows/rows.jsonl: 59,841
VL-SAT failure_cases/queue.jsonl: 36
Open3DSG recovery raw_dump/raw.jsonl: 26,938
Open3DSG recovery adapter/predictions.jsonl: 695,916
Open3DSG recovery geometry/verification.jsonl: 695,916
Open3DSG recovery failure_rows/rows.jsonl: 82,155
Open3DSG recovery failure_cases/queue.jsonl: 36
```

Full-validation bundle creation template:

```bash
mkdir -p release logs
ts=$(date +%Y%m%d_%H%M%S)
tar --zstd -cf release/h001_full_validation_results_${ts}.tar.zst \
  local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt \
  experiments/H001_geom_reliability/full_validation_transition/scope_contract \
  experiments/H001_geom_reliability/full_validation_transition/artifact_bundle \
  experiments/H001_geom_reliability/manifest.lock.json \
  experiments/H001_geom_reliability/report.md \
  experiments/H001_geom_reliability/tables \
  experiments/H001_geom_reliability/sources/vlsat/full_validation \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2 \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/table_caveats \
  experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection
sha256sum release/h001_full_validation_results_${ts}.tar.zst > release/h001_full_validation_results_${ts}.sha256
```

Historical verified 127-scan bundle:

```text
status: completed_verified_then_local_archive_deleted_on_2026-06-05
session: h001_core_bundle_20260526_160957
cwd: /home/yoohyun/research
log: logs/h001_core_bundle_20260526_160957.log
exit: logs/h001_core_bundle_20260526_160957.exit
output: release/h001_core_results_20260526_160957.tar.zst (local archive deleted after cleanup)
checksum: release/h001_core_results_20260526_160957.sha256 (local checksum deleted after cleanup)
size: 423 MB
archive_entries: 89
exit_code: 0
checksum_status: OK
row_counts: raw_dump 19,162; predictions 496,600; verification 496,600; failure_rows 57,736; qualitative_queue 36; total 1,070,134
metric_status: ready
exact command: tar --zstd -cf release/h001_core_results_20260526_160957.tar.zst local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt experiments/H001_geom_reliability/manifest.lock.json experiments/H001_geom_reliability/report.md experiments/H001_geom_reliability/tables experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl experiments/H001_geom_reliability/sources/open3dsg/adapter/predictions.jsonl experiments/H001_geom_reliability/sources/open3dsg/geometry/verification.jsonl experiments/H001_geom_reliability/sources/open3dsg/metrics/metrics.json experiments/H001_geom_reliability/sources/open3dsg/failure_rows/rows.jsonl experiments/H001_geom_reliability/sources/open3dsg/failure_cases/queue.jsonl experiments/H001_geom_reliability/sources/open3dsg/*/manifest.json experiments/H001_geom_reliability/sources/open3dsg/*/report.md
verification: sha256sum -c release/h001_core_results_20260526_160957.sha256 && wc -l experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl experiments/H001_geom_reliability/sources/open3dsg/adapter/predictions.jsonl experiments/H001_geom_reliability/sources/open3dsg/geometry/verification.jsonl experiments/H001_geom_reliability/sources/open3dsg/failure_rows/rows.jsonl experiments/H001_geom_reliability/sources/open3dsg/failure_cases/queue.jsonl && jq -r '.status' experiments/H001_geom_reliability/sources/open3dsg/metrics/metrics.json
boundary: historical/sensitivity bundle only; current paper-facing bundle is the full-validation plan above. The local tar/checksum copy was deleted on 2026-06-05 after the full-validation route became the default handoff path.
```

Full-validation bundle verification template after download/extract:

```bash
sha256sum -c release/h001_full_validation_results_<ts>.sha256
wc -l \
  experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/predictions.jsonl \
  experiments/H001_geom_reliability/sources/vlsat/full_validation/geometry/verification.jsonl \
  experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_rows/rows.jsonl \
  experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_cases/queue.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/raw_dump/raw.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/adapter/predictions.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/geometry/verification.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_rows/rows.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_cases/queue.jsonl
jq -r '.status' experiments/H001_geom_reliability/sources/vlsat/full_validation/metrics/metrics.json
jq -r '.status' experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics/metrics.json
jq -r '.status' experiments/H001_geom_reliability/sources/vlsat/full_validation/failure_cases/inspection.json
jq -r '.status' experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/failure_cases/inspection.json
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm table_builder'
```

Large feature-cache transfer template, only if full rerun speed matters:

```bash
mkdir -p release
ts=$(date +%Y%m%d_%H%M%S)
tar --zstd -cf release/h001_open3dsg_features_${ts}.tar.zst \
  local_dataset/Open3DSG_staged/training_repro/output/features/clip_features_h001_official_blip_top5_scales3 \
  local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3 \
  local_dataset/Open3DSG_staged/h001_full_validation_runtime/output/features/clip_features_h001_full_validation_recovery_relaxed_views_min2
sha256sum release/h001_open3dsg_features_${ts}.tar.zst > release/h001_open3dsg_features_${ts}.sha256
```

Feature transfer verification:

```bash
sha256sum -c release/h001_open3dsg_features_<ts>.sha256
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm feature_audit'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm feature_audit_h001_eval'
```

Do not put Qwen-VL model weights in the default core bundle. The Qwen path is
optional/non-metric and can be recreated from the fixed Hugging Face model id,
revision, and local-dir command above. If the goal is to continue the current
Qwen full-source run on another computer, preserve or transfer these paths:

```text
local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17/
local_dataset/qwen_vl_crops/full_source/
experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/
experiments/H001_geom_reliability/sources/qwen_vl/full_source_inference_plan/
experiments/H001_geom_reliability/sources/qwen_vl/full_source_runtime/
experiments/H001_geom_reliability/sources/qwen_vl/status.json
experiments/H001_geom_reliability/sources/qwen_vl/README.md
experiments/H001_geom_reliability/sources/qwen_vl/report.md
experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml
experiments/H001_geom_reliability/sources/qwen_vl/Dockerfile.qwen
experiments/H001_geom_reliability/scripts/run_qwen_vl_full_source_inference.py
experiments/H001_geom_reliability/scripts/run_qwen_vl_full_source_shard_loop.sh
experiments/H001_geom_reliability/scripts/plan_qwen_vl_full_source_inference.py
logs/qwen_vl_full_source_infer_remaining_20260527_023111.log
logs/qwen_vl_full_source_infer_remaining_20260527_023111.status.tsv
logs/qwen_vl_full_source_infer_remaining_20260527_023111.exit
```

## Environment And Docker

Build the main H001 table/evaluation image:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml build'
```

Build and check the Open3DSG reproduction image:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml build'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm env_check'
```

Build and check the Qwen-VL runtime image/cache:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml build'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_cache_verify'
```

## Data Download And Staging

VL-SAT / 3DSSG local roots:

- Source/runtime root: `local_dataset/VLSAT_code/CVPR2023-VLSAT/`.
- Staged validation roots:
  `local_dataset/VLSAT_staged/CVPR2023-VLSAT/` and
  `local_dataset/VLSAT_staged/h001_validation_hardened/CVPR2023-VLSAT/`.
- The official VL-SAT `data_processing/README.md` also records a Google Drive
  data link:
  `https://drive.google.com/file/d/1V_QIDvu1fZqKkjP2Kg41HNCjX8TPfH6u/view?usp=sharing`.

VL-SAT data download template if rebuilding the local staged root:

```bash
mkdir -p logs local_dataset/VLSAT_staged
python -m gdown 'https://drive.google.com/uc?id=1V_QIDvu1fZqKkjP2Kg41HNCjX8TPfH6u' -O local_dataset/VLSAT_staged/vlsat_data_processing_payload
```

Audit current Open3DSG/3RScan payload readiness:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_payload --repo-root /workspace'
```

Run a small resumable download/extract pilot:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_payload --repo-root /workspace --download-missing --extract-sequence --limit 1 --workers 2'
```

Run a resumable batch:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_payload --repo-root /workspace --download-missing --extract-sequence --limit 20 --workers 4 --timeout 300 --retries 1'
```

For long batches, use `tmux` and timestamped logs under `logs/`. Example:

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_open3dsg_payload_batch \
  "cd /home/yoohyun/research && bash -lc 'set -o pipefail; sg docker -c '\''env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_payload --repo-root /workspace --download-missing --extract-sequence --limit 100 --workers 4 --timeout 300 --retries 1'\''; rc=\$?; printf \"%s\n\" \"\$rc\" > logs/open3dsg_payload_batch_${ts}.exit; exit \$rc' > logs/open3dsg_payload_batch_${ts}.log 2>&1"
```

Stage H001 held-out eval scan symlinks:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm h001_eval_payload'
```

## Open3DSG Feature `.pt` Regeneration

Feature regeneration is possible and Docker-scripted, but it is one of the most
expensive parts of the reproduction. It requires the Open3DSG payload, view
pickles, preprocessing, model caches, and GPU runtime to be ready.

Current feature caches:

| Feature cache | Path | Current size | Expected complete ids |
| --- | --- | ---: | ---: |
| train/dev official BLIP TopK5/scales3 | `local_dataset/Open3DSG_staged/training_repro/output/features/clip_features_h001_official_blip_top5_scales3/` | about 131 GB | 3,900 |
| H001 eval BLIP TopK5/scales3 | `local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3/` | about 13 GB | 377 loadable ids |
| full-validation recovery BLIP TopK5/scales3 | `local_dataset/Open3DSG_staged/h001_full_validation_runtime/output/features/clip_features_h001_full_validation_recovery_relaxed_views_min2/` | local cache | 548 loadable ids |

Expected role directories inside each cache:

```text
export_obj_clip_valids/
export_obj_clip_emb_clip_OpenSeg_Topk_5_scales_3_vis_crit_0.19999999999999998_vis_crit_mask_0.1/
export_rel_clip_emb_clip_BLIP_Topk_5_scales_3_vis_crit_0.19999999999999998/
```

### Preconditions

Build and check the Open3DSG image/cache first:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml build'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm env_check'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm cache_preflight'
```

Stage train/dev views and preprocessed-ready splits if starting from raw data:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_train_root'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_views_full'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_preprocess_full'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_preprocess_filter'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm validation_views_full'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm validation_preprocess_full'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm validation_preprocess_filter'
```

Check runtime pressure before launching feature dumps:

```bash
tmux ls || true
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}'
nvidia-smi
free -h
```

### Regenerate Train/Dev Feature Cache

This command regenerates or resumes the official H001 Open3DSG train/dev
feature cache. It uses skip-existing behavior, so it can resume a partially
complete output directory.

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_open3dsg_dump_features \
  "cd /home/yoohyun/research && bash -lc 'set -o pipefail; echo \"started_at=\$(date -Is)\"; echo \"cwd=\$(pwd)\"; nvidia-smi --query-gpu=timestamp,index,name,memory.total,memory.used,memory.free,utilization.gpu --format=csv,noheader,nounits || true; sg docker -c '\''env UID=\$(id -u) GID=\$(id -g) OPEN3DSG_DUMP_WORKERS=0 OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=2 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:128 docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm dump_features_3rscan'\''; rc=\$?; echo \"finished_at=\$(date -Is)\"; echo \"exit_code=\$rc\"; printf \"%s\n\" \"\$rc\" > logs/open3dsg_dump_features_regen_${ts}.exit; exit \$rc' > logs/open3dsg_dump_features_regen_${ts}.log 2>&1"
```

Verify train/dev feature completion:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm feature_audit'
```

Expected verification result:

```text
Status: ready
Complete ids: 3900/3900
Split coverage: train 3744/3744, validation 156/156
```

Lightweight progress check without scanning logs:

```bash
find local_dataset/Open3DSG_staged/training_repro/output/features/clip_features_h001_official_blip_top5_scales3 -type f -name '*.pt' -printf '%f\n' \
  | sed 's/\.[^.]*$//' | sort | uniq -c | awk '$1==3{c++} END{print c+0}'
```

### Regenerate Historical H001 Eval Feature Cache

This section is for the historical 127-scan H001 eval branch. The current
paper-facing Open3DSG result is the full-validation
`recovery_relaxed_views_min2/` branch, which uses the selected official non-avg
checkpoint and the full-validation recovery feature cache listed above. Use the
historical H001 eval cache only to reproduce the 127-scan sensitivity/history
route.

Historical 127-scan checkpoint path:

```text
local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt
```

Current full-validation recovery feature cache:

```text
local_dataset/Open3DSG_staged/h001_full_validation_runtime/output/features/clip_features_h001_full_validation_recovery_relaxed_views_min2/
```

Stage held-out eval payload:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm h001_eval_payload'
```

Run the bounded shard loop. This is the preferred route because the full H001
eval feature dump had partial exit-137 failures before the shard loop was added.

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_open3dsg_dump_features_h001_eval_shard_loop \
  "cd /home/yoohyun/research && bash -lc 'set -o pipefail; python experiments/H001_geom_reliability/scripts/run_open3dsg_h001_eval_feature_shards.py --repo-root /home/yoohyun/research --max-new-ids 5; rc=\$?; echo \"finished_at=\$(date -Is)\"; echo \"exit_code=\$rc\"; printf \"%s\n\" \"\$rc\" > logs/open3dsg_dump_features_h001_eval_shard_loop_${ts}.exit; exit \$rc' > logs/open3dsg_dump_features_h001_eval_shard_loop_${ts}.log 2>&1"
```

Verify H001 eval feature completion:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm feature_audit_h001_eval'
```

Expected verification result:

```text
Complete covered loadable ids: 377/377
Missing complete ids: 0
Known caveat: validation_missing_preprocessed:11
```

Lightweight progress check:

```bash
find local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3 -type f -name '*.pt' -printf '%f\n' \
  | sed 's/\.[^.]*$//' | sort | uniq -c | awk '$1==3{c++} END{print c+0}'
```

Cost warning:

- Train/dev feature regeneration is very expensive: about 131 GB output and
  past H001 runs required multiple resumable tmux sessions over several days.
- H001 eval feature regeneration is smaller but still expensive: about 13 GB
  output, 377 complete loadable ids, and prior successful completion required a
  shard loop after partial failures.
- If moving to another computer for writing or metric regeneration only,
  transferring the feature directories is faster. If transferring is not
  practical, the commands above can regenerate them from raw/staged data.

## Checkpoints And Model Downloads

VL-SAT:

- Official checkpoint link recorded in local README:
  `https://drive.google.com/file/d/1_C-LXRlSobupApb-JsajKG5oxKnfKgdx/view?usp=sharing`.
- Local checkpoint root:
  `local_dataset/VLSAT_code/CVPR2023-VLSAT/output/ckp/Mmgnet/3dssg/`.
- Local CLIP adapter checkpoint:
  `local_dataset/VLSAT_code/CVPR2023-VLSAT/clip_adapter/checkpoint/origin_mean.pth`.
- Current local files include `rel_predictor_3d_best.pth`,
  `rel_encoder_3d_best.pth`, `obj_encoder_best.pth`, `mmg_best.pth`, and the
  matching optimizer/config scheduler files.

Download template if the VL-SAT checkpoint root must be rebuilt:

```bash
mkdir -p logs local_dataset/VLSAT_code/CVPR2023-VLSAT
python -m gdown 'https://drive.google.com/uc?id=1_C-LXRlSobupApb-JsajKG5oxKnfKgdx' -O local_dataset/VLSAT_code/CVPR2023-VLSAT/vlsat_checkpoint_download
```

Verify local VL-SAT checkpoint files:

```bash
find local_dataset/VLSAT_code/CVPR2023-VLSAT/output/ckp/Mmgnet/3dssg -maxdepth 1 -type f -name '*_best.pth' | sort
test -f local_dataset/VLSAT_code/CVPR2023-VLSAT/clip_adapter/checkpoint/origin_mean.pth
```

Open3DSG:

- The official Open3DSG repository did not expose a trusted final trained
  relation checkpoint in the checked path. The H001 Open3DSG checkpoint is
  generated by our Docker reproduction.
- Current paper-facing full-validation selected checkpoint:
  `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt`.
- Selection signal: train-dev `val/loss`
  0.5724539160728455 at step 13103; sha256
  `ca86d429b19e846aec2bfff014256bf36f6f90da07e566b90c461d6eca8d76bb`.
- Current paper-facing use: full-validation
  `sources/open3dsg/full_validation/recovery_relaxed_views_min2/` row-level
  JSONL, metrics, bootstrap CI, failure rows, qualitative cases, and Table 6.
  Report the recovery-policy caveat because this branch relaxes the Open3DSG
  visible-object preprocess gate to `min_visible=2` and regenerates relaxed
  views for two scans.
- Historical 127-scan averaged-BLIP checkpoint:
  `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt`.
- Historical selection signal: train-dev `val/loss` 0.32881081104278564 at step
  13103. This route remains the stronger 127-scan sensitivity/history branch by
  train-dev loss, but it is not the current paper-facing full-validation
  denominator.

Open3DSG component model downloads, if the staged checkpoint/component root must
be rebuilt:

```bash
python -m gdown 'https://drive.google.com/uc?id=1BfvxB6eo3XksE6AfMUgoBHwzVYce1ed1' -O local_dataset/Open3DSG_staged/training_repro/output/checkpoints/blip2_positional_embedding.pt
python -m gdown 'https://drive.google.com/uc?id=18RIPkqlt7KXiG8BzxNIweMxYvjlMZifO' -O local_dataset/Open3DSG_staged/training_repro/output/checkpoints/pointnet.pth
python -m gdown 'https://drive.google.com/uc?id=14oH-eZjyB4rlh2-_25pNpGBhbegKi16I' -O local_dataset/Open3DSG_staged/training_repro/output/checkpoints/pointnet2_ulip.pt
```

OpenSeg component model files are hosted under
`https://storage.googleapis.com/cloud-tpu-checkpoints/detection/projects/openseg/colab/exported_model/`
and are verified by Docker `cache_preflight`.

Qwen-VL:

- Model id: `Qwen/Qwen3-VL-4B-Instruct`
- Revision: `ebb281ec70b05090aa6165b016eac8ec08e71b17`
- Local dir:
  `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17/`
- Download status: completed, exit code 0, Docker `qwen_vl_cache_verify`
  status `model_cache_ready`.

Exact Qwen-VL background download command used:

```bash
mkdir -p logs experiments/H001_geom_reliability/sources/qwen_vl/model_cache
tmux new-session -d -s h001_qwen_vl_model_download "cd /home/yoohyun/research && bash -lc 'set -o pipefail; sg docker -c '\''env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml build qwen_vl_model_download && env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_model_download && env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_cache_verify'\''; rc=$?; printf \"%s\n\" \"$rc\" > logs/qwen_vl_model_download_20260512_082830.exit; exit $rc' > logs/qwen_vl_model_download_20260512_082830.log 2>&1"
```

## Experiment Reproduction Commands

Regenerate paper-facing H001 tables/report from locked artifacts:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm table_builder'
```

Recreate Open3DSG adapter, geometry join, metrics, and Table 6 from the
identity-audited raw dump:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_adapter_raw_dump'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_geometry_join'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_metric_eval'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm table_builder'
```

Regenerate Open3DSG failure-analysis rows and qualitative case queue:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_failure_generator_real'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_failure_case_sampler'
```

Qwen-VL runtime smoke has already passed. Use these commands only if rebuilding
or verifying a new computer:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_runtime_preflight'
sg docker -c 'env UID=$(id -u) GID=$(id -g) QWEN_VL_TINY_INFERENCE_LIMIT=3 docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_tiny_inference_smoke'
```

Resume Qwen-VL full-source inference only after GPU guard is acceptable. The
current clean resume point is `qwen_full_source_shard_0014`; shards 0000-0013
are already complete with 3,500 rows written.

```bash
tmux ls || true
nvidia-smi
free -h
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_qwen_vl_infer_remaining \
  "cd /home/yoohyun/research && bash -lc 'set -o pipefail; QWEN_VL_LOOP_RUN_ID=${ts} QWEN_VL_LOOP_START_SUFFIX=0014 QWEN_VL_LOOP_END_SUFFIX=0133 bash experiments/H001_geom_reliability/scripts/run_qwen_vl_full_source_shard_loop.sh; rc=\$?; printf \"%s\n\" \"\$rc\" > logs/qwen_vl_full_source_infer_remaining_${ts}.exit; exit \$rc' > logs/qwen_vl_full_source_infer_remaining_${ts}.log 2>&1"
```

After the loop finishes, Qwen still is not paper evidence until all-shard
validation, adapter export, geometry join, metrics, controls, bootstrap CI if
reported, and audit are completed through Docker.

Raw Open3DSG source eval has clean provenance through the v14 streaming
same-path resume. The canonical raw dump remains `raw_dump/raw.jsonl`, and the
streaming resume output `raw_stream_retry_20260519_092628.jsonl` completed with
exit 0, manifest status `raw_dump_stream_complete`, 377/377 completed batches,
19,162 rows, dropped/invalid partial rows 0/0, and SHA256 matching the canonical
raw dump. Earlier exit-137 attempts are historical run records.

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects'
```

## Verification Commands

Check key row counts:

```bash
wc -l \
  experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/adapter/predictions.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/geometry/verification.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/failure_rows/rows.jsonl \
  experiments/H001_geom_reliability/sources/open3dsg/failure_cases/queue.jsonl
```

Check Open3DSG metric status and key conditions:

```bash
jq -r '.status' experiments/H001_geom_reliability/sources/open3dsg/metrics/metrics.json
jq -r '.conditions | to_entries[] | select(.key=="semantic_only" or .key=="probabilistic_recalibrated" or .key=="rule_verified_point_subtype" or .key=="control_family_specific_p_geom_valid") | [.key, (.value.recall.by_k["50"].recall|tostring), (.value.recall.by_k["100"].recall|tostring), (.value.violation_rate.by_k["50"].violation_rate|tostring), (.value.violation_rate.by_k["100"].violation_rate|tostring)] | @tsv' experiments/H001_geom_reliability/sources/open3dsg/metrics/metrics.json
```

Check Qwen-VL cache:

```bash
cat logs/qwen_vl_model_download_20260512_082830.exit
find local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17 -maxdepth 2 -type f | wc -l
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/qwen_vl/compose.qwen.yaml run --rm qwen_vl_cache_verify'
```

## Artifact And Evaluation Summary

`VL-SAT` locked H001 result:

| Condition | R@50 | R@100 | Violation@50 | Violation@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.9599 | 0.9894 | 0.0247 | 0.0469 |
| `probabilistic_recalibrated` | 0.9642 | 0.9921 | 0.0234 | 0.0391 |
| `family_specific_p_geom_valid` | 0.9619 | 0.9914 | 0.0204 | 0.0310 |

`VL-SAT` full official validation rerun:

- artifact root:
  `experiments/H001_geom_reliability/sources/vlsat/full_validation/`
- command index: `experiments/H001_geom_reliability/commands.md`
- status: `vlsat_full_validation_metric_bundle_ready`
- scope: 157 scans, 548 contexts, 957,008 prediction rows, 11,254 GT rows,
  3,972 H001-family GT rows

| Condition | R@50 | R@100 | Violation@50 | Violation@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.9272 | 0.9635 | 0.0268 | 0.0476 |
| `probabilistic_recalibrated` | 0.9305 | 0.9688 | 0.0229 | 0.0404 |
| `rule_verified_point_subtype` | 0.9257 | 0.9627 | 0.0000 | 0.0000 |
| `family_specific_p_geom_valid` | 0.9288 | 0.9683 | 0.0206 | 0.0333 |

Additional `VL-SAT` verifier/audit evidence:

- Full-validation GT-positive rows: 3,972.
- Full-validation GT-derived negatives: 3,972.
- Full-validation `p_geom_valid` AUROC/AUPRC: 0.9772 / 0.9729.
- Historical reduced visual sanity check: 50/50 labels, reviewer `yhkim`,
  `ready_sanity_pass`.

Open3DSG full-validation recovery result:

| Condition | R@50 | R@100 | Violation@50 | Violation@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.4096 | 0.5161 | 0.1386 | 0.1242 |
| `probabilistic_recalibrated` | 0.3975 | 0.5723 | 0.0606 | 0.0811 |
| `rule_verified_point_subtype` | 0.4295 | 0.5368 | 0.0000 | 0.0000 |
| `family_specific_p_geom_valid` | 0.4658 | 0.6047 | 0.0286 | 0.0341 |

Open3DSG historical 127-scan second-source result:

| Condition | R@50 | R@100 | Violation@50 | Violation@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.3945 | 0.4963 | 0.1326 | 0.1195 |
| `probabilistic_recalibrated` | 0.3843 | 0.5580 | 0.0575 | 0.0803 |
| `rule_verified_point_subtype` | 0.4149 | 0.5238 | 0.0000 | 0.0000 |
| `family_specific_p_geom_valid` | 0.4530 | 0.5984 | 0.0228 | 0.0311 |

Open3DSG historical 127-scan artifact summary:

- Raw dump: `raw_dump/raw.jsonl`, 19,162 rows.
- Adapter predictions: 496,600 rows; 62 raw rows filtered outside the fixed
  H001 object context.
- Geometry join: 496,600/496,600 rows preserved; 114,600 geometry-checkable
  rows scored.
- Real failure-analysis rows: 57,736 rows, 0 validation errors.
- Qualitative queue: 36 high-severity cases from 6,162 visual-audit candidates.
- Required caveats are frozen under
  `experiments/H001_geom_reliability/sources/open3dsg/paper_caveats/`:
  filtered train split, averaged-BLIP Open3DSG variant, covered loadable H001
  eval scope, residual calibration risk, and `validation_missing_preprocessed:11`.

## Cleanup Candidates

Cleanup state, 2026-06-06 KST: the user-approved paths below were deleted from
the local workspace. They were not required for the current paper-facing
full-validation claim. Do not delete primary full-validation artifacts, raw
datasets, selected checkpoints, feature caches needed for reruns, Qwen resume
files, `sources/attachment_deferred/full_source_g5d/`, Open3DSG
`raw_clean_exit_review/`, or Open3DSG `h001_covered_recovery/provenance_review/`
unless the corresponding transfer/archive has been verified.

Deleted failed or superseded Open3DSG full-validation attempts:

```text
experiments/H001_geom_reliability/sources/open3dsg/full_validation/raw_dump_exit0_retry_20260604_235944/
experiments/H001_geom_reliability/sources/open3dsg/full_validation/raw_dump_exit0_retry_20260605_000241/
experiments/H001_geom_reliability/sources/open3dsg/full_validation/preprocess_retry2/
experiments/H001_geom_reliability/sources/open3dsg/full_validation/preprocess_recovery/
experiments/H001_geom_reliability/sources/open3dsg/full_validation/preprocess_recovery_relaxed_min2/
experiments/H001_geom_reliability/sources/open3dsg/full_validation/preprocess_shards/
experiments/H001_geom_reliability/sources/open3dsg/full_validation/feature_seed/
```

Deleted local generated Python cache:

```text
experiments/H001_geom_reliability/scripts/__pycache__/
hypothesis/CAND-001/H001_geometry-grounded-verification/tools/__pycache__/
paper/scripts/__pycache__/
local_dataset/**/__pycache__/
```

Deleted superseded attachment/lateral intermediate artifacts:

```text
experiments/H001_geom_reliability/sources/attachment_deferred/full_source_g5d_smoke/
```

Deleted failed or superseded logs whose important status is already summarized in the
reports/manifests:

```text
logs/h001_geom_reliability_build_fullval_failure_20260605_102448.log
logs/h001_geom_reliability_build_fullval_failure_20260605_102455.log
logs/open3dsg_full_validation_raw_exit0_retry_20260604_235944.*
logs/open3dsg_full_validation_raw_exit0_retry_20260605_000241.*
logs/open3dsg_full_validation_preprocess_retry2_20260604_234921.*
logs/open3dsg_full_validation_preprocess_missing_force_20260604_220501.*
logs/open3dsg_full_validation_preprocess_o180*
logs/open3dsg_full_validation_preprocess_o370*
logs/open3dsg_full_validation_feature_seed_*
logs/h001_attachment_g5d_smoke_20260606_113549.*
logs/h001_attachment_g5d_build_20260606_113531.*
logs/open3dsg_raw_provenance_review_build_20260606_205847.*
logs/h001_relative_lateral_policy_freeze_build_20260606_163118.log
logs/h001_relative_lateral_policy_freeze_run_20260606_163118.log
logs/h001_relative_lateral_train_dev_lock_build_20260606_165533.log
logs/h001_relative_lateral_train_dev_lock_run_20260606_165533.log
logs/h001_relative_lateral_train_dev_lock_rebuild_20260606_165611.log
logs/h001_relative_lateral_train_dev_lock_rerun_20260606_165611.log
logs/h001_relative_lateral_dev_diagnosis_build_20260606_170300.log
logs/h001_relative_lateral_dev_diagnosis_run_20260606_170300.log
```

Deleted historical release copy. The original row-level files and reports remain
under their source artifact roots:

```text
release/h001_core_results_20260526_160957.tar.zst
release/h001_core_results_20260526_160957.sha256
```
