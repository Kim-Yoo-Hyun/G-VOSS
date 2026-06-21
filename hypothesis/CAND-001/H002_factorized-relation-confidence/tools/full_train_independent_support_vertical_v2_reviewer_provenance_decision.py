#!/usr/bin/env python3
"""Decide the next H002 path after user-submitted review audit remains blocked."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_USER_SHEET = RGA_ROOT / "independent_support_vertical_v2_true_user_review_path/true_user_review_sheet_rank_band70.tsv"
DEFAULT_USER_INGESTION_SUMMARY = RGA_ROOT / "independent_support_vertical_v2_user_submitted_review_ingestion_rank_band70/summary.json"
DEFAULT_USER_AUDIT_SUMMARY = RGA_ROOT / "independent_support_vertical_v2_user_submitted_review_target_independence_audit_rank_band70/summary.json"
DEFAULT_EXTERNAL_PROTOCOL_SUMMARY = RGA_ROOT / "independent_support_vertical_v2_external_review_protocol/summary.json"
DEFAULT_EXTERNAL_SHEET = RGA_ROOT / "independent_support_vertical_v2_external_review_protocol/external_evidence_review_sheet.tsv"
DEFAULT_EXTERNAL_MANIFEST = RGA_ROOT / "independent_support_vertical_v2_external_review_protocol/external_manifest_post_label_only.jsonl"
DEFAULT_EXTERNAL_INSTRUCTIONS = RGA_ROOT / "independent_support_vertical_v2_external_review_protocol/reviewer_instructions.md"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_reviewer_provenance_decision"

COMPLETION_FIELDS = [
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

CODEx_REVIEWER_IDS = {
    "codex_packet_only_diagnostic",
    "(codex_proxy_user_review_pending)",
    "codex_proxy_user_requested",
    "codex_independent_ver",
    "codex_ver",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-sheet", type=Path, default=DEFAULT_USER_SHEET)
    parser.add_argument("--user-ingestion-summary", type=Path, default=DEFAULT_USER_INGESTION_SUMMARY)
    parser.add_argument("--user-audit-summary", type=Path, default=DEFAULT_USER_AUDIT_SUMMARY)
    parser.add_argument("--external-protocol-summary", type=Path, default=DEFAULT_EXTERNAL_PROTOCOL_SUMMARY)
    parser.add_argument("--external-sheet", type=Path, default=DEFAULT_EXTERNAL_SHEET)
    parser.add_argument("--external-manifest", type=Path, default=DEFAULT_EXTERNAL_MANIFEST)
    parser.add_argument("--external-instructions", type=Path, default=DEFAULT_EXTERNAL_INSTRUCTIONS)
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


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def copy_artifact(src: Path, dst: Path) -> None:
    src = as_abs(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def completed_field_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if str(row.get(field) or "").strip())
        for field in COMPLETION_FIELDS
    }


def reviewer_id_analysis(rows: list[dict[str, str]]) -> dict[str, Any]:
    ids = Counter(str(row.get("external_reviewer_id") or "").strip() for row in rows)
    rounds = Counter(str(row.get("external_review_round") or "").strip() for row in rows)
    codex_like = {key: value for key, value in ids.items() if key in CODEx_REVIEWER_IDS or key.startswith("codex")}
    nonempty_ids = {key: value for key, value in ids.items() if key}
    return {
        "reviewer_id_counts": dict(sorted(ids.items())),
        "review_round_counts": dict(sorted(rounds.items())),
        "codex_like_reviewer_id_counts": dict(sorted(codex_like.items())),
        "nonempty_reviewer_id_count": sum(nonempty_ids.values()),
        "codex_like_row_count": sum(codex_like.values()),
        "all_rows_have_codex_like_reviewer_id": bool(rows) and sum(codex_like.values()) == len(rows),
        "artifact_level_independence_confirmed": bool(rows) and sum(codex_like.values()) == 0 and "" not in ids,
    }


def external_protocol_counts(summary: dict[str, Any]) -> dict[str, Any]:
    counts = summary.get("counts", {})
    return {
        "review_rows": counts.get("review_rows", 0),
        "ready_packets": counts.get("ready_packets", 0),
        "ready_with_packet_caveat": counts.get("by_packet_status", {}).get("ready_with_packet_caveat", 0),
        "packet_path_errors": counts.get("packet_path_errors", 0),
        "header_leakage_hits": counts.get("header_leakage_hits", 0),
        "by_family": counts.get("by_family", {}),
    }


def target_audit_brief(summary: dict[str, Any]) -> dict[str, Any]:
    relation = summary.get("target_decisions", {}).get("relation_reliability_user_submitted_review_target", {})
    geom = summary.get("target_decisions", {}).get("geometry_validity_user_submitted_review_target", {})
    relation_original = relation.get("original", {})
    geom_original = geom.get("original", {})
    return {
        "audit_status": summary.get("status"),
        "strict_ready_targets": summary.get("strict_ready_targets", []),
        "construction_only_targets": summary.get("construction_only_targets", []),
        "blocked_targets": summary.get("blocked_targets", []),
        "relation_target": {
            "status": relation.get("status"),
            "rows": relation_original.get("rows", 0),
            "positive": relation_original.get("positive", 0),
            "negative": relation_original.get("negative", 0),
            "strict_slice": (relation.get("recommended_strict_slice") or {}).get("slice_name", "none"),
            "construction_slice": (relation.get("recommended_construction_slice") or {}).get("slice_name", "none"),
        },
        "geometry_target": {
            "status": geom.get("status"),
            "rows": geom_original.get("rows", 0),
            "positive": geom_original.get("positive", 0),
            "negative": geom_original.get("negative", 0),
            "strict_slice": (geom.get("recommended_strict_slice") or {}).get("slice_name", "none"),
            "construction_slice": (geom.get("recommended_construction_slice") or {}).get("slice_name", "none"),
        },
    }


def write_confirmation_request(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# H002 Reviewer Provenance Confirmation Request",
                "",
                "## Purpose",
                "",
                "This request records what must be confirmed before the submitted sheet can be described as non-Codex user/human annotation.",
                "",
                "## Current Artifact-Level Status",
                "",
                f"- Submitted rows: {summary['user_sheet']['rows']}",
                f"- Reviewer ids: `{summary['reviewer_id_analysis']['reviewer_id_counts']}`",
                f"- Artifact-level independence confirmed: `{summary['reviewer_id_analysis']['artifact_level_independence_confirmed']}`",
                "",
                "## Required Confirmation",
                "",
                "A reviewer must explicitly confirm all of the following before the labels are described as independent user/human labels:",
                "",
                "1. The reviewer personally inspected only the packet evidence for every completed row.",
                "2. The reviewer did not use source score, source rank, `p_geom_valid`, deterministic geometry status, hidden prior labels, previous Codex/proxy labels, or posterior targets.",
                "3. The reviewer id in the sheet should be replaced with a non-Codex reviewer id before any future ingestion.",
                "4. The review round should identify the actual review pass, not `r1_20260619_packet_only` if that string came from a diagnostic fill.",
                "",
                "## Important Boundary",
                "",
                "Even if provenance is later confirmed, the current target-independence audit found no strict or construction-only controlled slice. Provenance confirmation alone does not open posterior smoke.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_label_request(path: Path, summary: dict[str, Any]) -> None:
    protocol = summary["external_protocol"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# H002 External Label Collection Request",
                "",
                "## Decision",
                "",
                "Collect a fresh external evidence review pass with fixed reviewer provenance before any posterior smoke.",
                "",
                "## Recommended Batch",
                "",
                f"- Sheet: `{summary['output_paths']['recommended_external_review_sheet']}`",
                f"- Post-label manifest: `{summary['output_paths']['recommended_external_manifest_post_label_only']}`",
                f"- Instructions: `{summary['input_paths']['external_instructions']}`",
                "",
                "## Batch Counts",
                "",
                f"- Rows: {protocol['review_rows']}",
                f"- Ready packets: {protocol['ready_packets']}",
                f"- Ready-with-caveat packets: {protocol['ready_with_packet_caveat']}",
                f"- Packet path errors: {protocol['packet_path_errors']}",
                f"- Header leakage hits: {protocol['header_leakage_hits']}",
                f"- By family: `{protocol['by_family']}`",
                "",
                "## Reviewer Constraints",
                "",
                "- Fill `external_reviewer_id` with a real non-Codex reviewer id.",
                "- Fill `external_review_round` with a real review-pass id.",
                "- Use only multi-view packet, mesh/point-cloud packet, and contact/context sheet evidence.",
                "- Do not use source score/rank, `p_geom_valid`, hidden metadata, previous proxy labels, or posterior target fields.",
                "- Keep multi-view as audit evidence only; do not treat it as a deployable posterior input yet.",
                "",
                "## Why Full 127 Instead Of Reusing Only Rank-Band 70",
                "",
                "The user-submitted rank-band 70 target improved class balance, but still produced no strict or construction-only controlled slice. The full 127-row protocol is the next better collection surface because it increases sample size while preserving the same labeler-visible leakage controls.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_report(path: Path, summary: dict[str, Any]) -> None:
    audit = summary["target_audit"]
    reviewer = summary["reviewer_id_analysis"]
    protocol = summary["external_protocol"]
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# H002 Reviewer Provenance Decision",
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
        "- Open3DSG train-only hypothesis-stage decision.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- H001 artifacts are not used or modified.",
        "- This step checks label provenance and target-readiness only.",
        "",
        "## Reviewer Provenance",
        "",
        "| Item | Value |",
        "| --- | --- |",
        f"| submitted rows | {summary['user_sheet']['rows']} |",
        f"| reviewer id counts | `{reviewer['reviewer_id_counts']}` |",
        f"| codex-like reviewer rows | {reviewer['codex_like_row_count']} |",
        f"| artifact-level independence confirmed | `{reviewer['artifact_level_independence_confirmed']}` |",
        "",
        "## Target Audit Carryover",
        "",
        "| Target | Rows | Pos | Neg | Status | Strict Slice | Construction Slice |",
        "| --- | ---: | ---: | ---: | --- | --- | --- |",
        f"| `geometry_validity_user_submitted_review_target` | {audit['geometry_target']['rows']} | {audit['geometry_target']['positive']} | {audit['geometry_target']['negative']} | `{audit['geometry_target']['status']}` | `{audit['geometry_target']['strict_slice']}` | `{audit['geometry_target']['construction_slice']}` |",
        f"| `relation_reliability_user_submitted_review_target` | {audit['relation_target']['rows']} | {audit['relation_target']['positive']} | {audit['relation_target']['negative']} | `{audit['relation_target']['status']}` | `{audit['relation_target']['strict_slice']}` | `{audit['relation_target']['construction_slice']}` |",
        "",
        "## External Label Path",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| full external review rows | {protocol['review_rows']} |",
        f"| ready packets | {protocol['ready_packets']} |",
        f"| ready with packet caveat | {protocol['ready_with_packet_caveat']} |",
        f"| packet path errors | {protocol['packet_path_errors']} |",
        f"| header leakage hits | {protocol['header_leakage_hits']} |",
        "",
        "Recommended artifacts:",
        "",
        "```text",
        summary["output_paths"]["recommended_external_review_sheet"],
        summary["output_paths"]["recommended_external_manifest_post_label_only"],
        summary["output_paths"]["provenance_confirmation_request"],
        summary["output_paths"]["external_label_collection_request"],
        "```",
        "",
        "## Interpretation",
        "",
        "- The completed 70-row sheet cannot be confirmed as independent from the artifact alone.",
        "- All submitted rows still use a Codex-like reviewer id.",
        "- The target audit remains blocked even apart from provenance.",
        "- The next defensible path is a fresh full-127 external evidence review pass with fixed reviewer provenance.",
        "- Posterior smoke and combiner upgrade remain blocked.",
        "",
        "## Next TODO",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    user_fields, user_rows = read_tsv(args.user_sheet)
    user_ingestion = read_json(args.user_ingestion_summary)
    user_audit = read_json(args.user_audit_summary)
    external_protocol_summary = read_json(args.external_protocol_summary)

    recommended_sheet = output_dir / "external_evidence_review_sheet_full127_fixed_provenance.tsv"
    recommended_manifest = output_dir / "external_manifest_full127_post_label_only.jsonl"
    copy_artifact(args.external_sheet, recommended_sheet)
    copy_artifact(args.external_manifest, recommended_manifest)

    summary: dict[str, Any] = {
        "schema_version": "h002_support_vertical_v2_reviewer_provenance_decision_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "full_train_independent_support_vertical_v2_reviewer_provenance_decision_collect_external_labels",
        "decision": "Artifact-level reviewer independence is unconfirmed, and target-independence audit remains blocked; collect fresh full-127 external labels with fixed reviewer provenance.",
        "boundary": {
            "split": "open3dsg_train_full_only",
            "validation_used": False,
            "test_used": False,
            "posterior_trained": False,
            "h001_modified": False,
            "multi_view_as_posterior_input": False,
        },
        "input_paths": {
            "user_sheet": rel_path(args.user_sheet),
            "user_ingestion_summary": rel_path(args.user_ingestion_summary),
            "user_audit_summary": rel_path(args.user_audit_summary),
            "external_protocol_summary": rel_path(args.external_protocol_summary),
            "external_sheet": rel_path(args.external_sheet),
            "external_manifest": rel_path(args.external_manifest),
            "external_instructions": rel_path(args.external_instructions),
        },
        "user_sheet": {
            "rows": len(user_rows),
            "columns": len(user_fields),
            "completed_field_counts": completed_field_counts(user_rows),
            "ingestion_status": user_ingestion.get("status"),
        },
        "reviewer_id_analysis": reviewer_id_analysis(user_rows),
        "target_audit": target_audit_brief(user_audit),
        "external_protocol": external_protocol_counts(external_protocol_summary),
        "output_paths": {
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "provenance_confirmation_request": rel_path(output_dir / "provenance_confirmation_request.md"),
            "external_label_collection_request": rel_path(output_dir / "external_label_collection_request.md"),
            "recommended_external_review_sheet": rel_path(recommended_sheet),
            "recommended_external_manifest_post_label_only": rel_path(recommended_manifest),
        },
        "next_todo": "collect_external_full127_labels_with_fixed_reviewer_provenance",
    }

    write_confirmation_request(output_dir / "provenance_confirmation_request.md", summary)
    write_label_request(output_dir / "external_label_collection_request.md", summary)
    write_report(output_dir / "report.md", summary)
    write_json(output_dir / "summary.json", summary)

    print(
        "status={status} user_rows={rows} codex_like_rows={codex_rows} "
        "independence_confirmed={confirmed} relation_strict={strict} relation_construction={construction} "
        "external_rows={external_rows} validation_used={validation_used} test_used={test_used} next={next_todo}".format(
            status=summary["status"],
            rows=summary["user_sheet"]["rows"],
            codex_rows=summary["reviewer_id_analysis"]["codex_like_row_count"],
            confirmed=summary["reviewer_id_analysis"]["artifact_level_independence_confirmed"],
            strict=summary["target_audit"]["relation_target"]["strict_slice"],
            construction=summary["target_audit"]["relation_target"]["construction_slice"],
            external_rows=summary["external_protocol"]["review_rows"],
            validation_used=summary["boundary"]["validation_used"],
            test_used=summary["boundary"]["test_used"],
            next_todo=summary["next_todo"],
        )
    )


if __name__ == "__main__":
    main()
