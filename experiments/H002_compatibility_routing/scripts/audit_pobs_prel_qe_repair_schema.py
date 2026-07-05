#!/usr/bin/env python3
"""Audit repaired Q_e v2 schema for H002 p_obs / p_rel diagnostics."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h002_pobs_prel_qe_repair_schema_audit_v1"
STATUS_READY = "h002_pobs_prel_qe_repair_schema_audit_ready"
STATUS_ERROR = "h002_pobs_prel_qe_repair_schema_audit_errors"
EXPECTED_MATERIALIZATION_STATUS = "h002_pobs_prel_qe_repair_materialization_ready"
TRAIN_SPLIT = "internal_train"
EVAL_SPLIT = "official_validation_diagnostic_subset"

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
    "gt_exact_match",
    "h001_p_geom_valid",
    "p_geom_valid",
    "queue_kind",
    "repair_role",
    "codex_seed_hint_not_gt",
    "label_rationale",
    "hidden_selective_labels",
    "hidden_observability_labels",
    "hidden_observability_v2_labels",
}

REQUIRED_QE_BLOCKS = {
    "Q_e_asset_availability",
    "Q_e_visual_coverage",
    "Q_e_geometry_quality",
    "Q_e_ambiguity",
    "Q_e_state_v2",
    "Q_e_observability",
    "Q_e_safe",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--materialization-dir",
        type=Path,
        default=Path("experiments/H002_compatibility_routing/pobs_prel_qe_repair_materialization/latest"),
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


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
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


def feature_blocks(row: dict[str, Any]) -> dict[str, Any]:
    blocks = row.get("feature_blocks")
    return blocks if isinstance(blocks, dict) else {}


def q_block(row: dict[str, Any]) -> dict[str, Any]:
    block = feature_blocks(row).get("Q_e", {})
    return block if isinstance(block, dict) else {}


def qe_state(row: dict[str, Any]) -> str:
    state = q_block(row).get("Q_e_state_v2", {})
    if not isinstance(state, dict):
        return "missing_state_block"
    if state.get("q_e_state_sufficient_v2"):
        return "sufficient"
    if state.get("q_e_state_limited_v2"):
        return "limited"
    if state.get("q_e_state_ambiguous_v2"):
        return "ambiguous"
    if state.get("q_e_state_missing_v2"):
        return "missing"
    return "none"


def index_rows(rows: list[dict[str, Any]], view_name: str, errors: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    duplicates: Counter[str] = Counter()
    for row in rows:
        candidate_id = str(row.get("candidate_id"))
        duplicates[candidate_id] += 1
        out[candidate_id] = row
    for candidate_id, count in sorted(duplicates.items()):
        if count > 1:
            errors.append({"error_type": "duplicate_candidate_id", "view": view_name, "candidate_id": candidate_id, "count": count})
    return out


def blocked_hits(rows: list[dict[str, Any]], view_name: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row in rows:
        for flat_key in flatten_keys("", row):
            if flat_key.split(".")[-1] in BLOCKED_LEAF_KEYS:
                hits.append({"view": view_name, "candidate_id": row.get("candidate_id"), "blocked_key": flat_key})
    return hits


def block_audit(rows: list[dict[str, Any]], view_name: str, expected_mode: str) -> tuple[list[dict[str, Any]], Counter[str]]:
    audit_rows: list[dict[str, Any]] = []
    block_counts: Counter[str] = Counter()
    missing_required: Counter[str] = Counter()
    bad_qe_only = 0
    missing_qe = 0
    for row in rows:
        blocks = set(feature_blocks(row))
        for block in blocks:
            block_counts[block] += 1
        qe = q_block(row)
        if not qe:
            missing_qe += 1
        missing = REQUIRED_QE_BLOCKS.difference(qe)
        for block in missing:
            missing_required[block] += 1
        if expected_mode == "qe_only" and blocks != {"Q_e"}:
            bad_qe_only += 1
    audit_rows.append(
        {
            "view": view_name,
            "rows": len(rows),
            "feature_blocks": "|".join(sorted(block_counts)),
            "missing_qe_rows": missing_qe,
            "bad_qe_only_rows": bad_qe_only,
            "missing_required_qe_blocks": dict(sorted(missing_required.items())),
            "status": "pass" if missing_qe == 0 and bad_qe_only == 0 and not missing_required else "fail",
        }
    )
    return audit_rows, block_counts


def split_hidden(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        out[str(row.get("eval_split"))].append(row)
    return dict(out)


def row_alignment(
    split: str,
    qe_rows: list[dict[str, Any]],
    prel_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> dict[str, Any]:
    local_errors: list[dict[str, Any]] = []
    qe = index_rows(qe_rows, f"qe::{split}", local_errors)
    prel = index_rows(prel_rows, f"prel::{split}", local_errors)
    hidden = index_rows(hidden_rows, f"hidden::{split}", local_errors)
    qe_ids = set(qe)
    prel_ids = set(prel)
    hidden_ids = set(hidden)
    missing_in_prel = sorted(qe_ids - prel_ids)[:10]
    missing_in_qe = sorted(prel_ids - qe_ids)[:10]
    missing_hidden = sorted((qe_ids | prel_ids) - hidden_ids)[:10]
    extra_hidden = sorted(hidden_ids - (qe_ids | prel_ids))[:10]
    if local_errors:
        errors.extend(local_errors)
    if missing_in_prel or missing_in_qe or missing_hidden or extra_hidden:
        errors.append(
            {
                "error_type": "row_alignment_failed",
                "split": split,
                "missing_in_prel_sample": missing_in_prel,
                "missing_in_qe_sample": missing_in_qe,
                "missing_hidden_sample": missing_hidden,
                "extra_hidden_sample": extra_hidden,
            }
        )
    return {
        "split": split,
        "qe_rows": len(qe_rows),
        "prel_rows": len(prel_rows),
        "hidden_rows": len(hidden_rows),
        "qe_unique": len(qe_ids),
        "prel_unique": len(prel_ids),
        "hidden_unique": len(hidden_ids),
        "missing_in_prel": len(qe_ids - prel_ids),
        "missing_in_qe": len(prel_ids - qe_ids),
        "missing_hidden": len((qe_ids | prel_ids) - hidden_ids),
        "extra_hidden": len(hidden_ids - (qe_ids | prel_ids)),
        "status": "pass" if qe_ids == prel_ids == hidden_ids and not local_errors else "fail",
    }


def label_alignment(
    split: str,
    qe_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    qe = {str(row.get("candidate_id")): row for row in qe_rows}
    by_label: dict[str, Counter[str]] = defaultdict(Counter)
    mismatch_rows = 0
    for hidden in hidden_rows:
        candidate_id = str(hidden.get("candidate_id"))
        qrow = qe.get(candidate_id)
        if qrow is None:
            continue
        label = str(hidden.get("observability_label"))
        hidden_state = str(hidden.get("q_e_state_v2_hidden"))
        model_state = qe_state(qrow)
        by_label[label][model_state] += 1
        if hidden_state and hidden_state != model_state:
            mismatch_rows += 1
    if mismatch_rows:
        errors.append({"error_type": "qe_state_hidden_mismatch", "split": split, "rows": mismatch_rows})
    rows: list[dict[str, Any]] = []
    for label, counts in sorted(by_label.items()):
        rows.append(
            {
                "split": split,
                "observability_label": label,
                "rows": sum(counts.values()),
                "q_e_state_sufficient_v2": counts.get("sufficient", 0),
                "q_e_state_limited_v2": counts.get("limited", 0),
                "q_e_state_ambiguous_v2": counts.get("ambiguous", 0),
                "q_e_state_missing_v2": counts.get("missing", 0),
                "q_e_state_none": counts.get("none", 0),
            }
        )
    return rows


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    materialization_dir = resolve(repo_root, args.materialization_dir)
    out = resolve(repo_root, args.out)
    out.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    manifest = read_json(materialization_dir / "materialization_manifest.json")
    if manifest.get("status") != EXPECTED_MATERIALIZATION_STATUS:
        errors.append({"error_type": "unexpected_materialization_status", "actual": manifest.get("status")})
    if manifest.get("validation_errors") != 0:
        errors.append({"error_type": "materialization_validation_errors", "actual": manifest.get("validation_errors")})

    train_qe = read_jsonl(materialization_dir / "model_safe_qe_v2_train.jsonl")
    train_prel = read_jsonl(materialization_dir / "model_safe_prel_v2_train.jsonl")
    eval_qe = read_jsonl(materialization_dir / "model_safe_qe_v2_eval.jsonl")
    eval_prel = read_jsonl(materialization_dir / "model_safe_prel_v2_eval.jsonl")
    hidden_all = read_jsonl(materialization_dir / "hidden_observability_v2_labels.jsonl")
    hidden_by_split = split_hidden(hidden_all)
    train_hidden = hidden_by_split.get(TRAIN_SPLIT, [])
    eval_hidden = hidden_by_split.get(EVAL_SPLIT, [])

    blocked = (
        blocked_hits(train_qe, "model_safe_qe_v2_train")
        + blocked_hits(train_prel, "model_safe_prel_v2_train")
        + blocked_hits(eval_qe, "model_safe_qe_v2_eval")
        + blocked_hits(eval_prel, "model_safe_prel_v2_eval")
    )
    if blocked:
        errors.append({"error_type": "blocked_field_hits", "count": len(blocked)})

    row_alignment_rows = [
        row_alignment(TRAIN_SPLIT, train_qe, train_prel, train_hidden, errors),
        row_alignment(EVAL_SPLIT, eval_qe, eval_prel, eval_hidden, errors),
    ]

    block_rows: list[dict[str, Any]] = []
    for rows, view_name, mode in [
        (train_qe, "model_safe_qe_v2_train", "qe_only"),
        (eval_qe, "model_safe_qe_v2_eval", "qe_only"),
        (train_prel, "model_safe_prel_v2_train", "prel"),
        (eval_prel, "model_safe_prel_v2_eval", "prel"),
    ]:
        audit_rows, _ = block_audit(rows, view_name, mode)
        block_rows.extend(audit_rows)
    for row in block_rows:
        if row["status"] == "fail":
            errors.append({"error_type": "qe_block_audit_failed", **row})

    alignment_rows = label_alignment(TRAIN_SPLIT, train_qe, train_hidden, errors) + label_alignment(EVAL_SPLIT, eval_qe, eval_hidden, errors)
    train_counts = Counter(row.get("observability_label") for row in train_hidden)
    eval_counts = Counter(row.get("observability_label") for row in eval_hidden)
    if train_counts and len(set(train_counts.values())) != 1:
        errors.append({"error_type": "train_observability_balance_failed", "counts": dict(sorted(train_counts.items()))})
    eval_alignment = {row["observability_label"]: row for row in alignment_rows if row["split"] == EVAL_SPLIT}
    if eval_alignment.get("ambiguous_evidence", {}).get("q_e_state_sufficient_v2", 0) != 0:
        errors.append({"error_type": "ambiguous_eval_rows_still_sufficient"})
    if eval_alignment.get("unobservable_missing_evidence", {}).get("q_e_state_sufficient_v2", 0) != 0:
        errors.append({"error_type": "missing_eval_rows_still_sufficient"})

    schema_audit_rows = [
        {
            "check": "materialization_status",
            "status": "pass" if manifest.get("status") == EXPECTED_MATERIALIZATION_STATUS and manifest.get("validation_errors") == 0 else "fail",
            "detail": manifest.get("status"),
        },
        {
            "check": "blocked_field_hits",
            "status": "pass" if not blocked else "fail",
            "blocked_hit_count": len(blocked),
        },
        {
            "check": "train_row_alignment",
            "status": row_alignment_rows[0]["status"],
            "qe_rows": row_alignment_rows[0]["qe_rows"],
            "prel_rows": row_alignment_rows[0]["prel_rows"],
            "hidden_rows": row_alignment_rows[0]["hidden_rows"],
        },
        {
            "check": "eval_row_alignment",
            "status": row_alignment_rows[1]["status"],
            "qe_rows": row_alignment_rows[1]["qe_rows"],
            "prel_rows": row_alignment_rows[1]["prel_rows"],
            "hidden_rows": row_alignment_rows[1]["hidden_rows"],
        },
        {
            "check": "train_label_balance",
            "status": "pass" if train_counts and len(set(train_counts.values())) == 1 else "fail",
            "label_counts": dict(sorted(train_counts.items())),
        },
        {
            "check": "eval_ambiguous_missing_not_sufficient",
            "status": "pass"
            if eval_alignment.get("ambiguous_evidence", {}).get("q_e_state_sufficient_v2", 0) == 0
            and eval_alignment.get("unobservable_missing_evidence", {}).get("q_e_state_sufficient_v2", 0) == 0
            else "fail",
        },
    ]
    for row in schema_audit_rows:
        if row["status"] == "fail":
            errors.append({"error_type": row["check"], **row})

    label_balance_rows = (
        [{"split": "train", "field": "observability_label", "value": key, "rows": value} for key, value in sorted(train_counts.items())]
        + [{"split": "eval", "field": "observability_label", "value": key, "rows": value} for key, value in sorted(eval_counts.items())]
        + [
            {"split": "all", "field": "q_e_state_v2_hidden", "value": key, "rows": value}
            for key, value in sorted(Counter(row.get("q_e_state_v2_hidden") for row in hidden_all).items())
        ]
        + [
            {"split": "all", "field": "label_provenance", "value": key, "rows": value}
            for key, value in sorted(Counter(row.get("label_provenance") for row in hidden_all).items())
        ]
    )

    write_csv(out / "schema_separation_audit.csv", schema_audit_rows)
    write_csv(out / "row_alignment.csv", row_alignment_rows)
    write_csv(out / "qe_v2_block_audit.csv", block_rows)
    write_csv(out / "qe_v2_feature_label_alignment.csv", alignment_rows)
    write_csv(out / "label_balance.csv", label_balance_rows)
    write_jsonl(out / "blocked_field_hits.jsonl", blocked)
    write_jsonl(out / "validation_errors.jsonl", errors)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_ERROR if errors else STATUS_READY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "validation_errors": len(errors),
        "source_artifacts": {
            "materialization": repo_rel(repo_root, materialization_dir),
        },
        "counts": {
            "train_qe_rows": len(train_qe),
            "train_prel_rows": len(train_prel),
            "train_hidden_rows": len(train_hidden),
            "eval_qe_rows": len(eval_qe),
            "eval_prel_rows": len(eval_prel),
            "eval_hidden_rows": len(eval_hidden),
            "blocked_field_hits": len(blocked),
            "train_label_counts": dict(sorted(train_counts.items())),
            "eval_label_counts": dict(sorted(eval_counts.items())),
        },
        "gates": {
            "schema_separation": not blocked,
            "row_alignment": all(row["status"] == "pass" for row in row_alignment_rows),
            "qe_required_blocks": all(row["status"] == "pass" for row in block_rows),
            "train_label_balance": bool(train_counts and len(set(train_counts.values())) == 1),
            "eval_ambiguous_missing_not_sufficient": (
                eval_alignment.get("ambiguous_evidence", {}).get("q_e_state_sufficient_v2", 0) == 0
                and eval_alignment.get("unobservable_missing_evidence", {}).get("q_e_state_sufficient_v2", 0) == 0
            ),
        },
        "boundary": {
            "schema_audit_passed": len(errors) == 0,
            "pobs_only_diagnostic_metric_allowed": len(errors) == 0,
            "full_selective_decision_rerun_allowed": False,
            "paper_level_pobs_prel_solved_claim_allowed": False,
            "reason": "Q_e v2 labels are audit-proxy diagnostic and still require p_obs-only smoke before selective-decision rerun",
        },
        "decision": {
            "selected_path": "run_pobs_only_repair_smoke_before_full_selective_rerun" if len(errors) == 0 else "repair_schema_before_metric",
            "next_todo": "pobs_prel_qe_repair_pobs_only_metric" if len(errors) == 0 else "pobs_prel_qe_repair_schema_fix",
        },
        "outputs": {
            "schema_separation_audit": repo_rel(repo_root, out / "schema_separation_audit.csv"),
            "row_alignment": repo_rel(repo_root, out / "row_alignment.csv"),
            "qe_v2_block_audit": repo_rel(repo_root, out / "qe_v2_block_audit.csv"),
            "qe_v2_feature_label_alignment": repo_rel(repo_root, out / "qe_v2_feature_label_alignment.csv"),
            "label_balance": repo_rel(repo_root, out / "label_balance.csv"),
            "blocked_field_hits": repo_rel(repo_root, out / "blocked_field_hits.jsonl"),
            "validation_errors": repo_rel(repo_root, out / "validation_errors.jsonl"),
            "summary": repo_rel(repo_root, out / "summary.json"),
        },
    }
    write_json(out / "summary.json", summary)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
