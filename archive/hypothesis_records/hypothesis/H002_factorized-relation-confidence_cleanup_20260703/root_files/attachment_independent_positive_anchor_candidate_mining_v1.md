# H002 Attachment Independent Positive Anchor Candidate Mining V1

Created: 2026-06-25 KST

## Purpose

`attachment_independent_positive_anchor_mining_plan_v1`에서 고정한 contract에 따라
train-only attachment 후보를 실제로 선택한다.

이 단계의 핵심은 positive anchor를 많이 모으는 것이 아니다. Positive anchor마다 같은
object family, rank band, coverage tier, visible pair, or same-scene 축에서 hard negative를
같이 확보해 mixed strata를 만드는 것이다.

## Runner

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_independent_positive_anchor_candidate_mining_v1.py
```

Default output:

```text
artifacts/attachment_independent_positive_anchor_candidate_mining_v1/
```

## Result

```text
status = h002_attachment_independent_positive_anchor_candidate_mining_v1_ready_mixed_strata
selected_rows = 560
primary_binary_selected = 467
primary_uncertain_buffer_selected = 13
diagnostic_selected = 80
complete_positive_negative_contrast_pairs = 143
validation_errors = 0
next_todo = attachment_independent_positive_anchor_packet_materialization_v1
```

Query counts:

```text
Q1_hanging_on_positive_anchor = 116
Q2_hanging_on_hard_negative = 120
Q3_attached_to_structural_positive_anchor = 118
Q4_attached_to_hard_negative = 113
Q5_connected_near_or_overlap_diagnostic = 40
Q5_connected_far_or_functional_ambiguous_diagnostic = 40
Q6_primary_uncertain_buffer = 13
```

The original plan requested `480` primary binary seed rows. After de-duplicating the already
materialized v18/v20 seed pools, only `467` unique attached/hanging positive-or-negative rows were
available. The remaining `13` rows are included as `primary_uncertain_buffer` for packet audit
coverage, not as binary posterior targets.

## Mixed-Strata Evidence

Selected primary binary rows contain the following contrast structure:

| Stratum | Mixed Groups | Balanced Rows |
| --- | ---: | ---: |
| endpoint family + rank + coverage | 55 | 214 |
| endpoint family + rank | 61 | 280 |
| visible pair | 58 | 312 |
| rank band | 7 | 452 |
| same scene | 40 | 86 |
| same scene + endpoint family + rank | 11 | 28 |

This directly addresses the failure mode where source score, rank, predicate, or endpoint identity
alone can explain the target.

## Positive Anchor Contrast Rule

| Positive Anchor | Required Contrast | Current Handling |
| --- | --- | --- |
| clear `hanging on` accept | similar object pair but no actual contact | `Q1` selected with `Q2` in mixed strata |
| clear `attached to` accept | close or plausible pair but not attached | `Q3` selected with `Q4` in mixed strata |
| wall-object accept | wall-object reject | tracked through visible-pair and endpoint-family mixed groups |
| high-rank accept | high-rank reject | rank band is a control axis, not a selection score |
| visible accept | visible reject | packet requests are generated for both sides |
| same-scene accept | same or similar scene reject | same-scene mixed groups are explicitly reported |

## Outputs

```text
candidate_rows.jsonl
candidate_rows_internal.jsonl
hidden_manifest.jsonl
visible_review_template.csv
asset_request_manifest.jsonl
mixed_strata_summary.csv
summary.json
validation_errors.jsonl
```

`visible_review_template.csv` keeps review fields blank and excludes source score, rank, proxy role,
cell id, machine hints, prior labels, and GT-match status. Those fields are preserved only in
`hidden_manifest.jsonl` for post-label target-independence audit.

## Boundary

- train split only;
- no validation/test usage;
- no posterior training;
- no paper evidence promotion;
- no H001 artifact modification;
- source score/rank are not used as selection scores;
- multi-view/mesh remains audit evidence, not model input.

## Next

```text
attachment_independent_positive_anchor_packet_materialization_v1
```
