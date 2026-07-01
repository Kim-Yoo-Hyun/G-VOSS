# Attachment Deferred G5c Full-Source Protocol Commands

Run from repository root.

Current full-validation extension:

```bash
docker build -t h001-geom-reliability:latest -f configs/h001/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm \
  attachment_deferred_full_validation_protocol
```

Historical 127-scan provenance branch:

```bash
docker build -t h001-geom-reliability:latest -f configs/h001/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm \
  attachment_deferred_full_source_protocol
```

This freezes the source coverage, sharding, scoring schema, metric conditions,
control order, and claim boundary before any full-source attachment metrics.
It does not compute R@K, Violation@K, controls, bootstrap CI, or any source
metric.

Validation:

```bash
python -m py_compile src/geocalib/freeze_attachment_full_source_protocol.py
python -m json.tool <active-output-root>/manifest.json >/dev/null
python -m json.tool <active-output-root>/protocol.json >/dev/null
python -m json.tool <active-output-root>/denominator_audit.json >/dev/null
```
