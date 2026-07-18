# Evaluation

## Dataset / Benchmark

3DSSG only, under closed-set and held-out-predicate open-vocabulary settings.

## Splits

The paper follows its stated official 3DSSG partition and masks one-third of
predicate classes for open-vocabulary training.

## Metrics

- Predicate Classification R@K and mR@K.
- Relationship Triplet R@K and mR@K.
- Spatial-only R@K/mR@K, including strict top-1 evaluation.

## Baselines

Closed-set 3DSGG models and open-vocabulary systems including RelationField,
CCL-3DSGG, Open3DSG, ConceptGraphs, and an open-world 3DSGG method.

## Main Results

GEODE reports improvements across the standard and spatial-only evaluations.
The geometry-token removal and reversed update-order ablations substantially
reduce spatial recall, supporting the geometry-first generator design.

## Reproducibility Notes

The proceedings PDF reports a four-RTX-4090 training setup, 150 diffusion
steps, token/codebook sizes, optimization settings, and ablations. The official
CVF page did not expose a code link at the 2026-07-16 check.

## Evaluation Weaknesses

- One dataset does not establish cross-dataset transfer.
- The spatial-only protocol differs from H001's verifier-derived violation
  evaluation.
- Generator-level gains do not test transfer to multiple frozen predictors.
