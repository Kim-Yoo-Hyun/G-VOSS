# Open3DSG Source

Open3DSG is the selected second-source expansion for the top-tier path.

Current status:

```text
open3dsg_second_source_metrics_ready
```

Current caveat-reduction plan:

- status: `open3dsg_caveat_reduction_plan_frozen_r1_running`
- artifacts: `caveat_reduction_plan/{manifest.json,retry_plan.json,commands.md,report.md}`
- frozen order: R1 exact non-averaged BLIP route retry, R2 H001 covered-loadable context retry toward `388/388`, R3 attachment G5d only after Open3DSG caveat-reduction decisions are resolved or explicitly waived
- current decomposition for attachment impact: Open3DSG missing exact-label GT rows 199 total, with 23 tied to missing preprocessed H001 contexts and 176 tied to absent Open3DSG candidate pairs
- interpretation: non-avg BLIP and `388/388` success would strengthen Open3DSG source credibility, but they do not by themselves make `attachment_deferred_G5d` successful

Current R1 non-averaged BLIP retry:

- status: `launched_running`
- launched at: `2026-06-01 07:19:08 KST`
- tmux: `h001_open3dsg_train_full_nonavg_retry_20260601_071908`
- log: `logs/open3dsg_train_full_nonavg_retry_20260601_071908.log`
- exit file: `logs/open3dsg_train_full_nonavg_retry_20260601_071908.exit`
- run record: `train_pilot/full_nonavg_retry_20260601_071908.md`
- initial evidence: preflight passed, training entered epoch 0, and Open3DSG args show `avg_blip_emb=False`
- latest check: `2026-06-01 19:40 KST`, tmux active, no exit file, epoch 15 at about 595/3744 steps, best current train-dev checkpoint `epoch=13-step=13104.ckpt` with `val/loss=0.5724539161`, run size about 7.5G, disk free about 56G, and no OOM/traceback/no-space error found in the checked log tail
- boundary: not paper evidence unless the retry completes, checkpoint selection is refreshed, and the full H001 downstream Open3DSG chain is regenerated under separate non-avg output paths

Plan artifact:

```text
checkpoint_reproduction_plan_ready_training_not_started
```

Docker env artifact:

```text
ready
```

Required before broad cross-source claims:

- explicit filtered train split coverage after completed `training_repro` payload staging
- validation split coverage guard before feature dump/training
- train/validation feature dump on the filtered runtime split
- official BLIP TopK5/scales3 full dump completion, or clearly marked reduced/pilot route only for checkpoint smoke
- trained or otherwise trusted Open3DSG checkpoint: complete with averaged-BLIP variant caveat
- identity-preserving raw dump: complete, with clean v14 streaming source-process provenance
- streaming raw-dump source rerun: complete via same-path v14 resume, exit `0`, 377/377 completed batches, 19,162 rows, SHA256 matching `raw_dump/raw.jsonl`
- `open3dsg_ov` prediction JSONL export: complete
- geometry join: complete
- H001 metric table using the same suite as `VL-SAT`: complete
- failure-analysis rows generated from the pre-locked schema under `failure_rows/`: complete
- qualitative failure-case sample from high-severity visual-audit rows: complete
- qualitative failure-case inspection from sampled queue: complete
- paper-facing caveat wording: complete

Current metric/join contract:

- status: `ready_runtime_inputs_present_contract_only`
- artifacts: `metric_join_contract/{input_contract.json,output_contract.json,metrics.json,manifest.json,commands.md,report.md}`
- present inputs: Open3DSG prediction JSONL 496,600 rows; H001 ground-truth JSONL 7,505 rows; geometry verification JSONL 496,600 rows
- missing required inputs: none
- claim boundary: contract artifact only; real metrics live under `metrics/{metrics.json,report.md}`

Current checkpoint selection template:

- status: `checkpoint_selection_ready_labeled_avg_blip_variant`
- artifacts: `checkpoint_selection/{selection_policy.json,record_template.json,manifest.json,commands.md,report.md}`
- candidate checkpoints: 8
- selected checkpoint: `local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt`
- selected source stage: `avg_blip_full_variant`
- selection signal: Open3DSG train-dev `val/loss` 0.32881081104278564 at step 13103
- blockers: none
- selection boundary: primary checkpoint selection must not use H001 held-out R@K, violation rate, failure-analysis distribution, or visual inspection of H001 held-out Open3DSG predictions
- claim limitation: this is an explicitly labeled averaged-BLIP Open3DSG variant, not the exact non-averaged BLIP projector route

Current raw-dump identity checklist:

- status: `raw_dump_identity_audit_ready`
- artifacts: `raw_dump_identity/{checklist.json,manifest.json,commands.md,report.md}`
- fixed H001 identity scope: 127 scans / 388 contexts / 25,916 directed pairs
- raw dump: `raw_dump/raw.jsonl`, 19,162 rows
- clean source-process provenance: v14 streaming same-path resume `h001_open3dsg_eval_stream_raw_dump_resume_20260519_103227` exited `0`; manifest status `raw_dump_stream_complete`, 377/377 completed batches, 19,162 rows, dropped/invalid partial rows 0/0
- identity check: `raw_stream_retry_20260519_092628.jsonl` SHA256 matches canonical `raw_dump/raw.jsonl` exactly (`7072c77939a84f8739671025534cf09d5b834c507efad22fec3e3172e46ed2c2`)
- historical run records: v12 wrote the canonical raw dump then exited `137`; v13 and early v14 attempts also exited `137`; these are retained as run records but are superseded by the clean streaming resume for final provenance wording

Current metric-scope policy:

- status: `metric_scope_policy_ready_no_metric_execution`
- artifacts: `metric_scope/{predicate_mapping.json,denominator_policy.json,manifest.json,commands.md,report.md}`
- in-scope target families: `support_contact`, `proximity`, `relative_vertical`
- in-scope GT denominator: 2,545 rows
- target-family GT counts: support_contact 1,199, proximity 1,128, relative_vertical 218
- excluded families remain reportable as caveats but are not H001 geometry-checkable metric denominator
- recall matching remains predicate-label exact; family grouping is for verifier/violation reporting, not label collapsing

Current Table 6 hook:

- status: `ready`
- artifact: `table6_hook.json`
- ready gate: `metrics.json` status must be `ready`, condition metrics must be nonempty, blockers must be empty, and `metric_scope` must be ready
- current blocker surfaced in Table 6: none
- key Open3DSG metrics: semantic_only R@50/R@100 `0.3945/0.4963`, Violation@50/@100 `0.1326/0.1195`; probabilistic_recalibrated R@50/R@100 `0.3843/0.5580`, Violation@50/@100 `0.0575/0.0803`; rule_verified_point_subtype R@50/R@100 `0.4149/0.5238`, Violation@50/@100 `0.0/0.0`

Design tightening review:

- keep checkpoint provenance and checkpoint-selection records frozen before pilot/full training outputs are inspected
- raw-dump identity audit is now frozen before converting Open3DSG raw outputs to H001 prediction JSONL
- Open3DSG predicate-family mapping and filtered-denominator caveat are now frozen before real metric execution
- keep Qwen-VL and SceneFun3D/FunGraph3D as separate extension tracks unless the main paper question is rewritten

Current post-dump handoff:

- status: `completed`
- official feature dump: Docker `feature_audit` passed with 3900/3900 complete feature ids
- avg-BLIP full training: completed, selected checkpoint `epoch=13-step=13104.ckpt`
- H001 eval feature cache: completed for covered loadable scope, 377/377 complete feature ids and 1,131 `.pt` files
- raw dump and metric transition: raw dump identity, adapter, geometry join, metric eval, Table 6, real failure rows, qualitative case queue, and qualitative inspection are ready
- artifacts: `post_dump_handoff/{manifest.json,commands.md,report.md}`
- rule: run `feature_audit` first after the official dump completes; do not run `train_pilot` until that audit reports `ready`

Heavy training commands are guarded by `open3dsg_training_preflight.py`.
`dump_features_3rscan`, `train_pilot`, and `train_full` fail before Open3DSG execution unless the official payload, runtime train/validation split view/preprocess coverage, writable runtime directories, source entrypoint, and Docker import/CUDA gates are ready. The runtime train and validation splits are explicitly filtered after non-recoverable preprocess drops.

Current guard result:

- `dump_features_3rscan`: protected Docker command now uses `OPEN3DSG_LAZY_DATASET=1`, pre-forward skip-existing resume, deterministic no-shuffle feature iteration, `workers=0`, explicit `--epochs 1`, no-grad dump patch, stable official feature run dir, chunked BLIP embedding, and `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:128`
- `dump_features_3rscan_pilot`: reduced `--mini_dataset`, TopK1/scales1 route for checkpoint smoke only; not paper-result evidence
- `train_pilot`: non-averaged BLIP projector route is OOM-blocked and kept only as a limitation record
- `train_pilot_reduced`: reduced checkpoint-smoke route only; not paper-result evidence
- `train_full`: non-averaged BLIP projector route was previously OOM-blocked; R1 retry is now running under a 22GB free-memory GPU gate and has reached epoch 15, while `train_full_avg_blip` remains the currently selected completed checkpoint route until R1 finishes and checkpoint selection/downstream regeneration are complete
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
- protected `dump_features_3rscan` status: completed; Docker `feature_audit` passed with 3900/3900 complete feature ids under `output/features/clip_features_h001_official_blip_top5_scales3`
- current official feature partial: 3352/3900 complete feature ids, 85.95%, at the latest status check
- artifacts: `train_views/{manifest.json,records.jsonl,report.md}`, `train_preprocess/{manifest.json,records.jsonl,report.md}`, `train_preprocess_retry/{manifest.json,records.jsonl,report.md}`, and `train_preprocess_filter/{manifest.json,missing.jsonl,removed.jsonl,report.md}`

Current eval preflight:

- status: `ready`
- checkpoint: selected avg-BLIP variant checkpoint above
- runtime/scope/import gates: passed
- H001 eval scope: 127 selected scans / 388 contexts
- raw-dump contract: `contract_ready_raw_dump_missing` for `raw_dump/raw.jsonl`
- artifacts: `eval_preflight/{manifest.json,raw_dump_contract.json,report.md}`

Current raw dump run:

- first run status: `failed_false_positive_zero_length_dataloader`
- first run result: exit code `0`, but `raw_dump/raw.jsonl` was missing
- first run blocker: staged H001 runtime preprocess pickles used `numpy._core` paths that could not be unpickled by the Open3DSG Docker image with `numpy==1.23.3`; Lightning therefore saw a zero-length test DataLoader
- fix: source patch schema `h001_open3dsg_source_patch_v7` installs a NumPy pickle compatibility alias in `open_dataset.py`
- Docker load sanity after fix: 377/388 H001 eval contexts load; the remaining 11 are the known missing-preprocess caveat
- NumPy retry status: `failed_missing_h001_eval_features`
- NumPy retry result: exit code `1`, no `raw_dump/raw.jsonl`
- NumPy retry blocker: `OPEN3DSG_FEATURE_LOAD_DIR` pointed to the official `training_repro` feature dump, which does not contain H001 held-out eval feature ids
- feature-ready run status: `failed_shared_memory_after_full_test_loop`
- feature-ready run result: exit code `1`, test loop reached `388/388`, no `raw_dump/raw.jsonl`
- feature-ready blocker: Docker shared-memory / worker transfer failure, `RuntimeError: unable to write to file </torch_...>: No space left on device (28)` followed by `DataLoader worker ... Bus error`
- SHM retry status: `failed_dtype_mismatch`
- SHM retry result: exit code `1`, shared-memory failure mitigated, no `raw_dump/raw.jsonl`
- SHM retry blocker: avg-BLIP relationship generation passed float relationship image embeddings into bfloat16 InstructBLIP weights
- source patch dtype fix: schema `h001_open3dsg_source_patch_v11` casts relationship image embeddings to the loaded BLIP model dtype before `BLIP.generate_caption`
- dtype retry status: `failed_generation_length_validation`
- dtype retry result: exit code `1`, dtype mismatch mitigated, no `raw_dump/raw.jsonl`
- dtype retry blocker: current Transformers rejected legacy `max_length=20` generation after prompt/input embedding handling
- source patch generation fix: schema `h001_open3dsg_source_patch_v12` switches the BLIP relationship generation call to `max_new_tokens`, default `OPEN3DSG_BLIP_GENERATE_MAX_NEW_TOKENS=20`
- current retry status: `raw_dump_written_exit_137`
- current retry mitigation: compose `shm_size: 16gb`, `OPEN3DSG_EVAL_WORKERS=0`, source patch v12 BLIP dtype alignment, and BLIP `max_new_tokens` generation
- current retry tmux: `h001_open3dsg_eval_avg_blip_retry_generate`
- current retry log: `logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_generate_20260518_171846.log`
- current retry exit file: `logs/open3dsg_eval_h001_gt_objects_avg_blip_retry_generate_20260518_171846.exit`
- current retry result: exit code `137`, H001 context load `388/388`, Lightning `Testing DataLoader 0` reached `377/377`, raw dump hook wrote `19162` rows
- raw dump identity audit: Docker `open3dsg_raw_dump_identity` status `raw_dump_identity_audit_ready`, blockers none
- current retry latest check: 2026-05-18 17:49 KST, tmux missing, `raw_dump/raw.jsonl` has 19162 rows
- v13 clean raw-dump-only rerun: exit code `137` before raw writing; no `raw_clean_exit_20260518_194818.jsonl`
- v14 streaming rerun: exit code `137` before `Testing DataLoader` / first streamed batch; no `raw_stream_20260518_204538.jsonl`, completed file, or manifest
- output target: `raw_dump/raw.jsonl`
- run records: `raw_dump/eval_avg_blip_20260518_012214.md`, `raw_dump/eval_avg_blip_retry_numpy_20260518_013208.md`, `raw_dump/eval_avg_blip_feature_ready_20260518_170149.md`, `raw_dump/eval_avg_blip_retry_shm_20260518_170639.md`, `raw_dump/eval_avg_blip_retry_dtype_20260518_171351.md`, `raw_dump/eval_avg_blip_retry_generate_20260518_171846.md`, `raw_dump/eval_avg_blip_clean_raw_dump_20260518_194818.md`, `raw_dump/eval_avg_blip_stream_raw_dump_20260518_204538.md`

Current H001 eval feature dump:

- first attempt status: `failed_missing_h001_eval_sequence_payload`
- first attempt result: exit code `1`, feature files `0`
- payload fix: Docker `h001_eval_payload` staged 127/127 held-out scan symlinks and 127/127 sequence-ready scans under `h001_runtime/data/3RScan`
- payload retry status: `failed_partial_exit_137`
- payload retry result: exit code `137`, complete feature ids `194/377`, total `.pt` files `582`
- v9 resume status: `failed_partial_exit_137`
- v9 resume result: exit code `137`, complete feature ids still `194/377`, no new `.pt` files
- chunk1 resume status: `failed_partial_exit_137`
- chunk1 resume result: exit code `137`, complete feature ids advanced to `195/377`, total `.pt` files `585`
- source patch: `h001_open3dsg_source_patch_v10`, including NumPy pickle compatibility, lazy eval dataset loading, remaining-id shard filtering, test-mode dump-feature return guard, eval-only relation mapper skip during feature dumping, and test-step pre-forward skip-existing
- tmux: ended
- payload retry log: `logs/open3dsg_dump_features_h001_eval_retry_payload_20260518_014442.log`
- payload retry exit file: `logs/open3dsg_dump_features_h001_eval_retry_payload_20260518_014442.exit`
- v9 resume log: `logs/open3dsg_dump_features_h001_eval_resume_v9_skip_20260518_084946.log`
- v9 resume exit file: `logs/open3dsg_dump_features_h001_eval_resume_v9_skip_20260518_084946.exit`
- chunk1 resume log: `logs/open3dsg_dump_features_h001_eval_resume_chunk1_20260518_091944.log`
- chunk1 resume exit file: `logs/open3dsg_dump_features_h001_eval_resume_chunk1_20260518_091944.exit`
- output target: `local_dataset/Open3DSG_staged/h001_runtime/output/features/clip_features_h001_eval_blip_top5_scales3`
- latest check: 2026-05-18 09:42 KST, tmux missing, chunk1 resume exit file `137`, complete ids `195/377`, newly written id `10b1794e-3938-2467-89a7-ebc89e84cf88-2`, next first missing loadable id `10b17940-3938-2467-8a7a-958300ba83d3-1`
- shard mode status: `completed`
- shard mode log: `logs/open3dsg_dump_features_h001_eval_shard_20260518_100159.log`
- shard mode exit file: `logs/open3dsg_dump_features_h001_eval_shard_20260518_100159.exit`
- shard mode result: exit code `0`, DataLoader `5/5`, complete feature ids advanced from `195/377` to `200/377`, total `.pt` files `600`
- shard mode latest check: 2026-05-18 10:14 KST, tmux missing, next first missing loadable id `4fbad31e-465b-2a5d-84b7-c0ddea978db4-1`
- shard loop status: `completed`
- shard loop log: `logs/open3dsg_dump_features_h001_eval_shard_loop_20260518_103948.log`
- shard loop exit file: `logs/open3dsg_dump_features_h001_eval_shard_loop_20260518_103948.exit`
- shard loop result: exit code `0`, complete covered loadable scope `377/377`, total `.pt` files `1131`
- feature audit after shard loop: missing complete feature ids `0`; audit status remains `blocked` only because of the known `validation_missing_preprocessed:11` caveat
- shard loop latest check: 2026-05-18 17:01 KST, tmux missing, final event `h001_eval_feature_shard_loop_complete complete_ids=377 target_loadable_ids=377`
- run records: `dump_features_h001_eval/run_20260518_013909.md`, `dump_features_h001_eval/retry_payload_20260518_014442.md`, `dump_features_h001_eval/resume_v9_skip_20260518_084946.md`, `dump_features_h001_eval/resume_chunk1_20260518_091944.md`, `dump_features_h001_eval/shard_mode_20260518.md`, `dump_features_h001_eval/shard_20260518_100159.md`, `dump_features_h001_eval/shard_loop_20260518_103948.md`
- next gate after raw dump: none for Open3DSG core evidence; paper caveat wording is frozen

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

- real adapter status: `ready`
- contract status: superseded by real adapter export
- smoke status: `ready`
- smoke counts: 388 contexts, 1 synthetic raw row, 2 prediction rows, zero errors/warnings
- real counts: 19,162 raw rows -> 496,600 prediction rows; 62 raw rows filtered outside the fixed H001 object context
- artifacts: `adapter/{manifest.json,raw_schema_example.json,report.md,predictions.jsonl}` and `adapter_smoke/{manifest.json,raw_smoke.jsonl,predictions.jsonl,report.md}`

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

Current real failure-analysis result:

- status: `failure_analysis_real_ready`
- scope: real Open3DSG prediction/GT/geometry/metric joins; taxonomy unchanged
- selection: union of semantic top-100 and probabilistic geometry-reranked top-100 per subgraph
- counts: 57,736 rows, 57,736 metric eligible, 6,162 visual-audit queue rows, validation errors 0
- main categories: semantic_false_positive 27,326; insufficient_geometry_evidence 20,828; semantic_and_geometry_failure 5,183; geometry_contradiction 979; predicate_family_ambiguity 1,727; rank_only_failure 433; true_positive_supported 1,260
- artifacts: `failure_rows/{rows.jsonl,summary.json,manifest.json,report.md}`

Current qualitative failure-case sample:

- status: `failure_case_sample_ready`
- scope: high-severity Open3DSG rows with `needs_visual_audit=true`; qualitative inspection queue only, not an additional metric
- selected cases: 36 from 6,162 candidates
- selected categories: geometry_contradiction 14, semantic_and_geometry_failure 22
- selected families: proximity 8, relative_vertical 18, support_contact 10
- artifacts: `failure_cases/{queue.jsonl,manifest.json,report.md}`

Current qualitative failure-case inspection:

- status: `qualitative_case_inspection_ready`
- scope: deterministic inspection of sampled queue; not a new metric and not an independent visual audit
- counts: 36 selected cases, 23 demoted by geometry-aware reranking, 13 promoted or retained, 10 rule-violated cases with `p_geom_valid > 0.9`
- mechanism note: failure pattern is family-structured, but calibrated probability is not equivalent to hard rule validity
- artifacts: `failure_cases/{inspection.json,inspection.md}`

Current paper caveat wording:

- status: `open3dsg_paper_caveats_ready`
- scope: paper-facing caveat wording only; it does not change metrics, taxonomy, checkpoint selection, or denominator policy
- fixed caveats: filtered train 3,744/3,852 subgraphs, train-dev validation 156/160 subgraphs, H001 covered loadable scope 377/388 contexts, `validation_missing_preprocessed:11`, averaged-BLIP variant, exact-label 2,545-row H001-family denominator, and residual calibration risk
- artifacts: `paper_caveats/{manifest.json,report.md}`

Convert an identity-preserving raw dump after it exists:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_adapter_raw_dump'
```

Run the Open3DSG geometry join:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_geometry_join'
```

Run the Open3DSG metric eval:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_metric_eval'
```

Current geometry/metric result:

- geometry status: `ready`, `496600/496600` rows preserved, `114600` geometry-checkable rows scored
- metric status: `ready`, blockers none
- metric artifacts: `geometry/{verification.jsonl,manifest.json,report.md}` and `metrics/{metrics.json,report.md}`

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
