# Insights

## Full-PDF Pass

- Date checked: 2026-05-23.
- Source: arXiv v2 PDF, temporary local path `/tmp/relwitness_2605.20823.pdf`.
- Verdict: RelWitness is a stronger novelty threat than the abstract-only pass suggested because it includes a calibrated witness quality `Q`, validation-calibrated thresholds, witness-guided learning, and witness-consistent decoding. It still does not collapse H001 because its primary contribution is missing-supervision learning for an open-vocabulary generator, while H001 is a reproduced calibrated reliability evaluation/re-ranking framework over existing relation-source outputs.

## Facts

- Date checked: 2026-05-23.
- The arXiv page lists the title as `RelWitness: Open-Vocabulary 3D Scene Graph Generation with Visual-Geometric Relation Witnesses`.
- The paper is an arXiv preprint submitted on 2026-05-20 and revised on 2026-05-21.
- The abstract introduces relation witnesses as visual-geometric cues for relation observability in open-vocabulary 3D scene graph generation.
- The abstract says support, containment, proximity, orientation, and multi-view stability are tied to concrete witness cues.
- The abstract says the verifier assigns unannotated relation candidates to verified missing positives, reliable negatives, or uncertain unlabeled cases.
- The PDF states that numerical results are simulated manuscript-planning values and should be replaced by reproduced measurements before submission.
- The method includes a calibrated witness quality `Q`, thresholded verified missing positives / reliable negatives / uncertain candidates, and witness-consistent decoding.
- The method uses a three-stage training schedule: supervised warm-up, conservative witness bootstrapping, and joint witness-guided positive-unlabeled learning.
- The audit protocol reports Verified Missing Recall, Witness Precision, Multi-View Witness Agreement, Hallucination Rate, and Redundancy Rate.

## Paper Claims

- Open-vocabulary 3DSSG should address incomplete relation supervision, not only vocabulary expansion.
- Visual-geometric witnesses can improve relation supervision reliability.
- Witness-guided learning and decoding are intended to reduce hallucination and improve unseen-relation behavior.

## Inferences

- RelWitness raises the novelty bar for H001 because "geometry witness for 3D relation validity" and "calibrated witness quality" are no longer safe standalone novelty phrases.
- H001 remains distinguishable if it is framed as a calibrated geometry-consistency evaluation/re-ranking framework over existing relation-source outputs rather than a new witness-supervised open-vocabulary generator.
- H001's strongest defense is its reproduced, denominator-locked evidence: `VL-SAT` plus Open3DSG source-adapter metrics, recall/violation operating points, controls, GT-based verifier evaluation, failure rows, and caveat transparency.

## H001 Difference Matrix

| Dimension | RelWitness | H001 | Consequence for H001 |
| --- | --- | --- | --- |
| Primary problem | Open-vocabulary 3DSSG under incomplete relation supervision | Reliability/calibration of existing 3DSSG relation-source outputs | H001 should not claim missing-supervision learning; it should claim source-output reliability evaluation/re-ranking. |
| Main unit | Relation witness record for candidate pseudo-supervision | Identity-preserved prediction row joined to geometry evidence and GT denominator | H001's row contract and denominator audit remain a distinct contribution. |
| Method role | New generator/training framework | Post-source evaluation and re-ranking framework | Avoid presenting H001 as a generator. Emphasize adapter protocol over `VL-SAT` and Open3DSG. |
| Geometry signal | RGB/depth/3D/multi-view/role/null witness record | OBB/point-local/contact/distance/vertical evidence for fixed H001 families | RelWitness has broader witness modalities; H001 has stronger reproduced metric discipline in a narrower scope. |
| Calibration | Calibrated witness quality `Q` and family-dependent thresholds | Frozen `p_geom_valid`, rule variants, family-specific calibration, recall/violation operating points | H001 cannot claim "first calibrated geometry verifier"; it can claim calibrated reliability evaluation with explicit tradeoff metrics. |
| Learning | Positive-unlabeled objective with verified missing positives/reliable negatives/uncertain memory | No base predictor retraining; re-ranks or filters existing predictions | This is the cleanest method distinction. |
| Inference | Witness-consistent decoding using classifier confidence plus witness quality | Semantic score plus calibrated geometry validity under fixed operating points | Partial overlap; H001 must stress source-agnostic evaluation and controls. |
| Metrics | R@K/mR@K, unseen recall, witness precision, hallucination, redundancy, multi-view agreement, transfer, robustness | R@K plus `Violation@K`, recall retention, controls, GT verifier AUROC/AUPRC, audit precision | H001's `Violation@K` and controls are still differentiating. |
| Evidence maturity | All numerical values are simulated planning values in v2 | Docker-reproduced `VL-SAT` and Open3DSG tables exist | H001 has stronger current empirical footing. |
| Baselines | Includes Open3DSG, ConceptGraphs-style querying, OpenFunGraph, FROSS, completion baselines, variants | Uses reproduced `VL-SAT` and Docker-reproduced Open3DSG through the same H001 metric contract | H001 baseline count is narrower, but its comparison contract is cleaner. |
| Controls | Component ablations and threshold/parser/candidate sensitivity | Geometry-only, distance-only, shuffled-geometry, wrong-pair geometry, family-specific controls | H001 keeps stronger nontriviality controls. |
| Direct threat | Makes relation witnesses and calibrated witness quality prior-art-adjacent | Claims calibrated geometry-consistency evaluation/re-ranking, not witness invention | Related Work must cite RelWitness and define the distinction early. |

## Paper-Claim Decision

Recommended H001 wording after full-PDF pass:

> We study calibrated geometry-consistency evaluation and re-ranking for existing 3D scene graph relation predictions, measuring the recall/violation tradeoff under identity-preserving geometry joins across reproduced relation sources.

Do not use:

- `relation witness` as H001's main method name;
- `first visual-geometric relation verifier`;
- `first open-vocabulary 3DSSG reliability method`;
- `geometry evidence is novel`;
- `calibrated witness quality is novel`.

Safe distinction:

- RelWitness asks which unannotated open-vocabulary relations are physically observable enough to become training supervision.
- H001 asks whether already-produced relation rows are geometrically reliable, and how calibrated re-ranking changes recall and violation rates under fixed denominators.

## Connection to Field Trends

RelWitness strengthens a trend already visible in Open3DSG, CCL-3DSGG, FROSS, OpenFunGraph, Octree-Graph, and ZING-3D:

- 3D scene graph work is moving from fixed-label relation prediction toward open-vocabulary and VLM-mediated relation generation.
- The next bottleneck is not just relation vocabulary size, but whether relation edges are grounded, inspectable, and reliable.
- Relation-level visual-geometric evidence is becoming a central research object.

## Possible Contribution Angles

For H001, the contribution should be stated as:

> A calibrated geometry-consistency evaluation and re-ranking framework for 3D scene graph relation-source outputs, with identity-preserving geometry joins and recall/violation operating points.

Avoid these contribution phrasings:

- "We introduce visual-geometric relation witnesses."
- "We add geometry evidence to open-vocabulary relations."
- "We verify 3D scene graph relations with geometry."
- "We solve open-vocabulary 3DSSG reliability."

Defensible distinction:

- RelWitness: open-vocabulary 3DSG generation under incomplete relation supervision using witness-guided learning and decoding.
- H001: source-agnostic reliability layer and evaluation protocol over existing relation predictions, with calibrated `p_geom_valid`, re-ranking variants, controls, cross-source metrics, and failure analysis.

## What Would Change This Assessment

This assessment becomes stricter if a future RelWitness version adds:

- reproduced quantitative results rather than simulated planning values;
- arbitrary-source prediction-row adapters;
- H001-style `Violation@K` / recall-retention operating points;
- wrong-pair/shuffled-geometry controls;
- `VL-SAT` / Open3DSG source-transfer evidence under a shared geometry-join contract.

If those are present, H001 must cite RelWitness as the nearest concurrent work and emphasize experimental rigor/reproduction scope, denominator discipline, and the reliability-layer contract rather than method novelty alone.
