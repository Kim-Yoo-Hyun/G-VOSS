# H002 Full Train Label Policy Audit

Last updated: 2026-06-16

## Purpose

`63_full_train_posterior_smoke.md`에서 확인된 proxy blocker를 정량적으로 감사한다.
핵심 질문은 다음이다.

```text
Is the current codex_ver_full_train binary target explained by label policy
metadata rather than by factorized relation evidence?
```

## Decision

Current status:

```text
full_train_label_policy_entangled
```

Meaning:

```text
The current full-train bootstrap target is highly recoverable from label-policy
metadata. It is useful for RGA plumbing and audit framing, but not for a
factorized posterior method claim.
```

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_label_policy_audit.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_label_policy_audit.py
```

Observed:

```text
status=full_train_label_policy_entangled validation_used=False rows=173 pos=74 neg=99 role_majority=1.0000 role_nmi=1.0000 label_status_majority=0.9942 label_status_nmi=0.9550
```

## Input

Input rows:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/controlled_posterior_smoke_codex_ver/full_train_controlled_codex_ver_rows.jsonl
```

Count:

| Item | Count |
| --- | ---: |
| binary rows | 173 |
| positive | 74 |
| negative | 99 |

Boundary:

- train-only.
- no validation/test rows.
- labels are `(codex_ver_full_train)` bootstrap labels.
- not human-confirmed.
- not paper-level posterior evidence.

## Association Audit

Metadata-only majority rule:

| Key | Groups | Single-Class Groups | Majority Accuracy | NMI |
| --- | ---: | ---: | ---: | ---: |
| `proposed_audit_role` | 6 | 6 | 1.0000 | 1.0000 |
| `label_match_status` | 4 | 3 | 0.9942 | 0.9550 |
| `final_controlled_label` | 2 | 2 | 1.0000 | 1.0000 |
| `failure_taxonomy_label` | 3 | 3 | 1.0000 | 1.0000 |
| `queue_kind` | 2 | 1 | 0.9075 | 0.6434 |
| `geometry_status` | 2 | 1 | 0.9075 | 0.6434 |
| `rank_band` | 6 | 2 | 0.9075 | 0.6467 |
| `predicate_family` | 3 | 0 | 0.5723 | 0.0058 |
| `predicate_label` | 6 | 1 | 0.7514 | 0.2875 |

Interpretation:

```text
proposed_audit_role and label_match_status are effectively target construction
variables for the current bootstrap target.
```

This means the current target is not independent enough to validate:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

as a method contribution.

## Model/Proxy Check

Original full-train grouped-by-scan metrics:

| View | AUROC | AUPRC | Brier |
| --- | ---: | ---: | ---: |
| `semantic_plus_geometry` | 0.9044 | 0.7547 | 0.1188 |
| `factorized_reliability_posterior` | 0.9085 | 0.7665 | 0.1170 |
| `negative_rank_only` | 0.8965 | 0.7482 | 0.1411 |
| `queue_only` | 0.8793 | 0.7195 | 0.0881 |
| `label_status_only` | 0.9916 | 0.9473 | 0.0087 |
| `proposed_role_only` | 1.0000 | 1.0000 | 0.0035 |

Key deltas:

| Comparison | Delta AUROC | Delta AUPRC | Delta Brier |
| --- | ---: | ---: | ---: |
| `factorized - semantic_plus_geometry` | +0.0041 | +0.0117 | -0.0019 |
| `factorized - label_status_only` | -0.0831 | -0.1808 | +0.1083 |
| `factorized - proposed_role_only` | -0.0915 | -0.2335 | +0.1135 |

The factorized posterior remains a small improvement over `semantic_plus_geometry`
but is dominated by label-policy proxies. This is not posterior evidence.

## Balanced Variants

The audit exported compact policy-balanced variants for possible later debugging:

| Variant | Rows | Positive | Negative | Use |
| --- | ---: | ---: | ---: | --- |
| `family_balanced_codex_ver` | 148 | 74 | 74 | useful diagnostic |
| `predicate_balanced_codex_ver` | 86 | 43 | 43 | useful diagnostic |
| `queue_balanced_codex_ver` | 32 | 16 | 16 | small diagnostic |
| `geometry_status_balanced_codex_ver` | 32 | 16 | 16 | small diagnostic |
| `queue_family_balanced_codex_ver` | 28 | 14 | 14 | small diagnostic |
| `label_status_balanced_codex_ver` | 2 | 1 | 1 | not fit-worthy |
| `proposed_role_balanced_codex_ver` | 0 | 0 | 0 | confirms role defines target |

These variants can debug posterior behavior, but they do not solve the label
independence problem because `label_status_only` and `proposed_role_only` still
remain perfect or near-perfect on the fit-worthy variants.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/label_policy_audit_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/label_policy_audit_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/label_policy_audit_codex_ver/group_policy_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/label_policy_audit_codex_ver/metrics.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/label_policy_audit_codex_ver/comparisons.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/label_policy_audit_codex_ver/*_codex_ver.jsonl
```

Line counts:

| Artifact | Rows |
| --- | ---: |
| `group_policy_table.csv` | 36 + header |
| `metrics.csv` | 204 + header |
| `comparisons.csv` | 72 + header |
| exported variant JSONL total | 499 |

## Interpretation

The full-train expansion did not falsify H002 as a research problem. It did
falsify the current bootstrap target as an independent posterior target.

Therefore the current strongest H002 claim remains:

```text
RGA is a benchmark/diagnostic framework for exposing semantic-geometry-label
mismatch at relation level.
```

The factorized posterior is still a conditional method candidate, but it needs
an independent target before additional model-design changes are meaningful.

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_label_policy_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_label_policy_audit.py
```

Observed:

```text
validation_used=False
```

## Next TODO

Completed next action:

```text
full_train_independent_label_protocol
```

Result:

```text
full_train_independent_label_protocol_ready_needs_asset_packets
```

The blind labeling surface now hides `proposed_audit_role`,
`label_match_status`, `queue_kind`, `geometry_status`, rank, score, and
`p_geom_valid`. The next blocker is evidence packet generation.

Next action:

```text
full_train_independent_asset_packets
```
