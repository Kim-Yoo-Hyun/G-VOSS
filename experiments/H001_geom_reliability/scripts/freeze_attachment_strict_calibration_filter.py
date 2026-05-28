#!/usr/bin/env python3
"""Freeze the attachment-deferred strict-only calibration filter.

This G4c step turns the G4b calibration-filter disposition into a deterministic
strict-only calibration subset. It keeps only GT-positive rows that the policy
strictly satisfies and counterfactual rows that the policy strictly violates.
It does not fit calibration, score source predictions, compute source metrics,
or change the main AAAI claim.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h001_attachment_deferred_strict_filter_freeze_v1"
STATUS = "attachment_deferred_strict_filter_frozen_no_fit_no_source_metrics"
DEFAULT_ATTACHMENT_ROOT = Path("experiments/H001_geom_reliability/sources/attachment_deferred")
DEFAULT_GT_POLICY_DIR = DEFAULT_ATTACHMENT_ROOT / "gt_policy_smoke"
DEFAULT_ERROR_VISUAL_DIR = DEFAULT_ATTACHMENT_ROOT / "error_visual_sanity"
DEFAULT_OUT = DEFAULT_ATTACHMENT_ROOT / "strict_filter_freeze"

STRICT_POSITIVE = "use_as_strict_positive"
STRICT_NEGATIVE = "use_as_strict_negative"
STRICT_DISPOSITIONS = {STRICT_POSITIVE, STRICT_NEGATIVE}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--gt-policy-dir", type=Path, default=DEFAULT_GT_POLICY_DIR)
    parser.add_argument("--error-visual-dir", type=Path, default=DEFAULT_ERROR_VISUAL_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
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


def expected_disposition(eval_row: dict[str, Any]) -> str:
    status = eval_row["decision"]["verification_status"]
    target = int(eval_row["target_geom_valid"])
    if target == 1 and status == "satisfied":
        return STRICT_POSITIVE
    if target == 1 and status == "uncertain":
        return "soft_positive_or_review_before_calibration"
    if target == 1 and status == "violated":
        return "review_false_violation_before_any_positive_calibration_use"
    if target == 0 and status == "violated":
        return STRICT_NEGATIVE
    if target == 0 and status == "uncertain":
        return "skip_or_review_uncertain_negative"
    if target == 0 and status == "satisfied":
        return "exclude_or_review_counterfactual_seed_false_satisfaction"
    return "skip_unknown"


def count_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: value for key, value in sorted(counter.items())}


def nested_count_dict(counter: dict[str, Counter[str]]) -> dict[str, dict[str, int]]:
    return {key: count_dict(value) for key, value in sorted(counter.items())}


def strict_row(
    filter_row: dict[str, Any],
    eval_row: dict[str, Any],
    *,
    index: int,
) -> dict[str, Any]:
    decision = eval_row["decision"]
    target = int(eval_row["target_geom_valid"])
    calibration_label = 1 if target == 1 else 0
    return {
        "schema_version": "h001_attachment_deferred_strict_calibration_row_v1",
        "strict_index": index,
        "row_id": filter_row["row_id"],
        "seed_id": filter_row["seed_id"],
        "case_id": filter_row["case_id"],
        "split_role": eval_row["split_role"],
        "record_type": eval_row["record_type"],
        "scan_id": decision["scan_id"],
        "subgraph_id": decision["subgraph_id"],
        "subject_id": decision["subject_id"],
        "object_id": decision["object_id"],
        "predicate_family": decision["predicate_family"],
        "predicate_label": filter_row["predicate_label"],
        "subtype_hint": filter_row["subtype_hint"],
        "strategy": filter_row["strategy"],
        "target_geom_valid": target,
        "calibration_label": calibration_label,
        "verification_status": filter_row["verification_status"],
        "calibration_disposition": filter_row["calibration_disposition"],
        "reason_codes": decision.get("reason_codes", []),
        "evidence_requirements_met": decision.get("evidence_requirements_met", []),
        "freeze_decision": "include_strict_only",
        "freeze_reason": (
            "strict_policy_satisfied_gt_positive"
            if calibration_label == 1
            else "strict_policy_violated_counterfactual_negative"
        ),
    }


def excluded_row(
    filter_row: dict[str, Any],
    eval_row: dict[str, Any],
    *,
    index: int,
) -> dict[str, Any]:
    decision = eval_row["decision"]
    disposition = filter_row["calibration_disposition"]
    if disposition == "exclude_or_review_counterfactual_seed_false_satisfaction":
        reason = "counterfactual_seed_false_satisfied_by_policy"
    elif disposition == "review_false_violation_before_any_positive_calibration_use":
        reason = "gt_positive_false_violated_requires_visual_review"
    elif disposition in {
        "soft_positive_or_review_before_calibration",
        "skip_or_review_uncertain_negative",
    }:
        reason = "uncertain_policy_decision_excluded_from_strict_filter"
    else:
        reason = "non_strict_or_unknown_disposition"
    return {
        "schema_version": "h001_attachment_deferred_strict_filter_exclusion_v1",
        "excluded_index": index,
        "row_id": filter_row["row_id"],
        "seed_id": filter_row["seed_id"],
        "case_id": filter_row["case_id"],
        "split_role": eval_row["split_role"],
        "record_type": eval_row["record_type"],
        "scan_id": decision["scan_id"],
        "subgraph_id": decision["subgraph_id"],
        "subject_id": decision["subject_id"],
        "object_id": decision["object_id"],
        "predicate_family": decision["predicate_family"],
        "predicate_label": filter_row["predicate_label"],
        "subtype_hint": filter_row["subtype_hint"],
        "strategy": filter_row["strategy"],
        "target_geom_valid": int(eval_row["target_geom_valid"]),
        "verification_status": filter_row["verification_status"],
        "calibration_disposition": disposition,
        "likely_issue": filter_row["likely_issue"],
        "freeze_decision": "exclude_from_strict_filter",
        "freeze_reason": reason,
    }


def summarize(strict_rows: list[dict[str, Any]], excluded_rows: list[dict[str, Any]]) -> dict[str, Any]:
    strict_by_label = Counter(row["predicate_label"] for row in strict_rows)
    strict_by_split = Counter(row["split_role"] for row in strict_rows)
    strict_by_label_split: dict[str, Counter[str]] = defaultdict(Counter)
    strict_by_split_label: dict[str, Counter[str]] = defaultdict(Counter)
    strict_by_target = Counter(str(row["calibration_label"]) for row in strict_rows)
    strict_by_label_target: dict[str, Counter[str]] = defaultdict(Counter)
    strict_by_subtype = Counter(row["subtype_hint"] for row in strict_rows)
    excluded_by_disposition = Counter(row["calibration_disposition"] for row in excluded_rows)
    excluded_by_label = Counter(row["predicate_label"] for row in excluded_rows)
    warnings: list[str] = []

    for row in strict_rows:
        label = row["predicate_label"]
        split = row["split_role"]
        target = str(row["calibration_label"])
        strict_by_label_split[label][split] += 1
        strict_by_split_label[split][label] += 1
        strict_by_label_target[label][target] += 1

    for label in ["attached to", "hanging on", "connected to"]:
        label_targets = strict_by_label_target.get(label, Counter())
        if label_targets.get("1", 0) == 0 or label_targets.get("0", 0) == 0:
            warnings.append(f"{label}:missing_strict_positive_or_negative")
        for split in ["train", "dev"]:
            rows = [
                row
                for row in strict_rows
                if row["predicate_label"] == label and row["split_role"] == split
            ]
            if not rows:
                warnings.append(f"{label}:{split}:no_strict_rows")
    connected_dev = [
        row
        for row in strict_rows
        if row["predicate_label"] == "connected to" and row["split_role"] == "dev"
    ]
    if not connected_dev:
        warnings.append("connected_to_dev_absent_use_pooled_or_train_only_caveat")

    strict_positive = strict_by_target.get("1", 0)
    strict_negative = strict_by_target.get("0", 0)
    return {
        "strict_rows": len(strict_rows),
        "excluded_rows": len(excluded_rows),
        "strict_positive_rows": strict_positive,
        "strict_negative_rows": strict_negative,
        "strict_by_label": count_dict(strict_by_label),
        "strict_by_split": count_dict(strict_by_split),
        "strict_by_label_split": nested_count_dict(strict_by_label_split),
        "strict_by_split_label": nested_count_dict(strict_by_split_label),
        "strict_by_label_target": nested_count_dict(strict_by_label_target),
        "strict_by_subtype": count_dict(strict_by_subtype),
        "excluded_by_disposition": count_dict(excluded_by_disposition),
        "excluded_by_label": count_dict(excluded_by_label),
        "calibration_readiness": {
            "strict_filter_frozen": True,
            "ready_for_pooled_attachment_calibration_fit": strict_positive > 0 and strict_negative > 0,
            "ready_for_family_specific_connected_to_dev_calibration": bool(connected_dev),
            "warnings": warnings,
            "recommended_next": [
                "fit pooled or family-aware attachment calibrator from strict_calibration_rows.jsonl",
                "keep excluded rows out of strict calibration unless visual labels define a soft-label protocol",
                "record connected-to dev absence as a caveat if family-specific calibration is attempted",
            ],
        },
        "promotion_readiness": {
            "ready_for_source_metrics": False,
            "reason": "G4c freezes strict calibration rows only; fitted calibration, source metrics, controls, bootstrap CI, and audit remain missing.",
            "main_AAAI_claim_unchanged": True,
            "requires_final_user_confirmation_before_claim_promotion": True,
        },
    }


def freeze_policy() -> dict[str, Any]:
    return {
        "schema_version": "h001_attachment_deferred_strict_filter_policy_v1",
        "policy_name": "attachment_deferred_strict_only_calibration_filter",
        "include": {
            STRICT_POSITIVE: {
                "target_geom_valid": 1,
                "verification_status": "satisfied",
                "calibration_label": 1,
            },
            STRICT_NEGATIVE: {
                "target_geom_valid": 0,
                "verification_status": "violated",
                "calibration_label": 0,
            },
        },
        "exclude": {
            "exclude_or_review_counterfactual_seed_false_satisfaction": "counterfactual seed is not reliable as a negative without visual review",
            "review_false_violation_before_any_positive_calibration_use": "positive GT row needs visual review before use or threshold relaxation",
            "soft_positive_or_review_before_calibration": "uncertain positive is not strict positive calibration evidence",
            "skip_or_review_uncertain_negative": "uncertain counterfactual is not strict negative calibration evidence",
            "skip_unknown": "unknown disposition is never used in strict calibration",
        },
        "claim_boundary": {
            "visual_labels_required_for_soft_protocol": True,
            "calibration_fitted": False,
            "source_metrics_computed": False,
            "main_AAAI_claim_unchanged": True,
            "requires_user_confirmation_before_main_claim_promotion": True,
        },
    }


def commands_md() -> str:
    return """# Attachment Deferred G4c Strict Filter Freeze Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm \\
  attachment_deferred_strict_filter_freeze
```

Validation:

```bash
python -m py_compile experiments/H001_geom_reliability/scripts/freeze_attachment_strict_calibration_filter.py
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/strict_filter_freeze/manifest.json >/dev/null
python -m json.tool experiments/H001_geom_reliability/sources/attachment_deferred/strict_filter_freeze/summary.json >/dev/null
```

This command freezes strict calibration rows only. It does not fit calibration,
score source predictions, compute source metrics, run controls/bootstrap, or
update the main AAAI claim.
"""


def report_md(manifest: dict[str, Any], summary: dict[str, Any]) -> str:
    lines = [
        "# Attachment Deferred G4c Strict Filter Freeze",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Claim Boundary",
        "",
        "This artifact freezes a strict-only calibration subset. It does not fit",
        "calibration, score VL-SAT/Open3DSG predictions, compute source metrics,",
        "run controls/bootstrap, or change the current AAAI main claim.",
        "",
        "## Frozen Rows",
        "",
        f"- strict rows: `{summary['strict_rows']}`",
        f"- strict positives: `{summary['strict_positive_rows']}`",
        f"- strict negatives: `{summary['strict_negative_rows']}`",
        f"- excluded rows: `{summary['excluded_rows']}`",
        f"- strict by label: `{summary['strict_by_label']}`",
        f"- strict by split: `{summary['strict_by_split']}`",
        "",
        "## Exclusions",
        "",
        f"- excluded by disposition: `{summary['excluded_by_disposition']}`",
        f"- excluded by label: `{summary['excluded_by_label']}`",
        "",
        "## Warnings",
        "",
    ]
    warnings = summary["calibration_readiness"]["warnings"]
    if warnings:
        lines.extend(f"- `{warning}`" for warning in warnings)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Next Gate",
            "",
            "Fit attachment train-dev calibration from `strict_calibration_rows.jsonl`,",
            "then run VL-SAT/Open3DSG source metrics and controls. Do not promote",
            "`attachment_deferred` into the main AAAI claim without explicit final",
            "user confirmation.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    gt_policy_dir = args.gt_policy_dir if args.gt_policy_dir.is_absolute() else repo_root / args.gt_policy_dir
    error_visual_dir = (
        args.error_visual_dir if args.error_visual_dir.is_absolute() else repo_root / args.error_visual_dir
    )
    out = args.out if args.out.is_absolute() else repo_root / args.out

    gt_manifest_path = gt_policy_dir / "manifest.json"
    gt_eval_path = gt_policy_dir / "gt_eval_rows.jsonl"
    g4b_manifest_path = error_visual_dir / "manifest.json"
    calibration_filter_path = error_visual_dir / "calibration_filter.jsonl"
    for path in [gt_manifest_path, gt_eval_path, g4b_manifest_path, calibration_filter_path]:
        if not path.exists():
            raise FileNotFoundError(f"missing G4c input artifact: {path}")

    gt_manifest = read_json(gt_manifest_path)
    if gt_manifest.get("status") != "attachment_deferred_gt_policy_smoke_ready_no_source_metrics":
        raise ValueError(f"unexpected_gt_policy_status:{gt_manifest.get('status')}")
    g4b_manifest = read_json(g4b_manifest_path)
    if g4b_manifest.get("status") != "attachment_deferred_error_visual_sanity_plan_ready_no_source_metrics":
        raise ValueError(f"unexpected_g4b_status:{g4b_manifest.get('status')}")

    eval_rows = list(iter_jsonl(gt_eval_path))
    filter_rows = list(iter_jsonl(calibration_filter_path))
    eval_by_seed_id = {row["seed_id"]: row for row in eval_rows}
    if len(eval_by_seed_id) != len(eval_rows):
        raise ValueError("duplicate seed_id in gt_eval_rows")
    if len(filter_rows) != len(eval_rows):
        raise ValueError(f"filter/eval row-count mismatch: {len(filter_rows)} vs {len(eval_rows)}")

    strict_rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []
    validation_errors: list[str] = []
    strict_index = 0
    excluded_index = 0

    for filter_row in filter_rows:
        seed_id = filter_row["seed_id"]
        row_id = filter_row["row_id"]
        eval_row = eval_by_seed_id.get(seed_id)
        if eval_row is None:
            validation_errors.append(f"missing_eval_row:{seed_id}")
            continue
        if eval_row["decision"]["row_id"] != row_id:
            validation_errors.append(f"row_id_mismatch:{seed_id}:{row_id}:{eval_row['decision']['row_id']}")
        expected = expected_disposition(eval_row)
        if filter_row["calibration_disposition"] != expected:
            validation_errors.append(
                f"disposition_mismatch:{row_id}:{filter_row['calibration_disposition']}:{expected}"
            )
        if filter_row["predicate_label"] != eval_row["decision"]["predicate_label"]:
            validation_errors.append(f"predicate_mismatch:{row_id}")
        if int(filter_row["target_geom_valid"]) != int(eval_row["target_geom_valid"]):
            validation_errors.append(f"target_mismatch:{row_id}")

        if filter_row["calibration_disposition"] in STRICT_DISPOSITIONS:
            strict_index += 1
            strict_rows.append(strict_row(filter_row, eval_row, index=strict_index))
        else:
            excluded_index += 1
            excluded_rows.append(excluded_row(filter_row, eval_row, index=excluded_index))

    if validation_errors:
        raise ValueError(f"validation_errors:{validation_errors[:10]}")

    summary = summarize(strict_rows, excluded_rows)
    created_at = utc_now()
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "created_at": created_at,
        "claim_boundary": {
            "artifact_type": "strict_calibration_filter_freeze",
            "visual_labels_completed": False,
            "strict_filter_frozen": True,
            "calibration_fitted": False,
            "source_predictions_scored": False,
            "source_metrics_computed": False,
            "current_main_claim_unchanged": True,
            "requires_user_confirmation_before_main_claim_promotion": True,
        },
        "inputs": {
            "gt_policy_manifest": relpath(repo_root, gt_manifest_path),
            "gt_eval_rows": relpath(repo_root, gt_eval_path),
            "g4b_manifest": relpath(repo_root, g4b_manifest_path),
            "g4b_calibration_filter": relpath(repo_root, calibration_filter_path),
        },
        "outputs": {
            "manifest": "manifest.json",
            "summary": "summary.json",
            "freeze_policy": "freeze_policy.json",
            "strict_calibration_rows": "strict_calibration_rows.jsonl",
            "excluded_rows": "excluded_rows.jsonl",
            "commands": "commands.md",
            "report": "report.md",
        },
        "counts": {
            "input_eval_rows": len(eval_rows),
            "input_filter_rows": len(filter_rows),
            "strict_rows": len(strict_rows),
            "excluded_rows": len(excluded_rows),
            "validation_errors": 0,
        },
        "blockers": [
            "calibrator_not_fit",
            "source_metrics_not_run",
            "controls_not_run",
            "bootstrap_ci_not_run",
            "completed_visual_audit_optional_if_strict_filter_used_but_required_for_soft_protocol",
            "main_AAAI_claim_requires_user_confirmation_before_attachment_promotion",
        ],
        "next_gate": "G5_attachment_calibration_fit_then_source_metrics",
    }

    ensure_dir(out)
    write_json(out / "manifest.json", manifest)
    write_json(out / "summary.json", summary)
    write_json(out / "freeze_policy.json", freeze_policy())
    write_jsonl(out / "strict_calibration_rows.jsonl", strict_rows)
    write_jsonl(out / "excluded_rows.jsonl", excluded_rows)
    write_text(out / "commands.md", commands_md())
    write_text(out / "report.md", report_md(manifest, summary))
    print(
        json.dumps(
            {
                "status": STATUS,
                "out": relpath(repo_root, out),
                "strict_rows": len(strict_rows),
                "strict_positive": summary["strict_positive_rows"],
                "strict_negative": summary["strict_negative_rows"],
                "excluded_rows": len(excluded_rows),
                "warnings": summary["calibration_readiness"]["warnings"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
