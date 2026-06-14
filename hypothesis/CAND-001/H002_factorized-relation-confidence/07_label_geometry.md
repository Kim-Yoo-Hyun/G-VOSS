# H002 Label Geometry

Last updated: 2026-06-12

## Purpose

이 문서는 H002의 다음 decision gate인 label-geometry agreement diagnostic을 기록한다.
`06_equivalence.md`에서 확인한 것처럼, H001과 같은 scope/selection을 쓰면
`RGA-HL@K`는 H001 `Violation@K`로 붕괴한다. 따라서 H002가 독립 branch로 남으려면
label correctness와 geometric satisfiability가 실제로 다른 축이라는 증거가 필요하다.

이번 단계의 질문은 다음이다.

```text
Exact-label-correct 또는 family-correct relation이 geometry상 violated/uncertain인가?
반대로 GT label credit은 없지만 geometry상 satisfied인 relation이 많은가?
```

## Artifacts

Diagnostic script:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/label_geometry.py
```

Outputs:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/label_geometry/vlsat_label_geometry.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/label_geometry/open3dsg_recovery_label_geometry.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/label_geometry/report.md
```

Input source:

- H001 `failure_rows/rows.jsonl` only.
- No row-level H002 projection was created.
- No H001 artifact was modified.

## Boundary

This is not all-row label-geometry agreement. It uses H001 failure rows, which
are already selected for top-K, reranking, or failure-analysis relevance.

Therefore:

- counts are valid as a hypothesis-stage diagnostic;
- they are not dataset-level prevalence estimates;
- all-row label-geometry claims require a direct GT join in a later step.

## Top-100 Diagnostic

| Source | exact+violated | exact+uncertain | family+violated | family+uncertain | no-GT+satisfied | pair-other+satisfied |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `vlsat` | 13 | 532 | 57 | 380 | 20,110 | 7,685 |
| `open3dsg_recovery_relaxed_views_min2` | 5 | 308 | 58 | 216 | 17,427 | 3,904 |

Top-100 rates:

| Source | exact bad-geometry rate | label-positive bad-geometry rate | GT-negative geometry-satisfied rate |
| --- | ---: | ---: | ---: |
| `vlsat` | 0.1424 | 0.1536 | 0.5742 |
| `open3dsg_recovery_relaxed_views_min2` | 0.1527 | 0.1621 | 0.4317 |

Definitions:

- `bad-geometry` = `violated` or `uncertain`.
- `label-positive` = `exact_match` or `family_match`.
- `GT-negative` = `no_gt_for_pair` or `pair_has_other_predicate`.

## Top-50 Diagnostic

| Source | exact+violated | exact+uncertain | family+violated | family+uncertain | no-GT+satisfied | pair-other+satisfied |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `vlsat` | 11 | 507 | 31 | 186 | 10,309 | 4,356 |
| `open3dsg_recovery_relaxed_views_min2` | 4 | 263 | 25 | 110 | 8,761 | 1,885 |

Top-50 rates:

| Source | exact bad-geometry rate | label-positive bad-geometry rate | GT-negative geometry-satisfied rate |
| --- | ---: | ---: | ---: |
| `vlsat` | 0.1406 | 0.1406 | 0.6614 |
| `open3dsg_recovery_relaxed_views_min2` | 0.1641 | 0.1561 | 0.4334 |

## Family Pattern

Top-100 target counts are concentrated as follows.

`VL-SAT`:

- `support_contact`: exact+uncertain 361, exact+violated 11,
  family+uncertain 302, family+violated 23.
- `relative_vertical`: exact+uncertain 171, exact+violated 2,
  family+uncertain 78, family+violated 34.
- `proximity`: large no-GT+satisfied count, but no exact/family bad-geometry
  target in this summary.

Open3DSG recovery:

- `support_contact`: exact+uncertain 267, exact+violated 5,
  family+uncertain 175, family+violated 17.
- `relative_vertical`: exact+uncertain 41, family+uncertain 41,
  family+violated 41.
- `proximity`: large no-GT+satisfied count, but no exact/family bad-geometry
  target in this summary.

## Interpretation

The result is mixed.

Evidence against a strong independent H002 method claim:

- exact-label-correct plus geometry-violated rows are rare in both sources:
  13 for `VL-SAT` top-100 and 5 for Open3DSG top-100.
- The main label-positive disagreement is `uncertain`, not hard violation.
- This does not justify a factor graph method yet. A factor graph would still
  look like H001 recalibration plus uncertainty notation.

Evidence supporting a weaker RGA benchmark/diagnostic branch:

- exact/family-positive rows often have uncertain geometry: label-positive
  bad-geometry rate is about 15-16% in both sources, mostly uncertainty.
- many GT-negative rows are geometry-satisfied: 57.4% for `VL-SAT` top-100 and
  43.2% for Open3DSG top-100 under this failure-row diagnostic.
- This suggests label correctness and geometric satisfiability are not the same
  axis, especially because `no_gt_for_pair+satisfied` is large.

## Verdict

```text
H002 should not proceed to factor graph method yet.
H002 can continue only as an RGA benchmark / diagnostic branch.
```

Reason:

- The hard version of the original question, "semantic/label high but geometry
  actually violated", is not strong enough from this failure-row pass.
- The softer benchmark question, "label metric and geometry satisfiability are
  different axes", has evidence but needs all-row GT join validation.

## Current Claim Boundary

Allowed H002 claim at this stage:

```text
Failure-row diagnostics show that label correctness and geometric
satisfiability can diverge, mainly through geometry uncertainty and
geometry-satisfied no-GT rows. This supports an RGA benchmark audit, not yet a
new rescoring method.
```

Blocked H002 claims:

- H002 factor graph is more principled than H001.
- H002 solves high-semantic but geometry-invalid relations better than H001.
- `RGA-HL@K` is a novel replacement for H001 `Violation@K`.
- Label-correct relations are frequently geometrically violated.

## Next TODO

Next document:

```text
08_all_row_join.md
```

Required next work:

- Implement a direct all-row GT join for H002 projection rows.
- Compute all-row label-geometry buckets, not just failure-row diagnostics.
- Separate exact-label, family-label, no-GT-pair, and pair-other-predicate
  cases.
- Decide whether `no_gt_for_pair+satisfied` reflects annotation sparsity,
  source false positives, or genuine relation ambiguity.
- Only if all-row join confirms nontrivial label-geometry disagreement should
  H002 continue toward an RGA benchmark paper branch.

Stop condition:

- If all-row join shows the failure-row signal is selection-biased or already
  captured by H001 failure taxonomy, fold H002 into H001 appendix/failure
  analysis.
