# Table 2 Nontriviality Controls

| condition | purpose | r50 | r100 | violation50 | violation100 | delta_r50_vs_main | delta_violation50_vs_main |
| --- | --- | --- | --- | --- | --- | --- | --- |
| control_p_geom_valid_only | geometry-only ranking control | 0.2028 | 0.5049 | 0.0642 | 0.0701 | -0.7615 | +0.0409 |
| control_distance_only | simple distance heuristic control | 0.3835 | 0.5642 | 0.0731 | 0.0993 | -0.5807 | +0.0498 |
| control_shuffled_geometry | breaks geometry identity while preserving distribution | 0.9297 | 0.9788 | 0.0289 | 0.0559 | -0.0346 | +0.0056 |
| control_wrong_pair_geometry | tests object-pair identity | 0.9242 | 0.9788 | 0.0302 | 0.0581 | -0.0401 | +0.0069 |
| control_family_specific_p_geom_valid | stricter family-specific calibration | 0.9619 | 0.9914 | 0.0204 | 0.0310 | -0.0024 | -0.0030 |
