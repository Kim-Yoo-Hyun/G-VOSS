#!/usr/bin/env python3
"""Build H002 v3 reliability schema and positive-anchor sampling plan."""

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

DEFAULT_PATH_DECISION = RGA_ROOT / "endpoint_controlled_target_path_decision_codex_proxy_user_requested/summary.json"
DEFAULT_PACKET_MANIFEST = RGA_ROOT / "independent_asset_packets/packet_manifest.jsonl"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v3_positive_anchor_plan"

SELECTED_FAMILIES = {"support_contact", "relative_vertical"}
TARGET_PER_BUCKET = 40

STRUCTURAL_OR_TRIVIAL_LABELS = {
    "floor",
    "wall",
    "ceiling",
    "room",
    "door",
    "window",
    "cabinet",
    "kitchen cabinet",
    "shelf",
    "table",
    "desk",
    "chair",
    "stool",
    "counter",
    "countertop",
}

LABEL_FIELDS = [
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

FORBIDDEN_LABELER_HEADER_FRAGMENTS = [
    "target_y",
    "posterior",
    "p_geom",
    "score",
    "rank",
    "geometry_status",
    "queue",
    "endpoint_flag",
    "label_match",
    "expected",
    "needed",
    "prediction_id",
    "hidden",
]

FAMILY_QUESTIONS = {
    "support_contact": "Does the subject physically contact, rest on, or get supported by the object?",
    "relative_vertical": "Is the subject clearly higher/lower than the object in the evidence?",
}

POSITIVE_CUES = {
    "support_contact": "visible contact, plausible support surface, consistent support direction, non-trivial pair",
    "relative_vertical": "clear vertical ordering, comparable objects, predicate direction matches the evidence",
}

NEGATIVE_CUES = {
    "support_contact": "nearby without support, wrong surface, room-structure trivial relation, segmentation or identity issue",
    "relative_vertical": "wrong direction, ambiguous height, wall/floor dense relation, non-comparable pair",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-decision", type=Path, default=DEFAULT_PATH_DECISION)
    parser.add_argument("--packet-manifest", type=Path, default=DEFAULT_PACKET_MANIFEST)
    parser.add_argument("--hl-queue", type=Path, default=DEFAULT_HL_QUEUE)
    parser.add_argument("--lh-queue", type=Path, default=DEFAULT_LH_QUEUE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--target-per-bucket", type=int, default=TARGET_PER_BUCKET)
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


def iter_jsonl(path: Path):
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def row_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("scan_id")),
        str(row.get("subject_id")),
        str(row.get("object_id")),
        str(row.get("predicate_label")),
    )


def packet_ready(row: dict[str, Any]) -> bool:
    return (
        row.get("packet_status") == "ready"
        and bool(row.get("multiview_packet"))
        and bool(row.get("pointcloud_or_mesh_packet"))
        and bool(row.get("contact_or_context_sheet"))
    )


def load_packets(path: Path) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    packets = {}
    for row in iter_jsonl(path):
        if packet_ready(row):
            packets[row_key(row)] = row
    return packets


def numeric(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        value = row.get(key)
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def norm_label(value: Any) -> str:
    return str(value or "").strip().lower()


def endpoint_pair_note(row: dict[str, Any]) -> str:
    subject = norm_label(row.get("subject_label"))
    obj = norm_label(row.get("object_label"))
    notes = []
    if subject == obj:
        notes.append("same_label_pair")
    if subject in STRUCTURAL_OR_TRIVIAL_LABELS:
        notes.append("subject_structural_or_surface_like")
    if obj in STRUCTURAL_OR_TRIVIAL_LABELS:
        notes.append("object_structural_or_surface_like")
    return ",".join(notes)


def endpoint_pattern(row: dict[str, Any]) -> str:
    subject = norm_label(row.get("subject_label"))
    obj = norm_label(row.get("object_label"))
    family = str(row.get("predicate_family"))
    return "|".join(
        [
            f"subject_structural={int(subject in STRUCTURAL_OR_TRIVIAL_LABELS)}",
            f"object_structural={int(obj in STRUCTURAL_OR_TRIVIAL_LABELS)}",
            f"same_label={int(subject == obj)}",
            f"support_contact={int(family == 'support_contact')}",
            f"relative_vertical={int(family == 'relative_vertical')}",
        ]
    )


def blind_review_id(row: dict[str, Any], category: str) -> str:
    return "ftv3_" + stable_hash("h002_v3_positive_anchor:" + category + ":" + str(row["prediction_id"]))[:12]


def normalize_queue_row(row: dict[str, Any], packet: dict[str, Any], source_queue: str) -> dict[str, Any]:
    normalized = dict(row)
    normalized["source_queue"] = source_queue
    normalized["packet_status"] = packet.get("packet_status")
    normalized["multiview_packet"] = packet.get("multiview_packet", "")
    normalized["pointcloud_or_mesh_packet"] = packet.get("pointcloud_or_mesh_packet", "")
    normalized["contact_or_context_sheet"] = packet.get("contact_or_context_sheet", "")
    normalized["asset_request_id"] = packet.get("asset_request_id", "")
    normalized["original_blind_review_id"] = packet.get("blind_review_id", "")
    normalized["endpoint_pair_note"] = endpoint_pair_note(row)
    normalized["endpoint_flag_pattern_hidden"] = endpoint_pattern(row)
    return normalized


def collect_packet_ready_queue_rows(hl_queue: Path, lh_queue: Path, packets: dict[tuple[str, str, str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_queue, path in [("train_hl_queue", hl_queue), ("train_lh_queue", lh_queue)]:
        for row in iter_jsonl(path):
            if row.get("predicate_family") not in SELECTED_FAMILIES:
                continue
            packet = packets.get(row_key(row))
            if packet is None:
                continue
            rows.append(normalize_queue_row(row, packet, source_queue))
    return rows


def category_for(row: dict[str, Any]) -> list[str]:
    categories: list[str] = []
    geometry = row.get("geometry_status")
    label_status = row.get("label_match_status")
    queue = row.get("queue_kind")
    note = row.get("endpoint_pair_note", "")

    if queue == "LH" and geometry == "satisfied" and label_status == "exact_match":
        categories.append("reliable_positive_anchor")
    if queue == "HL" and geometry == "unsatisfied":
        categories.append("geometry_contradiction_negative")
    if queue == "LH" and geometry == "satisfied" and label_status in {"no_gt_for_pair", "pair_has_other_predicate"}:
        if "structural_or_surface_like" in note or row.get("predicate_family") == "relative_vertical":
            categories.append("trivial_dense_negative")
    if queue == "LH" and geometry == "satisfied" and label_status == "family_match":
        categories.append("ontology_or_uncertain_negative")
    return categories


def category_sort_key(row: dict[str, Any], category: str) -> tuple[Any, ...]:
    p_geom = numeric(row, "p_geom_valid", 0.5)
    rank = numeric(row, "semantic_rank", 999999)
    semantic = numeric(row, "semantic_score_norm", 0.0)
    if category == "reliable_positive_anchor":
        primary = -p_geom
    elif category == "geometry_contradiction_negative":
        primary = p_geom
    elif category == "trivial_dense_negative":
        primary = (0 if row.get("label_match_status") == "no_gt_for_pair" else 1, -p_geom)
    else:
        primary = -p_geom
    return (
        primary,
        rank,
        -semantic,
        str(row.get("scan_id")),
        str(row.get("prediction_id")),
    )


def select_diverse(candidates: list[dict[str, Any]], category: str, limit: int, used_prediction_ids: set[str]) -> list[dict[str, Any]]:
    sorted_rows = sorted(candidates, key=lambda row: category_sort_key(row, category))
    selected: list[dict[str, Any]] = []
    family_counts: Counter[str] = Counter()
    predicate_counts: Counter[str] = Counter()
    scan_counts: Counter[str] = Counter()
    for _ in range(limit):
        best_index = None
        best_score = None
        for index, row in enumerate(sorted_rows):
            if row["prediction_id"] in used_prediction_ids:
                continue
            score = (
                family_counts[str(row.get("predicate_family"))],
                predicate_counts[str(row.get("predicate_label"))],
                scan_counts[str(row.get("scan_id"))],
                category_sort_key(row, category),
            )
            if best_score is None or score < best_score:
                best_score = score
                best_index = index
        if best_index is None:
            break
        row = sorted_rows.pop(best_index)
        selected.append(row)
        used_prediction_ids.add(row["prediction_id"])
        family_counts[str(row.get("predicate_family"))] += 1
        predicate_counts[str(row.get("predicate_label"))] += 1
        scan_counts[str(row.get("scan_id"))] += 1
    return selected


def label_row(row: dict[str, Any]) -> dict[str, Any]:
    family = str(row.get("predicate_family"))
    return {
        "blind_review_id": row["blind_review_id"],
        "review_scope": "h002_reliability_v3_positive_anchor_plan",
        "scan_id": row.get("scan_id", ""),
        "scene_context_id": row.get("subgraph_id", ""),
        "subject_id": row.get("subject_id", ""),
        "subject_label": row.get("subject_label", ""),
        "predicate_label": row.get("predicate_label", ""),
        "predicate_family": family,
        "object_id": row.get("object_id", ""),
        "object_label": row.get("object_label", ""),
        "family_question": FAMILY_QUESTIONS.get(family, "Does the packet evidence support this relation?"),
        "positive_cues": POSITIVE_CUES.get(family, "clear evidence supports the relation and it is informative"),
        "negative_cues": NEGATIVE_CUES.get(family, "contradiction, ambiguity, triviality, ontology mismatch, or identity issue"),
        "evidence_packet_status": row.get("packet_status", ""),
        "multiview_packet": row.get("multiview_packet", ""),
        "pointcloud_or_mesh_packet": row.get("pointcloud_or_mesh_packet", ""),
        "contact_or_context_sheet": row.get("contact_or_context_sheet", ""),
        "reviewer_id": "",
        "review_round": "",
        "endpoint_identity_v3": "",
        "pair_evaluability_v3": "",
        "geometry_support_v3": "",
        "relation_usefulness_v3": "",
        "relation_reliability_v3": "",
        "primary_reason_v3": "",
        "uncertainty_reason_v3": "",
        "label_notes_v3": "",
    }


def manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_v3_positive_anchor_manifest_v1",
        "blind_review_id": row["blind_review_id"],
        "original_blind_review_id": row.get("original_blind_review_id"),
        "asset_request_id": row.get("asset_request_id"),
        "labeler_visible": False,
        "post_label_join_only": True,
        "sampling_category_hidden": row["sampling_category_hidden"],
        "expected_v3_role_hidden": row["expected_v3_role_hidden"],
        "prediction_id_hidden": row.get("prediction_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "hidden_sampling_axes_post_label_only": {
            "source_queue_hidden": row.get("source_queue"),
            "queue_kind_hidden": row.get("queue_kind"),
            "rank_band_hidden": row.get("rank_band"),
            "semantic_rank_hidden": row.get("semantic_rank"),
            "semantic_score_norm_hidden": row.get("semantic_score_norm"),
            "semantic_score_raw_hidden": row.get("semantic_score_raw"),
            "p_geom_valid_hidden": row.get("p_geom_valid"),
            "geometry_status_hidden": row.get("geometry_status"),
            "h001_verification_status_hidden": row.get("h001_verification_status"),
            "label_match_status_hidden": row.get("label_match_status"),
            "matched_predicates_hidden": row.get("matched_predicates", []),
            "matched_gt_ids_hidden": row.get("matched_gt_ids", []),
            "reason_codes_hidden": row.get("reason_codes", []),
            "machine_hint_hidden": row.get("machine_hint"),
            "endpoint_pair_note_hidden": row.get("endpoint_pair_note"),
            "endpoint_flag_pattern_hidden": row.get("endpoint_flag_pattern_hidden"),
        },
        "forbidden_as_labeler_visible": [
            "sampling_category",
            "expected_v3_role",
            "source queue",
            "semantic score/rank",
            "p_geom_valid",
            "geometry_status",
            "h001 verification status",
            "label_match_status",
            "matched GT labels",
            "reason codes",
            "endpoint flag pattern",
            "posterior target fields",
        ],
    }


def target_schema() -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_v3_label_schema_v1",
        "purpose": "Separate geometry support, usefulness, uncertainty, and final reliability before deriving a binary posterior target.",
        "boundary": {
            "split": "train_only",
            "posterior_target_y_defined": False,
            "posterior_smoke_allowed": False,
            "multi_view_as_model_input": False,
            "hidden_sampling_axes_visible_to_labeler": False,
        },
        "required_completion_fields": [
            "reviewer_id",
            "review_round",
            "endpoint_identity_v3",
            "pair_evaluability_v3",
            "geometry_support_v3",
            "relation_usefulness_v3",
            "relation_reliability_v3",
            "primary_reason_v3",
            "uncertainty_reason_v3",
        ],
        "allowed_values": {
            "endpoint_identity_v3": ["both_valid", "subject_invalid", "object_invalid", "pair_invalid", "uncertain"],
            "pair_evaluability_v3": ["evaluable", "partially_evaluable", "not_evaluable", "uncertain"],
            "geometry_support_v3": ["supports_predicate", "contradicts_predicate", "ambiguous", "not_evaluable"],
            "relation_usefulness_v3": ["informative", "trivial_dense_or_room_structure", "ontology_mismatch", "uncertain"],
            "relation_reliability_v3": [
                "reliable",
                "unreliable_geometry",
                "unreliable_trivial",
                "unreliable_ontology",
                "uncertain",
            ],
            "primary_reason_v3": [
                "physical_relation_supported_and_informative",
                "geometry_contradiction",
                "trivial_dense_relation",
                "ontology_or_predicate_granularity_mismatch",
                "identity_or_segmentation_issue",
                "insufficient_evidence",
            ],
            "uncertainty_reason_v3": [
                "none",
                "ambiguous_geometry",
                "low_visibility",
                "ambiguous_predicate",
                "missing_or_partial_packet",
                "other",
            ],
        },
        "binary_derivation_gate": [
            "derive binary reliability only after v3 labels are filled",
            "require enough reliable positives and typed negatives",
            "run target-independence audit before posterior smoke",
            "keep geometry-only target as diagnostic baseline, not main reliability target",
        ],
    }


def header_leakage(fieldnames: list[str]) -> list[dict[str, Any]]:
    hits = []
    for field in fieldnames:
        lower = field.lower()
        for fragment in FORBIDDEN_LABELER_HEADER_FRAGMENTS:
            if fragment in lower:
                hits.append({"field": field, "forbidden_fragment": fragment})
    return hits


def path_errors(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors = []
    for row in rows:
        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = str(row.get(field, ""))
            if not value:
                errors.append({"blind_review_id": row.get("blind_review_id"), "field": field, "error": "empty_path"})
            elif not as_abs(Path(value)).exists():
                errors.append({"blind_review_id": row.get("blind_review_id"), "field": field, "value": value, "error": "missing_path"})
    return errors


def bucket_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    table = []
    for category in sorted({row["sampling_category_hidden"] for row in rows}):
        group = [row for row in rows if row["sampling_category_hidden"] == category]
        table.append(
            {
                "sampling_category": category,
                "rows": len(group),
                "support_contact": sum(1 for row in group if row.get("predicate_family") == "support_contact"),
                "relative_vertical": sum(1 for row in group if row.get("predicate_family") == "relative_vertical"),
                "unique_scans": len({row.get("scan_id") for row in group}),
                "predicate_counts": dict(sorted(Counter(str(row.get("predicate_label")) for row in group).items())),
                "label_match_counts_hidden": dict(sorted(Counter(str(row.get("label_match_status")) for row in group).items())),
                "geometry_status_counts_hidden": dict(sorted(Counter(str(row.get("geometry_status")) for row in group).items())),
            }
        )
    return table


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Reliability Target V3 Positive-Anchor Plan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage artifact.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Multi-view/mesh packet evidence is audit evidence, not model input.",
        "- Hidden construction and score fields are post-label-only.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Sampling Buckets",
        "",
        "| Bucket | Rows | Support | Vertical | Unique Scans |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["bucket_summary"]:
        lines.append(
            f"| `{row['sampling_category']}` | {row['rows']} | {row['support_contact']} | {row['relative_vertical']} | {row['unique_scans']} |"
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
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    path_decision = read_json(args.path_decision)

    packets = load_packets(args.packet_manifest)
    queue_rows = collect_packet_ready_queue_rows(args.hl_queue, args.lh_queue, packets)
    category_pools: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in queue_rows:
        for category in category_for(row):
            category_pools[category].append(row)

    selected: list[dict[str, Any]] = []
    used_prediction_ids: set[str] = set()
    bucket_order = [
        "reliable_positive_anchor",
        "geometry_contradiction_negative",
        "trivial_dense_negative",
        "ontology_or_uncertain_negative",
    ]
    for category in bucket_order:
        bucket_rows = select_diverse(category_pools[category], category, args.target_per_bucket, used_prediction_ids)
        for row in bucket_rows:
            selected_row = dict(row)
            selected_row["sampling_category_hidden"] = category
            selected_row["expected_v3_role_hidden"] = {
                "reliable_positive_anchor": "positive_reliable_candidate",
                "geometry_contradiction_negative": "negative_geometry_contradiction_candidate",
                "trivial_dense_negative": "negative_trivial_dense_candidate",
                "ontology_or_uncertain_negative": "negative_ontology_or_granularity_candidate",
            }[category]
            selected_row["blind_review_id"] = blind_review_id(selected_row, category)
            selected.append(selected_row)

    label_rows = [label_row(row) for row in selected]
    manifest_rows = [manifest_row(row) for row in selected]
    errors = path_errors(label_rows)
    leakage_hits = header_leakage(LABEL_FIELDS)
    bucket_rows = bucket_summary(selected)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "v3_label_schema": output_dir / "v3_label_schema.json",
        "v3_positive_anchor_label_sheet": output_dir / "v3_positive_anchor_label_sheet.tsv",
        "v3_positive_anchor_manifest_post_label_only": output_dir / "v3_positive_anchor_manifest_post_label_only.jsonl",
        "v3_candidate_pool_packet_ready.jsonl": output_dir / "v3_candidate_pool_packet_ready.jsonl",
        "v3_bucket_summary": output_dir / "v3_bucket_summary.json",
        "v3_bucket_summary_csv": output_dir / "v3_bucket_summary.csv",
        "label_surface_leakage_hits": output_dir / "label_surface_leakage_hits.jsonl",
        "packet_path_errors": output_dir / "packet_path_errors.jsonl",
    }

    status = (
        "h002_reliability_target_v3_positive_anchor_plan_ready"
        if len(selected) == args.target_per_bucket * len(bucket_order) and not errors and not leakage_hits
        else "h002_reliability_target_v3_positive_anchor_plan_needs_review"
    )
    summary = {
        "schema_version": "h002_reliability_target_v3_positive_anchor_plan_summary_v1",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "path_decision": rel_path(args.path_decision),
            "packet_manifest": rel_path(args.packet_manifest),
            "hl_queue": rel_path(args.hl_queue),
            "lh_queue": rel_path(args.lh_queue),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "posterior_trained": False,
            "posterior_smoke_allowed": False,
            "multi_view_as_model_input": False,
            "labeler_hidden_fields_visible": False,
            "h001_artifacts_modified": False,
        },
        "path_decision_status": path_decision.get("status"),
        "target_per_bucket": args.target_per_bucket,
        "selected_rows": len(selected),
        "candidate_pool_counts": {key: len(value) for key, value in sorted(category_pools.items())},
        "bucket_summary": bucket_rows,
        "label_surface_leakage_hits": len(leakage_hits),
        "packet_path_errors": len(errors),
        "decision": (
            "V3 positive-anchor label sheet is ready for fill. This is not posterior evidence; "
            "binary reliability target must be derived only after v3 labels and target-independence audit."
        ),
        "next_todo": "reliability_target_v3_label_fill",
    }

    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    write_json(output_paths["v3_label_schema"], target_schema())
    write_tsv(output_paths["v3_positive_anchor_label_sheet"], label_rows, LABEL_FIELDS)
    write_jsonl(output_paths["v3_positive_anchor_manifest_post_label_only"], manifest_rows)
    write_jsonl(output_paths["v3_candidate_pool_packet_ready.jsonl"], selected)
    write_json(output_paths["v3_bucket_summary"], {"buckets": bucket_rows})
    write_csv(output_paths["v3_bucket_summary_csv"], bucket_rows)
    write_jsonl(output_paths["label_surface_leakage_hits"], leakage_hits)
    write_jsonl(output_paths["packet_path_errors"], errors)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = {row["sampling_category"]: row["rows"] for row in summary["bucket_summary"]}
    print(
        f"status={summary['status']} selected={summary['selected_rows']} "
        f"buckets={counts} leakage={summary['label_surface_leakage_hits']} "
        f"path_errors={summary['packet_path_errors']} "
        f"validation_used={summary['boundary']['validation_usage']} test_used={summary['boundary']['test_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
