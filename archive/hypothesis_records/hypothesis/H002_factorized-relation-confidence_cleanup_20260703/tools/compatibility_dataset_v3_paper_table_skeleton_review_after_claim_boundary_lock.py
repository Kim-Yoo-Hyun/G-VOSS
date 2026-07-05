#!/usr/bin/env python3
"""Review whether the H002 paper-table skeleton is principled and paper-claim ready."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SKELETON_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock"

EXPECTED_SKELETON_STATUS = "h002_compatibility_dataset_v3_paper_table_skeleton_after_claim_boundary_lock_ready"
EXPECTED_SKELETON_NEXT = "compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock_v1"
STATUS_READY = "h002_compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock_reviewed"
STATUS_ERRORS = "h002_compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock_input_errors"
SELECTED_PATH = "table_review_keep_as_bounded_mechanism_evidence_select_gap_plan"
NEXT_TODO = "compatibility_dataset_v3_principled_design_gap_plan_after_table_review"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skeleton-dir", type=Path, default=DEFAULT_SKELETON_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
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


def row_lookup(rows: list[dict[str, str]], **filters: str) -> dict[str, str] | None:
    for row in rows:
        if all(row.get(key) == value for key, value in filters.items()):
            return row
    return None


def as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def validate_inputs(skeleton_summary: dict[str, Any], skeleton_dir: Path, main_rows: list[dict[str, str]], family_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if skeleton_summary.get("status") != EXPECTED_SKELETON_STATUS:
        errors.append({"error_type": "unexpected_skeleton_status", "actual": skeleton_summary.get("status")})
    if skeleton_summary.get("next_todo") != EXPECTED_SKELETON_NEXT:
        errors.append({"error_type": "unexpected_skeleton_next_todo", "actual": skeleton_summary.get("next_todo")})
    if skeleton_summary.get("validation_errors") != 0:
        errors.append({"error_type": "skeleton_validation_errors", "actual": skeleton_summary.get("validation_errors")})
    if line_count(skeleton_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "skeleton_validation_errors_file_not_empty"})

    decision = skeleton_summary.get("decision", {})
    required_decision = {
        "paper_table_skeleton_ready": True,
        "final_paper_result_promotion": "not_yet",
        "primary_table_scope": "relative_vertical + size_relative",
        "official_test_usage": False,
        "source_reranking_claim_enabled": False,
        "p_rel_p_obs_claim_enabled": False,
    }
    for key, expected in required_decision.items():
        if decision.get(key) != expected:
            errors.append({"error_type": "unexpected_skeleton_decision", "key": key, "actual": decision.get(key), "expected": expected})

    m4 = row_lookup(main_rows, table_block="primary_mechanism_macro", view_id="M4_TxG_compatibility")
    if not m4 or as_float(m4.get("auroc")) is None or as_float(m4.get("auroc")) < 0.99:
        errors.append({"error_type": "primary_m4_not_strong", "row": m4})
    for family in ["relative_vertical", "size_relative", "relative_horizontal", "support_contact"]:
        if row_lookup(family_rows, route_family=family) is None:
            errors.append({"error_type": "missing_family_row", "route_family": family})
    return errors


def principle_review_rows() -> list[dict[str, Any]]:
    return [
        {
            "principle": "separate_semantic_content_from_source_confidence",
            "verdict": "natural_and_required",
            "reason": "T_e should describe what relation means, while Z_e is a prior from an upstream source; mixing them would let C_e copy source confidence.",
            "paper_status": "keep_in_method_contract",
        },
        {
            "principle": "predicate_independent_geometry_evidence",
            "verdict": "natural_and_required",
            "reason": "G_e must be geometry evidence before predicate interpretation; otherwise compatibility is no longer a test between semantics and geometry.",
            "paper_status": "keep_in_method_contract",
        },
        {
            "principle": "compatibility_as_Te_Ge_matching",
            "verdict": "principled",
            "reason": "A relation is reliable only if the predicate semantics and object-pair geometry are mutually compatible; wrong-T and shuffled-G controls directly test this.",
            "paper_status": "main_mechanism_claim_allowed_bounded",
        },
        {
            "principle": "observability_separate_from_truth",
            "verdict": "principled_but_not_evaluated_here",
            "reason": "Q_e should decide whether evidence is sufficient to judge, not whether the relation is true; current official table does not evaluate p_obs/p_rel.",
            "paper_status": "method_design_or_future_not_result",
        },
        {
            "principle": "route_specific_evidence",
            "verdict": "natural",
            "reason": "Different predicates need different geometry and observability routes; the current table already shows primary, caveated, and diagnostic roles.",
            "paper_status": "framework_claim_allowed_with_scope",
        },
    ]


def table_claim_review_rows(main_rows: list[dict[str, str]], family_rows: list[dict[str, str]], control_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    m4_primary = row_lookup(main_rows, table_block="primary_mechanism_macro", view_id="M4_TxG_compatibility") or {}
    baseline_rows = [
        row_lookup(main_rows, table_block="primary_mechanism_macro", view_id="M1_T_semantic_only") or {},
        row_lookup(main_rows, table_block="primary_mechanism_macro", view_id="M2_G_geometry_only") or {},
        row_lookup(main_rows, table_block="primary_mechanism_macro", view_id="M3_T_plus_G_concat") or {},
    ]
    best_baseline = max(as_float(row.get("auroc")) or 0.0 for row in baseline_rows)
    m4_auroc = as_float(m4_primary.get("auroc")) or 0.0
    horizontal = row_lookup(family_rows, route_family="relative_horizontal") or {}
    support = row_lookup(family_rows, route_family="support_contact") or {}
    support_wrong_t = row_lookup(control_rows, control_scope="support_contact", comparison="M4_vs_C2_wrong_T_across_route") or {}
    return [
        {
            "review_item": "primary_mechanism_signal",
            "verdict": "strong",
            "evidence": f"M4 primary AUROC {m4_auroc:.6f} vs best baseline {best_baseline:.6f}",
            "paper_action": "can be shown as bounded mechanism evidence",
        },
        {
            "review_item": "primary_relation_scope",
            "verdict": "too_clean_for_standalone_top_tier_claim",
            "evidence": "Primary rows are signed comparison routes: relative_vertical and size_relative.",
            "paper_action": "do not promote as a standalone broad paper result",
        },
        {
            "review_item": "relative_horizontal",
            "verdict": "supporting_with_caveat",
            "evidence": f"M4 AUROC {horizontal.get('m4_compatibility_auroc')} with required caveat {horizontal.get('required_caveat')}",
            "paper_action": "report as frame-aware evidence only",
        },
        {
            "review_item": "support_contact",
            "verdict": "diagnostic_not_success",
            "evidence": f"M4 AUROC {support.get('m4_compatibility_auroc')}; wrong-T across-route control delta {support_wrong_t.get('delta_auroc')}",
            "paper_action": "use as failure taxonomy and evidence-gap motivation",
        },
        {
            "review_item": "paper_promotion",
            "verdict": "not_yet",
            "evidence": "The table is strong as a mechanism proof but narrow and partly obvious.",
            "paper_action": "select a gap plan before paper-facing promotion",
        },
    ]


def risk_rows() -> list[dict[str, Any]]:
    return [
        {
            "risk": "obvious_signed_comparison_task",
            "severity": "high",
            "reason": "higher/lower and bigger/smaller can look like direct geometry sign checks.",
            "mitigation": "Frame as mechanism sanity evidence, or add a harder route where compatibility is not a direct sign rule.",
        },
        {
            "risk": "not_source_deployable_yet",
            "severity": "high",
            "reason": "Current table uses official GT/counterfactual mechanism rows, not VL-SAT/Open3DSG candidate reranking.",
            "mitigation": "Run a separate source-candidate experiment if claiming relation-source reliability improvement.",
        },
        {
            "risk": "p_obs_p_rel_not_evaluated",
            "severity": "medium",
            "reason": "The proposed framework includes observability and reliability heads, but current official metric evaluates C_e only.",
            "mitigation": "Keep Q_e/p_obs/p_rel as design/future or add an observability-target experiment.",
        },
        {
            "risk": "support_contact_failure",
            "severity": "medium",
            "reason": "support_contact is not solved and controls show evidence ambiguity.",
            "mitigation": "Use it as a failure taxonomy motivating richer geometry/visual evidence.",
        },
    ]


def recommendation_rows() -> list[dict[str, Any]]:
    return [
        {
            "option": "A_promote_table_as_main_result_now",
            "recommendation": "reject",
            "reason": "The primary rows are too clean and could be criticized as direct signed-geometry tasks.",
        },
        {
            "option": "B_keep_as_bounded_mechanism_evidence",
            "recommendation": "accept",
            "reason": "It cleanly supports the principle that C_e must match T_e and G_e under controls.",
        },
        {
            "option": "C_add_harder_route_before_promotion",
            "recommendation": "strong_accept",
            "reason": "A harder route can convert the principled decomposition into a stronger paper claim.",
        },
        {
            "option": "D_shift_to_source_reranking_immediately",
            "recommendation": "defer",
            "reason": "Source reranking should be a separate experiment after the mechanism claim boundary is stable.",
        },
    ]


def write_markdown_report(
    path: Path,
    summary: dict[str, Any],
    principle_rows: list[dict[str, Any]],
    claim_rows: list[dict[str, Any]],
    risks: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
) -> None:
    lines = [
        "# H002 Paper Table Skeleton Review After Claim Boundary Lock",
        "",
        "## Status",
        "",
        "```text",
        f"artifact_root = {summary['output_artifacts']['artifact_root']}",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Core Judgment",
        "",
        "The H002 structure is principled and natural: relation reliability should not be",
        "estimated by a single upstream confidence score, and compatibility is naturally",
        "defined as matching semantic content `T_e` against predicate-independent geometry",
        "evidence `G_e`. The current table supports this mechanism under wrong-`T` and",
        "shuffled-`G` controls.",
        "",
        "However, the current primary table is too clean to promote as a standalone",
        "paper-level result. The main rows are signed comparison routes",
        "(`relative_vertical`, `size_relative`), so a reviewer can argue that the result",
        "is a direct geometry-sign task rather than a complete reliability framework.",
        "",
        "## Principle Review",
        "",
        "| Principle | Verdict | Paper Status | Reason |",
        "| --- | --- | --- | --- |",
    ]
    for row in principle_rows:
        lines.append(f"| `{row['principle']}` | {row['verdict']} | {row['paper_status']} | {row['reason']} |")
    lines.extend(["", "## Table Claim Review", "", "| Item | Verdict | Evidence | Action |", "| --- | --- | --- | --- |"])
    for row in claim_rows:
        lines.append(f"| `{row['review_item']}` | {row['verdict']} | {row['evidence']} | {row['paper_action']} |")
    lines.extend(["", "## Risks", "", "| Risk | Severity | Reason | Mitigation |", "| --- | --- | --- | --- |"])
    for row in risks:
        lines.append(f"| `{row['risk']}` | {row['severity']} | {row['reason']} | {row['mitigation']} |")
    lines.extend(["", "## Recommendation", "", "| Option | Recommendation | Reason |", "| --- | --- | --- |"])
    for row in recommendations:
        lines.append(f"| `{row['option']}` | {row['recommendation']} | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Keep the table as bounded mechanism evidence.",
            "- Do not promote it as a standalone final paper result yet.",
            "- The design direction is conceptually sound, but a harder route or source-deployable",
            "  experiment is needed before a strong paper claim.",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    skeleton_dir = args.skeleton_dir
    output_dir = args.output_dir

    skeleton_summary = read_json(skeleton_dir / "summary.json")
    main_rows = read_csv(skeleton_dir / "main_table_skeleton.csv")
    family_rows = read_csv(skeleton_dir / "family_table_skeleton.csv")
    control_rows = read_csv(skeleton_dir / "control_table_skeleton.csv")
    validation_errors = validate_inputs(skeleton_summary, skeleton_dir, main_rows, family_rows)

    principle = principle_review_rows()
    claim_review = table_claim_review_rows(main_rows, family_rows, control_rows)
    risks = risk_rows()
    recommendations = recommendation_rows()

    status = STATUS_ERRORS if validation_errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH if not validation_errors else "blocked_fix_skeleton_inputs_before_review",
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO if not validation_errors else EXPECTED_SKELETON_NEXT,
        "input_artifacts": {
            "skeleton_summary": rel_path(skeleton_dir / "summary.json"),
            "main_table_skeleton": rel_path(skeleton_dir / "main_table_skeleton.csv"),
            "family_table_skeleton": rel_path(skeleton_dir / "family_table_skeleton.csv"),
            "control_table_skeleton": rel_path(skeleton_dir / "control_table_skeleton.csv"),
        },
        "decision": {
            "principled_structure": True,
            "natural_design_flow": True,
            "table_is_standalone_paper_result": False,
            "keep_as_bounded_mechanism_evidence": True,
            "final_paper_result_promotion": "not_yet",
            "main_reason_not_promoted": "primary evidence is strong but too clean/signed-comparison-heavy",
            "recommended_next_action": "gap_plan_for_harder_route_or_source_deployable_evidence",
        },
        "output_artifacts": {
            "artifact_root": rel_path(output_dir),
            "principle_review": rel_path(output_dir / "principle_review.csv"),
            "table_claim_review": rel_path(output_dir / "table_claim_review.csv"),
            "risk_review": rel_path(output_dir / "risk_review.csv"),
            "recommendation": rel_path(output_dir / "recommendation.csv"),
            "report": rel_path(output_dir / "report.md"),
        },
    }

    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(output_dir / "principle_review.csv", principle)
    write_csv(output_dir / "table_claim_review.csv", claim_review)
    write_csv(output_dir / "risk_review.csv", risks)
    write_csv(output_dir / "recommendation.csv", recommendations)
    write_markdown_report(output_dir / "report.md", summary, principle, claim_review, risks, recommendations)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
