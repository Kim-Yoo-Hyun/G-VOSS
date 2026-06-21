# H002 Full-Train Independent Support/Vertical V2 Label Ingestion

## Purpose

`91_full_train_independent_support_vertical_v2_label_fill.md`에서 채운 v2 factual
axes를 label lock 이후 hidden reference와 조인하고, target을 두 개로 분리해
materialize한다.

핵심 질문:

```text
Can geometry validity and relation reliability be derived separately from v2
factual axes without exposing hidden metadata or target-derivation fields as
posterior inputs?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- label은 human-confirmed가 아니라 Codex bootstrap label이다.
- hidden internal reference는 label-lock 이후에만 join한다.
- hidden target-construction metadata는 audit-only이며 posterior input이 아니다.
- v2 factual axes는 target derivation field이며 posterior input이 아니다.
- source score/rank와 `p_geom_valid`는 labeler에게 숨겼고, label-lock 이후
  deployable evidence candidate로만 보존한다.
- `proximity`는 main ingestion path에서 제외하고 risk slice로만 보존한다.
- multi-view는 audit evidence pointer일 뿐 posterior input이 아니다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_ingestion.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_label_ingested_with_target_risk
validation_used=False
test_used=False
labels=127
geom_binary=100
geom_pos=79
geom_neg=21
rel_binary=106
rel_pos=32
rel_neg=74
errors=0
next=full_train_independent_support_vertical_v2_target_independence_audit
```

## Target Derivation

### Geometry Validity Target

Positive:

```text
relation_geometry_answer_v2 = supports_predicate
geometry_evidence_strength_v2 in {strong, moderate}
```

Negative:

```text
relation_geometry_answer_v2 = contradicts_predicate
```

Excluded:

```text
ambiguous, not_evaluable, weak, none
```

### Relation Reliability Target

Positive:

```text
endpoint_validity_v2 = both_valid
pair_visibility_v2 in {visible, partially_visible}
relation_geometry_answer_v2 = supports_predicate
geometry_evidence_strength_v2 in {strong, moderate}
relation_informativeness_v2 = informative
ontology_fit_v2 = fits_predicate
```

Negative:

```text
endpoint invalid
or relation_geometry_answer_v2 = contradicts_predicate
or relation_informativeness_v2 in {dense_trivial, redundant_room_structure}
or ontology_fit_v2 in {better_alternative_predicate, ontology_mismatch}
```

Excluded:

```text
uncertain / weak / not_visible / not_evaluable / ambiguous cases
```

## Counts

| Item | Count |
| --- | ---: |
| completed sheet rows | 127 |
| internal reference rows | 127 |
| proximity risk slice rows | 31 |
| validated v2 labels | 127 |
| ingestion errors | 0 |

Target counts:

| Target | Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `geometry_validity_target_v2` | 100 | 79 | 21 | 0.7900 | 27 |
| `relation_reliability_target_v2` | 106 | 32 | 74 | 0.3019 | 21 |

Family breakdown:

| Target | Family | Positive | Negative |
| --- | --- | ---: | ---: |
| `geometry_validity_target_v2` | `support_contact` | 43 | 13 |
| `geometry_validity_target_v2` | `relative_vertical` | 36 | 8 |
| `relation_reliability_target_v2` | `support_contact` | 10 | 47 |
| `relation_reliability_target_v2` | `relative_vertical` | 22 | 27 |

## Target Independence Probe

Basic post-label probe status:

| Target | Probe Status | Hidden Risks | Visible Non-Target Shortcuts |
| --- | --- | ---: | ---: |
| `geometry_validity_target_v2` | `target_independence_risk_hidden_metadata_correlated` | 6 | 1 |
| `relation_reliability_target_v2` | `target_independence_risk_hidden_metadata_correlated` | 7 | 1 |

Top hidden risks:

| Target | Hidden Key | Majority Acc | NMI | Pos Rate Range |
| --- | --- | ---: | ---: | ---: |
| `geometry_validity_target_v2` | `relation_validity_label_hidden` | 0.8600 | 0.4610 | 1.0000 |
| `geometry_validity_target_v2` | `label_use_hidden` | 0.7900 | 0.3242 | 0.4476 |
| `geometry_validity_target_v2` | `posterior_target_y_hidden` | 0.7900 | 0.3242 | 0.4476 |
| `geometry_validity_target_v2` | `proposed_audit_role_hidden` | 0.8100 | 0.2688 | 1.0000 |
| `geometry_validity_target_v2` | `rank_band_hidden` | 0.8300 | 0.2065 | 0.6250 |
| `relation_reliability_target_v2` | `relation_validity_label_hidden` | 0.7547 | 0.3313 | 0.6250 |
| `relation_reliability_target_v2` | `label_use_hidden` | 0.7453 | 0.3196 | 0.5235 |
| `relation_reliability_target_v2` | `posterior_target_y_hidden` | 0.7453 | 0.3196 | 0.5235 |
| `relation_reliability_target_v2` | `rank_band_hidden` | 0.7075 | 0.1686 | 0.5556 |
| `relation_reliability_target_v2` | `proposed_audit_role_hidden` | 0.7075 | 0.1630 | 1.0000 |

해석:

- ingestion 자체는 성공했다.
- `geometry_validity_target_v2`와 `relation_reliability_target_v2`가 분리되어
  materialize됐다.
- 그러나 basic probe는 여전히 hidden prior label/use 및 construction metadata와의
  상관을 찾는다.
- 따라서 posterior smoke를 바로 진행하지 않는다.
- 다음 단계는 dedicated v2 target-independence audit이다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_ingestion_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_ingestion_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_ingestion_codex_ver/validated_v2_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_ingestion_codex_ver/geometry_validity_targets_v2.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_ingestion_codex_ver/relation_reliability_targets_v2.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_ingestion_codex_ver/geometry_validity_posterior_rows_v2.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_ingestion_codex_ver/relation_reliability_posterior_rows_v2.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_ingestion_codex_ver/excluded_targets_v2.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_ingestion_codex_ver/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_ingestion_codex_ver/target_group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_ingestion_codex_ver/shortcut_audit.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_ingestion_codex_ver/ingestion_errors.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_ingestion.py
```

Observed line counts:

```text
validated_v2_labels.jsonl = 127
geometry_validity_targets_v2.jsonl = 100
relation_reliability_targets_v2.jsonl = 106
geometry_validity_posterior_rows_v2.jsonl = 100
relation_reliability_posterior_rows_v2.jsonl = 106
excluded_targets_v2.jsonl = 48
ingestion_errors.jsonl = 0
```

Additional check:

```text
deployable_evidence_after_label_lock does not include v2 target-derivation fields.
v2 target-derivation fields are kept under audit_only_target_derivation_fields.
```

## Next TODO

Next action:

```text
revise_full_train_independent_support_vertical_v2_target_or_collect_independent_labels
```

Goal:

- v2 target-independence audit은 `93_full_train_independent_support_vertical_v2_target_independence_audit.md`에서 완료됐다.
- strict relation-reliability slice가 없으므로 posterior smoke는 계속 막는다.
- target construction을 다시 수정할지, stronger independent labels를 수집할지 결정한다.
