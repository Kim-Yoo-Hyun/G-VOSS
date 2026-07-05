#!/usr/bin/env python3
"""Decide the H002 path after v9 predicate/rank/hint feasibility."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_V9_DIR = RGA_ROOT / "reliability_target_v9_predicate_rank_hint_controlled_feasibility_scan_codex_proxy_user_requested"
DEFAULT_V8_MINING_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_target_repair_and_additional_mining_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v9_predicate_rank_hint_controlled_path_decision_codex_proxy_user_requested"

EXPECTED_V9_STATUS = "h002_reliability_target_v9_predicate_rank_hint_feasibility_exact_pair_not_feasible"
SELECTED_PATH = "v10_proximity_relation_family_feasibility_scan"
NEXT_TODO = "reliability_target_v10_proximity_relation_family_feasibility_scan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v9-dir", type=Path, default=DEFAULT_V9_DIR)
    parser.add_argument("--v8-mining-dir", type=Path, default=DEFAULT_V8_MINING_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def validate_inputs(v9: dict[str, Any], v8_mining: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if v9.get("status") != EXPECTED_V9_STATUS:
        errors.append({"error_type": "unexpected_v9_status", "expected": EXPECTED_V9_STATUS, "actual": v9.get("status")})
    if v9.get("next_todo") != "reliability_target_v9_predicate_rank_hint_controlled_path_decision":
        errors.append({"error_type": "unexpected_v9_next_todo", "actual": v9.get("next_todo")})
    if v9.get("feasibility", {}).get("strict_v9_exact_pair_feasible") is not False:
        errors.append({"error_type": "v9_exact_pair_unexpectedly_feasible"})
    if v9.get("feasibility", {}).get("rank_gate") is not False:
        errors.append({"error_type": "rank_gate_unexpected_value", "actual": v9.get("feasibility", {}).get("rank_gate")})
    if v9.get("feasibility", {}).get("eligible_rows", 0) < 1000:
        errors.append({"error_type": "v9_count_gate_unexpectedly_sparse", "actual": v9.get("feasibility", {}).get("eligible_rows")})
    boundary = v9.get("boundary", {})
    for key in ["validation_usage", "test_usage", "trains_new_posterior", "posterior_smoke_allowed", "paper_evidence_allowed", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "v9_boundary_violation", "key": key, "actual": boundary.get(key)})

    inventory = v8_mining.get("inventory_counts", {})
    if inventory.get("proximity_context_candidate_groups", 0) <= 0:
        errors.append({"error_type": "missing_proximity_candidate_inventory"})
    if v8_mining.get("boundary", {}).get("validation_usage") is not False:
        errors.append({"error_type": "v8_inventory_boundary_violation", "key": "validation_usage"})
    if v8_mining.get("boundary", {}).get("test_usage") is not False:
        errors.append({"error_type": "v8_inventory_boundary_violation", "key": "test_usage"})
    return errors


def option_matrix(v9: dict[str, Any], v8_mining: dict[str, Any]) -> list[dict[str, str]]:
    feasibility = v9["feasibility"]
    inventory = v8_mining.get("inventory_counts", {})
    proximity_groups = inventory.get("proximity_context_candidate_groups", 0)
    strict_proximity_groups = inventory.get("strict_nonstruct_not_current_proximity_groups", 0)
    support_rank_common = next(
        (
            item.get("common_balanced_rows_upper_bound", 0)
            for item in feasibility.get("rank_common_capacity", [])
            if item.get("family") == "support_contact"
        ),
        0,
    )
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": "v9 did not pass target-independence; posterior performance would mainly reflect rank/predicate shortcut exploitation.",
        },
        {
            "option": "continue_exact_endpoint_pair_v9_candidate_mining",
            "verdict": "reject",
            "reason": "Count and exact-pair gates pass, but rank_gate and hint_gate fail, so this exact-pair design is structurally biased.",
        },
        {
            "option": "support_contact_only_exact_pair",
            "verdict": "defer_as_fallback",
            "reason": f"support_contact has some common rank capacity ({support_rank_common} rows), but it keeps the standing/lying predicate-rank coupling and does not test relation-family generality.",
        },
        {
            "option": "endpoint_cell_rank_matched_relaxation_without_new_family",
            "verdict": "defer_as_fallback",
            "reason": "Relaxing exact endpoint-pair may be useful, but if it stays within the same support/vertical families it may preserve the same predicate/rank source structure.",
        },
        {
            "option": SELECTED_PATH,
            "verdict": "select",
            "reason": f"proximity has a large train-only inventory ({proximity_groups} context candidate groups; {strict_proximity_groups} strict nonstructural groups) and tests whether H002 generalizes beyond support/vertical exact-pair shortcuts.",
        },
        {
            "option": "attachment_or_multiview_extension_now",
            "verdict": "reject_for_now",
            "reason": "attachment-style relations likely need multi-view/mesh evidence; adding that now would mix target repair with a new evidence modality.",
        },
        {
            "option": "relative_horizontal_now",
            "verdict": "reject_for_now",
            "reason": "left/right/front/behind add coordinate-frame and viewpoint ambiguity, which is not the right next variable while target independence is unresolved.",
        },
        {
            "option": "freeze_h002_after_v9",
            "verdict": "reject_as_final",
            "reason": "v9 is useful negative evidence, but proximity inventory already exists and directly tests the relation-family expansion question.",
        },
    ]


def selected_plan(v9: dict[str, Any], v8_mining: dict[str, Any]) -> dict[str, Any]:
    inventory = v8_mining.get("inventory_counts", {})
    selection = v8_mining.get("selection_summary", {})
    return {
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "current_v9_role": "diagnostic_only_negative_evidence",
        "posterior_smoke_allowed": False,
        "why_relation_expansion_now": [
            "v9 showed that the exact support/vertical endpoint-pair target is rank/predicate entangled, not count-limited.",
            "proximity/close by gives a different geometry witness family based mainly on distance and coverage.",
            "a separate proximity branch can test H002 generality without injecting multi-view or attachment evidence.",
        ],
        "proximity_inventory_snapshot": {
            "proximity_context_candidate_groups": inventory.get("proximity_context_candidate_groups"),
            "strict_nonstruct_not_current_proximity_groups": inventory.get("strict_nonstruct_not_current_proximity_groups"),
            "future_proximity_preview_rows": selection.get("future_proximity_preview_rows"),
            "future_proximity_preview_pairs": selection.get("future_proximity_preview_pairs"),
            "kept_proximity_rows": v8_mining.get("train_counts", {}).get("kept_rows_by_family", {}).get("proximity"),
        },
        "v9_blocker_snapshot": {
            "eligible_pairs": v9["feasibility"].get("eligible_pairs"),
            "eligible_rows": v9["feasibility"].get("eligible_rows"),
            "rank_majority_accuracy": v9["feasibility"].get("rank_predicts_predicate", {}).get("majority_rule_accuracy"),
            "rank_baseline_accuracy": v9["feasibility"].get("rank_predicts_predicate", {}).get("majority_baseline_accuracy"),
            "rank_nmi": v9["feasibility"].get("rank_predicts_predicate", {}).get("normalized_mutual_information"),
            "strict_v9_exact_pair_feasible": v9["feasibility"].get("strict_v9_exact_pair_feasible"),
        },
        "v10_feasibility_requirements": {
            "split": "train_only",
            "relation_family": "proximity",
            "predicate": "close by",
            "minimum_preview_rows": 160,
            "minimum_binary_candidate_rows_after_label": 80,
            "preferred_hl_lh_balance": "B2/B3 or equivalent overconfidence/underconfidence buckets should both be present",
            "rank_control": "rank_band must be balanced or shown non-predictive before label fill",
            "object_control": "subject/object label-pair and endpoint-cell caps must pass before label fill",
            "coverage_control": "distance evidence and coverage state must be separated from invalid relation labels",
            "shortcut_audit_required": [
                "rank_band_hidden",
                "source_score_bucket_hidden",
                "subject_object_label_pair_hidden",
                "endpoint_cell_hidden",
                "scan_id",
                "geometry_distance_bucket",
                "coverage_state",
            ],
        },
        "hard_boundaries": [
            "do not train posterior in v10 feasibility",
            "do not use validation/test rows",
            "do not mix proximity rows into existing v8/v9 support/vertical target",
            "do not treat proximity as solved H002 evidence before target-independence audit",
            "do not add multi-view as model input in this step",
            "do not modify H001 artifacts",
        ],
        "fallbacks_if_v10_fails": [
            "support_contact-only rank-matched relaxation",
            "endpoint-cell/rank-matched relaxation within support/vertical",
            "freeze H002 as RGA diagnostic/benchmark direction until better independent labels exist",
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    plan = summary["selected_plan"]
    blocker = plan["v9_blocker_snapshot"]
    proximity = plan["proximity_inventory_snapshot"]
    lines = [
        "# H002 V9 Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Decision",
        "",
        f"Selected path: `{summary['selected_path']}`",
        "",
        summary["decision"],
        "",
        "## Why Exact-Pair V9 Stops Here",
        "",
        f"- eligible pairs: `{blocker['eligible_pairs']}`",
        f"- eligible rows: `{blocker['eligible_rows']}`",
        f"- strict exact-pair feasible: `{blocker['strict_v9_exact_pair_feasible']}`",
        f"- rank_band -> predicate majority accuracy: `{blocker['rank_majority_accuracy']:.4f}`",
        f"- rank baseline accuracy: `{blocker['rank_baseline_accuracy']:.4f}`",
        f"- rank NMI: `{blocker['rank_nmi']:.4f}`",
        "",
        "The issue is not row count. The exact-pair support/vertical design is structurally coupled to source rank and predicate.",
        "",
        "## Why Relation-Family Expansion Now",
        "",
    ]
    for item in plan["why_relation_expansion_now"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Proximity Inventory Snapshot",
            "",
            "```text",
            f"proximity_context_candidate_groups = {proximity['proximity_context_candidate_groups']}",
            f"strict_nonstruct_not_current_proximity_groups = {proximity['strict_nonstruct_not_current_proximity_groups']}",
            f"kept_proximity_rows = {proximity['kept_proximity_rows']}",
            f"future_proximity_preview_pairs = {proximity['future_proximity_preview_pairs']}",
            f"future_proximity_preview_rows = {proximity['future_proximity_preview_rows']}",
            "```",
            "",
            "## Option Matrix",
            "",
            "| Option | Verdict | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for row in summary["option_matrix"]:
        lines.append(f"| `{row['option']}` | `{row['verdict']}` | {row['reason']} |")
    lines.extend(
        [
            "",
            "## V10 Feasibility Requirements",
            "",
        ]
    )
    for key, value in plan["v10_feasibility_requirements"].items():
        if isinstance(value, list):
            lines.append(f"- `{key}`: {', '.join(value)}")
        else:
            lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
        ]
    )
    for item in plan["hard_boundaries"]:
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
    v9_dir = as_abs(args.v9_dir)
    v8_mining_dir = as_abs(args.v8_mining_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    v9 = read_json(v9_dir / "summary.json")
    v8_mining = read_json(v8_mining_dir / "summary.json")
    validation_errors = validate_inputs(v9, v8_mining)
    created_at = datetime.now(timezone.utc).isoformat()

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "option_matrix": output_dir / "option_matrix.json",
        "selected_plan": output_dir / "selected_plan.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    status = (
        "h002_reliability_target_v9_path_decision_select_proximity_v10"
        if not validation_errors
        else "h002_reliability_target_v9_path_decision_input_errors"
    )
    selected_path = SELECTED_PATH if not validation_errors else "fix_v9_path_decision_inputs"
    next_todo = NEXT_TODO if not validation_errors else "fix_reliability_target_v9_predicate_rank_hint_controlled_path_decision_inputs"
    decision = (
        "Freeze exact endpoint-pair v9 as diagnostic-only negative evidence and start a separate proximity/close by feasibility scan. This is a target-repair relation-family expansion, not a posterior smoke or paper metric claim."
        if not validation_errors
        else "Fix v9 path decision input validation errors before selecting the next H002 route."
    )

    options = option_matrix(v9, v8_mining)
    plan = selected_plan(v9, v8_mining)
    summary = {
        "schema_version": "h002_reliability_target_v9_path_decision_summary_v1",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "v9_summary": rel_path(v9_dir / "summary.json"),
            "v8_additional_mining_summary": rel_path(v8_mining_dir / "summary.json"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "selected_path": selected_path,
        "next_todo": next_todo,
        "decision": decision,
        "option_matrix": options,
        "selected_plan": plan,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "current_v9_exact_pair_final_posterior_input": False,
        },
        "validation_errors": len(validation_errors),
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["option_matrix"], options)
    write_json(output_paths["selected_plan"], plan)
    write_jsonl(output_paths["validation_errors"], validation_errors)
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
