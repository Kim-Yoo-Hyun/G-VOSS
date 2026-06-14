# Attachment Deferred G4b Error / Visual Sanity Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm \
  attachment_deferred_error_visual_sanity
```

Validation:

```bash
python -m py_compile experiments/H001_geom_reliability/scripts/inspect_attachment_policy_errors.py
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/error_visual_sanity/manifest.json >/dev/null
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/error_visual_sanity/summary.json >/dev/null
```

This command generates an error taxonomy, calibration filter, and targeted
visual sanity queue only. It does not fit calibration, score source
predictions, compute metrics, or update the main AAAI claim.
