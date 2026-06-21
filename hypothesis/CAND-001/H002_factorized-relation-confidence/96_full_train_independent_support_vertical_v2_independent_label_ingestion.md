# H002 Full-Train Independent Support/Vertical V2 Independent Label Ingestion

## Purpose

`95_full_train_independent_support_vertical_v2_independent_label_fill.md`에서
채운 `(codex_independent_ver)` visible-only labels를 label-locked target artifact로
ingest했다. 이번 단계의 목적은 independent geometry validity target과 relation
reliability target을 분리해 만들고, posterior smoke로 넘어가기 전 basic target
independence risk를 확인하는 것이다.

핵심 질문:

```text
Can the independent visible-only labels be materialized as train-only targets
without using hidden strata, v2 Codex axes, semantic score/rank, p_geom_valid, or
multi-view as model input?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- label fill 단계에서는 hidden manifest를 읽지 않았고, ingestion에서만 label lock 이후
  hidden strata를 audit metadata로 join한다.
- independent label fields, hidden strata, v2 reference axes는 target/audit 용도이며
  posterior input이 아니다.
- source score/rank와 `p_geom_valid`는 이번 target-path manifest에 포함되지 않는다.
  posterior smoke가 허용되려면 별도 post-label feature join이 필요하다.
- multi-view/mesh packet path는 audit evidence pointer일 뿐 model input이 아니다.
- label source는 `codex_independent_support_vertical_visible_only_bootstrap`이며,
  human-confirmed paper evidence가 아니다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_label_ingestion.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_independent_label_ingested_with_basic_probe_risk
validation_used=False
test_used=False
labels=127
geom_binary=102
geom_pos=81
geom_neg=21
rel_binary=102
rel_pos=32
rel_neg=70
errors=0
next=full_train_independent_support_vertical_v2_independent_target_independence_audit
```

## Target Counts

| Target | Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `geometry_validity_independent_target` | 102 | 81 | 21 | 0.7941 | 25 |
| `relation_reliability_independent_target` | 102 | 32 | 70 | 0.3137 | 25 |

Family breakdown:

| Target | Family | Positive | Negative |
| --- | --- | ---: | ---: |
| `geometry_validity_independent_target` | `relative_vertical` | 38 | 8 |
| `geometry_validity_independent_target` | `support_contact` | 43 | 13 |
| `relation_reliability_independent_target` | `relative_vertical` | 22 | 24 |
| `relation_reliability_independent_target` | `support_contact` | 10 | 46 |

## Basic Probe

Basic post-label probe는 target-independence 통과가 아니라 빠른 risk check다. 결과는
아직 posterior smoke로 갈 수 없다는 쪽이다.

| Target | Probe Status | Hidden Risks | Visible Non-Target Shortcuts |
| --- | --- | ---: | ---: |
| `geometry_validity_independent_target` | `target_independence_risk_hidden_metadata_correlated` | 6 | 1 |
| `relation_reliability_independent_target` | `target_independence_risk_hidden_metadata_correlated` | 7 | 1 |

Top hidden risks:

| Target | Hidden Key | Majority Acc | NMI | Pos Rate Range |
| --- | --- | ---: | ---: | ---: |
| `geometry_validity_independent_target` | `relation_validity_label_hidden` | 0.8627 | 0.4491 | 1.0000 |
| `geometry_validity_independent_target` | `label_use_hidden` | 0.7941 | 0.3069 | 0.4269 |
| `geometry_validity_independent_target` | `posterior_target_y_hidden` | 0.7941 | 0.3069 | 0.4269 |
| `relation_reliability_independent_target` | `relation_validity_label_hidden` | 0.7451 | 0.3166 | 0.6250 |
| `relation_reliability_independent_target` | `label_use_hidden` | 0.7353 | 0.3052 | 0.5216 |
| `relation_reliability_independent_target` | `posterior_target_y_hidden` | 0.7353 | 0.3052 | 0.5216 |

Visible shortcut note:

- `geometry_validity_independent_target`는 `predicate_label`에서 shortcut flag가 있다.
- `relation_reliability_independent_target`는 `evidence_packet_status`에서 boundary
  threshold 수준의 shortcut flag가 있다.

## Interpretation

좋아진 점:

- independent labels가 127 rows 모두 ingest됐다.
- geometry validity와 relation reliability target이 분리됐다.
- ingestion error는 0이다.
- validation/test leakage는 없다.
- hidden manifest join은 label lock 이후에만 수행됐다.

하지만 아직 posterior smoke로 가지 않는다.

이유:

- independent label이 human-confirmed가 아니다.
- labeler-visible raw witness surface가 v2 Codex target과 유사한 결정을 만들 수 있다.
- hidden prior-label/construction metadata와 target 사이의 correlation이 basic probe에서
  여전히 보인다.
- source score/rank와 `p_geom_valid` feature join은 pending 상태다.

따라서 이번 단계는 target materialization에는 성공했지만, method validation target으로
쓰기 전 dedicated target-independence audit이 필요하다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/96_full_train_independent_support_vertical_v2_independent_label_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_ingestion_codex_independent_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_ingestion_codex_independent_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_ingestion_codex_independent_ver/validated_independent_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_ingestion_codex_independent_ver/geometry_validity_independent_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_ingestion_codex_independent_ver/relation_reliability_independent_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_ingestion_codex_independent_ver/geometry_validity_independent_posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_ingestion_codex_independent_ver/relation_reliability_independent_posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_ingestion_codex_independent_ver/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_ingestion_codex_independent_ver/shortcut_audit.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_ingestion_codex_independent_ver/target_group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_independent_label_ingestion_codex_independent_ver/ingestion_errors.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_label_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_independent_label_ingestion.py
```

Line counts:

```text
validated_independent_labels.jsonl = 127
geometry_validity_independent_targets.jsonl = 102
relation_reliability_independent_targets.jsonl = 102
geometry_validity_independent_posterior_rows.jsonl = 102
relation_reliability_independent_posterior_rows.jsonl = 102
excluded_independent_targets.jsonl = 50
ingestion_errors.jsonl = 0
shortcut_audit.csv = 23
target_group_table.csv = 79
```

## Next TODO

Completed by:

```text
97_full_train_independent_support_vertical_v2_independent_target_independence_audit.md
```

Current next action:

```text
revise_independent_target_or_collect_human_confirmed_support_vertical_labels
```

Goal:

- decide whether to stop Codex-derived target revision and collect human-confirmed labels.
- define the minimum human-confirmed support/vertical subset needed for relation reliability.
- keep posterior smoke blocked until strict relation-reliability target evidence exists.
- keep source-score feature join pending until target independence is defensible.
