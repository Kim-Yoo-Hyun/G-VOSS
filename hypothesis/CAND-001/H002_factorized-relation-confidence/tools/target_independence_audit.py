#!/usr/bin/env python3
"""Audit target independence for H002 rank-matched codex labels."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_INPUT_DIR = RGA_ROOT / "rank_matched_target_codex_real_assumption"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "target_independence_audit_codex_real_assumption"

TARGET_ROW_FILES = {
    "mined_rank_matched_gap50_codex_ver": "mined_rank_matched_gap50_codex_ver_rows.jsonl",
    "combined_rank_matched_gap50_codex_ver": "combined_rank_matched_gap50_codex_ver_rows.jsonl",
}

METADATA_FIELDS = [
    "final_controlled_label",
    "proposed_review_stratum",
    "confidence",
    "rank_band",
    "predicate_family",
    "predicate_label",
    "geometry_status",
    "rank_matched_pair_scope",
]

RAW_FEATURES = {
    "negative_rank_only_raw": {
        "description": "1 - semantic_score_norm; high means source underconfidence",
        "source": "semantic",
    },
    "semantic_score_norm_raw": {
        "description": "semantic_score_norm; high means source semantic confidence",
        "source": "semantic",
    },
    "p_geom_valid_raw": {
        "description": "p_geom_valid_imputed_neutral",
        "source": "geometry",
    },
    "consistency_score_raw": {
        "description": "geometry consistency_score",
        "source": "geometry",
    },
    "negative_geometry_residual_raw": {
        "description": "1 - geometry_residual_proxy",
        "source": "geometry",
    },
    "underconfidence_raw": {
        "description": "underconfidence_score",
        "source": "uncertainty/rank-derived",
    },
    "absolute_disagreement_raw": {
        "description": "absolute_disagreement",
        "source": "uncertainty/rank-derived",
    },
    "negative_semantic_geometry_disagreement_raw": {
        "description": "1 - semantic_geometry_disagreement_score",
        "source": "uncertainty/rank-derived",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def feature_score(row: dict[str, Any], feature_name: str) -> float:
    features = row["baseline_inputs"]["factorized_reliability_posterior"]
    semantic = smoke.safe_float(features.get("semantic_score_norm"), 0.0)
    p_geom = smoke.safe_float(features.get("p_geom_valid_imputed_neutral"), 0.5)
    if feature_name == "negative_rank_only_raw":
        return 1.0 - semantic
    if feature_name == "semantic_score_norm_raw":
        return semantic
    if feature_name == "p_geom_valid_raw":
        return p_geom
    if feature_name == "consistency_score_raw":
        return smoke.safe_float(features.get("consistency_score"), 0.0)
    if feature_name == "negative_geometry_residual_raw":
        return 1.0 - smoke.safe_float(features.get("geometry_residual_proxy"), 1.0)
    if feature_name == "underconfidence_raw":
        return smoke.safe_float(features.get("underconfidence_score"), 0.0)
    if feature_name == "absolute_disagreement_raw":
        return smoke.safe_float(features.get("absolute_disagreement"), 0.0)
    if feature_name == "negative_semantic_geometry_disagreement_raw":
        return 1.0 - smoke.safe_float(features.get("semantic_geometry_disagreement_score"), 0.0)
    raise KeyError(feature_name)


def feature_summary(target_mode: str, rows: list[dict[str, Any]], pair_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    row_by_id = {str(row["identity"]["prediction_id"]): row for row in rows}
    target_pairs = [
        record for record in pair_records
        if record.get("target_mode") == target_mode
        and record.get("included_in_smoke") is True
    ]
    output = []
    ys = [smoke.target_y(row) for row in rows]
    for feature_name, spec in RAW_FEATURES.items():
        scores = [feature_score(row, feature_name) for row in rows]
        metrics = smoke.metrics(ys, scores)
        y0 = [score for y, score in zip(ys, scores) if y == 0]
        y1 = [score for y, score in zip(ys, scores) if y == 1]
        wins = []
        deltas = []
        for pair in target_pairs:
            positive = row_by_id[str(pair["positive_prediction_id"])]
            negative = row_by_id[str(pair["negative_prediction_id"])]
            pos_score = feature_score(positive, feature_name)
            neg_score = feature_score(negative, feature_name)
            deltas.append(pos_score - neg_score)
            if pos_score > neg_score:
                wins.append(1.0)
            elif pos_score == neg_score:
                wins.append(0.5)
            else:
                wins.append(0.0)
        output.append(
            {
                "target_mode": target_mode,
                "feature": feature_name,
                "source": spec["source"],
                "description": spec["description"],
                "rows": len(rows),
                "positive": sum(ys),
                "negative": len(rows) - sum(ys),
                "mean_y0": sum(y0) / len(y0) if y0 else None,
                "mean_y1": sum(y1) / len(y1) if y1 else None,
                "mean_y1_minus_y0": (sum(y1) / len(y1) - sum(y0) / len(y0)) if y0 and y1 else None,
                "auroc": metrics["auroc"],
                "auprc": metrics["auprc"],
                "brier": metrics["brier"],
                "pair_count": len(target_pairs),
                "pairwise_accuracy": sum(wins) / len(wins) if wins else None,
                "mean_pair_delta_pos_minus_neg": sum(deltas) / len(deltas) if deltas else None,
            }
        )
    return output


def metadata_summary(target_mode: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for field in METADATA_FIELDS:
        counts: dict[str, Counter[int]] = defaultdict(Counter)
        for row in rows:
            value = str(row["target"].get(field))
            counts[value][smoke.target_y(row)] += 1
        pure_values = 0
        mixed_values = 0
        max_value_purity_mass = 0
        for counter in counts.values():
            total = counter[0] + counter[1]
            majority = max(counter[0], counter[1])
            max_value_purity_mass += majority
            if counter[0] and counter[1]:
                mixed_values += 1
            else:
                pure_values += 1
        output.append(
            {
                "target_mode": target_mode,
                "field": field,
                "unique_values": len(counts),
                "pure_values": pure_values,
                "mixed_values": mixed_values,
                "row_majority_purity": max_value_purity_mass / len(rows) if rows else None,
                "counts": {
                    value: {"negative": counter[0], "positive": counter[1]}
                    for value, counter in sorted(counts.items())
                },
            }
        )
    return output


def pair_gap_summary(target_mode: str, pair_records: list[dict[str, Any]]) -> dict[str, Any]:
    pairs = [
        record for record in pair_records
        if record.get("target_mode") == target_mode
        and record.get("included_in_smoke") is True
    ]
    gaps = [float(record["rank_gap_abs"]) for record in pairs]
    positive_worse_rank = [
        1.0 if float(record["positive_rank_in_context"]) > float(record["negative_rank_in_context"]) else 0.0
        for record in pairs
    ]
    return {
        "target_mode": target_mode,
        "pair_count": len(pairs),
        "mean_rank_gap_abs": sum(gaps) / len(gaps) if gaps else None,
        "max_rank_gap_abs": max(gaps) if gaps else None,
        "positive_has_worse_rank_share": sum(positive_worse_rank) / len(positive_worse_rank) if positive_worse_rank else None,
    }


def target_overlap_summary(rows_by_target: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    id_sets = {
        target_mode: {str(row["identity"]["prediction_id"]) for row in rows}
        for target_mode, rows in rows_by_target.items()
    }
    target_modes = sorted(id_sets)
    pairwise = []
    for idx, left in enumerate(target_modes):
        for right in target_modes[idx + 1:]:
            intersection = id_sets[left] & id_sets[right]
            union = id_sets[left] | id_sets[right]
            pairwise.append(
                {
                    "left": left,
                    "right": right,
                    "left_rows": len(id_sets[left]),
                    "right_rows": len(id_sets[right]),
                    "intersection": len(intersection),
                    "jaccard": len(intersection) / len(union) if union else None,
                }
            )
    return {"pairwise": pairwise}


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Target Independence Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage audit.",
        "- `(codex_ver)` is treated as real label by user-directed assumption.",
        "- No validation/test rows are used.",
        "- This audit does not train a new posterior.",
        "- `V_mv_e` is not used as model input.",
        "",
        "## Verdict",
        "",
        summary["decision"],
        "",
        "## Pair Rank Direction",
        "",
        "| Target | Pairs | Mean gap | Max gap | Positive has worse rank share |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["pair_gap_summaries"]:
        lines.append(
            f"| `{row['target_mode']}` | {row['pair_count']} | {fmt(row['mean_rank_gap_abs'])} | "
            f"{fmt(row['max_rank_gap_abs'])} | {fmt(row['positive_has_worse_rank_share'])} |"
        )

    lines.extend(
        [
            "",
            "## Raw Feature Separability",
            "",
            "| Target | Feature | Source | Mean y1-y0 | AUROC | AUPRC | Pairwise accuracy |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["feature_summaries"]:
        lines.append(
            f"| `{row['target_mode']}` | `{row['feature']}` | `{row['source']}` | "
            f"{fmt(row['mean_y1_minus_y0'])} | {fmt(row['auroc'])} | "
            f"{fmt(row['auprc'])} | {fmt(row['pairwise_accuracy'])} |"
        )

    lines.extend(
        [
            "",
            "## Metadata Purity",
            "",
            "| Target | Field | Unique values | Pure values | Mixed values | Row-majority purity |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["metadata_summaries"]:
        lines.append(
            f"| `{row['target_mode']}` | `{row['field']}` | {row['unique_values']} | "
            f"{row['pure_values']} | {row['mixed_values']} | {fmt(row['row_majority_purity'])} |"
        )

    lines.extend(
        [
            "",
            "## Target Overlap",
            "",
            "| Left | Right | Left rows | Right rows | Intersection | Jaccard |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["target_overlap"]["pairwise"]:
        lines.append(
            f"| `{row['left']}` | `{row['right']}` | {row['left_rows']} | {row['right_rows']} | "
            f"{row['intersection']} | {fmt(row['jaccard'])} |"
        )

    lines.extend(
        [
            "",
            "## Minimum Evidence Needed",
            "",
            "- Rank-hidden independent audit labels: annotator should not see semantic rank, review stratum, or model score.",
            "- Same-rank randomized pairs: positive/negative candidate order should be randomized.",
            "- Multi-family target: at least `support_contact` plus one non-proximity family before method claim.",
            "- Separate audit fields from input features: label rationale and visual confirmation must not become deployable inputs.",
            "- Re-run residual/gated combiners only after independent labels exist.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(output_dir: Path, summary: dict[str, Any]) -> None:
    smoke.write_json(output_dir / "summary.json", summary)
    with (output_dir / "feature_summaries.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "target_mode",
                "feature",
                "source",
                "description",
                "rows",
                "positive",
                "negative",
                "mean_y0",
                "mean_y1",
                "mean_y1_minus_y0",
                "auroc",
                "auprc",
                "brier",
                "pair_count",
                "pairwise_accuracy",
                "mean_pair_delta_pos_minus_neg",
            ],
        )
        writer.writeheader()
        writer.writerows(summary["feature_summaries"])
    with (output_dir / "metadata_summaries.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "target_mode",
                "field",
                "unique_values",
                "pure_values",
                "mixed_values",
                "row_majority_purity",
            ],
        )
        writer.writeheader()
        for row in summary["metadata_summaries"]:
            writer.writerow({key: row[key] for key in writer.fieldnames})
    write_report(output_dir / "report.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_dir = smoke.as_abs(args.input_dir)
    output_dir = smoke.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    pair_records = smoke.read_jsonl(input_dir / "pair_records.jsonl")
    rows_by_target = {
        target_mode: smoke.read_jsonl(input_dir / filename)
        for target_mode, filename in TARGET_ROW_FILES.items()
    }
    feature_rows = []
    metadata_rows = []
    pair_gap_rows = []
    for target_mode, rows in rows_by_target.items():
        feature_rows.extend(feature_summary(target_mode, rows, pair_records))
        metadata_rows.extend(metadata_summary(target_mode, rows))
        pair_gap_rows.append(pair_gap_summary(target_mode, pair_records))

    negative_rank = [
        row for row in feature_rows
        if row["feature"] == "negative_rank_only_raw"
    ]
    p_geom = [
        row for row in feature_rows
        if row["feature"] == "p_geom_valid_raw"
    ]
    metadata_perfect = [
        row for row in metadata_rows
        if row["field"] in {"final_controlled_label", "proposed_review_stratum"}
        and row["row_majority_purity"] == 1.0
    ]
    rank_proxy_strong = all(
        row["pairwise_accuracy"] is not None and row["pairwise_accuracy"] >= 0.80
        for row in negative_rank
    )
    pgeom_weak = all(
        row["pairwise_accuracy"] is not None and row["pairwise_accuracy"] <= 0.60
        for row in p_geom
    )
    if rank_proxy_strong and pgeom_weak and len(metadata_perfect) >= 4:
        status = "target_independence_not_established"
        decision = (
            "Target independence is not established. Even after rank-gap matching, "
            "positive rows tend to have worse source rank than their matched negative "
            "rows, while raw geometry validity is weak. The codex target metadata "
            "also remains perfectly aligned with the binary label, so the current "
            "target should be treated as rank/label-construction confounded."
        )
    else:
        status = "target_independence_mixed"
        decision = (
            "Target independence is mixed. Some evidence reduces rank-gap shortcuts, "
            "but the audit is not strong enough to support a posterior method claim."
        )

    summary = {
        "schema_version": "h002_target_independence_audit_v0",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "input_dir": smoke.rel_path(input_dir),
            **{
                target_mode: smoke.rel_path(input_dir / filename)
                for target_mode, filename in TARGET_ROW_FILES.items()
            },
            "pair_records": smoke.rel_path(input_dir / "pair_records.jsonl"),
        },
        "output_dir": smoke.rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "codex_ver_treated_as_real_label_by_user_assumption": True,
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "vmv_model_input_allowed": False,
        },
        "target_overlap": target_overlap_summary(rows_by_target),
        "pair_gap_summaries": pair_gap_rows,
        "feature_summaries": feature_rows,
        "metadata_summaries": metadata_rows,
        "decision": decision,
    }
    write_outputs(output_dir, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        f"status={summary['status']} feature_rows={len(summary['feature_summaries'])} "
        f"metadata_rows={len(summary['metadata_summaries'])} validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
