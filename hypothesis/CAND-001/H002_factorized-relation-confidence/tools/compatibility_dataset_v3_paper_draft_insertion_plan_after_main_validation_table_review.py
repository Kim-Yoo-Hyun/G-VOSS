#!/usr/bin/env python3
"""Plan H002 paper-draft insertion after main validation table review."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_REVIEW_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_main_validation_table_review_after_materialization"
)
DEFAULT_TABLE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_paper_draft_insertion_plan_after_main_validation_table_review"
)

EXPECTED_REVIEW_STATUS = "h002_main_validation_table_review_after_materialization_ready"
EXPECTED_REVIEW_NEXT = (
    "compatibility_dataset_v3_paper_draft_insertion_plan_after_main_validation_table_review"
)
SCHEMA_VERSION = "h002_paper_draft_insertion_plan_after_main_validation_table_review_v1"
STATUS_READY = "h002_paper_draft_insertion_plan_after_main_validation_table_review_ready"
STATUS_ERRORS = "h002_paper_draft_insertion_plan_after_main_validation_table_review_input_errors"
SELECTED_PATH = "paper_draft_insertion_plan_locked_no_manuscript_edit"
NEXT_TODO = "compatibility_dataset_v3_h002_paper_outline_or_integration_decision_after_insertion_plan"
K_GRID = [5, 10, 20, 50, 100]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--table-dir", type=Path, default=DEFAULT_TABLE_DIR)
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


def validate_inputs(
    review_summary: dict[str, Any],
    main_rows: list[dict[str, str]],
    caveats: list[dict[str, str]],
    controls: list[dict[str, str]],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if review_summary.get("status") != EXPECTED_REVIEW_STATUS:
        errors.append(
            {
                "error_type": "unexpected_review_status",
                "actual": review_summary.get("status"),
                "expected": EXPECTED_REVIEW_STATUS,
            }
        )
    if review_summary.get("next_todo") != EXPECTED_REVIEW_NEXT:
        errors.append(
            {
                "error_type": "unexpected_review_next_todo",
                "actual": review_summary.get("next_todo"),
                "expected": EXPECTED_REVIEW_NEXT,
            }
        )
    if review_summary.get("validation_errors") != 0:
        errors.append(
            {
                "error_type": "review_validation_errors",
                "actual": review_summary.get("validation_errors"),
            }
        )
    if line_count(args.review_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "review_validation_errors_file_not_empty"})

    k_values = sorted(int(row["K"]) for row in main_rows if row.get("K"))
    if k_values != K_GRID:
        errors.append({"error_type": "unexpected_k_grid", "actual": k_values, "expected": K_GRID})
    if len(caveats) != 3:
        errors.append({"error_type": "unexpected_caveat_row_count", "actual": len(caveats)})
    if len(controls) != 15:
        errors.append({"error_type": "unexpected_control_row_count", "actual": len(controls)})

    bad_recall = [
        row
        for row in main_rows
        if as_float(row.get("Delta_Recall@K")) is None
        or as_float(row.get("Delta_Recall@K")) <= 0.0
    ]
    bad_violation = [
        row
        for row in main_rows
        if as_float(row.get("Delta_Violation@K")) is None
        or as_float(row.get("Delta_Violation@K")) >= 0.0
    ]
    if bad_recall:
        errors.append({"error_type": "primary_table_nonpositive_recall_delta", "rows": len(bad_recall)})
    if bad_violation:
        errors.append({"error_type": "primary_table_nonnegative_violation_delta", "rows": len(bad_violation)})
    return errors


def insertion_plan_rows() -> list[dict[str, Any]]:
    return [
        {
            "paper_area": "Method",
            "target_location": "after score definition",
            "insert": "Define C_e = compatibility(T_e, G_e) and S2 = normalized_source_score(Z_e) * C_e.",
            "status": "planned",
            "notes": "Emphasize that Z_e is excluded from C_e and combined only for final reranking.",
        },
        {
            "paper_area": "Experiments",
            "target_location": "validation setup subsection",
            "insert": "State official 3DSSG validation split, VL-SAT/Open3DSG validation predictions, closed-label mapping for quantitative Recall@K, and custom Violation@K.",
            "status": "planned",
            "notes": "Explicitly state that official test is not used.",
        },
        {
            "paper_area": "Results",
            "target_location": "main validation table",
            "insert": "Insert main_validation_table.md as Table candidate for S0 vs S2 over K={5,10,20,50,100}.",
            "status": "planned",
            "notes": "Use validation-only caption and 3 caveat rows.",
        },
        {
            "paper_area": "Appendix or Result Notes",
            "target_location": "controls and caveats",
            "insert": "Report C_e-only as diagnostic, and wrong-T / shuffled-C_e as violation-risk controls.",
            "status": "planned",
            "notes": "Do not claim universal recall collapse.",
        },
        {
            "paper_area": "Blocked",
            "target_location": "all paper sections",
            "insert": "Do not add official-test, SOTA, leaderboard, or uniform-improvement claims.",
            "status": "blocked",
            "notes": "Reopen only with independent relation-test labels or accepted evaluation server.",
        },
    ]


def blocked_wording_rows() -> list[dict[str, Any]]:
    return [
        {
            "blocked_text": "official 3DSSG test result",
            "reason": "official test relation labels/evaluation server remain unconfirmed",
            "replacement": "official 3DSSG validation split result",
        },
        {
            "blocked_text": "SOTA / leaderboard / state-of-the-art",
            "reason": "H002 is a validation-level custom evaluation, not leaderboard submission",
            "replacement": "main validation comparison",
        },
        {
            "blocked_text": "uniform improvement across all source/family/K cells",
            "reason": "3 source-family-K Recall@K cells regress slightly",
            "replacement": "primary weighted validation improvement with explicit caveats",
        },
        {
            "blocked_text": "Open3DSG open-set GT evaluation",
            "reason": "quantitative Recall@K uses closed-vocabulary 3DSSG mapping",
            "replacement": "Open3DSG as open-vocabulary source, closed-label quantitative evaluation",
        },
        {
            "blocked_text": "C_e alone is deployable",
            "reason": "C_e-only has low violation but low low-K recall",
            "replacement": "C_e-only diagnostic ablation; deployable score is S2_source_x_Ce",
        },
    ]


def caption_text() -> str:
    return (
        "Main validation comparison on the official 3DSSG validation split. "
        "We rerank VL-SAT and Open3DSG validation predictions using "
        "`S2_source_x_Ce`, where `C_e` is estimated from `T_e` and `G_e` before "
        "being combined with the source score `Z_e`. Open3DSG is used as an "
        "open-vocabulary relation source, while quantitative Recall@K is "
        "computed after mapping predictions to closed-vocabulary 3DSSG labels. "
        "Violation@K is our geometry-consistency metric. This is not an official "
        "test or leaderboard result."
    )


def footnote_text() -> str:
    return (
        "Three source-family-K cells show small Recall@K regressions "
        "(`Open3DSG/size_relative@5`, `VL-SAT/relative_vertical@5`, "
        "`VL-SAT/size_relative@50`), so the result should not be described as "
        "uniform improvement across all cells."
    )


def manuscript_snippets() -> str:
    return """# H002 Paper Draft Snippets

## Result Paragraph

On the official 3DSSG validation split, compatibility-aware reranking improves
the primary recall-violation tradeoff over the source-score baseline for the
clean comparison families (`relative_vertical` and `size_relative`). Across
K={5,10,20,50,100}, `S2_source_x_Ce` increases Recall@K while reducing
Violation@K relative to `S0_source_score`.

## Control Paragraph

The diagnostic `C_e`-only score reduces violation but is not deployable because
it loses low-K recall without source confidence. Wrong-T and shuffled-C_e
controls worsen violation-risk ranking, supporting that the gain comes from
predicate-geometry compatibility rather than a source-score-only effect.

## Caveat Paragraph

This evaluation uses the official 3DSSG validation split and should not be
reported as an official test, leaderboard, or SOTA result. Open3DSG is treated as
an open-vocabulary source, but quantitative Recall@K is computed using
closed-vocabulary 3DSSG label mapping. We also disclose three source-family-K
cells with small Recall@K regressions and avoid uniform-improvement wording.
"""


def write_report(path: Path, status: str, validation_errors: int) -> None:
    lines = [
        "# H002 Paper Draft Insertion Plan",
        "",
        "## Purpose",
        "",
        "Lock where and how the reviewed H002 validation table can enter a paper draft. "
        "This stage does not edit manuscript files, run metrics, or use official test data.",
        "",
        "## Result",
        "",
        "```text",
        f"status = {status}",
        f"selected_path = {SELECTED_PATH if validation_errors == 0 else 'paper_draft_insertion_plan_blocked'}",
        f"validation_errors = {validation_errors}",
        f"next_todo = {NEXT_TODO}",
        "```",
        "",
        "## Insertion Decision",
        "",
        "- Put the table in the H002 paper/results draft path as a validation-level main table candidate.",
        "- Use the validation-only caption and footnote from this artifact.",
        "- Keep controls/caveats near the table or in appendix notes.",
        "- Do not edit the current H001 manuscript from this gate.",
        "- Do not claim official test, SOTA, leaderboard, or uniform improvement.",
        "",
        "## Key Files",
        "",
        "| File | Role |",
        "| --- | --- |",
        "| `insertion_plan.csv` | section-by-section insertion plan |",
        "| `caption_and_footnotes.md` | caption and caveat wording |",
        "| `manuscript_snippets.md` | draft-ready result/control/caveat paragraphs |",
        "| `blocked_wording.csv` | wording that remains blocked |",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    review_summary = read_json(args.review_dir / "summary.json")
    main_rows = read_csv(args.table_dir / "main_validation_table.csv")
    caveats = read_csv(args.table_dir / "source_family_caveats.csv")
    controls = read_csv(args.table_dir / "control_table_compact.csv")
    errors = validate_inputs(review_summary, main_rows, caveats, controls, args)

    status = STATUS_READY if not errors else STATUS_ERRORS
    selected_path = SELECTED_PATH if not errors else "paper_draft_insertion_plan_blocked"

    write_csv(args.output_dir / "insertion_plan.csv", insertion_plan_rows())
    write_csv(args.output_dir / "blocked_wording.csv", blocked_wording_rows())
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", status, len(errors))
    (args.output_dir / "caption_and_footnotes.md").write_text(
        "# Caption And Footnotes\n\n"
        "## Caption\n\n"
        f"{caption_text()}\n\n"
        "## Required Footnote\n\n"
        f"{footnote_text()}\n",
        encoding="utf-8",
    )
    (args.output_dir / "manuscript_snippets.md").write_text(
        manuscript_snippets(),
        encoding="utf-8",
    )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(errors),
        "decision": {
            "paper_draft_insertion_plan_locked": not errors,
            "manuscript_files_edited": False,
            "recommended_table_position": "H002 results main validation table candidate",
            "h001_manuscript_edit_now": False,
            "official_test_usage": False,
            "official_test_claim_allowed": False,
            "sota_or_leaderboard_claim_allowed": False,
            "uniform_improvement_claim_allowed": False,
            "next_todo": NEXT_TODO,
        },
        "input_artifacts": {
            "review_summary": rel_path(args.review_dir / "summary.json"),
            "main_validation_table": rel_path(args.table_dir / "main_validation_table.csv"),
            "main_validation_table_markdown": rel_path(args.table_dir / "main_validation_table.md"),
            "source_family_caveats": rel_path(args.table_dir / "source_family_caveats.csv"),
            "control_table_compact": rel_path(args.table_dir / "control_table_compact.csv"),
        },
        "output_artifacts": {
            "artifact_root": rel_path(args.output_dir),
            "summary": rel_path(args.output_dir / "summary.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "insertion_plan": rel_path(args.output_dir / "insertion_plan.csv"),
            "caption_and_footnotes": rel_path(args.output_dir / "caption_and_footnotes.md"),
            "manuscript_snippets": rel_path(args.output_dir / "manuscript_snippets.md"),
            "blocked_wording": rel_path(args.output_dir / "blocked_wording.csv"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "next_todo": NEXT_TODO,
    }
    write_json(args.output_dir / "summary.json", summary)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
