#!/usr/bin/env python3
"""Mine compact full-train H002 controlled label candidates from RGA queues."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_SUMMARY = RGA_ROOT / "train_rga_summary.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "controlled_label_mining"

STRUCTURAL_LABELS = {
    "ceiling",
    "curtain",
    "door",
    "doorframe",
    "floor",
    "room",
    "shower",
    "shower curtain",
    "wall",
    "window",
}
GENERIC_LABELS = {"item", "object", "clutter", "unknown"}

REVIEW_FIELDS = [
    "reviewer_id",
    "review_round",
    "object_pair_valid",
    "predicate_visually_plausible",
    "geometry_witness_correct",
    "relation_informative",
    "relation_trivial_or_dense",
    "annotation_missing_or_sparse",
    "ontology_or_granularity_issue",
    "segmentation_or_instance_issue",
    "final_controlled_label",
    "failure_taxonomy_label",
    "confidence",
    "notes",
]

ALLOWED_FINAL_LABELS = [
    "reliable_promote",
    "unreliable_dense_noise",
    "relabel_only",
    "invalid_pair",
    "geometry_artifact",
    "abstain_uncertain",
]

ALLOWED_TAXONOMY_LABELS = [
    "true_underconfidence",
    "semantic_overconfidence_invalid",
    "dense_relation_noise",
    "annotation_sparsity",
    "ontology_or_granularity_issue",
    "geometry_artifact",
    "invalid_pair",
    "valid_but_trivial_dense",
    "uncertain_needs_visual_or_mesh",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hl-queue", type=Path, default=DEFAULT_HL_QUEUE)
    parser.add_argument("--lh-queue", type=Path, default=DEFAULT_LH_QUEUE)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--hl-per-stratum",
        type=int,
        default=8,
        help="Maximum selected rows for each HL predicate/label/rank stratum.",
    )
    parser.add_argument(
        "--lh-per-stratum",
        type=int,
        default=4,
        help="Maximum selected rows for each LH predicate/label/rank stratum.",
    )
    parser.add_argument(
        "--max-total",
        type=int,
        default=700,
        help="Global candidate cap after stratum sampling. Use 0 for no cap.",
    )
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path):
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc


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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def endpoint_category(label: str) -> str:
    low = label.lower()
    if low in STRUCTURAL_LABELS:
        return "structural"
    if low in GENERIC_LABELS:
        return "generic"
    return "object"


def queue_path(queue_kind: str, args: argparse.Namespace) -> Path:
    return args.hl_queue if queue_kind == "HL" else args.lh_queue


def safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def candidate_role(row: dict[str, Any]) -> tuple[str, str]:
    queue_kind = str(row["queue_kind"])
    family = str(row["predicate_family"])
    label_status = str(row["label_match_status"])

    if queue_kind == "HL":
        if label_status == "exact_match":
            return (
                "hl_exact_label_geometry_contradiction",
                "exact-label relation is high-ranked but geometry-unsatisfied; audit geometry artifact versus annotation issue",
            )
        if label_status == "family_match":
            return (
                "hl_family_match_geometry_contradiction",
                "same-family relation is high-ranked but geometry-unsatisfied; audit predicate granularity and geometry witness",
            )
        if label_status == "pair_has_other_predicate":
            return (
                "hl_wrong_predicate_geometry_contradiction",
                "object pair has another GT predicate while this high-ranked predicate is geometry-unsatisfied",
            )
        return (
            "hl_no_gt_geometry_contradiction",
            "high-ranked no-GT relation is geometry-unsatisfied; semantic overconfidence candidate",
        )

    if label_status == "exact_match":
        return (
            "lh_exact_label_underconfidence",
            "exact-label relation is low-ranked but geometry-satisfied; true underconfidence candidate",
        )
    if label_status == "family_match":
        return (
            "lh_family_match_granularity",
            "same-family relation is low-ranked but geometry-satisfied; predicate granularity candidate",
        )
    if label_status == "pair_has_other_predicate":
        return (
            "lh_alternative_relation_on_gt_pair",
            "same object pair has another GT predicate; audit relabel versus additional valid relation",
        )
    if family == "proximity":
        return (
            "lh_no_gt_proximity_dense_or_sparse",
            "geometry-satisfied proximity without GT; audit dense trivial relation versus missing annotation",
        )
    if family == "support_contact":
        return (
            "lh_no_gt_support_contact_missing_or_noise",
            "geometry-satisfied support/contact without GT; audit endpoint identity and support witness",
        )
    return (
        "lh_no_gt_vertical_sparse_or_trivial",
        "geometry-satisfied vertical relation without GT; audit annotation sparsity versus trivial ordering",
    )


def stratum_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row["queue_kind"]),
        str(row["predicate_family"]),
        str(row["predicate_label"]),
        str(row["label_match_status"]),
        str(row["rank_band"]),
    )


def priority_key(row: dict[str, Any]) -> tuple[Any, ...]:
    queue_kind = str(row["queue_kind"])
    rank = safe_int(row.get("semantic_rank"), 10**9)
    label_status = str(row["label_match_status"])
    label_bonus = {
        "exact_match": 0,
        "family_match": 1,
        "pair_has_other_predicate": 2,
        "no_gt_for_pair": 3,
    }.get(label_status, 4)
    if queue_kind == "HL":
        score_component = safe_float(row.get("semantic_score_norm"))
        return (label_bonus, rank, -score_component, str(row["prediction_id"]))
    underconfidence = safe_float(row.get("underconfidence_score"))
    p_geom = safe_float(row.get("p_geom_valid"))
    return (label_bonus, -underconfidence, -p_geom, rank, str(row["prediction_id"]))


def round_robin_by_scan(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    by_scan: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
    for row in sorted(rows, key=priority_key):
        by_scan[str(row["scan_id"])].append(row)
    selected: list[dict[str, Any]] = []
    scans = deque(sorted(by_scan))
    while scans and len(selected) < limit:
        scan = scans.popleft()
        queue = by_scan[scan]
        if queue:
            selected.append(queue.popleft())
        if queue:
            scans.append(scan)
    return selected


def collect_pools(args: argparse.Namespace) -> tuple[dict[tuple[str, str, str, str, str], list[dict[str, Any]]], dict[str, Any]]:
    pools: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    stats: dict[str, Any] = {
        "input_rows": Counter(),
        "input_by_family": Counter(),
        "input_by_predicate": Counter(),
        "input_by_label_status": Counter(),
        "input_by_rank_band": Counter(),
        "input_by_stratum": Counter(),
        "scan_ids": set(),
    }
    seen = set()
    for queue_kind in ("HL", "LH"):
        for row in iter_jsonl(queue_path(queue_kind, args)):
            if str(row.get("queue_kind")) != queue_kind:
                raise ValueError(f"queue_kind mismatch in {queue_path(queue_kind, args)}")
            identity = (
                row.get("prediction_id"),
                row.get("scan_id"),
                row.get("subgraph_id"),
                row.get("subject_id"),
                row.get("object_id"),
                row.get("predicate_label"),
            )
            if identity in seen:
                continue
            seen.add(identity)
            family = str(row["predicate_family"])
            predicate = str(row["predicate_label"])
            label_status = str(row["label_match_status"])
            rank_band = str(row["rank_band"])
            key = stratum_key(row)
            stats["input_rows"][queue_kind] += 1
            stats["input_by_family"][(queue_kind, family)] += 1
            stats["input_by_predicate"][(queue_kind, predicate)] += 1
            stats["input_by_label_status"][(queue_kind, label_status)] += 1
            stats["input_by_rank_band"][(queue_kind, rank_band)] += 1
            stats["input_by_stratum"][key] += 1
            stats["scan_ids"].add(str(row["scan_id"]))
            pools[key].append(row)
    return pools, stats


def select_candidates(
    pools: dict[tuple[str, str, str, str, str], list[dict[str, Any]]],
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    strata_rows: list[dict[str, Any]] = []
    review_index = 1
    for key in sorted(pools):
        queue_kind, family, predicate, label_status, rank_band = key
        cap = args.hl_per_stratum if queue_kind == "HL" else args.lh_per_stratum
        chosen = round_robin_by_scan(pools[key], cap)
        strata_rows.append(
            {
                "queue_kind": queue_kind,
                "predicate_family": family,
                "predicate_label": predicate,
                "label_match_status": label_status,
                "rank_band": rank_band,
                "available_rows": len(pools[key]),
                "selected_rows": len(chosen),
                "cap": cap,
            }
        )
        for row in chosen:
            role, reason = candidate_role(row)
            selected.append(normalize_candidate(row, review_index, role, reason))
            review_index += 1

    selected = sorted(
        selected,
        key=lambda row: (
            row["queue_kind"],
            row["predicate_family"],
            row["predicate_label"],
            row["label_match_status"],
            row["rank_band"],
            row["review_id"],
        ),
    )
    if args.max_total > 0 and len(selected) > args.max_total:
        selected = selected[: args.max_total]
    for index, row in enumerate(selected, start=1):
        row["review_id"] = f"ftctl_{index:04d}"
    return selected, strata_rows


def normalize_candidate(
    row: dict[str, Any],
    review_index: int,
    proposed_role: str,
    role_reason: str,
) -> dict[str, Any]:
    subject_label = str(row["subject_label"])
    object_label = str(row["object_label"])
    return {
        "schema_version": "h002_full_train_controlled_candidate_v0",
        "review_id": f"ftctl_{review_index:04d}",
        "source_id": row.get("source_id"),
        "source_scope": "open3dsg_train_full",
        "split_boundary": "train full only; no validation/test rows",
        "queue_kind": row.get("queue_kind"),
        "candidate_axis": "semantic_overconfidence"
        if row.get("queue_kind") == "HL"
        else "semantic_underconfidence_or_missing_relation",
        "proposed_audit_role": proposed_role,
        "role_reason": role_reason,
        "proposed_role_is_label": False,
        "prediction_id": row.get("prediction_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": subject_label,
        "subject_endpoint_category": endpoint_category(subject_label),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": object_label,
        "object_endpoint_category": endpoint_category(object_label),
        "same_endpoint_label": subject_label.lower() == object_label.lower(),
        "semantic_rank": row.get("semantic_rank"),
        "rank_band": row.get("rank_band"),
        "semantic_score_raw": row.get("semantic_score_raw"),
        "semantic_score_norm": row.get("semantic_score_norm"),
        "geometry_status": row.get("geometry_status"),
        "h001_verification_status": row.get("h001_verification_status"),
        "p_geom_valid": row.get("p_geom_valid"),
        "consistency_score": row.get("consistency_score"),
        "disagreement_score": row.get("disagreement_score"),
        "underconfidence_score": row.get("underconfidence_score"),
        "label_match_status": row.get("label_match_status"),
        "label_geometry_bucket": row.get("label_geometry_bucket"),
        "bucket_top50": row.get("bucket_top50"),
        "bucket_top100": row.get("bucket_top100"),
        "machine_hint": row.get("machine_hint"),
        "matched_predicates": row.get("matched_predicates") or [],
        "matched_gt_ids": row.get("matched_gt_ids") or [],
        "reason_codes": row.get("reason_codes") or [],
        "review_fields": {field: None for field in REVIEW_FIELDS},
        "audit_evidence_policy": (
            "Use point cloud/mesh/multi-view only for confirmation at this stage; "
            "do not add V_mv_e as model input until S_e/G_e/C_e/U_e evidence passes."
        ),
        "boundary": (
            "Candidate row only. proposed_audit_role is a sampling prior, not a "
            "training label or paper result."
        ),
    }


def sheet_row(row: dict[str, Any]) -> dict[str, Any]:
    flat = {
        "review_id": row["review_id"],
        "queue_kind": row["queue_kind"],
        "candidate_axis": row["candidate_axis"],
        "proposed_audit_role": row["proposed_audit_role"],
        "role_reason": row["role_reason"],
        "prediction_id": row["prediction_id"],
        "scan_id": row["scan_id"],
        "subgraph_id": row["subgraph_id"],
        "subject_id": row["subject_id"],
        "subject_label": row["subject_label"],
        "subject_endpoint_category": row["subject_endpoint_category"],
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "object_id": row["object_id"],
        "object_label": row["object_label"],
        "object_endpoint_category": row["object_endpoint_category"],
        "same_endpoint_label": row["same_endpoint_label"],
        "semantic_rank": row["semantic_rank"],
        "rank_band": row["rank_band"],
        "semantic_score_raw": row["semantic_score_raw"],
        "semantic_score_norm": row["semantic_score_norm"],
        "geometry_status": row["geometry_status"],
        "p_geom_valid": row["p_geom_valid"],
        "consistency_score": row["consistency_score"],
        "disagreement_score": row["disagreement_score"],
        "underconfidence_score": row["underconfidence_score"],
        "label_match_status": row["label_match_status"],
        "label_geometry_bucket": row["label_geometry_bucket"],
        "bucket_top50": row["bucket_top50"],
        "bucket_top100": row["bucket_top100"],
        "machine_hint": row["machine_hint"],
        "matched_predicates": ",".join(str(item) for item in row["matched_predicates"]),
        "reason_codes": ",".join(str(item) for item in row["reason_codes"]),
    }
    flat.update({field: "" for field in REVIEW_FIELDS})
    return flat


def counter_to_dict(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def summarize_candidates(
    selected: list[dict[str, Any]],
    strata_rows: list[dict[str, Any]],
    stats: dict[str, Any],
    args: argparse.Namespace,
    source_summary: dict[str, Any],
) -> dict[str, Any]:
    by_queue = Counter(str(row["queue_kind"]) for row in selected)
    by_family = Counter((row["queue_kind"], row["predicate_family"]) for row in selected)
    by_predicate = Counter((row["queue_kind"], row["predicate_label"]) for row in selected)
    by_label = Counter((row["queue_kind"], row["label_match_status"]) for row in selected)
    by_rank = Counter((row["queue_kind"], row["rank_band"]) for row in selected)
    by_role = Counter(str(row["proposed_audit_role"]) for row in selected)
    scan_ids = {str(row["scan_id"]) for row in selected}
    families_with_both_axes = sorted(
        family
        for family in {str(row["predicate_family"]) for row in selected}
        if by_family.get(("HL", family), 0) > 0 and by_family.get(("LH", family), 0) > 0
    )
    exact_or_family_lh = sum(
        1
        for row in selected
        if row["queue_kind"] == "LH" and row["label_match_status"] in {"exact_match", "family_match"}
    )
    hl_contradiction = sum(1 for row in selected if row["queue_kind"] == "HL")
    no_gt_lh = sum(
        1
        for row in selected
        if row["queue_kind"] == "LH" and row["label_match_status"] == "no_gt_for_pair"
    )
    ready_for_audit = (
        len(selected) >= 150
        and by_queue.get("HL", 0) >= 50
        and by_queue.get("LH", 0) >= 50
        and len(families_with_both_axes) >= 2
        and exact_or_family_lh >= 50
        and hl_contradiction >= 50
    )
    return {
        "schema_version": "h002_full_train_controlled_label_mining_summary_v0",
        "status": "ready_for_controlled_audit" if ready_for_audit else "needs_more_candidate_balance",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "validation_used": False,
        "test_used": False,
        "paper_result": False,
        "source_summary_status": source_summary.get("status"),
        "input_paths": {
            "hl_queue": rel_path(args.hl_queue),
            "lh_queue": rel_path(args.lh_queue),
            "summary_json": rel_path(args.summary_json),
        },
        "output_dir": rel_path(args.output_dir),
        "parameters": {
            "hl_per_stratum": args.hl_per_stratum,
            "lh_per_stratum": args.lh_per_stratum,
            "max_total": args.max_total,
            "stratum_key": [
                "queue_kind",
                "predicate_family",
                "predicate_label",
                "label_match_status",
                "rank_band",
            ],
        },
        "input": {
            "rows_by_queue": counter_to_dict(stats["input_rows"]),
            "unique_scans": len(stats["scan_ids"]),
        },
        "selected": {
            "rows": len(selected),
            "unique_scans": len(scan_ids),
            "by_queue": counter_to_dict(by_queue),
            "by_queue_family": counter_to_dict(by_family),
            "by_queue_predicate": counter_to_dict(by_predicate),
            "by_queue_label_status": counter_to_dict(by_label),
            "by_queue_rank_band": counter_to_dict(by_rank),
            "by_proposed_audit_role": counter_to_dict(by_role),
            "families_with_both_axes": families_with_both_axes,
            "exact_or_family_lh_rows": exact_or_family_lh,
            "no_gt_lh_rows": no_gt_lh,
            "hl_contradiction_rows": hl_contradiction,
        },
        "audit_boundary": {
            "candidate_role_is_not_label": True,
            "requires_independent_confirmation_before_training": True,
            "multi_view_policy": "audit evidence only; not deployable input at this stage",
            "forbidden_shortcut": (
                "Do not convert queue kind, predicate family, rank band, or p_geom_valid "
                "threshold directly into reliability labels."
            ),
        },
        "strata": strata_rows,
    }


def write_protocol(path: Path) -> None:
    write_json(
        path,
        {
            "schema_version": "h002_full_train_controlled_review_protocol_v0",
            "purpose": (
                "Confirm relation reliability labels for full-train RGA candidates "
                "without using validation/test rows."
            ),
            "review_fields": REVIEW_FIELDS,
            "allowed_final_controlled_label": ALLOWED_FINAL_LABELS,
            "allowed_failure_taxonomy_label": ALLOWED_TAXONOMY_LABELS,
            "yes_no_uncertain_fields": [
                "object_pair_valid",
                "predicate_visually_plausible",
                "geometry_witness_correct",
                "relation_informative",
                "relation_trivial_or_dense",
                "annotation_missing_or_sparse",
                "ontology_or_granularity_issue",
                "segmentation_or_instance_issue",
            ],
            "binary_target_mapping": {
                "reliable_promote": 1,
                "unreliable_dense_noise": 0,
                "relabel_only": None,
                "invalid_pair": None,
                "geometry_artifact": None,
                "abstain_uncertain": None,
            },
            "boundary": (
                "Candidate mining is train-only and hypothesis-stage. Proposed audit "
                "roles are sampling priors, not labels."
            ),
        },
    )


def write_report(path: Path, summary: dict[str, Any]) -> None:
    selected = summary["selected"]
    lines = [
        "# H002 Full Train Controlled Label Mining Report",
        "",
        f"Created: {summary['created_at']}",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Boundary",
        "",
        "- Split: train full only.",
        "- Validation/test rows used: false.",
        "- Candidate roles are sampling priors, not labels.",
        "- Multi-view/mesh evidence is audit support only at this stage.",
        "",
        "## Selected Candidates",
        "",
        f"- Rows: {selected['rows']}",
        f"- Unique scans: {selected['unique_scans']}",
        f"- Families with both HL and LH candidates: {', '.join(selected['families_with_both_axes'])}",
        f"- HL contradiction rows: {selected['hl_contradiction_rows']}",
        f"- LH exact/family rows: {selected['exact_or_family_lh_rows']}",
        f"- LH no-GT rows: {selected['no_gt_lh_rows']}",
        "",
        "## Queue Counts",
        "",
        "| Queue | Rows |",
        "| --- | ---: |",
    ]
    for key, value in selected["by_queue"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Proposed Audit Roles",
            "",
            "| Role | Rows |",
            "| --- | ---: |",
        ]
    )
    for key, value in selected["by_proposed_audit_role"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            "```text",
            f"{summary['output_dir']}/candidate_pool.jsonl",
            f"{summary['output_dir']}/candidate_sheet.tsv",
            f"{summary['output_dir']}/strata_summary.csv",
            f"{summary['output_dir']}/protocol.json",
            f"{summary['output_dir']}/summary.json",
            "```",
            "",
            "## Next Step",
            "",
            "Fill or independently confirm the review fields, then run a full-train "
            "label-readiness check before any posterior training.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.hl_queue = as_abs(args.hl_queue)
    args.lh_queue = as_abs(args.lh_queue)
    args.summary_json = as_abs(args.summary_json)
    args.output_dir = as_abs(args.output_dir)

    source_summary = read_json(args.summary_json)
    pools, stats = collect_pools(args)
    selected, strata_rows = select_candidates(pools, args)
    summary = summarize_candidates(selected, strata_rows, stats, args, source_summary)

    sheet_rows = [sheet_row(row) for row in selected]
    sheet_fields = [
        "review_id",
        "queue_kind",
        "candidate_axis",
        "proposed_audit_role",
        "role_reason",
        "prediction_id",
        "scan_id",
        "subgraph_id",
        "subject_id",
        "subject_label",
        "subject_endpoint_category",
        "predicate_label",
        "predicate_family",
        "object_id",
        "object_label",
        "object_endpoint_category",
        "same_endpoint_label",
        "semantic_rank",
        "rank_band",
        "semantic_score_raw",
        "semantic_score_norm",
        "geometry_status",
        "p_geom_valid",
        "consistency_score",
        "disagreement_score",
        "underconfidence_score",
        "label_match_status",
        "label_geometry_bucket",
        "bucket_top50",
        "bucket_top100",
        "machine_hint",
        "matched_predicates",
        "reason_codes",
        *REVIEW_FIELDS,
    ]
    strata_fields = [
        "queue_kind",
        "predicate_family",
        "predicate_label",
        "label_match_status",
        "rank_band",
        "available_rows",
        "selected_rows",
        "cap",
    ]

    write_jsonl(args.output_dir / "candidate_pool.jsonl", selected)
    write_tsv(args.output_dir / "candidate_sheet.tsv", sheet_rows, sheet_fields)
    write_csv(args.output_dir / "strata_summary.csv", strata_rows, strata_fields)
    write_protocol(args.output_dir / "protocol.json")
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary)

    print(
        "status={status} candidates={rows} hl={hl} lh={lh} output={output}".format(
            status=summary["status"],
            rows=summary["selected"]["rows"],
            hl=summary["selected"]["by_queue"].get("HL", 0),
            lh=summary["selected"]["by_queue"].get("LH", 0),
            output=rel_path(args.output_dir),
        )
    )


if __name__ == "__main__":
    main()
