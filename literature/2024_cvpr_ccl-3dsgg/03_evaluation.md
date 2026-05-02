# Evaluation

## Dataset / Benchmark

- 3DSSG: main quantitative benchmark.
- ScanNet: qualitative evaluation because it does not provide 3DSG ground truth labels.

## Splits

- 3DSSG training set: 3582 scenes.
- 3DSSG testing set: 548 scenes.
- Open-vocabulary setup: train with 70% base object/predicate classes and evaluate on base + 30% novel classes.
- Zero-shot setup: evaluate only the 30% novel classes.

## Metrics

- SGCLS and PREDCLS.
- R@20 / R@50 / R@100.
- mR@20 / mR@50 / mR@100.
- Mean of R and mR.
- mA@k for head/body/tail predicate analysis.
- Open-vocabulary and zero-shot R@50 / R@100.

## Baselines

- SGPN
- SGFN
- EdgeGCN
- KISGP
- Liu et al.
- Chen et al.
- Feng et al.
- VL-SAT

## Main Results

Close-set 3DSSG:

- CCL-3DSGG reports SGCLS R@20/50/100 = 37.6/40.3/45.7 and mR@20/50/100 = 35.0/37.3/40.6.
- PREDCLS R@20/50/100 = 73.6/80.5/82.9 and mR@20/50/100 = 59.1/66.7/69.1.
- Mean R/mR = 60.1/51.3.

Open-vocabulary and zero-shot:

- Open-vocabulary: CCL-3DSGG reports SGCLS R@50/100 = 37.1/42.3 and PREDCLS R@50/100 = 64.8/71.2.
- Zero-shot: CCL-3DSGG reports SGCLS R@50/100 = 35.5/40.6 and PREDCLS R@50/100 = 49.1/65.7.
- The paper reports strong gains over VL-SAT in zero-shot settings.

## Reproducibility Notes

- Public code was not found during this pass.
- The method assumes class-agnostic instance segmentation and available image/text pairs.
- It trains with Adam, batch size 8, 100 epochs, and reports RTX 2080Ti implementation.

## Evaluation Weaknesses

- The open-vocabulary task is still framed using held-out classes from 3DSSG, not arbitrary relation text in the wild.
- No direct geometry consistency or relation grounding metric is reported.
- ScanNet lacks ground-truth 3D scene graph labels, so cross-dataset evaluation is qualitative.

