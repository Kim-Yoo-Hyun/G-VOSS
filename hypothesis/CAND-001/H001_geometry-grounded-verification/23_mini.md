# Mini

Last updated: 2026-05-03

This document fixes the first H001-Mini validation scan set.

It selects scan payloads before inspecting any `VL-SAT` prediction failures, so later evaluation is less exposed to cherry-picking.

## Decision

Use 8 official `3DSSG_subset` validation scans as H001-Mini:

```text
280d8ebb-6cc6-2788-9153-98959a2da801
ddc73797-765b-241a-9e2c-097c5989baf6
8eabc45f-5af7-2f32-8528-640861d2a135
75c25975-9ca2-2844-9769-84677f46d4cf
c7895f7c-339c-2d13-819f-3bb0b26c91f6
38770ca1-86d7-27b8-8619-ab66f67d9adf
a0905fd9-66f7-2272-9dfb-0483fdcc54c7
c7895f27-339c-2d13-836b-c12dca280261
```

Artifact root:

```text
artifacts/subset/h001_mini/
```

Selection tool:

```text
tools/select_mini.py
```

## Selection Rule

Source:

```text
local_dataset/3DSSG_subset/relationships_validation.json
```

Primary target:

```text
support_contact = standing on, lying on, supported by
```

Secondary coverage:

```text
proximity = close by
relative_vertical = higher than, lower than
```

Score:

```text
support_contact + 0.25 * proximity + 0.25 * relative_vertical
```

Filters:

- validation split only;
- scan-level support/contact count at least 15;
- at least one subgraph with support/contact count at least 5;
- at most one selected scan per 3RScan reference/rescan group.

Rationale:

- support/contact is the primary H001 geometry-verification target;
- proximity and vertical relations keep the subset from becoming one-family only;
- reference/rescan group de-duplication reduces near-duplicate scene bias;
- selecting before model prediction inspection improves paper defensibility.

## Coverage

Selected H001-Mini totals:

| Item | Count |
| --- | ---: |
| scans | 8 |
| subgraph entries | 56 |
| relationships | 1,458 |
| support/contact | 224 |
| proximity | 254 |
| relative vertical | 78 |
| deferred attachment/contact | 85 |

Selected scan table:

| Rank | Scan | Score | Entries | Relations | Support/contact | Proximity | Vertical |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `280d8ebb-6cc6-2788-9153-98959a2da801` | 48.50 | 8 | 211 | 37 | 42 | 4 |
| 2 | `ddc73797-765b-241a-9e2c-097c5989baf6` | 43.00 | 7 | 203 | 32 | 34 | 10 |
| 3 | `8eabc45f-5af7-2f32-8528-640861d2a135` | 40.00 | 7 | 155 | 29 | 32 | 12 |
| 4 | `75c25975-9ca2-2844-9769-84677f46d4cf` | 37.00 | 5 | 269 | 20 | 32 | 36 |
| 5 | `c7895f7c-339c-2d13-819f-3bb0b26c91f6` | 35.50 | 4 | 133 | 23 | 48 | 2 |
| 6 | `38770ca1-86d7-27b8-8619-ab66f67d9adf` | 34.50 | 10 | 153 | 29 | 18 | 4 |
| 7 | `a0905fd9-66f7-2272-9dfb-0483fdcc54c7` | 34.50 | 9 | 169 | 26 | 28 | 6 |
| 8 | `c7895f27-339c-2d13-836b-c12dca280261` | 34.00 | 6 | 165 | 28 | 20 | 4 |

## Artifact Files

Generated files:

```text
artifacts/subset/h001_mini/manifest.json
artifacts/subset/h001_mini/scans.txt
artifacts/subset/h001_mini/candidates.jsonl
artifacts/subset/h001_mini/subgraphs.jsonl
artifacts/subset/h001_mini/report.md
```

`manifest.json` records the parameters, selected scan list, family counts, and local payload status.

`candidates.jsonl` records every validation scan candidate and why it was selected, skipped, or left after the selected limit.

## Payload Status

The selected scan ids are not currently downloaded under:

```text
local_dataset/3RScan/scans/
```

Required payloads per selected scan:

```text
labels.instances.annotated.v2.ply
semseg.v2.json
mesh.refined.0.010000.segs.v2.json
sequence.zip
```

`sequence.zip` is required because `22_prep.md` fixes the reportable `VL-SAT` path as faithful `multi_view`, not `MODEL.use_2d_feats=false`.

## Next

1. Implement staged-root prep for H001-Mini scan files, `3DSSG_subset` annotations, `references.txt`, and `rescans.txt`.
2. Download or stage the required scan payloads.
3. Generate aligned PLY for the selected scans.
4. Generate `multi_view` features for the selected scans.
5. Re-run the layout checker against the staged root.
