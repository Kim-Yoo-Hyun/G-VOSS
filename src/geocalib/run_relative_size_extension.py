#!/usr/bin/env python3
"""Freeze, fit, lock, and evaluate the H001 relative-size extension."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

import fit_calibration as calibration_metrics
import run_train_only_evaluation as existing


SCHEMA = "h001_relative_size_extension_v1"
PREDICATES = ("bigger than", "smaller than")
OLD_FAMILIES = ("support_contact", "proximity", "relative_vertical")
ALL_FAMILIES = OLD_FAMILIES + ("relative_size",)
KS = (5, 10, 20, 50, 100)
METHODS = (
    "semantic_only",
    "family_product",
    "rank_average_family",
    "point_rule_product",
    "obb_rule_product",
    "shuffled_geometry_product",
    "wrong_pair_product",
)
NUMERIC_FEATURES = (
    "abs_log_volume_ratio",
    "abs_log_max_extent_ratio",
    "abs_log_middle_extent_ratio",
    "abs_log_min_extent_ratio",
    "abs_axis_dominance",
    "predicate_signed_log_volume_ratio",
    "predicate_signed_log_max_extent_ratio",
    "predicate_signed_log_middle_extent_ratio",
    "predicate_signed_log_min_extent_ratio",
    "predicate_signed_axis_dominance",
)
FEATURE_NAMES = ("bias",) + tuple(
    f"num:{name}" for name in NUMERIC_FEATURES
)
VERIFIER_TIE_LOG_RATIO = math.log(1.10)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("freeze", "fit", "lock", "evaluate"))
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260713)
    parser.add_argument("--docker-service", required=True)
    return parser.parse_args()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(payload: Any) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def read_scans(path: Path) -> set[str]:
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_empty(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f"nonempty_output:{path}")


def protocol_paths(root: Path, out: Path) -> dict[str, Path]:
    base = root / "experiments/H001_geom_reliability/train_only_reestablishment_v1"
    return {
        "train_scans": base / "splits/train_scans.txt",
        "internal_dev_scans": base / "splits/internal_dev_scans.txt",
        "final_validation_scans": base / "splits/final_validation_scans.txt",
        "train_relationships": root / "local_dataset/3DSSG_subset/relationships_train.json",
        "validation_relationships": root / "local_dataset/3DSSG_subset/relationships_validation.json",
        "ground_truth": root / "experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl",
        "existing_models": base / "calibration/fitted/models.json",
        "protocol": out / "protocol.json",
        "fit_model": out / "fit/model.json",
        "fit_diagnostics": out / "fit/internal_dev_diagnostics.json",
        "lock": out / "lock.json",
    }


def freeze(root: Path, out: Path, docker_service: str) -> int:
    ensure_empty(out)
    paths = protocol_paths(root, out)
    train, dev, final = (read_scans(paths[name]) for name in ("train_scans", "internal_dev_scans", "final_validation_scans"))
    validations = {
        "split_counts_1061_117_157": (len(train), len(dev), len(final)) == (1061, 117, 157),
        "split_overlap_zero": not (train & dev or train & final or dev & final),
        "all_required_inputs_exist": all(paths[name].exists() for name in (
            "train_relationships", "validation_relationships", "ground_truth", "existing_models"
        )),
    }
    protocol = {
        "schema_version": SCHEMA,
        "created_at_utc": now(),
        "status": "relative_size_protocol_frozen_pre_fit" if all(validations.values()) else "blocked_protocol",
        "family": {"name": "relative_size", "predicates": list(PREDICATES)},
        "factor_contract": {
            "T_e": "exact predicate sign: +1 for bigger-than and -1 for smaller-than",
            "raw_G_e": "same-pair absolute point-derived relative extents and volume ratios",
            "T_x_G": "predicate sign times signed point-derived ratios and axis dominance",
            "forbidden": ["source score", "source rank", "object class", "ground-truth flag"],
            "Z_e_usage": "final reranking only",
        },
        "point_evidence": {
            "model_view": "per-object alternating vertex subset A; p05-p95 xyz extents",
            "verifier_view": "disjoint per-object alternating vertex subset B; p02-p98 xyz extents",
            "minimum_points_per_view": 10,
            "verifier_tie_band": {"absolute_log_volume_ratio_le": VERIFIER_TIE_LOG_RATIO, "meaning": "uncertain"},
            "annotation_obb_usage": "deterministic baseline only; excluded from learned main C_e",
        },
        "model": {
            "architecture": "inverse-equivariant logistic compatibility model without a standalone predicate bias",
            "feature_names": list(FEATURE_NAMES),
            "optimizer": {"epochs": 800, "learning_rate": 0.2, "l2": 1e-4, "initial_weights": 0.0},
            "calibration_target": "GT-positive plus same-pair inverse-predicate counterfactual",
            "fit_split": "train_1061_only",
            "internal_dev_role": "diagnostic and lock decision; no final-validation access",
        },
        "controls": {
            "wrong_T": "same ordered pair with bigger/smaller inverted",
            "inverse_equivariance": "endpoint swap plus inverse predicate",
            "common_scale_invariance": "multiply both endpoint dimensions by 0.5, 2, and 10",
            "wrong_pair": "within-context cyclic pair-geometry shift",
            "shuffled_geometry": "within-context cyclic compatibility shift",
            "obb_only_baseline": "fixed sigmoid of predicate-signed annotation-OBB log-volume ratio",
            "point_only_baseline": "fixed sigmoid of predicate-signed model-view robust log-volume ratio",
        },
        "evaluation": {
            "sources": ["vlsat", "open3dsg", "sgfn"],
            "K": list(KS),
            "primary_K": 100,
            "bootstrap": {"unit": "548 shared subgraph contexts", "samples": 1000, "paired": True},
            "views": ["within-relative-size", "global-four-family", "global-top-K-family-composition"],
            "primary_gate": "per source, paired delta-R@100 CI lower > -0.01 and delta-V@100 CI upper < 0",
            "promotion_rule": "all sources pass both within-relative-size and global-four-family primary gates; controls remain valid",
        },
        "split_firewall": {"train": len(train), "internal_dev": len(dev), "final_validation": len(final)},
        "input_hashes": {name: sha256_file(paths[name]) for name in (
            "train_scans", "internal_dev_scans", "final_validation_scans", "train_relationships", "validation_relationships", "existing_models"
        )},
        "validations": validations,
        "pre_fit_erratum": "The first fit invocation completed before inspection but was rejected without reading metrics because a code-level audit found that standalone predicate biases did not guarantee endpoint-swap inverse equivariance. Its outputs were deleted and this architecture-level correction was frozen before the accepted fit.",
        "docker_service": docker_service,
    }
    write_json(out / "protocol.json", protocol)
    write_json(out / "manifest.json", {
        "schema_version": SCHEMA,
        "status": protocol["status"],
        "protocol_sha256": sha256_file(out / "protocol.json"),
        "docker_command": f"env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm {docker_service}",
    })
    print(json.dumps({"status": protocol["status"], "validations": validations}))
    return 0 if all(validations.values()) else 2


def scan_entries(path: Path, selected: set[str]) -> list[dict[str, Any]]:
    return [row for row in read_json(path)["scans"] if str(row["scan"]) in selected]


def needed_size_objects(entries: list[dict[str, Any]]) -> dict[str, set[int]]:
    result: dict[str, set[int]] = defaultdict(set)
    for entry in entries:
        scan = str(entry["scan"])
        for relation in entry.get("relationships", []):
            if str(relation[3]) in PREDICATES:
                result[scan].update((int(relation[0]), int(relation[1])))
    return result


def all_entry_objects(entries: list[dict[str, Any]]) -> dict[str, set[int]]:
    result: dict[str, set[int]] = defaultdict(set)
    for entry in entries:
        scan = str(entry["scan"])
        result[scan].update(int(object_id) for object_id in entry.get("objects", {}))
    return result


def parse_ply_points(path: Path, target_ids: set[int]) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    properties: list[str] = []
    vertex_count = None
    in_vertex = False
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped.startswith("format") and stripped != "format ascii 1.0":
                raise ValueError(f"unsupported_ply_format:{path}:{stripped}")
            if stripped.startswith("element vertex"):
                vertex_count = int(stripped.split()[-1]); in_vertex = True
            elif stripped.startswith("element face"):
                in_vertex = False
            elif stripped.startswith("property") and in_vertex:
                properties.append(stripped.split()[-1])
            elif stripped == "end_header":
                break
        if vertex_count is None:
            raise ValueError(f"missing_vertex_count:{path}")
        for required in ("x", "y", "z", "objectId"):
            if required not in properties:
                raise ValueError(f"missing_property:{path}:{required}")
        idx = {name: properties.index(name) for name in ("x", "y", "z", "objectId")}
        max_idx = max(idx.values())
        a: dict[int, list[tuple[float, float, float]]] = {value: [] for value in target_ids}
        b: dict[int, list[tuple[float, float, float]]] = {value: [] for value in target_ids}
        seen: Counter[int] = Counter()
        for _ in range(vertex_count):
            line = handle.readline()
            if not line:
                break
            parts = line.split()
            if len(parts) <= max_idx:
                continue
            object_id = int(parts[idx["objectId"]])
            if object_id not in target_ids:
                continue
            point = (float(parts[idx["x"]]), float(parts[idx["y"]]), float(parts[idx["z"]]))
            (a if seen[object_id] % 2 == 0 else b)[object_id].append(point)
            seen[object_id] += 1
    return {
        object_id: (
            np.asarray(a[object_id], dtype=np.float64).reshape((-1, 3)),
            np.asarray(b[object_id], dtype=np.float64).reshape((-1, 3)),
        )
        for object_id in target_ids
    }


def robust_dims(points: np.ndarray, low: float, high: float) -> list[float] | None:
    if len(points) < 10:
        return None
    values = np.percentile(points, (low, high), axis=0)
    dims = np.maximum(values[1] - values[0], 1e-6)
    return [float(value) for value in dims]


def obb_dims(semseg: dict[str, Any], target_ids: set[int]) -> dict[int, list[float]]:
    result: dict[int, list[float]] = {}
    for group in semseg.get("segGroups", []):
        object_id = int(group.get("objectId", group.get("id", -1)))
        lengths = (group.get("obb") or {}).get("axesLengths")
        if object_id in target_ids and isinstance(lengths, list) and len(lengths) == 3:
            values = [max(float(value), 1e-6) for value in lengths]
            result[object_id] = values
    return result


def extract_object_stats(root: Path, needed: dict[str, set[int]]) -> tuple[dict[tuple[str, int], dict[str, Any]], dict[str, Any]]:
    output: dict[tuple[str, int], dict[str, Any]] = {}
    errors: list[str] = []
    for offset, scan in enumerate(sorted(needed), 1):
        scan_dir = root / "local_dataset/3RScan/scans" / scan
        try:
            points = parse_ply_points(scan_dir / "labels.instances.annotated.v2.ply", needed[scan])
            obb = obb_dims(read_json(scan_dir / "semseg.v2.json"), needed[scan])
            for object_id in sorted(needed[scan]):
                model_points, verifier_points = points[object_id]
                output[(scan, object_id)] = {
                    "scan_id": scan,
                    "object_id": object_id,
                    "model_dims_p05_p95": robust_dims(model_points, 5, 95),
                    "verifier_dims_p02_p98": robust_dims(verifier_points, 2, 98),
                    "obb_axes_lengths": obb.get(object_id),
                    "model_point_count": len(model_points),
                    "verifier_point_count": len(verifier_points),
                }
        except Exception as exc:  # preserve complete scan-level diagnostics
            errors.append(f"{scan}:{type(exc).__name__}:{exc}")
        if offset % 100 == 0:
            print(json.dumps({"progress_scans": offset, "total_scans": len(needed)}), flush=True)
    summary = {
        "scans_requested": len(needed),
        "objects_requested": sum(len(values) for values in needed.values()),
        "objects_emitted": len(output),
        "objects_model_ready": sum(row["model_dims_p05_p95"] is not None for row in output.values()),
        "objects_verifier_ready": sum(row["verifier_dims_p02_p98"] is not None for row in output.values()),
        "objects_obb_ready": sum(row["obb_axes_lengths"] is not None for row in output.values()),
        "scan_errors": errors,
    }
    return output, summary


def ratio_features(subject_dims: list[float], object_dims: list[float], predicate: str) -> dict[str, float]:
    s = np.sort(np.maximum(np.asarray(subject_dims, dtype=np.float64), 1e-6))[::-1]
    o = np.sort(np.maximum(np.asarray(object_dims, dtype=np.float64), 1e-6))[::-1]
    ratios = np.log(s / o)
    log_volume = float(np.sum(ratios))
    sign = 1.0 if predicate == "bigger than" else -1.0
    signed_raw = {
        "log_volume_ratio": log_volume,
        "log_max_extent_ratio": float(ratios[0]),
        "log_middle_extent_ratio": float(ratios[1]),
        "log_min_extent_ratio": float(ratios[2]),
        "axis_dominance": float(np.mean(np.sign(ratios))),
    }
    symmetric = {f"abs_{name}": abs(value) for name, value in signed_raw.items()}
    interactions = {f"predicate_signed_{name}": sign * value for name, value in signed_raw.items()}
    hidden = {f"_signed_{name}": value for name, value in signed_raw.items()}
    return symmetric | interactions | hidden


def make_training_rows(entries: list[dict[str, Any]], stats: dict[tuple[str, int], dict[str, Any]], train: set[str], dev: set[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    missing = 0
    for entry in entries:
        scan = str(entry["scan"])
        role = "train" if scan in train else "internal_dev" if scan in dev else None
        if role is None:
            continue
        split = int(entry.get("split", 0))
        for index, relation in enumerate(entry.get("relationships", [])):
            predicate = str(relation[3])
            if predicate not in PREDICATES:
                continue
            subject, obj = int(relation[0]), int(relation[1])
            left, right = stats.get((scan, subject)), stats.get((scan, obj))
            if not left or not right or left["model_dims_p05_p95"] is None or right["model_dims_p05_p95"] is None:
                missing += 1
                continue
            for label, used_predicate, kind in ((1, predicate, "gt_positive"), (0, PREDICATES[1 - PREDICATES.index(predicate)], "wrong_T")):
                rows.append({
                    "scan_id": scan, "subset_split_id": split, "subgraph_id": f"{scan}_{split}",
                    "subject_id": subject, "object_id": obj, "predicate": used_predicate,
                    "source_predicate": predicate, "label": label, "role": role, "row_type": kind,
                    "features": ratio_features(left["model_dims_p05_p95"], right["model_dims_p05_p95"], used_predicate),
                    "source_relation_index": index,
                })
    return rows, {"missing_gt_positive_geometry": missing}


def numeric_stats(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    result = {}
    for name in NUMERIC_FEATURES:
        values = np.asarray([row["features"][name] for row in rows], dtype=np.float64)
        result[name] = {"mean": float(values.mean()), "std": float(values.std()) or 1.0}
    return result


def vectorize(predicate: str, features: dict[str, float], stats: dict[str, dict[str, float]]) -> list[float]:
    vector = [1.0]
    vector.extend((features[name] - stats[name]["mean"]) / stats[name]["std"] for name in NUMERIC_FEATURES)
    return vector


def sigmoid(values: np.ndarray | float) -> np.ndarray | float:
    array = np.asarray(values, dtype=np.float64)
    result = np.empty_like(array)
    positive = array >= 0
    result[positive] = 1.0 / (1.0 + np.exp(-array[positive]))
    exp_values = np.exp(array[~positive])
    result[~positive] = exp_values / (1.0 + exp_values)
    return float(result) if result.ndim == 0 else result


def fit_logistic(x: np.ndarray, y: np.ndarray) -> tuple[list[float], list[dict[str, float]]]:
    weights = np.zeros(x.shape[1], dtype=np.float64)
    trace = []
    for epoch in range(1, 801):
        probs = sigmoid(x @ weights)
        gradient = (x.T @ (probs - y)) / len(y)
        gradient[1:] += 1e-4 * weights[1:]
        weights -= 0.2 * gradient
        if epoch == 1 or epoch % 50 == 0 or epoch == 800:
            clipped = np.clip(probs, 1e-12, 1 - 1e-12)
            nll = float(np.mean(-(y * np.log(clipped) + (1 - y) * np.log(1 - clipped))))
            trace.append({"epoch": epoch, "train_nll": nll})
    return weights.tolist(), trace


def model_probability(model: dict[str, Any], predicate: str, features: dict[str, float]) -> float:
    vector = vectorize(predicate, features, model["numeric_stats"])
    return float(sigmoid(np.dot(np.asarray(vector), np.asarray(model["weights"]))))


def binary_metrics(probabilities: list[float], labels: list[int]) -> dict[str, Any]:
    return {
        "rows": len(labels), "positive": sum(labels), "negative": len(labels) - sum(labels),
        "auroc": calibration_metrics.auroc(probabilities, labels),
        "auprc": calibration_metrics.average_precision(probabilities, labels),
        "brier": calibration_metrics.brier_score(probabilities, labels),
        "nll": calibration_metrics.log_loss(probabilities, labels),
    }


def verifier_status(subject: dict[str, Any], obj: dict[str, Any], predicate: str) -> str:
    left, right = subject.get("verifier_dims_p02_p98"), obj.get("verifier_dims_p02_p98")
    if left is None or right is None:
        return "unsupported"
    ratio = math.log(max(np.prod(left), 1e-12) / max(np.prod(right), 1e-12))
    if abs(ratio) <= VERIFIER_TIE_LOG_RATIO:
        return "uncertain"
    valid = ratio > 0 if predicate == "bigger than" else ratio < 0
    return "satisfied" if valid else "violated"


def fit(root: Path, out: Path, docker_service: str) -> int:
    fit_out = out / "fit"
    ensure_empty(fit_out)
    paths = protocol_paths(root, out)
    protocol = read_json(paths["protocol"])
    if protocol.get("status") != "relative_size_protocol_frozen_pre_fit":
        raise ValueError("protocol_not_frozen")
    train, dev, final = (read_scans(paths[name]) for name in ("train_scans", "internal_dev_scans", "final_validation_scans"))
    entries = scan_entries(paths["train_relationships"], train | dev)
    needed = needed_size_objects(entries)
    object_stats, extraction = extract_object_stats(root, needed)
    rows, row_warnings = make_training_rows(entries, object_stats, train, dev)
    if any(row["scan_id"] in final for row in rows):
        raise ValueError("final_validation_leakage")
    train_rows = [row for row in rows if row["role"] == "train"]
    dev_rows = [row for row in rows if row["role"] == "internal_dev"]
    stats = numeric_stats(train_rows)
    train_x = np.asarray([vectorize(row["predicate"], row["features"], stats) for row in train_rows])
    train_y = np.asarray([row["label"] for row in train_rows], dtype=np.float64)
    weights, trace = fit_logistic(train_x, train_y)
    model = {
        "schema_version": SCHEMA, "family": "relative_size", "architecture": "single_logistic_TxG",
        "feature_names": list(FEATURE_NAMES), "numeric_features": list(NUMERIC_FEATURES),
        "numeric_stats": stats, "weights": weights, "fit_split": "train_1061_only", "trace": trace,
    }
    diagnostics = {}
    for role, role_rows in (("train", train_rows), ("internal_dev", dev_rows)):
        probabilities = [model_probability(model, row["predicate"], row["features"]) for row in role_rows]
        diagnostics[role] = binary_metrics(probabilities, [row["label"] for row in role_rows])
    gt_dev = [row for row in dev_rows if row["row_type"] == "gt_positive"]
    gt_status = Counter()
    wrong_t_diffs, inverse_diffs, scale_diffs = [], [], []
    for row in gt_dev:
        subject, obj = object_stats[(row["scan_id"], row["subject_id"])], object_stats[(row["scan_id"], row["object_id"])]
        gt_status[verifier_status(subject, obj, row["predicate"])] += 1
        correct = model_probability(model, row["predicate"], row["features"])
        inverse_predicate = PREDICATES[1 - PREDICATES.index(row["predicate"])]
        wrong_features = ratio_features(subject["model_dims_p05_p95"], obj["model_dims_p05_p95"], inverse_predicate)
        wrong_t_diffs.append(correct - model_probability(model, inverse_predicate, wrong_features))
        swapped_features = ratio_features(obj["model_dims_p05_p95"], subject["model_dims_p05_p95"], inverse_predicate)
        inverse_diffs.append(abs(correct - model_probability(model, inverse_predicate, swapped_features)))
        for scale in (0.5, 2.0, 10.0):
            scaled = ratio_features(
                [scale * value for value in subject["model_dims_p05_p95"]],
                [scale * value for value in obj["model_dims_p05_p95"]], row["predicate"]
            )
            scale_diffs.append(abs(correct - model_probability(model, row["predicate"], scaled)))
    diagnostics["controls"] = {
        "wrong_T": {"rows": len(wrong_t_diffs), "correct_minus_wrong_mean": float(np.mean(wrong_t_diffs)), "correct_win_rate": float(np.mean(np.asarray(wrong_t_diffs) > 0))},
        "inverse_equivariance": {"rows": len(inverse_diffs), "mean_absolute_error": float(np.mean(inverse_diffs)), "max_absolute_error": float(np.max(inverse_diffs))},
        "common_scale_invariance": {"rows": len(scale_diffs), "mean_absolute_error": float(np.mean(scale_diffs)), "max_absolute_error": float(np.max(scale_diffs))},
        "independent_verifier_on_dev_GT": dict(sorted(gt_status.items())),
    }
    validations = {
        "zero_final_rows": not any(row["scan_id"] in final for row in rows),
        "train_and_dev_binary": {row["label"] for row in train_rows} == {0, 1} and {row["label"] for row in dev_rows} == {0, 1},
        "no_forbidden_features": not any(any(token in feature.lower() for token in ("source", "score", "rank", "class", "semantic")) for feature in FEATURE_NAMES),
        "all_weights_finite": all(math.isfinite(value) for value in weights),
        "point_views_disjoint_by_construction": True,
        "dev_wrong_T_win_rate_ge_0_95": diagnostics["controls"]["wrong_T"]["correct_win_rate"] >= 0.95,
        "inverse_max_error_le_1e_10": diagnostics["controls"]["inverse_equivariance"]["max_absolute_error"] <= 1e-10,
        "scale_max_error_le_1e_10": diagnostics["controls"]["common_scale_invariance"]["max_absolute_error"] <= 1e-10,
    }
    fit_out.mkdir(parents=True, exist_ok=True)
    write_json(fit_out / "model.json", model)
    write_json(fit_out / "internal_dev_diagnostics.json", diagnostics | {"extraction": extraction, "row_warnings": row_warnings})
    write_jsonl(fit_out / "calibration_rows.jsonl", rows)
    write_jsonl(fit_out / "object_stats.jsonl", list(object_stats.values()))
    manifest = {
        "schema_version": SCHEMA, "created_at_utc": now(),
        "status": "relative_size_train_only_fit_ready_for_lock" if all(validations.values()) else "relative_size_fit_ready_with_failed_control_gate",
        "counts": {"rows": len(rows), "train_rows": len(train_rows), "internal_dev_rows": len(dev_rows), "train_scans_with_rows": len({row['scan_id'] for row in train_rows}), "dev_scans_with_rows": len({row['scan_id'] for row in dev_rows})},
        "validations": validations, "extraction": extraction,
        "outputs": {name: {"path": relpath(root, fit_out / name), "sha256": sha256_file(fit_out / name)} for name in ("model.json", "internal_dev_diagnostics.json", "calibration_rows.jsonl", "object_stats.jsonl")},
        "docker_service": docker_service,
    }
    write_json(fit_out / "manifest.json", manifest)
    print(json.dumps({"status": manifest["status"], "counts": manifest["counts"], "diagnostics": diagnostics, "validations": validations}))
    return 0


def lock(root: Path, out: Path, docker_service: str) -> int:
    paths = protocol_paths(root, out)
    if paths["lock"].exists():
        raise FileExistsError(f"existing_lock:{paths['lock']}")
    model, diagnostics = read_json(paths["fit_model"]), read_json(paths["fit_diagnostics"])
    score_definition = {
        "relative_size_compatibility": "sigmoid(train-only logistic(T, point-view-A G, T-by-G))",
        "family_product": "source semantic score times family compatibility",
        "rank_average": "equal mean of within-context semantic and family-compatibility percentile ranks",
        "K": list(KS), "primary_K": 100,
    }
    payload = {
        "schema_version": SCHEMA, "created_at_utc": now(), "status": "relative_size_model_and_score_locked_pre_final_evaluation",
        "model_sha256": sha256_file(paths["fit_model"]), "protocol_sha256": sha256_file(paths["protocol"]),
        "diagnostics_sha256": sha256_file(paths["fit_diagnostics"]), "score_definition": score_definition,
        "score_definition_sha256": sha256_json(score_definition), "internal_dev_diagnostics": diagnostics,
        "docker_service": docker_service,
    }
    write_json(paths["lock"], payload)
    print(json.dumps({"status": payload["status"], "model_sha256": payload["model_sha256"], "score_definition_sha256": payload["score_definition_sha256"]}))
    return 0


def family_for_predicate(predicate: str, recorded: str | None = None) -> str | None:
    if predicate in PREDICATES:
        return "relative_size"
    return recorded if recorded in OLD_FAMILIES else None


def key_from_candidate(row: dict[str, Any]) -> tuple[str, int, int, int, str]:
    return (str(row["scan_id"]), int(row["subset_split_id"]), int(row["edge"]["subject_id"]), int(row["edge"]["object_id"]), str(row["predicate"]["predicate_label"]))


def key_from_gt(row: dict[str, Any]) -> tuple[str, int, int, int, str]:
    return (str(row["scan_id"]), int(row["subset_split_id"]), int(row["subject_id"]), int(row["object_id"]), str(row["predicate_label"]))


def load_gt(path: Path) -> tuple[dict[str, set[tuple[Any, ...]]], dict[str, dict[str, set[tuple[Any, ...]]]]]:
    overall: dict[str, set[tuple[Any, ...]]] = defaultdict(set)
    by_family: dict[str, dict[str, set[tuple[Any, ...]]]] = defaultdict(lambda: defaultdict(set))
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            family = family_for_predicate(str(row["predicate_label"]), row.get("predicate_family"))
            if family is None:
                continue
            key = key_from_gt(row)
            overall[row["subgraph_id"]].add(key)
            by_family[row["subgraph_id"]][family].add(key)
    return overall, by_family


def fixed_rule_probability(predicate: str, subject_dims: list[float] | None, object_dims: list[float] | None) -> float:
    if subject_dims is None or object_dims is None:
        return 0.5
    ratio = math.log(max(float(np.prod(subject_dims)), 1e-12) / max(float(np.prod(object_dims)), 1e-12))
    sign = 1.0 if predicate == "bigger than" else -1.0
    return float(sigmoid(4.0 * sign * ratio))


def load_source_candidates(path: Path, object_stats: dict[tuple[str, int], dict[str, Any]], size_model: dict[str, Any], old_models: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    counts = Counter()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            predicate = str(row["predicate"]["predicate_label"])
            family = family_for_predicate(predicate, row["predicate"].get("predicate_family"))
            if family is None:
                continue
            semantic = existing.finite((row.get("semantic") or {}).get("ranking_score"))
            if semantic is None:
                counts["missing_semantic"] += 1; continue
            subject_id, object_id = int(row["edge"]["subject_id"]), int(row["edge"]["object_id"])
            if family == "relative_size":
                subject, obj = object_stats.get((row["scan_id"], subject_id)), object_stats.get((row["scan_id"], object_id))
                if not subject or not obj or subject["model_dims_p05_p95"] is None or obj["model_dims_p05_p95"] is None:
                    counts["size_missing_geometry"] += 1; continue
                features = ratio_features(subject["model_dims_p05_p95"], obj["model_dims_p05_p95"], predicate)
                compatibility = model_probability(size_model, predicate, features)
                point_rule = fixed_rule_probability(predicate, subject["model_dims_p05_p95"], obj["model_dims_p05_p95"])
                obb_rule = fixed_rule_probability(predicate, subject.get("obb_axes_lengths"), obj.get("obb_axes_lengths"))
                status = verifier_status(subject, obj, predicate)
                raw_for_wrong = features
            else:
                raw = existing.raw_numeric(row)
                compatibility = existing.probability(old_models["family_models"][family], family, predicate, raw)
                point_rule = obb_rule = compatibility
                status = row.get("verification_status") or (row.get("verification") or {}).get("verification_status")
                raw_for_wrong = raw
            item = {
                "id": row["prediction_id"], "key": key_from_candidate(row), "subgraph": row["subgraph_id"],
                "scan": row["scan_id"], "family": family, "predicate": predicate, "subject": subject_id, "object": object_id,
                "semantic": semantic, "compatibility": compatibility, "point_rule": point_rule, "obb_rule": obb_rule,
                "status": status, "raw": raw_for_wrong, "scores": {},
            }
            grouped[row["subgraph_id"]].append(item)
            counts[f"family:{family}"] += 1
    for subgraph, candidates in grouped.items():
        size_items = sorted([item for item in candidates if item["family"] == "relative_size"], key=lambda item: item["key"])
        shuffled = {item["id"]: size_items[(index + 1) % len(size_items)]["compatibility"] for index, item in enumerate(size_items)} if size_items else {}
        pair_features: dict[tuple[int, int], dict[str, float]] = {}
        for item in size_items:
            pair_features.setdefault((item["subject"], item["object"]), item["raw"])
        pairs = sorted(pair_features)
        shifted = {pair: pairs[(index + 1) % len(pairs)] for index, pair in enumerate(pairs)} if pairs else {}
        for item in candidates:
            if item["family"] == "relative_size" and pairs:
                wrong_raw = pair_features[shifted[(item["subject"], item["object"])]]
                wrong_pair = model_probability(size_model, item["predicate"], {
                    name: (
                        wrong_raw[name]
                        if not name.startswith("predicate_signed_")
                        else (1.0 if item["predicate"] == "bigger than" else -1.0)
                        * wrong_raw[f"_signed_{name.removeprefix('predicate_signed_')}"]
                    )
                    for name in NUMERIC_FEATURES
                })
            else:
                wrong_pair = item["compatibility"]
            item["wrong_pair"] = wrong_pair
            item["shuffled"] = shuffled.get(item["id"], item["compatibility"])
        count = len(candidates); denominator = max(count - 1, 1)
        semantic_order = sorted(candidates, key=lambda item: (-item["semantic"], item["key"]))
        compatibility_order = sorted(candidates, key=lambda item: (-item["compatibility"], item["key"]))
        semantic_rank = {item["id"]: index for index, item in enumerate(semantic_order, 1)}
        compatibility_rank = {item["id"]: index for index, item in enumerate(compatibility_order, 1)}
        for item in candidates:
            sem_pct = 1.0 - (semantic_rank[item["id"]] - 1) / denominator
            comp_pct = 1.0 - (compatibility_rank[item["id"]] - 1) / denominator
            item["scores"] = {
                "semantic_only": item["semantic"],
                "family_product": item["semantic"] * item["compatibility"],
                "rank_average_family": 0.5 * (sem_pct + comp_pct),
                "point_rule_product": item["semantic"] * item["point_rule"],
                "obb_rule_product": item["semantic"] * item["obb_rule"],
                "shuffled_geometry_product": item["semantic"] * item["shuffled"],
                "wrong_pair_product": item["semantic"] * item["wrong_pair"],
            }
    return grouped, dict(sorted(counts.items()))


def empty_arrays(subgraphs: list[str]) -> dict[str, dict[str, np.ndarray]]:
    return {method: {name: np.zeros((len(KS), len(subgraphs)), dtype=np.float64) for name in ("recall_num", "recall_den", "violation_num", "violation_den")} for method in METHODS}


def add_cell(target: dict[str, np.ndarray], ki: int, si: int, selected: list[dict[str, Any]], gt: set[tuple[Any, ...]]) -> None:
    target["recall_num"][ki, si] = len({row["key"] for row in selected} & gt)
    target["recall_den"][ki, si] = len(gt)
    statuses = [row["status"] for row in selected if row["status"] in {"satisfied", "uncertain", "violated"}]
    target["violation_num"][ki, si] = sum(value == "violated" for value in statuses)
    target["violation_den"][ki, si] = len(statuses)


def contributions(grouped: dict[str, list[dict[str, Any]]], gt: dict[str, set[tuple[Any, ...]]], gt_family: dict[str, dict[str, set[tuple[Any, ...]]]], subgraphs: list[str]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    overall = empty_arrays(subgraphs)
    within = {family: empty_arrays(subgraphs) for family in ALL_FAMILIES}
    slices = {family: empty_arrays(subgraphs) for family in ALL_FAMILIES}
    composition: dict[str, dict[str, Counter[str]]] = {method: {str(k): Counter() for k in KS} for method in METHODS}
    for si, subgraph in enumerate(subgraphs):
        candidates = grouped.get(subgraph, [])
        for method in METHODS:
            ranked = sorted(candidates, key=lambda item: (-item["scores"][method], item["key"]))
            for ki, k in enumerate(KS):
                selected = ranked[:k]
                add_cell(overall[method], ki, si, selected, gt.get(subgraph, set()))
                composition[method][str(k)].update(item["family"] for item in selected)
                for family in ALL_FAMILIES:
                    family_ranked = [item for item in ranked if item["family"] == family]
                    add_cell(within[family][method], ki, si, family_ranked[:k], gt_family.get(subgraph, {}).get(family, set()))
                    add_cell(slices[family][method], ki, si, [item for item in selected if item["family"] == family], gt_family.get(subgraph, {}).get(family, set()))
    return overall, within, slices, composition


def ci(values: np.ndarray) -> list[float | None]:
    finite = values[np.isfinite(values)]
    return [float(value) for value in np.percentile(finite, (2.5, 97.5))] if len(finite) else [None, None]


def summarize_arrays(values: dict[str, Any], samples: np.ndarray) -> tuple[dict[str, Any], dict[str, Any]]:
    report, cache = {}, {}
    for method in METHODS:
        report[method], cache[method] = {}, {}
        for ki, k in enumerate(KS):
            report[method][str(k)], cache[method][str(k)] = {}, {}
            for metric in ("recall", "violation"):
                numerator = values[method][f"{metric}_num"][ki]
                denominator = values[method][f"{metric}_den"][ki]
                point = float(numerator.sum() / denominator.sum()) if denominator.sum() else None
                boot_num, boot_den = numerator[samples].sum(axis=1), denominator[samples].sum(axis=1)
                boot = np.divide(boot_num, boot_den, out=np.full_like(boot_num, np.nan), where=boot_den > 0)
                report[method][str(k)][metric] = {"point": point, "ci95": ci(boot), "numerator": int(numerator.sum()), "denominator": int(denominator.sum())}
                cache[method][str(k)][metric] = boot
    report["deltas_vs_semantic_only"] = {}
    for method in METHODS[1:]:
        report["deltas_vs_semantic_only"][method] = {}
        for k in KS:
            report["deltas_vs_semantic_only"][method][str(k)] = {}
            for metric in ("recall", "violation"):
                left, right = report[method][str(k)][metric]["point"], report["semantic_only"][str(k)][metric]["point"]
                boot = cache[method][str(k)][metric] - cache["semantic_only"][str(k)][metric]
                report["deltas_vs_semantic_only"][method][str(k)][metric] = {"point": left - right if left is not None and right is not None else None, "paired_ci95": ci(boot)}
    report["family_product_minus_baseline"] = {}
    for baseline in ("rank_average_family", "point_rule_product", "obb_rule_product", "shuffled_geometry_product", "wrong_pair_product"):
        report["family_product_minus_baseline"][baseline] = {}
        for k in KS:
            report["family_product_minus_baseline"][baseline][str(k)] = {}
            for metric in ("recall", "violation"):
                left = report["family_product"][str(k)][metric]["point"]
                right = report[baseline][str(k)][metric]["point"]
                boot = cache["family_product"][str(k)][metric] - cache[baseline][str(k)][metric]
                report["family_product_minus_baseline"][baseline][str(k)][metric] = {
                    "point": left - right if left is not None and right is not None else None,
                    "paired_ci95": ci(boot),
                }
    return report, cache


def gate(view: dict[str, Any], method: str = "family_product") -> dict[str, Any]:
    delta = view["deltas_vs_semantic_only"][method]["100"]
    recall, violation = delta["recall"], delta["violation"]
    recall_pass = recall["paired_ci95"][0] is not None and recall["paired_ci95"][0] > -0.01
    violation_pass = violation["paired_ci95"][1] is not None and violation["paired_ci95"][1] < 0
    return {"pass": recall_pass and violation_pass, "recall_guardrail_pass": recall_pass, "violation_gate_pass": violation_pass, "delta_recall": recall, "delta_violation": violation}


def markdown(summary: dict[str, Any]) -> str:
    lines = ["# Relative-size H001 extension", "", f"Status: `{summary['status']}`", "", "| source | view | method | R@100 | dR | V@100 | dV | gate |", "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |"]
    for source, payload in summary["sources"].items():
        for view_name in ("relative_size", "global_four_family"):
            view = payload[view_name]
            for method in ("semantic_only", "family_product", "rank_average_family", "point_rule_product", "obb_rule_product"):
                cell = view[method]["100"]
                delta = view["deltas_vs_semantic_only"].get(method, {}).get("100", {})
                d_r = delta.get("recall", {}).get("point", 0.0)
                d_v = delta.get("violation", {}).get("point", 0.0)
                gate_text = "baseline" if method == "semantic_only" else ("pass" if gate(view, method)["pass"] else "fail")
                lines.append(f"| {source} | {view_name} | {method} | {cell['recall']['point']:.6f} | {d_r:.6f} | {cell['violation']['point']:.6f} | {d_v:.6f} | {gate_text} |")
    lines.extend(["", f"Promotion decision: `{summary['promotion_decision']['decision']}`", ""])
    return "\n".join(lines)


def evaluate(root: Path, out: Path, docker_service: str, n_bootstrap: int, seed: int) -> int:
    evaluation_out = out / "evaluation"
    ensure_empty(evaluation_out)
    paths = protocol_paths(root, out)
    lock_payload = read_json(paths["lock"])
    if lock_payload.get("status") != "relative_size_model_and_score_locked_pre_final_evaluation":
        raise ValueError("model_not_locked")
    if lock_payload["model_sha256"] != sha256_file(paths["fit_model"]):
        raise ValueError("model_hash_changed_after_lock")
    final_scans = read_scans(paths["final_validation_scans"])
    entries = scan_entries(paths["validation_relationships"], final_scans)
    needed = all_entry_objects(entries)
    object_stats, extraction = extract_object_stats(root, needed)
    write_jsonl(evaluation_out / "final_object_stats.jsonl", list(object_stats.values()))
    size_model, old_models = read_json(paths["fit_model"]), read_json(paths["existing_models"])
    gt, gt_family = load_gt(paths["ground_truth"])
    subgraphs = sorted({f"{entry['scan']}_{int(entry.get('split', 0))}" for entry in entries})
    if len(subgraphs) != 548:
        raise ValueError(f"expected_548_contexts:{len(subgraphs)}")
    final_gt_audit = Counter()
    model_view_rule_agreement = []
    obb_rule_agreement = []
    with paths["ground_truth"].open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("predicate_label") not in PREDICATES:
                continue
            subject = object_stats.get((row["scan_id"], int(row["subject_id"])))
            obj = object_stats.get((row["scan_id"], int(row["object_id"])))
            if not subject or not obj:
                final_gt_audit["unsupported"] += 1
                continue
            status = verifier_status(subject, obj, row["predicate_label"])
            final_gt_audit[status] += 1
            if status in {"satisfied", "violated"}:
                target = status == "satisfied"
                model_prob = fixed_rule_probability(row["predicate_label"], subject.get("model_dims_p05_p95"), obj.get("model_dims_p05_p95"))
                obb_prob = fixed_rule_probability(row["predicate_label"], subject.get("obb_axes_lengths"), obj.get("obb_axes_lengths"))
                model_view_rule_agreement.append((model_prob >= 0.5) == target)
                obb_rule_agreement.append((obb_prob >= 0.5) == target)
    construct_audit = {
        "final_GT_rows": sum(final_gt_audit.values()),
        "disjoint_verifier_status": dict(sorted(final_gt_audit.items())),
        "model_view_rule_vs_disjoint_verifier_binary_agreement": float(np.mean(model_view_rule_agreement)) if model_view_rule_agreement else None,
        "annotation_OBB_rule_vs_disjoint_verifier_binary_agreement": float(np.mean(obb_rule_agreement)) if obb_rule_agreement else None,
        "boundary": "Disjoint vertex views and different percentile estimators remove exact rule reuse, but both remain measurements of the same segmented point cloud.",
    }
    rng = np.random.default_rng(seed)
    samples = rng.integers(0, len(subgraphs), size=(n_bootstrap, len(subgraphs)))
    source_paths = {
        "vlsat": root / "experiments/H001_geom_reliability/sources/vlsat/full_validation/geometry/verification.jsonl",
        "open3dsg": root / "experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/geometry/verification.jsonl",
        "sgfn": root / "experiments/H001_geom_reliability/sources/sgfn/geometry/verification.jsonl",
    }
    source_results = {}
    point_rows = []
    composition_rows = []
    for source, source_path in source_paths.items():
        print(json.dumps({"source_start": source}), flush=True)
        grouped, counts = load_source_candidates(source_path, object_stats, size_model, old_models)
        overall_arrays, within_arrays, slice_arrays, composition = contributions(grouped, gt, gt_family, subgraphs)
        overall, overall_cache = summarize_arrays(overall_arrays, samples)
        within, within_cache, slices = {}, {}, {}
        for family in ALL_FAMILIES:
            within[family], within_cache[family] = summarize_arrays(within_arrays[family], samples)
            slices[family], _ = summarize_arrays(slice_arrays[family], samples)
        # Simultaneous family-wise intervals for the main family product.
        for k in KS:
            for metric in ("recall", "violation"):
                point_values, boot_values, active = [], [], []
                for family in ALL_FAMILIES:
                    delta = within[family]["deltas_vs_semantic_only"]["family_product"][str(k)][metric]
                    boot = within_cache[family]["family_product"][str(k)][metric] - within_cache[family]["semantic_only"][str(k)][metric]
                    if delta["point"] is not None and np.any(np.isfinite(boot)):
                        point_values.append(delta["point"]); boot_values.append(boot); active.append(family)
                if boot_values:
                    matrix = np.column_stack(boot_values)
                    radius = float(np.nanpercentile(np.nanmax(np.abs(matrix - np.asarray(point_values)[None, :]), axis=1), 95.0))
                    for family, point in zip(active, point_values):
                        within[family]["deltas_vs_semantic_only"]["family_product"][str(k)][metric]["simultaneous_familywise_ci95"] = [point - radius, point + radius]
        source_results[source] = {
            "candidate_counts": counts,
            "global_four_family": overall,
            "relative_size": within["relative_size"],
            "within_family": within,
            "global_top_K_family_slices": slices,
            "composition": {method: {k: dict(sorted(values.items())) for k, values in by_k.items()} for method, by_k in composition.items()},
            "gates": {"relative_size_family_product": gate(within["relative_size"]), "global_four_family_product": gate(overall), "relative_size_rank_average": gate(within["relative_size"], "rank_average_family"), "global_rank_average": gate(overall, "rank_average_family")},
        }
        for view_name, view in (("relative_size", within["relative_size"]), ("global_four_family", overall)):
            for method in METHODS:
                for k in KS:
                    for metric in ("recall", "violation"):
                        cell = view[method][str(k)][metric]
                        delta = view["deltas_vs_semantic_only"].get(method, {}).get(str(k), {}).get(metric, {})
                        point_rows.append({"source": source, "view": view_name, "method": method, "K": k, "metric": metric, "point": cell["point"], "ci_low": cell["ci95"][0], "ci_high": cell["ci95"][1], "delta": delta.get("point"), "delta_ci_low": (delta.get("paired_ci95") or [None, None])[0], "delta_ci_high": (delta.get("paired_ci95") or [None, None])[1]})
        for method, by_k in composition.items():
            for k, values in by_k.items():
                for family, count in values.items():
                    composition_rows.append({"source": source, "method": method, "K": k, "family": family, "selected_count": count})
        print(json.dumps({"source_complete": source, "gates": source_results[source]["gates"]}), flush=True)
    control_valid = read_json(paths["fit_diagnostics"])["controls"]
    product_all_pass = all(payload["gates"][key]["pass"] for payload in source_results.values() for key in ("relative_size_family_product", "global_four_family_product"))
    controls_pass = control_valid["wrong_T"]["correct_win_rate"] >= 0.95 and control_valid["inverse_equivariance"]["max_absolute_error"] <= 1e-10 and control_valid["common_scale_invariance"]["max_absolute_error"] <= 1e-10
    learned_beats_point_rule = all(
        payload["relative_size"]["family_product_minus_baseline"]["point_rule_product"]["100"]["violation"]["paired_ci95"][1] < 0
        for payload in source_results.values()
    )
    promotion = {
        "decision": "promote_relative_size_to_framework_scope" if product_all_pass and controls_pass else "keep_relative_size_as_extension_evidence",
        "all_three_sources_product_gates_pass": product_all_pass,
        "controls_pass": controls_pass,
        "learned_product_strictly_beats_point_rule_on_V_all_sources": learned_beats_point_rule,
        "formula_claim": "framework-scope support only; do not claim learned compatibility or fusion superiority" if not learned_beats_point_rule else "learned advantage supported",
        "rule": "all sources pass within-size and global-four-family K=100 product gates, and frozen controls pass",
    }
    summary = {
        "schema_version": SCHEMA, "created_at_utc": now(),
        "status": "relative_size_three_source_evaluation_complete",
        "split_firewall": {"train": 1061, "internal_dev": 117, "final_validation": 157, "overlap": 0},
        "contexts": len(subgraphs), "K": list(KS), "n_bootstrap": n_bootstrap, "seed": seed,
        "model_sha256": sha256_file(paths["fit_model"]), "score_definition_sha256": lock_payload["score_definition_sha256"],
        "independent_point_evidence": extraction, "construct_audit": construct_audit, "controls": control_valid,
        "sources": source_results, "promotion_decision": promotion,
    }
    write_json(evaluation_out / "summary.json", summary)
    (evaluation_out / "summary.md").write_text(markdown(summary), encoding="utf-8")
    for filename, rows in (("metrics.csv", point_rows), ("global_composition.csv", composition_rows)):
        with (evaluation_out / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    manifest = {
        "schema_version": SCHEMA, "status": summary["status"], "promotion_decision": promotion,
        "inputs": {"model_sha256": sha256_file(paths["fit_model"]), "lock_sha256": sha256_file(paths["lock"]), "protocol_sha256": sha256_file(paths["protocol"]), "source_manifests": {
            source: sha256_file(path.parent / "manifest.json") for source, path in source_paths.items()
        }},
        "outputs": {name: {"path": relpath(root, evaluation_out / name), "sha256": sha256_file(evaluation_out / name)} for name in ("summary.json", "summary.md", "metrics.csv", "global_composition.csv", "final_object_stats.jsonl")},
        "docker_service": docker_service,
    }
    write_json(evaluation_out / "manifest.json", manifest)
    print(json.dumps({"status": summary["status"], "promotion_decision": promotion, "sources": {source: payload["gates"] for source, payload in source_results.items()}}))
    return 0


def main() -> int:
    args = parse_args()
    root, out = args.repo_root.resolve(), args.out
    out = out if out.is_absolute() else root / out
    if args.stage == "freeze":
        return freeze(root, out, args.docker_service)
    if args.stage == "fit":
        return fit(root, out, args.docker_service)
    if args.stage == "lock":
        return lock(root, out, args.docker_service)
    return evaluate(root, out, args.docker_service, args.n_bootstrap, args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
