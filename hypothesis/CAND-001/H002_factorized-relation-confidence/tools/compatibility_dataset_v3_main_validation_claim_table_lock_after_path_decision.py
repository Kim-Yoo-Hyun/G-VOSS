#!/usr/bin/env python3
"""Lock H002 main validation table and claim wording after path decision."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PATH_DECISION_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_h002_post_validation_position_path_decision"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_main_validation_claim_table_lock_after_path_decision"

EXPECTED_PATH_STATUS = "h002_post_validation_position_path_decision_ready"
EXPECTED_PATH_NEXT = "compatibility_dataset_v3_main_validation_claim_table_lock_after_path_decision"

SCHEMA_VERSION = "h002_main_validation_claim_table_lock_after_path_decision_v1"
STATUS_READY = "h002_main_validation_claim_table_lock_after_path_decision_ready"
STATUS_ERRORS = "h002_main_validation_claim_table_lock_after_path_decision_input_errors"
SELECTED_PATH = "main_validation_table_claim_locked_keep_official_test_blocked"
NEXT_TODO = "compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-decision-dir", type=Path, default=DEFAULT_PATH_DECISION_DIR)
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


def validate_path_decision(path_decision_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    summary_path = path_decision_dir / "summary.json"
    if not summary_path.exists():
        errors.append({"error_type": "missing_path_decision_summary", "path": rel_path(summary_path)})
        return {}, errors
    summary = read_json(summary_path)
    if summary.get("status") != EXPECTED_PATH_STATUS:
        errors.append({"error_type": "unexpected_path_decision_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_PATH_NEXT:
        errors.append({"error_type": "unexpected_path_decision_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "path_decision_validation_errors", "actual": summary.get("validation_errors")})
    if line_count(path_decision_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "path_decision_validation_errors_file_not_empty"})

    decision = summary.get("decision", {})
    expected_true = [
        "main_validation_claim_allowed",
        "main_validation_table_allowed",
        "open3dsg_open_vocab_source_claim_allowed",
    ]
    for key in expected_true:
        if decision.get(key) is not True:
            errors.append({"error_type": "expected_true_decision_missing", "key": key, "actual": decision.get(key)})
    expected_false = [
        "official_test_benchmark_claim_allowed",
        "official_test_usage",
        "sota_or_leaderboard_claim_allowed",
        "open3dsg_unconstrained_open_set_gt_claim_allowed",
    ]
    for key in expected_false:
        if decision.get(key) is not False:
            errors.append({"error_type": "expected_false_decision_missing", "key": key, "actual": decision.get(key)})
    if decision.get("validation_table_position") != "main_validation_benchmark":
        errors.append({"error_type": "unexpected_validation_table_position", "actual": decision.get("validation_table_position")})
    return summary, errors


def main_table_lock_rows() -> list[dict[str, Any]]:
    return [
        {
            "table_id": "main_validation_source_reranking",
            "paper_position": "main",
            "title": "Main validation benchmark: source reranking on 3DSSG validation",
            "caption_lock": "Evaluated on the official 3DSSG validation split. This is not an official 3DSSG test result.",
            "sources": "VL-SAT validation predictions; Open3DSG validation predictions",
            "metrics": "Recall@K; Violation@K",
            "include_conditions": "source_score baseline; source_score x C_e; controls if space allows",
        },
        {
            "table_id": "mechanism_control_table",
            "paper_position": "main_or_appendix",
            "title": "Compatibility controls",
            "caption_lock": "Controls are H002 custom controls, not official 3DSSG metrics.",
            "sources": "route/family controls",
            "metrics": "wrong-T; shuffled-G; family-wise caveats",
            "include_conditions": "include in main if reviewer defense needs direct mechanism proof",
        },
        {
            "table_id": "official_test_table",
            "paper_position": "blocked",
            "title": "Official test benchmark",
            "caption_lock": "Blocked until official relation-test GT or hidden evaluator exists.",
            "sources": "none",
            "metrics": "none",
            "include_conditions": "do not include",
        },
    ]


def baseline_wording_rows() -> list[dict[str, Any]]:
    return [
        {
            "baseline_or_condition": "S0_source_score",
            "allowed_wording": "source confidence baseline",
            "blocked_wording": "official SOTA baseline unless exact paper protocol is reproduced",
            "required_caveat": "same validation split and mapped relation-label space",
        },
        {
            "baseline_or_condition": "S2_source_x_Ce",
            "allowed_wording": "H002 compatibility-aware reranking score",
            "blocked_wording": "new relation predictor",
            "required_caveat": "reranks existing source predictions; C_e excludes Z_e",
        },
        {
            "baseline_or_condition": "Open3DSG",
            "allowed_wording": "open-vocabulary relation source evaluated after mapping to closed 3DSSG labels",
            "blocked_wording": "unconstrained open-set GT benchmark",
            "required_caveat": "quantitative Recall@K is closed-vocabulary 3DSSG mapping",
        },
        {
            "baseline_or_condition": "VL-SAT",
            "allowed_wording": "validation relation-source baseline",
            "blocked_wording": "test benchmark unless relation-test GT/evaluator exists",
            "required_caveat": "validation split",
        },
    ]


def blocked_wording_rows() -> list[dict[str, Any]]:
    return [
        {
            "blocked_claim": "official 3DSSG test result",
            "replacement": "official 3DSSG validation split result",
            "reason": "relation-test GT/evaluator not confirmed",
        },
        {
            "blocked_claim": "SOTA / leaderboard",
            "replacement": "main validation benchmark comparison",
            "reason": "requires exact official benchmark protocol and comparable baseline reproduction",
        },
        {
            "blocked_claim": "unconstrained open-set GT evaluation",
            "replacement": "open-vocabulary source with closed-vocabulary 3DSSG mapping",
            "reason": "GT labels are closed 3DSSG relation labels",
        },
        {
            "blocked_claim": "H002 is a new relation predictor",
            "replacement": "H002 is a factorized reliability/reranking layer",
            "reason": "method reranks existing VL-SAT/Open3DSG source predictions",
        },
    ]


def caveat_rows() -> list[dict[str, Any]]:
    return [
        {
            "caveat_id": "negative_recall_cells",
            "must_report": True,
            "wording": "Some source-family-K cells show small Recall@K regressions; report them instead of claiming uniform improvement.",
        },
        {
            "caveat_id": "violation_metric_custom",
            "must_report": True,
            "wording": "Violation@K is an H002 custom geometry-consistency metric, not an official 3DSSG metric.",
        },
        {
            "caveat_id": "support_contact_diagnostic",
            "must_report": True,
            "wording": "support/contact remains diagnostic/failure taxonomy, not solved compatibility-route evidence.",
        },
        {
            "caveat_id": "open3dsg_mapping",
            "must_report": True,
            "wording": "Open3DSG is open-vocabulary as a source; quantitative metrics use closed 3DSSG mapping.",
        },
        {
            "caveat_id": "official_test_absent",
            "must_report": True,
            "wording": "No official relation-test GT/evaluator is used.",
        },
    ]


def h003_extension_rows() -> list[dict[str, Any]]:
    return [
        {
            "extension": "H003_semantic_geometry_embedding",
            "paper_status_now": "future_or_optional_extension",
            "can_enter_paper_if": "beats explicit C_e on hard negatives, transfer, calibration, or family generalization",
            "do_not_claim_now": "learned embedding main contribution",
        },
        {
            "extension": "embedding_as_Ce_generalization",
            "paper_status_now": "discussion_friendly",
            "can_enter_paper_if": "small controlled prototype passes shortcut controls and improves source reranking",
            "do_not_claim_now": "replacement for H002 without evidence",
        },
    ]


def write_wording_guidance(path: Path) -> None:
    text = """# H002 Main Validation Table Wording Lock

## Main Table Caption

Recommended caption:

> Main validation benchmark on the official 3DSSG validation split. We compare
> source-score ranking with H002 compatibility-aware reranking on VL-SAT and
> Open3DSG validation predictions. Open3DSG is used as an open-vocabulary source,
> while quantitative Recall@K is computed after mapping to closed-vocabulary 3DSSG
> labels. Violation@K is our geometry-consistency metric.

## Main Text

Use:

> H002 is a factorized reliability/reranking layer over existing relation sources,
> not a replacement relation predictor.

Use:

> The compatibility score C_e is computed from T_e and G_e only; source score Z_e is
> combined only at the final reranking stage.

Avoid:

- official test result
- leaderboard/SOTA
- unconstrained open-set GT evaluation
- uniform improvement across all source/family/K cells
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_report(path: Path, output_dir: Path, status: str, validation_errors: int) -> None:
    text = f"""# H002 Main Validation Claim Table Lock

## Purpose

This gate locks H002's main validation benchmark wording after selecting the
official 3DSSG validation split as the main comparative claim. It does not run new
metrics.

## Result

```text
artifact_root = {rel_path(output_dir)}/
status = {status}
selected_path = {SELECTED_PATH}
validation_errors = {validation_errors}
main_table = official_3DSSG_validation_split
official_test_benchmark = false
next_todo = {NEXT_TODO}
```

## Locked Wording

- Main table is a validation benchmark table, not official test.
- H002 is a reliability/reranking layer over VL-SAT/Open3DSG source predictions.
- Open3DSG is an open-vocabulary source evaluated through closed 3DSSG mapping.
- Violation@K is an H002 custom geometry-consistency metric.
- H003 embedding remains a future/optional extension unless prototype evidence is added.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    path_summary, errors = validate_path_decision(args.path_decision_dir)
    status = STATUS_ERRORS if errors else STATUS_READY
    selected_path = "input_errors_fix_path_decision_before_table_lock" if errors else SELECTED_PATH
    next_todo = EXPECTED_PATH_NEXT if errors else NEXT_TODO

    validation_errors_path = output_dir / "validation_errors.jsonl"
    main_table_lock_path = output_dir / "main_table_lock.csv"
    baseline_wording_path = output_dir / "baseline_wording.csv"
    blocked_wording_path = output_dir / "blocked_wording.csv"
    caveats_path = output_dir / "required_caveats.csv"
    h003_extension_path = output_dir / "h003_extension_position.csv"
    wording_path = output_dir / "wording_guidance.md"
    next_contract_path = output_dir / "next_contract.json"
    report_path = output_dir / "report.md"
    summary_path = output_dir / "summary.json"

    write_jsonl(validation_errors_path, errors)
    write_csv(main_table_lock_path, main_table_lock_rows())
    write_csv(baseline_wording_path, baseline_wording_rows())
    write_csv(blocked_wording_path, blocked_wording_rows())
    write_csv(caveats_path, caveat_rows())
    write_csv(h003_extension_path, h003_extension_rows())
    write_wording_guidance(wording_path)
    write_report(report_path, output_dir, status, len(errors))
    write_json(
        next_contract_path,
        {
            "next_todo": next_todo,
            "main_table": "official_3DSSG_validation_split",
            "main_table_allowed": True,
            "official_test_benchmark": False,
            "locked_caption_requirements": [
                "official 3DSSG validation split",
                "VL-SAT and Open3DSG validation predictions",
                "Open3DSG open-vocabulary source with closed-label mapping",
                "Violation@K is custom H002 geometry-consistency metric",
                "not official 3DSSG test",
            ],
            "next_stage_should_materialize": [
                "compact main validation table rows",
                "source/family/K caveat rows",
                "caption-ready markdown",
                "blocked wording checklist",
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
            "path_decision_summary": rel_path(args.path_decision_dir / "summary.json"),
            "path_decision_next_contract": rel_path(args.path_decision_dir / "next_contract.json"),
        },
        "decision": {
            "main_validation_table_locked": True,
            "main_validation_table_allowed": True,
            "official_test_benchmark_claim_allowed": False,
            "sota_or_leaderboard_claim_allowed": False,
            "open3dsg_open_vocab_source_closed_eval_required": True,
            "h003_embedding_extension_in_main_claim_now": False,
            "h003_embedding_extension_future_optional": True,
        },
        "locked_claim_boundary": {
            "main_split": "official_3DSSG_validation_split",
            "sources": "VL-SAT and Open3DSG validation predictions",
            "primary_score": "S2_source_x_Ce",
            "baseline": "S0_source_score",
            "metrics": "Recall@K and Violation@K",
            "method_role": "factorized reliability/reranking layer",
        },
        "path_decision_stage_status": path_summary.get("status"),
        "output_artifacts": {
            "artifact_root": rel_path(output_dir),
            "summary": rel_path(summary_path),
            "validation_errors": rel_path(validation_errors_path),
            "main_table_lock": rel_path(main_table_lock_path),
            "baseline_wording": rel_path(baseline_wording_path),
            "blocked_wording": rel_path(blocked_wording_path),
            "required_caveats": rel_path(caveats_path),
            "h003_extension_position": rel_path(h003_extension_path),
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
