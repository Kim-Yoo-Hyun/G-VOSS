#!/usr/bin/env python3
"""Summarize the independent H001 visual spot-check labels.

The script validates reviewer-filled labels and joins them with the private
reference file only after review. It does not infer missing labels.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
H001_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[4]
DEFAULT_SPOTCHECK_DIR = (
    H001_ROOT
    / "artifacts"
    / "evaluation"
    / "vlsat_closed_set"
    / "hardened"
    / "human_audit"
    / "visual_spotcheck"
)
DEFAULT_QUEUE = DEFAULT_SPOTCHECK_DIR / "queue.jsonl"
DEFAULT_LABELS = DEFAULT_SPOTCHECK_DIR / "labels.jsonl"
DEFAULT_REFERENCE = DEFAULT_SPOTCHECK_DIR / "reference.jsonl"
DEFAULT_OUTPUT_DIR = DEFAULT_SPOTCHECK_DIR

VALID_VISUAL_LABELS = {
    "valid_relation",
    "invalid_relation",
    "ambiguous",
    "annotation_noise",
    "scan_geometry_missing",
    "verifier_error",
    "semantic_label_too_coarse",
}
QUALITY_ISSUE_LABELS = {
    "invalid_relation",
    "semantic_label_too_coarse",
    "annotation_noise",
    "scan_geometry_missing",
}
TARGET_BUCKETS = {
    "semantic_topk_violated",
    "probabilistic_reranked_away",
    "rule_verified_removed",
}
SUSPICIOUS_REVIEWER_TOKENS = ("codex", "openai", "assistant", "gpt", "model")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue-jsonl", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--labels-jsonl", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--reference-jsonl", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--min-labeled", type=int, default=50)
    parser.add_argument("--min-target-quality-issue-rate", type=float, default=0.5)
    parser.add_argument("--max-target-contradiction-rate", type=float, default=0.35)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}") from exc
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def index_rows(rows: list[dict[str, Any]], key: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    indexed: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    for row in rows:
        row_id = str(row.get(key, ""))
        if not row_id:
            duplicates.append("<missing>")
            continue
        if row_id in indexed:
            duplicates.append(row_id)
        indexed[row_id] = row
    return indexed, duplicates


def visual_label(row: dict[str, Any] | None) -> str:
    if row is None:
        return "missing_label_row"
    label = row.get("visual_label")
    if label in VALID_VISUAL_LABELS:
        return str(label)
    if label is None:
        return "unlabeled"
    return f"invalid_label:{label}"


def is_labeled(row: dict[str, Any] | None) -> bool:
    return row is not None and row.get("visual_label") in VALID_VISUAL_LABELS


def issue_category(label: str) -> str:
    if label in QUALITY_ISSUE_LABELS:
        return "quality_issue"
    if label == "valid_relation":
        return "valid"
    if label == "ambiguous":
        return "ambiguous"
    if label == "verifier_error":
        return "verifier_error"
    return "unlabeled_or_invalid"


def grouped_label_counts(
    spotcheck_ids: list[str],
    labels_by_id: dict[str, dict[str, Any]],
    reference_by_id: dict[str, dict[str, Any]],
    queue_by_id: dict[str, dict[str, Any]],
    field: str,
) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for spotcheck_id in spotcheck_ids:
        label = labels_by_id.get(spotcheck_id)
        reference = reference_by_id.get(spotcheck_id, {})
        queue = queue_by_id.get(spotcheck_id, {})
        if field == "bucket":
            key = str(reference.get("bucket", "missing"))
        elif field == "family":
            key = str(reference.get("predicate_family") or (queue.get("relation") or {}).get("predicate_family") or "missing")
        elif field == "verification_status":
            key = str(reference.get("verification_status", "missing"))
        elif field == "reviewer_id":
            key = str((label or {}).get("reviewer_id") or "missing")
        else:
            raise ValueError(field)
        grouped[key][visual_label(label)] += 1
    return {key: dict(sorted(counter.items())) for key, counter in sorted(grouped.items())}


def summarize_target_alignment(
    spotcheck_ids: list[str],
    labels_by_id: dict[str, dict[str, Any]],
    reference_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    target_ids = [
        spotcheck_id
        for spotcheck_id in spotcheck_ids
        if reference_by_id.get(spotcheck_id, {}).get("bucket") in TARGET_BUCKETS
    ]
    labeled_target_ids = [spotcheck_id for spotcheck_id in target_ids if is_labeled(labels_by_id.get(spotcheck_id))]
    support = 0
    contradiction = 0
    ambiguous = 0
    verifier_error = 0
    by_bucket: dict[str, Counter[str]] = defaultdict(Counter)
    for spotcheck_id in labeled_target_ids:
        label = str(labels_by_id[spotcheck_id]["visual_label"])
        bucket = str(reference_by_id.get(spotcheck_id, {}).get("bucket", "missing"))
        category = issue_category(label)
        by_bucket[bucket][category] += 1
        if label in QUALITY_ISSUE_LABELS:
            support += 1
        elif label == "valid_relation":
            contradiction += 1
        elif label == "verifier_error":
            contradiction += 1
            verifier_error += 1
        elif label == "ambiguous":
            ambiguous += 1

    denominator = len(labeled_target_ids)
    return {
        "target_buckets": sorted(TARGET_BUCKETS),
        "target_rows": len(target_ids),
        "labeled_target_rows": denominator,
        "quality_issue_support": support,
        "valid_or_verifier_error_contradiction": contradiction,
        "ambiguous": ambiguous,
        "verifier_error": verifier_error,
        "quality_issue_rate": ratio(support, denominator),
        "contradiction_rate": ratio(contradiction, denominator),
        "by_bucket_category": {key: dict(sorted(value.items())) for key, value in sorted(by_bucket.items())},
    }


def summarize_codex_agreement(
    spotcheck_ids: list[str],
    labels_by_id: dict[str, dict[str, Any]],
    reference_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    comparable = []
    exact = 0
    category_match = 0
    for spotcheck_id in spotcheck_ids:
        label_row = labels_by_id.get(spotcheck_id)
        reference = reference_by_id.get(spotcheck_id, {})
        if not is_labeled(label_row):
            continue
        codex_label = reference.get("codex_structured_label")
        if codex_label not in VALID_VISUAL_LABELS:
            continue
        human_label = str(label_row["visual_label"])
        comparable.append(spotcheck_id)
        if human_label == codex_label:
            exact += 1
        if issue_category(human_label) == issue_category(str(codex_label)):
            category_match += 1
    denominator = len(comparable)
    return {
        "comparable_rows": denominator,
        "exact_match": exact,
        "category_match": category_match,
        "exact_match_rate": ratio(exact, denominator),
        "category_match_rate": ratio(category_match, denominator),
    }


def collect_figure_candidates(
    spotcheck_ids: list[str],
    labels_by_id: dict[str, dict[str, Any]],
    queue_by_id: dict[str, dict[str, Any]],
    reference_by_id: dict[str, dict[str, Any]],
    limit: int = 20,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for spotcheck_id in spotcheck_ids:
        label = labels_by_id.get(spotcheck_id)
        if not label or label.get("figure_candidate") is not True:
            continue
        queue = queue_by_id.get(spotcheck_id, {})
        relation = queue.get("relation") or {}
        reference = reference_by_id.get(spotcheck_id, {})
        candidates.append(
            {
                "spotcheck_id": spotcheck_id,
                "source_sample_id": queue.get("source_sample_id"),
                "scan_id": queue.get("scan_id"),
                "bucket": reference.get("bucket"),
                "predicate_family": relation.get("predicate_family"),
                "predicate_label": relation.get("predicate_label"),
                "subject_label": relation.get("subject_label"),
                "object_label": relation.get("object_label"),
                "visual_label": label.get("visual_label"),
                "notes": label.get("notes", ""),
            }
        )
    return candidates[:limit]


def build_summary(args: argparse.Namespace) -> dict[str, Any]:
    queue_rows = read_jsonl(args.queue_jsonl)
    label_rows = read_jsonl(args.labels_jsonl)
    reference_rows = read_jsonl(args.reference_jsonl)

    queue_by_id, duplicate_queue_ids = index_rows(queue_rows, "spotcheck_id")
    labels_by_id, duplicate_label_ids = index_rows(label_rows, "spotcheck_id")
    reference_by_id, duplicate_reference_ids = index_rows(reference_rows, "spotcheck_id")
    spotcheck_ids = [str(row.get("spotcheck_id")) for row in queue_rows]

    queue_id_set = set(spotcheck_ids)
    label_id_set = set(labels_by_id)
    reference_id_set = set(reference_by_id)
    missing_label_ids = sorted(queue_id_set - label_id_set)
    extra_label_ids = sorted(label_id_set - queue_id_set)
    missing_reference_ids = sorted(queue_id_set - reference_id_set)
    extra_reference_ids = sorted(reference_id_set - queue_id_set)

    invalid_label_ids = [
        spotcheck_id
        for spotcheck_id in spotcheck_ids
        if labels_by_id.get(spotcheck_id, {}).get("visual_label") is not None
        and labels_by_id.get(spotcheck_id, {}).get("visual_label") not in VALID_VISUAL_LABELS
    ]
    labeled_ids = [spotcheck_id for spotcheck_id in spotcheck_ids if is_labeled(labels_by_id.get(spotcheck_id))]
    unlabeled_ids = [spotcheck_id for spotcheck_id in spotcheck_ids if not is_labeled(labels_by_id.get(spotcheck_id))]
    labeled_rows = [labels_by_id[spotcheck_id] for spotcheck_id in labeled_ids]

    missing_reviewer_ids = [
        row["spotcheck_id"] for row in labeled_rows if not str(row.get("reviewer_id", "")).strip()
    ]
    missing_reviewed_at = [
        row["spotcheck_id"] for row in labeled_rows if not str(row.get("reviewed_at", "")).strip()
    ]
    labeled_but_status_unlabeled = [
        row["spotcheck_id"] for row in labeled_rows if row.get("audit_status") == "unlabeled"
    ]
    bad_audit_source = [
        row["spotcheck_id"]
        for row in labeled_rows
        if row.get("audit_source") != "independent_human_visual_review"
    ]
    suspicious_reviewer_ids = [
        row["spotcheck_id"]
        for row in labeled_rows
        if any(token in str(row.get("reviewer_id", "")).lower() for token in SUSPICIOUS_REVIEWER_TOKENS)
    ]

    by_label = Counter(visual_label(labels_by_id.get(spotcheck_id)) for spotcheck_id in spotcheck_ids)
    by_category = Counter(issue_category(visual_label(labels_by_id.get(spotcheck_id))) for spotcheck_id in spotcheck_ids)
    target_alignment = summarize_target_alignment(spotcheck_ids, labels_by_id, reference_by_id)
    codex_agreement = summarize_codex_agreement(spotcheck_ids, labels_by_id, reference_by_id)

    blockers: list[str] = []
    warnings: list[str] = []
    if len(labeled_ids) < args.min_labeled:
        blockers.append(f"insufficient_labeled_rows:{len(labeled_ids)}/{args.min_labeled}")
    if missing_label_ids:
        blockers.append(f"missing_label_rows:{len(missing_label_ids)}")
    if extra_label_ids:
        blockers.append(f"extra_label_rows:{len(extra_label_ids)}")
    if missing_reference_ids:
        blockers.append(f"missing_reference_rows:{len(missing_reference_ids)}")
    if extra_reference_ids:
        blockers.append(f"extra_reference_rows:{len(extra_reference_ids)}")
    if duplicate_queue_ids:
        blockers.append(f"duplicate_queue_ids:{len(duplicate_queue_ids)}")
    if duplicate_label_ids:
        blockers.append(f"duplicate_label_ids:{len(duplicate_label_ids)}")
    if duplicate_reference_ids:
        blockers.append(f"duplicate_reference_ids:{len(duplicate_reference_ids)}")
    if invalid_label_ids:
        blockers.append(f"invalid_visual_labels:{len(invalid_label_ids)}")
    if missing_reviewer_ids:
        blockers.append(f"missing_reviewer_id:{len(missing_reviewer_ids)}")
    if missing_reviewed_at:
        blockers.append(f"missing_reviewed_at:{len(missing_reviewed_at)}")
    if labeled_but_status_unlabeled:
        blockers.append(f"audit_status_still_unlabeled:{len(labeled_but_status_unlabeled)}")
    if bad_audit_source:
        blockers.append(f"bad_audit_source:{len(bad_audit_source)}")
    if suspicious_reviewer_ids:
        blockers.append(f"suspicious_reviewer_id_not_independent:{len(suspicious_reviewer_ids)}")

    target_quality_rate = target_alignment["quality_issue_rate"]
    target_contradiction_rate = target_alignment["contradiction_rate"]
    if target_quality_rate is not None and target_quality_rate < args.min_target_quality_issue_rate:
        warnings.append(
            f"target_quality_issue_rate_below_threshold:{target_quality_rate:.4f}<"
            f"{args.min_target_quality_issue_rate:.4f}"
        )
    if target_contradiction_rate is not None and target_contradiction_rate > args.max_target_contradiction_rate:
        warnings.append(
            f"target_contradiction_rate_above_threshold:{target_contradiction_rate:.4f}>"
            f"{args.max_target_contradiction_rate:.4f}"
        )

    if blockers:
        status = "blocked_unlabeled" if len(labeled_ids) == 0 else "blocked_invalid_or_incomplete"
    elif warnings:
        status = "ready_mixed"
    else:
        status = "ready_sanity_pass"

    return {
        "schema_version": "h001_visual_spotcheck_summary_v1",
        "created_at": date.today().isoformat(),
        "status": status,
        "inputs": {
            "queue_jsonl": relpath(args.queue_jsonl),
            "labels_jsonl": relpath(args.labels_jsonl),
            "reference_jsonl": relpath(args.reference_jsonl),
        },
        "outputs": {
            "summary_json": relpath(args.output_dir / "summary.json"),
            "summary_md": relpath(args.output_dir / "summary.md"),
        },
        "parameters": {
            "min_labeled": args.min_labeled,
            "min_target_quality_issue_rate": args.min_target_quality_issue_rate,
            "max_target_contradiction_rate": args.max_target_contradiction_rate,
            "target_buckets": sorted(TARGET_BUCKETS),
            "quality_issue_labels": sorted(QUALITY_ISSUE_LABELS),
        },
        "counts": {
            "queue_rows": len(queue_rows),
            "label_rows": len(label_rows),
            "reference_rows": len(reference_rows),
            "labeled_rows": len(labeled_ids),
            "unlabeled_rows": len(unlabeled_ids),
            "invalid_label_rows": len(invalid_label_ids),
            "missing_reviewer_id_rows": len(missing_reviewer_ids),
            "missing_reviewed_at_rows": len(missing_reviewed_at),
            "audit_status_still_unlabeled_rows": len(labeled_but_status_unlabeled),
        },
        "label_distribution": dict(sorted(by_label.items())),
        "category_distribution": dict(sorted(by_category.items())),
        "by_bucket": grouped_label_counts(spotcheck_ids, labels_by_id, reference_by_id, queue_by_id, "bucket"),
        "by_family": grouped_label_counts(spotcheck_ids, labels_by_id, reference_by_id, queue_by_id, "family"),
        "by_verification_status": grouped_label_counts(
            spotcheck_ids,
            labels_by_id,
            reference_by_id,
            queue_by_id,
            "verification_status",
        ),
        "by_reviewer_id": grouped_label_counts(
            spotcheck_ids,
            labels_by_id,
            reference_by_id,
            queue_by_id,
            "reviewer_id",
        ),
        "target_alignment": target_alignment,
        "codex_structured_audit_agreement_private": codex_agreement,
        "figure_candidates": collect_figure_candidates(
            spotcheck_ids,
            labels_by_id,
            queue_by_id,
            reference_by_id,
        ),
        "blockers": blockers,
        "warnings": warnings,
        "decision": (
            "Use as independent visual sanity-check evidence only when status is ready_sanity_pass. "
            "If status is ready_mixed, report caveats and do not claim audit pass."
        ),
    }


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def render_report(summary: dict[str, Any]) -> str:
    target = summary["target_alignment"]
    codex = summary["codex_structured_audit_agreement_private"]
    lines = [
        "# Visual Spot-Check Summary",
        "",
        f"Created at: `{summary['created_at']}`",
        f"Status: `{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| queue rows | {summary['counts']['queue_rows']} |",
        f"| label rows | {summary['counts']['label_rows']} |",
        f"| labeled rows | {summary['counts']['labeled_rows']} |",
        f"| unlabeled rows | {summary['counts']['unlabeled_rows']} |",
        f"| invalid label rows | {summary['counts']['invalid_label_rows']} |",
        "",
        "## Gate",
        "",
    ]
    if summary["blockers"]:
        lines.extend(f"- `{item}`" for item in summary["blockers"])
    else:
        lines.append("- no blockers")
    if summary["warnings"]:
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"- `{item}`" for item in summary["warnings"])

    lines.extend(
        [
            "",
            "## Label Distribution",
            "",
            "| Label | Count |",
            "| --- | ---: |",
        ]
    )
    lines.extend(f"| `{key}` | {value} |" for key, value in summary["label_distribution"].items())

    lines.extend(
        [
            "",
            "## Target Buckets",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| target rows | {target['target_rows']} |",
            f"| labeled target rows | {target['labeled_target_rows']} |",
            f"| quality-issue support | {target['quality_issue_support']} |",
            f"| valid/verifier-error contradiction | {target['valid_or_verifier_error_contradiction']} |",
            f"| quality-issue rate | {fmt(target['quality_issue_rate'])} |",
            f"| contradiction rate | {fmt(target['contradiction_rate'])} |",
            "",
            "## Private Agreement Check",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
            f"| comparable rows | {codex['comparable_rows']} |",
            f"| exact match rate | {fmt(codex['exact_match_rate'])} |",
            f"| category match rate | {fmt(codex['category_match_rate'])} |",
            "",
            "## Interpretation",
            "",
            "Fact:",
            "",
            "- The queue is blinded; this summary joins private reference fields only after labels are filled.",
            "- This summary does not infer labels from verifier outputs.",
            "",
            "Inference:",
            "",
        ]
    )
    if summary["status"] == "ready_sanity_pass":
        lines.append("- The independent visual spot-check can be used as a qualitative sanity check for paper-level audit wording.")
    elif summary["status"] == "ready_mixed":
        lines.append("- The independent labels are complete but mixed; keep explicit caveats and avoid claiming audit pass.")
    else:
        lines.append("- Independent visual spot-check remains incomplete or invalid.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    summary = build_summary(args)
    if not args.dry_run:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_json(args.output_dir / "summary.json", summary)
        (args.output_dir / "summary.md").write_text(render_report(summary), encoding="utf-8")
    print(
        "visual_spotcheck_summary "
        f"status={summary['status']} "
        f"labeled={summary['counts']['labeled_rows']}/{summary['parameters']['min_labeled']} "
        f"blockers={len(summary['blockers'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
