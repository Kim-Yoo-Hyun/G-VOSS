#!/usr/bin/env python3
"""Decide path after support/contact class-pair repair capacity scan."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_CAPACITY_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan"
)

EXPECTED_INPUT_STATUS = (
    "h002_compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan_strict_blocked_class_pair_diagnostic_possible"
)
EXPECTED_INPUT_NEXT = (
    "compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_freeze_independent_validity_diagnostic"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_input_errors"
)
SELECTED_PATH = "freeze_support_contact_independent_validity_as_diagnostic_select_scope_synthesis"
NEXT_TODO = "compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capacity-dir", type=Path, default=DEFAULT_CAPACITY_DIR)
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


def validate_input(capacity: dict[str, Any], capacity_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if capacity.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"error_type": "unexpected_capacity_status", "actual": capacity.get("status")})
    if capacity.get("next_todo") != EXPECTED_INPUT_NEXT:
        errors.append({"error_type": "unexpected_capacity_next", "actual": capacity.get("next_todo")})
    # The capacity scan intentionally records one gate fail: strict predicate-class repair is too sparse.
    if capacity.get("validation_errors") != 1:
        errors.append({"error_type": "unexpected_capacity_validation_errors", "actual": capacity.get("validation_errors")})
    if capacity.get("selected_path") != "strict_repair_blocked_relaxed_class_pair_diagnostic_possible":
        errors.append({"error_type": "unexpected_capacity_selected_path", "actual": capacity.get("selected_path")})

    gate = capacity.get("capacity", {}).get("strict_repair_gate", {})
    if gate.get("strict_ready") is not False:
        errors.append({"error_type": "strict_gate_not_blocked", "actual": gate.get("strict_ready")})
    if gate.get("diagnostic_class_pair_possible") is not True:
        errors.append(
            {
                "error_type": "relaxed_class_pair_diagnostic_not_possible",
                "actual": gate.get("diagnostic_class_pair_possible"),
            }
        )

    axis = capacity.get("capacity", {}).get("axis_summaries", {})
    strict_capacity = axis.get("predicate_x_class_pair", {}).get("scan_capped_capacity")
    relaxed_capacity = axis.get("class_pair", {}).get("scan_capped_capacity")
    if strict_capacity != 88:
        errors.append({"error_type": "unexpected_strict_capacity", "actual": strict_capacity})
    if relaxed_capacity != 426:
        errors.append({"error_type": "unexpected_relaxed_capacity", "actual": relaxed_capacity})

    boundary = capacity.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "paper_evidence_allowed",
        "runs_learned_smoke",
        "trains_new_model",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    for name in ["summary.json", "top_strata.csv", "validation_errors.jsonl"]:
        if not (capacity_dir / name).exists():
            errors.append({"error_type": "missing_capacity_artifact", "path": rel_path(capacity_dir / name)})
    return errors


def route_table(capacity: dict[str, Any]) -> list[dict[str, Any]]:
    axis = capacity["capacity"]["axis_summaries"]
    strict = capacity["capacity"]["strict_by_predicate"]
    strict_capacity = axis["predicate_x_class_pair"]["scan_capped_capacity"]
    relaxed_capacity = axis["class_pair"]["scan_capped_capacity"]
    return [
        {
            "route": "strict_predicate_class_pair_repair_as_main_support_contact_target",
            "verdict": "reject",
            "evidence": (
                f"predicate_x_class_pair scan-capped capacity is {strict_capacity}; "
                f"lying on {strict['lying on']['scan_capped_capacity']}, "
                f"standing on {strict['standing on']['scan_capped_capacity']}."
            ),
            "reason": "Capacity is far below the 800-row main target gate and is predicate-imbalanced.",
            "claim_boundary": "cannot support main learned smoke or paper-level support/contact independent-validity claim",
        },
        {
            "route": "relaxed_subject_object_class_pair_diagnostic",
            "verdict": "defer_optional_diagnostic_only",
            "evidence": f"class_pair scan-capped capacity is {relaxed_capacity}.",
            "reason": (
                "This controls object-class pair but not predicate_x_class_pair, so it cannot remove the "
                "full shortcut that blocked the previous target."
            ),
            "claim_boundary": "diagnostic only; not main evidence",
        },
        {
            "route": "object_class_masked_diagnostic_on_1200_rows",
            "verdict": "defer_optional_diagnostic_only",
            "evidence": "Previous 1200-row target is balanced by predicate but class-composition shortcut remains.",
            "reason": (
                "Masking object labels can test whether non-class evidence remains, but it removes part of "
                "deployable T_e and therefore does not prove the intended factorized representation."
            ),
            "claim_boundary": "diagnostic only; not deployable method evidence",
        },
        {
            "route": "freeze_support_contact_independent_validity_as_diagnostic",
            "verdict": "selected",
            "evidence": "Strict repair failed; relaxed/masked alternatives are diagnostic-only.",
            "reason": (
                "This preserves the negative result without overstating support/contact as a clean "
                "independent-validity target."
            ),
            "claim_boundary": "support/contact independent-validity is diagnostic; earlier pose-conditioned support/contact remains scoped C_e mechanism evidence",
        },
        {
            "route": "search_new_gt_or_human_audit_source_for_support_contact_main_target",
            "verdict": "future_work_or_user_decision",
            "evidence": "Current Open3DSG train-side GT/source construction lacks strict predicate-class mixed capacity.",
            "reason": (
                "A main support/contact reliability target likely needs independent visual/mesh audit labels "
                "or a different source construction."
            ),
            "claim_boundary": "not part of current train-only path unless explicitly restarted",
        },
    ]


def write_report(path: Path, summary: dict[str, Any], routes: list[dict[str, Any]]) -> None:
    capacity = summary["capacity_snapshot"]
    lines = [
        "# H002 Support/Contact Class-Pair Repair Path Decision",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Decision",
        "",
        "Freeze support/contact independent-validity as diagnostic-only.",
        "",
        "The strict repair target is too sparse:",
        "",
        "```text",
        f"predicate_x_class_pair scan-capped capacity = {capacity['predicate_x_class_pair_scan_capped_capacity']}",
        f"lying on strict capacity = {capacity['lying_on_strict_scan_capped_capacity']}",
        f"standing on strict capacity = {capacity['standing_on_strict_scan_capped_capacity']}",
        "```",
        "",
        "The relaxed class-pair option is possible but only diagnostic:",
        "",
        "```text",
        f"class_pair scan-capped capacity = {capacity['class_pair_scan_capped_capacity']}",
        "```",
        "",
        "## Route Table",
        "",
    ]
    for row in routes:
        lines.extend(
            [
                f"- `{row['route']}`: {row['verdict']}",
                f"  Evidence: {row['evidence']}",
                f"  Reason: {row['reason']}",
                f"  Boundary: {row['claim_boundary']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only path decision.",
            "- No validation/test usage.",
            "- No row materialization.",
            "- No learned smoke or model training.",
            "- No calibrated `p_rel` / `p_obs` claim.",
            "- No paper-level evidence.",
            "- No H001 artifact modification.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    capacity_path = args.capacity_dir / "summary.json"
    if capacity_path.exists():
        capacity = read_json(capacity_path)
        validation_errors = validate_input(capacity, args.capacity_dir)
    else:
        capacity = {}
        validation_errors = [{"error_type": "missing_capacity_summary", "path": rel_path(capacity_path)}]

    if validation_errors:
        status = STATUS_ERROR
        selected_path = "blocked_input_errors"
        next_todo = EXPECTED_INPUT_NEXT
        routes: list[dict[str, Any]] = []
        capacity_snapshot: dict[str, Any] = {}
    else:
        status = STATUS_READY
        selected_path = SELECTED_PATH
        next_todo = NEXT_TODO
        routes = route_table(capacity)
        axis = capacity["capacity"]["axis_summaries"]
        strict = capacity["capacity"]["strict_by_predicate"]
        capacity_snapshot = {
            "class_pair_scan_capped_capacity": axis["class_pair"]["scan_capped_capacity"],
            "predicate_x_class_pair_scan_capped_capacity": axis["predicate_x_class_pair"]["scan_capped_capacity"],
            "predicate_x_class_pair_x_rank_band_scan_capped_capacity": axis[
                "predicate_x_class_pair_x_rank_band"
            ]["scan_capped_capacity"],
            "lying_on_strict_scan_capped_capacity": strict["lying on"]["scan_capped_capacity"],
            "standing_on_strict_scan_capped_capacity": strict["standing on"]["scan_capped_capacity"],
            "primary_candidate_rows": capacity["capacity"]["primary_candidate_rows"],
            "selected_family_rows": capacity["capacity"]["selected_family_rows"],
        }

    summary = {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_path_decision",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "capacity_snapshot": capacity_snapshot,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_capacity_summary": rel_path(capacity_path),
        "next_todo": next_todo,
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "status": status,
        "validation_errors": len(validation_errors),
        "validation_error_path": rel_path(args.output_dir / "validation_errors.jsonl"),
    }
    write_json(args.output_dir / "summary.json", summary)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "route_decision.csv", routes)
    write_report(args.output_dir / "report.md", summary, routes)
    print(
        json.dumps(
            {
                "status": status,
                "selected_path": selected_path,
                "validation_errors": len(validation_errors),
                "next_todo": next_todo,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 1 if status == STATUS_ERROR else 0


if __name__ == "__main__":
    raise SystemExit(main())
