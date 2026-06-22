# V11 Proximity Feasibility

Date: 2026-06-22 KST

## Purpose

v9에서 exact endpoint-pair route가 diagnostic-only로 고정된 뒤, `close by` /
`proximity`를 H002의 relation-family expansion target으로 사용할 수 있는지 train-only로
검사했다.

이 stage의 질문은 posterior 성능이 아니라 다음과 같다.

```text
Can proximity provide a less shortcut-dominated target pool for H002?
Is it bidirectional HL/LH, or only useful as an LH branch?
```

## Artifact

```text
artifacts/train_rga_full/open3dsg_train_full/rga/
  reliability_target_v10_proximity_relation_family_feasibility_scan/
    summary.json
    report.md
    feasibility_counts.csv
    shortcut_risks.json
    preview_candidates.jsonl
    validation_errors.jsonl
```

Validation errors: `0`

Validation/test usage: `false`

Posterior smoke: `blocked`

## Result

```text
status = h002_reliability_target_v10_proximity_feasibility_lh_only_ready_not_bidirectional
total_proximity_rows = 185346
queue_proximity_rows = 171324
RGA-HL proximity rows = 0
RGA-LH proximity rows = 171324
strict_lh_pool_rows = 50966
preview_rows = 240
```

`close by` / proximity는 전체 train row 수량과 LH 후보 수량은 충분하다. 하지만 현재 RGA
queue 기준에서는 `RGA-HL` proximity row가 없고, 사실상 `RGA-LH` 중심이다.

따라서 proximity는 현재 상태에서 양방향 semantic-geometry mismatch target이 아니다. 대신
다음과 같은 scoped target으로는 가능하다.

```text
low semantic + high geometry proximity:
  true underconfidence
  dense proximity noise
  annotation sparsity
  alternative relation on same pair
```

## Main Counts

Full train proximity summary:

```text
rga_top100 = {'RGA-HH': 2, 'RGA-LH': 171324, 'RGA-LL': 6692, 'RGA-LU': 7328}
geometry_status = {'satisfied': 171326, 'uncertain': 7328, 'unsatisfied': 6692}
label_match_status = {'exact_match': 9528, 'no_gt_for_pair': 142571, 'pair_has_other_predicate': 33247}
```

Strict LH pool after excluding structural/generic endpoint pairs:

```text
rows = 50966
exact_match = 8286
pair_has_other_predicate = 13418
no_gt_for_pair = 29262
```

Preview candidate selection:

```text
selected_rows = 240
exact_match = 80
pair_has_other_predicate = 80
no_gt_for_pair = 80
unique_scans = 106
unique_label_pairs = 173
max_rows_per_scan = 4
max_rows_per_label_pair = 8
```

## Shortcut Risk

The strict LH pool still has shortcut risks:

```text
machine_hint -> label_match_status majority accuracy = 1.0000
subject_object_label_pair -> label_match_status majority accuracy = 0.7621
scan_id -> label_match_status majority accuracy = 0.6145
rank_band -> label_match_status majority accuracy = 0.5742
baseline = 0.5741
```

Interpretation:

- `machine_hint` is a target-construction/audit field and must never become model input.
- object-pair and scan effects are still nontrivial, so label fill or posterior smoke should not start automatically.
- rank band is not the dominant shortcut in this proximity LH-only pool.

## Decision

Proximity is feasible as a train-only LH-only diagnostic/repair branch, but not as a
bidirectional target under the current RGA queues.

Next gate:

```text
reliability_target_v10_proximity_lh_only_path_decision
```

The next decision should choose one of:

```text
1. accept LH-only proximity as a scoped target-repair branch;
2. mine or construct a separate high-semantic/low-geometry proximity source;
3. keep proximity as diagnostic-only and return to support/vertical target repair.
```

Posterior smoke remains blocked until this path decision and a target-independence audit pass.
