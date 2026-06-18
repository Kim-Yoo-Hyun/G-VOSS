#!/usr/bin/env python3
"""Train-only shortcut controls for H002 revised factor posterior."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import factor_smoke as smoke
import full_train_independent_revised_factor_smoke as revised


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_ROWS = RGA_ROOT / "independent_revised_factor_dataset_codex_ver/revised_factor_rows.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_revised_factor_shortcut_controls_codex_ver"

BASE_VIEW = "semantic_plus_geometry"
SOURCE_VIEW = "D4_coverage_uncertainty_shrinkage"
CONTROL_L2 = {
    SOURCE_VIEW: 0.32,
    "D4_raw_witness_shuffle_global": 0.32,
    "D4_raw_witness_shuffle_within_family": 0.32,
    "D4_no_explicit_family_indicators": 0.30,
    "D4_no_typed_family_interaction": 0.24,
}
CONTROL_VIEWS = [
    SOURCE_VIEW,
    "D4_raw_witness_shuffle_global",
    "D4_raw_witness_shuffle_within_family",
    "D4_no_explicit_family_indicators",
    "D4_no_typed_family_interaction",
]
RAW_WITNESS_PREFIXES = (
    "raw_",
    "support_contact_x_",
    "relative_vertical_x_",
)
FAMILY_INTERACTION_PREFIXES = (
    "family_",
    "support_contact_x_",
    "relative_vertical_x_",
)
FAMILY_INTERACTION_KEYS = {
    "predicate_family",
    "support_contact_gate",
    "relative_vertical_gate",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, default=DEFAULT_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--epochs", type=int, default=1500)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--base-l2", type=float, default=0.03)
    parser.add_argument("--seed", type=int, default=20260618)
    return parser.parse_args()


def rel_path(path: Path | None) -> str | None:
    if path is None:
        return None
    path = smoke.as_abs(path)
    try:
        return str(path.relative_to(smoke.REPO_ROOT))
    except ValueError:
        return str(path)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def clone_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return json.loads(json.dumps(rows))


def feature_keys(rows: list[dict[str, Any]], view: str) -> list[str]:
    keys: set[str] = set()
    for row in rows:
        keys.update(row["baseline_inputs"][view].keys())
    return sorted(keys)


def is_raw_witness_key(key: str) -> bool:
    return key.startswith(RAW_WITNESS_PREFIXES)


def is_explicit_family_key(key: str) -> bool:
    return key == "predicate_family" or key.startswith("family_")


def is_family_interaction_key(key: str) -> bool:
    return key in FAMILY_INTERACTION_KEYS or key.startswith(FAMILY_INTERACTION_PREFIXES)


def add_view_without_keys(
    rows: list[dict[str, Any]],
    *,
    source_view: str,
    target_view: str,
    drop_key: Callable[[str], bool],
) -> None:
    for row in rows:
        source = row["baseline_inputs"][source_view]
        row["baseline_inputs"][target_view] = {
            key: value for key, value in source.items() if not drop_key(key)
        }


def grouped_indices(rows: list[dict[str, Any]], group_key: Callable[[dict[str, Any]], str]) -> list[list[int]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        groups[group_key(row)].append(idx)
    return [groups[key] for key in sorted(groups)]


def deranged(indices: list[int], rng: random.Random) -> list[int]:
    if len(indices) <= 1:
        return list(indices)
    donors = list(indices)
    rng.shuffle(donors)
    if any(dst == src for dst, src in zip(indices, donors)):
        donors = donors[1:] + donors[:1]
    return donors


def shuffle_feature_blocks(
    rows: list[dict[str, Any]],
    *,
    view: str,
    keys: list[str],
    groups: list[list[int]],
    seed: int,
) -> dict[str, Any]:
    rng = random.Random(seed)
    original_blocks = {
        idx: {key: rows[idx]["baseline_inputs"][view].get(key) for key in keys}
        for idx in range(len(rows))
    }
    changed_rows = 0
    singleton_groups = 0
    for indices in groups:
        if len(indices) <= 1:
            singleton_groups += 1
            continue
        donors = deranged(indices, rng)
        for dst, src in zip(indices, donors):
            if dst != src:
                changed_rows += 1
            for key in keys:
                if key in rows[dst]["baseline_inputs"][view]:
                    rows[dst]["baseline_inputs"][view][key] = original_blocks[src][key]
    return {
        "view": view,
        "shuffled_feature_count": len(keys),
        "groups": len(groups),
        "singleton_groups": singleton_groups,
        "changed_rows": changed_rows,
        "unchanged_rows": len(rows) - changed_rows,
    }


def add_shuffle_view(
    rows: list[dict[str, Any]],
    *,
    target_view: str,
    group_key: Callable[[dict[str, Any]], str],
    seed: int,
) -> dict[str, Any]:
    for row in rows:
        row["baseline_inputs"][target_view] = dict(row["baseline_inputs"][SOURCE_VIEW])
    keys = [key for key in feature_keys(rows, target_view) if is_raw_witness_key(key)]
    return shuffle_feature_blocks(
        rows,
        view=target_view,
        keys=keys,
        groups=grouped_indices(rows, group_key),
        seed=seed,
    )


def enrich_rows(rows: list[dict[str, Any]], seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    enriched = clone_rows(rows)
    controls = [
        add_shuffle_view(
            enriched,
            target_view="D4_raw_witness_shuffle_global",
            group_key=lambda _row: "all",
            seed=seed,
        ),
        add_shuffle_view(
            enriched,
            target_view="D4_raw_witness_shuffle_within_family",
            group_key=lambda row: str(row["identity"]["predicate_family"]),
            seed=seed + 17,
        ),
    ]
    add_view_without_keys(
        enriched,
        source_view=SOURCE_VIEW,
        target_view="D4_no_explicit_family_indicators",
        drop_key=is_explicit_family_key,
    )
    add_view_without_keys(
        enriched,
        source_view=SOURCE_VIEW,
        target_view="D4_no_typed_family_interaction",
        drop_key=is_family_interaction_key,
    )
    return enriched, controls


def select_rows(rows: list[dict[str, Any]], setting: str) -> list[dict[str, Any]]:
    if setting == "all_families":
        return list(rows)
    if setting == "support_vertical_only":
        return [
            row
            for row in rows
            if row["identity"]["predicate_family"] in {"support_contact", "relative_vertical"}
        ]
    if setting == "support_contact_only":
        return [row for row in rows if row["identity"]["predicate_family"] == "support_contact"]
    if setting == "relative_vertical_only":
        return [row for row in rows if row["identity"]["predicate_family"] == "relative_vertical"]
    if setting == "proximity_only":
        return [row for row in rows if row["identity"]["predicate_family"] == "proximity"]
    raise ValueError(f"unknown setting: {setting}")


def target_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(smoke.target_y(row) for row in rows)
    family_counts = Counter(str(row["identity"]["predicate_family"]) for row in rows)
    return {
        "rows": len(rows),
        "positive": counts[1],
        "negative": counts[0],
        "scan_count": len({str(row["identity"]["scan_id"]) for row in rows}),
        "predicate_family_counts": dict(sorted(family_counts.items())),
    }


def compare(metric_rows: list[dict[str, Any]], left: str, right: str = BASE_VIEW) -> dict[str, Any]:
    by_name = {row["name"]: row["metrics"] for row in metric_rows}
    left_metrics = by_name[left]
    right_metrics = by_name[right]

    def delta(key: str) -> float | None:
        if left_metrics.get(key) is None or right_metrics.get(key) is None:
            return None
        return left_metrics[key] - right_metrics[key]

    return {
        "left": left,
        "right": right,
        "delta": {
            "auroc": delta("auroc"),
            "auprc": delta("auprc"),
            "brier": delta("brier"),
            "ece_5bin": delta("ece_5bin"),
            "accuracy_at_0_5": delta("accuracy_at_0_5"),
        },
    }


def evaluate_setting(
    rows: list[dict[str, Any]],
    *,
    setting: str,
    args: argparse.Namespace,
) -> dict[str, Any]:
    if len({smoke.target_y(row) for row in rows}) != 2:
        return {
            "setting": setting,
            "target_summary": target_summary(rows),
            "skipped": True,
            "skip_reason": "single_class_target",
        }

    score_by_view: dict[str, list[float]] = {}
    feature_summaries: dict[str, dict[str, Any]] = {}
    kinds: dict[str, str] = {BASE_VIEW: "baseline"}

    base_probs, base_summary = revised.train_predict_grouped_baseline(
        rows,
        BASE_VIEW,
        folds=args.folds,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        l2=args.base_l2,
    )
    score_by_view[BASE_VIEW] = base_probs
    feature_summaries[BASE_VIEW] = base_summary

    for view in CONTROL_VIEWS:
        revised.REVISED_L2[view] = CONTROL_L2[view]
        probs, summary = revised.train_predict_grouped_offset(
            rows,
            view,
            folds=args.folds,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            base_l2=args.base_l2,
        )
        score_by_view[view] = probs
        feature_summaries[view] = summary
        if view == SOURCE_VIEW:
            kinds[view] = "original_revised_offset"
        elif "shuffle" in view:
            kinds[view] = "raw_witness_shuffle_control"
        else:
            kinds[view] = "family_ablation_control"

    metric_rows = []
    for view, probs in score_by_view.items():
        metric = revised.metric_record(kinds[view], view, rows, probs)
        metric["setting"] = setting
        metric_rows.append(metric)

    comparisons = []
    for view in CONTROL_VIEWS:
        record = compare(metric_rows, view)
        record["setting"] = setting
        comparisons.append(record)

    transfer_rows = revised.threshold_transfer(rows, score_by_view, reference_view=BASE_VIEW)
    for row in transfer_rows:
        row["setting"] = setting

    slice_rows = []
    for slice_name in ["predicate_family", "direction_bin", "coverage_bin"]:
        for row in revised.slice_metrics(rows, score_by_view, slice_name):
            row["setting"] = setting
            slice_rows.append(row)

    return {
        "setting": setting,
        "target_summary": target_summary(rows),
        "skipped": False,
        "feature_summaries": feature_summaries,
        "metric_rows": metric_rows,
        "comparisons": comparisons,
        "threshold_transfer": transfer_rows,
        "slice_metrics": slice_rows,
        "score_by_view": score_by_view,
    }


def flatten_metric_rows(setting_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for result in setting_results:
        if result.get("skipped"):
            continue
        for row in result["metric_rows"]:
            metrics = row["metrics"]
            rows.append(
                {
                    "setting": row["setting"],
                    "kind": row["kind"],
                    "view": row["name"],
                    "rows": metrics["rows"],
                    "positive": metrics["positive"],
                    "negative": metrics["negative"],
                    "auroc": metrics["auroc"],
                    "auprc": metrics["auprc"],
                    "brier": metrics["brier"],
                    "ece_5bin": metrics["ece_5bin"],
                    "accuracy_at_0_5": metrics["accuracy_at_0_5"],
                }
            )
    return rows


def flatten_comparisons(setting_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for result in setting_results:
        if result.get("skipped"):
            continue
        for row in result["comparisons"]:
            rows.append(
                {
                    "setting": row["setting"],
                    "left": row["left"],
                    "right": row["right"],
                    "delta_auroc": row["delta"]["auroc"],
                    "delta_auprc": row["delta"]["auprc"],
                    "delta_brier": row["delta"]["brier"],
                    "delta_ece_5bin": row["delta"]["ece_5bin"],
                    "delta_accuracy_at_0_5": row["delta"]["accuracy_at_0_5"],
                }
            )
    return rows


def flatten_threshold_transfer(setting_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for result in setting_results:
        if result.get("skipped"):
            continue
        rows.extend(result["threshold_transfer"])
    return rows


def flatten_slice_metrics(setting_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for result in setting_results:
        if result.get("skipped"):
            continue
        for row in result["slice_metrics"]:
            metrics = row["metrics"]
            rows.append(
                {
                    "setting": row["setting"],
                    "slice_name": row["slice_name"],
                    "slice_value": row["slice_value"],
                    "view": row["view"],
                    "single_class": row["single_class"],
                    "rows": metrics["rows"],
                    "positive": metrics["positive"],
                    "negative": metrics["negative"],
                    "auroc": metrics["auroc"],
                    "auprc": metrics["auprc"],
                    "brier": metrics["brier"],
                    "ece_5bin": metrics["ece_5bin"],
                    "accuracy_at_0_5": metrics["accuracy_at_0_5"],
                }
            )
    return rows


def prediction_rows(setting_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs = []
    for result in setting_results:
        if result.get("skipped"):
            continue
        rows = select_rows(result["_all_rows"], result["setting"])
        for view, probs in result["score_by_view"].items():
            for row, prob in zip(rows, probs):
                outputs.append(
                    {
                        "setting": result["setting"],
                        "prediction_id": row["identity"]["prediction_id"],
                        "scan_id": row["identity"]["scan_id"],
                        "predicate_label": row["identity"]["predicate_label"],
                        "predicate_family": row["identity"]["predicate_family"],
                        "view": view,
                        "posterior_target": smoke.target_y(row),
                        "probability": prob,
                    }
                )
    return outputs


def by_setting_comparison(comparisons: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    nested: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in comparisons:
        nested[row["setting"]][row["left"]] = row
    return nested


def ratio(value: float | None, denominator: float | None) -> float | None:
    if value is None or denominator is None or abs(denominator) < 1e-12:
        return None
    return value / denominator


def build_decision(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    nested = by_setting_comparison(comparisons)
    all_rows = nested["all_families"]
    scoped = nested["support_vertical_only"]
    proximity = nested["proximity_only"]
    original_delta = all_rows[SOURCE_VIEW]["delta_auprc"]
    global_shuffle_delta = all_rows["D4_raw_witness_shuffle_global"]["delta_auprc"]
    within_shuffle_delta = all_rows["D4_raw_witness_shuffle_within_family"]["delta_auprc"]
    no_family_delta = all_rows["D4_no_typed_family_interaction"]["delta_auprc"]
    scoped_original_delta = scoped[SOURCE_VIEW]["delta_auprc"]
    proximity_original_delta = proximity[SOURCE_VIEW]["delta_auprc"]

    diagnoses = []
    global_retention = ratio(global_shuffle_delta, original_delta)
    within_retention = ratio(within_shuffle_delta, original_delta)
    no_family_retention = ratio(no_family_delta, original_delta)
    if global_retention is not None and global_retention < 0.50:
        diagnoses.append("global_raw_witness_shuffle_substantially_reduces_gain")
    else:
        diagnoses.append("global_raw_witness_shuffle_retains_nontrivial_gain_risk")
    if within_retention is not None and within_retention < 0.75:
        diagnoses.append("within_family_raw_witness_alignment_matters")
    else:
        diagnoses.append("within_family_shuffle_retains_gain_shortcut_risk")
    if no_family_retention is not None and no_family_retention < 0.75:
        diagnoses.append("typed_family_interaction_adds_global_signal_but_needs_familywise_audit")
    else:
        diagnoses.append("typed_family_interaction_not_required_for_current_gain")
    if scoped_original_delta is not None and original_delta is not None and scoped_original_delta >= original_delta:
        diagnoses.append("support_vertical_scope_is_at_least_as_strong_as_all_family_scope")
    else:
        diagnoses.append("support_vertical_scope_does_not_dominate_all_family_scope")
    if proximity_original_delta is not None and proximity_original_delta < 0:
        diagnoses.append("proximity_slice_is_not_a_safe_ranking_claim")
    else:
        diagnoses.append("proximity_slice_not_negative_under_current_control")

    if (
        global_retention is not None
        and within_retention is not None
        and global_retention < 0.50
        and within_retention < 0.75
        and proximity_original_delta is not None
        and proximity_original_delta < 0
    ):
        recommendation = "scope_to_support_vertical_and_continue_label_audit"
        next_todo = "full_train_independent_revised_factor_claim_boundary"
    else:
        recommendation = "do_not_escalate_until_stronger_shortcut_or_label_controls"
        next_todo = "full_train_independent_revised_factor_label_control_audit"

    return {
        "diagnoses": diagnoses,
        "retention_ratios": {
            "global_raw_shuffle_vs_original_auprc_delta": global_retention,
            "within_family_raw_shuffle_vs_original_auprc_delta": within_retention,
            "no_typed_family_interaction_vs_original_auprc_delta": no_family_retention,
        },
        "key_deltas": {
            "all_original_delta_auprc": original_delta,
            "all_global_shuffle_delta_auprc": global_shuffle_delta,
            "all_within_family_shuffle_delta_auprc": within_shuffle_delta,
            "all_no_typed_family_interaction_delta_auprc": no_family_delta,
            "support_vertical_original_delta_auprc": scoped_original_delta,
            "proximity_original_delta_auprc": proximity_original_delta,
        },
        "recommendation": recommendation,
        "next_todo": next_todo,
    }


def compact_setting_results(setting_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact = []
    for result in setting_results:
        item = {
            "setting": result["setting"],
            "target_summary": result["target_summary"],
            "skipped": result["skipped"],
        }
        if not result["skipped"]:
            item["feature_summaries"] = result["feature_summaries"]
            item["metric_rows"] = result["metric_rows"]
            item["comparisons"] = result["comparisons"]
            item["threshold_transfer"] = result["threshold_transfer"]
        compact.append(item)
    return compact


def write_report(path: Path, summary: dict[str, Any], comparisons: list[dict[str, Any]]) -> None:
    nested = by_setting_comparison(comparisons)
    decision = summary["decision"]
    lines = [
        "# H002 Full-Train Independent Revised Factor Shortcut Controls",
        "",
        "## Boundary",
        "",
        "- Split: Open3DSG train-only.",
        "- validation/test는 사용하지 않았다.",
        "- label은 `(codex_ver_full_train_independent)` bootstrap label이다.",
        "- multi-view는 model input이 아니다.",
        "- 이 결과는 paper-level claim이 아니라 hypothesis-stage shortcut control이다.",
        "",
        "## Key Result",
        "",
        "| Setting | View | dAUPRC vs SG | dBrier vs SG |",
        "| --- | --- | ---: | ---: |",
    ]
    selected_settings = [
        "all_families",
        "support_vertical_only",
        "proximity_only",
    ]
    selected_views = [
        SOURCE_VIEW,
        "D4_raw_witness_shuffle_global",
        "D4_raw_witness_shuffle_within_family",
        "D4_no_typed_family_interaction",
    ]
    for setting in selected_settings:
        for view in selected_views:
            row = nested[setting][view]
            lines.append(
                f"| `{setting}` | `{view}` | "
                f"{row['delta_auprc']:+.4f} | {row['delta_brier']:+.4f} |"
            )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Recommendation: `{decision['recommendation']}`",
            f"- Next TODO: `{decision['next_todo']}`",
            "",
            "Diagnoses:",
            "",
        ]
    )
    for item in decision["diagnoses"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "Retention ratios:",
            "",
        ]
    )
    for key, value in decision["retention_ratios"].items():
        formatted = "null" if value is None else f"{value:.4f}"
        lines.append(f"- `{key}`: {formatted}")
    lines.extend(
        [
            "",
            "## Output Files",
            "",
            "```text",
            summary["output_paths"]["summary_json"],
            summary["output_paths"]["report_md"],
            summary["output_paths"]["control_metrics_csv"],
            summary["output_paths"]["control_comparisons_csv"],
            summary["output_paths"]["threshold_transfer_csv"],
            summary["output_paths"]["slice_metrics_csv"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = smoke.read_jsonl(args.rows)
    enriched, shuffle_controls = enrich_rows(rows, args.seed)
    settings = [
        "all_families",
        "support_vertical_only",
        "support_contact_only",
        "relative_vertical_only",
        "proximity_only",
    ]
    setting_results = []
    for setting in settings:
        selected = select_rows(enriched, setting)
        result = evaluate_setting(selected, setting=setting, args=args)
        result["_all_rows"] = enriched
        setting_results.append(result)

    metric_rows = flatten_metric_rows(setting_results)
    comparison_rows = flatten_comparisons(setting_results)
    threshold_rows = flatten_threshold_transfer(setting_results)
    slice_rows = flatten_slice_metrics(setting_results)
    predictions = prediction_rows(setting_results)
    decision = build_decision(comparison_rows)

    output_dir = smoke.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "summary_json": output_dir / "summary.json",
        "report_md": output_dir / "report.md",
        "control_metrics_csv": output_dir / "control_metrics.csv",
        "control_comparisons_csv": output_dir / "control_comparisons.csv",
        "threshold_transfer_csv": output_dir / "threshold_transfer.csv",
        "slice_metrics_csv": output_dir / "slice_metrics.csv",
        "predictions_jsonl": output_dir / "predictions.jsonl",
    }
    summary = {
        "schema_version": "h002_full_train_independent_revised_factor_shortcut_controls_v1",
        "status": "full_train_independent_revised_factor_shortcut_controls_ready",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "validation_used": False,
        "input": {
            "rows": rel_path(args.rows),
            "source_view": SOURCE_VIEW,
            "base_view": BASE_VIEW,
            "target_mode": revised.TARGET_MODE,
        },
        "hyperparameters": {
            "folds": args.folds,
            "epochs": args.epochs,
            "learning_rate": args.learning_rate,
            "base_l2": args.base_l2,
            "control_l2": CONTROL_L2,
            "seed": args.seed,
        },
        "shuffle_controls": shuffle_controls,
        "setting_results": compact_setting_results(setting_results),
        "decision": decision,
        "claim_boundary": {
            "allowed": (
                "Train-only shortcut controls can be used to decide whether the revised factor "
                "posterior should be scoped to support_contact/relative_vertical before stronger labels."
            ),
            "blocked": (
                "Paper-level posterior improvement remains blocked until independent labels and "
                "Dockerized paper experiments are available."
            ),
        },
        "next_todo": decision["next_todo"],
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
    }

    smoke.write_json(output_paths["summary_json"], summary)
    write_report(output_paths["report_md"], summary, comparison_rows)
    write_csv(output_paths["control_metrics_csv"], metric_rows)
    write_csv(output_paths["control_comparisons_csv"], comparison_rows)
    write_csv(output_paths["threshold_transfer_csv"], threshold_rows)
    write_csv(output_paths["slice_metrics_csv"], slice_rows)
    smoke.write_jsonl(output_paths["predictions_jsonl"], predictions)

    print(
        "status={status} validation_used={validation_used} "
        "all_d4_d_auprc={all_d4:+.4f} global_shuffle_retention={global_retention:.4f} "
        "within_shuffle_retention={within_retention:.4f} next={next_todo}".format(
            status=summary["status"],
            validation_used=summary["validation_used"],
            all_d4=decision["key_deltas"]["all_original_delta_auprc"],
            global_retention=decision["retention_ratios"]["global_raw_shuffle_vs_original_auprc_delta"],
            within_retention=decision["retention_ratios"]["within_family_raw_shuffle_vs_original_auprc_delta"],
            next_todo=summary["next_todo"],
        )
    )


if __name__ == "__main__":
    main()
