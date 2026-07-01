# Compatibility Dataset V2 Candidate Materialization

Artifact root:

```text
artifacts/compatibility_dataset_v2_candidate_materialization/
```

Status:

```text
status = h002_compatibility_dataset_v2_candidate_materialization_ready_for_schema_shortcut_audit
rows = 400
groups = 200
compatibility positive / negative = 200 / 200
raw_witness matched / requested = 400 / 400
validation_errors = 0
learned_smoke_allowed = false
next_todo = compatibility_dataset_v2_schema_shortcut_audit
```

## What Was Materialized

Primary family rows:

```text
support_contact positive / negative = 120 / 120
relative_vertical positive / negative = 80 / 80
```

Predicate balance:

```text
support_contact:
  lying on = 40 positive / 40 negative
  standing on = 40 positive / 40 negative
  supported by = 40 positive / 40 negative

relative_vertical:
  higher than = 40 positive / 40 negative
  lower than = 40 positive / 40 negative
```

Counterfactual types:

```text
support_contact:
  wrong_pair_geometry = 40
  shuffled_geometry = 40
  contact_gap_or_overlap_perturbation = 40

relative_vertical:
  predicate_flip = 40
  subject_object_swap = 40
```

## Important Boundary

This materialization does not promote H002 to a learned smoke result yet.

The rows are train-only candidate rows. Direct HL/LH construction fields remain hidden controls,
not model inputs. `C_e` is still restricted to:

```text
C_e = compatibility(T_e, G_e)
```

`Z_e`, source rank, source score, queue kind, geometry status, target construction fields, and
`p_geom_valid_baseline` are blocked from `C_e`.

## Output Files

```text
compatibility_rows.jsonl
counterfactual_groups.jsonl
baseline_view.jsonl
audit_view.jsonl
selection_manifest.jsonl
schema.json
split_manifest.json
feature_ranges.csv
control_balance.csv
summary.json
validation_errors.jsonl
report.md
```

## Interpretation

This step fixes the previous capacity-scan issue in a narrow way:

- it does not use direct HL/LH labels as the primary target;
- it keeps predicate counts balanced across positive and negative rows;
- it preserves source score/rank as `Z_e`, but excludes them from `C_e`;
- it uses raw numeric geometry as `G_e`;
- it generates relation-specific counterfactual negatives rather than relying on no-GT labels.

The next blocker is whether hidden construction fields or generated-counterfactual artifacts make
the target too easy. That must be checked before any learned smoke.

## Next

```text
compatibility_dataset_v2_schema_shortcut_audit
```
