#!/usr/bin/env python3
"""Factor-definition repair plan for H002 revised sampling all-label-ready slice."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_ERROR_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_controlled_error_analysis_all_label_ready"
DEFAULT_SOURCE_FEATURE_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_source_feature_join_all_label_ready"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan_all_label_ready"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--error-dir", type=Path, default=DEFAULT_ERROR_DIR)
    parser.add_argument("--source-feature-dir", type=Path, default=DEFAULT_SOURCE_FEATURE_DIR)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def first_raw_feature_schema(match_rows: Path) -> dict[str, Any]:
    raw_fields: list[str] = []
    sample_prediction_id = None
    rows_checked = 0
    with as_abs(match_rows).open("r", encoding="utf-8") as handle:
        for line in handle:
            rows_checked += 1
            row = json.loads(line)
            raw = row.get("geometry", {}).get("raw_features")
            if raw:
                raw_fields = sorted(raw)
                sample_prediction_id = row.get("identity", {}).get("prediction_id")
                break
    return {
        "match_rows": rel_path(match_rows),
        "rows_checked_until_first_raw_schema": rows_checked,
        "sample_prediction_id": sample_prediction_id,
        "raw_fields": raw_fields,
    }


def family_rows(slice_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output = []
    for row in slice_rows:
        if row["view"] == "factorized_reliability_posterior" and row["slice_name"] == "predicate_family":
            output.append(
                {
                    "family": row["slice_value"],
                    "rows": int(row["rows"]),
                    "positive": int(row["positive"]),
                    "negative": int(row["negative"]),
                    "delta_auprc_vs_semantic_plus_geometry": float(row["delta_auprc_view_minus_sg"]),
                    "delta_brier_vs_semantic_plus_geometry": float(row["delta_brier_view_minus_sg"]),
                    "new_errors_minus_fixes": int(row["new_errors_minus_fixes"]),
                }
            )
    return output


def factor_contracts() -> list[dict[str, Any]]:
    return [
        {
            "factor_id": "FD0_typed_relation_router",
            "scope": "all",
            "purpose": "Route each predicate to a deterministic witness template without learning a free family offset.",
            "required_inputs": "predicate_label,predicate_family",
            "derived_features": "support_contact_gate,relative_vertical_gate",
            "allowed": True,
            "not_allowed": "family_only_offset,free_predicate_id_embedding",
        },
        {
            "factor_id": "FD1_support_contact_raw_witness",
            "scope": "support_contact",
            "purpose": "Represent contact/support as contact gap, xy support overlap, and distance evidence instead of a single p_geom_valid scalar.",
            "required_inputs": "vertical_gap_subject_on_object,normalized_distance_xy,projected_subject_overlap_ratio,projected_object_overlap_ratio,projected_iou_xy",
            "derived_features": "support_gap_abs,support_gap_signed,support_xy_overlap_max,support_xy_overlap_min,support_iou_xy,support_distance_xy,contact_boundary_uncertainty",
            "allowed": True,
            "not_allowed": "geometry_status shortcut,review-derived informativeness",
        },
        {
            "factor_id": "FD2_relative_vertical_order_witness",
            "scope": "relative_vertical",
            "purpose": "Represent higher/lower as signed vertical order and margin evidence because p_geom_valid saturates for both positive and negative rows.",
            "required_inputs": "center_delta_z,normalized_center_delta_z,subject_bottom_z,subject_top_z,object_bottom_z,object_top_z,projected_iou_xy",
            "derived_features": "expected_z_sign,vertical_signed_margin,vertical_sign_agreement,vertical_margin_abs,vertical_interval_overlap,vertical_xy_context",
            "allowed": True,
            "not_allowed": "global p_geom_valid as main vertical reliability evidence",
        },
        {
            "factor_id": "FD3_family_local_normalization",
            "scope": "support_contact,relative_vertical",
            "purpose": "Normalize raw residuals inside typed witness families before supervised reliability fitting.",
            "required_inputs": "FD1 raw features,FD2 raw features,semantic_score_norm,semantic_rank",
            "derived_features": "family_local_residual_z,family_local_semantic_percentile,family_local_disagreement_z",
            "allowed": True,
            "not_allowed": "label-derived normalization,validation/test normalization",
        },
        {
            "factor_id": "FD4_uncertainty_and_boundary_evidence",
            "scope": "all",
            "purpose": "Separate ambiguous/boundary geometry from strong contradiction or strong support.",
            "required_inputs": "raw residual magnitudes,coverage flags,semantic_geometry_gap",
            "derived_features": "near_boundary_flag,strong_witness_flag,weak_witness_flag,semantic_geometry_gap_signed,semantic_geometry_gap_abs",
            "allowed": True,
            "not_allowed": "multi_view_as_model_input,target_label_as_uncertainty",
        },
        {
            "factor_id": "FD5_optional_endpoint_type_ablation",
            "scope": "support_contact",
            "purpose": "Test whether endpoint category helps contact reliability without becoming a shortcut.",
            "required_inputs": "subject_label,object_label",
            "derived_features": "object_floor_like_flag,object_wall_like_flag,subject_room_surface_flag",
            "allowed": "ablation_only",
            "not_allowed": "main claim unless controls show no shortcut",
        },
    ]


def feature_blocks() -> list[dict[str, Any]]:
    return [
        {
            "view": "semantic_only",
            "feature_blocks": "source_semantic_score,source_rank",
            "purpose": "Existing semantic baseline.",
        },
        {
            "view": "legacy_geometry_only",
            "feature_blocks": "p_geom_valid,consistency_score",
            "purpose": "Keep the old geometry-only scalar baseline for continuity.",
        },
        {
            "view": "raw_witness_only_v2",
            "feature_blocks": "FD1,FD2,FD3,FD4 without semantic score",
            "purpose": "Measure whether repaired geometry evidence carries relation reliability signal.",
        },
        {
            "view": "semantic_plus_raw_witness_v2",
            "feature_blocks": "semantic_only + FD1 + FD2 + FD3 + FD4",
            "purpose": "Direct replacement for semantic_plus_geometry.",
        },
        {
            "view": "factorized_reliability_posterior_v2_linear",
            "feature_blocks": "semantic_only + typed raw witness + signed disagreement + uncertainty",
            "purpose": "Low-capacity factorized posterior after feature repair.",
        },
        {
            "view": "factorized_reliability_posterior_v2_family_shrinkage",
            "feature_blocks": "v2_linear + constrained family-local residual deltas",
            "purpose": "First improved combiner candidate; use shrinkage, not a free high-capacity model.",
        },
        {
            "view": "endpoint_type_ablation",
            "feature_blocks": "v2_family_shrinkage + FD5",
            "purpose": "Check whether endpoint labels explain support_contact without overfitting.",
        },
    ]


def smoke_plan() -> dict[str, Any]:
    return {
        "next_todo": "revised_sampling_all_label_ready_raw_witness_feature_join_v2",
        "split_policy": "train_only",
        "evaluation": [
            "in_sample_diagnostic",
            "train_internal_3fold",
            "train_internal_grouped_by_scan",
        ],
        "main_comparisons": [
            "semantic_only",
            "legacy_geometry_only",
            "semantic_plus_geometry",
            "raw_witness_only_v2",
            "semantic_plus_raw_witness_v2",
            "factorized_reliability_posterior_v2_linear",
            "factorized_reliability_posterior_v2_family_shrinkage",
        ],
        "controls": [
            "raw_witness_shuffle_global",
            "raw_witness_shuffle_within_family",
            "wrong_pair_raw_witness",
            "family_only_offset",
            "no_family_local_normalization",
            "legacy_p_geom_only",
        ],
        "success_gate": {
            "primary": "factorized_reliability_posterior_v2_family_shrinkage",
            "reference": "semantic_plus_geometry",
            "grouped_by_scan_delta_auprc_min": 0.02,
            "grouped_by_scan_delta_brier_max": 0.0,
            "new_errors_minus_fixes_max": 0,
            "family_requirements": {
                "support_contact": "delta_brier <= 0 and delta_auprc >= 0",
                "relative_vertical": "delta_auprc >= 0 and no threshold regression",
            },
            "control_requirement": "raw witness shuffle controls must remove most of the v2 gain",
        },
    }


def input_contract_v2(raw_schema: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_support_vertical_v2_revised_sampling_input_contract_v2_plan",
        "allowed_model_input_root": "baseline_inputs",
        "new_required_source_join": "raw witness values from match_rows.geometry.raw_features keyed by prediction_id",
        "raw_feature_schema_source": raw_schema,
        "allowed_inputs": [
            "source semantic score/rank after label lock",
            "p_geom_valid only as a legacy baseline and auxiliary scalar",
            "raw geometry witness values from match_rows.geometry.raw_features",
            "deterministic typed witness gates derived from predicate label/family",
            "coverage/missingness indicators",
            "family-local normalization statistics fit on train-only rows",
        ],
        "forbidden_as_model_input": [
            "review fields",
            "target labels",
            "hidden audit metadata",
            "packet paths",
            "multi-view evidence",
            "queue/role/rank-band construction axes",
            "geometry_status satisfied/unsatisfied shortcut",
            "free predicate/family categorical shortcut",
            "validation/test rows",
        ],
        "predicate_family_policy": (
            "Family is allowed only as deterministic routing into relation-specific witness templates; "
            "free family-only offsets must remain a control, not the main model."
        ),
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    fam = {row["family"]: row for row in summary["error_analysis"]["family_slices"]}
    lines = [
        "# H002 Factor Definition Repair Plan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage repair plan.",
        "- No validation/test rows are used.",
        "- No model is trained in this step.",
        "- The plan changes the evidence contract before changing posterior capacity.",
        "- Results are not paper-level metrics.",
        "",
        "## Diagnosis Used",
        "",
        f"- Status: `{summary['input']['error_status']}`",
        f"- Rows: `{summary['input']['rows']}`",
        f"- Factorized vs `semantic_plus_geometry` grouped delta AUPRC: `{summary['error_analysis']['grouped_delta']['auprc']:.4f}`",
        f"- Factorized vs `semantic_plus_geometry` grouped delta Brier: `{summary['error_analysis']['grouped_delta']['brier']:.4f}`",
        "",
        "Family slices:",
        "",
        "| Family | Rows | Pos | Neg | dAUPRC | dBrier | New-Fix |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for family in ["support_contact", "relative_vertical"]:
        row = fam[family]
        lines.append(
            f"| `{family}` | {row['rows']} | {row['positive']} | {row['negative']} | "
            f"{row['delta_auprc_vs_semantic_plus_geometry']:.4f} | "
            f"{row['delta_brier_vs_semantic_plus_geometry']:.4f} | {row['new_errors_minus_fixes']} |"
        )
    lines.extend(
        [
            "",
            "## Repair Decision",
            "",
            "현재 실패는 posterior combiner capacity보다 evidence factor 정의 문제로 본다.",
            "`p_geom_valid`와 `consistency_score`가 relation reliability를 직접 설명하는 scalar로는 부족하고,",
            "`support_contact`와 `relative_vertical`에서 서로 다른 의미로 동작한다.",
            "",
            "따라서 다음 구현은 다음 원칙을 따른다.",
            "",
            "- `p_geom_valid`는 legacy geometry baseline으로 남긴다.",
            "- main geometry evidence는 raw witness residual로 재구성한다.",
            "- predicate family는 free categorical shortcut이 아니라 typed witness router로만 사용한다.",
            "- family-local normalization을 먼저 도입하고, high-capacity combiner는 이후로 미룬다.",
            "",
            "## Factor Contracts",
            "",
            "| Factor | Scope | Purpose |",
            "| --- | --- | --- |",
        ]
    )
    for row in summary["factor_contracts"]:
        lines.append(f"| `{row['factor_id']}` | `{row['scope']}` | {row['purpose']} |")
    lines.extend(
        [
            "",
            "## Next Smoke",
            "",
            f"Next TODO: `{summary['next_todo']}`",
            "",
            "Required main comparisons:",
            "",
        ]
    )
    for view in summary["smoke_plan"]["main_comparisons"]:
        lines.append(f"- `{view}`")
    lines.extend(
        [
            "",
            "Required controls:",
            "",
        ]
    )
    for control in summary["smoke_plan"]["controls"]:
        lines.append(f"- `{control}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    error_dir = as_abs(args.error_dir)
    source_feature_dir = as_abs(args.source_feature_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    error_summary = read_json(error_dir / "summary.json")
    source_summary = read_json(source_feature_dir / "summary.json")
    slice_rows = read_csv(error_dir / "slice_deltas.csv")
    raw_schema = first_raw_feature_schema(args.match_rows)
    grouped_delta = error_summary["grouped_factorized_minus_semantic_plus_geometry"]

    summary = {
        "schema_version": "h002_support_vertical_v2_revised_sampling_factor_definition_repair_plan_summary_v1",
        "status": "full_train_independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan_ready",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "error_dir": rel_path(error_dir),
            "source_feature_dir": rel_path(source_feature_dir),
            "error_status": error_summary["status"],
            "source_feature_status": source_summary["status"],
            "rows": error_summary["input"]["rows"],
            "positive": error_summary["input"]["positive"],
            "negative": error_summary["input"]["negative"],
        },
        "output_dir": rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_model": False,
            "changes_feature_contract": True,
            "changes_posterior_combiner": False,
            "paper_evidence_allowed": False,
        },
        "error_analysis": {
            "grouped_delta": grouped_delta,
            "family_slices": family_rows(slice_rows),
            "diagnosis": error_summary["diagnosis"],
        },
        "factor_contracts": factor_contracts(),
        "feature_blocks": feature_blocks(),
        "input_contract_v2": input_contract_v2(raw_schema),
        "smoke_plan": smoke_plan(),
        "decision": (
            "Repair typed geometry evidence and family-local normalization before trying higher-capacity "
            "posterior combiners. The next executable step is a raw-witness feature join v2 that keeps "
            "review fields, hidden construction axes, geometry_status shortcuts, packet paths, multi-view "
            "evidence, validation, and test data out of model inputs."
        ),
        "claim_boundary": {
            "allowed": (
                "The current all-label-ready smoke identifies feature/family alignment as the next blocker."
            ),
            "blocked": (
                "No factorized posterior improvement claim is allowed until raw-witness v2 smoke passes grouped "
                "and control gates."
            ),
        },
        "next_todo": "revised_sampling_all_label_ready_raw_witness_feature_join_v2",
    }

    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "input_contract_v2.json", summary["input_contract_v2"])
    write_json(output_dir / "next_smoke_plan.json", summary["smoke_plan"])
    write_csv(output_dir / "factor_contracts.csv", summary["factor_contracts"])
    write_csv(output_dir / "feature_blocks.csv", summary["feature_blocks"])
    write_report(output_dir / "report.md", summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    delta = summary["error_analysis"]["grouped_delta"]
    print(
        "status={status} rows={rows} validation_used={validation_used} "
        "changes_feature_contract={changes_feature_contract} changes_combiner={changes_combiner} "
        "raw_fields={raw_fields} d_auprc_factorized_vs_sg={d_auprc:.4f} next={next_todo}".format(
            status=summary["status"],
            rows=summary["input"]["rows"],
            validation_used=summary["boundary"]["validation_usage"],
            changes_feature_contract=summary["boundary"]["changes_feature_contract"],
            changes_combiner=summary["boundary"]["changes_posterior_combiner"],
            raw_fields=len(summary["input_contract_v2"]["raw_feature_schema_source"]["raw_fields"]),
            d_auprc=delta["auprc"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
