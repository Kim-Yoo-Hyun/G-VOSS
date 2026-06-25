# V72 Hanging-On Strict Audit Packet Leakage Review

## 목적

v71에서 materialize한 `hanging on` strict 240-row audit packet의 visible surface를
formal leakage review했다.

검사 대상은 visible review sheet, packet markdown, packet-local image names, packet index,
hidden manifest separation이다. 이 단계는 label fill, label ingestion, target-independence audit,
posterior smoke가 아니다.

## 입력

- Materialization summary: `reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_materialization/summary.json`
- Visible review sheet: `visible_review_sheet.tsv`
- Packet index: `packet_index.jsonl`
- Materialized hidden manifest: `materialized_hidden_manifest.jsonl`
- Packet markdown and packet-local image names under `packets/`

## 결과

```text
status = h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_leakage_review_passed_ready_for_label_fill
next_todo = reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_fill
formal_leakage_review_pass = true
visible_sheet_rows = 240
packet_markdown_files = 240
packet_dirs = 240
neutral_image_files = 4406
hidden_manifest_rows = 240
hidden_rows_with_source_paths = 240
hidden_rows_with_scan_ids = 240
hidden_rows_with_gt_match_axis = 240
visible_leakage_hits = 0
validation_errors = 0
posterior_smoke_allowed = false
```

GT auxiliary axis remains hidden:

```text
gt_label_match_status = no_gt_for_pair: 164, pair_has_other_predicate: 76
```

## Leakage Boundary

Visible artifacts do not expose:

- source paths
- scan/subgraph identifiers
- instance ids
- construction metadata
- rank bands
- geometry buckets
- planned proxy roles
- strict-group ids
- GT-match fields

Hidden manifest retains these fields for provenance and future mismatch analysis only.

## 해석

v72는 v22 `hanging on` packet surface가 label fill로 넘어갈 수 있음을 확인한 formal gate다.
이제 reviewer-visible packet만 사용한 reliability label fill이 가능하다.

다만 다음 label fill도 posterior evidence가 아니다. Label fill 이후에는 hidden manifest와
사후 join하는 label ingestion, target-independence audit, shortcut probe를 통과해야 posterior
smoke를 허용할 수 있다.

## 산출물

- Script: `tools/reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_leakage_review.py`
- Artifact root: `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_leakage_review/`
- Summary: `summary.json`
- Reviewed visible fields: `reviewed_visible_fields.json`
- Visible leakage hits: `visible_leakage_hits.jsonl`
- Validation errors: `validation_errors.jsonl`
- Report: `report.md`
