# Source Reranking Metric Runner

## 2026-07-02 Decision Update

목적:

Frozen source-reranking protocol에 따라 source-wide official validation 후보에
`C_e` scorer를 적용하고, source score `Z_e`와 결합한 downstream top-K metric을
계산했다. 이 단계는 official test 검증이나 final paper promotion이 아니라,
source-deployable reranking evidence를 만들기 위한 validation-level metric runner다.

결과:

```text
runtime_root = experiments/H002_compatibility_routing/source_reranking_evaluation/latest/
artifact_root = artifacts/compatibility_dataset_v3_source_reranking_metric_runner_after_protocol_freeze/
status = h002_source_reranking_metric_runner_after_protocol_freeze_ready
selected_path = source_reranking_metric_runner_ready_select_result_review
validation_errors = 0
next_todo = compatibility_dataset_v3_source_reranking_metric_result_review_after_runner
```

Runner boundary:

- `C_e` scorer는 internal train split `4868` rows에서만 fit했다.
- Official validation source rows `762888`개는 eval-only로 scoring했다.
- Official test는 사용하지 않았다.
- `C_e` input은 `T_e + G_e`만 사용했다.
- `Z_e`는 `C_e` 내부에 넣지 않고 reranking score에서만 결합했다.
- Post-hoc lambda tuning은 하지 않았다.
- `support_contact`는 success aggregation에서 제외하고 diagnostic으로 유지했다.

Runtime outputs:

| Output | 위치 |
| --- | --- |
| `metric_manifest.json` | `experiments/H002_compatibility_routing/source_reranking_evaluation/latest/` |
| `score_manifest.json` | same |
| `source_family_metrics.csv` | same |
| `score_condition_metrics.csv` | same |
| `control_metrics.csv` | same |
| `selected_predictions.jsonl` | same |
| `validation_errors.jsonl` | same |

Primary weighted result:

| K | `S2` Recall@K | `S0` Recall@K | Delta | `S2` Violation@K | `S0` Violation@K | Delta |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 0.352608 | 0.344671 | +0.007937 | 0.054491 | 0.295181 | -0.240690 |
| 10 | 0.513605 | 0.471655 | +0.041950 | 0.072342 | 0.302201 | -0.229859 |
| 20 | 0.724490 | 0.642857 | +0.081633 | 0.100487 | 0.343578 | -0.243091 |
| 50 | 0.952381 | 0.849206 | +0.103175 | 0.165998 | 0.425197 | -0.259199 |
| 100 | 1.000000 | 0.995465 | +0.004535 | 0.341919 | 0.484792 | -0.142873 |

Control summary:

- `S2_source_x_Ce` improves or preserves primary Recall@K over `S0_source_score`
  for every frozen K.
- `S2_source_x_Ce` reduces primary Violation@K over `S0_source_score` for every
  frozen K.
- shuffled-`C_e` and wrong-`T` controls underperform `S2` on primary Recall@K.
- wrong-`T` control has much higher Violation@K, which supports that the
  predicate-geometry compatibility direction matters.

Boundary:

이 결과는 source-reranking validation evidence다. 아직 final test result, final
paper promotion, `p_obs`/`p_rel` 검증, all-relation generalization claim으로 쓰면 안 된다.
다음 단계는 result review로, source별/family별 비대칭과 recall-violation tradeoff가
paper-facing claim으로 승격 가능한지 판단해야 한다.
