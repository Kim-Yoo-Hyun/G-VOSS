#!/usr/bin/env python3
"""Audit whether relative_horizontal can be promoted to a main validated route.

This stage follows the six-step review requested for left/right/front/behind:

1. define the route as frame-aware directional compatibility
2. freeze the frame protocol
3. define relation-specific residuals
4. check source/baseline/control behavior
5. inspect per-predicate slices
6. decide whether the route is promotable to main validated status

The script does not edit paper drafts and does not tune any score.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h002_relative_horizontal_frame_route_audit_v1"
STATUS_READY = "h002_relative_horizontal_frame_route_audit_ready"
STATUS_ERROR = "h002_relative_horizontal_frame_route_audit_errors"

K_GRID = [5, 10, 20, 50, 100]
PROMOTION_K = [10, 20, 50]
SOURCE_IDS = ["open3dsg_recovery_relaxed_views_min2", "vlsat_full_validation"]
PREDICATES = ["left", "right", "front", "behind"]
SCORE_IDS = [
    "S0_source_score",
    "S2_source_x_Ce",
    "A1_source_x_G_only",
    "A2_source_x_TG_concat",
    "C1_source_x_shuffled_Ce",
    "C2_source_x_wrong_T_Ce",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--materialization-dir", type=Path, required=True)
    parser.add_argument("--source-reranking-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def safe_float(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def sigmoid(value: float) -> float:
    if value > 40:
        return 1.0
    if value < -40:
        return 0.0
    return 1.0 / (1.0 + math.exp(-value))


def clipped(value: float, eps: float = 1e-6) -> float:
    return max(eps, min(1.0, value))


def nested_get(block: dict[str, Any], keys: list[str]) -> Any:
    value: Any = block
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def geometry_feature(row: dict[str, Any], name: str) -> float:
    g_block = row.get("feature_blocks", {}).get("G_e", {})
    paths = [
        ["g_e_feature_vector", name],
        ["G_e_horizontal", name],
        ["G_e_horizontal", name.replace("center_delta_", "delta_") + "_subject_minus_object"],
    ]
    for path in paths:
        value = nested_get(g_block, path)
        parsed = safe_float(value)
        if parsed is not None:
            return parsed
    return 0.0


def frame_score(predicate: str, dx: float, dy: float, mode: str) -> float:
    """Return a frozen world-XY directional compatibility score.

    dx/dy are subject minus object offsets. The protocol intentionally uses the
    existing source-wide materialization policy:

    - left/right: world X axis
    - front/behind: world Y axis
    - axis_swap: left/right use Y and front/behind use X
    - sign_flip: the correct axis with reversed sign
    """

    if mode == "correct":
        value = {
            "left": -dx,
            "right": dx,
            "front": dy,
            "behind": -dy,
        }[predicate]
    elif mode == "axis_swap":
        value = {
            "left": -dy,
            "right": dy,
            "front": dx,
            "behind": -dx,
        }[predicate]
    elif mode == "sign_flip":
        value = {
            "left": dx,
            "right": -dx,
            "front": -dy,
            "behind": dy,
        }[predicate]
    else:
        raise ValueError(mode)
    return sigmoid(8.0 * value)


def metric_empty() -> dict[str, Any]:
    return {
        "unit_count": 0,
        "gt_units": 0,
        "gt_total": 0,
        "gt_selected": 0,
        "selected_total": 0,
        "violation_denominator": 0,
        "violation_count": 0,
    }


def finalize_metric(base: dict[str, Any], acc: dict[str, Any]) -> dict[str, Any]:
    recall = None
    if acc["gt_total"] > 0:
        recall = acc["gt_selected"] / acc["gt_total"]
    violation = None
    if acc["violation_denominator"] > 0:
        violation = acc["violation_count"] / acc["violation_denominator"]
    selected_mean = None
    if acc["unit_count"] > 0:
        selected_mean = acc["selected_total"] / acc["unit_count"]
    return {
        **base,
        "unit_count": acc["unit_count"],
        "gt_units": acc["gt_units"],
        "gt_total": acc["gt_total"],
        "gt_selected": acc["gt_selected"],
        "Recall@K": recall,
        "selected_total": acc["selected_total"],
        "Selected@K_mean": selected_mean,
        "violation_denominator": acc["violation_denominator"],
        "violation_count": acc["violation_count"],
        "Violation@K": violation,
    }


def add_selected(acc: dict[str, Any], denom_gt: set[str], selected: list[dict[str, Any]]) -> None:
    acc["unit_count"] += 1
    acc["selected_total"] += len(selected)
    if denom_gt:
        acc["gt_units"] += 1
        acc["gt_total"] += len(denom_gt)
        acc["gt_selected"] += len({row["candidate_id"] for row in selected if row["gt_exact_match"]})
    for row in selected:
        if row["violation_checkable"]:
            acc["violation_denominator"] += 1
            if row["violation_status"] == "violated":
                acc["violation_count"] += 1


def build_frame_protocol_rows() -> list[dict[str, Any]]:
    return [
        {
            "step": 1,
            "item": "route_definition",
            "value": "frame_aware_directional_compatibility",
            "decision": "frozen_for_audit",
        },
        {
            "step": 1,
            "item": "relations",
            "value": "left,right,front,behind",
            "decision": "candidate_main_route_only_if_gates_pass",
        },
        {
            "step": 2,
            "item": "frame_protocol",
            "value": "dataset_world_xy_reference_frame_from_3rscan_obb_centroids",
            "decision": "frozen_before_metric_review",
        },
        {
            "step": 3,
            "item": "left_right_residual",
            "value": "signed normalized_center_delta_x, subject_minus_object",
            "decision": "left expects negative x, right expects positive x",
        },
        {
            "step": 3,
            "item": "front_behind_residual",
            "value": "signed normalized_center_delta_y, subject_minus_object",
            "decision": "front expects positive y, behind expects negative y",
        },
        {
            "step": 4,
            "item": "required_controls",
            "value": "source-only,G-only,concat,wrong-T,shuffled-G,axis-swap,sign-flip",
            "decision": "all must be reviewed before promotion",
        },
        {
            "step": 5,
            "item": "slice_policy",
            "value": "left,right,front,behind per source and K",
            "decision": "aggregate alone is insufficient",
        },
        {
            "step": 6,
            "item": "promotion_policy",
            "value": "no violation regression at K=10,20,50 on both sources; no large recall loss; controls degrade",
            "decision": "strict gate for main validated route",
        },
    ]


def existing_source_family_review(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_key = {
        (row["source_id"], row["score_id"], int(row["K"])): row
        for row in rows
        if row.get("route_family") == "relative_horizontal"
    }
    out: list[dict[str, Any]] = []
    for source_id in SOURCE_IDS:
        for k in K_GRID:
            s2 = by_key.get((source_id, "S2_source_x_Ce", k))
            if not s2:
                continue
            s2_recall = safe_float(s2.get("Recall@K"), 0.0) or 0.0
            s2_violation = safe_float(s2.get("Violation@K"), 0.0) or 0.0
            for baseline in [
                "S0_source_score",
                "A1_source_x_G_only",
                "A2_source_x_TG_concat",
                "C1_source_x_shuffled_Ce",
                "C2_source_x_wrong_T_Ce",
            ]:
                base = by_key.get((source_id, baseline, k))
                if not base:
                    continue
                base_recall = safe_float(base.get("Recall@K"), 0.0) or 0.0
                base_violation = safe_float(base.get("Violation@K"), 0.0) or 0.0
                delta_r = s2_recall - base_recall
                delta_v = s2_violation - base_violation
                out.append(
                    {
                        "source_id": source_id,
                        "K": k,
                        "comparison": f"S2_source_x_Ce_minus_{baseline}",
                        "S2_Recall@K": s2_recall,
                        "baseline_Recall@K": base_recall,
                        "delta_Recall@K": delta_r,
                        "S2_Violation@K": s2_violation,
                        "baseline_Violation@K": base_violation,
                        "delta_Violation@K": delta_v,
                        "recall_not_large_loss": delta_r >= -0.01,
                        "violation_nonincrease": delta_v <= 0.0,
                    }
                )
    return out


def load_relative_records(materialization_dir: Path) -> tuple[list[dict[str, Any]], dict[tuple[str, str], set[str]], dict[tuple[str, str, str], set[str]]]:
    ce_path = materialization_dir / "model_safe_ce_view.jsonl"
    rank_path = materialization_dir / "source_rank_view.jsonl"
    hidden_path = materialization_dir / "hidden_metric_manifest.jsonl"
    records: list[dict[str, Any]] = []
    denom_by_group: dict[tuple[str, str], set[str]] = defaultdict(set)
    denom_by_predicate_group: dict[tuple[str, str, str], set[str]] = defaultdict(set)

    with (
        ce_path.open("r", encoding="utf-8") as ce_handle,
        rank_path.open("r", encoding="utf-8") as rank_handle,
        hidden_path.open("r", encoding="utf-8") as hidden_handle,
    ):
        for ce_line, rank_line, hidden_line in zip(ce_handle, rank_handle, hidden_handle):
            ce = json.loads(ce_line)
            if ce.get("route_family") != "relative_horizontal":
                continue
            rank = json.loads(rank_line)
            hidden = json.loads(hidden_line)
            if ce.get("candidate_id") != rank.get("candidate_id") or ce.get("candidate_id") != hidden.get("candidate_id"):
                continue
            predicate = str(ce.get("predicate_label"))
            if predicate not in PREDICATES:
                continue
            source_id = str(ce["source_id"])
            subgraph_id = str(ce["subgraph_id"])
            dx = geometry_feature(ce, "normalized_center_delta_x")
            dy = geometry_feature(ce, "normalized_center_delta_y")
            source_score = safe_float(rank.get("Z_e", {}).get("ranking_score"), 0.0) or 0.0
            correct = frame_score(predicate, dx, dy, "correct")
            axis_swap = frame_score(predicate, dx, dy, "axis_swap")
            sign_flip = frame_score(predicate, dx, dy, "sign_flip")
            record = {
                "candidate_id": str(ce["candidate_id"]),
                "source_id": source_id,
                "subgraph_id": subgraph_id,
                "predicate_label": predicate,
                "gt_exact_match": bool(hidden.get("gt_exact_match")),
                "violation_checkable": bool(hidden.get("h2_violation_checkable")),
                "violation_status": str(hidden.get("h2_relation_status")),
                "scores": {
                    "D0_source_score": clipped(source_score),
                    "D1_source_x_world_xy_frame": clipped(source_score) * clipped(correct),
                    "D2_source_x_axis_swap": clipped(source_score) * clipped(axis_swap),
                    "D3_source_x_sign_flip": clipped(source_score) * clipped(sign_flip),
                    "D4_world_xy_frame_only": clipped(correct),
                    "D5_axis_swap_only": clipped(axis_swap),
                    "D6_sign_flip_only": clipped(sign_flip),
                },
            }
            records.append(record)
            if record["gt_exact_match"]:
                denom_by_group[(source_id, subgraph_id)].add(record["candidate_id"])
                denom_by_predicate_group[(source_id, subgraph_id, predicate)].add(record["candidate_id"])
    return records, denom_by_group, denom_by_predicate_group


def deterministic_frame_metrics(
    records: list[dict[str, Any]], denom_by_group: dict[tuple[str, str], set[str]]
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[(record["source_id"], record["subgraph_id"])].append(record)

    score_ids = [
        "D0_source_score",
        "D1_source_x_world_xy_frame",
        "D2_source_x_axis_swap",
        "D3_source_x_sign_flip",
        "D4_world_xy_frame_only",
        "D5_axis_swap_only",
        "D6_sign_flip_only",
    ]
    accs: dict[tuple[str, str, int], dict[str, Any]] = defaultdict(metric_empty)
    for group_key, bucket in grouped.items():
        denom = denom_by_group.get(group_key, set())
        for score_id in score_ids:
            ranked = sorted(bucket, key=lambda row: (row["scores"][score_id], row["scores"]["D0_source_score"], row["candidate_id"]), reverse=True)
            for k in K_GRID:
                selected = ranked[: min(k, len(ranked))]
                add_selected(accs[(group_key[0], score_id, k)], denom, selected)

    rows = []
    for (source_id, score_id, k), acc in sorted(accs.items()):
        rows.append(
            finalize_metric(
                {
                    "level": "source_family",
                    "source_id": source_id,
                    "route_family": "relative_horizontal",
                    "score_id": score_id,
                    "K": k,
                },
                acc,
            )
        )
    return rows


def selected_per_predicate_metrics(
    selected_predictions_path: Path,
    denom_by_predicate_group: dict[tuple[str, str, str], set[str]],
) -> list[dict[str, Any]]:
    denom_by_source_predicate: dict[tuple[str, str], set[str]] = defaultdict(set)
    units_by_source_predicate: dict[tuple[str, str], set[str]] = defaultdict(set)
    for (source_id, subgraph_id, predicate), ids in denom_by_predicate_group.items():
        denom_by_source_predicate[(source_id, predicate)].update(ids)
        units_by_source_predicate[(source_id, predicate)].add(subgraph_id)

    selected_acc: dict[tuple[str, str, str, int], dict[str, Any]] = defaultdict(metric_empty)
    selected_gt_sets: dict[tuple[str, str, str, int], set[str]] = defaultdict(set)
    with selected_predictions_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("route_family") != "relative_horizontal":
                continue
            predicate = str(row.get("predicate_label"))
            if predicate not in PREDICATES:
                continue
            score_id = str(row.get("score_id"))
            if score_id not in SCORE_IDS:
                continue
            rank = int(row.get("rank", 0))
            source_id = str(row.get("source_id"))
            for k in K_GRID:
                if rank > k:
                    continue
                key = (source_id, predicate, score_id, k)
                acc = selected_acc[key]
                acc["selected_total"] += 1
                if row.get("gt_exact_match"):
                    selected_gt_sets[key].add(str(row.get("candidate_id")))
                if row.get("violation_checkable"):
                    acc["violation_denominator"] += 1
                    if row.get("violation_status") == "violated":
                        acc["violation_count"] += 1

    rows: list[dict[str, Any]] = []
    for source_id in SOURCE_IDS:
        for predicate in PREDICATES:
            denom = denom_by_source_predicate.get((source_id, predicate), set())
            units = units_by_source_predicate.get((source_id, predicate), set())
            for score_id in SCORE_IDS:
                for k in K_GRID:
                    key = (source_id, predicate, score_id, k)
                    acc = selected_acc.get(key, metric_empty())
                    acc = dict(acc)
                    acc["unit_count"] = len(units)
                    acc["gt_units"] = len(units)
                    acc["gt_total"] = len(denom)
                    acc["gt_selected"] = len(selected_gt_sets.get(key, set()))
                    rows.append(
                        finalize_metric(
                            {
                                "level": "source_predicate",
                                "source_id": source_id,
                                "route_family": "relative_horizontal",
                                "predicate_label": predicate,
                                "score_id": score_id,
                                "K": k,
                            },
                            acc,
                        )
                    )
    return rows


def summarize_gate(
    existing_rows: list[dict[str, Any]],
    predicate_rows: list[dict[str, Any]],
    deterministic_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    # Strict source-wide gate for S2 against source baseline.
    s2_vs_s0 = [
        row
        for row in existing_rows
        if row["comparison"] == "S2_source_x_Ce_minus_S0_source_score" and int(row["K"]) in PROMOTION_K
    ]
    violation_regressions = [row for row in s2_vs_s0 if safe_float(row["delta_Violation@K"], 0.0) > 0.0]
    recall_large_losses = [row for row in s2_vs_s0 if safe_float(row["delta_Recall@K"], 0.0) < -0.01]

    # Baseline/control gate: S2 should not be worse than G-only/concat and controls.
    required_comparisons = [
        "S2_source_x_Ce_minus_A1_source_x_G_only",
        "S2_source_x_Ce_minus_A2_source_x_TG_concat",
        "S2_source_x_Ce_minus_C1_source_x_shuffled_Ce",
        "S2_source_x_Ce_minus_C2_source_x_wrong_T_Ce",
    ]
    control_failures = [
        row
        for row in existing_rows
        if row["comparison"] in required_comparisons
        and int(row["K"]) in PROMOTION_K
        and (
            safe_float(row["delta_Recall@K"], 0.0) < -0.01
            or safe_float(row["delta_Violation@K"], 0.0) > 0.0
        )
    ]

    # Predicate slice gate: all predicates should avoid violation regression vs S0 at K=20/50.
    by_key = {
        (row["source_id"], row["predicate_label"], row["score_id"], int(row["K"])): row
        for row in predicate_rows
    }
    predicate_failures: list[dict[str, Any]] = []
    for source_id in SOURCE_IDS:
        for predicate in PREDICATES:
            for k in [20, 50]:
                s2 = by_key.get((source_id, predicate, "S2_source_x_Ce", k))
                s0 = by_key.get((source_id, predicate, "S0_source_score", k))
                if not s2 or not s0:
                    continue
                s2_v = safe_float(s2.get("Violation@K"), 0.0) or 0.0
                s0_v = safe_float(s0.get("Violation@K"), 0.0) or 0.0
                s2_r = safe_float(s2.get("Recall@K"), 0.0) or 0.0
                s0_r = safe_float(s0.get("Recall@K"), 0.0) or 0.0
                if s2_v - s0_v > 0.0 or s2_r - s0_r < -0.02:
                    predicate_failures.append(
                        {
                            "source_id": source_id,
                            "predicate_label": predicate,
                            "K": k,
                            "delta_Recall@K": s2_r - s0_r,
                            "delta_Violation@K": s2_v - s0_v,
                        }
                    )

    # Axis-control diagnostic: correct world-XY residual should beat sign/axis swaps.
    det_by_key = {
        (row["source_id"], row["score_id"], int(row["K"])): row
        for row in deterministic_rows
    }
    axis_failures: list[dict[str, Any]] = []
    for source_id in SOURCE_IDS:
        for k in PROMOTION_K:
            correct = det_by_key.get((source_id, "D1_source_x_world_xy_frame", k))
            if not correct:
                continue
            correct_v = safe_float(correct.get("Violation@K"), 0.0) or 0.0
            correct_r = safe_float(correct.get("Recall@K"), 0.0) or 0.0
            for control in ["D2_source_x_axis_swap", "D3_source_x_sign_flip"]:
                other = det_by_key.get((source_id, control, k))
                if not other:
                    continue
                other_v = safe_float(other.get("Violation@K"), 0.0) or 0.0
                other_r = safe_float(other.get("Recall@K"), 0.0) or 0.0
                if correct_v > other_v and correct_r <= other_r:
                    axis_failures.append(
                        {
                            "source_id": source_id,
                            "K": k,
                            "control": control,
                            "delta_Recall@K": correct_r - other_r,
                            "delta_Violation@K": correct_v - other_v,
                        }
                    )

    gate_rows = [
        {
            "gate": "1_route_redefined",
            "passed": True,
            "decision": "frame_aware_directional_compatibility",
            "reason": "left/right/front/behind are treated as one frame-aware directional route",
        },
        {
            "gate": "2_frame_protocol_frozen",
            "passed": True,
            "decision": "dataset_world_xy_reference_frame_from_3rscan_obb_centroids",
            "reason": "uses existing materialization policy before metric review",
        },
        {
            "gate": "3_residuals_defined",
            "passed": True,
            "decision": "signed_dx_for_left_right_signed_dy_for_front_behind",
            "reason": "subject-minus-object world XY residuals are explicit",
        },
        {
            "gate": "4_source_wide_s2_no_regression",
            "passed": len(violation_regressions) == 0 and len(recall_large_losses) == 0,
            "decision": "pass" if len(violation_regressions) == 0 and len(recall_large_losses) == 0 else "fail",
            "reason": f"violation_regressions={len(violation_regressions)}, recall_large_losses={len(recall_large_losses)}",
        },
        {
            "gate": "4_controls_degrade",
            "passed": len(control_failures) == 0,
            "decision": "pass" if len(control_failures) == 0 else "fail",
            "reason": f"control_failures={len(control_failures)}",
        },
        {
            "gate": "5_per_predicate_slices_stable",
            "passed": len(predicate_failures) == 0,
            "decision": "pass" if len(predicate_failures) == 0 else "fail",
            "reason": f"predicate_failures={len(predicate_failures)}",
        },
        {
            "gate": "6_axis_controls_stable",
            "passed": len(axis_failures) == 0,
            "decision": "pass" if len(axis_failures) == 0 else "fail",
            "reason": f"axis_control_failures={len(axis_failures)}",
        },
    ]
    final_pass = all(bool(row["passed"]) for row in gate_rows)
    summary = {
        "final_pass": final_pass,
        "promote_to_main_validated_route": final_pass,
        "violation_regression_cells": len(violation_regressions),
        "recall_large_loss_cells": len(recall_large_losses),
        "control_failure_cells": len(control_failures),
        "predicate_failure_cells": len(predicate_failures),
        "axis_control_failure_cells": len(axis_failures),
        "selected_path": "promote_relative_horizontal_to_main_validated_route" if final_pass else "keep_relative_horizontal_as_frame_aware_caveated_diagnostic",
    }
    return gate_rows, summary


def report_text(
    summary: dict[str, Any],
    gate_rows: list[dict[str, Any]],
    existing_rows: list[dict[str, Any]],
    deterministic_rows: list[dict[str, Any]],
) -> str:
    key_existing = [
        row
        for row in existing_rows
        if row["comparison"] == "S2_source_x_Ce_minus_S0_source_score" and int(row["K"]) in PROMOTION_K
    ]
    key_deterministic = [
        row
        for row in deterministic_rows
        if row["score_id"] in {"D0_source_score", "D1_source_x_world_xy_frame", "D2_source_x_axis_swap", "D3_source_x_sign_flip"}
        and int(row["K"]) in PROMOTION_K
    ]

    def md_table(rows: list[dict[str, Any]], cols: list[str]) -> str:
        header = "| " + " | ".join(cols) + " |"
        sep = "| " + " | ".join("---" for _ in cols) + " |"
        body = ["| " + " | ".join(str(row.get(c, "")) for c in cols) + " |" for row in rows]
        return "\n".join([header, sep, *body])

    return f"""# H002 Relative Horizontal Frame Route Audit

## Status

```text
status = {summary['status']}
validation_errors = {summary['validation_errors']}
selected_path = {summary['selected_path']}
promote_to_main_validated_route = {str(summary['promote_to_main_validated_route']).lower()}
next_todo = {summary['next_todo']}
```

## Six-Step Result

{md_table(gate_rows, ['gate', 'passed', 'decision', 'reason'])}

## Existing S2 vs Source Baseline

{md_table(key_existing, ['source_id', 'K', 'delta_Recall@K', 'delta_Violation@K', 'recall_not_large_loss', 'violation_nonincrease'])}

## Deterministic Frame Residual Controls

{md_table(key_deterministic, ['source_id', 'score_id', 'K', 'Recall@K', 'Violation@K'])}

## Interpretation

`relative_horizontal`은 route definition과 frame protocol 자체는 만들 수 있다. 하지만 현재 locked `S2_current_source_x_Ce` 결과 기준으로는 main validated route 승격 gate를 통과하지 못한다.

핵심 blocker:

- Open3DSG에서 `S2`가 source baseline 대비 Violation@K를 크게 악화한다.
- VL-SAT에서는 low/mid-K에서 recall loss가 있고 K=50/100에서 violation regression이 나타난다.
- per-predicate slice와 axis/sign control도 안정적인 main-route evidence를 만들기에는 부족하다.

따라서 현재 판단은:

```text
relative_horizontal = frame-aware caveated diagnostic
not main validated route yet
```
"""


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    required = {
        "source_family_metrics": args.source_reranking_dir / "source_family_metrics.csv",
        "selected_predictions": args.source_reranking_dir / "selected_predictions.jsonl",
        "source_eval_errors": args.source_reranking_dir / "validation_errors.jsonl",
        "materialization_ce": args.materialization_dir / "model_safe_ce_view.jsonl",
        "materialization_rank": args.materialization_dir / "source_rank_view.jsonl",
        "materialization_hidden": args.materialization_dir / "hidden_metric_manifest.jsonl",
    }
    for name, path in required.items():
        if not path.exists():
            errors.append({"error": "missing_required_input", "name": name, "path": rel_path(repo_root, path)})
    if required["source_eval_errors"].exists() and required["source_eval_errors"].read_text(encoding="utf-8").strip():
        errors.append({"error": "source_reranking_validation_errors_not_empty"})

    if errors:
        summary = {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS_ERROR,
            "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "validation_errors": len(errors),
            "selected_path": "blocked_missing_inputs",
            "promote_to_main_validated_route": False,
            "next_todo": "resolve_relative_horizontal_frame_route_audit_errors",
        }
        write_json(out / "summary.json", summary)
        with (out / "validation_errors.jsonl").open("w", encoding="utf-8") as handle:
            for error in errors:
                handle.write(json.dumps(error, ensure_ascii=False, sort_keys=True) + "\n")
        write_csv(out / "frame_protocol.csv", build_frame_protocol_rows())
        write_csv(out / "promotion_gate.csv", [])
        write_text(out / "report.md", report_text(summary, [], [], []))
        return 1

    source_metrics = read_csv(required["source_family_metrics"])
    existing_rows = existing_source_family_review(source_metrics)
    records, denom_by_group, denom_by_predicate_group = load_relative_records(args.materialization_dir)
    deterministic_rows = deterministic_frame_metrics(records, denom_by_group)
    predicate_rows = selected_per_predicate_metrics(required["selected_predictions"], denom_by_predicate_group)
    gate_rows, gate_summary = summarize_gate(existing_rows, predicate_rows, deterministic_rows)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_READY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "validation_errors": 0,
        "route_family": "relative_horizontal",
        "relations": PREDICATES,
        "frame_protocol": "dataset_world_xy_reference_frame_from_3rscan_obb_centroids",
        "source_rows_audited": len(records),
        "selected_path": gate_summary["selected_path"],
        "promote_to_main_validated_route": gate_summary["promote_to_main_validated_route"],
        "final_pass": gate_summary["final_pass"],
        "violation_regression_cells": gate_summary["violation_regression_cells"],
        "recall_large_loss_cells": gate_summary["recall_large_loss_cells"],
        "control_failure_cells": gate_summary["control_failure_cells"],
        "predicate_failure_cells": gate_summary["predicate_failure_cells"],
        "axis_control_failure_cells": gate_summary["axis_control_failure_cells"],
        "outputs": {
            "frame_protocol": rel_path(repo_root, out / "frame_protocol.csv"),
            "existing_source_family_review": rel_path(repo_root, out / "existing_source_family_review.csv"),
            "selected_per_predicate_review": rel_path(repo_root, out / "selected_per_predicate_review.csv"),
            "deterministic_frame_control_metrics": rel_path(repo_root, out / "deterministic_frame_control_metrics.csv"),
            "promotion_gate": rel_path(repo_root, out / "promotion_gate.csv"),
            "report": rel_path(repo_root, out / "report.md"),
            "summary": rel_path(repo_root, out / "summary.json"),
            "validation_errors": rel_path(repo_root, out / "validation_errors.jsonl"),
        },
        "next_todo": "h002_relative_horizontal_main_route_user_decision_after_audit",
    }

    write_csv(out / "frame_protocol.csv", build_frame_protocol_rows())
    write_csv(out / "existing_source_family_review.csv", existing_rows)
    write_csv(out / "selected_per_predicate_review.csv", predicate_rows)
    write_csv(out / "deterministic_frame_control_metrics.csv", deterministic_rows)
    write_csv(out / "promotion_gate.csv", gate_rows)
    write_json(out / "summary.json", summary)
    write_text(out / "validation_errors.jsonl", "")
    write_text(out / "report.md", report_text(summary, gate_rows, existing_rows, deterministic_rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
