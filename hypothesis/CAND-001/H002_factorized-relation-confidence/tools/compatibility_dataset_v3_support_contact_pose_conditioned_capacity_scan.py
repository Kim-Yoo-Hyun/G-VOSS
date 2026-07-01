#!/usr/bin/env python3
"""Scan support/contact capacity for pose-conditioned same-G anchors."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_target_plan"
DEFAULT_RGA_DIR = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_3RSCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan"

FEATURE_RUNNER_PATH = H2_ROOT / "tools/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner.py"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_target_plan_ready_for_capacity_scan"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan_ready_for_candidate_materialization_plan"
STATUS_DIAGNOSTIC = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan_diagnostic_only"
STATUS_ERRORS = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan_input_errors"
SELECTED_PATH_READY = "plan_candidate_materialization_for_pose_conditioned_support_contact"
SELECTED_PATH_DIAGNOSTIC = "freeze_pose_conditioned_support_contact_capacity_diagnostic"
NEXT_READY = "compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan"
NEXT_DIAGNOSTIC = "compatibility_dataset_v3_support_contact_pose_conditioned_diagnostic_freeze"

SUPPORT_PREDICATES = {"lying on", "standing on", "supported by"}
TARGET_ANCHORS = 200
MIN_ANCHORS = 120
MIN_STATE_ANCHORS = 60
MIN_NON_HARD_SHARE = 0.30
MAX_VISIBLE_PAIR_SHARE = 0.12
MAX_SCAN_SHARE = 0.10
PREVIEW_LIMIT = 240
EPS = 1e-9


def load_feature_runner() -> Any:
    spec = importlib.util.spec_from_file_location("h002_support_contact_feature_runner", FEATURE_RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load feature runner: {FEATURE_RUNNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FR = load_feature_runner()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--rga-dir", type=Path, default=DEFAULT_RGA_DIR)
    parser.add_argument("--scan-root", type=Path, default=DEFAULT_3RSCAN_ROOT)
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


def validate_inputs(plan_summary: dict[str, Any], plan_errors: list[dict[str, Any]], rga_dir: Path, scan_root: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors", "actual": plan_summary.get("validation_errors")})
    if plan_errors:
        errors.append({"error_type": "plan_validation_error_rows_present", "rows": len(plan_errors)})
    decision = plan_summary.get("path_decision", {})
    if decision.get("capacity_scan_allowed") is not True:
        errors.append({"error_type": "capacity_scan_not_allowed", "actual": decision.get("capacity_scan_allowed")})
    for key in ["candidate_materialization_allowed", "learned_smoke_allowed", "paper_evidence_allowed"]:
        if decision.get(key) is not False:
            errors.append({"error_type": "plan_boundary_not_false", "key": key, "actual": decision.get(key)})
    for name in ["train_hl_queue.jsonl", "train_lh_queue.jsonl"]:
        if not (rga_dir / name).exists():
            errors.append({"error_type": "missing_rga_queue", "path": rel_path(rga_dir / name)})
    if not scan_root.exists():
        errors.append({"error_type": "missing_scan_root", "path": rel_path(scan_root)})
    return errors


def anchor_key(row: dict[str, Any]) -> str:
    return f"{row.get('scan_id')}|{row.get('subject_id')}|{row.get('object_id')}"


def anchor_id_from_key(key: str) -> str:
    import hashlib

    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def row_hash(row: dict[str, Any]) -> str:
    return str(FR.stable_hash(row))


def hard_surface_pair(row: dict[str, Any]) -> bool:
    return bool(FR.hard_surface_pair(row))


def visible_pair(row: dict[str, Any]) -> str:
    return str(FR.visible_pair(row))


def finite(value: Any) -> bool:
    return bool(FR.finite(value))


def safe_float(features: dict[str, Any], key: str, default: float | None = None) -> float | None:
    value = features.get(key)
    return float(value) if finite(value) else default


def fast_float(value: Any) -> float | None:
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def representative_anchors(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("predicate_label") in SUPPORT_PREDICATES:
            grouped[anchor_key(row)].append(row)
    anchors: list[dict[str, Any]] = []
    for key, values in grouped.items():
        values.sort(key=row_hash)
        base = dict(values[0])
        base["_anchor_key"] = key
        base["_anchor_id"] = anchor_id_from_key(key)
        base["_source_predicates"] = sorted({str(row.get("predicate_label")) for row in values})
        base["_queue_kinds"] = sorted({str(row.get("queue_kind")) for row in values})
        base["_prediction_count"] = len(values)
        anchors.append(base)
    anchors.sort(key=lambda row: str(row.get("_anchor_id")))
    return anchors


def capacity_values(features: dict[str, Any]) -> dict[str, float | None]:
    return {
        "abs_gap": fast_float(features.get("abs_surface_gap_subject_bottom_to_object_top")),
        "xy": fast_float(features.get("xy_overlap_min_ratio")),
        "subject_vertical": fast_float(features.get("subject_vertical_extent_ratio")),
        "subject_flatness": fast_float(features.get("subject_flatness_ratio")),
        "subject_major_upness": fast_float(features.get("subject_major_axis_upness")),
    }


def classify_anchor_values(values: dict[str, float | None], thresholds: dict[str, float]) -> str | None:
    abs_gap = values.get("abs_gap")
    xy = values.get("xy")
    subject_vertical = values.get("subject_vertical")
    subject_flatness = values.get("subject_flatness")
    subject_major_upness = values.get("subject_major_upness")
    if abs_gap is None or xy is None or subject_vertical is None or subject_flatness is None or subject_major_upness is None:
        return None
    contact_core = abs_gap <= thresholds["abs_gap_max"] and xy >= thresholds["xy_overlap_min"]
    if not contact_core:
        return None
    lying_like = (
        subject_vertical <= thresholds["lying_vertical_max"]
        and (
            subject_flatness <= thresholds["lying_flatness_max"]
            or subject_major_upness <= thresholds["lying_major_upness_max"]
        )
    )
    upright_like = (
        subject_vertical >= thresholds["upright_vertical_min"]
        and subject_major_upness >= thresholds["upright_major_upness_min"]
    )
    if lying_like and not upright_like:
        return "lying_like_support_contact"
    if upright_like and not lying_like:
        return "upright_support_contact"
    return None


def make_threshold_grid() -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    pose_profiles = [
        {
            "pose_profile": "strict",
            "lying_vertical_max": 0.45,
            "lying_flatness_max": 0.20,
            "lying_major_upness_max": 0.35,
            "upright_vertical_min": 1.50,
            "upright_major_upness_min": 0.80,
        },
        {
            "pose_profile": "medium",
            "lying_vertical_max": 0.60,
            "lying_flatness_max": 0.30,
            "lying_major_upness_max": 0.50,
            "upright_vertical_min": 1.20,
            "upright_major_upness_min": 0.65,
        },
        {
            "pose_profile": "broad",
            "lying_vertical_max": 0.80,
            "lying_flatness_max": 0.40,
            "lying_major_upness_max": 0.50,
            "upright_vertical_min": 1.00,
            "upright_major_upness_min": 0.50,
        },
        {
            "pose_profile": "lying_medium_upright_broad",
            "lying_vertical_max": 0.60,
            "lying_flatness_max": 0.30,
            "lying_major_upness_max": 0.50,
            "upright_vertical_min": 1.00,
            "upright_major_upness_min": 0.50,
        },
        {
            "pose_profile": "lying_broad_upright_medium",
            "lying_vertical_max": 0.80,
            "lying_flatness_max": 0.40,
            "lying_major_upness_max": 0.50,
            "upright_vertical_min": 1.20,
            "upright_major_upness_min": 0.65,
        },
    ]
    for abs_gap in [0.05, 0.10, 0.15, 0.20]:
        for xy in [0.10, 0.25, 0.40]:
            for profile in pose_profiles:
                rows.append({"abs_gap_max": abs_gap, "xy_overlap_min": xy, **profile})
    return rows


def selected_caps(target: int = TARGET_ANCHORS) -> dict[str, int]:
    return {
        "scan": max(1, int(math.floor(target * MAX_SCAN_SHARE))),
        "visible_pair": max(1, int(math.floor(target * MAX_VISIBLE_PAIR_SHARE))),
    }


def select_balanced_anchors(candidates: list[dict[str, Any]], target: int = TARGET_ANCHORS) -> list[dict[str, Any]]:
    caps = selected_caps(target)
    by_state: dict[str, list[dict[str, Any]]] = {
        "lying_like_support_contact": [],
        "upright_support_contact": [],
    }
    for anchor in candidates:
        state = anchor.get("anchor_pose_state")
        if state in by_state:
            by_state[state].append(anchor)
    for state in by_state:
        by_state[state].sort(key=lambda row: (hard_surface_pair(row), visible_pair(row), str(row.get("scan_id")), str(row.get("_anchor_id"))))

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    scan_counts: Counter[str] = Counter()
    visible_counts: Counter[str] = Counter()
    state_counts: Counter[str] = Counter()
    desired_per_state = target // 2

    def can_add(row: dict[str, Any], state: str) -> bool:
        if row.get("_anchor_id") in selected_ids:
            return False
        if len(selected) >= target:
            return False
        if state_counts[state] >= desired_per_state:
            return False
        if scan_counts[str(row.get("scan_id"))] >= caps["scan"]:
            return False
        if visible_counts[visible_pair(row)] >= caps["visible_pair"]:
            return False
        return True

    progress = True
    while progress and len(selected) < target:
        progress = False
        for state in ["lying_like_support_contact", "upright_support_contact"]:
            for row in by_state[state]:
                if can_add(row, state):
                    selected.append(row)
                    selected_ids.add(str(row.get("_anchor_id")))
                    scan_counts[str(row.get("scan_id"))] += 1
                    visible_counts[visible_pair(row)] += 1
                    state_counts[state] += 1
                    progress = True
                    break
    return selected


def threshold_row(thresholds: dict[str, float], classified: list[dict[str, Any]]) -> dict[str, Any]:
    selected = select_balanced_anchors(classified, TARGET_ANCHORS)
    state_counts = Counter(row["anchor_pose_state"] for row in classified)
    selected_state_counts = Counter(row["anchor_pose_state"] for row in selected)
    selected_hard = sum(1 for row in selected if hard_surface_pair(row))
    selected_non_hard = len(selected) - selected_hard
    scan_counts = Counter(str(row.get("scan_id")) for row in selected)
    visible_counts = Counter(visible_pair(row) for row in selected)
    non_hard_share = selected_non_hard / len(selected) if selected else 0.0
    max_scan_share = max(scan_counts.values()) / len(selected) if selected else 0.0
    max_visible_share = max(visible_counts.values()) / len(selected) if selected else 0.0
    passes = (
        len(selected) >= MIN_ANCHORS
        and selected_state_counts["lying_like_support_contact"] >= MIN_STATE_ANCHORS
        and selected_state_counts["upright_support_contact"] >= MIN_STATE_ANCHORS
        and non_hard_share >= MIN_NON_HARD_SHARE
        and max_scan_share <= MAX_SCAN_SHARE + EPS
        and max_visible_share <= MAX_VISIBLE_PAIR_SHARE + EPS
    )
    row = {
        **thresholds,
        "classified_anchors": len(classified),
        "lying_like_anchors": state_counts["lying_like_support_contact"],
        "upright_anchors": state_counts["upright_support_contact"],
        "selected_anchors": len(selected),
        "selected_lying_like_anchors": selected_state_counts["lying_like_support_contact"],
        "selected_upright_anchors": selected_state_counts["upright_support_contact"],
        "selected_non_hard_surface_anchors": selected_non_hard,
        "selected_hard_surface_anchors": selected_hard,
        "selected_non_hard_surface_share": non_hard_share,
        "selected_max_single_scan_share": max_scan_share,
        "selected_max_single_visible_pair_share": max_visible_share,
        "passes_materialization_capacity_gate": passes,
    }
    row["_selected_anchor_ids"] = [str(anchor.get("_anchor_id")) for anchor in selected]
    return row


def classify_for_thresholds(anchors: list[dict[str, Any]], thresholds: dict[str, float]) -> list[dict[str, Any]]:
    classified: list[dict[str, Any]] = []
    for anchor in anchors:
        state = classify_anchor_values(anchor["capacity_values"], thresholds)
        if state is None:
            continue
        item = dict(anchor)
        item["anchor_pose_state"] = state
        classified.append(item)
    return classified


def score_threshold_row(row: dict[str, Any]) -> tuple[int, float, int, float, float]:
    return (
        1 if row["passes_materialization_capacity_gate"] else 0,
        float(row["selected_non_hard_surface_share"]),
        int(row["selected_anchors"]),
        -abs(int(row["selected_lying_like_anchors"]) - int(row["selected_upright_anchors"])),
        -float(row["selected_max_single_visible_pair_share"]),
    )


def audit_rows(best_row: dict[str, Any], selected: list[dict[str, Any]], total_anchors: int, classified: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scan_counts = Counter(str(row.get("scan_id")) for row in selected)
    visible_counts = Counter(visible_pair(row) for row in selected)
    source_predicates = Counter(pred for row in selected for pred in row.get("_source_predicates", []))
    queue_kinds = Counter(kind for row in selected for kind in row.get("_queue_kinds", []))
    state_counts = Counter(row.get("anchor_pose_state") for row in selected)
    return [
        {
            "risk": "capacity_gate",
            "value": best_row["passes_materialization_capacity_gate"],
            "severity": "low" if best_row["passes_materialization_capacity_gate"] else "high",
            "mitigation": "Only materialize if all capacity gates pass.",
        },
        {
            "risk": "anchor_state_balance",
            "value": json.dumps(dict(sorted(state_counts.items())), sort_keys=True),
            "severity": "low" if min(state_counts.values() or [0]) >= MIN_STATE_ANCHORS else "high",
            "mitigation": "Require at least 60 lying-like and 60 upright anchors.",
        },
        {
            "risk": "hard_surface_dominance",
            "value": 1.0 - float(best_row["selected_non_hard_surface_share"]),
            "severity": "low" if float(best_row["selected_non_hard_surface_share"]) >= MIN_NON_HARD_SHARE else "high",
            "mitigation": "Prioritize and cap non-hard-surface anchors during materialization.",
        },
        {
            "risk": "visible_pair_concentration",
            "value": float(best_row["selected_max_single_visible_pair_share"]),
            "severity": "low" if float(best_row["selected_max_single_visible_pair_share"]) <= MAX_VISIBLE_PAIR_SHARE else "high",
            "mitigation": "Cap visible pair frequency before row materialization.",
        },
        {
            "risk": "scan_concentration",
            "value": float(best_row["selected_max_single_scan_share"]),
            "severity": "low" if float(best_row["selected_max_single_scan_share"]) <= MAX_SCAN_SHARE else "high",
            "mitigation": "Cap scan frequency before row materialization.",
        },
        {
            "risk": "source_predicate_distribution_audit",
            "value": json.dumps(dict(sorted(source_predicates.items())), sort_keys=True),
            "severity": "audit",
            "mitigation": "Source predicates remain audit-only; row labels come from pose-conditioned predicate flips.",
        },
        {
            "risk": "queue_kind_distribution_audit",
            "value": json.dumps(dict(sorted(queue_kinds.items())), sort_keys=True),
            "severity": "audit",
            "mitigation": "Queue kind remains audit-only and must not become model input.",
        },
        {
            "risk": "classified_anchor_fraction",
            "value": len(classified) / max(total_anchors, 1),
            "severity": "audit",
            "mitigation": "Capacity scan reports a thresholded anchor subset; it is not a final dataset.",
        },
        {
            "risk": "top_visible_pairs",
            "value": json.dumps(visible_counts.most_common(5), ensure_ascii=False),
            "severity": "audit",
            "mitigation": "Inspect before materialization; keep visible-pair fields out of model inputs.",
        },
        {
            "risk": "top_scans",
            "value": json.dumps(scan_counts.most_common(5), ensure_ascii=False),
            "severity": "audit",
            "mitigation": "Inspect before materialization; keep scan IDs out of model inputs.",
        },
    ]


def build_point_preview(selected: list[dict[str, Any]], scan_root: Path) -> dict[str, Any]:
    sample = selected[: min(len(selected), 120)]
    if not sample:
        return {"sampled_anchors": 0, "point_feature_rows": 0, "point_feature_complete_rows": 0}
    point_cache = FR.build_point_cache(sample, scan_root)
    complete = 0
    for row in sample:
        pfeatures = FR.point_features(row, point_cache)
        row["point_features_optional"] = pfeatures
        needed = [
            "point_surface_gap_subject_bottom_to_object_top",
            "point_abs_surface_gap",
            "point_contact_candidate_ratio",
            "point_subject_bottom_band_density",
            "point_object_top_band_density",
        ]
        if all(finite(pfeatures.get(key)) for key in needed):
            complete += 1
    return {
        "sampled_anchors": len(sample),
        "point_feature_rows": len(sample),
        "point_feature_complete_rows": complete,
        "point_feature_complete_rate": complete / len(sample) if sample else 0.0,
    }


def preview_rows(selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in selected[:PREVIEW_LIMIT]:
        features = row.get("features", {})
        pfeatures = row.get("point_features_optional", {})
        rows.append(
            {
                "anchor_id": row.get("_anchor_id"),
                "anchor_pose_state": row.get("anchor_pose_state"),
                "scan_id": row.get("scan_id"),
                "subject_id": row.get("subject_id"),
                "object_id": row.get("object_id"),
                "visible_pair": visible_pair(row),
                "hard_surface_pair": hard_surface_pair(row),
                "source_predicates": row.get("_source_predicates"),
                "queue_kinds": row.get("_queue_kinds"),
                "target_rows_preview": [
                    {
                        "predicate_label": "lying on",
                        "compatibility_y": 1 if row.get("anchor_pose_state") == "lying_like_support_contact" else 0,
                    },
                    {
                        "predicate_label": "standing on",
                        "compatibility_y": 1 if row.get("anchor_pose_state") == "upright_support_contact" else 0,
                    },
                ],
                "G_e_semseg_subset": {
                    "abs_surface_gap_subject_bottom_to_object_top": features.get("abs_surface_gap_subject_bottom_to_object_top"),
                    "xy_overlap_min_ratio": features.get("xy_overlap_min_ratio"),
                    "subject_vertical_extent_ratio": features.get("subject_vertical_extent_ratio"),
                    "subject_flatness_ratio": features.get("subject_flatness_ratio"),
                    "subject_major_axis_upness": features.get("subject_major_axis_upness"),
                    "obb_contact_likelihood_proxy": features.get("obb_contact_likelihood_proxy"),
                },
                "G_e_point_optional_subset": {
                    key: pfeatures.get(key)
                    for key in [
                        "point_surface_gap_subject_bottom_to_object_top",
                        "point_abs_surface_gap",
                        "point_contact_candidate_ratio",
                        "point_subject_bottom_band_density",
                        "point_object_top_band_density",
                    ]
                    if pfeatures
                },
            }
        )
    return rows


def capacity_summary(best_row: dict[str, Any], support_rows: list[dict[str, Any]], anchors: list[dict[str, Any]], classified: list[dict[str, Any]], selected: list[dict[str, Any]], point_summary: dict[str, Any]) -> dict[str, Any]:
    state_counts = Counter(row.get("anchor_pose_state") for row in selected)
    return {
        "support_queue_rows": len(support_rows),
        "unique_directed_anchors": len(anchors),
        "classified_anchors_for_selected_threshold": len(classified),
        "selected_anchor_groups": len(selected),
        "selected_total_rows_if_materialized": len(selected) * 2,
        "selected_state_counts": dict(sorted(state_counts.items())),
        "selected_non_hard_surface_share": best_row.get("selected_non_hard_surface_share"),
        "selected_max_single_visible_pair_share": best_row.get("selected_max_single_visible_pair_share"),
        "selected_max_single_scan_share": best_row.get("selected_max_single_scan_share"),
        "best_thresholds": {key: best_row[key] for key in [
            "pose_profile",
            "abs_gap_max",
            "xy_overlap_min",
            "lying_vertical_max",
            "lying_flatness_max",
            "lying_major_upness_max",
            "upright_vertical_min",
            "upright_major_upness_min",
        ]},
        "passes_materialization_capacity_gate": best_row.get("passes_materialization_capacity_gate"),
        "point_preview": point_summary,
    }


def path_decision(errors: list[dict[str, Any]], best_row: dict[str, Any] | None) -> dict[str, Any]:
    if errors:
        return {
            "status": STATUS_ERRORS,
            "selected_path": "fix_inputs_before_capacity_scan",
            "next_todo": EXPECTED_PLAN_NEXT,
            "validation_errors": len(errors),
            "candidate_materialization_plan_allowed": False,
            "candidate_materialization_allowed": False,
            "learned_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "rationale": "Input validation failed; capacity scan cannot be trusted.",
        }
    if best_row and best_row.get("passes_materialization_capacity_gate") is True:
        return {
            "status": STATUS_READY,
            "selected_path": SELECTED_PATH_READY,
            "next_todo": NEXT_READY,
            "validation_errors": 0,
            "candidate_materialization_plan_allowed": True,
            "candidate_materialization_allowed": False,
            "learned_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "rationale": "Capacity gates passed for pose-conditioned same-G lying/standing anchors; write a materialization plan next.",
        }
    return {
        "status": STATUS_DIAGNOSTIC,
        "selected_path": SELECTED_PATH_DIAGNOSTIC,
        "next_todo": NEXT_DIAGNOSTIC,
        "validation_errors": 0,
        "candidate_materialization_plan_allowed": False,
        "candidate_materialization_allowed": False,
        "learned_smoke_allowed": False,
        "paper_evidence_allowed": False,
        "rationale": "No threshold setting passed the frozen capacity gates.",
    }


def report_text(summary: dict[str, Any]) -> str:
    cap = summary["capacity_summary"]
    decision = summary["path_decision"]
    return f"""# Compatibility Dataset V3 Support/Contact Pose-Conditioned Capacity Scan

## Status

```text
status = {summary['status']}
selected_path = {summary['selected_path']}
next_todo = {summary['next_todo']}
validation_errors = {summary['validation_errors']}
```

## Capacity

```text
support_queue_rows = {cap['support_queue_rows']}
unique_directed_anchors = {cap['unique_directed_anchors']}
classified_anchors_for_selected_threshold = {cap['classified_anchors_for_selected_threshold']}
selected_anchor_groups = {cap['selected_anchor_groups']}
selected_total_rows_if_materialized = {cap['selected_total_rows_if_materialized']}
selected_state_counts = {cap['selected_state_counts']}
selected_non_hard_surface_share = {cap['selected_non_hard_surface_share']}
selected_max_single_visible_pair_share = {cap['selected_max_single_visible_pair_share']}
selected_max_single_scan_share = {cap['selected_max_single_scan_share']}
passes_materialization_capacity_gate = {cap['passes_materialization_capacity_gate']}
```

## Decision

```text
candidate_materialization_plan_allowed = {decision['candidate_materialization_plan_allowed']}
candidate_materialization_allowed = {decision['candidate_materialization_allowed']}
learned_smoke_allowed = {decision['learned_smoke_allowed']}
paper_evidence_allowed = {decision['paper_evidence_allowed']}
```

This is still a capacity scan. It does not materialize final candidate rows and does not run a
learned smoke model.

## Next

```text
{summary['next_todo']}
```
"""


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(args.plan_dir / "summary.json")
    plan_errors = read_jsonl(args.plan_dir / "validation_errors.jsonl")
    errors = validate_inputs(plan_summary, plan_errors, args.rga_dir, args.scan_root)

    support_rows: list[dict[str, Any]] = []
    line_counts: dict[str, int] = {}
    anchors: list[dict[str, Any]] = []
    threshold_rows: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    classified_for_best: list[dict[str, Any]] = []
    point_summary: dict[str, Any] = {"sampled_anchors": 0, "point_feature_rows": 0, "point_feature_complete_rows": 0}
    best_row: dict[str, Any] | None = None

    if not errors:
        support_rows, line_counts = FR.scan_support_queues(args.rga_dir)
        anchors = representative_anchors(support_rows)
        semseg_cache = FR.load_semseg_cache(anchors, args.scan_root)
        for row in anchors:
            objects = semseg_cache.get(str(row.get("scan_id")), {})
            row["features"] = FR.semseg_features(row, objects)
            row["capacity_values"] = capacity_values(row["features"])

        for thresholds in make_threshold_grid():
            classified = classify_for_thresholds(anchors, thresholds)
            row = threshold_row(thresholds, classified)
            threshold_rows.append(row)
        threshold_rows.sort(key=score_threshold_row, reverse=True)
        if threshold_rows:
            best_row = threshold_rows[0]
            classified_for_best = classify_for_thresholds(anchors, {key: float(best_row[key]) for key in [
                "abs_gap_max",
                "xy_overlap_min",
                "lying_vertical_max",
                "lying_flatness_max",
                "lying_major_upness_max",
                "upright_vertical_min",
                "upright_major_upness_min",
            ]})
            selected_ids = set(best_row.get("_selected_anchor_ids", []))
            selected = [row for row in classified_for_best if str(row.get("_anchor_id")) in selected_ids]
            selected.sort(key=lambda row: best_row.get("_selected_anchor_ids", []).index(str(row.get("_anchor_id"))))
            point_summary = build_point_preview(selected, args.scan_root)

    public_threshold_rows = []
    for row in threshold_rows:
        public = dict(row)
        public.pop("_selected_anchor_ids", None)
        public_threshold_rows.append(public)

    if best_row is None:
        best_row = {"passes_materialization_capacity_gate": False}
    cap_summary = capacity_summary(best_row, support_rows, anchors, classified_for_best, selected, point_summary)
    audit = audit_rows(best_row, selected, len(anchors), classified_for_best) if selected else []
    decision = path_decision(errors, best_row)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": decision["status"],
        "selected_path": decision["selected_path"],
        "next_todo": decision["next_todo"],
        "validation_errors": len(errors),
        "plan_status": plan_summary.get("status"),
        "line_counts": line_counts,
        "capacity_summary": cap_summary,
        "path_decision": decision,
        "output_paths": {
            "capacity_summary": rel_path(output_dir / "capacity_summary.json"),
            "threshold_grid_capacity": rel_path(output_dir / "threshold_grid_capacity.csv"),
            "anchor_candidate_preview": rel_path(output_dir / "anchor_candidate_preview.jsonl"),
            "shortcut_capacity_audit": rel_path(output_dir / "shortcut_capacity_audit.csv"),
            "path_decision": rel_path(output_dir / "path_decision.json"),
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "boundary": {
            "split": "train_only_capacity_scan",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "materializes_candidate_rows": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
        },
    }

    write_json(output_dir / "capacity_summary.json", cap_summary)
    write_csv(output_dir / "threshold_grid_capacity.csv", public_threshold_rows)
    write_jsonl(output_dir / "anchor_candidate_preview.jsonl", preview_rows(selected))
    write_csv(output_dir / "shortcut_capacity_audit.csv", audit)
    write_json(output_dir / "path_decision.json", decision)
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    (output_dir / "report.md").write_text(report_text(summary), encoding="utf-8")

    print(f"status={summary['status']}")
    print(f"selected_path={summary['selected_path']}")
    print(f"next={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
