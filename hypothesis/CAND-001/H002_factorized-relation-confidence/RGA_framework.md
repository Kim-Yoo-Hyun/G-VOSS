# H002 RGA Framework

Last updated: 2026-06-21

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

### Current Full-Train Extension

Documents:

```text
53_full_train_scope_contract.md
54_full_train_source_runner.md
55_full_train_runtime_stage.md
56_full_train_raw_dump.md
57_full_train_adapter_export.md
58_full_train_geometry_join.md
59_full_train_rga_rows.md
60_full_train_controlled_mining.md
84_full_train_independent_support_vertical_audit_packet.md
85_full_train_independent_support_vertical_label_readiness.md
86_full_train_independent_support_vertical_label_fill.md
87_full_train_independent_support_vertical_label_ingestion.md
88_full_train_independent_support_vertical_target_independence_audit.md
89_full_train_independent_support_vertical_label_policy_revision.md
90_full_train_independent_support_vertical_v2_label_readiness.md
91_full_train_independent_support_vertical_v2_label_fill.md
92_full_train_independent_support_vertical_v2_label_ingestion.md
93_full_train_independent_support_vertical_v2_target_independence_audit.md
94_full_train_independent_support_vertical_v2_target_path_decision.md
95_full_train_independent_support_vertical_v2_independent_label_fill.md
96_full_train_independent_support_vertical_v2_independent_label_ingestion.md
97_full_train_independent_support_vertical_v2_independent_target_independence_audit.md
98_full_train_independent_support_vertical_v2_human_label_path.md
99_full_train_independent_support_vertical_v2_human_label_fill.md
100_full_train_independent_support_vertical_v2_human_label_ingestion.md
101_full_train_independent_support_vertical_v2_human_target_independence_audit.md
102_full_train_independent_support_vertical_v2_external_review_protocol.md
103_full_train_independent_support_vertical_v2_external_review_fill.md
104_full_train_independent_support_vertical_v2_external_review_ingestion.md
105_full_train_independent_support_vertical_v2_external_review_target_independence_audit.md
106_full_train_independent_support_vertical_v2_true_user_review_path.md
107_full_train_independent_support_vertical_v2_true_user_review_fill.md
108_full_train_independent_support_vertical_v2_true_user_review_ingestion.md
109_full_train_independent_support_vertical_v2_true_user_review_target_independence_audit.md
110_full_train_independent_support_vertical_v2_true_user_review_target_path_decision.md
111_full_train_independent_support_vertical_v2_user_submitted_review_ingestion.md
112_full_train_independent_support_vertical_v2_user_submitted_review_target_independence_audit.md
113_full_train_independent_support_vertical_v2_reviewer_provenance_decision.md
114_full_train_independent_support_vertical_v2_user_confirmed_review_ingestion.md
115_full_train_independent_support_vertical_v2_user_confirmed_review_target_independence_audit.md
116_full_train_independent_support_vertical_v2_sampling_protocol_decision.md
117_full_train_independent_support_vertical_v2_revised_sampling_fill.md
118_full_train_independent_support_vertical_v2_revised_sampling_ingestion.md
119_full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit.md
120_full_train_independent_support_vertical_v2_all_label_ready_expansion.md
121_full_train_independent_support_vertical_v2_revised_sampling_source_feature_join.md
122_full_train_independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke.md
123_full_train_independent_support_vertical_v2_revised_sampling_controlled_error_analysis.md
124_full_train_independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan.md
125_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2.md
126_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke.md
127_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis.md
128_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan.md
129_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke.md
130_full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis.md
131_endpoint_controlled_resampling_plan.md
132_endpoint_controlled_candidate_mining.md
133_endpoint_controlled_asset_packets.md
134_endpoint_controlled_label_fill.md
135_endpoint_controlled_label_ingestion.md
136_endpoint_controlled_target_independence_audit.md
137_endpoint_controlled_target_path_decision.md
138_reliability_target_v3_positive_anchor_plan.md
139_reliability_target_v3_label_fill.md
140_reliability_target_v3_label_ingestion.md
141_reliability_target_v3_target_independence_audit.md
142_reliability_target_v3_path_decision.md
143_reliability_target_v3_object_endpoint_controlled_plan.md
144_reliability_target_v3_object_endpoint_candidate_mining.md
145_reliability_target_v3_object_endpoint_label_fill.md
146_reliability_target_v3_object_endpoint_label_ingestion.md
147_reliability_target_v3_object_endpoint_target_independence_audit.md
148_reliability_target_v3_object_endpoint_path_decision.md
149_reliability_target_v3_informative_anchor_plan.md
150_reliability_target_v3_informative_anchor_candidate_mining.md
151_reliability_target_v3_informative_anchor_asset_packets.md
152_reliability_target_v3_informative_anchor_label_fill.md
153_reliability_target_v3_informative_anchor_label_ingestion.md
```

Current full-train status:

| Stage | Status |
| --- | --- |
| source contract | `ready` |
| raw dump | `ready` |
| adapter export | `ready` |
| geometry join | `ready` |
| RGA rows | `ready` |
| controlled candidate mining | `ready_for_controlled_audit` |
| controlled label readiness | `not_ready_no_filled_labels` |
| controlled codex label fill | `ready_for_train_only_full_posterior_smoke` |
| controlled posterior smoke | `full_train_posterior_proxy_blocked` |
| selected support/vertical audit packet | `ready` |
| selected support/vertical v1 label policy | `blocked_by_target_carryover` |
| selected support/vertical v2 label readiness | `ready_for_fill` |
| selected support/vertical v2 label fill | `filled_no_direct_target` |
| selected support/vertical v2 label ingestion | `ingested_with_target_risk` |
| selected support/vertical v2 target independence audit | `strict_blocked_construction_slice_available` |
| selected support/vertical v2 target path decision | `collect_independent_labels` |
| selected support/vertical v2 independent label fill | `filled_codex_independent_visible_only` |
| selected support/vertical v2 independent label ingestion | `ingested_with_basic_probe_risk` |
| selected support/vertical v2 independent target independence audit | `strict_blocked_construction_slice_available` |
| selected support/vertical v2 human label path | `collect_human_confirmed_labels` |
| selected support/vertical v2 human label fill | `filled_codex_proxy_user_review_pending` |
| selected support/vertical v2 human label ingestion | `ingested_with_basic_probe_risk` |
| selected support/vertical v2 human target independence audit | `strict_blocked_construction_slice_available` |
| selected support/vertical v2 external review protocol | `ready` |
| selected support/vertical v2 external review fill | `filled_codex_proxy_user_requested` |
| selected support/vertical v2 external review ingestion | `ingested_with_basic_probe_risk` |
| selected support/vertical v2 external review target independence audit | `strict_blocked_construction_slice_available` |
| selected support/vertical v2 true user review path | `ready` |
| selected support/vertical v2 true user review fill | `filled_codex_proxy_pending_confirmation` |
| selected support/vertical v2 true user review ingestion | `ingested_with_basic_probe_risk` |
| selected support/vertical v2 true user review target independence audit | `strict_blocked_construction_slice_available` |
| selected support/vertical v2 true user review target path decision | `collect_real_independent_labels` |
| selected support/vertical v2 user-submitted review ingestion | `ingested_with_basic_probe_risk` |
| selected support/vertical v2 user-submitted review target independence audit | `blocked_no_controlled_slice` |
| selected support/vertical v2 reviewer provenance decision | `collect_external_full127_labels` |
| selected support/vertical v2 user-confirmed review ingestion | `ingested_with_basic_probe_risk` |
| selected support/vertical v2 user-confirmed review target independence audit | `blocked_no_controlled_slice` |
| selected support/vertical v2 sampling protocol decision | `revise_sampling_first_priority160_ready` |
| selected support/vertical v2 revised sampling fill | `filled_user_confirmed` |
| selected support/vertical v2 revised sampling ingestion | `ingested_with_basic_probe_risk` |
| selected support/vertical v2 revised sampling target independence audit | `blocked_no_controlled_slice` |
| selected support/vertical v2 all-label-ready expansion | `relation_strict_slice_ready` |
| selected support/vertical v2 revised sampling source feature join | `posterior_ready` |
| selected support/vertical v2 revised sampling controlled posterior smoke | `no_strong_signal` |
| selected support/vertical v2 revised sampling controlled error analysis | `feature_family_misalignment` |
| selected support/vertical v2 revised sampling factor definition repair plan | `ready` |
| selected support/vertical v2 revised sampling raw witness feature join v2 | `ready` |
| selected support/vertical v2 revised sampling raw witness v2 posterior smoke | `positive_smoke` |
| selected support/vertical v2 revised sampling raw witness v2 error analysis | `support_driven_linear_gap` |
| selected support/vertical v2 revised sampling raw witness v2 combiner repair plan | `ready` |
| selected support/vertical v2 revised sampling raw witness v2 combiner smoke | `no_new_primary_endpoint_shortcut_risk` |
| selected support/vertical v2 revised sampling raw witness v2 combiner error analysis | `endpoint_control_needed` |
| selected support/vertical v2 endpoint-controlled resampling plan | `needs_label_expansion` |
| selected support/vertical v2 endpoint-controlled candidate mining | `ready_needs_asset_packets` |
| selected support/vertical v2 endpoint-controlled asset packets | `ready` |
| selected support/vertical v2 endpoint-controlled label fill | `ready_for_ingestion_positive_sparse` |
| selected support/vertical v2 endpoint-controlled label ingestion | `positive_sparse_target_audit_needed` |
| selected support/vertical v2 endpoint-controlled target independence audit | `blocked_positive_sparse` |
| selected support/vertical v2 endpoint-controlled target path decision | `revise_target_v3_positive_anchor_sampling` |
| reliability target v3 positive-anchor plan | `ready` |
| reliability target v3 label fill | `filled_codex_proxy_user_requested` |
| reliability target v3 label ingestion | `ingested_with_probe_risk` |
| reliability target v3 target independence audit | `blocked_no_controlled_slice` |
| reliability target v3 path decision | `object_endpoint_controlled_sampling_first` |
| reliability target v3 object/endpoint-controlled plan | `ready_broader_mining_required` |
| reliability target v3 object/endpoint candidate mining | `ready_with_selection_deficit` |
| reliability target v3 object/endpoint label fill | `filled_codex_proxy_user_requested` |
| reliability target v3 object/endpoint label ingestion | `positive_sparse_with_probe_risk` |
| reliability target v3 object/endpoint target independence audit | `reliability_blocked_geometry_support_available` |
| reliability target v3 object/endpoint path decision | `informative_anchor_sampling` |
| reliability target v3 informative anchor plan | `ready_with_asset_requests` |
| reliability target v3 informative anchor candidate mining | `ready_needs_asset_packets` |
| reliability target v3 informative anchor asset packets | `ready` |
| reliability target v3 informative anchor label fill | `filled_codex_proxy_user_requested` |
| reliability target v3 informative anchor label ingestion | `ingested_with_probe_risk` |
| reliability target v3 informative anchor target independence audit | `blocked_no_controlled_slice` |
| reliability target v3 informative anchor path decision | `matched_contrast_v4` |
| reliability target v4 matched contrast plan | `ready_with_asset_requests` |
| reliability target v4 matched contrast candidate mining | `ready_needs_asset_packets` |
| reliability target v4 matched contrast asset packets | `partial_limited_endpoint_views` |
| reliability target v4 matched contrast asset packet gap audit | `ready_for_label_readiness` |
| reliability target v4 matched contrast label readiness | `ready_for_label_fill` |
| reliability target v4 matched contrast label fill | `filled_codex_proxy_user_requested` |
| reliability target v4 matched contrast label ingestion | `ingested_with_probe_risk` |

Full-train RGA rows:

```text
4,818,996 prediction rows
```

Full-train mismatch queues:

| Queue | Rows |
| --- | ---: |
| `RGA-HL` | 1,828 |
| `RGA-LH` | 455,598 |

Controlled mining output:

| Item | Count |
| --- | ---: |
| candidate rows | 360 |
| unique scans | 92 |
| `HL` candidates | 83 |
| `LH` candidates | 277 |

Interpretation:

```text
Full train confirms that the main available diagnostic mass is not only
high-semantic/low-geometry overconfidence. Low-semantic/high-geometry candidates
are much larger, so H002 remains a bidirectional RGA and audit framework.
```

Boundary:

```text
The full-train candidate roles are not labels. Posterior training still requires
controlled label readiness.
```

Initial 360-row label readiness:

```text
candidate sheet rows = 360
started review rows = 0
usable binary targets = 0
binary target files = empty
```

Current bootstrap label readiness:

```text
label source = codex_ver_full_train_policy_bootstrap
completed review rows = 360
usable binary targets = 173
positive rows = 74
negative rows = 99
status = ready_for_train_only_full_posterior_smoke
```

Boundary:

```text
codex_ver_full_train labels are not human-confirmed and do not support a
paper-level posterior claim. They only unlock train-only posterior smoke and
shortcut/proxy controls.
```

Current v3 label readiness:

```text
label sheet rows = 160
sampling buckets = 4 x 40
label fields filled = yes
labels ingested = yes
filled_by = codex_proxy_user_requested_visible_heuristic
reliable = 32
unreliable_geometry = 21
unreliable_trivial = 57
unreliable_ontology = 0
uncertain = 50
validation errors = 0
relation reliability binary target = 110 rows, 32 positive, 78 negative
geometry support binary target = 113 rows, 92 positive, 21 negative
relation usefulness binary target = 113 rows, 34 positive, 79 negative
target-independence probe = hidden/visible shortcut risk
target-independence audit = blocked_no_controlled_slice
strict controlled slice = none
diagnostic controlled slice = none
path decision = object_endpoint_controlled_sampling_first
object/endpoint plan = ready_broader_mining_required
object/endpoint plan candidate rows = 302
strict subject/object/family eligible rows = 73
object/endpoint mined label sheet rows = 130
object/endpoint mined residual rows = 28
object/endpoint filled reliable = 8
object/endpoint filled unreliable_geometry = 26
object/endpoint filled unreliable_trivial = 73
object/endpoint filled uncertain = 23
object/endpoint relation reliability target = 107 rows, 8 positive, 99 negative
object/endpoint geometry support target = 111 rows, 85 positive, 26 negative
object/endpoint usefulness target = 111 rows, 10 positive, 101 negative
object/endpoint target-independence audit = reliability_blocked_geometry_support_available
object/endpoint reliability status = blocked_positive_sparse
object/endpoint geometry-support status = blocked_no_controlled_slice
object/endpoint usefulness status = blocked_positive_sparse
object/endpoint path decision = informative_anchor_sampling
selected next path = revise_v3_informative_positive_anchor_sampling
informative anchor plan = ready_with_asset_requests
informative anchor selected seeds = 160 rows, 126 packet-ready, 34 asset-needed
informative anchor candidate mining = ready_needs_asset_packets
informative anchor full label sheet = 160 rows
informative anchor packet-ready fallback sheet = 126 rows
informative anchor asset-needed rows = 34
informative anchor asset packets = ready
informative anchor generated packets = 34
informative anchor full packet-ready label sheet = 160 rows
informative anchor label fill = filled_codex_proxy_user_requested
informative anchor reliable = 35
informative anchor unreliable_geometry = 13
informative anchor unreliable_trivial = 34
informative anchor uncertain = 78
informative anchor relation reliability target = 82 rows, 35 positive, 47 negative
informative anchor geometry support target = 85 rows, 72 positive, 13 negative
informative anchor usefulness target = 85 rows, 37 positive, 48 negative
informative anchor target-independence probe = hidden/visible shortcut risk
informative anchor target-independence audit = blocked_no_controlled_slice
informative anchor reliability status = blocked_no_controlled_slice
informative anchor geometry-support status = blocked_positive_sparse
informative anchor usefulness status = blocked_no_controlled_slice
informative anchor main risk = anchor/object/endpoint/rank shortcut
informative anchor path decision = matched_contrast_v4
selected next path = revise_to_matched_contrast_reliability_target_v4
v4 matched contrast plan = ready_with_asset_requests
v4 selected matching level = predicate_object_rank_controlled
v4 selected rows = 160
v4 selected pairs = 80
v4 packet-ready rows = 5
v4 asset-needed rows = 155
v4 rank policy = post_selection_quota_and_audit_control
v4 matched contrast candidate mining = ready_needs_asset_packets
v4 full label sheet = 160 rows
v4 packet-ready fallback sheet = 5 rows
v4 asset request rows = 155
v4 asset packets = partial_limited_endpoint_views
v4 generated packets = 155
v4 generated ready packets = 135
v4 generated partial packets = 20
v4 existing ready packets = 5
v4 ready label rows = 140
v4 partial label rows = 20
v4 partial support_contact rows = 13
v4 partial relative_vertical rows = 7
v4 partial rows missing subject crop = 12
v4 partial rows missing object crop = 8
v4 asset packet gap audit = ready_for_label_readiness
v4 label-ready rows after gap audit = 158
v4 label-ready pairs after gap audit = 79
v4 excluded pairs after gap audit = 1
v4 limited-view rows kept = 19
v4 role balance after gap audit = positive_proxy 79, negative_proxy 79
v4 label-surface leakage hits = 0
v4 packet path errors = 0
v4 input validation errors = 0
v4 label readiness = ready_for_label_fill
v4 label-ready rows = 158
v4 label-ready pairs = 79
v4 ready rows = 139
v4 limited-view rows = 19
v4 ready family counts = support_contact 90, relative_vertical 68
v4 role balance after readiness = positive_proxy 79, negative_proxy 79
v4 expected columns match = true
v4 label-readiness input validation errors = 0
v4 label-readiness sheet validation errors = 0
v4 label-readiness packet path errors = 0
v4 label-readiness leakage hits = 0
v4 label fill = filled_codex_proxy_user_requested
v4 filled rows = 158
v4 filled reliable = 23
v4 filled unreliable = 24
v4 filled uncertain = 111
v4 binary target rows = 47
v4 binary positive rows = 23
v4 binary negative rows = 24
v4 label fill input validation errors = 0
v4 label fill validation errors = 0
v4 matched role post-label distribution = negative_proxy 11/14/54, positive_proxy 12/10/57
v4 direct reliable/unreliable contrast pairs = 1
v4 label ingestion = ingested_with_probe_risk
v4 relation reliability target = 47 rows, 23 positive, 24 negative
v4 geometry support target = 47 rows, 30 positive, 17 negative
v4 relation usefulness target = 50 rows, 25 positive, 25 negative
v4 relation reliability probe = target_independence_risk_hidden_metadata_correlated
v4 relation reliability probe hidden risks = 3
v4 relation reliability probe visible risks = 2
v4 ingestion errors = 0
label-surface leakage hits = 0
packet path errors = 0
validation errors = 0
posterior allowed = no
next = reliability_target_v4_matched_contrast_target_independence_audit
```

## Reliability Target V3 Informative Anchor Target Independence Audit

2026-06-20 KST에 `reliability_target_v3_informative_anchor_target_independence_audit`을
진행했다. 이 단계는 informative-anchor v3 target이 posterior smoke로 넘어갈 만큼
독립적인지 확인하는 gate다. Posterior는 실행하지 않았다.

Result:

```text
status = h002_reliability_target_v3_informative_anchor_target_independence_audit_blocked
relation reliability = 82 rows, 35 positive, 47 negative, blocked_no_controlled_slice
geometry support = 85 rows, 72 positive, 13 negative, blocked_positive_sparse
relation usefulness = 85 rows, 37 positive, 48 negative, blocked_no_controlled_slice
validation errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v3_informative_anchor_path_decision
```

Interpretation:

- Informative-anchor sampling solved the earlier relation reliability positive-sparsity issue.
- It did not solve target independence.
- The main relation reliability target is still explained too strongly by
  `anchor_category_hidden`, `endpoint_flag_pattern_hidden`, subject/object family cells,
  object labels, subject labels, and `rank_band_hidden`.
- Family-balanced and predicate-balanced slices keep enough rows, but they still carry
  anchor/object/endpoint shortcut risks.
- Anchor-matched or endpoint-matched slices collapse to tiny balanced sets such as
  `6` rows or `4` rows, so they are not posterior-ready.
- Therefore the blocker is target construction, not posterior capacity.

## Reliability Target V3 Informative Anchor Path Decision

2026-06-20 KST에 `reliability_target_v3_informative_anchor_path_decision`을 진행했다.
이 단계는 informative-anchor v3 audit 이후 posterior를 진행할지, target construction을
바꿀지 결정하는 gate다. Posterior는 실행하지 않았다.

Result:

```text
status = h002_reliability_target_v3_informative_anchor_path_decision_matched_contrast_v4
selected_path = revise_to_matched_contrast_reliability_target_v4
relation reliability = 82 rows, 35 positive, 47 negative, blocked_no_controlled_slice
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v4_matched_contrast_plan
```

Decision:

- posterior smoke는 진행하지 않는다.
- full informative-anchor target도 posterior target으로 쓰지 않는다.
- geometry-support를 main reliability target으로 바꾸지 않는다.
- 같은 informative-anchor 방식으로 row만 더 모으지 않는다.
- 다음 단계는 `matched_contrast_reliability_target_v4`다.

Rationale:

- v3는 positive-sparsity는 해결했지만 target independence는 해결하지 못했다.
- `anchor_category_hidden`, endpoint/object structure, object labels, rank band가 target을
  너무 강하게 설명한다.
- 따라서 v4는 positive-like bucket과 negative-like bucket을 따로 뽑는 방식이 아니라,
  같은 predicate / endpoint-object / rank stratum 안에서 reliable edge와 unreliable edge를
  contrast해야 한다.
- v4도 실패하면 H002를 posterior method claim으로 강제하지 않고 RGA diagnostic/decomposition
  framework로 정리한다.

## Reliability Target V4 Matched Contrast Plan

2026-06-20 KST에 `reliability_target_v4_matched_contrast_plan`을 진행했다. 이 단계는
train-only queue에서 v4 matched contrast target construction이 실제로 가능한지 확인하는
planning gate다. Label fill이나 posterior smoke는 실행하지 않았다.

Result:

```text
status = h002_reliability_target_v4_matched_contrast_plan_ready_with_asset_requests
selected_matching_level = predicate_object_rank_controlled
selected_matching_keys = predicate_label, endpoint_flag_pattern_hidden, object_family_cell_hidden
rank_control_policy = post_selection_quota_and_audit_control
selected rows = 160
selected contrast pairs = 80
packet_ready = 5
asset_needed = 155
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v4_matched_contrast_candidate_mining
```

Interpretation:

- Exact rank-band matching is infeasible in the current train queue.
- `strict_predicate_object_rank`, `family_object_rank`, and `family_endpoint_rank` all have
  `0` eligible contrast groups.
- Feasible capacity appears only after rank is changed from exact matching to quota/audit
  control.
- The selected level is `predicate_object_rank_controlled`, with `114` eligible groups and
  `275` balanced-pair capacity.
- This is stricter than v3 because positive/negative proxy rows are drawn from the same
  predicate + endpoint/object stratum, not from separate anchor buckets.
- The next practical blocker is asset coverage: only `5/160` preview rows are packet-ready.

## Reliability Target V4 Matched Contrast Candidate Mining

2026-06-20 KST에 `reliability_target_v4_matched_contrast_candidate_mining`을 진행했다.
이 단계는 v4 plan의 80개 contrast pair / 160개 row를 실제 label package와 asset request
plan으로 고정하는 gate다. Label fill이나 posterior smoke는 실행하지 않았다.

Result:

```text
status = h002_reliability_target_v4_matched_contrast_candidate_mining_ready_needs_asset_packets
label rows = 160
contrast pairs = 80
packet-ready rows = 5
asset-needed rows = 155
support_contact rows = 90
relative_vertical rows = 70
label-surface leakage hits = 0
packet path errors = 0
input validation errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v4_matched_contrast_asset_packets
```

Interpretation:

- Matched-contrast label sheet와 post-label hidden manifest는 준비됐다.
- Label surface에는 contrast role, stratum, rank, semantic score, geometry status, proxy field를
  노출하지 않았다.
- 그러나 `5/160` row만 packet-ready라서 full label fill을 바로 진행하면 evidence coverage가
  부족하다.
- 다음 단계는 155개 asset-needed row의 multi-view / pointcloud-or-mesh / contact-context
  packet을 생성하는 것이다.
- Posterior는 label fill, ingestion, target-independence audit이 통과하기 전까지 계속 blocked다.

## Reliability Target V4 Matched Contrast Asset Packets

2026-06-20 KST에 `reliability_target_v4_matched_contrast_asset_packets`을 진행했다.
이 단계는 v4 candidate mining에서 남아 있던 155개 asset-needed row에 evidence packet을
생성하고, 기존 5개 packet-ready row와 합쳐 full 160-row label sheet를 만드는 단계다.
Label fill이나 posterior smoke는 실행하지 않았다.

Result:

```text
status = h002_reliability_target_v4_matched_contrast_asset_packets_partial
input selected rows = 160
asset-needed input rows = 155
generated packet rows = 155
generated ready rows = 135
generated partial rows = 20
existing packet-ready rows = 5
full label sheet rows = 160
ready label rows = 140
partial label rows = 20
packet path errors = 0
label-surface leakage hits = 0
visible value leakage hits = 0
validation errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v4_matched_contrast_asset_packet_gap_audit
```

Interpretation:

- 모든 row에 label-facing packet path는 존재한다.
- Label surface와 packet text에는 contrast role, rank, semantic score, `p_geom`,
  geometry status, target-construction proxy가 노출되지 않았다.
- 하지만 20개 generated row는 한쪽 endpoint crop이 없다:
  `support_contact` 13개, `relative_vertical` 7개이며, subject crop missing 12개,
  object crop missing 8개다.
- 따라서 바로 label fill로 넘어가지 않고, partial packet row를
  `limited_view_evaluable`, `needs_more_evidence`, or replacement-needed로 판정하는
  gap audit이 필요하다.

## Reliability Target V4 Matched Contrast Asset Packet Gap Audit

2026-06-20 KST에 `reliability_target_v4_matched_contrast_asset_packet_gap_audit`을
진행했다. 이 단계는 20개 partial packet row를 label fill 전에 감사하고, v4의 pair integrity를
보존하기 위해 replacement-needed row가 있는 matched pair를 제외하는 gate다.

Result:

```text
status = h002_reliability_target_v4_matched_contrast_asset_packet_gap_audit_ready_for_label_readiness
input rows = 160
input pairs = 80
label-ready rows = 158
label-ready pairs = 79
excluded rows = 2
excluded pairs = 1
limited-view rows kept = 19
replacement-needed rows = 1
role balance = positive_proxy 79, negative_proxy 79
output path errors = 0
visible leakage hits = 0
input validation errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v4_matched_contrast_label_readiness
```

Interpretation:

- 19/20 partial rows are kept as `limited_view_evaluable` because mesh packet and
  contact/context evidence are available.
- 1 partial row is `replacement_needed` because the missing endpoint has the generic label
  `object`.
- Matched contrast는 pair integrity가 중요하므로 replacement-needed row가 포함된
  `v4pair_0042` 전체를 label fill에서 제외했다.
- 남은 label-ready slice는 79 matched pairs / 158 rows이고 positive/negative proxy role
  balance가 `79/79`로 유지된다.
- 다음 단계는 label fill이 아니라, 이 158-row sheet의 schema/path/leakage/pair-balance를
  검증하는 label-readiness gate다.

## Reliability Target V4 Matched Contrast Label Readiness

2026-06-21 KST에 `reliability_target_v4_matched_contrast_label_readiness`를 진행했다.
이 단계는 gap audit 이후 남은 158-row / 79-pair sheet의 visible schema, packet paths,
excluded-pair removal, pair-role balance, and leakage를 검증하는 gate다. Label fill,
ingestion, posterior smoke는 진행하지 않았다.

Result:

```text
status = h002_reliability_target_v4_matched_contrast_label_readiness_ready_for_label_fill
label-ready rows = 158
label-ready pairs = 79
ready rows = 139
limited-view rows = 19
family counts = support_contact 90, relative_vertical 68
role balance = positive_proxy 79, negative_proxy 79
expected columns match = true
input validation errors = 0
sheet validation errors = 0
packet path errors = 0
leakage hits = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v4_matched_contrast_label_fill
```

Interpretation:

- The 158-row / 79-pair v4 matched-contrast sheet is ready for label fill.
- 이 결과는 posterior evidence가 아니라 label-fill readiness evidence다.
- Multi-view, mesh, contact/context packets are audit/label evidence only and remain
  excluded from posterior input.
- Posterior smoke remains blocked until label fill, ingestion, and target-independence
  audit pass.

Main artifacts:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/160_reliability_target_v4_matched_contrast_label_readiness.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_label_readiness.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/ready_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/ready_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/label_schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/pair_readiness.csv
```

## Reliability Target V4 Matched Contrast Label Fill

2026-06-21 KST에 `reliability_target_v4_matched_contrast_label_fill`을 진행했다. 이
단계는 158-row / 79-pair v4 matched-contrast sheet의 review fields를 visible-only
기준으로 채우는 단계다. Ingestion, target-independence audit, posterior smoke는 진행하지
않았다.

Result:

```text
status = h002_reliability_target_v4_matched_contrast_label_filled_codex_proxy_user_requested
rows = 158
reliable = 23
unreliable = 24
uncertain = 111
binary target rows = 47
binary positive rows = 23
binary negative rows = 24
geometry support = supports 30, contradicts 17, ambiguous 111
input validation errors = 0
fill validation errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v4_matched_contrast_label_ingestion
```

Post-label diagnostics:

| Hidden Group | Rows | Reliable | Unreliable | Uncertain |
| --- | ---: | ---: | ---: | ---: |
| `negative_proxy` / `HL` / `unsatisfied` | 79 | 11 | 14 | 54 |
| `positive_proxy` / `LH` / `satisfied` | 79 | 12 | 10 | 57 |
| `label_ready` rows | 139 | 23 | 24 | 92 |
| `limited_view_evaluable` rows | 19 | 0 | 0 | 19 |

Interpretation:

- Binary target rows are balanced at `23` positive / `24` negative.
- The fill is conservative: `111/158` rows remain `uncertain`.
- Hidden matched role does not trivially decide labels; positive and negative proxy sides have similar
  label distributions.
- Pair-level contrast remains weak: only `1/79` pair has a direct `reliable/unreliable` contrast.
- Therefore this unlocks ingestion and target-independence audit, not posterior smoke.

Main artifacts:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/161_reliability_target_v4_matched_contrast_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/completed_v4_matched_contrast_label_sheet_codex_proxy_user_requested.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/v4_proxy_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/relation_reliability_v4_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/post_label_diagnostics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/pair_post_label_diagnostics.csv
```

## Reliability Target V4 Matched Contrast Label Ingestion

2026-06-21 KST에 `reliability_target_v4_matched_contrast_label_ingestion`을 진행했다.
이 단계는 v4 proxy labels를 ingest해서 relation reliability, geometry support, relation
usefulness target artifacts로 분리하는 단계다. Posterior candidate file은 만들지만 posterior
smoke는 진행하지 않았다.

Result:

```text
status = h002_reliability_target_v4_matched_contrast_label_ingested_with_probe_risk
rows = 158
relation reliability binary = 47 rows, 23 positive, 24 negative
geometry support binary = 47 rows, 30 positive, 17 negative
relation usefulness binary = 50 rows, 25 positive, 25 negative
ingestion errors = 0
relation reliability probe = target_independence_risk_hidden_metadata_correlated
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v4_matched_contrast_target_independence_audit
```

Probe summary:

| Target | Probe Status | Hidden Risks | Visible Risks |
| --- | --- | ---: | ---: |
| `relation_reliability_v4_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 3 | 2 |
| `geometry_support_v4_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 3 | 4 |
| `relation_usefulness_v4_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 3 | 2 |

Top relation-reliability risks:

| Source | Group Key | NMI | Majority Accuracy |
| --- | --- | ---: | ---: |
| hidden | `subject_object_family_cell_hidden` | 1.0000 | 1.0000 |
| hidden | `endpoint_flag_pattern_hidden` | 0.5774 | 0.8085 |
| hidden | `object_family_cell_hidden` | 0.3937 | 0.7447 |
| visible | `subject_label` | 0.7764 | 0.9149 |
| visible | `object_label` | 0.3914 | 0.7447 |

Interpretation:

- Relation reliability target mass is balanced and usable for audit: `23/24`.
- However, target independence is not established because object/family cells and visible object labels
  strongly correlate with the binary target.
- This supports the current sequence: ingestion succeeded, but posterior remains blocked until a
  dedicated target-independence audit identifies a controlled slice or decides another target revision is
  needed.

Main artifacts:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/162_reliability_target_v4_matched_contrast_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/validated_v4_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/relation_reliability_v4_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/geometry_support_v4_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/relation_usefulness_v4_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested/target_independence_probe_summaries.csv
```

Earlier informative-anchor posterior-smoke boundary:

```text
The v3 ingestion is a Codex proxy artifact. It improves positive target mass but
the follow-up independence audit found no posterior-ready controlled slice.
```

Earlier posterior smoke result:

```text
factorized - semantic_plus_geometry grouped AUPRC = +0.0117
factorized - semantic_plus_geometry grouped Brier = -0.0019
proposed_role_only AUPRC = 1.0000
label_status_only AUPRC = 0.9473
```

Interpretation:

```text
The current full-train bootstrap target is dominated by label-policy proxies.
This supports RGA/audit framing, not a factorized posterior method claim.
```

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

### Stage 8. Factor Dataset

Document:

```text
26_factor_dataset.md
```

Purpose:

- materialize deployable feature rows from train RGA rows.
- join audit targets without leaking label/audit evidence into deployable inputs.
- create strict and weak train-only smoke inputs.
- freeze the concrete files used by the next posterior smoke fitting step.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/deployable_features_all.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/strict_smoke.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/weak_smoke.jsonl
```

Counts:

| Artifact | Rows |
| --- | ---: |
| `deployable_features_all.jsonl` | 118,560 |
| `target_joined.jsonl` | 217 |
| `strict_smoke.jsonl` | 93 |
| `weak_smoke.jsonl` | 132 |

Boundary:

```text
no validation usage
no label/audit evidence in deployable feature blocks
no paper-level performance claim
```

### Stage 9. Factor Smoke

Document:

```text
27_factor_smoke.md
```

Purpose:

- run train-only smoke fitting for the four planned baseline views.
- check whether the current strict/weak targets are independent enough for
  posterior interpretation.
- report shortcut risk before any method claim.

Key artifact:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_smoke/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_smoke/metrics.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_smoke/report.md
```

Main finding:

```text
status = ready_with_shortcut_caveat
```

Strict target is too close to the RGA bucket construction. The smoke therefore
validates the executable pipeline but does not validate posterior novelty.

### Stage 10. Shortcut Control

Document:

```text
28_shortcut_control.md
```

Purpose:

- remove target-construction shortcut feature groups.
- test whether strict/weak targets remain predictable after controls.
- decide whether posterior performance is interpretable.

Key artifact:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_shortcut_control/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_shortcut_control/metrics.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_shortcut_control/report.md
```

Main finding:

```text
status = ready_target_not_independent
```

The strict target remains perfectly predictable even with continuous-only
geometry evidence. This means the current target validates feature plumbing, not
posterior novelty.

### Stage 11. Target Redesign

Document:

```text
29_target_redesign.md
```

Purpose:

- replace shortcut-prone strict/weak targets.
- define within-geometry-supported reliability targets.
- separate relabel-only and abstain labels from binary reliability labels.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/target_contract.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/strict_proximity_informativeness.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/weak_satisfied_actionability.jsonl
```

Main finding:

```text
status = ready_target_v2_contract
```

The primary target is `strict_proximity_informativeness`: geometry-satisfied
proximity rows only, with `true_underconfidence` as positive and
`dense_relation_noise` as negative. It has 16 positives and 11 negatives, so it
is a small plumbing-smoke target, not paper evidence.

### Stage 12. Redesigned Target Smoke

Document:

```text
30_redesigned_target_smoke.md
```

Purpose:

- test target v2 with direct target identity features removed.
- verify whether the redesigned target still collapses to a trivial score.
- decide whether human confirmation is worth running.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/redesigned_target_smoke/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/redesigned_target_smoke/metrics.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/redesigned_target_smoke/report.md
```

Main finding:

```text
status = ready_plumbing_only
```

The strict target v2 is less shortcut-prone than the previous target but has only
27 rows. It justifies a human confirmation protocol, not a posterior performance
claim.

### Stage 13. Human Confirmation Protocol

Document:

```text
31_human_confirmation_protocol.md
```

Purpose:

- define human confirmation fields for target v2.
- create strict and weak review sheets.
- define when human labels can be used for posterior-training evidence.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/protocol.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_review_sheet.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/weak_extension_sheet.tsv
```

Main finding:

```text
status = ready_protocol_no_human_labels
```

The protocol is ready, but no human label has been filled. Posterior claims
remain blocked.

### Stage 14. Human Label Readiness

Document:

```text
32_human_label_readiness.md
```

Purpose:

- fill the strict primary sheet with a temporary `(codex_ver)` reviewer label.
- validate required fields and allowed values.
- compute usable binary posterior targets after exclusion.
- decide whether train-only posterior plumbing smoke can resume.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_review_sheet_codex_ver.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_codex_ver_labels.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_codex_ver_binary_targets.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/codex_ver_readiness_summary.json
```

Main finding:

```text
status = ready_for_train_only_codex_plumbing_smoke
```

Counts:

```text
strict rows = 27
usable binary rows = 27
positive targets = 16
negative targets = 11
missing required fields = 0
invalid values = 0
```

Boundary:

```text
(codex_ver) labels are not human-confirmed labels.
```

They can support a train-only plumbing smoke but cannot support paper evidence,
posterior advantage claims, or reviewer agreement.

### Stage 15. Multi-View Feasibility Check

Document:

```text
feasibility_check.md
```

Purpose:

- decide whether point cloud + multi-view belongs in H002.
- prevent the scope from drifting into a generic stronger relation predictor.
- define multi-view as an RGA evidence-axis extension.

Main verdict:

```text
reasonable, but only as evidence factor expansion
```

Future posterior form:

```text
P(R_e = 1 | S_e, G_3D_e, V_mv_e, C_e, U_e)
```

where `V_mv_e` is multi-view crop, co-visible image, visibility, occlusion, and
appearance-context evidence.

Boundary:

```text
Use multi-view as audit/confirmation evidence before using it as model input.
```

### Stage 16. Codex Label Smoke

Document:

```text
33_codex_label_smoke.md
```

Purpose:

- join `(codex_ver)` strict binary targets to target-v2 feature rows.
- run train-only posterior plumbing smoke.
- verify semantic-only, geometry-only, semantic+geometry, and factorized inputs.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/codex_label_smoke/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/codex_label_smoke/metrics.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/codex_label_smoke/report.md
```

Main finding:

```text
status = ready_plumbing_only_codex_labels
```

Train-internal 5-fold AUROC/AUPRC:

```text
semantic_only = 0.6080 / 0.7431
geometry_only = 0.8523 / 0.8986
semantic_plus_geometry = 0.8864 / 0.9217
factorized_reliability_posterior = 0.8864 / 0.9339
```

Interpretation:

- posterior pipeline can consume `(codex_ver)` labels.
- `p_geom_valid` alone is not relation reliability for the strict target.
- this is not posterior advantage evidence because labels are not human-confirmed
  and `N=27`.

### Stage 17. Multi-View Audit Protocol

Document:

```text
34_multiview_audit_protocol.md
```

Purpose:

- fix the order: validate current factorized posterior before adding `V_mv_e`.
- use multi-view only as audit/confirmation evidence for now.
- create review sheets for current strict labels and future support-contact audit.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/protocol.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/primary_strict_sheet.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/support_contact_sheet.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/all_candidate_sheet.tsv
```

Main finding:

```text
status = ready_audit_only_vmv_deferred
```

Counts:

```text
primary strict proximity rows = 27
support_contact extension rows = 26
relative_vertical lower-priority rows = 34
all candidates = 87
contact sheet coverage = 87 / 87
mesh link coverage = 87 / 87
```

Boundary:

```text
deployable_vmv_features_created = false
model_input_expansion_allowed_now = false
```

Current rule:

```text
Validate P(R_e = 1 | S_e, G_e, C_e, U_e) first.
Use multi-view only for audit evidence until that gate passes.
```

### Stage 18. Factorized Validation Plan

Document:

```text
35_factorized_validation_plan.md
```

Purpose:

- define when the current factorized posterior can support the H002 hypothesis.
- fix the minimal independent/human-confirmed label target.
- fix controls before any posterior advantage claim.
- keep `V_mv_e` out of model input.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factorized_validation_plan/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factorized_validation_plan/protocol.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/factorized_validation_plan/report.md
```

Main finding:

```text
status = ready_validation_plan_vmv_deferred
```

Target minimum:

```text
hypothesis-stage usable rows >= 60
per-class rows >= 20
label source = human-confirmed or independent audit
codex_ver sufficient = false
```

Required controls:

```text
same-family
same-geometry-status
same-rank-band
same-source for current pilot
no visual input
```

Acceptance rule:

```text
factorized_reliability_posterior must beat semantic_plus_geometry by
AUPRC >= +0.03 or Brier <= -0.02, with AUROC drop <= 0.02, under the
controlled label target.
```

### Stage 19. Controlled Label Target

Document:

```text
36_controlled_label_target.md
```

Purpose:

- expand the current strict target into a controlled human-review candidate set.
- preserve same-family, same-geometry-status, same-source, and rank-band controls.
- create review sheets without creating final labels.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/protocol.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/mined_controlled_queue.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/mined_controlled_sheet.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/combined_review_queue.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/combined_review_sheet.tsv
```

Main finding:

```text
status = ready_controlled_review_queue_no_labels
```

Mined controlled queue:

```text
rows = 96
predicate_family = proximity
predicate_label = close by
geometry_status = satisfied
semantic_rank > 100
candidate_reliable_promote_seed = 48
candidate_unreliable_dense_noise_seed = 48
rank_201_500 = 32
rank_501_1000 = 32
rank_gt1000 = 32
contact_sheet coverage = 96 / 96
mesh link coverage = 96 / 96
```

Combined with existing strict seed:

```text
combined review rows = 123
```

Boundary:

```text
proposed_review_stratum is not a final label.
final labels created = false.
```

### Stage 20. Controlled Label Readiness

Document:

```text
37_controlled_label_readiness.md
```

Purpose:

- validate whether controlled review sheets have filled final labels.
- check required fields and allowed values.
- export binary targets only from allowed final labels.
- block posterior fitting until target minimum is satisfied.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness/mined_binary_targets.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness/combined_binary_targets.jsonl
```

Main finding:

```text
status = not_ready_no_filled_labels
```

Readiness result:

| Sheet | Rows | Completed | Binary rows | Per-class min |
| --- | ---: | ---: | ---: | ---: |
| `mined_controlled` | 96 | 0 | 0 | 0 |
| `combined_review` | 123 | 0 | 0 | 0 |

Decision:

```text
current posterior fitting remains blocked.
```

The next gate is to fill controlled review labels with human/independent review,
then rerun the readiness validator. Proposed review strata remain sampling priors
and are not labels.

### Stage 21. Controlled Codex Labels

Document:

```text
38_controlled_codex_labels.md
```

Purpose:

- fill controlled review sheets with `(codex_ver)` bootstrap labels after user
  request.
- preserve original blank review sheets.
- rerun readiness on Codex-filled sheets.
- keep the label source boundary explicit.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/mined_controlled_sheet_codex_ver.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/combined_review_sheet_codex_ver.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_codex_labels/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness_codex_ver/summary.json
```

Main finding:

```text
status = controlled_codex_ver_labels_filled_not_human_confirmed
```

Counts:

| Sheet | Rows | Positive | Negative |
| --- | ---: | ---: | ---: |
| `mined_controlled` | 96 | 48 | 48 |
| `combined_review` | 123 | 64 | 59 |

Readiness:

```text
status = ready_for_train_only_controlled_posterior_smoke
```

Boundary:

```text
codex_ver labels are sampling-prior bootstrap labels, not human-confirmed labels.
```

### Stage 22. Controlled Posterior Smoke

Document:

```text
39_controlled_posterior_smoke.md
```

Purpose:

- join controlled Codex labels to deployable feature rows.
- run the four planned baseline views.
- verify end-to-end posterior plumbing under train-only constraints.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_posterior_smoke_codex_ver/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_posterior_smoke_codex_ver/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_posterior_smoke_codex_ver/metrics.csv
```

Train-internal 5-fold main result:

| Target | `semantic_plus_geometry` AUPRC | `factorized` AUPRC | Delta AUPRC | Delta Brier |
| --- | ---: | ---: | ---: | ---: |
| `mined_controlled_codex_ver` | 0.9546 | 0.9552 | +0.0006 | -0.0012 |
| `combined_controlled_codex_ver` | 0.7321 | 0.7658 | +0.0337 | -0.0081 |

Decision:

```text
posterior plumbing works, but H002 hypothesis is not validated by codex_ver labels.
```

The next scientific gate is human/independent controlled labels, not more model
fitting on Codex labels.

### Stage 23. Real Label Assumption Claim Audit

Document:

```text
40_real_label_claim_audit.md
```

Purpose:

- follow the user-directed assumption that `(codex_ver)` controlled labels are
  treated as real labels for hypothesis-stage analysis.
- reinterpret the controlled posterior smoke under that assumption.
- identify what still blocks a strong H002 posterior claim.

Working assumption:

```text
artifact provenance = codex_ver
current interpretation = user-directed real-label assumption
```

Main finding:

```text
weak conditional support only
```

Reinterpreted result:

| Target | Delta AUPRC | Delta Brier | Verdict |
| --- | ---: | ---: | --- |
| `mined_controlled_codex_ver` | +0.0006 | -0.0012 | insufficient |
| `combined_controlled_codex_ver` | +0.0337 | -0.0081 | weak positive signal |

Main blocker:

```text
factorized gain is not yet isolated from rank/identity/target-construction effects.
```

Evidence:

- `drop_direct_identity` collapses back to `semantic_plus_geometry` behavior.
- `drop_direct_identity_rank` and `safe_continuous` are near random.
- mined-only target does not show meaningful factorized gain.

Next required checks:

- scan-grouped CV.
- explicit `S+G`, `S+G+C`, `S+G+U`, `S+G+C+U` ablation.
- rank-band and strict-seed dependence analysis.
- proxy baselines such as rank-only and rank-band-only.
- paired bootstrap CI.
- calibration analysis with Brier/ECE/reliability bins.

### Stage 24. Grouped Control Smoke

Document:

```text
41_grouped_control_smoke.md
```

Purpose:

- treat `(codex_ver)` as real label under the user-directed hypothesis-stage
  assumption.
- rerun controlled posterior smoke with `scan_id` grouped folds.
- add explicit factor ablations and rank proxy baselines.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/grouped_control_smoke_codex_real_assumption/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/grouped_control_smoke_codex_real_assumption/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/grouped_control_smoke_codex_real_assumption/metrics.csv
```

Grouped result:

| Target | Factorized - `S+G` AUPRC | Factorized - `S+G` Brier | Verdict |
| --- | ---: | ---: | --- |
| `mined_controlled_codex_ver` | +0.0341 | -0.0234 | numeric pass |
| `combined_controlled_codex_ver` | +0.0268 | -0.0082 | weak / below AUPRC threshold |

Factor ablation:

```text
S+G+C adds no signal.
S+G+U carries the gain.
```

Critical blocker:

```text
negative_rank_only beats factorized_reliability_posterior.
```

Proxy evidence:

| Target | Factorized AUPRC | `negative_rank_only` AUPRC |
| --- | ---: | ---: |
| `mined_controlled_codex_ver` | 0.9409 | 0.9589 |
| `combined_controlled_codex_ver` | 0.6801 | 0.7094 |

Decision:

```text
H002 has conditional support for the reliability framing, but not yet strong
support for the factorized posterior as a method contribution.
```

### Stage 25. Rank Proxy Debias

Document:

```text
42_rank_proxy_debias.md
```

Purpose:

- test whether factorized posterior beats a simple rank-derived proxy.
- remove rank-derived features and evaluate non-rank evidence.
- add non-rank evidence to `negative_rank_only` and check whether it improves.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_proxy_debias_codex_real_assumption/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_proxy_debias_codex_real_assumption/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_proxy_debias_codex_real_assumption/metrics.csv
```

Main finding:

```text
status = rank_proxy_not_debiased
```

Critical comparisons:

| Target | Left | Right | Delta AUPRC | Delta Brier |
| --- | --- | --- | ---: | ---: |
| `mined_controlled_codex_ver` | `factorized` | `negative_rank_only` | -0.0179 | +0.0041 |
| `combined_controlled_codex_ver` | `factorized` | `negative_rank_only` | -0.0293 | +0.0187 |
| `mined_controlled_codex_ver` | `negative_rank + factorized_no_rank` | `negative_rank_only` | -0.0491 | +0.0286 |
| `combined_controlled_codex_ver` | `negative_rank + factorized_no_rank` | `negative_rank_only` | -0.0141 | +0.0164 |

Decision:

```text
The current controlled-label signal is still explainable by semantic rank /
underconfidence proxy. H002 should not claim a factorized-posterior method
contribution yet.
```

Implication:

```text
The next blocker is target construction, not model capacity.
```

### Stage 26. Within-Rank Stability

Document:

```text
43_within_rank_stability.md
```

Purpose:

- evaluate whether factorized evidence remains useful inside fixed rank bands.
- compare factorized posterior against `negative_rank_only` within each band.
- build rank-matched positive/negative pairs using `rank_in_context`.
- check whether the current controlled target is independent enough from
  semantic-rank construction.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/metrics.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/pairwise.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/within_rank_stability_codex_real_assumption/matched_pairs.jsonl
```

Result:

```text
status = within_rank_mixed
```

Primary grouped comparison:

| Target | Rank band | `factorized - negative_rank_only` AUPRC | `factorized - negative_rank_only` Brier |
| --- | --- | ---: | ---: |
| `mined_controlled_codex_ver` | `rank_201_500` | -0.0917 | +0.0727 |
| `mined_controlled_codex_ver` | `rank_501_1000` | -0.0545 | +0.0116 |
| `mined_controlled_codex_ver` | `rank_gt1000` | +0.0000 | +0.0020 |
| `combined_controlled_codex_ver` | `rank_201_500` | -0.0917 | +0.0727 |
| `combined_controlled_codex_ver` | `rank_501_1000` | -0.0545 | +0.0116 |
| `combined_controlled_codex_ver` | `rank_gt1000` | +0.0000 | +0.0020 |

Pairwise observation:

| Target | Rank band | Pairs | Mean rank gap | Factorized | `negative_rank_only` |
| --- | --- | ---: | ---: | ---: | ---: |
| `mined_controlled_codex_ver` | `rank_201_500` | 16 | 32.06 | 0.8750 | 0.8438 |
| `mined_controlled_codex_ver` | `rank_501_1000` | 16 | 11.56 | 0.8125 | 0.6875 |
| `mined_controlled_codex_ver` | `rank_gt1000` | 16 | 51.38 | 0.9375 | 0.9375 |

Decision:

```text
Within-rank evidence is mixed. Pairwise rank-matched checks show that relation
evidence can help inside some bands, but grouped primary-band metrics still do
not consistently beat the negative-rank proxy.
```

Implication:

```text
The next step is a stricter rank-matched target, not a larger posterior model.
```

### Stage 27. Rank-Matched Target

Document:

```text
44_rank_matched_target.md
```

Purpose:

- build a stricter controlled target by directly matching positive and negative
  rows with close `rank_in_context`.
- exclude large-gap non-tail pairs from primary smoke metrics.
- keep `tail` pairs as exploratory rows only.
- rerun train-only scan-grouped posterior smoke on the stricter target.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/metrics.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/pairwise.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/rank_matched_target_codex_real_assumption/pair_records.jsonl
```

Result:

```text
status = rank_matched_mixed
```

Target construction:

| Target | Scope | Rows | Pairs | Mean rank gap | Max rank gap | Evaluated |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `mined_rank_matched_gap50_codex_ver` | primary | 86 | 43 | 14.56 | 47.00 | yes |
| `combined_rank_matched_gap50_codex_ver` | primary | 86 | 43 | 14.56 | 47.00 | yes |
| `combined_tail_exploratory_gap500_codex_ver` | tail exploratory | 22 | 11 | 103.91 | 367.00 | no |

Primary grouped comparison:

| Left | Right | Delta AUPRC | Delta Brier |
| --- | --- | ---: | ---: |
| `factorized_reliability_posterior` | `semantic_plus_geometry` | +0.0245 | -0.0144 |
| `factorized_reliability_posterior` | `negative_rank_only` | -0.0239 | +0.0029 |
| `negative_rank_plus_factorized_no_rank` | `negative_rank_only` | -0.0490 | +0.0223 |
| `negative_rank_plus_disagreement` | `negative_rank_only` | -0.0049 | -0.0002 |

Pairwise observation:

| Target | Pairs | Factorized | `negative_rank_only` | `factorized_no_rank` | `p_geom_valid_raw` |
| --- | ---: | ---: | ---: | ---: | ---: |
| `mined_rank_matched_gap50_codex_ver` | 43 | 0.8605 | 0.8372 | 0.6512 | 0.5349 |

Decision:

```text
Rank-matched target is mixed. The stricter target reduces large rank-gap
shortcuts, but factorized posterior still does not beat negative_rank_only under
scan-grouped CV. Pairwise evidence remains mildly favorable but insufficient.
```

Implication:

```text
The next blocker is label/target independence. The current codex target is not
independent enough to support a posterior method claim.
```

### Stage 28. Target Independence Audit

Document:

```text
45_target_independence_audit.md
```

Purpose:

- diagnose why `negative_rank_only` remains strong after rank matching.
- separate target construction effects from deployable evidence effects.
- audit whether current codex labels are independent enough to support a
  posterior method claim.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_independence_audit_codex_real_assumption/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_independence_audit_codex_real_assumption/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_independence_audit_codex_real_assumption/feature_summaries.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_independence_audit_codex_real_assumption/metadata_summaries.csv
```

Result:

```text
status = target_independence_not_established
```

Main evidence:

| Check | Result |
| --- | --- |
| Mean matched rank gap | 14.56 |
| Positive has worse source rank share | 0.8140 |
| `negative_rank_only_raw` pairwise accuracy | 0.8372 |
| `p_geom_valid_raw` pairwise accuracy | 0.5349 |
| `final_controlled_label` row-majority purity | 1.0000 |
| `proposed_review_stratum` row-majority purity | 1.0000 |
| `mined` vs `combined` primary target Jaccard | 1.0000 |

Decision:

```text
Current codex-controlled rank-matched labels are still not independent enough
from semantic-rank / underconfidence construction to support a posterior method
claim.
```

Implication:

```text
H002 should continue the RGA framework and target construction work, but pause
posterior method claims until rank-hidden independent audit labels exist.
```

### Stage 29. Independent Label Protocol

Document:

```text
46_independent_label_protocol.md
```

Purpose:

- define rank-hidden independent label collection for H002.
- create blind review sheets that hide semantic rank, semantic score,
  `p_geom_valid`, working label, queue identity, and proposed stratum.
- use multi-view/mesh assets as audit evidence only, not deployable model input.
- prioritize relation families for future semantic-geometry-visual agreement.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/protocol.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_all_sheet.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_support_contact_sheet.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_proximity_sheet.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_relative_vertical_sheet.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/internal_key.jsonl
```

Result:

```text
status = independent_label_protocol_ready
```

Candidate counts:

| Family | Rows | Role |
| --- | ---: | --- |
| `support_contact` | 26 | first multi-view reliability family |
| `proximity` | 27 | current debugging family |
| `relative_vertical` | 34 | control / robustness family |
| `attachment_deferred` | 0 | future high-novelty family; separate generator needed |

Label mapping:

| Binary use | Labels |
| --- | --- |
| positive | `reliable_informative`, `annotation_sparsity_candidate` |
| negative | `valid_but_trivial_dense`, `invalid_relation`, `invalid_pair`, `visibility_or_geometry_artifact` |
| exclude or multiclass only | `ontology_mismatch`, `abstain_uncertain` |

Decision:

```text
Independent label protocol is ready. H002 should collect or fill rank-hidden
labels before any stronger posterior method claim.
```

Combiner follow-up after labels:

```text
residual reliability model -> gated evidence model -> pairwise rank-matched
ranking diagnostic -> debiased factor audit
```

### Stage 30. Independent Label Ingestion

Document:

```text
47_independent_label_ingestion.md
```

Purpose:

- validate completed rank-hidden blind sheets.
- join completed labels back to `internal_key.jsonl`.
- materialize independent binary and multiclass targets.
- keep hidden semantic/geometry/rank provenance out of deployable input
  features.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/schema.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/validated_labels.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/binary_targets.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/multiclass_targets.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/ingestion_errors.jsonl
```

Result:

```text
status = independent_label_ingestion_waiting_for_completed_labels
```

Counts:

| Item | Count |
| --- | ---: |
| blind sheet rows | 87 |
| internal key rows | 87 |
| completed label rows | 0 |
| binary target rows | 0 |
| ingestion errors | 0 |

Decision:

```text
The ingestion path is ready, but no independent labels are completed yet.
Residual/gated combiner diagnostics remain blocked until rank-hidden labels are
filled and ingested.
```

### Stage 31. Blind Label Fill

Document:

```text
48_blind_label_fill.md
```

Purpose:

- fill rank-hidden blind labels with `(codex_ver_blind)` bootstrap labels.
- fix asset-level leakage in the original contact sheets by generating sanitized
  crop paths and sanitized contact sheets.
- rerun independent label ingestion on the completed sheet.
- produce binary targets for train-only residual/gated combiner diagnostics.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_all_sheet_sanitized.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_all_sheet_codex_ver.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_blind_codex_labels/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_blind_codex_labels/labels.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_blind_codex_labels/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver/binary_targets.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver/report.md
```

Result:

```text
status = independent_label_targets_ready
```

Counts:

| Item | Count |
| --- | ---: |
| completed label rows | 87 |
| binary target rows | 75 |
| positive rows | 46 |
| negative rows | 29 |
| excluded rows | 12 |
| ingestion errors | 0 |

Boundary:

```text
codex_ver_blind labels are bootstrap labels, not human-confirmed labels.
```

Decision:

```text
H002 can proceed to train-only independent combiner diagnostics, but cannot
claim paper-level human-label evidence or posterior method advantage from these
labels alone.
```

### Stage 32. Independent Combiner Smoke

Document:

```text
49_independent_combiner_smoke.md
```

Purpose:

- join `independent_label_ingestion_codex_ver/binary_targets.jsonl` to deployable
  feature rows.
- evaluate semantic-only, geometry-only, semantic+geometry, factorized,
  residual, and gated evidence views.
- compare against rank, family, predicate, and `p_geom_valid` proxy controls.
- report grouped-by-scan, family-slice, and rank-matched pairwise diagnostics.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/metrics.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/family_slices.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/pairwise.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/matched_pairs.jsonl
```

Result:

```text
status = independent_combiner_no_strong_signal
```

Grouped-by-scan main deltas:

| Comparison | Delta AUPRC | Delta Brier |
| --- | ---: | ---: |
| `factorized - semantic_plus_geometry` | -0.0013 | +0.0016 |
| `residual - semantic_plus_geometry` | -0.1010 | +0.0184 |
| `gated - semantic_plus_geometry` | -0.0969 | +0.0186 |
| `factorized - negative_rank_only` | +0.1412 | -0.0289 |

Interpretation:

```text
Factorized beats the negative-rank proxy, but it does not beat
semantic_plus_geometry. Residual/gated variants are worse overall. The current
bootstrap label policy is strongly entangled with family/predicate semantics.
```

Decision:

```text
Independent combiner plumbing is complete, but posterior method claims remain
blocked. The next blocker is label-policy and family/predicate bias.
```

### Stage 33. Label Policy Audit

Document:

```text
50_label_policy_audit.md
```

Purpose:

- test whether `(codex_ver_blind)` labels are recoverable from family/predicate
  policy.
- export family-balanced, predicate-balanced, and proximity-only target variants.
- rerun train-only grouped smoke on those variants.
- decide whether posterior method claims remain plausible.

Key artifacts:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/group_policy_table.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/metrics.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/comparisons.csv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/family_balanced_codex_ver_blind.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/predicate_balanced_codex_ver_blind.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/proximity_only_codex_ver_blind.jsonl
```

Result:

```text
status = label_policy_entangled
```

Main finding:

| Key | Majority Accuracy | NMI |
| --- | ---: | ---: |
| `predicate_family` | 0.7067 | 0.1931 |
| `predicate_label` | 0.7067 | 0.2505 |
| `rank_band` | 0.6533 | 0.0980 |

Balanced target result:

| Target | Rows | Positive | Negative |
| --- | ---: | ---: | ---: |
| `family_balanced_codex_ver_blind` | 44 | 22 | 22 |
| `predicate_balanced_codex_ver_blind` | 44 | 22 | 22 |
| `proximity_only_codex_ver_blind` | 27 | 15 | 12 |

Decision:

```text
The current bootstrap target is too entangled with predicate/family policy to
support posterior novelty. H002 should not escalate the posterior method claim
without new human labels or a much tighter target protocol.
```

### Stage 34. Posterior Path Decision

Document:

```text
51_posterior_path_decision.md
```

Purpose:

- decide whether the posterior remains a method candidate.
- answer whether changing posterior combination could improve H002.
- separate model-formulation potential from current label-policy blocker.
- define minimum evidence required to revive posterior claims.

Decision:

```text
posterior_path_deferred
```

Meaning:

```text
Posterior remains a conditional future method candidate, but it should not be
the near-term H002 main contribution.
```

Current best main direction:

```text
RGA benchmark / diagnostic framework / failure taxonomy
```

Posterior revival candidates:

| Candidate | Role |
| --- | --- |
| semantic-prior residual posterior | strongest conceptual match |
| family-specific hierarchical posterior | useful after family-balanced labels |
| coverage-gated geometry model | useful after uncertainty-rich labels |
| pairwise rank-matched reliability ranking | useful for small controlled labels |
| debiased/orthogonalized factor posterior | tests independent geometry signal |
| selective/abstention-aware posterior | models uncertain/unsupported cases |
| monotonic calibrated posterior | improves calibration defensibility |

Feasibility-check reuse rule:

```text
feasibility_check.md is reused as the method map, but with staged entry.
```

Immediate use:

- multi-view/mesh/contact-sheet evidence is audit evidence, not model input.
- use it to distinguish `true_underconfidence`, `dense_relation_noise`,
  `annotation_sparsity`, `ontology_mismatch`, and visual/mesh uncertainty.
- keep relation-family expansion in the order
  `support_contact -> attachment_deferred -> relative_vertical`.

Deferred use:

- `V_mv_e` enters the posterior only after the current
  `S_e + G_e + C_e + U_e` target passes an independent-label gate.
- residual/gated/pairwise/debiased/product-of-experts/hierarchical/monotonic
  combiners are posterior revival candidates, not current main-claim evidence.

Minimum revival gate:

```text
human-confirmed predicate/family-controlled labels, >=150 binary usable rows,
per-family minority >=15, grouped CV gain over semantic_plus_geometry, and
predicate/family/rank proxy controls passed.
```

### Stage 35. RGA Main Framing

Document:

```text
52_rga_main_framing.md
```

Purpose:

- reframe near-term H002 around RGA benchmark, diagnostic framework, and failure
  taxonomy.
- keep posterior as a conditional method candidate.
- adopt full-train expansion before opening validation/test.
- connect `feasibility_check.md` to audit evidence and posterior revival.

Decision:

```text
full_train_expansion_before_validation
```

Meaning:

```text
Expand H002 from the Open3DSG train pilot to full train, keep validation/test
closed, use RGA as the main framework, and use full train to mine controlled
labels and test whether posterior signal survives shortcut controls.
```

Full-train expansion purpose:

- pilot train failure does not falsify H002 posterior on the full train
  distribution.
- full train can provide more balanced family/predicate/rank-controlled targets.
- validation/test must remain closed until target, features, metrics, baselines,
  and posterior combiner are frozen.

Immediate full-train gates:

1. freeze full-train source scope and row identity.
2. generate full-train RGA rows for train split only.
3. measure RGA-HL/RGA-LH, coverage, uncertainty, and label-axis distributions.
4. mine controlled label targets with at least 150 binary rows and family
   minority support.
5. run train-only grouped CV against semantic, geometry, semantic+geometry, and
   proxy controls.

Next document:

```text
53_full_train_scope_contract.md
```

### Stage 36. Full Train Scope Contract

Document:

```text
53_full_train_scope_contract.md
```

Purpose:

- define full-train source scope before any execution.
- separate the full-train artifact root from the train-pilot root.
- decide which pilot tools can be reused and which must be parameterized.
- keep validation/test closed.

Decision:

```text
full_train_scope_contract_ready_no_execution
```

Scope:

```text
open3dsg_train_full
```

Expected planning counts from the existing pilot manifest:

| Item | Count |
| --- | ---: |
| official train subset contexts | 3,852 |
| ready candidate train contexts | 3,738 |
| dropped preprocess-not-ready contexts | 108 |
| dropped no-relationship contexts | 6 |

Artifact root:

```text
artifacts/train_rga_full/open3dsg_train_full/
```

Key implementation decision:

```text
The pilot source-contract runner is not reusable as-is because it selects one
representative subgraph per scan. Full train requires all ready train contexts.
```

Next document:

```text
54_full_train_source_runner.md
```

### Stage 37. Full Train Source Runner

Document:

```text
54_full_train_source_runner.md
```

Purpose:

- implement the all-ready full-train source contract runner.
- create the full-train source contract artifact.
- verify train-only provenance and no validation/test source leakage.

Added tool:

```text
tools/full_train_source_contract.py
```

Result:

```text
status = full_train_source_contract_ready
```

Output root:

```text
artifacts/train_rga_full/open3dsg_train_full/source_contract/
```

Counts:

| Item | Count |
| --- | ---: |
| official train subset contexts | 3,852 |
| ready candidate contexts | 3,738 |
| selected contexts | 3,738 |
| selected scans | 1,157 |
| selected relationships | 79,704 |
| dropped preprocess-not-ready | 108 |
| dropped no-relationship | 6 |

Primary family coverage:

| Family | GT relations |
| --- | ---: |
| `support_contact` | 12,600 |
| `proximity` | 12,300 |
| `relative_vertical` | 3,552 |

Next document:

```text
55_full_train_runtime_stage.md
```

### Stage 38. Full Train Runtime Stage

Document:

```text
55_full_train_runtime_stage.md
```

Purpose:

- parameterize the H002 runtime staging tool for full train.
- create `compose.open3dsg_train_full.yaml`.
- stage an isolated full-train Open3DSG runtime.
- run Docker preflight before raw dump launch.

Decision:

```text
full_train_runtime_preflight_ready
```

Runtime root:

```text
local_dataset/Open3DSG_staged/h002_train_full_runtime
```

Runtime stage result:

| Item | Count |
| --- | ---: |
| contexts | 3,738 |
| selected scans | 1,157 |
| linked scans | 1,157 |
| sequence-ready scans | 1,157 |
| missing feature contexts | 0 |

Docker preflight:

| Gate | Passed |
| --- | --- |
| checkpoint | true |
| runtime | true |
| scope | true |
| imports | true |

Raw dump contract:

```text
contract_ready_raw_dump_missing
```

Next document:

```text
56_full_train_raw_dump.md
```

### Stage 39. Full Train Raw Dump

Document:

```text
56_full_train_raw_dump.md
```

Purpose:

- launch the full-train Open3DSG raw dump in a resumable background session.
- keep log and exit files under `logs/`.
- block adapter export until raw dump completeness is verified.

Current status:

```text
full_train_raw_dump_complete
```

tmux session:

```text
h002_open3dsg_train_full_raw_20260615_180429
```

Log:

```text
logs/h002_open3dsg_train_full_raw_20260615_180429.log
```

Exit file:

```text
logs/h002_open3dsg_train_full_raw_20260615_180429.exit
```

Completion evidence:

| Item | Count / Status |
| --- | ---: |
| process exit code | 0 |
| stream manifest status | `raw_dump_stream_complete` |
| completed batches | 3,738 |
| raw rows | 186,218 |
| completed rows | 3,738 |

Raw repair/dedup:

| Item | Count / Status |
| --- | ---: |
| repair status | `ready` |
| input rows | 186,218 |
| output rows | 186,139 |
| duplicate groups | 79 |
| duplicate extra rows | 79 |
| malformed identity rows | 0 |
| noncontiguous subgraph repeats | 0 |

Key artifacts:

```text
artifacts/train_rga_full/open3dsg_train_full/raw_dump/raw.jsonl
artifacts/train_rga_full/open3dsg_train_full/raw_dump/raw.dedup.jsonl
artifacts/train_rga_full/open3dsg_train_full/raw_dump/stream_manifest.json
artifacts/train_rga_full/open3dsg_train_full/raw_dump/repair_manifest.json
```

Next document:

```text
57_full_train_adapter_export.md
```

### Stage 40. Full Train Adapter Export

Document:

```text
57_full_train_adapter_export.md
```

Purpose:

- convert repaired full-train Open3DSG raw rows into identity-preserving
  prediction rows.
- avoid the existing pilot exporter's list-in-memory path at full-train scale.
- preserve train subset provenance.
- keep validation/test closed.

Added tool:

```text
tools/export_full_train_adapter.py
```

Decision:

```text
full_train_adapter_export_ready
```

Result:

| Item | Count / Status |
| --- | ---: |
| contexts | 3,738 |
| raw rows read | 186,139 |
| prediction rows | 4,818,996 |
| subgraphs written | 3,738 |
| conversion errors | 0 |
| adapter warnings | 793 |
| `relationships_validation`/`h001_validation` in prediction provenance | no match |

Warning breakdown:

| Warning | Count |
| --- | ---: |
| `raw_edge_outside_context_filtered` | 786 |
| `same_endpoint_skipped` | 7 |

Key artifact:

```text
artifacts/train_rga_full/open3dsg_train_full/adapter/predictions.jsonl
```

Family prediction rows:

| Family | Rows |
| --- | ---: |
| `support_contact` | 556,038 |
| `proximity` | 185,346 |
| `relative_vertical` | 370,692 |
| `relative_horizontal` | 741,384 |
| `attachment_deferred` | 556,038 |
| `unsupported_first_pass` | 2,409,498 |

Next action:

```text
full_train_geometry_join
```

### Stage 41. Full Train Geometry Join

Document:

```text
58_full_train_geometry_join.md
```

Purpose:

- join full-train prediction rows with H001 frozen geometry verifier evidence.
- preserve all full-train prediction rows.
- produce deterministic geometry status and geometry-only `p_geom_valid`.
- keep validation/test closed.

Current status:

```text
full_train_geometry_join_ready_with_exit_file_caveat
```

tmux session:

```text
h002_open3dsg_train_full_geometry_20260616_120342
```

Input:

| Item | Count |
| --- | ---: |
| prediction rows | 4,818,996 |
| selected train scans | 1,157 |

Output root:

```text
artifacts/train_rga_full/open3dsg_train_full/geometry/
```

Completion gate:

```text
manifest.status = ready
counts.predictions = 4,818,996
counts.verification_rows = 4,818,996
counts.rows_preserved = true
errors = []
```

Result:

| Item | Count / Status |
| --- | ---: |
| manifest status | `ready` |
| verification rows | 4,818,996 |
| rows preserved | true |
| primary family rows | 1,112,076 |
| unsupported family rows | 3,706,920 |
| calibration scored rows | 1,112,076 |
| warnings | 9 |
| exit file | missing wrapper caveat |

Status counts:

| Status | Rows |
| --- | ---: |
| `satisfied` | 474,898 |
| `uncertain` | 490,410 |
| `violated` | 146,768 |
| `unsupported` | 3,706,920 |

Next action:

```text
full_train_rga_rows
```

### Stage 42. Full Train RGA Rows

Document:

```text
59_full_train_rga_rows.md
```

Purpose:

- join full-train prediction rows, geometry verification rows, and train GT
  relation labels.
- compute full-train RGA buckets and label-axis distribution.
- produce HL/LH queues for later controlled label mining.
- keep validation/test closed.

Current status:

```text
full_train_rga_rows_ready_with_exit_file_caveat
```

tmux session:

```text
h002_open3dsg_train_full_rga_20260616_161755
```

Input:

| Item | Count |
| --- | ---: |
| prediction rows | 4,818,996 |
| geometry rows | 4,818,996 |
| selected train contexts | 3,738 |
| selected train scans | 1,157 |
| selected GT relations | 79,704 |

Output root:

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
```

Completion gate:

```text
summary.status = ready
validation.rows_written = 4,818,996
validation.prediction_geometry_mismatches = 0
validation.validation_error_count = 0
```

Result:

| Item | Count / Status |
| --- | ---: |
| summary status | `ready` |
| prediction rows | 4,818,996 |
| geometry rows | 4,818,996 |
| rows written | 4,818,996 |
| prediction-geometry mismatches | 0 |
| validation errors | 0 |
| HL queue rows | 1,828 |
| LH queue rows | 455,598 |
| exit file | missing wrapper caveat |

Primary full-train RGA metrics:

| Metric | K=50 | K=100 |
| --- | ---: | ---: |
| `RGA-HL@K` | 3.02% | 4.96% |
| `RGA-valid@K` | 61.90% | 52.39% |
| `RGA-coverage@K` | 2.91% | 9.86% |
| `RGA-LH-tail@K` | 42.61% | 42.37% |

Full-train top100 buckets:

| Bucket | Rows |
| --- | ---: |
| `RGA-HH` | 19,300 |
| `RGA-HL` | 1,828 |
| `RGA-HU` | 15,714 |
| `RGA-HM` | 336,910 |
| `RGA-LH` | 455,598 |
| `RGA-LL` | 144,940 |
| `RGA-LU` | 474,696 |
| `RGA-LM` | 3,370,010 |

Next action:

```text
full_train_controlled_label_mining
```

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

The future multi-view extension is:

```text
P(R_e = 1 | S_e, G_3D_e, V_mv_e, C_e, U_e)
```

This is an evidence-axis extension, not a new scene graph generator.

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

## Current Open3DSG Full Train Instantiation

Scope:

```text
Open3DSG train full
3,738 train subgraphs
1,157 scans
4,818,996 prediction rows
```

Current completed stages:

- full-train source contract.
- isolated full-train runtime stage.
- Docker preflight.
- raw dump completion.
- raw repair/dedup.
- streaming adapter export.
- streaming geometry join.
- full-train RGA row construction.
- controlled HL/LH candidate mining.
- controlled codex label readiness.
- controlled `(codex_ver_full_train)` label fill.
- train-only posterior smoke.
- label-policy audit.
- independent blind label protocol.
- independent asset packet generation.
- asset packet gap audit.

Current full-train diagnostic status:

```text
full_train_independent_combiner_path_decision_factor_revision_first
```

Core finding:

- Full-train RGA exposes large bidirectional mismatch mass:
  `RGA-HL@100=4.96%`, `RGA-LH-tail@100=42.37%`.
- The controlled bootstrap target is executable with 173 binary rows.
- `factorized_reliability_posterior` is only slightly better than
  `semantic_plus_geometry` on the bootstrap target.
- `proposed_audit_role` and `label_match_status` recover the target almost
  perfectly, so the current target cannot validate posterior novelty.
- A rank/role-hidden independent label protocol is now ready.
- Independent asset packets are ready for 347/360 rows and partial for 13/360
  rows; label-facing leakage audit passes.
- Asset packet gap audit keeps 355/360 rows for label fill and excludes 5 rows
  before label fill.
- Independent label readiness passes on 355/360 rows: schema/path/leakage errors
  are 0, and the 179-row priority sheet is also ready.
- Codex-version independent label fill produces 355 labels with 283 binary-usable
  rows: 155 positive and 128 negative. These are bootstrap labels, not
  human-confirmed paper evidence.
- Independent label ingestion succeeds with 355 validated labels, 283 binary
  targets, and 0 schema errors, but a basic target probe detects hidden metadata
  correlation through `proposed_audit_role_hidden` (NMI 0.2897).
- Target-independence audit confirms the original 283-row target is risky, but
  `proposed_role_balanced_codex_ver` remains as a 158-row controlled slice with
  79 positive and 79 negative rows and no hidden group risk under the audit
  thresholds.
- Controlled posterior smoke on that slice is executable but shows no strong
  factorized advantage: grouped AUPRC delta is -0.0047 versus
  `semantic_plus_geometry`, -0.0039 versus `semantic_only`, and +0.1155 versus
  `geometry_only`.
- Controlled error analysis shows why the current combiner is not enough:
  factorized posterior creates more threshold mistakes than it fixes relative to
  `semantic_plus_geometry` (`factorized_wrong_sg_correct=10`,
  `factorized_correct_sg_wrong=1`). The failure is structured by relation family
  and mismatch direction, so the next method step should design a family-gated,
  residual, uncertainty-gated combiner rather than adding a larger generic
  classifier.
- Combiner upgrade design is now fixed as a train-only hypothesis-stage plan:
  first smoke `C1_residual_logit_calibrator`, `C2_family_gated_residual`, and
  `C3_uncertainty_gated_geometry`; defer generic high-capacity GBDT-style and
  graph factor rescoring until edge-local evidence is stronger.
- Combiner upgrade smoke shows no safe gain over `semantic_plus_geometry`:
  `C2_family_gated_residual` gives the best upgraded AUPRC delta (+0.0070) but
  worsens Brier (+0.0062), while `C3_uncertainty_gated_geometry` improves AUROC,
  Brier, and threshold transfer but lowers AUPRC. No upgraded view passes the
  pre-defined progression rule.
- Combiner upgrade error analysis identifies the blocker: C2 is a
  ranking-oriented family gate with calibration damage and support-contact
  overcorrection, while C3 is safer for threshold/Brier and promising for
  `relative_vertical` / high-semantic-low-geometry slices but hurts global
  support-contact ranking. This points to a path decision before adding model
  capacity.
- Path decision keeps H002 active but freezes the current posterior performance
  result as a negative/partial boundary. The selected next path is
  relation-family-specific factor revision before any new smoke. Generic
  high-capacity combiners remain deferred, and posterior improvement over
  `semantic_plus_geometry` remains a blocked claim.
- Factor revision design confirms that full-train raw geometry witness fields
  are available for `support_contact`, `relative_vertical`, and `proximity`, but
  not for unsupported families. The next step is to materialize revised factor
  blocks from continuous raw geometry evidence rather than using
  `geometry_status` as a reliability shortcut.
- Revised factor dataset materialization joins raw geometry witness fields for
  all 158 controlled rows and adds D1-D4 revised factor views with zero
  forbidden feature-key hits. This prepares the train-only revised factor smoke
  but still does not support any posterior performance claim.
- Revised factor smoke is positive under train-only scan-grouped folds:
  D1-D4 all improve over `semantic_plus_geometry`, with D4 reaching AUPRC
  +0.1241 and Brier -0.0462. This is promising hypothesis-stage evidence, but
  it remains blocked from paper-level posterior claims until error analysis,
  shortcut controls, and stronger independent labels are complete.
- Revised factor error analysis shows that D4's gain is not explained solely by
  `predicate_family`: a family-only offset control has almost no AUPRC gain,
  while raw-only witness control has strong train-only signal. This keeps the
  raw-witness factorization path alive but makes raw-witness shortcut controls
  the next required gate.
- Revised factor shortcut controls show that row-specific raw witness alignment
  matters: global raw-witness shuffle flips D4's AUPRC delta negative, and
  within-family shuffle leaves only a small fraction of the original gain.
  However, proximity remains unsafe as a ranking claim and typed family
  interaction still needs family-wise audit. The next gate is therefore claim
  boundary definition, not another capacity increase.
- Revised factor claim boundary is now fixed as a hypothesis-stage diagnostic
  claim. The selected scope is `support_contact + relative_vertical`; proximity
  is excluded from the main posterior claim and preserved as a failure/risk
  slice. The method boundary is `RGA-scoped raw-witness residual reliability
  layer`, not D4 typed family interaction as a final combiner.
- The selected support/vertical audit packet is ready: 127 selected train-only
  rows, 72 support_contact and 55 relative_vertical, all with label-ready
  evidence packets. Labeler-visible sheets expose relation candidate, raw
  witness values, and asset pointers, while hidden target-construction metadata
  is kept in a post-label internal reference only. Leakage audit is zero-hit.
- Support/vertical label readiness is ready for fill: the 127-row sheet passes
  header, path, hidden-reference, risk-slice, and leakage checks. Allowed review
  values and the label-to-binary policy are frozen in a completion schema.
- Support/vertical Codex-version label fill is complete for 127 selected rows:
  114 binary-usable labels, 40 positives, 74 negatives, and 13 excluded rows.
  The fill used only visible relation fields and raw witness values; hidden
  internal reference and target-construction metadata were not read. These are
  bootstrap labels, not human-confirmed paper evidence.
- Support/vertical label ingestion is complete with 127 validated labels, 114
  binary targets, 40 positives, 74 negatives, and 0 ingestion errors. The
  post-label probe detects hidden metadata correlation
  (`relation_validity_label_hidden` NMI 0.5710, `label_use_hidden` NMI 0.4506,
  `rank_band_hidden` NMI 0.2128), so posterior smoke remains blocked until a
  dedicated target-independence audit constructs or rejects a controlled slice.
- Support/vertical target-independence audit rejects a strict controlled target:
  no slice clears prior-label carryover from `relation_validity_label_hidden`
  and `label_use_hidden`. A 70-row `rank_band_balanced_codex_ver` construction-only
  diagnostic slice remains, but it is not sufficient for posterior method
  validation. The next gate is label-policy revision, not posterior smoke.
- Support/vertical label policy v2 is now defined: direct
  `independent_relation_label` is removed from the labeler surface, review is
  split into factual axes, and geometry validity / relation reliability targets
  are derived only after label lock. The v2 sheet has 127 rows, with 72
  support_contact and 55 relative_vertical rows.
- Support/vertical v2 label readiness is complete: the 127-row fill sheet passes
  schema, packet-path, family-partition, proximity-exclusion, and leakage checks.
  This unlocks factual-axis fill, not posterior training or paper-level claims.
- Support/vertical v2 factual-axis fill is complete: 127 rows are filled with
  endpoint, visibility, geometry answer, evidence strength, informativeness,
  ontology fit, and uncertainty fields. Direct reliability labels and binary
  targets are still absent; ingestion must derive targets only after label lock.
- Support/vertical v2 ingestion is complete: `geometry_validity_target_v2` has
  100 binary rows with 79 positives and 21 negatives, while
  `relation_reliability_target_v2` has 106 binary rows with 32 positives and 74
  negatives. Basic probe still finds hidden prior-label/construction correlation,
  so posterior smoke remains blocked until dedicated v2 target-independence audit.
- Support/vertical v2 target-independence audit is complete: no strict
  relation-reliability slice clears harmful prior-label carryover. A 62-row
  `rank_band_balanced_v2` construction-only relation slice remains for
  plumbing/error diagnostics, but it is not method-validation evidence.
- Support/vertical v2 target path decision is complete: do not run posterior
  smoke on the current target and do not keep revising rule-based Codex targets
  as the main next step. A 127-row independent collection sheet is ready, with
  hidden metadata and v2 Codex axes kept out of the labeler-visible surface.
- Support/vertical v2 independent label fill is complete as a
  `(codex_independent_ver)` visible-only bootstrap: 127 rows, 32 reliable, 70
  unreliable, and 25 uncertain. It does not read hidden manifest, v2 Codex axes,
  prior labels, score/rank, `p_geom_valid`, or geometry status. It is still not
  human-confirmed paper evidence.
- Support/vertical v2 independent label ingestion is complete with 127 validated
  labels and 102 binary rows per target. `geometry_validity_independent_target`
  has 81 positives / 21 negatives, while `relation_reliability_independent_target`
  has 32 positives / 70 negatives. Basic probe still flags hidden prior-label
  and construction correlation, so posterior smoke remains blocked until a
  dedicated independent target-independence audit constructs or rejects a strict
  slice. Source score/rank and `p_geom_valid` feature join is also pending.
- Support/vertical v2 independent target-independence audit is complete: no
  strict relation-reliability slice clears harmful prior-label carryover. A
  62-row `rank_band_balanced_independent` relation slice remains for
  plumbing/error diagnostics, but it is not posterior method-validation evidence.
  This makes the next gate human-confirmed support/vertical label design or a
  fundamentally revised target path, not another immediate posterior smoke.
- Support/vertical v2 human label path decision is complete: stop treating
  another Codex-derived target revision as the main path. The recommended next
  evidence is a 127-row human-confirmed support/vertical batch; a 96-row minimum
  batch is acceptable only as a first pass and must expand if target independence
  fails. The generated sheets keep hidden metadata, prior labels, source scores,
  `p_geom_valid`, and v2 Codex axes out of the labeler-visible surface.
- Support/vertical v2 human label fill is complete as a Codex proxy at user
  request. The workflow treats the filled rows as human-confirmed for the next
  hypothesis steps, but provenance remains `codex_proxy_user_review_pending`.
  The full batch has 127 rows, 102 binary rows, 32 positive reliability labels,
  70 negative reliability labels, and 25 uncertain rows.
- Support/vertical v2 human label ingestion is complete with 127 validated rows.
  `geometry_validity_human_target` has 102 binary rows with 81 positives / 21
  negatives. `relation_reliability_human_target` has 102 binary rows with 32
  positives / 70 negatives. Basic probe still flags hidden metadata correlation
  risk, so posterior smoke remains blocked until a dedicated human-target
  independence audit.
- Support/vertical v2 human target-independence audit is complete: no strict
  relation-reliability slice clears harmful prior-label carryover. A 62-row
  `rank_band_balanced_human` relation slice exists as construction diagnostic,
  but not posterior method-validation evidence. The current blocker is target
  and evidence independence, not combiner capacity.
- Support/vertical v2 external review protocol is ready: 127 rows, 124 ready
  packets, 3 `ready_with_packet_caveat` rows, 0 packet path errors, and 0
  labeler-header leakage hits. The revised sheet hides numeric witness values,
  previous proxy labels, hidden prior labels, source rank/score, `p_geom_valid`,
  geometry status, and v2 reference axes. Multi-view/mesh/contact evidence is
  used only for audit/labeling, not as posterior input.
- Support/vertical v2 external review fill is complete as a user-requested
  Codex proxy: 127 rows, 47 reliable, 69 unreliable, 11 uncertain, and 0 schema
  validation errors. The fill did not read hidden manifest, numeric witness
  values, previous proxy labels, source score/rank, or `p_geom_valid`. It is
  treated as user review for workflow progression, but not paper-level external
  human annotation before user confirmation.
- Support/vertical v2 external review ingestion is complete: 127 labels, 116
  binary `geometry_validity_external_target` rows with 105 positives / 11
  negatives, and 116 binary `relation_reliability_external_target` rows with 47
  positives / 69 negatives. Relation reliability has 0 visible non-target
  shortcut flags in the basic probe, but still has 5 hidden correlation risks,
  so posterior smoke remains blocked until dedicated target-independence audit.
- Support/vertical v2 external review target-independence audit is complete:
  no strict relation-reliability slice clears harmful prior-label carryover. A
  70-row `rank_band_balanced_external` relation slice exists as a better
  construction diagnostic with 35/35 class balance and 0 construction,
  geometry-alignment, and visible non-target risks, but it still has 3 harmful
  prior risks. Posterior smoke remains blocked.
- Support/vertical v2 true user review path is ready: proxy labels are stopped
  as method-validation evidence. The recommended first pass is the 70-row
  `rank_band_balanced_external` batch, with 0 header leakage hits, 0 packet path
  errors, and post-label-only hidden manifests. A full 127-row optional
  expansion sheet is also available.
- Endpoint-controlled candidate mining is complete for the support/vertical
  revised sampling path: the capped strict endpoint deficit requested 62 labels,
  and mining selected 53 packet-ready plus 9 asset-needed train-only candidates
  with residual unfilled 0. This does not train a posterior and does not make
  endpoint fields deployable model inputs; it only prepares a target-repair
  batch before the next smoke.
- Endpoint-controlled asset packet generation is complete: the 9 asset-needed
  candidates were packetized, the full 62-row label sheet is packet-ready, packet
  path errors are 0, and label-surface leakage passes. This unlocks label fill,
  not posterior smoke.
- Endpoint-controlled label fill is complete as a Codex proxy: 62 rows, 2
  reliable, 32 unreliable, 28 uncertain, and 0 validation errors. This unlocks
  ingestion and target-independence audit only; the positive-sparse target is
  not ready for posterior smoke.

## Claim Boundary

Allowed current claim:

```text
RGA provides a train-only framework for separating semantic confidence,
geometric satisfiability, coverage, uncertainty, and label/audit evidence at
relation-edge level.
```

Allowed current diagnostic claim:

```text
On the Open3DSG train full split, RGA exposes both high-semantic/low-geometry
and low-semantic/high-geometry states. The low-semantic/high-geometry state is
large but requires independent audit because it mixes true underconfidence,
annotation sparsity, ontology mismatch, and dense relation noise.
```

Allowed current revised-factor diagnostic claim:

```text
Train-only diagnostics show that semantic score and legacy p_geom_valid are not
sufficient as the main geometry evidence, while typed relation-specific raw
witness evidence gives a positive posterior smoke signal on the revised
all-label-ready support/vertical slice.
```

Allowed current method-boundary claim:

```text
The defensible H002 method boundary is an RGA-scoped typed raw-witness residual
reliability layer for support_contact and relative_vertical. The exact posterior
combiner remains unsettled because C3 linear v2 remains the strongest train-only
reference after the C4-C7 combiner smoke, C4 only improves calibration/Brier while
losing AUPRC and threshold transfer, C6/C7 trade support_contact loss for partial
relative_vertical gains, and combiner error analysis shows that endpoint-only
controls explain the current target slice more strongly than the typed
raw-witness posterior. Endpoint-controlled resampling is now planned with strict
`endpoint_flag_pattern` matching, but the current all-label-ready pool is too
small after strict matching, so label expansion is required before another
posterior smoke. Endpoint-controlled candidate mining showed that the capped
deficit is coverable, and endpoint-controlled asset packet generation removed
the packet blocker by preparing a full 62-row packet-ready label sheet. Label
fill is now complete but yields only 2 reliable labels, so ingestion and
target-independence audit must determine whether this is a usable target or a
failure diagnosis before any new posterior smoke.
```

Blocked claims:

- RGA itself improves relation prediction.
- RGA-LH rows are automatically valid missing positives.
- working labels are paper-locked human annotations.
- `p_geom_valid` is full relation reliability.
- the factorized posterior is paper-level superior to rank-controlled baselines.
- proximity is a safe main ranking claim.
- typed family interaction is the final method design.
- the current `(codex_ver_full_train)` bootstrap target validates posterior
  novelty.
- blind labels are human-confirmed.
- codex-proxy human fields are independent external human annotations before
  user confirmation.
- user-requested Codex external-review fill is paper-level external human
  annotation before user confirmation.
- Codex-filled true-user review is paper-level true user/external annotation before
  user confirmation.
- ingested Codex-proxy true-user review targets validate posterior novelty before
  target-independence audit.
- construction-only true-user review slices validate posterior method novelty.
- upgrading the posterior combiner solves the current H002 blocker before target/evidence
  independence is fixed.
- proxy-only labels validate the posterior method after the true-user path has
  been opened.
- label-ready status is a relation reliability label.
- codex-version independent labels alone validate posterior novelty.
- user-submitted packet-only labels validate posterior novelty without reviewer-independence
  confirmation and controlled target-independence evidence.
- changing only reviewer provenance on the current 70-row labels is sufficient to open
  posterior smoke.
- user confirmation alone resolves the H002 target-independence blocker.
- simply expanding the same full-127 protocol is enough to open posterior smoke.
- endpoint/object-type features are valid deployable reliability evidence.
- a stronger or higher-capacity combiner should be tested before endpoint-controlled
  target repair.
- family-separated posterior is the immediate next method step before endpoint
  shortcut is reduced.
- endpoint-controlled ingestion with `2/32` relation-reliability target balance is
  enough to run posterior smoke.
- endpoint-controlled target audit with no strict/diagnostic slice validates the
  posterior method.
- geometry validity can replace relation reliability as the main H002 target.
- relaxing reliability to geometry-supported is a valid shortcut.
- held-out validation/test conclusions.

## Endpoint-Controlled Label Ingestion

2026-06-20 KST에 `endpoint_controlled_label_ingestion`을 진행했다. 이 단계는
packet-ready `62`-row Codex-proxy sheet를 target artifact로 변환하고, label lock
이후 hidden endpoint manifest를 join해 target balance와 shortcut risk를 확인했다.
Posterior model은 학습하지 않았다.

Result:

```text
status = h002_endpoint_controlled_label_ingested_positive_sparse
labels = 62
geometry_validity_binary = 34
geometry_validity_positive_negative = 23/11
relation_reliability_binary = 34
relation_reliability_positive_negative = 2/32
ingestion_errors = 0
validation_used = False
test_used = False
next = endpoint_controlled_target_independence_audit
```

Interpretation:

- The geometry-validity target has usable diagnostic mass, but relation
  reliability is severely positive-sparse.
- This confirms the H002 distinction that `geometry validity != relation
  reliability`.
- The artifact is not posterior method evidence. It is a target viability and
  failure-diagnosis artifact.
- The next step must audit target independence and construction shortcuts before
  any posterior smoke.

## Endpoint-Controlled Target Independence Audit

2026-06-20 KST에 `endpoint_controlled_target_independence_audit`을 진행했다.
이 단계는 endpoint-controlled ingestion target이 posterior smoke로 넘어갈 수 있는지
검증했다.

Result:

```text
status = h002_endpoint_controlled_target_independence_audit_blocked_positive_sparse
relation_rows = 34
relation_positive_negative = 2/32
relation_majority_baseline = 0.9412
validation_errors = 0
relation_strict_slice = none
relation_diagnostic_slice = none
validation_used = False
test_used = False
next = endpoint_controlled_target_path_decision
```

Interpretation:

- Endpoint-controlled sampling did not produce a posterior-ready reliability
  target.
- Relation reliability has only 2 positives, so a negative-majority predictor
  already reaches `0.9412`.
- Hidden endpoint pattern, construction role/rank, and visible predicate effects
  remain entangled with the target, but the dominant blocker is positive sparsity.
- Geometry validity has more target mass (`23/11`) but still lacks a strict
  controlled slice at this size.
- This is a target-construction failure, not evidence that a stronger posterior
  combiner is needed.

## Endpoint-Controlled Target Path Decision

2026-06-20 KST에 `endpoint_controlled_target_path_decision`을 진행했다. 이 단계는
posterior smoke를 진행할지, combiner를 바꿀지, target/sampling을 수정할지 결정했다.

Result:

```text
status = h002_endpoint_controlled_target_path_decision_revise_target_v3_positive_anchor_sampling
selected = revise_reliability_target_v3_and_positive_anchor_sampling
relation_reliability_positive_negative = 2/32
geometry_validity_positive_negative = 23/11
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_positive_anchor_plan
```

Decision:

- Do not run posterior smoke now.
- Do not upgrade the combiner now.
- Do not replace relation reliability with geometry validity.
- Do not relax reliability to simply mean geometry-supported.
- Revise relation reliability as a v3 multi-axis target.
- Mine positive-anchor candidates under train-only controls.

Interpretation:

The endpoint-controlled artifact does not show semantic-geometry agreement is
good. It shows that the current binary relation-reliability target collapses too
many states into negative: uncertain, trivial-dense, ontology mismatch, and
geometry contradiction. H002 should therefore preserve the distinction
`geometry validity != relation reliability`, but fix the target schema before
testing any posterior.

## Reliability Target V3 Positive-Anchor Plan

2026-06-20 KST에 `reliability_target_v3_positive_anchor_plan`을 진행했다. 이 단계는
posterior smoke가 아니라 v3 target schema와 positive-anchor label sheet를 준비한 것이다.

Result:

```text
status = h002_reliability_target_v3_positive_anchor_plan_ready
selected_rows = 160
label_surface_leakage_hits = 0
packet_path_errors = 0
validation_used = False
test_used = False
next = reliability_target_v3_label_fill
```

V3 target axes:

| Axis | Values |
| --- | --- |
| `endpoint_identity_v3` | `both_valid`, `subject_invalid`, `object_invalid`, `pair_invalid`, `uncertain` |
| `pair_evaluability_v3` | `evaluable`, `partially_evaluable`, `not_evaluable`, `uncertain` |
| `geometry_support_v3` | `supports_predicate`, `contradicts_predicate`, `ambiguous`, `not_evaluable` |
| `relation_usefulness_v3` | `informative`, `trivial_dense_or_room_structure`, `ontology_mismatch`, `uncertain` |
| `relation_reliability_v3` | `reliable`, `unreliable_geometry`, `unreliable_trivial`, `unreliable_ontology`, `uncertain` |

Sampling buckets:

| Bucket | Rows | Support | Vertical | Unique Scans |
| --- | ---: | ---: | ---: | ---: |
| `reliable_positive_anchor` | 40 | 20 | 20 | 32 |
| `geometry_contradiction_negative` | 40 | 20 | 20 | 31 |
| `trivial_dense_negative` | 40 | 20 | 20 | 21 |
| `ontology_or_uncertain_negative` | 40 | 30 | 10 | 21 |

Interpretation:

- This keeps `semantic score != geometry validity != relation reliability`.
- It does not convert all geometry-supported rows into reliable positives.
- It separates reliable positives from geometry contradiction, trivial dense
  relation, and ontology/granularity mismatch.
- The label sheet hides endpoint pattern, queue, rank, source score,
  `p_geom_valid`, geometry status, label-match status, and expected role.
- Posterior smoke remains blocked until v3 labels are filled, ingested, and
  target-independence is audited.
- This is train-only hypothesis-stage evidence, not paper-level posterior
  performance evidence.

## Reliability Target V3 Label Fill

2026-06-20 KST에 `reliability_target_v3_label_fill`을 진행했다. 사용자가 직접 채워야 하는
단계로 남기지 않고, 사용자 요청에 따라 Codex proxy로 160-row v3 sheet를 채웠다.

Result:

```text
status = h002_reliability_target_v3_label_filled_codex_proxy_user_requested
rows = 160
reliable = 32
unreliable_geometry = 21
unreliable_trivial = 57
unreliable_ontology = 0
uncertain = 50
validation_errors = 0
validation_used = False
test_used = False
next = reliability_target_v3_label_ingestion
```

Axis counts:

| Axis Value | Count |
| --- | ---: |
| `geometry_support_v3=supports_predicate` | 92 |
| `geometry_support_v3=contradicts_predicate` | 21 |
| `geometry_support_v3=ambiguous` | 47 |
| `relation_usefulness_v3=informative` | 34 |
| `relation_usefulness_v3=trivial_dense_or_room_structure` | 58 |
| `relation_usefulness_v3=ontology_mismatch` | 21 |
| `relation_usefulness_v3=uncertain` | 47 |

Post-label hidden bucket diagnostic:

| Hidden Bucket | Rows | Reliable | Unreliable Geometry | Unreliable Trivial | Uncertain |
| --- | ---: | ---: | ---: | ---: | ---: |
| `reliable_positive_anchor` | 40 | 7 | 0 | 8 | 25 |
| `geometry_contradiction_negative` | 40 | 1 | 18 | 14 | 7 |
| `trivial_dense_negative` | 40 | 10 | 3 | 19 | 8 |
| `ontology_or_uncertain_negative` | 40 | 14 | 0 | 16 | 10 |

Interpretation:

- Codex proxy fill did not use hidden sampling role, expected role, score/rank,
  `p_geom_valid`, geometry status, label-match status, or numeric witness values
  for label decisions.
- Hidden manifest was joined only after fill for diagnostic bucket counts.
- Positive-anchor sampling increased label coverage, but the positive-anchor
  bucket is not automatically reliable under visible-heuristic proxy labels.
- This strengthens the need for ingestion and target-independence audit before
  reopening posterior smoke.
- This is not independent human annotation and not paper-level evidence.

## Reliability Target V3 Label Ingestion

2026-06-20 KST에 `reliability_target_v3_label_ingestion`을 진행했다. 이 단계는 completed
v3 sheet를 ingest하고, reliability / geometry / usefulness target을 분리해 materialize했다.
Posterior는 학습하지 않았다.

Result:

```text
status = h002_reliability_target_v3_label_ingested_with_probe_risk
rows = 160
ingestion_errors = 0
validation_used = False
test_used = False
next = reliability_target_v3_target_independence_audit
```

Binary target counts:

| Target | Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `relation_reliability_v3_binary_target` | 110 | 32 | 78 | 0.2909 | 50 |
| `geometry_support_v3_binary_target` | 113 | 92 | 21 | 0.8142 | 47 |
| `relation_usefulness_v3_binary_target` | 113 | 34 | 79 | 0.3009 | 47 |

Probe result:

| Target | Probe Status | Hidden Risks | Visible Risks |
| --- | --- | ---: | ---: |
| `relation_reliability_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 7 | 2 |
| `geometry_support_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 7 | 4 |
| `relation_usefulness_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 7 | 2 |

Interpretation:

- The positive-sparse target problem is improved: relation reliability now has
  `32` positives and `78` negatives.
- However, target-independence is not solved. `endpoint_flag_pattern_hidden`,
  `sampling_category_hidden`, `geometry_status_hidden`, `label_match_status_hidden`,
  `subject_label`, and `object_label` remain shortcut risks.
- The target is therefore materialized but not posterior-ready.
- The next step must be dedicated target-independence audit, not posterior smoke.
- This remains train-only hypothesis-stage evidence and not paper-level human
  annotation evidence.

## Reliability Target V3 Target Independence Audit

2026-06-20 KST에 `reliability_target_v3_target_independence_audit`을 진행했다. 이
단계는 v3 target의 positive mass가 아니라 target independence를 확인했다. Posterior는
학습하지 않았다.

Result:

```text
status = h002_reliability_target_v3_target_independence_audit_blocked_no_controlled_slice
relation_rows = 110
relation_pos = 32
relation_neg = 78
errors = 0
relation_strict = none
relation_diagnostic = none
validation_used = False
test_used = False
next = reliability_target_v3_path_decision
```

Per-target decisions:

| Target | Status | Rows | Pos | Neg | Strict Slice | Diagnostic Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `relation_reliability_v3_binary_target` | `blocked_no_controlled_slice` | 110 | 32 | 78 | `none` | `none` |
| `geometry_support_v3_binary_target` | `blocked_no_controlled_slice` | 113 | 92 | 21 | `none` | `none` |
| `relation_usefulness_v3_binary_target` | `blocked_no_controlled_slice` | 113 | 34 | 79 | `none` | `none` |

Main reliability target risks:

| Risk | Key | Majority Acc | NMI | Pos Rate Range |
| --- | --- | ---: | ---: | ---: |
| endpoint pattern | `endpoint_flag_pattern_hidden` | 0.9182 | 0.5978 | 1.0000 |
| visible object identity | `object_label` | 0.9545 | 0.8587 | 1.0000 |
| visible object identity | `subject_label` | 0.9091 | 0.7070 | 1.0000 |
| hidden provenance | `sampling_category_hidden` | 0.7091 | 0.1640 | 0.4364 |
| construction | `rank_band_hidden` | 0.7182 | 0.1680 | 0.6667 |
| expected geometry alignment | `geometry_status_hidden` | 0.7091 | 0.1499 | 0.3723 |

Interpretation:

- v3 target은 positive-sparse 문제를 줄였지만 posterior-ready target independence를
  확보하지 못했다.
- `sampling_category_balanced_v3`와 `rank_band_balanced_v3` 같은 balanced slice는
  존재하지만 endpoint/object shortcut risk를 제거하지 못한다.
- Endpoint/object-balanced slice는 너무 작거나 construction risk가 남는다.
- 따라서 다음 단계는 posterior smoke나 combiner upgrade가 아니라 path decision이다.

## Reliability Target V3 Path Decision

2026-06-20 KST에 `reliability_target_v3_path_decision`을 진행했다. 이 단계는 posterior
smoke를 열지, combiner를 바꿀지, 아니면 target pool 자체를 다시 통제할지 결정했다.

Result:

```text
status = h002_reliability_target_v3_path_decision_object_endpoint_controlled_sampling_first
selected = revise_v3_object_endpoint_controlled_sampling
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_object_endpoint_controlled_plan
```

Decision:

- posterior smoke를 실행하지 않는다.
- combiner upgrade도 진행하지 않는다.
- `geometry_support_v3_binary_target`을 main reliability target으로 쓰지 않는다.
- v3 multi-axis label schema는 유지한다.
- 다음 label pool은 object/endpoint-controlled sampling으로 다시 만든다.

Interpretation:

The current issue is not model capacity. The relation reliability target has
positive mass, but target independence is not established. Object labels are
valid relation context, yet if subject/object label or endpoint flag can explain
the target almost alone, H002 cannot claim that semantic/geometry/coverage
factors are being combined into reliability. Therefore the next step controls
object and endpoint strata before any feature join or posterior smoke.

## Reliability Target V3 Object/Endpoint-Controlled Plan

2026-06-20 KST에 `reliability_target_v3_object_endpoint_controlled_plan`을 진행했다.
이 단계는 label fill이나 posterior가 아니라, object/endpoint shortcut을 끊기 위한
sampling cell feasibility를 계산했다.

Result:

```text
status = h002_reliability_target_v3_object_endpoint_controlled_plan_ready_broader_mining_required
candidate rows = 302
strict subject/object/family eligible rows = 73
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_object_endpoint_candidate_mining
```

Cell feasibility:

| Cell Type | Cells | Eligible Cells | Strong Cells | Eligible Rows | Pos Proxy | Neg Proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `subject_object_family` | 139 | 12 | 3 | 73 | 36 | 37 |
| `subject_object` | 119 | 13 | 3 | 89 | 46 | 43 |
| `object_family` | 54 | 10 | 4 | 163 | 91 | 72 |
| `object_predicate` | 89 | 5 | 2 | 73 | 22 | 51 |
| `endpoint_family` | 12 | 10 | 6 | 274 | 194 | 80 |

Recommended tiers:

| Tier | Suggested Total |
| --- | ---: |
| `T1_strict_subject_object_family` | 51 |
| `T2_object_family_fallback` | 42 |
| `T3_endpoint_family_balance` | 65 |

Interpretation:

- Strict object-matched cells are necessary but not sufficient.
- `object_family` and `endpoint_family` fallback tiers are required to reach a
  practical next label pool.
- Candidate-positive/negative proxy is a sampling stratum only, not a label.
- The next step is candidate mining into a label sheet with post-label-only
  hidden manifest.

## Reliability Target V3 Object/Endpoint Candidate Mining

2026-06-20 KST에 `reliability_target_v3_object_endpoint_candidate_mining`을 진행했다.
이 단계는 label fill이나 posterior가 아니라, recommended object/endpoint control cell을
실제 train-only v3 label sheet로 변환한 것이다.

Result:

```text
status = h002_reliability_target_v3_object_endpoint_candidate_mining_ready_with_selection_deficit
requested rows = 158
selected rows = 130
selection residual = 28
candidate-positive proxy strata = 68
candidate-negative proxy strata = 62
label_surface_leakage_hits = 0
packet_path_errors = 0
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_object_endpoint_label_fill
```

Tier summary:

| Tier | Rows | Pos Proxy | Neg Proxy | support_contact | relative_vertical | Unique Scans |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `T1_strict_subject_object_family` | 50 | 25 | 25 | 22 | 28 | 29 |
| `T2_object_family_fallback` | 31 | 14 | 17 | 23 | 8 | 27 |
| `T3_endpoint_family_balance` | 49 | 29 | 20 | 32 | 17 | 33 |

Interpretation:

- The label sheet is ready for hypothesis-stage v3 label fill.
- The 28-row residual comes from tier overlap plus duplicate-pair / scan-diversity controls.
- Proxy class, sampling tier/cell, semantic score/rank, `p_geom_valid`, geometry status,
  label-match status, endpoint flag pattern, and matched-predicate hints are not labeler-visible.
- Hidden construction fields are stored only in the post-label manifest.
- This is not posterior evidence; posterior smoke remains blocked until label fill, ingestion,
  and target-independence audit pass.

## Reliability Target V3 Object/Endpoint Label Fill

2026-06-20 KST에 `reliability_target_v3_object_endpoint_label_fill`을 진행했다.
이 단계는 object/endpoint-controlled `130`-row sheet를 hypothesis-stage Codex proxy로
채운 것이다.

Result:

```text
status = h002_reliability_target_v3_object_endpoint_label_filled_codex_proxy_user_requested
rows = 130
reliable = 8
unreliable_geometry = 26
unreliable_trivial = 73
unreliable_ontology = 0
uncertain = 23
input_errors = 0
fill_validation_errors = 0
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_object_endpoint_label_ingestion
```

Interpretation:

- `supports_predicate` and `relation_reliability` are now explicitly separated.
- `85` rows support the geometry predicate, but only `8` rows are reliable because
  `75` rows are `trivial_dense_or_room_structure`.
- The label distribution may still be positive-sparse for the main reliability target.
- The next step must ingest the labels and audit target independence before any posterior smoke.

## Reliability Target V3 Object/Endpoint Label Ingestion

2026-06-20 KST에 `reliability_target_v3_object_endpoint_label_ingestion`을 진행했다.
이 단계는 채워진 `130`개 v3 label을 ingest하고, reliability / geometry-support /
usefulness target을 분리해 만든 것이다.

Result:

```text
status = h002_reliability_target_v3_object_endpoint_label_ingested_positive_sparse_with_probe_risk
rows = 130
relation reliability target = 107 rows, 8 positive, 99 negative
geometry support target = 111 rows, 85 positive, 26 negative
relation usefulness target = 111 rows, 10 positive, 101 negative
ingestion_errors = 0
probe = target_independence_risk_hidden_metadata_correlated
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_object_endpoint_target_independence_audit
```

Interpretation:

- `geometry_support_v3_binary_target` has usable mass, but the main
  `relation_reliability_v3_binary_target` is positive-sparse.
- The quick probe flags hidden/visible shortcut risk, but it is imbalance-sensitive
  because the reliability target has only `8/107` positives.
- The next audit must separate true shortcut risk from positive-sparse majority-baseline artifact.
- Posterior smoke remains blocked.

## Reliability Target V3 Object/Endpoint Target Independence Audit

2026-06-20 KST에 `reliability_target_v3_object_endpoint_target_independence_audit`을
진행했다. 이 단계는 object/endpoint-controlled v3 target failure가 실제 shortcut인지,
positive-sparse target artifact인지 분리하기 위한 train-only 감사다. Posterior smoke는
실행하지 않았다.

Result:

```text
status = h002_reliability_target_v3_object_endpoint_target_independence_audit_reliability_blocked_geometry_support_available
relation reliability target = 107 rows, 8 positive, 99 negative, blocked_positive_sparse
geometry support target = 111 rows, 85 positive, 26 negative, blocked_no_controlled_slice
relation usefulness target = 111 rows, 10 positive, 101 negative, blocked_positive_sparse
validation_errors = 0
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_object_endpoint_path_decision
```

Interpretation:

- Main `relation_reliability_v3_binary_target`은 positive가 `8/107`뿐이라 posterior-ready가
  아니다.
- `relation_usefulness_v3_binary_target`도 `10/111` positive라 같은 positive-sparse
  문제가 있다.
- `geometry_support_v3_binary_target`은 `85/26`으로 mass가 있지만 strict/diagnostic
  controlled slice가 없으므로, relation reliability target을 대체하면 안 된다.
- 현재 병목은 posterior 결합 방식이 아니라 posterior가 배울 target 정의와 샘플링이다.

## Reliability Target V3 Object/Endpoint Path Decision

2026-06-20 KST에 `reliability_target_v3_object_endpoint_path_decision`을 진행했다.
이 단계는 object/endpoint-controlled v3 target audit 이후 posterior를 열지, geometry-support를
main target으로 바꿀지, 또는 target/sampling을 다시 고칠지 결정한 것이다. Posterior smoke와
combiner upgrade는 실행하지 않았다.

Result:

```text
status = h002_reliability_target_v3_object_endpoint_path_decision_informative_anchor_sampling
selected = revise_v3_informative_positive_anchor_sampling
relation reliability target = 107 rows, 8 positive, 99 negative
geometry supports-predicate rows = 85
unreliable_trivial rows = 73
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v3_informative_anchor_plan
```

Interpretation:

- Geometry-support를 main target으로 바꾸면 H002의 핵심 구분인
  `semantic score != geometry validity != relation reliability`가 사라진다.
- 같은 object/endpoint sampling을 더 모으면 reliable positive보다 trivial negative가 더
  많이 늘 가능성이 크다.
- 현재 남은 병목은 object/endpoint shortcut만이 아니라 `trivial room/surface relation`
  dominance다.
- 따라서 다음 단계는 object/endpoint control을 유지하면서 informative reliable positive anchor를
  별도로 찾는 sampling plan이다.
- informative-anchor mining도 controlled reliability target을 만들지 못하면 H002는 posterior
  method claim이 아니라 RGA diagnostic/decomposition framework로 정리한다.

## Reliability Target V3 Informative Anchor Plan

2026-06-20 KST에 `reliability_target_v3_informative_anchor_plan`을 진행했다. 이 단계는
object/endpoint control을 유지하면서 `floor`, `wall`, `ceiling` 중심 trivial relation을
cap하고, informative reliable positive가 될 가능성이 높은 row를 별도 sampling category로
mine하기 위한 plan이다. Label fill과 posterior는 실행하지 않았다.

Result:

```text
status = h002_reliability_target_v3_informative_anchor_plan_ready_with_asset_requests
full train support/vertical rows = 286102
informative positive proxy rows = 87054
geometry contradiction negative proxy rows = 1828
trivial room/surface negative proxy rows = 180518
uncertain/ontology proxy rows = 16702
selected seed rows = 160
selected packet-ready rows = 126
selected asset-needed rows = 34
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v3_informative_anchor_candidate_mining
```

Interpretation:

- Informative positive proxy 후보는 충분히 존재한다.
- 기존 object/endpoint attempt에서 빠진 것은 geometry support 자체가 아니라 non-trivial
  reliable relation positive를 적극적으로 찾는 sampling axis다.
- Selected seed는 `40/40/40/40` category로 구성한다:
  informative positive, geometry contradiction negative, trivial room/surface negative,
  uncertain/ontology negative.
- `floor`, `wall`, `ceiling`은 제거하지 않고 trivial negative로 cap한다.
- 34개 seed는 asset packet이 필요하므로 다음 candidate mining 단계에서 packet request 또는
  packet-ready-only fallback을 명시해야 한다.
- Posterior reopen gate는 그대로 유지한다.

## Reliability Target V3 Informative Anchor Candidate Mining

2026-06-20 KST에 `reliability_target_v3_informative_anchor_candidate_mining`을 진행했다.
이 단계는 informative-anchor plan의 160개 train-only seed를 실제 label sheet로 바꾸고,
labeler에게 보이면 안 되는 proxy/sampling field를 post-label manifest로 분리하는 단계다.
Label fill과 posterior는 실행하지 않았다.

Result:

```text
status = h002_reliability_target_v3_informative_anchor_candidate_mining_ready_needs_asset_packets
full label sheet rows = 160
packet-ready fallback label sheet rows = 126
asset-needed rows = 34
unique scans = 94
unique physical pairs = 160
support_contact rows = 76
relative_vertical rows = 84
label-surface leakage hits = 0
packet path errors = 0
validation errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v3_informative_anchor_asset_packets
```

Category summary:

| Category | Rows | Packet Ready | Asset Needed | support_contact | relative_vertical | Unique Scans |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `informative_reliable_positive_proxy` | 40 | 40 | 0 | 18 | 22 | 20 |
| `geometry_contradiction_negative_proxy` | 40 | 40 | 0 | 24 | 16 | 31 |
| `trivial_room_surface_negative_proxy` | 40 | 21 | 19 | 18 | 22 | 31 |
| `uncertain_or_ontology_negative_proxy` | 40 | 25 | 15 | 16 | 24 | 28 |

Interpretation:

- Preferred route는 160-row full sheet를 유지하는 것이다.
- Packet-ready-only fallback은 126 rows로 가능하지만, trivial room/surface negative와
  uncertain/ontology negative가 각각 21/40, 25/40으로 줄어든다.
- 따라서 fallback은 category coverage caveat가 붙는 진단용 route이고, primary route는 34개
  asset packet을 먼저 생성하거나 연결한 뒤 full sheet를 채우는 것이다.
- Candidate mining은 target을 만든 것이 아니라 label surface를 준비한 단계다. Posterior smoke는
  label fill, ingestion, target-independence audit이 통과하기 전까지 계속 block한다.

Main artifacts:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/150_reliability_target_v3_informative_anchor_candidate_mining.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_candidate_mining.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/informative_anchor_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/informative_anchor_packet_ready_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/informative_anchor_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/asset_request_plan.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_candidate_mining/category_summary.csv
```

## Reliability Target V3 Informative Anchor Asset Packets

2026-06-20 KST에 `reliability_target_v3_informative_anchor_asset_packets`을 진행했다.
이 단계는 informative-anchor candidate mining에서 남아 있던 34개 `asset_needed` row에 대해
multi-view/mesh/contact evidence packet을 생성하고, 기존 packet-ready 126개와 합쳐 full
160-row label sheet를 packet-complete 상태로 만드는 단계다. Label fill과 posterior는 실행하지
않았다.

Result:

```text
status = h002_reliability_target_v3_informative_anchor_asset_packets_ready
input selected rows = 160
asset-needed input rows = 34
generated packet rows = 34
generated non-ready rows = 0
full label sheet rows = 160
ready label rows = 160
packet path errors = 0
label-surface leakage hits = 0
validation errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v3_informative_anchor_label_fill
```

Category summary:

| Category | Rows | Ready | Generated | Existing | support_contact | relative_vertical | Unique Scans |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `geometry_contradiction_negative_proxy` | 40 | 40 | 0 | 40 | 24 | 16 | 31 |
| `informative_reliable_positive_proxy` | 40 | 40 | 0 | 40 | 18 | 22 | 20 |
| `trivial_room_surface_negative_proxy` | 40 | 40 | 19 | 21 | 18 | 22 | 31 |
| `uncertain_or_ontology_negative_proxy` | 40 | 40 | 15 | 25 | 16 | 24 | 28 |

Interpretation:

- Preferred route인 full 160-row informative-anchor label fill이 가능해졌다.
- 이전 blocker는 target definition이 아니라 34개 row의 packet 부재였다.
- 이 단계는 posterior evidence가 아니라 label-readiness evidence다.
- Posterior smoke는 label fill, ingestion, target-independence audit이 통과하기 전까지 계속 block한다.

Main artifacts:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/151_reliability_target_v3_informative_anchor_asset_packets.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_asset_packets.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/informative_anchor_full_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/informative_anchor_full_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/generated_packet_manifest.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/asset_needed_manifest_with_packets_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/category_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_asset_packets/packets/
```

## Reliability Target V3 Informative Anchor Label Fill

2026-06-20 KST에 `reliability_target_v3_informative_anchor_label_fill`을 진행했다.
이 단계는 full 160-row packet-complete informative-anchor sheet를 user-requested Codex proxy로
채우는 단계다. Hidden proxy/sampling field는 label decision 전에 사용하지 않았고, label fill
이후 diagnostics에만 조인했다. Posterior는 실행하지 않았다.

Result:

```text
status = h002_reliability_target_v3_informative_anchor_label_filled_codex_proxy_user_requested
rows = 160
reliable = 35
unreliable_geometry = 13
unreliable_trivial = 34
unreliable_ontology = 0
uncertain = 78
input validation errors = 0
fill validation errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v3_informative_anchor_label_ingestion
```

Axis counts:

| Axis | Value | Count |
| --- | --- | ---: |
| geometry_support | `supports_predicate` | 72 |
| geometry_support | `contradicts_predicate` | 13 |
| geometry_support | `ambiguous` | 75 |
| relation_usefulness | `informative` | 37 |
| relation_usefulness | `trivial_dense_or_room_structure` | 35 |
| relation_usefulness | `ontology_mismatch` | 13 |
| relation_usefulness | `uncertain` | 75 |

Post-label anchor-category diagnostics:

| Anchor Category | Rows | Reliable | Unreliable Geometry | Unreliable Trivial | Uncertain |
| --- | ---: | ---: | ---: | ---: | ---: |
| `informative_reliable_positive_proxy` | 40 | 32 | 0 | 0 | 8 |
| `geometry_contradiction_negative_proxy` | 40 | 1 | 13 | 18 | 8 |
| `trivial_room_surface_negative_proxy` | 40 | 2 | 0 | 16 | 22 |
| `uncertain_or_ontology_negative_proxy` | 40 | 0 | 0 | 0 | 40 |

Interpretation:

- Informative-anchor sampling improved positive mass from the object/endpoint attempt's 8 reliable rows to 35 reliable rows.
- Geometry support still does not equal reliability: 72 rows support the predicate, but only 35 are reliable.
- The target is still not posterior-ready until ingestion and target-independence audit pass.
- A specific risk is packet-source confounding: the 34 newly generated packet rows are all uncertain under the proxy fill.
- Therefore the next step must derive targets and audit shortcut risks before any posterior smoke.

Main artifacts:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/152_reliability_target_v3_informative_anchor_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/completed_informative_anchor_label_sheet_codex_proxy_user_requested.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/informative_anchor_v3_proxy_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/post_label_diagnostics.csv
```

## Reliability Target V3 Informative Anchor Label Ingestion

2026-06-20 KST에 `reliability_target_v3_informative_anchor_label_ingestion`을 진행했다.
이 단계는 filled v3 labels를 ingest하고 relation reliability, geometry support, relation
usefulness target을 분리해 만드는 단계다. Posterior는 실행하지 않았다.

Result:

```text
status = h002_reliability_target_v3_informative_anchor_label_ingested_with_probe_risk
rows = 160
relation reliability binary = 82 rows, 35 positive, 47 negative
geometry support binary = 85 rows, 72 positive, 13 negative
relation usefulness binary = 85 rows, 37 positive, 48 negative
ingestion errors = 0
relation reliability probe = target_independence_risk_hidden_metadata_correlated
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v3_informative_anchor_target_independence_audit
```

Binary target counts:

| Target | Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `relation_reliability_v3_binary_target` | 82 | 35 | 47 | 0.4268 | 78 |
| `geometry_support_v3_binary_target` | 85 | 72 | 13 | 0.8471 | 75 |
| `relation_usefulness_v3_binary_target` | 85 | 37 | 48 | 0.4353 | 75 |

Probe summary:

| Target | Probe Status | Hidden Risks | Visible Risks |
| --- | --- | ---: | ---: |
| `relation_reliability_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 11 | 2 |
| `geometry_support_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 13 | 4 |
| `relation_usefulness_v3_binary_target` | `target_independence_risk_hidden_metadata_correlated` | 11 | 2 |

Interpretation:

- Informative-anchor path finally produces usable relation reliability target mass: 35 positive / 47 negative.
- This improves the object/endpoint attempt's positive-sparse 8 / 99 relation reliability target.
- However, this is not posterior-ready because quick probes flag construction shortcuts.
- The strongest risks are anchor category, endpoint pattern, object labels, subject/object family cells, and rank band.
- Therefore the next step must be a target-independence audit, not posterior smoke.

Main artifacts:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/153_reliability_target_v3_informative_anchor_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/validated_informative_anchor_v3_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/relation_reliability_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/geometry_support_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/relation_usefulness_v3_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested/target_independence_probe_summaries.csv
```

## Next Step

The next H002 step is:

```text
reliability_target_v4_matched_contrast_target_independence_audit
```

Goal:

- test whether a controlled slice remains after object/family/rank/packet-source risks are removed.
- decide whether posterior smoke is allowed, blocked, or needs another target construction revision.
- keep relation reliability, geometry support, and relation usefulness targets separated.
- keep multi-view as audit/label evidence only, not posterior input.
- keep posterior smoke blocked until target-independence audit passes.
- keep validation/test unavailable.
- continue without paper-level posterior performance claims.

## Reliability Target V4 Matched Contrast Target Independence Audit

2026-06-21 KST에 `reliability_target_v4_matched_contrast_target_independence_audit`를
진행했다. 이 단계는 v4 matched-contrast target이 posterior smoke로 넘어갈 만큼
target-independent한지 확인하는 gate다. Posterior는 학습하지 않았고, validation/test는
사용하지 않았다.

결과:

```text
status = h002_reliability_target_v4_matched_contrast_target_independence_audit_blocked
validation_errors = 0
relation reliability = 47 rows, 23 positive, 24 negative
geometry support = 47 rows, 30 positive, 17 negative
relation usefulness = 50 rows, 25 positive, 25 negative
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v4_matched_contrast_path_decision
```

핵심 판단:

- v4 matched-contrast target은 class balance를 확보했지만 posterior-ready는 아니다.
- `matched_contrast_role_hidden` 자체는 original relation reliability target에서 strong risk로
  잡히지 않았다.
- 그러나 `subject_object_family_cell_hidden`이 relation reliability label을 완전히 설명한다
  (`NMI=1.0000`, majority accuracy `1.0000`).
- visible `subject_label`도 strong shortcut이다 (`NMI=0.7764`, majority accuracy `0.9149`).
- `endpoint_flag_pattern_hidden`, `endpoint_family_cell_hidden`, `object_family_cell_hidden`,
  visible `object_label`도 target과 강하게 묶여 있다.
- 18개 controlled slice 중 strict 또는 diagnostic posterior-ready slice는 없다.

해석:

현재 target으로 posterior smoke를 돌리면 결합 방식이 좋아져도 relation reliability를 배운 것인지,
object/family shortcut을 배운 것인지 방어할 수 없다. 따라서 다음 단계는 posterior가 아니라
`reliability_target_v4_matched_contrast_path_decision`이다.

Main artifacts:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/163_reliability_target_v4_matched_contrast_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested/group_table.csv
```

## Next Step

The next H002 step is:

```text
reliability_target_v4_matched_contrast_path_decision
```

Goal:

- decide whether to rebuild the target with stronger endpoint/object controls.
- keep relation reliability as the main target only if target-independence can be defended.
- keep geometry support and relation usefulness as auxiliary evidence axes, not replacement main targets.
- keep posterior smoke blocked until a strict controlled reliability slice exists.

## Reliability Target V4 Matched Contrast Path Decision

2026-06-21 KST에 `reliability_target_v4_matched_contrast_path_decision`을 진행했다.
이 단계는 v4 target-independence audit이 blocked 된 뒤 posterior를 강행할지,
같은 v4 sampling을 확장할지, target construction을 다시 바꿀지 결정하는 gate다.
Posterior는 학습하지 않았고 validation/test는 사용하지 않았다.

결과:

```text
status = h002_reliability_target_v4_matched_contrast_path_decision_select_v5_cell_contrast_feasibility
selected_path = v5_cell_contrast_feasibility_scan
relation reliability = 47 rows, 23 positive, 24 negative
direct reliable/unreliable pair contrast = 1 / 79 pairs
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v5_cell_contrast_feasibility_scan
```

핵심 판단:

- v4는 role/source/geometry balancing을 개선했지만 subject/object-family shortcut을 해결하지 못했다.
- `subject_object_family_cell_hidden`이 relation reliability target을 완전히 설명한다.
- current v4의 `subject_object_family_cell_balanced_v4` slice는 `0` rows다.
- pairwise direct contrast도 `1/79` pairs로 너무 sparse하다.
- 따라서 posterior smoke도, 같은 v4 sampling 단순 확장도 선택하지 않는다.

선택한 다음 경로는 `v5_cell_contrast_feasibility_scan`이다. 이는 label fill이 아니라 full train pool에서
same subject/object/family cell 안에 reliable-like와 unreliable-like 후보가 함께 존재하는지 먼저
확인하는 단계다.

Main artifacts:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/164_reliability_target_v4_matched_contrast_path_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_path_decision_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_path_decision_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_path_decision_codex_proxy_user_requested/option_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_path_decision_codex_proxy_user_requested/failure_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_path_decision_codex_proxy_user_requested/next_plan.json
```

## Next Step

The next H002 step is:

```text
reliability_target_v5_cell_contrast_feasibility_scan
```

Goal:

- scan full train-only support/vertical pool for within-cell positive/negative capacity.
- use subject/object/family cell as a control axis, not a learned shortcut.
- decide whether another label round is justified.
- freeze H002 as an RGA diagnostic framework if the feasibility scan fails.

## Reliability Target V5 Cell Contrast Feasibility Scan

2026-06-21 KST에 `reliability_target_v5_cell_contrast_feasibility_scan`을 진행했다.
이 단계는 v4에서 드러난 subject/object-family shortcut을 줄일 수 있는지 확인하기 위해,
새 label fill 전에 full train-only support/vertical pool의 within-cell contrast capacity만
측정하는 gate다. Label fill, posterior training, validation/test 사용은 하지 않았다.

결과:

```text
status = h002_reliability_target_v5_cell_contrast_feasibility_ready_for_candidate_mining
selected_level = strict_predicate_subject_object_endpoint
selected rows = 80
selected pairs = 40
selected mixed cells = 21
max_cell_share = 0.0500
packet_ready = 2
asset_needed = 78
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v5_cell_contrast_candidate_mining
```

핵심 판단:

- strict predicate + subject/object label + endpoint pattern level에서도 mixed proxy capacity가 있다.
- eligible groups는 `137`, balanced pair capacity는 `167`이다.
- selected preview는 `40` pairs / `80` rows / `21` cells이고 single-cell share는 `0.05`다.
- `support_contact`와 `relative_vertical`이 모두 포함된다 (`48/32` rows).
- 다만 packet coverage는 낮다: `2/80` ready, `78/80` asset-needed.

해석:

v4의 실패는 H002 아이디어 자체의 불가능성이 아니라 v4 label construction이 exact object-cell
control을 만들지 못한 문제에 가깝다. Full train pool에는 더 엄격한 cell contrast label round를
시도할 capacity가 있다. Posterior smoke는 여전히 blocked이며, 다음 단계는 v5 candidate sheet와
asset path를 만드는 것이다.

Main artifacts:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/165_reliability_target_v5_cell_contrast_feasibility_scan.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_feasibility_scan.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/matching_level_inventory.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/cell_inventory.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/seed_preview_internal.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_feasibility_scan/feasibility_contract.json
```

## Next Step

The next H002 step is:

```text
reliability_target_v5_cell_contrast_candidate_mining
```

Goal:

- turn the v5 strict-cell feasibility preview into a candidate/label sheet.
- keep cell contrast roles hidden from the label surface.
- prepare asset packet generation/readiness for the `78` asset-needed rows.
- keep posterior smoke blocked until v5 labels are filled, ingested, and target-independence audit passes.

## Reliability Target V5 Cell Contrast Candidate Mining

2026-06-21 KST에 `reliability_target_v5_cell_contrast_candidate_mining`을 진행했다.
이 단계는 v5 feasibility scan의 strict predicate+subject/object+endpoint contrast preview를
blind label sheet, hidden manifest, asset request plan으로 변환하는 단계다. Label fill,
posterior training, validation/test 사용은 하지 않았다.

결과:

```text
status = h002_reliability_target_v5_cell_contrast_candidate_mining_ready_needs_asset_packets
selected_level = strict_predicate_subject_object_endpoint
label rows = 80
contrast pairs = 40
contrast cells = 21
packet_ready = 2
asset_needed = 78
asset_request_rows = 78
field/value leakage = 0 / 0
packet/input errors = 0 / 0
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v5_cell_contrast_asset_packets
```

해석:

- Candidate label surface는 blind contract를 만족한다. Cell contrast role, source queue,
  rank band, geometry status, proxy label은 hidden manifest에만 남긴다.
- Hidden role, source queue, geometry status는 각각 `40/40`으로 balanced다.
- Family distribution은 `support_contact:48`, `relative_vertical:32`다.
- 하지만 packet-ready row는 `2/80`뿐이다. 따라서 label fill이 아니라 asset packet
  generation/readiness가 다음 gate다.
- Posterior smoke는 v5 label fill, ingestion, target-independence audit 이후에만 다시 열 수 있다.

Main artifacts:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/166_reliability_target_v5_cell_contrast_candidate_mining.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_candidate_mining.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/cell_contrast_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_candidate_mining/asset_request_plan.jsonl
```

## Next Step

The next H002 step is:

```text
reliability_target_v5_cell_contrast_asset_packets
```

Goal:

- generate or verify asset packets for the `78` asset-needed rows.
- keep label fill blocked until packet coverage is sufficient.
- preserve the blind label-surface contract.
- keep posterior smoke blocked until label fill, ingestion, and target-independence audit pass.

## Reliability Target V5 Cell Contrast Asset Packets

2026-06-21 KST에 `reliability_target_v5_cell_contrast_asset_packets`을 진행했다.
이 단계는 v5 candidate mining의 `78` asset-needed rows에 multi-view / mesh /
contact-context evidence packet을 생성하고, 기존 `2` packet-ready rows와 합쳐 full
`80`-row label sheet를 만드는 단계다. Label fill, posterior training, validation/test
사용은 하지 않았다.

결과:

```text
status = h002_reliability_target_v5_cell_contrast_asset_packets_partial
input selected rows = 80
asset-needed input rows = 78
generated packet rows = 78
generated ready rows = 66
generated non-ready rows = 12
existing packet-ready rows = 2
full label sheet rows = 80
ready label rows = 68
packet path errors = 1
label-surface leakage hits = 0
visible value leakage hits = 0
validation errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v5_cell_contrast_asset_packet_gap_audit
```

해석:

- Label surface leakage와 packet text leakage는 `0`이다.
- Full sheet는 `68/80` ready, `12/80` partial이다.
- Partial rows는 `support_contact:6`, `relative_vertical:6`으로 나뉜다.
- Partial 원인은 주로 endpoint crop 부족이다: subject crop missing `6`, object crop missing `7`.
- Mesh packet은 모든 partial row에서 생성됐다. 단 `ftv5cc_0a7d66060905`는
  `contact_or_context_sheet`가 비어 있어 packet path error `1`이 발생했다.
- 따라서 label fill은 아직 blocked이고, 다음 단계는 partial rows를 limited-view evaluable로
  볼 수 있는지 또는 replacement/needs-more-evidence로 보낼지 결정하는 gap audit이다.

Main artifacts:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/167_reliability_target_v5_cell_contrast_asset_packets.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_asset_packets.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/cell_contrast_full_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/generated_non_ready_packet_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packets/packet_path_errors.jsonl
```

## Next Step

The next H002 step is:

```text
reliability_target_v5_cell_contrast_asset_packet_gap_audit
```

Goal:

- inspect the `12` partial rows and the `1` empty packet path.
- decide limited-view-evaluable vs replacement/needs-more-evidence.
- keep label fill and posterior smoke blocked until packet coverage is resolved.

## Reliability Target V5 Cell Contrast Asset Packet Gap Audit

2026-06-21 KST에 `reliability_target_v5_cell_contrast_asset_packet_gap_audit`을
진행했다. 이 단계는 v5 asset packet generation의 partial packet rows를 label fill 전에
감사하고, pair integrity를 유지하기 위해 replacement-needed row가 있는 pair 전체를 제외하는
단계다. Label fill, posterior training, validation/test 사용은 하지 않았다.

결과:

```text
status = h002_reliability_target_v5_cell_contrast_asset_packet_gap_audit_ready_for_label_readiness
input rows = 80
input pairs = 40
label-ready rows = 72
label-ready pairs = 36
excluded rows = 8
excluded pairs = 4
limited-view rows kept = 6
replacement-needed rows = 5
output path errors = 0
visible leakage hits = 0
input validation errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v5_cell_contrast_label_readiness
```

해석:

- `36` cell-contrast pairs가 label-ready로 남았고, hidden role balance는
  `positive_proxy:36`, `negative_proxy:36`이다.
- Family balance는 `support_contact:44`, `relative_vertical:28`이다.
- `6` limited-view rows는 mesh/contact evidence가 충분하다고 판단되어 유지했다.
- `5` replacement-needed rows 때문에 `4` pairs를 제외했다:
  `v5cell_0013`, `v5cell_0014`, `v5cell_0033`, `v5cell_0034`.
- 이전 단계의 empty `contact_or_context_sheet` 문제는 해당 pair가 제외되면서 label-ready sheet에서
  사라졌다. Output path errors와 visible leakage hits는 `0`이다.
- Posterior smoke는 여전히 blocked이며, 다음 단계는 label fill이 아니라 label-readiness validation이다.

Main artifacts:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/168_reliability_target_v5_cell_contrast_asset_packet_gap_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v5_cell_contrast_asset_packet_gap_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/label_ready_full_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/label_ready_full_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v5_cell_contrast_asset_packet_gap_audit/excluded_pair_ids.txt
```

## Next Step

The next H002 step is:

```text
reliability_target_v5_cell_contrast_label_readiness
```

Goal:

- validate the `72`-row / `36`-pair label-ready sheet.
- check expected columns, packet paths, role balance, leakage, and readiness status.
- keep label fill and posterior smoke blocked until readiness passes.
