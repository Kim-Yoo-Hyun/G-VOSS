#!/usr/bin/env python3
"""Validate support/contact harder-route Docker materialization outputs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_harder_route_materialization_plan_after_source_inventory"
)
DEFAULT_MATERIALIZATION_DIR = (
    REPO_ROOT / "experiments/H002_compatibility_routing/support_contact_harder_materialization/latest"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_harder_route_docker_materialization_after_plan"
)

EXPECTED_PLAN_STATUS = "h002_support_contact_harder_route_materialization_plan_after_source_inventory_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_support_contact_harder_route_docker_materialization_after_plan"
EXPECTED_RUNTIME_STATUS = "h002_support_contact_harder_route_materialization_ready"
EXPECTED_RUNTIME_SCHEMA = "h002_support_contact_harder_route_materialization_v1"

SCHEMA_VERSION = "h002_support_contact_harder_route_docker_materialization_after_plan_v1"
STATUS_READY = "h002_support_contact_harder_route_docker_materialization_after_plan_ready"
STATUS_ERRORS = "h002_support_contact_harder_route_docker_materialization_after_plan_errors"
SELECTED_PATH = "support_contact_harder_route_materialized_select_schema_shortcut_audit"
NEXT_TODO = "compatibility_dataset_v3_support_contact_harder_route_schema_shortcut_audit_after_docker_materialization"

EXPECTED_ROWS = 3178
EXPECTED_GROUPS = 1589
EXPECTED_FEATURE_MIN = 40


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--materialization-dir", type=Path, default=DEFAULT_MATERIALIZATION_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
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


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


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


def validate_plan(plan_summary: dict[str, Any], plan_errors: int) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0 or plan_errors != 0:
        errors.append(
            {
                "error_type": "plan_validation_errors_present",
                "summary_errors": plan_summary.get("validation_errors"),
                "file_errors": plan_errors,
            }
        )
    return errors


def validate_runtime(materialization_dir: Path, manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    required = {
        "candidate_rows": materialization_dir / "candidate_rows.jsonl",
        "model_safe_main_no_class": materialization_dir / "model_safe_main_no_class.jsonl",
        "model_safe_main_with_class_ablation": materialization_dir / "model_safe_main_with_class_ablation.jsonl",
        "model_safe_geometry_only": materialization_dir / "model_safe_geometry_only.jsonl",
        "model_safe_qe_diagnostic": materialization_dir / "model_safe_qe_diagnostic.jsonl",
        "hidden_manifest": materialization_dir / "hidden_manifest.jsonl",
        "group_manifest": materialization_dir / "group_manifest.jsonl",
        "validation_errors": materialization_dir / "validation_errors.jsonl",
    }
    counts = {name: line_count(path) for name, path in required.items()}
    if manifest.get("status") != EXPECTED_RUNTIME_STATUS:
        errors.append({"error_type": "unexpected_runtime_status", "actual": manifest.get("status")})
    if manifest.get("schema_version") != EXPECTED_RUNTIME_SCHEMA:
        errors.append({"error_type": "unexpected_runtime_schema", "actual": manifest.get("schema_version")})
    if manifest.get("validation_errors") != 0 or counts["validation_errors"] != 0:
        errors.append(
            {
                "error_type": "runtime_validation_errors_present",
                "summary_errors": manifest.get("validation_errors"),
                "file_errors": counts["validation_errors"],
            }
        )
    for name, count in counts.items():
        if name == "group_manifest":
            expected = EXPECTED_GROUPS
        elif name == "validation_errors":
            expected = 0
        else:
            expected = EXPECTED_ROWS
        if count != expected:
            errors.append({"error_type": "line_count_mismatch", "file": name, "actual": count, "expected": expected})

    boundary = manifest.get("boundary", {})
    if boundary.get("main_view") != "model_safe_main_no_class":
        errors.append({"error_type": "unexpected_main_view", "actual": boundary.get("main_view")})
    if boundary.get("main_C_e_allowed_blocks") != ["T_e", "G_e"]:
        errors.append({"error_type": "unexpected_allowed_blocks", "actual": boundary.get("main_C_e_allowed_blocks")})
    for key in ["paper_metric_produced", "official_test_usage", "source_reranking_run", "p_rel_claim_enabled", "p_obs_claim_enabled"]:
        if manifest.get(key) is not False:
            errors.append({"error_type": "unexpected_runtime_claim_boundary", "key": key, "actual": manifest.get(key)})
    if manifest.get("official_validation_eval_only") is not True:
        errors.append({"error_type": "official_validation_not_eval_only", "actual": manifest.get("official_validation_eval_only")})

    ids_by_view: dict[str, set[str]] = {}
    for name, path in required.items():
        if name in {"validation_errors"}:
            continue
        ids_by_view[name] = {row.get("candidate_id") for row in iter_jsonl(path)}
    base_ids = ids_by_view.get("model_safe_main_no_class", set())
    for name, ids in ids_by_view.items():
        if name == "group_manifest":
            continue
        if ids != base_ids:
            errors.append({"error_type": "candidate_id_set_mismatch", "view": name, "missing": len(base_ids - ids), "extra": len(ids - base_ids)})

    no_class_bad = 0
    no_class_feature_counts: Counter[str] = Counter()
    labels = Counter()
    predicates = Counter()
    for row in iter_jsonl(required["model_safe_main_no_class"]):
        blocks = row.get("feature_blocks", {})
        if set(blocks) != {"T_e", "G_e"}:
            no_class_bad += 1
        t_e = blocks.get("T_e", {})
        if "subject_class_label" in t_e or "object_class_label" in t_e:
            no_class_bad += 1
        if row.get("feature_use_policy", {}).get("main_C_e_allowed_blocks") != ["T_e", "G_e"]:
            no_class_bad += 1
        if "target_y" in row:
            no_class_bad += 1
        labels[str(row.get("labels", {}).get("C_e"))] += 1
        predicates[str(row.get("predicate_label"))] += 1
        for feature in blocks.get("G_e", {}).get("g_e_feature_names", []):
            no_class_feature_counts[feature] += 1
    if no_class_bad:
        errors.append({"error_type": "model_safe_main_no_class_policy_violations", "rows": no_class_bad})
    if labels != Counter({"0": EXPECTED_ROWS // 2, "1": EXPECTED_ROWS // 2}):
        errors.append({"error_type": "unexpected_label_balance", "actual": dict(labels)})
    if predicates != Counter({"standing on": EXPECTED_ROWS // 2, "lying on": EXPECTED_ROWS // 2}):
        errors.append({"error_type": "unexpected_predicate_balance", "actual": dict(predicates)})
    if len(no_class_feature_counts) < EXPECTED_FEATURE_MIN:
        errors.append({"error_type": "too_few_features", "actual": len(no_class_feature_counts), "required": EXPECTED_FEATURE_MIN})

    bad_groups = 0
    for row in iter_jsonl(required["group_manifest"]):
        if row.get("pair_integrity_ok") is not True:
            bad_groups += 1
    if bad_groups:
        errors.append({"error_type": "bad_group_integrity_rows", "rows": bad_groups})

    feature_rows = read_csv(materialization_dir / "feature_availability.csv")
    low_feature_rows = []
    for row in feature_rows:
        try:
            present_rate = float(row.get("present_rate", "0"))
        except ValueError:
            present_rate = 0.0
        if present_rate < 1.0:
            low_feature_rows.append(row)
    if low_feature_rows:
        errors.append({"error_type": "incomplete_feature_availability", "rows": len(low_feature_rows)})

    file_rows = [{"file": name, "line_count": count} for name, count in sorted(counts.items())]
    view_rows = [
        {
            "view": "model_safe_main_no_class",
            "rows": counts["model_safe_main_no_class"],
            "feature_count": len(no_class_feature_counts),
            "label_0": labels.get("0", 0),
            "label_1": labels.get("1", 0),
            "standing_on": predicates.get("standing on", 0),
            "lying_on": predicates.get("lying on", 0),
            "policy_violations": no_class_bad,
        },
        {
            "view": "group_manifest",
            "rows": counts["group_manifest"],
            "bad_group_count": bad_groups,
        },
    ]
    return errors, counts, file_rows, view_rows


def build_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# H002 Support/Contact Harder Route Docker Materialization After Plan",
            "",
            "## Status",
            "",
            "```text",
            f"artifact_root = {summary['output_paths']['artifact_root']}",
            f"status = {summary['status']}",
            f"selected_path = {summary['selected_path']}",
            f"validation_errors = {summary['validation_errors']}",
            f"next_todo = {summary['next_todo']}",
            "```",
            "",
            "## Runtime Output",
            "",
            "```text",
            f"candidate_rows = {summary['runtime_counts']['candidate_rows']}",
            f"model_safe_main_no_class = {summary['runtime_counts']['model_safe_main_no_class']}",
            f"model_safe_main_with_class_ablation = {summary['runtime_counts']['model_safe_main_with_class_ablation']}",
            f"model_safe_geometry_only = {summary['runtime_counts']['model_safe_geometry_only']}",
            f"model_safe_qe_diagnostic = {summary['runtime_counts']['model_safe_qe_diagnostic']}",
            f"hidden_manifest = {summary['runtime_counts']['hidden_manifest']}",
            f"group_manifest = {summary['runtime_counts']['group_manifest']}",
            "metrics_run = false",
            "official_test_usage = false",
            "```",
            "",
            "## Decision",
            "",
            "The Docker materializer output is structurally ready for a schema/shortcut audit.",
            "This is still not a metric run and not a paper result.",
        ]
    ) + "\n"


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(args.plan_dir / "summary.json") if (args.plan_dir / "summary.json").exists() else {}
    plan_error_count = line_count(args.plan_dir / "validation_errors.jsonl")
    runtime_manifest = read_json(args.materialization_dir / "row_manifest.json") if (args.materialization_dir / "row_manifest.json").exists() else {}

    validation_errors = validate_plan(plan_summary, plan_error_count)
    runtime_errors, runtime_counts, file_rows, view_rows = validate_runtime(args.materialization_dir, runtime_manifest)
    validation_errors.extend(runtime_errors)

    status = STATUS_ERRORS if validation_errors else STATUS_READY
    selected_path = "blocked_by_validation_errors" if validation_errors else SELECTED_PATH
    next_todo = EXPECTED_PLAN_NEXT if validation_errors else NEXT_TODO

    output_paths = {
        "artifact_root": args.output_dir,
        "summary": args.output_dir / "summary.json",
        "file_counts": args.output_dir / "file_counts.csv",
        "view_integrity": args.output_dir / "view_integrity.csv",
        "feature_availability": args.output_dir / "feature_availability_snapshot.csv",
        "next_contract": args.output_dir / "next_contract.json",
        "report": args.output_dir / "report.md",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }
    next_contract = {
        "next_todo": NEXT_TODO,
        "selected_path": SELECTED_PATH,
        "purpose": "Audit richer support/contact materialization for schema leakage, shortcut risk, and control readiness before any metric runner.",
        "must_check": [
            "model_safe_main_no_class has no class labels, Q_e, Z_e, H001 p_geom_valid, GT/source, or construction fields",
            "model_safe_main_with_class_ablation remains ablation-only",
            "within-class-pair shuffled-G control can be constructed",
            "predicate x class-pair shortcut remains reported",
            "all 43 richer G_e features are available or explicitly masked",
        ],
        "must_not_do": [
            "do not run official test",
            "do not run metric before schema/shortcut audit passes",
            "do not promote support_contact as solved",
        ],
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "input_paths": {
            "plan_dir": rel_path(args.plan_dir),
            "materialization_dir": rel_path(args.materialization_dir),
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "runtime_counts": runtime_counts,
        "decision": {
            "docker_materialization_ready": not bool(validation_errors),
            "schema_shortcut_audit_next": not bool(validation_errors),
            "paper_metric_promoted": False,
            "official_test_usage": False,
            "metrics_run": False,
        },
    }

    write_json(output_paths["summary"], summary)
    write_csv(output_paths["file_counts"], file_rows)
    write_csv(output_paths["view_integrity"], view_rows)
    write_csv(output_paths["feature_availability"], read_csv(args.materialization_dir / "feature_availability.csv"))
    write_json(output_paths["next_contract"], next_contract)
    output_paths["report"].write_text(build_report(summary), encoding="utf-8")
    write_jsonl(output_paths["validation_errors"], validation_errors)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
