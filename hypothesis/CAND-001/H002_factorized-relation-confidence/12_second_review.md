# H002 Second Review

Last updated: 2026-06-12

## Purpose

`11_manual_labels.md`의 다음 TODO는 round-1 label 중 불확실한 row를 다시 보고,
ready row 일부를 sample-check하는 것이다. 이번 단계에서는 다음 두 범위를 contact
sheet 기준으로 점검했다.

- `needs_second_review`: 5 rows
- `ready_for_human_confirmation` stratified sample: 20 rows

Boundary:

```text
second_review_label != paper-locked human annotation
```

이번 review는 contact sheet 기반이다. Mesh/point-level 확인은 아직 하지 않았다.
따라서 label change는 paper-final label이 아니라 H002 audit workflow의 보수적
수정 권고다.

## Artifacts

Script:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/second_review.py
```

Outputs:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/second_review/reviewed_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/second_review/changed_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/second_review/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/second_review/report.md
```

No H001 artifact was modified.

## Scope

| Review group | Rows |
| --- | ---: |
| `needs_second_review` | 5 |
| `ready_sample` | 20 |
| total | 25 |

The ready sample intentionally over-sampled `support_contact /
plausible_unlabeled_relation`, because this bucket is the most important and
riskiest H002 positive signal.

## Result

Decision counts:

| Decision | Rows |
| --- | ---: |
| `keep` | 20 |
| `revise` | 5 |

Second-review label distribution:

| Second-review label | Rows |
| --- | ---: |
| `plausible_unlabeled_relation` | 6 |
| `label_granularity_mismatch` | 5 |
| `uncertain_needs_visual` | 5 |
| `annotation_sparsity_likely` | 4 |
| `source_false_positive` | 3 |
| `object_pair_mismatch` | 2 |

Changed rows:

| Row | Round 1 | Second review | Reason |
| --- | --- | --- | --- |
| `h002_round1_0021` | `plausible_unlabeled_relation` | `source_false_positive` | `shower curtain standing on floor` has weak predicate semantics. |
| `h002_round1_0025` | `plausible_unlabeled_relation` | `object_pair_mismatch` | support surface appears to be furniture/shelf, not wall endpoint. |
| `h002_round1_0031` | `plausible_unlabeled_relation` | `object_pair_mismatch` | `book standing on wall` is not reliable from crops. |
| `h002_round1_0056` | `plausible_unlabeled_relation` | `uncertain_needs_visual` | cabinet identity/crop is weak. |
| `h002_round1_0041` | `label_granularity_mismatch` | `source_false_positive` | `ottoman standing on cabinet` is visually unsupported; GT `right` is more plausible. |

## Interpretation

This second review does not kill H002, but it changes the claim boundary.

The positive signal still exists:

- `shelf higher than floor` and similar `relative_vertical` cases are visually
  straightforward annotation-sparsity/coverage cases.
- Some `support_contact` no-GT rows are convincing, such as `flower on shelf`,
  `box on floor`, `chair on floor`, and `sofa on floor`.
- `label_granularity_mismatch` is real for cases where the same object pair has
  GT `left`, `standing on`, `attached to`, or `standing in`, while the predicted
  relation expresses another compatible or nearby relation family.

But the risk is also clear:

- `support_contact` has high semantic and geometric appeal, but it is sensitive
  to endpoint identity. If the object endpoint is `wall` or the subject is
  generic/weakly cropped, a satisfied geometry witness can still produce a bad
  relation edge.
- Geometry satisfiability alone is not enough to call a no-GT edge a missing
  positive.
- H002 should keep `object_pair_mismatch`, `source_false_positive`, and
  `uncertain_needs_visual` as first-class audit outcomes rather than treating
  them as noise.

## Current Verdict

H002 should continue, but only as a conservative reliability benchmark branch.

Allowed current claim:

```text
Contact-sheet second review confirms that no-GT geometry-satisfied high-rank
relations include real annotation/ontology mismatch cases, but also exposes
support/contact-specific false positives and endpoint mismatches. Therefore
relation-level reliability must separate semantic confidence, geometry witness,
object-pair validity, and annotation coverage.
```

Blocked claims:

- `geometry_satisfied + no_gt` means missing positive.
- `support_contact` witness alone is enough for relation validity.
- Round-1 labels can be used as paper-final labels.
- H002 is ready as a rescoring method.

## Next TODO

Next document:

```text
13_revision_impact.md
```

Required next work:

- Estimate how the 5/25 second-review revision rate affects the high-rank
  round-1 distribution.
- Report revision risk by family, especially `support_contact`.
- Produce a conservative claim table:
  - confirmed/likely positive signal,
  - endpoint/object-pair risk,
  - source false-positive risk,
  - still-needs-mesh cases.
- Decide whether H002's next step should be:
  - a larger manual audit,
  - a mesh/point-level verifier audit,
  - or a benchmark framing document.

