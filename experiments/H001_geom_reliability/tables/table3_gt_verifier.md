# Table 3 GT-Based Verifier Evaluation

| metric | rows | value | note |
| --- | --- | --- | --- |
| GT-positive nonviolated rate | 2545 | 0.9972 | valid GT relations should not be flagged as violated |
| GT-derived negative nonsatisfied rate | 2545 | 0.9694 | counterfactual negatives should not be satisfied |
| p_geom_valid AUROC | 5090 | 0.9779 | probability discriminates GT positives from counterfactual negatives |
| p_geom_valid AUPRC | 5090 | 0.9737 | precision-recall discrimination |
| p_geom_valid Brier | 5090 | 0.0538 | calibration error on GT/counterfactual verifier evaluation |
