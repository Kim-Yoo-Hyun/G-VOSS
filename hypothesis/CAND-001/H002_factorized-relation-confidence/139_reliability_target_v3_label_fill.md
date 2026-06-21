# H002 Reliability Target V3 Label Fill

Date: 2026-06-20 KST

## Answer To User Question

사용자가 직접 채워야 하는 단계는 아니다. 이번 단계에서는 Codex가 사용자 요청에 따라
160-row v3 sheet의 completion fields를 proxy로 채웠다.

단, 이 label은 독립 human annotation이 아니다. Hypothesis-stage train-only proxy label로만
취급하며, paper-level evidence나 final target으로 쓰려면 ingestion과 target-independence
audit을 먼저 통과해야 한다.

## Purpose

`reliability_target_v3_positive_anchor_plan`에서 만든 160-row sheet의 human fields를
채운다. 이 단계는 posterior smoke가 아니라 label completion 단계다.

## Boundary

- Split: Open3DSG train-only.
- Validation/test rows: not used.
- Posterior training: not run.
- H001 artifacts: not modified.
- Filled by: Codex proxy at user request.
- Actual independent human reviewer: no.
- Label decision input: labeler-visible identity fields and packet path availability.
- Hidden sampling category, expected role, source score/rank, `p_geom_valid`,
  `geometry_status`, `label_match_status`, and numeric witness values are not used for
  label decisions.
- Hidden manifest is joined only after fill for diagnostic bucket counts.

## Command

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_label_fill.py
```

## Result

```text
status = h002_reliability_target_v3_label_filled_codex_proxy_user_requested
rows = 160
reliable = 32
unreliable_geometry = 21
unreliable_trivial = 57
unreliable_ontology = 0
uncertain = 50
validation_errors = 0
validation_used = False
test_used = False
next = reliability_target_v3_label_ingestion
```

## V3 Axis Counts

Geometry support:

| Value | Count |
| --- | ---: |
| `supports_predicate` | 92 |
| `contradicts_predicate` | 21 |
| `ambiguous` | 47 |

Relation usefulness:

| Value | Count |
| --- | ---: |
| `informative` | 34 |
| `trivial_dense_or_room_structure` | 58 |
| `ontology_mismatch` | 21 |
| `uncertain` | 47 |

Relation reliability:

| Value | Count |
| --- | ---: |
| `reliable` | 32 |
| `unreliable_geometry` | 21 |
| `unreliable_trivial` | 57 |
| `unreliable_ontology` | 0 |
| `uncertain` | 50 |

## Post-Label Bucket Diagnostic

이 diagnostic은 label을 채운 뒤에만 hidden sampling bucket과 조인한 것이다. Label 결정을
할 때 hidden bucket을 사용하지 않았다.

| Hidden Sampling Bucket | Rows | Reliable | Unreliable Geometry | Unreliable Trivial | Uncertain |
| --- | ---: | ---: | ---: | ---: | ---: |
| `reliable_positive_anchor` | 40 | 7 | 0 | 8 | 25 |
| `geometry_contradiction_negative` | 40 | 1 | 18 | 14 | 7 |
| `trivial_dense_negative` | 40 | 10 | 3 | 19 | 8 |
| `ontology_or_uncertain_negative` | 40 | 14 | 0 | 16 | 10 |

Interpretation:

- Positive-anchor sampling은 label mass를 늘렸지만, visible-heuristic proxy fill 기준으로
  hidden positive-anchor bucket이 그대로 reliable positive가 되지는 않는다.
- 이 결과는 v3 ingestion과 target-independence audit이 반드시 필요하다는 점을 강화한다.
- 현재 artifact는 posterior-ready target이 아니라 v3 label completion artifact다.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/139_reliability_target_v3_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_fill_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_fill_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_fill_codex_proxy_user_requested/completed_v3_positive_anchor_label_sheet_codex_proxy_user_requested.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_fill_codex_proxy_user_requested/v3_proxy_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_fill_codex_proxy_user_requested/bucket_diagnostics_post_label_only.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_label_fill_codex_proxy_user_requested/fill_validation_errors.jsonl
```

## Next TODO

```text
reliability_target_v3_label_ingestion
```

다음 단계는 completed v3 sheet를 ingest하고, binary/multi-class target으로 derive 가능한지
검사하는 것이다. Posterior smoke는 ingestion과 target-independence audit 이후에만 진행한다.
