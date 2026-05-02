# Insights

## Facts

- SMKA is a CVPR 2023 paper on 3D scene graph prediction from point clouds.
- It evaluates on 3DSSG with 160 object categories and 27 relationship classes.
- It uses a hierarchical physical-support prior, ConceptNet-derived symbolic knowledge, Point Cloud Transformer features, and graph reasoning.
- It reports stronger PredCls and SGCls results than SGPN, EdgeGCN/SGGpoint, and KISG.
- The official code link listed by the paper was inaccessible during the 2026-04-28 check.

## Paper Claims

- 3D physical space has hierarchical regularities that help relation prediction.
- Pure geometric feature classification and text-only prior knowledge are insufficient for complex 3D relationships.
- A hierarchical symbolic knowledge graph plus region-aware visual graph can regularize the semantic space of relationship prediction.
- The accumulated multimodal knowledge improves robustness to label noise and helps long-tail relationships.

## Inferences

- SMKA is one of the strongest closed-set precedents for CAND-001 because it explicitly links 3D spatial structure with textual/common-sense knowledge.
- Its limitation is also exactly where CAND-001 can differentiate: the relation edge is still a predicted label, not an evidence-bearing object.
- CAND-001 should not claim novelty from "using spatial knowledge" or "using symbolic knowledge" alone. SMKA already does that in 3DSSG.
- A sharper CAND-001 claim is: expose and evaluate edge-level geometric evidence rather than using support hierarchy only as a latent regularizer.

## Connection to Field Trends

- Extends the closed-set 3DSSG line after SGPN and SGGpoint by adding symbolic/textual knowledge and physical support hierarchy.
- Sits between SGGpoint and VL-SAT:
  - SGGpoint: explicit edge modeling with point-cloud features.
  - SMKA: 3D spatial hierarchy plus symbolic/textual knowledge accumulation.
  - VL-SAT: visual-language semantic assistance for long-tail and unseen triplets.
- Supports the broader trend that relation prediction needs more than object geometry: it needs structured priors, semantic context, and spatial reasoning.

## Possible Contribution Angles

- Use SMKA as a closed-set baseline or paper-level comparison for spatial-knowledge-guided relation prediction.
- Convert SMKA-style support hierarchy into explicit edge evidence:
  - support candidate;
  - supporting surface;
  - same-support context;
  - hierarchy layer;
  - geometry consistency score.
- Compare latent knowledge regularization against explicit geometry verification for support/proximity predicates.
- Build a small CAND-001 ablation: semantic proposal only vs semantic proposal + SMKA-style hierarchy prior vs semantic proposal + explicit geometry verifier.

## What Would Change This Assessment

- If the SMKA code becomes accessible, it could become a practical closed-set baseline for CAND-001.
- If CAND-001 chooses purely open-vocabulary relation generation without 3DSSG comparability, SMKA becomes background motivation rather than a baseline.
- If the thesis focuses on support hierarchy specifically, SMKA should become a central comparison point.
