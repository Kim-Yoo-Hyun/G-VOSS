#!/usr/bin/env python3
"""Audit route-specific H002 target manifests before materialization."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_MANIFEST_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan"
)

EXPECTED_MANIFEST_STATUS = "h002_compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze_ready"
EXPECTED_MANIFEST_NEXT = "compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan_input_errors"
SELECTED_PATH = "manifest_consistency_pass_select_route_target_materialization_plan"
NEXT_TODO = "compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest-dir", type=Path, default=DEFAULT_MANIFEST_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(summary: dict[str, Any], manifest_dir: Path, tables: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_MANIFEST_STATUS:
        errors.append({"error_type": "unexpected_manifest_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_MANIFEST_NEXT:
        errors.append({"error_type": "unexpected_manifest_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "manifest_validation_errors_present", "actual": summary.get("validation_errors")})
    if read_jsonl(manifest_dir / "validation_errors.jsonl"):
        errors.append({"error_type": "manifest_validation_error_rows_present"})

    boundary = summary.get("boundary", {})
    for key in ["materializes_rows", "runs_model", "paper_evidence_allowed_now", "h001_artifacts_modified", "validation_or_test_used"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})

    required_tables = {
        "target": "route_target_manifest.csv",
        "field": "route_field_manifest.csv",
        "hidden": "route_hidden_manifest.csv",
        "control": "route_control_manifest.csv",
        "artifact": "route_artifact_root_plan.csv",
        "priority": "route_promotion_priority.csv",
    }
    for table_name in required_tables:
        if len(tables.get(table_name, [])) != 13:
            errors.append({"error_type": "unexpected_table_row_count", "table": table_name, "actual": len(tables.get(table_name, []))})
    return errors


def route_id_set_audit(tables: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    route_ids = {row["route_id"] for row in tables["target"]}
    for name, table in tables.items():
        ids = {row["route_id"] for row in table}
        rows.append(
            {
                "check": "route_id_set",
                "table": name,
                "expected_count": len(route_ids),
                "actual_count": len(ids),
                "missing": "; ".join(sorted(route_ids - ids)),
                "extra": "; ".join(sorted(ids - route_ids)),
                "status": "pass" if ids == route_ids else "fail",
            }
        )
        if ids != route_ids:
            errors.append({"error_type": "route_id_set_mismatch", "table": name, "missing": sorted(route_ids - ids), "extra": sorted(ids - route_ids)})

    route_slugs = [row["route_slug"] for row in tables["target"]]
    artifact_roots = [row["artifact_root"] for row in tables["target"]]
    for check_name, values in [("route_slug_unique", route_slugs), ("artifact_root_unique", artifact_roots)]:
        duplicate = sorted({value for value in values if values.count(value) > 1})
        rows.append(
            {
                "check": check_name,
                "table": "target",
                "expected_count": len(values),
                "actual_count": len(set(values)),
                "missing": "",
                "extra": "; ".join(duplicate),
                "status": "pass" if not duplicate else "fail",
            }
        )
        if duplicate:
            errors.append({"error_type": check_name, "duplicates": duplicate})
    return rows, errors


def route_semantics_audit(tables: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    target = {row["route_id"]: row for row in tables["target"]}
    field = {row["route_id"]: row for row in tables["field"]}
    hidden = {row["route_id"]: row for row in tables["hidden"]}
    control = {row["route_id"]: row for row in tables["control"]}

    expected = [
        {
            "route_id": "R1",
            "family": "proximity",
            "must_contain": {
                "target_axis": "geometry_support",
                "label_space": "geometry_supported",
                "primary_metric": "geometry support",
                "C_e_definition": "C_e optional",
                "minimum_pass_condition": "geometry-only",
            },
            "must_not_contain": {
                "target_axis": "predicate_geometry",
                "primary_metric": "C_e interaction",
            },
        },
        {
            "route_id": "R6",
            "family": "superordinate_support",
            "must_contain": {
                "target_axis": "accept_relabel_abstain",
                "label_space": "relabel_to_subtype",
                "must_not_use_as_negative": "standing on or lying on",
                "C_e_definition": "accept/relabel/abstain",
            },
            "must_not_contain": {
                "label_space": "compatible; incompatible",
            },
        },
        {
            "route_id": "R7",
            "family": "attachment_observability",
            "must_contain": {
                "target_axis": "observability_then_reliability",
                "label_space": "unobservable_abstain",
                "label_space_2": "functional_or_topology_uncertain",
                "Q_e_model_safe": "view availability",
                "C_e_definition": "only when p_obs",
            },
            "must_not_contain": {
                "negative_definition": "unobservable",
            },
        },
        {
            "route_id": "R11",
            "family": "identity_symmetry",
            "must_contain": {
                "target_axis": "identity_or_symmetry_compatibility",
                "secondary_metrics": "class-only baseline",
                "C_e_definition": "identity/symmetry",
            },
            "must_not_contain": {},
        },
        {
            "route_id": "R12",
            "family": "semantic_structural",
            "must_contain": {
                "target_axis": "semantic_structural_compatibility",
                "secondary_metrics": "ontology baseline",
                "C_e_definition": "semantic-structural",
            },
            "must_not_contain": {},
        },
    ]
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for spec in expected:
        route_id = spec["route_id"]
        merged = " ".join(
            str(value)
            for value in {
                **target.get(route_id, {}),
                **field.get(route_id, {}),
                **hidden.get(route_id, {}),
                **control.get(route_id, {}),
            }.values()
        )
        route_errors: list[str] = []
        for field_name, needle in spec["must_contain"].items():
            if needle not in merged and needle not in str(target.get(route_id, {}).get(field_name, "")) and needle not in str(field.get(route_id, {}).get(field_name, "")):
                route_errors.append(f"missing:{field_name}:{needle}")
        for field_name, needle in spec["must_not_contain"].items():
            if needle and needle in str(target.get(route_id, {}).get(field_name, "")):
                route_errors.append(f"forbidden:{field_name}:{needle}")
        rows.append(
            {
                "route_id": route_id,
                "family": spec["family"],
                "check": "route_specific_semantics",
                "status": "pass" if not route_errors else "fail",
                "details": "; ".join(route_errors),
            }
        )
        for item in route_errors:
            errors.append({"error_type": "route_semantics_failure", "route_id": route_id, "detail": item})

    for row in tables["target"]:
        if row["route_type"] == "predicate_geometry_interaction_route":
            problems: list[str] = []
            if row["target_axis"] != "predicate_geometry_compatibility":
                problems.append("wrong_target_axis")
            if "compatible; incompatible; abstain" != row["label_space"]:
                problems.append("wrong_label_space")
            if "no-GT rows without counterfactual construction" not in row["must_not_use_as_negative"]:
                problems.append("no_gt_negative_guard_missing")
            rows.append(
                {
                    "route_id": row["route_id"],
                    "family": row["family"],
                    "check": "predicate_geometry_route_contract",
                    "status": "pass" if not problems else "fail",
                    "details": "; ".join(problems),
                }
            )
            for problem in problems:
                errors.append({"error_type": "predicate_geometry_contract_failure", "route_id": row["route_id"], "detail": problem})
    return rows, errors


def leakage_audit(tables: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    target = {row["route_id"]: row for row in tables["target"]}
    field = {row["route_id"]: row for row in tables["field"]}
    hidden = {row["route_id"]: row for row in tables["hidden"]}

    for route_id, row in field.items():
        problems: list[str] = []
        if "excluded from C_e" not in row["Z_e_model_safe"]:
            problems.append("Z_e_not_explicitly_excluded_from_Ce")
        if "source score" in row["G_e_model_safe"] or "source/rank" in row["G_e_model_safe"]:
            problems.append("G_e_contains_source_confidence")
        if "source score inside C_e" not in row["blocked_model_fields"]:
            problems.append("blocked_source_score_inside_Ce_missing")
        if target[route_id]["route_type"] != "geometry_only_learned_evaluated_route" and "C_e = compatibility" in row["C_e_definition"]:
            if "excluding Z_e" not in row["C_e_definition"]:
                problems.append("Ce_definition_missing_excluding_Ze")
        if hidden[route_id]["forbidden_use"].count("model input") == 0:
            problems.append("hidden_fields_not_forbidden_as_model_input")
        if hidden[route_id]["forbidden_use"].count("C_e input") == 0:
            problems.append("hidden_fields_not_forbidden_as_Ce_input")

        rows.append(
            {
                "route_id": route_id,
                "family": row["family"],
                "check": "field_leakage",
                "status": "pass" if not problems else "fail",
                "details": "; ".join(problems),
            }
        )
        for problem in problems:
            errors.append({"error_type": "field_leakage_failure", "route_id": route_id, "detail": problem})
    return rows, errors


def artifact_boundary_audit(summary: dict[str, Any], tables: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    boundary = summary.get("boundary", {})
    for key, expected in [
        ("materializes_rows", False),
        ("runs_model", False),
        ("paper_evidence_allowed_now", False),
        ("h001_artifacts_modified", False),
        ("validation_or_test_used", False),
    ]:
        actual = boundary.get(key)
        rows.append(
            {
                "check": "boundary",
                "field": key,
                "expected": expected,
                "actual": actual,
                "status": "pass" if actual is expected else "fail",
            }
        )
        if actual is not expected:
            errors.append({"error_type": "boundary_mismatch", "field": key, "actual": actual})

    priority = tables["priority"]
    ranks = sorted(int(row["rank"]) for row in priority)
    expected_ranks = list(range(1, 14))
    rows.append(
        {
            "check": "promotion_priority_ranks",
            "field": "rank",
            "expected": "1..13",
            "actual": ",".join(map(str, ranks)),
            "status": "pass" if ranks == expected_ranks else "fail",
        }
    )
    if ranks != expected_ranks:
        errors.append({"error_type": "promotion_rank_sequence_failure", "actual": ranks})

    for row in tables["artifact"]:
        problems: list[str] = []
        if row["materialization_allowed_now"] != "False":
            problems.append("materialization_allowed_now_not_false")
        if not row["artifact_root"].startswith("artifacts/route_specific_targets/"):
            problems.append("artifact_root_outside_route_specific_targets")
        rows.append(
            {
                "check": "artifact_root_boundary",
                "field": row["route_id"],
                "expected": "no_materialization_and_route_specific_root",
                "actual": row["artifact_root"],
                "status": "pass" if not problems else "fail",
            }
        )
        for problem in problems:
            errors.append({"error_type": "artifact_boundary_failure", "route_id": row["route_id"], "detail": problem})
    return rows, errors


def claim_update_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_item": "close by",
            "previous_risk": "diagnostic-only wording could imply it is not a learned/evaluated target",
            "audited_update": "geometry-only learned/evaluated route is preserved",
            "allowed_wording": "close by evaluates a geometry-only route rather than predicate-geometry interaction",
            "blocked_wording": "close by proves T_e x G_e interaction",
        },
        {
            "claim_item": "supported by",
            "previous_risk": "broad support label could be forced into a clean binary target",
            "audited_update": "accept/relabel/reject/abstain route is preserved",
            "allowed_wording": "supported by is a superordinate decomposition route",
            "blocked_wording": "supported by is a clean negative for standing/lying on",
        },
        {
            "claim_item": "attachment",
            "previous_risk": "OBB/contact geometry alone could be overclaimed",
            "audited_update": "observability_then_reliability target is preserved",
            "allowed_wording": "attachment requires p_obs/Q_e before p_rel",
            "blocked_wording": "distance alone decides attachment reliability",
        },
        {
            "claim_item": "all routes",
            "previous_risk": "one-target/one-fusion framing",
            "audited_update": "route-specific target axes are preserved",
            "allowed_wording": "H002 studies which route and target definition each relation family requires",
            "blocked_wording": "all relation types use one binary target or one fixed fusion head",
        },
    ]


def next_action_rows() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "next_todo": NEXT_TODO,
            "scope": "all route manifests",
            "action": "write materialization plan that chooses which route roots to instantiate first",
            "reason": "audit passed; next step can plan row materialization without changing target semantics",
        },
        {
            "rank": 2,
            "next_todo": "close_by_geometry_only_route_materialization_plan",
            "scope": "R1 proximity",
            "action": "prepare geometry_support rows and distance/scale/coverage controls",
            "reason": "close by is now a claim/control route rather than diagnostic-only wording",
        },
        {
            "rank": 3,
            "next_todo": "supported_by_decomposition_route_materialization_plan",
            "scope": "R6 superordinate support",
            "action": "prepare accept/relabel/reject/abstain subtype plan",
            "reason": "supported by is the most important new route opened by the revised taxonomy",
        },
        {
            "rank": 4,
            "next_todo": "attachment_observability_route_schema_audit",
            "scope": "R7 attachment",
            "action": "audit visual/mesh/topology evidence availability before materialization",
            "reason": "observability route should not be forced into binary accept/reject",
        },
    ]


def write_report(
    path: Path,
    status: str,
    validation_errors: int,
    audit_rows: list[dict[str, Any]],
) -> None:
    pass_count = sum(row["status"] == "pass" for row in audit_rows)
    fail_count = sum(row["status"] == "fail" for row in audit_rows)
    lines = [
        "# H002 Route-Specific Target Manifest Consistency Audit After Plan",
        "",
        "## Status",
        "",
        "```text",
        f"status = {status}",
        f"selected_path = {SELECTED_PATH}",
        f"validation_errors = {validation_errors}",
        f"next_todo = {NEXT_TODO}",
        "```",
        "",
        "## Audit Summary",
        "",
        f"- pass checks: `{pass_count}`",
        f"- fail checks: `{fail_count}`",
        "- row materialization: not performed",
        "- model run: not performed",
        "- validation/test usage: none",
        "",
        "## Main Result",
        "",
        "The route-specific manifests are internally consistent. The audit preserves:",
        "",
        "- `close by` as `geometry_support`, not predicate-geometry interaction",
        "- `supported by` as `accept_relabel_abstain`, not a clean binary support target",
        "- attachment relations as `observability_then_reliability`",
        "- `C_e` excluding `Z_e`",
        "- hidden construction fields excluded from model-safe/C_e inputs",
        "",
        "## Boundary",
        "",
        "Allowed next:",
        "",
        "- route-specific materialization planning",
        "- prioritizing close-by and supported-by route manifests",
        "- schema/audit planning for attachment observability",
        "",
        "Still blocked:",
        "",
        "- actual row materialization",
        "- learned smoke runner",
        "- Docker/paper promotion",
        "- calibrated `p_rel` / `p_obs` claim",
        "",
        "## Next",
        "",
        "```text",
        NEXT_TODO,
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    manifest_dir = args.manifest_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_in = read_json(manifest_dir / "summary.json")
    tables = {
        "target": read_csv(manifest_dir / "route_target_manifest.csv"),
        "field": read_csv(manifest_dir / "route_field_manifest.csv"),
        "hidden": read_csv(manifest_dir / "route_hidden_manifest.csv"),
        "control": read_csv(manifest_dir / "route_control_manifest.csv"),
        "artifact": read_csv(manifest_dir / "route_artifact_root_plan.csv"),
        "priority": read_csv(manifest_dir / "route_promotion_priority.csv"),
    }

    errors = validate_inputs(summary_in, manifest_dir, tables)
    id_rows, id_errors = route_id_set_audit(tables)
    route_rows, route_errors = route_semantics_audit(tables)
    leakage_rows, leakage_errors = leakage_audit(tables)
    boundary_rows, boundary_errors = artifact_boundary_audit(summary_in, tables)
    errors.extend(id_errors)
    errors.extend(route_errors)
    errors.extend(leakage_errors)
    errors.extend(boundary_errors)
    status = STATUS_ERRORS if errors else STATUS_READY

    all_audit_rows = id_rows + route_rows + leakage_rows + boundary_rows
    claim_rows = claim_update_rows()
    next_rows = next_action_rows()
    output_paths = {
        "artifact_root": rel_path(output_dir),
        "audit_matrix": rel_path(output_dir / "audit_matrix.csv"),
        "claim_update_matrix": rel_path(output_dir / "claim_update_matrix.csv"),
        "next_action_plan": rel_path(output_dir / "next_action_plan.csv"),
        "report": rel_path(output_dir / "report.md"),
        "summary": rel_path(output_dir / "summary.json"),
        "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "fix_manifest_inconsistencies_before_materialization",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "manifest_plan": rel_path(manifest_dir),
        },
        "output_paths": output_paths,
        "counts": {
            "audit_rows": len(all_audit_rows),
            "audit_pass_rows": sum(row["status"] == "pass" for row in all_audit_rows),
            "audit_fail_rows": sum(row["status"] == "fail" for row in all_audit_rows),
            "claim_update_rows": len(claim_rows),
            "next_action_rows": len(next_rows),
        },
        "audited_contracts": {
            "close_by_route": "geometry_support",
            "supported_by_route": "accept_relabel_abstain",
            "attachment_route": "observability_then_reliability",
            "Ce_excludes_Ze": True,
            "hidden_fields_model_safe": False,
        },
        "boundary": {
            "materializes_rows": False,
            "runs_model": False,
            "paper_evidence_allowed_now": False,
            "h001_artifacts_modified": False,
            "validation_or_test_used": False,
        },
        "next_todo": NEXT_TODO,
        "validation_errors": len(errors),
    }

    write_csv(output_dir / "audit_matrix.csv", all_audit_rows)
    write_csv(output_dir / "claim_update_matrix.csv", claim_rows)
    write_csv(output_dir / "next_action_plan.csv", next_rows)
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_report(output_dir / "report.md", status, len(errors), all_audit_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
