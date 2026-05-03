# Research Index

Last updated: 2026-05-03

## Status

현재 하네스는 `CAND-001 hypothesis prep`과 `CAND-003 literature survey`를 병렬로 추적한다. CAND-001 literature pass는 석사 연구 후보로 좁히는 데 충분하고, H001은 one-scan evidence export, rule verifier, point support evidence, `h001-rules-v1`, v1 review triage, visual inspection, support/contact subtype decision, `h001-verifier-v2` 구현 및 one-scan 검증, probabilistic calibration 설계, violation/recall evaluation protocol, official `3DSSG_subset` 기반 multi-scan/subset strategy 결정, prediction-level baseline 선택, `vlsat_closed_set` prediction schema 정의, VL-SAT local layout compatibility check, H001-internal VL-SAT layout checker 구현/실행, generated annotation staging, faithful VL-SAT eval path decision, faithful layout prep staging policy, H001-Mini validation scan selection까지 완료했다. 첫 baseline은 `VL-SAT` / `vlsat_closed_set`이다. 오래된 stage 문서 07~12는 `07_stage_log.md`로 병합했다. CAND-003은 2026-04-30 P1 paper intake까지 통해 RieMind, 3D-VCD, SayPlan, SG-Nav, SCOUT/SymSearch, 3DGraphLLM, 3D-Mem의 novelty boundary와 offline verifier/refiner first cut을 정리했다.

## Active Topic

3D Scene Graph / CAND-001 / CAND-003

## Active Questions

1. Selected H001-Mini scan payload를 faithful `VL-SAT` staged root로 어떻게 준비할 것인가?
2. Calibration table schema와 counterfactual negative export를 어떻게 구현할 것인가?
3. Relative horizontal coordinate-frame validation을 support/contact 이후 어떻게 처리할 것인가?
4. CAND-003을 CAND-001의 downstream extension으로 둘 것인가, 독립 thesis 후보로 키울 것인가?

## Current Working File

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

## Expansion Rule

문헌 조사 결과는 `literature/`에 저장한다. Hypothesis 산출물은 `hypothesis/`에 저장한다. 아직 `experiments/`, `paper/`, `decisions/` 구조는 만들지 않는다.
