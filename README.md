# Research Workspace

이 저장소는 3D Scene Graph 석사 연구를 위한 작업 공간이다.

현재 단계는 CAND-001 H001의 Docker-based full-validation experiment 결과를 paper writing phase로 전환하는 단계와 CAND-003 literature survey를 병렬로 추적하는 단계다. CAND-001은 `Geometry-Grounded Open-Vocabulary Relation Graph` 방향에서 hypothesis-stage evidence lock, scoped main experiment spec, VL-SAT/Open3DSG full-validation metric bundles, real failure-analysis rows, qualitative case inspection, paper preview, bilingual paper outline, first-pass manuscript body, ICCV-style source conversion, AAAI-style source conversion, and AAAI reproducibility checklist insertion까지 완료했다. 현재 target venue source는 `paper/aaai/`이다. H001 문서는 `hypothesis/CAND-001/H001_geometry-grounded-verification/` 아래 7개 canonical 파일로 정리되어 있다.

## Current Focus

- CAND-001: `experiments/H001_geom_reliability/`에서 Docker-generated full-validation `VL-SAT` tables, Open3DSG recovery-branch full-validation tables, raw-dump identity, adapter export, geometry join, metric eval, Table 6, real failure-analysis rows, qualitative failure-case inspection, and paper caveat wording are ready.
- CAND-001 full-validation direction: 2026-06-05 decision is to use the full
  official `3DSSG_subset` validation split as the paper-facing primary
  evaluation route. The full-validation metric bundles for both VL-SAT and
  Open3DSG are now generated. Target
  full-validation scope is 157 scans / 548 contexts / 11,254 GT rows / 3,972
  H001-family GT rows. Docker
  `full_validation_scope_contract` has frozen the scope contract under
  `experiments/H001_geom_reliability/full_validation_transition/scope_contract/`
  with 36,808 candidate directed pairs and 957,008 expected VL-SAT prediction
  rows. VL-SAT full-validation Docker route is ready under
  `experiments/H001_geom_reliability/sources/vlsat/full_validation/`: 157/157
  faithful staged scans, runtime image `h001-open3dsg-repro:cu128`, 16/16
  checkpoint files, raw dump `raw_dump_ready`, adapter export, geometry join,
  metric eval, GT verifier eval, and VL-SAT-only bootstrap CI all completed.
  Outputs: 957,008 prediction rows, 11,254 GT rows, 3,972 H001-family GT rows.
  Key VL-SAT full-validation metrics: semantic_only R@50/R@100
  `0.9272/0.9635`, V@50/@100 `0.0268/0.0476`; probabilistic_recalibrated
  `0.9305/0.9688`, V `0.0229/0.0404`; rule_verified_point_subtype
  `0.9257/0.9627`, V `0.0/0.0`; family_specific control
  `0.9288/0.9683`, V `0.0206/0.0333`. Open3DSG full-validation Docker route
  is also ready under
  `experiments/H001_geom_reliability/sources/open3dsg/full_validation/`:
  the original covered-scope branch has 533/548 preprocess coverage and the
  recovery branch
  `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/`
  reaches 548/548 after diagnosing the Open3DSG fewer-than-4-visible-objects
  preprocess gate, relaxing it to `min_visible=2`, and regenerating relaxed
  views for two scans. The recovery branch has clean-exit raw dump 26,938 rows
  / 548 batches, adapter 695,916 prediction rows, geometry join, metrics,
  bootstrap CI, 82,155 failure rows, and Table 6/caveat regeneration complete.
  Key Open3DSG recovery metrics: semantic_only R@50/R@100 `0.4096/0.5161`, V
  `0.1386/0.1242`; probabilistic_recalibrated `0.3975/0.5723`, V
  `0.0606/0.0811`; rule_verified_point_subtype `0.4295/0.5368`, V `0.0/0.0`;
  family_specific control `0.4658/0.6047`, V `0.0286/0.0341`. Full-validation
  failure taxonomy is also ready: VL-SAT has 59,841 diagnostic rows and a
  36-case qualitative inspection queue; Open3DSG recovery has 82,155 diagnostic
  rows and a new 36-case qualitative inspection queue. This 548/548 recovery
  branch is now the paper-facing primary Open3DSG full-validation route, while
  the original 533/548 covered branch remains a sensitivity /
  unmodified-source-route check. Main text and appendix must disclose the
  selected non-avg BLIP checkpoint plus recovery-policy preprocess/view caveat.
  Method provenance must be stated as train/train-dev-derived: final
  family mapping, verifier policies, counterfactuals, and `p_geom_valid`
  calibration are frozen before validation source-result reporting. H001-Mini
  is hypothesis/feasibility evidence, not paper metric evidence.
- CAND-001 paper handoff: `paper/README.md`, `paper/preview.md`, `paper/progress.md`, bilingual `paper/outline.md`, reviewed first-pass `paper/draft.md`, reviewer-risk register `paper/risk.md`, appendix/provenance plan `paper/appendix.md`, checklist-included AAAI-style LaTeX source `paper/aaai/`, historical ICCV-style source `paper/iccv/`, figure source lock `paper/figures.md`, and verified/layout-reviewed draft Figure 1-3 plus geometry-backed Figure 3 under `paper/generated/figures/` are ready. The draft now covers Title, Abstract, Introduction, Related Work, Problem Formulation, Method, Experimental Setup, Results/Discussion, Limitations, and Conclusion, and Related Work uses BibTeX-style citation keys.
- CAND-001 literature expansion: 2026-05-23 novelty-threat pass completed a RelWitness full-PDF skim and registered ZING-3D, Open-World 3DSG-RAG, View-on-Graph, and VIZOR as recent trend/boundary papers. H001 wording should avoid claiming novelty as relation witnesses, geometry evidence, or calibrated witness quality alone.
- CAND-001 next gate: no active main-claim metric blocker. `relative_horizontal` is frozen as appendix/limitation evidence because coordinate-frame ambiguity blocks promotion. `attachment_deferred` is now the preferred future relation-family expansion if H001 is upgraded beyond the current AAAI claim. Docker G0 scope/schema audit through G5c full-source protocol freeze are complete under `experiments/H001_geom_reliability/sources/attachment_deferred/`: it adds 967 GT rows (`attached to` 808, `hanging on` 126, `connected to` 33), expanding the candidate denominator from 2,545 to 3,512 if validated, with VL-SAT 77,748 and Open3DSG 57,300 candidate prediction rows. G5a fits model `h001-attachment-deferred-p-geom-valid-strict-v1`; G5b scores 120 scan-diverse bounded source rows with evidence ready 120/120 and validation errors 0; G5c freezes 69 deterministic full-source shards for 135,048 rows and source-specific denominators: VL-SAT 967/967, Open3DSG 768/967. This is not current metric evidence because full-source scoring, R@K/Violation@K, controls, bootstrap CI, and audit have not run. The Open3DSG R1 exact non-avg downstream branch is regenerated under `experiments/H001_geom_reliability/sources/open3dsg/non_avg/`: raw stream 19,162 rows / 377 batches, identity/export/geometry/metrics/bootstrap/Table 6-caveat report all ready. For the historical 127-scan comparison, the existing avg-BLIP route remains stronger on train-dev loss (`0.32881081104278564` vs non-avg `0.5724539160728455`); the paper-facing primary Open3DSG route is now the full-validation 548/548 recovery branch. R2 H001 covered-context retry toward `388/388` remains optional; attachment G5d remains after those decisions. Main AAAI claim expansion beyond current H001 families still requires explicit final user confirmation. Qwen-VL remains deferred until GPU runtime is acceptable, then resumes from shard 0014 as a third-source extension. Docker `paper/aaai/` PDF build is verified with `h001-aaai-tex:20260526`; latest rebuild log `logs/h001_aaai_pdf_build_full_validation_20260605_100108.log` exits 0, and `main.pdf` builds to 9 total pages with technical content on pages 1-7, references on page 8, and the AAAI reproducibility checklist on page 9. The AAAI source now uses the official AAAI-26 Author Kit checked on 2026-05-27 KST; no official AAAI-27 kit is confirmed. The manuscript treats Open3DSG as the main open-vocabulary relation-source case study and VL-SAT as a controlled reproduced anchor.
- CAND-001 AAAI reviewer-defense pass: the AAAI source now answers the hand-coded-verifier, geometry-only/distance, recall-tradeoff, Open3DSG recovery-policy, family-selection, and AAAI-relevance attacks for the selected full-validation route while preserving the scoped relation-reliability claim.
- CAND-001 reproducibility handoff: `docs/reproducibility.md` is updated with the 2026-05-21 `.gitignore` portability audit, the 2026-05-26 historical 127-scan bundle, and the 2026-06-05 full-validation paper-facing bundle plan. GitHub carries source/runbooks/scripts/compact summaries; the selected checkpoint and row-level full-validation JSONL outputs should be bundled separately, while datasets, feature caches, and model caches remain external or regenerated.
- CAND-001 optional extension: Qwen-VL is now fixed as a third semantic source / modern VLM extension, not a VL-SAT/Open3DSG replacement. Cache verification, Docker runtime preflight, 3-row tiny inference smoke, runtime raw-response validation, full-source promotion protocol, full-source input audit, full-source crop preflight, and full-source inference runner plan are ready; shard 0000 inference is complete and contract-validated as non-metric evidence. Remaining loop run id `20260527_023111` stopped at shard 0014 due to GPU utilization guard, not OOM or parser failure; shards 0000-0013 are complete with 3,500 rows written, and the clean resume point is `qwen_full_source_shard_0014`.
- CAND-001 experiment rule: 논문 본문용 실제 experiment 구현은 Docker 기반으로만 진행하고 host-only output은 paper result로 승격하지 않는다.
- Research target rule: 연구 목표와 방향성은 AI, ML, CV, Robotics top-tier journal/conference를 타겟으로 판단한다.
- CAND-003: `Geometry-Aware Refinement of LLM/VLM Task Reasoning on 3DSG` literature survey / feasibility boundary 정리 완료, hypothesis workflow 승격 여부 판단 대기.

## H001 Status

Facts:

- First prediction baseline is `VL-SAT` / `vlsat_closed_set`.
- Historical hardened 127-scan scope has 127 scans, 388 subgraphs, 25,916 directed pairs, 673,816 prediction rows, 7,505 ground-truth rows, and 2,545 in-scope GT relation instances. It is retained as sensitivity/history, not the current paper-facing denominator.
- Full official validation primary-route metric bundles have 157 scans, 548 contexts,
  36,808 candidate directed pairs, 957,008 expected VL-SAT prediction rows,
  11,254 GT rows, and 3,972 in-scope H001-family GT rows. Docker scope contract
  status is `full_official_validation_scope_contract_ready_no_metric_execution`.
  VL-SAT full-validation metric bundle status is
  `vlsat_full_validation_metric_bundle_ready`: raw dump/export, geometry join,
  metrics, GT verifier eval, and VL-SAT-only bootstrap CI are complete under
  `experiments/H001_geom_reliability/sources/vlsat/full_validation/`.
  Open3DSG full-validation metric bundle status is
  `open3dsg_full_validation_recovery_relaxed_views_min2_metric_bundle_ready`:
  recovery preprocess/features cover 548/548 contexts, raw stream writes 26,938
  rows with exit `0`, adapter exports 695,916 predictions, and geometry join,
  metrics/controls, bootstrap CI, failure rows, and table/caveat report are
  complete. VL-SAT full-validation failure taxonomy is ready with 59,841 rows
  and 36 qualitative cases; Open3DSG recovery failure taxonomy is ready with
  82,155 rows and 36 qualitative cases. This route is the selected paper-facing primary Open3DSG
  full-validation evidence; AAAI tables/prose and appendix provenance have been
  regenerated from the full-validation branch.
- VL-SAT full-validation `semantic_only`: R@50/R@100 0.9272/0.9635, Violation@50/@100 0.0268/0.0476.
- VL-SAT full-validation `probabilistic_recalibrated`: R@50/R@100 0.9305/0.9688, Violation@50/@100 0.0229/0.0404.
- VL-SAT full-validation `family_specific_p_geom_valid`: R@50/R@100 0.9288/0.9683, Violation@50/@100 0.0206/0.0333.
- Full-validation GT-based verifier evaluation: GT positives 3,972, GT-derived negatives 3,972, positive nonviolated 0.9965, negative nonsatisfied 0.9673, `p_geom_valid` AUROC/AUPRC 0.9772/0.9729.
- Structured audit: 250/250 labels, strict invalid-only precision 0.7133, quality-issue precision 0.8933.
- Reduced visual sanity check: 50/50 labels, reviewer id `yhkim`, status `ready_sanity_pass`, target quality-issue rate 0.9333, contradiction rate 0.0333.
- FROSS is runtime-blocked and does not cover `proximity` / `relative_vertical`.
- Open3DSG covers `support_contact`, `proximity`, and `relative_vertical` and is now the manuscript's main open-vocabulary relation-source case study within measured H001 families.
- `relative_horizontal` is tracked as a separate expansion candidate, not part of the current claim. Docker scope audit status is `relative_horizontal_scope_audit_ready_no_metric_execution`: 3,570 candidate GT rows, expanded candidate denominator 6,115/7,505 if validated, labels `left/right/front/behind` = 1,132/1,132/653/653, source rows VL-SAT 103,664 and Open3DSG 76,400, current verification status unsupported. Docker coordinate audit status is `relative_horizontal_coordinate_audit_blocked_no_metric_execution`: best frame `scan_left_neg_x_front_neg_y`, macro strict purity 0.7725, strict eligible share 0.6403, left/right purity 0.8005, front/behind purity 0.7445, inverse consistency 1.0, wrong-frame gap 0.1231. Docker bucket inspection status is `relative_horizontal_bucket_inspection_ready_no_metric_execution`: `front`/`behind` match:contradiction 2.9143, sign-only purity 0.7491, ambiguity flags `axis_margin_ambiguous` 230 / `conflicting_axis_dominates` 430 / `strong_projected_overlap` 44, recommendation `do_not_promote_relative_horizontal_to_main_claim`. This is not metric evidence and does not change the current claim.
- `attachment_deferred` is tracked as the preferred future physical-relation expansion, not part of the current claim. Docker scope/schema audit, extractor contract, evidence-only dry run, point/surface estimator validation, verifier-policy design, train-dev calibration/counterfactual route, G4 GT policy smoke, G4b error/visual sanity planning, G4c strict-only calibration-filter freeze, G5a pooled calibration fit, G5b bounded source scoring preflight, and G5c full-source protocol freeze are ready; current status is `attachment_deferred_full_source_protocol_frozen_no_metrics`. Current denominator policy records 967 GT rows: `attached to` 808, `hanging on` 126, and `connected to` 33. Source rows exist for VL-SAT 77,748 and Open3DSG 57,300, and both are currently verification-unsupported. G5c freezes 69 shards for 135,048 rows and source-specific covered denominators: VL-SAT 967/967 and Open3DSG 768/967. No full-source scoring, source metrics, controls, bootstrap CI, or completed visual audit exists yet. `connected to` dev absence must be handled by pooled calibration or an explicit caveat.
- Docker experiment root `experiments/H001_geom_reliability/` has generated Table 1-6, `manifest.lock.json`, `report.md`, figure specs, Open3DSG metric artifacts, real failure rows, qualitative case queue, and qualitative inspection.
- Qwen-VL is staged only as a third semantic source / modern VLM extension: input/output contract, parser skeleton, 30-row non-held-out tiny pilot, model-lock plan, 30/30 pair crops, Qwen3-VL-4B cache verification, runtime preflight, 3-row tiny inference smoke, raw-response validation, full-source promotion plan, full-source input audit, full-source crop preflight, and full-source inference runner plan are ready. Current Qwen input audit has 77,748 universe rows, 33,384 inferable input rows, 44,364 missing rows, and 134 shards; crop preflight verifies 11,128 unique pair crops for those rows; shards 0000-0013 inference completed with 3,500 parsed rows, and remaining resume starts from shard 0014 after GPU guard is acceptable. This is not metric evidence.
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
- Open3DSG R1 official non-avg BLIP full training completed with exit `0`; Docker checkpoint selection selected `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt` by train-dev `val/loss=0.5724539160728455`, before selected-route H001 held-out inspection. The regenerated non-avg branch is ready under `sources/open3dsg/non_avg/`, with semantic_only R@50/R@100 `0.4310/0.5320`, Violation@50/@100 `0.1395/0.1256`, and probabilistic_recalibrated R@50/R@100 `0.3945/0.5639`, Violation@50/@100 `0.0570/0.0782`. Because non-avg train-dev loss is worse than avg-BLIP by `+0.24364310503005981`, the historical 127-scan comparison keeps avg-BLIP as the stronger route; current paper-facing Open3DSG tables have been regenerated from the full-validation 548/548 recovery branch.
- Historical Open3DSG H001 eval feature cache is complete for the covered loadable scope: 377/377 complete feature ids, with `validation_missing_preprocessed:11` retained as a 127-scan branch caveat.
- Open3DSG raw dump `raw_dump/raw.jsonl` has 19,162 rows and passed Docker raw-dump identity. Clean v14 streaming same-path resume completed with exit `0`, wrote 377/377 completed batches and 19,162 rows, and its SHA256 matches `raw_dump/raw.jsonl`; earlier exit-137 attempts remain historical run records.
- Open3DSG adapter, geometry join, metric eval, and Table 6 are ready: 496,600 prediction rows, 496,600 geometry rows, 114,600 geometry-checkable rows, and no metric blockers.
- Historical Open3DSG 127-scan key metrics: semantic_only R@50/R@100 0.3945/0.4963, Violation@50/@100 0.1326/0.1195; probabilistic_recalibrated R@50/R@100 0.3843/0.5580, Violation@50/@100 0.0575/0.0803; rule_verified_point_subtype R@50/R@100 0.4149/0.5238, Violation@50/@100 0.0/0.0; family_specific control R@50/R@100 0.4530/0.5984, Violation@50/@100 0.0228/0.0311.
- Historical Open3DSG 127-scan qualitative inspection is ready: 36 selected cases, 23 demoted by geometry-aware reranking, 13 promoted or retained, 10 rule-violated cases with `p_geom_valid > 0.9`, and no taxonomy change. Current paper-facing full-validation qualitative evidence instead uses the VL-SAT and Open3DSG recovery 36-case queues recorded under each `full_validation/` source root. These are reviewer-defense evidence, not representative visual audits.
- Historical Open3DSG 127-scan paper caveat wording is ready in `paper_caveats/`: filtered train 3,744/3,852 subgraphs, train-dev validation 156/160 subgraphs, H001 covered loadable scope 377/388 contexts with `validation_missing_preprocessed:11`, averaged-BLIP variant, exact-label 2,545-row H001-family denominator, and residual calibration risk. Current full-validation wording must instead use the selected official non-avg checkpoint, 548/548 recovery policy, exact-label 3,972-row H001-family denominator, 533/548 sensitivity branch, and residual calibration risk.
- Paper workspace, preview, progress rationale, outline, risk register, appendix/provenance plan, and first-pass draft are ready: `paper/README.md` maps paper file roles, `paper/preview.md` summarizes current results and recovery files, `paper/progress.md` explains why each hypothesis/experiment stage was run and why the next stage was needed, `paper/outline.md` fixes the English/Korean paper skeleton, recommended title, title alternatives, three contribution statements, abstract skeleton, Introduction logic, evidence placement, reviewer-defense map, caveat placement, and manuscript-ready table/figure caption drafts, `paper/risk.md` tracks reviewer-risk mitigation, `paper/appendix.md` records calibrator/threshold provenance and caveat consistency, and `paper/draft.md` contains first-pass manuscript prose from Title through Conclusion. Cross-source results and failure analysis are empirical validation, not a fourth contribution.

Inference:

- H001 is promising as a scoped top-tier direction.
- Current evidence supports a cross-source reliability-layer claim within measured H001 families across `VL-SAT` and Open3DSG.
- Broad open-vocabulary 3DSSG improvement claims remain blocked beyond the measured H001-family scope. The train/validation filtering, selected-checkpoint provenance, recovery-policy branch, residual calibration risk, historical covered loadable scope caveat, and any reduced/pilot-only route are fixed as scope limitations.

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
- `docs/experiments.md`: Docker experiment workflow와 paper-result promotion 규칙
- `docs/paper.md`: paper framing과 novelty/reviewer-defense 기준
- `docs/reproducibility.md`: H001 데이터, checkpoint, Docker, 재현 명령, artifact/evaluation 요약
- `literature/README.md`: field map, trend synthesis, cross-paper insights
- `literature/PAPER.md`: paper registry와 reading queue
- `literature/Contribution Candidates.md`: 기여 후보 목록
- `literature/CAND-001.md`: CAND-001 세부 문제 설정과 feasibility
- `literature/CAND-003.md`: CAND-003 literature survey와 feasibility boundary
- `hypothesis/README.md`: hypothesis index
- `hypothesis/CAND-001/H001_geometry-grounded-verification/`: active H001 canonical files, tools, and artifacts
- `paper/README.md`: paper workspace file-role map and update rules
- `paper/preview.md`: paper writing phase 직전의 현재 결과 총정리와 재시작 시 필수 파일 목록
- `paper/progress.md`: hypothesis-to-experiment progression rationale and result interpretation
- `paper/outline.md`: 영어/한국어 paper skeleton, section별 evidence placement, reviewer-defense, figure/table plan
- `paper/draft.md`: Title through Conclusion first-pass manuscript prose
- `paper/risk.md`: reviewer-risk register and mitigation tracker
- `paper/appendix.md`: appendix/supplement provenance table and caveat consistency pass
- `paper/aaai/`: current AAAI-style LaTeX manuscript source using official AAAI-26 Author Kit style files checked on 2026-05-27 KST
- `paper/iccv/`: historical ICCV-style LaTeX manuscript source using vendored ICCV/CVF style files
- `paper/figures.md`: Figure 1-3 source lock, exact values, case IDs, and caption constraints
- `paper/generated/figures/`: verified draft Figure 1-3 SVGs and generation manifest

## Working Principle

작게 시작한다. Full baseline reproduction보다 먼저, 3DSSG / 3RScan에서 geometry-checkable predicate subset을 대상으로 relation edge evidence, verifier, subtype-aware support/contact consistency signal을 확인한다.

현재 만든 experiment 구조:

- `experiments/H001_geom_reliability/`
- `paper/README.md`: paper workspace file-role map
- `paper/preview.md`: paper writing phase 직전의 현재 결과 총정리와 재시작 시 필수 파일 목록
- `paper/outline.md`: paper skeleton과 한국어 병기 outline
- `paper/draft.md`: first-pass manuscript prose
- `paper/risk.md`: reviewer-risk register
- `paper/appendix.md`: appendix/supplement provenance table and caveat consistency pass
- `paper/aaai/`: current AAAI-style LaTeX source conversion
- `paper/iccv/`: historical ICCV-style LaTeX source conversion
- `paper/figures.md`: Figure 1-3 source lock
- `paper/generated/figures/`: draft Figure 1-3 SVGs

아직 만들지 않는 구조:

- `decisions/`
