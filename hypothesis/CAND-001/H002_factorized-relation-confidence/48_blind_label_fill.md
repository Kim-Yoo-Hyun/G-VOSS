# H002 Blind Label Fill

Last updated: 2026-06-14

## Purpose

`47_independent_label_ingestion.md` 이후의 다음 gate는 rank-hidden blind sheet에
completed labels를 채우는 것이다. 이 단계의 목적은 residual/gated combiner diagnostic을
재개할 수 있도록 independent-style binary target을 만드는 것이다.

이번 단계에서 중요한 수정이 있었다. `blind_all_sheet.tsv`의 column header는 hidden
field를 노출하지 않았지만, 기존 `contact_sheet` 이미지 안에는 source rank, source
score, geometry score, previous working label이 인쇄되어 있었다. 따라서 원본 contact
sheet를 그대로 보고 label을 채우면 `46_independent_label_protocol.md`의 rank-hidden
목적이 깨진다.

그래서 이번 단계는 다음 두 작업을 함께 수행했다.

1. reviewer-facing asset을 sanitized version으로 다시 생성한다.
2. sanitized blind sheet 위에서 `(codex_ver_blind)` bootstrap label을 채운다.

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/fill_independent_blind_codex_labels.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/fill_independent_blind_codex_labels.py
```

Result:

```text
status=independent_blind_codex_labels_filled rows=87 binary=75 positive=46 negative=29 excluded=12 validation_used=False
```

Then ingestion was rerun on the filled sheet:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/independent_label_ingestion.py \
  --completed-sheet hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_all_sheet_codex_ver.tsv \
  --output-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver
```

Result:

```text
status=independent_label_targets_ready completed=87 binary=75 errors=0 validation_used=False
```

## Boundary

- Train-only hypothesis-stage labels.
- No validation/test rows are used.
- The fill script reads the blind sheet only.
- The fill script does not read `internal_key.jsonl`.
- Hidden source rank, source score, geometry score, working label, queue, and
  proposed stratum are not used for label assignment.
- `(codex_ver_blind)` labels are bootstrap labels, not human-confirmed labels.
- These labels can support train-only combiner diagnostics.
- These labels cannot support paper-level human-label or posterior-advantage
  claims.

## Leakage Fix

Original issue:

```text
original contact_sheet images exposed hidden metadata inside the image canvas.
```

Fix:

- copied subject/object crop images to sanitized file names.
- generated new sanitized contact sheets from those crop images.
- replaced `contact_sheet`, `subject_image_1`, `subject_image_2`,
  `object_image_1`, and `object_image_2` paths in the sanitized and filled
  sheets.
- preserved original blind sheet unchanged.

Sanitized outputs:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_all_sheet_sanitized.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_support_contact_sheet_sanitized.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_proximity_sheet_sanitized.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_relative_vertical_sheet_sanitized.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_blind_codex_labels/sanitized_assets/
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_blind_codex_labels/sanitized_contact_sheets/
```

## Filled Label Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_all_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_support_contact_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_proximity_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_relative_vertical_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_blind_codex_labels/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_blind_codex_labels/labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_blind_codex_labels/report.md
```

Ingested target artifacts:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver/schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver/validated_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver/binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver/multiclass_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion_codex_ver/ingestion_errors.jsonl
```

## Counts

Fill result:

| Item | Count |
| --- | ---: |
| rows | 87 |
| sanitized contact sheets | 87 |
| binary-usable rows | 75 |
| positive rows | 46 |
| negative rows | 29 |
| excluded rows | 12 |

Label distribution:

| Label | Count | Binary Use |
| --- | ---: | --- |
| `reliable_informative` | 43 | positive |
| `annotation_sparsity_candidate` | 3 | positive |
| `valid_but_trivial_dense` | 27 | negative |
| `invalid_relation` | 2 | negative |
| `abstain_uncertain` | 12 | excluded |

Ingestion result:

| Item | Count |
| --- | ---: |
| completed label rows | 87 |
| binary target rows | 75 |
| multiclass target rows | 87 |
| errors | 0 |

## Labeling Policy

`(codex_ver_blind)` is a visible-metadata bootstrap label source. It uses:

- subject/object class labels.
- predicate label.
- predicate family.
- sanitized crop/contact-sheet paths.
- family-specific question.

It does not use:

- `internal_key.jsonl`.
- hidden source ranking fields.
- hidden geometry score fields.
- prior working labels.
- queue identity.
- proposed review stratum.

Family policy:

| Family | Positive Bias | Negative / Exclude Bias |
| --- | --- | --- |
| `support_contact` | plausible support surface or wall-mounted fixture | implausible support direction or uncertain support object |
| `proximity` | functionally meaningful proximity pair | dense/trivial close-by pair |
| `relative_vertical` | meaningful vertical ordering pair | ceiling/wall/floor-trivial relation or same-class ambiguity |

## Current Interpretation

This stage unblocks the next train-only diagnostic:

```text
independent_label_targets_ready
```

But the evidence level remains limited:

```text
codex_ver_blind label != human-confirmed label
```

Therefore H002 can now run residual/gated combiner smoke, but any result must be
reported as bootstrap hypothesis evidence, not paper-locked annotation evidence.

## Decision

Current decision:

```text
independent_label_targets_ready
```

Meaning:

```text
H002 has 75 binary-usable rank-hidden bootstrap targets and can proceed to
train-only independent combiner diagnostics.
```

## Next TODO

Next document:

```text
49_independent_combiner_smoke.md
```

Goal:

- join `independent_label_ingestion_codex_ver/binary_targets.jsonl` to deployable
  feature rows.
- compare `semantic_only`, `geometry_only`, `semantic_plus_geometry`,
  `factorized_reliability_posterior`, residual, and gated variants.
- include rank proxy controls and family-controlled slices.
- report AUPRC, AUROC, Brier, calibration, and pairwise diagnostics.
- continue using only train-pilot rows.
