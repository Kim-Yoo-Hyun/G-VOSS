# p_obs / p_rel Observability Metric Review

## Decision

The diagnostic rerun does not pass. `p_rel` has usable signal on user-confirmed observable rows, but `p_obs` fails to distinguish observable from ambiguous or missing evidence.

```text
p_obs_AUROC = 0.500000
p_obs_ECE_10 = 0.446174
p_rel_AUROC = 0.774704
p_rel_ECE_10 = 0.083819
decision_macro_F1 = 0.331637
diagnostic_metric_pass = false
paper_promotion_pass = false
```

## Cause

The failure is a `Q_e` feature/label mismatch. The hidden labels now include ambiguous and missing-evidence cases, but the model-safe `Q_e` view still marks every group as sufficient.

| Label | Rows | Q_e Sufficient Rows | Alignment |
| --- | ---: | ---: | --- |
| ambiguous_evidence | 126 | 126 | mismatch |
| observable_clear | 135 | 135 | aligned_or_partial |
| unobservable_missing_evidence | 4 | 4 | mismatch |

## Next Repair

| Priority | Repair | Reason |
| ---: | --- | --- |
| 1 | replace_static_Qe_state_with_audit_aligned_Qe_features | current Q_e marks ambiguous/missing labels as sufficient |
| 2 | add_visual_mesh_coverage_features | observability requires view count, crop quality, mesh/contact surface availability, and occlusion signals |
| 3 | add_support_contact_pose_ambiguity_features | most abstain rows are support/contact single-subtype ambiguity, not missing geometry |
| 4 | materialize_balanced_observability_train_rows | current p_obs train protocol uses synthetic missing controls, while eval labels are user-confirmed ambiguity labels |
| 5 | rerun_pobs_only_before_full_prel_decision | p_rel already has signal; p_obs is the bottleneck |

## Claim Boundary

`p_obs/p_rel` remains a framework component, not a solved calibrated reliability result. The next experiment should repair `Q_e` before any new p_obs/p_rel solved-claim attempt.
