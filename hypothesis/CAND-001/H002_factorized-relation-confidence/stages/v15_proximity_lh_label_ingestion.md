# V15 Proximity LH Label Ingestion

Date: 2026-06-22 KST

## Purpose

v14에서 채운 `proximity / close by` LH-only visible proxy labels를 hidden audit manifest와
`blind_review_id`로 join하고, multiclass/binary target artifact를 만들었다.

이 단계는 posterior smoke가 아니라 ingestion + quick shortcut probe다.

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v12_proximity_lh_only_label_ingestion/
    summary.json
    report.md
    ingested_rows.jsonl
    multiclass_target.jsonl
    binary_target.jsonl
    abstain_rows.jsonl
    quick_probe_risks.json
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Result

```text
status = h002_reliability_target_v12_proximity_lh_only_label_ingested_with_probe_risk
rows = 240
multiclass_rows = 240
binary_rows = 107
abstain_rows = 133
accept_reliable_close_by = 36
reject_unreliable_close_by = 71
abstain_uncertain = 133
quick_probe_risk_flags = 10
next_todo = reliability_target_v12_proximity_lh_only_target_independence_audit
```

Hidden audit distribution:

```text
label_match_status_hidden = exact_match:80, pair_has_other_predicate:80, no_gt_for_pair:80
machine_hint_hidden = 80/80/80 across the corresponding construction hints
rank_band_hidden = rank_101_200:2, rank_201_500:238
```

## Quick Probe Finding

The ingested target is not posterior-ready.

Strong shortcut risks:

```text
subject_object_label_pair_hidden -> multiclass accuracy = 1.0000
subject_object_label_pair_hidden -> binary accuracy = 1.0000
subject_object_visible_pair -> multiclass accuracy = 1.0000
subject_object_visible_pair -> binary accuracy = 1.0000
scan_id -> multiclass accuracy = 0.8750
scan_id -> binary accuracy = 0.9720
```

Moderate object-label risks:

```text
subject_label -> binary NMI = 0.2522
object_label -> binary NMI = 0.2740
```

Interpretation:

- This proxy label is dominated by visible object-pair semantics.
- This is expected because v14 deliberately used visible object labels only.
- Therefore the ingested target is useful diagnostic material but not yet a valid posterior target.

## Boundary

Allowed:

- Use this artifact for target-independence audit.
- Use it to diagnose why visible-only proxy labels are insufficient.

Blocked:

- posterior smoke
- paper metric evidence
- claim that factorized reliability improves relation reliability

## Next

```text
reliability_target_v12_proximity_lh_only_target_independence_audit
```

The next stage must decide whether a controlled slice exists. If not, this branch should be marked
diagnostic-only or repaired with a less object-pair-driven label source.
