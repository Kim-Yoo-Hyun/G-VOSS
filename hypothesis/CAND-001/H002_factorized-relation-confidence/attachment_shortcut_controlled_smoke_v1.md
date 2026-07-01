# H002 Attachment Shortcut-Controlled Smoke V1

Date: 2026-06-25 KST

## Purpose

`attachment_numeric_geometry_smoke_v1`에서 확인된 핵심 blocker는 hidden construction
probe가 높다는 점이었다.

```text
T+G AUROC = 0.9282
hidden construction probe AUROC = 0.8767
```

이번 단계의 목적은 attachment target을 더 작은 controlled slice로 줄이더라도,
hidden construction cell shortcut을 제거했을 때 `T_e + G_e` compatibility signal이
남는지 확인하는 것이다.

## Runner

Command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_shortcut_controlled_smoke_v1.py
```

Input:

```text
artifacts/attachment_numeric_geometry_v1/
```

Output:

```text
artifacts/attachment_shortcut_controlled_smoke_v1/
```

## Controlled Slice

Selection rule:

```text
for each hidden construction cell:
  keep only cells with both positive and negative Task-A rows
  downsample each cell to min(positive_count, negative_count)
  build paired grouped-CV rows
```

Result:

```text
rows = 34
positive / negative = 17 / 17
pair groups = 17
hidden cells = 4
validation_errors = 0
```

Selected hidden cells:

```text
A1_attached_near_anchor_supported_candidate = 16 rows
A2_attached_far_or_floor_confound_candidate = 6 rows
H1_hanging_anchor_supported_candidate = 10 rows
H2_hanging_no_anchor_or_floor_supported_candidate = 2 rows
```

`U1_attachment_missing_or_uncertain_coverage_audit` is excluded because it has no positive rows.

## Metrics

Task:

```text
Task A = binary predicate-geometry compatibility
```

| Model | AUROC | AUPRC | F1@0.5 |
| --- | ---: | ---: | ---: |
| `M1_source_only_Z` | 0.5467 | 0.6208 | 0.5789 |
| `M2_semantic_source_TZ` | 0.9585 | 0.9694 | 0.8649 |
| `M3_geometry_only_G` | 0.7232 | 0.6631 | 0.7368 |
| `M4_compatibility_TG` | 0.9550 | 0.9593 | 0.8889 |
| `M5_factorized_TZGQ` | 0.9689 | 0.9719 | 0.8889 |
| `S1_predicate_family_shortcut` | 0.5000 | 0.5705 | 0.6667 |
| `S2_source_rank_shortcut` | 0.5156 | 0.5845 | 0.3871 |
| `H0_hidden_cell_only_probe` | 0.5000 | 0.5705 | 0.6667 |
| `H1_hidden_construction_probe` | 0.5000 | 0.5705 | 0.6667 |
| `H2_hidden_witness_score_probe` | 0.5000 | 0.5705 | 0.6667 |

## Gate Result

```text
controlled_dataset = pass
compatibility_signal = pass
geometry_signal = pass
hidden_control = pass
overall = attachment_controlled_smoke_passed_promote_to_larger_controlled_mining
```

Key finding:

```text
T+G AUROC = 0.9550
hidden best AUROC = 0.5000
source-only AUROC = 0.5467
geometry-only AUROC = 0.7232
```

The earlier hidden construction shortcut does not survive this strict within-cell balanced slice.
This supports the interpretation that attachment numeric `G_e` can carry real compatibility signal.

## Boundary

This is not paper evidence.

Reasons:

- the controlled slice has only `34` rows;
- the slice is selected from a previously constructed diagnostic artifact;
- no validation/test split is used;
- no paper model is trained;
- the result only decides whether larger controlled mining is worth doing.

## Decision

Attachment remains a promising H002 extension.

The correct next step is not direct promotion into the combined main prototype. The correct next step
is to design a larger controlled attachment mining pass that preserves the same shortcut-control
logic while increasing row count and predicate coverage.

Next TODO:

```text
attachment_controlled_expansion_plan_v1
```

