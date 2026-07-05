#!/usr/bin/env python3
"""Validate grouped-eval feature extractor repair after relative-vertical failure analysis."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_FAILURE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review"
DEFAULT_RUNNER_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_grouped_eval_runner_after_protocol"
DEFAULT_REVIEW_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_grouped_eval_result_review_after_runner"
DEFAULT_SPLIT_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/splits/latest"
DEFAULT_RUNNER_SCRIPT = REPO_ROOT / "experiments/H002_compatibility_routing/scripts/run_grouped_eval.py"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis"

EXPECTED_FAILURE_STATUS = "h002_compatibility_dataset_v3_relative_vertical_failure_analysis_after_grouped_review_ready"
EXPECTED_FAILURE_NEXT = "compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis"
EXPECTED_RUNNER_STATUS = "h002_compatibility_dataset_v3_grouped_eval_runner_after_protocol_ready"
EXPECTED_REVIEW_STATUS = "h002_compatibility_dataset_v3_grouped_eval_result_review_after_runner_ready"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis_v1"
STATUS_READY = "h002_compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_grouped_eval_feature_extractor_repair_after_relative_vertical_failure_analysis_input_errors"
SELECTED_PATH = "feature_extractor_repair_ready_select_claim_boundary_review"
NEXT_TODO = "compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--failure-dir", type=Path, default=DEFAULT_FAILURE_DIR)
    parser.add_argument("--runner-dir", type=Path, default=DEFAULT_RUNNER_DIR)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--split-dir", type=Path, default=DEFAULT_SPLIT_DIR)
    parser.add_argument("--runner-script", type=Path, default=DEFAULT_RUNNER_SCRIPT)
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
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
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
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_runner_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("h002_grouped_eval_runner", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import runner script: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def first_relative_vertical_row(split_dir: Path) -> dict[str, Any] | None:
    path = split_dir / "model_safe_split_view.jsonl"
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("route_family") == "relative_vertical":
                return row
    return None


def family_decision(review_summary: dict[str, Any], family: str) -> dict[str, Any] | None:
    for item in review_summary.get("family_decisions", []):
        if item.get("route_family") == family:
            return item
    return None


def validate(
    *,
    failure_summary: dict[str, Any],
    runner_summary: dict[str, Any],
    review_summary: dict[str, Any],
    failure_errors: list[dict[str, Any]],
    runner_errors: list[dict[str, Any]],
    review_errors: list[dict[str, Any]],
    runner_script: Path,
    split_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if failure_summary.get("status") != EXPECTED_FAILURE_STATUS:
        errors.append({"error_type": "unexpected_failure_status", "actual": failure_summary.get("status")})
    if failure_summary.get("next_todo") != EXPECTED_FAILURE_NEXT:
        errors.append({"error_type": "unexpected_failure_next_todo", "actual": failure_summary.get("next_todo")})
    if runner_summary.get("status") != EXPECTED_RUNNER_STATUS:
        errors.append({"error_type": "unexpected_runner_status", "actual": runner_summary.get("status")})
    if review_summary.get("status") != EXPECTED_REVIEW_STATUS:
        errors.append({"error_type": "unexpected_review_status", "actual": review_summary.get("status")})
    for name, rows in [("failure", failure_errors), ("runner", runner_errors), ("review", review_errors)]:
        if rows:
            errors.append({"error_type": f"{name}_validation_errors_present", "rows": len(rows)})

    script_text = runner_script.read_text(encoding="utf-8")
    if "GEOMETRY_FEATURE_PATHS" not in script_text:
        errors.append({"error_type": "missing_explicit_geometry_feature_path_map"})
    if "raw_geometry_feature_vector" not in script_text:
        errors.append({"error_type": "missing_raw_geometry_feature_vector_path"})

    repair_probe: dict[str, Any] = {}
    row = first_relative_vertical_row(split_dir)
    if row is None:
        errors.append({"error_type": "missing_relative_vertical_probe_row"})
    else:
        module = load_runner_module(runner_script)
        raw_value = row["feature_blocks"]["G_e"]["G_e_raw"]["raw_geometry_feature_vector"]["center_delta_z"]
        repaired_value = module.numeric_value(row, "center_delta_z")
        sign_feature = module.compatibility_features(row).get("C.sign_x_center_delta_z")
        repair_probe = {
            "unified_row_id": row.get("unified_row_id"),
            "predicate_label": row.get("predicate_label"),
            "raw_center_delta_z": raw_value,
            "repaired_numeric_center_delta_z": repaired_value,
            "repaired_sign_feature": sign_feature,
            "matches_raw_center_delta_z": repaired_value == raw_value,
        }
        if repaired_value != raw_value:
            errors.append(
                {
                    "error_type": "repaired_numeric_value_does_not_match_raw_center_delta_z",
                    "raw": raw_value,
                    "actual": repaired_value,
                }
            )

    rv = family_decision(review_summary, "relative_vertical") or {}
    support = family_decision(review_summary, "support_contact") or {}
    overall = review_summary.get("overall", {}).get("metrics", {}).get("M4_TxG_compatibility", {})
    if rv.get("status") != "claim_supporting":
        errors.append({"error_type": "relative_vertical_not_claim_supporting_after_repair", "decision": rv})
    if float(rv.get("heldout_M4_auroc", 0.0)) < 0.95:
        errors.append({"error_type": "relative_vertical_repaired_auroc_too_low", "decision": rv})
    if float(overall.get("auroc", 0.0)) < 0.95:
        errors.append({"error_type": "overall_repaired_auroc_too_low", "overall": overall})
    if support.get("status") != "partial":
        errors.append({"error_type": "support_contact_expected_partial_boundary_changed", "decision": support})

    return errors, repair_probe


def write_report(path: Path, *, summary: dict[str, Any], family_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# H002 Grouped-Eval Feature Extractor Repair",
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
        "## Repair",
        "",
        "The grouped evaluator now reads relation-specific geometry through explicit raw feature paths instead of suffix-matching flattened `G_e` keys.",
        "",
        "The repaired probe confirms that `center_delta_z` reads `raw_geometry_feature_vector.center_delta_z` rather than `raw_geometry_feature_available_mask.center_delta_z`.",
        "",
        "## Repaired Internal Heldout",
        "",
        "| Family | Status | Heldout M4 AUROC | Balanced acc | Delta vs M1 | Delta vs M2 | Delta vs M3 | Delta vs wrong-T | Delta vs shuffled-G |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in family_rows:
        lines.append(
            "| {route_family} | {status} | {heldout_M4_auroc:.6f} | {heldout_M4_balanced_accuracy:.6f} | {delta_vs_M1:.6f} | {delta_vs_M2:.6f} | {delta_vs_M3:.6f} | {delta_vs_wrong_T:.6f} | {delta_vs_shuffled_G:.6f} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `relative_vertical` is restored as claim-supporting evidence after the feature extractor repair.",
            "- `relative_horizontal`, `relative_vertical`, and `size_relative` are now claim-supporting internal compatibility-route evidence.",
            "- `support_contact` remains partial/challenging and should not be presented as solved.",
            "- This is still internal H002 candidate-pool evidence, not official validation/test or paper-level evidence.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    failure_summary = read_json(args.failure_dir / "summary.json")
    runner_summary = read_json(args.runner_dir / "summary.json")
    review_summary = read_json(args.review_dir / "summary.json")
    failure_errors = read_jsonl(args.failure_dir / "validation_errors.jsonl")
    runner_errors = read_jsonl(args.runner_dir / "validation_errors.jsonl")
    review_errors = read_jsonl(args.review_dir / "validation_errors.jsonl")

    validation_errors, repair_probe = validate(
        failure_summary=failure_summary,
        runner_summary=runner_summary,
        review_summary=review_summary,
        failure_errors=failure_errors,
        runner_errors=runner_errors,
        review_errors=review_errors,
        runner_script=args.runner_script,
        split_dir=args.split_dir,
    )
    family_rows = review_summary.get("family_decisions", [])
    status = STATUS_ERRORS if validation_errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": SELECTED_PATH if not validation_errors else "fix_feature_extractor_repair_inputs",
        "next_todo": NEXT_TODO if not validation_errors else "fix_grouped_eval_feature_extractor_repair_inputs",
        "validation_errors": len(validation_errors),
        "input_artifacts": {
            "failure_analysis": rel_path(args.failure_dir / "summary.json"),
            "runner_summary": rel_path(args.runner_dir / "summary.json"),
            "review_summary": rel_path(args.review_dir / "summary.json"),
            "runner_script": rel_path(args.runner_script),
        },
        "boundary": {
            "official_validation_usage": False,
            "official_test_usage": False,
            "paper_metric_produced": False,
            "p_obs_claim_enabled": False,
            "p_rel_claim_enabled": False,
            "h001_artifacts_modified": False,
        },
        "repair_probe": repair_probe,
        "repaired_review": {
            "overall_M4_heldout_auroc": review_summary.get("overall", {}).get("metrics", {}).get("M4_TxG_compatibility", {}).get("auroc"),
            "family_decisions": family_rows,
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "next_contract.json", {"next_todo": summary["next_todo"], "selected_path": summary["selected_path"]})
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "family_decisions_after_repair.csv", family_rows)
    write_json(args.output_dir / "repair_probe.json", repair_probe)
    write_report(args.output_dir / "report.md", summary=summary, family_rows=family_rows)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
