# Hypothesis Index

Last updated: 2026-05-19

이 폴더는 literature candidate를 검증 가능한 research hypothesis로 좁히는 산출물을 저장한다. workflow와 작성 규칙은 `docs/hypothesis.md`를 따른다.

## Active Candidate

- `CAND-001: Geometry-Grounded Open-Vocabulary Relation Graph`
- Source: `literature/CAND-001.md`
- Status: H001 hypothesis-stage evidence is locked for a scoped `VL-SAT`-centered experiment. H001 notes are consolidated into seven canonical files, `01_overview.md` through `07_experiment_spec.md`.

## Hypothesis Registry

| Hypothesis | Folder | Status | Next Gate |
| --- | --- | --- | --- |
| H001: Geometry-grounded verification of open-vocabulary 3DSSG relations | `hypothesis/CAND-001/H001_geometry-grounded-verification/` | Hypothesis-stage evidence, Docker `VL-SAT` table/report reproduction, Open3DSG checkpoint reproduction, raw-dump identity, adapter export, geometry join, metric eval, Table 6 ready hook, locked failure-analysis schema, real failure-analysis rows, qualitative case inspection, paper caveat wording, and Qwen-VL full-source runner plan complete | Decide paper transition vs optional extension |

## Current Gate

H001 has entered the Docker experiment phase.

Facts recorded in the canonical files:

- `07_experiment_spec.md` fixes the scoped experiment plan: metrics, tables, figures, fixed input counts, allowed claim, acceptance criteria, and Docker-based reproducibility rule.
- First baseline is `VL-SAT` / `vlsat_closed_set`.
- Fixed hardened input counts are 127 scans, 388 subgraphs, 25,916 directed pairs, 673,816 prediction rows, 7,505 ground-truth rows, and 2,545 in-scope GT relation instances.
- Hardened `probabilistic_recalibrated` improves R@50/R@100 over `semantic_only` while lowering Violation@50/Violation@100.
- GT-based verifier evaluation reports GT positives 2,545, GT-derived negatives 2,545, positive nonviolated 0.9972, negative nonsatisfied 0.9694, and `p_geom_valid` AUROC/AUPRC 0.9779/0.9737.
- Reduced 50-row visual spot-check has reviewer id `yhkim`, status `ready_sanity_pass`, target quality-issue rate 0.9333, contradiction rate 0.0333, and a provenance caveat that Codex transcribed reviewer-confirmed reference-aligned labels.
- Method contribution is framed as calibrated geometry-consistency evaluation and re-ranking, not as a verifier script.
- Top-tier expansion direction is Open3DSG second-source adapter evidence from a Docker-reproduced checkpoint.
- Docker experiment root `experiments/H001_geom_reliability/` generated Table 1-6, `manifest.lock.json`, `report.md`, and figure specs from locked artifacts.
- Dockerized Open3DSG checkpoint reproduction plan is ready under `experiments/H001_geom_reliability/sources/open3dsg/`.
- Open3DSG `training_repro` metadata/split staging is ready with H001 held-out overlap 0/0. It stages official train 1178 scans / 3852 subgraphs / 81,190 relations and train-dev without H001 30 scans / 160 subgraphs / 3,749 relations.
- Open3DSG full payload staging is complete. Runtime train split is explicitly filtered to 1158 scans / 3744 subgraphs / 79,704 relations; runtime validation split is filtered to 30 scans / 156 subgraphs / 3,696 relations.
- Protected Open3DSG feature dump and H001 held-out feature-cache generation are complete; H001 eval feature shard loop reached 377/377 covered loadable feature ids. Reduced TopK1/scales1 route remains checkpoint-smoke-only.
- Open3DSG checkpoint provenance/selection is ready under `experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection/`; selected checkpoint is `epoch=13-step=13104.ckpt`, chosen by train-dev `val/loss` before H001 held-out metrics/failure/visual inspection. It forbids primary checkpoint selection using H001 held-out metrics or failure inspection.
- Open3DSG raw-dump identity audit is ready under `experiments/H001_geom_reliability/sources/open3dsg/raw_dump_identity/`; fixed identity scope is 127 scans / 388 contexts / 25,916 directed pairs. `raw_dump/raw.jsonl` has 19,162 rows, and clean v14 streaming same-path resume completed with exit `0` and matching SHA256, so source-process provenance is available. Historical exit-137 attempts stay as run records.
- Open3DSG metric-scope policy is frozen under `experiments/H001_geom_reliability/sources/open3dsg/metric_scope/`; current status is `metric_scope_policy_ready_no_metric_execution`, with in-scope GT denominator 2,545 rows across support_contact 1,199 / proximity 1,128 / relative_vertical 218. Recall matching remains predicate-label exact; filtered-train and covered-scope caveats are fixed before metric execution.
- Open3DSG failure-analysis schema is locked before metric/failure inspection. Docker `open3dsg_failure_schema` generated `schema.json`, `taxonomy.json`, `aggregation_plan.json`, `example.jsonl`, `manifest.json`, and `report.md` under `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis/`; status is `failure_analysis_schema_ready_no_metric_run`. Docker `open3dsg_failure_generator_smoke` generated 6 synthetic rows with 0 validation errors under `failure_analysis_generator_smoke/`; status is `failure_analysis_generator_smoke_ready_no_metric_inspection`.
- Open3DSG adapter, geometry join, metric eval, and Table 6 hook are ready. Docker `open3dsg_adapter_raw_dump` exported 496,600 prediction rows, Docker `open3dsg_geometry_join` preserved 496,600/496,600 rows and scored 114,600 geometry-checkable rows, Docker `open3dsg_metric_eval` generated `sources/open3dsg/metrics/metrics.json` with status `ready`, and Docker `table_builder` marks Open3DSG Table 6 `ready`. Claims remain scoped to measured H001 families and closed-set/GT-object setting.
- Open3DSG real failure-analysis rows are ready under `experiments/H001_geom_reliability/sources/open3dsg/failure_rows/`: 57,736 rows, 0 validation errors, 6,162 visual-audit queue rows, generated from semantic top-100 or geometry-reranked top-100 union per subgraph.
- Open3DSG qualitative case inspection is ready under `experiments/H001_geom_reliability/sources/open3dsg/failure_cases/`: 36 inspected cases, 23/36 demoted by geometry-aware reranking, 13/36 promoted or retained, 10/36 rule-violated cases with `p_geom_valid > 0.9`, and no taxonomy change.
- Open3DSG paper caveat wording is ready under `experiments/H001_geom_reliability/sources/open3dsg/paper_caveats/`: filtered train 3,744/3,852 subgraphs, train-dev validation 156/160 subgraphs, H001 covered loadable scope 377/388 contexts with `validation_missing_preprocessed:11`, averaged-BLIP variant, exact-label 2,545-row H001-family denominator, and residual calibration risk.
- Qwen-VL is fixed as a third semantic source / modern VLM extension, not a VL-SAT/Open3DSG replacement. It has frozen input/output JSONL contracts, a Docker contract-only validator/parser skeleton, a 30-row non-held-out tiny pilot scope, a Docker runtime model-lock plan, 30/30 rendered pair crops, model cache verification, runtime preflight, 3-row tiny inference smoke, runtime raw-response validation, a frozen full-source promotion plan, a full-source input audit, all-scope crop preflight, and a frozen full-source inference runner/resume plan. Recommended primary model is `Qwen/Qwen3-VL-4B-Instruct` revision `ebb281ec70b05090aa6165b016eac8ec08e71b17`, local-dir `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17`. Current full-source input audit has 77,748 universe rows, 33,384 inferable input rows, 44,364 missing rows, and 134 shards; crop preflight verifies 11,128 unique pair crops for the inferable rows; shard 0000 inference completed and validated with 250/250 parsed rows. Remaining shard loop is running in tmux `h001_qwen_vl_infer_remaining` with run id `20260527_023111` for shards 0001-0133. Full paper-metric evaluation has not started.

Inference:

- H001 is promising as a scoped top-tier direction. The current evidence supports a `VL-SAT`-centered geometry-consistency reliability claim as fallback, while the preferred top-tier path is second-source Open3DSG evidence rather than single-baseline-only justification.

## Parallel Track Dependencies

Calibration and prediction/evaluation can proceed in parallel only before their merge point.

Allowed parallel work:

- Calibration track: fit and apply frozen `p_geom_valid` from train/dev calibration rows.
- Prediction/evaluation track: identity-preserving prediction export, geometry join, metric runner extension, and non-final schema validation.

Do not violate these dependencies:

- Do not fit `p_geom_valid` if `train_dev_calib` is missing, blocked, or regenerated with validation errors.
- Do not run final prediction-level evaluation before `VL-SAT` predictions, geometry join, and calibrator outputs all exist.
- Do not train or tune on held-out validation scans.
- Do not change train/dev scan selection after inspecting held-out prediction failures.
- Do not place scans from the same 3RScan reference/rescan group across train, dev, and held-out validation when group metadata is available.

## Current Artifact Families

- One-scan verifier artifacts: `artifacts/one_scan/`
- Layout and staged-root artifacts: `artifacts/layout/`
- Subset manifests: `artifacts/subset/`
- Calibration outputs: `artifacts/calibration/`
- `VL-SAT` prediction/evaluation outputs: `artifacts/evaluation/vlsat_closed_set/`
- Audit outputs: `artifacts/evaluation/vlsat_closed_set/hardened/human_audit/`
- Evidence lock and GT verifier evaluation: `artifacts/evaluation/vlsat_closed_set/hardened/evidence_lock/`, `artifacts/evaluation/vlsat_closed_set/hardened/gt_eval/`
- FROSS and Open3DSG readiness outputs: `artifacts/evaluation/fross_scannet20/`, `artifacts/evaluation/open3dsg_ov/`

## Blocked Items

- Baseline-agnostic and broad open-vocabulary final claims remain blocked beyond the measured H001-family cross-source result.
- FROSS adapter implementation is blocked until a FROSS-compatible prediction pickle or rendered-depth/2D-SG staged root exists; FROSS does not cover `proximity` or `relative_vertical`.
- Open3DSG second-source metric, real failure-analysis, qualitative inspection, and paper caveat wording evidence exist. Reduced/pilot routes still must not be promoted to paper-result evidence.
- Qwen-VL metric evidence is blocked until sharded full-source inference, parser validation, identity-preserving prediction JSONL export, geometry join, metrics, controls, bootstrap CI, and audit all complete in Docker.
- Current G4 evidence should not be described as a large-scale or strictly blinded human audit.
- `experiments/H001_geom_reliability/` is the active Docker experiment root; do not create `paper/` or `decisions/` yet.
- Host-only outputs must not be promoted to paper experiment results; final paper tables/reports must be reproducible from documented Docker commands.
