#!/usr/bin/env python3
"""Decide the human-label path after independent target audit."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_AUDIT_DIR = RGA_ROOT / "independent_support_vertical_v2_independent_target_independence_audit_codex_independent_ver"
DEFAULT_COLLECTION_DIR = RGA_ROOT / "independent_support_vertical_v2_target_path_decision_codex_ver"
DEFAULT_FILL_DIR = RGA_ROOT / "independent_support_vertical_v2_independent_label_fill_codex_independent_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_human_label_path_decision_codex_ver"

FULL_REVIEW_ROWS = 127
MINIMUM_REVIEW_ROWS = 96
HYPOTHESIS_MIN_BINARY_ROWS = 60
HYPOTHESIS_MIN_PER_CLASS = 20

BASE_LABELER_FIELDS = [
    "blind_review_id",
    "audit_scope",
    "scan_id",
    "scene_context_id",
    "subject_id",
    "subject_label",
    "predicate_label",
    "predicate_family",
    "object_id",
    "object_label",
    "endpoint_pair_note",
    "family_question",
    "positive_cues",
    "negative_cues",
    "evidence_packet_status",
    "multiview_packet",
    "pointcloud_or_mesh_packet",
    "contact_or_context_sheet",
    "witness_distance_xy_m",
    "witness_distance_3d_m",
    "witness_center_delta_z_m",
    "witness_vertical_gap_subject_on_object_m",
    "witness_projected_iou_xy",
    "witness_subject_overlap_xy",
    "witness_object_overlap_xy",
    "witness_normalized_distance_xy",
    "witness_support_contact_gap_abs",
    "witness_support_contact_xy_overlap",
    "witness_relative_vertical_signed_margin",
    "witness_relative_vertical_sign_agreement",
]

HUMAN_COMPLETION_FIELDS = [
    "human_reviewer_id",
    "human_review_round",
    "endpoint_identity_human",
    "pair_evaluability_human",
    "geometry_validity_human",
    "relation_reliability_human",
    "primary_reason_human",
    "uncertainty_reason_human",
    "label_notes_human",
]

FORBIDDEN_LABELER_HEADER_FRAGMENTS = [
    "target",
    "posterior",
    "label_use",
    "geometry_status",
    "rank",
    "score",
    "p_geom",
    "label_match",
    "proposed",
    "queue",
    "prediction_id",
    "relation_validity_label",
    "v2",
    "hidden",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--collection-dir", type=Path, default=DEFAULT_COLLECTION_DIR)
    parser.add_argument("--fill-dir", type=Path, default=DEFAULT_FILL_DIR)
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


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), [dict(row) for row in reader]


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


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def header_hits(fieldnames: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for field in fieldnames:
        lower = field.lower()
        for fragment in FORBIDDEN_LABELER_HEADER_FRAGMENTS:
            if fragment in lower:
                hits.append({"field": field, "forbidden_fragment": fragment})
    return hits


def human_schema() -> dict[str, Any]:
    return {
        "schema_version": "h002_support_vertical_human_label_collection_schema_v1",
        "purpose": "human-confirmed relation reliability review for support_contact and relative_vertical",
        "boundary": {
            "split": "train_only",
            "direct_prior_labels_visible": False,
            "semantic_score_or_rank_visible": False,
            "p_geom_valid_visible": False,
            "geometry_status_visible": False,
            "v2_codex_axes_visible": False,
            "codex_independent_labels_visible": False,
            "multi_view_as_model_input": False,
        },
        "required_completion_fields": [
            "human_reviewer_id",
            "human_review_round",
            "endpoint_identity_human",
            "pair_evaluability_human",
            "geometry_validity_human",
            "relation_reliability_human",
            "primary_reason_human",
            "uncertainty_reason_human",
        ],
        "optional_completion_fields": ["label_notes_human"],
        "allowed_review_values": {
            "endpoint_identity_human": [
                "both_valid",
                "subject_invalid",
                "object_invalid",
                "pair_invalid",
                "uncertain",
            ],
            "pair_evaluability_human": [
                "evaluable",
                "partially_evaluable",
                "not_evaluable",
                "uncertain",
            ],
            "geometry_validity_human": [
                "supports_predicate",
                "contradicts_predicate",
                "ambiguous",
                "not_evaluable",
            ],
            "relation_reliability_human": [
                "reliable",
                "unreliable",
                "uncertain",
            ],
            "primary_reason_human": [
                "physically_supported_informative",
                "geometry_contradiction",
                "dense_or_trivial_relation",
                "endpoint_identity_issue",
                "ontology_mismatch",
                "better_alternative_predicate",
                "visibility_or_evidence_gap",
                "annotation_sparsity_candidate",
                "other",
            ],
            "uncertainty_reason_human": [
                "none",
                "endpoint_identity",
                "visibility_or_occlusion",
                "weak_geometry",
                "dense_relation",
                "ontology_ambiguity",
                "needs_multiview_or_mesh",
                "other",
            ],
        },
        "post_label_targets": {
            "geometry_validity_human_target": {
                "positive": {"geometry_validity_human": ["supports_predicate"]},
                "negative": {"geometry_validity_human": ["contradicts_predicate"]},
                "exclude": {"geometry_validity_human": ["ambiguous", "not_evaluable"]},
            },
            "relation_reliability_human_target": {
                "positive": {"relation_reliability_human": ["reliable"]},
                "negative": {"relation_reliability_human": ["unreliable"]},
                "exclude": {"relation_reliability_human": ["uncertain"]},
            },
        },
    }


def make_human_sheet_rows(source_rows: list[dict[str, str]], selected_ids: set[str], audit_scope: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in source_rows:
        if row["blind_review_id"] not in selected_ids:
            continue
        output = {key: row.get(key, "") for key in BASE_LABELER_FIELDS}
        output["audit_scope"] = audit_scope
        for key in HUMAN_COMPLETION_FIELDS:
            output[key] = ""
        rows.append(output)
    return rows


def hidden_value(manifest_by_id: dict[str, dict[str, Any]], blind_id: str, key: str) -> str:
    hidden = manifest_by_id.get(blind_id, {}).get("hidden_strata", {})
    return str(hidden.get(key) or "missing")


def pick_diverse_rows(
    all_rows: list[dict[str, str]],
    manifest_by_id: dict[str, dict[str, Any]],
    seed_ids: set[str],
    target_rows: int,
) -> set[str]:
    selected = set(seed_ids)
    family_target = {"relative_vertical": target_rows // 2, "support_contact": target_rows - target_rows // 2}
    family_counts = Counter(row["predicate_family"] for row in all_rows if row["blind_review_id"] in selected)
    predicate_counts = Counter(row["predicate_label"] for row in all_rows if row["blind_review_id"] in selected)
    prior_counts = Counter(
        hidden_value(manifest_by_id, row["blind_review_id"], "relation_validity_label_hidden")
        for row in all_rows
        if row["blind_review_id"] in selected
    )
    rank_counts = Counter(
        hidden_value(manifest_by_id, row["blind_review_id"], "rank_band_hidden")
        for row in all_rows
        if row["blind_review_id"] in selected
    )

    candidates_by_family: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in all_rows:
        if row["blind_review_id"] not in selected:
            candidates_by_family[row["predicate_family"]].append(row)

    def candidate_key(row: dict[str, str]) -> tuple[int, int, int, int, str]:
        blind_id = row["blind_review_id"]
        return (
            predicate_counts[row["predicate_label"]],
            prior_counts[hidden_value(manifest_by_id, blind_id, "relation_validity_label_hidden")],
            rank_counts[hidden_value(manifest_by_id, blind_id, "rank_band_hidden")],
            family_counts[row["predicate_family"]],
            blind_id,
        )

    for family, desired_count in family_target.items():
        while family_counts[family] < desired_count and candidates_by_family[family]:
            row = sorted(candidates_by_family[family], key=candidate_key)[0]
            candidates_by_family[family].remove(row)
            blind_id = row["blind_review_id"]
            selected.add(blind_id)
            family_counts[family] += 1
            predicate_counts[row["predicate_label"]] += 1
            prior_counts[hidden_value(manifest_by_id, blind_id, "relation_validity_label_hidden")] += 1
            rank_counts[hidden_value(manifest_by_id, blind_id, "rank_band_hidden")] += 1

    remaining = [row for rows in candidates_by_family.values() for row in rows if row["blind_review_id"] not in selected]
    while len(selected) < target_rows and remaining:
        row = sorted(remaining, key=candidate_key)[0]
        remaining.remove(row)
        blind_id = row["blind_review_id"]
        selected.add(blind_id)
        family_counts[row["predicate_family"]] += 1
        predicate_counts[row["predicate_label"]] += 1
        prior_counts[hidden_value(manifest_by_id, blind_id, "relation_validity_label_hidden")] += 1
        rank_counts[hidden_value(manifest_by_id, blind_id, "rank_band_hidden")] += 1

    return selected


def codex_label_counts(rows: list[dict[str, str]], selected_ids: set[str]) -> dict[str, Any]:
    selected = [row for row in rows if row["blind_review_id"] in selected_ids]
    relation_counts = Counter(row["relation_reliability_independent"] for row in selected)
    geometry_counts = Counter(row["geometry_validity_independent"] for row in selected)
    return {
        "rows": len(selected),
        "relation_reliability_independent": dict(sorted(relation_counts.items())),
        "geometry_validity_independent": dict(sorted(geometry_counts.items())),
        "estimated_relation_binary": relation_counts["reliable"] + relation_counts["unreliable"],
        "estimated_relation_positive": relation_counts["reliable"],
        "estimated_relation_negative": relation_counts["unreliable"],
        "estimated_relation_uncertain": relation_counts["uncertain"],
        "estimated_geometry_binary": geometry_counts["supports_predicate"] + geometry_counts["contradicts_predicate"],
        "estimated_geometry_positive": geometry_counts["supports_predicate"],
        "estimated_geometry_negative": geometry_counts["contradicts_predicate"],
    }


def row_counts(rows: list[dict[str, str]], manifest_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "by_family": dict(sorted(Counter(row["predicate_family"] for row in rows).items())),
        "by_predicate": dict(sorted(Counter(row["predicate_label"] for row in rows).items())),
        "by_rank_band_hidden_audit_only": dict(
            sorted(Counter(hidden_value(manifest_by_id, row["blind_review_id"], "rank_band_hidden") for row in rows).items())
        ),
        "by_prior_relation_validity_hidden_audit_only": dict(
            sorted(
                Counter(
                    hidden_value(manifest_by_id, row["blind_review_id"], "relation_validity_label_hidden")
                    for row in rows
                ).items()
            )
        ),
    }


def make_manifest(
    source_manifest: list[dict[str, Any]],
    selected_ids: set[str],
    batch_name: str,
    minimum_ids: set[str],
    full_ids: set[str],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in source_manifest:
        blind_id = str(row["blind_review_id"])
        if blind_id not in selected_ids:
            continue
        copied = dict(row)
        copied["schema_version"] = "h002_support_vertical_human_collection_internal_manifest_v1"
        copied["human_batch_name"] = batch_name
        copied["in_minimum_human_batch"] = blind_id in minimum_ids
        copied["in_full_human_batch"] = blind_id in full_ids
        copied["labeler_visible"] = False
        copied["post_label_join_only"] = True
        output.append(copied)
    return output


def option_matrix(audit_summary: dict[str, Any], minimum_counts: dict[str, Any], full_counts: dict[str, Any]) -> list[dict[str, Any]]:
    relation_decision = audit_summary["target_decisions"]["relation_reliability_independent_target"]
    construction = relation_decision.get("recommended_construction_slice")
    return [
        {
            "option": "revise_codex_target_again",
            "verdict": "reject_as_main_path",
            "reason": "v1, v2 factual-axis target, and codex-independent visible-only target all failed strict independence gates",
            "evidence": relation_decision["status"],
        },
        {
            "option": "use_rank_band_balanced_independent_for_method_evidence",
            "verdict": "reject_for_method_evidence",
            "reason": "construction risk is reduced but harmful prior carryover remains",
            "evidence": {
                "slice": construction["slice_name"] if construction else "none",
                "rows": construction["rows"] if construction else 0,
                "harmful_prior_risk_count": construction["harmful_prior_risk_count"] if construction else None,
            },
        },
        {
            "option": "collect_minimum_human_batch_96",
            "verdict": "acceptable_first_batch",
            "reason": "estimated binary/per-class count clears the hypothesis-stage minimum with lower labeling cost; must expand if audit fails",
            "evidence": minimum_counts,
        },
        {
            "option": "collect_full_human_batch_127",
            "verdict": "recommended",
            "reason": "small enough to label fully and most robust against class-count, uncertainty, and target-independence risk",
            "evidence": full_counts,
        },
        {
            "option": "add_multi_view_as_model_input_now",
            "verdict": "defer",
            "reason": "multi-view should remain audit evidence until a human-confirmed target passes independence checks",
            "evidence": "current blocker is target independence, not missing model capacity",
        },
    ]


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 Human Label Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Decision",
        "",
        summary["decision"],
        "",
        "## Minimum Gate",
        "",
        "| Gate | Value |",
        "| --- | ---: |",
        f"| hypothesis-stage binary rows | {summary['minimum_gate']['hypothesis_min_binary_rows']} |",
        f"| hypothesis-stage per-class rows | {summary['minimum_gate']['hypothesis_min_per_class']} |",
        f"| minimum human batch rows | {counts['minimum_human_batch_rows']} |",
        f"| full human batch rows | {counts['full_human_batch_rows']} |",
        "",
        "## Batch Estimates",
        "",
        "| Batch | Rows | Est. Binary | Est. Pos | Est. Neg | Est. Uncertain |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in ["minimum_human_batch", "full_human_batch"]:
        estimate = summary["bootstrap_estimates"][name]
        lines.append(
            f"| `{name}` | {estimate['rows']} | {estimate['estimated_relation_binary']} | "
            f"{estimate['estimated_relation_positive']} | {estimate['estimated_relation_negative']} | "
            f"{estimate['estimated_relation_uncertain']} |"
        )
    lines.extend(
        [
            "",
            "## Option Matrix",
            "",
            "| Option | Verdict | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for item in summary["option_matrix"]:
        lines.append(f"| `{item['option']}` | `{item['verdict']}` | {item['reason']} |")
    lines.extend(
        [
            "",
            "## Output Sheets",
            "",
            "Minimum first batch:",
            "",
            "```text",
            summary["output_paths"]["minimum_human_collection_sheet"],
            "```",
            "",
            "Recommended full batch:",
            "",
            "```text",
            summary["output_paths"]["full_human_collection_sheet"],
            "```",
            "",
            "## Boundary",
            "",
            "- No validation/test rows are used.",
            "- No posterior is trained.",
            "- Human label sheets do not expose hidden metadata, prior labels, v2 Codex axes, semantic score/rank, or `p_geom_valid`.",
            "- Multi-view/mesh/contact-sheet paths are audit evidence only, not model input.",
            "- Bootstrap estimates are not labeler-visible and are not paper evidence.",
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    audit_dir = as_abs(args.audit_dir)
    collection_dir = as_abs(args.collection_dir)
    fill_dir = as_abs(args.fill_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now(timezone.utc).isoformat()
    audit_summary = read_json(audit_dir / "summary.json")
    fieldnames, collection_rows = read_tsv(collection_dir / "independent_collection_sheet.tsv")
    source_manifest = read_jsonl(collection_dir / "internal_manifest_post_label_only.jsonl")
    _, codex_completed_rows = read_tsv(fill_dir / "completed_independent_collection_sheet_codex_independent_ver.tsv")
    rank_slice_rows = read_jsonl(
        audit_dir / "target_slices/relation_reliability_independent_target/rank_band_balanced_independent.jsonl"
    )

    manifest_by_id = {str(row["blind_review_id"]): row for row in source_manifest}
    full_ids = {row["blind_review_id"] for row in collection_rows}
    seed_ids = {str(row["blind_review_id"]) for row in rank_slice_rows}
    minimum_ids = pick_diverse_rows(collection_rows, manifest_by_id, seed_ids, MINIMUM_REVIEW_ROWS)

    human_fieldnames = BASE_LABELER_FIELDS + HUMAN_COMPLETION_FIELDS
    hits = header_hits(human_fieldnames)
    minimum_rows = make_human_sheet_rows(
        collection_rows,
        minimum_ids,
        "selected_support_vertical_human_minimum_review_v1",
    )
    full_rows = make_human_sheet_rows(
        collection_rows,
        full_ids,
        "selected_support_vertical_human_full_review_v1",
    )
    minimum_manifest = make_manifest(source_manifest, minimum_ids, "minimum_human_batch_96", minimum_ids, full_ids)
    full_manifest = make_manifest(source_manifest, full_ids, "full_human_batch_127", minimum_ids, full_ids)

    minimum_estimates = codex_label_counts(codex_completed_rows, minimum_ids)
    full_estimates = codex_label_counts(codex_completed_rows, full_ids)
    minimum_counts = row_counts(minimum_rows, manifest_by_id)
    full_counts = row_counts(full_rows, manifest_by_id)
    options = option_matrix(audit_summary, minimum_estimates, full_estimates)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "option_matrix": output_dir / "option_matrix.json",
        "human_collection_schema": output_dir / "human_collection_schema.json",
        "minimum_human_collection_sheet": output_dir / "minimum_human_collection_sheet.tsv",
        "full_human_collection_sheet": output_dir / "full_human_collection_sheet.tsv",
        "minimum_manifest_post_label_only": output_dir / "minimum_manifest_post_label_only.jsonl",
        "full_manifest_post_label_only": output_dir / "full_manifest_post_label_only.jsonl",
        "sampling_plan": output_dir / "sampling_plan.json",
        "labeler_header_leakage_hits": output_dir / "labeler_header_leakage_hits.jsonl",
    }

    if audit_summary.get("status") != "full_train_independent_support_vertical_v2_independent_target_independence_audit_strict_blocked_construction_slice_available":
        status = "full_train_independent_support_vertical_v2_human_label_path_decision_needs_audit_review"
        decision = "Audit status is unexpected; review independent target-independence output before choosing a human-label path."
        next_todo = "review_full_train_independent_support_vertical_v2_independent_target_audit"
    elif hits:
        status = "full_train_independent_support_vertical_v2_human_label_path_decision_sheet_has_leakage"
        decision = "Human collection sheet has forbidden labeler-visible fields; fix before label collection."
        next_todo = "fix_full_train_independent_support_vertical_v2_human_collection_sheet"
    else:
        status = "full_train_independent_support_vertical_v2_human_label_path_decision_collect_human_confirmed_labels"
        decision = (
            "Stop treating another Codex-derived target revision as the main path. "
            "Collect human-confirmed support/vertical labels, preferably the full 127-row batch; "
            "a 96-row minimum batch is acceptable as a first pass but must expand if target independence fails."
        )
        next_todo = "full_train_independent_support_vertical_v2_human_label_fill_or_external_review"

    summary = {
        "schema_version": "h002_support_vertical_v2_human_label_path_decision_summary_v1",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "audit_summary": rel_path(audit_dir / "summary.json"),
            "independent_collection_sheet": rel_path(collection_dir / "independent_collection_sheet.tsv"),
            "internal_manifest_post_label_only": rel_path(collection_dir / "internal_manifest_post_label_only.jsonl"),
            "codex_independent_completed_sheet": rel_path(fill_dir / "completed_independent_collection_sheet_codex_independent_ver.tsv"),
            "rank_band_diagnostic_slice": rel_path(
                audit_dir / "target_slices/relation_reliability_independent_target/rank_band_balanced_independent.jsonl"
            ),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "label_source_required_next": "human_confirmed",
            "codex_labels_as_paper_evidence": False,
            "labeler_visible_hidden_metadata": False,
            "labeler_visible_v2_codex_axes": False,
            "labeler_visible_codex_independent_labels": False,
            "labeler_visible_semantic_score_or_p_geom": False,
            "multi_view_as_model_input": False,
        },
        "minimum_gate": {
            "hypothesis_min_binary_rows": HYPOTHESIS_MIN_BINARY_ROWS,
            "hypothesis_min_per_class": HYPOTHESIS_MIN_PER_CLASS,
            "paper_level_posterior_gate_not_satisfied_by_this_scope": True,
            "paper_level_note": "Earlier broad posterior revival gate asks for >=150 binary rows; this support/vertical batch is a hypothesis-stage target gate.",
        },
        "counts": {
            "source_collection_rows": len(collection_rows),
            "rank_band_seed_rows": len(seed_ids),
            "minimum_human_batch_rows": len(minimum_rows),
            "full_human_batch_rows": len(full_rows),
            "labeler_header_leakage_hits": len(hits),
            "minimum_human_batch": minimum_counts,
            "full_human_batch": full_counts,
        },
        "bootstrap_estimates": {
            "source": "codex_independent_visible_only_estimate_not_labeler_visible",
            "minimum_human_batch": minimum_estimates,
            "full_human_batch": full_estimates,
        },
        "option_matrix": options,
        "decision": decision,
        "next_todo": next_todo,
    }

    sampling_plan = {
        "schema_version": "h002_support_vertical_human_sampling_plan_v1",
        "decision": decision,
        "recommended_batch": "full_human_batch_127",
        "minimum_first_batch": "minimum_human_batch_96",
        "minimum_batch_rule": (
            "Start from the 62-row rank-band-balanced diagnostic slice, then add 34 diverse rows "
            "to improve family, predicate, prior-label, and rank-band coverage. Selection metadata is "
            "post-label audit-only and not labeler-visible."
        ),
        "stopping_rule": (
            "After human labels are filled, ingest human targets and rerun target-independence audit. "
            "Proceed to source-score feature join only if relation reliability has >=60 binary rows, "
            ">=20 per class, and a strict slice clears harmful prior-label and construction risks. "
            "Otherwise expand to the full 127-row batch before revising the method."
        ),
        "minimum_ids": sorted(minimum_ids),
        "full_ids": sorted(full_ids),
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["option_matrix"], {"schema_version": "h002_support_vertical_human_option_matrix_v1", "options": options})
    write_json(output_paths["human_collection_schema"], human_schema())
    write_tsv(output_paths["minimum_human_collection_sheet"], human_fieldnames, minimum_rows)
    write_tsv(output_paths["full_human_collection_sheet"], human_fieldnames, full_rows)
    write_jsonl(output_paths["minimum_manifest_post_label_only"], minimum_manifest)
    write_jsonl(output_paths["full_manifest_post_label_only"], full_manifest)
    write_json(output_paths["sampling_plan"], sampling_plan)
    write_jsonl(output_paths["labeler_header_leakage_hits"], hits)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    minimum = summary["bootstrap_estimates"]["minimum_human_batch"]
    full = summary["bootstrap_estimates"]["full_human_batch"]
    print(
        f"status={summary['status']} min_rows={counts['minimum_human_batch_rows']} "
        f"min_est_binary={minimum['estimated_relation_binary']} "
        f"min_est_pos={minimum['estimated_relation_positive']} min_est_neg={minimum['estimated_relation_negative']} "
        f"full_rows={counts['full_human_batch_rows']} full_est_binary={full['estimated_relation_binary']} "
        f"leakage={counts['labeler_header_leakage_hits']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"test_used={summary['boundary']['test_usage']} next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
