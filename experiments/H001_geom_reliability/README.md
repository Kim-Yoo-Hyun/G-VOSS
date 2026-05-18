# H001 Geometry Reliability Experiment

Last updated: 2026-05-18

This is the first paper-body experiment workflow for H001. It is Docker-based by rule.

## Scope

Current executable source:

- `VL-SAT` / `vlsat_closed_set`

Selected top-tier expansion:

- Open3DSG second-source adapter result after Dockerized checkpoint reproduction; checkpoint plan, `training_repro` metadata/split staging, full payload staging, train/validation views, explicit train/validation preprocess filtering, official BLIP TopK5/scales3 feature dump, Docker feature audit, avg-BLIP checkpoint reproduction, checkpoint selection, eval preflight, raw-dump identity checklist, predicate-family/denominator metric-scope policy, pre-metric failure-analysis schema, synthetic failure row-generator smoke, metric/join blocked-input contract, and Table 6 blocked hook are ready. Current active step is H001 held-out eval feature dumping under the `h001_runtime` root, before rerunning the selected averaged-BLIP Open3DSG raw dump.
- Qwen-VL modern semantic-source extension contract is ready under `sources/qwen_vl/`; recommended small model ladder is Qwen3-VL-4B first, Qwen2.5-VL-3B stable fallback, and Qwen3-VL-2B parser-smoke candidate. Frozen input JSON Schema, output JSONL contract, contract-only validator/parser skeleton, non-held-out tiny pilot scope, runtime model-lock plan, and tiny-pilot pair-crop rendering path are recorded. The locked Qwen3-VL-4B model-cache download completed and cache verification is ready; runtime preflight is currently blocked by Open3DSG GPU occupancy, so tiny inference smoke has not started. This is not a replacement for Open3DSG reproduction evidence.

Current method framing:

```text
calibrated geometry-consistency evaluation and re-ranking framework
```

## What This Stage Does

This stage reads locked hypothesis artifacts, validates fixed counts, records input hashes/row counts, generates paper-facing tables/report files, records the Dockerized Open3DSG checkpoint reproduction plan, stages the Open3DSG `training_repro` metadata/split root, and tracks the Dockerized Open3DSG second-source reproduction pipeline. Paper-facing metric promotion remains blocked until raw-dump identity, adapter export, geometry join, and Open3DSG metrics pass.

Generated outputs:

- `tables/table1_main_prediction.*`
- `tables/table2_controls.*`
- `tables/table3_gt_verifier.*`
- `tables/table4_audit.*`
- `tables/table5_claim_boundary.*`
- `tables/table6_cross_source_status.*`
- `figures/figure_specs.*`
- `sources/vlsat/locked_inputs.json`
- `sources/open3dsg/checkpoint_plan.*`
- `sources/open3dsg/Dockerfile.repro`
- `sources/open3dsg/compose.open3dsg.yaml`
- `sources/open3dsg/commands.open3dsg.md`
- `sources/open3dsg/post_dump_handoff/manifest.json`
- `sources/open3dsg/post_dump_handoff/commands.md`
- `sources/open3dsg/post_dump_handoff/report.md`
- `sources/open3dsg/checkpoint_selection/selection_policy.json`
- `sources/open3dsg/checkpoint_selection/record_template.json`
- `sources/open3dsg/checkpoint_selection/manifest.json`
- `sources/open3dsg/checkpoint_selection/commands.md`
- `sources/open3dsg/checkpoint_selection/report.md`
- `sources/open3dsg/raw_dump_identity/checklist.json`
- `sources/open3dsg/raw_dump_identity/manifest.json`
- `sources/open3dsg/raw_dump_identity/commands.md`
- `sources/open3dsg/raw_dump_identity/report.md`
- `sources/open3dsg/metric_scope/predicate_mapping.json`
- `sources/open3dsg/metric_scope/denominator_policy.json`
- `sources/open3dsg/metric_scope/manifest.json`
- `sources/open3dsg/metric_scope/commands.md`
- `sources/open3dsg/metric_scope/report.md`
- `sources/open3dsg/failure_analysis/schema.json`
- `sources/open3dsg/failure_analysis/taxonomy.json`
- `sources/open3dsg/failure_analysis/aggregation_plan.json`
- `sources/open3dsg/failure_analysis/report.md`
- `sources/open3dsg/failure_analysis_generator_smoke/rows.jsonl`
- `sources/open3dsg/failure_analysis_generator_smoke/summary.json`
- `sources/open3dsg/failure_analysis_generator_smoke/manifest.json`
- `sources/open3dsg/failure_analysis_generator_smoke/report.md`
- `sources/open3dsg/metric_join_contract/input_contract.json`
- `sources/open3dsg/metric_join_contract/output_contract.json`
- `sources/open3dsg/metric_join_contract/metrics.json`
- `sources/open3dsg/metric_join_contract/manifest.json`
- `sources/open3dsg/metric_join_contract/commands.md`
- `sources/open3dsg/metric_join_contract/report.md`
- `sources/open3dsg/training_repro/manifest.json`
- `sources/open3dsg/training_repro/report.md`
- `sources/open3dsg/status.json`
- `sources/open3dsg/table6_hook.json`
- `sources/qwen_vl/adapter_contract.json`
- `sources/qwen_vl/input_schema.json`
- `sources/qwen_vl/input_schema_example.json`
- `sources/qwen_vl/model_candidates.json`
- `sources/qwen_vl/output_schema.json`
- `sources/qwen_vl/output_jsonl_contract.md`
- `sources/qwen_vl/prompt_templates.md`
- `sources/qwen_vl/prediction_schema_example.json`
- `sources/qwen_vl/validation/manifest.json`
- `sources/qwen_vl/validation/report.md`
- `sources/qwen_vl/tiny_pilot/input.jsonl`
- `sources/qwen_vl/tiny_pilot/manifest.json`
- `sources/qwen_vl/tiny_pilot/report.md`
- `sources/qwen_vl/runtime_plan/model_recommendation.json`
- `sources/qwen_vl/runtime_plan/report.md`
- `sources/qwen_vl/crops/records.jsonl`
- `sources/qwen_vl/crops/manifest.json`
- `sources/qwen_vl/crops/report.md`
- `manifest.lock.json`
- `report.md`

## Run

Use the commands in `commands.md`. Paper-facing outputs must be generated through Docker.

## Claim Boundary

Allowed now:

```text
Scoped VL-SAT-centered geometry-consistency reliability-layer result.
```

Blocked until Open3DSG metrics exist:

```text
Cross-predictor baseline-agnostic reliability-layer claim.
```

Current Open3DSG blocker:

```text
H001 eval feature dump is blocked on repeated exit 137 at the first post-resume missing feature id. The first raw dump run exited 0 but produced no raw_dump/raw.jsonl because numpy._core unpickle errors collapsed the test DataLoader to length 0. Source patch schema h001_open3dsg_source_patch_v7 recovered 377/388 H001 eval contexts; the NumPy retry then failed because H001 held-out eval feature ids were not present in the official training_repro feature dump. Source patch schema h001_open3dsg_source_patch_v8 added a test-mode dump-feature return guard. Docker h001_eval_payload staged 127/127 held-out scan symlinks and sequence-ready scans after the first H001 eval feature dump attempt found missing sequence payload under h001_runtime. The payload retry exited 137 after 194/377 complete feature ids; source patch schema h001_open3dsg_source_patch_v9 adds test-step pre-forward skip-existing, but the v9 resume also exited 137 after skipping to 194/377 without writing new feature ids. Next mitigation is a lower-memory resume, likely `OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=1`.
```

Current Open3DSG metric/join blocker:

```text
metric/join contract is frozen, but real Open3DSG predictions and geometry verification JSONL are missing; current status is blocked_runtime_inputs_missing and must not be treated as metric evidence.
```

Current Open3DSG checkpoint-selection blocker:

```text
checkpoint selection is ready for the explicitly labeled averaged-BLIP variant. Selected checkpoint: epoch=13-step=13104.ckpt by train-dev val/loss 0.32881081104278564 at step 13103, before H001 held-out raw dump/metrics/failure analysis/visual inspection. Exact non-averaged BLIP route remains OOM-blocked and must be reported as a limitation.
```

Current Open3DSG raw-dump identity blocker:

```text
raw-dump identity checklist is frozen with H001 scope 127 scans / 388 contexts / 25,916 directed pairs; current status is raw_dump_identity_checklist_ready_raw_dump_missing because the real raw dump does not exist yet.
```

Current Open3DSG metric-scope policy:

```text
predicate-family mapping and denominator caveat are frozen; in-scope GT denominator is 2,545 rows across support_contact 1,199 / proximity 1,128 / relative_vertical 218. Table 6 requires this policy before real Open3DSG metrics can be promoted.
```

Current Open3DSG Table 6 hook:

```text
table builder reads the metric/join contract and keeps Open3DSG Table 6 blocked until metrics.json status is ready, conditions are nonempty, and blockers are empty.
```
