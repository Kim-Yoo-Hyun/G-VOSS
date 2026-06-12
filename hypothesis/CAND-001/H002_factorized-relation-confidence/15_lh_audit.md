# H002 RGA-LH Audit

Last updated: 2026-06-12

## Scope Correction

This audit bundle was prepared from H001 `full_validation` artifacts through
`14_lh_diagnostic.md`.

Therefore the rows, contact sheets, and previsual labels in this document are
held-out diagnostic artifacts only. They are useful for checking that the audit
workflow is feasible, but they must not be used for hypothesis selection,
model-design decisions, threshold choice, or training-stage claim formation.

The next H002 step must rebuild the RGA diagnostic on train-set artifacts.

## Purpose

`14_lh_diagnostic.md`의 다음 TODO는 `RGA-LH`, 즉 low-semantic +
high-geometry row에 visual asset/contact sheet를 붙이고 audit 가능한 queue로
분리하는 것이다.

이번 단계는 final human annotation이 아니라 audit preparation이다.

```text
previsual_label != paper-final human label
```

특히 `RGA-LH`는 자동 graph promotion signal이 아니다. Exact-match LH는 semantic
underconfidence를 보는 가장 깨끗한 신호이고, no-GT LH는 annotation sparsity,
ontology/label granularity, geometry-trivial relation, object-pair mismatch를 따로
검토해야 한다.

## Artifacts

Script:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/lh_audit.py
```

Outputs:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/lh_audit/review_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/lh_audit/exact_first_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/lh_audit/no_gt_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/lh_audit/manual_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/lh_audit/previsual_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/lh_audit/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/lh_audit/contact_sheets/
```

No H001 artifact was modified. H001 artifacts were used as read-only source
evidence.

## Input Scope

Input queues:

- `artifacts/lh_diagnostic/vlsat_queue.jsonl`: 116 rows
- `artifacts/lh_diagnostic/open3dsg_recovery_relaxed_views_min2_queue.jsonl`: 120 rows

Total:

```text
236 rows
```

Visual asset availability:

| Asset state | Rows |
| --- | ---: |
| `subject_and_object_images` | 236 |

Contact sheets:

```text
236 sheets
```

All LH queue rows have subject/object multi-view crops and generated contact
sheets. Each row also records scan-level mesh, instance `.ply`, and `semseg`
paths when available.

## Priority Split

The LH audit is ordered by label evidence, not by source.

| Priority | Rows | Meaning |
| --- | ---: | --- |
| `P0_exact_match` | 66 | exact GT predicate exists, but semantic rank is outside top 100 |
| `P1_family_match` | 26 | same relation family exists in GT |
| `P2_pair_other` | 72 | same object pair has another GT predicate |
| `P3_no_gt` | 72 | no GT predicate for the directed object pair |

This ordering matters. `P0_exact_match` directly tests semantic underconfidence
because the relation is both GT-supported and geometry-satisfied, yet the source
ranked it low. `P3_no_gt` is not the same claim; it is an annotation/ontology
audit target.

## Previsual Triage

Previsual label distribution:

| Previsual label | Rows |
| --- | ---: |
| `label_granularity_mismatch` | 64 |
| `semantic_underconfidence_exact_gt` | 63 |
| `semantic_underconfidence_family_or_granularity` | 26 |
| `geometry_trivial_or_dense_relation` | 22 |
| `plausible_unlabeled_relation` | 22 |
| `annotation_sparsity_likely` | 19 |
| `uncertain_needs_visual_or_mesh` | 19 |
| `source_false_positive` | 1 |

Priority-label split:

| Priority / label | Rows |
| --- | ---: |
| `P0_exact_match / semantic_underconfidence_exact_gt` | 63 |
| `P0_exact_match / uncertain_needs_visual_or_mesh` | 3 |
| `P1_family_match / semantic_underconfidence_family_or_granularity` | 26 |
| `P2_pair_other / label_granularity_mismatch` | 64 |
| `P2_pair_other / uncertain_needs_visual_or_mesh` | 8 |
| `P3_no_gt / geometry_trivial_or_dense_relation` | 22 |
| `P3_no_gt / plausible_unlabeled_relation` | 22 |
| `P3_no_gt / annotation_sparsity_likely` | 19 |
| `P3_no_gt / uncertain_needs_visual_or_mesh` | 8 |
| `P3_no_gt / source_false_positive` | 1 |

Family-label split:

| Family / label | Rows |
| --- | ---: |
| `proximity / semantic_underconfidence_exact_gt` | 24 |
| `proximity / label_granularity_mismatch` | 22 |
| `proximity / geometry_trivial_or_dense_relation` | 22 |
| `proximity / uncertain_needs_visual_or_mesh` | 4 |
| `relative_vertical / label_granularity_mismatch` | 22 |
| `relative_vertical / semantic_underconfidence_exact_gt` | 19 |
| `relative_vertical / annotation_sparsity_likely` | 19 |
| `relative_vertical / uncertain_needs_visual_or_mesh` | 7 |
| `relative_vertical / semantic_underconfidence_family_or_granularity` | 2 |
| `support_contact / semantic_underconfidence_family_or_granularity` | 24 |
| `support_contact / plausible_unlabeled_relation` | 22 |
| `support_contact / label_granularity_mismatch` | 20 |
| `support_contact / semantic_underconfidence_exact_gt` | 20 |
| `support_contact / uncertain_needs_visual_or_mesh` | 8 |
| `support_contact / source_false_positive` | 1 |

## Baseline Clarification

`p_geom_valid` is the geometry-only calibrated validity proxy.

It is not the same as full edge reliability. It is computed from geometry
evidence/residuals and should be used in H002 as:

- a geometry-only baseline score,
- a geometry factor inside the factorized reliability posterior,
- a continuous disagreement axis against semantic score.

The frozen deterministic status, such as `satisfied`, `violated`, `uncertain`,
or `unsupported`, is not the final continuous score. It is the bucket anchor used
to define RGA states and audit denominators.

Minimum executable baseline set:

| Baseline | Score | Role |
| --- | --- | --- |
| semantic-only | source relation score/rank | original relation confidence |
| geometry-only | `p_geom_valid` | calibrated geometry validity factor |
| semantic + geometry | product or 2-factor calibrated score | simple H001-style fusion baseline |
| factorized reliability posterior | semantic, object, geometry, uncertainty, provenance factors | H002 proposed model |

Thus the core comparison has 4 baselines/conditions. For reviewer defense or a
paper experiment, add diagnostic ablations:

- hard-rule/status-only filter,
- no-uncertainty posterior,
- no-object-confidence posterior,
- pooled vs family-specific geometry calibration.

## Interpretation

The strongest LH signal is `P0_exact_match`.

```text
P0_exact_match = exact GT relation + geometry_satisfied + semantic_rank > 100
```

This is more direct than no-GT LH because it does not depend on claiming missing
annotation. The current bundle contains 66 exact-match LH rows, 63 of which
receive the clean previsual label `semantic_underconfidence_exact_gt`.

The second signal is `P1_family_match` and `P2_pair_other`.
These rows suggest that low semantic score may hide compatible relation-family or
label-granularity cases.

The riskiest signal is `P3_no_gt`.
It contains useful candidates, but also dense/trivial proximity and support
endpoint risk. Therefore no-GT LH must be audited separately and cannot be used
as automatic evidence of missing positives.

## Allowed Current Claim

```text
H002 has a concrete RGA-LH audit bundle. The cleanest initial evidence is
exact-match LH: some GT-supported and geometry-satisfied relations are ranked
outside semantic top-100. This supports modeling relation reliability as a
factorized semantic-geometry problem, while no-GT LH remains an annotation and
ontology audit target.
```

## Blocked Claims

- `RGA-LH` rows are valid missing positives.
- no-GT geometry-satisfied rows should be promoted into the scene graph.
- `p_geom_valid` alone is full relation reliability.
- contact-sheet-only previsual labels are paper-final human labels.

## Next TODO

Next document:

```text
16_train_scope.md
```

Required next work:

- Do not manually review the current validation-derived LH queue for hypothesis
  selection.
- Audit the available train-side artifacts.
- Choose the first train-set source route.
- Rebuild `RGA-HL/RGA-LH` diagnostics on train artifacts before manual LH review
  or baseline-contract decisions.
