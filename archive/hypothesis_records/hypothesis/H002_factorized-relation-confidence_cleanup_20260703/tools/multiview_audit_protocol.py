#!/usr/bin/env python3
"""Create H002 multi-view audit protocol artifacts without adding model inputs."""

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
DEFAULT_STRICT_QUEUE = DEFAULT_PROTOCOL_DIR / "strict_review_queue.jsonl"
DEFAULT_WEAK_QUEUE = DEFAULT_PROTOCOL_DIR / "weak_extension_queue.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "multiview_audit_protocol"

AUDIT_FIELDS = {
    "reviewer_id": "free text; required for completed audit",
    "review_round": "integer; required for completed audit",
    "subject_visibility": "good/partial/poor/not_visible/uncertain",
    "object_visibility": "good/partial/poor/not_visible/uncertain",
    "pair_covisible": "yes/no/uncertain",
    "pair_context_sufficient": "yes/no/uncertain",
    "visual_relation_support": "supports/contradicts/uncertain/not_evaluable",
    "visual_informativeness": "informative/trivial_dense/uncertain/not_evaluable",
    "occlusion_or_truncation_issue": "yes/no/uncertain",
    "crop_quality": "good/usable/poor/uncertain",
    "final_visual_audit_decision": (
        "confirm_reliable_promote/confirm_dense_noise/relabel_or_ontology/"
        "invalid_pair/visibility_or_geometry_artifact/abstain_uncertain"
    ),
    "confidence": "high/medium/low",
    "notes": "free text",
}

PROMOTION_GATES = {
    "current_h002_first": [
        "validate S_e + G_e + C_e + U_e with independent or human-confirmed labels",
        "run semantic_only, geometry_only, semantic_plus_geometry, factorized posterior",
        "pass same-family, same-geometry-status, and same-rank-band controls",
        "do not use V_mv_e as deployable model input before this gate",
    ],
    "multiview_audit_only_now": [
        "use contact sheets and multi-view crops to confirm labels",
        "separate visual audit decisions from deployable input features",
        "do not report visual-factor performance",
    ],
    "future_vmv_promotion": [
        "define V_mv_e feature contract",
        "add wrong-pair view, shuffled-view, shuffled-geometry, and low-visibility controls",
        "promote only after target independence and label quality gates pass",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict-queue", type=Path, default=DEFAULT_STRICT_QUEUE)
    parser.add_argument("--weak-queue", type=Path, default=DEFAULT_WEAK_QUEUE)
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


def asset(row: dict[str, Any], key: str) -> Any:
    return (row.get("visual_assets") or {}).get(key)


def queue_row(row: dict[str, Any], queue_name: str, priority_rank: int) -> dict[str, Any]:
    visual_assets = row.get("visual_assets") or {}
    return {
        "schema_version": "h002_multiview_audit_row_v0",
        "queue_name": queue_name,
        "priority_rank": priority_rank,
        "prediction_id": row["prediction_id"],
        "scan_id": row["scan_id"],
        "subgraph_id": row["subgraph_id"],
        "subject_id": row["subject_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "object_id": row["object_id"],
        "object_label": row["object_label"],
        "working_label": row["working_label"],
        "geometry_status": row["geometry_status"],
        "rank_bucket": row["rank_bucket"],
        "semantic_score_raw": row["semantic_score_raw"],
        "semantic_score_norm": row["semantic_score_norm"],
        "p_geom_valid": row["p_geom_valid"],
        "consistency_score": row["consistency_score"],
        "geometry_residual_proxy": row["geometry_residual_proxy"],
        "visual_assets": visual_assets,
        "audit_fields": {field: None for field in AUDIT_FIELDS},
        "boundary": "multi-view audit evidence only; not deployable model input",
    }


def sheet_row(row: dict[str, Any]) -> dict[str, Any]:
    visual_assets = row.get("visual_assets") or {}
    flat = {
        "queue_name": row["queue_name"],
        "priority_rank": row["priority_rank"],
        "prediction_id": row["prediction_id"],
        "scan_id": row["scan_id"],
        "subject_id": row["subject_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "object_id": row["object_id"],
        "object_label": row["object_label"],
        "working_label": row["working_label"],
        "geometry_status": row["geometry_status"],
        "rank_bucket": row["rank_bucket"],
        "semantic_score_raw": row["semantic_score_raw"],
        "semantic_score_norm": row["semantic_score_norm"],
        "p_geom_valid": row["p_geom_valid"],
        "contact_sheet": visual_assets.get("contact_sheet"),
        "subject_image_count": visual_assets.get("subject_image_count"),
        "object_image_count": visual_assets.get("object_image_count"),
        "subject_image_1": (visual_assets.get("subject_images") or [None, None])[0],
        "subject_image_2": (visual_assets.get("subject_images") or [None, None])[1]
        if len(visual_assets.get("subject_images") or []) > 1
        else None,
        "object_image_1": (visual_assets.get("object_images") or [None, None])[0],
        "object_image_2": (visual_assets.get("object_images") or [None, None])[1]
        if len(visual_assets.get("object_images") or []) > 1
        else None,
        "mesh_obj": visual_assets.get("mesh_obj"),
    }
    flat.update({field: "" for field in AUDIT_FIELDS})
    return flat


def write_sheet(path: Path, rows: list[dict[str, Any]]) -> None:
    columns = [
        "queue_name",
        "priority_rank",
        "prediction_id",
        "scan_id",
        "subject_id",
        "subject_label",
        "predicate_label",
        "predicate_family",
        "object_id",
        "object_label",
        "working_label",
        "geometry_status",
        "rank_bucket",
        "semantic_score_raw",
        "semantic_score_norm",
        "p_geom_valid",
        "contact_sheet",
        "subject_image_count",
        "object_image_count",
        "subject_image_1",
        "subject_image_2",
        "object_image_1",
        "object_image_2",
        "mesh_obj",
        *AUDIT_FIELDS.keys(),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(sheet_row(row))


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "queue_counts": dict(Counter(row["queue_name"] for row in rows)),
        "family_counts": dict(Counter(row["predicate_family"] for row in rows)),
        "predicate_counts": dict(Counter(row["predicate_label"] for row in rows)),
        "working_label_counts": dict(Counter(row["working_label"] for row in rows)),
        "contact_sheet_count": sum(1 for row in rows if asset(row, "contact_sheet")),
        "mesh_obj_count": sum(1 for row in rows if asset(row, "mesh_obj")),
        "subject_image_count_min": min((asset(row, "subject_image_count") or 0) for row in rows) if rows else 0,
        "subject_image_count_max": max((asset(row, "subject_image_count") or 0) for row in rows) if rows else 0,
        "object_image_count_min": min((asset(row, "object_image_count") or 0) for row in rows) if rows else 0,
        "object_image_count_max": max((asset(row, "object_image_count") or 0) for row in rows) if rows else 0,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Multi-View Audit Protocol",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Multi-view is audit/confirmation evidence only in this stage.",
        "- No `V_mv_e` deployable model input is created.",
        "- No validation/test rows are used.",
        "- Factorized posterior validation with `S_e, G_e, C_e, U_e` remains the first method gate.",
        "",
        "## Queues",
        "",
        "| Queue | Rows |",
        "| --- | ---: |",
    ]
    for queue_name, count in summary["counts"]["all_candidates"]["queue_counts"].items():
        lines.append(f"| `{queue_name}` | {count} |")
    lines.extend(
        [
            "",
            "## Asset Coverage",
            "",
            "| Sheet | Rows | Contact sheets | Mesh links | Subject image count | Object image count |",
            "| --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for key in ["primary_strict", "support_contact_extension", "all_candidates"]:
        counts = summary["counts"][key]
        lines.append(
            f"| `{key}` | {counts['rows']} | {counts['contact_sheet_count']} | "
            f"{counts['mesh_obj_count']} | {counts['subject_image_count_min']}-{counts['subject_image_count_max']} | "
            f"{counts['object_image_count_min']}-{counts['object_image_count_max']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "`V_mv_e` is deferred. Use these sheets to improve label confirmation before",
            "adding visual evidence as a model feature.",
            "",
            "Next gate: `35_factorized_validation_plan.md`.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    strict_rows = read_jsonl(args.strict_queue)
    weak_rows = read_jsonl(args.weak_queue)

    primary = [queue_row(row, "primary_strict_current_target", 1) for row in strict_rows]
    support = [
        queue_row(row, "extension_support_contact_future_family", 2)
        for row in weak_rows
        if row["predicate_family"] == "support_contact"
    ]
    relative = [
        queue_row(row, "extension_relative_vertical_lower_priority", 3)
        for row in weak_rows
        if row["predicate_family"] == "relative_vertical"
    ]
    proximity = [
        queue_row(row, "extension_proximity_duplicate_context", 4)
        for row in weak_rows
        if row["predicate_family"] == "proximity"
    ]
    all_candidates = primary + support + relative

    paths = {
        "summary": output_dir / "summary.json",
        "protocol": output_dir / "protocol.json",
        "primary_queue": output_dir / "primary_strict_queue.jsonl",
        "support_contact_queue": output_dir / "support_contact_extension_queue.jsonl",
        "all_candidate_queue": output_dir / "all_candidate_queue.jsonl",
        "primary_sheet": output_dir / "primary_strict_sheet.tsv",
        "support_contact_sheet": output_dir / "support_contact_sheet.tsv",
        "all_candidate_sheet": output_dir / "all_candidate_sheet.tsv",
        "report": output_dir / "report.md",
    }
    created_at = datetime.now(timezone.utc).isoformat()
    protocol = {
        "schema_version": "h002_multiview_audit_protocol_v0",
        "created_at": created_at,
        "decision": "defer_vmv_model_input_until_current_factorized_posterior_is_validated",
        "posterior_now": "P(R_e = 1 | S_e, G_e, C_e, U_e)",
        "posterior_future": "P(R_e = 1 | S_e, G_3D_e, V_mv_e, C_e, U_e)",
        "audit_fields": AUDIT_FIELDS,
        "promotion_gates": PROMOTION_GATES,
        "controls_required_before_vmv_model_input": [
            "wrong_pair_view",
            "shuffled_view",
            "shuffled_geometry",
            "no_view_or_low_visibility",
            "same_family",
            "same_geometry_status",
            "same_rank_band",
        ],
        "claim_boundary": {
            "uses_validation_rows": False,
            "creates_deployable_visual_features": False,
            "paper_result": False,
            "posterior_claim_allowed": False,
        },
    }
    summary = {
        "schema_version": "h002_multiview_audit_protocol_summary_v0",
        "status": "ready_audit_only_vmv_deferred",
        "created_at": created_at,
        "input_paths": {
            "strict_queue": rel_path(args.strict_queue),
            "weak_queue": rel_path(args.weak_queue),
        },
        "output_paths": {key: rel_path(path) for key, path in paths.items()},
        "counts": {
            "primary_strict": summarize(primary),
            "support_contact_extension": summarize(support),
            "relative_vertical_extension": summarize(relative),
            "all_candidates": summarize(all_candidates),
            "weak_proximity_duplicate_context": summarize(proximity),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "paper_result": False,
            "deployable_vmv_features_created": False,
            "model_input_expansion_allowed_now": False,
            "posterior_claim_allowed": False,
        },
        "next_gate": "35_factorized_validation_plan.md",
    }
    write_json(paths["protocol"], protocol)
    write_json(paths["summary"], summary)
    write_jsonl(paths["primary_queue"], primary)
    write_jsonl(paths["support_contact_queue"], support)
    write_jsonl(paths["all_candidate_queue"], all_candidates)
    write_sheet(paths["primary_sheet"], primary)
    write_sheet(paths["support_contact_sheet"], support)
    write_sheet(paths["all_candidate_sheet"], all_candidates)
    write_report(paths["report"], summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    counts = summary["counts"]
    print(
        f"status={summary['status']} primary={counts['primary_strict']['rows']} "
        f"support={counts['support_contact_extension']['rows']} "
        f"all={counts['all_candidates']['rows']} "
        f"vmv_input={summary['boundary']['deployable_vmv_features_created']} "
        f"validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
