#!/usr/bin/env python3
"""Run attachment-deferred G4 policy smoke and GT/counterfactual evaluation.

This step applies the frozen G2 conservative policy to G1c smoke evidence and
to G3 train-dev positive/counterfactual seeds after extracting point/surface
evidence. It does not fit a calibrator, score VL-SAT/Open3DSG predictions, run
source metrics, or change the current AAAI main claim.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from run_attachment_deferred_extractor_dry_run import (
    PREDICATE_LABELS,
    TARGET_FAMILY,
    build_evidence_row,
    ensure_dir,
    iter_jsonl,
    relpath,
    utc_now,
    write_json,
    write_jsonl,
)
from validate_attachment_deferred_point_surface import (
    DEFAULT_CONTACT_THRESHOLD_M,
    DEFAULT_MAX_POINTS_PER_OBJECT,
    read_target_points,
    update_row_with_points,
)


SCHEMA_VERSION = "h001_attachment_deferred_gt_policy_smoke_v1"
DECISION_SCHEMA_VERSION = "h001_attachment_deferred_verifier_decision_v1"
POLICY_NAME = "attachment_deferred_conservative_v1"
POLICY_VERSION = "h001_attachment_deferred_verifier_policy_v1"
STATUS_READY = "attachment_deferred_gt_policy_smoke_ready_no_source_metrics"
STATUS_PARTIAL = "attachment_deferred_gt_policy_smoke_partial_no_source_metrics"
NEXT_GATE_READY = "G4b_attachment_error_visual_sanity_before_calibration"
NEXT_GATE_PARTIAL = "G4_attachment_evidence_repair_before_source_metrics"

DEFAULT_ATTACHMENT_ROOT = Path("experiments/H001_geom_reliability/sources/attachment_deferred")
DEFAULT_CALIBRATION_DIR = DEFAULT_ATTACHMENT_ROOT / "calibration_counterfactuals"
DEFAULT_VERIFIER_POLICY_DIR = DEFAULT_ATTACHMENT_ROOT / "verifier_policy"
DEFAULT_POINT_SURFACE_DIR = DEFAULT_ATTACHMENT_ROOT / "point_surface_validation"
DEFAULT_OUT = DEFAULT_ATTACHMENT_ROOT / "gt_policy_smoke"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--dataset-root", type=Path, default=Path("local_dataset"))
    parser.add_argument("--calibration-dir", type=Path, default=DEFAULT_CALIBRATION_DIR)
    parser.add_argument("--verifier-policy-dir", type=Path, default=DEFAULT_VERIFIER_POLICY_DIR)
    parser.add_argument("--point-surface-dir", type=Path, default=DEFAULT_POINT_SURFACE_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--contact-threshold-m", type=float, default=DEFAULT_CONTACT_THRESHOLD_M)
    parser.add_argument("--max-points-per-object", type=int, default=DEFAULT_MAX_POINTS_PER_OBJECT)
    return parser.parse_args()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def seed_to_source_row(seed: dict[str, Any], source_name: str) -> dict[str, Any]:
    return {
        "source_name": source_name,
        "scan_id": str(seed["scan_id"]),
        "subgraph_id": str(seed["subgraph_id"]),
        "subject_id": int(seed["subject_id"]),
        "object_id": int(seed["object_id"]),
        "subject_label": seed.get("subject_label"),
        "object_label": seed.get("object_label"),
        "predicate_label": str(seed["predicate_label"]),
    }


def evidence_target_ids(rows: list[dict[str, Any]]) -> dict[str, set[int]]:
    result: dict[str, set[int]] = defaultdict(set)
    for row in rows:
        result[str(row["scan_id"])].update([int(row["subject_id"]), int(row["object_id"])])
    return result


def load_scan_points(
    *,
    dataset_root: Path,
    object_ids_by_scan: dict[str, set[int]],
) -> tuple[dict[str, dict[int, np.ndarray]], dict[str, dict[str, Any]], list[str]]:
    scan_points: dict[str, dict[int, np.ndarray]] = {}
    scan_stats: dict[str, dict[str, Any]] = {}
    scan_errors: list[str] = []
    for scan_id, object_ids in sorted(object_ids_by_scan.items()):
        ply_path = dataset_root / "3RScan" / "scans" / scan_id / "labels.instances.annotated.v2.ply"
        if not ply_path.exists():
            scan_errors.append(f"missing_ply:{scan_id}:{ply_path}")
            scan_points[scan_id] = {object_id: np.empty((0, 3), dtype=np.float32) for object_id in object_ids}
            scan_stats[scan_id] = {"error": "missing_ply", "target_object_ids": sorted(object_ids)}
            continue
        try:
            points, stats = read_target_points(ply_path, object_ids)
        except Exception as exc:  # pragma: no cover - surfaced in manifest.
            scan_errors.append(f"read_ply_failed:{scan_id}:{type(exc).__name__}:{exc}")
            points = {object_id: np.empty((0, 3), dtype=np.float32) for object_id in object_ids}
            stats = {"error": str(exc), "target_object_ids": sorted(object_ids)}
        scan_points[scan_id] = points
        scan_stats[scan_id] = stats
    return scan_points, scan_stats, scan_errors


def build_point_surface_evidence(
    *,
    source_rows: list[dict[str, Any]],
    dataset_root: Path,
    contact_threshold_m: float,
    max_points_per_object: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    geometry_cache: dict[str, tuple[dict[int, dict[str, Any]], list[str], list[str]]] = {}
    dry_rows: list[dict[str, Any]] = []
    dry_warnings: Counter[str] = Counter()
    for source_row in source_rows:
        dry_row, warnings = build_evidence_row(
            source_row,
            dataset_root=dataset_root,
            geometry_cache=geometry_cache,
        )
        dry_rows.append(dry_row)
        for warning in warnings:
            dry_warnings[str(warning)] += 1

    scan_points, scan_stats, scan_errors = load_scan_points(
        dataset_root=dataset_root,
        object_ids_by_scan=evidence_target_ids(dry_rows),
    )
    evidence_rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for row in dry_rows:
        scan_id = str(row["scan_id"])
        updated, diagnostic = update_row_with_points(
            row,
            points_by_object=scan_points.get(scan_id, {}),
            scan_stats=scan_stats.get(scan_id, {}),
            contact_threshold_m=contact_threshold_m,
            max_points_per_object=max_points_per_object,
        )
        evidence_rows.append(updated)
        diagnostics.append(diagnostic)
    return evidence_rows, diagnostics, {
        "dry_warning_counts": dict(sorted(dry_warnings.items())),
        "scan_errors": scan_errors,
        "scan_stats": {
            scan_id: {
                key: value
                for key, value in stats.items()
                if key
                in {
                    "ply_vertex_count_header",
                    "ply_face_count_header",
                    "ply_vertex_rows_read",
                    "target_vertex_rows_kept",
                    "target_object_ids",
                    "error",
                }
            }
            for scan_id, stats in sorted(scan_stats.items())
        },
    }


def policy_thresholds(policy: dict[str, Any]) -> dict[str, float]:
    common = policy.get("threshold_plan", {})
    return {
        "near": float(common["near_contact_threshold_m"]),
        "clear_far": float(common["clear_far_distance_m"]),
        "min_near_points": float(common["min_near_contact_points_for_satisfied"]),
        "min_patch": float(common["min_contact_patch_score_for_satisfied"]),
        "min_floor_clearance": float(common["min_floor_clearance_for_hanging_m"]),
        "max_support_no_contra": float(common["max_support_explanation_score_without_contradiction"]),
        "min_support_contra": float(common["min_support_explanation_score_for_contradiction"]),
    }


def status_decision(
    status: str,
    reasons: list[str],
    requirements: list[str],
    note: str,
) -> dict[str, Any]:
    return {
        "verification_status": status,
        "reason_codes": sorted(set(reasons)),
        "evidence_requirements_met": sorted(set(requirements)),
        "uncertain_by_design": status == "uncertain",
        "notes": [note],
    }


def evaluate_policy(row: dict[str, Any], thresholds: dict[str, float]) -> dict[str, Any]:
    point = row.get("point_contact_evidence", {})
    surface = row.get("surface_evidence", {})
    gravity = row.get("gravity_evidence", {})
    support = row.get("contradictory_support_evidence", {})
    affordance = row.get("affordance_context", {})

    subtype = str(row.get("subtype_hint") or "unknown")
    surface_type = str(surface.get("selected_surface_type") or "unknown")
    normal_class = str(surface.get("selected_surface_normal_class") or "unknown")
    min_distance = safe_float(point.get("min_point_distance_m"))
    near_count = safe_int(point.get("near_contact_point_count")) or 0
    patch_score = safe_float(point.get("contact_patch_score")) or 0.0
    floor_clearance = safe_float(gravity.get("floor_clearance_m"))
    hanging_score = safe_float(gravity.get("hanging_geometry_score")) or 0.0
    support_score = safe_float(support.get("support_explanation_score")) or 0.0
    floor_supported = bool(support.get("floor_or_table_supported"))
    class_prior = str(affordance.get("class_pair_prior") or "unknown")

    requirements: list[str] = []
    if row.get("extractor_status") == "ready":
        requirements.append("extractor_ready")
    if row.get("geometry_available", {}).get("points"):
        requirements.append("point_contact_available")
    if row.get("geometry_available", {}).get("normals"):
        requirements.append("surface_normal_available")
    if min_distance is not None and min_distance <= thresholds["near"]:
        requirements.append("near_contact_threshold_met")
    if near_count >= thresholds["min_near_points"]:
        requirements.append("near_contact_points_sufficient")
    if patch_score >= thresholds["min_patch"]:
        requirements.append("contact_patch_score_sufficient")
    if floor_clearance is not None and floor_clearance >= thresholds["min_floor_clearance"]:
        requirements.append("hanging_gravity_cue_present")
    if support_score <= thresholds["max_support_no_contra"]:
        requirements.append("no_strong_contradictory_support")

    contact_sufficient = (
        min_distance is not None
        and min_distance <= thresholds["near"]
        and (near_count >= thresholds["min_near_points"] or patch_score >= thresholds["min_patch"])
    )
    direct_contact = min_distance is not None and min_distance <= thresholds["near"]
    clear_far = min_distance is not None and min_distance >= thresholds["clear_far"] and near_count == 0
    support_contradicts_hanging = (
        floor_supported
        and support_score >= thresholds["min_support_contra"]
        and hanging_score <= 0.20
    )
    missing_required = (
        row.get("extractor_status") != "ready"
        or not row.get("geometry_available", {}).get("points")
        or not row.get("geometry_available", {}).get("normals")
        or min_distance is None
    )
    if affordance.get("allowed_as_proof") is not False:
        return status_decision(
            "uncertain",
            ["class_prior_only_not_allowed_as_proof"],
            requirements,
            "Invalid affordance proof flag; defaulting to uncertain.",
        )
    if missing_required:
        return status_decision(
            "uncertain",
            ["missing_point_or_normal_evidence"],
            requirements,
            "Required point/contact/normal evidence is missing.",
        )

    if subtype == "attached_to_vertical_or_overhead_surface":
        if (
            contact_sufficient
            and surface_type in {"wall", "ceiling", "fixture", "furniture", "object_part"}
            and normal_class in {"vertical", "horizontal_down", "slanted"}
        ):
            return status_decision(
                "satisfied",
                [
                    "near_contact_points_present",
                    "contact_patch_score_sufficient",
                    "surface_type_matches_subtype",
                    "surface_normal_matches_subtype",
                ],
                requirements,
                "Attachment evidence has direct contact with a plausible vertical/overhead surface.",
            )
        if surface_type == "floor" and clear_far and class_prior != "plausible":
            return status_decision(
                "violated",
                [
                    "clear_far_from_attachment_surface",
                    "no_near_contact_points",
                    "surface_type_contradicts_predicate",
                ],
                requirements,
                "Attachment is clearly far from the candidate surface and the surface type contradicts the predicate.",
            )
        return status_decision(
            "uncertain",
            ["distance_in_uncertain_band" if not clear_far else "class_prior_only_not_allowed_as_proof"],
            requirements,
            "Evidence is not strong enough for satisfied or violated.",
        )

    if subtype == "attached_to_furniture_or_fixture":
        if contact_sufficient and surface_type in {"furniture", "fixture", "object_part"}:
            return status_decision(
                "satisfied",
                [
                    "near_contact_points_present",
                    "contact_patch_score_sufficient",
                    "surface_type_matches_subtype",
                ],
                requirements,
                "Attachment evidence has direct contact with furniture/fixture/object-part surface.",
            )
        if clear_far and surface_type in {"floor", "unknown"} and class_prior != "plausible":
            return status_decision(
                "violated",
                [
                    "clear_far_from_attachment_surface",
                    "no_near_contact_points",
                    "surface_type_contradicts_predicate",
                ],
                requirements,
                "Attachment candidate is clearly far from a plausible attachment surface.",
            )
        return status_decision(
            "uncertain",
            ["distance_in_uncertain_band"],
            requirements,
            "Functional attachment may be occluded or part-mediated.",
        )

    if subtype == "ambiguous_functional_attachment":
        if clear_far and surface_type in {"floor", "unknown"} and class_prior == "implausible":
            return status_decision(
                "violated",
                [
                    "clear_far_from_attachment_surface",
                    "no_near_contact_points",
                    "surface_type_contradicts_predicate",
                ],
                requirements,
                "Ambiguous attachment has clear negative geometry and implausible surface context.",
            )
        return status_decision(
            "uncertain",
            ["ambiguous_functional_attachment"],
            requirements,
            "Ambiguous functional attachment defaults to uncertain.",
        )

    if subtype == "hanging_from_vertical_surface":
        if (
            contact_sufficient
            and surface_type in {"wall", "fixture", "furniture", "object_part"}
            and normal_class in {"vertical", "slanted"}
            and floor_clearance is not None
            and floor_clearance >= thresholds["min_floor_clearance"]
            and support_score <= thresholds["max_support_no_contra"]
        ):
            return status_decision(
                "satisfied",
                [
                    "near_contact_points_present",
                    "surface_type_matches_subtype",
                    "surface_normal_matches_subtype",
                    "hanging_gravity_cue_present",
                    "no_strong_contradictory_support",
                ],
                requirements,
                "Hanging evidence has contact with a vertical/slanted surface and no strong support contradiction.",
            )
        if (
            surface_type == "floor"
            and normal_class == "horizontal_up"
            and hanging_score <= 0.20
        ) or support_contradicts_hanging or clear_far:
            return status_decision(
                "violated",
                [
                    "floor_or_table_support_contradicts_hanging",
                    "hanging_gravity_cue_absent",
                ]
                + (["clear_far_from_attachment_surface", "no_near_contact_points"] if clear_far else []),
                requirements,
                "Hanging is contradicted by floor/table support or clear separation from a plausible surface.",
            )
        return status_decision(
            "uncertain",
            ["ambiguous_draped_or_occluded_hanging"],
            requirements,
            "Hanging evidence is not decisive.",
        )

    if subtype == "hanging_from_overhead_or_fixture":
        if (
            direct_contact
            and surface_type in {"ceiling", "fixture", "object_part"}
            and normal_class in {"horizontal_down", "vertical", "slanted"}
            and floor_clearance is not None
            and floor_clearance >= thresholds["min_floor_clearance"]
            and support_score <= thresholds["max_support_no_contra"]
        ):
            return status_decision(
                "satisfied",
                [
                    "near_contact_points_present",
                    "surface_type_matches_subtype",
                    "surface_normal_matches_subtype",
                    "hanging_gravity_cue_present",
                    "no_strong_contradictory_support",
                ],
                requirements,
                "Hanging evidence has direct contact with an overhead/fixture surface.",
            )
        if support_contradicts_hanging or (
            clear_far and surface_type not in {"ceiling", "fixture", "object_part"}
        ):
            return status_decision(
                "violated",
                [
                    "floor_or_table_support_contradicts_hanging",
                    "hanging_gravity_cue_absent",
                ]
                + (["clear_far_from_attachment_surface", "no_near_contact_points"] if clear_far else []),
                requirements,
                "Hanging from overhead/fixture is contradicted by support or clear separation.",
            )
        return status_decision(
            "uncertain",
            ["possible_occluded_connector_or_fastener"],
            requirements,
            "Thin wires, hooks, or occluded connectors may be missing.",
        )

    if subtype == "ambiguous_draped_or_occluded_hanging":
        if (
            surface_type == "floor"
            and normal_class == "horizontal_up"
            and hanging_score <= 0.20
        ) or (
            clear_far
            and floor_clearance is not None
            and floor_clearance < thresholds["min_floor_clearance"]
        ):
            return status_decision(
                "violated",
                [
                    "floor_or_table_support_contradicts_hanging",
                    "hanging_gravity_cue_absent",
                ]
                + (["clear_far_from_attachment_surface", "no_near_contact_points"] if clear_far else []),
                requirements,
                "Ambiguous hanging has clear contradiction from floor support or low clearance.",
            )
        return status_decision(
            "uncertain",
            ["ambiguous_draped_or_occluded_hanging"],
            requirements,
            "Ambiguous or occluded hanging defaults to uncertain.",
        )

    if subtype == "connected_adjacent_or_contiguous":
        if contact_sufficient:
            return status_decision(
                "satisfied",
                ["connected_adjacent_contact", "near_contact_points_present"],
                requirements,
                "Connected pair has direct contact or sufficient contact patch.",
            )
        if clear_far:
            return status_decision(
                "violated",
                ["connected_pair_far_apart", "no_near_contact_points"],
                requirements,
                "Connected pair is clearly far apart.",
            )
        return status_decision(
            "uncertain",
            ["possible_occluded_connector_or_fastener"],
            requirements,
            "Connection may be hidden, part-mediated, or sparse.",
        )

    if subtype == "connected_by_fixture_or_part":
        if contact_sufficient and surface_type in {"fixture", "furniture", "object_part"}:
            return status_decision(
                "satisfied",
                ["connected_adjacent_contact", "near_contact_points_present", "surface_type_matches_subtype"],
                requirements,
                "Connected pair has contact with a plausible fixture/furniture/object-part surface.",
            )
        if clear_far and surface_type in {"floor", "unknown"}:
            return status_decision(
                "violated",
                ["connected_pair_far_apart", "no_near_contact_points"],
                requirements,
                "Connected pair is clearly far apart from a plausible connector.",
            )
        return status_decision(
            "uncertain",
            ["possible_occluded_connector_or_fastener"],
            requirements,
            "Intermediate connector or object part may be missing.",
        )

    if subtype == "ambiguous_functional_connection":
        if clear_far and class_prior != "plausible":
            return status_decision(
                "violated",
                ["connected_pair_far_apart", "no_near_contact_points"],
                requirements,
                "Ambiguous functional connection has clear negative geometry.",
            )
        return status_decision(
            "uncertain",
            ["ambiguous_functional_connection"],
            requirements,
            "Functional connection defaults to uncertain.",
        )

    return status_decision(
        "uncertain",
        ["surface_type_unknown"],
        requirements,
        "Subtype is unknown under the frozen policy.",
    )


def decision_row(row: dict[str, Any], thresholds: dict[str, float]) -> dict[str, Any]:
    result = evaluate_policy(row, thresholds)
    return {
        "schema_version": DECISION_SCHEMA_VERSION,
        "policy_name": POLICY_NAME,
        "policy_version": POLICY_VERSION,
        "row_id": row["row_id"],
        "source_name": row["source_name"],
        "scan_id": row["scan_id"],
        "subgraph_id": row["subgraph_id"],
        "subject_id": row["subject_id"],
        "object_id": row["object_id"],
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "subtype_hint": row["subtype_hint"],
        **result,
    }


def validate_decision_rows(rows: list[dict[str, Any]], schema: dict[str, Any]) -> list[dict[str, Any]]:
    required = set(schema["required"])
    allowed = set(schema["properties"])
    forbidden = set(schema.get("forbidden_fields", []))
    errors: list[dict[str, Any]] = []
    for row in rows:
        row_errors = []
        missing = required - set(row)
        extra = set(row) - allowed
        present_forbidden = forbidden & set(row)
        if missing:
            row_errors.extend(f"missing_required:{field}" for field in sorted(missing))
        if extra:
            row_errors.extend(f"extra_field:{field}" for field in sorted(extra))
        if present_forbidden:
            row_errors.extend(f"forbidden_field:{field}" for field in sorted(present_forbidden))
        if row.get("schema_version") != DECISION_SCHEMA_VERSION:
            row_errors.append("bad_schema_version")
        if row.get("policy_name") != POLICY_NAME:
            row_errors.append("bad_policy_name")
        if row.get("policy_version") != POLICY_VERSION:
            row_errors.append("bad_policy_version")
        if row.get("predicate_label") not in PREDICATE_LABELS:
            row_errors.append("predicate_label_out_of_scope")
        if row.get("predicate_family") != TARGET_FAMILY:
            row_errors.append("predicate_family_out_of_scope")
        if row.get("verification_status") not in {"satisfied", "violated", "uncertain"}:
            row_errors.append("bad_verification_status")
        if row_errors:
            errors.append({"row_id": row.get("row_id"), "errors": row_errors})
    return errors


def count_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: value for key, value in sorted(counter.items())}


def nested_count_dict(counter: dict[str, Counter[str]]) -> dict[str, dict[str, int]]:
    return {key: count_dict(value) for key, value in sorted(counter.items())}


def decision_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_status = Counter(row["verification_status"] for row in rows)
    by_label_status: dict[str, Counter[str]] = defaultdict(Counter)
    by_source_status: dict[str, Counter[str]] = defaultdict(Counter)
    by_subtype_status: dict[str, Counter[str]] = defaultdict(Counter)
    reason_counts: Counter[str] = Counter()
    for row in rows:
        by_label_status[row["predicate_label"]][row["verification_status"]] += 1
        by_source_status[row["source_name"]][row["verification_status"]] += 1
        by_subtype_status[row["subtype_hint"]][row["verification_status"]] += 1
        for reason in row["reason_codes"]:
            reason_counts[reason] += 1
    return {
        "rows": len(rows),
        "by_status": count_dict(by_status),
        "by_label_status": nested_count_dict(by_label_status),
        "by_source_status": nested_count_dict(by_source_status),
        "by_subtype_status": nested_count_dict(by_subtype_status),
        "reason_counts": count_dict(reason_counts),
    }


def safe_rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def build_eval_rows(
    *,
    positive_seeds: list[dict[str, Any]],
    negative_seeds: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seed_rows = positive_seeds + negative_seeds
    if len(seed_rows) != len(decisions):
        raise ValueError("seed_decision_length_mismatch")
    eval_rows: list[dict[str, Any]] = []
    for seed, decision in zip(seed_rows, decisions, strict=True):
        target = int(seed["label"]["geom_valid"])
        status = decision["verification_status"]
        if target == 1:
            verdict = "correct_nonviolated" if status != "violated" else "false_violation"
        else:
            verdict = "correct_nonsatisfied" if status != "satisfied" else "false_satisfaction"
        eval_rows.append(
            {
                "schema_version": "h001_attachment_deferred_gt_policy_eval_row_v1",
                "seed_id": seed.get("seed_id") or seed.get("negative_id"),
                "record_type": seed["record_type"],
                "split_role": seed["split_role"],
                "strategy": seed.get("strategy"),
                "target_geom_valid": target,
                "eval_verdict": verdict,
                "decision": decision,
            }
        )
    return eval_rows


def gt_eval_summary(eval_rows: list[dict[str, Any]]) -> dict[str, Any]:
    positives = [row for row in eval_rows if row["target_geom_valid"] == 1]
    negatives = [row for row in eval_rows if row["target_geom_valid"] == 0]
    pos_status = Counter(row["decision"]["verification_status"] for row in positives)
    neg_status = Counter(row["decision"]["verification_status"] for row in negatives)
    by_label_status: dict[str, Counter[str]] = defaultdict(Counter)
    by_strategy_status: dict[str, Counter[str]] = defaultdict(Counter)
    by_split_target_status: dict[str, Counter[str]] = defaultdict(Counter)
    for row in eval_rows:
        decision = row["decision"]
        by_label_status[decision["predicate_label"]][decision["verification_status"]] += 1
        split_target = f"{row['split_role']}:target_{row['target_geom_valid']}"
        by_split_target_status[split_target][decision["verification_status"]] += 1
        if row.get("strategy"):
            by_strategy_status[row["strategy"]][decision["verification_status"]] += 1
    return {
        "rows": len(eval_rows),
        "positive_rows": len(positives),
        "counterfactual_rows": len(negatives),
        "positive_status_counts": count_dict(pos_status),
        "counterfactual_status_counts": count_dict(neg_status),
        "positive_nonviolated_rate": safe_rate(
            len([row for row in positives if row["decision"]["verification_status"] != "violated"]),
            len(positives),
        ),
        "positive_strict_satisfied_rate": safe_rate(pos_status.get("satisfied", 0), len(positives)),
        "counterfactual_nonsatisfied_rate": safe_rate(
            len([row for row in negatives if row["decision"]["verification_status"] != "satisfied"]),
            len(negatives),
        ),
        "counterfactual_strict_violated_rate": safe_rate(neg_status.get("violated", 0), len(negatives)),
        "counterfactual_calibration_negative_ready_rows": neg_status.get("violated", 0),
        "uncertain_rate_all": safe_rate(
            len([row for row in eval_rows if row["decision"]["verification_status"] == "uncertain"]),
            len(eval_rows),
        ),
        "by_label_status": nested_count_dict(by_label_status),
        "by_strategy_status": nested_count_dict(by_strategy_status),
        "by_split_target_status": nested_count_dict(by_split_target_status),
        "metric_boundary": {
            "p_geom_valid_auc_available": False,
            "reason": "no decision-to-probability calibrator fitted in G4",
        },
    }


def visual_sanity_plan(eval_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "planned_not_run",
        "purpose": "targeted visual sanity check for attachment/hanging/connection policy failures",
        "recommended_queue_size": 50,
        "sampling_priority": [
            "false_violation positives",
            "false_satisfaction counterfactuals",
            "strict violated counterfactuals used as calibration-ready negatives",
            "uncertain hanging cases with floor/table support contradiction",
            "connected-to cases because positive count is small",
        ],
        "current_eval_summary_pointer": {
            "positive_nonviolated_rate": eval_summary["positive_nonviolated_rate"],
            "counterfactual_nonsatisfied_rate": eval_summary["counterfactual_nonsatisfied_rate"],
            "uncertain_rate_all": eval_summary["uncertain_rate_all"],
        },
        "claim_boundary": "required before promoting attachment_deferred into the main AAAI claim",
    }


def commands_md() -> str:
    return """# Attachment Deferred G4 GT Policy Smoke Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm \\
  attachment_deferred_gt_policy_smoke
```

Validation:

```bash
python -m py_compile experiments/H001_geom_reliability/scripts/run_attachment_gt_policy_smoke.py
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/gt_policy_smoke/manifest.json >/dev/null
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/gt_policy_smoke/summary.json >/dev/null
```

This command applies the frozen policy to smoke and train-dev GT/counterfactual
rows only. It does not run VL-SAT/Open3DSG attachment source metrics, fit
calibration, or update the main AAAI claim.
"""


def report_md(manifest: dict[str, Any], summary: dict[str, Any]) -> str:
    gt = summary["gt_eval"]
    smoke = summary["policy_smoke"]
    lines = [
        "# Attachment Deferred G4 GT Policy Smoke",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Claim Boundary",
        "",
        "This is a G4 policy-smoke and train-dev GT/counterfactual verifier",
        "evaluation artifact. It does not run source metrics, fit calibration,",
        "score VL-SAT/Open3DSG predictions, or change the current AAAI main",
        "claim.",
        "",
        "## G1c Policy Smoke",
        "",
        f"- rows: `{smoke['rows']}`",
        f"- status counts: `{smoke['by_status']}`",
        "",
        "## Train/Dev GT-Counterfactual Evaluation",
        "",
        f"- rows: `{gt['rows']}`",
        f"- positives: `{gt['positive_rows']}`",
        f"- counterfactuals: `{gt['counterfactual_rows']}`",
        f"- positive nonviolated rate: `{gt['positive_nonviolated_rate']}`",
        f"- positive strict satisfied rate: `{gt['positive_strict_satisfied_rate']}`",
        f"- counterfactual nonsatisfied rate: `{gt['counterfactual_nonsatisfied_rate']}`",
        f"- counterfactual strict violated rate: `{gt['counterfactual_strict_violated_rate']}`",
        f"- calibration-ready counterfactual negatives: `{gt['counterfactual_calibration_negative_ready_rows']}`",
        f"- uncertain rate all: `{gt['uncertain_rate_all']}`",
        "",
        "## Important Interpretation",
        "",
        "`positive_nonviolated_rate` and `counterfactual_nonsatisfied_rate` are",
        "conservative policy checks. `uncertain` is counted as nonviolated for",
        "positives and nonsatisfied for counterfactuals, but uncertain rows are",
        "not calibration-ready proof. A fitted `p_geom_valid` calibrator, source",
        "metrics, controls, bootstrap CI, and visual audit remain required before",
        "any main-claim promotion.",
        "",
        "## Next Gate",
        "",
        f"`{manifest['next_gate']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    dataset_root = args.dataset_root if args.dataset_root.is_absolute() else repo_root / args.dataset_root
    calibration_dir = args.calibration_dir if args.calibration_dir.is_absolute() else repo_root / args.calibration_dir
    verifier_policy_dir = (
        args.verifier_policy_dir if args.verifier_policy_dir.is_absolute() else repo_root / args.verifier_policy_dir
    )
    point_surface_dir = (
        args.point_surface_dir if args.point_surface_dir.is_absolute() else repo_root / args.point_surface_dir
    )
    out = args.out if args.out.is_absolute() else repo_root / args.out

    required_inputs = [
        calibration_dir / "manifest.json",
        calibration_dir / "positive_seeds.jsonl",
        calibration_dir / "counterfactual_seeds.jsonl",
        verifier_policy_dir / "manifest.json",
        verifier_policy_dir / "verifier_policy.json",
        verifier_policy_dir / "decision_schema.json",
        point_surface_dir / "manifest.json",
        point_surface_dir / "rows.jsonl",
    ]
    for path in required_inputs:
        if not path.exists():
            raise FileNotFoundError(f"missing input artifact: {path}")

    calibration_manifest = read_json(calibration_dir / "manifest.json")
    policy_manifest = read_json(verifier_policy_dir / "manifest.json")
    point_surface_manifest = read_json(point_surface_dir / "manifest.json")
    if calibration_manifest.get("status") != "attachment_deferred_calibration_counterfactual_plan_ready_no_fit_no_metrics":
        raise ValueError(f"unexpected_calibration_status:{calibration_manifest.get('status')}")
    if policy_manifest.get("status") != "attachment_deferred_verifier_policy_ready_no_decisions_no_metrics":
        raise ValueError(f"unexpected_policy_status:{policy_manifest.get('status')}")
    if point_surface_manifest.get("status") != "attachment_deferred_point_surface_validation_ready_no_verifier":
        raise ValueError(f"unexpected_point_surface_status:{point_surface_manifest.get('status')}")

    policy = read_json(verifier_policy_dir / "verifier_policy.json")
    decision_schema = read_json(verifier_policy_dir / "decision_schema.json")
    thresholds = policy_thresholds(policy)

    smoke_evidence_rows = list(iter_jsonl(point_surface_dir / "rows.jsonl"))
    smoke_decisions = [decision_row(row, thresholds) for row in smoke_evidence_rows]

    positive_seeds = list(iter_jsonl(calibration_dir / "positive_seeds.jsonl"))
    negative_seeds = list(iter_jsonl(calibration_dir / "counterfactual_seeds.jsonl"))
    source_rows = [seed_to_source_row(seed, "gt_positive_train_dev") for seed in positive_seeds]
    source_rows.extend(seed_to_source_row(seed, "counterfactual_train_dev") for seed in negative_seeds)
    evidence_rows, diagnostics, evidence_meta = build_point_surface_evidence(
        source_rows=source_rows,
        dataset_root=dataset_root,
        contact_threshold_m=args.contact_threshold_m,
        max_points_per_object=args.max_points_per_object,
    )
    gt_decisions = [decision_row(row, thresholds) for row in evidence_rows]
    eval_rows = build_eval_rows(
        positive_seeds=positive_seeds,
        negative_seeds=negative_seeds,
        decisions=gt_decisions,
    )

    validation_errors = {
        "smoke_decision_errors": validate_decision_rows(smoke_decisions, decision_schema),
        "gt_decision_errors": validate_decision_rows(gt_decisions, decision_schema),
    }
    all_errors = validation_errors["smoke_decision_errors"] + validation_errors["gt_decision_errors"]

    ready_evidence_rows = sum(1 for row in evidence_rows if row.get("extractor_status") == "ready")
    point_available_rows = sum(1 for row in evidence_rows if row.get("geometry_available", {}).get("points"))
    normal_available_rows = sum(1 for row in evidence_rows if row.get("geometry_available", {}).get("normals"))
    partial = bool(all_errors or evidence_meta["scan_errors"] or ready_evidence_rows != len(evidence_rows))
    status = STATUS_PARTIAL if partial else STATUS_READY
    next_gate = NEXT_GATE_PARTIAL if partial else NEXT_GATE_READY

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "policy_smoke": decision_summary(smoke_decisions),
        "gt_eval": gt_eval_summary(eval_rows),
        "evidence_counts": {
            "gt_evidence_rows": len(evidence_rows),
            "ready_rows": ready_evidence_rows,
            "point_available_rows": point_available_rows,
            "normal_available_rows": normal_available_rows,
            "scan_errors": len(evidence_meta["scan_errors"]),
        },
        "evidence_meta": evidence_meta,
        "thresholds": thresholds,
    }
    visual_plan = visual_sanity_plan(summary["gt_eval"])
    blockers = [
        "calibrator_not_fit",
        "p_geom_valid_not_available",
        "source_metrics_not_run",
        "controls_not_run",
        "bootstrap_ci_not_run",
        "targeted_visual_sanity_not_run",
        "main_AAAI_claim_requires_user_confirmation_before_attachment_promotion",
    ]
    if partial:
        blockers.insert(0, "point_surface_evidence_not_ready_for_all_train_dev_rows")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": utc_now(),
        "claim_boundary": {
            "current_main_claim_unchanged": True,
            "artifact_type": "gt_policy_smoke_and_counterfactual_eval",
            "decision_rows_emitted": True,
            "calibration_fitted": False,
            "source_predictions_scored": False,
            "source_metrics_computed": False,
            "metric_evidence_for_current_paper": False,
            "requires_user_confirmation_before_main_claim_promotion": True,
        },
        "inputs": {
            "calibration_manifest": relpath(repo_root, calibration_dir / "manifest.json"),
            "positive_seeds": relpath(repo_root, calibration_dir / "positive_seeds.jsonl"),
            "counterfactual_seeds": relpath(repo_root, calibration_dir / "counterfactual_seeds.jsonl"),
            "policy_manifest": relpath(repo_root, verifier_policy_dir / "manifest.json"),
            "verifier_policy": relpath(repo_root, verifier_policy_dir / "verifier_policy.json"),
            "decision_schema": relpath(repo_root, verifier_policy_dir / "decision_schema.json"),
            "point_surface_rows": relpath(repo_root, point_surface_dir / "rows.jsonl"),
            "dataset_root": relpath(repo_root, dataset_root),
        },
        "settings": {
            "contact_threshold_m": args.contact_threshold_m,
            "max_points_per_object": args.max_points_per_object,
            "policy_name": POLICY_NAME,
            "policy_version": POLICY_VERSION,
        },
        "outputs": {
            "manifest": "manifest.json",
            "summary": "summary.json",
            "validation": "validation.json",
            "policy_smoke_decisions": "policy_smoke_decisions.jsonl",
            "gt_evidence_rows": "gt_evidence_rows.jsonl",
            "gt_evidence_diagnostics": "gt_evidence_diagnostics.jsonl",
            "gt_policy_decisions": "gt_policy_decisions.jsonl",
            "gt_eval_rows": "gt_eval_rows.jsonl",
            "visual_sanity_plan": "visual_sanity_plan.json",
            "commands": "commands.md",
            "report": "report.md",
        },
        "blockers": blockers,
        "next_gate": next_gate,
    }
    validation = {
        "status": "passed" if not all_errors else "failed",
        "smoke_decision_errors": validation_errors["smoke_decision_errors"],
        "gt_decision_errors": validation_errors["gt_decision_errors"],
        "scan_errors": evidence_meta["scan_errors"],
        "checked_smoke_decision_rows": len(smoke_decisions),
        "checked_gt_decision_rows": len(gt_decisions),
    }

    ensure_dir(out)
    write_json(out / "manifest.json", manifest)
    write_json(out / "summary.json", summary)
    write_json(out / "validation.json", validation)
    write_json(out / "visual_sanity_plan.json", visual_plan)
    write_jsonl(out / "policy_smoke_decisions.jsonl", smoke_decisions)
    write_jsonl(out / "gt_evidence_rows.jsonl", evidence_rows)
    write_jsonl(out / "gt_evidence_diagnostics.jsonl", diagnostics)
    write_jsonl(out / "gt_policy_decisions.jsonl", gt_decisions)
    write_jsonl(out / "gt_eval_rows.jsonl", eval_rows)
    write_text(out / "commands.md", commands_md())
    write_text(out / "report.md", report_md(manifest, summary))

    print(
        json.dumps(
            {
                "status": status,
                "out": relpath(repo_root, out),
                "smoke_rows": len(smoke_decisions),
                "gt_rows": len(gt_decisions),
                "positive_nonviolated_rate": summary["gt_eval"]["positive_nonviolated_rate"],
                "counterfactual_nonsatisfied_rate": summary["gt_eval"]["counterfactual_nonsatisfied_rate"],
            },
            sort_keys=True,
        )
    )
    return 0 if not all_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
