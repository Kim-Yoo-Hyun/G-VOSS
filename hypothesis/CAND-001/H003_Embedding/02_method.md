# H003 Method Contract

Last updated: 2026-06-18 KST

## Input Tuple

Initial input tuple:

```text
(predicate, subject_geometry, object_geometry, subject_class, object_class, source_score)
```

Optional later inputs:

- predicate text embedding.
- subject/object text embedding.
- compact geometry feature vector.
- source rank or calibrated source confidence.
- relation family id.
- coverage / uncertainty flags.
- multi-view evidence factor if H002-style visual-geometric extension becomes active.

Do not start with raw point clouds or multi-view crops as the first H003 prototype. The first prototype should use compact, auditable geometry features so shortcut behavior is easy to inspect.

## Representation

Two-tower or shared-encoder variants are possible.

Recommended first contract:

```text
z_sem = f_sem(predicate, subject_class, object_class, source_score)
z_geo = f_geo(subject_geometry, object_geometry, relation_family, coverage_flags)
score = sim(z_sem, z_geo)
```

The compatibility score can be used as:

- binary consistency probability.
- reranking score.
- counterfactual robustness score.
- calibration input for relation reliability.

## Positive Samples

Candidate positive rows:

- GT relation exists and geometry is satisfied.
- audit-confirmed valid relation.
- high semantic + high geometry relation, if provenance is clearly marked as weak supervision.

Positive labels must record provenance:

```text
gt_positive
audit_valid
weak_high_semantic_high_geometry
```

Weak positives should not be mixed with confirmed positives without reporting the label source.

## Negative Samples

Candidate negative rows:

- wrong-pair geometry.
- subject/object swap.
- shuffled geometry from another pair or scene.
- predicate-family label flip.
- vertical order inversion.
- support/contact removal.
- attachment/contact counterfactual if the relation family is later expanded.

Negative labels must record corruption type:

```text
wrong_pair
swap_subject_object
shuffle_geometry_same_scene
shuffle_geometry_cross_scene
predicate_family_flip
vertical_order_inversion
support_contact_removed
```

Avoid treating all unannotated GT-missing relations as negatives. Sparse annotation can create false negatives.

## Loss Candidates

Preferred first-stage objective:

```text
binary consistency classification + margin ranking
```

Reason:

- easier to debug than pure contrastive learning.
- compatible with existing recall/violation metrics.
- permits calibration metrics.

Second-stage objectives:

- contrastive loss.
- triplet loss.
- InfoNCE.

Use contrastive or InfoNCE only after hard-negative policy and split policy are stable.

## Baselines

Required baselines:

| Baseline | Inputs | Purpose |
| --- | --- | --- |
| `source_score_only` | source score/rank | Measures whether source confidence already contains the signal. |
| `semantic_only` | predicate/object classes/source score | Tests object-class and language-prior shortcut. |
| `geometry_only` | compact pair geometry | Tests whether semantics are unnecessary. |
| `explicit_rule_score` | deterministic geometry policy | Tests whether learning adds value beyond H001-style verification. |
| `embedding_compatibility` | semantic + geometry representation | Candidate H003 method. |

## Evaluation Metrics

Primary diagnostic metrics:

- validity AUROC/AUPRC.
- ECE / Brier score.
- hard-negative false-valid rate.
- counterfactual score drop.
- object-class shortcut gap.

Paper-compatible metrics if promoted:

- `R@K`.
- `Violation@K`.
- `Delta R`.
- `Delta V`.
- recall-retention under reranking.

K grid should follow the existing low-K diagnostic convention if reused:

```text
K = {5, 10, 20, 50, 100}
```

`K=1` remains sanity-check only unless separately justified.

## Split Policy

Minimum split rule:

- scene-level split.
- no shared scan/subgraph between train and held-out validation.
- if counterfactual negatives are generated from positives, the original positive and derived negatives stay in the same split.

Additional controls:

- same-family split.
- same-rank-band split.
- object-class-held-out probe.
- source-held-out transfer probe if enough rows exist.

## Promotion Gate

H003 can move from hypothesis docs to prototype implementation only after:

- label provenance schema is frozen.
- positive/negative construction policy is frozen.
- split policy is frozen.
- shortcut controls are specified.
- baseline list is fixed.
- H001 artifacts remain read-only and untouched.

