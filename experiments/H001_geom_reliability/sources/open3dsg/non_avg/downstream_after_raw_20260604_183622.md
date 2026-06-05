# Open3DSG Non-Avg Downstream Continuation

Status: `stopped_raw_exit_137_superseded_by_manual_downstream`

## Purpose

Continue the Open3DSG non-avg branch after the raw dump finishes. This job
waits for the raw-dump exit file and runs downstream Docker services only if
the raw dump exits with code `0`.

Outcome: the raw stream completed 19,162 rows and 377/377 batches, but the raw
process exit file contained `137` after stream finalization. This continuation
therefore stopped before running downstream services. Manual downstream
execution from the complete raw dump is recorded in
`downstream_manual_20260604.md` and reached
`open3dsg_non_avg_branch_ready`.

## Launch

- launched at: `2026-06-04 18:36:22 KST`
- tmux: `h001_open3dsg_nonavg_downstream_20260604_183622`
- working directory: `/home/yoohyun/research`
- log: `logs/open3dsg_nonavg_downstream_20260604_183622.log`
- exit file: `logs/open3dsg_nonavg_downstream_20260604_183622.exit`
- raw-dump dependency:
  `logs/open3dsg_eval_h001_gt_objects_nonavg_stream_20260604_182423.exit`
- wait budget: `360` minutes
- runner script:
  `experiments/H001_geom_reliability/scripts/run_open3dsg_nonavg_downstream_after_raw.sh`
- raw exit observed by this run: `137`
- downstream services run by this continuation: none
- superseding record: `downstream_manual_20260604.md`

## Command

```bash
TS=$(date +%Y%m%d_%H%M%S)
SESSION="h001_open3dsg_nonavg_downstream_${TS}"
LOG="logs/open3dsg_nonavg_downstream_${TS}.log"
EXITF="logs/open3dsg_nonavg_downstream_${TS}.exit"
tmux new-session -d -s "$SESSION" "cd /home/yoohyun/research && RAW_EXIT=logs/open3dsg_eval_h001_gt_objects_nonavg_stream_20260604_182423.exit EXITF=$EXITF WAIT_MINUTES=360 bash experiments/H001_geom_reliability/scripts/run_open3dsg_nonavg_downstream_after_raw.sh > $LOG 2>&1"
```

## Downstream Order

1. `open3dsg_raw_dump_identity_nonavg`
2. `open3dsg_adapter_raw_dump_nonavg`
3. `open3dsg_geometry_join_nonavg`
4. `open3dsg_metric_eval_nonavg`
5. `bootstrap_ci_nonavg`
6. `open3dsg_non_avg_table6_caveats`

If any service fails, the continuation exits with that service's exit code and
does not run later services.

## Verification Commands

```bash
tmux ls | rg h001_open3dsg_nonavg_downstream
tail -n 80 logs/open3dsg_nonavg_downstream_20260604_183622.log
test -f logs/open3dsg_nonavg_downstream_20260604_183622.exit && tail -n 1 logs/open3dsg_nonavg_downstream_20260604_183622.exit
```

## Boundary

This continuation did not produce downstream artifacts. The non-avg downstream
artifacts were produced manually from the stream-complete raw dump. Paper Table
6/caveat wording must not be promoted until the user explicitly confirms
promotion.
