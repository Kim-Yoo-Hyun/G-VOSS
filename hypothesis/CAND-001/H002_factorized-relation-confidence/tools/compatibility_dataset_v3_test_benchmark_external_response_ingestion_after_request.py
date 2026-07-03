#!/usr/bin/env python3
"""Ingest external provenance responses for the H002 test benchmark gate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_REQUEST_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_test_benchmark_external_provenance_request_after_source_resolution"
DEFAULT_RESPONSE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_test_benchmark_external_response_inbox"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_test_benchmark_external_response_ingestion_after_request"

EXPECTED_REQUEST_STATUS = "h002_test_benchmark_external_provenance_request_after_source_resolution_ready"
EXPECTED_REQUEST_NEXT = "compatibility_dataset_v3_test_benchmark_external_response_ingestion_after_request"

SCHEMA_VERSION = "h002_test_benchmark_external_response_ingestion_after_request_v1"
STATUS_NO_RESPONSE = "h002_test_benchmark_external_response_ingestion_after_request_ready_blocked_no_external_response"
STATUS_RESPONSE_DETECTED = "h002_test_benchmark_external_response_ingestion_after_request_ready_needs_manual_classification"
STATUS_ERRORS = "h002_test_benchmark_external_response_ingestion_after_request_input_errors"
SELECTED_PATH_NO_RESPONSE = "no_external_response_keep_test_benchmark_blocked_select_validation_position_lock"
SELECTED_PATH_RESPONSE_DETECTED = "external_response_detected_requires_manual_positive_provenance_classification"
NEXT_TODO_NO_RESPONSE = "compatibility_dataset_v3_validation_only_position_lock_after_no_external_response"
NEXT_TODO_RESPONSE_DETECTED = "compatibility_dataset_v3_test_benchmark_external_response_classification_after_ingestion"

RESPONSE_EXTENSIONS = {".md", ".txt", ".json", ".csv", ".eml", ".pdf"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-dir", type=Path, default=DEFAULT_REQUEST_DIR)
    parser.add_argument("--response-dir", type=Path, default=DEFAULT_RESPONSE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def validate_request(request_dir: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    summary_path = request_dir / "summary.json"
    next_contract_path = request_dir / "next_contract.json"
    if not summary_path.exists():
        errors.append({"error_type": "missing_request_summary", "path": rel_path(summary_path)})
        return {}, {}, errors
    request_summary = read_json(summary_path)
    next_contract = read_json(next_contract_path) if next_contract_path.exists() else {}
    if not next_contract_path.exists():
        errors.append({"error_type": "missing_request_next_contract", "path": rel_path(next_contract_path)})
    if request_summary.get("status") != EXPECTED_REQUEST_STATUS:
        errors.append({"error_type": "unexpected_request_status", "actual": request_summary.get("status")})
    if request_summary.get("next_todo") != EXPECTED_REQUEST_NEXT:
        errors.append({"error_type": "unexpected_request_next_todo", "actual": request_summary.get("next_todo")})
    if request_summary.get("validation_errors") != 0:
        errors.append({"error_type": "request_validation_errors", "actual": request_summary.get("validation_errors")})
    if line_count(request_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "request_validation_errors_file_not_empty"})
    if not (request_dir / "request_packet.md").exists():
        errors.append({"error_type": "missing_request_packet", "path": rel_path(request_dir / "request_packet.md")})
    decision = request_summary.get("decision", {})
    if decision.get("request_packet_ready") is not True:
        errors.append({"error_type": "request_packet_not_ready", "actual": decision.get("request_packet_ready")})
    if decision.get("test_benchmark_execution_allowed") is not False:
        errors.append({"error_type": "request_stage_unexpectedly_allowed_test", "actual": decision.get("test_benchmark_execution_allowed")})
    if next_contract.get("next_todo") not in {EXPECTED_REQUEST_NEXT, None}:
        errors.append({"error_type": "unexpected_request_next_contract_todo", "actual": next_contract.get("next_todo")})
    return request_summary, next_contract, errors


def inventory_response_files(response_dir: Path) -> list[dict[str, Any]]:
    if not response_dir.exists():
        return [
            {
                "response_dir": rel_path(response_dir),
                "response_dir_exists": False,
                "candidate_file_found": False,
                "path": "",
                "extension": "",
                "size_bytes": "",
                "sha256": "",
                "classification_status": "missing_response_dir",
            }
        ]

    rows: list[dict[str, Any]] = []
    for path in sorted(response_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in RESPONSE_EXTENSIONS:
            continue
        rows.append(
            {
                "response_dir": rel_path(response_dir),
                "response_dir_exists": True,
                "candidate_file_found": True,
                "path": rel_path(path),
                "extension": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "classification_status": "detected_unclassified",
            }
        )
    if not rows:
        rows.append(
            {
                "response_dir": rel_path(response_dir),
                "response_dir_exists": True,
                "candidate_file_found": False,
                "path": "",
                "extension": "",
                "size_bytes": "",
                "sha256": "",
                "classification_status": "no_candidate_response_files",
            }
        )
    return rows


def response_found(inventory_rows: list[dict[str, Any]]) -> bool:
    return any(row.get("candidate_file_found") is True for row in inventory_rows)


def decision_matrix_rows(found: bool) -> list[dict[str, Any]]:
    status = "unclassified_external_response" if found else "missing_external_response"
    return [
        {
            "decision_key": "official_eval_server_confirmed",
            "current_value": False,
            "evidence_status": status,
            "required_positive_evidence": "official server URL, submission schema, metric list, and split policy",
            "effect": "test benchmark remains blocked",
        },
        {
            "decision_key": "independent_relation_test_label_confirmed",
            "current_value": False,
            "evidence_status": status,
            "required_positive_evidence": "official relation-test label file provenance, checksum, and split mapping",
            "effect": "test Recall@K cannot be computed as benchmark",
        },
        {
            "decision_key": "official_validation_standard_confirmed",
            "current_value": False,
            "evidence_status": status,
            "required_positive_evidence": "official statement that validation is the intended relation-prediction reporting split",
            "effect": "validation table stays appendix/secondary analysis",
        },
        {
            "decision_key": "checkpoint_reproduction_is_sufficient",
            "current_value": False,
            "evidence_status": "unchanged",
            "required_positive_evidence": "relation GT/evaluator, not just a predictor checkpoint",
            "effect": "VL-SAT/Open3DSG checkpoints alone do not unblock test table",
        },
        {
            "decision_key": "prediction_only_test_scan_export_is_sufficient",
            "current_value": False,
            "evidence_status": "unchanged",
            "required_positive_evidence": "accepted evaluator or labels for the same test predictions",
            "effect": "3RScan test prediction export alone is not Recall@K",
        },
    ]


def blocked_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_or_action": "official test Recall@K / Violation@K benchmark table",
            "status": "blocked",
            "reason": "no official relation-test GT or accepted hidden evaluator ingested",
        },
        {
            "claim_or_action": "validation table as final benchmark table",
            "status": "blocked",
            "reason": "official validation-as-standard reporting protocol is not confirmed",
        },
        {
            "claim_or_action": "checkpoint reproduction as sufficient benchmark provenance",
            "status": "blocked",
            "reason": "checkpoints produce predictions but do not supply relation labels or accepted evaluator",
        },
        {
            "claim_or_action": "prediction-only 3RScan test scan export as Recall@K benchmark",
            "status": "blocked",
            "reason": "prediction rows without relation GT cannot define recall denominator",
        },
        {
            "claim_or_action": "single final test run",
            "status": "blocked",
            "reason": "must first freeze source predictions, C_e scorer, normalization, K grid, and metric schema after positive provenance",
        },
    ]


def response_requirement_rows() -> list[dict[str, Any]]:
    return [
        {
            "route": "hidden_official_eval_server",
            "positive_evidence_required": "maintainer/official docs provide server URL, accepted task name, submission payload schema, metric list, and split policy",
            "unblocks": "test-source prediction export and single final test submission protocol",
        },
        {
            "route": "public_or_private_relation_test_gt",
            "positive_evidence_required": "official `relationships_test.json` or equivalent relation-label file with provenance, checksum, scan split, and object-id schema",
            "unblocks": "local test Recall@K / Violation@K materialization",
        },
        {
            "route": "validation_is_standard_reporting_split",
            "positive_evidence_required": "official statement or accepted benchmark practice that 3DSSG relation prediction reports validation split because test labels/evaluator are unavailable",
            "unblocks": "validation table promotion from appendix/secondary to paper-facing benchmark, with wording caveat",
        },
        {
            "route": "negative_response",
            "positive_evidence_required": "official answer that no relation-test labels/evaluator are available and validation is not an official benchmark substitute",
            "unblocks": "keep validation-only analysis and remove test-benchmark claim from current paper scope",
        },
    ]


def write_report(path: Path, *, status: str, selected_path: str, found: bool, next_todo: str, output_dir: Path, response_dir: Path) -> None:
    response_state = "detected but unclassified" if found else "not found"
    text = f"""# H002 External Response Ingestion

## Purpose

The previous gate prepared a request packet for official 3DSSG/3RScan relation-test
provenance. This ingestion step records whether an external response or official
documentation has actually been received before any test benchmark runner is opened.

## Result

```text
artifact_root = {rel_path(output_dir)}/
status = {status}
selected_path = {selected_path}
external_response = {response_state}
test_benchmark_execution_allowed = false
validation_table_position = appendix_or_secondary_analysis_only
next_todo = {next_todo}
```

Response inbox:

```text
{rel_path(response_dir)}
```

## Decision

- No official relation-test GT or accepted hidden evaluation server is treated as
  confirmed in this gate.
- VL-SAT/Open3DSG checkpoints remain prediction sources only; they do not provide the
  relation-label denominator needed for test `Recall@K`.
- Prediction-only 3RScan test export remains insufficient for a benchmark table.
- Validation source-reranking results stay appendix/secondary analysis unless an
  official validation-as-standard protocol is confirmed.

## Next

Run `{next_todo}`. If a real response arrives later, put the response artifact in the
response inbox and rerun this ingestion script before changing benchmark status.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    request_summary, next_contract, errors = validate_request(args.request_dir)
    inventory_rows = inventory_response_files(args.response_dir)
    found = response_found(inventory_rows)

    if errors:
        status = STATUS_ERRORS
        selected_path = "input_errors_fix_request_stage_before_response_ingestion"
        next_todo = EXPECTED_REQUEST_NEXT
    elif found:
        status = STATUS_RESPONSE_DETECTED
        selected_path = SELECTED_PATH_RESPONSE_DETECTED
        next_todo = NEXT_TODO_RESPONSE_DETECTED
    else:
        status = STATUS_NO_RESPONSE
        selected_path = SELECTED_PATH_NO_RESPONSE
        next_todo = NEXT_TODO_NO_RESPONSE

    validation_errors_path = output_dir / "validation_errors.jsonl"
    response_inventory_path = output_dir / "response_inventory.csv"
    decision_matrix_path = output_dir / "ingestion_decision_matrix.csv"
    blocked_claims_path = output_dir / "blocked_claims.csv"
    response_requirements_path = output_dir / "response_requirements.csv"
    next_contract_path = output_dir / "next_contract.json"
    report_path = output_dir / "report.md"
    summary_path = output_dir / "summary.json"

    write_jsonl(validation_errors_path, errors)
    write_csv(response_inventory_path, inventory_rows)
    write_csv(decision_matrix_path, decision_matrix_rows(found))
    write_csv(blocked_claims_path, blocked_claim_rows())
    write_csv(response_requirements_path, response_requirement_rows())
    write_report(
        report_path,
        status=status,
        selected_path=selected_path,
        found=found,
        next_todo=next_todo,
        output_dir=output_dir,
        response_dir=args.response_dir,
    )
    write_json(
        next_contract_path,
        {
            "next_todo": next_todo,
            "expected_input_if_positive_response_arrives": [
                "official evaluation server URL and submission schema",
                "or official relation-test label file provenance/checksum",
                "or official validation-as-standard reporting statement",
            ],
            "do_not_do": [
                "do not run test benchmark metrics before positive provenance classification",
                "do not use checkpoint reproduction as relation test GT",
                "do not use prediction-only test scan export as Recall@K",
                "do not promote validation table as final benchmark without official protocol evidence",
            ],
            "after_positive_classification": [
                "freeze source prediction generation command",
                "freeze C_e scorer/hash/normalization",
                "freeze K grid and metric schema",
                "run split-disjointness and blocked-field schema audit",
                "execute a single final test run policy",
            ],
        },
    )

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(errors),
        "next_todo": next_todo,
        "input_artifacts": {
            "request_summary": rel_path(args.request_dir / "summary.json"),
            "request_next_contract": rel_path(args.request_dir / "next_contract.json"),
            "request_packet": rel_path(args.request_dir / "request_packet.md"),
        },
        "response_input": {
            "response_dir": rel_path(args.response_dir),
            "response_dir_exists": args.response_dir.exists(),
            "candidate_response_files": sum(1 for row in inventory_rows if row.get("candidate_file_found") is True),
        },
        "decision": {
            "external_response_found": found,
            "official_eval_server_confirmed": False,
            "independent_relation_test_label_confirmed": False,
            "official_validation_standard_confirmed": False,
            "checkpoint_reproduction_is_sufficient": False,
            "prediction_only_test_scan_export_is_sufficient": False,
            "test_benchmark_execution_allowed": False,
            "validation_table_position": "appendix_or_secondary_analysis_only",
        },
        "request_stage_status": request_summary.get("status"),
        "request_stage_next_contract": next_contract.get("next_todo"),
        "output_artifacts": {
            "artifact_root": rel_path(output_dir),
            "summary": rel_path(summary_path),
            "validation_errors": rel_path(validation_errors_path),
            "response_inventory": rel_path(response_inventory_path),
            "ingestion_decision_matrix": rel_path(decision_matrix_path),
            "blocked_claims": rel_path(blocked_claims_path),
            "response_requirements": rel_path(response_requirements_path),
            "next_contract": rel_path(next_contract_path),
            "report": rel_path(report_path),
        },
    }
    write_json(summary_path, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
