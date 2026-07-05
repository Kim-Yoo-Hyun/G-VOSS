#!/usr/bin/env python3
"""Freeze the hypothesis-stage claim boundary after revised-factor controls."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_SMOKE_SUMMARY = RGA_ROOT / "independent_revised_factor_smoke_codex_ver/summary.json"
DEFAULT_ERROR_SUMMARY = RGA_ROOT / "independent_revised_factor_error_analysis_codex_ver/summary.json"
DEFAULT_SHORTCUT_SUMMARY = RGA_ROOT / "independent_revised_factor_shortcut_controls_codex_ver/summary.json"
DEFAULT_SHORTCUT_COMPARISONS = RGA_ROOT / "independent_revised_factor_shortcut_controls_codex_ver/control_comparisons.csv"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_revised_factor_claim_boundary_codex_ver"

SOURCE_VIEW = "D4_coverage_uncertainty_shrinkage"
NO_TYPED_VIEW = "D4_no_typed_family_interaction"
GLOBAL_SHUFFLE_VIEW = "D4_raw_witness_shuffle_global"
WITHIN_FAMILY_SHUFFLE_VIEW = "D4_raw_witness_shuffle_within_family"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-summary", type=Path, default=DEFAULT_SMOKE_SUMMARY)
    parser.add_argument("--error-summary", type=Path, default=DEFAULT_ERROR_SUMMARY)
    parser.add_argument("--shortcut-summary", type=Path, default=DEFAULT_SHORTCUT_SUMMARY)
    parser.add_argument("--shortcut-comparisons", type=Path, default=DEFAULT_SHORTCUT_COMPARISONS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path | None) -> str | None:
    if path is None:
        return None
    path = smoke.as_abs(path)
    try:
        return str(path.relative_to(smoke.REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with smoke.as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_comparisons(path: Path) -> list[dict[str, Any]]:
    rows = []
    with smoke.as_abs(path).open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            parsed = dict(row)
            for key, value in row.items():
                if key.startswith("delta_"):
                    parsed[key] = float(value) if value not in {"", "None"} else None
            rows.append(parsed)
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def comparison_lookup(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(str(row["setting"]), str(row["left"])): row for row in rows}


def metric_item(rows: list[dict[str, Any]], setting: str, view: str) -> dict[str, Any]:
    row = comparison_lookup(rows)[(setting, view)]
    return {
        "setting": setting,
        "view": view,
        "delta_auprc": row["delta_auprc"],
        "delta_brier": row["delta_brier"],
        "delta_auroc": row["delta_auroc"],
        "delta_accuracy_at_0_5": row["delta_accuracy_at_0_5"],
    }


def build_claim_table(comparisons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = [
        ("support_contact_only", SOURCE_VIEW, "main_scope_positive_evidence"),
        ("relative_vertical_only", SOURCE_VIEW, "main_scope_positive_evidence"),
        ("support_vertical_only", SOURCE_VIEW, "combined_main_scope_positive_evidence"),
        ("all_families", SOURCE_VIEW, "global_positive_but_contains_proximity"),
        ("proximity_only", SOURCE_VIEW, "excluded_failure_slice"),
        ("all_families", GLOBAL_SHUFFLE_VIEW, "negative_shuffle_control"),
        ("all_families", WITHIN_FAMILY_SHUFFLE_VIEW, "within_family_shuffle_control"),
        ("support_vertical_only", GLOBAL_SHUFFLE_VIEW, "scoped_negative_shuffle_control"),
        ("support_vertical_only", WITHIN_FAMILY_SHUFFLE_VIEW, "scoped_within_family_shuffle_control"),
        ("all_families", NO_TYPED_VIEW, "method_simplification_ablation"),
        ("support_vertical_only", NO_TYPED_VIEW, "scoped_method_simplification_ablation"),
    ]
    return [
        {
            "role": role,
            **metric_item(comparisons, setting, view),
        }
        for setting, view, role in items
    ]


def make_decision(claim_table: list[dict[str, Any]], shortcut_summary: dict[str, Any]) -> dict[str, Any]:
    by_setting_view = {(row["setting"], row["view"]): row for row in claim_table}
    by_role = {row["role"]: row for row in claim_table if row["role"] != "main_scope_positive_evidence"}
    support_delta = by_setting_view[("support_contact_only", SOURCE_VIEW)]["delta_auprc"]
    vertical_delta = by_setting_view[("relative_vertical_only", SOURCE_VIEW)]["delta_auprc"]
    scoped_delta = by_role["combined_main_scope_positive_evidence"]["delta_auprc"]
    proximity_delta = by_role["excluded_failure_slice"]["delta_auprc"]
    global_shuffle_delta = by_role["negative_shuffle_control"]["delta_auprc"]
    within_shuffle_delta = by_role["within_family_shuffle_control"]["delta_auprc"]
    no_typed_delta = by_role["method_simplification_ablation"]["delta_auprc"]
    original_delta = by_role["global_positive_but_contains_proximity"]["delta_auprc"]

    diagnoses = [
        "main_scope_support_contact_positive" if support_delta > 0 else "main_scope_support_contact_not_positive",
        "main_scope_relative_vertical_positive" if vertical_delta > 0 else "main_scope_relative_vertical_not_positive",
        "combined_support_vertical_positive" if scoped_delta > 0 else "combined_support_vertical_not_positive",
        "proximity_excluded_from_main_claim" if proximity_delta < 0 else "proximity_requires_separate_evidence",
        "raw_alignment_control_supports_claim" if global_shuffle_delta < 0 and within_shuffle_delta < original_delta * 0.25 else "raw_alignment_control_weak",
        "typed_interaction_not_final_method" if no_typed_delta > 0 else "typed_interaction_required_by_current_evidence",
    ]
    return {
        "status": "claim_boundary_ready",
        "selected_claim_scope": [
            "support_contact",
            "relative_vertical",
        ],
        "excluded_from_main_claim": [
            "proximity",
            "unsupported_relation_families",
            "multi_view_input",
        ],
        "method_boundary": {
            "core": "RGA-scoped raw-witness residual reliability layer",
            "not_core_yet": "D4 typed family interaction as final combiner",
            "deferred": "generic high-capacity posterior combiner",
        },
        "diagnoses": diagnoses,
        "key_numbers": {
            "support_contact_d_auprc": support_delta,
            "relative_vertical_d_auprc": vertical_delta,
            "support_vertical_d_auprc": scoped_delta,
            "proximity_d_auprc": proximity_delta,
            "global_original_d_auprc": original_delta,
            "global_raw_shuffle_d_auprc": global_shuffle_delta,
            "global_within_family_shuffle_d_auprc": within_shuffle_delta,
            "global_no_typed_d_auprc": no_typed_delta,
            "global_raw_shuffle_retention": shortcut_summary["decision"]["retention_ratios"][
                "global_raw_shuffle_vs_original_auprc_delta"
            ],
            "within_family_raw_shuffle_retention": shortcut_summary["decision"]["retention_ratios"][
                "within_family_raw_shuffle_vs_original_auprc_delta"
            ],
        },
        "allowed_claims": [
            "RGA separates semantic score, geometry validity, coverage, uncertainty, and label/audit evidence at relation-edge level.",
            "Train-only controlled evidence suggests raw-witness residual factorization is promising for support_contact and relative_vertical.",
            "The positive revised-factor signal is not explained by predicate-family categorical shortcut alone.",
            "Raw-witness alignment matters because shuffling witness blocks removes or reverses most of the gain.",
        ],
        "blocked_claims": [
            "H002 posterior is a paper-level performance improvement.",
            "Proximity is solved by the current reliability posterior.",
            "Typed family interaction is the final method design.",
            "Codex bootstrap labels are human-confirmed labels.",
            "Validation/test generalization is established.",
            "Multi-view evidence is a deployable posterior input.",
        ],
        "next_todo": "full_train_independent_support_vertical_audit_packet",
    }


def write_report(path: Path, summary: dict[str, Any], claim_table: list[dict[str, Any]]) -> None:
    decision = summary["decision"]
    lines = [
        "# H002 Full-Train Independent Revised Factor Claim Boundary",
        "",
        "## Decision",
        "",
        f"- Status: `{decision['status']}`",
        f"- Selected scope: `{', '.join(decision['selected_claim_scope'])}`",
        f"- Next TODO: `{decision['next_todo']}`",
        "",
        "## Claim Table",
        "",
        "| Role | Setting | View | dAUPRC vs SG | dBrier vs SG |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for row in claim_table:
        lines.append(
            f"| `{row['role']}` | `{row['setting']}` | `{row['view']}` | "
            f"{row['delta_auprc']:+.4f} | {row['delta_brier']:+.4f} |"
        )
    lines.extend(
        [
            "",
            "## Allowed Claims",
            "",
        ]
    )
    for claim in decision["allowed_claims"]:
        lines.append(f"- {claim}")
    lines.extend(
        [
            "",
            "## Blocked Claims",
            "",
        ]
    )
    for claim in decision["blocked_claims"]:
        lines.append(f"- {claim}")
    lines.extend(
        [
            "",
            "## Method Boundary",
            "",
            f"- Core: `{decision['method_boundary']['core']}`",
            f"- Not core yet: `{decision['method_boundary']['not_core_yet']}`",
            f"- Deferred: `{decision['method_boundary']['deferred']}`",
            "",
            "## Diagnostics",
            "",
        ]
    )
    for diagnosis in decision["diagnoses"]:
        lines.append(f"- `{diagnosis}`")
    lines.extend(
        [
            "",
            "## Output Files",
            "",
            "```text",
            summary["output_paths"]["summary_json"],
            summary["output_paths"]["report_md"],
            summary["output_paths"]["claim_table_csv"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    smoke_summary = read_json(args.smoke_summary)
    error_summary = read_json(args.error_summary)
    shortcut_summary = read_json(args.shortcut_summary)
    comparisons = read_comparisons(args.shortcut_comparisons)
    claim_table = build_claim_table(comparisons)
    decision = make_decision(claim_table, shortcut_summary)

    output_dir = smoke.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "summary_json": output_dir / "summary.json",
        "report_md": output_dir / "report.md",
        "claim_table_csv": output_dir / "claim_table.csv",
    }
    summary = {
        "schema_version": "h002_full_train_independent_revised_factor_claim_boundary_v1",
        "status": "full_train_independent_revised_factor_claim_boundary_ready",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "validation_used": False,
        "input": {
            "smoke_summary": rel_path(args.smoke_summary),
            "error_summary": rel_path(args.error_summary),
            "shortcut_summary": rel_path(args.shortcut_summary),
            "shortcut_comparisons": rel_path(args.shortcut_comparisons),
            "smoke_status": smoke_summary.get("status"),
            "error_status": error_summary.get("status"),
            "shortcut_status": shortcut_summary.get("status"),
        },
        "decision": decision,
        "claim_table": claim_table,
        "claim_boundary": {
            "paper_level_claim": "blocked",
            "hypothesis_stage_claim": "allowed_with_scope",
            "scope": decision["selected_claim_scope"],
            "required_before_paper_claim": [
                "human-confirmed label audit for selected support/vertical rows",
                "Dockerized paper experiment if promoted beyond hypothesis stage",
                "held-out or second-source evaluation before generalization claims",
            ],
        },
        "next_todo": decision["next_todo"],
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
    }
    smoke.write_json(output_paths["summary_json"], summary)
    write_csv(output_paths["claim_table_csv"], claim_table)
    write_report(output_paths["report_md"], summary, claim_table)

    print(
        "status={status} validation_used={validation_used} scope={scope} "
        "proximity_d_auprc={proximity:+.4f} next={next_todo}".format(
            status=summary["status"],
            validation_used=summary["validation_used"],
            scope="+".join(decision["selected_claim_scope"]),
            proximity=decision["key_numbers"]["proximity_d_auprc"],
            next_todo=summary["next_todo"],
        )
    )


if __name__ == "__main__":
    main()
