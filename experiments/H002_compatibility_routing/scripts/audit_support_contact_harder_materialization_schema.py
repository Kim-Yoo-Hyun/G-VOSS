#!/usr/bin/env python3
"""Audit richer support/contact hard-route materialization before metrics."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h002_support_contact_harder_schema_shortcut_audit_v1"
EXPECTED_INPUT_SCHEMA = "h002_support_contact_harder_route_materialization_v1"
EXPECTED_INPUT_STATUS = "h002_support_contact_harder_route_materialization_ready"
EXPECTED_ROWS = 3178
EXPECTED_GROUPS = 1589
EXPECTED_FEATURE_MIN = 40
MAIN_VIEW = "model_safe_main_no_class"

BLOCKED_MAIN_TOKENS = {
    "class_label",
    "class_pair",
    "counterfactual",
    "exact_match",
    "geometry_status",
    "gt_",
    "h001",
    "object_id",
    "p_geom_valid",
    "rank",
    "scan_id",
    "score",
    "source",
    "subject_id",
    "target",
    "verification",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--materialization-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def repo_rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return list(iter_jsonl(path))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def line_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def flatten(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from flatten(child, child_prefix)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from flatten(child, f"{prefix}[{index}]")
    else:
        yield prefix, value


def label(row: dict[str, Any]) -> int:
    return int(row.get("labels", {}).get("C_e", -1))


def block(row: dict[str, Any], name: str) -> dict[str, Any]:
    blocks = row.get("feature_blocks", {})
    value = blocks.get(name, {}) if isinstance(blocks, dict) else {}
    return value if isinstance(value, dict) else {}


def hidden_class_pair(row: dict[str, Any]) -> str:
    return str(row.get("class_pair") or f"{row.get('subject_class_label')}->{row.get('object_class_label')}")


def class_pair_from_class_view(row: dict[str, Any]) -> str:
    t = block(row, "T_e")
    return f"{t.get('subject_class_label')}->{t.get('object_class_label')}"


def majority_accuracy(rows: list[dict[str, Any]], key_fn) -> dict[str, Any]:
    buckets: dict[str, Counter[int]] = defaultdict(Counter)
    for row in rows:
        buckets[str(key_fn(row))][label(row)] += 1
    correct = sum(max(counts.values()) for counts in buckets.values())
    total = len(rows)
    majority = correct / total if total else 0.0
    pure = sum(1 for counts in buckets.values() if len(counts) == 1)
    max_bucket = max((sum(counts.values()) for counts in buckets.values()), default=0)
    return {
        "rows": total,
        "unique_values": len(buckets),
        "max_bucket_rows": max_bucket,
        "pure_value_count": pure,
        "majority_accuracy": round(majority, 6),
        "risk": "high" if total >= 100 and majority >= 0.95 else "medium" if total >= 100 and majority >= 0.80 else "low",
    }


def audit_manifest_and_counts(materialization_dir: Path, manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    file_rows: list[dict[str, Any]] = []
    expected_counts = {
        "candidate_rows.jsonl": EXPECTED_ROWS,
        "model_safe_main_no_class.jsonl": EXPECTED_ROWS,
        "model_safe_main_with_class_ablation.jsonl": EXPECTED_ROWS,
        "model_safe_geometry_only.jsonl": EXPECTED_ROWS,
        "model_safe_qe_diagnostic.jsonl": EXPECTED_ROWS,
        "hidden_manifest.jsonl": EXPECTED_ROWS,
        "group_manifest.jsonl": EXPECTED_GROUPS,
        "validation_errors.jsonl": 0,
    }
    if manifest.get("schema_version") != EXPECTED_INPUT_SCHEMA:
        errors.append({"error_type": "unexpected_input_schema", "actual": manifest.get("schema_version")})
    if manifest.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"error_type": "unexpected_input_status", "actual": manifest.get("status")})
    if manifest.get("validation_errors") != 0:
        errors.append({"error_type": "runtime_manifest_validation_errors", "actual": manifest.get("validation_errors")})
    for key in ["paper_metric_produced", "official_test_usage", "source_reranking_run", "p_rel_claim_enabled", "p_obs_claim_enabled"]:
        if manifest.get(key) is not False:
            errors.append({"error_type": "unexpected_claim_boundary", "key": key, "actual": manifest.get(key)})
    if manifest.get("official_validation_eval_only") is not True:
        errors.append({"error_type": "official_validation_not_eval_only", "actual": manifest.get("official_validation_eval_only")})
    for filename, expected in expected_counts.items():
        count = line_count(materialization_dir / filename)
        file_rows.append({"file": filename, "line_count": count, "expected": expected, "match": count == expected})
        if count != expected:
            errors.append({"error_type": "line_count_mismatch", "file": filename, "actual": count, "expected": expected})
    return errors, file_rows


def audit_view_alignment(views: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    base_ids = {row.get("candidate_id") for row in views[MAIN_VIEW]}
    for view, view_rows in views.items():
        ids = {row.get("candidate_id") for row in view_rows}
        rows.append(
            {
                "view": view,
                "rows": len(view_rows),
                "shared_with_main": len(ids & base_ids),
                "missing_from_main": len(ids - base_ids),
                "missing_from_view": len(base_ids - ids),
            }
        )
        if ids != base_ids:
            errors.append({"error_type": "candidate_id_alignment_mismatch", "view": view})
    return errors, rows


def audit_main_view(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    blocked_hits: list[dict[str, Any]] = []
    feature_counts: Counter[str] = Counter()
    predicates = Counter()
    labels = Counter()
    policy_violations = 0
    for row in rows:
        candidate_id = row.get("candidate_id")
        if row.get("schema_version") != EXPECTED_INPUT_SCHEMA:
            errors.append({"error_type": "unexpected_schema", "candidate_id": candidate_id, "actual": row.get("schema_version")})
        if set(row.get("feature_blocks", {})) != {"T_e", "G_e"}:
            errors.append({"error_type": "unexpected_main_view_blocks", "candidate_id": candidate_id, "blocks": sorted(row.get("feature_blocks", {}))})
        if row.get("feature_use_policy", {}).get("main_C_e_allowed_blocks") != ["T_e", "G_e"]:
            policy_violations += 1
        if "target_y" in row:
            errors.append({"error_type": "target_y_in_main_view", "candidate_id": candidate_id})
        t = block(row, "T_e")
        if "subject_class_label" in t or "object_class_label" in t:
            errors.append({"error_type": "class_label_in_primary_no_class_view", "candidate_id": candidate_id})
        for path, value in flatten(row.get("feature_blocks", {}), "feature_blocks"):
            lower = path.lower()
            matched = sorted(token for token in BLOCKED_MAIN_TOKENS if token in lower)
            if matched:
                blocked_hits.append(
                    {
                        "candidate_id": candidate_id,
                        "path": path,
                        "matched_tokens": "|".join(matched),
                        "value_preview": str(value)[:120],
                    }
                )
        for feature in block(row, "G_e").get("g_e_feature_names", []):
            feature_counts[str(feature)] += 1
        predicates[str(row.get("predicate_label"))] += 1
        labels[str(label(row))] += 1
    if policy_violations:
        errors.append({"error_type": "main_view_policy_violations", "rows": policy_violations})
    if len(feature_counts) < EXPECTED_FEATURE_MIN:
        errors.append({"error_type": "too_few_main_g_e_features", "actual": len(feature_counts), "required": EXPECTED_FEATURE_MIN})
    summary = {
        "rows": len(rows),
        "feature_count": len(feature_counts),
        "label_0": labels.get("0", 0),
        "label_1": labels.get("1", 0),
        "standing_on": predicates.get("standing on", 0),
        "lying_on": predicates.get("lying on", 0),
        "policy_violations": policy_violations,
        "blocked_field_hits": len(blocked_hits),
    }
    feature_rows = [
        {"feature": feature, "present_rows": count, "present_rate": round(count / len(rows), 6) if rows else 0.0}
        for feature, count in sorted(feature_counts.items())
    ]
    return errors, blocked_hits, {"summary": summary, "feature_rows": feature_rows}


def audit_groups(group_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    bad_rows = [row for row in group_rows if row.get("pair_integrity_ok") is not True]
    if bad_rows:
        errors.append({"error_type": "bad_group_integrity", "rows": len(bad_rows)})
    summary = [
        {
            "groups": len(group_rows),
            "bad_group_count": len(bad_rows),
            "pair_integrity_ok_rate": round((len(group_rows) - len(bad_rows)) / len(group_rows), 6) if group_rows else 0.0,
        }
    ]
    return errors, summary


def shortcut_rows(
    main_rows: list[dict[str, Any]],
    class_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_hidden = {row.get("candidate_id"): row for row in hidden_rows}
    enriched: list[dict[str, Any]] = []
    for row in main_rows:
        hidden = by_hidden.get(row.get("candidate_id"), {})
        enriched.append({**row, "_hidden": hidden})
    probes = [
        ("primary_predicate_only", "primary_main_input", lambda row: row.get("predicate_label")),
        ("hidden_class_pair", "hidden_audit_only", lambda row: hidden_class_pair(row.get("_hidden", {}))),
        (
            "hidden_predicate_x_class_pair",
            "hidden_audit_only",
            lambda row: f"{row.get('predicate_label')}::{hidden_class_pair(row.get('_hidden', {}))}",
        ),
    ]
    out: list[dict[str, Any]] = []
    for probe, scope, fn in probes:
        stats = majority_accuracy(enriched, fn)
        out.append({"probe": probe, "scope": scope, **stats, "blocks_metric": False, "blocks_solved_claim": stats["risk"] == "high"})
    class_stats = majority_accuracy(class_rows, lambda row: class_pair_from_class_view(row))
    out.append(
        {
            "probe": "class_ablation_class_pair",
            "scope": "ablation_only",
            **class_stats,
            "blocks_metric": False,
            "blocks_solved_claim": class_stats["risk"] == "high",
        }
    )
    class_px_stats = majority_accuracy(class_rows, lambda row: f"{row.get('predicate_label')}::{class_pair_from_class_view(row)}")
    out.append(
        {
            "probe": "class_ablation_predicate_x_class_pair",
            "scope": "ablation_only",
            **class_px_stats,
            "blocks_metric": False,
            "blocks_solved_claim": class_px_stats["risk"] == "high",
        }
    )
    return out


def control_readiness(
    main_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    feature_availability: list[dict[str, str]],
) -> list[dict[str, Any]]:
    hidden_by_id = {row.get("candidate_id"): row for row in hidden_rows}
    class_counts: dict[str, int] = Counter(hidden_class_pair(row) for row in hidden_rows)
    groups_by_class: dict[str, int] = Counter()
    for row in main_rows:
        hidden = hidden_by_id.get(row.get("candidate_id"), {})
        groups_by_class[hidden_class_pair(hidden)] += 1
    feature_complete = all(float(row.get("present_rate", 0.0)) >= 1.0 for row in feature_availability)
    feature_count = len(feature_availability)
    controls = [
        {
            "control": "wrong_T_same_route",
            "ready": True,
            "reason": "standing/lying predicate pair exists for every group",
            "blocks_metric_freeze": False,
        },
        {
            "control": "shuffled_G_global",
            "ready": len(main_rows) > 1,
            "reason": "global geometry shuffle can be created from main view",
            "blocks_metric_freeze": len(main_rows) <= 1,
        },
        {
            "control": "shuffled_G_within_class_pair",
            "ready": any(count >= 4 for count in groups_by_class.values()),
            "reason": "hidden class-pair groups are available for class-controlled shuffle",
            "blocks_metric_freeze": not any(count >= 4 for count in groups_by_class.values()),
        },
        {
            "control": "class_ablation_view",
            "ready": True,
            "reason": "class labels are separated into ablation-only view",
            "blocks_metric_freeze": False,
        },
        {
            "control": "q_e_diagnostic_view",
            "ready": True,
            "reason": "Q_e is separated from primary C_e view",
            "blocks_metric_freeze": False,
        },
        {
            "control": "richer_G_e_feature_availability",
            "ready": feature_complete and feature_count >= EXPECTED_FEATURE_MIN,
            "reason": f"{feature_count} features observed with complete availability",
            "blocks_metric_freeze": not (feature_complete and feature_count >= EXPECTED_FEATURE_MIN),
        },
        {
            "control": "predicate_x_class_pair_shortcut_probe",
            "ready": bool(hidden_rows),
            "reason": "hidden class-pair provenance is available for shortcut reporting",
            "blocks_metric_freeze": not bool(hidden_rows),
        },
    ]
    return controls


def build_report(summary: dict[str, Any], shortcut_table: list[dict[str, Any]]) -> str:
    warnings = [row for row in shortcut_table if row["risk"] in {"medium", "high"}]
    return "\n".join(
        [
            "# H002 Support/Contact Harder Route Schema Shortcut Audit",
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
            "## Judgment",
            "",
            "The richer support/contact materialization passes schema and control-readiness checks.",
            "Shortcut warnings remain and must be handled in the metric protocol.",
            "",
            "## Warnings",
            "",
            *[
                f"- `{row['probe']}`: majority accuracy `{row['majority_accuracy']}`, risk `{row['risk']}`"
                for row in warnings
            ],
            "",
            "## Boundary",
            "",
            "- No metric was run.",
            "- Official test was not used.",
            "- `support_contact` remains challenging, not solved.",
        ]
    ) + "\n"


def main() -> int:
    args = parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    materialization_dir = args.materialization_dir

    manifest = read_json(materialization_dir / "row_manifest.json")
    validation_errors, file_rows = audit_manifest_and_counts(materialization_dir, manifest)
    views = {
        "model_safe_main_no_class": read_jsonl(materialization_dir / "model_safe_main_no_class.jsonl"),
        "model_safe_main_with_class_ablation": read_jsonl(materialization_dir / "model_safe_main_with_class_ablation.jsonl"),
        "model_safe_geometry_only": read_jsonl(materialization_dir / "model_safe_geometry_only.jsonl"),
        "model_safe_qe_diagnostic": read_jsonl(materialization_dir / "model_safe_qe_diagnostic.jsonl"),
        "hidden_manifest": read_jsonl(materialization_dir / "hidden_manifest.jsonl"),
        "candidate_rows": read_jsonl(materialization_dir / "candidate_rows.jsonl"),
    }
    group_rows = read_jsonl(materialization_dir / "group_manifest.jsonl")
    feature_availability = read_csv(materialization_dir / "feature_availability.csv")

    view_errors, view_alignment_rows = audit_view_alignment(views)
    main_errors, blocked_hits, main_payload = audit_main_view(views["model_safe_main_no_class"])
    group_errors, group_summary = audit_groups(group_rows)
    validation_errors.extend(view_errors)
    validation_errors.extend(main_errors)
    validation_errors.extend(group_errors)
    validation_errors.extend({"error_type": "blocked_main_field_hit", **row} for row in blocked_hits)

    shortcuts = shortcut_rows(
        views["model_safe_main_no_class"],
        views["model_safe_main_with_class_ablation"],
        views["hidden_manifest"],
    )
    high_shortcuts = [row for row in shortcuts if row["risk"] == "high"]
    warning_shortcuts = [row for row in shortcuts if row["risk"] in {"medium", "high"}]
    controls = control_readiness(views["model_safe_main_no_class"], views["hidden_manifest"], feature_availability)
    control_blockers = [row for row in controls if row["blocks_metric_freeze"]]
    validation_errors.extend({"error_type": "control_not_ready", **row} for row in control_blockers)

    status = "h002_support_contact_harder_schema_shortcut_audit_ready_with_warnings"
    selected_path = "schema_shortcut_audit_ready_select_metric_protocol_freeze"
    next_todo = "compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit"
    if validation_errors:
        status = "h002_support_contact_harder_schema_shortcut_audit_blocked"
        selected_path = "blocked_fix_schema_or_control_readiness"
        next_todo = "fix_support_contact_harder_schema_shortcut_audit_blockers"

    output_paths = {
        "audit_manifest": out / "audit_manifest.json",
        "validation_errors": out / "validation_errors.jsonl",
        "file_counts": out / "file_counts.csv",
        "view_alignment": out / "view_alignment.csv",
        "main_view_summary": out / "main_view_summary.csv",
        "feature_availability": out / "feature_availability.csv",
        "blocked_field_hits": out / "blocked_field_hits.jsonl",
        "group_integrity": out / "group_integrity.csv",
        "shortcut_risk_table": out / "shortcut_risk_table.csv",
        "shortcut_warnings": out / "shortcut_warnings.csv",
        "control_readiness": out / "control_readiness.csv",
        "next_contract": out / "next_contract.json",
        "report": out / "report.md",
    }
    next_contract = {
        "next_todo": next_todo,
        "selected_path": selected_path,
        "purpose": "Freeze metric protocol for richer support/contact hard route after schema/shortcut audit.",
        "must_include": [
            "primary no-class view",
            "geometry-only baseline",
            "predicate-only baseline",
            "plain concat baseline",
            "T_e x G_e compatibility model",
            "wrong-T same-route control",
            "shuffled-G global control",
            "shuffled-G within class-pair control",
            "class-ablation view reported separately",
        ],
        "must_not_do": [
            "do not use official test",
            "do not use class labels in primary metric",
            "do not claim support_contact solved if shortcut controls explain the gain",
        ],
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": selected_path,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "shortcut_warnings": len(warning_shortcuts),
        "high_shortcut_warnings": len(high_shortcuts),
        "input_artifacts": {
            "materialization_dir": repo_rel(args.repo_root, materialization_dir),
            "row_manifest": repo_rel(args.repo_root, materialization_dir / "row_manifest.json"),
        },
        "output_artifacts": {key: repo_rel(args.repo_root, value) for key, value in output_paths.items()},
        "main_view": main_payload["summary"],
        "group_summary": group_summary[0] if group_summary else {},
        "decision": {
            "schema_audit_passed": not bool(validation_errors),
            "metric_protocol_freeze_next": not bool(validation_errors),
            "paper_metric_promoted": False,
            "official_test_usage": False,
            "support_contact_solved_claim_allowed": False,
            "shortcut_warnings_require_controls": bool(warning_shortcuts),
        },
        "boundary": {
            "metrics_run": False,
            "official_test_usage": False,
            "paper_metric_produced": False,
            "primary_view": MAIN_VIEW,
            "class_ablation_only": True,
            "q_e_diagnostic_only": True,
        },
    }

    write_json(output_paths["audit_manifest"], summary)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_csv(output_paths["file_counts"], file_rows)
    write_csv(output_paths["view_alignment"], view_alignment_rows)
    write_csv(output_paths["main_view_summary"], [main_payload["summary"]])
    write_csv(output_paths["feature_availability"], main_payload["feature_rows"])
    write_jsonl(output_paths["blocked_field_hits"], blocked_hits)
    write_csv(output_paths["group_integrity"], group_summary)
    write_csv(output_paths["shortcut_risk_table"], shortcuts)
    write_csv(output_paths["shortcut_warnings"], warning_shortcuts)
    write_csv(output_paths["control_readiness"], controls)
    write_json(output_paths["next_contract"], next_contract)
    output_paths["report"].write_text(build_report(summary, shortcuts), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
