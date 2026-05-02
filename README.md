# Research Workspace

이 저장소는 3D Scene Graph 석사 연구를 위한 작업 공간이다.

현재 단계는 CAND-001 hypothesis prep과 CAND-003 literature survey를 병렬로 추적하는 단계다. CAND-001은 `Geometry-Grounded Open-Vocabulary Relation Graph` 방향에서 one-scan verifier smoke test, visual inspection, support/contact subtype decision, subtype-aware verifier v2 구현 및 검증, probabilistic calibration 설계, violation/recall evaluation protocol, official `3DSSG_subset` 기반 multi-scan/subset strategy 결정, prediction-level baseline 선택, `vlsat_closed_set` prediction schema 정의, VL-SAT local layout compatibility check, H001-internal VL-SAT layout checker 구현/실행까지 진행했다. 첫 prediction baseline은 `VL-SAT` / `vlsat_closed_set`으로 정했다. Probabilistic calibration은 설계 단계까지이며, `p_geom_valid` 구현/학습/검증은 아직 시작하지 않았다. CAND-003은 `Geometry-Aware Refinement of LLM/VLM Task Reasoning on 3DSG`의 근거 문헌과 feasibility boundary를 2026-04-30 P1 intake까지 정리했다.

## Current Focus

- CAND-001 hypothesis workflow 관리
- H001 problem definition / hypothesis / feasibility gate 정리
- 3DSSG / 3RScan local dataset validation: annotation/metadata 확인 완료, sample scan payload 1개 검증 완료
- relation verifier rule baseline 설계 완료
- first executable path 결정 완료: one-scan verifier sanity check first
- one-scan geometry evidence export 완료
- H001 design gap patch 완료: phase 구분, canonical mapping, geometry-source validation 정리
- Phase A evidence export 완료: 772 relation edges exported, validation passed
- `h001-rules-v0` verifier 적용 계획 작성 완료
- Phase B verifier smoke test 완료: 772 verifier decisions, primary metric denominator 129
- Verifier manual review 완료: support/contact는 point/local support evidence 필요, horizontal은 diagnostic 유지
- `ply_points_v1` support/contact smoke test 계획 작성 완료
- `ply_points_v1` support/contact extractor 실행 완료: 32 support/contact records, 19 point-satisfied, floor recovery 13/16
- OBB-only vs point/local-surface comparison report 작성 완료
- Point-aware support/contact rule revision decision 작성 완료
- `h001-rules-v1` support/contact contract 작성 완료
- `h001-rules-v1` implementation scope 결정 완료
- `h001-rules-v1` smoke test 실행 완료: 772 edges preserved, support/contact 19 satisfied / 1 uncertain / 12 violated
- `v1_review_queue.jsonl` triage 완료: floor/legged support, soft pillow/sofa support, counter-surface ambiguity로 분류
- visual inspection 완료: 7 representative cases, 6 visually plausible, 1 geometry-quality uncertain
- support/contact subtype decision 완료: `legged_floor_support`, `soft_support_contact`, `rigid_object_on_furniture`, `geometry_quality_uncertain`
- `14_verifier_v2.md` 작성 완료: subtype-aware verifier contract
- `h001-verifier-v2` 구현 및 one-scan 검증 완료: 772 edges preserved, support/contact 31 satisfied / 1 uncertain / 0 violated
- `15_calibration.md` 작성 완료: `consistency_score`를 calibrated probability로 확장하기 위한 target, label source, counterfactual negative, metric 설계. 실제 `p_geom_valid` fitting/evaluation은 아직 미완료
- `16_evaluation.md` 작성 완료: prediction-level violation/recall protocol, benchmark contribution boundary, multi-scan generalization 조건 설계
- `17_subset.md` 작성 완료: official `3DSSG_subset` 기반 H001 train/validation subgraph strategy 결정
- `18_baseline.md` 작성 완료: 첫 prediction-level baseline을 `VL-SAT` / `vlsat_closed_set`으로 선택
- `19_schema.md` 작성 완료: `vlsat_closed_set` prediction JSONL / ground-truth JSONL / manifest contract 정의
- `20_layout.md` 작성 완료: local `3DSSG_subset` / 3RScan layout과 `VL-SAT` expected layout compatibility 확인
- `tools/check_layout.py` 구현 및 실행 완료: default VL-SAT layout blocked, H001 one-scan geometry-ready scan 1개 확인
- stage 문서 정리 완료: 07~12 상세 문서를 `07_stage_log.md`로 병합
- full baseline reproduction 전에 geometry evidence와 verifier의 최소 신호 확인
- CAND-003 literature survey pass 완료: 3DSG+LLM/VLM task reasoning, geometry-aware refinement, hallucination mitigation, object search/navigation benchmark 축 정리
- CAND-003 P0 paper intake 완료: RieMind, 3D-VCD, SayPlan, SG-Nav, SCOUT/SymSearch
- CAND-003 P1 paper intake 완료: 3DGraphLLM, 3D-Mem
- CAND-003 first cut recommendation: full embodied robot system이 아니라 offline spatial QA / graph query verification부터 시작

## Active Direction

`CAND-001: Geometry-Grounded Open-Vocabulary Relation Graph`

Recommended formulation:

> Geometry-grounded verification and representation of open-vocabulary 3D scene graph relations.

Current hypothesis:

> H001: For geometry-checkable 3DSSG relation families, adding explicit 3D geometry evidence and verification to candidate semantic relation edges will reduce geometry-inconsistent relation predictions while preserving useful predicate/triplet recall.

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
- `literature/<paper-folder>/`: 논문별 상세 정리
- `hypothesis/README.md`: hypothesis index
- `hypothesis/CAND-001/README.md`: CAND-001 hypothesis index
- `hypothesis/CAND-001/H001_geometry-grounded-verification/`: active H001 문서

## Active Workflow

1. Literature evidence is stored under `literature/`.
2. Hypothesis workflow rules are stored in `docs/hypothesis.md`.
3. Actual hypothesis content is stored under `hypothesis/`.
4. Experiments are not created yet.

## Current Blocker

Local dataset validation is passed for one sample scan. The current CAND-001 gate is deciding the minimal `VL-SAT` eval path.

`/home/yoohyun/research/local_dataset` contains 3DSSG annotation files, official `3DSSG_subset` files, 3RScan metadata/split files, the 3RScan download script, and one validated sample scan payload.

Confirmed local files include:

- `local_dataset/3DSSG/objects.json`
- `local_dataset/3DSSG/relationships.json`
- `local_dataset/3DSSG/classes.txt`
- `local_dataset/3DSSG/relationships.txt`
- `local_dataset/3DSSG_subset/relationships.json`
- `local_dataset/3DSSG_subset/relationships_train.json`
- `local_dataset/3DSSG_subset/relationships_validation.json`
- `local_dataset/3DSSG_subset/classes.txt`
- `local_dataset/3DSSG_subset/relationships.txt`
- `local_dataset/3RScan/files/3RScan.json`
- `local_dataset/3RScan/files/release_scans.txt`
- `local_dataset/3RScan/files/train_scans.full.txt`
- `local_dataset/3RScan/files/val_scans.full.txt`
- `local_dataset/3RScan/download_3rscan.py`

Validated sample scan:

- `f62fd5fd-9a3f-2f44-883a-1e5cf819608e`

Validated sample files:

- `local_dataset/3RScan/scans/<scan_id>/labels.instances.annotated.v2.ply`
- `local_dataset/3RScan/scans/<scan_id>/semseg.v2.json`
- `local_dataset/3RScan/scans/<scan_id>/mesh.refined.0.010000.segs.v2.json`

Current `VL-SAT` layout finding:

- `3DSSG_subset` JSON annotation files are present.
- `relations.txt`, `train_scans.txt`, and `validation_scans.txt` are missing.
- local 3RScan files are under `local_dataset/3RScan/scans/<scan_id>/`, while `VL-SAT` expects a configured 3RScan root with scan folders directly below it.
- aligned PLY files and `multi_view/` features are missing.
- checker output is stored at `hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/layout/vlsat/`.
- full baseline reproduction remains blocked until layout prep and a minimal eval path are fixed.

Subset decision:

- use official `3DSSG_subset` as the primary split and relation-subgraph source;
- use full 3DSSG annotation only for coverage checks, compatibility checks, and counterfactual negative construction.

## Working Principle

작게 시작한다. Full baseline reproduction보다 먼저, 3DSSG / 3RScan에서 geometry-checkable predicate subset을 대상으로 relation edge evidence, verifier, subtype-aware support/contact consistency signal을 확인한다.

아직 만들지 않는 구조:

- `experiments/`
- `paper/`
- `decisions/`
