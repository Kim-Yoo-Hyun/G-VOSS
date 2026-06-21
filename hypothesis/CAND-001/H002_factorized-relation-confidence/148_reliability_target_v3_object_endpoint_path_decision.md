# H002 Reliability Target V3 Object/Endpoint Path Decision

Date: 2026-06-20 KST

## Purpose

`147_reliability_target_v3_object_endpoint_target_independence_audit.md`에서
object/endpoint-controlled v3 target이 여전히 posterior-ready가 아님을 확인했다.
이번 단계는 posterior smoke를 진행할지, geometry-support를 main target으로 바꿀지,
혹은 target/sampling을 다시 수정할지 결정한다.

핵심 질문:

```text
Should H002 continue toward posterior learning now, or first rebuild the
reliability target around informative non-trivial relation positives?
```

## Boundary

- Split: Open3DSG train-only.
- Validation/test row는 사용하지 않았다.
- Posterior model은 학습하지 않았다.
- Combiner upgrade는 진행하지 않았다.
- H001 artifact는 수정하지 않았다.
- Multi-view는 계속 audit/label evidence이며 model input이 아니다.
- 현재 label은 user-requested Codex proxy label이며 independent human evidence가 아니다.

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_path_decision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_path_decision.py
```

Observed:

```text
status=h002_reliability_target_v3_object_endpoint_path_decision_informative_anchor_sampling
selected=revise_v3_informative_positive_anchor_sampling
rel=107/8/99
supports=85
trivial=73
posterior_allowed=False
validation_used=False
test_used=False
next=reliability_target_v3_informative_anchor_plan
```

## Decision

Selected path:

```text
revise_v3_informative_positive_anchor_sampling
```

Decision:

```text
Do not run posterior smoke, upgrade the combiner, or use geometry-support as
the main target. The object/endpoint-controlled attempt shows that
geometry-supported rows are dominated by trivial room/surface relations, so the
next step is informative positive-anchor sampling with object/endpoint controls
retained.
```

## Why This Path

현재 실패는 세 가지를 동시에 보여준다.

| Observation | Count | Meaning |
| --- | ---: | --- |
| `geometry_support_v3.supports_predicate` | 85 | geometry predicate를 지지하는 row는 많다. |
| `relation_reliability_v3.reliable` | 8 | relation reliability positive는 매우 적다. |
| `relation_reliability_v3.unreliable_trivial` | 73 | geometry-supported row 상당수가 trivial room/surface relation이다. |
| `relation_usefulness_v3.trivial_dense_or_room_structure` | 75 | usefulness axis도 trivial relation에 지배된다. |

따라서 단순히 geometry score를 더 잘 쓰는 posterior를 만드는 문제가 아니다.
H002가 풀어야 하는 문제는 다음과 같이 더 정확히 정리된다.

```text
geometry-supported relation edge가 많더라도, 그 edge가 scene graph에서 reliable하고
informative한 relation이라는 뜻은 아니다.
```

즉, 현재 target은 `geometry validity`와 `relation reliability`가 다르다는 H002의 핵심
주장을 오히려 잘 보여준다. 하지만 이 target으로 posterior를 학습하면 대부분 negative인
target 또는 triviality detector를 맞추는 실험이 될 수 있다.

## Option Matrix

| Option | Verdict | Reason |
| --- | --- | --- |
| `run_posterior_smoke_now` | `reject` | main reliability target이 positive-sparse이고 controlled slice가 없다. |
| `upgrade_combiner_now` | `reject` | 병목은 posterior capacity가 아니라 target definition/sampling이다. |
| `use_geometry_support_as_main_target` | `reject_for_reliability_claim` | geometry support는 evidence axis이지 relation reliability가 아니다. |
| `relax_reliability_to_geometry_supported` | `reject` | H002의 핵심 구분을 무너뜨린다. |
| `collect_more_same_object_endpoint_labels` | `reject_as_primary` | 같은 분포에서 더 모으면 trivial negatives가 대부분 늘 가능성이 크다. |
| `keep_geometry_support_diagnostic_only` | `keep` | RGA decomposition evidence로는 유효하다. |
| `revise_v3_informative_positive_anchor_sampling` | `select` | 현재 실패 원인인 trivial room/surface dominance를 직접 겨냥한다. |
| `freeze_h002_as_rga_diagnostic_only` | `fallback` | 다음 mining도 실패하면 posterior method claim을 강제하지 않는다. |
| `add_multi_view_as_model_input_now` | `reject_now` | clean reliability target 없이 feature를 늘리면 target shortcut과 feature gain이 섞인다. |

## Next Sampling Direction

다음 label pool은 기존 v3 axis와 object/endpoint control을 유지하되,
`informative reliable positive`가 나올 가능성이 있는 row를 의도적으로 찾는다.

Recommended target:

| Category | Target Rows |
| --- | ---: |
| `informative_reliable_positive` | 40 |
| `geometry_contradiction_negative` | 40 |
| `trivial_room_surface_negative` | 40 |
| `uncertain_or_ontology_negative` | 40 |

Informative positive anchor 후보:

- `support_contact`에서 object가 `floor`, `wall`, `ceiling`이 아닌 non-room support relation.
- `table`, `desk`, `shelf`, `cabinet`, `chair`, `sofa` 등 object-level support surface와 movable subject 조합.
- `relative_vertical`에서 양쪽 endpoint가 object-level이고 height gap이 의미 있는 조합.
- geometry는 predicate를 지지하면서 relation_usefulness가 informative일 가능성이 높은 row.

Negative anchor 후보:

- 같은 predicate family 안의 geometry contradiction.
- trivial dense room/surface relation은 명시적 negative로 유지하되 cap을 둔다.
- ontology mismatch 또는 endpoint identity issue는 별도 negative/uncertain 축으로 유지한다.
- 같은 subject/object 또는 endpoint stratum 안의 hard negative를 포함한다.

## Posterior Reopen Gate

Posterior smoke는 다음 조건을 만족하기 전까지 계속 막는다.

- relation reliability binary target이 최소 `20` positive / `20` negative를 가진다.
- strict 또는 방어 가능한 diagnostic controlled slice가 존재한다.
- `trivial_dense_or_room_structure`가 negative target을 단독 지배하지 않는다.
- object-label-only 및 endpoint-only probe가 target을 설명하지 않는다.
- validation/test usage는 계속 `False`다.

## Fallback Stop Rule

다음 informative-anchor mining에서도 controlled reliability target을 만들지 못하면, H002를
posterior method claim으로 억지로 끌고 가지 않는다. 그 경우 H002는 다음 형태로 남기는 것이
더 방어 가능하다.

```text
RGA diagnostic/decomposition framework:
semantic score, geometry support, usefulness, uncertainty, and relation
reliability can be separated, but current data/source does not provide a clean
posterior target.
```

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/148_reliability_target_v3_object_endpoint_path_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_path_decision_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_path_decision_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_path_decision_codex_proxy_user_requested/option_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_path_decision_codex_proxy_user_requested/target_failure_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_path_decision_codex_proxy_user_requested/next_plan.json
```

## Next TODO

```text
reliability_target_v3_informative_anchor_plan
```

Goal:

- train-only full RGA rows에서 informative reliable positive anchor 후보를 찾는다.
- object/endpoint control은 유지하되 floor/wall/ceiling 및 trivial room/surface dominance를 cap한다.
- geometry contradiction, trivial negative, uncertain/ontology negative를 같이 구성한다.
- posterior smoke는 계속 block한다.
