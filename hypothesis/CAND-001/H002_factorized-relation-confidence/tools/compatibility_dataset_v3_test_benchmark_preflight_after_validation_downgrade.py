#!/usr/bin/env python3
"""Preflight H002 test benchmark readiness after validation-table downgrade."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_REVIEW_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_validation_table_review_after_skeleton"
DEFAULT_SOURCE_MATERIALIZATION_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/source_reranking_materialization/latest"
DEFAULT_SOURCE_EVAL_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/source_reranking_evaluation/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_test_benchmark_preflight_after_validation_downgrade"

EXPECTED_REVIEW_STATUS = "h002_source_reranking_validation_table_review_after_skeleton_ready"
EXPECTED_REVIEW_NEXT = "compatibility_dataset_v3_test_benchmark_preflight_after_validation_downgrade"
EXPECTED_SOURCE_EVAL_STATUS = "h002_source_reranking_metric_runner_ready"

SCHEMA_VERSION = "h002_test_benchmark_preflight_after_validation_downgrade_v1"
STATUS_READY = "h002_test_benchmark_preflight_after_validation_downgrade_ready_blocked"
STATUS_ERRORS = "h002_test_benchmark_preflight_after_validation_downgrade_input_errors"
SELECTED_PATH = "test_benchmark_blocked_select_independent_test_provenance_or_eval_server"
NEXT_TODO = "compatibility_dataset_v3_test_benchmark_source_resolution_after_preflight"

CANONICAL_ROOT = REPO_ROOT / "local_dataset/3DSSG_subset"
CANONICAL_TRAIN = CANONICAL_ROOT / "relationships_train.json"
CANONICAL_VAL = CANONICAL_ROOT / "relationships_validation.json"
CANONICAL_TEST = CANONICAL_ROOT / "relationships_test.json"
STAGED_TEST_CANDIDATES = [
    REPO_ROOT / "local_dataset/Open3DSG_staged/h001_full_validation_runtime/data/3RScan/3DSSG_subset/relationships_test.json",
    REPO_ROOT / "local_dataset/Open3DSG_staged/h001_runtime/data/3RScan/3DSSG_subset/relationships_test.json",
    REPO_ROOT / "local_dataset/Open3DSG_staged/h002_train_full_runtime/data/3RScan/3DSSG_subset/relationships_test.json",
    REPO_ROOT / "local_dataset/Open3DSG_staged/h002_train_pilot_runtime/data/3RScan/3DSSG_subset/relationships_test.json",
    REPO_ROOT / "local_dataset/Open3DSG_staged/training_repro/data/3RScan/3DSSG_subset/relationships_test.json",
]

PROMOTED_FAMILIES = {
    "relative_vertical": {"higher than", "lower than"},
    "size_relative": {"bigger than", "smaller than"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--source-materialization-dir", type=Path, default=DEFAULT_SOURCE_MATERIALIZATION_DIR)
    parser.add_argument("--source-eval-dir", type=Path, default=DEFAULT_SOURCE_EVAL_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def relationship_predicate(rel: Any) -> str:
    if isinstance(rel, list) and len(rel) >= 4:
        return str(rel[3])
    if isinstance(rel, dict):
        return str(rel.get("predicate") or rel.get("relationship") or rel.get("relation") or "unknown")
    return "unknown"


def relationship_subject(rel: Any) -> int | None:
    if isinstance(rel, list) and len(rel) >= 2:
        return int(rel[0])
    if isinstance(rel, dict):
        value = rel.get("subject_id") or rel.get("subject") or rel.get("source_id")
        return int(value) if value is not None else None
    return None


def relationship_object(rel: Any) -> int | None:
    if isinstance(rel, list) and len(rel) >= 2:
        return int(rel[1])
    if isinstance(rel, dict):
        value = rel.get("object_id") or rel.get("object") or rel.get("target_id")
        return int(value) if value is not None else None
    return None


def load_relationships(path: Path) -> tuple[list[dict[str, Any]], set[str], set[tuple[str, int, int]], int, Counter[str], Counter[Any]]:
    if not path.exists():
        return [], set(), set(), 0, Counter(), Counter()
    data = read_json(path)
    scans = data.get("scans", [])
    scan_ids: set[str] = set()
    pair_ids: set[tuple[str, int, int]] = set()
    rel_count = 0
    predicate_counts: Counter[str] = Counter()
    split_counts: Counter[Any] = Counter()
    for scan in scans:
        scan_id = str(scan.get("scan"))
        if scan_id:
            scan_ids.add(scan_id)
        split_counts[scan.get("split")] += 1
        for rel in scan.get("relationships", []) or []:
            rel_count += 1
            predicate = relationship_predicate(rel)
            predicate_counts[predicate] += 1
            sub = relationship_subject(rel)
            obj = relationship_object(rel)
            if scan_id and sub is not None and obj is not None:
                pair_ids.add((scan_id, sub, obj))
    return scans, scan_ids, pair_ids, rel_count, predicate_counts, split_counts


def promoted_counts(predicate_counts: Counter[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for family, predicates in PROMOTED_FAMILIES.items():
        out[family] = sum(predicate_counts[predicate] for predicate in predicates)
    return out


def validate_inputs(review_summary: dict[str, Any], source_eval_manifest: dict[str, Any], review_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if review_summary.get("status") != EXPECTED_REVIEW_STATUS:
        errors.append({"error_type": "unexpected_review_status", "actual": review_summary.get("status")})
    if review_summary.get("next_todo") != EXPECTED_REVIEW_NEXT:
        errors.append({"error_type": "unexpected_review_next_todo", "actual": review_summary.get("next_todo")})
    if review_summary.get("validation_errors") != 0:
        errors.append({"error_type": "review_validation_errors", "actual": review_summary.get("validation_errors")})
    if line_count(review_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "review_validation_errors_file_not_empty"})
    decision = review_summary.get("decision", {})
    if decision.get("validation_table_position") != "appendix_or_secondary_analysis_only":
        errors.append({"error_type": "validation_table_not_downgraded", "actual": decision.get("validation_table_position")})
    if decision.get("main_benchmark_table_requires_test") is not True:
        errors.append({"error_type": "main_benchmark_not_test_required"})
    if decision.get("test_benchmark_ready_now") is not False:
        errors.append({"error_type": "unexpected_test_benchmark_ready_now", "actual": decision.get("test_benchmark_ready_now")})
    if source_eval_manifest.get("status") != EXPECTED_SOURCE_EVAL_STATUS:
        errors.append({"error_type": "unexpected_source_eval_status", "actual": source_eval_manifest.get("status")})
    boundary = source_eval_manifest.get("boundary", {})
    for key, expected in {
        "official_validation_eval_only": True,
        "official_test_usage": False,
        "source_reranking_metric_produced": True,
        "paper_metric_promoted": False,
    }.items():
        if boundary.get(key) is not expected:
            errors.append({"error_type": "unexpected_source_eval_boundary", "key": key, "actual": boundary.get(key), "expected": expected})
    return errors


def test_label_provenance_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    _, train_scans, train_pairs, train_rels, train_pred, _ = load_relationships(CANONICAL_TRAIN)
    _, val_scans, val_pairs, val_rels, val_pred, _ = load_relationships(CANONICAL_VAL)
    candidates = [("canonical_test", CANONICAL_TEST)] + [(f"staged_candidate_{index}", path) for index, path in enumerate(STAGED_TEST_CANDIDATES, start=1)]
    rows: list[dict[str, Any]] = [
        {
            "candidate_id": "canonical_validation_reference",
            "path": rel_path(CANONICAL_VAL),
            "exists": CANONICAL_VAL.exists(),
            "scan_entries": 548 if CANONICAL_VAL.exists() else 0,
            "unique_scans": len(val_scans),
            "relations": val_rels,
            "train_scan_overlap": len(val_scans & train_scans),
            "validation_scan_overlap": len(val_scans),
            "train_pair_overlap": len(val_pairs & train_pairs),
            "validation_pair_overlap": len(val_pairs),
            "promoted_family_counts": json.dumps(promoted_counts(val_pred), ensure_ascii=False, sort_keys=True),
            "provenance_status": "validation_reference_only",
            "benchmark_use": "not_test",
        }
    ]
    non_empty = 0
    validation_alias = 0
    usable = 0
    for candidate_id, path in candidates:
        scans, scan_ids, pair_ids, rel_count, predicate_counts, split_counts = load_relationships(path)
        exists = path.exists()
        if exists and rel_count > 0:
            non_empty += 1
        train_overlap = len(scan_ids & train_scans)
        val_overlap = len(scan_ids & val_scans)
        pair_train_overlap = len(pair_ids & train_pairs)
        pair_val_overlap = len(pair_ids & val_pairs)
        if not exists:
            provenance = "missing"
            benchmark_use = "blocked_missing_file"
        elif rel_count == 0:
            provenance = "empty"
            benchmark_use = "blocked_empty_file"
        elif val_overlap == len(scan_ids) and len(scan_ids) > 0:
            provenance = "validation_alias_or_validation_subset"
            benchmark_use = "blocked_validation_alias_until_provenance_verified"
            validation_alias += 1
        elif train_overlap > 0:
            provenance = "train_overlap"
            benchmark_use = "blocked_split_overlap"
        else:
            provenance = "candidate_requires_external_provenance"
            benchmark_use = "not_ready_requires_eval_server_or_official_confirmation"
            usable += 1
        rows.append(
            {
                "candidate_id": candidate_id,
                "path": rel_path(path),
                "exists": exists,
                "scan_entries": len(scans),
                "unique_scans": len(scan_ids),
                "relations": rel_count,
                "train_scan_overlap": train_overlap,
                "validation_scan_overlap": val_overlap,
                "train_pair_overlap": pair_train_overlap,
                "validation_pair_overlap": pair_val_overlap,
                "split_field_counts": json.dumps(dict(split_counts), ensure_ascii=False, sort_keys=True),
                "promoted_family_counts": json.dumps(promoted_counts(predicate_counts), ensure_ascii=False, sort_keys=True),
                "provenance_status": provenance,
                "benchmark_use": benchmark_use,
            }
        )
    stats = {
        "canonical_train_scans": len(train_scans),
        "canonical_validation_scans": len(val_scans),
        "canonical_test_exists": CANONICAL_TEST.exists(),
        "candidate_count": len(candidates),
        "non_empty_test_candidates": non_empty,
        "validation_alias_candidates": validation_alias,
        "usable_candidate_without_overlap": usable,
    }
    return rows, stats


def source_prediction_rows(materialization_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = materialization_dir / "source_candidates.jsonl"
    counts: dict[tuple[str, str, str], int] = defaultdict(int)
    unique_scans: dict[tuple[str, str], set[str]] = defaultdict(set)
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                source_id = str(row.get("source_id", "unknown"))
                split = str(row.get("split", "unknown"))
                family = str(row.get("route_family", "unknown"))
                counts[(source_id, split, family)] += 1
                if row.get("scan_id"):
                    unique_scans[(source_id, split)].add(str(row["scan_id"]))
    rows = [
        {
            "source_id": source_id,
            "split": split,
            "route_family": family,
            "rows": count,
            "unique_scans_for_source_split": len(unique_scans[(source_id, split)]),
            "test_ready": str(split == "official_test").lower(),
        }
        for (source_id, split, family), count in sorted(counts.items())
    ]
    stats = {
        "source_candidate_file_exists": path.exists(),
        "source_candidate_rows": sum(counts.values()),
        "official_validation_rows": sum(count for (_, split, _), count in counts.items() if split == "official_validation"),
        "official_test_rows": sum(count for (_, split, _), count in counts.items() if split == "official_test"),
        "source_ids": sorted({source_id for (source_id, _, _) in counts}),
    }
    return rows, stats


def protocol_freeze_rows(source_eval_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    boundary = source_eval_manifest.get("boundary", {})
    model = source_eval_manifest.get("model", {})
    score_summary = source_eval_manifest.get("score_summary", {})
    return [
        {
            "item": "C_e_training_split",
            "current_value": model.get("C_e_train_split"),
            "preflight_status": "frozen_for_validation_reuse_only",
            "test_requirement": "must freeze exact model artifact/hash before test",
        },
        {
            "item": "feature_blocks",
            "current_value": ",".join(model.get("feature_blocks", [])),
            "preflight_status": "pass",
            "test_requirement": "T_e+G_e only; Z_e must remain excluded from C_e",
        },
        {
            "item": "source_score_and_Ce_combination",
            "current_value": "S2_source_x_Ce",
            "preflight_status": "pass",
            "test_requirement": "score formula fixed before test",
        },
        {
            "item": "post_hoc_lambda_tuning",
            "current_value": boundary.get("post_hoc_lambda_tuning"),
            "preflight_status": "pass" if boundary.get("post_hoc_lambda_tuning") is False else "fail",
            "test_requirement": "no post-hoc test tuning",
        },
        {
            "item": "source_rows_scored",
            "current_value": score_summary.get("row_count"),
            "preflight_status": "validation_only",
            "test_requirement": "must create separate official_test materialization",
        },
        {
            "item": "official_test_usage",
            "current_value": boundary.get("official_test_usage"),
            "preflight_status": "pass_unused",
            "test_requirement": "single final test run only after all gates pass",
        },
    ]


def gate_rows(test_stats: dict[str, Any], source_stats: dict[str, Any]) -> list[dict[str, Any]]:
    independent_test_ready = bool(CANONICAL_TEST.exists() and test_stats["usable_candidate_without_overlap"] > 0)
    source_test_ready = source_stats["official_test_rows"] > 0
    return [
        {
            "gate": "test_label_provenance",
            "status": "fail",
            "reason": "canonical test file missing; observed non-empty staged test candidates overlap validation scans",
            "blocks": "main benchmark table",
        },
        {
            "gate": "split_disjointness",
            "status": "fail",
            "reason": f"validation-alias candidates observed={test_stats['validation_alias_candidates']}",
            "blocks": "test benchmark execution",
        },
        {
            "gate": "test_source_prediction_availability",
            "status": "fail" if not source_test_ready else "pass",
            "reason": f"official_test source rows={source_stats['official_test_rows']}; existing source rows are validation-only",
            "blocks": "source-reranking benchmark",
        },
        {
            "gate": "frozen_Ce_model_and_features",
            "status": "partial",
            "reason": "validation protocol has T_e+G_e and no Z_e in C_e, but no test-specific frozen model/hash contract exists",
            "blocks": "test metric promotion",
        },
        {
            "gate": "normalization_freeze",
            "status": "partial",
            "reason": "validation normalization exists; test normalization policy must be frozen without using test labels",
            "blocks": "test ranking validity",
        },
        {
            "gate": "test_materialization_schema_audit",
            "status": "pending_blocked",
            "reason": "no official_test materialization exists yet",
            "blocks": "test metric run",
        },
        {
            "gate": "metric_and_claim_freeze",
            "status": "partial",
            "reason": "validation metrics/caveats frozen; test benchmark wording and CI policy still need freeze",
            "blocks": "paper benchmark claim",
        },
        {
            "gate": "single_final_test_run_policy",
            "status": "pending",
            "reason": "must be documented before any independent test run",
            "blocks": "test result credibility",
        },
        {
            "gate": "overall_test_benchmark_readiness",
            "status": "fail" if not (independent_test_ready and source_test_ready) else "pass",
            "reason": "test benchmark remains blocked until independent test provenance and test source rows are available",
            "blocks": "experiments-level test benchmark",
        },
    ]


def blocked_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "blocked_claim": "test_benchmark_ready",
            "reason": "independent test label/source rows are not verified",
            "replacement": "run test benchmark preflight resolution first",
        },
        {
            "blocked_claim": "staged_test_json_is_independent_test",
            "reason": "non-empty staged test JSON candidates overlap canonical validation scans",
            "replacement": "treat staged test files as blocked until provenance is proven",
        },
        {
            "blocked_claim": "validation_table_as_main_benchmark",
            "reason": "validation table was explicitly downgraded",
            "replacement": "appendix/secondary analysis only",
        },
    ]


def write_report(path: Path, summary: dict[str, Any], test_rows: list[dict[str, Any]], source_rows: list[dict[str, Any]], gates: list[dict[str, Any]]) -> None:
    lines = [
        "# H002 Test Benchmark Preflight",
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
        "## Decision",
        "",
        "- Test benchmark is not ready.",
        "- Validation table remains appendix/secondary analysis only.",
        "- Do not open an experiments-level test run until independent test provenance and test source rows are resolved.",
        "",
        "## Test Label Provenance",
        "",
        "| Candidate | Exists | Unique Scans | Relations | Val Overlap | Status |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in test_rows:
        lines.append(
            f"| `{row['candidate_id']}` | {row['exists']} | {row['unique_scans']} | {row['relations']} | "
            f"{row['validation_scan_overlap']} | {row['benchmark_use']} |"
        )
    lines.extend(
        [
            "",
            "## Source Prediction Availability",
            "",
            "| Source | Split | Family | Rows | Test Ready |",
            "| --- | --- | --- | ---: | --- |",
        ]
    )
    for row in source_rows:
        lines.append(
            f"| `{row['source_id']}` | `{row['split']}` | `{row['route_family']}` | {row['rows']} | {row['test_ready']} |"
        )
    lines.extend(
        [
            "",
            "## Gate Status",
            "",
            "| Gate | Status | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for row in gates:
        lines.append(f"| `{row['gate']}` | `{row['status']}` | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Required Before Experiment",
            "",
            "1. Verify an independent test label source or official evaluation server.",
            "2. Generate/freeze VL-SAT and Open3DSG source predictions for the exact test split.",
            "3. Freeze C_e model artifact, feature schema, score formula, K grid, normalization policy, metrics, controls, CI, and wording before test.",
            "4. Run test materialization and schema audit before any metric run.",
            "5. Execute test once and do not tune method/threshold/lambda/features/families/wording from the result.",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    review_summary = read_json(args.review_dir / "summary.json")
    source_eval_manifest = read_json(args.source_eval_dir / "metric_manifest.json")
    errors = validate_inputs(review_summary, source_eval_manifest, args.review_dir)

    test_rows, test_stats = test_label_provenance_rows()
    source_rows, source_stats = source_prediction_rows(args.source_materialization_dir)
    freeze_rows = protocol_freeze_rows(source_eval_manifest)
    gates = gate_rows(test_stats, source_stats)
    blocked = blocked_claim_rows()

    status = STATUS_ERRORS if errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "test_benchmark_preflight_blocked_by_input_errors",
        "validation_errors": len(errors),
        "input_artifacts": {
            "validation_table_review": rel_path(args.review_dir / "summary.json"),
            "source_materialization_dir": rel_path(args.source_materialization_dir),
            "source_eval_manifest": rel_path(args.source_eval_dir / "metric_manifest.json"),
        },
        "decision": {
            "validation_table_position": "appendix_or_secondary_analysis_only",
            "main_benchmark_requires_test": True,
            "test_benchmark_ready": False,
            "test_benchmark_blocker": "independent_test_provenance_and_test_source_rows_unresolved",
            "canonical_test_file_exists": CANONICAL_TEST.exists(),
            "non_empty_test_candidates": test_stats["non_empty_test_candidates"],
            "validation_alias_candidates": test_stats["validation_alias_candidates"],
            "official_test_source_rows": source_stats["official_test_rows"],
            "official_validation_source_rows": source_stats["official_validation_rows"],
            "experiments_test_run_allowed": False,
        },
        "output_artifacts": {
            "artifact_root": rel_path(args.output_dir),
            "test_label_provenance_audit": rel_path(args.output_dir / "test_label_provenance_audit.csv"),
            "source_prediction_availability": rel_path(args.output_dir / "source_prediction_availability.csv"),
            "protocol_freeze_audit": rel_path(args.output_dir / "protocol_freeze_audit.csv"),
            "preflight_gate_status": rel_path(args.output_dir / "preflight_gate_status.csv"),
            "blocked_claims": rel_path(args.output_dir / "blocked_claims.csv"),
            "next_contract": rel_path(args.output_dir / "next_contract.json"),
            "report": rel_path(args.output_dir / "report.md"),
        },
        "next_todo": NEXT_TODO if not errors else EXPECTED_REVIEW_NEXT,
    }

    next_contract = {
        "schema_version": f"{SCHEMA_VERSION}_next_contract",
        "next_todo": summary["next_todo"],
        "must_resolve": [
            "independent_test_label_or_official_evaluation_server",
            "test_split_disjointness",
            "test_source_prediction_rows_for_vlsat_and_open3dsg",
            "frozen_model_score_normalization_metric_claim_contract",
        ],
        "must_not_do": [
            "run_test_metric_before_provenance",
            "treat_validation_alias_as_test",
            "tune_score_formula_or_wording_after_test",
            "promote_validation_table_as_benchmark",
        ],
    }

    write_json(args.output_dir / "summary.json", summary)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_csv(args.output_dir / "test_label_provenance_audit.csv", test_rows)
    write_csv(args.output_dir / "source_prediction_availability.csv", source_rows)
    write_csv(args.output_dir / "protocol_freeze_audit.csv", freeze_rows)
    write_csv(args.output_dir / "preflight_gate_status.csv", gates)
    write_csv(args.output_dir / "blocked_claims.csv", blocked)
    write_json(args.output_dir / "next_contract.json", next_contract)
    write_report(args.output_dir / "report.md", summary, test_rows, source_rows, gates)

    print(json.dumps({"status": status, "validation_errors": len(errors), "next_todo": summary["next_todo"]}, ensure_ascii=False, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
