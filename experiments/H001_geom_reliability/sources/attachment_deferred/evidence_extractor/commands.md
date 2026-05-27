# Attachment Deferred Evidence Extractor Contract Commands

Run from the repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm attachment_deferred_extractor_contract
```

This command creates a design/contract artifact only. It does not read point
clouds, assign verification status, fit calibration, or run source metrics.

Next implementation gate:

```text
G1b_attachment_evidence_extractor_dry_run
```
