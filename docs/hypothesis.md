# Hypothesis Workflow

Last updated: 2026-06-12

이 문서는 연구 후보를 검증 가능한 hypothesis로 바꾸는 에이전트 workflow와 작성 규칙을 정의한다. 실제 hypothesis 내용은 루트의 `hypothesis/` 폴더에 저장한다.

## Ownership

- `docs/hypothesis.md`는 hypothesis workflow rulebook이다.
- 실제 candidate/hypothesis 상태와 active gate는 `hypothesis/README.md`가 소유한다.
- CAND-001처럼 active hypothesis가 하나인 candidate는 별도 `hypothesis/CAND-001/README.md`를 만들지 않는다. Candidate-level summary는 `hypothesis/README.md`에 병합하고, 세부 내용은 H-folder canonical files에 둔다.
- Candidate 안에 여러 active hypotheses가 생기거나 candidate-level assumption/risk가 `hypothesis/README.md`를 과도하게 키울 때만 `hypothesis/CAND-<number>/README.md`를 만든다.

## Storage Rule

Hypothesis 관련 산출물은 루트의 `hypothesis/` 폴더에 저장한다.

- workflow와 작성 규칙: `docs/hypothesis.md`
- hypothesis/candidate index: `hypothesis/README.md`
- candidate별 hypothesis 묶음: `hypothesis/CAND-<number>/`
- 개별 hypothesis: `hypothesis/CAND-<number>/H<number>_<short-title>/`
- 작업 계획과 진행 상태: `TODO.md`

`docs/hypothesis.md`는 절차와 기준만 관리한다. 문제 정의, hypothesis, feasibility gate, method, data/baseline, result, audit, second-source boundary, experiment spec은 `hypothesis/` 아래에 기록한다.

## Entry Context

Hypothesis 작업을 시작하는 에이전트는 아래 순서로 읽는다.

1. `README.md`
2. `TODO.md`
3. `docs/index.md`
4. `docs/literature.md`
5. `docs/hypothesis.md`
6. `literature/CAND-001.md`
7. `hypothesis/README.md`
8. 대상 hypothesis folder의 canonical files

## Folder Convention

```text
hypothesis/
  README.md
  CAND-001/
    H001_geometry-grounded-verification/
      01_overview.md
      02_method.md
      03_data_baseline.md
      04_results.md
      05_audit.md
      06_second_source.md
      07_experiment_spec.md
      tools/
      artifacts/
```

폴더명 규칙:

- candidate 폴더는 `CAND-<number>` 형식을 사용한다.
- hypothesis 폴더는 `H<number>_<short-title>` 형식을 사용한다.
- 번호가 필요한 workflow 문서는 기존 순서를 유지하되 제목은 짧게 둔다.
- 중복된 stage 문서는 하나의 짧은 canonical 문서로 병합한다. 이미 병합한 오래된 번호 파일을 다시 만들지 않는다.
- 아직 실험을 시작하지 않았으면 `experiments/` 폴더를 만들지 않는다.
- 논문 본문용 실제 experiment 구현은 Docker 기반으로만 진행한다. Host-only 실행 결과는 paper experiment 결과로 승격하지 않는다.

## File Roles

### `hypothesis/README.md`

전체 hypothesis index와 active candidate summary를 관리한다.

포함할 내용:

- active candidate
- active hypothesis
- hypothesis registry
- current gate
- blocked items
- candidate-level assumptions and risks when only one active hypothesis exists

### Optional `hypothesis/CAND-<number>/README.md`

candidate 안에 여러 active hypotheses가 생기거나 candidate-level 상태가 root index를 과도하게 키울 때만 만든다. 단일 active H001처럼 root index에서 충분히 관리되는 경우 만들지 않는다.

### `01_overview.md` / Overview

문제 정의, hypothesis, feasibility, claim boundary, transition gate를 관리한다.

### `02_method.md` / Method

Geometry evidence schema, deterministic verifier, subtype-aware support/contact rule, calibration design, prediction-row geometry join, evaluation protocol을 관리한다.

### `03_data_baseline.md` / Data And Baseline

`3DSSG` / `3RScan` / `3DSSG_subset` / `VL-SAT` layout, fixed validation scope, staged payload readiness, baseline input counts를 관리한다.

### `04_results.md` / Results

H001-Mini result, hardened `VL-SAT` result, G3 controls, final scoped evidence lock, GT-positive/counterfactual verifier evaluation을 관리한다.

### `05_audit.md` / Audit

Structured audit, reduced visual sanity check, reviewer/provenance caveat, paper-claim audit wording limits를 관리한다.

### `06_second_source.md` / Second Source

FROSS and Open3DSG source/runtime feasibility, family coverage, checkpoint/runtime blockers, second-source claim boundary를 관리한다.

### `07_experiment_spec.md` / Experiment Spec

Scoped main experiment implementation spec과 Docker 기반 experiment transition gate를 관리한다. Fixed input counts, allowed claim, required metrics/tables/figures, acceptance criteria, Docker command reproducibility, proposed experiment root를 고정한다.

## Artifact Rules

Hypothesis smoke-test artifact는 hypothesis 폴더 내부에만 둔다.

- one-scan artifact root: `artifacts/one_scan/<scan-id>/`
- baseline layout checker artifact root: `artifacts/layout/<baseline-name>/`
- subset selection artifact root: `artifacts/subset/<subset-name>/`
- calibration artifact root: `artifacts/calibration/<split-name>/`
- prediction/evaluation artifact root: `artifacts/evaluation/<baseline-name>/<split-name>/`
- visual inspection and audit outputs use short names such as `labels.jsonl`, `summary.json`, `report.md`
- Open3DSG readiness outputs live under `artifacts/evaluation/open3dsg_ov/<stage-name>/`
- Large runtime files stay under ignored staged dataset roots such as `local_dataset/VLSAT_staged/` or `local_dataset/Open3DSG_staged/`
- 중간 산출물이 더 구체적인 review/report artifact로 대체되면 오래된 queue 파일은 유지하지 않는다.

## Workflow

Hypothesis 작업은 현재 아래 단계로 수행한다. 단계 수는 고정된 논문 구조가 아니라 agent가 결정을 잃지 않도록 돕는 연구 추적 구조다.

1. Problem
   - literature candidate를 실험 가능한 문제로 좁힌다.
   - "좋은 아이디어"가 아니라 "측정 가능한 오류와 개선 가능성"을 정의한다.

2. Hypothesis Formulation
   - 하나의 hypothesis는 한 번에 하나의 주장을 검증한다.
   - hypothesis는 반증 가능해야 한다.
   - success criteria와 falsification condition을 같이 적는다.

3. Feasibility
   - dataset, baseline, metric, implementation 경로를 확인한다.
   - gate를 통과하기 전에는 full experiment workflow를 만들지 않는다.
   - local dataset path나 sample payload가 없으면 dataset gate는 pending으로 둔다.

4. Method Contract
   - geometry evidence, verifier status, subtype policy, calibration target, prediction JSONL schema를 고정한다.
   - semantic score, geometry score, calibrated probability는 서로 다른 필드로 보존한다.
   - scan/subgraph/object-pair identity를 잃는 aggregate metric 파일만으로는 H001 prediction evaluation을 진행하지 않는다.

5. Dataset And Baseline Prep
   - baseline reproduction 전에 local dataset layout이 baseline code의 expected layout과 맞는지 확인한다.
   - source dataset 파일을 조용히 바꾸지 않는다.
   - large/runtime 파일은 ignored staged root에 두고, 작은 generated annotation과 manifest만 H001 artifact로 추적한다.
   - validation scan payload selection 전에는 full prediction-level run을 시작하지 않는다.

6. Calibration And Evaluation
   - calibration fitting 전에 scan-level split과 calibration row schema를 고정한다.
   - final prediction-level evaluation은 predictions, geometry join, and frozen calibrator output이 모두 존재할 때만 실행한다.
   - violation rate, consistency-filtered recall, recall retention, and calibration metrics를 분리한다.
   - 좋은 metric 결과도 ablation/control과 audit 전에는 final paper claim으로 승격하지 않는다.

7. Audit And Reportability
   - verifier decision audit queue는 hardened metric과 controls가 ready인 뒤 만든다.
   - Codex structured audit은 non-independent structured review로 기록할 수 있다.
   - Reference-aligned label을 Codex가 전사한 경우 provenance를 남기고 strictly blinded audit wording을 피한다.
   - GT-based verifier evaluation은 audit 부담을 줄이지만 visual sanity check를 완전히 대체하지 않는다.

8. Second Source Boundary
   - `VL-SAT` 하나만으로 baseline-agnostic claim을 하지 않는다.
   - FROSS, Open3DSG 같은 second-source track은 source contract, runtime blocker, adapter feasibility, family coverage를 분리해 기록한다.
   - Runtime artifact나 trusted checkpoint가 없으면 metric claim을 하지 않는다.

9. Experiment Transition
   - 사용자가 experiment phase 진입을 명시하면 `07_experiment_spec.md`가 제안한 scoped root부터 만든다.
   - paper-body experiment implementation은 Docker 기반으로만 진행한다.
   - Host-only outputs are debugging/smoke evidence only.

## Evidence Rules

- 문헌 근거는 `literature/`에 있는 paper card와 CAND 문서를 우선 참조한다.
- 새 논문이나 최신 코드 상태를 말할 때는 primary source를 확인한다.
- "Fact", "Inference", "User judgment needed"를 구분한다.
- hypothesis 문서는 논문 요약을 반복하지 않는다. 논문 근거는 짧게 연결하고, 검증 문제에 집중한다.
- 연구 목표와 방향성은 AI, ML, CV, Robotics top-tier journal/conference를 타겟으로 판단한다.

## Update Protocol

Hypothesis 문서를 갱신한 에이전트는 아래를 함께 확인한다.

- `TODO.md`: 현재 작업과 다음 작업 상태 갱신
- `docs/index.md`: active workflow와 current working file 갱신
- `hypothesis/README.md`: active hypothesis와 gate 상태 갱신
- optional `hypothesis/CAND-<number>/README.md`: 여러 active hypotheses가 있는 경우에만 candidate-level 상태 갱신
- 필요 시 `literature/CAND-<number>.md`: literature-derived feasibility 판단만 갱신

## Experiment Transition Rule

사용자가 hypothesis에서 experiment phase로 넘기겠다고 명시하면 아래 규칙을 따른다.

- 논문 본문용 실제 experiment 구현은 Docker 기반으로만 만든다.
- 첫 experiment root는 active hypothesis spec이 제안한 구조를 따른다.
- Dockerfile 또는 compose file, pinned dependency record, mounted dataset/cache path, command entrypoint, output manifest를 함께 만든다.
- `local_dataset/` 같은 큰 runtime/data root는 container mount로 사용하고 tracked experiment artifact로 복사하지 않는다.
- Host 환경에서 직접 패키지를 설치하거나 host-only command로 얻은 결과는 debugging/smoke evidence로만 취급한다.
- Paper table/report 결과는 Docker command로 재생성 가능해야 한다.

## Do Not Over-Structure

- `experiments/` 폴더는 active hypothesis spec이 명시하고 사용자가 experiment phase 진입을 요청한 뒤 만든다.
- `experiments/` 폴더를 만들 때는 Docker 재현성 구조를 같이 만든다.
- `paper/`는 현재 H001 manuscript workspace로 존재한다. 새 paper/venue subtree는 실제 필요가 생길 때만 만든다.
- `decisions/` 같은 새 top-level workflow root는 아직 만들지 않는다.
- 하나의 candidate에 여러 hypothesis를 미리 만들지 않는다.
- evaluation protocol과 subset strategy 전에는 full baseline reproduction plan을 확정하지 않는다.
- hypothesis 문서는 연구 방향을 좁히는 도구이지 최종 논문 초안이 아니다.

## Current Active Hypothesis

- Candidate: `CAND-001`
- Hypothesis: `H001 Geometry-grounded verification of open-vocabulary 3DSSG relations`
- Status: H001 hypothesis-stage evidence, scoped main experiment spec, Docker `VL-SAT` table/report reproduction, Docker-reproduced Open3DSG second-source metrics, clean v14 Open3DSG streaming raw-dump provenance, Open3DSG qualitative case inspection, Open3DSG paper caveat wording, and Qwen-VL third-source full-source inference/downstream validation are complete; active notes are consolidated into `01_overview.md` through `07_experiment_spec.md`; active experiment root is `experiments/H001_geom_reliability/`; current gate is paper polish, artifact-release hygiene, or an explicit decision on whether Qwen should remain optional appendix evidence or be promoted beyond third-source extension.
