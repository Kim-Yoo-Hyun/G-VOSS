# Attachment Deferred G5c Full-Source Protocol Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm \
  attachment_deferred_full_source_protocol
```

This freezes the source coverage, sharding, scoring schema, metric conditions,
control order, and claim boundary before any full-source attachment metrics.
It does not compute R@K, Violation@K, controls, bootstrap CI, or any source
metric.

Validation:

```bash
python -m py_compile experiments/H001_geom_reliability/scripts/freeze_attachment_full_source_protocol.py
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/full_source_protocol/manifest.json >/dev/null
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/full_source_protocol/protocol.json >/dev/null
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/full_source_protocol/denominator_audit.json >/dev/null
```
