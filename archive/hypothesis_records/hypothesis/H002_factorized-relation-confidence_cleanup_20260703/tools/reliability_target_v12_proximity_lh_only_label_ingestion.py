#!/usr/bin/env python3
"""Ingest H002 proximity LH-only filled labels and run quick shortcut probes."""

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

FILL_DIR = RGA_ROOT / "reliability_target_v12_proximity_lh_only_label_fill"
READINESS_DIR = RGA_ROOT / "reliability_target_v12_proximity_lh_only_label_readiness"

DEFAULT_FILL_SUMMARY = FILL_DIR / "summary.json"
DEFAULT_FILLED_SHEET = FILL_DIR / "filled_label_sheet.tsv"
DEFAULT_HIDDEN_MANIFEST = READINESS_DIR / "hidden_audit_manifest.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v12_proximity_lh_only_label_ingestion"

SCHEMA_VERSION = "h002_reliability_target_v12_proximity_lh_only_label_ingestion_v1"
EXPECTED_FILL_STATUS = "h002_reliability_target_v12_proximity_lh_only_label_filled_codex_proxy_visible_only"
EXPECTED_NEXT_TODO = "reliability_target_v12_proximity_lh_only_label_ingestion"
NEXT_TODO = "reliability_target_v12_proximity_lh_only_target_independence_audit"

LABEL_SOURCE = "codex_proxy_v12_visible_only_user_requested"
MULTICLASS_TARGET = "proximity_lh_relation_reliability_v12_multiclass"
BINARY_TARGET = "proximity_lh_relation_reliability_v12_binary"

COMPLETION_FIELDS = [
    "reviewer_id_v12",
    "review_round_v12",
    "label_policy_v12",
    "relation_reliability_state_v12",
    "primary_reason_v12",
    "uncertainty_reason_v12",
    "review_notes_v12",
]

VISIBLE_IDENTITY_FIELDS = [
    "blind_review_id",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
]

HIDDEN_AUDIT_FIELDS = [
    "prediction_id",
    "split",
    "source_id",
    "scan_id",
    "subgraph_id",
    "subject_id",
    "object_id",
    "predicate_family",
    "source_queue_hidden",
    "semantic_rank_hidden",
    "semantic_score_norm_hidden",
    "p_geom_valid_hidden",
    "geometry_status_hidden",
    "label_match_status_hidden",
    "label_geometry_bucket_hidden",
    "machine_hint_hidden",
    "rank_band_hidden",
    "subject_object_label_pair_hidden",
    "endpoint_cell_hidden",
    "exact_endpoint_pair_key_hidden",
    "structural_pair_hidden",
    "hard_room_surface_pair_hidden",
    "generic_endpoint_pair_hidden",
]

RISK_PREDICTORS = [
    "label_match_status_hidden",
    "machine_hint_hidden",
    "rank_band_hidden",
    "subject_object_label_pair_hidden",
    "scan_id",
    "subject_label",
    "object_label",
    "subject_object_visible_pair",
]

RISK_THRESHOLDS = {
    "majority_rule_accuracy": 0.85,
    "majority_excess_over_baseline": 0.10,
    "normalized_mutual_information": 0.20,
    "large_group_rows": 10,
    "large_group_purity": 0.90,
}

ALLOWED_STATES = {
    "accept_reliable_close_by",
    "reject_unreliable_close_by",
    "abstain_uncertain",
}

BINARY_MAP = {
    "accept_reliable_close_by": 1,
    "reject_unreliable_close_by": 0,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fill-summary", type=Path, default=DEFAULT_FILL_SUMMARY)
    parser.add_argument("--filled-sheet", type=Path, default=DEFAULT_FILLED_SHEET)
    parser.add_argument("--hidden-manifest", type=Path, default=DEFAULT_HIDDEN_MANIFEST)
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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_fill_summary(fill_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if fill_summary.get("status") != EXPECTED_FILL_STATUS:
        errors.append({"error_type": "unexpected_fill_status", "expected": EXPECTED_FILL_STATUS, "actual": fill_summary.get("status")})
    if fill_summary.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append({"error_type": "unexpected_fill_next_todo", "expected": EXPECTED_NEXT_TODO, "actual": fill_summary.get("next_todo")})
    if fill_summary.get("validation_errors") != 0:
        errors.append({"error_type": "fill_validation_errors_present", "actual": fill_summary.get("validation_errors")})
    boundary = fill_summary.get("boundary", {})
    expected_false = [
        "validation_usage",
        "test_usage",
        "hidden_audit_manifest_read",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "rga_redefined_as_lh_only",
        "multi_view_as_model_input",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "fill_boundary_violation", "key": key, "actual": boundary.get(key)})
    if boundary.get("visible_only_label_fill") is not True:
        errors.append({"error_type": "fill_boundary_violation", "key": "visible_only_label_fill", "actual": boundary.get("visible_only_label_fill")})
    if boundary.get("fills_new_labels") is not True:
        errors.append({"error_type": "fill_boundary_violation", "key": "fills_new_labels", "actual": boundary.get("fills_new_labels")})
    return errors


def validate_id_sets(label_rows: list[dict[str, str]], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    label_ids = [str(row.get("blind_review_id") or "") for row in label_rows]
    manifest_ids = [str(row.get("blind_review_id") or "") for row in manifest_rows]
    for blind_id, count in Counter(label_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_filled_blind_review_id", "blind_review_id": blind_id, "count": count})
    for blind_id, count in Counter(manifest_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_manifest_blind_review_id", "blind_review_id": blind_id, "count": count})
    label_set = {blind_id for blind_id in label_ids if blind_id}
    manifest_set = {blind_id for blind_id in manifest_ids if blind_id}
    for blind_id in sorted(label_set - manifest_set):
        errors.append({"error_type": "filled_id_missing_from_manifest", "blind_review_id": blind_id})
    for blind_id in sorted(manifest_set - label_set):
        errors.append({"error_type": "manifest_id_missing_from_filled_sheet", "blind_review_id": blind_id})
    return errors


def validate_label_rows(fieldnames: list[str], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    required = [*VISIBLE_IDENTITY_FIELDS, *COMPLETION_FIELDS]
    for field in required:
        if field not in fieldnames:
            errors.append({"error_type": "missing_filled_sheet_field", "field": field})
    for row_number, row in enumerate(rows, start=2):
        blind_id = row.get("blind_review_id", "")
        state = row.get("relation_reliability_state_v12", "")
        if state not in ALLOWED_STATES:
            errors.append({"error_type": "invalid_reliability_state", "row_number": row_number, "blind_review_id": blind_id, "state": state})
        for field in COMPLETION_FIELDS:
            if not str(row.get(field, "")).strip() and field not in {"uncertainty_reason_v12"}:
                errors.append({"error_type": "missing_completion_field", "row_number": row_number, "blind_review_id": blind_id, "field": field})
        if row.get("predicate_label") != "close by":
            errors.append({"error_type": "unexpected_predicate", "row_number": row_number, "blind_review_id": blind_id, "predicate": row.get("predicate_label")})
    return errors


def joined_rows(label_rows: list[dict[str, str]], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manifest_by_id = {str(row["blind_review_id"]): row for row in manifest_rows}
    rows: list[dict[str, Any]] = []
    for label_row in label_rows:
        blind_id = str(label_row["blind_review_id"])
        manifest = manifest_by_id[blind_id]
        subject_label = label_row.get("subject_label", "")
        object_label = label_row.get("object_label", "")
        state = label_row["relation_reliability_state_v12"]
        binary = BINARY_MAP.get(state)
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "label_source": LABEL_SOURCE,
                "blind_review_id": blind_id,
                "prediction_id": manifest.get("prediction_id"),
                "split": "train",
                "source_id": manifest.get("source_id"),
                "scan_id": manifest.get("scan_id"),
                "subgraph_id": manifest.get("subgraph_id"),
                "subject_id": manifest.get("subject_id"),
                "subject_label": subject_label,
                "predicate_label": label_row.get("predicate_label"),
                "predicate_family": manifest.get("predicate_family"),
                "object_id": manifest.get("object_id"),
                "object_label": object_label,
                "subject_object_visible_pair": f"{subject_label.strip().lower()}|{object_label.strip().lower()}",
                "reviewer_id_v12": label_row.get("reviewer_id_v12"),
                "review_round_v12": label_row.get("review_round_v12"),
                "label_policy_v12": label_row.get("label_policy_v12"),
                "relation_reliability_state_v12": state,
                "relation_reliability_multiclass_target": state,
                "relation_reliability_binary_target": binary,
                "binary_usable": binary is not None,
                "primary_reason_v12": label_row.get("primary_reason_v12"),
                "uncertainty_reason_v12": label_row.get("uncertainty_reason_v12"),
                "review_notes_v12": label_row.get("review_notes_v12"),
                **{field: manifest.get(field) for field in HIDDEN_AUDIT_FIELDS},
            }
        )
    return rows


def entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    value = 0.0
    for count in counter.values():
        if count:
            p = count / total
            value -= p * math.log(p, 2)
    return value


def normalized_mutual_information(rows: list[dict[str, Any]], predictor: str, label: str) -> float:
    if not rows:
        return 0.0
    label_counts = Counter(str(row.get(label, "missing")) for row in rows)
    group_counts = Counter(str(row.get(predictor, "missing")) for row in rows)
    joint = Counter((str(row.get(predictor, "missing")), str(row.get(label, "missing"))) for row in rows)
    total = len(rows)
    mi = 0.0
    for (group, target), count in joint.items():
        pxy = count / total
        px = group_counts[group] / total
        py = label_counts[target] / total
        if pxy and px and py:
            mi += pxy * math.log(pxy / (px * py), 2)
    h_label = entropy(label_counts)
    h_group = entropy(group_counts)
    denom = math.sqrt(h_label * h_group)
    return mi / denom if denom else 0.0


def majority_risk(rows: list[dict[str, Any]], predictor: str, label: str) -> dict[str, Any]:
    if not rows:
        return {
            "predictor": predictor,
            "label": label,
            "rows": 0,
            "majority_rule_accuracy": None,
            "majority_baseline_accuracy": None,
            "majority_excess_over_baseline": None,
            "normalized_mutual_information": None,
            "risk_flag": False,
            "label_counts": {},
            "groups": 0,
            "top_groups": [],
        }
    label_counts = Counter(str(row.get(label, "missing")) for row in rows)
    baseline = max(label_counts.values()) / len(rows)
    groups: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        groups[str(row.get(predictor, "missing"))][str(row.get(label, "missing"))] += 1
    correct = sum(max(counter.values()) for counter in groups.values())
    acc = correct / len(rows)
    nmi = normalized_mutual_information(rows, predictor, label)
    top_groups = []
    large_pure_group = False
    for group_value, counter in groups.items():
        total = sum(counter.values())
        majority_label, majority_count = counter.most_common(1)[0]
        majority_rate = majority_count / total
        if total >= RISK_THRESHOLDS["large_group_rows"] and majority_rate >= RISK_THRESHOLDS["large_group_purity"]:
            large_pure_group = True
        top_groups.append(
            {
                "group_value": group_value,
                "rows": total,
                "majority_label": majority_label,
                "majority_rate": majority_rate,
                "label_counts": dict(counter),
            }
        )
    top_groups.sort(key=lambda item: (-item["rows"], str(item["group_value"])))
    risk_flag = (
        acc >= RISK_THRESHOLDS["majority_rule_accuracy"]
        and acc - baseline >= RISK_THRESHOLDS["majority_excess_over_baseline"]
    ) or nmi >= RISK_THRESHOLDS["normalized_mutual_information"] or large_pure_group
    return {
        "predictor": predictor,
        "label": label,
        "rows": len(rows),
        "groups": len(groups),
        "label_counts": dict(label_counts),
        "majority_rule_accuracy": acc,
        "majority_baseline_accuracy": baseline,
        "majority_excess_over_baseline": acc - baseline,
        "normalized_mutual_information": nmi,
        "risk_flag": risk_flag,
        "top_groups": top_groups[:12],
    }


def target_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    multiclass_rows = [
        {
            "blind_review_id": row["blind_review_id"],
            "prediction_id": row["prediction_id"],
            "split": row["split"],
            "target_name": MULTICLASS_TARGET,
            "target_value": row["relation_reliability_multiclass_target"],
            "label_source": LABEL_SOURCE,
            "predicate_family": row["predicate_family"],
            "predicate_label": row["predicate_label"],
        }
        for row in rows
    ]
    binary_rows = [
        {
            "blind_review_id": row["blind_review_id"],
            "prediction_id": row["prediction_id"],
            "split": row["split"],
            "target_name": BINARY_TARGET,
            "target_value": row["relation_reliability_binary_target"],
            "label_source": LABEL_SOURCE,
            "predicate_family": row["predicate_family"],
            "predicate_label": row["predicate_label"],
        }
        for row in rows
        if row["binary_usable"]
    ]
    abstain_rows = [
        {
            "blind_review_id": row["blind_review_id"],
            "prediction_id": row["prediction_id"],
            "split": row["split"],
            "target_name": BINARY_TARGET,
            "target_value": None,
            "abstain_reason": row["uncertainty_reason_v12"] or row["primary_reason_v12"],
            "label_source": LABEL_SOURCE,
            "predicate_family": row["predicate_family"],
            "predicate_label": row["predicate_label"],
        }
        for row in rows
        if not row["binary_usable"]
    ]
    return multiclass_rows, binary_rows, abstain_rows


def probe_risks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    binary_rows = [row for row in rows if row["binary_usable"]]
    risks: list[dict[str, Any]] = []
    for predictor in RISK_PREDICTORS:
        risks.append(majority_risk(rows, predictor, "relation_reliability_multiclass_target"))
        risks.append(majority_risk(binary_rows, predictor, "relation_reliability_binary_target"))
    return risks


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 V12 Proximity LH-Only Label Ingestion",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Result",
        "",
        "Ingested the filled visible labels and joined hidden audit metadata by `blind_review_id`.",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"multiclass_rows = {counts['multiclass_rows']}",
        f"binary_rows = {counts['binary_rows']}",
        f"abstain_rows = {counts['abstain_rows']}",
        f"relation_reliability_state_v12 = {counts['relation_reliability_state_v12']}",
        f"binary_target = {counts['binary_target']}",
        f"quick_probe_risk_flags = {counts['quick_probe_risk_flags']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Interpretation",
        "",
        "The target is ingested, but quick probes already show shortcut risk. This is expected because the proxy labels were filled from visible object-pair text. Posterior smoke remains blocked.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    fill_summary_path = as_abs(args.fill_summary)
    filled_sheet_path = as_abs(args.filled_sheet)
    hidden_manifest_path = as_abs(args.hidden_manifest)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fill_summary = read_json(fill_summary_path)
    fieldnames, label_rows = read_tsv(filled_sheet_path)
    manifest_rows = read_jsonl(hidden_manifest_path)

    validation_errors = validate_fill_summary(fill_summary)
    validation_errors.extend(validate_label_rows(fieldnames, label_rows))
    validation_errors.extend(validate_id_sets(label_rows, manifest_rows))

    rows = joined_rows(label_rows, manifest_rows) if not validation_errors else []
    multiclass_rows, binary_rows, abstain_rows = target_rows(rows)
    risks = probe_risks(rows)
    risk_flags = [risk for risk in risks if risk.get("risk_flag")]

    state_counts = Counter(row["relation_reliability_state_v12"] for row in rows)
    binary_counts = Counter(str(row["relation_reliability_binary_target"]) for row in rows if row["binary_usable"])
    reason_counts = Counter(row["primary_reason_v12"] for row in rows)
    label_match_counts = Counter(str(row.get("label_match_status_hidden")) for row in rows)
    machine_hint_counts = Counter(str(row.get("machine_hint_hidden")) for row in rows)
    rank_band_counts = Counter(str(row.get("rank_band_hidden")) for row in rows)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "ingested_rows": output_dir / "ingested_rows.jsonl",
        "multiclass_target": output_dir / "multiclass_target.jsonl",
        "binary_target": output_dir / "binary_target.jsonl",
        "abstain_rows": output_dir / "abstain_rows.jsonl",
        "quick_probe_risks": output_dir / "quick_probe_risks.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    status = (
        "h002_reliability_target_v12_proximity_lh_only_label_ingested_with_probe_risk"
        if not validation_errors and risk_flags
        else "h002_reliability_target_v12_proximity_lh_only_label_ingested_no_probe_risk"
        if not validation_errors
        else "h002_reliability_target_v12_proximity_lh_only_label_ingestion_errors"
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "fill_summary": rel_path(fill_summary_path),
            "filled_sheet": rel_path(filled_sheet_path),
            "hidden_manifest": rel_path(hidden_manifest_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "counts": {
            "rows": len(rows),
            "multiclass_rows": len(multiclass_rows),
            "binary_rows": len(binary_rows),
            "abstain_rows": len(abstain_rows),
            "relation_reliability_state_v12": dict(state_counts),
            "binary_target": dict(binary_counts),
            "primary_reason_v12": dict(reason_counts),
            "label_match_status_hidden": dict(label_match_counts),
            "machine_hint_hidden": dict(machine_hint_counts),
            "rank_band_hidden": dict(rank_band_counts),
            "quick_probe_risk_flags": len(risk_flags),
        },
        "quick_probe": {
            "risk_thresholds": RISK_THRESHOLDS,
            "risk_flags": [
                {
                    "predictor": risk["predictor"],
                    "label": risk["label"],
                    "rows": risk["rows"],
                    "majority_rule_accuracy": risk["majority_rule_accuracy"],
                    "majority_baseline_accuracy": risk["majority_baseline_accuracy"],
                    "normalized_mutual_information": risk["normalized_mutual_information"],
                }
                for risk in risk_flags
            ],
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": True,
            "reads_hidden_audit_manifest_for_audit": True,
            "hidden_fields_as_model_input": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
        },
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO,
    }

    write_jsonl(output_paths["ingested_rows"], rows)
    write_jsonl(output_paths["multiclass_target"], multiclass_rows)
    write_jsonl(output_paths["binary_target"], binary_rows)
    write_jsonl(output_paths["abstain_rows"], abstain_rows)
    write_json(output_paths["quick_probe_risks"], risks)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"rows={summary['counts']['rows']}")
    print(f"binary_rows={summary['counts']['binary_rows']}")
    print(f"abstain_rows={summary['counts']['abstain_rows']}")
    print(f"quick_probe_risk_flags={summary['counts']['quick_probe_risk_flags']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
