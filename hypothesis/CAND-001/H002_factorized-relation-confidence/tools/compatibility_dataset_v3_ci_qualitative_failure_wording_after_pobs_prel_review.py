#!/usr/bin/env python3
"""Create CI, qualitative examples, and failure wording after p_obs/p_rel review."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
DEFAULT_REVIEW_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_pobs_prel_result_review_after_metric_runner"
)
DEFAULT_EVAL_DIR = (
    REPO_ROOT / "experiments/H002_compatibility_routing/pobs_prel_evaluation/latest"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_ci_qualitative_failure_wording_after_pobs_prel_review"
)

EXPECTED_REVIEW_STATUS = "h002_pobs_prel_result_review_after_metric_runner_ready"
SCHEMA_VERSION = "h002_ci_qualitative_failure_wording_after_pobs_prel_review_v1"
STATUS_READY = "h002_ci_qualitative_failure_wording_after_pobs_prel_review_ready"
STATUS_ERROR = "h002_ci_qualitative_failure_wording_after_pobs_prel_review_input_errors"
NEXT_TODO = "compatibility_dataset_v3_h002_paper_outline_or_integration_decision_after_insertion_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--bootstrap", type=int, default=200)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def auc(labels: list[int], scores: list[float]) -> float:
    pairs = sorted(zip(scores, labels), key=lambda item: item[0])
    pos = sum(labels)
    neg = len(labels) - pos
    if pos == 0 or neg == 0:
        return 0.0
    rank_sum = 0.0
    i = 0
    while i < len(pairs):
        j = i + 1
        while j < len(pairs) and pairs[j][0] == pairs[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        rank_sum += avg_rank * sum(label for _, label in pairs[i:j])
        i = j
    return (rank_sum - pos * (pos + 1) / 2.0) / (pos * neg)


def macro_f1(labels: list[str], preds: list[str]) -> float:
    classes = ["accept", "reject", "abstain"]
    out = []
    for cls in classes:
        tp = sum(1 for y, p in zip(labels, preds) if y == cls and p == cls)
        fp = sum(1 for y, p in zip(labels, preds) if y != cls and p == cls)
        fn = sum(1 for y, p in zip(labels, preds) if y == cls and p != cls)
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        out.append(0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall))
    return sum(out) / len(out)


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(max(int(round((len(ordered) - 1) * q)), 0), len(ordered) - 1)
    return ordered[idx]


def ci_row(metric: str, values: list[float], point: float) -> dict[str, Any]:
    return {
        "metric": metric,
        "point": point,
        "ci_low_95": percentile(values, 0.025),
        "ci_high_95": percentile(values, 0.975),
        "bootstrap_samples": len(values),
    }


def bootstrap(rows: list[dict[str, Any]], n: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    observed = [row for row in rows if row["control_type"] == "observed_original"]
    controls = [row for row in rows if row["control_type"] != "observed_original"]
    pobs_labels = [int(row["obs_label"]) for row in rows]
    pobs_scores = [float(row["p_obs"]) for row in rows]
    prel_labels = [int(row["rel_label"]) for row in observed if row.get("rel_label") is not None]
    prel_scores = [float(row["p_rel"]) for row in observed if row.get("rel_label") is not None]
    dec_labels = [row["decision_label"] for row in rows]
    dec_preds = [row["pred_decision"] for row in rows]
    missing_abstain = [
        1.0 if row["pred_decision"] == "abstain" else 0.0
        for row in controls
    ]
    point = {
        "p_obs_auroc": auc(pobs_labels, pobs_scores),
        "p_rel_auroc": auc(prel_labels, prel_scores),
        "decision_macro_f1": macro_f1(dec_labels, dec_preds),
        "missing_control_abstain_rate": sum(missing_abstain) / max(len(missing_abstain), 1),
    }
    buckets: dict[str, list[float]] = {key: [] for key in point}
    for _ in range(n):
        sampled = [rows[rng.randrange(len(rows))] for _ in rows]
        sampled_observed = [row for row in sampled if row["control_type"] == "observed_original"]
        sampled_controls = [row for row in sampled if row["control_type"] != "observed_original"]
        buckets["p_obs_auroc"].append(
            auc([int(row["obs_label"]) for row in sampled], [float(row["p_obs"]) for row in sampled])
        )
        buckets["p_rel_auroc"].append(
            auc(
                [int(row["rel_label"]) for row in sampled_observed if row.get("rel_label") is not None],
                [float(row["p_rel"]) for row in sampled_observed if row.get("rel_label") is not None],
            )
        )
        buckets["decision_macro_f1"].append(
            macro_f1([row["decision_label"] for row in sampled], [row["pred_decision"] for row in sampled])
        )
        buckets["missing_control_abstain_rate"].append(
            sum(1 for row in sampled_controls if row["pred_decision"] == "abstain")
            / max(len(sampled_controls), 1)
        )
    return [ci_row(key, buckets[key], point[key]) for key in sorted(point)]


def representative_examples(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = {
        "correct_accept_high_p_rel": lambda r: r["decision_label"] == "accept" and r["pred_decision"] == "accept",
        "correct_reject_low_p_rel": lambda r: r["decision_label"] == "reject" and r["pred_decision"] == "reject",
        "correct_abstain_low_p_obs": lambda r: r["decision_label"] == "abstain" and r["pred_decision"] == "abstain",
        "false_accept_reject_as_accept": lambda r: r["decision_label"] == "reject" and r["pred_decision"] == "accept",
        "false_reject_accept_as_reject": lambda r: r["decision_label"] == "accept" and r["pred_decision"] == "reject",
    }
    examples: list[dict[str, Any]] = []
    for name, predicate in groups.items():
        candidates = [row for row in rows if predicate(row)]
        candidates = sorted(candidates, key=lambda row: (row["route_family"], row["predicate_label"], row["candidate_id"]))
        for row in candidates[:8]:
            examples.append(
                {
                    "example_type": name,
                    "candidate_id": row["candidate_id"],
                    "source_candidate_id": row.get("source_candidate_id"),
                    "route_family": row.get("route_family"),
                    "predicate_label": row.get("predicate_label"),
                    "control_type": row.get("control_type"),
                    "decision_label": row.get("decision_label"),
                    "pred_decision": row.get("pred_decision"),
                    "p_obs": f"{float(row['p_obs']):.6f}",
                    "p_rel": f"{float(row['p_rel']):.6f}",
                }
            )
    return examples


def failure_wording() -> str:
    return """# p_obs / p_rel Failure Wording

## Allowed Wording

- The selective-decision stress test passes: `p_obs` separates observable rows
  from synthetic missing-evidence controls, and `p_rel` remains above the
  minimum observable-edge AUROC gate.
- The result supports keeping `p_obs/p_rel` as a framework component.
- The current evidence is validation-level and uses synthetic missing-evidence
  controls for unobservable examples.
- Calibration remains imperfect, so calibrated quantitative wording should be
  conservative.

## Blocked Wording

- Do not claim an official-test p_obs/p_rel result.
- Do not claim independent human observability labels were used.
- Do not claim calibrated p_obs/p_rel reliability is solved.
- Do not claim support/contact, attachment, or containment are solved by this
  selective stress test.

## Paper-Safe Sentence

We include a selective-decision layer that separates observability from
observable-edge reliability. In a validation-level stress test, the layer
successfully abstains on synthetic missing-evidence controls and preserves a
non-trivial observable-edge reliability signal, but calibration and independent
observability annotation remain future requirements for a standalone
calibrated-selective benchmark claim.
"""


def main() -> int:
    args = parse_args()
    review = read_json(args.review_dir / "summary.json")
    gate = read_json(args.eval_dir / "gate_decision.json")
    rows = read_jsonl(args.eval_dir / "prediction_scores.jsonl")
    errors: list[dict[str, Any]] = []
    if review.get("status") != EXPECTED_REVIEW_STATUS:
        errors.append({"error_type": "unexpected_review_status", "actual": review.get("status")})
    if gate.get("selective_metric_pass") is not True:
        errors.append({"error_type": "selective_metric_not_passed"})
    if gate.get("paper_promotion_pass") is True:
        errors.append({"error_type": "unexpected_paper_promotion_pass"})

    args.output_dir.mkdir(parents=True, exist_ok=True)
    ci_rows = bootstrap(rows, args.bootstrap, args.seed)
    examples = representative_examples(rows)
    write_csv(args.output_dir / "bootstrap_ci.csv", ci_rows)
    write_csv(args.output_dir / "qualitative_examples.csv", examples)
    (args.output_dir / "failure_wording.md").write_text(failure_wording(), encoding="utf-8")
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_ERROR if errors else STATUS_READY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "review_dir": rel_path(args.review_dir),
        "eval_dir": rel_path(args.eval_dir),
        "outputs": {
            "bootstrap_ci": rel_path(args.output_dir / "bootstrap_ci.csv"),
            "qualitative_examples": rel_path(args.output_dir / "qualitative_examples.csv"),
            "failure_wording": rel_path(args.output_dir / "failure_wording.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "row_counts": {
            "prediction_rows": len(rows),
            "qualitative_examples": len(examples),
            "decision_labels": dict(Counter(row["decision_label"] for row in rows)),
            "pred_decisions": dict(Counter(row["pred_decision"] for row in rows)),
        },
        "ci_metrics": ci_rows,
        "selected_path": "keep_pobs_prel_as_framework_component_ci_qualitative_wording_ready",
        "paper_promotion_pass": False,
        "claim_boundary": {
            "selective_metric_pass": True,
            "calibrated_quantitative_result_claim_allowed": False,
            "synthetic_missing_evidence_controls_used": True,
            "independent_human_observability_labels_used": False,
            "official_test_used": False,
        },
        "validation_errors": len(errors),
        "next_todo": NEXT_TODO,
    }
    write_json(args.output_dir / "summary.json", summary)
    report = f"""# CI / Qualitative / Failure Wording After p_obs / p_rel Review

## 목적

`p_obs/p_rel` selective metric 통과 이후, paper claim으로 어디까지 말할 수
있는지 검토했다.

## 결과

```text
status = {summary['status']}
selected_path = {summary['selected_path']}
paper_promotion_pass = false
validation_errors = {len(errors)}
next_todo = {NEXT_TODO}
```

CI와 qualitative examples, failure wording을 생성했다. 이 단계의 결론은
`p_obs/p_rel`을 framework component로 유지하되, calibrated quantitative paper
claim은 아직 금지한다는 것이다.
"""
    (args.output_dir / "report.md").write_text(report, encoding="utf-8")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
