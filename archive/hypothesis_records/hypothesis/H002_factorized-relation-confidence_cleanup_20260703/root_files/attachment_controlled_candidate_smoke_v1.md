# H002 Attachment Controlled Candidate Smoke V1

Date: 2026-06-25 KST

## Purpose

`attachment_controlled_candidates_v1`의 `400` rows를 대상으로 controlled smoke를 실행한다.
목표는 다음 두 질문을 분리해서 확인하는 것이다.

```text
1. T_e + G_e가 source/rank/endpoint shortcut보다 attachment compatibility를 잘 설명하는가?
2. target이 hidden construction proxy에 의해 너무 직접적으로 결정되는가?
```

## Runner

Command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_controlled_candidate_smoke_v1.py
```

Output:

```text
artifacts/attachment_controlled_candidate_smoke_v1/
```

## Dataset

```text
candidate_rows = 400
Task A primary compatibility rows = 320
Task A positive / negative = 160 / 160
connected diagnostic rows = 80
validation_errors = 0
```

Task A uses only:

```text
attached to
hanging on
```

`connected to` remains diagnostic and is not used as primary binary compatibility.

## Task A Metrics

| Model | AUROC | AUPRC | F1@0.5 |
| --- | ---: | ---: | ---: |
| `M1_source_only_Z` | 0.4585 | 0.4711 | 0.4522 |
| `M2_semantic_source_TZ` | 0.4798 | 0.4912 | 0.4228 |
| `M3_geometry_only_G` | 1.0000 | 1.0000 | 1.0000 |
| `M4_compatibility_TG` | 1.0000 | 1.0000 | 1.0000 |
| `M5_factorized_TZGQ` | 1.0000 | 1.0000 | 1.0000 |
| `S1_predicate_family_shortcut` | 0.4876 | 0.4981 | 0.5356 |
| `S2_source_rank_shortcut` | 0.4908 | 0.4928 | 0.4620 |
| `S3_endpoint_label_pair_shortcut` | 0.5074 | 0.5233 | 0.4514 |
| `H0_hidden_cell_only_probe` | 1.0000 | 1.0000 | 1.0000 |
| `H1_hidden_construction_probe` | 1.0000 | 1.0000 | 1.0000 |
| `H2_hidden_geometry_status_probe` | 0.7620 | 0.8189 | 0.7452 |

## Gate Result

```text
dataset_sanity = pass
compatibility_signal = pass
geometry_signal = pass
endpoint_shortcut_control = pass
hidden_proxy_audit = fail
overall = attachment_controlled_candidate_smoke_promising_but_hidden_proxy_dominates
```

## Interpretation

Positive result:

```text
G-only AUROC = 1.0000
T+G AUROC = 1.0000
source-only AUROC = 0.4585
predicate/family shortcut AUROC = 0.4876
source-rank shortcut AUROC = 0.4908
endpoint-label-pair shortcut AUROC = 0.5074
```

This means the target is not explained by source confidence, rank, predicate frequency, or endpoint
label-pair identity. The numeric `G_e` axis is carrying the signal.

Blocker:

```text
hidden cell probe AUROC = 1.0000
hidden construction probe AUROC = 1.0000
```

This means the current binary target is still a geometry-proxy construction target, not an
independent human/audit reliability target. In other words, the smoke proves that the geometry
features reproduce the current proxy, but it does not yet prove that the proxy is an independent
relation reliability label.

## Decision

Do not promote this directly as paper evidence.

The correct next step is a path decision:

```text
attachment_controlled_candidate_path_decision_v1
```

That decision should choose between:

- using this as a geometry-pretraining/compatibility-proxy dataset;
- adding visual/mesh/human audit confirmation for a subset;
- mining a harder target where hidden construction cells do not define the label;
- merging only the feature schema, not the current proxy labels, into the combined H002 prototype.

## Boundary

- train-only hypothesis smoke;
- no validation/test usage;
- no paper model training;
- hidden probes are audit controls only;
- current result is diagnostic, not paper-level evidence.

