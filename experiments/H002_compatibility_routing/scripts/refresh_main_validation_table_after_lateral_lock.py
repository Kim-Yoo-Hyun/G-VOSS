#!/usr/bin/env python3
"""Refresh H002 experiment-stage table placement after the lateral route lock.

This script does not refit or retune any score. It combines already-frozen
experiment outputs:

- source reranking metrics for relative_vertical + size_relative
- bootstrap CIs for the source-reranking main score
- split-route left/right and front/behind metrics
- proximity geometry-only diagnostic
- support/contact capacity and failure-taxonomy decision

The output is an experiment-stage table contract, not a paper draft edit.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h002_main_validation_table_refresh_after_lateral_lock_v1"
STATUS_READY = "h002_main_validation_table_refresh_after_lateral_lock_ready"
STATUS_ERROR = "h002_main_validation_table_refresh_after_lateral_lock_errors"
NEXT_TODO = "none_scoped_h002_outputs_ready"

K_GRID = (5, 10, 20, 50, 100)
LATERAL_K_GRID = (10, 20, 50, 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--source-reranking-dir", type=Path, required=True)
    parser.add_argument("--source-ci-dir", type=Path, required=True)
    parser.add_argument("--lateral-dir", type=Path, required=True)
    parser.add_argument("--proximity-dir", type=Path, required=True)
    parser.add_argument("--support-contact-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
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
    if not rows:
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def line_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt(value: Any) -> str:
    number = safe_float(value)
    if number is None:
        return ""
    return f"{number:.6f}"


def markdown_table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    body = ["| " + " | ".join(str(row.get(col, "")) for col in cols) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def validation_errors_empty(path: Path) -> bool:
    return path.exists() and line_count(path) == 0


def validate_inputs(args: argparse.Namespace) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    required_files = {
        "source_control_metrics": args.source_reranking_dir / "control_metrics.csv",
        "source_validation_errors": args.source_reranking_dir / "validation_errors.jsonl",
        "source_ci_summary": args.source_ci_dir / "summary.json",
        "source_ci_delta": args.source_ci_dir / "main_reranking_delta_ci.csv",
        "source_ci_validation_errors": args.source_ci_dir / "validation_errors.jsonl",
        "lateral_summary": args.lateral_dir / "summary.json",
        "lateral_compact": args.lateral_dir / "lateral_compact_table.csv",
        "lateral_subroute_delta": args.lateral_dir / "subroute_delta_metrics.csv",
        "lateral_validation_errors": args.lateral_dir / "validation_errors.jsonl",
        "proximity_summary": args.proximity_dir / "summary.json",
        "proximity_deltas": args.proximity_dir / "proximity_source_wide_deltas.csv",
        "proximity_validation_errors": args.proximity_dir / "validation_errors.jsonl",
        "support_summary": args.support_contact_dir / "summary.json",
        "support_validation_errors": args.support_contact_dir / "validation_errors.jsonl",
    }
    for name, path in required_files.items():
        if not path.exists():
            errors.append({"error_type": "missing_required_file", "name": name, "path": str(path)})

    for name in [
        "source_validation_errors",
        "source_ci_validation_errors",
        "lateral_validation_errors",
        "proximity_validation_errors",
        "support_validation_errors",
    ]:
        path = required_files[name]
        if path.exists() and not validation_errors_empty(path):
            errors.append({"error_type": "validation_errors_file_not_empty", "name": name, "path": str(path)})

    if required_files["source_ci_summary"].exists():
        source_ci = read_json(required_files["source_ci_summary"])
        if source_ci.get("status") != "h002_source_reranking_bootstrap_ci_ready":
            errors.append({"error_type": "unexpected_source_ci_status", "actual": source_ci.get("status")})
        if source_ci.get("validation_errors") != 0:
            errors.append({"error_type": "source_ci_validation_errors", "actual": source_ci.get("validation_errors")})
        if set(source_ci.get("primary_families", [])) != {"relative_vertical", "size_relative"}:
            errors.append({"error_type": "unexpected_source_ci_primary_families", "actual": source_ci.get("primary_families")})

    if required_files["lateral_summary"].exists():
        lateral = read_json(required_files["lateral_summary"])
        if lateral.get("status") != "h002_relative_horizontal_split_route_scorer_ready":
            errors.append({"error_type": "unexpected_lateral_status", "actual": lateral.get("status")})
        left = lateral.get("subroutes", {}).get("lateral_left_right", {})
        depth = lateral.get("subroutes", {}).get("depth_front_behind", {})
        if left.get("selected_path") != "include_as_caveated_lateral_main_route":
            errors.append({"error_type": "lateral_not_locked_for_main", "actual": left.get("selected_path")})
        if depth.get("selected_path") != "classify_as_depth_reference_frame_failure_case":
            errors.append({"error_type": "depth_not_locked_as_failure", "actual": depth.get("selected_path")})

    if required_files["proximity_summary"].exists():
        proximity = read_json(required_files["proximity_summary"])
        if proximity.get("status") != "h002_proximity_geometry_only_route_diagnostic_ready":
            errors.append({"error_type": "unexpected_proximity_status", "actual": proximity.get("status")})
        if proximity.get("final_pass") is not True:
            errors.append({"error_type": "proximity_final_pass_false", "actual": proximity.get("final_pass")})

    if required_files["support_summary"].exists():
        support = read_json(required_files["support_summary"])
        decision = support.get("decision", {})
        if support.get("status") != "h002_support_contact_independent_target_repair_diagnostic_freeze_ready":
            errors.append({"error_type": "unexpected_support_status", "actual": support.get("status")})
        if decision.get("support_contact_solved_claim_allowed") is not False:
            errors.append({"error_type": "support_contact_solved_claim_not_blocked", "actual": decision})
    return errors


def ci_lookup(ci_rows: list[dict[str, str]]) -> dict[tuple[str, int, str], dict[str, str]]:
    lookup: dict[tuple[str, int, str], dict[str, str]] = {}
    for row in ci_rows:
        if (
            row.get("level") == "primary_success_weighted"
            and row.get("comparison") == "S2_source_x_Ce_minus_S0_source_score"
            and row.get("source_id") == "ALL"
            and row.get("route_family") == "PRIMARY"
        ):
            lookup[(row["comparison"], int(row["K"]), row["metric"])] = row
    return lookup


def build_core_rows(control_rows: list[dict[str, str]], ci_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    ci = ci_lookup(ci_rows)
    rows: list[dict[str, Any]] = []
    for k in K_GRID:
        row = next(
            item
            for item in control_rows
            if item.get("level") == "primary_success_weighted"
            and item.get("comparison") == "S2_vs_S0_source_score"
            and int(item["K"]) == k
        )
        recall_ci = ci[("S2_source_x_Ce_minus_S0_source_score", k, "Recall@K")]
        violation_ci = ci[("S2_source_x_Ce_minus_S0_source_score", k, "Violation@K")]
        rows.append(
            {
                "table_section": "main_core",
                "route": "predicate_geometry_comparison",
                "relations": "higher/lower + bigger/smaller",
                "score": "S2_source_x_Ce",
                "source_scope": "VL-SAT + Open3DSG validation",
                "K": k,
                "S0_Recall@K": fmt(row["baseline_Recall@K"]),
                "H002_Recall@K": fmt(row["primary_Recall@K"]),
                "Delta_Recall@K": fmt(row["delta_Recall@K"]),
                "Delta_Recall_CI95": f"[{fmt(recall_ci['ci_low_95'])}, {fmt(recall_ci['ci_high_95'])}]",
                "S0_Violation@K": fmt(row["baseline_Violation@K"]),
                "H002_Violation@K": fmt(row["primary_Violation@K"]),
                "Delta_Violation@K": fmt(row["delta_Violation@K"]),
                "Delta_Violation_CI95": f"[{fmt(violation_ci['ci_low_95'])}, {fmt(violation_ci['ci_high_95'])}]",
                "paper_role": "main_validated_compatibility_route",
                "caveat": "official validation only; source/family caveats remain separate",
            }
        )
    return rows


def build_lateral_rows(lateral_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in lateral_rows:
        k = int(row["K"])
        if k not in LATERAL_K_GRID:
            continue
        rows.append(
            {
                "table_section": "main_caveated_lateral",
                "route": "caveated_lateral_compatibility",
                "relations": "left/right",
                "score": "RH1_source_x_frame_score",
                "source_scope": row["source_id"],
                "K": k,
                "S0_Recall@K": fmt(row["S0_Recall@K"]),
                "H002_Recall@K": fmt(row["RH1_Recall@K"]),
                "Delta_Recall@K": fmt(row["delta_Recall@K"]),
                "Delta_Recall_CI95": row["delta_Recall_ci95"],
                "S0_Violation@K": fmt(row["S0_Violation@K"]),
                "H002_Violation@K": fmt(row["RH1_Violation@K"]),
                "Delta_Violation@K": fmt(row["delta_Violation@K"]),
                "Delta_Violation_CI95": row["delta_Violation_ci95"],
                "paper_role": "caveated_main_lateral_route",
                "caveat": "violation-risk reduction with bounded recall tradeoff; not a full relative-horizontal solved claim",
            }
        )
    return rows


def build_depth_rows(delta_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in delta_rows:
        if (
            row.get("subroute") == "depth_front_behind"
            and row.get("comparison") == "RH1_source_x_frame_score_minus_RH0_source_score"
            and int(row["K"]) in LATERAL_K_GRID
        ):
            rows.append(
                {
                    "table_section": "appendix_failure",
                    "route": "frame_depth_ambiguity",
                    "relations": "front/behind",
                    "score": "RH1_source_x_frame_score",
                    "source_scope": row["source_id"],
                    "K": row["K"],
                    "Delta_Recall@K": fmt(row["delta_Recall@K"]),
                    "Delta_Violation@K": fmt(row["delta_Violation@K"]),
                    "paper_role": "failure_case_appendix",
                    "interpretation": "Violation decreases, but Recall loss is too large for main success.",
                }
            )
    return rows


def build_proximity_rows(rows_in: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in rows_in:
        rows.append(
            {
                "table_section": "appendix_control",
                "route": "geometry_only_control",
                "relations": "close by",
                "score": "S2_source_x_Ce diagnostic / normalized distance control",
                "source_scope": row["source_id"],
                "K": row["K"],
                "Delta_Recall@K": fmt(row["delta_Recall@K"]),
                "Delta_Violation@K": fmt(row["delta_Violation@K"]),
                "paper_role": "geometry_only_route_control",
                "interpretation": "Proximity is geometry-decidable and supports relation-aware routing, not T_e x G_e interaction.",
            }
        )
    return rows


def build_support_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    decision = summary.get("decision", {})
    return [
        {
            "table_section": "appendix_failure",
            "route": "hard_contact_pose",
            "relations": "standing on / lying on / supported by",
            "score": "support/contact proxy audit",
            "source_scope": "official validation diagnostic",
            "K": "",
            "Delta_Recall@K": "",
            "Delta_Violation@K": "",
            "paper_role": "diagnostic_failure_taxonomy",
            "interpretation": (
                "35/347 binary target, 0.908 majority baseline, and exact "
                "construction-rule recovery block an independent solved-route claim"
            ),
            "binary_rows": 382,
            "mixed_class_pairs": "",
            "support_contact_solved": decision.get("support_contact_solved_claim_allowed", False),
        }
    ]


def table_placement_rows() -> list[dict[str, Any]]:
    return [
        {
            "route": "predicate_geometry_comparison",
            "relations": "higher/lower, bigger/smaller",
            "placement": "main_table",
            "status": "main_validated",
            "reason": "validated S2 source x C_e route with bootstrap CI and controls",
        },
        {
            "route": "caveated_lateral_compatibility",
            "relations": "left/right",
            "placement": "main_table_caveated_rows",
            "status": "caveated_main_validated",
            "reason": "15/20 win cells, no Violation regression, no recall-loss cell above 0.05, controls pass",
        },
        {
            "route": "frame_depth_ambiguity",
            "relations": "front/behind",
            "placement": "appendix_failure_analysis",
            "status": "failure_case",
            "reason": "Violation improves, but Recall loss is too large; reference-frame/depth ambiguity remains",
        },
        {
            "route": "geometry_only_control",
            "relations": "close by",
            "placement": "appendix_or_analysis_control",
            "status": "control_route",
            "reason": "geometry-only route is sufficient; not a T_e x G_e interaction success",
        },
        {
            "route": "hard_contact_pose",
            "relations": "standing on, lying on, supported by",
            "placement": "appendix_failure_taxonomy",
            "status": "diagnostic_failure",
            "reason": "capacity and shortcut-controlled labels block support/contact solved claim",
        },
        {
            "route": "full_relative_horizontal",
            "relations": "left/right/front/behind",
            "placement": "not_single_main_route",
            "status": "blocked_as_whole",
            "reason": "left/right and front/behind have different route behavior",
        },
    ]


def claim_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim": "relation-aware evidence routing framework",
            "status": "allowed_with_scope",
            "wording": "Framework proposed; predicate-geometry comparison and caveated lateral routes validated on official validation.",
        },
        {
            "claim": "predicate-geometry compatibility route",
            "status": "allowed",
            "wording": "Validated for relative_vertical and size_relative; left/right is caveated lateral.",
        },
        {
            "claim": "relative_horizontal solved",
            "status": "blocked",
            "wording": "Do not claim; split left/right from front/behind.",
        },
        {
            "claim": "front/behind solved",
            "status": "blocked",
            "wording": "Use as reference-frame/depth ambiguity failure case.",
        },
        {
            "claim": "support/contact solved",
            "status": "blocked",
            "wording": "Use as hard contact/pose failure taxonomy.",
        },
        {
            "claim": "calibrated p_obs/p_rel solved",
            "status": "blocked",
            "wording": "Optional/future diagnostic only.",
        },
        {
            "claim": "official test / SOTA / leaderboard",
            "status": "blocked",
            "wording": "Validation-level custom evaluation only.",
        },
    ]


def report_text(summary: dict[str, Any], main_rows: list[dict[str, Any]], placement_rows: list[dict[str, Any]], appendix_rows: list[dict[str, Any]]) -> str:
    compact_main = [
        row
        for row in main_rows
        if row["route"] == "predicate_geometry_comparison" and int(row["K"]) in {5, 20, 50, 100}
    ] + [
        row
        for row in main_rows
        if row["route"] == "caveated_lateral_compatibility" and int(row["K"]) in {20, 50, 100}
    ]
    return f"""# H002 Main Validation Table Refresh After Lateral Lock

## Status

```text
status = {summary['status']}
validation_errors = {summary['validation_errors']}
main_rows = {summary['row_counts']['main_table_rows']}
appendix_rows = {summary['row_counts']['appendix_table_rows']}
selected_path = {summary['selected_path']}
next_todo = {summary['next_todo']}
```

## Table Placement

{markdown_table(placement_rows, ['route', 'relations', 'placement', 'status', 'reason'])}

## Main Table Preview

{markdown_table(compact_main, ['route', 'relations', 'source_scope', 'K', 'Delta_Recall@K', 'Delta_Recall_CI95', 'Delta_Violation@K', 'Delta_Violation_CI95', 'paper_role'])}

## Appendix / Analysis Rows

{markdown_table(appendix_rows[:12], ['route', 'relations', 'source_scope', 'K', 'Delta_Recall@K', 'Delta_Violation@K', 'paper_role', 'interpretation'])}

## Interpretation

`left/right` is now included as a caveated lateral main validated route.
`front/behind` remains a reference-frame/depth ambiguity failure case. Full
`relative_horizontal` is not a single solved route. Paper draft files were not
edited by this table refresh.
"""


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    errors = validate_inputs(args)
    if errors:
        summary = {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS_ERROR,
            "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "validation_errors": len(errors),
            "selected_path": "blocked_input_validation_failed",
            "next_todo": "fix_inputs_then_rerun_h002_main_validation_table_refresh",
        }
        write_json(out / "summary.json", summary)
        write_jsonl(out / "validation_errors.jsonl", errors)
        return 1

    control_rows = read_csv(args.source_reranking_dir / "control_metrics.csv")
    source_ci_rows = read_csv(args.source_ci_dir / "main_reranking_delta_ci.csv")
    lateral_compact_rows = read_csv(args.lateral_dir / "lateral_compact_table.csv")
    lateral_delta_rows = read_csv(args.lateral_dir / "subroute_delta_metrics.csv")
    proximity_delta_rows = read_csv(args.proximity_dir / "proximity_source_wide_deltas.csv")
    support_summary = read_json(args.support_contact_dir / "summary.json")
    lateral_summary = read_json(args.lateral_dir / "summary.json")

    core_rows = build_core_rows(control_rows, source_ci_rows)
    lateral_rows = build_lateral_rows(lateral_compact_rows)
    depth_rows = build_depth_rows(lateral_delta_rows)
    proximity_rows = build_proximity_rows(proximity_delta_rows)
    support_rows = build_support_rows(support_summary)
    main_rows = core_rows + lateral_rows
    appendix_rows = depth_rows + proximity_rows + support_rows
    placement_rows = table_placement_rows()
    boundary_rows = claim_boundary_rows()

    lateral_state = lateral_summary.get("subroutes", {}).get("lateral_left_right", {})
    depth_state = lateral_summary.get("subroutes", {}).get("depth_front_behind", {})
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_READY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "validation_errors": 0,
        "selected_path": "main_appendix_table_refreshed_after_lateral_lock",
        "main_validated_routes": [
            "predicate_geometry_comparison",
            "caveated_lateral_compatibility",
        ],
        "appendix_analysis_routes": [
            "frame_depth_ambiguity",
            "geometry_only_control",
            "hard_contact_pose",
        ],
        "blocked_routes": [
            "full_relative_horizontal_solved",
            "front_behind_solved",
            "support_contact_solved",
            "calibrated_pobs_prel_solved",
        ],
        "route_lock": {
            "left_right": lateral_state,
            "front_behind": depth_state,
        },
        "row_counts": {
            "main_table_rows": len(main_rows),
            "core_main_rows": len(core_rows),
            "lateral_caveated_rows": len(lateral_rows),
            "appendix_table_rows": len(appendix_rows),
            "placement_rows": len(placement_rows),
            "claim_boundary_rows": len(boundary_rows),
        },
        "paper_draft_files_edited": False,
        "outputs": {
            "main_table_csv": rel_path(repo_root, out / "main_table.csv"),
            "main_table_md": rel_path(repo_root, out / "main_table.md"),
            "appendix_table_csv": rel_path(repo_root, out / "appendix_table.csv"),
            "appendix_table_md": rel_path(repo_root, out / "appendix_table.md"),
            "table_placement_csv": rel_path(repo_root, out / "table_placement.csv"),
            "claim_boundary_csv": rel_path(repo_root, out / "claim_boundary.csv"),
            "report": rel_path(repo_root, out / "report.md"),
            "summary": rel_path(repo_root, out / "summary.json"),
            "validation_errors": rel_path(repo_root, out / "validation_errors.jsonl"),
        },
        "next_todo": NEXT_TODO,
    }

    write_csv(out / "main_table.csv", main_rows)
    write_csv(out / "appendix_table.csv", appendix_rows)
    write_csv(out / "table_placement.csv", placement_rows)
    write_csv(out / "claim_boundary.csv", boundary_rows)
    write_text(
        out / "main_table.md",
        markdown_table(
            main_rows,
            [
                "table_section",
                "route",
                "relations",
                "source_scope",
                "K",
                "Delta_Recall@K",
                "Delta_Recall_CI95",
                "Delta_Violation@K",
                "Delta_Violation_CI95",
                "paper_role",
                "caveat",
            ],
        )
        + "\n",
    )
    write_text(
        out / "appendix_table.md",
        markdown_table(
            appendix_rows,
            [
                "table_section",
                "route",
                "relations",
                "source_scope",
                "K",
                "Delta_Recall@K",
                "Delta_Violation@K",
                "paper_role",
                "interpretation",
            ],
        )
        + "\n",
    )
    write_text(out / "validation_errors.jsonl", "")
    write_json(out / "summary.json", summary)
    write_text(out / "report.md", report_text(summary, main_rows, placement_rows, appendix_rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
