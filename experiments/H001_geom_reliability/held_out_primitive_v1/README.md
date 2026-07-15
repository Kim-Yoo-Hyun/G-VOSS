# Held-out Primitive Diagnostic

Status: completed; all 14 integrity validations pass.

This strict train-only diagnostic refits three relation-algebra compatibility
variants after removing (1) the exact normalized scalar consumed by the
verifier, (2) its broader reconstructible measurement family, or (3) all but
alternative overlap/horizontal-context evidence. Every condition preserves the
main orbit projection and family-slot route; support/contact remains a source-
order pass-through.

The experiment measures sensitivity to construct overlap. It cannot establish
an independent physical-validity reference because the constructed training
labels and verifier still share the same scenes, predicates, and broader
geometry-generating process.

Run with the `held_out_primitive_evaluation` service in
`configs/h001/compose.structured.yaml`. Compact models, metrics, scan-cluster
intervals, and a manifest are written to `evaluation/`.

The exact-scalar holdout preserves nearly the full routed result. Removing the
entire distance/vertical measurement family retains a strong Open3DSG effect
but yields near-source K=50 violation on VL-SAT and SGFN. At K=100, every
held-out condition improves both point metrics on all three predictors. The
result rules out literal reuse of one verifier scalar, but not broader
dependence on correlated geometry.

Canonical run: `logs/h001_held_out_primitive_rerun_20260715_200343.log`.
The preceding failed integrity run is preserved at
`logs/h001_held_out_primitive_20260715_200058.log`; it omitted two official
GT-free contexts from the Open3DSG resampling universe and changed no model,
feature condition, score, or point estimate. The protocol records this
execution erratum.

Canonical SHA256 values:

- protocol: `545dc0d8cabac1a285af3e0f4815d39f830943481e1efc08be5ba633a1835775`
- manifest: `6fd65c38fc7c95998cf779b6b53b2d2962e498a55a2bdab0f0e661c635997bbf`
- summary: `0657a582104c251ceacb007ba3f7ed2b0f358fa88b508943faffc01eb9cef527`
- models: `ffd204564d1dd66b7cd0e44c4c0081bc8fa994e5ffd729c39a146335a2b3136b`
