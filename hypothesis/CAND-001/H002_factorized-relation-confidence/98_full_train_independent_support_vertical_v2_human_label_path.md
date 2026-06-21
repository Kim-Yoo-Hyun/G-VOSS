# H002 Full-Train Independent Support/Vertical V2 Human Label Path

## Purpose

`97_full_train_independent_support_vertical_v2_independent_target_independence_audit.md`에서
Codex independent visible-only target도 strict relation-reliability target을 만들지
못한다는 것을 확인했다. 이번 단계는 다음 경로를 결정하고, human-confirmed label
collection을 시작할 수 있는 sheet/schema/manifest를 만든다.

핵심 질문:

```text
Should H002 keep revising Codex-derived targets, or move to human-confirmed
support/vertical labels before any posterior smoke?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- Codex labels는 bootstrap estimate일 뿐 paper evidence가 아니다.
- labeler-visible sheet에는 hidden metadata, prior label/use, v2 Codex axes,
  semantic score/rank, `p_geom_valid`, `geometry_status`, posterior target을 노출하지
  않는다.
- multi-view/mesh/contact-sheet path는 audit evidence pointer이며 model input이 아니다.
- 이번 단계는 human labels를 채운 것이 아니라, human-confirmed label collection path를
  고정한 것이다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_path_decision.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_human_label_path_decision_collect_human_confirmed_labels
validation_used=False
test_used=False
min_rows=96
min_est_binary=81
min_est_pos=32
min_est_neg=49
full_rows=127
full_est_binary=102
leakage=0
next=full_train_independent_support_vertical_v2_human_label_fill_or_external_review
```

## Decision

선택:

```text
collect_human_confirmed_labels
```

판단:

- 또 다른 Codex-derived target revision을 main path로 두지 않는다.
- `rank_band_balanced_independent`는 diagnostic slice일 뿐 method evidence가 아니다.
- 현재 blocker는 posterior combiner capacity가 아니라 target independence다.
- human-confirmed label을 받은 뒤에만 ingestion과 target-independence audit을 다시 수행한다.

## Batch Plan

Recommended:

```text
full_human_batch_127
```

Reason:

- 전체가 127 rows로 작다.
- estimated binary rows가 102개라 hypothesis-stage gate를 더 안정적으로 넘는다.
- class count, uncertainty, hidden carryover audit에서 minimum batch보다 안전하다.

Acceptable first pass:

```text
minimum_human_batch_96
```

Reason:

- 62-row `rank_band_balanced_independent` diagnostic slice에서 시작한다.
- 34 rows를 추가해 family/predicate/prior-label/rank-band coverage를 보강한다.
- bootstrap estimate 기준 relation binary 81, positive 32, negative 49로
  hypothesis-stage minimum을 넘는다.
- 단, target-independence audit이 실패하면 127-row full batch로 확장해야 한다.

## Minimum Gate

| Gate | Value |
| --- | ---: |
| hypothesis-stage usable binary rows | 60 |
| hypothesis-stage per-class rows | 20 |
| minimum human batch rows | 96 |
| full human batch rows | 127 |

주의:

```text
This is a hypothesis-stage target gate, not a paper-level posterior gate.
```

이전 broad posterior revival gate는 `>=150` binary rows를 요구한다. 현재
support/vertical 127-row batch는 H002 target independence를 검증하기 위한 scoped gate다.

## Bootstrap Estimates

이 숫자는 `(codex_independent_ver)` label을 사용한 planning estimate다. Labeler-visible
field가 아니며 paper evidence가 아니다.

| Batch | Rows | Est. Binary | Est. Pos | Est. Neg | Est. Uncertain |
| --- | ---: | ---: | ---: | ---: | ---: |
| `minimum_human_batch_96` | 96 | 81 | 32 | 49 | 15 |
| `full_human_batch_127` | 127 | 102 | 32 | 70 | 25 |

Batch composition:

| Batch | support_contact | relative_vertical |
| --- | ---: | ---: |
| `minimum_human_batch_96` | 48 | 48 |
| `full_human_batch_127` | 72 | 55 |

## Option Matrix

| Option | Verdict | Reason |
| --- | --- | --- |
| `revise_codex_target_again` | `reject_as_main_path` | v1, v2 factual-axis target, and codex-independent visible-only target all failed strict independence gates |
| `use_rank_band_balanced_independent_for_method_evidence` | `reject_for_method_evidence` | construction risk is reduced but harmful prior carryover remains |
| `collect_minimum_human_batch_96` | `acceptable_first_batch` | lower labeling cost and estimated per-class count clears hypothesis minimum; must expand if audit fails |
| `collect_full_human_batch_127` | `recommended` | small enough to label fully and most robust against class-count/uncertainty/independence risk |
| `add_multi_view_as_model_input_now` | `defer` | multi-view remains audit evidence until target independence passes |

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/98_full_train_independent_support_vertical_v2_human_label_path.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_path_decision_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_path_decision_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_path_decision_codex_ver/human_collection_schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_path_decision_codex_ver/minimum_human_collection_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_path_decision_codex_ver/full_human_collection_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_path_decision_codex_ver/minimum_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_path_decision_codex_ver/full_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_path_decision_codex_ver/sampling_plan.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_human_label_path_decision_codex_ver/labeler_header_leakage_hits.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_path_decision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_human_label_path_decision.py
```

Line counts:

```text
minimum_human_collection_sheet.tsv = 96 rows + header
full_human_collection_sheet.tsv = 127 rows + header
minimum_manifest_post_label_only.jsonl = 96
full_manifest_post_label_only.jsonl = 127
labeler_header_leakage_hits.jsonl = 0
```

## Next TODO

Next action:

```text
completed_by_99_full_train_independent_support_vertical_v2_human_label_fill
```

Goal:

- The requested Codex proxy fill was completed in
  `99_full_train_independent_support_vertical_v2_human_label_fill.md`.
- The next active H002 action after fill/ingestion is
  `full_train_independent_support_vertical_v2_human_target_independence_audit`.
