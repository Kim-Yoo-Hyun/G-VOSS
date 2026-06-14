# Research Workspace

이 저장소는 3D Scene Graph 관계 예측의 신뢰성을 연구하는 석사 연구 작업 공간이다. 현재 paper-facing 연구명은 `GeoCalib: Calibrating Geometric Consistency for Reliable 3D Scene Graph Relations`이며, `H001`은 내부 hypothesis/experiment identifier로 유지한다. GeoCalib는 기존 relation source가 낸 semantic relation edge를 explicit 3D geometry evidence로 검증하고 재정렬해, top-K relation의 recall과 geometry violation tradeoff를 함께 평가한다. 현재 main evidence는 `VL-SAT` full official validation과 Open3DSG full-validation recovery route를 중심으로 관리한다.

## 핵심 문제의식

기존 3D Scene Graph relation predictor는 의미상 그럴듯한 relation을 높은 점수로 예측할 수 있지만, 해당 subject-object pair의 실제 3D geometry와 일치하지 않을 수 있다. 이 저장소의 핵심 질문은 semantic confidence가 relation-level physical consistency에 calibrated 되어 있는지, 그리고 geometry-consistency scoring/re-ranking이 violation을 줄이면서 recall tradeoff를 명확히 보고할 수 있는지다. Claim boundary는 broad open-vocabulary 3DSSG generation improvement가 아니라, geometry-checkable relation family에 대한 scoped reliability layer다.

## Repository Structure

- `summary.md`: 연구 정의, claim boundary, evidence, paper direction의 압축 요약.
- `TODO.md`: 현재 작업판. `Now`, `Next`, 완료/보류 상태를 관리한다.
- `docs/`: workflow rulebook과 dashboard.
  - `docs/index.md`: 현재 연구 상태 dashboard.
  - `docs/paper.md`: paper framing, novelty, reviewer-defense rule.
  - `docs/experiments.md`: Docker experiment promotion rule.
  - `docs/reproducibility.md`: dataset/checkpoint/artifact recovery and handoff runbook.
  - `docs/literature.md`, `docs/hypothesis.md`: literature/hypothesis workflow.
- `literature/`: paper cards, trend synthesis, contribution candidates.
- `hypothesis/`: CAND/H hypothesis canonical notes and pre-paper evidence.
- `experiments/H001_geom_reliability/`: Docker-based paper experiment root.
- `paper/`: manuscript workspace, figure plans, appendix/risk docs, venue LaTeX source.
- `logs/`: long-running job logs and exit/status files.
- `local_dataset/`: ignored local dataset/cache/runtime root.
- `release/`: ignored external artifact staging root.

## 핵심 실행 코드와 실행 방법

Paper-result experiments must be Docker-based. Start from the experiment root:

```bash
cd /home/yoohyun/research
```

Primary experiment entry points:

- `experiments/H001_geom_reliability/compose.yaml`
- `experiments/H001_geom_reliability/commands.md`
- `experiments/H001_geom_reliability/README.md`
- Source-specific compose/runbooks under:
  - `experiments/H001_geom_reliability/sources/vlsat/`
  - `experiments/H001_geom_reliability/sources/open3dsg/`
  - `experiments/H001_geom_reliability/sources/qwen_vl/`

Paper source build entry point:

```bash
docker build -f paper/aaai/Dockerfile.tex -t h001-aaai-tex:20260526 paper/aaai
docker run --rm -v "$PWD/paper:/work" -w /work/aaai h001-aaai-tex:20260526 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Before rerunning metrics, uploads, recovery, or cleanup, read `docs/reproducibility.md` first. It owns the current artifact list, paths, verification commands, and cleanup implications.

## Artifact Management

Tracked GitHub content should include source code, Dockerfiles/compose files, scripts, runbooks, compact manifests, reports, metric summaries, paper source, and planning docs. Large datasets, model caches, checkpoints, feature caches, raw JSONL dumps, and row-level runtime outputs stay outside Git and must be regenerated or transferred separately.

Do not delete local dataset, checkpoint, feature-cache, model-cache, or row-level JSONL artifacts unless an external copy has been verified with checksums, file counts, expected layout, or a lightweight sanity script. For final submission or handoff, verify whether the current package was regenerated after GeoCalib naming, Figure updates, low-K table decisions, and any Qwen extension inclusion decision.

## Where To Continue

- Read `summary.md` for the current research story and claim boundary.
- Read `TODO.md` for immediate tasks and recently completed work.
- Read `docs/index.md` for a dashboard of active files and open questions.
- Read `docs/reproducibility.md` before any artifact transfer, deletion, rerun, or recovery.
- Read `paper/README.md` and `paper/preview.md` before editing manuscript text.
