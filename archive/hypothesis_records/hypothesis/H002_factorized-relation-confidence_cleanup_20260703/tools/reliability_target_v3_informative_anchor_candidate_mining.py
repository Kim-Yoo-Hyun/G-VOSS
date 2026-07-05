#!/usr/bin/env python3
"""Mine the H002 reliability target v3 informative-anchor label sheet."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

PLAN_DIR = RGA_ROOT / "reliability_target_v3_informative_anchor_plan"
SCHEMA_DIR = RGA_ROOT / "reliability_target_v3_positive_anchor_plan"

DEFAULT_PLAN_SUMMARY = PLAN_DIR / "summary.json"
DEFAULT_SEEDS = PLAN_DIR / "seed_candidates_internal.jsonl"
DEFAULT_ASSET_REQUESTS = PLAN_DIR / "asset_request_plan.jsonl"
DEFAULT_SCHEMA = SCHEMA_DIR / "v3_label_schema.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v3_informative_anchor_candidate_mining"

REVIEW_SCOPE = "h002_reliability_v3_informative_anchor_mining"
SCHEMA_VERSION = "h002_reliability_target_v3_informative_anchor_candidate_mining_v1"

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
    "positive_cues",
    "negative_cues",
    "evidence_packet_status",
    "multiview_packet",
    "pointcloud_or_mesh_packet",
    "contact_or_context_sheet",
    "reviewer_id",
    "review_round",
    "endpoint_identity_v3",
    "pair_evaluability_v3",
    "geometry_support_v3",
    "relation_usefulness_v3",
    "relation_reliability_v3",
    "primary_reason_v3",
    "uncertainty_reason_v3",
    "label_notes_v3",
]

COMPLETION_FIELDS = [
    "reviewer_id",
    "review_round",
    "endpoint_identity_v3",
    "pair_evaluability_v3",
    "geometry_support_v3",
    "relation_usefulness_v3",
    "relation_reliability_v3",
    "primary_reason_v3",
    "uncertainty_reason_v3",
    "label_notes_v3",
]

FAMILY_PROMPTS = {
    "support_contact": {
        "question": "Does the subject physically contact, rest on, support, or attach to the object in the evidence?",
        "positive_cues": "visible contact, plausible support or attachment surface, consistent support direction, non-trivial pair",
        "negative_cues": "nearby without contact/support, wrong support direction, trivial room-structure relation, segmentation or identity issue",
    },
    "relative_vertical": {
        "question": "Is the subject clearly higher/lower than the object in the evidence?",
        "positive_cues": "clear vertical ordering, predicate direction matches the evidence, comparable object-level endpoints",
        "negative_cues": "wrong vertical direction, ambiguous height, non-comparable room surface, segmentation or identity issue",
    },
}

FORBIDDEN_VISIBLE_FIELD_TOKENS = [
    "anchor_category",
    "candidate_proxy",
    "proxy",
    "queue_kind",
    "source_queue",
    "rank_band",
    "semantic_rank",
    "semantic_score",
    "p_geom_valid",
    "geometry_status",
    "h001_verification_status",
    "label_match_status",
    "sampling_category",
    "selection_pass",
    "informative_anchor_score",
    "room_surface_score",
    "endpoint_flag_pattern",
    "matched_predicates",
    "reason_codes",
    "hidden",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-summary", type=Path, default=DEFAULT_PLAN_SUMMARY)
    parser.add_argument("--seeds", type=Path, default=DEFAULT_SEEDS)
    parser.add_argument("--asset-requests", type=Path, default=DEFAULT_ASSET_REQUESTS)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def blind_review_id(row: dict[str, Any]) -> str:
    return "ftv3ia_" + stable_hash("h002_reliability_v3_informative_anchor:" + str(row["prediction_id"]))[:12]


def family_prompt(row: dict[str, Any]) -> dict[str, str]:
    return FAMILY_PROMPTS.get(
        str(row.get("predicate_family")),
        {
            "question": "Does the relation hold according to the evidence?",
            "positive_cues": "relation is supported by visual and geometric evidence",
            "negative_cues": "relation is contradicted, trivial, or not evaluable from the evidence",
        },
    )


def evidence_status(row: dict[str, Any]) -> str:
    return "ready" if row.get("packet_ready") is True and row.get("packet_status") == "ready" else "asset_needed"


def visible_row(row: dict[str, Any]) -> dict[str, Any]:
    prompt = family_prompt(row)
    ready = evidence_status(row) == "ready"
    output = {
        "blind_review_id": blind_review_id(row),
        "review_scope": REVIEW_SCOPE,
        "scan_id": row.get("scan_id"),
        "scene_context_id": row.get("scene_context_id") or row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "family_question": prompt["question"],
        "positive_cues": prompt["positive_cues"],
        "negative_cues": prompt["negative_cues"],
        "evidence_packet_status": evidence_status(row),
        "multiview_packet": row.get("multiview_packet", "") if ready else "",
        "pointcloud_or_mesh_packet": row.get("pointcloud_or_mesh_packet", "") if ready else "",
        "contact_or_context_sheet": row.get("contact_or_context_sheet", "") if ready else "",
    }
    for field in COMPLETION_FIELDS:
        output[field] = ""
    return output


def endpoint_pair_note(row: dict[str, Any]) -> str:
    pattern = str(row.get("endpoint_flag_pattern_hidden") or "")
    notes = []
    for part in pattern.split("|"):
        if part.endswith("=1"):
            notes.append(part.replace("=1", ""))
    return ",".join(notes)


def manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_v3_informative_anchor_manifest_v1",
        "batch_name": "reliability_target_v3_informative_anchor_candidate_mining",
        "blind_review_id": blind_review_id(row),
        "asset_request_id": row.get("original_blind_review_id", ""),
        "prediction_id_hidden": row.get("prediction_id"),
        "sampling_category_hidden": row.get("sampling_category_hidden"),
        "recommended_label_role_hidden": row.get("recommended_label_role_hidden"),
        "expected_v3_role_hidden": "informative_anchor_proxy_stratum_not_target",
        "labeler_visible": False,
        "post_label_join_only": True,
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("scene_context_id") or row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "evidence_packet_status": evidence_status(row),
        "packet_paths": {
            "multiview_packet": row.get("multiview_packet", ""),
            "pointcloud_or_mesh_packet": row.get("pointcloud_or_mesh_packet", ""),
            "contact_or_context_sheet": row.get("contact_or_context_sheet", ""),
        },
        "hidden_sampling_axes_post_label_only": {
            "anchor_category_hidden": row.get("anchor_category_hidden"),
            "sampling_category_hidden": row.get("sampling_category_hidden"),
            "sampling_selection_pass_hidden": row.get("sampling_selection_pass_hidden"),
            "informative_anchor_score_hidden": row.get("informative_anchor_score_hidden"),
            "room_surface_score_hidden": row.get("room_surface_score_hidden"),
            "endpoint_flag_pattern_hidden": row.get("endpoint_flag_pattern_hidden"),
            "endpoint_pair_note_hidden": endpoint_pair_note(row),
            "subject_object_family_cell_hidden": row.get("subject_object_family_cell_hidden"),
            "object_family_cell_hidden": row.get("object_family_cell_hidden"),
            "endpoint_family_cell_hidden": row.get("endpoint_family_cell_hidden"),
            "queue_kind_hidden": row.get("queue_kind_hidden"),
            "source_queue_hidden": row.get("source_queue_hidden"),
            "geometry_status_hidden": row.get("geometry_status_hidden"),
            "h001_verification_status_hidden": row.get("h001_verification_status_hidden"),
            "label_match_status_hidden": row.get("label_match_status_hidden"),
            "label_match_family_hidden": row.get("label_match_family_hidden"),
            "label_geometry_bucket_hidden": row.get("label_geometry_bucket_hidden"),
            "rank_band_hidden": row.get("rank_band_hidden"),
            "semantic_rank_hidden": row.get("semantic_rank_hidden"),
            "semantic_score_raw_hidden": row.get("semantic_score_raw_hidden"),
            "semantic_score_norm_hidden": row.get("semantic_score_norm_hidden"),
            "p_geom_valid_hidden": row.get("p_geom_valid_hidden"),
            "machine_hint_hidden": row.get("machine_hint_hidden"),
            "matched_predicates_hidden": row.get("matched_predicates_hidden", []),
            "reason_codes_hidden": row.get("reason_codes_hidden", []),
            "original_blind_review_id_hidden": row.get("original_blind_review_id"),
        },
        "forbidden_as_labeler_visible": [
            "anchor category",
            "sampling category",
            "source queue",
            "semantic score/rank",
            "p_geom_valid",
            "geometry_status",
            "h001 verification status",
            "label_match_status",
            "matched GT/predicate hints",
            "reason codes",
            "endpoint flag pattern",
            "posterior target fields",
        ],
    }


def surface_leakage_hits(fieldnames: list[str]) -> list[dict[str, Any]]:
    hits = []
    for field in fieldnames:
        lowered = field.lower()
        for token in FORBIDDEN_VISIBLE_FIELD_TOKENS:
            if token in lowered:
                hits.append({"field": field, "token": token, "error_type": "forbidden_visible_field"})
    return hits


def packet_path_errors(rows: list[dict[str, Any]], *, require_ready_only: bool) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):
        status = row.get("evidence_packet_status")
        if status == "asset_needed" and not require_ready_only:
            continue
        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = str(row.get(field) or "")
            if not value or not as_abs(Path(value)).exists():
                errors.append(
                    {
                        "row_number": row_number,
                        "blind_review_id": row.get("blind_review_id"),
                        "field": field,
                        "value": value,
                        "error_type": "packet_path_missing",
                    }
                )
    return errors


def category_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    categories = sorted({str(row.get("anchor_category_hidden")) for row in rows})
    output = []
    for category in categories:
        group = [row for row in rows if str(row.get("anchor_category_hidden")) == category]
        families = Counter(str(row.get("predicate_family")) for row in group)
        statuses = Counter(evidence_status(row) for row in group)
        output.append(
            {
                "anchor_category": category,
                "rows": len(group),
                "packet_ready": statuses.get("ready", 0),
                "asset_needed": statuses.get("asset_needed", 0),
                "support_contact": families.get("support_contact", 0),
                "relative_vertical": families.get("relative_vertical", 0),
                "unique_scans": len({str(row.get("scan_id")) for row in group}),
            }
        )
    return output


def validate_plan(plan_summary: dict[str, Any], seeds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("next_todo") != "reliability_target_v3_informative_anchor_candidate_mining":
        errors.append({"error_type": "unexpected_plan_next_todo", "value": plan_summary.get("next_todo")})
    for key in ["validation_used", "test_used", "posterior_allowed"]:
        if plan_summary.get(key) is not False:
            errors.append({"error_type": f"plan_{key}_not_false", "value": plan_summary.get(key)})
    ids = [str(row.get("prediction_id")) for row in seeds]
    for prediction_id, count in Counter(ids).items():
        if count > 1:
            errors.append({"error_type": "duplicate_seed_prediction_id", "prediction_id": prediction_id, "count": count})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 Reliability Target V3 Informative Anchor Candidate Mining",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only candidate mining.",
        "- No validation/test rows are used.",
        "- No labels are filled.",
        "- No posterior is trained.",
        "- Informative-anchor proxy categories are sampling strata only, not target labels.",
        "- Multi-view packets remain audit/label evidence only, not deployable model input.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| selected seed rows | {counts['selected_seed_rows']} |",
        f"| full label sheet rows | {counts['full_label_sheet_rows']} |",
        f"| packet-ready fallback rows | {counts['packet_ready_label_sheet_rows']} |",
        f"| asset-needed rows | {counts['asset_needed_rows']} |",
        f"| support_contact | {counts['by_family'].get('support_contact', 0)} |",
        f"| relative_vertical | {counts['by_family'].get('relative_vertical', 0)} |",
        f"| unique scans | {counts['unique_scans']} |",
        f"| unique physical pairs | {counts['unique_physical_pairs']} |",
        f"| label-surface leakage hits | {counts['label_surface_leakage_hits']} |",
        f"| packet path errors | {counts['packet_path_errors']} |",
        f"| validation errors | {counts['validation_errors']} |",
        "",
        "## Category Summary",
        "",
        "| Category | Rows | Packet Ready | Asset Needed | support_contact | relative_vertical | Unique Scans |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["category_summary"]:
        lines.append(
            f"| `{row['anchor_category']}` | {row['rows']} | {row['packet_ready']} | {row['asset_needed']} | "
            f"{row['support_contact']} | {row['relative_vertical']} | {row['unique_scans']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Next TODO",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(args.plan_summary)
    seeds = read_jsonl(args.seeds)
    asset_requests = read_jsonl(args.asset_requests)
    schema = read_json(args.schema)
    validation_errors = validate_plan(plan_summary, seeds)

    visible_rows = [visible_row(row) for row in seeds]
    packet_ready_visible_rows = [row for row in visible_rows if row["evidence_packet_status"] == "ready"]
    manifest_rows = [manifest_row(row) for row in seeds]
    category_rows = category_summary(seeds)
    leakage_hits = surface_leakage_hits(VISIBLE_FIELDS)
    path_errors = packet_path_errors(visible_rows, require_ready_only=False)
    ready_path_errors = packet_path_errors(packet_ready_visible_rows, require_ready_only=True)
    if ready_path_errors:
        path_errors.extend(ready_path_errors)

    family_counts = Counter(str(row.get("predicate_family")) for row in seeds)
    scan_counts = Counter(str(row.get("scan_id")) for row in seeds)
    pair_keys = Counter(
        (
            str(row.get("scan_id")),
            str(row.get("scene_context_id") or row.get("subgraph_id")),
            str(row.get("subject_id")),
            str(row.get("object_id")),
        )
        for row in seeds
    )
    evidence_counts = Counter(row["evidence_packet_status"] for row in visible_rows)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "label_sheet": output_dir / "informative_anchor_label_sheet.tsv",
        "packet_ready_label_sheet": output_dir / "informative_anchor_packet_ready_label_sheet.tsv",
        "manifest_post_label_only": output_dir / "informative_anchor_manifest_post_label_only.jsonl",
        "selected_candidates_internal": output_dir / "selected_candidates_internal.jsonl",
        "category_summary": output_dir / "category_summary.csv",
        "asset_request_plan": output_dir / "asset_request_plan.jsonl",
        "label_surface_leakage_hits": output_dir / "label_surface_leakage_hits.jsonl",
        "packet_path_errors": output_dir / "packet_path_errors.jsonl",
        "v3_label_schema": output_dir / "v3_label_schema.json",
    }

    error_count = len(validation_errors) + len(leakage_hits) + len(path_errors)
    if error_count:
        status = "h002_reliability_target_v3_informative_anchor_candidate_mining_input_errors"
        next_todo = "fix_reliability_target_v3_informative_anchor_candidate_mining_inputs"
        decision = "Candidate mining produced input errors; do not fill labels until these are fixed."
    elif evidence_counts.get("asset_needed", 0):
        status = "h002_reliability_target_v3_informative_anchor_candidate_mining_ready_needs_asset_packets"
        next_todo = "reliability_target_v3_informative_anchor_asset_packets"
        decision = (
            "The informative-anchor full label sheet is prepared, and a packet-ready fallback sheet is also "
            "available. Because 34 selected rows still need asset packets, generate/request those packets before "
            "the preferred balanced label fill. Use the packet-ready fallback only with an explicit coverage caveat."
        )
    else:
        status = "h002_reliability_target_v3_informative_anchor_candidate_mining_ready_for_label_fill"
        next_todo = "reliability_target_v3_informative_anchor_label_fill"
        decision = (
            "The informative-anchor label sheet is packet-complete and ready for v3 label fill. Hidden proxy and "
            "construction fields are stored only in the post-label manifest and must not be used for label decisions."
        )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "decision": decision,
        "next_todo": next_todo,
        "input_paths": {
            "plan_summary": rel_path(args.plan_summary),
            "seeds": rel_path(args.seeds),
            "asset_requests": rel_path(args.asset_requests),
            "schema": rel_path(args.schema),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "labels_filled": False,
            "posterior_trained": False,
            "posterior_smoke_allowed": False,
            "anchor_proxy_categories_are_sampling_strata_only": True,
            "multi_view_as_model_input": False,
            "paper_metric_evidence": False,
        },
        "counts": {
            "selected_seed_rows": len(seeds),
            "full_label_sheet_rows": len(visible_rows),
            "packet_ready_label_sheet_rows": len(packet_ready_visible_rows),
            "asset_needed_rows": evidence_counts.get("asset_needed", 0),
            "asset_request_plan_rows": len(asset_requests),
            "by_family": dict(sorted(family_counts.items())),
            "unique_scans": len(scan_counts),
            "max_rows_per_scan": max(scan_counts.values()) if scan_counts else 0,
            "unique_physical_pairs": len(pair_keys),
            "duplicated_physical_pair_keys": sum(1 for count in pair_keys.values() if count > 1),
            "label_surface_leakage_hits": len(leakage_hits),
            "packet_path_errors": len(path_errors),
            "validation_errors": len(validation_errors),
        },
        "category_summary": category_rows,
        "validation_errors": validation_errors,
    }

    write_tsv(output_paths["label_sheet"], visible_rows, VISIBLE_FIELDS)
    write_tsv(output_paths["packet_ready_label_sheet"], packet_ready_visible_rows, VISIBLE_FIELDS)
    write_jsonl(output_paths["manifest_post_label_only"], manifest_rows)
    write_jsonl(output_paths["selected_candidates_internal"], seeds)
    write_csv(output_paths["category_summary"], category_rows)
    write_jsonl(output_paths["asset_request_plan"], asset_requests)
    write_jsonl(output_paths["label_surface_leakage_hits"], leakage_hits)
    write_jsonl(output_paths["packet_path_errors"], path_errors)
    write_json(output_paths["v3_label_schema"], schema)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    print(
        "status={status} full={full} ready={ready} asset_needed={asset_needed} "
        "leakage={leakage} packet_errors={packet_errors} validation_used={validation_used} "
        "test_used={test_used} posterior_allowed={posterior_allowed} next={next_todo}".format(
            status=summary["status"],
            full=counts["full_label_sheet_rows"],
            ready=counts["packet_ready_label_sheet_rows"],
            asset_needed=counts["asset_needed_rows"],
            leakage=counts["label_surface_leakage_hits"],
            packet_errors=counts["packet_path_errors"],
            validation_used=summary["boundary"]["validation_usage"],
            test_used=summary["boundary"]["test_usage"],
            posterior_allowed=summary["boundary"]["posterior_smoke_allowed"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
