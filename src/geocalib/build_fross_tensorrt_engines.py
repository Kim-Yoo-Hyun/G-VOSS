#!/usr/bin/env python3
"""Build Blackwell-local TensorRT engines from FROSS's released ONNX graphs."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import tensorrt as trt


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(onnx_path: Path, engine_path: Path, logger: trt.Logger) -> None:
    builder = trt.Builder(logger)
    config = builder.create_builder_config()
    network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
    parser = trt.OnnxParser(network, logger)
    if not parser.parse(onnx_path.read_bytes()):
        errors = [str(parser.get_error(index)) for index in range(parser.num_errors)]
        raise RuntimeError(f"onnx_parse_failed:{onnx_path}:{errors}")
    config.set_flag(trt.BuilderFlag.FP16)
    serialized = builder.build_serialized_network(network, config)
    if serialized is None:
        raise RuntimeError(f"engine_build_failed:{onnx_path}")
    engine_path.write_bytes(serialized)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-path", type=Path, required=True)
    args = parser.parse_args()
    artifact = args.artifact_path.resolve()
    logger = trt.Logger(trt.Logger.WARNING)
    pairs = (("rt-detr.onnx", "rt-detr.engine"), ("egtr-head.onnx", "egtr-head.engine"))
    for onnx_name, engine_name in pairs:
        onnx_path, engine_path = artifact / onnx_name, artifact / engine_name
        if not onnx_path.is_file():
            raise FileNotFoundError(onnx_path)
        build(onnx_path, engine_path, logger)
    manifest = {
        "schema_version": "h001_fross_blackwell_engine_build_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "engines_ready",
        "tensorrt": trt.__version__,
        "precision": "FP16",
        "artifacts": {
            name: {"sha256": sha256(artifact / name), "bytes": (artifact / name).stat().st_size}
            for pair in pairs for name in pair
        },
    }
    (artifact / "h001_engine_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
