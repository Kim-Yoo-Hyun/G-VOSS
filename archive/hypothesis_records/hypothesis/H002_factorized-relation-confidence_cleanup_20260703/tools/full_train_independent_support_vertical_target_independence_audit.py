#!/usr/bin/env python3
"""Audit support/vertical target shortcut risk and controlled slices."""

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
DEFAULT_INPUT_ROWS = RGA_ROOT / "independent_support_vertical_label_ingestion_codex_ver/posterior_rows.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_target_independence_audit_codex_ver"

STRICT_HIDDEN_GROUP_KEYS = [
    "relation_validity_label_hidden",
    "label_use_hidden",
    "rank_band_hidden",
    "proposed_audit_role_hidden",
    "queue_kind_hidden",
    "geometry_status_hidden",
    "label_match_status_hidden",
]

CONSTRUCTION_HIDDEN_GROUP_KEYS = [
    "rank_band_hidden",
    "proposed_audit_role_hidden",
    "queue_kind_hidden",
    "geometry_status_hidden",
    "label_match_status_hidden",
]

VISIBLE_GROUP_KEYS = [
    "predicate_family",
    "predicate_label",
    "confidence",
    "visual_3d_support",
    "relation_informativeness",
    "object_pair_visible",
    "evidence_packet_status",
]

RISK_NMI_THRESHOLD = 0.20
RISK_MAJORITY_THRESHOLD = 0.85
RISK_POSITIVE_RATE_RANGE_THRESHOLD = 0.70
RISK_LARGE_GROUP_ROWS = 10
RISK_LARGE_GROUP_PURITY = 0.95

MIN_CANDIDATE_ROWS = 60
MIN_CANDIDATE_PER_CLASS = 25

SLICE_SPECS = {
    "original_support_vertical_codex_ver": {
        "balanced_keys": [],
        "reason": "full selected support/vertical codex-version binary target",
        "priority": 99,
    },
    "relation_validity_balanced_codex_ver": {
        "balanced_keys": ["relation_validity_label_hidden"],
        "reason": "matched positives/negatives within prior hidden relation-validity label",
        "priority": 10,
    },
    "label_use_balanced_codex_ver": {
        "balanced_keys": ["label_use_hidden"],
        "reason": "matched positives/negatives within prior hidden label-use bucket",
        "priority": 10,
    },
    "rank_band_balanced_codex_ver": {
        "balanced_keys": ["rank_band_hidden"],
        "reason": "matched positives/negatives within hidden semantic rank band",
        "priority": 1,
    },
    "rank_family_balanced_codex_ver": {
        "balanced_keys": ["rank_band_hidden", "predicate_family"],
        "reason": "matched positives/negatives within hidden rank band and visible family",
        "priority": 2,
    },
    "proposed_role_balanced_codex_ver": {
        "balanced_keys": ["proposed_audit_role_hidden"],
        "reason": "matched positives/negatives within hidden proposed audit role",
        "priority": 3,
    },
    "queue_balanced_codex_ver": {
        "balanced_keys": ["queue_kind_hidden"],
        "reason": "matched positives/negatives within hidden HL/LH queue",
        "priority": 4,
    },
    "geometry_status_balanced_codex_ver": {
        "balanced_keys": ["geometry_status_hidden"],
        "reason": "matched positives/negatives within hidden geometry status",
        "priority": 4,
    },
    "label_match_balanced_codex_ver": {
        "balanced_keys": ["label_match_status_hidden"],
        "reason": "matched positives/negatives within hidden label-match status",
        "priority": 5,
    },
    "family_balanced_codex_ver": {
        "balanced_keys": ["predicate_family"],
        "reason": "matched positives/negatives within visible predicate family",
        "priority": 6,
    },
    "predicate_balanced_codex_ver": {
        "balanced_keys": ["predicate_label"],
        "reason": "matched positives/negatives within visible predicate label",
        "priority": 7,
    },
    "role_family_balanced_codex_ver": {
        "balanced_keys": ["proposed_audit_role_hidden", "predicate_family"],
        "reason": "matched positives/negatives within hidden role and visible family",
        "priority": 8,
    },
    "queue_family_balanced_codex_ver": {
        "balanced_keys": ["queue_kind_hidden", "predicate_family"],
        "reason": "matched positives/negatives within hidden queue and visible family",
        "priority": 8,
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
    rows: list[dict[str, Any]] = []
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
    fieldnames: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
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
    coverage = deployable.get("coverage_evidence", {})
    if key in coverage:
        return str(coverage.get(key))
    source_scores = deployable.get("source_semantic_and_geometry_scores_hidden_from_labeler_until_lock", {})
    if key in source_scores:
        return str(source_scores.get(key))
    return "missing"


def semantic_rank(row: dict[str, Any]) -> float:
    hidden = row.get("hidden_audit_metadata_post_label_only", {})
    value = hidden.get("semantic_rank_hidden")
    if value is None:
        source_scores = row.get("deployable_evidence_after_label_lock", {}).get(
            "source_semantic_and_geometry_scores_hidden_from_labeler_until_lock", {}
        )
        value = source_scores.get("semantic_rank")
    try:
        return float(value)
    except (TypeError, ValueError):
        return 1e12


def stable_key(row: dict[str, Any]) -> tuple[float, str]:
    return semantic_rank(row), str(row.get("prediction_id", row.get("blind_review_id")))


def entropy_from_counts(counts: Counter[Any]) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        if count <= 0:
            continue
        prob = count / total
        entropy -= prob * math.log2(prob)
    return entropy


def group_summary(
    rows: list[dict[str, Any]],
    group_key: str,
    source: str,
    risk_mode: str,
    target_mode: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_group[group_value(row, group_key)].append(row)

    total_counts = Counter(target_y(row) for row in rows)
    overall_entropy = entropy_from_counts(total_counts)
    weighted_conditional_entropy = 0.0
    majority_correct = 0
    positive_rates: list[float] = []
    large_group_high_purity = False
    table: list[dict[str, Any]] = []
    for value, group_rows in sorted(by_group.items()):
        counts = Counter(target_y(row) for row in group_rows)
        pos = counts[1]
        neg = counts[0]
        total = pos + neg
        majority = max(pos, neg)
        majority_acc = majority / total if total else 0.0
        positive_rate = pos / total if total else 0.0
        group_entropy = entropy_from_counts(counts)
        if rows:
            weighted_conditional_entropy += total / len(rows) * group_entropy
        majority_correct += majority
        positive_rates.append(positive_rate)
        if total >= RISK_LARGE_GROUP_ROWS and majority_acc >= RISK_LARGE_GROUP_PURITY:
            large_group_high_purity = True
        table.append(
            {
                "target_mode": target_mode,
                "risk_mode": risk_mode,
                "source": source,
                "group_key": group_key,
                "group_value": value,
                "rows": total,
                "positive": pos,
                "negative": neg,
                "positive_rate": positive_rate,
                "majority_label": 1 if pos >= neg else 0,
                "majority_accuracy": majority_acc,
                "entropy_bits": group_entropy,
            }
        )

    mutual_information = max(0.0, overall_entropy - weighted_conditional_entropy)
    nmi = mutual_information / overall_entropy if overall_entropy > 0 else 0.0
    positive_rate_min = min(positive_rates) if positive_rates else 0.0
    positive_rate_max = max(positive_rates) if positive_rates else 0.0
    positive_rate_range = positive_rate_max - positive_rate_min
    majority_rule_accuracy = majority_correct / len(rows) if rows else 0.0
    risk_flag = (
        nmi >= RISK_NMI_THRESHOLD
        or majority_rule_accuracy >= RISK_MAJORITY_THRESHOLD
        or positive_rate_range >= RISK_POSITIVE_RATE_RANGE_THRESHOLD
        or large_group_high_purity
    )
    summary = {
        "target_mode": target_mode,
        "risk_mode": risk_mode,
        "source": source,
        "group_key": group_key,
        "groups": len(by_group),
        "rows": len(rows),
        "overall_positive": total_counts[1],
        "overall_negative": total_counts[0],
        "overall_entropy_bits": overall_entropy,
        "conditional_entropy_bits": weighted_conditional_entropy,
        "mutual_information_bits": mutual_information,
        "normalized_mutual_information": nmi,
        "majority_rule_accuracy": majority_rule_accuracy,
        "positive_rate_min": positive_rate_min,
        "positive_rate_max": positive_rate_max,
        "positive_rate_range": positive_rate_range,
        "large_group_high_purity": large_group_high_purity,
        "single_class_groups": sum(1 for item in table if item["positive"] == 0 or item["negative"] == 0),
        "risk_flag": risk_flag,
    }
    return table, summary


def all_group_summaries(
    rows: list[dict[str, Any]],
    target_mode: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    group_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for risk_mode, hidden_keys in [
        ("strict_hidden", STRICT_HIDDEN_GROUP_KEYS),
        ("construction_hidden", CONSTRUCTION_HIDDEN_GROUP_KEYS),
    ]:
        for key in hidden_keys:
            table, summary = group_summary(rows, key, "hidden_post_label_audit", risk_mode, target_mode)
            group_rows.extend(table)
            summaries.append(summary)
    for key in VISIBLE_GROUP_KEYS:
        table, summary = group_summary(rows, key, "visible_label_surface", "visible", target_mode)
        group_rows.extend(table)
        summaries.append(summary)
    return group_rows, summaries


def risk_summaries(
    summaries: list[dict[str, Any]],
    risk_mode: str,
    source: str | None = None,
) -> list[dict[str, Any]]:
    output = []
    for summary in summaries:
        if summary["risk_mode"] != risk_mode:
            continue
        if source is not None and summary["source"] != source:
            continue
        if summary["risk_flag"]:
            output.append(summary)
    return sorted(
        output,
        key=lambda item: (
            -float(item["normalized_mutual_information"]),
            -float(item["majority_rule_accuracy"]),
            -float(item["positive_rate_range"]),
        ),
    )


def clone_for_slice(row: dict[str, Any], target_mode: str, spec: dict[str, Any]) -> dict[str, Any]:
    copied = deepcopy(row)
    copied["target_mode"] = target_mode
    copied["target_slice_reason"] = spec["reason"]
    copied["balanced_keys"] = spec["balanced_keys"]
    copied["audit_selection_only"] = True
    copied["paper_evidence_allowed"] = False
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
        count = min(len(positives), len(negatives))
        selected.extend(clone_for_slice(row, target_mode, spec) for row in positives[:count])
        selected.extend(clone_for_slice(row, target_mode, spec) for row in negatives[:count])

    return sorted(selected, key=stable_key)


def counts_for(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(target_y(row) for row in rows)
    return {
        "rows": len(rows),
        "positive": counts[1],
        "negative": counts[0],
        "by_family": dict(sorted(Counter(group_value(row, "predicate_family") for row in rows).items())),
        "by_predicate": dict(sorted(Counter(group_value(row, "predicate_label") for row in rows).items())),
        "by_rank_band": dict(sorted(Counter(group_value(row, "rank_band_hidden") for row in rows).items())),
        "by_role": dict(sorted(Counter(group_value(row, "proposed_audit_role_hidden") for row in rows).items())),
        "by_prior_relation_validity": dict(
            sorted(Counter(group_value(row, "relation_validity_label_hidden") for row in rows).items())
        ),
    }


def top_risk_rows(risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "group_key": item["group_key"],
            "majority_rule_accuracy": item["majority_rule_accuracy"],
            "normalized_mutual_information": item["normalized_mutual_information"],
            "positive_rate_range": item["positive_rate_range"],
        }
        for item in risks[:6]
    ]


def slice_summary(
    target_mode: str,
    spec: dict[str, Any],
    rows: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    path: Path,
) -> dict[str, Any]:
    counts = counts_for(rows)
    strict_hidden_risks = risk_summaries(summaries, "strict_hidden", "hidden_post_label_audit")
    construction_hidden_risks = risk_summaries(summaries, "construction_hidden", "hidden_post_label_audit")
    visible_risks = risk_summaries(summaries, "visible", "visible_label_surface")
    min_class = min(counts["positive"], counts["negative"]) if rows else 0
    size_ready = counts["rows"] >= MIN_CANDIDATE_ROWS and min_class >= MIN_CANDIDATE_PER_CLASS
    strict_candidate = size_ready and len(strict_hidden_risks) == 0
    construction_candidate = size_ready and len(construction_hidden_risks) == 0
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
        "size_ready": size_ready,
        "strict_hidden_risk_count": len(strict_hidden_risks),
        "construction_hidden_risk_count": len(construction_hidden_risks),
        "visible_risk_count": len(visible_risks),
        "strict_candidate": strict_candidate,
        "construction_only_candidate": construction_candidate and not strict_candidate,
        "construction_candidate": construction_candidate,
        "top_strict_hidden_risks": top_risk_rows(strict_hidden_risks),
        "top_construction_hidden_risks": top_risk_rows(construction_hidden_risks),
        "top_visible_risks": top_risk_rows(visible_risks),
        "counts": counts,
    }


def build_slices(
    rows: list[dict[str, Any]],
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    slice_dir = output_dir / "target_slices"
    slice_summaries: list[dict[str, Any]] = []
    group_table: list[dict[str, Any]] = []
    group_summary_rows: list[dict[str, Any]] = []
    for target_mode, spec in SLICE_SPECS.items():
        slice_rows = balanced_slice(rows, target_mode, spec)
        path = slice_dir / f"{target_mode}.jsonl"
        write_jsonl(path, slice_rows)
        groups, summaries = all_group_summaries(slice_rows, target_mode)
        group_table.extend(groups)
        group_summary_rows.extend(summaries)
        slice_summaries.append(slice_summary(target_mode, spec, slice_rows, summaries, path))
    return slice_summaries, group_table, group_summary_rows


def choose_candidate(slice_summaries: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    candidates = [item for item in slice_summaries if item[key]]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (item["priority"], -item["rows"], -item["min_class"]))[0]


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Support/Vertical Target Independence Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage target audit.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Hidden metadata is used only after label lock for audit and controlled-slice construction.",
        "- Strict mode includes prior bootstrap label carryover fields.",
        "- Construction-only mode excludes prior label carryover and checks queue/rank/role/geometry shortcuts.",
        "- Codex labels are not human-confirmed paper evidence.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "Decision:",
        "",
        summary["decision"],
        "",
        "## Original Strict Risks",
        "",
        "| Key | Majority Acc | NMI | Pos Rate Range |",
        "| --- | ---: | ---: | ---: |",
    ]
    for item in summary["original_strict_hidden_risks"]:
        lines.append(
            "| `{group_key}` | {majority_rule_accuracy:.4f} | "
            "{normalized_mutual_information:.4f} | {positive_rate_range:.4f} |".format(**item)
        )
    if not summary["original_strict_hidden_risks"]:
        lines.append("| none | 0.0000 | 0.0000 | 0.0000 |")

    lines.extend(
        [
            "",
            "## Controlled Slices",
            "",
            "| Target Slice | Rows | Pos | Neg | Strict Risks | Construction Risks | Strict Candidate | Construction Candidate |",
            "| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for item in sorted(
        summary["slice_summaries"],
        key=lambda row: (
            not row["strict_candidate"],
            not row["construction_candidate"],
            row["priority"],
            -row["rows"],
        ),
    ):
        lines.append(
            f"| `{item['target_mode']}` | {item['rows']} | {item['positive']} | {item['negative']} | "
            f"{item['strict_hidden_risk_count']} | {item['construction_hidden_risk_count']} | "
            f"`{item['strict_candidate']}` | `{item['construction_candidate']}` |"
        )

    lines.extend(["", "## Recommendation", ""])
    strict = summary.get("recommended_strict_slice")
    construction = summary.get("recommended_construction_slice")
    if strict:
        lines.append(f"Strict controlled slice: `{strict['target_mode']}`.")
    else:
        lines.append("No strict controlled slice satisfies size and hidden-risk criteria.")
    if construction:
        lines.extend(
            [
                "",
                f"Construction-only diagnostic slice: `{construction['target_mode']}`.",
                "",
                f"Rows: `{construction['rows']}`, positive: `{construction['positive']}`, negative: `{construction['negative']}`.",
                "",
                "This is useful for plumbing/error diagnostics only; it does not clear prior-label carryover.",
            ]
        )
    lines.extend(["", "## Next TODO", "", f"`{summary['next_todo']}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def validate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if row.get("predicate_family") not in {"support_contact", "relative_vertical"}:
            errors.append(
                {
                    "error_type": "row_outside_support_vertical_scope",
                    "row_number": index,
                    "blind_review_id": row.get("blind_review_id"),
                    "predicate_family": row.get("predicate_family"),
                }
            )
        if row.get("human_confirmed") is not False:
            errors.append(
                {
                    "error_type": "unexpected_human_confirmed_flag",
                    "row_number": index,
                    "blind_review_id": row.get("blind_review_id"),
                    "human_confirmed": row.get("human_confirmed"),
                }
            )
    return errors


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_rows = as_abs(args.input_rows)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    rows = read_jsonl(input_rows)
    validation_errors = validate_rows(rows)
    slice_summaries, group_table, group_summary_rows = build_slices(rows, output_dir)
    original_summary = next(item for item in slice_summaries if item["target_mode"] == "original_support_vertical_codex_ver")
    strict_candidate = choose_candidate(slice_summaries, "strict_candidate")
    construction_candidate = choose_candidate(slice_summaries, "construction_candidate")

    if validation_errors:
        status = "full_train_independent_support_vertical_target_independence_audit_errors"
        decision = "Fix row validation errors before using any controlled target slice."
        next_todo = "fix_full_train_independent_support_vertical_target_independence_audit_errors"
    elif strict_candidate:
        status = "full_train_independent_support_vertical_target_independence_audit_strict_slice_ready"
        decision = (
            "A strict controlled slice satisfies size and hidden-risk criteria. Posterior "
            "smoke may resume only on that slice as train-only diagnostics."
        )
        next_todo = "full_train_independent_support_vertical_controlled_posterior_smoke"
    elif construction_candidate:
        status = "full_train_independent_support_vertical_target_independence_audit_strict_blocked_construction_slice_available"
        decision = (
            "No strict controlled slice survives prior-label carryover risk. A construction-only "
            "slice remains for plumbing/error diagnostics, but posterior method claims remain "
            "blocked. Revise the label policy or add stronger independent/human audit before "
            "using this target for method validation."
        )
        next_todo = "full_train_independent_support_vertical_label_policy_revision"
    else:
        status = "full_train_independent_support_vertical_target_independence_audit_blocked"
        decision = (
            "The support/vertical target has hidden metadata shortcut risk and no controlled "
            "slice is large enough under strict or construction-only criteria."
        )
        next_todo = "revise_full_train_independent_support_vertical_target_or_collect_labels"

    summary_path = output_dir / "summary.json"
    report_path = output_dir / "report.md"
    slice_summary_path = output_dir / "slice_summaries.csv"
    group_summary_path = output_dir / "group_summaries.csv"
    group_table_path = output_dir / "group_table.csv"
    errors_path = output_dir / "validation_errors.jsonl"

    summary = {
        "schema_version": "h002_support_vertical_target_independence_audit_summary_v1",
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
            "validation_errors": rel_path(errors_path),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "selected_scope": ["relative_vertical", "support_contact"],
            "label_source": "codex_ver_support_vertical_visible_witness_bootstrap",
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "hidden_metadata_used_for_audit_only": True,
            "multi_view_as_model_input": False,
        },
        "risk_thresholds": {
            "normalized_mutual_information": RISK_NMI_THRESHOLD,
            "majority_rule_accuracy": RISK_MAJORITY_THRESHOLD,
            "positive_rate_range": RISK_POSITIVE_RATE_RANGE_THRESHOLD,
            "large_group_rows": RISK_LARGE_GROUP_ROWS,
            "large_group_purity": RISK_LARGE_GROUP_PURITY,
            "min_candidate_rows": MIN_CANDIDATE_ROWS,
            "min_candidate_per_class": MIN_CANDIDATE_PER_CLASS,
        },
        "counts": {
            "input_rows": len(rows),
            "positive": Counter(target_y(row) for row in rows)[1],
            "negative": Counter(target_y(row) for row in rows)[0],
            "validation_errors": len(validation_errors),
        },
        "strict_hidden_keys": STRICT_HIDDEN_GROUP_KEYS,
        "construction_hidden_keys": CONSTRUCTION_HIDDEN_GROUP_KEYS,
        "original_strict_hidden_risks": original_summary["top_strict_hidden_risks"],
        "original_construction_hidden_risks": original_summary["top_construction_hidden_risks"],
        "slice_summaries": slice_summaries,
        "recommended_strict_slice": strict_candidate,
        "recommended_construction_slice": construction_candidate,
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
                "strict_hidden_risk_count": item["strict_hidden_risk_count"],
                "construction_hidden_risk_count": item["construction_hidden_risk_count"],
                "visible_risk_count": item["visible_risk_count"],
                "size_ready": item["size_ready"],
                "strict_candidate": item["strict_candidate"],
                "construction_candidate": item["construction_candidate"],
                "balanced_keys": "|".join(item["balanced_keys"]),
                "path": item["path"],
            }
            for item in slice_summaries
        ],
    )
    write_csv(group_summary_path, group_summary_rows)
    write_csv(group_table_path, group_table)
    write_jsonl(errors_path, validation_errors)
    write_report(report_path, summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    construction = summary.get("recommended_construction_slice")
    strict = summary.get("recommended_strict_slice")
    print(
        f"status={summary['status']} rows={summary['counts']['input_rows']} "
        f"positive={summary['counts']['positive']} negative={summary['counts']['negative']} "
        f"errors={summary['counts']['validation_errors']} "
        f"strict={strict['target_mode'] if strict else 'none'} "
        f"construction={construction['target_mode'] if construction else 'none'} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
