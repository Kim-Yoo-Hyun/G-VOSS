# Attachment Deferred G5b Source Scoring Preflight Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm \
  attachment_deferred_source_scoring_preflight
```

Current default selection is bounded to `20` rows per
source/predicate label. This is a preflight only. It does not compute R@K,
Violation@K, controls, bootstrap CI, or any source metric.

Validation:

```bash
python -m py_compile experiments/H001_geom_reliability/scripts/run_attachment_source_scoring_preflight.py
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/source_scoring_preflight/manifest.json >/dev/null
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/source_scoring_preflight/summary.json >/dev/null
```
