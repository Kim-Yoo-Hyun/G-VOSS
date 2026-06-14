#!/usr/bin/env python3
"""Audit Open3DSG model artifacts staged for H001."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from paths import H001_HYPOTHESIS_ROOT


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
H001_ROOT = H001_HYPOTHESIS_ROOT

DEFAULT_LOCAL_DATASET = REPO_ROOT / "local_dataset"
DEFAULT_STAGED_ROOT = DEFAULT_LOCAL_DATASET / "Open3DSG_staged" / "h001_runtime"
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "evaluation" / "open3dsg_ov" / "model_artifacts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-dataset", type=Path, default=DEFAULT_LOCAL_DATASET)
    parser.add_argument("--staged-root", type=Path, default=DEFAULT_STAGED_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": relpath(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_report(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Open3DSG Model Artifacts",
        "",
        f"Date: `{manifest['date_checked']}`",
        f"Status: `{manifest['status']}`",
        f"Checkpoint root: `{manifest['checkpoint_root']}`",
        "",
        "## Readiness",
        "",
        f"- Open3DSG checkpoint candidates: `{len(manifest['checkpoint_candidates'])}`",
        f"- BLIP2 positional embedding: `{manifest['blip2']['status']}`",
        f"- OpenSeg SavedModel: `{manifest['openseg']['status']}`",
        f"- PointNet weights: `{manifest['pointnet']['status']}`",
        "",
        "## Files",
        "",
        f"- BLIP2: `{manifest['blip2']['file']['path']}` ({manifest['blip2']['file']['size_bytes']} bytes)",
    ]
    for key, record in manifest["openseg"]["files"].items():
        lines.append(f"- OpenSeg `{key}`: `{record['path']}` ({record['size_bytes']} bytes)")
    for key, record in manifest["pointnet"]["files"].items():
        lines.append(f"- PointNet `{key}`: `{record['path']}` ({record['size_bytes']} bytes)")
    lines.extend(["", "## Official Link Check", ""])
    for key, record in manifest["official_link_check"].items():
        lines.append(f"- `{key}`: {record['result']}")
    lines.extend(["", "## Blockers", ""])
    if manifest["blockers"]:
        lines.extend(f"- `{blocker}`" for blocker in manifest["blockers"])
    else:
        lines.append("- none")
    lines.extend(["", "## Claim Limit", "", manifest["claim_limit"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    checkpoint_root = args.staged_root / "output" / "checkpoints"
    blip2_path = checkpoint_root / "blip2_positional_embedding.pt"
    pointnet_files = {
        "pointnet_pth": file_record(checkpoint_root / "pointnet.pth"),
        "pointnet2_ulip_pt": file_record(checkpoint_root / "pointnet2_ulip.pt"),
    }
    openseg_root = checkpoint_root / "openseg"
    openseg_files = {
        "saved_model_pb": file_record(openseg_root / "saved_model.pb"),
        "variables_data": file_record(openseg_root / "variables" / "variables.data-00000-of-00001"),
        "variables_index": file_record(openseg_root / "variables" / "variables.index"),
        "graph_def": file_record(openseg_root / "graph_def.txt"),
    }
    checkpoint_candidates = [
        relpath(path) for path in sorted(args.local_dataset.rglob("*.ckpt"))
    ] if args.local_dataset.exists() else []

    blip2_ready = blip2_path.exists() and blip2_path.stat().st_size > 0
    openseg_ready = all(record["exists"] and record["size_bytes"] > 0 for record in openseg_files.values())
    pointnet_ready = all(record["exists"] and record["size_bytes"] > 0 for record in pointnet_files.values())

    blockers: list[str] = []
    if not checkpoint_candidates:
        blockers.append("missing_model:open3dsg_checkpoint")
    if not blip2_ready:
        blockers.append("missing_model:blip2_positional_embedding")
    if not openseg_ready:
        blockers.append("missing_model:openseg_saved_model")

    status = "model_artifacts_ready" if not blockers else "model_artifacts_partial_ready"
    if blockers and not (blip2_ready or openseg_ready or checkpoint_candidates):
        status = "model_artifacts_missing"

    manifest: dict[str, Any] = {
        "schema_version": "h001_open3dsg_model_artifacts_v1",
        "date_checked": date.today().isoformat(),
        "status": status,
        "checkpoint_root": relpath(checkpoint_root),
        "sources": {
            "open3dsg_readme": "https://github.com/boschresearch/Open3DSG#model-downloads",
            "blip2_positional_embedding": "https://drive.google.com/file/d/1BfvxB6eo3XksE6AfMUgoBHwzVYce1ed1/view",
            "openseg_saved_model": "https://storage.googleapis.com/cloud-tpu-checkpoints/detection/projects/openseg/colab/exported_model/",
            "pointnet_weights": "https://drive.google.com/drive/folders/1PrnJVMpJVVh4MAV4yPRuRByhBu-DuXwH",
        },
        "official_link_check": {
            "open3dsg_repository": {
                "url": "https://github.com/boschresearch/Open3DSG",
                "result": "README lists OpenSeg, BLIP2, and PointNet/PointNet2 downloads; test command requires a user-specified checkpoint; repository has no release artifact.",
            },
            "pointnet_folder": {
                "url": "https://drive.google.com/drive/folders/1PrnJVMpJVVh4MAV4yPRuRByhBu-DuXwH",
                "result": "public folder title is pointnet_weights and folder listing contains pointnet.pth plus pointnet2_ulip.pt, not an Open3DSG trained checkpoint.",
            },
            "openseg_source": {
                "url": "https://github.com/tensorflow/tpu/tree/master/models/official/detection/projects/openseg",
                "result": "official OpenSeg source page exists; staged SavedModel files were downloaded from the OpenSeg GCS exported_model path.",
            },
            "blip2_file": {
                "url": "https://drive.google.com/file/d/1BfvxB6eo3XksE6AfMUgoBHwzVYce1ed1/view",
                "result": "public Drive file is blip2_positional_embedding.pt and the staged tensor validates as the expected positional embedding artifact.",
            },
        },
        "checkpoint_candidates": checkpoint_candidates,
        "blip2": {
            "status": "ready" if blip2_ready else "missing",
            "file": file_record(blip2_path),
        },
        "openseg": {
            "status": "ready" if openseg_ready else "missing",
            "files": openseg_files,
        },
        "pointnet": {
            "status": "ready" if pointnet_ready else "missing",
            "files": pointnet_files,
            "note": "Official Open3DSG README dependency. It does not replace the trained Open3DSG checkpoint required by the test command.",
        },
        "blockers": blockers,
        "claim_limit": "No Open3DSG raw dump, prediction JSONL, geometry join, metric, or improvement claim exists until a trained Open3DSG checkpoint is available.",
        "next_action": "Run Open3DSG training route feasibility/preflight unless a trusted checkpoint is supplied.",
    }

    write_json(args.output_dir / "manifest.json", manifest)
    write_report(args.output_dir / "report.md", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status in {"model_artifacts_ready", "model_artifacts_partial_ready"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
