# Research Index

Last updated: 2026-05-10

## Status

현재 하네스는 `CAND-001 hypothesis prep`과 `CAND-003 literature survey`를 병렬로 추적한다.

CAND-001 H001은 H001-Mini, hardened `VL-SAT` evaluation, G2 point/subtype join, G3 controls, G4 structured audit, reduced 50-row visual sanity check, G5 baseline feasibility, G6 reportability, FROSS/Open3DSG second-source feasibility, final scoped evidence lock, GT-based verifier evaluation, and scoped main experiment implementation spec까지 완료했다. H001 문서는 `01_overview.md` through `07_experiment_spec.md`의 7개 canonical file로 병합했다.

Facts:

- `07_experiment_spec.md` fixes the scoped experiment plan: fixed inputs, metrics, tables, figures, claim boundary, acceptance criteria, and Docker-based reproducibility rule.
- Hardened `VL-SAT` raw dump/export is ready with 388 subgraphs, 25,916 directed pairs, 673,816 prediction rows, and 7,505 ground-truth rows.
- `probabilistic_recalibrated` improves R@50/R@100 over semantic-only while lowering violation rate.
- GT-based verifier evaluation has GT positives 2,545, GT-derived negatives 2,545, positive nonviolated 0.9972, negative nonsatisfied 0.9694, and `p_geom_valid` AUROC/AUPRC 0.9779/0.9737.
- Visual spot-check status is `ready_sanity_pass` with reviewer id `yhkim`, labels 50/50, target quality-issue rate 0.9333, and contradiction rate 0.0333.
- FROSS is runtime-blocked and cannot cover `proximity` or `relative_vertical`.
- Open3DSG covers `support_contact`, `proximity`, and `relative_vertical` at source-contract level; the selected top-tier expansion is Dockerized Open3DSG checkpoint reproduction followed by second-source adapter metrics.
- `experiments/H001_geom_reliability/` is created and Docker-run ready. The Docker table builder generated Table 1-6, figure specs, `manifest.lock.json`, and `report.md` from locked hypothesis artifacts.
- Dockerized Open3DSG checkpoint reproduction plan is ready under `experiments/H001_geom_reliability/sources/open3dsg/`, including official train split counts, H001 eval split counts, dependency pins, dataset/cache mounts, train/eval commands, and failure budget.
- Open3DSG `training_repro` metadata/split staging is ready with no H001 held-out leakage. Full payload staging is complete: train scan dirs/raw/mesh/sequence are 1178/1178, train-dev payload is 30/30, and `open3dsg_train_handoff` status is `ready_for_open3dsg_env_check`.
- Open3DSG Docker env/cache preflight is ready on the cu128 image: torch `2.8.0+cu128`, CUDA device count 1, RTX 5090 `sm_120` supported, and only `torch_hub` remains as a non-blocking cache warning.
- Open3DSG train view staging is complete at 1178/1178 view pickles. `train_preprocess_full` exited 0 but produced 108 missing outputs; all 108 match the source-level `too few visible objects` drop, and a representative Docker retry did not recover the sampled missing targets.
- Open3DSG runtime train split is now explicitly filtered to the preprocessed-ready subset: 1158 scans / 3744 subgraphs / 79,704 relations retained from the official 1178 scans / 3852 subgraphs / 81,190 relations. The 108 removed subgraphs / 1,486 relations are recorded under `train_preprocess_filter/`.
- Open3DSG validation coverage guard is complete: validation views 30/30, runtime validation split 30 scans / 156 subgraphs / 3,696 relations after filtering 4 non-recoverable preprocess drops.
- Protected `dump_features_3rscan` preflight reports `ready`; official feature dump reaches feature writing. Docker `open3dsg_post_dump_handoff` last recorded 1131/3900 complete feature ids, 29.00%, and status `waiting_for_feature_dump_completion`; it also freezes the post-dump gates before training/metric transition. The restart policy uses lazy dataset loading, pre-forward skip-existing resume, deterministic no-shuffle dump iteration, no-grad feature dump, explicit `--epochs 1`, `workers=0`, and `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`. Open3DSG model training has not started.
- Open3DSG pre-metric failure-analysis schema is ready under `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis/`: 14 fixed primary categories, fixed assignment priority, 6 aggregation table specs, example rows, and status `failure_analysis_schema_ready_no_metric_run`. The Docker `open3dsg_failure_generator_smoke` skeleton also generated 6 synthetic rows across 6 primary categories with 0 validation errors under `failure_analysis_generator_smoke/`. No Open3DSG metric/failure inspection was performed while designing or smoke-validating it.
- Open3DSG checkpoint provenance/selection template is frozen under `experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection/`; current status is `checkpoint_selection_template_ready_checkpoint_missing` with blockers `no_checkpoint_candidates` and `official_feature_audit_not_ready:blocked`. The policy forbids choosing a primary checkpoint using H001 held-out metrics or failure inspection.
- Open3DSG raw-dump identity checklist is frozen under `experiments/H001_geom_reliability/sources/open3dsg/raw_dump_identity/`; current status is `raw_dump_identity_checklist_ready_raw_dump_missing`. It fixes the raw-dump identity denominator to 127 scans, 388 contexts, and 25,916 directed pairs, and blocks conversion/metric promotion until raw rows preserve scan/subgraph/object-pair identity.
- Open3DSG metric-scope policy is frozen under `experiments/H001_geom_reliability/sources/open3dsg/metric_scope/`; current status is `metric_scope_policy_ready_no_metric_execution`. It fixes the in-scope GT denominator to 2,545 rows across support_contact 1,199 / proximity 1,128 / relative_vertical 218, requires exact predicate-label recall matching, and records filtered-train/covered-scope caveats.
- Open3DSG metric/join contract is frozen under `experiments/H001_geom_reliability/sources/open3dsg/metric_join_contract/`; current status is `blocked_runtime_inputs_missing` because real Open3DSG prediction JSONL and geometry verification JSONL are missing. H001 GT JSONL is present with 7,505 rows. Docker table builder now writes `sources/open3dsg/table6_hook.json` and keeps Open3DSG Table 6 blocked until `metrics.json` status is `ready`, condition metrics are nonempty, blockers are empty, and `metric_scope` is ready. This is contract evidence only, not metric evidence.
- Qwen-VL optional modern semantic-source extension has frozen input JSON Schema, output JSONL contract, Docker `qwen_vl_contract_validator` parser skeleton, a 30-row non-held-out tiny pilot scope, Docker `qwen_vl_runtime_plan` model-lock output, and Docker-rendered pair crops. Tiny pilot family counts are support_contact/proximity/relative_vertical 10/10/10 with held-out overlap 0; `qwen_vl_pair_crop_render` rendered 30/30 pair crops after adding a shared-view selection gate, and validation parsed 30/30 rows with 0 errors/warnings. Recommended primary runtime model is `Qwen/Qwen3-VL-4B-Instruct` revision `ebb281ec70b05090aa6165b016eac8ec08e71b17` under `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17`. Model download and inference have not started.

Inference:

- Current CAND-001 gate is restarting/monitoring the protected official Open3DSG feature dump under the hardened resume policy; the reduced TopK1/scales1 route is allowed only for checkpoint smoke, not paper-result evidence.
- The method contribution should be framed as calibrated geometry-consistency evaluation and re-ranking, not as a verifier script.
- Current evidence supports a scoped `VL-SAT`-centered geometry-consistency reliability claim as fallback.
- For the top-tier main path, second-source adapter evidence from Open3DSG is preferred over a single-baseline-only justification.

CAND-003은 2026-04-30 P1 paper intake까지 통해 RieMind, `3D-VCD`, `SayPlan`, `SG-Nav`, `SCOUT/SymSearch`, `3DGraphLLM`, `3D-Mem`의 novelty boundary와 offline verifier/refiner first cut을 정리했다.

## Active Questions

1. Official Open3DSG BLIP TopK5/scales3 feature dump를 hardened resume policy로 계속 둘 것인가, 아니면 reduced/pilot route를 checkpoint smoke 전용으로 먼저 실행할 것인가?
2. `dump_features_3rscan` partial/full outputs가 Docker `feature_audit`에서 expected train+validation feature ids를 얼마나 만족하는가?
3. Open3DSG train filter limitation을 final paper tables/caveat에 어떤 문장으로 고정할 것인가?
4. H001 eval preprocessed partial coverage 11 skipped subgraphs를 checkpoint가 생긴 뒤 final metric claim에서 어떻게 filter/caveat할 것인가?
5. Open3DSG metric outputs가 생긴 뒤 synthetic-smoke row generator를 real prediction/GT/geometry/metric joins로 언제 전환할 것인가?
6. Qwen-VL pair crop validation 이후 locked `Qwen/Qwen3-VL-4B-Instruct`로 runtime smoke를 진행할 것인가, 아니면 Open3DSG dump/checkpoint를 우선할 것인가?
7. Qwen-VL runtime smoke를 진행한다면 model download/background job policy와 decoding/runtime manifest를 어떻게 고정할 것인가?
8. Strictly blinded independent audit wording이 필요하면 `reference.jsonl`을 보지 않은 reviewer로 50-row check를 반복할 것인가?
9. CAND-003을 CAND-001의 downstream extension으로 둘 것인가, 독립 thesis 후보로 키울 것인가?

## Current Working Files

- `docs/literature.md`: literature workflow
- `docs/hypothesis.md`: hypothesis workflow
- `literature/README.md`: trend synthesis / cross-paper insights
- `literature/PAPER.md`: paper registry / reading queue
- `literature/Contribution Candidates.md`: contribution candidates
- `literature/CAND-001.md`: CAND-001 details
- `literature/CAND-003.md`: CAND-003 literature survey
- `hypothesis/README.md`: hypothesis index
- `hypothesis/CAND-001/README.md`: CAND-001 hypothesis index
- `hypothesis/CAND-001/H001_geometry-grounded-verification/`: active H001 files
- `experiments/H001_geom_reliability/`: active Docker experiment root

## Expansion Rule

문헌 조사 결과는 `literature/`에 저장한다. Hypothesis 산출물은 `hypothesis/`에 저장한다. 논문 본문용 실제 experiment 구현은 Docker 기반으로만 진행한다. 현재 active experiment root는 `experiments/H001_geom_reliability/`이다. `paper/`, `decisions/` 구조는 아직 만들지 않는다.

Research target rule: 연구 목표와 방향성은 AI, ML, CV, Robotics top-tier journal/conference를 타겟으로 판단한다.
