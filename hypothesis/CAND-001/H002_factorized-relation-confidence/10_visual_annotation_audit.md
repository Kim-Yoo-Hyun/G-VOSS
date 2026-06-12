# H002 Visual Annotation Audit

Last updated: 2026-06-12

## Purpose

`09_no_gt_audit.md`의 다음 TODO는 no-GT geometry-satisfied row가 실제로
annotation sparsity인지, label granularity mismatch인지, source false positive인지
구분하는 것이다. 이번 단계에서는 288개 audit row를 final visual labeling에 바로 쓸
수 있도록 local visual/mesh evidence와 연결하고, conservative pre-visual triage를
수행했다.

중요한 boundary:

```text
previsual_label != final_label
```

`previsual_label`은 metadata, GT match status, relation family, geometry verifier
reason code, local visual asset availability를 기반으로 한 triage label이다. 실제 논문
claim에는 수동 image/point/mesh review로 채운 `final_label`만 사용할 수 있다.

## Artifacts

Script:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/annotation_audit.py
```

Outputs:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/visual_annotation_audit/review_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/visual_annotation_audit/previsual_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/visual_annotation_audit/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/visual_annotation_audit/contact_sheets/
```

No H001 artifact was modified.

## Input Scope

Input queues:

- `artifacts/no_gt_audit/vlsat_queue.jsonl`: 144 rows
- `artifacts/no_gt_audit/open3dsg_recovery_relaxed_views_min2_queue.jsonl`: 144 rows

Total:

```text
288 rows
```

Priority split:

| Priority | Rows | Meaning |
| --- | ---: | --- |
| `P0_top50` | 96 | paper-relevant high semantic rank |
| `P1_top100_only` | 96 | secondary high-rank evidence |
| `P2_outside_top100` | 96 | background/control review |

Visual asset availability:

| Asset state | Rows |
| --- | ---: |
| `subject_and_object_images` | 288 |

All sampled rows have local 3RScan subject/object multi-view crops. The review
queue also records scan-level `mesh.refined.v2.obj`, aligned instance `.ply`,
and `semseg.v2.json` paths when available.

Contact sheets:

```text
192 high-rank sheets = P0_top50 + P1_top100_only
```

One sheet was visually checked for nonblank rendering and readable row metadata.

## Previsual Triage Result

| Previsual label | Rows |
| --- | ---: |
| `label_granularity_mismatch` | 123 |
| `annotation_sparsity_likely` | 89 |
| `plausible_unlabeled_relation` | 44 |
| `uncertain_needs_visual` | 21 |
| `source_false_positive` | 11 |

Source-level split:

| Source / label | Rows |
| --- | ---: |
| `open3dsg_recovery_relaxed_views_min2 / label_granularity_mismatch` | 66 |
| `vlsat / label_granularity_mismatch` | 57 |
| `vlsat / annotation_sparsity_likely` | 46 |
| `open3dsg_recovery_relaxed_views_min2 / annotation_sparsity_likely` | 43 |
| `open3dsg_recovery_relaxed_views_min2 / plausible_unlabeled_relation` | 22 |
| `vlsat / plausible_unlabeled_relation` | 22 |
| `open3dsg_recovery_relaxed_views_min2 / uncertain_needs_visual` | 11 |
| `vlsat / uncertain_needs_visual` | 10 |
| `vlsat / source_false_positive` | 9 |
| `open3dsg_recovery_relaxed_views_min2 / source_false_positive` | 2 |

Family-level split:

| Family / label | Rows |
| --- | ---: |
| `relative_vertical / annotation_sparsity_likely` | 46 |
| `proximity / label_granularity_mismatch` | 44 |
| `support_contact / plausible_unlabeled_relation` | 44 |
| `proximity / annotation_sparsity_likely` | 43 |
| `relative_vertical / label_granularity_mismatch` | 42 |
| `support_contact / label_granularity_mismatch` | 37 |
| `support_contact / source_false_positive` | 11 |
| `proximity / uncertain_needs_visual` | 9 |
| `relative_vertical / uncertain_needs_visual` | 8 |
| `support_contact / uncertain_needs_visual` | 4 |

## Interpretation

Previsual evidence supports continuing H002 as a benchmark/problem branch.

Reason:

- The largest bucket is not immediate geometry artifact or obvious source false
  positive. It is `label_granularity_mismatch`, where the same object pair has
  another GT predicate but the predicted predicate may still be geometrically
  satisfied or derivable.
- `annotation_sparsity_likely` is large in both sources, especially proximity
  and relative vertical relations. This matches the hypothesis that label-only
  metrics collapse missing annotation, metric mismatch, and false positive into
  one error bucket.
- `support_contact / plausible_unlabeled_relation` appears symmetrically in
  both sources: 22 rows each. This is the most interesting manual audit target
  because support/contact has stronger physical semantics than `close by`.

However, this does not yet prove that H002 has a paper-level positive finding.
Object crops verify instance identity better than relation geometry. Final
labels still require image or point/mesh review, especially for support/contact
and structural pairs such as wall/floor/ceiling.

## Current Verdict

Allowed current claim:

```text
H002 has a concrete audit target: high-rank no-GT geometry-satisfied relation
candidates can be separated into annotation sparsity, label granularity mismatch,
plausible unlabeled support/contact, uncertain cases, and likely source errors.
The prepared audit bundle makes this distinction testable at row level.
```

Blocked claims:

- no-GT geometry-satisfied rows are definitely valid unlabeled relations.
- H002 proves annotation incompleteness.
- H002 factor graph rescoring is needed.
- H002 improves relation prediction.

## Next TODO

Next document:

```text
11_manual_labels.md
```

Required next work:

- Fill `final_label` for at least the 192 high-rank rows in
  `artifacts/visual_annotation_audit/review_queue.jsonl`.
- Use contact sheets first, then inspect mesh/point evidence for rows where
  object crops do not prove the relation.
- Report final-label proportions by source, family, and priority.
- Continue H002 only if a meaningful share of P0/P1 rows are
  `plausible_unlabeled_relation`, `annotation_sparsity_likely`, or
  `label_granularity_mismatch` after manual review.

