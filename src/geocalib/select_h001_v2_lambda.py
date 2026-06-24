#!/usr/bin/env python3
"""Select H001_v2 soft-reranking lambda from calibration dev rows only."""

from __future__ import annotations

import argparse
import json
import math
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paths import REPO_ROOT, repo_rel


SCHEMA_VERSION = "h001_v2_lambda_selection_v1"
DEFAULT_FAMILIES = ("support_contact", "proximity", "relative_vertical")
DEFAULT_SCORES = (
    Path("archive/hypothesis_records/hypothesis/CAND-001")
    / "H001_geometry-grounded-verification/artifacts/calibration"
    / "p_geom_valid_smoke/scores.jsonl"
)
DEFAULT_OUTPUT = (
    Path("hypothesis/CAND-001/H001_v2_risk_controlled_reranking")
    / "artifacts/calibration_lambda_selection"
)
READ_ONLY_ROOTS = (
    Path("experiments/H001_geom_reliability/sources/vlsat/full_validation"),
    Path(
        "experiments/H001_geom_reliability/sources/open3dsg/full_validation/"
        "recovery_relaxed_views_min2"
    ),
    Path(
        "archive/hypothesis_records/hypothesis/CAND-001/"
        "H001_geometry-grounded-verification"
    ),
    Path("results/h001_geom_reliability"),
    Path("paper"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select lambda for H001_v2 risk-aware soft reranking."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--scores-jsonl", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--families", nargs="+", default=list(DEFAULT_FAMILIES))
    parser.add_argument("--selection-role", default="dev")
    parser.add_argument("--diagnostic-role", default="train")
    parser.add_argument("--lambda-min", type=float, default=0.0)
    parser.add_argument("--lambda-max", type=float, default=4.0)
    parser.add_argument("--lambda-step", type=float, default=0.05)
    parser.add_argument("--epsilon", type=float, default=1.0e-12)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def resolve_path(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}") from exc
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def assert_writable_output(repo_root: Path, output_dir: Path, overwrite: bool) -> None:
    output_resolved = output_dir.resolve()
    for root in READ_ONLY_ROOTS:
        root_resolved = (repo_root / root).resolve()
        try:
            output_resolved.relative_to(root_resolved)
        except ValueError:
            continue
        raise ValueError(
            "Refusing to write H001_v2 lambda outputs under read-only root: "
            f"{repo_rel(output_dir, repo_root)}"
        )
    if output_dir.exists() and any(output_dir.iterdir()):
        if not overwrite:
            raise FileExistsError(
                f"Output directory is non-empty: {repo_rel(output_dir, repo_root)}. "
                "Pass --overwrite to replace this H001_v2 lambda-selection output."
            )
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def finite_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def lambda_grid(min_value: float, max_value: float, step: float) -> list[float]:
    if min_value < 0.0:
        raise ValueError("--lambda-min must be >= 0")
    if max_value < min_value:
        raise ValueError("--lambda-max must be >= --lambda-min")
    if step <= 0:
        raise ValueError("--lambda-step must be > 0")
    count = int(round((max_value - min_value) / step))
    values = [round(min_value + i * step, 10) for i in range(count + 1)]
    if values[-1] < max_value:
        values.append(round(max_value, 10))
    return sorted(set(values))


def normalize_rows(
    raw_rows: list[dict[str, Any]],
    families: set[str],
) -> tuple[list[dict[str, Any]], list[str], Counter[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    skipped: Counter[str] = Counter()
    for index, row in enumerate(raw_rows, 1):
        family = row.get("predicate", {}).get("predicate_family")
        if family not in families:
            skipped["family_out_of_scope"] += 1
            continue
        role = row.get("role")
        p_geom_valid = finite_float(row.get("p_geom_valid"))
        geom_valid = row.get("label", {}).get("geom_valid")
        if p_geom_valid is None:
            errors.append(f"missing_p_geom_valid:{index}")
            continue
        if not 0.0 <= p_geom_valid <= 1.0:
            errors.append(f"p_geom_valid_out_of_range:{index}:{p_geom_valid}")
            continue
        if geom_valid not in (0, 1):
            errors.append(f"invalid_geom_valid:{index}:{geom_valid}")
            continue
        rows.append(
            {
                "candidate_id": row.get("candidate_id"),
                "family": family,
                "role": role,
                "geom_valid": int(geom_valid),
                "p_geom_valid": p_geom_valid,
                "scan_id": row.get("scan_id"),
                "subgraph_id": row.get("subgraph_id"),
            }
        )
    return rows, errors, skipped


def clipped(value: float, epsilon: float) -> float:
    return min(max(value, epsilon), 1.0 - epsilon)


def transformed_probability(p_geom_valid: float, lam: float, epsilon: float) -> float:
    return clipped(p_geom_valid**lam, epsilon)


def evaluate_lambda(rows: list[dict[str, Any]], lam: float, epsilon: float) -> dict[str, Any]:
    if not rows:
        return {
            "rows": 0,
            "mean_nll": None,
            "mean_brier": None,
            "accuracy_at_0_5": None,
            "positive_rate": None,
            "mean_prediction": None,
        }
    nll = 0.0
    brier = 0.0
    correct = 0
    positives = 0
    predictions: list[float] = []
    for row in rows:
        y = int(row["geom_valid"])
        p = transformed_probability(float(row["p_geom_valid"]), lam, epsilon)
        nll += -(y * math.log(p) + (1 - y) * math.log1p(-p))
        brier += (p - y) ** 2
        correct += int((p >= 0.5) == bool(y))
        positives += y
        predictions.append(p)
    return {
        "rows": len(rows),
        "lambda": lam,
        "mean_nll": nll / len(rows),
        "mean_brier": brier / len(rows),
        "accuracy_at_0_5": correct / len(rows),
        "positive_rate": positives / len(rows),
        "mean_prediction": sum(predictions) / len(predictions),
    }


def family_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for family in sorted({row["family"] for row in rows}):
        family_rows = [row for row in rows if row["family"] == family]
        valid = sum(int(row["geom_valid"]) for row in family_rows)
        p_values = [float(row["p_geom_valid"]) for row in family_rows]
        summary[family] = {
            "rows": len(family_rows),
            "geom_valid": valid,
            "geom_invalid": len(family_rows) - valid,
            "mean_p_geom_valid": sum(p_values) / len(p_values) if p_values else None,
            "min_p_geom_valid": min(p_values) if p_values else None,
            "max_p_geom_valid": max(p_values) if p_values else None,
        }
    return summary


def select_lambda(
    selection_rows: list[dict[str, Any]],
    grid: list[float],
    epsilon: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    curve = [evaluate_lambda(selection_rows, lam, epsilon) for lam in grid]
    valid_curve = [row for row in curve if row["mean_nll"] is not None]
    if not valid_curve:
        return {"status": "lambda_selection_failed_no_rows", "lambda_star": None}, curve
    selected = min(
        valid_curve,
        key=lambda row: (
            float(row["mean_nll"]),
            float(row["mean_brier"]),
            abs(float(row["lambda"]) - 1.0),
            float(row["lambda"]),
        ),
    )
    policy = {
        "schema_version": SCHEMA_VERSION,
        "status": "ready",
        "lambda_star": selected["lambda"],
        "selection_objective": "minimize_dev_negative_log_likelihood_of_p_geom_valid_power_lambda",
        "score_formula": "semantic_score * p_geom_valid ** lambda_star",
        "selection_metrics": selected,
    }
    return policy, curve


def report_markdown(
    policy: dict[str, Any],
    manifest: dict[str, Any],
    diagnostics: dict[str, Any],
) -> str:
    lines = [
        "# H001_v2 Lambda Selection",
        "",
        f"Created at: `{manifest['created_at']}`",
        f"Status: `{policy['status']}`",
        "",
        "## Protocol",
        "",
        "- Select `lambda` from calibration score rows only.",
        "- Use `role == dev` as the selection split.",
        "- Keep `role == train` as diagnostic provenance only.",
        "- Do not read VL-SAT/Open3DSG source metrics during selection.",
        "- Apply the selected value as `score = semantic_score * p_geom_valid^lambda`.",
        "",
        "## Selected Policy",
        "",
        f"- lambda*: `{policy.get('lambda_star')}`",
        f"- objective: `{policy.get('selection_objective')}`",
        f"- score formula: `{policy.get('score_formula')}`",
        "",
        "## Selection Metrics",
        "",
    ]
    selected = policy.get("selection_metrics", {})
    for key in ["rows", "mean_nll", "mean_brier", "accuracy_at_0_5", "positive_rate", "mean_prediction"]:
        lines.append(f"- {key}: `{selected.get(key)}`")
    lines.extend(
        [
            "",
            "## Diagnostics",
            "",
            "| Split | Rows | Mean NLL | Mean Brier | Accuracy@0.5 | Positive rate | Mean prediction |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for split_name in ["selection", "diagnostic_train"]:
        item = diagnostics.get(split_name, {})
        lines.append(
            "| {split} | {rows} | {nll} | {brier} | {acc} | {pos} | {pred} |".format(
                split=split_name,
                rows=item.get("rows"),
                nll=f"{item.get('mean_nll'):.6f}" if item.get("mean_nll") is not None else "NA",
                brier=f"{item.get('mean_brier'):.6f}" if item.get("mean_brier") is not None else "NA",
                acc=f"{item.get('accuracy_at_0_5'):.6f}" if item.get("accuracy_at_0_5") is not None else "NA",
                pos=f"{item.get('positive_rate'):.6f}" if item.get("positive_rate") is not None else "NA",
                pred=f"{item.get('mean_prediction'):.6f}" if item.get("mean_prediction") is not None else "NA",
            )
        )
    lines.extend(
        [
            "",
            "## Family Summary",
            "",
            "| Split | Family | Rows | Valid | Invalid | Mean p_geom_valid |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for split_name, split_summary in manifest["calibration_summary"]["by_split"].items():
        for family, item in split_summary["by_family"].items():
            mean = item["mean_p_geom_valid"]
            lines.append(
                "| {split} | {family} | {rows} | {valid} | {invalid} | {mean} |".format(
                    split=split_name,
                    family=family,
                    rows=item["rows"],
                    valid=item["geom_valid"],
                    invalid=item["geom_invalid"],
                    mean=f"{mean:.6f}" if mean is not None else "NA",
                )
            )
    lines.extend(["", "Full lambda curve is in `selection_curve.jsonl`.", ""])
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    repo_root = resolve_path(REPO_ROOT, args.repo_root).resolve()
    scores_path = resolve_path(repo_root, args.scores_jsonl)
    output_dir = resolve_path(repo_root, args.output_dir)
    if not (0.0 < args.epsilon < 0.5):
        raise ValueError("--epsilon must be in (0, 0.5)")
    assert_writable_output(repo_root, output_dir, args.overwrite)
    raw_rows = load_jsonl(scores_path)
    families = set(args.families)
    rows, errors, skipped = normalize_rows(raw_rows, families)
    if errors:
        raise ValueError(f"Calibration row validation failed with {len(errors)} errors: {errors[:10]}")

    selection_rows = [row for row in rows if row["role"] == args.selection_role]
    diagnostic_rows = [row for row in rows if row["role"] == args.diagnostic_role]
    if not selection_rows:
        raise ValueError(f"No selection rows with role={args.selection_role}")

    grid = lambda_grid(args.lambda_min, args.lambda_max, args.lambda_step)
    policy, curve = select_lambda(selection_rows, grid, args.epsilon)
    lam = float(policy["lambda_star"])
    diagnostics = {
        "selection": evaluate_lambda(selection_rows, lam, args.epsilon),
        "diagnostic_train": evaluate_lambda(diagnostic_rows, lam, args.epsilon),
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": policy["status"],
        "code": "src/geocalib/select_h001_v2_lambda.py",
        "inputs": {
            "scores_jsonl": repo_rel(scores_path, repo_root),
            "families": sorted(families),
            "selection_role": args.selection_role,
            "diagnostic_role": args.diagnostic_role,
        },
        "config": {
            "lambda_min": args.lambda_min,
            "lambda_max": args.lambda_max,
            "lambda_step": args.lambda_step,
            "lambda_grid_size": len(grid),
            "epsilon": args.epsilon,
            "tie_break": "mean_nll, mean_brier, distance_to_lambda_1, lower_lambda",
        },
        "calibration_summary": {
            "raw_rows": len(raw_rows),
            "filtered_rows": len(rows),
            "skipped": dict(skipped),
            "by_split": {
                args.selection_role: {
                    "rows": len(selection_rows),
                    "by_family": family_summary(selection_rows),
                },
                args.diagnostic_role: {
                    "rows": len(diagnostic_rows),
                    "by_family": family_summary(diagnostic_rows),
                },
            },
        },
        "outputs": {
            "lambda_policy_json": "lambda_policy.json",
            "selection_curve_jsonl": "selection_curve.jsonl",
            "manifest_json": "manifest.json",
            "report_md": "report.md",
        },
        "notes": [
            "Lambda is selected before source evaluation.",
            "Source metrics are not read during lambda selection.",
            "The selected score is a soft reranking score, not a hard eligibility filter.",
        ],
    }

    write_json(output_dir / "manifest.json", manifest)
    write_json(output_dir / "lambda_policy.json", policy)
    write_jsonl(output_dir / "selection_curve.jsonl", curve)
    write_json(output_dir / "diagnostics.json", diagnostics)
    (output_dir / "report.md").write_text(
        report_markdown(policy, manifest, diagnostics),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": policy["status"],
                "lambda_star": policy["lambda_star"],
                "output_dir": repo_rel(output_dir, repo_root),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
