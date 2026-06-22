# V13 Proximity LH Label Readiness

Date: 2026-06-22 KST

## Purpose

v12 path decision에서 선택한 `proximity / close by` LH-only branch를 label-ready 상태로
준비했다.

이 단계의 목적은 label을 채우는 것이 아니라, reviewer-visible sheet와 hidden audit
manifest를 분리하는 것이다.

```text
visible sheet = reviewer가 볼 수 있는 relation label task
hidden manifest = shortcut / sampling / audit metadata only
```

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v12_proximity_lh_only_label_readiness/
    summary.json
    report.md
    label_ready_sheet.tsv
    hidden_audit_manifest.jsonl
    allowed_review_values.json
    validation_errors.jsonl
    review_cards/
```

Validation errors: `0`

Visible leakage hits: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

Label fill next: `allowed`

## Result

```text
status = h002_reliability_target_v12_proximity_lh_only_label_readiness_ready
rows = 240
unique_blind_review_ids = 240
unique_scans_hidden = 106
unique_label_pairs_hidden = 173
visible_leakage_hits = 0
validation_errors = 0
next_todo = reliability_target_v12_proximity_lh_only_label_fill
```

Reviewer-visible columns:

```text
blind_review_id
review_card
candidate_relation
subject_label
predicate_label
object_label
review_question
relation_reliability_state_v12
primary_reason_v12
uncertainty_reason_v12
review_notes_v12
```

Hidden-only fields:

```text
machine_hint
label_match_status
rank_band
scan_id
semantic_rank
semantic_score
p_geom_valid
geometry_status
subject_object_label_pair
endpoint_cell
exact_endpoint_pair_key
```

## Label Space

Primary state:

```text
accept_reliable_close_by
reject_unreliable_close_by
abstain_uncertain
```

Reason labels:

```text
meaningful_spatial_relation
dense_proximity_noise
possible_missing_annotation
alternative_relation_better
endpoint_or_label_ambiguous
trivial_or_redundant
insufficient_evidence
other
```

## Risk Notes

The sheet is readiness-valid, but not yet target-valid.

Hidden distribution:

```text
label_match_status_hidden = exact_match:80, pair_has_other_predicate:80, no_gt_for_pair:80
rank_band_hidden = rank_101_200:2, rank_201_500:238
max_rows_per_scan_hidden = 4
max_rows_per_label_pair_hidden = 8
```

Important implication:

- label-match strata are balanced.
- scan and label-pair caps are controlled.
- rank diversity is weak, so rank-band leakage must be checked after label ingestion.
- `label_match_status` and `machine_hint` must not be used as target labels or model inputs.

## Next

```text
reliability_target_v12_proximity_lh_only_label_fill
```

Posterior smoke remains blocked until label ingestion and target-independence audit pass.
