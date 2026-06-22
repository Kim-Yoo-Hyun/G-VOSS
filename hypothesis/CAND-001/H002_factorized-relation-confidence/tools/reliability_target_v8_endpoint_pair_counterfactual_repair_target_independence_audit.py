#!/usr/bin/env python3
"""Audit H002 v8 repair endpoint-pair counterfactual target independence."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import reliability_target_v8_endpoint_pair_counterfactual_target_independence_audit as base


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_label_ingestion_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_target_independence_audit_codex_proxy_user_requested"

TARGET_SCHEMA_VERSIONS = {
    base.RELIABILITY_MULTICLASS: "h002_reliability_target_v8_endpoint_pair_counterfactual_repair_multiclass_row_v1",
    base.RELIABILITY_BINARY: "h002_reliability_target_v8_endpoint_pair_counterfactual_repair_binary_row_v1",
    base.GEOMETRY_TARGET: "h002_geometry_support_v6_endpoint_pair_counterfactual_repair_binary_row_v1",
    base.USEFULNESS_TARGET: "h002_relation_usefulness_v6_endpoint_pair_counterfactual_repair_binary_row_v1",
}

GROUP_KEY_CATEGORIES = {
    "visible_relation": ["predicate_family", "predicate_label"],
    "visible_object_identity": ["subject_label", "object_label", "subject_object_label_pair_visible"],
    "hidden_sampling_axis": ["semantic_geometry_bucket_hidden", "source_queue_hidden", "rank_band_hidden"],
    "endpoint_pair_control": [
        "exact_endpoint_pair_key_hidden",
        "undirected_endpoint_pair_key_hidden",
        "v8_group_key_hidden",
        "counterfactual_pair_id_hidden",
        "counterfactual_pair_type_hidden",
        "endpoint_pattern_hidden",
        "subject_object_label_pair_hidden",
        "subject_object_family_cell_hidden",
        "structural_pair_hidden",
        "hard_room_surface_pair_hidden",
        "generic_endpoint_pair_hidden",
    ],
    "geometry_alignment": [
        "geometry_status_hidden",
        "h001_verification_status_hidden",
        "label_match_status_hidden",
        "label_geometry_bucket_hidden",
    ],
    "construction_coverage": [
        "evidence_packet_status",
        "packet_gap_decision",
        "primary_gap_decision_hidden",
        "row_gap_decision_hidden",
        "normalized_evidence_status_hidden",
        "packet_status_hidden",
        "asset_packet_source_hidden",
        "packet_source_hidden",
        "replacement_source_hidden",
        "diagnostic_status_hidden",
        "label_readiness_status_hidden",
    ],
    "hidden_machine_hint": ["machine_hint_hidden"],
}

SLICE_SPECS = {
    "original_v8": {
        "balanced_keys": [],
        "reason": "full restored v8 repair endpoint-pair counterfactual target",
        "priority": 99,
    },
    "family_balanced_repair_v8": {
        "balanced_keys": ["predicate_family"],
        "reason": "balanced within predicate family",
        "priority": 1,
    },
    "predicate_balanced_repair_v8": {
        "balanced_keys": ["predicate_label"],
        "reason": "balanced within predicate label",
        "priority": 2,
    },
    "source_queue_balanced_repair_v8": {
        "balanced_keys": ["source_queue_hidden"],
        "reason": "balanced within HL/LH source queue",
        "priority": 3,
    },
    "rank_band_balanced_repair_v8": {
        "balanced_keys": ["rank_band_hidden"],
        "reason": "balanced within semantic rank band",
        "priority": 4,
    },
    "geometry_status_balanced_repair_v8": {
        "balanced_keys": ["geometry_status_hidden"],
        "reason": "balanced within frozen geometry status",
        "priority": 5,
    },
    "label_geometry_bucket_balanced_repair_v8": {
        "balanced_keys": ["label_geometry_bucket_hidden"],
        "reason": "balanced within post-label RGA bucket",
        "priority": 6,
    },
    "subject_label_balanced_repair_v8": {
        "balanced_keys": ["subject_label"],
        "reason": "balanced within visible subject label",
        "priority": 7,
    },
    "object_label_balanced_repair_v8": {
        "balanced_keys": ["object_label"],
        "reason": "balanced within visible object label",
        "priority": 8,
    },
    "endpoint_pattern_balanced_repair_v8": {
        "balanced_keys": ["endpoint_pattern_hidden"],
        "reason": "balanced within endpoint pattern",
        "priority": 9,
    },
    "exact_endpoint_pair_balanced_repair_v8": {
        "balanced_keys": ["exact_endpoint_pair_key_hidden"],
        "reason": "balanced within exact endpoint pair",
        "priority": 10,
    },
    "counterfactual_pair_balanced_repair_v8": {
        "balanced_keys": ["counterfactual_pair_id_hidden"],
        "reason": "balanced within counterfactual predicate pair",
        "priority": 11,
    },
    "subject_object_label_pair_balanced_repair_v8": {
        "balanced_keys": ["subject_object_label_pair_hidden"],
        "reason": "balanced within subject/object label pair",
        "priority": 12,
    },
    "family_bucket_balanced_repair_v8": {
        "balanced_keys": ["predicate_family", "label_geometry_bucket_hidden"],
        "reason": "balanced within predicate family and RGA bucket",
        "priority": 13,
    },
    "family_geometry_status_balanced_repair_v8": {
        "balanced_keys": ["predicate_family", "geometry_status_hidden"],
        "reason": "balanced within predicate family and frozen geometry status",
        "priority": 14,
    },
    "predicate_geometry_status_balanced_repair_v8": {
        "balanced_keys": ["predicate_label", "geometry_status_hidden"],
        "reason": "balanced within predicate label and frozen geometry status",
        "priority": 15,
    },
    "predicate_endpoint_pair_balanced_repair_v8": {
        "balanced_keys": ["predicate_label", "exact_endpoint_pair_key_hidden"],
        "reason": "balanced within predicate and exact endpoint pair",
        "priority": 16,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def patch_base() -> None:
    base.TARGET_SCHEMA_VERSIONS = TARGET_SCHEMA_VERSIONS
    base.GROUP_KEY_CATEGORIES = GROUP_KEY_CATEGORIES
    base.SLICE_SPECS = SLICE_SPECS


def validate_ingestion_summary(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_next = "reliability_target_v8_endpoint_pair_counterfactual_repair_target_independence_audit"
    if summary.get("next_todo") != expected_next:
        errors.append({"error_type": "unexpected_ingestion_next_todo", "expected": expected_next, "value": summary.get("next_todo")})
    expected_status = "h002_reliability_target_v8_repair_label_ingested_with_probe_risk"
    if summary.get("status") != expected_status:
        errors.append({"error_type": "unexpected_ingestion_status", "expected": expected_status, "value": summary.get("status")})
    boundary = summary.get("boundary", {})
    if boundary.get("validation_usage") is not False or boundary.get("test_usage") is not False:
        errors.append(
            {
                "error_type": "ingestion_boundary_uses_validation_or_test",
                "validation_usage": boundary.get("validation_usage"),
                "test_usage": boundary.get("test_usage"),
            }
        )
    if boundary.get("posterior_smoke_allowed") is not False:
        errors.append({"error_type": "ingestion_boundary_posterior_already_allowed", "value": boundary.get("posterior_smoke_allowed")})
    return errors


def choose_top_status(relation_decision: dict[str, Any], validation_errors: list[dict[str, Any]]) -> tuple[str, str, str, bool]:
    if validation_errors:
        return (
            "h002_reliability_target_v8_repair_target_independence_audit_errors",
            "Validation errors remain; do not run posterior smoke.",
            "fix_reliability_target_v8_endpoint_pair_counterfactual_repair_target_independence_audit_errors",
            False,
        )
    if relation_decision["posterior_allowed"]:
        return (
            "h002_reliability_target_v8_repair_target_independence_audit_relation_binary_ready",
            "The repair relation-reliability binary target has a strict controlled slice and may proceed to feature join.",
            "reliability_target_v8_endpoint_pair_counterfactual_repair_source_feature_join",
            True,
        )
    if relation_decision["status"] == "blocked_geometry_control_required":
        return (
            "h002_reliability_target_v8_repair_target_independence_audit_blocked_geometry_control_required",
            "A diagnostic slice clears blocking shortcut risk, but geometry-alignment control risk remains. Keep posterior blocked.",
            "reliability_target_v8_endpoint_pair_counterfactual_repair_target_path_decision",
            False,
        )
    return (
        "h002_reliability_target_v8_repair_target_independence_audit_blocked_shortcut_risk",
        "The repair binary target is class-usable, but target-construction shortcuts remain too predictive. Keep posterior blocked.",
        "reliability_target_v8_endpoint_pair_counterfactual_repair_target_path_decision",
        False,
    )


def write_report(path: Path, summary: dict[str, Any]) -> None:
    relation_types = summary["relation_types"]
    lines = [
        "# H002 V8 Repair Target Independence Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Split: Open3DSG train-only.",
        "- No validation/test rows are used.",
        "- No posterior is trained in this step.",
        "- Hidden metadata is used only after label lock for target-independence auditing.",
        "- Geometry-status alignment is treated as control-required, not as deployable posterior input.",
        "- Multi-view remains audit evidence only.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        summary["decision"],
        "",
        "## Relation Types",
        "",
        "| Family | Rows | Predicate Counts |",
        "| --- | ---: | --- |",
    ]
    for family, item in sorted(relation_types["family_counts"].items()):
        pred_counts = relation_types["predicates_by_family"].get(family, {})
        pred_text = ", ".join(f"`{pred}`={count}" for pred, count in sorted(pred_counts.items()))
        lines.append(f"| `{family}` | {item} | {pred_text} |")
    lines.extend(
        [
            "",
            "## Target Artifacts",
            "",
            "| Target | Rows | Classes | Posterior Allowed | Status |",
            "| --- | ---: | --- | --- | --- |",
        ]
    )
    for target_name, decision in summary["target_decisions"].items():
        original = decision["original"]
        classes = ", ".join(f"`{label}`={count}" for label, count in original["classes"].items())
        lines.append(
            f"| `{target_name}` | {original['rows']} | {classes} | "
            f"`{decision['posterior_allowed']}` | `{decision['status']}` |"
        )
    lines.extend(
        [
            "",
            "## Original Shortcut Risks",
            "",
            "| Target | Category | Key | Majority Acc | Baseline | NMI | Class Range | Reasons |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for target_name, decision in summary["target_decisions"].items():
        original = decision["original"]
        risks = original["top_blocking_risks"] + original["top_control_required_risks"]
        if not risks:
            lines.append(f"| `{target_name}` | none | none | 0.0000 | 0.0000 | 0.0000 | 0.0000 | none |")
        for risk in risks:
            lines.append(
                f"| `{target_name}` | `{risk['category']}` | `{risk['group_key']}` | "
                f"{risk['majority_rule_accuracy']:.4f} | {risk['majority_baseline_accuracy']:.4f} | "
                f"{risk['normalized_mutual_information']:.4f} | {risk['class_rate_range']:.4f} | "
                f"`{','.join(risk['risk_reasons'])}` |"
            )
    lines.extend(
        [
            "",
            "## Controlled Slice Summary",
            "",
            "| Target | Slice | Rows | Min Class | Blocking Risks | Control Risks | Strict | Diagnostic |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for item in sorted(
        summary["slice_summaries"],
        key=lambda row: (
            row["target_name"],
            not row["strict_candidate"],
            not row["diagnostic_candidate"],
            row["priority"],
            -row["rows"],
        ),
    ):
        lines.append(
            f"| `{item['target_name']}` | `{item['slice_name']}` | {item['rows']} | {item['min_class']} | "
            f"{item['blocking_risk_count']} | {item['control_required_risk_count']} | "
            f"`{item['strict_candidate']}` | `{item['diagnostic_candidate']}` |"
        )
    rel = summary["target_decisions"][base.RELIABILITY_BINARY]
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- The repair relation-reliability binary target has `{rel['original']['rows']}` rows and class balance `{rel['original']['classes']}`.",
            "- This confirms the repair fixed the previous count/balance issue enough to run the audit.",
            "- Posterior smoke is allowed only if a strict controlled slice clears blocking and geometry-control risks.",
            "- Geometry-support and usefulness targets are exported as auxiliary diagnostics, not as proof of factorized posterior quality.",
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    patch_base()
    ingestion_dir = base.as_abs(args.ingestion_dir)
    output_dir = base.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    ingestion_summary = base.read_json(ingestion_dir / "summary.json")
    validation_errors = validate_ingestion_summary(ingestion_summary)
    input_paths: dict[str, str] = {"ingestion_summary": base.rel_path(ingestion_dir / "summary.json")}
    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "target_risk_summary": output_dir / "target_risk_summary.csv",
        "group_risk_table": output_dir / "group_risk_table.csv",
        "slice_summaries": output_dir / "slice_summaries.csv",
        "validation_errors": output_dir / "validation_errors.jsonl",
        "target_slices": output_dir / "target_slices",
    }

    all_slice_summaries: list[dict[str, Any]] = []
    all_group_risks: list[dict[str, Any]] = []
    target_decisions: dict[str, Any] = {}
    target_counts: dict[str, Any] = {}
    relation_type_source_rows: list[dict[str, Any]] = []

    for target_name, filename in base.TARGET_INPUTS.items():
        input_path = ingestion_dir / filename
        input_paths[target_name] = base.rel_path(input_path)
        rows = base.read_jsonl(input_path)
        if target_name == base.RELIABILITY_MULTICLASS:
            relation_type_source_rows = rows
        errors = base.validate_target_rows(target_name, rows)
        validation_errors.extend(errors)
        target_counts[target_name] = base.class_count_summary(rows)
        slice_summaries: list[dict[str, Any]] = []
        for slice_name, spec in SLICE_SPECS.items():
            slice_rows = base.balanced_slice(rows, spec["balanced_keys"])
            slice_path = output_paths["target_slices"] / target_name / f"{slice_name}.jsonl"
            base.write_jsonl(slice_path, slice_rows)
            summary, group_risks = base.slice_summary(target_name, slice_name, spec, slice_rows, slice_path)
            slice_summaries.append(summary)
            all_slice_summaries.append(summary)
            for risk in group_risks:
                all_group_risks.append(
                    {
                        "target_name": risk["target_name"],
                        "slice_name": slice_name,
                        "category": risk["category"],
                        "group_key": risk["group_key"],
                        "rows": risk["rows"],
                        "groups": risk["groups"],
                        "majority_baseline_accuracy": risk["majority_baseline_accuracy"],
                        "majority_rule_accuracy": risk["majority_rule_accuracy"],
                        "majority_excess_over_baseline": risk["majority_excess_over_baseline"],
                        "normalized_mutual_information": risk["normalized_mutual_information"],
                        "class_rate_range": risk["class_rate_range"],
                        "large_group_max_purity": risk["large_group_max_purity"],
                        "large_group_key": risk["large_group_key"],
                        "large_group_rows": risk["large_group_rows"],
                        "risk_level": risk["risk_level"],
                        "risk_reasons": "|".join(risk["risk_reasons"]),
                    }
                )
        target_decisions[target_name] = base.per_target_decision(target_name, slice_summaries, errors)

    family_counts = Counter(row.get("predicate_family") for row in relation_type_source_rows)
    predicate_counts = Counter(row.get("predicate_label") for row in relation_type_source_rows)
    predicates_by_family: dict[str, Counter[str]] = defaultdict(Counter)
    for row in relation_type_source_rows:
        predicates_by_family[str(row.get("predicate_family"))][str(row.get("predicate_label"))] += 1

    relation_decision = target_decisions[base.RELIABILITY_BINARY]
    status, decision, next_todo, posterior_allowed = choose_top_status(relation_decision, validation_errors)

    summary = {
        "schema_version": "h002_reliability_target_v8_repair_target_independence_audit_summary_v1",
        "status": status,
        "created_at": created_at,
        "input_paths": input_paths,
        "output_dir": base.rel_path(output_dir),
        "output_paths": {key: base.rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "posterior_claim_allowed": posterior_allowed,
            "multi_view_as_model_input": False,
            "hidden_metadata_used_for_audit_only": True,
            "geometry_status_is_control_axis_not_main_score": True,
            "target_labels_source": "codex_proxy_user_requested_treat_as_human_confirmed_for_hypothesis_stage",
        },
        "risk_thresholds": {
            "normalized_mutual_information": base.RISK_NMI_THRESHOLD,
            "majority_excess_over_baseline": base.RISK_MAJORITY_EXCESS_THRESHOLD,
            "majority_rule_accuracy": base.RISK_MAJORITY_ACC_THRESHOLD,
            "class_rate_range": base.RISK_CLASS_RATE_RANGE_THRESHOLD,
            "large_group_rows": base.RISK_LARGE_GROUP_ROWS,
            "large_group_purity": base.RISK_LARGE_GROUP_PURITY,
        },
        "relation_types": {
            "family_counts": dict(sorted(family_counts.items())),
            "predicate_counts": dict(sorted(predicate_counts.items())),
            "predicates_by_family": {family: dict(sorted(counts.items())) for family, counts in sorted(predicates_by_family.items())},
        },
        "ingestion_status": ingestion_summary.get("status"),
        "target_counts": target_counts,
        "target_decisions": target_decisions,
        "slice_summaries": all_slice_summaries,
        "validation_errors": len(validation_errors),
        "decision": decision,
        "next_todo": next_todo,
    }

    target_risk_rows: list[dict[str, Any]] = []
    for target_name, target_decision in target_decisions.items():
        original = target_decision["original"]
        for risk in original["top_blocking_risks"] + original["top_control_required_risks"]:
            target_risk_rows.append(
                {
                    "target_name": target_name,
                    "category": risk["category"],
                    "group_key": risk["group_key"],
                    "risk_level": risk["risk_level"],
                    "risk_reasons": "|".join(risk["risk_reasons"]),
                    "majority_rule_accuracy": risk["majority_rule_accuracy"],
                    "majority_baseline_accuracy": risk["majority_baseline_accuracy"],
                    "normalized_mutual_information": risk["normalized_mutual_information"],
                    "class_rate_range": risk["class_rate_range"],
                }
            )

    slice_csv_rows = [
        {
            "target_name": item["target_name"],
            "slice_name": item["slice_name"],
            "rows": item["rows"],
            "min_class": item["min_class"],
            "classes": json.dumps(item["classes"], sort_keys=True),
            "blocking_risk_count": item["blocking_risk_count"],
            "control_required_risk_count": item["control_required_risk_count"],
            "strict_size_ready": item["strict_size_ready"],
            "diagnostic_size_ready": item["diagnostic_size_ready"],
            "strict_candidate": item["strict_candidate"],
            "diagnostic_candidate": item["diagnostic_candidate"],
            "construction_only_candidate": item["construction_only_candidate"],
            "balanced_keys": "|".join(item["balanced_keys"]),
            "path": item["path"],
        }
        for item in all_slice_summaries
    ]

    base.write_json(output_paths["summary"], summary)
    base.write_csv(output_paths["target_risk_summary"], target_risk_rows)
    base.write_csv(output_paths["group_risk_table"], all_group_risks)
    base.write_csv(output_paths["slice_summaries"], slice_csv_rows)
    base.write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    rel = summary["target_decisions"][base.RELIABILITY_BINARY]
    original = rel["original"]
    print(f"status={summary['status']}")
    print(f"relation_binary_rows={original['rows']} classes={original['classes']}")
    print(f"relation_binary_status={rel['status']} posterior_allowed={rel['posterior_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"relation_types={summary['relation_types']['family_counts']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
