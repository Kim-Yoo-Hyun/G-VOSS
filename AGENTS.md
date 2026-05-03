# Research Agent Harness

이 저장소는 3D Scene Graph 분야의 석사 연구를 위해 문헌 조사, 동향 파악, 기여 가능성 탐색을 누적하는 작업 공간이다.

## Current Scope

- 현재 하네스는 `literature` 조사에서 `hypothesis` 준비 단계로 확장되었다.
- 실험, 논문 작성 워크플로우는 아직 만들지 않는다.
- `docs/hypothesis.md`는 hypothesis workflow와 작성 규칙을 관리한다.
- `docs/literature.md`는 literature workflow와 작성 규칙을 관리한다.
- 실제 문헌 조사 결과는 루트의 `literature/` 폴더에 저장한다.
- 실제 hypothesis 산출물은 루트의 `hypothesis/` 폴더에 저장한다.
- 논문 하나는 `literature/<paper-folder>/` 하나로 관리한다.

## Entry Points

에이전트는 작업을 시작할 때 아래 순서로 읽는다.

1. `README.md`
2. `TODO.md`
3. `docs/index.md`
4. `docs/literature.md`
5. `docs/hypothesis.md`
6. `literature/README.md`
7. `literature/PAPER.md`
8. `literature/Contribution Candidates.md`
9. `literature/CAND-001.md`
10. `hypothesis/README.md`

`docs/literature.md`는 literature workflow의 핵심 문맥이다.
`docs/hypothesis.md`는 hypothesis workflow의 핵심 문맥이다.
`literature/README.md`는 cross-paper synthesis다.
`literature/PAPER.md`는 paper registry와 reading queue다.
`literature/Contribution Candidates.md`는 기여 후보 목록이다.
`literature/CAND-001.md`는 CAND-001의 literature-derived problem setting과 feasibility다.
`hypothesis/README.md`는 hypothesis index다.
`TODO.md`는 앞으로 할 계획과 현재 진행 상태를 관리하는 루트 작업판이다.

## Working Language

- 사용자에게는 한국어로 답한다.
- 논문 제목, 방법명, 데이터셋명, metric, benchmark 이름은 영어 원문을 유지한다.
- "사실", "논문 주장", "에이전트 추론", "사용자 판단 필요"를 섞지 말고 구분한다.

## Naming Rules

- 파일명과 문서 제목은 직관적이고 핵심 단어 기반으로 짧게 작성한다.
- 부모 폴더나 workflow 이름을 파일명에 반복하지 않는다. 예: `visual_inspection/labels.jsonl`처럼 쓴다.
- 불필요한 긴 접두사, 중복된 candidate/hypothesis 이름, 설명문 형태의 파일명은 피한다.
- 번호가 필요한 workflow 문서는 기존 순서를 유지하되 제목은 짧게 둔다. 예: `01_problem.md`, `14_verifier_v2.md`.
- 중복된 stage 문서는 하나의 짧은 stage log로 병합한다. 이미 병합한 오래된 번호 파일을 다시 만들지 않는다.

## Evidence Rules

3D Scene Graph의 최근 동향, 최신 논문, 연구 공백, 기여 가능성을 다룰 때는 반드시 최신 정보를 확인한다.

- 우선순위 소스: 논문 PDF, arXiv, CVF Open Access, OpenReview, 공식 프로젝트 페이지, 공식 코드 저장소.
- 블로그/뉴스/요약글은 보조 자료로만 사용한다.
- 논문을 인용할 때는 제목, 연도, venue 또는 preprint 상태, 링크를 기록한다.
- "최근", "최신", "SOTA", "트렌드"라고 말하려면 검색 날짜 또는 확인 날짜를 함께 남긴다.
- 근거가 약한 판단은 `Inference`로 표시한다.
- 출처를 확인하지 못한 항목은 확정된 사실처럼 쓰지 않는다.

## Literature Workflow

문헌 조사 작업은 네 단계로 수행한다.

1. Field Map
   - 3D Scene Graph의 하위 흐름을 정리한다.
   - 예: open-vocabulary, dynamic/online, LLM/VLM reasoning, robotics/embodied AI, 3D generation, 3DGS/NeRF integration.

2. Paper Card
   - 각 논문을 같은 포맷으로 요약한다.
   - 문제, 핵심 아이디어, 데이터/실험, 강점, 한계, 내 연구와의 연결을 기록한다.

3. Trend Synthesis
   - 논문별 요약을 넘어서 흐름을 뽑는다.
   - 어떤 문제가 반복되는지, 어떤 assumption이 공유되는지, 어떤 benchmark가 병목인지 본다.

4. Contribution Scan
   - 석사 연구로 기여 가능한 지점을 찾는다.
   - 기여 가능성은 "아이디어"가 아니라 "검증 가능한 연구 질문" 형태로 정리한다.

## Update Protocol

문헌 조사를 수행한 에이전트는 `literature/` 아래에 결과를 저장한다.

- `literature/README.md`: Field Map, Trend Synthesis, Cross-Paper Insights, Open Questions
- `literature/PAPER.md`: Paper Registry, Reading Queue
- `literature/Contribution Candidates.md`: contribution candidate 목록
- `literature/CAND-<number>.md`: candidate별 세부 문제 설정과 feasibility
- `literature/<paper-folder>/paper.pdf`: 가능하면 저장하는 논문 원문 PDF
- `literature/<paper-folder>/01_metadata.md`: 논문 식별 정보와 링크
- `literature/<paper-folder>/02_paper_card.md`: 문제, 방법, 강점, 한계
- `literature/<paper-folder>/03_evaluation.md`: dataset, metric, baseline, result
- `literature/<paper-folder>/04_insights.md`: 내 연구와의 연결, 추론, 기여 가능성

갱신할 때는 날짜를 남긴다. 현재 날짜 기준으로 작성한다.

Hypothesis 작업을 수행한 에이전트는 `hypothesis/` 아래에 결과를 저장한다.

- `hypothesis/README.md`: hypothesis index와 active gate
- `hypothesis/CAND-<number>/README.md`: candidate-level hypothesis 묶음
- `hypothesis/CAND-<number>/H<number>_<short-title>/01_problem.md`: 문제 정의
- `hypothesis/CAND-<number>/H<number>_<short-title>/02_hypothesis.md`: 검증 가능한 가설
- `hypothesis/CAND-<number>/H<number>_<short-title>/03_feasibility.md`: dataset/baseline/metric gate
- `hypothesis/CAND-<number>/H<number>_<short-title>/04_experiment.md`: 첫 실험 형태
- `hypothesis/CAND-<number>/H<number>_<short-title>/05_evidence_schema.md`: evidence schema
- `hypothesis/CAND-<number>/H<number>_<short-title>/06_rule_verifier.md`: verifier design
- `hypothesis/CAND-<number>/H<number>_<short-title>/07_stage_log.md`: merged execution and stage log
- `hypothesis/CAND-<number>/H<number>_<short-title>/13_subtypes.md`: support/contact subtype decision
- `hypothesis/CAND-<number>/H<number>_<short-title>/14_verifier_v2.md`: subtype-aware verifier contract and one-scan result summary
- `hypothesis/CAND-<number>/H<number>_<short-title>/15_calibration.md`: probabilistic geometry consistency calibration design
- `hypothesis/CAND-<number>/H<number>_<short-title>/16_evaluation.md`: prediction-level violation/recall evaluation protocol
- `hypothesis/CAND-<number>/H<number>_<short-title>/17_subset.md`: multi-scan/subset strategy decision
- `hypothesis/CAND-<number>/H<number>_<short-title>/18_baseline.md`: prediction-level baseline decision
- `hypothesis/CAND-<number>/H<number>_<short-title>/19_schema.md`: prediction JSONL schema and adapter contract
- `hypothesis/CAND-<number>/H<number>_<short-title>/20_layout.md`: baseline layout compatibility check
- `hypothesis/CAND-<number>/H<number>_<short-title>/21_eval_path.md`: reportable baseline evaluation path decision
- `hypothesis/CAND-<number>/H<number>_<short-title>/22_prep.md`: faithful baseline layout prep staging policy
- `hypothesis/CAND-<number>/H<number>_<short-title>/23_mini.md`: mini validation scan selection
- `hypothesis/CAND-<number>/H<number>_<short-title>/tools/`: hypothesis-stage smoke-test scripts

Hypothesis smoke-test artifact는 hypothesis 폴더 내부에만 둔다.

- one-scan artifact root: `hypothesis/CAND-<number>/H<number>_<short-title>/artifacts/one_scan/<scan-id>/`
- baseline layout checker artifact root: `hypothesis/CAND-<number>/H<number>_<short-title>/artifacts/layout/<baseline-name>/`
- subset selection artifact root: `hypothesis/CAND-<number>/H<number>_<short-title>/artifacts/subset/<subset-name>/`
- Phase A files: `edges.jsonl`, `export_summary.json`, `export_report.md`, `thresholds.json`
- Phase B files: `decisions.jsonl`, `rules_summary.json`, `rules_report.md`, `review_queue.jsonl`, `review_labels.jsonl`, `review_report.md`
- Phase C files: `point_evidence.jsonl`, `point_comparison.jsonl`, `point_summary.json`, `point_report.md`, `comparison_report.md`
- Visual inspection files should live under `visual_inspection/` with short names such as `labels.jsonl`, `report.md`, `projections.png`.
- Versioned verifier outputs may use a short subfolder such as `v2/` and short filenames such as `decisions.jsonl`, `summary.json`, `report.md`.
- Layout checker outputs should use short filenames such as `summary.json`, `prep_manifest.json`, and `report.md`.
- Layout prep outputs should use short filenames such as `generated_manifest.json`, and generated baseline files should stay under `artifacts/layout/<baseline-name>/generated/`.
- Subset selection outputs should use short filenames such as `manifest.json`, `scans.txt`, `candidates.jsonl`, `subgraphs.jsonl`, and `report.md`.
- Large baseline runtime files should stay under an ignored staged dataset root such as `local_dataset/VLSAT_staged/`, not under tracked hypothesis artifacts.
- 중간 산출물이 더 구체적인 review/report artifact로 대체되면 오래된 queue 파일은 유지하지 않는다.

에이전트는 작업 전후로 `TODO.md`도 갱신한다.

- 시작할 작업은 `Now`에 둔다.
- 바로 다음 작업은 `Next`에 둔다.
- 완료한 작업은 체크한다.
- 상세 조사 내용은 `TODO.md`나 `docs/literature.md`에 길게 쓰지 말고 `literature/`에 쓴다.

## Contribution Candidate Standard

기여 후보는 아래 조건을 만족해야 한다.

- 어떤 기존 한계에서 출발하는지 분명해야 한다.
- 왜 3D Scene Graph 문제인지 설명되어야 한다.
- 어떤 데이터셋, benchmark, metric으로 확인할 수 있는지 가늠 가능해야 한다.
- 석사 과정에서 3-6개월 단위로 시도 가능한 범위여야 한다.
- 실패했을 때 무엇을 배울 수 있는지 적어야 한다.

## Do Not Over-Structure

- 빈 paper folder를 미리 많이 만들지 않는다.
- `experiments/`, `paper/`, `decisions/`는 아직 만들지 않는다.
- hypothesis는 루트의 `hypothesis/` 폴더에서만 관리한다.
- 해당 단계가 실제로 필요해지면 먼저 새 workflow 문서 하나에서 시작한다.
- 구조는 연구가 커질 때 따라오게 한다.
