#!/usr/bin/env python3
"""Plan the H002 v19 attachment independent-evidence repair route."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PATH_DIR = RGA_ROOT / "reliability_target_v18_attachment_deferred_path_decision_after_audit"
DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v18_attachment_deferred_target_independence_audit"
DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v18_attachment_deferred_label_ingestion"
DEFAULT_CANDIDATE_DIR = RGA_ROOT / "reliability_target_v18_attachment_deferred_candidate_mining"
DEFAULT_CAPACITY_DIR = RGA_ROOT / "reliability_target_v17_attachment_deferred_witness_schema_capacity_scan"
DEFAULT_3RSCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v19_attachment_deferred_independent_evidence_repair_plan"

EXPECTED_PATH_STATUS = "h002_reliability_target_v18_attachment_deferred_path_decision_select_v19_independent_evidence_repair_plan"
EXPECTED_PATH_NEXT = "reliability_target_v19_attachment_deferred_independent_evidence_repair_plan"
EXPECTED_SELECTED_PATH = "freeze_v18_attachment_diagnostic_select_v19_independent_evidence_repair_plan"
EXPECTED_AUDIT_STATUS = "h002_reliability_target_v18_attachment_deferred_target_independence_audit_blocked_positive_sparse_and_shortcut_risk"
EXPECTED_INGESTION_STATUS = "h002_reliability_target_v18_attachment_deferred_label_ingested_positive_sparse_with_probe_risk"
EXPECTED_CANDIDATE_STATUS = "h002_reliability_target_v18_attachment_deferred_candidate_mining_ready_for_label_fill"
EXPECTED_CAPACITY_STATUS = "h002_reliability_target_v17_attachment_deferred_witness_schema_capacity_scan_passed_ready_for_path_decision"

STATUS = "h002_reliability_target_v19_attachment_deferred_independent_evidence_repair_plan_ready_for_source_inventory"
NEXT_TODO = "reliability_target_v19_attachment_deferred_independent_evidence_source_inventory"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-dir", type=Path, default=DEFAULT_PATH_DIR)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE_DIR)
    parser.add_argument("--capacity-dir", type=Path, default=DEFAULT_CAPACITY_DIR)
    parser.add_argument("--three-rscan-root", type=Path, default=DEFAULT_3RSCAN_ROOT)
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


def false_boundary_errors(source: str, boundary: dict[str, Any], keys: list[str]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for key in keys:
        if boundary.get(key) is not False:
            errors.append(
                {
                    "error_type": "boundary_violation",
                    "source": source,
                    "key": key,
                    "expected": False,
                    "actual": boundary.get(key),
                }
            )
    return errors


def validate_inputs(
    path_summary: dict[str, Any],
    audit_summary: dict[str, Any],
    ingestion_summary: dict[str, Any],
    candidate_summary: dict[str, Any],
    capacity_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected = [
        ("path_decision", path_summary, EXPECTED_PATH_STATUS),
        ("target_audit", audit_summary, EXPECTED_AUDIT_STATUS),
        ("label_ingestion", ingestion_summary, EXPECTED_INGESTION_STATUS),
        ("candidate_mining", candidate_summary, EXPECTED_CANDIDATE_STATUS),
        ("capacity_scan", capacity_summary, EXPECTED_CAPACITY_STATUS),
    ]
    for source, payload, expected_status in expected:
        if payload.get("status") != expected_status:
            errors.append(
                {
                    "error_type": "unexpected_status",
                    "source": source,
                    "expected": expected_status,
                    "actual": payload.get("status"),
                }
            )
        if payload.get("validation_errors") not in (None, 0):
            errors.append(
                {
                    "error_type": "upstream_validation_errors_present",
                    "source": source,
                    "actual": payload.get("validation_errors"),
                }
            )

    if path_summary.get("next_todo") != EXPECTED_PATH_NEXT:
        errors.append({"error_type": "unexpected_path_next", "expected": EXPECTED_PATH_NEXT, "actual": path_summary.get("next_todo")})
    if path_summary.get("selected_path") != EXPECTED_SELECTED_PATH:
        errors.append({"error_type": "unexpected_selected_path", "expected": EXPECTED_SELECTED_PATH, "actual": path_summary.get("selected_path")})

    common_false = [
        "validation_usage",
        "test_usage",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "rga_redefined_as_lh_only",
        "multi_view_as_model_input",
        "hidden_fields_as_model_input",
    ]
    for source, payload, _ in expected:
        errors.extend(false_boundary_errors(source, payload.get("boundary", {}), common_false))

    path_boundary = path_summary.get("boundary", {})
    if path_boundary.get("multi_view_as_audit_or_confirmation_evidence_only") is not True:
        errors.append(
            {
                "error_type": "unexpected_multiview_policy",
                "expected": True,
                "actual": path_boundary.get("multi_view_as_audit_or_confirmation_evidence_only"),
            }
        )

    relation = audit_summary.get("target_decisions", {}).get("relation_binary", {})
    if relation.get("class_counts") != {"0": 81, "1": 33}:
        errors.append({"error_type": "unexpected_v18_class_counts", "expected": {"0": 81, "1": 33}, "actual": relation.get("class_counts")})
    if relation.get("strict_clear_slice_count") != 0:
        errors.append({"error_type": "relation_strict_slice_unexpected", "actual": relation.get("strict_clear_slice_count")})
    if relation.get("diagnostic_clear_slice_count") != 0:
        errors.append({"error_type": "relation_diagnostic_slice_unexpected", "actual": relation.get("diagnostic_clear_slice_count")})

    candidate_counts = candidate_summary.get("counts", {})
    if candidate_counts.get("selected_rows") != 240:
        errors.append({"error_type": "unexpected_candidate_rows", "expected": 240, "actual": candidate_counts.get("selected_rows")})
    if candidate_counts.get("primary_binary_candidate_rows") != 160:
        errors.append({"error_type": "unexpected_primary_candidate_rows", "expected": 160, "actual": candidate_counts.get("primary_binary_candidate_rows")})

    capacity_decision = capacity_summary.get("capacity_decision", {})
    if capacity_decision.get("capacity_pass") is not True:
        errors.append({"error_type": "capacity_expected_pass", "actual": capacity_decision.get("capacity_pass")})
    return errors


def probe_local_sources(three_rscan_root: Path) -> dict[str, Any]:
    root = as_abs(three_rscan_root)
    probe = {
        "source_probe_only": True,
        "root": rel_path(root),
        "exists": root.exists(),
        "scan_dir_count_sampled": 0,
        "sample_scan_dirs": [],
        "sample_multi_view_dirs": 0,
        "sample_sequence_dirs": 0,
        "sample_multi_view_file_examples": [],
        "inventory_required_next": True,
    }
    if not root.exists():
        return probe
    scan_dirs = sorted([path for path in root.iterdir() if path.is_dir()])
    sample_dirs = scan_dirs[:40]
    probe["scan_dir_count_sampled"] = len(sample_dirs)
    probe["sample_scan_dirs"] = [path.name for path in sample_dirs[:10]]
    examples: list[str] = []
    for scan_dir in sample_dirs:
        mv_dir = scan_dir / "multi_view"
        seq_dir = scan_dir / "sequence"
        if mv_dir.is_dir():
            probe["sample_multi_view_dirs"] += 1
            for item in sorted(mv_dir.iterdir())[:5]:
                if item.is_file() and len(examples) < 12:
                    examples.append(rel_path(item))
        if seq_dir.is_dir():
            probe["sample_sequence_dirs"] += 1
    probe["sample_multi_view_file_examples"] = examples
    return probe


def build_upstream_snapshot(
    path_summary: dict[str, Any],
    audit_summary: dict[str, Any],
    ingestion_summary: dict[str, Any],
    candidate_summary: dict[str, Any],
    capacity_summary: dict[str, Any],
) -> dict[str, Any]:
    relation = audit_summary["target_decisions"]["relation_binary"]
    connected = audit_summary["target_decisions"]["connected_diagnostic"]
    geometry = audit_summary["target_decisions"]["geometry_support_binary"]
    return {
        "v18_role": "diagnostic_only_negative_target_construction_evidence",
        "path_decision": {
            "selected_path": path_summary.get("selected_path"),
            "option_verdicts": path_summary.get("option_verdicts"),
        },
        "relation_target": {
            "rows": relation["rows"],
            "class_counts": relation["class_counts"],
            "min_class_count": relation["min_class_count"],
            "class_mass_pass": relation["class_mass_pass"],
            "strict_clear_slice_count": relation["strict_clear_slice_count"],
            "diagnostic_clear_slice_count": relation["diagnostic_clear_slice_count"],
        },
        "connected_diagnostic": {
            "rows": connected["rows"],
            "class_counts": connected["class_counts"],
            "status": connected["status"],
        },
        "geometry_support_auxiliary": {
            "rows": geometry["rows"],
            "class_counts": geometry["class_counts"],
            "class_mass_pass": geometry["class_mass_pass"],
            "strict_clear_slice_count": geometry["strict_clear_slice_count"],
            "why_not_primary": "geometry support is an evidence-axis target, not relation reliability",
        },
        "shortcut_risk": {
            "full_quick_probe_risk_flags": audit_summary["counts"]["full_quick_probe_risk_flags"],
            "slice_blocking_risk_flags": audit_summary["counts"]["slice_blocking_risk_flags"],
        },
        "candidate_source": {
            "selected_rows": candidate_summary["counts"]["selected_rows"],
            "primary_binary_candidate_rows": candidate_summary["counts"]["primary_binary_candidate_rows"],
            "diagnostic_rows": candidate_summary["counts"]["diagnostic_rows"],
            "uncertainty_audit_rows": candidate_summary["counts"]["uncertainty_audit_rows"],
            "unique_scans": candidate_summary["counts"]["unique_scans"],
            "unique_visible_label_pairs": candidate_summary["counts"]["unique_visible_label_pairs"],
        },
        "capacity_prior": {
            "attachment_rows": capacity_summary["counts"]["attachment_rows"],
            "raw_feature_join_coverage": capacity_summary["counts"]["raw_feature_join_coverage"],
            "cell_counts": capacity_summary["counts"]["cell_counts"],
            "selection_deficits": capacity_summary["selection_summary"]["deficits"],
        },
        "label_ingestion": {
            "binary_rows": ingestion_summary["counts"]["binary_rows"],
            "binary_target": ingestion_summary["counts"]["binary_target"],
            "geometry_support_rows": ingestion_summary["counts"]["geometry_support_rows"],
            "geometry_support_target": ingestion_summary["counts"]["geometry_support_target"],
            "abstain_rows": ingestion_summary["counts"]["abstain_rows"],
            "target_viability": ingestion_summary["target_viability"],
        },
    }


def independent_evidence_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_v19_attachment_independent_evidence_contract_v1",
        "purpose": "Separate relation-reliability labels from the same 3D geometry summaries used as evidence factors.",
        "core_rule": "audit evidence may decide labels, but audit labels must not be reused as deployable model input features",
        "evidence_roles": {
            "S_e": {
                "role": "source semantic plausibility",
                "examples": ["semantic score", "rank", "source predicate"],
                "not_label_evidence": True,
            },
            "G_3D_e": {
                "role": "deployable geometry evidence",
                "examples": ["distance", "overlap", "vertical relation", "anchor bucket", "floor-support confound"],
                "may_be_model_input_after_target_passes": True,
            },
            "C_e": {
                "role": "coverage evidence",
                "examples": ["raw geometry available", "view evidence available", "endpoint visible"],
                "may_be_model_input_after_target_passes": True,
            },
            "U_e": {
                "role": "uncertainty or abstain evidence",
                "examples": ["large OBB overlap", "thin connector missing", "functional connection ambiguity"],
                "may_be_model_input_after_target_passes": True,
            },
            "A_ind_e": {
                "role": "independent audit supervision source",
                "examples": ["multi-view crops", "co-visible context", "mesh/contact boundary", "manual visual/mesh audit"],
                "model_input_now": False,
                "label_decision_only": True,
            },
            "V_mv_e": {
                "role": "future deployable visual evidence factor",
                "model_input_now": False,
                "promotion_rule": "promote only after target-independent labels exist and visual-feature controls are defined",
            },
        },
        "forbidden_shortcuts": [
            "cell_id_hidden",
            "sampling_queue_hidden",
            "geometry_status_hidden",
            "machine_hint_hidden",
            "rank_band_hidden",
            "review_notes_v18",
            "relation_reliability_state_v18",
            "geometry_support_state_v18",
            "direct witness-summary strings as model inputs",
        ],
        "allowed_audit_only_sources": [
            "3RScan multi_view object crops",
            "3RScan sequence frames for context lookup",
            "mesh or point cloud contact-boundary inspection if available",
            "manual audit notes derived from visual/mesh inspection",
        ],
    }


def label_schema_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_v19_attachment_label_schema_v1",
        "principle": "geometry validity and relation reliability are separate labels",
        "stage_a_geometry_support": {
            "labels": ["supports", "contradicts", "ambiguous", "not_evaluable"],
            "source": "G_3D_e only",
            "purpose": "record whether 3D geometry can support attachment-like relation",
            "not_primary_target": True,
        },
        "stage_b_independent_attachment_reliability": {
            "labels": ["accept_reliable_attachment", "reject_unreliable_attachment", "abstain_uncertain"],
            "source": "A_ind_e plus visible object identity; not hidden construction metadata",
            "primary_target_candidate": True,
            "positive_criteria": [
                "subject/object identity is clear enough",
                "independent visual/mesh evidence supports a physical attachment or hanging relation",
                "relation is more informative than ordinary support/contact/proximity",
                "coverage is sufficient or uncertainty is low",
            ],
            "reject_criteria": [
                "independent evidence contradicts attachment or hanging",
                "layout is better explained by floor support, ordinary contact, or proximity",
                "wrong endpoint or wrong direction",
                "object pair is visible but relation is not physically meaningful",
            ],
            "abstain_criteria": [
                "subject/object not sufficiently visible",
                "connection boundary occluded",
                "mesh/visual evidence unavailable",
                "functional connection cannot be decided without additional evidence",
            ],
        },
        "stage_c_connected_diagnostic": {
            "labels": ["diagnostic_connected_possible", "diagnostic_connected_ambiguous", "diagnostic_connected_reject"],
            "source": "A_ind_e only",
            "primary_target_candidate": False,
            "promotion_condition": "promote only if source inventory finds enough visual/mesh-confirmable functional connections and later target-independence passes",
        },
    }


def source_inventory_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_v19_attachment_source_inventory_contract_v1",
        "next_todo": NEXT_TODO,
        "purpose": "Check whether the v18 attachment rows have enough independent visual/mesh audit evidence before any new labels are filled.",
        "input_rows": {
            "candidate_packet": rel_path(DEFAULT_CANDIDATE_DIR / "review_packet_v18.tsv"),
            "hidden_manifest": rel_path(DEFAULT_CANDIDATE_DIR / "hidden_audit_manifest_v18.jsonl"),
            "ingested_rows": rel_path(DEFAULT_INGESTION_DIR / "ingested_rows.jsonl"),
        },
        "local_source_roots_to_probe": {
            "three_rscan_scans": rel_path(DEFAULT_3RSCAN_ROOT),
            "multi_view_pattern": "local_dataset/3RScan/scans/<scan_id>/multi_view/instance_<object_id>_class_<label>_*",
            "sequence_pattern": "local_dataset/3RScan/scans/<scan_id>/sequence/*",
            "mesh_or_point_cloud_pattern": "to be discovered in source inventory",
        },
        "required_inventory_outputs": [
            "per-row subject crop count",
            "per-row object crop count",
            "same-view or co-visible evidence candidate count",
            "crop quality proxy from filename score/ratio when available",
            "sequence context availability",
            "mesh/point-cloud artifact availability",
            "audit-ready / not-audit-ready decision",
            "reason for missing evidence",
        ],
        "inventory_gates_before_label_repair": {
            "primary_rows_with_subject_and_object_crops_min": 100,
            "primary_rows_with_possible_covisible_or_same_view_context_min": 60,
            "hanging_or_attached_each_audit_ready_min": 30,
            "connected_rows_kept_diagnostic": True,
            "validation_errors_required": 0,
        },
        "forbidden_at_inventory_stage": [
            "do not fill new reliability labels",
            "do not train posterior",
            "do not treat crop score as deployable model input",
            "do not read validation/test rows",
        ],
    }


def target_independence_plan() -> dict[str, Any]:
    return {
        "schema_version": "h002_v19_attachment_future_independence_plan_v1",
        "pre_posterior_minimums": {
            "usable_binary_rows": 120,
            "accept_rows": 50,
            "reject_rows": 50,
            "strict_clear_slice_count_min": 1,
            "diagnostic_clear_slice_count_min": 1,
        },
        "future_shortcut_audits": [
            "predicate_label",
            "subject_object_visible_pair",
            "scan_id",
            "subject_label",
            "object_label",
            "rank_band_hidden",
            "semantic_score_bin_hidden",
            "cell_id_hidden",
            "sampling_queue_hidden",
            "geometry_status_hidden",
            "machine_hint_hidden",
            "anchor_bucket_hidden",
            "visual_audit_source_id",
            "crop_count_bucket",
            "coverage_state",
        ],
        "required_controls_if_visual_factor_is_later_promoted": [
            "wrong-pair view",
            "shuffled-view",
            "no-view or low-visibility rows",
            "same-predicate controlled split",
            "same-rank-band controlled split",
            "same-geometry-status controlled split",
            "same-visual-coverage controlled split",
        ],
        "posterior_smoke_allowed_after_this_plan": False,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    snap = summary["upstream_snapshot"]
    lines = [
        "# H002 V19 Attachment Independent-Evidence Repair Plan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        f"multi_view_as_model_input = {summary['boundary']['multi_view_as_model_input']}",
        "```",
        "",
        "## Decision",
        "",
        "Design an independent label/audit evidence repair route before any new attachment labels or posterior smoke.",
        "",
        "## Why",
        "",
        "The v18 target failed because the label surface was too close to geometry and construction metadata, not because the posterior combiner was too weak.",
        "",
        "```text",
        f"relation_binary = {snap['relation_target']['class_counts']}",
        f"strict_clear_slice_count = {snap['relation_target']['strict_clear_slice_count']}",
        f"diagnostic_clear_slice_count = {snap['relation_target']['diagnostic_clear_slice_count']}",
        f"full_quick_probe_risk_flags = {snap['shortcut_risk']['full_quick_probe_risk_flags']}",
        f"slice_blocking_risk_flags = {snap['shortcut_risk']['slice_blocking_risk_flags']}",
        "```",
        "",
        "## Plan",
        "",
        "- Keep `attached to` and `hanging on` as the primary repair scope.",
        "- Keep `connected to` diagnostic-only until visual/mesh evidence can verify functional connection.",
        "- Use multi-view/mesh only as audit or confirmation evidence in the next step.",
        "- Do not create deployable `V_mv_e` features yet.",
        "- First run source inventory over the v18 rows to see whether independent evidence exists.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    path_dir = as_abs(args.path_dir)
    audit_dir = as_abs(args.audit_dir)
    ingestion_dir = as_abs(args.ingestion_dir)
    candidate_dir = as_abs(args.candidate_dir)
    capacity_dir = as_abs(args.capacity_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    path_summary = read_json(path_dir / "summary.json")
    audit_summary = read_json(audit_dir / "summary.json")
    ingestion_summary = read_json(ingestion_dir / "summary.json")
    candidate_summary = read_json(candidate_dir / "summary.json")
    capacity_summary = read_json(capacity_dir / "summary.json")

    validation_errors = validate_inputs(path_summary, audit_summary, ingestion_summary, candidate_summary, capacity_summary)
    upstream = build_upstream_snapshot(path_summary, audit_summary, ingestion_summary, candidate_summary, capacity_summary)
    evidence = independent_evidence_contract()
    labels = label_schema_contract()
    inventory = source_inventory_contract()
    independence = target_independence_plan()
    source_probe = probe_local_sources(args.three_rscan_root)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "upstream_snapshot": output_dir / "upstream_snapshot.json",
        "evidence_contract": output_dir / "independent_evidence_contract.json",
        "label_schema": output_dir / "label_schema_contract.json",
        "source_inventory_contract": output_dir / "source_inventory_contract.json",
        "target_independence_plan": output_dir / "target_independence_plan.json",
        "local_source_probe": output_dir / "local_source_probe.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    boundary = {
        "split": "train_only",
        "validation_usage": False,
        "test_usage": False,
        "fills_new_labels": False,
        "ingests_existing_labels": False,
        "candidate_mining_allowed": False,
        "source_inventory_only_next": True,
        "hidden_fields_as_model_input": False,
        "trains_new_posterior": False,
        "posterior_smoke_allowed": False,
        "paper_evidence_allowed": False,
        "h001_artifacts_modified": False,
        "rga_redefined_as_lh_only": False,
        "multi_view_as_model_input": False,
        "multi_view_as_audit_or_confirmation_evidence_only": True,
        "mesh_as_audit_or_confirmation_evidence_only": True,
    }
    summary = {
        "schema_version": "h002_reliability_target_v19_attachment_deferred_independent_evidence_repair_plan_v1",
        "status": STATUS if not validation_errors else "h002_reliability_target_v19_attachment_deferred_independent_evidence_repair_plan_errors",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "path_decision_summary": rel_path(path_dir / "summary.json"),
            "target_audit_summary": rel_path(audit_dir / "summary.json"),
            "label_ingestion_summary": rel_path(ingestion_dir / "summary.json"),
            "candidate_mining_summary": rel_path(candidate_dir / "summary.json"),
            "capacity_scan_summary": rel_path(capacity_dir / "summary.json"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "upstream_snapshot": upstream,
        "selected_repair_route": {
            "name": "independent_visual_or_mesh_audit_packet_before_labels",
            "primary_scope": ["attached to", "hanging on"],
            "diagnostic_scope": ["connected to"],
            "next_gate": NEXT_TODO,
            "posterior_smoke_allowed": False,
        },
        "local_source_probe": source_probe,
        "boundary": boundary,
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO,
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["upstream_snapshot"], upstream)
    write_json(output_paths["evidence_contract"], evidence)
    write_json(output_paths["label_schema"], labels)
    write_json(output_paths["source_inventory_contract"], inventory)
    write_json(output_paths["target_independence_plan"], independence)
    write_json(output_paths["local_source_probe"], source_probe)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"selected_route={summary['selected_repair_route']['name']}")
    print(f"primary_scope={','.join(summary['selected_repair_route']['primary_scope'])}")
    print(f"diagnostic_scope={','.join(summary['selected_repair_route']['diagnostic_scope'])}")
    print(f"source_probe_exists={summary['local_source_probe']['exists']}")
    print(f"source_probe_sample_multi_view_dirs={summary['local_source_probe']['sample_multi_view_dirs']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"multi_view_as_model_input={summary['boundary']['multi_view_as_model_input']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
