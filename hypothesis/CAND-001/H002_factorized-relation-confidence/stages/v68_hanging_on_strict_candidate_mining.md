# V68 Hanging-On Strict Candidate Mining

## 목적

v67 packet plan의 hidden-only preview를 사용해 `hanging on` strict primary route의
hidden-field-safe candidate sheet를 만들었다.

이 단계는 packet asset materialization, label fill, label ingestion, target-independence audit,
posterior smoke가 아니다. Reviewer-visible candidate sheet와 hidden manifest를 분리해 다음
source inventory 단계로 넘기는 것이 목적이다.

## 입력

- Packet plan: `reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan/summary.json`
- Hidden preview: `reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan/hidden_selection_preview.jsonl`

## 결과

```text
status = h002_reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining_ready_for_source_inventory
next_todo = reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory
candidate_rows = 240
visible_rows = 240
hidden_rows = 240
visible_leakage_hits = 0
validation_errors = 0
posterior_smoke_allowed = false
```

Hidden distribution:

```text
predicate_counts = hanging on: 240
planned_proxy_role_counts = 120 / 120
rank_band_counts = top100_only: 18, rank_101_200: 94, rank_201_500: 128
geometry_bucket_counts = near_overlap: 164, loose_near_no_overlap: 52, loose_near_overlap: 16, near_no_overlap: 8
coverage_proxy_counts = joined_no_uncertainty_flags: 117, joined_with_uncertainty_flags: 123
uncertainty_bucket_counts = none: 117, visual_or_mesh_needed: 123
gt_label_match_status_counts = no_gt_for_pair: 164, pair_has_other_predicate: 76
strict_group_count = 95
scan_count = 192
visible_endpoint_pair_count = 193
```

## Field Boundary

Reviewer-visible sheet에는 relation text와 blank review fields만 둔다.

Visible:

- `blind_review_id`
- `candidate_relation`
- `subject_label`
- `predicate_label`
- `object_label`
- relation review prompts
- blank review fields

Hidden manifest only:

- `scan_id`, `subgraph_id`, instance ids, `prediction_id`
- `rank_band`
- `geometry_bucket`
- `object_family_pair`
- `coverage_proxy`
- `uncertainty_bucket`
- `gt_label_match_status`
- `planned_proxy_role`
- `strict_group_value`

## 해석

v68은 `hanging on` strict target을 label-ready로 만든 것이 아니라, source inventory와 이후
audit packet materialization을 시작할 수 있는 candidate sheet를 만든 단계다. Visual/mesh evidence는
아직 packet-local neutral assets로 복사되지 않았다.

다음 source inventory에서는 각 candidate의 scan, multi-view, sequence, mesh/crop availability를
확인해야 한다. Source inventory가 통과해야 audit packet plan/materialization으로 넘어갈 수 있다.

## 산출물

- Script: `tools/reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining.py`
- Artifact root: `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining/`
- Summary: `summary.json`
- Visible candidate sheet: `visible_candidate_sheet.tsv`
- Hidden candidate manifest: `hidden_candidate_manifest.jsonl`
- Candidate rows: `candidate_rows.jsonl`
- Visible schema: `visible_schema.json`
- Leakage report: `visible_leakage_report.json`
- Report: `report.md`
