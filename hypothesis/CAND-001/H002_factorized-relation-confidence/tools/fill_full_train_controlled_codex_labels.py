#!/usr/bin/env python3
"""Fill full-train H002 controlled sheet with marked Codex bootstrap labels."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
MINING_ROOT = (
    H002_ROOT
    / "artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_mining"
)
DEFAULT_INPUT_SHEET = MINING_ROOT / "candidate_sheet.tsv"
DEFAULT_OUTPUT_SHEET = MINING_ROOT / "candidate_sheet_codex_ver.tsv"
DEFAULT_OUTPUT_DIR = (
    H002_ROOT
    / "artifacts/train_rga_full/open3dsg_train_full/rga/controlled_label_fill_codex_ver"
)

REVIEWER_ID = "(codex_ver_full_train)"
REVIEW_ROUND = "1"

HL_NEGATIVE_ROLES = {
    "hl_exact_label_geometry_contradiction",
    "hl_family_match_geometry_contradiction",
    "hl_wrong_predicate_geometry_contradiction",
    "hl_no_gt_geometry_contradiction",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-sheet", type=Path, default=DEFAULT_INPUT_SHEET)
    parser.add_argument("--output-sheet", type=Path, default=DEFAULT_OUTPUT_SHEET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"{path}: missing TSV header")
        return list(reader.fieldnames), [dict(row) for row in reader]


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path = as_abs(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path = as_abs(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path = as_abs(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def safe_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def binary_target_for(final_label: str) -> int | None:
    if final_label == "reliable_promote":
        return 1
    if final_label == "unreliable_dense_noise":
        return 0
    return None


def assign_bootstrap_label(row: dict[str, str]) -> dict[str, str]:
    role = row["proposed_audit_role"]
    label_status = row["label_match_status"]
    family = row["predicate_family"]

    if role in HL_NEGATIVE_ROLES:
        return {
            "object_pair_valid": "uncertain" if label_status == "no_gt_for_pair" else "yes",
            "predicate_visually_plausible": "no",
            "geometry_witness_correct": "yes",
            "relation_informative": "no",
            "relation_trivial_or_dense": "no",
            "annotation_missing_or_sparse": "yes" if label_status == "no_gt_for_pair" else "no",
            "ontology_or_granularity_issue": "yes"
            if label_status in {"family_match", "pair_has_other_predicate"}
            else "no",
            "segmentation_or_instance_issue": "uncertain",
            "final_controlled_label": "unreliable_dense_noise",
            "failure_taxonomy_label": "semantic_overconfidence_invalid",
            "confidence": "medium",
            "policy_reason": (
                "high-semantic relation is geometry-unsatisfied; used as a "
                "bootstrap unreliable binary target"
            ),
        }

    if role == "lh_exact_label_underconfidence":
        return {
            "object_pair_valid": "yes",
            "predicate_visually_plausible": "yes",
            "geometry_witness_correct": "yes",
            "relation_informative": "yes",
            "relation_trivial_or_dense": "no" if family != "proximity" else "uncertain",
            "annotation_missing_or_sparse": "no",
            "ontology_or_granularity_issue": "no",
            "segmentation_or_instance_issue": "uncertain",
            "final_controlled_label": "reliable_promote",
            "failure_taxonomy_label": "true_underconfidence",
            "confidence": "high",
            "policy_reason": (
                "low-semantic row has exact train label and geometry-satisfied "
                "evidence; used as bootstrap reliable binary target"
            ),
        }

    if role == "lh_no_gt_proximity_dense_or_sparse":
        return {
            "object_pair_valid": "uncertain",
            "predicate_visually_plausible": "yes",
            "geometry_witness_correct": "yes",
            "relation_informative": "no",
            "relation_trivial_or_dense": "yes",
            "annotation_missing_or_sparse": "uncertain",
            "ontology_or_granularity_issue": "no",
            "segmentation_or_instance_issue": "uncertain",
            "final_controlled_label": "unreliable_dense_noise",
            "failure_taxonomy_label": "dense_relation_noise",
            "confidence": "medium",
            "policy_reason": (
                "no-GT proximity is geometry-satisfied but likely dense or "
                "uninformative; used as bootstrap unreliable binary target"
            ),
        }

    if role == "lh_family_match_granularity":
        return {
            "object_pair_valid": "yes",
            "predicate_visually_plausible": "yes",
            "geometry_witness_correct": "yes",
            "relation_informative": "yes",
            "relation_trivial_or_dense": "no",
            "annotation_missing_or_sparse": "yes",
            "ontology_or_granularity_issue": "yes",
            "segmentation_or_instance_issue": "uncertain",
            "final_controlled_label": "relabel_only",
            "failure_taxonomy_label": "ontology_or_granularity_issue",
            "confidence": "medium",
            "policy_reason": (
                "same-family label support indicates predicate granularity rather "
                "than a clean binary reliability target"
            ),
        }

    if role == "lh_alternative_relation_on_gt_pair":
        return {
            "object_pair_valid": "yes",
            "predicate_visually_plausible": "yes",
            "geometry_witness_correct": "yes",
            "relation_informative": "uncertain",
            "relation_trivial_or_dense": "uncertain",
            "annotation_missing_or_sparse": "yes",
            "ontology_or_granularity_issue": "yes",
            "segmentation_or_instance_issue": "uncertain",
            "final_controlled_label": "relabel_only",
            "failure_taxonomy_label": "ontology_or_granularity_issue",
            "confidence": "medium",
            "policy_reason": (
                "object pair has another GT predicate; keep as relabel-only "
                "instead of binary reliability supervision"
            ),
        }

    if role in {
        "lh_no_gt_support_contact_missing_or_noise",
        "lh_no_gt_vertical_sparse_or_trivial",
    }:
        return {
            "object_pair_valid": "uncertain",
            "predicate_visually_plausible": "uncertain",
            "geometry_witness_correct": "yes",
            "relation_informative": "uncertain",
            "relation_trivial_or_dense": "uncertain",
            "annotation_missing_or_sparse": "uncertain",
            "ontology_or_granularity_issue": "uncertain",
            "segmentation_or_instance_issue": "uncertain",
            "final_controlled_label": "abstain_uncertain",
            "failure_taxonomy_label": "uncertain_needs_visual_or_mesh",
            "confidence": "low",
            "policy_reason": (
                "no-GT support/vertical relation needs visual or mesh confirmation; "
                "excluded from bootstrap binary target"
            ),
        }

    raise ValueError(f"unsupported proposed_audit_role: {role}")


def label_record(row: dict[str, str], fields: dict[str, str]) -> dict[str, Any]:
    target = binary_target_for(fields["final_controlled_label"])
    return {
        "schema_version": "h002_full_train_controlled_codex_label_v0",
        "label_source": "codex_ver_full_train_policy_bootstrap",
        "not_human_confirmed": True,
        "paper_evidence_allowed": False,
        "posterior_claim_allowed": False,
        "reviewer_id": REVIEWER_ID,
        "review_round": int(REVIEW_ROUND),
        "review_id": row["review_id"],
        "prediction_id": row["prediction_id"],
        "scan_id": row["scan_id"],
        "subgraph_id": row["subgraph_id"],
        "subject_id": row["subject_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "object_id": row["object_id"],
        "object_label": row["object_label"],
        "queue_kind": row["queue_kind"],
        "rank_band": row["rank_band"],
        "semantic_rank": int(row["semantic_rank"]),
        "semantic_score_norm": safe_float(row["semantic_score_norm"]),
        "geometry_status": row["geometry_status"],
        "p_geom_valid": safe_float(row["p_geom_valid"]),
        "label_match_status": row["label_match_status"],
        "proposed_audit_role": row["proposed_audit_role"],
        "final_controlled_label": fields["final_controlled_label"],
        "failure_taxonomy_label": fields["failure_taxonomy_label"],
        "posterior_target": target,
        "binary_usable": target is not None,
        "confidence": fields["confidence"],
        "policy_reason": fields["policy_reason"],
    }


def fill_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    filled_rows = []
    labels = []
    for row in rows:
        fields = assign_bootstrap_label(row)
        filled = dict(row)
        notes = (
            "codex_ver_full_train bootstrap label; not human-confirmed; "
            f"role={row['proposed_audit_role']}; queue={row['queue_kind']}; "
            f"label_status={row['label_match_status']}; "
            f"geometry_status={row['geometry_status']}; policy={fields['policy_reason']}"
        )
        filled.update(
            {
                "reviewer_id": REVIEWER_ID,
                "review_round": REVIEW_ROUND,
                **{key: value for key, value in fields.items() if key != "policy_reason"},
                "notes": notes,
            }
        )
        filled_rows.append(filled)
        labels.append(label_record(row, fields))
    return filled_rows, labels


def summarize(labels: list[dict[str, Any]]) -> dict[str, Any]:
    final_counts = Counter(row["final_controlled_label"] for row in labels)
    taxonomy_counts = Counter(row["failure_taxonomy_label"] for row in labels)
    target_counts = Counter(str(row["posterior_target"]) for row in labels if row["binary_usable"])
    by_queue = Counter((row["queue_kind"], str(row["posterior_target"])) for row in labels if row["binary_usable"])
    by_family = Counter((row["predicate_family"], str(row["posterior_target"])) for row in labels if row["binary_usable"])
    by_role = Counter((row["proposed_audit_role"], str(row["posterior_target"])) for row in labels if row["binary_usable"])
    by_rank = Counter((row["rank_band"], str(row["posterior_target"])) for row in labels if row["binary_usable"])
    family_minority = {}
    target_by_family = defaultdict(Counter)
    for row in labels:
        if row["binary_usable"]:
            target_by_family[row["predicate_family"]][str(row["posterior_target"])] += 1
    for family, counts in target_by_family.items():
        family_minority[family] = min(counts.get("0", 0), counts.get("1", 0))
    return {
        "rows": len(labels),
        "binary_usable_rows": sum(1 for row in labels if row["binary_usable"]),
        "positive_rows": target_counts.get("1", 0),
        "negative_rows": target_counts.get("0", 0),
        "excluded_rows": sum(1 for row in labels if not row["binary_usable"]),
        "final_label_counts": dict(sorted(final_counts.items())),
        "failure_taxonomy_counts": dict(sorted(taxonomy_counts.items())),
        "posterior_target_counts": dict(sorted(target_counts.items())),
        "target_by_queue": {str(key): value for key, value in sorted(by_queue.items())},
        "target_by_family": {str(key): value for key, value in sorted(by_family.items())},
        "target_by_rank_band": {str(key): value for key, value in sorted(by_rank.items())},
        "target_by_role": {str(key): value for key, value in sorted(by_role.items())},
        "family_binary_minority_counts": dict(sorted(family_minority.items())),
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 Full Train Controlled Codex Labels",
        "",
        f"Created: {summary['created_at']}",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Boundary",
        "",
        "- Labels are `(codex_ver_full_train)` bootstrap labels.",
        "- The original blank candidate sheet is preserved.",
        "- Validation/test rows are not used.",
        "- Labels are not human-confirmed and are not paper evidence.",
        "- Proposed audit role is used only for bootstrap hypothesis-stage fill.",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| rows | {counts['rows']} |",
        f"| binary usable rows | {counts['binary_usable_rows']} |",
        f"| positive rows | {counts['positive_rows']} |",
        f"| negative rows | {counts['negative_rows']} |",
        f"| excluded rows | {counts['excluded_rows']} |",
        "",
        "## Final Labels",
        "",
        "| Label | Rows |",
        "| --- | ---: |",
    ]
    for label, count in counts["final_label_counts"].items():
        lines.append(f"| `{label}` | {count} |")
    lines.extend(
        [
            "",
            "## Binary Policy",
            "",
            "| Source | Final label | Target |",
            "| --- | --- | ---: |",
            "| `HL` geometry contradiction roles | `unreliable_dense_noise` | 0 |",
            "| `LH exact_match` | `reliable_promote` | 1 |",
            "| `LH no-GT proximity` | `unreliable_dense_noise` | 0 |",
            "| family/pair granularity | `relabel_only` | excluded |",
            "| no-GT support/vertical | `abstain_uncertain` | excluded |",
            "",
        ]
    )
    as_abs(path).write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fieldnames, rows = read_tsv(args.input_sheet)
    filled_rows, labels = fill_rows(rows)
    labels_path = output_dir / "labels.jsonl"
    summary_path = output_dir / "summary.json"
    report_path = output_dir / "report.md"
    write_tsv(args.output_sheet, fieldnames, filled_rows)
    write_jsonl(labels_path, labels)
    counts = summarize(labels)
    created_at = datetime.now(timezone.utc).isoformat()
    summary = {
        "schema_version": "h002_full_train_controlled_codex_fill_summary_v0",
        "status": "full_train_controlled_codex_labels_filled_not_human_confirmed",
        "created_at": created_at,
        "input_sheet": rel_path(args.input_sheet),
        "output_sheet": rel_path(args.output_sheet),
        "output_paths": {
            "labels": rel_path(labels_path),
            "summary": rel_path(summary_path),
            "report": rel_path(report_path),
        },
        "counts": counts,
        "boundary": {
            "split": "train_full_only",
            "validation_usage": False,
            "test_usage": False,
            "label_source": "codex_ver_full_train_policy_bootstrap",
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "vmv_model_input_allowed": False,
        },
        "binary_policy": {
            "hl_geometry_contradiction_roles": "unreliable_dense_noise -> 0",
            "lh_exact_label_underconfidence": "reliable_promote -> 1",
            "lh_no_gt_proximity_dense_or_sparse": "unreliable_dense_noise -> 0",
            "lh_family_match_granularity": "relabel_only -> excluded",
            "lh_alternative_relation_on_gt_pair": "relabel_only -> excluded",
            "lh_no_gt_support_or_vertical": "abstain_uncertain -> excluded",
        },
    }
    write_json(summary_path, summary)
    write_report(report_path, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    counts = summary["counts"]
    print(
        "status={status} rows={rows} binary={binary} positive={positive} "
        "negative={negative} excluded={excluded} validation_used={validation_used}".format(
            status=summary["status"],
            rows=counts["rows"],
            binary=counts["binary_usable_rows"],
            positive=counts["positive_rows"],
            negative=counts["negative_rows"],
            excluded=counts["excluded_rows"],
            validation_used=summary["boundary"]["validation_usage"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
