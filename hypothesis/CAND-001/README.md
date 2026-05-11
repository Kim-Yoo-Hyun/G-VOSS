# CAND-001 Hypotheses

Last updated: 2026-05-10

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
- Baseline-agnostic and broad open-vocabulary 3DSSG improvement claims require second-source adapter evidence.
- For the top-tier main path, second-source adapter evidence from Open3DSG is preferred over single-baseline-only justification.
- `Qwen2.5-VL` or `Qwen3-VL` is allowed as an additional modern-VLM semantic-source extension, but not as a replacement for the Open3DSG reproduction anchor.
- Qwen-VL contract-only input/output JSONL schema, parser skeleton, 30-row non-held-out tiny pilot scope, model-lock plan, and 30/30 rendered pair crops are ready under `experiments/H001_geom_reliability/sources/qwen_vl/`; no Qwen model download or inference has started.
- `SceneFun3D` / `FunGraph3D` is allowed only as an optional robotics/functionality expansion with a separate verifier contract and claim boundary.
- Dockerized Open3DSG checkpoint reproduction plan is ready under `experiments/H001_geom_reliability/sources/open3dsg/`, with official train split counts, H001 eval counts, dependency pins, dataset/cache mounts, training/evaluation commands, and failure budget.
- Open3DSG failure-analysis schema is locked before metric inspection under `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis/`; the taxonomy has 14 primary categories and 6 aggregation table specs. Docker `open3dsg_failure_generator_smoke` generated 6 synthetic rows with 0 validation errors under `experiments/H001_geom_reliability/sources/open3dsg/failure_analysis_generator_smoke/`. Real failure rows are blocked until Open3DSG prediction JSONL, GT join, geometry join, and metric outputs exist.
- Open3DSG `training_repro` metadata/split and full payload staging are complete with H001 held-out overlap 0/0. Runtime train/validation splits are explicitly filtered to preprocessed-ready rows.
- Protected Open3DSG feature dump reaches feature writing. Docker `open3dsg_post_dump_handoff` last recorded 1131/3900 complete feature ids, 29.00%, and status `waiting_for_feature_dump_completion`; it also freezes `feature_audit -> train_pilot -> train_full -> eval/raw dump -> adapter/metric/failure-analysis` gates. Restart policy uses lazy dataset loading, pre-forward skip-existing resume, deterministic no-shuffle dump iteration, no-grad dump, explicit `--epochs 1`, `workers=0`, and a stable official feature run dir. Reduced TopK1/scales1 route is checkpoint-smoke-only.
- Open3DSG checkpoint provenance/selection template is frozen under `experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection/`; current status is `checkpoint_selection_template_ready_checkpoint_missing` with blockers `no_checkpoint_candidates` and `official_feature_audit_not_ready:blocked`. It forbids primary checkpoint selection using H001 held-out metrics or failure inspection.
- Open3DSG raw-dump identity checklist is frozen under `experiments/H001_geom_reliability/sources/open3dsg/raw_dump_identity/`; current status is `raw_dump_identity_checklist_ready_raw_dump_missing`, with fixed identity scope 127 scans / 388 contexts / 25,916 directed pairs and blocker `missing_raw_dump`.
- Open3DSG metric-scope policy is frozen under `experiments/H001_geom_reliability/sources/open3dsg/metric_scope/`; current status is `metric_scope_policy_ready_no_metric_execution`, with in-scope GT denominator 2,545 rows across support_contact 1,199 / proximity 1,128 / relative_vertical 218. Recall matching remains predicate-label exact; filtered-train and covered-scope caveats are fixed before metric execution.
- Open3DSG metric/join contract is frozen under `experiments/H001_geom_reliability/sources/open3dsg/metric_join_contract/`; current status is `blocked_runtime_inputs_missing` because real Open3DSG prediction JSONL and geometry verification JSONL are missing. H001 GT JSONL is present with 7,505 rows. Docker table builder now writes `sources/open3dsg/table6_hook.json` and keeps Open3DSG Table 6 blocked until real ready metrics exist. This is contract evidence only, not metric evidence.

## Candidate-Level Risks

- `3DSSG` relation labels may be noisy or too coarse for geometry-consistency evaluation.
- Coordinate-frame handling still limits relative horizontal claims.
- A geometry verifier may lower violations by removing valid semantic relations if the operating point is too strict.
- FROSS is runtime-blocked and support/contact-only for H001.
- Open3DSG covers all target families at source-contract level; since the inspected official links do not expose a trained checkpoint, the selected expansion direction is Dockerized checkpoint reproduction by us.

## Next Gate

- Restart/monitor Open3DSG `dump_features_3rscan` official BLIP TopK5/scales3 run under the hardened resume policy.
- `VL-SAT` table/report reproduction is complete in `experiments/H001_geom_reliability/`.
- Add Open3DSG checkpoint reproduction and second-source adapter metrics after official feature dump/audit pass. The metric/join contract and Table 6 hook are already frozen; real metric execution remains blocked until prediction JSONL and geometry verification JSONL exist. Reduced route is allowed only for checkpoint smoke and not for paper-result evidence.
- Convert the synthetic Open3DSG failure-analysis generator to real rows only after Open3DSG predictions, GT join, geometry join, and metrics exist; do not change the locked taxonomy without schema version bump.
- Optional modern extension: Qwen-VL prompt schema, prediction JSONL contract, parser skeleton, tiny pilot scope, model id/revision/local-dir recommendation, and pair-crop rendering are fixed; only add Docker runtime smoke after explicit model-cache/download decision, then export identity-preserving prediction JSONL and metric evidence.
- Optional robotics/functionality expansion: add SceneFun3D/FunGraph3D only if scope expands from spatial relation reliability to functional/affordance relation reliability.
- Do not create additional `experiments/` roots, `paper/`, or `decisions/` yet.
- Continue using Docker-based reproduction as the paper-body experiment rule.
