# Replica-Developed Bounded Fusion: Cross-Source Evaluation

Selected configuration: `bounded_raw__a1__t0.6__d0`

| Source | Method | K | Recall | delta Recall | Violation | delta Violation |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| vlsat | semantic_only | 10 | 0.63218 | +0.00000 | 0.00821 | +0.00000 |
| vlsat | semantic_only | 50 | 0.92724 | +0.00000 | 0.02675 | +0.00000 |
| vlsat | semantic_only | 100 | 0.96349 | +0.00000 | 0.04765 | +0.00000 |
| vlsat | family_product | 10 | 0.63293 | +0.00076 | 0.00493 | -0.00328 |
| vlsat | family_product | 50 | 0.92925 | +0.00201 | 0.02040 | -0.00635 |
| vlsat | family_product | 100 | 0.96903 | +0.00554 | 0.03270 | -0.01495 |
| vlsat | rank_average_family | 10 | 0.35725 | -0.27492 | 0.01113 | +0.00292 |
| vlsat | rank_average_family | 50 | 0.81571 | -0.11153 | 0.01883 | -0.00792 |
| vlsat | rank_average_family | 100 | 0.96148 | -0.00201 | 0.02474 | -0.02290 |
| vlsat | bounded_selected | 10 | 0.62034 | -0.01183 | 0.00493 | -0.00328 |
| vlsat | bounded_selected | 50 | 0.91113 | -0.01611 | 0.01704 | -0.00971 |
| vlsat | bounded_selected | 100 | 0.95846 | -0.00504 | 0.02551 | -0.02214 |
| open3dsg | semantic_only | 10 | 0.10020 | +0.00000 | 0.32555 | +0.00000 |
| open3dsg | semantic_only | 50 | 0.40962 | +0.00000 | 0.13864 | +0.00000 |
| open3dsg | semantic_only | 100 | 0.51611 | +0.00000 | 0.12420 | +0.00000 |
| open3dsg | family_product | 10 | 0.19587 | +0.09567 | 0.04489 | -0.28066 |
| open3dsg | family_product | 50 | 0.47080 | +0.06118 | 0.02837 | -0.11027 |
| open3dsg | family_product | 100 | 0.60851 | +0.09240 | 0.03379 | -0.09041 |
| open3dsg | rank_average_family | 10 | 0.18756 | +0.08736 | 0.03175 | -0.29380 |
| open3dsg | rank_average_family | 50 | 0.47482 | +0.06521 | 0.03957 | -0.09907 |
| open3dsg | rank_average_family | 100 | 0.60272 | +0.08661 | 0.05313 | -0.07106 |
| open3dsg | bounded_selected | 10 | 0.16793 | +0.06772 | 0.04398 | -0.28157 |
| open3dsg | bounded_selected | 50 | 0.46853 | +0.05891 | 0.04418 | -0.09447 |
| open3dsg | bounded_selected | 100 | 0.58585 | +0.06974 | 0.05180 | -0.07240 |
| sgfn | semantic_only | 10 | 0.39753 | +0.00000 | 0.03485 | +0.00000 |
| sgfn | semantic_only | 50 | 0.74018 | +0.00000 | 0.03847 | +0.00000 |
| sgfn | semantic_only | 100 | 0.92346 | +0.00000 | 0.06297 | +0.00000 |
| sgfn | family_product | 10 | 0.40609 | +0.00856 | 0.03212 | -0.00274 |
| sgfn | family_product | 50 | 0.77090 | +0.03072 | 0.02566 | -0.01281 |
| sgfn | family_product | 100 | 0.94159 | +0.01813 | 0.03763 | -0.02535 |
| sgfn | rank_average_family | 10 | 0.29154 | -0.10599 | 0.02208 | -0.01277 |
| sgfn | rank_average_family | 50 | 0.73943 | -0.00076 | 0.02026 | -0.01821 |
| sgfn | rank_average_family | 100 | 0.94814 | +0.02467 | 0.02706 | -0.03591 |
| sgfn | bounded_selected | 10 | 0.39048 | -0.00705 | 0.03230 | -0.00255 |
| sgfn | bounded_selected | 50 | 0.76838 | +0.02820 | 0.02088 | -0.01759 |
| sgfn | bounded_selected | 100 | 0.93454 | +0.01108 | 0.02697 | -0.03600 |
