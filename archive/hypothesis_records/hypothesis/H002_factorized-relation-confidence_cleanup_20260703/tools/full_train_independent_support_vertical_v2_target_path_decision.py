#!/usr/bin/env python3
"""Decide the next path after v2 target-independence audit."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_AUDIT_DIR = RGA_ROOT / "independent_support_vertical_v2_target_independence_audit_codex_ver"
DEFAULT_READINESS_DIR = RGA_ROOT / "independent_support_vertical_v2_label_readiness_codex_ver"
DEFAULT_FILL_DIR = RGA_ROOT / "independent_support_vertical_v2_label_fill_codex_ver"
DEFAULT_PACKET_DIR = RGA_ROOT / "independent_support_vertical_audit_packet_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_target_path_decision_codex_ver"

BASE_LABELER_FIELDS = [
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
]

INDEPENDENT_COMPLETION_FIELDS = [
    "reviewer_id",
    "review_round",
    "endpoint_identity_independent",
    "pair_evaluability_independent",
    "geometry_validity_independent",
    "relation_reliability_independent",
    "primary_reason_independent",
    "uncertainty_reason_independent",
    "label_notes_independent",
]

FORBIDDEN_LABELER_HEADER_FRAGMENTS = [
    "target",
    "posterior",
    "label_use",
    "confidence",
    "geometry_status",
    "rank",
    "score",
    "p_geom",
    "label_match",
    "proposed",
    "queue",
    "prediction_id",
    "relation_validity_label",
    "independent_relation_label",
    "v2",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--readiness-dir", type=Path, default=DEFAULT_READINESS_DIR)
    parser.add_argument("--fill-dir", type=Path, default=DEFAULT_FILL_DIR)
    parser.add_argument("--packet-dir", type=Path, default=DEFAULT_PACKET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), [dict(row) for row in reader]


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


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def header_hits(fieldnames: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for field in fieldnames:
        lower = field.lower()
        for fragment in FORBIDDEN_LABELER_HEADER_FRAGMENTS:
            if fragment in lower:
                hits.append({"field": field, "forbidden_fragment": fragment})
    return hits


def make_collection_sheet(readiness_rows: list[dict[str, str]]) -> tuple[list[str], list[dict[str, str]]]:
    fieldnames = BASE_LABELER_FIELDS + INDEPENDENT_COMPLETION_FIELDS
    rows: list[dict[str, str]] = []
    for row in readiness_rows:
        output = {key: row.get(key, "") for key in BASE_LABELER_FIELDS}
        output["audit_scope"] = "selected_support_vertical_independent_label_collection_v1"
        for key in INDEPENDENT_COMPLETION_FIELDS:
            output[key] = ""
        rows.append(output)
    return fieldnames, rows


def make_internal_manifest(
    collection_rows: list[dict[str, str]],
    internal_rows: list[dict[str, Any]],
    relation_slice_rows: list[dict[str, Any]],
    completed_v2_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    internal_by_id = {str(row["blind_review_id"]): row for row in internal_rows}
    relation_slice_ids = {str(row["blind_review_id"]) for row in relation_slice_rows}
    v2_by_id = {str(row["blind_review_id"]): row for row in completed_v2_rows}
    manifest: list[dict[str, Any]] = []
    for row in collection_rows:
        blind_id = str(row["blind_review_id"])
        internal = internal_by_id.get(blind_id, {})
        v2 = v2_by_id.get(blind_id, {})
        manifest.append(
            {
                "schema_version": "h002_support_vertical_independent_collection_internal_manifest_v1",
                "blind_review_id": blind_id,
                "labeler_visible": False,
                "post_label_join_only": True,
                "in_relation_reliability_rank_band_construction_slice": blind_id in relation_slice_ids,
                "predicate_family": row.get("predicate_family"),
                "predicate_label": row.get("predicate_label"),
                "scan_id": row.get("scan_id"),
                "hidden_strata": {
                    "queue_kind_hidden": internal.get("queue_kind_hidden"),
                    "rank_band_hidden": internal.get("rank_band_hidden"),
                    "proposed_audit_role_hidden": internal.get("proposed_audit_role_hidden"),
                    "label_match_status_hidden": internal.get("label_match_status_hidden"),
                    "geometry_status_hidden": internal.get("geometry_status_hidden"),
                    "relation_validity_label_hidden": internal.get("relation_validity_label_hidden"),
                    "label_use_hidden": internal.get("label_use_hidden"),
                    "posterior_target_y_hidden": internal.get("posterior_target_y_hidden"),
                },
                "v2_audit_axes_post_label_reference": {
                    "endpoint_validity_v2": v2.get("endpoint_validity_v2"),
                    "pair_visibility_v2": v2.get("pair_visibility_v2"),
                    "relation_geometry_answer_v2": v2.get("relation_geometry_answer_v2"),
                    "geometry_evidence_strength_v2": v2.get("geometry_evidence_strength_v2"),
                    "relation_informativeness_v2": v2.get("relation_informativeness_v2"),
                    "ontology_fit_v2": v2.get("ontology_fit_v2"),
                    "uncertainty_reason_v2": v2.get("uncertainty_reason_v2"),
                },
            }
        )
    return manifest


def collection_schema() -> dict[str, Any]:
    return {
        "schema_version": "h002_support_vertical_independent_label_collection_schema_v1",
        "purpose": "independent human/external review for relation reliability; not Codex target derivation",
        "boundary": {
            "split": "train_only",
            "direct_prior_labels_visible": False,
            "semantic_score_or_rank_visible": False,
            "p_geom_valid_visible": False,
            "geometry_status_visible": False,
            "v2_codex_axes_visible": False,
            "multi_view_as_model_input": False,
        },
        "required_completion_fields": [
            "reviewer_id",
            "review_round",
            "endpoint_identity_independent",
            "pair_evaluability_independent",
            "geometry_validity_independent",
            "relation_reliability_independent",
            "primary_reason_independent",
            "uncertainty_reason_independent",
        ],
        "optional_completion_fields": ["label_notes_independent"],
        "allowed_review_values": {
            "endpoint_identity_independent": [
                "both_valid",
                "subject_invalid",
                "object_invalid",
                "pair_invalid",
                "uncertain",
            ],
            "pair_evaluability_independent": [
                "evaluable",
                "partially_evaluable",
                "not_evaluable",
                "uncertain",
            ],
            "geometry_validity_independent": [
                "supports_predicate",
                "contradicts_predicate",
                "ambiguous",
                "not_evaluable",
            ],
            "relation_reliability_independent": [
                "reliable",
                "unreliable",
                "uncertain",
            ],
            "primary_reason_independent": [
                "physically_supported_informative",
                "geometry_contradiction",
                "dense_or_trivial_relation",
                "endpoint_identity_issue",
                "ontology_mismatch",
                "better_alternative_predicate",
                "visibility_or_evidence_gap",
                "annotation_sparsity_candidate",
                "other",
            ],
            "uncertainty_reason_independent": [
                "none",
                "endpoint_identity",
                "visibility_or_occlusion",
                "weak_geometry",
                "dense_relation",
                "ontology_ambiguity",
                "needs_multiview_or_mesh",
                "other",
            ],
        },
        "post_label_targets": {
            "geometry_validity_human_v1": {
                "positive": {"geometry_validity_independent": ["supports_predicate"]},
                "negative": {"geometry_validity_independent": ["contradicts_predicate"]},
                "exclude": {"geometry_validity_independent": ["ambiguous", "not_evaluable"]},
            },
            "relation_reliability_human_v1": {
                "positive": {"relation_reliability_independent": ["reliable"]},
                "negative": {"relation_reliability_independent": ["unreliable"]},
                "exclude": {"relation_reliability_independent": ["uncertain"]},
            },
        },
    }


def option_matrix(audit_summary: dict[str, Any]) -> list[dict[str, Any]]:
    relation_decision = audit_summary["target_decisions"]["relation_reliability_target_v2"]
    construction = relation_decision.get("recommended_construction_slice")
    return [
        {
            "option": "run_posterior_on_current_v2_target",
            "verdict": "reject",
            "reason": "no strict relation-reliability slice; harmful prior-label carryover remains",
            "evidence": relation_decision["status"],
        },
        {
            "option": "use_rank_band_balanced_v2_for_method_evidence",
            "verdict": "reject_for_method_evidence",
            "reason": "construction risk is reduced but harmful prior carryover remains",
            "evidence": {
                "slice": construction["slice_name"] if construction else "none",
                "rows": construction["rows"] if construction else 0,
                "harmful_prior_risk_count": construction["harmful_prior_risk_count"] if construction else None,
            },
        },
        {
            "option": "revise_rule_based_codex_target_again",
            "verdict": "defer",
            "reason": "another Codex/witness-derived target is likely to inherit the same prior-label carryover unless new independent labels are added",
            "evidence": "v1 and v2 both failed strict target-independence gates",
        },
        {
            "option": "collect_stronger_independent_labels",
            "verdict": "select",
            "reason": "the blocker is target independence, not combiner capacity; an independently filled relation-reliability target is the cleanest next gate",
            "evidence": "strict slice absent; construction-only slice diagnostic only",
        },
        {
            "option": "add_multi_view_as_model_input_now",
            "verdict": "defer",
            "reason": "multi-view should first be audit evidence for independent labels; adding it as input before a clean target would confound target shortcut with extra features",
            "evidence": "current target, not evidence axis, is the blocker",
        },
    ]


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 V2 Target Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Decision",
        "",
        summary["decision"],
        "",
        "## Option Matrix",
        "",
        "| Option | Verdict | Reason |",
        "| --- | --- | --- |",
    ]
    for item in summary["option_matrix"]:
        lines.append(f"| `{item['option']}` | `{item['verdict']}` | {item['reason']} |")
    lines.extend(
        [
            "",
            "## Collection Packet",
            "",
            "| Item | Count |",
            "| --- | ---: |",
            f"| labeler-visible rows | {summary['counts']['collection_rows']} |",
            f"| support_contact rows | {summary['counts']['support_contact_rows']} |",
            f"| relative_vertical rows | {summary['counts']['relative_vertical_rows']} |",
            f"| construction-slice rows included | {summary['counts']['relation_construction_slice_rows']} |",
            f"| labeler header leakage hits | {summary['counts']['labeler_header_leakage_hits']} |",
            "",
            "Labeler-visible sheet:",
            "",
            "```text",
            summary["output_paths"]["independent_collection_sheet"],
            "```",
            "",
            "Internal post-label manifest:",
            "",
            "```text",
            summary["output_paths"]["internal_manifest_post_label_only"],
            "```",
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    audit_dir = as_abs(args.audit_dir)
    readiness_dir = as_abs(args.readiness_dir)
    fill_dir = as_abs(args.fill_dir)
    packet_dir = as_abs(args.packet_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now(timezone.utc).isoformat()
    audit_summary = read_json(audit_dir / "summary.json")
    _, readiness_rows = read_tsv(readiness_dir / "support_vertical_v2_label_fill_sheet.tsv")
    _, completed_v2_rows = read_tsv(fill_dir / "completed_support_vertical_v2_label_fill_sheet_codex_ver.tsv")
    internal_rows = read_jsonl(packet_dir / "internal_reference_post_label_only.jsonl")
    relation_slice_path = audit_dir / "target_slices/relation_reliability_target_v2/rank_band_balanced_v2.jsonl"
    relation_slice_rows = read_jsonl(relation_slice_path)

    fieldnames, collection_rows = make_collection_sheet(readiness_rows)
    hits = header_hits(fieldnames)
    manifest = make_internal_manifest(collection_rows, internal_rows, relation_slice_rows, completed_v2_rows)
    schema = collection_schema()
    options = option_matrix(audit_summary)
    family_counts = Counter(row["predicate_family"] for row in collection_rows)
    relation_slice_ids = {str(row["blind_review_id"]) for row in relation_slice_rows}

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "option_matrix": output_dir / "option_matrix.json",
        "collection_schema": output_dir / "independent_collection_schema.json",
        "independent_collection_sheet": output_dir / "independent_collection_sheet.tsv",
        "internal_manifest_post_label_only": output_dir / "internal_manifest_post_label_only.jsonl",
        "labeler_header_leakage_hits": output_dir / "labeler_header_leakage_hits.jsonl",
    }

    if audit_summary.get("status") != "full_train_independent_support_vertical_v2_target_independence_audit_strict_blocked_construction_slice_available":
        status = "full_train_independent_support_vertical_v2_target_path_decision_needs_audit_review"
        decision = "Audit status is unexpected; review v2 target-independence output before choosing a path."
        next_todo = "review_full_train_independent_support_vertical_v2_target_independence_audit"
    elif hits:
        status = "full_train_independent_support_vertical_v2_target_path_decision_sheet_has_leakage"
        decision = "Independent collection sheet has forbidden labeler-visible fields; fix before label collection."
        next_todo = "fix_full_train_independent_support_vertical_v2_independent_collection_sheet"
    else:
        status = "full_train_independent_support_vertical_v2_target_path_decision_collect_independent_labels"
        decision = (
            "Select stronger independent label collection over another rule-based target revision. "
            "The current construction-only slice is diagnostic only, and posterior smoke remains blocked "
            "until an independent relation-reliability target passes strict target-independence audit."
        )
        next_todo = "full_train_independent_support_vertical_v2_independent_label_fill_or_human_review"

    summary = {
        "schema_version": "h002_support_vertical_v2_target_path_decision_summary_v1",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "audit_summary": rel_path(audit_dir / "summary.json"),
            "readiness_sheet": rel_path(readiness_dir / "support_vertical_v2_label_fill_sheet.tsv"),
            "completed_v2_sheet": rel_path(fill_dir / "completed_support_vertical_v2_label_fill_sheet_codex_ver.tsv"),
            "internal_reference_post_label_only": rel_path(packet_dir / "internal_reference_post_label_only.jsonl"),
            "relation_construction_slice": rel_path(relation_slice_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "construction_slice_method_evidence_allowed": False,
            "labeler_visible_hidden_metadata": False,
            "labeler_visible_v2_codex_axes": False,
            "labeler_visible_semantic_score_or_p_geom": False,
            "multi_view_as_model_input": False,
        },
        "audit_status": audit_summary.get("status"),
        "option_matrix": options,
        "counts": {
            "collection_rows": len(collection_rows),
            "support_contact_rows": family_counts["support_contact"],
            "relative_vertical_rows": family_counts["relative_vertical"],
            "relation_construction_slice_rows": sum(
                1 for row in collection_rows if str(row["blind_review_id"]) in relation_slice_ids
            ),
            "labeler_header_leakage_hits": len(hits),
        },
        "decision": decision,
        "next_todo": next_todo,
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["option_matrix"], {"schema_version": "h002_support_vertical_v2_option_matrix_v1", "options": options})
    write_json(output_paths["collection_schema"], schema)
    write_tsv(output_paths["independent_collection_sheet"], fieldnames, collection_rows)
    write_jsonl(output_paths["internal_manifest_post_label_only"], manifest)
    write_jsonl(output_paths["labeler_header_leakage_hits"], hits)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    print(
        f"status={summary['status']} collection_rows={counts['collection_rows']} "
        f"support={counts['support_contact_rows']} vertical={counts['relative_vertical_rows']} "
        f"construction_rows={counts['relation_construction_slice_rows']} "
        f"leakage={counts['labeler_header_leakage_hits']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"test_used={summary['boundary']['test_usage']} next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
