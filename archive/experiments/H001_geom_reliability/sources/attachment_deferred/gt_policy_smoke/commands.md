# Attachment Deferred G4 GT Policy Smoke Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm \
  attachment_deferred_gt_policy_smoke
```

Validation:

```bash
python -m py_compile experiments/H001_geom_reliability/scripts/run_attachment_gt_policy_smoke.py
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/gt_policy_smoke/manifest.json >/dev/null
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/gt_policy_smoke/summary.json >/dev/null
```

This command applies the frozen policy to smoke and train-dev GT/counterfactual
rows only. It does not run VL-SAT/Open3DSG attachment source metrics, fit
calibration, or update the main AAAI claim.
