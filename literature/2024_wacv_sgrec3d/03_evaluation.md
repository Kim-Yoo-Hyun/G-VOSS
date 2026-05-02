# Evaluation

## Dataset / Benchmark

- Main evaluation: 3DSSG / 3RScan.
- Pretraining data: 3DSSG, ScanNet, S3DIS, and combinations.

## Splits

The paper follows previous 3DSSG train/evaluation splits. It reports that 3DSSG has 160 object classes, 27 relationship categories, over 1,000 3D indoor reconstructions, and over 4,000 subgraph samples; it also notes the dataset has 478 different scenes.

## Metrics

- Object R@5 / R@10
- Predicate R@3 / R@5
- Relationship R@50 / R@100
- Class-wise mean recall: object mR@5, predicate mR@3
- Rule-based verification for generated/reconstructed scene relationships

## Baselines

- 3D + MSDN, KERN, BGNN
- SGGPoint
- 3DSSG
- Liu et al.
- SGFN
- Point-cloud pretraining baselines: STRL, DepthContrast

## Main Results

On 3DSSG:

- SGRec3D reports object R@5 0.80, R@10 0.87; predicate R@3 0.97, R@5 0.99; relationship R@50 0.89, R@100 0.91.
- Compared with SGFN, the paper reports +10% on object prediction and +4% on relationship prediction.
- Class-wise mean recall improves strongly for body/tail classes.
- The model can use 5%-10% labeled data after pretraining and still outperform the same model trained from scratch.

## Reproducibility Notes

- Project page is public.
- Code link was not found on the project page during this pass.
- Requires access to 3DSSG/3RScan; pretraining can also use ScanNet/S3DIS.

## Evaluation Weaknesses

- Closed-set labels dominate the evaluation.
- High predicate recall suggests saturation for some standard metrics.
- Does not evaluate open-vocabulary relation generation.
- Geometry consistency is partly checked through simple rule-based predicates, but not used as the main relation evaluation.

