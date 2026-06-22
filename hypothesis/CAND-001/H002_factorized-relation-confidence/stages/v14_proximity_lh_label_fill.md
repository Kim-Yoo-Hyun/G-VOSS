# V14 Proximity LH Label Fill

Date: 2026-06-22 KST

## Purpose

v13에서 준비한 240-row `proximity / close by` LH-only visible sheet를 Codex proxy로
채웠다.

중요한 boundary:

```text
input = reviewer-visible sheet only
hidden_audit_manifest_read = false
posterior_smoke_allowed = false
paper_evidence_allowed = false
```

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v12_proximity_lh_only_label_fill/
    summary.json
    report.md
    filled_label_sheet.tsv
    label_decisions.jsonl
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Hidden manifest read: `false`

Posterior smoke: `blocked`

## Result

```text
status = h002_reliability_target_v12_proximity_lh_only_label_filled_codex_proxy_visible_only
rows = 240
accept_reliable_close_by = 36
reject_unreliable_close_by = 71
abstain_uncertain = 133
binary_usable_rows = 107
next_todo = reliability_target_v12_proximity_lh_only_label_ingestion
```

Reason distribution:

```text
meaningful_spatial_relation = 36
dense_proximity_noise = 51
alternative_relation_better = 20
insufficient_evidence = 133
```

## Label Policy

The label fill used a conservative visible-only policy:

- accept only when the visible object pair forms a plausible nontrivial close-by relation.
- reject same-label object pairs as dense proximity noise.
- reject storage/object pairs when containment or support is likely the better relation.
- abstain when text-only object labels are insufficient.

This is intentionally conservative because the visible sheet contains no scene image, geometry metric,
semantic rank, source score, or hidden audit metadata.

## Interpretation

This stage establishes that a filled proxy target exists, not that the target is independent.

The next stage must ingest the labels, join the hidden audit manifest, and audit shortcuts:

```text
rank_band
label_match_status
machine_hint
subject_object_label_pair
scan_id
```

Posterior smoke remains blocked until the target-independence audit passes.
