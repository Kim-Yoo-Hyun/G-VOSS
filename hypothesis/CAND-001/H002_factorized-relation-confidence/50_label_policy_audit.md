# H002 Label Policy Audit

Last updated: 2026-06-14

## Purpose

`49_independent_combiner_smoke.md`의 결론은 다음이었다.

```text
independent_combiner_no_strong_signal
```

그 원인이 model capacity 부족인지, 아니면 `(codex_ver_blind)` label이
family/predicate rule에 강하게 묶여 있기 때문인지 확인해야 한다.

이번 단계의 핵심 질문:

```text
Are current bootstrap relation reliability labels recoverable from
predicate_family or predicate_label policy alone?
```

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/label_policy_audit.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/label_policy_audit.py
```

Result:

```text
status=label_policy_entangled validation_used=False predicate_majority=0.7067 predicate_nmi=0.2505 family_majority=0.7067 family_nmi=0.1931 proximity_gated_d_auprc=-0.0071 proximity_gated_d_brier=0.0028
```

## Boundary

- Train-only hypothesis-stage audit.
- No validation/test rows are used.
- Labels are `(codex_ver_blind)` bootstrap labels.
- This audits label-policy bias, not paper-level performance.
- `V_mv_e` is not used as model input.
- Posterior method claim remains blocked.

## Input

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_combiner_smoke_codex_ver/independent_codex_ver_blind_rows.jsonl
```

Input count:

| Rows | Positive | Negative |
| ---: | ---: | ---: |
| 75 | 46 | 29 |

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/comparisons.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/group_policy_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/original_independent_codex_ver_blind.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/family_balanced_codex_ver_blind.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/predicate_balanced_codex_ver_blind.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/label_policy_audit_codex_ver/proximity_only_codex_ver_blind.jsonl
```

## Association Audit

Summary:

| Key | Groups | Majority Accuracy | NMI | Conditional Entropy |
| --- | ---: | ---: | ---: | ---: |
| `predicate_family` | 3 | 0.7067 | 0.1931 | 0.7767 |
| `predicate_label` | 5 | 0.7067 | 0.2505 | 0.7215 |
| `rank_band` | 4 | 0.6533 | 0.0980 | 0.8683 |

Important group rates:

| Group | Positive | Negative | Positive Rate | Majority Accuracy |
| --- | ---: | ---: | ---: | ---: |
| `support_contact` | 23 | 2 | 0.9200 | 0.9200 |
| `proximity` | 15 | 12 | 0.5556 | 0.5556 |
| `relative_vertical` | 8 | 15 | 0.3478 | 0.6522 |
| `standing on` | 15 | 0 | 1.0000 | 1.0000 |
| `lower than` | 0 | 2 | 0.0000 | 1.0000 |
| `supported by` | 8 | 2 | 0.8000 | 0.8000 |
| `higher than` | 8 | 13 | 0.3810 | 0.6190 |
| `close by` | 15 | 12 | 0.5556 | 0.5556 |

Interpretation:

```text
The target is strongly recoverable from predicate/family policy. Predicate label
has higher normalized mutual information than rank band.
```

This explains why `predicate_only` and `family_only` were strong in
`49_independent_combiner_smoke.md`.

## Balanced Variants

The audit exported stricter target variants.

| Target Variant | Rows | Positive | Negative | Purpose |
| --- | ---: | ---: | ---: | --- |
| `original_independent_codex_ver_blind` | 75 | 46 | 29 | full current target |
| `family_balanced_codex_ver_blind` | 44 | 22 | 22 | balance positives/negatives inside each predicate family |
| `predicate_balanced_codex_ver_blind` | 44 | 22 | 22 | balance positives/negatives inside each predicate label; single-class predicates excluded |
| `proximity_only_codex_ver_blind` | 27 | 15 | 12 | single-family/single-predicate slice |

These variants are not new labels. They are controlled subsets of the current
bootstrap labels.

## Variant Smoke

Grouped-by-scan metrics:

| Target | View | AUROC | AUPRC | Brier |
| --- | --- | ---: | ---: | ---: |
| `original` | `semantic_plus_geometry` | 0.7736 | 0.8539 | 0.1870 |
| `original` | `factorized` | 0.7714 | 0.8526 | 0.1886 |
| `original` | `predicate_only` | 0.7571 | 0.8650 | 0.1899 |
| `family_balanced` | `semantic_plus_geometry` | 0.3946 | 0.4377 | 0.3556 |
| `family_balanced` | `factorized` | 0.3946 | 0.4377 | 0.3586 |
| `family_balanced` | `gated` | 0.4174 | 0.4504 | 0.3492 |
| `predicate_balanced` | `semantic_plus_geometry` | 0.3533 | 0.4248 | 0.3557 |
| `predicate_balanced` | `factorized` | 0.3574 | 0.4262 | 0.3578 |
| `predicate_balanced` | `gated` | 0.3512 | 0.4232 | 0.3376 |
| `proximity_only` | `semantic_plus_geometry` | 0.5500 | 0.6928 | 0.2873 |
| `proximity_only` | `factorized` | 0.5444 | 0.6856 | 0.2908 |
| `proximity_only` | `gated` | 0.5444 | 0.6856 | 0.2902 |

Key deltas:

| Target | Comparison | Delta AUPRC | Delta Brier |
| --- | --- | ---: | ---: |
| `original` | `factorized - semantic_plus_geometry` | -0.0013 | +0.0016 |
| `family_balanced` | `gated - semantic_plus_geometry` | +0.0128 | -0.0064 |
| `predicate_balanced` | `factorized - semantic_plus_geometry` | +0.0013 | +0.0021 |
| `predicate_balanced` | `gated - semantic_plus_geometry` | -0.0016 | -0.0181 |
| `proximity_only` | `gated - semantic_plus_geometry` | -0.0071 | +0.0028 |

Interpretation:

- Once family/predicate policy is controlled, the original high AUPRC largely
  disappears.
- `predicate_balanced` does not recover factorized/gated AUPRC.
- `proximity_only` no longer shows the positive gated signal seen in the earlier
  non-grouped family slice.
- Some Brier improvements remain in balanced variants, but AUPRC/AUROC do not
  support a posterior method claim.

## Decision

Current status:

```text
label_policy_entangled
```

Meaning:

```text
The current codex_ver_blind labels are useful for plumbing, but they are too
entangled with family/predicate policy to support factorized posterior novelty.
```

Allowed:

- use exported balanced variants for further debugging.
- use this as negative evidence against immediate posterior method escalation.
- keep H002 as RGA benchmark/failure-analysis direction.
- design a new human label protocol that explicitly controls predicate/family
  balance.

Blocked:

- factorized posterior method claim.
- residual/gated combiner claim.
- multi-view promotion to model input.
- paper-level result claim from `(codex_ver_blind)` labels.

## Implication For H002

The current H002 evidence supports the problem framing more than the posterior
method.

Supported:

```text
semantic score != geometry validity != relation reliability
```

Still unsupported:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

as a method contribution that beats a strong `semantic_plus_geometry` baseline
under policy-controlled labels.

## Next TODO

Next document:

```text
51_posterior_path_decision.md
```

Goal:

- decide whether H002 should keep posterior as a method candidate.
- define the minimum new label evidence needed to revive posterior claims.
- decide whether the near-term paper framing should shift to RGA benchmark /
  failure taxonomy.
- keep validation/test unused.
