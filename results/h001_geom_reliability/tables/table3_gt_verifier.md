# Table 3 GT-Based Verifier Evaluation

| metric | rows | value | note |
| --- | --- | --- | --- |
| GT-positive nonviolated rate | 3972 | 0.9965 | valid full-validation GT relations should not be flagged as violated |
| GT-derived negative nonsatisfied rate | 3972 | 0.9673 | counterfactual negatives should not be satisfied |
| p_geom_valid AUROC | 7944 | 0.9772 | probability discriminates full-validation GT positives from counterfactual negatives |
| p_geom_valid AUPRC | 7944 | 0.9729 | precision-recall discrimination |
| p_geom_valid Brier | 7944 | 0.0543 | calibration error on GT/counterfactual verifier evaluation |
