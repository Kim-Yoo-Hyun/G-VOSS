#!/usr/bin/env python3
"""Apply h001-rules-v1 to one-scan verifier artifacts.

This is a hypothesis-stage smoke test. It revises only support/contact
verification by using existing point/local-surface evidence.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RULE_VERSION = "h001-rules-v1"
PREVIOUS_RULE_VERSION = "h001-rules-v0"
PRIMARY_FAMILIES = {"support_contact", "proximity", "relative_vertical"}
ALLOWED_STATUSES = {"satisfied", "violated", "uncertain", "unsupported"}
STATUS_ALIAS = {
    "satisfied": "pass",
    "violated": "fail",
    "uncertain": "uncertain",
    "unsupported": "not_applicable",
}
POINT_STATUS_TO_V1_STATUS = {
    "point_satisfied": "satisfied",
    "point_uncertain": "uncertain",
    "point_violated": "violated",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply h001-rules-v1 to one-scan H001 verifier artifacts."
    )
    parser.add_argument("--artifact-dir", required=True, type=Path)
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


def count_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: counter[key] for key in sorted(counter)}


def support_case_type(point_record: dict[str, Any] | None, edge: dict[str, Any]) -> str:
    label = ""
    if point_record is not None:
        label = str(point_record.get("object_label") or "")
    if not label:
        label = str(edge.get("object_label") or "")
    return "floor_support" if label.strip().lower() == "floor" else "object_object_support"


def v1_thresholds(v0_thresholds: dict[str, Any], point_summary: dict[str, Any] | None) -> dict[str, Any]:
    point_thresholds = {}
    if point_summary is not None:
        point_thresholds = {
            key: value
            for key, value in point_summary.get("threshold_config", {}).items()
            if key != "source_threshold_config"
        }
    return {
        "rule_version": RULE_VERSION,
        "previous_rule_version": PREVIOUS_RULE_VERSION,
        "source_threshold_config": v0_thresholds,
        "point_threshold_config": point_thresholds,
    }


def clone_carried_verification(
    edge: dict[str, Any],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    old = dict(edge.get("verification", {}))
    status = old.get("status", "uncertain")
    reason_codes = set(old.get("reason_codes", []))
    reason_codes.add("carried_from_h001_rules_v0")
    old["previous_rule_version"] = old.get("rule_version", PREVIOUS_RULE_VERSION)
    old["previous_status"] = status
    old["rule_version"] = RULE_VERSION
    old["status"] = status
    old["status_alias"] = STATUS_ALIAS.get(status, "uncertain")
    old["threshold_config"] = thresholds
    old["reason_codes"] = sorted(reason_codes)
    return old


def support_verification(
    edge: dict[str, Any],
    point_record: dict[str, Any] | None,
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    old = edge.get("verification", {})
    previous_status = old.get("status", "uncertain")
    case_type = support_case_type(point_record, edge)
    diagnostic_tags = [case_type + "_case"]

    if point_record is None:
        status = "uncertain"
        point_status = "point_missing"
        reason_codes = ["point_evidence_missing", *diagnostic_tags]
        evidence_available = False
        best_local = None
    else:
        point_status = str(point_record.get("point_status") or "point_uncertain")
        status = POINT_STATUS_TO_V1_STATUS.get(point_status, "uncertain")
        reason_codes = list(point_record.get("point_reason_codes") or [])
        if point_status not in POINT_STATUS_TO_V1_STATUS:
            reason_codes.append("unknown_point_status")
        reason_codes.extend(diagnostic_tags)
        evidence_available = bool(point_record.get("point_evidence_available"))
        best_local = point_record.get("best_local_support_evidence")

    checked = [
        "point_evidence_available",
        "support_points_under_subject",
        "local_vertical_gap",
    ]
    passed: list[str] = []
    failed: list[str] = []
    uncertain: list[str] = []
    if status == "satisfied":
        passed = checked
        geometry_score: float | None = 1.0
    elif status == "violated":
        passed = ["point_evidence_available", "support_points_under_subject"]
        failed = ["local_vertical_gap"]
        geometry_score = 0.0
    else:
        uncertain = checked
        geometry_score = None

    return {
        "rule_version": RULE_VERSION,
        "status": status,
        "status_alias": STATUS_ALIAS[status],
        "predicate_family": edge.get("predicate_family"),
        "primary_metric_eligible": edge.get("predicate_family") in PRIMARY_FAMILIES
        and status in {"satisfied", "violated"},
        "diagnostic_only": False,
        "geometry_score": geometry_score,
        "checked_constraints": checked,
        "passed_constraints": passed,
        "failed_constraints": failed,
        "uncertain_constraints": uncertain,
        "reason_codes": sorted(set(reason_codes)),
        "threshold_config": thresholds,
        "previous_rule_version": old.get("rule_version", PREVIOUS_RULE_VERSION),
        "previous_status": previous_status,
        "previous_reason_codes": old.get("reason_codes", []),
        "point_rule_version": (
            point_record.get("point_rule_version") if point_record is not None else None
        ),
        "point_evidence_available": evidence_available,
        "point_status_source": point_status,
        "best_local_support_evidence": best_local,
        "support_case_type": case_type,
    }


def transition(previous_status: str, status: str) -> str:
    return f"v0_{previous_status}_to_v1_{status}"


def comparison_record(edge: dict[str, Any], point_record: dict[str, Any] | None) -> dict[str, Any]:
    verification = edge["verification"]
    best_local = verification.get("best_local_support_evidence") or {}
    return {
        "edge_id": edge.get("edge_id"),
        "subject_label": edge.get("subject_label"),
        "predicate_label": edge.get("predicate_label"),
        "object_label": edge.get("object_label"),
        "support_case_type": verification.get("support_case_type"),
        "v0_status": verification.get("previous_status"),
        "v1_status": verification.get("status"),
        "point_status": verification.get("point_status_source"),
        "status_transition": transition(
            str(verification.get("previous_status")),
            str(verification.get("status")),
        ),
        "v1_reason_codes": verification.get("reason_codes", []),
        "point_reason_codes": (
            point_record.get("point_reason_codes", []) if point_record is not None else []
        ),
        "point_evidence_available": verification.get("point_evidence_available"),
        "support_points_under_subject_count": best_local.get(
            "support_points_under_subject_count"
        ),
        "local_vertical_gap_p05_p95": best_local.get("local_vertical_gap_p05_p95"),
        "local_vertical_gap_p01_p99": best_local.get("local_vertical_gap_p01_p99"),
        "xy_expansion_m": best_local.get("xy_expansion_m"),
    }


def review_queue_record(edge: dict[str, Any]) -> dict[str, Any]:
    verification = edge["verification"]
    best_local = verification.get("best_local_support_evidence") or {}
    return {
        "edge_id": edge.get("edge_id"),
        "subject_label": edge.get("subject_label"),
        "predicate_label": edge.get("predicate_label"),
        "object_label": edge.get("object_label"),
        "support_case_type": verification.get("support_case_type"),
        "v0_status": verification.get("previous_status"),
        "v1_status": verification.get("status"),
        "point_status": verification.get("point_status_source"),
        "reason_codes": verification.get("reason_codes", []),
        "support_points_under_subject_count": best_local.get(
            "support_points_under_subject_count"
        ),
        "local_vertical_gap_p05_p95": best_local.get("local_vertical_gap_p05_p95"),
        "local_vertical_gap_p01_p99": best_local.get("local_vertical_gap_p01_p99"),
        "manual_question": "Does this remaining support/contact uncertainty or violation reflect annotation noise, segmentation noise, or true relation inconsistency?",
    }


def compute_summary(
    artifact_dir: Path,
    output_paths: dict[str, Path],
    decisions: list[dict[str, Any]],
    point_records: list[dict[str, Any]],
    v1_records: list[dict[str, Any]],
    comparison: list[dict[str, Any]],
    review_queue: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = ["h001_rules_v1_smoke_test_only_not_benchmark_evidence"]

    status_counts = Counter(record["verification"]["status"] for record in v1_records)
    family_status_counts: dict[str, Counter[str]] = {}
    for record in v1_records:
        family = str(record.get("predicate_family"))
        family_status_counts.setdefault(family, Counter())[record["verification"]["status"]] += 1

    support_records = [
        record for record in v1_records if record.get("predicate_family") == "support_contact"
    ]
    support_status_counts = Counter(
        record["verification"]["status"] for record in support_records
    )
    support_transitions = Counter(record["status_transition"] for record in comparison)
    floor_support = [
        record
        for record in support_records
        if record["verification"].get("support_case_type") == "floor_support"
    ]
    floor_satisfied = [
        record for record in floor_support if record["verification"]["status"] == "satisfied"
    ]
    point_evidence_missing = [
        record
        for record in support_records
        if not record["verification"].get("point_evidence_available")
    ]
    primary_metric_denominator = sum(
        1 for record in v1_records if record["verification"].get("primary_metric_eligible")
    )

    if len(v1_records) != len(decisions):
        errors.append(f"output_edge_count_mismatch:{len(v1_records)}!={len(decisions)}")
    if len(support_records) != 32:
        errors.append(f"support_contact_edge_count_unexpected:{len(support_records)}")
    if support_status_counts.get("satisfied", 0) < 19:
        errors.append(
            f"support_contact_v1_satisfied_below_target:{support_status_counts.get('satisfied', 0)}<19"
        )
    if len(floor_satisfied) < 13:
        errors.append(f"floor_support_satisfied_below_target:{len(floor_satisfied)}<13")
    if point_evidence_missing:
        errors.append(f"point_evidence_missing_count:{len(point_evidence_missing)}")
    if len(review_queue) != 13:
        errors.append(f"v1_review_queue_count_unexpected:{len(review_queue)}")

    if support_status_counts.get("uncertain", 0):
        warnings.append(f"support_contact_uncertain_edges:{support_status_counts['uncertain']}")
    if support_status_counts.get("violated", 0):
        warnings.append(f"support_contact_violated_edges:{support_status_counts['violated']}")
    floor_violated = [
        record for record in floor_support if record["verification"]["status"] == "violated"
    ]
    if floor_violated:
        warnings.append(f"floor_support_violated_edges:{len(floor_violated)}")

    return {
        "scan_id": decisions[0].get("scan_id") if decisions else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "script_name": Path(__file__).name,
        "rule_version": RULE_VERSION,
        "previous_rule_version": PREVIOUS_RULE_VERSION,
        "phase": "Phase D: h001-rules-v1 support/contact smoke test",
        "artifact_dir": str(artifact_dir),
        "output_paths": {key: str(path) for key, path in output_paths.items()},
        "counts": {
            "all_edge_count": len(v1_records),
            "input_edge_count": len(decisions),
            "point_evidence_records": len(point_records),
            "support_contact_edge_count": len(support_records),
            "floor_support_edge_count": len(floor_support),
            "floor_support_satisfied_count": len(floor_satisfied),
            "point_evidence_available_count": sum(
                1
                for record in support_records
                if record["verification"].get("point_evidence_available")
            ),
            "point_evidence_missing_count": len(point_evidence_missing),
            "v1_review_queue_count": len(review_queue),
            "primary_metric_denominator": primary_metric_denominator,
        },
        "status_counts": count_dict(status_counts),
        "family_status_counts": {
            family: count_dict(counter) for family, counter in sorted(family_status_counts.items())
        },
        "support_contact_v1_status_counts": count_dict(support_status_counts),
        "support_contact_v0_to_v1_transition_counts": count_dict(support_transitions),
        "threshold_config": thresholds,
        "validation": {
            "passed": not errors,
            "errors": errors,
            "warnings": warnings,
        },
    }


def make_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Rules v1 Report",
        "",
        f"Created at: `{summary['created_at']}`",
        f"Scan id: `{summary['scan_id']}`",
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

    lines.extend(["", "## Support Contact Status", ""])
    for key, value in summary["support_contact_v1_status_counts"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Support Contact Transitions", ""])
    for key, value in summary["support_contact_v0_to_v1_transition_counts"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is a one-scan smoke test, not benchmark evidence.",
            "- `support_contact` now uses point/local-surface evidence as the primary verifier signal.",
            "- Remaining `uncertain` and `violated` support/contact edges require review before qualitative thesis use.",
            "",
            "## Next Action",
            "",
            "Review `v1_review_queue.jsonl` and decide whether visual inspection or multi-scan replication is needed next.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    artifact_dir = args.artifact_dir
    input_paths = {
        "decisions": artifact_dir / "decisions.jsonl",
        "point_evidence": artifact_dir / "point_evidence.jsonl",
        "point_comparison": artifact_dir / "point_comparison.jsonl",
        "thresholds": artifact_dir / "thresholds.json",
    }
    optional_paths = {
        "point_summary": artifact_dir / "point_summary.json",
    }

    missing = [f"{name}:{path}" for name, path in input_paths.items() if not path.exists()]
    if missing:
        raise SystemExit("missing_input_file:" + ",".join(missing))

    decisions = read_jsonl(input_paths["decisions"])
    point_records = read_jsonl(input_paths["point_evidence"])
    _point_comparison = read_jsonl(input_paths["point_comparison"])
    v0_thresholds = load_json(input_paths["thresholds"])
    point_summary = (
        load_json(optional_paths["point_summary"])
        if optional_paths["point_summary"].exists()
        else None
    )
    thresholds = v1_thresholds(v0_thresholds, point_summary)

    point_by_edge: dict[str, dict[str, Any]] = {}
    duplicate_point_edges: list[str] = []
    for record in point_records:
        record.pop("_source_line", None)
        edge_id = str(record.get("edge_id"))
        if edge_id in point_by_edge:
            duplicate_point_edges.append(edge_id)
        point_by_edge[edge_id] = record

    v1_records: list[dict[str, Any]] = []
    comparison: list[dict[str, Any]] = []
    review_queue: list[dict[str, Any]] = []
    support_missing_point_edges: list[str] = []
    non_support_status_changed: list[str] = []

    for source in decisions:
        source.pop("_source_line", None)
        record = dict(source)
        family = record.get("predicate_family")
        if family == "support_contact":
            point_record = point_by_edge.get(str(record.get("edge_id")))
            if point_record is None:
                support_missing_point_edges.append(str(record.get("edge_id")))
            record["verification"] = support_verification(record, point_record, thresholds)
            comparison.append(comparison_record(record, point_record))
            if record["verification"]["status"] in {"uncertain", "violated"}:
                review_queue.append(review_queue_record(record))
        else:
            previous_status = record.get("verification", {}).get("status")
            record["verification"] = clone_carried_verification(record, thresholds)
            if record["verification"].get("status") != previous_status:
                non_support_status_changed.append(str(record.get("edge_id")))
        v1_records.append(record)

    output_paths = {
        "decisions": artifact_dir / "v1_decisions.jsonl",
        "comparison": artifact_dir / "v1_comparison.jsonl",
        "summary": artifact_dir / "v1_summary.json",
        "report": artifact_dir / "v1_report.md",
        "review_queue": artifact_dir / "v1_review_queue.jsonl",
    }
    summary = compute_summary(
        artifact_dir,
        output_paths,
        decisions,
        point_records,
        v1_records,
        comparison,
        review_queue,
        thresholds,
    )
    if duplicate_point_edges:
        summary["validation"]["errors"].append(
            f"duplicate_point_evidence_edge_ids:{sorted(set(duplicate_point_edges))}"
        )
    if support_missing_point_edges:
        summary["validation"]["errors"].append(
            f"support_contact_edges_missing_point_evidence:{support_missing_point_edges}"
        )
    if non_support_status_changed:
        summary["validation"]["warnings"].append(
            f"non_support_status_changed_unexpectedly:{len(non_support_status_changed)}"
        )
    unsupported_statuses = sorted(
        {
            record["verification"].get("status")
            for record in v1_records
            if record["verification"].get("status") not in ALLOWED_STATUSES
        }
    )
    if unsupported_statuses:
        summary["validation"]["errors"].append(f"unsupported_v1_status:{unsupported_statuses}")
    summary["validation"]["passed"] = not summary["validation"]["errors"]

    write_jsonl(output_paths["decisions"], v1_records)
    write_jsonl(output_paths["comparison"], comparison)
    write_jsonl(output_paths["review_queue"], review_queue)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(make_report(summary), encoding="utf-8")

    if summary["validation"]["errors"]:
        print(f"Rules v1 completed with validation errors. Output: {artifact_dir}")
        for error in summary["validation"]["errors"]:
            print(f"ERROR: {error}")
        return 1

    print(f"Rules v1 completed. Output: {artifact_dir}")
    print(f"Edges: {summary['counts']['all_edge_count']}")
    print(
        "Support/contact status counts: "
        f"{summary['support_contact_v1_status_counts']}"
    )
    print(f"Warnings: {len(summary['validation']['warnings'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
