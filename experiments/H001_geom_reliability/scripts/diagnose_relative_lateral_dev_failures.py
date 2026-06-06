#!/usr/bin/env python3
"""Diagnose relative-lateral dev strict contradictions and uncertain rows.

This reads the train/dev policy-lock output only. It does not alter policy
thresholds, read source predictions, compute source metrics, or update the paper
claim.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_relative_lateral_dev_failure_diagnosis_v1"
STATUS = "relative_lateral_dev_failure_diagnosis_ready_no_policy_change_no_source_metrics"
DEFAULT_POLICY_LOCK = Path("experiments/H001_geom_reliability/sources/relative_lateral/train_dev_policy_lock")
DEFAULT_OUT = Path("experiments/H001_geom_reliability/sources/relative_lateral/dev_failure_diagnosis")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--policy-lock-dir", type=Path, default=DEFAULT_POLICY_LOCK)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--max-examples-per-bucket", type=int, default=25)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                try:
                    yield line_no, json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid_jsonl:{path}:{line_no}:{exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def finite(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def bucket_for_row(row: dict[str, Any]) -> str:
    status = row.get("verification_status")
    source_type = row.get("source_type")
    if source_type == "gt_positive" and status == "violated":
        return "positive_strict_contradiction"
    if source_type == "gt_positive" and status == "uncertain":
        return "positive_uncertain"
    if source_type == "label_flip_counterfactual" and status == "satisfied":
        return "counterfactual_false_satisfaction"
    if source_type == "label_flip_counterfactual" and status == "uncertain":
        return "counterfactual_uncertain"
    return "not_failure_focus"


def physical_pair_key(row: dict[str, Any]) -> str:
    ids = sorted([int(row["subject_id"]), int(row["object_id"])])
    return f"{row['scan_id']}:{row['subset_split_id']}:{ids[0]}:{ids[1]}"


def relation_key(row: dict[str, Any]) -> str:
    return f"{row['scan_id']}:{row['subset_split_id']}:{row['relation_idx']}"


def signed_projection_support(row: dict[str, Any]) -> str:
    status = row.get("verification_status")
    sign_only = row.get("sign_only_status")
    if status == "uncertain" and sign_only == "satisfied":
        return "lateral_sign_supports_label_but_strict_ambiguity"
    if status == "uncertain" and sign_only == "violated":
        return "lateral_sign_contradicts_label_with_strict_ambiguity"
    if status == "violated":
        return "lateral_sign_contradicts_label"
    if status == "satisfied":
        return "lateral_sign_supports_label"
    return "other"


def reason_signature(row: dict[str, Any]) -> str:
    reasons = row.get("reason_codes") or row.get("ambiguity_flags") or []
    return "+".join(sorted(str(item) for item in reasons)) if reasons else "no_strict_ambiguity_flag"


def numeric_summary(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "median": None, "mean": None, "max": None}
    values = sorted(values)
    return {
        "count": len(values),
        "min": values[0],
        "median": values[len(values) // 2],
        "mean": sum(values) / len(values),
        "max": values[-1],
    }


def row_ratios(row: dict[str, Any]) -> dict[str, Any]:
    target = finite(row.get("target_projection_m"))
    other = finite(row.get("other_projection_m"))
    margin = finite(row.get("margin_m"))
    ratios: dict[str, Any] = {
        "abs_target_over_margin": None,
        "abs_other_over_margin": None,
        "abs_other_over_abs_target": None,
    }
    if target is not None and margin is not None and margin > 0:
        ratios["abs_target_over_margin"] = abs(target) / margin
    if other is not None and margin is not None and margin > 0:
        ratios["abs_other_over_margin"] = abs(other) / margin
    if target is not None and other is not None and abs(target) > 1e-9:
        ratios["abs_other_over_abs_target"] = abs(other) / abs(target)
    return ratios


def compact_case(row: dict[str, Any], bucket: str) -> dict[str, Any]:
    ratios = row_ratios(row)
    return {
        "bucket": bucket,
        "row_id": row.get("row_id"),
        "physical_pair_key": physical_pair_key(row),
        "relation_key": relation_key(row),
        "source_type": row.get("source_type"),
        "scan_id": row.get("scan_id"),
        "subset_split_id": row.get("subset_split_id"),
        "relation_idx": row.get("relation_idx"),
        "subject_id": row.get("subject_id"),
        "object_id": row.get("object_id"),
        "subject_label": row.get("subject_label"),
        "object_label": row.get("object_label"),
        "predicate_label": row.get("predicate_label"),
        "verification_status": row.get("verification_status"),
        "sign_only_status": row.get("sign_only_status"),
        "reason_signature": reason_signature(row),
        "projection_support": signed_projection_support(row),
        "target_projection_m": row.get("target_projection_m"),
        "other_projection_m": row.get("other_projection_m"),
        "margin_m": row.get("margin_m"),
        "projected_overlap_max_ratio": row.get("projected_overlap_max_ratio"),
        "p_geom_valid_train_dev_lateral": row.get("p_geom_valid_train_dev_lateral"),
        **ratios,
    }


def summarize(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    dev_rows = [row for row in rows if row.get("split") == "dev"]
    focus_rows = [row for row in dev_rows if bucket_for_row(row) != "not_failure_focus"]
    focus_cases = [compact_case(row, bucket_for_row(row)) for row in focus_rows]
    positive_failures = [row for row in focus_rows if row.get("source_type") == "gt_positive"]
    pair_to_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    relation_to_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in focus_rows:
        pair_to_rows[physical_pair_key(row)].append(row)
        relation_to_rows[relation_key(row)].append(row)

    by_bucket: dict[str, Any] = {}
    for bucket in [
        "positive_strict_contradiction",
        "positive_uncertain",
        "counterfactual_false_satisfaction",
        "counterfactual_uncertain",
    ]:
        subset = [row for row in focus_rows if bucket_for_row(row) == bucket]
        ratios = [row_ratios(row) for row in subset]
        by_bucket[bucket] = {
            "rows": len(subset),
            "physical_pairs": len({physical_pair_key(row) for row in subset}),
            "same_object_label_rows": sum(1 for row in subset if row.get("subject_label") == row.get("object_label")),
            "same_object_label_share": (
                sum(1 for row in subset if row.get("subject_label") == row.get("object_label")) / len(subset)
                if subset
                else None
            ),
            "label_counts": dict(sorted(Counter(str(row.get("predicate_label")) for row in subset).items())),
            "reason_signatures": dict(sorted(Counter(reason_signature(row) for row in subset).items())),
            "projection_support": dict(sorted(Counter(signed_projection_support(row) for row in subset).items())),
            "scan_counts_top": Counter(str(row.get("scan_id")) for row in subset).most_common(8),
            "object_pair_label_top": Counter(
                f"{row.get('subject_label')}->{row.get('object_label')}" for row in subset
            ).most_common(12),
            "abs_target_over_margin": numeric_summary(
                [item["abs_target_over_margin"] for item in ratios if item["abs_target_over_margin"] is not None]
            ),
            "abs_other_over_abs_target": numeric_summary(
                [
                    item["abs_other_over_abs_target"]
                    for item in ratios
                    if item["abs_other_over_abs_target"] is not None
                ]
            ),
            "projected_overlap_max_ratio": numeric_summary(
                [
                    float(row["projected_overlap_max_ratio"])
                    for row in subset
                    if finite(row.get("projected_overlap_max_ratio")) is not None
                ]
            ),
        }

    by_positive_label = {
        label: {
            "rows": len([row for row in positive_failures if row.get("predicate_label") == label]),
            "status_counts": dict(
                sorted(Counter(row.get("verification_status") for row in positive_failures if row.get("predicate_label") == label).items())
            ),
            "reason_signatures": dict(
                sorted(Counter(reason_signature(row) for row in positive_failures if row.get("predicate_label") == label).items())
            ),
        }
        for label in ("left", "right")
    }
    pair_diagnostic_counts = Counter()
    for pair_rows in pair_to_rows.values():
        pair_buckets = sorted({bucket_for_row(row) for row in pair_rows})
        pair_diagnostic_counts["+".join(pair_buckets)] += 1

    contradiction_positive_rows = [row for row in dev_rows if row.get("source_type") == "gt_positive" and row.get("verification_status") == "violated"]
    uncertain_positive_rows = [row for row in dev_rows if row.get("source_type") == "gt_positive" and row.get("verification_status") == "uncertain"]
    contradiction_scans = Counter(str(row.get("scan_id")) for row in contradiction_positive_rows)
    uncertain_scans = Counter(str(row.get("scan_id")) for row in uncertain_positive_rows)
    summary = {
        "dev_rows": len(dev_rows),
        "dev_gt_positive_rows": sum(1 for row in dev_rows if row.get("source_type") == "gt_positive"),
        "dev_counterfactual_rows": sum(1 for row in dev_rows if row.get("source_type") == "label_flip_counterfactual"),
        "focus_rows": len(focus_rows),
        "focus_physical_pairs": len(pair_to_rows),
        "focus_relation_keys": len(relation_to_rows),
        "positive_strict_contradiction_rows": len(contradiction_positive_rows),
        "positive_strict_contradiction_physical_pairs": len({physical_pair_key(row) for row in contradiction_positive_rows}),
        "positive_strict_contradiction_scan_counts_top": contradiction_scans.most_common(8),
        "positive_strict_contradiction_same_label_share": (
            sum(1 for row in contradiction_positive_rows if row.get("subject_label") == row.get("object_label"))
            / len(contradiction_positive_rows)
            if contradiction_positive_rows
            else None
        ),
        "positive_uncertain_rows": len(uncertain_positive_rows),
        "positive_uncertain_physical_pairs": len({physical_pair_key(row) for row in uncertain_positive_rows}),
        "positive_uncertain_scan_counts_top": uncertain_scans.most_common(8),
        "positive_uncertain_same_label_share": (
            sum(1 for row in uncertain_positive_rows if row.get("subject_label") == row.get("object_label"))
            / len(uncertain_positive_rows)
            if uncertain_positive_rows
            else None
        ),
        "by_bucket": by_bucket,
        "by_positive_label": by_positive_label,
        "pair_diagnostic_counts": dict(sorted(pair_diagnostic_counts.items())),
        "primary_diagnosis": [
            "Strict contradictions are symmetric left/right sign conflicts at pair level, not random row noise.",
            "Strict contradictions are concentrated in two dev scans and about half involve same-label object pairs such as pillow-pillow or box-box.",
            "Most uncertain rows are not sign failures; they are caused by conflicting orthogonal-axis dominance, meaning the pair is more front/back separated than laterally separated under the frozen scan frame.",
            "Uncertain rows also contain many repeated-object cases, so a visual/frame-metadata study would be needed before treating this as broadly valid lateral evidence.",
            "The dev split is therefore a coordinate/frame-orientation boundary case for lateral promotion, not a source-prediction metric issue.",
        ],
    }
    return summary, focus_cases


def select_examples(cases: list[dict[str, Any]], max_examples_per_bucket: int) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        grouped[str(case["bucket"])].append(case)
    selected: list[dict[str, Any]] = []
    for bucket, rows in sorted(grouped.items()):
        rows.sort(
            key=lambda row: (
                -(float(row["abs_other_over_abs_target"]) if row.get("abs_other_over_abs_target") is not None else -1.0),
                str(row.get("scan_id")),
                int(row.get("subset_split_id") or 0),
                int(row.get("relation_idx") or 0),
            )
        )
        selected.extend(rows[:max_examples_per_bucket])
    return selected


def commands_md() -> str:
    return """# Relative Lateral Dev Failure Diagnosis Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm \\
  relative_lateral_dev_failure_diagnosis
```

This reads `relative_lateral/train_dev_policy_lock/rows.jsonl` only. It does
not change policy, read source predictions, or compute source metrics.
"""


def fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def report_md(manifest: dict[str, Any], summary: dict[str, Any]) -> str:
    lines = [
        "# Relative Lateral Dev Failure Diagnosis",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Boundary",
        "",
        "This diagnosis reads the frozen train/dev policy-lock rows only. It does",
        "not change the policy, does not read source predictions, does not compute",
        "source metrics, and does not change the paper claim.",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "|---|---:|",
        f"| dev GT-positive rows | {summary['dev_gt_positive_rows']} |",
        f"| positive strict contradiction rows | {summary['positive_strict_contradiction_rows']} |",
        f"| positive strict contradiction physical pairs | {summary['positive_strict_contradiction_physical_pairs']} |",
        f"| positive strict contradiction same-label share | {fmt(summary['positive_strict_contradiction_same_label_share'])} |",
        f"| positive uncertain rows | {summary['positive_uncertain_rows']} |",
        f"| positive uncertain physical pairs | {summary['positive_uncertain_physical_pairs']} |",
        f"| positive uncertain same-label share | {fmt(summary['positive_uncertain_same_label_share'])} |",
        f"| all focus rows including counterfactual mirrors | {summary['focus_rows']} |",
        f"| all focus physical pairs | {summary['focus_physical_pairs']} |",
        "",
        "## Bucket Summary",
        "",
        "| Bucket | Rows | Physical pairs | Same-label share | Top reasons | Top projection support |",
        "|---|---:|---:|---:|---|---|",
    ]
    for bucket, item in summary["by_bucket"].items():
        reasons = ", ".join(f"{key}:{value}" for key, value in list(item["reason_signatures"].items())[:3])
        support = ", ".join(f"{key}:{value}" for key, value in list(item["projection_support"].items())[:3])
        lines.append(
            f"| `{bucket}` | {item['rows']} | {item['physical_pairs']} | "
            f"{fmt(item['same_object_label_share'])} | `{reasons}` | `{support}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in summary["primary_diagnosis"])
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            "- Do not promote `relative_lateral` to main claim from the current strict",
            "  policy-lock result.",
            "- Do not tune the frozen validation policy to fix this dev split.",
            "- If this family is kept, frame it as caveated appendix evidence or run",
            "  a separate predeclared frame/annotation study before source metrics.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    policy_lock_dir = resolve(repo_root, args.policy_lock_dir)
    out = resolve(repo_root, args.out)
    manifest_in = read_json(policy_lock_dir / "manifest.json")
    rows = [row for _, row in iter_jsonl(policy_lock_dir / "rows.jsonl")]
    summary, cases = summarize(rows)
    examples = select_examples(cases, args.max_examples_per_bucket)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "policy_lock_manifest": relpath(repo_root, policy_lock_dir / "manifest.json"),
            "policy_lock_rows": relpath(repo_root, policy_lock_dir / "rows.jsonl"),
            "policy_lock_status": manifest_in.get("status"),
        },
        "claim_boundary": {
            "policy_changed": False,
            "source_predictions_used": False,
            "source_metrics_run": False,
            "paper_claim_promotion_allowed": False,
        },
        "summary": summary,
        "outputs": {
            "summary": "summary.json",
            "focus_cases": "focus_cases.jsonl",
            "examples": "examples.jsonl",
            "commands": "commands.md",
            "report": "report.md",
        },
        "next_gate": "relative_lateral_keep_caveated_or_predeclare_separate_frame_annotation_study",
    }
    ensure_dir(out)
    write_json(out / "manifest.json", manifest)
    write_json(out / "summary.json", summary)
    write_jsonl(out / "focus_cases.jsonl", cases)
    write_jsonl(out / "examples.jsonl", examples)
    write_text(out / "commands.md", commands_md())
    write_text(out / "report.md", report_md(manifest, summary))
    print(
        json.dumps(
            {
                "status": STATUS,
                "out": relpath(repo_root, out),
                "positive_strict_contradiction_rows": summary["positive_strict_contradiction_rows"],
                "positive_strict_contradiction_physical_pairs": summary[
                    "positive_strict_contradiction_physical_pairs"
                ],
                "positive_uncertain_rows": summary["positive_uncertain_rows"],
                "positive_uncertain_physical_pairs": summary["positive_uncertain_physical_pairs"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
