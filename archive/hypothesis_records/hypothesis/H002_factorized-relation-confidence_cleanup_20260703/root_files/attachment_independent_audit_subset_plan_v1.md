# H002 Attachment Independent Audit Subset Plan V1

Date: 2026-06-25 KST

## Purpose

`attachment_controlled_candidate_path_decision_v1`에서 400-row attachment proxy label을
main reliability target으로 승격하지 않기로 했다. 이유는 `G_e`와 `T+G`가 proxy target을
완벽히 맞추지만, hidden construction probe도 AUROC `1.0000`이었기 때문이다.

이 문서의 목적은 다음 단계인 independent audit label 생성을 위해, current H002 schema의
attachment rows와 기존 v20 visual/mesh packet asset을 연결한 blind review subset을 고정하는
것이다.

## Runner

Command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_independent_audit_subset_plan_v1.py
```

Output:

```text
artifacts/attachment_independent_audit_subset_plan_v1/
```

## Selected Route

```text
reuse_v20_packet_assets_with_blank_h002_independent_review_template
```

핵심은 기존 v20 packet asset을 재사용하되, 기존 v20 label이나 현재 proxy label을 새 H002
target으로 자동 승격하지 않는 것이다.

Visible review template의 label field는 모두 blank로 둔다.

```text
prior_v20_labels_used_as_current_target = false
prior_v20_labels_visible_to_reviewer = false
proxy_labels_promoted = false
multi_view_mesh_as_model_input = false
multi_view_mesh_as_audit_evidence = true
```

## Result

```text
status = h002_attachment_independent_audit_subset_plan_v1_ready
current_candidate_rows = 400
v20_packet_matched_rows = 298
v20_packet_unmatched_rows = 102
selected_rows = 200
primary_rows = 160
connected_diagnostic_rows = 40
validation_errors = 0
```

Selected primary predicate balance:

```text
attached to = 80
hanging on = 80
connected to = 40 diagnostic
```

Selected hidden cell balance:

```text
A1_attached_near_anchor_supported_candidate = 40
A2_attached_far_or_floor_confound_candidate = 40
H1_hanging_anchor_supported_candidate = 40
H2_hanging_no_anchor_or_floor_supported_candidate = 40
C1_connected_near_or_overlap_diagnostic = 20
C2_connected_far_or_functional_ambiguous_diagnostic = 20
```

Evidence tier:

```text
T1_strong_pair_visual = 72
T2_individual_visual_plus_mesh = 128
```

The selected rows preserve proxy balance:

```text
proxy positive = 80
proxy counterfactual_negative = 80
connected unknown = 40
```

This proxy balance is used only for sampling coverage. It is not the reliability label.

## Emitted Files

```text
visible_review_template.tsv
audit_subset_plan_rows.jsonl
hidden_audit_manifest.jsonl
visible_schema.json
summary.json
validation_errors.jsonl
report.md
```

`visible_review_template.tsv` contains only reviewer-visible fields and blank review columns.

`hidden_audit_manifest.jsonl` keeps provenance, current H002 row ids, proxy construction fields,
GT-match axis, numeric `G_e`, and prior v20 labels hidden from the reviewer.

## Why This Plan Is Needed

The previous 400-row proxy smoke showed that attachment `G_e` is strong, but not that relation
reliability is independently measurable. This plan changes the target source:

```text
old target = proxy construction label
new target = reviewer-visible packet evidence label
```

This directly addresses the current bottleneck:

```text
target independence, not model capacity
```

## Next TODO

```text
attachment_independent_audit_label_fill_v1
```

The next step should fill the blank review fields in `visible_review_template.tsv` using only
packet images and mesh/context evidence. The hidden manifest must not be used for label decisions.

After label fill, the required follow-up is ingestion and target-independence audit:

```text
attachment_independent_audit_label_ingestion_v1
attachment_independent_audit_target_independence_v1
```

## Boundary

- train-only H002 artifact;
- no validation/test data;
- no model training;
- no H001 modification;
- packet assets are referenced, not copied;
- prior v20 labels are hidden provenance only;
- multi-view/mesh remains audit evidence, not deployable model input.
