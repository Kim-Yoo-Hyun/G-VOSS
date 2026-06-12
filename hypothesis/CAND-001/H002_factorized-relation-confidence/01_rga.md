# H002 RGA Contract

Last updated: 2026-06-11

## Purpose

`RGA(Relation-Geometric Agreement)`는 H002의 문제 정의를 고정하는 benchmark
contract다. 목표는 3D Scene Graph relation prediction에서 semantic plausibility와
geometric satisfiability가 언제 일치하거나 충돌하는지 분리해 측정하는 것이다.

H002에서 `RGA`는 scoring method가 아니다. `p_geom_valid`를 새 이름으로 바꾸는
것도 아니다. `RGA`는 prediction row를 semantic axis와 geometry axis의 joint
state로 배치하고, 기존 label-recall 중심 metric과 H001 `Violation@K`가 숨길 수
있는 mismatch bucket을 정량화한다.

## Boundary From H001

H001의 핵심 geometry score는 다음과 같다.

```text
p_geom_valid = P(relation geometry is valid | family-specific geometry features)
```

H001의 primary use는 `semantic_score * p_geom_valid` re-ranking 또는
rule-verified filtering으로 violation을 줄이는 것이다.

H002의 `RGA`는 다른 target을 둔다.

```text
RGA(e) = joint_state(
  semantic_plausibility_or_label_match(e),
  geometric_satisfiability(e),
  evidence_coverage(e),
  uncertainty(e)
)
```

따라서 `p_geom_valid`는 H002에서 geometry axis의 입력 signal 중 하나일 뿐이고,
H002의 primary output은 `rga_bucket`, `RGA-HL@K`, `RGA-LH` diagnostics,
`RGA-disagreement`, and `RGA-coverage`다.

H002가 독립 branch로 남으려면 아래 중 적어도 하나를 보여야 한다.

- `RGA`가 기존 `Violation@K`와 다른 failure bucket 또는 denominator caveat를
  드러낸다.
- high-semantic / low-geometry bucket이 `VL-SAT`와 Open3DSG에서 반복된다.
- low-semantic / high-geometry bucket이 semantic underconfidence, missed relation,
  annotation sparsity, or ontology mismatch를 드러낸다.
- `semantic_score`와 `p_geom_valid`의 disagreement가 relation-family별 failure
  taxonomy와 일치한다.
- factorized posterior model이 H001 re-ranking보다 counterfactual robustness,
  calibration, or uncertainty handling에서 추가 설명력을 보인다.

그렇지 않으면 H002는 독립 hypothesis가 아니라 H001 analysis 또는 appendix로
흡수한다.

## Row Unit

RGA의 기본 단위는 identity-preserving relation prediction row다. aggregate metric
파일만으로는 RGA를 계산하지 않는다.

Required identity fields:

- `source_id`: `vlsat`, `open3dsg`, or later source id.
- `split`: train, train-dev, validation, or test-like split.
- `scan_id`
- `subgraph_id` or context id.
- `subject_id`
- `object_id`
- `predicate`
- `relation_family`
- `source_rank` or rank within source prediction list.
- `semantic_score_raw`
- `semantic_score_norm` or a declared rank-based proxy.
- `geometry_join_id`
- `geometry_status`
- `p_geom_valid`, if available.
- `label_match`, if GT matching is available.
- `provenance`: source artifact path, verifier version, mapping version.

## Axes

### Semantic Axis

Primary H002 semantic axis is rank-based, because different sources expose scores
with different calibration.

For top-K metrics:

```text
semantic_high_K(e) = e is selected by semantic_only top-K for its graph/context
```

Default K values:

- `K=50`
- `K=100`

For all-row diagnostics only, a source-specific `tau_sem` may be used. `tau_sem`
must be frozen from train/train-dev or declared as a fixed percentile before
validation reporting. It must not be selected after inspecting validation RGA
results.

When GT matching is available, H002 also records a label axis:

```text
label_match(e) in {1, 0, unavailable}
```

This separates two cases that can otherwise be conflated:

- high source confidence but no exact GT credit.
- exact-label correct but geometrically unsupported under observed 3D evidence.

### Geometry Axis

Primary geometry state uses the frozen H001 verifier/evidence policy when the
relation family is supported.

Allowed states:

- `satisfied`: relation-specific geometry evidence supports the predicate.
- `unsatisfied`: relation-specific geometry evidence contradicts the predicate.
- `uncertain`: geometry is checkable but evidence is ambiguous or incomplete.
- `unsupported`: relation family has no frozen geometry policy.
- `missing`: row cannot be joined to required geometry evidence.

Primary `unsatisfied` assignment is based on deterministic verifier status, not
on validation-tuned `p_geom_valid` thresholds.

`p_geom_valid` is used for continuous disagreement analysis and later posterior
models. If a probabilistic geometry threshold is needed for a sensitivity
analysis, the threshold must be fixed from train/train-dev calibration only.

## Buckets

RGA records confidence-geometry buckets:

| Bucket | Semantic axis | Geometry axis | Meaning |
| --- | --- | --- | --- |
| `RGA-HH` | high | satisfied | source trusts an edge that geometry supports |
| `RGA-HL` | high | unsatisfied | semantic overconfidence: high semantic, invalid geometry |
| `RGA-HU` | high | uncertain | source trusts an edge whose geometry cannot be decided |
| `RGA-HM` | high | missing/unsupported | source trusts an edge outside current geometry coverage |
| `RGA-LH` | low | satisfied | semantic underconfidence: geometry plausible edge under-ranked by semantic source |
| `RGA-LL` | low | unsatisfied | low semantic and invalid geometry |
| `RGA-LU` | low | uncertain | low semantic with uncertain geometry |
| `RGA-LM` | low | missing/unsupported | low semantic outside current geometry coverage |

When `label_match` is available, H002 also records label-geometry buckets:

| Bucket | Label axis | Geometry axis | Meaning |
| --- | --- | --- | --- |
| `RGA-TP-GS` | label match | satisfied | exact-label correct and geometry-supported |
| `RGA-TP-GU` | label match | unsatisfied | exact-label correct but geometry-contradicted |
| `RGA-FP-GS` | no label match | satisfied | no exact-label credit but geometry-supported |
| `RGA-FP-GU` | no label match | unsatisfied | no exact-label credit and geometry-contradicted |
| `RGA-*-GC` | any label state | uncertain/missing/unsupported | coverage or uncertainty case |

The label-geometry table is required for the claim that existing label-centric
metrics and geometry-centric violation metrics are insufficient by themselves.

## Metrics

All RGA metrics must report their denominator explicitly.

### `RGA-HL@K`

Core high-semantic / low-geometry failure rate.

```text
RGA-HL@K =
  count(e in TopK_semantic and geometry_status = unsatisfied)
  / count(e in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
```

Primary denominator excludes `unsupported` and `missing` rows, but includes
`uncertain` so that ambiguity is not silently removed from the selected set.

Report with:

- numerator count.
- denominator count.
- `RGA-uncertain@K`.
- `RGA-coverage@K`.

Equivalence check:

- If `RGA-HL@K` is numerically identical to H001 `Violation@K` for the same
  source and condition, H002 must show additional value through label-geometry
  buckets, disagreement, coverage, or counterfactual robustness. Otherwise this
  metric is just a rename.

### `RGA-valid@K`

Strict geometry-supported rate among semantically selected rows.

```text
RGA-valid@K =
  count(e in TopK_semantic and geometry_status = satisfied)
  / count(e in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
```

This is stricter than H001 non-violation because `uncertain` is not counted as
valid. For H001 comparability, also report:

```text
RGA-nonviolated@K =
  count(e in TopK_semantic and geometry_status in {satisfied, uncertain})
  / count(e in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
```

### `RGA-LH-tail@K`

Low-semantic / high-geometry candidate rate.

```text
RGA-LH-tail@K =
  count(e not in TopK_semantic and geometry_status = satisfied)
  / count(e not in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
```

This is not a relation-promotion metric by itself. It is a candidate-discovery
and annotation/ontology audit metric. Reports must stratify it by:

- rank band, such as `101-200`, `201-500`, `outside-500`, if available.
- relation family.
- label match status: exact, same-pair-other-predicate, no-GT-pair.
- object-pair quality or audit status when available.

Required interpretation:

- `RGA-LH` can indicate semantic underconfidence or a missed reliable relation.
- `RGA-LH` can also be a geometry-trivial relation, annotation sparsity case,
  object-pair mismatch, or source false positive.
- Therefore `RGA-LH` rows require audit before being used for graph promotion.

### `RGA-uncertain@K`

Geometry ambiguity rate among semantically selected rows.

```text
RGA-uncertain@K =
  count(e in TopK_semantic and geometry_status = uncertain)
  / count(e in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
```

This prevents `uncertain` rows from being hidden inside valid or invalid counts.

### `RGA-coverage@K`

How much of the semantically selected prediction set can be evaluated by the
current geometry policy.

```text
RGA-coverage@K =
  count(e in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
  / count(e in TopK_semantic)
```

Also report missing categories:

- `unsupported_family_rate@K`
- `missing_geometry_rate@K`

### `RGA-disagreement`

Continuous semantic-geometry mismatch score.

Primary overconfidence score:

```text
RGA-overconfidence@K =
  mean_{e in TopK_semantic and p_geom_valid available}
    max(0, semantic_score_norm(e) - p_geom_valid(e))
```

This focuses on high semantic confidence that geometry does not support.

Primary underconfidence score:

```text
RGA-underconfidence@tailK =
  mean_{e not in TopK_semantic and p_geom_valid available}
    max(0, p_geom_valid(e) - semantic_score_norm(e))
```

This focuses on geometry-supported relation candidates that semantic ranking
under-ranks. It must be reported with rank-band and label-geometry buckets;
otherwise dense spatial relations such as `close by` can dominate the signal.

Secondary diagnostics:

- Spearman correlation between `semantic_score_norm` and `p_geom_valid`.
- Mean absolute difference `abs(semantic_score_norm - p_geom_valid)`.
- Family-wise disagreement table.
- Source-wise disagreement table.

`semantic_score_norm` must be source-specific and frozen before validation
reporting. If reliable score normalization is unavailable, rank-derived
semantic confidence is used:

```text
semantic_score_norm(e) = 1 - (rank(e) - 1) / (N_context - 1)
```

with `N_context` declared per graph/context.

### Label-Geometry Agreement

When GT matching exists:

```text
RGA-TP-GU@K =
  count(e in TopK_semantic and label_match = 1 and geometry_status = unsatisfied)
  / count(e in TopK_semantic and label_match = 1 and geometry_status in {satisfied, unsatisfied, uncertain})
```

This is a reviewer-defense metric. It tests whether exact-label correctness and
geometric satisfiability can disagree, or whether apparent disagreement is only
caused by false-positive predictions.

## Uncertain Policy

Primary policy:

- `uncertain` is not valid.
- `uncertain` is not invalid.
- `uncertain` is reported as its own bucket.
- primary `RGA-HL@K` does not count `uncertain` as unsatisfied.
- primary `RGA-valid@K` does not count `uncertain` as satisfied.

Required sensitivity:

- conservative: count `uncertain` as invalid.
- optimistic: count `uncertain` as valid/nonviolated.

If conclusions depend on the uncertain policy, H002 cannot claim robust
semantic-geometric inconsistency reduction.

## Required Reports

Each RGA diagnostic report must include:

- source name and source artifact version.
- split and scope.
- relation families covered.
- number of graphs/contexts.
- number of source prediction rows.
- number of top-K selected rows.
- number of geometry-supported rows.
- number of unsupported-family rows.
- number of missing-geometry rows.
- `RGA-HL@50`, `RGA-HL@100`.
- `RGA-LH-tail@50`, `RGA-LH-tail@100`, or declared low-rank-band equivalent.
- `RGA-valid@50`, `RGA-valid@100`.
- `RGA-nonviolated@50`, `RGA-nonviolated@100`.
- `RGA-uncertain@50`, `RGA-uncertain@100`.
- `RGA-coverage@50`, `RGA-coverage@100`.
- `RGA-disagreement@50`, `RGA-disagreement@100`.
- `RGA-overconfidence` and `RGA-underconfidence` if continuous semantic and
  geometry scores are available.
- label-geometry bucket table if GT matching is available.
- family-wise table.
- source-wise table for `VL-SAT` and Open3DSG.

## Freeze Rules

Before validation RGA reporting:

- relation-family mapping must be frozen.
- geometry status mapping must be frozen.
- `semantic_score_norm` rule must be frozen per source.
- top-K values must be fixed at `50` and `100`.
- uncertain policy must be frozen.
- denominator policy must be frozen.

After validation RGA reporting:

- do not change bucket definitions to improve H002.
- do not tune `tau_sem` or `tau_geom` on validation rows.
- do not hide unsupported or missing rows from coverage.
- do not claim H002 novelty if RGA adds no information beyond H001
  `Violation@K` and existing failure rows.

## Next TODO

The next H002 document should be `02_schema.md` or `02_inventory.md`.

Minimum next checks:

- Inventory whether H001 full-validation `VL-SAT` artifacts expose all required
  RGA fields.
- Inventory whether Open3DSG recovery branch artifacts expose all required RGA
  fields.
- Define the first H002 edge schema projection with `semantic_score`,
  `geometry_residual`, `p_geom_valid`, `rga_bucket`, `posterior_edge_valid`,
  and `provenance`.
