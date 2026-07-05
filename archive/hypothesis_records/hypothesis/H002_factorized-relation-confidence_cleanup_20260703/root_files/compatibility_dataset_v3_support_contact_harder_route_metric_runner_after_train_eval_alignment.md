# Support/Contact Harder Route Metric Runner After Train/Eval Alignment

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_runner_after_train_eval_alignment/
runtime_root = experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/
status = h002_support_contact_harder_route_metric_runner_after_train_eval_alignment_ready
validation_errors = 0
metric_warnings = 4
next_todo = compatibility_dataset_v3_support_contact_harder_route_metric_result_review_after_runner
```

## 실행한 Docker Command

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-support-contact-hard-metric-runner
```

Metric runner는 aligned train/dev input을 사용해 `internal_train`에서만 fit하고,
`internal_dev`에서만 sanity selection을 본 뒤, official validation을 eval-only로
한 번 평가했다. Official test는 사용하지 않았다.

## Runtime Outputs

```text
experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/eval_manifest.json
experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/dev_metrics.csv
experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/official_metrics.csv
experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/control_metrics.csv
experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/paired_group_metrics.csv
experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/prediction_scores.jsonl
experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/failure_rows.jsonl
experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/validation_errors.jsonl
```

Hypothesis-stage review artifact:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_runner_after_train_eval_alignment/
```

## Primary Result

| Split | View | AUROC | Balanced accuracy | 판단 |
| --- | --- | ---: | ---: | --- |
| internal dev | `M4_TxG_compatibility` | 0.721356 | 0.658983 | train/dev 내부에서는 compatibility signal 존재 |
| official validation | `M4_TxG_compatibility` | 0.077539 | 0.180931 | official validation transfer 실패 |
| official validation | `M2_geometry_only` | 0.500000 | 0.500000 | geometry-only baseline |
| official validation | `M3_T_plus_G_concat` | 0.454660 | 0.463499 | simple concat baseline |
| official validation | `C1_wrong_T_same_route` | 0.922461 | 0.819069 | wrong-`T`가 오히려 강함 |

이 결과는 support/contact hard route를 paper-facing 성공 결과로 올릴 수 없다는 뜻이다.
특히 wrong-`T` control이 correct `T`보다 훨씬 높게 나온 것은 blocker다.

## Pair Metric Fix

기존 paired-group metric은 같은 pair의 두 후보 점수가 같을 때 row order 때문에
M0/M2가 `1.0`처럼 보일 수 있었다. Runner를 수정해 tied top score를 half-credit과
decisive-only로 분리했다.

수정 후:

- `M0_constant` paired accuracy: `0.5`
- `M2_geometry_only` paired accuracy: `0.5`
- `M4_TxG_compatibility` paired accuracy: `0.182505`
- `C1_wrong_T_same_route` paired accuracy: `0.817495`

## Feature Drift Warning

Train-aligned feature와 official validation feature의 분포 차이가 크다.

| Feature | Train mean | Official mean | Official outside train range |
| --- | ---: | ---: | ---: |
| `support_contact_likelihood_proxy` | 0.027720 | 0.761419 | 0.694147 |
| `xy_overlap_min_ratio` | 0.100429 | 0.983581 | 0.950913 |
| `surface_gap_subject_bottom_to_object_top` | -0.261022 | -0.296430 | 0.069226 |

즉 현재 실패는 단순히 model architecture 문제가 아니라, train reference와 official
validation materialization의 target/feature distribution mismatch 또는 feature mapping
scale mismatch를 먼저 검토해야 하는 상태다.

## Decision

- metric runner completed: yes
- runtime validation errors: `0`
- official validation eval-only: yes
- official test usage: no
- paper metric promoted: no
- support/contact solved claim: blocked
- next: result review

다음 단계에서는 아래 중 어떤 원인이 가장 큰지 판단해야 한다.

- train-side label target과 official GT predicate-flip target의 의미 불일치
- train-aligned `G_e`와 official canonical `G_e`의 feature distribution shift
- `standing on`/`lying on` predicate sign convention mismatch
- support/contact hard route가 current `G_e`로는 official validation에 transfer되지 않는 문제
