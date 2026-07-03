#!/usr/bin/env python3
"""Freeze H002 source-reranking metric protocol after schema audit."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SCHEMA_STAGE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_source_reranking_materialization_schema_audit_after_docker_materialization"
)
DEFAULT_RUNTIME_AUDIT_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/source_reranking_schema_audit/latest"
DEFAULT_MATERIALIZATION_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/source_reranking_materialization/latest"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_metric_protocol_freeze_after_schema_audit"
)

EXPECTED_SCHEMA_STATUS = "h002_source_reranking_materialization_schema_audit_after_docker_materialization_ready"
EXPECTED_SCHEMA_NEXT = "compatibility_dataset_v3_source_reranking_metric_protocol_freeze_after_schema_audit"
EXPECTED_RUNTIME_STATUS = "h002_source_reranking_materialization_schema_audit_ready"
EXPECTED_ROWS = 762888
EXPECTED_PRIMARY_ROWS = 254296

SCHEMA_VERSION = "h002_source_reranking_metric_protocol_freeze_after_schema_audit_v1"
STATUS_READY = "h002_source_reranking_metric_protocol_freeze_after_schema_audit_ready"
STATUS_ERRORS = "h002_source_reranking_metric_protocol_freeze_after_schema_audit_errors"
SELECTED_PATH = "source_reranking_metric_protocol_frozen_select_metric_runner"
NEXT_TODO = "compatibility_dataset_v3_source_reranking_metric_runner_after_protocol_freeze"
K_GRID = [5, 10, 20, 50, 100]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema-stage-dir", type=Path, default=DEFAULT_SCHEMA_STAGE_DIR)
    parser.add_argument("--runtime-audit-dir", type=Path, default=DEFAULT_RUNTIME_AUDIT_DIR)
    parser.add_argument("--materialization-dir", type=Path, default=DEFAULT_MATERIALIZATION_DIR)
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


def validate_inputs(schema_stage_dir: Path, runtime_audit_dir: Path, materialization_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    schema_summary = read_json(schema_stage_dir / "summary.json")
    runtime_audit = read_json(runtime_audit_dir / "audit_manifest.json")
    materialization = read_json(materialization_dir / "row_manifest.json")

    if schema_summary.get("status") != EXPECTED_SCHEMA_STATUS:
        errors.append({"error_type": "unexpected_schema_stage_status", "actual": schema_summary.get("status")})
    if schema_summary.get("next_todo") != EXPECTED_SCHEMA_NEXT:
        errors.append({"error_type": "unexpected_schema_stage_next_todo", "actual": schema_summary.get("next_todo")})
    if schema_summary.get("validation_errors") != 0:
        errors.append({"error_type": "schema_stage_validation_errors", "actual": schema_summary.get("validation_errors")})
    if schema_summary.get("decision", {}).get("ready_for_metric_protocol_freeze") is not True:
        errors.append({"error_type": "schema_stage_not_ready_for_metric_protocol_freeze"})
    if schema_summary.get("decision", {}).get("metric_run_allowed_now") is not False:
        errors.append({"error_type": "metric_run_allowed_before_protocol_freeze"})

    if runtime_audit.get("status") != EXPECTED_RUNTIME_STATUS:
        errors.append({"error_type": "unexpected_runtime_audit_status", "actual": runtime_audit.get("status")})
    if runtime_audit.get("validation_errors") != 0:
        errors.append({"error_type": "runtime_audit_validation_errors", "actual": runtime_audit.get("validation_errors")})
    if runtime_audit.get("next_todo") != EXPECTED_SCHEMA_NEXT:
        errors.append({"error_type": "unexpected_runtime_audit_next_todo", "actual": runtime_audit.get("next_todo")})
    for filename in ["validation_errors.jsonl", "blocked_field_hits.jsonl"]:
        count = line_count(runtime_audit_dir / filename)
        if count != 0:
            errors.append({"error_type": "non_empty_runtime_audit_file", "file": filename, "rows": count})

    row_counts = materialization.get("row_counts", {})
    if row_counts.get("total_rows") != EXPECTED_ROWS:
        errors.append({"error_type": "materialization_total_rows_mismatch", "actual": row_counts.get("total_rows")})
    if row_counts.get("primary_success_family_rows") != EXPECTED_PRIMARY_ROWS:
        errors.append({"error_type": "materialization_primary_rows_mismatch", "actual": row_counts.get("primary_success_family_rows")})
    for key in ["source_reranking_metrics_run", "official_test_usage", "paper_metric_produced", "paper_metric_promoted"]:
        if materialization.get(key) is not False:
            errors.append({"error_type": "unexpected_materialization_boundary", "key": key, "actual": materialization.get(key)})

    primary_rows = {
        row.get("family"): int(row.get("rows", 0))
        for row in read_csv(runtime_audit_dir / "family_success_aggregation.csv")
        if row.get("include_in_success_aggregation") == "True" and row.get("family") != "PRIMARY_MACRO"
    }
    if primary_rows != {"relative_vertical": 127148, "size_relative": 127148}:
        errors.append({"error_type": "unexpected_primary_success_aggregation", "actual": primary_rows})
    for row in read_csv(runtime_audit_dir / "control_readiness.csv"):
        if row.get("success_metric_role") == "primary":
            if row.get("wrong_T_control_ready") != "True" or row.get("shuffled_G_control_ready") != "True":
                errors.append({"error_type": "primary_controls_not_ready", "row": row})
    return errors


def score_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "score_id": "S0_source_score",
            "role": "source_baseline",
            "definition": "source_rank_view.Z_e.ranking_score",
            "uses_Ce": False,
            "uses_Ze": True,
            "normalization": "per_source_minmax_on_official_validation_source_rows_before_ranking",
            "allowed_for_main": True,
            "notes": "baseline source ranking; does not test H002 C_e",
        },
        {
            "score_id": "S1_Ce_only",
            "role": "diagnostic_compatibility_ranking",
            "definition": "C_e_score(model_safe_ce_view.T_e, model_safe_ce_view.G_e)",
            "uses_Ce": True,
            "uses_Ze": False,
            "normalization": "per_source_family_minmax_after_Ce_scoring",
            "allowed_for_main": False,
            "notes": "diagnostic only; source utility is ignored",
        },
        {
            "score_id": "S2_source_x_Ce",
            "role": "primary_bridge_candidate",
            "definition": "norm_source_score * norm_Ce_score",
            "uses_Ce": True,
            "uses_Ze": True,
            "normalization": "S0 per-source minmax; C_e per-source-family minmax; multiply after clipping to [1e-6,1]",
            "allowed_for_main": True,
            "notes": "Z_e is combined only after C_e scoring; Z_e is not inside C_e",
        },
        {
            "score_id": "S3_log_source_plus_Ce",
            "role": "pre_frozen_ablation",
            "definition": "log(clip(norm_source_score)) + lambda * log(clip(norm_Ce_score))",
            "uses_Ce": True,
            "uses_Ze": True,
            "normalization": "same as S2; lambda fixed to 1.0 for this protocol",
            "allowed_for_main": False,
            "notes": "ablation only; no lambda tuning on validation metrics",
        },
        {
            "score_id": "C1_source_x_shuffled_Ce",
            "role": "negative_control",
            "definition": "norm_source_score * shuffled_within_family_Ce_score",
            "uses_Ce": True,
            "uses_Ze": True,
            "normalization": "same as S2",
            "allowed_for_main": False,
            "notes": "must underperform real S2 if C_e is meaningful",
        },
        {
            "score_id": "C2_source_x_wrong_T_Ce",
            "role": "negative_control",
            "definition": "norm_source_score * wrong_T_within_route_Ce_score",
            "uses_Ce": True,
            "uses_Ze": True,
            "normalization": "same as S2",
            "allowed_for_main": False,
            "notes": "must underperform real S2 on primary families",
        },
    ]


def metric_protocol_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for metric in ["Recall@K", "Violation@K", "Selected@K"]:
        for k in K_GRID:
            rows.append(
                {
                    "metric": metric,
                    "K": k,
                    "unit": "source_id + subgraph_id + route_family",
                    "ranking_scope": "within each source/subgraph/family over materialized source prediction rows",
                    "aggregation": "per_source_per_family_then_macro_over_primary_success_families",
                    "official_validation_use": "eval_only",
                    "official_test_use": "forbidden",
                }
            )
    return rows


def recall_protocol_rows() -> list[dict[str, Any]]:
    return [
        {
            "target": "exact_GT_match",
            "positive_field": "hidden_metric_manifest.gt_exact_match",
            "denominator": "unique GT relation keys present in hidden manifest per source/family/subgraph",
            "dedup_policy": "deduplicate selected predictions by scan_id, subject_id, object_id, predicate_label",
            "partial_match": "not_used_in_primary",
            "family_match": "diagnostic_only",
            "note": "Reviewer-facing Recall@K uses exact predicate match, not family-only match.",
        }
    ]


def violation_protocol_rows() -> list[dict[str, Any]]:
    return [
        {
            "family": "relative_vertical",
            "violation_source": "hidden_metric_manifest.h2_relation_status",
            "violation_rule": "status == violated",
            "include_in_primary": True,
            "notes": "H002 signed z-order relation status; H001 p_geom_valid stays hidden/control.",
        },
        {
            "family": "size_relative",
            "violation_source": "hidden_metric_manifest.h2_relation_status",
            "violation_rule": "status == violated",
            "include_in_primary": True,
            "notes": "H002 signed volume/size relation status.",
        },
        {
            "family": "relative_horizontal",
            "violation_source": "hidden_metric_manifest.h2_relation_status",
            "violation_rule": "status == violated",
            "include_in_primary": False,
            "notes": "Caveated frame-aware separate table only.",
        },
        {
            "family": "proximity",
            "violation_source": "hidden_metric_manifest.h2_relation_status or H001 p_geom_valid diagnostic",
            "violation_rule": "status == violated",
            "include_in_primary": False,
            "notes": "Geometry-only control; not T_e x G_e interaction evidence.",
        },
        {
            "family": "support_contact",
            "violation_source": "hidden_metric_manifest.h001_verification_status diagnostic only",
            "violation_rule": "not used in success aggregation",
            "include_in_primary": False,
            "notes": "Diagnostic failure taxonomy; do not claim solved support/contact.",
        },
    ]


def family_aggregation_rows() -> list[dict[str, Any]]:
    return [
        {"family": "relative_vertical", "role": "primary_success", "rows": 127148, "include_in_primary_macro": True, "table": "main"},
        {"family": "size_relative", "role": "primary_success", "rows": 127148, "include_in_primary_macro": True, "table": "main"},
        {"family": "relative_horizontal", "role": "caveated_frame_aware", "rows": 254296, "include_in_primary_macro": False, "table": "caveated"},
        {"family": "proximity", "role": "geometry_only_control", "rows": 63574, "include_in_primary_macro": False, "table": "control"},
        {"family": "support_contact", "role": "diagnostic_failure_taxonomy", "rows": 190722, "include_in_primary_macro": False, "table": "diagnostic"},
        {"family": "PRIMARY_MACRO", "role": "macro_over_relative_vertical_and_size_relative", "rows": 254296, "include_in_primary_macro": True, "table": "main"},
    ]


def normalization_rows() -> list[dict[str, Any]]:
    return [
        {
            "item": "source_score",
            "policy": "per-source min-max on official validation source rows",
            "tuning": "none",
            "reason": "VL-SAT and Open3DSG score ranges are not directly comparable.",
        },
        {
            "item": "C_e_score",
            "policy": "per-source-family min-max after scorer application",
            "tuning": "none",
            "reason": "family-specific C_e distribution can differ by source and route.",
        },
        {
            "item": "lambda",
            "policy": "fixed lambda=1.0 only for S3 ablation",
            "tuning": "forbidden_on_official_validation",
            "reason": "avoid post-hoc validation tuning.",
        },
        {
            "item": "tie_break",
            "policy": "stable by source score, then prediction_id",
            "tuning": "none",
            "reason": "deterministic ranking.",
        },
    ]


def control_protocol_rows() -> list[dict[str, Any]]:
    return [
        {"control": "wrong_T_within_route", "families": "relative_vertical,size_relative,relative_horizontal,support_contact", "required_for_primary": True, "expected": "degrade_vs_S2"},
        {"control": "shuffled_G_within_family", "families": "all", "required_for_primary": True, "expected": "degrade_vs_S2"},
        {"control": "shuffled_Ce_within_source_family", "families": "all", "required_for_primary": True, "expected": "degrade_vs_S2"},
        {"control": "source_score_only", "families": "all", "required_for_primary": True, "expected": "S2_should_improve_or_tradeoff_vs_S0"},
        {"control": "support_contact_exclusion", "families": "support_contact", "required_for_primary": True, "expected": "excluded_from_success_aggregation"},
        {"control": "official_test_guard", "families": "all", "required_for_primary": True, "expected": "official_test_unused"},
    ]


def runner_contract(materialization_dir: Path, output_dir: Path) -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_VERSION}_runner_contract",
        "next_runner": "source_reranking_metric_runner_after_protocol_freeze",
        "materialization_dir": rel_path(materialization_dir),
        "protocol_dir": rel_path(output_dir),
        "expected_runtime_output_dir": "experiments/H002_compatibility_routing/source_reranking_evaluation/latest",
        "required_inputs": [
            "model_safe_ce_view.jsonl",
            "source_rank_view.jsonl",
            "hidden_metric_manifest.jsonl",
            "model_safe_geometry_only_view.jsonl",
        ],
        "required_outputs": [
            "metric_manifest.json",
            "score_manifest.json",
            "source_family_metrics.csv",
            "score_condition_metrics.csv",
            "control_metrics.csv",
            "selected_predictions.jsonl",
            "validation_errors.jsonl",
        ],
        "blocked_actions": [
            "official_test_use",
            "post_hoc_lambda_tuning",
            "support_contact_success_promotion",
            "put_Ze_inside_Ce",
        ],
    }


def make_report(summary: dict[str, Any]) -> str:
    return f"""# Source Reranking Metric Protocol Freeze

## Status

```text
status = {summary["status"]}
selected_path = {summary["selected_path"]}
validation_errors = {summary["validation_errors"]}
next_todo = {summary["next_todo"]}
```

## Result

The source-reranking metric protocol is frozen. This stage did not run
`Recall@K`, `Violation@K`, or official test.

Primary score: `S2_source_x_Ce = normalized_source_score * normalized_Ce_score`.

Primary success families: `relative_vertical`, `size_relative`.
"""


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    errors = validate_inputs(args.schema_stage_dir, args.runtime_audit_dir, args.materialization_dir)
    status = STATUS_READY if not errors else STATUS_ERRORS
    selected_path = SELECTED_PATH if not errors else "blocked_fix_source_reranking_metric_protocol_inputs"

    outputs = {
        "summary": output_dir / "summary.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
        "score_contract": output_dir / "score_contract.csv",
        "metric_protocol": output_dir / "metric_protocol.csv",
        "recall_protocol": output_dir / "recall_protocol.csv",
        "violation_protocol": output_dir / "violation_protocol.csv",
        "family_aggregation": output_dir / "family_aggregation.csv",
        "normalization_policy": output_dir / "normalization_policy.csv",
        "control_protocol": output_dir / "control_protocol.csv",
        "runner_input_contract": output_dir / "runner_input_contract.json",
        "next_contract": output_dir / "next_contract.json",
        "report": output_dir / "report.md",
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(errors),
        "next_todo": NEXT_TODO,
        "input_artifacts": {
            "schema_stage_summary": rel_path(args.schema_stage_dir / "summary.json"),
            "runtime_audit_manifest": rel_path(args.runtime_audit_dir / "audit_manifest.json"),
            "materialization_manifest": rel_path(args.materialization_dir / "row_manifest.json"),
        },
        "output_artifacts": {name: rel_path(path) for name, path in outputs.items()},
        "decision": {
            "metric_protocol_frozen": not errors,
            "metric_run_allowed_next": not errors,
            "metrics_run_in_this_stage": False,
            "official_test_usage": False,
            "primary_score": "S2_source_x_Ce",
            "K_grid": K_GRID,
            "primary_success_families": ["relative_vertical", "size_relative"],
            "support_contact_success_aggregation": "excluded_diagnostic",
            "C_e_excludes_Z_e": True,
            "no_post_hoc_lambda_tuning": True,
        },
    }
    next_contract = {
        "schema_version": f"{SCHEMA_VERSION}_next_contract",
        "status": "ready_for_source_reranking_metric_runner" if not errors else "blocked",
        "next_todo": NEXT_TODO,
        "protocol_dir": rel_path(output_dir),
        "runtime_output_dir": "experiments/H002_compatibility_routing/source_reranking_evaluation/latest",
        "must_run_next": [
            "apply_Ce_scorer_to_source_wide_model_safe_view",
            "compute_S0_S1_S2_and_controls",
            "compute_Recall@K_and_Violation@K",
            "write_family_and_score_condition_tables",
        ],
        "must_not_do": [
            "use_official_test",
            "tune_lambda_on_validation_results",
            "include_support_contact_in_success_aggregation",
            "claim_p_obs_p_rel",
        ],
    }

    write_json(outputs["summary"], summary)
    write_jsonl(outputs["validation_errors"], errors)
    write_csv(outputs["score_contract"], score_contract_rows())
    write_csv(outputs["metric_protocol"], metric_protocol_rows())
    write_csv(outputs["recall_protocol"], recall_protocol_rows())
    write_csv(outputs["violation_protocol"], violation_protocol_rows())
    write_csv(outputs["family_aggregation"], family_aggregation_rows())
    write_csv(outputs["normalization_policy"], normalization_rows())
    write_csv(outputs["control_protocol"], control_protocol_rows())
    write_json(outputs["runner_input_contract"], runner_contract(args.materialization_dir, output_dir))
    write_json(outputs["next_contract"], next_contract)
    outputs["report"].write_text(make_report(summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
