# H002 RGA Framework

Last updated: 2026-06-25 KST

## Purpose

`RGA(Relation-Geometric Agreement)`는 H002의 main method가 아니라, 새 method인
`Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations`를
검증하기 위한 diagnostic/evaluation framework다.

RGA의 핵심 질문은 다음이다.

```text
Does source confidence agree with predicate-geometry compatibility and
available geometry evidence for the subject-object pair?
```

RGA는 relation edge를 다음 축으로 배치한다.

```text
semantic-content axis
source-confidence axis
geometry-evidence axis
compatibility axis
observability axis
label/audit axis, if available
```

RGA는 `p_geom_valid`를 relation reliability로 이름만 바꾼 것이 아니다. `p_geom_valid`는
geometry-only baseline 또는 rule-based teacher 중 하나이며, final decision은
`T_e`, `Z_e`, `G_e`, `C_e`, `Q_e`를 분리한 뒤 `p_obs`와 `p_rel`로 계산한다.

## Current H002 Factorization

```text
T_e = semantic content
Z_e = source confidence
G_e = predicate-independent geometry evidence
C_e = compatibility(T_e, G_e)
Q_e = evidence quality / observability
p_obs = P(evidence is sufficient to decide)
p_rel = P(relation is reliable | evidence is observable)
```

기존 H002의 `coverage`와 `uncertainty`는 이제 `Q_e` 안에서 함께 다룬다.

```text
coverage + uncertainty + missing evidence + asset completeness
  -> evidence quality / observability
```

## Unit Of Analysis

기본 단위는 aggregate metric이 아니라 identity-preserving relation candidate row다.

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
geometry_evidence_fields
geometry_status, if rule-derived status exists
p_geom_valid, if available
observability_state
label_match_status or audit label, if available
provenance
```

## Semantic-Content Axis

Semantic-content axis는 어떤 relation이 주장되는지를 나타낸다.

Examples:

```text
predicate text or label
relation family
subject/object class
class text embedding
ontology group
```

이 축은 `T_e`에 해당한다. Source score, rank, source id는 여기에 넣지 않는다.

## Source-Confidence Axis

Source-confidence axis는 기존 relation source가 해당 edge를 얼마나 강하게 믿는지를 나타낸다.

Examples:

```text
source relation score
semantic rank
source id
source-specific score calibration metadata
```

이 축은 `Z_e`에 해당한다. `Z_e`는 final `p_rel`에는 들어갈 수 있지만, compatibility
`C_e = compatibility(T_e, G_e)`에는 들어가면 안 된다.

## Geometry Evidence Axis

Geometry evidence axis는 predicate를 모르는 상태에서도 계산 가능한 object-pair geometry
정보를 기록한다.

Examples:

```text
distance
height difference
XY separation
3D overlap
projected overlap
contact gap
support area proxy
containment ratio
surface gap
normal alignment
mesh completeness
point coverage
```

중요 원칙:

- geometry evidence encoder에는 predicate text, source score, rank를 넣지 않는다.
- relation-specific 해석은 compatibility head에서 수행한다.
- H001 `p_geom_valid`는 geometry-only baseline 또는 teacher signal로 사용할 수 있지만,
  그 자체가 final reliability는 아니다.
- rule-derived `geometry_status`는 model input보다 RGA bucket, teacher, baseline, audit axis로
  우선 사용한다.

## Compatibility Axis

Compatibility axis는 semantic content와 geometry evidence가 서로 맞는지 나타낸다.

```text
C_e = compatibility(T_e, G_e)
```

금지:

```text
C_e must not use Z_e.
```

예:

```text
close by + small boundary distance -> high compatibility
higher than + positive vertical margin -> high compatibility
standing on + contact/support evidence -> high compatibility
attached to + only far OBB distance -> low compatibility
hanging on + attachment-like contact plus vertical support -> high compatibility
```

Compatibility는 다음 counterfactual controls로 검증한다.

```text
wrong-pair geometry
shuffled geometry
predicate flip
subject/object swap
source-score shuffle
same-scene negative
same-family negative
same-rank-band negative
same-coverage negative
contact removal
vertical order flip
```

## Observability Axis

Observability axis는 evidence가 충분한지와 abstain이 필요한지를 기록한다.

Typical states:

```text
covered_checkable
limited_view_evaluable
low_point_coverage
mesh_incomplete
same_frame_visible
individual_view_plus_mesh
evidence_conflict
unsupported_family
missing_geometry
```

Observability가 필요한 이유는 다음을 구분하기 위해서다.

```text
geometry contradicts relation
vs
geometry evidence is insufficient
```

`Q_e`는 relation의 true/false를 직접 결정하지 않고 `p_obs`를 통해 selective decision을
조절한다.

## RGA Buckets

RGA bucket은 source-confidence axis와 geometry/compatibility axis의 진단용 조합이다.

| Bucket | Source Confidence | Geometry/Compatibility | Interpretation |
| --- | --- | --- | --- |
| `RGA-HH` | high | supports / compatible | source confidence and evidence agree |
| `RGA-HL` | high | contradicts / incompatible | source overconfidence or unsafe relation |
| `RGA-HU` | high | uncertain/missing | high source confidence but insufficient evidence |
| `RGA-LH` | low | supports / compatible | under-ranked relation, missing annotation, or dense relation noise |
| `RGA-LL` | low | contradicts / incompatible | low source confidence and weak geometry evidence |
| `RGA-LU` | low | uncertain/missing | low source confidence with insufficient evidence |

When label/audit evidence exists, RGA also records:

| Bucket | Label/Audit | Geometry/Compatibility | Interpretation |
| --- | --- | --- | --- |
| `GT+ / G+` | official or audit positive | supports | label and geometry agree |
| `GT+ / G-` | official or audit positive | contradicts | label exists but geometry evidence disagrees |
| `GT- / G+` | no GT or audit negative | supports | possible missing annotation or source underconfidence |
| `GT- / G-` | no GT or audit negative | contradicts | likely unreliable relation |
| `* / GU` | any label state | uncertain/missing | observability-limited case |

## Metrics

All metrics must report numerator and denominator.

```text
RGA-HL@K = high-source rows with geometry contradiction / high-source covered rows
RGA-HH@K = high-source rows with geometry support / high-source covered rows
RGA-HU@K = high-source rows with uncertain or missing evidence / high-source candidate rows
RGA-LH-tail = low-source rows with geometry support / low-source covered rows
RGA-coverage = rows with usable geometry evidence / candidate rows
```

Compatibility-specific metrics:

```text
counterfactual_drop = C(real pair) - C(counterfactual pair)
predicate_flip_drop = C(original predicate) - C(flipped predicate)
wrong_pair_AUROC
shuffled_geometry_AUROC
same_family_hard_negative_AUPRC
source_shuffle_invariance
```

Reliability/selective metrics:

```text
Recall@K on official GT
Violation@K from geometry evidence
ECE / Brier / AUPRC where valid targets exist
selective risk under abstain
p_obs calibration on limited/complete evidence subsets
accept/reject/abstain confusion on audit subset
```

## Method Boundary

RGA should not be used as a hidden shortcut target.

Blocked model inputs:

```text
target construction key
planned proxy role
machine hint
hidden rank bucket used only for sampling
hidden GT-match field
previous audit label
reviewer packet id
```

Allowed model inputs:

```text
T_e semantic content
Z_e source confidence
G_e geometry-only evidence
Q_e observability evidence
```

Allowed audit/control fields:

```text
rank band
predicate family
endpoint pair
object family
scan id
RGA bucket
GT match axis
```

## Current Role In H002

RGA now serves four roles:

1. diagnose source-confidence and geometry/compatibility mismatch;
2. build relation-family failure taxonomy;
3. evaluate whether compatibility learning uses geometry evidence rather than source/predicate shortcuts;
4. report reliability/violation/coverage tradeoffs in a reviewer-readable format.

It is no longer the next standalone contribution. The next method work after the completed
method/schema/counterfactual contracts is `prototype_dataset_contract_v1`.
