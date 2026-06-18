# H002 Full-Train Independent Revised Factor Shortcut Controls

## Purpose

이 문서는 81번 error analysis 이후 D4 gain이 raw witness alignment에서 오는지,
또는 family/category와 target-construction shortcut으로 설명되는지 확인한다.

핵심 질문:

```text
Revised factor posterior의 positive smoke는 edge-specific raw geometry witness가
깨져도 유지되는가?
```

## Boundary

- Split: Open3DSG train-only.
- 새 paper-level experiment는 아니다.
- validation/test는 사용하지 않는다.
- label은 `(codex_ver_full_train_independent)` bootstrap label이다.
- `geometry_status`, `label_match_status`, `proposed_audit_role`, rank-band 같은
  target-construction metadata는 model input으로 쓰지 않는다.
- multi-view는 model input이 아니다.
- paper-level posterior performance claim은 여전히 불가하다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_shortcut_controls.py
```

Observed:

```text
status=full_train_independent_revised_factor_shortcut_controls_ready
validation_used=False
all_d4_d_auprc=+0.1241
global_shuffle_retention=-0.6119
within_shuffle_retention=0.1565
next=full_train_independent_revised_factor_claim_boundary
```

## Controls

| Control | Meaning |
| --- | --- |
| `D4_raw_witness_shuffle_global` | D4의 raw/relation-specific witness block을 전체 row에서 섞는다. |
| `D4_raw_witness_shuffle_within_family` | 같은 predicate family 내부에서만 raw witness block을 섞는다. |
| `D4_no_explicit_family_indicators` | `predicate_family`, `family_*` indicator만 제거한다. |
| `D4_no_typed_family_interaction` | explicit family indicator와 `support_contact_x_*`, `relative_vertical_x_*` typed witness interaction을 제거한다. |

Raw witness shuffle은 개별 feature를 독립적으로 섞지 않고, 한 edge의 raw witness block을
다른 edge로 옮기는 방식이다. 따라서 feature distribution은 유지하지만 edge-specific
geometry alignment는 깨진다.

## Main Results

| Setting | View | dAUPRC vs SG | dBrier vs SG |
| --- | --- | ---: | ---: |
| `all_families` | `D4_coverage_uncertainty_shrinkage` | +0.1241 | -0.0462 |
| `all_families` | `D4_raw_witness_shuffle_global` | -0.0759 | +0.0291 |
| `all_families` | `D4_raw_witness_shuffle_within_family` | +0.0194 | +0.0021 |
| `all_families` | `D4_no_explicit_family_indicators` | +0.1124 | -0.0468 |
| `all_families` | `D4_no_typed_family_interaction` | +0.0827 | -0.0416 |
| `support_vertical_only` | `D4_coverage_uncertainty_shrinkage` | +0.0870 | -0.0399 |
| `support_vertical_only` | `D4_raw_witness_shuffle_global` | -0.1086 | +0.0489 |
| `support_vertical_only` | `D4_raw_witness_shuffle_within_family` | +0.0193 | +0.0125 |
| `support_vertical_only` | `D4_no_typed_family_interaction` | +0.0758 | -0.0348 |
| `proximity_only` | `D4_coverage_uncertainty_shrinkage` | -0.0917 | +0.0290 |
| `proximity_only` | `D4_raw_witness_shuffle_global` | +0.0598 | +0.0018 |
| `proximity_only` | `D4_raw_witness_shuffle_within_family` | +0.1226 | -0.0195 |
| `proximity_only` | `D4_no_typed_family_interaction` | -0.1103 | +0.0361 |

## Interpretation

Raw witness alignment은 실제로 중요하다.

- 전체 setting에서 D4는 `semantic_plus_geometry` 대비 AUPRC +0.1241이다.
- 전역 raw witness shuffle은 dAUPRC를 -0.0759로 뒤집고 Brier도 악화시킨다.
- within-family shuffle도 dAUPRC +0.0194만 남긴다.
- 즉, D4 gain은 단순 family distribution이나 raw witness marginal distribution만으로
  설명되지는 않는다.

Explicit family indicator만으로는 gain을 설명하기 어렵다.

- `D4_no_explicit_family_indicators`도 dAUPRC +0.1124를 유지한다.
- 따라서 `predicate_family` categorical shortcut 하나가 주된 원인은 아니다.

Typed family interaction은 전체 setting에서 추가 signal을 만들지만, 아직 안정적인
claim은 아니다.

- `D4_no_typed_family_interaction`은 전체 dAUPRC +0.0827로 원래 D4보다 낮다.
- 그러나 support_contact-only와 relative_vertical-only에서는 typed interaction 제거가
  오히려 비슷하거나 더 좋다.
- 따라서 typed interaction은 global train-only gain에는 기여하지만, family-wise 설계가
  최종형이라고 주장하면 안 된다.

Proximity는 현재 H002 posterior claim에 넣기 위험하다.

- `proximity_only`에서 D4는 dAUPRC -0.0917, dBrier +0.0290이다.
- raw witness shuffle이 proximity-only에서 오히려 더 좋아지는 현상은 proximity raw
  witness가 현재 bootstrap target과 안정적으로 맞지 않음을 뜻한다.
- proximity는 dense relation noise, annotation sparsity, semantic ambiguity가 섞여 있어
  support/vertical과 같은 reliability claim으로 묶으면 안 된다.

## Decision

Recommendation:

```text
scope_to_support_vertical_and_continue_label_audit
```

다음 단계:

```text
full_train_independent_revised_factor_claim_boundary
```

현재 허용되는 주장:

```text
Train-only bootstrap setting에서 revised raw-witness factorization은
support_contact와 relative_vertical 중심으로 promising하다. 이 gain은 raw witness
alignment를 깨뜨리는 shuffle control에서 대부분 사라진다.
```

현재 막힌 주장:

```text
H002 posterior가 paper-level로 relation reliability를 개선한다.
```

막힌 이유:

- label은 아직 human-confirmed가 아니다.
- proximity는 safe ranking claim이 아니다.
- typed family interaction의 family-wise 안정성이 부족하다.
- validation/test는 사용하지 않았다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_shortcut_controls_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_shortcut_controls_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_shortcut_controls_codex_ver/control_metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_shortcut_controls_codex_ver/control_comparisons.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_shortcut_controls_codex_ver/threshold_transfer.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_shortcut_controls_codex_ver/slice_metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_shortcut_controls_codex_ver/predictions.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_shortcut_controls.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_shortcut_controls.py
```

Observed:

```text
validation_used=False
global_shuffle_retention=-0.6119
within_shuffle_retention=0.1565
```

## Next TODO

Completed next action:

```text
full_train_independent_revised_factor_claim_boundary
```

Result:

```text
status=full_train_independent_revised_factor_claim_boundary_ready
scope=support_contact+relative_vertical
proximity_d_auprc=-0.0917
next=full_train_independent_support_vertical_audit_packet
```

Next action:

```text
full_train_independent_support_vertical_audit_packet
```

Goal:

- support_contact/relative_vertical selected scope만 대상으로 audit packet을 만든다.
- proximity를 main audit packet에서 제외하고 failure/risk slice로 별도 보존한다.
- human-confirmed label audit 전까지 paper-level posterior performance claim을 보류한다.
