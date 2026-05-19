# Open3DSG Post-Dump Handoff

Status: `completed_superseded_by_runtime_outputs`
Created at: `2026-05-11T15:27:01+00:00`
Updated at: `2026-05-18T21:37:00+09:00`

## Feature Progress

- feature run: `local_dataset/Open3DSG_staged/training_repro/output/features/clip_features_h001_official_blip_top5_scales3`
- complete feature ids: `3900/3900`
- progress: `100%`
- missing complete ids: `0`

## Gates

- `feature_dump_complete`: `True`
- `official_feature_audit`: `True`
- `checkpoint_available`: `True`, selected avg-BLIP checkpoint `epoch=13-step=13104.ckpt`
- `raw_dump_available`: `True`, `raw_dump/raw.jsonl` has 19,162 rows with exit-137-after-write caveat
- `adapter_ready`: `True`, 496,600 prediction rows
- `metrics_ready`: `True`, Open3DSG Table 6 hook ready
- `failure_rows_ready`: `True`, 57,736 real rows and 36 qualitative case candidates

## Transition Rule

The original handoff was a reproducibility/claim-boundary artifact only. It has
now been superseded by actual Docker runtime outputs under the Open3DSG source
folder.

Real Open3DSG second-source claims are enabled only within measured H001
families and closed-set/GT-object scope. Final paper wording must retain the
filtered-train, averaged-BLIP, covered-scope, source exit `137`, and
`validation_missing_preprocessed:11` caveats.
