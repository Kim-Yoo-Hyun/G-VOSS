# H001-Mini Scan Selection

Last updated: 2026-05-03

This artifact fixes the first H001-Mini validation scan list before any `VL-SAT` prediction failures are inspected.

## Selection Policy

- Source split: official `3DSSG_subset` validation split.
- Primary target: `support_contact` relation coverage.
- Secondary coverage: `proximity` and `relative_vertical`.
- Duplicate control: select at most one scan per 3RScan reference/rescan group.
- Score: `support_contact + 0.25 * proximity + 0.25 * relative_vertical`.

## Parameters

- selected scans: 8
- candidate scans: 157
- min scan-level support/contact: 15
- min best-subgraph support/contact: 5

## Selected Scans

| Rank | Scan | Group | Score | Entries | Relations | Objects | Support/contact | Proximity | Vertical | Attachment | Local payload |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `280d8ebb-6cc6-2788-9153-98959a2da801` | `280d8ebb-6cc6-2788-9153-98959a2da801` | 48.50 | 8 | 211 | 31 | 37 | 42 | 4 | 10 | missing |
| 2 | `ddc73797-765b-241a-9e2c-097c5989baf6` | `ddc73797-765b-241a-9e2c-097c5989baf6` | 43.00 | 7 | 203 | 25 | 32 | 34 | 10 | 11 | missing |
| 3 | `8eabc45f-5af7-2f32-8528-640861d2a135` | `8eabc45f-5af7-2f32-8528-640861d2a135` | 40.00 | 7 | 155 | 24 | 29 | 32 | 12 | 15 | missing |
| 4 | `75c25975-9ca2-2844-9769-84677f46d4cf` | `75c25975-9ca2-2844-9769-84677f46d4cf` | 37.00 | 5 | 269 | 15 | 20 | 32 | 36 | 5 | missing |
| 5 | `c7895f7c-339c-2d13-819f-3bb0b26c91f6` | `c7895f7c-339c-2d13-819f-3bb0b26c91f6` | 35.50 | 4 | 133 | 16 | 23 | 48 | 2 | 2 | missing |
| 6 | `38770ca1-86d7-27b8-8619-ab66f67d9adf` | `38770ca1-86d7-27b8-8619-ab66f67d9adf` | 34.50 | 10 | 153 | 37 | 29 | 18 | 4 | 20 | missing |
| 7 | `a0905fd9-66f7-2272-9dfb-0483fdcc54c7` | `a0905fd9-66f7-2272-9dfb-0483fdcc54c7` | 34.50 | 9 | 169 | 31 | 26 | 28 | 6 | 17 | missing |
| 8 | `c7895f27-339c-2d13-836b-c12dca280261` | `c7895f27-339c-2d13-836b-c12dca280261` | 34.00 | 6 | 165 | 15 | 28 | 20 | 4 | 5 | missing |

## Coverage Totals

- entries: 56
- relationships: 1458
- support/contact: 224
- proximity: 254
- relative vertical: 78
- deferred attachment/contact: 85

## Payload Status

Current local payload status is checked only under `local_dataset/3RScan/scans/<scan_id>/`.

Required per selected scan:

```text
labels.instances.annotated.v2.ply
semseg.v2.json
mesh.refined.0.010000.segs.v2.json
sequence.zip
```

Download pattern:

```text
python local_dataset/3RScan/download_3rscan.py -o local_dataset/3RScan/scans --id <scan_id> --type <file_type>
```

## Candidate Files

- `manifest.json`: selected list, parameters, totals, payload status.
- `scans.txt`: selected scan ids for download/prep scripts.
- `candidates.jsonl`: all validation scan candidates with selection reason.
- `subgraphs.jsonl`: selected subgraph summaries.

## Next

1. Download or stage required payloads for the selected scan ids.
2. Implement staged-root prep for `VL-SAT` annotations, scan files, `references.txt`, and `rescans.txt`.
3. Generate aligned PLY for selected scans.
4. Generate `multi_view` features for selected scans.

## Duplicate Group Skips

- `10b17957-3938-2467-88a5-9e9254930dad` skipped because group `280d8ebb-6cc6-2788-9153-98959a2da801` was already selected.
- `c7895f7a-339c-2d13-82ac-09ef1c9001ba` skipped because group `c7895f7c-339c-2d13-819f-3bb0b26c91f6` was already selected.
- `ea318260-0a4c-2749-9389-4c16c782c4b1` skipped because group `280d8ebb-6cc6-2788-9153-98959a2da801` was already selected.
- `0cac75b7-8d6f-2d13-8cb2-0b4e06913140` skipped because group `ddc73797-765b-241a-9e2c-097c5989baf6` was already selected.
- `c7895f07-339c-2d13-8176-7418b6e8d7ce` skipped because group `ddc73797-765b-241a-9e2c-097c5989baf6` was already selected.
