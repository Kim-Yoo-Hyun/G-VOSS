#!/usr/bin/env python3
"""Define the H002 v14 physical relation-family sampling plan."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_FEASIBILITY_DIR = RGA_ROOT / "reliability_target_v14_physical_relation_family_feasibility_scan"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v14_physical_relation_family_sampling_plan"

EXPECTED_STATUS = "h002_reliability_target_v14_physical_relation_family_feasibility_scan_ready_support_primary_attachment_schema_deferred"
EXPECTED_NEXT = "reliability_target_v14_physical_relation_family_sampling_plan"
STATUS_READY = "h002_reliability_target_v14_physical_relation_family_sampling_plan_ready_for_candidate_mining"
STATUS_ERRORS = "h002_reliability_target_v14_physical_relation_family_sampling_plan_errors"
NEXT_TODO_READY = "reliability_target_v14_physical_relation_family_candidate_mining"
NEXT_TODO_BLOCKED = "reliability_target_v14_physical_relation_family_path_decision"

CELL_QUOTAS = [
    {
        "cell_id": "S1_support_lie_hl",
        "predicate_family": "support_contact",
        "predicate_label": "lying on",
        "queue_kind": "HL",
        "semantic_geometry_bucket": "B2_semantic_high_geometry_low",
        "target_rows": 68,
        "row_role": "primary_anchor",
        "reason": "high-capacity same-predicate support-contact HL cell",
    },
    {
        "cell_id": "S2_support_lie_lh",
        "predicate_family": "support_contact",
        "predicate_label": "lying on",
        "queue_kind": "LH",
        "semantic_geometry_bucket": "B3_semantic_low_geometry_high",
        "target_rows": 68,
        "row_role": "primary_anchor",
        "reason": "same-predicate support-contact LH counterpart for S1",
    },
    {
        "cell_id": "S3_support_stand_hl",
        "predicate_family": "support_contact",
        "predicate_label": "standing on",
        "queue_kind": "HL",
        "semantic_geometry_bucket": "B2_semantic_high_geometry_low",
        "target_rows": 12,
        "row_role": "limited_primary_diversity",
        "reason": "standing-on HL capacity is only 17, so keep as limited diversity",
    },
    {
        "cell_id": "S4_support_stand_lh",
        "predicate_family": "support_contact",
        "predicate_label": "standing on",
        "queue_kind": "LH",
        "semantic_geometry_bucket": "B3_semantic_low_geometry_high",
        "target_rows": 12,
        "row_role": "limited_primary_diversity",
        "reason": "same-predicate LH counterpart for limited standing-on cell",
    },
    {
        "cell_id": "V1_vertical_lower_hl",
        "predicate_family": "relative_vertical",
        "predicate_label": "lower than",
        "queue_kind": "HL",
        "semantic_geometry_bucket": "B2_semantic_high_geometry_low",
        "target_rows": 40,
        "row_role": "control_family",
        "reason": "geometry-easy control with enough same-predicate HL capacity",
    },
    {
        "cell_id": "V2_vertical_lower_lh",
        "predicate_family": "relative_vertical",
        "predicate_label": "lower than",
        "queue_kind": "LH",
        "semantic_geometry_bucket": "B3_semantic_low_geometry_high",
        "target_rows": 40,
        "row_role": "control_family",
        "reason": "same-predicate LH counterpart for vertical control",
    },
]

EXCLUDED_CELLS = [
    {
        "predicate_family": "support_contact",
        "predicate_label": "supported by",
        "queue_kind": "LH",
        "reason": "LH-only under current queue and outside the narrow current H002 core; keep as future diagnostic diversity, not primary target",
    },
    {
        "predicate_family": "relative_vertical",
        "predicate_label": "higher than",
        "queue_kind": "HL",
        "reason": "HL capacity is one row, so same-predicate controlled sampling is not stable",
    },
    {
        "predicate_family": "relative_vertical",
        "predicate_label": "higher than",
        "queue_kind": "LH",
        "reason": "LH-only practical capacity after excluding one unstable HL row; defer from current control target",
    },
    {
        "predicate_family": "attachment_deferred",
        "predicate_label": "attached to / hanging on / connected to",
        "queue_kind": "any",
        "reason": "current geometry policy marks attachment_deferred as unsupported_family; needs witness schema before posterior target sampling",
    },
]

HARD_ROOM_SURFACES = ["floor", "wall", "ceiling"]
STRUCTURAL_CONTEXT = ["floor", "wall", "ceiling", "room", "door", "doorframe", "window"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feasibility-dir", type=Path, default=DEFAULT_FEASIBILITY_DIR)
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with as_abs(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def to_int(value: Any) -> int:
    try:
        if value in (None, ""):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def load_capacity(predicate_inventory: list[dict[str, str]]) -> dict[tuple[str, str, str], int]:
    capacity: dict[tuple[str, str, str], int] = {}
    for row in predicate_inventory:
        family = row["family"]
        predicate = row["predicate"]
        capacity[(family, predicate, "HL")] = to_int(row.get("hl_queue_rows"))
        capacity[(family, predicate, "LH")] = to_int(row.get("lh_queue_rows"))
    return capacity


def validate_upstream(feasibility: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if feasibility.get("status") != EXPECTED_STATUS:
        errors.append({"error_type": "unexpected_feasibility_status", "expected": EXPECTED_STATUS, "actual": feasibility.get("status")})
    if feasibility.get("next_todo") != EXPECTED_NEXT:
        errors.append({"error_type": "unexpected_feasibility_next_todo", "expected": EXPECTED_NEXT, "actual": feasibility.get("next_todo")})
    if feasibility.get("validation_errors") != 0:
        errors.append({"error_type": "feasibility_validation_errors_present", "actual": feasibility.get("validation_errors")})

    boundary = feasibility.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "hidden_fields_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "feasibility_boundary_violation", "key": key, "actual": boundary.get(key)})

    for name in ["summary.json", "predicate_inventory.csv", "queue_inventory.csv", "route_matrix.jsonl"]:
        path = as_abs(args.feasibility_dir) / name
        if not path.exists():
            errors.append({"error_type": "missing_feasibility_artifact", "path": rel_path(path)})
    return errors


def cell_quota_rows(capacity: dict[tuple[str, str, str], int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for cell in CELL_QUOTAS:
        available = capacity.get((cell["predicate_family"], cell["predicate_label"], cell["queue_kind"]), 0)
        row = {
            **cell,
            "available_queue_rows": available,
            "quota_feasible": available >= cell["target_rows"],
            "queue_kind_label_policy": "sampling_axis_only_not_target_label",
            "labeler_visible": False,
            "posterior_input_allowed": False,
        }
        if available < cell["target_rows"]:
            errors.append(
                {
                    "error_type": "cell_quota_exceeds_capacity",
                    "cell_id": cell["cell_id"],
                    "target_rows": cell["target_rows"],
                    "available_queue_rows": available,
                }
            )
        rows.append(row)
    return rows, errors


def target_schema() -> dict[str, Any]:
    return {
        "schema_version": "h002_v14_physical_relation_family_sampling_target_schema_v1",
        "target_queue_rows": sum(row["target_rows"] for row in CELL_QUOTAS),
        "primary_anchor_rows": sum(row["target_rows"] for row in CELL_QUOTAS if row["row_role"] in {"primary_anchor", "limited_primary_diversity"}),
        "control_rows": sum(row["target_rows"] for row in CELL_QUOTAS if row["row_role"] == "control_family"),
        "target_family_roles": {
            "support_contact": "primary_anchor",
            "relative_vertical": "control_family",
            "attachment_deferred": "schema_probe_only_deferred",
        },
        "primary_review_states": {
            "accept_reliable": "relation is reliable enough for graph use under visible evidence",
            "reject_unreliable": "relation should not be trusted under visible evidence",
            "abstain_uncertain": "evidence is insufficient, ambiguous, or endpoint/predicate identity is unclear",
        },
        "auxiliary_review_axes": {
            "geometry_support_state": ["supports", "contradicts", "ambiguous", "not_evaluable"],
            "relation_usefulness_state": ["useful_nontrivial", "trivial_or_redundant", "not_a_relation", "uncertain"],
            "endpoint_identity_state": ["clear", "uncertain", "wrong_endpoint", "not_evaluable"],
            "coverage_state": ["sufficient", "limited", "missing", "not_evaluable"],
        },
        "not_target_labels": [
            "queue_kind",
            "semantic_geometry_bucket",
            "rank_band",
            "machine_hint",
            "label_match_status",
            "p_geom_valid bin",
            "geometry_status",
        ],
        "target_policy": (
            "HL/LH buckets are used only to sample semantic-geometry disagreement cases. "
            "The reliability target must be assigned from reviewer-visible evidence and audited separately."
        ),
    }


def mining_policy() -> dict[str, Any]:
    return {
        "schema_version": "h002_v14_physical_relation_family_mining_policy_v1",
        "input_queues": {
            "HL": rel_path(RGA_ROOT / "train_hl_queue.jsonl"),
            "LH": rel_path(RGA_ROOT / "train_lh_queue.jsonl"),
            "match_rows": rel_path(RGA_ROOT / "match_rows.jsonl"),
        },
        "hard_filters": [
            "train-only rows only",
            "predicate_family/predicate_label/queue_kind must match one quota cell",
            "exclude attachment_deferred until witness schema exists",
            "exclude exact duplicate prediction_id",
            "exclude duplicate directed endpoint pair across the 240-row sheet unless explicitly reserved as a diagnostic pair",
            "for support_contact, exclude hard room surfaces as subject labels: floor, wall, ceiling",
            "for support_contact, exclude object label wall/ceiling in the primary quota; floor is allowed only as object/support surface",
            "for relative_vertical, exclude rows where both endpoints are hard room surfaces",
        ],
        "soft_caps": {
            "max_rows_per_scan": 6,
            "max_rows_per_subgraph": 3,
            "max_rows_per_directed_endpoint_pair": 1,
            "max_rows_per_subject_object_label_pair": 8,
            "max_rows_per_subject_label": 24,
            "max_rows_per_object_label": 30,
            "max_rows_with_any_hard_room_surface_endpoint": 48,
            "max_rows_with_floor_as_object": 32,
            "max_rows_per_quota_cell_from_one_scan": 2,
        },
        "fallback_order_if_quota_fails_after_filters": [
            "relax max_rows_with_floor_as_object from 32 to 48",
            "relax max_rows_per_subject_object_label_pair from 8 to 12",
            "relax support_contact object wall exclusion only for reject-enriched diagnostic rows",
            "reduce standing-on HL quota before adding unsupported or LH-only predicates",
            "do not fill deficits with attachment_deferred or proximity",
        ],
        "selection_tiebreakers": [
            "prefer rows with complete raw geometry join",
            "prefer larger distance from rank/geometry threshold boundary within the same quota cell",
            "prefer diverse scans and object-label pairs",
            "prefer non-structural endpoints after quota and family constraints",
            "stable hash of prediction_id",
        ],
        "forbidden_selection_tiebreakers": [
            "known or proxy reliability label",
            "label_match_status as a target proxy",
            "machine_hint as a target proxy",
            "validation or test performance",
            "posterior model score",
            "multi-view evidence as model input",
        ],
    }


def label_surface_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_v14_physical_relation_family_label_surface_contract_v1",
        "visible_fields": [
            "blind_review_id",
            "candidate_relation",
            "subject_label",
            "predicate_label",
            "object_label",
            "scene_context_summary",
            "geometry_witness_summary",
            "support_or_vertical_witness_summary",
            "coverage_summary",
            "endpoint_identity_summary",
            "review_question",
            "relation_reliability_state",
            "geometry_support_state",
            "relation_usefulness_state",
            "primary_reason",
            "uncertainty_reason",
            "review_notes",
        ],
        "hidden_audit_fields": [
            "queue_kind",
            "semantic_geometry_bucket",
            "semantic_rank",
            "rank_band",
            "semantic_score_norm",
            "p_geom_valid",
            "geometry_status",
            "machine_hint",
            "label_match_status",
            "matched_predicates",
            "source_queue_path",
            "prediction_id",
        ],
        "forbidden_visible_patterns": [
            "HL",
            "LH",
            "RGA-",
            "semantic_rank",
            "rank_band",
            "machine_hint",
            "label_match_status",
            "p_geom_valid",
            "posterior",
            "exact_match",
            "pair_has_other_predicate",
        ],
        "multi_view_policy": "audit/confirmation evidence only; not deployable posterior input at this stage",
    }


def independence_gate() -> dict[str, Any]:
    return {
        "schema_version": "h002_v14_physical_relation_family_independence_gate_v1",
        "posterior_smoke_allowed_initially": False,
        "post_label_requirements": {
            "minimum_binary_rows": 100,
            "minimum_accept_reliable": 50,
            "minimum_reject_unreliable": 50,
            "strict_or_diagnostic_clear_slice_required": True,
            "same_family_same_predicate_controls_required": True,
            "same_geometry_status_controls_required": True,
            "same_rank_band_controls_required": True,
            "quick_probe_shortcut_audit_required": True,
        },
        "blocked_if": [
            "reliability label is predictable from predicate_label alone",
            "reliability label is predictable from queue_kind alone",
            "reliability label is predictable from object label pair alone",
            "support_contact result is dominated by floor/wall/ceiling endpoint shortcuts",
            "relative_vertical control alone explains posterior gains",
            "class mass remains below minimum accept/reject counts",
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 V14 Physical Relation-Family Sampling Plan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Decision",
        "",
        "`support_contact` is selected as the primary anchor, `relative_vertical` is retained as a control family, and `attachment_deferred` remains deferred until a witness schema exists.",
        "",
        "```text",
        f"target_queue_rows = {summary['target_schema']['target_queue_rows']}",
        f"primary_anchor_rows = {summary['target_schema']['primary_anchor_rows']}",
        f"control_rows = {summary['target_schema']['control_rows']}",
        f"next_todo = {summary['next_todo']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Quota Cells",
        "",
        "| Cell | Family | Predicate | Queue | Rows | Available | Role |",
        "| --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in summary["cell_quotas"]:
        lines.append(
            f"| `{row['cell_id']}` | `{row['predicate_family']}` | `{row['predicate_label']}` | "
            f"`{row['queue_kind']}` | {row['target_rows']} | {row['available_queue_rows']} | `{row['row_role']}` |"
        )
    lines.extend(
        [
            "",
            "## Excluded Cells",
            "",
            "| Family | Predicate | Queue | Reason |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in summary["excluded_cells"]:
        lines.append(f"| `{row['predicate_family']}` | `{row['predicate_label']}` | `{row['queue_kind']}` | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            "HL/LH is a sampling axis, not a reliability label. Candidate mining may use hidden queue fields for quota control, but label fill and posterior inputs must not expose them.",
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    feasibility_dir = as_abs(args.feasibility_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    feasibility = read_json(feasibility_dir / "summary.json")
    validation_errors = validate_upstream(feasibility, args)
    predicate_inventory = read_csv(feasibility_dir / "predicate_inventory.csv")
    capacity = load_capacity(predicate_inventory)
    quota_rows, quota_errors = cell_quota_rows(capacity)
    validation_errors.extend(quota_errors)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "cell_quotas": output_dir / "cell_quotas.csv",
        "excluded_cells": output_dir / "excluded_cells.csv",
        "target_schema": output_dir / "target_schema.json",
        "mining_policy": output_dir / "mining_policy.json",
        "label_surface_contract": output_dir / "label_surface_contract.json",
        "independence_gate": output_dir / "independence_gate.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    target = target_schema()
    mining = mining_policy()
    label_surface = label_surface_contract()
    gate = independence_gate()
    status = STATUS_READY if not validation_errors else STATUS_ERRORS
    summary = {
        "schema_version": "h002_reliability_target_v14_physical_relation_family_sampling_plan_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "feasibility_summary": rel_path(feasibility_dir / "summary.json"),
            "predicate_inventory": rel_path(feasibility_dir / "predicate_inventory.csv"),
            "queue_inventory": rel_path(feasibility_dir / "queue_inventory.csv"),
            "route_matrix": rel_path(feasibility_dir / "route_matrix.jsonl"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "selected_route": "support_contact_primary_anchor_relative_vertical_control",
        "cell_quotas": quota_rows,
        "excluded_cells": EXCLUDED_CELLS,
        "target_schema": target,
        "mining_policy": mining,
        "label_surface_contract": label_surface,
        "independence_gate": gate,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
            "hidden_fields_as_model_input": False,
        },
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO_READY if not validation_errors else NEXT_TODO_BLOCKED,
    }

    write_csv(output_paths["cell_quotas"], quota_rows)
    write_csv(output_paths["excluded_cells"], EXCLUDED_CELLS)
    write_json(output_paths["target_schema"], target)
    write_json(output_paths["mining_policy"], mining)
    write_json(output_paths["label_surface_contract"], label_surface)
    write_json(output_paths["independence_gate"], gate)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"selected_route={summary['selected_route']}")
    print(f"target_queue_rows={summary['target_schema']['target_queue_rows']}")
    print(f"primary_anchor_rows={summary['target_schema']['primary_anchor_rows']}")
    print(f"control_rows={summary['target_schema']['control_rows']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
