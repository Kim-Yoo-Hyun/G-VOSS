#!/usr/bin/env python3
"""Apply H001 rules v0 to one-scan geometry evidence.

Phase B only: this script adds deterministic verifier decisions to Phase A
edge evidence records. It is a smoke-test verifier, not a benchmark pipeline.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PRIMARY_FAMILIES = {"support_contact", "proximity", "relative_vertical"}
DEFERRED_FAMILIES = {"attachment_deferred", "size_comparison_deferred"}
ALLOWED_STATUSES = {"satisfied", "violated", "uncertain", "unsupported"}
STATUS_ALIAS = {
    "satisfied": "pass",
    "violated": "fail",
    "uncertain": "uncertain",
    "unsupported": "not_applicable",
}
HORIZONTAL_CANDIDATE_KEYS = {
    "left": "left_candidate",
    "right": "right_candidate",
    "front": "front_candidate",
    "behind": "behind_candidate",
}
LARGE_PLANAR_OR_ROOM_LABELS = {
    "ceiling",
    "door",
    "floor",
    "room",
    "wall",
    "window",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply h001-rules-v0 to Phase A one-scan edge evidence."
    )
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            stripped = line.strip()
            if stripped:
                record = json.loads(stripped)
                record["_source_line"] = line_number
                records.append(record)
    return records


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def bool_score(values: list[bool | None]) -> float | None:
    if any(value is None for value in values):
        return None
    if not values:
        return None
    return sum(1.0 for value in values if value) / len(values)


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def label_is_large_planar_or_room(label: Any) -> bool:
    normalized = str(label or "").strip().lower()
    return normalized in LARGE_PLANAR_OR_ROOM_LABELS


def base_verification(
    edge: dict[str, Any],
    thresholds: dict[str, Any],
    status: str,
    geometry_score: float | None,
    checked_constraints: list[str],
    passed_constraints: list[str],
    failed_constraints: list[str],
    uncertain_constraints: list[str],
    reason_codes: list[str],
    diagnostic_only: bool = False,
    diagnostic_status: str | None = None,
) -> dict[str, Any]:
    family = edge.get("predicate_family")
    primary_metric_eligible = family in PRIMARY_FAMILIES and status in {"satisfied", "violated"}
    verification = {
        "rule_version": thresholds.get("rule_version", "h001-rules-v0"),
        "status": status,
        "status_alias": STATUS_ALIAS[status],
        "predicate_family": family,
        "primary_metric_eligible": primary_metric_eligible,
        "diagnostic_only": diagnostic_only,
        "geometry_score": geometry_score,
        "checked_constraints": checked_constraints,
        "passed_constraints": passed_constraints,
        "failed_constraints": failed_constraints,
        "uncertain_constraints": uncertain_constraints,
        "reason_codes": sorted(set(reason_codes)),
        "threshold_config": thresholds,
        "frame_assumption": thresholds.get("frame_assumption", "scene_xyz_v0"),
        "z_axis_assumption": thresholds.get("z_axis_assumption", "scene_z_up_v0"),
    }
    if diagnostic_status is not None:
        verification["diagnostic_status"] = diagnostic_status
    return verification


def missing_or_unsupported_precheck(
    edge: dict[str, Any],
    thresholds: dict[str, Any],
) -> dict[str, Any] | None:
    if not edge.get("geometry_available", False):
        return base_verification(
            edge,
            thresholds,
            "uncertain",
            None,
            [],
            [],
            [],
            ["geometry_available"],
            ["missing_geometry"],
        )
    if edge.get("missing_fields"):
        return base_verification(
            edge,
            thresholds,
            "uncertain",
            None,
            [],
            [],
            [],
            list(edge["missing_fields"]),
            ["missing_required_fields"],
        )

    family = edge.get("predicate_family")
    if family == "unsupported_first_pass":
        return base_verification(
            edge,
            thresholds,
            "unsupported",
            None,
            [],
            [],
            [],
            [],
            ["unsupported_predicate"],
        )
    if family in DEFERRED_FAMILIES:
        return base_verification(
            edge,
            thresholds,
            "unsupported",
            None,
            [],
            [],
            [],
            [],
            ["deferred_predicate_family"],
        )
    return None


def apply_support_contact(edge: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    inputs = edge.get("rule_inputs", {})
    is_above = safe_bool(inputs.get("is_subject_above_object"))
    small_gap = safe_bool(inputs.get("small_vertical_gap_candidate"))
    has_overlap = safe_bool(inputs.get("has_projected_overlap_candidate"))
    constraints = {
        "is_above_or_touching": is_above,
        "small_vertical_gap": small_gap,
        "has_projected_overlap": has_overlap,
    }

    checked = list(constraints)
    passed = [name for name, passed_value in constraints.items() if passed_value is True]
    failed = [name for name, passed_value in constraints.items() if passed_value is False]
    uncertain = [name for name, passed_value in constraints.items() if passed_value is None]
    score = bool_score(list(constraints.values()))

    if uncertain:
        return base_verification(
            edge,
            thresholds,
            "uncertain",
            score,
            checked,
            passed,
            failed,
            uncertain,
            ["missing_required_fields", "support_contact_requires_manual_inspection"],
        )

    large_support_object = label_is_large_planar_or_room(edge.get("object_label"))
    high_risk_gap_only = (
        large_support_object
        and small_gap is False
        and is_above is True
        and has_overlap is True
    )
    if high_risk_gap_only:
        return base_verification(
            edge,
            thresholds,
            "uncertain",
            score,
            checked,
            passed,
            failed,
            ["small_vertical_gap"],
            [
                "support_object_aabb_too_coarse",
                "support_contact_requires_manual_inspection",
            ],
        )

    if not failed:
        return base_verification(
            edge,
            thresholds,
            "satisfied",
            score,
            checked,
            passed,
            [],
            [],
            ["support_constraints_passed"],
        )

    reason_codes = ["support_contact_requires_manual_inspection"]
    if "is_above_or_touching" in failed:
        reason_codes.append("support_subject_not_above_object")
    if "small_vertical_gap" in failed:
        reason_codes.append("support_vertical_gap_too_large")
    if "has_projected_overlap" in failed:
        reason_codes.append("support_projected_overlap_too_low")

    return base_verification(
        edge,
        thresholds,
        "violated",
        score,
        checked,
        passed,
        failed,
        [],
        reason_codes,
    )


def apply_proximity(edge: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    inputs = edge.get("rule_inputs", {})
    evidence = edge.get("geometry_evidence", {})
    normalized_distance = safe_float(
        evidence.get("distances", {}).get("normalized_distance_xy")
    )
    near = safe_bool(inputs.get("near_by_normalized_distance_candidate"))
    checked = ["near_by_normalized_distance"]
    passed = checked if near is True else []
    failed = checked if near is False else []
    uncertain = checked if near is None else []

    if normalized_distance is None:
        score = None
    else:
        max_distance = float(thresholds["near_distance_norm_max"])
        score = clamp(1.0 - normalized_distance / max_distance)

    if near is None:
        return base_verification(
            edge,
            thresholds,
            "uncertain",
            score,
            checked,
            passed,
            failed,
            uncertain,
            ["missing_required_fields"],
        )

    if near:
        return base_verification(
            edge,
            thresholds,
            "satisfied",
            score,
            checked,
            passed,
            failed,
            [],
            ["proximity_distance_within_threshold"],
        )

    if label_is_large_planar_or_room(edge.get("subject_label")) or label_is_large_planar_or_room(edge.get("object_label")):
        return base_verification(
            edge,
            thresholds,
            "uncertain",
            score,
            checked,
            passed,
            failed,
            ["large_object_distance"],
            ["proximity_large_object_uncertain"],
        )

    return base_verification(
        edge,
        thresholds,
        "violated",
        score,
        checked,
        passed,
        failed,
        [],
        ["proximity_distance_above_threshold"],
    )


def apply_relative_vertical(edge: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    inputs = edge.get("rule_inputs", {})
    evidence = edge.get("geometry_evidence", {})
    predicate = edge.get("predicate_label")
    higher = safe_bool(inputs.get("higher_than_candidate"))
    lower = safe_bool(inputs.get("lower_than_candidate"))
    normalized_delta = safe_float(
        evidence.get("vertical", {}).get("normalized_center_delta_z")
    )

    if predicate == "higher than":
        target_key = "higher_than_candidate"
        target_value = higher
        opposite_value = lower
    elif predicate == "lower than":
        target_key = "lower_than_candidate"
        target_value = lower
        opposite_value = higher
    else:
        return base_verification(
            edge,
            thresholds,
            "unsupported",
            None,
            [],
            [],
            [],
            [],
            ["unsupported_predicate"],
        )

    checked = [target_key]
    score = None
    if normalized_delta is not None:
        score = clamp(abs(normalized_delta) / float(thresholds["relative_z_margin_norm"]))

    if target_value is True:
        return base_verification(
            edge,
            thresholds,
            "satisfied",
            score,
            checked,
            checked,
            [],
            [],
            ["vertical_order_matches"],
        )
    if opposite_value is True:
        return base_verification(
            edge,
            thresholds,
            "violated",
            score,
            checked,
            [],
            checked,
            [],
            ["vertical_order_opposite"],
        )

    return base_verification(
        edge,
        thresholds,
        "uncertain",
        score,
        checked,
        [],
        [],
        ["vertical_margin"],
        ["vertical_margin_too_small"],
    )


def apply_relative_horizontal(edge: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    inputs = edge.get("rule_inputs", {})
    predicate = edge.get("predicate_label")
    candidate_key = HORIZONTAL_CANDIDATE_KEYS.get(str(predicate))
    checked = [candidate_key] if candidate_key else []
    candidate_value = safe_bool(inputs.get(candidate_key)) if candidate_key else None

    passed = checked if candidate_value is True else []
    failed = checked if candidate_value is False else []
    uncertain = checked if candidate_value is None and checked else ["coordinate_frame"]
    diagnostic_status = "diagnostic_uncertain"
    reason_codes = ["horizontal_frame_not_validated"]
    score = None

    if candidate_value is True:
        diagnostic_status = "diagnostic_satisfied"
        reason_codes.append("horizontal_candidate_matches")
        score = 1.0
    elif candidate_value is False:
        diagnostic_status = "diagnostic_violated"
        reason_codes.append("horizontal_candidate_conflicts")
        score = 0.0

    if "coordinate_frame" not in uncertain:
        uncertain.append("coordinate_frame")

    return base_verification(
        edge,
        thresholds,
        "uncertain",
        score,
        checked,
        passed,
        failed,
        uncertain,
        reason_codes,
        diagnostic_only=True,
        diagnostic_status=diagnostic_status,
    )


def apply_rules(edge: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    precheck = missing_or_unsupported_precheck(edge, thresholds)
    if precheck is not None:
        return precheck

    family = edge.get("predicate_family")
    if family == "support_contact":
        return apply_support_contact(edge, thresholds)
    if family == "proximity":
        return apply_proximity(edge, thresholds)
    if family == "relative_vertical":
        return apply_relative_vertical(edge, thresholds)
    if family == "relative_horizontal":
        return apply_relative_horizontal(edge, thresholds)
    return base_verification(
        edge,
        thresholds,
        "unsupported",
        None,
        [],
        [],
        [],
        [],
        ["unsupported_predicate"],
    )


def key_geometry_evidence(edge: dict[str, Any]) -> dict[str, Any]:
    evidence = edge.get("geometry_evidence", {})
    return {
        "delta_xyz": evidence.get("centers", {}).get("delta_xyz"),
        "distance_xy": evidence.get("distances", {}).get("distance_xy"),
        "normalized_distance_xy": evidence.get("distances", {}).get("normalized_distance_xy"),
        "normalized_center_delta_z": evidence.get("vertical", {}).get("normalized_center_delta_z"),
        "vertical_gap_subject_on_object": evidence.get("vertical", {}).get("vertical_gap_subject_on_object"),
        "projected_subject_overlap_ratio": evidence.get("overlap", {}).get("projected_subject_overlap_ratio"),
    }


def manual_question(record: dict[str, Any]) -> str:
    family = record.get("predicate_family")
    if family == "support_contact":
        return "Does floor/wall geometry make the top-contact rule invalid?"
    if family == "proximity":
        return "Does the relation label look semantic rather than metric?"
    if family == "relative_vertical":
        return "Is the z-axis ordering plausible for this pair?"
    if family == "relative_horizontal":
        return "Is this horizontal relation scene-axis-relative or viewpoint/object-centric?"
    return "Should this edge be included in Phase B manual review?"


def manual_queue_record(record: dict[str, Any], selection_reason: str) -> dict[str, Any]:
    verification = record["verification"]
    return {
        "edge_id": record["edge_id"],
        "subject_label": record.get("subject_label"),
        "predicate_label": record.get("predicate_label"),
        "object_label": record.get("object_label"),
        "predicate_family": record.get("predicate_family"),
        "status": verification["status"],
        "geometry_score": verification["geometry_score"],
        "reason_codes": verification["reason_codes"],
        "selection_reason": selection_reason,
        "key_geometry_evidence": key_geometry_evidence(record),
        "manual_question": manual_question(record),
    }


def select_manual_review_queue(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    def add(record: dict[str, Any], reason: str) -> bool:
        edge_id = str(record["edge_id"])
        if edge_id in selected_ids:
            return False
        selected_ids.add(edge_id)
        selected.append(manual_queue_record(record, reason))
        return True

    def score(record: dict[str, Any]) -> float:
        value = record["verification"].get("geometry_score")
        return -1.0 if value is None else float(value)

    support = [r for r in records if r.get("predicate_family") == "support_contact"]
    for record in sorted(support, key=score, reverse=True)[:5]:
        add(record, "support_contact_high_score")
    support_risky = sorted(
        support,
        key=lambda r: (
            0 if r["verification"]["status"] in {"uncertain", "violated"} else 1,
            score(r),
        ),
    )
    support_added = 0
    for record in support_risky:
        if add(record, "support_contact_low_score_or_uncertain"):
            support_added += 1
        if support_added >= 5:
            break

    proximity = [r for r in records if r.get("predicate_family") == "proximity"]
    for record in sorted(proximity, key=score, reverse=True)[:5]:
        add(record, "proximity_high_score")
    proximity_added = 0
    for record in sorted(proximity, key=score):
        if record["verification"]["status"] in {"violated", "uncertain"} or proximity_added < 5:
            if add(record, "proximity_low_score_or_violated"):
                proximity_added += 1
        if proximity_added >= 5:
            break

    vertical = [r for r in records if r.get("predicate_family") == "relative_vertical"]
    vertical_added = 0
    for status in ("satisfied", "violated", "uncertain"):
        for record in [r for r in vertical if r["verification"]["status"] == status][:2]:
            if add(record, f"relative_vertical_{status}"):
                vertical_added += 1
            if vertical_added >= 5:
                break
        if vertical_added >= 5:
            break
    if vertical_added < 5:
        for record in sorted(vertical, key=score):
            if add(record, "relative_vertical_fill"):
                vertical_added += 1
            if vertical_added >= 5:
                break

    horizontal_conflicts = [
        r
        for r in records
        if r.get("predicate_family") == "relative_horizontal"
        and r["verification"].get("diagnostic_status") == "diagnostic_violated"
    ]
    for record in horizontal_conflicts[:5]:
        add(record, "relative_horizontal_diagnostic_conflict")

    return selected


def counter_to_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): value for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def nested_counter_to_dict(counter: dict[str, Counter[str]]) -> dict[str, dict[str, int]]:
    return {key: counter_to_dict(value) for key, value in sorted(counter.items())}


def compute_summary(
    records: list[dict[str, Any]],
    source_summary: dict[str, Any],
    thresholds: dict[str, Any],
    input_dir: Path,
    output_paths: dict[str, Path],
    manual_queue: list[dict[str, Any]],
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = ["phase_b_smoke_test_only_not_prediction_level_evidence"]

    expected_edges = source_summary.get("counts", {}).get("edges_exported")
    if expected_edges is not None and int(expected_edges) != len(records):
        errors.append(f"edge_count_mismatch:{expected_edges}!={len(records)}")

    status_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    family_status_counts: dict[str, Counter[str]] = defaultdict(Counter)
    reason_counts: Counter[str] = Counter()
    diagnostic_status_counts: Counter[str] = Counter()
    primary_status_counts: Counter[str] = Counter()
    primary_family_metrics: dict[str, dict[str, Any]] = {}

    for record in records:
        verification = record["verification"]
        status = verification["status"]
        family = str(record.get("predicate_family"))
        if status not in ALLOWED_STATUSES:
            errors.append(f"invalid_status:{record.get('edge_id')}:{status}")
        status_counts[status] += 1
        family_counts[family] += 1
        family_status_counts[family][status] += 1
        for reason_code in verification["reason_codes"]:
            reason_counts[reason_code] += 1
        if verification.get("diagnostic_status"):
            diagnostic_status_counts[verification["diagnostic_status"]] += 1
        if family in PRIMARY_FAMILIES:
            primary_status_counts[status] += 1

    for family in sorted(PRIMARY_FAMILIES):
        family_counter = family_status_counts.get(family, Counter())
        satisfied = family_counter.get("satisfied", 0)
        violated = family_counter.get("violated", 0)
        uncertain = family_counter.get("uncertain", 0)
        denominator = satisfied + violated
        primary_family_metrics[family] = {
            "satisfied": satisfied,
            "violated": violated,
            "uncertain": uncertain,
            "denominator": denominator,
            "violation_rate": violated / denominator if denominator else None,
            "uncertain_rate": uncertain / (satisfied + violated + uncertain)
            if (satisfied + violated + uncertain)
            else None,
        }

    support_uncertain = family_status_counts.get("support_contact", Counter()).get("uncertain", 0)
    if support_uncertain:
        warnings.append(f"support_contact_uncertain_edges:{support_uncertain}")
    if family_counts.get("relative_horizontal", 0):
        warnings.append("relative_horizontal_excluded_from_primary_metrics")

    primary_denominator = sum(
        metric["denominator"] for metric in primary_family_metrics.values()
    )
    summary = {
        "scan_id": source_summary.get("scan_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "script_name": Path(__file__).name,
        "rule_version": thresholds.get("rule_version", "h001-rules-v0"),
        "geometry_source": source_summary.get("geometry_source"),
        "phase": "Phase B: ground-truth relation verifier smoke test",
        "input_dir": str(input_dir),
        "output_paths": {key: str(path) for key, path in output_paths.items()},
        "counts": {
            "input_edges": len(records),
            "output_edges": len(records),
            "expected_edges": expected_edges,
            "manual_review_queue": len(manual_queue),
            "primary_family_edges": sum(family_counts.get(family, 0) for family in PRIMARY_FAMILIES),
            "primary_metric_denominator": primary_denominator,
            "diagnostic_only_edges": sum(
                1 for record in records if record["verification"].get("diagnostic_only")
            ),
            "unsupported_edges": status_counts.get("unsupported", 0),
            "uncertain_edges": status_counts.get("uncertain", 0),
        },
        "status_counts": counter_to_dict(status_counts),
        "predicate_family_counts": counter_to_dict(family_counts),
        "family_status_counts": nested_counter_to_dict(family_status_counts),
        "primary_status_counts": counter_to_dict(primary_status_counts),
        "primary_family_metrics": primary_family_metrics,
        "diagnostic_status_counts": counter_to_dict(diagnostic_status_counts),
        "reason_code_counts": counter_to_dict(reason_counts),
        "top_reason_codes": [
            {"reason_code": reason_code, "count": count}
            for reason_code, count in reason_counts.most_common(12)
        ],
        "validation": {
            "passed": not errors,
            "warnings": warnings,
            "errors": errors,
        },
        "threshold_config": thresholds,
    }
    return summary


def format_rate(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.3f}"


def make_report(summary: dict[str, Any], manual_queue: list[dict[str, Any]]) -> str:
    lines = [
        "# Rule Verifier",
        "",
        f"Created at: `{summary['created_at']}`",
        f"Scan id: `{summary['scan_id']}`",
        f"Geometry source: `{summary['geometry_source']}`",
        f"Rule version: `{summary['rule_version']}`",
        "",
        "## Validation",
        "",
        f"- Passed: `{summary['validation']['passed']}`",
        f"- Errors: `{len(summary['validation']['errors'])}`",
        f"- Warnings: `{len(summary['validation']['warnings'])}`",
        "",
        "## Counts",
        "",
    ]
    for key, value in summary["counts"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Status Counts", ""])
    for key, value in summary["status_counts"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Predicate Families", ""])
    for family, count in summary["predicate_family_counts"].items():
        family_status = summary["family_status_counts"].get(family, {})
        status_text = ", ".join(f"{status}={value}" for status, value in family_status.items())
        lines.append(f"- `{family}`: `{count}` ({status_text})")

    lines.extend(["", "## Primary Family Metrics", ""])
    lines.append("| Family | Satisfied | Violated | Uncertain | Denominator | Violation rate | Uncertain rate |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for family, metric in summary["primary_family_metrics"].items():
        lines.append(
            "| "
            f"`{family}` | {metric['satisfied']} | {metric['violated']} | "
            f"{metric['uncertain']} | {metric['denominator']} | "
            f"{format_rate(metric['violation_rate'])} | {format_rate(metric['uncertain_rate'])} |"
        )

    lines.extend(["", "## Top Reason Codes", ""])
    for item in summary["top_reason_codes"]:
        lines.append(f"- `{item['reason_code']}`: `{item['count']}`")

    lines.extend(["", "## Manual Review Queue", ""])
    lines.append(f"- Queue size: `{len(manual_queue)}`")
    for item in manual_queue[:10]:
        lines.append(
            "- "
            f"`{item['status']}` `{item['predicate_family']}` "
            f"`{item['subject_label']} --{item['predicate_label']}--> {item['object_label']}` "
            f"score=`{item['geometry_score']}` reason=`{','.join(item['reason_codes'])}`"
        )

    lines.extend(
        [
            "",
            "## Known Limitations",
            "",
            "- This is a one-scan smoke test, not benchmark evidence.",
            "- The verifier uses `semseg_obb_v0`; support/contact decisions can be distorted by coarse OBB-derived AABB geometry.",
            "- `relative_horizontal` is diagnostic only and excluded from primary violation-rate metrics.",
            "- `unsupported` and `uncertain` edges are not hard relation failures.",
            "",
            "## Next Action",
            "",
            "Review `review_queue.jsonl`, especially support/contact, proximity, and vertical relation edges.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir or input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    input_paths = {
        "edges": input_dir / "edges.jsonl",
        "thresholds": input_dir / "thresholds.json",
        "summary": input_dir / "export_summary.json",
    }
    for name, path in input_paths.items():
        if not path.exists():
            raise SystemExit(f"missing_input_file:{name}:{path}")

    thresholds = load_json(input_paths["thresholds"])
    source_summary = load_json(input_paths["summary"])
    edge_records = read_jsonl(input_paths["edges"])

    decision_records: list[dict[str, Any]] = []
    for edge in edge_records:
        edge.pop("_source_line", None)
        decision_record = dict(edge)
        decision_record["verification"] = apply_rules(edge, thresholds)
        decision_records.append(decision_record)

    manual_queue = select_manual_review_queue(decision_records)
    output_paths = {
        "decisions": output_dir / "decisions.jsonl",
        "summary": output_dir / "rules_summary.json",
        "report": output_dir / "rules_report.md",
        "review_queue": output_dir / "review_queue.jsonl",
    }
    summary = compute_summary(
        decision_records,
        source_summary,
        thresholds,
        input_dir,
        output_paths,
        manual_queue,
    )

    write_jsonl(output_paths["decisions"], decision_records)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(make_report(summary, manual_queue), encoding="utf-8")
    write_jsonl(output_paths["review_queue"], manual_queue)

    if summary["validation"]["errors"]:
        print(f"Verifier completed with validation errors. Output: {output_dir}")
        for error in summary["validation"]["errors"]:
            print(f"ERROR: {error}")
        return 1

    print(f"Verifier completed. Output: {output_dir}")
    print(f"Edges verified: {len(decision_records)}")
    print(f"Primary metric denominator: {summary['counts']['primary_metric_denominator']}")
    print(f"Warnings: {len(summary['validation']['warnings'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
