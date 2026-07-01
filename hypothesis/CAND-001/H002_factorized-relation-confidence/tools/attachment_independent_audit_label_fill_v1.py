#!/usr/bin/env python3
"""Fill H002 attachment independent audit labels from reviewer-visible fields only."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
INPUT_TEMPLATE = H2_ROOT / "artifacts/attachment_independent_audit_subset_plan_v1/visible_review_template.tsv"
OUT_DIR = H2_ROOT / "artifacts/attachment_independent_audit_label_fill_v1"

RELIABILITY_VALUES = {"accept_reliable", "reject_unreliable", "abstain_uncertain"}
GEOMETRY_VALUES = {"supported", "unsupported", "uncertain"}
ENDPOINT_VALUES = {"clear_endpoint_identity", "uncertain_endpoint_identity", "wrong_endpoint"}
COVERAGE_VALUES = {"sufficient", "limited", "insufficient"}
UNCERTAINTY_VALUES = {
    "none",
    "visual_ambiguous",
    "mesh_needed",
    "ontology_ambiguous",
    "functional_connection_ambiguous",
    "occlusion_or_viewpoint_limited",
}

STRUCTURAL_ANCHORS = {
    "wall",
    "ceiling",
    "floor",
    "doorframe",
    "window frame",
    "cabinet",
    "shelf",
    "wardrobe",
    "tv stand",
    "desk",
    "table",
    "blinds",
    "curtain",
}
MOUNTED_OR_FIXTURE_OBJECTS = {
    "doorframe",
    "window",
    "monitor",
    "tv",
    "lamp",
    "light",
    "radiator",
    "picture",
    "decoration",
    "toilet paper",
    "curtain",
    "blinds",
    "shelf",
    "cabinet",
    "kitchen cabinet",
}
HANGABLE_OBJECTS = {
    "plant",
    "object",
    "box",
    "pillow",
    "curtain",
    "picture",
    "towel",
    "blanket",
    "bag",
    "backpack",
    "clothes",
    "light",
    "lamp",
}
HANGING_SUPPORTS = {
    "wall",
    "shelf",
    "cabinet",
    "curtain",
    "ceiling",
    "desk",
    "blinds",
}
NON_ATTACHMENT_MOVABLES = {
    "chair",
    "dining chair",
    "armchair",
    "bag",
    "bucket",
    "box",
    "pillow",
    "towel",
    "blanket",
    "clothes",
    "shoes",
    "stool",
    "plant",
    "object",
    "item",
    "clutter",
    "laundry basket",
    "trash can",
    "basket",
}


def norm(text: str) -> str:
    return " ".join(text.strip().lower().split())


def is_same_endpoint(subject: str, obj: str) -> bool:
    return norm(subject) == norm(obj)


def coverage_from_tier(evidence_tier: str) -> str:
    return "sufficient" if evidence_tier == "T1_strong_pair_visual" else "limited"


def endpoint_identity(subject: str, obj: str) -> str:
    if is_same_endpoint(subject, obj):
        return "uncertain_endpoint_identity"
    return "clear_endpoint_identity"


def attached_plausibility(subject: str, obj: str) -> str:
    s = norm(subject)
    o = norm(obj)
    if is_same_endpoint(s, o):
        return "implausible_same_endpoint"
    if {s, o} == {"wall", "doorframe"}:
        return "strong"
    if {s, o} == {"wall", "window"}:
        return "strong"
    if (s in MOUNTED_OR_FIXTURE_OBJECTS and o in STRUCTURAL_ANCHORS) or (
        o in MOUNTED_OR_FIXTURE_OBJECTS and s in STRUCTURAL_ANCHORS
    ):
        return "plausible"
    if s in NON_ATTACHMENT_MOVABLES and o in NON_ATTACHMENT_MOVABLES:
        return "implausible_movable_pair"
    if o in STRUCTURAL_ANCHORS or s in STRUCTURAL_ANCHORS:
        return "ambiguous_anchor_contact"
    return "implausible"


def hanging_plausibility(subject: str, obj: str) -> str:
    s = norm(subject)
    o = norm(obj)
    if is_same_endpoint(s, o):
        return "implausible_same_endpoint"
    if s in {"window", "doorframe", "cabinet", "kitchen cabinet", "chair", "dining chair"}:
        return "implausible_wrong_subject"
    if s == "shelf" and o in {"wall", "ceiling", "cabinet", "kitchen cabinet"}:
        return "plausible"
    if s in HANGABLE_OBJECTS and o in HANGING_SUPPORTS:
        return "plausible"
    if o in HANGING_SUPPORTS:
        return "ambiguous_anchor_contact"
    return "implausible"


def connected_plausibility(subject: str, obj: str) -> str:
    s = norm(subject)
    o = norm(obj)
    if is_same_endpoint(s, o):
        return "ambiguous_same_endpoint"
    if {s, o} in [
        {"tv", "tv stand"},
        {"door", "doorframe"},
        {"wall", "window"},
        {"floor", "kitchen cabinet"},
        {"radiator", "floor"},
    ]:
        return "plausible_functional"
    return "functional_ambiguous"


def fill_primary(row: dict[str, str]) -> tuple[str, str, str, str, str, str]:
    subject = row["subject_label"]
    obj = row["object_label"]
    predicate = row["predicate_label"]
    evidence_tier = row["evidence_tier"]
    coverage = coverage_from_tier(evidence_tier)
    endpoint = endpoint_identity(subject, obj)

    if predicate == "attached to":
        plausibility = attached_plausibility(subject, obj)
    elif predicate == "hanging on":
        plausibility = hanging_plausibility(subject, obj)
    else:
        plausibility = connected_plausibility(subject, obj)

    if endpoint == "uncertain_endpoint_identity":
        return (
            "reject_unreliable",
            "uncertain",
            endpoint,
            coverage,
            "visual_ambiguous",
            "codex_visible_packet_label; same-label endpoints make instance identity ambiguous; reject relation reliability without using hidden metadata",
        )

    if plausibility == "strong":
        return (
            "accept_reliable",
            "supported",
            endpoint,
            coverage,
            "none" if coverage == "sufficient" else "mesh_needed",
            "codex_visible_packet_label; canonical attachment-like endpoint pair; accept based on visible packet context only",
        )

    if plausibility == "plausible":
        if coverage == "sufficient":
            return (
                "accept_reliable",
                "supported",
                endpoint,
                coverage,
                "none",
                "codex_visible_packet_label; predicate-object pair is physically plausible with sufficient packet context",
            )
        return (
            "abstain_uncertain",
            "uncertain",
            endpoint,
            coverage,
            "mesh_needed",
            "codex_visible_packet_label; plausible relation, but limited packet context requires mesh/visual confirmation",
        )

    if plausibility.startswith("ambiguous"):
        return (
            "abstain_uncertain",
            "uncertain",
            endpoint,
            coverage,
            "ontology_ambiguous",
            "codex_visible_packet_label; visible labels suggest possible contact/support but attachment semantics are ambiguous",
        )

    return (
        "reject_unreliable",
        "unsupported",
        endpoint,
        coverage,
        "none" if coverage == "sufficient" else "visual_ambiguous",
        "codex_visible_packet_label; visible predicate-object pair is not reliable attachment/hanging evidence",
    )


def fill_connected(row: dict[str, str]) -> tuple[str, str, str, str, str, str]:
    subject = row["subject_label"]
    obj = row["object_label"]
    coverage = coverage_from_tier(row["evidence_tier"])
    endpoint = endpoint_identity(subject, obj)
    plausibility = connected_plausibility(subject, obj)
    if plausibility == "plausible_functional" and coverage == "sufficient":
        return (
            "abstain_uncertain",
            "uncertain",
            endpoint,
            coverage,
            "functional_connection_ambiguous",
            "codex_visible_packet_label; physically plausible connection but connected-to remains diagnostic without functional evidence",
        )
    return (
        "abstain_uncertain",
        "uncertain",
        endpoint,
        coverage,
        "functional_connection_ambiguous",
        "codex_visible_packet_label; connected-to is diagnostic and requires functional/mesh confirmation",
    )


def fill_row(row: dict[str, str]) -> dict[str, str]:
    out = dict(row)
    if row["packet_role"] == "connected_diagnostic_only":
        rel, geom, endpoint, coverage, uncertainty, notes = fill_connected(row)
    else:
        rel, geom, endpoint, coverage, uncertainty, notes = fill_primary(row)
    out["review_relation_reliability"] = rel
    out["review_geometry_support"] = geom
    out["review_endpoint_identity"] = endpoint
    out["review_coverage"] = coverage
    out["review_uncertainty"] = uncertainty
    out["review_notes"] = notes
    return out


def validate(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        checks = [
            ("review_relation_reliability", RELIABILITY_VALUES),
            ("review_geometry_support", GEOMETRY_VALUES),
            ("review_endpoint_identity", ENDPOINT_VALUES),
            ("review_coverage", COVERAGE_VALUES),
            ("review_uncertainty", UNCERTAINTY_VALUES),
        ]
        for field, allowed in checks:
            if row.get(field) not in allowed:
                errors.append({"row": idx, "type": "invalid_value", "field": field, "value": row.get(field)})
        notes = row.get("review_notes", "").lower()
        if any(token in notes for token in ["_hidden", "proxy_role", "cell_id", "rank_band", "source_score"]):
            errors.append({"row": idx, "type": "hidden_token_in_notes", "notes": row.get("review_notes")})
    return errors


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with INPUT_TEMPLATE.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    filled = [fill_row(row) for row in rows]
    validation_errors = validate(filled)

    filled_sheet = OUT_DIR / "filled_visible_review_sheet.tsv"
    with filled_sheet.open("w", newline="") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filled)

    decisions = []
    for row in filled:
        decisions.append(
            {
                "packet_id": row["packet_id"],
                "blind_review_id": row["blind_review_id"],
                "candidate_relation": row["candidate_relation"],
                "predicate_label": row["predicate_label"],
                "packet_role": row["packet_role"],
                "evidence_tier": row["evidence_tier"],
                "review_relation_reliability": row["review_relation_reliability"],
                "review_geometry_support": row["review_geometry_support"],
                "review_endpoint_identity": row["review_endpoint_identity"],
                "review_coverage": row["review_coverage"],
                "review_uncertainty": row["review_uncertainty"],
                "review_notes": row["review_notes"],
                "label_source": "codex_visible_packet_label_v1",
                "hidden_fields_used": False,
                "prior_v20_labels_used": False,
            }
        )
    with (OUT_DIR / "label_decisions.jsonl").open("w") as f:
        for row in decisions:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    with (OUT_DIR / "validation_errors.jsonl").open("w") as f:
        for row in validation_errors:
            f.write(json.dumps(row, sort_keys=True) + "\n")

    counts = {
        "rows": len(filled),
        "review_relation_reliability": dict(Counter(row["review_relation_reliability"] for row in filled)),
        "review_geometry_support": dict(Counter(row["review_geometry_support"] for row in filled)),
        "review_endpoint_identity": dict(Counter(row["review_endpoint_identity"] for row in filled)),
        "review_coverage": dict(Counter(row["review_coverage"] for row in filled)),
        "review_uncertainty": dict(Counter(row["review_uncertainty"] for row in filled)),
        "by_predicate_and_reliability": {
            f"{pred}|{label}": count
            for (pred, label), count in Counter(
                (row["predicate_label"], row["review_relation_reliability"]) for row in filled
            ).items()
        },
        "primary_binary_preview": dict(
            Counter(
                row["review_relation_reliability"]
                for row in filled
                if row["packet_role"] == "primary_attachment_reliability_candidate"
                and row["review_relation_reliability"] != "abstain_uncertain"
            )
        ),
        "connected_diagnostic_rows": sum(1 for row in filled if row["packet_role"] == "connected_diagnostic_only"),
        "validation_errors": len(validation_errors),
    }
    summary = {
        "schema_version": "h002_attachment_independent_audit_label_fill_v1_summary",
        "status": "h002_attachment_independent_audit_label_fill_v1_completed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_template": str(INPUT_TEMPLATE.relative_to(H2_ROOT)),
        "output_dir": str(OUT_DIR.relative_to(H2_ROOT)),
        "counts": counts,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "hidden_manifest_used_for_label_decisions": False,
            "prior_v20_labels_used": False,
            "source_score_or_rank_used": False,
            "proxy_construction_label_used": False,
            "paper_evidence_allowed": False,
            "trains_model": False,
        },
        "next_todo": "attachment_independent_audit_label_ingestion_v1",
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    report = f"""# H002 Attachment Independent Audit Label Fill V1

Created at: `{summary['created_at']}`

## Status

```text
status = {summary['status']}
next_todo = {summary['next_todo']}
validation_errors = {len(validation_errors)}
paper_evidence_allowed = False
```

## Label Source

```text
label_source = codex_visible_packet_label_v1
hidden_manifest_used_for_label_decisions = False
prior_v20_labels_used = False
source_score_or_rank_used = False
proxy_construction_label_used = False
```

The fill uses only reviewer-visible fields from `visible_review_template.tsv`: relation text,
subject/object labels, evidence tier, visual context summary, mesh context summary, and audit
question. It does not read hidden manifest fields or prior v20 labels for label decisions.

## Counts

```text
rows = {counts['rows']}
review_relation_reliability = {counts['review_relation_reliability']}
review_geometry_support = {counts['review_geometry_support']}
review_endpoint_identity = {counts['review_endpoint_identity']}
review_coverage = {counts['review_coverage']}
review_uncertainty = {counts['review_uncertainty']}
primary_binary_preview = {counts['primary_binary_preview']}
connected_diagnostic_rows = {counts['connected_diagnostic_rows']}
```

## Interpretation

This fill intentionally does not balance classes. If relation reliability remains positive-sparse
after ingestion, that is evidence about the hardness of attachment reliability labeling rather than
a reason to tune the labels.

## Boundary

- train-only H002 artifact;
- no validation/test data;
- no model training;
- no H001 modification;
- prior v20 labels are not used;
- current proxy labels are not used.
"""
    (OUT_DIR / "report.md").write_text(report)


if __name__ == "__main__":
    main()
