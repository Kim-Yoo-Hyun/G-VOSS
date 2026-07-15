# H001 Reproducibility Runbook

Last updated: 2026-07-16 KST

This document consolidates dataset, checkpoint, environment, Docker, reproduction,
and evaluation-summary information for `experiments/H001_geom_reliability/`.
Detailed stage logs remain in the experiment subfolders.

## Canonical H001 Map

| Purpose | Canonical path |
| --- | --- |
| current research state and claim | `summary.md` |
| current task board | `TODO.md` |
| focused Docker entry point | `configs/h001/compose.structured.yaml` |
| full recovery/service registry | `configs/h001/compose.yaml` |
| frozen relation-algebra method | `experiments/H001_geom_reliability/relation_algebra_v1/` |
| primary applicability-routed evaluation | `experiments/H001_geom_reliability/support_contact_routing_v1/evaluation/` |
| synchronized unrestricted/comparator evaluation | `experiments/H001_geom_reliability/structured_main_v1/evaluation/` |
| matched nonlinear comparison | `experiments/H001_geom_reliability/supervision_matched_nonlinear_v1/evaluation/` |
| same-route product/rank/RRF/MLP comparison | `experiments/H001_geom_reliability/routed_comparators_v1/evaluation/` |
| Open3DSG 533/548 sensitivity | `experiments/H001_geom_reliability/open3dsg_official_route_v1/evaluation/` |
| paper-facing routed K=50/100 ablations | `experiments/H001_geom_reliability/structured_ablation_v1/routed_public_full_evaluation/` |
| supplemental unrestricted ablations | `experiments/H001_geom_reliability/structured_ablation_v1/evaluation/` |
| primary scan-cluster intervals | `experiments/H001_geom_reliability/support_contact_routing_v1/scan_cluster_sensitivity/` |
| held-out verifier-primitive diagnostic | `experiments/H001_geom_reliability/held_out_primitive_v1/evaluation/` |
| counterfactual-policy sensitivity | `experiments/H001_geom_reliability/counterfactual_sensitivity_v1/evaluation/` |
| ReplicaSSG locked final-method transfer | `experiments/H001_geom_reliability/sources/replicassg/final_method_transfer_v1/` |
| compact result report | `results/h001_geom_reliability/report.md` |
| active manuscript source/PDFs | `paper/aaai/` |
| current verified OpenReview bundle | `release/h001_aaai27_openreview_20260716_011716/` |

`summary_0713.md`, older release directories, and archived manuscript PDFs are
historical snapshots, not current-state owners.

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

1. `archive/hypothesis_records/hypothesis/README.md`
2. `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/01_overview.md`
3. `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/02_method.md`
4. `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/03_data_baseline.md`
5. `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/04_results.md`
6. `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/05_audit.md`
7. `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/06_second_source.md`
8. `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/07_experiment_spec.md`

H001 Docker experiment and result state:

1. `experiments/H001_geom_reliability/README.md`
2. `results/h001_geom_reliability/report.md`
3. `experiments/H001_geom_reliability/commands.md`
4. `results/h001_geom_reliability/manifest.lock.json`
5. `configs/h001/compose.structured.yaml`
6. `experiments/H001_geom_reliability/relation_algebra_v1/`
7. `experiments/H001_geom_reliability/structured_main_v1/`
8. `configs/h001/compose.yaml` (historical recovery and optional services)
9. `results/h001_geom_reliability/tables/`
10. `results/h001_geom_reliability/figures/figure_specs.md`
11. `results/h001_geom_reliability/bootstrap_ci/summary.md`
12. `experiments/H001_geom_reliability/factor_isolation_protocol/frozen_v1/`
13. `experiments/H001_geom_reliability/sources/3dssg_full_l160/`
14. `experiments/H001_geom_reliability/train_only_reestablishment_v1/`
15. `experiments/H001_geom_reliability/nonlinear_transfer_v1/`

The factor-isolation freeze requires the three source prediction/verification
JSONL pairs from the full result bundle, not raw datasets or model inference.
With those row-level artifacts present, reproduce the protocol and bit-exact
existing-score audit with:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm factor_isolation_protocol_freeze
```

Expected status is
`frozen_ready_for_post_hoc_mechanism_implementation`, validation errors `0`,
and `59/59` passing gates. This command does not fit the new factor models or
produce factor-performance metrics.

The completed train-only model freeze and fresh official-source evaluation are
reproduced in this order:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm factor_isolation_model_fit
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm 3dssg_confirmatory_target_freeze
wget -c https://www.campar.in.tum.de/public_datasets/2023_cvpr_wusc/trained_models/3DSSG_full_l160.zip -O local_dataset/SceneGraphFusion_checkpoints/3DSSG_full_l160.zip
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm 3dssg_checkpoint_stage
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm 3dssg_inference_smoke
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm 3dssg_inference
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm 3dssg_adapter_export
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm 3dssg_adapter_coverage_audit
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm 3dssg_geometry_join
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm 3dssg_confirmatory_metrics
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm 3dssg_confirmatory_audit
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm factor_isolation_metrics_3dssg
```

The stricter 1,061/117/157 reestablishment is a separate, later route. Its
frozen Docker order is:

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

Expected final statuses are
`strict_train_only_models_ready_pre_internal_dev_source_metrics`,
`execution_contract_frozen_pre_internal_dev_source_inference`,
`internal_dev_evaluation_ready`,
`final_method_locked_after_internal_dev_accept`, and
`final_validation_evaluation_ready`. The final evaluation can be regenerated
from the preserved 3DSSG geometry JSONL even when the redundant final adapter
prediction JSONL is absent, because each verification row preserves prediction
identity, semantic score, endpoint, predicate, and geometry features.

`3DSSG_full_l160.zip` SHA-256 is
`0adc59922ca700e131136dc9b055eb30c2e209da35c61c6dd00e478f98dd2da6`;
the extracted `model_best.pt` SHA-256 is
`5322bb0738b20312baba9cb0622d82368c3e5fa355fe726808f3470f4465ccf8`.
Preserve the raw/adapter/geometry JSONL files for exact reruns; the geometry
JSONL is large and is not a GitHub artifact.

Open3DSG source-specific state:

1. `experiments/H001_geom_reliability/sources/open3dsg/README.md`
2. `experiments/H001_geom_reliability/sources/open3dsg/commands.open3dsg.md`
3. `configs/open3dsg/compose.open3dsg.yaml`
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

Qwen-VL extension state:

1. `experiments/H001_geom_reliability/sources/qwen_vl/README.md`
2. `experiments/H001_geom_reliability/sources/qwen_vl/report.md`
3. `experiments/H001_geom_reliability/sources/qwen_vl/status.json`
4. `configs/qwen_vl/compose.qwen.yaml`
5. `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/input/`
6. `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/runtime/`
7. `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/validation/`
8. `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/adapter/`
9. `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/geometry/`
10. `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/failure_rows/`
11. `experiments/H001_geom_reliability/sources/qwen_vl/full_validation/failure_cases/`

Attachment subtype-v2 development state:

1. `archive/experiments/H001_geom_reliability/sources/attachment_deferred/README.md`
2. `archive/experiments/H001_geom_reliability/sources/attachment_deferred/subtype_redesign_v2/`
3. `subtype_redesign_v2/taxonomy.json`
4. `subtype_redesign_v2/control_contract.json`
5. `subtype_redesign_v2/legacy_audit.json`
6. `subtype_redesign_v2/mechanism_review_queue.csv`
7. `subtype_redesign_v2/development_diagnostic_v1/`
8. `subtype_redesign_v2/development_diagnostic_v2/`

Reproduce the design and both retrospective diagnostics with:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm attachment_subtype_redesign_v2
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm attachment_subtype_v2_development_diagnostic
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm attachment_subtype_v2_bounded_diagnostic
```

Expected validation errors are 0. These commands read the preserved
`full_validation_g5d/shards/*/{source_rows,evidence_rows}.jsonl` files. Deleting
those ignored row-level files blocks exact v2 source-diagnostic regeneration,
although compact metrics and manifests remain readable. Neither diagnostic is
paper-result or main-claim evidence.

Fresh SGFN confirmatory state:

1. `experiments/H001_geom_reliability/confirmatory_evaluation/sgfn_target_v1/`
2. `experiments/H001_geom_reliability/confirmatory_evaluation/sgfn_target_v2/`
3. `experiments/H001_geom_reliability/confirmatory_evaluation/sgfn_target_v2/checkpoint_audit.json`
4. `experiments/H001_geom_reliability/confirmatory_evaluation/sgfn_target_v3/`
5. `experiments/H001_geom_reliability/sources/sgfn/README.md`
6. `local_dataset/SceneGraphFusion_code/3DSSG/` at commit `4b783ecdc6caba1515b361f8a0643d0c2d568f52`
7. `local_dataset/SceneGraphFusion_checkpoints/SGFN_full_l20.zip` (downloaded
   audit failure; do not use for full_l160 inference)
8. `local_dataset/SceneGraphFusion_checkpoints/SGFN_full_l160.zip` (v3 locked,
   downloaded, checksum and 160/26 tensor audit passed)
9. `experiments/H001_geom_reliability/sources/sgfn/raw/manifest.json`
10. `experiments/H001_geom_reliability/sources/sgfn/adapter/coverage_audit.json`
11. `experiments/H001_geom_reliability/sources/sgfn/geometry/manifest.json`
12. `experiments/H001_geom_reliability/sources/sgfn/confirmatory_metrics/decision.json`

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
10. `archive/paper/aaai_snapshots/inspection_20260625/report.md`

If any listed runtime result file is missing, do not infer that the experiment
was never run. First check the artifact bundle section below and then verify
whether the file is in an external bundle, ignored runtime root, or regenerated
cache. Inspect large logs or JSONL files only through counts, `head`, `tail`,
targeted `rg`, or checksums.

## Current Status

Facts:

- Active experiment root: `experiments/H001_geom_reliability/`.
- Paper-body experiment outputs must be generated through Docker.
- Full-validation source artifacts, the primary family-slot route,
  supervision-matched nonlinear comparison, Open3DSG 533/548 sensitivity,
  deterministic qualitative inspection, routed public/full ablations, and
  K=50/100 scan-cluster intervals are ready
  for the selected paper-facing H001 route.
- Paper handoff and planning are ready: `paper/README.md`, `paper/preview.md`,
  `paper/progress.md`, `paper/appendix.md`, `paper/outline.md`,
  `paper/draft.md`, `paper/risk.md`, `paper/aaai/`, `archive/paper/iccv/`,
  `paper/figures.md`, and
  `paper/generated/figures/` contain the paper workspace map, current claim
  boundary, appendix/provenance table, paper skeleton, first-pass prose,
  reviewer-risk register, venue-specific LaTeX sources, figure locks, and
  reviewer-defense guardrails.
- Current target-year submission route uses the official `aaai2027` kit and a
  standalone reproducibility-checklist upload. Verified Docker outputs are
  `paper/aaai/main_aaai27.pdf` (9 pages; technical content through page 7,
  references on pages 8--9), `paper/aaai/supplement_aaai27.pdf` (5 pages),
  and `paper/aaai/reproducibility_checklist_aaai27.pdf` (2 pages). Build image:
  `h001-aaai27-tex:20260712`; final main log:
  `logs/h001_main_counterfactual_20260716_010956.log`; final supplement log:
  `logs/h001_supp_counterfactual_20260716_011157.log`. Main/supplement
  SHA256 values are
  `4b6be0f799bc20f551e6801394c040051dab9d2374110ad3a276f5b4ac805a17` and
  `865ae2ded7eb03b27f61b23078017e533dce11031c647941d5ffe67c8b476457`.
  The manuscript keeps
  Open3DSG as the main open-vocabulary case study and VL-SAT as the controlled
  reproduced anchor.

Human-alignment annotation and evaluation route:

- guide: `experiments/H001_geom_reliability/physical_validity_audit/frozen_v1/annotation_guide.md`
- first passes: `frozen_v1/annotator_a.csv`, `frozen_v1/annotator_b.csv`
- adjudication destination: `frozen_v1/adjudication.csv`
- validator output: `physical_validity_audit/human_alignment_validation_v1/`
- Human V/calibration output: `physical_validity_audit/evaluation_v1/`
- Codex--human output: `physical_validity_audit/codex_human_alignment_v1/`
- Docker order after first-pass lock: `human_alignment_validate`; after the
  generated mandatory queue is adjudicated, rerun that service, then run
  `physical_validity_audit_evaluate` and `codex_human_alignment_evaluate`.

The validator's mandatory set is the union of A/B disagreements, either
low-confidence decision, and either ambiguous/unobservable label. The two
first-pass reviewer IDs and the third adjudicator ID must be distinct non-proxy
pseudonyms with ISO-8601 timestamps. Do not expose `private_sidecar.jsonl`,
Codex labels, source scores/ranks, verifier results, GT, or result tables to
first-pass annotators.
- Current scoring convention: the applicability-routed relation-algebra
  product is the RelCompat3D primary ranking rule; `structured_rank_average`
  is its scale-robust
  instantiation, `structured_rrf_c60` is the strong rank-fusion comparator,
  `pooled_product` is the family-conditioning ablation, `hard_rule_filter` is
  the zero-violation diagnostic, and `structured_compatibility_only` removes
  source confidence but is not true geometry-only.
- Main-table conditions are Source score, the relation-algebra-constrained
  product, rank-average, RRF, and pooled product. Hard filtering remains a
  diagnostic artifact. The paper-facing `structured_ablation_v1/` route fixes
  the model, public/full 548 target, and family-slot routing while reporting
  wrong-predicate, wrong-pair, shuffled-geometry, label-fixed endpoint-swap,
  distance-only, and compatibility-only rankings at K=50/100. The earlier
  unrestricted/recovered route remains a supplemental mechanism audit.
- Qwen-VL is a third semantic source / modern VLM extension path. Full official
  validation downstream is complete: parser validation, adapter export,
  geometry join, metrics/controls, bootstrap CI, 31,881 failure rows, and 36
  deterministic qualitative cases are ready for 157 scans / 548 contexts /
  110,424 query rows / 46,506 inferable input rows / 35,131 exported
  predictions / 32,236 in-scope predictions / 3,972 H001-family GT rows. Treat
  Qwen as appendix/extension evidence unless explicitly promoted.
- Low-K reporting has been accepted for K = `{5,10,20,50,100}` in the main
  source-result table; K=1 remains sanity-check only. Docker-regenerated
  point-metric artifacts are available under
  `experiments/H001_geom_reliability/sources/vlsat/full_validation/metrics_k_sweep/`
  and
  `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics_k_sweep/`.
  K=50/100 values match each source's locked `metrics/metrics.json`; low-K
  bootstrap CI is not claimed unless separately regenerated.
- Runtime pressure is volatile: check `docker ps`, `tmux ls`, `nvidia-smi`, and
  `free -h` before launching heavy Open3DSG or Qwen jobs. The historical
  2026-05-26 Qwen-VL runtime-preflight retry was blocked by GPU guard, but the
  later 2026-05-27 runtime preflight, tiny inference smoke, crop preflight, and
  shard 0000 inference contract validation passed.
- SGFN target v3 was explicitly authorized and frozen before correct-checkpoint
  download. Target v2 records the earlier pre-inference split identity
  correction: the 548 H001 contexts use 157 scans
  exactly equal to official SGFN `files/cvpr/test_scans.txt`; the official
  117-scan validation list has zero overlap. The completed background download
  is `local_dataset/SceneGraphFusion_checkpoints/SGFN_full_l20.zip`, size
  `84,830,654`, SHA-256
  `9831357f4a04d996be48f7a9e3184525c33eab3712a08d7a98b4f984e85789b2`;
  log/exit are `logs/h001_sgfn_ckpt_20260710_155321.log` and
  `logs/h001_sgfn_ckpt_20260710_155321.exit` (`0`). Docker audit found object
  and relation heads `[20,256]` and `[8,256]`, so it is incompatible with the
  frozen full_l160 `[160,256]`/`[26,256]` contract. The official README exposes
  a separate `SGFN_full_l160.zip`. Target v3 downloaded it through background
  job `h001_sgfn_l160_ckpt`; log/exit are
  `logs/h001_sgfn_l160_ckpt_20260710_161227.log` and
  `logs/h001_sgfn_l160_ckpt_20260710_161227.exit` (`0`). Size is `86,777,444`,
  SHA-256 is
  `8e5af8f42cca5920d1b571b815f980e8884d931138462c30b5c8a70d9f747fa9`,
  and Docker audit confirms full_l160 object/relation heads `[160,256]` and
  `[26,256]`. Official test preprocessing is ready for 157 scans / 4,480 nodes
  / 27,712 relationship rows. One-scan inference smoke passes. Full inference
  completed with exit 0 under tmux `h001_sgfn_inference`; log
  `logs/h001_sgfn_inference_20260710_163351.log`, exit file
  `logs/h001_sgfn_inference_20260710_163351.exit`, output
  `experiments/H001_geom_reliability/sources/sgfn/raw/`. It produced 157 scans,
  4,480 nodes, 160,526 directed edges, and 4,173,676 relation scores. Adapter
  and geometry outputs preserve 957,008 rows each. Coverage is 548/548
  contexts and 36,808/36,808 nonself directed pairs; 11 self-`supported by` GT
  rows remain in the frozen 3,972-row denominator without synthesized edges.
  The 1,000-resample confirmatory audit status is
  `confirmatory_primary_gate_passed`; see
  `experiments/H001_geom_reliability/sources/sgfn/confirmatory_metrics/decision.json`
  for exact CIs and the verifier-V, family-wise, and rank-average boundaries.

## Reproduction Tiers And Dataset-Absent Path

Use this decision tree on a new computer before running any expensive job.

| Starting state | What is reproducible | Required action |
| --- | --- | --- |
| Git clone only, no `local_dataset/`, no external result bundle | Source/config sanity, paper source, compact tracked result summaries under `results/` | Do not claim regenerated metrics. Verify compose files and inspect tracked reports/tables only. |
| Git clone plus full-validation paper result bundle | Current paper-facing tables, metric summaries, row-count/checksum verification, and Table 6/report regeneration | Extract the bundle from the repo root, verify checksums/row counts, then run `table_builder` and optional bootstrap checks. Raw datasets are not required for this tier. |
| Git clone plus raw datasets/checkpoints/model caches | Full rerun from source data, including staging, raw dumps, adapter export, geometry join, metrics, controls, bootstrap, and failure rows | Follow the dataset/checkpoint staging sections below. This is GPU- and storage-heavy. |

Fresh clone sanity checks that do not require datasets:

```bash
docker compose -f configs/h001/compose.yaml config --quiet
docker compose -f configs/open3dsg/compose.open3dsg.yaml config --quiet
docker compose -f configs/qwen_vl/compose.qwen.yaml config --quiet
python -m py_compile $(rg --files src/geocalib -g '*.py')
```

If only the Git repo is available, `results/h001_geom_reliability/` is the
compact paper-facing snapshot. It is enough for reading, review, and source
sanity checks, but it is not a replacement for row-level artifacts. Do not run
`table_builder`, metric reruns, Open3DSG raw dump, or Qwen inference expecting
paper-equivalent outputs unless either the external result bundle or the
required datasets/checkpoints are present.

If the full-validation result bundle is available but raw datasets are not:

```bash
mkdir -p release logs
sha256sum -c release/h001_full_validation_results_<ts>.sha256
tar --zstd -xf release/h001_full_validation_results_<ts>.tar.zst -C /home/yoohyun/research
bash results/h001_geom_reliability/full_validation_transition/artifact_bundle/verify_upload_bundle.sh
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm table_builder'
```

This bundle tier can regenerate compact tables/reports from row-level
prediction, verification, metric, bootstrap, and failure artifacts. It still
cannot reproduce VL-SAT/Open3DSG raw inference, Open3DSG feature generation, or
Qwen-VL inference without the original datasets/model caches.

If neither datasets nor result bundle are available, first create the ignored
local roots and then acquire dependencies from the original providers or a
verified private transfer:

```bash
mkdir -p \
  local_dataset/3RScan/scans \
  local_dataset/3DSSG \
  local_dataset/3DSSG_subset \
  local_dataset/VLSAT_code \
  local_dataset/VLSAT_staged \
  local_dataset/Open3DSG_staged \
  local_dataset/model_cache \
  release logs
```

Minimum raw-data dependency order:

1. 3RScan scans and 3DSSG/3DSSG_subset relationship files under
   `local_dataset/3RScan/`, `local_dataset/3DSSG/`, and
   `local_dataset/3DSSG_subset/`.
2. VL-SAT source/data/checkpoints under `local_dataset/VLSAT_code/` and
   `local_dataset/VLSAT_staged/`.
3. Open3DSG source/runtime staging under `local_dataset/Open3DSG_staged/`,
   including component checkpoints and model caches checked by
   `cache_preflight`.
4. Optional Qwen-VL model cache and crop roots if reproducing the appendix
   third-source extension.

Lightweight readiness checks before launching a full rerun:

```bash
test -d local_dataset/3RScan/scans
test -f local_dataset/3DSSG_subset/relationships_validation.json
test -f local_dataset/3DSSG_subset/classes.txt
test -f local_dataset/3DSSG_subset/relationships.txt
test -d local_dataset/VLSAT_code/CVPR2023-VLSAT
test -d local_dataset/VLSAT_staged/h001_full_validation/CVPR2023-VLSAT
test -d local_dataset/Open3DSG_staged/training_repro
```

After these checks, use the Docker staging, feature-regeneration, checkpoint,
and experiment commands below. If any check fails, stop and restore/download
that dependency first; missing data should be treated as a setup blocker, not
as an experimental result.

## Data Locations

Large runtime data is intentionally under ignored local roots:

| Purpose | Path |
| --- | --- |
| Raw 3RScan payload | `local_dataset/3RScan/scans/` |
| 3DSSG raw/metadata payload | `local_dataset/3DSSG/` |
| 3DSSG subset files | `local_dataset/3DSSG_subset/` |
| VL-SAT source/runtime checkout | `local_dataset/VLSAT_code/CVPR2023-VLSAT/` |
| VL-SAT full-validation staged root | `local_dataset/VLSAT_staged/h001_full_validation/CVPR2023-VLSAT/` |
| Open3DSG training root | `local_dataset/Open3DSG_staged/training_repro/` |
| Open3DSG historical H001 eval root | `local_dataset/Open3DSG_staged/h001_runtime/` (deleted locally 2026-07-12; regenerate only for the 127-scan sensitivity route) |
| Open3DSG full-validation runtime root | `local_dataset/Open3DSG_staged/h001_full_validation_runtime/` |
| Open3DSG paper-facing checkpoint | `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt` |
| Open3DSG historical avg-BLIP checkpoint | `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt` |
| Open3DSG train/dev features | `local_dataset/Open3DSG_staged/training_repro/output/features/clip_features_h001_official_blip_top5_scales3/` |
| Open3DSG historical H001 eval features | `local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3/` (deleted locally 2026-07-12) |
| Open3DSG full-validation recovery features | `local_dataset/Open3DSG_staged/h001_full_validation_runtime/output/features/clip_features_h001_full_validation_recovery_relaxed_views_min2/` |
| Qwen-VL model cache | `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17/` (deleted locally 2026-07-12) |
| Qwen-VL tiny crops | `local_dataset/qwen_vl_crops/tiny_pilot/` (deleted locally 2026-07-12) |
| Qwen-VL full-source crops | `local_dataset/qwen_vl_crops/full_source/` (deleted locally 2026-07-12) |

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
archive/paper/iccv/
paper/figures.md
paper/generated/figures/
```

Hypothesis-stage smoke artifacts may exist under ignored `artifacts/` or
`**/evaluation/` paths. They are not the preferred cross-machine source of
truth; use the tracked reports, manifests, Docker commands, and locked tables
under `results/h001_geom_reliability/`, `configs/`, and
`experiments/H001_geom_reliability/`.

## GitHub Portability And `.gitignore` Audit

Checked on 2026-05-21 KST with `git check-ignore` and `git ls-files`.

Can be committed to GitHub:

- Root workflow docs: `README.md`, `TODO.md`, `AGENTS.md`, `summary.md`.
- Reproducibility docs: `docs/reproducibility.md`, `docs/index.md`,
  `docs/paper.md`, `docs/hypothesis.md`, `docs/literature.md`.
- Paper planning/source docs: `paper/README.md`, `paper/preview.md`, `paper/progress.md`,
  `paper/appendix.md`, `paper/outline.md`, `paper/draft.md`, `paper/risk.md`, `paper/aaai/`, `archive/paper/iccv/`, `paper/figures.md`, and
  compact figure metadata under `paper/generated/figures/`.
- Docker/reproduction source files:
  `configs/h001/Dockerfile`,
  `configs/h001/compose.yaml`,
  `experiments/H001_geom_reliability/commands.md`,
  `configs/open3dsg/`, `configs/qwen_vl/`, shell wrappers under `scripts/`,
  and executable Python under `src/geocalib/`.
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
- Ignored runtime roots such as `artifacts/`, `**/artifacts/`,
  `**/evaluation/`, `logs/`, and large row-level JSONL outputs.

Implication for another computer:

- The GitHub repo can carry the exact commands, Docker setup, paper/research
  state, compact manifests, and metric summaries.
- A GitHub-only checkout can validate code/configuration and inspect compact
  paper-facing summaries, but it cannot regenerate row-level metrics or raw
  inference artifacts without either the external result bundle or the original
  datasets/checkpoints.
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
compose files, runbooks, compact manifests, compact result tables/reports, and
metric summaries. Large
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
| A. GitHub tracked source | `README.md`, `TODO.md`, `summary.md`, `AGENTS.md`, `docs/`, `src/`, `scripts/`, `configs/`, `experiments/H001_geom_reliability/commands.md`, `results/h001_geom_reliability/`, `paper/aaai/`, and folder READMEs | Rebuild commands, compact results, and paper source | small | Commit to GitHub. |
| B. Full-validation paper result bundle | selected official non-avg Open3DSG checkpoint, full-validation VL-SAT row JSONL/metrics/bootstrap/failure artifacts, Open3DSG unmodified-source sensitivity row JSONL/metrics/bootstrap/failure artifacts, Open3DSG recovery row JSONL/metrics/bootstrap/failure artifacts, table outputs, manifest locks, checksum manifest | Reproduce current paper-facing full-validation tables and the Open3DSG recovery/unmodified-source caveat without rerunning multi-day feature/training jobs | fixed payload list: 211 files; row JSONL counts: VL-SAT predictions 957,008, verification 957,008, failure rows 59,841; Open3DSG unmodified predictions 690,924, verification 690,924, failure rows 81,448; Open3DSG recovery raw 26,938, predictions 695,916, verification 695,916, failure rows 82,155 | Good candidate for Google Drive, Zenodo, or Hugging Face Dataset. |
| C. Large feature-cache transfer bundle | Open3DSG train/dev features and H001 eval features | Fast full rerun without regenerating features | train/dev 131 GB; eval 13 GB | Optional; high storage cost but saves multi-day regeneration. |
| D. External-only dependencies | raw 3RScan/3DSSG/VL-SAT data, official third-party checkpoints, Qwen-VL HF cache | Dataset/model access under original terms | Qwen cache 8.3 GB; raw datasets much larger | Prefer documented download/rebuild over redistribution. |

Full-validation paper result upload bundle, fixed 2026-06-11 KST:

2026-06-14 status note: this file-list/checksum plan remains useful
provenance, but any final public upload package must be regenerated or
reverified after the RelCompat3D/Figure-1 update, the low-K table decision, and any
Qwen extension inclusion decision. Do not treat an older flattened archive as
final submission-ready without this pass.

Historical compact handoff package, 2026-07-12 KST:

```text
directory: release/h001_aaai27_submission_20260712_005127/
archive: release/h001_aaai27_submission_20260712_005127.tar.zst
archive sha256: e0543f392ac40b7bc518900b61f691563cb97bd0ba010bc009425bbabae9de8e
archive size: approximately 3.3 MB
package files: 499 including MANIFEST.sha256
verification logs: logs/h001_release_manifest_verify_20260712.log; logs/h001_release_archive_verify_20260712.log
```

This package contains self-contained main/supplement source and PDFs, compact
SGFN/factor/train-only/Codex/Replica/Open3DSG evidence, code, configs, and
runbooks. It intentionally excludes large datasets, checkpoint binaries,
feature caches, row-level predictions, and external Docker images. The copied
paper source was rebuilt independently in Docker before archive creation.

Current AAAI-27 OpenReview field bundle, verified 2026-07-16 KST:

```text
root: release/h001_aaai27_openreview_20260716_011716/
paper: main.pdf (1,196,168 bytes; SHA256 4b6be0f799bc20f551e6801394c040051dab9d2374110ad3a276f5b4ac805a17)
checklist: reproducibility_checklist.pdf (99,012 bytes; SHA256 4f7b254f2ee62291249f7a68e8d30fe34ea6976df91f235686a4e7740448e7fc)
technical supplement: technical_supplement.pdf (217,528 bytes; SHA256 865ae2ded7eb03b27f61b23078017e533dce11031c647941d5ffe67c8b476457)
code/data: code_and_data_supplement.zip (3,272,332 bytes; SHA256 734111cab9c21b7c8f5a5eee51f8f1b704b32967ed9cd60a3e5a7ba8d2b3315e)
upload manifest: UPLOAD_MANIFEST.sha256
```

The ZIP passed archive integrity, its 205-record internal `MANIFEST.sha256`, and
targeted author-identity/path scans. It contains no `.git` directory, external
Docker image, Codex proxy result, ReplicaSSG/FROSS development branch or
row-level payload, or Qwen-VL extension payload.
`README.md` maps files to the live OpenReview fields;
`submission_metadata.md` records topics, remaining author fields, claim scope,
and reporting notes. Do not upload the historical compact tarball or older
field bundles in place of these files.

The extracted source rebuild is recorded in
`logs/h001_release_{main,supp,check}_rebuild_20260716_011813.log`; inner-manifest
verification is `logs/h001_release_inner_manifest_20260716_011716.log`, archive
verification is `logs/h001_release_archive_20260716_011716.log`, and the
anonymous path/identity scan is
`logs/h001_release_identity_scan_20260716_011716.log`.
The extracted main,
supplement, and checklist reproduce the canonical page counts and text exactly;
binary PDF hashes differ only because TeX embeds build-time metadata. No
dataset, checkpoint, or Docker image was modified.

```text
status: upload_bundle_file_list_and_verification_fixed_no_archive_created
manifest: results/h001_geom_reliability/full_validation_transition/artifact_bundle/manifest.json
commands: results/h001_geom_reliability/full_validation_transition/artifact_bundle/commands.md
report: results/h001_geom_reliability/full_validation_transition/artifact_bundle/report.md
payload file list: results/h001_geom_reliability/full_validation_transition/artifact_bundle/upload_payload_files.txt
payload per-file checksums: results/h001_geom_reliability/full_validation_transition/artifact_bundle/upload_payload_sha256s.txt
payload row counts: results/h001_geom_reliability/full_validation_transition/artifact_bundle/upload_payload_row_counts.txt
verification script: results/h001_geom_reliability/full_validation_transition/artifact_bundle/verify_upload_bundle.sh
payload files: 211
payload checksum records: 211
payload file-list sha256: 392aa550557f64603a4548a9e494248d22eed899ecea3fefbc558451b39b716b
payload checksum-manifest sha256: 923bfde4e39921f5dd3fc10f0ec1a98eea606b50b83d4495d0d5b3afd1e4ff2b
payload row-count-file sha256: 2e86fe118260300bae6379f763f39f0cda0e4b07dd38455878de5d832d121943
checksum generation log: logs/h001_fullval_upload_checksums_20260611_002243.log
checksum generation exit: logs/h001_fullval_upload_checksums_20260611_002243.exit (0)
verification log: logs/h001_fullval_upload_verify_20260611_002319.log
verification exit: logs/h001_fullval_upload_verify_20260611_002319.exit (0)
```

Fixed payload roots:

```text
local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt
results/h001_geom_reliability/full_validation_transition/scope_contract/
results/h001_geom_reliability/manifest.lock.json
results/h001_geom_reliability/report.md
results/h001_geom_reliability/tables/
experiments/H001_geom_reliability/sources/vlsat/full_validation/
experiments/H001_geom_reliability/sources/open3dsg/full_validation/
experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection/
```

Key row counts for the fixed upload bundle:

```text
VL-SAT raw/raw.jsonl: 548
VL-SAT adapter/predictions.jsonl: 957,008
VL-SAT adapter/ground_truth.jsonl: 11,254
VL-SAT geometry/verification.jsonl: 957,008
VL-SAT gt_eval/gt_positive.jsonl: 3,972
VL-SAT gt_eval/counterfactuals.jsonl: 3,972
VL-SAT failure_rows/rows.jsonl: 59,841
VL-SAT failure_cases/queue.jsonl: 36
Open3DSG unmodified raw_dump/raw.jsonl: 26,746
Open3DSG unmodified adapter/predictions.jsonl: 690,924
Open3DSG unmodified geometry/verification.jsonl: 690,924
Open3DSG unmodified failure_rows/rows.jsonl: 81,448
Open3DSG recovery raw_dump/raw.jsonl: 26,938
Open3DSG recovery adapter/predictions.jsonl: 695,916
Open3DSG recovery geometry/verification.jsonl: 695,916
Open3DSG recovery failure_rows/rows.jsonl: 82,155
Open3DSG recovery failure_cases/queue.jsonl: 36
```

Full-validation upload archive creation template:

```bash
mkdir -p release logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_fullval_upload_archive_${ts} \
  "cd /home/yoohyun/research && tar --zstd -cf release/h001_full_validation_results_${ts}.tar.zst -T results/h001_geom_reliability/full_validation_transition/artifact_bundle/upload_payload_files.txt results/h001_geom_reliability/full_validation_transition/artifact_bundle > logs/h001_fullval_upload_archive_${ts}.log 2>&1 && sha256sum release/h001_full_validation_results_${ts}.tar.zst > release/h001_full_validation_results_${ts}.sha256; rc=\$?; printf '%s\n' \"\$rc\" > logs/h001_fullval_upload_archive_${ts}.exit; exit \"\$rc\""
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
exact command: tar --zstd -cf release/h001_core_results_20260526_160957.tar.zst local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt results/h001_geom_reliability/manifest.lock.json results/h001_geom_reliability/report.md results/h001_geom_reliability/tables experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl experiments/H001_geom_reliability/sources/open3dsg/adapter/predictions.jsonl experiments/H001_geom_reliability/sources/open3dsg/geometry/verification.jsonl experiments/H001_geom_reliability/sources/open3dsg/metrics/metrics.json experiments/H001_geom_reliability/sources/open3dsg/failure_rows/rows.jsonl experiments/H001_geom_reliability/sources/open3dsg/failure_cases/queue.jsonl experiments/H001_geom_reliability/sources/open3dsg/*/manifest.json experiments/H001_geom_reliability/sources/open3dsg/*/report.md
verification: sha256sum -c release/h001_core_results_20260526_160957.sha256 && wc -l experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl experiments/H001_geom_reliability/sources/open3dsg/adapter/predictions.jsonl experiments/H001_geom_reliability/sources/open3dsg/geometry/verification.jsonl experiments/H001_geom_reliability/sources/open3dsg/failure_rows/rows.jsonl experiments/H001_geom_reliability/sources/open3dsg/failure_cases/queue.jsonl && jq -r '.status' experiments/H001_geom_reliability/sources/open3dsg/metrics/metrics.json
boundary: historical/sensitivity bundle only; current paper-facing bundle is the full-validation plan above. The local tar/checksum copy was deleted on 2026-06-05 after the full-validation route became the default handoff path.
```

Full-validation bundle verification after download/extract:

```bash
sha256sum -c release/h001_full_validation_results_<ts>.sha256
bash results/h001_geom_reliability/full_validation_transition/artifact_bundle/verify_upload_bundle.sh
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
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm feature_audit'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm feature_audit_h001_eval'
```

Do not put Qwen-VL model weights in the default core bundle. The Qwen path is
appendix/extension evidence and can be recreated from the fixed Hugging Face
model id, revision, and local-dir command above. If the goal is to reproduce or
audit the completed Qwen full-validation extension on another computer,
preserve or transfer these paths:

```text
local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17/
local_dataset/qwen_vl_crops/full_source/
experiments/H001_geom_reliability/sources/qwen_vl/full_validation/
experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/
experiments/H001_geom_reliability/sources/qwen_vl/full_source_inference_plan/
experiments/H001_geom_reliability/sources/qwen_vl/full_source_runtime/
experiments/H001_geom_reliability/sources/qwen_vl/status.json
experiments/H001_geom_reliability/sources/qwen_vl/README.md
experiments/H001_geom_reliability/sources/qwen_vl/report.md
configs/qwen_vl/compose.qwen.yaml
configs/qwen_vl/Dockerfile.qwen
src/geocalib/run_qwen_vl_full_source_inference.py
scripts/run_qwen_vl_full_source_shard_loop.sh
src/geocalib/plan_qwen_vl_full_source_inference.py
logs/qwen_vl_full_source_infer_remaining_20260527_023111.log
logs/qwen_vl_full_source_infer_remaining_20260527_023111.status.tsv
logs/qwen_vl_full_source_infer_remaining_20260527_023111.exit
```

The `full_source_*` paths and 2026-05-27 loop logs are historical 127-scan
route provenance. For the current paper package, prefer the
`full_validation/` artifacts and their row-count/checksum manifest if Qwen-VL
is included.

## Environment And Docker

### Current image retention audit

Audited 2026-07-14 KST against active compose files, image IDs, and all local
containers. None of the listed H001/H002 research images is attached to an
existing container. Container absence alone is not enough to decide retention;
the reproduction tier below controls the decision.

| Image | Active reference / role | Current disposition |
| --- | --- | --- |
| `h001-aaai-tex:20260526` | superseded AAAI-26 build | safe to remove |
| `h001-aaai27-tex:20260712` | canonical AAAI-27 paper build | keep |
| `h001-geom-reliability:latest` | `configs/h001/compose.structured.yaml` and main H001 services | keep |
| `h001-real-proposals:ovdet-v0` | no active repository reference; non-main prototype | safe to remove |
| `h001-fross-replicassg:cu121` | redundant tag for the same ID as `cu128-trt108` | safe to untag; zero layer-space gain by itself |
| `h001-fross-replicassg:cu128-trt108` | ReplicaSSG/FROSS transfer-development only | removable for paper/package preservation; required only to rerun the de-scoped diagnostic |
| `h001-replicassg-render:habitat022` | ReplicaSSG rendering only | removable under the same condition |
| `h001-sgfn-confirmatory:cu128` | SGFN/SGPN inference and the base of the FROSS runtime | keep for full main-source reproduction; conditionally removable only after accepting loss of immediate SGFN inference reruns or archiving the image |

The SGFN image is intentionally not in the immediate-cleanup set: active
`configs/h001/compose.yaml` services reference it, SGFN is a current main-table
source, and its tracked Dockerfile starts from `h001-open3dsg-repro:cu128`,
whose local tag is currently absent. Rebuilding after deletion is therefore
more expensive than rebuilding the lightweight metric or TeX images.

The H002 images are outside H001 cleanup ownership. Current H002 configs use
`h002-compatibility-routing:latest`, `h002-paper-assets:20260710`, and
`h002-aaai2027-tex:latest`; keep those for the active H002 route.
`h002-compatibility-routing-learned-ge-phase-a:latest` belongs to a discarded
learned-geometry phase that the current H002 compose intentionally excludes,
so it is removable if no separate H002 recovery is desired.

Before any future removal, recheck that no container started after this audit
uses the candidate image:

```bash
docker ps -a --format '{{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}'
docker image inspect <image> --format '{{join .RepoTags ","}} {{.Id}}'
```

Build the main H001 table/evaluation image:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml build'
```

Build and check the Open3DSG reproduction image:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml build'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm env_check'
```

Build and check the Qwen-VL runtime image/cache:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/qwen_vl/compose.qwen.yaml build'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/qwen_vl/compose.qwen.yaml run --rm qwen_vl_cache_verify'
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
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_payload --repo-root /workspace'
```

Run a small resumable download/extract pilot:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_payload --repo-root /workspace --download-missing --extract-sequence --limit 1 --workers 2'
```

Run a resumable batch:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_payload --repo-root /workspace --download-missing --extract-sequence --limit 20 --workers 4 --timeout 300 --retries 1'
```

For long batches, use `tmux` and timestamped logs under `logs/`. Example:

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_open3dsg_payload_batch \
  "cd /home/yoohyun/research && bash -lc 'set -o pipefail; sg docker -c '\''env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_payload --repo-root /workspace --download-missing --extract-sequence --limit 100 --workers 4 --timeout 300 --retries 1'\''; rc=\$?; printf \"%s\n\" \"\$rc\" > logs/open3dsg_payload_batch_${ts}.exit; exit \$rc' > logs/open3dsg_payload_batch_${ts}.log 2>&1"
```

Stage H001 held-out eval scan symlinks:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm h001_eval_payload'
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
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml build'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm env_check'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm cache_preflight'
```

Stage train/dev views and preprocessed-ready splits if starting from raw data:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_train_root'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_views_full'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_preprocess_full'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm train_preprocess_filter'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm validation_views_full'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm validation_preprocess_full'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm validation_preprocess_filter'
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
  "cd /home/yoohyun/research && bash -lc 'set -o pipefail; echo \"started_at=\$(date -Is)\"; echo \"cwd=\$(pwd)\"; nvidia-smi --query-gpu=timestamp,index,name,memory.total,memory.used,memory.free,utilization.gpu --format=csv,noheader,nounits || true; sg docker -c '\''env UID=\$(id -u) GID=\$(id -g) OPEN3DSG_DUMP_WORKERS=0 OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=2 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:128 docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm dump_features_3rscan'\''; rc=\$?; echo \"finished_at=\$(date -Is)\"; echo \"exit_code=\$rc\"; printf \"%s\n\" \"\$rc\" > logs/open3dsg_dump_features_regen_${ts}.exit; exit \$rc' > logs/open3dsg_dump_features_regen_${ts}.log 2>&1"
```

Verify train/dev feature completion:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm feature_audit'
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
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm h001_eval_payload'
```

Run the bounded shard loop. This is the preferred route because the full H001
eval feature dump had partial exit-137 failures before the shard loop was added.

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_open3dsg_dump_features_h001_eval_shard_loop \
  "cd /home/yoohyun/research && bash -lc 'set -o pipefail; python src/geocalib/run_open3dsg_h001_eval_feature_shards.py --repo-root /home/yoohyun/research --max-new-ids 5; rc=\$?; echo \"finished_at=\$(date -Is)\"; echo \"exit_code=\$rc\"; printf \"%s\n\" \"\$rc\" > logs/open3dsg_dump_features_h001_eval_shard_loop_${ts}.exit; exit \$rc' > logs/open3dsg_dump_features_h001_eval_shard_loop_${ts}.log 2>&1"
```

Verify H001 eval feature completion:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm feature_audit_h001_eval'
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
tmux new-session -d -s h001_qwen_vl_model_download "cd /home/yoohyun/research && bash -lc 'set -o pipefail; sg docker -c '\''env UID=$(id -u) GID=$(id -g) docker compose -f configs/qwen_vl/compose.qwen.yaml build qwen_vl_model_download && env UID=$(id -u) GID=$(id -g) docker compose -f configs/qwen_vl/compose.qwen.yaml run --rm qwen_vl_model_download && env UID=$(id -u) GID=$(id -g) docker compose -f configs/qwen_vl/compose.qwen.yaml run --rm qwen_vl_cache_verify'\''; rc=$?; printf \"%s\n\" \"$rc\" > logs/qwen_vl_model_download_20260512_082830.exit; exit $rc' > logs/qwen_vl_model_download_20260512_082830.log 2>&1"
```

## Experiment Reproduction Commands

Regenerate paper-facing H001 tables/report from locked artifacts:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm table_builder'
```

Recreate Open3DSG adapter, geometry join, metrics, and Table 6 from the
identity-audited raw dump:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl docker compose -f configs/h001/compose.yaml run --rm open3dsg_adapter_raw_dump'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_geometry_join'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_metric_eval'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm table_builder'
```

Regenerate Open3DSG failure-analysis rows and qualitative case queue:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_failure_generator_real'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_failure_case_sampler'
```

Qwen-VL runtime smoke and full-validation downstream evaluation are complete in
the current workspace. Use these commands only if rebuilding or verifying a new
computer:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/qwen_vl/compose.qwen.yaml run --rm qwen_vl_runtime_preflight'
sg docker -c 'env UID=$(id -u) GID=$(id -g) QWEN_VL_TINY_INFERENCE_LIMIT=3 docker compose -f configs/qwen_vl/compose.qwen.yaml run --rm qwen_vl_tiny_inference_smoke'
```

Do not resume the historical `qwen_full_source_shard_0014` loop for the current
paper package. That command belongs to the older 127-scan full-source route and
is superseded by the full official validation extension artifacts under
`experiments/H001_geom_reliability/sources/qwen_vl/full_validation/`. If Qwen
is included in a release artifact, verify the full-validation input, runtime,
validation, adapter, geometry, metrics/bootstrap, failure rows, and qualitative
case files rather than restarting the old loop.

Historical 127-scan averaged-BLIP source eval has clean provenance through the v14 streaming
same-path resume. The canonical raw dump remains `raw_dump/raw.jsonl`, and the
streaming resume output `raw_stream_retry_20260519_092628.jsonl` completed with
exit 0, manifest status `raw_dump_stream_complete`, 377/377 completed batches,
19,162 rows, dropped/invalid partial rows 0/0, and SHA256 matching the canonical
raw dump. Earlier exit-137 attempts are historical run records.

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt docker compose -f configs/open3dsg/compose.open3dsg.yaml run --rm eval_h001_gt_objects'
```

The command above is historical-only. The paper-facing full-validation route
must use the command and manifest under
`sources/open3dsg/full_validation/recovery_relaxed_views_min2/`, which lock run
`25da9c4c00214f3b880cedbb2a124177` and `avg_blip_emb=False`.

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
jq -r '.status' experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics/metrics.json
jq -r '.conditions | to_entries[] | select(.key=="semantic_only" or .key=="probabilistic_recalibrated" or .key=="rule_verified_point_subtype" or .key=="control_family_specific_p_geom_valid") | [.key, (.value.recall.by_k["50"].recall|tostring), (.value.recall.by_k["100"].recall|tostring), (.value.violation_rate.by_k["50"].violation_rate|tostring), (.value.violation_rate.by_k["100"].violation_rate|tostring)] | @tsv' experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics/metrics.json
```

In paper-facing prose and tables, interpret the legacy JSON key
`control_family_specific_p_geom_valid` as `family_conditional_risk`.

Check Qwen-VL cache:

```bash
cat logs/qwen_vl_model_download_20260512_082830.exit
find local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17 -maxdepth 2 -type f | wc -l
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/qwen_vl/compose.qwen.yaml run --rm qwen_vl_cache_verify'
```

## Artifact And Evaluation Summary

`VL-SAT` locked H001 result:

| Condition | R@50 | R@100 | Violation@50 | Violation@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.9599 | 0.9894 | 0.0247 | 0.0469 |
| `probabilistic_recalibrated` | 0.9642 | 0.9921 | 0.0234 | 0.0391 |
| `family_conditional_risk` | 0.9619 | 0.9914 | 0.0204 | 0.0310 |

`VL-SAT` full official validation rerun:

- artifact root:
  `experiments/H001_geom_reliability/sources/vlsat/full_validation/`
- low-K metric root:
  `experiments/H001_geom_reliability/sources/vlsat/full_validation/metrics_k_sweep/`
- command index: `experiments/H001_geom_reliability/commands.md`
- status: `vlsat_full_validation_metric_bundle_ready`
- scope: 157 scans, 548 contexts, 957,008 prediction rows, 11,254 GT rows,
  3,972 H001-family GT rows

| Condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.4194 | 0.6322 | 0.8074 | 0.9272 | 0.9635 | 0.0029 | 0.0082 | 0.0142 | 0.0268 | 0.0476 |
| `probabilistic_recalibrated` | 0.4154 | 0.6322 | 0.8107 | 0.9305 | 0.9688 | 0.0015 | 0.0071 | 0.0120 | 0.0229 | 0.0404 |
| `rule_verified_point_subtype` | 0.4197 | 0.6317 | 0.8074 | 0.9257 | 0.9627 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `family_conditional_risk` | 0.4162 | 0.6309 | 0.8087 | 0.9288 | 0.9683 | 0.0011 | 0.0051 | 0.0109 | 0.0206 | 0.0333 |

Additional `VL-SAT` verifier/audit evidence:

- Full-validation GT-positive rows: 3,972.
- Full-validation GT-derived negatives: 3,972.
- Full-validation `p_geom_valid` AUROC/AUPRC: 0.9772 / 0.9729.
- Historical reduced visual sanity check: 50/50 labels, reviewer `yhkim`,
  `ready_sanity_pass`.

Open3DSG full-validation recovery result:

- artifact root:
  `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/`
- low-K metric root:
  `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics_k_sweep/`

| Condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.0368 | 0.1002 | 0.1991 | 0.4096 | 0.5161 | 0.5131 | 0.3255 | 0.2088 | 0.1386 | 0.1242 |
| `probabilistic_recalibrated` | 0.0826 | 0.1581 | 0.2603 | 0.3975 | 0.5723 | 0.0628 | 0.0699 | 0.0654 | 0.0606 | 0.0811 |
| `rule_verified_point_subtype` | 0.0707 | 0.1314 | 0.2422 | 0.4295 | 0.5368 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `family_conditional_risk` | 0.0984 | 0.1921 | 0.3291 | 0.4658 | 0.6047 | 0.0420 | 0.0482 | 0.0441 | 0.0286 | 0.0341 |

Open3DSG historical 127-scan second-source result:

| Condition | R@50 | R@100 | Violation@50 | Violation@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.3945 | 0.4963 | 0.1326 | 0.1195 |
| `probabilistic_recalibrated` | 0.3843 | 0.5580 | 0.0575 | 0.0803 |
| `rule_verified_point_subtype` | 0.4149 | 0.5238 | 0.0000 | 0.0000 |
| `family_conditional_risk` | 0.4530 | 0.5984 | 0.0228 | 0.0311 |

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

## ReplicaSSG / FROSS Transfer-Development Runtime

The initial transfer run and the current development diagnostic use these
workspace roots:

```text
local_dataset/ReplicaSSG_download/
local_dataset/ReplicaSSG_runtime/
local_dataset/ReplicaSSG_code/
local_dataset/FROSS_code/
local_dataset/FROSS_weights/
local_dataset/model_cache/fross_home/
experiments/H001_geom_reliability/sources/replicassg/fross_raw/shards/
```

The large local source/runtime roots were restored once for development v2 and
deleted again after the 4,293-row adapter/geometry outputs, 355-condition sweep,
LOSO summary, and 548-context cross-source summary passed Docker validation.
Compact row-level development inputs and evaluation artifacts remain under
`sources/replicassg/development_v2/`; raw archives, meshes, rendered sequences,
weights, engines, and source shards are regeneration-only. A full source rerun
requires restoring the official ReplicaSSG archive, FROSS weights/code, and
engine/runtime dependencies first.

Current restoration and development entry points:

```bash
scripts/restore_replicassg_runtime.sh dataset
scripts/restore_replicassg_runtime.sh weight
scripts/run_replicassg_development_v2_pipeline.sh
```

The Docker evaluation service is `replicassg_development_v2`. It writes the
test-specific development estimate under
`experiments/H001_geom_reliability/sources/replicassg/development_v2/evaluation/`.
The denominator-corrected cross-source diagnostic is under
`development_v2/cross_source_evaluation/` and includes all 548 contexts,
including ten with zero in-scope GT but valid Violation contributions.

The current final-method transfer metric does not require regenerating meshes,
frames, weights, or TensorRT inference while the preserved 4,293-row
verification JSONL remains present. Its frozen Docker command is:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm external_dataset_transfer
```

Canonical contract and result:

- `experiments/H001_geom_reliability/sources/replicassg/final_method_transfer_v1/protocol.json`
- `experiments/H001_geom_reliability/sources/replicassg/final_method_transfer_v1/evaluation/`
- evaluator: `src/geocalib/run_external_dataset_transfer.py`
- log: `logs/h001_external_dataset_transfer_20260715_111730.log`

The protocol locks the current model hash, zero target fit/tuning, 11-scene
bootstrap, seven conditions, and the negative-transfer decomposition before
metric execution. All 20 validations pass. The official test target had been
observed in previous development, so this result is an external benchmark
evaluation rather than prospective confirmation.

The source runner is storage-streamed. Use the stdin-isolation shim so Docker
does not consume the scan loop input:

```bash
PATH="$PWD/scripts/no_stdin_bin:$PATH" env UID=$(id -u) GID=$(id -g) \
  bash scripts/run_replicassg_fross_streaming.sh
env UID=$(id -u) GID=$(id -g) docker compose -f configs/fross/compose.yaml run --rm replicassg_fross_adapter
env UID=$(id -u) GID=$(id -g) docker compose -f configs/fross/compose.yaml run --rm replicassg_geometry
env UID=$(id -u) GID=$(id -g) docker compose -f configs/fross/compose.yaml run --rm replicassg_evaluation
```

Verify the tracked compact result and upstream chain with:

```bash
sha256sum results/h001_geom_reliability/replicassg_prospective/{summary.json,summary.md}
jq '.validations | to_entries | map(select(.value != true))' \
  experiments/H001_geom_reliability/sources/replicassg/evaluation/summary.json
jq -e '.status == "completed_development_diagnostic"' \
  experiments/H001_geom_reliability/sources/replicassg/development_v2/evaluation/summary.json
jq -e '.status == "completed_benchmark_evaluation" and ([.validations[]] | all)' \
  experiments/H001_geom_reliability/sources/replicassg/development_v2/cross_source_evaluation/summary.json
```

Expected values are compact hashes
`35338ff18cb8eb507c6e644a8668dd032f93de24a440b4ef55e739ef396992fa`
and `f21e6ce56d91250eebc863e766914ba1ab7cce6de65da3a8e8e5f8326e4d24c5`,
zero failed validations in the preserved summary, and completed development-v2
and denominator-corrected cross-source summaries. The
`replicassg_prospective` directory name is a preserved historical identifier;
its current role is transfer/development evidence. The former 11 local shards
are no longer expected after cleanup. No external file or Docker image was
modified by the 2026-07-12 cleanup.

## Cleanup Candidates

Cleanup state, 2026-07-12 KST: the user-approved first-priority non-main cleanup
removed 270 workspace entries and reclaimed 71,784,480,768 bytes
(approximately 66.9 GiB). Deletions were restricted to
`/home/yoohyun/research`; no external file or Docker image was touched. Removed
classes were ReplicaSSG/FROSS runtime and row-level shards, Qwen model/crop and
large runtime payloads, attachment aggregate/shard scored rows, historical
VL-SAT and Open3DSG row-level duplicates, non-main 3DSSG/SGFN payloads, the
stale release package, and rendered paper-inspection PNGs. Compact manifests,
metrics, reports, protocol locks, main datasets, and both Open3DSG checkpoints
were preserved.

Paper-folder cleanup, 2026-07-12 KST: `paper/aaai/` now contains only active
AAAI-27 source, official templates, and the three canonical final PDFs.
Superseded review PDFs, the AAAI-26 style, the appended legacy checklist, and
historical inspection notes moved to `archive/paper/aaai_snapshots/`. All
top-level LaTeX build sidecars and byte-identical default-output PDF duplicates
were deleted. No dataset, experiment result, external file, or Docker image was
modified. A clean Docker rebuild passed text equality for all three outputs and
pixel equality for all main-paper pages; verification log:
`logs/h001_aaai27_post_cleanup_verify_20260712.log`.

Cleanup state, 2026-07-11 KST: disk-pressure cleanup was restricted to
duplicate, failed, historical row-level, or deterministically regenerable
artifacts inside `/home/yoohyun/research`. After the user clarified the scope,
no external file or Docker image was modified. The following workspace paths
were removed:

```text
local_dataset/3DSSG_staged/checkpoint_failed_audit_v1/
experiments/H001_geom_reliability/sources/3dssg_full_l160/inference_smoke_failed_audit_v1/
experiments/H001_geom_reliability/sources/3dssg_full_l160/inference_smoke/
experiments/H001_geom_reliability/sources/3dssg_full_l160/adapter/predictions.jsonl
experiments/H001_geom_reliability/sources/sgfn/adapter/predictions.jsonl
experiments/H001_geom_reliability/sources/open3dsg/geometry/verification.jsonl
experiments/H001_geom_reliability/sources/open3dsg/adapter/predictions.jsonl
experiments/H001_geom_reliability/sources/open3dsg/non_avg/geometry/verification.jsonl
experiments/H001_geom_reliability/sources/open3dsg/non_avg/adapter/predictions.jsonl
experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/geometry/verification.jsonl
experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/adapter/predictions.jsonl
experiments/H001_geom_reliability/sources/open3dsg/full_validation/geometry/verification.jsonl
experiments/H001_geom_reliability/sources/open3dsg/full_validation/adapter/predictions.jsonl
local_dataset/Open3DSG_staged/training_repro/output/datasets/OpenSG_3RScan/
release/h001_full_validation_results_20260611_025158.tar.zst
logs/open3dsg_train_full_avg_blip_20260515_172644.log
logs/open3dsg_train_full_nonavg_retry_20260601_071908.log
```

The failed/incomplete factor-metric artifact was also removed. Compact
manifests, metrics, reports, the selected Open3DSG checkpoint, the 131-GB
feature cache, raw 3RScan scans, and the authoritative 3DSSG final geometry
JSONL were preserved. Removing `OpenSG_3RScan/` only removes derived
preprocessing and requires deterministic regeneration before a new Open3DSG
source rerun; it does not invalidate existing compact results. The redundant
release archive was removed without deleting its manifest or source artifacts.

Pre-clarification exception: an aborted cleanup command had already removed the
local Docker image tags `h001-open3dsg-repro:cu128` and
`h001-aaai-tex:20260611`. No external source file or dataset was deleted, and
the images were not required by the train-only run completed here. They have
not been rebuilt or otherwise touched after the user restricted cleanup to the
workspace; rebuild from the tracked Dockerfiles only if a future rerun needs
them.

Cleanup state, 2026-06-06 KST: the user-approved paths below were deleted from
the local workspace. They were not required for the current paper-facing
full-validation claim. Do not delete primary full-validation artifacts, raw
datasets, selected checkpoints, feature caches needed for reruns, Qwen resume
files, `archive/experiments/H001_geom_reliability/sources/attachment_deferred/full_source_g5d/`, Open3DSG
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
archive/cache/experiments_scripts_pycache/
archive/cache/paper_scripts_pycache/
paper/scripts/__pycache__/
local_dataset/**/__pycache__/
```

Deleted superseded attachment/lateral intermediate artifacts:

```text
archive/experiments/H001_geom_reliability/sources/attachment_deferred/full_source_g5d_smoke/
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

## 2026-07-12 Reviewer-Strengthening Artifacts

Docker commands:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm nonlinear_fusion_baseline
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm codex_proxy_audit_evaluate
```

Outputs:

- nonlinear protocol and result:
  `experiments/H001_geom_reliability/nonlinear_fusion_baseline/protocol.json`
  and `nonlinear_fusion_baseline/evaluation_v1/`;
- Codex non-human proxy evaluation:
  `experiments/H001_geom_reliability/physical_validity_audit/codex_proxy_evaluation_v1/`;
- the then-current submission PDF from this historical stage has been
  superseded; use the canonical hashes in `Current Status` above;
- non-submission proxy manuscript: `paper/paper_nonsub/main_nonsub.pdf`,
  SHA256
  `52dc1c775ede032df45f345999f6421cadbb331856a5e4862c083c29f9ee7287`.

The non-submission manuscript and Codex output must not be copied into an
anonymous submission bundle or represented as Human V@K. The nonlinear
baseline is reviewer-requested retrospective evidence and must retain its
source-specific exact-label supervision disclosure.

## 2026-07-14 Completed Codex Proxy Reference And External Check

Docker commands:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm codex_proxy_adjudicate
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm codex_proxy_reference_evaluate
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm external_proxy_review_validate
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm reviewer_verified_proxy_evaluate
```

Authoritative outputs:

- blank proxy reference handoff:
  `experiments/H001_geom_reliability/physical_validity_audit/codex_proxy_reference_v1/`;
- completed A/B/C sheets:
  `physical_validity_audit/external_reviews_completed_v1/`;
- reference SHA256:
  `64351b480abf366383c73ff918be5f6f31dabe8b3e12447391f142adc7050b62`;
- design-weighted proxy/construct evaluation:
  `physical_validity_audit/codex_proxy_reference_evaluation_v1/`, summary
  SHA256 `dd3e1febd3355ae7658fe10d91f85c6079294949cebad1bd9dfaecf7f536e77a`;
- external-review validator state:
  `physical_validity_audit/external_proxy_review_validation_v1/`;
- portable review handoff:
  `release/h001_codex_proxy_external_review_v1/`.

The evidence archive contains exactly 488 orthographic projection PNGs and 488
colored pair PLYs. Its SHA256 is
`b5821c4ce1f4235a2d51e4b737208cce1aec5c78c78f19196b6319b52b73b3e3`.
Optional RGB crop paths recorded at protocol freeze are no longer locally
available after H001 cleanup, so the external sheets leave RGB paths empty;
this does not change the frozen sample or the 488/488 raw-3D coverage.

Reviewers A, B, and C confirmed all 488 completed labels without revision at
`2026-07-14T22:49:11+09:00`. The real validator reports
`ready_reviewer_verified_proxy_reference`, 488/488 resolved rows, three
distinct reviewer IDs, and zero errors. The validated reference is
`external_proxy_review_validation_v1/reviewer_verified_reference.csv`; its
evaluation is under `reviewer_verified_proxy_evaluation_v1/`. The result
remains reviewer-verified LLM annotation, not Human V@K. The rebuilt
non-submission PDF is
`paper/paper_nonsub/main_nonsub.pdf`, SHA256
`c7518a7a2eec73783a87f4d5733b0fcd495fee3e50c6e4d4f9850cf7548496b9`.

## 2026-07-13 Relative-Size Extension

Authoritative root:
`experiments/H001_geom_reliability/relative_size_v1/`.

The Docker execution order is:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm relative_size_freeze
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm relative_size_fit
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm relative_size_lock
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm relative_size_evaluate
```

The route uses the existing 1,061 train / 117 internal-dev / 157 official
final-validation firewall and evaluates all 548 contexts. Model fitting uses
train only; internal-dev supplies diagnostics and lock acceptance; final
validation supplies no model or score parameter. The learned compatibility
uses point-view A, while the verifier uses a disjoint point-view B and a
different percentile extent. Annotation OBB is a baseline only.

Locked identifiers:

- model SHA-256:
  `bfb6068307b9743a0f852a1082e4fa40c50ef15094601f930f1e431cbdade015`;
- score-definition SHA-256:
  `d63bd805b0866118f0bb0fb510913b68270e543fe1923ed9b67d47496e0fb0c7`;
- lock SHA-256:
  `473dd5b723dd90f47f44491b7e7d13ff96a3d3bc779153803a13df2aa36d8585`;
- evaluation `summary.json` SHA-256:
  `aa5a40c9ce6d07697c4101816925bd8819b296a9de4accc8f283fccb4c83238a`;
- evaluation `metrics.csv` SHA-256:
  `443def0ade74ab7495887bf656a1118de438414fb63ddfc21cb8daf5c99edc67`.

Primary outputs are `protocol.json`, `fit/model.json`, `lock.json`, and
`evaluation/{summary.json,metrics.csv,global_composition.csv,manifest.json}`.
The learned product passes the frozen within-size and global four-family K=100
gate for VL-SAT, Open3DSG, and SGFN. The fixed point rule is as strong or
stronger on Violation, so the artifact supports framework-scope expansion only.
Do not overwrite the locked root. The recorded promotion is bounded to one
main-text scope sentence and full supplement evidence; it does not authorize a
learned-formula, universal-fusion, or headline main-claim expansion.

## 2026-07-13/14 Novelty-Mechanism Development

Authoritative compact roots:

- `experiments/H001_geom_reliability/relation_algebra_v1/`
- `experiments/H001_geom_reliability/structured_main_v1/`
- `experiments/H001_geom_reliability/structured_ablation_v1/`
- `experiments/H001_geom_reliability/nonlinear_transfer_v1/`
- `experiments/H001_geom_reliability/support_contact_routing_v1/`
- `experiments/H001_geom_reliability/supervision_matched_nonlinear_v1/`
- `experiments/H001_geom_reliability/open3dsg_official_route_v1/`

Docker commands:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.structured.yaml run --rm relation_algebra_development
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.structured.yaml run --rm structured_main_evaluation
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.structured.yaml run --rm support_contact_routing
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.structured.yaml run --rm supervision_matched_nonlinear
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.structured.yaml run --rm open3dsg_official_route_sensitivity
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.structured.yaml run --rm support_routing_scan_cluster
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.structured.yaml run --rm routed_public_ablation_evaluation
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.structured.yaml run --rm counterfactual_threshold_sensitivity
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.structured.yaml run --rm structured_ablation_evaluation
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm nonlinear_transfer_vlsat
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm nonlinear_transfer_open3dsg
```

The relation-algebra protocol was frozen before execution and reports every
attempt. Its result root is `relation_algebra_v1/evaluation/`; verify the five
payload hashes against `evaluation/manifest.json`. The only passing candidate
is `orbit_pairwise_projected_product`.

The coordinated promotion route is `structured_main_v1/`. Its shared
compatibility model excludes predictor identity and source score and is locked by SHA256
`62d251f3ce60e2db54eb1748c277350e3b9e2c7c9d2be0312cf2fb323b761410`.
Verify `evaluation/manifest.json`: split disjointness, source exclusion, model
hash, row/context counts, all K/method rows, family-wise paired intervals, and
hard-filter zero-violation checks must all be `true`. The compact paper-facing
entry point is `configs/h001/compose.structured.yaml`; it avoids historical
source-preparation and optional-extension services.

The paper-facing primary route is layered on this locked model under
`support_contact_routing_v1/`. `family_slot_rerank` was selected on the
117-scan internal-development split, preserves source family composition and
support/contact selection exactly at every K, and is evaluated unchanged on
the official target. Its primary scan-cluster intervals use public Open3DSG
predictions on the full 548-context universe; context-bootstrap intervals are
retained as sensitivity. `supervision_matched_nonlinear_v1/`
owns the shared-label 69-parameter MLP comparison and direct paired contrasts.
`open3dsg_official_route_v1/` owns the public-eligible 533, conservative
public/full-target 548, and recovered/full-target 548 sensitivity.

The paper-facing fixed-model ablation route is `structured_ablation_v1/`.
Verify `routed_public_full_evaluation/manifest.json`: every locked input hash,
public/full context count, source/main point equivalence, donor-coverage rule,
support/contact pass-through, and source-score exclusion check must be `true`.
Support/contact is excluded from all compatibility interventions because the
primary route passes it through unchanged. The older `evaluation/` manifest
owns the unrestricted/recovered mechanism audit used only in the supplement.

The train-only counterfactual-policy sensitivity is
`counterfactual_sensitivity_v1/`. Its protocol freezes nine
one-factor-at-a-time variants over proximity threshold, vertical margin,
negative cap, and pairwise-loss weight. Verify `evaluation/manifest.json` for
the exact 1,061/117/157 firewall, bit-exact default model/metric equivalence,
548 contexts, 3,972 GT relations, zero orbit errors, finite weights, and
source-score/predictor-identity exclusion. The compact output is about 4.1 MB
and deliberately retains no duplicate variant row-level exports.

The nonlinear transfer services deterministically refit the frozen SGFN
internal-development model, then apply it without target-source labels or
normalization to VL-SAT and Open3DSG. Their serialized parameter,
normalization, and training-trace payloads must match each other and the
original SGFN run when canonicalized. Outputs are under
`nonlinear_transfer_v1/{vlsat,open3dsg}/`.

These artifacts total under 3 MB and duplicate no row-level source data. They
depend on the existing multi-gigabyte verification JSONL files; do not delete
those inputs if a local rerun is required. The current active paper scope is
3DSSG/3RScan only. ReplicaSSG/FROSS artifacts are not part of this route.
