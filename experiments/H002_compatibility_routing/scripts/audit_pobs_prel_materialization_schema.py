#!/usr/bin/env python3
"""Audit H002 p_obs / p_rel selective materialization schema."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h002_pobs_prel_schema_audit_v1"
STATUS_READY = "h002_pobs_prel_schema_audit_ready"
STATUS_ERROR = "h002_pobs_prel_schema_audit_errors"
EXPECTED_MATERIALIZATION_STATUS = "h002_pobs_prel_selective_materialization_ready"
BLOCKED_MODEL_SAFE_KEYS = {
    "obs_label",
    "rel_label",
    "decision_label",
    "target_y",
    "gt_exact_match",
    "gt_match",
    "h001_p_geom_valid",
    "p_geom_valid",
    "verification_status",
    "hidden_selective_labels",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--materialization-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


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


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def flatten_keys(prefix: str, value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield from flatten_keys(f"{prefix}.{key}" if prefix else str(key), child)
    else:
        yield prefix


def audit_view(path: Path, view_name: str) -> tuple[int, list[dict[str, Any]], Counter[str], Counter[str]]:
    blocked_hits: list[dict[str, Any]] = []
    block_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()
    count = 0
    for row in iter_jsonl(path):
        count += 1
        split_counts[str(row.get("eval_split"))] += 1
        for block in (row.get("feature_blocks") or {}):
            block_counts[str(block)] += 1
        for flat_key in flatten_keys("", row):
            leaf = flat_key.split(".")[-1]
            if leaf in BLOCKED_MODEL_SAFE_KEYS:
                blocked_hits.append({
                    "view": view_name,
                    "candidate_id": row.get("candidate_id"),
                    "blocked_key": flat_key,
                })
    return count, blocked_hits, block_counts, split_counts


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    materialization_dir = args.materialization_dir if args.materialization_dir.is_absolute() else repo_root / args.materialization_dir
    out = args.out if args.out.is_absolute() else repo_root / args.out
    out.mkdir(parents=True, exist_ok=True)

    manifest = read_json(materialization_dir / "materialization_manifest.json")
    errors: list[dict[str, Any]] = []
    if manifest.get("status") != EXPECTED_MATERIALIZATION_STATUS:
        errors.append({"error": "unexpected_materialization_status", "observed": manifest.get("status")})

    qe_count, qe_hits, qe_blocks, qe_splits = audit_view(materialization_dir / "model_safe_qe_view.jsonl", "model_safe_qe_view")
    prel_count, prel_hits, prel_blocks, prel_splits = audit_view(materialization_dir / "model_safe_prel_view.jsonl", "model_safe_prel_view")
    hidden_rows = list(iter_jsonl(materialization_dir / "hidden_selective_labels.jsonl"))
    hidden_count = len(hidden_rows)

    if not (qe_count == prel_count == hidden_count):
        errors.append({"error": "view_count_mismatch", "qe": qe_count, "prel": prel_count, "hidden": hidden_count})

    blocked_hits = qe_hits + prel_hits
    label_counts = Counter(row.get("decision_label") for row in hidden_rows)
    obs_counts = Counter(str(row.get("obs_label")) for row in hidden_rows)
    rel_counts = Counter(str(row.get("rel_label")) for row in hidden_rows if row.get("rel_label") is not None)
    control_counts = Counter(row.get("control_type") for row in hidden_rows)
    split_counts = Counter(row.get("eval_split") for row in hidden_rows)

    audit_rows = [
        {
            "check": "view_count_alignment",
            "status": "pass" if qe_count == prel_count == hidden_count else "fail",
            "qe_rows": qe_count,
            "prel_rows": prel_count,
            "hidden_rows": hidden_count,
        },
        {
            "check": "blocked_field_hits",
            "status": "pass" if len(blocked_hits) == 0 else "fail",
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
    ]
    for row in audit_rows:
        if row["status"] == "fail":
            errors.append({"error": row["check"], **row})

    write_csv(out / "schema_separation_audit.csv", audit_rows)
    write_csv(
        out / "label_balance.csv",
        [
            {"label_type": "decision_label", "label": key, "count": value}
            for key, value in sorted(label_counts.items())
        ]
        + [{"label_type": "obs_label", "label": key, "count": value} for key, value in sorted(obs_counts.items())]
        + [{"label_type": "rel_label", "label": key, "count": value} for key, value in sorted(rel_counts.items())]
        + [{"label_type": "control_type", "label": key, "count": value} for key, value in sorted(control_counts.items())]
        + [{"label_type": "eval_split", "label": key, "count": value} for key, value in sorted(split_counts.items())],
    )
    write_jsonl(out / "blocked_field_hits.jsonl", blocked_hits)
    write_jsonl(out / "validation_errors.jsonl", errors)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_ERROR if errors else STATUS_READY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "materialization_dir": rel_path(repo_root, materialization_dir),
        "outputs": {
            "schema_separation_audit": rel_path(repo_root, out / "schema_separation_audit.csv"),
            "label_balance": rel_path(repo_root, out / "label_balance.csv"),
            "blocked_field_hits": rel_path(repo_root, out / "blocked_field_hits.jsonl"),
            "validation_errors": rel_path(repo_root, out / "validation_errors.jsonl"),
        },
        "counts": {
            "qe_rows": qe_count,
            "prel_rows": prel_count,
            "hidden_rows": hidden_count,
            "blocked_field_hits": len(blocked_hits),
            "qe_splits": dict(sorted(qe_splits.items())),
            "prel_splits": dict(sorted(prel_splits.items())),
        },
        "next_todo": "compatibility_dataset_v3_pobs_prel_metric_runner_after_schema_audit",
        "validation_errors": len(errors),
    }
    write_json(out / "summary.json", summary)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
