#!/usr/bin/env python3
"""Ingest H002 full-train independent labels after label lock."""

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
DEFAULT_FILL_DIR = RGA_ROOT / "independent_label_fill_codex_ver"
DEFAULT_READINESS_DIR = RGA_ROOT / "independent_label_readiness"
DEFAULT_PROTOCOL_DIR = RGA_ROOT / "independent_label_protocol"
DEFAULT_GAP_DIR = RGA_ROOT / "asset_packet_gap_audit"
DEFAULT_COMPLETED_SHEET = DEFAULT_FILL_DIR / "completed_all_sheet_codex_ver.tsv"
DEFAULT_INTERNAL_KEY = DEFAULT_PROTOCOL_DIR / "internal_key.jsonl"
DEFAULT_SCHEMA = DEFAULT_READINESS_DIR / "label_ingestion_schema.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_label_ingestion_codex_ver"

FORBIDDEN_COMPLETED_HEADER_FRAGMENTS = [
    "score",
    "rank",
    "p_geom",
    "geometry_status",
    "h001_verification",
    "queue",
    "label_match",
    "proposed",
    "role",
    "candidate_axis",
    "prediction_id",
    "final_controlled",
    "failure_taxonomy",
    "matched_gt",
    "matched_predicate",
    "bucket",
    "machine_hint",
    "reason_code",
    "semantic",
    "consistency",
    "disagreement",
    "underconfidence",
]

LABEL_USE = {
    "reliable_informative": "positive",
    "annotation_sparsity_candidate": "positive",
    "valid_but_trivial_dense": "negative",
    "invalid_relation": "negative",
    "invalid_pair": "negative",
    "visibility_or_geometry_artifact": "negative",
    "ontology_mismatch": "exclude_or_multiclass_only",
    "abstain_uncertain": "exclude_or_multiclass_only",
}

HIDDEN_GROUP_KEYS = [
    "queue_kind_hidden",
    "candidate_axis_hidden",
    "proposed_audit_role_hidden",
    "label_match_status_hidden",
    "geometry_status_hidden",
    "h001_verification_status_hidden",
    "rank_band_hidden",
    "label_geometry_bucket_hidden",
    "bucket_top50_hidden",
    "bucket_top100_hidden",
]

VISIBLE_GROUP_KEYS = [
    "predicate_family",
    "predicate_label",
    "confidence",
    "visual_3d_support",
    "relation_informativeness",
    "packet_gap_decision",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--completed-sheet", type=Path, default=DEFAULT_COMPLETED_SHEET)
    parser.add_argument("--internal-key", type=Path, default=DEFAULT_INTERNAL_KEY)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--gap-dir", type=Path, default=DEFAULT_GAP_DIR)
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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def nonempty(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def label_use(label: str) -> str:
    return LABEL_USE[label]


def binary_y(use: str) -> int | None:
    if use == "positive":
        return 1
    if use == "negative":
        return 0
    return None


def validate_headers(fieldnames: list[str]) -> list[dict[str, Any]]:
    errors = []
    for field in fieldnames:
        lower = field.lower()
        matches = [token for token in FORBIDDEN_COMPLETED_HEADER_FRAGMENTS if token in lower]
        if matches:
            errors.append(
                {
                    "error_type": "forbidden_completed_header",
                    "field": field,
                    "matches": matches,
                }
            )
    if "blind_review_id" not in fieldnames:
        errors.append({"error_type": "missing_required_header", "field": "blind_review_id"})
    if "independent_relation_label" not in fieldnames:
        errors.append({"error_type": "missing_required_header", "field": "independent_relation_label"})
    return errors


def completion_errors(row: dict[str, str], row_number: int, schema: dict[str, Any]) -> list[dict[str, Any]]:
    errors = []
    for field in schema["required_completion_fields"]:
        if not nonempty(row.get(field)):
            errors.append(
                {
                    "error_type": "missing_required_completion_field",
                    "row_number": row_number,
                    "blind_review_id": row.get("blind_review_id"),
                    "field": field,
                }
            )
    allowed_values = schema["allowed_review_values"]
    for field, allowed in allowed_values.items():
        value = str(row.get(field) or "").strip()
        if value and value not in set(allowed):
            errors.append(
                {
                    "error_type": "invalid_review_value",
                    "row_number": row_number,
                    "blind_review_id": row.get("blind_review_id"),
                    "field": field,
                    "value": value,
                    "allowed": allowed,
                }
            )
    return errors


def hidden_provenance(internal: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "review_id_hidden",
        "prediction_id_hidden",
        "queue_kind_hidden",
        "candidate_axis_hidden",
        "proposed_audit_role_hidden",
        "role_reason_hidden",
        "label_match_status_hidden",
        "geometry_status_hidden",
        "h001_verification_status_hidden",
        "semantic_rank_hidden",
        "rank_band_hidden",
        "semantic_score_raw_hidden",
        "semantic_score_norm_hidden",
        "p_geom_valid_hidden",
        "consistency_score_hidden",
        "disagreement_score_hidden",
        "underconfidence_score_hidden",
        "label_geometry_bucket_hidden",
        "bucket_top50_hidden",
        "bucket_top100_hidden",
        "machine_hint_hidden",
        "matched_predicates_hidden",
        "matched_gt_ids_hidden",
        "reason_codes_hidden",
    ]
    return {key: internal.get(key) for key in keys}


def evidence_features(internal: dict[str, Any]) -> dict[str, Any]:
    return {
        "semantic_score_raw": safe_float(internal.get("semantic_score_raw_hidden")),
        "semantic_score_norm": safe_float(internal.get("semantic_score_norm_hidden")),
        "semantic_rank": safe_float(internal.get("semantic_rank_hidden")),
        "p_geom_valid": safe_float(internal.get("p_geom_valid_hidden")),
        "consistency_score": safe_float(internal.get("consistency_score_hidden")),
        "disagreement_score": safe_float(internal.get("disagreement_score_hidden")),
        "underconfidence_score": safe_float(internal.get("underconfidence_score_hidden")),
    }


def make_joined_label(row: dict[str, str], internal: dict[str, Any]) -> dict[str, Any]:
    label = str(row["independent_relation_label"]).strip()
    use = label_use(label)
    y = binary_y(use)
    return {
        "schema_version": "h002_full_train_independent_ingested_label_v0",
        "blind_review_id": row["blind_review_id"],
        "asset_request_id": row["asset_request_id"],
        "prediction_id": internal["prediction_id_hidden"],
        "scan_id": internal["scan_id"],
        "subgraph_id": internal["subgraph_id"],
        "subject_id": internal["subject_id"],
        "subject_label": internal["subject_label"],
        "predicate_label": internal["predicate_label"],
        "predicate_family": internal["predicate_family"],
        "object_id": internal["object_id"],
        "object_label": internal["object_label"],
        "independent_relation_label": label,
        "label_use": use,
        "posterior_target": y,
        "binary_usable": y is not None,
        "reviewer_id": row.get("reviewer_id"),
        "review_round": row.get("review_round"),
        "subject_identity_valid": row.get("subject_identity_valid"),
        "object_identity_valid": row.get("object_identity_valid"),
        "object_pair_visible": row.get("object_pair_visible"),
        "relation_visible_or_inferable": row.get("relation_visible_or_inferable"),
        "visual_3d_support": row.get("visual_3d_support"),
        "relation_informativeness": row.get("relation_informativeness"),
        "confidence": row.get("confidence"),
        "evidence_packet_status": row.get("evidence_packet_status"),
        "packet_gap_decision": row.get("packet_gap_decision"),
        "evidence_notes": row.get("evidence_notes"),
        "deployable_evidence_after_label_lock": evidence_features(internal),
        "hidden_audit_metadata_post_label_only": hidden_provenance(internal),
        "boundary": {
            "split": "train_only",
            "label_source": "codex_ver_full_train_independent_visible_surface_bootstrap",
            "not_human_confirmed": True,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "hidden_metadata_joined_after_label_lock": True,
            "target_construction_metadata_is_not_deployable_input": True,
        },
    }


def build_targets(labels: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    multiclass = []
    binary = []
    posterior_rows = []
    for label in labels:
        base = {
            "blind_review_id": label["blind_review_id"],
            "prediction_id": label["prediction_id"],
            "scan_id": label["scan_id"],
            "subgraph_id": label["subgraph_id"],
            "subject_id": label["subject_id"],
            "subject_label": label["subject_label"],
            "predicate_label": label["predicate_label"],
            "predicate_family": label["predicate_family"],
            "object_id": label["object_id"],
            "object_label": label["object_label"],
            "independent_relation_label": label["independent_relation_label"],
            "label_use": label["label_use"],
            "reviewer_id": label["reviewer_id"],
            "confidence": label["confidence"],
        }
        multiclass.append(
            {
                "schema_version": "h002_full_train_independent_multiclass_target_v0",
                **base,
                "allowed_use": "train-only independent label taxonomy and reliability diagnostics",
                "paper_locked": False,
            }
        )
        if label["binary_usable"]:
            binary_row = {
                "schema_version": "h002_full_train_independent_binary_target_v0",
                **base,
                "posterior_target": label["posterior_target"],
                "allowed_use": "train-only independent posterior diagnostic",
                "paper_locked": False,
                "human_confirmed": False,
            }
            binary.append(binary_row)
            posterior_rows.append(
                {
                    **binary_row,
                    "schema_version": "h002_full_train_independent_posterior_row_v0",
                    "deployable_evidence_after_label_lock": label["deployable_evidence_after_label_lock"],
                    "hidden_audit_metadata_post_label_only": label["hidden_audit_metadata_post_label_only"],
                    "audit_note": (
                        "Use deployable evidence for posterior diagnostics. Use hidden audit "
                        "metadata only for target-independence probes."
                    ),
                }
            )
    return multiclass, binary, posterior_rows


def entropy(pos: int, neg: int) -> float:
    total = pos + neg
    if total == 0:
        return 0.0
    value = 0.0
    for count in [pos, neg]:
        if count <= 0:
            continue
        p = count / total
        value -= p * math.log2(p)
    return value


def group_target_value(row: dict[str, Any], key: str) -> str:
    if key in row:
        return str(row.get(key))
    hidden = row["hidden_audit_metadata_post_label_only"]
    if key in hidden:
        return str(hidden.get(key))
    return "missing"


def group_probe(rows: list[dict[str, Any]], key: str, source: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[group_target_value(row, key)].append(row)

    total_counts = Counter(int(row["posterior_target"]) for row in rows)
    overall_entropy = entropy(total_counts[1], total_counts[0])
    weighted_conditional_entropy = 0.0
    majority_correct = 0
    table = []
    for value, group_rows in sorted(groups.items()):
        counts = Counter(int(row["posterior_target"]) for row in group_rows)
        pos = counts[1]
        neg = counts[0]
        majority_label = 1 if pos >= neg else 0
        majority = max(pos, neg)
        group_entropy = entropy(pos, neg)
        weighted_conditional_entropy += len(group_rows) / len(rows) * group_entropy if rows else 0.0
        majority_correct += majority
        table.append(
            {
                "source": source,
                "group_key": key,
                "group_value": value,
                "rows": len(group_rows),
                "positive": pos,
                "negative": neg,
                "positive_rate": pos / len(group_rows) if group_rows else 0.0,
                "majority_label": majority_label,
                "majority_accuracy": majority / len(group_rows) if group_rows else 0.0,
                "entropy_bits": group_entropy,
            }
        )
    mutual_info = max(0.0, overall_entropy - weighted_conditional_entropy)
    summary = {
        "source": source,
        "group_key": key,
        "groups": len(groups),
        "rows": len(rows),
        "overall_positive": total_counts[1],
        "overall_negative": total_counts[0],
        "overall_entropy_bits": overall_entropy,
        "conditional_entropy_bits": weighted_conditional_entropy,
        "mutual_information_bits": mutual_info,
        "normalized_mutual_information": mutual_info / overall_entropy if overall_entropy > 0 else 0.0,
        "majority_rule_accuracy": majority_correct / len(rows) if rows else 0.0,
    }
    return table, summary


def target_independence_probe(posterior_rows: list[dict[str, Any]]) -> dict[str, Any]:
    table_rows: list[dict[str, Any]] = []
    summaries = []
    for key in VISIBLE_GROUP_KEYS:
        table, summary = group_probe(posterior_rows, key, "visible_label_surface")
        table_rows.extend(table)
        summaries.append(summary)
    for key in HIDDEN_GROUP_KEYS:
        table, summary = group_probe(posterior_rows, key, "hidden_post_label_audit")
        table_rows.extend(table)
        summaries.append(summary)

    hidden_risks = [
        item
        for item in summaries
        if item["source"] == "hidden_post_label_audit"
        and (
            item["majority_rule_accuracy"] >= 0.85
            or item["normalized_mutual_information"] >= 0.25
        )
    ]
    visible_shortcuts = [
        item
        for item in summaries
        if item["source"] == "visible_label_surface"
        and (
            item["majority_rule_accuracy"] >= 0.85
            or item["normalized_mutual_information"] >= 0.25
        )
    ]
    if hidden_risks:
        status = "target_independence_risk_hidden_metadata_correlated"
    elif visible_shortcuts:
        status = "target_independence_risk_visible_policy_shortcut"
    else:
        status = "target_independence_probe_pass"
    return {
        "schema_version": "h002_full_train_independent_target_probe_v0",
        "status": status,
        "risk_thresholds": {
            "majority_rule_accuracy": 0.85,
            "normalized_mutual_information": 0.25,
        },
        "summaries": summaries,
        "group_table": table_rows,
        "hidden_risks": hidden_risks,
        "visible_shortcuts": visible_shortcuts,
    }


def ingest(
    completed_rows: list[dict[str, str]],
    internal_rows: list[dict[str, Any]],
    schema: dict[str, Any],
    excluded_ids: set[str],
) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []
    internal_by_id = {str(row["blind_review_id"]): row for row in internal_rows}
    seen = Counter(str(row.get("blind_review_id") or "") for row in completed_rows)
    for blind_id, count in seen.items():
        if count > 1:
            errors.append({"error_type": "duplicate_blind_review_id", "blind_review_id": blind_id, "count": count})

    for row_number, row in enumerate(completed_rows, start=2):
        blind_id = str(row.get("blind_review_id") or "")
        if not blind_id:
            errors.append({"error_type": "missing_blind_review_id", "row_number": row_number})
            continue
        if blind_id in excluded_ids:
            errors.append(
                {
                    "error_type": "excluded_blind_id_in_completed_sheet",
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                }
            )
            continue
        internal = internal_by_id.get(blind_id)
        if internal is None:
            errors.append(
                {
                    "error_type": "unknown_blind_review_id",
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                }
            )
            continue
        errors.extend(completion_errors(row, row_number, schema))
        if any(error.get("row_number") == row_number for error in errors):
            continue
        labels.append(make_joined_label(row, internal))
    return {"errors": errors, "validated_labels": labels}


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    probe = summary["target_independence_probe"]
    lines = [
        "# H002 Full Train Independent Label Ingestion",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage ingestion.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Completed labels are joined to hidden provenance only after label lock.",
        "- Hidden target-construction metadata is audit-only, not deployable input.",
        "- Labels are Codex bootstrap labels, not human-confirmed paper evidence.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| completed sheet rows | {counts['completed_sheet_rows']} |",
        f"| validated label rows | {counts['validated_label_rows']} |",
        f"| binary target rows | {counts['binary_target_rows']} |",
        f"| positive rows | {counts['positive_rows']} |",
        f"| negative rows | {counts['negative_rows']} |",
        f"| multiclass target rows | {counts['multiclass_target_rows']} |",
        f"| ingestion errors | {counts['errors']} |",
        "",
        "## Label Counts",
        "",
        "| Label | Rows |",
        "| --- | ---: |",
    ]
    for label, count in summary["label_counts"].items():
        lines.append(f"| `{label}` | {count} |")
    lines.extend(
        [
            "",
            "## Target Probe",
            "",
            f"Probe status: `{probe['status']}`",
            "",
            "| Source | Group Key | Majority Acc | NMI |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for item in sorted(
        probe["summaries"],
        key=lambda row: (row["source"], -row["majority_rule_accuracy"], -row["normalized_mutual_information"]),
    )[:16]:
        lines.append(
            "| `{source}` | `{group_key}` | {majority_rule_accuracy:.4f} | {normalized_mutual_information:.4f} |".format(
                **item
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Next TODO",
            "",
            summary["next_todo"],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    completed_sheet = as_abs(args.completed_sheet)
    internal_key = as_abs(args.internal_key)
    schema_path = as_abs(args.schema)
    gap_dir = as_abs(args.gap_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    fieldnames, completed_rows = read_tsv(completed_sheet)
    schema = read_json(schema_path)
    internal_rows = read_jsonl(internal_key)
    excluded_ids_path = gap_dir / "excluded_blind_ids.txt"
    excluded_ids = {
        line.strip()
        for line in excluded_ids_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }

    ingestion = ingest(completed_rows, internal_rows, schema, excluded_ids)
    ingestion["errors"] = validate_headers(fieldnames) + ingestion["errors"]
    validated_labels = ingestion["validated_labels"]
    multiclass_targets, binary_targets, posterior_rows = build_targets(validated_labels)
    probe = target_independence_probe(posterior_rows) if posterior_rows else {
        "schema_version": "h002_full_train_independent_target_probe_v0",
        "status": "target_independence_probe_no_binary_rows",
        "summaries": [],
        "group_table": [],
        "hidden_risks": [],
        "visible_shortcuts": [],
    }

    target_counts = Counter(row["posterior_target"] for row in binary_targets)
    label_counts = dict(sorted(Counter(row["independent_relation_label"] for row in validated_labels).items()))

    if ingestion["errors"]:
        status = "full_train_independent_label_ingestion_errors"
        decision = "Fix completed-sheet schema or label errors before materializing posterior targets."
        next_todo = "fix_full_train_independent_label_ingestion_errors"
    elif not binary_targets:
        status = "full_train_independent_label_ingestion_no_binary_targets"
        decision = "Labels were ingested, but no binary target rows were created."
        next_todo = "revise_full_train_independent_label_policy"
    elif probe["status"] != "target_independence_probe_pass":
        status = "full_train_independent_label_ingested_with_target_policy_risk"
        decision = (
            "Labels and targets are materialized, but group-level target probe shows "
            "policy/metadata shortcut risk. Run a dedicated target-independence audit "
            "before posterior smoke."
        )
        next_todo = "full_train_independent_target_independence_audit"
    else:
        status = "full_train_independent_label_ingested_ready_for_posterior_smoke"
        decision = (
            "Labels and targets are materialized with no basic group-level shortcut "
            "risk. Posterior smoke may resume as train-only diagnostics."
        )
        next_todo = "full_train_independent_posterior_smoke"

    summary_path = output_dir / "summary.json"
    report_path = output_dir / "report.md"
    validated_path = output_dir / "validated_labels.jsonl"
    binary_path = output_dir / "binary_targets.jsonl"
    multiclass_path = output_dir / "multiclass_targets.jsonl"
    posterior_path = output_dir / "posterior_rows.jsonl"
    errors_path = output_dir / "ingestion_errors.jsonl"
    probe_path = output_dir / "target_independence_probe.json"
    group_table_path = output_dir / "target_group_table.csv"

    summary = {
        "schema_version": "h002_full_train_independent_label_ingestion_summary_v0",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "completed_sheet": rel_path(completed_sheet),
            "internal_key": rel_path(internal_key),
            "schema": rel_path(schema_path),
            "excluded_blind_ids": rel_path(excluded_ids_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {
            "summary": rel_path(summary_path),
            "report": rel_path(report_path),
            "validated_labels": rel_path(validated_path),
            "binary_targets": rel_path(binary_path),
            "multiclass_targets": rel_path(multiclass_path),
            "posterior_rows": rel_path(posterior_path),
            "ingestion_errors": rel_path(errors_path),
            "target_independence_probe": rel_path(probe_path),
            "target_group_table": rel_path(group_table_path),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "label_source": "codex_ver_full_train_independent_visible_surface_bootstrap",
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "hidden_metadata_joined_after_label_lock": True,
            "target_construction_metadata_is_deployable_input": False,
            "vmv_model_input_allowed": False,
        },
        "counts": {
            "completed_sheet_rows": len(completed_rows),
            "validated_label_rows": len(validated_labels),
            "binary_target_rows": len(binary_targets),
            "positive_rows": target_counts[1],
            "negative_rows": target_counts[0],
            "multiclass_target_rows": len(multiclass_targets),
            "errors": len(ingestion["errors"]),
            "internal_key_rows": len(internal_rows),
            "excluded_rows": len(excluded_ids),
        },
        "label_counts": label_counts,
        "target_independence_probe": {
            key: value for key, value in probe.items() if key != "group_table"
        },
        "decision": decision,
        "next_todo": next_todo,
    }

    write_json(summary_path, summary)
    write_json(probe_path, probe)
    write_jsonl(validated_path, validated_labels)
    write_jsonl(binary_path, binary_targets)
    write_jsonl(multiclass_path, multiclass_targets)
    write_jsonl(posterior_path, posterior_rows)
    write_jsonl(errors_path, ingestion["errors"])
    write_csv(group_table_path, probe["group_table"])
    write_report(report_path, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    counts = summary["counts"]
    print(
        f"status={summary['status']} labels={counts['validated_label_rows']} "
        f"binary={counts['binary_target_rows']} positive={counts['positive_rows']} "
        f"negative={counts['negative_rows']} errors={counts['errors']} "
        f"probe={summary['target_independence_probe']['status']} "
        f"validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
