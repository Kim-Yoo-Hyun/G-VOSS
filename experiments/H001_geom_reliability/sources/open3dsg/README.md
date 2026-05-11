# Open3DSG Source

Open3DSG is the selected second-source expansion for the top-tier path.

Current status:

```text
dump_features_background_running_hardened
```

Plan artifact:

```text
checkpoint_reproduction_plan_ready_training_not_started
```

Docker env artifact:

```text
ready
```

Required before cross-source claims:

- explicit filtered train split coverage after completed `training_repro` payload staging
- validation split coverage guard before feature dump/training
- train/validation feature dump on the filtered runtime split
- official BLIP TopK5/scales3 full dump completion, or clearly marked reduced/pilot route only for checkpoint smoke
- trained or otherwise trusted Open3DSG checkpoint
- identity-preserving raw dump
- `open3dsg_ov` prediction JSONL export
- geometry join
- H001 metric table using the same suite as `VL-SAT`
- failure-analysis rows generated from the pre-locked schema under `failure_analysis/`

Current metric/join contract:

- status: `blocked_runtime_inputs_missing`
- artifacts: `metric_join_contract/{input_contract.json,output_contract.json,metrics.json,manifest.json,commands.md,report.md}`
- present input: H001 ground-truth JSONL, 7,505 rows
- missing required inputs: real Open3DSG prediction JSONL and geometry verification JSONL
- claim boundary: contract/blocked-input artifact only, not Open3DSG metric evidence

Current checkpoint selection template:

- status: `checkpoint_selection_template_ready_checkpoint_missing`
- artifacts: `checkpoint_selection/{selection_policy.json,record_template.json,manifest.json,commands.md,report.md}`
- candidate checkpoints: 0
- blockers: `no_checkpoint_candidates`, `official_feature_audit_not_ready:blocked`
- selection boundary: primary checkpoint selection must not use H001 held-out R@K, violation rate, failure-analysis distribution, or visual inspection of H001 held-out Open3DSG predictions
- route priority: official full route for paper-result evidence; official pilot for debugging/progress only; reduced route is smoke-only

Current raw-dump identity checklist:

- status: `raw_dump_identity_checklist_ready_raw_dump_missing`
- artifacts: `raw_dump_identity/{checklist.json,manifest.json,commands.md,report.md}`
- fixed H001 identity scope: 127 scans / 388 contexts / 25,916 directed pairs
- current blocker: missing real raw dump at `raw_dump/raw.jsonl`
- required before adapter/metric: raw rows must preserve scan id, subset split, subgraph id, subject id, object id, predicate labels, and finite predicate scores

Current metric-scope policy:

- status: `metric_scope_policy_ready_no_metric_execution`
- artifacts: `metric_scope/{predicate_mapping.json,denominator_policy.json,manifest.json,commands.md,report.md}`
- in-scope target families: `support_contact`, `proximity`, `relative_vertical`
- in-scope GT denominator: 2,545 rows
- target-family GT counts: support_contact 1,199, proximity 1,128, relative_vertical 218
- excluded families remain reportable as caveats but are not H001 geometry-checkable metric denominator
- recall matching remains predicate-label exact; family grouping is for verifier/violation reporting, not label collapsing

Current Table 6 hook:

- status: `blocked_until_open3dsg_metrics_ready`
- artifact: `table6_hook.json`
- ready gate: `metrics.json` status must be `ready`, condition metrics must be nonempty, blockers must be empty, and `metric_scope` must be ready
- current blocker surfaced in Table 6: missing real Open3DSG prediction JSONL and geometry verification JSONL

Design tightening review:

- keep checkpoint provenance and checkpoint-selection records frozen before pilot/full training outputs are inspected
- raw-dump identity audit is now frozen before converting Open3DSG raw outputs to H001 prediction JSONL
- Open3DSG predicate-family mapping and filtered-denominator caveat are now frozen before real metric execution
- keep Qwen-VL and SceneFun3D/FunGraph3D as separate extension tracks unless the main paper question is rewritten

Current post-dump handoff:

- status: `waiting_for_feature_dump_completion`
- feature progress at last Docker handoff generation: 1131/3900 complete feature ids, 29.00%
- artifacts: `post_dump_handoff/{manifest.json,commands.md,report.md}`
- rule: run `feature_audit` first after the official dump completes; do not run `train_pilot` until that audit reports `ready`

Heavy training commands are guarded by `open3dsg_training_preflight.py`.
`dump_features_3rscan`, `train_pilot`, and `train_full` fail before Open3DSG execution unless the official payload, runtime train/validation split view/preprocess coverage, writable runtime directories, source entrypoint, and Docker import/CUDA gates are ready. The runtime train and validation splits are explicitly filtered after non-recoverable preprocess drops.

Current guard result:

- `dump_features_3rscan`: protected Docker command now uses `OPEN3DSG_LAZY_DATASET=1`, pre-forward skip-existing resume, deterministic no-shuffle feature iteration, `workers=0`, explicit `--epochs 1`, no-grad dump patch, stable official feature run dir, and `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`
- `dump_features_3rscan_pilot`: reduced `--mini_dataset`, TopK1/scales1 route for checkpoint smoke only; not paper-result evidence
- `train_pilot`: blocked until official feature outputs pass audit; `--load_features` points to the stable `clip_features_h001_official_blip_top5_scales3` run dir
- `train_pilot_reduced`: reduced checkpoint-smoke route only; not paper-result evidence
- `train_full`: blocked until official pilot/feature outputs exist
- source entrypoint gate: passed (`open3dsg/scripts/run.py` exists)
- Docker import/CUDA gate: passed (`torch 2.8.0+cu128`, CUDA visible, device count 1, RTX 5090 `sm_120` supported)
- artifacts: `training_preflight/{dump_features,train_pilot,train_full}.{json,md}`

Current train staging smoke:

- `train_views_audit`: 0/1178 ready before generation
- `train_views_smoke`: generated one scan view pickle
- `train_preprocess_smoke`: generated and then confirmed the matching scan view pickle and 7/7 train subgraph pickles for that scan
- current train view coverage: 1178/1178
- current train preprocessed coverage before filtering: 3744/3852 ready, 108 missing outputs across 101 scans
- recoverability audit: the full preprocess log has 108 `too few visible objects, scene missalignment possible` drops, matching the 108 manifest missing IDs; a representative Docker retry did not recover sampled missing targets
- explicit runtime train filter: retained 1158 scans / 3744 subgraphs / 79,704 relations; removed 108 subgraphs / 1,486 relations and 20 removed-only scans from the runtime train split
- validation view/preprocess guard: views 30/30, runtime validation split 30 scans / 156 subgraphs / 3,696 relations
- protected `dump_features_3rscan` status: previous run was interrupted after confirming feature writing because the command needed stronger runtime policy; retained partial feature files are under `output/features/clip_features_h001_official_blip_top5_scales3`
- current official feature partial: Docker `open3dsg_post_dump_handoff` last recorded 1131/3900 complete feature ids, 29.00%, and status `waiting_for_feature_dump_completion`
- artifacts: `train_views/{manifest.json,records.jsonl,report.md}`, `train_preprocess/{manifest.json,records.jsonl,report.md}`, `train_preprocess_retry/{manifest.json,records.jsonl,report.md}`, and `train_preprocess_filter/{manifest.json,missing.jsonl,removed.jsonl,report.md}`

Current eval preflight:

- status: `blocked`
- blocker: `missing_checkpoint_env:OPEN3DSG_CHECKPOINT`
- runtime/scope/import gates: passed
- H001 eval scope: 127 selected scans / 388 contexts
- raw-dump contract: `contract_ready_raw_dump_missing` for `raw_dump/raw.jsonl`
- artifacts: `eval_preflight/{manifest.json,raw_dump_contract.json,report.md}`

Current model/cache preflight:

- status: `ready_with_cache_warnings`
- local model files: passed (`blip2_positional_embedding.pt`, `pointnet.pth`, `pointnet2_ulip.pt`, `openseg/saved_model.pb`)
- Docker imports: passed (`torch`, `transformers`, `tensorflow`, `clip`, `open_clip`)
- disk budget: passed (`601GB` free at last check, minimum `300GB`)
- remaining warnings: only `torch_hub` cache is empty; HF `Salesforce/instructblip-vicuna-7b` is detected under current `HF_HOME`
- artifact: `cache_preflight/{manifest.json,report.md}`

Run the lightweight Docker planner from the repository root:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_plan'
```

Stage the leakage-guarded `training_repro` root:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_train_root'
```

Current `training_repro` result:

- official train metadata staged: 1178 scans / 3852 subgraphs / 81,190 relations
- train-dev split excludes H001 held-out scans: 30 scans / 160 subgraphs / 3,749 relations
- H001 held-out overlap in train/train-dev: 0 / 0
- current train scan dirs ready: 1178 / 1178
- current train-dev scan dirs ready: 30 / 30
- current train mesh/texture ready: 1178 / 1178
- current train sequence extracted: 1178 / 1178
- status: `training_repro_staged_root_ready_for_view_preprocess`

Current Docker env result:

- image: `h001-open3dsg-repro:cu128`
- CUDA visible: `True`
- CUDA device count: `1`
- torch: `2.8.0+cu128`
- detail: `env_check.md`

Run train view/preprocess staging after smoke:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_views_full'
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_preprocess_full'
```

Apply the explicit filtered train split if the staged runtime split is reset:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm train_preprocess_filter'
```

Prepare the training handoff contract:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_train_handoff'
```

Run the model/cache preflight:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm cache_preflight'
```

Run the eval preflight after a checkpoint exists:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/output/checkpoints/<checkpoint>.ckpt docker compose -f experiments/H001_geom_reliability/sources/open3dsg/compose.open3dsg.yaml run --rm eval_preflight'
```

Prepare the Open3DSG prediction adapter contract before raw dump exists:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_adapter_contract'
```

Run the adapter smoke test without a real Open3DSG checkpoint raw dump:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_adapter_smoke'
```

Current adapter result:

- contract status: `adapter_contract_ready_raw_dump_missing`
- smoke status: `ready`
- smoke counts: 388 contexts, 1 synthetic raw row, 2 prediction rows, zero errors/warnings
- artifacts: `adapter/{manifest.json,raw_schema_example.json,report.md}` and `adapter_smoke/{manifest.json,raw_smoke.jsonl,predictions.jsonl,report.md}`

Freeze the failure-analysis schema before Open3DSG metrics exist:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_failure_schema'
```

Current failure-analysis schema result:

- status: `failure_analysis_schema_ready_no_metric_run`
- scope: schema/taxonomy/aggregation plan only, no Open3DSG metric inspection
- artifacts: `failure_analysis/{schema.json,taxonomy.json,aggregation_plan.json,example.jsonl,manifest.json,report.md}`

Validate the failure-analysis row generator skeleton with synthetic rows only:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_failure_generator_smoke'
```

Current failure-analysis generator smoke result:

- status: `failure_analysis_generator_smoke_ready_no_metric_inspection`
- scope: synthetic row generation and locked schema validation only, no Open3DSG metric inspection
- counts: 6 synthetic rows across 6 primary categories, 0 validation errors
- artifacts: `failure_analysis_generator_smoke/{rows.jsonl,summary.json,manifest.json,report.md}`

Convert an identity-preserving raw dump after it exists:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_adapter_raw_dump'
```

Audit or run resumable 3RScan payload batches:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_payload --repo-root /workspace'
```

Small pilot download/extract batch:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_payload --repo-root /workspace --download-missing --extract-sequence --limit 1 --workers 2'
```

Continue with a resumable batch:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_payload --repo-root /workspace --download-missing --extract-sequence --limit 20 --workers 4 --timeout 300 --retries 1'
```
