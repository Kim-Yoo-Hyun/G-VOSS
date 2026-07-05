#!/usr/bin/env python3
"""Create a round-1 high-rank manual-label working set for H002.

The output fills `final_label` for workflow continuity, but marks every row as
not paper-locked. The original review queue is never modified.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
INPUT_QUEUE = H002_ROOT / "artifacts/visual_annotation_audit/review_queue.jsonl"
DEFAULT_OUTPUT_DIR = H002_ROOT / "artifacts/manual_labels"
HIGH_RANK_PRIORITIES = {"P0_top50", "P1_top100_only"}


FINAL_LABELS = {
    "plausible_unlabeled_relation",
    "annotation_sparsity_likely",
    "source_false_positive",
    "object_pair_mismatch",
    "label_granularity_mismatch",
    "geometry_artifact",
    "uncertain_needs_visual",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT_QUEUE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def label_from_row(row: dict[str, Any]) -> tuple[str, str, str]:
    """Return final_label, provenance, and confidence for round-1 labeling."""
    previsual = str(row.get("previsual_label") or "uncertain_needs_visual")
    match_status = str(row.get("match_status") or "")
    family = str(row.get("predicate_family") or "")
    reason_codes = [str(item) for item in row.get("reason_codes") or []]

    if previsual not in FINAL_LABELS:
        return (
            "uncertain_needs_visual",
            "unknown_previsual_label_fallback",
            "low",
        )

    if match_status == "pair_has_other_predicate":
        return (
            "label_granularity_mismatch",
            "same_pair_has_gt_other_predicate",
            "medium",
        )

    if previsual == "source_false_positive":
        return (
            "source_false_positive",
            "semantic_pair_suspicious_despite_geometry_satisfied",
            "low",
        )

    if previsual == "object_pair_mismatch":
        return (
            "object_pair_mismatch",
            "subject_object_identity_rule",
            "medium",
        )

    if family == "support_contact" and previsual == "plausible_unlabeled_relation":
        return (
            "plausible_unlabeled_relation",
            "support_contact_geometry_reason_codes:" + ",".join(reason_codes[:4]),
            "medium",
        )

    if family in {"proximity", "relative_vertical"} and previsual == "annotation_sparsity_likely":
        return (
            "annotation_sparsity_likely",
            f"{family}_geometry_satisfied_no_exact_gt",
            "medium",
        )

    if previsual == "uncertain_needs_visual":
        return (
            "uncertain_needs_visual",
            "generic_label_or_insufficient_relation_evidence",
            "low",
        )

    return (
        previsual,
        "previsual_label_carried_forward",
        "low",
    )


def review_status(final_label: str, confidence: str) -> str:
    if final_label in {"uncertain_needs_visual", "source_false_positive"}:
        return "needs_second_review"
    if confidence == "low":
        return "needs_second_review"
    return "ready_for_human_confirmation"


def row_sort_key(row: dict[str, Any]) -> tuple[int, str, int, str]:
    priority_rank = {"P0_top50": 0, "P1_top100_only": 1, "P2_outside_top100": 2}
    return (
        priority_rank.get(str(row.get("review_priority")), 99),
        str(row.get("source_id")),
        int(row.get("semantic_rank") or 10**9),
        str(row.get("prediction_id")),
    )


def compact_row(row: dict[str, Any]) -> dict[str, Any]:
    visual_assets = row.get("visual_assets") or {}
    return {
        "row_id": row["row_id"],
        "source_id": row.get("source_id"),
        "review_priority": row.get("review_priority"),
        "scan_id": row.get("scan_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "predicate_family": row.get("predicate_family"),
        "semantic_rank": row.get("semantic_rank"),
        "semantic_score": row.get("semantic_score"),
        "p_geom_valid": row.get("p_geom_valid"),
        "match_status": row.get("match_status"),
        "matched_predicates": row.get("matched_predicates"),
        "previsual_label": row.get("previsual_label"),
        "final_label": row.get("final_label"),
        "label_confidence": row.get("label_confidence"),
        "label_provenance": row.get("label_provenance"),
        "review_status": row.get("review_status"),
        "contact_sheet": visual_assets.get("contact_sheet"),
        "mesh_obj": visual_assets.get("mesh_obj"),
        "instance_ply": visual_assets.get("instance_ply"),
    }


def summarize(rows: list[dict[str, Any]], input_path: Path) -> dict[str, Any]:
    counters: dict[str, Counter] = {
        "by_source": Counter(),
        "by_priority": Counter(),
        "by_family": Counter(),
        "by_final_label": Counter(),
        "by_source_label": Counter(),
        "by_family_label": Counter(),
        "by_review_status": Counter(),
        "by_confidence": Counter(),
    }
    for row in rows:
        source = str(row.get("source_id"))
        priority = str(row.get("review_priority"))
        family = str(row.get("predicate_family"))
        final_label = str(row.get("final_label"))
        counters["by_source"][source] += 1
        counters["by_priority"][priority] += 1
        counters["by_family"][family] += 1
        counters["by_final_label"][final_label] += 1
        counters["by_source_label"][(source, final_label)] += 1
        counters["by_family_label"][(family, final_label)] += 1
        counters["by_review_status"][str(row.get("review_status"))] += 1
        counters["by_confidence"][str(row.get("label_confidence"))] += 1

    return {
        "schema_version": "h002_manual_labels_round1_v0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_queue": str(input_path.relative_to(H002_ROOT)),
        "scope": {
            "included_priorities": sorted(HIGH_RANK_PRIORITIES),
            "paper_locked": False,
            "boundary": (
                "Round-1 labels are working labels for H002 workflow continuity. "
                "They use metadata, GT-pair status, geometry verifier outputs, and "
                "available contact-sheet/mesh links. They are not paper-locked "
                "human visual annotations."
            ),
        },
        "row_count": len(rows),
        "counts": {
            "by_source": dict(sorted(counters["by_source"].items())),
            "by_priority": dict(sorted(counters["by_priority"].items())),
            "by_family": dict(sorted(counters["by_family"].items())),
            "by_final_label": dict(sorted(counters["by_final_label"].items())),
            "by_source_label": {
                f"{source}|{label}": count
                for (source, label), count in sorted(counters["by_source_label"].items())
            },
            "by_family_label": {
                f"{family}|{label}": count
                for (family, label), count in sorted(counters["by_family_label"].items())
            },
            "by_review_status": dict(sorted(counters["by_review_status"].items())),
            "by_confidence": dict(sorted(counters["by_confidence"].items())),
        },
    }


def markdown_table(counter: dict[str, int], headers: tuple[str, str]) -> list[str]:
    lines = [f"| {headers[0]} | {headers[1]} |", "| --- | ---: |"]
    for key, value in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{key}` | {value} |")
    return lines


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Manual Labels Round 1",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        summary["scope"]["boundary"],
        "",
        "The original visual annotation queue is unchanged. Use `manual_sheet.tsv` to confirm or revise labels.",
        "",
        "## Scope",
        "",
        f"- Rows: `{summary['row_count']}`",
        "- Priorities: `P0_top50`, `P1_top100_only`",
        "- Paper locked: `false`",
        "",
        "## Final Label Distribution",
        "",
        *markdown_table(summary["counts"]["by_final_label"], ("Final label", "Rows")),
        "",
        "## Review Status",
        "",
        *markdown_table(summary["counts"]["by_review_status"], ("Review status", "Rows")),
        "",
        "## Source And Label",
        "",
        *markdown_table(summary["counts"]["by_source_label"], ("Source|label", "Rows")),
        "",
        "## Family And Label",
        "",
        *markdown_table(summary["counts"]["by_family_label"], ("Family|label", "Rows")),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "row_id",
        "source_id",
        "review_priority",
        "scan_id",
        "subject_id",
        "subject_label",
        "predicate_label",
        "object_id",
        "object_label",
        "predicate_family",
        "semantic_rank",
        "semantic_score",
        "p_geom_valid",
        "match_status",
        "matched_predicates",
        "previsual_label",
        "final_label",
        "label_confidence",
        "label_provenance",
        "review_status",
        "contact_sheet",
        "mesh_obj",
        "instance_ply",
        "human_label",
        "human_notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in rows:
            compact = compact_row(row)
            compact["matched_predicates"] = ",".join(compact.get("matched_predicates") or [])
            compact["human_label"] = ""
            compact["human_notes"] = ""
            writer.writerow(compact)


def main() -> int:
    args = parse_args()
    input_path = args.input
    if not input_path.is_absolute():
        input_path = H002_ROOT / input_path
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = H002_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    all_rows = read_jsonl(input_path)
    high_rank_rows = [
        row for row in all_rows if str(row.get("review_priority")) in HIGH_RANK_PRIORITIES
    ]
    high_rank_rows = sorted(high_rank_rows, key=row_sort_key)

    labeled_rows: list[dict[str, Any]] = []
    needs_second_review: list[dict[str, Any]] = []
    for index, row in enumerate(high_rank_rows, start=1):
        final_label, provenance, confidence = label_from_row(row)
        labeled = dict(row)
        labeled.update(
            {
                "row_id": f"h002_round1_{index:04d}",
                "final_label": final_label,
                "label_confidence": confidence,
                "label_provenance": provenance,
                "review_status": review_status(final_label, confidence),
                "paper_locked": False,
                "requires_human_confirmation": True,
            }
        )
        labeled_rows.append(labeled)
        if labeled["review_status"] == "needs_second_review":
            needs_second_review.append(labeled)

    summary = summarize(labeled_rows, input_path)

    write_jsonl(output_dir / "round1_labels.jsonl", labeled_rows)
    write_jsonl(output_dir / "needs_second_review.jsonl", needs_second_review)
    write_tsv(output_dir / "manual_sheet.tsv", labeled_rows)
    with (output_dir / "round1_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    write_report(output_dir / "report.md", summary)

    print(
        f"rows={len(labeled_rows)} needs_second_review={len(needs_second_review)} "
        f"labels={summary['counts']['by_final_label']} output={output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
