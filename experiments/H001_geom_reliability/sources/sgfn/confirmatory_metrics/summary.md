# H001 Reviewer-Extension Metrics

Status: `ready_label_free_verifier_diagnostic`
Bootstrap: `1000` paired subgraph resamples

`rank_average_fusion` and `reciprocal_rank_fusion` are fixed, parameter-free, scale-robust late-fusion baselines. They are comparisons, not newly selected main scores.

## Overall global in-scope ranking

| source | condition | K | R@K | R 95% CI | V@K | V 95% CI | dR vs semantic | dV vs semantic |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| sgfn_official_full_l160_confirmatory | semantic_only | 5 | 0.3117 | [0.293922641688608, 0.3325432702238254] | 0.0237 | [0.017518248175182483, 0.029936131386861305] | n/a | n/a |
| sgfn_official_full_l160_confirmatory | semantic_only | 10 | 0.3975 | [0.3761547038561798, 0.42146058425223454] | 0.0349 | [0.02937956204379562, 0.041240875912408756] | n/a | n/a |
| sgfn_official_full_l160_confirmatory | semantic_only | 20 | 0.4912 | [0.4681143162632005, 0.5164259286722527] | 0.0322 | [0.02800866788321168, 0.036409671532846716] | n/a | n/a |
| sgfn_official_full_l160_confirmatory | semantic_only | 50 | 0.7402 | [0.7138187434328072, 0.7646187855698228] | 0.0385 | [0.0352536496350365, 0.04168248175182481] | n/a | n/a |
| sgfn_official_full_l160_confirmatory | semantic_only | 100 | 0.9235 | [0.903654339375205, 0.9420524163970221] | 0.0630 | [0.059725821167883206, 0.0663330291970803] | n/a | n/a |
| sgfn_official_full_l160_confirmatory | family_conditional_risk | 5 | 0.3094 | [0.29116203440145216, 0.3305701358401621] | 0.0252 | [0.01824817518248175, 0.032116788321167884] | -0.0023 | 0.0015 |
| sgfn_official_full_l160_confirmatory | family_conditional_risk | 10 | 0.4058 | [0.3852964065380837, 0.4297642326325712] | 0.0318 | [0.02645985401459854, 0.037778284671532845] | 0.0083 | -0.0031 |
| sgfn_official_full_l160_confirmatory | family_conditional_risk | 20 | 0.5116 | [0.4870646695034163, 0.5361670388662796] | 0.0273 | [0.023631386861313868, 0.031478102189781025] | 0.0204 | -0.0049 |
| sgfn_official_full_l160_confirmatory | family_conditional_risk | 50 | 0.7709 | [0.7445804606062066, 0.7958134534505407] | 0.0258 | [0.02324726277372263, 0.02832116788321168] | 0.0307 | -0.0127 |
| sgfn_official_full_l160_confirmatory | family_conditional_risk | 100 | 0.9416 | [0.9226898475948767, 0.9587731548090415] | 0.0381 | [0.0356021897810219, 0.04069343065693431] | 0.0181 | -0.0249 |
| sgfn_official_full_l160_confirmatory | pooled_calibration | 5 | 0.3094 | [0.29208374066514287, 0.32970599446702803] | 0.0241 | [0.017518248175182483, 0.03102189781021898] | -0.0023 | 0.0004 |
| sgfn_official_full_l160_confirmatory | pooled_calibration | 10 | 0.4076 | [0.38715266469885, 0.430192289708197] | 0.0314 | [0.026094890510948904, 0.037413321167883214] | 0.0101 | -0.0035 |
| sgfn_official_full_l160_confirmatory | pooled_calibration | 20 | 0.5126 | [0.4892685132203599, 0.5366785472337352] | 0.0275 | [0.023811587591240878, 0.031478102189781025] | 0.0214 | -0.0047 |
| sgfn_official_full_l160_confirmatory | pooled_calibration | 50 | 0.7709 | [0.7452774298764632, 0.7948577364875146] | 0.0293 | [0.026422445255474453, 0.03189872262773723] | 0.0307 | -0.0092 |
| sgfn_official_full_l160_confirmatory | pooled_calibration | 100 | 0.9396 | [0.920750502802763, 0.9566996075543691] | 0.0488 | [0.04607481751824818, 0.05180748175182481] | 0.0161 | -0.0142 |
| sgfn_official_full_l160_confirmatory | geometry_only_family | 5 | 0.0222 | [0.01709945454346044, 0.02792215675301375] | 0.0066 | [0.00291970802919708, 0.010948905109489052] | -0.2895 | -0.0172 |
| sgfn_official_full_l160_confirmatory | geometry_only_family | 10 | 0.0531 | [0.04506900577787996, 0.06157221557471124] | 0.0077 | [0.004562043795620438, 0.010948905109489052] | -0.3444 | -0.0272 |
| sgfn_official_full_l160_confirmatory | geometry_only_family | 20 | 0.1206 | [0.10929205718927024, 0.1317140633842671] | 0.0078 | [0.005563412408759125, 0.010130018248175181] | -0.3706 | -0.0244 |
| sgfn_official_full_l160_confirmatory | geometry_only_family | 50 | 0.3593 | [0.3406112792241524, 0.37846952824290003] | 0.0176 | [0.015218065693430656, 0.02018339416058394] | -0.3809 | -0.0209 |
| sgfn_official_full_l160_confirmatory | geometry_only_family | 100 | 0.6463 | [0.625026649573288, 0.6688723040109534] | 0.0224 | [0.020145529197080292, 0.024800638686131384] | -0.2772 | -0.0406 |
| sgfn_official_full_l160_confirmatory | rank_average_fusion | 5 | 0.1765 | [0.162144778345904, 0.1910393205395752] | 0.0245 | [0.017518248175182483, 0.032481751824817516] | -0.1352 | 0.0007 |
| sgfn_official_full_l160_confirmatory | rank_average_fusion | 10 | 0.2918 | [0.2730201048315042, 0.3102336932988953] | 0.0232 | [0.01824361313868613, 0.029014598540145986] | -0.1057 | -0.0117 |
| sgfn_official_full_l160_confirmatory | rank_average_fusion | 20 | 0.4539 | [0.4320772188410826, 0.47655520961908715] | 0.0219 | [0.018521897810218978, 0.025912408759124088] | -0.0373 | -0.0103 |
| sgfn_official_full_l160_confirmatory | rank_average_fusion | 50 | 0.7243 | [0.7032661553595888, 0.7462026346832349] | 0.0218 | [0.01941514598540146, 0.02445346715328467] | -0.0159 | -0.0167 |
| sgfn_official_full_l160_confirmatory | rank_average_fusion | 100 | 0.9476 | [0.9311764576074727, 0.9618824295991383] | 0.0277 | [0.025491788321167885, 0.030146897810218978] | 0.0242 | -0.0353 |
| sgfn_official_full_l160_confirmatory | reciprocal_rank_fusion | 5 | 0.1986 | [0.1832138722245681, 0.21434319743744856] | 0.0208 | [0.01458941605839416, 0.02846715328467153] | -0.1130 | -0.0029 |
| sgfn_official_full_l160_confirmatory | reciprocal_rank_fusion | 10 | 0.3283 | [0.3093787543278191, 0.34775673519066247] | 0.0228 | [0.017878649635036496, 0.028284671532846715] | -0.0692 | -0.0120 |
| sgfn_official_full_l160_confirmatory | reciprocal_rank_fusion | 20 | 0.5058 | [0.4824312886063371, 0.5300945065078964] | 0.0224 | [0.01897810218978102, 0.02636861313868613] | 0.0146 | -0.0098 |
| sgfn_official_full_l160_confirmatory | reciprocal_rank_fusion | 50 | 0.7341 | [0.710465320316904, 0.7569384301742156] | 0.0211 | [0.018795620437956205, 0.023541058394160583] | -0.0060 | -0.0173 |
| sgfn_official_full_l160_confirmatory | reciprocal_rank_fusion | 100 | 0.9192 | [0.9035958260052693, 0.9344196107581589] | 0.0284 | [0.026093521897810217, 0.030821167883211677] | -0.0043 | -0.0346 |

## Family-wise outputs

`family_metrics.csv` contains within-family top-K recall/violation with paired CIs. `global_topk_family_slice.csv` reports each family's contribution inside the actual global top-K list.

The violation target in this label-free table is still the frozen geometry verifier. The independent human audit evaluator is the non-circular primary check once labels are available.
