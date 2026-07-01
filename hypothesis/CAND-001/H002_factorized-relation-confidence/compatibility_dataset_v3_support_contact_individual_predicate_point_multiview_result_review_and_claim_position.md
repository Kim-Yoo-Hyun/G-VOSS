# H002 Support/Contact Point/Multiview Result Review And Claim Position

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position/
status = h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_claim_position_ready_for_multi_family_synthesis
selected_path = paper_position_support_contact_compatibility_route_evidence_with_caveat_keep_internal_near_threshold
validation_errors = 0
next_todo = compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview
```

## Claim Position

Support/contact is retained as:

```text
main compatibility-route evidence with caveat
```

It is not retained as:

```text
fully solved relation family
high absolute-performance support/contact branch
paper-level evidence
```

Internal status remains conservative:

```text
M8 = 0.699375
internal gate = 0.70
internal status = near-threshold diagnostic
```

The internal gate is not rewritten. The paper-facing interpretation uses the
baseline/control pattern, not the internal management threshold.

## Allowed Wording

Recommended claim:

> For support/contact relations, predicate-geometry interaction provides the
> strongest signal, while semantic-only, geometry-only, and plain concatenation
> baselines fail and wrong-predicate or shuffled-geometry controls collapse.

Recommended longer sentence:

> In support/contact relations, neither semantic content nor point-contact
> geometry alone explains the target. Predicate-conditioned interaction is the
> only setting that separates the target from wrong-predicate and shuffled-geometry
> controls, indicating that this family requires compatibility reasoning rather
> than fixed semantic-geometry fusion.

## Main Numbers

| Signal | AUROC |
| --- | ---: |
| `M8_TG_point_contact_interaction` | 0.699375 |
| `M1_semantic_only_T` | 0.442480 |
| `M5_point_contact_geometry` | 0.470249 |
| `M7_TG_point_contact_concat` | 0.434658 |
| `M9_TGQ_factorized_observability` | 0.694619 |
| `C1_wrong_T_same_G` | 0.273125 |
| `C2_shuffled_G_global` | 0.506240 |
| `C3_shuffled_G_within_predicate` | 0.463857 |
| `lying on` slice | 0.692578 |
| `standing on` slice | 0.707930 |

## Relation Route Table

| Family | Paper Role | Status |
| --- | --- | --- |
| `relative_vertical` | main mechanism evidence | `retain_main_route` |
| `support_contact` | main route evidence with caveat | `retain_main_route_with_caveat` |
| `support_contact_superordinate` | diagnostic only | `defer_primary_claim` |
| `proximity` | generality/control, not main compatibility proof | `diagnostic_only` |
| `attachment_like` | future/diagnostic unless visual/mesh evidence is promoted | `defer` |
| `relative_horizontal` | future work | `defer` |

## Reviewer Risks

- AUROC `0.699` is not high enough for a “solved support/contact” claim.
- Internal gate remains diagnostic, but that gate is not a paper evaluation metric.
- `Q_e` must stay observability/selective-decision evidence because `M9` does not beat `M8`.
- Support/contact residual class-pair difficulty should be reported as failure taxonomy.
- This is H002 hypothesis evidence, not Docker/held-out paper evidence.

## Decision

Selected path:

```text
paper_position_support_contact_compatibility_route_evidence_with_caveat_keep_internal_near_threshold
```

Meaning:

- keep the internal near-threshold diagnostic status;
- use support/contact as H002 paper-facing compatibility-route evidence;
- reject fully solved / high absolute-performance wording;
- reject direct `Q_e` truth interpretation;
- proceed to multi-family claim synthesis before adding more families or stronger combiners.

## Next

```text
compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview
```
