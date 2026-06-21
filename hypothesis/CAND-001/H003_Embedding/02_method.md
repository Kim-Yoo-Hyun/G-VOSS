# H003 Method Contract

Last updated: 2026-06-20 KST

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

The first H003 gate uses M3 before M2.

M3 factorized posterior:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e, interactions)
```

where:

- `S_e`: semantic evidence such as source score/rank and predicate/object semantics.
- `G_e`: compact object-pair geometry evidence or explicit geometry score.
- `C_e`: geometry coverage and evaluability state.
- `U_e`: uncertainty / unsupported / low-evidence state.
- `interactions`: combinations such as high-semantic / low-geometry.

This is the first deployable reliability model because it is easier to audit and
compare against existing score-combination baselines.

M2 embedding is the second-stage representation-learning method. Two-tower or
shared-encoder variants are possible.

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

Preferred first-stage objective for M3:

```text
binary reliability classification with calibrated probability
```

Preferred second-stage objective for M2:

```text
binary consistency classification + margin ranking
```

Reason:

- easier to debug than pure contrastive learning.
- compatible with existing recall/violation metrics.
- permits calibration metrics.

Later objectives:

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
| `semantic_times_geometry` | source score x geometry score | Tests the naive H001-adjacent combination. |
| `factorized_posterior` | semantic + geometry + coverage + uncertainty + interactions | First H003 method target. |
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
