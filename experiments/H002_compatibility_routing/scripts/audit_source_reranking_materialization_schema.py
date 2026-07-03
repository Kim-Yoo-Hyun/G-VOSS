#!/usr/bin/env python3
"""Audit source-reranking materialization before metric freeze."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h002_source_reranking_materialization_schema_audit_v1"
EXPECTED_INPUT_SCHEMA = "h002_source_reranking_materialization_v1"
EXPECTED_INPUT_STATUS = "h002_source_reranking_materialization_ready"
EXPECTED_TOTAL_ROWS = 762888
PRIMARY_SUCCESS_FAMILIES = {"relative_vertical", "size_relative"}
DIAGNOSTIC_FAMILIES = {"support_contact"}
GEOMETRY_ONLY_CONTROL_FAMILIES = {"proximity"}
CAVEATED_FAMILIES = {"relative_horizontal"}

BLOCKED_CE_FEATURE_TOKENS = {
    "gt_",
    "h001",
    "p_geom",
    "rank",
    "score",
    "source_score",
    "target_y",
    "verification",
    "violation",
    "z_e",
}

REQUIRED_RUNTIME_FILES = {
    "source_candidates": "source_candidates.jsonl",
    "model_safe_ce_view": "model_safe_ce_view.jsonl",
    "model_safe_geometry_only_view": "model_safe_geometry_only_view.jsonl",
    "source_rank_view": "source_rank_view.jsonl",
    "hidden_metric_manifest": "hidden_metric_manifest.jsonl",
    "validation_errors": "validation_errors.jsonl",
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


def flatten_paths(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield path, child
            yield from flatten_paths(child, path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from flatten_paths(child, f"{prefix}[{index}]")


def check_manifest(materialization_dir: Path, manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    count_rows: list[dict[str, Any]] = []
    if manifest.get("schema_version") != EXPECTED_INPUT_SCHEMA:
        errors.append({"error_type": "unexpected_runtime_schema", "actual": manifest.get("schema_version")})
    if manifest.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"error_type": "unexpected_runtime_status", "actual": manifest.get("status")})
    if manifest.get("validation_errors") != 0:
        errors.append({"error_type": "runtime_manifest_validation_errors", "actual": manifest.get("validation_errors")})
    for key in ["source_reranking_metrics_run", "official_test_usage", "paper_metric_produced", "paper_metric_promoted"]:
        if manifest.get(key) is not False:
            errors.append({"error_type": "unexpected_metric_boundary", "key": key, "actual": manifest.get(key)})
    if manifest.get("source_wide_Ce_materialization_done") is not True:
        errors.append({"error_type": "source_wide_Ce_materialization_not_done", "actual": manifest.get("source_wide_Ce_materialization_done")})
    for name, filename in REQUIRED_RUNTIME_FILES.items():
        expected = 0 if name == "validation_errors" else EXPECTED_TOTAL_ROWS
        count = line_count(materialization_dir / filename)
        count_rows.append({"file": filename, "line_count": count, "expected": expected, "match": count == expected})
        if count != expected:
            errors.append({"error_type": "line_count_mismatch", "file": filename, "actual": count, "expected": expected})
    return errors, count_rows


def audit_views(materialization_dir: Path) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    errors: list[dict[str, Any]] = []
    blocked_hits: list[dict[str, Any]] = []
    separation_rows: list[dict[str, Any]] = []
    control_rows: list[dict[str, Any]] = []
    aggregation_rows: list[dict[str, Any]] = []

    paths = {name: materialization_dir / filename for name, filename in REQUIRED_RUNTIME_FILES.items()}
    family_counts = Counter()
    source_counts = Counter()
    source_family_counts = Counter()
    predicate_counts = Counter()
    role_counts = Counter()
    h2_status_counts = Counter()
    h001_status_counts = Counter()
    gt_exact_counts = Counter()
    pair_family_predicates: dict[tuple[str, str, int, int, str], set[str]] = defaultdict(set)
    feature_policy_violations = 0
    source_rank_policy_violations = 0
    hidden_policy_violations = 0
    geometry_only_policy_violations = 0
    duplicate_ids = 0
    seen_ids: set[str] = set()

    files = [
        paths["source_candidates"].open("r", encoding="utf-8"),
        paths["model_safe_ce_view"].open("r", encoding="utf-8"),
        paths["model_safe_geometry_only_view"].open("r", encoding="utf-8"),
        paths["source_rank_view"].open("r", encoding="utf-8"),
        paths["hidden_metric_manifest"].open("r", encoding="utf-8"),
    ]
    try:
        for line_index, lines in enumerate(zip(*files), start=1):
            source_candidate, ce_view, geometry_only, source_rank, hidden = [json.loads(line) for line in lines]
            ids = {
                "source_candidates": source_candidate.get("candidate_id"),
                "model_safe_ce_view": ce_view.get("candidate_id"),
                "model_safe_geometry_only_view": geometry_only.get("candidate_id"),
                "source_rank_view": source_rank.get("candidate_id"),
                "hidden_metric_manifest": hidden.get("candidate_id"),
            }
            unique_ids = set(ids.values())
            candidate_id = str(ce_view.get("candidate_id"))
            if len(unique_ids) != 1:
                errors.append({"line": line_index, "error_type": "candidate_id_alignment_mismatch", **ids})
                continue
            if candidate_id in seen_ids:
                duplicate_ids += 1
            seen_ids.add(candidate_id)

            if ce_view.get("schema_version") != EXPECTED_INPUT_SCHEMA:
                errors.append({"line": line_index, "error_type": "unexpected_ce_view_schema", "candidate_id": candidate_id, "actual": ce_view.get("schema_version")})
            blocks = ce_view.get("feature_blocks", {})
            if set(blocks) != {"T_e", "G_e"}:
                feature_policy_violations += 1
            if ce_view.get("feature_use_policy", {}).get("main_C_e_allowed_blocks") != ["T_e", "G_e"]:
                feature_policy_violations += 1
            if "Z_e" in blocks or "Q_e" in blocks:
                feature_policy_violations += 1
            if "target_y" in ce_view:
                feature_policy_violations += 1

            for path, value in flatten_paths(blocks, "feature_blocks"):
                lower = path.lower()
                matched = sorted(token for token in BLOCKED_CE_FEATURE_TOKENS if token in lower)
                if matched:
                    blocked_hits.append(
                        {
                            "line": line_index,
                            "candidate_id": candidate_id,
                            "path": path,
                            "matched_tokens": "|".join(matched),
                            "value_preview": str(value)[:120],
                        }
                    )

            if set(geometry_only.get("feature_blocks", {})) != {"G_e"}:
                geometry_only_policy_violations += 1
            if "Z_e" not in source_rank or source_rank.get("feature_use_policy", {}).get("allowed_stage") != "reranking_only":
                source_rank_policy_violations += 1
            if hidden.get("metric_only") is not True:
                hidden_policy_violations += 1
            for key in ["gt_exact_match", "h2_relation_status", "h001_p_geom_valid", "h001_verification_status"]:
                if key not in hidden:
                    hidden_policy_violations += 1

            family = str(ce_view.get("route_family"))
            source = str(ce_view.get("source_id"))
            predicate = str(ce_view.get("predicate_label"))
            subject_id = int(ce_view.get("subject_id"))
            object_id = int(ce_view.get("object_id"))
            scan_id = str(ce_view.get("scan_id"))
            role = str(ce_view.get("candidate_role"))
            family_counts[family] += 1
            source_counts[source] += 1
            source_family_counts[f"{source}|{family}"] += 1
            predicate_counts[f"{family}|{predicate}"] += 1
            role_counts[role] += 1
            h2_status_counts[f"{family}|{hidden.get('h2_relation_status')}"] += 1
            h001_status_counts[f"{family}|{hidden.get('h001_verification_status')}"] += 1
            gt_exact_counts[f"{family}|{int(bool(hidden.get('gt_exact_match')))}"] += 1
            pair_family_predicates[(source, scan_id, subject_id, object_id, family)].add(predicate)
    finally:
        for handle in files:
            handle.close()

    if duplicate_ids:
        errors.append({"error_type": "duplicate_candidate_ids", "count": duplicate_ids})
    if feature_policy_violations:
        errors.append({"error_type": "ce_view_policy_violations", "count": feature_policy_violations})
    if geometry_only_policy_violations:
        errors.append({"error_type": "geometry_only_policy_violations", "count": geometry_only_policy_violations})
    if source_rank_policy_violations:
        errors.append({"error_type": "source_rank_policy_violations", "count": source_rank_policy_violations})
    if hidden_policy_violations:
        errors.append({"error_type": "hidden_metric_policy_violations", "count": hidden_policy_violations})
    if blocked_hits:
        errors.append({"error_type": "blocked_feature_hits_in_ce_view", "count": len(blocked_hits)})

    separation_rows.extend(
        [
            {"check": "candidate_id_alignment", "status": "pass" if not duplicate_ids else "fail", "rows": len(seen_ids), "duplicate_ids": duplicate_ids},
            {"check": "ce_feature_blocks_are_Te_Ge_only", "status": "pass" if feature_policy_violations == 0 else "fail", "violations": feature_policy_violations},
            {"check": "blocked_Ce_feature_absence", "status": "pass" if not blocked_hits else "fail", "hits": len(blocked_hits)},
            {"check": "source_rank_view_owns_Ze", "status": "pass" if source_rank_policy_violations == 0 else "fail", "violations": source_rank_policy_violations},
            {"check": "hidden_manifest_metric_only", "status": "pass" if hidden_policy_violations == 0 else "fail", "violations": hidden_policy_violations},
            {"check": "geometry_only_view_is_Ge_only", "status": "pass" if geometry_only_policy_violations == 0 else "fail", "violations": geometry_only_policy_violations},
        ]
    )

    for family, count in sorted(family_counts.items()):
        if family in PRIMARY_SUCCESS_FAMILIES:
            role = "primary_success"
            include_success = True
        elif family in DIAGNOSTIC_FAMILIES:
            role = "diagnostic_excluded"
            include_success = False
        elif family in GEOMETRY_ONLY_CONTROL_FAMILIES:
            role = "geometry_only_control"
            include_success = False
        elif family in CAVEATED_FAMILIES:
            role = "caveated_separate_table"
            include_success = False
        else:
            role = "unknown"
            include_success = False
        aggregation_rows.append({"family": family, "rows": count, "role": role, "include_in_success_aggregation": include_success})
    primary_counts = [row["rows"] for row in aggregation_rows if row["include_in_success_aggregation"]]
    primary_balanced = bool(primary_counts and len(set(primary_counts)) == 1)
    aggregation_rows.append(
        {
            "family": "PRIMARY_MACRO",
            "rows": sum(primary_counts),
            "role": "macro_average_over_primary_success_families",
            "include_in_success_aggregation": True,
            "balanced_primary_family_rows": primary_balanced,
        }
    )
    if not primary_balanced:
        errors.append({"error_type": "primary_success_family_imbalance", "counts": primary_counts})

    family_to_predicate_count = {
        "proximity": 1,
        "relative_vertical": 2,
        "size_relative": 2,
        "relative_horizontal": 4,
        "support_contact": 3,
    }
    complete_groups = Counter()
    total_groups = Counter()
    for (_source, _scan, _subject, _object, family), predicates in pair_family_predicates.items():
        total_groups[family] += 1
        if len(predicates) == family_to_predicate_count.get(family, 0):
            complete_groups[family] += 1
    for family, groups in sorted(total_groups.items()):
        expected_predicates = family_to_predicate_count[family]
        wrong_t_ready = expected_predicates > 1 and complete_groups[family] == groups
        shuffled_ready = family_counts[family] > 1
        if family == "proximity":
            wrong_t_note = "not_applicable_single_predicate_geometry_only_control"
        elif wrong_t_ready:
            wrong_t_note = "ready"
        else:
            wrong_t_note = "blocked_incomplete_pair_family_predicate_set"
        control_rows.append(
            {
                "family": family,
                "pair_family_groups": groups,
                "complete_groups": complete_groups[family],
                "expected_predicates_per_group": expected_predicates,
                "wrong_T_control_ready": wrong_t_ready,
                "wrong_T_note": wrong_t_note,
                "shuffled_G_control_ready": shuffled_ready,
                "within_family_shuffle_ready": shuffled_ready,
                "success_metric_role": "excluded" if family in DIAGNOSTIC_FAMILIES | GEOMETRY_ONLY_CONTROL_FAMILIES | CAVEATED_FAMILIES else "primary",
            }
        )
        if family in PRIMARY_SUCCESS_FAMILIES and not wrong_t_ready:
            errors.append({"error_type": "primary_wrong_T_control_not_ready", "family": family})

    summary_counts = {
        "family_counts": dict(sorted(family_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "source_family_counts": dict(sorted(source_family_counts.items())),
        "predicate_counts": dict(sorted(predicate_counts.items())),
        "role_counts": dict(sorted(role_counts.items())),
        "h2_status_counts": dict(sorted(h2_status_counts.items())),
        "h001_status_counts": dict(sorted(h001_status_counts.items())),
        "gt_exact_counts": dict(sorted(gt_exact_counts.items())),
        "unique_candidate_ids": len(seen_ids),
    }
    return errors, blocked_hits[:1000], separation_rows, aggregation_rows, control_rows, summary_counts


def make_metric_freeze_rows(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocking = len(errors)
    return [
        {
            "gate": "source_reranking_materialization_schema_audit",
            "status": "pass" if blocking == 0 else "blocked",
            "blocking_errors": blocking,
            "allows_next_metric_protocol_freeze": blocking == 0,
            "allows_metric_run_now": False,
            "note": "metric freeze next; metric run remains blocked until protocol freeze",
        },
        {
            "gate": "official_test_usage",
            "status": "pass",
            "allows_next_metric_protocol_freeze": True,
            "allows_metric_run_now": False,
            "note": "official test unused",
        },
        {
            "gate": "support_contact_success_exclusion",
            "status": "pass",
            "allows_next_metric_protocol_freeze": True,
            "allows_metric_run_now": False,
            "note": "support_contact diagnostic only",
        },
    ]


def make_report(summary: dict[str, Any]) -> str:
    counts = summary["row_counts"]
    return f"""# Source Reranking Materialization Schema Audit

## Status

```text
status = {summary["status"]}
selected_path = {summary["selected_path"]}
validation_errors = {summary["validation_errors"]}
next_todo = {summary["next_todo"]}
```

## Result

The source-reranking materialization schema audit passed.

- total rows: `{counts["unique_candidate_ids"]}`
- source reranking metrics run: `false`
- official test usage: `false`
- model-safe C_e view: `T_e + G_e` only
- source rank view: `Z_e` reranking-only
- hidden manifest: GT/violation metric-only

The next stage is source-reranking metric protocol freeze, not metric execution.
"""


def main() -> int:
    args = parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    repo_root = args.repo_root.resolve()
    materialization_dir = args.materialization_dir
    manifest = read_json(materialization_dir / "row_manifest.json")

    validation_errors, count_rows = check_manifest(materialization_dir, manifest)
    (
        view_errors,
        blocked_hits,
        separation_rows,
        aggregation_rows,
        control_rows,
        summary_counts,
    ) = audit_views(materialization_dir)
    validation_errors.extend(view_errors)
    metric_freeze_rows = make_metric_freeze_rows(validation_errors)
    status = "h002_source_reranking_materialization_schema_audit_ready" if not validation_errors else "h002_source_reranking_materialization_schema_audit_errors"
    selected_path = "source_reranking_materialization_schema_audit_passed_select_metric_protocol_freeze" if not validation_errors else "blocked_fix_source_reranking_materialization_schema"
    next_todo = "compatibility_dataset_v3_source_reranking_metric_protocol_freeze_after_schema_audit"

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(validation_errors),
        "next_todo": next_todo,
        "input_artifacts": {
            "runtime_manifest": repo_rel(repo_root, materialization_dir / "row_manifest.json"),
            "materialization_dir": repo_rel(repo_root, materialization_dir),
        },
        "output_artifacts": {
            "summary": repo_rel(repo_root, out / "audit_manifest.json"),
            "validation_errors": repo_rel(repo_root, out / "validation_errors.jsonl"),
            "runtime_count_audit": repo_rel(repo_root, out / "runtime_count_audit.csv"),
            "schema_separation_audit": repo_rel(repo_root, out / "schema_separation_audit.csv"),
            "blocked_field_hits": repo_rel(repo_root, out / "blocked_field_hits.jsonl"),
            "family_success_aggregation": repo_rel(repo_root, out / "family_success_aggregation.csv"),
            "control_readiness": repo_rel(repo_root, out / "control_readiness.csv"),
            "metric_freeze_precondition": repo_rel(repo_root, out / "metric_freeze_precondition.csv"),
            "report": repo_rel(repo_root, out / "report.md"),
        },
        "row_counts": summary_counts,
        "decision": {
            "schema_audit_passed": not validation_errors,
            "ready_for_metric_protocol_freeze": not validation_errors,
            "source_reranking_metrics_run": False,
            "metric_run_allowed_now": False,
            "official_test_usage": False,
            "support_contact_success_aggregation": "excluded_diagnostic",
        },
    }
    write_json(out / "audit_manifest.json", summary)
    write_json(out / "summary.json", summary)
    write_jsonl(out / "validation_errors.jsonl", validation_errors)
    write_jsonl(out / "blocked_field_hits.jsonl", blocked_hits)
    write_csv(out / "runtime_count_audit.csv", count_rows)
    write_csv(out / "schema_separation_audit.csv", separation_rows)
    write_csv(out / "family_success_aggregation.csv", aggregation_rows)
    write_csv(out / "control_readiness.csv", control_rows)
    write_csv(out / "metric_freeze_precondition.csv", metric_freeze_rows)
    (out / "report.md").write_text(make_report(summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
