# Attachment Deferred G5d Commands

Run from repository root.

Current full-validation extension:

```bash
docker build -t h001-geom-reliability:latest -f configs/h001/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm \
  attachment_deferred_full_validation_g5d
```

Historical 127-scan provenance branch:

```bash
docker build -t h001-geom-reliability:latest -f configs/h001/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm \
  attachment_deferred_full_source_g5d
```

This runs full-source attachment-deferred scoring, source metrics, controls,
and subgraph bootstrap CI under the frozen G5c protocol. It does not promote
`attachment_deferred` to the AAAI main claim.

For long full-validation runs, shard workers can be launched with
`--skip-finalize --shard-start-index <i> --shard-stride <n>` and then merged
with `--finalize-existing-shards`.
