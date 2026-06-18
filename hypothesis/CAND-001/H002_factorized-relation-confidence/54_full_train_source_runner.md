# H002 Full Train Source Runner

Last updated: 2026-06-15

## Purpose

`53_full_train_scope_contract.md`에서 정의한 full-train source scope를 실제
source-contract artifact로 생성한다.

이번 단계의 목표:

- all-ready train contexts를 선택하는 full-train source runner를 만든다.
- pilot artifact root를 덮지 않고 full-train root에 contract를 생성한다.
- train-only provenance, input hash, drop reason, family counts를 고정한다.
- validation/test를 열지 않는다.

## Added Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_source_contract.py
```

Reason:

```text
train_source_contract.py is pilot-specific and selects one representative
subgraph per scan. Full train requires all ready train contexts.
```

New runner behavior:

```text
selection_mode = all_ready_train_contexts
scope_id = open3dsg_train_full
source_id = open3dsg_train_full
```

It selects every train-origin context satisfying:

1. source file is `relationships_train.json`.
2. Open3DSG train preprocess record is valid.
3. Open3DSG train view record is valid.
4. GT relationship count is greater than zero.
5. matching `relationships_train.json` entry exists.

## Command

Syntax check:

```bash
python3 -m py_compile \
  hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_source_contract.py
```

Source contract generation:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_source_contract.py \
  --repo-root .
```

Result:

```text
status = ready
selected_contexts = 3,738
selected_scans = 1,157
```

## Output Artifacts

Output root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/source_contract/
```

Files:

```text
source_contract.json
selected_scans.txt
selected_subgraphs.txt
train_contexts.jsonl
relationships_train_full.json
report.md
```

Line counts:

| File | Rows |
| --- | ---: |
| `selected_scans.txt` | 1,157 |
| `selected_subgraphs.txt` | 3,738 |
| `train_contexts.jsonl` | 3,738 |

## Manifest Summary

Status:

```text
ready
```

Counts:

| Item | Count |
| --- | ---: |
| official train subset contexts | 3,852 |
| preprocess records | 3,852 |
| ready candidate contexts | 3,738 |
| selected contexts | 3,738 |
| selected subgraphs | 3,738 |
| selected scans | 1,157 |
| selected relationships | 79,704 |
| dropped preprocess-not-ready | 108 |
| dropped view-not-ready | 0 |
| dropped no-relationship | 6 |
| dropped missing-subset-entry | 0 |

Family counts in selected train contexts:

| Family | GT relations |
| --- | ---: |
| `support_contact` | 12,600 |
| `proximity` | 12,300 |
| `relative_vertical` | 3,552 |
| `relative_horizontal` | 36,944 |
| `attachment_deferred` | 8,767 |
| `unsupported_first_pass` | 5,541 |

Primary family coverage:

| Family | GT relations |
| --- | ---: |
| `support_contact` | 12,600 |
| `proximity` | 12,300 |
| `relative_vertical` | 3,552 |

Blockers:

```text
none
```

## Validation Checks

Input readiness:

```text
relationships_train.json: ready
train_preprocess records: ready
train_views records: ready
```

Contract checks:

```text
selection_mode = all_ready_train_contexts
selected_contexts == ready_candidate_contexts
blockers = []
validation_or_test_rows_used = false
h001_heldout_artifacts_used = false
```

Path-string check:

```bash
rg -n "full_validation|relationships_validation|relationships_test" \
  hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/source_contract
```

Result:

```text
no match
```

This confirms that the source-contract artifact itself does not refer to
validation/test split files. The later runtime staging may write
`relationships_train_full.json` into an isolated Open3DSG runtime file named
`relationships_validation.json`, but only because upstream Open3DSG `--test`
expects validation filenames.

## Boundary

Established:

- full-train source scope exists.
- all ready train contexts are selected.
- input hashes and drop reasons are recorded.
- H002 pilot root is untouched.
- validation/test rows are not used.

Not established:

- full-train runtime staging.
- full-train Open3DSG raw dump.
- adapter export.
- geometry join.
- RGA rows.
- audit labels.
- posterior smoke.

This is source-contract evidence only.

## Runtime Decision

Now that the source contract passes, runtime staging and compose can be cloned
from the pilot path, but only after parameterization.

Required next changes:

- create or parameterize full-train runtime staging to read
  `train_contexts.jsonl` and `relationships_train_full.json`.
- write into `local_dataset/Open3DSG_staged/h002_train_full_runtime`.
- write runtime manifests under
  `artifacts/train_rga_full/open3dsg_train_full/runtime_stage/`.
- create `compose.open3dsg_train_full.yaml`.
- set expected contexts to `3,738`.
- preserve train-only provenance even though Open3DSG runtime uses validation
  filenames internally.

## Decision

Current status:

```text
full_train_source_contract_ready
```

Meaning:

```text
H002 full-train source selection is ready. The next step is runtime staging and
preflight, not posterior modeling.
```

## Next TODO

Next document:

```text
55_full_train_runtime_stage.md
```

Goal:

- implement or parameterize the full-train runtime staging tool.
- create `compose.open3dsg_train_full.yaml`.
- run full-train runtime staging and Docker preflight if feasible.
- keep validation/test unavailable.
