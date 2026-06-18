#!/usr/bin/env python3
"""Audit H002 full-train independent target shortcut risk and controlled slices."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_INPUT_ROWS = RGA_ROOT / "independent_label_ingestion_codex_ver/posterior_rows.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_target_independence_audit_codex_ver"

HIDDEN_GROUP_KEYS = [
    "queue_kind_hidden",
    "candidate_axis_hidden",
    "proposed_audit_role_hidden",
    "label_match_status_hidden",
    "geometry_status_hidden",
    "h001_verification_status_hidden",
    "rank_band_hidden",
    "label_geometry_bucket_hidden",
    "bucket_top50_hidden",
    "bucket_top100_hidden",
]

VISIBLE_GROUP_KEYS = [
    "predicate_family",
    "predicate_label",
    "confidence",
    "visual_3d_support",
    "relation_informativeness",
    "packet_gap_decision",
]

RISK_NMI_THRESHOLD = 0.25
RISK_MAJORITY_THRESHOLD = 0.85
MIN_CANDIDATE_ROWS = 120
MIN_CANDIDATE_PER_CLASS = 50

SLICE_SPECS = {
    "original_independent_codex_ver": {
        "balanced_keys": [],
        "reason": "full ingested codex-version independent binary target",
        "priority": 99,
    },
    "family_balanced_codex_ver": {
        "balanced_keys": ["predicate_family"],
        "reason": "matched positives/negatives within predicate_family",
        "priority": 6,
    },
    "predicate_balanced_codex_ver": {
        "balanced_keys": ["predicate_label"],
        "reason": "matched positives/negatives within predicate_label",
        "priority": 7,
    },
    "queue_balanced_codex_ver": {
        "balanced_keys": ["queue_kind_hidden"],
        "reason": "matched positives/negatives within hidden HL/LH queue",
        "priority": 5,
    },
    "geometry_status_balanced_codex_ver": {
        "balanced_keys": ["geometry_status_hidden"],
        "reason": "matched positives/negatives within hidden geometry_status",
        "priority": 5,
    },
    "rank_band_balanced_codex_ver": {
        "balanced_keys": ["rank_band_hidden"],
        "reason": "matched positives/negatives within hidden semantic rank band",
        "priority": 4,
    },
    "label_status_balanced_codex_ver": {
        "balanced_keys": ["label_match_status_hidden"],
        "reason": "matched positives/negatives within hidden label_match_status",
        "priority": 3,
    },
    "proposed_role_balanced_codex_ver": {
        "balanced_keys": ["proposed_audit_role_hidden"],
        "reason": "matched positives/negatives within hidden proposed_audit_role",
        "priority": 1,
    },
    "queue_family_balanced_codex_ver": {
        "balanced_keys": ["queue_kind_hidden", "predicate_family"],
        "reason": "matched positives/negatives within hidden queue and visible family",
        "priority": 2,
    },
    "label_status_family_balanced_codex_ver": {
        "balanced_keys": ["label_match_status_hidden", "predicate_family"],
        "reason": "matched positives/negatives within hidden label status and visible family",
        "priority": 3,
    },
    "role_family_balanced_codex_ver": {
        "balanced_keys": ["proposed_audit_role_hidden", "predicate_family"],
        "reason": "matched positives/negatives within hidden proposed role and visible family",
        "priority": 2,
    },
    "rank_family_balanced_codex_ver": {
        "balanced_keys": ["rank_band_hidden", "predicate_family"],
        "reason": "matched positives/negatives within hidden rank band and visible family",
        "priority": 4,
    },
    "role_predicate_balanced_codex_ver": {
        "balanced_keys": ["proposed_audit_role_hidden", "predicate_label"],
        "reason": "matched positives/negatives within hidden proposed role and visible predicate",
        "priority": 2,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-rows", type=Path, default=DEFAULT_INPUT_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str | None:
    if path is None:
        return None
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def target_y(row: dict[str, Any]) -> int:
    return int(row["posterior_target"])


def group_value(row: dict[str, Any], key: str) -> str:
    if key in row:
        return str(row.get(key))
    hidden = row.get("hidden_audit_metadata_post_label_only", {})
    if key in hidden:
        return str(hidden.get(key))
    deployable = row.get("deployable_evidence_after_label_lock", {})
    if key in deployable:
        return str(deployable.get(key))
    return "missing"


def semantic_rank(row: dict[str, Any]) -> float:
    value = row.get("deployable_evidence_after_label_lock", {}).get("semantic_rank")
    try:
        return float(value)
    except (TypeError, ValueError):
        return 1e12


def stable_key(row: dict[str, Any]) -> tuple[float, str]:
    return semantic_rank(row), str(row.get("prediction_id", row.get("blind_review_id")))


def entropy_from_counts(pos: int, neg: int) -> float:
    total = pos + neg
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in [pos, neg]:
        if count <= 0:
            continue
        prob = count / total
        entropy -= prob * math.log2(prob)
    return entropy


def group_summary(rows: list[dict[str, Any]], group_key: str, source: str, target_mode: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_group[group_value(row, group_key)].append(row)

    total_counts = Counter(target_y(row) for row in rows)
    overall_entropy = entropy_from_counts(total_counts[1], total_counts[0])
    weighted_conditional_entropy = 0.0
    majority_correct = 0
    table = []
    for value, group_rows in sorted(by_group.items()):
        counts = Counter(target_y(row) for row in group_rows)
        pos = counts[1]
        neg = counts[0]
        majority_label = 1 if pos >= neg else 0
        majority = max(pos, neg)
        group_entropy = entropy_from_counts(pos, neg)
        if rows:
            weighted_conditional_entropy += len(group_rows) / len(rows) * group_entropy
        majority_correct += majority
        table.append(
            {
                "target_mode": target_mode,
                "source": source,
                "group_key": group_key,
                "group_value": value,
                "rows": len(group_rows),
                "positive": pos,
                "negative": neg,
                "positive_rate": pos / len(group_rows) if group_rows else 0.0,
                "majority_label": majority_label,
                "majority_accuracy": majority / len(group_rows) if group_rows else 0.0,
                "entropy_bits": group_entropy,
            }
        )

    mutual_information = max(0.0, overall_entropy - weighted_conditional_entropy)
    summary = {
        "target_mode": target_mode,
        "source": source,
        "group_key": group_key,
        "groups": len(by_group),
        "rows": len(rows),
        "overall_positive": total_counts[1],
        "overall_negative": total_counts[0],
        "overall_entropy_bits": overall_entropy,
        "conditional_entropy_bits": weighted_conditional_entropy,
        "mutual_information_bits": mutual_information,
        "normalized_mutual_information": mutual_information / overall_entropy if overall_entropy > 0 else 0.0,
        "majority_rule_accuracy": majority_correct / len(rows) if rows else 0.0,
        "single_class_groups": sum(1 for item in table if item["positive"] == 0 or item["negative"] == 0),
    }
    return table, summary


def all_group_summaries(rows: list[dict[str, Any]], target_mode: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    group_rows = []
    summaries = []
    for key in VISIBLE_GROUP_KEYS:
        table, summary = group_summary(rows, key, "visible_label_surface", target_mode)
        group_rows.extend(table)
        summaries.append(summary)
    for key in HIDDEN_GROUP_KEYS:
        table, summary = group_summary(rows, key, "hidden_post_label_audit", target_mode)
        group_rows.extend(table)
        summaries.append(summary)
    return group_rows, summaries


def is_risky(summary: dict[str, Any]) -> bool:
    return (
        float(summary["normalized_mutual_information"]) >= RISK_NMI_THRESHOLD
        or float(summary["majority_rule_accuracy"]) >= RISK_MAJORITY_THRESHOLD
    )


def risk_summaries(summaries: list[dict[str, Any]], source: str | None = None) -> list[dict[str, Any]]:
    output = []
    for summary in summaries:
        if source is not None and summary["source"] != source:
            continue
        if is_risky(summary):
            output.append(summary)
    return output


def clone_for_slice(row: dict[str, Any], target_mode: str, spec: dict[str, Any]) -> dict[str, Any]:
    copied = deepcopy(row)
    copied["target_mode"] = target_mode
    copied["target_slice_reason"] = spec["reason"]
    copied["balanced_keys"] = spec["balanced_keys"]
    copied["audit_selection_only"] = True
    return copied


def balanced_slice(rows: list[dict[str, Any]], target_mode: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    keys = list(spec["balanced_keys"])
    if not keys:
        return [clone_for_slice(row, target_mode, spec) for row in sorted(rows, key=stable_key)]

    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(group_value(row, key) for key in keys)].append(row)

    selected: list[dict[str, Any]] = []
    for _, group_rows in sorted(groups.items()):
        positives = sorted([row for row in group_rows if target_y(row) == 1], key=stable_key)
        negatives = sorted([row for row in group_rows if target_y(row) == 0], key=stable_key)
        if not positives or not negatives:
            continue
        minority, majority = (positives, negatives) if len(positives) <= len(negatives) else (negatives, positives)
        used_majority: set[str] = set()
        for row in minority:
            candidates = [
                candidate
                for candidate in majority
                if str(candidate["prediction_id"]) not in used_majority
            ]
            if not candidates:
                break
            match = min(
                candidates,
                key=lambda candidate: (
                    abs(semantic_rank(candidate) - semantic_rank(row)),
                    str(candidate["prediction_id"]),
                ),
            )
            used_majority.add(str(match["prediction_id"]))
            selected.append(clone_for_slice(row, target_mode, spec))
            selected.append(clone_for_slice(match, target_mode, spec))

    return sorted(selected, key=stable_key)


def slice_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(target_y(row) for row in rows)
    return {
        "rows": len(rows),
        "positive": counts[1],
        "negative": counts[0],
        "by_family": dict(sorted(Counter(group_value(row, "predicate_family") for row in rows).items())),
        "by_predicate": dict(sorted(Counter(group_value(row, "predicate_label") for row in rows).items())),
        "by_role": dict(sorted(Counter(group_value(row, "proposed_audit_role_hidden") for row in rows).items())),
        "by_label_status": dict(sorted(Counter(group_value(row, "label_match_status_hidden") for row in rows).items())),
    }


def slice_summary(
    target_mode: str,
    spec: dict[str, Any],
    rows: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    path: Path,
) -> dict[str, Any]:
    counts = slice_counts(rows)
    hidden_risks = risk_summaries(summaries, "hidden_post_label_audit")
    visible_risks = risk_summaries(summaries, "visible_label_surface")
    min_class = min(counts["positive"], counts["negative"]) if rows else 0
    size_ready = counts["rows"] >= MIN_CANDIDATE_ROWS and min_class >= MIN_CANDIDATE_PER_CLASS
    hidden_ready = len(hidden_risks) == 0
    visible_ready = len(visible_risks) == 0
    controlled_candidate = size_ready and hidden_ready
    return {
        "target_mode": target_mode,
        "path": rel_path(path),
        "balanced_keys": spec["balanced_keys"],
        "reason": spec["reason"],
        "priority": spec["priority"],
        "rows": counts["rows"],
        "positive": counts["positive"],
        "negative": counts["negative"],
        "min_class": min_class,
        "hidden_risk_count": len(hidden_risks),
        "visible_risk_count": len(visible_risks),
        "size_ready": size_ready,
        "hidden_ready": hidden_ready,
        "visible_ready": visible_ready,
        "controlled_candidate": controlled_candidate,
        "top_hidden_risks": [
            {
                "group_key": item["group_key"],
                "majority_rule_accuracy": item["majority_rule_accuracy"],
                "normalized_mutual_information": item["normalized_mutual_information"],
            }
            for item in sorted(
                hidden_risks,
                key=lambda item: (
                    -float(item["normalized_mutual_information"]),
                    -float(item["majority_rule_accuracy"]),
                ),
            )[:5]
        ],
        "top_visible_risks": [
            {
                "group_key": item["group_key"],
                "majority_rule_accuracy": item["majority_rule_accuracy"],
                "normalized_mutual_information": item["normalized_mutual_information"],
            }
            for item in sorted(
                visible_risks,
                key=lambda item: (
                    -float(item["normalized_mutual_information"]),
                    -float(item["majority_rule_accuracy"]),
                ),
            )[:5]
        ],
        "counts": counts,
    }


def build_slices(rows: list[dict[str, Any]], output_dir: Path) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    slice_dir = output_dir / "target_slices"
    slices: dict[str, list[dict[str, Any]]] = {}
    slice_summaries = []
    group_table = []
    group_summary_rows = []

    for target_mode, spec in SLICE_SPECS.items():
        slice_rows = balanced_slice(rows, target_mode, spec)
        path = slice_dir / f"{target_mode}.jsonl"
        write_jsonl(path, slice_rows)
        groups, summaries = all_group_summaries(slice_rows, target_mode)
        group_table.extend(groups)
        group_summary_rows.extend(summaries)
        slices[target_mode] = slice_rows
        slice_summaries.append(slice_summary(target_mode, spec, slice_rows, summaries, path))

    return slices, slice_summaries, group_table, group_summary_rows


def choose_recommendation(slice_summaries: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [item for item in slice_summaries if item["controlled_candidate"]]
    if not candidates:
        return None
    return sorted(
        candidates,
        key=lambda item: (
            int(item["priority"]),
            -int(item["rows"]),
            -int(item["min_class"]),
        ),
    )[0]


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Full Train Independent Target Independence Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage target audit.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Hidden metadata is used only after label lock for audit and controlled-slice construction.",
        "- Codex-version labels are not human-confirmed paper evidence.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "Decision:",
        "",
        summary["decision"],
        "",
        "## Original Risk",
        "",
        "| Key | Majority Acc | NMI |",
        "| --- | ---: | ---: |",
    ]
    for item in summary["original_hidden_risks"]:
        lines.append(
            f"| `{item['group_key']}` | {item['majority_rule_accuracy']:.4f} | {item['normalized_mutual_information']:.4f} |"
        )
    if not summary["original_hidden_risks"]:
        lines.append("| none | 0.0000 | 0.0000 |")

    lines.extend(
        [
            "",
            "## Controlled Slices",
            "",
            "| Target Slice | Rows | Pos | Neg | Hidden Risks | Candidate |",
            "| --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for item in sorted(summary["slice_summaries"], key=lambda row: (not row["controlled_candidate"], row["priority"], -row["rows"])):
        lines.append(
            f"| `{item['target_mode']}` | {item['rows']} | {item['positive']} | {item['negative']} | "
            f"{item['hidden_risk_count']} | `{item['controlled_candidate']}` |"
        )

    recommendation = summary.get("recommended_slice")
    lines.extend(["", "## Recommendation", ""])
    if recommendation:
        lines.extend(
            [
                f"Primary controlled target candidate: `{recommendation['target_mode']}`",
                "",
                f"Rows: `{recommendation['rows']}`, positive: `{recommendation['positive']}`, negative: `{recommendation['negative']}`.",
                "",
                "Use it only as a train-only controlled diagnostic target. It is not paper evidence.",
            ]
        )
    else:
        lines.append("No controlled slice satisfies the minimum size and hidden-risk criteria.")

    lines.extend(
        [
            "",
            "## Next TODO",
            "",
            summary["next_todo"],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_rows = as_abs(args.input_rows)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    rows = read_jsonl(input_rows)
    slices, slice_summaries, group_table, group_summary_rows = build_slices(rows, output_dir)
    original_summary = next(item for item in slice_summaries if item["target_mode"] == "original_independent_codex_ver")
    recommendation = choose_recommendation(slice_summaries)

    if recommendation:
        status = "full_train_independent_target_independence_audit_controlled_slice_ready"
        decision = (
            "The original target has hidden metadata shortcut risk, but at least one "
            "controlled slice is large enough and has no hidden group risk under the "
            "audit thresholds. Posterior smoke may resume only on the recommended "
            "controlled slice as train-only diagnostics."
        )
        next_todo = "full_train_independent_controlled_posterior_smoke"
    else:
        status = "full_train_independent_target_independence_audit_blocked"
        decision = (
            "The original target has hidden metadata shortcut risk and no controlled "
            "slice is large enough to support posterior smoke. Revise the target or "
            "collect stronger independent labels."
        )
        next_todo = "revise_full_train_independent_target_or_collect_labels"

    summary_path = output_dir / "summary.json"
    report_path = output_dir / "report.md"
    slice_summary_path = output_dir / "slice_summaries.csv"
    group_summary_path = output_dir / "group_summaries.csv"
    group_table_path = output_dir / "group_table.csv"

    summary = {
        "schema_version": "h002_full_train_independent_target_independence_audit_summary_v0",
        "status": status,
        "created_at": created_at,
        "input_rows": rel_path(input_rows),
        "output_dir": rel_path(output_dir),
        "output_paths": {
            "summary": rel_path(summary_path),
            "report": rel_path(report_path),
            "slice_summaries": rel_path(slice_summary_path),
            "group_summaries": rel_path(group_summary_path),
            "group_table": rel_path(group_table_path),
            "target_slices": rel_path(output_dir / "target_slices"),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "label_source": "codex_ver_full_train_independent_visible_surface_bootstrap",
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "hidden_metadata_used_for_audit_only": True,
            "vmv_model_input_allowed": False,
        },
        "risk_thresholds": {
            "normalized_mutual_information": RISK_NMI_THRESHOLD,
            "majority_rule_accuracy": RISK_MAJORITY_THRESHOLD,
            "min_candidate_rows": MIN_CANDIDATE_ROWS,
            "min_candidate_per_class": MIN_CANDIDATE_PER_CLASS,
        },
        "original_hidden_risks": original_summary["top_hidden_risks"],
        "slice_summaries": slice_summaries,
        "recommended_slice": recommendation,
        "decision": decision,
        "next_todo": next_todo,
    }

    write_json(summary_path, summary)
    write_csv(
        slice_summary_path,
        [
            {
                "target_mode": item["target_mode"],
                "rows": item["rows"],
                "positive": item["positive"],
                "negative": item["negative"],
                "min_class": item["min_class"],
                "balanced_keys": "|".join(item["balanced_keys"]),
                "hidden_risk_count": item["hidden_risk_count"],
                "visible_risk_count": item["visible_risk_count"],
                "size_ready": item["size_ready"],
                "hidden_ready": item["hidden_ready"],
                "visible_ready": item["visible_ready"],
                "controlled_candidate": item["controlled_candidate"],
                "path": item["path"],
            }
            for item in slice_summaries
        ],
    )
    write_csv(group_summary_path, group_summary_rows)
    write_csv(group_table_path, group_table)
    write_report(report_path, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    rec = summary.get("recommended_slice") or {}
    print(
        f"status={summary['status']} recommended={rec.get('target_mode', 'none')} "
        f"rows={rec.get('rows', 0)} positive={rec.get('positive', 0)} negative={rec.get('negative', 0)} "
        f"validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
