# H002 Full-Train Independent Support/Vertical V2 Label Fill

## Purpose

`90_full_train_independent_support_vertical_v2_label_readiness.md`에서 readiness를
통과한 127-row support/vertical v2 sheet를 `(codex_ver)` factual axes로 채운다.

핵심 질문:

```text
Can we fill factual review axes without directly assigning relation reliability
or binary posterior targets?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- 새 posterior를 학습하지 않는다.
- 이 label은 human-confirmed label이 아니다.
- label source는 `codex_ver_support_vertical_v2_factual_axes_bootstrap`이다.
- direct relation reliability label을 만들지 않는다.
- binary target을 만들지 않는다.
- hidden prior label/use, source score/rank, `p_geom_valid`, `geometry_status`,
  `label_match`, `prediction_id`를 읽지 않는다.
- multi-view/mesh packet path는 audit evidence pointer일 뿐 posterior input이 아니다.
- target derivation은 label lock 이후 ingestion 단계에서만 수행한다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_fill.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_labels_filled_codex_ver
validation_used=False
test_used=False
rows=127
support=72
vertical=55
fill_errors=0
header_errors=0
next=full_train_independent_support_vertical_v2_label_ingestion
```

## Fill Policy

입력:

```text
independent_support_vertical_v2_label_readiness_codex_ver/support_vertical_v2_label_fill_sheet.tsv
independent_support_vertical_v2_label_readiness_codex_ver/v2_completion_schema.json
```

사용한 visible evidence:

- subject/object label.
- predicate label/family.
- evidence packet status.
- raw witness fields:
  - distance XY/3D
  - center delta Z
  - support/contact vertical gap
  - projected/subject/object overlap
  - normalized XY distance
  - support-contact gap/overlap
  - relative-vertical signed margin/sign agreement

채운 factual axes:

```text
endpoint_validity_v2
pair_visibility_v2
relation_geometry_answer_v2
geometry_evidence_strength_v2
relation_informativeness_v2
ontology_fit_v2
uncertainty_reason_v2
audit_notes_v2
```

## Counts

| Item | Count |
| --- | ---: |
| rows | 127 |
| support_contact rows | 72 |
| relative_vertical rows | 55 |
| fill validation errors | 0 |
| output header errors | 0 |

## Axis Counts

### `relation_geometry_answer_v2`

| Value | Rows |
| --- | ---: |
| `supports_predicate` | 81 |
| `contradicts_predicate` | 21 |
| `ambiguous` | 17 |
| `not_evaluable` | 8 |

### `geometry_evidence_strength_v2`

| Value | Rows |
| --- | ---: |
| `strong` | 20 |
| `moderate` | 80 |
| `weak` | 19 |
| `none` | 8 |

### `relation_informativeness_v2`

| Value | Rows |
| --- | ---: |
| `informative` | 40 |
| `redundant_room_structure` | 45 |
| `uncertain` | 42 |

### `ontology_fit_v2`

| Value | Rows |
| --- | ---: |
| `fits_predicate` | 81 |
| `better_alternative_predicate` | 8 |
| `ontology_mismatch` | 13 |
| `uncertain` | 25 |

### `endpoint_validity_v2`

| Value | Rows |
| --- | ---: |
| `both_valid` | 119 |
| `uncertain` | 8 |

### `pair_visibility_v2`

| Value | Rows |
| --- | ---: |
| `visible` | 116 |
| `partially_visible` | 3 |
| `uncertain` | 8 |

### `uncertainty_reason_v2`

| Value | Rows |
| --- | ---: |
| `none` | 53 |
| `dense_relation` | 41 |
| `weak_geometry` | 17 |
| `endpoint_identity` | 8 |
| `ontology_ambiguity` | 8 |

## Family Breakdown

| Family | Geometry Answer | Informativeness | Ontology Fit |
| --- | --- | --- | --- |
| `support_contact` | `supports_predicate`:43, `contradicts_predicate`:13, `ambiguous`:10, `not_evaluable`:6 | `informative`:18, `redundant_room_structure`:26, `uncertain`:28 | `fits_predicate`:35, `better_alternative_predicate`:8, `ontology_mismatch`:13, `uncertain`:16 |
| `relative_vertical` | `supports_predicate`:38, `contradicts_predicate`:8, `ambiguous`:7, `not_evaluable`:2 | `informative`:22, `redundant_room_structure`:19, `uncertain`:14 | `fits_predicate`:46, `uncertain`:9 |

## Interpretation

이 단계의 의미는 다음과 같이 제한한다.

```text
The v2 factual-axis sheet has been filled without direct reliability labels or
binary targets. It can now be ingested post-label to derive separate geometry
validity and relation reliability targets.
```

중요한 점:

- 이 결과는 posterior 성능 증거가 아니다.
- 이 결과는 human-confirmed annotation이 아니다.
- v1에서 문제가 됐던 direct label carryover를 줄이기 위한 bootstrap factual-axis
  surface다.
- 다음 ingestion 단계에서 hidden reference를 post-label로 join하고, target derivation
  및 independence risk를 다시 audit해야 한다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_fill_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_fill_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_fill_codex_ver/completed_support_vertical_v2_label_fill_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_fill_codex_ver/completed_support_contact_v2_label_fill_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_fill_codex_ver/completed_relative_vertical_v2_label_fill_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_fill_codex_ver/factual_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_fill_codex_ver/fill_validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_fill_codex_ver/header_errors.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_fill.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_fill.py
```

Observed:

```text
validation_used=False
test_used=False
rows=127
support=72
vertical=55
fill_errors=0
header_errors=0
```

Additional check:

```text
completed sheet forbidden header hits for independent_relation_label,
posterior_target, binary_target, label_use, confidence, geometry_status,
rank_band, label_match, prediction_id, semantic_score, and p_geom_valid = 0
```

## Next TODO

Next action:

```text
full_train_independent_support_vertical_v2_target_independence_audit
```

Goal:

- v2 ingestion은 `92_full_train_independent_support_vertical_v2_label_ingestion.md`에서 완료됐다.
- derived `geometry_validity_target_v2`와 `relation_reliability_target_v2`의 hidden
  carryover 및 shortcut risk를 전용 audit로 검사한다.
- posterior smoke 가능 여부를 strict controlled slice 기준으로 판단한다.
