# H002 Full Train Scope Contract

Last updated: 2026-06-15

## Purpose

`52_rga_main_framing.md`의 결정에 따라 H002를 Open3DSG train pilot에서 full train
scope로 확장하기 전에 source scope, row identity, artifact path, execution boundary를
고정한다.

핵심 결정:

```text
full_train_expansion_before_validation
```

이 문서는 실행 결과가 아니라 full-train 실행 전 contract다.

## Scope Decision

Full train scope name:

```text
open3dsg_train_full
```

Scope definition:

```text
All train-origin Open3DSG-ready 3DSSG subset contexts that satisfy:
1. source split = relationships_train.json
2. Open3DSG train preprocess record is valid
3. Open3DSG train view record is valid
4. GT relationship_count > 0
5. corresponding relationships_train.json context exists
```

Expected initial count, recomputed from the pilot source-contract manifest:

| Item | Count |
| --- | ---: |
| official train subset contexts | 3,852 |
| ready candidate train contexts | 3,738 |
| dropped: preprocess not ready | 108 |
| dropped: no relationship | 6 |
| train view-ready scans | 1,178 |

Important:

```text
The above counts are planning counts from the existing pilot manifest.
The full-train source contract must recompute them at execution time and store
input hashes.
```

## Non-Negotiable Boundary

Forbidden inputs:

```text
relationships_validation.json
relationships_test.json
H001 full_validation artifacts
validation/test raw dumps
validation/test adapter predictions
validation/test geometry rows
validation/test RGA rows
```

Allowed read-only provenance inputs:

```text
local_dataset/3DSSG_subset/relationships_train.json
experiments/H001_geom_reliability/sources/open3dsg/train_preprocess/records.jsonl
experiments/H001_geom_reliability/sources/open3dsg/train_views/records.jsonl
local_dataset/Open3DSG_staged/training_repro/output/features/clip_features_h001_official_blip_top5_scales3/
local_dataset/3RScan/scans/
```

Allowed H001 reuse:

- H001 train-side Open3DSG preprocess/view readiness records as read-only source
  provenance.
- H001 geometry joiner code and frozen geometry-only `p_geom_valid` model as
  read-only tools.
- H001 Open3DSG adapter export script as a source-format converter.

Not allowed:

```text
Do not modify H001 artifacts, H001 experiment results, or H001 validation
runtime roots while generating H002 full-train artifacts.
```

## Artifact Root

Full-train artifacts must not overwrite the pilot root.

Pilot root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/
```

Full-train root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/
```

Required subdirectories:

```text
source_contract/
runtime_stage/
preflight/
raw_dump/
adapter/
geometry/
rga/
audit/
```

Runtime root:

```text
local_dataset/Open3DSG_staged/h002_train_full_runtime
```

Compose file:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/compose.open3dsg_train_full.yaml
```

## Source Contract Files

The source contract stage must write:

```text
source_contract/source_contract.json
source_contract/selected_scans.txt
source_contract/selected_subgraphs.txt
source_contract/train_contexts.jsonl
source_contract/relationships_train_full.json
source_contract/report.md
```

Contract status:

```text
ready only if selected contexts == all ready train contexts
```

Required manifest fields:

```text
schema_version
created_at
status
scope_id = open3dsg_train_full
selection_mode = all_ready_train_contexts
inputs with sha256
outputs
counts
family_counts
drop_reasons
blockers
claim_boundary
```

Required count fields:

```text
official_train_subset_contexts
ready_candidate_contexts
selected_contexts
selected_scans
dropped_preprocess_not_ready
dropped_view_not_ready
dropped_no_relationship
dropped_missing_subset_entry
```

## Row Identity Contract

Every downstream row must preserve this identity:

```text
source_id
scope_id
scan_id
subset_split_id
subgraph_id
prediction_id
subject_id
object_id
predicate_label
predicate_family
semantic_rank_in_subgraph
semantic_score_raw
semantic_score_norm
geometry_status
p_geom_valid
coverage_state
uncertainty_state
label_match_status
provenance
```

Required provenance checks:

```text
subset_source == relationships_train_full.json
split_name == h002_train_open3dsg_full
source_id == open3dsg_train_full
scope_id == open3dsg_train_full_ready_contexts
posterior_edge_valid is null before posterior smoke
no path contains full_validation
no path contains relationships_validation except inside isolated runtime adapter
```

Runtime caveat:

```text
Open3DSG upstream --test reads validation filenames. H002 may stage
relationships_train_full.json as runtime relationships_validation.json inside
the isolated h002_train_full_runtime only. The provenance owner remains
relationships_train_full.json.
```

## Existing Script Reuse Decision

### `train_source_contract.py`

Status:

```text
not reusable as-is for full train
```

Reason:

- current script is pilot-specific.
- default output path is `open3dsg_train_pilot/source_contract`.
- manifest uses `pilot_name = open3dsg_train_pilot`.
- selection rule chooses one representative subgraph per scan.
- full train requires all ready train contexts, not one subgraph per scan.

Required change:

```text
Add or create a full-train source contract runner with:
--scope-id open3dsg_train_full
--selection-mode all_ready_train_contexts
--out-dir artifacts/train_rga_full/open3dsg_train_full/source_contract
```

### `stage_train_raw_dump_runtime.py`

Status:

```text
concept reusable, but path contract must be parameterized
```

Reusable parts:

- isolated runtime root.
- train subset staged into Open3DSG eval path.
- empty train/test runtime files to prevent accidental expansion.
- read-only links to source, preprocessed data, views, features, and raw scans.
- feature gate.

Required change:

```text
Accept full-train contract filenames:
train_contexts.jsonl
relationships_train_full.json
```

and write to:

```text
local_dataset/Open3DSG_staged/h002_train_full_runtime
artifacts/train_rga_full/open3dsg_train_full/runtime_stage/
```

### `compose.open3dsg_train_pilot.yaml`

Status:

```text
clone and parameterize
```

Required full-train compose:

```text
compose.open3dsg_train_full.yaml
```

Required changes:

- `OPEN3DSG_BASE = h002_train_full_runtime`
- raw dump output paths under `train_rga_full/open3dsg_train_full/raw_dump`
- preflight output under `train_rga_full/open3dsg_train_full/preflight`
- selected scans path from full-train source contract
- subset JSON path from `relationships_train_full.json`
- expected contexts from full-train source contract count
- log/session names use `h002_open3dsg_train_full_*`

### Raw Repair, Adapter, Provenance Fix

Reusable with explicit arguments:

```text
repair_open3dsg_raw_dump.py
experiments/H001_geom_reliability/scripts/export_open3dsg_predictions.py
fix_adapter_provenance.py
```

Required full-train arguments:

```text
--raw-dump-jsonl artifacts/train_rga_full/open3dsg_train_full/raw_dump/raw.jsonl
--out-jsonl artifacts/train_rga_full/open3dsg_train_full/raw_dump/raw.dedup.jsonl
--subset-json artifacts/train_rga_full/open3dsg_train_full/source_contract/relationships_train_full.json
--selected-scans artifacts/train_rga_full/open3dsg_train_full/source_contract/selected_scans.txt
--output-dir artifacts/train_rga_full/open3dsg_train_full/adapter
--split-name h002_train_open3dsg_full
--baseline-run-id open3dsg_train_full_epoch13_step13104
--subset-source artifacts/train_rga_full/open3dsg_train_full/source_contract/relationships_train_full.json
```

### Geometry Join

Reusable command family:

```text
hypothesis/CAND-001/H001_geometry-grounded-verification/tools/join_predictions.py
```

Required full-train outputs:

```text
artifacts/train_rga_full/open3dsg_train_full/geometry/verification.jsonl
artifacts/train_rga_full/open3dsg_train_full/geometry/manifest.json
artifacts/train_rga_full/open3dsg_train_full/geometry/report.md
artifacts/train_rga_full/open3dsg_train_full/geometry/h002_summary.json
```

Boundary:

```text
p_geom_valid remains geometry-only validity evidence.
It is not H002 relation reliability posterior.
```

### `train_rga_rows.py`

Status:

```text
mostly reusable, but provenance wording and source-contract fields must be
generalized before full-train run.
```

Required change:

- accept `relationships_train_full.json`.
- accept `source_contract.counts.selected_contexts` or
  `source_contract.counts.ready_candidate_contexts`.
- set `source_id = open3dsg_train_full`.
- set `scope_id = open3dsg_train_full_ready_contexts`.
- replace pilot-specific provenance text with train-full wording.

## Expected Scale

Pilot scale:

| Item | Count |
| --- | ---: |
| contexts | 100 |
| raw rows before dedup | 4,626 |
| adapter prediction rows | 118,560 |
| geometry-checkable rows | 27,360 |

Full-train planning scale:

```text
ready candidate contexts ~= 3,738
estimated adapter prediction rows ~= 4.4M if pilot average holds
```

This estimate is not a claim. It is used to plan runtime, storage, and logs.

Implications:

- raw dump must run as resumable tmux/background job.
- geometry join can be long-running and should write logs.
- row-level JSONL artifacts remain ignored runtime artifacts.
- summary/report files must record row counts and blockers.

## Execution Gates

### Gate 1. Source Contract

Pass criteria:

```text
status = ready
selection_mode = all_ready_train_contexts
selected_contexts == ready_candidate_contexts
relationships_train_full.json exists
input hashes recorded
no validation/test source path
```

### Gate 2. Runtime Stage And Preflight

Pass criteria:

```text
runtime root = h002_train_full_runtime
feature missing contexts = 0 or explicitly blocked before raw dump
expected contexts == selected_contexts
Open3DSG import/checkpoint preflight passes
```

### Gate 3. Raw Dump

Pass criteria:

```text
stream_manifest.status = raw_dump_stream_complete
completed_batches == selected_contexts
raw rows > 0
exit code = 0 preferred
```

If exit code is nonzero after complete stream finalization, record it as a
runtime caveat and do not continue until row completeness is independently
verified.

### Gate 4. Adapter Export

Pass criteria:

```text
adapter status = ready
duplicate_prediction_ids = 0 after repair if needed
prediction rows > 0
subset_source = relationships_train_full.json
split_name = h002_train_open3dsg_full
```

### Gate 5. Geometry Join

Pass criteria:

```text
prediction rows == verification rows
prediction_id_mismatches = 0
p_geom_valid non-null for geometry-checkable families
unsupported families retained for coverage accounting
```

### Gate 6. Full-Train RGA Rows

Pass criteria:

```text
match_rows written
validation_error_count = 0
validation/full_validation provenance matches = 0
posterior_edge_valid non-null rows = 0
RGA-HL/RGA-LH tables written
family/status/label-axis tables written
```

No posterior model training starts before Gate 6 passes.

## Full-Train Outputs Required Before Posterior

```text
source_contract/source_contract.json
source_contract/relationships_train_full.json
raw_dump/stream_manifest.json
raw_dump/raw.dedup.jsonl
adapter/manifest.json
adapter/predictions.jsonl
geometry/manifest.json
geometry/verification.jsonl
rga/train_rga_summary.json
rga/match_rows.jsonl
rga/report.md
```

Minimum report tables:

- full-train context count and scan count.
- family distribution in GT.
- prediction family distribution.
- geometry status by family.
- label status by family.
- `RGA-HL@50`, `RGA-HL@100`.
- `RGA-LH-tail@50`, `RGA-LH-tail@100`.
- coverage/uncertainty/missing/unsupported rates.
- top scans by row count to detect scan dominance.

## Decision

Current status:

```text
full_train_scope_contract_ready_no_execution
```

Meaning:

```text
The full-train H002 expansion scope is defined, but no full-train source
contract, runtime, raw dump, geometry join, RGA rows, labels, or posterior
smoke have been executed yet.
```

## Next TODO

Next document:

```text
54_full_train_source_runner.md
```

Goal:

- implement or parameterize the full-train source contract runner.
- create the full-train source contract under
  `artifacts/train_rga_full/open3dsg_train_full/source_contract/`.
- decide whether runtime staging and compose can be cloned safely after the
  source contract passes.
- keep validation/test unavailable.
