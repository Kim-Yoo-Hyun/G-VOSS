# Hypothesis Workflow

Last updated: 2026-05-03

이 문서는 연구 후보를 검증 가능한 hypothesis로 바꾸는 에이전트 workflow와 작성 규칙을 정의한다. 실제 hypothesis 내용은 루트의 `hypothesis/` 폴더에 저장한다.

## Storage Rule

Hypothesis 관련 산출물은 루트의 `hypothesis/` 폴더에 저장한다.

- workflow와 작성 규칙: `docs/hypothesis.md`
- hypothesis index: `hypothesis/README.md`
- candidate별 hypothesis 묶음: `hypothesis/CAND-<number>/`
- 개별 hypothesis: `hypothesis/CAND-<number>/H<number>_<short-title>/`
- 작업 계획과 진행 상태: `TODO.md`

`docs/hypothesis.md`는 절차와 기준만 관리한다. 문제 정의, hypothesis, feasibility gate, first experiment shape는 `hypothesis/` 아래에 기록한다.

## Entry Context

Hypothesis 작업을 시작하는 에이전트는 아래 순서로 읽는다.

1. `README.md`
2. `TODO.md`
3. `docs/index.md`
4. `docs/literature.md`
5. `docs/hypothesis.md`
6. `literature/CAND-001.md`
7. `hypothesis/README.md`
8. 대상 hypothesis 폴더의 `README.md`

## Folder Convention

```text
hypothesis/
  README.md
  CAND-001/
    README.md
    H001_geometry-grounded-verification/
      01_problem.md
      02_hypothesis.md
      03_feasibility.md
      04_experiment.md
      05_evidence_schema.md
      06_rule_verifier.md
      07_stage_log.md
      13_subtypes.md
      14_verifier_v2.md
      15_calibration.md
      16_evaluation.md
      17_subset.md
      18_baseline.md
      19_schema.md
      20_layout.md
      21_eval_path.md
      tools/check_layout.py
      tools/prep_layout.py
```

폴더명 규칙:

- candidate 폴더는 `CAND-<number>` 형식을 사용한다.
- hypothesis 폴더는 `H<number>_<short-title>` 형식을 사용한다.
- 파일은 읽는 순서가 드러나도록 `01_`, `02_` prefix를 사용한다.
- 오래된 stage별 문서가 중복되면 하나의 짧은 stage log로 합친다. 이미 병합된 번호를 다시 만들지 않는다.
- 아직 실험을 시작하지 않았으면 `experiments/` 폴더를 만들지 않는다.
- one-scan smoke-test artifact는 `artifacts/one_scan/<scan-id>/` 아래에 둔다.
- baseline layout checker artifact는 `artifacts/layout/<baseline-name>/` 아래에 둔다.
- artifact 파일명은 짧은 역할명으로 쓴다. 예: `edges.jsonl`, `decisions.jsonl`, `review_report.md`, `point_comparison.jsonl`, `comparison_report.md`.
- 중간 queue가 더 구체적인 review artifact로 대체되면 오래된 queue 파일은 유지하지 않는다.

## File Roles

### `hypothesis/README.md`

전체 hypothesis index를 관리한다.

포함할 내용:

- active candidate
- active hypothesis
- hypothesis registry
- next validation gate
- blocked items

### `hypothesis/CAND-<number>/README.md`

candidate 단위의 hypothesis 묶음을 관리한다.

포함할 내용:

- source candidate
- research direction
- active hypothesis list
- candidate-level assumptions
- candidate-level open risks

### `01_problem.md` / Problem

문제를 검증 가능한 형태로 좁힌다.

포함할 내용:

- problem statement
- what this is not
- current evidence
- target users / research value
- assumptions
- out-of-scope

### `02_hypothesis.md` / Hypothesis

검증 가능한 hypothesis를 작성한다.

포함할 내용:

- hypothesis statement
- independent variable
- dependent variables
- expected effect
- falsification condition
- alternative explanations
- success criteria

### `03_feasibility.md` / Feasibility

실험으로 넘어가기 전 gate를 관리한다.

포함할 내용:

- dataset gate
- baseline gate
- implementation gate
- metric gate
- go / no-go decision
- what to check next

### `04_experiment.md` / Experiment

첫 실험의 형태를 설계한다. 실제 실험 로그나 결과는 여기에 길게 쓰지 않는다.

포함할 내용:

- minimal viable experiment
- input / output
- predicate subset
- geometry evidence fields
- verifier baseline
- metrics
- expected failure modes

### `05_evidence_schema.md` / Evidence Schema

relation-edge geometry evidence schema를 기록한다.

포함할 내용:

- input assumptions
- output edge record schema
- predicate family mapping
- evidence fields
- missing data policy
- quality checks
- active evidence sources

### `06_rule_verifier.md` / Rule Verifier

geometry evidence를 사용해 relation edge를 규칙 기반으로 검증하는 baseline과 현재 point-aware support/contact 방향을 기록한다.

포함할 내용:

- verifier role
- predicate family scope
- verification status schema
- rule constraints
- threshold policy
- geometry score
- reporting format
- open decisions

### `07_stage_log.md` / Stage Log

실행 순서, stage별 결과, decision trail을 짧게 합쳐 기록한다.

포함할 내용:

- merged source files if any
- scan and artifact root
- Phase A/B/C/D summaries
- visual inspection summary
- current decision and next gate

### `13_subtypes.md` / Subtypes

Visual inspection 기반 support/contact subtype decision을 기록한다.

포함할 내용:

- why one hard support/contact rule is insufficient
- visual inspection evidence
- subtype set
- subtype-specific evidence needs
- probabilistic/soft score direction
- evaluation implication

### `14_verifier_v2.md` / Verifier v2

Subtype-aware verifier contract와 one-scan result summary를 기록한다.

포함할 내용:

- input/output artifact contract
- subtype assignment policy
- subtype-specific evidence fields
- soft consistency score contract
- status mapping
- reason codes
- metrics and validation checks
- implementation scope

### `15_calibration.md` / Calibration

Rule-based consistency score를 probabilistic geometry validity score로 확장하는 설계를 기록한다.

포함할 내용:

- calibration target
- label source
- counterfactual negative construction
- feature set
- calibration model stages
- calibration metrics
- scan-level split policy
- acceptance criteria

### `16_evaluation.md` / Evaluation

Prediction-level violation/recall evaluation protocol과 benchmark contribution boundary를 기록한다.

포함할 내용:

- compared conditions
- prediction-level inputs
- predicate scope
- evaluation levels
- ranking policies
- core metrics
- reporting slices
- baseline choices
- benchmark artifact boundary
- generalization evidence

### `17_subset.md` / Subset

Multi-scan replication 또는 `3DSSG_subset` 전략 결정을 기록한다.

포함할 내용:

- local dataset availability
- official split usage
- derived subset policy
- train/dev/test scan-level split policy
- candidate scan criteria
- required scan payloads
- leakage controls

### `18_baseline.md` / Baseline

Prediction-level baseline 선택과 baseline adapter의 다음 gate를 기록한다.

포함할 내용:

- selected baseline
- selection criteria
- candidate comparison
- expected prediction fields
- adapter policy
- fallback policy

### `19_schema.md` / Schema

Prediction-level baseline output을 H001 verifier/evaluation이 소비할 수 있는 JSONL 계약으로 정의한다.

포함할 내용:

- prediction unit
- prediction JSONL fields
- ground-truth JSONL fields
- manifest fields
- predicate index policy
- adapter join policy
- validation checks

### `20_layout.md` / Layout

Prediction-level baseline 실행 전에 local dataset layout과 baseline expected layout의 차이를 기록한다.

포함할 내용:

- checked baseline source
- local annotation file compatibility
- local 3RScan payload compatibility
- missing files and path mismatches
- faithful route vs plumbing route decision boundary
- next layout prep action

### `21_eval_path.md` / Eval Path

Prediction-level baseline의 reportable route를 결정한다.

포함할 내용:

- faithful route vs plumbing route decision
- top-tier paper defensibility rationale
- aligned PLY route
- `multi_view` route
- validation scan requirement
- non-reportable plumbing boundary

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

4. Experiment
   - 최소 실험을 정의한다.
   - baseline reproduction보다 verifier sanity check를 먼저 둘 수 있다.
   - 실험 결과가 생기면 별도 experiment workflow를 만들지 판단한다.

5. Rule Verifier
   - geometry evidence를 해석하는 가장 단순한 deterministic baseline을 정의한다.
   - 학습 모델이 아니라 sanity check이므로 threshold와 rule version을 명시한다.
   - unsupported relation을 실패로 세지 않는다.

6. Stage Log
   - 실행한 smoke-test stage와 결과를 한 파일에 짧게 남긴다.
   - stage별 오래된 contract/decision 문서가 반복되면 `07_stage_log.md`로 병합한다.
   - artifact 상세 내용은 artifact 폴더에 두고, hypothesis 문서에는 결론과 다음 gate만 남긴다.

7. Subtype Decision
   - visual/manual inspection 결과가 쌓이면 relation family를 subtype으로 나눌지 결정한다.
   - 단순 threshold tuning인지, evidence model 자체를 바꿔야 하는지 구분한다.

8. Verifier Contract
   - 구현 전에 next verifier의 입력, 출력, status mapping, score, validation을 고정한다.
   - contract 없이 바로 script를 만들지 않는다.
   - implementation scope와 out-of-scope를 명시한다.

9. Calibration Design
   - rule score를 calibrated probability로 주장하지 않는다.
   - `p_geom_valid` target, label source, negative construction, scan split, metric을 분리해 정의한다.
   - calibration 구현 전에 violation/recall evaluation protocol을 먼저 작성한다.

10. Evaluation Protocol
   - prediction-level baseline에 verifier/recalibration을 적용하는 비교 조건을 정의한다.
   - violation rate, consistency-filtered recall, recall retention, calibration metric을 분리한다.
   - benchmark contribution은 새 dataset claim이 아니라 3DSSG/3RScan 위의 geometry-consistency evaluation layer로 제한한다.

11. Subset Strategy
   - calibration과 prediction-level evaluation 전에 scan-level split 전략을 고정한다.
   - official `3DSSG_subset`이 있으면 primary split/relation-subgraph source로 사용한다.
   - official subset이 없을 때만 full annotation과 official 3RScan train/val split에서 H001-controlled subset을 만든다.
   - split strategy만으로 artifact directory를 만들지 않는다.

12. Baseline Selection
   - prediction-level evaluation 전에 첫 baseline과 adapter 방향을 고정한다.
   - baseline 선택은 SOTA 여부보다 prediction output 확보 가능성과 official subset 호환성을 우선한다.
   - full training이나 experiment artifact 생성은 prediction schema가 고정된 뒤에 한다.

13. Prediction Schema
   - baseline별 raw output을 직접 evaluator에 물리지 않고, H001 prediction JSONL로 먼저 정규화한다.
   - semantic score, geometry score, calibrated probability는 서로 다른 필드로 보존한다.
   - scan/subgraph/object-pair identity를 잃는 aggregate metric 파일만으로는 H001 prediction evaluation을 진행하지 않는다.

14. Layout Compatibility
   - baseline reproduction 전에 local dataset layout이 baseline code의 expected layout과 맞는지 확인한다.
   - source dataset 파일을 조용히 바꾸지 않는다.
   - missing file, path mismatch, faithful route, plumbing-only route를 분리해서 기록한다.
   - checker/prep script는 `tools/` 아래에 두고, `summary.json`, `prep_manifest.json`, `generated_manifest.json`, `report.md`를 `artifacts/layout/<baseline-name>/`에 남긴다.
   - full baseline 실행은 layout prep과 minimal eval path가 고정된 뒤로 미룬다.

15. Eval Path Decision
   - reportable baseline과 non-reportable plumbing check를 분리한다.
   - top-tier paper claim에 쓰는 baseline은 가능한 official assumption을 유지한다.
   - baseline deviation이 필요하면 main result가 아니라 adapter smoke test나 ablation으로만 둔다.

## Evidence Rules

- 문헌 근거는 `literature/`에 있는 paper card와 CAND 문서를 우선 참조한다.
- 새 논문이나 최신 코드 상태를 말할 때는 primary source를 확인한다.
- "Fact", "Inference", "User judgment needed"를 구분한다.
- hypothesis 문서는 논문 요약을 반복하지 않는다. 논문 근거는 짧게 연결하고, 검증 문제에 집중한다.

## Update Protocol

Hypothesis 문서를 갱신한 에이전트는 아래를 함께 확인한다.

- `TODO.md`: 현재 작업과 다음 작업 상태 갱신
- `docs/index.md`: active workflow와 current working file 갱신
- `hypothesis/README.md`: active hypothesis와 gate 상태 갱신
- `hypothesis/CAND-<number>/README.md`: candidate-level 상태 갱신
- 필요 시 `literature/CAND-<number>.md`: literature-derived feasibility 판단만 갱신

## Do Not Over-Structure

- 아직 `experiments/`, `paper/`, `decisions/` 폴더를 만들지 않는다.
- 하나의 candidate에 여러 hypothesis를 미리 만들지 않는다.
- evaluation protocol과 subset strategy 전에는 full baseline reproduction plan을 확정하지 않는다.
- hypothesis 문서는 연구 방향을 좁히는 도구이지 최종 논문 초안이 아니다.

## Current Active Hypothesis

- Candidate: `CAND-001`
- Hypothesis: `H001 Geometry-grounded verification of open-vocabulary 3DSSG relations`
- Status: Drafted; one-scan Phase A/B/C, `h001-rules-v1`, visual inspection, support/contact subtype decision, stage doc consolidation, `h001-verifier-v2` implementation, `15_calibration.md`, `16_evaluation.md`, official `3DSSG_subset`-based `17_subset.md`, `18_baseline.md`, `19_schema.md`, `20_layout.md`, `tools/check_layout.py`, `tools/prep_layout.py`, and `21_eval_path.md` completed; faithful `VL-SAT` layout prep staging policy next
