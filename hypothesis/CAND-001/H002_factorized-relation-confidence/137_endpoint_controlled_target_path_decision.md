# Endpoint-Controlled Target Path Decision

Date: 2026-06-20 KST

## Purpose

`136_endpoint_controlled_target_independence_audit.md`에서 endpoint-controlled
relation reliability target이 positive-sparse로 막힌 것을 확인했다. 이번 단계는
posterior smoke를 진행할지, combiner를 바꿀지, target/sampling을 수정할지 결정한다.

핵심 질문:

```text
Should H002 run posterior smoke now, or fix the reliability target first?
```

## Boundary

- Split: Open3DSG train-only.
- Validation/test row는 사용하지 않았다.
- Posterior model은 학습하지 않았다.
- H001 artifact는 수정하지 않았다.
- Multi-view는 계속 audit evidence이며 model input이 아니다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_target_path_decision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_target_path_decision.py
```

Observed:

```text
status=h002_endpoint_controlled_target_path_decision_revise_target_v3_positive_anchor_sampling
selected=revise_reliability_target_v3_and_positive_anchor_sampling
relation=2/32
geometry=23/11
posterior_allowed=False
validation_used=False
test_used=False
next=reliability_target_v3_positive_anchor_plan
```

## Decision

Selected path:

```text
revise_reliability_target_v3_and_positive_anchor_sampling
```

Decision:

```text
Do not run posterior smoke or upgrade the combiner. Revise relation reliability
as a v3 multi-axis target and run positive-anchor sampling because the
endpoint-controlled binary target is positive-sparse and has no controlled slice.
```

## Key Counts

| Target | Rows | Pos | Neg | Majority Baseline |
| --- | ---: | ---: | ---: | ---: |
| `geometry_validity_endpoint_controlled_target` | 34 | 23 | 11 | 0.6765 |
| `relation_reliability_endpoint_controlled_target` | 34 | 2 | 32 | 0.9412 |

## Option Matrix

| Option | Verdict | Reason |
| --- | --- | --- |
| `run_posterior_smoke_now` | `reject` | Relation reliability is `2/32` and has no strict or diagnostic controlled slice. |
| `upgrade_combiner_now` | `reject` | Bottleneck is target construction and positive coverage, not combiner capacity. |
| `use_geometry_validity_as_main_target` | `reject_for_reliability_claim` | Geometry has `23/11` mass, but geometry validity is not relation reliability. |
| `collect_more_same_endpoint_controlled_labels` | `defer` | At observed positive rate `0.0588`, reaching 20 positives would require hundreds of same-distribution rows. |
| `relax_reliability_to_geometry_supported` | `reject_as_shortcut` | This collapses relation reliability into geometry validity. |
| `revise_reliability_target_v3_and_positive_anchor_sampling` | `select` | Directly addresses sparse positives and mixed failure reasons. |
| `add_multi_view_as_model_input_now` | `reject_now` | Clean target is unavailable; multi-view should remain audit evidence. |

## Interpretation

현재 결과는 semantic-geometry 정합이 잘 된다는 뜻이 아니다. 더 정확히는
현재 binary reliability target이 너무 많은 failure reason을 negative 하나로 접어서,
reliable positive가 거의 남지 않았다는 뜻이다.

Observed label axes:

```text
geometry supports/contradicts/uncertain = 23 / 11 / 28
relation reliability reliable/unreliable/uncertain = 2 / 32 / 28
relation informativeness informative/trivial/ontology_mismatch/uncertain = 2 / 21 / 11 / 28
```

즉, geometry상 성립하는 edge가 있어도 그것이 곧 relation reliability positive가 되지
않는다. H002의 핵심 구분은 유지된다.

```text
geometry validity != relation reliability
```

하지만 현재 target은 posterior 검증에는 부적합하다. 이 상태에서 posterior smoke를
진행하면 `semantic evidence + geometry evidence` 결합을 검증하는 것이 아니라,
대부분 negative인 target을 맞추는 실험이 된다.

## V3 Target Direction

다음 target은 binary reliability를 바로 만들지 말고, 다음 axis를 먼저 분리해야 한다.

| Axis | Values |
| --- | --- |
| `geometry_support` | `supports_predicate`, `contradicts_predicate`, `ambiguous`, `not_evaluable` |
| `relation_usefulness` | `informative`, `trivial_dense_or_room_structure`, `ontology_mismatch`, `uncertain` |
| `relation_reliability` | `reliable`, `unreliable_geometry`, `unreliable_trivial`, `unreliable_ontology`, `uncertain` |

Binary posterior target은 각 axis에 충분한 label mass가 생기고 target-independence audit을
통과한 뒤에만 derive한다.

## Positive Anchor Requirement

Current relation reliability:

```text
positive = 2
negative = 32
positive_rate = 0.0588
```

At the same observed positive rate:

| Goal | Needed Positives | Additional Rows Needed |
| --- | ---: | ---: |
| smoke minimum 10 positives | 8 more | 136 |
| posterior minimum 20 positives | 18 more | 306 |

따라서 같은 분포에서 label만 더 늘리는 것은 비효율적이다. 다음 단계는 reliable positive가
나올 가능성이 있는 positive-anchor 후보를 별도로 mine하고, 동시에 endpoint/predicate/family
shortcut을 통제해야 한다.

Recommended next label goal:

| Category | Target Rows |
| --- | ---: |
| reliable positive anchor | 40 |
| geometry contradiction negative | 40 |
| trivial dense negative | 40 |
| ontology or uncertain negative | 40 |

## Decision Boundary

Rejected now:

- posterior smoke.
- combiner upgrade.
- geometry validity as main reliability target.
- reliability definition을 단순히 geometry-supported로 완화하는 방식.
- multi-view를 model input으로 추가하는 방식.

Selected now:

- v3 reliability target schema.
- positive-anchor sampling.
- endpoint는 model evidence가 아니라 balancing/control stratum으로 유지.
- posterior smoke는 target mass와 target independence가 통과될 때까지 계속 block.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/137_endpoint_controlled_target_path_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_target_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_path_decision_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_path_decision_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_path_decision_codex_proxy_user_requested/option_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_path_decision_codex_proxy_user_requested/target_failure_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_path_decision_codex_proxy_user_requested/v3_positive_anchor_plan.json
```

## Next TODO

```text
reliability_target_v3_positive_anchor_plan
```

Goal:

- define the v3 multi-axis label schema.
- mine train-only positive-anchor candidates.
- keep hidden construction metadata invisible to labelers.
- keep validation/test unused.
- keep posterior smoke blocked until v3 target-independence audit passes.
