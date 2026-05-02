# Schema

Last updated: 2026-05-03

## Role

This document defines the H001 prediction JSONL contract for the first learned baseline:

```text
vlsat_closed_set
```

The schema is an adapter contract between `VL-SAT` outputs and H001 geometry verification/evaluation.

It is not an implementation log and does not create evaluation artifacts yet.

## Source Facts

Checked on 2026-05-01.

Primary source:

- `VL-SAT` official repository: <https://github.com/wz7in/CVPR2023-VLSAT>

Relevant `VL-SAT` facts:

- The README expects `data/3DSSG_subset/relations.txt`, `classes.txt`, and 3RScan scan folders with `multi_view` and `labels.instances.align.annotated.v2.ply`.
- `config/mmgnet.json` sets `MODEL.multi_rel_outputs` to `true`.
- In `src/dataset/dataset_3dssg.py`, `none` is removed from `relationNames` when `multi_rel_outputs` is true.
- In `PointNetRelClsMulti`, relation outputs are passed through `sigmoid`, so relation scores should be treated as multi-label predicate probabilities, not softmax probabilities.
- The validation code saves aggregate `.npy` outputs such as `topk_pred_list.npy`, `topk_triplet_list.npy`, `cls_matrix_list.npy`, `sub_scores_list.npy`, `obj_scores_list.npy`, and `rel_scores_list.npy`, but these files alone do not preserve enough scan/subgraph/object-pair metadata for H001 geometry verification.

Inference:

- H001 should export prediction JSONL during or immediately after `VL-SAT` validation while `scan_id`, `split`, object ids, edge indices, relation labels, and scores are still joinable.
- The adapter should not depend only on aggregate `.npy` metric files.

## Files

When implemented, the first adapter should produce:

```text
manifest.json
predictions.jsonl
ground_truth.jsonl
```

Recommended future artifact root:

```text
artifacts/evaluation/vlsat_closed_set/<split-name>/
```

Do not create this artifact directory until the first prediction-level run is actually implemented.

## Unit

One `predictions.jsonl` line represents:

```text
one candidate predicate for one directed object pair in one official 3DSSG_subset subgraph
```

Default export policy:

```text
all_non_none_predicates_per_directed_pair
```

Reason:

- `VL-SAT` uses multi-label sigmoid relation outputs;
- thresholding before H001 verification would hide recall/violation tradeoffs;
- H001 can rank/filter later using `semantic_only`, `rule_verified`, or `probabilistic_recalibrated` policies.

For quick smoke tests, an adapter may also emit a capped `top_m_per_pair` export, but that export must be marked in `manifest.json` and must not be used as final benchmark evidence.

## Identifier Policy

Subgraph id:

```text
<scan_id>_<subset_split_id>
```

Prediction id:

```text
<baseline_name>:<split_name>:<scan_id>:<subset_split_id>:<subject_id>:<object_id>:<predicate_label>
```

Ground-truth id:

```text
gt:<subset_source>:<scan_id>:<subset_split_id>:<subject_id>:<object_id>:<predicate_label>
```

Direction policy:

- `subject_id` is the first object id in the official relationship tuple.
- `object_id` is the second object id in the official relationship tuple.
- The adapter must not swap subject/object order to match variable names inside a baseline.

## Predicate Index Policy

Local `3DSSG_subset/relationships.txt` includes `none` at raw index 0.

`VL-SAT` removes `none` in multi-label mode.

Therefore:

```text
vlsat_predicate_index = raw_3dssg_predicate_id - 1
```

for every non-`none` predicate.

Rules:

- `predicate_label` must be the lowercase text label.
- `raw_3dssg_predicate_id` is the line index in `relationships.txt`, including `none`.
- `vlsat_predicate_index` is the model output column index, excluding `none`.
- `none` predictions are not emitted in H001 prediction JSONL.

Example:

| Predicate | Raw 3DSSG id | VL-SAT index |
| --- | ---: | ---: |
| `supported by` | 1 | 0 |
| `close by` | 6 | 5 |
| `standing on` | 15 | 14 |
| `lying on` | 16 | 15 |

## `manifest.json`

Required fields:

```json
{
  "schema_version": "h001_prediction_manifest_v1",
  "baseline_name": "vlsat_closed_set",
  "baseline_run_id": "string",
  "split_name": "train|dev|validation|test|mini",
  "task_mode": "predcls_relation|sgcls_triplet",
  "prediction_file": "predictions.jsonl",
  "ground_truth_file": "ground_truth.jsonl",
  "subset_file": "local_dataset/3DSSG_subset/relationships_validation.json",
  "class_file": "local_dataset/3DSSG_subset/classes.txt",
  "relationship_file": "local_dataset/3DSSG_subset/relationships.txt",
  "vlsat_relationship_file": "relations.txt",
  "export_policy": "all_non_none_predicates_per_directed_pair",
  "score_source": "vlsat_rel_cls_3d_sigmoid",
  "object_source": "3DSSG_subset_gt",
  "edge_source": "vlsat_edge_indices",
  "created_at": "YYYY-MM-DD",
  "counts": {
    "subgraphs": 0,
    "directed_pairs": 0,
    "predictions": 0,
    "ground_truth_edges": 0
  },
  "notes": []
}
```

Allowed first `task_mode`:

```text
predcls_relation
```

Reason:

- H001 first evaluates relation reliability with known object instances;
- object detection and SGCls-style object prediction should not be mixed into the first geometry verifier claim.

## `predictions.jsonl`

Required top-level fields:

```text
schema_version
record_type
prediction_id
baseline_name
baseline_run_id
split_name
subset_source
scan_id
subset_split_id
subgraph_id
task_mode
edge
predicate
scores
ranks
adapter
```

Example:

```json
{
  "schema_version": "h001_prediction_v1",
  "record_type": "prediction",
  "prediction_id": "vlsat_closed_set:validation:0cac7540-8d6f-2d13-8eee-36ba2a428e3f:3:13:25:close by",
  "baseline_name": "vlsat_closed_set",
  "baseline_run_id": "vlsat_eval_YYYYMMDD",
  "split_name": "validation",
  "subset_source": "3DSSG_subset/relationships_validation.json",
  "scan_id": "0cac7540-8d6f-2d13-8eee-36ba2a428e3f",
  "subset_split_id": 3,
  "subgraph_id": "0cac7540-8d6f-2d13-8eee-36ba2a428e3f_3",
  "task_mode": "predcls_relation",
  "edge": {
    "edge_index": 12,
    "edge_source": "vlsat_edge_indices",
    "subject_id": 13,
    "object_id": 25,
    "subject_node_index": 0,
    "object_node_index": 3,
    "subject_label": "cabinet",
    "object_label": "lamp",
    "subject_label_source": "3DSSG_subset",
    "object_label_source": "3DSSG_subset"
  },
  "predicate": {
    "predicate_label": "close by",
    "predicate_family": "proximity",
    "raw_3dssg_predicate_id": 6,
    "vlsat_predicate_index": 5,
    "predicate_vocab": "3DSSG_subset_26_no_none"
  },
  "scores": {
    "predicate_score": 0.82,
    "predicate_score_type": "sigmoid_probability",
    "subject_score": null,
    "object_score": null,
    "triplet_score": null,
    "ranking_score": 0.82,
    "ranking_score_type": "predicate_score"
  },
  "ranks": {
    "predicate_rank_for_pair": 1,
    "semantic_rank_in_subgraph": 12
  },
  "adapter": {
    "name": "vlsat_to_h001_predictions",
    "version": "v0",
    "export_policy": "all_non_none_predicates_per_directed_pair"
  }
}
```

### Field Rules

`task_mode`:

- `predcls_relation`: object ids and object labels come from official subset / ground truth; predicate is predicted.
- `sgcls_triplet`: object labels and predicate are predicted; not first H001 mode.

`predicate_score`:

- must be the raw `VL-SAT` relation probability after sigmoid for `multi_rel_outputs=true`;
- must not be replaced by a geometry score.

`ranking_score`:

- first run: same as `predicate_score`;
- later SGCls run: may be `subject_score * object_score * predicate_score`, but the formula must be recorded in `ranking_score_type`.

`semantic_rank_in_subgraph`:

- rank after sorting candidate predictions within one subgraph by `ranking_score` descending;
- ties should be stable by `(subject_id, object_id, predicate_label)`.

`predicate_family`:

- must use H001 mapping:
  - `standing on`, `lying on`, `supported by` -> `support_contact`
  - `close by` -> `proximity`
  - `higher than`, `lower than` -> `relative_vertical`
  - `left`, `right`, `front`, `behind` -> `relative_horizontal`
  - everything else -> existing H001 deferred/unsupported family.

## `ground_truth.jsonl`

One line represents one official relation tuple in an official subset subgraph.

Required fields:

```text
schema_version
record_type
gt_id
split_name
subset_source
scan_id
subset_split_id
subgraph_id
subject_id
object_id
subject_label
object_label
predicate_label
predicate_family
raw_3dssg_predicate_id
vlsat_predicate_index
```

Example:

```json
{
  "schema_version": "h001_ground_truth_v1",
  "record_type": "ground_truth",
  "gt_id": "gt:validation:0cac7540-8d6f-2d13-8eee-36ba2a428e3f:3:13:25:close by",
  "split_name": "validation",
  "subset_source": "3DSSG_subset/relationships_validation.json",
  "scan_id": "0cac7540-8d6f-2d13-8eee-36ba2a428e3f",
  "subset_split_id": 3,
  "subgraph_id": "0cac7540-8d6f-2d13-8eee-36ba2a428e3f_3",
  "subject_id": 13,
  "object_id": 25,
  "subject_label": "cabinet",
  "object_label": "lamp",
  "predicate_label": "close by",
  "predicate_family": "proximity",
  "raw_3dssg_predicate_id": 6,
  "vlsat_predicate_index": 5
}
```

If `predicate_label` is `none`, do not emit a ground-truth row.

## Adapter Contract

The adapter must preserve these joins:

```text
scan_id + subset_split_id
subject_id + object_id
predicate_label
```

Required adapter context:

- `dataset_valid.scans[i]` or equivalent subgraph id;
- `dataset_valid.objs_json[subgraph_id]`;
- `dataset_valid.relationship_json[subgraph_id]`;
- `edge_indices` for the current batch;
- `rel_cls_3d` scores from `VL-SAT`;
- `relationNames` after `none` removal.

Recommended implementation point:

```text
inside VL-SAT validation, before metric aggregation
```

Reason:

- after validation, saved aggregate `.npy` files lose direct scan/subgraph/object-pair identity;
- H001 needs that identity to join predictions to geometry evidence and official ground truth.

If implementing outside `VL-SAT`, export or reconstruct:

```text
subgraph_id
node_index_to_instance_id
edge_index_to_node_pair
rel_scores
```

Do not infer node-index-to-instance-id from array order unless the adapter has explicitly saved that mapping.

## Validation Checks

A valid prediction export must satisfy:

- every JSONL row parses;
- every `prediction_id` is unique;
- `baseline_name == "vlsat_closed_set"`;
- `predicate_label != "none"`;
- `0 <= predicate_score <= 1`;
- `ranking_score` is numeric;
- `vlsat_predicate_index == raw_3dssg_predicate_id - 1`;
- `subject_id` and `object_id` appear in the subgraph `objects`;
- `subject_id != object_id`;
- `predicate_family` is present;
- `semantic_rank_in_subgraph` is positive and unique within a subgraph after tie-breaking.

A valid ground-truth export must satisfy:

- every official non-`none` relationship tuple appears once;
- subject/object ids match the official tuple order;
- predicate label and raw predicate id agree with `relationships.txt`;
- train/dev/validation split source is recorded.

## H001 Evaluation Join

After this schema is implemented:

1. `predictions.jsonl` provides semantic candidate edges.
2. H001 geometry export adds geometry evidence for the same `(scan_id, subject_id, object_id)` pair.
3. `h001-verifier-v2` produces `satisfied`, `uncertain`, `violated`, or `unsupported`.
4. `16_evaluation.md` computes `semantic_only` vs `rule_verified` metrics.

The verifier must preserve every prediction row and attach verification status; it must not silently drop predictions.

## Next

1. Use `20_layout.md` as the local layout compatibility result.
2. Use `artifacts/layout/vlsat/report.md` as the latest checker output.
3. Use `21_eval_path.md` as the faithful eval path decision.
4. Do not implement calibration until prediction export and geometry join are validated.
