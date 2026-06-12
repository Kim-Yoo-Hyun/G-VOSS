# H002 RGA Framework

Last updated: 2026-06-12

## Purpose

`RGA(Relation-Geometric Agreement)`는 H002의 핵심 benchmark/diagnostic
framework다. 목표는 3D Scene Graph relation edge의 reliability를 단일 confidence로
보지 않고, semantic evidence와 geometry evidence가 서로 일치하는지 relation-level로
분해해 측정하는 것이다.

핵심 질문:

```text
Does semantic plausibility agree with geometric satisfiability?
```

RGA는 scoring model이 아니다. `p_geom_valid`를 다른 이름으로 바꾼 것도 아니다.
RGA는 relation candidate를 semantic axis, geometry axis, label axis, coverage axis,
uncertainty axis 위에 배치하고, 기존 label-recall metric이나 geometry-only violation
metric이 숨기는 mismatch state를 드러내는 framework다.

## Core View

H002의 출발점은 다음 분리다.

```text
semantic score != geometry validity != relation reliability
```

따라서 relation edge `e = (subject, predicate, object)`에 대해 RGA는 다음 joint state를
기록한다.

```text
RGA(e) = {
  semantic_axis(e),
  geometry_axis(e),
  label_axis(e),
  coverage_state(e),
  uncertainty_state(e),
  disagreement_score(e)
}
```

이 프레임워크에서 중요한 failure/candidate는 양방향이다.

| Case | Meaning |
| --- | --- |
| high semantic + low geometry | semantic overconfidence; source trusts a relation that geometry contradicts |
| low semantic + high geometry | semantic underconfidence, missed relation, annotation sparsity, or ontology mismatch candidate |
| high semantic + uncertain geometry | source trusts a relation whose physical status cannot be decided |
| high semantic + unsupported geometry | current verifier cannot evaluate this relation family |

## Unit Of Analysis

RGA의 기본 단위는 aggregate metric이 아니라 identity-preserving prediction row다.

Required identity:

```text
source_id
scan_id
subgraph_id
subject_id
object_id
predicate_label
predicate_family
prediction_id
semantic_rank_in_subgraph
semantic_score_raw
semantic_score_norm
geometry_status
p_geom_valid, if available
label_match_status, if GT/audit matching is available
provenance
```

현재 H002 train pilot의 row artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/match_rows.jsonl
```

Count:

```text
118,560 prediction rows
```

## Evidence Axes

### 1. Semantic Axis

Semantic axis는 relation source가 해당 edge를 얼마나 그럴듯하게 보는지 나타낸다.
서로 다른 source의 raw score calibration이 다를 수 있으므로, H002의 primary metric은
rank 기반이다.

Default top-K:

```text
K = 50
K = 100
```

Definition:

```text
semantic_high_K(e) = semantic_rank_in_subgraph(e) <= K
semantic_low_K(e)  = semantic_rank_in_subgraph(e) > K
```

현재 train RGA에서는 cross-source 비교가 아니라 Open3DSG train pilot 내부 진단이므로
rank-normalized semantic score도 함께 기록한다.

```text
semantic_score_norm =
  1 - (rank_in_context - 1) / (context_prediction_count - 1)
```

Semantic axis가 답하는 질문:

```text
Did the relation source rank this edge highly?
```

### 2. Geometry Axis

Geometry axis는 관측된 3D evidence가 해당 relation predicate를 지지하는지 본다.
현재 H002는 H001에서 동결한 relation-family geometry verifier를 읽어서 사용한다.

H001 status to H002 status:

| H001 status | H002 geometry status |
| --- | --- |
| `satisfied` | `satisfied` |
| `violated` | `unsatisfied` |
| `uncertain` | `uncertain` |
| `unsupported` | `unsupported` |
| missing join | `missing` |

Important rule:

```text
RGA-HL/RGA-LH bucket is determined by deterministic geometry_status,
not by thresholding p_geom_valid.
```

`p_geom_valid`는 geometry-only continuous evidence다. H002에서는 다음 용도로만 쓴다.

- `geometry_only` baseline score.
- semantic-geometry continuous disagreement.
- later factorized reliability posterior의 geometry factor.

Geometry axis가 답하는 질문:

```text
Does observed 3D geometry support this relation predicate?
```

### 3. Label Axis

Label axis는 GT relation 또는 audit label과의 관계를 기록한다. RGA의 deployable
posterior input으로 쓰는 것이 아니라, train/evaluation supervision과 diagnostic
stratification에 사용한다.

Train pilot label states:

| Label Status | Meaning |
| --- | --- |
| `exact_match` | same subject/object/predicate exists in train GT |
| `family_match` | same pair has a same-family predicate |
| `pair_has_other_predicate` | same pair has another GT predicate |
| `no_gt_for_pair` | no GT relation for the directed object pair |

Label axis가 답하는 질문:

```text
Is this edge supported by the annotation ontology, and if not, what kind of mismatch is it?
```

### 4. Coverage Axis

Coverage axis는 geometry verifier가 해당 row를 평가할 수 있었는지 기록한다.

Coverage states:

| Geometry Status | Coverage State |
| --- | --- |
| `satisfied` | `covered_checkable` |
| `unsatisfied` | `covered_checkable` |
| `uncertain` | `covered_checkable_uncertain` |
| `unsupported` | `unsupported_family` |
| `missing` | `missing_geometry` |

Coverage axis가 필요한 이유:

- unsupported relation family를 invalid geometry로 오해하지 않기 위해서.
- missing geometry를 model failure로 오해하지 않기 위해서.
- top-K metric denominator를 명확히 하기 위해서.

Coverage axis가 답하는 질문:

```text
Was this edge actually evaluable by the current geometry policy?
```

### 5. Uncertainty Axis

Uncertainty axis는 geometry가 애매하거나 evidence가 부족한 경우를 valid/invalid에
강제로 넣지 않는다.

Uncertainty examples:

```text
geometry_status = uncertain
ambiguous relation-specific residual
low point/view evidence
semantic-geometry conflict
unsupported family under current verifier
```

Uncertainty axis가 답하는 질문:

```text
Should the framework make a hard keep/reject decision, or abstain/audit?
```

## RGA Buckets

RGA는 semantic axis와 geometry axis를 결합해 bucket을 만든다.

| Bucket | Semantic | Geometry | Interpretation |
| --- | --- | --- | --- |
| `RGA-HH` | high | satisfied | source trusts an edge that geometry supports |
| `RGA-HL` | high | unsatisfied | semantic overconfidence |
| `RGA-HU` | high | uncertain | high semantic but geometry cannot decide |
| `RGA-HM` | high | unsupported/missing | high semantic outside current geometry coverage |
| `RGA-LH` | low | satisfied | semantic underconfidence or missed/under-ranked candidate |
| `RGA-LL` | low | unsatisfied | low semantic and invalid geometry |
| `RGA-LU` | low | uncertain | low semantic with ambiguous geometry |
| `RGA-LM` | low | unsupported/missing | low semantic outside current geometry coverage |

When label evidence exists, RGA also records label-geometry buckets.

| Bucket | Label Axis | Geometry | Interpretation |
| --- | --- | --- | --- |
| `RGA-TP-GS` | exact label match | satisfied | label-correct and geometry-supported |
| `RGA-TP-GU` | exact label match | unsatisfied | label-correct but geometry-contradicted |
| `RGA-FP-GS` | no exact label match | satisfied | no label credit but geometry-supported |
| `RGA-FP-GU` | no exact label match | unsatisfied | no label credit and geometry-contradicted |
| `RGA-*-GC` | any label state | uncertain/unsupported/missing | coverage or uncertainty case |

이 label-geometry table이 중요한 이유는 label-centric metric과 geometry-centric metric이
서로 다른 질문을 하기 때문이다.

```text
label correctness asks: is this annotated as correct?
geometry satisfiability asks: is this physically supported by observed 3D evidence?
relation reliability asks: should this edge be trusted under both evidence types and coverage limits?
```

## Metrics

All RGA metrics report numerator and denominator. Unsupported/missing rows are
not silently dropped; they are reported as coverage.

### `RGA-HL@K`

High semantic / low geometry failure rate.

```text
RGA-HL@K =
  count(e in TopK_semantic and geometry_status = unsatisfied)
  / count(e in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
```

This measures semantic overconfidence under checkable geometry.

### `RGA-valid@K`

Strict geometry-supported rate among semantically selected rows.

```text
RGA-valid@K =
  count(e in TopK_semantic and geometry_status = satisfied)
  / count(e in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
```

`uncertain` is not counted as valid.

### `RGA-nonviolated@K`

H001-compatible non-violation style rate.

```text
RGA-nonviolated@K =
  count(e in TopK_semantic and geometry_status in {satisfied, uncertain})
  / count(e in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
```

This is reported only for comparison. It is less strict than `RGA-valid@K`.

### `RGA-uncertain@K`

Ambiguous geometry rate among semantically selected rows.

```text
RGA-uncertain@K =
  count(e in TopK_semantic and geometry_status = uncertain)
  / count(e in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
```

### `RGA-coverage@K`

How much of the selected semantic top-K can be checked by the current geometry
policy.

```text
RGA-coverage@K =
  count(e in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
  / count(e in TopK_semantic)
```

### `RGA-LH-tail@K`

Low semantic / high geometry candidate rate.

```text
RGA-LH-tail@K =
  count(e not in TopK_semantic and geometry_status = satisfied)
  / count(e not in TopK_semantic and geometry_status in {satisfied, unsatisfied, uncertain})
```

Important interpretation:

```text
RGA-LH is not automatic graph promotion.
```

It must be audited because it can mean:

- true semantic underconfidence.
- annotation sparsity.
- ontology or predicate granularity mismatch.
- dense/trivial relation, especially `close by`.
- object-pair error.
- geometry artifact.

### Continuous Disagreement

RGA also records continuous mismatch using `semantic_score_norm` and `p_geom_valid`.

Overconfidence score:

```text
max(0, semantic_score_norm - p_geom_valid)
```

Underconfidence score:

```text
max(0, p_geom_valid - semantic_score_norm)
```

This continuous signal is useful for ranking audit candidates and later posterior
features, but it does not replace deterministic RGA buckets.

## Framework Pipeline

RGA is implemented as a staged framework.

### Stage 1. Train Source Contract

Document:

```text
18_train_source_contract.md
```

Purpose:

- select train-only Open3DSG pilot scope.
- avoid validation leakage.
- freeze 100 train subgraphs / 100 scans.
- preserve source provenance.

Key artifact:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/relationships_train_pilot.json
```

### Stage 2. Source Prediction Export

Documents:

```text
19_train_raw_dump_runner.md
20_train_adapter_export.md
```

Purpose:

- run Open3DSG train pilot raw dump.
- adapt raw source predictions into identity-preserving H001/H002 prediction rows.
- fix provenance so prediction rows point to `relationships_train_pilot.json`.

Key artifact:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/adapter/predictions.jsonl
```

Count:

```text
118,560 rows
```

### Stage 3. Geometry Join

Document:

```text
21_train_geometry_join.md
```

Purpose:

- attach H001 frozen geometry verifier outputs to each prediction row.
- preserve row identity.
- record deterministic geometry status and continuous `p_geom_valid`.

Key artifact:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/geometry/verification.jsonl
```

Current geometry status:

| Status | Rows |
| --- | ---: |
| `satisfied` | 12,285 |
| `uncertain` | 11,841 |
| `violated` / H002 `unsatisfied` | 3,234 |
| `unsupported` | 91,200 |

### Stage 4. RGA Row Construction

Document:

```text
22_train_rga_rows.md
```

Purpose:

- join prediction rows, geometry rows, and train GT subset.
- compute RGA buckets, label-geometry buckets, disagreement scores, coverage.
- keep `posterior_edge_valid = null`.

Key artifact:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/match_rows.jsonl
```

Primary train metrics:

| Metric | K=50 | K=100 |
| --- | ---: | ---: |
| `RGA-HL@K` | 2.35% | 3.87% |
| `RGA-valid@K` | 63.53% | 57.41% |
| `RGA-nonviolated@K` | 97.65% | 96.13% |
| `RGA-uncertain@K` | 34.12% | 38.71% |
| `RGA-coverage@K` | 3.40% | 12.14% |
| `RGA-LH-tail@K` | 44.78% | 44.32% |

Top100 denominator:

| Group | Total | Covered | Satisfied | Unsatisfied | Uncertain | Unsupported |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| top100 | 10,000 | 1,214 | 697 | 47 | 470 | 8,786 |
| tail > 100 | 108,560 | 26,146 | 11,588 | 3,187 | 11,371 | 82,414 |

### Stage 5. RGA Audit Seed

Document:

```text
23_train_rga_audit.md
```

Purpose:

- do not inspect all 11,588 LH rows manually.
- create compact audit seed.
- preserve strata by queue, family, rank band, and label status.

Audit seed:

| Queue | Source Rows | Seed Rows |
| --- | ---: | ---: |
| `HL` | 47 | 47 |
| `LH` | 11,588 | 170 |
| total | 11,635 | 217 |

Key artifact:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/audit/audit_seed.jsonl
```

### Stage 6. Manual-Audit Preparation

Document:

```text
24_train_manual_audit.md
```

Purpose:

- generate contact sheets and mesh/instance links.
- assign machine-assisted working labels.
- keep human-confirmed labels separate.

Working label distribution:

| Working Label | Rows |
| --- | ---: |
| `ontology_mismatch` | 63 |
| `true_underconfidence` | 48 |
| `semantic_overconfidence` | 45 |
| `annotation_sparsity` | 28 |
| `uncertain_needs_visual_or_mesh` | 22 |
| `dense_relation_noise` | 11 |

Boundary:

```text
working label != paper-locked human annotation
human_confirmed_share = 0.0
```

### Stage 7. Factor Contract

Document:

```text
25_factor_contract.md
```

Purpose:

- connect RGA diagnostics to a later factorized reliability posterior.
- define target modes.
- freeze leakage rules.
- define main baselines.

Deployable posterior:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

Oracle diagnostic only:

```text
P(R_e = 1 | S_e, L_e, G_e, C_e, U_e)
```

Main baseline set:

| Baseline | Feature Blocks |
| --- | --- |
| `semantic_only` | `S_e` |
| `geometry_only` | `G_e + C_e` |
| `semantic_plus_geometry` | `S_e + G_e` |
| `factorized_reliability_posterior` | `S_e + G_e + C_e + U_e + interactions` |

`L_e` is supervision/evaluation/oracle evidence only. It is not a deployable
input feature.

## RGA To Factorized Reliability

RGA is the measurement framework. Factorized reliability posterior is the later
method candidate.

The relation is:

```text
RGA rows -> audit labels/targets -> feature blocks -> posterior smoke model
```

RGA provides:

- semantic axis features.
- geometry axis features.
- coverage states.
- uncertainty states.
- label/audit targets.
- mismatch buckets for evaluation.

The posterior should learn:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

It should not simply learn:

```text
semantic_score * p_geom_valid
```

because that simple product cannot represent:

- unsupported geometry as coverage/abstention.
- uncertain geometry as uncertainty.
- low-semantic/high-geometry underconfidence.
- label granularity or ontology mismatch.
- dense relation noise.

## Current Open3DSG Train Pilot Instantiation

Scope:

```text
Open3DSG train pilot
100 train subgraphs
100 scans
118,560 prediction rows
```

Geometry-checkable families:

```text
proximity
relative_vertical
support_contact
```

Unsupported in current verifier:

```text
relative_horizontal
attachment_deferred
unsupported_first_pass
```

Primary observation:

- `RGA-HL@100 = 3.87%`: high semantic but geometry unsatisfied exists, but is not
  the dominant train pilot signal.
- `RGA-LH-tail@100 = 44.32%`: low semantic but geometry satisfied is large.
- LH is mixed: true underconfidence, annotation sparsity, ontology mismatch,
  dense relation noise, and uncertain cases.
- Therefore H002 must remain bidirectional and audit-aware.

## Claim Boundary

Allowed current claim:

```text
RGA provides a train-only framework for separating semantic confidence,
geometric satisfiability, coverage, uncertainty, and label/audit evidence at
relation-edge level.
```

Allowed current diagnostic claim:

```text
On the Open3DSG train pilot, RGA exposes both high-semantic/low-geometry and
low-semantic/high-geometry states. The low-semantic/high-geometry state is large
but requires audit because it mixes true underconfidence, annotation sparsity,
ontology mismatch, and dense relation noise.
```

Blocked claims:

- RGA itself improves relation prediction.
- RGA-LH rows are automatically valid missing positives.
- working labels are paper-locked human annotations.
- `p_geom_valid` is full relation reliability.
- the factorized posterior outperforms baselines.
- held-out validation/test conclusions.

## Next Step

The next H002 step remains:

```text
26_factor_dataset.md
```

Goal:

- materialize deployable feature rows from `match_rows.jsonl`.
- join `factor_targets.jsonl` to audit rows.
- create strict/weak train-only smoke-fitting inputs.
- preserve the rule that label/audit evidence is target/evaluation evidence, not
  deployment-time input.
