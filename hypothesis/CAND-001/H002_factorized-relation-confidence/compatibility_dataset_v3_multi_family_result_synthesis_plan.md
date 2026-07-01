# H002 Multi-Family Result Synthesis Plan

## Status

```text
stage = compatibility_dataset_v3_multi_family_result_synthesis_plan
status = h002_compatibility_dataset_v3_multi_family_result_synthesis_plan_ready
selected_path = freeze_two_family_Ce_claim_select_independent_validity_target_plan
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_target_plan
```

## Artifact

```text
script = tools/compatibility_dataset_v3_multi_family_result_synthesis_plan.py
artifact_root = artifacts/compatibility_dataset_v3_multi_family_result_synthesis_plan/
relative_vertical_input = artifacts/compatibility_dataset_v3_result_review_and_family_extension_decision/
support_contact_input = artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_result_review/
```

Generated files:

- `summary.json`
- `claim_boundary.json`
- `next_plan_contract.json`
- `family_evidence_table.csv`
- `reviewer_risk_table.csv`
- `route_table.csv`
- `validation_errors.jsonl`
- `report.md`

## Synthesis Decision

Current H002 evidence now supports a two-family `C_e` mechanism claim:

```text
Across relative-vertical and support/contact pose-conditioned relation families,
predicate-independent geometry evidence G_e is not sufficient by itself.
Relation compatibility requires an explicit semantic-geometry compatibility
factor C_e that conditions geometry interpretation on semantic content T_e.
```

This is the right claim boundary for the current artifacts.

It is not yet:

- broad 3D Scene Graph relation reliability;
- final `p_rel` / `p_obs` decision quality;
- human-audited reliability performance;
- all-family generality;
- paper-level Docker-reproduced evidence.

## Family Evidence

| Family | Predicates | Primary Result | Main Control Result | Role |
| --- | --- | --- | --- | --- |
| `relative_vertical` | `higher than`, `lower than` | `M5b` AUROC `1.000` | G-only `0.500`, concat `0.446`, wrong-T `0.000`, shuffled-G `0.478/0.515` | first scoped `C_e` proof |
| `support_contact_pose_conditioned` | `lying on`, `standing on` | `M5b` AUROC `1.000` | G-only `0.500`, concat `0.382`, wrong-T `0.000`, shuffled-G `0.525/0.568` | second scoped `C_e` proof |

Common mechanism:

- rows are built as same-`G_e` predicate-contrast groups;
- geometry-only cannot solve the target because paired rows share geometry evidence;
- semantic-only/source-only are not enough;
- no-interaction concatenation is not enough;
- explicit `T_e`-conditioned `G_e` interaction is the successful factor;
- wrong-`T_e` and shuffled-`G_e` controls degrade the result.

## Reviewer-Risk Decision

The dominant risk is no longer "does the mechanism exist?" but "does it transfer to a validity
target independent from the constructed same-`G_e` labels?"

| Risk | Severity | Decision |
| --- | --- | --- |
| constructed target | high | keep as mechanism proof only |
| too clean AUROC | medium | use as isolation evidence, not deployable robustness |
| limited family scope | medium | two families are enough to justify the mechanism, not all-family generality |
| no final reliability target | high | keep `p_rel` / `p_obs` blocked |
| not Docker paper evidence | high | do not create paper experiment root yet |

## Route Decision

Selected:

```text
freeze_two_family_Ce_claim_select_independent_validity_target_plan
```

Rejected or deferred:

- adding attachment/proximity immediately;
- promoting two-family `C_e` as broad reliability;
- creating Docker paper experiment before independent validity target design.

## Next

The next step should design a train-side independent validity target before adding more relation
families.

```text
compatibility_dataset_v3_independent_validity_target_plan
```

Candidate target sources:

- GT relation match versus `C_e` support/conflict;
- human/audit accept-reject subset with hidden construction fields excluded;
- high-precision cross-source agreement plus geometry-supported positive anchors;
- wrong-pair or predicate-flip hard negatives matched by source rank, object family, and coverage.

The next stage should decide whether `p_rel` / `p_obs` can be tested, or whether H002 should remain
at the `C_e` mechanism-proof level.

## Boundary

- Train-only H002 synthesis plan.
- No validation/test usage.
- No new learned model trained in this step.
- No H001 artifact modification.
- No paper-level evidence promotion.
