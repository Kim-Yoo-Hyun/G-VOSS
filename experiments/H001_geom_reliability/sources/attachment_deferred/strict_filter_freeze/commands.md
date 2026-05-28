# Attachment Deferred G4c Strict Filter Freeze Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm \
  attachment_deferred_strict_filter_freeze
```

Validation:

```bash
python -m py_compile experiments/H001_geom_reliability/scripts/freeze_attachment_strict_calibration_filter.py
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/strict_filter_freeze/manifest.json >/dev/null
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/strict_filter_freeze/summary.json >/dev/null
```

This command freezes strict calibration rows only. It does not fit calibration,
score source predictions, compute source metrics, run controls/bootstrap, or
update the main AAAI claim.
