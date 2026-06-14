# Open3DSG Raw-Dump Identity Commands

Freeze or refresh the raw-dump identity checklist:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_raw_dump_identity'
```

After a real raw dump exists, rerun the same command, then convert the raw dump:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) OPEN3DSG_RAW_DUMP_JSONL=/workspace/experiments/H001_geom_reliability/sources/open3dsg/raw_dump/raw.jsonl docker compose -f configs/h001/compose.yaml run --rm open3dsg_adapter_raw_dump'
```

Do not run Open3DSG metric/join until raw-dump identity audit and adapter export both pass.
