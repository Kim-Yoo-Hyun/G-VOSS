#!/usr/bin/env python3
"""Ingest filled H002 p_obs / p_rel observability labels into model-safe views."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h002_pobs_prel_observability_ingestion_v1"
EXPECTED_FILL_STATUS = "h002_pobs_prel_observability_label_fill_ready"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--label-fill-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/pobs_prel_observability_labels/latest"),
    )
    parser.add_argument(
        "--source-materialization-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/pobs_prel_materialization/latest"),
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


def sanitize_qe(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out["schema_version"] = f"{SCHEMA_VERSION}_qe_view"
    out["feature_use_policy"] = {
        "allowed_blocks": ["Q_e"],
        "blocked_blocks": ["T_e", "G_e", "Z_e", "hidden_observability_labels"],
        "label_fields_excluded": True,
    }
    return out


def sanitize_prel(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out["schema_version"] = f"{SCHEMA_VERSION}_prel_view"
    out["feature_use_policy"] = {
        "allowed_blocks": sorted((row.get("feature_blocks") or {}).keys()),
        "blocked_blocks": ["hidden_observability_labels"],
        "label_fields_excluded": True,
    }
    return out


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root
    fill_dir = resolve(repo_root, args.label_fill_dir)
    source_dir = resolve(repo_root, args.source_materialization_dir)
    out = resolve(repo_root, args.out)
    out.mkdir(parents=True, exist_ok=True)

    validation_errors: list[dict[str, Any]] = []
    fill_summary = read_json(fill_dir / "summary.json")
    if fill_summary.get("status") != EXPECTED_FILL_STATUS:
        validation_errors.append({"error_type": "unexpected_fill_status", "actual": fill_summary.get("status")})
    if fill_summary.get("validation_errors") != 0:
        validation_errors.append({"error_type": "fill_validation_errors", "actual": fill_summary.get("validation_errors")})

    labels = read_jsonl(fill_dir / "filled_observability_labels.jsonl")
    qe_source = {
        row.get("candidate_id"): row
        for row in read_jsonl(source_dir / "model_safe_qe_view.jsonl")
        if row.get("control_type") == "observed_original"
    }
    prel_source = {
        row.get("candidate_id"): row
        for row in read_jsonl(source_dir / "model_safe_prel_view.jsonl")
        if row.get("control_type") == "observed_original"
    }

    qe_rows: list[dict[str, Any]] = []
    prel_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    missing_qe = 0
    missing_prel = 0

    for label in labels:
        candidate_id = label.get("candidate_id")
        qe = qe_source.get(candidate_id)
        prel = prel_source.get(candidate_id)
        if qe is None:
            missing_qe += 1
            continue
        if prel is None:
            missing_prel += 1
            continue
        qe_rows.append(sanitize_qe(qe))
        prel_rows.append(sanitize_prel(prel))
        hidden_rows.append(
            {
                "schema_version": f"{SCHEMA_VERSION}_hidden_labels",
                "candidate_id": candidate_id,
                "source_candidate_id": qe.get("source_candidate_id", candidate_id),
                "eval_split": qe.get("eval_split"),
                "route_family": label.get("route_family"),
                "predicate_label": label.get("predicate_label"),
                "queue_id": label.get("queue_id"),
                "queue_kind": label.get("queue_kind"),
                "observability_label": label.get("observability_label"),
                "obs_label": label.get("p_obs_target_after_audit"),
                "rel_label": label.get("p_rel_target_after_audit"),
                "decision_label": label.get("decision_label_after_audit"),
                "p_rel_target_allowed": label.get("p_rel_target_allowed"),
                "external_reviewer_id": label.get("external_reviewer_id"),
                "label_provenance": label.get("label_provenance"),
                "human_confirmed": label.get("human_confirmed"),
                "needs_user_review": label.get("needs_user_review"),
                "label_only": True,
                "target_policy": "codex-filled observability labels; model-safe views exclude labels",
            }
        )

    if missing_qe:
        validation_errors.append({"error_type": "missing_qe_source_rows", "count": missing_qe})
    if missing_prel:
        validation_errors.append({"error_type": "missing_prel_source_rows", "count": missing_prel})
    if not (len(qe_rows) == len(prel_rows) == len(hidden_rows) == len(labels)):
        validation_errors.append(
            {
                "error_type": "ingestion_row_count_mismatch",
                "labels": len(labels),
                "qe": len(qe_rows),
                "prel": len(prel_rows),
                "hidden": len(hidden_rows),
            }
        )

    label_counts = Counter(row["observability_label"] for row in hidden_rows)
    obs_counts = Counter(str(row["obs_label"]) for row in hidden_rows)
    decision_counts = Counter(str(row["decision_label"]) for row in hidden_rows)
    queue_counts = Counter(str(row["queue_kind"]) for row in hidden_rows)

    write_jsonl(out / "model_safe_qe_view.jsonl", qe_rows)
    write_jsonl(out / "model_safe_prel_view.jsonl", prel_rows)
    write_jsonl(out / "hidden_observability_labels.jsonl", hidden_rows)
    write_csv(
        out / "label_balance.csv",
        [
            {"field": "observability_label", "value": key, "rows": value}
            for key, value in sorted(label_counts.items())
        ]
        + [{"field": "obs_label", "value": key, "rows": value} for key, value in sorted(obs_counts.items())]
        + [{"field": "decision_label", "value": key, "rows": value} for key, value in sorted(decision_counts.items())]
        + [{"field": "queue_kind", "value": key, "rows": value} for key, value in sorted(queue_counts.items())],
        ["field", "value", "rows"],
    )
    write_jsonl(out / "validation_errors.jsonl", validation_errors)

    manifest = {
        "status": "h002_pobs_prel_observability_label_ingestion_ready",
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "validation_errors": len(validation_errors),
        "source_artifacts": {
            "label_fill": repo_rel(repo_root, fill_dir),
            "source_materialization": repo_rel(repo_root, source_dir),
        },
        "row_counts": {
            "labels": len(labels),
            "model_safe_qe_view": len(qe_rows),
            "model_safe_prel_view": len(prel_rows),
            "hidden_observability_labels": len(hidden_rows),
            "label_counts": dict(sorted(label_counts.items())),
            "obs_counts": dict(sorted(obs_counts.items())),
            "decision_counts": dict(sorted(decision_counts.items())),
        },
        "boundary": {
            "model_safe_views_exclude_labels": True,
            "hidden_labels_are_codex_filled": True,
            "human_confirmed": False,
            "metric_rerun_allowed_now": False,
        },
        "decision": {
            "selected_path": "ingest_codex_filled_observability_labels_for_schema_audit",
            "next_todo": "pobs_prel_observability_schema_audit",
        },
        "outputs": {
            "model_safe_qe_view": repo_rel(repo_root, out / "model_safe_qe_view.jsonl"),
            "model_safe_prel_view": repo_rel(repo_root, out / "model_safe_prel_view.jsonl"),
            "hidden_observability_labels": repo_rel(repo_root, out / "hidden_observability_labels.jsonl"),
            "label_balance": repo_rel(repo_root, out / "label_balance.csv"),
            "validation_errors": repo_rel(repo_root, out / "validation_errors.jsonl"),
            "manifest": repo_rel(repo_root, out / "ingestion_manifest.json"),
        },
    }
    write_json(out / "ingestion_manifest.json", manifest)
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
