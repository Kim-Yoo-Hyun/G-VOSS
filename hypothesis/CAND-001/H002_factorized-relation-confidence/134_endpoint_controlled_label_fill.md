# Endpoint-Controlled Label Fill

Date: 2026-06-20 KST

## Purpose

이 단계는 `133_endpoint_controlled_asset_packets.md`에서 준비한 packet-ready
`62`-row endpoint-controlled label sheet를 채우는 것이다.

목적은 posterior 성능을 주장하는 것이 아니라, endpoint-controlled target repair
batch를 ingestion과 target-independence audit 단계로 넘길 수 있는 filled label
artifact를 만드는 것이다.

## Boundary

- Split: Open3DSG train only.
- Validation/test row는 사용하지 않았다.
- 새 posterior model은 학습하지 않았다.
- Codex proxy fill이며, 실제 paper-level external human annotation이 아니다.
- Hidden endpoint/sampling manifest를 읽지 않았다.
- Source score/rank, `p_geom_valid`, geometry status, numeric witness values를 읽지 않았다.
- Multi-view/mesh packet은 label evidence이며 posterior input이 아니다.
- H001 artifact는 수정하지 않았다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_label_fill.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_label_fill.py
```

Observed:

```text
status = h002_endpoint_controlled_label_fill_ready_for_ingestion
rows = 62
reliable = 2
unreliable = 32
uncertain = 28
validation_errors = 0
validation_used = False
test_used = False
next = endpoint_controlled_label_ingestion
```

## Counts

Family:

| Family | Rows |
| --- | ---: |
| `support_contact` | 37 |
| `relative_vertical` | 25 |

Final relation reliability:

| Label | Rows |
| --- | ---: |
| `reliable` | 2 |
| `unreliable` | 32 |
| `uncertain` | 28 |

Visual/mesh geometry answer:

| Answer | Rows |
| --- | ---: |
| `supports_predicate` | 23 |
| `contradicts_predicate` | 11 |
| `uncertain` | 28 |

Informativeness:

| Label | Rows |
| --- | ---: |
| `informative` | 2 |
| `ontology_mismatch` | 11 |
| `trivial_dense_or_room_structure` | 21 |
| `uncertain` | 28 |

## Interpretation

The fill completed cleanly at the schema level, but the resulting binary-positive
mass is very small:

```text
reliable = 2 / 62
```

This is important. Endpoint-controlled packet readiness solved the evidence
availability blocker, but the visible-only Codex proxy fill does not yet provide
a balanced or clearly usable posterior target. The correct next step is still
ingestion plus target-independence audit, not posterior smoke.

Possible outcomes after ingestion:

- If uncertain rows can be handled with a justified abstain/soft-label protocol,
  the batch may still be useful for diagnostic auditing.
- If binary target remains only `2` positives, it is likely insufficient for
  method-validation posterior smoke.
- If target-independence audit shows shortcut/endpoint carryover, the current
  filled labels should be treated as a failure diagnosis rather than method evidence.

## Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/134_endpoint_controlled_label_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_label_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_fill_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_fill_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_fill_codex_proxy_user_requested/completed_endpoint_controlled_label_sheet_codex_proxy_user_requested.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_fill_codex_proxy_user_requested/endpoint_controlled_proxy_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_fill_codex_proxy_user_requested/fill_validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_label_fill_codex_proxy_user_requested/endpoint_controlled_fill_schema.json
```

## Next TODO

```text
endpoint_controlled_label_ingestion
```

Required next action:

- Ingest the `62` filled endpoint-controlled labels.
- Derive binary/abstain target policy explicitly.
- Run target-independence audit before any posterior smoke.
- Keep posterior smoke blocked if the binary target remains too positive-sparse or shortcut-driven.
