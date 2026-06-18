# H002 Full-Train Independent Revised Factor Claim Boundary

## Purpose

이 문서는 80-82번 revised factor 결과를 바탕으로 H002가 현재 단계에서 어디까지
주장할 수 있고, 어디서 멈춰야 하는지 고정한다.

핵심 질문:

```text
현재 train-only Codex bootstrap evidence로 H002의 posterior/reliability claim을
어느 범위까지 방어할 수 있는가?
```

## Boundary

- Split: Open3DSG train-only.
- 새 paper-level experiment는 아니다.
- validation/test는 사용하지 않았다.
- label은 `(codex_ver_full_train_independent)` bootstrap label이다.
- human-confirmed label이 아니다.
- multi-view는 model input이 아니다.
- paper-level posterior performance claim은 여전히 막혀 있다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_claim_boundary.py
```

Observed:

```text
status=full_train_independent_revised_factor_claim_boundary_ready
validation_used=False
scope=support_contact+relative_vertical
proximity_d_auprc=-0.0917
next=full_train_independent_support_vertical_audit_packet
```

## Decision

현재 H002 revised-factor claim은 다음 scope로 제한한다.

```text
support_contact + relative_vertical
```

제외:

```text
proximity
unsupported relation families
multi-view as posterior input
```

Method boundary:

| Component | Decision |
| --- | --- |
| `RGA-scoped raw-witness residual reliability layer` | core로 유지 |
| `D4 typed family interaction as final combiner` | 아직 core로 주장하지 않음 |
| generic high-capacity posterior combiner | defer |
| multi-view evidence factor | 아직 audit evidence로만 사용 |

## Evidence Table

| Role | Setting | View | dAUPRC vs SG | dBrier vs SG |
| --- | --- | --- | ---: | ---: |
| main positive | `support_contact_only` | `D4_coverage_uncertainty_shrinkage` | +0.1572 | -0.0724 |
| main positive | `relative_vertical_only` | `D4_coverage_uncertainty_shrinkage` | +0.0627 | -0.0396 |
| combined scope | `support_vertical_only` | `D4_coverage_uncertainty_shrinkage` | +0.0870 | -0.0399 |
| global but mixed | `all_families` | `D4_coverage_uncertainty_shrinkage` | +0.1241 | -0.0462 |
| excluded slice | `proximity_only` | `D4_coverage_uncertainty_shrinkage` | -0.0917 | +0.0290 |
| negative control | `all_families` | `D4_raw_witness_shuffle_global` | -0.0759 | +0.0291 |
| within-family control | `all_families` | `D4_raw_witness_shuffle_within_family` | +0.0194 | +0.0021 |
| simplified method ablation | `all_families` | `D4_no_typed_family_interaction` | +0.0827 | -0.0416 |
| scoped simplified method ablation | `support_vertical_only` | `D4_no_typed_family_interaction` | +0.0758 | -0.0348 |

## Allowed Claims

현재 허용되는 claim은 hypothesis-stage diagnostic claim이다.

```text
RGA는 relation edge를 semantic score, geometry validity, coverage, uncertainty,
label/audit evidence로 분리하는 train-only diagnostic framework다.
```

```text
Train-only controlled evidence에서는 raw-witness residual factorization이
support_contact와 relative_vertical relation reliability에 유망하다.
```

```text
positive revised-factor signal은 predicate-family categorical shortcut 하나로만
설명되지 않는다.
```

```text
raw witness block을 섞으면 gain이 사라지거나 음수로 뒤집히므로, edge-specific
raw geometry witness alignment가 중요한 신호다.
```

## Blocked Claims

현재 막힌 claim:

- H002 posterior가 paper-level relation reliability를 개선한다.
- H002 posterior가 validation/test generalization을 보인다.
- proximity가 현재 reliability posterior로 해결됐다.
- typed family interaction이 최종 method design이다.
- Codex bootstrap label이 human-confirmed label이다.
- multi-view evidence가 deployable posterior input이다.
- current D4가 최종 SOTA급 결합 방식이다.

## Why This Boundary Is Better

이 boundary가 좋은 이유는 다음과 같다.

첫째, H002의 원래 문제인 relation reliability mismatch를 유지한다. `semantic score`,
`geometry validity`, `relation reliability`를 분리한다는 핵심 주장은 여전히 살아 있다.

둘째, raw-witness shuffle control이 positive signal을 실제로 공격한다. 전역 shuffle에서
dAUPRC가 +0.1241에서 -0.0759로 뒤집히고, within-family shuffle에서도 +0.0194만 남는다.
따라서 현재 positive signal은 단순 family count나 marginal raw feature distribution이
아니라 edge-specific witness alignment에 의존한다.

셋째, 약한 slice를 main claim에서 분리한다. proximity는 dAUPRC -0.0917, dBrier +0.0290이므로
support/vertical과 같은 main reliability claim으로 묶으면 reviewer risk가 커진다.

넷째, method를 과하게 고정하지 않는다. D4는 좋은 smoke 결과를 냈지만 typed interaction이
family-wise로 안정적인지는 아직 불확실하다. 따라서 method claim은 `D4 final combiner`가
아니라 `RGA-scoped raw-witness residual reliability layer`로 둔다.

## Remaining Risk

가장 큰 risk는 label이다.

현재 label은 `(codex_ver_full_train_independent)` bootstrap label이므로, posterior가
실제 relation reliability를 배운 것인지, Codex label policy를 배운 것인지 완전히 분리되지
않았다.

따라서 다음 단계는 모델 capacity를 올리는 것이 아니라 selected scope에 대해 audit packet을
만들고 human-confirmed 또는 더 독립적인 label evidence를 확보하는 것이다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_claim_boundary_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_claim_boundary_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_claim_boundary_codex_ver/claim_table.csv
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_claim_boundary.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_claim_boundary.py
```

Observed:

```text
validation_used=False
support_contact_d_auprc=+0.1572
relative_vertical_d_auprc=+0.0627
proximity_d_auprc=-0.0917
```

## Next TODO

Completed next action:

```text
full_train_independent_support_vertical_audit_packet
```

Result:

```text
status=full_train_independent_support_vertical_audit_packet_ready
selected_rows=127
support=72
vertical=55
leakage_hits=0
next=full_train_independent_support_vertical_label_readiness
```

Next action:

```text
full_train_independent_support_vertical_label_readiness
```

Goal:

- selected support/vertical audit sheet의 fill-in schema를 검증한다.
- allowed label values와 required fields를 고정한다.
- hidden metadata 없이 label fill이 가능한지 readiness gate를 통과시킨다.
- human-confirmed label 확보 전까지 paper-level posterior claim을 보류한다.
