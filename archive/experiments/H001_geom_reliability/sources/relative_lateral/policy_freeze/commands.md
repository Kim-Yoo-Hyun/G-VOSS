# Relative Lateral Policy Freeze Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm \
  relative_lateral_policy_freeze
```

This freezes family split, denominator, geometry policy, and threshold
provenance only. It does not run source metrics or update the paper claim.
