#!/usr/bin/env python3
"""Audit partial H002 full-train independent asset packets before label fill."""

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
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
PACKET_ROOT = RGA_ROOT / "independent_asset_packets"
DEFAULT_PACKET_MANIFEST = PACKET_ROOT / "packet_manifest.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "asset_packet_gap_audit"

SHEETS = [
    "blind_all_sheet_with_packets.tsv",
    "blind_priority_sheet_with_packets.tsv",
    "blind_support_contact_sheet_with_packets.tsv",
    "blind_relative_vertical_sheet_with_packets.tsv",
    "blind_proximity_sheet_with_packets.tsv",
]

GENERIC_ENDPOINT_LABELS = {
    "object",
    "objects",
    "item",
    "items",
    "clutter",
    "unknown",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-manifest", type=Path, default=DEFAULT_PACKET_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
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


def read_tsv(path: Path) -> list[dict[str, Any]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def missing_sides(row: dict[str, Any]) -> list[str]:
    sides = []
    if int(row.get("subject_image_count") or 0) <= 0:
        sides.append("subject")
    if int(row.get("object_image_count") or 0) <= 0:
        sides.append("object")
    return sides


def has_generic_missing_endpoint(row: dict[str, Any], sides: list[str]) -> bool:
    if "subject" in sides and str(row.get("subject_label", "")).lower() in GENERIC_ENDPOINT_LABELS:
        return True
    if "object" in sides and str(row.get("object_label", "")).lower() in GENERIC_ENDPOINT_LABELS:
        return True
    return False


def decide_packet(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("packet_status"))
    sides = missing_sides(row)
    contact_ready = bool(row.get("contact_sheet_ready"))
    mesh_ready = bool(row.get("mesh_packet_ready"))
    family = str(row.get("predicate_family"))

    if status == "ready":
        decision = "label_ready"
        reason = "complete packet: subject/object crops, contact/context sheet, and mesh packet are available"
        label_sheet_status = "ready"
    elif len(sides) >= 2:
        decision = "exclude_before_label_fill"
        reason = "both subject and object crops are missing; mesh-only evidence is too weak for independent label fill"
        label_sheet_status = "packet_gap_excluded"
    elif has_generic_missing_endpoint(row, sides):
        decision = "exclude_before_label_fill"
        reason = "missing endpoint has generic object label, so identity cannot be independently checked"
        label_sheet_status = "packet_gap_excluded"
    elif mesh_ready and contact_ready and len(sides) == 1:
        decision = "label_ready_with_packet_caveat"
        reason = (
            "one endpoint crop is missing, but mesh packet and contact/context sheet are available; "
            "labeler must use low confidence or abstain if identity is unclear"
        )
        label_sheet_status = "ready_with_packet_caveat"
    elif mesh_ready and family == "relative_vertical" and len(sides) == 1:
        decision = "label_ready_with_packet_caveat"
        reason = (
            "one endpoint crop is missing, but relative vertical evidence can be audited from mesh; "
            "labeler must use low confidence or abstain if identity is unclear"
        )
        label_sheet_status = "ready_with_packet_caveat"
    else:
        decision = "exclude_before_label_fill"
        reason = "insufficient visual/context evidence for independent label fill"
        label_sheet_status = "packet_gap_excluded"

    return {
        "blind_review_id": row["blind_review_id"],
        "asset_request_id": row["asset_request_id"],
        "packet_status": status,
        "packet_gap_decision": decision,
        "label_sheet_status": label_sheet_status,
        "packet_gap_reason": reason,
        "missing_sides": sides,
        "subject_image_count": row.get("subject_image_count"),
        "object_image_count": row.get("object_image_count"),
        "contact_sheet_ready": contact_ready,
        "mesh_packet_ready": mesh_ready,
        "scan_id": row.get("scan_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": family,
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "multiview_packet": row.get("multiview_packet"),
        "pointcloud_or_mesh_packet": row.get("pointcloud_or_mesh_packet"),
        "contact_or_context_sheet": row.get("contact_or_context_sheet"),
    }


def apply_decisions_to_sheet(sheet_path: Path, output_dir: Path, decisions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = read_tsv(sheet_path)
    updated_rows = []
    excluded_rows = []
    for row in rows:
        decision = decisions.get(str(row.get("blind_review_id")))
        if not decision:
            continue
        row["packet_gap_decision"] = decision["packet_gap_decision"]
        row["packet_gap_reason"] = decision["packet_gap_reason"]
        row["evidence_packet_status"] = decision["label_sheet_status"]
        if decision["packet_gap_decision"] == "exclude_before_label_fill":
            excluded_rows.append(row)
        else:
            updated_rows.append(row)
    output_path = output_dir / sheet_path.name.replace("blind_", "label_ready_")
    exclude_path = output_dir / sheet_path.name.replace("blind_", "excluded_")
    write_tsv(output_path, updated_rows)
    write_tsv(exclude_path, excluded_rows)
    return {
        "source_sheet": rel_path(sheet_path),
        "label_ready_sheet": rel_path(output_path),
        "excluded_sheet": rel_path(exclude_path),
        "source_rows": len(rows),
        "label_ready_rows": len(updated_rows),
        "excluded_rows": len(excluded_rows),
        "status_counts": dict(sorted(Counter(row["evidence_packet_status"] for row in updated_rows).items())),
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Full Train Asset Packet Gap Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage audit.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- This decides packet usability before independent label fill.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Decision Counts",
        "",
        "| Decision | Rows |",
        "| --- | ---: |",
    ]
    for key, value in summary["decision_counts"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Partial Row Decisions",
            "",
            "| Blind ID | Family | Predicate | Missing Sides | Decision |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in summary["partial_decisions"]:
        sides = ",".join(row["missing_sides"]) if row["missing_sides"] else "none"
        lines.append(
            f"| `{row['blind_review_id']}` | `{row['predicate_family']}` | `{row['predicate_label']}` | "
            f"`{sides}` | `{row['packet_gap_decision']}` |"
        )
    lines.extend(
        [
            "",
            "## Label-Ready Sheets",
            "",
            "| Sheet | Label-Ready | Excluded |",
            "| --- | ---: | ---: |",
        ]
    )
    for sheet in summary["sheet_outputs"]:
        lines.append(f"| `{sheet['label_ready_sheet']}` | {sheet['label_ready_rows']} | {sheet['excluded_rows']} |")
    lines.extend(
        [
            "",
            "## Next TODO",
            "",
            summary["next_todo"],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    packet_rows = read_jsonl(args.packet_manifest)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    decisions = [decide_packet(row) for row in packet_rows]
    decision_by_id = {row["blind_review_id"]: row for row in decisions}
    partial_decisions = [row for row in decisions if row["packet_status"] != "ready"]
    label_ready_rows = [row for row in decisions if row["packet_gap_decision"] != "exclude_before_label_fill"]
    excluded_rows = [row for row in decisions if row["packet_gap_decision"] == "exclude_before_label_fill"]

    write_jsonl(output_dir / "gap_decisions.jsonl", decisions)
    write_jsonl(output_dir / "label_ready_packet_rows.jsonl", label_ready_rows)
    write_jsonl(output_dir / "excluded_packet_rows.jsonl", excluded_rows)
    (output_dir / "excluded_blind_ids.txt").write_text(
        "\n".join(row["blind_review_id"] for row in excluded_rows) + ("\n" if excluded_rows else ""),
        encoding="utf-8",
    )

    sheet_outputs = []
    for sheet_name in SHEETS:
        sheet_path = PACKET_ROOT / sheet_name
        if sheet_path.exists():
            sheet_outputs.append(apply_decisions_to_sheet(sheet_path, output_dir, decision_by_id))

    decision_counts = dict(sorted(Counter(row["packet_gap_decision"] for row in decisions).items()))
    family_decision_counts = {
        f"{family}:{decision}": value
        for (family, decision), value in sorted(Counter((row["predicate_family"], row["packet_gap_decision"]) for row in decisions).items())
    }
    status = (
        "full_train_asset_packet_gap_audit_ready_for_label_readiness"
        if len(label_ready_rows) >= 300 and len(sheet_outputs) == len(SHEETS)
        else "full_train_asset_packet_gap_audit_needs_more_assets"
    )
    next_todo = (
        "full_train_independent_label_readiness: validate label-ready sheets and ingestion schema before label fill."
        if status == "full_train_asset_packet_gap_audit_ready_for_label_readiness"
        else "recover_or_replace_excluded_asset_packets"
    )
    summary = {
        "schema_version": "h002_full_train_asset_packet_gap_audit_summary_v0",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "packet_manifest": rel_path(args.packet_manifest),
        },
        "output_dir": rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "vmv_model_input_allowed": False,
        },
        "rows": len(decisions),
        "label_ready_rows": len(label_ready_rows),
        "excluded_rows": len(excluded_rows),
        "partial_rows": len(partial_decisions),
        "decision_counts": decision_counts,
        "family_decision_counts": family_decision_counts,
        "partial_decisions": partial_decisions,
        "sheet_outputs": sheet_outputs,
        "artifacts": {
            "gap_decisions": rel_path(output_dir / "gap_decisions.jsonl"),
            "label_ready_packet_rows": rel_path(output_dir / "label_ready_packet_rows.jsonl"),
            "excluded_packet_rows": rel_path(output_dir / "excluded_packet_rows.jsonl"),
            "excluded_blind_ids": rel_path(output_dir / "excluded_blind_ids.txt"),
        },
        "next_todo": next_todo,
    }
    write_json(output_dir / "summary.json", summary)
    write_report(output_dir / "report.md", summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        f"status={summary['status']} rows={summary['rows']} "
        f"label_ready={summary['label_ready_rows']} excluded={summary['excluded_rows']} "
        f"partial={summary['partial_rows']} validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
