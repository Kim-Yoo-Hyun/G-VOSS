#!/usr/bin/env python3
"""Scan support/contact class-pair repair capacity after shortcut audit."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
RGA_ROOT = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_AUDIT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit"
)
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan"
)

EXPECTED_INPUT_STATUS = (
    "h002_compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit_blocked_shortcut_risk"
)
EXPECTED_INPUT_NEXT = (
    "compatibility_dataset_v3_independent_validity_support_contact_balancing_path_decision_after_schema_shortcut_audit"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan_v1"
)
STATUS_STRICT_READY = (
    "h002_compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan_strict_ready"
)
STATUS_STRICT_BLOCKED_DIAGNOSTIC_POSSIBLE = (
    "h002_compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan_strict_blocked_class_pair_diagnostic_possible"
)
STATUS_BLOCKED = (
    "h002_compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan_blocked_insufficient_capacity"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan_input_errors"
)

NEXT_STRICT_READY = (
    "compatibility_dataset_v3_independent_validity_support_contact_exact_class_pair_repair_materialization_plan"
)
NEXT_DIAGNOSTIC = (
    "compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan"
)

RAW_MATCH_FAMILY = "support_contact"
PREDICATES = {"lying on", "standing on"}
TARGET_FAMILY = "support_contact_pose_conditioned"

MIN_STRICT_MAIN_ROWS = 800
MIN_STRICT_PER_PREDICATE_ROWS = 200
MIN_STRICT_MIXED_GROUPS = 20
MIN_CLASS_PAIR_DIAGNOSTIC_ROWS = 400
SCAN_SHARE_CAP = 0.08


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
                fields.append(key)
                seen.add(key)
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def safe_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def primary_label(row: dict[str, Any]) -> int | None:
    label_status = row.get("label", {}).get("label_match_status")
    geometry_status = row.get("geometry", {}).get("geometry_status")
    if label_status == "exact_match" and geometry_status == "satisfied":
        return 1
    if label_status in {"family_match", "pair_has_other_predicate"} and geometry_status == "unsatisfied":
        return 0
    return None


def has_source_z(row: dict[str, Any]) -> bool:
    semantic = row.get("semantic", {})
    return (
        semantic.get("semantic_score_raw") is not None
        and semantic.get("semantic_score_norm") is not None
        and semantic.get("rank_in_context") is not None
    )


def has_raw_g(row: dict[str, Any]) -> bool:
    geometry = row.get("geometry", {})
    return bool(geometry.get("geometry_checkable") is True and isinstance(geometry.get("raw_features"), dict))


def rank_band(row: dict[str, Any]) -> str:
    rga = row.get("rga", {})
    if rga.get("rank_band"):
        return str(rga["rank_band"])
    rank = safe_int(row.get("semantic", {}).get("rank_in_context"))
    if rank is None:
        return "rank_unknown"
    if rank <= 50:
        return "top50"
    if rank <= 100:
        return "top100_only"
    if rank <= 200:
        return "rank_101_200"
    if rank <= 500:
        return "rank_201_500"
    if rank <= 1000:
        return "rank_501_1000"
    return "rank_gt1000"


def scan_capped_capacity(pos_scans: Counter[str], neg_scans: Counter[str], raw_pairs: int) -> int:
    def capped_count(counter: Counter[str], target_pairs: int) -> int:
        cap = max(1, int(target_pairs * SCAN_SHARE_CAP))
        return sum(min(count, cap) for count in counter.values())

    for pairs in range(raw_pairs, 0, -1):
        if capped_count(pos_scans, pairs) >= pairs and capped_count(neg_scans, pairs) >= pairs:
            return pairs * 2
    return 0


def validate_inputs(audit_summary: dict[str, Any], match_rows: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if audit_summary.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": audit_summary.get("status")})
    if audit_summary.get("next_todo") != EXPECTED_INPUT_NEXT:
        errors.append({"error_type": "unexpected_audit_next", "actual": audit_summary.get("next_todo")})
    risk = audit_summary.get("risk_summary", {})
    expected_blockers = {
        "subject_class_label",
        "object_class_label",
        "subject_object_class_pair",
        "predicate_x_class_pair",
    }
    observed_blockers = set(risk.get("critical_high_or_medium_probe_names", []))
    if not expected_blockers.issubset(observed_blockers):
        errors.append(
            {
                "error_type": "missing_expected_shortcut_blockers",
                "expected_subset": sorted(expected_blockers),
                "actual": sorted(observed_blockers),
            }
        )
    if not match_rows.exists():
        errors.append({"error_type": "missing_match_rows", "path": rel_path(match_rows)})
    return errors


def axis_keys(row: dict[str, Any]) -> dict[str, tuple[Any, ...]]:
    edge = row.get("edge", {})
    predicate = row.get("predicate", {})
    subject = str(edge.get("subject_label"))
    obj = str(edge.get("object_label"))
    pred = str(predicate.get("predicate_label"))
    return {
        "class_pair": (subject, obj),
        "predicate_x_class_pair": (pred, subject, obj),
        "predicate_x_class_pair_x_rank_band": (pred, subject, obj, rank_band(row)),
    }


def scan_capacity(match_rows: Path) -> dict[str, Any]:
    axes = ["class_pair", "predicate_x_class_pair", "predicate_x_class_pair_x_rank_band"]
    counts: dict[str, dict[tuple[Any, ...], Counter[int]]] = {axis: defaultdict(Counter) for axis in axes}
    scan_counts: dict[str, dict[tuple[Any, ...], dict[int, Counter[str]]]] = {
        axis: defaultdict(lambda: {0: Counter(), 1: Counter()}) for axis in axes
    }
    by_predicate: dict[str, Counter[int]] = defaultdict(Counter)
    scanned_rows = 0
    selected_family_rows = 0
    primary_candidate_rows = 0
    skip_counts: Counter[str] = Counter()
    with match_rows.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            scanned_rows += 1
            row = json.loads(line)
            predicate = str(row.get("predicate", {}).get("predicate_label"))
            predicate_family = str(row.get("predicate", {}).get("predicate_family"))
            if predicate_family != RAW_MATCH_FAMILY or predicate not in PREDICATES:
                continue
            selected_family_rows += 1
            label_y = primary_label(row)
            if label_y is None:
                skip_counts["not_primary_label_policy"] += 1
                continue
            if not has_source_z(row):
                skip_counts["missing_source_z"] += 1
                continue
            if not has_raw_g(row):
                skip_counts["missing_raw_g"] += 1
                continue
            primary_candidate_rows += 1
            by_predicate[predicate][label_y] += 1
            scan_id = str(row.get("identity", {}).get("scan_id"))
            for axis, key in axis_keys(row).items():
                counts[axis][key][label_y] += 1
                scan_counts[axis][key][label_y][scan_id] += 1

    axis_summaries: dict[str, dict[str, Any]] = {}
    top_rows: list[dict[str, Any]] = []
    predicate_capacity: dict[str, Counter[str]] = defaultdict(Counter)
    for axis in axes:
        raw_capacity = 0
        scan_capacity = 0
        mixed_groups = 0
        top_axis: list[dict[str, Any]] = []
        for key, counter in counts[axis].items():
            positive = counter[1]
            negative = counter[0]
            raw_pairs = min(positive, negative)
            if raw_pairs <= 0:
                continue
            mixed_groups += 1
            raw_balanced = raw_pairs * 2
            scan_capped = scan_capped_capacity(scan_counts[axis][key][1], scan_counts[axis][key][0], raw_pairs)
            raw_capacity += raw_balanced
            scan_capacity += scan_capped
            if axis.startswith("predicate_x_class_pair"):
                predicate_capacity[str(key[0])][f"{axis}_raw"] += raw_balanced
                predicate_capacity[str(key[0])][f"{axis}_scan_capped"] += scan_capped
            top_axis.append(
                {
                    "axis": axis,
                    "stratum": json.dumps(key, ensure_ascii=False),
                    "positive": positive,
                    "negative": negative,
                    "raw_balanced_capacity": raw_balanced,
                    "scan_capped_capacity": scan_capped,
                    "positive_scans": len(scan_counts[axis][key][1]),
                    "negative_scans": len(scan_counts[axis][key][0]),
                    "rows": positive + negative,
                }
            )
        top_axis.sort(
            key=lambda row: (
                -int(row["scan_capped_capacity"]),
                -int(row["raw_balanced_capacity"]),
                row["stratum"],
            )
        )
        top_rows.extend(top_axis[:100])
        axis_summaries[axis] = {
            "all_groups": len(counts[axis]),
            "mixed_groups": mixed_groups,
            "raw_balanced_capacity": raw_capacity,
            "scan_capped_capacity": scan_capacity,
        }

    strict = axis_summaries["predicate_x_class_pair"]
    strict_by_predicate = {
        predicate: {
            "raw_balanced_capacity": predicate_capacity[predicate].get("predicate_x_class_pair_raw", 0),
            "scan_capped_capacity": predicate_capacity[predicate].get("predicate_x_class_pair_scan_capped", 0),
        }
        for predicate in sorted(PREDICATES)
    }
    strict_ready = (
        strict["scan_capped_capacity"] >= MIN_STRICT_MAIN_ROWS
        and strict["mixed_groups"] >= MIN_STRICT_MIXED_GROUPS
        and all(
            item["scan_capped_capacity"] >= MIN_STRICT_PER_PREDICATE_ROWS
            for item in strict_by_predicate.values()
        )
    )
    diagnostic_possible = axis_summaries["class_pair"]["scan_capped_capacity"] >= MIN_CLASS_PAIR_DIAGNOSTIC_ROWS

    return {
        "scanned_rows": scanned_rows,
        "selected_family_rows": selected_family_rows,
        "primary_candidate_rows": primary_candidate_rows,
        "skip_counts": dict(skip_counts),
        "by_predicate": {
            predicate: {"negative": counter[0], "positive": counter[1]}
            for predicate, counter in sorted(by_predicate.items())
        },
        "axis_summaries": axis_summaries,
        "strict_by_predicate": strict_by_predicate,
        "strict_repair_gate": {
            "strict_ready": strict_ready,
            "diagnostic_class_pair_possible": diagnostic_possible,
            "min_strict_main_rows": MIN_STRICT_MAIN_ROWS,
            "min_strict_per_predicate_rows": MIN_STRICT_PER_PREDICATE_ROWS,
            "min_strict_mixed_groups": MIN_STRICT_MIXED_GROUPS,
            "min_class_pair_diagnostic_rows": MIN_CLASS_PAIR_DIAGNOSTIC_ROWS,
            "scan_share_cap": SCAN_SHARE_CAP,
        },
        "top_rows": top_rows,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    axis = summary["capacity"]["axis_summaries"]
    strict = summary["capacity"]["strict_by_predicate"]
    gate = summary["capacity"]["strict_repair_gate"]
    lines = [
        "# H002 Support/Contact Class-Pair Repair Capacity Scan",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Capacity",
        "",
        "```text",
        f"primary_candidate_rows = {summary['capacity']['primary_candidate_rows']}",
        f"class_pair_scan_capped_capacity = {axis['class_pair']['scan_capped_capacity']}",
        f"predicate_x_class_pair_scan_capped_capacity = {axis['predicate_x_class_pair']['scan_capped_capacity']}",
        f"predicate_x_class_pair_x_rank_band_scan_capped_capacity = {axis['predicate_x_class_pair_x_rank_band']['scan_capped_capacity']}",
        "```",
        "",
        "Strict predicate-class capacity by predicate:",
        "",
        "```text",
        *[
            f"{predicate}: scan_capped = {values['scan_capped_capacity']}, raw = {values['raw_balanced_capacity']}"
            for predicate, values in strict.items()
        ],
        "```",
        "",
        "## Decision",
        "",
        f"- strict_ready = `{gate['strict_ready']}`",
        f"- diagnostic_class_pair_possible = `{gate['diagnostic_class_pair_possible']}`",
        "",
        "Interpretation:",
        "",
        "- Exact `predicate + subject_class + object_class` repair is too sparse for a main support/contact target.",
        "- Relaxed `subject_class + object_class` repair has enough rows for a small diagnostic, but it does not fully remove `predicate_x_class_pair` shortcut risk.",
        "- Learned smoke should remain blocked until a path decision selects a diagnostic-only route or a different target source.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    validation_errors: list[dict[str, Any]] = []

    audit_summary_path = args.audit_dir / "summary.json"
    if not audit_summary_path.exists():
        validation_errors.append({"error_type": "missing_audit_summary", "path": rel_path(audit_summary_path)})
        audit_summary: dict[str, Any] = {}
    else:
        audit_summary = read_json(audit_summary_path)
        validation_errors.extend(validate_inputs(audit_summary, args.match_rows))

    capacity = scan_capacity(args.match_rows) if args.match_rows.exists() else {
        "axis_summaries": {},
        "strict_repair_gate": {"strict_ready": False, "diagnostic_class_pair_possible": False},
        "top_rows": [],
    }
    gate = capacity["strict_repair_gate"]
    if validation_errors:
        status = STATUS_ERROR
        next_todo = EXPECTED_INPUT_NEXT
        selected_path = "blocked_input_errors"
    elif gate["strict_ready"]:
        status = STATUS_STRICT_READY
        next_todo = NEXT_STRICT_READY
        selected_path = "strict_predicate_class_pair_repair_ready"
    elif gate["diagnostic_class_pair_possible"]:
        status = STATUS_STRICT_BLOCKED_DIAGNOSTIC_POSSIBLE
        next_todo = NEXT_DIAGNOSTIC
        selected_path = "strict_repair_blocked_relaxed_class_pair_diagnostic_possible"
        validation_errors.append(
            {
                "field": "strict_predicate_class_pair_repair_capacity",
                "observed_scan_capped_capacity": capacity["axis_summaries"]["predicate_x_class_pair"]["scan_capped_capacity"],
                "required_scan_capped_capacity": MIN_STRICT_MAIN_ROWS,
                "scope": "support_contact_exact_predicate_class_pair",
            }
        )
    else:
        status = STATUS_BLOCKED
        next_todo = NEXT_DIAGNOSTIC
        selected_path = "strict_and_relaxed_class_pair_repair_blocked"
        validation_errors.append(
            {
                "field": "class_pair_repair_capacity",
                "observed_scan_capped_capacity": capacity["axis_summaries"].get("class_pair", {}).get("scan_capped_capacity"),
                "required_scan_capped_capacity": MIN_CLASS_PAIR_DIAGNOSTIC_ROWS,
                "scope": "support_contact_class_pair",
            }
        )

    summary = {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_capacity_scan",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "capacity": {k: v for k, v in capacity.items() if k != "top_rows"},
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_audit_summary": rel_path(audit_summary_path),
        "input_match_rows": rel_path(args.match_rows),
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "status": status,
        "target_family": TARGET_FAMILY,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "validation_error_path": rel_path(args.output_dir / "validation_errors.jsonl"),
    }
    write_json(args.output_dir / "summary.json", summary)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "top_strata.csv", capacity.get("top_rows", []))
    write_report(args.output_dir / "report.md", summary)
    print(json.dumps({
        "status": status,
        "validation_errors": len(validation_errors),
        "selected_path": selected_path,
        "next_todo": next_todo,
        "axis_summaries": capacity.get("axis_summaries", {}),
        "strict_by_predicate": capacity.get("strict_by_predicate", {}),
    }, ensure_ascii=False, sort_keys=True))
    return 1 if status == STATUS_ERROR else 0


if __name__ == "__main__":
    raise SystemExit(main())
