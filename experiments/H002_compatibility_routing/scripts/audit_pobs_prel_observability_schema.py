#!/usr/bin/env python3
"""Audit ingested H002 p_obs / p_rel observability label schema."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h002_pobs_prel_observability_schema_audit_v1"
EXPECTED_INGESTION_STATUS = "h002_pobs_prel_observability_label_ingestion_ready"
BLOCKED_LEAF_KEYS = {
    "observability_label",
    "obs_label",
    "rel_label",
    "decision_label",
    "p_obs_target_after_audit",
    "p_rel_target_after_audit",
    "label_status",
    "label_provenance",
    "external_reviewer_id",
    "target_y",
    "gt_match",
    "p_geom_valid",
    "hidden_observability_labels",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--ingestion-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/pobs_prel_observability_ingestion/latest"),
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


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


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


def flatten_keys(prefix: str, value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield from flatten_keys(f"{prefix}.{key}" if prefix else str(key), child)
    elif isinstance(value, list):
        yield prefix
    else:
        yield prefix


def audit_model_view(path: Path, view_name: str) -> tuple[int, Counter[str], Counter[str], list[dict[str, Any]]]:
    rows = 0
    block_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()
    blocked_hits: list[dict[str, Any]] = []
    for row in iter_jsonl(path):
        rows += 1
        split_counts[str(row.get("eval_split"))] += 1
        for block in (row.get("feature_blocks") or {}):
            block_counts[str(block)] += 1
        for flat_key in flatten_keys("", row):
            if flat_key.split(".")[-1] in BLOCKED_LEAF_KEYS:
                blocked_hits.append(
                    {
                        "view": view_name,
                        "candidate_id": row.get("candidate_id"),
                        "blocked_key": flat_key,
                    }
                )
    return rows, block_counts, split_counts, blocked_hits


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root
    ingestion_dir = resolve(repo_root, args.ingestion_dir)
    out = resolve(repo_root, args.out)
    out.mkdir(parents=True, exist_ok=True)

    validation_errors: list[dict[str, Any]] = []
    manifest = read_json(ingestion_dir / "ingestion_manifest.json")
    if manifest.get("status") != EXPECTED_INGESTION_STATUS:
        validation_errors.append({"error_type": "unexpected_ingestion_status", "actual": manifest.get("status")})
    if manifest.get("validation_errors") != 0:
        validation_errors.append({"error_type": "ingestion_validation_errors", "actual": manifest.get("validation_errors")})

    qe_rows, qe_blocks, qe_splits, qe_hits = audit_model_view(ingestion_dir / "model_safe_qe_view.jsonl", "model_safe_qe_view")
    prel_rows, prel_blocks, prel_splits, prel_hits = audit_model_view(ingestion_dir / "model_safe_prel_view.jsonl", "model_safe_prel_view")
    hidden_rows = list(iter_jsonl(ingestion_dir / "hidden_observability_labels.jsonl"))
    hidden_count = len(hidden_rows)

    blocked_hits = qe_hits + prel_hits
    if blocked_hits:
        validation_errors.append({"error_type": "blocked_field_hits", "count": len(blocked_hits)})
    if not (qe_rows == prel_rows == hidden_count):
        validation_errors.append(
            {
                "error_type": "row_count_mismatch",
                "qe_rows": qe_rows,
                "prel_rows": prel_rows,
                "hidden_rows": hidden_count,
            }
        )

    label_counts = Counter(row.get("observability_label") for row in hidden_rows)
    obs_counts = Counter(str(row.get("obs_label")) for row in hidden_rows)
    decision_counts = Counter(str(row.get("decision_label")) for row in hidden_rows)
    reviewer_counts = Counter(str(row.get("external_reviewer_id")) for row in hidden_rows)
    human_counts = Counter(str(row.get("human_confirmed")) for row in hidden_rows)

    audit_rows = [
        {
            "check": "row_count_alignment",
            "status": "pass" if qe_rows == prel_rows == hidden_count else "fail",
            "qe_rows": qe_rows,
            "prel_rows": prel_rows,
            "hidden_rows": hidden_count,
        },
        {
            "check": "blocked_field_hits",
            "status": "pass" if not blocked_hits else "fail",
            "blocked_hit_count": len(blocked_hits),
        },
        {
            "check": "qe_view_blocks",
            "status": "pass" if set(qe_blocks) == {"Q_e"} else "fail",
            "blocks": "|".join(sorted(qe_blocks)),
        },
        {
            "check": "prel_view_blocks",
            "status": "pass" if {"T_e", "G_e", "Q_e", "Z_e"}.issubset(set(prel_blocks)) else "fail",
            "blocks": "|".join(sorted(prel_blocks)),
        },
        {
            "check": "label_class_count",
            "status": "pass" if len(label_counts) >= 2 else "fail",
            "label_counts": dict(sorted(label_counts.items())),
        },
        {
            "check": "codex_provenance_explicit",
            "status": "pass" if reviewer_counts.get("codex_observability_label_fill_v1", 0) == hidden_count else "fail",
            "reviewer_counts": dict(sorted(reviewer_counts.items())),
        },
    ]
    for row in audit_rows:
        if row["status"] == "fail":
            validation_errors.append({"error_type": row["check"], **row})

    label_balance_rows = (
        [{"field": "observability_label", "value": key, "rows": value} for key, value in sorted(label_counts.items())]
        + [{"field": "obs_label", "value": key, "rows": value} for key, value in sorted(obs_counts.items())]
        + [{"field": "decision_label", "value": key, "rows": value} for key, value in sorted(decision_counts.items())]
        + [{"field": "external_reviewer_id", "value": key, "rows": value} for key, value in sorted(reviewer_counts.items())]
        + [{"field": "human_confirmed", "value": key, "rows": value} for key, value in sorted(human_counts.items())]
    )

    write_csv(
        out / "schema_separation_audit.csv",
        audit_rows,
        ["check", "status", "qe_rows", "prel_rows", "hidden_rows", "blocked_hit_count", "blocks", "label_counts", "reviewer_counts"],
    )
    write_csv(out / "label_balance.csv", label_balance_rows, ["field", "value", "rows"])
    write_jsonl(out / "blocked_field_hits.jsonl", blocked_hits)
    write_jsonl(out / "validation_errors.jsonl", validation_errors)
    summary = {
        "status": "h002_pobs_prel_observability_schema_audit_ready",
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "validation_errors": len(validation_errors),
        "source_artifacts": {
            "ingestion": repo_rel(repo_root, ingestion_dir),
        },
        "counts": {
            "qe_rows": qe_rows,
            "prel_rows": prel_rows,
            "hidden_rows": hidden_count,
            "blocked_field_hits": len(blocked_hits),
            "label_counts": dict(sorted(label_counts.items())),
            "obs_counts": dict(sorted(obs_counts.items())),
            "decision_counts": dict(sorted(decision_counts.items())),
            "human_confirmed_counts": dict(sorted(human_counts.items())),
        },
        "boundary": {
            "schema_audit_passed": len(validation_errors) == 0,
            "labels_are_codex_filled": True,
            "human_confirmed": False,
            "metric_rerun_allowed_now": False,
            "next_metric_gate_needed": True,
        },
        "decision": {
            "selected_path": "schema_passed_but_metric_gate_required_before_pobs_prel_rerun",
            "next_todo": "pobs_prel_observability_metric_gate_decision",
        },
        "outputs": {
            "schema_separation_audit": repo_rel(repo_root, out / "schema_separation_audit.csv"),
            "label_balance": repo_rel(repo_root, out / "label_balance.csv"),
            "blocked_field_hits": repo_rel(repo_root, out / "blocked_field_hits.jsonl"),
            "validation_errors": repo_rel(repo_root, out / "validation_errors.jsonl"),
            "summary": repo_rel(repo_root, out / "summary.json"),
        },
    }
    write_json(out / "summary.json", summary)
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
