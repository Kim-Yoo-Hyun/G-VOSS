# H002 Full-Train Independent Combiner Upgrade Error Analysis

## Purpose

이 문서는 combiner upgrade smoke에서 safe gain이 나오지 않은 이유를 분석한다.

핵심 질문:

```text
C2는 왜 AUPRC를 올리면서도 safe gain이 아닌가?
C3는 왜 Brier/threshold transfer를 개선하면서도 AUPRC가 낮아지는가?
```

## Boundary

- Split: Open3DSG train-only.
- Input: combiner upgrade smoke output.
- 새 모델은 학습하지 않는다.
- validation/test는 사용하지 않는다.
- hidden audit metadata는 사용하지 않는다.
- multi-view는 사용하지 않는다.
- 분석은 grouped prediction, deployable factor, target y만 사용한다.
- label은 `(codex_ver_full_train_independent)` bootstrap label이다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_upgrade_error_analysis.py
```

Observed:

```text
status=full_train_independent_combiner_upgrade_error_analysis_ready_for_decision
validation_used=False
hidden_used=False
c2_pos_rank_improved=28
c3_new_fix=-1
next=full_train_independent_combiner_path_decision
```

## Main Diagnosis

```text
C2_ranking_gain_is_not_calibrated_safe
C3_threshold_transfer_is_safer_than_C2
C3_calibration_gain_trades_off_ranking
C2_family_gate_overcorrects_support_contact
C3_is_promising_for_relative_vertical_not_global
```

## Rank And Probability Movement

Reference: `semantic_plus_geometry`.

| View | Pos Rank Improved | Pos Rank Worsened | Neg Demoted | Neg Promoted | Mean Pos Prob Delta | Mean Neg Prob Delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `C1_residual_logit_calibrator` | 27 | 33 | 30 | 30 | +0.0040 | -0.0027 |
| `C2_family_gated_residual` | 28 | 48 | 43 | 30 | +0.0212 | +0.0024 |
| `C3_uncertainty_gated_geometry` | 42 | 31 | 37 | 29 | +0.0155 | -0.0047 |

Interpretation:

- `C2`는 positive probability를 크게 올리지만 negative probability도 같이 올린다.
- `C2`는 negative demotion도 많지만 positive rank worsened가 더 많아 global하게 안정적이지 않다.
- `C3`는 positive probability를 올리고 negative probability를 낮추는 방향은 더 바람직하다.
- `C3`가 threshold transfer에서 더 안전한 이유는 negative probability를 평균적으로 낮추기 때문이다.

## C2 Finding

`C2_family_gated_residual`은 AUPRC 기준으로 가장 좋은 upgraded combiner였지만 safe gain은 아니다.

Grouped delta:

```text
Delta AUPRC vs semantic_plus_geometry = +0.0070
Delta Brier vs semantic_plus_geometry = +0.0062
New-Fix threshold transfer = +4
```

즉, ranking은 일부 좋아지지만 probability calibration과 threshold decision이 나빠진다.

Key slices:

| Slice | Rows | Delta AUPRC | Delta Brier | New-Fix |
| --- | ---: | ---: | ---: | ---: |
| `semantic_geometry_close` | 45 | +0.1111 | -0.0116 | 0 |
| `semantic_low_geometry_high` | 97 | +0.0232 | +0.0038 | 0 |
| `semantic_high_geometry_low` | 16 | +0.0093 | +0.0716 | +4 |
| `support_contact` | 72 | -0.0162 | +0.0209 | +6 |
| `relative_vertical` | 55 | +0.0093 | -0.0055 | 0 |
| `proximity` | 31 | +0.0047 | -0.0069 | -2 |

Interpretation:

```text
C2 is useful when family/direction gate aligns with the slice, especially
semantic_geometry_close and relative_vertical/proximity. But it overcorrects
support_contact and semantic_high_geometry_low, creating calibration and
threshold failures.
```

따라서 C2의 문제는 “family gate가 필요 없다”가 아니라, 현재 family gate가 너무 거칠고
support_contact/HL에서 geometry penalty 또는 residual scale을 잘못 준다는 것이다.

## C3 Finding

`C3_uncertainty_gated_geometry`는 global AUPRC는 낮지만 threshold/Brier 관점에서는 가장 안전했다.

Grouped delta:

```text
Delta AUROC vs semantic_plus_geometry = +0.0064
Delta AUPRC vs semantic_plus_geometry = -0.0052
Delta Brier vs semantic_plus_geometry = -0.0012
New-Fix threshold transfer = -1
```

즉, ranking objective에는 손해가 있지만 calibration/threshold에는 도움이 된다.

Key slices:

| Slice | Rows | Delta AUPRC | Delta Brier | New-Fix |
| --- | ---: | ---: | ---: | ---: |
| `semantic_high_geometry_low` | 16 | +0.0570 | -0.0174 | 0 |
| `relative_vertical` | 55 | +0.0255 | -0.0078 | -3 |
| `proximity` | 31 | +0.0110 | -0.0009 | -1 |
| `semantic_geometry_close` | 45 | -0.0202 | +0.0002 | -1 |
| `support_contact` | 72 | -0.0592 | +0.0038 | +3 |
| `semantic_low_geometry_high` | 97 | -0.0029 | +0.0009 | 0 |

Interpretation:

```text
C3 is not a globally better combiner, but it is the most promising gate for
relative_vertical and semantic_high_geometry_low. Its global failure is mostly
that support_contact ranking is damaged.
```

따라서 C3의 문제는 gate idea 자체보다 relation-family별 gate scale이 없다는 점이다.

## What This Means

현재 결과는 다음을 의미한다.

1. `semantic_plus_geometry`는 여전히 강한 base다.
2. 단순 factorized posterior와 단순 residual은 base를 안정적으로 넘지 못한다.
3. C2는 ranking signal을 만들지만 calibration-safe하지 않다.
4. C3는 reliability/threshold signal을 만들지만 ranking-safe하지 않다.
5. 성능 병목은 단순히 combiner capacity 부족이 아니라 factor-target mismatch와
   family-specific reliability behavior에 있다.

## Path Decision Implication

다음 단계에서 선택지는 세 가지다.

### Option A: Keep Negative Boundary

현재 controlled bootstrap target에서는 H002 posterior performance claim을 멈춘다.

장점:

- 가장 보수적이다.
- reviewer-risk가 낮다.
- RGA/mismatch framing과 audit benchmark 쪽으로 focus를 돌릴 수 있다.

단점:

- reliability posterior method contribution은 약해진다.

### Option B: Revise Factors Before More Capacity

combiner를 키우기 전에 factor를 개선한다.

우선순위:

- support_contact 전용 contact/support residual을 더 명시적으로 분리.
- relative_vertical 전용 vertical/order residual을 분리.
- uncertainty/coverage proxy를 실제 coverage factor로 교체.
- family-specific residual scale을 shrinkage 형태로 제한.

장점:

- 현재 failure mechanism과 직접 연결된다.
- “더 큰 classifier”가 아니라 “필요한 evidence factor를 고친다”는 주장이 가능하다.

단점:

- 추가 feature engineering과 audit이 필요하다.

### Option C: Add Higher-Capacity Combiner

monotonic GBDT나 mixture-of-experts를 추가한다.

현재 판단:

```text
not recommended yet
```

이유:

- 158-row bootstrap target에서 overfit 위험이 크다.
- C2/C3가 이미 partial signal을 보였으므로 먼저 factor와 target 독립성을 개선해야 한다.
- 고용량 모델이 좋아져도 method necessity가 약하다.

## Decision

현재 단계의 decision:

```text
Do not add a generic high-capacity combiner yet.
Move to path decision: either keep this as a negative boundary or revise
relation-family-specific factors before another smoke.
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_error_analysis_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_error_analysis_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_error_analysis_codex_ver/rank_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_error_analysis_codex_ver/slice_deltas.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_error_analysis_codex_ver/row_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_error_analysis_codex_ver/top_C2_family_gated_residual_losses.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_error_analysis_codex_ver/top_C2_family_gated_residual_wins.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_error_analysis_codex_ver/top_C3_uncertainty_gated_geometry_losses.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_combiner_upgrade_error_analysis_codex_ver/top_C3_uncertainty_gated_geometry_wins.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_upgrade_error_analysis.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_combiner_upgrade_error_analysis.py
```

Observed:

```text
validation_used=False
hidden_used=False
multi_view_used=False
trains_new_model=False
```

## Next TODO

Completed next action:

```text
full_train_independent_combiner_path_decision
```

Result:

```text
full_train_independent_combiner_path_decision_factor_revision_first
```

Implication:

- H002는 계속 진행하되, 현재 posterior performance claim은 negative/partial boundary로 고정한다.
- generic high-capacity combiner를 바로 추가하지 않는다.
- 다음 단계는 relation-family-specific factor revision design이다.

Next action:

```text
full_train_independent_factor_revision_design
```
