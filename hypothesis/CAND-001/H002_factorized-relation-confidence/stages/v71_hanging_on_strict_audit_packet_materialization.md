# V71 Hanging-On Strict Audit Packet Materialization

## 목적

v70 audit packet plan을 실제 packet directory와 packet-local neutral image assets로
materialize했다.

이 단계는 label fill, label ingestion, target-independence audit, posterior smoke가 아니다.
Visible review sheet와 packet markdown에는 neutral packet-local filenames만 노출하고,
source paths, scan/subgraph/instance ids, construction metadata, GT-match axis는 hidden
manifest에만 보존한다.

## 입력

- Plan summary: `reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_plan/summary.json`
- Visible packet template: `reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_plan/visible_packet_template.tsv`
- Hidden asset manifest plan: `reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_plan/hidden_asset_manifest_plan.jsonl`
- GT auxiliary source: `match_rows.jsonl`

## 결과

```text
status = h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_materialization_ready_for_leakage_review
next_todo = reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_leakage_review
visible_review_rows = 240
packet_dirs = 240
materialized_hidden_manifest_rows = 240
total_materialized_images = 4406
visible_leakage_hits = 0
validation_errors = 0
posterior_smoke_allowed = false
```

Evidence and auxiliary GT distribution:

```text
rows_by_packet_role = primary_hanging_on_reliability_candidate: 240
rows_by_evidence_tier = T1_strong_pair_visual: 73, T2_individual_visual_plus_mesh: 167
gt_match_axis_joined_rows = 240
gt_label_match_status = no_gt_for_pair: 164, pair_has_other_predicate: 76
```

## Visible/Hidden Boundary

Visible artifacts:

- `visible_review_sheet.tsv`
- packet-local `packet.md`
- packet-local image names such as `subject_crop_01.jpg`, `object_view_03.jpg`

Hidden artifacts:

- source image paths
- `scan_id`, `subgraph_id`, subject/object ids
- `planned_proxy_role_hidden`
- `rank_band_hidden`
- `geometry_bucket_hidden`
- `object_family_pair_hidden`
- `coverage_proxy_hidden`
- `uncertainty_bucket_hidden`
- `strict_group_value_hidden`
- existing GT relation match axis

## 해석

v71은 reviewer가 볼 수 있는 audit packet surface를 만들었지만, 아직 formal leakage review와
label fill을 수행하지 않았다. 현재 `visible_leakage_hits = 0`은 materialization script 내부
검사 결과이며, 다음 단계에서 별도 formal leakage review로 visible sheet, packet markdown,
packet-local image names, hidden manifest separation을 다시 확인해야 한다.

GT auxiliary axis는 hidden manifest에만 보존했다. 이후 label fill 이후에는 human-audited
reliability label과 existing GT relation match를 비교해 다음 mismatch table을 만들 수 있다.

```text
GT match & reliability accept
GT match & reliability reject
No GT & reliability accept
No GT & reliability reject
Abstain
```

## 산출물

- Script: `tools/reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_materialization.py`
- Artifact root: `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_materialization/`
- Visible review sheet: `visible_review_sheet.tsv`
- Packet index: `packet_index.jsonl`
- Materialized hidden manifest: `materialized_hidden_manifest.jsonl`
- Packet directories: `packets/`
- Visible leakage hits: `visible_leakage_hits.jsonl`
- Validation errors: `validation_errors.jsonl`
- Summary: `summary.json`
- Report: `report.md`
