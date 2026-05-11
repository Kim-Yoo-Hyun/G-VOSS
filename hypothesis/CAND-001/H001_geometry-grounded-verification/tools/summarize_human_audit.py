#!/usr/bin/env python3
"""Summarize H001 G4 audit labels.

This validates reviewer-filled labels and writes a compact audit summary. It
does not infer labels from verifier outputs; unlabeled rows keep G4 blocked.
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
DEFAULT_AUDIT_DIR = (
    H001_ROOT
    / "artifacts"
    / "evaluation"
    / "vlsat_closed_set"
    / "hardened"
    / "human_audit"
)
DEFAULT_LABELS = DEFAULT_AUDIT_DIR / "labels.jsonl"
DEFAULT_SAMPLES = DEFAULT_AUDIT_DIR / "samples.jsonl"
DEFAULT_OUTPUT_DIR = DEFAULT_AUDIT_DIR
VALID_HUMAN_LABELS = {
    "valid_relation",
    "invalid_relation",
    "ambiguous",
    "annotation_noise",
    "scan_geometry_missing",
    "verifier_error",
    "semantic_label_too_coarse",
}
FAILURE_OR_NOISE_LABELS = {
    "annotation_noise",
    "scan_geometry_missing",
    "verifier_error",
}
QUALITY_ISSUE_LABELS = {
    "invalid_relation",
    "semantic_label_too_coarse",
}
VIOLATION_BUCKETS = {
    "semantic_topk_violated",
    "probabilistic_reranked_away",
    "rule_verified_removed",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize H001 human-audit labels.")
    parser.add_argument("--labels-jsonl", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--samples-jsonl", type=Path, default=DEFAULT_SAMPLES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--min-labeled",
        type=int,
        default=250,
        help="Minimum labeled rows required before status can be ready.",
    )
    parser.add_argument(
        "--min-violated-precision",
        type=float,
        default=0.7,
        help=(
            "Minimum precision for verifier violated decisions, counting "
            "human_label=invalid_relation or semantic_label_too_coarse as a "
            "relation-quality issue."
        ),
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def relpath(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}") from exc
    return rows


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def is_labeled(row: dict[str, Any]) -> bool:
    return row.get("human_label") in VALID_HUMAN_LABELS


def label_value(row: dict[str, Any]) -> str:
    label = row.get("human_label")
    if label in VALID_HUMAN_LABELS:
        return str(label)
    return "unlabeled"


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def sample_index(samples: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in samples:
        result[row["sample_id"]] = row
    return result


def group_counts(
    labels: list[dict[str, Any]],
    samples_by_id: dict[str, dict[str, Any]],
    field: str,
) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for label in labels:
        sample = samples_by_id.get(label["sample_id"], {})
        if field == "bucket":
            key = str(label.get("bucket") or sample.get("bucket") or "missing")
        elif field == "family":
            key = str(
                label.get("predicate_family")
                or (sample.get("predicate") or {}).get("predicate_family")
                or "missing"
            )
        elif field == "predicate":
            key = str(
                label.get("predicate_label")
                or (sample.get("predicate") or {}).get("predicate_label")
                or "missing"
            )
        elif field == "verification_status":
            key = str((sample.get("verification") or {}).get("verification_status") or "missing")
        else:
            raise ValueError(field)
        counts[key][label_value(label)] += 1
    return {key: dict(sorted(counter.items())) for key, counter in sorted(counts.items())}


def bool_counts(labels: list[dict[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in labels:
        value = row.get(field)
        if value is True:
            counter["true"] += 1
        elif value is False:
            counter["false"] += 1
        else:
            counter["missing"] += 1
    return dict(sorted(counter.items()))


def summarize_precision(
    labels: list[dict[str, Any]],
    samples_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    violated_rows = []
    violation_bucket_rows = []
    for label in labels:
        sample = samples_by_id.get(label["sample_id"], {})
        status = (sample.get("verification") or {}).get("verification_status")
        bucket = str(label.get("bucket") or sample.get("bucket") or "")
        if status == "violated" and is_labeled(label):
            violated_rows.append(label)
            if bucket in VIOLATION_BUCKETS:
                violation_bucket_rows.append(label)

    def precision(rows: list[dict[str, Any]]) -> dict[str, Any]:
        denominator = len(rows)
        invalid = sum(1 for row in rows if row.get("human_label") == "invalid_relation")
        semantic_too_coarse = sum(
            1 for row in rows if row.get("human_label") == "semantic_label_too_coarse"
        )
        failure_or_noise = sum(1 for row in rows if row.get("human_label") in FAILURE_OR_NOISE_LABELS)
        valid = sum(1 for row in rows if row.get("human_label") == "valid_relation")
        ambiguous = sum(1 for row in rows if row.get("human_label") == "ambiguous")
        verifier_error = sum(1 for row in rows if row.get("human_label") == "verifier_error")
        quality_issue = invalid + semantic_too_coarse
        return {
            "denominator": denominator,
            "invalid_relation": invalid,
            "semantic_label_too_coarse": semantic_too_coarse,
            "valid_relation": valid,
            "ambiguous": ambiguous,
            "verifier_error": verifier_error,
            "failure_or_noise": failure_or_noise,
            "precision_invalid_only": ratio(invalid, denominator),
            "precision_quality_issue": ratio(quality_issue, denominator),
            "precision_invalid_or_noise": ratio(invalid + failure_or_noise, denominator),
        }

    return {
        "all_labeled_violated_samples": precision(violated_rows),
        "required_violation_buckets": precision(violation_bucket_rows),
    }


def collect_figure_candidates(
    labels: list[dict[str, Any]],
    samples_by_id: dict[str, dict[str, Any]],
    limit: int = 24,
) -> list[dict[str, Any]]:
    candidates = []
    for label in labels:
        if label.get("figure_candidate") is not True:
            continue
        sample = samples_by_id.get(label["sample_id"], {})
        candidates.append(
            {
                "sample_id": label["sample_id"],
                "prediction_id": label["prediction_id"],
                "bucket": label.get("bucket"),
                "human_label": label.get("human_label"),
                "scan_id": label.get("scan_id"),
                "predicate_family": label.get("predicate_family"),
                "predicate_label": label.get("predicate_label"),
                "subject": (sample.get("edge") or {}).get("subject_label"),
                "object": (sample.get("edge") or {}).get("object_label"),
                "notes": label.get("notes"),
            }
        )
    return candidates[:limit]


def make_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Human Audit Label Summary",
        "",
        f"Created at: `{summary['created_at']}`",
        f"Status: `{summary['status']}`",
        f"Labeled rows: `{summary['counts']['labeled_rows']}` / `{summary['counts']['label_rows']}`",
        f"Unlabeled rows: `{summary['counts']['unlabeled_rows']}`",
        "",
        "## Gate",
        "",
    ]
    for item in summary["blocked"]:
        lines.append(f"- Blocked: `{item}`")
    if not summary["blocked"]:
        lines.append("- No blockers recorded.")
    lines.extend(["", "## Human Labels", ""])
    for label, count in summary["label_counts"].items():
        lines.append(f"- `{label}`: `{count}`")
    lines.extend(["", "## Audit Source", ""])
    for source, count in summary["audit_sources"].items():
        lines.append(f"- `{source}`: `{count}`")
    lines.extend(["", "## Violation Precision", ""])
    precision = summary["violation_precision"]["required_violation_buckets"]
    lines.append(
        "- Required violation buckets precision invalid-only: "
        f"`{precision['precision_invalid_only']}` "
        f"({precision['invalid_relation']}/{precision['denominator']})"
    )
    lines.append(
        "- Required violation buckets precision quality-issue: "
        f"`{precision['precision_quality_issue']}` "
        f"(({precision['invalid_relation']} invalid + "
        f"{precision['semantic_label_too_coarse']} semantic-too-coarse)"
        f"/{precision['denominator']})"
    )
    lines.append(
        "- Required violation buckets precision invalid-or-noise: "
        f"`{precision['precision_invalid_or_noise']}`"
    )
    lines.extend(["", "## By Bucket", ""])
    for bucket, counts in summary["by_bucket"].items():
        lines.append(f"- `{bucket}`: `{counts}`")
    lines.extend(["", "## By Family", ""])
    for family, counts in summary["by_family"].items():
        lines.append(f"- `{family}`: `{counts}`")
    lines.extend(["", "## Notes", ""])
    lines.append(
        "This report is a validator/summary artifact. Codex structured audit "
        "labels do not replace independent human visual inspection of the "
        "sample rows."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    for name, path in {
        "labels_jsonl": args.labels_jsonl,
        "samples_jsonl": args.samples_jsonl,
    }.items():
        if not path.exists():
            errors.append(f"missing_input:{name}:{relpath(path)}")
    if errors:
        print(json.dumps({"status": "blocked", "errors": errors}, sort_keys=True))
        return 2

    labels = load_jsonl(args.labels_jsonl)
    samples = load_jsonl(args.samples_jsonl)
    samples_by_id = sample_index(samples)
    sample_ids = set(samples_by_id)
    label_ids = {row.get("sample_id") for row in labels}

    invalid_labels = [
        row["sample_id"]
        for row in labels
        if row.get("human_label") is not None and row.get("human_label") not in VALID_HUMAN_LABELS
    ]
    missing_sample_ids = sorted(str(sample_id) for sample_id in label_ids - sample_ids)
    missing_label_ids = sorted(str(sample_id) for sample_id in sample_ids - label_ids)
    duplicate_label_ids = [
        sample_id
        for sample_id, count in Counter(row.get("sample_id") for row in labels).items()
        if count > 1
    ]

    labeled_rows = sum(1 for row in labels if is_labeled(row))
    unlabeled_rows = len(labels) - labeled_rows
    blocked: list[str] = []
    if errors:
        blocked.extend(errors)
    if invalid_labels:
        blocked.append(f"invalid_human_label_count:{len(invalid_labels)}")
    if missing_sample_ids:
        blocked.append(f"labels_reference_missing_samples:{len(missing_sample_ids)}")
    if missing_label_ids:
        blocked.append(f"samples_without_label_rows:{len(missing_label_ids)}")
    if duplicate_label_ids:
        blocked.append(f"duplicate_label_sample_ids:{len(duplicate_label_ids)}")
    if labeled_rows < args.min_labeled:
        blocked.append(f"insufficient_labeled_rows:{labeled_rows}/{args.min_labeled}")

    precision_summary = summarize_precision(labels, samples_by_id)
    required_precision = precision_summary["required_violation_buckets"]["precision_quality_issue"]
    if required_precision is None:
        blocked.append("violated_precision_unavailable")
    elif required_precision < args.min_violated_precision:
        blocked.append(
            f"violated_quality_issue_precision_below_threshold:{required_precision:.4f}<{args.min_violated_precision:.4f}"
        )

    status = "ready" if not blocked else "blocked_unlabeled" if unlabeled_rows else "blocked"
    summary = {
        "schema_version": "h001_human_audit_label_summary_v1",
        "created_at": date.today().isoformat(),
        "status": status,
        "inputs": {
            "labels_jsonl": relpath(args.labels_jsonl),
            "samples_jsonl": relpath(args.samples_jsonl),
        },
        "parameters": {
            "min_labeled": args.min_labeled,
            "min_violated_precision": args.min_violated_precision,
        },
        "counts": {
            "sample_rows": len(samples),
            "label_rows": len(labels),
            "labeled_rows": labeled_rows,
            "unlabeled_rows": unlabeled_rows,
            "unique_sample_ids": len(sample_ids),
            "unique_label_sample_ids": len(label_ids),
        },
        "label_counts": dict(sorted(Counter(label_value(row) for row in labels).items())),
        "audit_sources": dict(
            sorted(Counter(str(row.get("audit_source") or "unspecified") for row in labels).items())
        ),
        "by_bucket": group_counts(labels, samples_by_id, "bucket"),
        "by_family": group_counts(labels, samples_by_id, "family"),
        "by_predicate": group_counts(labels, samples_by_id, "predicate"),
        "by_verification_status": group_counts(labels, samples_by_id, "verification_status"),
        "boolean_fields": {
            "relation_visible": bool_counts(labels, "relation_visible"),
            "geometry_sufficient": bool_counts(labels, "geometry_sufficient"),
            "verifier_decision_correct": bool_counts(labels, "verifier_decision_correct"),
            "figure_candidate": bool_counts(labels, "figure_candidate"),
        },
        "violation_precision": precision_summary,
        "figure_candidates": collect_figure_candidates(labels, samples_by_id),
        "validation": {
            "invalid_labels": invalid_labels[:50],
            "missing_sample_ids": missing_sample_ids[:50],
            "missing_label_ids": missing_label_ids[:50],
            "duplicate_label_ids": duplicate_label_ids[:50],
        },
        "blocked": blocked,
        "outputs": {
            "summary_json": relpath(args.output_dir / "label_summary.json"),
            "report_md": relpath(args.output_dir / "label_report.md"),
        },
    }

    if not args.dry_run:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_json(args.output_dir / "label_summary.json", summary)
        (args.output_dir / "label_report.md").write_text(make_report(summary), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": status,
                "dry_run": args.dry_run,
                "labeled_rows": labeled_rows,
                "unlabeled_rows": unlabeled_rows,
                "blocked": blocked,
                "output_dir": relpath(args.output_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
