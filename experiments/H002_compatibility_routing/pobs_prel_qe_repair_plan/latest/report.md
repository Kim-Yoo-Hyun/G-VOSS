# Q_e Repair Plan

## Why This Repair Is Needed

The p_obs failure is not a posterior-combination failure. It is a Q_e representation failure: the hidden labels distinguish observable, ambiguous, and missing-evidence rows, while the model-safe Q_e view still marks every label group as sufficient.

```text
p_obs_AUROC = 0.500000
p_rel_AUROC = 0.774704
decision_macro_F1 = 0.331637
```

## Repaired Q_e Schema

| Block | Purpose | Examples |
| --- | --- | --- |
| Q_e_asset_availability | distinguish missing evidence from usable evidence | has_mesh, has_point_pair_crop, has_contact_surface_proxy, subject_has_obb, object_has_obb |
| Q_e_visual_coverage | separate observable_clear from no-view or low-quality visual evidence | co_visible_view_count, min_crop_quality, subject_visible_ratio, object_visible_ratio, occlusion_proxy |
| Q_e_geometry_quality | measure whether geometry can support the target route decision | geometry_feature_coverage, surface_patch_available, local_point_density_near_contact, normal_available |
| Q_e_ambiguity | represent ambiguity even when geometry exists | support_subtype_candidate_count, standing_lying_pose_conflict, class_pair_subtype_entropy, competing_predicate_count |
| Q_e_state_v2 | replace the static sufficient-only state | q_e_state_sufficient_v2, q_e_state_limited_v2, q_e_state_ambiguous_v2, q_e_state_missing_v2 |

## Pass / Fail Gates

| Gate | Threshold | Reason |
| --- | --- | --- |
| schema_separation | validation_errors=0 and blocked_field_hits=0 | Q_e v2 must not leak hidden observability labels |
| qe_label_alignment | ambiguous/missing rows are not all q_e_sufficient_v2=1 | directly fixes the observed Q_e mismatch |
| p_obs_signal | p_obs AUROC >= 0.70 on user-confirmed subset | minimum evidence that observability is learnable |
| abstain_behavior | ambiguous/missing abstain recall >= 0.70 and observable abstain false-positive <= 0.30 | p_obs must actually abstain on uncertain evidence |
| calibration_sanity | p_obs ECE@10 <= 0.20 for diagnostic, <= 0.10 for paper promotion | avoid claiming calibrated observability from uncalibrated scores |
| paper_promotion | all diagnostic gates pass plus independently authored or clearly user-confirmed label provenance | paper-level p_obs/p_rel solved claim requires more than diagnostic rerun |

## Next Step

`pobs_prel_qe_repair_materialization` should build a repaired Q_e v2 view and a balanced p_obs train/eval protocol before any new p_obs/p_rel solved-claim attempt.
