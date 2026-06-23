# V40 Attachment Candidate Mining

Date: 2026-06-23 KST

## Purpose

v39 path decision에서 선택한 route에 따라 `attachment_deferred` relation의
hidden-field-safe candidate packet을 만들었다. 이 단계는 label fill이나 posterior smoke가
아니라 label-ready packet 생성이다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v18_attachment_deferred_candidate_mining/
    summary.json
    report.md
    label_ready_sheet_v18.tsv
    hidden_audit_manifest_v18.jsonl
    selected_candidates_internal.jsonl
    cell_summary.csv
    visible_leakage_hits.jsonl
    validation_errors.jsonl
    review_cards_v18/
```

Validation errors: `0`

Visible leakage hits: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Status

```text
status = h002_reliability_target_v18_attachment_deferred_candidate_mining_ready_for_label_fill
next_todo = reliability_target_v18_attachment_deferred_label_fill
selected_rows = 240
```

## Result

```text
primary_binary_candidate_rows = 160
diagnostic_rows = 60
uncertainty_audit_rows = 20
attached_to_rows = 82
hanging_on_rows = 96
connected_to_rows = 62
unique_scans = 202
unique_subgraphs = 230
unique_directed_pairs = 240
unique_visible_label_pairs = 199
```

Cell counts:

```text
A1 attached supported = 40
A2 attached counter/uncertain = 40
H1 hanging supported = 40
H2 hanging counter/uncertain = 40
C1 connected near/overlap diagnostic = 30
C2 connected counter/uncertain diagnostic = 30
U1 missing/uncertain coverage audit = 20
```

## Hidden-Field Policy

Visible sheet includes object labels, predicate label, directed relation text, 3D layout summary,
coverage summary, and ambiguity summary.

Hidden manifest keeps construction fields:

```text
cell_id
provisional_status
anchor_bucket
rank_band
machine_hint
geometry_status
reason_family
sampling_queue
semantic rank/score
label match status
raw feature dictionary
```

This means v18 is label-ready, not posterior-ready. The next label fill must use only the visible
sheet / review cards, not the hidden manifest.

## Boundary

This is train-only candidate construction evidence.

It is not:

- a filled label set
- target-independence evidence
- posterior performance evidence
- validation/test evidence
- paper-level benchmark evidence

## Next

```text
reliability_target_v18_attachment_deferred_label_fill
```
