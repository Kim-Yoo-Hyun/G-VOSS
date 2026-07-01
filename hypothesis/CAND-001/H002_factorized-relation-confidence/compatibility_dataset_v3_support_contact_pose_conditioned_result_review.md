# H002 Support/Contact Pose-Conditioned Result Review

## Status

```text
stage = compatibility_dataset_v3_support_contact_pose_conditioned_result_review
status = h002_compatibility_dataset_v3_support_contact_pose_conditioned_result_review_accept_scoped_Ce_select_multi_family_synthesis
selected_path = accept_support_contact_Ce_mechanism_proof_select_multi_family_synthesis
validation_errors = 0
next_todo = compatibility_dataset_v3_multi_family_result_synthesis_plan
```

## Artifact

```text
script = tools/compatibility_dataset_v3_support_contact_pose_conditioned_result_review.py
artifact_root = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_result_review/
input_artifact = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner/
```

Generated files:

- `summary.json`
- `path_decision.json`
- `route_table.csv`
- `family_table.csv`
- `caveat_table.csv`
- `next_plan_contract.json`
- `validation_errors.jsonl`
- `report.md`

## Decision

The support/contact pose-conditioned smoke result is accepted as a scoped `C_e`
mechanism proof.

Allowed claim:

```text
scoped predicate-geometry compatibility mechanism for support/contact pose-conditioned relations
```

This means the result supports the following limited statement:

```text
The same predicate-independent support/contact geometry evidence G_e can be
compatible or incompatible depending on semantic content T_e, and this cannot be
explained by source score, predicate-only, geometry-only, object-pair-only,
quality-only, or no-interaction concatenation baselines in this controlled target.
```

It does not yet support broad relation reliability.

## Evidence

Key runner metrics reviewed:

```text
rows = 400
paired_groups = 200
M1_source_only_Z_safe AUROC = 0.500
M2_semantic_only_T AUROC = 0.382
M4_geometry_only_G AUROC = 0.500
M5a_compatibility_TG_concat AUROC = 0.382
M5b_compatibility_TG_pose_interaction AUROC = 1.000
M6_factorized_sanitized_TZGQ_pose_interaction AUROC = 1.000
C1_wrong_T_same_G_control AUROC = 0.000
C2_shuffled_G_global_control AUROC = 0.525
C3_shuffled_G_within_predicate_control AUROC = 0.568
paired_mean_positive_minus_negative = 0.915326
```

Interpretation:

- `M5b` succeeds only when `T_e` and `G_e` are correctly aligned through the
  pose-conditioned interaction.
- Source-only, semantic-only, geometry-only, quality-only, object-pair-only, and
  no-interaction baselines do not explain the target.
- Wrong-`T_e` and shuffled-`G_e` controls degrade as expected.
- The result is train-only and controlled; it is not a deployable reliability
  model result.

## Claim Boundary

Blocked claims:

- broad relation reliability
- final `p_rel` / `p_obs` decision quality
- human-audited relation reliability performance
- all 3DSSG relation-family generality
- paper-level Docker-reproduced result

Main caveats:

| Caveat | Severity | Meaning | Required Mitigation |
| --- | --- | --- | --- |
| `constructed_target` | high | labels are controlled pose-compatibility labels, not independent human reliability labels | claim only `C_e` mechanism proof |
| `too_clean_auc` | medium | AUROC 1.0 can reflect the intentionally clean mechanism target | add harder external and multi-family checks |
| `calibration_not_established` | medium | current ECE is diagnostic only | run calibration after target scope is frozen |
| `paper_evidence_not_yet` | high | this is not Docker-reproduced paper evidence | promote only after experiment protocol is frozen |

## Family Decision

| Family | Current Status | Decision |
| --- | --- | --- |
| `relative_vertical` | passed scoped `C_e` mechanism | retain as first compatibility mechanism result |
| `support_contact_pose_conditioned` | passed scoped `C_e` mechanism | retain as second compatibility mechanism result |
| `support_contact_superordinate` | diagnostic only | do not use as primary negative |
| `attachment_like` | deferred hard family | wait for visual/mesh evidence axis |
| `proximity` | future generality | defer until multi-family claim boundary is stable |
| `relative_horizontal` | deferred | define reference-frame semantics first |

## Next

The next step should not add another relation family immediately. It should first
synthesize the `relative_vertical` and `support_contact_pose_conditioned` results
into one multi-family claim boundary.

```text
compatibility_dataset_v3_multi_family_result_synthesis_plan
```

Success condition for the next stage:

- one concise allowed-claim statement;
- family-by-family evidence table;
- explicit reviewer risk table;
- decision on next family versus external validation;
- Docker promotion prerequisites.

## Boundary

- Train-only H002 decision artifact.
- No validation/test usage.
- No new learned model trained in this step.
- No H001 artifact modification.
- No paper-level evidence promotion.
