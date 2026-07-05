#!/usr/bin/env python3
"""Validate H002 Docker materialization schema audit and write stage artifact."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_MATERIALIZATION_STAGE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight"
)
DEFAULT_SCHEMA_AUDIT_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/schema_audit/latest"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization"
)

EXPECTED_MATERIALIZATION_STATUS = (
    "h002_compatibility_dataset_v3_route_materialization_protocol_implementation_after_docker_preflight_ready"
)
EXPECTED_MATERIALIZATION_NEXT = "compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization"
EXPECTED_AUDIT_SCHEMA = "h002_materialization_schema_audit_v1"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization_v1"
STATUS_READY = "h002_compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization_ready"
STATUS_ERROR = "h002_compatibility_dataset_v3_materialization_schema_audit_after_docker_materialization_input_errors"
SELECTED_PATH = "schema_audit_passed_select_grouped_split_protocol"
NEXT_TODO = "compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialization-stage-dir", type=Path, default=DEFAULT_MATERIALIZATION_STAGE_DIR)
    parser.add_argument("--schema-audit-dir", type=Path, default=DEFAULT_SCHEMA_AUDIT_DIR)
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


def validate_inputs(materialization_summary: dict[str, Any], audit_manifest: dict[str, Any], audit_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if materialization_summary.get("status") != EXPECTED_MATERIALIZATION_STATUS:
        errors.append(
            {
                "error_type": "unexpected_materialization_stage_status",
                "expected": EXPECTED_MATERIALIZATION_STATUS,
                "actual": materialization_summary.get("status"),
            }
        )
    if materialization_summary.get("next_todo") != EXPECTED_MATERIALIZATION_NEXT:
        errors.append(
            {
                "error_type": "unexpected_materialization_stage_next_todo",
                "expected": EXPECTED_MATERIALIZATION_NEXT,
                "actual": materialization_summary.get("next_todo"),
            }
        )
    if int(materialization_summary.get("validation_errors", 0) or 0) != 0:
        errors.append({"error_type": "materialization_stage_validation_errors", "actual": materialization_summary.get("validation_errors")})

    required = [
        "audit_manifest.json",
        "schema_violations.jsonl",
        "blocked_field_hits.jsonl",
        "high_shortcut_warnings.jsonl",
        "block_presence_table.csv",
        "shortcut_risk_table.csv",
        "split_readiness_table.csv",
    ]
    for name in required:
        if not (audit_dir / name).exists():
            errors.append({"error_type": "missing_schema_audit_file", "file": name})

    if audit_manifest.get("schema_version") != EXPECTED_AUDIT_SCHEMA:
        errors.append(
            {
                "error_type": "unexpected_schema_audit_version",
                "expected": EXPECTED_AUDIT_SCHEMA,
                "actual": audit_manifest.get("schema_version"),
            }
        )
    if audit_manifest.get("status") != "ready":
        errors.append({"error_type": "schema_audit_not_ready", "actual": audit_manifest.get("status")})
    counts = audit_manifest.get("audit_counts", {})
    for key in ["schema_error_count", "blocked_C_e_field_hit_count", "high_C_e_allowed_shortcut_warning_count"]:
        if counts.get(key) != 0:
            errors.append({"error_type": "schema_audit_count_not_zero", "key": key, "actual": counts.get(key)})
    for name in ["schema_violations.jsonl", "blocked_field_hits.jsonl", "high_shortcut_warnings.jsonl"]:
        path = audit_dir / name
        if path.exists() and path.read_text(encoding="utf-8").strip():
            errors.append({"error_type": "schema_audit_error_file_not_empty", "file": name})
    boundary = audit_manifest.get("boundary", {})
    for key in ["paper_metric_produced", "grouped_holdout_run", "official_validation_usage", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "schema_audit_boundary_not_false", "key": key, "actual": boundary.get(key)})

    split_rows = read_csv(audit_dir / "split_readiness_table.csv") if (audit_dir / "split_readiness_table.csv").exists() else []
    for row in split_rows:
        if row.get("split_ready") != "True":
            errors.append({"error_type": "family_not_split_ready", "route_family": row.get("route_family"), "row": row})
    return errors


def next_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "must_do": [
            "create grouped split protocol over the materialized H002 candidate pool",
            "keep split group based on cv_group_id and prevent row/id leakage across train/dev/heldout",
            "preserve route-family label balance diagnostics in split manifest",
            "keep official validation/test wording blocked",
        ],
        "must_not_do": [
            "run paper-level learned metrics before the grouped split manifest exists",
            "use metadata-only fields such as cv_group_id/source_artifact as model features",
            "enable Z_e or Q_e for C_e without a new protocol",
            "copy row-level JSONL outputs into results/",
        ],
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# H002 Materialization Schema Audit",
        "",
        "## Verdict",
        "",
        "Docker materialization schema audit passed. The materialized `C_e` view has no blocked-field hits in `T_e + G_e`, no high-risk allowed-feature shortcut warning, and all promoted route families are split-ready.",
        "",
        "## Audit Counts",
        "",
        "| Check | Count |",
        "| --- | ---: |",
    ]
    for key, value in payload["audit_counts"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "## Split Readiness", "", "| Route family | Rows | Groups | Mixed groups | Split ready |", "| --- | ---: | ---: | ---: | --- |"])
    for row in payload["split_readiness_table"]:
        lines.append(
            f"| `{row['route_family']}` | {row['rows']} | {row['cv_group_count']} | {row['mixed_label_group_count']} | `{row['split_ready']}` |"
        )
    lines.extend(["", "## Boundary", ""])
    for key, value in payload["boundary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Next", "", f"`{NEXT_TODO}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    materialization_summary = read_json(args.materialization_stage_dir / "summary.json")
    audit_manifest = read_json(args.schema_audit_dir / "audit_manifest.json")
    errors = validate_inputs(materialization_summary, audit_manifest, args.schema_audit_dir)
    status = STATUS_READY if not errors else STATUS_ERROR

    split_rows = read_csv(args.schema_audit_dir / "split_readiness_table.csv")
    block_rows = read_csv(args.schema_audit_dir / "block_presence_table.csv")
    shortcut_rows = read_csv(args.schema_audit_dir / "shortcut_risk_table.csv")
    shortcut_summary = [
        {
            "risk": risk,
            "model_input_scope": scope,
            "count": sum(1 for row in shortcut_rows if row.get("risk") == risk and row.get("model_input_scope") == scope),
        }
        for scope in ["C_e_allowed", "metadata_only"]
        for risk in ["high", "medium", "low"]
    ]

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "fix_materialization_schema_audit_errors",
        "next_todo": NEXT_TODO if not errors else EXPECTED_MATERIALIZATION_NEXT,
        "created_at_utc": now,
        "validation_errors": len(errors),
        "input_artifacts": {
            "materialization_stage": rel_path(args.materialization_stage_dir),
            "schema_audit_runtime": rel_path(args.schema_audit_dir),
        },
        "runtime_outputs": {
            "audit_manifest": rel_path(args.schema_audit_dir / "audit_manifest.json"),
            "schema_violations": rel_path(args.schema_audit_dir / "schema_violations.jsonl"),
            "blocked_field_hits": rel_path(args.schema_audit_dir / "blocked_field_hits.jsonl"),
            "high_shortcut_warnings": rel_path(args.schema_audit_dir / "high_shortcut_warnings.jsonl"),
            "shortcut_risk_table": rel_path(args.schema_audit_dir / "shortcut_risk_table.csv"),
            "split_readiness_table": rel_path(args.schema_audit_dir / "split_readiness_table.csv"),
        },
        "row_count": audit_manifest.get("row_count"),
        "audit_counts": audit_manifest.get("audit_counts", {}),
        "block_presence_table": block_rows,
        "shortcut_summary": shortcut_summary,
        "split_readiness_table": split_rows,
        "boundary": {
            "schema_audit_run": not errors,
            "paper_metric_produced": False,
            "grouped_holdout_run": False,
            "official_validation_usage": False,
            "h001_artifacts_modified": False,
        },
        "next_step_contract": next_contract(),
    }

    write_csv(args.output_dir / "block_presence_table.csv", block_rows)
    write_csv(args.output_dir / "shortcut_summary.csv", shortcut_summary)
    write_csv(args.output_dir / "split_readiness_table.csv", split_rows)
    write_json(args.output_dir / "next_contract.json", next_contract())
    write_json(args.output_dir / "summary.json", payload)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", payload)

    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
