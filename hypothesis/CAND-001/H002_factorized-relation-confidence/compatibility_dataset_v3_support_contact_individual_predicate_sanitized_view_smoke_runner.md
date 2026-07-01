# H002 Support/Contact Individual Predicate Sanitized View Smoke Runner

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_runner/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_runner_diagnostic_only_failed_controls
rows = 640
positive / negative = 320 / 320
predicates = lying on 320 / standing on 320
groups = 258
mixed_label_groups = 155
validation_errors = 0
learned_smoke_executed = true
next_todo = compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis
```

## Main Result

| Model | AUROC | AUPRC | Accuracy |
| --- | ---: | ---: | ---: |
| `M1_semantic_only_T` | 0.4108 | 0.4424 | 0.4313 |
| `M2_geometry_only_G` | 0.5092 | 0.4988 | 0.5000 |
| `M3_TG_concat` | 0.4538 | 0.4555 | 0.4703 |
| `M4_TG_predicate_geometry_interaction` | 0.6316 | 0.6132 | 0.5828 |
| `M5_TGQ_factorized_observability` | 0.6316 | 0.6132 | 0.5828 |
| `S1_predicate_label_shortcut` | 0.4000 | 0.4371 | 0.4266 |
| `S2_class_pair_shortcut` | 0.4789 | 0.4774 | 0.4828 |
| `S3_quality_shortcut` | 0.4820 | 0.4807 | 0.4844 |
| `C1_wrong_T_same_G` | 0.3589 | 0.4078 | 0.4141 |
| `C2_shuffled_G_global` | 0.5223 | 0.5212 | 0.5297 |
| `C3_shuffled_G_within_predicate` | 0.4695 | 0.4673 | 0.4828 |

## Gate Interpretation

Passed:

- data integrity
- semantic/quality shortcut controls
- gain over `T_e` or `G_e`
- geometry-dominance check
- interaction over plain concat
- wrong-T same-G degradation
- shuffled-G degradation
- group contrast margin

Failed:

- primary predictive signal: `M4/M5 AUROC = 0.6316`, below the planned `0.70` gate.

This means the current support/contact individual-predicate target has real but weak
predicate-geometry compatibility signal. It is not solved by geometry-only evidence
(`M2 = 0.5092`) and not by semantic/class shortcuts, but the signal is not strong enough
to promote this branch as main learned compatibility evidence.

## Important Interpretation

This is not the same failure as the earlier grouped support/contact target.

- Earlier grouped support/contact failed because class-pair or construction shortcuts
  dominated.
- This individual-predicate target passed shortcut controls.
- The remaining issue is weaker separability: `standing on` versus `lying on` is only
  partially captured by current semseg OBB pose/contact features.

`Q_e` does not change the result because all rows share the same evidence profile:

```text
mesh=True
point=False
view=False
```

So this artifact cannot validate observability routing yet.

## Boundary

- train-only grouped-CV smoke
- no validation/test usage
- no paper-level evidence
- no H001 artifact modification
- support/contact individual-predicate result remains diagnostic

## Next

```text
compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis
```
