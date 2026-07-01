#!/usr/bin/env python3
"""Run the support/contact evidence probe before H002 v3 materialization or smoke."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Callable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_evidence_probe_plan"
DEFAULT_RGA_DIR = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_V2_SCHEMA_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_schema_shortcut_audit"
DEFAULT_V2_CANDIDATE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_candidate_materialization"
DEFAULT_V2_FAILURE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_failure_analysis"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_evidence_probe_runner"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v3_support_contact_evidence_probe_plan_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_support_contact_evidence_probe_runner"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_evidence_probe_runner_v1"
STATUS_READY = "h002_compatibility_dataset_v3_support_contact_evidence_probe_runner_blocks_numeric_support_smoke"
STATUS_ERRORS = "h002_compatibility_dataset_v3_support_contact_evidence_probe_runner_input_errors"
SELECTED_PATH = "block_numeric_support_contact_smoke_select_visual_mesh_or_defer_support_contact"
NEXT_TODO = "compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan"

SUPPORT_PREDICATES = {"standing on", "lying on", "supported by"}
HARD_SURFACES = {"floor", "wall", "ceiling", "room", "window", "door"}
REPORTABLE_GROUP_MIN = 60


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--rga-dir", type=Path, default=DEFAULT_RGA_DIR)
    parser.add_argument("--v2-schema-dir", type=Path, default=DEFAULT_V2_SCHEMA_DIR)
    parser.add_argument("--v2-candidate-dir", type=Path, default=DEFAULT_V2_CANDIDATE_DIR)
    parser.add_argument("--v2-failure-dir", type=Path, default=DEFAULT_V2_FAILURE_DIR)
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
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def support_family(row: dict[str, Any]) -> bool:
    return row.get("predicate_family") == "support_contact" and row.get("predicate_label") in SUPPORT_PREDICATES


def pair_key(row: dict[str, Any]) -> str:
    return f"{row.get('scan_id')}::{row.get('subgraph_id')}::{row.get('subject_id')}->{row.get('object_id')}"


def visible_pair(row: dict[str, Any]) -> str:
    return f"{row.get('subject_label')} [REL] {row.get('object_label')}"


def hard_surface_flag(row: dict[str, Any]) -> bool:
    return str(row.get("subject_label", "")).lower() in HARD_SURFACES or str(row.get("object_label", "")).lower() in HARD_SURFACES


def scan_support_queues(rga_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paths = [rga_dir / "train_hl_queue.jsonl", rga_dir / "train_lh_queue.jsonl"]
    support_rows: list[dict[str, Any]] = []
    line_counts: dict[str, int] = {}
    for path in paths:
        count = 0
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                count += 1
                row = json.loads(line)
                if support_family(row):
                    support_rows.append(row)
        line_counts[rel_path(path)] = count
    return support_rows, {"line_counts": line_counts}


def source_inventory_rows(support_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counters: dict[str, Counter[str]] = {
        "predicate": Counter(),
        "queue_kind": Counter(),
        "predicate_queue": Counter(),
        "predicate_geometry_status": Counter(),
        "predicate_label_match_status": Counter(),
        "rank_band": Counter(),
        "hard_surface": Counter(),
        "machine_hint": Counter(),
    }
    scans: set[str] = set()
    directed_pairs: set[str] = set()
    visible_pairs: set[str] = set()
    reason_codes: Counter[str] = Counter()
    for row in support_rows:
        pred = str(row.get("predicate_label"))
        queue = str(row.get("queue_kind"))
        geometry = str(row.get("geometry_status"))
        label_match = str(row.get("label_match_status"))
        counters["predicate"][pred] += 1
        counters["queue_kind"][queue] += 1
        counters["predicate_queue"][f"{pred}|{queue}"] += 1
        counters["predicate_geometry_status"][f"{pred}|{geometry}"] += 1
        counters["predicate_label_match_status"][f"{pred}|{label_match}"] += 1
        counters["rank_band"][str(row.get("rank_band"))] += 1
        counters["hard_surface"]["hard_surface"] += 1 if hard_surface_flag(row) else 0
        counters["hard_surface"]["non_hard_surface"] += 0 if hard_surface_flag(row) else 1
        counters["machine_hint"][str(row.get("machine_hint"))] += 1
        scans.add(str(row.get("scan_id")))
        directed_pairs.add(pair_key(row))
        visible_pairs.add(visible_pair(row))
        for code in row.get("reason_codes") or []:
            reason_codes[str(code)] += 1
    rows: list[dict[str, Any]] = [
        {"metric": "support_queue_rows", "value": len(support_rows)},
        {"metric": "distinct_scans", "value": len(scans)},
        {"metric": "distinct_directed_pairs", "value": len(directed_pairs)},
        {"metric": "distinct_visible_pairs", "value": len(visible_pairs)},
    ]
    for name, counter in counters.items():
        for key, value in sorted(counter.items()):
            rows.append({"metric": name, "key": key, "value": value})
    for key, value in reason_codes.most_common(30):
        rows.append({"metric": "top_reason_code", "key": key, "value": value})
    return rows


def exact_pair_capacity(support_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in support_rows:
        groups[pair_key(row)].append(row)
    summary_rows: list[dict[str, Any]] = []
    preview_rows: list[dict[str, Any]] = []
    counters: Counter[str] = Counter()
    predicate_sets: Counter[str] = Counter()
    for key, rows in groups.items():
        predicates = sorted({str(row.get("predicate_label")) for row in rows})
        statuses = sorted({str(row.get("geometry_status")) for row in rows})
        queues = sorted({str(row.get("queue_kind")) for row in rows})
        hints = sorted({str(row.get("machine_hint")) for row in rows})
        predicate_set = ";".join(predicates)
        predicate_sets[predicate_set] += 1
        if len(predicates) >= 2:
            counters["multi_predicate_exact_pair_groups"] += 1
        if len(predicates) >= 2 and len(statuses) >= 2:
            counters["multi_predicate_mixed_geometry_status_groups"] += 1
        if len(predicates) >= 2 and len(queues) >= 2:
            counters["multi_predicate_mixed_queue_groups"] += 1
        if len(predicates) >= 2 and len(statuses) >= 2 and not any(hard_surface_flag(row) for row in rows):
            counters["candidate_non_hard_surface_exact_pair_groups"] += 1
        if len(predicates) >= 2 and len(preview_rows) < 80:
            first = rows[0]
            preview_rows.append(
                {
                    "pair_key": key,
                    "scan_id": first.get("scan_id"),
                    "subgraph_id": first.get("subgraph_id"),
                    "subject_id": first.get("subject_id"),
                    "object_id": first.get("object_id"),
                    "subject_label": first.get("subject_label"),
                    "object_label": first.get("object_label"),
                    "predicates": predicates,
                    "geometry_statuses": statuses,
                    "queue_kinds": queues,
                    "machine_hints": hints,
                    "rows": len(rows),
                    "hard_surface": any(hard_surface_flag(row) for row in rows),
                }
            )
    summary_rows.extend(
        [
            {"probe": "exact_directed_pair", "metric": "total_groups", "value": len(groups)},
            {"probe": "exact_directed_pair", "metric": "multi_predicate_exact_pair_groups", "value": counters["multi_predicate_exact_pair_groups"]},
            {
                "probe": "exact_directed_pair",
                "metric": "multi_predicate_mixed_geometry_status_groups",
                "value": counters["multi_predicate_mixed_geometry_status_groups"],
            },
            {
                "probe": "exact_directed_pair",
                "metric": "multi_predicate_mixed_queue_groups",
                "value": counters["multi_predicate_mixed_queue_groups"],
            },
            {
                "probe": "exact_directed_pair",
                "metric": "candidate_non_hard_surface_exact_pair_groups",
                "value": counters["candidate_non_hard_surface_exact_pair_groups"],
            },
        ]
    )
    for key, value in predicate_sets.most_common(20):
        summary_rows.append({"probe": "exact_directed_pair_predicate_set", "metric": key, "value": value})
    return summary_rows, preview_rows


def geometry_features(row: dict[str, Any]) -> dict[str, float]:
    return {
        key: float(value)
        for key, value in (row.get("G_e_numeric", {}).get("geometry_features", {}) or {}).items()
        if isinstance(value, (int, float))
    }


def coarse_geometry_key(features: dict[str, float]) -> str:
    selected = [
        ("normalized_distance_xy", 0.10),
        ("projected_overlap_max", 0.10),
        ("vertical_gap_subject_on_object", 0.25),
        ("normalized_center_delta_z", 0.20),
    ]
    parts = []
    for key, width in selected:
        value = features.get(key)
        if value is None:
            parts.append(f"{key}=missing")
        else:
            parts.append(f"{key}={round(value / width)}")
    return "|".join(parts)


def v2_same_near_geometry_capacity(sanitized_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    support_rows = [row for row in sanitized_rows if row.get("T_e", {}).get("relation_family") == "support_contact"]
    exact: dict[str, list[dict[str, Any]]] = defaultdict(list)
    coarse: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in support_rows:
        features = geometry_features(row)
        exact[json.dumps(features, sort_keys=True)].append(row)
        coarse[coarse_geometry_key(features)].append(row)

    def summarize(groups: dict[str, list[dict[str, Any]]], probe_name: str) -> list[dict[str, Any]]:
        total = len(groups)
        multi_pred = 0
        mixed_label = 0
        multi_pred_mixed_label = 0
        non_generated_candidate = 0
        for rows in groups.values():
            preds = {row.get("T_e", {}).get("predicate_label") for row in rows}
            labels = {row.get("y_compatibility") for row in rows}
            if len(preds) >= 2:
                multi_pred += 1
            if len(labels) >= 2:
                mixed_label += 1
            if len(preds) >= 2 and len(labels) >= 2:
                multi_pred_mixed_label += 1
            # v2 sanitized rows do not expose enough provenance to certify non-generated status.
        return [
            {"probe": probe_name, "metric": "groups", "value": total},
            {"probe": probe_name, "metric": "multi_predicate_groups", "value": multi_pred},
            {"probe": probe_name, "metric": "mixed_label_groups", "value": mixed_label},
            {"probe": probe_name, "metric": "multi_predicate_mixed_label_groups", "value": multi_pred_mixed_label},
            {"probe": probe_name, "metric": "non_generated_certified_groups", "value": non_generated_candidate},
        ]

    return summarize(exact, "v2_exact_G_sanitized") + summarize(coarse, "v2_near_G_coarse_sanitized")


def evidence_axis_inventory(plan_summary: dict[str, Any]) -> list[dict[str, Any]]:
    axes = []
    for row in plan_summary.get("evidence_axes", []):
        item = dict(row)
        item["runner_verdict"] = "fail_required_axis" if row.get("status", "").startswith("missing") else "available_or_partial"
        if row.get("axis") == "distance_and_overlap":
            item["runner_verdict"] = "available_control_only"
        if row.get("axis") == "vertical_gap_and_support_order":
            item["runner_verdict"] = "partial_not_enough_for_standing_lying"
        axes.append(item)
    return axes


def negative_policy_audit(candidate_rows: list[dict[str, Any]], failure_summary: dict[str, Any]) -> list[dict[str, Any]]:
    support_rows = [row for row in candidate_rows if row.get("T_e", {}).get("relation_family") == "support_contact"]
    counter = Counter(row.get("counterfactual_axis", {}).get("counterfactual_type") for row in support_rows)
    policy = {
        "none": ("primary_positive_seed", "allowed_as_positive_anchor"),
        "contact_gap_or_overlap_perturbation": ("control_only", "too easy; solved by generic gap/overlap geometry"),
        "wrong_pair_geometry": ("control_only", "tests geometry alignment but is not predicate compatibility"),
        "shuffled_geometry": ("control_only", "v2 false-positive rate was high; not primary negative"),
    }
    rows = []
    for key, count in sorted(counter.items()):
        role, reason = policy.get(str(key), ("unknown", "not in current policy"))
        rows.append(
            {
                "counterfactual_type": key,
                "count": count,
                "policy": role,
                "reason": reason,
            }
        )
    for finding in failure_summary.get("key_findings", []):
        if finding.get("claim") == "Support/contact drives most geometry signal.":
            for item in finding.get("value", {}).get("highest_support_contact_negative_fp_types", []):
                rows.append(
                    {
                        "counterfactual_type": item.get("counterfactual_type"),
                        "count": item.get("n"),
                        "policy": "failure_diagnostic",
                        "M5_false_positive_rate": item.get("M5_false_positive_rate"),
                        "reason": "recorded v2 false-positive diagnostic",
                    }
                )
    return rows


def majority_accuracy(rows: list[dict[str, Any]], label_fn: Callable[[dict[str, Any]], int], feature_fn: Callable[[dict[str, Any]], str]) -> dict[str, Any]:
    groups: dict[str, list[int]] = defaultdict(list)
    labels = [label_fn(row) for row in rows]
    majority = max(Counter(labels).values()) / max(len(labels), 1)
    for row in rows:
        groups[feature_fn(row)].append(label_fn(row))
    correct = 0
    for vals in groups.values():
        count = Counter(vals)
        correct += max(count.values())
    return {
        "rows": len(rows),
        "majority_baseline": round(majority, 6),
        "predictor_accuracy": round(correct / max(len(rows), 1), 6),
        "distinct_values": len(groups),
    }


def best_threshold_accuracy(rows: list[dict[str, Any]], feature_key: str) -> dict[str, Any]:
    values: list[tuple[float, int]] = []
    for row in rows:
        features = geometry_features(row)
        if feature_key in features:
            values.append((features[feature_key], int(row.get("y_compatibility"))))
    if not values:
        return {"feature": feature_key, "rows": 0, "best_accuracy": None}
    labels = [label for _, label in values]
    majority = max(Counter(labels).values()) / len(labels)
    candidates = sorted({value for value, _ in values})
    best = majority
    best_threshold = None
    best_direction = None
    for threshold in candidates:
        for direction in ("ge", "lt"):
            correct = 0
            for value, label in values:
                pred = 1 if (value >= threshold if direction == "ge" else value < threshold) else 0
                if pred == label:
                    correct += 1
            acc = correct / len(values)
            if acc > best:
                best = acc
                best_threshold = threshold
                best_direction = direction
    return {
        "feature": feature_key,
        "rows": len(values),
        "majority_baseline": round(majority, 6),
        "best_accuracy": round(best, 6),
        "best_threshold": best_threshold,
        "best_direction": best_direction,
    }


def shortcut_precheck(sanitized_rows: list[dict[str, Any]], candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    support_rows = [row for row in sanitized_rows if row.get("T_e", {}).get("relation_family") == "support_contact"]
    candidate_support = [row for row in candidate_rows if row.get("T_e", {}).get("relation_family") == "support_contact"]
    label = lambda row: int(row.get("y_compatibility"))
    rows = []
    categorical = {
        "predicate_label": lambda row: str(row.get("T_e", {}).get("predicate_label")),
        "subject_label": lambda row: str(row.get("T_e", {}).get("subject_label")),
        "object_label": lambda row: str(row.get("T_e", {}).get("object_label")),
        "subject_object_text": lambda row: str(row.get("T_e", {}).get("subject_object_text")),
        "source_rank_band": lambda row: str(row.get("Z_e", {}).get("source_rank_band")),
    }
    for name, fn in categorical.items():
        result = majority_accuracy(support_rows, label, fn)
        rows.append({"probe": name, "source": "v2_sanitized_model_view", **result})

    hidden_label = lambda row: 1 if row.get("counterfactual_axis", {}).get("compatibility_label") == "positive" else 0
    hidden_fields = {
        "hidden_counterfactual_type": lambda row: str(row.get("counterfactual_axis", {}).get("counterfactual_type")),
        "hidden_row_role": lambda row: str(row.get("row_role")),
        "hidden_geometry_status_baseline": lambda row: str(row.get("geometry_status_baseline")),
        "hidden_machine_hint": lambda row: str(row.get("hidden_control", {}).get("source_machine_hint")),
    }
    for name, fn in hidden_fields.items():
        result = majority_accuracy(candidate_support, hidden_label, fn)
        rows.append({"probe": name, "source": "v2_candidate_hidden_diagnostic", "blocked_as_feature": True, **result})

    for key in [
        "normalized_distance_xy",
        "vertical_gap_subject_on_object",
        "distance_xy",
        "projected_overlap_max",
        "projected_iou_xy",
        "projected_subject_overlap_ratio",
    ]:
        rows.append({"probe": f"numeric_threshold:{key}", "source": "v2_sanitized_model_view", **best_threshold_accuracy(support_rows, key)})
    for row in rows:
        acc = row.get("predictor_accuracy", row.get("best_accuracy"))
        row["risk"] = "high" if isinstance(acc, float) and acc >= 0.8 else ("medium" if isinstance(acc, float) and acc >= 0.65 else "low")
    return rows


def path_decision(
    exact_rows: list[dict[str, Any]],
    v2_near_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
    shortcut_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    exact_metrics = {row["metric"]: row["value"] for row in exact_rows if row.get("probe") == "exact_directed_pair"}
    near_metrics = {f"{row['probe']}:{row['metric']}": row["value"] for row in v2_near_rows}
    missing_required_axes = [
        row["axis"]
        for row in evidence_rows
        if row.get("runner_verdict") == "fail_required_axis"
        and row["axis"] in {"role_orientation_pose", "contact_direction_surface_normal", "mesh_visual_multiview"}
    ]
    high_shortcuts = [row for row in shortcut_rows if row.get("risk") == "high"]
    exact_candidates = int(exact_metrics.get("multi_predicate_mixed_geometry_status_groups", 0) or 0)
    exact_non_hard_candidates = int(exact_metrics.get("candidate_non_hard_surface_exact_pair_groups", 0) or 0)
    materialization_allowed = exact_non_hard_candidates >= REPORTABLE_GROUP_MIN and not missing_required_axes and not high_shortcuts
    visual_mesh_required = bool(missing_required_axes)
    selected_path = (
        "support_contact_materialization_allowed"
        if materialization_allowed
        else (
            "route_to_visual_mesh_or_role_orientation_evidence"
            if visual_mesh_required
            else "keep_support_contact_diagnostic_due_to_shortcut_or_capacity"
        )
    )
    next_todo = (
        "compatibility_dataset_v3_support_contact_materialization_plan"
        if materialization_allowed
        else (
            "compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan"
            if visual_mesh_required
            else "compatibility_dataset_v3_support_contact_diagnostic_freeze_decision"
        )
    )
    return {
        "selected_path": selected_path,
        "next_todo": next_todo,
        "support_contact_materialization_allowed": materialization_allowed,
        "visual_mesh_or_role_orientation_required": visual_mesh_required,
        "diagnostic_only": not materialization_allowed,
        "exact_directed_pair_mixed_geometry_status_groups": exact_candidates,
        "candidate_non_hard_surface_exact_pair_groups": exact_non_hard_candidates,
        "reportable_group_min": REPORTABLE_GROUP_MIN,
        "missing_required_axes": missing_required_axes,
        "high_shortcut_count": len(high_shortcuts),
        "high_shortcuts": high_shortcuts[:20],
        "near_geometry_metrics": near_metrics,
        "rationale": (
            "Current numeric artifacts do not expose role/orientation/contact-direction/surface-normal/visual evidence, "
            "so support/contact should not proceed to learned smoke from numeric v2 rows."
            if not materialization_allowed
            else "Support/contact can proceed to materialization under the declared gates."
        ),
    }


def validate_inputs(plan_summary: dict[str, Any], plan_validation_rows: list[dict[str, Any]], rga_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors", "actual": plan_summary.get("validation_errors")})
    if plan_validation_rows:
        errors.append({"error_type": "plan_validation_error_rows_present", "rows": len(plan_validation_rows)})
    for name in ["train_hl_queue.jsonl", "train_lh_queue.jsonl"]:
        if not (rga_dir / name).exists():
            errors.append({"error_type": "missing_queue_file", "path": rel_path(rga_dir / name)})
    return errors


def build_report(summary: dict[str, Any]) -> str:
    decision = summary["path_decision"]
    inv = summary["source_inventory_summary"]
    lines = [
        "# Compatibility Dataset V3 Support/Contact Evidence Probe Runner",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {decision['selected_path']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Source Inventory",
        "",
        "```text",
        f"support_queue_rows = {inv['support_queue_rows']}",
        f"distinct_directed_pairs = {inv['distinct_directed_pairs']}",
        f"distinct_visible_pairs = {inv['distinct_visible_pairs']}",
        f"exact multi-predicate mixed-geometry groups = {decision['exact_directed_pair_mixed_geometry_status_groups']}",
        f"non-hard-surface exact candidate groups = {decision['candidate_non_hard_surface_exact_pair_groups']}",
        "```",
        "",
        "## Path Decision",
        "",
        "```text",
        f"support_contact_materialization_allowed = {decision['support_contact_materialization_allowed']}",
        f"visual_mesh_or_role_orientation_required = {decision['visual_mesh_or_role_orientation_required']}",
        f"diagnostic_only = {decision['diagnostic_only']}",
        f"missing_required_axes = {decision['missing_required_axes']}",
        f"high_shortcut_count = {decision['high_shortcut_count']}",
        "```",
        "",
        "## Interpretation",
        "",
        "The current support/contact numeric artifacts are not enough for a clean predicate-conditioned",
        "`C_e` smoke. They contain distance, overlap, and vertical-gap proxies, but not explicit role,",
        "orientation, contact direction, surface normals, mesh evidence, or multi-view evidence. The",
        "existing v2 support/contact rows also rely on generated negatives, so direct learned smoke",
        "would likely repeat the previous geometry-perturbation failure.",
        "",
        "## Boundary",
        "",
        "- Train-only evidence probe.",
        "- No learned smoke.",
        "- No validation/test usage.",
        "- No paper-level evidence promotion.",
        "- No H001 artifact modification.",
        "",
        "## Next",
        "",
        "```text",
        summary["next_todo"],
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(args.plan_dir / "summary.json")
    plan_validation_rows = read_jsonl(args.plan_dir / "validation_errors.jsonl")
    errors = validate_inputs(plan_summary, plan_validation_rows, args.rga_dir)

    support_rows, queue_meta = scan_support_queues(args.rga_dir)
    source_rows = source_inventory_rows(support_rows)
    source_summary = {row["metric"]: row.get("value") for row in source_rows if "key" not in row}

    exact_capacity_rows, exact_preview_rows = exact_pair_capacity(support_rows)
    sanitized_rows = read_jsonl(args.v2_schema_dir / "sanitized_model_view.jsonl")
    candidate_rows = read_jsonl(args.v2_candidate_dir / "compatibility_rows.jsonl")
    failure_summary = read_json(args.v2_failure_dir / "summary.json")
    v2_near_capacity_rows = v2_same_near_geometry_capacity(sanitized_rows)
    evidence_rows = evidence_axis_inventory(plan_summary)
    negative_rows = negative_policy_audit(candidate_rows, failure_summary)
    shortcut_rows = shortcut_precheck(sanitized_rows, candidate_rows)
    decision = path_decision(exact_capacity_rows, v2_near_capacity_rows, evidence_rows, shortcut_rows)

    status = STATUS_ERRORS if errors else STATUS_READY
    next_todo = "fix_support_contact_evidence_probe_runner_inputs" if errors else decision["next_todo"]
    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": decision["selected_path"] if not errors else "fix_inputs_before_path_decision",
        "next_todo": next_todo,
        "validation_errors": len(errors),
        "input_roots": {
            "plan": rel_path(args.plan_dir),
            "rga": rel_path(args.rga_dir),
            "v2_schema": rel_path(args.v2_schema_dir),
            "v2_candidate": rel_path(args.v2_candidate_dir),
            "v2_failure": rel_path(args.v2_failure_dir),
        },
        "queue_meta": queue_meta,
        "source_inventory_summary": source_summary,
        "path_decision": decision,
        "boundary": {
            "split": "train_only_probe_runner",
            "validation_usage": False,
            "test_usage": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "full_match_rows_scanned": False,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "path_decision": rel_path(args.output_dir / "path_decision.json"),
            "source_inventory": rel_path(args.output_dir / "source_inventory.json"),
            "source_inventory_csv": rel_path(args.output_dir / "source_inventory.csv"),
            "same_or_near_geometry_capacity": rel_path(args.output_dir / "same_or_near_geometry_capacity.csv"),
            "exact_pair_preview": rel_path(args.output_dir / "exact_pair_preview.jsonl"),
            "evidence_axis_inventory": rel_path(args.output_dir / "evidence_axis_inventory.csv"),
            "negative_policy_audit": rel_path(args.output_dir / "negative_policy_audit.csv"),
            "shortcut_precheck": rel_path(args.output_dir / "shortcut_precheck.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    source_inventory = {
        "summary": source_summary,
        "queue_meta": queue_meta,
        "rows": source_rows,
    }
    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "path_decision.json", decision)
    write_json(args.output_dir / "source_inventory.json", source_inventory)
    write_csv(args.output_dir / "source_inventory.csv", source_rows)
    write_csv(args.output_dir / "same_or_near_geometry_capacity.csv", exact_capacity_rows + v2_near_capacity_rows)
    write_jsonl(args.output_dir / "exact_pair_preview.jsonl", exact_preview_rows)
    write_csv(args.output_dir / "evidence_axis_inventory.csv", evidence_rows)
    write_csv(args.output_dir / "negative_policy_audit.csv", negative_rows)
    write_csv(args.output_dir / "shortcut_precheck.csv", shortcut_rows)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    (args.output_dir / "report.md").write_text(build_report(summary), encoding="utf-8")

    print(f"status={summary['status']}")
    print(f"selected_path={summary['selected_path']}")
    print(f"next={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
