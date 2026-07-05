#!/usr/bin/env python3
"""Error analysis for H002 raw-witness v2 combiner smoke."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_SMOKE_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready"

SPLIT_EVAL = "train_internal_grouped_by_scan"
LEGACY_REFERENCE = "C0_semantic_plus_geometry_legacy"
PRIMARY_REFERENCE = "C3_linear_v2"
ENDPOINT_ONLY = "K5_endpoint_type_only"
NEW_CANDIDATES = [
    "C4_calibrated_linear_v2",
    "C5_constrained_monotonic_additive",
    "C6_family_gated_calibrated_mixture",
    "C7_limited_interaction_model",
]
MAIN_VIEWS = [
    LEGACY_REFERENCE,
    "C1_raw_witness_only_v2",
    "C2_semantic_plus_raw_witness_v2",
    PRIMARY_REFERENCE,
    *NEW_CANDIDATES,
    "C8_endpoint_type_ablation_only",
]
CONTROL_VIEWS = [
    "K0_global_raw_witness_shuffle",
    "K1_within_family_raw_witness_shuffle",
    "K2_wrong_pair_raw_witness",
    "K3_family_only_offset",
    "K4_no_family_local_normalization",
    ENDPOINT_ONLY,
]
ANALYSIS_VIEWS = MAIN_VIEWS + CONTROL_VIEWS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-dir", type=Path, default=DEFAULT_SMOKE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sf(value: Any, default: float = 0.0) -> float:
    return smoke.safe_float(value, default)


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def correct(y: int, prob: float) -> bool:
    return int(prob >= 0.5) == int(y)


def brier(y: int, prob: float) -> float:
    return (prob - y) ** 2


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def metric_delta(left: dict[str, Any] | None, right: dict[str, Any] | None) -> dict[str, Any]:
    left = left or {}
    right = right or {}
    output = {}
    for key in ["auroc", "auprc", "brier", "ece_5bin", "accuracy_at_0_5"]:
        if left.get(key) is None or right.get(key) is None:
            output[key] = None
        else:
            output[key] = left[key] - right[key]
    return output


def load_predictions(smoke_dir: Path) -> dict[str, dict[str, float]]:
    predictions: dict[str, dict[str, float]] = defaultdict(dict)
    for row in smoke.read_jsonl(smoke_dir / "predictions.jsonl"):
        if row.get("split_eval") != SPLIT_EVAL:
            continue
        predictions[str(row["prediction_id"])][str(row["view"])] = sf(row.get("probability"), 0.5)
    return dict(predictions)


def metric_lookup(summary: dict[str, Any], view: str, split_eval: str = SPLIT_EVAL) -> dict[str, Any]:
    for row in summary["metric_rows"]:
        if row["split_eval"] == split_eval and row["name"] == view:
            return row["metrics"]
    return {}


def comparison_lookup(summary: dict[str, Any], left: str, right: str, split_eval: str = SPLIT_EVAL) -> dict[str, Any]:
    for row in summary["comparisons"]:
        if row["split_eval"] == split_eval and row["left"] == left and row["right"] == right:
            return row["delta"]
    return metric_delta(metric_lookup(summary, left, split_eval), metric_lookup(summary, right, split_eval))


def target_y(row: dict[str, Any]) -> int:
    return smoke.target_y(row)


def endpoint_flags(row: dict[str, Any]) -> dict[str, float]:
    endpoint = row["baseline_inputs"].get(ENDPOINT_ONLY, {})
    return {
        "endpoint_object_floor_like_flag": sf(endpoint.get("endpoint_object_floor_like_flag"), 0.0),
        "endpoint_object_support_surface_like_flag": sf(endpoint.get("endpoint_object_support_surface_like_flag"), 0.0),
        "endpoint_object_wall_like_flag": sf(endpoint.get("endpoint_object_wall_like_flag"), 0.0),
        "endpoint_subject_room_surface_flag": sf(endpoint.get("endpoint_subject_room_surface_flag"), 0.0),
        "support_contact_gate": sf(endpoint.get("support_contact_gate"), 0.0),
        "relative_vertical_gate": sf(endpoint.get("relative_vertical_gate"), 0.0),
    }


def endpoint_flag_pattern(row: dict[str, Any]) -> str:
    flags = endpoint_flags(row)
    return "|".join(f"{key}={int(value >= 0.5)}" for key, value in sorted(flags.items()))


def endpoint_label_pattern(row: dict[str, Any]) -> str:
    ident = row["identity"]
    return "{subject}|{predicate}|{object}".format(
        subject=ident.get("subject_label"),
        predicate=ident.get("predicate_label"),
        object=ident.get("object_label"),
    )


def feature_fields(row: dict[str, Any]) -> dict[str, Any]:
    ident = row["identity"]
    c3 = row["baseline_inputs"][PRIMARY_REFERENCE]
    raw = row["baseline_inputs"].get("C1_raw_witness_only_v2", row["baseline_inputs"].get("raw_witness_only_v2", {}))
    semantic = row["baseline_inputs"].get("semantic_only", {})
    flags = endpoint_flags(row)
    return {
        "prediction_id": str(ident["prediction_id"]),
        "scan_id": ident.get("scan_id"),
        "subgraph_id": ident.get("subgraph_id"),
        "subject_id": ident.get("subject_id"),
        "subject_label": ident.get("subject_label"),
        "predicate_label": ident.get("predicate_label"),
        "predicate_family": ident.get("predicate_family"),
        "object_id": ident.get("object_id"),
        "object_label": ident.get("object_label"),
        "target": target_y(row),
        "target_reason": row.get("target", {}).get("target_reason"),
        "endpoint_flag_pattern": endpoint_flag_pattern(row),
        "endpoint_label_pattern": endpoint_label_pattern(row),
        "semantic_score_norm": sf(semantic.get("semantic_score_norm", c3.get("semantic_score_norm")), 0.0),
        "semantic_rank": sf(semantic.get("semantic_rank", c3.get("semantic_rank")), 9999.0),
        "p_geom_valid": sf(c3.get("p_geom_valid"), 0.5),
        "consistency_score": sf(c3.get("consistency_score"), 0.5),
        "strong_raw_witness_score": sf(raw.get("strong_raw_witness_score"), 0.5),
        "weak_raw_witness_score": sf(raw.get("weak_raw_witness_score"), 0.5),
        "support_distance_closeness": sf(raw.get("support_distance_closeness"), 0.0),
        "support_gap_closeness": sf(raw.get("support_gap_closeness"), 0.0),
        "support_iou_xy": sf(raw.get("support_iou_xy"), 0.0),
        "support_gap_abs": sf(raw.get("support_gap_abs"), 0.0),
        "support_gap_abs_local_z": sf(raw.get("support_gap_abs_local_z"), 0.0),
        "vertical_sign_agreement": sf(raw.get("vertical_sign_agreement"), 0.0),
        "vertical_interval_overlap": sf(raw.get("vertical_interval_overlap"), 0.0),
        "vertical_margin_abs_local_z": sf(raw.get("vertical_margin_abs_local_z"), 0.0),
        "vertical_signed_margin_local_z": sf(raw.get("vertical_signed_margin_local_z"), 0.0),
        **flags,
    }


def transfer_state(y: int, view_prob: float, reference_prob: float, view: str, reference: str) -> str:
    view_correct = correct(y, view_prob)
    reference_correct = correct(y, reference_prob)
    if view_correct and not reference_correct:
        return f"{view}_fixes_{reference}_error"
    if reference_correct and not view_correct:
        return f"{view}_adds_error_vs_{reference}"
    if view_correct and reference_correct:
        return "both_correct"
    return "both_wrong"


def error_direction(y: int, prob: float) -> str:
    if correct(y, prob):
        return "correct"
    return "false_positive" if y == 0 else "false_negative"


def build_row_diagnostics(rows: list[dict[str, Any]], predictions: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    outputs = []
    for row in rows:
        fields = feature_fields(row)
        row_id = fields["prediction_id"]
        y = int(fields["target"])
        pred = predictions[row_id]
        view_fields: dict[str, Any] = {}
        for view in ANALYSIS_VIEWS:
            prob = pred[view]
            view_fields[f"prob_{view}"] = prob
            view_fields[f"correct_{view}"] = correct(y, prob)
            view_fields[f"brier_{view}"] = brier(y, prob)
            view_fields[f"error_direction_{view}"] = error_direction(y, prob)
            if view != PRIMARY_REFERENCE:
                view_fields[f"transfer_{view}_vs_{PRIMARY_REFERENCE}"] = transfer_state(
                    y, prob, pred[PRIMARY_REFERENCE], view, PRIMARY_REFERENCE
                )
                view_fields[f"prob_delta_{view}_minus_{PRIMARY_REFERENCE}"] = prob - pred[PRIMARY_REFERENCE]
                view_fields[f"brier_delta_{view}_minus_{PRIMARY_REFERENCE}"] = brier(y, prob) - brier(
                    y, pred[PRIMARY_REFERENCE]
                )
        view_fields["c3_error_direction"] = error_direction(y, pred[PRIMARY_REFERENCE])
        view_fields["endpoint_only_transfer_vs_c3"] = transfer_state(y, pred[ENDPOINT_ONLY], pred[PRIMARY_REFERENCE], ENDPOINT_ONLY, PRIMARY_REFERENCE)
        outputs.append({**fields, **view_fields})
    return outputs


def metric_for(row_diagnostics: list[dict[str, Any]], view: str) -> dict[str, Any] | None:
    if not row_diagnostics:
        return None
    ys = [int(row["target"]) for row in row_diagnostics]
    probs = [sf(row[f"prob_{view}"], 0.5) for row in row_diagnostics]
    return smoke.metrics(ys, probs)


def transfer_summary(row_diagnostics: list[dict[str, Any]], view: str, reference: str) -> dict[str, Any]:
    counts = Counter()
    y_by_error = Counter()
    prob_deltas = []
    brier_deltas = []
    for row in row_diagnostics:
        y = int(row["target"])
        view_prob = sf(row[f"prob_{view}"], 0.5)
        ref_prob = sf(row[f"prob_{reference}"], 0.5)
        view_correct = correct(y, view_prob)
        ref_correct = correct(y, ref_prob)
        if view_correct and not ref_correct:
            counts["view_fixes_reference_error"] += 1
        elif ref_correct and not view_correct:
            counts["view_adds_error"] += 1
        elif view_correct and ref_correct:
            counts["both_correct"] += 1
        else:
            counts["both_wrong"] += 1
        y_by_error[(view, error_direction(y, view_prob))] += 1
        y_by_error[(reference, error_direction(y, ref_prob))] += 1
        prob_deltas.append(view_prob - ref_prob)
        brier_deltas.append(brier(y, view_prob) - brier(y, ref_prob))
    view_metrics = metric_for(row_diagnostics, view)
    ref_metrics = metric_for(row_diagnostics, reference)
    delta = metric_delta(view_metrics, ref_metrics)
    return {
        "view": view,
        "reference_view": reference,
        "rows": len(row_diagnostics),
        "positive": sum(int(row["target"]) for row in row_diagnostics),
        "negative": len(row_diagnostics) - sum(int(row["target"]) for row in row_diagnostics),
        "view_fixes_reference_error": counts["view_fixes_reference_error"],
        "view_adds_error": counts["view_adds_error"],
        "both_correct": counts["both_correct"],
        "both_wrong": counts["both_wrong"],
        "new_errors_minus_fixes": counts["view_adds_error"] - counts["view_fixes_reference_error"],
        "view_false_positive": y_by_error[(view, "false_positive")],
        "view_false_negative": y_by_error[(view, "false_negative")],
        "reference_false_positive": y_by_error[(reference, "false_positive")],
        "reference_false_negative": y_by_error[(reference, "false_negative")],
        "mean_prob_delta_view_minus_ref": mean(prob_deltas),
        "mean_brier_delta_view_minus_ref": mean(brier_deltas),
        "view_auroc": view_metrics.get("auroc") if view_metrics else None,
        "view_auprc": view_metrics.get("auprc") if view_metrics else None,
        "view_brier": view_metrics.get("brier") if view_metrics else None,
        "view_ece_5bin": view_metrics.get("ece_5bin") if view_metrics else None,
        "view_accuracy_at_0_5": view_metrics.get("accuracy_at_0_5") if view_metrics else None,
        "reference_auroc": ref_metrics.get("auroc") if ref_metrics else None,
        "reference_auprc": ref_metrics.get("auprc") if ref_metrics else None,
        "reference_brier": ref_metrics.get("brier") if ref_metrics else None,
        "reference_ece_5bin": ref_metrics.get("ece_5bin") if ref_metrics else None,
        "reference_accuracy_at_0_5": ref_metrics.get("accuracy_at_0_5") if ref_metrics else None,
        "delta_auroc": delta.get("auroc"),
        "delta_auprc": delta.get("auprc"),
        "delta_brier": delta.get("brier"),
        "delta_ece_5bin": delta.get("ece_5bin"),
        "delta_accuracy_at_0_5": delta.get("accuracy_at_0_5"),
    }


def build_candidate_transfer(row_diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs = []
    views = NEW_CANDIDATES + ["C8_endpoint_type_ablation_only", ENDPOINT_ONLY]
    slice_specs: list[tuple[str, str, list[dict[str, Any]]]] = [("all", "all", row_diagnostics)]
    for key in ["predicate_family", "predicate_label", "target_reason", "endpoint_flag_pattern"]:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in row_diagnostics:
            groups[str(row.get(key, "missing"))].append(row)
        for value, group in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
            slice_specs.append((key, value, group))
    for slice_name, slice_value, group in slice_specs:
        for view in views:
            output = transfer_summary(group, view, PRIMARY_REFERENCE)
            output.update({"slice_name": slice_name, "slice_value": slice_value})
            outputs.append(output)
    return outputs


def build_family_tradeoff(smoke_summary: dict[str, Any], row_diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    family_deltas = smoke_summary.get("family_deltas", [])
    by_key = {(row["predicate_family"], row["left"], row["right"]): row for row in family_deltas}
    outputs = []
    families = sorted({str(row["predicate_family"]) for row in row_diagnostics})
    for family in families:
        family_rows = [row for row in row_diagnostics if str(row["predicate_family"]) == family]
        for candidate in NEW_CANDIDATES:
            transfer = transfer_summary(family_rows, candidate, PRIMARY_REFERENCE)
            vs_c3 = by_key.get((family, candidate, PRIMARY_REFERENCE), {})
            vs_legacy = by_key.get((family, candidate, LEGACY_REFERENCE), {})
            outputs.append(
                {
                    "predicate_family": family,
                    "candidate": candidate,
                    "rows": len(family_rows),
                    "positive": transfer["positive"],
                    "negative": transfer["negative"],
                    "fixes_c3_errors": transfer["view_fixes_reference_error"],
                    "adds_errors_vs_c3": transfer["view_adds_error"],
                    "new_errors_minus_fixes_vs_c3": transfer["new_errors_minus_fixes"],
                    "delta_auprc_vs_c3": vs_c3.get("delta_auprc"),
                    "delta_brier_vs_c3": vs_c3.get("delta_brier"),
                    "delta_ece_vs_c3": vs_c3.get("delta_ece_5bin"),
                    "delta_acc_vs_c3": vs_c3.get("delta_accuracy_at_0_5"),
                    "delta_auprc_vs_legacy": vs_legacy.get("delta_auprc"),
                    "delta_brier_vs_legacy": vs_legacy.get("delta_brier"),
                    "delta_ece_vs_legacy": vs_legacy.get("delta_ece_5bin"),
                    "delta_acc_vs_legacy": vs_legacy.get("delta_accuracy_at_0_5"),
                    "mean_prob_delta_vs_c3": transfer["mean_prob_delta_view_minus_ref"],
                    "mean_brier_delta_vs_c3": transfer["mean_brier_delta_view_minus_ref"],
                }
            )
    return outputs


def endpoint_group_summary(row_diagnostics: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in row_diagnostics:
        groups[str(row.get(key, "missing"))].append(row)
    outputs = []
    for value, rows in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
        ys = [int(row["target"]) for row in rows]
        c3_acc = sum(1 for row in rows if row[f"correct_{PRIMARY_REFERENCE}"]) / len(rows)
        endpoint_acc = sum(1 for row in rows if row[f"correct_{ENDPOINT_ONLY}"]) / len(rows)
        positive_rate = sum(ys) / len(ys)
        outputs.append(
            {
                "group_key": key,
                "group_value": value,
                "rows": len(rows),
                "positive": sum(ys),
                "negative": len(ys) - sum(ys),
                "positive_rate": positive_rate,
                "purity_from_balance": abs(positive_rate - 0.5),
                "is_label_pure": positive_rate in {0.0, 1.0},
                "mean_prob_c3": mean([sf(row[f"prob_{PRIMARY_REFERENCE}"], 0.5) for row in rows]),
                "mean_prob_endpoint_only": mean([sf(row[f"prob_{ENDPOINT_ONLY}"], 0.5) for row in rows]),
                "accuracy_c3": c3_acc,
                "accuracy_endpoint_only": endpoint_acc,
                "accuracy_gap_endpoint_minus_c3": endpoint_acc - c3_acc,
            }
        )
    return outputs


def endpoint_shortcut_summary(row_diagnostics: list[dict[str, Any]], smoke_summary: dict[str, Any]) -> dict[str, Any]:
    flag_groups = endpoint_group_summary(row_diagnostics, "endpoint_flag_pattern")
    label_groups = endpoint_group_summary(row_diagnostics, "endpoint_label_pattern")
    transfer = transfer_summary(row_diagnostics, ENDPOINT_ONLY, PRIMARY_REFERENCE)
    delta = comparison_lookup(smoke_summary, ENDPOINT_ONLY, PRIMARY_REFERENCE)
    flag_rows_in_pure_groups = sum(row["rows"] for row in flag_groups if row["is_label_pure"])
    label_rows_in_pure_groups = sum(row["rows"] for row in label_groups if row["is_label_pure"] and row["rows"] >= 2)
    severe = (
        sf(delta.get("auprc")) > 0.20
        and sf(delta.get("brier"), 1.0) < -0.10
        and transfer["new_errors_minus_fixes"] < -20
    )
    return {
        "endpoint_delta_vs_c3": delta,
        "endpoint_transfer_vs_c3": transfer,
        "endpoint_flag_group_count": len(flag_groups),
        "endpoint_label_group_count": len(label_groups),
        "endpoint_flag_rows_in_pure_groups": flag_rows_in_pure_groups,
        "endpoint_label_rows_in_pure_groups_min2": label_rows_in_pure_groups,
        "endpoint_shortcut_severity": "severe" if severe else "moderate_or_unresolved",
        "flag_groups": flag_groups,
        "label_groups": label_groups,
    }


def build_feature_target_summary(row_diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs = []
    feature_keys = [
        "semantic_score_norm",
        "semantic_rank",
        "p_geom_valid",
        "consistency_score",
        "strong_raw_witness_score",
        "support_iou_xy",
        "support_gap_closeness",
        "support_distance_closeness",
        "vertical_sign_agreement",
        "vertical_interval_overlap",
        "vertical_margin_abs_local_z",
        "endpoint_object_floor_like_flag",
        "endpoint_object_support_surface_like_flag",
        "endpoint_object_wall_like_flag",
        "endpoint_subject_room_surface_flag",
    ]
    slice_specs: list[tuple[str, str, list[dict[str, Any]]]] = [("all", "all", row_diagnostics)]
    for key in ["predicate_family", "predicate_label", "endpoint_flag_pattern"]:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in row_diagnostics:
            groups[str(row.get(key, "missing"))].append(row)
        for value, group in groups.items():
            slice_specs.append((key, value, group))
    for slice_name, slice_value, rows in slice_specs:
        for target in [0, 1]:
            selected = [row for row in rows if int(row["target"]) == target]
            if not selected:
                continue
            output: dict[str, Any] = {
                "slice_name": slice_name,
                "slice_value": slice_value,
                "target": target,
                "rows": len(selected),
            }
            for key in feature_keys:
                output[f"mean_{key}"] = mean([sf(row.get(key), 0.0) for row in selected])
            for view in [PRIMARY_REFERENCE, "C4_calibrated_linear_v2", "C6_family_gated_calibrated_mixture", ENDPOINT_ONLY]:
                output[f"mean_prob_{view}"] = mean([sf(row[f"prob_{view}"], 0.5) for row in selected])
                output[f"accuracy_{view}"] = sum(1 for row in selected if row[f"correct_{view}"]) / len(selected)
            outputs.append(output)
    return outputs


def representative_rows(row_diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        ("c4_support_fixes_c3", "C4_calibrated_linear_v2", "support_contact", True),
        ("c4_vertical_adds_error", "C4_calibrated_linear_v2", "relative_vertical", False),
        ("c6_vertical_fixes_c3", "C6_family_gated_calibrated_mixture", "relative_vertical", True),
        ("c6_support_adds_error", "C6_family_gated_calibrated_mixture", "support_contact", False),
        ("c7_vertical_fixes_c3", "C7_limited_interaction_model", "relative_vertical", True),
        ("c7_support_adds_error", "C7_limited_interaction_model", "support_contact", False),
        ("endpoint_only_fixes_c3", ENDPOINT_ONLY, None, True),
        ("endpoint_only_adds_error", ENDPOINT_ONLY, None, False),
    ]
    outputs = []
    for category, view, family, want_fix in specs:
        selected = []
        for row in row_diagnostics:
            if family is not None and row["predicate_family"] != family:
                continue
            y = int(row["target"])
            view_correct = correct(y, sf(row[f"prob_{view}"], 0.5))
            c3_correct = correct(y, sf(row[f"prob_{PRIMARY_REFERENCE}"], 0.5))
            if want_fix and not (view_correct and not c3_correct):
                continue
            if not want_fix and not (c3_correct and not view_correct):
                continue
            selected.append(row)
        selected = sorted(
            selected,
            key=lambda row: abs(sf(row[f"brier_delta_{view}_minus_{PRIMARY_REFERENCE}"], 0.0)),
            reverse=True,
        )[:8]
        for row in selected:
            outputs.append(
                {
                    "category": category,
                    "view": view,
                    "prediction_id": row["prediction_id"],
                    "scan_id": row["scan_id"],
                    "subject_label": row["subject_label"],
                    "predicate_label": row["predicate_label"],
                    "object_label": row["object_label"],
                    "predicate_family": row["predicate_family"],
                    "target": row["target"],
                    "target_reason": row["target_reason"],
                    "endpoint_flag_pattern": row["endpoint_flag_pattern"],
                    "endpoint_label_pattern": row["endpoint_label_pattern"],
                    "prob_c3": row[f"prob_{PRIMARY_REFERENCE}"],
                    "prob_view": row[f"prob_{view}"],
                    "prob_endpoint_only": row[f"prob_{ENDPOINT_ONLY}"],
                    "strong_raw_witness_score": row["strong_raw_witness_score"],
                    "p_geom_valid": row["p_geom_valid"],
                    "support_iou_xy": row["support_iou_xy"],
                    "support_gap_closeness": row["support_gap_closeness"],
                    "vertical_sign_agreement": row["vertical_sign_agreement"],
                    "vertical_margin_abs_local_z": row["vertical_margin_abs_local_z"],
                }
            )
    return outputs


def build_diagnosis(
    smoke_summary: dict[str, Any],
    family_tradeoff: list[dict[str, Any]],
    endpoint_summary: dict[str, Any],
) -> list[str]:
    diagnosis = []
    if endpoint_summary["endpoint_shortcut_severity"] == "severe":
        diagnosis.append("endpoint_type_shortcut_dominates_current_target_slice")
    for candidate in NEW_CANDIDATES:
        delta = comparison_lookup(smoke_summary, candidate, PRIMARY_REFERENCE)
        if sf(delta.get("auprc")) < 0.0:
            diagnosis.append(f"{candidate}_does_not_improve_ranking_over_c3")
    by_key = {(row["predicate_family"], row["candidate"]): row for row in family_tradeoff}
    c4_support = by_key.get(("support_contact", "C4_calibrated_linear_v2"), {})
    c4_vertical = by_key.get(("relative_vertical", "C4_calibrated_linear_v2"), {})
    if sf(c4_support.get("delta_auprc_vs_c3")) > 0.0 and sf(c4_vertical.get("delta_auprc_vs_c3")) < 0.0:
        diagnosis.append("c4_calibrated_linear_helps_support_contact_but_breaks_relative_vertical")
    for candidate in ["C6_family_gated_calibrated_mixture", "C7_limited_interaction_model"]:
        support = by_key.get(("support_contact", candidate), {})
        vertical = by_key.get(("relative_vertical", candidate), {})
        if sf(vertical.get("delta_auprc_vs_c3")) > 0.0 and sf(support.get("delta_auprc_vs_c3")) < 0.0:
            diagnosis.append(f"{candidate}_trades_support_contact_loss_for_relative_vertical_gain")
    c3_vs_global = comparison_lookup(smoke_summary, PRIMARY_REFERENCE, "K0_global_raw_witness_shuffle")
    c3_vs_wrong = comparison_lookup(smoke_summary, PRIMARY_REFERENCE, "K2_wrong_pair_raw_witness")
    if sf(c3_vs_global.get("auprc")) > 0.10 and sf(c3_vs_wrong.get("auprc")) > 0.10:
        diagnosis.append("pair_specific_raw_witness_signal_survives_shuffle_and_wrong_pair_controls")
    diagnosis.append("combiner_capacity_is_not_the_current_primary_blocker")
    diagnosis.append("next_step_should_control_endpoint_pattern_before_family_separated_posterior")
    return diagnosis


def write_report(path: Path, summary: dict[str, Any]) -> None:
    endpoint = summary["endpoint_shortcut"]
    endpoint_delta = endpoint["endpoint_delta_vs_c3"]
    endpoint_transfer = endpoint["endpoint_transfer_vs_c3"]
    lines = [
        "# H002 Raw-Witness V2 Combiner Error Analysis",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only post-hoc analysis of 129 combiner-smoke predictions.",
        "- No validation/test rows are used.",
        "- No new posterior model is trained in this step.",
        "- Endpoint/object-type features are analyzed as shortcut controls, not accepted main evidence.",
        "- Results are hypothesis-stage diagnostics, not paper-level metrics.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Diagnosis",
        "",
    ]
    lines.extend(f"- `{item}`" for item in summary["diagnosis"])
    lines.extend(
        [
            "",
            "## Endpoint Shortcut",
            "",
            "| Control | dAUROC vs C3 | dAUPRC vs C3 | dBrier vs C3 | dECE vs C3 | dAcc vs C3 | Fixes C3 | Adds Error | New-Fix |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            (
                f"| `{ENDPOINT_ONLY}` | {fmt(endpoint_delta.get('auroc'))} | {fmt(endpoint_delta.get('auprc'))} | "
                f"{fmt(endpoint_delta.get('brier'))} | {fmt(endpoint_delta.get('ece_5bin'))} | "
                f"{fmt(endpoint_delta.get('accuracy_at_0_5'))} | {endpoint_transfer['view_fixes_reference_error']} | "
                f"{endpoint_transfer['view_adds_error']} | {endpoint_transfer['new_errors_minus_fixes']} |"
            ),
            "",
            f"Endpoint flag pure-group rows: `{endpoint['endpoint_flag_rows_in_pure_groups']}` / `{summary['rows']}`",
            f"Endpoint label pure-group rows with group size >=2: `{endpoint['endpoint_label_rows_in_pure_groups_min2']}` / `{summary['rows']}`",
            "",
            "## Candidate Transfer Vs C3",
            "",
            "| Candidate | Fixes C3 | Adds Error | Both Correct | Both Wrong | New-Fix | dAUPRC | dBrier | dECE |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    all_transfer = [
        row
        for row in summary["candidate_transfer"]
        if row["slice_name"] == "all" and row["slice_value"] == "all" and row["view"] in NEW_CANDIDATES
    ]
    for row in all_transfer:
        lines.append(
            f"| `{row['view']}` | {row['view_fixes_reference_error']} | {row['view_adds_error']} | "
            f"{row['both_correct']} | {row['both_wrong']} | {row['new_errors_minus_fixes']} | "
            f"{fmt(row['delta_auprc'])} | {fmt(row['delta_brier'])} | {fmt(row['delta_ece_5bin'])} |"
        )
    lines.extend(
        [
            "",
            "## Family Tradeoff",
            "",
            "| Family | Candidate | Fixes C3 | Adds Error | New-Fix | dAUPRC vs C3 | dBrier vs C3 | dAUPRC vs Legacy |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["family_tradeoff"]:
        if row["candidate"] not in ["C4_calibrated_linear_v2", "C6_family_gated_calibrated_mixture", "C7_limited_interaction_model"]:
            continue
        lines.append(
            f"| `{row['predicate_family']}` | `{row['candidate']}` | {row['fixes_c3_errors']} | "
            f"{row['adds_errors_vs_c3']} | {row['new_errors_minus_fixes_vs_c3']} | "
            f"{fmt(row['delta_auprc_vs_c3'])} | {fmt(row['delta_brier_vs_c3'])} | "
            f"{fmt(row['delta_auprc_vs_legacy'])} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Next TODO",
            "",
            "```text",
            summary["next_todo"],
            "```",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    smoke_dir = as_abs(args.smoke_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = smoke.read_jsonl(smoke_dir / "combiner_rows.jsonl")
    smoke_summary = read_json(smoke_dir / "summary.json")
    predictions = load_predictions(smoke_dir)

    validation_errors = []
    for row in rows:
        row_id = str(row["identity"]["prediction_id"])
        if row_id not in predictions:
            validation_errors.append({"error_type": "missing_prediction_row", "prediction_id": row_id})
            continue
        missing = sorted(set(ANALYSIS_VIEWS) - set(predictions[row_id]))
        if missing:
            validation_errors.append({"error_type": "missing_prediction_views", "prediction_id": row_id, "missing": missing})
        provenance = row.get("provenance", {})
        if provenance.get("validation_usage") is not False or provenance.get("test_usage") is not False:
            validation_errors.append({"error_type": "split_boundary_violation", "prediction_id": row_id})
    if smoke_summary.get("status") != "full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_no_new_primary":
        validation_errors.append({"error_type": "unexpected_smoke_status", "status": smoke_summary.get("status")})

    row_diagnostics = build_row_diagnostics(rows, predictions) if not validation_errors else []
    candidate_transfer = build_candidate_transfer(row_diagnostics) if row_diagnostics else []
    family_tradeoff = build_family_tradeoff(smoke_summary, row_diagnostics) if row_diagnostics else []
    endpoint_shortcut = endpoint_shortcut_summary(row_diagnostics, smoke_summary) if row_diagnostics else {}
    feature_summary = build_feature_target_summary(row_diagnostics) if row_diagnostics else []
    representatives = representative_rows(row_diagnostics) if row_diagnostics else []
    diagnosis = build_diagnosis(smoke_summary, family_tradeoff, endpoint_shortcut) if row_diagnostics else ["input_validation_failed"]

    target_counts = Counter(target_y(row) for row in rows)
    status = (
        "full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_input_errors"
        if validation_errors
        else "full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_ready_endpoint_control_needed"
    )
    next_todo = (
        "fix_revised_sampling_all_label_ready_raw_witness_v2_combiner_error_analysis_inputs"
        if validation_errors
        else "revised_sampling_all_label_ready_endpoint_controlled_resampling_plan"
    )
    decision = (
        "Input contract errors must be fixed before interpreting combiner failures."
        if validation_errors
        else (
            "Do not pursue a higher-capacity or family-separated posterior as the immediate next step. "
            "The current blocker is target/evidence shortcut: endpoint-only controls explain the 134-row slice "
            "more strongly than the typed raw-witness posterior. Build an endpoint-controlled resampling protocol "
            "first; only after the shortcut is reduced should family-separated support/vertical posterior design be tested."
        )
    )

    summary = {
        "schema_version": "h002_raw_witness_v2_combiner_error_analysis_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "input_paths": {
            "smoke_dir": rel_path(smoke_dir),
            "combiner_rows": rel_path(smoke_dir / "combiner_rows.jsonl"),
            "predictions": rel_path(smoke_dir / "predictions.jsonl"),
            "smoke_summary": rel_path(smoke_dir / "summary.json"),
        },
        "output_dir": rel_path(output_dir),
        "boundary": {
            "split_policy": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "new_model_training": False,
            "endpoint_as_main_model_evidence": False,
            "paper_metric_evidence": False,
        },
        "rows": len(rows),
        "positive": target_counts[1],
        "negative": target_counts[0],
        "validation_errors": validation_errors,
        "diagnosis": diagnosis,
        "endpoint_shortcut": endpoint_shortcut,
        "candidate_transfer": candidate_transfer,
        "family_tradeoff": family_tradeoff,
        "decision": decision,
        "next_todo": next_todo,
    }

    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "row_diagnostics.jsonl", row_diagnostics)
    write_csv(output_dir / "candidate_transfer.csv", candidate_transfer)
    write_csv(output_dir / "family_tradeoff.csv", family_tradeoff)
    if endpoint_shortcut:
        write_csv(output_dir / "endpoint_flag_groups.csv", endpoint_shortcut["flag_groups"])
        write_csv(output_dir / "endpoint_label_groups.csv", endpoint_shortcut["label_groups"])
    else:
        write_csv(output_dir / "endpoint_flag_groups.csv", [])
        write_csv(output_dir / "endpoint_label_groups.csv", [])
    write_csv(output_dir / "feature_target_summary.csv", feature_summary)
    write_jsonl(output_dir / "representative_rows.jsonl", representatives)
    write_report(output_dir / "report.md", summary)

    print(f"status={summary['status']}")
    print(f"rows={summary['rows']} pos={summary['positive']} neg={summary['negative']}")
    if endpoint_shortcut:
        delta = endpoint_shortcut["endpoint_delta_vs_c3"]
        transfer = endpoint_shortcut["endpoint_transfer_vs_c3"]
        print(f"endpoint_d_auprc_vs_c3={fmt(delta.get('auprc'))}")
        print(f"endpoint_new_errors_minus_fixes={transfer['new_errors_minus_fixes']}")
        print(f"endpoint_shortcut_severity={endpoint_shortcut['endpoint_shortcut_severity']}")
    print(f"next={summary['next_todo']}")


if __name__ == "__main__":
    main()
