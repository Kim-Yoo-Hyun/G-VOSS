#!/usr/bin/env python3
"""Validate and summarize the H002 official metric runner output."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PROTOCOL_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit"
DEFAULT_EVAL_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/official_evaluation/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_metric_runner_after_protocol_freeze"

EXPECTED_PROTOCOL_STATUS = "h002_compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit_ready"
EXPECTED_PROTOCOL_NEXT = "compatibility_dataset_v3_official_metric_runner_after_protocol_freeze"
EXPECTED_EVAL_STATUS = "ready"
EXPECTED_OFFICIAL_ROWS = 23062

SCHEMA_VERSION = "h002_compatibility_dataset_v3_official_metric_runner_after_protocol_freeze_v1"
STATUS_READY = "h002_compatibility_dataset_v3_official_metric_runner_after_protocol_freeze_ready_with_caveats"
STATUS_ERRORS = "h002_compatibility_dataset_v3_official_metric_runner_after_protocol_freeze_input_errors"
SELECTED_PATH = "official_metric_runner_ready_select_result_review"
NEXT_TODO = "compatibility_dataset_v3_official_metric_result_review_after_runner"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-dir", type=Path, default=DEFAULT_PROTOCOL_DIR)
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
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def row_lookup(rows: list[dict[str, str]], **filters: str) -> dict[str, str] | None:
    for row in rows:
        if all(row.get(key) == value for key, value in filters.items()):
            return row
    return None


def validate_inputs(protocol: dict[str, Any], manifest: dict[str, Any], eval_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if protocol.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error_type": "unexpected_protocol_status", "actual": protocol.get("status")})
    if protocol.get("next_todo") != EXPECTED_PROTOCOL_NEXT:
        errors.append({"error_type": "unexpected_protocol_next_todo", "actual": protocol.get("next_todo")})
    if manifest.get("status") != EXPECTED_EVAL_STATUS:
        errors.append({"error_type": "unexpected_eval_status", "actual": manifest.get("status")})
    if manifest.get("validation_errors") != 0:
        errors.append({"error_type": "eval_manifest_validation_errors", "actual": manifest.get("validation_errors")})
    if line_count(eval_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "eval_validation_errors_file_not_empty"})
    row_counts = manifest.get("row_counts", {})
    if row_counts.get("official_validation") != EXPECTED_OFFICIAL_ROWS:
        errors.append({"error_type": "unexpected_official_validation_rows", "actual": row_counts.get("official_validation")})
    if row_counts.get("prediction_rows") != EXPECTED_OFFICIAL_ROWS:
        errors.append({"error_type": "unexpected_prediction_rows", "actual": row_counts.get("prediction_rows")})
    boundary = manifest.get("boundary", {})
    expected_boundary = {
        "official_validation_metric_produced": True,
        "official_validation_eval_only": True,
        "official_test_usage": False,
        "paper_metric_produced": False,
        "p_obs_claim_enabled": False,
        "p_rel_claim_enabled": False,
        "z_e_excluded_from_main_C_e": True,
        "q_e_excluded_from_main_C_e": True,
        "h001_p_geom_valid_excluded_from_main_G_e": True,
    }
    for key, expected in expected_boundary.items():
        if boundary.get(key) is not expected:
            errors.append({"error_type": "unexpected_boundary_value", "key": key, "actual": boundary.get(key), "expected": expected})
    return errors


def metric_snapshot(aggregate_rows: list[dict[str, str]], family_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    key_views = [
        "M1_T_semantic_only",
        "M2_G_geometry_only",
        "M3_T_plus_G_concat",
        "M4_TxG_compatibility",
        "C1_wrong_T_within_route",
        "C3_shuffled_G_global",
        "C4_shuffled_G_within_family",
        "C7_horizontal_frame_swap",
    ]
    for view_id in key_views:
        macro = row_lookup(aggregate_rows, level="macro_family_primary", view_id=view_id) or {}
        overall = row_lookup(aggregate_rows, level="overall_secondary", view_id=view_id) or {}
        rows.append(
            {
                "scope": "aggregate",
                "route_family": "ALL",
                "view_id": view_id,
                "macro_family_auroc": macro.get("macro_family_auroc"),
                "weighted_family_auroc": macro.get("weighted_family_auroc"),
                "overall_auroc": overall.get("auroc"),
                "macro_family_auprc": macro.get("macro_family_auprc"),
            }
        )
    for family in ["relative_horizontal", "relative_vertical", "size_relative", "support_contact"]:
        row = row_lookup(family_rows, route_family=family, view_id="M4_TxG_compatibility") or {}
        rows.append(
            {
                "scope": "family_M4",
                "route_family": family,
                "view_id": "M4_TxG_compatibility",
                "auroc": row.get("auroc"),
                "auprc": row.get("auprc"),
                "balanced_accuracy": row.get("balanced_accuracy"),
                "positive": row.get("positive"),
                "negative": row.get("negative"),
            }
        )
    return rows


def control_snapshot(control_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for comparison in [
        "M4_vs_M1",
        "M4_vs_M2",
        "M4_vs_M3",
        "M4_vs_wrong_T_within_route",
        "M4_vs_wrong_T_across_route",
        "M4_vs_shuffled_G_global",
        "M4_vs_shuffled_G_within_family",
        "M4_vs_subject_object_swap",
        "M4_vs_sign_flip",
        "M4_vs_horizontal_frame_swap",
    ]:
        row = row_lookup(control_rows, level="macro_family_primary", comparison=comparison) or {}
        rows.append(
            {
                "comparison": comparison,
                "primary_auroc": row.get("primary_auroc"),
                "baseline_auroc": row.get("baseline_auroc"),
                "delta_auroc": row.get("delta_auroc"),
                "interpretation": control_interpretation(comparison, as_float(row.get("delta_auroc"))),
            }
        )
    return rows


def control_interpretation(comparison: str, delta: float | None) -> str:
    if delta is None:
        return "missing"
    if comparison in {"M4_vs_M1", "M4_vs_M2", "M4_vs_M3"}:
        return "passes_primary_delta" if delta > 0 else "fails_primary_delta"
    if comparison == "M4_vs_horizontal_frame_swap":
        return "weak_control_margin" if delta < 0.05 else "control_degrades"
    return "control_degrades" if delta > 0 else "control_not_degraded"


def caveats(family_rows: list[dict[str, str]], control_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    support = row_lookup(family_rows, route_family="support_contact", view_id="M4_TxG_compatibility")
    support_auc = as_float(support.get("auroc") if support else None)
    if support_auc is not None and support_auc < 0.70:
        rows.append(
            {
                "caveat": "support_contact_challenging",
                "value": support_auc,
                "interpretation": "support_contact remains diagnostic/challenging, not solved",
            }
        )
    horiz = row_lookup(control_rows, level="macro_family_primary", comparison="M4_vs_horizontal_frame_swap")
    horiz_delta = as_float(horiz.get("delta_auroc") if horiz else None)
    if horiz_delta is not None and horiz_delta < 0.05:
        rows.append(
            {
                "caveat": "horizontal_frame_swap_weak_margin",
                "value": horiz_delta,
                "interpretation": "relative_horizontal frame-control needs result review before strong route claim",
            }
        )
    return rows


def report_text(
    *,
    status: str,
    validation_errors: list[dict[str, Any]],
    output_dir: Path,
    metric_rows: list[dict[str, Any]],
    controls: list[dict[str, Any]],
    caveat_rows: list[dict[str, Any]],
) -> str:
    m4_macro = next((row for row in metric_rows if row.get("scope") == "aggregate" and row.get("view_id") == "M4_TxG_compatibility"), {})
    lines = [
        "# H002 Official Metric Runner After Protocol Freeze",
        "",
        "## Status",
        "",
        "```text",
        f"artifact_root = {rel_path(output_dir)}/",
        f"status = {status}",
        f"selected_path = {SELECTED_PATH if not validation_errors else 'blocked_fix_runner_outputs'}",
        f"validation_errors = {len(validation_errors)}",
        f"next_todo = {NEXT_TODO if not validation_errors else 'fix_official_metric_runner_outputs'}",
        "```",
        "",
        "## Official Validation Metric Snapshot",
        "",
        f"- M4 macro-family AUROC: `{m4_macro.get('macro_family_auroc')}`",
        f"- M4 weighted-family AUROC: `{m4_macro.get('weighted_family_auroc')}`",
        f"- M4 overall AUROC: `{m4_macro.get('overall_auroc')}`",
        "",
        "## Control Snapshot",
        "",
    ]
    for row in controls:
        lines.append(
            f"- `{row['comparison']}`: delta AUROC `{row.get('delta_auroc')}` "
            f"({row.get('interpretation')})"
        )
    lines.extend(["", "## Caveats", ""])
    if caveat_rows:
        for row in caveat_rows:
            lines.append(f"- `{row['caveat']}`: `{row['value']}` - {row['interpretation']}")
    else:
        lines.append("- none recorded")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Official validation metric was produced.",
            "- Official validation was eval-only.",
            "- Official test was not used.",
            "- No paper-level result was promoted.",
            "- `p_rel` / `p_obs` remain disabled.",
            "",
            "## Next",
            "",
            "```text",
            NEXT_TODO,
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    protocol = read_json(args.protocol_dir / "summary.json")
    manifest = read_json(args.eval_dir / "eval_manifest.json")
    aggregate_rows = read_csv(args.eval_dir / "aggregate_metrics.csv")
    family_rows = read_csv(args.eval_dir / "family_metrics.csv")
    control_rows = read_csv(args.eval_dir / "control_metrics.csv")

    validation_errors = validate_inputs(protocol, manifest, args.eval_dir)
    metrics = metric_snapshot(aggregate_rows, family_rows)
    controls = control_snapshot(control_rows)
    caveat_rows = caveats(family_rows, control_rows)
    status = STATUS_READY if not validation_errors else STATUS_ERRORS
    selected_path = SELECTED_PATH if not validation_errors else "blocked_fix_runner_outputs"
    next_todo = NEXT_TODO if not validation_errors else "fix_official_metric_runner_outputs"

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(validation_errors),
        "next_todo": next_todo,
        "input_artifacts": {
            "eval_manifest": rel_path(args.eval_dir / "eval_manifest.json"),
            "aggregate_metrics": rel_path(args.eval_dir / "aggregate_metrics.csv"),
            "family_metrics": rel_path(args.eval_dir / "family_metrics.csv"),
            "control_metrics": rel_path(args.eval_dir / "control_metrics.csv"),
            "protocol_summary": rel_path(args.protocol_dir / "summary.json"),
        },
        "output_artifacts": {
            "metric_snapshot": rel_path(args.output_dir / "metric_snapshot.csv"),
            "control_snapshot": rel_path(args.output_dir / "control_snapshot.csv"),
            "caveats": rel_path(args.output_dir / "caveats.csv"),
            "report": rel_path(args.output_dir / "report.md"),
        },
        "metric_snapshot": {
            "m4_macro_family_auroc": next(
                (row.get("macro_family_auroc") for row in metrics if row.get("scope") == "aggregate" and row.get("view_id") == "M4_TxG_compatibility"),
                None,
            ),
            "m4_weighted_family_auroc": next(
                (row.get("weighted_family_auroc") for row in metrics if row.get("scope") == "aggregate" and row.get("view_id") == "M4_TxG_compatibility"),
                None,
            ),
            "m4_overall_auroc": next(
                (row.get("overall_auroc") for row in metrics if row.get("scope") == "aggregate" and row.get("view_id") == "M4_TxG_compatibility"),
                None,
            ),
        },
        "boundary": {
            "official_validation_metric_produced": True,
            "official_validation_eval_only": True,
            "official_test_usage": False,
            "paper_metric_produced": False,
            "p_rel_claim_enabled": False,
            "p_obs_claim_enabled": False,
            "result_review_required": True,
            "support_contact_claim": "challenging_not_solved",
        },
        "caveat_count": len(caveat_rows),
    }

    write_json(args.output_dir / "summary.json", summary)
    write_csv(args.output_dir / "metric_snapshot.csv", metrics)
    write_csv(args.output_dir / "control_snapshot.csv", controls)
    write_csv(args.output_dir / "caveats.csv", caveat_rows)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    (args.output_dir / "report.md").write_text(
        report_text(
            status=status,
            validation_errors=validation_errors,
            output_dir=args.output_dir,
            metric_rows=metrics,
            controls=controls,
            caveat_rows=caveat_rows,
        ),
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
