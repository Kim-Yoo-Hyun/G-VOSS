#!/usr/bin/env python3
"""Validate full-train H002 controlled label readiness."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
MINING_ROOT = (
    H002_ROOT
    / "artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_mining"
)
DEFAULT_PROTOCOL = MINING_ROOT / "protocol.json"
DEFAULT_CANDIDATE_SHEET = MINING_ROOT / "candidate_sheet.tsv"
DEFAULT_CANDIDATE_POOL = MINING_ROOT / "candidate_pool.jsonl"
DEFAULT_MINING_SUMMARY = MINING_ROOT / "summary.json"
DEFAULT_OUTPUT_DIR = (
    H002_ROOT
    / "artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_readiness"
)

YNU_FIELDS = [
    "object_pair_valid",
    "predicate_visually_plausible",
    "geometry_witness_correct",
    "relation_informative",
    "relation_trivial_or_dense",
    "annotation_missing_or_sparse",
    "ontology_or_granularity_issue",
    "segmentation_or_instance_issue",
]
REQUIRED_REVIEW_FIELDS = [
    "reviewer_id",
    "review_round",
    "object_pair_valid",
    "predicate_visually_plausible",
    "geometry_witness_correct",
    "relation_informative",
    "relation_trivial_or_dense",
    "final_controlled_label",
    "failure_taxonomy_label",
    "confidence",
]
REVIEW_FIELDS = [
    *REQUIRED_REVIEW_FIELDS,
    "annotation_missing_or_sparse",
    "ontology_or_granularity_issue",
    "segmentation_or_instance_issue",
    "notes",
]
REQUIRED_SCHEMA_FIELDS = [
    "review_id",
    "queue_kind",
    "candidate_axis",
    "proposed_audit_role",
    "prediction_id",
    "scan_id",
    "subgraph_id",
    "subject_id",
    "subject_label",
    "predicate_label",
    "predicate_family",
    "object_id",
    "object_label",
    "semantic_rank",
    "rank_band",
    "semantic_score_norm",
    "geometry_status",
    "p_geom_valid",
    "label_match_status",
    *REQUIRED_REVIEW_FIELDS,
]
ALLOWED_YNU = {"yes", "no", "uncertain"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
DEFAULT_FINAL_LABEL_TARGET = {
    "reliable_promote": 1,
    "unreliable_dense_noise": 0,
    "relabel_only": None,
    "invalid_pair": None,
    "geometry_artifact": None,
    "abstain_uncertain": None,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--candidate-sheet", type=Path, default=DEFAULT_CANDIDATE_SHEET)
    parser.add_argument("--candidate-pool", type=Path, default=DEFAULT_CANDIDATE_POOL)
    parser.add_argument("--mining-summary", type=Path, default=DEFAULT_MINING_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--min-binary", type=int, default=150)
    parser.add_argument("--min-per-class", type=int, default=50)
    parser.add_argument("--min-per-queue", type=int, default=50)
    parser.add_argument("--min-families-with-both-classes", type=int, default=2)
    parser.add_argument("--min-family-minority", type=int, default=15)
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
        if reader.fieldnames is None:
            raise ValueError(f"{path}: missing TSV header")
        return list(reader.fieldnames), [dict(row) for row in reader]


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


def filled(value: str | None) -> bool:
    return bool((value or "").strip())


def safe_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def normalize_binary_mapping(protocol: dict[str, Any]) -> dict[str, int | None]:
    mapping = protocol.get("binary_target_mapping")
    if not isinstance(mapping, dict):
        return dict(DEFAULT_FINAL_LABEL_TARGET)
    normalized = {}
    for key, value in mapping.items():
        if value is None:
            normalized[str(key)] = None
        else:
            normalized[str(key)] = int(value)
    return normalized


def row_started(row: dict[str, str]) -> bool:
    return any(filled(row.get(field)) for field in REVIEW_FIELDS)


def validate_row_values(
    row: dict[str, str],
    index: int,
    final_label_target: dict[str, int | None],
    allowed_failure_labels: set[str],
) -> list[dict[str, Any]]:
    invalid = []
    for field in YNU_FIELDS:
        value = (row.get(field) or "").strip()
        if value and value not in ALLOWED_YNU:
            invalid.append(
                {
                    "row_index": index,
                    "review_id": row.get("review_id"),
                    "field": field,
                    "value": value,
                    "allowed": sorted(ALLOWED_YNU),
                }
            )
    confidence = (row.get("confidence") or "").strip()
    if confidence and confidence not in ALLOWED_CONFIDENCE:
        invalid.append(
            {
                "row_index": index,
                "review_id": row.get("review_id"),
                "field": "confidence",
                "value": confidence,
                "allowed": sorted(ALLOWED_CONFIDENCE),
            }
        )
    final_label = (row.get("final_controlled_label") or "").strip()
    if final_label and final_label not in final_label_target:
        invalid.append(
            {
                "row_index": index,
                "review_id": row.get("review_id"),
                "field": "final_controlled_label",
                "value": final_label,
                "allowed": sorted(final_label_target),
            }
        )
    taxonomy = (row.get("failure_taxonomy_label") or "").strip()
    if taxonomy and taxonomy not in allowed_failure_labels:
        invalid.append(
            {
                "row_index": index,
                "review_id": row.get("review_id"),
                "field": "failure_taxonomy_label",
                "value": taxonomy,
                "allowed": sorted(allowed_failure_labels),
            }
        )
    review_round = (row.get("review_round") or "").strip()
    if review_round and safe_int(review_round) is None:
        invalid.append(
            {
                "row_index": index,
                "review_id": row.get("review_id"),
                "field": "review_round",
                "value": review_round,
                "allowed": "integer",
            }
        )
    return invalid


def binary_target_row(row: dict[str, str], target: int) -> dict[str, Any]:
    return {
        "schema_version": "h002_full_train_binary_target_v0",
        "source_scope": "open3dsg_train_full",
        "split_boundary": "train full only",
        "review_id": row.get("review_id"),
        "prediction_id": row.get("prediction_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "queue_kind": row.get("queue_kind"),
        "candidate_axis": row.get("candidate_axis"),
        "proposed_audit_role": row.get("proposed_audit_role"),
        "rank_band": row.get("rank_band"),
        "semantic_rank": safe_int(row.get("semantic_rank")),
        "semantic_score_norm": row.get("semantic_score_norm"),
        "geometry_status": row.get("geometry_status"),
        "p_geom_valid": row.get("p_geom_valid"),
        "label_match_status": row.get("label_match_status"),
        "final_controlled_label": row.get("final_controlled_label"),
        "failure_taxonomy_label": row.get("failure_taxonomy_label"),
        "posterior_target": target,
        "reviewer_id": row.get("reviewer_id"),
        "confidence": row.get("confidence"),
        "allowed_use": "train-only H002 posterior smoke after full-train readiness gate",
    }


def multiclass_review_row(row: dict[str, str]) -> dict[str, Any]:
    return {
        "schema_version": "h002_full_train_review_multiclass_v0",
        "review_id": row.get("review_id"),
        "prediction_id": row.get("prediction_id"),
        "scan_id": row.get("scan_id"),
        "predicate_family": row.get("predicate_family"),
        "predicate_label": row.get("predicate_label"),
        "queue_kind": row.get("queue_kind"),
        "rank_band": row.get("rank_band"),
        "label_match_status": row.get("label_match_status"),
        "final_controlled_label": row.get("final_controlled_label"),
        "failure_taxonomy_label": row.get("failure_taxonomy_label"),
        "reviewer_id": row.get("reviewer_id"),
        "confidence": row.get("confidence"),
        "allowed_use": "train-only taxonomy analysis, not a held-out paper result",
    }


def validate_sheet(
    fieldnames: list[str],
    rows: list[dict[str, str]],
    protocol: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    final_label_target = normalize_binary_mapping(protocol)
    allowed_failure_labels = set(protocol.get("allowed_failure_taxonomy_label") or [])
    missing_columns = [field for field in REQUIRED_SCHEMA_FIELDS if field not in fieldnames]
    duplicate_review_ids = []
    duplicate_prediction_ids = []
    seen_review_ids = set()
    seen_prediction_ids = set()
    started_rows = 0
    completed_rows = 0
    incomplete_started_rows = 0
    missing_required = []
    invalid_values = []
    binary_targets = []
    multiclass_rows = []
    final_label_counts = Counter()
    taxonomy_counts = Counter()
    target_counts = Counter()
    reviewers = Counter()
    by_queue = Counter()
    by_family = Counter()
    by_role = Counter()
    by_rank = Counter()
    by_label_status = Counter()
    target_by_queue = defaultdict(Counter)
    target_by_family = defaultdict(Counter)
    target_by_rank = defaultdict(Counter)
    target_by_role = defaultdict(Counter)

    for index, row in enumerate(rows, start=1):
        review_id = row.get("review_id") or f"row_{index}"
        prediction_id = row.get("prediction_id") or f"row_{index}"
        if review_id in seen_review_ids:
            duplicate_review_ids.append(review_id)
        seen_review_ids.add(review_id)
        if prediction_id in seen_prediction_ids:
            duplicate_prediction_ids.append(prediction_id)
        seen_prediction_ids.add(prediction_id)

        queue_kind = row.get("queue_kind") or "missing"
        family = row.get("predicate_family") or "missing"
        role = row.get("proposed_audit_role") or "missing"
        rank_band = row.get("rank_band") or "missing"
        label_status = row.get("label_match_status") or "missing"
        by_queue[queue_kind] += 1
        by_family[family] += 1
        by_role[role] += 1
        by_rank[rank_band] += 1
        by_label_status[label_status] += 1

        started = row_started(row)
        if started:
            started_rows += 1
        missing = [field for field in REQUIRED_REVIEW_FIELDS if not filled(row.get(field))]
        row_invalid = validate_row_values(row, index, final_label_target, allowed_failure_labels)
        invalid_values.extend(row_invalid)
        if started and missing:
            incomplete_started_rows += 1
            missing_required.append(
                {
                    "row_index": index,
                    "review_id": review_id,
                    "missing_fields": missing,
                }
            )
        complete = started and not missing and not row_invalid
        if complete:
            completed_rows += 1
            final_label = (row.get("final_controlled_label") or "").strip()
            taxonomy = (row.get("failure_taxonomy_label") or "").strip()
            reviewer = (row.get("reviewer_id") or "").strip()
            final_label_counts[final_label] += 1
            taxonomy_counts[taxonomy] += 1
            reviewers[reviewer] += 1
            multiclass_rows.append(multiclass_review_row(row))
            target = final_label_target.get(final_label)
            if target is not None:
                target_key = str(target)
                target_counts[target_key] += 1
                target_by_queue[queue_kind][target_key] += 1
                target_by_family[family][target_key] += 1
                target_by_rank[rank_band][target_key] += 1
                target_by_role[role][target_key] += 1
                binary_targets.append(binary_target_row(row, int(target)))

    schema_errors = []
    if missing_columns:
        schema_errors.append({"error": "missing_columns", "columns": missing_columns})
    if duplicate_review_ids:
        schema_errors.append(
            {
                "error": "duplicate_review_ids",
                "count": len(duplicate_review_ids),
                "examples": sorted(set(duplicate_review_ids))[:10],
            }
        )
    if duplicate_prediction_ids:
        schema_errors.append(
            {
                "error": "duplicate_prediction_ids",
                "count": len(duplicate_prediction_ids),
                "examples": sorted(set(duplicate_prediction_ids))[:10],
            }
        )

    families_with_both_classes = []
    family_binary_minority_counts = {}
    for family, counts in sorted(target_by_family.items()):
        minority = min(counts.get("0", 0), counts.get("1", 0))
        family_binary_minority_counts[family] = minority
        if counts.get("0", 0) > 0 and counts.get("1", 0) > 0:
            families_with_both_classes.append(family)

    return (
        {
            "rows": len(rows),
            "started_rows": started_rows,
            "completed_rows": completed_rows,
            "blank_rows": len(rows) - started_rows,
            "incomplete_started_rows": incomplete_started_rows,
            "schema_error_count": len(schema_errors),
            "schema_errors": schema_errors,
            "missing_required_count": len(missing_required),
            "missing_required_examples": missing_required[:20],
            "invalid_value_count": len(invalid_values),
            "invalid_value_examples": invalid_values[:20],
            "reviewers": dict(sorted(reviewers.items())),
            "final_label_counts": dict(sorted(final_label_counts.items())),
            "failure_taxonomy_counts": dict(sorted(taxonomy_counts.items())),
            "posterior_target_counts": dict(sorted(target_counts.items())),
            "usable_binary_rows": len(binary_targets),
            "by_queue": dict(sorted(by_queue.items())),
            "by_family": dict(sorted(by_family.items())),
            "by_rank_band": dict(sorted(by_rank.items())),
            "by_label_match_status": dict(sorted(by_label_status.items())),
            "by_proposed_audit_role": dict(sorted(by_role.items())),
            "target_by_queue": {
                key: dict(sorted(value.items())) for key, value in sorted(target_by_queue.items())
            },
            "target_by_family": {
                key: dict(sorted(value.items())) for key, value in sorted(target_by_family.items())
            },
            "target_by_rank_band": {
                key: dict(sorted(value.items())) for key, value in sorted(target_by_rank.items())
            },
            "target_by_proposed_audit_role": {
                key: dict(sorted(value.items())) for key, value in sorted(target_by_role.items())
            },
            "families_with_both_binary_classes": families_with_both_classes,
            "family_binary_minority_counts": family_binary_minority_counts,
        },
        binary_targets,
        multiclass_rows,
        invalid_values,
    )


def readiness_gates(sheet: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    target_counts = sheet["posterior_target_counts"]
    by_queue = sheet["target_by_queue"]
    positive = int(target_counts.get("1", 0))
    negative = int(target_counts.get("0", 0))
    queue_min = min(
        int(by_queue.get("HL", {}).get("0", 0)) + int(by_queue.get("HL", {}).get("1", 0)),
        int(by_queue.get("LH", {}).get("0", 0)) + int(by_queue.get("LH", {}).get("1", 0)),
    )
    families_with_minority = [
        family
        for family, minority in sheet["family_binary_minority_counts"].items()
        if int(minority) >= args.min_family_minority
    ]
    gates = {
        "schema_valid": sheet["schema_error_count"] == 0,
        "no_invalid_values": sheet["invalid_value_count"] == 0,
        "no_incomplete_started_rows": sheet["incomplete_started_rows"] == 0,
        "usable_binary_rows_min": sheet["usable_binary_rows"] >= args.min_binary,
        "positive_min": positive >= args.min_per_class,
        "negative_min": negative >= args.min_per_class,
        "queue_min": queue_min >= args.min_per_queue,
        "families_with_both_classes_min": (
            len(sheet["families_with_both_binary_classes"])
            >= args.min_families_with_both_classes
        ),
        "family_minority_min": (
            len(families_with_minority)
            >= args.min_families_with_both_classes
        ),
    }
    gates["all_passed"] = all(gates.values())
    return gates


def status_from(sheet: dict[str, Any], gates: dict[str, Any]) -> str:
    if sheet["schema_error_count"] > 0:
        return "schema_error"
    if sheet["started_rows"] == 0 and sheet["usable_binary_rows"] == 0:
        return "not_ready_no_filled_labels"
    if sheet["invalid_value_count"] > 0:
        return "not_ready_invalid_values"
    if gates["all_passed"]:
        return "ready_for_train_only_full_posterior_smoke"
    return "not_ready_incomplete_or_insufficient"


def write_report(path: Path, summary: dict[str, Any]) -> None:
    sheet = summary["sheet"]
    gates = summary["readiness_gates"]
    lines = [
        "# H002 Full Train Controlled Label Readiness",
        "",
        f"Created: {summary['created_at']}",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Boundary",
        "",
        "- Split: train full only.",
        "- Validation/test rows used: false.",
        "- Proposed audit roles are not labels.",
        "- Blank labels are not converted into targets.",
        "- Posterior fitting remains blocked until readiness passes.",
        "",
        "## Sheet",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| rows | {sheet['rows']} |",
        f"| started rows | {sheet['started_rows']} |",
        f"| completed rows | {sheet['completed_rows']} |",
        f"| blank rows | {sheet['blank_rows']} |",
        f"| usable binary rows | {sheet['usable_binary_rows']} |",
        f"| invalid values | {sheet['invalid_value_count']} |",
        f"| incomplete started rows | {sheet['incomplete_started_rows']} |",
        "",
        "## Target Counts",
        "",
        "| Target | Rows |",
        "| --- | ---: |",
    ]
    for key, value in sheet["posterior_target_counts"].items():
        lines.append(f"| `{key}` | {value} |")
    if not sheet["posterior_target_counts"]:
        lines.append("| none | 0 |")
    lines.extend(
        [
            "",
            "## Readiness Gates",
            "",
            "| Gate | Passed |",
            "| --- | --- |",
        ]
    )
    for key, value in gates.items():
        if key == "all_passed":
            continue
        lines.append(f"| `{key}` | `{str(value).lower()}` |")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            "```text",
            summary["output_paths"]["summary"],
            summary["output_paths"]["report"],
            summary["output_paths"]["binary_targets"],
            summary["output_paths"]["multiclass_review_rows"],
            summary["output_paths"]["invalid_rows"],
            "```",
            "",
            "## Next Step",
            "",
            summary["next_gate"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol = read_json(args.protocol)
    mining_summary = read_json(args.mining_summary)
    candidate_pool = read_jsonl(args.candidate_pool)
    fieldnames, rows = read_tsv(args.candidate_sheet)
    sheet, binary_targets, multiclass_rows, invalid_rows = validate_sheet(
        fieldnames, rows, protocol
    )
    gates = readiness_gates(sheet, args)
    status = status_from(sheet, gates)

    paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "binary_targets": output_dir / "binary_targets.jsonl",
        "multiclass_review_rows": output_dir / "multiclass_review_rows.jsonl",
        "invalid_rows": output_dir / "invalid_rows.jsonl",
    }
    created_at = datetime.now(timezone.utc).isoformat()
    summary = {
        "schema_version": "h002_full_train_controlled_label_readiness_summary_v0",
        "status": status,
        "created_at": created_at,
        "validation_used": False,
        "test_used": False,
        "paper_result": False,
        "input_paths": {
            "protocol": rel_path(args.protocol),
            "candidate_sheet": rel_path(args.candidate_sheet),
            "candidate_pool": rel_path(args.candidate_pool),
            "mining_summary": rel_path(args.mining_summary),
        },
        "output_paths": {key: rel_path(path) for key, path in paths.items()},
        "candidate_consistency": {
            "sheet_rows": len(rows),
            "pool_rows": len(candidate_pool),
            "mining_summary_rows": mining_summary.get("selected", {}).get("rows"),
            "row_counts_match": (
                len(rows) == len(candidate_pool) == mining_summary.get("selected", {}).get("rows")
            ),
        },
        "target_minimum": {
            "usable_binary_rows_min": args.min_binary,
            "positive_rows_min": args.min_per_class,
            "negative_rows_min": args.min_per_class,
            "binary_rows_per_queue_min": args.min_per_queue,
            "families_with_both_classes_min": args.min_families_with_both_classes,
            "per_family_minority_min": args.min_family_minority,
            "human_or_independent_labels_required": True,
            "codex_ver_sufficient_for_paper_claim": False,
        },
        "sheet": sheet,
        "readiness_gates": gates,
        "boundary": {
            "split": "train_full_only",
            "validation_usage": False,
            "test_usage": False,
            "proposed_audit_role_is_label": False,
            "posterior_claim_allowed": False,
            "vmv_model_input_allowed": False,
        },
        "next_gate": (
            "full_train_posterior_smoke"
            if status == "ready_for_train_only_full_posterior_smoke"
            else "fill_full_train_controlled_labels"
        ),
    }
    write_jsonl(paths["binary_targets"], binary_targets)
    write_jsonl(paths["multiclass_review_rows"], multiclass_rows)
    write_jsonl(paths["invalid_rows"], invalid_rows)
    write_json(paths["summary"], summary)
    write_report(paths["report"], summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    sheet = summary["sheet"]
    print(
        "status={status} rows={rows} started={started} completed={completed} "
        "binary={binary} validation_used={validation_used}".format(
            status=summary["status"],
            rows=sheet["rows"],
            started=sheet["started_rows"],
            completed=sheet["completed_rows"],
            binary=sheet["usable_binary_rows"],
            validation_used=summary["validation_used"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
