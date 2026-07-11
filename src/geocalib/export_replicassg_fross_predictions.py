#!/usr/bin/env python3
"""Export the frozen FROSS/ReplicaSSG source output into H001 candidate rows.

The adapter deliberately does not read ReplicaSSG relationship annotations.
Ground-truth relation labels enter only in the later metric stage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from plyfile import PlyData
from scipy.spatial import KDTree


SCHEMA_VERSION = "h001_replicassg_fross_adapter_v1"
PREDICATE_MAPPING = {
    "above": ("higher than", "relative_vertical"),
    "near": ("close by", "proximity"),
    "under": ("lower than", "relative_vertical"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--prediction-pkl", type=Path, required=True)
    parser.add_argument("--annotation-root", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--match-distance", type=float, default=0.1)
    parser.add_argument("--minimum-overlap", type=float, default=0.5)
    parser.add_argument("--maximum-ambiguity-ratio", type=float, default=0.75)
    parser.add_argument("--docker-service", default="replicassg_fross_adapter")
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dump_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def official_object_order(
    objects: dict[str, Any], mapping: dict[str, Any], scans: list[str]
) -> dict[str, list[tuple[int, str]]]:
    result: dict[str, list[tuple[int, str]]] = {}
    vg_classes = set(mapping["VisualGenome_list"])
    replica_to_vg = mapping["Replica2VisualGenome"]
    for scan in objects["scans"]:
        scan_id = str(scan["scan"])
        if scan_id not in scans:
            continue
        kept: list[tuple[int, str]] = []
        for obj in scan["objects"]:
            label = str(obj["label"])
            mapped = replica_to_vg.get(label)
            if mapped in vg_classes:
                kept.append((int(obj["id"]), label))
        result[scan_id] = kept
    return result


def load_gt_points(path: Path, allowed_ids: set[int]) -> tuple[np.ndarray, np.ndarray]:
    mesh = PlyData.read(str(path))
    vertices = mesh["vertex"]
    points = np.stack([vertices["x"], vertices["y"], vertices["z"]], axis=1)
    object_ids = np.asarray(vertices["objectId"], dtype=np.int64)
    mask = np.isin(object_ids, np.asarray(sorted(allowed_ids), dtype=np.int64))
    return np.asarray(points[mask], dtype=np.float64), object_ids[mask]


def official_match(
    pred_segments: list[Any],
    gt_points: np.ndarray,
    gt_point_ids: np.ndarray,
    ordered_gt_ids: list[int],
    *,
    distance: float,
    minimum_overlap: float,
    maximum_ambiguity_ratio: float,
) -> tuple[dict[int, int], np.ndarray]:
    """Reproduce FROSS Merging/evaluate.py's GT-to-prediction matching."""
    n_gt, n_pred = len(ordered_gt_ids), len(pred_segments)
    overlap_count = np.zeros((n_gt, n_pred), dtype=np.float64)
    if n_gt == 0 or n_pred == 0 or len(gt_points) == 0:
        return {}, overlap_count
    gt_index = {object_id: index for index, object_id in enumerate(ordered_gt_ids)}
    tree = KDTree(gt_points)
    for pred_idx, segment in enumerate(pred_segments):
        seg = np.asarray(segment, dtype=np.float64)
        if seg.ndim != 2 or seg.shape[1] != 3 or len(seg) == 0:
            continue
        _, indices = tree.query(seg, distance_upper_bound=distance)
        valid = indices != tree.n
        matched_ids = gt_point_ids[indices[valid]]
        for object_id in matched_ids:
            overlap_count[gt_index[int(object_id)], pred_idx] += 1
        overlap_fraction = overlap_count[:, pred_idx] / len(seg)
        order = np.flip(np.argsort(overlap_count[:, pred_idx], kind="stable"))
        best = int(order[0])
        second = int(order[1]) if n_gt > 1 else best
        best_fraction = float(overlap_fraction[best])
        second_fraction = float(overlap_fraction[second]) if n_gt > 1 else 0.0
        ambiguity_ratio = second_fraction / best_fraction if best_fraction > 0 else float("inf")
        if best_fraction < minimum_overlap or ambiguity_ratio > maximum_ambiguity_ratio:
            overlap_count[:, pred_idx] = 0
        else:
            overlap_count[np.arange(n_gt) != best, pred_idx] = 0

    pred_to_gt: dict[int, int] = {}
    for gt_idx, object_id in enumerate(ordered_gt_ids):
        pred_idx = int(np.argmax(overlap_count[gt_idx]))
        if overlap_count[gt_idx, pred_idx] > 0:
            if pred_idx in pred_to_gt:
                raise ValueError(f"official_matching_not_one_to_one:pred={pred_idx}")
            pred_to_gt[pred_idx] = object_id
    return pred_to_gt, overlap_count


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    prediction_path = resolve(root, args.prediction_pkl)
    annotation_root = resolve(root, args.annotation_root)
    dataset_root = resolve(root, args.dataset_root)
    protocol_path = resolve(root, args.protocol)
    out = resolve(root, args.out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"nonempty_output:{out}")

    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol.get("status") != "frozen_before_source_prediction":
        raise ValueError("prospective_protocol_not_frozen")
    expected_prediction = resolve(root, Path(protocol["semantic_source"]["source_prediction_path"]))
    if prediction_path.resolve() != expected_prediction.resolve():
        raise ValueError("prediction_path_differs_from_frozen_protocol")
    if not prediction_path.is_file():
        raise FileNotFoundError(prediction_path)
    if (args.match_distance, args.minimum_overlap, args.maximum_ambiguity_ratio) != (0.1, 0.5, 0.75):
        raise ValueError("object_matching_threshold_differs_from_frozen_protocol")

    scans = list(protocol["dataset"]["test_scans"])
    objects_path = annotation_root / "objects.json"
    mapping_path = annotation_root / "replica_to_visual_genome.json"
    objects = json.loads(objects_path.read_text(encoding="utf-8"))
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    object_order = official_object_order(objects, mapping, scans)
    relation_indices = {
        source: mapping["VisualGenome_rel"].index(source) for source in PREDICATE_MAPPING
    }
    # The official artifact is a trusted local output produced by the frozen source container.
    with prediction_path.open("rb") as handle:
        predictions = pickle.load(handle)
    if set(predictions) != set(scans):
        raise ValueError(
            f"prediction_scan_set_mismatch:missing={sorted(set(scans)-set(predictions))}:"
            f"extra={sorted(set(predictions)-set(scans))}"
        )

    rows: list[dict[str, Any]] = []
    matches: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    by_family: Counter[str] = Counter()
    by_predicate: Counter[str] = Counter()
    by_scan: Counter[str] = Counter()
    for scan_id in scans:
        pred = predictions[scan_id]
        ordered = object_order[scan_id]
        gt_ply = dataset_root / "data" / scan_id / "labels.instances.annotated.v2.ply"
        gt_points, gt_point_ids = load_gt_points(gt_ply, {item[0] for item in ordered})
        pred_to_gt, overlap = official_match(
            list(pred["pcd"]), gt_points, gt_point_ids, [item[0] for item in ordered],
            distance=args.match_distance,
            minimum_overlap=args.minimum_overlap,
            maximum_ambiguity_ratio=args.maximum_ambiguity_ratio,
        )
        gt_labels = dict(ordered)
        for pred_idx, gt_id in sorted(pred_to_gt.items()):
            gt_idx = [item[0] for item in ordered].index(gt_id)
            matches.append({
                "scan_id": scan_id,
                "source_node_index": pred_idx,
                "object_id": gt_id,
                "object_label": gt_labels[gt_id],
                "overlap_count": int(overlap[gt_idx, pred_idx]),
                "source_segment_points": int(len(pred["pcd"][pred_idx])),
                "overlap_fraction": float(overlap[gt_idx, pred_idx] / len(pred["pcd"][pred_idx])),
            })

        edge_index = np.asarray(pred["edge_index"])
        edge_cls = np.asarray(pred["edge_cls"], dtype=np.float64)
        if edge_index.size == 0:
            continue
        if edge_index.ndim != 2 or edge_index.shape[0] != 2:
            raise ValueError(f"invalid_edge_index_shape:{scan_id}:{edge_index.shape}")
        if edge_cls.ndim != 2 or edge_cls.shape[0] != edge_index.shape[1]:
            raise ValueError(f"invalid_edge_cls_shape:{scan_id}:{edge_cls.shape}")
        for edge_offset, (source_subject, source_object) in enumerate(edge_index.T.tolist()):
            source_subject, source_object = int(source_subject), int(source_object)
            if source_subject not in pred_to_gt or source_object not in pred_to_gt:
                continue
            subject_id, object_id = pred_to_gt[source_subject], pred_to_gt[source_object]
            if subject_id == object_id:
                continue
            for source_predicate, (canonical, family) in PREDICATE_MAPPING.items():
                score = float(edge_cls[edge_offset, relation_indices[source_predicate]])
                if not np.isfinite(score):
                    raise ValueError(f"nonfinite_source_score:{scan_id}:{edge_offset}:{source_predicate}")
                prediction_id = f"replicassg:fross:{scan_id}:{subject_id}:{object_id}:{canonical}"
                if prediction_id in seen_ids:
                    raise ValueError(f"duplicate_prediction_id:{prediction_id}")
                seen_ids.add(prediction_id)
                rows.append({
                    "prediction_id": prediction_id,
                    "scan_id": scan_id,
                    "subgraph_id": scan_id,
                    "subset_split_id": 0,
                    "split": "official_test",
                    "source": "FROSS_RTD-ETR_EGTR_VisualGenome_zero_shot",
                    "source_run_id": "fross_replicassg_test_gtpose_frozen_v1",
                    "edge": {
                        "subject_id": subject_id,
                        "subject_label": gt_labels[subject_id],
                        "object_id": object_id,
                        "object_label": gt_labels[object_id],
                        "source_subject_node": source_subject,
                        "source_object_node": source_object,
                    },
                    "predicate": {
                        "predicate_label": canonical,
                        "predicate_family": family,
                        "source_predicate": source_predicate,
                        "source_predicate_id": relation_indices[source_predicate],
                    },
                    "semantic": {
                        "ranking_score": score,
                        "predicate_score": score,
                        "score_definition": "FROSS normalized edge_cls vote probability",
                    },
                })
                by_family[family] += 1
                by_predicate[canonical] += 1
                by_scan[scan_id] += 1

    rows.sort(key=lambda row: (row["scan_id"], row["edge"]["subject_id"], row["edge"]["object_id"], row["predicate"]["predicate_label"]))
    matches.sort(key=lambda row: (row["scan_id"], row["source_node_index"]))
    out.mkdir(parents=True, exist_ok=False)
    predictions_jsonl = out / "predictions.jsonl"
    matching_jsonl = out / "object_matching.jsonl"
    with predictions_jsonl.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    with matching_jsonl.open("w", encoding="utf-8") as handle:
        for row in matches:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": "adapter_ready",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "firewall": {
            "relationship_annotations_read_by_adapter": False,
            "candidate_inclusion_uses_relation_ground_truth": False,
            "object_matching": "official FROSS GT-object matching only",
        },
        "thresholds": {
            "match_distance_m": args.match_distance,
            "minimum_overlap": args.minimum_overlap,
            "maximum_ambiguity_ratio": args.maximum_ambiguity_ratio,
        },
        "counts": {
            "contexts": len(scans),
            "candidate_rows": len(rows),
            "matched_objects": len(matches),
            "by_family": dict(sorted(by_family.items())),
            "by_predicate": dict(sorted(by_predicate.items())),
            "by_scan": {scan: by_scan[scan] for scan in scans},
        },
        "inputs": {
            "prediction": {"path": relpath(root, prediction_path), "sha256": sha256(prediction_path)},
            "objects": {"path": relpath(root, objects_path), "sha256": sha256(objects_path)},
            "mapping": {"path": relpath(root, mapping_path), "sha256": sha256(mapping_path)},
            "protocol": {"path": relpath(root, protocol_path), "sha256": sha256(protocol_path)},
        },
        "outputs": {
            "predictions": {"path": relpath(root, predictions_jsonl), "sha256": sha256(predictions_jsonl)},
            "object_matching": {"path": relpath(root, matching_jsonl), "sha256": sha256(matching_jsonl)},
        },
        "docker_command": f"env UID=$(id -u) GID=$(id -g) docker compose -f configs/fross/compose.yaml run --rm {args.docker_service}",
    }
    dump_json(out / "manifest.json", manifest)
    print(json.dumps({"status": manifest["status"], "counts": manifest["counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
