#!/usr/bin/env python3
"""Run a route-specific relative-horizontal frame scorer.

This experiment reopens left/right/front/behind as a separate
frame-aware directional route. It does not change the locked generic H002
score. The goal is to test whether a route-specific scorer can be promoted
beyond the earlier caveated diagnostic status.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from audit_relative_horizontal_frame_route import (
    K_GRID,
    PREDICATES,
    PROMOTION_K,
    SOURCE_IDS,
    build_frame_protocol_rows,
    deterministic_frame_metrics,
    load_relative_records,
    rel_path,
    safe_float,
    write_csv,
    write_json,
    write_text,
)


SCHEMA_VERSION = "h002_relative_horizontal_route_scorer_v1"
STATUS_READY = "h002_relative_horizontal_route_scorer_ready"
STATUS_ERROR = "h002_relative_horizontal_route_scorer_errors"

SELECTED_PREDICTION_K = 100

D_TO_RH = {
    "D0_source_score": "RH0_source_score",
    "D1_source_x_world_xy_frame": "RH1_source_x_frame_score",
    "D4_world_xy_frame_only": "RH2_frame_score_only",
    "D2_source_x_axis_swap": "RH3_source_x_axis_swap_control",
    "D3_source_x_sign_flip": "RH4_source_x_sign_flip_control",
    "D5_axis_swap_only": "RH5_axis_swap_only_control",
    "D6_sign_flip_only": "RH6_sign_flip_only_control",
}

RH_TO_D = {value: key for key, value in D_TO_RH.items()}
RH_SCORE_IDS = list(RH_TO_D)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--materialization-dir", type=Path, required=True)
    parser.add_argument("--frame-audit-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def remap_score_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        score_id = row.get("score_id")
        if score_id not in D_TO_RH:
            continue
        new_row = dict(row)
        new_row["score_id"] = D_TO_RH[str(score_id)]
        out.append(new_row)
    return out


def group_records(records: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[(record["source_id"], record["subgraph_id"])].append(record)
    return grouped


def selected_predictions(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grouped = group_records(records)
    for (source_id, subgraph_id), bucket in sorted(grouped.items()):
        for rh_score_id, d_score_id in RH_TO_D.items():
            ranked = sorted(
                bucket,
                key=lambda row: (
                    float(row["scores"][d_score_id]),
                    float(row["scores"]["D0_source_score"]),
                    str(row["candidate_id"]),
                ),
                reverse=True,
            )
            for rank, record in enumerate(ranked[:SELECTED_PREDICTION_K], start=1):
                rows.append(
                    {
                        "source_id": source_id,
                        "subgraph_id": subgraph_id,
                        "route_family": "relative_horizontal",
                        "predicate_label": record["predicate_label"],
                        "candidate_id": record["candidate_id"],
                        "score_id": rh_score_id,
                        "score": record["scores"][d_score_id],
                        "source_score": record["scores"]["D0_source_score"],
                        "rank": rank,
                        "gt_exact_match": record["gt_exact_match"],
                        "violation_checkable": record["violation_checkable"],
                        "violation_status": record["violation_status"],
                    }
                )
    return rows


def empty_acc() -> dict[str, Any]:
    return {
        "unit_count": 0,
        "gt_units": 0,
        "gt_total": 0,
        "gt_selected": 0,
        "selected_total": 0,
        "violation_denominator": 0,
        "violation_count": 0,
    }


def finalize(base: dict[str, Any], acc: dict[str, Any]) -> dict[str, Any]:
    recall = None if acc["gt_total"] == 0 else acc["gt_selected"] / acc["gt_total"]
    violation = None if acc["violation_denominator"] == 0 else acc["violation_count"] / acc["violation_denominator"]
    selected_mean = None if acc["unit_count"] == 0 else acc["selected_total"] / acc["unit_count"]
    return {
        **base,
        "unit_count": acc["unit_count"],
        "gt_units": acc["gt_units"],
        "gt_total": acc["gt_total"],
        "gt_selected": acc["gt_selected"],
        "Recall@K": recall,
        "selected_total": acc["selected_total"],
        "Selected@K_mean": selected_mean,
        "violation_denominator": acc["violation_denominator"],
        "violation_count": acc["violation_count"],
        "Violation@K": violation,
    }


def predicate_metrics(
    selected_rows: list[dict[str, Any]],
    denom_by_predicate_group: dict[tuple[str, str, str], set[str]],
) -> list[dict[str, Any]]:
    denom_by_source_predicate: dict[tuple[str, str], set[str]] = defaultdict(set)
    units_by_source_predicate: dict[tuple[str, str], set[str]] = defaultdict(set)
    for (source_id, subgraph_id, predicate), ids in denom_by_predicate_group.items():
        denom_by_source_predicate[(source_id, predicate)].update(ids)
        units_by_source_predicate[(source_id, predicate)].add(subgraph_id)

    accs: dict[tuple[str, str, str, int], dict[str, Any]] = defaultdict(empty_acc)
    selected_gt: dict[tuple[str, str, str, int], set[str]] = defaultdict(set)
    for row in selected_rows:
        predicate = str(row["predicate_label"])
        if predicate not in PREDICATES:
            continue
        rank = int(row["rank"])
        source_id = str(row["source_id"])
        score_id = str(row["score_id"])
        for k in K_GRID:
            if rank > k:
                continue
            key = (source_id, predicate, score_id, k)
            acc = accs[key]
            acc["selected_total"] += 1
            if row["gt_exact_match"]:
                selected_gt[key].add(str(row["candidate_id"]))
            if row["violation_checkable"]:
                acc["violation_denominator"] += 1
                if row["violation_status"] == "violated":
                    acc["violation_count"] += 1

    rows: list[dict[str, Any]] = []
    for source_id in SOURCE_IDS:
        for predicate in PREDICATES:
            denom = denom_by_source_predicate.get((source_id, predicate), set())
            units = units_by_source_predicate.get((source_id, predicate), set())
            for score_id in RH_SCORE_IDS:
                for k in K_GRID:
                    key = (source_id, predicate, score_id, k)
                    acc = dict(accs.get(key, empty_acc()))
                    acc["unit_count"] = len(units)
                    acc["gt_units"] = len(units)
                    acc["gt_total"] = len(denom)
                    acc["gt_selected"] = len(selected_gt.get(key, set()))
                    rows.append(
                        finalize(
                            {
                                "level": "source_predicate",
                                "source_id": source_id,
                                "route_family": "relative_horizontal",
                                "predicate_label": predicate,
                                "score_id": score_id,
                                "K": k,
                            },
                            acc,
                        )
                    )
    return rows


def comparison_rows(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {
        (row["level"], row["source_id"], row.get("predicate_label", ""), row["score_id"], int(row["K"])): row
        for row in metric_rows
    }
    comparisons = [
        "RH0_source_score",
        "RH2_frame_score_only",
        "RH3_source_x_axis_swap_control",
        "RH4_source_x_sign_flip_control",
        "RH5_axis_swap_only_control",
        "RH6_sign_flip_only_control",
    ]
    out: list[dict[str, Any]] = []
    levels = sorted({str(row["level"]) for row in metric_rows})
    for level in levels:
        predicates = [""] if level == "source_family" else PREDICATES
        for source_id in SOURCE_IDS:
            for predicate in predicates:
                for k in K_GRID:
                    target = by_key.get((level, source_id, predicate, "RH1_source_x_frame_score", k))
                    if not target:
                        continue
                    target_r = safe_float(target.get("Recall@K"), 0.0) or 0.0
                    target_v = safe_float(target.get("Violation@K"), 0.0) or 0.0
                    for baseline in comparisons:
                        base = by_key.get((level, source_id, predicate, baseline, k))
                        if not base:
                            continue
                        base_r = safe_float(base.get("Recall@K"), 0.0) or 0.0
                        base_v = safe_float(base.get("Violation@K"), 0.0) or 0.0
                        row = {
                            "level": level,
                            "source_id": source_id,
                            "route_family": "relative_horizontal",
                            "predicate_label": predicate,
                            "K": k,
                            "comparison": f"RH1_source_x_frame_score_minus_{baseline}",
                            "RH1_Recall@K": target_r,
                            "baseline_Recall@K": base_r,
                            "delta_Recall@K": target_r - base_r,
                            "RH1_Violation@K": target_v,
                            "baseline_Violation@K": base_v,
                            "delta_Violation@K": target_v - base_v,
                            "recall_not_large_loss_0p01": target_r - base_r >= -0.01,
                            "violation_nonincrease": target_v - base_v <= 0.0,
                            "violation_reduced_by_0p05": target_v - base_v <= -0.05,
                        }
                        out.append(row)
    return out


def summarize_gate(comparisons: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_vs_s0 = [
        row
        for row in comparisons
        if row["level"] == "source_family"
        and row["comparison"] == "RH1_source_x_frame_score_minus_RH0_source_score"
        and int(row["K"]) in PROMOTION_K
    ]
    predicate_vs_s0 = [
        row
        for row in comparisons
        if row["level"] == "source_predicate"
        and row["comparison"] == "RH1_source_x_frame_score_minus_RH0_source_score"
        and int(row["K"]) in [20, 50]
    ]
    source_violation_regressions = [row for row in source_vs_s0 if safe_float(row["delta_Violation@K"], 0.0) > 0.0]
    source_recall_losses = [row for row in source_vs_s0 if safe_float(row["delta_Recall@K"], 0.0) < -0.01]
    predicate_violation_regressions = [row for row in predicate_vs_s0 if safe_float(row["delta_Violation@K"], 0.0) > 0.0]
    predicate_recall_losses = [row for row in predicate_vs_s0 if safe_float(row["delta_Recall@K"], 0.0) < -0.05]

    control_comparisons = [
        row
        for row in comparisons
        if row["level"] == "source_family"
        and int(row["K"]) in PROMOTION_K
        and row["comparison"]
        in {
            "RH1_source_x_frame_score_minus_RH3_source_x_axis_swap_control",
            "RH1_source_x_frame_score_minus_RH4_source_x_sign_flip_control",
            "RH1_source_x_frame_score_minus_RH5_axis_swap_only_control",
            "RH1_source_x_frame_score_minus_RH6_sign_flip_only_control",
        }
    ]
    control_failures = [
        row
        for row in control_comparisons
        if not bool(row["violation_reduced_by_0p05"])
    ]

    source_violation_pass = len(source_violation_regressions) == 0
    predicate_violation_pass = len(predicate_violation_regressions) == 0
    control_pass = len(control_failures) == 0
    strict_balanced_pass = (
        source_violation_pass
        and len(source_recall_losses) == 0
        and predicate_violation_pass
        and len(predicate_recall_losses) == 0
        and control_pass
    )
    violation_control_pass = source_violation_pass and predicate_violation_pass and control_pass

    gate_rows = [
        {
            "step": 1,
            "gate": "route_specific_scorer_defined",
            "passed": True,
            "decision": "RH1_source_x_frame_score",
            "reason": "source score multiplied by frozen world-XY frame residual compatibility",
        },
        {
            "step": 2,
            "gate": "frame_protocol_frozen",
            "passed": True,
            "decision": "dataset_world_xy_reference_frame_from_3rscan_obb_centroids",
            "reason": "same protocol as the prior audit, no label-dependent tuning",
        },
        {
            "step": 3,
            "gate": "axis_and_sign_controls_degrade",
            "passed": control_pass,
            "decision": "pass" if control_pass else "fail",
            "reason": f"control_failures={len(control_failures)}",
        },
        {
            "step": 4,
            "gate": "source_wide_violation_nonincrease",
            "passed": source_violation_pass,
            "decision": "pass" if source_violation_pass else "fail",
            "reason": f"source_violation_regressions={len(source_violation_regressions)}",
        },
        {
            "step": 4,
            "gate": "source_wide_recall_not_large_loss",
            "passed": len(source_recall_losses) == 0,
            "decision": "pass" if len(source_recall_losses) == 0 else "fail",
            "reason": f"source_recall_loss_cells_gt_0p01={len(source_recall_losses)}",
        },
        {
            "step": 5,
            "gate": "per_predicate_violation_nonincrease",
            "passed": predicate_violation_pass,
            "decision": "pass" if predicate_violation_pass else "fail",
            "reason": f"predicate_violation_regressions={len(predicate_violation_regressions)}",
        },
        {
            "step": 5,
            "gate": "per_predicate_recall_not_large_loss",
            "passed": len(predicate_recall_losses) == 0,
            "decision": "pass" if len(predicate_recall_losses) == 0 else "fail",
            "reason": f"predicate_recall_loss_cells_gt_0p05={len(predicate_recall_losses)}",
        },
        {
            "step": 6,
            "gate": "strict_balanced_main_route",
            "passed": strict_balanced_pass,
            "decision": "promote" if strict_balanced_pass else "do_not_promote_as_balanced_main",
            "reason": "requires no violation regression, no large recall loss, and control collapse",
        },
        {
            "step": 6,
            "gate": "caveated_violation_control_route",
            "passed": violation_control_pass,
            "decision": "allow_caveated_route" if violation_control_pass else "keep_diagnostic",
            "reason": "allows route only as violation-control evidence when recall tradeoff remains",
        },
    ]
    if strict_balanced_pass:
        selected_path = "promote_relative_horizontal_to_main_validated_route"
    elif violation_control_pass:
        selected_path = "allow_relative_horizontal_as_caveated_frame_aware_violation_control_route"
    else:
        selected_path = "keep_relative_horizontal_as_diagnostic"

    return gate_rows, {
        "strict_balanced_main_route_pass": strict_balanced_pass,
        "violation_control_route_pass": violation_control_pass,
        "source_violation_regression_cells": len(source_violation_regressions),
        "source_recall_loss_cells_gt_0p01": len(source_recall_losses),
        "predicate_violation_regression_cells": len(predicate_violation_regressions),
        "predicate_recall_loss_cells_gt_0p05": len(predicate_recall_losses),
        "axis_sign_control_failure_cells": len(control_failures),
        "selected_path": selected_path,
        "promote_to_main_validated_route": strict_balanced_pass,
        "allow_caveated_violation_control_route": violation_control_pass,
    }


def markdown_table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    body = ["| " + " | ".join(str(row.get(col, "")) for col in cols) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def report_text(summary: dict[str, Any], gates: list[dict[str, Any]], comparisons: list[dict[str, Any]], family_rows: list[dict[str, Any]]) -> str:
    key_comparisons = [
        row
        for row in comparisons
        if row["level"] == "source_family"
        and row["comparison"] == "RH1_source_x_frame_score_minus_RH0_source_score"
        and int(row["K"]) in PROMOTION_K
    ]
    key_family = [
        row
        for row in family_rows
        if row["score_id"] in {"RH0_source_score", "RH1_source_x_frame_score", "RH3_source_x_axis_swap_control", "RH4_source_x_sign_flip_control"}
        and int(row["K"]) in PROMOTION_K
    ]
    return f"""# H002 Relative Horizontal Route-Specific Scorer

## Status

```text
status = {summary['status']}
validation_errors = {summary['validation_errors']}
selected_path = {summary['selected_path']}
strict_balanced_main_route_pass = {str(summary['strict_balanced_main_route_pass']).lower()}
violation_control_route_pass = {str(summary['violation_control_route_pass']).lower()}
promote_to_main_validated_route = {str(summary['promote_to_main_validated_route']).lower()}
```

## Gate Result

{markdown_table(gates, ['step', 'gate', 'passed', 'decision', 'reason'])}

## RH1 vs Source Baseline

{markdown_table(key_comparisons, ['source_id', 'K', 'delta_Recall@K', 'delta_Violation@K', 'recall_not_large_loss_0p01', 'violation_nonincrease'])}

## Source-Family Metrics

{markdown_table(key_family, ['source_id', 'score_id', 'K', 'Recall@K', 'Violation@K'])}

## Interpretation

`RH1_source_x_frame_score`는 `relative_horizontal`을 generic `S2_current_source_x_Ce`가 아니라 별도 frame-aware directional scorer로 재실험한 결과다.

판단:

- balanced main route 기준으로는 Recall loss가 남아 있어 즉시 승격하지 않는다.
- 다만 violation-control route 기준으로는 source-wide violation non-increase와 axis/sign control collapse를 만족하면 caveated route evidence로 사용할 수 있다.
- 따라서 paper main route 포함은 사용자가 선택할 수 있지만, 가장 방어적인 표현은 `main validated compatibility route`가 아니라 `frame-aware violation-control route`다.
"""


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    required = {
        "materialization_ce": args.materialization_dir / "model_safe_ce_view.jsonl",
        "materialization_rank": args.materialization_dir / "source_rank_view.jsonl",
        "materialization_hidden": args.materialization_dir / "hidden_metric_manifest.jsonl",
        "frame_audit_summary": args.frame_audit_dir / "summary.json",
        "frame_audit_errors": args.frame_audit_dir / "validation_errors.jsonl",
    }
    for name, path in required.items():
        if not path.exists():
            errors.append({"error": "missing_required_input", "name": name, "path": rel_path(repo_root, path)})
    if required["frame_audit_errors"].exists() and required["frame_audit_errors"].read_text(encoding="utf-8").strip():
        errors.append({"error": "frame_audit_validation_errors_not_empty"})

    if errors:
        summary = {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS_ERROR,
            "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "validation_errors": len(errors),
            "selected_path": "blocked_missing_inputs",
            "promote_to_main_validated_route": False,
            "next_todo": "resolve_relative_horizontal_route_scorer_errors",
        }
        write_json(out / "summary.json", summary)
        with (out / "validation_errors.jsonl").open("w", encoding="utf-8") as handle:
            for error in errors:
                handle.write(json.dumps(error, ensure_ascii=False, sort_keys=True) + "\n")
        write_csv(out / "promotion_gate.csv", [])
        write_text(out / "report.md", report_text(summary, [], [], []))
        return 1

    frame_audit_summary = json.loads(required["frame_audit_summary"].read_text(encoding="utf-8"))
    records, denom_by_group, denom_by_predicate_group = load_relative_records(args.materialization_dir)
    source_family_rows = remap_score_rows(deterministic_frame_metrics(records, denom_by_group))
    selected_rows = selected_predictions(records)
    source_predicate_rows = predicate_metrics(selected_rows, denom_by_predicate_group)
    comparisons = comparison_rows([*source_family_rows, *source_predicate_rows])
    gates, gate_summary = summarize_gate(comparisons)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_READY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "validation_errors": 0,
        "input_frame_audit_status": frame_audit_summary.get("status"),
        "route_family": "relative_horizontal",
        "relations": PREDICATES,
        "source_rows_scored": len(records),
        "score_ids": RH_SCORE_IDS,
        "main_candidate_score": "RH1_source_x_frame_score",
        **gate_summary,
        "outputs": {
            "frame_protocol": rel_path(repo_root, out / "frame_protocol.csv"),
            "score_manifest": rel_path(repo_root, out / "score_manifest.json"),
            "source_family_metrics": rel_path(repo_root, out / "source_family_metrics.csv"),
            "source_predicate_metrics": rel_path(repo_root, out / "source_predicate_metrics.csv"),
            "selected_predictions": rel_path(repo_root, out / "selected_predictions.jsonl"),
            "comparison_metrics": rel_path(repo_root, out / "comparison_metrics.csv"),
            "promotion_gate": rel_path(repo_root, out / "promotion_gate.csv"),
            "report": rel_path(repo_root, out / "report.md"),
            "summary": rel_path(repo_root, out / "summary.json"),
            "validation_errors": rel_path(repo_root, out / "validation_errors.jsonl"),
        },
        "next_todo": "h002_relative_horizontal_main_route_inclusion_decision_after_route_scorer",
    }

    score_manifest = {
        "schema_version": f"{SCHEMA_VERSION}_score_manifest",
        "score_ids": RH_SCORE_IDS,
        "main_candidate_score": "RH1_source_x_frame_score",
        "score_definitions": {
            "RH0_source_score": "source relation confidence only",
            "RH1_source_x_frame_score": "source_score * sigmoid(8 * predicate_aligned_world_xy_residual)",
            "RH2_frame_score_only": "sigmoid(8 * predicate_aligned_world_xy_residual)",
            "RH3_source_x_axis_swap_control": "source_score * axis-swapped frame residual",
            "RH4_source_x_sign_flip_control": "source_score * sign-flipped frame residual",
            "RH5_axis_swap_only_control": "axis-swapped frame residual only",
            "RH6_sign_flip_only_control": "sign-flipped frame residual only",
        },
        "frame_protocol": "dataset_world_xy_reference_frame_from_3rscan_obb_centroids",
        "relations": PREDICATES,
        "normalization": "no learned normalization; residual maps through frozen sigmoid scale 8.0",
        "no_tuning_policy": "no validation-result-dependent threshold/lambda/scale tuning in this stage",
    }

    write_csv(out / "frame_protocol.csv", build_frame_protocol_rows())
    write_json(out / "score_manifest.json", score_manifest)
    write_csv(out / "source_family_metrics.csv", source_family_rows)
    write_csv(out / "source_predicate_metrics.csv", source_predicate_rows)
    write_jsonl(out / "selected_predictions.jsonl", selected_rows)
    write_csv(out / "comparison_metrics.csv", comparisons)
    write_csv(out / "promotion_gate.csv", gates)
    write_json(out / "summary.json", summary)
    write_text(out / "validation_errors.jsonl", "")
    write_text(out / "report.md", report_text(summary, gates, comparisons, source_family_rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
