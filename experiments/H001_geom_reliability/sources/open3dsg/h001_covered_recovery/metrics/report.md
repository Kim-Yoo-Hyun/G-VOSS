# Prediction Metrics

Created at: `2026-06-05`
Status: `ready`
Families: `proximity, relative_vertical, support_contact`
K values: `50, 100`

## Semantic Only

- R@50: `0.39724950884086446` (1011/2545)
- R@100: `0.49901768172888017` (1270/2545)
- Violation@50: `0.13312870669025076` (2559/19222)
- Violation@100: `0.11988163787587972` (4497/37512)

## rule_verified_obb_only

- Policy: `filter_safe`
- Variant: `obb_only`
- Kept: `95627` / `498212`
- R@50: `0.4165029469548134` (1060/2545)
- R@100: `0.5304518664047151` (1350/2545)
- Violation@50: `0.0` (0/19169)
- Violation@100: `0.0` (0/37251)

## rule_verified_point_subtype

- Policy: `filter_safe`
- Variant: `point_subtype`
- Kept: `99149` / `498212`
- R@50: `0.41768172888015714` (1063/2545)
- R@100: `0.5265225933202358` (1340/2545)
- Violation@50: `0.0` (0/19163)
- Violation@100: `0.0` (0/37228)

## rule_verified_point_subtype_no_soft_support

- Policy: `filter_safe`
- Variant: `point_subtype_no_soft_support`
- Kept: `97733` / `498212`
- R@50: `0.4149312377210216` (1056/2545)
- R@100: `0.5265225933202358` (1340/2545)
- Violation@50: `0.0` (0/19169)
- Violation@100: `0.0` (0/37256)

## Probabilistic Recalibrated

- Score formula: `semantic_ranking_score*p_geom_valid`
- Scored: `114972` / `114972` in-scope predictions
- R@50: `0.38703339882121807` (985/2545)
- R@100: `0.5607072691552063` (1427/2545)
- Violation@50: `0.059411091457704714` (1142/19222)
- Violation@100: `0.08109404990403071` (3042/37512)

## control_distance_only

- Score formula: `1/(1+distance_3d)`
- Scored: `114972` / `114972` in-scope predictions
- R@50: `0.35717092337917483` (909/2545)
- R@100: `0.5108055009823183` (1300/2545)
- Violation@50: `0.08526688169805431` (1639/19222)
- Violation@100: `0.10793879291959906` (4049/37512)

## control_family_specific_p_geom_valid

- Score formula: `semantic_ranking_score*p_geom_valid_family_specific`
- Scored: `114972` / `114972` in-scope predictions
- R@50: `0.45579567779960706` (1160/2545)
- R@100: `0.6011787819253438` (1530/2545)
- Violation@50: `0.025387576734991157` (488/19222)
- Violation@100: `0.032336319044572404` (1213/37512)

## control_p_geom_valid_only

- Score formula: `p_geom_valid`
- Scored: `114972` / `114972` in-scope predictions
- R@50: `0.23497053045186642` (598/2545)
- R@100: `0.49666011787819253` (1264/2545)
- Violation@50: `0.0753303506398918` (1448/19222)
- Violation@100: `0.08477287268074216` (3180/37512)

## control_shuffled_geometry

- Score formula: `semantic_ranking_score*shuffled_family_p_geom_valid`
- Scored: `114972` / `114972` in-scope predictions
- R@50: `0.1292730844793713` (329/2545)
- R@100: `0.2424361493123772` (617/2545)
- Violation@50: `0.2036208511081053` (3914/19222)
- Violation@100: `0.19788334399658775` (7423/37512)

## control_wrong_pair_geometry

- Score formula: `semantic_ranking_score*wrong_pair_p_geom_valid`
- Scored: `114972` / `114972` in-scope predictions
- R@50: `0.10962671905697446` (279/2545)
- R@100: `0.22829076620825148` (581/2545)
- Violation@50: `0.19982311934242014` (3841/19222)
- Violation@100: `0.1968170185540627` (7383/37512)
