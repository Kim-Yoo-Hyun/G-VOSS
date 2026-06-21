# H002 Reliability Target V3 Object/Endpoint Label Fill

Date: 2026-06-20 KST

## Purpose

`144_reliability_target_v3_object_endpoint_candidate_mining.md`에서 만든 train-only
`130`-row object/endpoint-controlled v3 sheet를 hypothesis-stage proxy label로 채운다.

핵심 질문:

```text
After object/endpoint-controlled mining, does the v3 reliability label sheet
produce enough reliable / unreliable / uncertain supervision to justify
ingestion and target-independence audit?
```

## Boundary

- Split: Open3DSG train-only.
- Validation/test rows: not used.
- Posterior training/smoke: not run.
- Filled by Codex proxy at user request.
- This is not independent human annotation.
- H001 artifacts: not modified.
- Multi-view remains audit/label evidence only, not model input.
- Hidden manifest is joined only after label fill for diagnostics.

Label decision did not use:

- sampling tier/cell
- candidate proxy class
- source queue
- semantic score/rank
- `p_geom_valid`
- geometry status / H001 verification status
- label match status
- endpoint flag pattern
- matched predicate hints
- numeric witness values

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_label_fill.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_label_fill.py
```

Observed:

```text
status=h002_reliability_target_v3_object_endpoint_label_filled_codex_proxy_user_requested
rows=130
reliable=8
unreliable_geometry=26
unreliable_trivial=73
unreliable_ontology=0
uncertain=23
input_errors=0
errors=0
validation_used=False
test_used=False
posterior_allowed=False
next=reliability_target_v3_object_endpoint_label_ingestion
```

## Result

Status:

```text
h002_reliability_target_v3_object_endpoint_label_filled_codex_proxy_user_requested
```

Decision:

```text
Filled the object/endpoint-controlled v3 sheet as a user-requested Codex proxy.
This creates hypothesis-stage labels for ingestion and target-independence
audit, but it is not independent human evidence and does not unlock posterior
smoke by itself.
```

## Counts

| Item | Count |
| --- | ---: |
| rows | 130 |
| reliable | 8 |
| unreliable_geometry | 26 |
| unreliable_trivial | 73 |
| unreliable_ontology | 0 |
| uncertain | 23 |
| input validation errors | 0 |
| fill validation errors | 0 |

By family:

| Family | Rows |
| --- | ---: |
| `support_contact` | 77 |
| `relative_vertical` | 53 |

Geometry support:

| Geometry support | Count |
| --- | ---: |
| `supports_predicate` | 85 |
| `contradicts_predicate` | 26 |
| `ambiguous` | 19 |

Relation usefulness:

| Usefulness | Count |
| --- | ---: |
| `informative` | 10 |
| `trivial_dense_or_room_structure` | 75 |
| `ontology_mismatch` | 26 |
| `uncertain` | 19 |

## Post-Label Diagnostics

Tier-level counts:

| Tier | Rows | Reliable | Unreliable Geometry | Unreliable Trivial | Uncertain |
| --- | ---: | ---: | ---: | ---: | ---: |
| `T1_strict_subject_object_family` | 50 | 0 | 11 | 28 | 11 |
| `T2_object_family_fallback` | 31 | 2 | 5 | 20 | 4 |
| `T3_endpoint_family_balance` | 49 | 6 | 10 | 25 | 8 |

Proxy-stratum diagnostic counts:

| Proxy Stratum | Rows | Reliable | Unreliable Geometry | Unreliable Trivial | Uncertain |
| --- | ---: | ---: | ---: | ---: | ---: |
| candidate-positive proxy | 68 | 7 | 5 | 41 | 15 |
| candidate-negative proxy | 62 | 1 | 21 | 32 | 8 |

Important interpretation:

```text
supports_predicate != reliable
```

`85` rows support the geometric predicate, but only `8` rows are labeled reliable because
`75` rows are judged `trivial_dense_or_room_structure`. This is the expected separation
between geometry support and relation reliability, but it also means the resulting
binary reliability target may still be positive-sparse.

## Main Risk For Next Step

The next ingestion/audit must check:

- whether `8` reliable rows are enough for a relation reliability target,
- whether `unreliable_trivial` dominates the target too strongly,
- whether endpoint/object shortcut risk remains after label fill,
- whether geometry-support target and relation-reliability target should be audited separately,
- whether posterior smoke should remain blocked if no controlled slice exists.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/145_reliability_target_v3_object_endpoint_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_fill_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_fill_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_fill_codex_proxy_user_requested/completed_object_endpoint_label_sheet_codex_proxy_user_requested.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_fill_codex_proxy_user_requested/object_endpoint_v3_proxy_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_fill_codex_proxy_user_requested/post_label_diagnostics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_fill_codex_proxy_user_requested/fill_validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_label_fill_codex_proxy_user_requested/input_validation_errors.jsonl
```

## Next TODO

```text
reliability_target_v3_object_endpoint_label_ingestion
```

Goal:

- Ingest the 130 filled v3 rows.
- Derive reliability / geometry-support / usefulness binary targets.
- Keep review fields as target-only, not model input.
- Join hidden manifest only after label lock.
- Run target-independence audit before any posterior smoke.
