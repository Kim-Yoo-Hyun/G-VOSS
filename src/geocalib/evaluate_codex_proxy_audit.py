#!/usr/bin/env python3
"""Evaluate locked Codex blind passes or their adjudicated proxy reference."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


KS = (5, 10, 20, 50, 100)
SOURCES = ("vlsat_closed_set", "open3dsg_ov_recovery")
METHODS = ("semantic_only", "family_conditional_risk")
BINARY = {"physically_valid", "physically_invalid"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--sidecar", type=Path, required=True)
    parser.add_argument("--codex-v1", type=Path, required=True)
    parser.add_argument("--codex-v2", type=Path, required=True)
    parser.add_argument("--proxy-reference", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260714)
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def read_labels(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        output: dict[str, str] = {}
        for row in csv.DictReader(handle):
            output[row["audit_id"]] = (
                row.get("external_majority_label", "").strip()
                or row["physical_validity_label"]
            )
        return output


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def weighted_ratio(rows: list[dict[str, Any]], field: str = "invalid") -> float | None:
    denominator = sum(row["weight"] for row in rows)
    if denominator <= 0:
        return None
    return sum(row["weight"] * row[field] for row in rows) / denominator


def percentile(values: list[float]) -> list[float | None]:
    finite = np.asarray([value for value in values if np.isfinite(value)], dtype=np.float64)
    if not len(finite):
        return [None, None]
    low, high = np.percentile(finite, [2.5, 97.5])
    return [float(low), float(high)]


def bootstrap_ratio(rows: list[dict[str, Any]], n: int, seed: int, field: str = "invalid") -> list[float | None]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["scan_id"]].append(row)
    scans = sorted(grouped)
    if not scans:
        return [None, None]
    rng = np.random.default_rng(seed)
    samples: list[float] = []
    for _ in range(n):
        chosen = rng.choice(scans, size=len(scans), replace=True)
        sample = [row for scan in chosen for row in grouped[str(scan)]]
        value = weighted_ratio(sample, field)
        if value is not None:
            samples.append(value)
    return percentile(samples)


def bootstrap_delta(
    baseline: list[dict[str, Any]],
    method: list[dict[str, Any]],
    n: int,
    seed: int,
) -> list[float | None]:
    grouped_a: dict[str, list[dict[str, Any]]] = defaultdict(list)
    grouped_b: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in baseline:
        grouped_a[row["scan_id"]].append(row)
    for row in method:
        grouped_b[row["scan_id"]].append(row)
    scans = sorted(set(grouped_a) | set(grouped_b))
    if not scans:
        return [None, None]
    rng = np.random.default_rng(seed)
    samples: list[float] = []
    for _ in range(n):
        chosen = rng.choice(scans, size=len(scans), replace=True)
        sample_a = [row for scan in chosen for row in grouped_a.get(str(scan), [])]
        sample_b = [row for scan in chosen for row in grouped_b.get(str(scan), [])]
        value_a, value_b = weighted_ratio(sample_a), weighted_ratio(sample_b)
        if value_a is not None and value_b is not None:
            samples.append(value_b - value_a)
    return percentile(samples)


def weighted_construct_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    decidable = [row for row in rows if row["verifier_status"] in {"satisfied", "violated"}]
    total_weight = sum(row["weight"] for row in rows)
    decidable_weight = sum(row["weight"] for row in decidable)
    confusion = Counter()
    for row in decidable:
        proxy = "invalid" if row["invalid"] else "valid"
        verifier = "invalid" if row["verifier_status"] == "violated" else "valid"
        confusion[(proxy, verifier)] += row["weight"]
    tp = confusion[("invalid", "invalid")]
    fp = confusion[("valid", "invalid")]
    fn = confusion[("invalid", "valid")]
    tn = confusion[("valid", "valid")]
    accuracy = (tp + tn) / decidable_weight if decidable_weight else None
    proxy_invalid = (tp + fn) / decidable_weight if decidable_weight else None
    verifier_invalid = (tp + fp) / decidable_weight if decidable_weight else None
    expected = (
        proxy_invalid * verifier_invalid + (1.0 - proxy_invalid) * (1.0 - verifier_invalid)
        if proxy_invalid is not None and verifier_invalid is not None else None
    )
    kappa = (
        (accuracy - expected) / (1.0 - expected)
        if accuracy is not None and expected is not None and expected < 1.0 else None
    )
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    return {
        "binary_proxy_rows": len(rows),
        "decidable_verifier_rows": len(decidable),
        "weighted_decidable_coverage": decidable_weight / total_weight if total_weight else None,
        "weighted_accuracy": accuracy,
        "weighted_kappa": kappa,
        "verifier_invalid_precision": precision,
        "verifier_invalid_recall": recall,
        "verifier_invalid_f1": 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None,
        "weighted_confusion_proxy_rows_verifier_columns": {
            "valid": {"valid": tn, "invalid": fp},
            "invalid": {"valid": fn, "invalid": tp},
        },
    }


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    paths = {name: resolve(root, value) for name, value in {
        "sidecar": args.sidecar, "codex_v1": args.codex_v1, "codex_v2": args.codex_v2,
    }.items()}
    if args.proxy_reference:
        paths["proxy_reference"] = resolve(root, args.proxy_reference)
    reviewer_verified = (
        "proxy_reference" in paths
        and paths["proxy_reference"].name == "reviewer_verified_reference.csv"
    )
    out = resolve(root, args.out)
    v1, v2 = read_labels(paths["codex_v1"]), read_labels(paths["codex_v2"])
    if set(v1) != set(v2) or len(v1) != 488:
        raise ValueError("locked_pass_id_mismatch")
    if "proxy_reference" in paths:
        consensus = read_labels(paths["proxy_reference"])
        if set(consensus) != set(v1) or set(consensus.values()) - (BINARY | {"ambiguous", "unobservable"}):
            raise ValueError("proxy_reference_contract_failed")
        consensus_policy = (
            "use the three-reviewer-majority label from the completed Codex proxy reference"
            if reviewer_verified
            else "use the evidence-only visually adjudicated 488-row Codex proxy reference"
        )
    else:
        consensus = {key: v1[key] if v1[key] == v2[key] else "ambiguous" for key in v1}
        consensus_policy = "retain exact pass agreement; map every pass disagreement to ambiguous; exclude ambiguous/unobservable from the binary proxy denominator"
    accum: dict[tuple[str, str, int, str], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    selected_rows: dict[tuple[str, str, int, str], list[dict[str, Any]]] = defaultdict(list)
    construct_rows: list[dict[str, Any]] = []
    source_records = 0
    with paths["sidecar"].open(encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            audit_id, label, weight = item["audit_id"], consensus[item["audit_id"]], float(item["design_weight"])
            source_records_for_item = [record for record in item["source_records"] if record["source"] in SOURCES]
            if label in BINARY and source_records_for_item:
                statuses = {record["verifier_status"] for record in source_records_for_item}
                if len(statuses) != 1:
                    raise ValueError(f"mixed_verifier_status:{audit_id}")
                first = source_records_for_item[0]
                construct_rows.append({
                    "audit_id": audit_id,
                    "scan_id": first["scan_id"],
                    "family": first["predicate_family"],
                    "weight": weight,
                    "invalid": int(label == "physically_invalid"),
                    "verifier_status": next(iter(statuses)),
                })
            for record in item["source_records"]:
                source = record["source"]
                if source not in SOURCES:
                    continue
                source_records += 1
                family = record["predicate_family"]
                for method in METHODS:
                    rank = record["ranks"].get(f"global_in_scope:{method}")
                    if not isinstance(rank, int):
                        continue
                    for k in KS:
                        if rank > k:
                            continue
                        for slice_name in ("overall", family):
                            cell = accum[(source, method, k, slice_name)]
                            cell["sampled_rows"] += 1
                            cell["weighted_selected"] += weight
                            if label in BINARY:
                                cell["resolved_rows"] += 1
                                cell["weighted_resolved"] += weight
                                if label == "physically_invalid":
                                    cell["invalid_rows"] += 1
                                    cell["weighted_invalid"] += weight
                                selected_rows[(source, method, k, slice_name)].append({
                                    "audit_id": audit_id,
                                    "scan_id": record["scan_id"],
                                    "weight": weight,
                                    "invalid": int(label == "physically_invalid"),
                                })
    metrics: dict[str, Any] = {}
    for source in SOURCES:
        metrics[source] = {}
        for method in METHODS:
            metrics[source][method] = {}
            for k in KS:
                overall = accum[(source, method, k, "overall")]
                resolved = overall["weighted_resolved"]
                selected = overall["weighted_selected"]
                metrics[source][method][str(k)] = {
                    "proxy_violation": overall["weighted_invalid"] / resolved if resolved else None,
                    "proxy_violation_ci95_scan_bootstrap": bootstrap_ratio(
                        selected_rows[(source, method, k, "overall")],
                        args.n_bootstrap,
                        args.seed + 1000 * SOURCES.index(source) + 100 * METHODS.index(method) + k,
                    ),
                    "binary_resolution_coverage": resolved / selected if selected else None,
                    "sampled_rows": int(overall["sampled_rows"]),
                    "resolved_rows": int(overall["resolved_rows"]),
                    "invalid_rows": int(overall["invalid_rows"]),
                    "family": {
                        family: {
                            "proxy_violation": accum[(source, method, k, family)]["weighted_invalid"] / accum[(source, method, k, family)]["weighted_resolved"]
                            if accum[(source, method, k, family)]["weighted_resolved"] else None,
                            "proxy_violation_ci95_scan_bootstrap": bootstrap_ratio(
                                selected_rows[(source, method, k, family)],
                                args.n_bootstrap,
                                args.seed + 10000 + 1000 * SOURCES.index(source) + 100 * METHODS.index(method) + k,
                            ),
                            "resolved_rows": int(accum[(source, method, k, family)]["resolved_rows"]),
                        }
                        for family in ("support_contact", "proximity", "relative_vertical")
                    },
                }
        metrics[source]["paired_delta_product_minus_source"] = {}
        for k in KS:
            baseline_rows = selected_rows[(source, "semantic_only", k, "overall")]
            method_rows = selected_rows[(source, "family_conditional_risk", k, "overall")]
            baseline_value, method_value = weighted_ratio(baseline_rows), weighted_ratio(method_rows)
            metrics[source]["paired_delta_product_minus_source"][str(k)] = {
                "delta_proxy_violation": method_value - baseline_value
                if method_value is not None and baseline_value is not None else None,
                "ci95_scan_bootstrap": bootstrap_delta(
                    baseline_rows,
                    method_rows,
                    args.n_bootstrap,
                    args.seed + 20000 + 1000 * SOURCES.index(source) + k,
                ),
            }
    construct_validity = weighted_construct_summary(construct_rows)
    construct_validity["weighted_accuracy_ci95_scan_bootstrap"] = bootstrap_ratio(
        [
            {
                **row,
                "agreement": int(
                    (row["invalid"] == 1 and row["verifier_status"] == "violated")
                    or (row["invalid"] == 0 and row["verifier_status"] == "satisfied")
                ),
            }
            for row in construct_rows
            if row["verifier_status"] in {"satisfied", "violated"}
        ],
        args.n_bootstrap,
        args.seed + 30000,
        field="agreement",
    )
    construct_validity["by_family"] = {
        family: weighted_construct_summary([row for row in construct_rows if row["family"] == family])
        for family in ("support_contact", "proximity", "relative_vertical")
    }
    validations = {
        "two_locked_passes_488_rows": len(v1) == len(v2) == 488,
        "direct_valid_invalid_flips_zero": not any({v1[key], v2[key]} == BINARY for key in v1),
        "binary_proxy_rows_present": sum(label in BINARY for label in consensus.values()) > 0,
        "sidecar_source_records_present": source_records > 0,
    }
    out.mkdir(parents=True, exist_ok=True)
    status = "completed_reviewer_verified_llm_proxy" if reviewer_verified else "completed_nonhuman_proxy_only"
    claim_boundary = (
        "Three external reviewers verified the completed Codex labels without revision. This is reviewer-verified LLM annotation, not independent blank first-pass human annotation or Human Violation@K."
        if reviewer_verified
        else "Codex labels are non-human automatic-proxy evidence. Visual proxy adjudication resolves the automatic reference but does not establish independent physical validity or Human Violation@K."
    )
    summary = {
        "schema_version": "h001_codex_proxy_audit_evaluation_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status if all(validations.values()) else "failed",
        "consensus_policy": consensus_policy,
        "metrics": metrics,
        "construct_validity": construct_validity,
        "bootstrap": {"unit": "scan", "resamples": args.n_bootstrap, "seed": args.seed},
        "validations": validations,
        "claim_boundary": claim_boundary,
    }
    write_json(out / "summary.json", summary)
    lines = [
        "# Codex Blind Proxy Audit", "", f"Status: `{summary['status']}`", "",
        "This analysis is intentionally excluded from the submission manuscript unless an explicit later reporting decision promotes reviewer-verified LLM evidence.", "",
        "## Verifier--proxy construct agreement", "",
        f"- Decidable rows: {construct_validity['decidable_verifier_rows']} / {construct_validity['binary_proxy_rows']}",
        f"- Design-weighted accuracy: {construct_validity['weighted_accuracy']:.4f} "
        f"(scan-bootstrap 95% CI {construct_validity['weighted_accuracy_ci95_scan_bootstrap']})",
        f"- Design-weighted kappa: {construct_validity['weighted_kappa']:.4f}",
        f"- Invalid precision / recall / F1: {construct_validity['verifier_invalid_precision']:.4f} / "
        f"{construct_validity['verifier_invalid_recall']:.4f} / {construct_validity['verifier_invalid_f1']:.4f}",
        "", "## Design-weighted proxy Violation@K", "",
        "| Source | Method | K | Proxy violation | Resolution coverage | Resolved / sampled |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for source in SOURCES:
        for method in METHODS:
            for k in (10, 50, 100):
                cell = metrics[source][method][str(k)]
                lines.append(
                    f"| {source} | {method} | {k} | {cell['proxy_violation']:.4f} | "
                    f"{cell['binary_resolution_coverage']:.4f} | {cell['resolved_rows']} / {cell['sampled_rows']} |"
                )
    lines.extend(["", "These are design-weighted Codex proxy-reference estimates, not human measurements."])
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "h001_codex_proxy_audit_evaluation_manifest_v1",
        "status": summary["status"],
        "inputs": {name: {"path": relpath(root, path), "sha256": sha256_file(path)} for name, path in paths.items()},
        "outputs": {name: {"path": relpath(root, out / name), "sha256": sha256_file(out / name)} for name in ("summary.json", "summary.md")},
        "docker_command": (
            "env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm reviewer_verified_proxy_evaluate"
            if reviewer_verified else (
                "env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm codex_proxy_reference_evaluate"
                if "proxy_reference" in paths else
                "env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm codex_proxy_audit_evaluate"
            )
        ),
        "claim_boundary": summary["claim_boundary"],
    }
    write_json(out / "manifest.json", manifest)
    print(json.dumps({"status": summary["status"], "out": relpath(root, out)}))
    return 0 if all(validations.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
