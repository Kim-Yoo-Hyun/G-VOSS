# H001 Fresh-Source Factor-Isolation Evaluation

Status: `factor_isolation_fresh_source_ready`

All factor models were fit on calibration train only; dev and fresh-source results selected nothing.

## Global K=100

| condition | Recall | delta Recall | V | delta V |
| --- | ---: | ---: | ---: | ---: |
| semantic_only | 0.951410 | 0.000000 | 0.062153 | 0.000000 |
| product_M_T | 0.949648 | -0.001762 | 0.064927 | 0.002774 |
| product_M_G | 0.957704 | 0.006294 | 0.059617 | -0.002536 |
| product_M_add | 0.955942 | 0.004532 | 0.062682 | 0.000529 |
| product_M_int | 0.959215 | 0.007805 | 0.050000 | -0.012153 |
| product_M_existing | 0.958711 | 0.007301 | 0.034690 | -0.027464 |
| rank_average_M_T | 0.554129 | -0.397281 | 0.130292 | 0.068139 |
| rank_average_M_G | 0.917925 | -0.033484 | 0.081095 | 0.018942 |
| rank_average_M_add | 0.917925 | -0.033484 | 0.098850 | 0.036697 |
| rank_average_M_int | 0.937815 | -0.013595 | 0.044708 | -0.017445 |
| rank_average_M_existing | 0.949899 | -0.001511 | 0.021642 | -0.040511 |

Family-wise marginal and simultaneous CIs and frozen metamorphic controls are in `summary.json`.
