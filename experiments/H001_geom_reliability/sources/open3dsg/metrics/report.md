# Prediction Metrics

Created at: `2026-05-18`
Status: `ready`
Families: `proximity, relative_vertical, support_contact`
K values: `50, 100`

## Semantic Only

- R@50: `0.3944990176817289` (1004/2545)
- R@100: `0.4962671905697446` (1263/2545)
- Violation@50: `0.13262599469496023` (2500/18850)
- Violation@100: `0.11949380721593969` (4438/37140)

## rule_verified_obb_only

- Policy: `filter_safe`
- Variant: `obb_only`
- Kept: `95308` / `496600`
- R@50: `0.4137524557956778` (1053/2545)
- R@100: `0.5277013752455796` (1343/2545)
- Violation@50: `0.0` (0/18850)
- Violation@100: `0.0` (0/36932)

## rule_verified_point_subtype

- Policy: `filter_safe`
- Variant: `point_subtype`
- Kept: `98836` / `496600`
- R@50: `0.4149312377210216` (1056/2545)
- R@100: `0.5237721021611002` (1333/2545)
- Violation@50: `0.0` (0/18850)
- Violation@100: `0.0` (0/36915)

## rule_verified_point_subtype_no_soft_support

- Policy: `filter_safe`
- Variant: `point_subtype_no_soft_support`
- Kept: `97414` / `496600`
- R@50: `0.412180746561886` (1049/2545)
- R@100: `0.5237721021611002` (1333/2545)
- Violation@50: `0.0` (0/18850)
- Violation@100: `0.0` (0/36937)

## Probabilistic Recalibrated

- Score formula: `semantic_ranking_score*p_geom_valid`
- Scored: `114600` / `114600` in-scope predictions
- R@50: `0.3842829076620825` (978/2545)
- R@100: `0.5579567779960707` (1420/2545)
- Violation@50: `0.05745358090185677` (1083/18850)
- Violation@100: `0.0803177167474421` (2983/37140)

## control_distance_only

- Score formula: `1/(1+distance_3d)`
- Scored: `114600` / `114600` in-scope predictions
- R@50: `0.35442043222003927` (902/2545)
- R@100: `0.5080550098231827` (1293/2545)
- Violation@50: `0.08381962864721486` (1580/18850)
- Violation@100: `0.1074313408723748` (3990/37140)

## family_conditional_risk

- Score formula: `semantic_ranking_score*p_geom_valid_family_specific`
- Scored: `114600` / `114600` in-scope predictions
- R@50: `0.4530451866404715` (1153/2545)
- R@100: `0.5984282907662083` (1523/2545)
- Violation@50: `0.022758620689655173` (429/18850)
- Violation@100: `0.031071620893914915` (1154/37140)

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
- R@50: `0.13713163064833006` (349/2545)
- R@100: `0.256188605108055` (652/2545)
- Violation@50: `0.2087002652519894` (3934/18850)
- Violation@100: `0.20266558966074313` (7527/37140)

## control_wrong_pair_geometry

- Score formula: `semantic_ranking_score*wrong_pair_p_geom_valid`
- Scored: `114600` / `114600` in-scope predictions
- R@50: `0.1068762278978389` (272/2545)
- R@100: `0.22554027504911592` (574/2545)
- Violation@50: `0.20063660477453582` (3782/18850)
- Violation@100: `0.1971997845988153` (7324/37140)
