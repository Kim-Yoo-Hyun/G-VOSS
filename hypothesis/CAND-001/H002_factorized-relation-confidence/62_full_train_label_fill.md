# H002 Full Train Label Fill

Last updated: 2026-06-16

## Purpose

`61_full_train_label_readiness.md` 이후 full-train controlled candidate sheet를
`(codex_ver_full_train)` bootstrap label로 채운다.

이 단계의 목적:

- original blank candidate sheet를 보존한다.
- 별도 filled sheet를 만든다.
- train-only posterior smoke를 열 수 있는 최소 binary target을 만든다.
- label fill이 human-confirmed label이 아님을 명확히 기록한다.
- validation/test row는 계속 사용하지 않는다.

## Decision

Current status:

```text
full_train_codex_labels_ready_for_train_only_posterior_smoke
```

Meaning:

```text
The full-train controlled sheet now has `(codex_ver_full_train)` bootstrap
labels and passes the full-train readiness gate. This unlocks train-only
posterior smoke, but does not support a paper-level label or posterior claim.
```

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/fill_full_train_controlled_codex_labels.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/fill_full_train_controlled_codex_labels.py
```

Result:

```text
status=full_train_controlled_codex_labels_filled_not_human_confirmed rows=360 binary=173 positive=74 negative=99 excluded=187 validation_used=False
```

## Filled Artifacts

Original blank sheet preserved:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_mining/candidate_sheet.tsv
```

Filled sheet:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_mining/candidate_sheet_codex_ver.tsv
```

Label fill output:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_fill_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_fill_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_fill_codex_ver/labels.jsonl
```

## Bootstrap Label Policy

This fill is intentionally conservative.

Binary positive:

| Source | Final label | Target |
| --- | --- | ---: |
| `LH exact_match + geometry_satisfied` | `reliable_promote` | 1 |

Binary negative:

| Source | Final label | Target |
| --- | --- | ---: |
| `HL geometry contradiction` | `unreliable_dense_noise` | 0 |
| `LH no-GT proximity dense/sparse` | `unreliable_dense_noise` | 0 |

Excluded:

| Source | Final label | Reason |
| --- | --- | --- |
| `LH family_match` | `relabel_only` | predicate granularity, not clean binary |
| `LH pair_has_other_predicate` | `relabel_only` | alternative GT predicate on same pair |
| `LH no-GT support/vertical` | `abstain_uncertain` | needs visual or mesh confirmation |

Important caveat:

```text
unreliable_dense_noise is used as the available binary-negative final label.
The failure taxonomy still separates `semantic_overconfidence_invalid` from
`dense_relation_noise`.
```

## Counts

Filled rows:

| Item | Count |
| --- | ---: |
| total rows | 360 |
| binary usable rows | 173 |
| positive rows | 74 |
| negative rows | 99 |
| excluded rows | 187 |

Final label distribution:

| Final label | Rows |
| --- | ---: |
| `reliable_promote` | 74 |
| `unreliable_dense_noise` | 99 |
| `relabel_only` | 126 |
| `abstain_uncertain` | 61 |

Binary target by queue:

| Queue | Target 0 | Target 1 |
| --- | ---: | ---: |
| `HL` | 83 | 0 |
| `LH` | 16 | 74 |

Binary target by family:

| Family | Target 0 | Target 1 | Minority |
| --- | ---: | ---: | ---: |
| `support_contact` | 57 | 36 | 36 |
| `relative_vertical` | 26 | 24 | 24 |
| `proximity` | 16 | 14 | 14 |

## Readiness Recheck

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_controlled_label_readiness.py \
  --candidate-sheet hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_mining/candidate_sheet_codex_ver.tsv \
  --output-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_readiness_codex_ver
```

Result:

```text
status=ready_for_train_only_full_posterior_smoke rows=360 started=360 completed=360 binary=173 validation_used=False
```

Readiness output:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_readiness_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_readiness_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_readiness_codex_ver/binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_readiness_codex_ver/multiclass_review_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_readiness_codex_ver/invalid_rows.jsonl
```

Line counts:

| Artifact | Rows |
| --- | ---: |
| `labels.jsonl` | 360 |
| `candidate_sheet_codex_ver.tsv` | 360 + header |
| `binary_targets.jsonl` | 173 |
| `multiclass_review_rows.jsonl` | 360 |
| `invalid_rows.jsonl` | 0 |

Readiness gates:

| Gate | Result |
| --- | --- |
| schema valid | true |
| invalid values | 0 |
| incomplete started rows | 0 |
| usable binary rows >= 150 | true |
| positive rows >= 50 | true |
| negative rows >= 50 | true |
| binary rows per queue >= 50 | true |
| families with both classes >= 2 | true |
| per-family minority >= 15 in at least 2 families | true |

## Boundary

Established:

- full-train `(codex_ver_full_train)` labels are filled.
- all 360 rows have completed review fields.
- readiness passes for train-only posterior smoke.
- validation/test rows are not used.

Not established:

- human-confirmed labels.
- independent blind labels.
- paper-level label evidence.
- factorized posterior advantage.
- shortcut-free target independence.

Important:

```text
codex_ver_full_train label != human-confirmed label
```

The target still has shortcut risk:

- all `HL` binary rows are negative.
- `LH` has both positive and negative rows, but positive rows are exact-match
  underconfidence cases.
- next posterior smoke must include `queue_kind`, rank, family, predicate,
  label-status, and proposed-role proxy controls.

## Verification

Commands:

```bash
python3 -m py_compile \
  hypothesis/CAND-001/H002_factorized-relation-confidence/tools/fill_full_train_controlled_codex_labels.py \
  hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_controlled_label_readiness.py

python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/fill_full_train_controlled_codex_labels.py

python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_controlled_label_readiness.py \
  --candidate-sheet hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_mining/candidate_sheet_codex_ver.tsv \
  --output-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_readiness_codex_ver
```

## Next TODO

Completed next action:

```text
full_train_controlled_posterior_smoke
```

Result:

```text
63_full_train_posterior_smoke.md
```

Original goal:

- join `controlled_label_readiness_codex_ver/binary_targets.jsonl` with
  deployable full-train RGA features.
- compare `semantic_only`, `geometry_only`, `semantic_plus_geometry`, and
  `factorized_reliability_posterior`.
- include proxy controls for queue, rank, family, predicate, label status, and
  proposed audit role.
- report train-only grouped CV metrics and calibration.
- keep validation/test unavailable.
