# Evaluation

## Dataset / Benchmark

- Real-world benchmark: 3DSSG-O27R16, a cleaned/preprocessed dataset based on 3RScan + 3DSSG.
- Paper-reported real-world setting: over 1000 3D indoor point cloud reconstructions with 27 object classes and 16 relationship categories.
- Synthetic benchmark: SUNCG + SceneGraphNet relationship annotations.
- Additional graph representation checks: Planetoid and MoleculeNet.

## Splits

- Real-world evaluation follows the scene-level split specified by the 3DSSG / SGFN setting.
- Synthetic SUNCG evaluation follows SceneGraphNet splitting and preprocessing.

## Metrics

- Object class prediction: top-k recall, reported as `R@5` and `R@10`.
- Predicate class prediction: macro `F1@3` and `F1@5`, used because predicate categories are imbalanced.
- Relationship triplet prediction: `R@50` and `R@100`, with triplet confidence from subject, predicate, and object scores.
- Synthetic scene evaluation: object classification accuracy across room categories.

## Baselines

- `FB(.) alone`
- SGPN / GCN-style graph reasoning
- GloRe variants
- SGGpoint / EdgeGCN
- For synthetic scenes: GRAINs, Wang et al., MVCNN, SceneGraphNet

## Main Results

On real-world 3D scans:

| Method | Object R@5 | Object R@10 | Predicate F1@3 | Predicate F1@5 | Triplet R@50 | Triplet R@100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Backbone alone | 87.40 | 96.26 | 68.55 | 82.79 | 34.97 | 45.86 |
| SGPN / GCN | 89.61 | 96.98 | 63.58 | 77.79 | 32.45 | 41.65 |
| EdgeGCN / SGGpoint | 90.70 | 97.58 | 78.88 | 90.86 | 39.91 | 48.68 |

Main interpretation: EdgeGCN improves object classification, predicate classification, and triplet prediction, while a naive GCN can improve object recognition but hurt relation/triplet metrics.

On synthetic SUNCG scenes, SGGpoint reports competitive object classification accuracy across bedroom, living room, bathroom, and office settings, using support/surround/next-to relations.

## Reproducibility Notes

- Official project page and code are available.
- The released project describes preprocessing for 3DSSG-O27R16.
- Dataset access requires following 3RScan and 3DSSG terms, then obtaining the preprocessed SGGpoint data.
- The cleaned dataset removes or remaps some classes and relationships, so comparisons with later 3DSSG settings need care.

## Evaluation Weaknesses

- Predicate labels are reduced to 16 structural categories, which may underrepresent semantic/functional relations.
- Metrics evaluate classification accuracy, not explicit geometric consistency.
- Edge features are not separately evaluated as interpretable geometry evidence.
- The dataset preprocessing differs from later 3DSSG/open-vocabulary works, so reproduction may require mapping labels.
- CAND-001 should use SGGpoint as an edge-reasoning baseline, not as a final evaluation protocol.
