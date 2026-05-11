# Evaluation

## Dataset / Benchmark

- Distillation/training source: ScanNet, chosen because its RGB-D frames have better field of view for extracting object-pair visual features.
- Quantitative evaluation: 3DSSG / 3RScan, because it provides semantic 3D scene graph labels aligned with 3D scenes.

## Splits

Uses 3DSSG evaluation setup for closed-set comparison. The paper maps open-vocabulary outputs back to the 3DSSG label space for quantitative evaluation.

## Metrics

- Object Recall@5 / Recall@10
- Predicate Recall@3 / Recall@5
- Relationship triplet Recall@50 / Recall@100
- Mean Recall for class-wise evaluation

## Baselines

- Fully supervised: 3DSSG, SGFN, SGRec3D, VL-SAT
- Zero-shot / open-vocabulary baselines: CLIP naive, OpenSeg + CLIP, OpenSeg + NegCLIP, OpenSeg + captioning

## Main Results

On closed-vocabulary 3DSSG evaluation:

- Open3DSG: object R@5 0.57, R@10 0.68; predicate R@3 0.63, R@5 0.70; relationship R@50 0.64, R@100 0.66.
- It outperforms other zero-shot baselines but is below strong fully supervised methods like SGRec3D and VL-SAT on standard closed-set metrics.
- Frequency-based analysis shows better handling of less-common / long-tail classes than some fully supervised approaches.

## Reproducibility Notes

- Code is public but archived/read-only as confirmed on 2026-05-06; inspected source snapshot commit `a568358d6bb718929aa9ff67b2dfdecc4a4c3261`.
- The GitHub README reports requirements around 3RScan, 3DSSG, ScanNet, OpenSeg checkpoints, BLIP2 positional embeddings, PointNet/PointNet2 weights, and large precomputed 2D features.
- Precomputing VLM features can require substantial storage, reported around 300GB per dataset.

## Evaluation Weaknesses

- Open-vocabulary relation text is evaluated by mapping to a fixed set of 3DSSG predicates, which does not fully measure open-set relation quality.
- Metrics do not directly check whether semantic relations are geometrically consistent.
- Standard recall metrics do not separate language hallucination from geometric inconsistency.
