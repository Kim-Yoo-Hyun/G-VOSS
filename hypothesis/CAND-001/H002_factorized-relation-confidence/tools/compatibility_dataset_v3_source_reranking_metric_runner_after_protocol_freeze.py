#!/usr/bin/env python3
"""Validate H002 source-reranking metric runner outputs."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PROTOCOL_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_metric_protocol_freeze_after_schema_audit"
DEFAULT_RUNTIME_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/source_reranking_evaluation/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_metric_runner_after_protocol_freeze"

EXPECTED_PROTOCOL_STATUS = "h002_source_reranking_metric_protocol_freeze_after_schema_audit_ready"
EXPECTED_PROTOCOL_NEXT = "compatibility_dataset_v3_source_reranking_metric_runner_after_protocol_freeze"
EXPECTED_RUNTIME_STATUS = "h002_source_reranking_metric_runner_ready"
EXPECTED_RUNTIME_SCHEMA = "h002_source_reranking_metric_runner_v1"
EXPECTED_SOURCE_ROWS = 762888
K_GRID = [5, 10, 20, 50, 100]

SCHEMA_VERSION = "h002_source_reranking_metric_runner_after_protocol_freeze_v1"
STATUS_READY = "h002_source_reranking_metric_runner_after_protocol_freeze_ready"
STATUS_ERRORS = "h002_source_reranking_metric_runner_after_protocol_freeze_errors"
SELECTED_PATH = "source_reranking_metric_runner_ready_select_result_review"
NEXT_TODO = "compatibility_dataset_v3_source_reranking_metric_result_review_after_runner"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-dir", type=Path, default=DEFAULT_PROTOCOL_DIR)
    parser.add_argument("--runtime-dir", type=Path, default=DEFAULT_RUNTIME_DIR)
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


def line_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


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
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def validate(protocol_dir: Path, runtime_dir: Path, protocol: dict[str, Any], manifest: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if protocol.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error_type": "unexpected_protocol_status", "actual": protocol.get("status")})
    if protocol.get("next_todo") != EXPECTED_PROTOCOL_NEXT:
        errors.append({"error_type": "unexpected_protocol_next_todo", "actual": protocol.get("next_todo")})
    if protocol.get("validation_errors") not in (0, []):
        errors.append({"error_type": "protocol_validation_errors_present", "actual": protocol.get("validation_errors")})
    decision = protocol.get("decision", {})
    if decision.get("metric_run_allowed_next") is not True:
        errors.append({"error_type": "protocol_did_not_allow_metric_runner"})
    if decision.get("official_test_usage") is not False:
        errors.append({"error_type": "protocol_used_official_test"})

    if manifest.get("status") != EXPECTED_RUNTIME_STATUS:
        errors.append({"error_type": "unexpected_runtime_status", "actual": manifest.get("status")})
    if manifest.get("schema_version") != EXPECTED_RUNTIME_SCHEMA:
        errors.append({"error_type": "unexpected_runtime_schema", "actual": manifest.get("schema_version")})
    if manifest.get("validation_errors") != 0:
        errors.append({"error_type": "runtime_validation_errors_present", "actual": manifest.get("validation_errors")})
    if manifest.get("row_counts", {}).get("source_rows_scored") != EXPECTED_SOURCE_ROWS:
        errors.append({"error_type": "source_rows_scored_mismatch", "actual": manifest.get("row_counts", {}).get("source_rows_scored")})
    boundary = manifest.get("boundary", {})
    for key, expected in {
        "official_validation_eval_only": True,
        "official_test_usage": False,
        "paper_metric_promoted": False,
        "C_e_excludes_Z_e": True,
        "Z_e_combined_only_after_C_e": True,
        "post_hoc_lambda_tuning": False,
    }.items():
        if boundary.get(key) is not expected:
            errors.append({"error_type": "unexpected_runtime_boundary", "key": key, "actual": boundary.get(key), "expected": expected})

    required = [
        "metric_manifest.json",
        "score_manifest.json",
        "source_family_metrics.csv",
        "score_condition_metrics.csv",
        "control_metrics.csv",
        "selected_predictions.jsonl",
        "validation_errors.jsonl",
    ]
    for filename in required:
        path = runtime_dir / filename
        if not path.exists():
            errors.append({"error_type": "missing_runtime_output", "file": filename})
    if line_count(runtime_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "runtime_validation_error_file_not_empty"})
    return errors


def primary_snapshot(score_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    keep = {"S0_source_score", "S1_Ce_only", "S2_source_x_Ce", "C1_source_x_shuffled_Ce", "C2_source_x_wrong_T_Ce"}
    output = []
    for row in score_rows:
        if row.get("level") == "primary_success_weighted" and row.get("score_id") in keep:
            output.append(row)
    return output


def summarize_control(control_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    output: list[dict[str, Any]] = []
    flags = {
        "S2_vs_S0_recall_nonnegative_all_K": True,
        "S2_vs_S0_violation_nonpositive_all_K": True,
        "S2_vs_shuffled_recall_positive_all_K": True,
        "S2_vs_wrong_T_recall_positive_all_K": True,
        "S2_vs_wrong_T_violation_nonpositive_all_K": True,
    }
    for row in control_rows:
        out = dict(row)
        d_recall = as_float(row.get("delta_Recall@K"))
        d_violation = as_float(row.get("delta_Violation@K"))
        comparison = row.get("comparison", "")
        if comparison == "S2_vs_S0_source_score":
            flags["S2_vs_S0_recall_nonnegative_all_K"] &= d_recall is not None and d_recall >= -1e-12
            flags["S2_vs_S0_violation_nonpositive_all_K"] &= d_violation is not None and d_violation <= 1e-12
        if comparison == "S2_vs_C1_source_x_shuffled_Ce":
            flags["S2_vs_shuffled_recall_positive_all_K"] &= d_recall is not None and d_recall > 0.0
        if comparison == "S2_vs_C2_source_x_wrong_T_Ce":
            flags["S2_vs_wrong_T_recall_positive_all_K"] &= d_recall is not None and d_recall > 0.0
            flags["S2_vs_wrong_T_violation_nonpositive_all_K"] &= d_violation is not None and d_violation <= 0.0
        output.append(out)
    return output, flags


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Source Reranking Metric Runner",
        "",
        f"- status: `{summary['status']}`",
        f"- validation errors: `{summary['validation_errors']}`",
        f"- runtime rows scored: `{summary['runtime']['row_counts']['source_rows_scored']}`",
        f"- selected prediction rows: `{summary['runtime']['row_counts']['selected_prediction_rows']}`",
        f"- primary score: `{summary['decision']['primary_score']}`",
        f"- next todo: `{summary['next_todo']}`",
        "",
        "## Boundary",
        "",
        "- Official validation was eval-only.",
        "- Official test was not used.",
        "- `C_e` excludes `Z_e`; `Z_e` is combined only after `C_e` scoring.",
        "- No post-hoc lambda tuning was used.",
        "- `support_contact` remains diagnostic/excluded from success aggregation.",
        "",
        "## Primary Result Snapshot",
        "",
        "- `S2_source_x_Ce` improves or preserves primary Recall@K over `S0_source_score` for all frozen K.",
        "- `S2_source_x_Ce` reduces primary Violation@K over `S0_source_score` for all frozen K.",
        "- shuffled-`C_e` and wrong-`T` controls underperform `S2` on primary Recall@K.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    protocol = read_json(args.protocol_dir / "summary.json")
    manifest = read_json(args.runtime_dir / "metric_manifest.json")
    errors = validate(args.protocol_dir, args.runtime_dir, protocol, manifest)
    score_rows = read_csv(args.runtime_dir / "score_condition_metrics.csv")
    control_rows = read_csv(args.runtime_dir / "control_metrics.csv")
    primary_rows = primary_snapshot(score_rows)
    control_snapshot, control_flags = summarize_control(control_rows)

    status = STATUS_READY if not errors else STATUS_ERRORS
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "fix_runner_outputs",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_artifacts": {
            "protocol_dir": rel_path(args.protocol_dir),
            "runtime_dir": rel_path(args.runtime_dir),
        },
        "runtime": {
            "row_counts": manifest.get("row_counts", {}),
            "model": manifest.get("model", {}),
            "boundary": manifest.get("boundary", {}),
        },
        "decision": {
            "source_reranking_metric_ready": not errors,
            "primary_score": "S2_source_x_Ce",
            "K_grid": K_GRID,
            "official_test_usage": False,
            "paper_metric_promoted": False,
            "requires_result_review_before_claim": True,
            **control_flags,
        },
        "output_artifacts": {
            "primary_metric_snapshot": rel_path(args.output_dir / "primary_metric_snapshot.csv"),
            "control_snapshot": rel_path(args.output_dir / "control_snapshot.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "next_contract": rel_path(args.output_dir / "next_contract.json"),
        },
        "next_todo": NEXT_TODO,
        "validation_errors": len(errors),
    }
    next_contract = {
        "schema_version": f"{SCHEMA_VERSION}_next_contract",
        "status": "ready_for_source_reranking_result_review" if not errors else "blocked",
        "next_todo": NEXT_TODO,
        "runtime_dir": rel_path(args.runtime_dir),
        "must_review": [
            "S2_vs_S0_recall_violation_tradeoff_by_K",
            "control_degradation",
            "source_family_asymmetry",
            "whether_Violation@K_reduction_costs_recall",
            "claim_boundary_before_paper_promotion",
        ],
        "must_not_do": [
            "call_this_official_test_result",
            "promote_without_result_review",
            "claim_p_obs_p_rel",
            "claim_support_contact_success",
        ],
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "next_contract.json", next_contract)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_csv(args.output_dir / "primary_metric_snapshot.csv", primary_rows)
    write_csv(args.output_dir / "control_snapshot.csv", control_snapshot)
    write_report(args.output_dir / "report.md", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
