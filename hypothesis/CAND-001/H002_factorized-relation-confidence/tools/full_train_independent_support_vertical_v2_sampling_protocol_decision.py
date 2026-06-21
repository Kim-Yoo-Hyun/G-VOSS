#!/usr/bin/env python3
"""Decide and materialize the next H002 sampling protocol after user-confirmed target audit failure."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_USER_CONFIRMED_AUDIT = RGA_ROOT / "independent_support_vertical_v2_user_confirmed_review_target_independence_audit_rank_band70/summary.json"
DEFAULT_EXTERNAL_FULL127_AUDIT = RGA_ROOT / "independent_support_vertical_v2_external_review_target_independence_audit_codex_proxy_user_requested/summary.json"
DEFAULT_TRUE_USER_PATH = RGA_ROOT / "independent_support_vertical_v2_true_user_review_path/summary.json"
DEFAULT_CANDIDATE_POOL = RGA_ROOT / "controlled_label_mining/candidate_pool.jsonl"
DEFAULT_ASSET_REQUESTS = RGA_ROOT / "independent_label_protocol/asset_request_manifest.jsonl"
DEFAULT_PACKET_MANIFEST = RGA_ROOT / "independent_asset_packets/packet_manifest.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_sampling_protocol_decision"

VISIBLE_FIELDS = [
    "blind_review_id",
    "review_scope",
    "scan_id",
    "scene_context_id",
    "subject_id",
    "subject_label",
    "predicate_label",
    "predicate_family",
    "object_id",
    "object_label",
    "family_question",
    "evidence_packet_status",
    "multiview_packet",
    "pointcloud_or_mesh_packet",
    "contact_or_context_sheet",
    "external_reviewer_id",
    "external_review_round",
    "endpoint_identity_external",
    "visual_pair_evaluability_external",
    "mesh_pair_evaluability_external",
    "visual_geometry_answer_external",
    "mesh_geometry_answer_external",
    "relation_informativeness_external",
    "final_relation_reliability_external",
    "uncertainty_reason_external",
    "external_label_notes",
]

REVIEW_VALUES = {
    "endpoint_identity_external": ["both_valid", "subject_wrong", "object_wrong", "both_wrong", "unclear"],
    "visual_pair_evaluability_external": ["evaluable", "occluded_or_unclear", "missing_views"],
    "mesh_pair_evaluability_external": ["evaluable", "missing_mesh", "unclear"],
    "visual_geometry_answer_external": ["supports_predicate", "contradicts_predicate", "uncertain", "not_applicable"],
    "mesh_geometry_answer_external": ["supports_predicate", "contradicts_predicate", "uncertain", "not_applicable"],
    "relation_informativeness_external": ["informative", "trivial_dense_or_room_structure", "ontology_mismatch", "uncertain"],
    "final_relation_reliability_external": ["reliable", "unreliable", "uncertain"],
    "uncertainty_reason_external": [
        "none",
        "visual_mesh_disagree",
        "identity_uncertain",
        "occlusion_or_missing_view",
        "ambiguous_relation",
        "trivial_dense_relation",
        "ontology_mismatch",
        "insufficient_evidence",
    ],
}

FAMILY_QUESTIONS = {
    "support_contact": "Does the subject physically contact or support/attach to the object in the packet evidence?",
    "relative_vertical": "Is the subject clearly higher/lower than the object in the packet evidence?",
}

FORBIDDEN_HEADER_SUBSTRINGS = [
    "score",
    "rank",
    "p_geom",
    "geometry_status",
    "target_y",
    "label_use",
    "relation_validity_label",
    "posterior",
    "v2",
    "witness",
    "positive_cues",
    "negative_cues",
    "proxy",
    "human",
    "codex",
    "queue",
    "role",
    "match_status",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-confirmed-audit", type=Path, default=DEFAULT_USER_CONFIRMED_AUDIT)
    parser.add_argument("--external-full127-audit", type=Path, default=DEFAULT_EXTERNAL_FULL127_AUDIT)
    parser.add_argument("--true-user-path-summary", type=Path, default=DEFAULT_TRUE_USER_PATH)
    parser.add_argument("--candidate-pool", type=Path, default=DEFAULT_CANDIDATE_POOL)
    parser.add_argument("--asset-requests", type=Path, default=DEFAULT_ASSET_REQUESTS)
    parser.add_argument("--packet-manifest", type=Path, default=DEFAULT_PACKET_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--priority-size", type=int, default=160)
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


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def identity_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    return (
        str(row.get("prediction_id") or ""),
        str(row.get("scan_id") or ""),
        str(row.get("subgraph_id") or row.get("scene_context_id") or ""),
        str(row.get("subject_id") or ""),
        str(row.get("object_id") or ""),
        str(row.get("predicate_label") or ""),
    )


def header_leakage_hits() -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for field in VISIBLE_FIELDS:
        lowered = field.lower()
        for token in FORBIDDEN_HEADER_SUBSTRINGS:
            if token in lowered:
                hits.append({"field": field, "forbidden_substring": token})
    return hits


def visible_row(row: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    family = str(row["predicate_family"])
    return {
        "blind_review_id": packet["blind_review_id"],
        "review_scope": "selected_support_vertical_revised_sampling_v1",
        "scan_id": row["scan_id"],
        "scene_context_id": row["subgraph_id"],
        "subject_id": row["subject_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "predicate_family": family,
        "object_id": row["object_id"],
        "object_label": row["object_label"],
        "family_question": FAMILY_QUESTIONS[family],
        "evidence_packet_status": packet.get("packet_status") or "missing_packet",
        "multiview_packet": packet.get("multiview_packet", ""),
        "pointcloud_or_mesh_packet": packet.get("pointcloud_or_mesh_packet", ""),
        "contact_or_context_sheet": packet.get("contact_or_context_sheet", ""),
        "external_reviewer_id": "",
        "external_review_round": "",
        "endpoint_identity_external": "",
        "visual_pair_evaluability_external": "",
        "mesh_pair_evaluability_external": "",
        "visual_geometry_answer_external": "",
        "mesh_geometry_answer_external": "",
        "relation_informativeness_external": "",
        "final_relation_reliability_external": "",
        "uncertainty_reason_external": "",
        "external_label_notes": "",
    }


def manifest_row(row: dict[str, Any], packet: dict[str, Any], batch_name: str) -> dict[str, Any]:
    return {
        "schema_version": "h002_support_vertical_v2_revised_sampling_manifest_v1",
        "batch_name": batch_name,
        "blind_review_id": packet["blind_review_id"],
        "prediction_id": row["prediction_id"],
        "scan_id": row["scan_id"],
        "subgraph_id": row["subgraph_id"],
        "subject_id": row["subject_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "object_id": row["object_id"],
        "object_label": row["object_label"],
        "packet_paths": {
            "multiview_packet": packet.get("multiview_packet", ""),
            "pointcloud_or_mesh_packet": packet.get("pointcloud_or_mesh_packet", ""),
            "contact_or_context_sheet": packet.get("contact_or_context_sheet", ""),
        },
        "hidden_sampling_axes_post_label_only": {
            "queue_kind_hidden": row.get("queue_kind"),
            "geometry_status_hidden": row.get("geometry_status"),
            "proposed_audit_role_hidden": row.get("proposed_audit_role"),
            "label_match_status_hidden": row.get("label_match_status"),
            "rank_band_hidden": row.get("rank_band"),
            "predicate_family_hidden": row.get("predicate_family"),
            "predicate_label_hidden": row.get("predicate_label"),
            "candidate_axis_hidden": row.get("candidate_axis"),
            "semantic_rank_hidden": row.get("semantic_rank"),
            "semantic_score_norm_hidden": row.get("semantic_score_norm"),
            "p_geom_valid_hidden": row.get("p_geom_valid"),
        },
        "forbidden_as_labeler_visible": [
            "source score/rank",
            "p_geom_valid",
            "geometry_status",
            "queue kind",
            "proposed audit role",
            "label match status",
            "numeric witness values",
            "previous proxy labels",
            "posterior target fields",
        ],
    }


def counts(rows: list[dict[str, Any]], keys: list[str]) -> dict[str, dict[str, int]]:
    return {key: dict(sorted(Counter(str(row.get(key)) for row in rows).items())) for key in keys}


def select_priority_rows(rows: list[dict[str, Any]], priority_size: int) -> list[dict[str, Any]]:
    """Select all HL rows first, then round-robin LH rows across hidden strata."""
    rows = sorted(rows, key=lambda item: (str(item["scan_id"]), str(item["subgraph_id"]), str(item["prediction_id"])))
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    hl_rows = [row for row in rows if row.get("queue_kind") == "HL"]
    for row in hl_rows:
        if len(selected) >= priority_size:
            break
        selected.append(row)
        selected_ids.add(str(row["prediction_id"]))
    if len(selected) >= priority_size:
        return selected
    lh_groups: dict[tuple[str, str, str], deque[dict[str, Any]]] = defaultdict(deque)
    for row in rows:
        if str(row["prediction_id"]) in selected_ids or row.get("queue_kind") != "LH":
            continue
        key = (
            str(row.get("proposed_audit_role")),
            str(row.get("predicate_family")),
            str(row.get("rank_band")),
        )
        lh_groups[key].append(row)
    group_keys = sorted(lh_groups)
    while len(selected) < priority_size and group_keys:
        next_keys = []
        for key in group_keys:
            queue = lh_groups[key]
            if queue and len(selected) < priority_size:
                row = queue.popleft()
                selected.append(row)
                selected_ids.add(str(row["prediction_id"]))
            if queue:
                next_keys.append(key)
        group_keys = next_keys
    return selected


def build_protocol_rows(
    candidate_rows: list[dict[str, Any]],
    asset_requests: list[dict[str, Any]],
    packet_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    request_by_prediction = {str(row["prediction_id"]): row for row in asset_requests}
    packet_by_blind_id = {str(row["blind_review_id"]): row for row in packet_rows}
    ready: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for row in candidate_rows:
        if row.get("predicate_family") not in {"support_contact", "relative_vertical"}:
            continue
        req = request_by_prediction.get(str(row.get("prediction_id")))
        if not req:
            missing.append({"prediction_id": row.get("prediction_id"), "error_type": "missing_asset_request"})
            continue
        packet = packet_by_blind_id.get(str(req.get("blind_review_id")))
        if not packet:
            missing.append({"prediction_id": row.get("prediction_id"), "blind_review_id": req.get("blind_review_id"), "error_type": "missing_packet"})
            continue
        if packet.get("packet_status") not in {"ready", "ready_with_packet_caveat"}:
            missing.append({"prediction_id": row.get("prediction_id"), "blind_review_id": req.get("blind_review_id"), "error_type": "packet_not_label_ready", "packet_status": packet.get("packet_status")})
            continue
        ready.append({**row, "_packet": packet})
    return ready, missing


def audit_brief(summary: dict[str, Any], relation_target_name: str) -> dict[str, Any]:
    relation = summary.get("target_decisions", {}).get(relation_target_name, {})
    original = relation.get("original", {})
    return {
        "status": summary.get("status"),
        "decision": summary.get("decision"),
        "strict_ready_targets": summary.get("strict_ready_targets", []),
        "construction_only_targets": summary.get("construction_only_targets", []),
        "blocked_targets": summary.get("blocked_targets", []),
        "relation_rows": original.get("rows", summary.get("input_counts", {}).get(relation_target_name, {}).get("rows", 0)),
        "relation_pos": original.get("positive", summary.get("input_counts", {}).get(relation_target_name, {}).get("positive", 0)),
        "relation_neg": original.get("negative", summary.get("input_counts", {}).get(relation_target_name, {}).get("negative", 0)),
        "relation_strict_slice": (relation.get("recommended_strict_slice") or {}).get("slice_name", "none"),
        "relation_construction_slice": (relation.get("recommended_construction_slice") or {}).get("slice_name", "none"),
    }


def write_schema(path: Path) -> None:
    schema = {
        "schema_version": "h002_support_vertical_v2_revised_sampling_review_schema_v1",
        "visible_fields": VISIBLE_FIELDS,
        "review_values": REVIEW_VALUES,
        "hidden_sampling_axes_not_labeler_visible": [
            "queue_kind",
            "geometry_status",
            "proposed_audit_role",
            "label_match_status",
            "rank_band",
            "semantic_rank",
            "semantic_score_norm",
            "p_geom_valid",
        ],
        "target_derivation_note": "Targets are derived only after label lock. Hidden sampling axes are audit-only and must not be posterior inputs.",
    }
    write_json(path, schema)


def write_instructions(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# H002 Revised Sampling Review Instructions",
                "",
                "## Goal",
                "",
                "Fill the sheet using only the packet evidence. This revised batch was selected to reduce hidden sampling-axis carryover after the 70-row user-confirmed audit failed target-independence checks.",
                "",
                "## Use First",
                "",
                "Start with `revised_sampling_sheet_priority160.tsv`. Use `revised_sampling_sheet_all_label_ready.tsv` only if a larger pass is needed.",
                "",
                "## Do Not Use",
                "",
                "- source score or source rank",
                "- `p_geom_valid`",
                "- deterministic geometry status",
                "- queue kind",
                "- proposed audit role",
                "- label-match status",
                "- previous proxy labels",
                "- posterior target fields",
                "",
                "## Labeling Rule",
                "",
                "1. Confirm endpoint identity.",
                "2. Judge visual evidence and mesh evidence separately.",
                "3. Mark geometry support, contradiction, or uncertainty.",
                "4. Mark relation informativeness or ontology/triviality issues.",
                "5. Set final relation reliability.",
                "",
                "Multi-view and mesh evidence are audit evidence only. They are not deployable posterior inputs in the current H002 stage.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    option_rows = summary["option_matrix"]
    lines = [
        "# H002 Sampling Protocol Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "Decision:",
        "",
        summary["decision"],
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage protocol decision.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- H001 artifacts are not used or modified.",
        "- Hidden sampling axes are post-label-only audit metadata and are not labeler-visible.",
        "",
        "## Option Matrix",
        "",
        "| Option | Verdict | Reason |",
        "| --- | --- | --- |",
    ]
    for row in option_rows:
        lines.append(f"| `{row['option']}` | `{row['verdict']}` | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Evidence",
            "",
            "| Artifact | Rows | Pos | Neg | Strict | Construction |",
            "| --- | ---: | ---: | ---: | --- | --- |",
            f"| user-confirmed rank-band 70 | {summary['evidence']['user_confirmed_rank70']['relation_rows']} | {summary['evidence']['user_confirmed_rank70']['relation_pos']} | {summary['evidence']['user_confirmed_rank70']['relation_neg']} | `{summary['evidence']['user_confirmed_rank70']['relation_strict_slice']}` | `{summary['evidence']['user_confirmed_rank70']['relation_construction_slice']}` |",
            f"| previous full-127 external proxy | {summary['evidence']['previous_full127_external_proxy']['relation_rows']} | {summary['evidence']['previous_full127_external_proxy']['relation_pos']} | {summary['evidence']['previous_full127_external_proxy']['relation_neg']} | `{summary['evidence']['previous_full127_external_proxy']['relation_strict_slice']}` | `{summary['evidence']['previous_full127_external_proxy']['relation_construction_slice']}` |",
            "",
            "## Revised Sampling Artifacts",
            "",
            "| Item | Count |",
            "| --- | ---: |",
            f"| support/vertical candidate pool rows | {summary['revised_sampling']['all_candidate_rows']} |",
            f"| label-ready joined rows | {summary['revised_sampling']['joined_label_ready_rows']} |",
            f"| priority rows | {summary['revised_sampling']['priority_rows']} |",
            f"| missing packet/request rows | {summary['revised_sampling']['missing_or_unready_rows']} |",
            f"| header leakage hits | {summary['revised_sampling']['header_leakage_hits']} |",
            "",
            "Generated sheets:",
            "",
            "```text",
            summary["output_paths"]["priority_sheet"],
            summary["output_paths"]["all_sheet"],
            summary["output_paths"]["priority_manifest"],
            summary["output_paths"]["all_manifest"],
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
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    user_confirmed_audit = read_json(args.user_confirmed_audit)
    external_full127_audit = read_json(args.external_full127_audit)
    true_user_path = read_json(args.true_user_path_summary)
    candidate_pool = read_jsonl(args.candidate_pool)
    asset_requests = read_jsonl(args.asset_requests)
    packet_manifest = read_jsonl(args.packet_manifest)

    support_vertical_candidates = [
        row for row in candidate_pool if row.get("predicate_family") in {"support_contact", "relative_vertical"}
    ]
    joined_rows, missing_rows = build_protocol_rows(support_vertical_candidates, asset_requests, packet_manifest)
    joined_rows = sorted(joined_rows, key=lambda item: identity_key(item))
    priority_rows = select_priority_rows(joined_rows, min(args.priority_size, len(joined_rows)))

    def make_sheet(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [visible_row(row, row["_packet"]) for row in rows]

    def make_manifest(rows: list[dict[str, Any]], batch_name: str) -> list[dict[str, Any]]:
        return [manifest_row(row, row["_packet"], batch_name) for row in rows]

    priority_sheet_rows = make_sheet(priority_rows)
    all_sheet_rows = make_sheet(joined_rows)
    priority_manifest = make_manifest(priority_rows, "priority160_revised_sampling")
    all_manifest = make_manifest(joined_rows, "all_label_ready_revised_sampling")
    leakage = header_leakage_hits()

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "option_matrix": output_dir / "option_matrix.json",
        "priority_sheet": output_dir / "revised_sampling_sheet_priority160.tsv",
        "all_sheet": output_dir / "revised_sampling_sheet_all_label_ready.tsv",
        "priority_manifest": output_dir / "revised_sampling_manifest_priority160_post_label_only.jsonl",
        "all_manifest": output_dir / "revised_sampling_manifest_all_label_ready_post_label_only.jsonl",
        "schema": output_dir / "revised_sampling_review_schema.json",
        "instructions": output_dir / "reviewer_instructions.md",
        "missing_or_unready_rows": output_dir / "missing_or_unready_rows.jsonl",
        "header_leakage_hits": output_dir / "header_leakage_hits.jsonl",
        "priority_axis_counts": output_dir / "priority_axis_counts.json",
        "all_axis_counts": output_dir / "all_axis_counts.json",
    }

    user_brief = audit_brief(user_confirmed_audit, "relation_reliability_user_confirmed_review_target")
    full127_brief = audit_brief(external_full127_audit, "relation_reliability_external_target")
    option_matrix = [
        {
            "option": "run_posterior_on_user_confirmed_rank70",
            "verdict": "reject",
            "reason": "No strict or construction-only relation target slice exists.",
        },
        {
            "option": "expand_full127_same_protocol_then_posterior",
            "verdict": "reject_as_direct_posterior_path",
            "reason": "Previous full-127 proxy audit increased size but still produced no strict relation slice.",
        },
        {
            "option": "expand_full127_same_protocol_for_diagnostics",
            "verdict": "diagnostic_only",
            "reason": "It can improve sample size, but it does not directly solve hidden prior carryover.",
        },
        {
            "option": "revise_sampling_protocol_before_next_labels",
            "verdict": "select",
            "reason": "The blocker is target/evidence independence, so the next label surface must balance hidden queue, role, rank, and family axes before posterior smoke.",
        },
    ]
    summary = {
        "schema_version": "h002_support_vertical_v2_sampling_protocol_decision_v1",
        "created_at": created_at,
        "status": "full_train_independent_support_vertical_v2_sampling_protocol_decision_revise_sampling_first",
        "decision": "Revise sampling protocol before expanding labels or running posterior smoke.",
        "boundary": {
            "split": "open3dsg_train_full_only",
            "validation_used": False,
            "test_used": False,
            "posterior_trained": False,
            "h001_modified": False,
            "multi_view_as_posterior_input": False,
        },
        "input_paths": {
            "user_confirmed_audit": rel_path(args.user_confirmed_audit),
            "external_full127_audit": rel_path(args.external_full127_audit),
            "true_user_path_summary": rel_path(args.true_user_path_summary),
            "candidate_pool": rel_path(args.candidate_pool),
            "asset_requests": rel_path(args.asset_requests),
            "packet_manifest": rel_path(args.packet_manifest),
        },
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "evidence": {
            "user_confirmed_rank70": user_brief,
            "previous_full127_external_proxy": full127_brief,
            "true_user_path_counts": true_user_path.get("counts", {}),
        },
        "option_matrix": option_matrix,
        "revised_sampling": {
            "all_candidate_rows": len(support_vertical_candidates),
            "joined_label_ready_rows": len(joined_rows),
            "priority_rows": len(priority_rows),
            "missing_or_unready_rows": len(missing_rows),
            "header_leakage_hits": len(leakage),
            "priority_axis_counts": counts(priority_rows, ["predicate_family", "predicate_label", "queue_kind", "geometry_status", "proposed_audit_role", "label_match_status", "rank_band"]),
            "all_axis_counts": counts(joined_rows, ["predicate_family", "predicate_label", "queue_kind", "geometry_status", "proposed_audit_role", "label_match_status", "rank_band"]),
        },
        "next_todo": "fill_revised_sampling_priority160_sheet_or_user_confirmed_labels",
    }

    write_tsv(output_paths["priority_sheet"], priority_sheet_rows, VISIBLE_FIELDS)
    write_tsv(output_paths["all_sheet"], all_sheet_rows, VISIBLE_FIELDS)
    write_jsonl(output_paths["priority_manifest"], priority_manifest)
    write_jsonl(output_paths["all_manifest"], all_manifest)
    write_jsonl(output_paths["missing_or_unready_rows"], missing_rows)
    write_jsonl(output_paths["header_leakage_hits"], leakage)
    write_json(output_paths["priority_axis_counts"], summary["revised_sampling"]["priority_axis_counts"])
    write_json(output_paths["all_axis_counts"], summary["revised_sampling"]["all_axis_counts"])
    write_json(output_paths["option_matrix"], {"option_matrix": option_matrix})
    write_schema(output_paths["schema"])
    write_instructions(output_paths["instructions"])
    write_report(output_paths["report"], summary)
    write_json(output_paths["summary"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    rs = summary["revised_sampling"]
    print(
        f"status={summary['status']} decision=revise_sampling_first "
        f"all_candidates={rs['all_candidate_rows']} joined={rs['joined_label_ready_rows']} "
        f"priority={rs['priority_rows']} missing={rs['missing_or_unready_rows']} "
        f"header_leakage={rs['header_leakage_hits']} "
        f"validation_used={summary['boundary']['validation_used']} test_used={summary['boundary']['test_used']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
