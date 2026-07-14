# H001 Paper Preview

Last updated: 2026-07-14 KST

이 문서는 H001을 paper/experiment writing phase로 넘기기 직전에 현재까지의 연구 결과, 주장 범위, 실험 근거, caveat, 그리고 재시작 시 반드시 읽어야 할 파일을 한곳에 고정한 preview다. 최종 manuscript가 아니라 paper draft를 쓰기 위한 handoff 문서다.

Paper-facing name: `Beyond Semantic Confidence: Relation-Algebra-Constrained Geometric Compatibility for 3D Scene Graph Relations`. `H001` remains an internal identifier.

Current 2026-07-14 framing override:

- The active manuscript uses six top-level sections: Introduction, Related
  Work, Method, Experiments, Discussion and Limitations, and Conclusion.
  Problem Setup is integrated into Method; setup and result subsections are
  grouped under Experiments.
- The submission narrative is failure-first: observed inconsistency,
  structural cause, factor-isolation necessity, method, evidence, then
  limitations. Novelty is a predictor-agnostic reliability contract and
  evaluation framework, not a fusion-formula claim.
- RelCompat3D is a framework-level contribution. The strict train-only
  relation-algebra-constrained product is the main soft method and rank-average
  is a scale-robust framework instantiation; neither is claimed universally
  dominant.
- On SGFN, both satisfy the K=100 joint recall/verifier-violation gate. This
  supports the aggregate framework effect,
  while `support_contact` regression and the LLM-proxy/human-validity boundary
  remain explicit limits.
- The final paper scope is cross-predictor robustness on one shared
  3DSSG/3RScan target. ReplicaSSG/FROSS is de-scoped archived development
  provenance and is removed from the active submission route.
- Current AAAI-27 outputs are `paper/aaai/main_aaai27.pdf` (8 pages; technical
  content through page 7, references on pages 7--8),
  `supplement_aaai27.pdf` (2 pages), and the separate
  `reproducibility_checklist_aaai27.pdf` (2 pages). Final triplet log is
  `logs/h001_main_figure_refresh_20260714.log`; the active field bundle is
  `release/h001_aaai27_openreview_20260714_170829/`. It passes outer/inner
  checksums, ZIP extraction, structured-manifest validation, and author-path
  scans. Prior snapshots are preserved as historical provenance.
- H001 factorizes each row into predicate/family semantics `T_e`, raw
  predicate-independent same-pair geometry `G_e`, source relation score `Z_e`, and
  bounded constructed-target compatibility
  `C_e=sigmoid(h_a(Phi(T_e,G_e)))`, followed by exact relation-algebra orbit
  projection. The leakage boundary is `Z_e notin C_e`;
  product and rank-average remain instances of `S_e=F(Z_e,C_e)`.
- `y_cal` comes from train/dev GT positives plus high-margin counterfactual
  negatives and is not direct human physical validity. The old
  `control_p_geom_valid_only` removes `Z_e` but is not true `G_e`-only because
  the calibrator includes predicate/family and predicate-aligned interaction
  features.
- The factor-isolation package is complete for `T`-only, true-`G`-only,
  additive, interaction, wrong-`T`/pair, close-by swap, and vertical inverse
  controls. The selected strict family model passes its exact controls; pooled
  `M_int` fails structural controls and is not promoted. These diagnostics do
  not retroactively alter the SGFN gate.
- Uncertainty sensitivity reports decidable-only Violation, uncertainty
  rate, and a pessimistic bound. The structured product lowers all three
  relative to Source score at K=100 for VL-SAT, Open3DSG, and SGFN, so the
  aggregate result is not an uncertain-denominator artifact.
- The 69-parameter nonlinear rescorer, trained on disjoint internal-dev
  exact-label correctness, is stronger than the product on SGFN at low K and
  lowers K=100 Violation. This blocks formula superiority and is reported
  honestly; unlike RelCompat3D, it consumes source confidence and source-specific
  exact-label supervision.
- Applying that unchanged SGFN-supervised rescorer to VL-SAT and Open3DSG
  significantly loses Recall on VL-SAT at K=100 and on both sources at smaller
  K. It is therefore a source-adapted upper bound rather than a uniform
  alternative to the predictor-agnostic factor contract.
- Six relation-algebra candidates were evaluated behind a frozen 3DSSG-only
  gate. Only linked-counterfactual margin fitting plus exact orbit projection
  passes. It has exactly zero close-by swap and vertical-inverse error while
  preserving K=100 Recall continuity on all three sources. It is now the main
  compatibility model, and every comparator, uncertainty result, figure, and
  table has been rebuilt under the same strict model route.
- Figure 2 and one joint Recall/Violation table report
  K=`{5,10,20,50,100}` on VL-SAT, Open3DSG, and SGFN. A second table reports
  six fixed-model controls at K=50/100 in one column. K=100 is primary;
  smaller budgets show predictor-dependent trade-offs. Figures 1--3 are
  included as vector PDFs to preserve type and line quality.

2026-07-11 train-only provenance override:

- `train_only_reestablishment_v1` is complete with a disjoint
  1,061/117/157 firewall, zero final-validation rows in fit, a pre-inference
  execution contract, internal-dev acceptance, and a pre-final model/score
  hash lock.
- Final K=100 changes exact-label Recall from `0.951410` to `0.958963`
  (dR `+0.007553`, paired CI `[+0.004079,+0.011854]`) and verifier V from
  `0.062153` to `0.034252` (dV `-0.027901`, paired CI
  `[-0.030347,-0.025656]`).
- Final-row fitting leakage is zero. The full method-selection/prospective
  classification is maintained once in `docs/paper.md` and the authoritative
  experiment report rather than repeated throughout paper workspace files.
- Support/contact verifier V still regresses in family-wise views. Keep the
  aggregate framework wording and independent-human-validity boundary; do not claim
  family-uniform improvement or support/contact solved.
- The manuscript reports strict factor/counterfactual results without
  recasting the observed official validation target as prospective. Codex proxy
  results are excluded from the submission and isolated in
  `paper/paper_nonsub/`; human alignment remains optional and unclaimed.

Prior 2026-06-25 source snapshot:

- Main paper evidence remains VL-SAT full official validation plus Open3DSG full-validation `recovery_relaxed_views_min2/`.
- Low-K source-result reporting is accepted for K = `{5,10,20,50,100}`; point-metric provenance is present in both paper-facing `metrics_k_sweep/` roots, and K=1 stays sanity-check only.
- The calibrated-product operating point is `family_conditional_risk`
  (`semantic_score * p_geom_valid_family`). Pooled
  `probabilistic_recalibrated` (`semantic_score * p_geom_valid`) is an
  ablation/baseline, and the `p_geom_valid`-only control removes semantic score
  but is now named calibrator-only/no-`Z`, not true geometry-only.
- Qwen-VL full official validation downstream is complete and should be treated as appendix/extension evidence unless explicitly promoted.
- Active target-year PDF build:
  `logs/h001_structured_main_final_20260713.log`, exit 0. Outputs are
  `paper/aaai/main_aaai27.pdf` (9 pages; technical content through page 7 and
  references only on pages 8--9), `supplement_aaai27.pdf` (3 pages), and
  `reproducibility_checklist_aaai27.pdf` (2 pages). The previous upload set is
  synchronized with the verified 2026-07-13 field bundle.
- Remaining paper work is submission/package hygiene, not new main-source result generation.

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
For geometry-checkable 3D scene graph relation families, RelCompat3D learns
predictor-agnostic predicate--geometry compatibility with linked
counterfactuals and exact relation-algebra projection, reducing aggregate
geometric violations while preserving measurable recall tradeoffs across
VL-SAT, Open3DSG, and SGFN on one shared 3DSSG target.
```

Blocked current claim:

```text
This is a broad open-vocabulary 3DSSG generation improvement or arbitrary-baseline general method.
```

## Current Evidence Summary

Fact:

- Paper-facing full official validation scope has 157 scans, 548 contexts, 36,808 directed pairs, 957,008 `VL-SAT` prediction rows, 11,254 GT rows, and 3,972 in-scope measured-family GT relations. The earlier 127-scan scope is retained only as sensitivity/history.
- Docker experiment root: `experiments/H001_geom_reliability/`.
- The coordinated Docker route generated every main comparator, paired
  interval, uncertainty result, figure source, and table under
  `structured_main_v1/evaluation/`; all manifest validations pass.
- Open3DSG second-source path is complete for the measured measured-family setting. The historical 127-scan avg-BLIP downstream result remains reproduced and table-ready. R1 official non-avg checkpoint selection and separate non-avg downstream regeneration are also complete. The selected paper-facing route is now the full official validation branch, using the 548/548 Open3DSG recovery branch as the primary full-denominator Open3DSG result and the 533/548 covered branch as sensitivity / unmodified-source-route evidence.

2026-06-03 direction update:

- The intended paper-facing primary route is now full official
  `3DSSG_subset` validation after a complete Docker rerun, not the
  pilot-excluded 127-scan scope.
- Full official validation target: 157 scans, 548 contexts, 36,808 candidate
  directed pairs, 957,008 expected VL-SAT prediction rows, 11,254 GT rows, and
  3,972 measured-family GT rows.
- Docker `full_validation_scope_contract` has frozen the scope contract under
  `results/h001_geom_reliability/full_validation_transition/scope_contract/`;
  this was the protocol-freeze artifact.
- 2026-06-04: VL-SAT full-validation rerun is now metric-ready under
  `experiments/H001_geom_reliability/sources/vlsat/full_validation/`: raw
  dump/export, ground-truth JSONL, geometry join, metric eval, GT verifier
  eval, VL-SAT-only bootstrap CI, failure rows, and deterministic qualitative
  failure-case inspection are complete. Outputs are 957,008 predictions, 11,254
  GT rows, 3,972 measured-family GT rows, 59,841 diagnostic failure rows, and a
  36-case qualitative queue.
- 2026-06-05: Open3DSG full-validation is metric-ready in two forms. The
  original covered branch keeps 533/548 contexts with a 15-context preprocess
  caveat. The recovery branch
  `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/`
  reaches 548/548 by relaxing the visible-object gate to `min_visible=2` and
  regenerating relaxed views for two scans; feature audit, clean-exit raw dump,
  adapter, geometry, metrics, bootstrap CI, failure rows, and Table 6/caveat
  regeneration are complete. A new recovery-branch 36-case qualitative failure
  inspection is also complete.
- The earlier 127-scan results remain historical/sensitivity evidence. Within
  that historical scope, the completed R2 388/388 branch is the representative
  sensitivity result, and the old 377/388 branch is retained as the comparison
  row. The manuscript main table route is regenerated from the full official
  validation results: VL-SAT full-validation as the controlled anchor and
  Open3DSG `recovery_relaxed_views_min2/` as the primary full-denominator
  Open3DSG branch.
- Paper-facing provenance should state that final method design, hard-rule
  policies, counterfactual construction, and `p_geom_valid` calibration are
  train/train-dev-derived and frozen before validation source-result reporting.
- H001-Mini is hypothesis/feasibility evidence, not a paper metric or
  calibration/tuning split.
- Transition record:
  `results/h001_geom_reliability/full_validation_transition/report.md`.

## Key Metrics

### Current Promoted Structured Main, K=100

| source | Source score R/V | structured product R/V | rank-average R/V | RRF R/V | pooled product R/V | hard filter R/V |
| --- | --- | --- | --- | --- | --- | --- |
| VL-SAT | .9635/.0476 | .9688/.0325 | .9617/.0248 | .9610/.0233 | .9690/.0387 | .9627/.0000 |
| Open3DSG | .5161/.1242 | .6055/.0339 | .5994/.0531 | .5979/.0785 | .6443/.0747 | .5368/.0000 |
| SGFN | .9235/.0630 | .9418/.0372 | .9474/.0268 | .9074/.0266 | .9413/.0464 | .9270/.0000 |

Authority: `experiments/H001_geom_reliability/structured_main_v1/evaluation/`.
The model SHA256 is
`62d251f3ce60e2db54eb1748c277350e3b9e2c7c9d2be0312cf2fb323b761410`.

### VL-SAT Historical 127-Scan Sensitivity

This section is historical/sensitivity evidence only. Do not use these values
as the current paper-facing main table.

| condition | R@50 | R@100 | Violation@50 | Violation@100 | role |
| --- | ---: | ---: | ---: | ---: | --- |
| `semantic_only` | 0.9599 | 0.9894 | 0.0247 | 0.0469 | reproduced semantic ranking |
| `probabilistic_recalibrated` | 0.9642 | 0.9921 | 0.0234 | 0.0391 | historical pooled calibrated-risk ablation |
| `rule_verified_point_subtype` | 0.9587 | 0.9890 | 0.0000 | 0.0000 | hard-filter zero-violation diagnostic |
| `family_conditional_risk` | 0.9619 | 0.9914 | 0.0204 | 0.0310 | historical family-conditional RelCompat3D score |

Interpretation:

- `probabilistic_recalibrated` is the pooled calibrated-risk ablation, not the
  current main score.
- `rule_verified_point_subtype` demonstrates zero-violation behavior but should be reported as a diagnostic, not the default main operating point.
- `family_conditional_risk` gives a clearer historical violation reduction but
  is superseded by the relation-algebra-constrained structured product.

Pre-promotion full official validation continuity table:

| condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 | role |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `semantic_only` | 0.4194 | 0.6322 | 0.8074 | 0.9272 | 0.9635 | 0.0029 | 0.0082 | 0.0142 | 0.0268 | 0.0476 | full official validation source ranking |
| `probabilistic_recalibrated` | 0.4154 | 0.6322 | 0.8107 | 0.9305 | 0.9688 | 0.0015 | 0.0071 | 0.0120 | 0.0229 | 0.0404 | full-validation pooled calibrated-risk ablation |
| `rule_verified_point_subtype` | 0.4197 | 0.6317 | 0.8074 | 0.9257 | 0.9627 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | full-validation zero-violation diagnostic |
| `family_conditional_risk` | 0.4162 | 0.6309 | 0.8087 | 0.9288 | 0.9683 | 0.0011 | 0.0051 | 0.0109 | 0.0206 | 0.0333 | calibrated-product instantiation |

Full-validation interpretation:

- The direction is consistent with the hardened result on a broader official
  validation scope: the calibrated product reduces violations, the
  pooled score is a recall-favoring ablation, and rule filtering reaches zero
  violation with only a small recall tradeoff.
- Recall is lower than the 127-scan hardened result because the full official
  validation denominator is broader and includes all 157 scans / 548 contexts.
- This table is retained for provenance. Current paper tables/prose are
  regenerated from the promoted structured-main artifacts above.

### Open3DSG Full Validation Recovery

| condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 | role |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `semantic_only` | 0.0368 | 0.1002 | 0.1991 | 0.4096 | 0.5161 | 0.5131 | 0.3255 | 0.2088 | 0.1386 | 0.1242 | recovery full-validation source ranking |
| `probabilistic_recalibrated` | 0.0826 | 0.1581 | 0.2603 | 0.3975 | 0.5723 | 0.0628 | 0.0699 | 0.0654 | 0.0606 | 0.0811 | recovery pooled calibrated-risk ablation |
| `rule_verified_point_subtype` | 0.0707 | 0.1314 | 0.2422 | 0.4295 | 0.5368 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | recovery zero-violation diagnostic |
| `family_conditional_risk` | 0.0984 | 0.1921 | 0.3291 | 0.4658 | 0.6047 | 0.0420 | 0.0482 | 0.0441 | 0.0286 | 0.0341 | calibrated-product instantiation |

Recovery caveat: this removes the 15-context missing-preprocess denominator
caveat, but it is a recovery-policy variant rather than the unmodified Open3DSG
preprocess route.

### VL-SAT Full-Validation Controls

| condition | R@50 | R@100 | Violation@50 | Violation@100 | purpose |
| --- | ---: | ---: | ---: | ---: | --- |
| `control_p_geom_valid_only` | 0.2110 | 0.5184 | 0.0661 | 0.0711 | geometry-only ranking control; no semantic score |
| `control_distance_only` | 0.3746 | 0.5554 | 0.0724 | 0.0981 | simple distance heuristic control |
| `control_shuffled_geometry` | 0.8890 | 0.9494 | 0.0295 | 0.0588 | breaks geometry identity while preserving distribution |
| `control_wrong_pair_geometry` | 0.8915 | 0.9529 | 0.0320 | 0.0601 | tests object-pair identity |

Interpretation:

- Geometry-only control is `p_geom_valid` ranking without semantic score; it is
  separate from pooled calibrated reranking.
- Simple distance is not enough.
- Wrong-pair and shuffled-geometry controls degrade performance, supporting the claim that relation-level object-pair geometry matters.

### GT-Based Verifier Evaluation

| metric | rows | value |
| --- | ---: | ---: |
| GT-positive nonviolated rate | 3,972 | 0.9965 |
| GT-derived negative nonsatisfied rate | 3,972 | 0.9673 |
| `p_geom_valid` AUROC | 7,944 | 0.9772 |
| `p_geom_valid` AUPRC | 7,944 | 0.9729 |
| `p_geom_valid` Brier | 7,944 | 0.0543 |

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

### Open3DSG Historical 127-Scan Sensitivity

| branch | condition | R@50 | R@100 | Violation@50 | Violation@100 | role |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| old 377/388 | `semantic_only` | 0.3945 | 0.4963 | 0.1326 | 0.1195 | comparison row |
| old 377/388 | `probabilistic_recalibrated` | 0.3843 | 0.5580 | 0.0575 | 0.0803 | comparison row |
| old 377/388 | `rule_verified_point_subtype` | 0.4149 | 0.5238 | 0.0000 | 0.0000 | comparison row |
| old 377/388 | `family_conditional_risk` | 0.4530 | 0.5984 | 0.0228 | 0.0311 | comparison row |
| R2 388/388 | `semantic_only` | 0.3972 | 0.4990 | 0.1331 | 0.1199 | representative historical sensitivity |
| R2 388/388 | `probabilistic_recalibrated` | 0.3870 | 0.5607 | 0.0594 | 0.0811 | representative historical sensitivity |
| R2 388/388 | `rule_verified_point_subtype` | 0.4177 | 0.5265 | 0.0000 | 0.0000 | representative historical sensitivity |
| R2 388/388 | `family_conditional_risk` | 0.4558 | 0.6012 | 0.0254 | 0.0323 | representative historical sensitivity |

Interpretation:

- Open3DSG historical 127-scan evidence is retained as sensitivity evidence that geometry-consistency can reduce violations in the same H001 families.
- R2 removes the historical missing-context caveat inside the 127-scan scope,
  but the metric changes are small: R@100 increases by about +0.28 percentage
  points and Violation@100 changes by +0.00 to +0.13 points. This supports the
  appendix claim that the old 377/388 missing contexts did not drive the trend.
- R2 provenance review confirms the clean-return raw files are row/predicate-
  score equivalent to the canonical R2 raw dump after excluding run metadata;
  the process-level exit-137 teardown caveat remains visible.
- The best Open3DSG pattern is not identical to `VL-SAT`; use it to support cross-source reliability evidence, not to claim universal behavior.
- `family_conditional_risk` is the calibrated-product instantiation; present
  `probabilistic_recalibrated` as pooled ablation and geometry-only as a
  separate control.

## Open3DSG Caveats To Preserve

Fact:

- Open3DSG checkpoint is generated by Docker reproduction, not downloaded as an official trained checkpoint.
- Paper-facing full-validation checkpoint: official non-avg BLIP
  `epoch=13-step=13104.ckpt` from run
  `25da9c4c00214f3b880cedbb2a124177`.
- Selection signal: train-dev `val/loss=0.5724539160728455` at step 13103,
  chosen before selected-route H001 held-out metric/failure/visual inspection.
- Historical 127-scan avg-BLIP branch remains reproduced and stronger on
  train-dev loss (`0.32881081104278564`), but it is now sensitivity/historical
  evidence rather than the main paper-facing route.
- Runtime train split is filtered to 3,744/3,852 train subgraphs.
- Train-dev validation split is filtered to 156/160 subgraphs.
- Full-validation primary Open3DSG route covers 548/548 contexts through
  `recovery_relaxed_views_min2/`.
- Exact-label measured-family denominator is 3,972 GT relations on the full official
  validation route.
- Qualitative inspection found 10/36 sampled rule-violated cases with `p_geom_valid > 0.9`.

Paper wording rule:

- Every paper-facing Open3DSG full-validation table/discussion must mention the
  selected official non-avg checkpoint, filtered train/dev provenance,
  exact-label denominator, residual calibration risk, and recovery policy:
  `OPEN3DSG_MIN_VISIBLE_OBJECTS=2` plus relaxed view regeneration for two scans.
- The 533/548 covered full-validation branch should be reported as sensitivity /
  unmodified-source-route evidence.
- Historical 127-scan sensitivity should be reported as old 377/388 versus R2
  388/388. Use R2 as the representative historical branch, but keep it outside
  the main result table because the paper-facing denominator is the full
  official validation route.
- Historical 127-scan exit-137 attempts are run records, not final raw-dump
  provenance caveats.

## Failure Analysis

Fact:

- VL-SAT full-validation failure-analysis rows: 59,841.
- VL-SAT validation errors: 0.
- VL-SAT visual-audit queue rows: 2,897.
- VL-SAT qualitative case inspection: 36 cases; 28/36 demoted by
  geometry-aware reranking, 8/36 promoted or retained, and 7/36 were
  rule-violated but still had `p_geom_valid > 0.9`.
- Open3DSG recovery full-validation failure-analysis rows: 82,155.
- Open3DSG recovery validation errors: 0.
- Open3DSG recovery visual-audit queue rows: 8,821.
- Open3DSG recovery qualitative case inspection: 36 cases; 25/36 demoted by
  geometry-aware reranking, 11/36 promoted or retained, and 8/36 were
  rule-violated but still had `p_geom_valid > 0.9`.

Interpretation:

- The failure analysis supports the failure-mechanism narrative: semantic plausibility and physical consistency can diverge.
- It also exposes residual calibration risk, which should be reported rather than hidden.

## Optional Scope Expansion Boundary

Fact:

- `relative_horizontal` is a separate expansion track, not part of the current
  main claim.
- Docker scope audit finds 3,570 candidate GT rows and an expanded candidate
  denominator of 6,115 / 7,505 if validated.
- Docker coordinate audit and bucket inspection are complete but blocked for
  promotion: best frame `scan_left_neg_x_front_neg_y`, macro strict purity
  0.7725, `front`/`behind` strict purity 0.7445, inverse consistency 1.0,
  wrong-frame gap 0.1231, and `front`/`behind` ambiguity buckets remain large.
- Current recommendation: `do_not_promote_relative_horizontal_to_main_claim`.
- Current AAAI-path decision: freeze as appendix/limitation evidence and do not
  run expanded-family metrics.
- `relative_lateral` was then tested as a narrower left/right-only split.
  Policy freeze, train/dev policy lock, train-only calibration, and dev failure
  diagnosis are complete.
- `relative_lateral` train/dev result: train positive strict purity 0.8738,
  dev positive strict purity 0.6975, dev lenient nonviolated rate 0.8095, and
  dev calibration AUROC 0.7401.
- `relative_lateral` dev diagnosis: strict contradictions are 72 rows / 36
  physical pairs concentrated in two dev scans; uncertain positives are 140
  rows / 70 physical pairs; about half of both buckets involve same-label object
  pairs; most uncertain rows are orthogonal-axis dominance.

Interpretation:

- This is useful scope-boundary evidence, not a broader-coverage result.
- Do not run or report expanded-family VL-SAT/Open3DSG metrics on the current
  AAAI path. A targeted `front`/`behind` visual/frame-metadata check is only
  justified if the paper strategy later pivots to broader spatial-family
  coverage.
- Current `relative_lateral` decision: stop as appendix/future-work boundary.
  Do not run paper-facing lateral source metrics from the current strict policy.
  A future revival needs a separate predeclared frame/annotation study, not
  threshold tuning.

## Future Attachment Upgrade

Fact:

- `attachment_deferred` is a future H001 upgrade path, not part of the current
  main claim.
- Docker G0 scope/schema audit, G1 extractor contract, G1b evidence-only dry
  run, G1c point/surface validation, G2 conservative verifier-policy design,
  G3 train-dev calibration/counterfactual route, G4 GT policy smoke, G4b
  error/visual sanity planning, G4c strict-only calibration-filter freeze, G5a
  pooled strict calibration fit, G5b bounded source scoring preflight, G5c
  full-source protocol freeze, and G5d full-source scoring/metrics/controls/
  bootstrap are complete with status `attachment_deferred_g5d_full_source_metrics_ready`.
- Current denominator policy records 967 GT rows: `attached to` 808,
  `hanging on` 126, and `connected to` 33.
- If validated, the candidate denominator grows from 2,545 to 3,512.
- Candidate source rows already exist: VL-SAT 77,748 and Open3DSG 57,300.
- G5d source evidence exists, but the track is not current main-claim evidence.
- The extractor contract explicitly forbids `verification_status`,
  `p_geom_valid`, recall credit, and reranking scores in extractor output.
- G1c produced 36/36 schema-valid point/surface-ready evidence rows and 0
  validation errors, with 9 rows each from GT positives, counterfactuals,
  VL-SAT, and Open3DSG; 27/36 rows have near-contact points under the 0.05m
  diagnostic threshold.
- G2 freezes a 9-subtype verifier-policy contract with conservative defaults:
  near-contact 0.05m, uncertain contact band 0.05-0.15m, clear-far distance
  0.30m, min near-contact points 3, and min contact patch score 0.20. It emits
  no decision rows, calibration, source scoring, or metrics.
- G3 prepares 315 train/dev positive seeds and 446 counterfactual negative
  seeds with held-out scan overlap 0. G4 applies the frozen policy to 36 smoke
  rows and 761 train/dev seed rows with schema validation passed, positive
  nonviolated 0.9048, counterfactual nonsatisfied 0.8274, positive strict
  satisfied 0.3841, counterfactual strict violated 0.4574, and uncertain rate
  0.4323. G4b freezes 436 review cases, a 50-row visual sanity queue, 121
  strict positive candidates, 204 strict negative candidates, 77
  false-satisfied counterfactuals, 30 false-violated positives, and 329
  uncertain rows. G4c freezes 325 strict calibration rows, with 121 strict
  positives, 204 strict negatives, and 436 excluded non-strict rows. G5a fits
  pooled model `h001-attachment-deferred-p-geom-valid-strict-v1` with dev
  Brier/NLL/ECE 0.0010/0.0077/0.0071 and dev AUROC/AUPRC 1.0/1.0 on 83 strict
  rows. G5b scores 120 scan-diverse bounded source rows with evidence ready
  120/120 and validation errors 0. G5c freezes 69 deterministic full-source
  shards for 135,048 rows and source-specific covered denominators: VL-SAT
  967/967 and Open3DSG 768/967. G5d scores all 135,048 rows with validation
  errors 0 and computes source metrics/controls/bootstrap. Remaining promotion
  blockers are Open3DSG 199 missing exact-label GT rows, noisy `attached to`
  behavior, no `connected to` dev strict rows, and likely additional
  failure/visual audit.
- The nine-subtype contract is now legacy provenance. Subtype-v2 separates
  predicate semantics, physical mechanism, and observability/applicability.
  Its migration covers 761 train/dev rows; 199/325 legacy strict rows used an
  `ambiguous_*` subtype. Official-validation routing covers 190,722 rows:
  74,433 bidirectional, 19,287 positive-only, and 97,002 abstained.
- The raw-selective v2 product fails. The bounded v2 multiplier passes VL-SAT
  K=100 but fails Open3DSG K=100 and VL-SAT K=50. Both are retrospective
  development diagnostics and remain outside the paper result set.

Interpretation:

- This is a better next relation-family expansion than `relative_horizontal`
  because it stays inside H001's physical-consistency mechanism: attachment and
  hanging should be constrained by contact, surface type, gravity, and object
  affordance.
- It is also harder than support/contact and cannot be promoted without
  resolving its mechanism/observability labels, rebuilding the target and
  verifier contract, and passing source gates after a new model lock.
  Main-claim promotion requires explicit final user confirmation.
- A small function-reasoning case study is reasonable only after the
  attachment-reliability result exists; it should show simple physical
  precondition reasoning, not claim broad affordance or robotics performance.

## Main Tables And Figures To Draft

Fact:

- First-pass manuscript prose and claim/evidence review are recorded in
  `paper/draft.md`; the current AAAI-style LaTeX source conversion is under
  `paper/aaai/`; the historical ICCV-style source is under `archive/paper/iccv/`;
  Figure 1-3 source rows and caveat wording are locked in `paper/figures.md`;
  verified/layout-reviewed draft SVGs are under `paper/generated/figures/`.
- AAAI Table 1: fixed RelCompat3D evaluation scope and denominator.
- AAAI Table 2: main source results, with Open3DSG first as the main
  open-vocabulary case study and `VL-SAT` second as the controlled reproduced
  anchor.
- AAAI Table 3: controls and diagnostics separating calibrated same-pair
  geometry from geometry-only, distance-only, shuffled-geometry, and wrong-pair
  explanations.
- SGFN is reported as an additional exact-label source comparison of semantic,
  calibrated product, rank-average, and RRF, with verifier/human-validity
  boundaries; it is not presented as a separate prospective table.
- ReplicaSSG/FROSS is outside the finalized 3DSSG-only paper and must not be
  included in the active supplement package.
- Source-specific claim boundary / non-claims, GT-based verifier evaluation,
  structured audit, visual sanity check, and detailed family rows are kept as
  prose-backed reviewer-defense evidence unless an appendix is added.
- Figure specs are already generated under `results/h001_geom_reliability/figures/`.

Recommended paper narrative:

1. Define failure: semantic relation confidence is not calibrated to physical relation consistency.
2. Define target families: `support_contact`, `proximity`, `relative_vertical`.
3. Present calibrated geometry-consistency framework.
4. Show Open3DSG as the main open-vocabulary case study, with VL-SAT as the controlled reproduced anchor.
5. Use controls, GT-based verifier evaluation, and audit as prose-backed reviewer defense.
6. Use failure analysis to explain where the framework helps and where residual risk remains.
7. Keep Qwen-VL as optional extension unless full metric evidence is added.

## Reviewer Defense Map

| reviewer attack | current defense | remaining discipline |
| --- | --- | --- |
| "This is just a hand-coded verifier." | Frame as calibrated evaluation/re-ranking framework with calibration, controls, GT counterfactuals, and failure analysis. | Avoid script-level method wording. |
| "It only works on VL-SAT." | Open3DSG second-source metric evidence is ready. | Keep claim within measured families. |
| "It trades recall for filtering." | Report R@K and Violation@K together; calibrated product, rank-average, RRF, pooled calibration, and strict diagnostics expose different tradeoffs. | Include source-dependent Pareto/tradeoff wording. |
| "Rules were tuned on test set." | Denominator policy, metric scope, checkpoint selection, and caveat wording are fixed before paper writing; GT-based verifier eval exists. | State selection/provenance clearly. |
| "Open3DSG reproduction is not exact." | Docker provenance, selected official non-avg checkpoint record, full-validation recovery-policy disclosure, and 533/548 covered-branch sensitivity evidence. | Do not claim Open3DSG leaderboard/SOTA reproduction; frame as source-output reliability evidence. |
| "Open-vocabulary claim is too broad." | Current claim is measured reliability-layer evidence, not broad generation improvement. | Keep non-claims visible. |

## Optional Extensions

Qwen-VL:

- Current status: third semantic source / modern VLM extension with full official validation downstream complete.
- Full-validation scope: 157 scans, 548 contexts, 110,424 query rows, 46,506 inferable input rows, 63,918 missing query rows, 187 shards, 35,131 exported predictions, 32,236 in-scope predictions, and 3,972 measured-family GT rows.
- Downstream artifacts: parser validation, adapter export, geometry join, metrics/controls, bootstrap CI, 31,881 failure rows, and 36 deterministic qualitative cases.
- Key diagnostic metrics: semantic_only R@50/R@100 `0.2815/0.3600`, V@50/@100 `0.1226/0.1246`; probabilistic_recalibrated `0.3215/0.3653`, V `0.0795/0.1166`; rule_verified_point_subtype `0.3009/0.3630`, V `0.0/0.0`; family_conditional_risk `0.3379/0.3653`, V `0.0510/0.1113`.
- It should stay appendix/extension evidence unless the main claim is explicitly widened.

FROSS:

- Official ReplicaSSG full-trajectory inference is complete, so the earlier
  runtime blocker is resolved for this route.
- Exact `near/above/under` mappings cover proximity and relative-vertical, not
  support/contact. The untouched 11-scene test passes all provenance gates but
  fails the pre-registered K=100 framework gate.
- Treat it as external negative/limitation evidence, not a positive extension
  or a reason to retune K, fusion, mapping, or family scope.

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
9. `paper/README.md`
10. `paper/preview.md`
11. `paper/risk.md`
12. `paper/appendix.md`
13. `paper/outline.md`
14. `paper/draft.md`
15. `paper/aaai/README.md`
16. `paper/aaai/main.tex`
17. `archive/paper/iccv/README.md`
18. `paper/figures.md`

### Must-Read Hypothesis Files

Read these to recover the claim, method, and evaluation contract:

1. `archive/hypothesis_records/hypothesis/README.md`
2. `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/01_overview.md`
3. `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/02_method.md`
4. `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/03_data_baseline.md`
5. `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/04_results.md`
6. `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/05_audit.md`
7. `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/06_second_source.md`
8. `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/07_experiment_spec.md`

### Must-Read Experiment Result Files

Read these to recover the locked paper-result state:

1. `experiments/H001_geom_reliability/README.md`
2. `results/h001_geom_reliability/report.md`
3. `results/h001_geom_reliability/manifest.lock.json`
4. `experiments/H001_geom_reliability/commands.md`
5. `results/h001_geom_reliability/tables/table1_main_prediction.md`
6. `results/h001_geom_reliability/tables/table2_controls.md`
7. `results/h001_geom_reliability/tables/table3_gt_verifier.md`
8. `results/h001_geom_reliability/tables/table4_audit.md`
9. `results/h001_geom_reliability/tables/table5_claim_boundary.md`
10. `results/h001_geom_reliability/tables/table6_cross_source_status.md`
11. `results/h001_geom_reliability/figures/figure_specs.md`
12. `results/h001_geom_reliability/bootstrap_ci/summary.md`

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

### Must-Read Qwen-VL Files

Read these before resuming Qwen-VL or moving the run to another computer:

1. `experiments/H001_geom_reliability/sources/qwen_vl/README.md`
2. `experiments/H001_geom_reliability/sources/qwen_vl/report.md`
3. `experiments/H001_geom_reliability/sources/qwen_vl/status.json`
4. `configs/qwen_vl/compose.qwen.yaml`
5. `experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/manifest.json`
6. `experiments/H001_geom_reliability/sources/qwen_vl/full_source_inference_plan/commands.md`
7. `experiments/H001_geom_reliability/sources/qwen_vl/full_source_runtime/manifests/`
8. `logs/qwen_vl_full_source_infer_remaining_20260527_023111.status.tsv`
9. `logs/qwen_vl_full_source_infer_remaining_20260527_023111.exit`

### Runtime Data That May Need Rebuild

These are usually not safe to assume on a new computer:

| runtime item | current expected path |
| --- | --- |
| Raw 3RScan payload | `local_dataset/3RScan/scans/` |
| VL-SAT code/data/checkpoints | `local_dataset/VLSAT_code/CVPR2023-VLSAT/` |
| Open3DSG training root | `local_dataset/Open3DSG_staged/training_repro/` |
| Open3DSG H001 eval root | `local_dataset/Open3DSG_staged/h001_runtime/` |
| Open3DSG paper-facing checkpoint | `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/25da9c4c00214f3b880cedbb2a124177/checkpoints/epoch=13-step=13104.ckpt` (`avg_blip_emb=False`; SHA-256 `ca86d429...d76bb`) |
| Open3DSG historical checkpoint | `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt` (127-scan averaged-BLIP sensitivity only; SHA-256 `c1302882...d64511`) |
| Open3DSG train/dev features | `local_dataset/Open3DSG_staged/training_repro/output/features/clip_features_h001_official_blip_top5_scales3/` |
| Open3DSG H001 eval features | `local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3/` |
| Qwen-VL model cache | `local_dataset/model_cache/huggingface/qwen_vl/Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17/` |
| Qwen-VL full-source crops | `local_dataset/qwen_vl_crops/full_source/` |

Recovery rule:

- Do not start by retraining or redownloading everything.
- First read `docs/reproducibility.md`.
- Then verify which local paths exist.
- Only rebuild missing payloads/checkpoints/features with the Docker commands recorded in `docs/reproducibility.md` and `experiments/H001_geom_reliability/commands.md`.
- Long downloads, feature dumps, training, decompression, and preprocessing must run in `tmux` or background jobs with timestamped logs under `logs/`.

## Immediate Next Step

Recommended next action:

1. Use `paper/draft.md` as the active reviewed first-pass manuscript prose, `paper/aaai/` as the current AAAI-style LaTeX source, and `paper/generated/figures/` as the active draft figure output.
2. Treat the claim-consistency review in `paper/outline.md` as the current paper guardrail: title, contributions, abstract, Introduction, table captions, and figure captions must stay within the scoped relation-reliability claim.
3. Treat the reproducibility checklist as a separate AAAI-27 OpenReview upload.
   The verified containerized-build triplet is `main_aaai27.pdf` (8 pages),
   `supplement_aaai27.pdf` (2 pages), and
   `reproducibility_checklist_aaai27.pdf` (2 pages). Remaining work is author
   metadata, final public license/artifact URL, and optional human alignment,
   not source-result regeneration.
4. Treat the AAAI reviewer-defense pass as updated for the selected full-validation route: hand-coded verifier, geometry-only/distance, recall-tradeoff, Open3DSG recovery-policy provenance, family-selection, and AAAI-relevance attacks must all remain answered during polish.
5. Treat `paper/appendix.md` as the current appendix/provenance owner: calibrator/threshold provenance, Open3DSG caveat consistency, Figure 3 optionality, and Qwen-VL third-source boundary are recorded there.
6. Keep Open3DSG caveats explicit during any further polish; caption compression must not hide selected-checkpoint provenance, filtered split, exact-label denominator, recovery policy, 533/548 sensitivity branch, or residual calibration risk.
7. Keep Qwen-VL as third-source extension only unless the user explicitly promotes it into the main claim after reviewing the completed extension evidence.
