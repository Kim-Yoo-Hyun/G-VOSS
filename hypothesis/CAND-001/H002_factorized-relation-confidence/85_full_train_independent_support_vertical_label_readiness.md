# H002 Full-Train Independent Support/Vertical Label Readiness

## Purpose

이 문서는 84번에서 만든 `support_contact + relative_vertical` audit packet이 실제
independent label fill에 들어가도 되는지 검증한다.

핵심 질문:

```text
selected support/vertical audit sheet가 hidden metadata 없이, 고정된 allowed values와
required fields로 label fill 가능한 상태인가?
```

## Boundary

- Split: Open3DSG train-only.
- 새 paper-level experiment는 아니다.
- validation/test는 사용하지 않는다.
- 이 단계는 label을 채우지 않는다.
- `support_contact + relative_vertical` selected scope만 검증한다.
- `proximity`는 main label-fill path에서 제외하고 risk slice로 유지한다.
- multi-view/mesh packet은 audit evidence only다.
- hidden metadata는 label lock 이후에만 join한다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_readiness.py
```

Observed:

```text
status=full_train_independent_support_vertical_label_readiness_ready_for_label_fill
validation_used=False
rows=127
errors=0
leakage=0
next=full_train_independent_support_vertical_label_fill
```

## Coverage

| Sheet | Rows | Scans | Status |
| --- | ---: | ---: | --- |
| `support_vertical` | 127 | 41 | `pass` |
| `support_contact` | 72 | 33 | `pass` |
| `relative_vertical` | 55 | 23 | `pass` |

Family coverage:

| Family | Rows |
| --- | ---: |
| `support_contact` | 72 |
| `relative_vertical` | 55 |

Packet status:

```text
ready = 124
ready_with_packet_caveat = 3
```

## Readiness Checks

| Check | Count |
| --- | ---: |
| readiness errors | 0 |
| leakage hits | 0 |
| review-started rows | 0 |
| selected label-ready rows | 127 |
| internal reference rows | 127 |
| proximity risk rows | 31 |

검증한 항목:

- expected header와 실제 header 일치.
- `blind_review_id` 중복 없음.
- 모든 selected row가 `internal_reference_post_label_only.jsonl`에 존재.
- `proximity_risk_slice_post_label_only.jsonl`과 selected sheet의 ID overlap 없음.
- `multiview_packet`, `pointcloud_or_mesh_packet`, `contact_or_context_sheet` path 존재.
- reviewer fill-in field가 아직 비어 있음.
- labeler surface leakage hit 0.
- sampled packet text leakage hit 0.
- hidden metadata는 labeler sheet에 없고 internal reference에만 있음.

## Completion Schema

Label fill용 schema를 다음 파일에 고정했다.

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_readiness_codex_ver/completion_schema.json
```

Required completion fields:

```text
reviewer_id
review_round
subject_identity_valid
object_identity_valid
object_pair_visible
relation_visible_or_inferable
visual_3d_support
relation_informativeness
independent_relation_label
confidence
```

Optional completion field:

```text
evidence_notes
```

Allowed values:

| Field | Allowed Values |
| --- | --- |
| `subject_identity_valid` | `yes`, `no`, `uncertain` |
| `object_identity_valid` | `yes`, `no`, `uncertain` |
| `object_pair_visible` | `yes`, `no`, `partial`, `uncertain` |
| `relation_visible_or_inferable` | `yes`, `no`, `uncertain` |
| `visual_3d_support` | `supports`, `contradicts`, `uncertain`, `not_evaluable` |
| `relation_informativeness` | `informative`, `trivial_dense`, `uncertain`, `not_evaluable` |
| `independent_relation_label` | `reliable_informative`, `valid_but_trivial_dense`, `annotation_sparsity_candidate`, `ontology_mismatch`, `invalid_relation`, `invalid_pair`, `visibility_or_geometry_artifact`, `abstain_uncertain` |
| `confidence` | `high`, `medium`, `low` |

Binary policy:

| Binary Use | Labels |
| --- | --- |
| positive | `reliable_informative`, `annotation_sparsity_candidate` |
| negative | `valid_but_trivial_dense`, `invalid_relation`, `invalid_pair`, `visibility_or_geometry_artifact` |
| exclude/multiclass only | `ontology_mismatch`, `abstain_uncertain` |

## Label Fill Sheet

Label fill은 다음 sheet에서 진행한다.

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_readiness_codex_ver/support_vertical_label_fill_sheet.tsv
```

이 파일은 84번의 `support_vertical_audit_sheet.tsv`를 readiness-passed fill sheet로
복사한 것이다. 아직 review field는 모두 비어 있다.

## Hidden Reference Policy

Hidden metadata는 다음 파일에만 있다.

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_audit_packet_codex_ver/internal_reference_post_label_only.jsonl
```

Policy:

```text
hidden_fields_must_not_be_visible_before_label_lock = true
hidden_fields_must_not_be_model_inputs = true
```

따라서 label fill 이전에는 이 파일을 reviewer에게 제공하지 않는다. Label lock 이후에만
bootstrap target, geometry status, semantic rank, p_geom, disagreement 등을 post-hoc으로
join한다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_readiness_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_readiness_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_readiness_codex_ver/completion_schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_readiness_codex_ver/label_ready_manifest.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_readiness_codex_ver/support_vertical_label_fill_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_readiness_codex_ver/readiness_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_readiness_codex_ver/leakage_hits.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_readiness.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_readiness.py
```

Observed:

```text
validation_used=False
rows=127
errors=0
leakage=0
```

## Next TODO

Completed next action:

```text
full_train_independent_support_vertical_label_fill
```

Result:

```text
status=full_train_independent_support_vertical_labels_filled_codex_ver
rows=127
binary=114
positive=40
negative=74
excluded=13
errors=0
next=full_train_independent_support_vertical_label_ingestion
```

Next action:

```text
full_train_independent_support_vertical_label_ingestion
```

Goal:

- completed label sheet와 `internal_reference_post_label_only.jsonl`을 label-lock 이후 join한다.
- filled labels를 validated labels, binary targets, multiclass labels로 export한다.
- bootstrap label과 hidden audit metadata 사이의 shortcut risk를 다시 검사한다.
- human-confirmed label 확보 전까지 paper-level posterior claim을 보류한다.
