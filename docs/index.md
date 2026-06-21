# Research Index

Last updated: 2026-06-21 KST

## Docs Directory Usage

`docs/`는 세부 artifact dump가 아니라 repo-wide workflow와 recovery rule을 관리한다. `AGENTS.md`가 상위 agent instruction과 파일 책임을 정하면, `docs/*.md`는 각 workflow의 더 구체적인 사용 규칙과 상태 dashboard를 소유한다. 실제 결과물과 긴 실행 로그는 owning folder의 `README.md`, report, manifest, or `logs/`에 둔다.

Current docs roles:

- `docs/index.md`: current research dashboard. Owns high-level status, active questions, current working files, and expansion rules. It should point to detailed owners instead of copying full runbooks.
- `docs/literature.md`: authoritative literature workflow rulebook. Owns how to perform and store literature review. Actual paper cards, registry, synthesis, and contribution candidates live under `literature/`.
- `docs/hypothesis.md`: authoritative hypothesis workflow rulebook. Owns hypothesis-stage gates, canonical file conventions, smoke-test/audit expectations, and transition criteria. Preserved candidate and H001 records live under `archive/hypothesis_records/hypothesis/`; CAND-001's former candidate README is merged into `archive/hypothesis_records/hypothesis/README.md`.
- `docs/experiments.md`: authoritative Docker experiment workflow rulebook. Owns paper-result promotion gates, source adapter expectations, metric-freeze requirements, and experiment-root creation rules. Actual run status and artifacts live under `experiments/`.
- `docs/paper.md`: paper-framing rulebook. Owns novelty standard, claim boundary, reviewer-defense checklist, and required evidence patterns. `paper/README.md` owns the paper workspace map; manuscript prose and figure/table planning live under `paper/`.
- `docs/reproducibility.md`: H001 reproducibility and recovery runbook. Owns datasets, checkpoints, model/cache paths, Docker commands, artifact bundles, verification commands, handoff, and cleanup safety. Experiment-specific details remain under `experiments/**/README.md` and source-specific reports.

Update rule:

- Add or change stable cross-repo rules in `AGENTS.md`.
- Add workflow-specific rules in the relevant `docs/*.md`.
- Add folder-local commands, status, and artifact details in the folder `README.md` or report files.
- When a durable root-level workflow folder is newly created or activated, add or update its matching `docs/<folder>.md` rulebook and link it here.
- If the same detailed list appears in multiple places, keep the authoritative copy in the most specific owner and replace other copies with a pointer.

## Status

현재 하네스는 CAND-001/H001의 paper/submission package 정리와 `CAND-003 literature survey`를 병렬로 추적한다. Paper-facing name is `GeoCalib: Calibrating Geometric Consistency for Reliable 3D Scene Graph Relations`; `H001` remains the internal hypothesis/experiment identifier.

Current snapshot:

- Main GeoCalib claim remains scoped relation reliability, not broad open-vocabulary 3DSSG generation. The measured main families are `support_contact`, `proximity`, and `relative_vertical`.
- Main evidence route is frozen around VL-SAT full official validation and Open3DSG full-validation `recovery_relaxed_views_min2/` as the main open-vocabulary relation-source case study; the Open3DSG 533/548 route and historical 127-scan routes remain sensitivity/provenance evidence.
- Low-K reporting decision is to expose K = `{5, 10, 20, 50, 100}` where table space and provenance support it; K=1 remains a sanity check only. The current checkout does not expose a tracked low-K result directory, so low-K metric/CI artifacts should be regenerated or restored before final upload/package claims.
- Qwen-VL full official validation downstream is complete as a third-source / modern VLM extension: 157 scans, 548 contexts, 110,424 query rows, 46,506 inferable input rows, 35,131 exported predictions, 32,236 in-scope predictions, 3,972 H001-family GT rows, metrics/controls/bootstrap/failure rows, and 36 deterministic qualitative cases. It remains appendix/extension evidence unless explicitly promoted.
- Latest known paper build is `logs/h001_aaai_pdf_build_geocalib_figure_20260613_104500.log`, exit 0, 9 pages. Older packages generated before GeoCalib/Figure-1 updates should be regenerated before upload.
- H002 active hypothesis branch lives at
  `hypothesis/CAND-001/H002_factorized-relation-confidence/`. It frames
  semantic score / geometry validity mismatch as relation-level reliability.
  Current H002 status: reliability target v5 cell contrast asset packet gap
  audit is complete and ready for label-readiness validation. From the 80-row
  / 40-pair sheet, the audit keeps 72 rows / 36 pairs label-ready, preserves
  hidden role balance `positive_proxy:36` / `negative_proxy:36`, and excludes
  4 pairs (`v5cell_0013`, `v5cell_0014`, `v5cell_0033`, `v5cell_0034`).
  Output path errors, visible leakage hits, and input validation errors are 0.
  Posterior smoke remains blocked. Next step is
  `reliability_target_v5_cell_contrast_label_readiness`.

CAND-001 H001은 H001-Mini, hardened `VL-SAT` evaluation, G2 point/subtype join, G3 controls, G4 structured audit, reduced 50-row visual sanity check, G5 baseline feasibility, G6 reportability, FROSS/Open3DSG second-source feasibility, final scoped evidence lock, GT-based verifier evaluation, scoped main experiment implementation spec, Docker scoped experiment result, Open3DSG second-source metric/failure evidence, paper preview, bilingual paper outline, first-pass manuscript draft, Figure 1-3 source lock, verified draft Figure 1-3 generation, top-tier novelty/layout figure review, ICCV-style source conversion, AAAI-style source conversion, and AAAI reproducibility checklist까지 완료했다. H001 문서는 `01_overview.md` through `07_experiment_spec.md`의 7개 canonical file로 병합했다.

Facts:

- `07_experiment_spec.md` fixes the scoped experiment plan: fixed inputs, metrics, tables, figures, claim boundary, acceptance criteria, and Docker-based reproducibility rule.
- Hardened `VL-SAT` raw dump/export is ready with 388 subgraphs, 25,916 directed pairs, 673,816 prediction rows, and 7,505 ground-truth rows.
- Full official validation is now the paper-facing primary route after the
  complete Docker rerun. Target scope is official `3DSSG_subset` validation:
  157 scans, 548 contexts, 11,254 GT rows, and 3,972 H001-family GT rows.
  VL-SAT full-validation is the controlled-anchor source and Open3DSG
  `recovery_relaxed_views_min2/` is the primary open-vocabulary source. The
  completed 127-scan hardened result remains historical/sensitivity evidence.
  Method provenance must remain train/train-dev-derived; H001-Mini is
  hypothesis/feasibility evidence, not paper metric evidence. Owner:
  `results/h001_geom_reliability/full_validation_transition/report.md`.
  Docker `full_validation_scope_contract` has frozen the scope contract under
  `results/h001_geom_reliability/full_validation_transition/scope_contract/`
  with status
  `full_official_validation_scope_contract_ready_no_metric_execution`;
  additional frozen counts are 36,808 candidate directed pairs and 957,008
  expected VL-SAT prediction rows. VL-SAT full-validation Docker route is
  metric-ready under
  `experiments/H001_geom_reliability/sources/vlsat/full_validation/` with
  status `vlsat_full_validation_metric_bundle_ready`: 157/157 faithful staged
  scans, raw dump `raw_dump_ready`, adapter export, geometry join, metric eval,
  GT verifier eval, and VL-SAT-only bootstrap CI complete. This is VL-SAT
  full-validation metric evidence. VL-SAT full-validation failure-analysis is
  also ready: 59,841 diagnostic rows and a 36-case deterministic qualitative
  inspection queue. Open3DSG full-validation Docker route is ready under
  `experiments/H001_geom_reliability/sources/open3dsg/full_validation/`: the
  original 533/548 branch is retained as the unmodified-source-route
  sensitivity check, while
  `recovery_relaxed_views_min2/` reaches 548/548 contexts, writes 26,938 raw
  rows with clean exit `0`, exports 695,916 prediction rows, preserves 695,916
  geometry rows, and has metrics/controls, bootstrap CI, 82,155 failure rows,
  36-case qualitative inspection, and Table 6/caveat regeneration complete.
  Paper-wide full-validation promotion is already selected; the recovery policy
  must be disclosed.
- `probabilistic_recalibrated` improves R@50/R@100 over semantic-only while lowering violation rate.
- Full-validation GT-based verifier evaluation has GT positives 3,972, GT-derived negatives 3,972, positive nonviolated 0.9965, negative nonsatisfied 0.9673, and `p_geom_valid` AUROC/AUPRC 0.9772/0.9729. The earlier 2,545-row verifier result is retained as historical 127-scan sanity evidence.
- Visual spot-check status is `ready_sanity_pass` with reviewer id `yhkim`, labels 50/50, target quality-issue rate 0.9333, and contradiction rate 0.0333.
- FROSS is runtime-blocked and cannot cover `proximity` or `relative_vertical`.
- Open3DSG covers `support_contact`, `proximity`, and `relative_vertical` at source-contract level; the selected top-tier expansion is Dockerized Open3DSG checkpoint reproduction followed by second-source adapter metrics.
- `experiments/H001_geom_reliability/` is created and Docker-run ready. The Docker table builder generated Table 1-6, figure specs, `manifest.lock.json`, and `report.md` from locked hypothesis artifacts.
- Dockerized Open3DSG checkpoint reproduction plan is ready under `experiments/H001_geom_reliability/sources/open3dsg/`, including official train split counts, H001 eval split counts, dependency pins, dataset/cache mounts, train/eval commands, and failure budget.
- Open3DSG `training_repro` metadata/split staging is ready with no H001 held-out leakage. Full payload staging is complete: train scan dirs/raw/mesh/sequence are 1178/1178, train-dev payload is 30/30, and `open3dsg_train_handoff` status is `ready_for_open3dsg_env_check`.
- Open3DSG Docker env/cache preflight is ready on the cu128 image: torch `2.8.0+cu128`, CUDA device count 1, RTX 5090 `sm_120` supported, and only `torch_hub` remains as a non-blocking cache warning.
- Open3DSG train view staging is complete at 1178/1178 view pickles. `train_preprocess_full` exited 0 but produced 108 missing outputs; all 108 match the source-level `too few visible objects` drop, and a representative Docker retry did not recover the sampled missing targets.
- Open3DSG runtime train split is now explicitly filtered to the preprocessed-ready subset: 1158 scans / 3744 subgraphs / 79,704 relations retained from the official 1178 scans / 3852 subgraphs / 81,190 relations. The 108 removed subgraphs / 1,486 relations are recorded under `train_preprocess_filter/`.
- Open3DSG validation coverage guard is complete: validation views 30/30, runtime validation split 30 scans / 156 subgraphs / 3,696 relations after filtering 4 non-recoverable preprocess drops.
- Open3DSG official BLIP TopK5/scales3 feature dump is complete and Docker `feature_audit` passed with 3900/3900 complete feature ids. The non-averaged BLIP projector route failed three checkpoint-pilot attempts with CUDA OOM, but the later R1 exact non-avg full retry completed with exit `0`.
- Open3DSG avg-BLIP full training completed and remains the stronger historical 127-scan route by train-dev loss. Docker checkpoint selection schema `h001_open3dsg_checkpoint_selection_v4` also selects the official non-avg checkpoint `epoch=13-step=13104.ckpt` from MLflow run `25da9c4c00214f3b880cedbb2a124177` using train-dev `val/loss` 0.5724539160728455 at step 13103, before selected-route H001 held-out raw dump, metrics, failure-analysis, or visual inspection. Route comparison remains unfavorable to non-avg for the historical 127-scan comparison: best avg-BLIP train-dev `val/loss` is 0.32881081104278564. The separate non-avg downstream branch is ready under `experiments/H001_geom_reliability/sources/open3dsg/non_avg/`; the current paper-facing Open3DSG route is the full-validation `recovery_relaxed_views_min2/` branch with explicit recovery-policy caveat.
- Docker `eval_preflight` passed with the selected checkpoint. H001 held-out eval feature-cache generation is complete for the covered loadable scope: shard loop exit `0`, 377/377 complete feature ids, 1,131 `.pt` files, and known `validation_missing_preprocessed:11` caveat retained. Raw-dump identity, adapter, geometry, metric, and failure-row gates passed. Clean v14 streaming same-path resume completed raw-dump source-process provenance with exit `0`, 377/377 completed batches, 19,162 rows, dropped/invalid partial rows 0/0, and SHA256 matching `raw_dump/raw.jsonl`; earlier exit-137 attempts remain historical run records.
- Open3DSG pre-metric failure-analysis schema is ready under `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis/`: 14 fixed primary categories, fixed assignment priority, 6 aggregation table specs, example rows, and status `failure_analysis_schema_ready_no_metric_run`. The Docker `open3dsg_failure_generator_smoke` skeleton generated 6 synthetic rows across 6 primary categories with 0 validation errors. Docker `open3dsg_failure_generator_real` then generated 57,736 real rows from prediction/GT/geometry/metric joins with 0 validation errors under `failure_rows/`; visual-audit queue rows: 6,162.
- Open3DSG checkpoint provenance/selection is ready under `experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection/`; selected checkpoint is `epoch=13-step=13104.ckpt`, chosen by train-dev `val/loss` before H001 held-out metrics/failure/visual inspection. The policy forbids choosing or changing the primary checkpoint using H001 held-out metrics.
- Open3DSG raw-dump identity audit is ready under `experiments/H001_geom_reliability/sources/open3dsg/raw_dump_identity/`; it fixes the raw-dump identity denominator to 127 scans, 388 contexts, and 25,916 directed pairs. The raw dump has 19,162 rows; clean v14 streaming resume completed with exit `0` and produced the same row set as the canonical raw dump, so downstream identity/adapter/metric gates have clean source-process provenance.
- Open3DSG metric-scope policy is frozen under `experiments/H001_geom_reliability/sources/open3dsg/metric_scope/`; current status is `metric_scope_policy_ready_no_metric_execution`. It fixes the in-scope GT denominator to 2,545 rows across support_contact 1,199 / proximity 1,128 / relative_vertical 218, requires exact predicate-label recall matching, and records filtered-train/covered-scope caveats.
- `relative_horizontal` is now a separate scope-expansion validation track under `archive/experiments/H001_geom_reliability/sources/relative_horizontal/`, not part of the current main paper claim. Docker `relative_horizontal_scope_audit` is complete with status `relative_horizontal_scope_audit_ready_no_metric_execution`: 3,570 candidate GT rows, expanded candidate denominator 6,115/7,505, labels `left/right/front/behind` = 1,132/1,132/653/653, source rows VL-SAT 103,664 and Open3DSG 76,400, current verification status unsupported for both sources. `coordinate_frame_protocol.md` is frozen and Docker `relative_horizontal_coordinate_audit` is complete but blocked for promotion: best frame `scan_left_neg_x_front_neg_y`, macro strict purity 0.7725, `front`/`behind` purity 0.7445, inverse consistency 1.0, wrong-frame gap 0.1231. Docker `relative_horizontal_bucket_inspection` is complete and recommends `do_not_promote_relative_horizontal_to_main_claim`: `front`/`behind` match:contradiction 2.9143, sign-only purity 0.7491, and ambiguity flags `axis_margin_ambiguous` 230 / `conflicting_axis_dominates` 430 / `strong_projected_overlap` 44. Current AAAI-path decision is to freeze this as appendix/limitation evidence and not run expanded-family metrics.
- `attachment_deferred` is now the preferred future relation-family upgrade if H001 is expanded beyond the current AAAI claim. It is not current main-claim evidence. Docker G0 scope/schema audit, G1 extractor contract, G1b evidence-only dry run, G1c point/surface estimator validation, G2 verifier-policy design, G3 train-dev calibration/counterfactual route, G4 GT policy smoke, G4b error/visual sanity planning, G4c strict-only calibration-filter freeze, G5a pooled strict calibration fit, G5b bounded source scoring preflight, G5c full-source protocol freeze, and G5d full-source scoring/metrics/controls/bootstrap are complete. G5d status is `attachment_deferred_g5d_full_source_metrics_ready`; log `logs/h001_attachment_g5d_full_20260606_113803.log`; output `archive/experiments/H001_geom_reliability/sources/attachment_deferred/full_source_g5d/`; 69/69 shards, 135,048 scored rows, validation errors 0. Frozen scope: 967 GT rows (`attached to` 808, `hanging on` 126, `connected to` 33), candidate denominator 3,512 if validated, VL-SAT 77,748 candidate prediction rows, Open3DSG 57,300 candidate prediction rows, VL-SAT denominator 967/967, and Open3DSG denominator 768/967 with 199 missing exact-label GT rows. Key G5d results: VL-SAT semantic_only R@100/V@100 `1.0000/0.2126`, probabilistic_recalibrated `0.9979/0.2210`, rule_verified_attachment_policy `0.9380/0.0215`; Open3DSG semantic_only `0.9297/0.3021`, probabilistic_recalibrated `0.6628/0.2460`, rule_verified_attachment_policy `0.9245/0.0842`. Warning: `connected to` has no dev strict rows. Owner: `archive/experiments/H001_geom_reliability/sources/attachment_deferred/README.md`.
- Historical 127-scan Open3DSG adapter, geometry join, metric eval, and Table 6 hook are ready. Docker `open3dsg_adapter_raw_dump` exported 496,600 prediction rows, Docker `open3dsg_geometry_join` preserved 496,600/496,600 rows and scored 114,600 geometry-checkable rows, Docker `open3dsg_metric_eval` generated `sources/open3dsg/metrics/metrics.json` with status `ready`, and Docker `table_builder` marks that historical Table 6 route `ready` with no blockers. Key historical Open3DSG metrics: semantic_only R@50/R@100 0.3945/0.4963, Violation@50/@100 0.1326/0.1195; probabilistic_recalibrated R@50/R@100 0.3843/0.5580, Violation@50/@100 0.0575/0.0803; rule_verified_point_subtype R@50/R@100 0.4149/0.5238, Violation@50/@100 0.0/0.0.
- Open3DSG caveat-reduction plan is frozen under `experiments/H001_geom_reliability/sources/open3dsg/caveat_reduction_plan/` with status `open3dsg_caveat_reduction_plan_frozen_no_execution`. R1 exact non-averaged BLIP retry is complete, selected, and downstream-regenerated. Non-avg key metrics: semantic_only R@50/R@100 0.4310/0.5320, Violation@50/@100 0.1395/0.1256; probabilistic_recalibrated R@50/R@100 0.3945/0.5639, Violation@50/@100 0.0570/0.0782; rule_verified_point_subtype R@50/R@100 0.4507/0.5481, Violation@50/@100 0.0/0.0; family_specific control R@50/R@100 0.4750/0.6047, Violation@50/@100 0.0243/0.0310. R2 covered-loadable H001 context retry is also complete at `388/388`; downstream metrics/bootstrap/table-caveat refresh and Docker provenance review are ready under `experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery/`, and clean-return raw files are row/predicate-score equivalent to the canonical R2 raw dump after excluding run metadata. The plan records attachment Open3DSG missing exact-label GT rows as 199 total: 23 from missing preprocessed H001 contexts and 176 from absent Open3DSG candidate pairs, so `388/388` can only partially improve attachment coverage.
- Paper workspace is ready: `paper/README.md` maps the paper folder roles; `paper/preview.md` summarizes current results, caveats, reviewer-defense map, optional extension boundary, and recovery files; `paper/progress.md` explains the hypothesis-to-experiment progression and result interpretations; `paper/outline.md` contains the English/Korean paper skeleton, recommended title, title alternatives, three contribution statements, abstract skeleton, Introduction logic, section evidence placement, Open3DSG caveat placement, reviewer-defense plan, and manuscript-ready table/figure caption drafts; `paper/draft.md` contains first-pass manuscript prose from Title through Conclusion and claim/evidence review; `paper/risk.md` tracks reviewer-risk mitigation; `paper/appendix.md` records calibrator/threshold provenance, Open3DSG caveat consistency, Figure 3 optionality, and Qwen-VL extension boundary; `paper/aaai/` contains the current AAAI-style LaTeX source with Open3DSG-first main source-results table, a references-after checklist, and official AAAI-26 Author Kit style files checked on 2026-05-27 KST; `archive/paper/iccv/` remains a historical/alternate ICCV-style source; `paper/figures.md` locks Figure 1-3 sources, exact values, case IDs, and caption constraints; `paper/generated/figures/` contains verified/layout-reviewed draft SVGs. Cross-source results and failure analysis are empirical validation, not a fourth contribution.
- 2026-05-23 literature novelty-threat expansion progressed: RelWitness full-PDF skim and H001 difference matrix are complete, ZING-3D / Open-World 3DSG-RAG / View-on-Graph / VIZOR are registered as recent trend/boundary papers, and `paper/draft.md` now distinguishes relation-witness/calibrated-witness prior art from H001's reproduced calibrated geometry-consistency evaluation/re-ranking claim.
- Qwen-VL is fixed as a third semantic source / modern VLM extension, not a VL-SAT/Open3DSG replacement. The full official validation downstream route is complete with parser validation, adapter export, geometry join, metrics/controls, bootstrap CI, 31,881 failure rows, and 36 deterministic qualitative cases. Key metrics: semantic_only R@50/R@100 `0.2815/0.3600`, V@50/@100 `0.1226/0.1246`; probabilistic_recalibrated `0.3215/0.3653`, V `0.0795/0.1166`; rule_verified_point_subtype `0.3009/0.3630`, V `0.0/0.0`; family_specific `0.3379/0.3653`, V `0.0510/0.1113`. Treat this as appendix/extension evidence unless the main claim is explicitly widened.

Inference:

- Current CAND-001 gate is no longer blocked on main-source metrics, failure-row evidence, qualitative inspection, reviewer-risk framing, Figure 1 generation, Qwen extension downstream metrics, or paper build. Remaining work is submission hygiene: portal/form verification, artifact URL/DOI and supplementary policy, checklist answer pass, release/package regeneration after GeoCalib/Figure-1 changes, and low-K provenance sync if low-K rows stay in the paper.
- `docs/reproducibility.md` now includes a 2026-05-21 GitHub portability check, the historical 2026-05-26 127-scan bundle, the 2026-06-05 full-validation paper-facing bundle plan, and cleanup guidance: runbooks, Dockerfiles/compose files, scripts, reports, compact manifests, table/metric summaries, and paper planning docs can be committed; selected checkpoint and full-validation row-level JSONL outputs are bundled separately; large `local_dataset/` payloads, feature caches, and model caches remain intentionally ignored, transferred, or regenerated.
- The method contribution should be framed as calibrated geometry-consistency evaluation and re-ranking, not as a verifier script.
- Current evidence supports a measured cross-source geometry-consistency reliability claim within H001 families across `VL-SAT` and Open3DSG.
- The preferred next strengthening step is now paper polish/artifact release
  preparation, not another full-validation rerun. VL-SAT full-validation metric
  and failure-analysis bundle is ready
  under `experiments/H001_geom_reliability/sources/vlsat/full_validation/`:
  957,008 prediction rows, 11,254 GT rows, 3,972 H001-family GT rows, metric
  status `ready`, GT verifier AUROC `0.9772`, bootstrap warnings `0`, failure
  rows 59,841, and qualitative cases 36. Open3DSG full-validation metric and
  failure-analysis bundle is ready under
  `experiments/H001_geom_reliability/sources/open3dsg/full_validation/`:
  primary recovery branch 695,916 prediction rows, 548 covered batches, 3,972
  H001-family GT rows, metric status `ready`, bootstrap status `ready`,
  failure rows 82,155, qualitative cases 36, and explicit caveats for the
  selected non-avg BLIP route plus recovery-policy preprocess/view changes. The
  original 533/548 branch remains sensitivity evidence.
- Broad open-vocabulary 3DSSG generation improvement remains out of scope until additional source/task evidence exists.

CAND-003은 2026-04-30 P1 paper intake까지 통해 RieMind, `3D-VCD`, `SayPlan`, `SG-Nav`, `SCOUT/SymSearch`, `3DGraphLLM`, `3D-Mem`의 novelty boundary와 offline verifier/refiner first cut을 정리했다.

## Active Questions

1. Full-validation result와 recovery-policy caveat가 AAAI main text, appendix, Table 6, and reproducibility checklist에서 일관되게 유지되는가?
2. Final Related Work에 들어간 recent boundary citations가 H001의 scoped reliability claim을 흐리지 않는가?
3. Full-validation artifact bundle을 Google Drive/Zenodo/HF Dataset 중 어디에 올리고, 공개 bundle의 checksum/verification command를 어떻게 고정할 것인가?
4. `attachment_deferred` G5d 결과를 main claim에 넣을지, appendix/future-upgrade evidence로 둘지 판단하기 전에 failure/visual audit이 필요한가?
5. Qwen-VL을 third semantic source로 계속 밀 경우, remaining shard loop를 언제 background job으로 실행하고 어떻게 검증할 것인가?
6. Qwen-VL full-source outputs가 frozen output JSONL contract로 parse되고 `parser_status`가 stable하게 유지되는가?
7. Strictly blinded independent audit wording이 필요하면 `reference.jsonl`을 보지 않은 reviewer로 50-row check를 반복할 것인가?
8. CAND-003을 CAND-001의 downstream extension으로 둘 것인가, 독립 thesis 후보로 키울 것인가?

## Current Working Files

- `docs/literature.md`: literature workflow
- `docs/hypothesis.md`: hypothesis workflow
- `docs/experiments.md`: Docker experiment workflow and paper-result promotion rules
- `docs/paper.md`: paper framing / novelty standard / reviewer-defense rules
- `docs/reproducibility.md`: H001 data/checkpoint/Docker/reproduction runbook
- `src/README.md`: core executable code map
- `configs/README.md`: Docker/compose configuration map
- `scripts/README.md`: shell wrapper map
- `literature/README.md`: trend synthesis / cross-paper insights
- `literature/PAPER.md`: paper registry / reading queue
- `literature/Contribution Candidates.md`: contribution candidates
- `literature/CAND-001.md`: CAND-001 details
- `literature/CAND-003.md`: CAND-003 literature survey
- `archive/hypothesis_records/hypothesis/README.md`: hypothesis index
- `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/`: active H001 files
- `hypothesis/CAND-001/H002_factorized-relation-confidence/`: active H002 factorized relation reliability hypothesis branch
- `experiments/H001_geom_reliability/`: active Docker experiment root
- `results/h001_geom_reliability/`: compact paper-facing H001 tables, reports, manifests, and figure specs
- `archive/README.md`: archived/superseded/optional material map
- `paper/README.md`: paper workspace map and file roles
- `paper/preview.md`: paper handoff summary and recovery file list
- `paper/progress.md`: hypothesis-to-experiment progression rationale
- `paper/outline.md`: English/Korean paper outline, title/three-contribution statements, abstract skeleton, Introduction logic, and manuscript-ready caption plan
- `paper/draft.md`: first-pass manuscript prose from Title through Conclusion
- `paper/risk.md`: reviewer-risk register and mitigation tracking
- `paper/appendix.md`: appendix/supplement provenance table, caveat consistency pass, and optional extension boundary
- `paper/aaai/`: current AAAI-style LaTeX manuscript source
- `archive/paper/iccv/`: historical ICCV-style LaTeX manuscript source
- `paper/figures.md`: Figure 1-3 source lock

## Expansion Rule

문헌 조사 결과는 `literature/`에 저장한다. Hypothesis records are stored under `archive/hypothesis_records/hypothesis/`. Executable code lives under `src/`, Docker/compose entry points under `configs/`, compact paper-facing outputs under `results/`, and superseded/optional material under `archive/`. Paper-level framing과 novelty/reviewer-defense 기준은 `docs/paper.md`에 저장한다. 논문 본문용 실제 experiment 구현은 Docker 기반으로만 진행한다. 현재 active experiment root는 `experiments/H001_geom_reliability/`이다. `paper/README.md`, `paper/preview.md`, `paper/outline.md`, `paper/draft.md`, `paper/appendix.md`, `paper/aaai/`, `archive/paper/iccv/`, `paper/figures.md`, and `paper/risk.md`는 paper writing handoff/draft planning에 사용하고, `decisions/` 구조는 아직 만들지 않는다.

Research target rule: 연구 목표와 방향성은 AI, ML, CV, Robotics top-tier journal/conference를 타겟으로 판단한다.
