#!/usr/bin/env python3
"""Validate H002 grouped evaluation runner outputs and write stage artifact."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PROTOCOL_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split"
DEFAULT_EVAL_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/evaluation/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_grouped_eval_runner_after_protocol"

EXPECTED_PROTOCOL_STATUS = "h002_compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split_ready"
EXPECTED_PROTOCOL_NEXT = "compatibility_dataset_v3_grouped_eval_runner_after_protocol"
EXPECTED_EVAL_SCHEMA = "h002_grouped_eval_runner_v1"
EXPECTED_VIEWS = {
    "M0_constant",
    "M1_T_semantic_only",
    "M2_G_geometry_only",
    "M3_T_plus_G_concat",
    "M4_TxG_compatibility",
    "C1_wrong_T_control",
    "C2_shuffled_G_control",
    "D1_Z_source_confidence_diagnostic",
    "D2_Q_observability_diagnostic",
}
EXPECTED_ROUTE_FAMILIES = {"relative_horizontal", "relative_vertical", "size_relative", "support_contact"}

SCHEMA_VERSION = "h002_compatibility_dataset_v3_grouped_eval_runner_after_protocol_v1"
STATUS_READY = "h002_compatibility_dataset_v3_grouped_eval_runner_after_protocol_ready"
STATUS_ERROR = "h002_compatibility_dataset_v3_grouped_eval_runner_after_protocol_input_errors"
SELECTED_PATH = "grouped_eval_runner_ready_select_result_review"
NEXT_TODO = "compatibility_dataset_v3_grouped_eval_result_review_after_runner"


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
    with path.open(newline="", encoding="utf-8") as handle:
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
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def as_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def metric_lookup(rows: list[dict[str, str]], level: str, split: str, view: str, family: str = "ALL") -> dict[str, str] | None:
    for row in rows:
        if row.get("level") == level and row.get("protocol_split") == split and row.get("view_id") == view and row.get("route_family") == family:
            return row
    return None


def summarize_metrics(route_rows: list[dict[str, str]], control_rows: list[dict[str, str]]) -> dict[str, Any]:
    summary: dict[str, Any] = {"overall": {}, "family_M4": {}, "overall_controls": {}}
    for split in ["internal_dev", "internal_heldout"]:
        summary["overall"][split] = {}
        for view in sorted(EXPECTED_VIEWS):
            row = metric_lookup(route_rows, "overall", split, view)
            if row:
                summary["overall"][split][view] = {
                    "auroc": as_float(row.get("auroc")),
                    "balanced_accuracy": as_float(row.get("balanced_accuracy")),
                    "macro_F1": as_float(row.get("macro_F1")),
                    "rows": int(float(row.get("rows", "0"))),
                }
        summary["family_M4"][split] = {}
        for family in sorted(EXPECTED_ROUTE_FAMILIES):
            row = metric_lookup(route_rows, "route_family", split, "M4_TxG_compatibility", family)
            if row:
                summary["family_M4"][split][family] = {
                    "auroc": as_float(row.get("auroc")),
                    "balanced_accuracy": as_float(row.get("balanced_accuracy")),
                    "macro_F1": as_float(row.get("macro_F1")),
                    "rows": int(float(row.get("rows", "0"))),
                }
        summary["overall_controls"][split] = {}
        for row in control_rows:
            if row.get("level") == "overall" and row.get("protocol_split") == split:
                summary["overall_controls"][split][row["comparison"]] = {
                    "delta_auroc": as_float(row.get("delta_auroc")),
                    "primary_auroc": as_float(row.get("primary_auroc")),
                    "baseline_auroc": as_float(row.get("baseline_auroc")),
                }
    return summary


def validate(protocol: dict[str, Any], manifest: dict[str, Any], eval_dir: Path, route_rows: list[dict[str, str]], controls: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if protocol.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error_type": "unexpected_protocol_status", "actual": protocol.get("status")})
    if protocol.get("next_todo") != EXPECTED_PROTOCOL_NEXT:
        errors.append({"error_type": "unexpected_protocol_next_todo", "actual": protocol.get("next_todo")})
    required_files = [
        "eval_manifest.json",
        "model_view_manifest.json",
        "route_metrics.csv",
        "predicate_metrics.csv",
        "control_metrics.csv",
        "prediction_scores.jsonl",
        "leakage_audit.csv",
        "validation_errors.jsonl",
    ]
    for name in required_files:
        if not (eval_dir / name).exists():
            errors.append({"error_type": "missing_eval_file", "file": name})
    if errors:
        return errors
    if manifest.get("schema_version") != EXPECTED_EVAL_SCHEMA:
        errors.append({"error_type": "unexpected_eval_schema", "actual": manifest.get("schema_version")})
    if manifest.get("status") != "ready":
        errors.append({"error_type": "eval_manifest_not_ready", "actual": manifest.get("status")})
    if int(manifest.get("validation_errors", 0) or 0) != 0:
        errors.append({"error_type": "eval_manifest_validation_errors", "actual": manifest.get("validation_errors")})
    if (eval_dir / "validation_errors.jsonl").read_text(encoding="utf-8").strip():
        errors.append({"error_type": "eval_validation_errors_nonempty"})
    boundary = manifest.get("boundary", {})
    if boundary.get("grouped_metric_run") is not True:
        errors.append({"error_type": "grouped_metric_run_not_true"})
    for key in ["official_validation_usage", "official_test_usage", "paper_metric_produced", "p_obs_claim_enabled", "p_rel_claim_enabled", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "unexpected_boundary_value", "key": key, "actual": boundary.get(key)})
    if set(manifest.get("model_views", [])) != EXPECTED_VIEWS:
        errors.append({"error_type": "unexpected_model_views", "actual": manifest.get("model_views")})
    row_counts = manifest.get("row_counts", {})
    if row_counts.get("total") != 6952 or row_counts.get("prediction_rows") != 2084:
        errors.append({"error_type": "unexpected_row_counts", "row_counts": row_counts})
    leakage = read_csv(eval_dir / "leakage_audit.csv")
    for row in leakage:
        if row.get("status") != "pass" or row.get("violations") not in {"0", 0}:
            errors.append({"error_type": "leakage_audit_failed", "row": row})
    for split in ["internal_dev", "internal_heldout"]:
        for view in EXPECTED_VIEWS:
            if metric_lookup(route_rows, "overall", split, view) is None:
                errors.append({"error_type": "missing_overall_metric", "split": split, "view": view})
        for family in EXPECTED_ROUTE_FAMILIES:
            if metric_lookup(route_rows, "route_family", split, "M4_TxG_compatibility", family) is None:
                errors.append({"error_type": "missing_family_M4_metric", "split": split, "family": family})
    if not controls:
        errors.append({"error_type": "empty_control_metrics"})
    return errors


def next_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "must_do": [
            "review grouped internal-dev/internal-heldout metrics before claim promotion",
            "separate aggregate success from route-family-specific claim boundaries",
            "verify that feature-extraction repairs preserve wrong-T and shuffled-G controls",
            "treat support_contact as challenging/partial unless result review justifies otherwise",
            "keep this as internal candidate-pool evidence, not official validation/test evidence",
        ],
        "must_not_do": [
            "promote aggregate AUROC as a paper result without family-level review",
            "claim p_obs or p_rel calibration from this C_e-only evaluation",
            "hide that wrong-T/shuffled-G controls are counterfactual eval controls",
            "call this official validation/test",
        ],
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    overall = payload["metric_summary"]["overall"]["internal_heldout"]
    family = payload["metric_summary"]["family_M4"]["internal_heldout"]
    controls = payload["metric_summary"]["overall_controls"]["internal_heldout"]
    lines = [
        "# H002 Grouped Evaluation Runner",
        "",
        "## Verdict",
        "",
        "Grouped evaluation runner completed on the internal H002 candidate-pool split. This is not official validation/test and not a paper-level result.",
        "",
        "## Heldout Overall",
        "",
        "| View | AUROC | Balanced acc | Macro-F1 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for view, metrics in overall.items():
        lines.append(f"| `{view}` | {metrics['auroc']:.6f} | {metrics['balanced_accuracy']:.6f} | {metrics['macro_F1']:.6f} |")
    lines.extend(["", "## Heldout M4 By Family", "", "| Family | Rows | AUROC | Balanced acc | Macro-F1 |", "| --- | ---: | ---: | ---: | ---: |"])
    for fam, metrics in family.items():
        lines.append(f"| `{fam}` | {metrics['rows']} | {metrics['auroc']:.6f} | {metrics['balanced_accuracy']:.6f} | {metrics['macro_F1']:.6f} |")
    lines.extend(["", "## Heldout Controls", "", "| Comparison | Delta AUROC | Primary | Baseline |", "| --- | ---: | ---: | ---: |"])
    for comp, metrics in controls.items():
        lines.append(f"| `{comp}` | {metrics['delta_auroc']:.6f} | {metrics['primary_auroc']:.6f} | {metrics['baseline_auroc']:.6f} |")
    lines.extend(["", "## Next", "", f"`{NEXT_TODO}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    protocol = read_json(args.protocol_dir / "summary.json")
    manifest = read_json(args.eval_dir / "eval_manifest.json")
    route_rows = read_csv(args.eval_dir / "route_metrics.csv")
    predicate_rows = read_csv(args.eval_dir / "predicate_metrics.csv")
    control_rows = read_csv(args.eval_dir / "control_metrics.csv")
    errors = validate(protocol, manifest, args.eval_dir, route_rows, control_rows)
    status = STATUS_READY if not errors else STATUS_ERROR
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "fix_grouped_eval_runner_outputs",
        "next_todo": NEXT_TODO if not errors else EXPECTED_PROTOCOL_NEXT,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "validation_errors": len(errors),
        "input_artifacts": {
            "protocol": rel_path(args.protocol_dir),
            "evaluation_runtime": rel_path(args.eval_dir),
        },
        "row_counts": manifest.get("row_counts", {}),
        "metric_summary": summarize_metrics(route_rows, control_rows),
        "boundary": {
            "grouped_metric_run": not errors,
            "official_validation_usage": False,
            "official_test_usage": False,
            "paper_metric_produced": False,
            "p_obs_claim_enabled": False,
            "p_rel_claim_enabled": False,
            "h001_artifacts_modified": False,
        },
        "next_step_contract": next_contract(),
    }
    write_json(args.output_dir / "summary.json", payload)
    write_json(args.output_dir / "next_contract.json", next_contract())
    write_csv(args.output_dir / "route_metrics.csv", route_rows)
    write_csv(args.output_dir / "predicate_metrics.csv", predicate_rows)
    write_csv(args.output_dir / "control_metrics.csv", control_rows)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
