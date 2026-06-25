# V73 Hanging-On Strict Audit Packet Label Fill

## 목적

v72 leakage review를 통과한 `hanging on` strict 240-row audit packet을 사용해
visible-only reliability label을 채웠다.

이 단계는 label materialization이다. Hidden manifest, source path, scan id, existing
GT-match axis, proxy role, strict group id, rank/score, geometry bucket, `p_geom_valid`,
validation/test split은 label fill에 사용하지 않았다.

## 입력

- Materialization summary: `reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_materialization/summary.json`
- Leakage review summary: `reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_leakage_review/summary.json`
- Visible review sheet: `visible_review_sheet.tsv`
- Packet index: `packet_index.jsonl`
- Packet markdown and packet-local image availability

## 결과

```text
status = h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_filled_codex_visible_packet
next_todo = reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingestion
rows = 240
validation_errors = 0
hidden_manifest_read = false
posterior_smoke_allowed = false
```

Label distribution:

```text
review_relation_reliability =
  accept_reliable: 9
  reject_unreliable: 193
  abstain_uncertain: 38

review_geometry_support =
  supports: 9
  contradicts: 193
  ambiguous: 38

review_endpoint_identity =
  clear_endpoint_identity: 199
  uncertain_endpoint_identity: 41

review_coverage =
  sufficient: 71
  limited: 169

review_uncertainty =
  low: 64
  medium: 137
  high: 1
  visual_ambiguous: 13
  endpoint_ambiguous: 25
```

Primary binary preview:

```text
binary_primary_usable_rows = 202
primary_positive_rows = 9
primary_negative_rows = 193
abstain_rows = 38
```

Decision reasons:

```text
implausible_hanging_subject = 71
support_or_proximity_confound = 71
missing_hanging_anchor_or_wrong_relation_family = 35
generic_endpoint_label = 25
duplicate_or_self_like_endpoint = 16
mountable_pair_limited_pair_context = 13
strong_hanging_subject_anchor_pair = 9
```

## 해석

v73 결과는 v22 strict packet이 posterior smoke로 바로 갈 수 있다는 뜻이 아니다.
오히려 visible-only reliability target이 매우 positive-sparse하다는 강한 경고다.

accept된 row는 `curtain/blinds/towel/bag`이 `door/window/stand` 계열 anchor에 걸린
명확한 hanging pair에 제한됐다. 대부분의 row는 `pillow-bed`, `chair-curtain`,
`cabinet-object`, `shelf-table`, `window-curtain`처럼 support/proximity, reversed endpoint,
generic endpoint, 또는 wrong relation family로 판정됐다.

따라서 다음 단계는 posterior가 아니라 label ingestion이다. Ingestion은 label lock 이후에만
hidden manifest와 GT-match auxiliary axis를 사후 join하고, class mass, endpoint/object/predicate,
evidence-tier, hidden proxy/strict-group shortcut risk를 검사해야 한다.

## 산출물

- Script: `tools/reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_fill.py`
- Artifact root: `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_fill/`
- Filled sheet: `filled_visible_review_sheet_v22.tsv`
- Label decisions: `label_decisions_v22.jsonl`
- Summary: `summary.json`
- Report: `report.md`
- Validation errors: `validation_errors.jsonl`
