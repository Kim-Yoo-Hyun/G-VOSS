#!/usr/bin/env python3
"""Fill H002 p_obs / p_rel observability audit labels with Codex provenance."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h002_pobs_prel_observability_label_fill_v1"
EXPECTED_REPAIR_STATUS = "h002_pobs_prel_observability_repair_ready"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--repair-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/pobs_prel_observability_repair/latest"),
    )
    parser.add_argument(
        "--source-hidden-labels",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/pobs_prel_materialization/latest/hidden_selective_labels.jsonl"),
    )
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def repo_rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def decide_observability_label(row: dict[str, Any]) -> tuple[str, str, str]:
    queue_kind = row.get("queue_kind", "")
    seed = row.get("codex_seed_hint_not_gt", "")
    predicate = row.get("predicate_label", "")

    if queue_kind in {"route_observable_control", "support_contact_binary_control"}:
        return (
            "observable_clear",
            "high",
            "control rows are intended to confirm that evidence is sufficient for accept/reject decisions",
        )
    if "weak_support_evidence" in seed:
        return (
            "unobservable_missing_evidence",
            "medium",
            "support evidence proxy is weak, so visual/mesh evidence is treated as insufficient",
        )
    if "ambiguous_pose" in seed:
        return (
            "ambiguous_evidence",
            "medium",
            "pose proxy is explicitly ambiguous for the support/contact subtype",
        )
    if queue_kind == "support_contact_single_subtype_abstain":
        return (
            "ambiguous_evidence",
            "medium",
            "single-subtype class-pair lacks controlled subtype contrast; class-pair semantics confound the visual decision",
        )
    if queue_kind == "support_contact_mixed_overflow_abstain":
        if "horizontal_like" in seed or "upright_like" in seed:
            return (
                "observable_clear",
                "medium",
                f"mixed-class-pair overflow has controlled class-pair context and a {seed.rsplit(':', 1)[-1]} pose proxy",
            )
        return (
            "ambiguous_evidence",
            "medium",
            f"mixed overflow row for predicate {predicate} lacks a clear enough pose proxy",
        )
    return (
        "ambiguous_evidence",
        "low",
        "fallback: queue row is not covered by a high-confidence fill rule",
    )


def obs_target(label: str) -> int:
    return 1 if label == "observable_clear" else 0


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root
    repair_dir = resolve(repo_root, args.repair_dir)
    source_hidden_path = resolve(repo_root, args.source_hidden_labels)
    out = resolve(repo_root, args.out)
    out.mkdir(parents=True, exist_ok=True)

    validation_errors: list[dict[str, Any]] = []
    repair_summary = read_json(repair_dir / "summary.json")
    queue_rows = read_jsonl(repair_dir / "observability_label_queue.jsonl")
    source_hidden_rows = read_jsonl(source_hidden_path)
    source_hidden_by_id = {
        row.get("candidate_id"): row
        for row in source_hidden_rows
        if row.get("control_type") == "observed_original"
    }

    if repair_summary.get("status") != EXPECTED_REPAIR_STATUS:
        validation_errors.append({"error_type": "unexpected_repair_status", "actual": repair_summary.get("status")})
    if repair_summary.get("validation_errors") != 0:
        validation_errors.append({"error_type": "repair_validation_errors", "actual": repair_summary.get("validation_errors")})
    if not queue_rows:
        validation_errors.append({"error_type": "empty_queue"})

    filled: list[dict[str, Any]] = []
    for row in queue_rows:
        label, confidence, rationale = decide_observability_label(row)
        source_hidden = source_hidden_by_id.get(row.get("candidate_id"), {})
        p_obs_target = obs_target(label)
        p_rel_allowed = label == "observable_clear"
        rel_label = source_hidden.get("rel_label") if p_rel_allowed else None
        if p_rel_allowed and rel_label is None:
            decision_label = "observable_without_relation_label"
        elif not p_rel_allowed:
            decision_label = "abstain"
        else:
            decision_label = "accept" if int(rel_label) == 1 else "reject"
        filled.append(
            {
                **row,
                "schema_version": SCHEMA_VERSION,
                "label_status": "filled",
                "observability_label": label,
                "p_obs_target_after_audit": p_obs_target,
                "p_rel_target_allowed": p_rel_allowed,
                "p_rel_target_after_audit": rel_label,
                "decision_label_after_audit": decision_label,
                "external_reviewer_id": "codex_observability_label_fill_v1",
                "label_provenance": "codex_rule_fill_from_queue_role_pose_proxy_and_existing_hidden_label",
                "label_confidence": confidence,
                "label_rationale": rationale,
                "human_confirmed": False,
                "needs_user_review": True,
            }
        )

    label_counts = Counter(row["observability_label"] for row in filled)
    queue_counts = Counter(row["queue_kind"] for row in filled)
    decision_counts = Counter(row["decision_label_after_audit"] for row in filled)
    rel_missing = sum(
        1
        for row in filled
        if row["p_rel_target_allowed"] and row["p_rel_target_after_audit"] is None
    )
    if rel_missing:
        validation_errors.append({"error_type": "observable_rows_missing_rel_label", "count": rel_missing})
    if len(label_counts) < 2:
        validation_errors.append({"error_type": "observability_labels_single_class", "label_counts": dict(label_counts)})
    if len(filled) != len(queue_rows):
        validation_errors.append({"error_type": "filled_queue_count_mismatch", "filled": len(filled), "queue": len(queue_rows)})

    summary_rows = [
        {
            "field": "observability_label",
            "value": key,
            "rows": value,
        }
        for key, value in sorted(label_counts.items())
    ] + [
        {
            "field": "queue_kind",
            "value": key,
            "rows": value,
        }
        for key, value in sorted(queue_counts.items())
    ] + [
        {
            "field": "decision_label_after_audit",
            "value": key,
            "rows": value,
        }
        for key, value in sorted(decision_counts.items())
    ]

    write_jsonl(out / "filled_observability_labels.jsonl", filled)
    write_csv(out / "label_summary.csv", summary_rows, ["field", "value", "rows"])
    write_jsonl(out / "validation_errors.jsonl", validation_errors)
    summary = {
        "status": "h002_pobs_prel_observability_label_fill_ready",
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "validation_errors": len(validation_errors),
        "source_artifacts": {
            "observability_repair": repo_rel(repo_root, repair_dir),
            "source_hidden_labels": repo_rel(repo_root, source_hidden_path),
        },
        "row_counts": {
            "queue_rows": len(queue_rows),
            "filled_rows": len(filled),
            "label_counts": dict(sorted(label_counts.items())),
            "queue_counts": dict(sorted(queue_counts.items())),
            "decision_counts": dict(sorted(decision_counts.items())),
        },
        "boundary": {
            "label_source": "codex_filled_not_human_confirmed",
            "human_confirmed": False,
            "metric_rerun_allowed_now": False,
            "ingestion_allowed": len(validation_errors) == 0,
        },
        "decision": {
            "selected_path": "codex_filled_observability_labels_then_ingestion_schema_audit",
            "next_todo": "pobs_prel_observability_label_ingestion",
        },
        "output_artifacts": {
            "filled_observability_labels": repo_rel(repo_root, out / "filled_observability_labels.jsonl"),
            "label_summary": repo_rel(repo_root, out / "label_summary.csv"),
            "validation_errors": repo_rel(repo_root, out / "validation_errors.jsonl"),
            "summary": repo_rel(repo_root, out / "summary.json"),
        },
    }
    write_json(out / "summary.json", summary)
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
