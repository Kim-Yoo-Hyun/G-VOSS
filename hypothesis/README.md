# Hypothesis Index

Last updated: 2026-05-10

이 폴더는 literature candidate를 검증 가능한 research hypothesis로 좁히는 산출물을 저장한다. workflow와 작성 규칙은 `docs/hypothesis.md`를 따른다.

## Active Candidate

- `CAND-001: Geometry-Grounded Open-Vocabulary Relation Graph`
- Source: `literature/CAND-001.md`
- Status: H001 hypothesis-stage evidence is locked for a scoped `VL-SAT`-centered experiment. H001 notes are consolidated into seven canonical files, `01_overview.md` through `07_experiment_spec.md`.

## Hypothesis Registry

| Hypothesis | Folder | Status | Next Gate |
| --- | --- | --- | --- |
| H001: Geometry-grounded verification of open-vocabulary 3DSSG relations | `hypothesis/CAND-001/H001_geometry-grounded-verification/` | Hypothesis-stage evidence, Docker `VL-SAT` table/report reproduction, Open3DSG checkpoint reproduction plan, full payload staging, train/validation coverage guard, dump-feature runtime hardening, post-dump handoff gates, checkpoint-selection template, raw-dump identity checklist, metric-scope policy, Open3DSG failure-analysis schema, synthetic row-generator smoke, metric/join blocked-input contract, Table 6 blocked hook, and Qwen-VL tiny-pilot model-lock/pair-crop rendering complete | Continue protected Open3DSG feature dump; run real Open3DSG metric/join only after prediction JSONL, geometry join, and GT join exist |

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
- Protected `dump_features_3rscan` reaches feature writing. Docker `open3dsg_post_dump_handoff` last recorded 1131/3900 complete feature ids, 29.00%, and status `waiting_for_feature_dump_completion`; it also freezes `feature_audit -> train_pilot -> train_full -> eval/raw dump -> adapter/metric/failure-analysis` gates. Restart policy uses lazy dataset loading, pre-forward skip-existing resume, deterministic no-shuffle dump iteration, no-grad feature dump, explicit `--epochs 1`, `workers=0`, and a stable official feature run dir. Reduced TopK1/scales1 route is checkpoint-smoke-only.
- Open3DSG checkpoint provenance/selection template is frozen under `experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection/`; current status is `checkpoint_selection_template_ready_checkpoint_missing` with blockers `no_checkpoint_candidates` and `official_feature_audit_not_ready:blocked`. It forbids primary checkpoint selection using H001 held-out metrics or failure inspection.
- Open3DSG raw-dump identity checklist is frozen under `experiments/H001_geom_reliability/sources/open3dsg/raw_dump_identity/`; current status is `raw_dump_identity_checklist_ready_raw_dump_missing`, with fixed identity scope 127 scans / 388 contexts / 25,916 directed pairs and blocker `missing_raw_dump`.
- Open3DSG metric-scope policy is frozen under `experiments/H001_geom_reliability/sources/open3dsg/metric_scope/`; current status is `metric_scope_policy_ready_no_metric_execution`, with in-scope GT denominator 2,545 rows across support_contact 1,199 / proximity 1,128 / relative_vertical 218. Recall matching remains predicate-label exact; filtered-train and covered-scope caveats are fixed before metric execution.
- Open3DSG failure-analysis schema is locked before metric/failure inspection. Docker `open3dsg_failure_schema` generated `schema.json`, `taxonomy.json`, `aggregation_plan.json`, `example.jsonl`, `manifest.json`, and `report.md` under `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis/`; status is `failure_analysis_schema_ready_no_metric_run`. Docker `open3dsg_failure_generator_smoke` generated 6 synthetic rows with 0 validation errors under `failure_analysis_generator_smoke/`; status is `failure_analysis_generator_smoke_ready_no_metric_inspection`.
- Open3DSG metric/join contract is frozen under `experiments/H001_geom_reliability/sources/open3dsg/metric_join_contract/`; current status is `blocked_runtime_inputs_missing` because real Open3DSG prediction JSONL and geometry verification JSONL are missing. H001 GT JSONL is present with 7,505 rows. Docker table builder now writes `sources/open3dsg/table6_hook.json` and keeps Open3DSG Table 6 blocked until real ready metrics exist. This is contract evidence only, not metric evidence.
- Qwen-VL optional modern semantic-source extension has frozen input/output JSONL contracts, a Docker contract-only validator/parser skeleton, a 30-row non-held-out tiny pilot scope, a Docker runtime model-lock plan, and 30/30 rendered pair crops. Status is `pair_crops_rendered_no_model_download_no_inference` for crop rendering and `runtime_plan_ready_no_model_download_no_inference` for runtime preflight; family counts are support_contact/proximity/relative_vertical 10/10/10 with held-out overlap 0. Recommended primary model is `Qwen/Qwen3-VL-4B-Instruct` revision `ebb281ec70b05090aa6165b016eac8ec08e71b17`, local-dir `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17`. Model download and inference have not started.

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

- Baseline-agnostic and broad open-vocabulary final claims remain blocked until second-source adapter evidence is recorded.
- FROSS adapter implementation is blocked until a FROSS-compatible prediction pickle or rendered-depth/2D-SG staged root exists; FROSS does not cover `proximity` or `relative_vertical`.
- Open3DSG second-source evidence is blocked until official feature dump completion, Docker-reproduced checkpoint, identity-preserving raw dump, prediction JSONL export, geometry verification JSONL, metric run, and real locked-schema failure-analysis rows exist. The current metric/join output is a blocked-input contract only, and the current failure-analysis generator output is synthetic smoke only. Neither may be promoted to paper-result evidence. Reduced/pilot route can support checkpoint smoke only and must not be promoted to paper-result evidence.
- Qwen-VL metric evidence is blocked until the locked `Qwen/Qwen3-VL-4B-Instruct` local cache/runtime smoke succeeds or a documented fallback is chosen, identity-preserving held-out prediction JSONL is exported, geometry join succeeds, and metric tables are generated.
- Current G4 evidence should not be described as a large-scale or strictly blinded human audit.
- `experiments/H001_geom_reliability/` is the active Docker experiment root; do not create `paper/` or `decisions/` yet.
- Host-only outputs must not be promoted to paper experiment results; final paper tables/reports must be reproducible from documented Docker commands.
