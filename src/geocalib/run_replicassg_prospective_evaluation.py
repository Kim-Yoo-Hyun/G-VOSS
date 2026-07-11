#!/usr/bin/env python3
"""Evaluate the pre-inference-frozen H001 methods on ReplicaSSG/FROSS."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


SCHEMA_VERSION = "h001_replicassg_dataset_prospective_evaluation_v1"
FAMILIES = ("proximity", "relative_vertical")
KS = (5, 10, 20, 50, 100)
METHODS = (
    "semantic_only", "family_product", "rank_average_family", "rrf_c60",
    "product_M_T", "product_M_G", "product_M_add", "product_M_int",
)
PRIMARY_SOFT_METHODS = ("family_product", "rank_average_family")
COMPAT_MODELS = ("family_specific", "M_T", "M_G", "M_add", "M_int")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--verification", type=Path, required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--final-lock", type=Path, required=True)
    parser.add_argument("--adapter-manifest", type=Path, required=True)
    parser.add_argument("--geometry-manifest", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260711)
    parser.add_argument("--docker-service", default="replicassg_evaluation")
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


def finite(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def raw_numeric(row: dict[str, Any]) -> dict[str, float]:
    source = (row.get("geometry") or {}).get("features") or {}
    names = (
        "distance_3d", "distance_xy", "normalized_distance_3d", "normalized_distance_xy",
        "center_delta_z", "normalized_center_delta_z", "projected_iou_xy",
        "projected_subject_overlap_ratio", "projected_object_overlap_ratio",
        "vertical_gap_subject_on_object", "subject_bottom_z", "subject_top_z",
        "object_bottom_z", "object_top_z",
    )
    values = {name: value for name in names if (value := finite(source.get(name))) is not None}
    return derive_abs(values)


def derive_abs(values: dict[str, float]) -> dict[str, float]:
    result = dict(values)
    for source, target in (
        ("center_delta_z", "abs_center_delta_z"),
        ("normalized_center_delta_z", "abs_normalized_center_delta_z"),
        ("vertical_gap_subject_on_object", "abs_vertical_gap_subject_on_object"),
    ):
        if source in result:
            result[target] = abs(result[source])
    return result


def align_predicate(raw: dict[str, float], predicate: str) -> dict[str, float]:
    values = dict(raw)
    values.pop("predicate_aligned_center_delta_z", None)
    values.pop("predicate_aligned_normalized_center_delta_z", None)
    direction = 1.0 if predicate == "higher than" else -1.0 if predicate == "lower than" else 0.0
    if direction and "center_delta_z" in values:
        values["predicate_aligned_center_delta_z"] = direction * values["center_delta_z"]
    if direction and "normalized_center_delta_z" in values:
        values["predicate_aligned_normalized_center_delta_z"] = direction * values["normalized_center_delta_z"]
    return values


def sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def probability(model: dict[str, Any], family: str, predicate: str, raw: dict[str, float]) -> float:
    values = align_predicate(raw, predicate)
    vector: list[float] = []
    for feature in model["feature_names"]:
        if feature == "bias":
            vector.append(1.0)
        elif feature.startswith("family:"):
            vector.append(float(family == feature.split(":", 1)[1]))
        elif feature.startswith("predicate:"):
            vector.append(float(predicate == feature.split(":", 1)[1]))
        elif feature.startswith("num:"):
            name = feature.split(":", 1)[1]
            stat = model["numeric_stats"][name]
            vector.append((values.get(name, stat["mean"]) - stat["mean"]) / (stat["std"] or 1.0))
        else:
            raise ValueError(f"unsupported_feature:{feature}")
    if len(vector) != len(model["weights"]):
        raise ValueError("model_width_mismatch")
    return sigmoid(sum(left * right for left, right in zip(model["weights"], vector)))


def key(row: dict[str, Any]) -> tuple[str, int, int, int, str]:
    edge = row["edge"]
    return (
        str(row["scan_id"]), int(row["subset_split_id"]), int(edge["subject_id"]),
        int(edge["object_id"]), str(row["predicate"]["predicate_label"]),
    )


def gt_key(row: dict[str, Any]) -> tuple[str, int, int, int, str]:
    return (
        str(row["scan_id"]), int(row["subset_split_id"]), int(row["subject_id"]),
        int(row["object_id"]), str(row["predicate_label"]),
    )


def load_gt(path: Path, scans: list[str]) -> tuple[dict[str, set[tuple[Any, ...]]], dict[str, dict[str, set[tuple[Any, ...]]]]]:
    overall = {scan: set() for scan in scans}
    by_family = {scan: {family: set() for family in FAMILIES} for scan in scans}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            family = str(row["predicate_family"])
            if row["scan_id"] not in overall or family not in FAMILIES:
                raise ValueError("ground_truth_outside_frozen_scope")
            value = gt_key(row)
            overall[row["scan_id"]].add(value)
            by_family[row["scan_id"]][family].add(value)
    return overall, by_family


def load_candidates(path: Path, models: dict[str, Any], scans: list[str]) -> tuple[dict[str, list[dict[str, Any]]], int]:
    grouped = {scan: [] for scan in scans}
    rows = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows += 1
            row = json.loads(line)
            scan, family = str(row["scan_id"]), str(row["predicate"]["predicate_family"])
            if scan not in grouped or family not in FAMILIES:
                raise ValueError("candidate_outside_frozen_scope")
            predicate = str(row["predicate"]["predicate_label"])
            raw = raw_numeric(row)
            compatibility = {
                "family_specific": probability(models["family_models"][family], family, predicate, raw),
                **{
                    name: probability(model, family, predicate, raw)
                    for name, model in models["factor_models"].items()
                },
            }
            semantic = finite((row.get("semantic") or {}).get("ranking_score"))
            if semantic is None:
                raise ValueError(f"missing_semantic:{row['prediction_id']}")
            grouped[scan].append({
                "id": row["prediction_id"], "key": key(row), "family": family,
                "predicate": predicate, "subject": int(row["edge"]["subject_id"]),
                "object": int(row["edge"]["object_id"]), "semantic": semantic,
                "compat": compatibility, "raw": raw,
                "status": row.get("verification_status"), "scores": {},
            })
    for candidates in grouped.values():
        denominator = max(len(candidates) - 1, 1)
        semantic_order = sorted(candidates, key=lambda item: (-item["semantic"], item["key"]))
        geometry_order = sorted(candidates, key=lambda item: (-item["compat"]["family_specific"], item["key"]))
        semantic_rank = {item["id"]: index for index, item in enumerate(semantic_order, 1)}
        geometry_rank = {item["id"]: index for index, item in enumerate(geometry_order, 1)}
        for item in candidates:
            semantic_pct = 1.0 - (semantic_rank[item["id"]] - 1) / denominator
            geometry_pct = 1.0 - (geometry_rank[item["id"]] - 1) / denominator
            item["scores"] = {
                "semantic_only": item["semantic"],
                "family_product": item["semantic"] * item["compat"]["family_specific"],
                "rank_average_family": 0.5 * (semantic_pct + geometry_pct),
                "rrf_c60": 1.0 / (60 + semantic_rank[item["id"]]) + 1.0 / (60 + geometry_rank[item["id"]]),
                "product_M_T": item["semantic"] * item["compat"]["M_T"],
                "product_M_G": item["semantic"] * item["compat"]["M_G"],
                "product_M_add": item["semantic"] * item["compat"]["M_add"],
                "product_M_int": item["semantic"] * item["compat"]["M_int"],
            }
    return grouped, rows


def empty_arrays(scans: list[str]) -> dict[str, dict[str, np.ndarray]]:
    return {
        method: {
            name: np.zeros((len(KS), len(scans)), dtype=np.float64)
            for name in ("recall_num", "recall_den", "violation_num", "violation_den")
        }
        for method in METHODS
    }


def add_cell(target: dict[str, np.ndarray], ki: int, si: int, selected: list[dict[str, Any]], gt: set[tuple[Any, ...]]) -> None:
    target["recall_num"][ki, si] = len({row["key"] for row in selected} & gt)
    target["recall_den"][ki, si] = len(gt)
    statuses = [row["status"] for row in selected if row["status"] in {"satisfied", "uncertain", "violated"}]
    target["violation_num"][ki, si] = sum(value == "violated" for value in statuses)
    target["violation_den"][ki, si] = len(statuses)


def contributions(grouped: dict[str, list[dict[str, Any]]], gt: dict[str, set[tuple[Any, ...]]], gt_family: dict[str, dict[str, set[tuple[Any, ...]]]], scans: list[str]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    overall = empty_arrays(scans)
    within = {family: empty_arrays(scans) for family in FAMILIES}
    global_slice = {family: empty_arrays(scans) for family in FAMILIES}
    for si, scan in enumerate(scans):
        for method in METHODS:
            ranked = sorted(grouped[scan], key=lambda item: (-item["scores"][method], item["key"]))
            for ki, k_value in enumerate(KS):
                selected = ranked[:k_value]
                add_cell(overall[method], ki, si, selected, gt[scan])
                for family in FAMILIES:
                    ranked_family = [item for item in ranked if item["family"] == family]
                    add_cell(within[family][method], ki, si, ranked_family[:k_value], gt_family[scan][family])
                    add_cell(global_slice[family][method], ki, si, [item for item in selected if item["family"] == family], gt_family[scan][family])
    return overall, within, global_slice


def ci(values: np.ndarray) -> list[float | None]:
    values = values[np.isfinite(values)]
    return [float(value) for value in np.percentile(values, (2.5, 97.5))] if len(values) else [None, None]


def ratio(values: dict[str, np.ndarray], metric: str, ki: int, samples: np.ndarray) -> tuple[float | None, np.ndarray, int, int]:
    numerator, denominator = values[f"{metric}_num"][ki], values[f"{metric}_den"][ki]
    point = float(numerator.sum() / denominator.sum()) if denominator.sum() else None
    boot_num, boot_den = numerator[samples].sum(axis=1), denominator[samples].sum(axis=1)
    boot = np.divide(boot_num, boot_den, out=np.full_like(boot_num, np.nan), where=boot_den > 0)
    return point, boot, int(numerator.sum()), int(denominator.sum())


def summarize(values: dict[str, Any], samples: np.ndarray) -> tuple[dict[str, Any], dict[str, Any]]:
    report: dict[str, Any] = {}
    cache: dict[str, Any] = {}
    for method in METHODS:
        report[method], cache[method] = {}, {}
        for ki, k_value in enumerate(KS):
            report[method][str(k_value)], cache[method][str(k_value)] = {}, {}
            for metric in ("recall", "violation"):
                point, boot, numerator, denominator = ratio(values[method], metric, ki, samples)
                report[method][str(k_value)][metric] = {
                    "point": point, "ci95": ci(boot), "numerator": numerator, "denominator": denominator,
                }
                cache[method][str(k_value)][metric] = boot
    report["deltas_vs_semantic_only"] = {}
    for method in METHODS[1:]:
        report["deltas_vs_semantic_only"][method] = {}
        for k_value in KS:
            report["deltas_vs_semantic_only"][method][str(k_value)] = {}
            for metric in ("recall", "violation"):
                left = report[method][str(k_value)][metric]["point"]
                right = report["semantic_only"][str(k_value)][metric]["point"]
                delta_boot = cache[method][str(k_value)][metric] - cache["semantic_only"][str(k_value)][metric]
                report["deltas_vs_semantic_only"][method][str(k_value)][metric] = {
                    "point": left - right if left is not None and right is not None else None,
                    "paired_ci95": ci(delta_boot),
                }
    return report, cache


def add_familywise_ci(report: dict[str, Any], cache: dict[str, Any]) -> None:
    for method in METHODS[1:]:
        for k_value in KS:
            for metric in ("recall", "violation"):
                deltas, points, active = [], [], []
                for family in FAMILIES:
                    item = report[family]["deltas_vs_semantic_only"][method][str(k_value)][metric]
                    boot = cache[family][method][str(k_value)][metric] - cache[family]["semantic_only"][str(k_value)][metric]
                    if item["point"] is not None and np.any(np.isfinite(boot)):
                        deltas.append(boot)
                        points.append(item["point"])
                        active.append(family)
                radius = None
                if deltas:
                    matrix = np.column_stack(deltas)
                    radius = float(np.nanpercentile(np.nanmax(np.abs(matrix - np.asarray(points)[None, :]), axis=1), 95.0))
                for family in FAMILIES:
                    item = report[family]["deltas_vs_semantic_only"][method][str(k_value)][metric]
                    item["simultaneous_familywise_ci95"] = (
                        [item["point"] - radius, item["point"] + radius]
                        if radius is not None and family in active else [None, None]
                    )


def swap_raw(raw: dict[str, float]) -> dict[str, float]:
    result = dict(raw)
    for name in ("center_delta_z", "normalized_center_delta_z"):
        if name in result:
            result[name] = -result[name]
    left = raw.get("projected_subject_overlap_ratio")
    right = raw.get("projected_object_overlap_ratio")
    if right is not None:
        result["projected_subject_overlap_ratio"] = right
    if left is not None:
        result["projected_object_overlap_ratio"] = left
    for left_name, right_name in (
        ("subject_bottom_z", "object_bottom_z"), ("subject_top_z", "object_top_z")
    ):
        if right_name in raw:
            result[left_name] = raw[right_name]
        if left_name in raw:
            result[right_name] = raw[left_name]
    if "object_bottom_z" in raw and "subject_top_z" in raw:
        result["vertical_gap_subject_on_object"] = raw["object_bottom_z"] - raw["subject_top_z"]
    return derive_abs(result)


def clustered(values: list[tuple[str, float]], scans: list[str], samples: np.ndarray) -> dict[str, Any]:
    totals, counts = np.zeros(len(scans)), np.zeros(len(scans))
    indices = {scan: index for index, scan in enumerate(scans)}
    for scan, value in values:
        totals[indices[scan]] += value
        counts[indices[scan]] += 1
    boot_total, boot_count = totals[samples].sum(axis=1), counts[samples].sum(axis=1)
    boot = np.divide(boot_total, boot_count, out=np.full_like(boot_total, np.nan), where=boot_count > 0)
    raw = np.asarray([value for _, value in values])
    return {
        "rows": len(values), "contexts": int(np.sum(counts > 0)),
        "mean": float(raw.mean()) if len(raw) else None,
        "median": float(np.median(raw)) if len(raw) else None,
        "p95": float(np.percentile(raw, 95)) if len(raw) else None,
        "paired_scene_ci95": ci(boot),
    }


def controls(grouped: dict[str, list[dict[str, Any]]], gt: dict[str, set[tuple[Any, ...]]], models: dict[str, Any], scans: list[str], samples: np.ndarray) -> dict[str, Any]:
    result: dict[str, Any] = {
        "wrong_T_on_exact_GT_relative_vertical": {},
        "close_by_endpoint_swap_invariance": {},
        "vertical_inverse_equivariance": {},
        "wrong_pair_geometry": {},
        "support_contact_endpoint_swap": {"status": "not_run_prohibited_by_frozen_protocol"},
    }
    for name in COMPAT_MODELS:
        wrong_t, wrong_t_wins, close_swap, vertical_inverse, wrong_pair = [], [], [], [], []
        for scan in scans:
            candidates = grouped[scan]
            pair_raw: dict[tuple[int, int], dict[str, float]] = {}
            for row in candidates:
                pair_raw.setdefault((row["subject"], row["object"]), row["raw"])
                model = models["family_models"][row["family"]] if name == "family_specific" else models["factor_models"][name]
                if row["family"] == "relative_vertical" and row["key"] in gt[scan]:
                    inverse = "lower than" if row["predicate"] == "higher than" else "higher than"
                    difference = row["compat"][name] - probability(model, row["family"], inverse, row["raw"])
                    wrong_t.append((scan, difference))
                    wrong_t_wins.append((scan, float(difference > 0)))
                if row["predicate"] == "close by":
                    swapped = probability(model, row["family"], row["predicate"], swap_raw(row["raw"]))
                    close_swap.append((scan, abs(row["compat"][name] - swapped)))
                if row["family"] == "relative_vertical":
                    inverse = "lower than" if row["predicate"] == "higher than" else "higher than"
                    swapped = probability(model, row["family"], inverse, swap_raw(row["raw"]))
                    vertical_inverse.append((scan, abs(row["compat"][name] - swapped)))
            ordered_pairs = sorted(pair_raw)
            if len(ordered_pairs) > 1:
                shifted = {pair: ordered_pairs[(index + 1) % len(ordered_pairs)] for index, pair in enumerate(ordered_pairs)}
                for row in candidates:
                    if row["key"] not in gt[scan]:
                        continue
                    model = models["family_models"][row["family"]] if name == "family_specific" else models["factor_models"][name]
                    wrong = probability(model, row["family"], row["predicate"], pair_raw[shifted[(row["subject"], row["object"])]])
                    wrong_pair.append((scan, row["compat"][name] - wrong))
        result["wrong_T_on_exact_GT_relative_vertical"][name] = {
            "correct_minus_inverse": clustered(wrong_t, scans, samples),
            "correct_above_inverse_rate": clustered(wrong_t_wins, scans, samples),
        }
        result["close_by_endpoint_swap_invariance"][name] = {"absolute_error": clustered(close_swap, scans, samples)}
        result["vertical_inverse_equivariance"][name] = {"absolute_error": clustered(vertical_inverse, scans, samples)}
        result["wrong_pair_geometry"][name] = {"correct_minus_wrong_pair": clustered(wrong_pair, scans, samples)}
    result["wrong_pair_geometry"]["transform"] = "within-scene lexicographic directed-pair cyclic shift; T fixed; exact-label GT candidate rows only"
    return result


def gate(overall: dict[str, Any], method: str) -> dict[str, Any]:
    delta = overall["deltas_vs_semantic_only"][method]["100"]
    recall_ci = delta["recall"]["paired_ci95"]
    violation_ci = delta["violation"]["paired_ci95"]
    recall_pass = recall_ci[0] is not None and recall_ci[0] > -0.01
    violation_pass = violation_ci[1] is not None and violation_ci[1] < 0.0
    return {
        "decision": "pass" if recall_pass and violation_pass else "fail",
        "recall_guardrail_pass": recall_pass,
        "violation_gate_pass": violation_pass,
        "delta_recall_at_100": delta["recall"],
        "delta_violation_at_100": delta["violation"],
        "rule": "paired dRecall@100 CI lower > -0.01 and paired dViolation@100 CI upper < 0",
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# ReplicaSSG dataset-level prospective evaluation", "",
        f"Status: `{report['status']}`", "",
        "| method | Recall@100 | delta Recall | V@100 | delta V | gate |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    overall = report["overall"]
    for method in METHODS:
        cell = overall[method]["100"]
        delta = overall["deltas_vs_semantic_only"].get(method, {}).get("100", {})
        gate_value = report["joint_gates"].get(method, {}).get("decision", "diagnostic")
        lines.append(
            f"| {method} | {cell['recall']['point']:.6f} | {delta.get('recall', {}).get('point', 0.0):.6f} | "
            f"{cell['violation']['point']:.6f} | {delta.get('violation', {}).get('point', 0.0):.6f} | {gate_value} |"
        )
    lines.extend([
        "", f"Framework gate: `{report['framework_gate']['decision']}`",
        f"Formula-robust gate: `{report['formula_robust_gate']['decision']}`", "",
    ])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    paths = {
        name: resolve(root, value) for name, value in {
            "verification": args.verification, "ground_truth": args.ground_truth,
            "models": args.models, "protocol": args.protocol, "final_lock": args.final_lock,
            "adapter_manifest": args.adapter_manifest, "geometry_manifest": args.geometry_manifest,
            "source_manifest": args.source_manifest,
        }.items()
    }
    out = resolve(root, args.out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"nonempty_output:{out}")
    protocol = json.loads(paths["protocol"].read_text(encoding="utf-8"))
    models = json.loads(paths["models"].read_text(encoding="utf-8"))
    final_lock = json.loads(paths["final_lock"].read_text(encoding="utf-8"))
    adapter = json.loads(paths["adapter_manifest"].read_text(encoding="utf-8"))
    geometry_manifest = json.loads(paths["geometry_manifest"].read_text(encoding="utf-8"))
    source_manifest = json.loads(paths["source_manifest"].read_text(encoding="utf-8"))
    scans = list(protocol["dataset"]["test_scans"])
    gt, gt_family = load_gt(paths["ground_truth"], scans)
    grouped, input_rows = load_candidates(paths["verification"], models, scans)
    rng = np.random.default_rng(args.seed)
    samples = rng.integers(0, len(scans), size=(args.n_bootstrap, len(scans)))
    overall_values, within_values, slice_values = contributions(grouped, gt, gt_family, scans)
    overall, _ = summarize(overall_values, samples)
    within, within_cache, global_slice, global_cache = {}, {}, {}, {}
    for family in FAMILIES:
        within[family], within_cache[family] = summarize(within_values[family], samples)
        global_slice[family], global_cache[family] = summarize(slice_values[family], samples)
    add_familywise_ci(within, within_cache)
    add_familywise_ci(global_slice, global_cache)
    gates = {method: gate(overall, method) for method in PRIMARY_SOFT_METHODS}
    framework_pass = any(value["decision"] == "pass" for value in gates.values())
    robust_pass = all(value["decision"] == "pass" for value in gates.values())
    gt_denominator = sum(len(value) for value in gt.values())
    validation_scans = set(protocol["dataset"]["validation_scans"])
    code_hashes = protocol.get("implementation_hashes", {})
    validations = {
        "protocol_frozen_before_source_prediction": (
            protocol.get("status") == "frozen_before_source_prediction"
            and protocol["semantic_source"]["source_prediction_present_at_freeze"] is False
        ),
        "dataset_and_source_classification_frozen": protocol.get("classification_target") == "untouched_dataset_and_source_prospective_confirmation",
        "contexts_exact": len(scans) == 11 and set(grouped) == set(scans),
        "gt_denominator_exact": gt_denominator == 172,
        "validation_test_overlap_zero": not validation_scans.intersection(scans),
        "replica_archive_hash_locked_pre_source": (
            protocol["dataset"].get("base_archive_hash_status") == "locked_pre_source"
            and isinstance(protocol["dataset"].get("base_archive_sha256"), str)
            and len(protocol["dataset"]["base_archive_sha256"]) == 64
        ),
        "validation_candidates_absent": not validation_scans.intersection(grouped),
        "models_hash_locked": sha256(paths["models"]) == protocol["frozen_methods"]["model_sha256"] == final_lock["hashes"]["models_sha256"],
        "adapter_candidate_firewall": adapter["firewall"]["relationship_annotations_read_by_adapter"] is False,
        "source_merge_ready": source_manifest.get("status") == "frozen_source_prediction_ready",
        "source_uses_exact_frozen_protocol": source_manifest["inputs"]["protocol"]["sha256"] == sha256(paths["protocol"]),
        "source_weight_hash_locked": source_manifest["inputs"]["weight_zip"]["sha256"] == protocol["semantic_source"]["weight_zip_sha256"],
        "source_prediction_hash_chain": source_manifest["output"]["sha256"] == adapter["inputs"]["prediction"]["sha256"],
        "source_runtime_artifacts_complete": set(source_manifest.get("runtime_artifacts", {})) == {
            "config.json", "checkpoints/epoch=23-validation_loss=4.60.ckpt",
            "rt-detr.onnx", "egtr-head.onnx", "rt-detr.engine", "egtr-head.engine",
            "h001_engine_manifest.json",
        },
        "prospective_timestamp_order": (
            protocol["created_at_utc"] < source_manifest["created_at_utc"]
            < adapter["created_at_utc"] < geometry_manifest["created_at_utc"]
        ),
        "geometry_relation_gt_firewall": geometry_manifest["firewall"]["relation_ground_truth_used"] is False,
        "rows_preserved": geometry_manifest["counts"]["rows_preserved"] is True and input_rows == adapter["counts"]["candidate_rows"],
        "bootstrap_frozen": args.n_bootstrap == 1000 and args.seed == 20260711,
        "all_frozen_methods_reported": set(METHODS) == set(overall) - {"deltas_vs_semantic_only"},
        "adapter_code_hash_locked": code_hashes.get("adapter_sha256") == sha256(root / "src/geocalib/export_replicassg_fross_predictions.py"),
        "geometry_code_hash_locked": code_hashes.get("geometry_sha256") == sha256(root / "src/geocalib/score_replicassg_geometry.py"),
        "evaluator_code_hash_locked": code_hashes.get("evaluator_sha256") == sha256(Path(__file__).resolve()),
        "shard_merger_code_hash_locked": code_hashes.get("shard_merger_sha256") == sha256(root / "src/geocalib/merge_replicassg_fross_shards.py"),
        "streaming_runner_hash_locked": code_hashes.get("streaming_runner_sha256") == sha256(root / "scripts/run_replicassg_fross_streaming.sh"),
        "compose_hash_locked": code_hashes.get("compose_sha256") == sha256(root / "configs/fross/compose.yaml"),
    }
    status = "dataset_level_prospective_evaluation_ready" if all(validations.values()) else "blocked_prospective_evaluation"
    report = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "classification": "untouched ReplicaSSG dataset plus untouched FROSS source, protocol frozen before source prediction",
        "counts": {
            "contexts": len(scans), "candidate_rows": input_rows, "gt_denominator": gt_denominator,
            "candidate_rows_by_context": {scan: len(grouped[scan]) for scan in scans},
        },
        "methods": list(METHODS), "primary_methods": list(PRIMARY_SOFT_METHODS), "ks": list(KS),
        "overall": overall, "within_family": within, "global_topk_family_slice": global_slice,
        "controls": controls(grouped, gt, models, scans, samples),
        "joint_gates": gates,
        "framework_gate": {
            "decision": "pass" if framework_pass else "fail",
            "rule": "at least one of family_product or rank_average_family passes its frozen joint gate",
        },
        "formula_robust_gate": {
            "decision": "pass" if robust_pass else "fail",
            "rule": "both family_product and rank_average_family pass their frozen joint gates",
        },
        "validations": validations,
        "limitations": [
            "Violation is verifier-derived rather than an independent human physical-validity outcome.",
            "FROSS objects are associated to ReplicaSSG instance IDs with the official GT-object matching protocol.",
            "Geometry uses ReplicaSSG instance-annotated face-center point clouds; relation labels are not used for scoring.",
            "Only exact near/above/under mappings are evaluated; support/contact transfer is not claimed.",
            "There are 11 independent test-scene bootstrap units, so confidence intervals may be wide.",
        ],
        "inputs": {name: {"path": relpath(root, path), "sha256": sha256(path)} for name, path in paths.items()},
        "docker_command": f"env UID=$(id -u) GID=$(id -g) docker compose -f configs/fross/compose.yaml run --rm {args.docker_service}",
    }
    out.mkdir(parents=True, exist_ok=False)
    summary_json = out / "summary.json"
    summary_md = out / "summary.md"
    summary_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_md.write_text(markdown(report), encoding="utf-8")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": report["created_at_utc"], "status": status, "validations": validations,
        "outputs": {
            "summary_json": {"path": relpath(root, summary_json), "sha256": sha256(summary_json)},
            "summary_md": {"path": relpath(root, summary_md), "sha256": sha256(summary_md)},
        },
        "docker_command": report["docker_command"],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": status, "counts": report["counts"], "joint_gates": gates,
        "framework_gate": report["framework_gate"], "formula_robust_gate": report["formula_robust_gate"],
    }, sort_keys=True))
    return 0 if all(validations.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
