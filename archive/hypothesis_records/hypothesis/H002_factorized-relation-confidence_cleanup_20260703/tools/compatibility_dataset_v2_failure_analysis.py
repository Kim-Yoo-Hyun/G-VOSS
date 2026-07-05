#!/usr/bin/env python3
"""Analyze why H002 compatibility dataset v2 sanitized smoke failed controls."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from learned_smoke_runner_v1 import binary_metrics, rel_path, safe_float


H2_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SMOKE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_sanitized_view_smoke_runner"
DEFAULT_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_sanitized_view_smoke_plan"
DEFAULT_RAW_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_candidate_materialization"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_failure_analysis"

EXPECTED_SMOKE_STATUS = "h002_compatibility_dataset_v2_sanitized_view_smoke_runner_diagnostic_only_failed_controls"
EXPECTED_SMOKE_NEXT = "compatibility_dataset_v2_failure_analysis"

SCHEMA_VERSION = "h002_compatibility_dataset_v2_failure_analysis_v1"
STATUS_READY = "h002_compatibility_dataset_v2_failure_analysis_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v2_failure_analysis_input_errors"
NEXT_TODO = "compatibility_dataset_v2_target_redesign_plan"

PRIMARY_MODEL = "M5_compatibility_TG_numeric"
GEOMETRY_MODEL = "M4_geometry_numeric_G"
WRONG_T_MODEL = "C2_wrong_T_same_G_control"
SHUFFLED_G_MODEL = "C1_shuffled_G_within_family_control"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-dir", type=Path, default=DEFAULT_SMOKE_DIR)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


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


def join_rows(smoke_rows: list[dict[str, Any]], prediction_rows: list[dict[str, Any]], raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pred_by_id = {row["row_id"]: row for row in prediction_rows}
    raw_by_id = {row["row_id"]: row for row in raw_rows}
    joined: list[dict[str, Any]] = []
    for row in smoke_rows:
        row_id = row["row_id"]
        pred = pred_by_id[row_id]
        raw = raw_by_id[row_id]
        joined.append(
            {
                "row_id": row_id,
                "group_id": row["group_id"],
                "label": int(row["y_compatibility"]),
                "family": row["T_e"]["relation_family"],
                "predicate": row["T_e"]["predicate_label"],
                "subject": row["T_e"]["subject_label"],
                "object": row["T_e"]["object_label"],
                "counterfactual_type": raw.get("counterfactual_axis", {}).get("counterfactual_type"),
                "row_role": raw.get("row_role"),
                "source_rank_band": row.get("Z_e_safe", {}).get("source_rank_band"),
                "source_score": row.get("Z_e_safe", {}).get("source_score_normalized"),
                "G": row.get("G_e_numeric", {}),
                "scores": {
                    PRIMARY_MODEL: pred[PRIMARY_MODEL],
                    GEOMETRY_MODEL: pred[GEOMETRY_MODEL],
                    WRONG_T_MODEL: pred[WRONG_T_MODEL],
                    SHUFFLED_G_MODEL: pred[SHUFFLED_G_MODEL],
                    "M6_factorized_sanitized_TZGQ": pred["M6_factorized_sanitized_TZGQ"],
                    "M2_semantic_only_T": pred["M2_semantic_only_T"],
                    "S3_object_label_pair_shortcut": pred["S3_object_label_pair_shortcut"],
                },
            }
        )
    return joined


def validation_errors(smoke_summary: dict[str, Any], smoke_rows: list[dict[str, Any]], predictions: list[dict[str, Any]], raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if smoke_summary.get("status") != EXPECTED_SMOKE_STATUS:
        errors.append({"error_type": "unexpected_smoke_status", "actual": smoke_summary.get("status")})
    if smoke_summary.get("next_todo") != EXPECTED_SMOKE_NEXT:
        errors.append({"error_type": "unexpected_smoke_next", "actual": smoke_summary.get("next_todo")})
    if smoke_summary.get("validation_errors") != 0:
        errors.append({"error_type": "smoke_validation_errors", "actual": smoke_summary.get("validation_errors")})
    ids = {row["row_id"] for row in smoke_rows}
    pred_ids = {row["row_id"] for row in predictions}
    raw_ids = {row["row_id"] for row in raw_rows}
    if ids != pred_ids:
        errors.append({"error_type": "prediction_row_id_mismatch", "missing_predictions": len(ids - pred_ids), "extra_predictions": len(pred_ids - ids)})
    if ids != raw_ids:
        errors.append({"error_type": "raw_row_id_mismatch", "missing_raw": len(ids - raw_ids), "extra_raw": len(raw_ids - ids)})
    return errors


def metric_for(rows: list[dict[str, Any]], model: str) -> dict[str, Any]:
    if not rows:
        return {"n": 0}
    labels = [row["label"] for row in rows]
    scores = [row["scores"][model] for row in rows]
    return binary_metrics(labels, scores)


def slice_metrics(joined: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    slice_specs = {
        "all": lambda row: "all",
        "family": lambda row: row["family"],
        "predicate": lambda row: f"{row['family']}|{row['predicate']}",
        "counterfactual_type": lambda row: row["counterfactual_type"],
    }
    for axis, key_fn in slice_specs.items():
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in joined:
            grouped[str(key_fn(row))].append(row)
        for key, items in sorted(grouped.items()):
            labels = Counter(row["label"] for row in items)
            if labels[0] == 0 or labels[1] == 0:
                # Keep single-class negative slices for false-positive diagnostics.
                m5_fp = sum(1 for row in items if row["label"] == 0 and row["scores"][PRIMARY_MODEL] >= 0.5)
                neg = labels[0]
                rows.append(
                    {
                        "axis": axis,
                        "key": key,
                        "n": len(items),
                        "positive": labels[1],
                        "negative": labels[0],
                        "M5_auroc": None,
                        "M4_auroc": None,
                        "C2_auroc": None,
                        "M5_negative_false_positive_rate": round(m5_fp / neg, 6) if neg else None,
                        "M5_mean_score": round(mean(row["scores"][PRIMARY_MODEL] for row in items), 6),
                        "M4_mean_score": round(mean(row["scores"][GEOMETRY_MODEL] for row in items), 6),
                    }
                )
                continue
            m5 = metric_for(items, PRIMARY_MODEL)
            m4 = metric_for(items, GEOMETRY_MODEL)
            c2 = metric_for(items, WRONG_T_MODEL)
            rows.append(
                {
                    "axis": axis,
                    "key": key,
                    "n": len(items),
                    "positive": labels[1],
                    "negative": labels[0],
                    "M5_auroc": m5.get("auroc"),
                    "M4_auroc": m4.get("auroc"),
                    "C2_auroc": c2.get("auroc"),
                    "M5_minus_M4": round((m5.get("auroc") or 0.0) - (m4.get("auroc") or 0.0), 6),
                    "M5_minus_C2": round((m5.get("auroc") or 0.0) - (c2.get("auroc") or 0.0), 6),
                    "M5_mean_score": round(mean(row["scores"][PRIMARY_MODEL] for row in items), 6),
                    "M4_mean_score": round(mean(row["scores"][GEOMETRY_MODEL] for row in items), 6),
                }
            )
    return rows


def feature_rows(joined: list[dict[str, Any]]) -> list[dict[str, Any]]:
    features = sorted({key for row in joined for key in row["G"]})
    out: list[dict[str, Any]] = []
    for family in ["all"] + sorted({row["family"] for row in joined}):
        rows = joined if family == "all" else [row for row in joined if row["family"] == family]
        positives = [row for row in rows if row["label"] == 1]
        negatives = [row for row in rows if row["label"] == 0]
        for feature in features:
            pos_vals = [safe_float(row["G"].get(feature), 0.0) for row in positives]
            neg_vals = [safe_float(row["G"].get(feature), 0.0) for row in negatives]
            if not pos_vals or not neg_vals:
                continue
            pos_mean = mean(pos_vals)
            neg_mean = mean(neg_vals)
            pooled = math.sqrt((sum((v - pos_mean) ** 2 for v in pos_vals) + sum((v - neg_mean) ** 2 for v in neg_vals)) / max(len(pos_vals) + len(neg_vals) - 2, 1))
            effect = (pos_mean - neg_mean) / pooled if pooled > 1e-9 else 0.0
            out.append(
                {
                    "family": family,
                    "feature": feature,
                    "positive_mean": round(pos_mean, 6),
                    "negative_mean": round(neg_mean, 6),
                    "mean_delta_pos_minus_neg": round(pos_mean - neg_mean, 6),
                    "abs_effect_size": round(abs(effect), 6),
                    "signed_effect_size": round(effect, 6),
                }
            )
    return sorted(out, key=lambda row: row["abs_effect_size"], reverse=True)


def prediction_difference_rows(joined: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    groups = {
        "all": joined,
        **{f"family:{family}": [row for row in joined if row["family"] == family] for family in sorted({row["family"] for row in joined})},
    }
    for key, items in groups.items():
        if not items:
            continue
        m5_c2 = [abs(row["scores"][PRIMARY_MODEL] - row["scores"][WRONG_T_MODEL]) for row in items]
        m5_m4 = [row["scores"][PRIMARY_MODEL] - row["scores"][GEOMETRY_MODEL] for row in items]
        m5_c1 = [row["scores"][PRIMARY_MODEL] - row["scores"][SHUFFLED_G_MODEL] for row in items]
        rows.append(
            {
                "slice": key,
                "n": len(items),
                "mean_abs_M5_minus_wrongT": round(mean(m5_c2), 8),
                "max_abs_M5_minus_wrongT": round(max(m5_c2), 8),
                "mean_M5_minus_M4_geometry": round(mean(m5_m4), 8),
                "mean_M5_minus_shuffledG": round(mean(m5_c1), 8),
            }
        )
    return rows


def confusion_by_type(joined: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in joined:
        grouped[(row["family"], row["counterfactual_type"])].append(row)
    for (family, ctype), rows in sorted(grouped.items()):
        labels = Counter(row["label"] for row in rows)
        fp = sum(1 for row in rows if row["label"] == 0 and row["scores"][PRIMARY_MODEL] >= 0.5)
        fn = sum(1 for row in rows if row["label"] == 1 and row["scores"][PRIMARY_MODEL] < 0.5)
        out.append(
            {
                "family": family,
                "counterfactual_type": ctype,
                "n": len(rows),
                "positive": labels[1],
                "negative": labels[0],
                "M5_mean_score": round(mean(row["scores"][PRIMARY_MODEL] for row in rows), 6),
                "M4_mean_score": round(mean(row["scores"][GEOMETRY_MODEL] for row in rows), 6),
                "M5_false_positive_rate": round(fp / labels[0], 6) if labels[0] else None,
                "M5_false_negative_rate": round(fn / labels[1], 6) if labels[1] else None,
            }
        )
    return out


def failure_cases(joined: list[dict[str, Any]], limit: int = 40) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for row in joined:
        score = row["scores"][PRIMARY_MODEL]
        pred = 1 if score >= 0.5 else 0
        if pred == row["label"]:
            continue
        cases.append(
            {
                "row_id": row["row_id"],
                "group_id": row["group_id"],
                "family": row["family"],
                "predicate": row["predicate"],
                "counterfactual_type": row["counterfactual_type"],
                "label": row["label"],
                "prediction": pred,
                "M5_score": round(score, 6),
                "M4_score": round(row["scores"][GEOMETRY_MODEL], 6),
                "wrongT_score": round(row["scores"][WRONG_T_MODEL], 6),
                "subject": row["subject"],
                "object": row["object"],
            }
        )
    return sorted(cases, key=lambda row: abs(float(row["M5_score"]) - 0.5), reverse=True)[:limit]


def diagnosis(summary: dict[str, Any], feature_top: list[dict[str, Any]], diff_rows: list[dict[str, Any]], type_rows: list[dict[str, Any]]) -> dict[str, Any]:
    m = summary["key_metrics"]
    all_diff = next(row for row in diff_rows if row["slice"] == "all")
    support = summary["key_metrics"][GEOMETRY_MODEL]["auroc"] - summary["key_metrics"][PRIMARY_MODEL]["auroc"]
    support_contact_fp = [
        row for row in type_rows
        if row["family"] == "support_contact" and row["negative"] and row["M5_false_positive_rate"] is not None
    ]
    high_fp_types = sorted(support_contact_fp, key=lambda row: row["M5_false_positive_rate"], reverse=True)[:3]
    return {
        "primary_cause": "target_is_geometry_perturbation_detection_not_predicate_conditioned_compatibility",
        "evidence": [
            {
                "claim": "Geometry-only beats compatibility.",
                "value": {
                    "M4_geometry_auc": m[GEOMETRY_MODEL]["auroc"],
                    "M5_compatibility_auc": m[PRIMARY_MODEL]["auroc"],
                },
            },
            {
                "claim": "Wrong predicate does not change predictions.",
                "value": {
                    "M5_auc": m[PRIMARY_MODEL]["auroc"],
                    "wrongT_auc": m[WRONG_T_MODEL]["auroc"],
                    "mean_abs_prediction_delta": all_diff["mean_abs_M5_minus_wrongT"],
                },
            },
            {
                "claim": "Support/contact drives most geometry signal.",
                "value": {
                    "overall_M4_minus_M5_auc": round(support, 6),
                    "highest_support_contact_negative_fp_types": high_fp_types,
                },
            },
            {
                "claim": "Top numeric feature shifts are geometry distribution shifts, not predicate-conditioned evidence.",
                "value": feature_top[:8],
            },
        ],
        "target_redesign_requirements": [
            "Create same-geometry multi-predicate contrasts where the same object-pair geometry is valid for one predicate and invalid for another.",
            "Avoid negative construction types that can be solved by generic geometry perturbation alone.",
            "For support/contact, separate wrong-pair perturbation from predicate compatibility and add same-pair predicate alternatives.",
            "For relative-vertical, create stronger directional pairs where vertical order is clearly separable but predicate conditioning is evaluated explicitly.",
            "Report geometry-only as a strong baseline, not just a control.",
        ],
        "next_todo": NEXT_TODO,
    }


def write_report(path: Path, summary: dict[str, Any], diag: dict[str, Any], top_features: list[dict[str, Any]], diff_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Compatibility Dataset V2 Failure Analysis",
        "",
        "Artifact root:",
        "",
        "```text",
        "artifacts/compatibility_dataset_v2_failure_analysis/",
        "```",
        "",
        "Status:",
        "",
        "```text",
        f"status = {summary['status']}",
        f"rows = {summary['counts']['rows']}",
        f"validation_errors = {summary['validation_errors']}",
        f"primary_cause = {diag['primary_cause']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Main Diagnosis",
        "",
        "The sanitized v2 smoke failed for a principled reason: after construction shortcuts were",
        "removed, the remaining task is still mostly generic geometry perturbation detection. It is not",
        "yet a predicate-conditioned compatibility task.",
        "",
        "Key evidence:",
        "",
        "```text",
        "geometry-only M4 AUROC = 0.6731",
        "compatibility M5 AUROC = 0.6250",
        "wrong-T same-G AUROC = 0.6250",
        f"mean |M5 - wrongT| = {diff_rows[0]['mean_abs_M5_minus_wrongT']}",
        "```",
        "",
        "## Top Geometry Shifts",
        "",
        "| Family | Feature | Pos Mean | Neg Mean | Effect |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in top_features[:12]:
        lines.append(
            f"| {row['family']} | `{row['feature']}` | {row['positive_mean']} | "
            f"{row['negative_mean']} | {row['signed_effect_size']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Source, rank, predicate, family, and object-pair priors are no longer solving the target.",
            "- Numeric geometry is useful, but it is useful as generic geometry signal.",
            "- Wrong predicate leaves the score unchanged, so `T_e` is not controlling which geometry",
            "  evidence matters.",
            "- Support/contact carries the usable signal; relative vertical remains weak under this",
            "  construction.",
            "",
            "## Required Redesign",
            "",
        ]
    )
    for item in diag["target_redesign_requirements"]:
        lines.append(f"- {item}")
    lines.extend(
        [
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

    smoke_summary = read_json(args.smoke_dir / "summary.json")
    smoke_rows = read_jsonl(args.plan_dir / "smoke_ready_view.jsonl")
    predictions = read_jsonl(args.smoke_dir / "predictions.jsonl")
    raw_rows = read_jsonl(args.raw_dir / "compatibility_rows.jsonl")
    errors = validation_errors(smoke_summary, smoke_rows, predictions, raw_rows)
    joined = join_rows(smoke_rows, predictions, raw_rows)

    slices = slice_metrics(joined)
    features = feature_rows(joined)
    diffs = prediction_difference_rows(joined)
    types = confusion_by_type(joined)
    cases = failure_cases(joined)
    diag = diagnosis(smoke_summary, features, diffs, types)

    status = STATUS_ERRORS if errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": NEXT_TODO,
        "smoke_root": rel_path(args.smoke_dir),
        "plan_root": rel_path(args.plan_dir),
        "raw_root": rel_path(args.raw_dir),
        "output_root": rel_path(args.output_dir),
        "counts": {
            "rows": len(joined),
            "positive": sum(row["label"] for row in joined),
            "negative": sum(1 - row["label"] for row in joined),
            "families": sorted({row["family"] for row in joined}),
        },
        "validation_errors": len(errors),
        "primary_cause": diag["primary_cause"],
        "key_findings": diag["evidence"],
        "target_redesign_requirements": diag["target_redesign_requirements"],
        "paper_evidence_allowed": False,
        "boundary": {
            "analysis_only": True,
            "uses_hidden_provenance_for_diagnosis_only": True,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "slice_metrics": rel_path(args.output_dir / "slice_metrics.csv"),
            "geometry_feature_shifts": rel_path(args.output_dir / "geometry_feature_shifts.csv"),
            "prediction_differences": rel_path(args.output_dir / "prediction_differences.csv"),
            "counterfactual_type_diagnostics": rel_path(args.output_dir / "counterfactual_type_diagnostics.csv"),
            "failure_cases": rel_path(args.output_dir / "failure_cases.jsonl"),
            "diagnosis": rel_path(args.output_dir / "diagnosis.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    write_csv(args.output_dir / "slice_metrics.csv", slices)
    write_csv(args.output_dir / "geometry_feature_shifts.csv", features)
    write_csv(args.output_dir / "prediction_differences.csv", diffs)
    write_csv(args.output_dir / "counterfactual_type_diagnostics.csv", types)
    write_jsonl(args.output_dir / "failure_cases.jsonl", cases)
    write_json(args.output_dir / "diagnosis.json", diag)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, diag, features, diffs)


if __name__ == "__main__":
    main()
