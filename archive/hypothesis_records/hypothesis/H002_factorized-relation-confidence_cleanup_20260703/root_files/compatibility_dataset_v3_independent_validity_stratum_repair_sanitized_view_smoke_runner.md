# Compatibility Dataset V3 Independent Validity Stratum Repair Smoke Runner

Artifact root:

```text
artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner/
```

## Status

```text
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner_passed_controls
rows = 1600
positive / negative = 800 / 800
groups = 1097
mixed_label_groups = 491
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review
```

## Result

| Model | AUROC | Role |
| --- | ---: | --- |
| `M1_semantic_only_T` | 0.416131 | semantic-content shortcut baseline |
| `M2_source_only_Z` | 0.568110 | source-confidence shortcut baseline |
| `M3_semantic_source_TZ` | 0.533226 | non-geometry shortcut baseline |
| `M4_geometry_only_G` | 0.527064 | predicate-independent geometry baseline |
| `M5_TG_concat` | 0.480008 | plain concatenation baseline |
| `M6_TG_compatibility_interaction` | 0.995633 | primary `C_e` compatibility model |
| `M7_factorized_TZGQ` | 0.995280 | full factorized view |
| `S1_predicate_x_class_pair_shortcut` | 0.353567 | repaired exact-stratum shortcut probe |
| `S2_source_rank_score_shortcut` | 0.548804 | score/rank shortcut probe |
| `C1_shuffled_G_global` | 0.514618 | aligned-geometry negative control |
| `C2_shuffled_G_within_predicate` | 0.458553 | within-predicate aligned-geometry control |
| `C3_wrong_predicate_family_control` | 0.026644 | wrong-predicate control |

## Gate Decision

All planned smoke gates passed:

- semantic/source shortcut max AUROC is `0.568110`, below the `0.60` gate;
- best primary AUROC is `0.995633`, above the `0.65` gate;
- best primary gain over semantic/source is `0.427523`, above the `0.05` gate;
- geometry-only AUROC is `0.527064`, so the primary margin over geometry-only is `0.468569`;
- shuffled-geometry controls fall near chance;
- wrong-predicate control collapses to `0.026644`, consistent with predicate-conditioned geometry use.

The result is therefore not the previous geometry-only dominance failure. On this repaired target,
the model needs the compatibility interaction between `T_e` and aligned `G_e_raw`.

## Boundary

This is train-only grouped-CV hypothesis evidence. It is not paper-level evidence, not a held-out
validation/test result, and not a calibrated probability claim. `ECE-10` is high for the primary
models, so the current evidence supports discrimination/ranking of compatibility, not calibrated
posterior reliability.

`support_contact_pose_conditioned` remains diagnostic in this artifact because it contributes only
`88` of `1600` rows. The primary learned conclusion is still relative-vertical dominant until a
larger support/contact-independent target is materialized or a separate result review justifies the
scope.

## Output Files

```text
summary.json
metrics.json
metrics.csv
metrics_by_family.json
paired_score_drop.json
folds.json
predictions.jsonl
error_cases_m6.jsonl
gate_results.csv
report.md
validation_errors.jsonl
```

## Next

```text
compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review
```
