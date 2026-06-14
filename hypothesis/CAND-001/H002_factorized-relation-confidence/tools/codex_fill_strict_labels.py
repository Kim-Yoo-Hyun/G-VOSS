#!/usr/bin/env python3
"""Fill H002 strict review labels with a clearly marked Codex bootstrap version."""

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
DEFAULT_PROTOCOL_DIR = RGA_ROOT / "human_confirmation_protocol"
DEFAULT_INPUT_SHEET = DEFAULT_PROTOCOL_DIR / "strict_review_sheet.tsv"
DEFAULT_INPUT_QUEUE = DEFAULT_PROTOCOL_DIR / "strict_review_queue.jsonl"
DEFAULT_OUTPUT_SHEET = DEFAULT_PROTOCOL_DIR / "strict_review_sheet_codex_ver.tsv"
DEFAULT_OUTPUT_LABELS = DEFAULT_PROTOCOL_DIR / "strict_codex_ver_labels.jsonl"
DEFAULT_OUTPUT_SUMMARY = DEFAULT_PROTOCOL_DIR / "codex_ver_summary.json"
DEFAULT_OUTPUT_REPORT = DEFAULT_PROTOCOL_DIR / "codex_ver_report.md"

REVIEWER_ID = "(codex_ver)"

FIELD_VALUES = {
    "true_underconfidence": {
        "object_pair_valid": "yes",
        "predicate_visually_plausible": "yes",
        "geometry_witness_correct": "yes",
        "relation_informative": "yes",
        "relation_trivial_or_dense": "no",
        "annotation_missing_or_sparse": "yes",
        "ontology_or_granularity_issue": "no",
        "segmentation_or_instance_issue": "uncertain",
        "final_human_label": "reliable_promote",
        "posterior_target": 1,
        "confidence": "medium",
        "note": (
            "codex_ver metadata-assisted bootstrap label; maps true_underconfidence "
            "to reliable_promote; not human-confirmed"
        ),
    },
    "dense_relation_noise": {
        "object_pair_valid": "yes",
        "predicate_visually_plausible": "yes",
        "geometry_witness_correct": "yes",
        "relation_informative": "no",
        "relation_trivial_or_dense": "yes",
        "annotation_missing_or_sparse": "no",
        "ontology_or_granularity_issue": "no",
        "segmentation_or_instance_issue": "uncertain",
        "final_human_label": "unreliable_dense_noise",
        "posterior_target": 0,
        "confidence": "medium",
        "note": (
            "codex_ver metadata-assisted bootstrap label; maps dense_relation_noise "
            "to unreliable_dense_noise; not human-confirmed"
        ),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-sheet", type=Path, default=DEFAULT_INPUT_SHEET)
    parser.add_argument("--input-queue", type=Path, default=DEFAULT_INPUT_QUEUE)
    parser.add_argument("--output-sheet", type=Path, default=DEFAULT_OUTPUT_SHEET)
    parser.add_argument("--output-labels", type=Path, default=DEFAULT_OUTPUT_LABELS)
    parser.add_argument("--output-summary", type=Path, default=DEFAULT_OUTPUT_SUMMARY)
    parser.add_argument("--output-report", type=Path, default=DEFAULT_OUTPUT_REPORT)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
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


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = [dict(row) for row in reader]
        if reader.fieldnames is None:
            raise ValueError(f"{path}: missing TSV header")
        return list(reader.fieldnames), rows


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path = as_abs(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


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


def fill_row(row: dict[str, str], queue_row: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    working_label = row["working_label"]
    if working_label not in FIELD_VALUES:
        raise ValueError(f"unsupported working_label for Codex fill: {working_label}")
    spec = FIELD_VALUES[working_label]
    filled = dict(row)
    filled.update(
        {
            "reviewer_id": REVIEWER_ID,
            "review_round": "1",
            "object_pair_valid": spec["object_pair_valid"],
            "predicate_visually_plausible": spec["predicate_visually_plausible"],
            "geometry_witness_correct": spec["geometry_witness_correct"],
            "relation_informative": spec["relation_informative"],
            "relation_trivial_or_dense": spec["relation_trivial_or_dense"],
            "annotation_missing_or_sparse": spec["annotation_missing_or_sparse"],
            "ontology_or_granularity_issue": spec["ontology_or_granularity_issue"],
            "segmentation_or_instance_issue": spec["segmentation_or_instance_issue"],
            "final_human_label": spec["final_human_label"],
            "confidence": spec["confidence"],
            "notes": (
                f"{spec['note']}; geometry_status={queue_row.get('geometry_status')}; "
                f"label_status={queue_row.get('label_match_status', 'not_in_queue')}; "
                f"contact_sheet={row.get('contact_sheet')}"
            ),
        }
    )
    label_row = {
        "schema_version": "h002_codex_ver_strict_label_v0",
        "label_source": "codex_ver_metadata_assisted_bootstrap",
        "not_human_confirmed": True,
        "reviewer_id": REVIEWER_ID,
        "review_round": 1,
        "prediction_id": row["prediction_id"],
        "scan_id": row["scan_id"],
        "subject_id": row["subject_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "object_id": row["object_id"],
        "object_label": row["object_label"],
        "working_label": working_label,
        "machine_y": int(row["machine_y"]),
        "final_human_label": spec["final_human_label"],
        "posterior_target": spec["posterior_target"],
        "confidence": spec["confidence"],
        "review_fields": {
            key: filled[key]
            for key in [
                "object_pair_valid",
                "predicate_visually_plausible",
                "geometry_witness_correct",
                "relation_informative",
                "relation_trivial_or_dense",
                "annotation_missing_or_sparse",
                "ontology_or_granularity_issue",
                "segmentation_or_instance_issue",
            ]
        },
        "contact_sheet": row.get("contact_sheet"),
        "mesh_obj": row.get("mesh_obj"),
        "notes": filled["notes"],
    }
    return filled, label_row


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Codex Ver Strict Labels",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- These labels are filled by Codex as `(codex_ver)`.",
        "- They are metadata-assisted bootstrap labels, not human-confirmed labels.",
        "- They may be used for train-only posterior plumbing smoke.",
        "- They must not be used as paper evidence or reviewer-agreement evidence.",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| rows | {summary['counts']['rows']} |",
        f"| reliable_promote | {summary['counts']['final_label_counts'].get('reliable_promote', 0)} |",
        f"| unreliable_dense_noise | {summary['counts']['final_label_counts'].get('unreliable_dense_noise', 0)} |",
        f"| positive posterior targets | {summary['counts']['posterior_target_counts'].get('1', 0)} |",
        f"| negative posterior targets | {summary['counts']['posterior_target_counts'].get('0', 0)} |",
        "",
        "## Mapping",
        "",
        "| Working label | Codex label | Posterior target |",
        "| --- | --- | ---: |",
        "| `true_underconfidence` | `reliable_promote` | 1 |",
        "| `dense_relation_noise` | `unreliable_dense_noise` | 0 |",
        "",
    ]
    as_abs(path).write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    fieldnames, sheet_rows = read_tsv(args.input_sheet)
    queue_by_id = {str(row["prediction_id"]): row for row in read_jsonl(args.input_queue)}
    filled_rows = []
    label_rows = []
    missing_queue = []
    for row in sheet_rows:
        queue_row = queue_by_id.get(row["prediction_id"])
        if queue_row is None:
            missing_queue.append(row["prediction_id"])
            queue_row = {}
        filled, label_row = fill_row(row, queue_row)
        filled_rows.append(filled)
        label_rows.append(label_row)

    final_label_counts = Counter(str(row["final_human_label"]) for row in label_rows)
    target_counts = Counter(str(row["posterior_target"]) for row in label_rows)
    working_counts = Counter(str(row["working_label"]) for row in label_rows)
    created_at = datetime.now(timezone.utc).isoformat()
    summary = {
        "schema_version": "h002_codex_ver_strict_label_summary_v0",
        "status": "strict_codex_ver_labels_filled_not_human_confirmed",
        "created_at": created_at,
        "input_paths": {
            "input_sheet": rel_path(args.input_sheet),
            "input_queue": rel_path(args.input_queue),
        },
        "output_paths": {
            "output_sheet": rel_path(args.output_sheet),
            "output_labels": rel_path(args.output_labels),
            "output_summary": rel_path(args.output_summary),
            "output_report": rel_path(args.output_report),
        },
        "counts": {
            "rows": len(filled_rows),
            "working_label_counts": dict(sorted(working_counts.items())),
            "final_label_counts": dict(sorted(final_label_counts.items())),
            "posterior_target_counts": dict(sorted(target_counts.items())),
            "missing_queue_rows": len(missing_queue),
        },
        "boundary": {
            "split": "train_only",
            "reviewer_id": REVIEWER_ID,
            "codex_filled": True,
            "human_confirmed": False,
            "paper_result": False,
            "validation_usage": False,
            "posterior_claim_allowed": False,
            "allowed_use": "train-only posterior plumbing smoke only",
        },
    }
    write_tsv(args.output_sheet, fieldnames, filled_rows)
    write_jsonl(args.output_labels, label_rows)
    write_json(args.output_summary, summary)
    write_report(args.output_report, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        f"status={summary['status']} rows={summary['counts']['rows']} "
        f"labels={summary['counts']['final_label_counts']} "
        f"validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
