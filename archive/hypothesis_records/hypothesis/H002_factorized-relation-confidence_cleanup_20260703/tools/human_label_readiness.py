#!/usr/bin/env python3
"""Validate H002 strict review label readiness for posterior plumbing smoke."""

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
DEFAULT_PROTOCOL_DIR = RGA_ROOT / "human_confirmation_protocol"
DEFAULT_PROTOCOL = DEFAULT_PROTOCOL_DIR / "protocol.json"
DEFAULT_SHEET = DEFAULT_PROTOCOL_DIR / "strict_review_sheet_codex_ver.tsv"
DEFAULT_BINARY_TARGETS = DEFAULT_PROTOCOL_DIR / "strict_codex_ver_binary_targets.jsonl"
DEFAULT_SUMMARY = DEFAULT_PROTOCOL_DIR / "codex_ver_readiness_summary.json"
DEFAULT_REPORT = DEFAULT_PROTOCOL_DIR / "codex_ver_readiness_report.md"

YES_NO_UNCERTAIN_FIELDS = [
    "object_pair_valid",
    "predicate_visually_plausible",
    "geometry_witness_correct",
    "relation_informative",
    "relation_trivial_or_dense",
    "annotation_missing_or_sparse",
    "ontology_or_granularity_issue",
    "segmentation_or_instance_issue",
]
ALLOWED_YNU = {"yes", "no", "uncertain"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--sheet", type=Path, default=DEFAULT_SHEET)
    parser.add_argument("--output-targets", type=Path, default=DEFAULT_BINARY_TARGETS)
    parser.add_argument("--output-summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output-report", type=Path, default=DEFAULT_REPORT)
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


def read_tsv(path: Path) -> list[dict[str, str]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"{path}: missing TSV header")
        return [dict(row) for row in reader]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path = as_abs(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path = as_abs(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def validate_rows(rows: list[dict[str, str]], protocol: dict[str, Any]) -> dict[str, Any]:
    final_policy = protocol["final_label_policy"]
    required = protocol["acceptance_criteria"]["hypothesis_stage_minimum"]["required_fields"]
    min_rows = int(protocol["acceptance_criteria"]["hypothesis_stage_minimum"]["usable_binary_rows_min"])
    min_per_class = int(protocol["acceptance_criteria"]["hypothesis_stage_minimum"]["per_class_min_after_exclusion"])

    missing_required: list[dict[str, Any]] = []
    invalid_values: list[dict[str, Any]] = []
    binary_targets: list[dict[str, Any]] = []
    completed_rows = 0
    reviewers = set()
    final_counts = Counter()
    target_counts = Counter()
    reviewer_counts = Counter()
    target_by_reviewer: dict[str, Counter] = defaultdict(Counter)

    for index, row in enumerate(rows, start=1):
        row_errors = []
        reviewer = row.get("reviewer_id", "").strip()
        review_round = row.get("review_round", "").strip()
        if not reviewer:
            row_errors.append("reviewer_id")
        else:
            reviewers.add(reviewer)
            reviewer_counts[reviewer] += 1
        if not review_round:
            row_errors.append("review_round")
        else:
            try:
                int(review_round)
            except ValueError:
                invalid_values.append(
                    {
                        "row_index": index,
                        "prediction_id": row.get("prediction_id"),
                        "field": "review_round",
                        "value": review_round,
                    }
                )
        for field in required:
            if not row.get(field, "").strip():
                row_errors.append(field)
        if row_errors:
            missing_required.append(
                {
                    "row_index": index,
                    "prediction_id": row.get("prediction_id"),
                    "missing_fields": row_errors,
                }
            )
        for field in YES_NO_UNCERTAIN_FIELDS:
            value = row.get(field, "").strip()
            if value and value not in ALLOWED_YNU:
                invalid_values.append(
                    {
                        "row_index": index,
                        "prediction_id": row.get("prediction_id"),
                        "field": field,
                        "value": value,
                    }
                )
        final_label = row.get("final_human_label", "").strip()
        if final_label:
            if final_label not in final_policy:
                invalid_values.append(
                    {
                        "row_index": index,
                        "prediction_id": row.get("prediction_id"),
                        "field": "final_human_label",
                        "value": final_label,
                    }
                )
            else:
                final_counts[final_label] += 1
        confidence = row.get("confidence", "").strip()
        if confidence and confidence not in ALLOWED_CONFIDENCE:
            invalid_values.append(
                {
                    "row_index": index,
                    "prediction_id": row.get("prediction_id"),
                    "field": "confidence",
                    "value": confidence,
                }
            )

        complete = not row_errors and not any(
            err["row_index"] == index for err in invalid_values
        )
        if complete:
            completed_rows += 1
        if final_label in final_policy:
            target = final_policy[final_label]["posterior_target"]
            if target is not None:
                target_key = str(target)
                target_counts[target_key] += 1
                target_by_reviewer[reviewer][target_key] += 1
                binary_targets.append(
                    {
                        "schema_version": "h002_strict_review_binary_target_v0",
                        "prediction_id": row["prediction_id"],
                        "scan_id": row["scan_id"],
                        "subject_id": row["subject_id"],
                        "subject_label": row["subject_label"],
                        "predicate_label": row["predicate_label"],
                        "object_id": row["object_id"],
                        "object_label": row["object_label"],
                        "working_label": row["working_label"],
                        "final_human_label": final_label,
                        "posterior_target": target,
                        "confidence": confidence,
                        "reviewer_id": reviewer,
                        "label_source": (
                            "codex_ver_not_human_confirmed"
                            if reviewer == "(codex_ver)"
                            else "human_or_external_reviewer"
                        ),
                        "not_human_confirmed": reviewer == "(codex_ver)",
                        "allowed_use": (
                            "train-only posterior plumbing smoke"
                            if reviewer == "(codex_ver)"
                            else "train-only label-quality gate; still no validation/test claim"
                        ),
                    }
                )

    usable = len(binary_targets)
    per_class_values = [target_counts.get("0", 0), target_counts.get("1", 0)]
    strict_rows_complete = completed_rows == len(rows) and len(rows) > 0
    required_values_valid = not missing_required and not invalid_values
    hypothesis_minimum_met = (
        strict_rows_complete
        and required_values_valid
        and len(reviewers) >= 1
        and usable >= min_rows
        and min(per_class_values) >= min_per_class
    )
    only_codex = reviewers == {"(codex_ver)"}
    status = (
        "ready_for_train_only_codex_plumbing_smoke"
        if hypothesis_minimum_met and only_codex
        else "ready_for_train_only_human_label_smoke"
        if hypothesis_minimum_met
        else "not_ready"
    )
    return {
        "status": status,
        "rows": len(rows),
        "completed_rows": completed_rows,
        "reviewers": sorted(reviewers),
        "reviewer_counts": dict(sorted(reviewer_counts.items())),
        "final_label_counts": dict(sorted(final_counts.items())),
        "posterior_target_counts": dict(sorted(target_counts.items())),
        "target_by_reviewer": {
            reviewer: dict(sorted(counter.items()))
            for reviewer, counter in sorted(target_by_reviewer.items())
        },
        "usable_binary_rows": usable,
        "per_class_min": min(per_class_values) if per_class_values else 0,
        "missing_required_count": len(missing_required),
        "invalid_value_count": len(invalid_values),
        "missing_required_examples": missing_required[:10],
        "invalid_value_examples": invalid_values[:10],
        "hypothesis_stage_minimum_met": hypothesis_minimum_met,
        "paper_evidence_minimum_met": False,
        "only_codex_ver": only_codex,
        "binary_targets": binary_targets,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    validation = summary["validation"]
    lines = [
        "# H002 Human Label Readiness",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{validation['status']}`",
        "",
        "## Boundary",
        "",
        "- Split: train-only.",
        "- Validation/test rows: not used.",
        "- Codex labels are not human-confirmed labels.",
        "- Paper evidence and posterior advantage claims remain blocked.",
        "",
        "## Counts",
        "",
        "| Item | Value |",
        "| --- | ---: |",
        f"| strict rows | {validation['rows']} |",
        f"| completed rows | {validation['completed_rows']} |",
        f"| usable binary rows | {validation['usable_binary_rows']} |",
        f"| per-class minimum | {validation['per_class_min']} |",
        f"| missing required fields | {validation['missing_required_count']} |",
        f"| invalid values | {validation['invalid_value_count']} |",
        "",
        "Final labels:",
        "",
        "```json",
        json.dumps(validation["final_label_counts"], indent=2, sort_keys=True, ensure_ascii=False),
        "```",
        "",
        "Posterior targets:",
        "",
        "```json",
        json.dumps(validation["posterior_target_counts"], indent=2, sort_keys=True, ensure_ascii=False),
        "```",
        "",
        "## Decision",
        "",
    ]
    if validation["status"] == "ready_for_train_only_codex_plumbing_smoke":
        lines.extend(
            [
                "The filled strict sheet passes the hypothesis-stage structural gate for a",
                "`codex_ver` train-only plumbing smoke. It does not pass the paper-evidence",
                "minimum because there is only one Codex bootstrap label source and no",
                "independent human agreement.",
            ]
        )
    elif validation["hypothesis_stage_minimum_met"]:
        lines.append("The filled strict sheet passes the hypothesis-stage structural gate.")
    else:
        lines.append("The filled strict sheet does not pass the hypothesis-stage gate.")
    lines.extend(
        [
            "",
            "Next gate: `33_codex_label_smoke.md` if using `(codex_ver)` labels only,",
            "or independent human review if the goal is paper-level evidence.",
            "",
        ]
    )
    as_abs(path).write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    protocol = read_json(args.protocol)
    rows = read_tsv(args.sheet)
    validation = validate_rows(rows, protocol)
    binary_targets = validation.pop("binary_targets")
    created_at = datetime.now(timezone.utc).isoformat()
    summary = {
        "schema_version": "h002_human_label_readiness_summary_v0",
        "created_at": created_at,
        "input_paths": {
            "protocol": rel_path(args.protocol),
            "sheet": rel_path(args.sheet),
        },
        "output_paths": {
            "binary_targets": rel_path(args.output_targets),
            "summary": rel_path(args.output_summary),
            "report": rel_path(args.output_report),
        },
        "validation": validation,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "paper_result": False,
            "posterior_claim_allowed": False,
            "human_confirmed": not validation["only_codex_ver"],
        },
    }
    write_jsonl(args.output_targets, binary_targets)
    write_json(args.output_summary, summary)
    write_report(args.output_report, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    validation = summary["validation"]
    print(
        f"status={validation['status']} rows={validation['rows']} "
        f"usable_binary={validation['usable_binary_rows']} "
        f"targets={validation['posterior_target_counts']} "
        f"validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
