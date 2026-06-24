#!/usr/bin/env python3
"""Materialize H002 v20 endpoint-balanced attachment audit packets."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PLAN_DIR = RGA_ROOT / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_plan"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = (
    RGA_ROOT / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_materialization"
)

EXPECTED_PLAN_STATUS = (
    "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_"
    "audit_packet_plan_ready_for_materialization"
)
EXPECTED_PLAN_NEXT = (
    "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_materialization"
)

STATUS = (
    "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_"
    "audit_packet_materialization_ready_for_leakage_review"
)
NEXT_TODO = "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_leakage_review"

UUID_RE = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE)

FORBIDDEN_VISIBLE_PATTERNS = [
    "local_dataset",
    "3RScan",
    "scan_id",
    "subgraph_id",
    "source_id",
    "subject_id",
    "object_id",
    "instance_",
    "prediction_id",
    "directed_pair_id",
    "_hidden",
    "proxy_role",
    "selection_route",
    "cell_id",
    "capacity_evidence",
    "typed_witness",
    "rank_band",
    "semantic_rank",
    "semantic_score",
    "source_score",
    "p_geom",
    "geometry_status",
    "near_contact",
    "projected_overlap",
    "far_separated",
    "provisional_status",
    "raw_feature",
    "source_path",
    "label_match_status",
    "matched_predicates",
    "label_source",
]

REVIEW_FIELDS = [
    "review_relation_reliability",
    "review_geometry_support",
    "review_endpoint_identity",
    "review_coverage",
    "review_uncertainty",
    "review_notes",
]

VISIBLE_FIELDS = [
    "packet_id",
    "blind_review_id",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "relation_family_visible",
    "packet_role",
    "evidence_tier",
    "evidence_tier_description",
    "visual_context_summary",
    "mesh_context_summary",
    "audit_question",
    *REVIEW_FIELDS,
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_tsv(path: Path) -> list[dict[str, str]]:
    with as_abs(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [dict(row) for row in reader]


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


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def validate_inputs(
    plan_summary: dict[str, Any],
    visible_rows: list[dict[str, str]],
    hidden_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append(
            {"error_type": "unexpected_plan_status", "expected": EXPECTED_PLAN_STATUS, "actual": plan_summary.get("status")}
        )
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append(
            {"error_type": "unexpected_plan_next", "expected": EXPECTED_PLAN_NEXT, "actual": plan_summary.get("next_todo")}
        )
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan_summary.get("validation_errors")})

    boundary = plan_summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "mesh_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_violation", "key": key, "expected": False, "actual": boundary.get(key)})

    if len(visible_rows) != 320:
        errors.append({"error_type": "unexpected_visible_rows", "expected": 320, "actual": len(visible_rows)})
    if len(hidden_rows) != 320:
        errors.append({"error_type": "unexpected_hidden_rows", "expected": 320, "actual": len(hidden_rows)})
    visible_ids = [row.get("packet_id") for row in visible_rows]
    hidden_ids = [row.get("packet_id") for row in hidden_rows]
    if set(visible_ids) != set(hidden_ids):
        errors.append({"error_type": "visible_hidden_packet_id_mismatch"})
    for row in visible_rows:
        if set(row) != set(VISIBLE_FIELDS):
            errors.append(
                {
                    "error_type": "visible_schema_mismatch",
                    "packet_id": row.get("packet_id"),
                    "missing": sorted(set(VISIBLE_FIELDS) - set(row)),
                    "extra": sorted(set(row) - set(VISIBLE_FIELDS)),
                }
            )
        for field in REVIEW_FIELDS:
            if row.get(field) != "":
                errors.append({"error_type": "review_field_not_blank", "packet_id": row.get("packet_id"), "field": field})
    return errors


def hidden_identity_key(row: dict[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("scan_id")),
            str(row.get("subgraph_id")),
            str(row.get("subject_id")),
            str(row.get("object_id")),
            str(row.get("predicate_label")),
        ]
    )


def match_row_identity_key(row: dict[str, Any]) -> str:
    identity = row.get("identity", {})
    predicate = row.get("predicate", {})
    return "|".join(
        [
            str(identity.get("scan_id")),
            str(identity.get("subgraph_id")),
            str(identity.get("subject_id")),
            str(identity.get("object_id")),
            str(predicate.get("predicate_label")),
        ]
    )


def collect_gt_match_rows(match_rows_path: Path, target_keys: set[str]) -> tuple[dict[str, dict[str, Any]], int]:
    found: dict[str, dict[str, Any]] = {}
    scanned = 0
    with as_abs(match_rows_path).open("r", encoding="utf-8") as handle:
        for line in handle:
            scanned += 1
            row = json.loads(line)
            row_key = match_row_identity_key(row)
            if row_key not in target_keys:
                continue
            identity = row.get("identity", {})
            label = row.get("label", {})
            rga = row.get("rga", {})
            geometry = row.get("geometry", {})
            semantic = row.get("semantic", {})
            found[row_key] = {
                "prediction_id_hidden": identity.get("prediction_id") or identity.get("row_key"),
                "label_match_status_hidden": label.get("label_match_status"),
                "label_source_hidden": label.get("label_source"),
                "label_match_hidden": label.get("label_match"),
                "family_match_hidden": label.get("family_match"),
                "matched_predicates_hidden": label.get("matched_predicates"),
                "matched_families_hidden": label.get("matched_families"),
                "matched_gt_ids_hidden": label.get("matched_gt_ids"),
                "rga_bucket_top50_hidden": rga.get("bucket_top50"),
                "rga_bucket_top100_hidden": rga.get("bucket_top100"),
                "label_geometry_bucket_hidden": rga.get("label_geometry_bucket"),
                "coverage_state_hidden": rga.get("coverage_state"),
                "geometry_status_hidden": geometry.get("geometry_status"),
                "p_geom_valid_hidden": geometry.get("p_geom_valid"),
                "rank_in_context_hidden": semantic.get("rank_in_context"),
                "semantic_score_norm_hidden": semantic.get("semantic_score_norm"),
            }
            if len(found) == len(target_keys):
                break
    return found, scanned


def leakage_scan_text(text: str, source: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    if UUID_RE.search(text):
        hits.append({"source": source, "hit_type": "uuid_like_scan_id", "pattern": "uuid"})
    lower = text.lower()
    for pattern in FORBIDDEN_VISIBLE_PATTERNS:
        if pattern.lower() in lower:
            hits.append({"source": source, "hit_type": "forbidden_visible_pattern", "pattern": pattern})
    return hits


def neutral_copy_name(group: str, index: int, suffix: str) -> str:
    clean_suffix = suffix.lower()
    if clean_suffix not in {".jpg", ".jpeg", ".png"}:
        clean_suffix = ".jpg"
    return f"{group}_{index:02d}{clean_suffix}"


def copy_group(packet_dir: Path, group: str, source_paths: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    copied: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    image_dir = packet_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    for index, source in enumerate(source_paths, start=1):
        source_path = as_abs(Path(source))
        target_name = neutral_copy_name(group, index, source_path.suffix)
        target_path = image_dir / target_name
        if not source_path.is_file():
            errors.append({"error_type": "source_image_missing", "group": group, "source": rel_path(source_path), "target": rel_path(target_path)})
            continue
        shutil.copy2(source_path, target_path)
        copied.append(
            {
                "group": group,
                "source_path_hidden": rel_path(source_path),
                "visible_name": target_name,
                "materialized_path_hidden": rel_path(target_path),
                "bytes": target_path.stat().st_size,
            }
        )
    return copied, errors


def packet_markdown(visible: dict[str, str], copied_assets: list[dict[str, Any]]) -> str:
    by_group: dict[str, list[str]] = {}
    for asset in copied_assets:
        by_group.setdefault(asset["group"], []).append(asset["visible_name"])

    lines = [
        f"# Packet {visible['packet_id']}",
        "",
        f"Relation: `{visible['candidate_relation']}`",
        "",
        f"Role: `{visible['packet_role']}`",
        "",
        f"Evidence tier: `{visible['evidence_tier']}`",
        "",
        visible["evidence_tier_description"],
        "",
        "## Context",
        "",
        f"- Visual: {visible['visual_context_summary']}",
        f"- Mesh: {visible['mesh_context_summary']}",
        "",
        "## Images",
        "",
    ]
    group_titles = {
        "subject_crop": "Subject crops",
        "subject_view": "Subject context views",
        "object_crop": "Object crops",
        "object_view": "Object context views",
    }
    for group in ["subject_crop", "subject_view", "object_crop", "object_view"]:
        names = by_group.get(group, [])
        lines.append(f"### {group_titles[group]}")
        lines.append("")
        if not names:
            lines.append("No packet-local image was materialized for this group.")
        for name in names:
            lines.append(f"![{group}]({Path('images') / name})")
        lines.append("")

    lines.extend(
        [
            "## Question",
            "",
            visible["audit_question"],
            "",
            "## Review Fields",
            "",
            "- Relation reliability:",
            "- Geometry support:",
            "- Endpoint identity:",
            "- Coverage:",
            "- Uncertainty:",
            "- Notes:",
            "",
        ]
    )
    return "\n".join(lines)


def materialize_packets(
    visible_rows: list[dict[str, str]],
    hidden_rows: list[dict[str, Any]],
    gt_match_by_identity: dict[str, dict[str, Any]],
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    hidden_by_packet = {row["packet_id"]: row for row in hidden_rows}
    packet_index: list[dict[str, Any]] = []
    materialized_manifest: list[dict[str, Any]] = []
    validation_errors: list[dict[str, Any]] = []
    packet_root = output_dir / "packets"
    packet_root.mkdir(parents=True, exist_ok=True)

    for visible in visible_rows:
        packet_id = visible["packet_id"]
        hidden = hidden_by_packet[packet_id]
        packet_dir = packet_root / packet_id
        packet_dir.mkdir(parents=True, exist_ok=True)

        copied_assets: list[dict[str, Any]] = []
        for group, key in [
            ("subject_crop", "subject_crop_file_examples"),
            ("subject_view", "subject_origin_file_examples"),
            ("object_crop", "object_crop_file_examples"),
            ("object_view", "object_origin_file_examples"),
        ]:
            copied, errors = copy_group(packet_dir, group, hidden.get(key, []))
            copied_assets.extend(copied)
            for error in errors:
                error["packet_id"] = packet_id
                validation_errors.append(error)

        packet_md = packet_dir / "packet.md"
        packet_md.write_text(packet_markdown(visible, copied_assets), encoding="utf-8")

        packet_index.append(
            {
                "packet_id": packet_id,
                "packet_role": visible["packet_role"],
                "evidence_tier": visible["evidence_tier"],
                "predicate_label": visible["predicate_label"],
                "packet_dir": rel_path(packet_dir),
                "packet_markdown": rel_path(packet_md),
                "materialized_image_count": len(copied_assets),
            }
        )

        identity_key = hidden_identity_key(hidden)
        gt_fields = gt_match_by_identity.get(identity_key)
        if gt_fields is None:
            validation_errors.append({"error_type": "gt_match_row_missing", "packet_id": packet_id, "identity_key": identity_key})
            gt_fields = {}
        prediction_id = str(gt_fields.get("prediction_id_hidden") or "")

        materialized_manifest.append(
            {
                "schema_version": "h002_reliability_target_v20_attachment_endpoint_balanced_audit_packet_materialized_hidden_manifest_v1",
                "packet_id": packet_id,
                "blind_review_id": visible["blind_review_id"],
                "scan_id_hidden": hidden["scan_id"],
                "subgraph_id_hidden": hidden["subgraph_id"],
                "source_id_hidden": hidden["source_id"],
                "subject_id_hidden": hidden["subject_id"],
                "object_id_hidden": hidden["object_id"],
                "prediction_id_hidden": prediction_id,
                "subject_label": visible["subject_label"],
                "predicate_label": visible["predicate_label"],
                "object_label": visible["object_label"],
                "packet_role": visible["packet_role"],
                "evidence_tier": visible["evidence_tier"],
                "candidate_role_hidden": hidden["candidate_role_hidden"],
                "proxy_role_hidden": hidden["proxy_role_hidden"],
                "cell_id_hidden": hidden["cell_id_hidden"],
                "capacity_evidence_tier_hidden": hidden["capacity_evidence_tier_hidden"],
                "selection_route_level_hidden": hidden["selection_route_level_hidden"],
                "audit_ready_state_hidden": hidden["audit_ready_state"],
                "visual_context_state_hidden": hidden["visual_context_state"],
                "shared_origin_frames_hidden": hidden["shared_origin_frames"],
                "shared_crop_view_ranks_hidden": hidden["shared_crop_view_ranks"],
                "mesh_ready_hidden": hidden["mesh_ready"],
                "sequence_ready_hidden": hidden["sequence_ready"],
                "packet_dir_hidden": rel_path(packet_dir),
                "packet_markdown_hidden": rel_path(packet_md),
                "copied_assets_hidden": copied_assets,
                "existing_gt_match_axis_hidden": gt_fields,
                "human_reliability_label_future_primary_target": True,
                "existing_gt_relation_match_future_auxiliary_axis": True,
                "mismatch_analysis_future_axis": True,
                "model_input_allowed_now": False,
            }
        )
    return packet_index, materialized_manifest, validation_errors


def visible_leakage_hits(output_paths: list[Path]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for path in output_paths:
        if not path.is_file():
            continue
        hits.extend(leakage_scan_text(path.read_text(encoding="utf-8"), rel_path(path)))
    return hits


def validate_materialized(
    visible_rows: list[dict[str, str]],
    packet_index: list[dict[str, Any]],
    materialized_manifest: list[dict[str, Any]],
    visible_hits: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(packet_index) != 320:
        errors.append({"error_type": "unexpected_packet_index_rows", "expected": 320, "actual": len(packet_index)})
    if len(materialized_manifest) != 320:
        errors.append({"error_type": "unexpected_materialized_manifest_rows", "expected": 320, "actual": len(materialized_manifest)})
    missing_packet_dirs = [row["packet_id"] for row in packet_index if not as_abs(Path(row["packet_dir"])).is_dir()]
    if missing_packet_dirs:
        errors.append({"error_type": "missing_packet_dirs", "packet_ids": missing_packet_dirs[:20], "count": len(missing_packet_dirs)})
    no_images = [row["packet_id"] for row in packet_index if row["materialized_image_count"] <= 0]
    if no_images:
        errors.append({"error_type": "packets_without_images", "packet_ids": no_images[:20], "count": len(no_images)})
    if visible_hits:
        errors.append({"error_type": "visible_leakage_hits_present", "count": len(visible_hits)})

    primary_rows = [row for row in visible_rows if row["packet_role"] == "primary_attachment_reliability_candidate"]
    connected_rows = [row for row in visible_rows if row["packet_role"] == "connected_diagnostic_only"]
    primary_tiers = Counter(row["evidence_tier"] for row in primary_rows)
    all_tiers = Counter(row["evidence_tier"] for row in visible_rows)
    if len(primary_rows) != 256:
        errors.append({"error_type": "unexpected_primary_rows", "expected": 256, "actual": len(primary_rows)})
    if len(connected_rows) != 64:
        errors.append({"error_type": "unexpected_connected_rows", "expected": 64, "actual": len(connected_rows)})
    if all_tiers.get("T1_strong_pair_visual", 0) != 75:
        errors.append({"error_type": "unexpected_t1_rows", "expected": 75, "actual": all_tiers.get("T1_strong_pair_visual", 0)})
    if all_tiers.get("T2_individual_visual_plus_mesh", 0) != 245:
        errors.append({"error_type": "unexpected_t2_rows", "expected": 245, "actual": all_tiers.get("T2_individual_visual_plus_mesh", 0)})
    if primary_tiers.get("T1_strong_pair_visual", 0) != 62:
        errors.append({"error_type": "unexpected_primary_t1_rows", "expected": 62, "actual": primary_tiers.get("T1_strong_pair_visual", 0)})
    if primary_tiers.get("T2_individual_visual_plus_mesh", 0) != 194:
        errors.append({"error_type": "unexpected_primary_t2_rows", "expected": 194, "actual": primary_tiers.get("T2_individual_visual_plus_mesh", 0)})

    gt_axis_missing = [
        row["packet_id"]
        for row in materialized_manifest
        if not row.get("existing_gt_match_axis_hidden")
        or row["existing_gt_match_axis_hidden"].get("label_match_status_hidden") is None
    ]
    if gt_axis_missing:
        errors.append({"error_type": "existing_gt_match_axis_missing", "count": len(gt_axis_missing), "packet_ids": gt_axis_missing[:20]})
    return errors


def report_text(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    return f"""# H002 V20 Attachment Endpoint-Balanced Audit Packet Materialization

Created at: `{summary['created_at']}`

## Status

```text
status = {summary['status']}
next_todo = {summary['next_todo']}
validation_errors = {summary['validation_errors']}
visible_leakage_hits = {counts['visible_leakage_hits']}
posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}
multi_view_as_model_input = {summary['boundary']['multi_view_as_model_input']}
```

## Counts

```text
visible_review_rows = {counts['visible_review_rows']}
packet_dirs = {counts['packet_dirs']}
materialized_hidden_manifest_rows = {counts['materialized_hidden_manifest_rows']}
total_materialized_images = {counts['total_materialized_images']}
rows_by_packet_role = {counts['rows_by_packet_role']}
rows_by_evidence_tier = {counts['rows_by_evidence_tier']}
primary_by_evidence_tier = {counts['primary_by_evidence_tier']}
gt_match_axis_joined_rows = {counts['gt_match_axis_joined_rows']}
gt_label_match_status = {counts['gt_label_match_status']}
```

## Direction Preserved

The materialized hidden manifest preserves two future evaluation axes:

- primary target: future human-audited reliability label from packet review.
- auxiliary axis: existing GT relation match from `match_rows.jsonl`.

The future mismatch table should compare human reliability with GT match:

```text
GT match & reliability accept
GT match & reliability reject
No GT & reliability accept
No GT & reliability reject
Abstain
```

## Boundary

Visible artifacts use neutral packet-local image names. Source paths, scan ids, subgraph ids,
instance ids, construction metadata, geometry status, rank, `p_geom_valid`, and GT match fields
remain hidden. This stage does not fill labels, train posterior, use validation/test rows, or
promote multi-view as deployable model input.
"""


def main() -> int:
    args = parse_args()
    plan_dir = as_abs(args.plan_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(plan_dir / "summary.json")
    visible_rows = read_tsv(plan_dir / "visible_packet_template.tsv")
    hidden_rows = read_jsonl(plan_dir / "hidden_asset_manifest_plan.jsonl")
    validation_errors = validate_inputs(plan_summary, visible_rows, hidden_rows)

    target_keys = {hidden_identity_key(row) for row in hidden_rows}
    gt_match_by_identity, match_rows_scanned = collect_gt_match_rows(args.match_rows, target_keys)
    missing_gt = sorted(target_keys - set(gt_match_by_identity))
    if missing_gt:
        validation_errors.append({"error_type": "missing_gt_match_rows", "count": len(missing_gt), "identity_keys": missing_gt[:20]})

    packet_index, materialized_manifest, materialize_errors = materialize_packets(
        visible_rows, hidden_rows, gt_match_by_identity, output_dir
    )
    validation_errors.extend(materialize_errors)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "visible_review_sheet": output_dir / "visible_review_sheet.tsv",
        "packet_index": output_dir / "packet_index.jsonl",
        "materialized_hidden_manifest": output_dir / "materialized_hidden_manifest.jsonl",
        "visible_leakage_hits": output_dir / "visible_leakage_hits.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    write_tsv(output_paths["visible_review_sheet"], visible_rows, VISIBLE_FIELDS)
    write_jsonl(output_paths["packet_index"], packet_index)
    write_jsonl(output_paths["materialized_hidden_manifest"], materialized_manifest)

    visible_paths = [output_paths["visible_review_sheet"]]
    visible_paths.extend(as_abs(Path(row["packet_markdown"])) for row in packet_index)
    leakage_hits = visible_leakage_hits(visible_paths)
    validation_errors.extend(validate_materialized(visible_rows, packet_index, materialized_manifest, leakage_hits))

    rows_by_packet_role = Counter(row["packet_role"] for row in visible_rows)
    rows_by_evidence_tier = Counter(row["evidence_tier"] for row in visible_rows)
    primary_rows = [row for row in visible_rows if row["packet_role"] == "primary_attachment_reliability_candidate"]
    primary_by_evidence_tier = Counter(row["evidence_tier"] for row in primary_rows)
    total_images = sum(row["materialized_image_count"] for row in packet_index)
    gt_label_status = Counter(
        row.get("existing_gt_match_axis_hidden", {}).get("label_match_status_hidden", "missing")
        for row in materialized_manifest
    )
    counts = {
        "visible_review_rows": len(visible_rows),
        "packet_dirs": len(packet_index),
        "materialized_hidden_manifest_rows": len(materialized_manifest),
        "total_materialized_images": total_images,
        "visible_leakage_hits": len(leakage_hits),
        "rows_by_packet_role": dict(rows_by_packet_role),
        "rows_by_evidence_tier": dict(rows_by_evidence_tier),
        "primary_by_evidence_tier": dict(primary_by_evidence_tier),
        "gt_match_axis_joined_rows": len(gt_match_by_identity),
        "gt_label_match_status": dict(gt_label_status),
        "match_rows_scanned_for_gt_axis": match_rows_scanned,
    }

    summary = {
        "schema_version": "h002_reliability_target_v20_attachment_endpoint_balanced_audit_packet_materialization_summary_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "next_todo": NEXT_TODO,
        "input_paths": {
            "audit_packet_plan_summary": rel_path(plan_dir / "summary.json"),
            "visible_packet_template": rel_path(plan_dir / "visible_packet_template.tsv"),
            "hidden_asset_manifest_plan": rel_path(plan_dir / "hidden_asset_manifest_plan.jsonl"),
            "match_rows": rel_path(args.match_rows),
        },
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "candidate_mining_allowed": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "multi_view_as_audit_or_confirmation_evidence_only": True,
            "mesh_as_audit_or_confirmation_evidence_only": True,
            "human_reliability_label_future_primary_target": True,
            "existing_gt_relation_match_future_auxiliary_axis": True,
            "mismatch_analysis_future_axis": True,
            "construction_metadata_visible": False,
            "gt_match_axis_visible": False,
        },
        "counts": counts,
        "validation_errors": len(validation_errors),
    }
    write_json(output_paths["summary"], summary)
    write_jsonl(output_paths["visible_leakage_hits"], leakage_hits)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    output_paths["report"].write_text(report_text(summary), encoding="utf-8")

    print(f"status={STATUS}")
    print(f"next={NEXT_TODO}")
    print(f"visible_review_rows={counts['visible_review_rows']}")
    print(f"packet_dirs={counts['packet_dirs']}")
    print(f"total_materialized_images={counts['total_materialized_images']}")
    print(f"visible_leakage_hits={counts['visible_leakage_hits']}")
    print(f"gt_match_axis_joined_rows={counts['gt_match_axis_joined_rows']}")
    print(f"validation_errors={len(validation_errors)}")
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
