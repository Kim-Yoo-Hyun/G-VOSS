# Attachment Deferred G5 Calibration Fit Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm \
  attachment_deferred_calibration_fit
```

Validation:

```bash
python -m py_compile experiments/H001_geom_reliability/scripts/fit_attachment_strict_calibration.py
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/calibration_fit/manifest.json >/dev/null
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/calibration_fit/metrics.json >/dev/null
```

This command fits calibration only. It does not score source predictions,
compute source metrics, run controls/bootstrap, or update the main AAAI claim.
