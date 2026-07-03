#!/usr/bin/env python3
"""Lock H002 validation-only paper positioning after no external test response."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_INGESTION_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_test_benchmark_external_response_ingestion_after_request"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_validation_only_position_lock_after_no_external_response"

EXPECTED_INGESTION_STATUS = "h002_test_benchmark_external_response_ingestion_after_request_ready_blocked_no_external_response"
EXPECTED_INGESTION_NEXT = "compatibility_dataset_v3_validation_only_position_lock_after_no_external_response"

SCHEMA_VERSION = "h002_validation_only_position_lock_after_no_external_response_v1"
STATUS_READY = "h002_validation_only_position_lock_after_no_external_response_ready"
STATUS_ERRORS = "h002_validation_only_position_lock_after_no_external_response_input_errors"
SELECTED_PATH = "validation_only_appendix_secondary_lock_keep_test_benchmark_blocked"
NEXT_TODO = "compatibility_dataset_v3_h002_post_validation_position_path_decision"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
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


def validate_ingestion(ingestion_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    summary_path = ingestion_dir / "summary.json"
    if not summary_path.exists():
        errors.append({"error_type": "missing_ingestion_summary", "path": rel_path(summary_path)})
        return {}, errors
    summary = read_json(summary_path)
    if summary.get("status") != EXPECTED_INGESTION_STATUS:
        errors.append({"error_type": "unexpected_ingestion_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_INGESTION_NEXT:
        errors.append({"error_type": "unexpected_ingestion_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "ingestion_validation_errors", "actual": summary.get("validation_errors")})
    if line_count(ingestion_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "ingestion_validation_errors_file_not_empty"})

    decision = summary.get("decision", {})
    expected_false = [
        "external_response_found",
        "official_eval_server_confirmed",
        "independent_relation_test_label_confirmed",
        "official_validation_standard_confirmed",
        "checkpoint_reproduction_is_sufficient",
        "prediction_only_test_scan_export_is_sufficient",
        "test_benchmark_execution_allowed",
    ]
    for key in expected_false:
        if decision.get(key) is not False:
            errors.append({"error_type": "unexpected_ingestion_decision", "key": key, "actual": decision.get(key), "expected": False})
    if decision.get("validation_table_position") != "appendix_or_secondary_analysis_only":
        errors.append({"error_type": "unexpected_validation_table_position", "actual": decision.get("validation_table_position")})
    response_input = summary.get("response_input", {})
    if response_input.get("candidate_response_files") != 0:
        errors.append({"error_type": "candidate_response_files_not_zero", "actual": response_input.get("candidate_response_files")})
    return summary, errors


def paper_position_rows() -> list[dict[str, Any]]:
    return [
        {
            "item": "dataset_split",
            "locked_position": "official_3DSSG_validation_split",
            "paper_location": "appendix_or_secondary_analysis",
            "allowed_wording": "evaluated on the official 3DSSG validation split",
            "blocked_wording": "official 3DSSG test benchmark",
            "rationale": "verified public relation GT exists for validation, not for test",
        },
        {
            "item": "evaluation_protocol",
            "locked_position": "custom_H002_reliability_reranking_protocol",
            "paper_location": "method_analysis_or_appendix",
            "allowed_wording": "custom reliability/reranking evaluation protocol",
            "blocked_wording": "official leaderboard protocol",
            "rationale": "H002 defines C_e reranking and Violation@K, which are not official 3DSSG leaderboard metrics",
        },
        {
            "item": "source_reranking_table",
            "locked_position": "validation_level_evidence",
            "paper_location": "appendix_or_secondary_analysis",
            "allowed_wording": "validation-level source-reranking evidence",
            "blocked_wording": "final benchmark table",
            "rationale": "test relation GT/evaluator is not confirmed",
        },
        {
            "item": "open3dsg_source",
            "locked_position": "open_vocabulary_source_closed_vocabulary_evaluation",
            "paper_location": "source_description_and_caveat",
            "allowed_wording": "Open3DSG is used as an open-vocabulary relation source and evaluated after mapping to closed 3DSSG labels",
            "blocked_wording": "unconstrained open-set GT evaluation",
            "rationale": "source predictions may be open-vocabulary, but GT/Recall@K are closed-label 3DSSG mappings",
        },
    ]


def allowed_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "validation_source_reranking",
            "allowed": True,
            "wording": "H002 reranks VL-SAT and Open3DSG validation predictions using source_score x C_e.",
            "required_caveat": "official validation split; not official test benchmark",
        },
        {
            "claim_id": "validation_recall_violation_improvement",
            "allowed": True,
            "wording": "On the validation split, H002 reports Recall@K and Violation@K changes under a frozen custom protocol.",
            "required_caveat": "validation-level evidence only; report negative recall cells and family caveats",
        },
        {
            "claim_id": "open_vocab_source_closed_eval",
            "allowed": True,
            "wording": "Open3DSG is treated as an open-vocabulary relation source, but quantitative evaluation is mapped to closed-vocabulary 3DSSG relation families.",
            "required_caveat": "do not claim unconstrained open-set GT evaluation",
        },
        {
            "claim_id": "compatibility_layer_transfer",
            "allowed": True,
            "wording": "The same H002 compatibility layer can be applied to two validation prediction sources under the mapped 3DSSG family protocol.",
            "required_caveat": "validation-only and scoped to promoted families",
        },
    ]


def blocked_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "official_test_result",
            "blocked": True,
            "blocked_wording": "official 3DSSG test result",
            "reason": "no verified relation-test GT or hidden evaluation server",
        },
        {
            "claim_id": "sota_or_leaderboard",
            "blocked": True,
            "blocked_wording": "SOTA or leaderboard performance",
            "reason": "current table is validation-level custom protocol, not official test/leaderboard",
        },
        {
            "claim_id": "unconstrained_open_set_gt",
            "blocked": True,
            "blocked_wording": "unconstrained open-set relation GT evaluation",
            "reason": "quantitative GT is closed-vocabulary 3DSSG mapping",
        },
        {
            "claim_id": "validation_as_final_benchmark",
            "blocked": True,
            "blocked_wording": "validation table as final benchmark table",
            "reason": "official validation-as-standard reporting protocol is not confirmed",
        },
        {
            "claim_id": "prediction_only_test_recall",
            "blocked": True,
            "blocked_wording": "Recall@K on prediction-only 3RScan test scans",
            "reason": "without relation GT, recall denominator is undefined",
        },
    ]


def reopen_condition_rows() -> list[dict[str, Any]]:
    return [
        {
            "route": "official_relationships_test_json",
            "required_evidence": "official relation-test file, provenance, checksum, scan split, object-id schema, and split-disjointness proof",
            "unblocks": "local test materialization, schema audit, and single final test run",
        },
        {
            "route": "hidden_evaluation_server",
            "required_evidence": "official server URL, task definition, submission schema, metric list, K policy, and submission frequency policy",
            "unblocks": "test prediction export and accepted benchmark submission",
        },
        {
            "route": "validation_is_standard_reporting_split",
            "required_evidence": "maintainer or official documentation statement that validation is the intended reporting split for 3DSSG relation prediction",
            "unblocks": "promotion of validation table from appendix/secondary analysis to paper-facing benchmark with caveat",
        },
        {
            "route": "human_audited_reliability_benchmark",
            "required_evidence": "new benchmark protocol, held-out scan selection, blinded labeling, accept/reject/abstain schema, IAA, release plan, and claim separated from official 3DSSG test",
            "unblocks": "separate H002 reliability benchmark claim, not official 3DSSG test claim",
        },
    ]


def source_vocab_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "source": "VL-SAT",
            "source_role": "closed-vocabulary/source-prediction baseline for 3DSSG validation",
            "evaluation_gt": "closed-vocabulary 3DSSG validation GT",
            "claim_boundary": "validation prediction reranking only",
        },
        {
            "source": "Open3DSG",
            "source_role": "open-vocabulary relation source",
            "evaluation_gt": "closed-vocabulary 3DSSG validation GT after mapping",
            "claim_boundary": "open-vocabulary source, not unconstrained open-set GT evaluation",
        },
    ]


def metric_position_rows() -> list[dict[str, Any]]:
    return [
        {
            "metric": "Recall@K",
            "current_use": "validation-level source reranking",
            "paper_role": "secondary/appendix unless validation-as-standard is confirmed",
            "official_test_role": "blocked",
        },
        {
            "metric": "Violation@K",
            "current_use": "custom H002 reliability/geometry-consistency diagnostic on validation predictions",
            "paper_role": "secondary/appendix mechanism evidence",
            "official_test_role": "blocked until GT/evaluator exists",
        },
        {
            "metric": "C_e mechanism AUROC/control metrics",
            "current_use": "mechanism evidence for compatibility layer",
            "paper_role": "method analysis",
            "official_test_role": "not an official benchmark metric",
        },
    ]


def write_wording_guidance(path: Path) -> None:
    text = """# H002 Validation-Only Wording Lock

## Allowed

- We evaluate H002 source reranking on the official 3DSSG validation split.
- We apply H002 to VL-SAT and Open3DSG validation predictions.
- Open3DSG is used as an open-vocabulary relation source, while quantitative
  Recall@K is computed after mapping to closed-vocabulary 3DSSG relation labels.
- Recall@K and Violation@K are reported as validation-level custom protocol
  evidence.

## Blocked

- Official 3DSSG test result.
- SOTA or leaderboard claim.
- Unconstrained open-set relation-GT evaluation.
- Validation table as final benchmark table without official validation-as-standard
  evidence.
- Recall@K on prediction-only 3RScan test scans without relation GT/evaluator.

## Reopen Rule

Reopen the test benchmark path only if official `relationships_test.json`, a hidden
evaluation server, an official validation-as-standard statement, or a separately
defined human-audited benchmark protocol is available and recorded.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_report(path: Path, output_dir: Path, status: str, validation_errors: int) -> None:
    text = f"""# H002 Validation-Only Position Lock

## Purpose

No external official response/provenance was ingested for 3DSSG relation-test GT or
hidden evaluation. This gate locks the current H002 source-reranking result as
validation-level evidence and prevents accidental promotion to an official test or
SOTA claim.

## Result

```text
artifact_root = {rel_path(output_dir)}/
status = {status}
selected_path = {SELECTED_PATH}
validation_errors = {validation_errors}
paper_position = appendix_or_secondary_analysis
official_test_benchmark = blocked
next_todo = {NEXT_TODO}
```

## Locked Interpretation

- Current H002 source reranking uses VL-SAT and Open3DSG validation predictions.
- GT comparison is against official 3DSSG validation relation labels.
- Open3DSG may be described as an open-vocabulary relation source, but quantitative
  evaluation is closed-vocabulary 3DSSG mapping.
- The table can support validation-level mechanism/deployability evidence, not an
  official test benchmark.

## Reopen Conditions

The test path can reopen only with official `relationships_test.json`, hidden
evaluation server details, official validation-as-standard guidance, or a new
human-audited reliability benchmark that is explicitly not the official 3DSSG test.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    ingestion_summary, errors = validate_ingestion(args.ingestion_dir)
    status = STATUS_ERRORS if errors else STATUS_READY
    selected_path = "input_errors_fix_response_ingestion_before_position_lock" if errors else SELECTED_PATH
    next_todo = EXPECTED_INGESTION_NEXT if errors else NEXT_TODO

    validation_errors_path = output_dir / "validation_errors.jsonl"
    paper_position_path = output_dir / "paper_position_lock.csv"
    allowed_claims_path = output_dir / "allowed_claims.csv"
    blocked_claims_path = output_dir / "blocked_claims.csv"
    reopen_conditions_path = output_dir / "reopen_conditions.csv"
    source_vocab_boundary_path = output_dir / "source_vocab_boundary.csv"
    metric_position_path = output_dir / "metric_position.csv"
    wording_guidance_path = output_dir / "wording_guidance.md"
    next_contract_path = output_dir / "next_contract.json"
    report_path = output_dir / "report.md"
    summary_path = output_dir / "summary.json"

    write_jsonl(validation_errors_path, errors)
    write_csv(paper_position_path, paper_position_rows())
    write_csv(allowed_claims_path, allowed_claim_rows())
    write_csv(blocked_claims_path, blocked_claim_rows())
    write_csv(reopen_conditions_path, reopen_condition_rows())
    write_csv(source_vocab_boundary_path, source_vocab_boundary_rows())
    write_csv(metric_position_path, metric_position_rows())
    write_wording_guidance(wording_guidance_path)
    write_report(report_path, output_dir, status, len(errors))
    write_json(
        next_contract_path,
        {
            "next_todo": next_todo,
            "locked_position": "validation_only_appendix_or_secondary_analysis",
            "allowed_claims": [
                "validation-level source reranking on VL-SAT/Open3DSG",
                "Recall@K and Violation@K under custom H002 validation protocol",
                "Open3DSG as open-vocabulary source with closed-vocabulary 3DSSG mapping",
            ],
            "blocked_claims": [
                "official 3DSSG test result",
                "SOTA/leaderboard result",
                "unconstrained open-set GT evaluation",
                "validation table as final benchmark without official validation-as-standard evidence",
            ],
            "reopen_conditions": [
                "official relationships_test.json",
                "hidden evaluation server",
                "official validation-as-standard statement",
                "separate human-audited reliability benchmark protocol",
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
            "ingestion_summary": rel_path(args.ingestion_dir / "summary.json"),
            "ingestion_next_contract": rel_path(args.ingestion_dir / "next_contract.json"),
        },
        "locked_position": {
            "paper_position": "appendix_or_secondary_analysis",
            "dataset_basis": "official_3DSSG_validation_split",
            "evaluation_protocol": "custom_H002_source_reranking_reliability_protocol",
            "official_test_benchmark": False,
            "validation_table_as_final_benchmark": False,
            "open3dsg_source_boundary": "open_vocabulary_source_closed_vocabulary_3dssg_mapping",
        },
        "decision": {
            "allowed_validation_source_reranking_claim": True,
            "allowed_recall_violation_validation_improvement_claim": True,
            "allowed_open_vocab_source_closed_eval_claim": True,
            "official_test_result_claim_allowed": False,
            "sota_or_leaderboard_claim_allowed": False,
            "unconstrained_open_set_gt_claim_allowed": False,
            "validation_table_final_benchmark_claim_allowed": False,
            "test_benchmark_execution_allowed": False,
        },
        "ingestion_stage_status": ingestion_summary.get("status"),
        "output_artifacts": {
            "artifact_root": rel_path(output_dir),
            "summary": rel_path(summary_path),
            "validation_errors": rel_path(validation_errors_path),
            "paper_position_lock": rel_path(paper_position_path),
            "allowed_claims": rel_path(allowed_claims_path),
            "blocked_claims": rel_path(blocked_claims_path),
            "reopen_conditions": rel_path(reopen_conditions_path),
            "source_vocab_boundary": rel_path(source_vocab_boundary_path),
            "metric_position": rel_path(metric_position_path),
            "wording_guidance": rel_path(wording_guidance_path),
            "next_contract": rel_path(next_contract_path),
            "report": rel_path(report_path),
        },
    }
    write_json(summary_path, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
