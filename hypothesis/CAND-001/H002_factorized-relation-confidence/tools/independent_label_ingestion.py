#!/usr/bin/env python3
"""Validate and ingest rank-hidden H002 independent audit labels."""

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
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_PROTOCOL_DIR = RGA_ROOT / "independent_label_protocol"
DEFAULT_COMPLETED_SHEET = DEFAULT_PROTOCOL_DIR / "blind_all_sheet.tsv"
DEFAULT_INTERNAL_KEY = DEFAULT_PROTOCOL_DIR / "internal_key.jsonl"
DEFAULT_PROTOCOL = DEFAULT_PROTOCOL_DIR / "protocol.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_label_ingestion"

REQUIRED_COMPLETION_FIELDS = [
    "reviewer_id",
    "review_round",
    "relation_validity_label",
    "confidence",
]

FORBIDDEN_BLIND_HEADER_FRAGMENTS = [
    "score",
    "rank",
    "working_label",
    "p_geom",
    "geometry_status",
    "queue",
    "prediction_id",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--completed-sheet", type=Path, default=DEFAULT_COMPLETED_SHEET)
    parser.add_argument("--internal-key", type=Path, default=DEFAULT_INTERNAL_KEY)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
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


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


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


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
        return fieldnames, [dict(row) for row in reader]


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


def nonempty(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def label_policy(protocol: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    policy = protocol["label_to_binary_policy"]
    for label in policy["positive"]:
        mapping[label] = "positive"
    for label in policy["negative"]:
        mapping[label] = "negative"
    for label in policy["exclude_or_multiclass_only"]:
        mapping[label] = "exclude_or_multiclass_only"
    return mapping


def binary_y(label_use: str) -> int | None:
    if label_use == "positive":
        return 1
    if label_use == "negative":
        return 0
    return None


def validate_headers(fieldnames: list[str]) -> list[dict[str, Any]]:
    errors = []
    for field in fieldnames:
        lower = field.lower()
        matches = [fragment for fragment in FORBIDDEN_BLIND_HEADER_FRAGMENTS if fragment in lower]
        if matches:
            errors.append(
                {
                    "error_type": "forbidden_blind_header",
                    "field": field,
                    "matches": matches,
                }
            )
    if "blind_review_id" not in fieldnames:
        errors.append({"error_type": "missing_required_header", "field": "blind_review_id"})
    return errors


def build_ingestion(
    completed_rows: list[dict[str, str]],
    internal_rows: list[dict[str, Any]],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    internal_by_blind_id = {str(row["blind_review_id"]): row for row in internal_rows}
    label_map = label_policy(protocol)
    allowed_labels = set(label_map)
    errors = []
    completed_labels = []
    binary_targets = []
    multiclass_targets = []
    seen_ids = Counter(str(row.get("blind_review_id")) for row in completed_rows)
    for blind_id, count in seen_ids.items():
        if count > 1:
            errors.append(
                {
                    "error_type": "duplicate_blind_review_id",
                    "blind_review_id": blind_id,
                    "count": count,
                }
            )

    for row_idx, row in enumerate(completed_rows, start=2):
        blind_id = str(row.get("blind_review_id") or "")
        internal = internal_by_blind_id.get(blind_id)
        if internal is None:
            errors.append(
                {
                    "error_type": "unknown_blind_review_id",
                    "row_number": row_idx,
                    "blind_review_id": blind_id,
                }
            )
            continue

        label = str(row.get("relation_validity_label") or "").strip()
        is_started = any(nonempty(row.get(field)) for field in REQUIRED_COMPLETION_FIELDS)
        is_complete = all(nonempty(row.get(field)) for field in REQUIRED_COMPLETION_FIELDS)
        if not is_started:
            continue
        if not is_complete:
            missing = [field for field in REQUIRED_COMPLETION_FIELDS if not nonempty(row.get(field))]
            errors.append(
                {
                    "error_type": "incomplete_label_row",
                    "row_number": row_idx,
                    "blind_review_id": blind_id,
                    "missing": missing,
                }
            )
            continue
        if label not in allowed_labels:
            errors.append(
                {
                    "error_type": "invalid_relation_validity_label",
                    "row_number": row_idx,
                    "blind_review_id": blind_id,
                    "label": label,
                    "allowed": sorted(allowed_labels),
                }
            )
            continue

        label_use = label_map[label]
        joined = {
            "schema_version": "h002_independent_label_v0",
            "blind_review_id": blind_id,
            "prediction_id": internal["prediction_id"],
            "scan_id": internal["scan_id"],
            "subgraph_id": internal["subgraph_id"],
            "subject_id": internal["subject_id"],
            "predicate_label": internal["predicate_label"],
            "predicate_family": internal["predicate_family"],
            "object_id": internal["object_id"],
            "relation_validity_label": label,
            "label_use": label_use,
            "reviewer_id": row.get("reviewer_id"),
            "review_round": row.get("review_round"),
            "confidence": row.get("confidence"),
            "subject_visibility": row.get("subject_visibility"),
            "object_visibility": row.get("object_visibility"),
            "pair_covisible": row.get("pair_covisible"),
            "pair_context_sufficient": row.get("pair_context_sufficient"),
            "visual_3d_support": row.get("visual_3d_support"),
            "relation_informativeness": row.get("relation_informativeness"),
            "family_specific_check": row.get("family_specific_check"),
            "notes": row.get("notes"),
            "hidden_provenance": {
                "queue_name": internal.get("queue_name_hidden"),
                "working_label": internal.get("working_label_hidden"),
                "geometry_status": internal.get("geometry_status_hidden"),
                "rank_bucket": internal.get("rank_bucket_hidden"),
                "semantic_score_raw": internal.get("semantic_score_raw_hidden"),
                "semantic_score_norm": internal.get("semantic_score_norm_hidden"),
                "p_geom_valid": internal.get("p_geom_valid_hidden"),
                "consistency_score": internal.get("consistency_score_hidden"),
                "geometry_residual_proxy": internal.get("geometry_residual_proxy_hidden"),
            },
            "leakage_boundary": (
                "Hidden provenance is for post-label analysis only and must not be "
                "used as deployable input feature."
            ),
        }
        completed_labels.append(joined)
        multiclass_targets.append(
            {
                "schema_version": "h002_independent_multiclass_target_v0",
                "blind_review_id": blind_id,
                "prediction_id": internal["prediction_id"],
                "predicate_family": internal["predicate_family"],
                "predicate_label": internal["predicate_label"],
                "relation_validity_label": label,
                "label_use": label_use,
                "allowed_use": "train-only independent label diagnostic",
            }
        )
        y = binary_y(label_use)
        if y is not None:
            binary_targets.append(
                {
                    "schema_version": "h002_independent_binary_target_v0",
                    "blind_review_id": blind_id,
                    "prediction_id": internal["prediction_id"],
                    "posterior_target": y,
                    "relation_validity_label": label,
                    "label_use": label_use,
                    "predicate_family": internal["predicate_family"],
                    "predicate_label": internal["predicate_label"],
                    "reviewer_id": row.get("reviewer_id"),
                    "confidence": row.get("confidence"),
                    "allowed_use": "train-only independent posterior diagnostic",
                    "paper_locked": False,
                }
            )
    return {
        "errors": errors,
        "completed_labels": completed_labels,
        "binary_targets": binary_targets,
        "multiclass_targets": multiclass_targets,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Independent Label Ingestion",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage ingestion protocol.",
        "- No validation/test rows are used.",
        "- No posterior is trained in this stage.",
        "- Hidden fields are joined only after labels are completed.",
        "- Hidden provenance must not become deployable input features.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| completed label rows | {summary['counts']['completed_label_rows']} |",
        f"| binary target rows | {summary['counts']['binary_target_rows']} |",
        f"| multiclass target rows | {summary['counts']['multiclass_target_rows']} |",
        f"| errors | {summary['counts']['errors']} |",
        "",
        "## Label Counts",
        "",
        "| Label | Count |",
        "| --- | ---: |",
    ]
    for label, count in summary["label_counts"].items():
        lines.append(f"| `{label}` | {count} |")
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


def write_outputs(output_dir: Path, summary: dict[str, Any], ingestion: dict[str, Any]) -> None:
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validated_labels.jsonl", ingestion["completed_labels"])
    write_jsonl(output_dir / "binary_targets.jsonl", ingestion["binary_targets"])
    write_jsonl(output_dir / "multiclass_targets.jsonl", ingestion["multiclass_targets"])
    write_jsonl(output_dir / "ingestion_errors.jsonl", ingestion["errors"])
    write_json(
        output_dir / "schema.json",
        {
            "schema_version": "h002_independent_label_ingestion_schema_v0",
            "required_completion_fields": REQUIRED_COMPLETION_FIELDS,
            "forbidden_blind_header_fragments": FORBIDDEN_BLIND_HEADER_FRAGMENTS,
            "outputs": {
                "validated_labels.jsonl": "completed labels joined to internal key; contains hidden provenance for post-label analysis only",
                "binary_targets.jsonl": "usable positive/negative rows for train-only posterior diagnostics",
                "multiclass_targets.jsonl": "all completed labels including exclude/multiclass-only labels",
                "ingestion_errors.jsonl": "schema and label validation errors",
            },
        },
    )
    write_report(output_dir / "report.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    completed_sheet = as_abs(args.completed_sheet)
    internal_key = as_abs(args.internal_key)
    protocol_path = as_abs(args.protocol)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    fieldnames, completed_rows = read_tsv(completed_sheet)
    header_errors = validate_headers(fieldnames)
    internal_rows = read_jsonl(internal_key)
    protocol = read_json(protocol_path)
    ingestion = build_ingestion(completed_rows, internal_rows, protocol)
    ingestion["errors"] = header_errors + ingestion["errors"]

    label_counts = dict(Counter(row["relation_validity_label"] for row in ingestion["completed_labels"]))
    if ingestion["errors"]:
        status = "independent_label_ingestion_errors"
        decision = (
            "Independent label ingestion found schema or label errors. Fix completed "
            "blind sheets before materializing posterior targets."
        )
    elif not ingestion["completed_labels"]:
        status = "independent_label_ingestion_waiting_for_completed_labels"
        decision = (
            "Ingestion protocol is ready, but the blind sheet has no completed labels. "
            "Fill rank-hidden labels before running residual/gated combiner diagnostics."
        )
    elif not ingestion["binary_targets"]:
        status = "independent_label_ingestion_no_binary_targets"
        decision = (
            "Completed labels were ingested, but none map to binary posterior targets. "
            "Use multiclass analysis or collect binary-usable labels."
        )
    else:
        status = "independent_label_targets_ready"
        decision = (
            "Independent labels are ingested and binary targets are available for "
            "train-only residual/gated combiner diagnostics."
        )

    summary = {
        "schema_version": "h002_independent_label_ingestion_summary_v0",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "completed_sheet": rel_path(completed_sheet),
            "internal_key": rel_path(internal_key),
            "protocol": rel_path(protocol_path),
        },
        "output_dir": rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "hidden_fields_used_as_deployable_features": False,
        },
        "counts": {
            "sheet_rows": len(completed_rows),
            "internal_key_rows": len(internal_rows),
            "completed_label_rows": len(ingestion["completed_labels"]),
            "binary_target_rows": len(ingestion["binary_targets"]),
            "multiclass_target_rows": len(ingestion["multiclass_targets"]),
            "errors": len(ingestion["errors"]),
        },
        "label_counts": label_counts,
        "decision": decision,
    }
    write_outputs(output_dir, summary, ingestion)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        f"status={summary['status']} completed={summary['counts']['completed_label_rows']} "
        f"binary={summary['counts']['binary_target_rows']} errors={summary['counts']['errors']} "
        f"validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
