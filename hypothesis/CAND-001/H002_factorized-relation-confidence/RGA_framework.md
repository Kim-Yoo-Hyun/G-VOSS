# H002 RGA Framework

Last updated: 2026-06-22 KST

## Purpose

`RGA(Relation-Geometric Agreement)`는 3D Scene Graph relation edge의 reliability를
단일 confidence로 보지 않고, semantic evidence와 geometry evidence가 서로 일치하는지
분해해서 측정하는 H002의 benchmark/diagnostic framework다.

핵심 질문:

```text
Does semantic plausibility agree with geometric satisfiability?
```

RGA는 `p_geom_valid`를 이름만 바꾼 score가 아니다. RGA는 relation candidate를
semantic axis, geometry axis, label/audit axis, coverage axis, uncertainty axis 위에
배치하고, 기존 label-recall metric이나 geometry-only violation metric이 숨기는 mismatch
state를 드러낸다.

## Core Separation

H002의 기본 분리는 다음이다.

```text
semantic score != geometry validity != relation reliability
```

Relation edge `e = (subject, predicate, object)`에 대해 RGA는 다음 state를 기록한다.

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

이 프레임워크에서 중요한 mismatch는 양방향이다.

| Case | Meaning |
| --- | --- |
| high semantic + high geometry | relation source가 높게 본 edge를 geometry도 지지 |
| high semantic + low geometry | semantic overconfidence 또는 unsafe relation |
| low semantic + high geometry | semantic underconfidence, missed relation, annotation sparsity 후보 |
| high semantic + uncertain geometry | source score는 높지만 physical status가 애매함 |
| unsupported or missing geometry | 현재 verifier/asset coverage 밖의 relation |

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
label_match_status or audit label, if available
coverage_state
uncertainty_state
provenance
```

## Evidence Axes

### Semantic Axis

Semantic axis는 relation source가 해당 edge를 얼마나 그럴듯하게 보는지 나타낸다.
서로 다른 source의 raw score calibration이 다를 수 있으므로, H002에서는 rank band와
normalized rank score를 함께 기록한다.

```text
semantic_high_K(e) = semantic_rank_in_subgraph(e) <= K
semantic_low_K(e)  = semantic_rank_in_subgraph(e) > K
```

### Geometry Axis

Geometry axis는 관측된 3D evidence가 해당 relation predicate를 지지하는지 본다.
현재 H002는 H001에서 동결한 relation-family geometry witness를 geometry-only evidence로
재사용한다.

```text
geometry_status in {satisfied, unsatisfied, uncertain, unsupported, missing}
```

중요한 규칙:

```text
RGA bucket은 deterministic geometry_status로 결정한다.
p_geom_valid는 geometry-only continuous evidence로만 사용한다.
```

즉 `p_geom_valid`는 H002의 `geometry validity`에 해당하지만, relation reliability의
최종 score는 아니다.

### Label/Audit Axis

Label axis는 GT relation 또는 audit label과의 관계를 기록한다. 이 값은 deployable
posterior input이 아니라 supervision, audit, stratification 용도다.

Typical states:

```text
exact_match
family_match
pair_has_other_predicate
no_gt_for_pair
accept_reliable
reject_unreliable
abstain_uncertain
```

### Coverage Axis

Coverage axis는 geometry verifier나 evidence packet이 해당 row를 평가할 수 있었는지
기록한다.

```text
covered_checkable
covered_checkable_uncertain
unsupported_family
missing_geometry
limited_view_evaluable
asset_incomplete
```

Coverage가 필요한 이유는 unsupported/missing relation을 invalid geometry로 오해하지
않기 위해서다.

### Uncertainty Axis

Uncertainty axis는 evidence가 부족하거나 애매한 경우를 hard accept/reject로 강제하지
않는다.

Examples:

```text
geometry_status = uncertain
low point or view coverage
ambiguous relation-specific residual
annotation sparsity
ontology mismatch
```

## RGA Buckets

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
| `RGA-TP-GS` | exact/audit positive | satisfied | label-correct and geometry-supported |
| `RGA-TP-GU` | exact/audit positive | unsatisfied | label-correct but geometry-contradicted |
| `RGA-FP-GS` | no exact label or audit negative | satisfied | no label credit but geometry-supported |
| `RGA-FP-GU` | no exact label or audit negative | unsatisfied | no label credit and geometry-contradicted |
| `RGA-*-GC` | any label state | uncertain/unsupported/missing | coverage or uncertainty case |

## Metrics

All RGA metrics report numerator and denominator. Unsupported/missing rows are not silently mixed into invalid rows.

```text
RGA-HL@K = high-semantic rows with geometry unsatisfied / high-semantic covered rows
RGA-valid@K = high-semantic rows with geometry satisfied / high-semantic covered rows
RGA-uncertain@K = high-semantic rows with geometry uncertain / high-semantic covered rows
RGA-coverage@K = high-semantic covered rows / high-semantic candidate rows
RGA-LH-tail@K = low-semantic rows with geometry satisfied / low-semantic covered rows
```

Continuous disagreement:

```text
overconfidence_gap = max(0, semantic_score_norm - p_geom_valid)
underconfidence_gap = max(0, p_geom_valid - semantic_score_norm)
```

This continuous signal is useful for audit ranking and later posterior features, but it does not replace deterministic RGA buckets.

## Posterior Boundary

RGA defines the problem and target-quality gates. It does not by itself prove a
posterior method claim.

Target posterior form:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

Where:

```text
S_e = semantic evidence
G_e = geometry evidence
C_e = coverage evidence
U_e = uncertainty evidence
```

Posterior smoke is allowed only when relation reliability target passes
target-independence checks.

Blocked inputs:

```text
rank_band_hidden as model input
machine_hint_hidden as model input
target construction keys as model input
prior label fields as model input
```

These fields can be used only for sampling control or audit.

## Current Status

```text
current_gate = v13 proximity LH scene/geometry label fill completed
status = h002_reliability_target_v13_proximity_lh_scene_geometry_label_filled_codex_proxy_visible_only
posterior_smoke_allowed = false
validation_or_test_used = false
next = reliability_target_v13_proximity_lh_scene_geometry_label_ingestion
```

Current finding:

```text
eligible_pairs = 9984
eligible_rows = 19968
strict_v9_exact_pair_feasible = false
rank_band -> predicate majority accuracy = 0.9229
baseline = 0.4976
proximity_total_rows = 185346
proximity_RGA_HL = 0
proximity_RGA_LH = 171324
proximity_strict_LH_pool = 50966
proximity_v13_block_candidate_groups = 1510
proximity_v13_strong_block_candidate_groups = 778
proximity_v13_selected_rows = 240
proximity_v13_selected_blocks = 30
proximity_v13_label_fill_accept = 39
proximity_v13_label_fill_reject = 137
proximity_v13_label_fill_abstain = 64
proximity_v13_label_fill_binary_usable = 176
```

Interpretation:

- row count is sufficient.
- exact endpoint-pair contrast exists.
- but predicate and source rank are structurally entangled under the exact-pair design.
- therefore current exact-pair v9 must not become the primary posterior target.
- v10/v11 show that `close by` / proximity is feasible only as an LH-only target-repair branch under the current RGA queues, not as a bidirectional HL/LH target.
- v12 selects that LH-only branch while explicitly keeping the RGA framework bidirectional.
- v13 prepares a 240-row visible label sheet with hidden audit metadata separated; this is label-ready but not yet target-valid.
- v14 fills visible-only proxy labels (`36/71/133` accept/reject/abstain); this is still not target-valid until hidden shortcut audit passes.
- v15 ingests the target (`240` multiclass, `107` binary) and quick probes show strong object-pair shortcut risk; posterior remains blocked.
- v16 confirms no strict/diagnostic controlled slice; object-pair mixed contrast is `0`, so the visible-only proximity target is diagnostic-only unless repaired.
- v17 freezes the visible-only branch as diagnostic-only negative evidence and selects scene/geometry-aware target repair as the next route.
- v18 confirms scene/geometry-aware repair capacity: `50,966` train-only repair-pool rows, `1,510` block candidate groups, and `778` strong block candidate groups.
- v19 creates a `240`-row scene/geometry-aware label sheet from `30` visible object-pair blocks with visible leakage `0`; posterior remains blocked until labels and target-independence audit pass.
- v20 fills that sheet with visible-only scene/geometry proxy labels: `39` accept, `137` reject, `64` abstain, `176` binary usable rows. The fill is valid as target material but not posterior-ready because positive mass is below the earlier minimum-per-class gate and shortcut independence is still untested.

## Current Relation Scope

Core target construction currently focuses on:

```text
support_contact: standing on, lying on
relative_vertical: higher than, lower than
```

Active empirical branch:

```text
proximity: close by, scene/geometry-aware LH label ingestion
```

Deferred expansion:

```text
attachment_deferred: attached to, hanging on, connected to
relative_horizontal: left, right, front, behind
```

`close by` is important for generality, but current evidence supports only a
low-semantic/high-geometry branch. It should not be mixed into the current core target
or used for posterior smoke until the repaired target passes target-independence audit.

## File Ownership

```text
README.md = H002 folder map and current status
summary_branch_v2.md = research framing, claim boundary, latest summary, and v1-v20 overview
RGA_framework.md = RGA definitions, axes, buckets, metrics, gates
feasibility_check.md = posterior combiner and multi-view feasibility notes
stages/ = v1-v20 stage-specific progress, problems, and transition rationale
artifacts/ = raw per-stage outputs
```
