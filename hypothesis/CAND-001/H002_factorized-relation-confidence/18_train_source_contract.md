# H002 Train Source Contract

Last updated: 2026-06-12

## Purpose

`16_train_scope.md`와 `17_train_rga_seed.md`의 결론에 따라 H002의 다음
diagnostic은 validation set이 아니라 train set에서 수행한다. 이 문서는
Open3DSG train pilot RGA seed의 source contract를 고정한다.

핵심 원칙:

```text
H002 train diagnostic must not use H001 full_validation artifacts.
```

이번 단계에서 완료한 것은 source scope freeze와 adapter contract validation이다.
아직 Open3DSG train raw dump, train predictions, train geometry join, train RGA
diagnostic은 실행하지 않았다.

## Frozen Train Pilot

선택된 pilot:

```text
Open3DSG train pilot RGA seed
```

생성 도구:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/train_source_contract.py
```

실행 명령:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/train_source_contract.py \
  --repo-root . \
  --limit 100
```

출력 위치:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/
```

생성된 파일:

```text
source_contract.json
selected_scans.txt
selected_subgraphs.txt
pilot_contexts.jsonl
relationships_train_pilot.json
report.md
```

선택 결과:

| Item | Count |
| --- | ---: |
| train subset contexts | 3,852 |
| candidate train subgraphs | 3,738 |
| selected pilot subgraphs | 100 |
| selected scans | 100 |
| pilot subset contexts | 100 |

Primary relation-family coverage:

| Family | GT Relation Count In Pilot |
| --- | ---: |
| `proximity` | 476 |
| `relative_vertical` | 144 |
| `support_contact` | 433 |

Full family counts in the pilot:

| Family | Count |
| --- | ---: |
| `attachment_deferred` | 190 |
| `proximity` | 476 |
| `relative_horizontal` | 1,338 |
| `relative_vertical` | 144 |
| `support_contact` | 433 |
| `unsupported_first_pass` | 142 |

Status:

```text
ready
```

Blockers:

```text
none
```

## Selection Rule

Selection rule recorded in `source_contract.json`:

```text
train-only subgraphs with ready Open3DSG preprocess pickle, ready train view
pickle, at least one GT relationship, one subgraph per scan, greedy coverage
of support_contact/proximity/relative_vertical, then deterministic scan order
```

Rationale:

- train split only.
- no validation scan or H001 `full_validation` artifact is used.
- one subgraph per scan keeps the pilot broad rather than repeatedly sampling
  the same scan.
- `relationships_train_pilot.json` fixes the exact 100 subgraph contexts, so
  adapter/export stages do not silently expand from selected scans to all train
  subgraphs of those scans.
- unsupported relation families are retained for coverage accounting but are
  not part of the geometry-checkable denominator until a typed witness exists.

## Source Inputs

Read-only source inputs:

```text
local_dataset/3DSSG_subset/relationships_train.json
experiments/H001_geom_reliability/sources/open3dsg/train_preprocess/records.jsonl
experiments/H001_geom_reliability/sources/open3dsg/train_views/records.jsonl
```

These files are read as provenance. H002 does not modify H001 train or validation
artifacts.

## Adapter Contract Check

The Open3DSG adapter was run in `contract-only` mode against the pilot-only train
subset.

Command:

```bash
python3 experiments/H001_geom_reliability/scripts/export_open3dsg_predictions.py \
  --repo-root . \
  --raw-dump-jsonl hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/raw.jsonl \
  --subset-json hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/relationships_train_pilot.json \
  --relationships-file local_dataset/3DSSG_subset/relationships.txt \
  --selected-scans hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/selected_scans.txt \
  --output-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/adapter_contract \
  --split-name h002_train_open3dsg_pilot \
  --baseline-run-id open3dsg_train_pilot_pending \
  --contract-only
```

Result:

```text
status: adapter_contract_ready_raw_dump_missing
contexts: 100
raw_rows: 0
prediction_rows: 0
errors: 0
warnings: 0
```

Interpretation:

- The adapter can read exactly the 100 frozen train contexts.
- Prediction export is blocked only because the train raw dump has not been
  generated yet.
- This is a contract check, not H002 diagnostic evidence.

## Required Train Source Bundle

The next executable H002 diagnostic must create the following bundle under:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/
```

Required outputs:

```text
raw_dump/raw.jsonl
raw_dump/raw.completed.jsonl
raw_dump/stream_manifest.json
adapter/predictions.jsonl
adapter/manifest.json
geometry/verification.jsonl
geometry/manifest.json
rga/match_rows.jsonl
rga/train_rga_summary.json
rga/train_hl_queue.jsonl
rga/train_lh_queue.jsonl
rga/report.md
```

Minimum row-level identity fields:

```text
scan_id
subset_split_id
subgraph_id
edge.subject_id
edge.object_id
predicate.predicate_label
predicate.score or rank
geometry.geometry_validity_score
geometry.status
label_match_status
rga_bucket
```

## Command Sequence Contract

### Step 0: Freeze Train Pilot

Done in this document.

### Step 1: Generate Train Raw Dump

Required but not yet implemented.

Reason:

- Existing Open3DSG eval services in
  `experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml`
  target H001 validation runtime paths by default.
- H002 must not launch those services as-is for train diagnostics.
- A train-only Docker runner must stage or mount
  `relationships_train_pilot.json` into the Open3DSG runtime and write raw rows
  to the H002 train artifact path.

Required runtime contract:

```text
OPEN3DSG_RAW_DUMP_JSONL=/workspace/hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/raw.jsonl
OPEN3DSG_RAW_DUMP_COMPLETED_JSONL=/workspace/hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/raw.completed.jsonl
OPEN3DSG_RAW_DUMP_MANIFEST_JSON=/workspace/hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/stream_manifest.json
OPEN3DSG_BASELINE_RUN_ID=open3dsg_train_pilot_epoch13_step13104
OPEN3DSG_MODEL_SOURCE_STAGE=official_non_avg_blip_train_pilot
```

The runner must use:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/relationships_train_pilot.json
```

not:

```text
local_dataset/3DSSG_subset/relationships_validation.json
experiments/H001_geom_reliability/sources/open3dsg/full_validation/
```

### Step 2: Export Adapter Predictions

Run after raw dump exists:

```bash
python3 experiments/H001_geom_reliability/scripts/export_open3dsg_predictions.py \
  --repo-root . \
  --raw-dump-jsonl hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/raw_dump/raw.jsonl \
  --subset-json hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/relationships_train_pilot.json \
  --relationships-file local_dataset/3DSSG_subset/relationships.txt \
  --selected-scans hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/selected_scans.txt \
  --output-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/adapter \
  --split-name h002_train_open3dsg_pilot \
  --baseline-run-id open3dsg_train_pilot_epoch13_step13104
```

Expected:

```text
adapter/manifest.json status == ready
adapter/manifest.json counts.contexts == 100
adapter/predictions.jsonl exists and has > 0 rows
```

### Step 3: Join Geometry Evidence

Run after adapter predictions exist:

```bash
python3 hypothesis/CAND-001/H001_geometry-grounded-verification/tools/join_predictions.py \
  --predictions-jsonl hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/adapter/predictions.jsonl \
  --dataset-root local_dataset \
  --model-json hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_smoke/model.json \
  --output-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/geometry \
  --selected-scans hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/selected_scans.txt \
  --verification-policy point_subtype
```

Expected:

```text
geometry/verification.jsonl exists
geometry row count == adapter prediction row count
p_geom_valid remains geometry-only evidence
```

### Step 4: Build Train RGA Rows

Required but not yet implemented as a train-path runner.

The runner should join:

```text
adapter/predictions.jsonl
source_contract/relationships_train_pilot.json
geometry/verification.jsonl
```

and output:

```text
rga/match_rows.jsonl
rga/train_rga_summary.json
rga/train_hl_queue.jsonl
rga/train_lh_queue.jsonl
```

This step should reuse the H002 `RGA-HL/RGA-LH` definitions, but the source paths
must be parameterized instead of hardcoding H001 `full_validation` paths.

## Verification Commands

Source contract:

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path("hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract/source_contract.json")
m = json.loads(p.read_text())
assert m["status"] == "ready"
assert m["counts"]["selected_subgraphs"] == 100
assert m["counts"]["selected_scans"] == 100
assert m["blockers"] == []
print("source_contract_ok")
PY
```

Adapter contract:

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path("hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/adapter_contract/manifest.json")
m = json.loads(p.read_text())
assert m["status"] == "adapter_contract_ready_raw_dump_missing"
assert m["counts"]["contexts"] == 100
assert m["validation"]["errors"] == []
print("adapter_contract_ok")
PY
```

Anti-leak check:

```bash
rg -n "full_validation|relationships_validation" \
  hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/source_contract \
  hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/adapter_contract
```

Expected result:

```text
no validation path should appear in the train pilot source/adapter contract
```

## Current Boundary

What is established:

- H002 now has a fixed train-only Open3DSG pilot scope.
- The scope has 100 train subgraphs and covers all current H001 primary
  geometry-checkable families.
- The adapter contract sees exactly 100 contexts.

What is not established:

- no train raw Open3DSG semantic scores yet.
- no train `p_geom_valid` join yet.
- no train `RGA-HL/RGA-LH` result yet.
- no factorized reliability posterior result yet.

Therefore, H002 claims remain at the problem-definition/source-contract stage.

## Next TODO

Next document:

```text
19_train_raw_dump_runner.md
```

Required next work:

- define or add the Docker-based Open3DSG train pilot raw dump runner.
- make sure it uses `relationships_train_pilot.json`, not validation runtime
  data.
- generate `raw_dump/raw.jsonl` under the H002 train pilot artifact path.
- rerun adapter export without `--contract-only`.
