# Prediction Metrics

Created at: `2026-06-04`
Status: `ready`
Families: `proximity, relative_vertical, support_contact`
K values: `50, 100`

## Semantic Only

- R@50: `0.4043303121852971` (1606/3972)
- R@100: `0.5110775427995972` (2030/3972)
- Violation@50: `0.13872203033488512` (3695/26636)
- Violation@100: `0.12415160527720583` (6512/52452)

## rule_verified_obb_only

- Policy: `filter_safe`
- Variant: `obb_only`
- Kept: `131833` / `690924`
- R@50: `0.4254783484390735` (1690/3972)
- R@100: `0.5397784491440081` (2144/3972)
- Violation@50: `0.0` (0/26632)
- Violation@100: `0.0` (0/52096)

## rule_verified_point_subtype

- Policy: `filter_safe`
- Variant: `point_subtype`
- Kept: `137564` / `690924`
- R@50: `0.4242195367573011` (1685/3972)
- R@100: `0.5319738167170192` (2113/3972)
- Violation@50: `0.0` (0/26631)
- Violation@100: `0.0` (0/52121)

## rule_verified_point_subtype_no_soft_support

- Policy: `filter_safe`
- Variant: `point_subtype_no_soft_support`
- Kept: `135139` / `690924`
- R@50: `0.42321248741188316` (1681/3972)
- R@100: `0.5354984894259819` (2127/3972)
- Violation@50: `0.0` (0/26632)
- Violation@100: `0.0` (0/52131)

## Probabilistic Recalibrated

- Score formula: `semantic_ranking_score*p_geom_valid`
- Scored: `159444` / `159444` in-scope predictions
- R@50: `0.3942598187311178` (1566/3972)
- R@100: `0.5684793554884189` (2258/3972)
- Violation@50: `0.058980327376482955` (1571/26636)
- Violation@100: `0.0807214214901243` (4234/52452)

## control_distance_only

- Score formula: `1/(1+distance_3d)`
- Scored: `159444` / `159444` in-scope predictions
- R@50: `0.3429003021148036` (1362/3972)
- R@100: `0.5025176233635448` (1996/3972)
- Violation@50: `0.08349602042348701` (2224/26636)
- Violation@100: `0.106726149622512` (5598/52452)

## family_conditional_risk

- Score formula: `semantic_ranking_score*p_geom_valid_family_specific`
- Scored: `159444` / `159444` in-scope predictions
- R@50: `0.4612286002014099` (1832/3972)
- R@100: `0.5999496475327291` (2383/3972)
- Violation@50: `0.026505481303499025` (706/26636)
- Violation@100: `0.03324944711355144` (1744/52452)

## control_p_geom_valid_only

- Score formula: `p_geom_valid`
- Scored: `159444` / `159444` in-scope predictions
- R@50: `0.24295065458207452` (965/3972)
- R@100: `0.5083081570996979` (2019/3972)
- Violation@50: `0.07482354707914102` (1993/26636)
- Violation@100: `0.08607870052619537` (4515/52452)

## control_shuffled_geometry

- Score formula: `semantic_ranking_score*shuffled_family_p_geom_valid`
- Scored: `159444` / `159444` in-scope predictions
- R@50: `0.13469284994964753` (535/3972)
- R@100: `0.2663645518630413` (1058/3972)
- Violation@50: `0.20960354407568704` (5583/26636)
- Violation@100: `0.20048806527873103` (10516/52452)

## control_wrong_pair_geometry

- Score formula: `semantic_ranking_score*wrong_pair_p_geom_valid`
- Scored: `159444` / `159444` in-scope predictions
- R@50: `0.11178247734138973` (444/3972)
- R@100: `0.23187311178247735` (921/3972)
- Violation@50: `0.2056239675626971` (5477/26636)
- Violation@100: `0.19871501563334096` (10423/52452)
