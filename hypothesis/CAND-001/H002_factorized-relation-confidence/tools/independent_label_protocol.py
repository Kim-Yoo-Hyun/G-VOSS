#!/usr/bin/env python3
"""Create rank-hidden independent audit protocol artifacts for H002."""

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
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_INPUT_QUEUE = RGA_ROOT / "multiview_audit_protocol/all_candidate_queue.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_label_protocol"

BLIND_AUDIT_FIELDS = {
    "reviewer_id": "free text; required",
    "review_round": "integer; required",
    "subject_visibility": "good/partial/poor/not_visible/uncertain",
    "object_visibility": "good/partial/poor/not_visible/uncertain",
    "pair_covisible": "yes/no/uncertain",
    "pair_context_sufficient": "yes/no/uncertain",
    "visual_3d_support": "supports/contradicts/uncertain/not_evaluable",
    "relation_informativeness": "informative/trivial_dense/uncertain/not_evaluable",
    "relation_validity_label": (
        "reliable_informative/valid_but_trivial_dense/annotation_sparsity_candidate/"
        "ontology_mismatch/invalid_relation/invalid_pair/visibility_or_geometry_artifact/"
        "abstain_uncertain"
    ),
    "family_specific_check": "free text or controlled family-specific note",
    "confidence": "high/medium/low",
    "notes": "free text",
}

FAMILY_PRIORITY = {
    "support_contact": 0,
    "proximity": 1,
    "relative_vertical": 2,
}

FAMILY_GUIDANCE = {
    "support_contact": {
        "priority": 1,
        "role": "first multi-view family",
        "question": "Is there visual/3D evidence that the subject is physically supported by or standing on the object?",
        "positive_evidence": [
            "contact or near-contact at plausible support surface",
            "vertical support order is plausible",
            "contact boundary visible in one or more views",
            "object pair is not merely nearby",
        ],
        "negative_evidence": [
            "no visible support/contact",
            "support object is implausible",
            "subject/object identity mismatch",
            "contact is occluded or geometry artifact only",
        ],
    },
    "attachment_deferred": {
        "priority": 2,
        "role": "future high-novelty family; no current H002 blind rows generated",
        "question": "Is there visual/3D evidence of attachment, hanging, or connection rather than mere proximity?",
        "positive_evidence": [
            "visible attachment boundary, hook, cable, handle, fixture, or anchor",
            "hanging direction or connected component is plausible",
            "multi-view context supports physical attachment",
        ],
        "negative_evidence": [
            "only nearby objects with no attachment cue",
            "thin structure missing or occluded",
            "functional connection is semantically plausible but not visually supported",
        ],
    },
    "relative_vertical": {
        "priority": 3,
        "role": "control / robustness family",
        "question": "Is the subject clearly higher/lower than the object under observed 3D evidence?",
        "positive_evidence": [
            "vertical order is visible or clear from 3D context",
            "object extents and identities are reliable",
        ],
        "negative_evidence": [
            "vertical relation is ambiguous due to partial observation",
            "objects overlap or are not comparable",
            "object identity/crop evidence is poor",
        ],
    },
    "proximity": {
        "priority": 4,
        "role": "current debugging family; not best final multi-view payoff",
        "question": "Is the relation informative rather than dense/trivial proximity?",
        "positive_evidence": [
            "pair relation is meaningful for scene graph reasoning",
            "not merely one of many dense nearby object pairs",
        ],
        "negative_evidence": [
            "valid but trivial dense relation",
            "nearby relation is uninformative or over-generated",
        ],
    },
}

LABEL_TO_BINARY_POLICY = {
    "positive": [
        "reliable_informative",
        "annotation_sparsity_candidate",
    ],
    "negative": [
        "valid_but_trivial_dense",
        "invalid_relation",
        "invalid_pair",
        "visibility_or_geometry_artifact",
    ],
    "exclude_or_multiclass_only": [
        "ontology_mismatch",
        "abstain_uncertain",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-queue", type=Path, default=DEFAULT_INPUT_QUEUE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str | None:
    if path is None:
        return None
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
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


def stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def blind_review_id(row: dict[str, Any]) -> str:
    digest = stable_hash("h002_independent_label_protocol_v0:" + str(row["prediction_id"]))
    return "h002_ind_" + digest[:12]


def blind_sort_key(row: dict[str, Any]) -> tuple[int, str]:
    family = str(row.get("predicate_family"))
    return (
        FAMILY_PRIORITY.get(family, 99),
        stable_hash("h002_blind_order:" + str(row["prediction_id"])),
    )


def asset(row: dict[str, Any], key: str) -> Any:
    return (row.get("visual_assets") or {}).get(key)


def list_value(value: Any, index: int) -> Any:
    if not isinstance(value, list) or len(value) <= index:
        return None
    return value[index]


def blind_row(row: dict[str, Any]) -> dict[str, Any]:
    visual_assets = row.get("visual_assets") or {}
    family = str(row.get("predicate_family"))
    guidance = FAMILY_GUIDANCE.get(family, {})
    output = {
        "blind_review_id": blind_review_id(row),
        "scan_id": row.get("scan_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": family,
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "family_priority": guidance.get("priority"),
        "family_question": guidance.get("question"),
        "contact_sheet": visual_assets.get("contact_sheet"),
        "subject_image_count": visual_assets.get("subject_image_count"),
        "object_image_count": visual_assets.get("object_image_count"),
        "subject_image_1": list_value(visual_assets.get("subject_images"), 0),
        "subject_image_2": list_value(visual_assets.get("subject_images"), 1),
        "object_image_1": list_value(visual_assets.get("object_images"), 0),
        "object_image_2": list_value(visual_assets.get("object_images"), 1),
        "mesh_obj": visual_assets.get("mesh_obj"),
        "instance_ply": visual_assets.get("instance_ply"),
    }
    output.update({field: "" for field in BLIND_AUDIT_FIELDS})
    return output


def internal_key_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "blind_review_id": blind_review_id(row),
        "prediction_id": row.get("prediction_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "queue_name_hidden": row.get("queue_name"),
        "priority_rank_hidden": row.get("priority_rank"),
        "working_label_hidden": row.get("working_label"),
        "geometry_status_hidden": row.get("geometry_status"),
        "rank_bucket_hidden": row.get("rank_bucket"),
        "semantic_score_raw_hidden": row.get("semantic_score_raw"),
        "semantic_score_norm_hidden": row.get("semantic_score_norm"),
        "p_geom_valid_hidden": row.get("p_geom_valid"),
        "consistency_score_hidden": row.get("consistency_score"),
        "geometry_residual_proxy_hidden": row.get("geometry_residual_proxy"),
        "leakage_boundary": (
            "Internal key only. Do not expose to annotator before label is locked."
        ),
    }


def write_sheet(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "family_counts": dict(Counter(str(row.get("predicate_family")) for row in rows)),
        "predicate_counts": dict(Counter(str(row.get("predicate_label")) for row in rows)),
        "hidden_working_label_counts": dict(Counter(str(row.get("working_label")) for row in rows)),
        "hidden_queue_counts": dict(Counter(str(row.get("queue_name")) for row in rows)),
        "contact_sheet_count": sum(1 for row in rows if asset(row, "contact_sheet")),
        "mesh_obj_count": sum(1 for row in rows if asset(row, "mesh_obj")),
        "subject_image_count_min": min((asset(row, "subject_image_count") or 0) for row in rows) if rows else 0,
        "subject_image_count_max": max((asset(row, "subject_image_count") or 0) for row in rows) if rows else 0,
        "object_image_count_min": min((asset(row, "object_image_count") or 0) for row in rows) if rows else 0,
        "object_image_count_max": max((asset(row, "object_image_count") or 0) for row in rows) if rows else 0,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Independent Label Protocol",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage protocol.",
        "- Semantic rank, semantic score, `p_geom_valid`, working label, proposed stratum, and queue identity are hidden from annotators.",
        "- Multi-view and mesh assets are audit evidence only, not deployable model input.",
        "- No validation/test rows are used.",
        "- No new posterior is trained in this stage.",
        "",
        "## Blind Sheets",
        "",
        "| Sheet | Rows | Families |",
        "| --- | ---: | --- |",
    ]
    for sheet in summary["blind_sheets"]:
        family_text = ", ".join(f"{key}:{value}" for key, value in sheet["summary"]["family_counts"].items())
        lines.append(f"| `{sheet['path']}` | {sheet['summary']['rows']} | {family_text} |")

    lines.extend(
        [
            "",
            "## Family Priority",
            "",
            "| Family | Priority | Role | Current rows |",
            "| --- | ---: | --- | ---: |",
        ]
    )
    current_counts = summary["candidate_summary"]["family_counts"]
    for family, guidance in sorted(FAMILY_GUIDANCE.items(), key=lambda item: item[1]["priority"]):
        lines.append(
            f"| `{family}` | {guidance['priority']} | {guidance['role']} | {current_counts.get(family, 0)} |"
        )

    lines.extend(
        [
            "",
            "## Label Mapping",
            "",
            "| Binary use | Labels |",
            "| --- | --- |",
        ]
    )
    for key, labels in LABEL_TO_BINARY_POLICY.items():
        lines.append(f"| `{key}` | {', '.join(f'`{label}`' for label in labels)} |")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_queue = as_abs(args.input_queue)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    rows = sorted(read_jsonl(input_queue), key=blind_sort_key)
    blind_rows = [blind_row(row) for row in rows]
    internal_key_rows = [internal_key_row(row) for row in rows]

    by_family: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_family.setdefault(str(row.get("predicate_family")), []).append(row)

    sheets = []
    sheet_specs = [
        ("blind_all_sheet.tsv", rows),
        ("blind_support_contact_sheet.tsv", by_family.get("support_contact", [])),
        ("blind_proximity_sheet.tsv", by_family.get("proximity", [])),
        ("blind_relative_vertical_sheet.tsv", by_family.get("relative_vertical", [])),
    ]
    blind_by_id = {row["blind_review_id"]: row for row in blind_rows}
    original_to_blind = {str(row["prediction_id"]): blind_review_id(row) for row in rows}
    for filename, source_rows in sheet_specs:
        current_blind_rows = [blind_by_id[original_to_blind[str(row["prediction_id"])]] for row in source_rows]
        path = output_dir / filename
        write_sheet(path, current_blind_rows)
        sheets.append(
            {
                "path": rel_path(path),
                "summary": summarize_rows(source_rows),
            }
        )

    internal_key_path = output_dir / "internal_key.jsonl"
    write_jsonl(internal_key_path, internal_key_rows)

    protocol = {
        "schema_version": "h002_independent_label_protocol_v0",
        "created_at": created_at,
        "input_queue": rel_path(input_queue),
        "rank_hidden": True,
        "hidden_from_annotator": [
            "prediction_id",
            "queue_name",
            "priority_rank",
            "working_label",
            "geometry_status",
            "rank_bucket",
            "semantic_score_raw",
            "semantic_score_norm",
            "p_geom_valid",
            "consistency_score",
            "geometry_residual_proxy",
            "proposed_review_stratum",
            "final_controlled_label",
        ],
        "shown_to_annotator": [
            "blind_review_id",
            "scan_id",
            "subject_id",
            "subject_label",
            "predicate_label",
            "predicate_family",
            "object_id",
            "object_label",
            "multi-view crop/contact sheet paths",
            "mesh and instance paths",
            "family-specific question",
        ],
        "audit_fields": BLIND_AUDIT_FIELDS,
        "label_to_binary_policy": LABEL_TO_BINARY_POLICY,
        "family_guidance": FAMILY_GUIDANCE,
        "multi_view_policy": {
            "current_role": "audit_evidence_only",
            "deployable_input_allowed": False,
            "promotion_condition": (
                "Only after rank-hidden independent labels support residual/gated "
                "S_e+G_e+C_e+U_e combiner diagnostics."
            ),
        },
        "combiner_followup": {
            "first": "residual_reliability_model",
            "second": "gated_evidence_model",
            "third": "pairwise_rank_matched_ranking_loss",
            "control": "debiased_or_orthogonalized_factor_audit",
        },
    }
    protocol_path = output_dir / "protocol.json"
    write_json(protocol_path, protocol)

    candidate_summary = summarize_rows(rows)
    current_family_counts = candidate_summary["family_counts"]
    decision = (
        "Independent label protocol is ready for current H002 train-only candidates. "
        "Use support_contact as the first multi-view reliability family, keep "
        "proximity as debugging evidence, use relative_vertical as a control family, "
        "and treat attachment_deferred as a future high-novelty family requiring a "
        "separate candidate generator."
    )
    summary = {
        "schema_version": "h002_independent_label_protocol_summary_v0",
        "status": "independent_label_protocol_ready",
        "created_at": created_at,
        "input_paths": {
            "input_queue": rel_path(input_queue),
        },
        "output_dir": rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "vmv_model_input_allowed": False,
            "rank_hidden_from_annotator": True,
            "score_hidden_from_annotator": True,
        },
        "candidate_summary": candidate_summary,
        "available_family_counts": current_family_counts,
        "attachment_deferred_current_rows": current_family_counts.get("attachment_deferred", 0),
        "blind_sheets": sheets,
        "internal_key": rel_path(internal_key_path),
        "protocol": rel_path(protocol_path),
        "decision": decision,
    }
    summary_path = output_dir / "summary.json"
    write_json(summary_path, summary)
    write_report(output_dir / "report.md", summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        f"status={summary['status']} rows={summary['candidate_summary']['rows']} "
        f"families={summary['available_family_counts']} validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
