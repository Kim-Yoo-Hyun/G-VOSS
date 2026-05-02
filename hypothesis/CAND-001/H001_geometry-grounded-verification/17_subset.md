# Subset

Last updated: 2026-05-03

## Role

This document records the multi-scan / `3DSSG_subset` strategy for H001.

The goal is to fix the scan and relation subset source before implementing:

```text
prediction-level baseline evaluation
calibration table export
counterfactual negative generation
p_geom_valid fitting/evaluation
```

## Local Dataset Facts

Checked on 2026-05-01.

Available local files:

| Item | Status |
| --- | --- |
| `local_dataset/3DSSG/objects.json` | available |
| `local_dataset/3DSSG/relationships.json` | available |
| `local_dataset/3DSSG_subset/relationships.json` | available |
| `local_dataset/3DSSG_subset/relationships_train.json` | available |
| `local_dataset/3DSSG_subset/relationships_validation.json` | available |
| `local_dataset/3DSSG_subset/classes.txt` | available |
| `local_dataset/3DSSG_subset/relationships.txt` | available |
| `local_dataset/3RScan/files/train_scans.full.txt` | available |
| `local_dataset/3RScan/files/val_scans.full.txt` | available |
| `local_dataset/3RScan/scans/<scan-id>/` payloads | only one scan available |

3DSSG subset counts:

| File | Entries | Unique scans |
| --- | ---: | ---: |
| `relationships.json` | 1,335 scan entries | 1,335 |
| `relationships_train.json` | 3,852 subgraph entries | 1,178 |
| `relationships_validation.json` | 548 subgraph entries | 157 |

Train and validation unique scan ids are disjoint.

Currently downloaded scan:

| Scan | Split | Full relations | Subset subgraph entries | Downloaded payload |
| --- | --- | ---: | ---: | --- |
| `f62fd5fd-9a3f-2f44-883a-1e5cf819608e` | train | 772 | 7 | yes |

Subset subgraph entries for the downloaded scan:

| Split | Relations | Objects |
| ---: | ---: | ---: |
| 1 | 25 | 9 |
| 2 | 34 | 9 |
| 3 | 17 | 9 |
| 4 | 27 | 9 |
| 5 | 32 | 9 |
| 6 | 23 | 9 |
| 7 | 20 | 9 |

The downloaded scan has these required payloads:

```text
labels.instances.annotated.v2.ply
semseg.v2.json
mesh.refined.0.010000.segs.v2.json
```

## Subset Format

`relationships_train.json` and `relationships_validation.json` contain subgraph entries:

```text
scan
split
objects
relationships
```

Important:

- `scan` is the 3RScan scan id.
- `split` is a subgraph index within a scan, not a train/val label.
- `objects` is an object-id to class-label mapping for the subgraph.
- `relationships` is the relation list for that subgraph.
- The same scan can appear multiple times with different `split` values.

Implication:

Prediction-level baseline evaluation should use subgraph entries as the natural unit when reproducing 3DSSG-style outputs. Geometry evidence extraction still needs scan-level 3RScan payloads.

## Predicate Coverage

Subset predicate counts:

| Predicate | Train | Validation |
| --- | ---: | ---: |
| `standing on` | 9,992 | 1,357 |
| `lying on` | 2,024 | 232 |
| `supported by` | 821 | 227 |
| `close by` | 12,484 | 1,766 |
| `higher than` | 1,831 | 195 |
| `lower than` | 1,831 | 195 |

Support/contact totals:

| Split | Subgraph entries | Support/contact |
| --- | ---: | ---: |
| train | 3,852 | 12,837 |
| validation | 548 | 1,816 |

Subgraph entries with at least 5 support/contact edges:

| Split | Entries | Relations | Support/contact |
| --- | ---: | ---: | ---: |
| train | 1,034 | 35,095 | 5,903 |
| validation | 150 | 4,905 | 866 |

Inference:

- The official subset has enough support/contact and geometry-checkable relations for H001.
- The blocker is no longer subset definition.
- The remaining blocker for multi-scan evaluation is downloading 3RScan scan payloads for selected subset scans.

## Decision

Use official `3DSSG_subset` as the primary split and relation-subgraph source.

Use full 3DSSG annotation only as auxiliary data for:

- checking scan-level relation coverage;
- compatibility checks;
- generating counterfactual negatives when official subset positives are insufficient;
- debugging one-scan smoke-test differences.

Do not use edge-random splits.

## Split Policy

Use official subset files as outer split boundary:

| Role | Source |
| --- | --- |
| train/dev candidates | `relationships_train.json` |
| held-out test candidates | `relationships_validation.json` |

For calibration:

- train calibrator on train subset scans;
- select thresholds/hyperparameters using a held-out dev slice from train subset scans;
- report final calibration and violation/recall metrics on validation subset scans.

Avoid selecting validation scans after inspecting verifier failures.

## Subset Stages

### Stage S0: Existing Smoke Scan

Purpose:

```text
script sanity check and artifact format validation
```

Status:

```text
completed
```

Scan:

```text
f62fd5fd-9a3f-2f44-883a-1e5cf819608e
```

Do not fit `p_geom_valid` here.

### Stage S1: H001-Mini

Purpose:

```text
multi-scan verifier replication on official subset entries
```

Recommended size:

```text
8 train scans + 4 validation scans
```

Selection unit:

```text
scan id
```

Evaluation unit:

```text
3DSSG_subset subgraph entry
```

Use:

- verify subset entry parsing;
- verify geometry evidence export across multiple scans;
- check support/contact subtype distribution;
- estimate download and runtime cost.

Do not report this as final benchmark evidence.

### Stage S2: H001-Calib-Pilot

Purpose:

```text
first calibration table and counterfactual negative smoke test
```

Recommended size:

```text
24 train scans + 8 dev scans + 8 validation scans
```

Use:

- export calibration table;
- generate high-margin counterfactual negatives;
- fit a simple `p_geom_valid` calibrator;
- report Brier/NLL/ECE/AUROC/AUPRC as pilot numbers.

This stage can show whether probabilistic calibration is feasible, but should still be framed as a pilot unless repeated at larger scale.

### Stage S3: H001-Benchmark

Purpose:

```text
prediction-level baseline evaluation
```

Use:

- run selected prediction baseline on official subset format;
- compare semantic-only vs rule-verified vs probabilistic-recalibrated;
- report violation/recall tradeoff on held-out validation scans.

Scale beyond S2 only after baseline output format is fixed.

## Scan Selection Criteria

Required:

- scan id appears in `3DSSG_subset` train or validation file;
- required 3RScan files are downloadable;
- subgraph entries include geometry-checkable relations;
- support/contact count is sufficient for H001.

Recommended first filter:

```text
support/contact >= 5 per subgraph entry
```

Required geometry-checkable families:

```text
support_contact
proximity
relative_vertical
```

Defer `relative_horizontal` until coordinate-frame validation.

Selection score for candidate subgraph entries:

```text
score = support_contact_count
      + 0.25 * proximity_count
      + 0.25 * relative_vertical_count
```

When selecting scan ids, aggregate scores over subgraph entries but avoid near-duplicate scene leakage if 3RScan reference/rescan grouping suggests overlap.

## Candidate Subgraph Entries

Top train entries by support/contact count:

| Scan | Split | Relations | Objects | Support/contact | Proximity | Relative vertical |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `355465d6-d29b-29f9-957c-e9ebbb5751ec` | 1 | 166 | 9 | 8 | 16 | 0 |
| `77941466-cfdf-29cb-865f-0e2fcea3af87` | 1 | 144 | 9 | 8 | 20 | 0 |
| `7794146a-cfdf-29cb-8705-f3f89d9ed3ae` | 1 | 140 | 9 | 8 | 18 | 0 |
| `0cac7558-8d6f-2d13-8fe1-c8af0362735d` | 4 | 124 | 9 | 8 | 8 | 26 |
| `1d233ffc-e280-2b1a-8c3a-af74ca2b0cea` | 1 | 114 | 9 | 8 | 18 | 16 |
| `355465d0-d29b-29f9-94f2-7707ac505bae` | 1 | 106 | 9 | 8 | 12 | 10 |

Top validation entries by support/contact count:

| Scan | Split | Relations | Objects | Support/contact | Proximity | Relative vertical |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `0cac7540-8d6f-2d13-8eee-36ba2a428e3f` | 3 | 86 | 9 | 8 | 2 | 0 |
| `c7895f29-339c-2d13-83e9-90dbe61fa8be` | 2 | 72 | 9 | 8 | 2 | 2 |
| `4fbad331-465b-2a5d-8488-852fcda9513c` | 3 | 66 | 9 | 8 | 8 | 0 |
| `0cac7532-8d6f-2d13-8cea-1e70d5ae4856` | 1 | 44 | 9 | 8 | 2 | 0 |
| `4a9a43d2-7736-2874-874d-d0fad0570e19` | 7 | 44 | 9 | 8 | 4 | 0 |
| `2451c048-fae8-24f6-9043-f1604dbada2c` | 2 | 36 | 9 | 8 | 10 | 0 |

## Required Payloads

H001 does not need full RGB-D sequences or texture files for the next stages.

Required per selected scan:

```text
labels.instances.annotated.v2.ply
semseg.v2.json
mesh.refined.0.010000.segs.v2.json
```

Avoid downloading for this stage unless needed:

```text
sequence.zip
mesh.refined.v2.obj
mesh.refined.mtl
mesh.refined_0.png
```

Reason:

- H001 evidence export and support/contact verification use object ids, semantic objects, and point geometry;
- full mesh/textures increase disk cost without changing the current verifier.

## Leakage Controls

Before finalizing a split:

- check train/dev/test are disjoint by scan id;
- check 3RScan reference/rescan groups from `3RScan.json`;
- avoid placing rescans from the same scene group across train/dev/test if group mapping is available;
- do not tune thresholds on validation scans;
- do not select validation scans after seeing verifier failures.

## Decision Summary

Chosen strategy:

```text
official 3DSSG_subset for baseline-compatible subgraph evaluation
```

Auxiliary strategy:

```text
full 3DSSG annotation for coverage checks and counterfactual construction
```

Immediate next action:

```text
write faithful VL-SAT layout prep staging policy
```

Reason:

- the official subset is now available;
- evaluation protocol already fixes the metric target;
- baseline choice is fixed in `18_baseline.md`;
- prediction schema is fixed in `19_schema.md`;
- full calibration should wait until local baseline layout prep, calibration table schema, and counterfactual negative policy are implemented.

## Next

1. Use `21_eval_path.md` as the faithful eval path decision.
2. Write layout prep staging policy.
3. Write calibration table schema.
4. Generate H001-Mini manifest only when downloading/running multi-scan payloads.
5. Implement calibration only after scan payloads and counterfactual negatives exist.
