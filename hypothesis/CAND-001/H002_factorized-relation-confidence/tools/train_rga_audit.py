#!/usr/bin/env python3
"""Create compact train RGA audit seeds from H002 HL/LH queues."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_SUMMARY = RGA_ROOT / "train_rga_summary.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "audit"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hl-queue", type=Path, default=DEFAULT_HL_QUEUE)
    parser.add_argument("--lh-queue", type=Path, default=DEFAULT_LH_QUEUE)
    parser.add_argument("--rga-summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--per-stratum", type=int, default=2)
    parser.add_argument("--hl-include-all-limit", type=int, default=100)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    path = as_abs(path)
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def read_json(path: Path) -> dict[str, Any]:
    path = as_abs(path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def safe_rate(num: int, den: int) -> float | None:
    return num / den if den else None


def serial_counter(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def serial_nested_counter(mapping: dict[Any, Counter[Any]]) -> dict[str, dict[str, int]]:
    return {str(key): serial_counter(value) for key, value in sorted(mapping.items(), key=lambda item: str(item[0]))}


def row_key(row: dict[str, Any]) -> str:
    return str(row["prediction_id"])


def queue_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    rank = row.get("semantic_rank")
    rank_value = int(rank) if rank is not None else 10**9
    if row.get("queue_kind") == "HL":
        disagreement = row.get("disagreement_score")
        p_geom_valid = row.get("p_geom_valid")
        return (
            rank_value,
            -(float(disagreement) if disagreement is not None else -1.0),
            float(p_geom_valid) if p_geom_valid is not None else 2.0,
            row_key(row),
        )
    underconfidence = row.get("underconfidence_score")
    p_geom_valid = row.get("p_geom_valid")
    return (
        -(float(underconfidence) if underconfidence is not None else -1.0),
        -(float(p_geom_valid) if p_geom_valid is not None else -1.0),
        rank_value,
        row_key(row),
    )


def count_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_family: dict[str, Counter[str]] = defaultdict(Counter)
    by_rank_band: dict[str, Counter[str]] = defaultdict(Counter)
    by_match: dict[str, Counter[str]] = defaultdict(Counter)
    by_reason: Counter[str] = Counter()
    by_hint: Counter[str] = Counter()
    by_predicate: dict[str, Counter[str]] = defaultdict(Counter)
    by_family_rank: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        family = str(row.get("predicate_family"))
        label_status = str(row.get("label_match_status"))
        rank_band = str(row.get("rank_band"))
        predicate = str(row.get("predicate_label"))
        by_family[family][label_status] += 1
        by_rank_band[rank_band][label_status] += 1
        by_match[label_status][family] += 1
        by_predicate[predicate][label_status] += 1
        by_family_rank[family][rank_band] += 1
        by_hint[str(row.get("machine_hint"))] += 1
        for reason in row.get("reason_codes") or []:
            by_reason[str(reason)] += 1
    return {
        "rows": len(rows),
        "by_family_label": serial_nested_counter(by_family),
        "by_rank_band_label": serial_nested_counter(by_rank_band),
        "by_label_family": serial_nested_counter(by_match),
        "by_predicate_label": serial_nested_counter(by_predicate),
        "by_family_rank_band": serial_nested_counter(by_family_rank),
        "reason_code_counts": serial_counter(by_reason),
        "machine_hint_counts": serial_counter(by_hint),
    }


def audit_question(row: dict[str, Any]) -> str:
    kind = row.get("queue_kind")
    family = row.get("predicate_family")
    label_status = row.get("label_match_status")
    if kind == "HL":
        if label_status == "pair_has_other_predicate":
            return "semantic relation is high-ranked but geometry contradicts it; check if GT predicate is a better relation for the same pair"
        return "semantic relation is high-ranked but geometry contradicts it; check object pair, support/vertical witness, and annotation"
    if label_status == "exact_match":
        return "GT relation is geometry-supported but source ranks it low; check if this is true semantic underconfidence"
    if label_status == "family_match":
        return "same-family GT exists and geometry is satisfied; check predicate granularity or ontology mismatch"
    if label_status == "pair_has_other_predicate":
        return "same pair has another GT predicate and geometry is satisfied; check if multiple relation labels should coexist"
    if family == "proximity":
        return "no GT pair but proximity is geometry-supported; check dense relation or annotation sparsity"
    return "no GT pair but geometry is supported; check missed relation, object-pair validity, or geometry artifact"


def preliminary_bucket(row: dict[str, Any]) -> str:
    kind = row.get("queue_kind")
    family = row.get("predicate_family")
    label_status = row.get("label_match_status")
    if kind == "HL":
        if label_status == "pair_has_other_predicate":
            return "overconfidence_wrong_predicate_or_ontology"
        return "overconfidence_geometry_contradiction"
    if label_status == "exact_match":
        return "underconfidence_exact_gt"
    if label_status == "family_match":
        return "ontology_or_granularity_candidate"
    if label_status == "pair_has_other_predicate":
        return "multi_relation_or_wrong_predicate_candidate"
    if family == "proximity":
        return "dense_proximity_or_annotation_sparsity"
    return "annotation_sparsity_or_geometry_artifact_candidate"


def add_seed_rows(
    seed: list[dict[str, Any]],
    seen: set[str],
    rows: list[dict[str, Any]],
    sample_reason: str,
    limit: int,
) -> int:
    added = 0
    for row in sorted(rows, key=queue_sort_key):
        if added >= limit:
            break
        key = row_key(row)
        if key in seen:
            continue
        seen.add(key)
        seed.append(make_seed_row(row, sample_reason))
        added += 1
    return added


def make_seed_row(row: dict[str, Any], sample_reason: str) -> dict[str, Any]:
    return {
        **row,
        "audit_seed": {
            "sample_reason": sample_reason,
            "preliminary_bucket": preliminary_bucket(row),
            "audit_question": audit_question(row),
            "requires_visual_or_mesh_check": True,
            "manual_fields": {
                "object_pair_valid": None,
                "predicate_visually_plausible": None,
                "geometry_witness_correct": None,
                "gt_annotation_missing_or_sparse": None,
                "ontology_or_granularity_issue": None,
                "segmentation_or_instance_issue": None,
                "final_audit_label": None,
                "notes": None,
            },
        },
    }


def filter_rows(rows: list[dict[str, Any]], predicate: Callable[[dict[str, Any]], bool]) -> list[dict[str, Any]]:
    return [row for row in rows if predicate(row)]


def build_lh_seed(lh_rows: list[dict[str, Any]], per_stratum: int) -> tuple[list[dict[str, Any]], dict[str, int]]:
    seed: list[dict[str, Any]] = []
    seen: set[str] = set()
    additions: dict[str, int] = {}

    priority_slices: list[tuple[str, Callable[[dict[str, Any]], bool], int]] = [
        (
            "lh_exact_nonproximity_high_underconfidence",
            lambda row: row.get("label_match_status") == "exact_match"
            and row.get("predicate_family") != "proximity",
            20,
        ),
        (
            "lh_exact_proximity_high_underconfidence",
            lambda row: row.get("label_match_status") == "exact_match"
            and row.get("predicate_family") == "proximity",
            10,
        ),
        (
            "lh_family_match_high_underconfidence",
            lambda row: row.get("label_match_status") == "family_match",
            20,
        ),
        (
            "lh_pair_other_support_or_vertical",
            lambda row: row.get("label_match_status") == "pair_has_other_predicate"
            and row.get("predicate_family") in {"support_contact", "relative_vertical"},
            20,
        ),
        (
            "lh_no_gt_support_or_vertical",
            lambda row: row.get("label_match_status") == "no_gt_for_pair"
            and row.get("predicate_family") in {"support_contact", "relative_vertical"},
            20,
        ),
        (
            "lh_no_gt_proximity_dense_check",
            lambda row: row.get("label_match_status") == "no_gt_for_pair"
            and row.get("predicate_family") == "proximity",
            10,
        ),
    ]

    for reason, predicate, limit in priority_slices:
        additions[reason] = add_seed_rows(seed, seen, filter_rows(lh_rows, predicate), reason, limit)

    strata: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in lh_rows:
        strata[
            (
                str(row.get("predicate_family")),
                str(row.get("label_match_status")),
                str(row.get("rank_band")),
            )
        ].append(row)
    stratum_added = 0
    for key in sorted(strata):
        reason = f"lh_stratum:{key[0]}:{key[1]}:{key[2]}"
        stratum_added += add_seed_rows(seed, seen, strata[key], reason, per_stratum)
    additions["lh_stratified_fill"] = stratum_added

    return sorted(seed, key=lambda row: (str(row["audit_seed"]["sample_reason"]), queue_sort_key(row))), additions


def build_hl_seed(hl_rows: list[dict[str, Any]], include_all_limit: int) -> tuple[list[dict[str, Any]], dict[str, int]]:
    if len(hl_rows) <= include_all_limit:
        rows = [make_seed_row(row, "hl_all_rows") for row in sorted(hl_rows, key=queue_sort_key)]
        return rows, {"hl_all_rows": len(rows)}
    rows = []
    seen: set[str] = set()
    additions = {
        "hl_top_ranked": add_seed_rows(rows, seen, hl_rows, "hl_top_ranked", include_all_limit // 2),
        "hl_high_disagreement": add_seed_rows(
            rows,
            seen,
            sorted(
                hl_rows,
                key=lambda row: (
                    -(float(row.get("disagreement_score") or 0.0)),
                    queue_sort_key(row),
                ),
            ),
            "hl_high_disagreement",
            include_all_limit - (include_all_limit // 2),
        ),
    }
    return sorted(rows, key=queue_sort_key), additions


def write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for idx, row in enumerate(rows, start=1):
            out = dict(row)
            prefix = str(out.get("queue_kind") or "Q")
            out["audit_seed"] = dict(out["audit_seed"])
            out["audit_seed"]["audit_id"] = f"{prefix}-{idx:04d}"
            handle.write(json.dumps(out, sort_keys=True, ensure_ascii=False) + "\n")


def pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.2f}%"


def make_report(summary: dict[str, Any]) -> str:
    lh = summary["queue_stratification"]["LH"]
    hl = summary["queue_stratification"]["HL"]
    factor = summary["factorized_reliability_note"]
    lines = [
        "# H002 Train RGA Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Queue Scope",
        "",
        "| Queue | Rows | Seed rows |",
        "| --- | ---: | ---: |",
        f"| HL | {hl['rows']} | {summary['audit_seed']['hl_seed_rows']} |",
        f"| LH | {lh['rows']} | {summary['audit_seed']['lh_seed_rows']} |",
        f"| total | {hl['rows'] + lh['rows']} | {summary['audit_seed']['total_seed_rows']} |",
        "",
        "HL has only 47 rows, so all HL rows are included in the audit seed. LH is sampled by priority slices and strata.",
        "",
        "## LH Label Mix",
        "",
        "| Label status | Families |",
        "| --- | --- |",
    ]
    for label_status, families in lh["by_label_family"].items():
        family_text = ", ".join(f"`{family}`={count}" for family, count in families.items())
        lines.append(f"| `{label_status}` | {family_text} |")

    lines.extend(["", "## HL Label Mix", "", "| Label status | Families |", "| --- | --- |"])
    for label_status, families in hl["by_label_family"].items():
        family_text = ", ".join(f"`{family}`={count}" for family, count in families.items())
        lines.append(f"| `{label_status}` | {family_text} |")

    lines.extend(
        [
            "",
            "## Preliminary Read",
            "",
            f"- LH exact/family rows: `{summary['preliminary_read']['lh_label_or_family_positive_rows']}`.",
            f"- LH no-GT rows: `{summary['preliminary_read']['lh_no_gt_rows']}`.",
            f"- LH proximity no-GT share: `{pct(summary['preliminary_read']['lh_no_gt_proximity_share'])}`.",
            f"- HL exact/family rows: `{summary['preliminary_read']['hl_label_or_family_positive_rows']}`.",
            "",
            "These are machine strata, not human audit labels.",
            "",
            "## Factorized Reliability Note",
            "",
            "H002 posterior should combine evidence factors, not blindly concatenate every field.",
            "",
            "```text",
            factor["formula"],
            "```",
            "",
            "- semantic evidence says whether the source believes the relation.",
            "- geometry evidence says whether the observed 3D witness supports it.",
            "- label evidence is available for train/evaluation calibration, but not always at deployment.",
            "- coverage and uncertainty modulate whether the model should trust, downweight, or abstain.",
            "",
            "## Next TODO",
            "",
            "Use `audit_seed.jsonl` to perform manual/visual audit and write `24_train_manual_audit.md`. "
            "Write a factorized reliability contract only after audit labels are available.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    hl_rows = read_jsonl(args.hl_queue)
    lh_rows = read_jsonl(args.lh_queue)
    rga_summary = read_json(args.rga_summary)
    created_at = datetime.now(timezone.utc).isoformat()

    hl_seed, hl_additions = build_hl_seed(hl_rows, args.hl_include_all_limit)
    lh_seed, lh_additions = build_lh_seed(lh_rows, args.per_stratum)
    audit_seed = sorted(hl_seed + lh_seed, key=lambda row: (str(row.get("queue_kind")), queue_sort_key(row)))

    lh_no_gt = [row for row in lh_rows if row.get("label_match_status") == "no_gt_for_pair"]
    lh_no_gt_prox = [row for row in lh_no_gt if row.get("predicate_family") == "proximity"]
    lh_label_or_family = [
        row for row in lh_rows if row.get("label_match_status") in {"exact_match", "family_match"}
    ]
    hl_label_or_family = [
        row for row in hl_rows if row.get("label_match_status") in {"exact_match", "family_match"}
    ]

    summary = {
        "schema_version": "h002_train_rga_audit_v0",
        "status": "ready",
        "created_at": created_at,
        "input_paths": {
            "hl_queue": rel_path(args.hl_queue),
            "lh_queue": rel_path(args.lh_queue),
            "rga_summary": rel_path(args.rga_summary),
        },
        "output_paths": {
            "summary": rel_path(output_dir / "train_rga_audit_summary.json"),
            "audit_seed": rel_path(output_dir / "audit_seed.jsonl"),
            "hl_seed": rel_path(output_dir / "hl_seed.jsonl"),
            "lh_seed": rel_path(output_dir / "lh_seed.jsonl"),
            "report": rel_path(output_dir / "report.md"),
        },
        "source_rga": {
            "rga_hl_at_100": rga_summary["metrics_by_k"]["100"]["high_semantic"]["rga_hl_at_100"],
            "rga_lh_tail_at_100": rga_summary["metrics_by_k"]["100"]["low_semantic_tail"]["rga_lh_tail_at_100"],
            "top100_coverage": rga_summary["metrics_by_k"]["100"]["high_semantic"]["rga_coverage_at_100"],
            "tail_gt100_coverage": rga_summary["metrics_by_k"]["100"]["low_semantic_tail"]["rga_tail_coverage_at_100"],
        },
        "queue_stratification": {
            "HL": count_rows(hl_rows),
            "LH": count_rows(lh_rows),
        },
        "audit_seed": {
            "policy": "all_HL_plus_priority_and_stratified_LH_v0",
            "per_stratum": args.per_stratum,
            "hl_seed_rows": len(hl_seed),
            "lh_seed_rows": len(lh_seed),
            "total_seed_rows": len(audit_seed),
            "hl_additions": hl_additions,
            "lh_additions": lh_additions,
        },
        "preliminary_read": {
            "lh_label_or_family_positive_rows": len(lh_label_or_family),
            "lh_label_or_family_positive_share": safe_rate(len(lh_label_or_family), len(lh_rows)),
            "lh_no_gt_rows": len(lh_no_gt),
            "lh_no_gt_share": safe_rate(len(lh_no_gt), len(lh_rows)),
            "lh_no_gt_proximity_rows": len(lh_no_gt_prox),
            "lh_no_gt_proximity_share": safe_rate(len(lh_no_gt_prox), len(lh_no_gt)),
            "hl_label_or_family_positive_rows": len(hl_label_or_family),
            "hl_label_or_family_positive_share": safe_rate(len(hl_label_or_family), len(hl_rows)),
            "machine_interpretation": (
                "LH contains a substantial exact/family-positive subset, but most LH rows are no-GT "
                "or same-pair-other-predicate candidates. Manual audit is required before treating "
                "LH as promotion evidence."
            ),
        },
        "factorized_reliability_note": {
            "formula": (
                "P(R_e=1 | S_e, L_e, G_e, C_e, U_e) ∝ "
                "ψ_sem(R_e,S_e) ψ_label(R_e,L_e) ψ_geom(R_e,G_e) "
                "ψ_cov(R_e,C_e) ψ_unc(R_e,U_e)"
            ),
            "logit_form": (
                "logit P(R_e=1) = β0 + f_sem(S_e) + f_label(L_e) + "
                "f_geom(G_e) + f_cov(C_e) + f_unc(U_e) + f_interact(S_e,G_e,C_e)"
            ),
            "boundary": (
                "Label evidence is a train/evaluation calibration signal when GT or audit labels are "
                "available. For deployment on unlabeled graphs, L_e must be absent, predicted, or replaced "
                "by weak/audit-derived supervision."
            ),
        },
        "boundary": {
            "manual_audit_done": False,
            "visual_mesh_audit_done": False,
            "posterior_training_done": False,
            "not_paper_result": True,
        },
    }

    write_json(output_dir / "train_rga_audit_summary.json", summary)
    write_jsonl(output_dir / "hl_seed.jsonl", hl_seed)
    write_jsonl(output_dir / "lh_seed.jsonl", lh_seed)
    write_jsonl(output_dir / "audit_seed.jsonl", audit_seed)
    (output_dir / "report.md").write_text(make_report(summary), encoding="utf-8")

    print(
        f"status=ready hl={len(hl_rows)} lh={len(lh_rows)} "
        f"seed={len(audit_seed)} output={output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
