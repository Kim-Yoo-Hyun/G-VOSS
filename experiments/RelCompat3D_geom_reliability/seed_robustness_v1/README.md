# Five-Seed Robustness

This frozen post-hoc analysis refits RelCompat3D-Linear and RelCompat3D-MLP
under five predeclared seed identifiers. The active MLP seed, `20260714`, was
fixed before the analysis and is not reselected. Training rows and linked
counterfactual identities remain unchanged.

The Linear optimizer is deterministic with zero initialization and full-batch
updates. Its five executions therefore test exact repeatability. MLP runs vary
only the model initialization seed. The output reports predictor-by-K
Recall/Violation mean, standard deviation, range, and Source-direction checks.

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_seed_robustness
```
