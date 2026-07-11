#!/usr/bin/env python3
"""Build a compact qualitative evidence package for the scoped H002 claim.

This stage does not create a new score, run a new metric, train a model, or
promote any route. It samples row-pattern examples from existing selected
prediction artifacts and pairs them with the locked route-level summaries.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h002_qualitative_evidence_package_v1"
STATUS_READY = "h002_qualitative_evidence_package_ready"
STATUS_ERROR = "h002_qualitative_evidence_package_errors"
NEXT_TODO = "h002_extension_stage_e2_user_decision_gate_after_qualitative_package_when_requested"

PRIMARY_ROUTES = {"relative_vertical", "size_relative"}
SOURCE_BASELINE_SCORE = "S0_source_score"
SOURCE_COMP_SCORES = {"S2_current_source_x_Ce", "S2_source_x_Ce"}
HORIZONTAL_BASELINE_SCORE = "RH0_source_score"
HORIZONTAL_FRAME_SCORE = "RH1_source_x_frame_score"
QUALITATIVE_TOPK = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--source-selected",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/source_reranking_evaluation/latest/selected_predictions.jsonl"),
    )
    parser.add_argument(
        "--horizontal-selected",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/relative_horizontal_split_route_scorer/latest/selected_predictions.jsonl"),
    )
    parser.add_argument(
        "--main-table",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/main_validation_table_refresh/latest/main_table.csv"),
    )
    parser.add_argument(
        "--appendix-table",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/main_validation_table_refresh/latest/appendix_table.csv"),
    )
    parser.add_argument(
        "--proximity-metrics",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/proximity_geometry_only_diagnostic/latest/proximity_geometry_control_metrics.csv"),
    )
    parser.add_argument(
        "--support-summary",
        type=Path,
        default=Path(
            "experiments/H002_compatibility_routing/"
            "support_contact_independent_target_repair_diagnostic_freeze/latest/summary.json"
        ),
    )
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
                fields.append(key)
                seen.add(key)
    if not rows:
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def compact_row(row: dict[str, Any], evidence_level: str, case_id: str, interpretation: str) -> dict[str, Any]:
    keep = [
        "source_id",
        "subgraph_id",
        "candidate_id",
        "predicate_label",
        "route_family",
        "subroute",
        "score_id",
        "rank",
        "score",
        "source_score",
        "K",
        "gt_exact_match",
        "violation_checkable",
        "violation_status",
    ]
    out = {key: row.get(key, "") for key in keep}
    out.update(
        {
            "case_id": case_id,
            "evidence_level": evidence_level,
            "interpretation": interpretation,
        }
    )
    return out


def rank_value(row: dict[str, Any]) -> int:
    try:
        return int(row.get("rank", 10**9))
    except (TypeError, ValueError):
        return 10**9


def score_value(row: dict[str, Any]) -> float:
    try:
        return float(row.get("score", -1.0))
    except (TypeError, ValueError):
        return -1.0


def better_candidate(rows: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    items = list(rows)
    if not items:
        return None
    return sorted(items, key=lambda row: (rank_value(row), -score_value(row), str(row.get("candidate_id", ""))))[0]


def source_examples(source_selected: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    s0_rows: dict[str, dict[str, Any]] = {}
    s2_rows: dict[str, dict[str, Any]] = {}
    support_diagnostic: dict[str, Any] | None = None
    scanned = 0
    matched_primary = 0
    with source_selected.open("r", encoding="utf-8") as handle:
        for line in handle:
            scanned += 1
            row = json.loads(line)
            score_id = row.get("score_id")
            if row.get("route_family") == "support_contact" and support_diagnostic is None:
                support_diagnostic = row
            # The source-selected artifact stores a K=100 selected pool; top-K
            # slices are recovered by the score-specific rank field.
            if row.get("K") != 100 or rank_value(row) > QUALITATIVE_TOPK:
                continue
            if row.get("route_family") not in PRIMARY_ROUTES:
                continue
            if score_id not in ({SOURCE_BASELINE_SCORE} | SOURCE_COMP_SCORES):
                continue
            matched_primary += 1
            cid = row.get("candidate_id")
            if not cid:
                continue
            if score_id == SOURCE_BASELINE_SCORE:
                s0_rows.setdefault(cid, row)
            elif score_id in SOURCE_COMP_SCORES:
                s2_rows.setdefault(cid, row)

    s0_ids = set(s0_rows)
    s2_ids = set(s2_rows)
    cases: list[dict[str, Any]] = []

    filtered = better_candidate(
        row
        for cid, row in s0_rows.items()
        if cid not in s2_ids
        and row.get("gt_exact_match") is False
        and row.get("violation_status") == "violated"
    )
    if filtered:
        cases.append(
            compact_row(
                filtered,
                "selected_prediction_row",
                "comparison_source_violation_filtered_by_scomp",
                "A source-selected comparison candidate is GT-negative and geometry-violated; it drops out of the S_comp top-20 set.",
            )
        )

    promoted = better_candidate(
        row
        for cid, row in s2_rows.items()
        if cid not in s0_ids
        and row.get("gt_exact_match") is True
        and row.get("violation_status") == "satisfied"
    )
    if promoted:
        cases.append(
            compact_row(
                promoted,
                "selected_prediction_row",
                "comparison_gt_match_promoted_by_scomp",
                "A comparison candidate selected by S_comp is GT-positive and geometry-satisfied but absent from the source-score top-20 set.",
            )
        )

    safe_selected = better_candidate(
        row
        for row in s2_rows.values()
        if row.get("violation_status") == "satisfied"
    )
    if safe_selected:
        cases.append(
            compact_row(
                safe_selected,
                "selected_prediction_row",
                "comparison_scomp_satisfied_selection",
                "S_comp selects a geometry-satisfied comparison candidate, illustrating the Recall-Violation tradeoff target.",
            )
        )

    if support_diagnostic:
        cases.append(
            compact_row(
                support_diagnostic,
                "selected_prediction_row_boundary",
                "support_contact_diagnostic_only_row",
                "Support/contact rows are present in the source pool, but the current violation target is diagnostic-only and not promoted.",
            )
        )

    stats = {
        "source_selected_rows_scanned": scanned,
        "source_primary_k20_rows_matched": matched_primary,
        "source_primary_k20_s0_unique": len(s0_rows),
        "source_primary_k20_s2_unique": len(s2_rows),
        "source_primary_k20_overlap": len(s0_ids & s2_ids),
    }
    return cases, stats


def horizontal_examples(horizontal_selected: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    lateral_base: dict[str, dict[str, Any]] = {}
    lateral_frame: dict[str, dict[str, Any]] = {}
    depth_frame: list[dict[str, Any]] = []
    scanned = 0
    with horizontal_selected.open("r", encoding="utf-8") as handle:
        for line in handle:
            scanned += 1
            row = json.loads(line)
            score_id = row.get("score_id")
            cid = row.get("candidate_id")
            if not cid:
                continue
            if row.get("subroute") == "lateral_left_right" and rank_value(row) <= 20:
                if score_id == HORIZONTAL_BASELINE_SCORE:
                    lateral_base.setdefault(cid, row)
                elif score_id == HORIZONTAL_FRAME_SCORE:
                    lateral_frame.setdefault(cid, row)
            if row.get("subroute") == "depth_front_behind" and score_id == HORIZONTAL_FRAME_SCORE and rank_value(row) <= 20:
                if len(depth_frame) < 1000:
                    depth_frame.append(row)

    base_ids = set(lateral_base)
    frame_ids = set(lateral_frame)
    cases: list[dict[str, Any]] = []
    filtered_lateral = better_candidate(
        row
        for cid, row in lateral_base.items()
        if cid not in frame_ids
        and row.get("gt_exact_match") is False
        and row.get("violation_status") == "violated"
    )
    if filtered_lateral:
        cases.append(
            compact_row(
                filtered_lateral,
                "selected_prediction_row",
                "left_right_source_violation_filtered_by_frame_route",
                "A source-ranked left/right candidate is geometry-violated and is filtered out by the frame-aware lateral route.",
            )
        )

    lateral_true = better_candidate(
        row
        for cid, row in lateral_frame.items()
        if cid not in base_ids
        and row.get("gt_exact_match") is True
        and row.get("violation_status") == "satisfied"
    )
    if lateral_true:
        cases.append(
            compact_row(
                lateral_true,
                "selected_prediction_row",
                "left_right_gt_match_promoted_by_frame_route",
                "The caveated left/right route promotes a GT-positive and geometry-satisfied candidate.",
            )
        )

    depth_case = better_candidate(
        row
        for row in depth_frame
        if row.get("gt_exact_match") is False and row.get("violation_status") == "satisfied"
    )
    if depth_case:
        cases.append(
            compact_row(
                depth_case,
                "selected_prediction_row_boundary",
                "front_behind_depth_ambiguity_row",
                "A front/behind row can be geometry-satisfied by the frame score but still GT-negative, motivating the depth/reference-frame failure boundary.",
            )
        )

    stats = {
        "horizontal_rows_scanned": scanned,
        "lateral_rank20_baseline_unique": len(lateral_base),
        "lateral_rank20_frame_unique": len(lateral_frame),
        "lateral_rank20_overlap": len(base_ids & frame_ids),
        "depth_rank20_frame_sampled": len(depth_frame),
    }
    return cases, stats


def build_route_summary(
    main_rows: list[dict[str, str]],
    appendix_rows: list[dict[str, str]],
    proximity_rows: list[dict[str, str]],
    support_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in main_rows:
        if row.get("K") in {"10", "20", "50"}:
            rows.append(
                {
                    "case_id": f"metric_{row.get('route')}_K{row.get('K')}_{row.get('source_scope')}",
                    "evidence_level": "route_metric_summary",
                    "route": row.get("route"),
                    "relations": row.get("relations"),
                    "source_scope": row.get("source_scope"),
                    "K": row.get("K"),
                    "delta_recall": row.get("Delta_Recall@K"),
                    "delta_recall_ci95": row.get("Delta_Recall_CI95"),
                    "delta_violation": row.get("Delta_Violation@K"),
                    "delta_violation_ci95": row.get("Delta_Violation_CI95"),
                    "paper_role": row.get("paper_role"),
                    "interpretation": row.get("caveat"),
                }
            )
    for row in appendix_rows:
        if row.get("route") in {"frame_depth_ambiguity", "geometry_only_control"} and row.get("K") in {"20", "50"}:
            rows.append(
                {
                    "case_id": f"appendix_{row.get('route')}_K{row.get('K')}_{row.get('source_scope')}",
                    "evidence_level": "appendix_metric_summary",
                    "route": row.get("route"),
                    "relations": row.get("relations"),
                    "source_scope": row.get("source_scope"),
                    "K": row.get("K"),
                    "delta_recall": row.get("Delta_Recall@K"),
                    "delta_violation": row.get("Delta_Violation@K"),
                    "paper_role": row.get("paper_role"),
                    "interpretation": row.get("interpretation"),
                }
            )
    for row in proximity_rows:
        rows.append(
            {
                "case_id": f"proximity_control_{row.get('control_name')}",
                "evidence_level": "geometry_only_control_summary",
                "route": "geometry_only_control",
                "relations": "close by",
                "control_name": row.get("control_name"),
                "auroc": row.get("auroc"),
                "best_accuracy": row.get("best_accuracy"),
                "interpretation": row.get("interpretation"),
            }
        )
    rows.append(
        {
            "case_id": "support_contact_diagnostic_freeze",
            "evidence_level": "route_boundary_summary",
            "route": "hard_contact_pose",
            "relations": "standing on, lying on, supported by",
            "status": support_summary.get("status"),
            "selected_policy": support_summary.get("selected_policy"),
            "support_contact_solved_claim_allowed": support_summary.get("boundary", {}).get("support_contact_solved_claim_allowed"),
            "metric_rerun_allowed_now": support_summary.get("boundary", {}).get("metric_rerun_allowed_now"),
            "interpretation": "Support/contact remains a hard-route diagnostic; current H002 claim is unchanged.",
        }
    )
    return rows


def md_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(str(row.get(column, "")) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, sep, *body])


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out = resolve(repo_root, args.out)
    paths = {
        "source_selected": resolve(repo_root, args.source_selected),
        "horizontal_selected": resolve(repo_root, args.horizontal_selected),
        "main_table": resolve(repo_root, args.main_table),
        "appendix_table": resolve(repo_root, args.appendix_table),
        "proximity_metrics": resolve(repo_root, args.proximity_metrics),
        "support_summary": resolve(repo_root, args.support_summary),
    }
    errors: list[dict[str, Any]] = []
    for name, path in paths.items():
        if not path.exists():
            errors.append({"error_type": "missing_input", "input": name, "path": rel_path(repo_root, path)})

    cases: list[dict[str, Any]] = []
    stats: dict[str, Any] = {}
    route_summary: list[dict[str, Any]] = []
    if not errors:
        source_cases, source_stats = source_examples(paths["source_selected"])
        horizontal_cases, horizontal_stats = horizontal_examples(paths["horizontal_selected"])
        cases.extend(source_cases)
        cases.extend(horizontal_cases)
        stats.update(source_stats)
        stats.update(horizontal_stats)
        route_summary = build_route_summary(
            read_csv(paths["main_table"]),
            read_csv(paths["appendix_table"]),
            read_csv(paths["proximity_metrics"]),
            read_json(paths["support_summary"]),
        )

    required_case_ids = {
        "comparison_source_violation_filtered_by_scomp",
        "comparison_gt_match_promoted_by_scomp",
        "left_right_source_violation_filtered_by_frame_route",
        "front_behind_depth_ambiguity_row",
        "support_contact_diagnostic_only_row",
    }
    found = {row.get("case_id") for row in cases}
    missing_required = sorted(required_case_ids - found)
    for case_id in missing_required:
        errors.append({"error_type": "missing_required_case", "case_id": case_id})

    validation_errors_path = out / "validation_errors.jsonl"
    write_jsonl(validation_errors_path, errors)
    write_jsonl(out / "qualitative_cases.jsonl", cases)
    write_csv(out / "qualitative_cases.csv", cases)
    write_csv(out / "route_pattern_summary.csv", route_summary)

    status = STATUS_READY if not errors else STATUS_ERROR
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "validation_errors": len(errors),
        "next_todo": NEXT_TODO,
        "claim_changed": False,
        "metric_rerun_opened": False,
        "training_opened": False,
        "paper_files_edited": False,
        "case_count": len(cases),
        "route_summary_rows": len(route_summary),
        "required_case_ids": sorted(required_case_ids),
        "missing_required_case_ids": missing_required,
        "stats": stats,
        "outputs": {
            "qualitative_cases_jsonl": rel_path(repo_root, out / "qualitative_cases.jsonl"),
            "qualitative_cases_csv": rel_path(repo_root, out / "qualitative_cases.csv"),
            "route_pattern_summary": rel_path(repo_root, out / "route_pattern_summary.csv"),
            "case_summary": rel_path(repo_root, out / "case_summary.md"),
            "report": rel_path(repo_root, out / "report.md"),
            "summary": rel_path(repo_root, out / "summary.json"),
            "validation_errors": rel_path(repo_root, validation_errors_path),
        },
    }
    write_json(out / "summary.json", summary)

    case_columns = [
        "case_id",
        "evidence_level",
        "source_id",
        "route_family",
        "subroute",
        "predicate_label",
        "score_id",
        "rank",
        "K",
        "gt_exact_match",
        "violation_status",
        "interpretation",
    ]
    route_columns = [
        "case_id",
        "evidence_level",
        "route",
        "relations",
        "source_scope",
        "K",
        "delta_recall",
        "delta_violation",
        "interpretation",
    ]
    case_summary = "\n".join(
        [
            "# H002 Qualitative Evidence Package",
            "",
            "## Purpose",
            "",
            "This package supports the scoped H002 paper claim with row-pattern examples and locked route summaries. It does not change the score, route scope, or paper claim.",
            "",
            "## Candidate-Level Cases",
            "",
            md_table(cases, case_columns),
            "",
            "## Route-Level Patterns",
            "",
            md_table(route_summary[:20], route_columns),
            "",
            "## Boundary",
            "",
            "- This is not a new benchmark result.",
            "- It does not promote support/contact, p_obs/p_rel, learned G_e, H003, or all-relation reliability.",
            "- It should be used as appendix/qualitative support for the existing scoped validation claim.",
            "",
        ]
    )
    write_text(out / "case_summary.md", case_summary)

    report = "\n".join(
        [
            "# H002 Qualitative Evidence Package",
            "",
            "## Status",
            "",
            "```text",
            f"status = {status}",
            f"validation_errors = {len(errors)}",
            f"case_count = {len(cases)}",
            f"route_summary_rows = {len(route_summary)}",
            "claim_changed = false",
            "metric_rerun_opened = false",
            "```",
            "",
            "## Interpretation",
            "",
            "The package converts existing locked artifacts into paper-facing qualitative evidence. It shows source-selected violated comparison rows, S_comp-selected satisfied rows, the caveated left/right pattern, the front/behind boundary, and the support/contact diagnostic-only boundary.",
            "",
            "## Outputs",
            "",
            md_table(
                [{"artifact": key, "path": value} for key, value in summary["outputs"].items()],
                ["artifact", "path"],
            ),
            "",
        ]
    )
    write_text(out / "report.md", report)


if __name__ == "__main__":
    main()
