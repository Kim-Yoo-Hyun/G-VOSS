# Qwen-VL Full-Source Promotion Commands

Current command that freezes this plan:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm qwen_vl_full_source_plan'
```

Outputs:

- `experiments/H001_geom_reliability/sources/qwen_vl/full_source_plan/manifest.json`
- `experiments/H001_geom_reliability/sources/qwen_vl/full_source_plan/protocol.json`
- `experiments/H001_geom_reliability/sources/qwen_vl/full_source_plan/report.md`
- `experiments/H001_geom_reliability/sources/qwen_vl/full_source_plan/commands.md`

Future implementation order. These services are intentionally not run by this
plan and should be implemented only after the protocol is accepted:

1. `qwen_vl_full_source_input`: build the complete H001 directed-pair/family input manifest and crop audit.
2. `qwen_vl_full_source_infer`: run Qwen inference in resumable shards under `tmux`, with timestamped `logs/`.
3. `qwen_vl_full_source_validate`: validate raw responses against `h001_qwen_vl_prediction_v2`.
4. `qwen_vl_adapter_export`: convert parsed Qwen rows into H001 `predictions.jsonl`.
5. `qwen_vl_geometry_join`: run the existing H001 geometry join.
6. `qwen_vl_metric_eval`: run the existing R@K / Violation@K evaluator and controls.
7. `qwen_vl_bootstrap_ci`: run subgraph bootstrap CI if Qwen appears in a paper table.
8. `qwen_vl_failure_audit`: generate deterministic qualitative/failure cases.
