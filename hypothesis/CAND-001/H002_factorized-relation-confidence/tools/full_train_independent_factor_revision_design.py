#!/usr/bin/env python3
"""Design deployable revised factor blocks for H002 train-only posterior work."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke


H002_ROOT = Path(__file__).resolve().parents[1]
FULL_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full"
RGA_ROOT = FULL_ROOT / "rga"
DEFAULT_PATH_DECISION = RGA_ROOT / "independent_combiner_path_decision_codex_ver/summary.json"
DEFAULT_ERROR_SUMMARY = RGA_ROOT / "independent_combiner_upgrade_error_analysis_codex_ver/summary.json"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_factor_revision_design_codex_ver"

RAW_GEOMETRY_FIELDS = [
    "center_delta_z",
    "distance_3d",
    "distance_xy",
    "normalized_center_delta_z",
    "normalized_distance_3d",
    "normalized_distance_xy",
    "object_bottom_z",
    "object_top_z",
    "projected_iou_xy",
    "projected_object_overlap_ratio",
    "projected_subject_overlap_ratio",
    "subject_bottom_z",
    "subject_top_z",
    "vertical_gap_subject_on_object",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-decision", type=Path, default=DEFAULT_PATH_DECISION)
    parser.add_argument("--error-summary", type=Path, default=DEFAULT_ERROR_SUMMARY)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--max-match-rows",
        type=int,
        default=None,
        help="Optional debug limit. Default scans all train match rows.",
    )
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    with smoke.as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path) -> Any:
    with smoke.as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc


def collect_availability(path: Path, max_rows: int | None = None) -> dict[str, Any]:
    family_counts: Counter[str] = Counter()
    status_counts: dict[str, Counter[str]] = defaultdict(Counter)
    raw_feature_rows: Counter[str] = Counter()
    checkable_rows: Counter[str] = Counter()
    available_rows: Counter[str] = Counter()
    raw_keys: dict[str, set[str]] = defaultdict(set)
    total = 0
    for row in iter_jsonl(path):
        total += 1
        predicate = row.get("predicate") or {}
        geometry = row.get("geometry") or {}
        family = str(predicate.get("predicate_family", "missing_family"))
        family_counts[family] += 1
        status_counts[family][str(geometry.get("geometry_status", "missing_status"))] += 1
        if geometry.get("geometry_checkable"):
            checkable_rows[family] += 1
        if geometry.get("geometry_available"):
            available_rows[family] += 1
        features = geometry.get("raw_features") or {}
        if features:
            raw_feature_rows[family] += 1
            raw_keys[family].update(str(key) for key in features)
        if max_rows is not None and total >= max_rows:
            break

    rows = []
    for family, count in sorted(family_counts.items()):
        rows.append(
            {
                "predicate_family": family,
                "rows": count,
                "geometry_available_rows": available_rows[family],
                "geometry_checkable_rows": checkable_rows[family],
                "raw_feature_rows": raw_feature_rows[family],
                "raw_feature_coverage": raw_feature_rows[family] / count if count else 0.0,
                "status_satisfied": status_counts[family]["satisfied"],
                "status_unsatisfied": status_counts[family]["unsatisfied"],
                "status_uncertain": status_counts[family]["uncertain"],
                "status_unsupported": status_counts[family]["unsupported"],
                "raw_feature_keys": ",".join(sorted(raw_keys[family])),
            }
        )
    return {
        "schema_version": "h002_factor_revision_availability_v0",
        "input_path": smoke.rel_path(path),
        "max_rows": max_rows,
        "rows_scanned": total,
        "family_rows": rows,
    }


def factor_contracts() -> list[dict[str, Any]]:
    return [
        {
            "factor_id": "FR1_support_contact_witness_split",
            "priority": 1,
            "scope": "support_contact",
            "current_failure": (
                "C2/C3 overcorrect support_contact; support_contact contributes many new "
                "threshold mistakes and worsens calibration."
            ),
            "deployable_inputs": (
                "predicate label/family, subject/object labels, p_geom_valid, consistency, "
                "vertical_gap_subject_on_object, normalized_distance_xy, "
                "projected_subject_overlap_ratio, projected_object_overlap_ratio"
            ),
            "derived_features": (
                "contact_gap_abs, penetration_proxy, xy_support_overlap, "
                "floor_like_support_flag, object_object_support_flag, weak_contact_flag"
            ),
            "formula_sketch": (
                "Split support into floor/support-surface contact, object-object support, "
                "and weak/no-contact regimes before applying any residual correction."
            ),
            "forbidden_inputs": (
                "geometry_status as target shortcut, label_match_status, proposed_audit_role, "
                "queue_kind, rank_band, labeler confidence"
            ),
            "success_check": (
                "support_contact slice should no longer dominate new mistakes, and Brier "
                "should not worsen relative to semantic_plus_geometry."
            ),
        },
        {
            "factor_id": "FR2_relative_vertical_order_residual",
            "priority": 2,
            "scope": "relative_vertical",
            "current_failure": (
                "C3 is promising for relative_vertical and HL rows, but the signal is mixed "
                "into one global uncertainty gate."
            ),
            "deployable_inputs": (
                "predicate label, center_delta_z, normalized_center_delta_z, subject/object "
                "top/bottom z, vertical_gap_subject_on_object, projected_iou_xy"
            ),
            "derived_features": (
                "predicate_expected_z_sign, vertical_sign_agreement, vertical_margin_abs, "
                "vertical_clearance, xy_overlap_context"
            ),
            "formula_sketch": (
                "Use sign and margin of vertical order as a continuous residual; do not "
                "collapse higher/lower evidence into p_geom_valid only."
            ),
            "forbidden_inputs": (
                "deterministic satisfied/unsatisfied labels as main score and all audit "
                "target-construction metadata"
            ),
            "success_check": (
                "relative_vertical and semantic_high_geometry_low gains should persist "
                "without damaging support_contact."
            ),
        },
        {
            "factor_id": "FR3_coverage_uncertainty_gate",
            "priority": 3,
            "scope": "all families",
            "current_failure": (
                "Current uncertainty gate uses weak proxies and cannot separate evidence "
                "absence from true contradiction."
            ),
            "deployable_inputs": (
                "geometry_available, geometry_checkable, raw_feature_present, consistency, "
                "semantic rank, semantic score, absolute semantic-geometry disagreement"
            ),
            "derived_features": (
                "coverage_flag, unsupported_family_flag, raw_geometry_missing_flag, "
                "near_boundary_uncertainty, disagreement_uncertainty"
            ),
            "formula_sketch": (
                "Gate geometry corrections by evidence coverage; uncertain/unsupported rows "
                "should abstain or shrink toward semantic_plus_geometry."
            ),
            "forbidden_inputs": "human audit labels, multi-view as model input, validation/test rows",
            "success_check": (
                "C3-like threshold safety should remain while reducing ranking damage in "
                "support_contact."
            ),
        },
        {
            "factor_id": "FR4_family_shrinkage_residual",
            "priority": 4,
            "scope": "all supported families",
            "current_failure": (
                "Family gates help some slices but overcorrect others when each family has "
                "too much freedom."
            ),
            "deployable_inputs": "FR1-FR3 feature blocks plus predicate_family",
            "derived_features": (
                "global_residual, family_residual_delta, family_residual_scale, "
                "family_sample_weight"
            ),
            "formula_sketch": (
                "Use a global residual plus family-specific residual scales that are shrunk "
                "toward the global residual. No per-predicate free model at current N."
            ),
            "forbidden_inputs": "predicate-specific free parameters unless label count increases",
            "success_check": "Family-gated model improves ranking without worsening Brier.",
        },
        {
            "factor_id": "FR5_target_confirmation_gate",
            "priority": 5,
            "scope": "supervision",
            "current_failure": "All current posterior labels are Codex bootstrap labels.",
            "deployable_inputs": "none; this is an evidence gate, not a model input",
            "derived_features": "paper_claim_allowed flag remains false",
            "formula_sketch": (
                "Positive smoke results remain hypothesis-stage until human-confirmed or "
                "stronger independent labels exist."
            ),
            "forbidden_inputs": "using Codex label confidence as a model feature",
            "success_check": "No posterior performance claim is made from bootstrap labels alone.",
        },
    ]


def feature_blocks() -> list[dict[str, Any]]:
    rows = []
    base_fields = [
        ("semantic_score_norm", "semantic.rank/score", "available_now", "semantic plausibility"),
        ("semantic_rank_log", "semantic.rank", "available_now", "rank-derived semantic uncertainty"),
        ("p_geom_valid", "geometry calibration", "available_now", "geometry-only continuous evidence"),
        ("consistency_score", "geometry verifier", "available_now", "geometry consistency proxy"),
        ("absolute_disagreement", "derived", "available_now", "semantic-geometry mismatch magnitude"),
    ]
    for field, source, status, role in base_fields:
        rows.append(
            {
                "block_id": "base_sgcu",
                "field_name": field,
                "source": source,
                "status": status,
                "role": role,
                "model_input_allowed": True,
            }
        )
    for field in RAW_GEOMETRY_FIELDS:
        rows.append(
            {
                "block_id": "raw_geometry_witness",
                "field_name": field,
                "source": "match_rows.geometry.raw_features",
                "status": "available_for_checkable_supported_families",
                "role": "continuous relation-specific geometry evidence",
                "model_input_allowed": True,
            }
        )
    forbidden = [
        "geometry_status_satisfied_unsatisfied_as_main_score",
        "label_match_status",
        "proposed_audit_role",
        "queue_kind",
        "rank_band_hidden",
        "labeler_confidence",
        "multi_view_features_before_base_hypothesis_support",
        "validation_or_test_rows",
    ]
    for field in forbidden:
        rows.append(
            {
                "block_id": "forbidden_or_deferred",
                "field_name": field,
                "source": "audit/target construction",
                "status": "forbidden_or_deferred",
                "role": "would create leakage or scope expansion",
                "model_input_allowed": False,
            }
        )
    return rows


def next_smoke_plan() -> dict[str, Any]:
    return {
        "next_todo": "full_train_independent_revised_factor_dataset",
        "then": "full_train_independent_revised_factor_smoke",
        "split_policy": "train_only",
        "active_target": "proposed_role_balanced_codex_ver",
        "baseline_views": [
            "semantic_only",
            "geometry_only",
            "semantic_plus_geometry",
            "current_factorized_reliability_posterior",
        ],
        "revised_factor_views": [
            "D1_revised_residual_base",
            "D2_support_contact_split_residual",
            "D3_relative_vertical_order_residual",
            "D4_coverage_uncertainty_shrinkage",
        ],
        "controls": [
            "scan-grouped folds",
            "same 158-row controlled slice before any target expansion",
            "no validation/test",
            "no hidden audit metadata",
            "multi-view audit only",
            "semantic_plus_geometry remains the main baseline",
            "report family/direction/coverage slices",
            "report threshold transfer and Brier, not AUPRC alone",
        ],
        "progression_rule": {
            "primary": "no new-mistake increase versus semantic_plus_geometry",
            "secondary": "Brier <= semantic_plus_geometry or AUPRC >= semantic_plus_geometry + 0.01",
            "paper_claim_allowed": False,
        },
    }


def build_summary(
    path_decision: dict[str, Any],
    error_summary: dict[str, Any],
    availability: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    return {
        "schema_version": "h002_full_train_independent_factor_revision_design_summary_v0",
        "status": "full_train_independent_factor_revision_design_ready",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "path_decision": smoke.rel_path(DEFAULT_PATH_DECISION),
            "path_decision_status": path_decision.get("status"),
            "error_summary": smoke.rel_path(DEFAULT_ERROR_SUMMARY),
            "error_status": error_summary.get("status"),
            "match_rows": smoke.rel_path(DEFAULT_MATCH_ROWS),
        },
        "output_dir": smoke.rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "trains_new_model": False,
            "validation_usage": False,
            "test_usage": False,
            "hidden_metadata_as_model_input": False,
            "multi_view_as_model_input": False,
            "paper_evidence_allowed": False,
            "posterior_performance_claim_allowed": False,
            "generic_high_capacity_combiner_next": False,
        },
        "availability": availability,
        "factor_contracts": factor_contracts(),
        "feature_blocks": feature_blocks(),
        "next_smoke_plan": next_smoke_plan(),
        "decision": (
            "Materialize revised deployable factor blocks before another combiner smoke. "
            "Use raw geometry witness fields for supported families, split support_contact "
            "and relative_vertical evidence, add explicit coverage/uncertainty factors, "
            "and keep family effects shrinkage-limited."
        ),
        "claim_boundary": {
            "allowed": (
                "The current evidence supports factor redesign as the next hypothesis-stage "
                "step because the previous combiners failed in structured family-specific ways."
            ),
            "blocked": (
                "Any claim that a revised posterior improves relation reliability is blocked "
                "until the revised factor dataset and train-only smoke pass controls."
            ),
        },
        "next_todo": "full_train_independent_revised_factor_dataset",
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Full Train Independent Factor Revision Design",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Boundary",
        "",
        "- Train-only design artifact.",
        "- No new model is trained here.",
        "- No validation/test rows are used.",
        "- Hidden audit metadata is forbidden as model input.",
        "- Multi-view remains audit evidence only.",
        "- Posterior performance claims remain blocked.",
        "",
        "## Decision",
        "",
        summary["decision"],
        "",
        "## Availability",
        "",
        "| Family | Rows | Raw Feature Rows | Raw Coverage | Satisfied | Unsatisfied | Uncertain | Unsupported |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["availability"]["family_rows"]:
        lines.append(
            f"| `{row['predicate_family']}` | {row['rows']} | {row['raw_feature_rows']} | "
            f"{row['raw_feature_coverage']:.4f} | {row['status_satisfied']} | "
            f"{row['status_unsatisfied']} | {row['status_uncertain']} | {row['status_unsupported']} |"
        )
    lines.extend(
        [
            "",
            "## Factor Contracts",
            "",
            "| Priority | Factor | Scope | Success Check |",
            "| ---: | --- | --- | --- |",
        ]
    )
    for row in summary["factor_contracts"]:
        lines.append(f"| {row['priority']} | `{row['factor_id']}` | `{row['scope']}` | {row['success_check']} |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"Allowed: {summary['claim_boundary']['allowed']}",
            "",
            f"Blocked: {summary['claim_boundary']['blocked']}",
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(output_dir: Path, summary: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    smoke.write_json(output_dir / "summary.json", summary)
    smoke.write_json(output_dir / "feature_spec.json", {"feature_blocks": summary["feature_blocks"]})
    smoke.write_json(output_dir / "smoke_plan.json", summary["next_smoke_plan"])
    write_csv(
        output_dir / "factor_contracts.csv",
        summary["factor_contracts"],
        [
            "factor_id",
            "priority",
            "scope",
            "current_failure",
            "deployable_inputs",
            "derived_features",
            "formula_sketch",
            "forbidden_inputs",
            "success_check",
        ],
    )
    write_csv(
        output_dir / "feature_blocks.csv",
        summary["feature_blocks"],
        ["block_id", "field_name", "source", "status", "role", "model_input_allowed"],
    )
    write_csv(
        output_dir / "availability_by_family.csv",
        summary["availability"]["family_rows"],
        [
            "predicate_family",
            "rows",
            "geometry_available_rows",
            "geometry_checkable_rows",
            "raw_feature_rows",
            "raw_feature_coverage",
            "status_satisfied",
            "status_unsatisfied",
            "status_uncertain",
            "status_unsupported",
            "raw_feature_keys",
        ],
    )
    write_report(output_dir / "design.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    path_decision = read_json(args.path_decision)
    error_summary = read_json(args.error_summary)
    output_dir = smoke.as_abs(args.output_dir)
    availability = collect_availability(args.match_rows, args.max_match_rows)
    summary = build_summary(path_decision, error_summary, availability, output_dir)
    summary["input"]["path_decision"] = smoke.rel_path(args.path_decision)
    summary["input"]["error_summary"] = smoke.rel_path(args.error_summary)
    summary["input"]["match_rows"] = smoke.rel_path(args.match_rows)
    write_outputs(output_dir, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        "status={status} factors={factors} families={families} validation_used={validation_used} "
        "posterior_claim_allowed={posterior_claim_allowed} next={next_todo}".format(
            status=summary["status"],
            factors=len(summary["factor_contracts"]),
            families=len(summary["availability"]["family_rows"]),
            validation_used=summary["boundary"]["validation_usage"],
            posterior_claim_allowed=summary["boundary"]["posterior_performance_claim_allowed"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
