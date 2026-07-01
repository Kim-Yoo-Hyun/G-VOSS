# H002 Size-Relative Sanitized View Smoke Runner After Plan

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan/
status = h002_compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan_passed_controls
overall = size_relative_smoke_passed_controls
validation_errors = 0
next_todo = compatibility_dataset_v3_size_relative_smoke_result_review_after_runner
```

This stage runs the train-only grouped-CV learned smoke over the frozen
`size_relative` runner-ready view. It uses no validation/test split and does not
modify H001 artifacts.

## Data

```text
rows = 2400
positive / negative = 1200 / 1200
paired groups = 1200
predicate_counts = bigger than 1200 / smaller than 1200
```

## Main Metrics

| Model | AUROC | Accuracy | Interpretation |
| --- | ---: | ---: | --- |
| `M1_semantic_only_T` | 0.471 | 0.478 | semantic-only shortcut fails |
| `M2_geometry_only_G_size` | 0.500 | 0.500 | same-G target blocks geometry-only solution |
| `M3_TG_concat_no_interaction` | 0.471 | 0.478 | plain concat does not solve the target |
| `M4_TG_size_interaction` | 0.9999 | 0.993 | primary predicate-geometry interaction succeeds |
| `S1_predicate_label_shortcut` | 0.471 | 0.478 | predicate label alone fails |
| `S2_geometry_exact_tuple_shortcut` | 0.500 | 0.500 | exact geometry tuple shortcut fails |
| `C1_wrong_T_same_G` | 0.00009 | 0.0067 | wrong predicate inverts/collapses |
| `C2_shuffled_G_global` | 0.493 | 0.494 | shuffled geometry collapses |
| `C3_shuffled_G_within_predicate` | 0.477 | 0.475 | within-predicate geometry shuffle collapses |
| `C4_sign_flipped_G_control` | 0.00008 | 0.0067 | sign-flipped geometry inverts/collapses |

Paired margin:

```text
mean_positive_minus_negative = 0.838783
positive_margin_fraction = 0.993333
```

## Gate Summary

```text
data integrity = pass
single-factor shortcuts near chance = pass
primary interaction signal = pass
primary gain over single factor = pass
plain concat caveat = false
wrong-T degradation = pass
shuffled-G degradation = pass
sign-flipped-G control = pass
paired score margin = pass
```

## Interpretation

The result supports the `size_relative` predicate-geometry compatibility route:
the same predicate-independent `G_e_size` evidence cannot solve the task alone,
and predicate text cannot solve it alone, but their interaction nearly perfectly
recovers compatibility.

The controls are important:

- wrong-T and sign-flipped-G almost invert the target;
- shuffled-G falls near chance;
- plain concat remains near chance.

This is not a calibrated probability result. `M4_TG_size_interaction` has strong
ranking/decision metrics, but ECE is high, so it should not be used as evidence
that the output probability is calibrated. It is mechanism evidence for
compatibility learning only.

This is still train-only hypothesis evidence. Paper-level use requires Docker
reproduction and a held-out protocol.
