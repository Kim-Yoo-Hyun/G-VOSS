# Prediction Metrics

Created at: `2026-06-11`
Status: `ready`
Families: `proximity, relative_vertical, support_contact`
K values: `50, 100`

## Semantic Only

- R@50: `0.2683693516699411` (683/2545)
- R@100: `0.35795677799607073` (911/2545)
- Violation@50: `0.12389492296034352` (1962/15836)
- Violation@100: `0.12601626016260162` (2790/22140)

## rule_verified_obb_only

- Policy: `filter_safe`
- Variant: `obb_only`
- Kept: `20303` / `25262`
- R@50: `0.29037328094302556` (739/2545)
- R@100: `0.36385068762278977` (926/2545)
- Violation@50: `0.0` (0/15211)
- Violation@100: `0.0` (0/19982)

## rule_verified_point_subtype

- Policy: `filter_safe`
- Variant: `point_subtype`
- Kept: `20147` / `25262`
- R@50: `0.29037328094302556` (739/2545)
- R@100: `0.3630648330058939` (924/2545)
- Violation@50: `0.0` (0/15156)
- Violation@100: `0.0` (0/19842)

## rule_verified_point_subtype_no_soft_support

- Policy: `filter_safe`
- Variant: `point_subtype_no_soft_support`
- Kept: `20220` / `25262`
- R@50: `0.29037328094302556` (739/2545)
- R@100: `0.3630648330058939` (924/2545)
- Violation@50: `0.0` (0/15188)
- Violation@100: `0.0` (0/19910)

## Probabilistic Recalibrated

- Score formula: `semantic_ranking_score*p_geom_valid`
- Scored: `23084` / `23084` in-scope predictions
- R@50: `0.3092337917485265` (787/2545)
- R@100: `0.3654223968565815` (930/2545)
- Violation@50: `0.07868148522354129` (1246/15836)
- Violation@100: `0.11666666666666667` (2583/22140)

## control_distance_only

- Score formula: `1/(1+distance_3d)`
- Scored: `23084` / `23084` in-scope predictions
- R@50: `0.3198428290766208` (814/2545)
- R@100: `0.36345776031434185` (925/2545)
- Violation@50: `0.11682242990654206` (1850/15836)
- Violation@100: `0.12610659439927732` (2792/22140)

## control_family_specific_p_geom_valid

- Score formula: `semantic_ranking_score*p_geom_valid_family_specific`
- Scored: `23084` / `23084` in-scope predictions
- R@50: `0.33084479371316305` (842/2545)
- R@100: `0.3654223968565815` (930/2545)
- Violation@50: `0.04988633493306391` (790/15836)
- Violation@100: `0.11056910569105691` (2448/22140)

## control_p_geom_valid_only

- Score formula: `p_geom_valid`
- Scored: `23084` / `23084` in-scope predictions
- R@50: `0.2911591355599214` (741/2545)
- R@100: `0.3654223968565815` (930/2545)
- Violation@50: `0.07823945440767871` (1239/15836)
- Violation@100: `0.11671183378500452` (2584/22140)

## control_shuffled_geometry

- Score formula: `semantic_ranking_score*shuffled_family_p_geom_valid`
- Scored: `23084` / `23084` in-scope predictions
- R@50: `0.2585461689587426` (658/2545)
- R@100: `0.35717092337917483` (909/2545)
- Violation@50: `0.13273553927759535` (2102/15836)
- Violation@100: `0.12700993676603434` (2812/22140)

## control_wrong_pair_geometry

- Score formula: `semantic_ranking_score*wrong_pair_p_geom_valid`
- Scored: `23084` / `23084` in-scope predictions
- R@50: `0.2601178781925344` (662/2545)
- R@100: `0.35402750491159135` (901/2545)
- Violation@50: `0.12515786814852237` (1982/15836)
- Violation@100: `0.12393857271906053` (2744/22140)
