# Construct-Dependence Package

This folder owns the P0-4 hash-verified evidence package. It makes the overlap
between training-target construction, the primary OBB verifier, and the
point/mesh audit explicit, then indexes the existing feature-removal,
counterfactual, uncertainty-policy, component-removal, and point/mesh evidence.

The package is a provenance and construct-validity audit. It does not create
human physical-validity labels or independent cross-dataset evidence.

Run through Docker:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_construct_dependence
```
