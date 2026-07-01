#!/usr/bin/env python3
"""Decide path after support/contact visual/mesh class-pair repair label ingestion."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_INGESTION_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingestion"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion"
)

EXPECTED_INPUT_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_label_ingested_shortcut_risk_blocks_smoke"
)
EXPECTED_INPUT_NEXT = (
    "compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_freeze_diagnostic"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_input_errors"
)
SELECTED_PATH = (
    "freeze_support_contact_visual_mesh_class_pair_repair_as_diagnostic_select_scope_synthesis"
)
NEXT_TODO = (
    "compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
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
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
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


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
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


def target_value(row: dict[str, Any], target_field: str) -> str | None:
    value = row.get(target_field)
    if value is None:
        return None
    return str(value)


def is_generic_endpoint(row: dict[str, Any]) -> bool:
    return str(row.get("generic_endpoint_visible")).lower() == "true"


def majority_diagnostic(
    rows: list[dict[str, Any]],
    target_field: str,
    predictor: str,
    row_filter: Callable[[dict[str, Any]], bool] | None = None,
) -> dict[str, Any]:
    usable = [row for row in rows if target_value(row, target_field) is not None]
    if row_filter is not None:
        usable = [row for row in usable if row_filter(row)]
    target_counts = Counter(target_value(row, target_field) for row in usable)
    total = sum(target_counts.values())
    baseline = (max(target_counts.values()) / total) if total else 0.0
    groups: dict[str, list[str]] = defaultdict(list)
    for row in usable:
        groups[str(row.get(predictor))].append(str(target_value(row, target_field)))
    correct = 0
    mixed_groups = 0
    pure_groups = 0
    max_group_rows = 0
    for values in groups.values():
        counts = Counter(values)
        correct += max(counts.values())
        mixed_groups += int(len(counts) > 1)
        pure_groups += int(len(counts) == 1)
        max_group_rows = max(max_group_rows, len(values))
    majority_accuracy = (correct / total) if total else 0.0
    return {
        "target_field": target_field,
        "predictor": predictor,
        "rows": total,
        "target_counts": dict(target_counts),
        "baseline_accuracy": baseline,
        "majority_rule_accuracy": majority_accuracy,
        "majority_excess_over_baseline": majority_accuracy - baseline,
        "num_groups": len(groups),
        "mixed_groups": mixed_groups,
        "pure_groups": pure_groups,
        "max_group_rows": max_group_rows,
    }


def target_profile(rows: list[dict[str, Any]], name: str, row_filter: Callable[[dict[str, Any]], bool] | None) -> dict[str, Any]:
    filtered = [row for row in rows if row_filter is None or row_filter(row)]
    p_rel_rows = [row for row in filtered if row.get("p_rel_target") is not None]
    relation_counts = Counter(row.get("relation_multiclass_target") for row in filtered)
    p_rel_counts = Counter(str(row.get("p_rel_target")) for row in p_rel_rows)
    diagnostics = [
        majority_diagnostic(filtered, "p_rel_target", "predicate_x_subject_object_class_pair_visible"),
        majority_diagnostic(filtered, "p_rel_target", "subject_object_class_pair"),
        majority_diagnostic(filtered, "p_rel_target", "subject_label"),
        majority_diagnostic(filtered, "p_rel_target", "object_label"),
        majority_diagnostic(filtered, "p_rel_target", "predicate_label"),
        majority_diagnostic(filtered, "relation_multiclass_target", "generic_endpoint_visible"),
        majority_diagnostic(filtered, "relation_multiclass_target", "predicate_x_subject_object_class_pair_visible"),
    ]
    return {
        "profile": name,
        "rows": len(filtered),
        "relation_multiclass_counts": dict(relation_counts),
        "p_rel_binary_rows": len(p_rel_rows),
        "p_rel_counts": dict(p_rel_counts),
        "diagnostics": diagnostics,
    }


def find_diag(diag_rows: list[dict[str, str]], target_name: str, predictor: str) -> dict[str, Any]:
    for row in diag_rows:
        if row.get("target_name") == target_name and row.get("predictor") == predictor:
            out: dict[str, Any] = dict(row)
            for key in [
                "rows",
                "baseline_accuracy",
                "majority_rule_accuracy",
                "majority_excess_over_baseline",
                "normalized_mutual_information",
                "num_groups",
                "mixed_groups",
                "max_group_rows",
                "large_pure_groups",
            ]:
                if key in out:
                    try:
                        out[key] = float(out[key]) if "." in out[key] else int(out[key])
                    except (TypeError, ValueError):
                        pass
            return out
    return {"target_name": target_name, "predictor": predictor, "missing": True}


def validate_input(summary: dict[str, Any], rows: list[dict[str, Any]], diag_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"error_type": "unexpected_input_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_INPUT_NEXT:
        errors.append({"error_type": "unexpected_input_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "input_validation_errors_present", "actual": summary.get("validation_errors")})
    if len(rows) != 480:
        errors.append({"error_type": "target_row_count_mismatch", "actual": len(rows), "expected": 480})
    if not diag_rows:
        errors.append({"error_type": "missing_shortcut_diagnostics_rows"})
    boundary = summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "runs_learned_smoke", "trains_new_model"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    if boundary.get("split") != "train full only":
        errors.append({"error_type": "unexpected_split", "actual": boundary.get("split")})
    return errors


def route_table(summary: dict[str, Any], profiles: list[dict[str, Any]], key_diags: dict[str, Any]) -> list[dict[str, Any]]:
    target_summary = summary["target_summary"]
    non_generic = next(profile for profile in profiles if profile["profile"] == "non_generic_rows")
    non_generic_pred_diag = next(
        diag
        for diag in non_generic["diagnostics"]
        if diag["target_field"] == "p_rel_target" and diag["predictor"] == "predicate_x_subject_object_class_pair_visible"
    )
    return [
        {
            "route": "run_learned_smoke_on_current_class_pair_repair_target",
            "verdict": "reject",
            "evidence": (
                f"p_rel/C_e binary rows are {target_summary['p_rel_binary_rows']} with "
                f"{target_summary['p_rel_binary_counts']}, but "
                f"predicate_x_class_pair majority accuracy is "
                f"{key_diags['p_rel_predicate_x_class_pair']['majority_rule_accuracy']:.4f}."
            ),
            "reason": "The target is count-viable but not identifiable; a model can solve it from predicate and object class labels.",
            "claim_boundary": "no learned smoke, no calibrated p_rel/p_obs claim",
        },
        {
            "route": "generic_endpoint_filtered_target",
            "verdict": "reject_as_main_defer_diagnostic_only",
            "evidence": (
                f"After removing generic endpoints, rows={non_generic['rows']}, "
                f"p_rel rows={non_generic['p_rel_binary_rows']}, p_rel counts={non_generic['p_rel_counts']}, "
                f"predicate_x_class_pair p_rel majority accuracy remains "
                f"{non_generic_pred_diag['majority_rule_accuracy']:.4f}."
            ),
            "reason": "Filtering generic endpoints reduces the multiclass abstain shortcut but does not fix the binary predicate-class shortcut.",
            "claim_boundary": "optional diagnostic only; not main C_e or p_rel evidence",
        },
        {
            "route": "stricter_within_predicate_class_pair_visual_relabel",
            "verdict": "reject_as_current_continuation_defer_new_protocol",
            "evidence": (
                "Current visible-label policy makes every predicate_x_class_pair group pure for the binary target; "
                "the artifact has zero mixed predicate_x_class_pair groups for p_rel/C_e."
            ),
            "reason": (
                "A stricter relabel cannot be obtained by reusing the current proxy target; it needs a new independent "
                "visual/mesh audit protocol or a different source construction."
            ),
            "claim_boundary": "future source/label protocol, not immediate smoke",
        },
        {
            "route": "freeze_support_contact_visual_mesh_class_pair_repair_as_diagnostic",
            "verdict": "selected",
            "evidence": (
                "Class-pair repair improved binary mass but still has predicate_x_class_pair and endpoint-label shortcuts; "
                "p_obs/Q are degenerate because all packets are observable."
            ),
            "reason": "This preserves the negative result without forcing support/contact into a main reliability target.",
            "claim_boundary": (
                "support/contact visual-mesh repair is diagnostic; relative_vertical remains the clean train-only C_e anchor; "
                "support/contact pose-conditioned evidence remains scoped mechanism evidence"
            ),
        },
        {
            "route": "new_independent_gt_or_human_audit_source_for_support_contact",
            "verdict": "future_work_or_user_decision",
            "evidence": "The current Open3DSG train-side proxy construction does not yield a shortcut-controlled support/contact target.",
            "reason": (
                "A main support/contact p_rel target likely needs independent visual/mesh human labels, multi-view evidence "
                "as audit input, or a different GT source rather than another proxy remapping."
            ),
            "claim_boundary": "not part of the current train-only smoke path unless explicitly restarted",
        },
    ]


def risk_register(summary: dict[str, Any], key_diags: dict[str, Any]) -> list[dict[str, Any]]:
    target_summary = summary["target_summary"]
    return [
        {
            "risk": "target_identifiability_shortcut",
            "severity": "blocking",
            "evidence": (
                f"predicate_x_subject_object_class_pair_visible p_rel majority accuracy "
                f"{key_diags['p_rel_predicate_x_class_pair']['majority_rule_accuracy']:.4f}; "
                f"hidden predicate_class_pair p_rel majority accuracy "
                f"{key_diags['p_rel_hidden_predicate_class_pair']['majority_rule_accuracy']:.4f}"
            ),
            "decision": "block learned smoke",
        },
        {
            "risk": "observability_head_degenerate",
            "severity": "blocking_for_p_obs_q",
            "evidence": f"p_obs counts {target_summary['p_obs_counts']} and Q rows all sufficient.",
            "decision": "do not claim p_obs/Q learning from this target",
        },
        {
            "risk": "generic_endpoint_abstain_shortcut",
            "severity": "diagnostic",
            "evidence": (
                f"generic_endpoint_visible relation-multiclass majority accuracy "
                f"{key_diags['multiclass_generic_endpoint']['majority_rule_accuracy']:.4f}"
            ),
            "decision": "do not use multiclass accept/reject/abstain target as main evidence",
        },
        {
            "risk": "proxy_label_provenance",
            "severity": "blocking_for_paper",
            "evidence": summary["boundary"].get("label_provenance"),
            "decision": "keep as hypothesis diagnostic, not paper evidence",
        },
    ]


def write_report(path: Path, output_summary: dict[str, Any], routes: list[dict[str, Any]], risks: list[dict[str, Any]]) -> None:
    target = output_summary["input_snapshot"]["target_summary"]
    key = output_summary["key_shortcut_diagnostics"]
    lines = [
        "# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Class-Pair Repair Path Decision",
        "",
        "## Status",
        "",
        "```text",
        f"status = {output_summary['status']}",
        f"selected_path = {output_summary['selected_path']}",
        f"validation_errors = {output_summary['validation_errors']}",
        f"next_todo = {output_summary['next_todo']}",
        "```",
        "",
        "## Decision",
        "",
        "Freeze the support/contact visual-mesh class-pair repair artifact as diagnostic-only.",
        "",
        "The artifact is count-viable but not target-identifiable:",
        "",
        "```text",
        f"p_rel/C_e binary rows = {target['p_rel_binary_rows']}",
        f"p_rel/C_e binary counts = {target['p_rel_binary_counts']}",
        f"relation multiclass counts = {target['relation_multiclass_counts']}",
        f"predicate_x_class_pair p_rel majority accuracy = {key['p_rel_predicate_x_class_pair']['majority_rule_accuracy']:.4f}",
        f"hidden predicate_class_pair p_rel majority accuracy = {key['p_rel_hidden_predicate_class_pair']['majority_rule_accuracy']:.4f}",
        f"generic_endpoint_visible multiclass majority accuracy = {key['multiclass_generic_endpoint']['majority_rule_accuracy']:.4f}",
        "```",
        "",
        "## Route Table",
        "",
    ]
    for row in routes:
        lines.extend(
            [
                f"- `{row['route']}`: {row['verdict']}",
                f"  Evidence: {row['evidence']}",
                f"  Reason: {row['reason']}",
                f"  Boundary: {row['claim_boundary']}",
            ]
        )
    lines.extend(["", "## Risk Register", ""])
    for row in risks:
        lines.extend(
            [
                f"- `{row['risk']}`: {row['severity']}",
                f"  Evidence: {row['evidence']}",
                f"  Decision: {row['decision']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only path decision.",
            "- No validation/test usage.",
            "- No learned smoke or model training.",
            "- No new label fill.",
            "- No paper evidence.",
            "- No H001 artifact modification.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = args.ingestion_dir / "summary.json"
    rows_path = args.ingestion_dir / "target_rows.jsonl"
    diag_path = args.ingestion_dir / "shortcut_diagnostics.csv"

    if not summary_path.exists() or not rows_path.exists() or not diag_path.exists():
        validation_errors = [
            {
                "error_type": "missing_input_artifact",
                "summary_exists": summary_path.exists(),
                "target_rows_exists": rows_path.exists(),
                "shortcut_diagnostics_exists": diag_path.exists(),
            }
        ]
        output_summary = {
            "boundary": {
                "h001_artifacts_modified": False,
                "materializes_rows": False,
                "paper_evidence_allowed": False,
                "runs_learned_smoke": False,
                "split": "train_only_path_decision",
                "test_usage": False,
                "trains_new_model": False,
                "validation_usage": False,
            },
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "input_ingestion_summary": rel_path(summary_path),
            "next_todo": EXPECTED_INPUT_NEXT,
            "schema_version": SCHEMA_VERSION,
            "selected_path": "blocked_missing_input_artifact",
            "status": STATUS_ERROR,
            "validation_errors": len(validation_errors),
        }
        write_json(args.output_dir / "summary.json", output_summary)
        write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
        print(json.dumps({k: output_summary[k] for k in ["status", "selected_path", "validation_errors", "next_todo"]}, sort_keys=True))
        return 1

    input_summary = read_json(summary_path)
    target_rows = read_jsonl(rows_path)
    diag_rows = read_csv(diag_path)
    validation_errors = validate_input(input_summary, target_rows, diag_rows)

    key_diags = {
        "p_rel_predicate_x_class_pair": find_diag(
            diag_rows, "p_rel_binary", "predicate_x_subject_object_class_pair_visible"
        ),
        "p_rel_hidden_predicate_class_pair": find_diag(diag_rows, "p_rel_binary", "predicate_class_pair_hidden"),
        "p_rel_subject_label": find_diag(diag_rows, "p_rel_binary", "subject_label"),
        "p_rel_object_label": find_diag(diag_rows, "p_rel_binary", "object_label"),
        "multiclass_generic_endpoint": find_diag(diag_rows, "relation_multiclass", "generic_endpoint_visible"),
    }
    profiles = [
        target_profile(target_rows, "all_rows", None),
        target_profile(target_rows, "non_generic_rows", lambda row: not is_generic_endpoint(row)),
        target_profile(target_rows, "generic_rows", is_generic_endpoint),
    ]

    if validation_errors:
        status = STATUS_ERROR
        selected_path = "blocked_input_errors"
        next_todo = EXPECTED_INPUT_NEXT
        routes: list[dict[str, Any]] = []
        risks: list[dict[str, Any]] = []
    else:
        status = STATUS_READY
        selected_path = SELECTED_PATH
        next_todo = NEXT_TODO
        routes = route_table(input_summary, profiles, key_diags)
        risks = risk_register(input_summary, key_diags)

    output_paths = {
        "input_profile": args.output_dir / "input_profile.json",
        "key_shortcut_diagnostics": args.output_dir / "key_shortcut_diagnostics.json",
        "report": args.output_dir / "report.md",
        "risk_register": args.output_dir / "risk_register.csv",
        "route_decision": args.output_dir / "route_decision.csv",
        "summary": args.output_dir / "summary.json",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }
    output_summary = {
        "boundary": {
            "fills_new_labels": False,
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_path_decision",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_ingestion_summary": rel_path(summary_path),
        "input_snapshot": {
            "status": input_summary.get("status"),
            "selected_path": input_summary.get("selected_path"),
            "target_summary": input_summary.get("target_summary", {}),
        },
        "key_shortcut_diagnostics": key_diags,
        "next_todo": next_todo,
        "output_paths": {name: rel_path(path) for name, path in output_paths.items()},
        "profile_summary": {
            profile["profile"]: {
                "rows": profile["rows"],
                "p_rel_binary_rows": profile["p_rel_binary_rows"],
                "p_rel_counts": profile["p_rel_counts"],
                "relation_multiclass_counts": profile["relation_multiclass_counts"],
            }
            for profile in profiles
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "status": status,
        "validation_errors": len(validation_errors),
    }

    write_json(output_paths["summary"], output_summary)
    write_json(output_paths["input_profile"], profiles)
    write_json(output_paths["key_shortcut_diagnostics"], key_diags)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_csv(output_paths["route_decision"], routes)
    write_csv(output_paths["risk_register"], risks)
    write_report(output_paths["report"], output_summary, routes, risks)

    print(
        json.dumps(
            {
                "status": status,
                "selected_path": selected_path,
                "validation_errors": len(validation_errors),
                "next_todo": next_todo,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 1 if status == STATUS_ERROR else 0


if __name__ == "__main__":
    raise SystemExit(main())
