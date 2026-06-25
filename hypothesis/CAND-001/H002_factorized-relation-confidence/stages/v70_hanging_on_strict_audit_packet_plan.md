# V70 Hanging-On Strict Audit Packet Plan

## 목적

v69 source inventory를 바탕으로 `hanging on` strict 240-row candidate set의
neutral audit packet plan을 만들었다.

이 단계는 실제 packet image/materialization, label fill, label ingestion,
target-independence audit, posterior smoke가 아니다. Reviewer-visible packet template,
hidden asset manifest plan, visible schema, audit packet contract를 정의하는 것이 목적이다.

## 입력

- Source inventory: `reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory/summary.json`
- Source inventory rows: `reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory/inventory_rows.jsonl`
- Candidate mining summary: `reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining/summary.json`

## 결과

```text
status = h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_plan_ready_for_materialization
next_todo = reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_materialization
rows = 240
primary_rows = 240
audit_packet_plan_gate_pass = true
validation_errors = 0
posterior_smoke_allowed = false
```

Packet/evidence distribution:

```text
rows_by_packet_role = primary_hanging_on_reliability_candidate: 240
rows_by_predicate = hanging on: 240
T1_strong_pair_visual = 73
T2_individual_visual_plus_mesh = 167
hidden_proxy_balance = accept_proxy_supported_candidate: 120, reject_proxy_contradicted_candidate: 120
accept_proxy_tier = T1: 36, T2: 84
reject_proxy_tier = T1: 37, T2: 83
```

## Visible/Hidden Boundary

Visible packet template contains:

- `packet_id`
- `blind_review_id`
- relation text and endpoint labels
- neutral packet role
- evidence tier and neutral evidence summaries
- blank review fields

Hidden manifest preserves:

- `scan_id`, `subgraph_id`, source/instance ids
- original crop/origin image source paths
- `planned_proxy_role_hidden`
- `rank_band_hidden`
- `geometry_bucket_hidden`
- `object_family_pair_hidden`
- `coverage_proxy_hidden`
- `uncertainty_bucket_hidden`
- `gt_label_match_status_hidden`
- `strict_group_value_hidden`

## 해석

v70은 v22 `hanging on` strict route가 audit packet materialization으로 넘어갈 수 있음을
확인한 planning 단계다. T1/T2 evidence tier를 visible packet에서 중립적으로 표시하되,
relation construction shortcut이 될 수 있는 source path, scan/subgraph/instance id, proxy role,
rank band, geometry bucket, GT-match status, strict group id는 visible surface에서 제외했다.

다음 단계는 이 plan에 따라 packet-local neutral asset names를 만들고, visible leakage review로
넘길 수 있는 materialized packet directories를 생성하는 것이다. Label fill과 posterior smoke는
계속 금지된다.

## 산출물

- Script: `tools/reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_plan.py`
- Artifact root: `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_plan/`
- Summary: `summary.json`
- Visible packet template: `visible_packet_template.tsv`
- Packet plan rows: `packet_plan_rows.jsonl`
- Hidden asset manifest plan: `hidden_asset_manifest_plan.jsonl`
- Visible schema: `visible_schema.json`
- Audit packet contract: `audit_packet_contract.json`
- Report: `report.md`
