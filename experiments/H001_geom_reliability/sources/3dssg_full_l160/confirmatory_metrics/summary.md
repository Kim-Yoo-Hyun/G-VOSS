# H001 Reviewer-Extension Metrics

Status: `ready_label_free_verifier_diagnostic`
Bootstrap: `1000` paired subgraph resamples

`rank_average_fusion` and `reciprocal_rank_fusion` are fixed, parameter-free, scale-robust late-fusion baselines. They are comparisons, not newly selected main scores.

## Overall global in-scope ranking

| source | condition | K | R@K | R 95% CI | V@K | V 95% CI | dR vs semantic | dV vs semantic |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3dssg_official_full_l160_confirmatory | semantic_only | 5 | 0.3270 | [0.30701570852033955, 0.347397264577748] | 0.0204 | [0.015328467153284672, 0.02592153284671532] | n/a | n/a |
| 3dssg_official_full_l160_confirmatory | semantic_only | 10 | 0.4746 | [0.45097162542598906, 0.4987305260270122] | 0.0234 | [0.01916058394160584, 0.02828923357664233] | n/a | n/a |
| 3dssg_official_full_l160_confirmatory | semantic_only | 20 | 0.6720 | [0.6446091580227234, 0.6997400746230042] | 0.0241 | [0.020985401459854013, 0.027463503649635037] | n/a | n/a |
| 3dssg_official_full_l160_confirmatory | semantic_only | 50 | 0.8726 | [0.8494049051143834, 0.8972458421112355] | 0.0370 | [0.033940693430656935, 0.04018248175182482] | n/a | n/a |
| 3dssg_official_full_l160_confirmatory | semantic_only | 100 | 0.9514 | [0.9366856870654009, 0.9640951953382939] | 0.0622 | [0.05873950729927007, 0.06574863138686132] | n/a | n/a |
| 3dssg_official_full_l160_confirmatory | family_conditional_risk | 5 | 0.3283 | [0.3088930672084018, 0.347515913682165] | 0.0179 | [0.013138686131386862, 0.02335766423357664] | 0.0013 | -0.0026 |
| 3dssg_official_full_l160_confirmatory | family_conditional_risk | 10 | 0.4794 | [0.4560036980553179, 0.5030509087064867] | 0.0204 | [0.016423357664233577, 0.025] | 0.0048 | -0.0029 |
| 3dssg_official_full_l160_confirmatory | family_conditional_risk | 20 | 0.6813 | [0.6539697022539106, 0.7102242384461102] | 0.0178 | [0.015323905109489052, 0.0207139598540146] | 0.0093 | -0.0063 |
| 3dssg_official_full_l160_confirmatory | family_conditional_risk | 50 | 0.8799 | [0.8580008623110799, 0.9027247922364823] | 0.0208 | [0.018759124087591242, 0.023029197080291972] | 0.0073 | -0.0162 |
| 3dssg_official_full_l160_confirmatory | family_conditional_risk | 100 | 0.9587 | [0.9462569490971245, 0.9694613572845966] | 0.0347 | [0.03228102189781022, 0.037117244525547446] | 0.0073 | -0.0275 |
| 3dssg_official_full_l160_confirmatory | pooled_calibration | 5 | 0.3285 | [0.30921669257298806, 0.34895819661655597] | 0.0186 | [0.013138686131386862, 0.02408759124087591] | 0.0015 | -0.0018 |
| 3dssg_official_full_l160_confirmatory | pooled_calibration | 10 | 0.4849 | [0.4616212984091849, 0.5094230947173994] | 0.0203 | [0.016418795620437958, 0.024817518248175182] | 0.0103 | -0.0031 |
| 3dssg_official_full_l160_confirmatory | pooled_calibration | 20 | 0.6845 | [0.6579386633061187, 0.7123671746023428] | 0.0194 | [0.0166970802919708, 0.02271897810218978] | 0.0126 | -0.0047 |
| 3dssg_official_full_l160_confirmatory | pooled_calibration | 50 | 0.8832 | [0.8616554701291392, 0.9052695857383357] | 0.0276 | [0.025291970802919707, 0.03018248175182482] | 0.0106 | -0.0094 |
| 3dssg_official_full_l160_confirmatory | pooled_calibration | 100 | 0.9592 | [0.9458388260662106, 0.9708263929770204] | 0.0500 | [0.04717107664233577, 0.05317563868613139] | 0.0078 | -0.0122 |
| 3dssg_official_full_l160_confirmatory | geometry_only_family | 5 | 0.0222 | [0.01709945454346044, 0.02792215675301375] | 0.0066 | [0.00291970802919708, 0.010948905109489052] | -0.3049 | -0.0139 |
| 3dssg_official_full_l160_confirmatory | geometry_only_family | 10 | 0.0531 | [0.04506900577787996, 0.06157221557471124] | 0.0077 | [0.004562043795620438, 0.010948905109489052] | -0.4215 | -0.0157 |
| 3dssg_official_full_l160_confirmatory | geometry_only_family | 20 | 0.1206 | [0.10929205718927024, 0.1317140633842671] | 0.0078 | [0.005563412408759125, 0.010130018248175181] | -0.5514 | -0.0162 |
| 3dssg_official_full_l160_confirmatory | geometry_only_family | 50 | 0.3593 | [0.3406112792241524, 0.37846952824290003] | 0.0176 | [0.015218065693430656, 0.02018339416058394] | -0.5133 | -0.0194 |
| 3dssg_official_full_l160_confirmatory | geometry_only_family | 100 | 0.6463 | [0.625026649573288, 0.6688723040109534] | 0.0224 | [0.020145529197080292, 0.024800638686131384] | -0.3051 | -0.0398 |
| 3dssg_official_full_l160_confirmatory | rank_average_fusion | 5 | 0.1893 | [0.17612744621763535, 0.2033435380288868] | 0.0120 | [0.007664233576642336, 0.017153284671532848] | -0.1377 | -0.0084 |
| 3dssg_official_full_l160_confirmatory | rank_average_fusion | 10 | 0.3124 | [0.29592435329302547, 0.3299543557563989] | 0.0117 | [0.008394160583941606, 0.01551094890510949] | -0.1621 | -0.0117 |
| 3dssg_official_full_l160_confirmatory | rank_average_fusion | 20 | 0.4864 | [0.46512131690635994, 0.5077297269355575] | 0.0150 | [0.012135036496350365, 0.018065693430656934] | -0.1855 | -0.0091 |
| 3dssg_official_full_l160_confirmatory | rank_average_fusion | 50 | 0.7550 | [0.7347516644605567, 0.7732896811584583] | 0.0161 | [0.014051094890510948, 0.018394160583941607] | -0.1176 | -0.0209 |
| 3dssg_official_full_l160_confirmatory | rank_average_fusion | 100 | 0.9499 | [0.9394239904988124, 0.9594130064327617] | 0.0216 | [0.01959808394160584, 0.023851733576642335] | -0.0015 | -0.0405 |
| 3dssg_official_full_l160_confirmatory | reciprocal_rank_fusion | 5 | 0.2007 | [0.1864890990667364, 0.21528297383433875] | 0.0128 | [0.008394160583941606, 0.01824817518248175] | -0.1264 | -0.0077 |
| 3dssg_official_full_l160_confirmatory | reciprocal_rank_fusion | 10 | 0.3346 | [0.3151146820143099, 0.3544877843840186] | 0.0133 | [0.009854014598540146, 0.017157846715328464] | -0.1400 | -0.0100 |
| 3dssg_official_full_l160_confirmatory | reciprocal_rank_fusion | 20 | 0.5375 | [0.5155668755396562, 0.560755387018798] | 0.0133 | [0.010764142335766424, 0.01615191605839416] | -0.1344 | -0.0108 |
| 3dssg_official_full_l160_confirmatory | reciprocal_rank_fusion | 50 | 0.8366 | [0.8148198446136554, 0.8590131821975018] | 0.0161 | [0.014121350364963503, 0.01824817518248175] | -0.0360 | -0.0209 |
| 3dssg_official_full_l160_confirmatory | reciprocal_rank_fusion | 100 | 0.9476 | [0.9350293550025394, 0.9584909961506386] | 0.0267 | [0.024434306569343065, 0.02914324817518248] | -0.0038 | -0.0355 |

## Family-wise outputs

`family_metrics.csv` contains within-family top-K recall/violation with paired CIs. `global_topk_family_slice.csv` reports each family's contribution inside the actual global top-K list.

The violation target in this label-free table is still the frozen geometry verifier. The independent human audit evaluator is the non-circular primary check once labels are available.
