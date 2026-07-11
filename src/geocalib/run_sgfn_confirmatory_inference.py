#!/usr/bin/env python3
"""Run official SGFN full_l160 and stream identity-preserving full-scan scores."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--preprocess-manifest", type=Path, required=True)
    parser.add_argument("--target-manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-scans", type=int, default=0)
    parser.add_argument("--source-id", default="sgfn_official_full_l160")
    parser.add_argument("--source-split", default="official_test_scans")
    parser.add_argument("--model-name", default="SGFN_full_l160")
    parser.add_argument("--expected-method", default="sgfn")
    parser.add_argument(
        "--target-status",
        default="target_v3_frozen_pre_correct_checkpoint_pre_inference",
    )
    parser.add_argument("--raw-schema", default="h001_sgfn_raw_scan_scores_v1")
    parser.add_argument("--raw-record-type", default="sgfn_full_scan_scores")
    parser.add_argument("--manifest-schema", default="h001_sgfn_raw_inference_manifest_v1")
    parser.add_argument("--ready-status", default="sgfn_raw_inference_ready")
    parser.add_argument("--smoke-status", default="sgfn_inference_smoke_ready")
    parser.add_argument("--docker-service", default="sgfn_inference")
    parser.add_argument("--dataset-mode", choices=("train", "validation", "test"), default="test")
    parser.add_argument("--official-scans-file", type=Path)
    parser.add_argument("--expected-scans", type=int, default=157)
    parser.add_argument("--preprocess-status", default="sgfn_preprocess_ready")
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def install_cpu_color_alignment_patch(util_ply: Any, define: Any) -> dict[str, Any]:
    import trimesh
    from scipy.spatial import cKDTree

    stats: dict[str, Any] = {"scans": 0, "max_query_distance_m": 0.0, "p95_query_distance_m": []}

    def load_rgb_cpu(path: str, target_name: str = define.LABEL_FILE_NAME, with_worker: bool = True):
        del with_worker
        dirname = Path(path)
        aligned_path = dirname / target_name
        raw_path = dirname / define.LABEL_FILE_NAME_RAW
        obj_path = dirname / define.OBJ_NAME
        mesh = trimesh.load(obj_path, process=False)
        aligned = trimesh.load(aligned_path, process=False)
        raw = trimesh.load(raw_path, process=False)
        if not isinstance(mesh, trimesh.Trimesh):
            raise TypeError(f"expected_trimesh:{obj_path}:{type(mesh).__name__}")
        colors = trimesh.visual.uv_to_color(mesh.visual.uv, mesh.visual.material.image)
        distances, indices = cKDTree(np.asarray(mesh.vertices)).query(
            np.asarray(raw.vertices), k=1, workers=-1
        )
        mapped = colors[indices]
        if len(mapped) != len(aligned.vertices):
            raise ValueError(
                f"aligned_raw_vertex_count_mismatch:{dirname.name}:{len(mapped)}:{len(aligned.vertices)}"
            )
        ply_raw = "ply_raw" if "ply_raw" in aligned.metadata else "_ply_raw"
        data = aligned.metadata[ply_raw]["vertex"]["data"]
        properties = aligned.metadata[ply_raw]["vertex"]["properties"]
        normals = np.asarray(aligned.vertex_normals, dtype=np.float32)
        for name, values in (
            ("nx", normals[:, 0]),
            ("ny", normals[:, 1]),
            ("nz", normals[:, 2]),
        ):
            if name not in data:
                properties[name] = "<f4"
            data[name] = values
        data["red"] = mapped[:, 0]
        data["green"] = mapped[:, 1]
        data["blue"] = mapped[:, 2]
        stats["scans"] += 1
        stats["max_query_distance_m"] = max(
            float(stats["max_query_distance_m"]), float(np.max(distances))
        )
        stats["p95_query_distance_m"].append(float(np.percentile(distances, 95)))
        return aligned

    util_ply.load_rgb = load_rgb_cpu
    return stats


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def install_pyg_private_api_patch() -> None:
    """Replace the removed PyG 1.x private collector with direct edge gathers."""
    from ssg.models.edge_encoder import EdgeDescriptor_SGFN  # type: ignore

    def forward(self, descriptor, edges_indices):
        if edges_indices.shape[0] != 2:
            edges_indices = edges_indices.t().contiguous()
        source = descriptor[edges_indices[0]]
        target = descriptor[edges_indices[1]]
        return self.message(x_i=target, x_j=source)

    EdgeDescriptor_SGFN.forward = forward


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    source = resolve(root, args.source_root)
    config_path = resolve(root, args.config)
    checkpoint_path = resolve(root, args.checkpoint)
    preprocess_manifest_path = resolve(root, args.preprocess_manifest)
    target_manifest_path = resolve(root, args.target_manifest)
    out = resolve(root, args.out)
    raw_path = out / "raw.jsonl"
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"nonempty_output:{out}")
    required = [source, config_path, checkpoint_path, preprocess_manifest_path, target_manifest_path]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing_inputs:{missing}")
    preprocess_manifest = json.loads(preprocess_manifest_path.read_text(encoding="utf-8"))
    target_manifest = json.loads(target_manifest_path.read_text(encoding="utf-8"))
    if preprocess_manifest.get("status") != args.preprocess_status:
        raise ValueError(
            f"preprocess_not_ready:{preprocess_manifest.get('status')}:{args.preprocess_status}"
        )
    if target_manifest.get("status") != args.target_status:
        raise ValueError(
            f"target_not_ready:{target_manifest.get('status')}:{args.target_status}"
        )
    if not torch.cuda.is_available():
        raise RuntimeError("cuda_required_for_sgfn_confirmatory_inference")

    compat = root / "src/geocalib/sgfn_compat"
    sys.path.insert(0, str(compat))
    sys.path.insert(1, str(source))
    import codeLib  # type: ignore
    import ssg.config as ssg_config  # type: ignore
    from ssg.utils import util_ply  # type: ignore
    from ssg import define  # type: ignore

    color_stats = install_cpu_color_alignment_patch(util_ply, define)
    install_pyg_private_api_patch()
    cfg = codeLib.Config(str(config_path))
    cfg.DEVICE = torch.device("cuda")
    cfg.MODE = "eval"
    cfg.name = args.model_name
    cfg.log_level = "INFO"
    set_seed(int(cfg.SEED))

    started = time.time()
    dataset = ssg_config.get_dataset(cfg, args.dataset_mode)
    if str(cfg.model.method) != args.expected_method:
        raise ValueError(f"source_method_mismatch:{cfg.model.method}:{args.expected_method}")
    relation_names = list(dataset.relationNames)
    class_names = list(dataset.classNames)
    if len(class_names) != 160 or len(relation_names) != 26 or "none" in relation_names:
        raise ValueError(
            f"source_vocab_mismatch:classes={len(class_names)}:relations={len(relation_names)}:none={'none' in relation_names}"
        )
    model = ssg_config.get_model(cfg, num_obj_cls=len(class_names), num_rel_cls=len(relation_names))
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model"], strict=True)
    model.eval()

    out.mkdir(parents=True, exist_ok=True)
    scan_counts: list[dict[str, Any]] = []
    run_count = len(dataset) if args.max_scans <= 0 else min(args.max_scans, len(dataset))
    with raw_path.open("w", encoding="utf-8") as handle, torch.no_grad():
        for index in range(run_count):
            data = dataset[index]
            scan_id = str(data["scan_id"])
            node_ids = [int(value) for value in data["node"].oid.cpu().tolist()]
            edge_index_tensor = data["node", "to", "node"].edge_index.cpu()
            edge_indices = edge_index_tensor.t().contiguous().tolist()
            expected_edges = len(node_ids) * max(len(node_ids) - 1, 0)
            if len(edge_indices) != expected_edges:
                raise ValueError(
                    f"not_full_directed_graph:{scan_id}:{len(node_ids)}:{len(edge_indices)}:{expected_edges}"
                )
            data = data.to(cfg.DEVICE)
            _, edge_logits = model(data)
            if edge_logits is None or list(edge_logits.shape) != [len(edge_indices), len(relation_names)]:
                raise ValueError(f"edge_logit_shape_mismatch:{scan_id}:{getattr(edge_logits, 'shape', None)}")
            scores = torch.sigmoid(edge_logits).detach().cpu().float().numpy()
            record = {
                "schema_version": args.raw_schema,
                "record_type": args.raw_record_type,
                "source_id": args.source_id,
                "source_split": args.source_split,
                "scan_id": scan_id,
                "node_instance_ids": node_ids,
                "edge_indices": edge_indices,
                "relation_names": relation_names,
                "relation_score_type": "sigmoid_probability",
                "rel_scores": scores.tolist(),
            }
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            handle.flush()
            scan_counts.append(
                {"scan_id": scan_id, "nodes": len(node_ids), "edges": len(edge_indices)}
            )
            print(
                json.dumps(
                    {
                        "scan_index": index + 1,
                        "scan_total": run_count,
                        "scan_id": scan_id,
                        "nodes": len(node_ids),
                        "edges": len(edge_indices),
                    }
                ),
                flush=True,
            )
            del data, edge_logits, scores
            torch.cuda.empty_cache()

    scan_ids = {row["scan_id"] for row in scan_counts}
    official_scans_path = (
        resolve(root, args.official_scans_file)
        if args.official_scans_file
        else source / f"files/cvpr/{args.dataset_mode}_scans.txt"
    )
    official_scans = {
        line.strip()
        for line in official_scans_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    color_p95 = color_stats.pop("p95_query_distance_m")
    is_full = args.max_scans <= 0
    color_alignment_required = args.expected_method == "sgfn"
    validations = {
        "raw_scan_count_matches_mode": len(scan_counts) == (args.expected_scans if is_full else run_count),
        "raw_scans_match_scope": scan_ids == official_scans if is_full else scan_ids.issubset(official_scans),
        "all_graphs_full_directed": all(
            row["edges"] == row["nodes"] * (row["nodes"] - 1) for row in scan_counts
        ),
        "source_vocab_160_26": len(class_names) == 160 and len(relation_names) == 26,
        "checkpoint_loaded_strict": True,
        "source_method_matches_frozen": str(cfg.model.method) == args.expected_method,
        "color_alignment_applied_per_scan_or_not_used_by_method": (
            int(color_stats["scans"]) == len(scan_counts)
            if color_alignment_required
            else int(color_stats["scans"]) == 0
        ),
    }
    status = (
        args.ready_status
        if is_full and all(validations.values())
        else args.smoke_status
        if not is_full and all(validations.values())
        else "blocked_sgfn_raw_inference_audit"
    )
    manifest = {
        "schema_version": args.manifest_schema,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source_id": args.source_id,
        "source_method": str(cfg.model.method),
        "counts": {
            "scans": len(scan_counts),
            "nodes": sum(row["nodes"] for row in scan_counts),
            "directed_edges": sum(row["edges"] for row in scan_counts),
            "relation_scores": sum(row["edges"] for row in scan_counts) * len(relation_names),
            "min_nodes": min(row["nodes"] for row in scan_counts),
            "max_nodes": max(row["nodes"] for row in scan_counts),
        },
        "validations": validations,
        "runtime": {
            "seconds": time.time() - started,
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0),
            "seed": int(cfg.SEED),
            "pythonhashseed": os.environ.get("PYTHONHASHSEED"),
            "max_scans": args.max_scans,
            "dataset_mode": args.dataset_mode,
        },
        "compatibility": {
            "wandb": "non-network import stub; logging.method=none",
            "pytictoc": "timer-compatible local stub",
            "pyg_edge_descriptor": "removed PyG 1.x private __collect__/__check_input__ calls replaced by mathematically identical source/target tensor gathers",
            "rgb_alignment": "same OBJ-texture nearest-vertex mapping as source, using scipy cKDTree instead of unavailable knn_cuda",
            "rgb_alignment_max_query_distance_m": color_stats["max_query_distance_m"],
            "rgb_alignment_p95_query_distance_m_max": max(color_p95) if color_p95 else None,
            "rgb_alignment_required_by_method": color_alignment_required,
            "full_edge_export": "data.max_num_edge=-1 to satisfy frozen every-available-edge export contract",
        },
        "inputs": {
            "config": {"path": relpath(root, config_path), "sha256": sha256_file(config_path)},
            "checkpoint": {"path": relpath(root, checkpoint_path), "sha256": sha256_file(checkpoint_path)},
            "preprocess_manifest": relpath(root, preprocess_manifest_path),
            "target_manifest": relpath(root, target_manifest_path),
            "official_scans": {"path": relpath(root, official_scans_path), "sha256": sha256_file(official_scans_path)},
        },
        "outputs": {"raw_jsonl": relpath(root, raw_path), "sha256": sha256_file(raw_path)},
        "docker_command": f"env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm {args.docker_service}",
    }
    write_json(out / "manifest.json", manifest)
    print(json.dumps({"status": manifest["status"], "counts": manifest["counts"], "out": relpath(root, out)}))
    return 0 if manifest["status"] in {args.ready_status, args.smoke_status} else 2


if __name__ == "__main__":
    raise SystemExit(main())
