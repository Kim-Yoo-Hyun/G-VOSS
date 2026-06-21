# H002 Reliability Target V3 Object/Endpoint Candidate Mining

Date: 2026-06-20 KST

## Purpose

`143_reliability_target_v3_object_endpoint_controlled_plan.md`에서 정한
object/endpoint-controlled sampling cell을 실제 train-only label sheet로 변환한다.

핵심 질문:

```text
Can we mine a labeler-visible v3 review sheet from object/endpoint-controlled
cells while keeping proxy labels and construction fields hidden until after
label lock?
```

## Boundary

- Split: Open3DSG train-only.
- Validation/test rows: not used.
- Label fill: not run.
- Posterior training/smoke: not run.
- H001 artifacts: not modified.
- Multi-view remains audit/label evidence only, not model input.
- Candidate-positive / candidate-negative proxy는 sampling stratum일 뿐 target label이 아니다.

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_candidate_mining.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_candidate_mining.py
```

Observed:

```text
status=h002_reliability_target_v3_object_endpoint_candidate_mining_ready_with_selection_deficit
requested=158
selected=130
residual=28
pos_proxy=68
neg_proxy=62
leakage=0
packet_errors=0
validation_used=False
test_used=False
posterior_allowed=False
next=reliability_target_v3_object_endpoint_label_fill
```

## Result

Status:

```text
h002_reliability_target_v3_object_endpoint_candidate_mining_ready_with_selection_deficit
```

Decision:

```text
The label sheet is ready, but duplicate-pair and scan-diversity controls left a
selection deficit. Proceed to label fill only if this controlled size is
acceptable; otherwise relax caps explicitly.
```

## Counts

| Item | Count |
| --- | ---: |
| candidate pool rows | 302 |
| recommended cells | 22 |
| requested rows from plan | 158 |
| selected rows | 130 |
| selection residual | 28 |
| candidate-positive proxy strata | 68 |
| candidate-negative proxy strata | 62 |
| support_contact | 77 |
| relative_vertical | 53 |
| unique scans | 70 |
| unique physical pairs | 118 |
| duplicated physical-pair keys | 12 |
| max rows per scan | 9 |
| packet path errors | 0 |
| label-surface leakage hits | 0 |
| validation errors | 0 |

## Tier Summary

| Tier | Rows | Pos Proxy | Neg Proxy | support_contact | relative_vertical | Unique Scans | Unique Pairs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `T1_strict_subject_object_family` | 50 | 25 | 25 | 22 | 28 | 29 | 45 |
| `T2_object_family_fallback` | 31 | 14 | 17 | 23 | 8 | 27 | 30 |
| `T3_endpoint_family_balance` | 49 | 29 | 20 | 32 | 17 | 33 | 46 |

## Labeler-Visible Surface

The generated TSV exposes only:

- object/relation identity fields
- family-level review question and cues
- packet paths for audit evidence
- blank v3 completion fields

The generated TSV does not expose:

- candidate proxy class
- queue kind
- sampling tier/cell
- semantic rank/score
- `p_geom_valid`
- geometry status / H001 verification status
- label match status
- endpoint flag pattern
- matched-predicate hints
- posterior target fields

Hidden construction fields are stored in `object_endpoint_manifest_post_label_only.jsonl`
and must be joined only after label fill.

## Interpretation

이 단계는 posterior-ready 결과가 아니다. 하지만 이전보다 좋은 점은, 다음 label pool이
더 이상 단순 positive anchor가 아니라 object/endpoint shortcut을 통제하기 위한 cell에서
나왔다는 것이다.

`130`개는 plan의 `158`개보다 작다. 이 deficit은 row 부족만 의미하지 않는다. T1/T2/T3
cell 사이에 같은 후보가 겹치고, duplicate physical pair와 scan concentration을 줄이는
selection cap을 적용했기 때문에 생긴다. 따라서 다음 label fill 후 target-independence
audit에서 `130` rows가 충분하지 않으면, caps를 명시적으로 완화하거나 추가 cell을 다시
mining해야 한다.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/144_reliability_target_v3_object_endpoint_candidate_mining.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_candidate_mining.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_candidate_mining/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_candidate_mining/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_candidate_mining/object_endpoint_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_candidate_mining/object_endpoint_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_candidate_mining/selected_candidates_internal.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_candidate_mining/selection_status.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_candidate_mining/tier_summary.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_candidate_mining/v3_label_schema.json
```

## Next TODO

```text
reliability_target_v3_object_endpoint_label_fill
```

Goal:

- Fill the `130`-row object/endpoint-controlled v3 sheet.
- Treat the fill as hypothesis-stage Codex proxy unless a real human review is added.
- Do not use hidden manifest fields during label decisions.
- Ingest labels only after fill validation passes.
- Keep posterior smoke blocked until target-independence audit is rerun.
