# Routing Constraint Controls

This folder owns the frozen P0-3 analysis of the family-aware routing
constraint. The direct matched comparison is `family_slots` versus
`pv_global`: both use identical candidates, compatibility, product utility,
support/contact positions, and support/contact order. Only the separate
proximity and vertical-order queues are removed in `pv_global`.

`support_order_only` and `all_families` progressively relax additional scope
constraints. They are reported as interpretation controls, not replacement
methods selected from final-validation results.

Run through Docker:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_routing_constraints
```

The command refuses to overwrite a nonempty output directory. Exact external
row paths and hashes are frozen in `protocol.json`.
