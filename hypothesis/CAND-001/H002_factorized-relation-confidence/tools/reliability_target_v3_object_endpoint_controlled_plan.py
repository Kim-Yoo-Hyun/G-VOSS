#!/usr/bin/env python3
"""Plan object/endpoint-controlled sampling for H002 reliability target v3."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PATH_DECISION = RGA_ROOT / "reliability_target_v3_path_decision_codex_proxy_user_requested/summary.json"
DEFAULT_PACKET_MANIFEST = RGA_ROOT / "independent_asset_packets/packet_manifest.jsonl"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v3_object_endpoint_controlled_plan"

SELECTED_FAMILIES = {"support_contact", "relative_vertical"}
STRUCTURAL_OR_TRIVIAL_LABELS = {
    "floor",
    "wall",
    "ceiling",
    "room",
    "door",
    "window",
    "cabinet",
    "kitchen cabinet",
    "shelf",
    "table",
    "desk",
    "chair",
    "stool",
    "counter",
    "countertop",
}

TARGET_LABEL_ROWS = 160
PER_CELL_CLASS_CAP = 6


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-decision", type=Path, default=DEFAULT_PATH_DECISION)
    parser.add_argument("--packet-manifest", type=Path, default=DEFAULT_PACKET_MANIFEST)
    parser.add_argument("--hl-queue", type=Path, default=DEFAULT_HL_QUEUE)
    parser.add_argument("--lh-queue", type=Path, default=DEFAULT_LH_QUEUE)
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


def iter_jsonl(path: Path):
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def norm_label(value: Any) -> str:
    return str(value or "").strip().lower()


def packet_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("scan_id")),
        str(row.get("subject_id")),
        str(row.get("object_id")),
        str(row.get("predicate_label")),
    )


def packet_ready(row: dict[str, Any]) -> bool:
    return (
        row.get("packet_status") == "ready"
        and bool(row.get("multiview_packet"))
        and bool(row.get("pointcloud_or_mesh_packet"))
        and bool(row.get("contact_or_context_sheet"))
    )


def endpoint_flag_pattern(row: dict[str, Any]) -> str:
    subject = norm_label(row.get("subject_label"))
    obj = norm_label(row.get("object_label"))
    family = str(row.get("predicate_family"))
    return "|".join(
        [
            f"subject_structural={int(subject in STRUCTURAL_OR_TRIVIAL_LABELS)}",
            f"object_structural={int(obj in STRUCTURAL_OR_TRIVIAL_LABELS)}",
            f"same_label={int(subject == obj)}",
            f"support_contact={int(family == 'support_contact')}",
            f"relative_vertical={int(family == 'relative_vertical')}",
        ]
    )


def proxy_class(row: dict[str, Any]) -> str:
    queue = str(row.get("queue_kind") or row.get("source_queue") or "")
    geometry = str(row.get("geometry_status") or row.get("h001_verification_status") or "")
    if queue == "LH" and geometry == "satisfied":
        return "candidate_positive_proxy"
    if queue == "HL" and geometry in {"unsatisfied", "violated"}:
        return "candidate_negative_proxy"
    if queue == "LH":
        return "candidate_positive_proxy"
    if queue == "HL":
        return "candidate_negative_proxy"
    return "candidate_uncertain_proxy"


def load_ready_packets(path: Path) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    packets = {}
    for row in iter_jsonl(path):
        if packet_ready(row):
            packets[packet_key(row)] = row
    return packets


def normalize_row(row: dict[str, Any], packet: dict[str, Any], source_queue: str) -> dict[str, Any]:
    normalized = {
        "prediction_id": row.get("prediction_id"),
        "source_id": row.get("source_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "scene_context_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "packet_status": packet.get("packet_status"),
        "multiview_packet": packet.get("multiview_packet", ""),
        "pointcloud_or_mesh_packet": packet.get("pointcloud_or_mesh_packet", ""),
        "contact_or_context_sheet": packet.get("contact_or_context_sheet", ""),
        "original_blind_review_id": packet.get("blind_review_id", ""),
        "queue_kind_hidden": source_queue,
        "source_queue_hidden": source_queue,
        "rank_band_hidden": row.get("rank_band"),
        "semantic_rank_hidden": row.get("semantic_rank"),
        "semantic_score_norm_hidden": row.get("semantic_score_norm"),
        "semantic_score_raw_hidden": row.get("semantic_score_raw"),
        "p_geom_valid_hidden": row.get("p_geom_valid"),
        "geometry_status_hidden": row.get("geometry_status"),
        "h001_verification_status_hidden": row.get("h001_verification_status"),
        "label_match_status_hidden": row.get("label_match_status"),
        "label_geometry_bucket_hidden": row.get("label_geometry_bucket"),
        "machine_hint_hidden": row.get("machine_hint"),
        "matched_predicates_hidden": row.get("matched_predicates", []),
        "reason_codes_hidden": row.get("reason_codes", []),
    }
    normalized["endpoint_flag_pattern_hidden"] = endpoint_flag_pattern(row)
    normalized["candidate_proxy_class_hidden"] = proxy_class({**row, "queue_kind": source_queue})
    normalized["subject_object_family_cell"] = "|".join(
        [
            str(normalized["subject_label"]),
            str(normalized["object_label"]),
            str(normalized["predicate_family"]),
        ]
    )
    normalized["subject_object_cell"] = "|".join(
        [str(normalized["subject_label"]), str(normalized["object_label"])]
    )
    normalized["object_family_cell"] = "|".join(
        [str(normalized["object_label"]), str(normalized["predicate_family"])]
    )
    normalized["object_predicate_cell"] = "|".join(
        [str(normalized["object_label"]), str(normalized["predicate_label"])]
    )
    normalized["endpoint_family_cell"] = "|".join(
        [str(normalized["endpoint_flag_pattern_hidden"]), str(normalized["predicate_family"])]
    )
    return normalized


def load_candidate_rows(hl_queue: Path, lh_queue: Path, packets: dict[tuple[str, str, str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_queue, path in [("HL", hl_queue), ("LH", lh_queue)]:
        for row in iter_jsonl(path):
            if row.get("predicate_family") not in SELECTED_FAMILIES:
                continue
            packet = packets.get(packet_key(row))
            if packet is None:
                continue
            rows.append(normalize_row(row, packet, source_queue))
    return rows


def summarize_cells(
    rows: list[dict[str, Any]],
    cell_type: str,
    key_fn: Callable[[dict[str, Any]], str],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[key_fn(row)].append(row)
    summaries: list[dict[str, Any]] = []
    for key, cell_rows in grouped.items():
        classes = Counter(row["candidate_proxy_class_hidden"] for row in cell_rows)
        pos = classes.get("candidate_positive_proxy", 0)
        neg = classes.get("candidate_negative_proxy", 0)
        summary = {
            "cell_type": cell_type,
            "cell_key": key,
            "rows": len(cell_rows),
            "candidate_positive_proxy": pos,
            "candidate_negative_proxy": neg,
            "candidate_uncertain_proxy": classes.get("candidate_uncertain_proxy", 0),
            "min_binary_class": min(pos, neg),
            "positive_proxy_rate": pos / (pos + neg) if pos + neg else 0.0,
            "unique_scans": len({str(row.get("scan_id")) for row in cell_rows}),
            "predicate_families": dict(Counter(str(row.get("predicate_family")) for row in cell_rows)),
            "predicate_labels": dict(Counter(str(row.get("predicate_label")) for row in cell_rows)),
            "subject_labels": dict(Counter(str(row.get("subject_label")) for row in cell_rows).most_common(5)),
            "object_labels": dict(Counter(str(row.get("object_label")) for row in cell_rows).most_common(5)),
            "eligible_binary_cell": pos > 0 and neg > 0,
            "strong_binary_cell": len(cell_rows) >= 6 and pos >= 2 and neg >= 2,
        }
        summaries.append(summary)
    summaries.sort(key=lambda row: (-row["strong_binary_cell"], -row["min_binary_class"], -row["rows"], row["cell_key"]))
    return summaries


def csv_ready_cell(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "cell_type": summary["cell_type"],
        "cell_key": summary["cell_key"],
        "rows": summary["rows"],
        "candidate_positive_proxy": summary["candidate_positive_proxy"],
        "candidate_negative_proxy": summary["candidate_negative_proxy"],
        "candidate_uncertain_proxy": summary["candidate_uncertain_proxy"],
        "min_binary_class": summary["min_binary_class"],
        "positive_proxy_rate": f"{summary['positive_proxy_rate']:.4f}",
        "unique_scans": summary["unique_scans"],
        "eligible_binary_cell": summary["eligible_binary_cell"],
        "strong_binary_cell": summary["strong_binary_cell"],
        "predicate_families": json.dumps(summary["predicate_families"], sort_keys=True),
        "predicate_labels": json.dumps(summary["predicate_labels"], sort_keys=True),
        "subject_labels": json.dumps(summary["subject_labels"], sort_keys=True),
        "object_labels": json.dumps(summary["object_labels"], sort_keys=True),
    }


def allocate_cells(
    summaries: list[dict[str, Any]],
    *,
    tier: str,
    cell_type: str,
    max_cells: int,
    include_weak: bool = False,
) -> list[dict[str, Any]]:
    selected = []
    for summary in summaries:
        if summary["cell_type"] != cell_type:
            continue
        if not summary["eligible_binary_cell"]:
            continue
        if not include_weak and not summary["strong_binary_cell"]:
            continue
        pos_take = min(summary["candidate_positive_proxy"], PER_CELL_CLASS_CAP)
        neg_take = min(summary["candidate_negative_proxy"], PER_CELL_CLASS_CAP)
        if pos_take == 0 or neg_take == 0:
            continue
        selected.append(
            {
                "tier": tier,
                "cell_type": cell_type,
                "cell_key": summary["cell_key"],
                "available_rows": summary["rows"],
                "available_positive_proxy": summary["candidate_positive_proxy"],
                "available_negative_proxy": summary["candidate_negative_proxy"],
                "suggested_positive_proxy": pos_take,
                "suggested_negative_proxy": neg_take,
                "suggested_total": pos_take + neg_take,
                "unique_scans": summary["unique_scans"],
                "reason": "matched positive/negative proxy rows inside this control cell",
            }
        )
        if len(selected) >= max_cells:
            break
    return selected


def build_recommended_cells(cell_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    recommendations.extend(
        allocate_cells(
            cell_summaries,
            tier="T1_strict_subject_object_family",
            cell_type="subject_object_family",
            max_cells=12,
            include_weak=True,
        )
    )
    recommendations.extend(
        allocate_cells(
            cell_summaries,
            tier="T2_object_family_fallback",
            cell_type="object_family",
            max_cells=12,
            include_weak=False,
        )
    )
    recommendations.extend(
        allocate_cells(
            cell_summaries,
            tier="T3_endpoint_family_balance",
            cell_type="endpoint_family",
            max_cells=12,
            include_weak=False,
        )
    )
    return recommendations


def aggregate_recommendations(recommendations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_tier: dict[str, dict[str, Any]] = {}
    for row in recommendations:
        tier = row["tier"]
        agg = by_tier.setdefault(
            tier,
            {
                "tier": tier,
                "cells": 0,
                "suggested_positive_proxy": 0,
                "suggested_negative_proxy": 0,
                "suggested_total": 0,
            },
        )
        agg["cells"] += 1
        agg["suggested_positive_proxy"] += int(row["suggested_positive_proxy"])
        agg["suggested_negative_proxy"] += int(row["suggested_negative_proxy"])
        agg["suggested_total"] += int(row["suggested_total"])
    return list(by_tier.values())


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Reliability Target V3 Object/Endpoint-Controlled Plan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only planning artifact.",
        "- No validation/test rows are used.",
        "- No labels are filled.",
        "- No posterior is trained.",
        "- H001 artifacts are not modified.",
        "- Multi-view remains audit/label evidence, not model input.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "Decision:",
        "",
        summary["decision"],
        "",
        "## Candidate Inventory",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| packet-ready support/vertical rows | {summary['candidate_inventory']['packet_ready_support_vertical_rows']} |",
        f"| candidate-positive proxy rows | {summary['candidate_inventory']['candidate_positive_proxy']} |",
        f"| candidate-negative proxy rows | {summary['candidate_inventory']['candidate_negative_proxy']} |",
        f"| support_contact rows | {summary['candidate_inventory']['support_contact_rows']} |",
        f"| relative_vertical rows | {summary['candidate_inventory']['relative_vertical_rows']} |",
        "",
        "## Cell Feasibility",
        "",
        "| Cell Type | Cells | Eligible Cells | Strong Cells | Eligible Rows | Pos Proxy | Neg Proxy |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["cell_feasibility"]:
        lines.append(
            f"| `{row['cell_type']}` | {row['cells']} | {row['eligible_cells']} | {row['strong_cells']} | "
            f"{row['eligible_rows']} | {row['eligible_positive_proxy']} | {row['eligible_negative_proxy']} |"
        )
    lines.extend(
        [
            "",
            "## Recommended Sampling Tiers",
            "",
            "| Tier | Cells | Suggested Pos Proxy | Suggested Neg Proxy | Suggested Total |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["recommended_tier_summary"]:
        lines.append(
            f"| `{row['tier']}` | {row['cells']} | {row['suggested_positive_proxy']} | "
            f"{row['suggested_negative_proxy']} | {row['suggested_total']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Strict `subject_label/object_label/predicate_family` cells exist, but they are too sparse to fill a full target alone.",
            "- `object_family` and `endpoint_family` fallback tiers are required to reach a practical label pool while keeping shortcut controls explicit.",
            "- Candidate-positive and candidate-negative proxy labels are sampling strata only. They are not target labels.",
            "- The next step should mine a label sheet from these cells, then fill v3 labels and rerun target-independence audit.",
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    path_decision = read_json(args.path_decision)
    packets = load_ready_packets(args.packet_manifest)
    candidates = load_candidate_rows(args.hl_queue, args.lh_queue, packets)

    cell_specs: list[tuple[str, Callable[[dict[str, Any]], str]]] = [
        ("subject_object_family", lambda row: row["subject_object_family_cell"]),
        ("subject_object", lambda row: row["subject_object_cell"]),
        ("object_family", lambda row: row["object_family_cell"]),
        ("object_predicate", lambda row: row["object_predicate_cell"]),
        ("endpoint_family", lambda row: row["endpoint_family_cell"]),
        ("predicate_label", lambda row: str(row["predicate_label"])),
    ]
    all_cell_summaries: list[dict[str, Any]] = []
    cell_feasibility: list[dict[str, Any]] = []
    for cell_type, key_fn in cell_specs:
        summaries = summarize_cells(candidates, cell_type, key_fn)
        all_cell_summaries.extend(summaries)
        eligible = [row for row in summaries if row["eligible_binary_cell"]]
        strong = [row for row in summaries if row["strong_binary_cell"]]
        cell_feasibility.append(
            {
                "cell_type": cell_type,
                "cells": len(summaries),
                "eligible_cells": len(eligible),
                "strong_cells": len(strong),
                "eligible_rows": sum(row["rows"] for row in eligible),
                "eligible_positive_proxy": sum(row["candidate_positive_proxy"] for row in eligible),
                "eligible_negative_proxy": sum(row["candidate_negative_proxy"] for row in eligible),
            }
        )

    recommendations = build_recommended_cells(all_cell_summaries)
    recommended_tier_summary = aggregate_recommendations(recommendations)

    class_counts = Counter(row["candidate_proxy_class_hidden"] for row in candidates)
    family_counts = Counter(row["predicate_family"] for row in candidates)

    strict_feasibility = next(row for row in cell_feasibility if row["cell_type"] == "subject_object_family")
    if strict_feasibility["eligible_rows"] >= TARGET_LABEL_ROWS:
        plan_status = "h002_reliability_target_v3_object_endpoint_controlled_plan_ready_strict_cells_sufficient"
    else:
        plan_status = "h002_reliability_target_v3_object_endpoint_controlled_plan_ready_broader_mining_required"

    summary = {
        "schema_version": "h002_reliability_target_v3_object_endpoint_controlled_plan_summary_v1",
        "created_at": created_at,
        "status": plan_status,
        "decision": (
            "Use a multi-tier object/endpoint-controlled sampling contract. Strict subject/object/family cells are "
            "preferred but insufficient alone, so the next candidate mining step must combine strict matched cells, "
            "object-family fallback cells, and endpoint-family balancing cells."
        ),
        "path_decision_status": path_decision.get("status"),
        "path_decision_selected": path_decision.get("selected_path"),
        "posterior_allowed": False,
        "validation_used": False,
        "test_used": False,
        "multi_view_as_model_input": False,
        "next_todo": "reliability_target_v3_object_endpoint_candidate_mining",
        "input_paths": {
            "path_decision": rel_path(args.path_decision),
            "packet_manifest": rel_path(args.packet_manifest),
            "hl_queue": rel_path(args.hl_queue),
            "lh_queue": rel_path(args.lh_queue),
        },
        "candidate_inventory": {
            "ready_packets": len(packets),
            "packet_ready_support_vertical_rows": len(candidates),
            "candidate_positive_proxy": class_counts.get("candidate_positive_proxy", 0),
            "candidate_negative_proxy": class_counts.get("candidate_negative_proxy", 0),
            "candidate_uncertain_proxy": class_counts.get("candidate_uncertain_proxy", 0),
            "support_contact_rows": family_counts.get("support_contact", 0),
            "relative_vertical_rows": family_counts.get("relative_vertical", 0),
        },
        "cell_feasibility": cell_feasibility,
        "recommended_tier_summary": recommended_tier_summary,
        "target_label_rows": TARGET_LABEL_ROWS,
        "sampling_contract": {
            "primary_tier": "T1_strict_subject_object_family",
            "fallback_tiers": ["T2_object_family_fallback", "T3_endpoint_family_balance"],
            "candidate_proxy_labels_are_sampling_strata_only": True,
            "labeler_visible_forbidden_fields": [
                "candidate_proxy_class",
                "queue_kind",
                "rank_band",
                "sampling_category",
                "expected_role",
                "geometry_status",
                "p_geom_valid",
                "semantic_score",
                "semantic_rank",
                "label_match_status",
                "endpoint_flag_pattern",
            ],
            "post_label_audit_required": [
                "hidden provenance risk",
                "endpoint pattern risk",
                "construction risk",
                "visible object identity risk",
                "visible relation surface risk",
                "geometry alignment risk",
                "scan/group leakage risk",
            ],
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "candidate_pool_internal_preview": rel_path(output_dir / "candidate_pool_internal_preview.jsonl"),
            "cell_inventory": rel_path(output_dir / "cell_inventory.csv"),
            "recommended_sampling_cells": rel_path(output_dir / "recommended_sampling_cells.csv"),
            "recommended_sampling_cells_json": rel_path(output_dir / "recommended_sampling_cells.json"),
        },
    }

    write_json(output_dir / "summary.json", summary)
    write_report(output_dir / "report.md", summary)
    write_jsonl(output_dir / "candidate_pool_internal_preview.jsonl", candidates)
    write_csv(output_dir / "cell_inventory.csv", [csv_ready_cell(row) for row in all_cell_summaries])
    write_csv(output_dir / "recommended_sampling_cells.csv", recommendations)
    write_json(output_dir / "recommended_sampling_cells.json", recommendations)
    return summary


def main() -> None:
    summary = run(parse_args())
    print(
        "status={status} candidates={candidates} strict_eligible_rows={strict_rows} "
        "posterior_allowed={posterior_allowed} validation_used={validation_used} test_used={test_used} "
        "next={next_todo}".format(
            status=summary["status"],
            candidates=summary["candidate_inventory"]["packet_ready_support_vertical_rows"],
            strict_rows=next(
                row for row in summary["cell_feasibility"] if row["cell_type"] == "subject_object_family"
            )["eligible_rows"],
            posterior_allowed=summary["posterior_allowed"],
            validation_used=summary["validation_used"],
            test_used=summary["test_used"],
            next_todo=summary["next_todo"],
        )
    )


if __name__ == "__main__":
    main()
