# Attachment Deferred G3 Calibration / Counterfactual Route

This command prepares G3 planning artifacts. It does not fit a calibrator, apply
the verifier, score source predictions, or compute metrics.

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm \
  attachment_deferred_calibration_counterfactuals
```

Validation:

```bash
python -m py_compile \
  experiments/H001_geom_reliability/scripts/prepare_attachment_calibration_counterfactuals.py
python -m json.tool \
  experiments/H001_geom_reliability/sources/attachment_deferred/calibration_counterfactuals/manifest.json >/dev/null
```
