# Compatibility Dataset V3 Independent Validity Stratum Repair Smoke Result Review

Artifact root:

```text
artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review/
```

## Status

```text
status = h002_compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review_accept_Ce_select_calibration_scope_plan
selected_path = accept_independent_validity_Ce_smoke_select_calibration_and_scope_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_calibration_scope_plan
```

## Decision

The repaired independent-validity smoke is accepted as the current strongest H002 `C_e` mechanism
evidence. It fixed the earlier shortcut and geometry-dominance blockers:

| Item | Value |
| --- | ---: |
| semantic/source max AUROC | 0.568110 |
| geometry-only AUROC | 0.527064 |
| `M6_TG_compatibility_interaction` AUROC | 0.995633 |
| `M7_factorized_TZGQ` AUROC | 0.995280 |
| wrong-predicate control AUROC | 0.026644 |
| primary ECE-10 | 0.480112 |

## Allowed Claim

On a train-only exact-stratum repaired independent-validity target, semantic/source features and
predicate-independent geometry alone are insufficient, while an explicit predicate-conditioned
compatibility factor

```text
C_e = compatibility(T_e, G_e)
```

separates valid and invalid relation candidates.

## Blocked Claims

- calibrated relation reliability posterior;
- paper-level result;
- held-out validation/test performance;
- broad all-relation 3DSSG reliability;
- support/contact independent-validity generality from this artifact;
- attachment/proximity/horizontal relation generality.

## Family Scope

| Family | Rows | Verdict | Notes |
| --- | ---: | --- | --- |
| `relative_vertical` | 1512 | primary supported | `M6` AUROC `0.999990`, geometry-only `0.524527`, wrong-predicate `0.000000` |
| `support_contact_pose_conditioned` | 88 | diagnostic only | `M6` AUROC `0.702479`, geometry-only `0.576446`, wrong-predicate `0.603306` |

The global result is relative-vertical dominant. Support/contact shows a small positive signal but
is not strong enough in this artifact to support a primary generality claim.

## Main Risks

- `calibration_gap`: primary `ECE-10 = 0.480112`, so the score is not a calibrated reliability probability.
- `relative_vertical_dominance`: `1512/1600` rows are relative vertical.
- `too_clean_target`: AUROC is near-perfect, so the target may be mechanism-clean rather than open-world hard.
- `train_only_evidence`: no validation/test or Docker paper experiment is involved.
- `architecture_overfitting`: adding a larger model now would hide calibration/scope issues.

## Next

```text
compatibility_dataset_v3_independent_validity_calibration_scope_plan
```
