#!/usr/bin/env python3
"""Mine an object/endpoint-controlled H002 reliability target v3 label sheet."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

PLAN_DIR = RGA_ROOT / "reliability_target_v3_object_endpoint_controlled_plan"
POSITIVE_ANCHOR_PLAN_DIR = RGA_ROOT / "reliability_target_v3_positive_anchor_plan"

DEFAULT_PLAN_SUMMARY = PLAN_DIR / "summary.json"
DEFAULT_RECOMMENDED_CELLS = PLAN_DIR / "recommended_sampling_cells.json"
DEFAULT_CANDIDATE_POOL = PLAN_DIR / "candidate_pool_internal_preview.jsonl"
DEFAULT_SCHEMA = POSITIVE_ANCHOR_PLAN_DIR / "v3_label_schema.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v3_object_endpoint_candidate_mining"

REVIEW_SCOPE = "h002_reliability_v3_object_endpoint_controlled_mining"
SCHEMA_VERSION = "h002_reliability_v3_object_endpoint_candidate_mining_v1"

VISIBLE_FIELDS = [
    "blind_review_id",
    "review_scope",
    "scan_id",
    "scene_context_id",
    "subject_id",
    "subject_label",
    "predicate_label",
    "predicate_family",
    "object_id",
    "object_label",
    "family_question",
    "positive_cues",
    "negative_cues",
    "evidence_packet_status",
    "multiview_packet",
    "pointcloud_or_mesh_packet",
    "contact_or_context_sheet",
    "reviewer_id",
    "review_round",
    "endpoint_identity_v3",
    "pair_evaluability_v3",
    "geometry_support_v3",
    "relation_usefulness_v3",
    "relation_reliability_v3",
    "primary_reason_v3",
    "uncertainty_reason_v3",
    "label_notes_v3",
]

COMPLETION_FIELDS = [
    "reviewer_id",
    "review_round",
    "endpoint_identity_v3",
    "pair_evaluability_v3",
    "geometry_support_v3",
    "relation_usefulness_v3",
    "relation_reliability_v3",
    "primary_reason_v3",
    "uncertainty_reason_v3",
    "label_notes_v3",
]

FAMILY_PROMPTS = {
    "support_contact": {
        "question": "Does the subject physically contact, rest on, support, or attach to the object in the evidence?",
        "positive_cues": "visible contact, plausible support or attachment surface, consistent support direction, non-trivial pair",
        "negative_cues": "nearby without contact/support, wrong support direction, trivial room-structure relation, segmentation or identity issue",
    },
    "relative_vertical": {
        "question": "Is the subject clearly higher/lower than the object in the evidence?",
        "positive_cues": "clear vertical ordering, predicate direction matches the evidence, comparable endpoints",
        "negative_cues": "wrong vertical direction, ambiguous height, non-comparable room surface, segmentation or identity issue",
    },
}

FORBIDDEN_VISIBLE_FIELD_TOKENS = [
    "candidate_proxy",
    "proxy_class",
    "queue_kind",
    "source_queue",
    "rank_band",
    "semantic_rank",
    "semantic_score",
    "p_geom_valid",
    "geometry_status",
    "h001_verification_status",
    "label_match_status",
    "sampling_category",
    "expected_v3_role",
    "endpoint_flag_pattern",
    "matched_predicates",
    "reason_codes",
    "hidden",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-summary", type=Path, default=DEFAULT_PLAN_SUMMARY)
    parser.add_argument("--recommended-cells", type=Path, default=DEFAULT_RECOMMENDED_CELLS)
    parser.add_argument("--candidate-pool", type=Path, default=DEFAULT_CANDIDATE_POOL)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_json_list(path: Path) -> list[dict[str, Any]]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError(f"Expected list JSON: {path}")
    return payload


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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def blind_review_id(row: dict[str, Any]) -> str:
    return "ftv3oe_" + stable_hash("h002_reliability_v3_object_endpoint:" + str(row["prediction_id"]))[:12]


def physical_pair_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("scan_id")),
        str(row.get("scene_context_id") or row.get("subgraph_id")),
        str(row.get("subject_id")),
        str(row.get("object_id")),
    )


def row_cell_value(row: dict[str, Any], cell_type: str) -> str:
    if cell_type == "predicate_label":
        return str(row.get("predicate_label"))
    key = f"{cell_type}_cell"
    return str(row.get(key))


def proxy_label_key(proxy_class: str) -> str:
    if proxy_class == "candidate_positive_proxy":
        return "positive"
    if proxy_class == "candidate_negative_proxy":
        return "negative"
    return "unknown"


def float_value(row: dict[str, Any], key: str, default: float) -> float:
    try:
        value = row.get(key)
        return float(value if value is not None else default)
    except (TypeError, ValueError):
        return default


def rank_value(row: dict[str, Any]) -> float:
    try:
        value = row.get("semantic_rank_hidden")
        return float(value if value is not None else 999999)
    except (TypeError, ValueError):
        return 999999.0


def sort_key(
    row: dict[str, Any],
    proxy_class: str,
    scan_counts: Counter[str],
    pair_counts: Counter[tuple[str, str, str, str]],
) -> tuple[Any, ...]:
    p_geom = float_value(row, "p_geom_valid_hidden", 0.5)
    semantic_score = float_value(row, "semantic_score_norm_hidden", 0.0)
    pair_key = physical_pair_key(row)
    base = (
        scan_counts[str(row.get("scan_id"))],
        pair_counts[pair_key],
        str(row.get("scan_id")),
    )
    if proxy_class == "candidate_positive_proxy":
        quality = (-p_geom, rank_value(row), -semantic_score)
    else:
        quality = (p_geom, rank_value(row), -semantic_score)
    return (*base, *quality, str(row.get("prediction_id")))


def candidate_pool_for_cell(
    rows: list[dict[str, Any]],
    cell_type: str,
    cell_key: str,
    proxy_class: str,
    used_prediction_ids: set[str],
) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if str(row.get("candidate_proxy_class_hidden")) == proxy_class
        and str(row.get("prediction_id")) not in used_prediction_ids
        and row_cell_value(row, cell_type) == cell_key
    ]


def greedy_select(
    rows: list[dict[str, Any]],
    *,
    requested: int,
    proxy_class: str,
    used_prediction_ids: set[str],
    scan_counts: Counter[str],
    pair_counts: Counter[tuple[str, str, str, str]],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    passes = [
        {"max_pair": 1, "max_scan": 4, "policy": "pair_cap_1_scan_cap_4"},
        {"max_pair": 1, "max_scan": 8, "policy": "pair_cap_1_scan_cap_8"},
        {"max_pair": 2, "max_scan": 999999, "policy": "pair_cap_2_scan_unbounded"},
    ]
    for selection_pass in passes:
        while len(selected) < requested:
            eligible = []
            for row in rows:
                prediction_id = str(row.get("prediction_id"))
                pair_key = physical_pair_key(row)
                scan_id = str(row.get("scan_id"))
                if prediction_id in used_prediction_ids:
                    continue
                if pair_counts[pair_key] >= selection_pass["max_pair"]:
                    continue
                if scan_counts[scan_id] >= selection_pass["max_scan"]:
                    continue
                eligible.append(row)
            if not eligible:
                break
            eligible.sort(key=lambda row: sort_key(row, proxy_class, scan_counts, pair_counts))
            row = dict(eligible[0])
            row["selection_pass_hidden"] = selection_pass["policy"]
            selected.append(row)
            used_prediction_ids.add(str(row.get("prediction_id")))
            pair_counts[physical_pair_key(row)] += 1
            scan_counts[str(row.get("scan_id"))] += 1
    return selected


def select_candidates(
    candidate_rows: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    used_prediction_ids: set[str] = set()
    scan_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str, str, str]] = Counter()
    selected_rows: list[dict[str, Any]] = []
    status_rows: list[dict[str, Any]] = []

    for rec_index, rec in enumerate(recommendations, start=1):
        cell_type = str(rec["cell_type"])
        cell_key = str(rec["cell_key"])
        tier = str(rec["tier"])
        for proxy_class, requested_key in [
            ("candidate_positive_proxy", "suggested_positive_proxy"),
            ("candidate_negative_proxy", "suggested_negative_proxy"),
        ]:
            requested = int(rec.get(requested_key, 0))
            if requested <= 0:
                continue
            pool = candidate_pool_for_cell(candidate_rows, cell_type, cell_key, proxy_class, used_prediction_ids)
            selected = greedy_select(
                pool,
                requested=requested,
                proxy_class=proxy_class,
                used_prediction_ids=used_prediction_ids,
                scan_counts=scan_counts,
                pair_counts=pair_counts,
            )
            for within_cell_index, row in enumerate(selected, start=1):
                row.update(
                    {
                        "sampling_tier_hidden": tier,
                        "sampling_cell_type_hidden": cell_type,
                        "sampling_cell_key_hidden": cell_key,
                        "sampling_recommendation_index_hidden": rec_index,
                        "sampling_proxy_label_key_hidden": proxy_label_key(proxy_class),
                        "sampling_requested_for_proxy_hidden": requested,
                        "sampling_within_cell_index_hidden": within_cell_index,
                    }
                )
                selected_rows.append(row)
            status_rows.append(
                {
                    "tier": tier,
                    "cell_type": cell_type,
                    "cell_key": cell_key,
                    "proxy_class": proxy_class,
                    "requested": requested,
                    "available_after_prior_tiers": len(pool),
                    "selected": len(selected),
                    "residual": requested - len(selected),
                    "selection_policy": "greedy_pair_scan_diversified",
                }
            )

    return selected_rows, status_rows


def family_prompt(row: dict[str, Any]) -> dict[str, str]:
    return FAMILY_PROMPTS.get(
        str(row.get("predicate_family")),
        {
            "question": "Does the relation hold according to the evidence?",
            "positive_cues": "relation is supported by visual and geometric evidence",
            "negative_cues": "relation is contradicted or not evaluable from the evidence",
        },
    )


def visible_row(row: dict[str, Any]) -> dict[str, Any]:
    prompt = family_prompt(row)
    output = {
        "blind_review_id": blind_review_id(row),
        "review_scope": REVIEW_SCOPE,
        "scan_id": row.get("scan_id"),
        "scene_context_id": row.get("scene_context_id") or row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "family_question": prompt["question"],
        "positive_cues": prompt["positive_cues"],
        "negative_cues": prompt["negative_cues"],
        "evidence_packet_status": row.get("packet_status"),
        "multiview_packet": row.get("multiview_packet", ""),
        "pointcloud_or_mesh_packet": row.get("pointcloud_or_mesh_packet", ""),
        "contact_or_context_sheet": row.get("contact_or_context_sheet", ""),
    }
    for field in COMPLETION_FIELDS:
        output[field] = ""
    return output


def endpoint_pair_note(row: dict[str, Any]) -> str:
    pattern = str(row.get("endpoint_flag_pattern_hidden") or "")
    notes = []
    for part in pattern.split("|"):
        if part.endswith("=1"):
            notes.append(part.replace("=1", ""))
    return ",".join(notes)


def manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_v3_object_endpoint_manifest_v1",
        "batch_name": "reliability_target_v3_object_endpoint_candidate_mining",
        "blind_review_id": blind_review_id(row),
        "asset_request_id": row.get("original_blind_review_id"),
        "prediction_id_hidden": row.get("prediction_id"),
        "sampling_category_hidden": row.get("sampling_tier_hidden"),
        "expected_v3_role_hidden": "review_required_proxy_stratum_not_target",
        "labeler_visible": False,
        "post_label_join_only": True,
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("scene_context_id") or row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "packet_paths": {
            "multiview_packet": row.get("multiview_packet", ""),
            "pointcloud_or_mesh_packet": row.get("pointcloud_or_mesh_packet", ""),
            "contact_or_context_sheet": row.get("contact_or_context_sheet", ""),
        },
        "hidden_sampling_axes_post_label_only": {
            "sampling_tier_hidden": row.get("sampling_tier_hidden"),
            "sampling_cell_type_hidden": row.get("sampling_cell_type_hidden"),
            "sampling_cell_key_hidden": row.get("sampling_cell_key_hidden"),
            "sampling_proxy_label_key_hidden": row.get("sampling_proxy_label_key_hidden"),
            "sampling_requested_for_proxy_hidden": row.get("sampling_requested_for_proxy_hidden"),
            "sampling_within_cell_index_hidden": row.get("sampling_within_cell_index_hidden"),
            "selection_pass_hidden": row.get("selection_pass_hidden"),
            "candidate_proxy_class_hidden": row.get("candidate_proxy_class_hidden"),
            "endpoint_flag_pattern_hidden": row.get("endpoint_flag_pattern_hidden"),
            "endpoint_pair_note_hidden": endpoint_pair_note(row),
            "subject_object_family_cell_hidden": row.get("subject_object_family_cell"),
            "subject_object_cell_hidden": row.get("subject_object_cell"),
            "object_family_cell_hidden": row.get("object_family_cell"),
            "object_predicate_cell_hidden": row.get("object_predicate_cell"),
            "endpoint_family_cell_hidden": row.get("endpoint_family_cell"),
            "queue_kind_hidden": row.get("queue_kind_hidden"),
            "source_queue_hidden": row.get("source_queue_hidden"),
            "geometry_status_hidden": row.get("geometry_status_hidden"),
            "h001_verification_status_hidden": row.get("h001_verification_status_hidden"),
            "label_match_status_hidden": row.get("label_match_status_hidden"),
            "label_geometry_bucket_hidden": row.get("label_geometry_bucket_hidden"),
            "rank_band_hidden": row.get("rank_band_hidden"),
            "semantic_rank_hidden": row.get("semantic_rank_hidden"),
            "semantic_score_raw_hidden": row.get("semantic_score_raw_hidden"),
            "semantic_score_norm_hidden": row.get("semantic_score_norm_hidden"),
            "p_geom_valid_hidden": row.get("p_geom_valid_hidden"),
            "machine_hint_hidden": row.get("machine_hint_hidden"),
            "matched_predicates_hidden": row.get("matched_predicates_hidden", []),
            "reason_codes_hidden": row.get("reason_codes_hidden", []),
            "original_blind_review_id_hidden": row.get("original_blind_review_id"),
        },
        "forbidden_as_labeler_visible": [
            "candidate_proxy_class",
            "sampling_tier",
            "sampling_cell",
            "source queue",
            "semantic score/rank",
            "p_geom_valid",
            "geometry_status",
            "h001 verification status",
            "label_match_status",
            "matched GT/predicate hints",
            "reason codes",
            "endpoint flag pattern",
            "posterior target fields",
        ],
    }


def packet_path_errors(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):
        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = str(row.get(field) or "")
            if not value or not as_abs(Path(value)).exists():
                errors.append(
                    {
                        "row_number": row_number,
                        "blind_review_id": row.get("blind_review_id"),
                        "field": field,
                        "value": value,
                        "error_type": "packet_path_missing",
                    }
                )
    return errors


def surface_leakage_hits(fieldnames: list[str]) -> list[dict[str, Any]]:
    hits = []
    for field in fieldnames:
        lowered = field.lower()
        for token in FORBIDDEN_VISIBLE_FIELD_TOKENS:
            if token in lowered:
                hits.append({"field": field, "token": token, "error_type": "forbidden_visible_field"})
    return hits


def tier_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("sampling_tier_hidden"))].append(row)
    summaries = []
    for tier, tier_rows in sorted(grouped.items()):
        classes = Counter(str(row.get("candidate_proxy_class_hidden")) for row in tier_rows)
        families = Counter(str(row.get("predicate_family")) for row in tier_rows)
        summaries.append(
            {
                "tier": tier,
                "rows": len(tier_rows),
                "candidate_positive_proxy": classes.get("candidate_positive_proxy", 0),
                "candidate_negative_proxy": classes.get("candidate_negative_proxy", 0),
                "support_contact": families.get("support_contact", 0),
                "relative_vertical": families.get("relative_vertical", 0),
                "unique_scans": len({str(row.get("scan_id")) for row in tier_rows}),
                "unique_physical_pairs": len({physical_pair_key(row) for row in tier_rows}),
            }
        )
    return summaries


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 Reliability Target V3 Object/Endpoint Candidate Mining",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only candidate mining.",
        "- No validation/test rows are used.",
        "- No labels are filled.",
        "- No posterior is trained.",
        "- Candidate-positive/negative proxy is a sampling stratum only, not a target label.",
        "- Multi-view packets remain audit/label evidence only, not deployable model input.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| requested rows from plan | {counts['requested_rows_from_plan']} |",
        f"| selected rows | {counts['selected_rows']} |",
        f"| selection residual | {counts['selection_residual']} |",
        f"| candidate-positive proxy strata | {counts['candidate_positive_proxy']} |",
        f"| candidate-negative proxy strata | {counts['candidate_negative_proxy']} |",
        f"| support_contact | {counts['by_family'].get('support_contact', 0)} |",
        f"| relative_vertical | {counts['by_family'].get('relative_vertical', 0)} |",
        f"| unique scans | {counts['unique_scans']} |",
        f"| unique physical pairs | {counts['unique_physical_pairs']} |",
        f"| duplicated physical-pair keys | {counts['duplicated_physical_pair_keys']} |",
        f"| max rows per scan | {counts['max_rows_per_scan']} |",
        f"| packet path errors | {counts['packet_path_errors']} |",
        f"| label-surface leakage hits | {counts['label_surface_leakage_hits']} |",
        "",
        "## Tier Summary",
        "",
        "| Tier | Rows | Pos Proxy | Neg Proxy | support_contact | relative_vertical | Unique Scans |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["tier_summary"]:
        lines.append(
            f"| `{row['tier']}` | {row['rows']} | {row['candidate_positive_proxy']} | "
            f"{row['candidate_negative_proxy']} | {row['support_contact']} | "
            f"{row['relative_vertical']} | {row['unique_scans']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Next TODO",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def validate_plan(plan_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("next_todo") != "reliability_target_v3_object_endpoint_candidate_mining":
        errors.append({"error_type": "unexpected_plan_next_todo", "value": plan_summary.get("next_todo")})
    if plan_summary.get("validation_used") is not False:
        errors.append({"error_type": "plan_validation_used_not_false"})
    if plan_summary.get("test_used") is not False:
        errors.append({"error_type": "plan_test_used_not_false"})
    if plan_summary.get("posterior_allowed") is not False:
        errors.append({"error_type": "plan_posterior_allowed_not_false"})
    return errors


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(args.plan_summary)
    recommendations = read_json_list(args.recommended_cells)
    candidate_rows = read_jsonl(args.candidate_pool)
    schema = read_json(args.schema)
    validation_errors = validate_plan(plan_summary)

    selected_rows, selection_status = select_candidates(candidate_rows, recommendations)
    visible_rows = [visible_row(row) for row in selected_rows]
    manifest_rows = [manifest_row(row) for row in selected_rows]

    path_errors = packet_path_errors(visible_rows)
    leakage_hits = surface_leakage_hits(VISIBLE_FIELDS)

    requested = sum(int(row["suggested_total"]) for row in recommendations)
    class_counts = Counter(str(row.get("candidate_proxy_class_hidden")) for row in selected_rows)
    family_counts = Counter(str(row.get("predicate_family")) for row in selected_rows)
    scan_counts = Counter(str(row.get("scan_id")) for row in selected_rows)
    pair_counts = Counter(physical_pair_key(row) for row in selected_rows)
    selected_tier_summary = tier_summary(selected_rows)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "label_sheet": output_dir / "object_endpoint_label_sheet.tsv",
        "manifest_post_label_only": output_dir / "object_endpoint_manifest_post_label_only.jsonl",
        "selected_candidates_internal": output_dir / "selected_candidates_internal.jsonl",
        "selection_status": output_dir / "selection_status.csv",
        "tier_summary": output_dir / "tier_summary.csv",
        "tier_summary_json": output_dir / "tier_summary.json",
        "label_surface_leakage_hits": output_dir / "label_surface_leakage_hits.jsonl",
        "packet_path_errors": output_dir / "packet_path_errors.jsonl",
        "v3_label_schema": output_dir / "v3_label_schema.json",
    }

    input_error_count = len(validation_errors) + len(path_errors) + len(leakage_hits)
    if input_error_count:
        status = "h002_reliability_target_v3_object_endpoint_candidate_mining_input_errors"
        next_todo = "fix_reliability_target_v3_object_endpoint_candidate_mining_inputs"
        decision = "Candidate mining produced input errors; do not fill labels until these are fixed."
    elif len(selected_rows) < requested:
        status = "h002_reliability_target_v3_object_endpoint_candidate_mining_ready_with_selection_deficit"
        next_todo = "reliability_target_v3_object_endpoint_label_fill"
        decision = (
            "The label sheet is ready, but duplicate-pair and scan-diversity controls left a selection deficit. "
            "Proceed to label fill only if this controlled size is acceptable; otherwise relax caps explicitly."
        )
    else:
        status = "h002_reliability_target_v3_object_endpoint_candidate_mining_ready_for_label_fill"
        next_todo = "reliability_target_v3_object_endpoint_label_fill"
        decision = (
            "The object/endpoint-controlled label sheet is ready for v3 label fill. Hidden proxy and construction "
            "fields are stored only in the post-label manifest and must not be used for label decisions."
        )

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "decision": decision,
        "next_todo": next_todo,
        "input_paths": {
            "plan_summary": rel_path(args.plan_summary),
            "recommended_cells": rel_path(args.recommended_cells),
            "candidate_pool": rel_path(args.candidate_pool),
            "schema": rel_path(args.schema),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "labels_filled": False,
            "posterior_trained": False,
            "posterior_smoke_allowed": False,
            "candidate_proxy_labels_are_sampling_strata_only": True,
            "multi_view_as_model_input": False,
            "paper_metric_evidence": False,
        },
        "counts": {
            "candidate_pool_rows": len(candidate_rows),
            "recommended_cells": len(recommendations),
            "requested_rows_from_plan": requested,
            "selected_rows": len(selected_rows),
            "selection_residual": requested - len(selected_rows),
            "candidate_positive_proxy": class_counts.get("candidate_positive_proxy", 0),
            "candidate_negative_proxy": class_counts.get("candidate_negative_proxy", 0),
            "by_family": dict(sorted(family_counts.items())),
            "unique_scans": len(scan_counts),
            "max_rows_per_scan": max(scan_counts.values()) if scan_counts else 0,
            "unique_physical_pairs": len(pair_counts),
            "duplicated_physical_pair_keys": sum(1 for count in pair_counts.values() if count > 1),
            "packet_path_errors": len(path_errors),
            "label_surface_leakage_hits": len(leakage_hits),
            "validation_errors": len(validation_errors),
        },
        "tier_summary": selected_tier_summary,
        "selection_status": selection_status,
        "validation_errors": validation_errors,
    }

    write_tsv(output_paths["label_sheet"], visible_rows, VISIBLE_FIELDS)
    write_jsonl(output_paths["manifest_post_label_only"], manifest_rows)
    write_jsonl(output_paths["selected_candidates_internal"], selected_rows)
    write_csv(output_paths["selection_status"], selection_status)
    write_csv(output_paths["tier_summary"], selected_tier_summary)
    write_json(output_paths["tier_summary_json"], {"tiers": selected_tier_summary})
    write_jsonl(output_paths["label_surface_leakage_hits"], leakage_hits)
    write_jsonl(output_paths["packet_path_errors"], path_errors)
    write_json(output_paths["v3_label_schema"], schema)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    print(
        "status={status} requested={requested} selected={selected} residual={residual} "
        "pos_proxy={pos} neg_proxy={neg} leakage={leakage} packet_errors={packet_errors} "
        "validation_used={validation_used} test_used={test_used} posterior_allowed={posterior_allowed} next={next_todo}".format(
            status=summary["status"],
            requested=counts["requested_rows_from_plan"],
            selected=counts["selected_rows"],
            residual=counts["selection_residual"],
            pos=counts["candidate_positive_proxy"],
            neg=counts["candidate_negative_proxy"],
            leakage=counts["label_surface_leakage_hits"],
            packet_errors=counts["packet_path_errors"],
            validation_used=summary["boundary"]["validation_usage"],
            test_used=summary["boundary"]["test_usage"],
            posterior_allowed=summary["boundary"]["posterior_smoke_allowed"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
