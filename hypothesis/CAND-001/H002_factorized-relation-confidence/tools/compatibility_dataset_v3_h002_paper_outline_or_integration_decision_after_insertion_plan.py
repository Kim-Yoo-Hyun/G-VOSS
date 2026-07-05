#!/usr/bin/env python3
"""Decide whether H002 should become an outline, H001 integration, or artifact."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
DEFAULT_INSERTION_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_paper_draft_insertion_plan_after_main_validation_table_review"
)
DEFAULT_POBS_CI_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_ci_qualitative_failure_wording_after_pobs_prel_review"
)
DEFAULT_TABLE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_h002_paper_outline_or_integration_decision_after_insertion_plan"
)

EXPECTED_INSERTION_STATUS = "h002_paper_draft_insertion_plan_after_main_validation_table_review_ready"
EXPECTED_INSERTION_NEXT = "compatibility_dataset_v3_h002_paper_outline_or_integration_decision_after_insertion_plan"
EXPECTED_POBS_CI_STATUS = "h002_ci_qualitative_failure_wording_after_pobs_prel_review_ready"
SCHEMA_VERSION = "h002_paper_outline_or_integration_decision_after_insertion_plan_v1"
STATUS_READY = "h002_paper_outline_or_integration_decision_after_insertion_plan_ready"
STATUS_ERROR = "h002_paper_outline_or_integration_decision_after_insertion_plan_input_errors"
SELECTED_PATH = "open_h002_standalone_outline_candidate_no_h001_edit_no_new_paper_root"
NEXT_TODO = "compatibility_dataset_v3_h002_standalone_outline_gap_review_after_decision"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--insertion-dir", type=Path, default=DEFAULT_INSERTION_DIR)
    parser.add_argument("--pobs-ci-dir", type=Path, default=DEFAULT_POBS_CI_DIR)
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


def validate(
    insertion: dict[str, Any],
    pobs: dict[str, Any],
    main_rows: list[dict[str, str]],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if insertion.get("status") != EXPECTED_INSERTION_STATUS:
        errors.append({"error_type": "unexpected_insertion_status", "actual": insertion.get("status")})
    if insertion.get("next_todo") != EXPECTED_INSERTION_NEXT:
        errors.append({"error_type": "unexpected_insertion_next_todo", "actual": insertion.get("next_todo")})
    if insertion.get("validation_errors") != 0:
        errors.append({"error_type": "insertion_validation_errors", "actual": insertion.get("validation_errors")})
    if pobs.get("status") != EXPECTED_POBS_CI_STATUS:
        errors.append({"error_type": "unexpected_pobs_ci_status", "actual": pobs.get("status")})
    if pobs.get("validation_errors") != 0:
        errors.append({"error_type": "pobs_ci_validation_errors", "actual": pobs.get("validation_errors")})
    if pobs.get("paper_promotion_pass") is True:
        errors.append({"error_type": "unexpected_pobs_paper_promotion_pass"})
    if line_count(args.pobs_ci_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "pobs_ci_validation_error_file_not_empty"})
    k_values = sorted(int(row["K"]) for row in main_rows if row.get("K"))
    if k_values != [5, 10, 20, 50, 100]:
        errors.append({"error_type": "unexpected_main_table_k_grid", "actual": k_values})
    return errors


def decision_matrix() -> list[dict[str, Any]]:
    return [
        {
            "option": "open_h002_standalone_outline_candidate",
            "decision": "selected",
            "rationale": "H002 has a coherent factorized compatibility/reranking claim with validation-level evidence, but it is methodologically distinct from H001/GeoCalib and should not overload the active H001 manuscript.",
            "action_now": "Create outline artifact inside H002 only; do not create a new root paper folder yet.",
        },
        {
            "option": "integrate_into_h001_manuscript_now",
            "decision": "rejected_now",
            "rationale": "H001 is already a scoped calibrated geometry-consistency paper. H002 introduces T_e/G_e/Z_e/Q_e decomposition, C_e compatibility, and p_obs/p_rel selective decision; merging now would blur the H001 claim and expand the paper beyond its locked evidence boundary.",
            "action_now": "No H001 manuscript edit.",
        },
        {
            "option": "keep_h002_as_hypothesis_artifact_only",
            "decision": "rejected_as_final_position",
            "rationale": "H002 has enough validation-level mechanism and reranking evidence to deserve an independent outline candidate, even though official-test/SOTA and calibrated p_obs/p_rel claims remain blocked.",
            "action_now": "Keep as hypothesis-owned outline candidate until paper-root promotion is explicitly requested.",
        },
        {
            "option": "create_new_paper_root_now",
            "decision": "deferred",
            "rationale": "Repo rules avoid premature paper-folder proliferation. The next step should review outline gaps and evidence needs before creating a durable paper workspace.",
            "action_now": "No new top-level paper or venue subtree.",
        },
    ]


def claim_position() -> list[dict[str, Any]]:
    return [
        {
            "claim_component": "core_method",
            "paper_position": "main",
            "allowed_wording": "Factorized compatibility reranking separates semantic content T_e, predicate-independent geometry evidence G_e, and source confidence Z_e before final source reranking.",
            "blocked_wording": "Do not present this as a new end-to-end 3DSSG predictor.",
        },
        {
            "claim_component": "main_validation_table",
            "paper_position": "main_result_candidate",
            "allowed_wording": "Official 3DSSG validation split comparison of S0_source_score and S2_source_x_Ce on VL-SAT/Open3DSG validation predictions.",
            "blocked_wording": "Do not call it official test, leaderboard, or SOTA.",
        },
        {
            "claim_component": "p_obs_p_rel",
            "paper_position": "method_component_and_stress_test",
            "allowed_wording": "Selective decision layer that separates observability from observable-edge reliability; stress-test passed on synthetic missing-evidence controls.",
            "blocked_wording": "Do not claim calibrated p_obs/p_rel reliability is solved or independently human-labeled.",
        },
        {
            "claim_component": "support_contact",
            "paper_position": "failure_taxonomy",
            "allowed_wording": "A challenging route showing current geometry evidence is insufficient for contact/pose-heavy relations.",
            "blocked_wording": "Do not present support/contact as solved.",
        },
        {
            "claim_component": "open3dsg",
            "paper_position": "second_source_case",
            "allowed_wording": "Open-vocabulary source evaluated after mapping predictions to closed-vocabulary 3DSSG labels.",
            "blocked_wording": "Do not claim unconstrained open-set GT evaluation.",
        },
    ]


def paper_outline() -> str:
    return """# H002 Standalone Paper Outline Candidate

Working title:

```text
Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations
```

## Core Claim

3D Scene Graph relation confidence should not be treated as relation
reliability. A source score mixes semantic plausibility, geometry compatibility,
and source-specific ranking behavior. H002 separates these factors into
semantic content `T_e`, predicate-independent geometry evidence `G_e`, source
confidence `Z_e`, compatibility `C_e`, observability quality `Q_e`, and
selective decision heads `p_obs/p_rel`.

## Contributions

1. A factorized relation reliability formulation:
   `T_e`, `G_e`, `Z_e`, `C_e`, `Q_e`, `p_obs`, `p_rel`.
2. A compatibility scorer `C_e = compatibility(T_e, G_e)` that excludes source
   confidence from compatibility estimation and combines it with `Z_e` only at
   reranking time.
3. A validation-level source reranking benchmark comparing `S0_source_score`
   with `S2_source_x_Ce` on VL-SAT and Open3DSG validation predictions.
4. Counterfactual controls: wrong predicate, shuffled geometry/compatibility,
   subject-object/sign controls, and route-family caveats.
5. A selective-decision layer that separates observability (`p_obs`) from
   observable-edge reliability (`p_rel`), currently supported as a stress-test
   rather than a calibrated benchmark claim.
6. A failure taxonomy showing where current geometry evidence is insufficient,
   especially support/contact and observability-heavy routes.

## Paper Structure

1. Introduction
   - relation source confidence is not relation reliability.
   - fixed semantic-geometry fusion is insufficient.
   - relation family and evidence route matter.
2. Related Work
   - 3D Scene Graph relation prediction.
   - reliability/calibration/selective prediction.
   - multimodal/factorized evidence fusion.
   - geometry-aware relation verification.
3. Method
   - factor definitions: `T_e`, `G_e`, `Z_e`, `C_e`, `Q_e`.
   - compatibility scorer and source reranking.
   - selective decision: `p_obs` then `p_rel`.
   - controls and blocked leakage fields.
4. Experiments
   - official 3DSSG validation split.
   - VL-SAT/Open3DSG validation predictions.
   - mechanism metrics: semantic-only, geometry-only, concat, compatibility.
   - source reranking metrics: Recall@K and Violation@K.
   - p_obs/p_rel stress test and CI.
5. Analysis
   - family-wise behavior.
   - support/contact failure taxonomy.
   - calibration and observability limitations.
6. Limitations
   - no official-test claim.
   - p_obs/p_rel uses synthetic missing-evidence controls.
   - support/contact, attachment, containment not solved.

## Main Tables

- Table 1: mechanism evaluation by route family.
- Table 2: source reranking Recall@K / Violation@K.
- Table 3: counterfactual controls.
- Table 4: p_obs/p_rel selective stress test with CI.
- Table 5: failure taxonomy and route boundary.

## Current Promotion Boundary

This is an H002 standalone outline candidate, not a new paper workspace yet.
Do not edit the active H001 manuscript and do not create a new top-level paper
folder until the outline-gap review is complete.
"""


def integration_boundary() -> str:
    return """# H002 Integration Boundary

## Selected Path

```text
open_h002_standalone_outline_candidate_no_h001_edit_no_new_paper_root
```

## Why Not H001 Integration Now

H001/GeoCalib is already framed as calibrated geometry-consistency evaluation
and reranking. H002 introduces a different method shape:

- factorized semantic/geometry/source/observability decomposition
- predicate-geometry compatibility `C_e`
- source reranking with `S2_source_x_Ce`
- selective decision via `p_obs/p_rel`

Putting H002 directly into H001 now would make the active H001 manuscript less
focused and would force H001 to absorb H002's remaining caveats: validation-only
benchmarking, support/contact failure, and non-calibrated p_obs/p_rel wording.

## What Is Allowed Now

- Keep H002 as an independent paper-outline candidate under the H002 hypothesis
  folder.
- Use the existing validation table, controls, p_obs/p_rel stress test, and
  failure taxonomy as outline material.
- Decide later whether to create a new paper workspace.

## What Is Blocked Now

- editing the active H001 manuscript
- claiming H002 official-test/SOTA/leaderboard performance
- claiming calibrated p_obs/p_rel reliability is solved
- creating a new top-level paper folder before outline-gap review

## Reopen Conditions

Create a durable H002 paper workspace only after:

1. outline-gap review is complete,
2. target venue and paper scope are selected,
3. the user explicitly approves opening a new paper workspace or integrating
   into an existing manuscript.
"""


def report_text(status: str, errors: list[dict[str, Any]]) -> str:
    return f"""# H002 Paper Outline / Integration Decision

## 목적

H002를 독립 paper outline으로 열지, H001 manuscript에 통합할지, 또는 hypothesis
artifact로 유지할지 결정했다.

## 결과

```text
status = {status}
selected_path = {SELECTED_PATH}
validation_errors = {len(errors)}
next_todo = {NEXT_TODO}
```

결론은 H002를 독립 paper-outline candidate로 유지하는 것이다. 지금은 H001
manuscript를 수정하지 않고, 새 top-level paper folder도 만들지 않는다.
"""


def main() -> int:
    args = parse_args()
    insertion = read_json(args.insertion_dir / "summary.json")
    pobs = read_json(args.pobs_ci_dir / "summary.json")
    main_rows = read_csv(args.table_dir / "main_validation_table.csv")
    errors = validate(insertion, pobs, main_rows, args)
    status = STATUS_ERROR if errors else STATUS_READY

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "decision_matrix.csv", decision_matrix())
    write_csv(args.output_dir / "claim_position.csv", claim_position())
    (args.output_dir / "paper_outline.md").write_text(paper_outline(), encoding="utf-8")
    (args.output_dir / "integration_boundary.md").write_text(integration_boundary(), encoding="utf-8")
    (args.output_dir / "report.md").write_text(report_text(status, errors), encoding="utf-8")
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "selected_path": SELECTED_PATH,
        "decision": {
            "open_h002_standalone_outline_candidate": True,
            "h001_manuscript_edit_now": False,
            "new_top_level_paper_folder_now": False,
            "keep_hypothesis_only_as_final_position": False,
            "paper_promotion_now": False,
            "official_test_claim_allowed": False,
            "sota_or_leaderboard_claim_allowed": False,
            "calibrated_pobs_prel_claim_allowed": False,
        },
        "input_artifacts": {
            "insertion_plan": rel_path(args.insertion_dir),
            "pobs_ci": rel_path(args.pobs_ci_dir),
            "main_validation_table": rel_path(args.table_dir / "main_validation_table.csv"),
        },
        "output_artifacts": {
            "artifact_root": rel_path(args.output_dir),
            "summary": rel_path(args.output_dir / "summary.json"),
            "decision_matrix": rel_path(args.output_dir / "decision_matrix.csv"),
            "claim_position": rel_path(args.output_dir / "claim_position.csv"),
            "paper_outline": rel_path(args.output_dir / "paper_outline.md"),
            "integration_boundary": rel_path(args.output_dir / "integration_boundary.md"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "validation_errors": len(errors),
        "next_todo": NEXT_TODO,
    }
    write_json(args.output_dir / "summary.json", summary)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
