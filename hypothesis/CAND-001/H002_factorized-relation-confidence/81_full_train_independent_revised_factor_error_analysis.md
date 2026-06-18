# H002 Full-Train Independent Revised Factor Error Analysis

## Purpose

이 문서는 80번 positive smoke 이후 D1-D4 gain의 출처와 shortcut risk를 분석한다.

핵심 질문:

```text
D1-D4의 gain은 실제 raw geometry witness factorization 때문인가,
아니면 family/category 또는 target-construction shortcut 때문인가?
```

## Boundary

- Split: Open3DSG train-only.
- Input: revised factor smoke output.
- 새 paper-level experiment는 아니다.
- validation/test는 사용하지 않는다.
- control probes는 train-only grouped folds 안에서만 학습한다.
- hidden audit metadata는 model input이 아니다.
- `geometry_status`는 model input이 아니다.
- multi-view는 model input이 아니다.
- label은 `(codex_ver_full_train_independent)` bootstrap label이다.
- paper-level posterior performance claim은 여전히 불가하다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_error_analysis.py
```

Observed:

```text
status=full_train_independent_revised_factor_error_analysis_ready
validation_used=False
diagnoses=6
family_only_d_auprc=-0.0000
raw_only_d_auprc=+0.0794
next=full_train_independent_revised_factor_shortcut_controls
```

## Main Diagnosis

```text
all_revised_views_improve_global_ranking
all_revised_views_improve_global_calibration
family_categorical_not_sole_gain_source
family_interactions_add_ranking_gain_beyond_d1
proximity_ranking_regresses_despite_brier_gain
raw_witness_control_has_strong_signal
```

## Shortcut Controls

Control probes are offset residual controls over `semantic_plus_geometry`.

| Control | AUROC | AUPRC | Brier | dAUPRC vs SG | dBrier vs SG | New-Fix |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `family_only_offset_control` | 0.6632 | 0.6299 | 0.2329 | -0.0000 | -0.0012 | +1 |
| `raw_only_offset_control` | 0.7718 | 0.7094 | 0.1959 | +0.0794 | -0.0382 | -16 |

Interpretation:

- D4 gain은 단순 `predicate_family` categorical shortcut만으로 설명되지 않는다.
- 이유는 `family_only_offset_control`이 AUPRC를 거의 올리지 못했고, threshold transfer도
  안전하지 않기 때문이다.
- 반대로 `raw_only_offset_control`은 강한 train-only signal을 보인다.
- 따라서 현재 가장 중요한 risk는 family shortcut보다 raw witness가 target construction
  또는 bootstrap label policy를 너무 잘 반영하는 shortcut일 가능성이다.

## D1 vs D4 Interpretation

`D1_revised_residual_base`는 family categorical feature가 없는 raw witness residual이다.
그런데 이미 `semantic_plus_geometry` 대비 다음 이득을 보였다.

```text
D1 dAUPRC vs SG = +0.0816
D1 dBrier vs SG = -0.0437
D1 New-Fix = -17
```

따라서 D4의 positive result는 family categorical feature 하나 때문은 아니다.

하지만 D4는 D1보다 AUPRC가 더 높다.

```text
D4 dAUPRC vs SG = +0.1241
D4 dBrier vs SG = -0.0462
```

즉, family interaction은 추가 ranking gain을 만든다. 다만 이것이 좋은 family-specific
geometry factor인지, 아니면 작은 158-row target에서 family별 label distribution을 탄
shortcut인지는 아직 분리되지 않았다.

## Key D4 Slices

| Slice | Rows | dAUPRC | dBrier | New-Fix |
| --- | ---: | ---: | ---: | ---: |
| `support_contact` | 72 | +0.1445 | -0.0626 | -4 |
| `relative_vertical` | 55 | +0.1194 | -0.0407 | -8 |
| `proximity` | 31 | -0.0553 | -0.0178 | -3 |
| `semantic_low_geometry_high` | 97 | +0.1367 | -0.0506 | -12 |
| `semantic_geometry_close` | 45 | +0.0584 | -0.0152 | -1 |
| `semantic_high_geometry_low` | 16 | +0.2601 | -0.1063 | -2 |

Interpretation:

- H002가 의도한 `support_contact`와 `relative_vertical`에서 gain이 크다.
- 양방향 mismatch인 `semantic_high_geometry_low`와 `semantic_low_geometry_high` 모두에서
  gain이 보인다.
- `proximity`는 Brier와 threshold transfer는 좋아지지만 AUPRC는 낮아진다. 즉,
  probability calibration은 좋아졌지만 ranking은 나빠졌을 가능성이 있다.

## Proximity Risk

`proximity`는 현재 H002 revised posterior claim의 약한 slice다.

```text
proximity rows = 31
D4 dAUPRC vs SG = -0.0553
D4 dBrier vs SG = -0.0178
D4 New-Fix = -3
```

해석:

- binary decision과 calibration에는 도움이 될 수 있다.
- 하지만 ranking objective에서는 손해가 있다.
- proximity는 dense relation noise와 annotation sparsity가 섞일 가능성이 커서,
  support/vertical처럼 raw geometry witness가 reliability를 직접 설명하지 못할 수 있다.

다음 단계에서 proximity를 별도 ablation하거나, H002 posterior claim을
`support_contact + relative_vertical` 중심으로 제한할지 확인해야 한다.

## Claim Boundary

Allowed:

```text
Revised raw-witness factorization is promising under train-only bootstrap labels,
with gains concentrated in support_contact, relative_vertical, and both mismatch
directions.
```

Blocked:

```text
Paper-level posterior improvement claim remains blocked until shortcut-controlled
ablation and stronger labels are available.
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_error_analysis_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_error_analysis_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_error_analysis_codex_ver/row_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_error_analysis_codex_ver/slice_deltas.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_error_analysis_codex_ver/rank_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_error_analysis_codex_ver/shortcut_controls.csv
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_error_analysis.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_error_analysis.py
```

Observed:

```text
validation_used=False
family_only_d_auprc=-0.0000
raw_only_d_auprc=+0.0794
```

## Next TODO

Completed next action:

```text
full_train_independent_revised_factor_shortcut_controls
```

Result:

```text
status=full_train_independent_revised_factor_shortcut_controls_ready
global_shuffle_retention=-0.6119
within_shuffle_retention=0.1565
next=full_train_independent_revised_factor_claim_boundary
```

Next action:

```text
full_train_independent_revised_factor_claim_boundary
```

Goal:

- support_contact/relative_vertical 중심의 최소 defensible claim boundary를 정한다.
- proximity를 main posterior claim에서 제외할지 결정한다.
- typed interaction을 method claim으로 둘지 raw shared witness evidence로 단순화할지 결정한다.
