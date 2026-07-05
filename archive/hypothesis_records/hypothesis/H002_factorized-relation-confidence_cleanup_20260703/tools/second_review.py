#!/usr/bin/env python3
"""Record H002 second-review decisions for selected high-rank rows.

The script is intentionally scoped: it writes a reviewed subset and does not
modify round-1 labels.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
ROUND1_PATH = H002_ROOT / "artifacts/manual_labels/round1_labels.jsonl"
NEEDS_REVIEW_PATH = H002_ROOT / "artifacts/manual_labels/needs_second_review.jsonl"
DEFAULT_OUTPUT_DIR = H002_ROOT / "artifacts/second_review"


READY_SAMPLE_IDS = [
    "h002_round1_0013",
    "h002_round1_0019",
    "h002_round1_0021",
    "h002_round1_0025",
    "h002_round1_0031",
    "h002_round1_0049",
    "h002_round1_0052",
    "h002_round1_0053",
    "h002_round1_0054",
    "h002_round1_0056",
    "h002_round1_0004",
    "h002_round1_0007",
    "h002_round1_0001",
    "h002_round1_0002",
    "h002_round1_0022",
    "h002_round1_0028",
    "h002_round1_0003",
    "h002_round1_0041",
    "h002_round1_0042",
    "h002_round1_0043",
]


DECISIONS: dict[str, dict[str, str]] = {
    "h002_round1_0009": {
        "second_review_label": "uncertain_needs_visual",
        "decision": "keep",
        "visual_note": "Subject is labeled clutter and appears like a bathroom floor fixture; close-by relation to toilet cannot be paper-locked from crop alone.",
    },
    "h002_round1_0016": {
        "second_review_label": "uncertain_needs_visual",
        "decision": "keep",
        "visual_note": "Subject is generic clutter and object door crop is weak; keep uncertain.",
    },
    "h002_round1_0017": {
        "second_review_label": "uncertain_needs_visual",
        "decision": "keep",
        "visual_note": "Subject appears like bathroom floor fixture and sink is visible; proximity is plausible but object identity is too generic for a final missing-positive label.",
    },
    "h002_round1_0027": {
        "second_review_label": "uncertain_needs_visual",
        "decision": "keep",
        "visual_note": "Subject label is generic object and crop is dark/ambiguous; standing-on-floor cannot be paper-locked.",
    },
    "h002_round1_0050": {
        "second_review_label": "source_false_positive",
        "decision": "keep",
        "visual_note": "Wall standing on floor is semantically inappropriate even if structural contact exists.",
    },
    "h002_round1_0013": {
        "second_review_label": "plausible_unlabeled_relation",
        "decision": "keep",
        "visual_note": "Flower pot on shelf is visually plausible and matches support/contact witness.",
    },
    "h002_round1_0019": {
        "second_review_label": "plausible_unlabeled_relation",
        "decision": "keep",
        "visual_note": "Box on floor is visually plausible.",
    },
    "h002_round1_0021": {
        "second_review_label": "source_false_positive",
        "decision": "revise",
        "visual_note": "Shower curtain may touch the floor, but standing-on is a poor predicate for this object type.",
    },
    "h002_round1_0025": {
        "second_review_label": "object_pair_mismatch",
        "decision": "revise",
        "visual_note": "Box support appears associated with furniture/shelf area, while object endpoint is wall; pair target is not reliable.",
    },
    "h002_round1_0031": {
        "second_review_label": "object_pair_mismatch",
        "decision": "revise",
        "visual_note": "Book-on-wall is not reliable from crops; support surface/object endpoint appears mismatched.",
    },
    "h002_round1_0049": {
        "second_review_label": "plausible_unlabeled_relation",
        "decision": "keep",
        "visual_note": "Chair on floor is visually plausible.",
    },
    "h002_round1_0052": {
        "second_review_label": "plausible_unlabeled_relation",
        "decision": "keep",
        "visual_note": "Sofa on floor is visually plausible.",
    },
    "h002_round1_0053": {
        "second_review_label": "plausible_unlabeled_relation",
        "decision": "keep",
        "visual_note": "Plant on floor remains plausible, though final paper lock should check point/mesh evidence.",
    },
    "h002_round1_0054": {
        "second_review_label": "plausible_unlabeled_relation",
        "decision": "keep",
        "visual_note": "Armchair on floor is visually plausible.",
    },
    "h002_round1_0056": {
        "second_review_label": "uncertain_needs_visual",
        "decision": "revise",
        "visual_note": "Cabinet crop/identity is weak; do not count as confirmed plausible support.",
    },
    "h002_round1_0004": {
        "second_review_label": "annotation_sparsity_likely",
        "decision": "keep",
        "visual_note": "Decoration-fireplace proximity remains plausible but crop resolution is weak.",
    },
    "h002_round1_0007": {
        "second_review_label": "annotation_sparsity_likely",
        "decision": "keep",
        "visual_note": "Decoration-fireplace proximity remains plausible but should not be paper-locked without stronger visual/mesh evidence.",
    },
    "h002_round1_0001": {
        "second_review_label": "annotation_sparsity_likely",
        "decision": "keep",
        "visual_note": "Shelf higher than floor is visually clear.",
    },
    "h002_round1_0002": {
        "second_review_label": "annotation_sparsity_likely",
        "decision": "keep",
        "visual_note": "Shelf higher than floor is visually clear.",
    },
    "h002_round1_0022": {
        "second_review_label": "label_granularity_mismatch",
        "decision": "keep",
        "visual_note": "GT has left relation on same pair; close-by is compatible as a coarser spatial relation.",
    },
    "h002_round1_0028": {
        "second_review_label": "label_granularity_mismatch",
        "decision": "keep",
        "visual_note": "GT has left relation on same pair; close-by remains a label granularity case.",
    },
    "h002_round1_0003": {
        "second_review_label": "label_granularity_mismatch",
        "decision": "keep",
        "visual_note": "GT standing-on and predicted higher-than both describe the shelf/floor pair at different relation granularity.",
    },
    "h002_round1_0041": {
        "second_review_label": "source_false_positive",
        "decision": "revise",
        "visual_note": "Ottoman standing on cabinet is not visually supported; same-pair GT right is more plausible.",
    },
    "h002_round1_0042": {
        "second_review_label": "label_granularity_mismatch",
        "decision": "keep",
        "visual_note": "Clock attached-to wall is the GT; standing-on reflects predicate-set mismatch around wall attachment.",
    },
    "h002_round1_0043": {
        "second_review_label": "label_granularity_mismatch",
        "decision": "keep",
        "visual_note": "GT standing-in and predicted standing-on are a predicate granularity/ontology mismatch.",
    },
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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def compact_review(row: dict[str, Any], review_group: str) -> dict[str, Any]:
    decision = DECISIONS[row["row_id"]]
    visual_assets = row.get("visual_assets") or {}
    second_label = decision["second_review_label"]
    original_label = str(row.get("final_label"))
    return {
        "row_id": row["row_id"],
        "review_group": review_group,
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
        "p_geom_valid": row.get("p_geom_valid"),
        "match_status": row.get("match_status"),
        "matched_predicates": row.get("matched_predicates"),
        "round1_label": original_label,
        "second_review_label": second_label,
        "decision": decision["decision"],
        "changed": original_label != second_label,
        "visual_note": decision["visual_note"],
        "contact_sheet": visual_assets.get("contact_sheet"),
        "mesh_obj": visual_assets.get("mesh_obj"),
        "instance_ply": visual_assets.get("instance_ply"),
        "review_modality": "contact_sheet_only",
        "paper_locked": False,
    }


def build_review_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    round1_rows = {row["row_id"]: row for row in read_jsonl(ROUND1_PATH)}
    needs_review_ids = [row["row_id"] for row in read_jsonl(NEEDS_REVIEW_PATH)]
    selected_ids = needs_review_ids + READY_SAMPLE_IDS

    missing = [row_id for row_id in selected_ids if row_id not in round1_rows]
    missing_decisions = [row_id for row_id in selected_ids if row_id not in DECISIONS]
    if missing or missing_decisions:
        raise ValueError(
            f"missing_rows={missing} missing_decisions={missing_decisions}"
        )

    reviewed: list[dict[str, Any]] = []
    for row_id in selected_ids:
        group = "needs_second_review" if row_id in needs_review_ids else "ready_sample"
        reviewed.append(compact_review(round1_rows[row_id], group))

    counters: dict[str, Counter] = {
        "by_group": Counter(),
        "by_decision": Counter(),
        "by_round1_label": Counter(),
        "by_second_review_label": Counter(),
        "by_family_label": Counter(),
        "by_source_label": Counter(),
        "by_changed": Counter(),
    }
    for row in reviewed:
        counters["by_group"][row["review_group"]] += 1
        counters["by_decision"][row["decision"]] += 1
        counters["by_round1_label"][row["round1_label"]] += 1
        counters["by_second_review_label"][row["second_review_label"]] += 1
        counters["by_family_label"][
            (row["predicate_family"], row["second_review_label"])
        ] += 1
        counters["by_source_label"][(row["source_id"], row["second_review_label"])] += 1
        counters["by_changed"][str(row["changed"]).lower()] += 1

    summary = {
        "schema_version": "h002_second_review_v0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "round1_labels": str(ROUND1_PATH.relative_to(H002_ROOT)),
            "needs_second_review": str(NEEDS_REVIEW_PATH.relative_to(H002_ROOT)),
        },
        "scope": {
            "needs_second_review_rows": len(needs_review_ids),
            "ready_sample_rows": len(READY_SAMPLE_IDS),
            "total_reviewed_rows": len(reviewed),
            "review_modality": "contact_sheet_only",
            "paper_locked": False,
        },
        "counts": {
            "by_group": dict(sorted(counters["by_group"].items())),
            "by_decision": dict(sorted(counters["by_decision"].items())),
            "by_round1_label": dict(sorted(counters["by_round1_label"].items())),
            "by_second_review_label": dict(
                sorted(counters["by_second_review_label"].items())
            ),
            "by_family_label": {
                f"{family}|{label}": count
                for (family, label), count in sorted(counters["by_family_label"].items())
            },
            "by_source_label": {
                f"{source}|{label}": count
                for (source, label), count in sorted(counters["by_source_label"].items())
            },
            "by_changed": dict(sorted(counters["by_changed"].items())),
        },
        "boundary": (
            "Second review uses contact sheets only and does not paper-lock labels. "
            "Changed labels are review recommendations for the H002 audit workflow."
        ),
    }
    return reviewed, summary


def markdown_table(counter: dict[str, int], headers: tuple[str, str]) -> list[str]:
    lines = [f"| {headers[0]} | {headers[1]} |", "| --- | ---: |"]
    for key, value in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{key}` | {value} |")
    return lines


def write_report(path: Path, summary: dict[str, Any], reviewed: list[dict[str, Any]]) -> None:
    changed = [row for row in reviewed if row["changed"]]
    lines = [
        "# H002 Second Review",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        summary["boundary"],
        "",
        "## Scope",
        "",
        f"- Needs-second-review rows: `{summary['scope']['needs_second_review_rows']}`",
        f"- Ready sample rows: `{summary['scope']['ready_sample_rows']}`",
        f"- Total reviewed rows: `{summary['scope']['total_reviewed_rows']}`",
        "- Paper locked: `false`",
        "",
        "## Decisions",
        "",
        *markdown_table(summary["counts"]["by_decision"], ("Decision", "Rows")),
        "",
        "## Second-Review Labels",
        "",
        *markdown_table(
            summary["counts"]["by_second_review_label"], ("Second-review label", "Rows")
        ),
        "",
        "## Changed Rows",
        "",
    ]
    if not changed:
        lines.append("No changed rows.")
    else:
        lines.extend(["| Row | Round 1 | Second review | Note |", "| --- | --- | --- | --- |"])
        for row in changed:
            note = row["visual_note"].replace("|", "/")
            lines.append(
                f"| `{row['row_id']}` | `{row['round1_label']}` | "
                f"`{row['second_review_label']}` | {note} |"
            )
    lines.extend(
        [
            "",
            "## Family And Label",
            "",
            *markdown_table(summary["counts"]["by_family_label"], ("Family|label", "Rows")),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = H002_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    reviewed, summary = build_review_rows()
    changed = [row for row in reviewed if row["changed"]]

    write_jsonl(output_dir / "reviewed_rows.jsonl", reviewed)
    write_jsonl(output_dir / "changed_rows.jsonl", changed)
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    write_report(output_dir / "report.md", summary, reviewed)

    print(
        f"reviewed={len(reviewed)} changed={len(changed)} "
        f"labels={summary['counts']['by_second_review_label']} output={output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
