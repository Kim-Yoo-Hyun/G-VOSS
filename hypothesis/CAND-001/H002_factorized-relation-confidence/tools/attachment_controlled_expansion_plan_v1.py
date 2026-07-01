#!/usr/bin/env python3
"""Write the H002 attachment controlled expansion plan.

This runner does not rescan the 17GB train RGA dump. It validates the current
shortcut-controlled smoke result and the existing full-train attachment capacity
artifacts, then freezes the next materialization contract.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H002_ROOT.parents[2]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_CONTROLLED_SMOKE = H002_ROOT / "artifacts/attachment_shortcut_controlled_smoke_v1"
DEFAULT_V20_CAPACITY = (
    RGA_ROOT / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan"
)
DEFAULT_V20_CANDIDATES = (
    RGA_ROOT / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_candidate_mining"
)
DEFAULT_V21_CAPACITY = RGA_ROOT / "reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan"
DEFAULT_V22_HANGING = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining"
DEFAULT_OUTPUT_DIR = H002_ROOT / "artifacts/attachment_controlled_expansion_plan_v1"

STATUS_READY = "h002_attachment_controlled_expansion_plan_v1_ready"
STATUS_ERRORS = "h002_attachment_controlled_expansion_plan_v1_input_errors"
NEXT_TODO = "attachment_controlled_candidate_materialization_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controlled-smoke-dir", type=Path, default=DEFAULT_CONTROLLED_SMOKE)
    parser.add_argument("--v20-capacity-dir", type=Path, default=DEFAULT_V20_CAPACITY)
    parser.add_argument("--v20-candidates-dir", type=Path, default=DEFAULT_V20_CANDIDATES)
    parser.add_argument("--v21-capacity-dir", type=Path, default=DEFAULT_V21_CAPACITY)
    parser.add_argument("--v22-hanging-dir", type=Path, default=DEFAULT_V22_HANGING)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def load_summary(root: Path, errors: list[dict[str, Any]], key: str) -> dict[str, Any]:
    path = root / "summary.json"
    if not path.exists():
        errors.append({"error_type": "missing_summary", "key": key, "path": rel_path(path)})
        return {}
    return read_json(path)


def validate_inputs(
    controlled: dict[str, Any],
    v20_capacity: dict[str, Any],
    v20_candidates: dict[str, Any],
    v21_capacity: dict[str, Any],
    v22_hanging: dict[str, Any],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []

    if controlled.get("status") != "h002_attachment_shortcut_controlled_smoke_v1_completed":
        errors.append({"error_type": "controlled_smoke_not_completed", "actual": controlled.get("status")})
    if controlled.get("next_todo") != "attachment_controlled_expansion_plan_v1":
        errors.append({"error_type": "unexpected_controlled_next", "actual": controlled.get("next_todo")})
    gates = controlled.get("gates", {})
    if gates.get("gate_4_hidden_control", {}).get("pass") is not True:
        errors.append({"error_type": "controlled_hidden_gate_not_passed"})
    if gates.get("overall_interpretation") != "attachment_controlled_smoke_passed_promote_to_larger_controlled_mining":
        errors.append({"error_type": "controlled_overall_not_promotable", "actual": gates.get("overall_interpretation")})

    if v20_capacity.get("status") != (
        "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_"
        "counterfactual_capacity_scan_passed_ready_for_candidate_mining"
    ):
        errors.append({"error_type": "v20_capacity_not_passed", "actual": v20_capacity.get("status")})
    sample_400 = v20_capacity.get("sample_size_feasibility", {}).get("400", {})
    if sample_400.get("feasible") is not True or sample_400.get("selected_rows") != 400:
        errors.append({"error_type": "v20_400_preview_not_feasible", "actual": sample_400})

    expected_quota_400 = {
        "attached to|primary_hard_negative_proxy": 80,
        "attached to|primary_positive_anchor_proxy": 80,
        "connected to|connected_far_or_functional_ambiguous_diagnostic": 40,
        "connected to|connected_near_or_overlap_diagnostic": 40,
        "hanging on|primary_hard_negative_proxy": 80,
        "hanging on|primary_positive_anchor_proxy": 80,
    }
    if sample_400.get("quota_counts") != expected_quota_400:
        errors.append(
            {
                "error_type": "v20_400_quota_mismatch",
                "expected": expected_quota_400,
                "actual": sample_400.get("quota_counts"),
            }
        )

    if v20_candidates.get("status") != (
        "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_"
        "counterfactual_candidate_mining_ready_for_source_inventory"
    ):
        errors.append({"error_type": "v20_candidates_not_ready", "actual": v20_candidates.get("status")})

    if v21_capacity.get("status") != (
        "h002_reliability_target_v21_attachment_deferred_conditional_contrast_"
        "capacity_scan_blocked_predicate_imbalanced_strict_capacity"
    ):
        errors.append({"error_type": "v21_status_unexpected", "actual": v21_capacity.get("status")})

    if v22_hanging.get("status") != (
        "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_"
        "candidate_mining_ready_for_source_inventory"
    ):
        errors.append({"error_type": "v22_hanging_not_ready", "actual": v22_hanging.get("status")})

    for name, payload in [
        ("controlled", controlled),
        ("v20_capacity", v20_capacity),
        ("v20_candidates", v20_candidates),
        ("v21_capacity", v21_capacity),
        ("v22_hanging", v22_hanging),
    ]:
        if payload.get("validation_errors") not in (None, 0):
            errors.append({"error_type": "input_validation_errors_present", "input": name, "actual": payload.get("validation_errors")})
        boundary = payload.get("boundary", {})
        for key in ["validation_usage", "test_usage", "paper_evidence_allowed", "trains_new_posterior"]:
            if boundary.get(key) is True:
                errors.append({"error_type": "boundary_violation", "input": name, "key": key, "actual": boundary.get(key)})
    return errors


def plan_payload(
    args: argparse.Namespace,
    controlled: dict[str, Any],
    v20_capacity: dict[str, Any],
    v20_candidates: dict[str, Any],
    v21_capacity: dict[str, Any],
    v22_hanging: dict[str, Any],
    errors: list[dict[str, Any]],
) -> dict[str, Any]:
    sample_400 = v20_capacity.get("sample_size_feasibility", {}).get("400", {})
    return {
        "schema_version": "h002_attachment_controlled_expansion_plan_v1",
        "status": STATUS_READY if not errors else STATUS_ERRORS,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_roots": {
            "controlled_smoke": rel_path(args.controlled_smoke_dir),
            "v20_capacity": rel_path(args.v20_capacity_dir),
            "v20_candidates": rel_path(args.v20_candidates_dir),
            "v21_capacity": rel_path(args.v21_capacity_dir),
            "v22_hanging": rel_path(args.v22_hanging_dir),
        },
        "validation_errors": len(errors),
        "selected_route": "v20_endpoint_balanced_preview_400_repackage_with_numeric_geometry_join",
        "rejected_routes": {
            "direct_attachment_promotion": "controlled smoke is promising but only 34 rows",
            "v21_same_predicate_rank_geometry_family_strict_primary": "blocked by predicate imbalance; useful as diagnostic only",
            "v22_hanging_only_primary": "too narrow for attachment-family generality",
            "connected_to_binary_primary": "functional connection needs visual or mesh confirmation",
        },
        "evidence_used": {
            "controlled_smoke": {
                "rows": controlled.get("counts", {}).get("controlled_rows"),
                "positive": controlled.get("counts", {}).get("controlled_positive"),
                "negative": controlled.get("counts", {}).get("controlled_negative"),
                "compatibility_TG_auc": controlled.get("gates", {}).get("gate_2_compatibility_signal", {}).get("compatibility_TG_auc"),
                "hidden_best_auc": controlled.get("gates", {}).get("gate_4_hidden_control", {}).get("hidden_best_auc"),
            },
            "v20_capacity_400": {
                "feasible": sample_400.get("feasible"),
                "selected_rows": sample_400.get("selected_rows"),
                "quota_counts": sample_400.get("quota_counts"),
                "quota_deficits": sample_400.get("quota_deficits"),
            },
            "v20_existing_candidate_preview": {
                "selected_rows": v20_candidates.get("counts", {}).get("selected_rows"),
                "primary_binary_candidate_rows": v20_candidates.get("counts", {}).get("primary_binary_candidate_rows"),
                "connected_diagnostic_rows": v20_candidates.get("counts", {}).get("connected_diagnostic_rows"),
                "unique_scans": v20_candidates.get("counts", {}).get("unique_scans"),
                "unique_visible_endpoint_pairs": v20_candidates.get("counts", {}).get("unique_visible_endpoint_pairs"),
            },
            "v21_strict_capacity": {
                "status": v21_capacity.get("status"),
                "failed_checks": v21_capacity.get("capacity_decision", {}).get("failed_checks"),
            },
            "v22_hanging_strict_candidate": {
                "candidate_rows": v22_hanging.get("counts", {}).get("candidate_rows"),
                "strict_group_count_hidden": v22_hanging.get("counts", {}).get("strict_group_count_hidden"),
            },
        },
        "target_contract": {
            "target_rows": 400,
            "primary_binary_rows": 320,
            "diagnostic_connected_rows": 80,
            "primary_predicates": ["attached to", "hanging on"],
            "diagnostic_predicates": ["connected to"],
            "quota": {
                "attached to": {"positive": 80, "counterfactual_negative": 80},
                "hanging on": {"positive": 80, "counterfactual_negative": 80},
                "connected to": {"near_or_overlap_diagnostic": 40, "far_or_functional_ambiguous_diagnostic": 40},
            },
            "row_source": "v20 preview_internal_400 plus raw geometry join",
            "split": "train_only",
        },
        "materialization_contract": {
            "next_runner": "tools/attachment_controlled_candidate_materialization_v1.py",
            "input_preview": rel_path(args.v20_capacity_dir / "preview_internal_400.jsonl"),
            "required_geometry_join": "join preview rows back to full train raw pair geometry by prediction_id or directed_pair_id",
            "output_root": "artifacts/attachment_controlled_candidates_v1/",
            "must_emit": [
                "candidate_rows.jsonl",
                "compatibility_rows.jsonl",
                "diagnostic_connected_rows.jsonl",
                "summary.json",
                "validation_errors.jsonl",
                "report.md",
            ],
        },
        "model_input_contract": {
            "T_e": ["predicate_label", "relation_family", "subject_label", "object_label"],
            "Z_e": ["source_rank", "source_rank_band", "source_score_if_available"],
            "G_e": [
                "normalized_distance_3d",
                "normalized_distance_xy",
                "normalized_center_delta_z",
                "vertical_gap_subject_on_object",
                "projected_iou_xy",
                "projected_subject_overlap_ratio",
                "projected_object_overlap_ratio",
                "near_contact",
                "loose_near_contact",
                "far_separated",
                "projected_overlap_support",
                "derived_closeness_and_overlap_features",
            ],
            "Q_e": ["raw_geometry_join_state", "uncertainty_flags", "connected_to_unsupported_family_flag"],
            "forbidden_inputs": [
                "cell_id_hidden",
                "proxy_role",
                "provisional_status_hidden",
                "capacity_evidence_tier",
                "geometry_status",
                "machine_hint",
                "label fields",
                "review fields",
            ],
            "compatibility_head_rule": "C_e may use T_e and G_e only; Z_e is excluded.",
        },
        "evaluation_contract": {
            "primary_task": "binary predicate-geometry compatibility for attached to and hanging on",
            "diagnostic_task": "connected to observability/ambiguity diagnostic only",
            "required_models": [
                "source_only_Z",
                "semantic_source_TZ",
                "geometry_only_G",
                "compatibility_TG",
                "factorized_TZGQ",
                "predicate_family_shortcut",
                "source_rank_shortcut",
                "endpoint_label_pair_shortcut",
                "hidden_cell_probe",
                "hidden_construction_probe",
                "hidden_witness_probe",
            ],
            "minimum_gates": {
                "primary_binary_rows_min": 240,
                "per_primary_predicate_min_positive": 60,
                "per_primary_predicate_min_negative": 60,
                "validation_errors": 0,
                "compatibility_TG_beats_source_only": True,
                "compatibility_TG_beats_predicate_family_shortcut": True,
                "compatibility_TG_beats_hidden_best_by_margin": 0.05,
                "endpoint_label_pair_shortcut_auc_max": 0.70,
            },
        },
        "boundary": {
            "validation_usage": False,
            "test_usage": False,
            "paper_evidence_allowed": False,
            "trains_paper_model": False,
            "modifies_h001": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "multi_view_or_mesh_as_audit_only": True,
        },
        "next_todo": NEXT_TODO,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    evidence = summary["evidence_used"]
    contract = summary["target_contract"]
    gates = summary["evaluation_contract"]["minimum_gates"]
    lines = [
        "# H002 Attachment Controlled Expansion Plan V1",
        "",
        f"Date: {summary['created_at']}",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Decision",
        "",
        "Selected route:",
        "",
        f"`{summary['selected_route']}`",
        "",
        "The strict 34-row controlled smoke passed, but it is too small for a method claim. The next",
        "step is a larger train-only attachment candidate materialization using the v20 endpoint-balanced",
        "full-train capacity preview.",
        "",
        "## Evidence",
        "",
        "Controlled smoke:",
        "",
        "```text",
        f"rows = {evidence['controlled_smoke']['rows']}",
        f"positive / negative = {evidence['controlled_smoke']['positive']} / {evidence['controlled_smoke']['negative']}",
        f"T+G AUROC = {evidence['controlled_smoke']['compatibility_TG_auc']}",
        f"hidden best AUROC = {evidence['controlled_smoke']['hidden_best_auc']}",
        "```",
        "",
        "v20 full-train capacity:",
        "",
        "```text",
        f"400-row feasible = {evidence['v20_capacity_400']['feasible']}",
        f"selected rows = {evidence['v20_capacity_400']['selected_rows']}",
        f"quota deficits = {evidence['v20_capacity_400']['quota_deficits']}",
        "```",
        "",
        "Rejected strict route:",
        "",
        "```text",
        f"v21 status = {evidence['v21_strict_capacity']['status']}",
        f"failed checks = {evidence['v21_strict_capacity']['failed_checks']}",
        "```",
        "",
        "## Target Contract",
        "",
        "```text",
        f"target rows = {contract['target_rows']}",
        f"primary binary rows = {contract['primary_binary_rows']}",
        f"diagnostic connected rows = {contract['diagnostic_connected_rows']}",
        "attached to = 80 positive + 80 counterfactual negative",
        "hanging on = 80 positive + 80 counterfactual negative",
        "connected to = 40 near/overlap diagnostic + 40 far/ambiguous diagnostic",
        "```",
        "",
        "## Input Boundary",
        "",
        "- `T_e`: predicate and object semantic content.",
        "- `Z_e`: source score/rank only.",
        "- `G_e`: predicate-independent numeric geometry evidence.",
        "- `Q_e`: raw geometry availability and uncertainty/observability cues.",
        "- `C_e` may use `T_e + G_e` only; `Z_e` is excluded from compatibility.",
        "- Hidden construction fields are selection/control fields only, not model input.",
        "",
        "## Gates For The Next Smoke",
        "",
        "```text",
        f"primary_binary_rows_min = {gates['primary_binary_rows_min']}",
        f"per_primary_predicate_min_positive = {gates['per_primary_predicate_min_positive']}",
        f"per_primary_predicate_min_negative = {gates['per_primary_predicate_min_negative']}",
        f"compatibility_TG_beats_hidden_best_by_margin = {gates['compatibility_TG_beats_hidden_best_by_margin']}",
        f"endpoint_label_pair_shortcut_auc_max = {gates['endpoint_label_pair_shortcut_auc_max']}",
        "validation_errors = 0",
        "```",
        "",
        "## Boundary",
        "",
        "- train-only hypothesis plan.",
        "- no validation/test usage.",
        "- no paper model training.",
        "- no H001 artifact modification.",
        "- connected to remains diagnostic until visual/mesh confirmation is introduced.",
        "",
        "## Next TODO",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    load_errors: list[dict[str, Any]] = []
    controlled = load_summary(args.controlled_smoke_dir, load_errors, "controlled_smoke")
    v20_capacity = load_summary(args.v20_capacity_dir, load_errors, "v20_capacity")
    v20_candidates = load_summary(args.v20_candidates_dir, load_errors, "v20_candidates")
    v21_capacity = load_summary(args.v21_capacity_dir, load_errors, "v21_capacity")
    v22_hanging = load_summary(args.v22_hanging_dir, load_errors, "v22_hanging")

    validation_errors = load_errors + validate_inputs(controlled, v20_capacity, v20_candidates, v21_capacity, v22_hanging)
    summary = plan_payload(args, controlled, v20_capacity, v20_candidates, v21_capacity, v22_hanging, validation_errors)

    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", validation_errors)
    write_report(output_dir / "report.md", summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(
        "status={status} route={route} target_rows={rows} primary_binary_rows={primary} "
        "validation_errors={errors} next={next}".format(
            status=summary["status"],
            route=summary["selected_route"],
            rows=summary["target_contract"]["target_rows"],
            primary=summary["target_contract"]["primary_binary_rows"],
            errors=summary["validation_errors"],
            next=summary["next_todo"],
        )
    )
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

