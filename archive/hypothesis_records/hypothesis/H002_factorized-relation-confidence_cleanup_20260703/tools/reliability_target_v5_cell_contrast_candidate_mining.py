#!/usr/bin/env python3
"""Create the H002 reliability target v5 cell-contrast label package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

FEASIBILITY_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_feasibility_scan"
DEFAULT_FEASIBILITY_SUMMARY = FEASIBILITY_DIR / "summary.json"
DEFAULT_FEASIBILITY_CONTRACT = FEASIBILITY_DIR / "feasibility_contract.json"
DEFAULT_SEEDS = FEASIBILITY_DIR / "seed_preview_internal.jsonl"
DEFAULT_ASSET_REQUESTS = FEASIBILITY_DIR / "asset_request_preview.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_candidate_mining"

REVIEW_SCOPE = "h002_reliability_v5_relation_review"
SCHEMA_VERSION = "h002_reliability_target_v5_cell_contrast_candidate_mining_v1"

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
    "supporting_cues",
    "contradicting_cues",
    "evidence_packet_status",
    "multiview_packet",
    "pointcloud_or_mesh_packet",
    "contact_or_context_sheet",
    "reviewer_id",
    "review_round",
    "endpoint_identity_v5",
    "pair_evaluability_v5",
    "geometry_support_v5",
    "relation_usefulness_v5",
    "relation_reliability_v5",
    "primary_reason_v5",
    "uncertainty_reason_v5",
    "label_notes_v5",
]

COMPLETION_FIELDS = [
    "reviewer_id",
    "review_round",
    "endpoint_identity_v5",
    "pair_evaluability_v5",
    "geometry_support_v5",
    "relation_usefulness_v5",
    "relation_reliability_v5",
    "primary_reason_v5",
    "uncertainty_reason_v5",
    "label_notes_v5",
]

FAMILY_PROMPTS = {
    "support_contact": {
        "question": "Does the subject physically contact, rest on, support, or attach to the object in the evidence?",
        "supporting_cues": "visible contact or support, plausible load/contact direction, consistent object identity, non-trivial object pair",
        "contradicting_cues": "nearby without contact/support, clear gap or wrong support direction, endpoint identity issue, room-surface triviality",
    },
    "relative_vertical": {
        "question": "Is the subject clearly higher or lower than the object as stated by the predicate?",
        "supporting_cues": "clear vertical ordering, predicate direction matches the evidence, comparable object-level endpoints",
        "contradicting_cues": "wrong vertical direction, ambiguous height, non-comparable room surface, endpoint identity issue",
    },
}

FORBIDDEN_VISIBLE_FIELD_TOKENS = [
    "anchor_category",
    "candidate_proxy",
    "cell_contrast",
    "contrast",
    "endpoint_flag_pattern",
    "geometry_status",
    "hidden",
    "informative_score",
    "label_geometry_bucket",
    "label_match",
    "machine_hint",
    "matched_predicates",
    "p_geom",
    "packet_ready",
    "proxy",
    "queue_kind",
    "rank_band",
    "reason_codes",
    "role_hidden",
    "sampling",
    "semantic_rank",
    "semantic_score",
    "source_queue",
    "stratum",
]

FORBIDDEN_VISIBLE_VALUE_TOKENS = [
    "cell_contrast",
    "contrast_role",
    "geometry_status",
    "p_geom",
    "rank_band",
    "semantic_rank",
    "source_queue",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feasibility-summary", type=Path, default=DEFAULT_FEASIBILITY_SUMMARY)
    parser.add_argument("--feasibility-contract", type=Path, default=DEFAULT_FEASIBILITY_CONTRACT)
    parser.add_argument("--seeds", type=Path, default=DEFAULT_SEEDS)
    parser.add_argument("--asset-requests", type=Path, default=DEFAULT_ASSET_REQUESTS)
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
    return "ftv5cc_" + stable_hash("h002_reliability_v5_cell_contrast:" + str(row["prediction_id"]))[:12]


def family_prompt(row: dict[str, Any]) -> dict[str, str]:
    return FAMILY_PROMPTS.get(
        str(row.get("predicate_family")),
        {
            "question": "Does the relation hold according to the evidence?",
            "supporting_cues": "relation is supported by visual and geometric evidence",
            "contradicting_cues": "relation is contradicted, trivial, or not evaluable from the evidence",
        },
    )


def evidence_status(row: dict[str, Any]) -> str:
    if row.get("packet_ready") is True and row.get("packet_status") == "ready":
        return "ready"
    return "asset_needed"


def visible_row(row: dict[str, Any]) -> dict[str, Any]:
    prompt = family_prompt(row)
    ready = evidence_status(row) == "ready"
    output = {
        "blind_review_id": blind_review_id(row),
        "review_scope": REVIEW_SCOPE,
        "scan_id": row.get("scan_id", ""),
        "scene_context_id": row.get("scene_context_id") or row.get("subgraph_id", ""),
        "subject_id": row.get("subject_id", ""),
        "subject_label": row.get("subject_label", ""),
        "predicate_label": row.get("predicate_label", ""),
        "predicate_family": row.get("predicate_family", ""),
        "object_id": row.get("object_id", ""),
        "object_label": row.get("object_label", ""),
        "family_question": prompt["question"],
        "supporting_cues": prompt["supporting_cues"],
        "contradicting_cues": prompt["contradicting_cues"],
        "evidence_packet_status": evidence_status(row),
        "multiview_packet": row.get("multiview_packet", "") if ready else "",
        "pointcloud_or_mesh_packet": row.get("pointcloud_or_mesh_packet", "") if ready else "",
        "contact_or_context_sheet": row.get("contact_or_context_sheet", "") if ready else "",
    }
    for field in COMPLETION_FIELDS:
        output[field] = ""
    return output


def manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v5_cell_contrast_manifest_v1",
        "batch_name": "reliability_target_v5_cell_contrast_candidate_mining",
        "blind_review_id": blind_review_id(row),
        "prediction_id_hidden": row.get("prediction_id"),
        "scan_id": row.get("scan_id"),
        "scene_context_id": row.get("scene_context_id") or row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "subject_label_norm_hidden": row.get("subject_label_norm"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "object_label_norm_hidden": row.get("object_label_norm"),
        "source_id_hidden": row.get("source_id"),
        "source_queue_hidden": row.get("source_queue_hidden"),
        "queue_kind_hidden": row.get("queue_kind_hidden"),
        "cell_contrast_pair_id_hidden": row.get("cell_contrast_pair_id"),
        "cell_contrast_role_hidden": row.get("cell_contrast_role_hidden"),
        "contrast_role_hidden": row.get("contrast_role_hidden"),
        "cell_contrast_level_hidden": row.get("cell_contrast_level_hidden"),
        "cell_contrast_key_hidden": row.get("cell_contrast_key_hidden"),
        "endpoint_flag_pattern_hidden": row.get("endpoint_flag_pattern_hidden"),
        "object_family_cell_hidden": row.get("object_family_cell_hidden"),
        "endpoint_family_cell_hidden": row.get("endpoint_family_cell_hidden"),
        "subject_object_family_cell_hidden": row.get("subject_object_family_cell_hidden"),
        "rank_band_hidden": row.get("rank_band_hidden"),
        "semantic_rank_hidden": row.get("semantic_rank_hidden"),
        "semantic_score_raw_hidden": row.get("semantic_score_raw_hidden"),
        "semantic_score_norm_hidden": row.get("semantic_score_norm_hidden"),
        "p_geom_valid_hidden": row.get("p_geom_valid_hidden"),
        "geometry_status_hidden": row.get("geometry_status_hidden"),
        "h001_verification_status_hidden": row.get("h001_verification_status_hidden"),
        "label_match_status_hidden": row.get("label_match_status_hidden"),
        "label_match_family_hidden": row.get("label_match_family_hidden"),
        "label_geometry_bucket_hidden": row.get("label_geometry_bucket_hidden"),
        "matched_predicates_hidden": row.get("matched_predicates_hidden"),
        "reason_codes_hidden": row.get("reason_codes_hidden"),
        "machine_hint_hidden": row.get("machine_hint_hidden"),
        "informative_score_hidden": row.get("informative_score_hidden"),
        "room_surface_score_hidden": row.get("room_surface_score_hidden"),
        "packet_status_hidden": evidence_status(row),
        "original_packet_id_hidden": row.get("original_blind_review_id", ""),
        "forbidden_as_labeler_visible": [
            "cell_contrast_pair_id_hidden",
            "cell_contrast_role_hidden",
            "contrast_role_hidden",
            "cell_contrast_level_hidden",
            "cell_contrast_key_hidden",
            "rank_band_hidden",
            "semantic_rank_hidden",
            "semantic_score_norm_hidden",
            "p_geom_valid_hidden",
            "geometry_status_hidden",
            "label_match_status_hidden",
            "machine_hint_hidden",
        ],
    }


def enrich_seed(row: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(row)
    enriched["blind_review_id"] = blind_review_id(row)
    enriched["evidence_packet_status"] = evidence_status(row)
    return enriched


def asset_request_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_request_reason": "v5_cell_contrast_candidate_needs_multiview_pointcloud_context_packet",
        "blind_review_id": blind_review_id(row),
        "prediction_id": row.get("prediction_id"),
        "scan_id": row.get("scan_id"),
        "scene_context_id": row.get("scene_context_id") or row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "cell_contrast_pair_id_hidden": row.get("cell_contrast_pair_id"),
        "cell_contrast_role_hidden": row.get("cell_contrast_role_hidden"),
        "cell_contrast_level_hidden": row.get("cell_contrast_level_hidden"),
        "cell_contrast_key_hidden": row.get("cell_contrast_key_hidden"),
        "requested_artifacts": [
            "multiview_packet",
            "pointcloud_or_mesh_packet",
            "contact_or_context_sheet",
        ],
        "target_packet_stem": blind_review_id(row),
    }


def leakage_hits(fieldnames: list[str]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for field in fieldnames:
        lower = field.lower()
        for token in FORBIDDEN_VISIBLE_FIELD_TOKENS:
            if token in lower:
                hits.append({"field": field, "forbidden_token": token})
    return hits


def visible_value_leakage_hits(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row in rows:
        blind_id = row.get("blind_review_id")
        for field, value in row.items():
            if field in {"multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"}:
                continue
            lower = str(value).lower()
            for token in FORBIDDEN_VISIBLE_VALUE_TOKENS:
                if token in lower:
                    hits.append({"blind_review_id": blind_id, "field": field, "forbidden_token": token})
    return hits


def packet_path_errors(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row in rows:
        if evidence_status(row) != "ready":
            continue
        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = row.get(field)
            if not value:
                errors.append(
                    {
                        "blind_review_id": blind_review_id(row),
                        "prediction_id": row.get("prediction_id"),
                        "field": field,
                        "error": "missing_ready_packet_path",
                    }
                )
                continue
            if not as_abs(Path(str(value))).exists():
                errors.append(
                    {
                        "blind_review_id": blind_review_id(row),
                        "prediction_id": row.get("prediction_id"),
                        "field": field,
                        "path": value,
                        "error": "ready_packet_path_not_found",
                    }
                )
    return errors


def pair_summary_rows(seeds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in seeds:
        by_pair[str(row.get("cell_contrast_pair_id"))].append(row)

    output: list[dict[str, Any]] = []
    for pair_id in sorted(by_pair):
        pair_rows = by_pair[pair_id]
        role_map = {str(row.get("cell_contrast_role_hidden")): row for row in pair_rows}
        pos = role_map.get("positive_proxy", {})
        neg = role_map.get("negative_proxy", {})
        output.append(
            {
                "cell_contrast_pair_id_hidden": pair_id,
                "pair_row_count": len(pair_rows),
                "cell_contrast_level_hidden": pair_rows[0].get("cell_contrast_level_hidden", ""),
                "cell_contrast_key_hidden": pair_rows[0].get("cell_contrast_key_hidden", ""),
                "predicate_label": pair_rows[0].get("predicate_label", ""),
                "predicate_family": pair_rows[0].get("predicate_family", ""),
                "subject_object_family_cell_hidden": pair_rows[0].get("subject_object_family_cell_hidden", ""),
                "positive_blind_review_id": blind_review_id(pos) if pos else "",
                "negative_blind_review_id": blind_review_id(neg) if neg else "",
                "positive_packet_status": evidence_status(pos) if pos else "",
                "negative_packet_status": evidence_status(neg) if neg else "",
                "positive_rank_band_hidden": pos.get("rank_band_hidden", ""),
                "negative_rank_band_hidden": neg.get("rank_band_hidden", ""),
                "positive_geometry_status_hidden": pos.get("geometry_status_hidden", ""),
                "negative_geometry_status_hidden": neg.get("geometry_status_hidden", ""),
                "positive_label_match_status_hidden": pos.get("label_match_status_hidden", ""),
                "negative_label_match_status_hidden": neg.get("label_match_status_hidden", ""),
            }
        )
    return output


def cell_summary_rows(seeds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in seeds:
        by_cell[str(row.get("cell_contrast_key_hidden"))].append(row)

    output: list[dict[str, Any]] = []
    for cell in sorted(by_cell):
        rows = by_cell[cell]
        pair_ids = {row.get("cell_contrast_pair_id") for row in rows}
        output.append(
            {
                "cell_contrast_key_hidden": cell,
                "row_count": len(rows),
                "pair_count": len(pair_ids),
                "positive_proxy_rows": sum(1 for row in rows if row.get("cell_contrast_role_hidden") == "positive_proxy"),
                "negative_proxy_rows": sum(1 for row in rows if row.get("cell_contrast_role_hidden") == "negative_proxy"),
                "packet_ready_rows": sum(1 for row in rows if evidence_status(row) == "ready"),
                "asset_needed_rows": sum(1 for row in rows if evidence_status(row) != "ready"),
                "rank_band_counts_hidden": json.dumps(Counter(str(row.get("rank_band_hidden")) for row in rows), sort_keys=True),
                "geometry_status_counts_hidden": json.dumps(Counter(str(row.get("geometry_status_hidden")) for row in rows), sort_keys=True),
                "label_match_status_counts_hidden": json.dumps(Counter(str(row.get("label_match_status_hidden")) for row in rows), sort_keys=True),
            }
        )
    return output


def validate_inputs(
    feasibility_summary: dict[str, Any],
    feasibility_contract: dict[str, Any],
    seeds: list[dict[str, Any]],
    asset_requests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_status = "h002_reliability_target_v5_cell_contrast_feasibility_ready_for_candidate_mining"
    if feasibility_summary.get("status") != expected_status:
        errors.append({"field": "feasibility_summary.status", "error": "unexpected_status", "value": feasibility_summary.get("status")})
    if feasibility_summary.get("next_todo") != "reliability_target_v5_cell_contrast_candidate_mining":
        errors.append({"field": "feasibility_summary.next_todo", "error": "unexpected_next_todo", "value": feasibility_summary.get("next_todo")})
    if feasibility_contract.get("selected_matching_level") != "strict_predicate_subject_object_endpoint":
        errors.append(
            {
                "field": "feasibility_contract.selected_matching_level",
                "error": "unexpected_matching_level",
                "value": feasibility_contract.get("selected_matching_level"),
            }
        )
    if feasibility_contract.get("next_label_round_allowed") is not True:
        errors.append({"field": "feasibility_contract.next_label_round_allowed", "error": "label_round_not_allowed"})
    expected_rows = feasibility_contract.get("target_rows_for_next_label_round")
    if expected_rows != len(seeds):
        errors.append(
            {
                "field": "feasibility_contract.target_rows_for_next_label_round",
                "error": "seed_count_mismatch",
                "expected": expected_rows,
                "actual": len(seeds),
            }
        )
    expected_asset_rows = feasibility_summary.get("preview_selection", {}).get("asset_needed_rows")
    if expected_asset_rows != len(asset_requests):
        errors.append(
            {
                "field": "feasibility_summary.preview_selection.asset_needed_rows",
                "error": "asset_request_count_mismatch",
                "expected": expected_asset_rows,
                "actual": len(asset_requests),
            }
        )

    seen_prediction_ids: set[str] = set()
    seen_blind_ids: set[str] = set()
    pair_roles: dict[str, Counter[str]] = defaultdict(Counter)
    for row in seeds:
        prediction_id = str(row.get("prediction_id"))
        blind_id = blind_review_id(row)
        if prediction_id in seen_prediction_ids:
            errors.append({"prediction_id": prediction_id, "error": "duplicate_prediction_id"})
        seen_prediction_ids.add(prediction_id)
        if blind_id in seen_blind_ids:
            errors.append({"blind_review_id": blind_id, "error": "duplicate_blind_review_id"})
        seen_blind_ids.add(blind_id)
        pair_roles[str(row.get("cell_contrast_pair_id"))][str(row.get("cell_contrast_role_hidden"))] += 1

    for pair_id, roles in sorted(pair_roles.items()):
        if roles.get("positive_proxy", 0) != 1 or roles.get("negative_proxy", 0) != 1:
            errors.append({"cell_contrast_pair_id": pair_id, "roles": dict(roles), "error": "invalid_pair_role_counts"})
    return errors


def label_schema() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "visible_fields": VISIBLE_FIELDS,
        "completion_fields": {
            "endpoint_identity_v5": ["same_endpoints", "endpoint_identity_issue", "uncertain"],
            "pair_evaluability_v5": ["evaluable", "not_evaluable", "needs_more_evidence"],
            "geometry_support_v5": ["supports", "contradicts", "ambiguous", "not_evaluable"],
            "relation_usefulness_v5": ["useful_nontrivial", "trivial_or_redundant", "not_a_relation", "uncertain"],
            "relation_reliability_v5": ["reliable", "unreliable", "uncertain"],
            "primary_reason_v5": [
                "geometric_support",
                "geometric_contradiction",
                "semantic_ontology_mismatch",
                "annotation_sparsity_candidate",
                "dense_relation_noise",
                "endpoint_identity_issue",
                "insufficient_evidence",
                "trivial_room_surface_or_structure",
                "other",
            ],
            "uncertainty_reason_v5": [
                "",
                "occlusion_or_view_limit",
                "mesh_or_pointcloud_limit",
                "ambiguous_contact",
                "ambiguous_vertical_order",
                "object_segmentation_issue",
                "predicate_definition_ambiguous",
                "other",
            ],
        },
        "label_target_after_review": "relation_reliability_v5_binary_target",
        "hidden_sampling_fields_are_not_label_targets": True,
    }


def report_text(summary: dict[str, Any]) -> str:
    return f"""# H002 Reliability Target V5 Cell Contrast Candidate Mining

Created at: `{summary["created_at"]}`

## Boundary

- Train-only artifact.
- No validation/test rows are used.
- No labels are filled.
- No posterior is trained.
- H001 artifacts are not modified.
- Multi-view remains audit/label evidence, not model input.
- Cell-contrast role, cell key, rank, semantic score, geometry status, and proxy labels are hidden from the label surface.

## Status

`{summary["status"]}`

## Outputs

| Item | Count |
| --- | ---: |
| label rows | {summary["counts"]["label_rows"]} |
| contrast pairs | {summary["counts"]["contrast_pairs"]} |
| contrast cells | {summary["counts"]["contrast_cells"]} |
| packet-ready rows | {summary["counts"]["packet_ready_rows"]} |
| asset-needed rows | {summary["counts"]["asset_needed_rows"]} |
| packet-ready fallback rows | {summary["counts"]["packet_ready_fallback_rows"]} |
| asset request rows | {summary["counts"]["asset_request_rows"]} |
| label surface field leakage hits | {summary["validation"]["label_surface_field_leakage_hits"]} |
| label surface value leakage hits | {summary["validation"]["label_surface_value_leakage_hits"]} |
| packet path errors | {summary["validation"]["packet_path_errors"]} |
| input validation errors | {summary["validation"]["input_validation_errors"]} |

## Interpretation

- The v5 cell-contrast candidate package is ready for asset packet generation/readiness.
- The full candidate sheet should not be filled before asset packets are generated for the `{summary["counts"]["asset_needed_rows"]}` missing rows.
- The packet-ready fallback sheet has only `{summary["counts"]["packet_ready_rows"]}` rows and is too small for label fill or posterior reopening.
- Posterior smoke remains blocked until v5 labels are filled, ingested, and target-independence audit passes.

## Next TODO

`{summary["next_todo"]}`
"""


def main() -> None:
    args = parse_args()
    feasibility_summary = read_json(args.feasibility_summary)
    feasibility_contract = read_json(args.feasibility_contract)
    seeds = read_jsonl(args.seeds)
    plan_asset_requests = read_jsonl(args.asset_requests)

    out_dir = as_abs(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    input_errors = validate_inputs(feasibility_summary, feasibility_contract, seeds, plan_asset_requests)
    visible_rows = [visible_row(row) for row in seeds]
    packet_ready_visible_rows = [visible_row(row) for row in seeds if evidence_status(row) == "ready"]
    manifests = [manifest_row(row) for row in seeds]
    internal_rows = [enrich_seed(row) for row in seeds]
    asset_requests = [asset_request_row(row) for row in seeds if evidence_status(row) != "ready"]
    pair_rows = pair_summary_rows(seeds)
    cell_rows = cell_summary_rows(seeds)
    field_leakage = leakage_hits(VISIBLE_FIELDS)
    value_leakage = visible_value_leakage_hits(visible_rows)
    packet_errors = packet_path_errors(seeds)

    output_paths = {
        "summary": out_dir / "summary.json",
        "report": out_dir / "report.md",
        "label_sheet": out_dir / "cell_contrast_label_sheet.tsv",
        "packet_ready_label_sheet": out_dir / "cell_contrast_packet_ready_label_sheet.tsv",
        "manifest_post_label_only": out_dir / "cell_contrast_manifest_post_label_only.jsonl",
        "selected_candidates_internal": out_dir / "selected_candidates_internal.jsonl",
        "pair_summary": out_dir / "pair_summary.csv",
        "cell_summary": out_dir / "cell_summary.csv",
        "asset_request_plan": out_dir / "asset_request_plan.jsonl",
        "label_surface_field_leakage_hits": out_dir / "label_surface_field_leakage_hits.jsonl",
        "label_surface_value_leakage_hits": out_dir / "label_surface_value_leakage_hits.jsonl",
        "packet_path_errors": out_dir / "packet_path_errors.jsonl",
        "input_validation_errors": out_dir / "input_validation_errors.jsonl",
        "feasibility_contract": out_dir / "feasibility_contract.json",
        "v5_label_schema": out_dir / "v5_label_schema.json",
    }

    boundary = {
        "split": "train_only",
        "validation_usage": False,
        "test_usage": False,
        "labels_filled": False,
        "posterior_trained": False,
        "posterior_smoke_allowed": False,
        "paper_evidence_allowed": False,
        "h001_artifacts_modified": False,
        "multi_view_as_model_input": False,
        "cell_contrast_roles_visible_to_labeler": False,
    }
    counts = {
        "label_rows": len(visible_rows),
        "contrast_pairs": len({row.get("cell_contrast_pair_id") for row in seeds}),
        "contrast_cells": len({row.get("cell_contrast_key_hidden") for row in seeds}),
        "packet_ready_rows": len(packet_ready_visible_rows),
        "packet_ready_fallback_rows": len(packet_ready_visible_rows),
        "asset_needed_rows": len(asset_requests),
        "asset_request_rows": len(asset_requests),
        "family_counts": dict(sorted(Counter(str(row.get("predicate_family")) for row in seeds).items())),
        "hidden_role_counts": dict(sorted(Counter(str(row.get("cell_contrast_role_hidden")) for row in seeds).items())),
        "source_queue_counts_hidden": dict(sorted(Counter(str(row.get("source_queue_hidden")) for row in seeds).items())),
        "rank_band_counts_hidden": dict(sorted(Counter(str(row.get("rank_band_hidden")) for row in seeds).items())),
        "geometry_status_counts_hidden": dict(sorted(Counter(str(row.get("geometry_status_hidden")) for row in seeds).items())),
        "label_match_status_counts_hidden": dict(sorted(Counter(str(row.get("label_match_status_hidden")) for row in seeds).items())),
    }
    validation = {
        "input_validation_errors": len(input_errors),
        "label_surface_field_leakage_hits": len(field_leakage),
        "label_surface_value_leakage_hits": len(value_leakage),
        "packet_path_errors": len(packet_errors),
        "duplicate_visible_ids": len(visible_rows) - len({row["blind_review_id"] for row in visible_rows}),
        "visible_field_count": len(VISIBLE_FIELDS),
        "visible_field_tokens_checked": FORBIDDEN_VISIBLE_FIELD_TOKENS,
        "visible_value_tokens_checked": FORBIDDEN_VISIBLE_VALUE_TOKENS,
    }
    status = "h002_reliability_target_v5_cell_contrast_candidate_mining_ready_needs_asset_packets"
    if input_errors or field_leakage or value_leakage or packet_errors:
        status = "h002_reliability_target_v5_cell_contrast_candidate_mining_ready_with_validation_warnings"

    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "boundary": boundary,
        "feasibility_status": feasibility_summary.get("status"),
        "selected_matching_level": feasibility_contract.get("selected_matching_level"),
        "selected_matching_keys": feasibility_contract.get("selected_matching_keys"),
        "label_schema_version": SCHEMA_VERSION,
        "counts": counts,
        "validation": validation,
        "input_paths": {
            "feasibility_summary": rel_path(args.feasibility_summary),
            "feasibility_contract": rel_path(args.feasibility_contract),
            "seed_preview_internal": rel_path(args.seeds),
            "asset_request_preview": rel_path(args.asset_requests),
        },
        "output_dir": rel_path(out_dir),
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "next_todo": "reliability_target_v5_cell_contrast_asset_packets",
        "posterior_reopen_gate": feasibility_contract.get("posterior_reopen_gate_after_labels"),
    }

    write_tsv(output_paths["label_sheet"], visible_rows, VISIBLE_FIELDS)
    write_tsv(output_paths["packet_ready_label_sheet"], packet_ready_visible_rows, VISIBLE_FIELDS)
    write_jsonl(output_paths["manifest_post_label_only"], manifests)
    write_jsonl(output_paths["selected_candidates_internal"], internal_rows)
    write_csv(output_paths["pair_summary"], pair_rows)
    write_csv(output_paths["cell_summary"], cell_rows)
    write_jsonl(output_paths["asset_request_plan"], asset_requests)
    write_jsonl(output_paths["label_surface_field_leakage_hits"], field_leakage)
    write_jsonl(output_paths["label_surface_value_leakage_hits"], value_leakage)
    write_jsonl(output_paths["packet_path_errors"], packet_errors)
    write_jsonl(output_paths["input_validation_errors"], input_errors)
    write_json(output_paths["feasibility_contract"], feasibility_contract)
    write_json(output_paths["v5_label_schema"], label_schema())
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(report_text(summary), encoding="utf-8")

    print(
        "status={status} rows={rows} pairs={pairs} cells={cells} packet_ready={packet_ready} "
        "asset_needed={asset_needed} field_leakage={field_leakage} value_leakage={value_leakage} "
        "packet_errors={packet_errors} input_errors={input_errors} posterior_allowed={posterior_allowed} "
        "validation_used={validation_used} test_used={test_used} next={next_todo}".format(
            status=summary["status"],
            rows=counts["label_rows"],
            pairs=counts["contrast_pairs"],
            cells=counts["contrast_cells"],
            packet_ready=counts["packet_ready_rows"],
            asset_needed=counts["asset_needed_rows"],
            field_leakage=validation["label_surface_field_leakage_hits"],
            value_leakage=validation["label_surface_value_leakage_hits"],
            packet_errors=validation["packet_path_errors"],
            input_errors=validation["input_validation_errors"],
            posterior_allowed=boundary["posterior_smoke_allowed"],
            validation_used=boundary["validation_usage"],
            test_used=boundary["test_usage"],
            next_todo=summary["next_todo"],
        )
    )


if __name__ == "__main__":
    main()
