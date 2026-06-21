# H002 Full-Train Independent Support/Vertical V2 Independent Label Fill

## Purpose

`94_full_train_independent_support_vertical_v2_target_path_decision.md`에서
stronger independent labels 수집 경로를 선택했다. 이번 단계는 labeler-visible
collection sheet를 `(codex_independent_ver)`로 채워 independent-label ingestion을
준비한다.

핵심 질문:

```text
Can we fill the independent collection sheet using only the labeler-visible
surface, without reading hidden metadata, v2 Codex axes, prior labels, scores,
or geometry status?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- 이 label은 human-confirmed label이 아니다.
- label source는 `codex_independent_support_vertical_visible_only_bootstrap`이다.
- hidden manifest를 읽지 않는다.
- v2 Codex factual axes를 읽지 않는다.
- prior label/use, source score/rank, `p_geom_valid`, `geometry_status`,
  `label_match`, construction queue/rank/role metadata를 읽지 않는다.
- multi-view/mesh packet path는 audit evidence pointer일 뿐 posterior input이 아니다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_label_fill.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_independent_labels_filled_codex_independent_ver
validation_used=False
test_used=False
rows=127
support=72
vertical=55
reliable=32
unreliable=70
uncertain=25
geom_support=81
geom_contra=21
errors=0
next=full_train_independent_support_vertical_v2_independent_label_ingestion
```

## Fill Policy

입력:

```text
independent_support_vertical_v2_target_path_decision_codex_ver/independent_collection_sheet.tsv
independent_support_vertical_v2_target_path_decision_codex_ver/independent_collection_schema.json
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

채운 independent fields:

```text
endpoint_identity_independent
pair_evaluability_independent
geometry_validity_independent
relation_reliability_independent
primary_reason_independent
uncertainty_reason_independent
label_notes_independent
```

## Counts

| Item | Count |
| --- | ---: |
| rows | 127 |
| support_contact rows | 72 |
| relative_vertical rows | 55 |
| fill validation errors | 0 |

## Axis Counts

### `geometry_validity_independent`

| Value | Rows |
| --- | ---: |
| `supports_predicate` | 81 |
| `contradicts_predicate` | 21 |
| `ambiguous` | 17 |
| `not_evaluable` | 8 |

### `relation_reliability_independent`

| Value | Rows |
| --- | ---: |
| `reliable` | 32 |
| `unreliable` | 70 |
| `uncertain` | 25 |

### `primary_reason_independent`

| Value | Rows |
| --- | ---: |
| `physically_supported_informative` | 15 |
| `annotation_sparsity_candidate` | 17 |
| `dense_or_trivial_relation` | 41 |
| `geometry_contradiction` | 21 |
| `visibility_or_evidence_gap` | 17 |
| `endpoint_identity_issue` | 8 |
| `better_alternative_predicate` | 8 |

### `endpoint_identity_independent`

| Value | Rows |
| --- | ---: |
| `both_valid` | 119 |
| `uncertain` | 8 |

### `pair_evaluability_independent`

| Value | Rows |
| --- | ---: |
| `evaluable` | 116 |
| `partially_evaluable` | 3 |
| `uncertain` | 8 |

## Family Breakdown

| Family | Geometry | Reliability |
| --- | --- | --- |
| `support_contact` | `supports_predicate`:43, `contradicts_predicate`:13, `ambiguous`:10, `not_evaluable`:6 | `reliable`:10, `unreliable`:46, `uncertain`:16 |
| `relative_vertical` | `supports_predicate`:38, `contradicts_predicate`:8, `ambiguous`:7, `not_evaluable`:2 | `reliable`:22, `unreliable`:24, `uncertain`:9 |

## Interpretation

이번 단계는 independent-label collection path를 실제 artifact로 진행한 것이다.
다만 결과를 과대해석하면 안 된다.

```text
This is a Codex independent visible-only bootstrap, not human-confirmed evidence.
```

좋아진 점:

- fill script는 hidden manifest와 v2 Codex axes를 읽지 않는다.
- labeler-visible collection sheet만 사용한다.
- schema validation error가 없다.
- 다음 ingestion 단계에서 hidden manifest를 post-label로 join해 strict target
  independence audit을 다시 수행할 수 있다.

주의점:

- 같은 raw witness surface를 사용하므로, distribution이 v2 target과 유사할 수 있다.
- 이 label 자체만으로 posterior smoke를 허용하지 않는다.
- ingestion과 target-independence audit을 통과해야만 posterior smoke를 고려할 수 있다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_fill_codex_independent_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_fill_codex_independent_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_fill_codex_independent_ver/completed_independent_collection_sheet_codex_independent_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_fill_codex_independent_ver/completed_support_contact_independent_sheet_codex_independent_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_fill_codex_independent_ver/completed_relative_vertical_independent_sheet_codex_independent_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_fill_codex_independent_ver/independent_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_fill_codex_independent_ver/fill_validation_errors.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_label_fill.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_label_fill.py
```

Observed:

```text
validation_used=False
test_used=False
rows=127
errors=0
```

Line counts:

```text
completed_independent_collection_sheet_codex_independent_ver.tsv = 127
completed_support_contact_independent_sheet_codex_independent_ver.tsv = 72
completed_relative_vertical_independent_sheet_codex_independent_ver.tsv = 55
independent_labels.jsonl = 127
fill_validation_errors.jsonl = 0
```

Additional check:

```text
completed sheet forbidden header hits = 0
```

## Next TODO

Completed by:

```text
96_full_train_independent_support_vertical_v2_independent_label_ingestion.md
```

Current next action:

```text
full_train_independent_support_vertical_v2_independent_target_independence_audit
```

Goal:

- construct or reject strict target-independent slices for the independent targets.
- separate expected geometry alignment from harmful prior-label/construction carryover.
- keep posterior smoke blocked unless relation reliability target independence is defensible.
