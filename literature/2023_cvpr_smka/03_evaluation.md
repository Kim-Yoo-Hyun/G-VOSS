# Evaluation

## Dataset / Benchmark

- Primary dataset: 3DSSG, derived from 3RScan.
- Main paper setting: 160 object categories and 27 relationship classes.
- Knowledge filtering: object categories collected from SUNRGBD and ScanNet; ConceptNet is filtered to about 760 nodes and 5,000 edges.
- Supplemental data preparation:
  - each input scene is randomly sub-sampled to 40,000 points with XYZ and RGB;
  - each object instance is sampled to 512 points by farthest point sampling;
  - random scaling uses Uniform[0.9, 1.1];
  - rotation augmentation is not used because proximity relations such as left/right depend on heading angle.

## Splits

- Follows the 3DSSG / KISG experimental setting.
- Head/body/tail split:
  - 5 most common relationships as head;
  - 5 least common relationships as tail;
  - remaining relationships as body.

## Metrics

- Main constrained metrics: `R@K` and `mR@K`.
- Tasks:
  - `PredCls`: ground-truth 3D boxes and object labels are given; predict relationships.
  - `SGCls`: ground-truth 3D boxes are given; predict object categories and relationships.
  - `SGDet`: raw point cloud input; detect 3D objects, semantic labels, and relationships.
- Supplemental reports unconstrained `R@K` and `mR@K`, where multiple relationship scores per object pair can be used in ranking.

## Baselines

2D SGG models adapted to 3DSSG:

- IMP
- MOTIFS
- VCTree
- KERN
- Schemata
- HetH

3D SGG baselines:

- SGPN
- EdgeGCN / SGGpoint
- KISG

Implementation references:

- VoteNet is used as the 3D object detection backbone for SGDet.
- Point Cloud Transformer is used for object visual features.

## Main Results

Comparison with 3D point-cloud SGG baselines on 3DSSG:

| Method | PredCls R@50/100 | PredCls mR@50/100 | SGCls R@50/100 | SGCls mR@50/100 |
| --- | --- | --- | --- | --- |
| SGPN | 57.71 / 58.05 | 38.12 / 38.67 | 28.39 / 28.74 | 22.23 / 22.57 |
| EdgeGCN | 58.42 / 59.11 | 38.84 / 39.35 | 28.58 / 28.93 | 22.67 / 23.33 |
| KISG | 64.47 / 64.93 | 63.19 / 63.52 | 29.46 / 29.65 | 28.20 / 28.64 |
| SMKA | 68.32 / 69.49 | 66.54 / 66.92 | 31.50 / 31.64 | 30.29 / 30.56 |

The paper reports:

- `+2.92% R@50` over SGPN in SGCls.
- `+9.90% R@50` over EdgeGCN in PredCls.
- `+2.04% R@50` over KISG in SGCls.

Comparison with adapted 2D SGG baselines:

- SMKA reaches `68.32 / 69.49` PredCls R@50/100 and `66.54 / 66.92` PredCls mR@50/100.
- SMKA reaches `31.50 / 31.64` SGCls R@50/100 and `30.29 / 30.56` SGCls mR@50/100.
- SGDet performance is `29.41 / 29.44` R@50/100 and `25.35 / 25.36` mR@50/100; the paper notes object detection is a bottleneck.

Ablation highlights on SGCls:

- Removing hierarchical tokens: `30.47 / 30.67 R@50/100`, `28.94 / 29.19 mR@50/100`.
- Removing support edges: `30.55 / 30.74 R@50/100`, `29.17 / 29.47 mR@50/100`.
- Removing both: `28.41 / 28.47 R@50/100`, `27.13 / 27.52 mR@50/100`.
- Replacing hierarchical visual graph with fully connected graph: `28.17 / 28.32 R@50/100`, `26.28 / 26.29 mR@50/100`.
- Removing 3D spatial multimodal knowledge embedding: `26.27 / 26.35 R@50/100`, `22.93 / 23.18 mR@50/100`.
- Full SMKA: `31.50 / 31.64 R@50/100`, `30.29 / 30.56 mR@50/100`.

Long-tail analysis:

| Method | Head R@50 | Body R@50 | Tail R@50 |
| --- | --- | --- | --- |
| SGPN | 39.42 | 23.64 | 13.03 |
| EdgeGCN | 39.51 | 23.85 | 13.15 |
| KISG | 40.36 | 24.56 | 13.61 |
| SMKA | 44.23 | 26.27 | 14.73 |

## Reproducibility Notes

- The paper reports implementation in PyTorch.
- Training: one NVIDIA GTX TITAN X GPU, 40 epochs, Adam optimizer, initial learning rate `0.0001`, batch size `4`, learning-rate drops after epochs 15, 25, and 40.
- VoteNet is used for SGDet to generate 256 object candidates.
- The supplemental states object features concatenate 1024-dim Point Cloud Transformer visual feature, 256-dim spatial feature, and 200-dim semantic feature.
- The paper lists code at `https://github.com/HHrEtvP/SMKA`, but the repository was inaccessible during the 2026-04-28 check.

## Evaluation Weaknesses

- The evaluation is closed-set and tied to fixed 3DSSG labels.
- The method improves relation prediction, but it does not output explicit edge-level geometry evidence or a violation flag.
- Support hierarchy is treated as prior knowledge / latent graph structure, not as an inspectable geometric verifier.
- ConceptNet filtering and learned hierarchy labels introduce assumptions that may not transfer to open-vocabulary predicates.
- SGDet gains are limited by 3D object detection, which means CAND-001 should likely start from ground-truth or reliable instance masks.
