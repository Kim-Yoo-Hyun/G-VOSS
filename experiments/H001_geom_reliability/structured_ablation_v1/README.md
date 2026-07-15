# Structured Ablation v1

Last updated: 2026-07-15 KST

This directory owns the frozen K=50/100 falsification and information-ablation
evaluation for the promoted RelCompat3D model. The paper-facing route is fixed
by `routed_public_full_protocol.json` and generated under
`routed_public_full_evaluation/`: it uses the public/full 548-context target and
the same family-slot routing as the primary method. The earlier
`protocol.json` and `evaluation/` pair is retained only as an unrestricted
fusion and recovered/full-coverage mechanism audit for the supplement.

The endpoint control swaps proximity/vertical geometry while deliberately
retaining the original predicate. It is a corruption test, not the valid
relation-algebra transform. Support/contact is left unchanged because no
family-wide endpoint transform is authorized. `compatibility_only` excludes
the source score but still uses predicate-conditioned compatibility; it must
not be called true raw-geometry-only.

Run from the repository root:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm routed_public_ablation_evaluation
```

The primary output root is `routed_public_full_evaluation/` and must be empty
before execution. Its manifest verifies all 548 contexts and 157 scans, the
3,972 exact-label denominator, 533 public Open3DSG prediction contexts plus 15
zero-prediction contexts, support/contact pass-through, and exact equality of
the primary point estimates with the promoted main evaluation.

The unrestricted diagnostic can be reproduced separately with:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm structured_ablation_evaluation
```
