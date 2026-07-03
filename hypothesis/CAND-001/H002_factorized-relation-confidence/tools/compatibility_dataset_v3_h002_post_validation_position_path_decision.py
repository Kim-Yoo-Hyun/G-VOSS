#!/usr/bin/env python3
"""Select H002's post-validation paper position after validation-only lock."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_POSITION_LOCK_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_validation_only_position_lock_after_no_external_response"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_h002_post_validation_position_path_decision"

EXPECTED_POSITION_STATUS = "h002_validation_only_position_lock_after_no_external_response_ready"
EXPECTED_POSITION_NEXT = "compatibility_dataset_v3_h002_post_validation_position_path_decision"

SCHEMA_VERSION = "h002_post_validation_position_path_decision_v1"
STATUS_READY = "h002_post_validation_position_path_decision_ready"
STATUS_ERRORS = "h002_post_validation_position_path_decision_input_errors"
SELECTED_PATH = "promote_official_validation_as_main_comparative_claim_keep_test_blocked"
NEXT_TODO = "compatibility_dataset_v3_main_validation_claim_table_lock_after_path_decision"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--position-lock-dir", type=Path, default=DEFAULT_POSITION_LOCK_DIR)
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


def validate_position_lock(position_lock_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    summary_path = position_lock_dir / "summary.json"
    if not summary_path.exists():
        errors.append({"error_type": "missing_position_lock_summary", "path": rel_path(summary_path)})
        return {}, errors
    summary = read_json(summary_path)
    if summary.get("status") != EXPECTED_POSITION_STATUS:
        errors.append({"error_type": "unexpected_position_lock_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_POSITION_NEXT:
        errors.append({"error_type": "unexpected_position_lock_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "position_lock_validation_errors", "actual": summary.get("validation_errors")})
    if line_count(position_lock_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "position_lock_validation_errors_file_not_empty"})

    decision = summary.get("decision", {})
    locked = summary.get("locked_position", {})
    if decision.get("allowed_validation_source_reranking_claim") is not True:
        errors.append({"error_type": "expected_validation_source_reranking_allowed"})
    if decision.get("allowed_recall_violation_validation_improvement_claim") is not True:
        errors.append({"error_type": "expected_validation_recall_violation_allowed"})
    if decision.get("allowed_open_vocab_source_closed_eval_claim") is not True:
        errors.append({"error_type": "expected_open_vocab_source_closed_eval_allowed"})
    if decision.get("official_test_result_claim_allowed") is not False:
        errors.append({"error_type": "official_test_claim_should_be_blocked"})
    if locked.get("dataset_basis") != "official_3DSSG_validation_split":
        errors.append({"error_type": "unexpected_dataset_basis", "actual": locked.get("dataset_basis")})
    if locked.get("official_test_benchmark") is not False:
        errors.append({"error_type": "official_test_benchmark_should_be_false"})
    return summary, errors


def path_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "candidate_path": "keep_appendix_secondary_only",
            "selected": False,
            "reason": "too conservative for H002 because VL-SAT/Open3DSG and available 3DSSG relation evaluation are validation-based",
        },
        {
            "candidate_path": "promote_official_validation_as_main_comparative_claim",
            "selected": True,
            "reason": "same official 3DSSG validation split enables direct comparison with VL-SAT/Open3DSG source predictions while test relation GT remains unavailable",
        },
        {
            "candidate_path": "wait_for_official_test_response",
            "selected": False,
            "reason": "external response/provenance is currently absent; waiting would block current H002 paper framing",
        },
        {
            "candidate_path": "new_human_audited_benchmark_now",
            "selected": False,
            "reason": "possible extension, but larger scope and separate benchmark claim; not required for main validation claim",
        },
    ]


def main_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_component": "main_dataset",
            "locked_value": "official_3DSSG_validation_split",
            "allowed_main_text": "main validation benchmark",
            "required_caveat": "not official 3DSSG test",
        },
        {
            "claim_component": "source_comparison",
            "locked_value": "VL-SAT and Open3DSG validation predictions",
            "allowed_main_text": "comparison across two relation sources on the same validation GT",
            "required_caveat": "source-specific prediction generation and mapping provenance must be reported",
        },
        {
            "claim_component": "metrics",
            "locked_value": "Recall@K and Violation@K",
            "allowed_main_text": "main H002 downstream metrics under frozen validation protocol",
            "required_caveat": "Violation@K is H002 custom reliability metric, not official 3DSSG metric",
        },
        {
            "claim_component": "open3dsg_boundary",
            "locked_value": "open-vocabulary source, closed-vocabulary 3DSSG evaluation",
            "allowed_main_text": "Open3DSG tests whether H002 applies to an open-vocabulary relation source",
            "required_caveat": "quantitative GT comparison is closed-label mapping, not unconstrained open-set GT",
        },
    ]


def allowed_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "main_validation_claim",
            "allowed": True,
            "wording": "We use the official 3DSSG validation split as the main comparative evaluation split.",
            "scope": "main paper table allowed with validation caveat",
        },
        {
            "claim_id": "source_reranking_main_table",
            "allowed": True,
            "wording": "H002 reranks VL-SAT and Open3DSG validation predictions and reports Recall@K / Violation@K.",
            "scope": "main validation table, not official test table",
        },
        {
            "claim_id": "open_vocab_source_generalization",
            "allowed": True,
            "wording": "Open3DSG serves as an open-vocabulary relation source evaluated after closed-vocabulary 3DSSG mapping.",
            "scope": "source generality evidence with closed-label evaluation caveat",
        },
        {
            "claim_id": "comparison_with_baseline_papers",
            "allowed": True,
            "wording": "Comparison is valid when aligned to the same official 3DSSG validation split and comparable closed-vocabulary mapping.",
            "scope": "validation benchmark comparison, not leaderboard/test SOTA",
        },
    ]


def blocked_claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "official_test_result",
            "blocked": True,
            "blocked_wording": "official 3DSSG test benchmark result",
            "reason": "relation-test GT or accepted hidden evaluator is still not confirmed",
        },
        {
            "claim_id": "leaderboard_sota",
            "blocked": True,
            "blocked_wording": "leaderboard/SOTA on official test",
            "reason": "main table is validation-based; SOTA wording requires exact benchmark protocol and comparable baseline reproduction",
        },
        {
            "claim_id": "unconstrained_open_set_gt",
            "blocked": True,
            "blocked_wording": "unconstrained open-set GT evaluation",
            "reason": "Open3DSG source can be open-vocabulary, but quantitative GT evaluation remains closed 3DSSG mapping",
        },
        {
            "claim_id": "test_scan_prediction_recall",
            "blocked": True,
            "blocked_wording": "Recall@K on prediction-only 3RScan test scans",
            "reason": "without relation GT, recall denominator is undefined",
        },
    ]


def table_position_rows() -> list[dict[str, Any]]:
    return [
        {
            "table": "main_validation_source_reranking",
            "position": "main",
            "include": True,
            "content": "VL-SAT/Open3DSG validation Recall@K and Violation@K for source score vs source_score x C_e",
            "caption_caveat": "official 3DSSG validation split; not official test",
        },
        {
            "table": "mechanism_controls",
            "position": "main_or_appendix",
            "include": True,
            "content": "wrong-T, shuffled-G, family-level controls",
            "caption_caveat": "custom H002 controls",
        },
        {
            "table": "official_test_benchmark",
            "position": "blocked",
            "include": False,
            "content": "official test Recall@K",
            "caption_caveat": "requires relation-test GT/evaluator",
        },
        {
            "table": "human_audited_benchmark",
            "position": "future_or_separate",
            "include": False,
            "content": "human accept/reject/abstain reliability benchmark",
            "caption_caveat": "separate benchmark claim if created",
        },
    ]


def wording_guidance(output_path: Path) -> None:
    text = """# H002 Main Validation Claim Wording

## Main Wording

Use:

> We evaluate H002 on the official 3DSSG validation split and compare reranking
> results on VL-SAT and Open3DSG validation predictions.

Use:

> Open3DSG is treated as an open-vocabulary relation source; quantitative metrics
> are computed after mapping predictions to closed-vocabulary 3DSSG relation labels.

Use:

> Recall@K is the closed-label validation recall metric, and Violation@K is our
> geometry-consistency/reliability metric.

## Avoid

- Official 3DSSG test result.
- Leaderboard/SOTA unless the exact official benchmark protocol and comparable
  baselines are reproduced.
- Unconstrained open-set GT evaluation.
- Recall@K on prediction-only 3RScan test scans.
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def write_report(path: Path, output_dir: Path, status: str, validation_errors: int) -> None:
    text = f"""# H002 Post-Validation Position Path Decision

## Purpose

The previous gate conservatively placed H002 validation results in appendix or
secondary analysis because no official test relation GT/evaluator was confirmed.
This path-decision step promotes the same official 3DSSG validation split to the
main comparative claim because VL-SAT/Open3DSG relation-source comparisons and the
available public evaluation flow are validation-based.

## Result

```text
artifact_root = {rel_path(output_dir)}/
status = {status}
selected_path = {SELECTED_PATH}
validation_errors = {validation_errors}
main_claim_split = official_3DSSG_validation_split
main_table_allowed = true_validation_benchmark
official_test_benchmark = false
next_todo = {NEXT_TODO}
```

## Interpretation

H002 can use the official 3DSSG validation split as its main evaluation split,
provided that the paper explicitly says it is validation-based and not an official
test benchmark. Open3DSG can be used as an open-vocabulary source, but quantitative
evaluation remains closed-vocabulary 3DSSG mapping.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    position_summary, errors = validate_position_lock(args.position_lock_dir)
    status = STATUS_ERRORS if errors else STATUS_READY
    selected_path = "input_errors_fix_position_lock_before_path_decision" if errors else SELECTED_PATH
    next_todo = EXPECTED_POSITION_NEXT if errors else NEXT_TODO

    validation_errors_path = output_dir / "validation_errors.jsonl"
    path_decision_path = output_dir / "path_decision.csv"
    main_claim_path = output_dir / "main_claim_boundary.csv"
    allowed_claims_path = output_dir / "allowed_claims.csv"
    blocked_claims_path = output_dir / "blocked_claims.csv"
    table_position_path = output_dir / "table_position.csv"
    wording_path = output_dir / "wording_guidance.md"
    next_contract_path = output_dir / "next_contract.json"
    report_path = output_dir / "report.md"
    summary_path = output_dir / "summary.json"

    write_jsonl(validation_errors_path, errors)
    write_csv(path_decision_path, path_decision_rows())
    write_csv(main_claim_path, main_claim_rows())
    write_csv(allowed_claims_path, allowed_claim_rows())
    write_csv(blocked_claims_path, blocked_claim_rows())
    write_csv(table_position_path, table_position_rows())
    wording_guidance(wording_path)
    write_report(report_path, output_dir, status, len(errors))
    write_json(
        next_contract_path,
        {
            "next_todo": next_todo,
            "selected_path": selected_path,
            "main_claim_split": "official_3DSSG_validation_split",
            "main_table_allowed": "true_validation_benchmark",
            "official_test_benchmark": False,
            "must_state": [
                "official 3DSSG validation split",
                "not official 3DSSG test",
                "Open3DSG open-vocabulary source with closed-vocabulary 3DSSG mapping",
                "Violation@K is H002 custom reliability metric",
            ],
            "next_stage_should_lock": [
                "main validation table caption",
                "allowed baseline comparison wording",
                "blocked test/SOTA/open-set wording",
                "negative source-family-K cells and caveats",
            ],
        },
    )

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(errors),
        "next_todo": next_todo,
        "input_artifacts": {
            "position_lock_summary": rel_path(args.position_lock_dir / "summary.json"),
            "position_lock_next_contract": rel_path(args.position_lock_dir / "next_contract.json"),
        },
        "decision": {
            "main_validation_claim_allowed": True,
            "main_validation_table_allowed": True,
            "validation_table_position": "main_validation_benchmark",
            "official_test_benchmark_claim_allowed": False,
            "official_test_usage": False,
            "sota_or_leaderboard_claim_allowed": False,
            "open3dsg_open_vocab_source_claim_allowed": True,
            "open3dsg_unconstrained_open_set_gt_claim_allowed": False,
        },
        "claim_boundary": {
            "dataset_basis": "official_3DSSG_validation_split",
            "source_comparison": "VL-SAT and Open3DSG validation predictions",
            "metrics": "Recall@K and Violation@K",
            "open3dsg_boundary": "open_vocabulary_source_closed_vocabulary_3dssg_mapping",
        },
        "position_lock_stage_status": position_summary.get("status"),
        "output_artifacts": {
            "artifact_root": rel_path(output_dir),
            "summary": rel_path(summary_path),
            "validation_errors": rel_path(validation_errors_path),
            "path_decision": rel_path(path_decision_path),
            "main_claim_boundary": rel_path(main_claim_path),
            "allowed_claims": rel_path(allowed_claims_path),
            "blocked_claims": rel_path(blocked_claims_path),
            "table_position": rel_path(table_position_path),
            "wording_guidance": rel_path(wording_path),
            "next_contract": rel_path(next_contract_path),
            "report": rel_path(report_path),
        },
    }
    write_json(summary_path, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
