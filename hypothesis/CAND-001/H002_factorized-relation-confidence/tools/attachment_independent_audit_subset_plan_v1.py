#!/usr/bin/env python3
"""Plan a blind independent audit subset for H002 attachment rows."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

INPUT_ROWS = H2_ROOT / "artifacts/attachment_controlled_candidates_v1/candidate_rows.jsonl"
V20_PACKET_ROOT = (
    H2_ROOT
    / "artifacts/train_rga_full/open3dsg_train_full/rga/"
    / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_materialization"
)
V20_VISIBLE = V20_PACKET_ROOT / "visible_review_sheet.tsv"
V20_HIDDEN = V20_PACKET_ROOT / "materialized_hidden_manifest.jsonl"
V20_PACKET_INDEX = V20_PACKET_ROOT / "packet_index.jsonl"

OUT_DIR = H2_ROOT / "artifacts/attachment_independent_audit_subset_plan_v1"

PRIMARY_CELL_QUOTAS = {
    "A1_attached_near_anchor_supported_candidate": 40,
    "A2_attached_far_or_floor_confound_candidate": 40,
    "H1_hanging_anchor_supported_candidate": 40,
    "H2_hanging_no_anchor_or_floor_supported_candidate": 40,
}
CONNECTED_CELL_QUOTAS = {
    "C1_connected_near_or_overlap_diagnostic": 20,
    "C2_connected_far_or_functional_ambiguous_diagnostic": 20,
}

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
    "review_relation_reliability",
    "review_geometry_support",
    "review_endpoint_identity",
    "review_coverage",
    "review_uncertainty",
    "review_notes",
]

FORBIDDEN_VISIBLE_SUBSTRINGS = [
    "_hidden",
    "proxy",
    "selection_route",
    "rank_band",
    "source_score",
    "p_geom",
    "geometry_status",
    "scan_id",
    "subgraph_id",
    "subject_id",
    "object_id",
    "prediction_id",
    "directed_pair_id",
    "raw_feature",
    "cell_id",
    "capacity_evidence",
    "provisional_status",
    "anchor_bucket",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open() as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def suffix_from_blind_id(blind_id: str) -> str:
    return blind_id.split("_", 1)[1] if "_" in blind_id else blind_id


def load_v20_visible() -> dict[str, dict[str, str]]:
    mapping: dict[str, dict[str, str]] = {}
    with V20_VISIBLE.open(newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            suffix = suffix_from_blind_id(row["blind_review_id"])
            mapping[suffix] = row
            mapping[suffix[:12]] = row
    return mapping


def load_v20_hidden() -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(V20_HIDDEN):
        suffix = suffix_from_blind_id(row["blind_review_id"])
        mapping[suffix] = row
        mapping[suffix[:12]] = row
    return mapping


def load_v20_packet_index() -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(V20_PACKET_INDEX):
        packet_id = row["packet_id"]
        mapping[packet_id] = row
        suffix = packet_id.split("_attv20_", 1)[-1]
        mapping[suffix] = row
        mapping[suffix[:12]] = row
    return mapping


def match_v20(row: dict[str, Any], visible: dict[str, dict[str, str]]) -> dict[str, str] | None:
    suffix = suffix_from_blind_id(row["hidden_control"]["blind_review_id"])
    return visible.get(suffix) or visible.get(suffix[:12])


def evidence_priority(row: dict[str, Any]) -> tuple[int, str, str, str]:
    visible = row["_v20_visible"]
    tier_rank = 0 if visible.get("evidence_tier") == "T1_strong_pair_visual" else 1
    hidden = row["hidden_control"]
    return (
        tier_rank,
        hidden.get("object_family_pair_hidden", ""),
        row.get("candidate_relation_text", ""),
        row.get("row_id", ""),
    )


def select_cell(rows: list[dict[str, Any]], quota: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    pair_counts: Counter[str] = Counter()
    scan_counts: Counter[str] = Counter()
    for row in sorted(rows, key=evidence_priority):
        visible_pair = row["hidden_control"].get("visible_endpoint_pair_hidden", "")
        scan_id = row.get("scan_id", "")
        if pair_counts[visible_pair] >= 4:
            continue
        if scan_counts[scan_id] >= 2:
            continue
        selected.append(row)
        pair_counts[visible_pair] += 1
        scan_counts[scan_id] += 1
        if len(selected) == quota:
            return selected

    seen = {row["row_id"] for row in selected}
    for row in sorted(rows, key=evidence_priority):
        if row["row_id"] in seen:
            continue
        selected.append(row)
        if len(selected) == quota:
            return selected
    return selected


def visible_template_row(row: dict[str, Any], idx: int) -> dict[str, str]:
    visible = row["_v20_visible"]
    review_id = f"h002_att_audit_v1_{idx:04d}"
    out = {field: visible.get(field, "") for field in VISIBLE_FIELDS}
    out["blind_review_id"] = review_id
    out["candidate_relation"] = row["candidate_relation_text"]
    out["subject_label"] = row["T_e"]["subject_label"]
    out["predicate_label"] = row["T_e"]["predicate_label"]
    out["object_label"] = row["T_e"]["object_label"]
    out["relation_family_visible"] = "attachment-like relation"
    if row["row_role"] == "connected_diagnostic":
        out["packet_role"] = "connected_diagnostic_only"
        out["audit_question"] = (
            "Using only the packet images and mesh/context evidence, is "
            f"`{row['candidate_relation_text']}` visually/physically plausible, "
            "or should it be marked uncertain?"
        )
    else:
        out["packet_role"] = "primary_attachment_reliability_candidate"
        out["audit_question"] = (
            "Using only the packet images and mesh/context evidence, should "
            f"`{row['candidate_relation_text']}` be accepted as a reliable "
            "attachment-like scene-graph relation, rejected, or marked uncertain?"
        )
    for field in [
        "review_relation_reliability",
        "review_geometry_support",
        "review_endpoint_identity",
        "review_coverage",
        "review_uncertainty",
        "review_notes",
    ]:
        out[field] = ""
    return out


def hidden_manifest_row(row: dict[str, Any], visible_row: dict[str, str], idx: int) -> dict[str, Any]:
    old_visible = row["_v20_visible"]
    suffix = suffix_from_blind_id(old_visible["blind_review_id"])
    hidden = row.get("_v20_hidden") or {}
    packet_index = row.get("_v20_packet_index") or {}
    return {
        "audit_subset_row_id": f"h002_att_audit_v1_{idx:04d}",
        "current_h002_row_id": row["row_id"],
        "current_candidate_relation_text": row["candidate_relation_text"],
        "split": row["split"],
        "row_role": row["row_role"],
        "source_dataset": row["source_dataset"],
        "scan_id_hidden": row["scan_id"],
        "subgraph_id_hidden": row["subgraph_id"],
        "subject_instance_id_hidden": row["subject_instance_id"],
        "object_instance_id_hidden": row["object_instance_id"],
        "directed_pair_id_hidden": row["directed_pair_id"],
        "prediction_id_hidden": row["prediction_id"],
        "current_blind_review_id_hidden": row["hidden_control"]["blind_review_id"],
        "new_blind_review_id": visible_row["blind_review_id"],
        "v20_blind_review_id_hidden": old_visible["blind_review_id"],
        "v20_suffix_hidden": suffix,
        "v20_packet_id": old_visible["packet_id"],
        "v20_packet_dir": packet_index.get("packet_dir"),
        "v20_packet_markdown": packet_index.get("packet_markdown"),
        "v20_materialized_image_count": packet_index.get("materialized_image_count"),
        "v20_audit_ready_state_hidden": hidden.get("audit_ready_state_hidden"),
        "prior_v20_review_relation_reliability_hidden": old_visible.get("review_relation_reliability"),
        "prior_v20_review_geometry_support_hidden": old_visible.get("review_geometry_support"),
        "prior_v20_review_endpoint_identity_hidden": old_visible.get("review_endpoint_identity"),
        "prior_v20_review_coverage_hidden": old_visible.get("review_coverage"),
        "prior_v20_review_uncertainty_hidden": old_visible.get("review_uncertainty"),
        "prior_v20_review_notes_hidden": old_visible.get("review_notes"),
        "counterfactual_axis_hidden": row["counterfactual_axis"],
        "official_gt_axis_hidden": row["official_gt_axis"],
        "hidden_control": row["hidden_control"],
        "G_e_numeric_summary_hidden": row["G_e"]["geometry_features"],
        "Q_e_hidden": row["Q_e"],
    }


def validate_visible_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        missing = [field for field in VISIBLE_FIELDS if field not in row]
        if missing:
            errors.append({"row": idx, "type": "missing_visible_fields", "fields": missing})
        for field, value in row.items():
            needle = field.lower()
            if any(blocked in needle for blocked in FORBIDDEN_VISIBLE_SUBSTRINGS):
                errors.append({"row": idx, "type": "forbidden_visible_field", "field": field})
            value_l = str(value).lower()
            if any(blocked in value_l for blocked in ["scan_id", "prediction_id", "directed_pair_id"]):
                errors.append({"row": idx, "type": "forbidden_visible_value", "field": field})
    return errors


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_jsonl(INPUT_ROWS)
    visible = load_v20_visible()
    hidden = load_v20_hidden()
    packet_index = load_v20_packet_index()

    matched: list[dict[str, Any]] = []
    for row in rows:
        visible_row = match_v20(row, visible)
        if not visible_row:
            continue
        suffix = suffix_from_blind_id(visible_row["blind_review_id"])
        row["_v20_visible"] = visible_row
        row["_v20_hidden"] = hidden.get(suffix) or hidden.get(suffix[:12])
        row["_v20_packet_index"] = packet_index.get(visible_row["packet_id"]) or packet_index.get(suffix[:12])
        matched.append(row)

    by_cell: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in matched:
        by_cell[row["hidden_control"]["cell_id_hidden"]].append(row)

    selected: list[dict[str, Any]] = []
    quota_errors: list[dict[str, Any]] = []
    for cell, quota in {**PRIMARY_CELL_QUOTAS, **CONNECTED_CELL_QUOTAS}.items():
        chosen = select_cell(by_cell[cell], quota)
        selected.extend(chosen)
        if len(chosen) != quota:
            quota_errors.append(
                {"type": "quota_not_met", "cell": cell, "quota": quota, "selected": len(chosen)}
            )

    visible_rows = [visible_template_row(row, idx) for idx, row in enumerate(selected)]
    hidden_rows = [hidden_manifest_row(row, visible_rows[idx], idx) for idx, row in enumerate(selected)]

    # Validate packet references without copying or mutating packet assets.
    packet_ref_errors: list[dict[str, Any]] = []
    for row in hidden_rows:
        packet_dir = row.get("v20_packet_dir")
        packet_md = row.get("v20_packet_markdown")
        if not packet_dir or not (REPO_ROOT / packet_dir).exists():
            packet_ref_errors.append(
                {"type": "missing_packet_dir", "row": row["audit_subset_row_id"], "packet_dir": packet_dir}
            )
        if not packet_md or not (REPO_ROOT / packet_md).exists():
            packet_ref_errors.append(
                {"type": "missing_packet_markdown", "row": row["audit_subset_row_id"], "packet_markdown": packet_md}
            )

    visible_errors = validate_visible_rows(visible_rows)
    validation_errors = quota_errors + packet_ref_errors + visible_errors

    with (OUT_DIR / "visible_review_template.tsv").open("w", newline="") as f:
        writer = csv.DictWriter(f, delimiter="\t", fieldnames=VISIBLE_FIELDS)
        writer.writeheader()
        writer.writerows(visible_rows)

    write_jsonl(OUT_DIR / "audit_subset_plan_rows.jsonl", [
        {
            "audit_subset_row_id": hidden_rows[idx]["audit_subset_row_id"],
            "current_h002_row_id": row["row_id"],
            "row_role": row["row_role"],
            "predicate_label": row["T_e"]["predicate_label"],
            "candidate_relation_text": row["candidate_relation_text"],
            "evidence_tier": visible_rows[idx]["evidence_tier"],
            "packet_role": visible_rows[idx]["packet_role"],
            "review_label_fields_blank": True,
            "v20_packet_id": visible_rows[idx]["packet_id"],
            "v20_packet_reuse": True,
        }
        for idx, row in enumerate(selected)
    ])
    write_jsonl(OUT_DIR / "hidden_audit_manifest.jsonl", hidden_rows)
    write_jsonl(OUT_DIR / "validation_errors.jsonl", validation_errors)

    visible_schema = {
        "schema_version": "h002_attachment_independent_audit_subset_plan_v1_visible_schema",
        "visible_fields": VISIBLE_FIELDS,
        "review_value_schema": {
            "review_relation_reliability": [
                "accept_reliable",
                "reject_unreliable",
                "abstain_uncertain",
            ],
            "review_geometry_support": ["supported", "unsupported", "uncertain"],
            "review_endpoint_identity": [
                "clear_endpoint_identity",
                "uncertain_endpoint_identity",
                "wrong_endpoint",
            ],
            "review_coverage": ["sufficient", "limited", "insufficient"],
            "review_uncertainty": [
                "none",
                "visual_ambiguous",
                "mesh_needed",
                "ontology_ambiguous",
                "functional_connection_ambiguous",
                "occlusion_or_viewpoint_limited",
            ],
        },
        "forbidden_visible_substrings": FORBIDDEN_VISIBLE_SUBSTRINGS,
        "review_labels_are_blank_by_design": True,
    }
    (OUT_DIR / "visible_schema.json").write_text(json.dumps(visible_schema, indent=2, sort_keys=True) + "\n")

    selected_counts = {
        "rows": len(selected),
        "primary_rows": sum(1 for row in selected if row["row_role"] == "primary_binary"),
        "connected_diagnostic_rows": sum(1 for row in selected if row["row_role"] == "connected_diagnostic"),
        "by_cell": dict(Counter(row["hidden_control"]["cell_id_hidden"] for row in selected)),
        "by_predicate": dict(Counter(row["T_e"]["predicate_label"] for row in selected)),
        "by_proxy_compatibility": dict(Counter(row["counterfactual_axis"]["compatibility_label"] for row in selected)),
        "by_evidence_tier": dict(Counter(row["_v20_visible"]["evidence_tier"] for row in selected)),
        "prior_v20_review_relation_reliability_hidden": dict(
            Counter(row["_v20_visible"].get("review_relation_reliability", "") for row in selected)
        ),
    }
    summary = {
        "schema_version": "h002_attachment_independent_audit_subset_plan_v1_summary",
        "status": "h002_attachment_independent_audit_subset_plan_v1_ready",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "current_candidates": str(INPUT_ROWS.relative_to(H2_ROOT)),
            "v20_visible_review_sheet": str(V20_VISIBLE.relative_to(H2_ROOT)),
            "v20_materialized_hidden_manifest": str(V20_HIDDEN.relative_to(H2_ROOT)),
            "v20_packet_index": str(V20_PACKET_INDEX.relative_to(H2_ROOT)),
        },
        "counts": {
            "current_candidate_rows": len(rows),
            "v20_packet_matched_rows": len(matched),
            "v20_packet_unmatched_rows": len(rows) - len(matched),
            "selected": selected_counts,
            "validation_errors": len(validation_errors),
        },
        "decision": {
            "selected_route": "reuse_v20_packet_assets_with_blank_h002_independent_review_template",
            "proxy_labels_promoted": False,
            "prior_v20_labels_visible_to_reviewer": False,
            "prior_v20_labels_used_as_current_target": False,
            "multi_view_mesh_as_model_input": False,
            "multi_view_mesh_as_audit_evidence": True,
            "paper_evidence_allowed": False,
        },
        "next_todo": "attachment_independent_audit_label_fill_v1",
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_model": False,
            "modifies_h001": False,
            "copies_packet_assets": False,
        },
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    report = f"""# H002 Attachment Independent Audit Subset Plan V1

Created at: `{summary['created_at']}`

## Status

```text
status = {summary['status']}
next_todo = {summary['next_todo']}
validation_errors = {len(validation_errors)}
paper_evidence_allowed = False
```

## Selected Route

```text
reuse_v20_packet_assets_with_blank_h002_independent_review_template
```

The planner reuses existing v20 visual/mesh packet assets only as audit evidence. It does not
reuse current proxy labels as reliability targets, and it blanks review fields in the new visible
template.

## Counts

```text
current_candidate_rows = {len(rows)}
v20_packet_matched_rows = {len(matched)}
selected_rows = {len(selected)}
primary_rows = {selected_counts['primary_rows']}
connected_diagnostic_rows = {selected_counts['connected_diagnostic_rows']}
by_cell = {selected_counts['by_cell']}
by_predicate = {selected_counts['by_predicate']}
by_evidence_tier = {selected_counts['by_evidence_tier']}
prior_v20_review_relation_reliability_hidden = {selected_counts['prior_v20_review_relation_reliability_hidden']}
```

## Files

```text
visible_review_template.tsv
audit_subset_plan_rows.jsonl
hidden_audit_manifest.jsonl
visible_schema.json
summary.json
validation_errors.jsonl
```

## Boundary

- train-only H002 hypothesis artifact;
- no validation/test rows;
- no model training;
- no H001 modification;
- packet assets are referenced, not copied;
- prior v20 labels are hidden provenance only and are not current H002 targets.
"""
    (OUT_DIR / "report.md").write_text(report)


if __name__ == "__main__":
    main()
