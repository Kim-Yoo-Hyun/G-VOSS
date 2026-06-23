# VL-SAT Full Official Validation

Status: `vlsat_full_validation_metric_and_failure_analysis_ready`

Last updated: `2026-06-23 KST`

This directory owns the Docker-generated VL-SAT rerun on the full official
`3DSSG_subset` validation scope. It is separate from the older 127-scan
hardened VL-SAT artifact.

## Scope

- validation scans: `157`
- contexts: `548`
- directed candidate pairs: `36,808`
- prediction rows: `957,008`
- GT rows: `11,254`
- H001-family GT rows: `3,972`

## Completed Gates

- stage: `stage/`
- runtime record: `runtime_record/`
- raw preflight: `raw_preflight/`
- raw dump: `raw/`, status `raw_dump_ready`
- adapter export: `adapter/`, status `ready`
- geometry join: `geometry/`, status `ready`
- metric eval: `metrics/`, status `ready`
- low-K metric sweep: `metrics_k_sweep/`, status `ready`, K=`{5,10,20,50,100}`
- GT verifier eval: `gt_eval/`, status `ready`
- bootstrap CI: `bootstrap_ci/`, status `ready`
- failure-analysis rows: `failure_rows/`, status `failure_analysis_real_ready`
- deterministic qualitative queue/inspection: `failure_cases/`, status
  `qualitative_case_inspection_ready`

## Key Metrics

Low-K sweep artifact: `metrics_k_sweep/metrics.json`. K=50/100 values match
the locked `metrics/metrics.json` exactly.

| condition | R@5 | R@10 | R@20 | R@50 | R@100 | V@5 | V@10 | V@20 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| semantic_only | 0.4194 | 0.6322 | 0.8074 | 0.9272 | 0.9635 | 0.0029 | 0.0082 | 0.0142 | 0.0268 | 0.0476 |
| probabilistic_recalibrated | 0.4154 | 0.6322 | 0.8107 | 0.9305 | 0.9688 | 0.0015 | 0.0071 | 0.0120 | 0.0229 | 0.0404 |
| rule_verified_point_subtype | 0.4197 | 0.6317 | 0.8074 | 0.9257 | 0.9627 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| control_family_specific_p_geom_valid | 0.4162 | 0.6309 | 0.8087 | 0.9288 | 0.9683 | 0.0011 | 0.0051 | 0.0109 | 0.0206 | 0.0333 |

GT verifier full-validation check:

- GT positives / counterfactual negatives: `3,972 / 3,972`
- positive nonviolated rate: `0.9965`
- negative nonsatisfied rate: `0.9673`
- `p_geom_valid` AUROC/AUPRC: `0.9772 / 0.9729`

Bootstrap CI summary:

```text
bootstrap_ci/summary.md
```

Failure-analysis summary:

- rows: `59,841`
- validation errors: `0`
- visual-audit queue rows: `2,897`
- primary categories:
  `semantic_false_positive` 30,624,
  `insufficient_geometry_evidence` 19,702,
  `true_positive_supported` 3,814,
  `predicate_family_ambiguity` 2,781,
  `semantic_and_geometry_failure` 2,381,
  `geometry_contradiction` 516,
  `rank_only_failure` 23
- selected qualitative cases: `36`
- selected case families: `support_contact` 10, `proximity` 6,
  `relative_vertical` 20
- inspection summary: 28 demoted by geometry-aware reranking, 8
  promoted/retained, and 7 violated cases with `p_geom_valid > 0.9`

Key files:

```text
failure_rows/rows.jsonl
failure_rows/summary.json
failure_rows/manifest.json
failure_cases/queue.jsonl
failure_cases/manifest.json
failure_cases/inspection.json
failure_cases/inspection.md
```

## Claim Boundary

This is valid VL-SAT full-validation metric and failure-taxonomy evidence for
the current H001 families. It is now the controlled-anchor source in the
paper-facing full-validation route. The qualitative queue is deterministic
failure-mechanism evidence, not a representative human audit.
