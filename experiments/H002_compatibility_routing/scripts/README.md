# Scripts

## Role

This folder owns executable H002 runtime code. These scripts are the code path
that creates materialized rows, audits leakage/schema boundaries, computes C_e
scores, and evaluates metrics.

## Core Scripts

| Script | Role |
| --- | --- |
| `materialize_source_reranking_candidates.py` | creates source-wide reranking input views |
| `audit_source_reranking_materialization_schema.py` | checks `T_e/G_e`, `Z_e`, geometry-only, and hidden metric separation |
| `run_source_reranking_metric.py` | fits C_e plus `A1` geometry-only and `A2` concat ablations, then computes Recall@K / Violation@K |
| `bootstrap_source_reranking_ci.py` | bootstraps frozen source-reranking Recall@K / Violation@K, `S2-S0`, `S2-A1`, `S2-A2`, controls, and family-wise CI |
| `run_ce_improvement_path.py` | evaluates hard-negative/structured, route-aware, richer-G_e gate, and calibrated-C_e variants |
| `review_ce_candidate_ci_family.py` | reviews the calibrated route-aware C_e candidate with bootstrap CI, K=5 result, family blockers, and promotion gates |
| `official_materialize_candidates.py` | builds official-validation route-family candidate rows |
| `audit_official_materialization_schema.py` | audits official candidate schema/leakage/shortcut risk |
| `run_official_metric.py` | evaluates semantic-only, geometry-only, concat, and T x G compatibility views |
| `materialize_support_contact_harder_route.py` | creates diagnostic support/contact hard-route rows |
| `run_support_contact_harder_metric.py` | evaluates diagnostic support/contact hard-route failure |
| `materialize_pobs_prel_selective.py` | creates `Q_e`, `p_rel`, and hidden selective-label views |
| `audit_pobs_prel_materialization_schema.py` | checks p_obs / p_rel schema separation and hidden-label leakage |
| `run_pobs_prel_selective_metric.py` | evaluates p_obs, p_rel, accept/reject/abstain, missing-evidence controls, and risk-coverage |
| `run_pobs_prel_calibration_upgrade.py` | runs fixed-split p_obs / p_rel calibration, asset observability audit, CI, controls, and route connection |
| `repair_pobs_prel_observability.py` | creates the p_obs / p_rel real-observability schema and 265-row audit queue |
| `fill_pobs_prel_observability_labels.py` | fills the observability audit queue with Codex labels and explicit non-human provenance |
| `ingest_pobs_prel_observability_labels.py` | builds model-safe Q_e / p_rel views and hidden observability labels |
| `audit_pobs_prel_observability_schema.py` | audits row alignment, blocked fields, and model-safe / hidden separation for the observability labels |
| `decide_pobs_prel_observability_metric_gate.py` | records user confirmation and opens a diagnostic metric gate for the Codex-filled labels |
| `run_pobs_prel_observability_metric.py` | trains on the frozen internal protocol and evaluates the 265-row user-confirmed observability subset |
| `review_pobs_prel_observability_metric.py` | reviews p_obs/p_rel observability results and emits the Q_e repair plan |
| `plan_pobs_prel_qe_repair.py` | defines Q_e v2 schema, materialization contract, gates, and implementation steps after p_obs failure |
| `materialize_pobs_prel_qe_repair.py` | builds repaired Q_e v2 train/eval model-safe views and hidden observability v2 labels |
| `audit_pobs_prel_qe_repair_schema.py` | audits repaired Q_e v2 model-safe / hidden separation and p_obs-only rerun readiness |
| `run_pobs_prel_qe_repair_pobs_only_metric.py` | runs the repaired Q_e v2 p_obs-only diagnostic smoke test |
| `review_pobs_prel_qe_repair_pobs_metric.py` | reviews the p_obs-only diagnostic pass and freezes the p_obs claim boundary |

The remaining scripts support preflight, early route materialization, grouped
splits, and internal grouped evaluation.

## Paper Status

The paper-facing runtime path is source reranking:

```text
materialize_source_reranking_candidates.py
audit_source_reranking_materialization_schema.py
run_source_reranking_metric.py
bootstrap_source_reranking_ci.py
```

Official test is not used.

The p_obs / p_rel path is an active framework-extension stress test:

```text
materialize_pobs_prel_selective.py
audit_pobs_prel_materialization_schema.py
run_pobs_prel_selective_metric.py
run_pobs_prel_calibration_upgrade.py
repair_pobs_prel_observability.py
fill_pobs_prel_observability_labels.py
ingest_pobs_prel_observability_labels.py
audit_pobs_prel_observability_schema.py
decide_pobs_prel_observability_metric_gate.py
run_pobs_prel_observability_metric.py
review_pobs_prel_observability_metric.py
plan_pobs_prel_qe_repair.py
materialize_pobs_prel_qe_repair.py
audit_pobs_prel_qe_repair_schema.py
run_pobs_prel_qe_repair_pobs_only_metric.py
```

The calibration-upgrade run adds asset-derived observability audit labels, but
the current result still does not promote calibrated p_obs / p_rel as a solved
quantitative paper claim. The observability label-fill chain now passes schema
audit, but its labels are Codex-filled rather than human-confirmed, so metric
rerun was opened only after user confirmation. The diagnostic metric rerun shows
`p_rel` signal but `p_obs` failure on ambiguous/missing-evidence rows, so
calibrated p_obs / p_rel solved wording remains blocked. The review step fixes
the next path as Q_e feature repair, and the repair-plan step freezes the Q_e
v2 schema and materialization gates. The repair materializer now produces
balanced train rows and a 265-row diagnostic eval view with `validation_errors=0`.
The Q_e v2 schema audit also passes with validation errors `0`, blocked field
hits `0`, required Q_e blocks present, and row/state alignment intact. The next
step runs a p_obs-only diagnostic smoke test, not a full selective-decision
rerun. That smoke test passes, but the p_obs metric review marks the result as
proxy/state-driven because direct `Q_e state_code` reaches the same AUROC. For
the current H002 paper path, `p_obs` is optional diagnostic/future evidence, not
a required core claim.

The latest C_e improvement path is:

```text
run_ce_improvement_path.py
```

It keeps `p_obs/p_rel` disabled, adds inverse-predicate hard negatives,
structured signed-margin features, route-specific C_e models, support/contact
capacity gating, and internal-dev temperature calibration. The current result
selects calibrated route-aware C_e as a candidate improved score, but does not
promote it before bootstrap CI and family-wise review.
