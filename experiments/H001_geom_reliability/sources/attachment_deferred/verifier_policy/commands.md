# Attachment Deferred Verifier Policy Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm attachment_deferred_verifier_policy
```

Expected status:

```json
{"status": "attachment_deferred_verifier_policy_ready_no_decisions_no_metrics"}
```

This command freezes policy artifacts only. It does not apply decisions to
source predictions, fit calibration, compute metrics, or update the main paper
claim.
