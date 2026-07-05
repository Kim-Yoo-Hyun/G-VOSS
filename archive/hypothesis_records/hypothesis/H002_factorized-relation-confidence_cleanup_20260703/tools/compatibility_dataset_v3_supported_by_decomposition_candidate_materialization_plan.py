#!/usr/bin/env python3
"""Plan candidate materialization for R6 supported-by decomposition route."""

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

DEFAULT_TARGET_PLAN_DIR = ARTIFACT_ROOT / "compatibility_dataset_v3_supported_by_decomposition_target_plan"
DEFAULT_SOURCE_INVENTORY_DIR = (
    ARTIFACT_ROOT / "compatibility_dataset_v3_support_contact_individual_predicate_source_inventory"
)
DEFAULT_EXISTING_MATERIALIZATION_DIR = (
    ARTIFACT_ROOT / "compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization"
)
DEFAULT_OUTPUT_DIR = (
    ARTIFACT_ROOT / "compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan"
)

EXPECTED_TARGET_PLAN_STATUS = "h002_compatibility_dataset_v3_supported_by_decomposition_target_plan_ready"
EXPECTED_TARGET_PLAN_NEXT = "compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan"
EXPECTED_SOURCE_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_source_inventory_ready_for_candidate_materialization_plan"
)
EXPECTED_EXISTING_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_ready_for_schema_shortcut_audit"
)

SCHEMA_VERSION = "h002_compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan_input_errors"
SELECTED_PATH = "plan_320row_supported_by_decomposition_with_240row_min_viable_fallback"
NEXT_TODO = "compatibility_dataset_v3_supported_by_decomposition_candidate_materialization"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-plan-dir", type=Path, default=DEFAULT_TARGET_PLAN_DIR)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
    parser.add_argument("--existing-materialization-dir", type=Path, default=DEFAULT_EXISTING_MATERIALIZATION_DIR)
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
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def as_int(row: dict[str, str] | None, key: str) -> int:
    if not row:
        return 0
    try:
        return int(row.get(key, "0"))
    except ValueError:
        return 0


def by_key(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row.get(key, ""): row for row in rows if row.get(key)}


def validate_inputs(
    target_summary: dict[str, Any],
    source_summary: dict[str, Any],
    existing_summary: dict[str, Any],
    predicate_rows: list[dict[str, str]],
    role_rows: list[dict[str, str]],
    cell_rows: list[dict[str, str]],
    target_validation_rows: list[dict[str, Any]],
    source_validation_rows: list[dict[str, Any]],
    existing_validation_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []

    if target_summary.get("status") != EXPECTED_TARGET_PLAN_STATUS:
        errors.append({"error_type": "unexpected_target_plan_status", "actual": target_summary.get("status")})
    if target_summary.get("next_todo") != EXPECTED_TARGET_PLAN_NEXT:
        errors.append({"error_type": "unexpected_target_plan_next", "actual": target_summary.get("next_todo")})
    if target_summary.get("validation_errors") != 0 or target_validation_rows:
        errors.append(
            {
                "error_type": "target_plan_validation_errors_present",
                "summary_count": target_summary.get("validation_errors"),
                "rows": len(target_validation_rows),
            }
        )

    if source_summary.get("status") != EXPECTED_SOURCE_STATUS:
        errors.append({"error_type": "unexpected_source_inventory_status", "actual": source_summary.get("status")})
    if source_summary.get("validation_errors") != 0 or source_validation_rows:
        errors.append(
            {
                "error_type": "source_inventory_validation_errors_present",
                "summary_count": source_summary.get("validation_errors"),
                "rows": len(source_validation_rows),
            }
        )

    if existing_summary.get("status") != EXPECTED_EXISTING_STATUS:
        errors.append({"error_type": "unexpected_existing_materialization_status", "actual": existing_summary.get("status")})
    if existing_summary.get("validation_errors") != 0 or existing_validation_rows:
        errors.append(
            {
                "error_type": "existing_materialization_validation_errors_present",
                "summary_count": existing_summary.get("validation_errors"),
                "rows": len(existing_validation_rows),
            }
        )

    for name, summary in [
        ("target_plan", target_summary),
        ("source_inventory", source_summary),
        ("existing_materialization", existing_summary),
    ]:
        boundary = summary.get("boundary", {})
        for key in ["h001_artifacts_modified", "test_usage", "validation_usage"]:
            if boundary.get(key) is not False:
                errors.append(
                    {
                        "error_type": "boundary_not_false",
                        "source": name,
                        "key": key,
                        "actual": boundary.get(key),
                    }
                )

    pred = by_key(predicate_rows, "predicate_label")
    supported = pred.get("supported by")
    if not supported:
        errors.append({"error_type": "missing_supported_by_predicate_inventory"})
    else:
        if as_int(supported, "rows") < 50000:
            errors.append({"error_type": "supported_by_total_capacity_low", "actual": as_int(supported, "rows")})
        if as_int(supported, "class_pair_balanced_rows") < 160:
            errors.append(
                {
                    "error_type": "supported_by_class_pair_balanced_capacity_low",
                    "actual": as_int(supported, "class_pair_balanced_rows"),
                }
            )
        if as_int(supported, "class_pair_rank_balanced_rows") < 120:
            errors.append(
                {
                    "error_type": "supported_by_class_pair_rank_capacity_low",
                    "actual": as_int(supported, "class_pair_rank_balanced_rows"),
                }
            )

    role_lookup = {
        (row.get("predicate_label"), row.get("candidate_role")): row
        for row in role_rows
        if row.get("predicate_label") and row.get("candidate_role")
    }
    role_requirements = {
        "clear_accept": 240,
        "hard_reject_no_support": 1000,
        "overlap_or_abstain": 1000,
    }
    for role, minimum in role_requirements.items():
        actual = as_int(role_lookup.get(("supported by", role)), "rows")
        if actual < minimum:
            errors.append({"error_type": "supported_by_role_capacity_low", "role": role, "actual": actual, "minimum": minimum})

    cell_lookup = {
        (row.get("predicate_label"), row.get("axis")): row
        for row in cell_rows
        if row.get("predicate_label") and row.get("axis")
    }
    for axis, minimum in [("class_pair", 160), ("class_pair_x_rank_band", 120), ("scan_x_class_pair", 40)]:
        actual = as_int(cell_lookup.get(("supported by", axis)), "balanced_rows")
        if actual < minimum:
            errors.append({"error_type": "supported_by_cell_capacity_low", "axis": axis, "actual": actual, "minimum": minimum})

    existing_counts = existing_summary.get("counts", {})
    if existing_counts.get("predicate_counts", {}).get("supported by") != 160:
        errors.append(
            {
                "error_type": "unexpected_existing_supported_by_diagnostic_count",
                "actual": existing_counts.get("predicate_counts", {}).get("supported by"),
            }
        )

    return errors


def quota_plan_rows() -> list[dict[str, Any]]:
    return [
        {
            "route_label": "accept_broad_support",
            "preferred_rows": 80,
            "minimum_rows": 60,
            "primary_source_roles": "supported by exact_match / clear_accept",
            "selection_rule": "stable support evidence, no strong standing/lying subtype need",
            "q_e_requirement": "observable_or_sufficient",
        },
        {
            "route_label": "relabel_to_subtype",
            "preferred_rows": 80,
            "minimum_rows": 60,
            "primary_source_roles": "supported by family_match or overlap where standing/lying subtype is stronger",
            "selection_rule": "physical support present but subtype predicate is more informative",
            "q_e_requirement": "observable_or_sufficient_with_subtype_evidence",
        },
        {
            "route_label": "reject_no_support",
            "preferred_rows": 80,
            "minimum_rows": 60,
            "primary_source_roles": "hard_reject_no_support with explicit geometry/visual contradiction",
            "selection_rule": "not no-GT alone; must show no support/contact/vertical-support evidence",
            "q_e_requirement": "observable_or_sufficient",
        },
        {
            "route_label": "abstain",
            "preferred_rows": 80,
            "minimum_rows": 60,
            "primary_source_roles": "overlap_or_abstain with generic/missing/occluded/ontology-overlap evidence",
            "selection_rule": "include generic and non-generic ambiguity; generic endpoint cannot dominate",
            "q_e_requirement": "low_observability_or_ambiguous",
        },
    ]


def mining_query_rows() -> list[dict[str, Any]]:
    return [
        {
            "query_id": "Q1_accept_broad_support",
            "route_label": "accept_broad_support",
            "candidate_roles": "clear_accept",
            "label_match_status": "exact_match",
            "geometry_filter": "support_area/contact/vertical support present",
            "exclude": "strong standing/lying subtype evidence if subtype label is clearer",
            "target_rows": 80,
        },
        {
            "query_id": "Q2_relabel_to_standing",
            "route_label": "relabel_to_subtype",
            "candidate_roles": "overlap_or_abstain or family_match",
            "label_match_status": "family_match or pair_has_other_predicate",
            "geometry_filter": "upright object, bottom contact, support surface below",
            "exclude": "generic endpoint only",
            "target_rows": 40,
        },
        {
            "query_id": "Q3_relabel_to_lying",
            "route_label": "relabel_to_subtype",
            "candidate_roles": "overlap_or_abstain or family_match",
            "label_match_status": "family_match or pair_has_other_predicate",
            "geometry_filter": "horizontal/elongated object, large surface contact or resting evidence",
            "exclude": "generic endpoint only",
            "target_rows": 40,
        },
        {
            "query_id": "Q4_reject_no_support",
            "route_label": "reject_no_support",
            "candidate_roles": "hard_reject_no_support",
            "label_match_status": "pair_has_other_predicate preferred; no-GT only if contradiction is visible",
            "geometry_filter": "large gap, no overlap/contact, wrong vertical order, or impossible support surface",
            "exclude": "no-GT without visible/geometry contradiction",
            "target_rows": 80,
        },
        {
            "query_id": "Q5_abstain_generic_endpoint",
            "route_label": "abstain",
            "candidate_roles": "overlap_or_abstain",
            "label_match_status": "no_gt_for_pair or ambiguous overlap",
            "geometry_filter": "generic subject/object or ontology overlap",
            "exclude": "cap to at most half of abstain rows",
            "target_rows": 40,
        },
        {
            "query_id": "Q6_abstain_non_generic_low_observability",
            "route_label": "abstain",
            "candidate_roles": "overlap_or_abstain",
            "label_match_status": "ambiguous overlap, limited view, missing evidence",
            "geometry_filter": "non-generic endpoint but insufficient subtype or support evidence",
            "exclude": "clear no-support contradiction",
            "target_rows": 40,
        },
    ]


def balancing_rows() -> list[dict[str, Any]]:
    return [
        {
            "constraint": "preferred_total_rows",
            "value": 320,
            "reason": "80 rows for each of four decomposition labels",
            "fallback": "240 rows if strict same-class-pair mixing cannot satisfy preferred quota",
        },
        {
            "constraint": "minimum_total_rows",
            "value": 240,
            "reason": "60 rows per class is the minimum viable route-specific materialization",
            "fallback": "if not met, freeze R6 as diagnostic-only and move to R7 attachment observability",
        },
        {
            "constraint": "max_rows_per_scan",
            "value": 12,
            "reason": "avoid scan/source context memorization",
            "fallback": "relax to 16 only if all four labels remain balanced",
        },
        {
            "constraint": "max_rows_per_directed_pair",
            "value": 1,
            "reason": "avoid duplicate pair leakage across labels",
            "fallback": "allow 2 only for paired hidden-control rows, not model-safe rows",
        },
        {
            "constraint": "max_rows_per_subject_object_class_pair",
            "value": 16,
            "reason": "class-pair is a known shortcut in support/contact",
            "fallback": "relax to 24 with explicit class-pair shortcut audit",
        },
        {
            "constraint": "min_mixed_class_pair_cells",
            "value": 12,
            "reason": "same class-pair must contain multiple route labels",
            "fallback": "if below 12, materialize diagnostic-only rows",
        },
        {
            "constraint": "max_hard_surface_share",
            "value": 0.55,
            "reason": "floor/table/wall-like endpoints dominate support/contact",
            "fallback": "report separate hard-surface slice if exceeded",
        },
        {
            "constraint": "max_generic_endpoint_abstain_share",
            "value": 0.50,
            "reason": "abstain cannot be equivalent to generic endpoint",
            "fallback": "add non-generic low-observability rows or block p_obs/Q_e smoke",
        },
    ]


def output_contract() -> dict[str, Any]:
    return {
        "artifact_root": "artifacts/route_specific_targets/r6_superordinate_support/",
        "required_files": {
            "model_safe_rows.jsonl": "T_e/G_e/Q_e plus decomposition labels, no hidden construction fields",
            "hidden_manifest.jsonl": "source/rank/GT/machine/provenance fields for audit only",
            "audit_view.jsonl": "reviewable compact row packet without source score/rank",
            "schema.json": "field contract and label mapping",
            "quota_audit.csv": "label count, predicate/class-pair/rank/source quotas",
            "cell_balance_audit.csv": "same-class-pair mixed-label diagnostics",
            "control_manifest.json": "wrong-pair/shuffled-G/source/class-pair/generic-endpoint controls",
            "validation_errors.jsonl": "empty when materialization passes",
            "summary.json": "machine-readable status and next_todo",
            "report.md": "human-readable route materialization result",
        },
        "model_safe_feature_blocks": {
            "T_e": ["predicate_text", "subject_class_text", "object_class_text", "optional subtype query text"],
            "G_e": [
                "surface gap",
                "xy overlap",
                "support area proxy",
                "contact likelihood",
                "vertical order",
                "pose/upness",
                "normal/support-surface cues",
            ],
            "Q_e": [
                "mesh/semseg availability",
                "visual evidence availability",
                "generic endpoint visible flag",
                "missing evidence mask",
                "observability/ambiguity flags",
            ],
        },
        "hidden_only_fields": [
            "source score",
            "source rank",
            "rank band",
            "queue kind",
            "GT match status",
            "old geometry status",
            "p_geom_valid",
            "candidate role",
            "construction bucket",
            "machine hint",
            "scan id",
            "subgraph id",
            "directed pair id",
        ],
    }


def control_rows() -> list[dict[str, Any]]:
    return [
        {
            "control": "class_pair_only",
            "gate": "majority accuracy must not exceed 0.60 for the four-way target",
            "purpose": "prevent class-pair from reconstructing decomposition labels",
        },
        {
            "control": "source_score_rank_hidden",
            "gate": "source/rank hidden probes must not exceed 0.60 AUROC/accuracy",
            "purpose": "prevent source confidence from acting as target construction shortcut",
        },
        {
            "control": "generic_endpoint_only",
            "gate": "generic endpoint alone must not solve abstain",
            "purpose": "prevent p_obs/Q_e from degenerating into generic label detection",
        },
        {
            "control": "hard_surface_slice",
            "gate": "report all metrics by hard-surface and non-hard-surface slices",
            "purpose": "avoid floor/table/wall endpoint dominance",
        },
        {
            "control": "wrong_pair_geometry",
            "gate": "decomposition confidence should degrade under wrong-pair G_e",
            "purpose": "verify pair-specific geometry use",
        },
        {
            "control": "shuffled_G_within_class_pair",
            "gate": "performance should collapse toward chance within class-pair shuffled G_e",
            "purpose": "separate geometry evidence from object class semantics",
        },
        {
            "control": "no_gt_not_negative",
            "gate": "no-GT rows cannot be mapped directly to reject",
            "purpose": "avoid annotation incompleteness becoming a false negative label",
        },
        {
            "control": "subtype_relabel_consistency",
            "gate": "relabel rows must include subtype target and evidence reason",
            "purpose": "separate broad accept from standing/lying subtype correction",
        },
    ]


def next_steps() -> list[dict[str, Any]]:
    return [
        {
            "order": 1,
            "next_todo": NEXT_TODO,
            "action": "materialize R6 rows under the 320 preferred / 240 minimum contract",
            "blocked": False,
        },
        {
            "order": 2,
            "next_todo": "compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit",
            "action": "audit schema leakage, class-pair shortcut, generic abstain shortcut, source/rank hidden probes",
            "blocked": "requires materialized R6 rows",
        },
        {
            "order": 3,
            "next_todo": "compatibility_dataset_v3_supported_by_decomposition_route_control_runner_plan",
            "action": "plan deterministic controls only if schema audit passes",
            "blocked": "requires schema/shortcut audit",
        },
        {
            "order": 4,
            "next_todo": "compatibility_dataset_v3_attachment_observability_target_plan",
            "action": "move to R7 if R6 cannot satisfy minimum materialization gates",
            "blocked": "fallback path",
        },
    ]


def write_report(
    path: Path,
    summary: dict[str, Any],
    quotas: list[dict[str, Any]],
    balancing: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> None:
    lines = [
        "# H002 R6 Supported-By Decomposition Candidate Materialization Plan",
        "",
        f"Created: {summary['created_at_utc']}",
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
        "## Plan",
        "",
        "Materialize R6 `supported by` as a four-way decomposition target, not as a binary",
        "compatibility target. The preferred target is 320 rows, with 80 rows per label.",
        "The minimum viable fallback is 240 rows, with 60 rows per label.",
        "",
        "## Quotas",
        "",
        "| Label | Preferred | Minimum | Source Roles |",
        "| --- | ---: | ---: | --- |",
    ]
    for row in quotas:
        lines.append(
            f"| `{row['route_label']}` | {row['preferred_rows']} | {row['minimum_rows']} | {row['primary_source_roles']} |"
        )
    lines.extend(["", "## Balancing Gates", ""])
    for row in balancing:
        lines.append(f"- `{row['constraint']}` = {row['value']}: {row['reason']}")
    lines.extend(["", "## Required Controls", ""])
    for row in controls:
        lines.append(f"- `{row['control']}`: {row['gate']}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only materialization planning only.",
            "- No rows are materialized in this step.",
            "- No learned smoke/model training.",
            "- No validation/test usage.",
            "- H001 artifacts are not modified.",
            "- No paper-level evidence is claimed.",
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
    output_dir = args.output_dir

    target_summary = read_json(args.target_plan_dir / "summary.json")
    source_summary = read_json(args.source_inventory_dir / "summary.json")
    existing_summary = read_json(args.existing_materialization_dir / "summary.json")
    predicate_rows = read_csv(args.source_inventory_dir / "predicate_source_inventory.csv")
    role_rows = read_csv(args.source_inventory_dir / "role_capacity.csv")
    cell_rows = read_csv(args.source_inventory_dir / "controlled_cell_capacity.csv")
    target_validation_rows = read_jsonl(args.target_plan_dir / "validation_errors.jsonl")
    source_validation_rows = read_jsonl(args.source_inventory_dir / "validation_errors.jsonl")
    existing_validation_rows = read_jsonl(args.existing_materialization_dir / "validation_errors.jsonl")

    errors = validate_inputs(
        target_summary,
        source_summary,
        existing_summary,
        predicate_rows,
        role_rows,
        cell_rows,
        target_validation_rows,
        source_validation_rows,
        existing_validation_rows,
    )

    quotas = [] if errors else quota_plan_rows()
    mining_queries = [] if errors else mining_query_rows()
    balancing = [] if errors else balancing_rows()
    controls = [] if errors else control_rows()
    next_rows = [] if errors else next_steps()

    status = STATUS_ERRORS if errors else STATUS_READY
    supported_predicate = by_key(predicate_rows, "predicate_label").get("supported by", {})
    role_lookup = {
        (row.get("predicate_label"), row.get("candidate_role")): row
        for row in role_rows
        if row.get("predicate_label") and row.get("candidate_role")
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": None if errors else SELECTED_PATH,
        "next_todo": None if errors else NEXT_TODO,
        "validation_errors": len(errors),
        "route": {
            "route_id": "R6",
            "family": "superordinate_support",
            "relation": "supported by",
            "route_type": "superordinate_support_decomposition_route",
            "target_axis": "accept_relabel_abstain",
        },
        "input_paths": {
            "target_plan": rel_path(args.target_plan_dir),
            "source_inventory": rel_path(args.source_inventory_dir),
            "existing_materialization": rel_path(args.existing_materialization_dir),
        },
        "output_paths": {
            "artifact_root": rel_path(output_dir),
            "summary": rel_path(output_dir / "summary.json"),
            "quota_plan": rel_path(output_dir / "quota_plan.csv"),
            "mining_query_plan": rel_path(output_dir / "mining_query_plan.csv"),
            "balancing_constraints": rel_path(output_dir / "balancing_constraints.csv"),
            "control_plan": rel_path(output_dir / "control_plan.csv"),
            "output_contract": rel_path(output_dir / "output_contract.json"),
            "next_steps": rel_path(output_dir / "next_steps.csv"),
            "report": rel_path(output_dir / "report.md"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "planned_rows": {
            "preferred_total": 320,
            "minimum_viable_total": 240,
            "preferred_per_label": 80,
            "minimum_per_label": 60,
        },
        "source_capacity": {
            "supported_by_rows": as_int(supported_predicate, "rows"),
            "supported_by_class_pair_balanced_rows": as_int(supported_predicate, "class_pair_balanced_rows"),
            "supported_by_class_pair_rank_balanced_rows": as_int(supported_predicate, "class_pair_rank_balanced_rows"),
            "clear_accept_rows": as_int(role_lookup.get(("supported by", "clear_accept")), "rows"),
            "hard_reject_no_support_rows": as_int(role_lookup.get(("supported by", "hard_reject_no_support")), "rows"),
            "overlap_or_abstain_rows": as_int(role_lookup.get(("supported by", "overlap_or_abstain")), "rows"),
            "existing_supported_by_diagnostic_rows": existing_summary.get("counts", {})
            .get("predicate_counts", {})
            .get("supported by"),
        },
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
            "test_usage": False,
            "validation_usage": False,
            "binary_only_target_allowed": False,
            "no_gt_as_negative_allowed": False,
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", summary)
    write_csv(output_dir / "quota_plan.csv", quotas)
    write_csv(output_dir / "mining_query_plan.csv", mining_queries)
    write_csv(output_dir / "balancing_constraints.csv", balancing)
    write_csv(output_dir / "control_plan.csv", controls)
    write_json(output_dir / "output_contract.json", output_contract())
    write_csv(output_dir / "next_steps.csv", next_rows)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_report(output_dir / "report.md", summary, quotas, balancing, controls)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
