# Prediction Metrics

Created at: `2026-06-04`
Status: `ready`
Families: `proximity, relative_vertical, support_contact`
K values: `50, 100`

## Semantic Only

- R@50: `0.9272406847935549` (3683/3972)
- R@100: `0.9634944612286002` (3827/3972)
- Violation@50: `0.026751824817518248` (733/27400)
- Violation@100: `0.04764598540145985` (2611/54800)

## rule_verified_obb_only

- Policy: `filter_safe`
- Variant: `obb_only`
- Kept: `178930` / `957008`
- R@50: `0.9277442094662638` (3685/3972)
- R@100: `0.9655085599194361` (3835/3972)
- Violation@50: `0.0` (0/27400)
- Violation@100: `0.0` (0/54782)

## rule_verified_point_subtype

- Policy: `filter_safe`
- Variant: `point_subtype`
- Kept: `189592` / `957008`
- R@50: `0.925730110775428` (3677/3972)
- R@100: `0.9627391742195368` (3824/3972)
- Violation@50: `0.0` (0/27400)
- Violation@100: `0.0` (0/54781)

## rule_verified_point_subtype_no_soft_support

- Policy: `filter_safe`
- Variant: `point_subtype_no_soft_support`
- Kept: `184902` / `957008`
- R@50: `0.9254783484390735` (3676/3972)
- R@100: `0.9627391742195368` (3824/3972)
- Violation@50: `0.0` (0/27400)
- Violation@100: `0.0` (0/54784)

## Probabilistic Recalibrated

- Score formula: `semantic_ranking_score*p_geom_valid`
- Scored: `220848` / `220848` in-scope predictions
- R@50: `0.9305135951661632` (3696/3972)
- R@100: `0.9687814702920443` (3848/3972)
- Violation@50: `0.02291970802919708` (628/27400)
- Violation@100: `0.04043795620437956` (2216/54800)

## control_distance_only

- Score formula: `1/(1+distance_3d)`
- Scored: `220848` / `220848` in-scope predictions
- R@50: `0.37462235649546827` (1488/3972)
- R@100: `0.5553877139979859` (2206/3972)
- Violation@50: `0.07237226277372263` (1983/27400)
- Violation@100: `0.09808394160583941` (5375/54800)

## control_family_specific_p_geom_valid

- Score formula: `semantic_ranking_score*p_geom_valid_family_specific`
- Scored: `220848` / `220848` in-scope predictions
- R@50: `0.9287512588116817` (3689/3972)
- R@100: `0.9682779456193353` (3846/3972)
- Violation@50: `0.020620437956204378` (565/27400)
- Violation@100: `0.0333029197080292` (1825/54800)

## control_p_geom_valid_only

- Score formula: `p_geom_valid`
- Scored: `220848` / `220848` in-scope predictions
- R@50: `0.2109768378650554` (838/3972)
- R@100: `0.5183786505538771` (2059/3972)
- Violation@50: `0.06605839416058394` (1810/27400)
- Violation@100: `0.0710948905109489` (3896/54800)

## control_shuffled_geometry

- Score formula: `semantic_ranking_score*shuffled_family_p_geom_valid`
- Scored: `220848` / `220848` in-scope predictions
- R@50: `0.8889728096676737` (3531/3972)
- R@100: `0.9493957703927492` (3771/3972)
- Violation@50: `0.029452554744525548` (807/27400)
- Violation@100: `0.05883211678832117` (3224/54800)

## control_wrong_pair_geometry

- Score formula: `semantic_ranking_score*wrong_pair_p_geom_valid`
- Scored: `220848` / `220848` in-scope predictions
- R@50: `0.8914904330312186` (3541/3972)
- R@100: `0.952920443101712` (3785/3972)
- Violation@50: `0.03204379562043796` (878/27400)
- Violation@100: `0.06009124087591241` (3293/54800)
