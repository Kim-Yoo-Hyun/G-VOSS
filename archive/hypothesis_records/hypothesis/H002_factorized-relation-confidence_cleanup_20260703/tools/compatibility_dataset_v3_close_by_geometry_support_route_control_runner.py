#!/usr/bin/env python3
"""Run deterministic R1 close-by geometry-support route controls."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan"
DEFAULT_ROUTE_ROOT = H2_ROOT / "artifacts/route_specific_targets/r1_proximity"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_close_by_geometry_support_route_control_runner"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_close_by_geometry_support_route_control_runner"
EXPECTED_ROUTE_STATUS = "h002_compatibility_dataset_v3_close_by_geometry_support_route_materialization_after_plan_ready"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_close_by_geometry_support_route_control_runner_v1"
STATUS_READY = "h002_compatibility_dataset_v3_close_by_geometry_support_route_control_runner_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_close_by_geometry_support_route_control_runner_input_errors"
SELECTED_PATH = "ran_r1_close_by_geometry_only_route_controls_no_interaction_model"
NEXT_TODO = "compatibility_dataset_v3_close_by_geometry_support_route_result_review"

EXPECTED_TOTAL_ROWS = 1284
EXPECTED_PRIMARY_ROWS = 800
EXPECTED_CONTROL_ROWS = 12


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--route-root", type=Path, default=DEFAULT_ROUTE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def nested_get(row: dict[str, Any], dotted: str, default: Any = None) -> Any:
    value: Any = row
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(parsed):
        return default
    return parsed


def auc_score(labels: list[int], scores: list[float]) -> float | None:
    if not labels or len(labels) != len(scores):
        return None
    n_pos = sum(1 for label in labels if label == 1)
    n_neg = sum(1 for label in labels if label == 0)
    if n_pos == 0 or n_neg == 0:
        return None
    indexed = sorted(enumerate(scores), key=lambda item: item[1])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    pos_rank_sum = sum(rank for rank, label in zip(ranks, labels) if label == 1)
    return (pos_rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def binary_metrics(labels: list[int], scores: list[float]) -> dict[str, Any]:
    if not labels or len(labels) != len(scores):
        return {
            "rows": len(labels),
            "auroc": "",
            "best_accuracy": "",
            "best_f1": "",
            "best_threshold": "",
            "positive": sum(1 for label in labels if label == 1),
            "negative": sum(1 for label in labels if label == 0),
        }
    candidates = sorted(set(scores))
    thresholds = [max(candidates) + 1.0] + candidates + [min(candidates) - 1.0]
    best = {"accuracy": -1.0, "f1": -1.0, "threshold": ""}
    for threshold in thresholds:
        tp = fp = tn = fn = 0
        for label, score in zip(labels, scores):
            pred = 1 if score >= threshold else 0
            if label == 1 and pred == 1:
                tp += 1
            elif label == 1 and pred == 0:
                fn += 1
            elif label == 0 and pred == 1:
                fp += 1
            else:
                tn += 1
        accuracy = (tp + tn) / len(labels)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        if accuracy > best["accuracy"] or (accuracy == best["accuracy"] and f1 > best["f1"]):
            best = {"accuracy": accuracy, "f1": f1, "threshold": threshold}
    return {
        "rows": len(labels),
        "positive": sum(1 for label in labels if label == 1),
        "negative": sum(1 for label in labels if label == 0),
        "auroc": auc_score(labels, scores),
        "best_accuracy": best["accuracy"],
        "best_f1": best["f1"],
        "best_threshold": best["threshold"],
    }


def categorical_majority_metrics(labels: list[int], categories: list[str]) -> dict[str, Any]:
    counts: dict[str, Counter[int]] = defaultdict(Counter)
    for label, category in zip(labels, categories):
        counts[str(category)][label] += 1
    correct = 0
    for label, category in zip(labels, categories):
        counter = counts[str(category)]
        pred = 1 if counter[1] >= counter[0] else 0
        correct += int(pred == label)
    return {
        "rows": len(labels),
        "positive": sum(1 for label in labels if label == 1),
        "negative": sum(1 for label in labels if label == 0),
        "num_categories": len(counts),
        "majority_accuracy": correct / len(labels) if labels else "",
    }


def validate_inputs(
    plan_summary: dict[str, Any],
    route_summary: dict[str, Any],
    plan_errors: list[dict[str, Any]],
    route_errors: list[dict[str, Any]],
    control_rows: list[dict[str, str]],
    model_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0 or plan_errors:
        errors.append(
            {
                "error_type": "plan_validation_errors_present",
                "summary_count": plan_summary.get("validation_errors"),
                "rows": len(plan_errors),
            }
        )
    if route_summary.get("status") != EXPECTED_ROUTE_STATUS:
        errors.append({"error_type": "unexpected_route_status", "actual": route_summary.get("status")})
    if route_summary.get("validation_errors") != 0 or route_errors:
        errors.append(
            {
                "error_type": "route_validation_errors_present",
                "summary_count": route_summary.get("validation_errors"),
                "rows": len(route_errors),
            }
        )
    if len(control_rows) != EXPECTED_CONTROL_ROWS:
        errors.append({"error_type": "unexpected_control_plan_rows", "actual": len(control_rows)})
    if len(model_rows) != EXPECTED_TOTAL_ROWS or len(hidden_rows) != EXPECTED_TOTAL_ROWS:
        errors.append({"error_type": "unexpected_row_count", "model": len(model_rows), "hidden": len(hidden_rows)})
    hidden_ids = {row.get("route_row_id") for row in hidden_rows}
    model_ids = {row.get("route_row_id") for row in model_rows}
    if model_ids != hidden_ids:
        errors.append({"error_type": "model_hidden_route_id_mismatch"})
    primary_rows = [row for row in model_rows if row.get("route_targets", {}).get("is_primary_binary")]
    if len(primary_rows) != EXPECTED_PRIMARY_ROWS:
        errors.append({"error_type": "unexpected_primary_rows", "actual": len(primary_rows)})
    for name, summary in [("plan", plan_summary), ("route", route_summary)]:
        boundary = summary.get("boundary", {})
        for key in ["h001_artifacts_modified", "validation_usage", "test_usage", "runs_model", "paper_evidence_allowed_now"]:
            if key in boundary and boundary.get(key) is not False:
                errors.append({"error_type": "boundary_not_false", "summary": name, "key": key, "actual": boundary.get(key)})
    return errors


def primary_pairs(model_rows: list[dict[str, Any]], hidden_rows: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    hidden_by_id = {row["route_row_id"]: row for row in hidden_rows}
    pairs = []
    for row in model_rows:
        label = row.get("route_targets", {}).get("geometry_support_binary")
        if row.get("route_targets", {}).get("is_primary_binary") and label in {0, 1}:
            pairs.append((row, hidden_by_id[row["route_row_id"]]))
    return pairs


def binary_pairs_for_subsets(
    model_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    subsets: set[str],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    hidden_by_id = {row["route_row_id"]: row for row in hidden_rows}
    pairs = []
    for row in model_rows:
        label = row.get("route_targets", {}).get("geometry_support_binary")
        if row.get("subset") in subsets and label in {0, 1}:
            pairs.append((row, hidden_by_id[row["route_row_id"]]))
    return pairs


def labels_from_pairs(pairs: list[tuple[dict[str, Any], dict[str, Any]]]) -> list[int]:
    return [int(row.get("route_targets", {}).get("geometry_support_binary")) for row, _ in pairs]


def g_value(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    return float(safe_float(nested_get(row, f"feature_blocks.G_e_route.{key}"), default))


def z_value(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    return float(safe_float(nested_get(row, f"feature_blocks.Z_e_source_baseline.{key}"), default))


def hidden_value(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    return float(safe_float(nested_get(row, f"hidden_controls.{key}"), default))


def metric_row(control_id: str, control_name: str, rows_used: str, labels: list[int], scores: list[float], **extra: Any) -> dict[str, Any]:
    metrics = binary_metrics(labels, scores)
    payload = {
        "control_id": control_id,
        "control_name": control_name,
        "rows_used": rows_used,
        "rows": metrics["rows"],
        "positive": metrics["positive"],
        "negative": metrics["negative"],
        "auroc": metrics["auroc"],
        "best_accuracy": metrics["best_accuracy"],
        "best_f1": metrics["best_f1"],
        "best_threshold": metrics["best_threshold"],
    }
    payload.update(extra)
    return payload


def build_shifted_scores(
    pairs: list[tuple[dict[str, Any], dict[str, Any]]],
    key: str,
    group_key: str | None,
    shift: int,
) -> list[float]:
    if group_key is None:
        ordered = [row for row, _ in pairs]
        return [-g_value(ordered[(idx + shift) % len(ordered)], key) for idx in range(len(ordered))]

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row, hidden in pairs:
        groups[str(nested_get(hidden, f"hidden_controls.{group_key}", "missing"))].append(row)
    scores = []
    for row, hidden in pairs:
        group = groups[str(nested_get(hidden, f"hidden_controls.{group_key}", "missing"))]
        if len(group) < 2:
            ordered = [candidate for candidate, _ in pairs]
            source = ordered[(ordered.index(row) + shift) % len(ordered)]
        else:
            idx = group.index(row)
            source = group[(idx + 1) % len(group)]
        scores.append(-g_value(source, key))
    return scores


def run_metrics(model_rows: list[dict[str, Any]], hidden_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    primary = primary_pairs(model_rows, hidden_rows)
    primary_labels = labels_from_pairs(primary)
    primary_rows = [row for row, _ in primary]
    primary_hidden = [hidden for _, hidden in primary]
    combined = binary_pairs_for_subsets(model_rows, hidden_rows, {"primary_binary", "raw_distance_diagnostic"})
    combined_labels = labels_from_pairs(combined)
    combined_rows = [row for row, _ in combined]
    combined_hidden = [hidden for _, hidden in combined]

    metrics: list[dict[str, Any]] = []
    score_rows: list[dict[str, Any]] = []
    flags: list[dict[str, Any]] = []

    score_defs = {
        "distance_xy": [-g_value(row, "distance_xy") for row in primary_rows],
        "distance_3d": [-g_value(row, "distance_3d") for row in primary_rows],
        "normalized_distance_xy": [-g_value(row, "normalized_distance_xy") for row in primary_rows],
        "normalized_distance_3d": [-g_value(row, "normalized_distance_3d") for row in primary_rows],
        "overlap_geometry": [
            max(
                g_value(row, "projected_iou_xy"),
                g_value(row, "projected_subject_overlap_ratio"),
                g_value(row, "projected_object_overlap_ratio"),
            )
            for row in primary_rows
        ],
        "source_semantic_score_norm": [z_value(row, "semantic_score_norm") for row in primary_rows],
        "source_rank_inverse": [-z_value(row, "rank_in_context") for row in primary_rows],
        "p_geom_valid_hidden": [hidden_value(hidden, "p_geom_valid") for hidden in primary_hidden],
    }

    metrics.append(metric_row("C1", "distance_xy", "primary_binary", primary_labels, score_defs["distance_xy"]))
    metrics.append(metric_row("C2", "distance_3d", "primary_binary", primary_labels, score_defs["distance_3d"]))
    metrics.append(metric_row("C3", "normalized_distance_xy", "primary_binary", primary_labels, score_defs["normalized_distance_xy"]))
    metrics.append(metric_row("C4", "normalized_distance_3d", "primary_binary", primary_labels, score_defs["normalized_distance_3d"]))
    metrics.append(metric_row("C5", "overlap_geometry", "primary_binary", primary_labels, score_defs["overlap_geometry"]))

    raw_primary = binary_metrics(primary_labels, score_defs["distance_xy"])
    norm_primary = binary_metrics(primary_labels, score_defs["normalized_distance_xy"])
    raw_diag_scores = [-g_value(row, "distance_xy") for row in combined_rows]
    norm_diag_scores = [-g_value(row, "normalized_distance_xy") for row in combined_rows]
    raw_diag = binary_metrics(combined_labels, raw_diag_scores)
    norm_diag = binary_metrics(combined_labels, norm_diag_scores)
    metrics.append(
        {
            "control_id": "C6",
            "control_name": "scale_control",
            "rows_used": "primary_binary+raw_distance_diagnostic",
            "rows": len(combined_labels),
            "positive": sum(combined_labels),
            "negative": len(combined_labels) - sum(combined_labels),
            "auroc": norm_diag["auroc"],
            "best_accuracy": norm_diag["best_accuracy"],
            "best_f1": norm_diag["best_f1"],
            "best_threshold": norm_diag["best_threshold"],
            "raw_distance_primary_auroc": raw_primary["auroc"],
            "normalized_distance_primary_auroc": norm_primary["auroc"],
            "raw_distance_combined_auroc": raw_diag["auroc"],
            "normalized_distance_combined_auroc": norm_diag["auroc"],
            "normalized_minus_raw_primary_auroc": None
            if raw_primary["auroc"] in {"", None} or norm_primary["auroc"] in {"", None}
            else norm_primary["auroc"] - raw_primary["auroc"],
            "normalized_minus_raw_combined_auroc": None
            if raw_diag["auroc"] in {"", None} or norm_diag["auroc"] in {"", None}
            else norm_diag["auroc"] - raw_diag["auroc"],
        }
    )

    subset_counts = Counter(row.get("subset") for row in model_rows)
    q_complete = sum(
        1
        for row in model_rows
        if nested_get(row, "feature_blocks.Q_e_observability.geometry_available") is True
        and nested_get(row, "feature_blocks.Q_e_observability.geometry_checkable") is True
        and nested_get(row, "feature_blocks.Q_e_observability.feature_complete") is True
    )
    metrics.append(
        {
            "control_id": "C7",
            "control_name": "coverage_control",
            "rows_used": "all_rows",
            "rows": len(model_rows),
            "positive": "",
            "negative": "",
            "auroc": "",
            "best_accuracy": "",
            "best_f1": "",
            "best_threshold": "",
            "primary_binary_rows": subset_counts.get("primary_binary", 0),
            "raw_distance_diagnostic_rows": subset_counts.get("raw_distance_diagnostic", 0),
            "abstain_qe_rows": subset_counts.get("abstain_qe", 0),
            "diagnostic_only_rows": subset_counts.get("diagnostic_only", 0),
            "q_e_complete_rows": q_complete,
        }
    )

    semantic = binary_metrics(primary_labels, score_defs["source_semantic_score_norm"])
    rank = binary_metrics(primary_labels, score_defs["source_rank_inverse"])
    metrics.append(
        {
            "control_id": "C8",
            "control_name": "source_score_rank",
            "rows_used": "primary_binary",
            "rows": len(primary_labels),
            "positive": sum(primary_labels),
            "negative": len(primary_labels) - sum(primary_labels),
            "auroc": semantic["auroc"],
            "best_accuracy": semantic["best_accuracy"],
            "best_f1": semantic["best_f1"],
            "best_threshold": semantic["best_threshold"],
            "rank_inverse_auroc": rank["auroc"],
            "rank_inverse_best_accuracy": rank["best_accuracy"],
        }
    )

    class_pair_metrics = categorical_majority_metrics(
        primary_labels,
        [str(nested_get(hidden, "hidden_controls.subject_object_class_pair", "missing")) for hidden in primary_hidden],
    )
    metrics.append(
        {
            "control_id": "C9",
            "control_name": "class_pair_only",
            "rows_used": "primary_binary_hidden_audit",
            "rows": class_pair_metrics["rows"],
            "positive": class_pair_metrics["positive"],
            "negative": class_pair_metrics["negative"],
            "auroc": "",
            "best_accuracy": class_pair_metrics["majority_accuracy"],
            "best_f1": "",
            "best_threshold": "",
            "num_categories": class_pair_metrics["num_categories"],
        }
    )

    metrics.append(
        metric_row(
            "C10",
            "p_geom_valid_hidden_baseline",
            "primary_binary_hidden_audit",
            primary_labels,
            score_defs["p_geom_valid_hidden"],
            hidden_reference_only=True,
        )
    )

    true_norm_auc = norm_primary["auroc"]
    shuffled_scores = build_shifted_scores(primary, "normalized_distance_xy", None, 137)
    shuffled = binary_metrics(primary_labels, shuffled_scores)
    metrics.append(
        {
            "control_id": "C11",
            "control_name": "shuffled_G",
            "rows_used": "primary_binary",
            "rows": len(primary_labels),
            "positive": sum(primary_labels),
            "negative": len(primary_labels) - sum(primary_labels),
            "auroc": shuffled["auroc"],
            "best_accuracy": shuffled["best_accuracy"],
            "best_f1": shuffled["best_f1"],
            "best_threshold": shuffled["best_threshold"],
            "true_normalized_distance_xy_auroc": true_norm_auc,
            "control_drop": None if true_norm_auc in {"", None} or shuffled["auroc"] in {"", None} else true_norm_auc - shuffled["auroc"],
        }
    )

    wrong_pair_scores = build_shifted_scores(primary, "normalized_distance_xy", "rank_band", 1)
    wrong_pair = binary_metrics(primary_labels, wrong_pair_scores)
    metrics.append(
        {
            "control_id": "C12",
            "control_name": "wrong_pair_geometry",
            "rows_used": "primary_binary_same_rank_band_rotation",
            "rows": len(primary_labels),
            "positive": sum(primary_labels),
            "negative": len(primary_labels) - sum(primary_labels),
            "auroc": wrong_pair["auroc"],
            "best_accuracy": wrong_pair["best_accuracy"],
            "best_f1": wrong_pair["best_f1"],
            "best_threshold": wrong_pair["best_threshold"],
            "true_normalized_distance_xy_auroc": true_norm_auc,
            "control_drop": None if true_norm_auc in {"", None} or wrong_pair["auroc"] in {"", None} else true_norm_auc - wrong_pair["auroc"],
        }
    )

    for (row, hidden), shuffled_score, wrong_score in zip(primary, shuffled_scores, wrong_pair_scores):
        score_rows.append(
            {
                "route_row_id": row["route_row_id"],
                "subset": row.get("subset"),
                "label": row.get("route_targets", {}).get("geometry_support_binary"),
                "distance_xy_score": -g_value(row, "distance_xy"),
                "distance_3d_score": -g_value(row, "distance_3d"),
                "normalized_distance_xy_score": -g_value(row, "normalized_distance_xy"),
                "normalized_distance_3d_score": -g_value(row, "normalized_distance_3d"),
                "overlap_geometry_score": max(
                    g_value(row, "projected_iou_xy"),
                    g_value(row, "projected_subject_overlap_ratio"),
                    g_value(row, "projected_object_overlap_ratio"),
                ),
                "semantic_score_norm": z_value(row, "semantic_score_norm"),
                "rank_inverse_score": -z_value(row, "rank_in_context"),
                "p_geom_valid_hidden_score": hidden_value(hidden, "p_geom_valid"),
                "shuffled_normalized_distance_xy_score": shuffled_score,
                "wrong_pair_normalized_distance_xy_score": wrong_score,
            }
        )

    by_metric = {row["control_name"]: row for row in metrics}
    for control_name, threshold, direction in [
        ("normalized_distance_xy", 0.95, "min"),
        ("normalized_distance_3d", 0.95, "min"),
        ("shuffled_G", 0.80, "max"),
        ("wrong_pair_geometry", 0.80, "max"),
    ]:
        value = by_metric.get(control_name, {}).get("auroc")
        if isinstance(value, (int, float)):
            if direction == "min" and value < threshold:
                flags.append({"flag": "unexpected_low_auroc", "control_name": control_name, "value": value, "threshold": threshold})
            if direction == "max" and value > threshold:
                flags.append({"flag": "control_too_strong", "control_name": control_name, "value": value, "threshold": threshold})
    return metrics, score_rows, flags


def render_report(summary: dict[str, Any], metrics: list[dict[str, Any]]) -> str:
    by_name = {row["control_name"]: row for row in metrics}
    def fmt(name: str, key: str = "auroc") -> str:
        value = by_name.get(name, {}).get(key, "")
        return "" if value == "" else f"{float(value):.6f}"

    return f"""# H002 R1 Close-By Geometry-Support Route Control Runner

## Status

```text
status = {summary['status']}
selected_path = {summary['selected_path']}
validation_errors = {summary['validation_errors']}
next_todo = {summary['next_todo']}
```

## Result

Deterministic geometry-only route controls were executed for R1 `close by`.
No learned model was trained.

Key AUROC values:

| Control | AUROC |
| --- | ---: |
| `distance_xy` | {fmt('distance_xy')} |
| `distance_3d` | {fmt('distance_3d')} |
| `normalized_distance_xy` | {fmt('normalized_distance_xy')} |
| `normalized_distance_3d` | {fmt('normalized_distance_3d')} |
| `source_score_rank` semantic score | {fmt('source_score_rank')} |
| `p_geom_valid_hidden_baseline` | {fmt('p_geom_valid_hidden_baseline')} |
| `shuffled_G` | {fmt('shuffled_G')} |
| `wrong_pair_geometry` | {fmt('wrong_pair_geometry')} |

## Interpretation

This result confirms that R1 `close by` is a geometry-only route. Strong
distance metrics are expected and are not evidence of `T_e x G_e` interaction.

## Boundary

- Train-only deterministic control runner.
- No validation/test used.
- No model training.
- No paper-level claim from R1 alone.
- H001 artifacts were not modified.

## Next

```text
{summary['next_todo']}
```
"""


def main() -> None:
    args = parse_args()

    plan_summary = read_json(args.plan_dir / "summary.json")
    route_summary = read_json(args.route_root / "summary.json")
    plan_errors = read_jsonl(args.plan_dir / "validation_errors.jsonl")
    route_errors = read_jsonl(args.route_root / "validation_errors.jsonl")
    control_rows = read_csv(args.plan_dir / "control_runner_plan.csv")
    model_rows = read_jsonl(args.route_root / "model_safe_rows.jsonl")
    hidden_rows = read_jsonl(args.route_root / "hidden_manifest.jsonl")

    errors = validate_inputs(plan_summary, route_summary, plan_errors, route_errors, control_rows, model_rows, hidden_rows)
    metrics, score_rows, flags = run_metrics(model_rows, hidden_rows)
    errors.extend([{"error_type": "control_failure_flag", **flag} for flag in flags if flag["flag"] == "unexpected_low_auroc"])

    status = STATUS_READY if not errors else STATUS_ERRORS
    output_paths = {
        "summary": args.output_dir / "summary.json",
        "route_control_metrics": args.output_dir / "route_control_metrics.csv",
        "route_control_scores": args.output_dir / "route_control_scores.jsonl",
        "control_failure_flags": args.output_dir / "control_failure_flags.csv",
        "report": args.output_dir / "report.md",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }
    summary = {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed_now": False,
            "runs_metrics": True,
            "runs_model": False,
            "test_usage": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_artifacts": {
            "plan": rel_path(args.plan_dir),
            "route_root": rel_path(args.route_root),
        },
        "next_todo": NEXT_TODO,
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "route": route_summary.get("route", {}),
        "row_counts": route_summary.get("row_counts", {}),
        "schema_version": SCHEMA_VERSION,
        "selected_path": SELECTED_PATH,
        "status": status,
        "validation_errors": len(errors),
    }

    write_json(output_paths["summary"], summary)
    write_csv(output_paths["route_control_metrics"], metrics)
    write_jsonl(output_paths["route_control_scores"], score_rows)
    write_csv(output_paths["control_failure_flags"], flags)
    write_jsonl(output_paths["validation_errors"], errors)
    output_paths["report"].write_text(render_report(summary, metrics), encoding="utf-8")


if __name__ == "__main__":
    main()
