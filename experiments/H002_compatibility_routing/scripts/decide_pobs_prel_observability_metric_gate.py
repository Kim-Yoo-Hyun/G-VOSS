#!/usr/bin/env python3
"""Allow H002 p_obs / p_rel observability metric rerun after user confirmation."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h002_pobs_prel_observability_metric_gate_v1"
STATUS_READY = "h002_pobs_prel_observability_metric_gate_ready"
STATUS_ERROR = "h002_pobs_prel_observability_metric_gate_errors"
EXPECTED_SCHEMA_STATUS = "h002_pobs_prel_observability_schema_audit_ready"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--schema-audit-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--user-confirmed-codex-labels",
        action="store_true",
        help="Record that the user reviewed and accepts the Codex-filled labels for diagnostic metric rerun.",
    )
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def repo_rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    schema_audit_dir = resolve(repo_root, args.schema_audit_dir)
    out = resolve(repo_root, args.out)
    out.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    schema = read_json(schema_audit_dir / "summary.json")
    if schema.get("status") != EXPECTED_SCHEMA_STATUS:
        errors.append({"error": "unexpected_schema_audit_status", "actual": schema.get("status")})
    if schema.get("validation_errors") != 0:
        errors.append({"error": "schema_audit_validation_errors", "actual": schema.get("validation_errors")})
    if schema.get("counts", {}).get("blocked_field_hits") != 0:
        errors.append({"error": "blocked_field_hits", "actual": schema.get("counts", {}).get("blocked_field_hits")})
    if not args.user_confirmed_codex_labels:
        errors.append({"error": "user_confirmation_missing"})

    metric_allowed = not errors and args.user_confirmed_codex_labels
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_ERROR if errors else STATUS_READY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_artifacts": {
            "schema_audit": repo_rel(repo_root, schema_audit_dir),
        },
        "counts": {
            "rows": schema.get("counts", {}).get("hidden_rows"),
            "blocked_field_hits": schema.get("counts", {}).get("blocked_field_hits"),
            "label_counts": schema.get("counts", {}).get("label_counts", {}),
            "decision_counts": schema.get("counts", {}).get("decision_counts", {}),
        },
        "boundary": {
            "codex_filled_labels": True,
            "user_review_completed": bool(args.user_confirmed_codex_labels),
            "treat_as_user_confirmed_for_diagnostic_metric": metric_allowed,
            "human_confirmed_in_raw_label_file": False,
            "paper_level_gt_claim_allowed": False,
            "metric_rerun_allowed_now": metric_allowed,
            "metric_scope": "diagnostic_observability_subset_rerun",
        },
        "decision": {
            "selected_path": "allow_diagnostic_metric_rerun_with_user_confirmed_codex_filled_labels"
            if metric_allowed
            else "keep_metric_rerun_blocked",
            "next_todo": "pobs_prel_observability_metric_rerun" if metric_allowed else "pobs_prel_observability_label_review",
        },
        "validation_errors": len(errors),
        "outputs": {
            "summary": repo_rel(repo_root, out / "summary.json"),
            "validation_errors": repo_rel(repo_root, out / "validation_errors.jsonl"),
        },
    }
    write_json(out / "summary.json", payload)
    write_jsonl(out / "validation_errors.jsonl", errors)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
