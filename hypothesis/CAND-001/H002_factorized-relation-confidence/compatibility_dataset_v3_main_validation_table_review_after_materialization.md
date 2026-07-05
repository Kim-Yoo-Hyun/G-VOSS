# Main Validation Table Review

## Purpose

Review the materialized H002 main validation table before paper draft insertion.
This stage checks table wording, caveat disclosure, control interpretation, and
blocked claims. It does not run new metrics, tune scores, or touch official test
data.

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_main_validation_table_review_after_materialization/
status = h002_main_validation_table_review_after_materialization_ready
selected_path = main_validation_table_reviewed_select_paper_insertion_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_paper_draft_insertion_plan_after_main_validation_table_review
```

## Interpretation

- `main_validation_table.csv` is acceptable as a validation-level table
  candidate for the primary success families.
- The table must be worded as official 3DSSG validation split evidence, not
  official test evidence.
- The 3 source/family/K Recall@K regression caveats must be disclosed.
- `C_e only` remains a diagnostic ablation because it trades recall for very low
  violation; the deployable score is `S2_source_x_Ce`.
- Wrong-T and shuffled-C_e controls support compatibility-specific
  violation-risk ranking, but the paper should not claim universal recall
  collapse across all controls.

