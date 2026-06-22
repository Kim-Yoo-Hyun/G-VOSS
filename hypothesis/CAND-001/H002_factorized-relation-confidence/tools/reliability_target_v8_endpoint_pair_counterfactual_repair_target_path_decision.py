#!/usr/bin/env python3
"""Decide the H002 path after v8 repair target-independence audit."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_target_independence_audit_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_target_path_decision_codex_proxy_user_requested"

RELIABILITY_MULTICLASS = "relation_reliability_state_v6_multiclass_target"
RELIABILITY_BINARY = "relation_reliability_v6_binary_target"
GEOMETRY_TARGET = "geometry_support_v6_binary_target"
USEFULNESS_TARGET = "relation_usefulness_v6_binary_target"

SELECTED_PATH = "v9_predicate_rank_hint_controlled_feasibility_scan"
NEXT_TODO = "reliability_target_v9_predicate_rank_hint_controlled_feasibility_scan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def relation_binary_snapshot(audit: dict[str, Any]) -> dict[str, Any]:
    decision = audit["target_decisions"][RELIABILITY_BINARY]
    original = decision["original"]
    return {
        "status": decision["status"],
        "posterior_allowed": decision["posterior_allowed"],
        "rows": original["rows"],
        "classes": original["classes"],
        "strict_size_ready": original["strict_size_ready"],
        "diagnostic_size_ready": original["diagnostic_size_ready"],
        "strict_candidate": original["strict_candidate"],
        "diagnostic_candidate": original["diagnostic_candidate"],
        "blocking_risk_count": original["blocking_risk_count"],
        "control_required_risk_count": original["control_required_risk_count"],
        "blocking_by_category": original["blocking_by_category"],
        "top_blocking_risks": [
            {
                "category": risk["category"],
                "group_key": risk["group_key"],
                "majority_rule_accuracy": risk["majority_rule_accuracy"],
                "majority_baseline_accuracy": risk["majority_baseline_accuracy"],
                "normalized_mutual_information": risk["normalized_mutual_information"],
                "class_rate_range": risk["class_rate_range"],
                "risk_reasons": risk["risk_reasons"],
            }
            for risk in original["top_blocking_risks"]
        ],
    }


def target_snapshot(audit: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for target_name in [RELIABILITY_MULTICLASS, RELIABILITY_BINARY, GEOMETRY_TARGET, USEFULNESS_TARGET]:
        decision = audit["target_decisions"][target_name]
        original = decision["original"]
        output[target_name] = {
            "status": decision["status"],
            "posterior_allowed": decision["posterior_allowed"],
            "rows": original["rows"],
            "classes": original["classes"],
            "min_class": original["min_class"],
            "strict_size_ready": original["strict_size_ready"],
            "diagnostic_size_ready": original["diagnostic_size_ready"],
            "strict_candidate": original["strict_candidate"],
            "diagnostic_candidate": original["diagnostic_candidate"],
            "blocking_risk_count": original["blocking_risk_count"],
            "control_required_risk_count": original["control_required_risk_count"],
        }
    return output


def validate_audit(audit: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_status = "h002_reliability_target_v8_repair_target_independence_audit_blocked_shortcut_risk"
    expected_next = "reliability_target_v8_endpoint_pair_counterfactual_repair_target_path_decision"
    if audit.get("status") != expected_status:
        errors.append({"error_type": "unexpected_audit_status", "expected": expected_status, "actual": audit.get("status")})
    if audit.get("next_todo") != expected_next:
        errors.append({"error_type": "unexpected_audit_next_todo", "expected": expected_next, "actual": audit.get("next_todo")})
    if audit.get("validation_errors") != 0:
        errors.append({"error_type": "audit_validation_errors_present", "actual": audit.get("validation_errors")})
    boundary = audit.get("boundary", {})
    for key in ["validation_usage", "test_usage", "trains_new_posterior", "posterior_claim_allowed", "multi_view_as_model_input"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "audit_boundary_violation", "key": key, "expected": False, "actual": boundary.get(key)})
    if boundary.get("split") != "train_only":
        errors.append({"error_type": "unexpected_boundary_split", "expected": "train_only", "actual": boundary.get("split")})

    relation = audit["target_decisions"][RELIABILITY_BINARY]
    if relation.get("posterior_allowed") is not False:
        errors.append({"error_type": "relation_binary_unexpectedly_allows_posterior"})
    if relation["original"].get("rows", 0) < 50:
        errors.append({"error_type": "relation_binary_rows_unexpectedly_sparse", "actual": relation["original"].get("rows")})
    return errors


def option_matrix() -> list[dict[str, str]]:
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": "The relation binary target is size-ready but still fails target-independence; posterior performance would mostly measure shortcut exploitation.",
        },
        {
            "option": "change_factorized_combiner_now",
            "verdict": "reject_for_now",
            "reason": "The current blocker is target construction, not posterior capacity. A stronger combiner could learn predicate/rank/hint bias faster.",
        },
        {
            "option": "downgrade_current_repair_to_final_diagnostic_only",
            "verdict": "reject_as_final",
            "reason": "The repair target fixed count/balance and endpoint-pair controls enough to justify one more targeted mining pass.",
        },
        {
            "option": "mix_close_by_into_current_repair",
            "verdict": "reject_for_now",
            "reason": "Proximity is needed for generality, but adding it before the core target is clean would confound dense-relation noise with the remaining shortcut problem.",
        },
        {
            "option": "use_machine_hint_as_model_input",
            "verdict": "reject",
            "reason": "machine_hint_hidden is a construction diagnostic. It may be used only as a sampling/audit control axis, never as deployable posterior evidence.",
        },
        {
            "option": SELECTED_PATH,
            "verdict": "select",
            "reason": "The remaining risks are localized to predicate_label, rank_band_hidden, and machine_hint_hidden, so the next target should explicitly balance those axes while preserving endpoint-pair contrast.",
        },
    ]


def selected_path_plan() -> dict[str, Any]:
    return {
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "current_repair_target_role": "diagnostic_only_until_a_new_independence_audit_passes",
        "posterior_smoke_allowed": False,
        "sampling_controls": [
            "predicate_label",
            "rank_band_hidden",
            "machine_hint_hidden",
            "exact_endpoint_pair_key_hidden",
            "counterfactual_pair_id_hidden",
            "source_queue_hidden",
            "label_geometry_bucket_hidden",
        ],
        "hard_constraints": [
            "train_only",
            "no_validation_or_test_usage",
            "do_not_use_machine_hint_as_model_input",
            "do_not_use_rank_band_hidden_as_model_input",
            "hidden axes are sampling/audit controls only",
            "keep multi-view as audit evidence only",
            "keep current repair artifacts unchanged",
        ],
        "feasibility_scan_questions": [
            "Can the full train pool support accept/reject candidates balanced within predicate_label?",
            "Can rank_band_hidden be balanced without collapsing row count below strict thresholds?",
            "Can machine_hint_hidden be balanced enough that it no longer predicts reliability?",
            "Can endpoint-pair/counterfactual contrast be preserved while applying those controls?",
            "Does the controlled pool leave enough support_contact and relative_vertical examples for label readiness?",
        ],
        "minimum_gate": {
            "relation_binary_rows": 80,
            "per_class_min": 35,
            "preferred_strict_slice_rows": 70,
            "blocking_risk_count": 0,
            "posterior_smoke_before_gate": False,
        },
        "deferred_extension": {
            "close_by_proximity": "defer_until_core_v9_path_decision_or_add_as_separate_generality_branch",
            "attachment_deferred": "not_part_of_current_target_repair",
            "multi_view_model_input": "defer_until S/G/C/U target passes",
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    relation = summary["relation_binary_snapshot"]
    lines = [
        "# H002 V8 Repair Target Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Decision",
        "",
        f"Selected path: `{summary['selected_path']}`",
        "",
        summary["decision"],
        "",
        "## Why Not Posterior Now",
        "",
        f"- Relation binary rows: `{relation['rows']}` with classes `{relation['classes']}`.",
        f"- Strict size ready: `{relation['strict_size_ready']}`.",
        f"- Strict candidate: `{relation['strict_candidate']}`.",
        f"- Blocking risks: `{relation['blocking_risk_count']}`.",
        "- Remaining risks are `predicate_label`, `rank_band_hidden`, and `machine_hint_hidden`.",
        "- A posterior model could learn these shortcuts without proving factorized reliability.",
        "",
        "## Selected Next Target",
        "",
        "The current repair target is preserved as diagnostic-only. The next target should keep the endpoint-pair/counterfactual benefits but explicitly control predicate, rank-band, and machine-hint axes during mining.",
        "",
        "```text",
        f"next = {summary['next_todo']}",
        "posterior_smoke_allowed = False",
        "```",
        "",
        "## Option Matrix",
        "",
        "| Option | Verdict | Reason |",
        "| --- | --- | --- |",
    ]
    for option in summary["option_matrix"]:
        lines.append(f"| `{option['option']}` | `{option['verdict']}` | {option['reason']} |")
    lines.extend(
        [
            "",
            "## V9 Feasibility Questions",
            "",
        ]
    )
    for item in summary["selected_path_plan"]["feasibility_scan_questions"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Next TODO",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    audit_dir = as_abs(args.audit_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    audit = read_json(audit_dir / "summary.json")
    validation_errors = validate_audit(audit)
    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    selected = SELECTED_PATH if not validation_errors else "fix_v8_repair_target_path_decision_inputs"
    next_todo = NEXT_TODO if not validation_errors else "fix_reliability_target_v8_endpoint_pair_counterfactual_repair_target_path_decision_inputs"
    decision = (
        "Do not run posterior smoke. Preserve the current v8 repair target as diagnostic-only and launch a v9 feasibility scan that controls predicate_label, rank_band_hidden, and machine_hint_hidden while preserving endpoint-pair contrast."
        if not validation_errors
        else "Fix path-decision input validation errors before choosing the next H002 route."
    )
    status = (
        "h002_reliability_target_v8_repair_path_decision_select_v9_controlled_mining"
        if not validation_errors
        else "h002_reliability_target_v8_repair_path_decision_input_errors"
    )

    summary = {
        "schema_version": "h002_reliability_target_v8_repair_target_path_decision_summary_v1",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "audit_summary": rel_path(audit_dir / "summary.json"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "selected_path": selected,
        "next_todo": next_todo,
        "decision": decision,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "current_repair_target_final_posterior_input": False,
        },
        "audit_status": audit.get("status"),
        "relation_types": audit.get("relation_types", {}),
        "target_snapshot": target_snapshot(audit),
        "relation_binary_snapshot": relation_binary_snapshot(audit),
        "option_matrix": option_matrix(),
        "selected_path_plan": selected_path_plan(),
        "validation_errors": len(validation_errors),
    }
    write_json(output_paths["summary"], summary)
    with output_paths["validation_errors"].open("w", encoding="utf-8") as handle:
        for row in validation_errors:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"selected_path={summary['selected_path']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
