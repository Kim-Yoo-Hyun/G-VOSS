# Prediction Metrics

Created at: `2026-06-04`
Status: `ready`
Families: `proximity, relative_vertical, support_contact`
K values: `50, 100`

## Semantic Only

- R@50: `0.4096173212487412` (1627/3972)
- R@100: `0.5161127895266868` (2050/3972)
- Violation@50: `0.1386412202490605` (3763/27142)
- Violation@100: `0.12419865751564975` (6587/53036)

## rule_verified_obb_only

- Policy: `filter_safe`
- Variant: `obb_only`
- Kept: `132753` / `695916`
- R@50: `0.4302618328298087` (1709/3972)
- R@100: `0.5450654582074521` (2165/3972)
- Violation@50: `0.0` (0/27079)
- Violation@100: `0.0` (0/52625)

## rule_verified_point_subtype

- Policy: `filter_safe`
- Variant: `point_subtype`
- Kept: `138574` / `695916`
- R@50: `0.4295065458207452` (1706/3972)
- R@100: `0.5367573011077543` (2132/3972)
- Violation@50: `0.0` (0/27066)
- Violation@100: `0.0` (0/52644)

## rule_verified_point_subtype_no_soft_support

- Policy: `filter_safe`
- Variant: `point_subtype_no_soft_support`
- Kept: `136115` / `695916`
- R@50: `0.42799597180261834` (1700/3972)
- R@100: `0.540281973816717` (2146/3972)
- Violation@50: `0.0` (0/27075)
- Violation@100: `0.0` (0/52662)

## Probabilistic Recalibrated

- Score formula: `semantic_ranking_score*p_geom_valid`
- Scored: `160596` / `160596` in-scope predictions
- R@50: `0.39753272910372606` (1579/3972)
- R@100: `0.5722557905337362` (2273/3972)
- Violation@50: `0.06064402033748434` (1646/27142)
- Violation@100: `0.08113356965080323` (4303/53036)

## control_distance_only

- Score formula: `1/(1+distance_3d)`
- Scored: `160596` / `160596` in-scope predictions
- R@50: `0.34541792547834843` (1372/3972)
- R@100: `0.5037764350453172` (2001/3972)
- Violation@50: `0.08459214501510574` (2296/27142)
- Violation@100: `0.10709706614375142` (5680/53036)

## control_family_specific_p_geom_valid

- Score formula: `semantic_ranking_score*p_geom_valid_family_specific`
- Scored: `160596` / `160596` in-scope predictions
- R@50: `0.46576032225579056` (1850/3972)
- R@100: `0.6047331319234642` (2402/3972)
- Violation@50: `0.028627219806941273` (777/27142)
- Violation@100: `0.03407119692284486` (1807/53036)

## control_p_geom_valid_only

- Score formula: `p_geom_valid`
- Scored: `160596` / `160596` in-scope predictions
- R@50: `0.24622356495468278` (978/3972)
- R@100: `0.5115810674723061` (2032/3972)
- Violation@50: `0.07619187974357085` (2068/27142)
- Violation@100: `0.08650727807526963` (4588/53036)

## control_shuffled_geometry

- Score formula: `semantic_ranking_score*shuffled_family_p_geom_valid`
- Scored: `160596` / `160596` in-scope predictions
- R@50: `0.14300100704934543` (568/3972)
- R@100: `0.2542799597180262` (1010/3972)
- Violation@50: `0.2070223270208533` (5619/27142)
- Violation@100: `0.1997888226864771` (10596/53036)

## control_wrong_pair_geometry

- Score formula: `semantic_ranking_score*wrong_pair_p_geom_valid`
- Scored: `160596` / `160596` in-scope predictions
- R@50: `0.11304128902316213` (449/3972)
- R@100: `0.23313192346424974` (926/3972)
- Violation@50: `0.20503279050917397` (5565/27142)
- Violation@100: `0.19845010935968022` (10525/53036)
