# Insights

## Facts

- GEODE is a CVPR Findings 2026 paper evaluated on 3DSSG.
- It explicitly conditions relation denoising on updated geometry tokens.
- It reports geometry and update-order ablations.

## Paper Claims

The paper claims state-of-the-art closed-set and open-vocabulary 3DSGG
performance, with strong spatial-predicate gains.

## Inferences

- Geometry-conditioned predicate generation is no longer a defensible H001
  novelty claim.
- H001's boundary must be generator-independent post-prediction reliability,
  not geometry-aware relation learning in general.
- GEODE shares H001's single-3DSSG evidence limitation, but addresses a
  different stage of the pipeline.

## Connection to Field Trends

GEODE reinforces the shift from semantic-only relation reasoning toward
explicit geometry-relation coupling inside generators. H001 complements that
trend by auditing and re-ranking candidate outputs after generation.

## What Would Change This Assessment

A released GEODE adapter that directly re-ranks arbitrary predictor candidates,
or a verifier-derived/human validity evaluation across frozen predictors, would
make it substantially closer to H001.
