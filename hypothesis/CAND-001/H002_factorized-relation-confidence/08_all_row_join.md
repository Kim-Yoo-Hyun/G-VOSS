# H002 All Row Join

Last updated: 2026-06-12

## Purpose

`07_label_geometry.md`는 H001 failure rows에서 label-geometry disagreement를
확인했다. 하지만 failure rows는 top-K/reranking/failure-analysis 중심으로 선택된
row라서 selection bias가 있다. 이 문서는 전체 prediction row에 direct GT join을
수행해 H002의 label-geometry 신호가 실제로 유지되는지 확인한다.

핵심 질문:

```text
Failure-row에서 보인 label-geometry disagreement가 전체 prediction universe에서도
충분히 강한가?
```

## Artifacts

Script:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/all_row_join.py
```

Outputs:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/all_row_join/vlsat_all_row_join.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/all_row_join/open3dsg_recovery_all_row_join.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/all_row_join/report.md
```

Inputs:

- GT: `experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl`
- `VL-SAT`: 957,008 prediction rows and 957,008 geometry rows.
- Open3DSG recovery: 695,916 prediction rows and 695,916 geometry rows.

No row-level H002 join file was created. The outputs are compact summaries only.
No H001 artifact was modified.

## Join Rule

The direct GT join follows the H001 failure-analysis logic.

Exact key:

```text
(scan_id, subset_split_id, subject_id, object_id, predicate_label)
```

Pair key:

```text
(scan_id, subset_split_id, subject_id, object_id)
```

Status mapping:

- `exact_match`: exact key exists in GT.
- `family_match`: pair exists and at least one GT relation has the same
  predicate family.
- `pair_has_other_predicate`: pair exists but not in the same family.
- `no_gt_for_pair`: pair does not exist in GT.

Geometry status is copied from H001 `verification_status`.

## All-Row Result

| Source | Rows | exact+violated | exact+uncertain | family+violated | family+uncertain | no-GT+satisfied | pair-other+satisfied |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `vlsat` | 957,008 | 14 | 544 | 251 | 734 | 66,342 | 16,356 |
| `open3dsg_recovery_relaxed_views_min2` | 695,916 | 11 | 395 | 154 | 549 | 49,775 | 12,937 |

All-row rates:

| Source | exact bad-geometry rate | label-positive bad-geometry rate | GT-negative geometry-satisfied rate | geometry-supported share |
| --- | ---: | ---: | ---: | ---: |
| `vlsat` | 0.0496 | 0.0444 | 0.0897 | 0.2308 |
| `open3dsg_recovery_relaxed_views_min2` | 0.0470 | 0.0422 | 0.0936 | 0.2308 |

Interpretation:

- exact-label + hard geometry violation is extremely rare.
- exact/family-positive bad geometry exists mostly as `uncertain`, not
  `violated`.
- All-row GT-negative geometry-satisfied rate is much lower than the
  failure-row diagnostic suggested.

## Global Top-100 Result

| Source | Rows | exact+violated | exact+uncertain | family+violated | family+uncertain | no-GT+satisfied | pair-other+satisfied |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `vlsat` | 54,800 | 10 | 464 | 17 | 113 | 6,462 | 2,950 |
| `open3dsg_recovery_relaxed_views_min2` | 54,704 | 4 | 213 | 20 | 78 | 6,488 | 1,308 |

Top-100 rates:

| Source | exact bad-geometry rate | label-positive bad-geometry rate | GT-negative geometry-satisfied rate | geometry-supported share |
| --- | ---: | ---: | ---: | ---: |
| `vlsat` | 0.0464 | 0.0412 | 0.2344 | 0.3265 |
| `open3dsg_recovery_relaxed_views_min2` | 0.1060 | 0.0678 | 0.1557 | 0.3633 |

## H001-Family Global Top-100

This is the top-100 subset restricted to H001-supported families under the
global source rank, not H001's scoped-score top-K selection.

| Source | Rows | exact+violated | exact+uncertain | family+violated | family+uncertain | no-GT+satisfied | pair-other+satisfied |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `vlsat` | 17,890 | 10 | 464 | 17 | 113 | 6,462 | 2,950 |
| `open3dsg_recovery_relaxed_views_min2` | 19,874 | 4 | 213 | 20 | 78 | 6,488 | 1,308 |

Rates:

| Source | exact bad-geometry rate | label-positive bad-geometry rate | GT-negative geometry-satisfied rate |
| --- | ---: | ---: | ---: |
| `vlsat` | 0.1339 | 0.1306 | 0.7095 |
| `open3dsg_recovery_relaxed_views_min2` | 0.1598 | 0.1514 | 0.4381 |

Interpretation:

- Once unsupported families are removed, the remaining covered top-100 rows
  expose a strong GT-negative geometry-satisfied signal.
- This is not automatically a model error. It may indicate sparse relation
  annotation, alternative valid relations, or source false positives.
- This is the most plausible remaining H002 benchmark direction.

## Comparison To Failure-Row Diagnostic

The failure-row diagnostic overstated the all-row strength of the signal.

Examples:

- `VL-SAT` failure-row top100 exact bad-geometry rate was 0.1424; all-row
  global top100 is 0.0464.
- Open3DSG failure-row top100 exact bad-geometry rate was 0.1527; all-row
  global top100 is 0.1060.
- All-row exact+violated remains tiny: 14 for `VL-SAT`, 11 for Open3DSG.

This means H002 cannot claim that label-correct relations are frequently
geometrically violated.

## Verdict

```text
H002 should not become a factor-graph rescoring method branch now.
H002 can continue only as an RGA benchmark branch focused on annotation/metric
disagreement and geometry-supported no-GT relations.
```

Why:

- The hard high-semantic/high-label but geometry-violated failure is too rare.
- The remaining nontrivial signal is GT-negative but geometry-satisfied rows.
- That signal needs visual/annotation audit before it can support a paper-level
  benchmark claim.

## Current Claim Boundary

Allowed:

```text
All-row direct joins show that exact-label correctness and geometric
satisfiability are not identical, but hard label-correct geometry violations are
rare. The strongest remaining RGA signal is geometry-satisfied predictions with
no exact GT relation, which may reveal annotation sparsity or relation ambiguity.
```

Blocked:

- H002 factor graph is necessary.
- H002 has stronger method novelty than H001.
- Exact-label-correct relations are often geometrically violated.
- `RGA-HL@K` is a better replacement for H001 `Violation@K`.

## Next TODO

Next document:

```text
09_no_gt_audit.md
```

Required next work:

- Sample geometry-satisfied `no_gt_for_pair` and `pair_has_other_predicate`
  rows from both sources.
- Separate likely annotation sparsity, source false positive, label granularity
  mismatch, object-pair mismatch, and genuinely valid unlabeled relation.
- Check whether the same pattern appears across `support_contact`, `proximity`,
  and `relative_vertical`.
- Decide whether H002's remaining contribution is a benchmark for
  relation-annotation incompleteness / semantic-geometric agreement, or whether
  it should be folded into H001 failure analysis.

Stop condition:

- If most no-GT+satisfied rows are obvious false positives or artifacts, stop
  H002 as an independent branch.

Continue condition:

- If many no-GT+satisfied rows are plausible unlabeled valid relations, H002 can
  continue as an RGA benchmark branch. Factor graph design still remains
  deferred until the benchmark claim is stable.
