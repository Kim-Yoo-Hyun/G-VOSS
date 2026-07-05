#!/usr/bin/env python3
"""Fill support/contact visual-mesh audit labels from reviewer-visible packet fields only."""

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

DEFAULT_PACKET_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill"
)

EXPECTED_PACKET_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization_ready_for_label_fill"
)
EXPECTED_PACKET_NEXT = "compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill_v1"
STATUS_READY = "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill_completed"
STATUS_ERROR = "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill_errors"
SELECTED_PATH = "codex_visible_packet_proxy_labels_filled_user_requested"
NEXT_TODO = "compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion"

TARGET_ROWS = 480
REVIEWER_ID = "codex_visible_packet_proxy_labeler_user_requested"
REVIEW_ROUND = "1"
LABEL_POLICY = "support_contact_visible_packet_proxy_v1"

REL_VALUES = {"accept", "reject", "abstain"}
GEOM_VALUES = {"supports", "contradicts", "insufficient", "ambiguous"}
OBS_VALUES = {"sufficient", "limited", "not_evaluable"}
COUNTER_VALUES = {"lying on", "standing on", "supported by", "other", "none", "unknown"}
UNCERTAINTY_VALUES = {"occlusion", "missing_mesh", "ambiguous_pose", "ontology_overlap", "other"}

VISIBLE_FIELDS = [
    "review_id",
    "scan_id_visible",
    "subject_label",
    "predicate_label",
    "object_label",
    "point_crop_path",
    "mesh_render_path",
    "multiview_contact_sheet_path",
    "mesh_contact_summary_visible",
    "pose_summary_visible",
    "coverage_summary_visible",
    "review_relation_reliability",
    "review_geometry_support",
    "review_observability",
    "review_counter_relation",
    "review_uncertainty_reason",
    "review_notes",
]

FILLED_FIELDS = [
    *VISIBLE_FIELDS,
    "reviewer_id",
    "review_round",
    "label_policy",
    "decision_reason",
    "packet_asset_count",
    "used_hidden_manifest",
    "used_source_score_or_rank",
    "used_old_geometry_fields",
]

FORBIDDEN_NOTE_TOKENS = {
    "source_score",
    "source_rank",
    "queue_kind",
    "geometry_status",
    "p_geom",
    "label_match",
    "construction_bucket",
    "hidden_stratum",
    "prediction_id",
    "subject_id",
    "object_id",
    "rank_band",
    "_hidden",
}

GENERIC = {"object", "objects", "item", "items", "thing", "things", "stuff", "clutter"}
STRUCTURAL = {"floor", "wall", "ceiling", "room", "door", "window", "doorframe", "window frame"}
VERTICAL_OR_ATTACHMENT_ANCHORS = {
    "wall",
    "ceiling",
    "door",
    "doorframe",
    "window",
    "curtain",
    "blinds",
    "mirror",
    "picture",
}
SUPPORT_SURFACES = {
    "floor",
    "table",
    "desk",
    "dining table",
    "coffee table",
    "side table",
    "nightstand",
    "kitchen counter",
    "counter",
    "shelf",
    "cabinet",
    "kitchen cabinet",
    "bath cabinet",
    "wardrobe",
    "cupboard",
    "drawer",
    "rack",
    "commode",
    "bed",
    "sofa",
    "couch",
    "armchair",
    "chair",
    "dining chair",
    "bench",
    "stool",
    "ottoman",
    "tv stand",
    "box",
    "basket",
    "bin",
    "bar",
    "washing machine",
    "clothes dryer",
    "dryer",
    "sink",
    "bathtub",
    "shower",
    "toilet",
    "heater",
    "radiator",
    "blanket",
    "pillow",
    "cushion",
}
SOFT_OR_RESTING_SUBJECTS = {
    "pillow",
    "cushion",
    "blanket",
    "towel",
    "clothes",
    "clothing",
    "bag",
    "backpack",
    "pack",
    "suitcase",
    "book",
    "paper",
    "paper towel",
    "shoes",
    "laundry basket",
}
UPRIGHT_OR_STANDING_SUBJECTS = {
    "chair",
    "dining chair",
    "armchair",
    "bench",
    "stool",
    "table",
    "desk",
    "side table",
    "nightstand",
    "shelf",
    "cabinet",
    "kitchen cabinet",
    "bath cabinet",
    "wardrobe",
    "showcase",
    "plant",
    "vase",
    "lamp",
    "table lamp",
    "light",
    "monitor",
    "tv",
    "microwave",
    "printer",
    "laptop",
    "decoration",
    "box",
    "basket",
    "trash can",
    "refrigerator",
    "kitchen appliance",
}


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


def as_abs(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else REPO_ROOT / path


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def path_ready(path_text: str) -> bool:
    return bool(path_text) and as_abs(path_text).exists()


def packet_asset_count(row: dict[str, str]) -> int:
    return sum(
        1
        for field in ["point_crop_path", "mesh_render_path", "multiview_contact_sheet_path"]
        if path_ready(row.get(field, ""))
    )


def observability(row: dict[str, str]) -> str:
    if packet_asset_count(row) == 3 and "packet_status=ready" in row.get("coverage_summary_visible", ""):
        return "sufficient"
    if packet_asset_count(row) > 0:
        return "limited"
    return "not_evaluable"


def decision(
    reliability: str,
    geometry: str,
    counter_relation: str,
    uncertainty: str,
    reason: str,
    note: str,
) -> dict[str, str]:
    return {
        "review_relation_reliability": reliability,
        "review_geometry_support": geometry,
        "review_counter_relation": counter_relation,
        "review_uncertainty_reason": uncertainty,
        "decision_reason": reason,
        "review_notes": note,
    }


def same_or_generic(subject: str, obj: str) -> bool:
    return subject == obj or subject in GENERIC or obj in GENERIC


def support_object(obj: str) -> bool:
    return obj in SUPPORT_SURFACES


def label_lying(subject: str, obj: str) -> dict[str, str]:
    if same_or_generic(subject, obj):
        return decision(
            "abstain",
            "ambiguous",
            "unknown",
            "ontology_overlap",
            "same_or_generic_endpoint_for_lying",
            "codex visible packet proxy: endpoint identity or generic label makes lying-on judgment ambiguous",
        )
    if subject in STRUCTURAL or obj in {"wall", "ceiling", "door", "window"}:
        return decision(
            "reject",
            "contradicts",
            "none",
            "other",
            "structural_or_vertical_endpoint_contradicts_lying",
            "codex visible packet proxy: structural or vertical endpoint does not support a lying-on relation",
        )
    if subject in SOFT_OR_RESTING_SUBJECTS and support_object(obj):
        return decision(
            "accept",
            "supports",
            "none",
            "other",
            "soft_resting_subject_on_support_surface",
            "codex visible packet proxy: soft or resting subject with support surface is accepted as lying on",
        )
    if subject in UPRIGHT_OR_STANDING_SUBJECTS and support_object(obj):
        return decision(
            "reject",
            "contradicts",
            "standing on",
            "ambiguous_pose",
            "upright_subject_better_matches_standing_or_support",
            "codex visible packet proxy: upright object is more consistent with standing on or generic support than lying on",
        )
    if support_object(obj):
        return decision(
            "abstain",
            "ambiguous",
            "supported by",
            "ambiguous_pose",
            "support_present_but_pose_unclear_for_lying",
            "codex visible packet proxy: support is plausible but visible category does not prove lying pose",
        )
    return decision(
        "reject",
        "contradicts",
        "none",
        "other",
        "missing_support_surface_for_lying",
        "codex visible packet proxy: endpoint categories do not support lying on",
    )


def label_standing(subject: str, obj: str) -> dict[str, str]:
    if same_or_generic(subject, obj):
        return decision(
            "abstain",
            "ambiguous",
            "unknown",
            "ontology_overlap",
            "same_or_generic_endpoint_for_standing",
            "codex visible packet proxy: endpoint identity or generic label makes standing-on judgment ambiguous",
        )
    if subject in STRUCTURAL or obj in {"wall", "ceiling", "door", "window", "mirror"}:
        return decision(
            "reject",
            "contradicts",
            "none",
            "other",
            "structural_or_vertical_endpoint_contradicts_standing",
            "codex visible packet proxy: structural or vertical endpoint does not support standing on",
        )
    if subject in SOFT_OR_RESTING_SUBJECTS and support_object(obj):
        return decision(
            "reject",
            "contradicts",
            "lying on",
            "ambiguous_pose",
            "soft_subject_better_matches_lying_or_support",
            "codex visible packet proxy: soft or resting object is more consistent with lying on or generic support",
        )
    if support_object(obj) and subject not in STRUCTURAL:
        return decision(
            "accept",
            "supports",
            "none",
            "other",
            "object_on_support_surface_standing_plausible",
            "codex visible packet proxy: movable or upright object on support surface is accepted as standing on",
        )
    return decision(
        "reject",
        "contradicts",
        "none",
        "other",
        "missing_support_surface_for_standing",
        "codex visible packet proxy: endpoint categories do not support standing on",
    )


def label_supported(subject: str, obj: str) -> dict[str, str]:
    if same_or_generic(subject, obj):
        return decision(
            "abstain",
            "ambiguous",
            "unknown",
            "ontology_overlap",
            "same_or_generic_endpoint_for_supported_by",
            "codex visible packet proxy: broad support relation is ambiguous for same/generic endpoints",
        )
    if subject in STRUCTURAL:
        return decision(
            "reject",
            "contradicts",
            "other",
            "ontology_overlap",
            "structural_subject_not_supported_by_object",
            "codex visible packet proxy: structural subject is not treated as a reliable supported-by candidate",
        )
    if obj in VERTICAL_OR_ATTACHMENT_ANCHORS and obj not in SUPPORT_SURFACES:
        return decision(
            "reject",
            "contradicts",
            "other",
            "ontology_overlap",
            "vertical_anchor_better_matches_attachment_or_hanging",
            "codex visible packet proxy: vertical anchor suggests attachment or hanging rather than support",
        )
    if support_object(obj):
        return decision(
            "accept",
            "supports",
            "none",
            "other",
            "broad_support_surface_for_supported_by",
            "codex visible packet proxy: object category is a plausible support surface for supported by",
        )
    return decision(
        "abstain",
        "ambiguous",
        "unknown",
        "ontology_overlap",
        "support_relation_unclear_from_endpoint_categories",
        "codex visible packet proxy: support relation cannot be decided confidently from visible packet fields",
    )


def label_row(row: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    subject = norm(row["subject_label"])
    obj = norm(row["object_label"])
    predicate = norm(row["predicate_label"])
    obs = observability(row)
    if obs == "not_evaluable":
        label = decision(
            "abstain",
            "insufficient",
            "unknown",
            "missing_mesh",
            "packet_not_evaluable",
            "codex visible packet proxy: packet assets are not available enough for judgment",
        )
    elif predicate == "lying on":
        label = label_lying(subject, obj)
    elif predicate == "standing on":
        label = label_standing(subject, obj)
    elif predicate == "supported by":
        label = label_supported(subject, obj)
    else:
        label = decision(
            "abstain",
            "ambiguous",
            "unknown",
            "ontology_overlap",
            "unsupported_predicate_for_support_contact_fill",
            "codex visible packet proxy: predicate is outside support/contact label-fill scope",
        )
    filled = {
        **row,
        "review_relation_reliability": label["review_relation_reliability"],
        "review_geometry_support": label["review_geometry_support"],
        "review_observability": obs,
        "review_counter_relation": label["review_counter_relation"],
        "review_uncertainty_reason": label["review_uncertainty_reason"],
        "review_notes": label["review_notes"],
        "reviewer_id": REVIEWER_ID,
        "review_round": REVIEW_ROUND,
        "label_policy": LABEL_POLICY,
        "decision_reason": label["decision_reason"],
        "packet_asset_count": packet_asset_count(row),
        "used_hidden_manifest": False,
        "used_source_score_or_rank": False,
        "used_old_geometry_fields": False,
    }
    decision_row = {
        "schema_version": SCHEMA_VERSION,
        "review_id": row["review_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "object_label": row["object_label"],
        "packet_asset_count": packet_asset_count(row),
        "review_relation_reliability": filled["review_relation_reliability"],
        "review_geometry_support": filled["review_geometry_support"],
        "review_observability": filled["review_observability"],
        "review_counter_relation": filled["review_counter_relation"],
        "review_uncertainty_reason": filled["review_uncertainty_reason"],
        "decision_reason": filled["decision_reason"],
        "review_notes": filled["review_notes"],
        "provenance": {
            "filled_by": REVIEWER_ID,
            "user_requested_codex_fill": True,
            "used_visible_review_sheet": True,
            "used_packet_paths": True,
            "used_packet_asset_existence": True,
            "used_hidden_manifest": False,
            "used_source_score_or_rank": False,
            "used_old_geometry_status_or_p_geom_valid": False,
            "used_label_match_status": False,
            "used_prediction_id": False,
            "used_subject_or_object_ids": False,
        },
    }
    return filled, decision_row


def validate_packet_input(summary: dict[str, Any], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
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
        for field in ["point_crop_path", "mesh_render_path", "multiview_contact_sheet_path"]:
            if not path_ready(row.get(field, "")):
                errors.append({"row": idx, "error_type": "missing_packet_asset", "field": field, "value": row.get(field)})
    boundary = summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "runs_learned_smoke", "trains_new_model"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "packet_boundary_not_false", "key": key, "actual": boundary.get(key)})
    return errors


def validate_filled(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        checks = [
            ("review_relation_reliability", REL_VALUES),
            ("review_geometry_support", GEOM_VALUES),
            ("review_observability", OBS_VALUES),
            ("review_counter_relation", COUNTER_VALUES),
            ("review_uncertainty_reason", UNCERTAINTY_VALUES),
        ]
        for field, allowed in checks:
            if row.get(field) not in allowed:
                errors.append({"row": idx, "error_type": "invalid_value", "field": field, "value": row.get(field)})
        notes = str(row.get("review_notes", "")).lower()
        reason = str(row.get("decision_reason", "")).lower()
        for token in FORBIDDEN_NOTE_TOKENS:
            if token in notes or token in reason:
                errors.append({"row": idx, "error_type": "hidden_token_in_note_or_reason", "token": token})
    return errors


def build_count_rows(filled: list[dict[str, Any]]) -> list[dict[str, Any]]:
    axes = [
        "review_relation_reliability",
        "review_geometry_support",
        "review_observability",
        "review_counter_relation",
        "review_uncertainty_reason",
        "predicate_label",
        "decision_reason",
    ]
    rows: list[dict[str, Any]] = []
    for axis in axes:
        counts = Counter(str(row.get(axis)) for row in filled)
        total = sum(counts.values()) or 1
        for value, count in counts.most_common():
            rows.append({"axis": axis, "value": value, "count": count, "share": count / total})
    combo = Counter((row["predicate_label"], row["review_relation_reliability"]) for row in filled)
    for (predicate, label), count in sorted(combo.items()):
        rows.append(
            {
                "axis": "predicate_x_reliability",
                "value": f"{predicate}|{label}",
                "count": count,
                "share": count / (sum(1 for row in filled if row["predicate_label"] == predicate) or 1),
            }
        )
    return rows


def build_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Label Fill",
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
            "## Label Counts",
            "",
            "```json",
            json.dumps(summary["label_counts"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Boundary",
            "",
            "These are Codex proxy labels requested by the user. The fill used reviewer-visible packet fields and packet asset paths only. Hidden manifest fields, source score/rank, old geometry fields, label-match status, prediction ids, and subject/object ids were not used for label decisions.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    packet_summary = read_json(args.packet_dir / "summary.json")
    visible_rows = read_csv(args.packet_dir / "visible_review_sheet_with_packets.csv")
    validation_errors = validate_packet_input(packet_summary, visible_rows)

    filled_rows: list[dict[str, Any]] = []
    decision_rows: list[dict[str, Any]] = []
    for row in visible_rows:
        filled, decision_row = label_row(row)
        filled_rows.append(filled)
        decision_rows.append(decision_row)
    validation_errors.extend(validate_filled(filled_rows))

    rel_counts = Counter(row["review_relation_reliability"] for row in filled_rows)
    geom_counts = Counter(row["review_geometry_support"] for row in filled_rows)
    obs_counts = Counter(row["review_observability"] for row in filled_rows)
    uncertainty_counts = Counter(row["review_uncertainty_reason"] for row in filled_rows)
    predicate_rel_counts = Counter(
        f"{row['predicate_label']}|{row['review_relation_reliability']}" for row in filled_rows
    )

    status = STATUS_READY if not validation_errors else STATUS_ERROR
    next_todo = NEXT_TODO if not validation_errors else "repair_support_contact_visual_mesh_audit_label_fill"

    output_paths = {
        "filled_visible_review_sheet": output_dir / "filled_visible_review_sheet.csv",
        "label_decisions": output_dir / "label_decisions.jsonl",
        "label_counts": output_dir / "label_counts.csv",
        "report": output_dir / "report.md",
        "summary": output_dir / "summary.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "packet_materialization_status": packet_summary.get("status"),
        "label_counts": {
            "rows": len(filled_rows),
            "review_relation_reliability": dict(rel_counts),
            "review_geometry_support": dict(geom_counts),
            "review_observability": dict(obs_counts),
            "review_uncertainty_reason": dict(uncertainty_counts),
            "predicate_x_reliability": dict(sorted(predicate_rel_counts.items())),
        },
        "boundary": {
            "split": "train full only",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "fills_labels": True,
            "label_provenance": REVIEWER_ID,
            "independent_human_audit": False,
            "user_requested_codex_fill": True,
            "used_visible_review_sheet": True,
            "used_packet_paths": True,
            "used_packet_asset_existence": True,
            "used_hidden_manifest": False,
            "used_source_score_or_rank": False,
            "used_old_geometry_status_or_p_geom_valid": False,
            "used_label_match_status": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
    }

    write_csv(output_paths["filled_visible_review_sheet"], filled_rows, FILLED_FIELDS)
    write_jsonl(output_paths["label_decisions"], decision_rows)
    write_csv(output_paths["label_counts"], build_count_rows(filled_rows), ["axis", "value", "count", "share"])
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(build_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
