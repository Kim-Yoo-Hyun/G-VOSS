# H002 Full-Train Independent Support/Vertical Label Fill

## Purpose

이 문서는 85번에서 readiness를 통과한 `support_vertical_label_fill_sheet.tsv`의
127 rows를 `(codex_ver)` bootstrap label로 채운다.

핵심 질문:

```text
hidden internal reference 없이, labeler-visible relation/witness surface만 사용해
selected support/vertical labels를 completion schema에 맞춰 채울 수 있는가?
```

## Boundary

- Split: Open3DSG train-only.
- 새 paper-level experiment는 아니다.
- validation/test는 사용하지 않는다.
- 이 label은 human-confirmed label이 아니다.
- label source는 `codex_ver_support_vertical_visible_witness_bootstrap`이다.
- hidden internal reference를 읽지 않는다.
- source score/rank, `p_geom_valid`, `geometry_status`, bootstrap target label을 읽지 않는다.
- multi-view/mesh packet path는 audit evidence pointer일 뿐 posterior input이 아니다.
- paper-level posterior claim은 여전히 막혀 있다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_fill.py
```

Observed:

```text
status=full_train_independent_support_vertical_labels_filled_codex_ver
validation_used=False
rows=127
binary=114
positive=40
negative=74
excluded=13
errors=0
next=full_train_independent_support_vertical_label_ingestion
```

## Label Fill Policy

입력:

```text
independent_support_vertical_label_readiness_codex_ver/support_vertical_label_fill_sheet.tsv
independent_support_vertical_label_readiness_codex_ver/completion_schema.json
```

사용한 visible evidence:

- subject/object label.
- predicate label/family.
- packet status.
- raw witness fields:
  - distance XY/3D
  - center delta Z
  - support/contact vertical gap
  - projected overlap
  - support-contact gap/overlap
  - relative-vertical signed margin/sign agreement

사용하지 않은 evidence:

- hidden internal reference.
- source score/rank.
- `p_geom_valid`.
- `geometry_status`.
- bootstrap target `y`.
- `label_match_status`.
- `proposed_audit_role`.
- `queue_kind`.

## Counts

| Item | Count |
| --- | ---: |
| rows | 127 |
| binary usable rows | 114 |
| positive rows | 40 |
| negative rows | 74 |
| excluded rows | 13 |
| fill validation errors | 0 |

## Label Counts

| Label | Rows |
| --- | ---: |
| `reliable_informative` | 14 |
| `annotation_sparsity_candidate` | 26 |
| `valid_but_trivial_dense` | 45 |
| `invalid_relation` | 21 |
| `invalid_pair` | 8 |
| `abstain_uncertain` | 13 |

Binary policy:

```text
positive = reliable_informative, annotation_sparsity_candidate
negative = valid_but_trivial_dense, invalid_relation, invalid_pair, visibility_or_geometry_artifact
exclude_or_multiclass_only = ontology_mismatch, abstain_uncertain
```

## Family Breakdown

| Family | Labels |
| --- | --- |
| `support_contact` | `abstain_uncertain:9`, `annotation_sparsity_candidate:12`, `invalid_pair:6`, `invalid_relation:13`, `reliable_informative:6`, `valid_but_trivial_dense:26` |
| `relative_vertical` | `abstain_uncertain:4`, `annotation_sparsity_candidate:14`, `invalid_pair:2`, `invalid_relation:8`, `reliable_informative:8`, `valid_but_trivial_dense:19` |

## Predicate Breakdown

| Predicate | Labels |
| --- | --- |
| `lying on` | `abstain_uncertain:4`, `annotation_sparsity_candidate:3`, `invalid_pair:3`, `invalid_relation:3`, `reliable_informative:5`, `valid_but_trivial_dense:15` |
| `standing on` | `abstain_uncertain:2`, `annotation_sparsity_candidate:3`, `invalid_pair:2`, `invalid_relation:9`, `valid_but_trivial_dense:3` |
| `supported by` | `abstain_uncertain:3`, `annotation_sparsity_candidate:6`, `invalid_pair:1`, `invalid_relation:1`, `reliable_informative:1`, `valid_but_trivial_dense:8` |
| `higher than` | `abstain_uncertain:1`, `annotation_sparsity_candidate:5`, `invalid_relation:1`, `reliable_informative:5`, `valid_but_trivial_dense:11` |
| `lower than` | `abstain_uncertain:3`, `annotation_sparsity_candidate:9`, `invalid_pair:2`, `invalid_relation:7`, `reliable_informative:3`, `valid_but_trivial_dense:8` |

## Interpretation

이 결과는 human-confirmed label이 아니라 bootstrap label이다.

현재 useful point:

- selected support/vertical 127 rows가 모두 completion schema에 맞게 채워졌다.
- binary usable rows는 114개다.
- positive:negative는 40:74로 negative-heavy다.
- excluded 13 rows는 대부분 `abstain_uncertain`이다.
- fill validation error는 0이다.

주의점:

- 이 label은 paper-level evidence가 아니다.
- label distribution이 negative-heavy이므로 ingestion 이후 target independence와 family/predicate
  shortcut audit가 필요하다.
- 다음 단계에서 hidden internal reference를 post-label로 join해 bootstrap target과의
  관계를 분석해야 한다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_fill_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_fill_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_fill_codex_ver/completed_support_vertical_label_fill_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_fill_codex_ver/completed_support_contact_label_fill_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_fill_codex_ver/completed_relative_vertical_label_fill_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_fill_codex_ver/labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_fill_codex_ver/binary_targets_preview.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_fill_codex_ver/fill_validation_errors.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_fill.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_fill.py
```

Observed:

```text
validation_used=False
rows=127
binary=114
positive=40
negative=74
excluded=13
errors=0
```

Additional check:

```text
completed sheet value/header hits for rank, p_geom, geometry_status, target,
label_match, proposed, queue = 0
```

## Follow-Up Status

The next action from this document has been completed:

```text
full_train_independent_support_vertical_label_ingestion
```

Observed follow-up:

```text
status=full_train_independent_support_vertical_label_ingested_with_target_risk
validation_used=False
labels=127
binary=114
positive=40
negative=74
excluded=13
errors=0
```

## Next TODO

Next action:

```text
full_train_independent_support_vertical_target_independence_audit
```

Goal:

- hidden metadata와 visible-surface shortcut risk를 dedicated audit로 확인한다.
- posterior smoke 전에 controlled target slice가 가능한지 판단한다.
