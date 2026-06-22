#!/usr/bin/env python3
"""Select the H001_v2 geometry-risk threshold from held-out calibration rows."""

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


SCHEMA_VERSION = "h001_v2_threshold_selection_v1"
DEFAULT_FAMILIES = ("support_contact", "proximity", "relative_vertical")
DEFAULT_SCORES = (
    Path("archive/hypothesis_records/hypothesis/CAND-001")
    / "H001_geometry-grounded-verification/artifacts/calibration"
    / "p_geom_valid_smoke/scores.jsonl"
)
DEFAULT_OUTPUT = (
    Path("hypothesis/CAND-001/H001_v2_risk_controlled_reranking")
    / "artifacts/calibration_threshold_selection"
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
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="H001_v2 calibration-only geometry-risk threshold selector."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--scores-jsonl", type=Path, default=DEFAULT_SCORES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--families", nargs="+", default=list(DEFAULT_FAMILIES))
    parser.add_argument("--role", default="dev")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--delta", type=float, default=0.05)
    parser.add_argument("--tau-step", type=float, default=0.01)
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
            "Refusing to write H001_v2 outputs under read-only H001 root: "
            f"{repo_rel(output_dir, repo_root)}"
        )
    if output_dir.exists() and any(output_dir.iterdir()):
        if not overwrite:
            raise FileExistsError(
                f"Output directory is non-empty: {repo_rel(output_dir, repo_root)}. "
                "Pass --overwrite to replace this H001_v2 dry-run output."
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


def beta_continued_fraction(a: float, b: float, x: float) -> float:
    max_iter = 300
    eps = 3.0e-14
    fpmin = 1.0e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) <= eps:
            return h
    raise RuntimeError("beta continued fraction did not converge")


def regularized_incomplete_beta(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    log_bt = (
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )
    bt = math.exp(log_bt)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * beta_continued_fraction(a, b, x) / a
    return 1.0 - bt * beta_continued_fraction(b, a, 1.0 - x) / b


def beta_ppf(probability: float, a: float, b: float) -> float:
    if probability <= 0.0:
        return 0.0
    if probability >= 1.0:
        return 1.0
    lo = 0.0
    hi = 1.0
    for _ in range(120):
        mid = (lo + hi) / 2.0
        cdf = regularized_incomplete_beta(a, b, mid)
        if cdf < probability:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def clopper_pearson_upper(violations: int, total: int, delta: float) -> float | None:
    if total <= 0:
        return None
    if violations < 0 or violations > total:
        raise ValueError(f"Invalid violation count {violations}/{total}")
    if violations == total:
        return 1.0
    return beta_ppf(1.0 - delta, violations + 1.0, total - violations)


def tau_grid(step: float) -> list[float]:
    if step <= 0 or step > 1:
        raise ValueError("--tau-step must be in (0, 1]")
    count = int(round(1.0 / step))
    grid = [round(i * step, 10) for i in range(count + 1)]
    if grid[-1] != 1.0:
        grid.append(1.0)
    return sorted(set(grid))


def normalized_rows(
    raw_rows: list[dict[str, Any]],
    families: set[str],
    role: str,
) -> tuple[list[dict[str, Any]], list[str], Counter[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    skipped: Counter[str] = Counter()
    for index, row in enumerate(raw_rows, 1):
        family = row.get("predicate", {}).get("predicate_family")
        if family not in families:
            skipped["family_out_of_scope"] += 1
            continue
        if row.get("role") != role:
            skipped[f"role_not_{role}"] += 1
            continue
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
                "geom_valid": int(geom_valid),
                "p_geom_valid": p_geom_valid,
                "risk": 1.0 - p_geom_valid,
                "scan_id": row.get("scan_id"),
                "subgraph_id": row.get("subgraph_id"),
            }
        )
    return rows, errors, skipped


def select_threshold(
    rows: list[dict[str, Any]],
    alpha: float,
    delta: float,
    grid: list[float],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    curve: list[dict[str, Any]] = []
    feasible_rows: list[dict[str, Any]] = []
    for tau in grid:
        selected = [row for row in rows if row["risk"] <= tau]
        total = len(selected)
        violations = sum(1 for row in selected if row["geom_valid"] == 0)
        empirical = violations / total if total else None
        upper = clopper_pearson_upper(violations, total, delta)
        feasible = upper is not None and upper <= alpha
        curve_row = {
            "tau": tau,
            "p_geom_valid_threshold": round(1.0 - tau, 10),
            "selected_count": total,
            "violations": violations,
            "empirical_violation_rate": empirical,
            "cp_upper": upper,
            "alpha": alpha,
            "delta": delta,
            "feasible": feasible,
        }
        curve.append(curve_row)
        if feasible:
            feasible_rows.append(curve_row)
    if not feasible_rows:
        return {
            "status": "risk_budget_infeasible",
            "tau_star": None,
            "p_geom_valid_threshold": None,
            "reason": "no_tau_satisfies_cp_upper_le_alpha",
        }, curve
    selected_policy = max(feasible_rows, key=lambda row: (row["tau"], row["selected_count"]))
    return {
        "status": "ready",
        "tau_star": selected_policy["tau"],
        "p_geom_valid_threshold": selected_policy["p_geom_valid_threshold"],
        "selected_count": selected_policy["selected_count"],
        "violations": selected_policy["violations"],
        "empirical_violation_rate": selected_policy["empirical_violation_rate"],
        "cp_upper": selected_policy["cp_upper"],
        "alpha": alpha,
        "delta": delta,
    }, curve


def family_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for family in sorted({row["family"] for row in rows}):
        family_rows = [row for row in rows if row["family"] == family]
        valid = sum(1 for row in family_rows if row["geom_valid"] == 1)
        invalid = len(family_rows) - valid
        p_values = [row["p_geom_valid"] for row in family_rows]
        summary[family] = {
            "rows": len(family_rows),
            "geom_valid": valid,
            "geom_invalid": invalid,
            "min_p_geom_valid": min(p_values) if p_values else None,
            "max_p_geom_valid": max(p_values) if p_values else None,
            "mean_p_geom_valid": sum(p_values) / len(p_values) if p_values else None,
        }
    return summary


def report_markdown(
    policy: dict[str, Any],
    manifest: dict[str, Any],
    curve: list[dict[str, Any]],
) -> str:
    lines = [
        "# H001_v2 Calibration Threshold Selection",
        "",
        f"Created at: {manifest['created_at']}",
        "",
        f"Status: `{policy['status']}`",
        "",
        "## Inputs",
        "",
        f"- scores: `{manifest['inputs']['scores_jsonl']}`",
        f"- role: `{manifest['inputs']['role']}`",
        f"- families: `{', '.join(manifest['inputs']['families'])}`",
        "",
        "## Policy",
        "",
        f"- alpha: `{manifest['config']['alpha']}`",
        f"- delta: `{manifest['config']['delta']}`",
        f"- tau step: `{manifest['config']['tau_step']}`",
        f"- selected tau: `{policy.get('tau_star')}`",
        f"- p_geom_valid threshold: `{policy.get('p_geom_valid_threshold')}`",
        f"- CP upper: `{policy.get('cp_upper')}`",
        f"- empirical violation: `{policy.get('empirical_violation_rate')}`",
        f"- selected rows: `{policy.get('selected_count')}`",
        "",
        "## Family Summary",
        "",
        "| Family | Rows | Valid | Invalid | Mean p_geom_valid |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for family, item in manifest["calibration_summary"]["by_family"].items():
        lines.append(
            "| {family} | {rows} | {valid} | {invalid} | {mean} |".format(
                family=family,
                rows=item["rows"],
                valid=item["geom_valid"],
                invalid=item["geom_invalid"],
                mean=(
                    f"{item['mean_p_geom_valid']:.6f}"
                    if item["mean_p_geom_valid"] is not None
                    else "NA"
                ),
            )
        )
    feasible = sum(1 for row in curve if row["feasible"])
    lines.extend(
        [
            "",
            "## Curve Summary",
            "",
            f"- threshold candidates: `{len(curve)}`",
            f"- feasible candidates: `{feasible}`",
            "",
            "Full curve is in `selection_curve.jsonl`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    repo_root = resolve_path(REPO_ROOT, args.repo_root).resolve()
    scores_path = resolve_path(repo_root, args.scores_jsonl)
    output_dir = resolve_path(repo_root, args.output_dir)
    if not (0.0 < args.alpha < 1.0):
        raise ValueError("--alpha must be in (0, 1)")
    if not (0.0 < args.delta < 1.0):
        raise ValueError("--delta must be in (0, 1)")
    assert_writable_output(repo_root, output_dir, args.overwrite)

    raw_rows = load_jsonl(scores_path)
    families = set(args.families)
    rows, errors, skipped = normalized_rows(raw_rows, families=families, role=args.role)
    if errors:
        raise ValueError(f"Calibration row validation failed with {len(errors)} errors: {errors[:10]}")
    if not rows:
        raise ValueError("No calibration rows remain after family/role filtering")

    grid = tau_grid(args.tau_step)
    policy, curve = select_threshold(rows, alpha=args.alpha, delta=args.delta, grid=grid)
    selected = [row for row in rows if policy["tau_star"] is not None and row["risk"] <= policy["tau_star"]]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": policy["status"],
        "inputs": {
            "scores_jsonl": repo_rel(scores_path, repo_root),
            "role": args.role,
            "families": sorted(families),
        },
        "config": {
            "alpha": args.alpha,
            "delta": args.delta,
            "tau_step": args.tau_step,
            "tau_grid_size": len(grid),
            "upper_bound": "one_sided_clopper_pearson",
            "beta_quantile": "internal_bisection_regularized_incomplete_beta",
        },
        "calibration_summary": {
            "raw_rows": len(raw_rows),
            "filtered_rows": len(rows),
            "skipped": dict(skipped),
            "by_family": family_summary(rows),
        },
        "selected_policy_file": "thresholds.json",
        "curve_file": "selection_curve.jsonl",
        "selected_rows_file": "selected_rows.jsonl",
        "report_file": "report.md",
        "notes": [
            "Threshold selected from held-out calibration score rows only.",
            "Top-K source metrics must apply this fixed threshold without reselecting tau.",
        ],
    }

    write_json(output_dir / "manifest.json", manifest)
    write_json(output_dir / "thresholds.json", policy)
    write_jsonl(output_dir / "selection_curve.jsonl", curve)
    write_jsonl(output_dir / "selected_rows.jsonl", selected)
    (output_dir / "report.md").write_text(
        report_markdown(policy, manifest, curve),
        encoding="utf-8",
    )

    print(json.dumps({"status": policy["status"], "output_dir": repo_rel(output_dir, repo_root)}, sort_keys=True))


if __name__ == "__main__":
    main()
