# FROSS / ReplicaSSG Runtime

This directory owns the isolated CUDA/TensorRT runtime used for H001's
ReplicaSSG dataset-level prospective confirmation. It does not own GeoCalib
method fitting; the frozen strict train-only GeoCalib model remains under the
H001 experiment root.

- `Dockerfile.runtime`: official FROSS weight export and RGB-D inference.
- `Dockerfile.render`: Replica semantic-mesh preprocessing and deterministic
  official-trajectory RGB-D rendering.
- `compose.yaml`: environment checks, weight extraction/engine export,
  Replica preprocessing/rendering, FROSS test inference, frozen adapter and
  geometry export, and the paired scene-bootstrap evaluation.

Large Replica assets, rendered sequences, weights, engines, and prediction
pickles remain under ignored `local_dataset/` or row-level experiment paths.
Only Docker-generated, manifest-audited adapter/geometry/metric outputs may be
promoted to paper evidence.

For the scene-wise runner, prepend `scripts/no_stdin_bin/` to `PATH`. The
wrapper leaves the frozen runner and Docker services unchanged and prevents an
attached `docker compose run` process from consuming the runner's scan-list
stdin. This is an orchestration safeguard, not a scientific implementation
variant.
