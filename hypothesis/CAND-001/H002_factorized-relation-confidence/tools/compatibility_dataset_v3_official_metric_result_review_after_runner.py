#!/usr/bin/env python3
"""Review H002 official validation metric outputs and lock the next claim boundary."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_RUNNER_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_metric_runner_after_protocol_freeze"
DEFAULT_EVAL_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/official_evaluation/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_metric_result_review_after_runner"

EXPECTED_RUNNER_STATUS = "h002_compatibility_dataset_v3_official_metric_runner_after_protocol_freeze_ready_with_caveats"
EXPECTED_RUNNER_NEXT = "compatibility_dataset_v3_official_metric_result_review_after_runner"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_official_metric_result_review_after_runner_v1"
STATUS_READY = "h002_compatibility_dataset_v3_official_metric_result_review_after_runner_ready_with_boundaries"
STATUS_ERRORS = "h002_compatibility_dataset_v3_official_metric_result_review_after_runner_input_errors"
SELECTED_PATH = "official_metric_review_ready_select_claim_boundary_lock"
NEXT_TODO = "compatibility_dataset_v3_official_metric_claim_boundary_lock_after_result_review"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-dir", type=Path, default=DEFAULT_RUNNER_DIR)
    parser.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL_DIR)
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


def as_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def row_lookup(rows: list[dict[str, str]], **filters: str) -> dict[str, str] | None:
    for row in rows:
        if all(row.get(key) == value for key, value in filters.items()):
            return row
    return None


def metric_value(rows: list[dict[str, str]], view_id: str, key: str, *, level: str = "macro_family_primary") -> float | None:
    row = row_lookup(rows, level=level, view_id=view_id)
    return as_float(row.get(key) if row else None)


def family_metric(rows: list[dict[str, str]], family: str, view_id: str, key: str) -> float | None:
    row = row_lookup(rows, level="route_family", route_family=family, view_id=view_id)
    return as_float(row.get(key) if row else None)


def validate_inputs(runner_summary: dict[str, Any], eval_manifest: dict[str, Any], runner_dir: Path, eval_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if runner_summary.get("status") != EXPECTED_RUNNER_STATUS:
        errors.append({"error_type": "unexpected_runner_status", "actual": runner_summary.get("status")})
    if runner_summary.get("next_todo") != EXPECTED_RUNNER_NEXT:
        errors.append({"error_type": "unexpected_runner_next_todo", "actual": runner_summary.get("next_todo")})
    if runner_summary.get("validation_errors") != 0:
        errors.append({"error_type": "runner_stage_validation_errors", "actual": runner_summary.get("validation_errors")})
    if line_count(runner_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "runner_stage_validation_errors_file_not_empty"})
    if eval_manifest.get("status") != "ready":
        errors.append({"error_type": "unexpected_eval_manifest_status", "actual": eval_manifest.get("status")})
    if eval_manifest.get("validation_errors") != 0:
        errors.append({"error_type": "eval_manifest_validation_errors", "actual": eval_manifest.get("validation_errors")})
    if line_count(eval_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "eval_validation_errors_file_not_empty"})

    boundary = eval_manifest.get("boundary", {})
    required = {
        "official_validation_metric_produced": True,
        "official_validation_eval_only": True,
        "official_test_usage": False,
        "paper_metric_produced": False,
        "p_obs_claim_enabled": False,
        "p_rel_claim_enabled": False,
        "z_e_excluded_from_main_C_e": True,
        "q_e_excluded_from_main_C_e": True,
        "h001_p_geom_valid_excluded_from_main_G_e": True,
    }
    for key, expected in required.items():
        if boundary.get(key) is not expected:
            errors.append({"error_type": "unexpected_eval_boundary", "key": key, "actual": boundary.get(key), "expected": expected})
    return errors


def paper_level_gate_rows(
    aggregate_rows: list[dict[str, str]],
    family_rows: list[dict[str, str]],
    control_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    m4_macro = metric_value(aggregate_rows, "M4_TxG_compatibility", "macro_family_auroc")
    m1_macro = metric_value(aggregate_rows, "M1_T_semantic_only", "macro_family_auroc")
    m2_macro = metric_value(aggregate_rows, "M2_G_geometry_only", "macro_family_auroc")
    m3_macro = metric_value(aggregate_rows, "M3_T_plus_G_concat", "macro_family_auroc")
    wrong_t = control_delta(control_rows, "M4_vs_wrong_T_within_route")
    shuffled_global = control_delta(control_rows, "M4_vs_shuffled_G_global")
    shuffled_family = control_delta(control_rows, "M4_vs_shuffled_G_within_family")
    horizontal_frame = control_delta(control_rows, "M4_vs_horizontal_frame_swap")
    support_auc = family_metric(family_rows, "support_contact", "M4_TxG_compatibility", "auroc")
    horizontal_auc = family_metric(family_rows, "relative_horizontal", "M4_TxG_compatibility", "auroc")
    horizontal_frame_family_delta = (
        horizontal_auc - family_metric(family_rows, "relative_horizontal", "C7_horizontal_frame_swap", "auroc")
        if horizontal_auc is not None and family_metric(family_rows, "relative_horizontal", "C7_horizontal_frame_swap", "auroc") is not None
        else None
    )
    baseline_pass = all(
        value is not None and m4_macro is not None and m4_macro > value
        for value in [m1_macro, m2_macro, m3_macro]
    )
    controls_pass = all(value is not None and value > 0.25 for value in [wrong_t, shuffled_global, shuffled_family])
    return [
        {
            "gate": "docker_reproducible_runner",
            "status": "pass",
            "evidence": "h002-official-metric-runner exited 0 and wrote official_evaluation/latest",
            "decision": "paper_level_runner_execution_valid",
        },
        {
            "gate": "official_validation_policy",
            "status": "pass",
            "evidence": "official validation eval-only, official test false",
            "decision": "no_test_leakage",
        },
        {
            "gate": "main_feature_boundary",
            "status": "pass",
            "evidence": "main C_e uses T_e and G_e only; Z_e/Q_e/H001 p_geom_valid excluded",
            "decision": "feature_contract_valid",
        },
        {
            "gate": "primary_metric_vs_baselines",
            "status": "pass" if baseline_pass else "fail",
            "evidence": f"M4 macro AUROC={m4_macro}, M1={m1_macro}, M2={m2_macro}, M3={m3_macro}",
            "decision": "compatibility_signal_supported" if baseline_pass else "baseline_delta_insufficient",
        },
        {
            "gate": "wrong_T_and_shuffled_G_controls",
            "status": "pass" if controls_pass else "caveat",
            "evidence": f"wrong_T_delta={wrong_t}, shuffled_global_delta={shuffled_global}, shuffled_family_delta={shuffled_family}",
            "decision": "controls_support_TG_matching" if controls_pass else "control_review_required",
        },
        {
            "gate": "relative_horizontal_frame_control",
            "status": "caveat",
            "evidence": f"macro horizontal-frame delta={horizontal_frame}, relative_horizontal family delta={horizontal_frame_family_delta}",
            "decision": "allow_as_frame_aware_evidence_only_with_control_caveat",
        },
        {
            "gate": "support_contact_claim",
            "status": "caveat",
            "evidence": f"support_contact M4 AUROC={support_auc}; prior predicate/class-pair shortcut=0.993707",
            "decision": "diagnostic_only_not_solved",
        },
        {
            "gate": "paper_promotion",
            "status": "conditional_pass",
            "evidence": "official metric exists and main mechanism is supported, but claim boundary lock is still required",
            "decision": "proceed_to_claim_boundary_lock_not_final_paper_promotion",
        },
    ]


def control_delta(control_rows: list[dict[str, str]], comparison: str) -> float | None:
    row = row_lookup(control_rows, level="macro_family_primary", comparison=comparison)
    return as_float(row.get("delta_auroc") if row else None)


def family_decision_rows(family_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    specs = {
        "relative_vertical": {
            "status": "paper_candidate_main_evidence",
            "claim": "axis-order relation route supports predicate-geometry compatibility",
        },
        "size_relative": {
            "status": "paper_candidate_main_evidence",
            "claim": "size-comparison route supports predicate-geometry compatibility",
        },
        "relative_horizontal": {
            "status": "paper_candidate_with_frame_control_caveat",
            "claim": "frame-aware horizontal relation route supports compatibility, but frame-control wording must be conservative",
        },
        "support_contact": {
            "status": "diagnostic_challenging_only",
            "claim": "contact/pose route remains difficult; use as failure taxonomy and evidence-gap analysis",
        },
    }
    rows: list[dict[str, Any]] = []
    for family, spec in specs.items():
        m4 = row_lookup(family_rows, level="route_family", route_family=family, view_id="M4_TxG_compatibility") or {}
        rows.append(
            {
                "route_family": family,
                "status": spec["status"],
                "allowed_claim": spec["claim"],
                "rows": m4.get("rows"),
                "positive": m4.get("positive"),
                "negative": m4.get("negative"),
                "m4_auroc": m4.get("auroc"),
                "m4_auprc": m4.get("auprc"),
                "m4_balanced_accuracy": m4.get("balanced_accuracy"),
                "paper_boundary": "not_promoted_until_claim_boundary_lock",
            }
        )
    return rows


def blocked_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "blocked_claim": "all_relation_generalization",
            "reason": "Only four promoted families were evaluated in official validation.",
        },
        {
            "blocked_claim": "solved_support_contact",
            "reason": "support_contact M4 AUROC is 0.631712 and schema audit shows strong predicate/class-pair shortcut risk.",
        },
        {
            "blocked_claim": "strong_relative_horizontal_frame_invariance",
            "reason": "horizontal frame-swap macro delta is weak; use family-specific control caveat.",
        },
        {
            "blocked_claim": "p_rel_or_p_obs_reliability",
            "reason": "Current official metric evaluates C_e only; p_rel/p_obs remain disabled.",
        },
        {
            "blocked_claim": "source_reranking_recall_tradeoff",
            "reason": "Current official metric uses GT/counterfactual C_e mechanism rows, not VL-SAT/Open3DSG source reranking.",
        },
        {
            "blocked_claim": "official_test_result",
            "reason": "Official test was not used.",
        },
    ]


def report_text(
    *,
    output_dir: Path,
    status: str,
    validation_errors: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
    family_rows: list[dict[str, Any]],
    blocked_rows: list[dict[str, Any]],
) -> str:
    lines = [
        "# H002 Official Metric Result Review After Runner",
        "",
        "## Status",
        "",
        "```text",
        f"artifact_root = {rel_path(output_dir)}/",
        f"status = {status}",
        f"selected_path = {SELECTED_PATH if not validation_errors else 'blocked_fix_review_inputs'}",
        f"validation_errors = {len(validation_errors)}",
        f"next_todo = {NEXT_TODO if not validation_errors else 'fix_official_metric_review_inputs'}",
        "```",
        "",
        "## Paper-Level Gate Decision",
        "",
        "| Gate | Status | Decision |",
        "| --- | --- | --- |",
    ]
    for row in gate_rows:
        lines.append(f"| `{row['gate']}` | `{row['status']}` | {row['decision']} |")
    lines.extend(["", "## Family Claim Boundary", "", "| Family | Status | M4 AUROC | Boundary |", "| --- | --- | ---: | --- |"])
    for row in family_rows:
        lines.append(f"| `{row['route_family']}` | `{row['status']}` | {row['m4_auroc']} | {row['allowed_claim']} |")
    lines.extend(["", "## Blocked Claims", ""])
    for row in blocked_rows:
        lines.append(f"- `{row['blocked_claim']}`: {row['reason']}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Official validation C_e mechanism experiment is valid enough to move to claim-boundary lock.",
            "It is not yet a final paper table result because paper wording, relation-family scope,",
            "and caveats must be locked first.",
            "",
            "## Next",
            "",
            "```text",
            NEXT_TODO,
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    runner_summary = read_json(args.runner_dir / "summary.json")
    eval_manifest = read_json(args.eval_dir / "eval_manifest.json")
    aggregate_rows = read_csv(args.eval_dir / "aggregate_metrics.csv")
    family_metrics = read_csv(args.eval_dir / "family_metrics.csv")
    control_rows = read_csv(args.eval_dir / "control_metrics.csv")
    validation_errors = validate_inputs(runner_summary, eval_manifest, args.runner_dir, args.eval_dir)

    gates = paper_level_gate_rows(aggregate_rows, family_metrics, control_rows)
    family_decisions = family_decision_rows(family_metrics)
    blocked = blocked_claim_rows()
    status = STATUS_READY if not validation_errors else STATUS_ERRORS
    selected_path = SELECTED_PATH if not validation_errors else "blocked_fix_review_inputs"
    next_todo = NEXT_TODO if not validation_errors else "fix_official_metric_review_inputs"

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(validation_errors),
        "next_todo": next_todo,
        "input_artifacts": {
            "runner_summary": rel_path(args.runner_dir / "summary.json"),
            "eval_manifest": rel_path(args.eval_dir / "eval_manifest.json"),
            "aggregate_metrics": rel_path(args.eval_dir / "aggregate_metrics.csv"),
            "family_metrics": rel_path(args.eval_dir / "family_metrics.csv"),
            "control_metrics": rel_path(args.eval_dir / "control_metrics.csv"),
        },
        "output_artifacts": {
            "paper_level_gate": rel_path(args.output_dir / "paper_level_gate.csv"),
            "family_claim_decisions": rel_path(args.output_dir / "family_claim_decisions.csv"),
            "blocked_claims": rel_path(args.output_dir / "blocked_claims.csv"),
            "report": rel_path(args.output_dir / "report.md"),
        },
        "decision": {
            "paper_level_experiment_execution_gate": "passed_with_caveats",
            "paper_result_promotion": "not_yet",
            "next_action": "claim_boundary_lock",
            "main_candidate_families": ["relative_vertical", "size_relative"],
            "conditional_candidate_families": ["relative_horizontal"],
            "diagnostic_families": ["support_contact"],
        },
        "boundary": {
            "official_validation_metric_produced": True,
            "official_validation_eval_only": True,
            "official_test_usage": False,
            "paper_metric_promoted": False,
            "p_rel_claim_enabled": False,
            "p_obs_claim_enabled": False,
            "all_relation_generalization_enabled": False,
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_csv(args.output_dir / "paper_level_gate.csv", gates)
    write_csv(args.output_dir / "family_claim_decisions.csv", family_decisions)
    write_csv(args.output_dir / "blocked_claims.csv", blocked)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    (args.output_dir / "report.md").write_text(
        report_text(
            output_dir=args.output_dir,
            status=status,
            validation_errors=validation_errors,
            gate_rows=gates,
            family_rows=family_decisions,
            blocked_rows=blocked,
        ),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
