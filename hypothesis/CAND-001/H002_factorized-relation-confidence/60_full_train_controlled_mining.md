# H002 Full Train Controlled Mining

Last updated: 2026-06-16

## Purpose

`59_full_train_rga_rows.md`에서 만든 full-train `RGA-HL` / `RGA-LH` queue를
posterior 학습에 바로 쓰지 않고, 통제된 label/audit 후보군으로 압축한다.

핵심 목적:

- full train의 큰 mismatch mass를 사람이 검토 가능한 크기로 줄인다.
- `queue_kind`, relation family, predicate, label status, rank band shortcut을
  최대한 통제한다.
- `RGA-HL`과 `RGA-LH`를 모두 포함해 bidirectional mismatch를 유지한다.
- `proposed_audit_role`을 label로 쓰지 않고 sampling/audit prior로만 둔다.
- validation/test row는 계속 사용하지 않는다.

## Decision

Current status:

```text
full_train_controlled_audit_candidates_ready
```

Meaning:

```text
Full-train HL/LH queues have enough balanced candidate rows for controlled
audit. This is not a posterior training target yet because review fields are
blank and proposed audit roles are not labels.
```

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_controlled_label_mining.py
```

The tool reads only compact queue files:

```text
train_hl_queue.jsonl
train_lh_queue.jsonl
```

It does not reread or duplicate the 17G `match_rows.jsonl`.

## Command

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_controlled_label_mining.py
```

Result:

```text
status=ready_for_controlled_audit candidates=360 hl=83 lh=277
```

## Sampling Contract

Stratum key:

```text
queue_kind
predicate_family
predicate_label
label_match_status
rank_band
```

Default caps:

| Queue | Cap |
| --- | ---: |
| `HL` | 8 rows per stratum |
| `LH` | 4 rows per stratum |
| global | 700 rows |

Selection rule:

```text
within each stratum, scan-round-robin deterministic sampling
```

Reason:

- prevents one scan from dominating the review queue.
- prevents `close by` dense proximity rows from dominating the candidate set.
- keeps exact/family/pair/no-GT label states visible.
- preserves both semantic-overconfidence and semantic-underconfidence axes.

## Output Artifacts

Output root:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_mining/
```

Files:

| Artifact | Purpose | Size |
| --- | --- | ---: |
| `candidate_pool.jsonl` | normalized candidate rows | 887K |
| `candidate_sheet.tsv` | review sheet with blank labels | 260K |
| `strata_summary.csv` | available/selected count per stratum | 6K |
| `protocol.json` | allowed labels and review fields | 2K |
| `summary.json` | machine-readable summary | 27K |
| `report.md` | human-readable report | 2K |

## Candidate Distribution

Total selected candidates:

```text
360 rows across 92 scans
```

By queue:

| Queue | Rows |
| --- | ---: |
| `HL` | 83 |
| `LH` | 277 |

By family:

| Queue / Family | Rows |
| --- | ---: |
| `HL / support_contact` | 57 |
| `HL / relative_vertical` | 26 |
| `LH / support_contact` | 144 |
| `LH / relative_vertical` | 88 |
| `LH / proximity` | 45 |

Families with both HL and LH candidates:

```text
relative_vertical
support_contact
```

By label status:

| Queue / Label Status | Rows |
| --- | ---: |
| `HL / exact_match` | 1 |
| `HL / family_match` | 20 |
| `HL / pair_has_other_predicate` | 28 |
| `HL / no_gt_for_pair` | 34 |
| `LH / exact_match` | 74 |
| `LH / family_match` | 48 |
| `LH / pair_has_other_predicate` | 78 |
| `LH / no_gt_for_pair` | 77 |

By rank band:

| Queue / Rank Band | Rows |
| --- | ---: |
| `HL / top50` | 31 |
| `HL / top100_only` | 52 |
| `LH / rank_101_200` | 73 |
| `LH / rank_201_500` | 87 |
| `LH / rank_501_1000` | 73 |
| `LH / rank_gt1000` | 44 |

## Proposed Audit Roles

These roles are sampling priors, not labels.

| Role | Rows |
| --- | ---: |
| `hl_exact_label_geometry_contradiction` | 1 |
| `hl_family_match_geometry_contradiction` | 20 |
| `hl_wrong_predicate_geometry_contradiction` | 28 |
| `hl_no_gt_geometry_contradiction` | 34 |
| `lh_exact_label_underconfidence` | 74 |
| `lh_family_match_granularity` | 48 |
| `lh_alternative_relation_on_gt_pair` | 78 |
| `lh_no_gt_proximity_dense_or_sparse` | 16 |
| `lh_no_gt_support_contact_missing_or_noise` | 36 |
| `lh_no_gt_vertical_sparse_or_trivial` | 25 |

## Interpretation

이 결과는 full train에서 H002 controlled audit을 진행할 후보가 충분하다는 뜻이다.
특히 pilot에서 부족했던 문제를 일부 줄인다.

Improved:

- binary-audit 후보 수가 150 row 기준을 넘는다.
- `HL >= 50`, `LH >= 50` 기준을 넘는다.
- `support_contact`와 `relative_vertical`에서 HL/LH 양방향 후보가 모두 있다.
- `LH exact/family`가 122 rows 있어 true underconfidence 후보를 더 많이 검토할 수
  있다.
- `LH no-GT`도 77 rows 남겨 annotation sparsity와 dense noise를 분리할 수 있다.

Still not established:

- human-confirmed labels.
- independent blind labels.
- posterior target readiness.
- factorized posterior advantage.
- validation/test performance.

## Boundary

Important:

```text
proposed_audit_role != final_controlled_label
```

The following shortcuts are forbidden:

- `queue_kind`를 label로 직접 쓰는 것.
- `predicate_family` majority를 label로 쓰는 것.
- rank band를 positive/negative label로 쓰는 것.
- `p_geom_valid` threshold를 reliability label로 쓰는 것.

Multi-view / mesh / point-cloud evidence is allowed only as audit confirmation
evidence at this stage. It is not yet a deployable model input `V_mv_e`.

## Verification

Checks performed:

```text
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_controlled_label_mining.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_controlled_label_mining.py
```

Completion conditions:

| Check | Result |
| --- | --- |
| validation/test used | false |
| output rows | 360 |
| HL rows | 83 |
| LH rows | 277 |
| unique scans | 92 |
| families with both axes | 2 |
| compact output only | true |

## Next TODO

Completed next action:

```text
full_train_controlled_label_readiness
```

Result:

```text
61_full_train_label_readiness.md
```

Original goal:

- validate the full-train candidate sheet schema.
- confirm that blank labels are not accidentally treated as targets.
- define the minimum readiness gate for filled full-train labels.
- prepare a later `codex_ver` or independent blind fill only if the user chooses
  to treat bootstrap labels as hypothesis-stage targets.
