# Open3DSG Raw-Dump Identity Audit

Status: `raw_dump_identity_checklist_ready_raw_dump_missing`
Created at: `2026-05-10T05:32:09+00:00`

## Fact

- This artifact freezes the raw-dump identity checklist before Open3DSG raw outputs exist.
- It does not run Open3DSG eval, convert predictions, inspect metrics, or assign failure labels.
- The fixed H001 eval scope is used as the identity denominator.

## Scope

- selected scans: `127/127`
- contexts: `388/388`
- directed pairs: `25916/25916`

## Raw Dump

- path: `experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl`
- status: `raw_dump_missing`
- rows: `0`

## Blockers

- `missing_raw_dump:experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl`

## Claim Boundary

This is checklist/audit readiness only. It is not Open3DSG metric evidence.
