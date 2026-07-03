#!/usr/bin/env python3
"""Validate source-reranking materialization schema-audit runtime outputs."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_DOCKER_MATERIALIZATION_ARTIFACT = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_docker_materialization_after_protocol"
)
DEFAULT_AUDIT_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/source_reranking_schema_audit/latest"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_materialization_schema_audit_after_docker_materialization"
)

EXPECTED_PREV_STATUS = "h002_source_reranking_docker_materialization_after_protocol_ready"
EXPECTED_PREV_NEXT = "compatibility_dataset_v3_source_reranking_materialization_schema_audit_after_docker_materialization"
EXPECTED_AUDIT_STATUS = "h002_source_reranking_materialization_schema_audit_ready"
EXPECTED_AUDIT_SCHEMA = "h002_source_reranking_materialization_schema_audit_v1"
EXPECTED_AUDIT_NEXT = "compatibility_dataset_v3_source_reranking_metric_protocol_freeze_after_schema_audit"
EXPECTED_ROWS = 762888

SCHEMA_VERSION = "h002_source_reranking_materialization_schema_audit_after_docker_materialization_v1"
STATUS_READY = "h002_source_reranking_materialization_schema_audit_after_docker_materialization_ready"
STATUS_ERRORS = "h002_source_reranking_materialization_schema_audit_after_docker_materialization_errors"
SELECTED_PATH = "source_reranking_schema_audit_passed_select_metric_protocol_freeze"
NEXT_TODO = "compatibility_dataset_v3_source_reranking_metric_protocol_freeze_after_schema_audit"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docker-materialization-artifact", type=Path, default=DEFAULT_DOCKER_MATERIALIZATION_ARTIFACT)
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


def validate_prev(prev_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    prev = read_json(prev_dir / "summary.json")
    if prev.get("status") != EXPECTED_PREV_STATUS:
        errors.append({"error_type": "unexpected_previous_status", "actual": prev.get("status")})
    if prev.get("next_todo") != EXPECTED_PREV_NEXT:
        errors.append({"error_type": "unexpected_previous_next_todo", "actual": prev.get("next_todo")})
    if prev.get("validation_errors") != 0:
        errors.append({"error_type": "previous_validation_errors", "actual": prev.get("validation_errors")})
    return errors


def validate_audit(audit_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []
    manifest = read_json(audit_dir / "audit_manifest.json")
    if manifest.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": manifest.get("status")})
    if manifest.get("schema_version") != EXPECTED_AUDIT_SCHEMA:
        errors.append({"error_type": "unexpected_audit_schema", "actual": manifest.get("schema_version")})
    if manifest.get("next_todo") != EXPECTED_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_audit_next_todo", "actual": manifest.get("next_todo")})
    if manifest.get("validation_errors") != 0 or line_count(audit_dir / "validation_errors.jsonl") != 0:
        errors.append(
            {
                "error_type": "audit_validation_errors",
                "summary_errors": manifest.get("validation_errors"),
                "file_errors": line_count(audit_dir / "validation_errors.jsonl"),
            }
        )
    if line_count(audit_dir / "blocked_field_hits.jsonl") != 0:
        errors.append({"error_type": "blocked_field_hits_present", "count": line_count(audit_dir / "blocked_field_hits.jsonl")})
    decision = manifest.get("decision", {})
    if decision.get("ready_for_metric_protocol_freeze") is not True:
        errors.append({"error_type": "not_ready_for_metric_protocol_freeze", "actual": decision.get("ready_for_metric_protocol_freeze")})
    if decision.get("metric_run_allowed_now") is not False:
        errors.append({"error_type": "metric_run_allowed_too_early", "actual": decision.get("metric_run_allowed_now")})
    if decision.get("source_reranking_metrics_run") is not False:
        errors.append({"error_type": "source_reranking_metrics_were_run", "actual": decision.get("source_reranking_metrics_run")})
    if decision.get("official_test_usage") is not False:
        errors.append({"error_type": "official_test_used", "actual": decision.get("official_test_usage")})
    row_counts = manifest.get("row_counts", {})
    if row_counts.get("unique_candidate_ids") != EXPECTED_ROWS:
        errors.append({"error_type": "unique_candidate_id_count_mismatch", "actual": row_counts.get("unique_candidate_ids")})

    for row in read_csv(audit_dir / "schema_separation_audit.csv"):
        gate_rows.append({"gate": row.get("check"), "status": row.get("status"), "source": "schema_separation_audit"})
        if row.get("status") != "pass":
            errors.append({"error_type": "schema_separation_gate_failed", "gate": row.get("check"), "status": row.get("status")})
    family_rows = read_csv(audit_dir / "family_success_aggregation.csv")
    primary_macro = [row for row in family_rows if row.get("family") == "PRIMARY_MACRO"]
    if not primary_macro or primary_macro[0].get("balanced_primary_family_rows") != "True":
        errors.append({"error_type": "primary_macro_not_balanced", "row": primary_macro[0] if primary_macro else None})
    for row in family_rows:
        if row.get("family") == "support_contact" and row.get("include_in_success_aggregation") != "False":
            errors.append({"error_type": "support_contact_not_excluded", "row": row})
    for row in read_csv(audit_dir / "control_readiness.csv"):
        if row.get("success_metric_role") == "primary":
            if row.get("wrong_T_control_ready") != "True" or row.get("shuffled_G_control_ready") != "True":
                errors.append({"error_type": "primary_control_not_ready", "row": row})
    for row in read_csv(audit_dir / "metric_freeze_precondition.csv"):
        gate_rows.append({"gate": row.get("gate"), "status": row.get("status"), "source": "metric_freeze_precondition"})
        if row.get("gate") == "source_reranking_materialization_schema_audit" and row.get("status") != "pass":
            errors.append({"error_type": "metric_freeze_precondition_failed", "row": row})
    return errors, gate_rows


def make_report(summary: dict[str, Any]) -> str:
    return f"""# Source Reranking Materialization Schema Audit After Docker Materialization

## Status

```text
status = {summary["status"]}
selected_path = {summary["selected_path"]}
validation_errors = {summary["validation_errors"]}
next_todo = {summary["next_todo"]}
```

## Result

The Docker schema audit passed and source reranking can move to metric protocol freeze.
No source reranking metric or official test was run.
"""


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    errors = validate_prev(args.docker_materialization_artifact)
    audit_errors, gate_rows = validate_audit(args.audit_dir)
    errors.extend(audit_errors)
    status = STATUS_READY if not errors else STATUS_ERRORS
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "blocked_fix_source_reranking_schema_audit",
        "validation_errors": len(errors),
        "next_todo": NEXT_TODO,
        "input_artifacts": {
            "docker_materialization_summary": rel_path(args.docker_materialization_artifact / "summary.json"),
            "runtime_audit_manifest": rel_path(args.audit_dir / "audit_manifest.json"),
        },
        "output_artifacts": {
            "summary": rel_path(output_dir / "summary.json"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
            "gate_review": rel_path(output_dir / "gate_review.csv"),
            "next_contract": rel_path(output_dir / "next_contract.json"),
            "report": rel_path(output_dir / "report.md"),
        },
        "decision": {
            "schema_audit_passed": not errors,
            "ready_for_metric_protocol_freeze": not errors,
            "metric_run_allowed_now": False,
            "source_reranking_metrics_run": False,
            "official_test_usage": False,
        },
    }
    next_contract = {
        "schema_version": f"{SCHEMA_VERSION}_next_contract",
        "status": "ready_for_source_reranking_metric_protocol_freeze" if not errors else "blocked",
        "next_todo": NEXT_TODO,
        "must_freeze_next": [
            "score_definitions_S0_S1_S2_controls",
            "K_grid_and_family_aggregation",
            "Recall@K_GT_match_protocol",
            "Violation@K_label_source_by_family",
            "normalization_and_no_lambda_tuning_policy",
        ],
        "must_not_do": [
            "run_metrics_before_protocol_freeze",
            "use_official_test",
            "include_support_contact_in_success_aggregation",
            "put_Ze_inside_Ce",
        ],
    }
    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "next_contract.json", next_contract)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_csv(output_dir / "gate_review.csv", gate_rows)
    (output_dir / "report.md").write_text(make_report(summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
