# H002 Reliability Target V4 Matched Contrast Label Fill

Date: 2026-06-21 KST

## Purpose

이 단계는 `158` row / `79` pair v4 matched-contrast label-ready sheet의 review fields를
visible-only 기준으로 채우는 단계다. Posterior smoke, ingestion, target-independence audit은
진행하지 않았다.

## Boundary

```text
split = train_only
validation_used = False
test_used = False
posterior_trained = False
posterior_smoke_allowed = False
paper_evidence_allowed = False
filled_by = codex_proxy
user_requested_proxy_fill = True
actual_user_reviewer = False
multi_view_as_model_input = False
```

Label decision에 사용하지 않은 field:

```text
hidden contrast role
matched pair id
semantic rank / semantic score
p_geom_valid
geometry_status
label_match_status
target-construction metadata
```

Hidden manifest는 label fill 이후 diagnostics에만 join했다.

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_label_fill.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_label_fill.py
```

## Result

```text
status = h002_reliability_target_v4_matched_contrast_label_filled_codex_proxy_user_requested
rows = 158
reliable = 23
unreliable = 24
uncertain = 111
binary target rows = 47
binary positive rows = 23
binary negative rows = 24
input validation errors = 0
fill validation errors = 0
validation_used = False
test_used = False
posterior_allowed = False
next = reliability_target_v4_matched_contrast_label_ingestion
```

## Label Counts

| Item | Count |
| --- | ---: |
| rows | 158 |
| label-ready pairs | 79 |
| reliable | 23 |
| unreliable | 24 |
| uncertain | 111 |
| binary usable rows | 47 |
| binary positive rows | 23 |
| binary negative rows | 24 |
| input validation errors | 0 |
| fill validation errors | 0 |

Family counts:

| Family | Rows |
| --- | ---: |
| `support_contact` | 90 |
| `relative_vertical` | 68 |

Geometry support:

| Geometry Support | Rows |
| --- | ---: |
| `supports` | 30 |
| `contradicts` | 17 |
| `ambiguous` | 111 |

Relation usefulness:

| Usefulness | Rows |
| --- | ---: |
| `useful_nontrivial` | 25 |
| `trivial_or_redundant` | 8 |
| `not_a_relation` | 17 |
| `uncertain` | 108 |

## Post-Label Diagnostics

Hidden role/source diagnostics were joined only after label lock.

| Hidden Group | Rows | Reliable | Unreliable | Uncertain |
| --- | ---: | ---: | ---: | ---: |
| `negative_proxy` / `HL` / `unsatisfied` | 79 | 11 | 14 | 54 |
| `positive_proxy` / `LH` / `satisfied` | 79 | 12 | 10 | 57 |
| `label_ready` rows | 139 | 23 | 24 | 92 |
| `limited_view_evaluable` rows | 19 | 0 | 0 | 19 |
| `existing_independent_asset_packet` | 5 | 5 | 0 | 0 |
| `generated_v4_matched_contrast_asset_packet` | 153 | 18 | 24 | 111 |

Pair-level diagnostics:

| Pair Pattern | Pairs |
| --- | ---: |
| `uncertain/uncertain` | 47 |
| `reliable/uncertain` | 10 |
| `unreliable/unreliable` | 8 |
| `uncertain/unreliable` | 7 |
| `reliable/reliable` | 6 |
| `reliable/unreliable` | 1 |

Interpretation:

- Binary usable mass is now balanced: `23` positive / `24` negative.
- However, `111/158` rows are uncertain, so this remains a conservative proxy label set.
- Matched role itself does not trivially determine the label: positive and negative proxy sides have similar label distribution.
- Pair-level contrast is weaker than expected because only `1/79` pair has a direct reliable/unreliable contrast under this conservative visible-only fill.
- Therefore this step creates labels for ingestion and audit, not posterior evidence.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/161_reliability_target_v4_matched_contrast_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/completed_v4_matched_contrast_label_sheet_codex_proxy_user_requested.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/v4_proxy_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/relation_reliability_v4_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/post_label_diagnostics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/pair_post_label_diagnostics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/input_validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested/fill_validation_errors.jsonl
```

## Next TODO

```text
reliability_target_v4_matched_contrast_label_ingestion
```

Goal:

- ingest v4 proxy labels into binary/multiclass target artifacts.
- verify binary target count and pair integrity.
- audit whether hidden role, source queue, rank band, object/family cells, or packet source explain labels.
- keep posterior smoke blocked unless target-independence audit passes.
