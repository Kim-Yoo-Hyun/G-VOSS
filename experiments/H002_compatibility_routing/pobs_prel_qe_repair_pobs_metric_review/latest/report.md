# p_obs Metric Review After Q_e Repair

## Decision

`p_obs` is not required for the current H002 main paper claim.

The repaired `Q_e v2` p_obs-only smoke test passes diagnostically, but it should not be promoted as a calibrated solved p_obs/p_rel result. The current main H002 claim is the factor-isolated compatibility reranking path, not a full observability/abstention system.

```text
p_obs_AUROC = 1.000000
p_obs_ECE_10 = 0.049266
abstain_recall = 1.000000
direct_Qe_state_AUROC = 1.000000
eval_rows = 265
unobservable_missing_rows = 4
proxy_shortcut_risk = high
pobs_required_for_core_claim = false
pobs_main_claim_allowed = false
```

## Why It Is Not Core

H002's core mechanism is:

```text
T_e = predicate / semantic content
G_e = geometry evidence
Z_e = source score / rank
C_e = compatibility(T_e, G_e)
S2(e) = normalized_source_score(Z_e) * C_e
```

This directly addresses the original problem: source confidence is a mixed signal, so relation reliability should use a factor-isolated predicate-geometry compatibility score before reranking. `p_obs` answers a different question: whether the available evidence is sufficient to make a decision at all.

Therefore `p_obs` is only necessary if the paper claims an observability-aware selective decision system for attachment, containment, occlusion-heavy, or missing-evidence routes. It is not necessary for the current validation-level comparison-route source-reranking claim.

## Why Promotion Is Blocked

- direct `Q_e state_code` also reaches AUROC 1.0, so the learned p_obs result is strongly state/proxy-driven.
- eval `Q_e v2` is audit-proxy diagnostic material, not independent visual/mesh annotation.
- the missing-evidence negative slice has only 4 rows, so broad missing-evidence generalization is not validated.
- this run evaluates p_obs only; it does not rerun a full p_obs/p_rel selective decision system.

## Paper Boundary

Use `p_obs` as optional diagnostic or future/appendix framework component. Do not make it part of the main solved claim unless independent observability labels and full selective-decision metrics later pass.

## Next Step

`h002_core_claim_without_pobs_boundary_update`
