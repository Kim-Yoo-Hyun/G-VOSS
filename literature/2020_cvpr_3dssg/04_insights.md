# Insights

## Facts

- 3DSSG explicitly combines semantic annotations with geometric data and human verification.
- Relations are grouped into spatial/proximity, support, and comparative relationships.
- Support relationships rely on local geometric candidates and semantic verification.

## Paper Claims

- 3D semantic scene graphs are compact and robust representations for 3D scene understanding.
- They can bridge modalities such as 2D images and 3D scans for retrieval.

## Inferences

- 3DSSG already supports the intuition behind CAND-001: relation edges should be semantic and geometry-grounded.
- The research gap is not the existence of semantic+geometry relations, but making the geometry evidence explicit, queryable, and usable for open-vocabulary relation verification.
- The taxonomy can guide the first version of CAND-001's verifier: support and proximity predicates are more tractable than comparative or affordance predicates.

## Connection to Field Trends

- Establishes the closed-set 3DSG baseline.
- Supplies the benchmark vocabulary used by SGRec3D, Open3DSG, and CCL-3DSGG.

## Possible Contribution Angles

- Create a predicate-to-geometry-evidence map for 3DSSG.
- Add violation metrics for support/proximity predicates.
- Use 3DSSG as the controlled benchmark before moving to open-vocabulary text.

## What Would Change This Assessment

- If 3DSSG annotations are too noisy or inaccessible, the thesis should use a smaller ReplicaSSG or synthetic subset for geometry-grounding experiments.

