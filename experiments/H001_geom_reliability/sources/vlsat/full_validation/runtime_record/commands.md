# VL-SAT Full-Validation Runtime Commands

Status: `vlsat_full_validation_runtime_record_ready_no_metric_execution` if the manifest has no blockers.

Run from the repository root. The raw dump is GPU/I/O-heavy and must run as a background job.

## Stage Full Validation Runtime Root

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm --build vlsat_full_validation_stage
```

## Refresh Runtime Record

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm --build vlsat_full_validation_runtime_record
```

## Raw-Dump Preflight

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm vlsat_full_validation_raw_preflight
```

Expected preflight files:

- `experiments/H001_geom_reliability/sources/vlsat/full_validation/raw_preflight/summary.json`
- `experiments/H001_geom_reliability/sources/vlsat/full_validation/raw_preflight/report.md`

## Raw Dump Background Job

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s h001_vlsat_full_validation_raw "\
cd /workspace && \
env UID=\$(id -u) GID=\$(id -g) docker compose -f configs/h001/compose.yaml run --rm vlsat_full_validation_raw_dump \
> logs/vlsat_full_validation_raw_${ts}.log 2>&1; \
echo \$? > logs/vlsat_full_validation_raw_${ts}.exit"
```

Expected raw-dump files:

- `experiments/H001_geom_reliability/sources/vlsat/full_validation/raw/raw.jsonl`
- `experiments/H001_geom_reliability/sources/vlsat/full_validation/raw/summary.json`
- `experiments/H001_geom_reliability/sources/vlsat/full_validation/raw/report.md`
- `experiments/H001_geom_reliability/sources/vlsat/full_validation/raw/config.json`

## Completion Verification

```bash
python - <<'PY'
import json
from pathlib import Path
summary = Path('experiments/H001_geom_reliability/sources/vlsat/full_validation/raw/summary.json')
data = json.loads(summary.read_text())
assert data['status'] == 'raw_dump_ready', data['status']
assert data['counts']['selected_scans'] == 157, data['counts']
assert data['counts']['dumped_subgraphs'] == 548, data['counts']
print(json.dumps(data['counts'], sort_keys=True))
PY
```

Promotion rule: this raw dump is still not a paper metric until adapter export, ground-truth JSONL, geometry join, metric evaluation, controls, GT verifier check, bootstrap CI, and table/report regeneration are all rerun under the same full-validation scope.
