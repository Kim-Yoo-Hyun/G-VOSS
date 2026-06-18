#!/usr/bin/env python3
"""Revise the support/vertical label policy after target-independence failure."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_INGESTION_DIR = RGA_ROOT / "independent_support_vertical_label_ingestion_codex_ver"
DEFAULT_AUDIT_DIR = RGA_ROOT / "independent_support_vertical_target_independence_audit_codex_ver"
DEFAULT_READINESS_DIR = RGA_ROOT / "independent_support_vertical_label_readiness_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_label_policy_revision_codex_ver"

DEFAULT_VALIDATED_LABELS = DEFAULT_INGESTION_DIR / "validated_labels.jsonl"
DEFAULT_POSTERIOR_ROWS = DEFAULT_INGESTION_DIR / "posterior_rows.jsonl"
DEFAULT_TARGET_AUDIT_SUMMARY = DEFAULT_AUDIT_DIR / "summary.json"
DEFAULT_SOURCE_SHEET = DEFAULT_READINESS_DIR / "support_vertical_label_fill_sheet.tsv"

OLD_COMPLETION_FIELDS = {
    "reviewer_id",
    "review_round",
    "subject_identity_valid",
    "object_identity_valid",
    "object_pair_visible",
    "relation_visible_or_inferable",
    "visual_3d_support",
    "relation_informativeness",
    "independent_relation_label",
    "confidence",
    "evidence_notes",
}

V2_COMPLETION_FIELDS = [
    "reviewer_id",
    "review_round",
    "endpoint_validity_v2",
    "pair_visibility_v2",
    "relation_geometry_answer_v2",
    "geometry_evidence_strength_v2",
    "relation_informativeness_v2",
    "ontology_fit_v2",
    "uncertainty_reason_v2",
    "audit_notes_v2",
]

V2_ALLOWED_VALUES = {
    "endpoint_validity_v2": [
        "both_valid",
        "subject_invalid",
        "object_invalid",
        "pair_invalid",
        "uncertain",
    ],
    "pair_visibility_v2": [
        "visible",
        "partially_visible",
        "not_visible",
        "uncertain",
    ],
    "relation_geometry_answer_v2": [
        "supports_predicate",
        "contradicts_predicate",
        "ambiguous",
        "not_evaluable",
    ],
    "geometry_evidence_strength_v2": [
        "strong",
        "moderate",
        "weak",
        "none",
    ],
    "relation_informativeness_v2": [
        "informative",
        "dense_trivial",
        "redundant_room_structure",
        "uncertain",
    ],
    "ontology_fit_v2": [
        "fits_predicate",
        "better_alternative_predicate",
        "ontology_mismatch",
        "uncertain",
    ],
    "uncertainty_reason_v2": [
        "none",
        "endpoint_identity",
        "visibility_or_occlusion",
        "weak_geometry",
        "dense_relation",
        "ontology_ambiguity",
        "needs_multiview_or_mesh",
        "other",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validated-labels", type=Path, default=DEFAULT_VALIDATED_LABELS)
    parser.add_argument("--posterior-rows", type=Path, default=DEFAULT_POSTERIOR_ROWS)
    parser.add_argument("--target-audit-summary", type=Path, default=DEFAULT_TARGET_AUDIT_SUMMARY)
    parser.add_argument("--source-sheet", type=Path, default=DEFAULT_SOURCE_SHEET)
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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
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


def entropy_from_counts(counts: Counter[Any]) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    value = 0.0
    for count in counts.values():
        if count <= 0:
            continue
        p = count / total
        value -= p * math.log2(p)
    return value


def hidden_value(row: dict[str, Any], key: str) -> str:
    hidden = row.get("hidden_audit_metadata_post_label_only", {})
    return str(hidden.get(key))


def target_y(row: dict[str, Any]) -> int | None:
    value = row.get("posterior_target")
    if value is None:
        return None
    return int(value)


def association_summary(rows: list[dict[str, Any]], key: str, target_key: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if key.startswith("hidden."):
            value = hidden_value(row, key.split(".", 1)[1])
        else:
            value = str(row.get(key))
        by_group[value].append(row)

    table: list[dict[str, Any]] = []
    total_counts: Counter[Any] = Counter(str(row.get(target_key)) for row in rows)
    overall_entropy = entropy_from_counts(total_counts)
    weighted_conditional_entropy = 0.0
    majority_correct = 0
    for value, group_rows in sorted(by_group.items()):
        counts: Counter[Any] = Counter(str(row.get(target_key)) for row in group_rows)
        total = sum(counts.values())
        majority_label, majority_count = counts.most_common(1)[0]
        majority_correct += majority_count
        weighted_conditional_entropy += total / len(rows) * entropy_from_counts(counts) if rows else 0.0
        table.append(
            {
                "source_key": key,
                "target_key": target_key,
                "group_value": value,
                "rows": total,
                "majority_label": majority_label,
                "majority_accuracy": majority_count / total if total else 0.0,
                "label_counts": json.dumps(dict(sorted(counts.items())), sort_keys=True),
            }
        )
    mutual_info = max(0.0, overall_entropy - weighted_conditional_entropy)
    summary = {
        "source_key": key,
        "target_key": target_key,
        "groups": len(by_group),
        "rows": len(rows),
        "overall_entropy_bits": overall_entropy,
        "conditional_entropy_bits": weighted_conditional_entropy,
        "mutual_information_bits": mutual_info,
        "normalized_mutual_information": mutual_info / overall_entropy if overall_entropy > 0 else 0.0,
        "majority_rule_accuracy": majority_correct / len(rows) if rows else 0.0,
    }
    return table, summary


def binary_policy_transfer(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        prior_label = hidden_value(row, "relation_validity_label_hidden")
        current_label = str(row.get("independent_relation_label"))
        prior_use = hidden_value(row, "label_use_hidden")
        current_use = str(row.get("label_use"))
        output.append(
            {
                "blind_review_id": row["blind_review_id"],
                "predicate_family": row["predicate_family"],
                "predicate_label": row["predicate_label"],
                "prior_relation_validity_label_hidden": prior_label,
                "current_independent_relation_label": current_label,
                "prior_label_use_hidden": prior_use,
                "current_label_use": current_use,
                "same_label": prior_label == current_label,
                "same_use": prior_use == current_use,
                "posterior_target": row.get("posterior_target"),
            }
        )
    return output


def build_v2_schema() -> dict[str, Any]:
    return {
        "schema_version": "h002_support_vertical_label_policy_v2_schema",
        "purpose": "second-pass factual-axis review; no direct reliability/binary label field",
        "required_completion_fields": V2_COMPLETION_FIELDS[:-1],
        "optional_completion_fields": ["audit_notes_v2"],
        "allowed_review_values": V2_ALLOWED_VALUES,
        "removed_fields_from_v1": sorted(OLD_COMPLETION_FIELDS),
        "target_derivation_policy_post_label_only": {
            "geometry_validity_target_v2": {
                "positive": {
                    "relation_geometry_answer_v2": ["supports_predicate"],
                    "geometry_evidence_strength_v2": ["strong", "moderate"],
                },
                "negative": {
                    "relation_geometry_answer_v2": ["contradicts_predicate"],
                },
                "exclude": {
                    "relation_geometry_answer_v2": ["ambiguous", "not_evaluable"],
                    "geometry_evidence_strength_v2": ["weak", "none"],
                },
            },
            "relation_reliability_target_v2": {
                "positive": {
                    "endpoint_validity_v2": ["both_valid"],
                    "pair_visibility_v2": ["visible", "partially_visible"],
                    "relation_geometry_answer_v2": ["supports_predicate"],
                    "geometry_evidence_strength_v2": ["strong", "moderate"],
                    "relation_informativeness_v2": ["informative"],
                    "ontology_fit_v2": ["fits_predicate"],
                },
                "negative": {
                    "endpoint_validity_v2": ["subject_invalid", "object_invalid", "pair_invalid"],
                    "relation_geometry_answer_v2": ["contradicts_predicate"],
                    "relation_informativeness_v2": ["dense_trivial", "redundant_room_structure"],
                    "ontology_fit_v2": ["better_alternative_predicate", "ontology_mismatch"],
                },
                "exclude": {
                    "endpoint_validity_v2": ["uncertain"],
                    "pair_visibility_v2": ["not_visible", "uncertain"],
                    "relation_geometry_answer_v2": ["ambiguous", "not_evaluable"],
                    "geometry_evidence_strength_v2": ["weak", "none"],
                    "relation_informativeness_v2": ["uncertain"],
                    "ontology_fit_v2": ["uncertain"],
                },
            },
        },
        "boundary": {
            "direct_reliability_label_removed": True,
            "binary_target_not_labeler_visible": True,
            "hidden_metadata_join_after_label_lock_only": True,
            "multi_view_as_model_input": False,
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
        },
    }


def build_feature_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_support_vertical_feature_contract_v2",
        "allowed_deployable_inputs_after_label_lock": [
            "source semantic score/rank normalized within source context",
            "continuous geometry evidence from raw witness values",
            "automatic geometry coverage/missingness indicators",
            "automatic relation family/predicate identity for stratified calibration only if explicitly ablated",
        ],
        "audit_only_not_model_input": [
            "endpoint_validity_v2",
            "pair_visibility_v2",
            "relation_geometry_answer_v2",
            "geometry_evidence_strength_v2",
            "relation_informativeness_v2",
            "ontology_fit_v2",
            "uncertainty_reason_v2",
            "reviewer_id",
            "review_round",
            "audit_notes_v2",
            "hidden relation_validity_label",
            "hidden label_use",
            "hidden proposed_audit_role",
            "hidden label_match_status",
            "hidden geometry_status",
            "human/codex reviewer confidence",
        ],
        "reason": (
            "The failed target-independence audit showed that direct relation labels "
            "and review confidence/visibility fields can become target-construction "
            "shortcuts rather than deployable evidence."
        ),
    }


def build_second_pass_rows(fieldnames: list[str], rows: list[dict[str, str]]) -> tuple[list[str], list[dict[str, str]]]:
    preserved_fields = [field for field in fieldnames if field not in OLD_COMPLETION_FIELDS]
    output_fields = preserved_fields + V2_COMPLETION_FIELDS
    output_rows: list[dict[str, str]] = []
    for row in rows:
        output = {field: row.get(field, "") for field in preserved_fields}
        output["audit_scope"] = "selected_support_vertical_label_policy_v2"
        for field in V2_COMPLETION_FIELDS:
            output[field] = ""
        output_rows.append(output)
    return output_fields, output_rows


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Support/Vertical Label Policy Revision",
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
        "## Current Policy Failure",
        "",
        "| Key | Target | Majority Acc | NMI |",
        "| --- | --- | ---: | ---: |",
    ]
    for item in summary["association_summaries"]:
        lines.append(
            f"| `{item['source_key']}` | `{item['target_key']}` | "
            f"{item['majority_rule_accuracy']:.4f} | {item['normalized_mutual_information']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## V2 Change",
            "",
            "- remove direct `independent_relation_label` from the review sheet.",
            "- split review into factual axes: endpoint validity, visibility, geometry answer, evidence strength, informativeness, ontology fit, uncertainty reason.",
            "- derive binary targets only after label lock.",
            "- keep reviewer confidence/visibility fields audit-only rather than posterior input.",
            "",
            "## V2 Sheets",
            "",
            f"- all: `{summary['output_paths']['second_pass_sheet']}`",
            f"- support_contact: `{summary['output_paths']['support_contact_sheet']}`",
            f"- relative_vertical: `{summary['output_paths']['relative_vertical_sheet']}`",
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    validated_path = as_abs(args.validated_labels)
    posterior_path = as_abs(args.posterior_rows)
    audit_summary_path = as_abs(args.target_audit_summary)
    source_sheet_path = as_abs(args.source_sheet)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    validated_rows = read_jsonl(validated_path)
    posterior_rows = read_jsonl(posterior_path)
    audit_summary = read_json(audit_summary_path)
    fieldnames, source_rows = read_tsv(source_sheet_path)

    association_tables: list[dict[str, Any]] = []
    association_summaries: list[dict[str, Any]] = []
    for source_key, target_key in [
        ("hidden.relation_validity_label_hidden", "independent_relation_label"),
        ("hidden.label_use_hidden", "label_use"),
        ("predicate_family", "independent_relation_label"),
        ("predicate_label", "independent_relation_label"),
        ("confidence", "independent_relation_label"),
        ("visual_3d_support", "independent_relation_label"),
        ("relation_informativeness", "independent_relation_label"),
    ]:
        table, summary = association_summary(validated_rows, source_key, target_key)
        association_tables.extend(table)
        association_summaries.append(summary)

    transfer_rows = binary_policy_transfer(validated_rows)
    transfer_counts = Counter((row["same_label"], row["same_use"]) for row in transfer_rows)
    schema = build_v2_schema()
    feature_contract = build_feature_contract()
    output_fields, second_pass_rows = build_second_pass_rows(fieldnames, source_rows)
    support_rows = [row for row in second_pass_rows if row.get("predicate_family") == "support_contact"]
    vertical_rows = [row for row in second_pass_rows if row.get("predicate_family") == "relative_vertical"]

    summary_path = output_dir / "summary.json"
    report_path = output_dir / "report.md"
    schema_path = output_dir / "v2_completion_schema.json"
    feature_contract_path = output_dir / "v2_feature_contract.json"
    carryover_table_path = output_dir / "carryover_table.csv"
    carryover_matrix_path = output_dir / "carryover_matrix.jsonl"
    second_pass_sheet_path = output_dir / "support_vertical_v2_label_sheet.tsv"
    support_sheet_path = output_dir / "support_contact_v2_label_sheet.tsv"
    vertical_sheet_path = output_dir / "relative_vertical_v2_label_sheet.tsv"

    strict_blocked = audit_summary.get("recommended_strict_slice") is None
    construction_available = audit_summary.get("recommended_construction_slice") is not None
    status = "full_train_independent_support_vertical_label_policy_revision_ready_for_v2_readiness"
    decision = (
        "Direct reliability-label filling caused prior-label carryover. V2 removes the "
        "direct relation reliability label from the labeler surface and separates factual "
        "review axes from post-label target derivation."
    )
    next_todo = "full_train_independent_support_vertical_v2_label_readiness"

    summary = {
        "schema_version": "h002_support_vertical_label_policy_revision_summary_v1",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "validated_labels": rel_path(validated_path),
            "posterior_rows": rel_path(posterior_path),
            "target_audit_summary": rel_path(audit_summary_path),
            "source_sheet": rel_path(source_sheet_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {
            "summary": rel_path(summary_path),
            "report": rel_path(report_path),
            "v2_completion_schema": rel_path(schema_path),
            "v2_feature_contract": rel_path(feature_contract_path),
            "carryover_table": rel_path(carryover_table_path),
            "carryover_matrix": rel_path(carryover_matrix_path),
            "second_pass_sheet": rel_path(second_pass_sheet_path),
            "support_contact_sheet": rel_path(support_sheet_path),
            "relative_vertical_sheet": rel_path(vertical_sheet_path),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "hidden_metadata_used_for_policy_audit_only": True,
            "multi_view_as_model_input": False,
        },
        "counts": {
            "validated_labels": len(validated_rows),
            "posterior_rows": len(posterior_rows),
            "source_sheet_rows": len(source_rows),
            "second_pass_sheet_rows": len(second_pass_rows),
            "support_contact_rows": len(support_rows),
            "relative_vertical_rows": len(vertical_rows),
            "same_prior_relation_label_rows": sum(1 for row in transfer_rows if row["same_label"]),
            "same_prior_label_use_rows": sum(1 for row in transfer_rows if row["same_use"]),
        },
        "target_audit_status": audit_summary.get("status"),
        "strict_blocked": strict_blocked,
        "construction_diagnostic_available": construction_available,
        "association_summaries": association_summaries,
        "transfer_counts": {str(key): value for key, value in sorted(transfer_counts.items())},
        "v2_policy_summary": {
            "direct_reliability_label_removed": True,
            "review_axes": V2_COMPLETION_FIELDS,
            "binary_target_derived_post_label_only": True,
            "confidence_and_visibility_not_model_inputs": True,
        },
        "decision": decision,
        "next_todo": next_todo,
    }

    write_json(summary_path, summary)
    write_json(report_path.with_suffix(".debug.json"), {"association_tables": association_tables})
    write_json(schema_path, schema)
    write_json(feature_contract_path, feature_contract)
    write_csv(carryover_table_path, association_tables)
    write_jsonl(carryover_matrix_path, transfer_rows)
    write_tsv(second_pass_sheet_path, output_fields, second_pass_rows)
    write_tsv(support_sheet_path, output_fields, support_rows)
    write_tsv(vertical_sheet_path, output_fields, vertical_rows)
    write_report(report_path, summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    print(
        f"status={summary['status']} rows={counts['second_pass_sheet_rows']} "
        f"support={counts['support_contact_rows']} vertical={counts['relative_vertical_rows']} "
        f"same_label={counts['same_prior_relation_label_rows']} "
        f"same_use={counts['same_prior_label_use_rows']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
