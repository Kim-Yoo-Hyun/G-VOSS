# H002 Full-Train Independent Support/Vertical V2 Target Path Decision

## Purpose

`93_full_train_independent_support_vertical_v2_target_independence_audit.md`에서
strict relation-reliability slice가 없고, construction-only diagnostic slice만 남는
것을 확인했다. 이번 단계의 목적은 다음 경로를 결정하는 것이다.

핵심 질문:

```text
Should H002 revise another Codex/rule-derived target, or collect stronger
independent labels before posterior smoke?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- 현재 construction-only slice는 method evidence가 아니다.
- multi-view는 model input이 아니라 independent label audit evidence로만 둔다.
- labeler-visible sheet에는 hidden metadata, v2 Codex axes, semantic score/rank,
  `p_geom_valid`, `geometry_status`, prior label/use, posterior target을 노출하지 않는다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_target_path_decision.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_target_path_decision_collect_independent_labels
validation_used=False
test_used=False
collection_rows=127
support=72
vertical=55
construction_rows=62
leakage=0
next=full_train_independent_support_vertical_v2_independent_label_fill_or_human_review
```

## Decision

Selected path:

```text
collect_stronger_independent_labels
```

Reason:

```text
The blocker is target independence, not combiner capacity.
```

현재 v2 target은 구조적으로는 좋아졌다. `geometry_validity_target_v2`와
`relation_reliability_target_v2`가 분리됐고, expected geometry alignment와 harmful
prior-label carryover도 분리해서 볼 수 있다. 하지만 relation reliability strict slice가
없으므로 posterior smoke를 method evidence로 진행하면 안 된다.

## Option Matrix

| Option | Verdict | Reason |
| --- | --- | --- |
| `run_posterior_on_current_v2_target` | `reject` | strict relation-reliability slice가 없다. |
| `use_rank_band_balanced_v2_for_method_evidence` | `reject_for_method_evidence` | construction risk는 줄었지만 harmful prior carryover가 남아 있다. |
| `revise_rule_based_codex_target_again` | `defer` | 같은 Codex/witness-derived target은 prior-label carryover를 반복할 가능성이 높다. |
| `collect_stronger_independent_labels` | `select` | 독립 target 없이는 posterior quality를 판단할 수 없다. |
| `add_multi_view_as_model_input_now` | `defer` | clean target 없이 feature를 늘리면 target shortcut과 feature gain이 섞인다. |

## Collection Packet

Labeler-visible sheet:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_path_decision_codex_ver/independent_collection_sheet.tsv
```

Internal post-label manifest:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_path_decision_codex_ver/internal_manifest_post_label_only.jsonl
```

Counts:

| Item | Count |
| --- | ---: |
| collection rows | 127 |
| support_contact rows | 72 |
| relative_vertical rows | 55 |
| relation construction-slice rows included | 62 |
| labeler header leakage hits | 0 |

Labeler-visible completion fields:

```text
endpoint_identity_independent
pair_evaluability_independent
geometry_validity_independent
relation_reliability_independent
primary_reason_independent
uncertainty_reason_independent
label_notes_independent
```

The independent labeler does not see:

```text
semantic score/rank
p_geom_valid
geometry_status
prior relation_validity_label
prior label_use
posterior target
v2 Codex factual axes
construction queue/rank/role metadata
```

## Interpretation

이번 단계의 결론은 다음과 같다.

```text
Do not revise the rule-based target again as the main next step.
Prepare independent relation-reliability labels, then rerun ingestion and
target-independence audit.
```

이 판단은 H002 방향을 억지로 맞추는 것이 아니라, 실패 원인에 맞춰 다음 실험 조건을
수정하는 것이다. 현재 실패 원인은 combiner가 약해서가 아니라 target이 독립적이지
않다는 점이다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_target_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_path_decision_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_path_decision_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_path_decision_codex_ver/option_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_path_decision_codex_ver/independent_collection_schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_path_decision_codex_ver/independent_collection_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_path_decision_codex_ver/internal_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_target_path_decision_codex_ver/labeler_header_leakage_hits.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_target_path_decision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_target_path_decision.py
```

Observed:

```text
validation_used=False
test_used=False
collection_rows=127
leakage=0
```

Additional check:

```text
independent_collection_sheet.tsv forbidden header hits = 0
```

## Next TODO

Next action:

```text
full_train_independent_support_vertical_v2_independent_label_ingestion
```

Goal:

- independent label fill은 `95_full_train_independent_support_vertical_v2_independent_label_fill.md`에서
  `(codex_independent_ver)` bootstrap으로 완료됐다.
- internal manifest를 label lock 이후에만 join한다.
- independent geometry validity와 relation reliability target을 derive한다.
- strict target-independence audit을 다시 수행한다.
- keep posterior smoke blocked until strict relation-reliability target evidence exists.
