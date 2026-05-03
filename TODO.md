# TODO

Last updated: 2026-05-03

이 파일은 에이전트가 다음 작업 계획과 진행 상태를 관리하는 루트 작업판이다. 자세한 문헌 조사 내용은 `literature/`에 기록하고, 이 파일에는 다음 행동과 상태만 남긴다.

## Current Phase

Parallel candidate tracking.

CAND-001은 hypothesis prep / verifier implementation 트랙이다. 현재까지의 literature pass는 CAND-001을 석사 연구 후보로 좁히는 데 충분하다. Hypothesis workflow와 H001 초안은 생성되었다. 2026-04-28 재확인 결과, `/home/yoohyun/research/local_dataset`에 3DSSG annotation, 3RScan metadata/download script, sample scan payload 1개가 존재한다. 2026-05-03 기준 Phase A/B/C, `h001-rules-v1`, visual inspection, support/contact subtype decision, `h001-verifier-v2` 구현 및 one-scan artifact 검증, probabilistic geometry consistency calibration 설계, violation/recall evaluation protocol, official `3DSSG_subset` 기반 multi-scan/subset strategy 결정, prediction-level baseline 선택, `vlsat_closed_set` prediction schema 정의, VL-SAT local layout compatibility check, H001-internal VL-SAT layout checker 구현/실행, generated annotation staging, faithful VL-SAT eval path decision, faithful layout prep staging policy, H001-Mini validation scan selection까지 완료했다. 첫 baseline은 `VL-SAT` / `vlsat_closed_set`이다. Checker 결과 default VL-SAT layout은 여전히 blocked이지만, annotation blocker 3개는 staging으로 해결했고 남은 blocker는 selected scan payload, aligned PLY와 `multi_view`다. Minimal eval path는 논문 방어력을 위해 faithful aligned PLY + faithful `multi_view`로 고정했다. Probabilistic calibration의 설계는 완료했지만, `p_geom_valid` 학습/보정/검증 구현은 아직 하지 않았다.

CAND-003은 literature survey 트랙이다. 2026-04-30 기준으로 LLM/VLM task reasoning on 3DSG, geometry-aware refinement, object placement/search/navigation decision evaluation을 primary source 중심으로 재확인했고, `literature/CAND-003.md`에 survey pass와 P1 intake 결과를 작성했다. P0 paper intake는 `RieMind`, `3D-VCD`, `SayPlan`, `SG-Nav`, `SCOUT/SymSearch`까지 완료했고, P1 paper intake는 `3DGraphLLM`, `3D-Mem`까지 완료했다. 다음 CAND-003 단계는 사용자가 hypothesis workflow 승격 여부를 판단하는 것이다.

## Active Objective

- CAND-001: `Geometry-Grounded Open-Vocabulary Relation Graph`의 smoke-test verifier를 확정하고 calibration/evaluation protocol로 확장한다.
- CAND-003: `Geometry-Aware Refinement of LLM/VLM Task Reasoning on 3DSG`의 literature evidence, novelty boundary, benchmark/metric feasibility와 P0/P1 paper intake를 정리했다. 다음에는 사용자가 P1 결과물을 보고 hypothesis workflow 승격 여부를 판단한다.

## Now

### CAND-001

- [ ] VL-SAT faithful staging script 구현: staged root, selected scan files, references/rescans, aligned PLY prep

### CAND-003

- No active task.

## Next

### CAND-001

- [ ] VL-SAT `multi_view` generation route 구현: selected validation scans 대상
- [ ] Calibration table schema와 counterfactual negative export 설계
- [ ] Probabilistic calibration smoke implementation: `p_geom_valid` fitting/evaluation
- [ ] Relative horizontal coordinate-frame validation은 support/contact 보완 이후 필요 시 진행

### CAND-003

- [ ] CAND-003 hypothesis workflow 승격 여부 사용자 판단 대기

## Recently Completed

- [x] H001-Mini validation scan payload selection 완료: 8 validation scans, 56 subgraphs, support/contact 224, `23_mini.md`, `tools/select_mini.py`, `artifacts/subset/h001_mini/`
- [x] VL-SAT faithful layout prep staging policy 작성: `22_prep.md`
- [x] VL-SAT minimal eval path decision: faithful aligned PLY + faithful `multi_view`, `21_eval_path.md`
- [x] VL-SAT generated annotation files staging 완료: `tools/prep_layout.py`, `generated/3DSSG_subset/relations.txt`, `train_scans.txt`, `validation_scans.txt`
- [x] H001-internal VL-SAT layout checker 구현 및 실행: `tools/check_layout.py`, `artifacts/layout/vlsat/report.md`
- [x] H001 VL-SAT local layout compatibility check: `20_layout.md`
- [x] H001 `vlsat_closed_set` prediction JSONL schema 정의: `19_schema.md`
- [x] H001 prediction-level baseline 후보 선택: `VL-SAT` / `vlsat_closed_set`, `18_baseline.md`
- [x] H001 official `3DSSG_subset` 파일 검증 및 multi-scan/subset strategy 업데이트: `17_subset.md`
- [x] H001 violation/recall evaluation protocol 설계: `16_evaluation.md`
- [x] H001 probabilistic geometry consistency calibration 설계: `15_calibration.md` (`p_geom_valid` 구현/학습은 아직 미완료)
- [x] H001 `h001-verifier-v2` one-scan 실행 및 artifact 검증: 772 edges, support/contact 31 satisfied / 1 uncertain / 0 violated, validation passed
- [x] H001 `tools/apply_verifier_v2.py` 구현: subtype-aware support/contact verifier
- [x] H001 `14_verifier_v2.md` 작성: subtype-aware verifier contract
- [x] H001 stage 문서 병합: `07_execution_path.md`~`12_rules_v1_contract.md` 내용을 `07_stage_log.md`로 통합
- [x] H001 support/contact subtype decision 작성: `hypothesis/CAND-001/H001_geometry-grounded-verification/13_subtypes.md`
- [x] H001 visual inspection label 작성: `visual_inspection/labels.jsonl`, `visual_inspection/report.md`, `visual_inspection/projections.png`
- [x] `AGENTS.md` 파일명 원칙 추가: 직관적이고 핵심 단어 기반으로 짧게 작성
- [x] H001 viewable point subset artifact 생성: `visual_inspection/` 아래 7개 colored PLY, `summary.json`, `README.md`, label template
- [x] H001 visual inspection artifact export 도구 구현: `hypothesis/CAND-001/H001_geometry-grounded-verification/tools/export_visual_inspection_points.py`
- [x] H001 minimal visual inspection pass 준비: `visual_inspection_manifest.json`, `visual_inspection_queue.jsonl`
- [x] H001 `v1_review_queue.jsonl` triage 작성: `v1_review_report.md`, `v1_review_labels.jsonl`
- [x] v1 review queue 결과 기반 visual inspection 필요 여부 결정: 필요
- [x] v1 review queue 결과 기반 multi-scan replication 필요 여부 결정: visual inspection 전까지 보류
- [x] H001 tools 파일명 단순화: `export_evidence.py`, `apply_rules_v0.py`, `export_point_support.py`, `apply_rules_v1.py`
- [x] H001 `tools/apply_rules_v1.py` 구현
- [x] H001 `h001-rules-v1` 실행 및 artifact 검증: 772 edges, support/contact 19/1/12, validation passed
- [x] H001 `h001-rules-v1` hypothesis-internal smoke-test 구현 범위와 contract 작성: `07_stage_log.md`로 병합
- [x] H001 point-aware support/contact rule revision decision 작성: `07_stage_log.md`로 병합
- [x] H001 artifact 비교 리포트 작성: `hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/one_scan/f62fd5fd-9a3f-2f44-883a-1e5cf819608e/comparison_report.md`
- [x] H001 artifact 파일명 단순화: `one_scan/`, `edges.jsonl`, `decisions.jsonl`, `point_comparison.jsonl` 등으로 정리
- [x] H001 artifact cleanup: superseded Phase A `manual_inspection_queue.jsonl` 제거
- [x] `AGENTS.md` hypothesis artifact convention 업데이트
- [x] CAND-003 P1 intake 결과 기반 scope decision note 작성: `literature/CAND-003.md`
- [x] CAND-003 P1 paper intake: 3D-Mem, `literature/2025_cvpr_3d-mem/`
- [x] CAND-003 P1 paper intake: 3DGraphLLM, `literature/2025_iccv_3dgraphllm/`
- [x] H001 md 파일명 제목 업데이트 및 stage 문서 병합
- [x] H001 hypothesis 문서 정리: 10개 md 제목 단순화, 07-10 stage summary로 압축, 중복 run contract 제거
- [x] CAND-003 P0 paper intake: SCOUT / SymSearch, `literature/2026_arxiv_scout/`
- [x] CAND-003 P0 paper intake: SG-Nav, `literature/2024_neurips_sg-nav/`
- [x] CAND-003 synthesis 업데이트: SG-Nav / SCOUT search-navigation boundary 반영
- [x] CAND-003 P0 paper intake: SayPlan, `literature/2023_corl_sayplan/`
- [x] CAND-003 P0 paper intake: 3D-VCD, `literature/2026_cvpr_3d-vcd/`
- [x] CAND-003 P0 paper intake: RieMind, `literature/2026_arxiv_riemind/`
- [x] CAND-003 synthesis 업데이트: `literature/CAND-003.md`, `literature/README.md`, `literature/PAPER.md`, `literature/Contribution Candidates.md`
- [x] CAND-003 관련 root dashboard 업데이트: `README.md`, `docs/index.md`
- [x] CAND-003 관련 `literature/PAPER.md`, `literature/README.md`, `literature/Contribution Candidates.md` 업데이트
- [x] CAND-003 paper intake 우선순위 확정: RieMind, 3D-VCD, SayPlan, SG-Nav, SCOUT/SymSearch 순
- [x] CAND-003 seed evidence scan: FirePlace, RieMind, 3D-VCD, SayPlan, SG-Nav, SCOUT, 3DGraphLLM, 3D-Mem, MSQA/MSNN, 3D-GRAND, OVSG, ConceptGraphs, HOV-SG 계열 확인
- [x] `literature/CAND-003.md` 생성
- [x] `ply_points_v1` support/contact evidence extractor 구현 및 실행: `hypothesis/CAND-001/H001_geometry-grounded-verification/tools/export_point_support.py`
- [x] `ply_points_v1` output sanity check: 32 support/contact edges, 19 point_satisfied, floor recovery 13/16
- [x] `ply_points_v1` point support evidence 정리: `07_stage_log.md`로 병합
- [x] Verifier manual review completed through `relative_horizontal`: `review_report.md`, `review_labels.jsonl`
- [x] Support/contact 실패 원인 분류: OBB-derived AABB artifact 가능성이 높고 point/local support evidence 필요
- [x] `ply_points_v1` 또는 floor-plane-specific evidence 필요 여부 결정: support/contact 보완에 필요
- [x] One-scan verifier output sanity check: 772 decisions, validation passed, primary denominator 129
- [x] `h001-rules-v0` verifier script 구현 및 실행: `hypothesis/CAND-001/H001_geometry-grounded-verification/tools/apply_rules_v0.py`
- [x] `h001-rules-v0` rule application 정리: `07_stage_log.md`로 병합
- [x] Phase A evidence export artifacts 생성: `hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/one_scan/f62fd5fd-9a3f-2f44-883a-1e5cf819608e/`
- [x] One-scan geometry evidence export output 검증: 772 edges exported, validation passed, 0 errors
- [x] H001-local evidence export script 구현: `hypothesis/CAND-001/H001_geometry-grounded-verification/tools/export_evidence.py`
- [x] H001 design gap patch: phase 구분, predicate canonical mapping, geometry-source validation, stale next-action 정리
- [x] Evidence export 정리: `07_stage_log.md`로 병합
- [x] One-scan verifier sanity check 구현 위치와 출력 경로 결정
- [x] One-scan verifier report schema 작성
- [x] First executable path 결정: one-scan verifier sanity check first, `3DSSG_subset` strategy deferred
- [x] Rule verifier 정리: `06_rule_verifier.md`
- [x] 3RScan sample payload 확보/검증: `f62fd5fd-9a3f-2f44-883a-1e5cf819608e`
- [x] Sample payload files 확인: `labels.instances.annotated.v2.ply`, `semseg.v2.json`, `mesh.refined.0.010000.segs.v2.json`
- [x] Sample scan annotation 연결 확인: 3DSSG objects 60개와 `semseg.v2.json` object ids 60개 일치
- [x] `/home/yoohyun/research/local_dataset` 재확인: 3DSSG annotation과 3RScan metadata 존재 확인
- [x] 3RScan download script 확인: duplicate hash 일치, py_compile 통과, `--help` 동작 확인
- [x] `03_feasibility.md` 업데이트: dataset gate를 partial pass로 변경
- [x] Root `README.md` 업데이트: CAND-001 hypothesis prep 상태 반영
- [x] Earlier local dataset validation attempt: searched expected paths before `local_dataset` was provided; dataset root not found
- [x] `03_feasibility.md` 업데이트: local dataset validation attempt 결과 반영
- [x] Evidence schema 정리: `05_evidence_schema.md`
- [x] `docs/hypothesis.md` workflow 설계
- [x] `hypothesis/` root folder 생성
- [x] CAND-001 hypothesis folder 생성: `hypothesis/CAND-001/`
- [x] H001 초안 작성: `hypothesis/CAND-001/H001_geometry-grounded-verification/`
- [x] First experiment shape 정리: ground-truth relation verifier sanity check 중심
- [x] 3DSSG predicate subset 초안 확정: support/contact, proximity, relative-position 중심
- [x] CAND-001 synthesis pass: edge schema, predicate subset, baseline table, remaining gap 정리
- [x] CAND-001 baseline code feasibility check: SGGpoint, VL-SAT, Open3DSG, CCL-3DSGG
- [x] CAND-001 dataset access route and layout feasibility check: 3DSSG / 3RScan
- [x] 3D Spatial Multimodal Knowledge Accumulation paper intake: `literature/2023_cvpr_smka/`
- [x] Open-Vocabulary Octree-Graph paper intake: `literature/2025_iccv_octree-graph/`
- [x] Open-Vocabulary Functional 3D Scene Graphs paper intake: `literature/2025_cvpr_openfungraph/`
- [x] VL-SAT paper intake: `literature/2023_cvpr_vl-sat/`
- [x] SGGpoint paper intake: `literature/2021_cvpr_sggpoint/`
- [x] Open3DSG paper intake: `literature/2024_cvpr_open3dsg/`
- [x] SGRec3D paper intake: `literature/2024_wacv_sgrec3d/`
- [x] FirePlace paper intake: `literature/2025_cvpr_fireplace/`
- [x] CAND-001 근거 보강 조사: AI/ML/CV/Robotics top-tier 중심으로 추가 문헌 확인 및 registry 업데이트
- [x] CAND-001 feasibility와 evidence corpus 업데이트
- [x] Field Survey Pass 수행: 최근 2-3년 3D Scene Graph 연구 흐름 조사
- [x] P0 reading queue 확정
- [x] closed-set 3DSG 기본 problem setting 정리
- [x] open-vocabulary / open-world 3DSG 대표 논문 paper card 작성
- [x] LLM/VLM + 3D scene reasoning 대표 논문 paper card 작성
- [x] robotics / embodied AI 방향의 3DSG 활용 정리

## Pending / Blocked

- [ ] Multi-scan evaluation is blocked until selected H001-Mini 3RScan scan payloads are downloaded and staged.
- [ ] Calibration fitting is blocked until calibration table schema and counterfactual negatives exist.
- [ ] Do not create `experiments/`, `paper/`, or `decisions/` folders yet.
- [ ] Do not start full baseline reproduction before local `VL-SAT` layout prep and minimal eval path are fixed.

## Potential Follow-up

현재 활성 TODO는 아니다. CAND-001 workflow가 안정되면 아래를 queue로 승격한다.

- VL-SAT small-subset eval feasibility check
- Open3DSG inference-only feasibility check
- Additional 3RScan sample payload validation
- Calibration table export smoke check
- OVSG / ConceptGraphs intake for robotics motivation

## Rules

- 작업을 시작할 때 이 파일을 먼저 확인한다.
- 작업 중 새 task가 생기면 이 파일에 추가한다.
- 완료한 task는 체크하고, 필요한 상세 내용은 `literature/` 또는 해당 workflow 문서에 기록한다.
- 이 파일은 긴 설명을 담지 않는다. 계획, 상태, 다음 행동만 관리한다.
