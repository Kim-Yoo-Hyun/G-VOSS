# H002 Manual Labels

Last updated: 2026-06-12

## Purpose

`10_visual_annotation_audit.md`의 다음 TODO는 high-rank no-GT
geometry-satisfied row에 `final_label`을 채우는 것이다. 이번 단계에서는 원본
`review_queue.jsonl`을 수정하지 않고, 별도 round-1 working label set을 만들었다.

Boundary:

```text
round1 final_label != paper-locked human annotation
```

Round-1 label은 H002 workflow를 이어가기 위한 working label이다. Metadata, same-pair
GT predicate status, geometry verifier output, contact sheet/mesh asset link를 사용해
`final_label` field를 채웠지만, 모든 row는 `paper_locked=false`와
`requires_human_confirmation=true`를 가진다.

## Artifacts

Script:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/manual_labels.py
```

Outputs:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/manual_labels/round1_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/manual_labels/needs_second_review.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/manual_labels/manual_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/manual_labels/round1_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/manual_labels/report.md
```

No H001 artifact was modified.

## Scope

Included:

- `P0_top50`: 96 rows
- `P1_top100_only`: 96 rows

Excluded for now:

- `P2_outside_top100`: 96 rows

Total labeled in round 1:

```text
192 high-rank rows
```

All 192 rows have contact sheets.

## Labeling Rule

The original `review_queue.jsonl` remains unchanged. The round-1 script writes a
new `round1_labels.jsonl` file.

Operational rule:

- `pair_has_other_predicate` -> `label_granularity_mismatch`
- no-GT `proximity` or `relative_vertical` with satisfied geometry ->
  `annotation_sparsity_likely`
- no-GT `support_contact` with satisfied support/contact witness ->
  `plausible_unlabeled_relation`
- generic or weak object identity evidence -> `uncertain_needs_visual`
- semantically suspicious structural support/contact pair ->
  `source_false_positive`

This is intentionally conservative. It separates likely annotation/metric issues
from uncertain cases without claiming that every no-GT geometry-satisfied edge is
a true missing positive.

## Round-1 Result

Final label distribution:

| Final label | Rows |
| --- | ---: |
| `label_granularity_mismatch` | 96 |
| `annotation_sparsity_likely` | 61 |
| `plausible_unlabeled_relation` | 30 |
| `uncertain_needs_visual` | 4 |
| `source_false_positive` | 1 |

Review status:

| Review status | Rows |
| --- | ---: |
| `ready_for_human_confirmation` | 187 |
| `needs_second_review` | 5 |

Source split:

| Source / label | Rows |
| --- | ---: |
| `open3dsg_recovery_relaxed_views_min2 / label_granularity_mismatch` | 48 |
| `vlsat / label_granularity_mismatch` | 48 |
| `vlsat / annotation_sparsity_likely` | 32 |
| `open3dsg_recovery_relaxed_views_min2 / annotation_sparsity_likely` | 29 |
| `open3dsg_recovery_relaxed_views_min2 / plausible_unlabeled_relation` | 15 |
| `vlsat / plausible_unlabeled_relation` | 15 |
| `open3dsg_recovery_relaxed_views_min2 / uncertain_needs_visual` | 4 |
| `vlsat / source_false_positive` | 1 |

Family split:

| Family / label | Rows |
| --- | ---: |
| `proximity / label_granularity_mismatch` | 32 |
| `relative_vertical / annotation_sparsity_likely` | 32 |
| `relative_vertical / label_granularity_mismatch` | 32 |
| `support_contact / label_granularity_mismatch` | 32 |
| `support_contact / plausible_unlabeled_relation` | 30 |
| `proximity / annotation_sparsity_likely` | 29 |
| `proximity / uncertain_needs_visual` | 3 |
| `support_contact / source_false_positive` | 1 |
| `support_contact / uncertain_needs_visual` | 1 |

## Interpretation

The round-1 result supports keeping H002 alive as an independent diagnostic
benchmark branch, but not yet as a method branch.

Main signal:

```text
label_granularity_mismatch + annotation_sparsity_likely + plausible_unlabeled_relation
= 187 / 192 high-rank rows
```

This suggests that high-rank no-GT geometry-satisfied relation candidates are
not mainly obvious geometry artifacts or source false positives. The stronger
interpretation is that label-only evaluation conflates at least three cases:

- same object pair has another relation label,
- relation is geometrically plausible but sparsely annotated,
- support/contact relation may be a plausible unlabeled missing relation.

The strongest H002 paper direction is therefore still:

```text
relation-level reliability requires separating semantic score, GT label match,
geometry satisfiability, and annotation coverage.
```

## Claim Boundary

Allowed current claim:

```text
On the high-rank audit queue, round-1 labels indicate that no-GT
geometry-satisfied relation candidates mostly fall into label granularity,
annotation sparsity, or plausible unlabeled relation buckets rather than obvious
source-error buckets.
```

Blocked claims:

- These 192 labels are paper-locked human annotations.
- H002 has proven dataset annotation errors.
- H002 improves prediction or rescoring.
- All no-GT geometry-satisfied rows are valid missing positives.

## Next TODO

Next document:

```text
12_second_review.md
```

Required next work:

- Inspect the 5 rows in `artifacts/manual_labels/needs_second_review.jsonl`.
- Use the contact sheet first; if still ambiguous, inspect the linked
  `mesh.refined.v2.obj` or aligned instance `.ply`.
- Confirm or revise `uncertain_needs_visual` and `source_false_positive`.
- Then sample-check at least 20 rows from `ready_for_human_confirmation`, with
  emphasis on `support_contact / plausible_unlabeled_relation`.

Continue condition:

- H002 continues if second review does not collapse the
  `plausible_unlabeled_relation` and `annotation_sparsity_likely` buckets into
  source false positives.

