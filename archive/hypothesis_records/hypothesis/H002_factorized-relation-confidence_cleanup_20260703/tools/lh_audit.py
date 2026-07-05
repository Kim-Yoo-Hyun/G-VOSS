#!/usr/bin/env python3
"""Prepare RGA-LH rows for visual and annotation audit.

This script enriches the low-semantic/high-geometry queue with local visual
assets. It does not assign paper-final labels.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from annotation_audit import (
    H002_ROOT,
    find_instance_images,
    read_jsonl,
    render_contact_sheet,
    repo_rel,
    safe_slug,
    scan_asset_paths,
)


DEFAULT_OUTPUT_DIR = H002_ROOT / "artifacts/lh_audit"
QUEUE_INPUTS = [
    H002_ROOT / "artifacts/lh_diagnostic/vlsat_queue.jsonl",
    H002_ROOT
    / "artifacts/lh_diagnostic/open3dsg_recovery_relaxed_views_min2_queue.jsonl",
]

FINAL_LABEL_OPTIONS = [
    "semantic_underconfidence_exact_gt",
    "semantic_underconfidence_family_or_granularity",
    "label_granularity_mismatch",
    "annotation_sparsity_likely",
    "geometry_trivial_or_dense_relation",
    "plausible_unlabeled_relation",
    "object_pair_mismatch",
    "source_false_positive",
    "geometry_artifact",
    "uncertain_needs_visual_or_mesh",
]

GENERIC_LABELS = {"item", "object", "clutter", "unknown"}
STRUCTURAL_LABELS = {"wall", "floor", "ceiling", "doorframe", "window", "shower wall"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--render-contact-sheets", action="store_true")
    parser.add_argument(
        "--render-scope",
        choices=["all", "exact_first"],
        default="all",
        help="exact_first renders exact-match rows only.",
    )
    parser.add_argument("--images-per-object", type=int, default=2)
    return parser.parse_args()


def review_priority(row: dict[str, Any]) -> str:
    match_status = str(row.get("match_status"))
    if match_status == "exact_match":
        return "P0_exact_match"
    if match_status == "family_match":
        return "P1_family_match"
    if match_status == "pair_has_other_predicate":
        return "P2_pair_other"
    return "P3_no_gt"


def infer_lh_previsual_label(row: dict[str, Any]) -> tuple[str, str]:
    family = str(row.get("predicate_family"))
    predicate = str(row.get("predicate_label"))
    match_status = str(row.get("match_status"))
    subject_label = str(row.get("subject_label") or "").lower()
    object_label = str(row.get("object_label") or "").lower()
    matched_predicates = [str(item) for item in row.get("matched_predicates") or []]
    reason_codes = [str(item) for item in row.get("reason_codes") or []]

    if row.get("verification_status") != "satisfied":
        return "geometry_artifact", "LH audit expects geometry-satisfied rows only"

    if row.get("subject_id") == row.get("object_id"):
        return "object_pair_mismatch", "subject_id and object_id are identical"

    if subject_label in GENERIC_LABELS or object_label in GENERIC_LABELS:
        return (
            "uncertain_needs_visual_or_mesh",
            "one endpoint has a generic object label; visual identity must be checked",
        )

    if match_status == "exact_match":
        return (
            "semantic_underconfidence_exact_gt",
            "exact GT predicate is present, geometry is satisfied, but semantic rank is outside top 100",
        )

    if match_status == "family_match":
        return (
            "semantic_underconfidence_family_or_granularity",
            "GT has a same-family predicate; low semantic rank may reflect predicate granularity",
        )

    if match_status == "pair_has_other_predicate":
        return (
            "label_granularity_mismatch",
            "GT has another predicate on the same object pair: "
            + (", ".join(matched_predicates[:4]) if matched_predicates else "unknown"),
        )

    if (
        family == "support_contact"
        and predicate in {"standing on", "supported by", "lying on"}
        and subject_label in STRUCTURAL_LABELS
        and object_label in STRUCTURAL_LABELS
    ):
        return (
            "source_false_positive",
            "structural support/contact wording is suspicious before visual confirmation",
        )

    if family == "proximity":
        return (
            "geometry_trivial_or_dense_relation",
            "dense proximity relations can be geometry-satisfied but uninformative or sparsely annotated",
        )

    if family == "relative_vertical":
        return (
            "annotation_sparsity_likely",
            "vertical order is geometry-satisfied but no exact GT predicate is present",
        )

    if family == "support_contact":
        if reason_codes:
            return (
                "plausible_unlabeled_relation",
                "support/contact satisfied witness codes: " + ", ".join(reason_codes[:4]),
            )
        return (
            "uncertain_needs_visual_or_mesh",
            "support/contact needs endpoint and mesh/point verification",
        )

    return "uncertain_needs_visual_or_mesh", "relation family is outside the LH previsual rules"


def should_render(row: dict[str, Any], render_scope: str) -> bool:
    if render_scope == "all":
        return True
    return row.get("match_status") == "exact_match"


def enrich_rows(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    output_dir = args.output_dir if args.output_dir.is_absolute() else H002_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    counters: dict[str, Counter] = {
        "by_source": Counter(),
        "by_family": Counter(),
        "by_match_status": Counter(),
        "by_rank_band": Counter(),
        "by_priority": Counter(),
        "by_previsual_label": Counter(),
        "by_asset_state": Counter(),
        "by_source_label": Counter(),
        "by_family_label": Counter(),
        "by_priority_label": Counter(),
    }
    input_counts: dict[str, int] = {}

    for queue_path in QUEUE_INPUTS:
        input_key = str(queue_path.relative_to(H002_ROOT))
        input_counts[input_key] = 0
        for _, row in read_jsonl(queue_path):
            input_counts[input_key] += 1
            subject_images, subject_image_count = find_instance_images(
                str(row["scan_id"]), int(row["subject_id"]), args.images_per_object
            )
            object_images, object_image_count = find_instance_images(
                str(row["scan_id"]), int(row["object_id"]), args.images_per_object
            )
            priority = review_priority(row)
            previsual_label, previsual_reason = infer_lh_previsual_label(row)
            asset_state = (
                "subject_and_object_images"
                if subject_images and object_images
                else "missing_subject_or_object_images"
            )

            review_row = dict(row)
            review_row.update(
                {
                    "review_priority": priority,
                    "previsual_label": previsual_label,
                    "previsual_reason": previsual_reason,
                    "final_label": None,
                    "requires_visual_confirmation": True,
                    "requires_mesh_or_point_check": row.get("predicate_family") == "support_contact",
                    "asset_state": asset_state,
                    "visual_assets": {
                        **scan_asset_paths(str(row["scan_id"])),
                        "subject_images": [repo_rel(path) for path in subject_images],
                        "object_images": [repo_rel(path) for path in object_images],
                        "subject_image_count": subject_image_count,
                        "object_image_count": object_image_count,
                        "contact_sheet": None,
                    },
                }
            )

            if args.render_contact_sheets and should_render(review_row, args.render_scope):
                sheet_name = (
                    f"{len(rows) + 1:04d}_lh_{safe_slug(row['source_id'])}_"
                    f"{safe_slug(str(row['scan_id'])[:8])}_{row['subject_id']}_"
                    f"{safe_slug(row['predicate_label'])}_{row['object_id']}.jpg"
                )
                sheet_path = output_dir / "contact_sheets" / sheet_name
                if subject_images and object_images:
                    render_contact_sheet(review_row, subject_images, object_images, sheet_path)
                    review_row["visual_assets"]["contact_sheet"] = repo_rel(sheet_path)

            rows.append(review_row)

            source = str(row.get("source_id"))
            family = str(row.get("predicate_family"))
            match_status = str(row.get("match_status"))
            rank_band = str(row.get("rank_band"))
            counters["by_source"][source] += 1
            counters["by_family"][family] += 1
            counters["by_match_status"][match_status] += 1
            counters["by_rank_band"][rank_band] += 1
            counters["by_priority"][priority] += 1
            counters["by_previsual_label"][previsual_label] += 1
            counters["by_asset_state"][asset_state] += 1
            counters["by_source_label"][(source, previsual_label)] += 1
            counters["by_family_label"][(family, previsual_label)] += 1
            counters["by_priority_label"][(priority, previsual_label)] += 1

    summary = {
        "schema_version": "h002_lh_audit_preparation_v0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_counts": input_counts,
        "total_rows": len(rows),
        "final_label_options": FINAL_LABEL_OPTIONS,
        "counts": {
            "by_source": dict(sorted(counters["by_source"].items())),
            "by_family": dict(sorted(counters["by_family"].items())),
            "by_match_status": dict(sorted(counters["by_match_status"].items())),
            "by_rank_band": dict(sorted(counters["by_rank_band"].items())),
            "by_priority": dict(sorted(counters["by_priority"].items())),
            "by_previsual_label": dict(sorted(counters["by_previsual_label"].items())),
            "by_asset_state": dict(sorted(counters["by_asset_state"].items())),
            "by_source_label": {
                f"{source}|{label}": count
                for (source, label), count in sorted(counters["by_source_label"].items())
            },
            "by_family_label": {
                f"{family}|{label}": count
                for (family, label), count in sorted(counters["by_family_label"].items())
            },
            "by_priority_label": {
                f"{priority}|{label}": count
                for (priority, label), count in sorted(counters["by_priority_label"].items())
            },
        },
        "boundary": (
            "previsual_label is a triage label for RGA-LH audit only. It is not a "
            "paper-final human annotation and does not imply automatic graph promotion."
        ),
    }
    return rows, summary


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_manual_sheet(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "audit_id",
        "source_id",
        "review_priority",
        "match_status",
        "rank_band",
        "semantic_rank",
        "predicate_family",
        "subject_label",
        "predicate_label",
        "object_label",
        "previsual_label",
        "final_label",
        "contact_sheet",
        "mesh_obj",
        "instance_ply",
        "prediction_id",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for idx, row in enumerate(rows, start=1):
            assets = row.get("visual_assets") or {}
            writer.writerow(
                {
                    "audit_id": f"h002_lh_{idx:04d}",
                    "source_id": row.get("source_id"),
                    "review_priority": row.get("review_priority"),
                    "match_status": row.get("match_status"),
                    "rank_band": row.get("rank_band"),
                    "semantic_rank": row.get("semantic_rank"),
                    "predicate_family": row.get("predicate_family"),
                    "subject_label": row.get("subject_label"),
                    "predicate_label": row.get("predicate_label"),
                    "object_label": row.get("object_label"),
                    "previsual_label": row.get("previsual_label"),
                    "final_label": row.get("final_label"),
                    "contact_sheet": assets.get("contact_sheet"),
                    "mesh_obj": assets.get("mesh_obj"),
                    "instance_ply": assets.get("instance_ply"),
                    "prediction_id": row.get("prediction_id"),
                }
            )


def markdown_table(counter: dict[str, int], headers: tuple[str, str]) -> list[str]:
    lines = [f"| {headers[0]} | {headers[1]} |", "| --- | ---: |"]
    for key, value in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{key}` | {value} |")
    return lines


def write_report(output_dir: Path, summary: dict[str, Any]) -> None:
    lines: list[str] = [
        "# H002 RGA-LH Audit Preparation",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        summary["boundary"],
        "",
        "This report prepares 236 low-semantic/high-geometry rows for visual, annotation, and mesh/point review.",
        "",
        "## Outputs",
        "",
        "- `review_queue.jsonl`: enriched LH audit queue with visual asset paths.",
        "- `exact_first_queue.jsonl`: exact-match LH rows for first manual pass.",
        "- `no_gt_queue.jsonl`: no-GT LH rows for separate annotation/ontology audit.",
        "- `manual_sheet.tsv`: compact review sheet.",
        "- `previsual_summary.json`: counts and schema boundary.",
        "- `contact_sheets/`: generated contact sheets when rendering is enabled.",
        "",
        "## Counts",
        "",
        f"- Total rows: `{summary['total_rows']}`",
        "",
        "### Priority",
        "",
        *markdown_table(summary["counts"]["by_priority"], ("Priority", "Rows")),
        "",
        "### Match Status",
        "",
        *markdown_table(summary["counts"]["by_match_status"], ("Match status", "Rows")),
        "",
        "### Family",
        "",
        *markdown_table(summary["counts"]["by_family"], ("Family", "Rows")),
        "",
        "### Rank Band",
        "",
        *markdown_table(summary["counts"]["by_rank_band"], ("Rank band", "Rows")),
        "",
        "### Visual Asset State",
        "",
        *markdown_table(summary["counts"]["by_asset_state"], ("Asset state", "Rows")),
        "",
        "### Previsual Labels",
        "",
        *markdown_table(summary["counts"]["by_previsual_label"], ("Previsual label", "Rows")),
        "",
        "### Priority And Label",
        "",
        *markdown_table(summary["counts"]["by_priority_label"], ("Priority|label", "Rows")),
        "",
        "## Next Step",
        "",
        "Review `exact_first_queue.jsonl` first. Then review `no_gt_queue.jsonl` separately because no-GT LH rows are candidate-discovery or annotation/ontology cases, not automatic positives.",
        "",
    ]
    (output_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else H002_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    rows, summary = enrich_rows(args)
    write_jsonl(output_dir / "review_queue.jsonl", rows)
    write_jsonl(
        output_dir / "exact_first_queue.jsonl",
        [row for row in rows if row.get("match_status") == "exact_match"],
    )
    write_jsonl(
        output_dir / "no_gt_queue.jsonl",
        [row for row in rows if row.get("match_status") == "no_gt_for_pair"],
    )
    write_manual_sheet(output_dir / "manual_sheet.tsv", rows)
    with (output_dir / "previsual_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    write_report(output_dir, summary)

    print(
        f"rows={summary['total_rows']} "
        f"labels={summary['counts']['by_previsual_label']} "
        f"output={output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
