#!/usr/bin/env python3
"""Fill G4 audit labels with a transparent structured Codex audit.

This is not a substitute for independent human inspection. It creates a
reviewer-labeled draft from predicate labels, object labels, verifier reason
codes, and geometry fields so G4 can be stress-tested end to end.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
H001_ROOT = SCRIPT_PATH.parents[1]
DEFAULT_AUDIT_DIR = (
    H001_ROOT
    / "artifacts"
    / "evaluation"
    / "vlsat_closed_set"
    / "hardened"
    / "human_audit"
)
DEFAULT_LABELS = DEFAULT_AUDIT_DIR / "labels.jsonl"
DEFAULT_SAMPLES = DEFAULT_AUDIT_DIR / "samples.jsonl"
VALID_LABELS = {
    "valid_relation",
    "invalid_relation",
    "ambiguous",
    "annotation_noise",
    "scan_geometry_missing",
    "verifier_error",
    "semantic_label_too_coarse",
}
QUALITY_ISSUE_LABELS = {"invalid_relation", "semantic_label_too_coarse"}
FLOOR_LIKE = {"floor", "carpet", "shower floor"}
VERTICAL_OR_ATTACHMENT_SURFACES = {
    "wall",
    "ceiling",
    "frame",
    "doorframe",
    "window",
    "windowsill",
    "board",
}
SOFT_OR_FLAT_SUBJECTS = {
    "pillow",
    "blanket",
    "towel",
    "bag",
    "cloth",
    "clothes",
    "object",
    "item",
    "clutter",
    "picture",
    "poster",
}
COMMON_FLOOR_STANDING_SUBJECTS = {
    "cabinet",
    "kitchen cabinet",
    "bath cabinet",
    "chair",
    "stool",
    "table",
    "desk",
    "couch",
    "sofa",
    "plant",
    "washing machine",
    "trash can",
    "trashcan",
    "garbage",
    "bidet",
    "toilet",
    "toilet brush",
    "heater",
    "lamp",
    "refrigerator",
    "shoe",
    "shoes",
}
PLAUSIBLE_SUPPORT_OBJECTS = {
    "floor",
    "carpet",
    "shower floor",
    "table",
    "counter",
    "kitchen counter",
    "cabinet",
    "kitchen cabinet",
    "bath cabinet",
    "couch",
    "sofa",
    "chair",
    "armchair",
    "bed",
    "shelf",
    "rack",
    "stand",
    "stool",
    "refrigerator",
    "commode",
    "washing machine",
    "garbage bin",
    "heater",
    "frame",
    "board",
    "wall",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fill labels.jsonl with Codex structured labels.")
    parser.add_argument("--labels-jsonl", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--samples-jsonl", type=Path, default=DEFAULT_SAMPLES)
    parser.add_argument("--reviewer-id", default="codex_structured_audit_v1")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def lower_text(value: Any) -> str:
    return str(value or "").strip().lower()


def has_reason(sample: dict[str, Any], reason: str) -> bool:
    return reason in set((sample.get("verification") or {}).get("reason_codes") or [])


def number(sample: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = (sample.get("geometry_features") or {}).get(key)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def proximity_label(sample: dict[str, Any]) -> tuple[str, str, bool]:
    status = sample["verification"]["verification_status"]
    distance_xy = number(sample, "distance_xy", 999.0)
    normalized_xy = number(sample, "normalized_distance_xy", 999.0)
    overlap = max(
        number(sample, "projected_iou_xy"),
        number(sample, "projected_subject_overlap_ratio"),
        number(sample, "projected_object_overlap_ratio"),
    )
    if status == "violated":
        if distance_xy >= 1.5 or normalized_xy >= 4.5:
            return (
                "invalid_relation",
                "close-by prediction is far by absolute or normalized XY distance",
                True,
            )
        return (
            "ambiguous",
            "close-by violation is borderline because absolute distance is not clearly large",
            False,
        )
    if status == "satisfied":
        if distance_xy <= 2.2 or overlap > 0.02:
            return ("valid_relation", "near/overlapping geometry supports close-by", True)
        return ("ambiguous", "close-by relation is broad and distance is borderline", False)
    return ("ambiguous", "proximity verifier marked the case uncertain", False)


def relative_vertical_label(sample: dict[str, Any]) -> tuple[str, str, bool]:
    predicate = lower_text(sample["predicate"]["predicate_label"])
    dz = number(sample, "center_delta_z")
    normalized_dz = number(sample, "normalized_center_delta_z")
    margin = max(abs(dz), abs(normalized_dz))
    if margin < 0.12:
        return ("ambiguous", "vertical offset is too small for a confident label", False)
    expected_positive = predicate == "higher than"
    matches = dz > 0 if expected_positive else dz < 0
    if matches:
        return ("valid_relation", "vertical order matches the predicate direction", True)
    return ("invalid_relation", "vertical order contradicts the predicate direction", True)


def support_label(sample: dict[str, Any]) -> tuple[str, str, bool]:
    status = sample["verification"]["verification_status"]
    predicate = lower_text(sample["predicate"]["predicate_label"])
    subject = lower_text(sample["edge"]["subject_label"])
    obj = lower_text(sample["edge"]["object_label"])
    support_subtype = lower_text((sample.get("verification") or {}).get("support_subtype"))
    ndxy = number(sample, "normalized_distance_xy", 999.0)
    overlap = max(
        number(sample, "projected_iou_xy"),
        number(sample, "projected_subject_overlap_ratio"),
        number(sample, "projected_object_overlap_ratio"),
    )
    missing_point = has_reason(sample, "missing_point_evidence")

    if subject == obj and predicate in {"lying on", "standing on", "supported by"}:
        return ("annotation_noise", "same-class/self-like support pair is likely annotation or instance noise", False)

    if predicate in {"standing on", "lying on"} and obj in {"wall", "ceiling", "frame", "doorframe"}:
        return (
            "semantic_label_too_coarse",
            "vertical attachment/contact is expressed as a horizontal support predicate",
            True,
        )

    if subject == "ceiling" or (obj == "ceiling" and predicate != "supported by"):
        return ("invalid_relation", "ceiling support/contact predicate is physically implausible as written", True)

    if predicate == "standing on" and subject in SOFT_OR_FLAT_SUBJECTS:
        return (
            "semantic_label_too_coarse",
            "soft/flat object can be on the support but standing-on is too specific",
            True,
        )

    if predicate == "lying on" and subject not in SOFT_OR_FLAT_SUBJECTS and obj in PLAUSIBLE_SUPPORT_OBJECTS:
        if status == "satisfied" and overlap > 0.2:
            return ("semantic_label_too_coarse", "contact may be valid but lying-on is semantically too specific", True)
        if status == "violated":
            return ("invalid_relation", "lying-on predicate is implausible or unsupported by geometry", True)

    if missing_point:
        if status == "uncertain":
            return ("scan_geometry_missing", "point evidence is missing, so relation cannot be resolved confidently", False)
        if ndxy > 1.0 and overlap == 0.0:
            return ("scan_geometry_missing", "point evidence is missing and coarse geometry is weak", False)

    if predicate == "supported by" and obj in {"wall", "frame", "doorframe", "board"}:
        return (
            "semantic_label_too_coarse",
            "relation is likely attachment/fixture support rather than horizontal support",
            True,
        )

    if predicate == "supported by" and obj in PLAUSIBLE_SUPPORT_OBJECTS:
        if status == "violated" and overlap >= 0.2 and ndxy <= 0.8:
            return ("valid_relation", "object labels and overlap make support plausible despite verifier violation", True)
        if status == "violated" and ndxy > 0.9 and overlap == 0.0:
            return ("invalid_relation", "support object is plausible but geometry is too weak/far", True)
        return ("valid_relation", "support object is plausible and verifier did not prove invalidity", True)

    if predicate == "standing on" and obj in FLOOR_LIKE:
        if subject in COMMON_FLOOR_STANDING_SUBJECTS or support_subtype == "legged_floor_support":
            return ("valid_relation", "floor-standing relation is plausible", True)
        return ("semantic_label_too_coarse", "object may be on the floor but standing-on is too specific", True)

    if predicate in {"standing on", "lying on"} and obj in PLAUSIBLE_SUPPORT_OBJECTS:
        if status == "violated" and (ndxy > 0.9 or overlap == 0.0):
            return ("invalid_relation", "support/contact geometry is weak for the predicted predicate", True)
        return ("valid_relation", "support/contact relation is plausible from labels and geometry", True)

    if status == "satisfied":
        return ("valid_relation", "verifier and structured relation fields support the relation", True)
    if status == "violated":
        return ("invalid_relation", "support/contact prediction is implausible under structured audit", True)
    return ("ambiguous", "support/contact relation is unresolved under structured audit", False)


def label_sample(sample: dict[str, Any]) -> tuple[str, str, bool]:
    family = sample["predicate"]["predicate_family"]
    if family == "proximity":
        return proximity_label(sample)
    if family == "relative_vertical":
        return relative_vertical_label(sample)
    if family == "support_contact":
        return support_label(sample)
    return ("ambiguous", "predicate family is outside structured audit policy", False)


def verifier_decision_correct(sample: dict[str, Any], label: str) -> bool | None:
    status = sample["verification"]["verification_status"]
    if status == "violated":
        return label in QUALITY_ISSUE_LABELS or label == "invalid_relation"
    if status == "satisfied":
        return label == "valid_relation"
    if status == "uncertain":
        if label in {"ambiguous", "scan_geometry_missing"}:
            return True
        if label == "valid_relation":
            return True
        if label in QUALITY_ISSUE_LABELS:
            return False
    return None


def main() -> int:
    args = parse_args()
    labels = load_jsonl(args.labels_jsonl)
    samples = load_jsonl(args.samples_jsonl)
    samples_by_id = {row["sample_id"]: row for row in samples}
    today = date.today().isoformat()
    output = []
    figure_count = 0
    for row in labels:
        sample = samples_by_id[row["sample_id"]]
        label, note, geometry_sufficient = label_sample(sample)
        if label not in VALID_LABELS:
            raise ValueError(f"invalid generated label:{label}")
        updated = dict(row)
        updated["audit_status"] = "labeled"
        updated["human_label"] = label
        updated["relation_visible"] = None
        updated["geometry_sufficient"] = geometry_sufficient
        updated["verifier_decision_correct"] = verifier_decision_correct(sample, label)
        figure_candidate = (
            figure_count < 24
            and sample["bucket"]
            in {
                "semantic_topk_violated",
                "probabilistic_reranked_away",
                "rule_verified_removed",
            }
            and label in QUALITY_ISSUE_LABELS
        )
        updated["figure_candidate"] = figure_candidate
        if figure_candidate:
            figure_count += 1
        updated["reviewer_id"] = args.reviewer_id
        updated["reviewed_at"] = today
        updated["notes"] = (
            f"Codex structured audit from labels/geometry/verifier fields; no independent 3D visual rendering. {note}"
        )
        updated["audit_source"] = "codex_structured_audit_not_independent_human_review"
        output.append(updated)

    if not args.dry_run:
        write_jsonl(args.labels_jsonl, output)

    counts: dict[str, int] = {}
    for row in output:
        counts[row["human_label"]] = counts.get(row["human_label"], 0) + 1
    print(
        json.dumps(
            {
                "dry_run": args.dry_run,
                "labels": len(output),
                "label_counts": dict(sorted(counts.items())),
                "figure_candidates": figure_count,
                "labels_jsonl": str(args.labels_jsonl),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
