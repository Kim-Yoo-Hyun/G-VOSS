#!/usr/bin/env python3
"""Write the H002 compatibility dataset v2 sanitized-view smoke plan."""

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

DEFAULT_AUDIT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_schema_shortcut_audit"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_sanitized_view_smoke_plan"

EXPECTED_AUDIT_STATUS = "h002_compatibility_dataset_v2_schema_shortcut_audit_requires_sanitized_view"
EXPECTED_AUDIT_NEXT = "compatibility_dataset_v2_sanitized_view_smoke_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v2_sanitized_view_smoke_plan_v1"
SMOKE_READY_SCHEMA = "h002_compatibility_dataset_v2_smoke_ready_view_v1"
STATUS_READY = "h002_compatibility_dataset_v2_sanitized_view_smoke_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v2_sanitized_view_smoke_plan_input_errors"
NEXT_TODO = "compatibility_dataset_v2_sanitized_view_smoke_runner"

BLOCKED_FIELDS = [
    "row_role",
    "counterfactual_axis.counterfactual_type",
    "hidden_control",
    "hidden_control.generated",
    "hidden_control.counterfactual_type",
    "G_e.geometry_source",
    "Q_e.coverage_features.generated_counterfactual",
    "Q_e.evidence_conflict_flag",
    "geometry_status_baseline",
    "relation_source",
    "audit_reference",
    "Z_e.source_score_inherited_for_counterfactual",
    "row_id as feature",
    "group_id as feature",
]

T_FIELDS = [
    "predicate_label",
    "predicate_text",
    "relation_family",
    "subject_label",
    "object_label",
    "subject_object_text",
]

Z_SAFE_FIELDS = [
    "source_id",
    "source_score_available",
    "source_score_raw",
    "source_score_normalized",
    "source_rank",
    "source_rank_band",
]

Q_SAFE_COVERAGE_FIELDS = [
    "coverage_has_raw_witness",
    "raw_feature_available_ratio",
    "raw_witness_missing_flag",
]

Q_SAFE_FIELDS = [
    "asset_tier",
    "missing_geometry_flag",
    "low_coverage_flag",
    "unsupported_family_flag",
    "raw_feature_missing_count",
    "geometry_available",
    "geometry_checkable",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def safe_label(row: dict[str, Any]) -> int:
    return int(row.get("y_compatibility"))


def value_key(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None or value == "":
        return "missing"
    return str(value)


def majority_accuracy(rows: list[dict[str, Any]], value_fn: Callable[[dict[str, Any]], Any]) -> float:
    groups: dict[str, Counter[int]] = defaultdict(Counter)
    for row in rows:
        groups[value_key(value_fn(row))][safe_label(row)] += 1
    return sum(max(counter.values()) for counter in groups.values()) / len(rows) if rows else 0.0


def pick_fields(source: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    return {field: source.get(field) for field in fields}


def make_q_safe(row: dict[str, Any]) -> dict[str, Any]:
    q = row.get("Q_e_sanitized", {})
    coverage = q.get("coverage_features", {})
    return {
        "coverage_features": pick_fields(coverage, Q_SAFE_COVERAGE_FIELDS),
        **pick_fields(q, Q_SAFE_FIELDS),
    }


def make_smoke_ready_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        t_safe = pick_fields(row.get("T_e", {}), T_FIELDS)
        z_safe = pick_fields(row.get("Z_e", {}), Z_SAFE_FIELDS)
        g_safe = dict(row.get("G_e_numeric", {}).get("geometry_features", {}))
        q_safe = make_q_safe(row)
        out.append(
            {
                "schema_version": SMOKE_READY_SCHEMA,
                "row_id": row.get("row_id"),
                "group_id": row.get("group_id"),
                "split": row.get("split"),
                "y_compatibility": safe_label(row),
                "T_e": t_safe,
                "Z_e_safe": z_safe,
                "G_e_numeric": g_safe,
                "Q_e_safe": q_safe,
                "model_views": {
                    "M1_source_only_Z_safe": {"Z_e_safe": z_safe},
                    "M2_semantic_only_T": {"T_e": t_safe},
                    "M3_semantic_source_TZ_safe": {"T_e": t_safe, "Z_e_safe": z_safe},
                    "M4_geometry_numeric_G": {"G_e_numeric": g_safe},
                    "M5_compatibility_TG_numeric": {"T_e": t_safe, "G_e_numeric": g_safe},
                    "M6_factorized_sanitized_TZGQ": {
                        "T_e": t_safe,
                        "Z_e_safe": z_safe,
                        "G_e_numeric": g_safe,
                        "Q_e_safe": q_safe,
                    },
                    "S1_predicate_family_shortcut": {
                        "predicate_label": t_safe.get("predicate_label"),
                        "relation_family": t_safe.get("relation_family"),
                    },
                    "S2_source_score_rank_shortcut": {
                        "source_score_normalized": z_safe.get("source_score_normalized"),
                        "source_rank": z_safe.get("source_rank"),
                        "source_rank_band": z_safe.get("source_rank_band"),
                    },
                    "S3_object_label_pair_shortcut": {
                        "subject_label": t_safe.get("subject_label"),
                        "object_label": t_safe.get("object_label"),
                        "subject_object_text": t_safe.get("subject_object_text"),
                    },
                },
            }
        )
    return out


def count_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_label = Counter(safe_label(row) for row in rows)
    by_group = defaultdict(list)
    for row in rows:
        by_group[row.get("group_id")].append(safe_label(row))
    complete_groups = sum(1 for labels in by_group.values() if sorted(labels) == [0, 1])
    return {
        "rows": len(rows),
        "positive": by_label[1],
        "negative": by_label[0],
        "groups": len(by_group),
        "paired_groups_with_one_positive_one_negative": complete_groups,
    }


def field_probe_rows(rows: list[dict[str, Any]], smoke_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    probes = [
        {
            "field": "pre_plan_sanitized.Z_e.source_score_inherited_for_counterfactual",
            "location": "input_sanitized_view",
            "allowed_in_smoke_ready_view": False,
            "accuracy": majority_accuracy(rows, lambda row: row.get("Z_e", {}).get("source_score_inherited_for_counterfactual")),
            "decision": "blocked",
        },
        {
            "field": "T_e.predicate_label",
            "location": "smoke_ready_view",
            "allowed_in_smoke_ready_view": True,
            "accuracy": majority_accuracy(smoke_rows, lambda row: row.get("T_e", {}).get("predicate_label")),
            "decision": "allowed_controlled_semantic_content",
        },
        {
            "field": "T_e.relation_family",
            "location": "smoke_ready_view",
            "allowed_in_smoke_ready_view": True,
            "accuracy": majority_accuracy(smoke_rows, lambda row: row.get("T_e", {}).get("relation_family")),
            "decision": "allowed_controlled_semantic_content",
        },
        {
            "field": "Z_e_safe.source_rank_band",
            "location": "smoke_ready_view",
            "allowed_in_smoke_ready_view": True,
            "accuracy": majority_accuracy(smoke_rows, lambda row: row.get("Z_e_safe", {}).get("source_rank_band")),
            "decision": "allowed_source_control",
        },
        {
            "field": "Z_e_safe.source_id",
            "location": "smoke_ready_view",
            "allowed_in_smoke_ready_view": True,
            "accuracy": majority_accuracy(smoke_rows, lambda row: row.get("Z_e_safe", {}).get("source_id")),
            "decision": "allowed_source_control",
        },
        {
            "field": "Q_e_safe.coverage_features.raw_feature_available_ratio",
            "location": "smoke_ready_view",
            "allowed_in_smoke_ready_view": True,
            "accuracy": majority_accuracy(
                smoke_rows,
                lambda row: row.get("Q_e_safe", {}).get("coverage_features", {}).get("raw_feature_available_ratio"),
            ),
            "decision": "allowed_but_expected_constant_in_v2",
        },
    ]
    for probe in probes:
        probe["accuracy"] = round(float(probe["accuracy"]), 6)
    return probes


def model_view_rows() -> list[dict[str, Any]]:
    return [
        {
            "model": "M0_intercept",
            "input_blocks": "none",
            "purpose": "class-balance sanity baseline",
            "primary": False,
        },
        {
            "model": "M1_source_only_Z_safe",
            "input_blocks": "Z_e_safe",
            "purpose": "tests whether source score/rank alone solves compatibility",
            "primary": False,
        },
        {
            "model": "M2_semantic_only_T",
            "input_blocks": "T_e",
            "purpose": "tests semantic/object prior shortcut without source or geometry",
            "primary": False,
        },
        {
            "model": "M3_semantic_source_TZ_safe",
            "input_blocks": "T_e + Z_e_safe",
            "purpose": "tests semantic plus source shortcut without geometry",
            "primary": False,
        },
        {
            "model": "M4_geometry_numeric_G",
            "input_blocks": "G_e_numeric",
            "purpose": "tests predicate-independent geometry signal",
            "primary": False,
        },
        {
            "model": "M5_compatibility_TG_numeric",
            "input_blocks": "T_e + G_e_numeric",
            "purpose": "primary C_e smoke: predicate-geometry compatibility without Z_e",
            "primary": True,
        },
        {
            "model": "M6_factorized_sanitized_TZGQ",
            "input_blocks": "T_e + Z_e_safe + G_e_numeric + Q_e_safe",
            "purpose": "checks whether final factorized representation improves without construction leakage",
            "primary": False,
        },
        {
            "model": "S1_predicate_family_shortcut",
            "input_blocks": "predicate_label + relation_family",
            "purpose": "semantic shortcut probe",
            "primary": False,
        },
        {
            "model": "S2_source_score_rank_shortcut",
            "input_blocks": "source_score_normalized + source_rank + source_rank_band",
            "purpose": "source confidence shortcut probe",
            "primary": False,
        },
        {
            "model": "S3_object_label_pair_shortcut",
            "input_blocks": "subject_label + object_label + subject_object_text",
            "purpose": "object-pair semantic prior probe",
            "primary": False,
        },
        {
            "model": "C1_shuffled_G_within_family_control",
            "input_blocks": "T_e + shuffled G_e_numeric within relation family",
            "purpose": "negative control: verifies M5 is using aligned geometry",
            "primary": False,
        },
        {
            "model": "C2_wrong_T_same_G_control",
            "input_blocks": "wrong predicate T_e + same G_e_numeric",
            "purpose": "negative control: verifies predicate conditioning matters",
            "primary": False,
        },
    ]


def smoke_plan() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "task": {
            "name": "Task A compatibility only",
            "target": "y_compatibility: positive vs generated counterfactual negative",
            "secondary_tasks": [
                "No p_obs training target in this v2 smoke. Q_e_safe is covariate/ablation only.",
                "No p_rel human reliability target in this v2 smoke.",
            ],
        },
        "input_contract": {
            "input_file": "smoke_ready_view.jsonl",
            "row_count": 400,
            "positive": 200,
            "negative": 200,
            "group_split_key": "group_id",
            "forbidden_as_features": BLOCKED_FIELDS,
            "allowed_blocks": {
                "T_e": T_FIELDS,
                "Z_e_safe": Z_SAFE_FIELDS,
                "G_e_numeric": "geometry_features only",
                "Q_e_safe.coverage_features": Q_SAFE_COVERAGE_FIELDS,
                "Q_e_safe": Q_SAFE_FIELDS,
            },
        },
        "split_policy": {
            "split": "train_internal_grouped_cv",
            "folds": 5,
            "group_key": "group_id",
            "stratification": "group-level because each group should contain one positive and one negative",
            "validation_test_usage": False,
        },
        "metrics": [
            "AUROC",
            "AUPRC",
            "accuracy",
            "balanced_accuracy",
            "paired anchor-vs-counterfactual score drop",
            "family-specific AUROC/AUPRC",
            "counterfactual-type slice metrics",
        ],
        "gates": {
            "data_gate": [
                "validation_errors == 0",
                "rows == 400",
                "positive == 200 and negative == 200",
                "paired_groups_with_one_positive_one_negative == 200",
                "no blocked field appears inside model_views",
            ],
            "leakage_gate": [
                "Z_e.source_score_inherited_for_counterfactual must be absent",
                "raw construction metadata must not be read by feature extractors",
                "row_id/group_id can be used only for bookkeeping/splitting",
            ],
            "compatibility_gate": [
                "M5_compatibility_TG_numeric should beat M1/M2/M3 shortcut baselines",
                "M5 should degrade under shuffled-G and wrong-T controls",
                "family-specific results must be reported for support_contact and relative_vertical",
            ],
            "failure_actions": [
                "If M2 or S3 matches M5, target remains semantic-prior dominated.",
                "If M4 matches M5, predicate conditioning is not adding evidence.",
                "If C1 does not degrade, aligned geometry is not being used.",
                "If C2 does not degrade, predicate semantics are not being used.",
            ],
        },
        "paper_boundary": {
            "paper_evidence_allowed": False,
            "hypothesis_stage_only": True,
            "docker_required_before_paper_promotion": True,
        },
    }


def blocked_field_rows() -> list[dict[str, Any]]:
    return [
        {"field": field, "allowed_in_smoke_ready_view": False, "reason": "construction metadata or bookkeeping only"}
        for field in BLOCKED_FIELDS
    ]


def validation_errors(audit_summary: dict[str, Any], rows: list[dict[str, Any]], smoke_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if audit_summary.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": audit_summary.get("status")})
    if audit_summary.get("next_todo") != EXPECTED_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_audit_next", "actual": audit_summary.get("next_todo")})
    if audit_summary.get("validation_errors") != 0:
        errors.append({"error_type": "audit_validation_errors", "actual": audit_summary.get("validation_errors")})
    if audit_summary.get("sanitized_view_written") is not True:
        errors.append({"error_type": "missing_sanitized_view_flag"})
    counts = count_summary(smoke_rows)
    if counts["rows"] != 400 or counts["positive"] != 200 or counts["negative"] != 200:
        errors.append({"error_type": "unexpected_smoke_ready_counts", **counts})
    if counts["paired_groups_with_one_positive_one_negative"] != 200:
        errors.append({"error_type": "unexpected_group_pairing", **counts})
    for row in smoke_rows:
        row_id = row.get("row_id")
        z_keys = set(row.get("Z_e_safe", {}))
        if "source_score_inherited_for_counterfactual" in z_keys:
            errors.append({"error_type": "inherited_counterfactual_flag_in_Z_e_safe", "row_id": row_id})
        for view_name, view in row.get("model_views", {}).items():
            text = json.dumps(view, ensure_ascii=False)
            for blocked in [
                "source_score_inherited_for_counterfactual",
                "generated_counterfactual",
                "evidence_conflict_flag",
                "geometry_source",
                "counterfactual_type",
                "row_role",
                "relation_source",
                "geometry_status_baseline",
                "hidden_control",
            ]:
                if blocked in text:
                    errors.append({"error_type": "blocked_token_in_model_view", "row_id": row_id, "view": view_name, "token": blocked})
    if len(rows) != len(smoke_rows):
        errors.append({"error_type": "row_count_changed_during_projection", "input": len(rows), "output": len(smoke_rows)})
    return errors


def write_report(path: Path, summary: dict[str, Any], field_probes: list[dict[str, Any]]) -> None:
    lines = [
        "# Compatibility Dataset V2 Sanitized View Smoke Plan",
        "",
        "Artifact root:",
        "",
        "```text",
        "artifacts/compatibility_dataset_v2_sanitized_view_smoke_plan/",
        "```",
        "",
        "Status:",
        "",
        "```text",
        f"status = {summary['status']}",
        f"rows = {summary['counts']['rows']}",
        f"compatibility positive / negative = {summary['counts']['positive']} / {summary['counts']['negative']}",
        f"paired groups = {summary['counts']['paired_groups_with_one_positive_one_negative']}",
        f"validation_errors = {summary['validation_errors']}",
        f"smoke_ready_view_written = {str(summary['smoke_ready_view_written']).lower()}",
        f"learned_smoke_executed = {str(summary['learned_smoke_executed']).lower()}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Main Decision",
        "",
        "The next learned smoke must not use the raw sanitized view directly. The field",
        "`Z_e.source_score_inherited_for_counterfactual` is also a perfect generated-negative",
        "shortcut, so this plan writes a stricter `smoke_ready_view.jsonl`.",
        "",
        "Allowed model blocks:",
        "",
        "```text",
        "T_e",
        "Z_e_safe",
        "G_e_numeric",
        "Q_e_safe",
        "```",
        "",
        "Blocked construction fields include `row_role`, `counterfactual_type`,",
        "`G_e.geometry_source`, `Q_e.generated_counterfactual`, `Q_e.evidence_conflict_flag`,",
        "`relation_source`, `geometry_status_baseline`, and",
        "`Z_e.source_score_inherited_for_counterfactual`.",
        "",
        "## Field Probes",
        "",
        "| Field | Location | Allowed | Accuracy | Decision |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for probe in field_probes:
        lines.append(
            f"| {probe['field']} | {probe['location']} | {str(probe['allowed_in_smoke_ready_view']).lower()} | "
            f"{float(probe['accuracy']):.3f} | {probe['decision']} |"
        )
    lines.extend(
        [
            "",
            "## Planned Models",
            "",
            "- `M1_source_only_Z_safe`",
            "- `M2_semantic_only_T`",
            "- `M3_semantic_source_TZ_safe`",
            "- `M4_geometry_numeric_G`",
            "- `M5_compatibility_TG_numeric` as the primary `C_e` smoke",
            "- `M6_factorized_sanitized_TZGQ`",
            "- shortcut controls `S1`/`S2`/`S3`",
            "- corruption controls `C1` shuffled geometry and `C2` wrong predicate",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    audit_summary = read_json(args.audit_dir / "summary.json")
    rows = read_jsonl(args.audit_dir / "sanitized_model_view.jsonl")
    smoke_rows = make_smoke_ready_rows(rows)
    field_probes = field_probe_rows(rows, smoke_rows)
    errors = validation_errors(audit_summary, rows, smoke_rows)
    status = STATUS_READY if not errors else STATUS_ERRORS

    write_jsonl(args.output_dir / "smoke_ready_view.jsonl", smoke_rows)
    write_json(args.output_dir / "smoke_plan.json", smoke_plan())
    write_csv(args.output_dir / "model_views.csv", model_view_rows())
    write_csv(args.output_dir / "blocked_fields.csv", blocked_field_rows())
    write_csv(args.output_dir / "field_probe.csv", field_probes)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": NEXT_TODO,
        "audit_root": rel_path(args.audit_dir),
        "output_root": rel_path(args.output_dir),
        "counts": count_summary(smoke_rows),
        "validation_errors": len(errors),
        "input_sanitized_rows": len(rows),
        "smoke_ready_view_written": True,
        "learned_smoke_executed": False,
        "smoke_runner_implementation_allowed": not errors,
        "paper_evidence_allowed": False,
        "blocked_after_audit": ["Z_e.source_score_inherited_for_counterfactual"],
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "smoke_plan": rel_path(args.output_dir / "smoke_plan.json"),
            "smoke_ready_view": rel_path(args.output_dir / "smoke_ready_view.jsonl"),
            "model_views": rel_path(args.output_dir / "model_views.csv"),
            "blocked_fields": rel_path(args.output_dir / "blocked_fields.csv"),
            "field_probe": rel_path(args.output_dir / "field_probe.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "boundary": {
            "split": "train_only_smoke_plan",
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "raw_construction_metadata_promoted": False,
        },
    }
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, field_probes)


if __name__ == "__main__":
    main()
