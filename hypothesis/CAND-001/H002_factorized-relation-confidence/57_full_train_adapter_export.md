# H002 Full Train Adapter Export

Last updated: 2026-06-16

## Purpose

`56_full_train_raw_dump.md`에서 완료된 full-train raw dump를 H002/RGA가 사용할 수
있는 identity-preserving prediction row contract로 변환한다.

이번 단계의 목표:

- repaired raw dump인 `raw.dedup.jsonl`을 사용한다.
- train-origin source contract의 provenance를 유지한다.
- 기존 pilot exporter의 list-in-memory 구조를 full-train에 그대로 쓰지 않는다.
- subgraph-local rank를 보존하면서 full-train prediction rows를 streaming export한다.

## Tool Update

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/export_full_train_adapter.py
```

Reason:

```text
The existing Open3DSG adapter materializes all prediction rows in memory before
assigning ranks. Full train expands to about 4.8M prediction rows, so H002 uses
a streaming exporter that buffers only one contiguous subgraph at a time.
```

The exporter writes the train subset source directly:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/source_contract/relationships_train_full.json
```

No separate provenance fix is needed for this full-train export.

## Command

Syntax check:

```bash
python3 -m py_compile \
  hypothesis/CAND-001/H002_factorized-relation-confidence/tools/export_full_train_adapter.py \
  hypothesis/CAND-001/H002_factorized-relation-confidence/tools/repair_open3dsg_raw_dump.py \
  hypothesis/CAND-001/H002_factorized-relation-confidence/tools/fix_adapter_provenance.py
```

Export:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/export_full_train_adapter.py \
  --repo-root .
```

## Result

Current status:

```text
full_train_adapter_export_ready
```

Manifest:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/adapter/manifest.json
```

Output prediction file:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/adapter/predictions.jsonl
```

Counts:

| Item | Count |
| --- | ---: |
| contexts | 3,738 |
| raw rows read | 186,139 |
| prediction rows written | 4,818,996 |
| subgraphs written | 3,738 |
| relationship labels | 27 |
| errors | 0 |
| warnings | 793 |

Warning breakdown:

| Warning | Count |
| --- | ---: |
| `raw_edge_outside_context_filtered` | 786 |
| `same_endpoint_skipped` | 7 |

These warnings are adapter-contract filters, not conversion errors.

Family prediction rows:

| Family | Rows |
| --- | ---: |
| `support_contact` | 556,038 |
| `proximity` | 185,346 |
| `relative_vertical` | 370,692 |
| `relative_horizontal` | 741,384 |
| `attachment_deferred` | 556,038 |
| `unsupported_first_pass` | 2,409,498 |

Verification:

```text
wc -l predictions.jsonl = 4,818,996
no predictions.jsonl.tmp remains
rg relationships_validation/h001_validation in predictions.jsonl = no match
manifest.status = ready
manifest.validation.errors.total = 0
```

Disk note:

```text
predictions.jsonl size = 7.3G
filesystem free space after export = about 43G
```

## Boundary

Established:

- full-train Open3DSG semantic source predictions are exported.
- row identity includes scan/subgraph/subject/object/predicate/rank.
- provenance points to `relationships_train_full.json`.
- validation/test rows are still closed.
- output is hypothesis-stage evidence, not paper-level experiment evidence.

Not established:

- full-train geometry join.
- full-train RGA bucket distribution.
- full-train controlled labels.
- posterior improvement over semantic/geometry baselines.

## Next TODO

Next step:

```text
full_train_geometry_join
```

Goal:

- join `adapter/predictions.jsonl` with train-origin geometry evidence.
- preserve all 4,818,996 prediction rows.
- produce H002 geometry status mapping: `satisfied`, `unsatisfied`, `uncertain`,
  `unsupported`, `missing`.
- record `p_geom_valid` as geometry-only continuous evidence.
- keep validation/test unavailable.
