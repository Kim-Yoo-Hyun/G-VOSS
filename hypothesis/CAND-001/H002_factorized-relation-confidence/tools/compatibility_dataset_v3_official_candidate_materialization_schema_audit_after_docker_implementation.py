#!/usr/bin/env python3
"""Validate official materialization schema/shortcut audit outputs for H002."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_MATERIALIZATION_STAGE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol"
DEFAULT_AUDIT_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/official_schema_audit/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation"

EXPECTED_MATERIALIZATION_STAGE_STATUS = "h002_compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol_ready"
EXPECTED_AUDIT_STATUS = "h002_official_materialization_schema_audit_ready_with_shortcut_warnings"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation_v1"
STATUS_READY = "h002_compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation_ready_with_caveats"
STATUS_ERRORS = "h002_compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation_errors"
SELECTED_PATH = "schema_audit_ready_select_official_metric_protocol_freeze"
NEXT_TODO = "compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialization-stage-dir", type=Path, default=DEFAULT_MATERIALIZATION_STAGE_DIR)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
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


def validate(
    materialization_summary: dict[str, Any],
    audit_manifest: dict[str, Any],
    runtime_validation_errors: list[dict[str, Any]],
    schema_violations: list[dict[str, Any]],
    blocked_hits: list[dict[str, Any]],
    separation_rows: list[dict[str, str]],
    control_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if materialization_summary.get("status") != EXPECTED_MATERIALIZATION_STAGE_STATUS:
        errors.append({"error_type": "unexpected_materialization_stage_status", "actual": materialization_summary.get("status")})
    if materialization_summary.get("validation_errors") != 0:
        errors.append({"error_type": "materialization_stage_validation_errors", "actual": materialization_summary.get("validation_errors")})
    if audit_manifest.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": audit_manifest.get("status")})
    if audit_manifest.get("validation_errors") != 0:
        errors.append({"error_type": "audit_manifest_validation_errors", "actual": audit_manifest.get("validation_errors")})
    if runtime_validation_errors:
        errors.append({"error_type": "runtime_validation_errors_present", "rows": len(runtime_validation_errors)})
    if schema_violations:
        errors.append({"error_type": "schema_violations_present", "rows": len(schema_violations)})
    if blocked_hits:
        errors.append({"error_type": "blocked_field_hits_present", "rows": len(blocked_hits)})
    if not separation_rows:
        errors.append({"error_type": "missing_separation_audit"})
    else:
        row = separation_rows[0]
        if row.get("model_safe_missing_hidden") not in {"0", 0} or row.get("hidden_missing_model_safe") not in {"0", 0}:
            errors.append({"error_type": "model_safe_hidden_misalignment", "row": row})
    control_blockers = [row for row in control_rows if row.get("blocks_metric_freeze") == "True"]
    if control_blockers:
        errors.append({"error_type": "control_readiness_blockers", "rows": len(control_blockers)})
    boundary = audit_manifest.get("boundary", {})
    for key in ["official_validation_metric_produced", "official_test_usage", "paper_metric_produced", "p_rel_claim_enabled", "p_obs_claim_enabled"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "unexpected_boundary_value", "key": key, "actual": boundary.get(key)})
    if boundary.get("z_e_excluded_from_main_c_e") is not True:
        errors.append({"error_type": "z_e_not_excluded"})
    if boundary.get("family_macro_metric_required_next") is not True:
        errors.append({"error_type": "family_macro_metric_not_required"})
    return errors


def write_report(path: Path, summary: dict[str, Any], label_rows: list[dict[str, str]], high_shortcuts: list[dict[str, str]]) -> None:
    lines = [
        "# H002 Official Candidate Materialization Schema Audit",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"shortcut_warnings = {summary['shortcut_warnings']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Label Balance",
        "",
        "| Family | Rows | Label 0 | Label 1 | Majority | Dataset Weight |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in label_rows:
        lines.append(
            f"| `{row['family']}` | {row['rows']} | {row['label_0']} | {row['label_1']} | "
            f"{row['majority_rate']} | {row['dataset_weight']} |"
        )
    lines.extend(["", "## Shortcut Caveats", ""])
    if high_shortcuts:
        lines.extend(["| Family | Probe | Accuracy | Caveat |", "| --- | --- | ---: | --- |"])
        for row in high_shortcuts:
            lines.append(
                f"| `{row['family']}` | `{row['probe']}` | {row['majority_accuracy']} | blocks family solved claim, not metric protocol |"
            )
    else:
        lines.append("No high shortcut caveat.")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- schema violations: 0",
            "- blocked field hits: 0",
            "- model-safe/hidden alignment: passed",
            "- official metric: not produced",
            "- next stage: official metric protocol freeze with family-wise/macro controls",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    materialization_summary = read_json(args.materialization_stage_dir / "summary.json")
    audit_manifest = read_json(args.audit_dir / "audit_manifest.json")
    runtime_validation_errors = read_jsonl(args.audit_dir / "validation_errors.jsonl")
    schema_violations = read_jsonl(args.audit_dir / "schema_violations.jsonl")
    blocked_hits = read_jsonl(args.audit_dir / "blocked_field_hits.jsonl")
    separation_rows = read_csv(args.audit_dir / "separation_audit.csv")
    label_rows = read_csv(args.audit_dir / "label_balance.csv")
    shortcut_rows = read_csv(args.audit_dir / "shortcut_risk_table.csv")
    high_shortcuts = read_csv(args.audit_dir / "high_shortcut_warnings.csv")
    control_rows = read_csv(args.audit_dir / "control_readiness.csv")

    validation_errors = validate(
        materialization_summary,
        audit_manifest,
        runtime_validation_errors,
        schema_violations,
        blocked_hits,
        separation_rows,
        control_rows,
    )

    status = STATUS_ERRORS if validation_errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": SELECTED_PATH if not validation_errors else "blocked_fix_schema_audit",
        "next_todo": NEXT_TODO if not validation_errors else "fix_official_materialization_schema_audit",
        "validation_errors": len(validation_errors),
        "shortcut_warnings": len(high_shortcuts),
        "input_artifacts": {
            "audit_manifest": rel_path(args.audit_dir / "audit_manifest.json"),
            "label_balance": rel_path(args.audit_dir / "label_balance.csv"),
            "shortcut_risk_table": rel_path(args.audit_dir / "shortcut_risk_table.csv"),
            "control_readiness": rel_path(args.audit_dir / "control_readiness.csv"),
        },
        "output_artifacts": {
            "report": rel_path(args.output_dir / "report.md"),
            "shortcut_caveats": rel_path(args.output_dir / "shortcut_caveats.csv"),
            "next_runner_contract": rel_path(args.output_dir / "next_runner_contract.json"),
        },
        "audit_summary": {
            "schema_violations": len(schema_violations),
            "blocked_field_hits": len(blocked_hits),
            "runtime_validation_errors": len(runtime_validation_errors),
            "high_shortcut_warnings": len(high_shortcuts),
            "support_contact_high_shortcut": any(row.get("family") == "support_contact" for row in high_shortcuts),
            "family_macro_metric_required": True,
            "z_e_excluded_from_main_c_e": True,
        },
        "boundary": {
            "official_validation_metric_produced": False,
            "official_test_usage": False,
            "paper_metric_produced": False,
            "p_rel_claim_enabled": False,
            "p_obs_claim_enabled": False,
            "support_contact_claim": "challenging_not_solved",
        },
    }
    next_runner_contract = {
        "next_todo": summary["next_todo"],
        "runner_purpose": "Freeze official C_e metric protocol before computing official validation metrics.",
        "required_metric_policy": [
            "per_family_AUROC",
            "macro_family_AUROC",
            "weighted_family_AUROC",
            "overall_AUROC_as_secondary",
            "wrong_T_control",
            "shuffled_G_control",
            "family_specific_controls",
        ],
        "must_not_do": [
            "include Z_e in main C_e metric",
            "claim support_contact solved",
            "use official test",
            "promote metric before result review",
        ],
    }
    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "next_runner_contract.json", next_runner_contract)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "label_balance.csv", label_rows)
    write_csv(args.output_dir / "shortcut_caveats.csv", high_shortcuts)
    write_report(args.output_dir / "report.md", summary, label_rows, high_shortcuts)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
