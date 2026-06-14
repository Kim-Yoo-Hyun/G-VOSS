# H002 Factor Dataset

Last updated: 2026-06-12

## Purpose

`25_factor_contract.md`에서 고정한 target, feature block, baseline, leakage rule을
실제 train-only dataset artifact로 materialize했다.

이 단계의 목적은 factorized reliability posterior를 바로 주장하는 것이 아니라, 다음
smoke fitting 단계가 사용할 입력을 명확히 분리하는 것이다.

핵심 원칙:

```text
deployable feature input != label/audit target evidence
```

즉, `semantic evidence`, `geometry evidence`, `coverage evidence`, `uncertainty
evidence`는 deployable input으로 만들고, `working_label`, `strict/weak target`,
`action_target`은 target block에만 둔다.

## Input Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/match_rows.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_contract/factor_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_contract/factor_contract.json
```

Input facts:

| Item | Rows |
| --- | ---: |
| train RGA rows | 118,560 |
| factor target rows | 217 |
| strict usable target rows | 93 |
| weak usable target rows | 132 |

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/factor_dataset.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/factor_dataset.py
```

Status:

```text
status: ready
```

Output directory:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/
```

## Output Artifacts

| Artifact | Rows | Role |
| --- | ---: | --- |
| `deployable_features_all.jsonl` | 118,560 | all train deployable feature rows |
| `target_joined.jsonl` | 217 | audit target rows joined with feature blocks |
| `strict_smoke.jsonl` | 93 | strict binary train smoke input |
| `weak_smoke.jsonl` | 132 | weak binary train smoke input |
| `dataset_summary.json` | 1 | dataset summary and validation boundary |
| `schema.json` | 1 | feature/target schema |
| `report.md` | 1 | compact generated report |

Size note:

```text
deployable_features_all.jsonl ~= 596MB
```

The first smoke model should use `strict_smoke.jsonl` and `weak_smoke.jsonl`, not
the full 118,560-row feature file.

## Dataset Schema

Each deployable feature row has four main blocks.

```text
S_e = semantic_evidence
G_e = geometry_evidence
C_e = coverage_evidence
U_e = uncertainty_evidence
```

Baseline input views are also materialized in each row:

```text
semantic_only
geometry_only
semantic_plus_geometry
factorized_reliability_posterior
```

The deployable H002 posterior remains:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

The oracle diagnostic form with label evidence remains non-deployable:

```text
P(R_e = 1 | S_e, L_e, G_e, C_e, U_e)
```

`L_e` appears only in target/evaluation blocks, not in deployable input features.

## Feature Distribution

Geometry status:

| Status | Rows |
| --- | ---: |
| `satisfied` | 12,285 |
| `uncertain` | 11,841 |
| `unsatisfied` | 3,234 |
| `unsupported` | 91,200 |

Predicate family:

| Family | Rows |
| --- | ---: |
| `attachment_deferred` | 13,680 |
| `proximity` | 4,560 |
| `relative_horizontal` | 18,240 |
| `relative_vertical` | 9,120 |
| `support_contact` | 13,680 |
| `unsupported_first_pass` | 59,280 |

## Target Subsets

Strict target:

| Class | Rows | Working label |
| --- | ---: | --- |
| positive | 48 | `true_underconfidence` |
| negative | 45 | `semantic_overconfidence` |

Strict target by predicate family:

| Target | Family | Rows |
| --- | --- | ---: |
| negative | `relative_vertical` | 18 |
| negative | `support_contact` | 27 |
| positive | `proximity` | 16 |
| positive | `relative_vertical` | 11 |
| positive | `support_contact` | 21 |

Weak target:

| Class | Rows | Working labels |
| --- | ---: | --- |
| positive | 76 | `true_underconfidence`, `annotation_sparsity` |
| negative | 56 | `semantic_overconfidence`, `dense_relation_noise` |

Weak target by predicate family:

| Target | Family | Rows |
| --- | --- | ---: |
| negative | `proximity` | 11 |
| negative | `relative_vertical` | 18 |
| negative | `support_contact` | 27 |
| positive | `proximity` | 16 |
| positive | `relative_vertical` | 34 |
| positive | `support_contact` | 26 |

## Leakage Check

The generated summary reports:

```text
forbidden deployable feature keys: []
missing target joins: 0
extra targets not found in features: []
validation usage: none
```

An additional full-file string scan over `deployable_features_all.jsonl` found no
forbidden target/label fields:

```text
working_label
label_match_status
strict_binary_target
weak_binary_target
matched_gt_ids
matched_predicates
```

This matters because H002 should not let the model learn relation reliability by
secretly reading GT match or audit labels as input features.

## Interpretation

This stage turns RGA into a concrete train-only modeling interface:

```text
RGA rows -> deployable feature blocks -> target-joined audit rows -> smoke inputs
```

The important outcome is not model performance yet. The important outcome is that
H002 now has a controlled input/output contract for testing whether
factor-separated evidence explains relation reliability better than:

1. `semantic_only`
2. `geometry_only`
3. `semantic_plus_geometry`
4. `factorized_reliability_posterior`

The strict target is scientifically cleaner but small. The weak target is larger
but must remain hypothesis-stage weak supervision until human-confirmed labels
replace the current working labels.

## Current Boundary

Established:

- train-only factor dataset exists.
- all 118,560 train RGA rows have deployable feature blocks.
- all 217 target rows join back to feature rows.
- strict and weak smoke inputs are ready.
- label/audit evidence is excluded from deployable feature blocks.
- no validation rows or validation-derived target choices are used.

Not established:

- any fitted posterior.
- any AUROC/AUPRC/calibration result.
- any paper-level performance claim.
- human-confirmed target labels.
- held-out validation/test evidence.

## Next TODO

Next document:

```text
27_factor_smoke.md
```

Required next work:

- fit train-only smoke baselines on `strict_smoke.jsonl`.
- run `weak_smoke.jsonl` only as sensitivity.
- compare `semantic_only`, `geometry_only`, `semantic_plus_geometry`, and
  `factorized_reliability_posterior`.
- report AUROC/AUPRC/calibration only as hypothesis-stage train diagnostics.
- do not tune on validation and do not present the result as a paper metric.
