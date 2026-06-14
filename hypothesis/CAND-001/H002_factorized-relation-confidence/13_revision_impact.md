# H002 Revision Impact

Last updated: 2026-06-12

## Purpose

`12_second_review.md`의 다음 TODO는 second-review revision이 high-rank round-1
distribution에 어떤 영향을 주는지 계산하고, H002의 다음 방향을 정하는 것이다.

이번 문서의 결론은 두 가지다.

1. `support_contact`는 positive signal이 남아 있지만 endpoint/object-pair risk가 크다.
2. H002는 `high-semantic + low-geometry`만 보면 불완전하다. 다음 단계부터
   `low-semantic + high-geometry`까지 포함하는 **bidirectional mismatch**로 확장한다.

## Artifacts

Script:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/revision_impact.py
```

Outputs:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/revision_impact/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/revision_impact/report.md
```

No H001 artifact was modified.

## Scope

Input:

- `artifacts/manual_labels/round1_labels.jsonl`: 192 high-rank rows
- `artifacts/second_review/reviewed_rows.jsonl`: 25 reviewed rows

Boundary:

```text
second-review rows are contact-sheet-only and intentionally emphasize
support_contact plausible cases; revision rates are diagnostic, not population
estimates.
```

## Direct Revision Impact

Round-1 distribution:

| Label | Rows |
| --- | ---: |
| `label_granularity_mismatch` | 96 |
| `annotation_sparsity_likely` | 61 |
| `plausible_unlabeled_relation` | 30 |
| `uncertain_needs_visual` | 4 |
| `source_false_positive` | 1 |

Direct-patch distribution after applying the 5 observed second-review changes:

| Label | Rows |
| --- | ---: |
| `label_granularity_mismatch` | 95 |
| `annotation_sparsity_likely` | 61 |
| `plausible_unlabeled_relation` | 26 |
| `uncertain_needs_visual` | 5 |
| `source_false_positive` | 3 |
| `object_pair_mismatch` | 2 |

Positive-signal bucket:

```text
round1:      187 / 192
direct patch: 182 / 192
```

Here positive signal means:

```text
label_granularity_mismatch
+ annotation_sparsity_likely
+ plausible_unlabeled_relation
```

Risk bucket:

```text
round1:       5 / 192
direct patch: 10 / 192
```

Risk means:

```text
source_false_positive
+ object_pair_mismatch
+ geometry_artifact
+ uncertain_needs_visual
```

## Revision Strata

All changed rows came from `support_contact`:

| Family / label change | Rows |
| --- | ---: |
| `support_contact / plausible_unlabeled_relation -> object_pair_mismatch` | 2 |
| `support_contact / plausible_unlabeled_relation -> source_false_positive` | 1 |
| `support_contact / plausible_unlabeled_relation -> uncertain_needs_visual` | 1 |
| `support_contact / label_granularity_mismatch -> source_false_positive` | 1 |

Interpretation:

- The second-review problem is not random across families.
- `relative_vertical` and many `proximity` cases remained stable in the sample.
- `support_contact` is useful but risky because geometry contact can be satisfied
  while the semantic predicate or object endpoint is wrong.

## Support-Contact Stress Test

For `support_contact / plausible_unlabeled_relation`, the sample was intentionally
strict:

| Quantity | Value |
| --- | ---: |
| high-rank target rows | 30 |
| reviewed target rows | 10 |
| changed target rows | 4 |
| sample revision rate | 0.400 |

If this diagnostic 40% revision rate were applied only as a stress test to all
30 `support_contact / plausible_unlabeled_relation` rows, the projected
distribution would be:

| Label | Rows |
| --- | ---: |
| `label_granularity_mismatch` | 96 |
| `annotation_sparsity_likely` | 61 |
| `plausible_unlabeled_relation` | 18 |
| `uncertain_needs_visual` | 7 |
| `object_pair_mismatch` | 6 |
| `source_false_positive` | 4 |

This is not a statistical population estimate. It is a reviewer-risk stress
test. Even under this stress test, H002 keeps a large annotation/ontology signal,
but the `support_contact` positive bucket becomes much less safe.

## Claim Table

| Claim type | Current support | Risk | Status |
| --- | --- | --- | --- |
| confirmed/likely positive signal | direct-patch positive bucket remains `182 / 192` | labels are not paper-locked | allowed as hypothesis-stage evidence |
| annotation/ontology mismatch | `label_granularity_mismatch` and `annotation_sparsity_likely` remain large | may include weak object crops | allowed with audit boundary |
| support/contact missing relation | some rows are convincing: `flower on shelf`, `box/chair/sofa on floor` | endpoint mismatch and predicate semantics errors | allowed only as audited subset |
| source false-positive risk | direct patch increases risk bucket from `5` to `10` | concentrated in `support_contact` | must be reported |
| still-needs-mesh cases | `uncertain_needs_visual`, weak crops, wall endpoints | contact sheet cannot prove contact/endpoint | requires mesh/point audit |

## Direction Update

H002 is now explicitly a bidirectional mismatch branch.

Old incomplete framing:

```text
high semantic + low geometry
```

Updated framing:

```text
high semantic + low geometry  -> semantic overconfidence / unsafe relation
low semantic + high geometry  -> semantic underconfidence / missed or under-ranked relation
```

Why this update is necessary:

- If H002 only studies `RGA-HL`, it is too close to H001-style geometry violation
  analysis.
- `RGA-LH` tests the other half of the factorized reliability claim: whether
  geometry can expose relation candidates that semantic rank underestimates.
- Scene graph update requires both directions:
  - `RGA-HL`: suppress, relabel, repair, or defer.
  - `RGA-LH`: discover candidate, audit annotation/ontology, delayed promote.

Boundary:

```text
RGA-LH is not automatic graph promotion.
```

Low-semantic/high-geometry rows must be separated into:

- true missed relation,
- annotation sparsity,
- predicate ontology mismatch,
- geometry-trivial relation,
- object-pair mismatch,
- source underconfidence,
- uncertain-needs-visual/mesh.

## Current Verdict

H002 should continue as a **bidirectional RGA benchmark/problem branch**.

Allowed current claim:

```text
Relation-level reliability cannot be explained by semantic confidence alone:
H002 must measure both semantic overconfidence (`RGA-HL`) and semantic
underconfidence or missed geometry-supported relations (`RGA-LH`), while
separating annotation coverage, object-pair validity, and uncertainty.
```

Blocked claims:

- `RGA-LH` rows are automatically valid missing positives.
- `RGA-HL` alone is enough to establish H002.
- Second-review labels are paper-final.
- H002 is ready as a rescoring or graph-update method.

## Next TODO

Next document:

```text
14_lh_diagnostic.md
```

Required next work:

- Define `low semantic` operationally:
  - outside top-100,
  - rank bands such as `101-200`, `201-500`, `outside-500`,
  - or bottom percentile if rank bands are unavailable.
- Build an `RGA-LH` candidate table:
  - `geometry_status = satisfied`,
  - semantic rank outside high-rank set,
  - family in current geometry-supported set,
  - label status: exact, pair-other, no-GT.
- Report counts by source, family, rank band, and label status.
- Create an audit queue for `low-semantic + high-geometry`.
- Compare `RGA-HL` and `RGA-LH` to decide whether H002 truly needs a
  bidirectional reliability representation.

