# H002 Full-Train Independent Support/Vertical V2 External Review Ingestion

## Purpose

`103_full_train_independent_support_vertical_v2_external_review_fill.md`에서 채운
external review sheet를 ingest하여 external targets를 만들었다.

핵심 질문:

```text
Does the revised external review surface produce usable geometry/reliability
targets before posterior smoke?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- external review fields는 target/audit only이며 posterior input이 아니다.
- hidden manifest는 label lock 이후 audit에만 join한다.
- labels are Codex proxy external review fields pending user confirmation.
- paper-level external human annotation claim은 아직 금지한다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_ingestion.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_external_review_ingested_with_basic_probe_risk
labels=127
geom_binary=116
geom_pos=105
geom_neg=11
rel_binary=116
rel_pos=47
rel_neg=69
errors=0
validation_used=False
test_used=False
next=external_evidence_review_target_independence_audit
```

## Target Counts

| Target | Binary Rows | Positive | Negative | Positive Rate | Excluded |
| --- | ---: | ---: | ---: | ---: | ---: |
| `geometry_validity_external_target` | 116 | 105 | 11 | 0.9052 | 11 |
| `relation_reliability_external_target` | 116 | 47 | 69 | 0.4052 | 11 |

Relation reliability by family:

| Family | Positive | Negative |
| --- | ---: | ---: |
| `relative_vertical` | 20 | 26 |
| `support_contact` | 27 | 43 |

Relation reliability by predicate:

| Predicate | Positive | Negative |
| --- | ---: | ---: |
| `higher than` | 8 | 12 |
| `lower than` | 12 | 14 |
| `lying on` | 14 | 19 |
| `standing on` | 3 | 14 |
| `supported by` | 10 | 10 |

## Basic Probe

| Target | Probe Status | Hidden Risks | Visible Non-Target Shortcuts |
| --- | --- | ---: | ---: |
| `geometry_validity_external_target` | `target_independence_risk_hidden_metadata_correlated` | 8 | 3 |
| `relation_reliability_external_target` | `target_independence_risk_hidden_metadata_correlated` | 5 | 0 |

Interpretation:

- External review ingestion은 성공했고 error는 0이다.
- `relation_reliability_external_target`은 116 binary rows, 47 positive / 69 negative로
  이전 human-proxy target보다 usable row 수가 늘었다.
- visible non-target shortcut은 relation reliability에서 0으로 줄었다.
- 하지만 hidden metadata correlation risk가 여전히 5개 남아 있어 posterior smoke는 아직
  열지 않는다.
- 다음 단계는 dedicated target-independence audit이다.

## Target Derivation

`geometry_validity_external_target`:

- positive: visual 또는 mesh answer가 predicate를 support하고, 다른 modality가 명확히
  contradict하지 않는 경우.
- negative: visual 또는 mesh answer가 predicate를 contradict하고, support modality가 없는
  경우.
- exclude: endpoint invalid/unclear, visual-mesh disagreement, insufficient evidence,
  uncertain.

`relation_reliability_external_target`:

- positive: endpoint valid, geometry positive, relation informative, final reliability
  `reliable`.
- negative: final reliability `unreliable`, endpoint invalid, geometry contradicts,
  ontology mismatch, trivial dense/room-structure relation.
- exclude: final reliability `uncertain` 또는 ambiguous contract.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/104_full_train_independent_support_vertical_v2_external_review_ingestion.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_ingestion_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_ingestion_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_ingestion_codex_proxy_user_requested/validated_external_review_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_ingestion_codex_proxy_user_requested/geometry_validity_external_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_ingestion_codex_proxy_user_requested/relation_reliability_external_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_ingestion_codex_proxy_user_requested/geometry_validity_external_posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_ingestion_codex_proxy_user_requested/relation_reliability_external_posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_ingestion_codex_proxy_user_requested/excluded_external_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_ingestion_codex_proxy_user_requested/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_ingestion_codex_proxy_user_requested/target_group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_ingestion_codex_proxy_user_requested/shortcut_audit.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_ingestion_codex_proxy_user_requested/ingestion_errors.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_ingestion.py
```

Line counts:

```text
validated_external_review_labels.jsonl = 127
geometry_validity_external_targets.jsonl = 116
relation_reliability_external_targets.jsonl = 116
excluded_external_targets.jsonl = 22
ingestion_errors.jsonl = 0
```

## Next TODO

Completed by:

```text
105_full_train_independent_support_vertical_v2_external_review_target_independence_audit
```

Goal:

- The dedicated target-independence audit was completed in
  `105_full_train_independent_support_vertical_v2_external_review_target_independence_audit.md`.
- Current active next action is `revise_external_review_or_collect_true_user_labels`.
