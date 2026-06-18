# H002 Full-Train Independent Support/Vertical V2 Label Readiness

## Purpose

`89_full_train_independent_support_vertical_label_policy_revision.md`에서 direct
relation reliability label을 제거하고 factual-axis v2 policy를 정의했다. 이번
단계의 목적은 v2 label fill 전에 labeler-visible sheet가 실제로 target shortcut과
hidden construction metadata를 노출하지 않는지 검증하는 것이다.

핵심 질문:

```text
Is the support/vertical v2 factual-axis sheet ready for label fill without
exposing direct reliability targets, hidden metadata, or posterior features?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- label을 채우지 않는다.
- posterior를 학습하지 않는다.
- direct reliability label과 binary target은 labeler-visible field에 두지 않는다.
- hidden metadata는 label lock 이후 검사용 reference로만 사용한다.
- multi-view/mesh는 audit evidence pointer일 뿐 posterior input이 아니다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_readiness.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_label_readiness_ready_for_fill
rows=127
support=72
vertical=55
errors=0
leakage=0
started=0
validation_used=False
next=full_train_independent_support_vertical_v2_label_fill
```

## Readiness Checks

| Check | Result |
| --- | ---: |
| selected rows | 127 |
| support_contact rows | 72 |
| relative_vertical rows | 55 |
| readiness errors | 0 |
| leakage hits | 0 |
| v2 completion started rows | 0 |

Coverage:

| Sheet | Rows | Scans | Packet Status |
| --- | ---: | ---: | --- |
| `support_vertical` | 127 | 41 | `ready`: 124, `ready_with_packet_caveat`: 3 |
| `support_contact` | 72 | 33 | `ready`: 70, `ready_with_packet_caveat`: 2 |
| `relative_vertical` | 55 | 23 | `ready`: 54, `ready_with_packet_caveat`: 1 |

Predicate coverage:

| Predicate | Rows |
| --- | ---: |
| `higher than` | 23 |
| `lower than` | 32 |
| `lying on` | 33 |
| `standing on` | 19 |
| `supported by` | 20 |

## What Passed

The readiness gate validates:

- exact v2 header schema.
- absence of direct reliability labels and posterior target fields.
- absence of hidden metadata fields such as rank band, geometry status, label match,
  proposed role, prediction id, and prior validity label.
- v2 completion fields are blank before fill.
- packet paths exist.
- support/vertical family sheets partition the 127-row all sheet.
- proximity risk slice does not overlap the main support/vertical v2 fill sheet.
- feature contract keeps v2 review fields audit-only and out of deployable
  posterior inputs.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_readiness.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_readiness_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_readiness_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_readiness_codex_ver/v2_completion_schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_readiness_codex_ver/v2_feature_contract.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_readiness_codex_ver/v2_label_ready_manifest.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_readiness_codex_ver/support_vertical_v2_label_fill_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_readiness_codex_ver/readiness_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_label_readiness_codex_ver/leakage_hits.jsonl
```

## Interpretation

V2 readiness is a structural gate, not evidence that the posterior works. The
important result is narrower:

```text
The v2 support/vertical label sheet is ready to be filled as factual-axis review
without exposing the target shortcuts that blocked the v1 support/vertical path.
```

This keeps H002's current failure-solving path principled: the next step is not
to increase combiner capacity, but to create a less shortcut-prone target surface.

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_readiness.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_label_readiness.py
```

Observed:

```text
validation_used=False
rows=127
support=72
vertical=55
errors=0
leakage=0
started=0
```

Header leakage probe on `support_vertical_v2_label_fill_sheet.tsv` found no
forbidden target, score, rank, geometry-status, label-match, or prediction-id
fields.

## Next TODO

Next action:

```text
full_train_independent_support_vertical_v2_label_ingestion
```

Goal:

- v2 fill은 `91_full_train_independent_support_vertical_v2_label_fill.md`에서 완료됐다.
- hidden reference를 label lock 이후에만 join한다.
- `geometry_validity_target_v2`와 `relation_reliability_target_v2`를 factual axes에서
  분리해 derive한다.
- target balance, exclusion, shortcut/carryover risk를 posterior smoke 전에 검사한다.
