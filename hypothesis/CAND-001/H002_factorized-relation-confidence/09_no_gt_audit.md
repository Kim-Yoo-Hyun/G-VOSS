# H002 No-GT Audit

Last updated: 2026-06-12

## Purpose

`08_all_row_join.md`에서 H002의 강한 hard-failure claim은 약해졌다. Exact-label
correct relation이 geometry-violated인 경우는 매우 적었다. 대신 남은 가장 큰 신호는
다음 bucket이다.

```text
no_gt_for_pair + geometry_satisfied
pair_has_other_predicate + geometry_satisfied
```

이 문서는 이 bucket이 단순 source false positive인지, annotation sparsity인지,
relation ambiguity인지 구분하기 위한 1차 audit queue를 만든 결과를 기록한다.

## Artifacts

Script:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/no_gt_audit.py
```

Outputs:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/no_gt_audit/vlsat_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/no_gt_audit/vlsat_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/no_gt_audit/open3dsg_recovery_relaxed_views_min2_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/no_gt_audit/open3dsg_recovery_relaxed_views_min2_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/no_gt_audit/report.md
```

No H001 artifact was modified.

## Audit Target

Included rows:

- geometry status = `satisfied`
- match status = `no_gt_for_pair` or `pair_has_other_predicate`
- relation family in `support_contact`, `proximity`, `relative_vertical`

Sampling policy:

```text
top semantic-rank rows per (family, match_status, top_scope) stratum
```

Top scopes:

- `top50`
- `top100_only`
- `outside_top100`

Sample size:

- `VL-SAT`: 144 rows
- Open3DSG recovery: 144 rows
- Total: 288 rows

Machine hints are triage labels only. They are not final visual-audit labels.

## Target Counts

| Source | Target total | no-GT pair | pair-other predicate |
| --- | ---: | ---: | ---: |
| `vlsat` | 82,698 | 66,342 | 16,356 |
| `open3dsg_recovery_relaxed_views_min2` | 62,712 | 49,775 | 12,937 |

Interpretation:

- The no-GT geometry-satisfied signal is large in both sources.
- It is not source-specific.
- It appears across all three H002/H001-covered relation families.

## Family Pattern

| Source | Family | no-GT pair | pair-other predicate |
| --- | --- | ---: | ---: |
| `vlsat` | `proximity` | 25,404 | 5,642 |
| `vlsat` | `relative_vertical` | 22,268 | 3,342 |
| `vlsat` | `support_contact` | 18,670 | 7,372 |
| `open3dsg_recovery_relaxed_views_min2` | `proximity` | 18,688 | 4,382 |
| `open3dsg_recovery_relaxed_views_min2` | `relative_vertical` | 15,759 | 2,619 |
| `open3dsg_recovery_relaxed_views_min2` | `support_contact` | 15,328 | 5,936 |

Preliminary reading:

- `proximity` is expected to produce many no-GT rows because proximity relations
  can be dense and under-annotated.
- `relative_vertical` may reflect annotation sparsity or spatial relation
  ambiguity.
- `support_contact` is more interesting because geometry-satisfied support
  without GT can indicate unlabeled valid support, source false positive, or
  object-pair mismatch.

## Top-Scope Pattern

| Source | Scope | no-GT pair | pair-other predicate |
| --- | --- | ---: | ---: |
| `vlsat` | top50 | 2,732 | 1,457 |
| `vlsat` | top100 only | 3,730 | 1,493 |
| `vlsat` | outside top100 | 59,880 | 13,406 |
| `open3dsg_recovery_relaxed_views_min2` | top50 | 3,099 | 577 |
| `open3dsg_recovery_relaxed_views_min2` | top100 only | 3,389 | 731 |
| `open3dsg_recovery_relaxed_views_min2` | outside top100 | 43,287 | 11,629 |

Interpretation:

- Most no-GT satisfied rows are outside top-100.
- The paper-relevant subset is still nontrivial: top50 + top100-only has
  thousands of rows in both sources.
- H002 should not claim all target rows are important; it should focus on
  high-rank no-GT satisfied rows and relation-family patterns.

## Machine Hint Triage

| Source | Hint | Count |
| --- | --- | ---: |
| `vlsat` | annotation_sparsity_or_dense_proximity_relation | 25,404 |
| `vlsat` | annotation_sparsity_or_spatial_relation_ambiguity | 22,268 |
| `vlsat` | plausible_unlabeled_support_candidate | 18,670 |
| `vlsat` | alternative_relation_on_same_pair | 10,714 |
| `vlsat` | label_granularity_or_relation_set_mismatch | 5,642 |
| Open3DSG recovery | annotation_sparsity_or_dense_proximity_relation | 18,688 |
| Open3DSG recovery | annotation_sparsity_or_spatial_relation_ambiguity | 15,759 |
| Open3DSG recovery | plausible_unlabeled_support_candidate | 15,328 |
| Open3DSG recovery | alternative_relation_on_same_pair | 8,555 |
| Open3DSG recovery | label_granularity_or_relation_set_mismatch | 4,382 |

Boundary:

- These hints are rule-based triage categories.
- They must not be treated as final evidence.
- Visual or point-evidence audit is required before paper-level claims.

## Current Interpretation

This gate changes H002's shape.

Weak direction:

```text
Semantic score is high but geometry is violated.
```

This is not sufficiently strong as the main H002 claim because exact-label
geometry violations are rare.

Stronger remaining direction:

```text
Relation labels, semantic rank, and geometric satisfiability define different
reliability states. In particular, many geometry-satisfied relation candidates
have no exact GT relation, suggesting annotation incompleteness, relation
ambiguity, or source false positives that current metrics conflate.
```

This is an RGA benchmark / annotation audit problem, not a factor graph method
problem yet.

## Verdict

```text
H002 continues as an independent benchmark/problem branch, not as a rescoring
method branch.
```

Allowed current claim:

```text
Semantic-geometric relation reliability requires auditing not only violated
high-score relations, but also geometry-satisfied no-GT relation candidates.
These cases are common across sources and relation families and may expose
annotation incompleteness or metric blind spots.
```

Blocked claims:

- H002 factor graph is needed.
- H002 improves relation prediction.
- no-GT+satisfied rows are definitely valid unlabeled relations.
- no-GT+satisfied rows are definitely annotation errors.

## Next TODO

Next document:

```text
10_visual_annotation_audit.md
```

Required next work:

- Audit the 288 sampled rows in `artifacts/no_gt_audit/*_queue.jsonl`.
- Assign final labels:
  - `plausible_unlabeled_relation`
  - `annotation_sparsity_likely`
  - `source_false_positive`
  - `object_pair_mismatch`
  - `label_granularity_mismatch`
  - `geometry_artifact`
  - `uncertain_needs_visual`
- Prioritize top50 and top100-only rows.
- Report per-source and per-family proportions.

Continue condition:

- H002 continues if a meaningful share of high-rank no-GT+satisfied rows are
  plausible unlabeled valid relations or annotation-sparsity cases in both
  sources.

Stop condition:

- If most audited high-rank rows are source false positives, object-pair
  mismatches, or geometry artifacts, H002 should be folded into relation failure
  analysis rather than kept as an independent branch.
