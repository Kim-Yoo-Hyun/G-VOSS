# H002 Reliability Target V4 Matched Contrast Label Readiness

Date: 2026-06-21 KST

## Purpose

이 단계는 v4 matched-contrast gap audit 이후 남은 `158` row / `79` pair label-ready
sheet가 실제 label fill로 넘어가도 되는지 검증하는 gate다. Label fill, ingestion,
posterior smoke는 실행하지 않았다.

검증 대상:

- visible label schema
- packet path existence
- excluded pair removal
- matched pair role balance
- hidden/proxy value leakage
- train-only boundary

## Boundary

```text
split = train_only
validation_used = False
test_used = False
labels_filled = False
posterior_trained = False
posterior_smoke_allowed = False
multi_view_as_model_input = False
paper_metric_evidence = False
```

Multi-view, mesh, contact/context packets are used only as audit/label evidence. They are
not posterior input.

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_label_readiness.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_label_readiness.py
```

## Result

```text
status = h002_reliability_target_v4_matched_contrast_label_readiness_ready_for_label_fill
rows = 158
pairs = 79
ready rows = 139
limited-view rows = 19
excluded pair count = 1
excluded pair row count = 2
path errors = 0
leakage hits = 0
validation_used = False
test_used = False
next = reliability_target_v4_matched_contrast_label_fill
```

## Label-Ready Counts

| Item | Count |
| --- | ---: |
| label-ready rows | 158 |
| label-ready pairs | 79 |
| ready rows | 139 |
| limited-view rows | 19 |
| support_contact rows | 90 |
| relative_vertical rows | 68 |
| positive proxy rows | 79 |
| negative proxy rows | 79 |
| excluded pair count | 1 |
| excluded pair rows | 2 |

Packet status:

| Status | Rows |
| --- | ---: |
| `ready` | 139 |
| `limited_view_evaluable` | 19 |

## Validation

| Check | Result |
| --- | --- |
| expected columns match | true |
| input validation errors | 0 |
| sheet validation errors | 0 |
| packet path errors | 0 |
| leakage hits | 0 |

## Interpretation

The 158-row / 79-pair v4 matched-contrast sheet is ready for label fill.

이 결과가 의미하는 것은 posterior 성능이 아니라 label-fill readiness다. 즉, H002의 다음
단계에서 visible-only label을 채울 수 있는 sheet가 준비됐다는 뜻이다. Posterior smoke는
label fill 이후 ingestion과 target-independence audit이 통과할 때까지 계속 block한다.

중요한 점:

- `positive_proxy` / `negative_proxy` balance는 `79/79`로 유지된다.
- `v4pair_0042`처럼 replacement-needed row가 포함된 pair는 label surface에서 제거됐다.
- label-facing sheet와 packet path에서 contrast role, rank, semantic score, geometry status,
  target-construction proxy leakage는 발견되지 않았다.
- `limited_view_evaluable` 19 rows는 한쪽 endpoint crop이 부족하지만 mesh/contact/context
  evidence가 있어 label fill 대상에 남긴다.

## Label To Binary Policy

Label fill 이후 binary target으로 변환할 때의 기본 policy는 다음과 같다.

| Label | Binary Use |
| --- | --- |
| `reliable` | positive |
| `unreliable` | negative |
| `uncertain` | exclude or multiclass-only |

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_label_readiness.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/ready_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/ready_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/label_schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/pair_readiness.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/input_validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/sheet_validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/packet_path_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_readiness/leakage_hits.jsonl
```

## Next TODO

```text
reliability_target_v4_matched_contrast_label_fill
```

Goal:

- fill visible-only reliability labels for 158 rows.
- keep hidden role/rank/semantic/geometry/proxy fields out of the label decision.
- treat label fill as hypothesis-stage evidence, not paper metric evidence.
- proceed to ingestion only after the completed sheet validates.
