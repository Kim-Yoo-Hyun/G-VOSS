# TODO

Last updated: 2026-05-10

이 파일은 에이전트가 다음 작업 계획과 진행 상태를 관리하는 루트 작업판이다. 자세한 문헌 조사 내용은 `literature/`에 기록하고, 자세한 hypothesis 근거는 `hypothesis/`에 기록한다.

## Current Phase

Parallel candidate tracking.

CAND-001은 hypothesis prep / verifier implementation 트랙이다. H001 hypothesis-stage evidence lock, GT-based verifier evaluation, reduced 50-row visual sanity check, and scoped main experiment implementation spec are complete. H001 markdown records have been consolidated into seven canonical files:

- `01_overview.md`
- `02_method.md`
- `03_data_baseline.md`
- `04_results.md`
- `05_audit.md`
- `06_second_source.md`
- `07_experiment_spec.md`

Docker-based scoped H001 experiment workflow entry는 완료했다. `experiments/H001_geom_reliability/`에서 Docker build/run으로 locked `VL-SAT` artifact를 검증하고 Table 1-6, figure specs, locked input manifest, report를 생성했다. Method contribution은 verifier script가 아니라 calibrated geometry-consistency evaluation/re-ranking framework로 정리한다. Top-tier main path는 single-baseline-only justification보다 Open3DSG second-source adapter evidence를 우선한다. Qwen2.5-VL/Qwen3-VL은 Open3DSG reproduction anchor를 대체하지 않는 modern-VLM semantic-source extension으로 허용하며, Docker `qwen_vl_adapter_contract`가 2B/3B/4B 후보, frozen input JSON Schema, frozen output JSONL contract를 생성했다. Docker `qwen_vl_runtime_plan`은 primary model lock을 `Qwen/Qwen3-VL-4B-Instruct` revision `ebb281ec70b05090aa6165b016eac8ec08e71b17`로 추천하고, local-dir을 `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17`로 고정했다. Docker `qwen_vl_pair_crop_render`는 renderable shared-view gate를 적용한 30-row tiny pilot pair crops를 생성했고 validator/runtime preflight가 pair crops 30/30을 확인했다. Qwen-VL model download/inference는 아직 시작하지 않았다. SceneFun3D/FunGraph3D는 spatial relation claim을 대체하지 않는 robotics/functionality expansion으로만 허용한다. Dockerized Open3DSG checkpoint reproduction plan, post-dump handoff gates, checkpoint provenance/selection template, raw-dump identity checklist, metric-scope policy, pre-metric failure-analysis schema, synthetic failure-analysis row-generator smoke, metric/join blocked-input contract, and Table 6 blocked hook are ready. Open3DSG `training_repro` metadata/split and full payload staging are complete with no H001 held-out leakage; Docker env/cache preflight is ready on the cu128 image, train/validation view staging is complete, and train/validation preprocess generation is explicitly filtered to preprocessed-ready runtime splits. Runtime train split is 1158 scans / 3744 subgraphs / 79,704 relations; runtime validation split is 30 scans / 156 subgraphs / 3,696 relations. Protected `dump_features_3rscan` reaches feature writing; Docker partial audit before restart recorded 5/3900 complete feature ids, and the hardened restart has confirmed additional feature writing. Runtime policy is now hardened with lazy/no-grad source patches, pre-forward skip-existing resume, deterministic no-shuffle dump iteration, `workers=0`, explicit `--epochs 1`, and a corrected stable `--load_features` run dir for training. Actual Open3DSG model training has not started. 논문 본문용 실제 experiment 구현은 계속 Docker 기반으로 진행한다. Host-only outputs must not be promoted to paper experiment results.

Research target rule: goal and direction are judged against AI, ML, CV, and Robotics top-tier journal/conference standards.

CAND-003은 literature survey 트랙이다. 2026-04-30 기준으로 LLM/VLM task reasoning on 3DSG, geometry-aware refinement, object placement/search/navigation decision evaluation을 primary source 중심으로 재확인했고, `literature/CAND-003.md`에 survey pass와 P1 intake 결과를 작성했다. 다음 CAND-003 단계는 사용자가 hypothesis workflow 승격 여부를 판단하는 것이다.

## Active Objective

- CAND-001: Open3DSG official feature dump를 hardened Docker command로 background 실행 중이다. Last check 2026-05-11 00:57 KST via Docker `open3dsg_post_dump_handoff`: 1932/3900 complete feature ids, 49.54%, no paper-result evidence yet. The 3900 target is feature-output coverage, not dataset download; raw dataset/payload staging is already complete.
- CAND-001: Qwen-VL contract-only stage는 frozen input schema / output JSONL contract / validator-parser skeleton / non-held-out tiny pilot scope / runtime preflight and model-lock plan / 30-row pair-crop rendering and validation까지 완료했다. Primary recommendation은 `Qwen/Qwen3-VL-4B-Instruct` revision `ebb281ec70b05090aa6165b016eac8ec08e71b17`, local-dir `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17`이다. Model download/inference는 시작하지 않았다.
- CAND-003: P1 결과물을 보고 hypothesis workflow 승격 여부를 판단한다.

## Now

### CAND-001

Data-dependent:

- [ ] Keep protected official BLIP TopK5/scales3 `dump_features_3rscan` running in background; check progress only when requested or when a dependent task needs the result
- [ ] Run Docker `feature_audit` after official dump completion, or `feature_audit_pilot` only if using the reduced checkpoint-smoke route

Non-data while dump runs:

- No active non-data task until feature dump completion or explicit optional-track decision.

### CAND-003

- No active task.

## Next

### CAND-001 Data-Dependent Order

- [ ] Audit Open3DSG feature dump outputs with Docker `feature_audit` after protected official dump reaches 3900/3900 complete feature ids
- [ ] Open3DSG checkpoint pilot training after official `feature_audit` pass
- [ ] Open3DSG full checkpoint training/reproduction after pilot checkpoint passes
- [ ] Open3DSG raw dump generation after reproduced checkpoint exists and `eval_preflight` passes
- [ ] Run `open3dsg_adapter_contract` and rerun without `--contract-only` after identity-preserving raw dump exists
- [ ] `open3dsg_ov` prediction JSONL export after raw dump exists
- [ ] Open3DSG metric/join runner with real runtime inputs after prediction JSONL, GT join, and geometry join exist
- [ ] Open3DSG real failure-analysis row generation after metric outputs exist; do not change the locked taxonomy without schema version bump
- [ ] Open3DSG preprocessed coverage decision/filtering for 11 skipped subgraphs before final metric claim

### CAND-001 Non-Data Order While Feature Dump Runs

- [ ] Optional Qwen-VL cache/runtime smoke plan only after explicit model-cache/download decision; prefer locked `Qwen/Qwen3-VL-4B-Instruct` revision `ebb281ec70b05090aa6165b016eac8ec08e71b17`, fallback `Qwen/Qwen2.5-VL-3B-Instruct`, parser-smoke `Qwen/Qwen3-VL-2B-Instruct`
- [ ] Optional reduced checkpoint smoke only if the official route is intentionally paused or declared too slow: `dump_features_3rscan_pilot` -> `feature_audit_pilot` -> `train_pilot_reduced`; do not promote to paper-result evidence
- [ ] Optional SceneFun3D/FunGraph3D expansion only if paper scope pivots to robotics/functionality: separate verifier contract, denominator, metrics, and claim boundary
- [ ] FROSS runtime artifact acquisition path: prediction pickle or rendered-depth/2D-SG staged root
- [ ] Implement minimal `fross_scannet20` prediction JSONL adapter after runtime artifact exists
- [ ] Relative horizontal coordinate-frame validation은 support/contact 보완 이후 필요 시 진행

### CAND-003

- [ ] CAND-003 hypothesis workflow 승격 여부 사용자 판단 대기

## Recently Completed

- [x] Literature PAPER.md SGAligner / SG-PGM positioning 업데이트 완료: SGAligner ICCV 2023 and SG-PGM CVPR 2024를 3D scene graph downstream alignment / semantic-geometric fusion 근거로 registry, CAND-001 evidence view, reading queue에 추가했다. H001 direct baseline이 아니라 relation reliability motivation / optional downstream sanity-check 근거로 경계를 기록했다.
- [x] H001 reviewer-risk defense checklist report 반영 완료: Docker `table_builder` report template and regenerated `experiments/H001_geom_reliability/report.md` now record likely reviewer attacks, required defenses, metric-scope denominator transparency, exact-label recall caveat, and the fact that background Open3DSG feature dump only strengthens defense after downstream audit/checkpoint/raw-dump/adapter/metric/failure-analysis gates complete.
- [x] H001 Open3DSG predicate-family mapping / denominator policy 완료: Docker `open3dsg_metric_scope` generated `sources/open3dsg/metric_scope/{predicate_mapping.json,denominator_policy.json,manifest.json,commands.md,report.md}` with status `metric_scope_policy_ready_no_metric_execution`; in-scope GT denominator 2,545 rows across support_contact 1,199 / proximity 1,128 / relative_vertical 218; recall matching remains predicate-label exact; filtered-train and covered-scope caveats are frozen before Open3DSG metric execution. Docker `table_builder` now requires this metric-scope policy for Open3DSG Table 6 promotion.
- [x] H001 Open3DSG raw-dump identity checklist 완료: Docker `open3dsg_raw_dump_identity` generated `sources/open3dsg/raw_dump_identity/{checklist.json,manifest.json,commands.md,report.md}` with status `raw_dump_identity_checklist_ready_raw_dump_missing`; fixed identity scope is 127 scans / 388 contexts / 25,916 directed pairs, and current blocker is missing real raw dump `raw_dump/raw.jsonl`. No Open3DSG eval, adapter conversion, metric computation, or failure inspection was run.
- [x] H001 Open3DSG checkpoint provenance/selection template 완료: Docker `open3dsg_checkpoint_selection` generated `sources/open3dsg/checkpoint_selection/{selection_policy.json,record_template.json,manifest.json,commands.md,report.md}` with status `checkpoint_selection_template_ready_checkpoint_missing`; current blockers are `no_checkpoint_candidates` and `official_feature_audit_not_ready:blocked`. The policy freezes route priority and forbids choosing a primary checkpoint using H001 held-out R@K, violation rate, failure-analysis distribution, or held-out visual inspection.
- [x] H001 Open3DSG Table 6 blocked hook 완료: Docker `table_builder` now writes `sources/open3dsg/table6_hook.json`, reads `sources/open3dsg/metric_join_contract/metrics.json`, and keeps `tables/table6_cross_source_status.*` blocked until Open3DSG `metrics.json` status is `ready`, condition metrics are nonempty, and blockers are empty. Current Open3DSG Table 6 status is `blocked` with blockers for missing prediction JSONL and geometry verification JSONL.
- [x] H001 Open3DSG metric/join runner contract skeleton 완료: Docker `open3dsg_metric_join_contract` generated `sources/open3dsg/metric_join_contract/{input_contract.json,output_contract.json,metrics.json,manifest.json,commands.md,report.md}` with status `blocked_runtime_inputs_missing`; H001 GT JSONL is present with 7,505 rows, while real Open3DSG prediction JSONL and geometry verification JSONL are missing. No heavy training, prediction inspection, or metric computation was run.
- [x] H001 Open3DSG post-dump handoff gate 고정 완료: Docker `open3dsg_post_dump_handoff` generated `sources/open3dsg/post_dump_handoff/{manifest.json,commands.md,report.md}` with status `waiting_for_feature_dump_completion`, ordered gates `feature_audit -> train_pilot -> train_full -> eval_preflight/eval_h001_gt_objects -> adapter_raw_dump -> real failure-analysis rows`, and current feature progress 1932/3900 complete ids (49.54% as of 2026-05-11 00:57 KST); no heavy training or metric inspection was run.
- [x] H001 Open3DSG failure-analysis row generator skeleton 완료: Docker `open3dsg_failure_generator_smoke` generated `sources/open3dsg/failure_analysis_generator_smoke/{rows.jsonl,summary.json,manifest.json,report.md}` with 6 synthetic rows, 6 primary categories, locked schema/taxonomy validation errors 0, and status `failure_analysis_generator_smoke_ready_no_metric_inspection`; no Open3DSG metric/failure inspection was performed.
- [x] H001 Open3DSG failure-analysis schema 설계 완료: Docker `open3dsg_failure_schema` generated `sources/open3dsg/failure_analysis/{schema.json,taxonomy.json,aggregation_plan.json,example.jsonl,manifest.json,report.md}` with status `failure_analysis_schema_ready_no_metric_run`; taxonomy has 14 fixed primary categories and 6 aggregation table specs, and no Open3DSG metric/failure inspection was performed.
- [x] H001 Qwen-VL tiny pilot pair-crop rendering 완료: Docker `qwen_vl_tiny_pilot_scope` now filters for shared subject/object views, Docker `qwen_vl_pair_crop_render` generated `sources/qwen_vl/crops/{records.jsonl,manifest.json,report.md}` plus 30 ignored PNG crops under `local_dataset/qwen_vl_crops/tiny_pilot/`; prompt template records red=subject and blue=object box convention; Docker `qwen_vl_tiny_pilot_validator` parsed 30/30 rows with 0 errors/warnings, and rerun `qwen_vl_runtime_plan` reports pair crops 30/30. No model download/inference was started.
- [x] H001 Qwen-VL crop-rendering preflight/model-lock plan 완료: Docker `qwen_vl_runtime_plan` generated `sources/qwen_vl/runtime_plan/{crop_plan.jsonl,model_recommendation.json,commands.md,manifest.json,report.md}` with status `runtime_plan_ready_no_model_download_no_inference`; context frames/object2image metadata are 30/30 and the recommended primary model is `Qwen/Qwen3-VL-4B-Instruct` revision `ebb281ec70b05090aa6165b016eac8ec08e71b17` under `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17`.
- [x] H001 Qwen-VL tiny pilot scope 선택 완료: Docker `qwen_vl_tiny_pilot_scope` selected 30 non-held-out pilot input rows from filtered train split, balanced as support_contact/proximity/relative_vertical 10/10/10 across 12 scans and 18 subgraphs; held-out overlap 0, pair crops reserved but not rendered, model download/inference not started. Docker `qwen_vl_tiny_pilot_validator` parsed 30/30 synthetic template rows with 0 errors/warnings.
- [x] H001 Qwen-VL contract-only validator/parser skeleton 완료: Docker `qwen_vl_contract_validator` generated `sources/qwen_vl/validation/{input_smoke.jsonl,parsed.jsonl,parser_contract.json,manifest.json,report.md}` with status `validator_parser_skeleton_ready_no_model_runtime`; model download/inference was not started.
- [x] H001 Qwen-VL input/output contract freeze 완료: Docker `qwen_vl_adapter_contract` regenerated frozen `input_schema.json`, `input_schema_example.json`, `output_schema.json`, `output_jsonl_contract.md`, `prediction_schema_example.json`, and status `io_contract_frozen_model_runtime_not_started`; model download/inference was not started.
- [x] Research target rule 추가: 연구 목표와 방향성은 AI, ML, CV, Robotics top-tier journal/conference를 타겟으로 판단한다.
- [x] H001 experiment spec에 Qwen2.5-VL/Qwen3-VL modern-VLM semantic-source extension 추가: Qwen-VL은 Open3DSG reproduction anchor의 대체가 아니라 trend-aligned optional track이며, Docker/model id/prompt/parser/prediction JSONL/geometry join/metric gate를 요구한다.
- [x] Qwen-VL adapter contract 생성 완료: Docker `qwen_vl_adapter_contract` generated `sources/qwen_vl/{adapter_contract.json,model_candidates.json,prediction_schema_example.json,prompt_templates.md,commands.qwen_vl.md,report.md}` with 2B/3B/4B small-model ladder.
- [x] H001 experiment spec에 layered paper strategy 추가: 3DSSG/VL-SAT main anchor, Open3DSG reproduction anchor, Qwen-VL modern semantic-source extension, SceneFun3D/FunGraph3D robotics/functionality expansion을 분리했다.
- [x] AGENTS long-running/background task policy 추가: long-running I/O jobs는 `tmux`/background로 실행, `logs/` timestamp log, resumable command, exact command/verification record, targeted log inspection, completion verification, TODO/hypothesis status update를 요구한다.
- [x] H001 Open3DSG hardened official dump restart 확인: tmux `h001_open3dsg_dump_features` restarted; preflight/patch ready, `epochs=1` active, existing 5 feature ids skipped in ~16s, and additional official TopK5/scales3 feature ids are being written.
- [x] H001 Open3DSG partial feature audit 완료: Docker `feature_audit` now records official run coverage as blocked with 5/3900 complete feature ids, train 5/3744, validation 0/156, missing preprocessed 0.
- [x] H001 Open3DSG feature dump runtime policy hardening 완료: previous official run was interrupted after confirming feature writing because the command needed stronger runtime policy; `dump_features_3rscan` now has explicit `--epochs 1`, pre-forward skip-existing resume, deterministic no-shuffle dump iteration, stable official run dir, corrected training `--load_features` path, and a clearly marked reduced TopK1/scales1 pilot route for checkpoint smoke only.
- [x] H001 Open3DSG validation coverage guard 완료: validation views 30/30, validation preprocess 156/160 ready after retry/filter, runtime validation split 30 scans / 156 subgraphs / 3,696 relations.
- [x] H001 Open3DSG `dump_features_3rscan` hardening 진행: process-pool crash는 `OPEN3DSG_DATASET_LOAD_WORKERS=1`로 우회, preload OOM은 `OPEN3DSG_LAZY_DATASET=1` lazy dataset patch로 우회, DataLoader shm bus error는 `workers=0`으로 우회, dump-time CUDA OOM은 `dump_features` no-grad patch와 `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`로 우회했다. Current run reaches feature writing but official BLIP TopK5/scales3 throughput is slow.
- [x] H001 Open3DSG missing preprocess recoverability audit 완료: `train_preprocess/full.log`의 `too few visible objects, scene missalignment possible` count가 108이고 manifest의 108개 `missing_output` ID와 일치한다. Docker representative retry는 sample missing targets를 회복하지 못했으며, 단순 재시도/fix 대상이 아니라 source-level visibility filter drop으로 판단했다.
- [x] H001 Open3DSG explicit train preprocess filter 적용 완료: runtime `relationships_train.json`/`train_scans.txt`를 preprocessed-ready split으로 갱신하고 `.unfiltered` backup을 남겼다. Runtime train split은 1178 scans / 3852 subgraphs / 81,190 relations에서 1158 scans / 3744 subgraphs / 79,704 relations로 줄었고, 108 missing subgraphs / 1,486 relations / 20 removed-only scans는 `train_preprocess_filter/`에 기록했다. Docker `train_preprocess_filter` service로 같은 count를 재현했고, protected `dump_features_3rscan` preflight now reports `ready`.
- [x] H001 Open3DSG cu128 env/cache + guarded dump rerun 완료: `env_check` passes with CUDA visible, device count 1, torch `2.8.0+cu128`, RTX 5090 `sm_120` supported; `cache_preflight` status is `ready_with_cache_warnings` with only `torch_hub` cache warning; the initial protected `dump_features_3rscan` rerun correctly stopped before Open3DSG execution at runtime coverage blockers `train_views:2/1178` and `train_preprocessed:7/3852`.
- [x] H001 Open3DSG train view/preprocess Docker staging smoke 완료: `train_views_audit`, `train_views_smoke`, and corrected `train_preprocess_smoke` services added; smoke generated/confirmed train views for 2 scans total and preprocessed 7 subgraphs for one scan, with no preprocess blockers in the smoke artifact.
- [x] H001 Open3DSG `train_views_full` 완료: detached tmux run exited 0; `train_views/full.log` and `train_views/manifest.json` report 1178/1178 ready scan view pickles, actions `generated` 1176 and `already_ready` 2.
- [x] H001 Open3DSG `train_preprocess_full` 완료: detached tmux run exited 0; `train_preprocess/manifest.json` status is `preprocess_partial_ready`, 3744/3852 ready subgraphs, 108 missing outputs across 101 scans, actions `generated` 3737 and `already_ready` 7. This initially blocked protected `dump_features_3rscan` at `train_preprocessed:3744/3852`; the later explicit filter item records the current resolution.
- [x] H001 Open3DSG full train payload staging 완료: `training_repro` status is `training_repro_staged_root_ready_for_view_preprocess`; official train payload is 1178/1178 for scan dirs, raw files, Open3DSG mesh/texture, and sequence files; train-dev payload is 30/30. Background tmux downloader session has ended, and `open3dsg_train_handoff` now reports `ready_for_open3dsg_env_check`.
- [x] H001 Open3DSG eval checkpoint/path guard 완료: Docker `eval_preflight` service and `eval_h001_gt_objects` inline guard added; it checks `OPEN3DSG_CHECKPOINT`, H001 runtime paths, model files, selected 127 scans / 388 contexts, Docker imports/CUDA, and raw-dump JSONL contract. Current protected eval smoke stops before `pip install -e .` and Open3DSG execution because checkpoint env/file is missing.
- [x] H001 Open3DSG adapter smoke-test 완료: `export_open3dsg_predictions.py --smoke-test` and Docker `open3dsg_adapter_smoke` service added; synthetic identity-preserving raw JSONL converts to H001 prediction JSONL with 388 contexts, 1 raw row, 2 prediction rows, zero errors/warnings. Contract-only adapter remains `adapter_contract_ready_raw_dump_missing` until reproduced checkpoint raw dump exists.
- [x] H001 Open3DSG model/cache preflight 완료: Docker `cache_preflight` service added for persistent `HOME`/`XDG_CACHE_HOME`, HF/torch/CLIP cache dirs, 300GB disk budget, OpenSeg/BLIP/PointNet local checkpoint files, and model import checks; current cu128 rerun passes required files/imports/disk and leaves only a non-blocking `torch_hub` cache warning.
- [x] H001 Open3DSG training preflight hardening 완료: `open3dsg_training_preflight.py` now checks full train payload, runtime train view/preprocess coverage, writable runtime/cache dirs, Open3DSG source entrypoint, Docker imports (`torch`, `pytorch_lightning`, `tensorflow`, `open3d`, `transformers`), and CUDA visibility; protected `dump_features_3rscan`, `train_pilot`, and `train_full` stop before Open3DSG execution until coverage/features are ready.
- [x] H001 Open3DSG Docker env image build/import check 완료: `h001-open3dsg-repro:cu128` build/import path passes with CUDA visible (`torch.cuda.is_available=True`, device count 1, torch `2.8.0+cu128`, RTX 5090 `sm_120` supported). 기록: `experiments/H001_geom_reliability/sources/open3dsg/env_check.md`.
- [x] H001 Open3DSG Docker training preflight guard 완료: `open3dsg_training_preflight.py` added and wired before `dump_features_3rscan`, `train_pilot`, and `train_full`; protected compose commands now stop before Open3DSG execution while payload is incomplete. Current guard artifacts are under `experiments/H001_geom_reliability/sources/open3dsg/training_preflight/`.
- [x] H001 Open3DSG training handoff + prediction adapter skeleton 완료: Docker `open3dsg_train_handoff` service generated `sources/open3dsg/training_handoff/{manifest.json,commands.md,report.md}` with current status `blocked_payload_incomplete`; Docker `open3dsg_adapter_contract` service generated `sources/open3dsg/adapter/{manifest.json,raw_schema_example.json,report.md}` with status `adapter_contract_ready_raw_dump_missing` and 388 H001 contexts.
- [x] H001 Open3DSG 3RScan payload batch route/progress 완료: Docker `open3dsg_payload` service added; audit pass, pilot batches, and resumable background `--limit 100` loop worked with no file/sequence failures in the recorded route; final synced `training_repro` readiness is train scan dirs 1178/1178, train mesh/texture 1178/1178, train sequence extracted 1178/1178.
- [x] H001 Open3DSG `training_repro` metadata/split staging 완료: Docker `open3dsg_train_root` service generated `sources/open3dsg/training_repro/{manifest.json,records.jsonl,missing_train_scans.txt,missing_train_dev_scans.txt,report.md}` and local staged root `local_dataset/Open3DSG_staged/training_repro/`; official train metadata 1178 scans / 3852 subgraphs / 81,190 relations, train-dev without H001 held-out 30 scans / 160 subgraphs / 3,749 relations, H001 held-out overlap train/train-dev 0/0; status `training_repro_staged_root_ready_for_view_preprocess`.
- [x] H001 Dockerized Open3DSG checkpoint reproduction plan 완료: Docker `open3dsg_plan` service generated `checkpoint_plan.{json,md}`, `Dockerfile.repro`, `compose.open3dsg.yaml`, `commands.open3dsg.md`, and status `checkpoint_reproduction_plan_ready_training_not_started`; split fixed to official train 1178 scans / 3852 subgraphs / 81,190 relations and H001 eval 127 scans / 388 subgraphs / 7,505 relations, with dependency pins, dataset/cache mounts, training commands, and failure budget recorded.
- [x] H001 Docker table/report reproduction 재실행 완료: `sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml build && env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm table_builder'`, status `ready`, predictions 673,816 / GT 7,505 / verification 673,816 row count 재확인
- [x] H001 hypothesis markdown consolidation 완료: H001 root markdown files reduced to 7 canonical files, with duplicated stage content merged and current dashboards updated.
- [x] H001 Docker experiment workflow entry 완료: `experiments/H001_geom_reliability/` 생성, Dockerfile/compose/commands/manifest/script 작성, `sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm table_builder'`로 Table 1-6, `manifest.lock.json`, `report.md`, `figure_specs.*`, source status files 생성; manifest status `ready`.
- [x] H001 top-tier direction update 완료: method contribution을 calibrated geometry-consistency evaluation/re-ranking framework로 정리하고, Open3DSG checkpoint를 Docker로 직접 재현해 second-source adapter result를 확보하는 방향을 선택; single-baseline reliability-layer justification은 fallback으로 유지.
- [x] H001 scoped main experiment implementation spec 완료: `07_experiment_spec.md`, status `hypothesis_stage_complete_for_geom_reliability_experiment`; fixed inputs, metrics, tables, figures, acceptance criteria, and proposed `experiments/H001_geom_reliability/` workflow root 고정.
- [x] Paper experiment Docker rule 고정: 논문 본문용 실제 experiment 구현은 Docker 기반으로만 진행하며, host-only output은 paper experiment 결과로 승격하지 않음.
- [x] H001 GT-based verifier evaluation 완료: GT positives 2,545, GT-derived negatives 2,545, positive nonviolated 0.9972, negative nonsatisfied 0.9694, `p_geom_valid` AUROC/AUPRC 0.9779/0.9737.
- [x] H001 reduced visual spot-check label fill/summary 완료: reviewer id `yhkim`, status `ready_sanity_pass`, labels 50/50, target quality-issue rate 0.9333, contradiction rate 0.0333.
- [x] H001 final scoped evidence lock 완료: status `scoped_hypothesis_evidence_locked_with_reduced_visual_sanity_check`; scoped main experiment implementation spec으로 진행 가능.
- [x] H001 Open3DSG second-source path decision 업데이트: official checkpoint 대기 대신 Dockerized checkpoint reproduction을 선택; raw dump/JSONL/join/metric은 reproduced checkpoint 이후 진행.
- [x] H001 Open3DSG runtime staging 완료: staged metadata/root, mesh/texture, view pickles, source-visible preprocessed pickles, BLIP2/OpenSeg/PointNet/PointNet2 ready/partial-ready; trained checkpoint missing.
- [x] H001 FROSS source/runtime feasibility 완료: FROSS is support/contact-only for H001 and blocked by missing runtime artifacts.
- [x] H001 G3/G4/G5/G6 hardening completed: family-specific calibration control, structured audit, baseline feasibility, and reportability gate recorded.
- [x] H001 hardened `VL-SAT` raw/export/join/metrics completed: 127 scans, 388 subgraphs, 673,816 prediction rows, 7,505 ground-truth rows.
- [x] H001 calibration track completed: calibration data contract, train/dev split/export, `p_geom_valid` smoke, family-specific control, and held-out application.
- [x] CAND-003 literature survey pass completed through P1 paper intake.

## Pending / Blocked

- [ ] Do not treat hardened `VL-SAT` metric summary as baseline-agnostic or broad open-vocabulary final evidence until Open3DSG second-source adapter evidence is recorded.
- [ ] FROSS adapter implementation is blocked until a FROSS-compatible prediction pickle or rendered-depth/2D-SG staged root exists.
- [ ] Do not use FROSS as full-family evidence; it does not cover H001 `proximity` / `relative_vertical` families.
- [ ] Open3DSG second-source evidence is blocked until full train view/preprocess coverage, feature dump, Docker-reproduced checkpoint, identity-preserving raw dump, prediction JSONL export, geometry join, and metric run exist.
- [ ] Do not choose or change the primary Open3DSG checkpoint using H001 held-out metrics, failure-analysis distribution, or held-out visual inspection.
- [ ] Do not convert Open3DSG raw dump to H001 prediction JSONL or run Open3DSG metrics until raw-dump identity audit passes.
- [ ] Do not promote Open3DSG metric/Table 6 results unless `metric_scope` status is ready, predicate recall remains exact-label matched, and filtered-train / covered-scope caveats are reported.
- [ ] Do not overstate the reduced 50-row visual sanity check as a large-scale or strictly blinded human audit; provenance is `yhkim` reference-aligned labels transcribed by Codex.
- [ ] Do not create `paper/` or `decisions/` folders yet; `experiments/H001_geom_reliability/` is the active Docker experiment root.
- [ ] Do not promote host-only outputs to paper experiment results; final paper tables/reports must be reproducible from documented Docker commands.
- [ ] Do not promote H001 to final paper claim without explicitly recording remaining limitations and next validation requirements.

## Rules

- 작업을 시작할 때 이 파일을 먼저 확인한다.
- 작업 중 새 task가 생기면 이 파일에 추가한다.
- 완료한 task는 체크하고, 필요한 상세 내용은 `literature/` 또는 해당 workflow 문서에 기록한다.
- 이 파일은 긴 설명을 담지 않는다. 계획, 상태, 다음 행동만 관리한다.
