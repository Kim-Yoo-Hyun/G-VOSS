# H002 Full-Train Independent Controlled Error Analysis

## Purpose

이 문서는 `proposed_role_balanced_codex_ver` controlled slice에서 현재
`factorized_reliability_posterior`가 왜 `semantic_plus_geometry`보다 낮게 나왔는지
분해한다.

핵심 목적은 곧바로 더 강한 combiner를 넣는 것이 아니라, 어떤 결합 구조가 필요한지
정당화하는 것이다.

## Boundary

- Split: Open3DSG train-only.
- Validation/test는 사용하지 않는다.
- 새 combiner를 학습하지 않는다.
- `semantic_plus_geometry` 대비 현재 factorized posterior의 post-hoc error만 본다.
- hidden audit metadata는 post-hoc diagnostic axis로만 사용한다.
- hidden audit metadata는 model input이나 deployable evidence가 아니다.
- label은 `(codex_ver_full_train_independent)` bootstrap label이다.
- human-confirmed paper evidence가 아니다.

## Input

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_posterior_smoke_codex_ver/controlled_posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_posterior_smoke_codex_ver/predictions.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_posterior_smoke_codex_ver/summary.json
```

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_controlled_error_analysis.py
```

Observed:

```text
status=full_train_independent_controlled_error_analysis_ready_for_combiner_design
rows=158
validation_used=False
f_wrong_sg_correct=10
f_correct_sg_wrong=1
mean_brier_delta=0.0021
next=full_train_independent_combiner_upgrade_design
```

## Result Summary

Overall:

| Rows | Positive | Negative | Mean Brier Delta F-SG | Mean NLL Delta F-SG | Mean AbsErr Delta F-SG |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 158 | 79 | 79 | +0.0021 | +0.0017 | +0.0010 |

Correctness cases:

| Case | Count |
| --- | ---: |
| `both_correct` | 91 |
| `both_wrong` | 56 |
| `factorized_correct_sg_wrong` | 1 |
| `factorized_wrong_sg_correct` | 10 |

Interpretation:

```text
현재 factorized posterior는 semantic_plus_geometry가 맞춘 threshold decision을
더 많이 망가뜨린다. 즉, 단순히 feature를 더 많이 넣은 것이 reliability posterior를
더 좋게 만들지 않았다.
```

## View Metrics

Grouped train-only metrics:

| View | AUROC | AUPRC | Brier | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| `semantic_only` | 0.6623 | 0.6291 | 0.2360 | 0.6076 |
| `geometry_only` | 0.4575 | 0.5098 | 0.2559 | 0.4810 |
| `semantic_plus_geometry` | 0.6640 | 0.6300 | 0.2341 | 0.6392 |
| `factorized_reliability_posterior` | 0.6531 | 0.6253 | 0.2363 | 0.5823 |
| `residual_reliability_model` | 0.6558 | 0.6255 | 0.2358 | 0.6203 |

## Family Slice Finding

| Family | Rows | Pos | Neg | Delta AUPRC F-SG | Mean Brier Delta F-SG | F Wrong SG Correct | F Correct SG Wrong |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `support_contact` | 72 | 44 | 28 | +0.0121 | +0.0054 | 9 | 0 |
| `relative_vertical` | 55 | 26 | 29 | -0.0099 | +0.0014 | 1 | 1 |
| `proximity` | 31 | 9 | 22 | -0.0540 | -0.0041 | 0 | 0 |

Interpretation:

- `support_contact`는 AUPRC ranking 관점에서는 factorized가 약간 낫지만,
  Brier와 threshold decision에서는 손해가 크다.
- `relative_vertical`은 factorized가 거의 이득을 주지 못한다.
- `proximity`는 factorized ranking이 크게 나쁘지만 Brier는 약간 좋아진다.
- 따라서 relation family별로 geometry evidence를 쓰는 방식이 달라야 한다.

## Direction Slice Finding

| Direction | Rows | Pos | Neg | Delta AUPRC F-SG | Mean Brier Delta F-SG |
| --- | ---: | ---: | ---: | ---: | ---: |
| `semantic_low_geometry_high` | 97 | 42 | 55 | -0.0036 | +0.0003 |
| `semantic_geometry_close` | 45 | 29 | 16 | +0.0344 | -0.0014 |
| `semantic_high_geometry_low` | 16 | 8 | 8 | -0.0670 | +0.0235 |

Interpretation:

```text
현재 factorized posterior는 semantic과 geometry가 가까운 row에서는 도움이 되지만,
정작 H002가 중요하게 보는 high-semantic/low-geometry 구간에서는 크게 손해를 본다.
```

이는 단순 disagreement feature를 넣는 방식이 부족하다는 뜻이다. 특히 HL 구간에서는
geometry contradiction을 항상 같은 방향으로 반영하면 안 되고, relation family,
coverage, predicate, label uncertainty에 따라 geometry penalty를 다르게 줘야 한다.

## Feature Finding

Positive vs negative mean:

| Feature | Positive Mean | Negative Mean | Pos-Neg |
| --- | ---: | ---: | ---: |
| `semantic_score_norm` | 0.5787 | 0.4360 | +0.1426 |
| `p_geom_valid` | 0.8688 | 0.8468 | +0.0220 |
| `consistency_score` | 0.7539 | 0.7423 | +0.0117 |
| `absolute_disagreement` | 0.4145 | 0.5375 | -0.1231 |
| `underconfidence_score` | 0.3523 | 0.4741 | -0.1218 |
| `overconfidence_score` | 0.0622 | 0.0634 | -0.0012 |

Interpretation:

- 현재 target에서는 semantic score가 geometry validity보다 더 큰 target separation을 가진다.
- `p_geom_valid` 자체의 positive-negative separation은 작다.
- disagreement와 underconfidence는 유의미한 방향성을 보이지만, global linear posterior가
  이를 충분히 활용하지 못한다.

## Diagnosis

Error analysis 결과 현재 상태는 다음으로 해석한다.

- `factorized_reliability_posterior`는 `semantic_plus_geometry`를 아직 이기지 못한다.
- 성능 하락은 단순 random noise가 아니라 family/direction별로 구조화되어 있다.
- 현재 결합 방식은 one-size global logistic combiner에 가깝다.
- H002의 핵심 mismatch인 HL/LH를 같은 방식으로 처리하면 안 된다.
- 따라서 combiner upgrade는 필요하지만, 단순히 더 큰 classifier를 넣는 방향은 위험하다.

## Combiner Implication

다음 combiner upgrade는 아래 순서가 가장 방어 가능하다.

1. `family_gated_calibrated_fusion`
   - relation family별로 geometry evidence의 의미가 다르다.
   - `support_contact`, `relative_vertical`, `proximity`를 같은 posterior로 묶으면
     geometry signal이 평균화된다.

2. `residual_correction_over_semantic_plus_geometry`
   - 현재 가장 강한 simple baseline은 `semantic_plus_geometry`다.
   - upgraded model은 이를 대체하기보다 residual reliability correction을 학습해야 한다.

3. `uncertainty_gated_geometry_use`
   - geometry-only는 global하게 약하지만 특정 regime에서는 도움이 된다.
   - geometry penalty/boost는 confidence, coverage, disagreement, family에 의해 gate되어야 한다.

4. `SOTA-style combiner` 후보
   - sample이 작은 현재 단계에서는 `family-conditioned logistic calibration` 또는
     `hierarchical logistic calibration`이 1순위다.
   - sample이 늘어나면 `monotonic GBDT`, `mixture-of-experts`, `stacked calibrator`,
     `isotonic/beta calibration`을 비교할 수 있다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_error_analysis_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_error_analysis_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_error_analysis_codex_ver/view_metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_error_analysis_codex_ver/slice_errors.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_error_analysis_codex_ver/feature_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_error_analysis_codex_ver/row_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_error_analysis_codex_ver/top_factorized_losses.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_controlled_error_analysis_codex_ver/top_factorized_wins.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_controlled_error_analysis.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_controlled_error_analysis.py
```

Observed:

```text
validation_used=False
trains_new_combiner=False
hidden_metadata_as_model_input=False
```

## Next TODO

Completed next action:

```text
full_train_independent_combiner_upgrade_design
```

Result:

```text
full_train_independent_combiner_upgrade_design_ready_for_smoke
```

The design step fixed three next-smoke upgraded combiner candidates:

```text
C1_residual_logit_calibrator
C2_family_gated_residual
C3_uncertainty_gated_geometry
```

The next action is:

```text
full_train_independent_combiner_upgrade_smoke
```
