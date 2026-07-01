#!/usr/bin/env python3
"""Plan R6 supported-by decomposition target under route-specific H002 taxonomy."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
ARTIFACT_ROOT = H2_ROOT / "artifacts"

DEFAULT_CLOSE_BY_REVIEW_DIR = (
    ARTIFACT_ROOT / "compatibility_dataset_v3_close_by_geometry_support_route_result_review"
)
DEFAULT_MANIFEST_PLAN_DIR = (
    ARTIFACT_ROOT / "compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze"
)
DEFAULT_SOURCE_INVENTORY_DIR = (
    ARTIFACT_ROOT / "compatibility_dataset_v3_support_contact_individual_predicate_source_inventory"
)
DEFAULT_INDIVIDUAL_MATERIALIZATION_DIR = (
    ARTIFACT_ROOT / "compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization"
)
DEFAULT_VISUAL_LABEL_DIR = (
    ARTIFACT_ROOT / "compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion"
)
DEFAULT_CLASS_PAIR_REPAIR_LABEL_DIR = (
    ARTIFACT_ROOT / "compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion"
)
DEFAULT_OUTPUT_DIR = ARTIFACT_ROOT / "compatibility_dataset_v3_supported_by_decomposition_target_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_supported_by_decomposition_target_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_supported_by_decomposition_target_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_supported_by_decomposition_target_plan_input_errors"
SELECTED_PATH = "plan_supported_by_superordinate_accept_relabel_reject_abstain_route"
NEXT_TODO = "compatibility_dataset_v3_supported_by_decomposition_candidate_materialization_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--close-by-review-dir", type=Path, default=DEFAULT_CLOSE_BY_REVIEW_DIR)
    parser.add_argument("--manifest-plan-dir", type=Path, default=DEFAULT_MANIFEST_PLAN_DIR)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
    parser.add_argument("--individual-materialization-dir", type=Path, default=DEFAULT_INDIVIDUAL_MATERIALIZATION_DIR)
    parser.add_argument("--visual-label-dir", type=Path, default=DEFAULT_VISUAL_LABEL_DIR)
    parser.add_argument("--class-pair-repair-label-dir", type=Path, default=DEFAULT_CLASS_PAIR_REPAIR_LABEL_DIR)
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
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def status_ok(summary: dict[str, Any], expected_prefix: str) -> bool:
    return str(summary.get("status", "")).startswith(expected_prefix) and summary.get("validation_errors") == 0


def predicate_label(row: dict[str, Any]) -> str | None:
    return (
        row.get("predicate_label")
        or row.get("feature_blocks", {}).get("T_e", {}).get("predicate_label")
        or row.get("visible_fields", {}).get("predicate_label")
    )


def relation_label(row: dict[str, Any]) -> str | None:
    return (
        row.get("relation_multiclass_target")
        or row.get("review_relation_reliability")
        or row.get("labels", {}).get("p_rel")
    )


def count_supported_by_labels(path: Path) -> dict[str, Any]:
    rows = read_jsonl(path)
    predicate_counts: Counter[str] = Counter()
    relation_counts: Counter[str] = Counter()
    supported_counts: Counter[str] = Counter()
    for row in rows:
        pred = predicate_label(row) or "unknown"
        label = relation_label(row) or "unknown"
        predicate_counts[pred] += 1
        relation_counts[label] += 1
        if pred == "supported by":
            supported_counts[label] += 1
    return {
        "rows": len(rows),
        "predicate_counts": dict(predicate_counts),
        "relation_counts": dict(relation_counts),
        "supported_by_counts": dict(supported_counts),
    }


def validate_inputs(
    close_by_summary: dict[str, Any],
    manifest_report: str,
    source_summary: dict[str, Any],
    materialization_summary: dict[str, Any],
    visual_summary: dict[str, Any],
    repair_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []

    if close_by_summary.get("status") != "h002_compatibility_dataset_v3_close_by_geometry_support_route_result_review_ready":
        errors.append({"error_type": "close_by_review_not_ready", "actual": close_by_summary.get("status")})
    if close_by_summary.get("next_todo") != "compatibility_dataset_v3_supported_by_decomposition_target_plan":
        errors.append({"error_type": "unexpected_close_by_next_todo", "actual": close_by_summary.get("next_todo")})

    required_manifest_terms = [
        "superordinate_support_decomposition_route",
        "supported by",
        "accept_broad_support",
        "relabel_to_subtype",
        "reject_no_support",
        "abstain",
    ]
    for term in required_manifest_terms:
        if term not in manifest_report:
            errors.append({"error_type": "manifest_missing_term", "term": term})

    if not status_ok(source_summary, "h002_compatibility_dataset_v3_support_contact_individual_predicate_source_inventory_ready"):
        errors.append({"error_type": "source_inventory_not_ready", "actual": source_summary.get("status")})
    if not status_ok(materialization_summary, "h002_compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_ready"):
        errors.append({"error_type": "individual_materialization_not_ready", "actual": materialization_summary.get("status")})
    if not status_ok(visual_summary, "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingested"):
        errors.append({"error_type": "visual_label_ingestion_not_ready", "actual": visual_summary.get("status")})
    if not status_ok(repair_summary, "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingested"):
        errors.append({"error_type": "class_pair_repair_ingestion_not_ready", "actual": repair_summary.get("status")})

    for name, summary in [
        ("close_by", close_by_summary),
        ("source_inventory", source_summary),
        ("individual_materialization", materialization_summary),
        ("visual_label_ingestion", visual_summary),
        ("class_pair_repair_label_ingestion", repair_summary),
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

    counts = materialization_summary.get("counts", {})
    supported_rows = counts.get("predicate_counts", {}).get("supported by")
    if supported_rows != 160:
        errors.append({"error_type": "unexpected_supported_by_diagnostic_rows", "actual": supported_rows})
    roles = counts.get("quota_role_counts", {})
    for role, minimum in [
        ("supported by::clear_accept", 40),
        ("supported by::hard_reject_no_support", 40),
        ("supported by::overlap_or_abstain", 80),
    ]:
        if roles.get(role, 0) < minimum:
            errors.append({"error_type": "supported_by_role_count_low", "role": role, "actual": roles.get(role, 0)})

    return errors


def label_space_rows() -> list[dict[str, Any]]:
    return [
        {
            "route_label": "accept_broad_support",
            "decision_head": "p_obs=1,p_rel=accept",
            "meaning": "supported by is reliable as a broad support relation without forcing a finer subtype",
            "positive_for_binary_rel": True,
            "requires_subtype": False,
            "model_safe_target": True,
        },
        {
            "route_label": "relabel_to_subtype",
            "decision_head": "p_obs=1,p_rel=accept_with_relabel",
            "meaning": "physical support is present but standing on or lying on is the more informative predicate",
            "positive_for_binary_rel": True,
            "requires_subtype": True,
            "model_safe_target": True,
        },
        {
            "route_label": "reject_no_support",
            "decision_head": "p_obs=1,p_rel=reject",
            "meaning": "the candidate is not supported by the object under available geometry/visual evidence",
            "positive_for_binary_rel": False,
            "requires_subtype": False,
            "model_safe_target": True,
        },
        {
            "route_label": "abstain",
            "decision_head": "p_obs=0,p_rel=undefined",
            "meaning": "generic endpoints, missing evidence, ontology overlap, or unclear support subtype makes reliability undecidable",
            "positive_for_binary_rel": None,
            "requires_subtype": False,
            "model_safe_target": True,
        },
    ]


def source_inventory_rows(
    source_summary: dict[str, Any],
    materialization_summary: dict[str, Any],
    visual_counts: dict[str, Any],
    repair_counts: dict[str, Any],
) -> list[dict[str, Any]]:
    counts = materialization_summary.get("counts", {})
    return [
        {
            "source": "individual_predicate_source_inventory",
            "usable_for": "capacity_context",
            "supported_by_signal": "rows=50601, class_pair_balanced_rows=164, mixed_groups=45",
            "risk": "capacity exists but broad/superordinate overlap prevents clean binary use",
        },
        {
            "source": "individual_predicate_candidate_materialization",
            "usable_for": "pilot_seed_roles",
            "supported_by_signal": (
                f"diagnostic_rows={counts.get('predicate_counts', {}).get('supported by')}; "
                f"clear_accept={counts.get('quota_role_counts', {}).get('supported by::clear_accept')}; "
                f"hard_reject_no_support={counts.get('quota_role_counts', {}).get('supported by::hard_reject_no_support')}; "
                f"overlap_or_abstain={counts.get('quota_role_counts', {}).get('supported by::overlap_or_abstain')}"
            ),
            "risk": "existing roles need relabel/abstain split before model use",
        },
        {
            "source": "visual_mesh_audit_label_ingestion",
            "usable_for": "diagnostic_prior",
            "supported_by_signal": str(visual_counts.get("supported_by_counts", {})),
            "risk": "reject count is too low for clean binary supported-by learning",
        },
        {
            "source": "visual_mesh_class_pair_repair_label_ingestion",
            "usable_for": "diagnostic_prior_after_class_pair_repair",
            "supported_by_signal": str(repair_counts.get("supported_by_counts", {})),
            "risk": "predicate_x_class_pair still reconstructs labels; p_obs/Q_e degenerate",
        },
    ]


def materialization_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "quota_role": "accept_broad_support",
            "minimum_rows": 60,
            "preferred_rows": 80,
            "source_strategy": "supported-by candidate with stable support evidence but no strong standing/lying subtype need",
            "must_control": "subject/object class-pair, hard-surface endpoint, rank band, source score",
        },
        {
            "quota_role": "relabel_to_subtype",
            "minimum_rows": 60,
            "preferred_rows": 80,
            "source_strategy": "supported-by candidate where visual/mesh/pose evidence indicates standing on or lying on is more specific",
            "must_control": "subtype distribution, same class-pair accept/relabel cells, no supported-by as clean negative",
        },
        {
            "quota_role": "reject_no_support",
            "minimum_rows": 60,
            "preferred_rows": 80,
            "source_strategy": "nearby or source-supported-by candidate with no physical support/contact/vertical support evidence",
            "must_control": "do not use no-GT alone; require visual/mesh or geometry contradiction",
        },
        {
            "quota_role": "abstain",
            "minimum_rows": 60,
            "preferred_rows": 80,
            "source_strategy": "generic endpoints, missing/occluded evidence, topology/ontology overlap, or insufficient subtype evidence",
            "must_control": "generic endpoint cannot be the only abstain shortcut; include non-generic low-observability rows",
        },
    ]


def model_boundary() -> dict[str, Any]:
    return {
        "allowed_model_safe_blocks": {
            "T_e": [
                "predicate_text='supported by'",
                "subject_class_text",
                "object_class_text",
                "optional_subtype_query_text only for relabel head",
            ],
            "G_e": [
                "surface gap",
                "XY overlap ratios",
                "support area proxy",
                "contact likelihood",
                "vertical ordering",
                "normal/upness and pose features",
                "point/multiview-derived evidence only after Q_e provenance is explicit",
            ],
            "Q_e": [
                "mesh/semseg availability",
                "visual packet availability",
                "generic endpoint flag",
                "missing evidence mask",
                "occlusion/ambiguity flag when audited",
            ],
        },
        "blocked_model_inputs": [
            "source score",
            "source rank",
            "rank band",
            "queue kind",
            "GT match status",
            "old geometry status",
            "p_geom_valid hidden reference",
            "construction bucket",
            "machine hint",
            "scan id",
            "subgraph id",
            "directed pair id",
            "candidate role",
            "route label source",
        ],
        "hidden_audit_only": [
            "source score/rank",
            "label_match_status",
            "construction_bucket",
            "p_geom_valid",
            "H001 verification status",
            "candidate mining role",
        ],
        "decision_contract": {
            "p_obs_low": "abstain",
            "p_obs_high_and_accept_broad_support": "accept supported by",
            "p_obs_high_and_relabel_to_subtype": "accept physical support but update predicate to subtype",
            "p_obs_high_and_reject_no_support": "reject supported by",
        },
    }


def control_rows() -> list[dict[str, Any]]:
    return [
        {
            "control": "same_predicate_class_pair_balance",
            "purpose": "ensure accept/relabel/reject/abstain co-exist inside supported-by class-pair strata",
            "required_before_smoke": True,
        },
        {
            "control": "generic_endpoint_abstain_control",
            "purpose": "prevent abstain from being equivalent to generic subject/object labels",
            "required_before_smoke": True,
        },
        {
            "control": "hard_surface_cap",
            "purpose": "avoid floor/table/wall endpoint dominance",
            "required_before_smoke": True,
        },
        {
            "control": "source_rank_score_hidden_probe",
            "purpose": "verify source confidence does not reconstruct route labels",
            "required_before_smoke": True,
        },
        {
            "control": "subtype_relabel_consistency",
            "purpose": "separate broad accept from relabel-to-standing/lying rather than treating all support as accept",
            "required_before_smoke": True,
        },
        {
            "control": "wrong_pair_geometry",
            "purpose": "route labels must degrade when object-pair geometry is replaced",
            "required_before_smoke": True,
        },
        {
            "control": "shuffled_G_within_class_pair",
            "purpose": "prevent class-pair memorization from replacing geometry evidence",
            "required_before_smoke": True,
        },
        {
            "control": "no_GT_not_negative",
            "purpose": "no-GT rows are audit/abstain candidates unless physical contradiction is visible",
            "required_before_smoke": True,
        },
    ]


def risk_rows(visual_counts: dict[str, Any], repair_counts: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "risk": "supported_by_is_superordinate",
            "severity": "high",
            "evidence": "standing/lying support may also satisfy supported by",
            "mitigation": "use accept/relabel/reject/abstain route instead of binary compatibility",
        },
        {
            "risk": "reject_sparse_under_proxy_labels",
            "severity": "high",
            "evidence": f"supported-by proxy labels: {visual_counts.get('supported_by_counts', {})}; repair labels: {repair_counts.get('supported_by_counts', {})}",
            "mitigation": "mine explicit no-support contradictions and keep no-GT separate from reject",
        },
        {
            "risk": "class_pair_shortcut",
            "severity": "high",
            "evidence": "previous repair still had predicate_x_class_pair majority accuracy 1.0",
            "mitigation": "require mixed route labels within supported-by class-pair cells",
        },
        {
            "risk": "abstain_shortcut",
            "severity": "medium",
            "evidence": "generic endpoints can dominate abstain rows",
            "mitigation": "include non-generic missing/occlusion/ambiguous rows and audit generic endpoint separately",
        },
        {
            "risk": "q_e_degenerate",
            "severity": "medium",
            "evidence": "previous support/contact visual audit had p_obs=1 and Q_e=sufficient for all rows",
            "mitigation": "materialize low-observability/missing-evidence rows before p_obs/Q_e smoke",
        },
    ]


def next_steps() -> list[dict[str, Any]]:
    return [
        {
            "order": 1,
            "next_todo": NEXT_TODO,
            "action": "write candidate materialization plan for R6 supported-by decomposition",
            "blocked": False,
        },
        {
            "order": 2,
            "next_todo": "compatibility_dataset_v3_supported_by_decomposition_candidate_materialization",
            "action": "materialize route-specific rows only after class-pair and abstain-control quotas are fixed",
            "blocked": "requires materialization plan",
        },
        {
            "order": 3,
            "next_todo": "compatibility_dataset_v3_supported_by_decomposition_schema_shortcut_audit",
            "action": "audit model-safe fields, class-pair leakage, source/rank leakage, generic endpoint leakage",
            "blocked": "requires materialized rows",
        },
        {
            "order": 4,
            "next_todo": "compatibility_dataset_v3_attachment_observability_target_plan",
            "action": "move to R7 attachment observability route after R6 materialization plan or if R6 capacity fails",
            "blocked": "optional next route",
        },
    ]


def write_report(
    path: Path,
    summary: dict[str, Any],
    label_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    risks: list[dict[str, Any]],
) -> None:
    lines = [
        "# H002 R6 Supported-By Decomposition Target Plan",
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
        "## Decision",
        "",
        "`supported by`는 clean binary compatibility target으로 두지 않는다. 이 relation은",
        "`standing on` / `lying on`과 동시에 참일 수 있는 broad superordinate support label이다.",
        "따라서 R6는 `accept_broad_support`, `relabel_to_subtype`, `reject_no_support`,",
        "`abstain`으로 분해하는 route-specific target으로 설계한다.",
        "",
        "## Label Space",
        "",
        "| Label | Decision Head | Meaning |",
        "| --- | --- | --- |",
    ]
    for row in label_rows:
        lines.append(f"| `{row['route_label']}` | `{row['decision_head']}` | {row['meaning']} |")
    lines.extend(
        [
            "",
            "## Source Snapshot",
            "",
            "| Source | Usable For | Supported-By Signal | Risk |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in source_rows:
        lines.append(
            f"| `{row['source']}` | {row['usable_for']} | {row['supported_by_signal']} | {row['risk']} |"
        )
    lines.extend(["", "## Main Risks", ""])
    for row in risks:
        lines.append(f"- `{row['risk']}` ({row['severity']}): {row['mitigation']}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only planning only.",
            "- No row materialization in this step.",
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

    close_by_summary = read_json(args.close_by_review_dir / "summary.json")
    manifest_report = (args.manifest_plan_dir / "report.md").read_text(encoding="utf-8")
    source_summary = read_json(args.source_inventory_dir / "summary.json")
    materialization_summary = read_json(args.individual_materialization_dir / "summary.json")
    visual_summary = read_json(args.visual_label_dir / "summary.json")
    repair_summary = read_json(args.class_pair_repair_label_dir / "summary.json")
    visual_counts = count_supported_by_labels(args.visual_label_dir / "target_rows.jsonl")
    repair_counts = count_supported_by_labels(args.class_pair_repair_label_dir / "target_rows.jsonl")

    errors = validate_inputs(
        close_by_summary,
        manifest_report,
        source_summary,
        materialization_summary,
        visual_summary,
        repair_summary,
    )

    label_rows = [] if errors else label_space_rows()
    source_rows = [] if errors else source_inventory_rows(source_summary, materialization_summary, visual_counts, repair_counts)
    materialization_rows = [] if errors else materialization_contract_rows()
    controls = [] if errors else control_rows()
    risks = [] if errors else risk_rows(visual_counts, repair_counts)
    next_rows = [] if errors else next_steps()

    status = STATUS_ERRORS if errors else STATUS_READY
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
            "close_by_review": rel_path(args.close_by_review_dir),
            "manifest_plan": rel_path(args.manifest_plan_dir),
            "source_inventory": rel_path(args.source_inventory_dir),
            "individual_materialization": rel_path(args.individual_materialization_dir),
            "visual_label_ingestion": rel_path(args.visual_label_dir),
            "class_pair_repair_label_ingestion": rel_path(args.class_pair_repair_label_dir),
        },
        "output_paths": {
            "artifact_root": rel_path(output_dir),
            "summary": rel_path(output_dir / "summary.json"),
            "target_schema": rel_path(output_dir / "target_schema.json"),
            "label_space": rel_path(output_dir / "label_space.csv"),
            "source_snapshot": rel_path(output_dir / "source_snapshot.csv"),
            "materialization_contract": rel_path(output_dir / "materialization_contract.csv"),
            "model_input_boundary": rel_path(output_dir / "model_input_boundary.json"),
            "controls": rel_path(output_dir / "controls.csv"),
            "risk_register": rel_path(output_dir / "risk_register.csv"),
            "next_steps": rel_path(output_dir / "next_steps.csv"),
            "report": rel_path(output_dir / "report.md"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "source_snapshot": {
            "supported_by_existing_diagnostic_rows": materialization_summary.get("counts", {})
            .get("predicate_counts", {})
            .get("supported by"),
            "supported_by_existing_role_counts": {
                key: value
                for key, value in materialization_summary.get("counts", {})
                .get("quota_role_counts", {})
                .items()
                if key.startswith("supported by::")
            },
            "visual_label_supported_by_counts": visual_counts.get("supported_by_counts", {}),
            "class_pair_repair_supported_by_counts": repair_counts.get("supported_by_counts", {}),
        },
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
            "test_usage": False,
            "validation_usage": False,
            "supported_by_as_clean_negative_allowed": False,
            "binary_only_target_allowed": False,
        },
    }
    target_schema = {
        "schema_version": SCHEMA_VERSION,
        "route": summary["route"],
        "label_space": label_rows,
        "primary_multiclass_target": "supported_by_decomposition_label",
        "secondary_fields": {
            "subtype_relabel_target": ["standing on", "lying on", "other_support_subtype", "none"],
            "p_obs_target": "1 for evidence-sufficient labels, 0 for abstain",
            "p_rel_target": "accept for accept_broad_support/relabel_to_subtype, reject for reject_no_support, undefined for abstain",
        },
        "model_input_boundary": model_boundary(),
        "promotion_gate_before_smoke": [
            "balanced label mass across accept/relabel/reject/abstain",
            "same class-pair mixed labels",
            "generic endpoint does not define abstain alone",
            "source score/rank hidden predictors fail",
            "wrong-pair and shuffled-G controls degrade",
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "target_schema.json", target_schema)
    write_csv(output_dir / "label_space.csv", label_rows)
    write_csv(output_dir / "source_snapshot.csv", source_rows)
    write_csv(output_dir / "materialization_contract.csv", materialization_rows)
    write_json(output_dir / "model_input_boundary.json", model_boundary())
    write_csv(output_dir / "controls.csv", controls)
    write_csv(output_dir / "risk_register.csv", risks)
    write_csv(output_dir / "next_steps.csv", next_rows)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_report(output_dir / "report.md", summary, label_rows, source_rows, risks)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
