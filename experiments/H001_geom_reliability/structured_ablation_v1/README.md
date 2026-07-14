# Structured Ablation v1

Last updated: 2026-07-14 KST

This directory owns the frozen K=50/100 falsification and information-ablation
evaluation for the promoted RelCompat3D model. `protocol.json` fixes every
mapping, donor policy, input hash, source, denominator, K, and bootstrap unit
before `evaluation/` is generated.

The endpoint control swaps proximity/vertical geometry while deliberately
retaining the original predicate. It is a corruption test, not the valid
relation-algebra transform. Support/contact is left unchanged because no
family-wide endpoint transform is authorized. `compatibility_only` excludes
the source score but still uses predicate-conditioned compatibility; it must
not be called true raw-geometry-only.

Run from the repository root:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm structured_ablation_evaluation
```

The output root is `evaluation/` and must be empty before execution.
