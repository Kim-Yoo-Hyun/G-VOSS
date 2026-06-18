# H002 Full-Train Independent Support/Vertical Label Ingestion

## Purpose

이 문서는 86번에서 채운 selected `support_contact + relative_vertical`
`(codex_ver)` bootstrap labels를 label-lock 이후 hidden provenance와 조인해
posterior smoke 전에 사용할 train-only target artifact로 materialize한다.

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- label은 human-confirmed가 아니라 Codex bootstrap label이다.
- hidden internal reference는 label-lock 이후에만 join한다.
- hidden target-construction metadata는 audit-only이며 posterior input이 아니다.
- source score/rank와 `p_geom_valid`는 labeler에게 숨겼지만, label-lock 이후
  deployable evidence candidate로만 보존한다.
- `proximity`는 main ingestion path에서 제외하고 risk slice로만 보존한다.
- multi-view는 audit evidence pointer일 뿐 posterior input이 아니다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_ingestion.py
```

Observed:

```text
status=full_train_independent_support_vertical_label_ingested_with_target_risk
validation_used=False
labels=127
binary=114
positive=40
negative=74
excluded=13
errors=0
probe=target_independence_risk_hidden_metadata_correlated
next=full_train_independent_support_vertical_target_independence_audit
```

## Validation Checks

Ingestion에서 확인한 조건:

- completed sheet required fields 존재.
- completion schema allowed value 준수.
- duplicate `blind_review_id` 없음.
- completed sheet와 internal reference의 selected IDs가 1:1로 일치.
- internal reference rows는 `post_label_join_only=true`.
- proximity risk slice IDs가 selected support/vertical IDs와 겹치지 않음.
- selected rows의 family는 `support_contact` 또는 `relative_vertical`.
- proximity risk slice의 family는 `proximity`.
- fill summary가 hidden reference, source score/rank, `p_geom_valid`,
  `geometry_status`를 label fill에서 읽지 않았음을 확인.

결과:

```text
ingestion_errors = 0
```

## Counts

| Item | Count |
| --- | ---: |
| completed sheet rows | 127 |
| internal reference rows | 127 |
| proximity risk slice rows | 31 |
| validated labels | 127 |
| binary targets | 114 |
| positive targets | 40 |
| negative targets | 74 |
| excluded rows | 13 |
| positive rate among binary | 0.3509 |

## Target Probe

Basic post-label probe 결과:

```text
probe = target_independence_risk_hidden_metadata_correlated
```

Top hidden risks:

| Hidden Key | NMI | Majority Acc | Pos Rate Range |
| --- | ---: | ---: | ---: |
| `relation_validity_label_hidden` | 0.5710 | 0.8421 | 0.9583 |
| `label_use_hidden` | 0.4506 | 0.8333 | 0.6667 |
| `rank_band_hidden` | 0.2128 | 0.6930 | 0.7778 |
| `proposed_audit_role_hidden` | 0.1672 | 0.6491 | 0.5000 |
| `queue_kind_hidden` | 0.1634 | 0.6491 | 0.4376 |
| `geometry_status_hidden` | 0.1634 | 0.6491 | 0.4376 |

해석:

- ingestion 자체는 성공했다.
- 하지만 target 자체는 아직 posterior smoke에 바로 넣기에는 위험하다.
- 특히 `relation_validity_label_hidden`과 `label_use_hidden`은 이전 bootstrap
  target에 가까운 metadata라서, 독립 target이라고 주장하려면 반드시 제거하거나
  controlled slice를 구성해야 한다.
- 따라서 이 단계의 결론은 `label ingestion complete, posterior smoke not yet allowed`다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_ingestion.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/validated_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/multiclass_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/posterior_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/target_independence_probe.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/target_group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/shortcut_audit.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_ingestion_codex_ver/ingestion_errors.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_ingestion.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_ingestion.py
```

Observed:

```text
errors=0
validation_used=False
binary=114
positive=40
negative=74
probe=target_independence_risk_hidden_metadata_correlated
```

Line counts:

```text
validated_labels.jsonl = 127
binary_targets.jsonl = 114
multiclass_targets.jsonl = 127
posterior_rows.jsonl = 114
ingestion_errors.jsonl = 0
```

## Follow-Up Status

The next action from this document has been completed:

```text
full_train_independent_support_vertical_target_independence_audit
```

Observed follow-up:

```text
status=full_train_independent_support_vertical_target_independence_audit_strict_blocked_construction_slice_available
validation_used=False
rows=114
positive=40
negative=74
errors=0
strict=none
construction=rank_band_balanced_codex_ver
```

## Next TODO

Next action:

```text
full_train_independent_support_vertical_label_policy_revision
```

Goal:

- prior-label carryover를 줄이는 label policy를 설계한다.
- posterior smoke를 method evidence로 진행하기 전에 strict target을 다시 만든다.
