# Structured Main Evaluation

Status: `completed`

This branch promotes the train-only `orbit_pairwise_projected` compatibility
selected by the frozen relation-algebra development gate. Paper-facing prose
calls it **relation-algebra-constrained compatibility**; the long artifact ID
is retained only for provenance.

The compatibility model never consumes source score, source rank, source
identity, or source-specific exact-label correctness. It was fit on the 1,061
training scans with training-only normalization. The 117-scan internal split
was used for method diagnostics, and the 157-scan official validation scope is
used for 3DSSG benchmark evaluation.

The Docker evaluation reports source score, the structured product,
rank-average, RRF, pooled product, hard-rule filtering, an unprojected
family-product ablation, and compatibility-only. It also regenerates
the all-status and uncertainty-sensitive metrics from the same selected rows.
No row-level duplicate of the large verification inputs is written.

Run:

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.structured.yaml run --rm structured_main_evaluation
```

Compact outputs are written to `evaluation/` only after protocol and input-hash
validation. The completed manifest reports every validation as `true`; the
locked compatibility-model SHA256 is
`62d251f3ce60e2db54eb1748c277350e3b9e2c7c9d2be0312cf2fb323b761410`.

The separate `scan_cluster_sensitivity` service keeps every ranking fixed and
resamples all relation contexts belonging to each sampled scan together. Its
frozen protocol is `scan_cluster_protocol.json`, and its compact outputs are
written to `scan_cluster_sensitivity/`.
