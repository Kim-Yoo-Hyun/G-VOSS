# GeoCalib / H001 Research Summary

Last updated: 2026-06-23 KST

이 문서는 CAND-001 / H001의 현재 연구 정의, 필요성, 가설, metric,
비교군, 실험 세팅, contribution, 구현 방향, baseline 재현 가능성을 한곳에
정리한다.

Paper-facing name: `GeoCalib: Calibrating Geometric Consistency for Reliable 3D Scene Graph Relations`. Use `GeoCalib` in manuscript-facing prose and keep `H001` for internal hypothesis/experiment paths.

## Current Snapshot, 2026-06-23 KST

Facts:

- Main evidence route is complete for the scoped three-family reliability claim: VL-SAT full official validation and Open3DSG full-validation `recovery_relaxed_views_min2/` are the paper-facing main sources.
- Release-oriented repo layout is in place: `src/geocalib/` for executable code, `scripts/` for shell wrappers, `configs/` for Docker/compose entry points, `experiments/` for source-specific run records, `results/` for compact paper-facing outputs, and `archive/` for preserved hypothesis records plus superseded or optional material.
- Low-K reporting decision is to show K = `{5, 10, 20, 50, 100}` in the main source-result table; K=1 is excluded from paper metrics and kept only as a sanity check. Docker-regenerated low-K metric artifacts now live under `sources/vlsat/full_validation/metrics_k_sweep/` and `sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics_k_sweep/`; K=50/100 values match the locked `metrics/metrics.json` point estimates.
- Qwen-VL full official validation downstream is complete as a third-source / modern VLM extension with 157 scans / 548 contexts / 110,424 query rows / 46,506 inferable input rows / 35,131 exported predictions / 32,236 in-scope predictions / 3,972 H001-family GT rows. It remains appendix/extension evidence unless explicitly promoted.
- Latest known paper build is `logs/h001_aaai_pdf_build_lowk_full_20260623_191806.log`, exit 0, 9 pages, with GeoCalib, Figure-1, and low-K table updates. Any older release package generated before these updates must be regenerated before upload.

Inference:

- The defensible paper claim is still a scoped calibrated geometry-consistency reliability layer, not broad 3DSSG generation, broad SOTA, or arbitrary-baseline improvement.
- Immediate work is submission/package hygiene rather than new main-source experiments: portal form, artifact URL/DOI, supplementary policy, checklist answers, package regeneration, and final PDF/source sanity checks.

## One-Line Summary

Fact:

- H001은 새로운 3DSSG generator를 제안하는 연구가 아니라, 기존 3DSSG
  relation predictor의 semantic relation prediction을 explicit 3D geometry
  evidence로 검증하고 보정하는 연구다.

Inference:

- 가장 방어 가능한 논문 framing은 `calibrated geometry-consistency evaluation
  and re-ranking framework for 3D scene graph relations`이다.

## Problem Definition

Fact:

- Open-vocabulary 또는 learned 3D Scene Graph predictor는 visual/language
  prior 때문에 의미상 그럴듯한 relation edge를 낼 수 있다.
- 그러나 이런 relation edge가 실제 3D geometry와는 맞지 않을 수 있다.
- H001은 전체 predicate를 다루지 않고, geometry로 검증 가능한 relation
  family에 집중한다.

Target families:

- `support_contact`
- `proximity`
- `relative_vertical`

Out of first-scope:

- full functional relation discovery
- relative-horizontal coordinate-frame claim remains outside the current main
  claim; it is now a selected scope-expansion validation track with blocked
  coordinate-audit and bucket-inspection diagnostics
- attachment / hanging / connection relations remain outside the current main
  claim, but `attachment_deferred` is the preferred future physical-relation
  upgrade path; Docker G0 scope/schema audit, G1 extractor contract, G1b
  evidence-only dry run, G1c point/surface validation, G2 conservative
  verifier-policy design, G3 train-dev calibration/counterfactual route, G4 GT
  policy smoke, G4b error/visual sanity planning, G4c strict-only
  calibration-filter freeze, G5a pooled strict calibration fit, G5b bounded
  source scoring preflight, G5c full-source protocol freeze, and G5d
  full-source scoring plus source metrics/controls/bootstrap are complete
- online RGB-D graph generation
- robotics navigation
- broad open-vocabulary 3DSSG generation improvement

Recent novelty-threat update:

- 2026-05-23 RelWitness full-PDF skim identified `RelWitness` as the closest
  wording/method threat because it explicitly uses visual-geometric relation
  witnesses, calibrated witness quality, and witness-consistent decoding for
  open-vocabulary 3DSSG under incomplete relation supervision.
- This does not replace H001's reproduced evidence because the checked arXiv v2
  PDF states its numerical tables are simulated manuscript-planning values, but
  it does mean H001 should not claim novelty as "relation witnesses",
  "geometry evidence", or "calibrated witness quality" alone.
- The current defensible difference remains calibrated geometry-consistency
  evaluation/re-ranking over existing relation-source outputs, with reproduced
  `VL-SAT` and Open3DSG metrics, controls, denominator accounting, and failure
  analysis.

## Why This Research Is Needed

Fact:

- 3D Scene Graph는 relation prediction benchmark뿐 아니라 alignment,
  registration, navigation, planning, LLM/VLM reasoning 같은 downstream
  task에서도 structured scene representation으로 쓰인다.
- 기존 3DSSG metric인 R@K / mR@K는 semantic label recall은 보여주지만,
  top-k relation이 물리적 또는 기하학적으로 가능한지 직접 측정하지 않는다.
- VL-SAT, Open3DSG, CCL-3DSGG 등은 semantic 또는 open-vocabulary relation
  prediction을 강화하지만, relation edge마다 explicit geometry validity,
  evidence provenance, violation reason을 표준적으로 보고하지는 않는다.

Inference:

- Top-tier contribution을 만들려면 "semantic + geometry를 쓴다"가 아니라,
  relation edge의 reliability를 측정하고 개선하는 evaluation / re-ranking
  layer로 좁혀야 한다.
- H001의 필요성은 "더 높은 R@K"만이 아니라, R@K를 유지하면서
  geometry-inconsistent top-k relation을 줄이고 왜 실패했는지 분석 가능하게
  만드는 데 있다.

## Hypothesis

Main hypothesis:

```text
For geometry-checkable 3DSSG relation families, adding explicit 3D geometry
evidence and verification to candidate semantic relation edges will reduce
geometry-inconsistent relation predictions while preserving useful
predicate/triplet recall.
```

Operational form:

```text
semantic prediction score + frozen geometry evidence/verifier + calibrated
p_geom_valid -> reliability-aware reranking/filtering
```

Allowed current claim:

```text
Across reproduced VL-SAT and Open3DSG relation-source outputs,
geometry-calibrated consistency scoring exposes and reduces
geometry-inconsistent top-k predictions for geometry-checkable families while
reporting recall tradeoffs under fixed denominators and source-specific
caveats.
```

Preferred upgraded claim after Open3DSG second-source evidence:

```text
Across reproduced VL-SAT and Open3DSG prediction sources, calibrated
geometry-consistency re-ranking improves relation reliability for
geometry-checkable 3DSSG families while preserving useful recall.
```

Not allowed now:

```text
The method broadly improves open-vocabulary 3D scene graph generation.
```

Not allowed now:

```text
The method is already baseline-agnostic across 3DSSG predictors.
```

## Method Contribution

Contribution should be stated as:

```text
calibrated geometry-consistency evaluation and re-ranking for 3D scene graph
relations
```

Core components:

| Component | Role |
| --- | --- |
| identity-preserving prediction rows | preserve scan/subgraph/object-pair identity across prediction, geometry, and GT joins |
| geometry evidence schema | attach auditable OBB, point/local, distance, vertical, contact, and support evidence to relation candidates |
| subtype-aware verifier | convert geometry evidence into `satisfied`, `uncertain`, or `violated` decisions |
| `p_geom_valid` calibration | estimate geometry-valid probability from frozen calibration data and counterfactual negatives |
| reliability-aware re-ranking/filtering | combine semantic score and calibrated geometry validity without replacing the base predictor |
| violation/recall evaluation layer | measure geometry reliability separately from standard recall |
| failure-analysis schema | explain whether failures come from semantic confusion, geometry violation, preprocessing, denominator coverage, or model/source limitations |

Avoid this framing:

```text
a rule verifier script for VL-SAT
```

## Experimental Setting

Paper-facing full-validation setting:

| Item | Fixed value |
| --- | --- |
| dataset | official `3DSSG_subset` / 3RScan full validation |
| implemented prediction source | reproduced `VL-SAT` / `vlsat_closed_set` full-validation route |
| selected second-source path | Docker-reproduced `Open3DSG` full-validation recovery branch |
| held-out scans | 157 |
| contexts | 548 |
| directed pairs | 36,808 |
| VL-SAT prediction rows | 957,008 |
| Open3DSG prediction rows | 695,916 |
| ground-truth rows | 11,254 |
| in-scope GT denominator | 3,972 |
| predicate families | `support_contact`, `proximity`, `relative_vertical` |
| frozen verifier policy | `point_subtype` |
| frozen pooled calibrator | `artifacts/calibration/p_geom_valid_smoke/model.json` |
| frozen family calibrator | `artifacts/calibration/p_geom_valid_family/model.json` |

Full official validation branch:

- status: `full_validation_primary_route_selected_recovery_branch`
- scope: official `3DSSG_subset` validation, 157 scans / 548 contexts /
  11,254 GT rows / 3,972 H001-family GT rows
- VL-SAT: 957,008 prediction rows, adapter/geometry/metrics/controls/GT
  verifier/bootstrap/failure-analysis ready under
  `experiments/H001_geom_reliability/sources/vlsat/full_validation/`
- Open3DSG covered-scope branch: 690,924 prediction rows, 533 covered raw
  batches, adapter/raw identity/geometry/metrics/controls/bootstrap/failure
  rows/Table 6 caveats ready under
  `experiments/H001_geom_reliability/sources/open3dsg/full_validation/`
- Open3DSG caveats: selected official non-avg BLIP checkpoint route, 15 missing
  preprocessed validation contexts after recovery, and raw process exit `137`
  after stream finalization
- Open3DSG covered-scope provenance review:
  `sources/open3dsg/full_validation/raw_clean_exit_review/` records that the
  expected 533/548 clean-exit retry artifact is no longer present after cleanup,
  so the unmodified branch keeps its exit-137 caveat. The selected 548/548
  recovery branch is unaffected and has raw stream exit `0`.
- Open3DSG missing-15 recovery branch: diagnosis identified the exact
  Open3DSG source condition as the hard-coded 4-visible-object preprocess gate;
  a separate recovery variant with `OPEN3DSG_MIN_VISIBLE_OBJECTS=2` plus
  relaxed view generation for two scans now passes preprocess audit at 548/548.
  The full recovery downstream bundle is ready under
  `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/`:
  feature audit 548/548, clean-exit raw dump 26,938 rows / 548 batches,
  adapter 695,916 prediction rows, geometry 695,916 rows, 160,596
  H001-family geometry-checkable rows, metrics/controls, bootstrap CI, 82,155
  failure rows, 36-case qualitative failure inspection, and Table 6/caveat
  regeneration. Low-K sweep artifacts are ready in `metrics_k_sweep/` with
  K=`{5,10,20,50,100}`; K=50/100 matches the locked `metrics/` point estimates.
  Key recovery pattern: at K=5/10, semantic-only violation is `0.5131/0.3255`,
  while `family_specific_p_geom_valid` reduces it to `0.0420/0.0482` and raises
  recall from `0.0368/0.1002` to `0.0984/0.1921`.
- Open3DSG recovery caveat: this removes the missing-context denominator caveat
  but must be described as a recovery-policy variant, not as the unmodified
  Open3DSG preprocess route.
- paper rule: regenerate AAAI main tables/prose from the selected
  full-validation route. Use VL-SAT full-validation as the controlled-anchor
  result and Open3DSG `recovery_relaxed_views_min2/` as the primary
  full-denominator Open3DSG result; report the 533/548 covered branch as a
  sensitivity / unmodified-source-route check. Historical 127-scan Open3DSG
  results belong only in appendix/sensitivity, with R2 388/388 as the
  representative historical branch and old 377/388 as the comparison row.
- full-validation failure taxonomy: VL-SAT has 59,841 diagnostic rows, 2,897
  visual-audit queue rows, and a 36-case deterministic qualitative inspection;
  Open3DSG recovery has 82,155 diagnostic rows, 8,821 visual-audit queue rows,
  and a new 36-case deterministic qualitative inspection. These artifacts
  support failure-mechanism/reviewer-defense discussion; they are not
  representative human-audit metrics.

Open3DSG metric-scope policy:

- current paper-facing full-validation H001-family GT denominator: 3,972 rows
- current full-validation families: `support_contact` 1,816, `proximity` 1,766,
  `relative_vertical` 390
- historical 127-scan H001-family GT denominator: 2,545 rows
- historical 127-scan families: `support_contact` 1,199, `proximity` 1,128,
  `relative_vertical` 218
- recall matching remains exact predicate-label matching
- family grouping is for reliability / violation reporting, not recall-label
  collapse
- current primary caveats: selected checkpoint provenance, filtered train/dev
  provenance, recovery-policy branch, 533/548 full-validation sensitivity
  branch, appendix historical 377/388 versus R2 388/388 sensitivity, and
  residual calibration risk

Relative-horizontal expansion track:

- status: `relative_horizontal_bucket_inspection_ready_do_not_promote_no_metric_execution`
- current claim remains unchanged until the expanded track reaches the current
  H001 evidence standard
- candidate GT rows: 3,570, with labels `left/right/front/behind`
  1,132/1,132/653/653
- expanded candidate denominator: 6,115 / 7,505 if validated
- source prediction rows: VL-SAT 103,664 and Open3DSG 76,400
- current verification status: unsupported for both sources
- coordinate audit result: selected frame `scan_left_neg_x_front_neg_y`, macro
  strict purity 0.7725, strict eligible share 0.6403, `left`/`right` purity
  0.8005, `front`/`behind` purity 0.7445, inverse consistency 1.0, wrong-frame
  gap 0.1231
- bucket inspection result: `front`/`behind` strict match:contradiction 2.9143,
  sign-only purity 0.7491, ambiguity flags `axis_margin_ambiguous` 230,
  `conflicting_axis_dominates` 430, `strong_projected_overlap` 44
- recommendation: `do_not_promote_relative_horizontal_to_main_claim`
- current AAAI-path decision: stop as appendix/limitation evidence; do not run
  expanded-family metrics unless the paper strategy explicitly pivots to broader
  spatial-family coverage

Attachment-deferred upgrade track:

- status: `attachment_deferred_g5d_full_source_metrics_ready`
- full log: `logs/h001_attachment_g5d_full_20260606_113803.log`
- output: `archive/experiments/H001_geom_reliability/sources/attachment_deferred/full_source_g5d/`
- counts: 69/69 shards, 135,048 scored rows, validation errors 0, 300 failure rows
- cleanup note: the earlier 1-shard G5d smoke output/log was deleted after the
  full G5d run completed; the retained source of truth is `full_source_g5d/`
  plus `logs/h001_attachment_g5d_full_20260606_113803.log`
- key metrics:
  - VL-SAT semantic_only R@100/V@100 `1.0000/0.2126`,
    probabilistic_recalibrated `0.9979/0.2210`,
    rule_verified_attachment_policy `0.9380/0.0215`
  - Open3DSG semantic_only R@100/V@100 `0.9297/0.3021`,
    probabilistic_recalibrated `0.6628/0.2460`,
    rule_verified_attachment_policy `0.9245/0.0842`
- current claim remains unchanged; this is a future H001 upgrade path
- candidate GT rows: 967, with labels `attached to` 808, `hanging on` 126,
  `connected to` 33
- expanded candidate denominator: 3,512 / 7,505 if validated
- source prediction rows: VL-SAT 77,748 and Open3DSG 57,300
- full-source protocol: 69 deterministic shards for 135,048 source rows
- source-specific covered denominators: VL-SAT 967/967, Open3DSG 768/967
- existing geometry verification status: `unsupported` for both sources
- completed Docker outputs:
  `archive/experiments/H001_geom_reliability/sources/attachment_deferred/scope_audit/{manifest.json,label_counts.json,evidence_schema.json,report.md}`
- completed G1 contract outputs:
  `archive/experiments/H001_geom_reliability/sources/attachment_deferred/evidence_extractor/{manifest.json,extractor_contract.json,output_schema.json,field_catalog.json,subtype_policy.json,extraction_plan.json,validation_plan.json,example_row.json,report.md}`
- completed G1b dry-run outputs:
  `archive/experiments/H001_geom_reliability/sources/attachment_deferred/extractor_dry_run/{rows.jsonl,manifest.json,summary.json,validation.json,report.md}`
- completed G1c point/surface validation outputs:
  `archive/experiments/H001_geom_reliability/sources/attachment_deferred/point_surface_validation/{rows.jsonl,diagnostics.jsonl,manifest.json,summary.json,validation.json,report.md}`
- completed G2 verifier-policy outputs:
  `archive/experiments/H001_geom_reliability/sources/attachment_deferred/verifier_policy/{manifest.json,verifier_policy.json,decision_schema.json,threshold_plan.json,reason_codes.json,calibration_plan.json,commands.md,report.md}`
- completed G3 calibration/counterfactual route outputs:
  `archive/experiments/H001_geom_reliability/sources/attachment_deferred/calibration_counterfactuals/{manifest.json,positive_seeds.jsonl,counterfactual_seeds.jsonl,split_plan.json,counterfactual_plan.json,policy_smoke_plan.json,gt_eval_inputs.json,threshold_freeze_protocol.json,commands.md,report.md}`
- completed G4 GT policy-smoke outputs:
  `archive/experiments/H001_geom_reliability/sources/attachment_deferred/gt_policy_smoke/{manifest.json,summary.json,validation.json,policy_smoke_decisions.jsonl,gt_evidence_rows.jsonl,gt_evidence_diagnostics.jsonl,gt_policy_decisions.jsonl,gt_eval_rows.jsonl,visual_sanity_plan.json,commands.md,report.md}`
- completed G4b error/visual sanity outputs:
  `archive/experiments/H001_geom_reliability/sources/attachment_deferred/error_visual_sanity/{manifest.json,summary.json,review_cases.jsonl,visual_queue.jsonl,calibration_filter.jsonl,guide.md,commands.md,report.md}`
- completed G4c strict filter freeze outputs:
  `archive/experiments/H001_geom_reliability/sources/attachment_deferred/strict_filter_freeze/{manifest.json,summary.json,freeze_policy.json,strict_calibration_rows.jsonl,excluded_rows.jsonl,commands.md,report.md}`
- completed G5a pooled strict calibration-fit outputs:
  `archive/experiments/H001_geom_reliability/sources/attachment_deferred/calibration_fit/{manifest.json,model.json,metrics.json,scores.jsonl,commands.md,report.md}`
- completed G5b bounded source-scoring preflight outputs:
  `archive/experiments/H001_geom_reliability/sources/attachment_deferred/source_scoring_preflight/{manifest.json,summary.json,source_rows.jsonl,evidence_rows.jsonl,diagnostics.jsonl,scored_rows.jsonl,commands.md,report.md}`
- frozen extractor rule: emit evidence only; do not emit `verification_status`,
  `p_geom_valid`, recall credit, or reranking scores
- dry-run result: 36 input rows -> 36 output rows, validation errors 0, source
  rows 9 each for `gt_positive`, `counterfactual`, `vlsat_closed_set`, and
  `open3dsg_ov`, label rows 12 each for `attached to`, `hanging on`, and
  `connected to`
- point/surface validation result: 36/36 ready rows, point available rows 36,
  normal available rows 36, near-contact rows 27, surface normal classes
  horizontal_up 14 / vertical 21 / slanted 1, forbidden verifier/metric fields
  absent
- G2 verifier-policy result: 9 subtype policies, conservative defaults
  near-contact 0.05m, uncertain contact band 0.05-0.15m, clear-far distance
  0.30m, min near-contact points 3, min contact patch score 0.20; no decision
  rows, calibration, source scoring, or metrics are emitted
- G3 calibration/counterfactual route result: 315 train/dev positive seeds and
  446 counterfactual negative seeds, held-out scan overlap 0, no verifier
  application, no fitted calibration, no source scoring, and no metrics; warning
  that dev split has no `connected to` positive seed, so future connected-to
  family-specific calibration requires pooled calibration, augmented dev
  selection, or explicit limitation
- G4 GT policy-smoke result: 36/36 smoke decisions and 761/761 train/dev seed
  decisions pass schema validation; point/surface evidence is ready for
  761/761 seed rows with scan errors 0. Positive nonviolated is 0.9048,
  positive strict satisfied is 0.3841, counterfactual nonsatisfied is 0.8274,
  counterfactual strict violated is 0.4574, calibration-ready counterfactual
  negatives are 204/446, and overall uncertain rate is 0.4323.
- G4b error/visual sanity result: 436 review cases, 50 visual queue rows, 761
  calibration-filter rows, strict positive candidates 121, strict negative
  candidates 204, false-satisfied counterfactuals 77, false-violated positives
  30, uncertain positives 164, and uncertain counterfactuals 165. The visual
  queue is label-diverse: `attached to` 38, `connected to` 6, `hanging on` 6.
- G4c strict filter freeze result: 325 strict calibration rows, with 121 strict
  positives, 204 strict negatives, and 436 excluded non-strict rows. Strict
  label counts are `attached to` 200, `hanging on` 113, and `connected to` 12;
  split counts are train 242 and dev 83. Warning: `connected to` has no dev
  strict rows, so pooled calibration, augmented dev selection, or an explicit
  limitation is required.
- G5a pooled strict calibration-fit result: model
  `h001-attachment-deferred-p-geom-valid-strict-v1`, train/dev rows 242/83,
  dev positives/negatives 27/56, dev Brier/NLL/ECE
  0.0010/0.0077/0.0071, and dev AUROC/AUPRC 1.0/1.0. This is calibration
  readiness only: the strict subset is policy-selected and nearly separable, no
  source predictions are scored, and no source metrics/controls/bootstrap/audit
  have run.
- G5b bounded source-scoring preflight result: 120 scan-diverse source rows
  scored with the G5a fitted model, 60 VL-SAT and 60 Open3DSG rows, 40 rows per
  label, 20 selected unique scans per source, evidence ready 120/120,
  validation errors 0, and mean/median `p_geom_valid` 0.3610/0.0580. This is
  not source metric evidence because it is bounded preflight only and does not
  run full-source scoring, R@K, Violation@K, controls, bootstrap CI, or audit.
- reason to prefer over `relative_horizontal`: smaller denominator gain but
  stronger conceptual fit to H001, because attachment/hanging/connection require
  physical adjacency, contact, near-surface support, gravity, and object
  affordance consistency
- core risk: harder than support/contact; requires wall/ceiling/furniture
  surface evidence, local point contact, surface normals, gravity/hanging
  evidence, conservative uncertain handling, and visual audit
- upgrade order: full-source scoring ->
  VL-SAT/Open3DSG metrics and controls ->
  bootstrap CI/failure analysis -> optional function-reasoning pilot
- main AAAI claim promotion rule: do not add `attachment_deferred` to the main
  claim without explicit final user confirmation, even if later gates pass

## Metrics

Prediction metrics:

- `R@K` for K = `{5, 10, 20, 50, 100}`
- `Violation@K` for K = `{5, 10, 20, 50, 100}`
- delta versus `semantic_only`
- relative violation reduction versus `semantic_only`
- recall retention

Verifier-validity metrics:

- GT-positive nonviolated rate
- GT-derived negative nonsatisfied rate
- `p_geom_valid` Brier
- `p_geom_valid` AUROC
- `p_geom_valid` AUPRC

Audit / sanity metrics:

- structured audit strict invalid-only precision
- structured audit quality-issue precision
- reduced visual spot-check target-bucket quality-issue rate
- reduced visual spot-check contradiction rate

Uncertainty metric:

- deterministic subgraph bootstrap CI for `R@K` and `Violation@K` over the same
  locked source rows; this is evaluation-context uncertainty, not repeated
  training variance

## Comparison Groups

Primary conditions:

| Condition | Role |
| --- | --- |
| `semantic_only` | reproduced base predictor ranking |
| `probabilistic_recalibrated` | main recall-first H001 condition, semantic score combined with frozen pooled `p_geom_valid` |
| `rule_verified_point_subtype` | hard-filter diagnostic / zero-violation operating point |
| `family_specific_p_geom_valid` | stricter violation-first operating point |

Control conditions:

| Condition | What it tests |
| --- | --- |
| `control_p_geom_valid_only` | whether geometry alone explains the result |
| `control_distance_only` | whether a simple distance heuristic explains the result |
| `control_shuffled_geometry` | whether geometry distribution alone explains the result |
| `control_wrong_pair_geometry` | whether object-pair identity matters |

Cross-source comparison:

| Source | Role | Status |
| --- | --- | --- |
| Open3DSG | manuscript main open-vocabulary relation-source case study | Docker-reproduced historical 127-scan avg-BLIP checkpoint, H001 eval features, clean v14 raw-dump provenance, adapter/geometry/metrics, failure rows, qualitative inspection, and bootstrap CI are ready as sensitivity evidence. R1 official non-avg checkpoint selection/downstream regeneration are complete under `sources/open3dsg/non_avg/`. R2 historical covered-context recovery is complete at 388/388 with downstream metrics/bootstrap/table-caveat reporting and provenance review; clean-return raw files are row/predicate-score equivalent to canonical R2 raw after excluding run metadata, so R2 is the representative appendix/sensitivity branch and old 377/388 remains the comparison row. Full official validation is the selected paper-facing route: the recovery branch `recovery_relaxed_views_min2/` reaches 548/548 with clean raw dump, 695,916 predictions, geometry/metrics/bootstrap, 82,155 failure rows, 36-case qualitative inspection, and Table 6 caveats ready, and must disclose the recovery policy; the original 533/548 covered branch remains sensitivity / unmodified-source-route evidence with exit-137 caveat. |
| `VL-SAT` | controlled reproduced anchor | 127-scan hardened result is reproduced and table-ready as historical/sensitivity evidence; full official validation rerun is the selected controlled-anchor primary route under `sources/vlsat/full_validation/` with 957,008 predictions, 11,254 GT rows, 3,972 H001-family GT rows, metric status `ready`, GT verifier AUROC `0.9772`, bootstrap warnings 0, 59,841 failure rows, and 36-case qualitative inspection. AAAI table/prose regeneration from this route is complete; remaining work is polish/build verification. |
| Qwen-VL | third semantic source / modern VLM extension | full official validation downstream complete: 157 scans / 548 contexts / 110,424 query rows / 46,506 inferable input rows / 35,131 exported predictions / 32,236 in-scope predictions / 3,972 H001-family GT rows; parser validation, adapter export, geometry join, metrics/controls/bootstrap, 31,881 failure rows, and 36 deterministic qualitative cases ready; appendix/extension evidence unless explicitly promoted |
| FROSS | optional online support/contact source | not full-family H001 evidence |

## What The Experiments Compare

RQ1:

```text
Does geometry-calibrated reranking improve recall while lowering
geometry-inconsistent top-k predictions compared with semantic-only ranking?
```

RQ2:

```text
Is the improvement nontrivial, or can it be explained by geometry-only ranking,
distance heuristics, shuffled geometry, or wrong-pair geometry?
```

RQ3:

```text
Does the verifier agree with held-out GT-positive relations and reject
deterministic GT-derived counterfactual negatives?
```

RQ4:

```text
Do structured audit and reduced visual sanity-check evidence support the
interpretation that violation labels correspond to real relation-quality
issues?
```

Optional RQ5:

```text
Does the same geometry-consistency framework improve reliability when the
semantic source is a modern VLM rather than a trained 3DSSG predictor?
```

## Current Evidence

Fact, paper-facing VL-SAT full-validation primary route:

| Condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.4194 | 0.6322 | 0.8074 | 0.9272 | 0.9635 | 0.0029 | 0.0082 | 0.0142 | 0.0268 | 0.0476 |
| `probabilistic_recalibrated` | 0.4154 | 0.6322 | 0.8107 | 0.9305 | 0.9688 | 0.0015 | 0.0071 | 0.0120 | 0.0229 | 0.0404 |
| `rule_verified_point_subtype` | 0.4197 | 0.6317 | 0.8074 | 0.9257 | 0.9627 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `family_specific_p_geom_valid` | 0.4162 | 0.6309 | 0.8087 | 0.9288 | 0.9683 | 0.0011 | 0.0051 | 0.0109 | 0.0206 | 0.0333 |

Open3DSG full-validation recovery result:

| Condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.0368 | 0.1002 | 0.1991 | 0.4096 | 0.5161 | 0.5131 | 0.3255 | 0.2088 | 0.1386 | 0.1242 |
| `probabilistic_recalibrated` | 0.0826 | 0.1581 | 0.2603 | 0.3975 | 0.5723 | 0.0628 | 0.0699 | 0.0654 | 0.0606 | 0.0811 |
| `rule_verified_point_subtype` | 0.0707 | 0.1314 | 0.2422 | 0.4295 | 0.5368 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `family_specific_p_geom_valid` | 0.0984 | 0.1921 | 0.3291 | 0.4658 | 0.6047 | 0.0420 | 0.0482 | 0.0441 | 0.0286 | 0.0341 |

Bootstrap CI:

- Docker `bootstrap_ci` status: `ready`, 1,000 subgraph resamples, warnings none.
- Open3DSG `family_specific` vs `semantic_only`: R@100 delta `+8.86 pp`
  with 95% CI `[+6.69,+10.96]`; Violation@100 delta `-9.01 pp` with 95% CI
  `[-9.49,-8.53]`.
- VL-SAT `family_specific` vs `semantic_only`: R@100 delta `+0.48 pp` with
  95% CI `[+0.11,+0.93]`; Violation@100 delta `-1.43 pp` with 95% CI
  `[-1.60,-1.28]`.

Fact:

- GT positives: 3,972
- GT-derived negatives: 3,972
- GT-positive nonviolated rate: 0.9965
- GT-derived negative nonsatisfied rate: 0.9673
- `p_geom_valid` AUROC/AUPRC: 0.9772 / 0.9729
- reduced visual sanity-check target quality-issue rate: 0.9333
- reduced visual sanity-check contradiction rate: 0.0333

Inference:

- The current evidence supports a measured cross-source reliability-layer claim
  within H001 families across `VL-SAT` and Open3DSG.
- It supports a cross-source reliability-layer claim only within the measured
  H001 families and closed-set/GT-object setting.
- It does not yet support a broad open-vocabulary 3DSSG generation improvement
  claim.

## Required Tables And Figures

Current AAAI manuscript tables:

| Table | Content |
| --- | --- |
| AAAI Table 1 | fixed H001 evaluation scope and denominator |
| AAAI Table 2 | source-specific claim boundary and blocked extensions |
| AAAI Table 3 | main source results, Open3DSG first and `VL-SAT` second, with Open3DSG caveats |

Prose-backed reviewer-defense evidence:

| Evidence | Content |
| --- | --- |
| Controls | geometry-only, distance-only, shuffled-geometry, wrong-pair geometry |
| GT verifier | GT-positive/counterfactual verifier evaluation |
| Audit | structured audit and reduced visual sanity check |
| Optional extensions | Qwen-VL or functional/robotics results only if promoted with the same Docker, denominator, metric, and audit treatment |

Required figures:

| Figure | Content |
| --- | --- |
| Figure 1 | framework pipeline: prediction rows, geometry evidence, verifier, `p_geom_valid`, reranking/filtering |
| Figure 2 | reliability-recall tradeoff across operating points |
| Figure 3 | traceable Open3DSG qualitative cases with geometry-backed point-cloud panels |

## Main Baselines And Reproducibility

Fact:

- Current main baseline set: `VL-SAT` + Open3DSG.
- `VL-SAT` is already reproduced as the implemented main source.
- Open3DSG is the required second-source anchor for the top-tier path.
- SGFormer is a plausible optional closed-set comparison only after its model
  release, checkpoint path, and dataset contract are verified in Docker.

Baseline selection policy:

1. If official pre-trained weights exist, first run the author's evaluation path
   as a Docker sanity check and record whether the reported table can be
   re-evaluated under the same dataset split.
2. Regardless of pre-trained weights, run or attempt Docker re-training with the
   paper's exposed hyperparameters. If hyperparameters, exact split, or
   checkpoints are missing, record that as a reproducibility limitation instead
   of silently changing the claim.
3. H001 paper tables should not copy original paper Table 1/Table 2 directly.
   They should re-evaluate each baseline through the same H001 prediction-row,
   geometry-join, verifier, and recall/violation metric contract.

| Baseline paper | Current H001 role | Official code | Pre-trained baseline checkpoint | Re-training possible | Current decision |
| --- | --- | --- | --- | --- | --- |
| `VL-SAT: Visual-Linguistic Semantics Assisted Training for 3D Semantic Scene Graph Prediction in Point Cloud` | Primary reproducible baseline / closed-set 3DSSG anchor | Yes: `wz7in/CVPR2023-VLSAT` | Yes. Official README links a Google Drive `checkpoint`, and mentions `clip_adapter/checkpoint/origin_mean.pth`. GitHub Releases are empty, so checkpoint is Drive-based. | Yes. README gives dependencies, data preparation, multi-view generation, CLIP adapter training, default config, and train/eval commands. | Best first baseline. Use for pre-trained re-eval, retraining attempt, H001 Table 1/2/controls, and ablations. |
| `Open3DSG: Open-Vocabulary 3D Scene Graphs from Point Clouds with Queryable Objects and Open-Set Relationships` | Required second-source / open-vocabulary anchor | Yes: `boschresearch/Open3DSG`; repo is archived/read-only as of 2026-05-15 check | No trusted final trained Open3DSG checkpoint confirmed in the official repo. Component downloads exist for OpenSeg, BLIP2 positional embedding, and PointNet/PointNet2, but test still requires `--checkpoint [path to checkpoint]`. | Yes, but heavy. README gives setup, data prep, preprocessing, optional 2D feature dump, train, and test commands. Feature dump can require about 300GB per dataset. | Docker reproduction produced historical avg-BLIP H001 metrics, an official non-avg branch, and the selected full-validation 548/548 recovery branch. R1 exact non-avg full training selected an official non-avg checkpoint; downstream non-avg metrics are ready but train-dev loss remains worse than avg-BLIP for the historical 127-scan route. Current paper-facing second-source evidence should use the full-validation `recovery_relaxed_views_min2/` branch with explicit selected-checkpoint, filtered-train/dev, exact-label denominator, residual calibration-risk, and recovery-policy caveats; the 533/548 covered branch is sensitivity / unmodified-source-route evidence. |
| `SGFormer: Semantic Graph Transformer for Point Cloud-based 3D Scene Graph Generation` | Optional additional closed-set baseline | Yes: `Andy20178/SGFormer` | Official README states code and model release, but the actual checkpoint asset/path still needs Docker-side verification. | Likely possible. README gives dataset, install, training, and inference commands, but commands include local absolute paths and 3DSSG-O27R16 / 160O26R setup details that need cleanup. | Use only after `VL-SAT` and Open3DSG. Good candidate if a clean checkpoint download and split-compatible adapter are confirmed. |

Recommended baseline order:

| Priority | Baseline | Reason |
| --- | --- | --- |
| 1 | `VL-SAT` | best fit for the user's criteria: official code, Drive checkpoint, default config, train/eval commands, already adapted to H001 |
| 2 | Open3DSG | necessary for top-tier second-source and open-vocabulary defense; checkpoint and H001 metrics are now Docker-reproduced by us |
| 3 | SGFormer | optional extra closed-set comparison if checkpoint and dataset adapter verify cleanly |

Not current main baselines:

| Paper / source | Why it matters | Current status |
| --- | --- | --- |
| `CCL-3DSGG` | strong CVPR 2024 open-vocabulary 3DSGG paper-level competitor | no official code/checkpoint path confirmed in the current pass |
| `SGGpoint` | edge-oriented 3DSSG relation baseline and source of cleaned 3DSSG-O27R16 setup | official implementation exists, but pre-trained weight / easy re-eval path is not confirmed |
| `SMKA` | spatial-knowledge closed-set baseline | paper-level baseline to avoid overclaiming spatial-knowledge novelty |
| FROSS | online 3D SSG / ReplicaSSG direction | optional route only; does not cover all H001 families |
| `Qwen2.5-VL` / `Qwen3-VL` | modern VLM semantic-source extension | optional extension, not replacement for Open3DSG |

## Implementation Direction

Paper-body experiment rule:

- final experiment outputs must be Docker-generated;
- host-only outputs are not paper-result evidence;
- long-running I/O or training jobs run in background sessions with logs;
- exact commands, working directory, expected outputs, and verification commands
  must be recorded.

Current experiment root:

```text
experiments/H001_geom_reliability/
```

Implemented / ready:

- Docker table builder for locked `VL-SAT` artifacts
- Table 1-6 placeholder/report generation
- locked input manifest
- Open3DSG checkpoint reproduction plan
- Open3DSG post-dump handoff gates
- Open3DSG checkpoint provenance/selection template
- Open3DSG raw-dump identity checklist
- Open3DSG metric-scope policy
- Open3DSG metric/join contract, real adapter export, geometry join, metric eval, and Table 6 hook
- Open3DSG failure-analysis schema and synthetic smoke generator
- Open3DSG real failure-analysis rows and qualitative failure-case sampler
- Qwen-VL input/output schema, parser skeleton, tiny pilot, model-lock plan,
  30/30 pair-crop rendering, tiny runtime smoke, full-source promotion plan,
  full-source input audit, and all-scope crop preflight

Current data/runtime status:

- Open3DSG official BLIP TopK5/scales3 feature dump is complete.
- Docker `feature_audit` passed on 2026-05-15 KST with status `ready` and
  blockers none.
- Feature root:
  `local_dataset/Open3DSG_staged/training_repro/output/features/clip_features_h001_official_blip_top5_scales3/`.
- Current feature coverage: 3900/3900 complete feature ids.
- Split coverage: train 3744/3744, validation 156/156, missing complete 0,
  missing preprocessed 0.
- Each required feature directory has 3900 `.pt` files:
  `export_obj_clip_valids`, `export_obj_clip_emb_clip_OpenSeg_Topk_5_scales_3_vis_crit_0.19999999999999998_vis_crit_mask_0.1`,
  and `export_rel_clip_emb_clip_BLIP_Topk_5_scales_3_vis_crit_0.19999999999999998`.
- The first Open3DSG checkpoint pilot launched in tmux
  `h001_open3dsg_train_pilot` on 2026-05-15 13:18 KST, reached epoch 0
  step 1419/3744, and failed with CUDA OOM during BLIP projector forward.
  Exit code was 1 and no `.ckpt` file was found.
- The first retry used source patch schema `h001_open3dsg_source_patch_v5`
  with chunked BLIP projector forward and
  `OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=4`. It reached epoch 0 step 235/3744
  and failed with CUDA OOM while an unrelated `conceptgraph` container had
  expanded GPU usage. Exit code was 1 and no `.ckpt` file was found.
- Training preflight schema `h001_open3dsg_training_preflight_v6` now records
  GPU free/total memory and blocks `train_pilot`/`train_full` if
  `OPEN3DSG_MIN_GPU_FREE_MB` is not met. Docker preflight passed at
  2026-05-15 13:49 KST with 30019/32100 MB free and threshold 18000 MB.
- Retry2 used `OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1`, reached epoch 0
  step 699/3744, and failed with CUDA OOM in the chunked BLIP projector path.
  Exit code was 1 and no `.ckpt` file was found.
- The historical lower-memory route is Open3DSG's existing `--avg_blip_emb`
  option, which is compatible with the official `[num_edges, 257, 1408]`
  BLIP feature tensors and skips the train-time BLIP projector. This is a
  reproducible Open3DSG averaged-BLIP variant, not the exact non-averaged
  projector route.
- Avg-BLIP pilot completed with exit code 0, global step 936, val/loss
  0.37145, and two `avg_blip_pilot` checkpoints. Docker
  `open3dsg_checkpoint_selection` was refreshed with schema
  `h001_open3dsg_checkpoint_selection_v2`, candidate_count 2, and
  paper-result eligible candidates 0.
- Full avg-BLIP training completed and Docker checkpoint selection selected
  `epoch=13-step=13104.ckpt` before H001 held-out inspection.
- Exact non-averaged BLIP route was previously OOM-blocked in pilot retries,
  but R1 caveat-reduction full retry completed with exit `0` at
  `2026-06-04T17:01:07+09:00`. Docker checkpoint selection selected
  `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt`,
  sha256 `ca86d429b19e846aec2bfff014256bf36f6f90da07e566b90c461d6eca8d76bb`,
  by train-dev `val/loss=0.5724539160728455` before selected-route H001
  held-out metrics. The avg-BLIP checkpoint remains better on train-dev loss
  (`0.32881081104278564`, delta `+0.24364310503005981` for non-avg), so this
  remains worse than avg-BLIP for the historical 127-scan comparison. The
  paper-facing route has since moved to full-validation Open3DSG
  `recovery_relaxed_views_min2/`, which uses the selected official non-avg
  checkpoint and must disclose its recovery policy. A separate non-avg
  downstream branch is complete under
  `experiments/H001_geom_reliability/sources/open3dsg/non_avg/`; raw stream
  wrote 19,162 rows / 377 batches, and identity/export/join/metrics/bootstrap/
  Table 6-caveat services passed.
- H001 held-out eval feature cache is complete for the covered loadable scope:
  shard loop exit 0, `377/377` complete feature ids, and `1131` `.pt` files.
  Docker `feature_audit_h001_eval` has missing complete feature ids `0`, while
  retaining the known `validation_missing_preprocessed:11` caveat.
- The feature-ready raw dump reached the full context load but failed before
  writing `raw_dump/raw.jsonl` because of Docker shared-memory / DataLoader
  worker errors. The SHM retry avoided that failure but exposed an avg-BLIP
  Float/BFloat16 mismatch in relationship generation. The dtype retry avoided
  that mismatch but exposed a legacy BLIP `max_length` generation validation
  error under current Transformers. Source patch schema
  `h001_open3dsg_source_patch_v12` aligns relationship image embeddings to the
  loaded BLIP model dtype, switches BLIP generation to `max_new_tokens`, and
  enabled the canonical raw dump retry.
  The guarded generation retry reached Lightning `Testing DataLoader 0`
  `377/377` and wrote `19162` rows to `raw_dump/raw.jsonl`; the container
  then ended with exit code `137`. Docker `open3dsg_raw_dump_identity` reports
  `raw_dump_identity_audit_ready` with no blockers.
- The v13 clean raw-dump-only source rerun ended with exit `137` before raw
  writing because raw export still occurred only at `on_test_epoch_end`.
- Source patch `h001_open3dsg_source_patch_v14` added per-batch raw streaming,
  a resumable `.completed.jsonl`, partial-row repair, and no streaming-mode
  `test_step_outputs` accumulation. The first v14 streaming run exited `137`
  before the first streamed batch, and the retry exited `137` after 294/377
  completed batches. The same-path resume
  `h001_open3dsg_eval_stream_raw_dump_resume_20260519_103227` completed with
  exit `0`: manifest status `raw_dump_stream_complete`, 377/377 completed
  batches, 19,162 rows, dropped/invalid partial rows 0/0. Its SHA256 matches
  canonical `raw_dump/raw.jsonl`, so clean raw-dump source-process provenance is
  now available; earlier exit-137 attempts remain historical run records.
- Docker `open3dsg_adapter_raw_dump` is ready: `19162` raw rows -> `496600`
  prediction rows, with `62` raw rows filtered outside the fixed H001 object
  context and counted in the manifest.
- Docker `open3dsg_geometry_join` is ready: `496600/496600` rows preserved,
  `114600` geometry-checkable rows scored, and G2 variants emitted
  (`obb_only`, `point_subtype`, `point_subtype_no_soft_support`).
- Historical 127-scan Docker `open3dsg_metric_eval` is ready with no blockers.
  Key Open3DSG H001-family metrics for that historical branch are:
  semantic_only R@50/R@100 `0.3945/0.4963`,
  Violation@50/@100 `0.1326/0.1195`; probabilistic_recalibrated
  R@50/R@100 `0.3843/0.5580`, Violation@50/@100 `0.0575/0.0803`;
  rule_verified_point_subtype R@50/R@100 `0.4149/0.5238`,
  Violation@50/@100 `0.0/0.0`; family_specific control R@50/R@100
  `0.4530/0.5984`, Violation@50/@100 `0.0228/0.0311`.
- Historical 127-scan Docker `table_builder` regenerated Table 6 from
  `sources/open3dsg/metrics/metrics.json`; Open3DSG Table 6 hook status is
  `ready`.
- Historical 127-scan Docker `open3dsg_failure_generator_real` is ready: it
  generated 57,736 real failure-analysis rows from semantic top-100 or geometry-reranked top-100
  union per subgraph, with 0 validation errors. Primary categories include
  semantic_false_positive 27,326, insufficient_geometry_evidence 20,828,
  semantic_and_geometry_failure 5,183, geometry_contradiction 979,
  predicate_family_ambiguity 1,727, rank_only_failure 433, and
  true_positive_supported 1,260. Visual-audit queue rows: 6,162.
- Docker `open3dsg_failure_case_sampler` is ready: it selected 36
  high-severity visual-audit qualitative candidates from 6,162 candidate rows.
  The sample covers geometry_contradiction 14 and
  semantic_and_geometry_failure 22, across proximity 8, relative_vertical 18,
  and support_contact 10. This is a qualitative inspection queue, not an
  additional metric or representative human audit.
- Docker `open3dsg_failure_case_inspection` is ready: it generated
  `failure_cases/{inspection.json,inspection.md}` with 36 inspected cases,
  23/36 demoted by geometry-aware reranking, 13/36 promoted or retained, and
  10/36 rule-violated cases with `p_geom_valid > 0.9`. This supports the
  failure-mechanism narrative while also exposing residual calibration risk.
- Docker `open3dsg_paper_caveats` is ready: it generated
  `paper_caveats/{manifest.json,report.md}` and freezes filtered-train
  3,744/3,852 subgraphs, train-dev validation 156/160 subgraphs, H001 covered
  loadable scope 377/388 contexts, `validation_missing_preprocessed:11`,
  averaged-BLIP variant, exact-label 2,545-row H001-family denominator, and
  residual calibration-risk wording.

Current paper handoff:

- `paper/README.md` is ready and maps the paper workspace files, reading order,
  and update ownership.
- `paper/preview.md` is ready and summarizes current results, caveats,
  reviewer-defense map, optional extension boundary, and recovery files.
- `paper/progress.md` is ready and records the hypothesis-to-experiment
  progression rationale: why each experiment was run, why the next stage was
  needed, and how key results should be interpreted.
- `paper/outline.md` is ready with English/Korean paper skeleton, section-level
  evidence placement, recommended title, title alternatives, three contribution
  statements, abstract skeleton, Introduction logic, Open3DSG caveat placement,
  reviewer-defense plan, manuscript-ready table/figure caption drafts, and
  claim-consistency review across title, contribution, abstract, Introduction,
  table captions, and figure captions. Cross-source results and failure
  analysis are empirical validation, not a fourth contribution.
- `paper/draft.md` is ready as first-pass manuscript prose covering
  Title, Abstract, Introduction, Related Work, Problem Formulation, Method,
  Experimental Setup, Results/Discussion, Limitations, and Conclusion. Related
  Work now uses BibTeX-style citation keys and `paper/references.bib` scaffolds
  all inserted keys.
- `paper/risk.md` is ready as the reviewer-risk register tracking attack
  surface, mitigation status, and remaining defense work.
- `paper/appendix.md` is ready as the appendix/supplement plan. It records the
  calibrator/threshold provenance table, Open3DSG caveat consistency pass,
  optional Figure 3 decision, and Qwen-VL third-source boundary.
- `paper/aaai/` is ready as the current AAAI-style LaTeX source conversion. It
  uses AAAI-26 style files until the exact target-year official kit is fixed,
  splits the manuscript into `main.tex` plus `sec/*.tex`, and points the
  bibliography to `paper/references.bib`. Docker build verification is complete
  with `h001-aaai-tex:20260526`; latest low-K table rebuild
  `logs/h001_aaai_pdf_build_lowk_full_20260623_191806.log` exits 0.
  `main.pdf` builds to 9 total pages, technical content pages 1-7, references
  page 8, AAAI reproducibility checklist page 9, and
  targeted grep found no missing citations, undefined refs, overfull hboxes,
  LaTeX errors, or AAAI package errors.
- The current full-validation/table-policy source preserves the reviewer-defense
  answers after compression: hand-coded verifier, geometry-only/distance,
  recall-tradeoff, Open3DSG recovery-policy provenance, family-selection,
  AAAI-relevance, and small-delta uncertainty remain covered within the
  9-page build. Latest visual/layout inspection passes with wide floats delayed
  but readable before references.
- The 2026-05-27 appendix/caveat PDF rebuild and the 2026-06-06 compression
  rebuild are historical checks. The latest current low-K table check is
  `logs/h001_aaai_pdf_build_lowk_full_20260623_191806.log`, exit 0, with
  9 pages and no blocking LaTeX or AAAI warnings in targeted grep.
- `paper/figures.md` is ready and locks Figure 1-3 claims/assets before drawing:
  Figure 1 method framework, Figure 2 two-panel R@100/Violation@100 tradeoff,
  and Figure 3 Open3DSG qualitative case panels.
- `paper/generated/figures/` is ready with verified draft SVGs:
  `figure1_framework.svg`, `figure2_tradeoff.svg`, and
  `figure3_failure_cases.svg`, plus the preferred geometry-backed Figure 3
  upgrade `figure3_geometry_panels.svg`. Validation passed for locked Figure 2
  values, Figure 3 case IDs, geometry case IDs, and SVG XML parsing.
- `paper/generated/figures/layout_review.md` is ready. Figure 1 was revised to
  foreground failure mechanism -> cause -> design necessity; Figure 2 is kept
  as the strongest recall/violation evidence; Figure 3 now uses deterministic
  preprocessed object point-cloud geometry panels for the same locked cases.

Next required drafting step:

1. Full-validation AAAI source regeneration, GeoCalib/Figure-1 update, low-K
   table update, and Docker PDF build are complete:
   `logs/h001_aaai_pdf_build_lowk_full_20260623_191806.log` exits 0 and
   `paper/aaai/main.pdf` has 9 pages. Next work is submission/package hygiene,
   not source-result regeneration.
2. Confirm portal/form/style/checklist requirements, decide artifact URL/DOI
   and supplementary/code-data policy, and regenerate any flattened release
   package created before the low-K table update.
3. Include `metrics_k_sweep/` in the final artifact/release bundle and keep the
   Docker regeneration commands in `experiments/H001_geom_reliability/commands.md`.
4. Keep Open3DSG caveats explicit during any further polish; the current
   consistency target is selected official non-avg checkpoint provenance,
   filtered train/dev provenance, full-validation exact-label denominator,
   548/548 recovery policy, 533/548 full-validation sensitivity branch,
   appendix historical 377/388 versus R2 388/388 sensitivity, and residual
   calibration-risk checks in `paper/appendix.md`.
3. Keep only an optional final-polish task for rendered scene-crop Figure 3
   evidence if a deterministic path is added; the geometry-backed panel is
   already sufficient for manuscript planning.
4. Keep the current paper claim unchanged while `relative_horizontal` remains a
   frozen appendix/limitation track for the AAAI path. The scope audit,
   coordinate audit, and bucket inspection are ready, but the track is blocked
   for promotion; promotion requires resolving `front`/`behind` ambiguity plus
   verifier policy, calibration, source metrics, controls, bootstrap CI, and
   failure/audit evidence at the current H001 standard.
5. Treat `attachment_deferred` as the preferred future H001 upgrade if relation
   scope expands. Docker G0 scope/schema audit, G1 extractor contract, G1b
   evidence-only dry run, G1c point/surface validation, G2 verifier-policy
   design, G3 train-dev calibration/counterfactual route, G4 GT policy smoke,
   G4b error/visual sanity planning, G4c strict-only calibration-filter freeze,
   G5a pooled strict calibration fit, G5b bounded source scoring preflight, and
   G5c full-source protocol freeze are complete; next start with full-source
   scoring rather than held-out source metrics.

Recent Related Work decision:

- Keep `RelWitness` as required direct novelty-threat citation.
- Keep `VIZOR` as required spatial-relation / viewpoint-boundary citation.
- Keep `ZING-3D` as VLM/incremental 3DSG trend citation.
- Keep `Open-World 3DSG-RAG` as broad open-world/RAG boundary citation.
- Keep `View-on-Graph` as downstream grounding-motivation citation.

Section-structure decision:

- Keep Section 5 as a short standalone `Experimental Setup` section.
- Do not merge it into Results. Denominator, filtered-train/dev provenance,
  selected checkpoint, recovery-policy branch, exact-label denominator,
  Docker-result boundary, and non-claim caveats are reviewer-defense material
  and should remain visible before the metric results.
- Use the standard section title and state scope in the first paragraph/tables;
  this follows common CV paper structure more closely than putting `Scope` in
  the heading.

Reproducibility/GitHub portability note:

- `docs/reproducibility.md` records the 2026-05-21 `.gitignore` audit, the
  historical 2026-05-26 127-scan bundle, the 2026-06-05 full-validation
  paper-facing bundle plan, and cleanup candidates that are not required for the
  current full-validation claim.
- GitHub can carry the runbooks, Docker setup, scripts, reports, compact
  manifests, tables/metric summaries, and paper planning docs.
- The selected official non-avg Open3DSG checkpoint and full-validation row-level
  JSONL outputs should be released as a separate paper-facing result bundle with
  checksum verification. The existing verified
  `release/h001_core_results_20260526_160957.tar.zst` bundle is now
  historical/sensitivity evidence, not the default paper-facing bundle; its
  local tar/checksum copy was deleted during the 2026-06-05 cleanup.
- Large datasets, feature caches, and model caches remain intentionally ignored
  and must be rebuilt/downloaded or transferred separately on another computer.

Optional extension sequence:

- `relative_horizontal` has completed the non-GPU scope, coordinate, and bucket
  inspections. The current recommendation is
  `do_not_promote_relative_horizontal_to_main_claim`; the AAAI-path decision is
  to stop as appendix/limitation evidence. A targeted `front`/`behind`
  visual/frame-metadata check is optional only if the paper strategy later
  pivots to broader spatial-family coverage.
- `attachment_deferred` is the preferred next relation-family expansion if H001
  is upgraded: Docker scope/schema audit, G1 extractor contract, G1b
  evidence-only dry run, G1c point/surface validation, G2 verifier-policy
  design, G3 calibration/counterfactual route, G4 GT policy smoke, G4b
  error/visual sanity planning, G4c strict-only calibration-filter freeze, G5a
  pooled strict calibration fit, G5b bounded source scoring preflight, and G5c
  full-source protocol freeze are complete, so the next step is full-source
  scoring; then add source metrics/controls, bootstrap CI, and audit. A simple
  function-reasoning case study should come only after relation reliability is
  established.
- Qwen-VL extension status: full official validation downstream is complete
  with parser validation, adapter export, geometry join, metrics/controls,
  bootstrap CI, failure rows, and deterministic qualitative inspection. Keep
  Qwen as third-source appendix/extension evidence unless explicitly promoted
  into the main claim.
- AAAI source route: `paper/aaai/` now uses official AAAI-26 Author Kit style
  files checked on 2026-05-27 KST. `aaai2026.sty` was replaced from the
  official kit, `aaai2026.bst` already matched, and no official AAAI-27 author
  kit was confirmed.
- Reduced checkpoint smoke only if official route is intentionally paused or
  declared too slow; it must not become paper-result evidence.
- SceneFun3D/FunGraph3D only if the paper scope expands to functional or
  affordance relation reliability with a separate contract.

## Reviewer-Risk Defense

Likely reviewer attacks:

- "This is only a rule-based post-processing script."
- "The result is a VL-SAT-specific trick."
- "The claim overstates open-vocabulary or baseline-agnostic improvement."
- "Violation improves only because recall is pruned."
- "The denominator or filtered training split is cherry-picked."
- "The relation families are too narrow."

Required defenses:

- keep method framing as calibrated geometry-consistency evaluation and
  re-ranking, not a rule script;
- report recall and violation together;
- include semantic-only, calibrated, hard-filter, family-specific, and control
  conditions;
- report in-scope denominator, excluded rows, filtered train/validation counts,
  and covered Open3DSG contexts;
- add Open3DSG second-source metrics before making cross-predictor claims;
- treat Qwen-VL and functional/robotics benchmarks as separate optional tracks.
- cite and distinguish RelWitness before final submission: H001 is not a
  witness-supervised open-vocabulary generator, but a calibrated reliability
  layer and evaluation protocol over existing relation-source outputs.

## Sources Checked

- Checked / updated: 2026-05-22 KST
- `VL-SAT` official repository: https://github.com/wz7in/CVPR2023-VLSAT
- `VL-SAT` CVF page: https://openaccess.thecvf.com/content/CVPR2023/html/Wang_VL-SAT_Visual-Linguistic_Semantics_Assisted_Training_for_3D_Semantic_Scene_Graph_CVPR_2023_paper.html
- `Open3DSG` official repository: https://github.com/boschresearch/Open3DSG
- `Open3DSG` CVF/arXiv paper: https://arxiv.org/abs/2402.12259
- `CCL-3DSGG` CVF page: https://openaccess.thecvf.com/content/CVPR2024/html/Chen_CLIP-Driven_Open-Vocabulary_3D_Scene_Graph_Generation_via_Cross-Modality_Contrastive_Learning_CVPR_2024_paper.html
- `SGFormer` official repository: https://github.com/Andy20178/SGFormer
- `SGGpoint` official repository: https://github.com/chaoyivision/SGGpoint
- `RelWitness` arXiv page: https://arxiv.org/abs/2605.20823
- `ZING-3D` arXiv page: https://arxiv.org/abs/2510.21069
- `Open-World 3DSG-RAG` arXiv page: https://arxiv.org/abs/2511.05894
- `View-on-Graph` AAAI page: https://ojs.aaai.org/index.php/AAAI/article/view/37677
- `VIZOR` CVF PDF: https://openaccess.thecvf.com/content/WACV2026/papers/Madhavaram_VIZOR_Viewpoint-Invariant_Zero-Shot_Scene_Graph_Generation_for_3D_Scene_Reasoning_WACV_2026_paper.pdf
