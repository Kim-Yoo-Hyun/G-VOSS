#!/usr/bin/env python3
"""Plan class-pair-balanced repair mining for R7 attachment observability."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
ARTIFACT_ROOT = H2_ROOT / "artifacts"
RGA_ROOT = ARTIFACT_ROOT / "train_rga_full/open3dsg_train_full/rga"

DEFAULT_PATH_DECISION_DIR = (
    ARTIFACT_ROOT / "compatibility_dataset_v3_attachment_observability_path_decision_after_schema_shortcut_audit"
)
DEFAULT_SOURCE_INVENTORY_DIR = ARTIFACT_ROOT / "compatibility_dataset_v3_attachment_observability_source_inventory"
DEFAULT_V20_DIR = RGA_ROOT / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan"
DEFAULT_V21_DIR = RGA_ROOT / "reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan"
DEFAULT_OUTPUT_DIR = ARTIFACT_ROOT / "compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan"

EXPECTED_PATH_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_path_decision_select_class_pair_balanced_repair_mining"
)
EXPECTED_PATH_NEXT = "compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan"
EXPECTED_SOURCE_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_source_inventory_ready_for_materialization_plan"
)

SCHEMA_VERSION = "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan_ready"
STATUS_ERROR = "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_mining_plan_input_errors"
SELECTED_PATH = "plan_exact_predicate_class_pair_capacity_scan_before_packet_mining"
NEXT_TODO = "compatibility_dataset_v3_attachment_observability_class_pair_repair_capacity_scan"

PRIMARY_PREDICATES = ["attached to", "hanging on"]
DIAGNOSTIC_PREDICATES = ["connected to"]
MIN_BALANCED_PRIMARY_ROWS = 400
MIN_POSITIVE_ROWS = 100
MIN_EXACT_MIXED_STRATA = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-decision-dir", type=Path, default=DEFAULT_PATH_DECISION_DIR)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
    parser.add_argument("--v20-dir", type=Path, default=DEFAULT_V20_DIR)
    parser.add_argument("--v21-dir", type=Path, default=DEFAULT_V21_DIR)
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
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def validate_inputs(
    path_summary: dict[str, Any],
    source_summary: dict[str, Any],
    v20_summary: dict[str, Any],
    v21_summary: dict[str, Any],
    path_dir: Path,
    source_dir: Path,
    v20_dir: Path,
    v21_dir: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if path_summary.get("status") != EXPECTED_PATH_STATUS:
        errors.append({"error_type": "unexpected_path_decision_status", "actual": path_summary.get("status")})
    if path_summary.get("next_todo") != EXPECTED_PATH_NEXT:
        errors.append({"error_type": "unexpected_path_decision_next", "actual": path_summary.get("next_todo")})
    if path_summary.get("validation_errors") != 0:
        errors.append({"error_type": "path_decision_validation_errors_present", "actual": path_summary.get("validation_errors")})
    if path_summary.get("selected_next_route") != "full_train_class_pair_balanced_repair_mining":
        errors.append({"error_type": "path_decision_not_repair_mining", "actual": path_summary.get("selected_next_route")})

    repair = path_summary.get("repair_capacity", {})
    if repair.get("current_exact_predicate_class_pair_p_obs_balanced_capacity") != 0:
        errors.append({"error_type": "unexpected_current_p_obs_capacity", "actual": repair})
    if repair.get("current_exact_predicate_class_pair_p_rel_balanced_capacity") != 0:
        errors.append({"error_type": "unexpected_current_p_rel_capacity", "actual": repair})

    if source_summary.get("status") != EXPECTED_SOURCE_STATUS:
        errors.append({"error_type": "unexpected_source_inventory_status", "actual": source_summary.get("status")})
    if source_summary.get("validation_errors") != 0:
        errors.append({"error_type": "source_inventory_validation_errors_present", "actual": source_summary.get("validation_errors")})

    rows_by_pred = source_summary.get("full_train_inventory", {}).get("rows_by_predicate", {})
    for predicate in PRIMARY_PREDICATES + DIAGNOSTIC_PREDICATES:
        if rows_by_pred.get(predicate, 0) < 100000:
            errors.append({"error_type": "full_train_predicate_capacity_low", "predicate": predicate, "actual": rows_by_pred.get(predicate)})

    if v20_summary.get("capacity_decision", {}).get("capacity_pass") is not True:
        errors.append({"error_type": "v20_capacity_not_passed", "actual": v20_summary.get("capacity_decision", {})})
    if v20_summary.get("boundary", {}).get("validation_usage") is not False:
        errors.append({"error_type": "v20_validation_usage_not_false"})
    if v21_summary.get("boundary", {}).get("validation_usage") is not False:
        errors.append({"error_type": "v21_validation_usage_not_false"})

    for name, root, required in [
        ("path_decision", path_dir, ["summary.json", "next_mining_contract.json"]),
        ("source_inventory", source_dir, ["summary.json", "full_train_top_class_pairs.csv", "route_readiness.csv"]),
        ("v20_capacity", v20_dir, ["summary.json", "capacity_by_predicate_role.csv", "exact_endpoint_pair_mixed_capacity.csv"]),
        ("v21_capacity", v21_dir, ["summary.json", "conditional_strata_capacity.csv"]),
    ]:
        for file_name in required:
            if not (root / file_name).exists():
                errors.append({"error_type": "missing_required_input", "source": name, "path": rel_path(root / file_name)})

    for name, summary in [
        ("path_decision", path_summary),
        ("source_inventory", source_summary),
        ("v20_capacity", v20_summary),
        ("v21_capacity", v21_summary),
    ]:
        boundary = summary.get("boundary", {})
        for key in ["h001_artifacts_modified", "test_usage", "validation_usage"]:
            if boundary.get(key) is not False:
                errors.append({"error_type": f"{name}_boundary_not_false", "key": key, "actual": boundary.get(key)})
    return errors


def int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def classify_seed_cell(predicate: str, class_pair: str) -> tuple[str, str]:
    subject, _, object_ = class_pair.partition("|")
    structural = {"wall", "ceiling", "doorframe", "door", "window", "shelf", "cabinet", "rack", "stand"}
    hangable = {"curtain", "towel", "clothes", "jacket", "bag", "backpack", "picture", "plant", "lamp", "light"}
    attachable = {"picture", "mirror", "frame", "door", "window", "light", "lamp", "heater", "radiator", "shelf", "cabinet"}
    confounds = {"floor", "chair", "pillow", "box"}
    if subject in confounds or object_ in confounds:
        return "negative_or_confound_seed", "floor/furniture/same-object confound likely useful for hard negatives"
    if predicate == "hanging on" and (subject in hangable or object_ in structural):
        return "positive_anchor_search_seed", "hangable subject or structural anchor appears in class pair"
    if predicate == "attached to" and (subject in attachable or object_ in structural):
        return "positive_anchor_search_seed", "attachable subject or structural anchor appears in class pair"
    if subject == object_:
        return "same_class_control_seed", "same-class pair should be controlled, not used as simple positive source"
    return "broad_capacity_seed", "large class-pair cell for exact-class repair scan"


def seed_cell_plan(top_class_pairs: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in top_class_pairs:
        predicate = row.get("predicate_label", "")
        if predicate not in PRIMARY_PREDICATES:
            continue
        class_pair = row.get("class_pair", "")
        role, reason = classify_seed_cell(predicate, class_pair)
        rows.append(
            {
                "predicate_label": predicate,
                "class_pair": class_pair,
                "full_train_rows": int_value(row.get("rows")),
                "seed_role": role,
                "reason": reason,
                "capacity_scan_use": "include_as_seed_but_require_accept_reject_mix",
            }
        )
    return sorted(rows, key=lambda item: (item["seed_role"], -item["full_train_rows"], item["predicate_label"], item["class_pair"]))


def quota_plan() -> list[dict[str, Any]]:
    return [
        {
            "quota_id": "R7A_attached_exact_class_pair_repair",
            "predicate_label": "attached to",
            "role": "primary_repair",
            "capacity_scan_min_mixed_strata": 10,
            "post_label_min_accept": 50,
            "post_label_min_reject": 100,
            "requested_packet_rows_if_capacity_passes": 240,
            "target_cell_type": "exact_predicate_x_subject_label_x_object_label",
            "notes": "Keep attached-to primary only if accepted positives survive within exact class-pair controls.",
        },
        {
            "quota_id": "R7H_hanging_exact_class_pair_repair",
            "predicate_label": "hanging on",
            "role": "primary_repair",
            "capacity_scan_min_mixed_strata": 10,
            "post_label_min_accept": 50,
            "post_label_min_reject": 100,
            "requested_packet_rows_if_capacity_passes": 240,
            "target_cell_type": "exact_predicate_x_subject_label_x_object_label",
            "notes": "Hanging-on can carry the observability route if exact-class balanced positives exist.",
        },
        {
            "quota_id": "R7C_connected_diagnostic",
            "predicate_label": "connected to",
            "role": "diagnostic_only",
            "capacity_scan_min_mixed_strata": 0,
            "post_label_min_accept": 0,
            "post_label_min_reject": 0,
            "requested_packet_rows_if_capacity_passes": 0,
            "target_cell_type": "topology_or_functional_evidence_required",
            "notes": "Do not promote without explicit topology/functional evidence.",
        },
    ]


def scan_contract(v20_summary: dict[str, Any], v21_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "input_rows": "artifacts/train_rga_full/open3dsg_train_full/rga/match_rows.jsonl",
        "selected_predicates": PRIMARY_PREDICATES,
        "diagnostic_predicates": DIAGNOSTIC_PREDICATES,
        "target_control_axis": "predicate_label + subject_label + object_label",
        "secondary_control_axes": [
            "rank_band",
            "scan_id cap",
            "geometry_bucket hidden selection only",
            "coverage_proxy hidden selection only",
            "object_family_pair fallback if exact label capacity fails",
        ],
        "proxy_roles_for_capacity_only": [
            "accept_proxy_supported_candidate",
            "reject_proxy_contradicted_candidate",
            "uncertain_proxy",
        ],
        "minimum_capacity_gates": {
            "balanced_primary_rows": MIN_BALANCED_PRIMARY_ROWS,
            "positive_rows": MIN_POSITIVE_ROWS,
            "exact_predicate_class_pair_mixed_strata": MIN_EXACT_MIXED_STRATA,
        },
        "do_not_use_as_model_input": [
            "proxy role",
            "geometry_bucket",
            "coverage_proxy",
            "rank_band",
            "source score",
            "source rank",
            "GT match status",
            "packet id",
            "review label",
        ],
        "prior_capacity_context": {
            "v20_exact_endpoint_pair_mixed_groups": v20_summary.get("contrast_capacity", {})
            .get("exact_endpoint_pair_summary", {})
            .get("mixed_groups"),
            "v20_exact_endpoint_pair_balanced_pair_capacity": v20_summary.get("contrast_capacity", {})
            .get("exact_endpoint_pair_summary", {})
            .get("balanced_pair_capacity"),
            "v21_same_predicate_rank_family_mixed_groups": _find_v21_spec(v21_summary, "same_predicate_rank_family").get("mixed_accept_reject_groups"),
            "v21_same_predicate_rank_family_balanced_capacity": _find_v21_spec(v21_summary, "same_predicate_rank_family").get("balanced_pair_capacity"),
            "v21_strict_rank_geometry_family_balanced_capacity": _find_v21_spec(v21_summary, "same_predicate_rank_geometry_family").get("balanced_pair_capacity"),
        },
    }


def _find_v21_spec(v21_summary: dict[str, Any], spec_name: str) -> dict[str, Any]:
    # v21 summary does not inline the CSV rows. This helper is filled by the caller through a cached key if present.
    return v21_summary.get("_spec_rows_by_name", {}).get(spec_name, {})


def field_boundary() -> dict[str, Any]:
    return {
        "model_safe_after_label_ingestion": [
            "T_e predicate/object semantic content",
            "G_e_attachment derived geometry evidence",
            "Q_e_observability derived evidence availability",
        ],
        "hidden_selection_only": [
            "source score",
            "source rank",
            "rank band",
            "proxy role",
            "geometry bucket",
            "coverage proxy",
            "GT label match status",
            "candidate cell id",
            "packet id and packet path",
        ],
        "labeler_visible": [
            "subject/object labels",
            "predicate label",
            "pair/multiview/mesh/contact packet",
            "minimal object ids needed to inspect the packet",
        ],
        "labeler_hidden": [
            "proxy role",
            "source confidence",
            "rank band",
            "GT match status",
            "previous review label",
            "construction bucket",
        ],
        "must_rerun_before_smoke": [
            "label ingestion",
            "schema leakage audit",
            "class-pair shortcut audit",
            "wrong-T and shuffled-G/Q controls",
        ],
    }


def route_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "route": "capacity_scan_exact_predicate_class_pair",
            "decision": "selected_next",
            "reason": "current artifact has zero exact predicate/class-pair mixed capacity but full train has enough candidate rows",
        },
        {
            "route": "candidate_mining_now_without_capacity_scan",
            "decision": "reject",
            "reason": "would repeat shortcut-prone sampling without knowing exact class-pair mixed capacity",
        },
        {
            "route": "family_pair_fallback",
            "decision": "fallback_only",
            "reason": "coarse family balancing may still leak exact class labels; use only if exact class-pair capacity fails and mark weaker",
        },
        {
            "route": "freeze_R7_diagnostic_now",
            "decision": "fallback_not_selected",
            "reason": "one targeted repair scan is still justified by full-train candidate capacity",
        },
        {
            "route": "connected_to_primary",
            "decision": "defer",
            "reason": "requires explicit topology or functional connection evidence",
        },
    ]


def enrich_v21_summary(v21_summary: dict[str, Any], rows: list[dict[str, str]]) -> dict[str, Any]:
    out = dict(v21_summary)
    out["_spec_rows_by_name"] = {}
    for row in rows:
        parsed: dict[str, Any] = {}
        for key, value in row.items():
            parsed[key] = int_value(value) if key in {"groups", "rows", "mixed_accept_reject_groups", "mixed_with_uncertain_groups", "balanced_pair_capacity", "groups_with_uncertain"} else value
        out["_spec_rows_by_name"][row.get("spec_name", "")] = parsed
    return out


def build_report(summary: dict[str, Any], quota_rows: list[dict[str, Any]], route_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# H002 R7 Attachment Observability Class-Pair Repair Mining Plan",
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
        "## Decision",
        "",
        "Plan one exact predicate x subject/object class-pair capacity scan before any packet mining or learned smoke.",
        "",
        "## Quotas",
        "",
        "| Quota | Predicate | Role | Requested Packet Rows | Post-label Accept Min | Post-label Reject Min |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in quota_rows:
        lines.append(
            f"| `{row['quota_id']}` | `{row['predicate_label']}` | `{row['role']}` | {row['requested_packet_rows_if_capacity_passes']} | {row['post_label_min_accept']} | {row['post_label_min_reject']} |"
        )
    lines.extend(["", "## Route Decisions", ""])
    for row in route_rows:
        lines.append(f"- `{row['route']}`: `{row['decision']}` - {row['reason']}")
    lines.extend(
        [
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    path_summary = read_json(args.path_decision_dir / "summary.json")
    source_summary = read_json(args.source_inventory_dir / "summary.json")
    v20_summary = read_json(args.v20_dir / "summary.json")
    v21_summary = enrich_v21_summary(
        read_json(args.v21_dir / "summary.json"),
        read_csv(args.v21_dir / "conditional_strata_capacity.csv"),
    )
    top_class_pairs = read_csv(args.source_inventory_dir / "full_train_top_class_pairs.csv")

    errors = validate_inputs(
        path_summary,
        source_summary,
        v20_summary,
        v21_summary,
        args.path_decision_dir,
        args.source_inventory_dir,
        args.v20_dir,
        args.v21_dir,
    )
    seeds = seed_cell_plan(top_class_pairs)
    quotas = quota_plan()
    scan = scan_contract(v20_summary, v21_summary)
    routes = route_decision_rows()

    status = STATUS_ERROR if errors else STATUS_READY
    next_todo = "fix_attachment_observability_class_pair_repair_mining_plan_inputs" if errors else NEXT_TODO
    selected_path = "fix_inputs" if errors else SELECTED_PATH
    output_paths = {
        "capacity_scan_contract": args.output_dir / "capacity_scan_contract.json",
        "field_boundary": args.output_dir / "field_boundary.json",
        "quota_plan": args.output_dir / "quota_plan.csv",
        "report": args.output_dir / "report.md",
        "route_decision": args.output_dir / "route_decision.csv",
        "seed_cell_plan": args.output_dir / "seed_cell_plan.csv",
        "summary": args.output_dir / "summary.json",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }
    summary = {
        "boundary": {
            "fills_labels": False,
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "packet_materialization_started": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_mining_plan",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "path_decision_summary": rel_path(args.path_decision_dir / "summary.json"),
            "source_inventory_summary": rel_path(args.source_inventory_dir / "summary.json"),
            "v20_capacity_summary": rel_path(args.v20_dir / "summary.json"),
            "v21_capacity_summary": rel_path(args.v21_dir / "summary.json"),
        },
        "next_todo": next_todo,
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "plan": {
            "diagnostic_predicates": DIAGNOSTIC_PREDICATES,
            "minimum_balanced_primary_rows": MIN_BALANCED_PRIMARY_ROWS,
            "minimum_exact_mixed_strata": MIN_EXACT_MIXED_STRATA,
            "minimum_positive_rows": MIN_POSITIVE_ROWS,
            "primary_predicates": PRIMARY_PREDICATES,
            "quota_rows": len(quotas),
            "seed_cells": len(seeds),
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "status": status,
        "validation_errors": len(errors),
    }

    write_json(output_paths["capacity_scan_contract"], scan)
    write_json(output_paths["field_boundary"], field_boundary())
    write_csv(output_paths["quota_plan"], quotas)
    write_csv(output_paths["route_decision"], routes)
    write_csv(output_paths["seed_cell_plan"], seeds)
    write_jsonl(output_paths["validation_errors"], errors)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(build_report(summary, quotas, routes), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
