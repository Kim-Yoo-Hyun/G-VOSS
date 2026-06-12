# Prediction Metrics

Created at: `2026-06-11`
Status: `ready`
Families: `proximity, relative_vertical, support_contact`
K values: `50, 100`

## Semantic Only

- R@50: `0.2814702920443102` (1118/3972)
- R@100: `0.3600201409869084` (1430/3972)
- Violation@50: `0.12264610749257832` (2768/22569)
- Violation@100: `0.12459396005531792` (3874/31093)

## rule_verified_obb_only

- Policy: `filter_safe`
- Variant: `obb_only`
- Kept: `28398` / `35131`
- R@50: `0.30085599194360524` (1195/3972)
- R@100: `0.3640483383685801` (1446/3972)
- Violation@50: `0.0` (0/21664)
- Violation@100: `0.0` (0/28020)

## rule_verified_point_subtype

- Policy: `filter_safe`
- Variant: `point_subtype`
- Kept: `28187` / `35131`
- R@50: `0.30085599194360524` (1195/3972)
- R@100: `0.36304128902316213` (1442/3972)
- Violation@50: `0.0` (0/21583)
- Violation@100: `0.0` (0/27819)

## rule_verified_point_subtype_no_soft_support

- Policy: `filter_safe`
- Variant: `point_subtype_no_soft_support`
- Kept: `28288` / `35131`
- R@50: `0.30085599194360524` (1195/3972)
- R@100: `0.36304128902316213` (1442/3972)
- Violation@50: `0.0` (0/21628)
- Violation@100: `0.0` (0/27915)

## Probabilistic Recalibrated

- Score formula: `semantic_ranking_score*p_geom_valid`
- Scored: `32236` / `32236` in-scope predictions
- R@50: `0.3215005035246727` (1277/3972)
- R@100: `0.36530715005035247` (1451/3972)
- Violation@50: `0.07953387389782444` (1795/22569)
- Violation@100: `0.11655356511111825` (3624/31093)

## control_distance_only

- Score formula: `1/(1+distance_3d)`
- Scored: `32236` / `32236` in-scope predictions
- R@50: `0.32376636455186303` (1286/3972)
- R@100: `0.3640483383685801` (1446/3972)
- Violation@50: `0.11524657716336568` (2601/22569)
- Violation@100: `0.12465828321487152` (3876/31093)

## control_family_specific_p_geom_valid

- Score formula: `semantic_ranking_score*p_geom_valid_family_specific`
- Scored: `32236` / `32236` in-scope predictions
- R@50: `0.337865055387714` (1342/3972)
- R@100: `0.36530715005035247` (1451/3972)
- Violation@50: `0.051043466702113516` (1152/22569)
- Violation@100: `0.11131122760750008` (3461/31093)

## control_p_geom_valid_only

- Score formula: `p_geom_valid`
- Scored: `32236` / `32236` in-scope predictions
- R@50: `0.30614300100704933` (1216/3972)
- R@100: `0.36530715005035247` (1451/3972)
- Violation@50: `0.07944525676813328` (1793/22569)
- Violation@100: `0.11652140353134145` (3623/31093)

## control_shuffled_geometry

- Score formula: `semantic_ranking_score*shuffled_family_p_geom_valid`
- Scored: `32236` / `32236` in-scope predictions
- R@50: `0.2721550855991944` (1081/3972)
- R@100: `0.3592648539778449` (1427/3972)
- Violation@50: `0.13115335194293057` (2960/22569)
- Violation@100: `0.1250442221721931` (3888/31093)

## control_wrong_pair_geometry

- Score formula: `semantic_ranking_score*wrong_pair_p_geom_valid`
- Scored: `32236` / `32236` in-scope predictions
- R@50: `0.2729103726082578` (1084/3972)
- R@100: `0.3580060422960725` (1422/3972)
- Violation@50: `0.12264610749257832` (2768/22569)
- Violation@100: `0.1225999421091564` (3812/31093)
