#!/usr/bin/env python3
"""Summarize second-review impact for H002 high-rank labels."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
ROUND1_PATH = H002_ROOT / "artifacts/manual_labels/round1_labels.jsonl"
SECOND_REVIEW_PATH = H002_ROOT / "artifacts/second_review/reviewed_rows.jsonl"
DEFAULT_OUTPUT_DIR = H002_ROOT / "artifacts/revision_impact"

POSITIVE_SIGNAL_LABELS = {
    "label_granularity_mismatch",
    "annotation_sparsity_likely",
    "plausible_unlabeled_relation",
}
RISK_LABELS = {
    "source_false_positive",
    "object_pair_mismatch",
    "geometry_artifact",
    "uncertain_needs_visual",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
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


def counter_to_sorted_dict(counter: Counter) -> dict[str, int]:
    return dict(sorted(counter.items()))


def count_labels(rows: list[dict[str, Any]], label_field: str) -> Counter:
    return Counter(str(row.get(label_field)) for row in rows)


def positive_count(counter: Counter) -> int:
    return sum(counter.get(label, 0) for label in POSITIVE_SIGNAL_LABELS)


def risk_count(counter: Counter) -> int:
    return sum(counter.get(label, 0) for label in RISK_LABELS)


def apply_direct_patch(round1_rows: list[dict[str, Any]], reviewed_rows: list[dict[str, Any]]) -> Counter:
    labels_by_id = {row["row_id"]: str(row["final_label"]) for row in round1_rows}
    for row in reviewed_rows:
        if row.get("changed"):
            labels_by_id[row["row_id"]] = str(row["second_review_label"])
    return Counter(labels_by_id.values())


def support_plausible_stress(round1_rows: list[dict[str, Any]], reviewed_rows: list[dict[str, Any]]) -> dict[str, Any]:
    target_rows = [
        row
        for row in round1_rows
        if row.get("predicate_family") == "support_contact"
        and row.get("final_label") == "plausible_unlabeled_relation"
    ]
    reviewed_target = [
        row
        for row in reviewed_rows
        if row.get("predicate_family") == "support_contact"
        and row.get("round1_label") == "plausible_unlabeled_relation"
    ]
    changed_target = [row for row in reviewed_target if row.get("changed")]
    revision_destinations = Counter(str(row["second_review_label"]) for row in changed_target)
    keep_rate = (
        (len(reviewed_target) - len(changed_target)) / len(reviewed_target)
        if reviewed_target
        else 0.0
    )
    revision_rate = 1.0 - keep_rate

    projected_keep = round(len(target_rows) * keep_rate)
    projected_revised_total = len(target_rows) - projected_keep
    projected_destinations = Counter()
    if changed_target:
        assigned = 0
        destinations = list(revision_destinations.items())
        for index, (label, count) in enumerate(destinations):
            if index == len(destinations) - 1:
                value = projected_revised_total - assigned
            else:
                value = round(projected_revised_total * count / len(changed_target))
                assigned += value
            projected_destinations[label] += value

    base = count_labels(round1_rows, "final_label")
    base["plausible_unlabeled_relation"] -= len(target_rows)
    base["plausible_unlabeled_relation"] += projected_keep
    for label, count in projected_destinations.items():
        base[label] += count

    return {
        "target_rows": len(target_rows),
        "sample_rows": len(reviewed_target),
        "sample_changed": len(changed_target),
        "sample_revision_rate": revision_rate,
        "sample_revision_destinations": counter_to_sorted_dict(revision_destinations),
        "projected_distribution": counter_to_sorted_dict(base),
        "projected_positive_signal_count": positive_count(base),
        "projected_risk_count": risk_count(base),
        "boundary": (
            "Stress test only. The second-review sample intentionally over-sampled "
            "support_contact plausible rows and is not a statistically representative estimate."
        ),
    }


def build_summary() -> dict[str, Any]:
    round1_rows = read_jsonl(ROUND1_PATH)
    reviewed_rows = read_jsonl(SECOND_REVIEW_PATH)
    changed_rows = [row for row in reviewed_rows if row.get("changed")]

    round1_counts = count_labels(round1_rows, "final_label")
    direct_counts = apply_direct_patch(round1_rows, reviewed_rows)
    reviewed_round1_counts = count_labels(reviewed_rows, "round1_label")
    reviewed_second_counts = count_labels(reviewed_rows, "second_review_label")

    by_family_review = Counter(
        f"{row.get('predicate_family')}|{row.get('round1_label')}|{row.get('second_review_label')}"
        for row in reviewed_rows
    )
    by_family_changed = Counter(
        f"{row.get('predicate_family')}|{row.get('round1_label')}->{row.get('second_review_label')}"
        for row in changed_rows
    )

    summary = {
        "schema_version": "h002_revision_impact_v0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "round1_labels": str(ROUND1_PATH.relative_to(H002_ROOT)),
            "second_review": str(SECOND_REVIEW_PATH.relative_to(H002_ROOT)),
        },
        "scope": {
            "high_rank_rows": len(round1_rows),
            "second_review_rows": len(reviewed_rows),
            "changed_rows": len(changed_rows),
            "second_review_revision_rate": len(changed_rows) / len(reviewed_rows)
            if reviewed_rows
            else 0.0,
            "paper_locked": False,
            "sample_boundary": (
                "Second-review rows are contact-sheet-only and intentionally emphasize "
                "support_contact plausible cases; revision rates are diagnostic, not "
                "population estimates."
            ),
        },
        "round1_distribution": counter_to_sorted_dict(round1_counts),
        "direct_patch_distribution": counter_to_sorted_dict(direct_counts),
        "reviewed_round1_distribution": counter_to_sorted_dict(reviewed_round1_counts),
        "reviewed_second_distribution": counter_to_sorted_dict(reviewed_second_counts),
        "by_family_review": counter_to_sorted_dict(by_family_review),
        "by_family_changed": counter_to_sorted_dict(by_family_changed),
        "round1_positive_signal_count": positive_count(round1_counts),
        "direct_patch_positive_signal_count": positive_count(direct_counts),
        "round1_risk_count": risk_count(round1_counts),
        "direct_patch_risk_count": risk_count(direct_counts),
        "support_plausible_stress": support_plausible_stress(round1_rows, reviewed_rows),
        "next_direction": {
            "decision": "expand_to_bidirectional_mismatch",
            "new_required_bucket": "RGA-LH",
            "meaning": "low-semantic + high-geometry relation candidates",
            "reason": (
                "H002's factorized reliability claim is incomplete if it only studies "
                "semantic overconfidence. It must also test semantic underconfidence "
                "and geometry-supported missed/under-ranked relations."
            ),
        },
    }
    return summary


def markdown_table(counter: dict[str, int], headers: tuple[str, str]) -> list[str]:
    lines = [f"| {headers[0]} | {headers[1]} |", "| --- | ---: |"]
    for key, value in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{key}` | {value} |")
    return lines


def write_report(path: Path, summary: dict[str, Any]) -> None:
    stress = summary["support_plausible_stress"]
    lines = [
        "# H002 Revision Impact",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        summary["scope"]["sample_boundary"],
        "",
        "## Scope",
        "",
        f"- High-rank rows: `{summary['scope']['high_rank_rows']}`",
        f"- Second-review rows: `{summary['scope']['second_review_rows']}`",
        f"- Changed rows: `{summary['scope']['changed_rows']}`",
        f"- Diagnostic revision rate: `{summary['scope']['second_review_revision_rate']:.3f}`",
        "",
        "## Round-1 Distribution",
        "",
        *markdown_table(summary["round1_distribution"], ("Label", "Rows")),
        "",
        "## Direct Patch Distribution",
        "",
        *markdown_table(summary["direct_patch_distribution"], ("Label", "Rows")),
        "",
        "## Changed Strata",
        "",
        *markdown_table(summary["by_family_changed"], ("Family / label change", "Rows")),
        "",
        "## Support Plausible Stress Test",
        "",
        f"- Target rows: `{stress['target_rows']}`",
        f"- Reviewed target rows: `{stress['sample_rows']}`",
        f"- Changed target rows: `{stress['sample_changed']}`",
        f"- Sample revision rate: `{stress['sample_revision_rate']:.3f}`",
        "",
        stress["boundary"],
        "",
        "Projected distribution under this stress test:",
        "",
        *markdown_table(stress["projected_distribution"], ("Label", "Rows")),
        "",
        "## Next Direction",
        "",
        f"Decision: `{summary['next_direction']['decision']}`",
        "",
        summary["next_direction"]["reason"],
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = H002_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = build_summary()
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    write_report(output_dir / "report.md", summary)

    print(
        f"high_rank={summary['scope']['high_rank_rows']} "
        f"reviewed={summary['scope']['second_review_rows']} "
        f"changed={summary['scope']['changed_rows']} "
        f"direction={summary['next_direction']['decision']} output={output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
