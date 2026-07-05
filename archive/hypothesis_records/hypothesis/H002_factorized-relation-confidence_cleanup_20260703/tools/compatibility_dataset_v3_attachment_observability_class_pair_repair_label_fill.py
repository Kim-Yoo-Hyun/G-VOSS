#!/usr/bin/env python3
"""Fill R7 attachment-observability labels from visible packet evidence only."""

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

DEFAULT_PACKET_DIR = (
    ARTIFACT_ROOT
    / "compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization"
)
DEFAULT_OUTPUT_DIR = (
    ARTIFACT_ROOT
    / "compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill"
)

EXPECTED_PACKET_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_ready_for_label_fill"
)
EXPECTED_PACKET_NEXT = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill_completed"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill_errors"
)
NEXT_TODO = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_label_ingestion"
)

TARGET_ROWS = 480
REVIEWER_ID = "codex_visible_packet_labeler_user_requested"
REVIEW_ROUND = "1"
LABEL_POLICY = "r7_attachment_observability_visible_packet_conservative_v1"

OBS_VALUES = {"observable", "not_observable", "uncertain"}
REL_VALUES = {"accept", "reject", "abstain"}
QUALITY_VALUES = {"sufficient", "partial", "poor"}
ENDPOINT_VALUES = {"clear", "ambiguous", "wrong_endpoint"}

VISIBLE_FIELDS = [
    "review_row_id",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "relation_route",
    "review_order",
    "packet_scope",
    "packet_status",
    "evidence_tier",
    "subject_image_count",
    "object_image_count",
    "pair_shared_view_count",
    "pair_shared_frame_count",
    "mesh_ready",
    "sequence_ready",
    "review_observability_label",
    "review_relation_label",
    "review_evidence_quality",
    "review_endpoint_identity",
    "review_notes",
]

FILLED_FIELDS = [
    *VISIBLE_FIELDS,
    "reviewer_id",
    "review_round",
    "label_policy",
    "decision_reason",
    "packet_asset_count",
    "used_visible_sheet",
    "used_packet_assets",
    "used_non_visible_metadata",
    "used_existing_target",
]

FORBIDDEN_NOTE_TOKENS = {
    "_hidden",
    "proxy",
    "cell_id",
    "rank",
    "source",
    "p_geom",
    "scan_id",
    "subject_id",
    "object_id",
    "gt_",
    "label_match",
    "geometry_bucket",
    "coverage_proxy",
    "prediction_id",
    "candidate_id",
}

GENERIC_LABELS = {"object", "objects", "item", "items", "thing", "things", "stuff", "clutter"}

IMPLAUSIBLE_HANGING_SUBJECTS = {
    "bed",
    "bench",
    "chair",
    "dining chair",
    "armchair",
    "sofa",
    "couch",
    "table",
    "desk",
    "side table",
    "nightstand",
    "stool",
    "window",
    "doorframe",
    "door",
    "floor",
    "heater",
    "radiator",
    "bucket",
    "box",
    "pillow",
    "trash can",
    "basket",
}

HANGING_SUBJECTS = {
    "curtain",
    "blinds",
    "towel",
    "bag",
    "backpack",
    "clothes",
    "picture",
    "mirror",
    "decoration",
    "light",
    "lamp",
    "chandelier",
    "plant",
}

HANGING_ANCHORS = {
    "wall",
    "ceiling",
    "window",
    "doorframe",
    "door",
    "cabinet",
    "kitchen cabinet",
    "bath cabinet",
    "curtain",
    "blinds",
    "rack",
    "rail",
    "shelf",
}

HANGING_MOUNTABLE_SUBJECTS = {"shelf", "cabinet", "kitchen cabinet", "bath cabinet", "rack", "board"}
HANGING_MOUNTING_ANCHORS = {"wall", "ceiling", "doorframe", "door"}
SUPPORT_OR_PROXIMITY_ANCHORS = {
    "bed",
    "bench",
    "chair",
    "dining chair",
    "armchair",
    "sofa",
    "couch",
    "table",
    "desk",
    "side table",
    "nightstand",
    "stool",
    "floor",
    "pillow",
    "box",
    "bucket",
    "object",
    "item",
}

FIXTURE_OR_MOUNTED_OBJECTS = {
    "window",
    "doorframe",
    "door",
    "cabinet",
    "kitchen cabinet",
    "bath cabinet",
    "shelf",
    "picture",
    "mirror",
    "decoration",
    "lamp",
    "light",
    "radiator",
    "heater",
    "curtain",
    "blinds",
    "monitor",
    "tv",
    "plant",
    "board",
    "frame",
    "rack",
    "pipe",
}

ATTACHMENT_STRUCTURES = {
    "wall",
    "ceiling",
    "floor",
    "doorframe",
    "window",
    "door",
    "cabinet",
    "kitchen cabinet",
    "bath cabinet",
    "shelf",
    "wardrobe",
    "curtain",
    "blinds",
    "rack",
    "rail",
}

MOVABLE_OR_SUPPORT_OBJECTS = {
    "chair",
    "dining chair",
    "armchair",
    "bench",
    "bed",
    "box",
    "bucket",
    "bag",
    "pillow",
    "towel",
    "blanket",
    "clothes",
    "stool",
    "object",
    "item",
    "basket",
    "trash can",
    "side table",
    "table",
    "desk",
    "sofa",
    "couch",
}

STRUCTURAL_ATTACHMENT_PAIRS = [
    {"wall", "doorframe"},
    {"wall", "window"},
    {"wall", "ceiling"},
    {"wall", "floor"},
    {"door", "doorframe"},
    {"ceiling", "light"},
    {"ceiling", "lamp"},
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-dir", type=Path, default=DEFAULT_PACKET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


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


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def packet_dir_for(packet_root: Path, review_row_id: str) -> Path:
    return packet_root / "packets" / review_row_id


def packet_asset_count(packet_root: Path, review_row_id: str) -> int:
    packet_dir = packet_dir_for(packet_root, review_row_id)
    required = ["packet.md", "pair_crop.png", "observability_card.png", "multiview_sheet.jpg"]
    return sum(1 for name in required if (packet_dir / name).exists())


def endpoint_identity(subject: str, obj: str) -> str:
    if subject == obj or subject in GENERIC_LABELS or obj in GENERIC_LABELS:
        return "ambiguous"
    return "clear"


def evidence_quality(row: dict[str, str], packet_assets: int) -> str:
    if row.get("packet_status") != "ready" or packet_assets < 4:
        return "poor" if packet_assets == 0 else "partial"
    subject_count = as_int(row.get("subject_image_count"))
    object_count = as_int(row.get("object_image_count"))
    shared_view_count = as_int(row.get("pair_shared_view_count"))
    mesh_ready = as_bool(row.get("mesh_ready"))
    if subject_count >= 4 and object_count >= 4 and shared_view_count >= 2 and mesh_ready:
        return "sufficient"
    return "partial"


def observability_label(quality: str, endpoint: str) -> str:
    if quality == "poor":
        return "not_observable"
    if endpoint == "ambiguous" or quality == "partial":
        return "uncertain"
    return "observable"


def decision(relation: str, reason: str, note: str) -> dict[str, str]:
    return {
        "review_relation_label": relation,
        "decision_reason": reason,
        "review_notes": note,
    }


def label_hanging(subject: str, obj: str, obs: str) -> dict[str, str]:
    if obs != "observable":
        return decision(
            "abstain",
            "evidence_or_endpoint_not_decidable",
            "visible packet: evidence or endpoint identity is not decisive enough for hanging",
        )
    if subject in IMPLAUSIBLE_HANGING_SUBJECTS:
        return decision(
            "reject",
            "implausible_hanging_subject",
            "visible packet: subject category is better explained by support, contact, or proximity",
        )
    if obj in SUPPORT_OR_PROXIMITY_ANCHORS:
        return decision(
            "reject",
            "support_or_proximity_anchor",
            "visible packet: object category is a support or proximity surface rather than a hanging anchor",
        )
    if subject in HANGING_SUBJECTS and obj in HANGING_ANCHORS:
        return decision(
            "accept",
            "plausible_hanging_subject_anchor_pair",
            "visible packet: endpoint categories form a plausible hanging relation",
        )
    if subject in HANGING_MOUNTABLE_SUBJECTS and obj in HANGING_MOUNTING_ANCHORS:
        return decision(
            "accept",
            "plausible_mounted_object_anchor_pair",
            "visible packet: mountable subject with wall or ceiling-like anchor supports hanging or mounted placement",
        )
    if obj in HANGING_ANCHORS:
        return decision(
            "abstain",
            "anchor_present_relation_family_ambiguous",
            "visible packet: anchor exists, but attachment, support, and hanging are hard to separate",
        )
    return decision(
        "reject",
        "missing_hanging_anchor",
        "visible packet: endpoint categories do not support hanging",
    )


def label_attached(subject: str, obj: str, obs: str) -> dict[str, str]:
    if obs != "observable":
        return decision(
            "abstain",
            "evidence_or_endpoint_not_decidable",
            "visible packet: evidence or endpoint identity is not decisive enough for attachment",
        )
    pair = {subject, obj}
    if any(pair == accepted_pair for accepted_pair in STRUCTURAL_ATTACHMENT_PAIRS):
        return decision(
            "accept",
            "canonical_structural_attachment_pair",
            "visible packet: structural endpoint pair is a canonical attachment relation",
        )
    fixture_to_structure = (
        subject in FIXTURE_OR_MOUNTED_OBJECTS and obj in ATTACHMENT_STRUCTURES
    ) or (
        obj in FIXTURE_OR_MOUNTED_OBJECTS and subject in ATTACHMENT_STRUCTURES
    )
    movable_confounded = (
        subject in MOVABLE_OR_SUPPORT_OBJECTS and obj in ATTACHMENT_STRUCTURES and subject not in FIXTURE_OR_MOUNTED_OBJECTS
    ) or (
        obj in MOVABLE_OR_SUPPORT_OBJECTS and subject in ATTACHMENT_STRUCTURES and obj not in FIXTURE_OR_MOUNTED_OBJECTS
    )
    if fixture_to_structure and not movable_confounded:
        return decision(
            "accept",
            "fixture_or_mounted_object_attachment_pair",
            "visible packet: fixture or mounted endpoint with structural anchor supports attachment",
        )
    if subject in MOVABLE_OR_SUPPORT_OBJECTS and obj in MOVABLE_OR_SUPPORT_OBJECTS:
        return decision(
            "reject",
            "movable_pair_contact_or_proximity_confound",
            "visible packet: movable-object pair is better explained by contact or proximity than attachment",
        )
    if subject in ATTACHMENT_STRUCTURES or obj in ATTACHMENT_STRUCTURES:
        return decision(
            "abstain",
            "structural_anchor_without_clear_attachment",
            "visible packet: structural anchor exists, but direct attachment evidence is ambiguous",
        )
    return decision(
        "reject",
        "missing_attachment_anchor",
        "visible packet: endpoint categories do not support attachment",
    )


def label_row(row: dict[str, str], packet_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    packet_assets = packet_asset_count(packet_root, row["review_row_id"])
    quality = evidence_quality(row, packet_assets)
    endpoint = endpoint_identity(norm(row["subject_label"]), norm(row["object_label"]))
    obs = observability_label(quality, endpoint)
    subject = norm(row["subject_label"])
    obj = norm(row["object_label"])
    predicate = norm(row["predicate_label"])

    if predicate == "attached to":
        label = label_attached(subject, obj, obs)
    elif predicate == "hanging on":
        label = label_hanging(subject, obj, obs)
    else:
        label = decision(
            "abstain",
            "unsupported_predicate_for_r7_label_fill",
            "visible packet: predicate is outside the current attachment observability label-fill scope",
        )

    filled = {
        **row,
        "review_observability_label": obs,
        "review_relation_label": label["review_relation_label"],
        "review_evidence_quality": quality,
        "review_endpoint_identity": endpoint,
        "review_notes": label["review_notes"],
        "reviewer_id": REVIEWER_ID,
        "review_round": REVIEW_ROUND,
        "label_policy": LABEL_POLICY,
        "decision_reason": label["decision_reason"],
        "packet_asset_count": packet_assets,
        "used_visible_sheet": True,
        "used_packet_assets": True,
        "used_non_visible_metadata": False,
        "used_existing_target": False,
    }
    decision_row = {
        "schema_version": SCHEMA_VERSION,
        "review_row_id": row["review_row_id"],
        "candidate_relation": row["candidate_relation"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "object_label": row["object_label"],
        "packet_status": row["packet_status"],
        "packet_asset_count": packet_assets,
        "review_observability_label": obs,
        "review_relation_label": label["review_relation_label"],
        "review_evidence_quality": quality,
        "review_endpoint_identity": endpoint,
        "decision_reason": label["decision_reason"],
        "review_notes": label["review_notes"],
        "provenance": {
            "filled_by": REVIEWER_ID,
            "user_requested_codex_fill": True,
            "used_visible_review_sheet": True,
            "used_packet_assets": True,
            "used_non_visible_metadata": False,
            "used_existing_target": False,
            "used_model_prediction": False,
        },
    }
    return filled, decision_row


def validate_packet_input(summary: dict[str, Any], rows: list[dict[str, str]], packet_root: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_PACKET_STATUS:
        errors.append({"error_type": "unexpected_packet_status", "actual": summary.get("status"), "expected": EXPECTED_PACKET_STATUS})
    if summary.get("next_todo") != EXPECTED_PACKET_NEXT:
        errors.append({"error_type": "unexpected_packet_next_todo", "actual": summary.get("next_todo"), "expected": EXPECTED_PACKET_NEXT})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "packet_validation_errors_present", "actual": summary.get("validation_errors")})
    if len(rows) != TARGET_ROWS:
        errors.append({"error_type": "visible_row_count_mismatch", "actual": len(rows), "expected": TARGET_ROWS})
    for idx, row in enumerate(rows, start=1):
        for field in VISIBLE_FIELDS:
            if field not in row:
                errors.append({"row": idx, "error_type": "missing_visible_field", "field": field})
        packet_dir = packet_dir_for(packet_root, row.get("review_row_id", ""))
        for asset in ["packet.md", "pair_crop.png", "observability_card.png", "multiview_sheet.jpg"]:
            if not (packet_dir / asset).exists():
                errors.append({"row": idx, "error_type": "missing_packet_asset", "asset": asset})
    boundary = summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "fills_labels",
        "ingests_labels",
        "materializes_model_rows",
        "runs_learned_smoke",
        "trains_new_model",
        "paper_evidence_allowed",
        "multi_view_or_mesh_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "packet_boundary_not_false", "key": key, "actual": boundary.get(key)})
    return errors


def validate_filled(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        checks = [
            ("review_observability_label", OBS_VALUES),
            ("review_relation_label", REL_VALUES),
            ("review_evidence_quality", QUALITY_VALUES),
            ("review_endpoint_identity", ENDPOINT_VALUES),
        ]
        for field, allowed in checks:
            if row.get(field) not in allowed:
                errors.append({"row": idx, "error_type": "invalid_label_value", "field": field, "value": row.get(field)})
        text = f"{row.get('review_notes', '')} {row.get('decision_reason', '')}".lower()
        for token in FORBIDDEN_NOTE_TOKENS:
            if token in text:
                errors.append({"row": idx, "error_type": "forbidden_token_in_note_or_reason", "token": token})
        if row.get("used_non_visible_metadata") is not False:
            errors.append({"row": idx, "error_type": "non_visible_metadata_used"})
        if row.get("used_existing_target") is not False:
            errors.append({"row": idx, "error_type": "existing_target_used"})
    return errors


def count_rows(filled: list[dict[str, Any]]) -> list[dict[str, Any]]:
    axes = [
        "review_observability_label",
        "review_relation_label",
        "review_evidence_quality",
        "review_endpoint_identity",
        "predicate_label",
        "decision_reason",
    ]
    rows: list[dict[str, Any]] = []
    for axis in axes:
        counts = Counter(str(row.get(axis)) for row in filled)
        total = sum(counts.values()) or 1
        for value, count in counts.most_common():
            rows.append({"axis": axis, "value": value, "count": count, "share": count / total})
    combo = Counter((row["predicate_label"], row["review_relation_label"]) for row in filled)
    for (predicate, label), count in sorted(combo.items()):
        denom = sum(1 for row in filled if row["predicate_label"] == predicate) or 1
        rows.append(
            {
                "axis": "predicate_x_relation_label",
                "value": f"{predicate}|{label}",
                "count": count,
                "share": count / denom,
            }
        )
    obs_rel = Counter((row["review_observability_label"], row["review_relation_label"]) for row in filled)
    for (obs, label), count in sorted(obs_rel.items()):
        rows.append(
            {
                "axis": "observability_x_relation_label",
                "value": f"{obs}|{label}",
                "count": count,
                "share": count / (len(filled) or 1),
            }
        )
    return rows


def build_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R7 Attachment Observability Class-Pair Repair Label Fill",
            "",
            "## Result",
            "",
            "```text",
            f"status = {summary['status']}",
            f"selected_path = {summary['selected_path']}",
            f"validation_errors = {summary['validation_errors']}",
            f"next_todo = {summary['next_todo']}",
            "```",
            "",
            "## Counts",
            "",
            "```json",
            json.dumps(summary["counts"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Boundary",
            "",
            "The labels were filled from the visible review sheet and packet assets only. This step does not ingest labels, materialize model-safe rows, run learned smoke, use validation/test data, or modify H001 artifacts.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    packet_summary = read_json(args.packet_dir / "summary.json")
    visible_rows = read_csv(args.packet_dir / "visible_review_sheet.csv")
    validation_errors = validate_packet_input(packet_summary, visible_rows, args.packet_dir)

    filled_rows: list[dict[str, Any]] = []
    decision_rows: list[dict[str, Any]] = []
    for row in visible_rows:
        filled, decision_row = label_row(row, args.packet_dir)
        filled_rows.append(filled)
        decision_rows.append(decision_row)
    validation_errors.extend(validate_filled(filled_rows))

    status = STATUS_ERROR if validation_errors else STATUS_READY
    selected_path = (
        "label_fill_errors"
        if validation_errors
        else "codex_visible_packet_labels_filled_user_requested"
    )
    next_todo = "repair_attachment_observability_class_pair_repair_label_fill" if validation_errors else NEXT_TODO

    output_paths = {
        "filled_visible_review_sheet": output_dir / "filled_visible_review_sheet.csv",
        "label_decisions": output_dir / "label_decisions.jsonl",
        "label_count_audit": output_dir / "label_count_audit.csv",
        "validation_errors": output_dir / "validation_errors.jsonl",
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
    }

    counts = {
        "rows": len(filled_rows),
        "review_observability_label": dict(Counter(row["review_observability_label"] for row in filled_rows)),
        "review_relation_label": dict(Counter(row["review_relation_label"] for row in filled_rows)),
        "review_evidence_quality": dict(Counter(row["review_evidence_quality"] for row in filled_rows)),
        "review_endpoint_identity": dict(Counter(row["review_endpoint_identity"] for row in filled_rows)),
        "predicate_label": dict(Counter(row["predicate_label"] for row in filled_rows)),
        "predicate_x_relation_label": {
            f"{predicate}|{label}": count
            for (predicate, label), count in sorted(
                Counter((row["predicate_label"], row["review_relation_label"]) for row in filled_rows).items()
            )
        },
        "decision_reason": dict(Counter(row["decision_reason"] for row in filled_rows).most_common()),
        "packet_asset_count": dict(Counter(str(row["packet_asset_count"]) for row in filled_rows)),
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(validation_errors),
        "next_todo": next_todo,
        "label_policy": LABEL_POLICY,
        "reviewer_id": REVIEWER_ID,
        "packet_status": packet_summary.get("status"),
        "counts": counts,
        "boundary": {
            "split": "train_only_visible_packet_label_fill",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "fills_labels": True,
            "ingests_labels": False,
            "materializes_model_rows": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
            "used_visible_review_sheet": True,
            "used_packet_assets": True,
            "used_non_visible_metadata": False,
            "used_existing_target": False,
            "multi_view_or_mesh_as_audit_evidence": True,
            "multi_view_or_mesh_as_model_input": False,
        },
        "input_paths": {
            "packet_summary": rel_path(args.packet_dir / "summary.json"),
            "visible_review_sheet": rel_path(args.packet_dir / "visible_review_sheet.csv"),
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
    }

    write_csv(output_paths["filled_visible_review_sheet"], filled_rows, FILLED_FIELDS)
    write_jsonl(output_paths["label_decisions"], decision_rows)
    write_csv(output_paths["label_count_audit"], count_rows(filled_rows), ["axis", "value", "count", "share"])
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(build_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
