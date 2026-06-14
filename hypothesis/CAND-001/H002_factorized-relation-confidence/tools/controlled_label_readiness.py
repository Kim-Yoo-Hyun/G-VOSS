#!/usr/bin/env python3
"""Validate readiness of H002 controlled review labels."""

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
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_TARGET_DIR = RGA_ROOT / "controlled_label_target"
DEFAULT_PROTOCOL = DEFAULT_TARGET_DIR / "protocol.json"
DEFAULT_MINED_SHEET = DEFAULT_TARGET_DIR / "mined_controlled_sheet.tsv"
DEFAULT_COMBINED_SHEET = DEFAULT_TARGET_DIR / "combined_review_sheet.tsv"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "controlled_label_readiness"

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
REQUIRED_FIELDS = [
    "reviewer_id",
    "review_round",
    "object_pair_valid",
    "predicate_visually_plausible",
    "geometry_witness_correct",
    "relation_informative",
    "relation_trivial_or_dense",
    "final_controlled_label",
    "confidence",
]
ALLOWED_YNU = {"yes", "no", "uncertain"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
FINAL_LABEL_TARGET = {
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
    parser.add_argument("--mined-sheet", type=Path, default=DEFAULT_MINED_SHEET)
    parser.add_argument("--combined-sheet", type=Path, default=DEFAULT_COMBINED_SHEET)
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


def read_tsv(path: Path) -> list[dict[str, str]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"{path}: missing TSV header")
        return [dict(row) for row in reader]


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


def row_is_started(row: dict[str, str]) -> bool:
    return any(filled(row.get(field)) for field in REQUIRED_FIELDS + ["notes"])


def validate_sheet(rows: list[dict[str, str]], sheet_name: str) -> dict[str, Any]:
    completed_rows = 0
    started_rows = 0
    missing_required = []
    invalid_values = []
    binary_targets = []
    reviewers = Counter()
    final_counts = Counter()
    target_counts = Counter()
    rank_band_counts = Counter()
    target_by_rank = defaultdict(Counter)
    stratum_counts = Counter()
    target_by_stratum = defaultdict(Counter)

    for index, row in enumerate(rows, start=1):
        if row_is_started(row):
            started_rows += 1
        missing = [field for field in REQUIRED_FIELDS if not filled(row.get(field))]
        if missing:
            missing_required.append(
                {
                    "row_index": index,
                    "review_id": row.get("review_id"),
                    "missing_fields": missing,
                }
            )
        for field in YNU_FIELDS:
            value = (row.get(field) or "").strip()
            if value and value not in ALLOWED_YNU:
                invalid_values.append(
                    {
                        "row_index": index,
                        "review_id": row.get("review_id"),
                        "field": field,
                        "value": value,
                    }
                )
        confidence = (row.get("confidence") or "").strip()
        if confidence and confidence not in ALLOWED_CONFIDENCE:
            invalid_values.append(
                {
                    "row_index": index,
                    "review_id": row.get("review_id"),
                    "field": "confidence",
                    "value": confidence,
                }
            )
        final_label = (row.get("final_controlled_label") or "").strip()
        if final_label:
            if final_label not in FINAL_LABEL_TARGET:
                invalid_values.append(
                    {
                        "row_index": index,
                        "review_id": row.get("review_id"),
                        "field": "final_controlled_label",
                        "value": final_label,
                    }
                )
            else:
                final_counts[final_label] += 1
        review_round = (row.get("review_round") or "").strip()
        if review_round:
            try:
                int(review_round)
            except ValueError:
                invalid_values.append(
                    {
                        "row_index": index,
                        "review_id": row.get("review_id"),
                        "field": "review_round",
                        "value": review_round,
                    }
                )
        reviewer = (row.get("reviewer_id") or "").strip()
        if reviewer:
            reviewers[reviewer] += 1

        row_invalid = any(err["row_index"] == index for err in invalid_values)
        complete = not missing and not row_invalid
        if complete:
            completed_rows += 1
        rank_band = row.get("rank_band") or "missing"
        stratum = row.get("proposed_review_stratum") or "missing"
        rank_band_counts[rank_band] += 1
        stratum_counts[stratum] += 1
        if final_label in FINAL_LABEL_TARGET:
            target = FINAL_LABEL_TARGET[final_label]
            if target is not None:
                target_key = str(target)
                target_counts[target_key] += 1
                target_by_rank[rank_band][target_key] += 1
                target_by_stratum[stratum][target_key] += 1
                binary_targets.append(
                    {
                        "schema_version": "h002_controlled_binary_target_v0",
                        "sheet_name": sheet_name,
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
                        "rank_band": rank_band,
                        "geometry_status": row.get("geometry_status"),
                        "proposed_review_stratum": stratum,
                        "final_controlled_label": final_label,
                        "posterior_target": target,
                        "reviewer_id": reviewer,
                        "confidence": confidence,
                        "allowed_use": "train-only controlled posterior validation after readiness gate",
                    }
                )

    per_class_values = [target_counts.get("0", 0), target_counts.get("1", 0)]
    usable_binary_rows = len(binary_targets)
    per_class_min = min(per_class_values) if all(value > 0 for value in per_class_values) else 0
    hypothesis_ready = (
        completed_rows == len(rows)
        and not invalid_values
        and usable_binary_rows >= 60
        and per_class_min >= 20
    )
    if usable_binary_rows == 0:
        status = "not_ready_no_filled_labels"
    elif not hypothesis_ready:
        status = "not_ready_incomplete_or_insufficient"
    else:
        status = "ready_for_train_only_controlled_posterior_smoke"
    return {
        "sheet_name": sheet_name,
        "status": status,
        "rows": len(rows),
        "started_rows": started_rows,
        "completed_rows": completed_rows,
        "reviewers": dict(sorted(reviewers.items())),
        "final_label_counts": dict(sorted(final_counts.items())),
        "posterior_target_counts": dict(sorted(target_counts.items())),
        "usable_binary_rows": usable_binary_rows,
        "per_class_min": per_class_min,
        "rank_band_counts": dict(sorted(rank_band_counts.items())),
        "stratum_counts": dict(sorted(stratum_counts.items())),
        "target_by_rank_band": {
            key: dict(sorted(value.items())) for key, value in sorted(target_by_rank.items())
        },
        "target_by_stratum": {
            key: dict(sorted(value.items())) for key, value in sorted(target_by_stratum.items())
        },
        "missing_required_count": len(missing_required),
        "invalid_value_count": len(invalid_values),
        "missing_required_examples": missing_required[:10],
        "invalid_value_examples": invalid_values[:10],
        "hypothesis_stage_minimum_met": hypothesis_ready,
        "binary_targets": binary_targets,
    }


def strip_targets(result: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    copy = dict(result)
    targets = copy.pop("binary_targets")
    return copy, targets


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Controlled Label Readiness",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only readiness check.",
        "- No validation/test rows are used.",
        "- Proposed strata are not labels.",
        "- Posterior fitting remains blocked until final labels are filled.",
        "",
        "## Sheet Status",
        "",
        "| Sheet | Status | Rows | Started | Completed | Binary rows | Per-class min |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, result in summary["sheets"].items():
        lines.append(
            f"| `{name}` | `{result['status']}` | {result['rows']} | {result['started_rows']} | "
            f"{result['completed_rows']} | {result['usable_binary_rows']} | {result['per_class_min']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"Overall status: `{summary['status']}`",
            "",
        ]
    )
    if summary["status"] == "not_ready_no_filled_labels":
        lines.append("No controlled final labels are filled yet. Continue with review, not model fitting.")
    else:
        lines.append("See summary.json for missing fields, invalid values, and binary target counts.")
    lines.extend(["", "Next gate: `controlled_posterior_smoke` only after readiness passes.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol = read_json(args.protocol)
    mined_rows = read_tsv(args.mined_sheet)
    combined_rows = read_tsv(args.combined_sheet)
    mined_result, mined_targets = strip_targets(validate_sheet(mined_rows, "mined_controlled"))
    combined_result, combined_targets = strip_targets(validate_sheet(combined_rows, "combined_review"))
    created_at = datetime.now(timezone.utc).isoformat()
    paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "mined_binary_targets": output_dir / "mined_binary_targets.jsonl",
        "combined_binary_targets": output_dir / "combined_binary_targets.jsonl",
    }
    sheet_results = {
        "mined_controlled": mined_result,
        "combined_review": combined_result,
    }
    statuses = {result["status"] for result in sheet_results.values()}
    if statuses == {"not_ready_no_filled_labels"}:
        status = "not_ready_no_filled_labels"
    elif any(result["hypothesis_stage_minimum_met"] for result in sheet_results.values()):
        status = "ready_for_train_only_controlled_posterior_smoke"
    else:
        status = "not_ready_incomplete_or_insufficient"
    summary = {
        "schema_version": "h002_controlled_label_readiness_summary_v0",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "protocol": rel_path(args.protocol),
            "mined_sheet": rel_path(args.mined_sheet),
            "combined_sheet": rel_path(args.combined_sheet),
        },
        "output_paths": {key: rel_path(path) for key, path in paths.items()},
        "sheets": sheet_results,
        "target_minimum": {
            "usable_binary_rows_min": 60,
            "per_class_min": 20,
            "human_or_independent_labels_required": True,
            "codex_ver_sufficient": False,
        },
        "protocol_boundary": protocol.get("claim_boundary", {}),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "paper_result": False,
            "posterior_claim_allowed": False,
            "vmv_model_input_allowed": False,
        },
        "next_gate": (
            "controlled_posterior_smoke"
            if status == "ready_for_train_only_controlled_posterior_smoke"
            else "fill_controlled_review_labels"
        ),
    }
    write_jsonl(paths["mined_binary_targets"], mined_targets)
    write_jsonl(paths["combined_binary_targets"], combined_targets)
    write_json(paths["summary"], summary)
    write_report(paths["report"], summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    mined = summary["sheets"]["mined_controlled"]
    combined = summary["sheets"]["combined_review"]
    print(
        f"status={summary['status']} "
        f"mined_completed={mined['completed_rows']}/{mined['rows']} "
        f"combined_completed={combined['completed_rows']}/{combined['rows']} "
        f"mined_binary={mined['usable_binary_rows']} "
        f"combined_binary={combined['usable_binary_rows']} "
        f"validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
