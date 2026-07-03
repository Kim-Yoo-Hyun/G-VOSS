#!/usr/bin/env python3
"""Review and downgrade H002 source-reranking validation table before test benchmark."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SKELETON_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_validation_table_skeleton_after_claim_boundary_lock"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_validation_table_review_after_skeleton"

EXPECTED_SKELETON_STATUS = "h002_source_reranking_validation_table_skeleton_after_claim_boundary_lock_ready"
EXPECTED_SKELETON_NEXT = "compatibility_dataset_v3_source_reranking_validation_table_review_after_skeleton"

SCHEMA_VERSION = "h002_source_reranking_validation_table_review_after_skeleton_v1"
STATUS_READY = "h002_source_reranking_validation_table_review_after_skeleton_ready"
STATUS_ERRORS = "h002_source_reranking_validation_table_review_after_skeleton_input_errors"
SELECTED_PATH = "downgrade_validation_table_select_test_benchmark_preflight"
NEXT_TODO = "compatibility_dataset_v3_test_benchmark_preflight_after_validation_downgrade"

CANONICAL_VAL = REPO_ROOT / "local_dataset/3DSSG_subset/relationships_validation.json"
CANONICAL_TEST = REPO_ROOT / "local_dataset/3DSSG_subset/relationships_test.json"
STAGED_TEST_CANDIDATES = [
    REPO_ROOT / "local_dataset/Open3DSG_staged/h001_full_validation_runtime/data/3RScan/3DSSG_subset/relationships_test.json",
    REPO_ROOT / "local_dataset/Open3DSG_staged/h001_runtime/data/3RScan/3DSSG_subset/relationships_test.json",
    REPO_ROOT / "local_dataset/Open3DSG_staged/h002_train_full_runtime/data/3RScan/3DSSG_subset/relationships_test.json",
    REPO_ROOT / "local_dataset/Open3DSG_staged/training_repro/data/3RScan/3DSSG_subset/relationships_test.json",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skeleton-dir", type=Path, default=DEFAULT_SKELETON_DIR)
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


def load_scan_set(path: Path) -> tuple[set[str], int, int]:
    if not path.exists():
        return set(), 0, 0
    data = json.loads(path.read_text(encoding="utf-8"))
    scans = data.get("scans", [])
    unique = {scan.get("scan") for scan in scans if scan.get("scan")}
    rel_count = sum(len(scan.get("relationships") or []) for scan in scans)
    return unique, len(scans), rel_count


def validate_inputs(skeleton_summary: dict[str, Any], skeleton_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if skeleton_summary.get("status") != EXPECTED_SKELETON_STATUS:
        errors.append({"error_type": "unexpected_skeleton_status", "actual": skeleton_summary.get("status")})
    if skeleton_summary.get("next_todo") != EXPECTED_SKELETON_NEXT:
        errors.append({"error_type": "unexpected_skeleton_next_todo", "actual": skeleton_summary.get("next_todo")})
    if skeleton_summary.get("validation_errors") != 0:
        errors.append({"error_type": "skeleton_validation_errors", "actual": skeleton_summary.get("validation_errors")})
    if line_count(skeleton_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "skeleton_validation_errors_file_not_empty"})
    decision = skeleton_summary.get("decision", {})
    if decision.get("validation_table_skeleton_ready") is not True:
        errors.append({"error_type": "validation_table_skeleton_not_ready"})
    if decision.get("final_paper_result_promotion") != "not_yet":
        errors.append({"error_type": "unexpected_final_paper_result_promotion", "actual": decision.get("final_paper_result_promotion")})
    if decision.get("official_test_usage") is not False:
        errors.append({"error_type": "unexpected_official_test_usage", "actual": decision.get("official_test_usage")})
    return errors


def local_test_probe_rows() -> list[dict[str, Any]]:
    val_scans, val_entries, val_rels = load_scan_set(CANONICAL_VAL)
    rows = [
        {
            "candidate": "canonical_3dssg_subset_test",
            "path": rel_path(CANONICAL_TEST),
            "exists": CANONICAL_TEST.exists(),
            "scan_entries": 0,
            "unique_scans": 0,
            "relations": 0,
            "overlap_with_canonical_validation_scans": 0,
            "benchmark_use": "blocked_missing_local_file",
            "note": "canonical local_dataset/3DSSG_subset has no relationships_test.json",
        }
    ]
    for path in STAGED_TEST_CANDIDATES:
        scans, entries, rels = load_scan_set(path)
        overlap = len(scans & val_scans)
        if not path.exists():
            use = "blocked_missing_file"
            note = "file not present"
        elif entries == 0:
            use = "blocked_empty_file"
            note = "empty test json; not benchmark-ready"
        elif overlap == len(scans) and len(scans) > 0:
            use = "blocked_validation_alias_until_provenance_verified"
            note = "all unique scans overlap canonical validation; cannot be treated as independent test"
        else:
            use = "candidate_requires_provenance_and_split_audit"
            note = "non-empty file exists, but provenance/split/source availability must be audited"
        rows.append(
            {
                "candidate": path.parent.parent.parent.name + "/" + path.parent.parent.name if len(path.parts) > 2 else path.name,
                "path": rel_path(path),
                "exists": path.exists(),
                "scan_entries": entries,
                "unique_scans": len(scans),
                "relations": rels,
                "overlap_with_canonical_validation_scans": overlap,
                "benchmark_use": use,
                "note": note,
            }
        )
    rows.insert(
        0,
        {
            "candidate": "canonical_3dssg_subset_validation_reference",
            "path": rel_path(CANONICAL_VAL),
            "exists": CANONICAL_VAL.exists(),
            "scan_entries": val_entries,
            "unique_scans": len(val_scans),
            "relations": val_rels,
            "overlap_with_canonical_validation_scans": len(val_scans),
            "benchmark_use": "validation_reference_only",
            "note": "used only to detect test/validation aliasing",
        },
    )
    return rows


def validation_table_position_rows() -> list[dict[str, Any]]:
    return [
        {
            "table": "source_reranking_validation_primary_tradeoff",
            "old_position": "secondary_validation_table_candidate_or_appendix",
            "locked_position": "appendix_or_secondary_analysis_only",
            "main_benchmark_allowed": "false",
            "reason": "user decision: benchmark table should use test set, not validation table",
        },
        {
            "table": "source_reranking_controls",
            "old_position": "supporting_control_rows",
            "locked_position": "appendix_or_method_validation_controls",
            "main_benchmark_allowed": "false",
            "reason": "use only to explain validation-level factor separation and controls",
        },
        {
            "table": "source_family_caveats",
            "old_position": "required caveat table or footnote",
            "locked_position": "required_if_validation_table_reported",
            "main_benchmark_allowed": "false",
            "reason": "3/20 recall regressions block uniform-improvement wording",
        },
    ]


def preflight_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "gate": "test_label_provenance",
            "required_check": "Identify an independent official test label file or official evaluation server; reject validation aliases.",
            "blocks_if_fail": "no test benchmark table",
            "current_status": "not_ready",
        },
        {
            "gate": "split_disjointness",
            "required_check": "Scan IDs, object-pair IDs, candidate IDs, and generated contrast groups must not overlap train/validation/test in invalid ways.",
            "blocks_if_fail": "test contamination risk",
            "current_status": "pending",
        },
        {
            "gate": "source_prediction_availability",
            "required_check": "VL-SAT/Open3DSG source predictions must exist or be generated for the exact test split with frozen parser and source-score contract.",
            "blocks_if_fail": "cannot run source-reranking benchmark",
            "current_status": "pending",
        },
        {
            "gate": "frozen_Ce_model_and_features",
            "required_check": "Freeze C_e training rows, feature schema, family scope, score IDs, K grid, and no post-validation changes before test.",
            "blocks_if_fail": "test no longer independent",
            "current_status": "pending",
        },
        {
            "gate": "normalization_freeze",
            "required_check": "Freeze source-score and C_e normalization/calibration without using test labels or post-hoc test statistics that change ranking policy.",
            "blocks_if_fail": "transductive/test-tuned reranking risk",
            "current_status": "pending",
        },
        {
            "gate": "test_materialization_schema_audit",
            "required_check": "Create model-safe, source-rank, and hidden metric views for test; blocked-field hits must be zero.",
            "blocks_if_fail": "label/construction leakage risk",
            "current_status": "pending",
        },
        {
            "gate": "metric_and_claim_freeze",
            "required_check": "Freeze Recall@K, Violation@K, controls, family aggregation, confidence intervals, and exact paper wording before test run.",
            "blocks_if_fail": "cherry-picking/post-hoc claim risk",
            "current_status": "pending",
        },
        {
            "gate": "single_final_test_run_policy",
            "required_check": "After test execution, no method, threshold, lambda, feature, family, or wording changes may be made based on test results.",
            "blocks_if_fail": "invalid final benchmark",
            "current_status": "pending",
        },
    ]


def blocked_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "blocked_claim": "validation_table_as_benchmark_table",
            "reason": "User selected test set as benchmark table; validation result is downgraded.",
            "replacement": "Use validation as appendix/secondary analysis only.",
        },
        {
            "blocked_claim": "local_staged_relationships_test_is_independent_test",
            "reason": "Observed staged non-empty test JSON overlaps canonical validation scans; provenance must be verified.",
            "replacement": "Treat as blocked/candidate until test provenance and split disjointness pass.",
        },
        {
            "blocked_claim": "official_test_result_available_now",
            "reason": "No accepted independent H002 test benchmark protocol has been frozen or run.",
            "replacement": "Run test benchmark only after preflight, protocol freeze, and Docker materialization/audit.",
        },
    ]


def write_report(path: Path, summary: dict[str, Any], probe_rows: list[dict[str, Any]], gates: list[dict[str, Any]]) -> None:
    lines = [
        "# H002 Source Reranking Validation Table Review",
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
        "## Decision",
        "",
        "- Validation table is downgraded to appendix or secondary analysis.",
        "- Main benchmark table must use an independent test set or accepted official evaluation server.",
        "- Current local staged `relationships_test.json` files are not benchmark-ready until provenance and split-disjointness pass.",
        "",
        "## Local Test Probe",
        "",
        "| Candidate | Exists | Unique Scans | Relations | Validation Overlap | Benchmark Use |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in probe_rows:
        lines.append(
            f"| `{row['candidate']}` | {row['exists']} | {row['unique_scans']} | {row['relations']} | "
            f"{row['overlap_with_canonical_validation_scans']} | {row['benchmark_use']} |"
        )
    lines.extend(
        [
            "",
            "## Required Pre-Experiment Gates",
            "",
            "| Gate | Required Check | Current Status |",
            "| --- | --- | --- |",
        ]
    )
    for row in gates:
        lines.append(f"| `{row['gate']}` | {row['required_check']} | {row['current_status']} |")
    lines.extend(
        [
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    skeleton_summary = read_json(args.skeleton_dir / "summary.json")
    errors = validate_inputs(skeleton_summary, args.skeleton_dir)
    probe_rows = local_test_probe_rows()
    position_rows = validation_table_position_rows()
    gate_rows = preflight_gate_rows()
    blocked_rows = blocked_claim_rows()

    status = STATUS_ERRORS if errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "validation_table_review_blocked_by_input_errors",
        "validation_errors": len(errors),
        "input_artifacts": {
            "validation_table_skeleton": rel_path(args.skeleton_dir / "summary.json"),
            "primary_tradeoff_table": rel_path(args.skeleton_dir / "primary_tradeoff_table.csv"),
            "source_family_caveat_table": rel_path(args.skeleton_dir / "source_family_caveat_table.csv"),
        },
        "decision": {
            "validation_table_position": "appendix_or_secondary_analysis_only",
            "main_benchmark_table_requires_test": True,
            "validation_table_main_benchmark_allowed": False,
            "test_benchmark_ready_now": False,
            "test_benchmark_blocker": "test_label_provenance_and_split_disjointness_not_verified",
            "canonical_test_file_exists": CANONICAL_TEST.exists(),
            "staged_test_files_observed": sum(1 for row in probe_rows if row["candidate"] != "canonical_3dssg_subset_validation_reference" and row["exists"]),
            "final_paper_result_promotion": "not_yet",
        },
        "output_artifacts": {
            "artifact_root": rel_path(args.output_dir),
            "validation_table_position": rel_path(args.output_dir / "validation_table_position.csv"),
            "local_test_probe": rel_path(args.output_dir / "local_test_probe.csv"),
            "test_benchmark_preflight_gates": rel_path(args.output_dir / "test_benchmark_preflight_gates.csv"),
            "blocked_claims": rel_path(args.output_dir / "blocked_claims.csv"),
            "report": rel_path(args.output_dir / "report.md"),
        },
        "next_todo": NEXT_TODO if not errors else EXPECTED_SKELETON_NEXT,
    }

    write_json(args.output_dir / "summary.json", summary)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_csv(args.output_dir / "validation_table_position.csv", position_rows)
    write_csv(args.output_dir / "local_test_probe.csv", probe_rows)
    write_csv(args.output_dir / "test_benchmark_preflight_gates.csv", gate_rows)
    write_csv(args.output_dir / "blocked_claims.csv", blocked_rows)
    write_report(args.output_dir / "report.md", summary, probe_rows, gate_rows)

    print(json.dumps({"status": status, "validation_errors": len(errors), "next_todo": summary["next_todo"]}, ensure_ascii=False, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
