# Hypothesis Index

Last updated: 2026-05-27

이 폴더는 literature candidate를 검증 가능한 research hypothesis로 좁히는 산출물을 저장한다. Workflow와 작성 규칙은 `docs/hypothesis.md`를 따른다.

## Ownership

- 이 파일은 hypothesis-level index와 active candidate summary를 함께 관리한다.
- `hypothesis/CAND-001/README.md`는 중복 상태를 줄이기 위해 이 파일로 병합했고 더 이상 사용하지 않는다.
- Candidate-specific detail은 필요할 때만 각 H-folder의 canonical files에 기록한다.
- 자세한 experiment/runtime/reproducibility 상태는 `experiments/H001_geom_reliability/`, `docs/reproducibility.md`, `paper/preview.md`가 소유한다.

## Active Candidate

- Candidate: `CAND-001: Geometry-Grounded Open-Vocabulary Relation Graph`
- Source: `literature/CAND-001.md`
- Recommended formulation: `Geometry-grounded verification and representation of open-vocabulary 3D scene graph relations`
- Active hypothesis: `H001 Geometry-grounded verification of open-vocabulary 3DSSG relations`
- H001 folder: `hypothesis/CAND-001/H001_geometry-grounded-verification/`

## Hypothesis Registry

| Hypothesis | Folder | Status | Next Gate |
| --- | --- | --- | --- |
| H001: Geometry-grounded verification of open-vocabulary 3DSSG relations | `CAND-001/H001_geometry-grounded-verification/` | Hypothesis-stage evidence, Docker `VL-SAT` table/report reproduction, Open3DSG metric/failure/caveat evidence, paper handoff, and Qwen-VL runner plan are complete | Resume Qwen-VL from shard 0014 if pursuing third-source extension; otherwise continue paper polish |

## H001 Claim Boundary

Allowed current claim:

> Calibrated geometry-consistency evaluation and re-ranking improves relation reliability within measured H001 families across reproduced `VL-SAT` and Open3DSG source outputs.

Blocked claims:

- Broad open-vocabulary 3DSSG SOTA improvement.
- Baseline-agnostic improvement across arbitrary relation predictors.
- Qwen-VL as a replacement for `VL-SAT` or Open3DSG.
- Exact non-averaged Open3DSG reproduction.

## H001 Canonical Files

- `01_overview.md`: problem, hypothesis, feasibility, claim boundary, transition gate
- `02_method.md`: evidence schema, verifier, calibration, prediction-row join, evaluation protocol
- `03_data_baseline.md`: dataset/baseline layout, fixed scope, staged payload readiness
- `04_results.md`: mini/hardened metrics, controls, evidence lock, GT-based verifier evaluation
- `05_audit.md`: structured audit, visual sanity check, provenance and wording limits
- `06_second_source.md`: FROSS/Open3DSG source/runtime feasibility and claim boundary
- `07_experiment_spec.md`: scoped Docker-based main experiment spec, required metrics/tables/figures, acceptance criteria

## Current Gate

Facts:

- H001 has entered the Docker experiment and paper-writing phase.
- `experiments/H001_geom_reliability/` is the active paper experiment root.
- `VL-SAT` locked results and Open3DSG second-source metric/failure/caveat evidence are ready for the scoped H001 claim.
- Paper handoff files are ready under `paper/preview.md`, `paper/progress.md`, `paper/outline.md`, `paper/draft.md`, `paper/aaai/`, and `paper/figures.md`.
- Qwen-VL is a third semantic source / modern VLM extension only. Shards 0000-0013 are complete with 3,500 parsed rows; run id `20260527_023111` stopped at shard 0014 because of GPU utilization guard. Clean resume starts from `qwen_full_source_shard_0014`.

Inference:

- H001 is promising as a scoped top-tier direction if the manuscript keeps the claim narrow: failure mechanism, calibrated geometry-consistency framework, recall/violation tradeoff, controls, denominator transparency, and Open3DSG caveats.
- Qwen-VL should remain non-metric extension evidence until sharded inference, parser validation, adapter export, geometry join, metrics, controls, bootstrap CI if reported, and audit complete through Docker.

## Active Artifact Families

- Hypothesis smoke-test artifacts stay under `hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/`.
- Paper experiment artifacts stay under `experiments/H001_geom_reliability/`.
- Large runtime data, model caches, checkpoints, and features stay under ignored roots such as `local_dataset/` or external artifact bundles.

## Update Rule

- Update this file when the active hypothesis, claim boundary, or current gate changes.
- Update `docs/hypothesis.md` when hypothesis workflow rules change.
- Update `docs/reproducibility.md` and relevant experiment README files for commands, datasets, checkpoints, artifact bundles, or recovery details.
- Do not recreate `hypothesis/CAND-001/README.md` unless CAND-001 later contains multiple active hypotheses whose candidate-level summary can no longer fit here.
