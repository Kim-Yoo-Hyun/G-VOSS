#!/usr/bin/env python3
"""Prepare H002 external provenance request packet for test benchmark gating."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SOURCE_RESOLUTION_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_test_benchmark_source_resolution_after_preflight"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_test_benchmark_external_provenance_request_after_source_resolution"

EXPECTED_SOURCE_RESOLUTION_STATUS = "h002_test_benchmark_source_resolution_after_preflight_ready_blocked"
EXPECTED_SOURCE_RESOLUTION_NEXT = "compatibility_dataset_v3_test_benchmark_external_provenance_request_after_source_resolution"

SCHEMA_VERSION = "h002_test_benchmark_external_provenance_request_after_source_resolution_v1"
STATUS_READY = "h002_test_benchmark_external_provenance_request_after_source_resolution_ready"
STATUS_ERRORS = "h002_test_benchmark_external_provenance_request_after_source_resolution_input_errors"
SELECTED_PATH = "external_request_packet_ready_keep_test_benchmark_blocked"
NEXT_TODO = "compatibility_dataset_v3_test_benchmark_external_response_ingestion_after_request"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-resolution-dir", type=Path, default=DEFAULT_SOURCE_RESOLUTION_DIR)
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


def validate_inputs(source_resolution_summary: dict[str, Any], source_resolution_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if source_resolution_summary.get("status") != EXPECTED_SOURCE_RESOLUTION_STATUS:
        errors.append({"error_type": "unexpected_source_resolution_status", "actual": source_resolution_summary.get("status")})
    if source_resolution_summary.get("next_todo") != EXPECTED_SOURCE_RESOLUTION_NEXT:
        errors.append({"error_type": "unexpected_source_resolution_next_todo", "actual": source_resolution_summary.get("next_todo")})
    if source_resolution_summary.get("validation_errors") != 0:
        errors.append({"error_type": "source_resolution_validation_errors", "actual": source_resolution_summary.get("validation_errors")})
    if line_count(source_resolution_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "source_resolution_validation_errors_file_not_empty"})
    decision = source_resolution_summary.get("decision", {})
    expected_false = {
        "accepted_official_eval_server_confirmed": decision.get("accepted_official_eval_server_confirmed"),
        "independent_relation_test_label_confirmed": decision.get("independent_relation_test_label_confirmed"),
        "relation_test_source_predictions_available": decision.get("relation_test_source_predictions_available"),
        "experiments_test_run_allowed": decision.get("experiments_test_run_allowed"),
    }
    for key, actual in expected_false.items():
        if actual is not False:
            errors.append({"error_type": "unexpected_source_resolution_decision", "key": key, "actual": actual, "expected": False})
    if decision.get("scan_level_3rscan_test_split_exists") is not True:
        errors.append({"error_type": "expected_scan_level_test_split_exists", "actual": decision.get("scan_level_3rscan_test_split_exists")})
    if decision.get("scan_level_split_is_sufficient_for_h002") is not False:
        errors.append({"error_type": "scan_level_split_should_not_be_sufficient", "actual": decision.get("scan_level_split_is_sufficient_for_h002")})
    return errors


def source_evidence_rows() -> list[dict[str, Any]]:
    return [
        {
            "source_id": "3rscan_submission_policy",
            "url": "https://vmnavab26.in.tum.de/3RScan/documentation.php",
            "checked_at": "2026-07-03",
            "relevant_observation": "3RScan documentation has a test-data submission policy and one-shot evaluation-server style language.",
            "why_it_matters": "This suggests an official scan-level evaluation culture exists, but H002 still needs relation-label task compatibility.",
        },
        {
            "source_id": "3rscan_github",
            "url": "https://github.com/WaldJohannaU/3RScan",
            "checked_at": "2026-07-03",
            "relevant_observation": "3RScan provides scan-level data and semantic/geometry resources.",
            "why_it_matters": "Useful for test-scan prediction and geometry evidence, but not sufficient as 3DSSG relation GT.",
        },
        {
            "source_id": "3dssg_official_repo",
            "url": "https://github.com/3DSSG/3DSSG.github.io/",
            "checked_at": "2026-07-03",
            "relevant_observation": "3DSSG describes scene graphs, objects, relationships, and dataset package organization.",
            "why_it_matters": "Primary place to ask whether a relation test split or evaluation server exists.",
        },
        {
            "source_id": "open3dsg_readme",
            "url": "https://github.com/boschresearch/Open3DSG",
            "checked_at": "2026-07-03",
            "relevant_observation": "Open3DSG README states 3DSSG provides pre-constructed GT scene graphs for training and validation.",
            "why_it_matters": "Supports the current validation-only boundary and motivates asking whether hidden/public relation test GT exists.",
        },
        {
            "source_id": "open3dsg_run_py",
            "url": "https://github.com/boschresearch/Open3DSG/blob/main/open3dsg/scripts/run.py",
            "checked_at": "2026-07-03",
            "relevant_observation": "`test_scans_3rscan` is described as 3RScan test scans not labeled in 3DSSG.",
            "why_it_matters": "Prediction export on 3RScan test scans is not enough for H002 Recall@K without relation GT or eval server.",
        },
        {
            "source_id": "vlsat_repo",
            "url": "https://github.com/wz7in/CVPR2023-VLSAT",
            "checked_at": "2026-07-03",
            "relevant_observation": "VL-SAT repository provides code, checkpoint link, and train/eval commands.",
            "why_it_matters": "VL-SAT test prediction may be reproducible if exact test input/GT route is confirmed.",
        },
    ]


def request_question_rows() -> list[dict[str, Any]]:
    return [
        {
            "priority": 1,
            "question_id": "relation_test_gt_availability",
            "question": "Does 3DSSG provide official relation labels for the 3RScan test split, either publicly or through a hidden evaluation server?",
            "needed_answer_type": "yes/no plus access instructions",
            "unblocks": "Recall@K benchmark on test",
        },
        {
            "priority": 2,
            "question_id": "official_eval_server",
            "question": "Is there an accepted official evaluation server for 3DSSG relation prediction/triplet prediction? If yes, what is the submission URL and format?",
            "needed_answer_type": "server URL, submission schema, metric list, frequency/one-shot policy",
            "unblocks": "test benchmark without public GT labels",
        },
        {
            "priority": 3,
            "question_id": "relationships_test_json",
            "question": "Should a valid 3DSSG subset distribution include `relationships_test.json`, or are public labels intentionally limited to train/validation?",
            "needed_answer_type": "file list or official statement",
            "unblocks": "local test-label provenance decision",
        },
        {
            "priority": 4,
            "question_id": "test_scan_prediction_evaluation",
            "question": "Can predictions generated on 3RScan test scans be evaluated for relationship labels, or are those scans unlabeled for 3DSSG relation evaluation?",
            "needed_answer_type": "evaluation feasibility and required input/output fields",
            "unblocks": "VL-SAT/Open3DSG test-source prediction plan",
        },
        {
            "priority": 5,
            "question_id": "standard_paper_split",
            "question": "If no relation test evaluation is available, is the 3DSSG validation split the expected paper-reporting split for relation prediction methods?",
            "needed_answer_type": "recommended benchmark protocol",
            "unblocks": "validation-table paper positioning",
        },
        {
            "priority": 6,
            "question_id": "submission_payload",
            "question": "For relation prediction, should submissions use object IDs from the scan, directed subject-object pairs, top-K predicate scores, or full triplets?",
            "needed_answer_type": "JSON schema and metric definitions",
            "unblocks": "test materialization schema and final metric freeze",
        },
    ]


def readiness_matrix_rows() -> list[dict[str, Any]]:
    return [
        {
            "component": "VL-SAT checkpoint/source predictor",
            "current_state": "checkpoint route exists",
            "sufficient_for_test_recall": "false_without_relation_gt",
            "next_requirement": "exact test input split and relation GT/eval server",
        },
        {
            "component": "Open3DSG source predictor",
            "current_state": "test command route exists; local/H001 recovered source route exists",
            "sufficient_for_test_recall": "false_without_relation_gt",
            "next_requirement": "test source prediction export only after relation GT/eval route is confirmed",
        },
        {
            "component": "3RScan test scans",
            "current_state": "scan-level test split exists",
            "sufficient_for_test_recall": "false",
            "next_requirement": "3DSSG relation labels or hidden evaluator for those scans",
        },
        {
            "component": "H002 C_e scorer",
            "current_state": "validation protocol frozen; C_e excludes Z_e",
            "sufficient_for_test_recall": "partial",
            "next_requirement": "freeze scorer/hash/normalization before any accepted test run",
        },
        {
            "component": "Validation source-reranking table",
            "current_state": "appendix/secondary evidence",
            "sufficient_for_test_recall": "false",
            "next_requirement": "keep downgraded unless test route is confirmed",
        },
    ]


def request_packet_md() -> str:
    return "\n".join(
        [
            "# Request: 3DSSG Relation Test Benchmark Provenance",
            "",
            "Hello,",
            "",
            "I am working on a 3D Scene Graph relation reliability study using 3DSSG/3RScan, VL-SAT, and Open3DSG-style relation sources. I would like to clarify the official evaluation route for relation prediction on the 3DSSG/3RScan test split.",
            "",
            "Could you please confirm the following?",
            "",
            "1. Does 3DSSG provide official relationship labels for the 3RScan test split, either publicly or through a hidden evaluation server?",
            "2. If an official evaluation server exists for 3DSSG relation/triplet prediction, what is the submission URL, JSON schema, metric set, and submission policy?",
            "3. Should an official 3DSSG subset distribution include `relationships_test.json`, or are public relationship labels intentionally limited to train/validation?",
            "4. Can predictions generated on 3RScan test scans be evaluated for relationship labels, or are those scans unlabeled for 3DSSG relation evaluation?",
            "5. If no test relation evaluation is available, is the validation split the expected reporting split for 3DSSG relation prediction papers?",
            "",
            "For context, the method does not need to train on test labels. The goal is only to report a final frozen benchmark table using source predictions from VL-SAT/Open3DSG and fixed reranking scores. I will keep test evaluation one-shot if a hidden test server exists.",
            "",
            "Thank you.",
            "",
        ]
    )


def report_text(summary: dict[str, Any]) -> str:
    decision = summary["decision"]
    return "\n".join(
        [
            "# H002 External Provenance Request After Source Resolution",
            "",
            "## Purpose",
            "",
            "Prepare a request packet for official 3DSSG relation-test provenance or evaluation-server access.",
            "",
            "## Decision",
            "",
            f"- status: `{summary['status']}`",
            f"- selected path: `{summary['selected_path']}`",
            f"- next todo: `{summary['next_todo']}`",
            f"- request packet ready: `{str(decision['request_packet_ready']).lower()}`",
            f"- test benchmark execution allowed: `{str(decision['test_benchmark_execution_allowed']).lower()}`",
            f"- validation table position: `{decision['validation_table_position']}`",
            "",
            "## Key Point",
            "",
            "Official checkpoints or test-scan prediction routes are not enough. H002 needs either relation-label test GT or an accepted hidden evaluation server before Recall@K can be reported on test.",
            "",
            "## Next",
            "",
            "Send or use the request packet. If a positive response arrives, ingest it as external provenance before opening any test benchmark runner.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    source_resolution_summary_path = args.source_resolution_dir / "summary.json"
    if not source_resolution_summary_path.exists():
        raise FileNotFoundError(f"Missing source-resolution summary: {source_resolution_summary_path}")

    source_resolution_summary = read_json(source_resolution_summary_path)
    validation_errors = validate_inputs(source_resolution_summary, args.source_resolution_dir)
    status = STATUS_ERRORS if validation_errors else STATUS_READY

    decision = {
        "request_packet_ready": not validation_errors,
        "test_benchmark_execution_allowed": False,
        "checkpoint_reproduction_is_sufficient": False,
        "prediction_only_test_scan_export_is_sufficient": False,
        "validation_table_position": "appendix_or_secondary_analysis_only",
        "required_external_answer": "official evaluation server or independent 3DSSG relation-test label provenance",
        "single_final_test_run_policy_required_after_positive_response": True,
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH,
        "validation_errors": len(validation_errors),
        "decision": decision,
        "input_artifacts": {
            "source_resolution_summary": rel_path(source_resolution_summary_path),
            "source_resolution_next_contract": rel_path(args.source_resolution_dir / "next_contract.json"),
        },
        "output_artifacts": {
            "artifact_root": rel_path(args.output_dir),
            "source_evidence": rel_path(args.output_dir / "source_evidence.csv"),
            "request_questions": rel_path(args.output_dir / "request_questions.csv"),
            "readiness_matrix": rel_path(args.output_dir / "readiness_matrix.csv"),
            "request_packet": rel_path(args.output_dir / "request_packet.md"),
            "next_contract": rel_path(args.output_dir / "next_contract.json"),
            "report": rel_path(args.output_dir / "report.md"),
        },
        "next_todo": NEXT_TODO,
    }

    next_contract = {
        "next_todo": NEXT_TODO,
        "expected_input": [
            "email/contact response from 3DSSG/3RScan maintainers",
            "or official documentation proving relation test labels/evaluation server",
            "or official statement that validation split is the intended relation benchmark split",
        ],
        "positive_response_unblocks": [
            "test source prediction availability audit",
            "frozen C_e scorer/hash/normalization contract",
            "test materialization schema audit",
            "single final test run policy",
        ],
        "do_not_do": [
            "do not run test benchmark metric runner before response/provenance ingestion",
            "do not treat checkpoint reproduction as relation GT",
            "do not treat prediction-only 3RScan test export as Recall@K benchmark",
            "do not promote validation table as benchmark table",
        ],
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "summary.json", summary)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "source_evidence.csv", source_evidence_rows())
    write_csv(args.output_dir / "request_questions.csv", request_question_rows())
    write_csv(args.output_dir / "readiness_matrix.csv", readiness_matrix_rows())
    write_json(args.output_dir / "next_contract.json", next_contract)
    (args.output_dir / "request_packet.md").write_text(request_packet_md(), encoding="utf-8")
    (args.output_dir / "report.md").write_text(report_text(summary), encoding="utf-8")

    print(json.dumps({"status": status, "validation_errors": len(validation_errors), "next_todo": NEXT_TODO}, ensure_ascii=False, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
