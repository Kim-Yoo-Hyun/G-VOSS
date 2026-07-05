#!/usr/bin/env python3
"""Review the materialized H002 main validation table after claim lock."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_MATERIALIZATION_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_main_validation_table_review_after_materialization"
)

EXPECTED_INPUT_STATUS = "h002_main_validation_table_materialization_after_claim_lock_ready"
EXPECTED_INPUT_NEXT = "compatibility_dataset_v3_main_validation_table_review_after_materialization"
SCHEMA_VERSION = "h002_main_validation_table_review_after_materialization_v1"
STATUS_READY = "h002_main_validation_table_review_after_materialization_ready"
STATUS_ERRORS = "h002_main_validation_table_review_after_materialization_input_errors"
SELECTED_PATH = "main_validation_table_reviewed_select_paper_insertion_plan"
NEXT_TODO = "compatibility_dataset_v3_paper_draft_insertion_plan_after_main_validation_table_review"
K_GRID = [5, 10, 20, 50, 100]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialization-dir", type=Path, default=DEFAULT_MATERIALIZATION_DIR)
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
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"


def add_check(rows: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    rows.append(
        {
            "check": name,
            "status": "pass" if passed else "fail",
            "detail": detail,
        }
    )


def validate(
    summary: dict[str, Any],
    main_rows: list[dict[str, str]],
    caveats: list[dict[str, str]],
    controls: list[dict[str, str]],
    blocked: list[dict[str, str]],
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []

    def fail(error_type: str, **payload: Any) -> None:
        errors.append({"error_type": error_type, **payload})

    add_check(
        checks,
        "input_status",
        summary.get("status") == EXPECTED_INPUT_STATUS,
        f"status={summary.get('status')}",
    )
    if summary.get("status") != EXPECTED_INPUT_STATUS:
        fail("unexpected_input_status", actual=summary.get("status"))

    add_check(
        checks,
        "input_next_todo",
        summary.get("next_todo") == EXPECTED_INPUT_NEXT,
        f"next_todo={summary.get('next_todo')}",
    )
    if summary.get("next_todo") != EXPECTED_INPUT_NEXT:
        fail("unexpected_input_next_todo", actual=summary.get("next_todo"))

    add_check(
        checks,
        "input_validation_errors",
        summary.get("validation_errors") == 0
        and line_count(args.materialization_dir / "validation_errors.jsonl") == 0,
        "materialization validation_errors must be 0",
    )
    if summary.get("validation_errors") != 0:
        fail("input_validation_errors", actual=summary.get("validation_errors"))
    if line_count(args.materialization_dir / "validation_errors.jsonl") != 0:
        fail("input_validation_errors_file_not_empty")

    k_values = sorted(int(row["K"]) for row in main_rows if row.get("K"))
    add_check(checks, "k_grid", k_values == K_GRID, f"K={k_values}")
    if k_values != K_GRID:
        fail("unexpected_k_grid", actual=k_values, expected=K_GRID)

    split_ok = all(row.get("split") == "official_3DSSG_validation" for row in main_rows)
    add_check(checks, "split_boundary", split_ok, "main rows must say official_3DSSG_validation")
    if not split_ok:
        fail("split_boundary_violation")

    official_test_text = "official test"
    table_md = (args.materialization_dir / "main_validation_table.md").read_text(encoding="utf-8")
    caption_ok = (
        "official 3DSSG validation split" in table_md
        and "not official test" in table_md
        and "SOTA" not in table_md
        and "leaderboard" not in table_md
    )
    add_check(
        checks,
        "caption_boundary",
        caption_ok,
        "caption/notes must keep validation-only wording and avoid SOTA/leaderboard",
    )
    if not caption_ok:
        fail("caption_boundary_violation", official_test_mentions=table_md.count(official_test_text))

    rows_have_expected_score = all(
        row.get("baseline") == "S0_source_score" and row.get("h002_score") == "S2_source_x_Ce"
        for row in main_rows
    )
    add_check(checks, "score_ids", rows_have_expected_score, "baseline S0 and primary S2")
    if not rows_have_expected_score:
        fail("unexpected_score_ids")

    recall_deltas = [as_float(row.get("Delta_Recall@K")) for row in main_rows]
    violation_deltas = [as_float(row.get("Delta_Violation@K")) for row in main_rows]
    recall_ok = all(value is not None and value > 0.0 for value in recall_deltas)
    violation_ok = all(value is not None and value < 0.0 for value in violation_deltas)
    add_check(
        checks,
        "primary_recall_improvement",
        recall_ok,
        f"min_delta={fmt(min(v for v in recall_deltas if v is not None)) if recall_deltas else ''}",
    )
    add_check(
        checks,
        "primary_violation_reduction",
        violation_ok,
        f"max_delta={fmt(max(v for v in violation_deltas if v is not None)) if violation_deltas else ''}",
    )
    if not recall_ok:
        fail("primary_recall_not_improved_at_all_k")
    if not violation_ok:
        fail("primary_violation_not_reduced_at_all_k")

    caveat_ok = len(caveats) == 3 and all(
        as_float(row.get("Delta_Recall@K")) is not None
        and as_float(row.get("Delta_Recall@K")) < 0.0
        and "do not claim uniform improvement" in row.get("required_caveat", "")
        for row in caveats
    )
    add_check(checks, "source_family_caveats", caveat_ok, f"rows={len(caveats)}")
    if not caveat_ok:
        fail("source_family_caveat_contract_failed", rows=len(caveats))

    blocked_claims = {row.get("claim_or_field"): row for row in blocked}
    required_blocked = [
        "official 3DSSG test result",
        "SOTA / leaderboard wording",
        "unconstrained open-set GT evaluation",
        "uniform improvement across all source/family/K cells",
        "H003 embedding as main contribution",
    ]
    blocked_ok = all(
        blocked_claims.get(item, {}).get("status", "").startswith("blocked")
        for item in required_blocked
    )
    add_check(checks, "blocked_wording", blocked_ok, f"blocked_items={len(blocked_claims)}")
    if not blocked_ok:
        fail("blocked_wording_contract_failed")

    control_roles = {row.get("control"): row.get("paper_role") for row in controls}
    control_rows_ok = len(controls) == 15
    ce_only_role_ok = control_roles.get("C_e only") == "diagnostic_ablation_row"
    wrong_t_rows = [row for row in controls if row.get("control") == "source x wrong-T C_e"]
    shuffled_rows = [row for row in controls if row.get("control") == "source x shuffled C_e"]
    wrong_t_ok = len(wrong_t_rows) == 5 and all(
        as_float(row.get("Delta_Violation@K")) is not None
        and as_float(row.get("Delta_Violation@K")) < 0.0
        for row in wrong_t_rows
    )
    shuffled_ok = len(shuffled_rows) == 5 and all(
        as_float(row.get("Delta_Violation@K")) is not None
        and as_float(row.get("Delta_Violation@K")) < 0.0
        for row in shuffled_rows
    )
    add_check(checks, "control_rows", control_rows_ok, f"rows={len(controls)}")
    add_check(checks, "ce_only_role", ce_only_role_ok, "C_e only must stay diagnostic")
    add_check(checks, "wrong_t_violation_control", wrong_t_ok, "wrong-T has worse Violation@K than S2")
    add_check(checks, "shuffled_g_violation_control", shuffled_ok, "shuffled C_e has worse Violation@K than S2")
    if not control_rows_ok:
        fail("unexpected_control_row_count", rows=len(controls))
    if not ce_only_role_ok:
        fail("ce_only_not_diagnostic")
    if not wrong_t_ok:
        fail("wrong_t_control_contract_failed")
    if not shuffled_ok:
        fail("shuffled_control_contract_failed")

    return errors, checks


def write_report(
    path: Path,
    status: str,
    selected_path: str,
    main_rows: list[dict[str, str]],
    caveats: list[dict[str, str]],
    checks: list[dict[str, Any]],
) -> None:
    lines: list[str] = [
        "# H002 Main Validation Table Review",
        "",
        "## Purpose",
        "",
        "Review the materialized main validation table before paper draft insertion. "
        "This stage does not run new metrics, tune scores, or touch official test data.",
        "",
        "## Result",
        "",
        "```text",
        f"status = {status}",
        f"selected_path = {selected_path}",
        f"validation_errors = {sum(1 for row in checks if row['status'] == 'fail')}",
        f"next_todo = {NEXT_TODO}",
        "```",
        "",
        "## Main Table Review",
        "",
        "| K | Delta Recall@K | Delta Violation@K |",
        "| ---: | ---: | ---: |",
    ]
    for row in main_rows:
        lines.append(
            f"| {row.get('K')} | {row.get('Delta_Recall@K')} | {row.get('Delta_Violation@K')} |"
        )
    lines.extend(
        [
            "",
            "Review decision: the table is acceptable as a validation-level paper table candidate "
            "for the primary success families, with explicit validation-only and caveat wording.",
            "",
            "## Required Caveats",
            "",
            "| source_id | route_family | K | Delta Recall@K | Required caveat |",
            "| --- | --- | ---: | ---: | --- |",
        ]
    )
    for row in caveats:
        lines.append(
            "| "
            f"{row.get('source_id')} | {row.get('route_family')} | {row.get('K')} | "
            f"{row.get('Delta_Recall@K')} | {row.get('required_caveat')} |"
        )
    lines.extend(
        [
            "",
            "## Wording Lock",
            "",
            "- Use `official 3DSSG validation split`, not `official test`.",
            "- Do not use SOTA, leaderboard, or uniform-improvement wording.",
            "- Describe Open3DSG as an open-vocabulary source evaluated through closed 3DSSG label mapping.",
            "- Keep `C_e only` as a diagnostic ablation; the deployable score is `S2_source_x_Ce`.",
            "- Use control wording carefully: wrong-T and shuffled-C_e mainly support violation-risk specificity, not a universal recall-collapse claim.",
            "",
            "## Checks",
            "",
            "| Check | Status | Detail |",
            "| --- | --- | --- |",
        ]
    )
    for row in checks:
        lines.append(f"| {row['check']} | {row['status']} | {row['detail']} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    summary = read_json(args.materialization_dir / "summary.json")
    main_rows = read_csv(args.materialization_dir / "main_validation_table.csv")
    caveats = read_csv(args.materialization_dir / "source_family_caveats.csv")
    controls = read_csv(args.materialization_dir / "control_table_compact.csv")
    blocked = read_csv(args.materialization_dir / "blocked_wording_checklist.csv")

    errors, checks = validate(summary, main_rows, caveats, controls, blocked, args)
    status = STATUS_READY if not errors else STATUS_ERRORS
    selected_path = SELECTED_PATH if not errors else "main_validation_table_review_blocked"

    decision_rows = [
        {
            "decision": "paper_table_candidate",
            "status": "allowed_with_caveats" if not errors else "blocked",
            "scope": "official_3DSSG_validation_split_primary_success_families",
            "baseline": "S0_source_score",
            "h002_score": "S2_source_x_Ce",
            "required_caveat": "validation-only, not SOTA/test; 3 source-family-K recall regressions must be disclosed",
        },
        {
            "decision": "controls",
            "status": "supporting_but_wording_limited",
            "scope": "C_e only, shuffled C_e, wrong-T C_e",
            "baseline": "",
            "h002_score": "",
            "required_caveat": "do not claim all controls collapse in recall; use violation-risk specificity wording",
        },
        {
            "decision": "next_step",
            "status": "ready",
            "scope": NEXT_TODO,
            "baseline": "",
            "h002_score": "",
            "required_caveat": "plan manuscript insertion before editing paper prose",
        },
    ]

    wording_rows = [
        {
            "wording_item": "allowed_caption",
            "status": "allowed",
            "text": "Official 3DSSG validation split; VL-SAT/Open3DSG validation predictions; Recall@K and custom Violation@K.",
        },
        {
            "wording_item": "blocked_test",
            "status": "blocked",
            "text": "official 3DSSG test result",
        },
        {
            "wording_item": "blocked_sota",
            "status": "blocked",
            "text": "SOTA, leaderboard, state-of-the-art benchmark claim",
        },
        {
            "wording_item": "blocked_uniform",
            "status": "blocked",
            "text": "uniform improvement across every source/family/K cell",
        },
        {
            "wording_item": "control_wording",
            "status": "allowed_with_caveat",
            "text": "wrong-T and shuffled-C_e controls worsen violation-risk ranking; C_e-only is diagnostic, not deployable.",
        },
    ]

    write_csv(args.output_dir / "review_checks.csv", checks)
    write_csv(args.output_dir / "review_decision.csv", decision_rows)
    write_csv(args.output_dir / "wording_gate.csv", wording_rows)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", status, selected_path, main_rows, caveats, checks)

    summary_out = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(errors),
        "decision": {
            "paper_table_candidate": not errors,
            "paper_table_position": "main_validation_table_candidate_with_validation_only_wording",
            "official_test_usage": False,
            "sota_or_leaderboard_claim_allowed": False,
            "uniform_improvement_claim_allowed": False,
            "control_collapse_wording_allowed": False,
            "control_specificity_wording_allowed": True,
            "next_todo": NEXT_TODO,
        },
        "input_artifacts": {
            "materialization_summary": rel_path(args.materialization_dir / "summary.json"),
            "main_validation_table": rel_path(args.materialization_dir / "main_validation_table.csv"),
            "source_family_caveats": rel_path(args.materialization_dir / "source_family_caveats.csv"),
            "control_table_compact": rel_path(args.materialization_dir / "control_table_compact.csv"),
            "blocked_wording_checklist": rel_path(args.materialization_dir / "blocked_wording_checklist.csv"),
        },
        "output_artifacts": {
            "artifact_root": rel_path(args.output_dir),
            "summary": rel_path(args.output_dir / "summary.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "review_checks": rel_path(args.output_dir / "review_checks.csv"),
            "review_decision": rel_path(args.output_dir / "review_decision.csv"),
            "wording_gate": rel_path(args.output_dir / "wording_gate.csv"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "next_todo": NEXT_TODO,
    }
    write_json(args.output_dir / "summary.json", summary_out)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
