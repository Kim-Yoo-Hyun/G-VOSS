#!/usr/bin/env python3
"""Prepare train RGA audit seed for manual review and working labels."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from annotation_audit import (
    H002_ROOT,
    find_instance_images,
    render_contact_sheet,
    repo_rel,
    safe_slug,
    scan_asset_paths,
)


REPO_ROOT = Path(__file__).resolve().parents[4]
AUDIT_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga/audit"
DEFAULT_INPUT = AUDIT_ROOT / "audit_seed.jsonl"
DEFAULT_OUTPUT_DIR = (
    H002_ROOT
    / "artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit"
)

GENERIC_LABELS = {"item", "object", "clutter", "unknown"}
STRUCTURAL_LABELS = {"wall", "floor", "ceiling", "doorframe", "window", "shower wall"}

WORKING_LABELS = [
    "true_underconfidence",
    "annotation_sparsity",
    "ontology_mismatch",
    "semantic_overconfidence",
    "dense_relation_noise",
    "object_pair_error",
    "geometry_artifact",
    "uncertain_needs_visual_or_mesh",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--images-per-object", type=int, default=2)
    parser.add_argument("--render-contact-sheets", action="store_true")
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
    rows: list[dict[str, Any]] = []
    path = as_abs(path)
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def safe_rate(num: int, den: int) -> float | None:
    return num / den if den else None


def serial_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def serial_nested_counter(mapping: dict[Any, Counter[Any]]) -> dict[str, dict[str, int]]:
    return {str(key): serial_counter(value) for key, value in sorted(mapping.items(), key=lambda item: str(item[0]))}


def working_label(row: dict[str, Any]) -> tuple[str, str, str]:
    """Return working_label, reason, confidence."""
    kind = str(row.get("queue_kind"))
    family = str(row.get("predicate_family"))
    match_status = str(row.get("label_match_status"))
    subject_label = str(row.get("subject_label") or "").lower()
    object_label = str(row.get("object_label") or "").lower()

    if row.get("subject_id") == row.get("object_id"):
        return "object_pair_error", "subject_id equals object_id", "high"

    if subject_label in GENERIC_LABELS or object_label in GENERIC_LABELS:
        return (
            "uncertain_needs_visual_or_mesh",
            "generic endpoint label requires visual identity confirmation",
            "low",
        )

    if kind == "HL":
        if match_status == "pair_has_other_predicate":
            return (
                "semantic_overconfidence",
                "high semantic rank, geometry unsatisfied, and same pair has another GT predicate",
                "medium",
            )
        return (
            "semantic_overconfidence",
            "high semantic rank but deterministic geometry status is unsatisfied",
            "medium",
        )

    if kind == "LH":
        if match_status == "exact_match":
            return (
                "true_underconfidence",
                "exact GT predicate exists and geometry is satisfied, but semantic rank is outside top100",
                "medium",
            )
        if match_status == "family_match":
            return (
                "ontology_mismatch",
                "same-family GT predicate exists; low rank may reflect predicate granularity",
                "medium",
            )
        if match_status == "pair_has_other_predicate":
            return (
                "ontology_mismatch",
                "same directed pair has another GT predicate; multiple relations or ontology mismatch are plausible",
                "low",
            )
        if match_status == "no_gt_for_pair" and family == "proximity":
            return (
                "dense_relation_noise",
                "proximity is geometry-satisfied but dense and often uninformative without annotation",
                "low",
            )
        if match_status == "no_gt_for_pair" and family == "relative_vertical":
            return (
                "annotation_sparsity",
                "vertical order is geometry-satisfied but no directed-pair GT relation exists",
                "low",
            )
        if match_status == "no_gt_for_pair" and family == "support_contact":
            if subject_label in STRUCTURAL_LABELS and object_label in STRUCTURAL_LABELS:
                return (
                    "uncertain_needs_visual_or_mesh",
                    "support/contact between structural endpoints needs visual confirmation",
                    "low",
                )
            return (
                "annotation_sparsity",
                "support/contact witness is satisfied but no directed-pair GT relation exists",
                "low",
            )

    return (
        "uncertain_needs_visual_or_mesh",
        "no conservative working rule matched this row",
        "low",
    )


def normalize_for_contact_sheet(row: dict[str, Any], label: str, reason: str) -> dict[str, Any]:
    return {
        **row,
        "match_status": row.get("label_match_status"),
        "semantic_score": row.get("semantic_score_raw"),
        "verification_status": row.get("h001_verification_status") or row.get("geometry_status"),
        "previsual_label": label,
        "previsual_reason": reason,
    }


def queue_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    kind_order = {"HL": 0, "LH": 1}
    label_order = {
        "exact_match": 0,
        "family_match": 1,
        "pair_has_other_predicate": 2,
        "no_gt_for_pair": 3,
    }
    rank = row.get("semantic_rank")
    return (
        kind_order.get(str(row.get("queue_kind")), 9),
        label_order.get(str(row.get("label_match_status")), 9),
        str(row.get("predicate_family")),
        int(rank) if rank is not None else 10**9,
        str(row.get("prediction_id")),
    )


def enrich_rows(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    input_path = as_abs(args.input)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = sorted(read_jsonl(input_path), key=queue_sort_key)
    enriched: list[dict[str, Any]] = []
    counters: dict[str, Counter[Any]] = {
        "by_queue": Counter(),
        "by_label_match": Counter(),
        "by_family": Counter(),
        "by_working_label": Counter(),
        "by_confidence": Counter(),
        "by_asset_state": Counter(),
        "by_queue_working_label": Counter(),
        "by_family_working_label": Counter(),
        "by_label_match_working_label": Counter(),
    }
    human_field_non_null = Counter()
    contact_sheets_rendered = 0

    for idx, row in enumerate(rows, start=1):
        label, reason, confidence = working_label(row)
        subject_images, subject_image_count = find_instance_images(
            str(row["scan_id"]), int(row["subject_id"]), args.images_per_object
        )
        object_images, object_image_count = find_instance_images(
            str(row["scan_id"]), int(row["object_id"]), args.images_per_object
        )
        asset_state = (
            "subject_and_object_images"
            if subject_images and object_images
            else "missing_subject_or_object_images"
        )
        contact_sheet = None
        sheet_row = normalize_for_contact_sheet(row, label, reason)
        if args.render_contact_sheets and subject_images and object_images:
            sheet_name = (
                f"{idx:04d}_{safe_slug(row['queue_kind'])}_{safe_slug(row['scan_id'][:8])}_"
                f"{row['subject_id']}_{safe_slug(row['predicate_label'])}_{row['object_id']}.jpg"
            )
            sheet_path = output_dir / "contact_sheets" / sheet_name
            render_contact_sheet(sheet_row, subject_images, object_images, sheet_path)
            contact_sheet = rel_path(sheet_path)
            contact_sheets_rendered += 1

        audit_id = f"train_audit_{idx:04d}"
        audit_seed = row.get("audit_seed") or {}
        original_manual_fields = audit_seed.get("manual_fields") or {}
        for field, value in original_manual_fields.items():
            if value is not None:
                human_field_non_null[field] += 1

        enriched_row = {
            **row,
            "audit_id": audit_id,
            "visual_assets": {
                **scan_asset_paths(str(row["scan_id"])),
                "subject_images": [rel_path(path) for path in subject_images],
                "object_images": [rel_path(path) for path in object_images],
                "subject_image_count": subject_image_count,
                "object_image_count": object_image_count,
                "contact_sheet": contact_sheet,
            },
            "asset_state": asset_state,
            "working_audit": {
                "working_label": label,
                "working_label_reason": reason,
                "working_label_confidence": confidence,
                "paper_locked": False,
                "human_confirmed": False,
                "evidence_scope": (
                    "metadata, GT join status, deterministic geometry status, reason codes, "
                    "and generated visual asset links; no human visual confirmation"
                ),
                "allowed_labels": WORKING_LABELS,
            },
            "manual_fields": {
                "object_pair_valid": None,
                "predicate_visually_plausible": None,
                "geometry_witness_correct": None,
                "gt_annotation_missing_or_sparse": None,
                "ontology_or_granularity_issue": None,
                "segmentation_or_instance_issue": None,
                "final_audit_label": None,
                "notes": None,
            },
        }
        enriched.append(enriched_row)

        queue_kind = str(row.get("queue_kind"))
        label_match = str(row.get("label_match_status"))
        family = str(row.get("predicate_family"))
        counters["by_queue"][queue_kind] += 1
        counters["by_label_match"][label_match] += 1
        counters["by_family"][family] += 1
        counters["by_working_label"][label] += 1
        counters["by_confidence"][confidence] += 1
        counters["by_asset_state"][asset_state] += 1
        counters["by_queue_working_label"][(queue_kind, label)] += 1
        counters["by_family_working_label"][(family, label)] += 1
        counters["by_label_match_working_label"][(label_match, label)] += 1

    summary = {
        "schema_version": "h002_train_manual_audit_v0",
        "status": "ready",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_path": rel_path(input_path),
        "output_paths": {
            "review_queue": rel_path(output_dir / "review_queue.jsonl"),
            "working_labels": rel_path(output_dir / "working_labels.jsonl"),
            "manual_sheet": rel_path(output_dir / "manual_sheet.tsv"),
            "needs_human_confirmation": rel_path(output_dir / "needs_human_confirmation.jsonl"),
            "summary": rel_path(output_dir / "train_manual_audit_summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "contact_sheets": rel_path(output_dir / "contact_sheets"),
        },
        "counts": {
            "rows": len(enriched),
            "contact_sheets_rendered": contact_sheets_rendered,
            "by_queue": serial_counter(counters["by_queue"]),
            "by_label_match": serial_counter(counters["by_label_match"]),
            "by_family": serial_counter(counters["by_family"]),
            "by_working_label": serial_counter(counters["by_working_label"]),
            "by_confidence": serial_counter(counters["by_confidence"]),
            "by_asset_state": serial_counter(counters["by_asset_state"]),
            "human_manual_field_non_null": serial_counter(human_field_non_null),
        },
        "cross_tabs": {
            "queue_working_label": {
                f"{queue}|{label}": int(count)
                for (queue, label), count in sorted(counters["by_queue_working_label"].items())
            },
            "family_working_label": {
                f"{family}|{label}": int(count)
                for (family, label), count in sorted(counters["by_family_working_label"].items())
            },
            "label_match_working_label": {
                f"{label_match}|{label}": int(count)
                for (label_match, label), count in sorted(counters["by_label_match_working_label"].items())
            },
        },
        "rates": {
            "working_true_underconfidence_share": safe_rate(
                counters["by_working_label"]["true_underconfidence"], len(enriched)
            ),
            "working_annotation_sparsity_share": safe_rate(
                counters["by_working_label"]["annotation_sparsity"], len(enriched)
            ),
            "working_ontology_mismatch_share": safe_rate(
                counters["by_working_label"]["ontology_mismatch"], len(enriched)
            ),
            "working_dense_relation_noise_share": safe_rate(
                counters["by_working_label"]["dense_relation_noise"], len(enriched)
            ),
            "human_confirmed_share": 0.0,
        },
        "boundary": {
            "paper_locked": False,
            "human_visual_confirmation_done": False,
            "working_labels_are_machine_assisted": True,
            "manual_fields_remain_null": True,
            "claim_boundary": (
                "This artifact prepares and triages train audit rows. Working labels are not "
                "paper-final manual annotations and cannot train a final posterior without "
                "human confirmation or a separately declared weak-supervision boundary."
            ),
        },
    }
    return enriched, summary


def write_manual_sheet(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "audit_id",
        "queue_kind",
        "label_match_status",
        "predicate_family",
        "rank_band",
        "semantic_rank",
        "subject_label",
        "predicate_label",
        "object_label",
        "working_label",
        "working_label_confidence",
        "working_label_reason",
        "contact_sheet",
        "mesh_obj",
        "instance_ply",
        "prediction_id",
        "human_final_audit_label",
        "human_notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in rows:
            assets = row.get("visual_assets") or {}
            working = row.get("working_audit") or {}
            writer.writerow(
                {
                    "audit_id": row.get("audit_id"),
                    "queue_kind": row.get("queue_kind"),
                    "label_match_status": row.get("label_match_status"),
                    "predicate_family": row.get("predicate_family"),
                    "rank_band": row.get("rank_band"),
                    "semantic_rank": row.get("semantic_rank"),
                    "subject_label": row.get("subject_label"),
                    "predicate_label": row.get("predicate_label"),
                    "object_label": row.get("object_label"),
                    "working_label": working.get("working_label"),
                    "working_label_confidence": working.get("working_label_confidence"),
                    "working_label_reason": working.get("working_label_reason"),
                    "contact_sheet": assets.get("contact_sheet"),
                    "mesh_obj": assets.get("mesh_obj"),
                    "instance_ply": assets.get("instance_ply"),
                    "prediction_id": row.get("prediction_id"),
                    "human_final_audit_label": "",
                    "human_notes": "",
                }
            )


def markdown_table(counter: dict[str, int], headers: tuple[str, str]) -> list[str]:
    lines = [f"| {headers[0]} | {headers[1]} |", "| --- | ---: |"]
    for key, value in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{key}` | {value} |")
    return lines


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Train Manual Audit Preparation",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        summary["boundary"]["claim_boundary"],
        "",
        "## Counts",
        "",
        f"- Rows: `{summary['counts']['rows']}`",
        f"- Contact sheets rendered: `{summary['counts']['contact_sheets_rendered']}`",
        "- Human visual confirmation: `false`",
        "- Paper locked: `false`",
        "",
        "## Working Labels",
        "",
        *markdown_table(summary["counts"]["by_working_label"], ("Working label", "Rows")),
        "",
        "## Queue And Working Label",
        "",
        *markdown_table(summary["cross_tabs"]["queue_working_label"], ("Queue|label", "Rows")),
        "",
        "## Family And Working Label",
        "",
        *markdown_table(summary["cross_tabs"]["family_working_label"], ("Family|label", "Rows")),
        "",
        "## Asset State",
        "",
        *markdown_table(summary["counts"]["by_asset_state"], ("Asset state", "Rows")),
        "",
        "## Next Step",
        "",
        "Open `manual_sheet.tsv` and inspect the contact sheets before treating any working label as a human-confirmed audit label.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows, summary = enrich_rows(args)
    write_jsonl(output_dir / "review_queue.jsonl", rows)
    write_jsonl(output_dir / "working_labels.jsonl", rows)
    write_jsonl(output_dir / "needs_human_confirmation.jsonl", rows)
    write_manual_sheet(output_dir / "manual_sheet.tsv", rows)
    write_json(output_dir / "train_manual_audit_summary.json", summary)
    write_report(output_dir / "report.md", summary)

    print(
        f"status={summary['status']} rows={summary['counts']['rows']} "
        f"sheets={summary['counts']['contact_sheets_rendered']} "
        f"output={output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
