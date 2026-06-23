#!/usr/bin/env python3
"""Fill H002 v14 physical relation-family labels using visible fields only."""

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

DEFAULT_CANDIDATE_DIR = RGA_ROOT / "reliability_target_v14_physical_relation_family_candidate_mining"
DEFAULT_CANDIDATE_SUMMARY = DEFAULT_CANDIDATE_DIR / "summary.json"
DEFAULT_INPUT_SHEET = DEFAULT_CANDIDATE_DIR / "label_ready_sheet_v14.tsv"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v14_physical_relation_family_label_fill"

SCHEMA_VERSION = "h002_reliability_target_v14_physical_relation_family_label_fill_v1"
EXPECTED_CANDIDATE_STATUS = "h002_reliability_target_v14_physical_relation_family_candidate_mining_ready_for_label_fill"
EXPECTED_NEXT_TODO = "reliability_target_v14_physical_relation_family_label_fill"
STATUS_READY = "h002_reliability_target_v14_physical_relation_family_label_filled_codex_proxy_visible_only"
STATUS_ERROR = "h002_reliability_target_v14_physical_relation_family_label_fill_errors"
NEXT_TODO = "reliability_target_v14_physical_relation_family_label_ingestion"

REVIEWER_ID = "codex_proxy_v14_physical_relation_visible_only_user_requested"
REVIEW_ROUND = "1"
LABEL_POLICY = "v14_visible_support_vertical_conservative"

VISIBLE_FIELDS = [
    "blind_review_id",
    "review_card",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "relation_family_visible",
    "scene_context_summary_v14",
    "geometry_witness_summary_v14",
    "support_or_vertical_witness_summary_v14",
    "coverage_summary_v14",
    "endpoint_identity_summary_v14",
    "review_question_v14",
    "relation_reliability_state_v14",
    "geometry_support_state_v14",
    "relation_usefulness_state_v14",
    "endpoint_identity_state_v14",
    "coverage_state_v14",
    "primary_reason_v14",
    "uncertainty_reason_v14",
    "review_notes_v14",
]

FILLED_FIELDS = [
    "blind_review_id",
    "review_card",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "relation_family_visible",
    "scene_context_summary_v14",
    "geometry_witness_summary_v14",
    "support_or_vertical_witness_summary_v14",
    "coverage_summary_v14",
    "endpoint_identity_summary_v14",
    "review_question_v14",
    "reviewer_id_v14",
    "review_round_v14",
    "label_policy_v14",
    "relation_reliability_state_v14",
    "geometry_support_state_v14",
    "relation_usefulness_state_v14",
    "endpoint_identity_state_v14",
    "coverage_state_v14",
    "primary_reason_v14",
    "uncertainty_reason_v14",
    "review_notes_v14",
]

ALLOWED_VALUES = {
    "relation_reliability_state_v14": {"accept_reliable", "reject_unreliable", "abstain_uncertain"},
    "geometry_support_state_v14": {"supports", "contradicts", "ambiguous", "not_evaluable"},
    "relation_usefulness_state_v14": {"useful_nontrivial", "trivial_or_redundant", "not_a_relation", "uncertain"},
    "endpoint_identity_state_v14": {"clear", "uncertain", "wrong_endpoint", "not_evaluable"},
    "coverage_state_v14": {"sufficient", "limited", "missing", "not_evaluable"},
    "primary_reason_v14": {
        "clear_support_contact_geometry",
        "contact_geometry_contradiction",
        "clear_vertical_order",
        "vertical_order_contradiction",
        "endpoint_identity_ambiguous",
        "geometry_evidence_mixed",
        "coverage_limited",
    },
    "uncertainty_reason_v14": {
        "none",
        "generic_endpoint_label",
        "mixed_support_contact_cues",
        "similar_height_band",
        "coverage_or_layout_limited",
    },
}

FORBIDDEN_INPUT_FIELDS = {
    "machine_hint",
    "label_match_status",
    "rank_band",
    "scan_id",
    "subgraph_id",
    "prediction_id",
    "semantic_rank",
    "semantic_score",
    "p_geom",
    "source_queue",
    "queue_kind",
    "target_construction",
    "hidden",
}

GENERIC_LABELS = {"object", "objects", "item", "items", "stuff", "thing", "things"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-summary", type=Path, default=DEFAULT_CANDIDATE_SUMMARY)
    parser.add_argument("--input-sheet", type=Path, default=DEFAULT_INPUT_SHEET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
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


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def parse_visible_cues(row: dict[str, str]) -> dict[str, Any]:
    text = norm(row.get("geometry_witness_summary_v14", ""))
    witness = norm(row.get("support_or_vertical_witness_summary_v14", ""))
    subject = norm(row.get("subject_label"))
    obj = norm(row.get("object_label"))
    return {
        "distance": parse_choice(
            text,
            {
                "tight horizontal separation": "tight",
                "moderate horizontal separation": "moderate",
                "wide horizontal separation": "wide",
            },
            "unknown",
        ),
        "overlap": parse_choice(
            text,
            {
                "large footprint overlap": "large",
                "partial footprint overlap": "partial",
                "little footprint overlap": "little",
            },
            "unknown",
        ),
        "vertical_order": parse_choice(
            text,
            {
                "subject center appears above object center": "above",
                "subject center appears below object center": "below",
                "subject and object appear in a similar height band": "similar",
            },
            "unknown",
        ),
        "support_gap": parse_choice(
            witness,
            {
                "near-contact vertical gap": "near",
                "small vertical gap": "small",
                "large vertical gap": "large",
            },
            "unknown",
        ),
        "family": norm(row.get("relation_family_visible")),
        "predicate": norm(row.get("predicate_label")),
        "endpoint_generic": subject in GENERIC_LABELS or obj in GENERIC_LABELS,
    }


def parse_choice(text: str, mapping: dict[str, str], default: str) -> str:
    for marker, value in mapping.items():
        if marker in text:
            return value
    return default


def base_result(
    relation: str,
    geometry: str,
    usefulness: str,
    endpoint: str,
    coverage: str,
    reason: str,
    uncertainty: str,
    note: str,
) -> dict[str, str]:
    return {
        "relation_reliability_state_v14": relation,
        "geometry_support_state_v14": geometry,
        "relation_usefulness_state_v14": usefulness,
        "endpoint_identity_state_v14": endpoint,
        "coverage_state_v14": coverage,
        "primary_reason_v14": reason,
        "uncertainty_reason_v14": uncertainty,
        "review_notes_v14": note,
    }


def label_support_contact(row: dict[str, str], cues: dict[str, Any]) -> dict[str, str]:
    if cues["endpoint_generic"]:
        return base_result(
            "abstain_uncertain",
            "ambiguous",
            "uncertain",
            "uncertain",
            "sufficient",
            "endpoint_identity_ambiguous",
            "generic_endpoint_label",
            "codex v14 visible-only: support/contact geometry is not enough when an endpoint label is generic",
        )

    strong_overlap = cues["overlap"] == "large"
    usable_overlap = cues["overlap"] in {"large", "partial"}
    close_xy = cues["distance"] in {"tight", "moderate"}
    contact_gap = cues["support_gap"] in {"near", "small"}
    vertical_ok = cues["vertical_order"] in {"above", "similar"}

    if close_xy and usable_overlap and contact_gap and vertical_ok:
        return base_result(
            "accept_reliable",
            "supports",
            "useful_nontrivial",
            "clear",
            "sufficient",
            "clear_support_contact_geometry",
            "none",
            "codex v14 visible-only: contact-style relation has compatible overlap, vertical gap, and endpoint ordering",
        )

    if cues["support_gap"] == "large" or cues["vertical_order"] == "below":
        return base_result(
            "reject_unreliable",
            "contradicts",
            "not_a_relation",
            "clear",
            "sufficient",
            "contact_geometry_contradiction",
            "none",
            "codex v14 visible-only: support/contact relation is contradicted by large vertical gap or reversed vertical ordering",
        )

    if cues["distance"] == "wide" and cues["overlap"] == "little":
        return base_result(
            "reject_unreliable",
            "contradicts",
            "not_a_relation",
            "clear",
            "sufficient",
            "contact_geometry_contradiction",
            "none",
            "codex v14 visible-only: support/contact relation is contradicted by wide separation and little footprint overlap",
        )

    if strong_overlap and contact_gap and vertical_ok:
        return base_result(
            "accept_reliable",
            "supports",
            "useful_nontrivial",
            "clear",
            "sufficient",
            "clear_support_contact_geometry",
            "none",
            "codex v14 visible-only: strong overlap and contact-gap cues support the relation despite mixed distance evidence",
        )

    return base_result(
        "abstain_uncertain",
        "ambiguous",
        "uncertain",
        "clear",
        "sufficient",
        "geometry_evidence_mixed",
        "mixed_support_contact_cues",
        "codex v14 visible-only: support/contact cues are mixed and not reliable enough for a binary decision",
    )


def label_relative_vertical(row: dict[str, str], cues: dict[str, Any]) -> dict[str, str]:
    if cues["endpoint_generic"]:
        return base_result(
            "abstain_uncertain",
            "ambiguous",
            "uncertain",
            "uncertain",
            "sufficient",
            "endpoint_identity_ambiguous",
            "generic_endpoint_label",
            "codex v14 visible-only: vertical ordering is not enough when an endpoint label is generic",
        )
    if cues["predicate"] == "lower than" and cues["vertical_order"] == "below":
        return base_result(
            "accept_reliable",
            "supports",
            "useful_nontrivial",
            "clear",
            "sufficient",
            "clear_vertical_order",
            "none",
            "codex v14 visible-only: visible center ordering supports the lower-than relation",
        )
    if cues["predicate"] == "lower than" and cues["vertical_order"] == "above":
        return base_result(
            "reject_unreliable",
            "contradicts",
            "not_a_relation",
            "clear",
            "sufficient",
            "vertical_order_contradiction",
            "none",
            "codex v14 visible-only: visible center ordering contradicts the lower-than relation",
        )
    return base_result(
        "abstain_uncertain",
        "ambiguous",
        "uncertain",
        "clear",
        "sufficient",
        "geometry_evidence_mixed",
        "similar_height_band",
        "codex v14 visible-only: vertical relation is ambiguous from the visible height-band cue",
    )


def label_row(row: dict[str, str]) -> dict[str, str]:
    cues = parse_visible_cues(row)
    if cues["family"] == "support/contact relation":
        return label_support_contact(row, cues)
    if cues["family"] == "relative vertical relation":
        return label_relative_vertical(row, cues)
    return base_result(
        "abstain_uncertain",
        "not_evaluable",
        "uncertain",
        "not_evaluable",
        "not_evaluable",
        "coverage_limited",
        "coverage_or_layout_limited",
        "codex v14 visible-only: relation family is not recognized by the v14 label policy",
    )


def validate_inputs(candidate_summary: dict[str, Any], fieldnames: list[str], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if candidate_summary.get("status") != EXPECTED_CANDIDATE_STATUS:
        errors.append({"error_type": "unexpected_candidate_status", "expected": EXPECTED_CANDIDATE_STATUS, "actual": candidate_summary.get("status")})
    if candidate_summary.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append({"error_type": "unexpected_candidate_next_todo", "expected": EXPECTED_NEXT_TODO, "actual": candidate_summary.get("next_todo")})
    if candidate_summary.get("validation_errors") != 0:
        errors.append({"error_type": "candidate_validation_errors_present", "actual": candidate_summary.get("validation_errors")})
    boundary = candidate_summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "ingests_existing_labels",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "hidden_fields_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "candidate_boundary_violation", "key": key, "actual": boundary.get(key)})
    expected_rows = candidate_summary.get("counts", {}).get("selected_rows")
    if expected_rows != len(rows):
        errors.append({"error_type": "row_count_mismatch", "expected": expected_rows, "actual": len(rows)})
    if fieldnames != VISIBLE_FIELDS:
        errors.append({"error_type": "visible_columns_mismatch", "expected": VISIBLE_FIELDS, "actual": fieldnames})
    for field in fieldnames:
        lower = field.lower()
        for token in FORBIDDEN_INPUT_FIELDS:
            if token in lower:
                errors.append({"error_type": "forbidden_visible_input_field", "field": field, "token": token})
    seen_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        blind_id = row.get("blind_review_id", "")
        if not blind_id:
            errors.append({"error_type": "missing_blind_review_id", "row_number": row_number})
        if blind_id in seen_ids:
            errors.append({"error_type": "duplicate_blind_review_id", "blind_review_id": blind_id})
        seen_ids.add(blind_id)
        for field in [
            "relation_reliability_state_v14",
            "geometry_support_state_v14",
            "relation_usefulness_state_v14",
            "endpoint_identity_state_v14",
            "coverage_state_v14",
            "primary_reason_v14",
            "uncertainty_reason_v14",
            "review_notes_v14",
        ]:
            if str(row.get(field, "")).strip():
                errors.append({"error_type": "review_field_already_filled", "row_number": row_number, "blind_review_id": blind_id, "field": field})
        if row.get("predicate_label") not in {"lying on", "standing on", "lower than"}:
            errors.append({"error_type": "unexpected_predicate", "row_number": row_number, "blind_review_id": blind_id, "predicate": row.get("predicate_label")})
    return errors


def fill_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    filled: list[dict[str, str]] = []
    decisions: list[dict[str, Any]] = []
    for row in rows:
        decision = label_row(row)
        filled_row = {key: row.get(key, "") for key in VISIBLE_FIELDS}
        filled_row.update(
            {
                "reviewer_id_v14": REVIEWER_ID,
                "review_round_v14": REVIEW_ROUND,
                "label_policy_v14": LABEL_POLICY,
                **decision,
            }
        )
        filled.append(filled_row)
        decisions.append(
            {
                "blind_review_id": row.get("blind_review_id"),
                "candidate_relation": row.get("candidate_relation"),
                "subject_label": row.get("subject_label"),
                "predicate_label": row.get("predicate_label"),
                "object_label": row.get("object_label"),
                "relation_family_visible": row.get("relation_family_visible"),
                **parse_visible_cues(row),
                **decision,
                "reviewer_id_v14": REVIEWER_ID,
                "label_policy_v14": LABEL_POLICY,
            }
        )
    return filled, decisions


def validate_outputs(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):
        for field, allowed in ALLOWED_VALUES.items():
            value = row.get(field, "")
            if value not in allowed:
                errors.append({"error_type": "invalid_review_value", "row_number": row_number, "blind_review_id": row.get("blind_review_id"), "field": field, "value": value})
        if row.get("reviewer_id_v14") != REVIEWER_ID:
            errors.append({"error_type": "missing_reviewer_id", "row_number": row_number, "blind_review_id": row.get("blind_review_id")})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 V14 Physical Relation-Family Label Fill",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Result",
        "",
        "Filled the v14 physical relation-family label sheet with Codex proxy labels using only reviewer-visible fields.",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"relation_reliability_state_v14 = {counts['relation_reliability_state_v14']}",
        f"geometry_support_state_v14 = {counts['geometry_support_state_v14']}",
        f"binary_usable_rows = {counts['binary_usable_rows']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Label Policy",
        "",
        "`support_contact` is accepted only when visible overlap, contact-gap, horizontal separation, and vertical-order cues are compatible. It is rejected when visible geometry contradicts contact/support. `lower than` is accepted when visible center ordering supports the relation and rejected when ordering is reversed. Generic endpoint labels are abstained. Hidden audit metadata was not read or used during fill.",
        "",
        "## Boundary",
        "",
        "This is a hypothesis-stage proxy label fill. It is not paper evidence and not posterior evidence.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    candidate_summary_path = as_abs(args.candidate_summary)
    input_sheet = as_abs(args.input_sheet)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    candidate_summary = read_json(candidate_summary_path)
    fieldnames, input_rows = read_tsv(input_sheet)
    validation_errors = validate_inputs(candidate_summary, fieldnames, input_rows)
    filled_rows, decision_rows = fill_rows(input_rows)
    validation_errors.extend(validate_outputs(filled_rows))

    reliability_counts = Counter(row["relation_reliability_state_v14"] for row in filled_rows)
    geometry_counts = Counter(row["geometry_support_state_v14"] for row in filled_rows)
    usefulness_counts = Counter(row["relation_usefulness_state_v14"] for row in filled_rows)
    endpoint_counts = Counter(row["endpoint_identity_state_v14"] for row in filled_rows)
    coverage_counts = Counter(row["coverage_state_v14"] for row in filled_rows)
    reason_counts = Counter(row["primary_reason_v14"] for row in filled_rows)
    uncertainty_counts = Counter(row["uncertainty_reason_v14"] for row in filled_rows)
    predicate_reliability_counts = Counter(f"{row['predicate_label']}|{row['relation_reliability_state_v14']}" for row in filled_rows)
    family_reliability_counts = Counter(f"{row['relation_family_visible']}|{row['relation_reliability_state_v14']}" for row in filled_rows)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "filled_label_sheet": output_dir / "filled_label_sheet_v14.tsv",
        "label_decisions": output_dir / "label_decisions_v14.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    status = STATUS_READY if not validation_errors else STATUS_ERROR
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "candidate_summary": rel_path(candidate_summary_path),
            "input_sheet": rel_path(input_sheet),
            "hidden_manifest_read": False,
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "reviewer_id": REVIEWER_ID,
        "review_round": REVIEW_ROUND,
        "label_policy": LABEL_POLICY,
        "counts": {
            "rows": len(filled_rows),
            "relation_reliability_state_v14": dict(reliability_counts),
            "geometry_support_state_v14": dict(geometry_counts),
            "relation_usefulness_state_v14": dict(usefulness_counts),
            "endpoint_identity_state_v14": dict(endpoint_counts),
            "coverage_state_v14": dict(coverage_counts),
            "primary_reason_v14": dict(reason_counts),
            "uncertainty_reason_v14": dict(uncertainty_counts),
            "predicate_reliability_state_v14": dict(predicate_reliability_counts),
            "family_reliability_state_v14": dict(family_reliability_counts),
            "binary_usable_rows": int(reliability_counts.get("accept_reliable", 0) + reliability_counts.get("reject_unreliable", 0)),
            "positive_rows": int(reliability_counts.get("accept_reliable", 0)),
            "negative_rows": int(reliability_counts.get("reject_unreliable", 0)),
            "abstain_rows": int(reliability_counts.get("abstain_uncertain", 0)),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": True,
            "visible_only_label_fill": True,
            "hidden_audit_manifest_read": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
        },
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO,
    }

    write_tsv(output_paths["filled_label_sheet"], filled_rows, FILLED_FIELDS)
    write_jsonl(output_paths["label_decisions"], decision_rows)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"rows={summary['counts']['rows']}")
    print(f"labels={summary['counts']['relation_reliability_state_v14']}")
    print(f"geometry_support={summary['counts']['geometry_support_state_v14']}")
    print(f"binary_usable_rows={summary['counts']['binary_usable_rows']}")
    print(f"hidden_manifest_read={summary['boundary']['hidden_audit_manifest_read']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
