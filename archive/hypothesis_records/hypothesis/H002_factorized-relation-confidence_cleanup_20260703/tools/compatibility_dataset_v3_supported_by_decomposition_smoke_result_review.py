#!/usr/bin/env python3
"""Review R6 supported-by decomposition smoke and freeze route position."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_RUNNER_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_supported_by_decomposition_smoke_runner"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_supported_by_decomposition_smoke_result_review"

EXPECTED_RUNNER_STATUS = (
    "h002_compatibility_dataset_v3_supported_by_decomposition_smoke_runner_q_observability_diagnostic"
)
EXPECTED_RUNNER_NEXT = "compatibility_dataset_v3_supported_by_decomposition_smoke_result_review"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_supported_by_decomposition_smoke_result_review_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_supported_by_decomposition_smoke_result_review_ready_for_route_update"
)
STATUS_ERRORS = "h002_compatibility_dataset_v3_supported_by_decomposition_smoke_result_review_input_errors"
SELECTED_PATH = "freeze_supported_by_as_superordinate_decomposition_diagnostic_keep_out_of_main_factorized_success"
NEXT_TODO = "compatibility_dataset_v3_route_map_update_after_supported_by_decomposition_review"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-dir", type=Path, default=DEFAULT_RUNNER_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def snapshot(gates: dict[str, Any], name: str) -> float | None:
    value = gates.get("model_auroc_snapshot", {}).get(name)
    return float(value) if isinstance(value, (int, float)) else None


def validate_inputs(
    runner_summary: dict[str, Any],
    gate_results: dict[str, Any],
    hidden_probe_results: dict[str, Any],
    runner_validation: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if runner_summary.get("status") != EXPECTED_RUNNER_STATUS:
        errors.append({"error_type": "unexpected_runner_status", "actual": runner_summary.get("status")})
    if runner_summary.get("next_todo") != EXPECTED_RUNNER_NEXT:
        errors.append({"error_type": "unexpected_runner_next_todo", "actual": runner_summary.get("next_todo")})
    if runner_summary.get("validation_errors") != 0:
        errors.append({"error_type": "runner_validation_errors", "actual": runner_summary.get("validation_errors")})
    if runner_validation:
        errors.append({"error_type": "runner_validation_error_rows_present", "rows": len(runner_validation)})
    if runner_summary.get("learned_smoke_executed") is not True:
        errors.append({"error_type": "runner_not_executed"})

    boundary = runner_summary.get("boundary", {})
    for key in ["h001_artifacts_modified", "hidden_probes_model_input_allowed", "paper_evidence_allowed", "test_usage", "validation_usage"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    if boundary.get("split") != "train_internal_grouped_by_cv_group_id":
        errors.append({"error_type": "unexpected_split", "actual": boundary.get("split")})

    required_gates = [
        "gate_data_integrity",
        "gate_p_obs_signal",
        "gate_p_rel_signal",
        "gate_p_rel_gain",
        "gate_q_boundary_on_observable_p_rel",
        "gate_shortcut_boundary",
        "gate_shuffled_G_degradation",
        "gate_shuffled_Q_boundary",
    ]
    for gate_name in required_gates:
        if gate_name not in gate_results:
            errors.append({"error_type": "missing_gate", "gate": gate_name})

    if gate_results.get("gate_data_integrity", {}).get("pass") is not True:
        errors.append({"error_type": "data_integrity_gate_failed"})
    if gate_results.get("gate_p_obs_signal", {}).get("pass") is not True:
        errors.append({"error_type": "p_obs_signal_gate_failed"})
    if gate_results.get("gate_p_rel_signal", {}).get("pass") is not True:
        errors.append({"error_type": "p_rel_signal_gate_failed"})
    if gate_results.get("gate_shuffled_G_degradation", {}).get("pass") is not True:
        errors.append({"error_type": "shuffled_g_gate_failed"})

    if gate_results.get("gate_p_rel_gain", {}).get("pass") is not False:
        errors.append({"error_type": "expected_p_rel_gain_gate_to_fail_for_diagnostic_review"})
    if gate_results.get("gate_q_boundary_on_observable_p_rel", {}).get("pass") is not False:
        errors.append({"error_type": "expected_q_boundary_gate_to_fail_for_diagnostic_review"})

    construction_p_rel = hidden_probe_results.get("construction_p_rel", {}).get("auroc")
    if not isinstance(construction_p_rel, (int, float)) or construction_p_rel < 0.95:
        errors.append({"error_type": "construction_probe_not_strong_enough_for_leakage_boundary", "actual": construction_p_rel})
    return errors


def metric_rows(gates: dict[str, Any], hidden: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": "T1_p_obs_M6_TGQ",
            "auroc": snapshot(gates, "T1_p_obs_M6"),
            "interpretation": "p_obs has strong signal; Q_e is expected to dominate observability.",
        },
        {
            "name": "T1_p_obs_Q_only",
            "auroc": snapshot(gates, "T1_p_obs_Q_only"),
            "interpretation": "Q_e can solve p_obs, which is acceptable for observability.",
        },
        {
            "name": "T2_p_rel_M6_TGQ",
            "auroc": snapshot(gates, "T2_p_rel_M6_TGQ"),
            "interpretation": "observable p_rel has signal but is not the best route.",
        },
        {
            "name": "T2_p_rel_M5_GQ",
            "auroc": snapshot(gates, "T2_p_rel_M5_GQ"),
            "interpretation": "G_e + Q_e dominates the full factorized route.",
        },
        {
            "name": "T2_p_rel_M3_Q_only",
            "auroc": snapshot(gates, "T2_p_rel_M3_Q"),
            "interpretation": "Q_e is too predictive for observable p_rel, causing the diagnostic boundary.",
        },
        {
            "name": "T2_p_rel_S2_single_G",
            "auroc": snapshot(gates, "T2_p_rel_S2_single_G"),
            "interpretation": "single geometry evidence is also very strong; not a clean T_e x G_e interaction proof.",
        },
        {
            "name": "T2_p_rel_shuffled_G",
            "auroc": snapshot(gates, "T2_p_rel_shuffled_G"),
            "interpretation": "shuffled geometry degrades, so pair-specific geometry still matters.",
        },
        {
            "name": "hidden_construction_p_rel",
            "auroc": hidden.get("construction_p_rel", {}).get("auroc"),
            "interpretation": "construction fields can copy the target and must stay audit-only.",
        },
    ]


def route_position() -> list[dict[str, Any]]:
    return [
        {
            "route_id": "R6",
            "family": "superordinate_support",
            "relations": "supported by",
            "route_type": "accept_relabel_reject_abstain_decomposition",
            "status": "diagnostic_frozen_not_main_factorized_success",
            "paper_role": "broad-label decomposition and abstention boundary evidence",
            "allowed_claim": "broad `supported by` labels should be decomposed into accept/relabel/reject/abstain rather than treated as a clean binary compatibility target",
            "blocked_claim": "factorized `T_e + G_e + Q_e` route outperforms component routes for `supported by`",
        },
        {
            "route_id": "R3",
            "family": "support_contact",
            "relations": "standing on; lying on",
            "route_type": "predicate_geometry_compatibility",
            "status": "kept_separate_from_supported_by",
            "paper_role": "main/challenging compatibility-route evidence with caveat",
            "allowed_claim": "specific support/contact predicates can test predicate-conditioned geometry evidence",
            "blocked_claim": "`supported by` diagnostic result invalidates support/contact compatibility evidence",
        },
        {
            "route_id": "R7",
            "family": "attachment_observability",
            "relations": "attached to; hanging on; connected to",
            "route_type": "observability_first",
            "status": "queued_after_route_map_update",
            "paper_role": "next route-specific target family if expansion continues",
            "allowed_claim": "hard physical relations may require Q_e/p_obs before p_rel",
            "blocked_claim": "direct visual/multiview model input before audit and Q_e separation",
        },
    ]


def claim_boundary() -> list[dict[str, Any]]:
    return [
        {
            "claim_area": "superordinate_support_decomposition",
            "allowed": True,
            "statement": "`supported by` supports the need for decomposition/relabel/abstain routes for broad relation labels.",
        },
        {
            "claim_area": "observability_quality",
            "allowed": True,
            "statement": "`Q_e` is useful for p_obs and exposes when broad relation labels are dominated by evidence-quality states.",
        },
        {
            "claim_area": "factorized_reliability_success",
            "allowed": False,
            "statement": "Do not claim `T_e + G_e + Q_e` improves p_rel for R6; `G_e + Q_e` and Q-only are stronger.",
        },
        {
            "claim_area": "calibrated_p_rel",
            "allowed": False,
            "statement": "Do not claim calibrated relation reliability from this smoke.",
        },
        {
            "claim_area": "paper_level_result",
            "allowed": False,
            "statement": "This is train-only hypothesis evidence and not Docker/held-out paper evidence.",
        },
    ]


def reviewer_risks() -> list[dict[str, Any]]:
    return [
        {
            "risk": "Q_e_leaks_target_semantics",
            "severity": "high_if_overclaimed",
            "evidence": "Q-only AUROC on observable p_rel is 0.880547.",
            "mitigation": "Use R6 as diagnostic decomposition evidence, not main p_rel success.",
        },
        {
            "risk": "construction_proxy_leakage",
            "severity": "high",
            "evidence": "Hidden construction p_rel probe AUROC is 1.0.",
            "mitigation": "Keep construction fields hidden and audit-only; state this boundary explicitly.",
        },
        {
            "risk": "supported_by_label_too_broad",
            "severity": "medium",
            "evidence": "`supported by` mixes broad support, subtype relabel, no support, and abstain cases.",
            "mitigation": "Separate it from `standing on` / `lying on` predicate-level compatibility.",
        },
        {
            "risk": "false_negative_interpretation",
            "severity": "medium",
            "evidence": "p_rel signal exists, but component routes dominate.",
            "mitigation": "Describe as useful diagnostic signal rather than failed overall H002 framework.",
        },
    ]


def next_steps() -> list[dict[str, Any]]:
    return [
        {
            "order": 1,
            "next_todo": NEXT_TODO,
            "action": "Update the H002 route map with R6 frozen as diagnostic superordinate-support decomposition.",
            "blocked": False,
        },
        {
            "order": 2,
            "next_todo": "compatibility_dataset_v3_attachment_observability_target_plan",
            "action": "If continuing route expansion, start the R7 observability-first target plan for attached/hanging/connected.",
            "blocked": "until route map update records the R6 boundary",
        },
        {
            "order": 3,
            "next_todo": "compatibility_dataset_v3_promotion_boundary_review",
            "action": "Review which train-only route results can become paper-level experiment candidates.",
            "blocked": "until route map and family table are consistent",
        },
    ]


def write_report(
    path: Path,
    summary: dict[str, Any],
    metrics: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    boundary_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# R6 Supported-By Decomposition Smoke Result Review",
        "",
        f"Created: {summary['created_at_utc']}",
        "",
        "## Decision",
        "",
        "`supported by`는 main factorized-route success가 아니라",
        "`superordinate support decomposition / observability-geometry diagnostic`으로 고정한다.",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Key Metrics",
        "",
        "| Metric | AUROC | Interpretation |",
        "| --- | ---: | --- |",
    ]
    for row in metrics:
        value = row.get("auroc")
        value_s = f"{value:.6f}" if isinstance(value, (int, float)) else "n/a"
        lines.append(f"| `{row['name']}` | {value_s} | {row['interpretation']} |")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `p_obs`는 강하게 풀리며, 여기서 `Q_e`가 강한 것은 정상이다.",
            "- 그러나 observable `p_rel`에서도 `Q_e`와 `G_e+Q_e`가 full `T_e+G_e+Q_e`보다 강하다.",
            "- 따라서 R6는 clean predicate-geometry compatibility success가 아니라 broad label decomposition diagnostic이다.",
            "- `supported by`는 `standing on`/`lying on`과 분리해서 다뤄야 한다.",
            "",
            "## Route Position",
            "",
            "| Route | Family | Relations | Status | Paper Role |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in route_rows:
        lines.append(
            f"| `{row['route_id']}` | `{row['family']}` | {row['relations']} | `{row['status']}` | {row['paper_role']} |"
        )

    lines.extend(["", "## Claim Boundary", ""])
    for row in boundary_rows:
        lines.append(f"- `{row['claim_area']}`: allowed={row['allowed']} / {row['statement']}")

    lines.extend(
        [
            "",
            "## Next",
            "",
            "```text",
            str(summary["next_todo"]),
            "```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    runner_dir = args.runner_dir
    output_dir = args.output_dir

    runner_summary = read_json(runner_dir / "summary.json")
    gate_results = read_json(runner_dir / "gate_results.json")
    hidden_probe_results = read_json(runner_dir / "hidden_probe_results.json")
    runner_validation = read_jsonl(runner_dir / "validation_errors.jsonl")

    errors = validate_inputs(runner_summary, gate_results, hidden_probe_results, runner_validation)
    status = STATUS_ERRORS if errors else STATUS_READY
    metrics = [] if errors else metric_rows(gate_results, hidden_probe_results)
    route_rows = [] if errors else route_position()
    boundary_rows = [] if errors else claim_boundary()
    risk_rows = reviewer_risks()
    next_rows = next_steps()

    runner_snapshot = gate_results.get("model_auroc_snapshot", {})
    hidden_snapshot = {
        "construction_p_rel_auroc": hidden_probe_results.get("construction_p_rel", {}).get("auroc"),
        "source_rank_p_rel_auroc": hidden_probe_results.get("source_rank_p_rel", {}).get("auroc"),
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": None if errors else SELECTED_PATH,
        "next_todo": None if errors else NEXT_TODO,
        "validation_errors": len(errors),
        "input_paths": {
            "runner_dir": rel_path(runner_dir),
            "runner_summary": rel_path(runner_dir / "summary.json"),
            "gate_results": rel_path(runner_dir / "gate_results.json"),
            "hidden_probe_results": rel_path(runner_dir / "hidden_probe_results.json"),
        },
        "output_paths": {
            "artifact_root": rel_path(output_dir),
            "summary": rel_path(output_dir / "summary.json"),
            "review_decision": rel_path(output_dir / "review_decision.json"),
            "key_metrics": rel_path(output_dir / "key_metrics.csv"),
            "route_position": rel_path(output_dir / "route_position.csv"),
            "claim_boundary": rel_path(output_dir / "claim_boundary.csv"),
            "reviewer_risks": rel_path(output_dir / "reviewer_risks.csv"),
            "next_steps": rel_path(output_dir / "next_steps.csv"),
            "report": rel_path(output_dir / "report.md"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "runner_snapshot": runner_snapshot,
        "hidden_snapshot": hidden_snapshot,
        "gate_decision": {
            "p_obs_signal_pass": gate_results.get("gate_p_obs_signal", {}).get("pass"),
            "p_rel_signal_pass": gate_results.get("gate_p_rel_signal", {}).get("pass"),
            "p_rel_gain_pass": gate_results.get("gate_p_rel_gain", {}).get("pass"),
            "q_boundary_on_observable_p_rel_pass": gate_results.get("gate_q_boundary_on_observable_p_rel", {}).get("pass"),
            "overall_promising": gate_results.get("overall_promising"),
        },
        "boundary": {
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "test_usage": False,
            "validation_usage": False,
            "calibrated_probability_claim_allowed": False,
            "factorized_route_success_claim_allowed": False,
            "diagnostic_route_claim_allowed": True,
            "split": "train_only_grouped_cv_smoke",
        },
    }
    review_decision = {
        "selected_path": summary["selected_path"],
        "decision": "freeze_supported_by_as_diagnostic_superordinate_decomposition" if not errors else "blocked",
        "allowed_claim": (
            "`supported by` is a broad superordinate support label that benefits from accept/relabel/reject/abstain decomposition "
            "and should be separated from clean predicate-level support/contact compatibility."
        )
        if not errors
        else None,
        "blocked_claims": [
            "`supported by` is a main factorized-route success",
            "`T_e + G_e + Q_e` outperforms component routes on observable p_rel",
            "Q_e directly represents relation truth",
            "this train-only smoke is paper-level evidence",
        ],
        "why_next": "The route map must record R6 as diagnostic before moving to attachment/observability or promotion planning.",
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "review_decision.json", review_decision)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_csv(output_dir / "key_metrics.csv", metrics)
    write_csv(output_dir / "route_position.csv", route_rows)
    write_csv(output_dir / "claim_boundary.csv", boundary_rows)
    write_csv(output_dir / "reviewer_risks.csv", risk_rows)
    write_csv(output_dir / "next_steps.csv", next_rows)
    if not errors:
        write_report(output_dir / "report.md", summary, metrics, route_rows, boundary_rows)
    else:
        (output_dir / "report.md").write_text(
            "# R6 Supported-By Decomposition Smoke Result Review\n\nInput validation failed; see `validation_errors.jsonl`.\n",
            encoding="utf-8",
        )

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
