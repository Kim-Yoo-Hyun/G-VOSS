#!/usr/bin/env python3
"""Update H002 route map after R6 supported-by decomposition review."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SCHEMA_FREEZE_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review"
)
DEFAULT_ROUTE_MANIFEST_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze"
)
DEFAULT_R6_REVIEW_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_supported_by_decomposition_smoke_result_review"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review"
)

EXPECTED_SCHEMA_FREEZE_STATUS = (
    "h002_compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review_ready"
)
EXPECTED_ROUTE_MANIFEST_STATUS = (
    "h002_compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze_ready"
)
EXPECTED_R6_REVIEW_STATUS = (
    "h002_compatibility_dataset_v3_supported_by_decomposition_smoke_result_review_ready_for_route_update"
)
EXPECTED_R6_REVIEW_NEXT = "compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review_v1"
STATUS_READY = "h002_compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review_input_errors"
SELECTED_PATH = "merge_r6_diagnostic_boundary_select_attachment_observability_target_plan"
NEXT_TODO = "compatibility_dataset_v3_attachment_observability_target_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema-freeze-dir", type=Path, default=DEFAULT_SCHEMA_FREEZE_DIR)
    parser.add_argument("--route-manifest-dir", type=Path, default=DEFAULT_ROUTE_MANIFEST_DIR)
    parser.add_argument("--r6-review-dir", type=Path, default=DEFAULT_R6_REVIEW_DIR)
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
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(
    schema_summary: dict[str, Any],
    route_manifest_summary: dict[str, Any],
    r6_summary: dict[str, Any],
    schema_routes: list[dict[str, str]],
    route_manifest_rows: list[dict[str, str]],
    r6_route_rows: list[dict[str, str]],
    roots: dict[str, Path],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected = {
        "schema_freeze": (schema_summary, EXPECTED_SCHEMA_FREEZE_STATUS),
        "route_manifest": (route_manifest_summary, EXPECTED_ROUTE_MANIFEST_STATUS),
        "r6_review": (r6_summary, EXPECTED_R6_REVIEW_STATUS),
    }
    for name, (summary, status) in expected.items():
        if summary.get("status") != status:
            errors.append({"input": name, "error_type": "unexpected_status", "actual": summary.get("status")})
        if summary.get("validation_errors") != 0:
            errors.append({"input": name, "error_type": "validation_errors_present", "actual": summary.get("validation_errors")})
        if read_jsonl(roots[name] / "validation_errors.jsonl"):
            errors.append({"input": name, "error_type": "validation_error_rows_present"})

    if r6_summary.get("next_todo") != EXPECTED_R6_REVIEW_NEXT:
        errors.append({"input": "r6_review", "error_type": "unexpected_next_todo", "actual": r6_summary.get("next_todo")})

    boundary = r6_summary.get("boundary", {})
    if boundary.get("factorized_route_success_claim_allowed") is not False:
        errors.append({"input": "r6_review", "error_type": "factorized_success_boundary_not_false"})
    if boundary.get("diagnostic_route_claim_allowed") is not True:
        errors.append({"input": "r6_review", "error_type": "diagnostic_boundary_not_true"})
    for key in ["paper_evidence_allowed", "test_usage", "validation_usage"]:
        if boundary.get(key) is not False:
            errors.append({"input": "r6_review", "error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})

    if len(schema_routes) != 13:
        errors.append({"input": "schema_routes", "error_type": "unexpected_route_count", "actual": len(schema_routes)})
    if len(route_manifest_rows) != 13:
        errors.append({"input": "route_manifest", "error_type": "unexpected_route_count", "actual": len(route_manifest_rows)})

    schema_by_id = {row.get("route_id"): row for row in schema_routes}
    manifest_by_id = {row.get("route_id"): row for row in route_manifest_rows}
    for route_id in ["R5", "R6", "R7"]:
        if route_id not in schema_by_id:
            errors.append({"input": "schema_routes", "error_type": "missing_route", "route_id": route_id})
        if route_id not in manifest_by_id:
            errors.append({"input": "route_manifest", "error_type": "missing_route", "route_id": route_id})

    if schema_by_id.get("R6", {}).get("family") != "superordinate_support":
        errors.append({"input": "schema_routes", "error_type": "r6_family_not_superordinate_support"})
    if schema_by_id.get("R5", {}).get("relations") != "standing on; lying on":
        errors.append({"input": "schema_routes", "error_type": "r5_not_standing_lying"})
    if schema_by_id.get("R7", {}).get("relations") != "attached to; hanging on; connected to":
        errors.append({"input": "schema_routes", "error_type": "r7_attachment_relation_mismatch"})

    r6_by_id = {row.get("route_id"): row for row in r6_route_rows}
    if r6_by_id.get("R6", {}).get("status") != "diagnostic_frozen_not_main_factorized_success":
        errors.append({"input": "r6_route_position", "error_type": "r6_not_frozen_diagnostic"})
    if r6_by_id.get("R3", {}).get("status") != "kept_separate_from_supported_by":
        errors.append({"input": "r6_route_position", "error_type": "support_contact_not_separated"})
    if r6_by_id.get("R7", {}).get("status") != "queued_after_route_map_update":
        errors.append({"input": "r6_route_position", "error_type": "r7_not_queued"})
    return errors


def update_route_taxonomy(schema_routes: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in schema_routes:
        updated = dict(row)
        route_id = updated.get("route_id")
        if route_id == "R6":
            updated.update(
                {
                    "paper_role": "diagnostic_broad_label_decomposition_boundary",
                    "target_semantics": (
                        "broad support requires accept/relabel/reject/abstain decomposition; "
                        "it is not a clean binary predicate-geometry compatibility target"
                    ),
                    "primary_factors": "G_e; Q_e; p_obs; relabel target; hidden construction fields audit-only",
                    "blocked_interpretation": (
                        "supported by is a main factorized-route success or a clean negative for standing/lying on"
                    ),
                    "status_after_update": "diagnostic_frozen_not_main_factorized_success",
                }
            )
        elif route_id == "R5":
            updated.update(
                {
                    "paper_role": "main_challenging_evidence_with_caveat_kept_separate_from_supported_by",
                    "blocked_interpretation": (
                        "support/contact result can be merged with broad supported-by decomposition without boundary"
                    ),
                    "status_after_update": "main_challenging_route_preserved",
                }
            )
        elif route_id == "R7":
            updated.update(
                {
                    "paper_role": "selected_next_observability_probe",
                    "status_after_update": "selected_next_active_route",
                }
            )
        else:
            updated["status_after_update"] = updated.get("status_after_freeze")
        rows.append(updated)
    return rows


def route_delta() -> list[dict[str, Any]]:
    return [
        {
            "route_id": "R6",
            "field": "status",
            "before": "included_as_decomposition_route_candidate",
            "after": "diagnostic_frozen_not_main_factorized_success",
            "reason": "R6 p_rel is dominated by G_e+Q_e and Q-only, not by full T_e+G_e+Q_e.",
        },
        {
            "route_id": "R6",
            "field": "paper_role",
            "before": "claim_control_or_next_probe",
            "after": "diagnostic_broad_label_decomposition_boundary",
            "reason": "Useful as broad-label decomposition/abstention evidence, not main factorized success.",
        },
        {
            "route_id": "R5",
            "field": "boundary",
            "before": "support/contact route with supported-by diagnostic nearby",
            "after": "standing/lying on kept separate from supported by",
            "reason": "Specific support/contact predicate compatibility should not inherit broad supported-by ambiguity.",
        },
        {
            "route_id": "R7",
            "field": "next_active_route",
            "before": "queued_after_route_map_update",
            "after": "selected_next_active_route",
            "reason": "Attachment-like relations are the next highest-value observability route after R6 boundary is frozen.",
        },
    ]


def claim_boundary_update() -> list[dict[str, Any]]:
    return [
        {
            "claim_area": "main_mechanism_families",
            "status": "unchanged",
            "allowed": "relative_vertical; size_relative; relative_horizontal; support_contact",
            "blocked": "do not add supported by as main mechanism row",
        },
        {
            "claim_area": "superordinate_support",
            "status": "diagnostic_only",
            "allowed": "broad support labels need decomposition/relabel/abstain or abstention-aware routing",
            "blocked": "R6 demonstrates factorized p_rel success",
        },
        {
            "claim_area": "observability_route",
            "status": "selected_next",
            "allowed": "plan attached/hanging/connected as p_obs/Q_e-first target",
            "blocked": "direct visual/multiview learned input before audit and model-safe boundary",
        },
        {
            "claim_area": "paper_level",
            "status": "blocked",
            "allowed": "train-only hypothesis-stage route taxonomy",
            "blocked": "paper-level performance, calibrated p_rel/p_obs, held-out relation reliability",
        },
    ]


def next_active_route() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "next_todo": NEXT_TODO,
            "route_id": "R7",
            "family": "attachment_observability",
            "relations": "attached to; hanging on; connected to",
            "why_selected": (
                "After R6 broad support is frozen as diagnostic, the main remaining route-generalization "
                "gap is observability-heavy physical relations where Q_e/p_obs must be defined before p_rel."
            ),
            "first_step": "target plan only; no materialization or learned smoke",
        },
        {
            "rank": 2,
            "next_todo": "compatibility_dataset_v3_promotion_boundary_review",
            "route_id": "promotion",
            "family": "all_current_routes",
            "relations": "current route table",
            "why_selected": "Needed later to decide which train-only route results can become paper-level experiment candidates.",
            "first_step": "deferred until R7 plan or explicit user stop",
        },
        {
            "rank": 3,
            "next_todo": "compatibility_dataset_v3_contact_orientation_feasibility_plan",
            "route_id": "R8",
            "family": "contact_orientation",
            "relations": "leaning against",
            "why_selected": "Feasible follow-up if attachment route is blocked by observability assets.",
            "first_step": "capacity/schema plan only",
        },
    ]


def write_report(
    path: Path,
    summary: dict[str, Any],
    updated_routes: list[dict[str, Any]],
    deltas: list[dict[str, Any]],
    boundaries: list[dict[str, Any]],
    next_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# H002 Route Map Update After Supported-By Decomposition Review",
        "",
        f"Created: {summary['created_at_utc']}",
        "",
        "## Decision",
        "",
        "R6 `supported by`를 `superordinate_support` diagnostic route로 고정하고,",
        "R5 `standing on` / `lying on` support/contact compatibility route와 분리한다.",
        "다음 active route는 R7 `attached to` / `hanging on` / `connected to` observability-first target plan이다.",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Route Delta",
        "",
        "| Route | Field | Before | After | Reason |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in deltas:
        lines.append(
            f"| `{row['route_id']}` | {row['field']} | {row['before']} | {row['after']} | {row['reason']} |"
        )

    lines.extend(
        [
            "",
            "## Updated Route Positions",
            "",
            "| Route | Family | Relations | Paper Role | Status |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in updated_routes:
        lines.append(
            f"| `{row['route_id']}` | `{row['family']}` | {row['relations']} | {row['paper_role']} | `{row['status_after_update']}` |"
        )

    lines.extend(["", "## Claim Boundary", ""])
    for row in boundaries:
        lines.append(f"- `{row['claim_area']}`: status={row['status']} / allowed={row['allowed']} / blocked={row['blocked']}")

    lines.extend(["", "## Next Active Route", ""])
    for row in next_rows:
        lines.append(f"- `{row['rank']}`. `{row['next_todo']}`: {row['family']} / {row['why_selected']}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    roots = {
        "schema_freeze": args.schema_freeze_dir,
        "route_manifest": args.route_manifest_dir,
        "r6_review": args.r6_review_dir,
    }

    schema_summary = read_json(args.schema_freeze_dir / "summary.json")
    route_manifest_summary = read_json(args.route_manifest_dir / "summary.json")
    r6_summary = read_json(args.r6_review_dir / "summary.json")
    schema_routes = read_csv(args.schema_freeze_dir / "route_taxonomy_freeze.csv")
    route_manifest_rows = read_csv(args.route_manifest_dir / "route_target_manifest.csv")
    r6_route_rows = read_csv(args.r6_review_dir / "route_position.csv")

    errors = validate_inputs(
        schema_summary,
        route_manifest_summary,
        r6_summary,
        schema_routes,
        route_manifest_rows,
        r6_route_rows,
        roots,
    )
    status = STATUS_ERRORS if errors else STATUS_READY
    updated_routes = [] if errors else update_route_taxonomy(schema_routes)
    deltas = [] if errors else route_delta()
    boundaries = [] if errors else claim_boundary_update()
    next_rows = [] if errors else next_active_route()

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": None if errors else SELECTED_PATH,
        "next_todo": None if errors else NEXT_TODO,
        "validation_errors": len(errors),
        "input_paths": {
            "schema_freeze_dir": rel_path(args.schema_freeze_dir),
            "route_manifest_dir": rel_path(args.route_manifest_dir),
            "r6_review_dir": rel_path(args.r6_review_dir),
        },
        "output_paths": {
            "artifact_root": rel_path(args.output_dir),
            "summary": rel_path(args.output_dir / "summary.json"),
            "updated_route_map": rel_path(args.output_dir / "updated_route_map.csv"),
            "route_delta": rel_path(args.output_dir / "route_delta.csv"),
            "claim_boundary_update": rel_path(args.output_dir / "claim_boundary_update.csv"),
            "next_active_route": rel_path(args.output_dir / "next_active_route.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "main_mechanism_families": [
            "relative_vertical",
            "size_relative",
            "relative_horizontal",
            "support_contact",
        ],
        "diagnostic_or_control_families": ["proximity", "superordinate_support"],
        "next_active_route": "attachment_observability" if not errors else None,
        "r6_decision": {
            "status": "diagnostic_frozen_not_main_factorized_success" if not errors else None,
            "factorized_route_success_claim_allowed": False,
            "kept_separate_from_support_contact": True,
        },
        "boundary": {
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "test_usage": False,
            "validation_usage": False,
            "runs_model": False,
            "materializes_rows": False,
            "calibrated_p_rel_p_obs_allowed": False,
        },
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "summary.json", summary)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_csv(args.output_dir / "updated_route_map.csv", updated_routes)
    write_csv(args.output_dir / "route_delta.csv", deltas)
    write_csv(args.output_dir / "claim_boundary_update.csv", boundaries)
    write_csv(args.output_dir / "next_active_route.csv", next_rows)
    if not errors:
        write_report(args.output_dir / "report.md", summary, updated_routes, deltas, boundaries, next_rows)
    else:
        (args.output_dir / "report.md").write_text(
            "# H002 Route Map Update After Supported-By Decomposition Review\n\nInput validation failed; see `validation_errors.jsonl`.\n",
            encoding="utf-8",
        )

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
