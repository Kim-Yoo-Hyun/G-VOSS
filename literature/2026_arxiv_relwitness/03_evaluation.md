# Evaluation

## Dataset / Benchmark

Full-PDF skim facts:

- `3DSSG/3RScan`: closed-vocabulary benchmark and missing-label setting where annotated relations are observed positives and other candidate phrases are unlabeled.
- `OV-3DSSG`: an open-vocabulary split that reserves rare and compositional relation phrases as unseen.
- `ScanNet-OV`: a ScanNet-derived RGB-D open-vocabulary split for multi-view witness testing.
- Audit subset: 2,400 candidate relations across methods, including 1,200 unannotated predictions, balanced by relation family and confidence range.

## Splits

The PDF specifies intended split types but does not provide enough reproduced implementation detail to treat them as executable benchmark splits in this pass.

Recorded setup:

- standard 3DSSG/3RScan closed-vocabulary relation prediction;
- missing-label setting over 3DSSG/3RScan;
- OV-3DSSG rare/compositional unseen phrase split;
- ScanNet-OV object instances from ground-truth or detector masks depending on protocol;
- audit pool generated once from all methods, then randomized for annotators.

The paper says relation pool, witness thresholds, and audit protocol are fixed before main comparisons, and thresholds are tuned on validation witness precision rather than test recall.

## Metrics

Metrics reported in the design:

- 3DSSG-style relation prediction `R@50`, `R@100`, `mR@50`, `mR@100` for Predicate Classification and Scene Graph Generation;
- open-vocabulary seen/unseen raw and mean recall;
- harmonic mean for seen/unseen behavior;
- Verified Missing Recall;
- Witness Precision;
- Multi-View Witness Agreement;
- Hallucination Rate;
- Redundancy Rate;
- witness memory precision/diversity;
- witness type parser quality;
- cross-dataset transfer;
- object source robustness;
- efficiency.

H001-specific comparison still missing:

- predicate/triplet `R@K`;
- `Violation@K`;
- recall retention;
- calibration metrics;
- denominator audit;
- family-level metrics for support/contact, proximity, relative vertical/orientation, and containment.

## Baselines

Full-PDF skim baseline list:

- closed-set 3D SGG baselines;
- SceneGraphFusion-style RGB-D relation fusion;
- Open3DSG;
- ConceptGraphs-style relation querying;
- OpenFunGraph;
- FROSS;
- Text Completion;
- Object-Prior Completion;
- RGB-only, depth-only, and geometry-only variants.

## Main Results

Do not use as reproduced evidence.

The PDF states that the numerical values are simulated planning results for manuscript development only and should be read as plausible experiment templates, not reproduced claims. It also labels multiple tables as simulated manuscript-planning numbers.

For H001, this means RelWitness should be cited as a very recent related direction / novelty-threat watch item, not as a stable quantitative baseline.

## Reproducibility Notes

- No official code was found in a targeted web search on 2026-05-23.
- No local PDF is stored in the repo; `/tmp/relwitness_2605.20823.pdf` was used for the full-PDF skim.
- Dataset scripts, exact thresholds, audit label files, and reproduced measurements are not available from the checked sources.

## Evaluation Weaknesses

Inference:

- Because the reported values are simulated planning values, the paper cannot yet be used to invalidate H001's reproduced Docker tables.
- Because RelWitness is a new generator under incomplete supervision, it is adjacent but not identical to H001's reliability-layer framing over existing relation-source outputs.
- Because RelWitness also uses family-specific visual-geometric checks and validation-calibrated thresholds, H001 must not describe itself as the first geometry-calibrated relation verifier.
- Reviewers may ask both papers the same hard questions: why these physical checks, how thresholds/calibration are chosen, what recall tradeoff is induced, and how robust the method is across source models and object-instance quality.
