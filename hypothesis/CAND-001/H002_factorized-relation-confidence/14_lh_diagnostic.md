# H002 LH Diagnostic

Last updated: 2026-06-12

## Scope Correction

This diagnostic was computed from H001 `full_validation` artifacts:

- `experiments/H001_geom_reliability/sources/vlsat/full_validation/`
- `experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/`

Therefore this document is held-out diagnostic evidence only. It must not be
used as hypothesis-selection or model-design evidence. H002 hypothesis-stage
diagnostics must be rebuilt on train-set artifacts before any method or benchmark
decision is made.

## Purpose

`13_revision_impact.md`에서 H002 방향을 bidirectional mismatch로 확장했다. 이번
단계의 목적은 새로 추가된 축인 `low-semantic + high-geometry`, 즉 `RGA-LH`가 실제로
존재하는지, 그리고 `RGA-HL`과 다른 정보를 주는지 확인하는 것이다.

Core question:

```text
semantic rank가 낮거나 top-K 밖인 relation 중 geometry는 satisfied인 candidate가
충분히 존재하는가?
```

## Operational Definition

Low semantic:

```text
semantic_rank_in_subgraph > 100
```

High semantic reference:

```text
semantic_rank_in_subgraph <= 100
```

Rank bands:

- `rank_101_200`
- `rank_201_500`
- `rank_501_1000`
- `rank_gt1000`

LH condition:

```text
rank > 100
and predicate_family in {support_contact, proximity, relative_vertical}
and verification_status = satisfied
```

HL reference condition:

```text
rank <= 100
and predicate_family in {support_contact, proximity, relative_vertical}
and verification_status = violated
```

## Artifacts

Script:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/lh_diagnostic.py
```

Outputs:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/lh_diagnostic/vlsat_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/lh_diagnostic/vlsat_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/lh_diagnostic/open3dsg_recovery_relaxed_views_min2_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/lh_diagnostic/open3dsg_recovery_relaxed_views_min2_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/lh_diagnostic/report.md
```

No H001 artifact was modified.

## Source Summary

| Source | High checkable | `RGA-HL@100` count | `RGA-HL@100` rate | Low-tail checkable | `RGA-LH-tail` count | `RGA-LH-tail` rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `vlsat` | 17,890 | 337 | 0.0188 | 202,958 | 75,684 | 0.3729 |
| `open3dsg_recovery_relaxed_views_min2` | 19,874 | 3,118 | 0.1569 | 140,722 | 58,493 | 0.4157 |
| combined | 37,764 | 3,455 | 0.0915 | 343,680 | 134,177 | 0.3904 |

Interpretation:

- `RGA-LH` exists at large scale in both sources.
- `RGA-LH` is not the same signal as `RGA-HL`.
- `RGA-HL` is about semantic overconfidence.
- `RGA-LH` is about semantic underconfidence, missing/under-ranked relation
  candidates, annotation coverage, and ontology mismatch.

## LH Distribution

Combined LH rows by family:

| Family | LH rows |
| --- | ---: |
| `support_contact` | 48,039 |
| `proximity` | 45,451 |
| `relative_vertical` | 40,687 |

Combined LH rows by rank band:

| Rank band | LH rows |
| --- | ---: |
| `rank_501_1000` | 39,970 |
| `rank_201_500` | 38,778 |
| `rank_gt1000` | 36,716 |
| `rank_101_200` | 18,713 |

Combined LH rows by label status:

| Label status | LH rows |
| --- | ---: |
| `no_gt_for_pair` | 103,167 |
| `pair_has_other_predicate` | 25,035 |
| `family_match` | 3,999 |
| `exact_match` | 1,976 |

Key reading:

- `exact_match + geometry_satisfied + rank > 100` exists: 1,976 rows.
  This is the cleanest semantic-underconfidence signal because the relation has
  exact GT label credit and geometry support but is not in semantic top-100.
- Most LH rows are `no_gt_for_pair`: 103,167 rows.
  This is not automatically a missing-positive signal. It may include annotation
  sparsity, trivial geometry, object-pair mismatch, or source false positive.
- `pair_has_other_predicate`: 25,035 rows.
  This is likely where ontology and multi-relation granularity matter.

## Family And Label Status

| Family / label status | LH rows |
| --- | ---: |
| `proximity / no_gt_for_pair` | 36,692 |
| `relative_vertical / no_gt_for_pair` | 35,155 |
| `support_contact / no_gt_for_pair` | 31,320 |
| `support_contact / pair_has_other_predicate` | 12,087 |
| `proximity / pair_has_other_predicate` | 7,577 |
| `relative_vertical / pair_has_other_predicate` | 5,371 |
| `support_contact / family_match` | 3,997 |
| `proximity / exact_match` | 1,182 |
| `support_contact / exact_match` | 635 |
| `relative_vertical / exact_match` | 159 |
| `relative_vertical / family_match` | 2 |

Interpretation:

- `proximity` and `relative_vertical` LH rows may be dense geometry or annotation
  sparsity. They are useful for benchmark coverage, but less useful for direct
  graph promotion.
- `support_contact` has the strongest graph-update relevance, but prior
  second-review showed it also has endpoint/object-pair risk.
- Exact-match LH rows should be the first paper-safe evidence target because
  they avoid the no-GT ambiguity.

## Audit Queue

Audit queues were created for both sources:

| Source | Queue rows |
| --- | ---: |
| `vlsat` | 116 |
| `open3dsg_recovery_relaxed_views_min2` | 120 |
| total | 236 |

Sampling policy:

```text
top low-tail rank per (family, match_status, rank_band), per_stratum=3
```

Queue rows include:

- source id
- scan/subgraph id
- subject/object id and label
- predicate/family
- semantic score/rank
- rank band
- label match status
- geometry status
- `p_geom_valid`
- geometry reason codes
- LH machine hint

## Comparison With Previous H002 Evidence

Earlier H002 work focused mostly on:

```text
high semantic + low/uncertain geometry
high semantic + no-GT + geometry satisfied
```

This was useful but incomplete. The new LH diagnostic adds the other side:

```text
low semantic + geometry satisfied
```

This matters because relation reliability should explain both:

- why a high-scoring relation may be unsafe,
- why a low-scoring relation may still be geometrically/annotationally important.

Scene graph update implication:

| Bucket | Update implication |
| --- | --- |
| `RGA-HH` | keep/promote |
| `RGA-HL` | suppress, relabel, repair, or defer |
| `RGA-HU/HM` | defer until evidence improves |
| `RGA-LH` | candidate discovery, annotation/ontology audit, delayed promote |
| `RGA-LL` | ignore unless needed as negative/control |

## Current Verdict

H002 should continue as a bidirectional relation reliability benchmark branch.

Allowed current claim:

```text
RGA-LH exists at scale in both VL-SAT and Open3DSG recovery. This shows that
semantic-geometric mismatch is bidirectional: relation sources can be
geometrically unsafe when they are overconfident, but they can also under-rank
geometry-supported relations. Therefore H002's factorized relation reliability
representation is better motivated as a bidirectional diagnostic than as a
high-semantic failure detector only.
```

Blocked claims:

- `RGA-LH` rows are valid missing positives.
- `RGA-LH` rows should be automatically promoted into the scene graph.
- LH count alone proves annotation incompleteness.
- H002 is ready as a graph-update method.

## Next TODO

Next document:

```text
15_lh_audit.md
```

Required next work:

- Attach local visual assets/contact sheets to the 236 LH queue rows.
- Prioritize exact-match LH rows first:
  - `exact_match + geometry_satisfied + rank > 100`
  - especially `support_contact` and non-trivial `relative_vertical`.
- Then audit no-GT LH rows separately:
  - annotation sparsity,
  - geometry-trivial relation,
  - ontology mismatch,
  - object-pair mismatch,
  - source underconfidence,
  - uncertain-needs-mesh.
- Compare LH audit labels with previous HH/HL/no-GT high-rank audit labels.
- Decide whether H002 should move toward:
  - bidirectional benchmark only,
  - graph-update candidate discovery,
  - or scoped mesh/point-level audit.
