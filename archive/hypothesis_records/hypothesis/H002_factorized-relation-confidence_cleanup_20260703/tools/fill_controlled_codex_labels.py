#!/usr/bin/env python3
"""Fill H002 controlled review sheets with clearly marked Codex bootstrap labels."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_TARGET_DIR = RGA_ROOT / "controlled_label_target"
DEFAULT_INPUT_MINED = DEFAULT_TARGET_DIR / "mined_controlled_sheet.tsv"
DEFAULT_INPUT_COMBINED = DEFAULT_TARGET_DIR / "combined_review_sheet.tsv"
DEFAULT_OUTPUT_MINED = DEFAULT_TARGET_DIR / "mined_controlled_sheet_codex_ver.tsv"
DEFAULT_OUTPUT_COMBINED = DEFAULT_TARGET_DIR / "combined_review_sheet_codex_ver.tsv"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "controlled_codex_labels"

REVIEWER_ID = "(codex_ver)"

RELIABLE_STRATA = {
    "candidate_reliable_promote_seed",
    "existing_strict_reliable_seed",
}
DENSE_STRATA = {
    "candidate_unreliable_dense_noise_seed",
    "existing_strict_dense_seed",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-mined", type=Path, default=DEFAULT_INPUT_MINED)
    parser.add_argument("--input-combined", type=Path, default=DEFAULT_INPUT_COMBINED)
    parser.add_argument("--output-mined", type=Path, default=DEFAULT_OUTPUT_MINED)
    parser.add_argument("--output-combined", type=Path, default=DEFAULT_OUTPUT_COMBINED)
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


def confidence_for(row: dict[str, str]) -> str:
    p_geom = safe_float(row.get("p_geom_valid", ""), 0.0)
    if p_geom < 0.30:
        return "low"
    if row.get("label_match_status") == "exact_match":
        return "high"
    return "medium"


def annotation_missing_value(row: dict[str, str]) -> str:
    if row.get("label_match_status") == "exact_match":
        return "no"
    if row.get("label_match_status") == "pair_has_other_predicate":
        return "yes"
    if row.get("source_queue") == "existing_strict_seed":
        return "yes"
    return "no"


def ontology_issue_value(row: dict[str, str]) -> str:
    matched = (row.get("matched_predicates") or "").strip()
    if not matched:
        return "no"
    if matched == "close by":
        return "no"
    return "uncertain"


def fill_row(row: dict[str, str], sheet_name: str) -> tuple[dict[str, str], dict[str, Any]]:
    stratum = row.get("proposed_review_stratum", "")
    filled = dict(row)
    if stratum in RELIABLE_STRATA:
        final_label = "reliable_promote"
        target = 1
        fields = {
            "object_pair_valid": "yes",
            "predicate_visually_plausible": "yes",
            "geometry_witness_correct": "yes",
            "relation_informative": "yes",
            "relation_trivial_or_dense": "no",
            "annotation_missing_or_sparse": annotation_missing_value(row),
            "ontology_or_granularity_issue": ontology_issue_value(row),
            "segmentation_or_instance_issue": "uncertain",
            "final_controlled_label": final_label,
            "confidence": confidence_for(row),
        }
        rationale = (
            "codex_ver bootstrap: proposed reliable seed is treated as "
            "reliable_promote for train-only plumbing; not human-confirmed"
        )
    elif stratum in DENSE_STRATA:
        final_label = "unreliable_dense_noise"
        target = 0
        fields = {
            "object_pair_valid": "yes",
            "predicate_visually_plausible": "yes",
            "geometry_witness_correct": "yes",
            "relation_informative": "no",
            "relation_trivial_or_dense": "yes",
            "annotation_missing_or_sparse": "no",
            "ontology_or_granularity_issue": "no",
            "segmentation_or_instance_issue": "uncertain",
            "final_controlled_label": final_label,
            "confidence": confidence_for(row),
        }
        rationale = (
            "codex_ver bootstrap: proposed dense/noise seed is treated as "
            "unreliable_dense_noise for train-only plumbing; not human-confirmed"
        )
    else:
        raise ValueError(f"unsupported proposed_review_stratum: {stratum!r}")

    filled.update(
        {
            "reviewer_id": REVIEWER_ID,
            "review_round": "1",
            **fields,
            "notes": (
                f"{rationale}; sheet={sheet_name}; source_queue={row.get('source_queue')}; "
                f"stratum={stratum}; geometry_status={row.get('geometry_status')}; "
                f"p_geom_valid={row.get('p_geom_valid')}; label_match_status={row.get('label_match_status')}; "
                f"contact_sheet={row.get('contact_sheet')}"
            ),
        }
    )
    label_row = {
        "schema_version": "h002_controlled_codex_ver_label_v0",
        "sheet_name": sheet_name,
        "label_source": "codex_ver_sampling_prior_bootstrap",
        "not_human_confirmed": True,
        "paper_evidence_allowed": False,
        "posterior_claim_allowed": False,
        "reviewer_id": REVIEWER_ID,
        "review_round": 1,
        "review_id": row.get("review_id"),
        "prediction_id": row.get("prediction_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "rank_band": row.get("rank_band"),
        "geometry_status": row.get("geometry_status"),
        "p_geom_valid": safe_float(row.get("p_geom_valid", ""), 0.0),
        "label_match_status": row.get("label_match_status"),
        "proposed_review_stratum": stratum,
        "final_controlled_label": final_label,
        "posterior_target": target,
        "confidence": fields["confidence"],
        "review_fields": {
            key: filled[key]
            for key in [
                "object_pair_valid",
                "predicate_visually_plausible",
                "geometry_witness_correct",
                "relation_informative",
                "relation_trivial_or_dense",
                "annotation_missing_or_sparse",
                "ontology_or_granularity_issue",
                "segmentation_or_instance_issue",
            ]
        },
        "contact_sheet": row.get("contact_sheet"),
        "mesh_obj": row.get("mesh_obj"),
        "notes": filled["notes"],
    }
    return filled, label_row


def fill_sheet(
    input_sheet: Path,
    output_sheet: Path,
    labels_path: Path,
    sheet_name: str,
) -> dict[str, Any]:
    fieldnames, rows = read_tsv(input_sheet)
    filled_rows = []
    label_rows = []
    for row in rows:
        filled, label_row = fill_row(row, sheet_name)
        filled_rows.append(filled)
        label_rows.append(label_row)
    write_tsv(output_sheet, fieldnames, filled_rows)
    write_jsonl(labels_path, label_rows)
    final_counts = Counter(row["final_controlled_label"] for row in label_rows)
    target_counts = Counter(str(row["posterior_target"]) for row in label_rows)
    stratum_counts = Counter(row["proposed_review_stratum"] for row in label_rows)
    rank_target = Counter((row["rank_band"], str(row["posterior_target"])) for row in label_rows)
    return {
        "sheet_name": sheet_name,
        "rows": len(label_rows),
        "output_sheet": rel_path(output_sheet),
        "labels_path": rel_path(labels_path),
        "final_label_counts": dict(sorted(final_counts.items())),
        "posterior_target_counts": dict(sorted(target_counts.items())),
        "stratum_counts": dict(sorted(stratum_counts.items())),
        "target_by_rank_band": [
            {"rank_band": key[0], "posterior_target": key[1], "rows": value}
            for key, value in sorted(rank_target.items())
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Controlled Codex Labels",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- These are `(codex_ver)` bootstrap labels.",
        "- They are generated from controlled sampling strata, not human visual review.",
        "- They may be used only for train-only plumbing smoke.",
        "- They do not satisfy the human/independent label requirement for a posterior claim.",
        "",
        "## Counts",
        "",
        "| Sheet | Rows | Positive | Negative |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name in ["mined_controlled", "combined_review"]:
        result = summary["sheets"][name]
        lines.append(
            f"| `{name}` | {result['rows']} | "
            f"{result['posterior_target_counts'].get('1', 0)} | "
            f"{result['posterior_target_counts'].get('0', 0)} |"
        )
    lines.extend(
        [
            "",
            "## Mapping",
            "",
            "| Proposed stratum | Final label | Target |",
            "| --- | --- | ---: |",
            "| `candidate_reliable_promote_seed` | `reliable_promote` | 1 |",
            "| `existing_strict_reliable_seed` | `reliable_promote` | 1 |",
            "| `candidate_unreliable_dense_noise_seed` | `unreliable_dense_noise` | 0 |",
            "| `existing_strict_dense_seed` | `unreliable_dense_noise` | 0 |",
            "",
        ]
    )
    as_abs(path).write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    mined_labels = output_dir / "mined_codex_ver_labels.jsonl"
    combined_labels = output_dir / "combined_codex_ver_labels.jsonl"
    summary_path = output_dir / "summary.json"
    report_path = output_dir / "report.md"
    sheets = {
        "mined_controlled": fill_sheet(
            args.input_mined,
            args.output_mined,
            mined_labels,
            "mined_controlled",
        ),
        "combined_review": fill_sheet(
            args.input_combined,
            args.output_combined,
            combined_labels,
            "combined_review",
        ),
    }
    summary = {
        "schema_version": "h002_controlled_codex_label_summary_v0",
        "status": "controlled_codex_ver_labels_filled_not_human_confirmed",
        "created_at": created_at,
        "input_paths": {
            "mined_sheet": rel_path(args.input_mined),
            "combined_sheet": rel_path(args.input_combined),
        },
        "output_paths": {
            "mined_sheet_codex_ver": rel_path(args.output_mined),
            "combined_sheet_codex_ver": rel_path(args.output_combined),
            "mined_labels": rel_path(mined_labels),
            "combined_labels": rel_path(combined_labels),
            "summary": rel_path(summary_path),
            "report": rel_path(report_path),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "label_source": "codex_ver_sampling_prior_bootstrap",
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "vmv_model_input_allowed": False,
        },
        "mapping": {
            "candidate_reliable_promote_seed": "reliable_promote",
            "existing_strict_reliable_seed": "reliable_promote",
            "candidate_unreliable_dense_noise_seed": "unreliable_dense_noise",
            "existing_strict_dense_seed": "unreliable_dense_noise",
        },
        "sheets": sheets,
    }
    write_json(summary_path, summary)
    write_report(report_path, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    mined = summary["sheets"]["mined_controlled"]
    combined = summary["sheets"]["combined_review"]
    print(
        f"status={summary['status']} "
        f"mined={mined['rows']} pos={mined['posterior_target_counts'].get('1', 0)} "
        f"neg={mined['posterior_target_counts'].get('0', 0)} "
        f"combined={combined['rows']} pos={combined['posterior_target_counts'].get('1', 0)} "
        f"neg={combined['posterior_target_counts'].get('0', 0)} "
        f"validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
