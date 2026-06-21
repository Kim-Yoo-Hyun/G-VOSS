# H002 Full-Train Independent Support/Vertical V2 True User Review Target Path Decision

## Purpose

`109_full_train_independent_support_vertical_v2_true_user_review_target_independence_audit.md`에서
Codex-proxy pending-confirmation true-user-review target도 strict relation-reliability
slice를 만들지 못했다. 이번 단계는 실패 원인을 posterior 결합 방식 문제와
target/evidence 요소 문제로 분리하고, 다음 경로를 고정한다.

핵심 질문:

```text
Should H002 improve the posterior combiner now, revise the proxy target again,
or collect genuinely independent labels first?
```

## Direct Answer

현재 blocker는 posterior 결합 방식보다 결합을 검증할 target/evidence 요소의 독립성
문제다.

즉, `P(edge reliability | semantic evidence, geometry evidence, coverage, uncertainty)`
의 결합 함수를 더 강하게 만드는 것이 먼저가 아니다. 지금은 그 posterior가 맞춰야 할
`relation reliability target`이 hidden prior carryover에서 독립적이지 않다.

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- H001 artifact를 사용하거나 수정하지 않는다.
- Codex-proxy labels는 method-validation evidence가 아니다.
- combiner upgrade는 clean target 전까지 진행하지 않는다.
- multi-view는 audit evidence이며 model input이 아니다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_target_path_decision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_target_path_decision.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_true_user_review_target_path_decision_collect_real_independent_labels
decision=collect_real_independent_labels_on_rank_band70_first
relation_rows=70
relation_pos=35
relation_neg=35
relation_strict=none
relation_construction=rank_band_balanced_true_user_review
geometry_pos=69
geometry_neg=1
posterior_allowed=False
validation_used=False
test_used=False
next=collect_real_user_labels_on_rank_band70_sheet
```

## Element Failure Matrix

| Element | Problem | Why Combiner Does Not Fix It | Required Fix |
| --- | --- | --- | --- |
| `geometry_validity_target` | 69/1에 가까운 single-class target이라 discrimination target으로 약하다. | 어떤 combiner도 거의 항상 positive인 target에서 geometry validity 구분 능력을 검증할 수 없다. | contradiction/uncertain 사례를 독립 label로 확보하거나 geometry target을 posterior main target에서 제외한다. |
| `relation_reliability_target` | `relation_validity_label_hidden`, `label_use_hidden`, `posterior_target_y_hidden` carryover가 남았다. | 성능이 좋아도 relation evidence 결합이 아니라 hidden prior structure 재현일 수 있다. | prior labels를 보지 않은 실제 독립 reviewer label을 확보하고 다시 target-independence audit을 수행한다. |
| `label_source` | 현재 label은 Codex-proxy pending-confirmation이며 실제 true user/external annotation이 아니다. | label source가 독립적이지 않으면 model score를 해석할 ground truth가 없다. | 기존 blank review sheet를 실제 user/external reviewer가 packet evidence만 보고 채운다. |
| `candidate_selection` | rank/queue/geometry-status construction axis는 통제됐지만 prior relation-label axis가 target과 연결된다. | balanced construction slice는 plumbing diagnostic일 뿐 method-validation target이 아니다. | prior-label-balanced sample을 충분한 size로 확장하거나 real labels로 carryover를 재검증한다. |
| `deployable_feature_join` | source score/rank와 `p_geom_valid` feature join은 아직 target audit 이후로 미뤄져 있다. | clean target 없이 feature를 join하면 feature gain과 target shortcut이 섞인다. | strict/defensible target이 생긴 뒤에만 semantic/geometric feature join과 posterior smoke를 연다. |

## Option Matrix

| Option | Verdict | Reason |
| --- | --- | --- |
| `run_posterior_smoke_now` | `reject` | strict relation-reliability slice가 없고 hidden prior carryover가 남아 있다. |
| `upgrade_combiner_now` | `reject` | 현재 blocker는 combiner capacity가 아니라 target/evidence contract다. |
| `use_rank_band_balanced_true_user_review` | `diagnostic_only` | 70 rows 35/35이지만 harmful prior risk 3개가 남아 method evidence가 아니다. |
| `revise_codex_proxy_target_again` | `defer` | 여러 proxy target pass가 같은 hidden prior carryover를 반복했다. |
| `collect_real_independent_labels_on_rank_band70` | `select` | 기존 packet/sheet가 준비되어 있고, target independence 문제를 직접 해결하는 경로다. |
| `expand_to_full127_after_real_first_pass` | `conditional` | rank_band70 실제 label도 strict slice가 없거나 class count가 부족하면 full127로 확장한다. |

## Decision

선택:

```text
collect_real_independent_labels_on_rank_band70_first
```

판단:

- posterior 결합 방식은 아직 검증 대상이 아니다.
- 현재 blocker는 target/evidence 요소가 hidden prior carryover에서 충분히 독립적이지 않다는 점이다.
- 이 문제를 직접 해결하려면 기존 `rank_band70` packet을 실제 독립 reviewer가 다시 label해야 한다.
- Codex-proxy label을 더 수정하는 것은 main path로 두지 않는다.

## Real Label Collection Packet

| Item | Path / Count |
| --- | --- |
| review sheet | `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/true_user_review_sheet_rank_band70.tsv` |
| review sheet rows + header | 71 |
| reviewer instructions | `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/reviewer_instructions.md` |
| post-label manifest, audit only | `hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_path/true_user_manifest_rank_band70_post_label_only.jsonl` |
| post-label manifest rows | 70 |

The reviewer must not use:

- semantic score/rank
- `p_geom_valid`
- geometry status
- prior relation validity labels
- previous Codex proxy labels
- posterior target fields
- hidden manifest fields

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/110_full_train_independent_support_vertical_v2_true_user_review_target_path_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_target_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_path_decision/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_path_decision/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_path_decision/element_failure_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_path_decision/option_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_true_user_review_target_path_decision/real_label_collection_request.md
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_target_path_decision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_true_user_review_target_path_decision.py
```

Observed:

```text
posterior_allowed=False
validation_used=False
test_used=False
review_sheet_rows_plus_header=71
post_label_manifest_rows=70
```

## Next TODO

Current next action:

```text
completed_by_111_112_user_submitted_sheet_ingestion_and_audit
```

Goal:

- `111_full_train_independent_support_vertical_v2_user_submitted_review_ingestion.md`
  ingests the completed 70-row sheet.
- `112_full_train_independent_support_vertical_v2_user_submitted_review_target_independence_audit.md`
  audits the resulting targets.
- posterior smoke remains blocked because no strict or construction-only controlled slice exists.
- reviewer-id provenance remains caveated because the sheet uses
  `codex_packet_only_diagnostic`.
- next active TODO is `confirm_reviewer_independence_or_collect_external_labels`.
