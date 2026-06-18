# H002 Independent Label Ingestion

Last updated: 2026-06-14

## Purpose

`46_independent_label_protocol.md`에서 만든 blind sheet를 실제 posterior target으로
쓰기 전에, completed label이 schema-valid인지 확인하고 `internal_key.jsonl`에
join하는 ingestion layer를 고정한다.

이번 단계의 목적은 모델을 학습하는 것이 아니다. 목적은 rank-hidden audit label이
들어왔을 때 다음을 보장하는 것이다.

- blind sheet에 forbidden header가 노출되지 않았는지 확인한다.
- required label field가 모두 채워졌는지 확인한다.
- allowed label taxonomy만 posterior target으로 materialize한다.
- hidden provenance는 post-label analysis용으로만 join한다.
- validation/test row를 사용하지 않는다.

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/independent_label_ingestion.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/independent_label_ingestion.py
```

Result:

```text
status=independent_label_ingestion_waiting_for_completed_labels completed=0 binary=0 errors=0 validation_used=False
```

## Boundary

- Train-only hypothesis-stage ingestion.
- No validation/test rows are used.
- No posterior is trained in this stage.
- `V_mv_e` remains audit evidence only, not model input.
- Hidden fields are joined only after label completion.
- Hidden provenance must not become deployable posterior features.

## Input Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_all_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/internal_key.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/protocol.json
```

Current input counts:

| Item | Count |
| --- | ---: |
| blind sheet rows | 87 |
| internal key rows | 87 |
| completed label rows | 0 |

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/validated_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/multiclass_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_ingestion/ingestion_errors.jsonl
```

## Validation Checks

Forbidden blind-sheet header fragments:

```text
score
rank
working_label
p_geom
geometry_status
queue
prediction_id
```

Required completion fields:

```text
reviewer_id
review_round
relation_validity_label
confidence
```

Allowed binary mapping:

| Binary use | Labels |
| --- | --- |
| positive | `reliable_informative`, `annotation_sparsity_candidate` |
| negative | `valid_but_trivial_dense`, `invalid_relation`, `invalid_pair`, `visibility_or_geometry_artifact` |
| exclude or multiclass only | `ontology_mismatch`, `abstain_uncertain` |

## Current Result

Current status:

```text
independent_label_ingestion_waiting_for_completed_labels
```

Counts:

| Item | Count |
| --- | ---: |
| completed label rows | 0 |
| binary target rows | 0 |
| multiclass target rows | 0 |
| ingestion errors | 0 |

Interpretation:

```text
The ingestion protocol is executable and leakage checks pass, but the blind
sheet has no completed labels yet. No residual/gated combiner diagnostic should
run until rank-hidden labels are filled.
```

## Claim Boundary

Allowed:

- claim that the blind label ingestion path is ready.
- claim that the current blank sheet has no schema/header leakage errors.
- use the generated schema as the contract for future independent labels.

Blocked:

- posterior method claim.
- factorized posterior advantage claim.
- human/independent label evidence claim.
- multi-view deployable input claim.

## Decision

Current decision:

```text
independent_label_ingestion_waiting_for_completed_labels
```

Meaning:

```text
H002 cannot continue to residual/gated combiner diagnostics until the
rank-hidden blind sheet has completed labels.
```

## Next TODO

Next document:

```text
48_blind_label_fill.md
```

Goal:

- fill `blind_all_sheet.tsv` or the family-specific blind sheets under the
  rank-hidden protocol.
- keep `(codex_ver)` or human reviewer identity explicit.
- rerun `independent_label_ingestion.py` on the completed sheet.
- require nonzero binary target rows before residual/gated combiner diagnostics.
- continue using only train-pilot rows.
