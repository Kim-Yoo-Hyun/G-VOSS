# H002 Real Label Assumption Claim Audit

Last updated: 2026-06-13

## Purpose

사용자 지시에 따라 `(codex_ver)` controlled labels를 hypothesis-stage real label로
취급하고, 현재 H002 posterior 결과가 어디까지 가설을 지지하는지 재해석한다.

중요한 기록 원칙:

```text
artifact provenance = codex_ver
current interpretation = user-directed real-label assumption
```

즉, 파일 provenance를 바꾸지는 않는다. 다만 hypothesis-stage 판단에서는 현재
`codex_ver` target을 real binary reliability label처럼 보고 다음 gate를 판단한다.

## Assumption

Working assumption:

```text
reliable_promote / unreliable_dense_noise labels in controlled_codex_ver targets
are accepted as real relation-reliability labels for hypothesis-stage analysis.
```

Still unchanged:

```text
split = train_only
validation usage = false
test usage = false
V_mv_e model input = false
```

## Current Targets

| Target | Rows | Positive | Negative | Family | Geometry status | Rank control |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `mined_controlled_codex_ver` | 96 | 48 | 48 | `proximity` | `satisfied` | `rank_201_500`, `rank_501_1000`, `rank_gt1000` |
| `combined_controlled_codex_ver` | 123 | 64 | 59 | `proximity` | `satisfied` | mined rank bands + strict `tail` seed |

The core controlled setting is good for H002 because:

- same predicate family: `proximity`
- same predicate label: `close by`
- same geometry status: `satisfied`
- no validation/test rows
- no `V_mv_e` input

This directly tests:

```text
geometry validity != relation reliability
```

## Reinterpreted Result

Train-internal 5-fold:

| Target | `semantic_plus_geometry` AUPRC | `factorized` AUPRC | Delta AUPRC | Delta Brier | Numeric rule |
| --- | ---: | ---: | ---: | ---: | --- |
| `mined_controlled_codex_ver` | 0.9546 | 0.9552 | +0.0006 | -0.0012 | fail |
| `combined_controlled_codex_ver` | 0.7321 | 0.7658 | +0.0337 | -0.0081 | pass by AUPRC |

Under the real-label assumption:

- `combined_controlled_codex_ver` gives weak positive support for the current
  posterior form because AUPRC improves by `+0.0337` and AUROC does not drop.
- `mined_controlled_codex_ver` does not support a factorized posterior advantage
  because the improvement over `semantic_plus_geometry` is almost zero.

## Why This Is Not Strong Yet

The acceptance rule from `35_factorized_validation_plan.md` also required that the
gain remain after direct identity/RGA-bucket features are removed.

That condition is not yet satisfied.

Control-view evidence:

| Target | View | AUROC | AUPRC | Brier |
| --- | --- | ---: | ---: | ---: |
| `mined_controlled_codex_ver` | `drop_direct_identity` | 0.9484 | 0.9546 | 0.1024 |
| `mined_controlled_codex_ver` | `drop_direct_identity_rank` | 0.5486 | 0.5402 | 0.2582 |
| `mined_controlled_codex_ver` | `safe_continuous` | 0.5486 | 0.5402 | 0.2582 |
| `combined_controlled_codex_ver` | `drop_direct_identity` | 0.7940 | 0.7321 | 0.1925 |
| `combined_controlled_codex_ver` | `drop_direct_identity_rank` | 0.5313 | 0.5288 | 0.2566 |
| `combined_controlled_codex_ver` | `safe_continuous` | 0.5313 | 0.5288 | 0.2566 |

Interpretation:

- `drop_direct_identity` almost equals `semantic_plus_geometry`.
- Once rank/normalized semantic score is also removed, performance collapses
  near random.
- Therefore the current factorized gain is not yet clearly from `C_e` and `U_e`.
- It may be carried by semantic/rank structure or target construction.

## Hypothesis-Stage Verdict

With `codex_ver` treated as real labels:

```text
H002 has weak conditional support on the combined controlled target,
but not strong support for the factorized posterior method.
```

What is supported:

- RGA framing is useful because all rows are geometry-satisfied but reliability
  labels still differ.
- `geometry_only` is near random in the controlled target, so geometry validity
  alone is not relation reliability.
- `semantic_plus_geometry` is a strong baseline.
- Factorized posterior can run and sometimes improves AUPRC.

What is not yet supported:

- `C_e`/`U_e` add robust signal beyond `S_e + G_e`.
- factorized posterior advantage survives rank/identity controls.
- the result is stable across target variants.
- the result is stable under grouped scene-level splits.

## Remaining Hypothesis Checks

### 1. Grouped CV By Scan

Current train-internal 5-fold is row-stratified. The next check should group by
`scan_id` so train/test folds do not share the same scene.

Why:

- relation candidates from the same scene can share source/rank/geometry
  structure.
- row-level crossfit can overestimate generalization.

Required result:

```text
factorized - semantic_plus_geometry remains positive under scan-grouped CV.
```

### 2. Factor Ablation

Run explicit factor views:

```text
S_e
G_e
S_e + G_e
S_e + G_e + C_e
S_e + G_e + U_e
S_e + G_e + C_e + U_e
```

Why:

- current result does not isolate whether `C_e` or `U_e` actually matter.
- H002 claim is factorized reliability, not just a larger feature set.

Required result:

```text
C_e/U_e improve AUPRC or Brier beyond S_e + G_e.
```

### 3. Rank-Band Controlled Evaluation

Report performance inside each rank band:

```text
rank_201_500
rank_501_1000
rank_gt1000
tail strict seed
```

Why:

- current labels may be partly recoverable from rank/semantic structure.
- combined target includes strict tail rows, while mined target does not.

Required result:

```text
factorized gain is not concentrated only in the strict tail seed.
```

### 4. Target Variant Stability

Compare at least:

```text
mined_controlled only
combined_controlled
combined minus strict seed
strict seed only
```

Why:

- mined-only fails the numeric rule.
- combined passes by AUPRC, so the strict seed may be carrying the effect.

Required result:

```text
claim should rely on mined/controlled target, not only on strict seed mixture.
```

### 5. Proxy-Baseline Audit

Add diagnostic baselines:

```text
rank_only
negative_rank_only
rank_band_only
p_geom_valid_only
endpoint_category_or_structure_proxy, if available
label_match_status_oracle, diagnostic only
```

Why:

- `negative_semantic_score_norm` is very strong as a probe.
- the label construction may encode "lower semantic rank means more reliable
  underconfidence" rather than true factorized reliability.

Required result:

```text
factorized posterior beats the strongest simple proxy baseline.
```

### 6. Bootstrap Confidence Interval

Estimate uncertainty for:

```text
Delta AUPRC
Delta Brier
Delta AUROC
```

Why:

- N is still small: 96 or 123 rows.
- `+0.0337` AUPRC on combined target may not be stable.

Required result:

```text
paired bootstrap CI excludes zero for the chosen primary metric.
```

### 7. Calibration Check

Report reliability/calibration:

```text
Brier
ECE
reliability bins
threshold behavior
```

Why:

- H002 is a reliability posterior, so ranking alone is not enough.
- combined target improves AUPRC but Brier improvement is only `-0.0081`, below
  the stronger `-0.02` threshold.

Required result:

```text
posterior is not only better-ranked but also better calibrated.
```

### 8. Failure Audit

Inspect rows where:

```text
factorized correct, semantic_plus_geometry wrong
factorized wrong, semantic_plus_geometry correct
```

Why:

- this tells whether improvement is a meaningful reliability signal or a
  target-construction artifact.

Required result:

```text
factorized wins correspond to coverage/uncertainty/geometry-evidence reasoning.
```

## Next TODO

Next document:

```text
41_grouped_control_smoke.md
```

Recommended next implementation:

- rerun controlled posterior smoke with `scan_id`-grouped folds.
- add factor ablations for `S+G+C`, `S+G+U`, `S+G+C+U`.
- report mined-only and combined target separately.
- keep validation/test unused.
