# H002 Full-Train Independent Revised Factor Dataset

## Purpose

이 문서는 78번 factor revision design을 실제 smoke-ready row artifact로 변환한 결과를
기록한다.

핵심 질문:

```text
158-row controlled slice에 raw geometry witness를 안전하게 join하고,
FR1-FR4 revised factor block을 baseline_inputs에 materialize할 수 있는가?
```

## Boundary

- Split: Open3DSG train-only.
- Input rows: `proposed_role_balanced_codex_ver` controlled 158 rows.
- 새 모델은 학습하지 않는다.
- validation/test는 사용하지 않는다.
- hidden audit metadata는 revised factor view 안에 넣지 않는다.
- multi-view는 model input으로 넣지 않는다.
- `geometry_status`는 model feature로 넣지 않는다.
- paper-level posterior performance claim은 불가하다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_dataset.py
```

Observed:

```text
status=full_train_independent_revised_factor_dataset_ready
rows=158
matched=158
forbidden_hits=0
validation_used=False
next=full_train_independent_revised_factor_smoke
```

## Dataset Summary

Join result:

```text
input rows = 158
unique prediction ids = 158
matched raw geometry ids = 158
missing ids = 0
match_rows scanned until complete = 4,046,423
```

Target balance:

```text
y=0: 79
y=1: 79
```

Family counts:

| Family | Rows | Raw Feature Rows |
| --- | ---: | ---: |
| `support_contact` | 72 | 72 |
| `relative_vertical` | 55 | 55 |
| `proximity` | 31 | 31 |

## Materialized Revised Views

새로 추가한 `baseline_inputs` views:

```text
D1_revised_residual_base
D2_support_contact_split_residual
D3_relative_vertical_order_residual
D4_coverage_uncertainty_shrinkage
```

Feature counts:

| View | Numeric Features | Categorical Features |
| --- | ---: | ---: |
| `D1_revised_residual_base` | 37 | 0 |
| `D2_support_contact_split_residual` | 50 | 0 |
| `D3_relative_vertical_order_residual` | 47 | 0 |
| `D4_coverage_uncertainty_shrinkage` | 70 | 3 |

## Feature Blocks

`D1_revised_residual_base`:

- existing semantic/geometry/conflict factors.
- raw geometry witness fields.
- coverage flags.
- uncertainty proxies.

`D2_support_contact_split_residual`:

- D1 features.
- support-contact gate.
- contact gap, penetration proxy, XY support overlap.
- floor/support-surface flags.
- weak-contact and far-XY risk proxies.

`D3_relative_vertical_order_residual`:

- D1 features.
- relative-vertical gate.
- expected vertical sign.
- signed vertical margin and clearance.
- sign agreement/conflict.

`D4_coverage_uncertainty_shrinkage`:

- D1-D3 features.
- predicate family categorical feature.
- coverage/unsupported/raw-missing flags.
- coverage-disagreement interactions.
- uncertainty-weighted semantic-geometry residuals.

## Leakage Check

Forbidden feature key fragments:

```text
label_match
proposed_audit_role
queue_kind
rank_band
geometry_status
reviewer
labeler_confidence
label_confidence
human_confirmed
paper_locked
target_slice
```

Result:

```text
forbidden_feature_key_hits = 0
```

중요한 점:

- `underconfidence_score`와 `overconfidence_score`는 H002의 합법적인 mismatch feature다.
- labeler confidence와 target-construction confidence는 feature로 넣지 않는다.
- target 내부 hidden fields는 audit/stratification metadata로 남아 있지만 revised
  `baseline_inputs` view에는 들어가지 않는다.

## Claim Boundary

Allowed:

```text
Revised deployable factor dataset is ready for train-only smoke.
```

Blocked:

```text
No posterior performance claim is allowed before revised factor smoke.
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_dataset_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_dataset_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_dataset_codex_ver/revised_factor_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_dataset_codex_ver/feature_schema.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_dataset_codex_ver/leakage_report.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_dataset_codex_ver/join_manifest.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_dataset_codex_ver/smoke_plan.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_revised_factor_dataset_codex_ver/feature_audit_sample.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_dataset.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_revised_factor_dataset.py
```

Observed:

```text
rows=158
matched=158
forbidden_hits=0
validation_used=False
```

## Next TODO

Completed next action:

```text
full_train_independent_revised_factor_smoke
```

Result:

```text
full_train_independent_revised_factor_smoke_positive
```

Implication:

- revised factor views D1-D4를 scan-grouped train-only fold로 비교한다.
- `semantic_plus_geometry`를 main baseline으로 둔다.
- Brier, AUPRC, threshold transfer, family/direction slice를 함께 본다.
- positive result가 나와도 Codex bootstrap target 기반 paper claim으로 승격하지 않는다.

Next action:

```text
full_train_independent_revised_factor_error_analysis
```
