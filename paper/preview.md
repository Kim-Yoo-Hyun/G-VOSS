# H001 Paper Preview

Last updated: 2026-05-19 KST

이 문서는 H001을 paper/experiment writing phase로 넘기기 직전에 현재까지의 연구 결과, 주장 범위, 실험 근거, caveat, 그리고 재시작 시 반드시 읽어야 할 파일을 한곳에 고정한 preview다. 최종 manuscript가 아니라 paper draft를 쓰기 위한 handoff 문서다.

## Paper Direction

Fact:

- Active candidate: `CAND-001 / H001_geometry-grounded-verification`.
- Method framing: calibrated geometry-consistency evaluation and re-ranking framework for 3D scene graph relation predictions.
- Main relation families: `support_contact`, `proximity`, `relative_vertical`.
- Main prediction sources with completed metric evidence: `VL-SAT` and Open3DSG.
- Paper-body experiment rule: paper-result experiments must be Docker reproducible.

Inference:

- The strongest current paper path is a scoped cross-source reliability-layer paper, not a broad open-vocabulary 3DSSG SOTA paper.
- Novelty should be framed around a failure mechanism: semantic relation predictors can rank plausible relations without calibrating them to relation-level physical consistency.
- The method contribution is not "a verifier script"; it is a calibrated geometry-consistency evaluation/re-ranking framework with metrics, calibration variants, controls, denominator accounting, and failure analysis.

Allowed current claim:

```text
For geometry-checkable 3D scene graph relation families, calibrated geometry-consistency scoring exposes semantically plausible but physically inconsistent relation predictions and can reduce geometric violations while preserving measurable recall tradeoffs across VL-SAT and Open3DSG.
```

Blocked current claim:

```text
This is a broad open-vocabulary 3DSSG generation improvement or arbitrary-baseline general method.
```

## Current Evidence Summary

Fact:

- Fixed H001 held-out scope has 127 scans, 388 subgraphs, 25,916 directed pairs, 673,816 `VL-SAT` prediction rows, 7,505 GT rows, and 2,545 in-scope H001-family GT relations.
- Docker experiment root: `experiments/H001_geom_reliability/`.
- Docker table builder generated Table 1-6, figure specs, `manifest.lock.json`, and `report.md`.
- Open3DSG second-source path is complete for the measured H001-family setting: checkpoint reproduction, H001 eval features, raw dump identity, clean v14 streaming raw-dump provenance, adapter export, geometry join, metric eval, Table 6 hook, real failure rows, qualitative case inspection, and paper caveat wording.

## Key Metrics

### VL-SAT

| condition | R@50 | R@100 | Violation@50 | Violation@100 | role |
| --- | ---: | ---: | ---: | ---: | --- |
| `semantic_only` | 0.9599 | 0.9894 | 0.0247 | 0.0469 | reproduced semantic ranking |
| `probabilistic_recalibrated` | 0.9642 | 0.9921 | 0.0234 | 0.0391 | main recall-first H001 condition |
| `rule_verified_point_subtype` | 0.9587 | 0.9890 | 0.0000 | 0.0000 | hard-filter zero-violation diagnostic |
| `family_specific_p_geom_valid` | 0.9619 | 0.9914 | 0.0204 | 0.0310 | stricter violation-first operating point |

Interpretation:

- `probabilistic_recalibrated` improves recall and lowers violation relative to `semantic_only`.
- `rule_verified_point_subtype` demonstrates zero-violation behavior but should be reported as a diagnostic, not the default main operating point.
- `family_specific_p_geom_valid` gives a clearer violation reduction but is a stricter operating point.

### Controls

| condition | R@50 | R@100 | Violation@50 | Violation@100 | purpose |
| --- | ---: | ---: | ---: | ---: | --- |
| `control_p_geom_valid_only` | 0.2028 | 0.5049 | 0.0642 | 0.0701 | geometry-only ranking control |
| `control_distance_only` | 0.3835 | 0.5642 | 0.0731 | 0.0993 | simple distance heuristic control |
| `control_shuffled_geometry` | 0.9297 | 0.9788 | 0.0289 | 0.0559 | breaks geometry identity while preserving distribution |
| `control_wrong_pair_geometry` | 0.9242 | 0.9788 | 0.0302 | 0.0581 | tests object-pair identity |

Interpretation:

- Geometry alone is not enough.
- Simple distance is not enough.
- Wrong-pair and shuffled-geometry controls degrade performance, supporting the claim that relation-level object-pair geometry matters.

### GT-Based Verifier Evaluation

| metric | rows | value |
| --- | ---: | ---: |
| GT-positive nonviolated rate | 2,545 | 0.9972 |
| GT-derived negative nonsatisfied rate | 2,545 | 0.9694 |
| `p_geom_valid` AUROC | 5,090 | 0.9779 |
| `p_geom_valid` AUPRC | 5,090 | 0.9737 |
| `p_geom_valid` Brier | 5,090 | 0.0538 |

Interpretation:

- The verifier signal is not only a test-set post-hoc heuristic; it has GT-positive and counterfactual-negative support.
- This should be used to defend calibration and rule design, while still acknowledging residual calibration risk.

### Audit And Visual Sanity

| source | rows | metric | value | caveat |
| --- | ---: | --- | ---: | --- |
| structured audit | 250 | strict invalid-only precision | 0.7133 | non-independent structured audit |
| structured audit | 250 | quality-issue precision | 0.8933 | includes invalid/coarse/scan-missing/annotation-noise |
| visual spot-check | 50 | target-bucket quality-issue rate | 0.9333 | reduced sanity check, reviewer `yhkim` |
| visual spot-check | 50 | contradiction rate | 0.0333 | valid/verifier-error contradiction among target buckets |
| visual spot-check | 50 | private-reference exact match rate | 1.0000 | Codex transcribed reviewer-confirmed labels |

Interpretation:

- Use this as sanity and reviewer-defense evidence.
- Do not describe it as a large-scale or strictly blinded independent human audit.

### Open3DSG

| condition | R@50 | R@100 | Violation@50 | Violation@100 |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.3945 | 0.4963 | 0.1326 | 0.1195 |
| `probabilistic_recalibrated` | 0.3843 | 0.5580 | 0.0575 | 0.0803 |
| `rule_verified_point_subtype` | 0.4149 | 0.5238 | 0.0000 | 0.0000 |
| `family_specific_p_geom_valid` | 0.4530 | 0.5984 | 0.0228 | 0.0311 |

Interpretation:

- Open3DSG provides second-source evidence that geometry-consistency can reduce violations in the same H001 families.
- The best Open3DSG pattern is not identical to `VL-SAT`; use it to support cross-source reliability evidence, not to claim universal behavior.
- `family_specific_p_geom_valid` is strong on Open3DSG but must be presented as a family-specific operating point.

## Open3DSG Caveats To Preserve

Fact:

- Open3DSG checkpoint is generated by Docker reproduction, not downloaded as an official trained checkpoint.
- Selected checkpoint: `epoch=13-step=13104.ckpt`.
- Selection signal: train-dev `val/loss` 0.32881081104278564 at step 13103, chosen before H001 held-out metric/failure/visual inspection.
- This is an explicitly labeled averaged-BLIP variant, not the exact non-averaged BLIP projector route.
- Runtime train split is filtered to 3,744/3,852 train subgraphs.
- Train-dev validation split is filtered to 156/160 subgraphs.
- H001 eval covered loadable scope is 377/388 contexts with `validation_missing_preprocessed:11`.
- Exact-label H001-family denominator is 2,545 GT relations.
- Qualitative inspection found 10/36 sampled rule-violated cases with `p_geom_valid > 0.9`.

Paper wording rule:

- Every Open3DSG table/discussion must mention filtered-train, averaged-BLIP, covered-scope, exact-label denominator, `validation_missing_preprocessed:11`, and residual calibration-risk caveats.
- Historical exit-137 attempts are run records, not final raw-dump provenance caveats.
- Clean raw-dump source-process provenance is v14 streaming same-path resume: exit 0, 377/377 completed batches, 19,162 rows, dropped/invalid partial rows 0/0, SHA256 matching canonical `raw_dump/raw.jsonl`.

## Failure Analysis

Fact:

- Open3DSG real failure-analysis rows: 57,736.
- Validation errors: 0.
- Visual-audit queue rows: 6,162.
- Qualitative case inspection: 36 cases.
- Geometry-aware reranking demoted 23/36 selected cases.
- 13/36 were promoted or retained.
- 10/36 were rule-violated but still had `p_geom_valid > 0.9`.

Interpretation:

- The failure analysis supports the failure-mechanism narrative: semantic plausibility and physical consistency can diverge.
- It also exposes residual calibration risk, which should be reported rather than hidden.

## Main Tables And Figures To Draft

Fact:

- Table 1: `VL-SAT` semantic-only vs calibrated/rule/family-specific conditions.
- Table 2: nontriviality controls, including geometry-only, distance-only, shuffled-geometry, and wrong-pair geometry.
- Table 3: GT-based verifier evaluation.
- Table 4: structured audit and visual sanity check.
- Table 5: source-specific claim boundary.
- Table 6: cross-source `VL-SAT` + Open3DSG status.
- Figure specs are already generated under `experiments/H001_geom_reliability/figures/`.

Recommended paper narrative:

1. Define failure: semantic relation confidence is not calibrated to physical relation consistency.
2. Define target families: `support_contact`, `proximity`, `relative_vertical`.
3. Present calibrated geometry-consistency framework.
4. Show `VL-SAT` metrics, controls, and GT-based verifier evaluation.
5. Show Open3DSG second-source metrics with caveats.
6. Use failure analysis to explain where the framework helps and where residual risk remains.
7. Keep Qwen-VL as optional extension unless full metric evidence is added.

## Reviewer Defense Map

| reviewer attack | current defense | remaining discipline |
| --- | --- | --- |
| "This is just a hand-coded verifier." | Frame as calibrated evaluation/re-ranking framework with calibration, controls, GT counterfactuals, and failure analysis. | Avoid script-level method wording. |
| "It only works on VL-SAT." | Open3DSG second-source metric evidence is ready. | Keep claim within measured H001 families. |
| "It trades recall for filtering." | Report R@K and Violation@K together; `probabilistic_recalibrated` and `family_specific_p_geom_valid` show different operating points. | Include Pareto/tradeoff wording. |
| "Rules were tuned on test set." | Denominator policy, metric scope, checkpoint selection, and caveat wording are fixed before paper writing; GT-based verifier eval exists. | State selection/provenance clearly. |
| "Open3DSG reproduction is not exact." | Explicit averaged-BLIP variant caveat and Docker provenance. | Do not claim exact non-averaged Open3DSG route. |
| "Open-vocabulary claim is too broad." | Current claim is measured reliability-layer evidence, not broad generation improvement. | Keep non-claims visible. |

## Optional Extensions

Qwen-VL:

- Current status: contract, parser skeleton, 30-row non-held-out tiny pilot, pair crops, model-lock plan, and Qwen3-VL-4B cache are ready.
- Runtime preflight and tiny inference smoke have not been run after Open3DSG jobs completed.
- It should stay optional unless full prediction JSONL, geometry join, denominator, metrics, and audit treatment are added.

FROSS:

- Runtime-blocked and does not cover `proximity` / `relative_vertical`.
- Not suitable as the main current extension.

SceneFun3D/FunGraph3D:

- Only relevant if the paper scope pivots toward functionality, affordance, or robotics downstream relations.

## If The Computer Changes

If a new machine starts without `local_dataset/`, the tracked markdown and experiment artifacts should be read before any download, training, or rerun. The goal is to recover the research state first, then rebuild only missing runtime data.

### Must-Read Entry Files

Read these first:

1. `AGENTS.md`
2. `README.md`
3. `TODO.md`
4. `docs/index.md`
5. `docs/hypothesis.md`
6. `docs/paper.md`
7. `docs/reproducibility.md`
8. `summary.md`
9. `paper/preview.md`

### Must-Read Hypothesis Files

Read these to recover the claim, method, and evaluation contract:

1. `hypothesis/README.md`
2. `hypothesis/CAND-001/README.md`
3. `hypothesis/CAND-001/H001_geometry-grounded-verification/01_overview.md`
4. `hypothesis/CAND-001/H001_geometry-grounded-verification/02_method.md`
5. `hypothesis/CAND-001/H001_geometry-grounded-verification/03_data_baseline.md`
6. `hypothesis/CAND-001/H001_geometry-grounded-verification/04_results.md`
7. `hypothesis/CAND-001/H001_geometry-grounded-verification/05_audit.md`
8. `hypothesis/CAND-001/H001_geometry-grounded-verification/06_second_source.md`
9. `hypothesis/CAND-001/H001_geometry-grounded-verification/07_experiment_spec.md`

### Must-Read Experiment Result Files

Read these to recover the locked paper-result state:

1. `experiments/H001_geom_reliability/README.md`
2. `experiments/H001_geom_reliability/report.md`
3. `experiments/H001_geom_reliability/manifest.lock.json`
4. `experiments/H001_geom_reliability/commands.md`
5. `experiments/H001_geom_reliability/tables/table1_main_prediction.md`
6. `experiments/H001_geom_reliability/tables/table2_controls.md`
7. `experiments/H001_geom_reliability/tables/table3_gt_verifier.md`
8. `experiments/H001_geom_reliability/tables/table4_audit.md`
9. `experiments/H001_geom_reliability/tables/table5_claim_boundary.md`
10. `experiments/H001_geom_reliability/tables/table6_cross_source_status.md`
11. `experiments/H001_geom_reliability/figures/figure_specs.md`

### Must-Read Open3DSG Files

Read these before rerunning Open3DSG:

1. `experiments/H001_geom_reliability/sources/open3dsg/README.md`
2. `experiments/H001_geom_reliability/sources/open3dsg/commands.open3dsg.md`
3. `experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection/report.md`
4. `experiments/H001_geom_reliability/sources/open3dsg/eval_preflight/report.md`
5. `experiments/H001_geom_reliability/sources/open3dsg/dump_features/report.md`
6. `experiments/H001_geom_reliability/sources/open3dsg/dump_features_h001_eval/report.md`
7. `experiments/H001_geom_reliability/sources/open3dsg/raw_dump_identity/report.md`
8. `experiments/H001_geom_reliability/sources/open3dsg/adapter/report.md`
9. `experiments/H001_geom_reliability/sources/open3dsg/geometry/report.md`
10. `experiments/H001_geom_reliability/sources/open3dsg/metrics/report.md`
11. `experiments/H001_geom_reliability/sources/open3dsg/metrics/metrics.json`
12. `experiments/H001_geom_reliability/sources/open3dsg/failure_rows/report.md`
13. `experiments/H001_geom_reliability/sources/open3dsg/failure_cases/inspection.md`
14. `experiments/H001_geom_reliability/sources/open3dsg/paper_caveats/report.md`

### Runtime Data That May Need Rebuild

These are usually not safe to assume on a new computer:

| runtime item | current expected path |
| --- | --- |
| Raw 3RScan payload | `local_dataset/3RScan/scans/` |
| VL-SAT code/data/checkpoints | `local_dataset/VLSAT_code/CVPR2023-VLSAT/` |
| Open3DSG training root | `local_dataset/Open3DSG_staged/training_repro/` |
| Open3DSG H001 eval root | `local_dataset/Open3DSG_staged/h001_runtime/` |
| Open3DSG selected checkpoint | `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt` |
| Open3DSG train/dev features | `local_dataset/Open3DSG_staged/training_repro/output/features/clip_features_h001_official_blip_top5_scales3/` |
| Open3DSG H001 eval features | `local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3/` |
| Qwen-VL model cache | `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17/` |

Recovery rule:

- Do not start by retraining or redownloading everything.
- First read `docs/reproducibility.md`.
- Then verify which local paths exist.
- Only rebuild missing payloads/checkpoints/features with the Docker commands recorded in `docs/reproducibility.md` and `experiments/H001_geom_reliability/commands.md`.
- Long downloads, feature dumps, training, decompression, and preprocessing must run in `tmux` or background jobs with timestamped logs under `logs/`.

## Immediate Next Step

Recommended next action:

1. Start paper writing from this preview.
2. Draft the paper outline and contribution statements before adding optional Qwen-VL evidence.
3. Keep Qwen-VL runtime smoke as optional extension only, unless the paper outline reveals a concrete reviewer-defense gap that needs it.
