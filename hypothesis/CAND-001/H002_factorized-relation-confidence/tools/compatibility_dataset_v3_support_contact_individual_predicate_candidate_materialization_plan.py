#!/usr/bin/env python3
"""Write a route-aware materialization plan for individual support/contact predicates."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_INVENTORY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_source_inventory"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan"
)

EXPECTED_INVENTORY_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_source_inventory_ready_for_candidate_materialization_plan"
)
EXPECTED_INVENTORY_NEXT = "compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan_ready"
)
STATUS_ERROR = "h002_compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan_input_errors"
SELECTED_PATH = "materialize_route_aware_standing_lying_candidates_with_supported_by_diagnostic"
NEXT_TODO = "compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization"

STANDING_ACCEPT = 160
STANDING_REJECT = 160
LYING_ACCEPT = 160
LYING_REJECT = 160
SUPPORTED_ACCEPT_DIAG = 40
SUPPORTED_REJECT_DIAG = 40
SUPPORTED_OVERLAP_ABSTAIN_DIAG = 80

MAX_ROWS_PER_SCAN = 20
MAX_ROWS_PER_PREDICATE_CLASS_PAIR = 32
MAX_ROWS_PER_PREDICATE_CLASS_PAIR_RANK = 24
MAX_ROWS_PER_DIRECTED_PAIR = 2
MAX_HARD_SURFACE_ROWS = 360


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-dir", type=Path, default=DEFAULT_INVENTORY_DIR)
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
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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


def as_int(row: dict[str, str], key: str) -> int:
    try:
        return int(row.get(key, "0"))
    except ValueError:
        return 0


def as_bool(row: dict[str, str], key: str) -> bool:
    return str(row.get(key, "")).lower() == "true"


def by_key(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows if key in row}


def validate_inputs(
    inventory_summary: dict[str, Any],
    inventory_errors: list[dict[str, Any]],
    predicate_rows: list[dict[str, str]],
    cell_rows: list[dict[str, str]],
    anchor_rows: list[dict[str, str]],
    source_availability_rows: list[dict[str, str]],
    inventory_dir: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if inventory_summary.get("status") != EXPECTED_INVENTORY_STATUS:
        errors.append({"error_type": "unexpected_inventory_status", "actual": inventory_summary.get("status")})
    if inventory_summary.get("next_todo") != EXPECTED_INVENTORY_NEXT:
        errors.append({"error_type": "unexpected_inventory_next", "actual": inventory_summary.get("next_todo")})
    if inventory_summary.get("validation_errors") != 0:
        errors.append({"error_type": "inventory_validation_errors_present", "actual": inventory_summary.get("validation_errors")})
    if inventory_errors:
        errors.append({"error_type": "inventory_validation_error_rows_present", "rows": len(inventory_errors)})
    if inventory_summary.get("source_summary", {}).get("primary_ready") is not True:
        errors.append(
            {
                "error_type": "inventory_primary_not_ready",
                "actual": inventory_summary.get("source_summary", {}).get("primary_ready"),
            }
        )
    if inventory_summary.get("source_summary", {}).get("supported_by_role") != "diagnostic_superordinate":
        errors.append(
            {
                "error_type": "unexpected_supported_by_role",
                "actual": inventory_summary.get("source_summary", {}).get("supported_by_role"),
            }
        )
    boundary = inventory_summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "materializes_rows",
        "fills_labels",
        "runs_learned_smoke",
        "trains_new_model",
        "paper_evidence_allowed",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "inventory_boundary_not_false", "key": key, "actual": boundary.get(key)})

    pred = by_key(predicate_rows, "predicate_label")
    for predicate, min_balanced in [("standing on", 320), ("lying on", 320), ("supported by", 120)]:
        row = pred.get(predicate)
        if not row:
            errors.append({"error_type": "missing_predicate_inventory_row", "predicate": predicate})
            continue
        if not as_bool(row, "source_inventory_ready"):
            errors.append({"error_type": "predicate_not_inventory_ready", "predicate": predicate})
        if as_int(row, "class_pair_balanced_rows") < min_balanced:
            errors.append(
                {
                    "error_type": "class_pair_capacity_too_small",
                    "predicate": predicate,
                    "actual": as_int(row, "class_pair_balanced_rows"),
                    "required": min_balanced,
                }
            )

    cell_by_predicate_axis = {(row["predicate_label"], row["axis"]): row for row in cell_rows}
    for predicate, required in [("standing on", 320), ("lying on", 320)]:
        row = cell_by_predicate_axis.get((predicate, "class_pair_x_rank_band"))
        if not row or as_int(row, "balanced_rows") < required:
            errors.append(
                {
                    "error_type": "class_pair_rank_capacity_too_small",
                    "predicate": predicate,
                    "actual": as_int(row or {}, "balanced_rows"),
                    "required": required,
                }
            )

    anchor_by_type = by_key(anchor_rows, "anchor_type")
    if as_int(anchor_by_type.get("predicted_same_pair_standing_and_lying", {}), "pairs") < 1000:
        errors.append(
            {
                "error_type": "same_geometry_anchor_capacity_too_small",
                "actual": as_int(anchor_by_type.get("predicted_same_pair_standing_and_lying", {}), "pairs"),
            }
        )

    if source_availability_rows:
        missing = [row for row in source_availability_rows if str(row.get("all_required_sources_exist", "")).lower() != "true"]
        if missing:
            errors.append({"error_type": "source_availability_missing", "rows": len(missing)})
    else:
        errors.append({"error_type": "missing_source_availability_rows"})

    for name in [
        "summary.json",
        "predicate_source_inventory.csv",
        "controlled_cell_capacity.csv",
        "same_geometry_anchor_capacity.csv",
        "source_availability.csv",
        "shortcut_capacity_audit.csv",
    ]:
        path = inventory_dir / name
        if not path.exists():
            errors.append({"error_type": "missing_inventory_artifact", "path": rel_path(path)})
    return errors


def evidence_route_table() -> list[dict[str, Any]]:
    return [
        {
            "predicate_label": "standing on",
            "route_name": "support_contact_upright_compatibility_route",
            "route_role": "main_learned_target_candidate",
            "route_factors": "T_e + G_e + C_e + Q_e",
            "positive_role": "clear_accept",
            "negative_role": "hard_reject_lying_like",
            "target_use": "main C_e; later p_rel only after audit",
            "reason": "upright support/contact requires predicate-conditioned interpretation of contact and pose evidence",
        },
        {
            "predicate_label": "lying on",
            "route_name": "support_contact_lying_compatibility_route",
            "route_role": "secondary_learned_target_candidate",
            "route_factors": "T_e + G_e + C_e + Q_e",
            "positive_role": "clear_accept",
            "negative_role": "hard_reject_standing_like",
            "target_use": "main/secondary C_e; paired with standing on where possible",
            "reason": "lying support/contact differs from standing support/contact by pose-conditioned geometry compatibility",
        },
        {
            "predicate_label": "supported by",
            "route_name": "support_superordinate_diagnostic_route",
            "route_role": "diagnostic_only",
            "route_factors": "G_e + Q_e; C_e diagnostic only",
            "positive_role": "clear_accept",
            "negative_role": "hard_reject_no_support",
            "target_use": "diagnostic/Q_e/taxonomy; excluded from main binary learned target",
            "reason": "supported by can be true together with standing/lying support states, so it is not a clean binary negative",
        },
    ]


def quota_plan() -> list[dict[str, Any]]:
    rows = [
        {
            "subset": "main_compatibility",
            "predicate_label": "standing on",
            "route_name": "support_contact_upright_compatibility_route",
            "candidate_role": "clear_accept",
            "label_C_e": 1,
            "quota": STANDING_ACCEPT,
            "model_use": "main_train_candidate_if_schema_audit_passes",
        },
        {
            "subset": "main_compatibility",
            "predicate_label": "standing on",
            "route_name": "support_contact_upright_compatibility_route",
            "candidate_role": "hard_reject_lying_like",
            "label_C_e": 0,
            "quota": STANDING_REJECT,
            "model_use": "main_train_candidate_if_schema_audit_passes",
        },
        {
            "subset": "main_compatibility",
            "predicate_label": "lying on",
            "route_name": "support_contact_lying_compatibility_route",
            "candidate_role": "clear_accept",
            "label_C_e": 1,
            "quota": LYING_ACCEPT,
            "model_use": "main_train_candidate_if_schema_audit_passes",
        },
        {
            "subset": "main_compatibility",
            "predicate_label": "lying on",
            "route_name": "support_contact_lying_compatibility_route",
            "candidate_role": "hard_reject_standing_like",
            "label_C_e": 0,
            "quota": LYING_REJECT,
            "model_use": "main_train_candidate_if_schema_audit_passes",
        },
        {
            "subset": "supported_by_diagnostic",
            "predicate_label": "supported by",
            "route_name": "support_superordinate_diagnostic_route",
            "candidate_role": "clear_accept",
            "label_C_e": "diagnostic_accept",
            "quota": SUPPORTED_ACCEPT_DIAG,
            "model_use": "diagnostic_only",
        },
        {
            "subset": "supported_by_diagnostic",
            "predicate_label": "supported by",
            "route_name": "support_superordinate_diagnostic_route",
            "candidate_role": "hard_reject_no_support",
            "label_C_e": "diagnostic_reject",
            "quota": SUPPORTED_REJECT_DIAG,
            "model_use": "diagnostic_only",
        },
        {
            "subset": "supported_by_diagnostic",
            "predicate_label": "supported by",
            "route_name": "support_superordinate_diagnostic_route",
            "candidate_role": "overlap_or_abstain",
            "label_C_e": "abstain_or_overlap",
            "quota": SUPPORTED_OVERLAP_ABSTAIN_DIAG,
            "model_use": "diagnostic_only",
        },
    ]
    rows.append(
        {
            "subset": "planned_total",
            "predicate_label": "all",
            "route_name": "all",
            "candidate_role": "summary",
            "label_C_e": "",
            "quota": sum(int(row["quota"]) for row in rows),
            "model_use": "summary",
        }
    )
    return rows


def sampling_caps() -> list[dict[str, Any]]:
    return [
        {
            "cap_axis": "scan_id",
            "max_rows": MAX_ROWS_PER_SCAN,
            "applies_to": "all rows",
            "reason": "avoid scan memorization",
        },
        {
            "cap_axis": "predicate_label + subject_object_class_pair",
            "max_rows": MAX_ROWS_PER_PREDICATE_CLASS_PAIR,
            "applies_to": "main compatibility rows",
            "reason": "avoid class-pair target shortcut while preserving mixed class-pair cells",
        },
        {
            "cap_axis": "predicate_label + subject_object_class_pair + rank_band",
            "max_rows": MAX_ROWS_PER_PREDICATE_CLASS_PAIR_RANK,
            "applies_to": "main compatibility rows",
            "reason": "avoid rank/source shortcut inside class-pair cells",
        },
        {
            "cap_axis": "directed_pair_id",
            "max_rows": MAX_ROWS_PER_DIRECTED_PAIR,
            "applies_to": "all rows",
            "reason": "avoid endpoint pair memorization",
        },
        {
            "cap_axis": "hard_surface_pair",
            "max_rows": MAX_HARD_SURFACE_ROWS,
            "applies_to": "all rows",
            "reason": "hard-surface rows are about 69-71% in source pools, so materialization must cap them",
        },
    ]


def model_view_contract() -> list[dict[str, Any]]:
    return [
        {
            "view": "T_only",
            "allowed_fields": "predicate text/label, relation family, subject/object class text",
            "blocked_fields": "source score/rank, raw geometry, hidden construction fields",
            "purpose": "semantic-content baseline",
        },
        {
            "view": "Z_only",
            "allowed_fields": "source confidence availability, source score/rank only for baseline",
            "blocked_fields": "geometry, target labels, hidden construction fields",
            "purpose": "source-confidence shortcut baseline",
        },
        {
            "view": "G_only",
            "allowed_fields": "contact/support/pose/mesh geometry evidence without predicate label",
            "blocked_fields": "predicate label, source confidence, target role",
            "purpose": "predicate-independent geometry baseline",
        },
        {
            "view": "T_plus_G_compatibility",
            "allowed_fields": "T_e + G_e interaction, route family safe token",
            "blocked_fields": "Z_e, queue kind, label_match_status, construction role, p_geom_valid",
            "purpose": "main C_e learned view if shortcut audit passes",
        },
        {
            "view": "T_plus_G_plus_Q",
            "allowed_fields": "T_e + G_e + evidence availability and missingness mask",
            "blocked_fields": "Z_e for C_e, source rank, hidden target fields",
            "purpose": "observability-aware compatibility diagnostic",
        },
        {
            "view": "route_rule_baseline",
            "allowed_fields": "relation-family route id and rule-selected factor mask",
            "blocked_fields": "target labels and hidden construction fields",
            "purpose": "tests relation-aware routing against fixed fusion",
        },
    ]


def blocked_fields() -> list[dict[str, Any]]:
    blocked = [
        ("prediction_id", "identity/source", "row identity shortcut"),
        ("scan_id", "identity/control", "scan memorization"),
        ("subgraph_id", "identity/control", "scene graph identity shortcut"),
        ("subject_id", "identity/control", "instance shortcut"),
        ("object_id", "identity/control", "instance shortcut"),
        ("directed_pair_id", "identity/control", "endpoint pair memorization"),
        ("queue_kind", "source construction", "HL/LH cannot be model input"),
        ("label_match_status", "GT/source join", "target construction leakage"),
        ("matched_gt_ids", "GT/source join", "GT leakage"),
        ("matched_predicates", "GT/source join", "target construction leakage"),
        ("candidate_role", "target construction", "direct label leakage"),
        ("route_name", "allowed only as route-rule baseline", "not a learned C_e feature unless route baseline explicitly evaluated"),
        ("semantic_rank", "source confidence", "Z_e baseline only, excluded from C_e"),
        ("rank_band", "source confidence", "Z_e baseline and audit only"),
        ("semantic_score_raw", "source confidence", "Z_e baseline and final reliability only, not C_e"),
        ("semantic_score_norm", "source confidence", "Z_e baseline and final reliability only, not C_e"),
        ("geometry_status", "legacy geometry status", "hidden audit only"),
        ("h001_verification_status", "legacy geometry status", "hidden audit only"),
        ("p_geom_valid", "legacy H001 rule", "baseline-only, not main G_e"),
    ]
    return [{"field": field, "source": source, "reason": reason, "model_safe": False} for field, source, reason in blocked]


def shortcut_audit_plan() -> list[dict[str, Any]]:
    return [
        {
            "audit": "predicate_only",
            "target": "C_e",
            "required": True,
            "failure_action": "block learned smoke if predicate alone solves target",
        },
        {
            "audit": "class_pair_only",
            "target": "C_e",
            "required": True,
            "failure_action": "repair sampling or freeze diagnostic",
        },
        {
            "audit": "rank_source_only",
            "target": "C_e",
            "required": True,
            "failure_action": "remove source fields and rebalance",
        },
        {
            "audit": "hard_surface_only",
            "target": "C_e",
            "required": True,
            "failure_action": "tighten hard-surface cap or stratify reporting",
        },
        {
            "audit": "G_only",
            "target": "C_e",
            "required": True,
            "failure_action": "interpret as geometry-easy target unless T+G beats controls with wrong-T/shuffle controls",
        },
        {
            "audit": "wrong_T",
            "target": "C_e",
            "required": True,
            "failure_action": "block compatibility claim if wrong predicate does not degrade",
        },
        {
            "audit": "shuffled_G",
            "target": "C_e",
            "required": True,
            "failure_action": "block compatibility claim if shuffled geometry does not degrade",
        },
        {
            "audit": "route_rule_vs_fixed_fusion",
            "target": "route-aware framing",
            "required": True,
            "failure_action": "do not claim adaptive routing; keep fixed-route diagnostic",
        },
    ]


def materialization_gates(quota_rows: list[dict[str, Any]], predicate_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    pred = by_key(predicate_rows, "predicate_label")
    total = sum(int(row["quota"]) for row in quota_rows if row["subset"] != "planned_total")
    return [
        {
            "gate": "standing_class_pair_capacity",
            "value": as_int(pred["standing on"], "class_pair_balanced_rows"),
            "required": STANDING_ACCEPT + STANDING_REJECT,
            "passed": as_int(pred["standing on"], "class_pair_balanced_rows") >= STANDING_ACCEPT + STANDING_REJECT,
        },
        {
            "gate": "lying_class_pair_capacity",
            "value": as_int(pred["lying on"], "class_pair_balanced_rows"),
            "required": LYING_ACCEPT + LYING_REJECT,
            "passed": as_int(pred["lying on"], "class_pair_balanced_rows") >= LYING_ACCEPT + LYING_REJECT,
        },
        {
            "gate": "supported_by_diagnostic_capacity",
            "value": as_int(pred["supported by"], "class_pair_balanced_rows"),
            "required": SUPPORTED_ACCEPT_DIAG + SUPPORTED_REJECT_DIAG,
            "passed": as_int(pred["supported by"], "class_pair_balanced_rows") >= SUPPORTED_ACCEPT_DIAG + SUPPORTED_REJECT_DIAG,
        },
        {
            "gate": "planned_total_rows",
            "value": total,
            "required": 800,
            "passed": total == 800,
        },
        {
            "gate": "supported_by_not_main_target",
            "value": "diagnostic_only",
            "required": "diagnostic_only",
            "passed": True,
        },
    ]


def route_aware_contract() -> dict[str, Any]:
    return {
        "contract_name": "h002_route_aware_support_contact_materialization_plan_v1",
        "purpose": (
            "Materialize only compatibility-ready support/contact predicates as main learned-target candidates, "
            "while preserving superordinate supported-by rows as diagnostic evidence."
        ),
        "main_learned_target_candidates": ["standing on", "lying on"],
        "diagnostic_predicates": ["supported by"],
        "relation_aware_routing_principle": (
            "Relation family and evidence availability determine the factor route before factor fusion. "
            "This materialization does not assume one fixed fusion formula for all predicates."
        ),
        "factor_boundary": {
            "T_e": "predicate/object semantic content",
            "Z_e": "source confidence; baseline/final reliability only, excluded from C_e",
            "G_e": "predicate-independent contact/support/pose/mesh geometry evidence",
            "C_e": "compatibility(T_e, G_e)",
            "Q_e": "observability and evidence quality",
        },
        "learning_blocked_until": [
            "candidate rows are materialized",
            "model-safe and hidden views are separated",
            "schema/shortcut audit passes",
        ],
    }


def route_decision() -> list[dict[str, Any]]:
    return [
        {
            "route": "standing_on_main_compatibility_materialization",
            "verdict": "selected",
            "quota": STANDING_ACCEPT + STANDING_REJECT,
            "reason": "source inventory has enough clear accept and lying-like hard reject capacity",
        },
        {
            "route": "lying_on_main_compatibility_materialization",
            "verdict": "selected",
            "quota": LYING_ACCEPT + LYING_REJECT,
            "reason": "source inventory has enough clear accept and standing-like hard reject capacity",
        },
        {
            "route": "supported_by_main_binary_materialization",
            "verdict": "rejected",
            "quota": 0,
            "reason": "supported by is superordinate and remains diagnostic even though source capacity exists",
        },
        {
            "route": "supported_by_diagnostic_materialization",
            "verdict": "selected_diagnostic",
            "quota": SUPPORTED_ACCEPT_DIAG + SUPPORTED_REJECT_DIAG + SUPPORTED_OVERLAP_ABSTAIN_DIAG,
            "reason": "preserve support/contact taxonomy boundary and Q_e/abstain evidence",
        },
    ]


def write_report(path: Path, summary: dict[str, Any], quota_rows: list[dict[str, Any]], gates: list[dict[str, Any]]) -> None:
    lines = [
        "# H002 Support/Contact Individual Predicate Candidate Materialization Plan",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Route-Aware Decision",
        "",
        "`standing on` and `lying on` are materialized as compatibility-ready main candidates. `supported by` is diagnostic only.",
        "",
        "## Quota",
        "",
        "| Subset | Predicate | Role | C_e | Quota | Use |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for row in quota_rows:
        if row["subset"] == "planned_total":
            continue
        lines.append(
            "| "
            f"{row['subset']} | `{row['predicate_label']}` | {row['candidate_role']} | "
            f"{row['label_C_e']} | {row['quota']} | {row['model_use']} |"
        )
    lines.extend(
        [
            "",
            "## Gates",
            "",
            "| Gate | Value | Required | Passed |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    for row in gates:
        lines.append(f"| `{row['gate']}` | {row['value']} | {row['required']} | {row['passed']} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only materialization plan.",
            "- No row materialization yet.",
            "- No labels are filled.",
            "- No learned smoke or model training.",
            "- No validation/test usage.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    inventory_summary_path = args.inventory_dir / "summary.json"
    inventory_summary = read_json(inventory_summary_path) if inventory_summary_path.exists() else {}
    inventory_errors = read_jsonl(args.inventory_dir / "validation_errors.jsonl")
    predicate_rows = read_csv(args.inventory_dir / "predicate_source_inventory.csv")
    cell_rows = read_csv(args.inventory_dir / "controlled_cell_capacity.csv")
    anchor_rows = read_csv(args.inventory_dir / "same_geometry_anchor_capacity.csv")
    source_availability_rows = read_csv(args.inventory_dir / "source_availability.csv")

    validation_errors = validate_inputs(
        inventory_summary,
        inventory_errors,
        predicate_rows,
        cell_rows,
        anchor_rows,
        source_availability_rows,
        args.inventory_dir,
    )
    quota_rows = quota_plan()
    gate_rows = materialization_gates(quota_rows, predicate_rows) if not validation_errors else []
    if any(row.get("passed") is False for row in gate_rows):
        validation_errors.extend(
            {
                "error_type": "materialization_gate_failed",
                "gate": row["gate"],
                "value": row["value"],
                "required": row["required"],
            }
            for row in gate_rows
            if row.get("passed") is False
        )

    status = STATUS_ERROR if validation_errors else STATUS_READY
    selected_path = "blocked_input_or_gate_errors" if validation_errors else SELECTED_PATH
    next_todo = EXPECTED_INVENTORY_NEXT if validation_errors else NEXT_TODO

    summary = {
        "boundary": {
            "fills_labels": False,
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_materialization_plan",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "source_inventory_summary": rel_path(inventory_summary_path),
            "predicate_source_inventory": rel_path(args.inventory_dir / "predicate_source_inventory.csv"),
            "controlled_cell_capacity": rel_path(args.inventory_dir / "controlled_cell_capacity.csv"),
            "same_geometry_anchor_capacity": rel_path(args.inventory_dir / "same_geometry_anchor_capacity.csv"),
        },
        "next_todo": next_todo,
        "output_paths": {
            "blocked_fields": rel_path(args.output_dir / "blocked_fields.csv"),
            "evidence_route_table": rel_path(args.output_dir / "evidence_route_table.csv"),
            "materialization_gates": rel_path(args.output_dir / "materialization_gates.csv"),
            "model_view_contract": rel_path(args.output_dir / "model_view_contract.csv"),
            "quota_plan": rel_path(args.output_dir / "quota_plan.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "route_aware_contract": rel_path(args.output_dir / "route_aware_contract.json"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "sampling_caps": rel_path(args.output_dir / "sampling_caps.csv"),
            "shortcut_audit_plan": rel_path(args.output_dir / "shortcut_audit_plan.csv"),
            "summary": rel_path(args.output_dir / "summary.json"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "planned_counts": {
            "main_compatibility_rows": STANDING_ACCEPT + STANDING_REJECT + LYING_ACCEPT + LYING_REJECT,
            "standing_on_rows": STANDING_ACCEPT + STANDING_REJECT,
            "lying_on_rows": LYING_ACCEPT + LYING_REJECT,
            "supported_by_diagnostic_rows": SUPPORTED_ACCEPT_DIAG + SUPPORTED_REJECT_DIAG + SUPPORTED_OVERLAP_ABSTAIN_DIAG,
            "total_rows": sum(int(row["quota"]) for row in quota_rows if row["subset"] != "planned_total"),
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "status": status,
        "validation_errors": len(validation_errors),
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "route_aware_contract.json", route_aware_contract())
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "evidence_route_table.csv", evidence_route_table())
    write_csv(args.output_dir / "quota_plan.csv", quota_rows)
    write_csv(args.output_dir / "sampling_caps.csv", sampling_caps())
    write_csv(args.output_dir / "model_view_contract.csv", model_view_contract())
    write_csv(args.output_dir / "blocked_fields.csv", blocked_fields())
    write_csv(args.output_dir / "shortcut_audit_plan.csv", shortcut_audit_plan())
    write_csv(args.output_dir / "route_decision.csv", route_decision())
    write_csv(args.output_dir / "materialization_gates.csv", gate_rows)
    write_report(args.output_dir / "report.md", summary, quota_rows, gate_rows)

    print(
        json.dumps(
            {
                "status": status,
                "selected_path": selected_path,
                "validation_errors": len(validation_errors),
                "next_todo": next_todo,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
