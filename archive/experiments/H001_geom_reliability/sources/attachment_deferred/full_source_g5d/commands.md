# Attachment Deferred G5d Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm \
  attachment_deferred_full_source_g5d
```

This runs full-source attachment-deferred scoring, source metrics, controls,
and subgraph bootstrap CI under the frozen G5c protocol. It does not promote
`attachment_deferred` to the AAAI main claim.
