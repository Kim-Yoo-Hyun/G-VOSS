#!/usr/bin/env python3
"""Create bounded H002 paper-table skeletons from the locked claim boundary."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_LOCK_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review"
DEFAULT_EVAL_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/official_evaluation/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock"

EXPECTED_LOCK_STATUS = "h002_compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review_locked"
EXPECTED_LOCK_NEXT = "compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock_v1"
STATUS_READY = "h002_compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock_input_errors"
SELECTED_PATH = "paper_table_skeleton_ready_select_table_review"
NEXT_TODO = "compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock"

METHOD_VIEWS = [
    ("M1_T_semantic_only", "T_e only", "semantic_content_baseline"),
    ("M2_G_geometry_only", "G_e only", "geometry_evidence_baseline"),
    ("M3_T_plus_G_concat", "T_e + G_e concat", "plain_concat_baseline"),
    ("M4_TxG_compatibility", "C_e compatibility", "proposed_mechanism"),
]

CONTROL_VIEWS = [
    ("C1_wrong_T_within_route", "wrong T within route", "predicate_matching_control"),
    ("C3_shuffled_G_global", "shuffled G global", "geometry_matching_control"),
    ("C4_shuffled_G_within_family", "shuffled G within family", "geometry_matching_control"),
    ("C5_subject_object_swap", "subject/object swap", "directionality_control"),
    ("C6_sign_flip", "sign flip", "signed_geometry_control"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock-dir", type=Path, default=DEFAULT_LOCK_DIR)
    parser.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
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
                fields.append(key)
                seen.add(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
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


def as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"


def row_lookup(rows: list[dict[str, str]], **filters: str) -> dict[str, str] | None:
    for row in rows:
        if all(row.get(key) == value for key, value in filters.items()):
            return row
    return None


def metric(rows: list[dict[str, str]], family: str, view_id: str, key: str) -> float | None:
    row = row_lookup(rows, level="route_family", route_family=family, view_id=view_id)
    return as_float(row.get(key) if row else None)


def macro(values: list[float | None]) -> float | None:
    clean = [value for value in values if value is not None]
    if len(clean) != len(values) or not clean:
        return None
    return mean(clean)


def validate_inputs(lock_summary: dict[str, Any], eval_manifest: dict[str, Any], lock_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if lock_summary.get("status") != EXPECTED_LOCK_STATUS:
        errors.append({"error_type": "unexpected_lock_status", "actual": lock_summary.get("status")})
    if lock_summary.get("next_todo") != EXPECTED_LOCK_NEXT:
        errors.append({"error_type": "unexpected_lock_next_todo", "actual": lock_summary.get("next_todo")})
    if lock_summary.get("validation_errors") != 0:
        errors.append({"error_type": "lock_validation_errors", "actual": lock_summary.get("validation_errors")})
    if line_count(lock_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "lock_validation_errors_file_not_empty"})

    decision = lock_summary.get("decision", {})
    if decision.get("claim_boundary_locked") is not True:
        errors.append({"error_type": "claim_boundary_not_locked"})
    if decision.get("paper_table_draft_allowed") is not True:
        errors.append({"error_type": "paper_table_draft_not_allowed"})
    if decision.get("final_paper_result_promotion") != "not_yet":
        errors.append({"error_type": "unexpected_final_paper_result_promotion", "actual": decision.get("final_paper_result_promotion")})
    if decision.get("primary_mechanism_families") != ["relative_vertical", "size_relative"]:
        errors.append({"error_type": "unexpected_primary_mechanism_families", "actual": decision.get("primary_mechanism_families")})

    boundary = eval_manifest.get("boundary", {})
    required = {
        "official_validation_eval_only": True,
        "official_test_usage": False,
        "official_validation_metric_produced": True,
        "paper_metric_produced": False,
        "z_e_excluded_from_main_C_e": True,
        "q_e_excluded_from_main_C_e": True,
        "h001_p_geom_valid_excluded_from_main_G_e": True,
    }
    for key, expected in required.items():
        if boundary.get(key) is not expected:
            errors.append({"error_type": "unexpected_eval_boundary", "key": key, "actual": boundary.get(key), "expected": expected})
    return errors


def main_table_rows(family_metrics: list[dict[str, str]]) -> list[dict[str, Any]]:
    primary_families = ["relative_vertical", "size_relative"]
    rows: list[dict[str, Any]] = []
    for view_id, display_name, role in METHOD_VIEWS:
        auc = macro([metric(family_metrics, family, view_id, "auroc") for family in primary_families])
        ba = macro([metric(family_metrics, family, view_id, "balanced_accuracy") for family in primary_families])
        auprc = macro([metric(family_metrics, family, view_id, "auprc") for family in primary_families])
        rows.append(
            {
                "table_block": "primary_mechanism_macro",
                "scope": "relative_vertical + size_relative",
                "view_id": view_id,
                "display_name": display_name,
                "method_role": role,
                "auroc": fmt(auc),
                "auprc": fmt(auprc),
                "balanced_accuracy": fmt(ba),
                "paper_interpretation": "main comparison row" if view_id == "M4_TxG_compatibility" else "baseline row",
                "claim_boundary": "primary signed comparison routes only",
            }
        )
    for family, role, note in [
        ("relative_horizontal", "caveated_frame_aware_row", "report separately; do not claim frame invariance"),
        ("support_contact", "diagnostic_failure_taxonomy_row", "report as challenging diagnostic only"),
    ]:
        m4 = row_lookup(family_metrics, level="route_family", route_family=family, view_id="M4_TxG_compatibility") or {}
        rows.append(
            {
                "table_block": role,
                "scope": family,
                "view_id": "M4_TxG_compatibility",
                "display_name": "C_e compatibility",
                "method_role": "proposed_mechanism_context",
                "auroc": fmt(as_float(m4.get("auroc"))),
                "auprc": fmt(as_float(m4.get("auprc"))),
                "balanced_accuracy": fmt(as_float(m4.get("balanced_accuracy"))),
                "paper_interpretation": note,
                "claim_boundary": note,
            }
        )
    return rows


def family_table_rows(family_metrics: list[dict[str, str]], role_lock: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for role in role_lock:
        family = role["route_family"]
        values = {view_id: metric(family_metrics, family, view_id, "auroc") for view_id, _, _ in METHOD_VIEWS}
        baselines = [values["M1_T_semantic_only"], values["M2_G_geometry_only"], values["M3_T_plus_G_concat"]]
        best_baseline = max(value for value in baselines if value is not None)
        m4 = values["M4_TxG_compatibility"]
        rows.append(
            {
                "route_family": family,
                "relation_types": role.get("relation_types", ""),
                "paper_success_role": role.get("paper_success_role", ""),
                "locked_table_role": role.get("locked_table_role", ""),
                "rows": role.get("rows", ""),
                "positive": role.get("positive", ""),
                "negative": role.get("negative", ""),
                "m1_semantic_auroc": fmt(values["M1_T_semantic_only"]),
                "m2_geometry_auroc": fmt(values["M2_G_geometry_only"]),
                "m3_concat_auroc": fmt(values["M3_T_plus_G_concat"]),
                "m4_compatibility_auroc": fmt(m4),
                "m4_minus_best_baseline": fmt(m4 - best_baseline if m4 is not None else None),
                "m4_balanced_accuracy": role.get("m4_balanced_accuracy", ""),
                "required_caveat": role.get("must_report_caveat", ""),
                "claim_boundary": role.get("claim_boundary", ""),
            }
        )
    return rows


def control_rows(family_metrics: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    primary_families = ["relative_vertical", "size_relative"]
    m4_primary = macro([metric(family_metrics, family, "M4_TxG_compatibility", "auroc") for family in primary_families])
    for view_id, display_name, role in [
        *[(view_id, display_name, role) for view_id, display_name, role in METHOD_VIEWS[:3]],
        *CONTROL_VIEWS,
    ]:
        baseline = macro([metric(family_metrics, family, view_id, "auroc") for family in primary_families])
        rows.append(
            {
                "control_scope": "primary_mechanism_macro",
                "families": "relative_vertical + size_relative",
                "comparison": f"M4_vs_{view_id}",
                "control_name": display_name,
                "control_role": role,
                "m4_auroc": fmt(m4_primary),
                "control_auroc": fmt(baseline),
                "delta_auroc": fmt(m4_primary - baseline if m4_primary is not None and baseline is not None else None),
                "paper_role": "main control" if view_id in {"M1_T_semantic_only", "M2_G_geometry_only", "M3_T_plus_G_concat", "C1_wrong_T_within_route", "C3_shuffled_G_global", "C4_shuffled_G_within_family"} else "supporting control",
            }
        )

    for family, view_id, label, note in [
        ("relative_horizontal", "C7_horizontal_frame_swap", "horizontal frame swap", "caveat: modest frame-control margin"),
        ("support_contact", "C2_wrong_T_across_route", "wrong T across route", "diagnostic: control does not collapse"),
        ("support_contact", "C4_shuffled_G_within_family", "shuffled G within family", "diagnostic: weak geometry-control margin"),
    ]:
        m4 = metric(family_metrics, family, "M4_TxG_compatibility", "auroc")
        baseline = metric(family_metrics, family, view_id, "auroc")
        rows.append(
            {
                "control_scope": family,
                "families": family,
                "comparison": f"M4_vs_{view_id}",
                "control_name": label,
                "control_role": "caveat_or_diagnostic_control",
                "m4_auroc": fmt(m4),
                "control_auroc": fmt(baseline),
                "delta_auroc": fmt(m4 - baseline if m4 is not None and baseline is not None else None),
                "paper_role": note,
            }
        )
    return rows


def promotion_checklist_rows() -> list[dict[str, Any]]:
    return [
        {
            "item": "official_validation_only",
            "status": "locked",
            "paper_action": "state validation-only provenance in caption",
        },
        {
            "item": "official_test_unused",
            "status": "locked",
            "paper_action": "do not mention test performance",
        },
        {
            "item": "primary_rows",
            "status": "locked",
            "paper_action": "use relative_vertical and size_relative as primary mechanism evidence",
        },
        {
            "item": "relative_horizontal",
            "status": "caveated",
            "paper_action": "report separately as frame-aware evidence; include frame-control caveat",
        },
        {
            "item": "support_contact",
            "status": "diagnostic",
            "paper_action": "use only in failure taxonomy or limitation table",
        },
        {
            "item": "final_paper_result_promotion",
            "status": "not_yet",
            "paper_action": "review table skeleton before promoting to paper-facing results",
        },
    ]


def write_markdown_report(
    path: Path,
    summary: dict[str, Any],
    main_rows: list[dict[str, Any]],
    family_rows: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> None:
    lines = [
        "# H002 Paper Table Skeleton After Claim Boundary Lock",
        "",
        "## Status",
        "",
        "```text",
        f"artifact_root = {summary['output_artifacts']['artifact_root']}",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Table Skeleton Decision",
        "",
        "- This is a bounded table draft, not final paper-result promotion.",
        "- Primary mechanism rows are restricted to `relative_vertical` and `size_relative`.",
        "- `relative_horizontal` is a caveated frame-aware row.",
        "- `support_contact` is a diagnostic/failure-taxonomy row.",
        "",
        "## Main Table Skeleton",
        "",
        "| Block | Scope | Method | AUROC | AUPRC | Balanced Acc. | Interpretation |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in main_rows:
        lines.append(
            "| {table_block} | {scope} | {display_name} | {auroc} | {auprc} | {balanced_accuracy} | {paper_interpretation} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Family Rows",
            "",
            "| Family | Role | M1 | M2 | M3 | M4 | M4 - Best Baseline | Caveat |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in family_rows:
        lines.append(
            "| {route_family} | {paper_success_role} | {m1_semantic_auroc} | {m2_geometry_auroc} | {m3_concat_auroc} | {m4_compatibility_auroc} | {m4_minus_best_baseline} | {required_caveat} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Control Rows",
            "",
            "| Scope | Control | M4 AUROC | Control AUROC | Delta | Role |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in controls:
        lines.append(
            "| {control_scope} | {control_name} | {m4_auroc} | {control_auroc} | {delta_auroc} | {paper_role} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Draft Caption",
            "",
            "Official-validation mechanism evaluation for H002 `C_e = compatibility(T_e, G_e)`. "
            "The primary block reports only the locked signed-comparison routes "
            "(`relative_vertical` and `size_relative`). `relative_horizontal` is reported as "
            "frame-aware caveated evidence, and `support_contact` is diagnostic. The table does "
            "not use official test data and does not evaluate source reranking, calibrated "
            "`p_rel`/`p_obs`, or all-relation 3DSSG performance.",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    lock_dir = args.lock_dir
    eval_dir = args.eval_dir
    output_dir = args.output_dir

    lock_summary = read_json(lock_dir / "summary.json")
    eval_manifest = read_json(eval_dir / "eval_manifest.json")
    family_metrics = read_csv(eval_dir / "family_metrics.csv")
    role_lock = read_csv(lock_dir / "table_role_lock.csv")
    validation_errors = validate_inputs(lock_summary, eval_manifest, lock_dir)

    main_rows = main_table_rows(family_metrics)
    family_rows = family_table_rows(family_metrics, role_lock)
    controls = control_rows(family_metrics)
    checklist = promotion_checklist_rows()

    status = STATUS_ERRORS if validation_errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH if not validation_errors else "blocked_fix_inputs_before_table_skeleton",
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO if not validation_errors else EXPECTED_LOCK_NEXT,
        "input_artifacts": {
            "lock_summary": rel_path(lock_dir / "summary.json"),
            "table_role_lock": rel_path(lock_dir / "table_role_lock.csv"),
            "family_metrics": rel_path(eval_dir / "family_metrics.csv"),
            "aggregate_metrics": rel_path(eval_dir / "aggregate_metrics.csv"),
            "control_metrics": rel_path(eval_dir / "control_metrics.csv"),
            "eval_manifest": rel_path(eval_dir / "eval_manifest.json"),
        },
        "decision": {
            "paper_table_skeleton_ready": not validation_errors,
            "final_paper_result_promotion": "not_yet",
            "primary_table_scope": "relative_vertical + size_relative",
            "caveated_rows": ["relative_horizontal"],
            "diagnostic_rows": ["support_contact"],
            "official_test_usage": False,
            "source_reranking_claim_enabled": False,
            "p_rel_p_obs_claim_enabled": False,
        },
        "output_artifacts": {
            "artifact_root": rel_path(output_dir),
            "main_table_skeleton": rel_path(output_dir / "main_table_skeleton.csv"),
            "family_table_skeleton": rel_path(output_dir / "family_table_skeleton.csv"),
            "control_table_skeleton": rel_path(output_dir / "control_table_skeleton.csv"),
            "promotion_checklist": rel_path(output_dir / "promotion_checklist.csv"),
            "paper_table_skeleton_md": rel_path(output_dir / "paper_table_skeleton.md"),
            "report": rel_path(output_dir / "report.md"),
        },
    }

    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(output_dir / "main_table_skeleton.csv", main_rows)
    write_csv(output_dir / "family_table_skeleton.csv", family_rows)
    write_csv(output_dir / "control_table_skeleton.csv", controls)
    write_csv(output_dir / "promotion_checklist.csv", checklist)
    write_markdown_report(output_dir / "paper_table_skeleton.md", summary, main_rows, family_rows, controls)
    write_markdown_report(output_dir / "report.md", summary, main_rows, family_rows, controls)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
