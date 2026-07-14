# Relation-Algebra Compatibility Development

Status: `completed`

This is a retrospective 3DSSG-only method-development branch for testing a
stronger RelCompat3D mechanism. It compares the existing family product with
relation-algebra projection, transform-augmented training, linked
counterfactual margin training, their combination, and an algebra-constrained
feature basis.

The branch is designed to answer the novelty objection that RelCompat3D is
only a generic engineered-feature recalibrator. Every new compatibility model
keeps source confidence, source rank, source identity, and source-specific
exact-label supervision out of `C_e`. The intended distinction is structural:
the score should satisfy the known algebra of `close by` and inverse vertical
predicates and should order each exported counterfactual below its linked
positive.

This experiment cannot support dataset-level generalization, prospective
confirmation, family-uniform improvement, independent physical validity, or a
best-rescorer claim. All frozen attempts must be reported, including failures.

Run through the `relation_algebra_development` service in
`configs/h001/compose.structured.yaml`. Compact outputs are written to `evaluation/`; no
row-level duplicate of the multi-gigabyte source verification files is
materialized.

## Result

The Docker run completed on 2026-07-13 with all 15 integrity validations
passing. Of the six new conditions, only
`orbit_pairwise_projected_product` passes every frozen gate. It combines the
fixed linked-counterfactual margin objective with parameter-free orbit
projection at inference. Projection makes proximity swap error and vertical
inverse-equivariance error exactly zero on 2,106 and 566 internal-development
rows, respectively. Linked-positive win rate rises from 0.991752 to 0.992321
over 3,516 paired examples.

At K=100, the passing condition obtains R/V of `0.9688/0.0325` on VL-SAT,
`0.6055/0.0339` on Open3DSG, and `0.9418/0.0372` on SGFN. Relative to the strict
train-only family product, Recall changes by `-0.00025`, `-0.00302`, and
`+0.00025`; every paired Recall CI remains above the frozen `-0.01`
continuity guard. The candidate also passes the joint Recall--Violation gate
against the original source score on all three sources.

The result strengthens a relation-algebra-constrained compatibility mechanism,
but it does not show score-formula superiority: Open3DSG verifier V is
essentially unchanged and the SGFN-supervised nonlinear comparator remains
stronger on SGFN. Canonical result files are under `evaluation/`.
