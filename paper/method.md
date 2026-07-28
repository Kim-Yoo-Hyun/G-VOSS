# RelCompat3D Method Guide

Last updated: 2026-07-28 KST

## 1. Research Task

RelCompat3D is a post-hoc reliability layer for fixed 3D scene graph relation
predictions. It estimates whether a predicted predicate is compatible with the
reconstructed geometry of the corresponding ordered subject--object pair, then
uses that estimate for constrained re-ranking.

It does not replace the source relation predictor or generate new candidates.

## 2. Candidate Representation

Each candidate is

\[
r_i=(\mathrm{scan}_i,\mathrm{context}_i,s_i,o_i,p_i,a_i,Z_i),
\]

where:

- \(s_i,o_i\) are ordered subject and object instance identifiers;
- \(p_i\) is the predicate;
- \(a_i\) is the mapped relation family;
- \(Z_i\) is the source relation score.

Two identities are distinguished:

\[
k_i^{\rm pair}=(\mathrm{scan}_i,\mathrm{context}_i,s_i,o_i)
\]

for geometry association and

\[
k_i^{\rm rel}=(\mathrm{scan}_i,\mathrm{context}_i,s_i,p_i,o_i)
\]

for exact-match evaluation.

## 3. Separated Inputs

- \(T_i=p_i\): predicate semantics.
- \(a_i\): relation family and transformation/routing selector.
- \(G_i\): predicate-independent measurements of the ordered pair.
- \(Z_i\): source score, excluded from compatibility estimation.

\(G_i\) contains OBB-derived 3D and XY distances, relative height, projected
overlap, and vertical-gap features. Point-level contact evidence is used only
by the support/contact verifier.

## 4. Scope

\[
\mathcal A_{\rm eval}
=
\{\text{support/contact},\text{proximity},\text{vertical order}\},
\]

\[
\mathcal A_{\rm rank}
=
\{\text{proximity},\text{vertical order}\}.
\]

Support/contact is evaluated but remains in source order. Its compatibility
head exists only for the Product (all families) scope comparison.

## 5. Compatibility Estimators

For \(q\in\{\mathrm{lin},\mathrm{mlp}\}\),

\[
C_i^q=\sigma(f_q(T_i,a_i,G_i)).
\]

This is a bounded ranking score, not a posterior probability of physical
validity.

### RelCompat3D-Linear

The family label selects a family-specific head and normalization statistics.
The feature vector contains:

- intercept;
- predicate indicators;
- standardized geometry;
- signed-height interactions
  \(d(p_i)\Delta z_i\) and \(d(p_i)\Delta z_i^{\rm norm}\).

\[
\Delta z_i=z_{s_i}-z_{o_i},\qquad
\Delta z_i^{\rm norm}
=
\frac{2\Delta z_i}{h_{s_i}+h_{o_i}}.
\]

### RelCompat3D-MLP

The nonlinear estimator is one shared MLP with a two-unit ReLU hidden layer
and a predicate-linear skip path. It receives family and predicate indicators,
the same geometric primitives, signed-height interactions, and the sum of the
directional overlap ratios.

Both estimators exclude:

- source relation score;
- source rank;
- predictor identity;
- object-class features.

## 6. Training Construction

Training-split ground truth provides positives.

- Proximity negatives use distant, non-overlapping same-context pairs.
- Vertical-order negatives retain the endpoints and replace the predicate
  with its inverse.
- Support/contact negatives are defined by the full rules in the supplement.
- Relation-preserving augmentation swaps proximity endpoints without changing
  the predicate and jointly swaps vertical endpoints with the inverse
  predicate.

Evaluation rows, evaluation labels, source relation scores, and primary
verifier-status labels do not enter target construction.

The loss is

\[
\mathcal L_q
=
\mathcal L_{\rm BCE}
+\lambda_{\rm pair}\mathbb E_{\mathcal P}
\left[
\operatorname{softplus}
\left(m-(\ell^q_{i^+}-\ell^q_{i^-})\right)
\right]
+\lambda_{\rm reg}\mathcal R(\theta_q).
\]

Final settings:

- \(m=1\);
- \(\lambda_{\rm pair}=0.25\);
- \(\lambda_{\rm reg}=10^{-4}\);
- Linear: 800 full-batch gradient-descent steps, learning rate 0.2;
- MLP: 120 full-batch Adam steps, learning rate 0.02.

## 7. Transformation Averaging

For proximity, \(\tau_a\) swaps endpoints and leaves “close by” unchanged.
For vertical order, it swaps endpoints and exchanges “higher than” and
“lower than”. Support/contact uses only the identity.

For transformation orbit

\[
\mathcal O_i=\{g(T_i,G_i):g\in H_{a_i}\},
\]

the final compatibility is

\[
C_i^{\rm tr,q}
=
\frac{1}{|\mathcal O_i|}
\sum_{(T',G')\in\mathcal O_i}
\sigma(f_q(T',a_i,G')).
\]

This makes proximity symmetry and the vertical endpoint/inverse-predicate
identity exact at inference.

## 8. Within-Family Score

\[
u_i^q=
\begin{cases}
Z_iC_i^{\rm tr,q}, & a_i\in\mathcal A_{\rm rank},\\
Z_i, & a_i=\text{support/contact}.
\end{cases}
\]

The source score is introduced only here.

## 9. Family-Aware Re-Ranking

1. Record the relation-family label at every source position.
2. Sort proximity and vertical-order candidates independently by \(u_i^q\).
3. Keep the support/contact family subsequence in source order.
4. Fill each source position from the next unused candidate in its original
   family queue.

The output preserves:

- source relation-family sequence;
- support/contact identities and order;
- highest within-family utilities for each prefix, subject to those
  constraints.

The rule is composition-preserving, not claimed to maximize aggregate Recall
or Violation across arbitrary cross-family competition.

## 10. Main Controls

- RankAvg and RRF test alternative fusion.
- Product (all families) changes the support/contact scope.
- Wrong predicate tests predicate dependence.
- Wrong pair and shuffled geometry test ordered-pair association.
- Fixed-predicate swap tests transformation semantics.
- Distance-only tests whether a simple distance ranking suffices.
- Compatibility-only tests whether \(C\) can replace \(Z\).

The supplement adds direct component removals, simple compatibility baselines,
score mappings, seeds, routing controls, feature removals, and oracles.

## 11. Terminology Contract

Use consistently:

- predicate--geometry compatibility;
- ordered-pair identity;
- ordered-pair measurements;
- source relation score;
- transformation averaging;
- family-aware re-ranking;
- exact-match Recall@\(K\);
- verifier-derived Violation@\(K\);
- point- and mesh-based consistency audit.

Use **validation split** for the dataset partition and **validation scenes** for
the evaluated scenes. Do not use compatibility and physical validity as
synonyms.

## 12. Claim Boundary

RelCompat3D does not claim:

- calibrated correctness probability;
- independent ground truth for physical validity;
- relation generation;
- support/contact correction;
- dataset-level generalization;
- universal routing or fusion optimality.
