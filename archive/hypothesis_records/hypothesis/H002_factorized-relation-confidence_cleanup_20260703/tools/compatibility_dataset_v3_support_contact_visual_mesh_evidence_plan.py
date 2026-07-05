#!/usr/bin/env python3
"""Write the support/contact visual-mesh evidence extension plan."""

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

DEFAULT_PROBE_RUNNER_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_evidence_probe_runner"
DEFAULT_3RSCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_VISUAL_AUDIT_ROOT = H2_ROOT / "artifacts/visual_annotation_audit"
DEFAULT_ATTACHMENT_PACKET_ROOT = H2_ROOT / "artifacts/attachment_independent_positive_anchor_packet_materialization_v1"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan"

EXPECTED_PROBE_STATUS = "h002_compatibility_dataset_v3_support_contact_evidence_probe_runner_blocks_numeric_support_smoke"
EXPECTED_PROBE_NEXT = "compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan_input_errors"
SELECTED_ROUTE = "mesh_pose_contact_first_multiview_audit_first"
NEXT_TODO = "compatibility_dataset_v3_support_contact_visual_mesh_source_inventory"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-runner-dir", type=Path, default=DEFAULT_PROBE_RUNNER_DIR)
    parser.add_argument("--three-rscan-root", type=Path, default=DEFAULT_3RSCAN_ROOT)
    parser.add_argument("--visual-audit-root", type=Path, default=DEFAULT_VISUAL_AUDIT_ROOT)
    parser.add_argument("--attachment-packet-root", type=Path, default=DEFAULT_ATTACHMENT_PACKET_ROOT)
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
    if not fields:
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def scan_3rscan(root: Path) -> dict[str, Any]:
    if not root.exists():
        return {
            "root": rel_path(root),
            "exists": False,
            "scan_dirs": 0,
            "sequence_zip": 0,
            "labels_instances_annotated_v2_ply": 0,
            "labels_instances_align_annotated_v2_ply": 0,
            "semseg_v2_json": 0,
            "mesh_refined_v2_obj": 0,
            "mesh_refined_seg_json": 0,
            "mesh_texture_png": 0,
        }

    scan_dirs = [path for path in root.iterdir() if path.is_dir()]
    counts = Counter()
    for scan_dir in scan_dirs:
        if (scan_dir / "sequence.zip").exists():
            counts["sequence_zip"] += 1
        if (scan_dir / "labels.instances.annotated.v2.ply").exists():
            counts["labels_instances_annotated_v2_ply"] += 1
        if (scan_dir / "labels.instances.align.annotated.v2.ply").exists():
            counts["labels_instances_align_annotated_v2_ply"] += 1
        if (scan_dir / "semseg.v2.json").exists():
            counts["semseg_v2_json"] += 1
        if (scan_dir / "mesh.refined.v2.obj").exists():
            counts["mesh_refined_v2_obj"] += 1
        if (scan_dir / "mesh.refined.0.010000.segs.v2.json").exists():
            counts["mesh_refined_seg_json"] += 1
        if (scan_dir / "mesh.refined_0.png").exists():
            counts["mesh_texture_png"] += 1
    return {
        "root": rel_path(root),
        "exists": True,
        "scan_dirs": len(scan_dirs),
        "sequence_zip": counts["sequence_zip"],
        "labels_instances_annotated_v2_ply": counts["labels_instances_annotated_v2_ply"],
        "labels_instances_align_annotated_v2_ply": counts["labels_instances_align_annotated_v2_ply"],
        "semseg_v2_json": counts["semseg_v2_json"],
        "mesh_refined_v2_obj": counts["mesh_refined_v2_obj"],
        "mesh_refined_seg_json": counts["mesh_refined_seg_json"],
        "mesh_texture_png": counts["mesh_texture_png"],
    }


def scan_visual_audit(root: Path) -> dict[str, Any]:
    contact_sheet_dir = root / "contact_sheets"
    files = sorted(contact_sheet_dir.glob("*.jpg")) if contact_sheet_dir.exists() else []
    predicate_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    support_contact_predicates = {"standing-on", "lying-on", "supported-by"}
    for path in files:
        parts = path.stem.split("_")
        predicate = parts[-2] if len(parts) >= 2 else "unknown"
        source = parts[1] if len(parts) >= 3 else "unknown"
        predicate_counts[predicate] += 1
        source_counts[source] += 1
    return {
        "root": rel_path(root),
        "exists": root.exists(),
        "contact_sheet_dir": rel_path(contact_sheet_dir),
        "contact_sheet_count": len(files),
        "support_contact_sheet_count": sum(predicate_counts[predicate] for predicate in support_contact_predicates),
        "predicate_counts": dict(sorted(predicate_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "previsual_summary_exists": (root / "previsual_summary.json").exists(),
    }


def scan_attachment_packets(root: Path) -> dict[str, Any]:
    packets_root = root / "packets"
    packet_dirs = [path for path in packets_root.iterdir() if path.is_dir()] if packets_root.exists() else []
    contact_sheets = list(packets_root.glob("*/contact_context_sheet.jpg")) if packets_root.exists() else []
    mesh_packets = list(packets_root.glob("*/mesh_packet.md")) if packets_root.exists() else []
    packet_mds = list(packets_root.glob("*/packet.md")) if packets_root.exists() else []
    return {
        "root": rel_path(root),
        "exists": root.exists(),
        "packets_root": rel_path(packets_root),
        "packet_dirs": len(packet_dirs),
        "contact_context_sheets": len(contact_sheets),
        "mesh_packet_md": len(mesh_packets),
        "packet_md": len(packet_mds),
        "summary_exists": (root / "summary.json").exists(),
        "label_ready_manifest_exists": (root / "label_ready_manifest.jsonl").exists(),
        "reuse_role": "template_and_renderer_reference_only_for_support_contact",
    }


def validate_probe(summary: dict[str, Any], validation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_PROBE_STATUS:
        errors.append({"error_type": "unexpected_probe_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_PROBE_NEXT:
        errors.append({"error_type": "unexpected_probe_next", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "probe_validation_errors", "actual": summary.get("validation_errors")})
    if validation_rows:
        errors.append({"error_type": "probe_validation_error_rows_present", "rows": len(validation_rows)})

    decision = summary.get("path_decision", {})
    if decision.get("support_contact_materialization_allowed") is not False:
        errors.append({"error_type": "numeric_materialization_not_blocked", "actual": decision.get("support_contact_materialization_allowed")})
    if decision.get("visual_mesh_or_role_orientation_required") is not True:
        errors.append({"error_type": "visual_mesh_requirement_not_set", "actual": decision.get("visual_mesh_or_role_orientation_required")})
    if int(decision.get("candidate_non_hard_surface_exact_pair_groups", 0) or 0) >= int(decision.get("reportable_group_min", 60) or 60):
        errors.append({"error_type": "unexpected_non_hard_capacity_pass", "decision": decision})

    boundary = summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "runs_learned_smoke", "trains_new_model"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    return errors


def evidence_axis_rows() -> list[dict[str, Any]]:
    return [
        {
            "axis": "mesh_instance_points",
            "factor": "G_e",
            "priority": "primary",
            "source": "labels.instances.align.annotated.v2.ply; semseg.v2.json",
            "derived_features": "pair point crop, instance PCA axes, extents, support candidate surface bands",
            "why_needed": "standing vs lying requires object pose/orientation beyond OBB gap and overlap.",
            "model_input_allowed_after_audit": True,
            "human_label_allowed_as_feature": False,
        },
        {
            "axis": "mesh_contact_surface",
            "factor": "G_e",
            "priority": "primary",
            "source": "mesh.refined.v2.obj; mesh segment json; instance labels",
            "derived_features": "surface gap histogram, contact patch area, support overlap, local surface normal alignment",
            "why_needed": "supported by should depend on support surface geometry, not just center height.",
            "model_input_allowed_after_audit": True,
            "human_label_allowed_as_feature": False,
        },
        {
            "axis": "role_orientation_pose",
            "factor": "G_e",
            "priority": "primary",
            "source": "instance point cloud / mesh PCA / oriented extent ratios",
            "derived_features": "uprightness, horizontalness, major-axis alignment, bottom-contact band",
            "why_needed": "standing on and lying on can share contact but differ in subject pose.",
            "model_input_allowed_after_audit": True,
            "human_label_allowed_as_feature": False,
        },
        {
            "axis": "multi_view_covisibility",
            "factor": "Q_e_first_then_optional_V_e",
            "priority": "secondary_audit_first",
            "source": "sequence.zip RGB-D frames and camera poses",
            "derived_features": "co-visible frame count, subject/object visibility, pair crop quality, occlusion/conflict flags",
            "why_needed": "visual evidence can confirm ambiguous contact/pose and decide abstain, but should not become a shortcut before controls.",
            "model_input_allowed_after_audit": "only after source-inventory and shortcut controls",
            "human_label_allowed_as_feature": False,
        },
        {
            "axis": "reviewer_packet_visuals",
            "factor": "audit_label_source_only",
            "priority": "audit_support",
            "source": "contact sheets and packet renderer pattern",
            "derived_features": "human-visible packet for accept/reject/abstain labeling",
            "why_needed": "helps create independent labels without exposing source score/rank or construction proxy.",
            "model_input_allowed_after_audit": False,
            "human_label_allowed_as_feature": False,
        },
        {
            "axis": "numeric_obb_baseline",
            "factor": "G_e_control",
            "priority": "control_only",
            "source": "current numeric artifacts",
            "derived_features": "distance, overlap, vertical gap, top/bottom z",
            "why_needed": "kept as baseline and shortcut-risk control; not enough as primary support/contact evidence.",
            "model_input_allowed_after_audit": True,
            "human_label_allowed_as_feature": False,
        },
    ]


def relation_family_rows() -> list[dict[str, Any]]:
    return [
        {
            "predicate": "standing on",
            "family": "support_contact",
            "needed_evidence": "support contact + upright subject pose",
            "likely_G_e": "surface gap, support overlap, local normal alignment, subject uprightness",
            "likely_Q_e": "mesh completeness, co-visible crop quality, contact visibility",
            "hard_negative": "same support proximity but subject not upright or no support contact",
            "main_shortcut_to_block": "floor/object category and one-frame obvious contact",
        },
        {
            "predicate": "lying on",
            "family": "support_contact",
            "needed_evidence": "support contact + horizontal subject pose",
            "likely_G_e": "large support contact band, horizontal major axis, low vertical thickness",
            "likely_Q_e": "mesh completeness, occlusion, view coverage",
            "hard_negative": "same support contact but upright or only nearby",
            "main_shortcut_to_block": "bed/sofa object category",
        },
        {
            "predicate": "supported by",
            "family": "support_contact",
            "needed_evidence": "support direction and stable surface relation",
            "likely_G_e": "object top/support surface normal, subject bottom contact, support area ratio",
            "likely_Q_e": "mesh segmentation quality and surface availability",
            "hard_negative": "near or overlapping without upward support",
            "main_shortcut_to_block": "object category and hard-surface dominance",
        },
    ]


def route_rows() -> list[dict[str, Any]]:
    return [
        {
            "route": "run_numeric_only_support_contact_smoke",
            "verdict": "reject",
            "reason": "Previous probe found only 4 non-hard-surface exact candidate groups and missing role/orientation/contact evidence.",
            "next_action": "do_not_run",
        },
        {
            "route": "reuse_attachment_packets_as_support_contact_labels",
            "verdict": "reject_as_primary",
            "reason": "Attachment packets are useful renderer/template references, but their labels and candidate strata are not support/contact GT.",
            "next_action": "reuse_packet_builder_pattern_only",
        },
        {
            "route": "add_multiview_directly_as_model_input_now",
            "verdict": "defer",
            "reason": "Direct visual input could improve metrics while hiding target-construction shortcut; use multi-view for audit/Q_e first.",
            "next_action": "inventory_coverage_and_define_controls",
        },
        {
            "route": "mesh_pose_contact_evidence_first",
            "verdict": "selected_primary",
            "reason": "It directly addresses the failure cause: current numeric G_e lacks role, orientation, contact direction, and surface evidence.",
            "next_action": NEXT_TODO,
        },
        {
            "route": "multiview_audit_first",
            "verdict": "selected_secondary",
            "reason": "Visual evidence is valuable for confirming ambiguous rows and Q_e/abstain, but deployable V_e should wait for controls.",
            "next_action": NEXT_TODO,
        },
    ]


def feature_boundary() -> dict[str, Any]:
    return {
        "T_e": {
            "allowed": ["predicate_label", "predicate_text", "subject_class", "object_class", "relation_family"],
            "blocked": ["source_score", "source_rank", "construction_route"],
        },
        "Z_e": {
            "allowed": ["source_score", "source_rank", "source_id", "rank_band"],
            "usage": "allowed in final p_rel comparison, not in C_e compatibility head",
        },
        "G_e": {
            "allowed": [
                "numeric OBB/distance/overlap controls",
                "mesh contact surface features",
                "instance point/pose/orientation features",
                "surface normal/contact direction features",
            ],
            "blocked": ["predicate label", "source confidence", "human label", "row construction type"],
        },
        "C_e": {
            "definition": "compatibility(T_e, G_e)",
            "blocked_inputs": ["Z_e", "human audit label", "hidden row role", "counterfactual type"],
        },
        "Q_e": {
            "allowed": ["mesh completeness", "co-visible frame count", "crop quality", "occlusion", "segmentation completeness"],
            "usage": "controls p_obs/abstain, not relation truth by itself",
        },
        "audit_label": {
            "allowed_inputs": ["reviewer-visible packet", "mesh context", "visual contact sheets", "non-source semantic labels"],
            "blocked_inputs": ["source score", "source rank", "hidden construction proxy", "previous proxy target"],
        },
    }


def runner_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Inventory whether mesh/pose/contact/multi-view sources can be joined to support/contact train candidates before materialization.",
        "input_roots": {
            "probe_runner": rel_path(DEFAULT_PROBE_RUNNER_DIR),
            "three_rscan": rel_path(DEFAULT_3RSCAN_ROOT),
            "visual_annotation_audit": rel_path(DEFAULT_VISUAL_AUDIT_ROOT),
            "attachment_packet_template": rel_path(DEFAULT_ATTACHMENT_PACKET_ROOT),
        },
        "required_outputs": [
            "scan_asset_inventory.csv",
            "support_contact_candidate_source_join_preview.jsonl",
            "mesh_pose_contact_feature_feasibility.csv",
            "multiview_packet_feasibility.csv",
            "shortcut_and_scope_risk.csv",
            "path_decision.json",
            "summary.json",
            "report.md",
        ],
        "success_conditions": [
            "support/contact candidate rows can be joined to scan-level mesh and instance-label assets",
            "at least one role/orientation or mesh contact evidence axis is derivable without predicate/source leakage",
            "multi-view evidence is classified as Q_e/audit-first unless controls justify model input",
            "candidate materialization path can avoid hard-surface/object-category/source-rank shortcuts",
            "no validation/test split is used",
        ],
        "failure_routes": [
            "If mesh/pose/contact features cannot be joined, keep support/contact diagnostic and return to relative_vertical/proximity generality.",
            "If only visual packets are available, use them for audit labels and Q_e, not deployable C_e.",
            "If support/contact remains object-category dominated, defer as family-specific failure taxonomy.",
        ],
    }


def build_summary(
    probe_summary: dict[str, Any],
    source_inventory: dict[str, Any],
    errors: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Any]:
    status = STATUS_READY if not errors else STATUS_ERRORS
    next_todo = NEXT_TODO if not errors else "fix_support_contact_visual_mesh_plan_inputs"
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_route": SELECTED_ROUTE if not errors else "fix_inputs_before_plan",
        "next_todo": next_todo,
        "validation_errors": len(errors),
        "probe_status": probe_summary.get("status"),
        "probe_decision": probe_summary.get("path_decision", {}),
        "source_inventory_summary": {
            "three_rscan_scan_dirs": source_inventory["three_rscan"].get("scan_dirs"),
            "three_rscan_mesh_obj": source_inventory["three_rscan"].get("mesh_refined_v2_obj"),
            "three_rscan_sequence_zip": source_inventory["three_rscan"].get("sequence_zip"),
            "visual_contact_sheets": source_inventory["visual_annotation_audit"].get("contact_sheet_count"),
            "visual_support_contact_sheets": source_inventory["visual_annotation_audit"].get("support_contact_sheet_count"),
            "attachment_packet_dirs_template": source_inventory["attachment_packet_template"].get("packet_dirs"),
        },
        "plan_decision": {
            "numeric_only_support_contact_smoke_allowed": False,
            "mesh_pose_contact_evidence_required": True,
            "multiview_model_input_allowed_now": False,
            "multiview_audit_first": True,
            "attachment_packets_reuse_as_labels": False,
            "attachment_packet_builder_reuse_as_template": True,
        },
        "output_paths": {
            "summary": rel_path(output_dir / "summary.json"),
            "source_inventory": rel_path(output_dir / "source_inventory.json"),
            "source_inventory_csv": rel_path(output_dir / "source_inventory.csv"),
            "evidence_axis_plan": rel_path(output_dir / "evidence_axis_plan.json"),
            "evidence_axis_plan_csv": rel_path(output_dir / "evidence_axis_plan.csv"),
            "relation_family_plan": rel_path(output_dir / "relation_family_plan.csv"),
            "route_decision": rel_path(output_dir / "route_decision.csv"),
            "feature_boundary": rel_path(output_dir / "feature_boundary.json"),
            "runner_contract": rel_path(output_dir / "runner_contract.json"),
            "report": rel_path(output_dir / "report.md"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "boundary": {
            "split": "train_only_plan",
            "validation_usage": False,
            "test_usage": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "materializes_candidate_rows": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
        },
    }


def report_text(summary: dict[str, Any], source_inventory: dict[str, Any]) -> str:
    three = source_inventory["three_rscan"]
    visual = source_inventory["visual_annotation_audit"]
    attachment = source_inventory["attachment_packet_template"]
    decision = summary["plan_decision"]
    return "\n".join(
        [
            "# Compatibility Dataset V3 Support/Contact Visual-Mesh Evidence Plan",
            "",
            "## Status",
            "",
            "```text",
            f"status = {summary['status']}",
            f"selected_route = {summary['selected_route']}",
            f"next_todo = {summary['next_todo']}",
            f"validation_errors = {summary['validation_errors']}",
            "```",
            "",
            "## Why This Plan Exists",
            "",
            "The previous support/contact evidence probe blocked numeric-only smoke. The queue is large,",
            "but the current numeric view exposes mostly distance, overlap, vertical gap, and OBB top/bottom",
            "fields. It does not expose role/orientation, contact direction, surface normals, mesh contact,",
            "or multi-view evidence.",
            "",
            "## Source Snapshot",
            "",
            "```text",
            f"3RScan scan dirs = {three.get('scan_dirs')}",
            f"mesh refined obj = {three.get('mesh_refined_v2_obj')}",
            f"aligned instance ply = {three.get('labels_instances_align_annotated_v2_ply')}",
            f"sequence.zip = {three.get('sequence_zip')}",
            f"visual contact sheets = {visual.get('contact_sheet_count')}",
            f"visual support/contact sheets = {visual.get('support_contact_sheet_count')}",
            f"attachment packet template dirs = {attachment.get('packet_dirs')}",
            "```",
            "",
            "## Decision",
            "",
            "```text",
            f"numeric_only_support_contact_smoke_allowed = {decision['numeric_only_support_contact_smoke_allowed']}",
            f"mesh_pose_contact_evidence_required = {decision['mesh_pose_contact_evidence_required']}",
            f"multiview_model_input_allowed_now = {decision['multiview_model_input_allowed_now']}",
            f"multiview_audit_first = {decision['multiview_audit_first']}",
            f"attachment_packets_reuse_as_labels = {decision['attachment_packets_reuse_as_labels']}",
            f"attachment_packet_builder_reuse_as_template = {decision['attachment_packet_builder_reuse_as_template']}",
            "```",
            "",
            "## Evidence Plan",
            "",
            "- Primary next evidence: mesh instance points, contact surface geometry, role/orientation/pose.",
            "- Secondary evidence: multi-view co-visibility and crop quality as `Q_e` / audit evidence first.",
            "- Control evidence: current numeric OBB/distance/overlap fields remain baselines and shortcut checks.",
            "- Attachment packet assets can be reused as rendering/template references, not as support/contact labels.",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
            "The next runner should inventory whether support/contact train candidates can be joined to",
            "3RScan mesh, instance labels, sequence frames, and packet-rendering assets before any new",
            "materialization or learned smoke is allowed.",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    probe_summary = read_json(args.probe_runner_dir / "summary.json")
    probe_validation = read_jsonl(args.probe_runner_dir / "validation_errors.jsonl")
    errors = validate_probe(probe_summary, probe_validation)

    source_inventory = {
        "three_rscan": scan_3rscan(args.three_rscan_root),
        "visual_annotation_audit": scan_visual_audit(args.visual_audit_root),
        "attachment_packet_template": scan_attachment_packets(args.attachment_packet_root),
    }

    summary = build_summary(probe_summary, source_inventory, errors, output_dir)
    evidence_rows = evidence_axis_rows()
    family_rows = relation_family_rows()
    routes = route_rows()
    boundary = feature_boundary()
    contract = runner_contract()

    source_rows = []
    for source_name, values in source_inventory.items():
        row = {"source": source_name}
        row.update(values)
        for key, value in list(row.items()):
            if isinstance(value, (dict, list)):
                row[key] = json.dumps(value, ensure_ascii=False, sort_keys=True)
        source_rows.append(row)

    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "source_inventory.json", source_inventory)
    write_csv(output_dir / "source_inventory.csv", source_rows)
    write_json(output_dir / "evidence_axis_plan.json", evidence_rows)
    write_csv(output_dir / "evidence_axis_plan.csv", evidence_rows)
    write_csv(output_dir / "relation_family_plan.csv", family_rows)
    write_csv(output_dir / "route_decision.csv", routes)
    write_json(output_dir / "feature_boundary.json", boundary)
    write_json(output_dir / "runner_contract.json", contract)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    (output_dir / "report.md").write_text(report_text(summary, source_inventory), encoding="utf-8")

    print(f"status={summary['status']}")
    print(f"selected_route={summary['selected_route']}")
    print(f"next={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
