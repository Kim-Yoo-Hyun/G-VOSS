# Reliability Target V3 Informative Anchor Label Fill

Date: 2026-06-20 KST

## Purpose

`151_reliability_target_v3_informative_anchor_asset_packets.md`에서 준비한 full `160`-row
packet-complete informative-anchor label sheet를 hypothesis-stage proxy label로 채운다.

핵심 질문:

```text
Does the informative-anchor full label sheet produce enough reliable / typed-negative
/ uncertain supervision to justify label ingestion and target-independence audit?
```

## Boundary

- Split: Open3DSG train only.
- Validation/test row는 사용하지 않았다.
- Posterior training/smoke는 수행하지 않았다.
- Filled by Codex proxy at user request.
- This is not independent human annotation.
- H001 artifact는 수정하지 않았다.
- Multi-view/mesh packet은 audit/label evidence일 뿐, model input이 아니다.
- Hidden manifest는 label fill 이후 diagnostics에만 조인했다.

Label decision did not use:

- anchor category / sampling category
- expected proxy role
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
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_label_fill.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_label_fill.py
```

Observed:

```text
status=h002_reliability_target_v3_informative_anchor_label_filled_codex_proxy_user_requested
rows=160
reliable=35
unreliable_geometry=13
unreliable_trivial=34
unreliable_ontology=0
uncertain=78
input_errors=0
errors=0
validation_used=False
test_used=False
posterior_allowed=False
next=reliability_target_v3_informative_anchor_label_ingestion
```

## Result

Status:

```text
h002_reliability_target_v3_informative_anchor_label_filled_codex_proxy_user_requested
```

Decision:

```text
Filled the full 160-row informative-anchor v3 sheet as a user-requested Codex
proxy. This creates hypothesis-stage labels for ingestion and target-independence
audit, but it is not independent human evidence and does not unlock posterior
smoke by itself.
```

## Counts

| Item | Count |
| --- | ---: |
| rows | 160 |
| reliable | 35 |
| unreliable_geometry | 13 |
| unreliable_trivial | 34 |
| unreliable_ontology | 0 |
| uncertain | 78 |
| input validation errors | 0 |
| fill validation errors | 0 |

By family:

| Family | Rows |
| --- | ---: |
| `relative_vertical` | 84 |
| `support_contact` | 76 |

Geometry support:

| Geometry support | Count |
| --- | ---: |
| `supports_predicate` | 72 |
| `contradicts_predicate` | 13 |
| `ambiguous` | 75 |

Relation usefulness:

| Usefulness | Count |
| --- | ---: |
| `informative` | 37 |
| `trivial_dense_or_room_structure` | 35 |
| `ontology_mismatch` | 13 |
| `uncertain` | 75 |

## Post-Label Diagnostics

Anchor-category diagnostic counts:

| Anchor Category | Rows | Reliable | Unreliable Geometry | Unreliable Trivial | Uncertain |
| --- | ---: | ---: | ---: | ---: | ---: |
| `informative_reliable_positive_proxy` | 40 | 32 | 0 | 0 | 8 |
| `geometry_contradiction_negative_proxy` | 40 | 1 | 13 | 18 | 8 |
| `trivial_room_surface_negative_proxy` | 40 | 2 | 0 | 16 | 22 |
| `uncertain_or_ontology_negative_proxy` | 40 | 0 | 0 | 0 | 40 |

Packet-source diagnostic counts:

| Packet Source | Rows | Reliable | Unreliable Geometry | Unreliable Trivial | Uncertain |
| --- | ---: | ---: | ---: | ---: | ---: |
| `existing_independent_asset_packet` | 126 | 35 | 13 | 34 | 44 |
| `generated_informative_anchor_asset_packet` | 34 | 0 | 0 | 0 | 34 |

Important interpretation:

```text
supports_predicate != reliable
```

`72` rows support the predicate geometrically, but only `35` rows are labeled reliable because
`34` rows are trivial room/surface relations and `78` rows remain uncertain. This preserves H002's
core distinction between geometry support and relation reliability.

## Main Risk For Next Step

The next ingestion/audit must check:

- whether `35` reliable rows and typed negatives are enough for a binary reliability target,
- whether `uncertain=78` makes the target too sparse after binary derivation,
- whether anchor category or packet source explains the target too directly,
- whether generated asset packet rows being `34/34 uncertain` creates packet-source confounding,
- whether same-family / endpoint / rank-band / geometry-status controlled slices exist,
- whether posterior smoke should remain blocked if no controlled slice passes.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/152_reliability_target_v3_informative_anchor_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/completed_informative_anchor_label_sheet_codex_proxy_user_requested.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/informative_anchor_v3_proxy_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/post_label_diagnostics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/fill_validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested/input_validation_errors.jsonl
```

## Next TODO

```text
reliability_target_v3_informative_anchor_label_ingestion
```

Goal:

- Ingest the 160 filled v3 rows.
- Derive reliability / geometry-support / usefulness binary targets.
- Keep review fields as target-only, not model input.
- Join hidden manifest only after label lock.
- Audit target independence before any posterior smoke.
