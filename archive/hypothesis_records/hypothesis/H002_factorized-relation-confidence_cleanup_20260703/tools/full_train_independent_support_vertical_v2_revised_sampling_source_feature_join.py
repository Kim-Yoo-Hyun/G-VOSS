#!/usr/bin/env python3
"""Join deployable source features for the revised all-label-ready strict slice."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_STRICT_SLICE = (
    RGA_ROOT
    / "independent_support_vertical_v2_revised_sampling_target_independence_audit_all_label_ready_user_confirmed"
    / "target_slices/relation_reliability_revised_sampling_user_confirmed_target/rank_band_balanced_revised_sampling.jsonl"
)
DEFAULT_AUDIT_SUMMARY = (
    RGA_ROOT
    / "independent_support_vertical_v2_revised_sampling_target_independence_audit_all_label_ready_user_confirmed/summary.json"
)
DEFAULT_CANDIDATE_POOL = RGA_ROOT / "controlled_label_mining/candidate_pool.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_source_feature_join_all_label_ready"

TARGET_MODE = "rank_band_balanced_revised_sampling"

MAIN_INPUT_VIEWS = [
    "semantic_only",
    "geometry_only",
    "semantic_plus_geometry",
    "semantic_geometry_coverage",
    "factorized_reliability_posterior",
]

DIAGNOSTIC_INPUT_VIEWS = [
    "coverage_only",
    "semantic_score_only",
    "rank_only",
    "p_geom_valid_only",
    "residual_reliability_model",
]

FORBIDDEN_MODEL_INPUT_FRAGMENTS = [
    "review",
    "hidden",
    "packet",
    "path",
    "target",
    "label",
    "role",
    "queue",
    "rank_band",
    "geometry_status",
    "match_status",
    "audit",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict-slice", type=Path, default=DEFAULT_STRICT_SLICE)
    parser.add_argument("--audit-summary", type=Path, default=DEFAULT_AUDIT_SUMMARY)
    parser.add_argument("--candidate-pool", type=Path, default=DEFAULT_CANDIDATE_POOL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
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


def safe_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        output = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(output) or math.isinf(output):
        return default
    return output


def rank_block(rank_value: Any) -> dict[str, float]:
    rank = max(safe_float(rank_value, 1.0), 1.0)
    return {
        "semantic_rank": rank,
        "semantic_rank_log": math.log1p(rank),
        "semantic_rank_inverse": 1.0 / rank,
    }


def candidate_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_prediction: dict[str, dict[str, Any]] = {}
    for row in rows:
        prediction_id = str(row.get("prediction_id") or "")
        if prediction_id:
            by_prediction[prediction_id] = row
    return by_prediction


def source_values(slice_row: dict[str, Any], candidate: dict[str, Any]) -> dict[str, float]:
    source_scores = (
        slice_row.get("deployable_evidence_after_label_lock", {})
        .get("source_semantic_and_geometry_scores_hidden_from_labeler_until_lock", {})
    )
    semantic_norm = safe_float(candidate.get("semantic_score_norm"), safe_float(source_scores.get("semantic_score_norm"), 0.0))
    semantic_raw = safe_float(candidate.get("semantic_score_raw"), semantic_norm)
    semantic_rank = safe_float(candidate.get("semantic_rank"), safe_float(source_scores.get("semantic_rank"), 1.0))
    p_geom = safe_float(candidate.get("p_geom_valid"), safe_float(source_scores.get("p_geom_valid"), 0.5))
    consistency = safe_float(candidate.get("consistency_score"), p_geom)
    reported_disagreement = safe_float(candidate.get("disagreement_score"), abs(semantic_norm - p_geom))
    underconfidence = safe_float(candidate.get("underconfidence_score"), max(0.0, p_geom - semantic_norm))
    overconfidence = max(0.0, semantic_norm - p_geom)
    coverage = slice_row.get("deployable_evidence_after_label_lock", {}).get("coverage_evidence", {})
    packet_ready = 1.0 if str(coverage.get("evidence_packet_status") or "") == "ready" else 0.0
    return {
        "semantic_score_norm": semantic_norm,
        "semantic_score_raw": semantic_raw,
        "semantic_rank": semantic_rank,
        "p_geom_valid": p_geom,
        "consistency_score": consistency,
        "reported_disagreement_score": reported_disagreement,
        "underconfidence_score": underconfidence,
        "overconfidence_score": overconfidence,
        "coverage_evidence_ready": packet_ready,
        "coverage_has_source_features": 1.0,
        "coverage_has_semantic_score": 1.0,
        "coverage_has_geometry_score": 1.0,
        "coverage_has_consistency_score": 1.0 if "consistency_score" in candidate else 0.0,
    }


def build_baseline_inputs(values: dict[str, float]) -> dict[str, dict[str, float]]:
    semantic = values["semantic_score_norm"]
    p_geom = values["p_geom_valid"]
    consistency = values["consistency_score"]
    semantic_block = {
        "semantic_score_raw": values["semantic_score_raw"],
        "semantic_score_norm": semantic,
        "negative_semantic_score_norm": 1.0 - semantic,
        **rank_block(values["semantic_rank"]),
    }
    geometry_block = {
        "p_geom_valid": p_geom,
        "p_geom_invalid": 1.0 - p_geom,
        "consistency_score": consistency,
    }
    coverage_block = {
        "coverage_evidence_ready": values["coverage_evidence_ready"],
        "coverage_has_source_features": values["coverage_has_source_features"],
        "coverage_has_semantic_score": values["coverage_has_semantic_score"],
        "coverage_has_geometry_score": values["coverage_has_geometry_score"],
        "coverage_has_consistency_score": values["coverage_has_consistency_score"],
    }
    residual_block = {
        "absolute_disagreement": abs(semantic - p_geom),
        "reported_disagreement_score": values["reported_disagreement_score"],
        "semantic_minus_geometry": semantic - p_geom,
        "geometry_minus_semantic": p_geom - semantic,
        "underconfidence_score": values["underconfidence_score"],
        "overconfidence_score": values["overconfidence_score"],
        "semantic_x_geometry": semantic * p_geom,
        "semantic_x_consistency": semantic * consistency,
        "geometry_x_consistency": p_geom * consistency,
    }
    return {
        "semantic_only": semantic_block,
        "geometry_only": geometry_block,
        "coverage_only": coverage_block,
        "semantic_plus_geometry": {**semantic_block, **geometry_block},
        "semantic_geometry_coverage": {**semantic_block, **geometry_block, **coverage_block},
        "factorized_reliability_posterior": {**semantic_block, **geometry_block, **coverage_block, **residual_block},
        "residual_reliability_model": {**semantic_block, **geometry_block, **residual_block},
        "semantic_score_only": {"semantic_score_norm": semantic},
        "rank_only": rank_block(values["semantic_rank"]),
        "p_geom_valid_only": {"p_geom_valid": p_geom},
    }


def identity(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "prediction_id": row["prediction_id"],
        "blind_review_id": row["blind_review_id"],
        "scan_id": row["scan_id"],
        "subgraph_id": row["subgraph_id"],
        "subject_id": row["subject_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "object_id": row["object_id"],
        "object_label": row["object_label"],
    }


def posterior_row(slice_row: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    values = source_values(slice_row, candidate)
    return {
        "schema_version": "h002_support_vertical_v2_revised_sampling_source_feature_join_row_v1",
        "record_type": "h002_support_vertical_v2_revised_sampling_posterior_ready_row",
        "identity": identity(slice_row),
        "baseline_inputs": build_baseline_inputs(values),
        "target": {
            "target_mode": TARGET_MODE,
            "target_name": slice_row["target_name"],
            "y": int(slice_row["target_y"]),
            "sample_weight": 1.0,
            "target_use": slice_row.get("target_use"),
            "target_reason": slice_row.get("target_reason"),
            "target_slice_name": slice_row.get("target_slice_name"),
            "target_slice_reason": slice_row.get("target_slice_reason"),
            "balanced_keys": slice_row.get("balanced_keys", []),
            "audit_selection_only": bool(slice_row.get("audit_selection_only")),
            "allowed_use": "train-only controlled posterior smoke",
            "paper_locked": False,
        },
        "provenance": {
            "split_policy": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "source_feature_pool": "controlled_label_mining/candidate_pool.jsonl",
            "target_slice": "rank_band_balanced_revised_sampling",
            "user_confirmed_workflow_labels": True,
            "hidden_metadata_as_model_input": False,
            "review_fields_as_model_input": False,
            "target_labels_as_model_input": False,
            "packet_paths_as_model_input": False,
            "multi_view_as_model_input": False,
        },
    }


def feature_leakage_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    leakage: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows, start=1):
        for view_name, features in row.get("baseline_inputs", {}).items():
            for feature_name in features:
                lowered = feature_name.lower()
                for fragment in FORBIDDEN_MODEL_INPUT_FRAGMENTS:
                    if fragment in lowered:
                        leakage.append(
                            {
                                "row_index": row_index,
                                "prediction_id": row["identity"]["prediction_id"],
                                "view": view_name,
                                "feature_name": feature_name,
                                "forbidden_fragment": fragment,
                            }
                        )
    return leakage


def validate_rows(rows: list[dict[str, Any]], slice_rows: list[dict[str, Any]], candidate_matches: int) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(rows) != len(slice_rows):
        errors.append({"error_type": "posterior_row_count_mismatch", "posterior_rows": len(rows), "slice_rows": len(slice_rows)})
    if candidate_matches != len(slice_rows):
        errors.append({"error_type": "candidate_pool_match_count_mismatch", "matches": candidate_matches, "slice_rows": len(slice_rows)})
    seen = set()
    for row_number, row in enumerate(rows, start=1):
        prediction_id = row.get("identity", {}).get("prediction_id")
        if prediction_id in seen:
            errors.append({"error_type": "duplicate_prediction_id", "row_number": row_number, "prediction_id": prediction_id})
        seen.add(prediction_id)
        if row.get("target", {}).get("y") not in {0, 1}:
            errors.append({"error_type": "non_binary_target", "row_number": row_number, "prediction_id": prediction_id})
        baseline_inputs = row.get("baseline_inputs", {})
        for view in [*MAIN_INPUT_VIEWS, *DIAGNOSTIC_INPUT_VIEWS]:
            if view not in baseline_inputs:
                errors.append({"error_type": "missing_input_view", "row_number": row_number, "prediction_id": prediction_id, "view": view})
        for forbidden_top in [
            "audit_only_user_confirmed_review_fields",
            "hidden_audit_metadata_post_label_only",
            "audit_packet_paths_not_model_input",
        ]:
            if forbidden_top in row:
                errors.append({"error_type": "forbidden_top_level_field_present", "row_number": row_number, "prediction_id": prediction_id, "field": forbidden_top})
    return errors


def summarize_feature_ranges(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    values_by_name: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        for view, features in row["baseline_inputs"].items():
            for name, value in features.items():
                values_by_name.setdefault((view, name), []).append(safe_float(value))
    outputs = []
    for (view, name), values in sorted(values_by_name.items()):
        outputs.append(
            {
                "view": view,
                "feature": name,
                "rows": len(values),
                "min": min(values) if values else None,
                "max": max(values) if values else None,
                "mean": sum(values) / len(values) if values else None,
            }
        )
    return outputs


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 Revised Sampling Source Feature Join",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage feature join.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Active target slice is `rank_band_balanced_revised_sampling`.",
        "- Review fields, hidden audit metadata, target labels, packet paths, and multi-view evidence are not model inputs.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| posterior-ready rows | {counts['posterior_ready_rows']} |",
        f"| positive | {counts['positive']} |",
        f"| negative | {counts['negative']} |",
        f"| candidate matches | {counts['candidate_pool_matches']} |",
        f"| feature leakage hits | {counts['feature_leakage_hits']} |",
        f"| validation errors | {counts['validation_errors']} |",
        "",
        "## Input Views",
        "",
        "| View | Type |",
        "| --- | --- |",
    ]
    for view in MAIN_INPUT_VIEWS:
        lines.append(f"| `{view}` | main |")
    for view in DIAGNOSTIC_INPUT_VIEWS:
        lines.append(f"| `{view}` | diagnostic |")
    lines.extend(["", "## Next TODO", "", f"`{summary['next_todo']}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    strict_slice_path = as_abs(args.strict_slice)
    audit_summary_path = as_abs(args.audit_summary)
    candidate_pool_path = as_abs(args.candidate_pool)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    strict_rows = read_jsonl(strict_slice_path)
    audit_summary = read_json(audit_summary_path)
    candidates = read_jsonl(candidate_pool_path)
    candidates_by_prediction = candidate_index(candidates)

    posterior_rows: list[dict[str, Any]] = []
    join_errors: list[dict[str, Any]] = []
    candidate_matches = 0
    for row_number, row in enumerate(strict_rows, start=1):
        prediction_id = str(row.get("prediction_id") or "")
        candidate = candidates_by_prediction.get(prediction_id)
        if candidate is None:
            join_errors.append({"error_type": "missing_candidate_pool_row", "row_number": row_number, "prediction_id": prediction_id})
            continue
        candidate_matches += 1
        posterior_rows.append(posterior_row(row, candidate))

    leakage = feature_leakage_rows(posterior_rows)
    validation_errors = validate_rows(posterior_rows, strict_rows, candidate_matches)
    validation_errors.extend(join_errors)
    validation_errors.extend({"error_type": "feature_leakage_hit", **item} for item in leakage)

    target_counts = Counter(row["target"]["y"] for row in posterior_rows)
    status = "full_train_independent_support_vertical_v2_revised_sampling_source_feature_join_ready"
    decision = "Posterior-ready feature table is ready for controlled smoke on the strict relation slice."
    next_todo = "revised_sampling_all_label_ready_controlled_posterior_smoke"
    if validation_errors:
        status = "full_train_independent_support_vertical_v2_revised_sampling_source_feature_join_errors"
        decision = "Fix source feature join errors before posterior smoke."
        next_todo = "fix_revised_sampling_all_label_ready_source_feature_join"

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "posterior_ready_rows": output_dir / "posterior_ready_rows.jsonl",
        "input_contract": output_dir / "input_contract.json",
        "feature_ranges": output_dir / "feature_ranges.csv",
        "feature_leakage": output_dir / "feature_leakage.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    input_contract = {
        "schema_version": "h002_support_vertical_v2_revised_sampling_input_contract_v1",
        "main_input_views": MAIN_INPUT_VIEWS,
        "diagnostic_input_views": DIAGNOSTIC_INPUT_VIEWS,
        "allowed_model_input_root": "baseline_inputs",
        "forbidden_as_model_input": [
            "review fields",
            "target labels",
            "hidden audit metadata",
            "packet paths",
            "multi-view evidence",
            "queue/role/rank-band construction axes",
            "predicate label/family categorical shortcuts",
        ],
        "feature_leakage_fragments_checked": FORBIDDEN_MODEL_INPUT_FRAGMENTS,
    }
    summary = {
        "schema_version": "h002_support_vertical_v2_revised_sampling_source_feature_join_summary_v1",
        "status": status,
        "created_at": created_at,
        "decision": decision,
        "input_paths": {
            "strict_slice": rel_path(strict_slice_path),
            "audit_summary": rel_path(audit_summary_path),
            "candidate_pool": rel_path(candidate_pool_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "target_slice": TARGET_MODE,
            "audit_status": audit_summary.get("status"),
            "review_fields_as_model_input": False,
            "hidden_audit_metadata_as_model_input": False,
            "target_labels_as_model_input": False,
            "packet_paths_as_model_input": False,
            "multi_view_as_model_input": False,
            "predicate_label_as_model_input": False,
            "predicate_family_as_model_input": False,
        },
        "counts": {
            "strict_slice_rows": len(strict_rows),
            "candidate_pool_rows": len(candidates),
            "candidate_pool_matches": candidate_matches,
            "posterior_ready_rows": len(posterior_rows),
            "positive": target_counts[1],
            "negative": target_counts[0],
            "by_family": dict(sorted(Counter(row["identity"]["predicate_family"] for row in posterior_rows).items())),
            "by_predicate": dict(sorted(Counter(row["identity"]["predicate_label"] for row in posterior_rows).items())),
            "feature_leakage_hits": len(leakage),
            "validation_errors": len(validation_errors),
        },
        "input_contract": input_contract,
        "next_todo": next_todo,
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["input_contract"], input_contract)
    write_jsonl(output_paths["posterior_ready_rows"], posterior_rows)
    write_csv(output_paths["feature_ranges"], summarize_feature_ranges(posterior_rows))
    write_jsonl(output_paths["feature_leakage"], leakage)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    print(
        f"status={summary['status']} rows={counts['posterior_ready_rows']} "
        f"pos={counts['positive']} neg={counts['negative']} "
        f"candidate_matches={counts['candidate_pool_matches']} leakage={counts['feature_leakage_hits']} "
        f"errors={counts['validation_errors']} validation_used={summary['boundary']['validation_usage']} "
        f"test_used={summary['boundary']['test_usage']} next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
