# Research Workspace

이 저장소는 3D Scene Graph 석사 연구를 위한 작업 공간이다.

현재 단계는 CAND-001 hypothesis prep과 CAND-003 literature survey를 병렬로 추적하는 단계다. CAND-001은 `Geometry-Grounded Open-Vocabulary Relation Graph` 방향에서 H001 hypothesis-stage evidence lock과 scoped main experiment spec까지 완료했다. H001 문서는 `hypothesis/CAND-001/H001_geometry-grounded-verification/` 아래 7개 canonical 파일로 정리되어 있다.

## Current Focus

- CAND-001: `experiments/H001_geom_reliability/`에서 Docker-based `VL-SAT` table/report reproduction, Dockerized Open3DSG checkpoint reproduction plan, Open3DSG `training_repro` full payload staging, cu128 env/cache preflight, train/validation view staging, explicit train/validation preprocess filtering, and protected `dump_features_3rscan` runtime-policy hardening 진행
- CAND-001 next gate: restart/monitor official BLIP TopK5/scales3 `dump_features_3rscan` with hardened resume policy; reduced TopK1/scales1 route is checkpoint-smoke-only
- CAND-001 experiment rule: 논문 본문용 실제 experiment 구현은 Docker 기반으로만 진행하고 host-only output은 paper result로 승격하지 않는다
- Research target rule: 연구 목표와 방향성은 AI, ML, CV, Robotics top-tier journal/conference를 타겟으로 판단한다
- CAND-003: `Geometry-Aware Refinement of LLM/VLM Task Reasoning on 3DSG` literature survey / feasibility boundary 정리 완료, hypothesis workflow 승격 여부 판단 대기

## H001 Status

Facts:

- First prediction baseline is `VL-SAT` / `vlsat_closed_set`.
- Fixed hardened scope has 127 scans, 388 subgraphs, 25,916 directed pairs, 673,816 prediction rows, 7,505 ground-truth rows, and 2,545 in-scope GT relation instances.
- Hardened `semantic_only`: R@50/R@100 0.9599/0.9894, Violation@50/@100 0.0247/0.0469.
- Hardened `probabilistic_recalibrated`: R@50/R@100 0.9642/0.9921, Violation@50/@100 0.0234/0.0391.
- Hardened `family_specific_p_geom_valid`: R@50/R@100 0.9619/0.9914, Violation@50/@100 0.0204/0.0310.
- GT-based verifier evaluation: GT positives 2,545, GT-derived negatives 2,545, positive nonviolated 0.9972, negative nonsatisfied 0.9694, `p_geom_valid` AUROC/AUPRC 0.9779/0.9737.
- Structured audit: 250/250 labels, strict invalid-only precision 0.7133, quality-issue precision 0.8933.
- Reduced visual sanity check: 50/50 labels, reviewer id `yhkim`, status `ready_sanity_pass`, target quality-issue rate 0.9333, contradiction rate 0.0333.
- FROSS is runtime-blocked and does not cover `proximity` / `relative_vertical`.
- Open3DSG covers `support_contact`, `proximity`, and `relative_vertical` at source-contract level; the selected top-tier expansion is to generate the Open3DSG checkpoint ourselves through Dockerized reproduction.
- Docker experiment root `experiments/H001_geom_reliability/` has generated Table 1-6, `manifest.lock.json`, `report.md`, and figure specs from locked artifacts.
- Qwen-VL is staged only as an optional modern semantic-source extension: input/output contract, parser skeleton, 30-row non-held-out tiny pilot, model-lock plan, and 30/30 pair crops are ready; no Qwen model download or inference has started.
- Dockerized Open3DSG checkpoint reproduction plan is ready under `experiments/H001_geom_reliability/sources/open3dsg/`: official train split 1178 scans / 3852 subgraphs / 81,190 relations, H001 eval split 127 scans / 388 subgraphs / 7,505 relations, dependency pins, dataset/cache mounts, train/eval commands, and failure budget.
- Open3DSG `training_repro` metadata/split staging is ready with H001 held-out overlap 0/0: official train 1178 scans / 3852 subgraphs / 81,190 relations and train-dev without H001 30 scans / 160 subgraphs / 3,749 relations.
- Open3DSG full train payload staging is complete: train scan dirs, raw files, Open3DSG mesh/texture, and sequence files are 1178/1178; train-dev payload is 30/30; `open3dsg_train_handoff` status is `ready_for_open3dsg_env_check`.
- Open3DSG Docker env/cache is ready on `h001-open3dsg-repro:cu128` with torch `2.8.0+cu128` and RTX 5090 `sm_120` support; cache preflight has only a non-blocking `torch_hub` cache warning.
- Open3DSG train view generation is complete at 1178/1178 view pickles; `train_views_full` exited 0 with 1176 generated and 2 already ready.
- Open3DSG validation view/preprocess guard is complete: validation views 30/30 and runtime validation split 30 scans / 156 subgraphs / 3,696 relations after filtering 4 non-recoverable preprocess drops.
- Open3DSG train preprocess recoverability audit is complete: all 108 missing outputs match the source-level `too few visible objects` drop, and a representative Docker retry did not recover the sampled missing targets.
- Open3DSG runtime train split is explicitly filtered to preprocessed-ready rows: 1158 scans / 3744 subgraphs / 79,704 relations retained from the official 1178 scans / 3852 subgraphs / 81,190 relations. The 108 removed subgraphs / 1,486 relations are recorded under `train_preprocess_filter/`, and `.unfiltered` backups exist in the staged runtime split.
- Protected `dump_features_3rscan` preflight reports `ready`; official feature dump reaches feature writing. Docker partial audit before restart recorded 5/3900 complete feature ids, and the hardened restart has confirmed additional feature writing. The restart policy uses lazy dataset loading, pre-forward skip-existing resume, deterministic no-shuffle dump iteration, no-grad feature dump, explicit `--epochs 1`, `workers=0`, and `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`. Open3DSG model training has not started.

Inference:

- H001 is promising as a scoped top-tier direction.
- Current evidence supports a `VL-SAT`-centered geometry-consistency reliability claim as a fallback.
- For the main top-tier path, second-source adapter evidence is preferred over a single-baseline-only justification.
- Baseline-agnostic and broad open-vocabulary 3DSSG improvement claims remain blocked until Open3DSG filtered-train feature dump, checkpoint reproduction, adapter export, geometry join, and metric evidence exist. The train/validation filtering and any reduced/pilot-only route must be reported as scope limitations, not hidden as full official-train preprocessing.

## H001 Canonical Files

- `01_overview.md`: problem, hypothesis, feasibility, claim boundary, transition gate
- `02_method.md`: evidence schema, verifier, calibration, prediction-row join, evaluation protocol
- `03_data_baseline.md`: dataset/baseline layout, fixed scope, staged payload readiness
- `04_results.md`: mini/hardened metrics, controls, evidence lock, GT-based verifier evaluation
- `05_audit.md`: structured audit, visual sanity check, provenance and wording limits
- `06_second_source.md`: FROSS/Open3DSG source/runtime feasibility and claim boundary
- `07_experiment_spec.md`: scoped Docker-based main experiment spec, required metrics/tables/figures, acceptance criteria

## Active Direction

`CAND-001: Geometry-Grounded Open-Vocabulary Relation Graph`

Recommended formulation:

> Geometry-grounded verification and representation of open-vocabulary 3D scene graph relations.

Current hypothesis:

> H001: For geometry-checkable 3DSSG relation families, adding explicit 3D geometry evidence and verification to candidate semantic relation edges will reduce geometry-inconsistent relation predictions while preserving useful predicate/triplet recall.

Method contribution framing:

> Calibrated geometry-consistency evaluation and re-ranking framework for 3D scene graph relation predictions.

`CAND-003: Geometry-Aware Refinement of LLM/VLM Task Reasoning on 3DSG`

Recommended formulation:

> Geometry-grounded verification of LLM/VLM task reasoning over 3D scene graphs.

Current survey verdict:

> CAND-003은 `3DSG + LLM/VLM` 자체가 아니라, task output을 explicit 3D geometry constraints와 scene-graph evidence로 verify/refine하는 방향으로 좁혀야 한다.

## Key Files

- `AGENTS.md`: 에이전트 작업 규칙
- `TODO.md`: 현재 작업판
- `docs/index.md`: 현재 연구 상태 대시보드
- `docs/literature.md`: literature workflow와 작성 규칙
- `docs/hypothesis.md`: hypothesis workflow와 작성 규칙
- `literature/README.md`: field map, trend synthesis, cross-paper insights
- `literature/PAPER.md`: paper registry와 reading queue
- `literature/Contribution Candidates.md`: 기여 후보 목록
- `literature/CAND-001.md`: CAND-001 세부 문제 설정과 feasibility
- `literature/CAND-003.md`: CAND-003 literature survey와 feasibility boundary
- `hypothesis/README.md`: hypothesis index
- `hypothesis/CAND-001/README.md`: CAND-001 hypothesis index
- `hypothesis/CAND-001/H001_geometry-grounded-verification/`: active H001 canonical files, tools, and artifacts

## Working Principle

작게 시작한다. Full baseline reproduction보다 먼저, 3DSSG / 3RScan에서 geometry-checkable predicate subset을 대상으로 relation edge evidence, verifier, subtype-aware support/contact consistency signal을 확인한다.

현재 만든 experiment 구조:

- `experiments/H001_geom_reliability/`

아직 만들지 않는 구조:

- `paper/`
- `decisions/`
