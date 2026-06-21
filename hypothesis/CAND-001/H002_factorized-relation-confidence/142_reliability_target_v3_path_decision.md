# H002 Reliability Target V3 Path Decision

Date: 2026-06-20 KST

## Purpose

`141_reliability_target_v3_target_independence_audit.md`에서 v3 target이
`blocked_no_controlled_slice`로 막힌 뒤, posterior smoke를 진행할지, combiner를 바꿀지,
sampling/label contract를 다시 고칠지 결정한다.

핵심 질문:

```text
Should H002 run posterior smoke now, or rebuild the target pool so relation
reliability cannot be explained by object/endpoint shortcuts?
```

## Boundary

- Split: Open3DSG train-only.
- Validation/test rows: not used.
- Posterior training: not run.
- H001 artifacts: not modified.
- Multi-view remains audit/label evidence only, not model input.
- Current v3 labels are Codex proxy labels, not independent human annotation.

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_path_decision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_path_decision.py
```

Observed:

```text
status=h002_reliability_target_v3_path_decision_object_endpoint_controlled_sampling_first
selected=revise_v3_object_endpoint_controlled_sampling
posterior_allowed=False
validation_used=False
test_used=False
next=reliability_target_v3_object_endpoint_controlled_plan
```

## Decision

Selected path:

```text
revise_v3_object_endpoint_controlled_sampling
```

Decision:

```text
Do not run posterior smoke or upgrade the combiner. Keep v3 multi-axis labels,
but rebuild the next label pool with object/endpoint-controlled sampling because
the current target can be explained by endpoint and subject/object label shortcuts.
```

## Audit Extract

| Target | Rows | Positive | Negative | Strict Slice | Diagnostic Slice |
| --- | ---: | ---: | ---: | --- | --- |
| `relation_reliability_v3_binary_target` | 110 | 32 | 78 | `none` | `none` |
| `geometry_support_v3_binary_target` | 113 | 92 | 21 | `none` | `none` |
| `relation_usefulness_v3_binary_target` | 113 | 34 | 79 | `none` | `none` |

## Why Not Posterior Or Combiner Now

현재 문제는 posterior 결합 방식이 약하다는 것이 아니다. Target 자체가 endpoint pattern,
subject label, object label, rank/queue construction metadata와 얽혀 있다. 따라서 더 강한
combiner를 쓰면 더 좋은 방법이 되는 것이 아니라, shortcut을 더 잘 맞추는 모델이 될 수 있다.

특히 relation reliability target은 positive mass가 `32`개로 생겼지만, controlled slice가
없다. 이 상태에서 성능이 올라가도 그것이 `semantic evidence + geometry evidence + coverage
+ uncertainty`를 잘 결합했기 때문인지, `floor`, `wall`, endpoint structure 같은 label/context
shortcut을 맞췄기 때문인지 분리할 수 없다.

## Option Matrix

| Option | Verdict | Reason |
| --- | --- | --- |
| `run_posterior_smoke_now` | `reject` | strict/diagnostic controlled relation reliability slice가 없다. |
| `upgrade_combiner_now` | `reject` | 현재 blocker는 combiner capacity가 아니라 target independence다. |
| `use_geometry_support_as_main_target` | `reject_for_reliability_claim` | geometry support는 evidence axis이며 relation reliability와 같지 않다. |
| `collect_more_same_v3_proxy_labels` | `reject` | 같은 sampling/label policy로 더 모으면 object/endpoint shortcut이 유지될 가능성이 높다. |
| `collect_independent_labels_immediately_on_current_160` | `defer` | 현재 160-row pool 자체가 object/endpoint controlled가 아니므로 relabeling만으로 문제를 해결하기 어렵다. |
| `revise_v3_object_endpoint_controlled_sampling` | `select` | 실패 원인인 object/endpoint shortcut을 직접 통제한다. |
| `freeze_as_rga_diagnostic_only` | `keep_as_fallback` | 다음 controlled sampling도 실패하면 H002는 posterior method claim이 아니라 RGA diagnostic benchmark로 남긴다. |
| `add_multi_view_as_model_input_now` | `reject_now` | clean target 없이 visual feature를 추가하면 feature gain과 target shortcut이 섞인다. |

## Next Sampling Contract

다음 단계는 v3 axis를 유지하되 sampling과 label contract를 바꾼다.

Primary controls:

- 같은 또는 near-matched `subject_label/object_label` cell 안에서 positive/negative 후보가
  같이 존재하도록 만든다.
- `endpoint_flag_pattern` stratum 안에서도 가능한 한 양쪽 class가 나오게 한다.
- `predicate_family`와 `predicate_label`이 single-class proxy가 되지 않게 한다.
- `rank_band`, `queue_kind`, `sampling_category`, expected role, `geometry_status`,
  `p_geom_valid`, source score/rank, `label_match_status`는 labeler-visible surface에서
  제외한다.
- Hidden construction metadata는 label lock 이후 audit 전용으로만 조인한다.

Posterior reopen gate:

- relation reliability binary target이 최소 `20` positive / `20` negative를 가진다.
- strict 또는 명시적으로 방어 가능한 diagnostic controlled slice가 존재한다.
- object-label-only 및 endpoint-only probe가 semantic/geometry evidence를 압도하지 않는다.
- validation/test usage는 계속 `False`다.

## Interpretation

이 결정은 H002를 억지로 posterior 방향으로 끌고 가는 것이 아니다. 현재 실패 원인은
`relation reliability`라는 target이 독립적으로 구성되지 않았다는 점이다. 따라서 다음
실험은 더 강한 모델이 아니라, 모델이 학습할 target을 원리적으로 다시 통제하는 것이다.

Object label은 relation reasoning에서 완전히 제거할 수 없는 유효한 context다. 문제는
object label이 target을 거의 단독으로 설명해버리면, H002가 주장하는 factorized reliability
결합을 검증할 수 없다는 점이다. 그래서 object label을 숨기는 것이 아니라, object/endpoint
matched cell 안에서 semantic/geometry evidence가 실제로 target 차이를 설명하는지 보도록
sampling을 바꾼다.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/142_reliability_target_v3_path_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_path_decision_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_path_decision_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_path_decision_codex_proxy_user_requested/option_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_path_decision_codex_proxy_user_requested/element_failure_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_path_decision_codex_proxy_user_requested/next_sampling_plan.json
```

## Next TODO

```text
reliability_target_v3_object_endpoint_controlled_plan
```

Goal:

- train-only full RGA rows에서 object/endpoint matched sampling cell을 정의한다.
- current v3 axis는 유지하되 object/endpoint shortcut을 제어하는 label pool을 설계한다.
- multi-view/mesh는 label/audit evidence로만 둔다.
- posterior smoke는 계속 block한다.
