# Evaluation

## Dataset / Benchmark

- Primary dataset: 3DSSG, derived from 3RScan.
- Paper-reported scale for experiments: 1553 reconstructed indoor scenes, 160 object classes, 26 predicate types.
- Data preparation and train/validation split follow 3DSSG.
- Additional qualitative check: ScanNet with relationships manually parsed from ScanRefer descriptions; this is not a native quantitative 3DSG benchmark.

## Splits

- Uses the same data preparation and training/validation split as 3DSSG.
- Tail/body/head predicate split is based on predicate frequency in the 3DSSG training set.
- Unseen triplets are relation triplets that do not appear in the training set but appear in validation.

## Metrics

- Object classification: `A@k`.
- Predicate classification: `A@k` and class-balanced `mA@k`.
- Triplet prediction: triplet score from subject, predicate, and object scores; `A@k` / `mA@k`.
- SGCls / PredCls comparison: `R@20/50/100` and `mR@20/50/100`.
- Tail evaluation: head/body/tail predicate `mA@3` and `mA@5`.
- Unseen/seen triplet evaluation: `A@50` and `A@100`.

## Baselines

- SGPN
- SGFN
- SGGpoint
- non-VL-SAT 3D-only baseline
- CoOccurrence
- KERN
- Schemata
- Zhang et al. knowledge-inspired 3D scene graph prediction

## Main Results

- Compared with `non-VL-SAT`, VL-SAT improves predicate `mA@1/3/5` by about 12.0, 6.8, and 6.0 points.
- Compared with SGFN on tail predicates, VL-SAT improves tail predicate `mA@3` from 38.67 to 52.38 and `mA@5` from 58.21 to 66.13.
- On unseen triplets, VL-SAT improves `A@50` from 22.59 for SGFN to 31.28.
- VL-SAT improves SGGpoint:
  - Predicate `mA@1/3`: 27.95 / 49.98 -> 38.04 / 60.36.
  - Triplet `mA@50/100`: 45.02 / 56.03 -> 52.51 / 64.31.
- VL-SAT improves SGFN:
  - Predicate `mA@1/3`: 41.89 / 70.82 -> 52.91 / 72.37.
  - Triplet `mA@50/100`: 58.37 / 67.61 -> 63.57 / 72.02.
- Ablations show cumulative gains from CLIP-initialized object classifier, node-level collaboration, edge-level collaboration, and triplet-level CLIP regularization.

## Reproducibility Notes

- Code is available at `https://github.com/wz7in/CVPR2023-VLSAT`.
- Requires 3RScan and 3DSSG-sub annotations.
- Requires generating 2D multi-view images from point clouds and training or using a CLIP adapter checkpoint.
- The released code targets Python 3.8, PyTorch 1.12.1 + CUDA 11.3, PyTorch Geometric, and OpenAI CLIP.

## Evaluation Weaknesses

- The primary benchmark remains closed-set 3DSSG, so open-vocabulary relation quality is not evaluated.
- Metrics measure label/triplet correctness, not explicit geometry consistency.
- Visual-linguistic assistance is latent; the benchmark does not ask whether a predicted relation is physically supported by 3D evidence.
- Qualitative ScanNet evaluation is useful but not a standardized graph benchmark.
- A CAND-001 contribution should not merely improve `mA@k`; it needs a geometry-grounding or violation metric.
