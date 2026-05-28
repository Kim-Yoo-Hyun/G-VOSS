#!/usr/bin/env python3
"""Inspect attachment-deferred G4 errors and freeze a visual sanity queue.

This G4b step reads the G4 GT/counterfactual policy-smoke outputs, separates
false violations, false satisfactions, and uncertain-heavy cases, then creates
a deterministic targeted visual sanity queue. It does not inspect source
predictions, fit calibration, compute metrics, or change the main AAAI claim.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h001_attachment_deferred_error_visual_sanity_v1"
STATUS = "attachment_deferred_error_visual_sanity_plan_ready_no_source_metrics"
TARGET_QUEUE_SIZE = 50
DEFAULT_ATTACHMENT_ROOT = Path("experiments/H001_geom_reliability/sources/attachment_deferred")
DEFAULT_GT_POLICY_DIR = DEFAULT_ATTACHMENT_ROOT / "gt_policy_smoke"
DEFAULT_OUT = DEFAULT_ATTACHMENT_ROOT / "error_visual_sanity"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--gt-policy-dir", type=Path, default=DEFAULT_GT_POLICY_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--target-queue-size", type=int, default=TARGET_QUEUE_SIZE)
    return parser.parse_args()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def safe_float(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def evidence_snapshot(evidence: dict[str, Any] | None) -> dict[str, Any]:
    if not evidence:
        return {
            "evidence_missing": True,
            "subject_label": None,
            "object_label": None,
            "min_point_distance_m": None,
            "near_contact_point_count": None,
            "contact_patch_score": None,
            "surface_type": None,
            "surface_normal_class": None,
            "floor_clearance_m": None,
            "support_explanation_score": None,
            "class_pair_prior": None,
        }
    point = evidence.get("point_contact_evidence", {})
    surface = evidence.get("surface_evidence", {})
    gravity = evidence.get("gravity_evidence", {})
    support = evidence.get("contradictory_support_evidence", {})
    affordance = evidence.get("affordance_context", {})
    return {
        "evidence_missing": False,
        "subject_label": evidence.get("subject_label"),
        "object_label": evidence.get("object_label"),
        "min_point_distance_m": point.get("min_point_distance_m"),
        "near_contact_point_count": point.get("near_contact_point_count"),
        "contact_patch_score": point.get("contact_patch_score"),
        "surface_type": surface.get("selected_surface_type"),
        "surface_normal_class": surface.get("selected_surface_normal_class"),
        "floor_clearance_m": gravity.get("floor_clearance_m"),
        "hanging_geometry_score": gravity.get("hanging_geometry_score"),
        "floor_or_table_supported": support.get("floor_or_table_supported"),
        "support_explanation_score": support.get("support_explanation_score"),
        "class_pair_prior": affordance.get("class_pair_prior"),
        "quality_flags": evidence.get("quality_flags", []),
    }


def case_type(eval_row: dict[str, Any]) -> str:
    status = eval_row["decision"]["verification_status"]
    target = int(eval_row["target_geom_valid"])
    if target == 1 and status == "violated":
        return "false_violation_positive"
    if target == 0 and status == "satisfied":
        return "false_satisfaction_counterfactual"
    if target == 1 and status == "uncertain":
        return "uncertain_positive"
    if target == 0 and status == "uncertain":
        return "uncertain_counterfactual"
    if target == 1 and status == "satisfied":
        return "strict_satisfied_positive"
    if target == 0 and status == "violated":
        return "strict_violated_counterfactual"
    return "other"


def calibration_disposition(eval_row: dict[str, Any]) -> str:
    status = eval_row["decision"]["verification_status"]
    target = int(eval_row["target_geom_valid"])
    if target == 1 and status == "satisfied":
        return "use_as_strict_positive"
    if target == 1 and status == "uncertain":
        return "soft_positive_or_review_before_calibration"
    if target == 1 and status == "violated":
        return "review_false_violation_before_any_positive_calibration_use"
    if target == 0 and status == "violated":
        return "use_as_strict_negative"
    if target == 0 and status == "uncertain":
        return "skip_or_review_uncertain_negative"
    if target == 0 and status == "satisfied":
        return "exclude_or_review_counterfactual_seed_false_satisfaction"
    return "skip_unknown"


def likely_issue(eval_row: dict[str, Any], evidence: dict[str, Any] | None) -> str:
    decision = eval_row["decision"]
    ctype = case_type(eval_row)
    snapshot = evidence_snapshot(evidence)
    reasons = set(decision.get("reason_codes", []))
    strategy = eval_row.get("strategy")
    min_dist = safe_float(snapshot.get("min_point_distance_m"))
    near_count = int(snapshot.get("near_contact_point_count") or 0)
    surface_type = snapshot.get("surface_type")
    subtype = decision.get("subtype_hint")

    if ctype == "false_satisfaction_counterfactual":
        if strategy == "far_object_pair" and (near_count > 0 or (min_dist is not None and min_dist <= 0.05)):
            return "counterfactual_seed_not_geometrically_negative_far_pair_has_direct_contact"
        if strategy == "wrong_pair_attachment" and near_count > 0:
            return "wrong_pair_counterfactual_has_visible_contact_or_contiguity"
        return "policy_too_permissive_or_counterfactual_seed_invalid"
    if ctype == "false_violation_positive":
        if surface_type in {"floor", "unknown"}:
            return "positive_annotation_or_object_role_conflicts_with_surface_type"
        if {"clear_far_from_attachment_surface", "no_near_contact_points"} <= reasons:
            return "positive_gt_far_from_extracted_surface_needs_visual_check"
        return "policy_too_strict_for_positive_gt"
    if ctype == "uncertain_positive":
        if subtype == "ambiguous_functional_attachment":
            return "positive_functional_attachment_semantics_ambiguous"
        if "distance_in_uncertain_band" in reasons:
            return "positive_contact_threshold_or_surface_normal_ambiguous"
        if "ambiguous_draped_or_occluded_hanging" in reasons:
            return "positive_hanging_occlusion_or_draping_ambiguous"
        return "positive_uncertain_needs_visual_or_policy_review"
    if ctype == "uncertain_counterfactual":
        if strategy == "far_object_pair" and "distance_in_uncertain_band" in reasons:
            return "counterfactual_far_pair_margin_not_clear_enough"
        if subtype == "ambiguous_functional_attachment":
            return "counterfactual_functional_attachment_ambiguous_skip"
        return "counterfactual_uncertain_skip_or_review"
    if ctype == "strict_violated_counterfactual":
        return "strict_negative_candidate"
    if ctype == "strict_satisfied_positive":
        return "strict_positive_candidate"
    return "other"


def recommended_action(ctype: str, issue: str) -> str:
    if ctype == "false_satisfaction_counterfactual":
        return "exclude_from_negative_calibration_and_review_seed_generation_margin"
    if ctype == "false_violation_positive":
        return "visual_check_before_relaxing_policy_or_excluding_positive"
    if ctype == "uncertain_positive":
        return "keep_nonviolated_but_do_not_use_as_strict_positive_without_review"
    if ctype == "uncertain_counterfactual":
        return "skip_as_negative_or_review_if_needed_for_calibration_balance"
    if ctype == "strict_violated_counterfactual":
        return "eligible_as_strict_negative_if_no_visual_contradiction"
    if ctype == "strict_satisfied_positive":
        return "eligible_as_strict_positive_if_no_visual_contradiction"
    return "skip"


def severity_score(row: dict[str, Any]) -> tuple[int, str]:
    ctype = row["case_type"]
    snapshot = row["evidence_snapshot"]
    near_count = int(snapshot.get("near_contact_point_count") or 0)
    min_dist = safe_float(snapshot.get("min_point_distance_m"))
    strategy = row.get("strategy") or ""
    score = 0
    if ctype == "false_satisfaction_counterfactual":
        score = 100
        if strategy == "far_object_pair":
            score += 20
        if near_count > 0:
            score += 10
        if min_dist is not None and min_dist <= 0.05:
            score += 10
    elif ctype == "false_violation_positive":
        score = 95
        if row["predicate_label"] == "attached to":
            score += 5
    elif ctype == "uncertain_positive":
        score = 70
        if row["subtype_hint"].startswith("ambiguous"):
            score += 5
    elif ctype == "uncertain_counterfactual":
        score = 60
        if strategy == "far_object_pair":
            score += 5
    elif ctype == "strict_violated_counterfactual":
        score = 40
    elif ctype == "strict_satisfied_positive":
        score = 30
    return -score, row["case_id"]


def build_case(
    eval_row: dict[str, Any],
    evidence: dict[str, Any] | None,
    *,
    index: int,
    repo_root: Path,
) -> dict[str, Any]:
    decision = eval_row["decision"]
    ctype = case_type(eval_row)
    issue = likely_issue(eval_row, evidence)
    scan_id = decision["scan_id"]
    case_id = f"attach_g4b_{index:04d}_{ctype}"
    return {
        "schema_version": "h001_attachment_deferred_error_case_v1",
        "case_id": case_id,
        "seed_id": eval_row.get("seed_id"),
        "row_id": decision["row_id"],
        "case_type": ctype,
        "eval_verdict": eval_row["eval_verdict"],
        "target_geom_valid": int(eval_row["target_geom_valid"]),
        "verification_status": decision["verification_status"],
        "split_role": eval_row["split_role"],
        "strategy": eval_row.get("strategy"),
        "predicate_label": decision["predicate_label"],
        "subtype_hint": decision["subtype_hint"],
        "scan_id": scan_id,
        "subgraph_id": decision["subgraph_id"],
        "subject_id": decision["subject_id"],
        "object_id": decision["object_id"],
        "reason_codes": decision.get("reason_codes", []),
        "evidence_requirements_met": decision.get("evidence_requirements_met", []),
        "evidence_snapshot": evidence_snapshot(evidence),
        "likely_issue": issue,
        "recommended_action": recommended_action(ctype, issue),
        "calibration_disposition": calibration_disposition(eval_row),
        "local_paths": {
            "scan_dir": relpath(repo_root, repo_root / "local_dataset/3RScan/scans" / scan_id),
            "mesh": relpath(
                repo_root,
                repo_root
                / "local_dataset/3RScan/scans"
                / scan_id
                / "labels.instances.annotated.v2.ply",
            ),
            "semseg": relpath(
                repo_root,
                repo_root / "local_dataset/3RScan/scans" / scan_id / "semseg.v2.json",
            ),
        },
    }


def count_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: value for key, value in sorted(counter.items())}


def nested_count_dict(counter: dict[str, Counter[str]]) -> dict[str, dict[str, int]]:
    return {key: count_dict(value) for key, value in sorted(counter.items())}


def select_visual_queue(cases: list[dict[str, Any]], target_size: int) -> list[dict[str, Any]]:
    review_case_types = {
        "false_satisfaction_counterfactual",
        "false_violation_positive",
        "uncertain_positive",
        "uncertain_counterfactual",
    }
    review_types = [
        ("false_satisfaction_counterfactual", 15),
        ("false_violation_positive", 15),
        ("uncertain_positive", 10),
        ("uncertain_counterfactual", 10),
    ]
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        by_type[case["case_type"]].append(case)
    for ctype, quota in review_types:
        candidates = sorted(by_type.get(ctype, []), key=severity_score)
        for candidate in candidates[:quota]:
            selected.append(candidate)
            selected_ids.add(candidate["case_id"])
    label_minimums = {
        "hanging on": min(6, len([case for case in cases if case["predicate_label"] == "hanging on" and case["case_type"] in review_case_types])),
        "connected to": min(6, len([case for case in cases if case["predicate_label"] == "connected to" and case["case_type"] in review_case_types])),
    }
    for label, minimum in label_minimums.items():
        current = len([case for case in selected if case["predicate_label"] == label])
        if current >= minimum:
            continue
        candidates = [
            case
            for case in sorted(cases, key=severity_score)
            if case["predicate_label"] == label
            and case["case_type"] in review_case_types
            and case["case_id"] not in selected_ids
        ]
        for candidate in candidates[: minimum - current]:
            selected.append(candidate)
            selected_ids.add(candidate["case_id"])
    while len(selected) > target_size:
        label_counts = Counter(case["predicate_label"] for case in selected)
        removable = [
            case
            for case in selected
            if label_counts[case["predicate_label"]] > label_minimums.get(case["predicate_label"], 0)
        ]
        if not removable:
            break
        remove_case = min(removable, key=lambda case: -severity_score(case)[0])
        selected = [case for case in selected if case["case_id"] != remove_case["case_id"]]
        selected_ids.discard(remove_case["case_id"])
    if len(selected) < target_size:
        remaining = [
            case
            for case in sorted(cases, key=severity_score)
            if case["case_id"] not in selected_ids
            and case["case_type"] in review_case_types
        ]
        for candidate in remaining:
            if len(selected) >= target_size:
                break
            selected.append(candidate)
            selected_ids.add(candidate["case_id"])
    selected = selected[:target_size]
    queue_rows = []
    for queue_index, case in enumerate(selected, start=1):
        queue_row = {
            "schema_version": "h001_attachment_deferred_visual_queue_v1",
            "queue_index": queue_index,
            "review_status": "pending",
            "reviewer_id": None,
            "visual_label": None,
            "allowed_visual_labels": [
                "policy_correct",
                "policy_too_strict",
                "policy_too_permissive",
                "counterfactual_seed_invalid",
                "annotation_ambiguous",
                "geometry_evidence_bad",
                "cannot_judge",
            ],
            "case": case,
        }
        queue_rows.append(queue_row)
    return queue_rows


def summarize_cases(cases: list[dict[str, Any]], queue: list[dict[str, Any]]) -> dict[str, Any]:
    by_type = Counter(case["case_type"] for case in cases)
    by_label_type: dict[str, Counter[str]] = defaultdict(Counter)
    by_subtype_type: dict[str, Counter[str]] = defaultdict(Counter)
    by_strategy_type: dict[str, Counter[str]] = defaultdict(Counter)
    by_issue = Counter(case["likely_issue"] for case in cases)
    by_disposition = Counter(case["calibration_disposition"] for case in cases)
    queue_by_type = Counter(row["case"]["case_type"] for row in queue)
    queue_by_label = Counter(row["case"]["predicate_label"] for row in queue)
    for case in cases:
        by_label_type[case["predicate_label"]][case["case_type"]] += 1
        by_subtype_type[case["subtype_hint"]][case["case_type"]] += 1
        by_strategy_type[str(case.get("strategy"))][case["case_type"]] += 1
    strict_positive = by_type.get("strict_satisfied_positive", 0)
    strict_negative = by_type.get("strict_violated_counterfactual", 0)
    false_satisfaction = by_type.get("false_satisfaction_counterfactual", 0)
    false_violation = by_type.get("false_violation_positive", 0)
    uncertain = by_type.get("uncertain_positive", 0) + by_type.get("uncertain_counterfactual", 0)
    return {
        "rows": len(cases),
        "by_case_type": count_dict(by_type),
        "by_label_case_type": nested_count_dict(by_label_type),
        "by_subtype_case_type": nested_count_dict(by_subtype_type),
        "by_strategy_case_type": nested_count_dict(by_strategy_type),
        "by_likely_issue": count_dict(by_issue),
        "by_calibration_disposition": count_dict(by_disposition),
        "queue_rows": len(queue),
        "queue_by_case_type": count_dict(queue_by_type),
        "queue_by_label": count_dict(queue_by_label),
        "calibration_readiness": {
            "strict_positive_candidates": strict_positive,
            "strict_negative_candidates": strict_negative,
            "false_satisfaction_counterfactuals_to_exclude_or_review": false_satisfaction,
            "false_violation_positives_to_visual_check": false_violation,
            "uncertain_rows_to_skip_or_review": uncertain,
            "recommended_before_calibration": [
                "exclude false-satisfied counterfactuals from negative calibration unless visual review confirms the seed is valid",
                "visual-check false-violated positives before relaxing policy thresholds",
                "keep uncertain rows out of strict calibration tables unless a separate soft-label protocol is defined",
            ],
        },
        "promotion_readiness": {
            "ready_for_source_metrics": False,
            "reason": "G4b only freezes error review and visual-sanity queue; fitted calibration, controls, source metrics, bootstrap CI, and audit remain missing.",
            "main_AAAI_claim_unchanged": True,
            "requires_final_user_confirmation_before_claim_promotion": True,
        },
    }


def guide_md() -> str:
    return """# Attachment Deferred Visual Sanity Guide

This queue is for G4b review before any attachment-deferred source metrics.

Allowed labels:

- `policy_correct`: the policy decision matches the visible geometry.
- `policy_too_strict`: a positive relation was marked violated despite visible
  evidence or reasonable annotation semantics.
- `policy_too_permissive`: a counterfactual was marked satisfied despite no
  convincing attachment/connection evidence.
- `counterfactual_seed_invalid`: the generated counterfactual is not a valid
  negative because the replacement object is actually in contact or plausibly
  related.
- `annotation_ambiguous`: the 3DSSG relation wording or object role is too
  ambiguous to use as strict calibration evidence.
- `geometry_evidence_bad`: segmented points, surface normal, object id, or mesh
  evidence is visibly wrong.
- `cannot_judge`: the case cannot be judged from available local artifacts.

Do not use this queue as source metric evidence. It is a pre-metric policy and
calibration-risk review queue.
"""


def commands_md() -> str:
    return """# Attachment Deferred G4b Error / Visual Sanity Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm \\
  attachment_deferred_error_visual_sanity
```

Validation:

```bash
python -m py_compile experiments/H001_geom_reliability/scripts/inspect_attachment_policy_errors.py
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/error_visual_sanity/manifest.json >/dev/null
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/error_visual_sanity/summary.json >/dev/null
```

This command generates an error taxonomy, calibration filter, and targeted
visual sanity queue only. It does not fit calibration, score source
predictions, compute metrics, or update the main AAAI claim.
"""


def report_md(manifest: dict[str, Any], summary: dict[str, Any]) -> str:
    cal = summary["calibration_readiness"]
    lines = [
        "# Attachment Deferred G4b Error / Visual Sanity",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Claim Boundary",
        "",
        "This is an error-review and visual-sanity planning artifact. It does not",
        "fit calibration, score VL-SAT/Open3DSG predictions, compute source",
        "metrics, or change the current AAAI main claim.",
        "",
        "## Error Distribution",
        "",
        f"- false satisfaction counterfactuals: `{summary['by_case_type'].get('false_satisfaction_counterfactual', 0)}`",
        f"- false violation positives: `{summary['by_case_type'].get('false_violation_positive', 0)}`",
        f"- uncertain positives: `{summary['by_case_type'].get('uncertain_positive', 0)}`",
        f"- uncertain counterfactuals: `{summary['by_case_type'].get('uncertain_counterfactual', 0)}`",
        f"- strict positive candidates: `{cal['strict_positive_candidates']}`",
        f"- strict negative candidates: `{cal['strict_negative_candidates']}`",
        "",
        "## Visual Queue",
        "",
        f"- queue rows: `{summary['queue_rows']}`",
        f"- queue by case type: `{summary['queue_by_case_type']}`",
        f"- queue by label: `{summary['queue_by_label']}`",
        "",
        "## Calibration Guidance",
        "",
    ]
    for item in cal["recommended_before_calibration"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Promotion Decision",
            "",
            "`attachment_deferred` remains blocked for source metrics and main-claim",
            "promotion until visual sanity review, calibration filter freeze, source",
            "metrics, controls, bootstrap CI, and audit are complete. Main AAAI claim",
            "promotion still requires explicit final user confirmation.",
            "",
            "## Next Gate",
            "",
            f"`{manifest['next_gate']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    gt_policy_dir = args.gt_policy_dir if args.gt_policy_dir.is_absolute() else repo_root / args.gt_policy_dir
    out = args.out if args.out.is_absolute() else repo_root / args.out

    manifest_path = gt_policy_dir / "manifest.json"
    eval_path = gt_policy_dir / "gt_eval_rows.jsonl"
    evidence_path = gt_policy_dir / "gt_evidence_rows.jsonl"
    for path in [manifest_path, eval_path, evidence_path]:
        if not path.exists():
            raise FileNotFoundError(f"missing G4 input artifact: {path}")

    gt_manifest = read_json(manifest_path)
    if gt_manifest.get("status") != "attachment_deferred_gt_policy_smoke_ready_no_source_metrics":
        raise ValueError(f"unexpected_gt_policy_status:{gt_manifest.get('status')}")

    evidence_by_row_id = {row["row_id"]: row for row in iter_jsonl(evidence_path)}
    eval_rows = list(iter_jsonl(eval_path))
    cases = [
        build_case(row, evidence_by_row_id.get(row["decision"]["row_id"]), index=index, repo_root=repo_root)
        for index, row in enumerate(eval_rows, start=1)
    ]
    review_cases = [
        case
        for case in cases
        if case["case_type"]
        in {
            "false_satisfaction_counterfactual",
            "false_violation_positive",
            "uncertain_positive",
            "uncertain_counterfactual",
        }
    ]
    queue = select_visual_queue(cases, args.target_queue_size)
    summary = summarize_cases(cases, queue)
    calibration_filter_rows = [
        {
            "schema_version": "h001_attachment_deferred_calibration_filter_v1",
            "case_id": case["case_id"],
            "row_id": case["row_id"],
            "seed_id": case["seed_id"],
            "predicate_label": case["predicate_label"],
            "subtype_hint": case["subtype_hint"],
            "strategy": case["strategy"],
            "target_geom_valid": case["target_geom_valid"],
            "verification_status": case["verification_status"],
            "calibration_disposition": case["calibration_disposition"],
            "likely_issue": case["likely_issue"],
        }
        for case in cases
    ]

    created_at = utc_now()
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "created_at": created_at,
        "claim_boundary": {
            "current_main_claim_unchanged": True,
            "artifact_type": "error_visual_sanity_planning",
            "visual_labels_completed": False,
            "calibration_fitted": False,
            "source_predictions_scored": False,
            "source_metrics_computed": False,
            "requires_user_confirmation_before_main_claim_promotion": True,
        },
        "inputs": {
            "gt_policy_manifest": relpath(repo_root, manifest_path),
            "gt_eval_rows": relpath(repo_root, eval_path),
            "gt_evidence_rows": relpath(repo_root, evidence_path),
        },
        "outputs": {
            "manifest": "manifest.json",
            "summary": "summary.json",
            "review_cases": "review_cases.jsonl",
            "visual_queue": "visual_queue.jsonl",
            "calibration_filter": "calibration_filter.jsonl",
            "guide": "guide.md",
            "commands": "commands.md",
            "report": "report.md",
        },
        "counts": {
            "eval_rows": len(eval_rows),
            "evidence_rows": len(evidence_by_row_id),
            "review_case_rows": len(review_cases),
            "visual_queue_rows": len(queue),
        },
        "blockers": [
            "visual_queue_not_labeled",
            "calibration_filter_not_frozen_from_review",
            "calibrator_not_fit",
            "source_metrics_not_run",
            "controls_not_run",
            "bootstrap_ci_not_run",
            "main_AAAI_claim_requires_user_confirmation_before_attachment_promotion",
        ],
        "next_gate": "G4c_attachment_visual_review_or_calibration_filter_freeze",
    }

    ensure_dir(out)
    write_json(out / "manifest.json", manifest)
    write_json(out / "summary.json", summary)
    write_jsonl(out / "review_cases.jsonl", review_cases)
    write_jsonl(out / "visual_queue.jsonl", queue)
    write_jsonl(out / "calibration_filter.jsonl", calibration_filter_rows)
    write_text(out / "guide.md", guide_md())
    write_text(out / "commands.md", commands_md())
    write_text(out / "report.md", report_md(manifest, summary))
    print(
        json.dumps(
            {
                "status": STATUS,
                "out": relpath(repo_root, out),
                "review_cases": len(review_cases),
                "visual_queue": len(queue),
                "false_satisfaction": summary["by_case_type"].get("false_satisfaction_counterfactual", 0),
                "false_violation": summary["by_case_type"].get("false_violation_positive", 0),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
