#!/usr/bin/env python3
"""Decide the support/contact capacity gate after repair materialization."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


EXPECTED_STATUS = "h002_support_contact_generalization_repair_materialization_ready"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--materialization-dir",
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
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root
    mat_dir = resolve(repo_root, args.materialization_dir)
    out = resolve(repo_root, args.out)
    out.mkdir(parents=True, exist_ok=True)

    validation_errors: list[dict[str, Any]] = []
    manifest = read_json(mat_dir / "row_manifest.json")
    schema = read_json(mat_dir / "schema_precheck.json")
    gate_failures = read_jsonl(mat_dir / "gate_failures.jsonl")
    class_pair_quota = read_csv(mat_dir / "class_pair_quota.csv")

    if manifest.get("status") != EXPECTED_STATUS:
        validation_errors.append({"error_type": "unexpected_materialization_status", "actual": manifest.get("status")})
    if manifest.get("validation_errors") != 0:
        validation_errors.append({"error_type": "materialization_validation_errors", "actual": manifest.get("validation_errors")})
    if schema.get("blocked_field_hits") != 0:
        validation_errors.append({"error_type": "blocked_field_hits", "actual": schema.get("blocked_field_hits")})

    row_counts = manifest.get("row_counts", {})
    binary_rows = int(row_counts.get("model_safe_binary_no_class", 0))
    mixed_class_pairs = int(row_counts.get("mixed_class_pairs", 0))
    selective_rows = int(row_counts.get("model_safe_selective_no_class", 0))
    abstain_rows = int(manifest.get("decision_counts", {}).get("abstain", 0))

    capacity_pass = binary_rows >= 200 and mixed_class_pairs >= 10
    selected_path = "freeze_support_contact_as_diagnostic_failure_taxonomy_no_metric_rerun"
    metric_rerun_allowed = False
    support_contact_solved_claim_allowed = False
    next_todo = "pobs_prel_observability_repair"

    option_rows = [
        {
            "option_id": "A",
            "option": "run_metric_on_strict_mixed_class_pair_binary_rows",
            "evidence": f"{binary_rows} rows over {mixed_class_pairs} mixed class-pairs",
            "risk": "underpowered_metric_and_unstable_CI",
            "decision": "reject",
            "reason": "below frozen capacity gate",
        },
        {
            "option_id": "B",
            "option": "include_single_subtype_class_pairs_for_more_rows",
            "evidence": f"{selective_rows - binary_rows} rows are abstain/diagnostic under current repair",
            "risk": "class_pair_shortcut_returns_and_predicate_geometry_claim_collapses",
            "decision": "reject_for_main_metric",
            "reason": "most class-pairs contain only one positive subtype",
        },
        {
            "option_id": "C",
            "option": "continue_support_contact_with_additional_visual_mesh_audit",
            "evidence": "would require new independent pose/observability labels",
            "risk": "new benchmark_building_scope_and_not_immediate_validation_metric",
            "decision": "defer_reopen_condition",
            "reason": "scientifically possible but not available from current official validation GT",
        },
        {
            "option_id": "D",
            "option": "freeze_support_contact_as_diagnostic_and_move_to_observability_repair",
            "evidence": "schema is valid; capacity gate fails; failure mode is informative",
            "risk": "support_contact_not_a_solved_route_in_current_H002",
            "decision": "select",
            "reason": "most principled current path without reintroducing shortcuts",
        },
    ]

    paper_boundary_rows = [
        {
            "claim": "support_contact_solved_route",
            "status": "blocked",
            "allowed_wording": "support/contact is a challenging diagnostic route with pose-subtype and class-pair capacity limits",
            "blocked_wording": "support/contact is solved or metric-ready",
        },
        {
            "claim": "relation_aware_evidence_routing",
            "status": "allowed_with_caveat",
            "allowed_wording": "support/contact shows why some relation families require observability-aware abstain or relabel handling",
            "blocked_wording": "the route-aware framework is validated for all physical relations",
        },
        {
            "claim": "metric_rerun",
            "status": "blocked",
            "allowed_wording": "no support/contact metric rerun after repair due to capacity gate failure",
            "blocked_wording": "rerun support/contact metric on 40 binary rows as paper evidence",
        },
    ]

    reopen_rows = [
        {
            "condition": "independent_pose_audit_capacity",
            "requirement": ">= 200 binary accept/reject rows and >= 10 mixed class-pairs after class-pair control",
            "current": f"{binary_rows} rows and {mixed_class_pairs} mixed class-pairs",
            "status": "not_met",
        },
        {
            "condition": "observability_label_capacity",
            "requirement": "observable / unobservable / ambiguous labels from visual or mesh evidence, separated from C_e inputs",
            "current": "not available in current support/contact materialization",
            "status": "not_met",
        },
        {
            "condition": "superordinate_support_decomposition",
            "requirement": "supported_by relabel/abstain target with subtype mapping and independent audit",
            "current": "official validation materialization only covers standing on / lying on",
            "status": "not_met",
        },
        {
            "condition": "shortcut_control",
            "requirement": "predicate/class-pair/source/rank-only probes cannot solve target",
            "current": "single-subtype class-pairs dominate; strict control leaves low capacity",
            "status": "not_met",
        },
    ]

    decision_matrix_rows = [
        {
            "gate": "schema_valid",
            "value": manifest.get("validation_errors", ""),
            "pass": manifest.get("validation_errors") == 0 and schema.get("blocked_field_hits") == 0,
            "interpretation": "materialization is valid",
        },
        {
            "gate": "binary_capacity",
            "value": binary_rows,
            "pass": binary_rows >= 200,
            "interpretation": "too few rows for support/contact metric evidence",
        },
        {
            "gate": "mixed_class_pair_capacity",
            "value": mixed_class_pairs,
            "pass": mixed_class_pairs >= 10,
            "interpretation": "too few class-pairs after shortcut control",
        },
        {
            "gate": "metric_rerun_ready",
            "value": schema.get("metric_rerun_ready"),
            "pass": bool(schema.get("metric_rerun_ready")),
            "interpretation": "metric rerun is blocked",
        },
        {
            "gate": "diagnostic_value",
            "value": abstain_rows,
            "pass": abstain_rows > 0,
            "interpretation": "failure is useful as diagnostic evidence for observability/abstain route",
        },
    ]

    write_csv(
        out / "capacity_options.csv",
        option_rows,
        ["option_id", "option", "evidence", "risk", "decision", "reason"],
    )
    write_csv(
        out / "decision_matrix.csv",
        decision_matrix_rows,
        ["gate", "value", "pass", "interpretation"],
    )
    write_csv(
        out / "paper_boundary.csv",
        paper_boundary_rows,
        ["claim", "status", "allowed_wording", "blocked_wording"],
    )
    write_csv(
        out / "reopen_conditions.csv",
        reopen_rows,
        ["condition", "requirement", "current", "status"],
    )
    write_csv(
        out / "class_pair_capacity.csv",
        [
            {
                "class_pair": row.get("class_pair", ""),
                "standing_positive_groups": row.get("standing_positive_groups", ""),
                "lying_positive_groups": row.get("lying_positive_groups", ""),
                "selected_binary_rows": row.get("selected_binary_rows", ""),
                "decision": "kept_but_capacity_insufficient",
            }
            for row in class_pair_quota
        ],
        ["class_pair", "standing_positive_groups", "lying_positive_groups", "selected_binary_rows", "decision"],
    )
    write_jsonl(out / "validation_errors.jsonl", validation_errors)

    summary = {
        "status": "h002_support_contact_generalization_repair_capacity_decision_ready",
        "schema_version": "h002_support_contact_generalization_repair_capacity_decision_v1",
        "validation_errors": len(validation_errors),
        "source_artifacts": {
            "repair_materialization": repo_rel(repo_root, mat_dir),
        },
        "input_counts": {
            "binary_rows": binary_rows,
            "mixed_class_pairs": mixed_class_pairs,
            "selective_rows": selective_rows,
            "abstain_rows": abstain_rows,
            "gate_failures": len(gate_failures),
        },
        "decision": {
            "selected_path": selected_path,
            "support_contact_solved": False,
            "support_contact_metric_rerun_allowed": metric_rerun_allowed,
            "support_contact_solved_claim_allowed": support_contact_solved_claim_allowed,
            "capacity_pass": capacity_pass,
            "paper_role": "diagnostic_failure_taxonomy_and_observability_abstain_motivation",
            "reason": "strict shortcut-controlled support/contact leaves only 40 binary rows over 4 class-pairs; relaxing the target reintroduces class-pair shortcut",
            "next_todo": next_todo,
        },
        "output_artifacts": {
            "capacity_options": repo_rel(repo_root, out / "capacity_options.csv"),
            "decision_matrix": repo_rel(repo_root, out / "decision_matrix.csv"),
            "paper_boundary": repo_rel(repo_root, out / "paper_boundary.csv"),
            "reopen_conditions": repo_rel(repo_root, out / "reopen_conditions.csv"),
            "class_pair_capacity": repo_rel(repo_root, out / "class_pair_capacity.csv"),
            "validation_errors": repo_rel(repo_root, out / "validation_errors.jsonl"),
            "summary": repo_rel(repo_root, out / "summary.json"),
        },
    }
    write_json(out / "summary.json", summary)
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
