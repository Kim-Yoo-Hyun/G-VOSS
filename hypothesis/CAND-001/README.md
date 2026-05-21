# CAND-001 Hypotheses

Last updated: 2026-05-21

## Source Candidate

- Candidate: `CAND-001: Geometry-Grounded Open-Vocabulary Relation Graph`
- Source file: `literature/CAND-001.md`
- Recommended formulation: `Geometry-grounded verification and representation of open-vocabulary 3D scene graph relations`

## Candidate Direction

Given object instances and candidate semantic relations in a 3D indoor scene, construct relation edges that store both semantic predicate information and explicit geometry evidence, then verify or refine those relations using geometry-consistency checks.

## Active Hypothesis

| ID | Title | Folder | Status |
| --- | --- | --- | --- |
| H001 | Geometry-grounded verification of open-vocabulary 3DSSG relations | `H001_geometry-grounded-verification/` | Hypothesis-stage evidence and scoped main experiment spec complete |

## H001 Canonical Files

- `01_overview.md`: problem, hypothesis, feasibility, claim boundary, transition gate
- `02_method.md`: evidence schema, rule verifier, calibration, prediction-row join, evaluation protocol
- `03_data_baseline.md`: `3DSSG` / `3RScan` / `VL-SAT` layout, scope, staged payload, fixed input counts
- `04_results.md`: H001-Mini, hardened metrics, G3 controls, evidence lock, GT-based verifier evaluation
- `05_audit.md`: structured audit, reduced 50-row visual sanity check, reviewer/provenance caveat
- `06_second_source.md`: FROSS and Open3DSG source/runtime feasibility, blocked second-source metric path
- `07_experiment_spec.md`: scoped Docker-based main experiment spec, required metrics/tables/figures, acceptance criteria; implemented by `experiments/H001_geom_reliability/`
- `tools/`: hypothesis-stage scripts used to generate smoke-test, calibration, evaluation, audit, and source-readiness artifacts
- `artifacts/`: compact manifests, JSONL outputs, reports, and summaries; large runtime data remains under ignored `local_dataset/`

## Fixed Experiment Plan

`07_experiment_spec.md` already fixes the first scoped experiment design before transition:

- Primary baseline: `VL-SAT` / `vlsat_closed_set`
- Method contribution framing: calibrated geometry-consistency evaluation and re-ranking framework
- Fixed held-out scope: 127 scans, 388 subgraphs, 25,916 directed pairs, 673,816 prediction rows, 7,505 ground-truth rows
- In-scope denominator: 2,545 ground-truth relation instances across `support_contact`, `proximity`, and `relative_vertical`
- Main metrics: R@50/R@100, Violation@50/Violation@100, delta vs `semantic_only`, recall retention, GT-positive/counterfactual verifier metrics, audit precision/sanity summaries
- Main tables: baseline comparison, geometry-ablation/control, verifier GT evaluation, audit summary, claim-scope/limitation table
- Required reproducibility rule: paper-body experiment implementation must be Docker-based; host-only outputs are hypothesis/debug evidence only

## Current Evidence

- Hardened `semantic_only`: R@50/R@100 0.9599/0.9894, Violation@50/@100 0.0247/0.0469
- Hardened `probabilistic_recalibrated`: R@50/R@100 0.9642/0.9921, Violation@50/@100 0.0234/0.0391
- Hardened `family_specific_p_geom_valid`: R@50/R@100 0.9619/0.9914, Violation@50/@100 0.0204/0.0310
- GT-based verifier evaluation: GT positives 2,545, GT-derived negatives 2,545, positive nonviolated 0.9972, negative nonsatisfied 0.9694, AUROC/AUPRC 0.9779/0.9737
- Structured audit: 250/250 labels, strict invalid-only precision 0.7133, quality-issue precision 0.8933
- Reduced visual spot-check: 50/50 labels, reviewer id `yhkim`, status `ready_sanity_pass`, target quality-issue rate 0.9333, contradiction rate 0.0333

## Candidate-Level Assumptions

- `3DSSG` / `3RScan` is the primary benchmark path.
- Official `3DSSG_subset` is the primary split and relation-subgraph source.
- `VL-SAT` / `vlsat_closed_set` is the first prediction-level learned baseline.
- The first reportable claim remains scoped to geometry-consistency reliability for geometry-checkable relation families.
- Baseline-agnostic and broad open-vocabulary 3DSSG improvement claims require evidence beyond the current measured H001-family cross-source result.
- For the top-tier main path, second-source adapter evidence from Open3DSG is preferred over single-baseline-only justification.
- `Qwen2.5-VL` or `Qwen3-VL` is allowed as an additional modern-VLM semantic-source extension, but not as a replacement for the Open3DSG reproduction anchor.
- Qwen-VL contract-only input/output JSONL schema, parser skeleton, 30-row non-held-out tiny pilot scope, model-lock plan, 30/30 rendered pair crops, and Qwen3-VL-4B cache verification are ready under `experiments/H001_geom_reliability/sources/qwen_vl/`; runtime preflight and inference have not started.
- `SceneFun3D` / `FunGraph3D` is allowed only as an optional robotics/functionality expansion with a separate verifier contract and claim boundary.
- Dockerized Open3DSG checkpoint reproduction plan is ready under `experiments/H001_geom_reliability/sources/open3dsg/`, with official train split counts, H001 eval counts, dependency pins, dataset/cache mounts, training/evaluation commands, and failure budget.
- Open3DSG failure-analysis schema is locked before metric inspection under `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis/`; the taxonomy has 14 primary categories and 6 aggregation table specs. Docker `open3dsg_failure_generator_smoke` generated 6 synthetic rows with 0 validation errors under `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis_generator_smoke/`. Docker `open3dsg_failure_generator_real` generated 57,736 real rows with 0 validation errors under `experiments/H001_geom_reliability/sources/open3dsg/failure_rows/`. Docker `open3dsg_failure_case_inspection` generated 36-case qualitative inspection with no taxonomy change and identified 10 rule-violated high-`p_geom_valid` residual calibration-risk cases. Docker `open3dsg_paper_caveats` froze filtered-train, averaged-BLIP, covered-scope, denominator, `validation_missing_preprocessed:11`, and residual calibration-risk wording.
- Open3DSG `training_repro` metadata/split and full payload staging are complete with H001 held-out overlap 0/0. Runtime train/validation splits are explicitly filtered to preprocessed-ready rows.
- Protected Open3DSG feature dump and H001 eval feature-cache generation are complete; H001 eval feature shard loop reached 377/377 covered loadable feature ids. Reduced TopK1/scales1 route remains checkpoint-smoke-only.
- Open3DSG checkpoint provenance/selection is ready under `experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection/`; selected checkpoint is `epoch=13-step=13104.ckpt`, chosen by train-dev `val/loss` before H001 held-out metrics/failure/visual inspection. It forbids primary checkpoint selection using H001 held-out metrics or failure inspection.
- Open3DSG raw-dump identity audit is ready under `experiments/H001_geom_reliability/sources/open3dsg/raw_dump_identity/`; fixed identity scope is 127 scans / 388 contexts / 25,916 directed pairs. `raw_dump/raw.jsonl` has 19,162 rows, and clean v14 streaming same-path resume completed with exit `0` and matching SHA256, so source-process provenance is available. Historical exit-137 attempts stay as run records.
- Open3DSG metric-scope policy is frozen under `experiments/H001_geom_reliability/sources/open3dsg/metric_scope/`; current status is `metric_scope_policy_ready_no_metric_execution`, with in-scope GT denominator 2,545 rows across support_contact 1,199 / proximity 1,128 / relative_vertical 218. Recall matching remains predicate-label exact; filtered-train and covered-scope caveats are fixed before metric execution.
- Open3DSG adapter, geometry join, metric eval, and Table 6 hook are ready. Docker `open3dsg_adapter_raw_dump` exported 496,600 prediction rows, Docker `open3dsg_geometry_join` preserved 496,600/496,600 rows and scored 114,600 geometry-checkable rows, Docker `open3dsg_metric_eval` generated `sources/open3dsg/metrics/metrics.json` with status `ready`, and Docker `table_builder` marks Open3DSG Table 6 `ready`. Claims remain scoped to measured H001 families and closed-set/GT-object setting.

## Candidate-Level Risks

- `3DSSG` relation labels may be noisy or too coarse for geometry-consistency evaluation.
- Coordinate-frame handling still limits relative horizontal claims.
- A geometry verifier may lower violations by removing valid semantic relations if the operating point is too strict.
- FROSS is runtime-blocked and support/contact-only for H001.
- Open3DSG covers all target families at source-contract level; since the inspected official links do not expose a trained checkpoint, the selected expansion direction is Dockerized checkpoint reproduction by us.

## Next Gate

- `VL-SAT` table/report reproduction is complete in `experiments/H001_geom_reliability/`.
- Use the completed Open3DSG second-source metrics for measured H001-family cross-source evidence; report the frozen `paper_caveats/` wording for filtered-train, covered-scope, averaged-BLIP, `validation_missing_preprocessed:11`, exact-label denominator, and residual calibration-risk caveats. Keep historical exit-137 attempts in run records, not final raw-dump caveat wording.
- Paper handoff is ready in `paper/preview.md`, bilingual `paper/outline.md`, and reviewed first-pass `paper/draft.md`; title candidates, three contribution statements, abstract skeleton, Introduction logic, table/figure caption drafts, claim-consistency review, related-work positioning, problem/method formalization, Figure 1-3 asset plan, table/appendix placement, limitation/reviewer-defense prose skeletons, first-pass manuscript prose, and draft claim/evidence review are now fixed, with cross-source results/failure analysis treated as empirical validation. The next drafting step is to source-lock Figure 1-3 claims/assets before drawing. Table 6/Open3DSG caveat compression is deferred until the paper-body logic is stable. Do not change the locked taxonomy without schema version bump.
- Keep the clean v14 streaming raw-dump provenance and earlier exit-137 attempts separated in reproducibility wording.
- Optional modern extension: Qwen-VL prompt schema, prediction JSONL contract, parser skeleton, tiny pilot scope, model id/revision/local-dir recommendation, pair-crop rendering, and model cache are fixed; only add Docker runtime smoke after GPU/RAM pressure is cleared, then export identity-preserving prediction JSONL and metric evidence if the extension becomes part of the paper.
- Optional robotics/functionality expansion: add SceneFun3D/FunGraph3D only if scope expands from spatial relation reliability to functional/affordance relation reliability.
- Do not create additional `experiments/` roots or `decisions/` yet. Keep `paper/` limited to handoff/draft-planning files until manuscript drafting needs a larger structure.
- Continue using Docker-based reproduction as the paper-body experiment rule.
