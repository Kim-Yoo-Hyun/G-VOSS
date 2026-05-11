# Open3DSG Metric Scope

Status: `metric_scope_policy_ready_no_metric_execution`
Created at: `2026-05-10T06:57:01+00:00`

## Fact

- Predicate-family mapping and denominator policy are frozen before Open3DSG metric execution.
- This artifact does not run Open3DSG metrics, inspect prediction failures, or change the verifier.
- Recall matching remains predicate-label exact; family grouping is used for H001 verifier/violation reporting.

## H001 Denominator

- all GT rows: `7505`
- in-scope GT rows: `2545`
- target family counts: `{'support_contact': 1199, 'proximity': 1128, 'relative_vertical': 218}`

## Filtered Training Caveat

- train filtered: `{'relations': 79704, 'subgraphs': 3744, 'unique_scans': 1158}`
- train removed: `{'object_count_histogram': {'2': 8, '3': 4, '4': 3, '5': 36, '6': 6, '7': 7, '8': 4, '9': 40}, 'relations': 1486, 'removed_only_scans': 20, 'subgraphs': 108, 'unique_scans': 101}`
- train-dev filtered: `{'relations': 3696, 'subgraphs': 156, 'unique_scans': 30}`
- train-dev removed: `{'object_count_histogram': {'6': 1, '8': 1, '9': 2}, 'relations': 53, 'removed_only_scans': 0, 'subgraphs': 4, 'unique_scans': 3}`

## Claim Boundary

Open3DSG Table 6 cannot be promoted to a full cross-source result unless raw dump coverage, prediction export, geometry join, and metric scope all match this policy.
