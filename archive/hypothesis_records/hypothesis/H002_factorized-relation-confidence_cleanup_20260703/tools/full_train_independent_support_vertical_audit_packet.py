#!/usr/bin/env python3
"""Build the selected support/vertical audit packet after H002 claim-boundary lock."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_REVISED_ROWS = RGA_ROOT / "independent_revised_factor_dataset_codex_ver/revised_factor_rows.jsonl"
DEFAULT_CLAIM_BOUNDARY = RGA_ROOT / "independent_revised_factor_claim_boundary_codex_ver/summary.json"
DEFAULT_GAP_AUDIT_DIR = RGA_ROOT / "asset_packet_gap_audit"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_audit_packet_codex_ver"

SELECTED_FAMILIES = {"support_contact", "relative_vertical"}
PROXIMITY_FAMILY = "proximity"

READY_SHEETS = [
    "label_ready_support_contact_sheet_with_packets.tsv",
    "label_ready_relative_vertical_sheet_with_packets.tsv",
]

FORBIDDEN_LABELER_SURFACE_SUBSTRINGS = [
    "score",
    "rank",
    "p_geom",
    "geometry_status",
    "h001_verification",
    "queue",
    "label_match",
    "proposed",
    "candidate_axis",
    "prediction_id",
    "target",
    "final_controlled",
    "failure_taxonomy",
    "matched_gt",
    "matched_predicate",
    "bucket",
    "machine_hint",
    "reason_code",
    "consistency",
    "disagreement",
    "underconfidence",
    "overconfidence",
    "label_source",
]

FORBIDDEN_PACKET_TEXT_SUBSTRINGS = [
    token
    for token in FORBIDDEN_LABELER_SURFACE_SUBSTRINGS
    if token != "target"
] + [
    "target_y",
    "posterior_target",
    "relation_validity_label",
]

LABELER_FIELDS = [
    "blind_review_id",
    "audit_scope",
    "scan_id",
    "scene_context_id",
    "subject_id",
    "subject_label",
    "predicate_label",
    "predicate_family",
    "object_id",
    "object_label",
    "endpoint_pair_note",
    "family_question",
    "positive_cues",
    "negative_cues",
    "evidence_packet_status",
    "multiview_packet",
    "pointcloud_or_mesh_packet",
    "contact_or_context_sheet",
    "witness_distance_xy_m",
    "witness_distance_3d_m",
    "witness_center_delta_z_m",
    "witness_vertical_gap_subject_on_object_m",
    "witness_projected_iou_xy",
    "witness_subject_overlap_xy",
    "witness_object_overlap_xy",
    "witness_normalized_distance_xy",
    "witness_support_contact_gap_abs",
    "witness_support_contact_xy_overlap",
    "witness_relative_vertical_signed_margin",
    "witness_relative_vertical_sign_agreement",
    "reviewer_id",
    "review_round",
    "subject_identity_valid",
    "object_identity_valid",
    "object_pair_visible",
    "relation_visible_or_inferable",
    "visual_3d_support",
    "relation_informativeness",
    "independent_relation_label",
    "confidence",
    "evidence_notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revised-rows", type=Path, default=DEFAULT_REVISED_ROWS)
    parser.add_argument("--claim-boundary", type=Path, default=DEFAULT_CLAIM_BOUNDARY)
    parser.add_argument("--gap-audit-dir", type=Path, default=DEFAULT_GAP_AUDIT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    path = smoke.as_abs(path)
    try:
        return str(path.relative_to(smoke.REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with smoke.as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_tsv(path: Path) -> list[dict[str, Any]]:
    with smoke.as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def safe_float(value: Any, default: float | None = None) -> float | None:
    result = smoke.safe_float(value, default if default is not None else 0.0)
    if default is None and value is None:
        return None
    return result


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def load_ready_sheets(gap_audit_dir: Path) -> dict[str, dict[str, Any]]:
    ready: dict[str, dict[str, Any]] = {}
    for name in READY_SHEETS:
        for row in read_tsv(gap_audit_dir / name):
            ready[str(row["blind_review_id"])] = row
    return ready


def selected_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if str(row["identity"]["predicate_family"]) in SELECTED_FAMILIES
    ]


def proximity_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if str(row["identity"]["predicate_family"]) == PROXIMITY_FAMILY
    ]


def make_labeler_row(row: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    identity = row["identity"]
    d4 = row["baseline_inputs"]["D4_coverage_uncertainty_shrinkage"]
    audit_scope = "selected_support_vertical_claim_scope"
    return {
        "blind_review_id": identity["blind_review_id"],
        "audit_scope": audit_scope,
        "scan_id": identity["scan_id"],
        "scene_context_id": identity["subgraph_id"],
        "subject_id": identity["subject_id"],
        "subject_label": identity["subject_label"],
        "predicate_label": identity["predicate_label"],
        "predicate_family": identity["predicate_family"],
        "object_id": identity["object_id"],
        "object_label": identity["object_label"],
        "endpoint_pair_note": packet.get("endpoint_pair_note", ""),
        "family_question": packet.get("family_question", ""),
        "positive_cues": packet.get("positive_cues", ""),
        "negative_cues": packet.get("negative_cues", ""),
        "evidence_packet_status": packet.get("evidence_packet_status", ""),
        "multiview_packet": packet.get("multiview_packet", ""),
        "pointcloud_or_mesh_packet": packet.get("pointcloud_or_mesh_packet", ""),
        "contact_or_context_sheet": packet.get("contact_or_context_sheet", ""),
        "witness_distance_xy_m": fmt(safe_float(d4.get("raw_distance_xy"))),
        "witness_distance_3d_m": fmt(safe_float(d4.get("raw_distance_3d"))),
        "witness_center_delta_z_m": fmt(safe_float(d4.get("raw_center_delta_z"))),
        "witness_vertical_gap_subject_on_object_m": fmt(safe_float(d4.get("raw_vertical_gap_subject_on_object"))),
        "witness_projected_iou_xy": fmt(safe_float(d4.get("raw_projected_iou_xy"))),
        "witness_subject_overlap_xy": fmt(safe_float(d4.get("raw_projected_subject_overlap_ratio"))),
        "witness_object_overlap_xy": fmt(safe_float(d4.get("raw_projected_object_overlap_ratio"))),
        "witness_normalized_distance_xy": fmt(safe_float(d4.get("raw_normalized_distance_xy"))),
        "witness_support_contact_gap_abs": fmt(safe_float(d4.get("support_contact_x_contact_gap_abs"))),
        "witness_support_contact_xy_overlap": fmt(safe_float(d4.get("support_contact_x_xy_support_overlap"))),
        "witness_relative_vertical_signed_margin": fmt(safe_float(d4.get("relative_vertical_x_signed_margin"))),
        "witness_relative_vertical_sign_agreement": fmt(safe_float(d4.get("relative_vertical_x_sign_agreement"))),
        "reviewer_id": "",
        "review_round": "",
        "subject_identity_valid": "",
        "object_identity_valid": "",
        "object_pair_visible": "",
        "relation_visible_or_inferable": "",
        "visual_3d_support": "",
        "relation_informativeness": "",
        "independent_relation_label": "",
        "confidence": "",
        "evidence_notes": "",
    }


def make_internal_reference(row: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    identity = row["identity"]
    target = row["target"]
    d4 = row["baseline_inputs"]["D4_coverage_uncertainty_shrinkage"]
    return {
        "blind_review_id": identity["blind_review_id"],
        "prediction_id_hidden": identity["prediction_id"],
        "scan_id": identity["scan_id"],
        "subgraph_id": identity["subgraph_id"],
        "subject_id": identity["subject_id"],
        "subject_label": identity["subject_label"],
        "predicate_label": identity["predicate_label"],
        "predicate_family": identity["predicate_family"],
        "object_id": identity["object_id"],
        "object_label": identity["object_label"],
        "posterior_target_y_hidden": target["y"],
        "relation_validity_label_hidden": target.get("relation_validity_label"),
        "label_use_hidden": target.get("label_use"),
        "label_source_hidden": target.get("label_source"),
        "reviewer_id_hidden": target.get("reviewer_id"),
        "human_confirmed_hidden": target.get("human_confirmed"),
        "geometry_status_hidden": target.get("geometry_status_hidden"),
        "label_match_status_hidden": target.get("label_match_status_hidden"),
        "proposed_audit_role_hidden": target.get("proposed_audit_role_hidden"),
        "queue_kind_hidden": target.get("queue_kind_hidden"),
        "rank_band_hidden": target.get("rank_band_hidden"),
        "semantic_rank_hidden": target.get("semantic_rank"),
        "semantic_score_norm_hidden": d4.get("semantic_score_norm"),
        "p_geom_valid_hidden": d4.get("p_geom_valid"),
        "absolute_disagreement_hidden": d4.get("absolute_disagreement"),
        "evidence_packet_status": packet.get("evidence_packet_status", ""),
        "multiview_packet": packet.get("multiview_packet", ""),
        "pointcloud_or_mesh_packet": packet.get("pointcloud_or_mesh_packet", ""),
        "contact_or_context_sheet": packet.get("contact_or_context_sheet", ""),
        "post_label_join_only": True,
    }


def make_risk_slice(row: dict[str, Any]) -> dict[str, Any]:
    identity = row["identity"]
    target = row["target"]
    d4 = row["baseline_inputs"]["D4_coverage_uncertainty_shrinkage"]
    return {
        "blind_review_id": identity["blind_review_id"],
        "scan_id": identity["scan_id"],
        "subgraph_id": identity["subgraph_id"],
        "subject_id": identity["subject_id"],
        "subject_label": identity["subject_label"],
        "predicate_label": identity["predicate_label"],
        "predicate_family": identity["predicate_family"],
        "object_id": identity["object_id"],
        "object_label": identity["object_label"],
        "posterior_target_y_hidden": target["y"],
        "relation_validity_label_hidden": target.get("relation_validity_label"),
        "semantic_rank_hidden": target.get("semantic_rank"),
        "p_geom_valid_hidden": d4.get("p_geom_valid"),
        "risk_reason": "proximity excluded from main claim boundary after negative D4 ranking control",
    }


def surface_hits(rows: list[dict[str, Any]], fieldnames: list[str]) -> list[dict[str, Any]]:
    hits = []
    for field in fieldnames:
        lowered = field.lower()
        for token in FORBIDDEN_LABELER_SURFACE_SUBSTRINGS:
            if token in lowered:
                hits.append({"surface": "header", "field": field, "forbidden_token": token})
    for idx, row in enumerate(rows, start=1):
        for field in fieldnames:
            value = str(row.get(field, "")).lower()
            for token in FORBIDDEN_LABELER_SURFACE_SUBSTRINGS:
                if token in value:
                    hits.append(
                        {
                            "surface": "value",
                            "row_number": idx,
                            "field": field,
                            "forbidden_token": token,
                            "value_preview": str(row.get(field, ""))[:120],
                        }
                    )
    return hits


def packet_text_hits(rows: list[dict[str, Any]], limit: int = 30) -> list[dict[str, Any]]:
    hits = []
    sampled_paths = []
    for row in rows:
        for key in ["multiview_packet", "pointcloud_or_mesh_packet"]:
            value = row.get(key)
            if value:
                sampled_paths.append(smoke.as_abs(Path(value)))
        if len(sampled_paths) >= limit:
            break
    for path in sampled_paths[:limit]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        for token in FORBIDDEN_PACKET_TEXT_SUBSTRINGS:
            if token in text:
                hits.append(
                    {
                        "surface": "packet_text",
                        "path": rel_path(path),
                        "forbidden_token": token,
                    }
                )
    return hits


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Full-Train Support/Vertical Audit Packet",
        "",
        "## Boundary",
        "",
        "- Split: Open3DSG train-only.",
        "- Selected scope: support_contact + relative_vertical.",
        "- Proximity is excluded from the main audit packet and preserved as a risk slice.",
        "- Labeler sheets do not expose source score/rank, p_geom_valid, geometry_status, target labels, or hidden construction metadata.",
        "- Multi-view and mesh packets are audit evidence only, not posterior input.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| selected rows | {summary['counts']['selected_rows']} |",
        f"| support_contact rows | {summary['counts']['by_family'].get('support_contact', 0)} |",
        f"| relative_vertical rows | {summary['counts']['by_family'].get('relative_vertical', 0)} |",
        f"| proximity risk rows | {summary['counts']['proximity_risk_rows']} |",
        f"| labeler leakage hits | {summary['leakage_audit']['labeler_surface_hit_count']} |",
        f"| packet text leakage hits | {summary['leakage_audit']['packet_text_hit_count']} |",
        "",
        "## Output Files",
        "",
        "```text",
        summary["output_paths"]["support_vertical_audit_sheet"],
        summary["output_paths"]["support_contact_audit_sheet"],
        summary["output_paths"]["relative_vertical_audit_sheet"],
        summary["output_paths"]["internal_reference"],
        summary["output_paths"]["proximity_risk_slice"],
        summary["output_paths"]["manifest"],
        "```",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    claim_boundary = read_json(args.claim_boundary)
    revised_rows = smoke.read_jsonl(args.revised_rows)
    selected = selected_rows(revised_rows)
    proximity = proximity_rows(revised_rows)
    ready_by_id = load_ready_sheets(args.gap_audit_dir)

    missing = [
        row["identity"]["blind_review_id"]
        for row in selected
        if row["identity"]["blind_review_id"] not in ready_by_id
    ]
    if missing:
        raise RuntimeError(f"selected rows missing label-ready packet entries: {missing[:10]}")

    selected = sorted(
        selected,
        key=lambda row: (
            str(row["identity"]["predicate_family"]),
            str(row["identity"]["scan_id"]),
            str(row["identity"]["predicate_label"]),
            str(row["identity"]["blind_review_id"]),
        ),
    )
    labeler_rows = [
        make_labeler_row(row, ready_by_id[row["identity"]["blind_review_id"]])
        for row in selected
    ]
    support_rows = [row for row in labeler_rows if row["predicate_family"] == "support_contact"]
    vertical_rows = [row for row in labeler_rows if row["predicate_family"] == "relative_vertical"]
    internal_rows = [
        make_internal_reference(row, ready_by_id[row["identity"]["blind_review_id"]])
        for row in selected
    ]
    risk_rows = [make_risk_slice(row) for row in proximity]

    label_hits = surface_hits(labeler_rows, LABELER_FIELDS)
    text_hits = packet_text_hits(labeler_rows)
    status = (
        "full_train_independent_support_vertical_audit_packet_ready"
        if not label_hits and not text_hits
        else "full_train_independent_support_vertical_audit_packet_leakage_risk"
    )

    output_dir = smoke.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "summary_json": output_dir / "summary.json",
        "report_md": output_dir / "report.md",
        "support_vertical_audit_sheet": output_dir / "support_vertical_audit_sheet.tsv",
        "support_contact_audit_sheet": output_dir / "support_contact_audit_sheet.tsv",
        "relative_vertical_audit_sheet": output_dir / "relative_vertical_audit_sheet.tsv",
        "internal_reference": output_dir / "internal_reference_post_label_only.jsonl",
        "proximity_risk_slice": output_dir / "proximity_risk_slice_post_label_only.jsonl",
        "manifest": output_dir / "manifest.jsonl",
        "leakage_hits": output_dir / "leakage_hits.jsonl",
    }
    manifest_rows = [
        {
            "blind_review_id": row["blind_review_id"],
            "predicate_family": row["predicate_family"],
            "predicate_label": row["predicate_label"],
            "scan_id": row["scan_id"],
            "evidence_packet_status": row["evidence_packet_status"],
            "multiview_packet": row["multiview_packet"],
            "pointcloud_or_mesh_packet": row["pointcloud_or_mesh_packet"],
            "contact_or_context_sheet": row["contact_or_context_sheet"],
            "boundary": "audit_evidence_only_not_posterior_input",
        }
        for row in labeler_rows
    ]
    summary = {
        "schema_version": "h002_full_train_independent_support_vertical_audit_packet_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "validation_used": False,
        "input": {
            "revised_rows": rel_path(args.revised_rows),
            "claim_boundary": rel_path(args.claim_boundary),
            "claim_boundary_status": claim_boundary.get("status"),
            "gap_audit_dir": rel_path(args.gap_audit_dir),
        },
        "counts": {
            "selected_rows": len(labeler_rows),
            "by_family": dict(sorted(Counter(row["predicate_family"] for row in labeler_rows).items())),
            "by_packet_status": dict(sorted(Counter(row["evidence_packet_status"] for row in labeler_rows).items())),
            "proximity_risk_rows": len(risk_rows),
            "internal_reference_rows": len(internal_rows),
            "missing_packet_rows": len(missing),
        },
        "boundary": {
            "split": "train_only",
            "selected_scope": sorted(SELECTED_FAMILIES),
            "excluded_from_main_packet": [PROXIMITY_FAMILY],
            "multi_view_as_model_input": False,
            "mesh_or_pointcloud_as_model_input": False,
            "hidden_metadata_labeler_visible": False,
            "internal_reference_post_label_only": True,
        },
        "leakage_audit": {
            "status": "pass" if not label_hits and not text_hits else "fail",
            "forbidden_substrings": FORBIDDEN_LABELER_SURFACE_SUBSTRINGS,
            "packet_text_forbidden_substrings": FORBIDDEN_PACKET_TEXT_SUBSTRINGS,
            "labeler_surface_hit_count": len(label_hits),
            "packet_text_hit_count": len(text_hits),
            "hits_path": rel_path(output_paths["leakage_hits"]),
        },
        "next_todo": "full_train_independent_support_vertical_label_readiness",
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
    }

    write_tsv(output_paths["support_vertical_audit_sheet"], labeler_rows, LABELER_FIELDS)
    write_tsv(output_paths["support_contact_audit_sheet"], support_rows, LABELER_FIELDS)
    write_tsv(output_paths["relative_vertical_audit_sheet"], vertical_rows, LABELER_FIELDS)
    write_jsonl(output_paths["internal_reference"], internal_rows)
    write_jsonl(output_paths["proximity_risk_slice"], risk_rows)
    write_jsonl(output_paths["manifest"], manifest_rows)
    write_jsonl(output_paths["leakage_hits"], label_hits + text_hits)
    write_json(output_paths["summary_json"], summary)
    write_report(output_paths["report_md"], summary)

    print(
        "status={status} validation_used={validation_used} selected_rows={selected} "
        "support={support} vertical={vertical} leakage_hits={hits} next={next_todo}".format(
            status=summary["status"],
            validation_used=summary["validation_used"],
            selected=summary["counts"]["selected_rows"],
            support=summary["counts"]["by_family"].get("support_contact", 0),
            vertical=summary["counts"]["by_family"].get("relative_vertical", 0),
            hits=summary["leakage_audit"]["labeler_surface_hit_count"]
            + summary["leakage_audit"]["packet_text_hit_count"],
            next_todo=summary["next_todo"],
        )
    )


if __name__ == "__main__":
    main()
