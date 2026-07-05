#!/usr/bin/env python3
"""Create the p_obs/p_rel observability repair package for H002."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--pobs-calibration-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/pobs_prel_calibration_upgrade/latest"),
    )
    parser.add_argument(
        "--support-capacity-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/support_contact_capacity_decision/latest"),
    )
    parser.add_argument(
        "--support-repair-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/support_contact_repair_materialization/latest"),
    )
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def repo_rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def pick_rows(rows: list[dict[str, Any]], limit: int, key: str = "candidate_id") -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: str(row.get(key, "")))[:limit]


def audit_question(route_family: str, predicate: str, role: str) -> str:
    if route_family == "support_contact":
        return (
            "Can visual/mesh/point evidence determine the support subtype "
            f"for predicate '{predicate}', or should this pair abstain/relabel?"
        )
    return (
        "Are the available visual/mesh/geometry assets sufficient to decide "
        f"predicate '{predicate}' for this object pair?"
    )


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root
    pobs_dir = resolve(repo_root, args.pobs_calibration_dir)
    support_capacity_dir = resolve(repo_root, args.support_capacity_dir)
    support_repair_dir = resolve(repo_root, args.support_repair_dir)
    out = resolve(repo_root, args.out)
    out.mkdir(parents=True, exist_ok=True)

    validation_errors: list[dict[str, Any]] = []
    pobs_summary = read_json(pobs_dir / "summary.json")
    support_capacity = read_json(support_capacity_dir / "summary.json")
    support_manifest = read_json(support_repair_dir / "row_manifest.json")
    support_hidden = read_jsonl(support_repair_dir / "hidden_manifest.jsonl")
    asset_rows = read_csv(pobs_dir / "observability_asset_audit_labels.csv")
    failure_route_rows = read_csv(pobs_dir / "failure_route_connection.csv")

    if pobs_summary.get("validation_errors") != 0:
        validation_errors.append({"error_type": "pobs_calibration_has_validation_errors", "actual": pobs_summary.get("validation_errors")})
    if support_capacity.get("validation_errors") != 0:
        validation_errors.append({"error_type": "support_capacity_has_validation_errors", "actual": support_capacity.get("validation_errors")})
    if support_manifest.get("validation_errors") != 0:
        validation_errors.append({"error_type": "support_repair_materialization_has_validation_errors", "actual": support_manifest.get("validation_errors")})

    asset_label_counts = Counter(row.get("asset_observability_label", "") for row in asset_rows)
    route_counts = Counter(row.get("route_family", "") for row in asset_rows)
    has_real_negative_or_ambiguous = any(asset_label_counts.get(label, 0) > 0 for label in ["unobservable", "ambiguous"])

    label_schema_rows = [
        {
            "label": "observable_clear",
            "p_obs_target": 1,
            "p_rel_target_allowed": True,
            "definition": "Visual/mesh/geometry evidence is sufficient to decide accept/reject for the relation.",
            "allowed_source": "human_or_visual_mesh_audit",
            "not_allowed_source": "file_existence_only",
        },
        {
            "label": "unobservable_missing_evidence",
            "p_obs_target": 0,
            "p_rel_target_allowed": False,
            "definition": "Required relation evidence is absent, occluded, corrupted, or unavailable.",
            "allowed_source": "human_or_visual_mesh_audit",
            "not_allowed_source": "synthetic_no_view_control_as_final_gt",
        },
        {
            "label": "ambiguous_evidence",
            "p_obs_target": 0,
            "p_rel_target_allowed": False,
            "definition": "Evidence exists but is insufficient to disambiguate relation subtype or accept/reject.",
            "allowed_source": "human_or_visual_mesh_audit",
            "not_allowed_source": "class_pair_or_predicate_prior_only",
        },
        {
            "label": "unsupported_route",
            "p_obs_target": "",
            "p_rel_target_allowed": False,
            "definition": "Route is not materialized with the evidence needed for p_obs/p_rel evaluation.",
            "allowed_source": "route_inventory",
            "not_allowed_source": "treat_as_negative_observability",
        },
    ]

    gap_rows = [
        {
            "gap": "asset_observability_single_class",
            "current_evidence": f"asset labels: {dict(asset_label_counts)}",
            "why_it_matters": "p_obs vs real asset labels has no negative/ambiguous class, so AUROC is undefined.",
            "repair_action": "collect observable_clear / unobservable_missing_evidence / ambiguous_evidence labels.",
            "claim_status": "blocks calibrated p_obs solved claim",
        },
        {
            "gap": "synthetic_missing_controls",
            "current_evidence": "no_view, low_visibility, missing_mesh, shuffled_view, wrong_pair controls drive p_obs separation.",
            "why_it_matters": "controls prove sensitivity to missing evidence but are not real deployment labels.",
            "repair_action": "use controls only as stress tests after real observability labels exist.",
            "claim_status": "appendix/control only",
        },
        {
            "gap": "p_rel_calibration",
            "current_evidence": f"p_rel calibrated ECE@10={pobs_summary.get('primary_metrics', {}).get('p_rel_calibrated_ECE_10')}",
            "why_it_matters": "p_rel discrimination passes but calibration does not.",
            "repair_action": "freeze calibration split and recalibrate after real observability filtering.",
            "claim_status": "blocks calibrated p_rel solved claim",
        },
        {
            "gap": "missing_observability_heavy_routes",
            "current_evidence": "attachment_like and containment rows are absent in current p_obs/p_rel runtime.",
            "why_it_matters": "p_obs claim is weakest exactly for relations where observability should matter most.",
            "repair_action": "add attachment/containment audit rows before broad p_obs/p_rel claims.",
            "claim_status": "blocks general observability claim",
        },
        {
            "gap": "support_contact_pose_ambiguity",
            "current_evidence": "support/contact strict repair leaves 3138 abstain/diagnostic rows.",
            "why_it_matters": "these rows are good candidates for real ambiguous_evidence labels.",
            "repair_action": "use support/contact abstain rows as visual/mesh audit queue, not as automatic labels.",
            "claim_status": "diagnostic evidence only until audited",
        },
    ]

    hidden_by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in support_hidden:
        hidden_by_role[str(row.get("repair_role", ""))].append(row)

    queue_rows: list[dict[str, Any]] = []
    queue_id = 0

    def add_queue(row: dict[str, Any], queue_kind: str, seed_hint: str) -> None:
        nonlocal queue_id
        queue_id += 1
        route = "support_contact"
        predicate = str(row.get("predicate_label", ""))
        role = str(row.get("repair_role", ""))
        queue_rows.append(
            {
                "queue_id": f"pobs_obs_repair_{queue_id:04d}",
                "candidate_id": row.get("candidate_id", ""),
                "route_family": route,
                "predicate_label": predicate,
                "class_pair": row.get("class_pair", ""),
                "repair_role": role,
                "queue_kind": queue_kind,
                "audit_question": audit_question(route, predicate, role),
                "requested_label_space": "observable_clear|unobservable_missing_evidence|ambiguous_evidence",
                "codex_seed_hint_not_gt": seed_hint,
                "label_status": "needs_visual_mesh_audit",
                "p_obs_target_after_audit": "",
                "p_rel_target_after_audit": "",
                "use_policy": "audit_queue_only_not_training_until_label_filled",
            }
        )

    for row in pick_rows(hidden_by_role.get("abstain_single_subtype_class_pair", []), 120):
        pose_state = row.get("pose_proxy", {}).get("pose_proxy_state", "unknown_pose_proxy")
        add_queue(row, "support_contact_single_subtype_abstain", f"candidate_ambiguous_or_pose_dependent:{pose_state}")
    for row in pick_rows(hidden_by_role.get("abstain_mixed_class_pair_overflow", []), 60):
        pose_state = row.get("pose_proxy", {}).get("pose_proxy_state", "unknown_pose_proxy")
        add_queue(row, "support_contact_mixed_overflow_abstain", f"candidate_ambiguous_or_pose_dependent:{pose_state}")
    for row in pick_rows(hidden_by_role.get("main_binary_mixed_class_pair", []), 40):
        add_queue(row, "support_contact_binary_control", "candidate_observable_control_needs_confirmation")

    # Add route-diverse observable controls from the asset audit. These are not
    # negative labels; they help the audit packet keep easy positive controls.
    route_added: Counter[str] = Counter()
    for row in sorted(asset_rows, key=lambda item: item.get("candidate_id", "")):
        route = row.get("route_family", "")
        if route == "support_contact":
            continue
        if route_added[route] >= 15:
            continue
        route_added[route] += 1
        queue_id += 1
        queue_rows.append(
            {
                "queue_id": f"pobs_obs_repair_{queue_id:04d}",
                "candidate_id": row.get("candidate_id", ""),
                "route_family": route,
                "predicate_label": row.get("predicate_label", ""),
                "class_pair": "",
                "repair_role": "asset_observable_control",
                "queue_kind": "route_observable_control",
                "audit_question": audit_question(route, row.get("predicate_label", ""), "asset_observable_control"),
                "requested_label_space": "observable_clear|unobservable_missing_evidence|ambiguous_evidence",
                "codex_seed_hint_not_gt": "asset_files_exist_but_needs_visual_mesh_confirmation",
                "label_status": "needs_visual_mesh_audit",
                "p_obs_target_after_audit": "",
                "p_rel_target_after_audit": "",
                "use_policy": "audit_queue_only_not_training_until_label_filled",
            }
        )

    queue_counts = Counter(row["queue_kind"] for row in queue_rows)

    gate_rows = [
        {
            "gate": "real_observability_label_classes",
            "required": "observable_clear plus at least one of unobservable_missing_evidence or ambiguous_evidence",
            "current": dict(asset_label_counts),
            "passed": has_real_negative_or_ambiguous,
            "decision": "blocked",
        },
        {
            "gate": "audit_queue_created",
            "required": ">= 200 candidate rows for visual/mesh audit",
            "current": len(queue_rows),
            "passed": len(queue_rows) >= 200,
            "decision": "passed_for_label_collection_not_for_metric",
        },
        {
            "gate": "support_contact_ambiguous_candidates",
            "required": "support/contact abstain rows available for ambiguity audit",
            "current": support_manifest.get("row_counts", {}).get("single_subtype_groups", 0),
            "passed": int(support_manifest.get("row_counts", {}).get("single_subtype_groups", 0)) > 0,
            "decision": "passed_as_audit_source",
        },
        {
            "gate": "attachment_containment_route_presence",
            "required": "nonzero attachment_like or containment rows",
            "current": {row.get("route_family"): row.get("rows") for row in failure_route_rows if row.get("route_family") in {"attachment_like", "containment"}},
            "passed": False,
            "decision": "blocked_for_general_observability_claim",
        },
        {
            "gate": "calibrated_pobs_prel_claim",
            "required": "real observability labels, p_rel ECE <= 0.10, route coverage",
            "current": "not met",
            "passed": False,
            "decision": "blocked",
        },
    ]

    next_steps = [
        {
            "order": 1,
            "todo": "pobs_prel_observability_label_fill",
            "description": "Fill the audit queue with visual/mesh-grounded observable_clear, unobservable_missing_evidence, and ambiguous_evidence labels.",
            "run_metric_after": False,
        },
        {
            "order": 2,
            "todo": "pobs_prel_observability_label_ingestion",
            "description": "Convert filled labels into model-safe Q_e and hidden selective-label artifacts.",
            "run_metric_after": False,
        },
        {
            "order": 3,
            "todo": "pobs_prel_observability_metric_after_ingestion",
            "description": "Rerun p_obs/p_rel selective metrics only if label-class and capacity gates pass.",
            "run_metric_after": True,
        },
    ]

    write_csv(
        out / "observability_gap.csv",
        gap_rows,
        ["gap", "current_evidence", "why_it_matters", "repair_action", "claim_status"],
    )
    write_csv(
        out / "label_schema.csv",
        label_schema_rows,
        ["label", "p_obs_target", "p_rel_target_allowed", "definition", "allowed_source", "not_allowed_source"],
    )
    write_jsonl(out / "observability_label_queue.jsonl", queue_rows)
    write_csv(
        out / "queue_summary.csv",
        [{"queue_kind": key, "rows": value} for key, value in sorted(queue_counts.items())],
        ["queue_kind", "rows"],
    )
    write_csv(
        out / "gate_plan.csv",
        gate_rows,
        ["gate", "required", "current", "passed", "decision"],
    )
    write_csv(
        out / "next_steps.csv",
        next_steps,
        ["order", "todo", "description", "run_metric_after"],
    )
    write_jsonl(out / "validation_errors.jsonl", validation_errors)

    summary = {
        "status": "h002_pobs_prel_observability_repair_ready",
        "schema_version": "h002_pobs_prel_observability_repair_v1",
        "validation_errors": len(validation_errors),
        "source_artifacts": {
            "pobs_calibration_upgrade": repo_rel(repo_root, pobs_dir),
            "support_contact_capacity_decision": repo_rel(repo_root, support_capacity_dir),
            "support_contact_repair_materialization": repo_rel(repo_root, support_repair_dir),
        },
        "current_blockers": {
            "asset_observability_label_counts": dict(asset_label_counts),
            "has_real_negative_or_ambiguous_observability_labels": has_real_negative_or_ambiguous,
            "p_rel_calibrated_ECE_10": pobs_summary.get("primary_metrics", {}).get("p_rel_calibrated_ECE_10"),
            "attachment_containment_rows_available": pobs_summary.get("claim_boundary", {}).get("attachment_containment_empirical_rows_available"),
            "support_contact_metric_rerun_allowed": support_capacity.get("decision", {}).get("support_contact_metric_rerun_allowed"),
        },
        "repair_outputs": {
            "observability_label_queue_rows": len(queue_rows),
            "queue_counts": dict(queue_counts),
            "label_schema": repo_rel(repo_root, out / "label_schema.csv"),
            "observability_gap": repo_rel(repo_root, out / "observability_gap.csv"),
            "observability_label_queue": repo_rel(repo_root, out / "observability_label_queue.jsonl"),
            "gate_plan": repo_rel(repo_root, out / "gate_plan.csv"),
            "next_steps": repo_rel(repo_root, out / "next_steps.csv"),
        },
        "decision": {
            "selected_path": "create_visual_mesh_observability_audit_queue_no_metric_rerun",
            "pobs_prel_metric_rerun_allowed": False,
            "pobs_prel_calibrated_solved_claim_allowed": False,
            "reason": "current p_obs labels are single-class observable under asset audit; synthetic controls are useful stress tests but not real negative/ambiguous observability GT",
            "next_todo": "pobs_prel_observability_label_fill",
        },
    }
    write_json(out / "summary.json", summary)
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
