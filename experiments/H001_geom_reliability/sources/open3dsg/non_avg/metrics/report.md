# Prediction Metrics

Created at: `2026-06-04`
Status: `ready`
Families: `proximity, relative_vertical, support_contact`
K values: `50, 100`

## Semantic Only

- R@50: `0.431041257367387` (1097/2545)
- R@100: `0.5320235756385069` (1354/2545)
- Violation@50: `0.13952254641909814` (2630/18850)
- Violation@100: `0.1256327409800754` (4666/37140)

## rule_verified_obb_only

- Policy: `filter_safe`
- Variant: `obb_only`
- Kept: `95308` / `496600`
- R@50: `0.45029469548133594` (1146/2545)
- R@100: `0.555992141453831` (1415/2545)
- Violation@50: `0.0` (0/18850)
- Violation@100: `0.0` (0/36932)

## rule_verified_point_subtype

- Policy: `filter_safe`
- Variant: `point_subtype`
- Kept: `98836` / `496600`
- R@50: `0.4506876227897839` (1147/2545)
- R@100: `0.5481335952848723` (1395/2545)
- Violation@50: `0.0` (0/18850)
- Violation@100: `0.0` (0/36915)

## rule_verified_point_subtype_no_soft_support

- Policy: `filter_safe`
- Variant: `point_subtype_no_soft_support`
- Kept: `97414` / `496600`
- R@50: `0.44715127701375246` (1138/2545)
- R@100: `0.5528487229862475` (1407/2545)
- Violation@50: `0.0` (0/18850)
- Violation@100: `0.0` (0/36937)

## Probabilistic Recalibrated

- Score formula: `semantic_ranking_score*p_geom_valid`
- Scored: `114600` / `114600` in-scope predictions
- R@50: `0.3944990176817289` (1004/2545)
- R@100: `0.5638506876227898` (1435/2545)
- Violation@50: `0.05702917771883289` (1075/18850)
- Violation@100: `0.07824448034464189` (2906/37140)

## control_distance_only

- Score formula: `1/(1+distance_3d)`
- Scored: `114600` / `114600` in-scope predictions
- R@50: `0.35442043222003927` (902/2545)
- R@100: `0.5080550098231827` (1293/2545)
- Violation@50: `0.08381962864721486` (1580/18850)
- Violation@100: `0.1074313408723748` (3990/37140)

## control_family_specific_p_geom_valid

- Score formula: `semantic_ranking_score*p_geom_valid_family_specific`
- Scored: `114600` / `114600` in-scope predictions
- R@50: `0.475049115913556` (1209/2545)
- R@100: `0.6047151277013753` (1539/2545)
- Violation@50: `0.02429708222811671` (458/18850)
- Violation@100: `0.031017770597738286` (1152/37140)

## control_p_geom_valid_only

- Score formula: `p_geom_valid`
- Scored: `114600` / `114600` in-scope predictions
- R@50: `0.23222003929273086` (591/2545)
- R@100: `0.49390962671905697` (1257/2545)
- Violation@50: `0.0736870026525199` (1389/18850)
- Violation@100: `0.08403338718362952` (3121/37140)

## control_shuffled_geometry

- Score formula: `semantic_ranking_score*shuffled_family_p_geom_valid`
- Scored: `114600` / `114600` in-scope predictions
- R@50: `0.13948919449901767` (355/2545)
- R@100: `0.25697445972495087` (654/2545)
- Violation@50: `0.2163395225464191` (4078/18850)
- Violation@100: `0.20498115239633818` (7613/37140)

## control_wrong_pair_geometry

- Score formula: `semantic_ranking_score*wrong_pair_p_geom_valid`
- Scored: `114600` / `114600` in-scope predictions
- R@50: `0.11394891944990176` (290/2545)
- R@100: `0.2286836935166994` (582/2545)
- Violation@50: `0.20843501326259947` (3929/18850)
- Violation@100: `0.20008077544426495` (7431/37140)
