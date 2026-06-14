# Open3DSG Non-Avg Manual Downstream Completion

Status: `open3dsg_non_avg_branch_ready`

## Reason

The raw-dump stream completed all expected batches and wrote a complete raw
JSONL, but the Open3DSG process exited `137` after finalization:

```text
raw rows: 19,162
completed batches: 377/377
stream manifest status: raw_dump_stream_complete
raw process exit: 137
```

The previously launched continuation waited for raw exit code `0`, so it did
not run downstream services. Because the stream manifest and raw row counts
matched the complete avg-BLIP route, downstream services were run manually from
the complete non-avg raw dump.

## Commands Run

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_raw_dump_identity_nonavg
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_adapter_raw_dump_nonavg
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_geometry_join_nonavg
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_metric_eval_nonavg
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm bootstrap_ci_nonavg
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_non_avg_table6_caveats
```

## Output Status

| gate | artifact | status |
| --- | --- | --- |
| raw-dump identity | `raw_dump_identity/manifest.json` | `raw_dump_identity_audit_ready` |
| adapter export | `adapter/manifest.json` | `ready` |
| geometry join | `geometry/manifest.json` | `ready` |
| metric eval | `metrics/metrics.json` | `ready` |
| bootstrap CI | `bootstrap_ci/manifest.json` | `ready` |
| Table 6 / caveat report | `table6_caveats/manifest.json` | `open3dsg_non_avg_branch_ready` |

## Key Counts

- raw rows: `19,162`
- adapter prediction rows: `496,600`
- geometry verification rows: `496,600`
- geometry-checkable rows: `114,600`
- H001 exact-label denominator: `2,545`
- covered H001 loadable contexts: `377/388`
- retained caveat: `validation_missing_preprocessed:11`

## Metric Summary

| condition | R@50 | R@100 | V@50 | V@100 |
| --- | ---: | ---: | ---: | ---: |
| semantic_only | 0.4310 | 0.5320 | 0.1395 | 0.1256 |
| probabilistic_recalibrated | 0.3945 | 0.5639 | 0.0570 | 0.0782 |
| rule_verified_point_subtype | 0.4507 | 0.5481 | 0.0000 | 0.0000 |
| control_family_specific_p_geom_valid | 0.4750 | 0.6047 | 0.0243 | 0.0310 |

Compared with the avg-BLIP branch, non-avg improves R@100 for all listed
conditions. Semantic-only violation is slightly higher, while the
geometry-aware conditions are similar or slightly better on V@100.

## Claim Boundary

This branch is now complete enough to be reported as a separately regenerated
official non-avg Open3DSG branch. It should not replace the current avg-BLIP
paper-facing wording unless the user explicitly confirms promotion. Filtered
train/dev, covered H001 `377/388`, exact-label denominator `2,545`,
`validation_missing_preprocessed:11`, and residual calibration-risk caveats
remain.
