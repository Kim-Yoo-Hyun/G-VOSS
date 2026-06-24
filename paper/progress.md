# H001 Experiment Progress Rationale

Last updated: 2026-06-23 KST

This document explains why H001 moved from hypothesis checks to Docker paper
experiments, why each next experiment was introduced, and how the key results
should be interpreted. It is a progress rationale, not a replacement for
`paper/draft.md`, `paper/preview.md`, or the Docker result tables.

Paper-facing name: `GeoCalib: Calibrating Geometric Consistency for Reliable 3D Scene Graph Relations`; `H001` remains the internal experiment identifier.

Current progress snapshot:

- Main source-result evidence is complete for the scoped GeoCalib claim.
- Low-K reporting is accepted for K = `{5,10,20,50,100}`; point-metric provenance is present in both paper-facing `metrics_k_sweep/` roots, and K=1 remains sanity-check only.
- Qwen-VL full official validation downstream is complete as appendix/extension evidence, not as a main-source replacement.
- Latest known paper build is `logs/h001_aaai_pdf_build_lowk_full_20260623_191806.log`, exit 0, 9 pages.
- Remaining work is submission/package hygiene and artifact packaging, not new main-source experiments.

## Research Claim Being Tested

H001 does not propose a new 3D Scene Graph generator. It tests a narrower
reliability claim:

```text
For geometry-checkable 3D scene graph relation families, calibrated
geometry-consistency scoring can expose and reduce semantically plausible but
physically inconsistent relation predictions while reporting recall tradeoffs.
```

The claim is restricted to `support_contact`, `proximity`, and
`relative_vertical`. This scope exists because these families can be checked by
explicit 3D geometry. Functional, social, affordance, relative-horizontal, and
open-ended language relations were not promoted into the main claim because the
current verifier evidence does not cover them.

## Stage 1: H001-Mini Smoke

Why this stage was run:

- The first question was whether semantic predictions contain enough
  geometry-inconsistent rows to make a reliability layer meaningful.
- A small pilot was cheaper than immediately building Docker-scale experiments.

What it showed:

| condition | R@50 | R@100 | Violation@100 | interpretation |
| --- | ---: | ---: | ---: | --- |
| `semantic_only` | 0.8741 | 0.9263 | not final | source ranking baseline |
| `probabilistic_recalibrated` | 0.8831 | 0.9353 | 0.0193 | positive smoke signal |

Why we moved on:

- The signal was positive but not top-tier evidence.
- The pilot did not have enough denominator discipline, controls, or
  reproducibility guarantees.
- Next step therefore had to be a hardened held-out evaluation with fixed
  denominator and paper-safe metrics.

## Stage 2: Hardened VL-SAT Evaluation (Historical 127-Scan Route)

Why this stage was run:

- `VL-SAT` had official code/checkpoint route and was the cleanest first
  relation-source anchor.
- The hypothesis needed a fixed held-out scope, exact prediction/GT row counts,
  and Docker-promotable artifacts.

Historical fixed scope:

| item | count |
| --- | ---: |
| scans | 127 |
| subgraphs | 388 |
| directed pairs | 25,916 |
| prediction rows | 673,816 |
| GT rows | 7,505 |
| in-scope GT denominator | 2,545 |

Historical key result:

| condition | R@50 | R@100 | Violation@50 | Violation@100 | reading |
| --- | ---: | ---: | ---: | ---: | --- |
| `semantic_only` | 0.9599 | 0.9894 | 0.0247 | 0.0469 | reproduced source ranking |
| `probabilistic_recalibrated` | 0.9642 | 0.9921 | 0.0234 | 0.0391 | recall-first calibrated setting |
| `family_conditional_risk` | 0.9619 | 0.9914 | 0.0204 | 0.0310 | family-conditional calibrated risk setting |
| `rule_verified_point_subtype` | 0.9587 | 0.9890 | 0.0000 | 0.0000 | hard-filter diagnostic |

Interpretation:

- The main signal is not just hard pruning. `probabilistic_recalibrated`
  preserves or slightly improves exact-label recall while reducing violations.
- `rule_verified_point_subtype` is useful as a zero-violation diagnostic, but
  it should not be framed as the default method because a reviewer could read
  it as simply filtering away difficult relations.
- `family_conditional_risk` shows a stronger violation-reduction
  operating point and motivates family-conditional calibration as a method variant.

Why we moved on:

- A single-source `VL-SAT` result could be attacked as a method-specific trick.
- The next required evidence was nontriviality controls and independent verifier
  checks.

## Stage 3: Nontriviality Controls (Historical 127-Scan Route)

Why this stage was run:

- Reviewers would ask whether the gain comes from a trivial spatial heuristic.
- H001 needed to show that semantic confidence, object-pair identity, and
  calibrated geometry all matter.

Historical control result:

| control | R@50 | R@100 | Violation@100 | what it tests |
| --- | ---: | ---: | ---: | --- |
| `control_p_geom_valid_only` | 0.2028 | 0.5049 | 0.0701 | geometry alone is insufficient |
| `control_distance_only` | 0.3835 | 0.5642 | 0.0993 | distance alone is insufficient |
| `control_shuffled_geometry` | 0.9297 | 0.9788 | 0.0559 | geometry distribution is insufficient |
| `control_wrong_pair_geometry` | 0.9242 | 0.9788 | 0.0581 | correct object-pair identity matters |

Interpretation:

- Geometry-only and distance-only controls perform much worse, so the method is
  not a simple geometry heuristic.
- Shuffled and wrong-pair controls degrade behavior, supporting the
  identity-preserving join as part of the contribution.

Why we moved on:

- Controls defended the re-ranking mechanism, but not the verifier itself.
- The next step was to test whether `p_geom_valid` separates GT-positive
  relations from deterministic counterfactual negatives.

## Stage 4: GT-Based Verifier Evaluation (Historical 127-Scan Route)

Why this stage was run:

- A human audit would be slow and subjective if used as the primary verifier
  validation.
- GT positives and controlled counterfactual negatives provide a lower-burden
  evaluation of the geometry-validity signal.

Historical result:

| metric | rows | value |
| --- | ---: | ---: |
| GT-positive nonviolated rate | 2,545 | 0.9972 |
| GT-derived negative nonsatisfied rate | 2,545 | 0.9694 |
| `p_geom_valid` AUROC | 5,090 | 0.9779 |
| `p_geom_valid` AUPRC | 5,090 | 0.9737 |
| `p_geom_valid` Brier | 5,090 | 0.0538 |

Interpretation:

- The verifier signal has strong GT-positive/counterfactual support.
- This supports `p_geom_valid` as a reliability signal, while not proving
  physical correctness for every predicted row.

Why we moved on:

- GT/counterfactual evaluation does not replace qualitative sanity checks.
- The next step was a reduced visual/structured audit to confirm that flagged
  relation-quality issues correspond to plausible visual/geometric failures.

## Stage 5: Structured Audit And Reduced Visual Sanity

Why this stage was run:

- The method needed reviewer-defense evidence that violation labels correspond
  to meaningful relation-quality problems.
- A full large-scale human audit was not necessary for the hypothesis gate once
  GT-based verifier evaluation existed.

Result:

| source | rows | metric | value | caveat |
| --- | ---: | --- | ---: | --- |
| structured audit | 250 | quality-issue precision | 0.8933 | non-independent structured audit |
| visual spot-check | 50 | target-bucket quality-issue rate | 0.9333 | reviewer `yhkim`, reduced sanity check |
| visual spot-check | 50 | contradiction rate | 0.0333 | target-bucket contradiction |

Interpretation:

- The audit supports the failure interpretation.
- It must not be described as a large-scale or strictly blinded independent
  human study.

Why we moved on:

- At this point the hypothesis was sufficiently supported for a scoped
  `VL-SAT` reliability claim.
- For top-tier positioning, however, a single-source result was still weak.
- The next required experiment was a second-source relation predictor.

## Stage 6: Experiment Transition Gate

Why this gate existed:

- Hypothesis-stage artifacts were enough to decide feasibility, but not enough
  for paper-result claims.
- The user set a rule that paper experiments must be Docker reproducible.

What changed:

- H001 moved from hypothesis scripts/artifacts into
  `experiments/H001_geom_reliability/`.
- Docker table generation produced Table 1-6, locked manifests, reports, and
  paper-ready metric artifacts.

Interpretation:

- This transition prevented host-only or one-off outputs from becoming paper
  evidence.
- It also made later Open3DSG work compatible with the same row contract,
  geometry join, and metric evaluation.

## Stage 7: Open3DSG Second-Source Reproduction

Why this stage was run:

- A `VL-SAT`-only claim could be attacked as baseline-specific.
- Open3DSG was selected over a single-baseline justification because it is a
  stronger top-tier defense: it tests whether the same reliability layer works
  on a different relation source with open-vocabulary motivation.

Why this took many substeps:

- No trusted final trained Open3DSG checkpoint was confirmed in the official
  repository.
- Therefore we needed Dockerized payload staging, feature dump, training,
  checkpoint selection, H001 eval feature generation, raw-dump identity audit,
  adapter export, geometry join, metric evaluation, and caveat wording.

Historical 127-scan caveats:

- The historical 127-scan result is a Docker-reproduced averaged-BLIP variant.
- R1 official non-avg checkpoint selection and downstream regeneration are now
  complete as sensitivity evidence. The current paper-facing Open3DSG result is
  instead the full-validation `recovery_relaxed_views_min2/` branch using the
  selected official non-avg checkpoint.
- Train split is filtered to 3,744/3,852 preprocessed-ready subgraphs.
- Train-dev validation is 156/160 subgraphs.
- H001 covered loadable eval scope started at 377/388 contexts with
  `validation_missing_preprocessed:11`. The R2 covered-recovery sensitivity
  branch now reaches 388/388 contexts and completes raw identity, adapter,
  geometry, metrics, bootstrap CI, table/caveat reporting, and provenance
  review. The clean-return raw files are row/predicate-score equivalent to the
  canonical R2 raw dump after excluding run metadata, while the process-level
  exit-137 teardown caveat remains.
- Recall is exact predicate-label recall over the historical 2,545-row
  measured-family denominator.

Historical Open3DSG 127-scan sensitivity result:

| branch | condition | R@50 | R@100 | Violation@50 | Violation@100 |
| --- | --- | ---: | ---: | ---: | ---: |
| old 377/388 | `semantic_only` | 0.3945 | 0.4963 | 0.1326 | 0.1195 |
| old 377/388 | `probabilistic_recalibrated` | 0.3843 | 0.5580 | 0.0575 | 0.0803 |
| old 377/388 | `rule_verified_point_subtype` | 0.4149 | 0.5238 | 0.0000 | 0.0000 |
| old 377/388 | `family_conditional_risk` | 0.4530 | 0.5984 | 0.0228 | 0.0311 |
| R2 388/388 | `semantic_only` | 0.3972 | 0.4990 | 0.1331 | 0.1199 |
| R2 388/388 | `probabilistic_recalibrated` | 0.3870 | 0.5607 | 0.0594 | 0.0811 |
| R2 388/388 | `rule_verified_point_subtype` | 0.4177 | 0.5265 | 0.0000 | 0.0000 |
| R2 388/388 | `family_conditional_risk` | 0.4558 | 0.6012 | 0.0254 | 0.0323 |

Interpretation:

- Open3DSG supports the cross-source reliability claim within the measured
  families.
- In the historical 127-scan scope, R2 388/388 should be the representative
  appendix/sensitivity branch, with old 377/388 kept as the comparison row.
- The small R2-minus-old change shows that the old missing 11 contexts did not
  drive the Open3DSG trend.
- The pattern is not identical to VL-SAT, which is useful: the framework is an
  operating-point/evaluation layer rather than a source-specific metric trick.
- The caveats are part of the result and must remain visible.

Why we moved on:

- Metrics alone do not explain why rows fail or whether residual risk remains.
- The next step was failure-analysis rows and qualitative inspection.

## Stage 8: Open3DSG Failure Analysis

Why this stage was run:

- Top-tier novelty needs "why the failure happens," not only metric deltas.
- Failure analysis connects semantic plausibility to physical inconsistency and
  exposes residual calibration risk.

Historical result:

| item | value |
| --- | ---: |
| real failure-analysis rows | 57,736 |
| validation errors | 0 |
| visual-audit queue rows | 6,162 |
| qualitative cases inspected | 36 |
| demoted by geometry-aware re-ranking | 23 |
| rule-violated with `p_geom_valid > 0.9` | 10 |

Interpretation:

- Qualitative rows support the paper's failure mechanism: predicted relations
  can be semantically plausible but physically inconsistent for the object pair.
- The 10 high-confidence rule-violated cases show residual calibration risk.
  This is why the paper reports probabilistic, rule-verified, and
  family-conditional risk operating points separately.

Why we moved on:

- With VL-SAT, controls, GT verifier evaluation, audit sanity, Open3DSG metrics,
  and failure analysis complete, the hypothesis had enough paper-facing
  evidence for a scoped reliability paper.
- The next stage became paper writing, not another heavy baseline by default.

## Stage 10: Full Official Validation Transition

Why this stage was introduced:

- The 127-scan hardened split was valid for scoped evidence, but reviewers
  could attack it as pilot-excluded or less standard than the full official
  `3DSSG_subset` validation split.
- The method design, thresholds, verifier policy, counterfactuals, and
  `p_geom_valid` calibration had already been frozen from train/train-dev
  artifacts, so a full official validation rerun could be used as a stronger
  frozen evaluation rather than a tuning step.

What was run:

- Docker scope contract for 157 scans, 548 contexts, 36,808 directed candidate
  pairs, 957,008 expected VL-SAT prediction rows, 11,254 GT rows, and 3,972
  measured-family GT rows.
- VL-SAT full-validation staging/runtime/raw dump, adapter export,
  ground-truth JSONL export, geometry join, metric eval, GT verifier eval, and
  VL-SAT-only bootstrap CI under
  `experiments/H001_geom_reliability/sources/vlsat/full_validation/`.
- Open3DSG full-validation covered branch under
  `experiments/H001_geom_reliability/sources/open3dsg/full_validation/`, plus
  the recovery branch under
  `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/`.
  The recovery branch diagnoses the 15 missing contexts as Open3DSG's
  fewer-than-4-visible-objects preprocess gate, recovers them with
  `min_visible=2` plus relaxed two-scan view generation, and completes feature
  audit, clean-exit raw dump, adapter, geometry, metrics, bootstrap CI, failure
  rows, deterministic qualitative case inspection, and Table 6/caveat
  regeneration.
- VL-SAT full-validation failure rows and deterministic qualitative case
  inspection under `sources/vlsat/full_validation/{failure_rows,failure_cases}/`,
  so both paper-facing sources now have metric, control, bootstrap, and
  failure-taxonomy artifacts.

Key VL-SAT full-validation result:

| condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 | reading |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `semantic_only` | 0.4194 | 0.6322 | 0.8074 | 0.9272 | 0.9635 | 0.0029 | 0.0082 | 0.0142 | 0.0268 | 0.0476 | full official source ranking |
| `probabilistic_recalibrated` | 0.4154 | 0.6322 | 0.8107 | 0.9305 | 0.9688 | 0.0015 | 0.0071 | 0.0120 | 0.0229 | 0.0404 | recall-first calibrated setting |
| `family_conditional_risk` | 0.4162 | 0.6309 | 0.8087 | 0.9288 | 0.9683 | 0.0011 | 0.0051 | 0.0109 | 0.0206 | 0.0333 | family-conditional calibrated risk setting |
| `rule_verified_point_subtype` | 0.4197 | 0.6317 | 0.8074 | 0.9257 | 0.9627 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | hard-filter diagnostic |

Interpretation:

- The full official validation route preserves the main qualitative pattern:
  calibrated/family-conditional risk reranking reduces violation while maintaining or
  slightly improving recall, and rule filtering reaches zero violation with a
  small recall tradeoff.
- The absolute recall is lower than the 127-scan result because the denominator
  is broader, which is expected and should be reported rather than hidden.
- This is now the selected cross-source full-validation primary route. The
  548-context Open3DSG recovery branch is the primary full-denominator Open3DSG
  result and must disclose its recovery policy; the 533-context covered branch
  preserves the unmodified missing-preprocess behavior and should be reported as
  sensitivity / unmodified-source-route evidence.

Key Open3DSG recovery full-validation result:

| condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 | reading |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `semantic_only` | 0.0368 | 0.1002 | 0.1991 | 0.4096 | 0.5161 | 0.5131 | 0.3255 | 0.2088 | 0.1386 | 0.1242 | recovery full official source ranking |
| `probabilistic_recalibrated` | 0.0826 | 0.1581 | 0.2603 | 0.3975 | 0.5723 | 0.0628 | 0.0699 | 0.0654 | 0.0606 | 0.0811 | recall-first calibrated setting |
| `family_conditional_risk` | 0.0984 | 0.1921 | 0.3291 | 0.4658 | 0.6047 | 0.0420 | 0.0482 | 0.0441 | 0.0286 | 0.0341 | family-conditional calibrated risk setting |
| `rule_verified_point_subtype` | 0.0707 | 0.1314 | 0.2422 | 0.4295 | 0.5368 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | hard-filter diagnostic |

Full-validation uncertainty and verifier checks:

- Open3DSG `family_conditional_risk` vs `semantic_only`: R@100 delta `+8.86 pp`
  with 95% CI `[+6.69,+10.96]`; Violation@100 delta `-9.01 pp` with
  95% CI `[-9.49,-8.53]`.
- VL-SAT `family_conditional_risk` vs `semantic_only`: R@100 delta `+0.48 pp`
  with 95% CI `[+0.11,+0.93]`; Violation@100 delta `-1.43 pp` with
  95% CI `[-1.60,-1.28]`.
- Full-validation GT verifier: 3,972 positives and 3,972 counterfactual
  negatives; positive nonviolated `0.9965`, negative nonsatisfied `0.9673`,
  AUROC/AUPRC `0.9772/0.9729`, Brier `0.0543`.
- VL-SAT full-validation failure analysis produces 59,841 rows with zero
  validation errors; the 36-case qualitative queue has 28 demoted cases, 8
  promoted/retained cases, and 7 violated cases with `p_geom_valid > 0.9`.
- Open3DSG recovery failure analysis produces 82,155 rows with zero validation
  errors; the new 36-case recovery qualitative queue has 25 demoted cases, 11
  promoted/retained cases, and 8 violated cases with `p_geom_valid > 0.9`.
- These qualitative queues are deterministic failure-mechanism evidence, not
  representative human audits.

## Optional Branches And Why They Are Not Main Evidence Yet

### Relation-Family Expansion Attempts

Why they existed:

- Reviewers may ask whether the framework is only hand-fit to
  `support_contact`, `proximity`, and `relative_vertical`.
- We therefore tested plausible expansion families before broadening the claim.

What happened:

- `relative_horizontal` had data scale but did not pass coordinate-frame
  validation. The best scan frame had inverse consistency 1.0 and wrong-frame
  gap 0.1231, but full-family macro strict purity was 0.7725 and
  `front`/`behind` strict purity was 0.7445 with large ambiguity buckets.
- `relative_lateral` split out `left/right` and looked stronger in the held-out
  coordinate audit, but train/dev policy lock remained caveated. Train positive
  strict purity was 0.8738, while dev positive strict purity was only 0.6975.
  Dev diagnosis found 72 strict contradiction rows / 36 physical pairs
  concentrated in two scans, plus 140 uncertain rows / 70 physical pairs; about
  half involved same-label object pairs and most uncertain cases were
  orthogonal-axis dominance.
- `attachment_deferred` reached full-source scoring/metrics/controls/bootstrap,
  but it is not current main-claim evidence. It is promising, especially
  `hanging on`, but Open3DSG covers 768/967 exact-label GT rows, `attached to`
  is noisy, `connected to` has no dev strict rows, and additional failure/visual
  audit is needed before promotion.

Why not main evidence:

- These tracks show disciplined scope control rather than broader validated
  coverage.
- `relative_horizontal` and `relative_lateral` expose coordinate/frame
  ambiguity, not source-prediction reliability.
- `attachment_deferred` is a plausible future upgrade, but it needs explicit
  user confirmation and additional caveat handling before main-claim promotion.

### Qwen-VL

Why it exists:

- Qwen-VL is a third semantic source / modern VLM extension and helps align the
  project with recent VLM/open-vocabulary trends without replacing VL-SAT or
  Open3DSG.

Current status:

- Qwen-VL full official validation downstream is complete as a third-source /
  modern VLM extension: 157 scans, 548 contexts, 110,424 query rows, 46,506
  inferable input rows, 35,131 exported predictions, 32,236 in-scope
  predictions, 3,972 measured-family GT rows, metrics/controls/bootstrap, failure
  rows, and deterministic qualitative cases.

Why not main evidence:

- It was added as an extension after the main VL-SAT/Open3DSG route was already
  framed and should not replace Open3DSG as the current main open-vocabulary
  relation-source case study.
- It can support appendix/extension discussion unless the user explicitly
  promotes it into the main claim.

### FROSS / Functional Benchmarks

Why considered:

- They are relevant for online or functional/robotics scene graph directions.

Why not main evidence:

- FROSS does not cover all H001 target families cleanly.
- SceneFun3D/FunGraph3D would require a separate relation contract, denominator,
  verifier, and claim boundary.

## Current Paper-Ready Interpretation

Allowed:

- H001 is a calibrated geometry-consistency evaluation/re-ranking framework.
- It reduces geometry violations under measurable recall tradeoffs on measured
  `VL-SAT` and Open3DSG measured-family scopes.
- It provides controls, GT-based verifier support, denominator transparency,
  and failure-analysis evidence.

Not allowed:

- Broad open-vocabulary 3DSSG generation improvement.
- Arbitrary-baseline or baseline-agnostic generality.
- Describing the selected official non-averaged Open3DSG recovery branch as an
  exact Open3DSG leaderboard reproduction. It is allowed only as the
  paper-facing full-validation source-output reliability case study with the
  recovery-policy caveat and the 533/548 covered branch retained as sensitivity
  evidence.
- Guaranteed physical correctness.

## Current Paper Stage

The current paper body is in `paper/draft.md` and now runs from Title through
Conclusion. The current target-venue LaTeX source is in `paper/aaai/`, using
the checked AAAI-26 style route until the exact target-year AAAI kit/form is
reconfirmed. Docker PDF build verification is complete with
`h001-aaai-tex:20260526`: latest low-K table rebuild
`logs/h001_aaai_pdf_build_lowk_full_20260623_191806.log` exits 0.
`main.pdf` builds to 9 total pages, technical content occupies pages 1-7,
references are on page 8, the AAAI reproducibility checklist is on page 9,
BibTeX uses 19 entries, and targeted grep found no missing citations, undefined
  refs, overfull hboxes, LaTeX errors, or AAAI package errors. Low-K source
  metrics are now regenerated in `metrics_k_sweep/` for both paper-facing
  sources, with K=50/100 matching locked `metrics/`. The next work is
  submission package hygiene: portal form, artifact URL/DOI, supplementary/code-
  data decision, checklist answer pass, low-K artifact packaging, and final
  package regeneration.
Open3DSG-first table ordering is preserved: the manuscript treats Open3DSG as
the main open-vocabulary case study and VL-SAT as the controlled anchor.
The latest reviewer-defense pass adds explicit main-text answers to the
hand-coded-verifier, simple-geometry/distance, recall-tradeoff, Open3DSG
reproduction-caveat, family-selection, and AAAI-relevance attacks without
moving technical content beyond page 7.
Paper-result
experiments should remain Docker
reproducible, and optional Qwen/FROSS/functional extensions should not change
the main claim unless explicitly promoted after row contract, metric,
denominator, bootstrap, and audit evidence are reviewed.
