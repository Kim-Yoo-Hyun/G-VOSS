#!/usr/bin/env python3
"""Resolve H002 test-benchmark source availability after blocked preflight."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PREFLIGHT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_test_benchmark_preflight_after_validation_downgrade"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_test_benchmark_source_resolution_after_preflight"

EXPECTED_PREFLIGHT_STATUS = "h002_test_benchmark_preflight_after_validation_downgrade_ready_blocked"
EXPECTED_PREFLIGHT_NEXT = "compatibility_dataset_v3_test_benchmark_source_resolution_after_preflight"

SCHEMA_VERSION = "h002_test_benchmark_source_resolution_after_preflight_v1"
STATUS_READY_BLOCKED = "h002_test_benchmark_source_resolution_after_preflight_ready_blocked"
STATUS_ERRORS = "h002_test_benchmark_source_resolution_after_preflight_input_errors"
SELECTED_PATH = "official_eval_server_not_confirmed_keep_validation_appendix_request_external_provenance"
NEXT_TODO = "compatibility_dataset_v3_test_benchmark_external_provenance_request_after_source_resolution"

LOCAL_OPEN3DSG_README = REPO_ROOT / "local_dataset/Open3DSG_staged/h001_runtime/source/open3dsg_source/README.md"
LOCAL_OPEN3DSG_RUN = REPO_ROOT / "local_dataset/Open3DSG_staged/h001_runtime/source/open3dsg_source/open3dsg/scripts/run.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight-dir", type=Path, default=DEFAULT_PREFLIGHT_DIR)
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


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_inputs(preflight_summary: dict[str, Any], preflight_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if preflight_summary.get("status") != EXPECTED_PREFLIGHT_STATUS:
        errors.append({"error_type": "unexpected_preflight_status", "actual": preflight_summary.get("status")})
    if preflight_summary.get("next_todo") != EXPECTED_PREFLIGHT_NEXT:
        errors.append({"error_type": "unexpected_preflight_next_todo", "actual": preflight_summary.get("next_todo")})
    if preflight_summary.get("validation_errors") != 0:
        errors.append({"error_type": "preflight_validation_errors", "actual": preflight_summary.get("validation_errors")})
    if line_count(preflight_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "preflight_validation_errors_file_not_empty"})
    decision = preflight_summary.get("decision", {})
    expected_false = {
        "test_benchmark_ready": decision.get("test_benchmark_ready"),
        "experiments_test_run_allowed": decision.get("experiments_test_run_allowed"),
        "canonical_test_file_exists": decision.get("canonical_test_file_exists"),
    }
    for key, actual in expected_false.items():
        if actual is not False:
            errors.append({"error_type": "unexpected_preflight_decision", "key": key, "actual": actual, "expected": False})
    if decision.get("official_test_source_rows") != 0:
        errors.append({"error_type": "unexpected_official_test_source_rows", "actual": decision.get("official_test_source_rows")})
    if decision.get("validation_table_position") != "appendix_or_secondary_analysis_only":
        errors.append({"error_type": "validation_table_not_downgraded", "actual": decision.get("validation_table_position")})
    return errors


def official_source_evidence_rows() -> list[dict[str, Any]]:
    return [
        {
            "source_id": "3rscan_official_github",
            "url": "https://github.com/WaldJohannaU/3RScan",
            "checked_at_utc": "2026-07-02",
            "observed_fact": "3RScan official README exposes train, validation, and test split links for scan-level data.",
            "h002_interpretation": "A 3RScan scan-level test split exists, but this alone does not prove 3DSSG relation-label test GT availability.",
            "test_benchmark_status": "insufficient_alone",
        },
        {
            "source_id": "3dssg_official_project",
            "url": "https://3dssg.github.io/",
            "checked_at_utc": "2026-07-02",
            "observed_fact": "3DSSG project page describes the dataset and links the paper/data route; no public evaluation server was observed on the page.",
            "h002_interpretation": "Accepted official evaluation-server route is not confirmed from the official project page.",
            "test_benchmark_status": "not_confirmed",
        },
        {
            "source_id": "3dssg_official_github_pages_repo",
            "url": "https://github.com/3DSSG/3DSSG.github.io/",
            "checked_at_utc": "2026-07-02",
            "observed_fact": "The official 3DSSG data description lists object and relationship files in the downloadable package.",
            "h002_interpretation": "The checked official repo page does not by itself establish an independent relation test-label file or evaluation server.",
            "test_benchmark_status": "not_confirmed",
        },
        {
            "source_id": "shunchengwu_3dssg_repo",
            "url": "https://github.com/ShunChengWu/3DSSG",
            "checked_at_utc": "2026-07-02",
            "observed_fact": "The representative 3DSSG framework repo documents local setup, preparation, training, and evaluation scripts.",
            "h002_interpretation": "No accepted public official evaluation server was observed in the checked README.",
            "test_benchmark_status": "not_confirmed",
        },
        {
            "source_id": "open3dsg_official_repo",
            "url": "https://github.com/boschresearch/Open3DSG",
            "checked_at_utc": "2026-07-02",
            "observed_fact": "Open3DSG README states that 3DSSG provides pre-constructed scene graphs with GT labels for training and validation.",
            "h002_interpretation": "This supports keeping current H002 validation results as validation-level evidence, not as test benchmark evidence.",
            "test_benchmark_status": "validation_supported_test_unconfirmed",
        },
    ]


def local_source_evidence_rows(preflight_dir: Path) -> list[dict[str, Any]]:
    preflight_summary = read_json(preflight_dir / "summary.json")
    decision = preflight_summary.get("decision", {})
    gate_rows = load_csv(preflight_dir / "preflight_gate_status.csv")
    label_rows = load_csv(preflight_dir / "test_label_provenance_audit.csv")

    open3dsg_readme_text = LOCAL_OPEN3DSG_README.read_text(encoding="utf-8") if LOCAL_OPEN3DSG_README.exists() else ""
    open3dsg_run_text = LOCAL_OPEN3DSG_RUN.read_text(encoding="utf-8") if LOCAL_OPEN3DSG_RUN.exists() else ""
    return [
        {
            "source_id": "preflight_summary",
            "path": rel_path(preflight_dir / "summary.json"),
            "observed_fact": (
                f"canonical_test_file_exists={decision.get('canonical_test_file_exists')}; "
                f"validation_alias_candidates={decision.get('validation_alias_candidates')}; "
                f"official_test_source_rows={decision.get('official_test_source_rows')}; "
                f"official_validation_source_rows={decision.get('official_validation_source_rows')}"
            ),
            "h002_interpretation": "Local preflight blocks experiments-level test benchmark.",
            "test_benchmark_status": "blocked",
        },
        {
            "source_id": "preflight_gate_status",
            "path": rel_path(preflight_dir / "preflight_gate_status.csv"),
            "observed_fact": "; ".join(f"{row.get('gate')}={row.get('status')}" for row in gate_rows if row.get("gate") in {"test_label_provenance", "split_disjointness", "test_source_prediction_availability"}),
            "h002_interpretation": "The three source-readiness gates all fail.",
            "test_benchmark_status": "blocked",
        },
        {
            "source_id": "test_label_provenance_audit",
            "path": rel_path(preflight_dir / "test_label_provenance_audit.csv"),
            "observed_fact": f"rows={len(label_rows)}; blocked rows include missing canonical test and validation-alias staged candidates.",
            "h002_interpretation": "No local relationships_test candidate is benchmark-usable without external provenance.",
            "test_benchmark_status": "blocked",
        },
        {
            "source_id": "local_open3dsg_readme",
            "path": rel_path(LOCAL_OPEN3DSG_README),
            "observed_fact": "contains_3dssg_gt_train_validation_statement=" + str("ground-truth labels for training and validation" in open3dsg_readme_text),
            "h002_interpretation": "Local checked Open3DSG documentation supports train/validation GT availability, not independent test GT promotion.",
            "test_benchmark_status": "validation_supported_test_unconfirmed",
        },
        {
            "source_id": "local_open3dsg_run_py",
            "path": rel_path(LOCAL_OPEN3DSG_RUN),
            "observed_fact": "contains_unlabeled_3rscan_test_comment=" + str("not labeled in 3dssg" in open3dsg_run_text.lower()),
            "h002_interpretation": "`test_scans_3rscan` is not sufficient as 3DSSG relation-GT benchmark evidence.",
            "test_benchmark_status": "blocks_relation_gt_assumption",
        },
    ]


def resolution_rows() -> list[dict[str, Any]]:
    return [
        {
            "route": "accepted_official_evaluation_server",
            "status": "not_confirmed",
            "can_run_experiment_now": "false",
            "reason": "Checked official project/repo sources did not expose an accepted public 3DSSG relation evaluation server.",
            "next_action": "Prepare external provenance/contact request before any benchmark claim.",
        },
        {
            "route": "independent_relationships_test_json",
            "status": "not_available_locally",
            "can_run_experiment_now": "false",
            "reason": "Canonical local test file is missing; staged non-empty candidates overlap validation scans.",
            "next_action": "Require official provenance and split-disjointness proof before use.",
        },
        {
            "route": "3rscan_scan_level_test_split",
            "status": "exists_but_insufficient",
            "can_run_experiment_now": "false",
            "reason": "Scan-level test split exists, but H002 needs 3DSSG relation labels/source predictions on exact test candidates.",
            "next_action": "Do not equate scan split existence with relation benchmark readiness.",
        },
        {
            "route": "validation_only_appendix",
            "status": "selected_until_test_source_resolves",
            "can_run_experiment_now": "false_for_test_benchmark",
            "reason": "Validation source-reranking evidence is already claim-locked as appendix/secondary analysis.",
            "next_action": "Keep validation table downgraded and block final benchmark wording.",
        },
    ]


def blocked_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "blocked_claim": "H002 source-reranking benchmark result on official test",
            "reason": "No accepted official evaluation server or independent relation test-label provenance is confirmed.",
        },
        {
            "blocked_claim": "local staged relationships_test.json is independent test",
            "reason": "Non-empty staged candidates overlap validation scans; local source-resolution did not clear provenance.",
        },
        {
            "blocked_claim": "3RScan test split implies 3DSSG relation test GT",
            "reason": "3RScan scan-level split existence is not equivalent to relation-label GT availability.",
        },
        {
            "blocked_claim": "validation table is main benchmark table",
            "reason": "User decision and source resolution keep validation evidence as appendix/secondary analysis only.",
        },
        {
            "blocked_claim": "final paper promotion or SOTA/full-3DSSG source claim",
            "reason": "Current source-reranking result remains validation-level and test benchmark is blocked.",
        },
    ]


def report_text(summary: dict[str, Any]) -> str:
    decision = summary["decision"]
    return "\n".join(
        [
            "# H002 Test Benchmark Source Resolution After Preflight",
            "",
            "## Purpose",
            "",
            "Resolve whether H002 can move from validation-level source-reranking evidence to a test benchmark table.",
            "",
            "## Decision",
            "",
            f"- status: `{summary['status']}`",
            f"- selected path: `{summary['selected_path']}`",
            f"- next todo: `{summary['next_todo']}`",
            f"- accepted official evaluation server confirmed: `{str(decision['accepted_official_eval_server_confirmed']).lower()}`",
            f"- independent relation test label confirmed: `{str(decision['independent_relation_test_label_confirmed']).lower()}`",
            f"- scan-level 3RScan test split exists: `{str(decision['scan_level_3rscan_test_split_exists']).lower()}`",
            f"- relation-test source predictions available: `{str(decision['relation_test_source_predictions_available']).lower()}`",
            f"- experiments test run allowed: `{str(decision['experiments_test_run_allowed']).lower()}`",
            "",
            "## Interpretation",
            "",
            "A 3RScan scan-level test split exists, but H002 needs relation-label GT and source predictions on the exact test candidate pool. "
            "The checked official pages and local Open3DSG code do not clear that requirement. Current source-reranking results therefore remain "
            "appendix/secondary validation evidence.",
            "",
            "## Next",
            "",
            "Prepare an external provenance/contact request or obtain an official evaluation-server route. Do not run the test benchmark metric runner yet.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    preflight_summary_path = args.preflight_dir / "summary.json"
    if not preflight_summary_path.exists():
        raise FileNotFoundError(f"Missing preflight summary: {preflight_summary_path}")

    preflight_summary = read_json(preflight_summary_path)
    validation_errors = validate_inputs(preflight_summary, args.preflight_dir)

    status = STATUS_ERRORS if validation_errors else STATUS_READY_BLOCKED
    decision = {
        "accepted_official_eval_server_confirmed": False,
        "independent_relation_test_label_confirmed": False,
        "scan_level_3rscan_test_split_exists": True,
        "scan_level_split_is_sufficient_for_h002": False,
        "local_staged_test_candidates_usable": False,
        "relation_test_source_predictions_available": False,
        "validation_table_position": "appendix_or_secondary_analysis_only",
        "experiments_test_run_allowed": False,
        "final_paper_benchmark_allowed": False,
        "source_resolution_blocker": "official_eval_server_or_independent_relation_test_provenance_not_confirmed",
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH,
        "validation_errors": len(validation_errors),
        "decision": decision,
        "input_artifacts": {
            "preflight_summary": rel_path(preflight_summary_path),
            "preflight_gate_status": rel_path(args.preflight_dir / "preflight_gate_status.csv"),
            "test_label_provenance_audit": rel_path(args.preflight_dir / "test_label_provenance_audit.csv"),
        },
        "output_artifacts": {
            "artifact_root": rel_path(args.output_dir),
            "official_source_evidence": rel_path(args.output_dir / "official_source_evidence.csv"),
            "local_source_evidence": rel_path(args.output_dir / "local_source_evidence.csv"),
            "resolution_options": rel_path(args.output_dir / "resolution_options.csv"),
            "blocked_claims": rel_path(args.output_dir / "blocked_claims.csv"),
            "next_contract": rel_path(args.output_dir / "next_contract.json"),
            "report": rel_path(args.output_dir / "report.md"),
        },
        "next_todo": NEXT_TODO,
    }

    next_contract = {
        "next_todo": NEXT_TODO,
        "required_before_test_benchmark": [
            "official evaluation server route with accepted submission/eval protocol, or independent 3DSSG relation test-label file",
            "split-disjointness proof for scan/object-pair/candidate ids",
            "VL-SAT/Open3DSG source predictions on the exact test candidate pool",
            "frozen C_e scorer, feature schema, source score normalization, K grid, and single final test run policy",
        ],
        "do_not_do": [
            "do not run test benchmark metric runner",
            "do not use validation-alias staged relationships_test.json as test",
            "do not promote validation table as benchmark table",
            "do not tune normalization or wording on test results",
        ],
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "summary.json", summary)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "official_source_evidence.csv", official_source_evidence_rows())
    write_csv(args.output_dir / "local_source_evidence.csv", local_source_evidence_rows(args.preflight_dir))
    write_csv(args.output_dir / "resolution_options.csv", resolution_rows())
    write_csv(args.output_dir / "blocked_claims.csv", blocked_claim_rows())
    write_json(args.output_dir / "next_contract.json", next_contract)
    (args.output_dir / "report.md").write_text(report_text(summary), encoding="utf-8")

    print(json.dumps({"status": status, "validation_errors": len(validation_errors), "next_todo": NEXT_TODO}, ensure_ascii=False, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
