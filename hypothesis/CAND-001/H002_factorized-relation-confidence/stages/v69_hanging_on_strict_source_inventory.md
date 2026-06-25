# V69 Hanging-On Strict Source Inventory

## 목적

v68에서 생성한 `hanging on` strict 240-row candidate set이 실제 audit packet으로
이어질 수 있는 source evidence를 갖는지 확인했다.

이 단계는 label fill, label ingestion, target-independence audit, posterior smoke가 아니다.
`multi_view`, sequence, mesh, subject/object crop availability를 row별로 inventory하고,
multi-view/mesh는 계속 audit/confirmation evidence로만 유지한다.

## 입력

- Candidate mining summary: `reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining/summary.json`
- Visible candidate sheet: `reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining/visible_candidate_sheet.tsv`
- Hidden candidate manifest: `reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining/hidden_candidate_manifest.jsonl`
- Source root: `local_dataset/3RScan/scans`

## 결과

```text
status = h002_reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory_ready_for_audit_packet_plan
next_todo = reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_plan
rows = 240
source_inventory_gate_pass = true
validation_errors = 0
posterior_smoke_allowed = false
```

Source/evidence availability:

```text
unique_scans = 192
scan_exists = 192
multi_view_exists = 192
sequence_exists = 192
mesh_ready = 192
both_have_crop_rows = 240
possible_covisible_or_same_view_rows = 240
audit_ready_rows = 240
strong_pair_visual_ready_rows = 73
individual_visual_plus_mesh_audit_ready_rows = 167
```

Proxy-role balance after inventory:

```text
accept_proxy_supported_candidate = 120 rows, 120 audit-ready
reject_proxy_contradicted_candidate = 120 rows, 120 audit-ready
```

Hidden construction distribution remains:

```text
predicate = hanging on: 240
rank_band = top100_only: 18, rank_101_200: 94, rank_201_500: 128
geometry_bucket = near_overlap: 164, loose_near_no_overlap: 52, loose_near_overlap: 16, near_no_overlap: 8
coverage_proxy = joined_no_uncertainty_flags: 117, joined_with_uncertainty_flags: 123
uncertainty_bucket = none: 117, visual_or_mesh_needed: 123
gt_label_match_status = no_gt_for_pair: 164, pair_has_other_predicate: 76
strict_group_count = 95
visible_endpoint_pair_count = 193
```

## Gate

All source inventory gates passed:

```text
rows_exactly_240 = true
hanging_on_rows_exactly_240 = true
subject_and_object_crops_min_200 = true
possible_covisible_or_same_view_context_min_120 = true
audit_ready_rows_min_200 = true
accept_and_reject_each_audit_ready_min_100 = true
```

## 해석

v69는 v22 `hanging on` strict route가 source-availability 관점에서 audit packet plan으로
넘어갈 수 있음을 확인한 단계다. 240개 row 모두 subject/object crop과 mesh/sequence/multi-view
evidence를 갖고, 73개는 same-frame co-visible strong tier, 167개는 individual visual plus mesh
tier다.

다만 이 결과는 relation reliability label이나 posterior evidence가 아니다. 다음 audit packet
plan은 strong same-frame evidence와 individual-view-plus-mesh evidence tier를 visible packet에서
중립적으로 구분하되, source path, scan id, instance id, rank, geometry bucket, GT-match status,
planned proxy role, strict group id는 visible surface에 노출하지 않아야 한다.

## 산출물

- Script: `tools/reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory.py`
- Artifact root: `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory/`
- Summary: `summary.json`
- Inventory rows: `inventory_rows.jsonl`
- Inventory table: `inventory_table.csv`
- Scan summary: `scan_summary.json`
- Validation errors: `validation_errors.jsonl`
- Report: `report.md`
