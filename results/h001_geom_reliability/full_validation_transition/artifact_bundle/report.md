# Full-Validation Upload Artifact Bundle

Status: `upload_bundle_file_list_and_verification_fixed_no_archive_created`

This folder fixes the paper-facing artifact bundle to upload separately from
GitHub. It is intended for Google Drive, Zenodo, or Hugging Face Dataset. The
archive itself has not been created in this pass; the exact payload list,
per-file checksum manifest, row-count checks, and verification script are fixed.

Generated inventory status:

- payload files: 211
- per-file checksum records: 211
- row-count snapshot records: 18
- payload file-list sha256:
  `392aa550557f64603a4548a9e494248d22eed899ecea3fefbc558451b39b716b`
- payload checksum-manifest sha256:
  `923bfde4e39921f5dd3fc10f0ec1a98eea606b50b83d4495d0d5b3afd1e4ff2b`
- payload row-count-file sha256:
  `2e86fe118260300bae6379f763f39f0cda0e4b07dd38455878de5d832d121943`
- checksum generation log:
  `logs/h001_fullval_upload_checksums_20260611_002243.log`
- checksum generation exit:
  `logs/h001_fullval_upload_checksums_20260611_002243.exit` = 0
- verification log:
  `logs/h001_fullval_upload_verify_20260611_002319.log`
- verification exit:
  `logs/h001_fullval_upload_verify_20260611_002319.exit` = 0

## Included Sources

| Component | Role | Key rows / cases |
| --- | --- | ---: |
| Open3DSG selected checkpoint | selected official non-avg checkpoint | sha256 `ca86d429b19e846aec2bfff014256bf36f6f90da07e566b90c461d6eca8d76bb` |
| VL-SAT full-validation | controlled anchor | 957,008 predictions, 957,008 geometry rows, 59,841 failure rows, 36 qualitative cases |
| Open3DSG unmodified full-validation | source-as-is sensitivity route | 26,746 raw rows, 690,924 predictions, 690,924 geometry rows, 81,448 failure rows |
| Open3DSG recovery full-validation | primary open-vocabulary source | 26,938 raw rows, 695,916 predictions, 695,916 geometry rows, 82,155 failure rows, 36 qualitative cases |
| Scope/tables/manifests | paper-facing provenance | full official validation scope, current H001 tables, checkpoint-selection provenance |

## Fixed Inventory Files

- `upload_payload_files.txt`: exact payload file list used for archive creation
- `upload_payload_sha256s.txt`: per-file SHA256 checksums for the payload files
- `upload_payload_row_counts.txt`: key row-level JSONL counts
- `verify_upload_bundle.sh`: checksum, row-count, and status verification script

## Boundary

The bundle supports the current full-validation H001 claim only. It does not
include raw 3RScan/3DSSG datasets, Open3DSG feature `.pt` caches, Qwen-VL model
cache/runtime outputs, or optional attachment/lateral expansion outputs.

The Open3DSG recovery route must be described as a recovery-policy branch using
`OPEN3DSG_MIN_VISIBLE_OBJECTS=2` plus relaxed two-scan view regeneration. The
unmodified 533/548 route is included as sensitivity/provenance evidence, not as
the selected full-denominator main route.

## Verification

Run from the repository root after download/extraction:

```bash
sha256sum -c results/h001_geom_reliability/full_validation_transition/artifact_bundle/upload_payload_sha256s.txt
bash results/h001_geom_reliability/full_validation_transition/artifact_bundle/verify_upload_bundle.sh
```

If an upload archive is created, also verify the archive checksum:

```bash
sha256sum -c release/h001_full_validation_results_<timestamp>.sha256
```
