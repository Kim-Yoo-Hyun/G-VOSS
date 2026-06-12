# H002 Factor Contract

Last updated: 2026-06-12

## Purpose

`24_train_manual_audit.md` 이후 H002의 first factorized reliability model을 바로
학습하지 않고, 먼저 target, feature block, baseline, leakage rule을 고정한다.

This stage is a contract stage. It defines what a future train-only smoke model is
allowed to use.

## Input Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/working_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/train_rga_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/train_manual_audit_summary.json
```

Input facts:

| Item | Value |
| --- | ---: |
| train RGA prediction rows | 118,560 |
| train audit working-label rows | 217 |
| human-confirmed share | 0.0 |
| Top100 HL rows | 47 |
| tail>100 LH rows | 11,588 |

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/factor_contract.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/factor_contract.py
```

Status:

```text
status: ready
```

Outputs:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_contract/factor_contract.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_contract/feature_blocks.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_contract/baseline_contract.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_contract/factor_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_contract/report.md
```

## Posterior Definition

The deployable H002 posterior is:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

where:

- `R_e`: relation edge is reliable enough to keep, use, or promote.
- `S_e`: semantic evidence.
- `G_e`: geometry evidence.
- `C_e`: coverage evidence.
- `U_e`: uncertainty evidence.

The oracle diagnostic form is:

```text
P(R_e = 1 | S_e, L_e, G_e, C_e, U_e)
```

where `L_e` is label/audit evidence.

Important decision:

```text
L_e is not a deployment-time input feature.
```

`L_e` can be used as train supervision, calibration target, evaluation
stratification, or oracle diagnostic evidence. If `L_e` is used as an input
feature, that model is an oracle diagnostic upper bound, not a deployable
baseline.

## Factor Form

Deployable factor form:

```text
P(R_e=1 | S_e,G_e,C_e,U_e)
  ∝ ψ_sem(R_e,S_e)
    ψ_geom(R_e,G_e)
    ψ_cov(R_e,C_e)
    ψ_unc(R_e,U_e)
    ψ_interact(R_e,S_e,G_e,C_e)
```

Trainable logit form:

```text
logit P(R_e=1)
  = β0
  + f_sem(S_e)
  + f_geom(G_e)
  + f_cov(C_e)
  + f_unc(U_e)
  + f_interact(S_e, G_e, C_e)
```

Oracle diagnostic logit form:

```text
logit P_oracle(R_e=1)
  = β0
  + f_sem(S_e)
  + f_label(L_e)
  + f_geom(G_e)
  + f_cov(C_e)
  + f_unc(U_e)
  + f_interact(S_e, G_e, C_e)
```

## Target Contract

Current labels are machine-assisted working labels, not human-confirmed labels.
Therefore H002 defines three target modes.

### Strict Binary Target

Use:

```text
clean train-only smoke target
```

Mapping:

| Working Label | Target |
| --- | --- |
| `true_underconfidence` | positive |
| `semantic_overconfidence` | negative |
| all others | excluded |

Counts:

| Class | Rows |
| --- | ---: |
| positive | 48 |
| negative | 45 |
| excluded | 124 |
| usable | 93 |

This is small but least ambiguous.

### Weak Binary Target

Use:

```text
hypothesis-stage weak supervision only
```

Mapping:

| Working Label | Target |
| --- | --- |
| `true_underconfidence` | positive |
| `annotation_sparsity` | positive |
| `semantic_overconfidence` | negative |
| `dense_relation_noise` | negative |
| all others | excluded |

Counts:

| Class | Rows |
| --- | ---: |
| positive | 76 |
| negative | 56 |
| excluded | 85 |
| usable | 132 |

This is more useful for smoke fitting but weaker scientifically.

### Soft / Action Target

Soft target is sensitivity-only:

| Working Label | Soft Target | Action |
| --- | ---: | --- |
| `true_underconfidence` | 1.0 | promote or keep candidate |
| `annotation_sparsity` | 0.7 | audit annotation or weak keep |
| `ontology_mismatch` | 0.5 | relabel or multi-relation review |
| `semantic_overconfidence` | 0.0 | reject or downweight |
| `dense_relation_noise` | 0.2 | do not promote dense relation |
| `uncertain_needs_visual_or_mesh` | null | abstain |

This target should not be used for paper-level claims unless human-confirmed
labels replace the current working labels.

## Feature Blocks

### Semantic Evidence `S_e`

Allowed deployment features:

```text
semantic_score_raw
semantic_score_norm
rank_in_context
predicate_rank_for_pair
top50_semantic
top100_semantic
predicate_label
predicate_family
source_id
```

### Geometry Evidence `G_e`

Allowed deployment features:

```text
geometry_status
p_geom_valid
p_geom_invalid
consistency_score
geometry_residual_proxy
reason_codes
raw_features
selected_policy
```

`p_geom_valid` remains geometry-only evidence. It is not the H002 posterior.

### Coverage Evidence `C_e`

Allowed deployment features:

```text
coverage_state
geometry_available
geometry_checkable
predicate_family_supported
missing_geometry
unsupported_family
visual_asset_available_for_audit
```

Coverage prevents `unsupported` or `missing` geometry from being treated as
negative geometry.

### Uncertainty Evidence `U_e`

Allowed deployment features:

```text
geometry_status_is_uncertain
semantic_geometry_disagreement_score
underconfidence_score
absolute_disagreement
abstain_reason_codes
```

Working-label confidence can be used only for target weighting in train smoke,
not as deployment input.

### Label / Audit Evidence `L_e`

Not deployment features:

```text
exact_match
family_match
pair_has_other_predicate
no_gt_for_pair
working_label
human_final_audit_label
```

Allowed uses:

- training target
- calibration target
- evaluation stratification
- oracle diagnostic upper bound

Forbidden uses:

- deployable posterior input
- main-table baseline feature
- validation-time tuning signal

## Baseline Contract

Main executable comparison:

| Baseline | Feature Blocks | Deployment Allowed | Role |
| --- | --- | --- | --- |
| `semantic_only` | `S_e` | yes | source confidence baseline |
| `geometry_only` | `G_e + C_e` | yes | calibrated geometry validity baseline |
| `semantic_plus_geometry` | `S_e + G_e` | yes | H001-style fusion baseline |
| `factorized_reliability_posterior` | `S_e + G_e + C_e + U_e + interactions` | yes | H002 proposed posterior |

Diagnostic-only:

| Baseline | Feature Blocks | Deployment Allowed | Role |
| --- | --- | --- | --- |
| `oracle_label_factor_diagnostic` | `S_e + L_e + G_e + C_e + U_e + interactions` | no | oracle upper-bound / analysis only |

This means the final main table should not compare against a deployable model
that secretly uses exact-match or working labels as input.

## Leakage Rules

Frozen rules:

- validation artifacts are forbidden for H002 hypothesis-stage target,
  threshold, or model selection.
- `label_match_status` cannot be a deployable input feature.
- `working_label` cannot be a deployable input feature.
- `human_final_audit_label` cannot be a deployable input feature, except in
  oracle diagnostic analysis.
- working labels may supervise train-only smoke fitting only under weak-label
  boundary.
- paper-level posterior claims require either human-confirmed labels or an
  explicit weak-supervision claim boundary.

## Current Decision

Use order:

1. Start with `strict_binary_target` for the first train-only smoke.
2. Run `weak_binary_target` only as sensitivity.
3. Keep `oracle_label_factor_diagnostic` out of the main deployable comparison.
4. Do not use validation rows until H002 feature/target definitions are frozen.

This preserves the main H002 claim:

```text
Relation reliability is not just semantic score times geometry validity.
It requires separate treatment of semantic evidence, geometry evidence,
coverage, and uncertainty, with label/audit evidence used as supervision or
diagnostic stratification rather than deployment input.
```

## Current Boundary

Established:

- train-only target modes are fixed.
- feature blocks are fixed.
- baseline set is fixed.
- label leakage rules are fixed.
- `factor_targets.jsonl` exists for the 217 train audit rows.

Not established:

- actual factorized model fitting.
- feature matrix for all 118,560 rows.
- train-only AUROC/AUPRC/calibration smoke result.
- human-confirmed target labels.
- held-out validation/test evidence.

## Next TODO

Next document:

```text
26_factor_dataset.md
```

Required next work:

- materialize train-only deployable feature rows from `match_rows.jsonl`.
- join `factor_targets.jsonl` for the 217 audit rows.
- produce strict/weak target subsets without validation.
- prepare smoke-fitting inputs for:
  - `semantic_only`
  - `geometry_only`
  - `semantic_plus_geometry`
  - `factorized_reliability_posterior`
