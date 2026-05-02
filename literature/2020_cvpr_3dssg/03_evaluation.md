# Evaluation

## Dataset / Benchmark

3DSSG extends 3RScan with semantic scene graph annotations.

Reported dataset scale in the paper:

- 1482 3D reconstructions.
- 478 naturally changing indoor environments.
- 48k object nodes.
- 544k edges.
- 534 object classes.
- 40 object relationships.
- 93 attributes on approximately 21k object instances.
- 363k graph-image pairs can be rendered from the 3D graphs and RGB-D images.

## Relationship Taxonomy

- Spatial / proximity relationships: e.g. next to, in front of.
- Support relationships: e.g. standing, lying, supported by; support candidates are derived from neighboring instances within a small radius and then verified.
- Comparative relationships: derived from attributes, e.g. bigger than, darker than, cleaner than, same shape as.

## Splits

The paper follows the train/test splits from 3RScan and evaluates graph prediction on 3DSSG.

## Metrics

- Relationship triplet R@50 / R@100.
- Object class R@5 / R@10.
- Predicate R@3 / R@5.
- Scene retrieval Top-1 / Top-3 / Top-5 with graph matching coefficients.

## Baselines

- A relation prediction baseline adapted from visual relationship detection.
- Single predicate model.
- Multi-predicate model.
- GCN-feature variant.

## Main Results

Table 2 reports:

- Multi Predicate, ObjCls from PointNet features: relationship R@50 0.40, R@100 0.66; object R@5 0.68, R@10 0.78; predicate R@3 0.89, R@5 0.93.
- Relation Prediction Baseline: relationship R@50 0.39, R@100 0.45; object R@5 0.66, R@10 0.77; predicate R@3 0.62, R@5 0.88.

## Reproducibility Notes

- Dataset project page is public.
- Access to 3RScan/3DSSG data may require following dataset-specific terms.

## Evaluation Weaknesses

- Closed-set evaluation.
- Original benchmark does not evaluate open-vocabulary text relations.
- It does not expose geometry violation rate as a metric, despite using geometry in annotation construction.

