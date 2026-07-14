# H001 Containers

Last updated: 2026-07-14 KST

`compose.structured.yaml` is the compact paper-facing entry point for the
strict train-only relation-algebra model and promoted main evaluation. It avoids
the historical source-preparation and optional extension services retained in
the full `compose.yaml`.

From the repository root:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm relation_algebra_development
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm structured_main_evaluation
```

Both services mount the repository at `/workspace`. Their protocols enumerate
the required strict split, compatibility model, verification rows, and exact
input hashes. Existing nonempty output directories are rejected so a previous
result cannot be silently overwritten.

The `scan_cluster_sensitivity` service leaves scores and rankings unchanged and
resamples the 157 scan identifiers, carrying all relation contexts from each
sampled scan together.

The `structured_ablation_evaluation` service keeps the promoted model fixed and
evaluates the frozen K=50/100 wrong-predicate, wrong-pair, shuffled-geometry,
endpoint-corruption, distance-only, and no-source-score controls. Its protocol
and output owner is `experiments/H001_geom_reliability/structured_ablation_v1/`.

`compose.yaml` remains the full recovery/service registry for historical source
generation and optional analyses. The paper experiment image is defined by
`Dockerfile`; the manuscript image is separately defined by
`paper/aaai/Dockerfile.tex`.

## Image Roles

| Image | Current role | Retention rule |
| --- | --- | --- |
| `h001-geom-reliability:latest` | focused structured method, metrics, controls, and sensitivity | keep for the active experiment route |
| `h001-sgfn-confirmatory:cu128` | SGFN/SGPN source inference and exact full-source recovery | keep when full inference reproduction is required |
| `h001-aaai27-tex:20260712` | canonical AAAI-27 main/supplement/checklist build | keep for the active manuscript route |
| `h001-aaai-tex:20260526` | superseded AAAI-26 build | removable |
| `h001-fross-replicassg:cu128-trt108`, `h001-replicassg-render:habitat022` | de-scoped ReplicaSSG/FROSS development only | removable for active-submission preservation; retain only to rerun that diagnostic |
| `h001-real-proposals:ovdet-v0` | non-main proposal prototype with no active compose reference | removable |

`h001-fross-replicassg:cu121` and
`h001-fross-replicassg:cu128-trt108` currently point to the same image ID; the
former is a redundant tag and removing only that tag does not reclaim image
layers. The authoritative cleanup matrix and pre-removal checks are in
`docs/reproducibility.md`.
