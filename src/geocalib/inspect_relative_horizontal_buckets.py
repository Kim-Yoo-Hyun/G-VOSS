#!/usr/bin/env python3
"""Inspect relative-horizontal coordinate-audit buckets.

This script turns the coordinate audit into threshold-free diagnostic evidence:
per-label status counts, wrong-frame gap, inverse consistency, ambiguity flags,
contradiction buckets, and representative rows. It does not implement a
verifier, does not run source metrics, and does not alter the current paper
claim.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPERIMENT_ROOT = Path("experiments/H001_geom_reliability")
DEFAULT_COORDINATE_DIR = EXPERIMENT_ROOT / "sources/relative_horizontal/coordinate_audit"
DEFAULT_OUT = EXPERIMENT_ROOT / "sources/relative_horizontal/bucket_inspection"

TARGET_LABELS = ("left", "right", "front", "behind")
FOCUS_LABELS = ("front", "behind")
COMPARISON_LABELS = ("left", "right")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                try:
                    yield line_no, json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid_jsonl:{path}:{line_no}:{exc}") from exc


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def finite_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def ratio(num: int | float, den: int | float) -> float | None:
    return round(float(num) / float(den), 4) if den else None


def compact_row(row: dict[str, Any]) -> dict[str, Any]:
    outcome = row.get("outcome", {})
    geometry = row.get("geometry", {})
    target_projection = finite_float(outcome.get("target_projection_m"))
    other_projection = finite_float(outcome.get("other_projection_m"))
    dominance_ratio = None
    if target_projection is not None and abs(target_projection) > 1e-9 and other_projection is not None:
        dominance_ratio = round(abs(other_projection) / abs(target_projection), 4)
    return {
        "gt_id": row.get("gt_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "object_id": row.get("object_id"),
        "subject_label": row.get("subject_label"),
        "object_label": row.get("object_label"),
        "predicate_label": row.get("predicate_label"),
        "strict_status": outcome.get("strict_status"),
        "sign_only_status": outcome.get("sign_only_status"),
        "sign_matches": outcome.get("sign_matches"),
        "ambiguity_flags": outcome.get("ambiguity_flags", []),
        "target_projection_m": target_projection,
        "other_projection_m": other_projection,
        "dominance_ratio_abs_other_over_target": dominance_ratio,
        "margin_m": finite_float(outcome.get("margin_m")),
        "distance_xy": finite_float(geometry.get("distance_xy")),
        "projected_overlap_max_ratio": finite_float(geometry.get("projected_overlap_max_ratio")),
        "frame_name": row.get("frame_name"),
    }


def status_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    strict = Counter(row["outcome"]["strict_status"] for row in rows)
    sign_only = Counter(row["outcome"]["sign_only_status"] for row in rows)
    flags = Counter(flag for row in rows for flag in row["outcome"].get("ambiguity_flags", []))
    combos = Counter(tuple(row["outcome"].get("ambiguity_flags", [])) for row in rows)
    strict_eligible = strict["match"] + strict["contradiction"]
    sign_eligible = sign_only["match"] + sign_only["contradiction"]
    return {
        "rows": len(rows),
        "strict_status_counts": dict(sorted(strict.items())),
        "strict_match_to_contradiction_ratio": ratio(strict["match"], strict["contradiction"]),
        "strict_purity": ratio(strict["match"], strict_eligible),
        "strict_eligible_share": ratio(strict_eligible, len(rows)),
        "sign_only_status_counts": dict(sorted(sign_only.items())),
        "sign_only_match_to_contradiction_ratio": ratio(sign_only["match"], sign_only["contradiction"]),
        "sign_only_purity": ratio(sign_only["match"], sign_eligible),
        "sign_only_eligible_share": ratio(sign_eligible, len(rows)),
        "ambiguity_flag_counts": dict(sorted(flags.items())),
        "ambiguity_combo_counts": {
            "+".join(combo) if combo else "none": count for combo, count in combos.most_common(12)
        },
    }


def top_counter(counter: Counter[Any], limit: int = 20) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for key, count in counter.most_common(limit):
        if isinstance(key, tuple):
            item = {"key": list(key), "count": count}
        else:
            item = {"key": key, "count": count}
        result.append(item)
    return result


def quantiles(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"min": None, "p25": None, "median": None, "p75": None, "max": None}
    values = sorted(values)

    def q(position: float) -> float:
        if len(values) == 1:
            return values[0]
        idx = position * (len(values) - 1)
        low = int(math.floor(idx))
        high = int(math.ceil(idx))
        if low == high:
            return values[low]
        frac = idx - low
        return values[low] * (1.0 - frac) + values[high] * frac

    return {
        "min": round(values[0], 6),
        "p25": round(q(0.25), 6),
        "median": round(q(0.50), 6),
        "p75": round(q(0.75), 6),
        "max": round(values[-1], 6),
    }


def bucket_diagnostics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    contradictions = [row for row in rows if row["outcome"]["strict_status"] == "contradiction"]
    uncertain = [row for row in rows if row["outcome"]["strict_status"] == "uncertain"]
    matches = [row for row in rows if row["outcome"]["strict_status"] == "match"]
    pair_counter = Counter((row.get("subject_label"), row.get("object_label")) for row in contradictions)
    same_label_contradictions = [
        row for row in contradictions if row.get("subject_label") == row.get("object_label")
    ]
    dominance_values: list[float] = []
    for row in rows:
        compact = compact_row(row)
        value = compact.get("dominance_ratio_abs_other_over_target")
        if isinstance(value, (float, int)) and math.isfinite(float(value)):
            dominance_values.append(float(value))
    return {
        "matches": len(matches),
        "uncertain": len(uncertain),
        "contradictions": len(contradictions),
        "contradiction_pair_top": top_counter(pair_counter, 15),
        "same_label_contradictions": len(same_label_contradictions),
        "same_label_contradiction_share": ratio(len(same_label_contradictions), len(contradictions)),
        "dominance_ratio_abs_other_over_target": quantiles(dominance_values),
        "uncertain_flag_top": top_counter(
            Counter(tuple(row["outcome"].get("ambiguity_flags", [])) for row in uncertain),
            12,
        ),
    }


def example_rows(rows: list[dict[str, Any]], *, limit_per_bucket: int) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        label = row["predicate_label"]
        status = row["outcome"]["strict_status"]
        key = f"{label}:{status}"
        if len(buckets[key]) < limit_per_bucket:
            buckets[key].append(compact_row(row))
    result: list[dict[str, Any]] = []
    for key in sorted(buckets):
        result.extend({"bucket": key, **row} for row in buckets[key])
    return result


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, manifest: dict[str, Any], summary: dict[str, Any]) -> None:
    lines = [
        "# Relative Horizontal Bucket Inspection",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Claim Boundary",
        "",
        "This inspection is threshold-free diagnostic evidence for the optional "
        "`relative_horizontal` expansion track. It does not run source metrics "
        "and does not change the current H001 paper claim.",
        "",
        "## Threshold-Free Evidence",
        "",
        markdown_table(
            ["Evidence", "Value"],
            [
                ["selected frame", summary["selected_frame"]["frame_name"]],
                ["inverse consistency", summary["selected_frame"]["inverse_consistency"]],
                ["wrong-frame gap", summary["selected_frame"]["wrong_frame_gap"]],
                ["front/behind strict match:contradiction", summary["focus"]["strict_match_to_contradiction_ratio"]],
                ["front/behind strict purity", summary["focus"]["strict_purity"]],
                ["front/behind sign-only purity", summary["focus"]["sign_only_purity"]],
                ["left/right strict purity", summary["comparison"]["strict_purity"]],
            ],
        ),
        "",
        "## Per-Label Buckets",
        "",
        markdown_table(
            [
                "Label",
                "Rows",
                "Strict match",
                "Strict uncertain",
                "Strict contradiction",
                "Strict purity",
                "Sign-only purity",
            ],
            [
                [
                    label,
                    payload["rows"],
                    payload["strict_status_counts"].get("match", 0),
                    payload["strict_status_counts"].get("uncertain", 0),
                    payload["strict_status_counts"].get("contradiction", 0),
                    payload["strict_purity"],
                    payload["sign_only_purity"],
                ]
                for label, payload in summary["by_label"].items()
            ],
        ),
        "",
        "## Front / Behind Ambiguity",
        "",
        markdown_table(
            ["Flag", "Count"],
            [[flag, count] for flag, count in summary["focus"]["ambiguity_flag_counts"].items()],
        ),
        "",
        "## Diagnostic Decision",
        "",
        f"- Recommendation: `{manifest['recommendation']['decision']}`",
        f"- Rationale: {manifest['recommendation']['rationale']}",
        "",
        "## Next Step",
        "",
        "- Do not run expanded-family VL-SAT/Open3DSG metrics yet.",
        "- If this track continues, add a targeted visual check or stronger frame metadata analysis for `front`/`behind` first.",
        "",
    ]
    ensure_dir(path.parent)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--coordinate-dir", type=Path, default=DEFAULT_COORDINATE_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--limit-per-bucket", type=int, default=5)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    coordinate_dir = args.coordinate_dir if args.coordinate_dir.is_absolute() else repo_root / args.coordinate_dir
    out = args.out if args.out.is_absolute() else repo_root / args.out
    manifest_path = coordinate_dir / "manifest.json"
    records_path = coordinate_dir / "records.jsonl"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing_coordinate_manifest:{manifest_path}")
    if not records_path.exists():
        raise FileNotFoundError(f"missing_coordinate_records:{records_path}")

    coordinate_manifest = read_json(manifest_path)
    records = [row for _, row in iter_jsonl(records_path)]
    rows_by_label = {label: [row for row in records if row["predicate_label"] == label] for label in TARGET_LABELS}
    focus_rows = [row for row in records if row["predicate_label"] in FOCUS_LABELS]
    comparison_rows = [row for row in records if row["predicate_label"] in COMPARISON_LABELS]

    by_label = {label: status_summary(rows_by_label[label]) for label in TARGET_LABELS}
    summary = {
        "selected_frame": {
            "frame_name": coordinate_manifest["selected_frame"]["frame_name"],
            "frame_family": coordinate_manifest["selected_frame"]["frame_family"],
            "wrong_frame_gap": coordinate_manifest["gate"]["wrong_frame_gap"],
            "inverse_consistency": coordinate_manifest["inverse_pair_consistency"]["inverse_consistency"],
        },
        "by_label": by_label,
        "focus": {
            **status_summary(focus_rows),
            "diagnostics": bucket_diagnostics(focus_rows),
        },
        "comparison": {
            **status_summary(comparison_rows),
            "diagnostics": bucket_diagnostics(comparison_rows),
        },
    }

    focus = summary["focus"]
    diagnostics = focus["diagnostics"]
    decision = "do_not_promote_relative_horizontal_to_main_claim"
    rationale = (
        "The selected frame shows nontrivial signal through inverse consistency and wrong-frame gap, "
        "but front/behind still has substantial contradiction and ambiguity buckets. "
        "This supports scope-boundary or appendix discussion, not expanded source metrics."
    )
    if (
        focus["strict_match_to_contradiction_ratio"] is not None
        and focus["strict_match_to_contradiction_ratio"] >= 2.0
        and focus["ambiguity_flag_counts"].get("conflicting_axis_dominates", 0) > 0
    ):
        policy_path = "possible_only_after_targeted_front_behind_visual_or_frame_metadata_check"
    else:
        policy_path = "not_defensible_without_new_frame_evidence"

    manifest = {
        "schema_version": "h001_relative_horizontal_bucket_inspection_v1",
        "status": "relative_horizontal_bucket_inspection_ready_no_metric_execution",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": {
            "current_main_claim_unchanged": True,
            "metric_evidence": False,
            "candidate_family": "relative_horizontal",
        },
        "inputs": {
            "coordinate_manifest": str(manifest_path),
            "coordinate_records": str(records_path),
        },
        "summary": {
            "records": len(records),
            "focus_labels": list(FOCUS_LABELS),
            "comparison_labels": list(COMPARISON_LABELS),
            "front_behind_contradictions": diagnostics["contradictions"],
            "front_behind_uncertain": diagnostics["uncertain"],
            "front_behind_matches": diagnostics["matches"],
            "front_behind_same_label_contradictions": diagnostics["same_label_contradictions"],
        },
        "recommendation": {
            "decision": decision,
            "policy_path": policy_path,
            "rationale": rationale,
            "next_step": "targeted_front_behind_visual_or_frame_metadata_check_if_user_wants_to_continue_expansion",
        },
    }

    examples = example_rows(focus_rows, limit_per_bucket=args.limit_per_bucket)
    ensure_dir(out)
    write_json(out / "manifest.json", manifest)
    write_json(out / "summary.json", summary)
    write_jsonl(out / "examples.jsonl", examples)
    write_report(out / "report.md", manifest, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
