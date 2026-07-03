# Support/Contact Harder Route Metric Runner

```text
status = h002_support_contact_harder_metric_runner_ready
validation_errors = 0
next_todo = compatibility_dataset_v3_support_contact_harder_route_metric_result_review_after_runner
```

Official validation is eval-only. No official test was used. No paper result is promoted here.

Primary official metric:

```json
{
  "Brier": 0.7039212879357659,
  "NLL": 2.627466689301555,
  "auprc": 0.3153689009678573,
  "auroc": 0.0775390596379055,
  "balanced_accuracy": 0.18093140339836375,
  "eval_split": "official_validation",
  "fn": 1323,
  "fp": 1280,
  "level": "overall",
  "macro_F1": 0.18078142492920513,
  "negative": 1589,
  "positive": 1589,
  "predicate_label": "ALL",
  "route_family": "support_contact",
  "rows": 3178,
  "tn": 309,
  "tp": 266,
  "view_id": "M4_TxG_compatibility"
}
```
