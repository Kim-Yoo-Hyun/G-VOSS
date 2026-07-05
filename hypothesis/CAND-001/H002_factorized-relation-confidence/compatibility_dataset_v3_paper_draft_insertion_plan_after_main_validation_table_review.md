# Paper Draft Insertion Plan

## Purpose

Lock where and how the reviewed H002 validation table can enter a paper draft.
This stage stays in the H002 hypothesis folder because it fixes claim wording
before manuscript editing. It does not run new metrics, tune scores, or use
official test data.

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_paper_draft_insertion_plan_after_main_validation_table_review/
status = h002_paper_draft_insertion_plan_after_main_validation_table_review_ready
selected_path = paper_draft_insertion_plan_locked_no_manuscript_edit
validation_errors = 0
next_todo = compatibility_dataset_v3_h002_paper_outline_or_integration_decision_after_insertion_plan
```

## Interpretation

- The reviewed validation table can be used as an H002 paper/results draft
  candidate.
- This gate does not edit the current H001 manuscript.
- The table must be described as official 3DSSG validation evidence, not
  official test or SOTA evidence.
- The caption, footnote, blocked wording, and draft snippets are frozen in the
  generated artifact.
- The next decision is whether to open an H002 paper outline/integration path or
  keep the result as a hypothesis artifact.

