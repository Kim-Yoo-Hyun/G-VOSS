# Research Workspace

이 저장소는 3D Scene Graph 석사 연구를 위한 작업 공간이다.

현재 단계는 CAND-001 H001의 Docker-based scoped experiment 결과를 paper writing phase로 전환하는 단계와 CAND-003 literature survey를 병렬로 추적하는 단계다. CAND-001은 `Geometry-Grounded Open-Vocabulary Relation Graph` 방향에서 hypothesis-stage evidence lock, scoped main experiment spec, `VL-SAT` locked result, Open3DSG second-source metric evidence, real failure-analysis rows, qualitative case inspection, paper preview, bilingual paper outline, ICCV-style first-pass manuscript body, and ICCV-style LaTeX source conversion까지 완료했다. H001 문서는 `hypothesis/CAND-001/H001_geometry-grounded-verification/` 아래 7개 canonical 파일로 정리되어 있다.

## Current Focus

- CAND-001: `experiments/H001_geom_reliability/`에서 Docker-generated `VL-SAT` tables, Open3DSG avg-BLIP checkpoint reproduction, raw-dump identity, adapter export, geometry join, metric eval, Table 6, real failure-analysis rows, qualitative failure-case inspection, and paper caveat wording are ready.
- CAND-001 paper handoff: `paper/preview.md`, `paper/progress.md`, bilingual `paper/outline.md`, reviewed first-pass `paper/draft.md`, ICCV-style LaTeX source `paper/iccv/`, figure source lock `paper/figures.md`, and verified/layout-reviewed draft Figure 1-3 plus geometry-backed Figure 3 under `paper/generated/figures/` are ready. The draft now covers Title, Abstract, Introduction, Related Work, Problem Formulation, Method, Experimental Setup, Results/Discussion, Limitations, and Conclusion, and Related Work uses BibTeX-style citation keys.
- CAND-001 literature expansion: 2026-05-23 novelty-threat pass completed a RelWitness full-PDF skim and registered ZING-3D, Open-World 3DSG-RAG, View-on-Graph, and VIZOR as recent trend/boundary papers. H001 wording should avoid claiming novelty as relation witnesses, geometry evidence, or calibrated witness quality alone.
- CAND-001 next gate: complete the manuscript-content pass inside `paper/iccv/` before PDF build. Section prose, table/figure callouts, captions, Open3DSG caveats, and limitations should be fully filled and claim-consistent first; then convert figures and verify/build. The current host lacks `pdflatex`, `bibtex`, `latexmk`, `rsvg-convert`, and `inkscape`, so build and figure conversion have not been verified. The paper-body budget review is complete: Title-through-Conclusion prose is about 3,507 words, with Table 1/2/3/6 as the recommended main-table set and Table 4/full Table 5 as appendix/prose fallback.
- CAND-001 reproducibility handoff: `docs/reproducibility.md` is updated with the 2026-05-21 `.gitignore` portability audit. GitHub can carry runbooks, Docker setup, scripts, reports, compact manifests, and metric summaries; large datasets/checkpoints/features/raw JSONL/model caches must be rebuilt/downloaded or transferred separately.
- CAND-001 optional extension: Qwen-VL cache is ready; runtime preflight/tiny inference smoke can run only after GPU/RAM pressure is cleared, and remains non-metric extension evidence.
- CAND-001 experiment rule: 논문 본문용 실제 experiment 구현은 Docker 기반으로만 진행하고 host-only output은 paper result로 승격하지 않는다.
- Research target rule: 연구 목표와 방향성은 AI, ML, CV, Robotics top-tier journal/conference를 타겟으로 판단한다.
- CAND-003: `Geometry-Aware Refinement of LLM/VLM Task Reasoning on 3DSG` literature survey / feasibility boundary 정리 완료, hypothesis workflow 승격 여부 판단 대기.

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
- Open3DSG covers `support_contact`, `proximity`, and `relative_vertical` and now provides second-source metric evidence within measured H001 families.
- Docker experiment root `experiments/H001_geom_reliability/` has generated Table 1-6, `manifest.lock.json`, `report.md`, figure specs, Open3DSG metric artifacts, real failure rows, qualitative case queue, and qualitative inspection.
- Qwen-VL is staged only as an optional modern semantic-source extension: input/output contract, parser skeleton, 30-row non-held-out tiny pilot, model-lock plan, 30/30 pair crops, and Qwen3-VL-4B cache verification are ready; runtime preflight/inference has not started.
- Dockerized Open3DSG checkpoint reproduction plan is ready under `experiments/H001_geom_reliability/sources/open3dsg/`: official train split 1178 scans / 3852 subgraphs / 81,190 relations, H001 eval split 127 scans / 388 subgraphs / 7,505 relations, dependency pins, dataset/cache mounts, train/eval commands, and failure budget.
- Open3DSG `training_repro` metadata/split staging is ready with H001 held-out overlap 0/0: official train 1178 scans / 3852 subgraphs / 81,190 relations and train-dev without H001 30 scans / 160 subgraphs / 3,749 relations.
- Open3DSG full train payload staging is complete: train scan dirs, raw files, Open3DSG mesh/texture, and sequence files are 1178/1178; train-dev payload is 30/30; `open3dsg_train_handoff` status is `ready_for_open3dsg_env_check`.
- Open3DSG Docker env/cache is ready on `h001-open3dsg-repro:cu128` with torch `2.8.0+cu128` and RTX 5090 `sm_120` support; cache preflight has only a non-blocking `torch_hub` cache warning.
- Open3DSG train view generation is complete at 1178/1178 view pickles; `train_views_full` exited 0 with 1176 generated and 2 already ready.
- Open3DSG validation view/preprocess guard is complete: validation views 30/30 and runtime validation split 30 scans / 156 subgraphs / 3,696 relations after filtering 4 non-recoverable preprocess drops.
- Open3DSG train preprocess recoverability audit is complete: all 108 missing outputs match the source-level `too few visible objects` drop, and a representative Docker retry did not recover the sampled missing targets.
- Open3DSG runtime train split is explicitly filtered to preprocessed-ready rows: 1158 scans / 3744 subgraphs / 79,704 relations retained from the official 1178 scans / 3852 subgraphs / 81,190 relations. The 108 removed subgraphs / 1,486 relations are recorded under `train_preprocess_filter/`, and `.unfiltered` backups exist in the staged runtime split.
- Open3DSG official BLIP TopK5/scales3 feature dump is complete and Docker `feature_audit` passed with 3900/3900 complete feature ids.
- Open3DSG avg-BLIP full training completed. The selected checkpoint is `epoch=13-step=13104.ckpt`, chosen by train-dev `val/loss` 0.32881081104278564 before H001 held-out inspection.
- Open3DSG H001 eval feature cache is complete for the covered loadable scope: 377/377 complete feature ids, with `validation_missing_preprocessed:11` retained as a caveat.
- Open3DSG raw dump `raw_dump/raw.jsonl` has 19,162 rows and passed Docker raw-dump identity. Clean v14 streaming same-path resume completed with exit `0`, wrote 377/377 completed batches and 19,162 rows, and its SHA256 matches `raw_dump/raw.jsonl`; earlier exit-137 attempts remain historical run records.
- Open3DSG adapter, geometry join, metric eval, and Table 6 are ready: 496,600 prediction rows, 496,600 geometry rows, 114,600 geometry-checkable rows, and no metric blockers.
- Open3DSG key metrics: semantic_only R@50/R@100 0.3945/0.4963, Violation@50/@100 0.1326/0.1195; probabilistic_recalibrated R@50/R@100 0.3843/0.5580, Violation@50/@100 0.0575/0.0803; rule_verified_point_subtype R@50/R@100 0.4149/0.5238, Violation@50/@100 0.0/0.0; family_specific control R@50/R@100 0.4530/0.5984, Violation@50/@100 0.0228/0.0311.
- Open3DSG qualitative inspection is ready: 36 selected cases, 23 demoted by geometry-aware reranking, 13 promoted or retained, 10 rule-violated cases with `p_geom_valid > 0.9`, and no taxonomy change. This is reviewer-defense evidence, not a representative visual audit.
- Open3DSG paper caveat wording is ready: filtered train 3,744/3,852 subgraphs, train-dev validation 156/160 subgraphs, H001 covered loadable scope 377/388 contexts with `validation_missing_preprocessed:11`, averaged-BLIP variant, exact-label 2,545-row H001-family denominator, and residual calibration risk are fixed in `paper_caveats/`.
- Paper preview, progress rationale, outline, and first-pass draft are ready: `paper/preview.md` summarizes current results and recovery files, `paper/progress.md` explains why each hypothesis/experiment stage was run and why the next stage was needed, `paper/outline.md` fixes the English/Korean paper skeleton, recommended title, title alternatives, three contribution statements, abstract skeleton, Introduction logic, evidence placement, reviewer-defense map, caveat placement, and manuscript-ready table/figure caption drafts, and `paper/draft.md` contains ICCV-style first-pass manuscript prose from Title through Conclusion. Cross-source results and failure analysis are empirical validation, not a fourth contribution.

Inference:

- H001 is promising as a scoped top-tier direction.
- Current evidence supports a cross-source reliability-layer claim within measured H001 families across `VL-SAT` and Open3DSG.
- Broad open-vocabulary 3DSSG improvement claims remain blocked beyond the measured H001-family scope. The train/validation filtering, averaged-BLIP route, covered loadable scope, residual calibration risk, `validation_missing_preprocessed:11`, and any reduced/pilot-only route are fixed as scope limitations.

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
- `docs/paper.md`: paper framing과 novelty/reviewer-defense 기준
- `docs/reproducibility.md`: H001 데이터, checkpoint, Docker, 재현 명령, artifact/evaluation 요약
- `literature/README.md`: field map, trend synthesis, cross-paper insights
- `literature/PAPER.md`: paper registry와 reading queue
- `literature/Contribution Candidates.md`: 기여 후보 목록
- `literature/CAND-001.md`: CAND-001 세부 문제 설정과 feasibility
- `literature/CAND-003.md`: CAND-003 literature survey와 feasibility boundary
- `hypothesis/README.md`: hypothesis index
- `hypothesis/CAND-001/README.md`: CAND-001 hypothesis index
- `hypothesis/CAND-001/H001_geometry-grounded-verification/`: active H001 canonical files, tools, and artifacts
- `paper/preview.md`: paper writing phase 직전의 현재 결과 총정리와 재시작 시 필수 파일 목록
- `paper/progress.md`: hypothesis-to-experiment progression rationale and result interpretation
- `paper/outline.md`: 영어/한국어 paper skeleton, section별 evidence placement, reviewer-defense, figure/table plan
- `paper/draft.md`: Title through Conclusion first-pass manuscript prose
- `paper/iccv/`: ICCV-style LaTeX manuscript source using vendored ICCV/CVF style files; build pending TeX/figure-conversion tooling
- `paper/figures.md`: Figure 1-3 source lock, exact values, case IDs, and caption constraints
- `paper/generated/figures/`: verified draft Figure 1-3 SVGs and generation manifest

## Working Principle

작게 시작한다. Full baseline reproduction보다 먼저, 3DSSG / 3RScan에서 geometry-checkable predicate subset을 대상으로 relation edge evidence, verifier, subtype-aware support/contact consistency signal을 확인한다.

현재 만든 experiment 구조:

- `experiments/H001_geom_reliability/`
- `paper/preview.md`: paper writing phase 직전의 현재 결과 총정리와 재시작 시 필수 파일 목록
- `paper/outline.md`: paper skeleton과 한국어 병기 outline
- `paper/draft.md`: first-pass manuscript prose
- `paper/iccv/`: ICCV-style LaTeX source conversion
- `paper/figures.md`: Figure 1-3 source lock
- `paper/generated/figures/`: draft Figure 1-3 SVGs

아직 만들지 않는 구조:

- `decisions/`
