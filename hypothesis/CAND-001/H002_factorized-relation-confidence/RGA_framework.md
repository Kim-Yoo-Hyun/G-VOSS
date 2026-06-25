# H002 RGA Framework

Last updated: 2026-06-24 KST

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

Current H002 target policy:

```text
human-audited reliability label = primary target
existing GT relation match = auxiliary analysis axis
GT/reliability mismatch table = required analysis
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

Attachment v19 adds a temporary evidence-boundary distinction:

```text
A_ind_e = independent audit supervision source
V_mv_e  = future deployable visual evidence factor
```

At the current gate, `A_ind_e` may be used only to construct or confirm labels.
`V_mv_e` is not a model input until the target is independent and visual controls
are defined.

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
current_gate = v23 hanging-on positive-anchor repair plan completed
status = h002_reliability_target_v23_hanging_on_positive_anchor_repair_plan_ready_for_capacity_scan
posterior_smoke_allowed = false
validation_or_test_used = false
next = reliability_target_v23_hanging_on_positive_anchor_capacity_scan
```

Current finding:

```text
v16_support_contact_raw_quota_capacity = sufficient
v16_support_contact_controlled_target = blocked_by_geometry_status_shortcut
attachment_deferred_rows = 556038
attachment_deferred_checkable_rows_before_schema = 0
attachment_deferred_raw_feature_join_coverage = 1.0
attachment_deferred_capacity_pass = true
attachment_deferred_path_decision = attached_hanging_primary_connected_diagnostic
attachment_deferred_candidate_mining = label_ready_240_visible_leakage_0
attachment_deferred_candidate_primary_binary = 160
attachment_deferred_candidate_diagnostic = 60
attachment_deferred_candidate_audit = 20
attachment_deferred_label_fill = visible_only_accept33_reject81_abstain64_connected_diagnostic62
attachment_deferred_primary_binary_usable = 114
attachment_deferred_primary_positive = 33
attachment_deferred_primary_negative = 81
attachment_deferred_label_ingestion = binary114_positive33_negative81_quick_probe_risk102
attachment_deferred_target_audit = blocked_positive_sparse_strict0_diagnostic0_risk119_slice3163
attachment_deferred_path_decision_after_audit = freeze_diagnostic_select_v19_independent_evidence_repair
attachment_deferred_independent_evidence_repair_plan = ready_for_source_inventory_audit_only
attachment_deferred_local_source_probe = 3rscan_exists_multiview40_sequence40_sample
attachment_deferred_source_inventory = gate_pass_primary160_audit_ready160_strong_same_frame43
attachment_deferred_audit_packet_plan = ready_for_materialization_primary_t1_31_t2_129
attachment_deferred_audit_packet_materialization = packets240_images4466_visible_leakage0
attachment_deferred_audit_packet_leakage_review = passed_visible_leakage0_validation0
attachment_deferred_audit_packet_label_fill = accept26_reject99_abstain53_connected15_47
attachment_deferred_audit_packet_primary_binary = positive26_negative99
attachment_deferred_audit_packet_label_ingestion = multiclass240_primary_binary125_geometry140_connected62
attachment_deferred_audit_packet_target_viability = positive_sparse_26_99_quick_probe_risk43
attachment_deferred_audit_packet_target_independence = blocked_positive_sparse_strict0_diagnostic0_risk56_slice1185
attachment_deferred_audit_packet_path_decision = freeze_v19_diagnostic_select_v20_endpoint_balanced_counterfactual_repair
attachment_deferred_endpoint_balanced_counterfactual_repair_plan = ready_for_capacity_scan_primary_attached_hanging_connected_diagnostic
attachment_deferred_endpoint_balanced_counterfactual_capacity_scan = passed_exact_endpoint_pair_mixed_groups4616_preview320_feasible
attachment_deferred_endpoint_balanced_counterfactual_candidate_mining = selected320_primary256_connected64_visible_leakage0
attachment_deferred_endpoint_balanced_counterfactual_source_inventory = gate_pass_audit_ready320_strong75_t2_245
attachment_deferred_endpoint_balanced_counterfactual_audit_packet_plan = ready_for_materialization_rows320_t1_75_t2_245
attachment_deferred_endpoint_balanced_counterfactual_audit_packet_materialization = packets320_images5836_visible_leakage0_gt_axis320
attachment_deferred_endpoint_balanced_counterfactual_audit_packet_leakage_review = passed_visible_leakage0_validation0_ready_for_label_fill
attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_fill = user_filled_accept25_reject182_abstain113
attachment_deferred_endpoint_balanced_counterfactual_audit_packet_label_ingestion = primary_binary25_182_quick_probe_risk70_gt_mismatch_ready
attachment_deferred_endpoint_balanced_counterfactual_audit_packet_target_independence = blocked_positive_sparse_strict0_diagnostic0_risk82_slice1112
attachment_deferred_endpoint_balanced_counterfactual_audit_packet_path_decision = freeze_v20_diagnostic_select_v21_conditional_contrast_capacity_scan
attachment_deferred_conditional_contrast_capacity_scan = blocked_predicate_imbalanced_strict_capacity
attachment_deferred_v21_primary_rows = 370692
attachment_deferred_v21_diagnostic_connected_rows = 185346
attachment_deferred_v21_strict_mixed_groups = 258
attachment_deferred_v21_strict_balanced_capacity = 4507
attachment_deferred_v21_strict_by_predicate = hanging_on_only
attachment_deferred_v21_diagnostic_mixed_groups = 591
attachment_deferred_v21_path_decision = hanging_on_strict_primary_attached_to_diagnostic
attachment_deferred_v22_packet_plan = ready_for_candidate_mining_rows240_proxy120_120_groups95_scans192
attachment_deferred_v22_candidate_mining = ready_for_source_inventory_rows240_visible_leakage0
attachment_deferred_v22_source_inventory = ready_for_audit_packet_plan_rows240_audit_ready240_strong73_t2_167
attachment_deferred_v22_audit_packet_plan = ready_for_materialization_rows240_t1_73_t2_167_proxy120_120
attachment_deferred_v22_audit_packet_materialization = ready_for_leakage_review_packets240_images4406_visible_leakage0_gt_axis240
attachment_deferred_v22_audit_packet_leakage_review = passed_visible_leakage0_validation0_ready_for_label_fill
attachment_deferred_v22_audit_packet_label_fill = codex_visible_accept9_reject193_abstain38
attachment_deferred_v22_audit_packet_label_ingestion = primary_binary9_193_quick_probe_risk97_gt_no_current240
attachment_deferred_v22_audit_packet_target_independence = blocked_positive_sparse_strict0_diagnostic0_risk107_slice1666
attachment_deferred_v22_audit_packet_path_decision = freeze_v22_diagnostic_select_v23_positive_anchor_repair_plan
attachment_deferred_v23_positive_anchor_repair_plan = ready_for_capacity_scan_accept_seed9_cell9_2
attachment_deferred_next_question = hanging_on_positive_anchor_capacity_scan
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
proximity_v13_label_ingestion_binary_positive = 39
proximity_v13_label_ingestion_binary_negative = 137
proximity_v13_geometry_support_positive = 121
proximity_v13_geometry_support_negative = 55
proximity_v13_same_block_mixed_binary_groups = 22
proximity_v13_same_visible_pair_mixed_binary_groups = 22
proximity_v13_quick_probe_risk_flags = 32
proximity_v13_target_audit_relation_strict_clear_slices = 0
proximity_v13_target_audit_relation_diagnostic_clear_slices = 0
proximity_v13_target_audit_full_quick_probe_risk_flags = 41
proximity_v13_target_audit_slice_blocking_risk_flags = 517
proximity_v13_path_decision = diagnostic_only_generality_evidence
physical_family_v14_feasibility = support_contact_primary_anchor_relative_vertical_control_attachment_schema_deferred
physical_family_v14_sampling_plan = support_contact_160_relative_vertical_80_ready
physical_family_v14_candidate_mining = label_ready_240_visible_leakage_0
physical_family_v14_label_fill = visible_only_accept48_reject152_abstain40
physical_family_v14_label_ingestion = binary48_152_quick_probe_risk64
physical_family_v14_target_audit = blocked_positive_sparse_strict0_diagnostic0
physical_family_v14_path_decision = freeze_diagnostic_select_v15_repair
physical_family_v15_repair_plan = support_contact_witness_matched_ready_for_capacity_scan
physical_family_v15_capacity_scan = row_capacity_sufficient_mixed_witness_strata_0
physical_family_v15_path_decision = reject_same_witness_select_cross_stratum_support_contact
physical_family_v16_cross_stratum_plan = lying_on_hl100_lh100_standing_lh24_vertical_control16
selected_next_path = v22_hanging_on_strict_conditional_contrast_audit_packet_target_independence_audit
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
- v21 ingests the labels and joins hidden audit metadata: `240` multiclass, `176` binary, `176` geometry-support, and `176` usefulness target rows. Same block / same visible-pair mixed binary groups increase to `22`, but reliability positive mass remains `39` and quick probes report `32` shortcut-risk flags, so posterior remains blocked.
- v22 audits target independence. Primary relation reliability remains blocked by positive sparsity (`39/137`) and has `0` strict or diagnostic clear slices. Geometry-support has class mass (`121/55`) but no strict independent slice, so it cannot replace the primary reliability target.
- v23 freezes proximity as diagnostic/generality evidence and selects `v14_physical_relation_family_feasibility_scan` as the next primary target-repair route.
- v24 scans `support_contact`, `attachment_deferred`, and `relative_vertical` on train-only rows. `support_contact` has enough checkable row mass and same-predicate HL/LH capacity to become the next sampling anchor; `relative_vertical` is kept as a geometry-easy control; `attachment_deferred` is deferred because current geometry policy marks it as unsupported.
- v25 freezes a 240-row sampling plan: `support_contact` primary anchor `160` rows and `relative_vertical` control `80` rows. Queue bucket remains a hidden sampling axis, not a relation reliability label.
- v26 materializes that plan into a 240-row label-ready sheet with hidden audit manifest separated, raw geometry joined for all rows, visible leakage `0`, and posterior still blocked until label fill, ingestion, and target-independence audit.
- v27 fills the visible-only v14 label sheet with `48` accept, `152` reject, and `40` abstain rows. This creates target material for ingestion, but positive class mass is still below the earlier `50` gate, so posterior remains blocked.
- v28 ingests the locked labels into target artifacts: `240` multiclass, `200` binary, `200` geometry-support, `200` usefulness, `240` endpoint, and `240` coverage rows. Positive mass remains `48/152` and quick probes flag `64` risks, so posterior remains blocked until target-independence audit.
- v29 audits target independence. Primary relation binary remains blocked by positive sparsity (`48/152`), has `0` strict clear slices and `0` diagnostic clear slices, and reports `1,171` slice-level blocking risk flags. Posterior remains blocked.
- v30 freezes current v14 as diagnostic target-construction evidence and selects a v15 witness-matched physical relation-family repair plan. Adding two positives is rejected because the balanced `48/48` slice remains shortcut-entangled.
- v31 fixes the v15 repair contract. `support_contact` remains primary, `relative_vertical` is reduced to a small control, direct witness-summary fields are forbidden from the visible label surface, and posterior remains blocked until capacity scan plus target-independence audit pass.
- v32 scans train-only capacity for that contract. Row count and capped preview are sufficient (`support_contact` after caps `224`), but same-witness mixed HL/LH strata are `0`, so the repair contract itself needs a path decision before any label sheet.
- v33 rejects same-witness HL/LH matching and selects controlled cross-stratum support/contact contrast. This keeps H002's bidirectional mismatch definition while requiring strong shortcut controls before candidate mining.
- v34 fixes the v16 cross-stratum plan: `lying on` HL/LH `100/100` as primary, `standing on` LH `24` as diagnostic diversity, and `lower than` LH `16` as small control. Capacity scan is required before any label sheet.
- v35 scans v16 cross-stratum capacity. Raw quota is sufficient, but `lying on` HL is all `unsatisfied`, LH is all `satisfied`, and mixed primary blocks are only `4`, so label sheet creation is blocked.
- v36 freezes v16 as diagnostic-only and selects `attachment_deferred_witness_schema_probe`. The failure is treated as target-construction evidence, not as evidence against H002.
- v37 fixes a typed witness schema for `attached to`, `hanging on`, and `connected to`, with multi-view kept as audit-only and posterior smoke blocked.
- v38 verifies capacity for that schema. All 556,038 attachment rows join to pair-level raw geometry, typed witness cells pass, and a 240-row capped preview has no deficits.
- v39 authorizes v18 candidate mining for `attached to` and `hanging on` as primary binary candidates, while keeping `connected to` diagnostic-only because functional connection is not reliable from OBB geometry alone.
- v40 creates the hidden-field-safe v18 candidate packet: 240 visible rows, 240 hidden manifest rows, 160 primary `attached to`/`hanging on` candidates, 60 diagnostic `connected to` rows, 20 uncertainty audit rows, and 0 visible leakage hits.
- v41 fills visible-only proxy labels without reading the hidden manifest. The primary attachment target has 114 usable binary rows with 33 positives and 81 negatives, so posterior smoke remains blocked pending ingestion and target-independence audit.
- v42 ingests v18 labels with the hidden audit manifest. Target artifacts are created, but positive class mass remains low (`33/81`) and quick probes report `102` shortcut-risk flags, so posterior smoke remains blocked.
- v43 audits target independence. Primary relation binary remains positive-sparse (`33/81`) with `0` strict and `0` diagnostic clear slices. Full quick probes flag `119` risks and slice-level blocking risk totals `3,163`, so posterior smoke remains blocked.
- v44 freezes v18 attachment as diagnostic target-construction evidence and selects v19 independent-evidence repair planning. Multi-view/mesh may be used only as audit or confirmation evidence, not as deployable model input.
- v45 fixes the v19 independent-evidence contract and label schema. The selected route is `independent_visual_or_mesh_audit_packet_before_labels`; primary scope is `attached to` / `hanging on`, `connected to` remains diagnostic-only, local 3RScan `multi_view` and `sequence` samples exist, and the next step is row-level source inventory before any labels or posterior smoke.
- v46 inventories row-level source availability. All 160 primary attachment rows have subject/object crops and audit-ready visual/mesh assets, but exact same-frame co-visible evidence exists for only 43/240 rows. RGA therefore moves to a tiered audit-packet plan rather than immediate label fill.
- v47 fixes the tiered audit-packet plan. Reviewer-visible fields exclude construction metadata and v18 labels; hidden asset paths remain internal. The next step is materialization, still before any labels or posterior smoke.
- v48 materializes the packet set: 240 visible rows, 240 packet directories, 4,466 neutral packet-local image copies, and 0 visible leakage hits. The next step is a formal leakage review before labels.
- v49 passes formal leakage review: visible sheet, packet markdown, and neutral image filenames have 0 leakage hits. The next step is packet-based label fill; posterior smoke remains blocked.
- v50 fills leakage-reviewed packet labels without reading the hidden manifest. The label material is cleanly generated, but the primary binary preview is positive-sparse (`26/99`), so posterior smoke remains blocked until ingestion and target-independence audit.
- v51 ingests the filled packet labels after label lock. Target artifacts are created (`240` multiclass, `125` primary binary, `140` geometry-support, `62` connected diagnostic), but class mass fails and quick probes flag `43` shortcut risks. Posterior smoke remains blocked.
- v52 audits target independence. The primary relation target remains blocked (`26/99`, strict clear slices `0`, diagnostic clear slices `0`), and endpoint/scan/subject-label shortcuts remain strong. Posterior smoke remains blocked.
- v53 freezes the v19 audit-packet target as diagnostic negative target-construction evidence and selects a v20 endpoint-balanced counterfactual repair plan. Stronger posterior combiners remain blocked because the current label target is still shortcut-explainable.
- v54 freezes the v20 repair contract. `attached to` and `hanging on` stay primary, `connected to` stays diagnostic-only, sample sizes `240/320/400` must be capacity-scanned, and post-label gates require at least `60/60` accept/reject plus controlled non-shortcut slices before posterior smoke.
- v55 scans full train capacity. Exact visible endpoint-pair mixed contrast passes with `4,616` mixed groups and `26,054` balanced pairs; sample sizes `240/320/400` are all feasible. This unlocks candidate mining, not posterior smoke.
- v56 materializes the default 320-row candidate set with 256 primary `attached to`/`hanging on` rows and 64 `connected to` diagnostic rows. Visible leakage is 0, but source inventory is required before label fill.
- v57 inventories v56 rows and passes the source gate: 320/320 rows are audit-ready, with 75 strong same-frame co-visible rows and 245 individual-view-plus-mesh rows. The next audit packet plan must preserve this tier distinction before label fill.
- v58 fixes the tiered audit-packet plan: 320 visible packet rows, 256 primary attachment rows, 64 connected diagnostic-only rows, T1/T2 = 75/245, and validation errors 0. The next step is materialization, still before label fill or posterior smoke.
- v59 materializes the tiered packets: 320 packet directories, 5,836 neutral packet-local images, visible leakage 0, validation errors 0, and existing GT-match auxiliary axis joined for 320/320 hidden rows. The next step is formal leakage review before label fill.
- v60 passes formal leakage review: 320 visible rows, 320 packet markdown files, 5,836 neutral image filenames, 0 visible leakage hits, 0 validation errors, and GT-match auxiliary axis preserved only in hidden manifest. The next step is packet label fill, still before posterior smoke.
- v61 locks user-filled visible packet labels: `accept/reject/abstain = 25/182/113`, with primary binary preview `25/182`, hidden manifest not read, validation errors 0, and posterior smoke blocked.
- v62 ingests locked labels with hidden manifest and GT-match axis after label lock: multiclass 320, primary binary 207 (`25/182`), geometry-support 219, endpoint/coverage/uncertainty 320, quick-probe risk 70, validation errors 0. The next step is target-independence audit.
- v63 audits target independence. Primary relation binary remains positive-sparse (`25/182`) with `0` strict and `0` diagnostic clear slices. Full quick probes flag `82` risks and slice-level blocking risk totals `1,112`, so posterior smoke remains blocked and the next step is path decision.
- v64 freezes v20 as diagnostic negative target-construction evidence and selects a full-train conditional contrast capacity scan. This keeps open the possibility that the 320-row packet was a sampling artifact, while still blocking posterior smoke until factorization-requiring strata are shown to exist.
- v65 scans the full-train attachment pool. Conditional contrast proxy exists, but strict `same_predicate_rank_geometry_family` mixed strata remain only for `hanging on`; `attached to` survives only under a relaxed diagnostic spec. Therefore the next step is path decision, not label packet creation or posterior smoke.
- v66 completes that path decision. The strict condition is recorded as an H002 control rule, not a dataset GT rule. The selected route is `hanging on` strict primary, with `attached to` and `connected to` kept diagnostic until stronger evidence or a separate target route exists.
- v67 completes the `hanging on` strict packet plan. A hidden-only dry-run preview can select 240 rows with 120/120 proxy balance across 95 strict groups, 192 scans, and 193 visible endpoint pairs. This unlocks candidate mining, not label fill or posterior smoke.
- v68 materializes a hidden-field-safe 240-row candidate sheet for `hanging on`. Visible leakage is 0; source ids and construction fields are hidden. This unlocks source inventory, not packet assets, label fill, or posterior smoke.
- v69 inventories source evidence for the 240 `hanging on` rows. All rows are audit-ready, all 192 scans have `multi_view`, sequence, and mesh source, 73 rows have strong same-frame co-visible evidence, and 167 rows use individual-view-plus-mesh evidence. This unlocks audit packet planning, not packet materialization, label fill, or posterior smoke.
- v70 fixes the audit packet plan for the 240 `hanging on` rows. Visible packet templates, hidden asset manifest plan, visible schema, and audit packet contract are ready, with T1/T2 = 73/167 and hidden proxy balance 120/120. This unlocks packet materialization, not label fill or posterior smoke.
- v71 materializes the v22 packet set: 240 visible review rows, 240 packet directories, 4,406 neutral packet-local images, hidden GT-match axis joined for 240/240, visible leakage hits 0, validation errors 0. This unlocks formal leakage review, not label fill or posterior smoke.
- v72 passes formal leakage review for the v22 packet surface: 240 visible rows, 240 packet markdown files, 240 packet directories, 4,406 neutral packet-local images, hidden manifest rows 240, visible leakage hits 0, validation errors 0. This unlocks visible-only label fill, not label ingestion, target-independence audit, or posterior smoke.
- v73 fills the v22 leakage-reviewed packet labels from visible packet evidence only. The result is `accept/reject/abstain = 9/193/38`, binary preview `9/193`, validation errors 0, hidden manifest read false. This unlocks label ingestion, not target-independence audit or posterior smoke.
- v74 ingests the locked v73 labels with hidden manifest and GT axis after label lock. It creates multiclass 240, primary binary 202 (`9/193`), geometry-support 202, endpoint/coverage/uncertainty 240 targets. Class mass fails and quick-probe risk flags are 97, so posterior smoke remains blocked and the next step is target-independence audit.
- v75 audits target independence for the v22 `hanging on` packet target. Primary relation binary remains `9/193`, minimum class mass is 9 versus required 60, strict/diagnostic clear slices are `0/0`, full quick-probe risk flags are 107, and slice-level blocking risk totals 1,666. This repeats the target-construction bottleneck and routes next to path decision, not posterior smoke.
- v76 completes the path decision after v75. v22 is frozen as diagnostic-only negative target-construction evidence, and the selected next route is `v23_hanging_on_positive_anchor_repair_plan`. The repair route must test accept-rich subject-anchor affordance cells with matched hard negatives; it must not simply add easy positives.
- v77 freezes the v23 positive-anchor repair plan. The v22 accept seed is concentrated in `curtain/blinds/bag/towel` subjects and `door/window/stand` anchors; the positive-anchor candidate cell has `accept:9, reject:2`. The next step is a full-train capacity scan requiring at least 300 positive-anchor candidates, 30 matched positive/negative cells, and 160 balanced proxy capacity before any candidate mining or labels.

## Current Relation Scope

Core target construction currently focuses on:

```text
attachment_deferred: hanging on positive-anchor capacity scan
attachment_deferred_diagnostic: attached to and connected to
```

Previous train-only/full-train branches remain diagnostic or control evidence:

```text
support_contact: standing on, lying on
relative_vertical: higher than, lower than
proximity: close by
```

Active empirical branch:

```text
reliability_target_v23_hanging_on_positive_anchor_capacity_scan
```

Deferred expansion:

```text
relative_horizontal: left, right, front, behind
```

`close by` is important for generality, but current evidence supports only a
low-semantic/high-geometry branch. It should not be mixed into the current core target
or used for posterior smoke until the repaired target passes target-independence audit.

## File Ownership

```text
README.md = H002 folder map and current status
summary_branch_v2.md = research framing, claim boundary, latest summary, and v1-v77 overview
RGA_framework.md = RGA definitions, axes, buckets, metrics, gates
feasibility_check.md = posterior combiner and multi-view feasibility notes
stages/ = v1-v77 stage-specific progress, problems, and transition rationale
artifacts/ = raw per-stage outputs
```
