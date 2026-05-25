# Research Index

Last updated: 2026-05-25

## Status

현재 하네스는 `CAND-001 hypothesis prep`과 `CAND-003 literature survey`를 병렬로 추적한다.

CAND-001 H001은 H001-Mini, hardened `VL-SAT` evaluation, G2 point/subtype join, G3 controls, G4 structured audit, reduced 50-row visual sanity check, G5 baseline feasibility, G6 reportability, FROSS/Open3DSG second-source feasibility, final scoped evidence lock, GT-based verifier evaluation, scoped main experiment implementation spec, Docker scoped experiment result, Open3DSG second-source metric/failure evidence, paper preview, bilingual paper outline, first-pass manuscript draft, Figure 1-3 source lock, verified draft Figure 1-3 generation, top-tier novelty/layout figure review, and ICCV-style LaTeX source conversion까지 완료했다. H001 문서는 `01_overview.md` through `07_experiment_spec.md`의 7개 canonical file로 병합했다.

Facts:

- `07_experiment_spec.md` fixes the scoped experiment plan: fixed inputs, metrics, tables, figures, claim boundary, acceptance criteria, and Docker-based reproducibility rule.
- Hardened `VL-SAT` raw dump/export is ready with 388 subgraphs, 25,916 directed pairs, 673,816 prediction rows, and 7,505 ground-truth rows.
- `probabilistic_recalibrated` improves R@50/R@100 over semantic-only while lowering violation rate.
- GT-based verifier evaluation has GT positives 2,545, GT-derived negatives 2,545, positive nonviolated 0.9972, negative nonsatisfied 0.9694, and `p_geom_valid` AUROC/AUPRC 0.9779/0.9737.
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
- Open3DSG official BLIP TopK5/scales3 feature dump is complete and Docker `feature_audit` passed with 3900/3900 complete feature ids. The non-averaged BLIP projector route failed three checkpoint-pilot attempts with CUDA OOM and produced no checkpoint, so the lower-memory Open3DSG `--avg_blip_emb` route was explicitly labeled as an averaged-BLIP variant.
- Open3DSG avg-BLIP full training completed. Docker checkpoint selection schema `h001_open3dsg_checkpoint_selection_v3` selected `epoch=13-step=13104.ckpt` using train-dev `val/loss` 0.32881081104278564 at step 13103, before H001 held-out raw dump, metrics, failure-analysis, or visual inspection.
- Docker `eval_preflight` passed with the selected checkpoint. H001 held-out eval feature-cache generation is complete for the covered loadable scope: shard loop exit `0`, 377/377 complete feature ids, 1,131 `.pt` files, and known `validation_missing_preprocessed:11` caveat retained. Raw-dump identity, adapter, geometry, metric, and failure-row gates passed. Clean v14 streaming same-path resume completed raw-dump source-process provenance with exit `0`, 377/377 completed batches, 19,162 rows, dropped/invalid partial rows 0/0, and SHA256 matching `raw_dump/raw.jsonl`; earlier exit-137 attempts remain historical run records.
- Open3DSG pre-metric failure-analysis schema is ready under `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis/`: 14 fixed primary categories, fixed assignment priority, 6 aggregation table specs, example rows, and status `failure_analysis_schema_ready_no_metric_run`. The Docker `open3dsg_failure_generator_smoke` skeleton generated 6 synthetic rows across 6 primary categories with 0 validation errors. Docker `open3dsg_failure_generator_real` then generated 57,736 real rows from prediction/GT/geometry/metric joins with 0 validation errors under `failure_rows/`; visual-audit queue rows: 6,162.
- Open3DSG checkpoint provenance/selection is ready under `experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection/`; selected checkpoint is `epoch=13-step=13104.ckpt`, chosen by train-dev `val/loss` before H001 held-out metrics/failure/visual inspection. The policy forbids choosing or changing the primary checkpoint using H001 held-out metrics.
- Open3DSG raw-dump identity audit is ready under `experiments/H001_geom_reliability/sources/open3dsg/raw_dump_identity/`; it fixes the raw-dump identity denominator to 127 scans, 388 contexts, and 25,916 directed pairs. The raw dump has 19,162 rows; clean v14 streaming resume completed with exit `0` and produced the same row set as the canonical raw dump, so downstream identity/adapter/metric gates have clean source-process provenance.
- Open3DSG metric-scope policy is frozen under `experiments/H001_geom_reliability/sources/open3dsg/metric_scope/`; current status is `metric_scope_policy_ready_no_metric_execution`. It fixes the in-scope GT denominator to 2,545 rows across support_contact 1,199 / proximity 1,128 / relative_vertical 218, requires exact predicate-label recall matching, and records filtered-train/covered-scope caveats.
- Open3DSG adapter, geometry join, metric eval, and Table 6 hook are ready. Docker `open3dsg_adapter_raw_dump` exported 496,600 prediction rows, Docker `open3dsg_geometry_join` preserved 496,600/496,600 rows and scored 114,600 geometry-checkable rows, Docker `open3dsg_metric_eval` generated `sources/open3dsg/metrics/metrics.json` with status `ready`, and Docker `table_builder` now marks Open3DSG Table 6 `ready` with no blockers. Key Open3DSG metrics: semantic_only R@50/R@100 0.3945/0.4963, Violation@50/@100 0.1326/0.1195; probabilistic_recalibrated R@50/R@100 0.3843/0.5580, Violation@50/@100 0.0575/0.0803; rule_verified_point_subtype R@50/R@100 0.4149/0.5238, Violation@50/@100 0.0/0.0.
- Paper handoff is ready: `paper/preview.md` summarizes current results, caveats, reviewer-defense map, optional extension boundary, and recovery files; `paper/progress.md` explains the hypothesis-to-experiment progression and result interpretations; `paper/outline.md` contains the English/Korean paper skeleton, recommended title, title alternatives, three contribution statements, abstract skeleton, Introduction logic, section evidence placement, Open3DSG caveat placement, reviewer-defense plan, and manuscript-ready table/figure caption drafts; `paper/draft.md` contains ICCV-style first-pass manuscript prose from Title through Conclusion and claim/evidence review; `paper/iccv/` contains the first ICCV-style LaTeX source conversion using the official ICCV/CVF author-kit route; `paper/figures.md` locks Figure 1-3 sources, exact values, case IDs, and caption constraints; `paper/generated/figures/` contains verified/layout-reviewed draft SVGs. Cross-source results and failure analysis are empirical validation, not a fourth contribution.
- 2026-05-23 literature novelty-threat expansion progressed: RelWitness full-PDF skim and H001 difference matrix are complete, ZING-3D / Open-World 3DSG-RAG / View-on-Graph / VIZOR are registered as recent trend/boundary papers, and `paper/draft.md` now distinguishes relation-witness/calibrated-witness prior art from H001's reproduced calibrated geometry-consistency evaluation/re-ranking claim.
- Qwen-VL optional modern semantic-source extension has frozen input JSON Schema, output JSONL contract, Docker `qwen_vl_contract_validator` parser skeleton, a 30-row non-held-out tiny pilot scope, Docker `qwen_vl_runtime_plan` model-lock output, and Docker-rendered pair crops. Tiny pilot family counts are support_contact/proximity/relative_vertical 10/10/10 with held-out overlap 0; `qwen_vl_pair_crop_render` rendered 30/30 pair crops after adding a shared-view selection gate, and validation parsed 30/30 rows with 0 errors/warnings. Recommended primary runtime model is `Qwen/Qwen3-VL-4B-Instruct` revision `ebb281ec70b05090aa6165b016eac8ec08e71b17` under `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17`. Model cache download completed with exit code 0 and Docker `qwen_vl_cache_verify` reports `model_cache_ready`; Docker `qwen_vl_runtime_preflight` has not been rerun after Open3DSG jobs completed. A 2026-05-23 resource check found current GPU memory above the preflight guard threshold, so inference has not started.

Inference:

- Current CAND-001 gate is no longer blocked on Open3DSG metric, failure-row evidence, raw-dump source-process provenance, qualitative case inspection, final caveat wording, paper preview, paper outline, title candidates, contribution statements, abstract skeleton, Introduction logic, table/figure caption drafts, paper claim-consistency review, related-work positioning, method/problem formalization, Figure 1-3 asset plan, table/appendix placement, limitation/reviewer-defense prose skeletons, first-pass manuscript prose, draft claim/evidence review, Figure 1-3 source lock, draft Figure 1-3 generation, figure layout review, Related Work citation-key replacement, RelWitness full-PDF novelty matrix, recent 2025-2026 final Related Work role decision, draft section-structure decision, draft Section 5 title standardization, draft BibTeX scaffold, Title/Abstract/Introduction fill, front matter quick review, paper-body gap patch, word-budget/table-placement review, or ICCV-style manuscript-source conversion. The next paper task is manuscript-content completion inside `paper/iccv/`; TeX/figure build verification comes after content is fully filled.
- `docs/reproducibility.md` now includes a 2026-05-21 GitHub portability check: runbooks, Dockerfiles/compose files, scripts, reports, compact manifests, table/metric summaries, and paper planning docs can be committed; large `local_dataset/` payloads, checkpoints/features, raw JSONL rows, and model caches are intentionally ignored.
- The method contribution should be framed as calibrated geometry-consistency evaluation and re-ranking, not as a verifier script.
- Current evidence supports a measured cross-source geometry-consistency reliability claim within H001 families across `VL-SAT` and Open3DSG.
- Broad open-vocabulary 3DSSG generation improvement remains out of scope until additional source/task evidence exists.

CAND-003은 2026-04-30 P1 paper intake까지 통해 RieMind, `3D-VCD`, `SayPlan`, `SG-Nav`, `SCOUT/SymSearch`, `3DGraphLLM`, `3D-Mem`의 novelty boundary와 offline verifier/refiner first cut을 정리했다.

## Active Questions

1. `paper/iccv/` 본문 내용이 build 전에 충분히 채워졌는가: section prose, table/figure callouts, captions, Open3DSG caveats, limitations가 scoped H001 claim과 일치하는가?
2. Final Related Work에 들어간 recent boundary citations가 H001의 scoped reliability claim을 흐리지 않는가?
3. Content pass 이후 TeX/figure-conversion build route를 어떻게 둘 것인가: local TeX install, Docker TeX build image, or Overleaf-style external build 중 무엇으로 `paper/iccv/`를 검증할 것인가?
4. H001을 현재 scoped cross-source reliability paper path로 계속 전개할 것인가, 아니면 Qwen-VL/FROSS/functional benchmark extension을 먼저 추가할 것인가?
5. Qwen-VL runtime smoke는 GPU/RAM pressure가 해소된 뒤 `qwen_vl_runtime_preflight` -> `qwen_vl_tiny_inference_smoke` 순서로 통과하는가?
6. Qwen-VL tiny inference output이 frozen output JSONL contract로 parse되고 `parser_status`가 stable하게 유지되는가?
7. Strictly blinded independent audit wording이 필요하면 `reference.jsonl`을 보지 않은 reviewer로 50-row check를 반복할 것인가?
8. CAND-003을 CAND-001의 downstream extension으로 둘 것인가, 독립 thesis 후보로 키울 것인가?

## Current Working Files

- `docs/literature.md`: literature workflow
- `docs/hypothesis.md`: hypothesis workflow
- `docs/paper.md`: paper framing / novelty standard / reviewer-defense rules
- `docs/reproducibility.md`: H001 data/checkpoint/Docker/reproduction runbook
- `literature/README.md`: trend synthesis / cross-paper insights
- `literature/PAPER.md`: paper registry / reading queue
- `literature/Contribution Candidates.md`: contribution candidates
- `literature/CAND-001.md`: CAND-001 details
- `literature/CAND-003.md`: CAND-003 literature survey
- `hypothesis/README.md`: hypothesis index
- `hypothesis/CAND-001/README.md`: CAND-001 hypothesis index
- `hypothesis/CAND-001/H001_geometry-grounded-verification/`: active H001 files
- `experiments/H001_geom_reliability/`: active Docker experiment root
- `paper/preview.md`: paper handoff summary and recovery file list
- `paper/progress.md`: hypothesis-to-experiment progression rationale
- `paper/outline.md`: English/Korean paper outline, title/three-contribution statements, abstract skeleton, Introduction logic, and manuscript-ready caption plan
- `paper/draft.md`: first-pass manuscript prose from Title through Conclusion
- `paper/iccv/`: ICCV-style LaTeX manuscript source; build pending TeX/figure-conversion tooling
- `paper/figures.md`: Figure 1-3 source lock

## Expansion Rule

문헌 조사 결과는 `literature/`에 저장한다. Hypothesis 산출물은 `hypothesis/`에 저장한다. Paper-level framing과 novelty/reviewer-defense 기준은 `docs/paper.md`에 저장한다. 논문 본문용 실제 experiment 구현은 Docker 기반으로만 진행한다. 현재 active experiment root는 `experiments/H001_geom_reliability/`이다. `paper/preview.md`, `paper/outline.md`, `paper/draft.md`, `paper/iccv/`, and `paper/figures.md`는 paper writing handoff/draft planning에만 사용하고, `decisions/` 구조는 아직 만들지 않는다.

Research target rule: 연구 목표와 방향성은 AI, ML, CV, Robotics top-tier journal/conference를 타겟으로 판단한다.
