#!/usr/bin/env python3
"""Decide the H002 path after proximity LH-only feasibility."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_V10_DIR = RGA_ROOT / "reliability_target_v10_proximity_relation_family_feasibility_scan"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v10_proximity_lh_only_path_decision"

EXPECTED_V10_STATUS = "h002_reliability_target_v10_proximity_feasibility_lh_only_ready_not_bidirectional"
SELECTED_PATH = "v12_proximity_lh_only_label_readiness"
NEXT_TODO = "reliability_target_v12_proximity_lh_only_label_readiness"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v10-dir", type=Path, default=DEFAULT_V10_DIR)
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


def validate_v10(v10: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if v10.get("status") != EXPECTED_V10_STATUS:
        errors.append({"error_type": "unexpected_v10_status", "expected": EXPECTED_V10_STATUS, "actual": v10.get("status")})
    if v10.get("next_todo") != "reliability_target_v10_proximity_lh_only_path_decision":
        errors.append({"error_type": "unexpected_v10_next_todo", "actual": v10.get("next_todo")})
    if v10.get("validation_errors") != 0:
        errors.append({"error_type": "v10_validation_errors_present", "actual": v10.get("validation_errors")})

    gates = v10.get("feasibility_gates", {})
    bidirectional = gates.get("bidirectional_hl_lh_gate", {})
    if bidirectional.get("pass") is not False:
        errors.append({"error_type": "unexpected_bidirectional_gate", "actual": bidirectional.get("pass")})
    if int(bidirectional.get("hl_rows", -1)) != 0:
        errors.append({"error_type": "unexpected_proximity_hl_rows", "actual": bidirectional.get("hl_rows")})
    if int(bidirectional.get("lh_rows", 0) or 0) < 1000:
        errors.append({"error_type": "proximity_lh_pool_too_small", "actual": bidirectional.get("lh_rows")})
    if gates.get("lh_pool_gate", {}).get("pass") is not True:
        errors.append({"error_type": "lh_pool_gate_failed", "actual": gates.get("lh_pool_gate", {})})
    if gates.get("preview_capacity_gate", {}).get("pass") is not True:
        errors.append({"error_type": "preview_capacity_gate_failed", "actual": gates.get("preview_capacity_gate", {})})

    boundary = v10.get("boundary", {})
    for key in ["validation_usage", "test_usage", "trains_new_posterior", "posterior_smoke_allowed", "label_fill_allowed", "paper_evidence_allowed", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "v10_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def option_matrix(v10: dict[str, Any]) -> list[dict[str, Any]]:
    gates = v10["feasibility_gates"]
    risks = {risk["predictor"]: risk for risk in v10.get("shortcut_risks", [])}
    return [
        {
            "option": "redefine_rga_as_lh_only",
            "verdict": "reject",
            "reason": "H002's framework-level claim is semantic score != geometry validity != relation reliability, which requires RGA to remain bidirectional even if the current branch is LH-only.",
        },
        {
            "option": "run_factorized_posterior_now",
            "verdict": "reject",
            "reason": "No independent reliability labels exist yet; machine_hint and object-pair shortcuts are still present, so posterior performance would not be interpretable.",
        },
        {
            "option": "construct_proximity_hl_source_now",
            "verdict": "defer",
            "reason": "Current train evidence has proximity RGA-HL = 0. Creating an HL source now would likely be synthetic or source-dependent and would add target-construction risk before the real LH branch is tested.",
        },
        {
            "option": "keep_proximity_diagnostic_only",
            "verdict": "reject_as_next",
            "reason": f"Proximity has enough train-only LH evidence: total={gates['total_proximity_rows_gate']['value']}, strict_lh_pool={gates['lh_pool_gate']['value']}, preview={gates['preview_capacity_gate']['value']}.",
        },
        {
            "option": "return_to_support_vertical_exact_pair",
            "verdict": "defer_as_fallback",
            "reason": "Support/vertical exact-pair v9 is already known to be rank/predicate entangled. It remains useful diagnostic evidence but is not the cleanest next target.",
        },
        {
            "option": "accept_proximity_lh_only_branch",
            "verdict": "select",
            "reason": "This keeps the RGA framework bidirectional while validating a real, abundant failure mode: low semantic confidence but high geometry support.",
        },
        {
            "option": "add_multiview_or_attachment_now",
            "verdict": "reject_for_now",
            "reason": "That would mix target repair with a new evidence modality. Multi-view should remain audit evidence until the base S/G/C/U posterior path has a clean target.",
        },
        {
            "option": "label_match_status_as_target",
            "verdict": "reject",
            "reason": f"machine_hint predicts label_match_status with majority accuracy {risks.get('machine_hint', {}).get('majority_rule_accuracy')}; label_match_status can be a sampling stratum or audit axis, not the final reliability target.",
        },
    ]


def selected_plan(v10: dict[str, Any]) -> dict[str, Any]:
    gates = v10["feasibility_gates"]
    preview = v10["preview_selection"]
    risks = {risk["predictor"]: risk for risk in v10.get("shortcut_risks", [])}
    return {
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "framework_boundary": {
            "rga_framework": "bidirectional_hl_lh_mismatch",
            "current_empirical_branch": "proximity_lh_only",
            "claim_boundary": "validates one RGA failure mode, not the full bidirectional framework",
        },
        "why_select_lh_only": [
            "The current train artifact contains no proximity RGA-HL rows, so forcing a bidirectional proximity benchmark would create an artificial target.",
            "The proximity LH pool is real and large enough for controlled label readiness.",
            "This branch directly tests whether relation reliability differs from both semantic score and geometry validity when semantic score is low but geometry evidence is high.",
        ],
        "target_question": "Among low-semantic/high-geometry close-by edges, distinguish reliable true underconfidence from dense proximity noise, annotation sparsity, and alternative-relation cases.",
        "candidate_pool_snapshot": {
            "total_proximity_rows": gates["total_proximity_rows_gate"]["value"],
            "queue_proximity_rows": gates["total_proximity_rows_gate"]["queue_value"],
            "rga_hl_rows": gates["bidirectional_hl_lh_gate"]["hl_rows"],
            "rga_lh_rows": gates["bidirectional_hl_lh_gate"]["lh_rows"],
            "strict_lh_pool_rows": gates["lh_pool_gate"]["value"],
            "preview_rows": preview["selected_rows"],
            "preview_by_label_match_status": preview["selected_by_label_match_status"],
            "unique_scans": preview["unique_scans"],
            "unique_label_pairs": preview["unique_label_pairs"],
        },
        "next_label_task": {
            "candidate_source": "v10 preview_candidates.jsonl",
            "visible_prompt": "Is the close-by relation meaningful and reliable for this subject-object pair, rather than dense proximity noise, a trivial relation, or an annotation artifact?",
            "allowed_labels": [
                "accept_reliable_close_by",
                "reject_unreliable_close_by",
                "abstain_uncertain",
            ],
            "binary_target_after_ingestion": "accept_reliable_close_by vs reject_unreliable_close_by; abstain excluded",
            "do_not_use_as_target": [
                "label_match_status",
                "machine_hint",
                "rank_band",
                "scan_id",
                "subject_object_label_pair",
            ],
        },
        "controls_required_before_posterior": [
            "hide machine_hint and label_match_status from reviewer-visible fields",
            "audit object-label pair and scan shortcuts after label ingestion",
            "verify rank_band is not predictive of binary reliability labels",
            "cap or stratify dominant subject-object label pairs if needed",
            "keep all rows train-only",
            "do not merge this target with v8/v9 support/vertical targets",
        ],
        "known_risks": {
            "machine_hint_majority_accuracy_on_label_match_status": risks.get("machine_hint", {}).get("majority_rule_accuracy"),
            "subject_object_label_pair_majority_accuracy_on_label_match_status": risks.get("subject_object_label_pair", {}).get("majority_rule_accuracy"),
            "scan_id_majority_accuracy_on_label_match_status": risks.get("scan_id", {}).get("majority_rule_accuracy"),
            "rank_band_majority_accuracy_on_label_match_status": risks.get("rank_band", {}).get("majority_rule_accuracy"),
        },
        "rejected_paths": [
            "run posterior immediately",
            "redefine RGA as LH-only",
            "construct synthetic proximity HL now",
            "use label_match_status as reliability target",
            "add multi-view model input now",
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    plan = summary["selected_plan"]
    pool = plan["candidate_pool_snapshot"]
    lines = [
        "# H002 V10 Proximity LH-Only Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Decision",
        "",
        "Select `proximity` / `close by` as an LH-only target-repair branch.",
        "",
        "Do not redefine RGA as LH-only. The framework remains bidirectional; this branch validates one real failure mode where semantic confidence is low but geometry evidence is high.",
        "",
        "## Evidence",
        "",
        "```text",
        f"total_proximity_rows = {pool['total_proximity_rows']}",
        f"queue_proximity_rows = {pool['queue_proximity_rows']}",
        f"RGA-HL proximity rows = {pool['rga_hl_rows']}",
        f"RGA-LH proximity rows = {pool['rga_lh_rows']}",
        f"strict_lh_pool_rows = {pool['strict_lh_pool_rows']}",
        f"preview_rows = {pool['preview_rows']}",
        f"unique_scans = {pool['unique_scans']}",
        f"unique_label_pairs = {pool['unique_label_pairs']}",
        "```",
        "",
        "## Target Question",
        "",
        plan["target_question"],
        "",
        "## Rejected Alternatives",
        "",
    ]
    for option in summary["option_matrix"]:
        lines.append(f"- `{option['option']}`: `{option['verdict']}` - {option['reason']}")
    lines.extend(
        [
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}`",
            "",
            "Label readiness may be prepared from the v10 preview candidates, but label fill and posterior smoke remain blocked until readiness and target-independence checks pass.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    v10_dir = as_abs(args.v10_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    v10 = read_json(v10_dir / "summary.json")
    validation_errors = validate_v10(v10)
    matrix = option_matrix(v10)
    plan = selected_plan(v10)

    status = (
        "h002_reliability_target_v10_proximity_lh_path_decision_select_lh_only_label_readiness"
        if not validation_errors
        else "h002_reliability_target_v10_proximity_lh_path_decision_blocked"
    )
    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "option_matrix": output_dir / "option_matrix.json",
        "selected_plan": output_dir / "selected_plan.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    summary = {
        "schema_version": "h002_reliability_target_v10_proximity_lh_path_decision_summary_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "v10_summary": rel_path(v10_dir / "summary.json"),
            "v10_preview_candidates": rel_path(v10_dir / "preview_candidates.jsonl"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "option_matrix": matrix,
        "selected_plan": plan,
        "selected_path": plan["selected_path"],
        "next_todo": plan["next_todo"],
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "label_readiness_allowed": True,
            "label_fill_allowed": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
        },
        "validation_errors": len(validation_errors),
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["option_matrix"], matrix)
    write_json(output_paths["selected_plan"], plan)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"selected_path={summary['selected_path']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"label_readiness_allowed={summary['boundary']['label_readiness_allowed']}")
    print(f"label_fill_allowed={summary['boundary']['label_fill_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
