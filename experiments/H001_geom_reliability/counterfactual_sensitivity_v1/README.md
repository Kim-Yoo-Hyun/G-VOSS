# Counterfactual-Policy Sensitivity

This directory owns the frozen one-factor-at-a-time sensitivity of the
counterfactual target policy. Each condition regenerates train/development
targets, recomputes train-only normalization, refits the proximity and vertical
orbit-pairwise heads, and evaluates the unchanged family-slot route on the
official 548-context target. Row-level variant exports are not retained.

Run with:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm \
  counterfactual_threshold_sensitivity
```
