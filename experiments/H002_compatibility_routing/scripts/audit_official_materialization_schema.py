#!/usr/bin/env python3
"""Audit official H002 materialization for schema leakage and shortcut risk."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h002_official_materialization_schema_audit_v1"
EXPECTED_INPUT_SCHEMA = "h002_official_candidate_materialization_v1"
EXPECTED_INPUT_STATUS = "h002_official_candidate_materialization_ready"
EXPECTED_FAMILIES = {"relative_horizontal", "relative_vertical", "size_relative", "support_contact"}
MAIN_ALLOWED_BLOCKS = ["T_e", "G_e"]
DIAGNOSTIC_ONLY_BLOCKS = ["Q_e", "Z_e"]

BLOCKED_PATH_TOKENS = {
    "candidate_bucket",
    "candidate_origin",
    "construction_bucket",
    "counterfactual",
    "distance_bucket",
    "exact_match",
    "geometry_status",
    "gt_exact",
    "h001",
    "label_match",
    "old_proxy",
    "p_geom_valid",
    "rank_band",
    "ranking_score",
    "semantic_rank",
    "source_id",
    "source_score",
    "target_generation",
    "verification_status",
}

SHORTCUT_PROBES = [
    ("route_family_only", "metadata_only"),
    ("predicate_only", "C_e_T"),
    ("subject_class_only", "C_e_T"),
    ("object_class_only", "C_e_T"),
    ("class_pair", "C_e_T"),
    ("predicate_x_class_pair", "C_e_T"),
    ("scan_id", "metadata_only"),
    ("subject_id", "metadata_only"),
    ("object_id", "metadata_only"),
    ("directed_pair", "metadata_only"),
    ("cv_or_group_key", "metadata_only"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--materialization-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def repo_rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def flatten_paths(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from flatten_paths(child, child_prefix)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from flatten_paths(child, f"{prefix}[{index}]")
    else:
        yield prefix, value


def block(row: dict[str, Any], name: str) -> dict[str, Any]:
    blocks = row.get("feature_blocks", {})
    value = blocks.get(name, {}) if isinstance(blocks, dict) else {}
    return value if isinstance(value, dict) else {}


def text(value: Any) -> str:
    if value is None:
        return "__MISSING__"
    return str(value)


def probe_value(row: dict[str, Any], probe: str) -> str:
    t = block(row, "T_e")
    if probe == "route_family_only":
        return text(row.get("route_family"))
    if probe == "predicate_only":
        return text(t.get("predicate_label") or row.get("predicate_label"))
    if probe == "subject_class_only":
        return text(t.get("subject_class_label"))
    if probe == "object_class_only":
        return text(t.get("object_class_label"))
    if probe == "class_pair":
        return f"{text(t.get('subject_class_label'))}::{text(t.get('object_class_label'))}"
    if probe == "predicate_x_class_pair":
        return f"{probe_value(row, 'predicate_only')}::{probe_value(row, 'class_pair')}"
    if probe == "scan_id":
        return text(row.get("scan_id"))
    if probe == "subject_id":
        return text(row.get("subject_id"))
    if probe == "object_id":
        return text(row.get("object_id"))
    if probe == "directed_pair":
        return f"{text(row.get('scan_id'))}::{text(row.get('subject_id'))}->{text(row.get('object_id'))}"
    if probe == "cv_or_group_key":
        return text(row.get("cv_or_group_key"))
    raise KeyError(probe)


def majority_probe(rows: list[dict[str, Any]], probe: str, scope: str, family: str | None = None) -> dict[str, Any]:
    selected = [row for row in rows if family is None or row.get("route_family") == family]
    buckets: dict[str, Counter[int]] = defaultdict(Counter)
    for row in selected:
        buckets[probe_value(row, probe)][int(row["target_y"])] += 1
    correct = sum(max(counts.values()) for counts in buckets.values())
    total = len(selected)
    accuracy = correct / total if total else 0.0
    pure = sum(1 for counts in buckets.values() if len(counts) == 1)
    max_bucket = max((sum(counts.values()) for counts in buckets.values()), default=0)
    high_risk = total >= 100 and accuracy >= 0.95
    return {
        "family": family or "ALL",
        "probe": probe,
        "scope": scope,
        "rows": total,
        "unique_values": len(buckets),
        "max_bucket_rows": max_bucket,
        "pure_value_count": pure,
        "majority_accuracy": round(accuracy, 6),
        "risk": "high" if high_risk else "medium" if total >= 100 and accuracy >= 0.80 else "low",
        "blocks_metric_freeze": False,
        "blocks_family_main_claim": bool(high_risk and scope == "C_e_T"),
    }


def audit_schema(rows: list[dict[str, Any]], hidden_rows: list[dict[str, Any]], manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    schema_violations: list[dict[str, Any]] = []
    blocked_hits: list[dict[str, Any]] = []
    separation_rows: list[dict[str, Any]] = []

    hidden_ids = {row.get("candidate_id") for row in hidden_rows}
    seen_ids: set[str] = set()
    for index, row in enumerate(rows, start=1):
        candidate_id = row.get("candidate_id")
        if candidate_id in seen_ids:
            schema_violations.append({"line": index, "error_type": "duplicate_candidate_id", "candidate_id": candidate_id})
        seen_ids.add(candidate_id)
        if candidate_id not in hidden_ids:
            schema_violations.append({"line": index, "error_type": "missing_hidden_manifest_row", "candidate_id": candidate_id})
        if row.get("schema_version") != EXPECTED_INPUT_SCHEMA:
            schema_violations.append({"line": index, "error_type": "unexpected_schema_version", "candidate_id": candidate_id, "actual": row.get("schema_version")})
        policy = row.get("feature_use_policy", {})
        if policy.get("main_C_e_allowed_blocks") != MAIN_ALLOWED_BLOCKS:
            schema_violations.append({"line": index, "error_type": "invalid_main_C_e_allowed_blocks", "candidate_id": candidate_id, "actual": policy.get("main_C_e_allowed_blocks")})
        for required in ["T_e", "G_e", "Q_e", "Z_e", "extra_safe_blocks"]:
            if required not in row.get("feature_blocks", {}):
                schema_violations.append({"line": index, "error_type": "missing_feature_block", "candidate_id": candidate_id, "block": required})
        for blocked_top in ["candidate_origin", "compatibility_label", "compatibility_label_source"]:
            if blocked_top in row:
                schema_violations.append({"line": index, "error_type": "construction_or_label_string_in_model_safe", "candidate_id": candidate_id, "field": blocked_top})
        for allowed in MAIN_ALLOWED_BLOCKS:
            for path, value in flatten_paths(block(row, allowed), f"feature_blocks.{allowed}"):
                lower = path.lower()
                matched = sorted(token for token in BLOCKED_PATH_TOKENS if token in lower)
                if matched:
                    blocked_hits.append(
                        {
                            "line": index,
                            "candidate_id": candidate_id,
                            "route_family": row.get("route_family"),
                            "predicate_label": row.get("predicate_label"),
                            "path": path,
                            "matched_tokens": "|".join(matched),
                            "value_preview": text(value)[:120],
                        }
                    )

    separation_rows.append(
        {
            "check": "model_safe_hidden_candidate_id_alignment",
            "model_safe_rows": len(rows),
            "hidden_rows": len(hidden_rows),
            "shared_ids": len(seen_ids & hidden_ids),
            "model_safe_missing_hidden": len(seen_ids - hidden_ids),
            "hidden_missing_model_safe": len(hidden_ids - seen_ids),
        }
    )
    if manifest.get("status") != EXPECTED_INPUT_STATUS:
        schema_violations.append({"error_type": "unexpected_materialization_status", "actual": manifest.get("status")})
    if manifest.get("validation_errors") != 0:
        schema_violations.append({"error_type": "materialization_validation_errors", "actual": manifest.get("validation_errors")})
    for key in ["official_validation_metric_produced", "official_test_usage", "paper_metric_produced", "p_rel_claim_enabled", "p_obs_claim_enabled"]:
        if manifest.get(key) is not False:
            schema_violations.append({"error_type": "unexpected_metric_boundary", "key": key, "actual": manifest.get(key)})
    return schema_violations, blocked_hits, separation_rows


def label_balance(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    families = sorted({str(row.get("route_family")) for row in rows})
    out: list[dict[str, Any]] = []
    total_all = len(rows)
    for family in ["ALL", *families]:
        selected = rows if family == "ALL" else [row for row in rows if row.get("route_family") == family]
        labels = Counter(int(row["target_y"]) for row in selected)
        total = len(selected)
        majority = max(labels.values()) if labels else 0
        out.append(
            {
                "family": family,
                "rows": total,
                "label_0": labels[0],
                "label_1": labels[1],
                "positive_rate": round(labels[1] / total, 6) if total else 0.0,
                "majority_rate": round(majority / total, 6) if total else 0.0,
                "dataset_weight": round(total / total_all, 6) if total_all else 0.0,
                "paper_metric_requirement": "family_wise_and_macro_required" if family == "ALL" else "report_per_family",
                "imbalance_risk": "high" if total >= 100 and majority / max(total, 1) >= 0.70 else "low",
            }
        )
    return out


def shortcut_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    families = sorted({str(row.get("route_family")) for row in rows})
    out: list[dict[str, Any]] = []
    for probe, scope in SHORTCUT_PROBES:
        out.append(majority_probe(rows, probe, scope, None))
        for family in families:
            out.append(majority_probe(rows, probe, scope, family))
    return out


def control_readiness(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    families = sorted({str(row.get("route_family")) for row in rows})
    rows_by_family = {family: [row for row in rows if row.get("route_family") == family] for family in families}
    out: list[dict[str, Any]] = []
    for family, family_rows in rows_by_family.items():
        predicates = sorted({row.get("predicate_label") for row in family_rows})
        feature_names = set()
        for row in family_rows[: min(100, len(family_rows))]:
            names = block(row, "G_e").get("g_e_feature_names", [])
            if isinstance(names, list):
                feature_names.update(str(name) for name in names)
        checks = [
            ("wrong_predicate_within_route", len(predicates) >= 2),
            ("wrong_predicate_across_route", len(families) >= 2),
            ("shuffled_geometry_global", len(rows) > 1),
            ("shuffled_geometry_within_family", len(family_rows) > 1),
            ("subject_object_swap", True),
            ("sign_flip_where_applicable", any(name in feature_names for name in ["center_delta_z", "normalized_center_delta_z", "center_delta_x", "center_delta_y", "log_volume_ratio_s_over_o"])),
            ("horizontal_frame_swap", family == "relative_horizontal" and {"center_delta_x", "center_delta_y"} <= feature_names),
        ]
        for check, ready in checks:
            out.append(
                {
                    "family": family,
                    "control": check,
                    "ready": bool(ready),
                    "predicate_count": len(predicates),
                    "sampled_g_e_features": "; ".join(sorted(feature_names)),
                    "blocks_metric_freeze": not bool(ready) and check in {"wrong_predicate_within_route", "shuffled_geometry_within_family"},
                }
            )
    return out


def write_report(path: Path, manifest: dict[str, Any], summary: dict[str, Any], balance: list[dict[str, Any]], shortcuts: list[dict[str, Any]], controls: list[dict[str, Any]]) -> None:
    high_shortcuts = [row for row in shortcuts if row["risk"] == "high"]
    blocking_controls = [row for row in controls if row["blocks_metric_freeze"]]
    lines = [
        "# H002 Official Materialization Schema Audit",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"shortcut_warnings = {summary['shortcut_warnings']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Runtime Boundary",
        "",
        f"- materialized rows: `{manifest['row_counts']['model_safe_view']}`",
        "- official validation metric: `false`",
        "- paper metric: `false`",
        "- official test usage: `false`",
        "",
        "## Label Balance",
        "",
        "| Family | Rows | Label 0 | Label 1 | Majority | Dataset Weight |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in balance:
        lines.append(
            f"| `{row['family']}` | {row['rows']} | {row['label_0']} | {row['label_1']} | "
            f"{row['majority_rate']:.6f} | {row['dataset_weight']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Shortcut Summary",
            "",
            f"- high shortcut rows: `{len(high_shortcuts)}`",
            f"- blocking controls: `{len(blocking_controls)}`",
            "- metric protocol must report family-wise, macro-average, weighted-average, and route controls.",
            "",
            "## Boundary",
            "",
            "- This stage audits inputs only; no AUROC/F1 metric was computed.",
            "- `Z_e` remains excluded from the main `C_e` compatibility metric.",
            "- `support_contact` remains a challenging route, not a solved claim.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    materialization_dir = args.materialization_dir
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    manifest = read_json(materialization_dir / "row_manifest.json")
    model_rows = list(iter_jsonl(materialization_dir / "model_safe_view.jsonl"))
    hidden_rows = list(iter_jsonl(materialization_dir / "hidden_manifest.jsonl"))
    schema_violations, blocked_hits, separation_rows = audit_schema(model_rows, hidden_rows, manifest)
    balance_rows = label_balance(model_rows)
    shortcut_rows = shortcut_table(model_rows)
    control_rows = control_readiness(model_rows)
    high_shortcut_rows = [row for row in shortcut_rows if row["risk"] == "high"]
    control_blockers = [row for row in control_rows if row["blocks_metric_freeze"]]

    validation_errors: list[dict[str, Any]] = []
    validation_errors.extend(schema_violations)
    validation_errors.extend({"error_type": "blocked_field_hit", **row} for row in blocked_hits)
    validation_errors.extend({"error_type": "control_not_ready", **row} for row in control_blockers)

    status = "h002_official_materialization_schema_audit_ready_with_shortcut_warnings"
    selected_path = "schema_audit_ready_select_metric_protocol_freeze_with_caveats"
    next_todo = "compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit"
    if validation_errors:
        status = "h002_official_materialization_schema_audit_blocked"
        selected_path = "blocked_fix_schema_or_control_readiness"
        next_todo = "fix_official_materialization_schema_audit_blockers"

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": selected_path,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "shortcut_warnings": len(high_shortcut_rows),
        "input_artifacts": {
            "row_manifest": repo_rel(args.repo_root, materialization_dir / "row_manifest.json"),
            "model_safe_view": repo_rel(args.repo_root, materialization_dir / "model_safe_view.jsonl"),
            "hidden_manifest": repo_rel(args.repo_root, materialization_dir / "hidden_manifest.jsonl"),
        },
        "output_artifacts": {
            "schema_violations": repo_rel(args.repo_root, out / "schema_violations.jsonl"),
            "blocked_field_hits": repo_rel(args.repo_root, out / "blocked_field_hits.jsonl"),
            "separation_audit": repo_rel(args.repo_root, out / "separation_audit.csv"),
            "label_balance": repo_rel(args.repo_root, out / "label_balance.csv"),
            "shortcut_risk_table": repo_rel(args.repo_root, out / "shortcut_risk_table.csv"),
            "high_shortcut_warnings": repo_rel(args.repo_root, out / "high_shortcut_warnings.csv"),
            "control_readiness": repo_rel(args.repo_root, out / "control_readiness.csv"),
            "report": repo_rel(args.repo_root, out / "report.md"),
        },
        "boundary": {
            "official_validation_metric_produced": False,
            "official_test_usage": False,
            "paper_metric_produced": False,
            "p_rel_claim_enabled": False,
            "p_obs_claim_enabled": False,
            "z_e_excluded_from_main_c_e": True,
            "family_macro_metric_required_next": True,
            "support_contact_claim": "challenging_not_solved",
        },
    }

    write_json(out / "audit_manifest.json", summary)
    write_jsonl(out / "validation_errors.jsonl", validation_errors)
    write_jsonl(out / "schema_violations.jsonl", schema_violations)
    write_jsonl(out / "blocked_field_hits.jsonl", blocked_hits)
    write_csv(out / "separation_audit.csv", separation_rows)
    write_csv(out / "label_balance.csv", balance_rows)
    write_csv(out / "shortcut_risk_table.csv", shortcut_rows)
    write_csv(out / "high_shortcut_warnings.csv", high_shortcut_rows)
    write_csv(out / "control_readiness.csv", control_rows)
    write_report(out / "report.md", manifest, summary, balance_rows, shortcut_rows, control_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
